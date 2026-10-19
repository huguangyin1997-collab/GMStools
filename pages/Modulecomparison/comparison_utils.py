from typing import List

# 已知架构前缀，模块名前面的ABI前缀应被移除，
# 使同一模块的不同架构版本（如 arm64-v8a / armeabi-v7a）视为同一个模块
ABI_PREFIXES = (
    'arm64-v8a', 'armeabi-v7a', 'armeabi',
    'x86_64', 'x86',
    'mips64', 'mips',
    'riscv64',
)

def split_abi_prefix(module: str):
    """拆分模块名中的架构前缀，返回 (abi, 模块主体)。
    无架构前缀时 abi 为 None"""
    try:
        normalized = module.strip()
        for abi in ABI_PREFIXES:
            prefix = abi + ' '
            if normalized.startswith(prefix):
                return abi, normalized[len(prefix):].strip()
        return None, normalized
    except Exception:
        return None, module

def normalize_cts_module(module: str) -> str:
    """标准化模块名（移除架构前缀，保留模块主体及参数）
    如 'arm64-v8a AconfigPublicApiCtsTests' 与 'armeabi-v7a AconfigPublicApiCtsTests'
    统一为 'AconfigPublicApiCtsTests'，视为同一个模块"""
    try:
        return split_abi_prefix(module)[1]
    except Exception:
        return module

def find_abi_only_entries(old_modules: List[str], new_modules: List[str], same_modules: set) -> tuple:
    """找出同一模块两个文件中都存在、但某一架构版本仅出现在一个文件中的条目。
    例如旧文件有 'armeabi-v7a AconfigPublicApiCtsTests'，新文件只有 'arm64-v8a AconfigPublicApiCtsTests'，
    则 'armeabi-v7a AconfigPublicApiCtsTests' 记入 old_only：仅单独说明显示，不计入 --include-filter。
    返回 (old_only_entries, new_only_entries)，均按名称排序"""
    try:
        old_abis = {}
        new_abis = {}
        for m in old_modules:
            abi, base = split_abi_prefix(m)
            if abi:
                old_abis.setdefault(base, set()).add(abi)
        for m in new_modules:
            abi, base = split_abi_prefix(m)
            if abi:
                new_abis.setdefault(base, set()).add(abi)

        old_only = []
        new_only = []
        for base in sorted(old_abis.keys() | new_abis.keys()):
            # 仅关注两个文件都存在的模块；整个模块仅一方有的情况已体现在 old_unique/new_unique 中
            if base not in same_modules:
                continue
            for abi in sorted(old_abis.get(base, set()) - new_abis.get(base, set())):
                old_only.append(f"{abi} {base}")
            for abi in sorted(new_abis.get(base, set()) - old_abis.get(base, set())):
                new_only.append(f"{abi} {base}")
        return old_only, new_only
    except Exception:
        return [], []

def compare_files(new_modules: List[str], old_modules: List[str], new_file_path: str = "", old_file_path: str = "") -> dict:
    """增强型模块差异对比分析，返回对比结果字典。
    不论XML/HTML/TXT，统一先移除架构前缀再对比，
    同一模块的不同架构版本视为同一个模块"""
    try:
        result = {}

        # 检查文件类型
        new_is_xml = new_file_path.lower().endswith('.xml') if new_file_path else False
        old_is_xml = old_file_path.lower().endswith('.xml') if old_file_path else False

        # 先标准化（移除arm64-v8a/armeabi-v7a等架构前缀），再计算差异，
        # 避免同一模块的不同架构版本被误判为独有模块
        old_norm = {normalize_cts_module(m) for m in old_modules}
        new_norm = {normalize_cts_module(m) for m in new_modules}

        old_unique = old_norm - new_norm
        new_unique = new_norm - old_norm
        same_modules = old_norm & new_norm

        # 同一模块双方都有、但架构版本仅一方有的条目（如旧文件有armeabi-v7a版本而新文件没有），
        # 单独说明显示，不计入--include-filter
        old_abi_only, new_abi_only = find_abi_only_entries(old_modules, new_modules, same_modules)

        # 如果两个文件都是XML，计算独有模块和相同模块
        if new_is_xml and old_is_xml:
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
                'old_abi_only': old_abi_only,
                'new_abi_only': new_abi_only,
                'is_xml_comparison': True
            }

            return result

        # 生成过滤命令
        old_command = ' '.join(f"--include-filter {m}" for m in sorted(old_unique)) or "无"
        new_command = ' '.join(f"--include-filter {m}" for m in sorted(new_unique)) or "无"

        # 构建结果字典
        result = {
            'old_raw': sorted(old_unique),
            'new_raw': sorted(new_unique),
            'old_clean': sorted(old_unique),
            'new_clean': sorted(new_unique),
            'old_command': old_command,
            'new_command': new_command,
            'old_abi_only': old_abi_only,
            'new_abi_only': new_abi_only,
            'is_xml_comparison': False
        }

        return result

    except Exception as e:
        raise
