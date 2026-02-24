import datetime
import os
import traceback
import re
import json
from PyQt6.QtCore import QThread, pyqtSignal

from .CVReportAnalyzer import CVReportAnalyzer
from .OtherReportAnalyzer import OtherReportAnalyzer
from .AptsReportAnalyzer import AptsReportAnalyzer


# ============================ 报告分析器 ============================

class ReportAnalyzer(QThread):
    """报告分析线程 - 负责在后台线程中执行报告分析任务"""
    
    analysis_finished = pyqtSignal(str, str)
    # progress_updated = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, test_path, check_apts=True):
        super().__init__()
        self.test_path = test_path
        self.check_apts = check_apts  # 控制是否检查APTS
        self.cv_analyzer = CVReportAnalyzer()
        self.other_analyzer = OtherReportAnalyzer()
        self.apts_analyzer = AptsReportAnalyzer()
        # 新增：存储CTS设备信息版本
        self.cts_device_info_version = None
    
    def run(self):
        """执行报告分析 - 在线程中运行的主要逻辑"""
        try:
            # self.progress_updated.emit(10)
            
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
            # self.progress_updated.emit(20)
            for (dirpath, dirnames, filenames) in os.walk(self.test_path):
                for filename in filenames:
                    pathnames.append(os.path.join(dirpath, filename))
            
            if not pathnames:
                error_msg = f"❌ 在目录中未找到任何报告文件: {self.test_path}"
                output_error.append(error_msg)
                self.error_occurred.emit(error_msg)
                return
            
            # 首先检查是否存在APTS报告文件
            # self.progress_updated.emit(25)
            apts_report_exists = self.check_apts_reports_existence(pathnames)
            
            # 检查APTS报告存在性是否符合版本要求
            if self.check_apts and not apts_report_exists:
                # GO版本或默认模式，但没有APTS报告
                output_error.append("❌ GO版本模式下未找到APTS报告，请检查")
            elif not self.check_apts and apts_report_exists:
                # FULL版本模式，但发现了APTS报告
                output_error.append("❌ FULL版本模式下发现了APTS报告，请检查")
            
            # 新增：从CTS报告中提取PackageDeviceInfo版本号
            cts_version_comparison = self.extract_and_compare_cts_device_info_versions(pathnames)
            if cts_version_comparison:
                # 根据模式决定输出哪种版本信息
                if self.check_apts:
                    # GO版本模式 - 只检查GO版本
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
                    # FULL版本模式 - 只检查FULL版本
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
                
                # 添加分隔符
                output_lines.append(ReportDelimiter)
            else:
                output_error.append(f"⚠️ 无法提取CTS设备信息版本")
            
            # 按照字母顺序 A-Z 分析报告
            # 1. 先分析APTS报告 (A开头) - 根据配置决定是否检查
            # self.progress_updated.emit(30)
            try:
                if self.check_apts:
                    output_lines, apts_errors = self.apts_analyzer.analyze_apts_reports(pathnames, output_lines, [])
                    # 按顺序添加APTS错误
                    output_error.extend(apts_errors)
                else:
                    output_lines.append("💡 已跳过APTS报告分析（FULL版本模式）")
                    output_lines.append(ReportDelimiter)
            except Exception as e:
                error_msg = f"APTS报告分析错误: {str(e)}\n{traceback.format_exc()}"
                output_error.append(error_msg)
                self.error_occurred.emit(error_msg)
                return
            
            # 2. 再分析CTS报告 (C开头) - 由CVReportAnalyzer处理CTS_VERIFIER
            # self.progress_updated.emit(50)
            try:
                output_lines, cts_errors = self.cv_analyzer.analyze_cv_reports(pathnames, output_lines, [])
                # 按顺序添加CTS错误
                output_error.extend(cts_errors)
            except Exception as e:
                error_msg = f"CTS报告分析错误: {str(e)}\n{traceback.format_exc()}"
                output_error.append(error_msg)
                self.error_occurred.emit(error_msg)
                return
            
            # 3. 最后分析其他报告 (GTS, STS, VTS等) - 由OtherReportAnalyzer处理
            # self.progress_updated.emit(70)
            try:
                output_lines, other_errors = self.other_analyzer.analyze_other_reports(pathnames, output_lines, [])
                # 按顺序添加其他错误
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
            
            # 根据是否检查APTS来合并数据
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
            
            # 使用列表来存储错误信息，保持顺序
            ordered_errors = []
            seen_errors = set()  # 用于去重的集合
            
            # 首先添加从各个分析器收集的错误（按分析顺序）
            for error in output_error:
                if error not in seen_errors:
                    seen_errors.add(error)
                    ordered_errors.append(error)
            
            # 检查Fingerprint差异 - 保持顺序的同时去重
            # self.progress_updated.emit(85)
            for i in range(len(all_fingerprints)):
                if i > 0 and all_fingerprints[0] != all_fingerprints[i]:
                    tool_name = all_suite_plans[i] if i < len(all_suite_plans) else "未知工具"
                    error_line = f"❌ {tool_name}存在有不同的Fingerprint：\n❌ Fingerprint\t{all_fingerprints[0]}\n❌ Fingerprint\t{all_fingerprints[i]}"
                    # 去重检查
                    if error_line not in seen_errors:
                        seen_errors.add(error_line)
                        ordered_errors.append(error_line)
            
            # 检查Security_Patch差异 - 保持顺序的同时去重
            # self.progress_updated.emit(95)
            # 检查第一个安全补丁是否超过60天
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
                    padding = ' ' * 4  # 4个空格
                    error_line = f"❌ {tool_name}存在有不同的Security_Patch：\n❌ {label}{padding}{all_security_patches[0]}\n❌ {label}{padding}{all_security_patches[i]}"
                    # 去重检查
                    if error_line not in seen_errors:
                        seen_errors.add(error_line)
                        ordered_errors.append(error_line)
            
            # ==================== 新增：分析工具最低版本 ====================
            # self.progress_updated.emit(97)
            min_versions_output = self.analyze_minimum_tool_versions()
            if min_versions_output:
                # 只在错误信息中添加最低版本信息，用于人工确认
                min_versions_block = []
                min_versions_block.append("="*100)
                min_versions_block.append("⚠️ 各测试工具最低版本汇总 (按构建号升序) - 请人工确认:")
                # 为每一行都添加警告符号
                for line in min_versions_output:
                    min_versions_block.append(f"⚠️ {line}")
                min_versions_block.append("="*100)
                
                # 将整个块作为一个字符串添加到错误信息中，确保在最后
                min_versions_text = "\n".join(min_versions_block)
                if min_versions_text not in seen_errors:
                    seen_errors.add(min_versions_text)
                    ordered_errors.append(min_versions_text)
            
            # self.progress_updated.emit(100)
            
            # 发射完成信号，同时传递完整结果和错误信息
            full_result = "\n".join(output_lines)
            
            # 格式化错误信息：每个错误信息之间用分隔符隔开
            if ordered_errors:
                formatted_errors = []
                for error in ordered_errors:
                    formatted_errors.append(ReportDelimiter)
                    formatted_errors.append(error)
                # 添加最后一个分隔符
                formatted_errors.append(ReportDelimiter)
                error_result = "\n".join(formatted_errors)
            else:
                error_result = "没有发现错误"
                
            self.analysis_finished.emit(full_result, error_result)
            
        except Exception as e:
            error_msg = f"❌ 分析过程中出现错误: {str(e)}\n{traceback.format_exc()}"
            output_error.append(error_msg)
            self.error_occurred.emit(error_msg)
    
    def check_apts_reports_existence(self, pathnames):
        """检查是否存在APTS报告文件"""
        for path in pathnames:
            # 检查路径是否包含test_approval并且包含test_result.xml
            if "test_approval" in path and "test_result.xml" in path:
                return True
        return False
    
    def extract_and_compare_cts_device_info_versions(self, pathnames):
        try:
            # 查找所有CTS报告目录中的PackageDeviceInfo.deviceinfo.json文件
            cts_device_info_files = []
            for path in pathnames:
                # 更精确地匹配PackageDeviceInfo.deviceinfo.json文件
                path_lower = path.lower()
                if "packagedeviceinfo.deviceinfo.json" in path_lower:
                    cts_device_info_files.append(path)
            
            # 如果没有找到，尝试宽泛匹配
            if not cts_device_info_files:
                for path in pathnames:
                    path_lower = path.lower()
                    if "deviceinfo.json" in path_lower and "cts_verifier" not in path_lower:
                        # 检查是否在CTS相关目录中
                        if any(cts_marker in path_lower for cts_marker in ['/cts/', '\\cts\\', '_cts_', 'android-cts']):
                            cts_device_info_files.append(path)
            
            if not cts_device_info_files:
                # 删除调试信息打印
                return None
            
            # 收集所有版本信息
            go_versions = []
            full_versions = []
            all_file_paths = []
            
            for file_path in cts_device_info_files:
                try:
                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 尝试解析JSON
                    try:
                        data = json.loads(content)
                        
                        # 根据数据结构提取包信息
                        go_version = None
                        full_version = None
                        
                        # 情况1: 数据是字典，包含"package"键
                        if isinstance(data, dict):
                            # 首先尝试从"package"键获取包列表
                            if "package" in data:
                                packages = data["package"]
                                if isinstance(packages, list):
                                    # 遍历所有包，查找目标包
                                    for package in packages:
                                        if isinstance(package, dict):
                                            package_name = package.get("name", "")
                                            
                                            # 检查是否是目标包
                                            if package_name == "com.google.mainline.go.primary":
                                                version_name = package.get("version_name", "未知")
                                                go_version = version_name
                                            
                                            elif package_name == "com.google.android.modulemetadata":
                                                version_name = package.get("version_name", "未知")
                                                full_version = version_name
                            else:
                                # 尝试其他可能的键名
                                for key in data.keys():
                                    if "package" in key.lower():
                                        packages = data[key]
                                        if isinstance(packages, list):
                                            # 遍历包列表
                                            for package in packages:
                                                if isinstance(package, dict):
                                                    package_name = package.get("name", "")
                                                    
                                                    # 检查是否是目标包
                                                    if package_name == "com.google.mainline.go.primary":
                                                        version_name = package.get("version_name", "未知")
                                                        go_version = version_name
                                                    
                                                    elif package_name == "com.google.android.modulemetadata":
                                                        version_name = package.get("version_name", "未知")
                                                        full_version = version_name
                        
                        # 情况2: 数据是列表
                        elif isinstance(data, list):
                            # 遍历列表中的每个包对象
                            for package in data:
                                if isinstance(package, dict):
                                    package_name = package.get("name", "")
                                    
                                    # 检查是否是目标包
                                    if package_name == "com.google.mainline.go.primary":
                                        version_name = package.get("version_name", "未知")
                                        go_version = version_name
                                    
                                    elif package_name == "com.google.android.modulemetadata":
                                        version_name = package.get("version_name", "未知")
                                        full_version = version_name
                        
                        else:
                            # 尝试直接搜索包名和版本名
                            content_lower = content.lower()
                            
                            # 搜索com.google.android.modulemetadata
                            if "com.google.android.modulemetadata" in content_lower:
                                # 尝试提取版本号
                                version_match = re.search(r'"version_name"\s*:\s*"([^"]+)"', content)
                                if version_match:
                                    full_version = version_match.group(1)
                            
                            # 搜索com.google.mainline.go.primary
                            if "com.google.mainline.go.primary" in content_lower:
                                # 尝试提取版本号
                                version_match = re.search(r'"version_name"\s*:\s*"([^"]+)"', content)
                                if version_match:
                                    go_version = version_match.group(1)
                    
                    except json.JSONDecodeError as e:
                        # 尝试处理可能包含多行JSON的情况（每行一个JSON对象）
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
                            
                            # 处理解析后的对象列表
                            go_version = None
                            full_version = None
                            
                            for obj in data:
                                if isinstance(obj, dict):
                                    package_name = obj.get("name", "")
                                    
                                    # 检查是否是目标包
                                    if package_name == "com.google.mainline.go.primary":
                                        version_name = obj.get("version_name", "未知")
                                        go_version = version_name
                                    
                                    elif package_name == "com.google.android.modulemetadata":
                                        version_name = obj.get("version_name", "未知")
                                        full_version = version_name
                        else:
                            continue
                    
                    # 保存找到的版本信息
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
        
        # 从各个分析器收集版本信息
        if self.check_apts:
            self._collect_versions_from_analyzer(self.apts_analyzer, all_tool_versions)
        
        self._collect_versions_from_analyzer(self.cv_analyzer, all_tool_versions)
        self._collect_versions_from_analyzer(self.other_analyzer, all_tool_versions)
        
        # 分析每个工具的最低版本
        for tool_type, versions in all_tool_versions.items():
            if versions:
                # 按构建号升序排序（构建号越小版本越低）
                sorted_versions = sorted(versions, key=lambda x: self._parse_build_number(x[3]))
                
                # 最低版本是构建号最小的版本
                min_version = sorted_versions[0]
                tool_name = min_version[1]  # 工具名称在索引1
                version_num = min_version[2]  # 版本号在索引2
                build_num = min_version[3]  # 构建号在索引3
                
                # 特殊处理APTS的输出格式
                if tool_type == "APTS":
                    # APTS只显示版本号，不显示构建号
                    output_lines.append(f"{tool_type} ({tool_name}):")
                    output_lines.append(f"  最低版本: {version_num}")
                else:
                    # 其他工具保持原来的输出格式
                    output_lines.append(f"{tool_type} ({tool_name}):")
                    output_lines.append(f"  最低版本: {version_num} / {build_num}")
        
        return output_lines
    
    def _collect_versions_from_analyzer(self, analyzer, all_tool_versions):
        """从分析器收集版本信息"""
        if hasattr(analyzer, 'tool_versions') and analyzer.tool_versions:
            for tool_type, tool_name, version_num, build_num in analyzer.tool_versions:
                if tool_type not in all_tool_versions:
                    all_tool_versions[tool_type] = []
                # 存储格式: (工具类型, 工具名称, 版本号, 构建号)
                all_tool_versions[tool_type].append((tool_type, tool_name, version_num, build_num))
    
    def _parse_build_number(self, build_str):
        """解析构建号，转换为整数进行比较"""
        try:
            # 移除可能的非数字字符，只保留数字
            clean_build = re.sub(r'[^\d]', '', build_str)
            return int(clean_build) if clean_build else 0
        except (ValueError, TypeError):
            return 0