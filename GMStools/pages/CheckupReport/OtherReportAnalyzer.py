
import os
import re
import datetime

# ============================ 其他报告分析器 ============================
ReportDelimiter = "=" * 100

class OtherReportAnalyzer:
    """其他报告分析器"""
    
    def __init__(self):
        self.result_path = []
        self.Suite_Plan_comparison = []
        self.Fingerprint_comparison = []
        self.Security_Patch_comparison = []
        # 新增：存储工具版本信息
        self.tool_versions = []  # 格式: (工具类型, 工具名称, 版本号, 构建号)
    
    def analyze_other_reports(self, pathnames, output_lines, output_error):
        """分析其他报告 - 按工具类型排序"""
        
        # 查找测试结果文件
        for i in pathnames:
            if "test_result_failures_suite.html" in i:
                self.result_path.append(str(i))
        
        # 按工具类型排序：GTS -> STS -> VTS -> 其他
        self.result_path.sort(key=lambda x: self.get_tool_priority(x))
        
        # 访问结果绝对路径并匹配出相应信息
        for j in self.result_path:
            try:
                with open(j, 'r', encoding="utf-8") as htmlf:
                    htmlcont = htmlf.read().replace("\\n", "")
                
                Suite_Plan_match = re.findall("Suite / Plan</td><td>(.*?)</td>", htmlcont)
                if Suite_Plan_match:
                    Suite_Plan = Suite_Plan_match[0]
                    self.Suite_Plan_comparison.append(Suite_Plan)
                    
                    Suite_Build = re.findall("Suite / Build</td><td>(.*?)</td>", htmlcont)[0]
                    Tests_Passed = re.findall("Tests Passed</td><td>(.*?)</td>", htmlcont)[0]
                    Tests_Failed = re.findall("Tests Failed</td><td>(.*?)</td>", htmlcont)[0]
                    Modules_Done = re.findall("Modules Done</td><td>(.*?)</td>", htmlcont)[0]
                    Modules_Total = re.findall("Modules Total</td><td>(.*?)</td>", htmlcont)[0]
                    Fingerprint = re.findall("Fingerprint</td><td>(.*?)</td>", htmlcont)[0]
                    self.Fingerprint_comparison.append(Fingerprint)
                    Security_Patch = re.findall("Security Patch</td><td>(.*?)</td>", htmlcont)[0]
                    self.Security_Patch_comparison.append(Security_Patch)
                    
                    # 使用制表符对齐
                    output_lines.append("测试工具:\t%s" % Suite_Plan)
                    output_lines.append("工具版本:\t%s" % Suite_Build)
                    output_lines.append("PASS数:\t%s" % Tests_Passed)
                    output_lines.append("FAIL数:\t%s" % Tests_Failed)
                    output_lines.append("模块完成:\t%s" % Modules_Done)
                    output_lines.append("模块总数:\t%s" % Modules_Total)
                    output_lines.append("Fingerprint:\t%s" % Fingerprint)
                    output_lines.append("安全补丁:\t%s" % Security_Patch)
                    
                    # 新增：收集工具版本信息
                    self.collect_tool_version(Suite_Plan, Suite_Build)
                    
                    # 检查FAIL数是否为0
                    try:
                        failed_count = int(Tests_Failed)
                        if failed_count > 0:
                            output_error.append(f"❌ {Suite_Plan} 有 {failed_count} 个测试失败，请检查")
                    except ValueError:
                        pass
                    
                    # STS工具版本检查
                    if 'sts' in Suite_Plan.lower():
                        self.check_sts_version(Suite_Plan, Suite_Build, Security_Patch, output_lines, output_error)
                    
                    if Modules_Done != Modules_Total:
                        output_error.append(f"❌ {Suite_Plan}的模块数量不完整，请检查")
                    
                    output_lines.append(ReportDelimiter)
            except Exception as e:
                output_error.append(f"❌ 处理报告文件时出错 {j}: {str(e)}")
        
        return output_lines, output_error
    
    def collect_tool_version(self, suite_plan, suite_build):
        """收集工具版本信息"""
        # 解析工具类型和名称
        if " / " in suite_plan:
            parts = suite_plan.split(" / ")
            tool_type = parts[0].strip()
            tool_name = parts[1].strip()
        else:
            tool_type = suite_plan
            tool_name = suite_plan
        
        # 解析版本号和构建号
        if " / " in suite_build:
            version_parts = suite_build.split(" / ")
            version_num = version_parts[0].strip()
            build_num = version_parts[1].strip()
        else:
            version_num = suite_build
            build_num = "0"  # 如果没有构建号，设为0
        
        # 特殊处理CTS-on-GSI - 将其与普通CTS分开
        if "cts-on-gsi" in tool_name.lower():
            tool_type = "CTS_ON_GSI"  # 单独的工具类型
            tool_name = "cts-on-gsi"
        # 特殊处理CTS - 确保CTS和CTS-on-GSI分开
        elif "cts" in tool_name.lower() and "cts-on-gsi" not in tool_name.lower():
            tool_type = "CTS"  # 普通CTS测试
            if "cts" not in tool_name.lower():
                tool_name = "cts"
        # 特殊处理GTS的不同测试计划
        elif "gts" in tool_type.lower():
            # GTS的不同测试计划需要分开对比
            if "gts-root" in tool_name.lower():
                tool_type = "GTS_ROOT"
                tool_name = "gts-root"
            elif "gts-interactive" in tool_name.lower():
                tool_type = "GTS_INTERACTIVE"
                tool_name = "gts-interactive"
            else:
                tool_type = "GTS"
                tool_name = "gts"
        
        self.tool_versions.append((tool_type, tool_name, version_num, build_num))
    
    def get_tool_priority(self, file_path):
        """根据文件路径确定工具优先级"""
        path_lower = file_path.lower()
        if 'gts' in path_lower:
            return 1  # GTS最高优先级
        elif 'sts' in path_lower:  # 修正：将中文"在"改为英文"in"
            return 2  # STS次之
        elif 'vts' in path_lower:
            return 3  # VTS再次之
        else:
            return 4  # 其他工具最后
    
    def check_sts_version(self, suite_plan, suite_build, security_patch, output_lines, output_error):
        """检查STS工具版本"""
        detected_version = self.extract_sts_version(suite_build)
        
        if detected_version:
            # 检查安全补丁时间是否超过60天
            patch_status, days_diff = self.check_security_patch_age(security_patch)
            if not patch_status:
                output_error.append(f"❌ 安全补丁时间已超{days_diff}天,请确认是否正确")
            
            # 获取当前可用的最新3个STS版本
            available_versions = self.get_available_sts_versions()
            
            # 获取安全补丁对应的理论STS版本
            theoretical_versions = self.get_theoretical_sts_versions(security_patch)
            
            # 检查检测到的版本是否在可用版本范围内
            if detected_version in available_versions:
                pass
            else:
                output_error.append(f"❌ STS工具版本不可用: 检测到 {detected_version}，当前可用范围: {', '.join(available_versions)}")
                
                # 输出安全补丁与使用工具的对应关系
                output_error.append(f"❌ 安全补丁 {security_patch} 对应的理论工具版本: {', '.join(theoretical_versions)}")
                
                # 检查检测到的版本是否在理论版本范围内
                if detected_version in theoretical_versions:
                    output_error.append(f"❌ 检测到的工具版本 {detected_version} 在安全补丁的理论版本范围内")
                else:
                    output_error.append(f"❌ 检测到的工具版本 {detected_version} 不在安全补丁的理论版本范围内")
        else:
            output_error.append(f"❌ 无法从工具版本 '{suite_build}' 中提取STS版本信息")
    
    def check_security_patch_age(self, security_patch):
        """检查安全补丁时间是否超过60天"""
        try:
            patch_date = datetime.datetime.strptime(security_patch, "%Y-%m-%d")
            current_date = datetime.datetime.now()
            days_diff = (current_date - patch_date).days
            return (days_diff <= 60, days_diff)
        except Exception:
            return (True, 0)
    
    def get_available_sts_versions(self):
        """根据当前系统时间确定实际能拿到的工具版本范围"""
        current_date = datetime.datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        
        # 计算当前系统能拿到的最新STS版本
        base_release_year = 2025
        base_release_month = 9
        base_version = 43
        
        months_diff = (current_year - base_release_year) * 12 + (current_month - base_release_month)
        current_version = base_version + months_diff
        
        return [
            f"sts-r{current_version-2}",
            f"sts-r{current_version-1}", 
            f"sts-r{current_version}"
        ]
    
    def get_theoretical_sts_versions(self, security_patch):
        """根据安全补丁时间获取理论上可用的STS版本范围"""
        try:
            patch_date = datetime.datetime.strptime(security_patch, "%Y-%m-%d")
            year = patch_date.year
            month = patch_date.month
            
            base_year = 2025
            base_month = 10
            base_version = 43
            
            months_diff = (year - base_year) * 12 + (month - base_month)
            current_version = base_version + months_diff
            
            return [
                f"sts-r{current_version}",
                f"sts-r{current_version+1}", 
                f"sts-r{current_version+2}"
            ]
        except Exception:
            return ["sts-r41", "sts-r42", "sts-r43"]
    
    def extract_sts_version(self, suite_build):
        """从工具版本字符串中提取STS版本"""
        version_patterns = [
            r'sts[_-]?[Rr]?(\d+)',
            r'STS[_-]?[Rr]?(\d+)',
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, suite_build, re.IGNORECASE)
            if match:
                version_num = match.group(1)
                try:
                    version_int = int(version_num)
                    return f"sts-r{version_int}"
                except ValueError:
                    continue
        
        direct_r_match = re.search(r'[Rr](\d+)', suite_build)
        if direct_r_match:
            version_num = direct_r_match.group(1)
            try:
                version_int = int(version_num)
                return f"sts-r{version_int}"
            except ValueError:
                pass
        
        return None
