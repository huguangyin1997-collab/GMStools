import os
from .file_utils import check_file_extension
from .comparison_utils import compare_files

class ComparisonEngine:
    """比较引擎"""
    
    def __init__(self):
        pass
    
    def perform_comparison(self, old_file_path, new_file_path):
        """执行文件比较"""
        if not old_file_path or not new_file_path:
            return None
        
        if not os.path.exists(old_file_path) or not os.path.exists(new_file_path):
            return None
        
        try:
            old_modules = check_file_extension(old_file_path)
            new_modules = check_file_extension(new_file_path)
            return compare_files(new_modules, old_modules, new_file_path, old_file_path)
        except Exception:
            return None
    
    def format_same_modules_text(self, same_modules):
        """格式化相同模块文本"""
        if not same_modules:
            return ""
        
        same_text = f"相同测试项({len(same_modules)}个):\n"
        for i, module in enumerate(same_modules, 1):
            same_text += f"{i}. {module}\n"
        return same_text