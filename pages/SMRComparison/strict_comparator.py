import json
from typing import Dict, List, Any


class StrictFeatureComparator:
    """严格Feature JSON文件对比器 - 完全一致才PASS"""
    
    def compare(self, mr_feature_data, smr_feature_data):
        """严格比较两个Feature JSON文件的差异"""
        if mr_feature_data is None or smr_feature_data is None:
            return "无法比较：其中一个文件为空\n"
        
        result_text = "Feature DeviceInfo 严格对比结果:\n"
        result_text += "=" * 70 + "\n"
        
        # 获取features列表
        mr_features = self._get_features_list(mr_feature_data)
        smr_features = self._get_features_list(smr_feature_data)
        
        # 统计总数
        mr_total = len(mr_features) if mr_features else 0
        smr_total = len(smr_features) if smr_features else 0
        
        result_text += f"MR Feature总数: {mr_total}\n"
        result_text += f"SMR Feature总数: {smr_total}\n\n"
        
        # 首先检查整个JSON是否完全一致
        if self._are_json_identical(mr_feature_data, smr_feature_data):
            result_text += "✅ PASS - 两个Feature文件完全相同\n"
            result_text += "请详细查看comparison_reports中生成的html文件\n"
            return result_text
        
        # 如果总数不同，直接报错
        if mr_total != smr_total:
            result_text += f"❌ FAIL - Feature数量不同: MR={mr_total}, SMR={smr_total}\n\n"
        
        # 详细对比每个feature
        result_text += "❌ FAIL - 发现差异\n\n"
        # 添加提示信息
        result_text += "请详细查看comparison_reports中生成的html文件\n"
        return result_text
    
    def _get_features_list(self, data):
        """获取feature列表"""
        if not isinstance(data, dict):
            return None
        return data.get("feature") if isinstance(data.get("feature"), list) else None
    
    def _are_json_identical(self, json1, json2):
        """检查两个JSON是否完全一致（包括顺序）"""
        try:
            # 使用相同的格式和顺序比较
            json_str1 = json.dumps(json1, sort_keys=False, indent=None, ensure_ascii=False)
            json_str2 = json.dumps(json2, sort_keys=False, indent=None, ensure_ascii=False)
            return json_str1 == json_str2
        except:
            return False
    
    def _strict_compare_features(self, mr_features, smr_features):
        """严格对比feature列表"""
        result = ""
        differences_found = False
        
        # 如果其中一个为空
        if not mr_features or not smr_features:
            if not mr_features and smr_features:
                result += "错误: MR feature列表为空\n"
            elif mr_features and not smr_features:
                result += "错误: SMR feature列表为空\n"
            else:
                result += "错误: 两个feature列表都为空\n"
            return result
        
        # 确定对比范围
        max_len = max(len(mr_features), len(smr_features))
        min_len = min(len(mr_features), len(smr_features))
        
        for i in range(max_len):
            if i >= len(mr_features):
                # SMR多出的feature
                result += f"第{i+1}个feature: MR缺失，SMR有\n"
                if i < len(smr_features):
                    feature = smr_features[i]
                    result += f"  SMR feature: name={feature.get('name', '未知')}, "
                    result += f"type={feature.get('type', 'N/A')}, "
                    result += f"available={feature.get('available', 'N/A')}\n"
                differences_found = True
                continue
                
            if i >= len(smr_features):
                # MR多出的feature
                result += f"第{i+1}个feature: SMR缺失，MR有\n"
                feature = mr_features[i]
                result += f"  MR feature: name={feature.get('name', '未知')}, "
                result += f"type={feature.get('type', 'N/A')}, "
                result += f"available={feature.get('available', 'N/A')}\n"
                differences_found = True
                continue
            
            # 两个文件都有这个位置，对比内容
            mr_feature = mr_features[i]
            smr_feature = smr_features[i]
            
            # 首先检查是否为同一个feature（通过name判断）
            mr_name = mr_feature.get('name', f'未命名_{i}')
            smr_name = smr_feature.get('name', f'未命名_{i}')
            
            if mr_name != smr_name:
                result += f"第{i+1}个feature: 名称不同\n"
                result += f"  MR: {mr_name}\n"
                result += f"  SMR: {smr_name}\n"
                differences_found = True
                # 继续检查其他差异
            
            # 对比feature内容
            feature_diffs = self._compare_single_feature(mr_feature, smr_feature, i+1)
            if feature_diffs:
                if mr_name == smr_name:
                    result += f"第{i+1}个feature ({mr_name}): 内容不同\n"
                result += feature_diffs
                differences_found = True
        
        if not differences_found and len(mr_features) == len(smr_features):
            result += "✅ 所有feature内容相同\n"
        
        return result
    
    def _compare_single_feature(self, mr_feature, smr_feature, index):
        """对比单个feature的内容"""
        if not isinstance(mr_feature, dict) or not isinstance(smr_feature, dict):
            return f"  第{index}个feature: 类型错误\n"
        
        result = ""
        all_keys = set(mr_feature.keys()) | set(smr_feature.keys())
        
        for key in sorted(all_keys):
            if key not in mr_feature:
                result += f"    MR缺失字段: {key} = {smr_feature.get(key)}\n"
            elif key not in smr_feature:
                result += f"    SMR缺失字段: {key} = {mr_feature.get(key)}\n"
            else:
                mr_value = mr_feature[key]
                smr_value = smr_feature[key]
                
                # 比较值
                if not self._values_equal(mr_value, smr_value):
                    result += f"    字段 {key} 不同:\n"
                    result += f"      MR: {self._format_value(mr_value)}\n"
                    result += f"      SMR: {self._format_value(smr_value)}\n"
        
        return result
    
    def _values_equal(self, val1, val2):
        """比较两个值是否相等"""
        # 处理None
        if val1 is None and val2 is None:
            return True
        if val1 is None or val2 is None:
            return False
        
        # 处理基本类型
        if type(val1) != type(val2):
            return False
        
        # 处理字典和列表
        if isinstance(val1, dict) and isinstance(val2, dict):
            return self._are_json_identical(val1, val2)
        elif isinstance(val1, list) and isinstance(val2, list):
            if len(val1) != len(val2):
                return False
            return all(self._values_equal(v1, v2) for v1, v2 in zip(val1, val2))
        else:
            return val1 == val2
    
    def _format_value(self, value):
        """格式化值用于显示"""
        if value is None:
            return "null"
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)[:100] + ("..." if len(json.dumps(value, ensure_ascii=False)) > 100 else "")
        return str(value)