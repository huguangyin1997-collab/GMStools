# constants.py
import sys
import os


def _get_build_version() -> str:
    """尝试从 build_info.py 读取编译时写入的版本，失败则返回默认值"""
    try:
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            # 开发环境：当前文件在 pages/Concerning/constants.py
            # 向上三级到达项目根目录
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        build_info_path = os.path.join(base_path, 'build_info.py')

        import importlib.util
        spec = importlib.util.spec_from_file_location("build_info", build_info_path)
        if spec and spec.loader:
            build_info = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(build_info)
            return build_info.BUILD_VERSION
    except Exception:
        pass
    return "V26.6.18"   # 默认版本（开发时使用）


APP_VERSION = _get_build_version()
GITHUB_API_URL = "https://api.github.com/repos/huguangyin1997-collab/GMStools/releases/latest"
CACHE_FILE = "version_cache.json"


def compare_versions(v1: str, v2: str) -> int:
    """语义化版本比较，返回 v1 - v2 的差值（兼容 V/v 前缀）"""
    def normalize(v):
        v = v.lstrip('V').lstrip('v')  # 去掉版本号前的 V 或 v
        return [int(x) for x in v.split('.')]

    parts1 = normalize(v1)
    parts2 = normalize(v2)
    for i in range(max(len(parts1), len(parts2))):
        n1 = parts1[i] if i < len(parts1) else 0
        n2 = parts2[i] if i < len(parts2) else 0
        if n1 != n2:
            return n1 - n2
    return 0