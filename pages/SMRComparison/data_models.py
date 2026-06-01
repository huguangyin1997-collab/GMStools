from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple, Optional


class data_modelsChangeType(Enum):
    """变更类型"""
    SAME = "same"           # 相同
    MOVED = "moved"         # 移动（位置变化）
    MODIFIED = "modified"   # 修改
    ADDED = "added"         # 新增
    REMOVED = "removed"     # 删除


@dataclass
class FeatureItem:
    """功能项"""
    index: int
    name: str
    data: Dict[str, Any]
    
    def get(self, key: str, default=None):
        """获取字段值"""
        return self.data.get(key, default)
    
    def to_json(self) -> str:
        """转换为格式化的JSON字符串"""
        import json
        return json.dumps(self.data, indent=2, ensure_ascii=False)


@dataclass
class FeatureChange:
    """功能变更"""
    change_type: data_modelsChangeType
    old_item: Optional[FeatureItem]
    new_item: Optional[FeatureItem]
    old_index: Optional[int] = None
    new_index: Optional[int] = None
    changes: List[Tuple[str, Any, Any]] = None  # 字段名, 旧值, 新值
    
    def __post_init__(self):
        if self.changes is None:
            self.changes = []
        
        # 确保索引被正确设置
        if self.old_item and self.old_index is None:
            self.old_index = self.old_item.index
        if self.new_item and self.new_index is None:
            self.new_index = self.new_item.index


@dataclass
class ComparisonResult:
    """比较结果数据结构"""
    is_identical: bool
    status: str
    summary: Dict[str, int]  # 各类变更的统计
    changes: List[FeatureChange]  # 所有变更
    old_features: List[Dict[str, Any]]  # 旧文件完整功能列表
    new_features: List[Dict[str, Any]]  # 新文件完整功能列表