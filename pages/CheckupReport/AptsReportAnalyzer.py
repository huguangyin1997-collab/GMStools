import os
import re
import xml.etree.ElementTree as ET

class AptsReportAnalyzer:
    """APTS报告分析器（仅处理旧版XML格式）"""
    
    def __init__(self):
        self.apts_result_path = []
        self.Suite_Plan_comparison = []
        self.Fingerprint_comparison = []
        self.Security_Patch_comparison = []
        self.tool_versions = []
        self.ReportDelimiter = "=" * 100
    
    def analyze_apts_reports(self, pathnames, output_lines, output_error):
        """分析APTS报告（仅XML格式）"""
        # 清空列表
        self.apts_result_path.clear()
        self.Suite_Plan_comparison.clear()
        self.Fingerprint_comparison.clear()
        self.Security_Patch_comparison.clear()
        self.tool_versions.clear()

        # 仅查找标准的XML格式APTS报告（路径含test_approval，文件名test_result.xml）
        for path in pathnames:
            if "test_approval" in path and "test_result.xml" in path:
                self.apts_result_path.append(path)

        if not self.apts_result_path:
            output_error.append("❌ 未找到APTS报告 请确认目录中是否包含APTS测试结果文件")
            
        # 处理XML报告
        for file_path in self.apts_result_path:
            try:
                self._parse_xml_apts_report(file_path, output_lines, output_error)
            except Exception as e:
                output_error.append(f"❌ 处理APTS报告文件时出错 {file_path}: {str(e)}请确认文件格式是否正确")
        
        return output_lines, output_error
    
    def _parse_xml_apts_report(self, xml_file, output_lines, output_error):
        """解析XML格式的APTS报告"""
        with open(xml_file, 'r', encoding="utf-8") as xmlf:
            xml_content = xmlf.read()
        
        root = ET.fromstring(xml_content)
        
        suite_name = root.get('suite_name', '')
        suite_plan = root.get('suite_plan', '')
        suite_version = root.get('suite_version', '')
        Suite_Plan = f"{suite_name} / {suite_plan}"
        self.Suite_Plan_comparison.append(Suite_Plan)
        
        summary = root.find('Summary')
        Tests_Passed = summary.get('pass', '0') if summary is not None else '0'
        Tests_Failed = summary.get('failed', '0') if summary is not None else '0'
        Warning_Count = summary.get('warning', '0') if summary is not None else '0'
        Modules_Done = summary.get('modules_done', '0') if summary is not None else '0'
        Modules_Total = summary.get('modules_total', '0') if summary is not None else '0'
        
        build = root.find('Build')
        Fingerprint = build.get('build_fingerprint', '') if build is not None else ''
        self.Fingerprint_comparison.append(Fingerprint)
        Security_Patch = build.get('build_version_security_patch', '') if build is not None else ''
        self.Security_Patch_comparison.append(Security_Patch)
        
        apts_version = self.extract_apts_version_from_summary(xml_file)
        
        output_lines.append("测试工具:\t%s" % Suite_Plan)
        output_lines.append("工具版本:\t%s" % (apts_version if apts_version else suite_version))
        output_lines.append("PASS数:\t%s" % Tests_Passed)
        output_lines.append("FAIL数:\t%s" % Tests_Failed)
        output_lines.append("Warning数:\t%s" % Warning_Count)
        output_lines.append("模块完成:\t%s" % Modules_Done)
        output_lines.append("模块总数:\t%s" % Modules_Total)
        output_lines.append("Fingerprint:\t%s" % Fingerprint)
        output_lines.append("安全补丁:\t%s" % Security_Patch)
        
        tool_type = "APTS"
        tool_name = suite_plan
        version_num = apts_version if apts_version else suite_version
        build_num = self.extract_build_number_from_version(version_num)
        self.tool_versions.append((tool_type, tool_name, version_num, build_num))
        
        try:
            failed_count = int(Tests_Failed)
            if failed_count > 0:
                output_error.append(f"❌ {Suite_Plan} 有 {failed_count} 个测试失败，请检查")
        except ValueError:
            pass
        
        if Modules_Done != Modules_Total:
            output_error.append(f"❌ {Suite_Plan}的模块数量不完整，请检查")
        
        try:
            warning_count = int(Warning_Count)
            if warning_count > 0:
                output_error.append(f"❌ {Suite_Plan} 有 {warning_count} 个警告，请关注")
        except ValueError:
            pass
        
        output_lines.append(self.ReportDelimiter)
    
    def extract_apts_version_from_summary(self, xml_file_path):
        """从同目录的summary.txt文件中提取APTS版本信息"""
        try:
            xml_dir = os.path.dirname(xml_file_path)
            summary_file_path = os.path.join(xml_dir, "summary.txt")
            if not os.path.exists(summary_file_path):
                return None
            with open(summary_file_path, 'r', encoding='utf-8') as f:
                summary_content = f.read()
            apts_version_pattern = r"APTS Version\s*:\s*(.+)"
            match = re.search(apts_version_pattern, summary_content)
            return match.group(1).strip() if match else None
        except Exception:
            return None
    
    def extract_build_number_from_version(self, version_string):
        """从版本字符串中提取构建号"""
        if not version_string:
            return "0"
        try:
            build_pattern = r'\((\d+)\)'
            match = re.search(build_pattern, version_string)
            if match:
                return match.group(1)
            digits_pattern = r'\b(\d+)\b'
            matches = re.findall(digits_pattern, version_string)
            if matches:
                return max(matches, key=len)
        except Exception:
            pass
        return "0"
    
    def get_tool_versions(self):
        return self.tool_versions