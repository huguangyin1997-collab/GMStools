import os
import re
import datetime


# ============================ CV报告分析器 ============================

class CVReportAnalyzer:
    """CV报告分析器"""
    
    def __init__(self):
        self.cv_test_result = []
        self.Suite_Plan_comparison = []
        self.Fingerprint_comparison = []
        self.Security_Patch_comparison = []
        # 新增：存储工具版本信息
        self.tool_versions = []  # 格式: (工具类型, 工具名称, 版本号, 构建号)
    
    def analyze_cv_reports(self, pathnames, output_lines, output_error):
        """分析CV报告"""
        cv_status = False
        ReportDelimiter = "=" * 100
        cv_timeout_reports = []
        
        # 检测CV报告
        for j in pathnames:
            if "CTS_VERIFIER" in j:
                cv_time_match = re.findall("(.*?)-CTS_VERIFIER", j)
                if cv_time_match and len(cv_time_match[0]) >= 19:
                    cv_time = cv_time_match[0][-19:]
                    if "test_result.xml" in j:
                        cv_status = True
                        self.cv_test_result.append(str(j))
                        output_lines.append(f"CV报告导出时间：{cv_time}")
                        
                        # 检查报告时间是否超过5天
                        CVTime = (re.findall("(.*?)_", cv_time))[0].replace(".", "-")
                        CVTime = datetime.datetime.strptime(CVTime, "%Y-%m-%d")
                        TimeDiffer = (datetime.datetime.now() - CVTime).days
                        if TimeDiffer > 5:
                            cv_timeout_reports.append(cv_time)
        
        # 如果有超时的报告，只输出一次错误信息
        if cv_timeout_reports:
            output_error.append("❌ CV报告时间已超5天,请确认是否正确")
        
        if not cv_status:
            output_error.append("❌ 未找到详细CV报告！！！")
            # 如果没有找到CV报告，直接返回
            return output_lines, output_error
        
        # 访问CV报告路径test_result
        for i in self.cv_test_result:
            try:
                with open(i, 'r', encoding="utf-8") as htmlf:
                    htmlcont = htmlf.read().replace("\\n", "")
                
                suite_name = re.findall('suite_name="(.*?)"', htmlcont)
                suite_plan = re.findall('suite_plan="(.*?)"', htmlcont)
                
                if suite_name and suite_plan:
                    Suite_Plan = suite_name[0] + " / " + suite_plan[0]
                    self.Suite_Plan_comparison.append(Suite_Plan)
                    
                    suite_version = re.findall('suite_version="(.*?)"', htmlcont)[0]
                    suite_build_number = re.findall('suite_build_number="(.*?)"', htmlcont)
                    Summary_pass = re.findall('Summary pass="(.*?)"', htmlcont)[0]
                    Failed = re.findall('failed="(.*?)"', htmlcont)[0]
                    modules_done = re.findall('modules_done="(.*?)"', htmlcont)[0]
                    modules_total = re.findall('modules_total="(.*?)"', htmlcont)[0]
                    build_fingerprint = re.findall('build_fingerprint="(.*?)"', htmlcont)[0]
                    self.Fingerprint_comparison.append(build_fingerprint)
                    build_version_security_patch = re.findall('build_version_security_patch="(.*?)"', htmlcont)[0]
                    self.Security_Patch_comparison.append(build_version_security_patch)
                    
                    # 使用制表符对齐
                    output_lines.append("测试工具:\t\t%s" % Suite_Plan)
                    
                    # 处理工具版本显示 - 总是显示完整版本信息
                    if suite_build_number:
                        # 总是显示版本号/构建号，即使构建号为0
                        tool_version_display = f"{suite_version} / {suite_build_number[0]}"
                    else:
                        # 如果没有构建号，只显示版本号
                        tool_version_display = suite_version
                    
                    output_lines.append("工具版本:\t%s" % tool_version_display)
                    output_lines.append("PASS数:\t%s" % Summary_pass)
                    output_lines.append("FAIL数:\t%s" % Failed)
                    output_lines.append("模块完成:\t%s" % modules_done)
                    output_lines.append("模块总数:\t%s" % modules_total)
                    output_lines.append("Fingerprint:\t%s" % build_fingerprint)
                    output_lines.append("安全补丁:\t%s" % build_version_security_patch)
                    
                    # 新增：收集CTS_VERIFIER版本信息
                    tool_type = "CTS_VERIFIER"  # 单独的工具类型
                    tool_name = suite_plan[0]
                    
                    # 解析版本号和构建号
                    version_num = suite_version
                    build_num = suite_build_number[0] if suite_build_number else "0"
                    
                    self.tool_versions.append((tool_type, tool_name, version_num, build_num))
                    
                    # 检查FAIL数是否为0
                    try:
                        failed_count = int(Failed)
                        if failed_count > 0:
                            output_error.append(f"❌ {Suite_Plan} 有 {failed_count} 个测试失败，请检查")
                    except ValueError:
                        pass
                    
                    if modules_done != modules_total:
                        output_error.append(f"❌ {Suite_Plan}的模块数量不完整，请检查")
                    
                    # 每个CV报告分析完成后添加分隔符
                    output_lines.append(ReportDelimiter)
                    
            except Exception as e:
                output_error.append(f"❌ 处理CV报告时出错 {i}: {str(e)}")
        
        return output_lines, output_error
