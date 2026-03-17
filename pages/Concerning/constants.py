# constants.py
APP_VERSION = "1.2.16"
GITHUB_API_URL = "https://api.github.com/repos/huguangyin1997-collab/GMStools/releases/latest"
CACHE_FILE = "version_cache.json"


def compare_versions(v1: str, v2: str) -> int:
    """语义化版本比较，返回 v1 - v2 的差值"""
    def normalize(v):
        return [int(x) for x in v.split('.')]

    parts1 = normalize(v1)
    parts2 = normalize(v2)
    for i in range(max(len(parts1), len(parts2))):
        n1 = parts1[i] if i < len(parts1) else 0
        n2 = parts2[i] if i < len(parts2) else 0
        if n1 != n2:
            return n1 - n2
    return 0