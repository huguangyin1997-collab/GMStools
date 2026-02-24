# Package_models.py
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple


class PackageChangeType(Enum):
    """变更类型"""
    SAME = "same"           # 相同
    MODIFIED = "modified"   # 修改
    ADDED = "added"         # 新增
    REMOVED = "removed"     # 删除


@dataclass
class PackageChange:
    """包变更信息"""
    change_type: PackageChangeType
    package_name: str
    old_package: Optional[Dict]
    new_package: Optional[Dict]
    differences: List[Tuple[str, Any, Any]] = None  # 字段名, 旧值, 新值
    old_index: Optional[int] = None
    new_index: Optional[int] = None
    
    def __post_init__(self):
        if self.differences is None:
            self.differences = []


@dataclass
class PackageComparisonResult:
    """包比较结果"""
    is_identical: bool
    status: str
    summary: Dict[str, int]
    changes: List[PackageChange]
    old_file_stats: Dict[str, Any]
    new_file_stats: Dict[str, Any]
    old_packages: List[Dict]
    new_packages: List[Dict]
    comparison_text: str = ""