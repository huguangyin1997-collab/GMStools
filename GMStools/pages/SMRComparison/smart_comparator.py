import json
import difflib
from typing import Dict, List, Any, Tuple, Optional, Set
from .data_models import data_modelsChangeType, FeatureItem, FeatureChange, ComparisonResult


class SmartFeatureComparator:
    """智能Feature对比器 - 使用BCompare算法进行智能对比"""
    
    def __init__(self):
        pass
    
    def smart_compare(self, mr_feature_data, smr_feature_data):
        """使用BCompare算法进行智能对比，返回ComparisonResult对象"""
        
        # 获取features列表
        mr_features = self._get_features_list(mr_feature_data)
        smr_features = self._get_features_list(smr_feature_data)
        
        if not mr_features or not smr_features:
            raise ValueError("无法获取feature列表")
        
        # 创建FeatureItem列表
        mr_items = []
        for i, feature in enumerate(mr_features):
            name = feature.get('name', f'未知_{i}')
            mr_items.append(FeatureItem(index=i, name=name, data=feature))
        
        smr_items = []
        for i, feature in enumerate(smr_features):
            name = feature.get('name', f'未知_{i}')
            smr_items.append(FeatureItem(index=i, name=name, data=feature))
        
        # 使用BCompare算法构建映射
        changes = self._build_mapping(mr_items, smr_items)
        
        # 统计各类变更
        summary = {
            "same": 0,
            "moved": 0,
            "modified": 0,
            "added": 0,
            "removed": 0
        }
        
        for change in changes:
            if change.change_type == data_modelsChangeType.SAME:
                summary["same"] += 1
            elif change.change_type == data_modelsChangeType.MOVED:
                summary["moved"] += 1
            elif change.change_type == data_modelsChangeType.MODIFIED:
                summary["modified"] += 1
            elif change.change_type == data_modelsChangeType.ADDED:
                summary["added"] += 1
            elif change.change_type == data_modelsChangeType.REMOVED:
                summary["removed"] += 1
        
        # 检查是否完全相同
        is_identical = (summary["same"] == len(mr_items) == len(smr_items))
        
        # 创建比较结果
        result = ComparisonResult(
            is_identical=is_identical,
            status="PASS" if is_identical else "FAIL",
            summary=summary,
            changes=changes,
            old_features=mr_features,
            new_features=smr_features
        )
        
        return result
    
    def _get_features_list(self, data):
        """获取feature列表"""
        if not isinstance(data, dict):
            return None
        return data.get("feature") if isinstance(data.get("feature"), list) else None
    
    def _compare_values(self, value1: Any, value2: Any) -> bool:
        """比较两个值是否相同"""
        if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
            return value1 == value2
        return value1 == value2
    
    def _compare_items(self, item1: FeatureItem, item2: FeatureItem) -> List[Tuple[str, Any, Any]]:
        """比较两个功能项的差异"""
        changes = []
        
        # 获取所有字段
        all_keys = set(item1.data.keys()) | set(item2.data.keys())
        
        for key in sorted(all_keys):
            value1 = item1.data.get(key)
            value2 = item2.data.get(key)
            
            # 检查是否存在差异
            if value1 is None and value2 is not None:
                changes.append((key, None, value2))
            elif value1 is not None and value2 is None:
                changes.append((key, value1, None))
            elif not self._compare_values(value1, value2):
                changes.append((key, value1, value2))
        
        return changes
    
    def _find_best_match(self, old_item: FeatureItem, new_items: List[FeatureItem], 
                        matched_new_indices: Set[int]) -> Optional[Tuple[int, List[Tuple[str, Any, Any]]]]:
        """为旧项在新列表中寻找最佳匹配"""
        best_match = None
        best_score = -1
        
        for j, new_item in enumerate(new_items):
            if j in matched_new_indices:
                continue
            
            # 如果名称相同，直接匹配
            if old_item.name == new_item.name:
                changes = self._compare_items(old_item, new_item)
                return (j, changes)
            
            # 计算相似度得分
            score = self._calculate_similarity(old_item, new_item)
            if score > best_score:
                best_score = score
                best_match = (j, self._compare_items(old_item, new_item))
        
        # 如果相似度足够高，则匹配
        if best_score > 0.5:  # 阈值可以根据需要调整
            return best_match
        
        return None
    
    def _calculate_similarity(self, item1: FeatureItem, item2: FeatureItem) -> float:
        """计算两个功能项的相似度"""
        score = 0.0
        
        # 名称相似度（使用difflib的序列匹配器）
        name_similarity = difflib.SequenceMatcher(None, item1.name, item2.name).ratio()
        score += name_similarity * 0.3
        
        # 类型相似度
        type1 = item1.get('type')
        type2 = item2.get('type')
        if type1 == type2:
            score += 0.2
        
        # 可用性相似度
        available1 = item1.get('available')
        available2 = item2.get('available')
        if available1 == available2:
            score += 0.2
        
        # 其他字段相似度
        common_keys = set(item1.data.keys()) & set(item2.data.keys())
        for key in common_keys:
            if key not in ['name', 'type', 'available']:
                if self._compare_values(item1.data[key], item2.data[key]):
                    score += 0.1
        
        return min(score, 1.0)
    
    def _build_mapping(self, old_items: List[FeatureItem], new_items: List[FeatureItem]) -> List[FeatureChange]:
        """构建新旧文件的映射关系（BCompare算法）"""
        changes = []
        
        # 已经匹配的索引
        matched_old_indices = set()
        matched_new_indices = set()
        
        # 第一阶段：匹配位置相同且内容相同的项
        for i in range(min(len(old_items), len(new_items))):
            old_item = old_items[i]
            new_item = new_items[i]
            
            if old_item.name == new_item.name:
                diff = self._compare_items(old_item, new_item)
                if not diff:
                    changes.append(FeatureChange(
                        change_type=data_modelsChangeType.SAME,
                        old_item=old_item,
                        new_item=new_item
                    ))
                    matched_old_indices.add(i)
                    matched_new_indices.add(i)
        
        # 第二阶段：匹配名称相同但位置不同的项
        for i, old_item in enumerate(old_items):
            if i in matched_old_indices:
                continue
            
            # 查找名称相同的新项
            for j, new_item in enumerate(new_items):
                if j in matched_new_indices:
                    continue
                
                if old_item.name == new_item.name:
                    diff = self._compare_items(old_item, new_item)
                    
                    if not diff:
                        change_type = data_modelsChangeType.MOVED
                    else:
                        change_type = data_modelsChangeType.MODIFIED
                    
                    changes.append(FeatureChange(
                        change_type=change_type,
                        old_item=old_item,
                        new_item=new_item,
                        changes=diff
                    ))
                    matched_old_indices.add(i)
                    matched_new_indices.add(j)
                    break
        
        # 第三阶段：匹配相似的项（BCompare的智能匹配）
        for i, old_item in enumerate(old_items):
            if i in matched_old_indices:
                continue
            
            best_match = self._find_best_match(old_item, new_items, matched_new_indices)
            if best_match:
                j, diff = best_match
                new_item = new_items[j]
                
                if not diff:
                    change_type = data_modelsChangeType.MOVED
                else:
                        change_type = data_modelsChangeType.MODIFIED
                
                changes.append(FeatureChange(
                    change_type=change_type,
                    old_item=old_item,
                    new_item=new_item,
                    changes=diff
                ))
                matched_old_indices.add(i)
                matched_new_indices.add(j)
        
        # 第四阶段：处理未匹配的项
        # 删除的项（在旧文件中但不在新文件中）
        for i, old_item in enumerate(old_items):
            if i not in matched_old_indices:
                changes.append(FeatureChange(
                    change_type=data_modelsChangeType.REMOVED,
                    old_item=old_item,
                    new_item=None
                ))
        
        # 新增的项（在新文件中但不在旧文件中）
        for j, new_item in enumerate(new_items):
            if j not in matched_new_indices:
                changes.append(FeatureChange(
                    change_type=data_modelsChangeType.ADDED,
                    old_item=None,
                    new_item=new_item
                ))
        
        return changes