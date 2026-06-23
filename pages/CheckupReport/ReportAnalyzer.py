import datetime
import os
import traceback
import re
import json
from PyQt6.QtCore import QThread, pyqtSignal

from .CVReportAnalyzer import CVReportAnalyzer
from .OtherReportAnalyzer import OtherReportAnalyzer
from .AptsReportAnalyzer import AptsReportAnalyzer


class ReportAnalyzer(QThread):
    """报告分析线程 - 负责在后台线程中执行报告分析任务"""
    
    analysis_finished = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, test_path, check_apts=True):
        super().__init__()
        self.test_path = test_path
        self.check_apts = check_apts  # 控制是否检查APTS
        self.cv_analyzer = CVReportAnalyzer()
        self.other_analyzer = OtherReportAnalyzer()
        self.apts_analyzer = AptsReportAnalyzer()
        self.cts_device_info_version = None
    
    def run(self):
        """执行报告分析 - 在线程中运行的主要逻辑"""
        try:
            pathnames = []
            output_lines = []
            output_error = []
            ReportDelimiter = "=" * 100
            output_lines.append(ReportDelimiter)
            
            # 检查目录是否存在
            if not os.path.exists(self.test_path):
                error_msg = f"❌ 目录不存在: {self.test_path}"
                self.error_occurred.emit(error_msg)
                output_error.append(error_msg)
                return
            
            if not os.path.isdir(self.test_path):
                error_msg = f"❌ 路径不是目录: {self.test_path}"
                self.error_occurred.emit(error_msg)
                output_error.append(error_msg)
                return
            
            # 遍历目录获取所有文件路径
            for (dirpath, dirnames, filenames) in os.walk(self.test_path):
                for filename in filenames:
                    pathnames.append(os.path.join(dirpath, filename))
            
            if not pathnames:
                error_msg = f"❌ 在目录中未找到任何报告文件: {self.test_path}"
                output_error.append(error_msg)
                self.error_occurred.emit(error_msg)
                return
            
            # 检查两种格式的APTS报告是否存在
            apts_xml_exists = self.check_apts_xml_existence(pathnames)
            gts_apts_html_exists = self.check_gts_apts_html_existence(pathnames)
            apts_report_exists = apts_xml_exists or gts_apts_html_exists
            
            # 检查APTS报告存在性是否符合版本要求
            if self.check_apts and not apts_report_exists:
                output_error.append("❌ GO版本模式下未找到APTS报告，请检查")
            elif not self.check_apts and apts_report_exists:
                output_error.append("❌ FULL版本模式下发现了APTS报告，请检查")
            
            # 从CTS报告中提取PackageDeviceInfo版本号
            cts_version_comparison = self.extract_and_compare_cts_device_info_versions(pathnames)
            if cts_version_comparison:
                if self.check_apts:
                    package_name = "com.google.mainline.go.primary"
                    version_label = "GO主模块版本"
                    extracted_versions = cts_version_comparison.get("go_versions", [])
                    
                    if extracted_versions:
                        unique_versions = set(extracted_versions)
                        if len(unique_versions) == 1:
                            version = list(unique_versions)[0]
                            self.cts_device_info_version = version
                            output_lines.append(f"{version_label}:\t{package_name} = {version}")
                        else:
                            output_error.append(f"⚠️ {version_label}存在不同的版本号，请人工确认:")
                            for i, version in enumerate(extracted_versions, 1):
                                output_error.append(f"⚠️   版本{i}: {version}")
                            output_lines.append(f"⚠️ {version_label} (需人工确认):")
                            output_lines.append(f"⚠️   {package_name} 存在 {len(unique_versions)} 个不同版本:")
                            for version in sorted(unique_versions):
                                output_lines.append(f"⚠️     - {version}")
                    else:
                        output_error.append(f"⚠️ CTS报告中未找到GO版本包信息: {package_name}")
                else:
                    package_name = "com.google.android.modulemetadata"
                    version_label = "Mainline版本"
                    extracted_versions = cts_version_comparison.get("full_versions", [])
                    
                    if extracted_versions:
                        unique_versions = set(extracted_versions)
                        if len(unique_versions) == 1:
                            version = list(unique_versions)[0]
                            self.cts_device_info_version = version
                            output_lines.append(f"{version_label}:\t{package_name} = {version}")
                        else:
                            output_error.append(f"⚠️ {version_label}存在不同的版本号，请人工确认:")
                            for i, version in enumerate(extracted_versions, 1):
                                output_error.append(f"⚠️   版本{i}: {version}")
                            output_lines.append(f"⚠️ {version_label} (需人工确认):")
                            output_lines.append(f"⚠️   {package_name} 存在 {len(unique_versions)} 个不同版本:")
                            for version in sorted(unique_versions):
                                output_lines.append(f"⚠️     - {version}")
                    else:
                        output_error.append(f"⚠️ CTS报告中未找到FULL版本包信息: {package_name}")
                
                output_lines.append(ReportDelimiter)
            else:
                output_error.append(f"⚠️ 无法提取CTS设备信息版本")
            
            # 1. 分析APTS报告（仅当存在XML格式时才调用AptsReportAnalyzer）
            if self.check_apts:
                if apts_xml_exists:
                    output_lines, apts_errors = self.apts_analyzer.analyze_apts_reports(pathnames, output_lines, [])
                    output_error.extend(apts_errors)
                else:
                    output_lines.append("💡 未找到旧版XML APTS报告，但检测到GTS/apts报告（由其他分析器处理）")
                    output_lines.append(ReportDelimiter)
            else:
                output_lines.append("💡 已跳过APTS报告分析（FULL版本模式）")
                output_lines.append(ReportDelimiter)
            
            # 2. 分析CTS报告（CVReportAnalyzer处理CTS_VERIFIER）
            try:
                output_lines, cts_errors = self.cv_analyzer.analyze_cv_reports(pathnames, output_lines, [])
                output_error.extend(cts_errors)
            except Exception as e:
                error_msg = f"CTS报告分析错误: {str(e)}\n{traceback.format_exc()}"
                output_error.append(error_msg)
                self.error_occurred.emit(error_msg)
                return
            
            # 3. 分析其他报告（GTS, STS, VTS等）—— GTS/apts将被归类为APTS
            try:
                output_lines, other_errors = self.other_analyzer.analyze_other_reports(pathnames, output_lines, [])
                output_error.extend(other_errors)
            except Exception as e:
                error_msg = f"❌ 其他报告分析错误: {str(e)}\n{traceback.format_exc()}"
                output_error.append(error_msg)
                self.error_occurred.emit(error_msg)
                return
            
            # 合并所有分析数据
            all_suite_plans = []
            all_fingerprints = []
            all_security_patches = []
            
            if self.check_apts:
                all_suite_plans.extend(self.apts_analyzer.Suite_Plan_comparison)
                all_fingerprints.extend(self.apts_analyzer.Fingerprint_comparison)
                all_security_patches.extend(self.apts_analyzer.Security_Patch_comparison)
            
            all_suite_plans.extend(self.cv_analyzer.Suite_Plan_comparison)
            all_fingerprints.extend(self.cv_analyzer.Fingerprint_comparison)
            all_security_patches.extend(self.cv_analyzer.Security_Patch_comparison)
            
            all_suite_plans.extend(self.other_analyzer.Suite_Plan_comparison)
            all_fingerprints.extend(self.other_analyzer.Fingerprint_comparison)
            all_security_patches.extend(self.other_analyzer.Security_Patch_comparison)
            
            # 构建有序且去重的错误列表
            ordered_errors = []
            seen_errors = set()
            
            for error in output_error:
                if error not in seen_errors:
                    seen_errors.add(error)
                    ordered_errors.append(error)
            
            # 检查Fingerprint差异
            for i in range(len(all_fingerprints)):
                if i > 0 and all_fingerprints[0] != all_fingerprints[i]:
                    tool_name = all_suite_plans[i] if i < len(all_suite_plans) else "未知工具"
                    error_line = f"❌ {tool_name}存在有不同的Fingerprint：\n❌ Fingerprint\t{all_fingerprints[0]}\n❌ Fingerprint\t{all_fingerprints[i]}"
                    if error_line not in seen_errors:
                        seen_errors.add(error_line)
                        ordered_errors.append(error_line)
            
            # 检查安全补丁年龄
            if all_security_patches:
                try:
                    Security_Patch_time = datetime.datetime.strptime(all_security_patches[0], "%Y-%m-%d")
                    diff_days = (datetime.datetime.now() - Security_Patch_time).days
                    if diff_days > 60:
                        error_line = '❌ 当前安全补丁已超出送测日期,需更新安全补丁'
                        if error_line not in seen_errors:
                            seen_errors.add(error_line)
                            ordered_errors.append(error_line)
                except Exception as e:
                    error_line = f"❌ 安全补丁日期解析错误: {str(e)}"
                    if error_line not in seen_errors:
                        seen_errors.add(error_line)
                        ordered_errors.append(error_line)
            
            # 检查安全补丁差异
            for i in range(len(all_security_patches)):
                if i > 0 and all_security_patches[0] != all_security_patches[i]:
                    tool_name = all_suite_plans[i] if i < len(all_suite_plans) else "未知工具"
                    label = "Security_Patch"
                    padding = ' ' * 4
                    error_line = f"❌ {tool_name}存在有不同的Security_Patch：\n❌ {label}{padding}{all_security_patches[0]}\n❌ {label}{padding}{all_security_patches[i]}"
                    if error_line not in seen_errors:
                        seen_errors.add(error_line)
                        ordered_errors.append(error_line)
            
            # 分析工具最低版本
            min_versions_output = self.analyze_minimum_tool_versions()
            if min_versions_output:
                min_versions_block = []
                min_versions_block.append("="*100)
                min_versions_block.append("⚠️ 各测试工具最低版本汇总 (按构建号升序) - 请人工确认:")
                for line in min_versions_output:
                    min_versions_block.append(f"⚠️ {line}")
                min_versions_block.append("="*100)
                min_versions_text = "\n".join(min_versions_block)
                if min_versions_text not in seen_errors:
                    seen_errors.add(min_versions_text)
                    ordered_errors.append(min_versions_text)
            
            # 发射完成信号
            full_result = "\n".join(output_lines)
            
            if ordered_errors:
                formatted_errors = []
                for error in ordered_errors:
                    formatted_errors.append(ReportDelimiter)
                    formatted_errors.append(error)
                formatted_errors.append(ReportDelimiter)
                error_result = "\n".join(formatted_errors)
            else:
                error_result = "没有发现错误"
                
            self.analysis_finished.emit(full_result, error_result)
            
        except Exception as e:
            error_msg = f"❌ 分析过程中出现错误: {str(e)}\n{traceback.format_exc()}"
            output_error.append(error_msg)
            self.error_occurred.emit(error_msg)
    
    # ==================== 辅助方法 ====================
    def check_apts_xml_existence(self, pathnames):
        """检查是否存在XML格式的旧版APTS报告"""
        for path in pathnames:
            if "test_approval" in path and "test_result.xml" in path:
                return True
        return False
    
    def check_gts_apts_html_existence(self, pathnames):
        """检查是否存在GTS/apts格式的HTML报告（视为新APTS报告）"""
        for path in pathnames:
            if path.endswith("test_result_failures_suite.html"):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if "GTS / apts" in content:
                        return True
                except:
                    continue
        return False
    
    def extract_and_compare_cts_device_info_versions(self, pathnames):
        """从CTS报告中提取PackageDeviceInfo版本号"""
        try:
            # 查找所有CTS报告目录中的PackageDeviceInfo.deviceinfo.json文件
            cts_device_info_files = []
            for path in pathnames:
                path_lower = path.lower()
                if "packagedeviceinfo.deviceinfo.json" in path_lower:
                    cts_device_info_files.append(path)
            
            # 如果没有找到，尝试宽泛匹配
            if not cts_device_info_files:
                for path in pathnames:
                    path_lower = path.lower()
                    if "deviceinfo.json" in path_lower and "cts_verifier" not in path_lower:
                        if any(cts_marker in path_lower for cts_marker in ['/cts/', '\\cts\\', '_cts_', 'android-cts']):
                            cts_device_info_files.append(path)
            
            if not cts_device_info_files:
                return None
            
            # 收集所有版本信息
            go_versions = []
            full_versions = []
            all_file_paths = []
            
            for file_path in cts_device_info_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 尝试解析JSON
                    try:
                        data = json.loads(content)
                        
                        go_version = None
                        full_version = None
                        
                        if isinstance(data, dict):
                            if "package" in data:
                                packages = data["package"]
                                if isinstance(packages, list):
                                    for package in packages:
                                        if isinstance(package, dict):
                                            package_name = package.get("name", "")
                                            if package_name == "com.google.mainline.go.primary":
                                                version_name = package.get("version_name", "未知")
                                                go_version = version_name
                                            elif package_name == "com.google.android.modulemetadata":
                                                version_name = package.get("version_name", "未知")
                                                full_version = version_name
                            else:
                                for key in data.keys():
                                    if "package" in key.lower():
                                        packages = data[key]
                                        if isinstance(packages, list):
                                            for package in packages:
                                                if isinstance(package, dict):
                                                    package_name = package.get("name", "")
                                                    if package_name == "com.google.mainline.go.primary":
                                                        version_name = package.get("version_name", "未知")
                                                        go_version = version_name
                                                    elif package_name == "com.google.android.modulemetadata":
                                                        version_name = package.get("version_name", "未知")
                                                        full_version = version_name
                        elif isinstance(data, list):
                            for package in data:
                                if isinstance(package, dict):
                                    package_name = package.get("name", "")
                                    if package_name == "com.google.mainline.go.primary":
                                        version_name = package.get("version_name", "未知")
                                        go_version = version_name
                                    elif package_name == "com.google.android.modulemetadata":
                                        version_name = package.get("version_name", "未知")
                                        full_version = version_name
                        else:
                            content_lower = content.lower()
                            if "com.google.android.modulemetadata" in content_lower:
                                version_match = re.search(r'"version_name"\s*:\s*"([^"]+)"', content)
                                if version_match:
                                    full_version = version_match.group(1)
                            if "com.google.mainline.go.primary" in content_lower:
                                version_match = re.search(r'"version_name"\s*:\s*"([^"]+)"', content)
                                if version_match:
                                    go_version = version_match.group(1)
                    
                    except json.JSONDecodeError:
                        lines = content.strip().split('\n')
                        parsed_objects = []
                        for line in lines:
                            line = line.strip()
                            if line:
                                try:
                                    obj = json.loads(line)
                                    parsed_objects.append(obj)
                                except json.JSONDecodeError:
                                    continue
                        if parsed_objects:
                            data = parsed_objects
                            go_version = None
                            full_version = None
                            for obj in data:
                                if isinstance(obj, dict):
                                    package_name = obj.get("name", "")
                                    if package_name == "com.google.mainline.go.primary":
                                        version_name = obj.get("version_name", "未知")
                                        go_version = version_name
                                    elif package_name == "com.google.android.modulemetadata":
                                        version_name = obj.get("version_name", "未知")
                                        full_version = version_name
                    
                    if go_version:
                        go_versions.append(go_version)
                    if full_version:
                        full_versions.append(full_version)
                    
                    all_file_paths.append(file_path)
                    
                except Exception:
                    continue
            
            return {
                "go_versions": go_versions,
                "full_versions": full_versions,
                "file_paths": all_file_paths
            }
                
        except Exception:
            return None
    
    def analyze_minimum_tool_versions(self):
        """分析各测试工具的最低版本（按构建号升序）"""
        output_lines = []
        
        # 收集所有工具版本信息
        all_tool_versions = {}
        
        if self.check_apts:
            self._collect_versions_from_analyzer(self.apts_analyzer, all_tool_versions)
        
        self._collect_versions_from_analyzer(self.cv_analyzer, all_tool_versions)
        self._collect_versions_from_analyzer(self.other_analyzer, all_tool_versions)
        
        # 分析每个工具的最低版本
        for tool_type, versions in all_tool_versions.items():
            if versions:
                sorted_versions = sorted(versions, key=lambda x: self._parse_build_number(x[3]))
                min_version = sorted_versions[0]
                tool_name = min_version[1]
                version_num = min_version[2]
                build_num = min_version[3]
                
                if tool_type == "APTS":
                    output_lines.append(f"{tool_type} ({tool_name}):")
                    output_lines.append(f"  最低版本: {version_num}")
                else:
                    output_lines.append(f"{tool_type} ({tool_name}):")
                    output_lines.append(f"  最低版本: {version_num} / {build_num}")
        
        return output_lines
    
    def _collect_versions_from_analyzer(self, analyzer, all_tool_versions):
        if hasattr(analyzer, 'tool_versions') and analyzer.tool_versions:
            for tool_type, tool_name, version_num, build_num in analyzer.tool_versions:
                if tool_type not in all_tool_versions:
                    all_tool_versions[tool_type] = []
                all_tool_versions[tool_type].append((tool_type, tool_name, version_num, build_num))
    
    def _parse_build_number(self, build_str):
        try:
            clean_build = re.sub(r'[^\d]', '', build_str)
            return int(clean_build) if clean_build else 0
        except (ValueError, TypeError):
            return 0