from typing import List

def normalize_cts_module(module: str) -> str:
    """安全标准化模块名（保留参数）"""
    try:
        # 分割架构前缀和模块主体
        parts = module.split(" ", 1)
        # 保留模块主体（包含参数）
        base_module = parts[1] if len(parts) > 1 else parts[0]
        # 移除前后空白但保留所有参数
        normalized = base_module.strip()
        return normalized
    except Exception as e:
        return module

def compare_files(new_modules: List[str], old_modules: List[str], new_file_path: str = "", old_file_path: str = "") -> dict:
    """增强型模块差异对比分析，返回对比结果字典"""
    try:
        result = {}
        
        # 检查文件类型
        new_is_xml = new_file_path.lower().endswith('.xml') if new_file_path else False
        old_is_xml = old_file_path.lower().endswith('.xml') if old_file_path else False
        
        # 如果两个文件都是XML，计算独有模块和相同模块
        if new_is_xml and old_is_xml:
            # 计算独有模块
            old_unique = set(old_modules) - set(new_modules)
            new_unique = set(new_modules) - set(old_modules)
            
            # 计算相同模块
            same_modules = set(old_modules) & set(new_modules)
            
            # 构建相同测试项的格式化字符串
            same_text = "=== 相同测试项 ===\n"
            same_text += f"相同测试项({len(same_modules)}个):\n"
            for i, module in enumerate(sorted(same_modules), 1):
                same_text += f"{i}. {module}\n"
            
            # 构建XML专用结果
            result = {
                'old_raw': sorted(old_unique),
                'new_raw': sorted(new_unique),
                'old_clean': [],
                'new_clean': [],
                'old_command': same_text,  # 将相同测试项字符串赋值给命令
                'new_command': same_text,  # 将相同测试项字符串赋值给命令
                'same_modules': sorted(same_modules),
                'is_xml_comparison': True
            }
            
            return result
        
        # 原始差异集计算
        diff_old = set(old_modules) - set(new_modules)
        diff_new = set(new_modules) - set(old_modules)
        
        # 标准化处理
        diff_old_clean = {normalize_cts_module(m) for m in diff_old}
        diff_new_clean = {normalize_cts_module(m) for m in diff_new}
        
        # 标准化后差异集
        diff_old_remove_arch = diff_old_clean - diff_new_clean
        diff_new_remove_arch = diff_new_clean - diff_old_clean
        
        # 旧文件差异对比
        lost_old = diff_old - {m for m in diff_old if normalize_cts_module(m) in diff_old_remove_arch}
        
        # 新文件差异对比
        lost_new = diff_new - {m for m in diff_new if normalize_cts_module(m) in diff_new_remove_arch}
        
        # 生成过滤命令
        old_command = ' '.join(f"--include-filter {m}" for m in sorted(diff_old_remove_arch)) or "无"
        new_command = ' '.join(f"--include-filter {m}" for m in sorted(diff_new_remove_arch)) or "无"
        
        # 构建结果字典
        result = {
            'old_raw': sorted(diff_old),
            'new_raw': sorted(diff_new),
            'old_clean': sorted(diff_old_remove_arch),
            'new_clean': sorted(diff_new_remove_arch),
            'old_command': old_command,
            'new_command': new_command,
            'is_xml_comparison': False
        }
        
        return result

    except Exception as e:
        raise