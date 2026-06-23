"""PyInstaller runtime hook: 添加系统 Python site-packages 到 sys.path。
打包时排除了 PyQt6，启动时从系统 Python 加载，避免 DLL 冲突。"""
import sys
import os
import subprocess
import platform


def _find_system_site_packages():
    """查找系统 Python 的 site-packages 路径。"""
    interpreters = []

    # 1. 常见安装位置
    if platform.system() == "Windows":
        for base in [os.path.expanduser(r"~\AppData\Local\Programs\Python"),
                      r"C:\Program Files\Python",
                      r"C:\Python"]:
            if os.path.isdir(base):
                for d in sorted(os.listdir(base), reverse=True):
                    py = os.path.join(base, d, "python.exe")
                    if os.path.isfile(py):
                        interpreters.append(py)
        # where python
        try:
            r = subprocess.run(["where", "python"], capture_output=True,
                               text=True, timeout=5)
            for line in r.stdout.strip().splitlines():
                p = line.strip()
                if p and p not in interpreters:
                    interpreters.append(p)
        except Exception:
            pass
    else:
        for p in ["python3", "python"]:
            try:
                r = subprocess.run(["which", p], capture_output=True,
                                   text=True, timeout=3)
                if r.returncode == 0:
                    interpreters.append(r.stdout.strip())
            except Exception:
                pass

    for py in interpreters:
        if not os.path.isfile(py):
            continue
        try:
            r = subprocess.run(
                [py, "-c",
                 "import site; print(site.getsitepackages()[0])"],
                capture_output=True, text=True, timeout=10
            )
            sp = r.stdout.strip()
            if sp and os.path.isdir(sp):
                return sp
        except Exception:
            continue
    return ""


_sp = _find_system_site_packages()
if _sp and _sp not in sys.path:
    sys.path.insert(0, _sp)
    # Windows: 注册 DLL 目录
    if platform.system() == "Windows":
        qt_bin = os.path.join(_sp, "PyQt6", "Qt6", "bin")
        if os.path.isdir(qt_bin):
            try:
                os.add_dll_directory(qt_bin)
            except Exception:
                pass
    else:
        qt_lib = os.path.join(_sp, "PyQt6", "Qt6", "lib")
        if os.path.isdir(qt_lib):
            os.environ["LD_LIBRARY_PATH"] = qt_lib + ":" + os.environ.get("LD_LIBRARY_PATH", "")
