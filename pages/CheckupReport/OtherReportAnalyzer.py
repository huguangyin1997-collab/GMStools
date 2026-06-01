import os
import re
import datetime

ReportDelimiter = "=" * 100

class OtherReportAnalyzer:
    """其他报告分析器"""
    
    def __init__(self):
        self.result_path = []
        self.Suite_Plan_comparison = []
        self.Fingerprint_comparison = []
        self.Security_Patch_comparison = []
        self.tool_versions = []
    
    def analyze_other_reports(self, pathnames, output_lines, output_error):
        self.result_path.clear()
        self.Suite_Plan_comparison.clear()
        self.Fingerprint_comparison.clear()
        self.Security_Patch_comparison.clear()
        self.tool_versions.clear()

        for i in pathnames:
            if "test_result_failures_suite.html" in i:
                self.result_path.append(str(i))
        
        self.result_path.sort(key=lambda x: self.get_tool_priority(x))
        
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
                    
                    # 输出时直接使用 Suite_Plan，不修改显示文本
                    output_lines.append("测试工具:\t%s" % Suite_Plan)
                    output_lines.append("工具版本:\t%s" % Suite_Build)
                    output_lines.append("PASS数:\t%s" % Tests_Passed)
                    output_lines.append("FAIL数:\t%s" % Tests_Failed)
                    output_lines.append("模块完成:\t%s" % Modules_Done)
                    output_lines.append("模块总数:\t%s" % Modules_Total)
                    output_lines.append("Fingerprint:\t%s" % Fingerprint)
                    output_lines.append("安全补丁:\t%s" % Security_Patch)
                    
                    # 收集工具版本信息，传入真实的 Suite_Plan
                    self.collect_tool_version(Suite_Plan, Suite_Build)
                    
                    try:
                        failed_count = int(Tests_Failed)
                        if failed_count > 0:
                            output_error.append(f"❌ {Suite_Plan} 有 {failed_count} 个测试失败，请检查")
                    except ValueError:
                        pass
                    
                    if 'sts' in Suite_Plan.lower():
                        self.check_sts_version(Suite_Plan, Suite_Build, Security_Patch, output_lines, output_error)
                    
                    if Modules_Done != Modules_Total:
                        output_error.append(f"❌ {Suite_Plan}的模块数量不完整，请检查")
                    
                    output_lines.append(ReportDelimiter)
            except Exception as e:
                output_error.append(f"❌ 处理报告文件时出错 {j}: {str(e)}")
        
        return output_lines, output_error
    
    def collect_tool_version(self, suite_plan, suite_build):
        """收集工具版本信息，特殊处理 GTS / apts 归类为 APTS（仅修改 tool_type，不修改显示）"""
        if " / " in suite_plan:
            parts = suite_plan.split(" / ")
            tool_type = parts[0].strip()
            tool_name = parts[1].strip()
        else:
            tool_type = suite_plan
            tool_name = suite_plan

        # 特殊处理：将 GTS / apts 归类为 APTS（内部归类，显示文本不变）
        if suite_plan == "GTS / apts":
            tool_type = "APTS"
            tool_name = "apts"  # 为了版本汇总统一
        # 其他工具类型处理（保持不变）
        elif "cts-on-gsi" in tool_name.lower():
            tool_type = "CTS_ON_GSI"
            tool_name = "cts-on-gsi"
        elif "cts" in tool_name.lower() and "cts-on-gsi" not in tool_name.lower():
            tool_type = "CTS"
            if "cts" not in tool_name.lower():
                tool_name = "cts"
        elif "gts" in tool_type.lower():
            if "gts-root" in tool_name.lower():
                tool_type = "GTS_ROOT"
                tool_name = "gts-root"
            elif "gts-interactive" in tool_name.lower():
                tool_type = "GTS_INTERACTIVE"
                tool_name = "gts-interactive"
            else:
                tool_type = "GTS"
                tool_name = "gts"

        # 解析版本号和构建号
        if " / " in suite_build:
            version_parts = suite_build.split(" / ")
            version_num = version_parts[0].strip()
            build_num = version_parts[1].strip()
        else:
            version_num = suite_build
            build_num = "0"
        
        self.tool_versions.append((tool_type, tool_name, version_num, build_num))
    
    def get_tool_priority(self, file_path):
        path_lower = file_path.lower()
        if 'gts' in path_lower:
            return 1
        elif 'sts' in path_lower:
            return 2
        elif 'vts' in path_lower:
            return 3
        else:
            return 4
    
    def check_sts_version(self, suite_plan, suite_build, security_patch, output_lines, output_error):
        detected_version = self.extract_sts_version(suite_build)
        if detected_version:
            patch_status, days_diff = self.check_security_patch_age(security_patch)
            if not patch_status:
                output_error.append(f"❌ 安全补丁时间已超{days_diff}天,请确认是否正确")
            available_versions = self.get_available_sts_versions()
            theoretical_versions = self.get_theoretical_sts_versions(security_patch)
            if detected_version in available_versions:
                pass
            else:
                output_error.append(f"❌ STS工具版本不可用: 检测到 {detected_version}，当前可用范围: {', '.join(available_versions)}")
                output_error.append(f"❌ 安全补丁 {security_patch} 对应的理论工具版本: {', '.join(theoretical_versions)}")
                if detected_version in theoretical_versions:
                    output_error.append(f"❌ 检测到的工具版本 {detected_version} 在安全补丁的理论版本范围内")
                else:
                    output_error.append(f"❌ 检测到的工具版本 {detected_version} 不在安全补丁的理论版本范围内")
        else:
            output_error.append(f"❌ 无法从工具版本 '{suite_build}' 中提取STS版本信息")
    
    def check_security_patch_age(self, security_patch):
        try:
            patch_date = datetime.datetime.strptime(security_patch, "%Y-%m-%d")
            current_date = datetime.datetime.now()
            days_diff = (current_date - patch_date).days
            return (days_diff <= 60, days_diff)
        except Exception:
            return (True, 0)
    
    def get_available_sts_versions(self):
        current_date = datetime.datetime.now()
        current_year = current_date.year
        current_month = current_date.month
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