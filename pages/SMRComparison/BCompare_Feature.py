from datetime import datetime
from pathlib import Path
from .strict_comparator import StrictFeatureComparator
from .smart_comparator import SmartFeatureComparator
from .html_generator import HTMLReportGenerator


class FeatureComparator:
    """Feature JSON文件对比器 (始终生成智能对比HTML报告)"""
    
    def __init__(self):
        self.strict_comparator = StrictFeatureComparator()
        self.smart_comparator = SmartFeatureComparator()
        self.html_generator = HTMLReportGenerator()
    
    def compare(self, mr_feature_data, smr_feature_data):
        """比较两个Feature JSON文件的差异"""
        # 首先生成严格对比的文本结果
        result_text = self.strict_comparator.compare(mr_feature_data, smr_feature_data)
        
        # 无论严格对比结果是否一致，都生成智能对比的HTML报告
        output_dir = Path.cwd() / "comparison_reports"
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"Feature_Smart_Comparison_{timestamp}.html"
        
        try:
            # 使用智能对比算法进行分析
            smart_result = self.smart_comparator.smart_compare(
                mr_feature_data, 
                smr_feature_data
            )
            
            # 生成HTML报告
            self.html_generator.generate_html_report(smart_result, str(output_path))
            
            # 在文本结果中添加HTML报告信息
            result_text += f"\n📝 智能对比HTML报告已生成: {output_path}\n"
            result_text += "   请用浏览器打开查看详细对比结果\n"
            
            # 如果严格对比是PASS，但智能对比可能显示移动等变化
            if "✅ PASS" in result_text:
                summary = smart_result.summary
                if summary['moved'] > 0:
                    result_text += f"\n📌 注意: 虽然文件内容相同，但检测到 {summary['moved']} 个功能项位置有变化\n"
            
        except Exception as e:
            result_text += f"\n⚠️  智能对比HTML报告生成失败: {str(e)}\n"
        
        return result_text
    
    def strict_compare_only(self, mr_feature_data, smr_feature_data):
        """仅进行严格对比"""
        return self.strict_comparator.compare(mr_feature_data, smr_feature_data)
    
    def smart_compare_only(self, mr_feature_data, smr_feature_data, output_path=None):
        """仅进行智能对比"""
        try:
            # 使用智能对比算法进行分析
            smart_result = self.smart_comparator.smart_compare(
                mr_feature_data, 
                smr_feature_data
            )
            
            if output_path:
                # 生成HTML报告
                html_content = self.html_generator.generate_html_report(
                    smart_result, 
                    output_path
                )
                return smart_result, html_content
            else:
                return smart_result
            
        except Exception as e:
            raise Exception(f"智能对比失败: {str(e)}")