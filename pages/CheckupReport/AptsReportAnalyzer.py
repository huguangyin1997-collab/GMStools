import os
import re
import datetime
import xml.etree.ElementTree as ET

# ============================ APTS报告分析器 ============================

class AptsReportAnalyzer:
    """APTS报告分析器"""
    
    def __init__(self):
        self.apts_result_path = []
        self.Suite_Plan_comparison = []
        self.Fingerprint_comparison = []
        self.Security_Patch_comparison = []
        # 新增：存储工具版本信息
        self.tool_versions = []  # 格式: (工具类型, 工具名称, 版本号, 构建号)
    
    def analyze_apts_reports(self, pathnames, output_lines, output_error):
        """分析APTS报告"""
        ReportDelimiter = "=" * 100

        # 简化的APTS报告查找逻辑 - 专注于匹配包含test_approval的路径
        for path in pathnames:
            # 检查路径是否包含test_approval并且包含test_result.xml
            if "test_approval" in path and "test_result.xml" in path:
                self.apts_result_path.append(path)
        
        # 如果没有找到APTS报告，输出调试信息
        if not self.apts_result_path:
            output_error.append("❌ 未找到APTS报告 请确认目录中是否包含APTS测试结果文件")
            
        # 访问结果绝对路径并解析XML信息
        for j in self.apts_result_path:
            try:
                with open(j, 'r', encoding="utf-8") as xmlf:
                    xml_content = xmlf.read()
                
                # 解析XML内容
                root = ET.fromstring(xml_content)
                
                # 提取基本信息
                suite_name = root.get('suite_name', '')
                suite_plan = root.get('suite_plan', '')
                suite_version = root.get('suite_version', '')
                
                Suite_Plan = f"{suite_name} / {suite_plan}"
                self.Suite_Plan_comparison.append(Suite_Plan)
                
                # 提取Summary信息
                summary = root.find('Summary')
                Tests_Passed = summary.get('pass', '0') if summary is not None else '0'
                Tests_Failed = summary.get('failed', '0') if summary is not None else '0'
                Warning_Count = summary.get('warning', '0') if summary is not None else '0'
                Modules_Done = summary.get('modules_done', '0') if summary is not None else '0'
                Modules_Total = summary.get('modules_total', '0') if summary is not None else '0'
                
                # 提取Build信息
                build = root.find('Build')
                Fingerprint = build.get('build_fingerprint', '') if build is not None else ''
                self.Fingerprint_comparison.append(Fingerprint)
                Security_Patch = build.get('build_version_security_patch', '') if build is not None else ''
                self.Security_Patch_comparison.append(Security_Patch)
                
                # 从同目录的summary.txt文件中提取APTS版本信息
                apts_version = self.extract_apts_version_from_summary(j)
                
                # 使用制表符对齐 - 与其他分析器保持一致
                output_lines.append("测试工具:\t%s" % Suite_Plan)
                output_lines.append("工具版本:\t%s" % apts_version if apts_version else suite_version)
                output_lines.append("PASS数:\t%s" % Tests_Passed)
                output_lines.append("FAIL数:\t%s" % Tests_Failed)
                output_lines.append("Warning数:\t%s" % Warning_Count)
                output_lines.append("模块完成:\t%s" % Modules_Done)
                output_lines.append("模块总数:\t%s" % Modules_Total)
                output_lines.append("Fingerprint:\t%s" % Fingerprint)
                output_lines.append("安全补丁:\t%s" % Security_Patch)
                
                # 新增：收集APTS版本信息
                tool_type = "APTS"
                tool_name = suite_plan
                
                # 使用从summary.txt中提取的版本号，如果没有则使用XML中的版本号
                version_num = apts_version if apts_version else suite_version
                build_num = self.extract_build_number_from_version(version_num)
                
                self.tool_versions.append((tool_type, tool_name, version_num, build_num))
                
                # 检查FAIL数是否为0
                try:
                    failed_count = int(Tests_Failed)
                    if failed_count > 0:
                        output_error.append(f"❌ {Suite_Plan} 有 {failed_count} 个测试失败，请检查")
                except ValueError:
                    pass
                
                # 检查模块数量是否完整
                if Modules_Done != Modules_Total:
                    output_error.append(f"❌ {Suite_Plan}的模块数量不完整，请检查")
                
                # 检查Warning数是否过多
                try:
                    warning_count = int(Warning_Count)
                    if warning_count > 0:
                        output_error.append(f"❌ {Suite_Plan} 有 {warning_count} 个警告，请关注")
                except ValueError:
                    pass
                
                output_lines.append(ReportDelimiter)
                
            except Exception as e:
                output_error.append(f"❌ 处理APTS报告文件时出错 {j}: {str(e)}请确认文件格式是否正确")
        
        return output_lines, output_error
    
    def extract_apts_version_from_summary(self, xml_file_path):
        """从同目录的summary.txt文件中提取APTS版本信息"""
        try:
            # 获取xml文件所在目录
            xml_dir = os.path.dirname(xml_file_path)
            summary_file_path = os.path.join(xml_dir, "summary.txt")
            
            # 检查summary.txt文件是否存在
            if not os.path.exists(summary_file_path):
                print(f"未找到summary.txt文件: {summary_file_path}")
                return None
            
            # 读取summary.txt文件内容
            with open(summary_file_path, 'r', encoding='utf-8') as f:
                summary_content = f.read()
            
            # 使用正则表达式提取APTS版本信息
            # 匹配格式: "APTS Version         : APTS - Go variant (11771464)"
            apts_version_pattern = r"APTS Version\s*:\s*(.+)"
            match = re.search(apts_version_pattern, summary_content)
            
            if match:
                apts_version = match.group(1).strip()
                # print(f"从summary.txt中提取到APTS版本: {apts_version}")
                return apts_version
            else:
                print("在summary.txt中未找到APTS版本信息")
                return None
                
        except Exception as e:
            print(f"提取APTS版本信息时出错: {e}")
            return None
    
    def extract_build_number_from_version(self, version_string):
        """从版本字符串中提取构建号"""
        if not version_string:
            return "0"
        
        try:
            # 尝试从括号中提取构建号，例如："APTS - Go variant (11771464)" -> "11771464"
            build_pattern = r'\((\d+)\)'
            match = re.search(build_pattern, version_string)
            
            if match:
                return match.group(1)
            
            # 如果括号中没有找到，尝试提取纯数字
            digits_pattern = r'\b(\d+)\b'
            matches = re.findall(digits_pattern, version_string)
            
            if matches:
                # 返回最大的数字（通常是构建号）
                return max(matches, key=len)
            
        except Exception:
            pass
        
        return "0"
    
    def get_tool_versions(self):
        """获取工具版本信息"""
        return self.tool_versions