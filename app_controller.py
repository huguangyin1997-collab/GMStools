import sys
import os
import ctypes
import subprocess as _sp
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QSharedMemory, QSettings, QObject, QEvent, Qt
from window_manager import WindowManager
from usekey import verify_disclaimer_accepted

# Windows 下隐藏 subprocess 黑窗
_SP_KWARGS = {"creationflags": _sp.CREATE_NO_WINDOW} if sys.platform == "win32" else {}


def _discover_python_envs():
    """探测系统上所有 Python 环境的 site-packages 路径。
    跨平台支持 Windows / Linux，包括系统 Python、conda 环境等。"""
    paths = []
    import platform as _platform

    # 要探测的 Python 解释器列表
    interpreters = []

    # 1. 当前运行的 Python（非打包模式）
    #  打包模式下 sys.executable 是 PyInstaller 生成的二进制文件，
    #  用它执行 -c 会触发 main() 递归调用导致 fork bomb！
    if not getattr(sys, 'frozen', False):
        interpreters.append(sys.executable)

    if _platform.system() == "Windows":
        # 2. Windows: 用 where 命令查找所有 python
        try:
            r = _sp.run(
                ["where", "python"], capture_output=True, text=True, timeout=5, **_SP_KWARGS
            )
            for line in r.stdout.strip().splitlines():
                p = line.strip()
                if p and p not in interpreters:
                    interpreters.append(p)
        except Exception:
            pass
        # 3. Windows conda 环境
        for conda_base in [
            os.path.expanduser("~/anaconda3"),
            os.path.expanduser("~/miniconda3"),
            "C:\\ProgramData\\anaconda3",
            "C:\\ProgramData\\miniconda3",
            "C:\\Users\\Administrator\\anaconda3",
            "C:\\Users\\Administrator\\miniconda3",
        ]:
            conda_python = os.path.join(conda_base, "python.exe")
            if os.path.exists(conda_python):
                interpreters.append(conda_python)
    else:
        # 2. Linux: 优先探测 conda 环境（双击启动时不加载 .bashrc，
        #    PATH 中没有 conda，which python3 只找到系统 Python）
        for conda_base in [
            os.path.join(os.path.expanduser("~"), "anaconda3"),
            os.path.join(os.path.expanduser("~"), "miniconda3"),
            os.path.join(os.path.expanduser("~"), "miniforge3"),
            os.path.join(os.path.expanduser("~"), "micromamba"),
            "/opt/anaconda3",
            "/opt/miniconda3",
        ]:
            conda_python = os.path.join(conda_base, "bin", "python")
            if os.path.exists(conda_python):
                interpreters.append(conda_python)
        # 3. Linux: which 查找 PATH 中的 Python（终端启动时有 conda）
        for p in ["python3", "python"]:
            try:
                result = _sp.run(
                    ["which", p], capture_output=True, text=True, timeout=3, **_SP_KWARGS
                )
                if result.returncode == 0:
                    interpreters.append(result.stdout.strip())
            except Exception:
                pass

    # 去重
    interpreters = list(dict.fromkeys(interpreters))

    for py_exe in interpreters:
        if not os.path.exists(py_exe):
            continue
        try:
            result = _sp.run(
                [py_exe, "-c",
                 "import site; [print(p) for p in site.getsitepackages()]"],
                capture_output=True, text=True, timeout=5,
                env={**os.environ, "PYTHONPATH": ""}, **_SP_KWARGS
            )
            for p in result.stdout.strip().splitlines():
                p = p.strip()
                if p and os.path.isdir(p) and p not in paths:
                    paths.append(p)
        except Exception:
            continue

    # 兜底：子进程可能因缺少 conda 环境变量而失败（如 conda deactivate 后
    # 双击启动），手动补上 conda site-packages 路径
    import glob as _glob
    for py_exe in interpreters:
        # 只对类 conda 前缀的解释器做兜底（子进程方式可能因缺环境变量失败）
        py_dir = os.path.dirname(os.path.dirname(py_exe))  # e.g. ~/anaconda3
        if not _glob.glob(os.path.join(py_dir, "lib", "python3.*")):
            continue  # 不是 conda 类安装，跳过
        for ver_dir in sorted(
            _glob.glob(os.path.join(py_dir, "lib", "python3.*")),
            reverse=True
        ):
            sp = os.path.join(ver_dir, "site-packages")
            if os.path.isdir(sp) and sp not in paths:
                paths.append(sp)

    return paths


def _ensure_webengine():
    """检测 PyQt6-WebEngine 是否可用（轻量检测，不实际加载模块）。
    打包模式：探测系统/conda Python 环境的 site-packages。
    开发模式：用 importlib.util.find_spec + 子进程验证。"""
    import importlib.util

    # 开发模式：轻量检测，不加载 100MB+ Chromium 库
    if not getattr(sys, 'frozen', False):
        spec = importlib.util.find_spec('PyQt6.QtWebEngineWidgets')
        return spec is not None

    # === 打包模式 ===
    # Linux: LD_LIBRARY_PATH + __path__ 扩展加载外部 WebEngine。
    if sys.platform == "win32":
        return _ensure_webengine_windows()
    else:
        return _ensure_webengine_linux()


def _ensure_webengine_linux():
    """Linux 打包版：从外部 Python 环境加载 WebEngine。"""
    import importlib.util

    _webengine_sp = _read_webengine_config()
    if _webengine_sp:
        if _webengine_sp not in sys.path:
            sys.path.insert(0, _webengine_sp)
        _setup_webengine_env(_webengine_sp)
        _extend_pyqt6_path(_webengine_sp)
        if importlib.util.find_spec('PyQt6.QtWebEngineWidgets') is not None:
            return True

    discovered = _discover_python_envs()
    for sp in discovered:
        if sp not in sys.path:
            sys.path.insert(0, sp)
        _setup_webengine_env(sp)
        _extend_pyqt6_path(sp)

    if discovered and importlib.util.find_spec('PyQt6.QtWebEngineWidgets') is not None:
        return True

    if _load_webengine_from_system():
        return True
    return False


def _ensure_webengine_windows():
    """Windows 打包版：检测并注册外部 WebEngine 路径。"""
    import importlib.util
    _webengine_sp = _read_webengine_config()
    candidates = [_webengine_sp] if _webengine_sp else _discover_python_envs()
    for sp in candidates:
        if not sp or 'site-packages' not in sp.replace('\\', '/'):
            continue
        if sp not in sys.path:
            sys.path.insert(0, sp)
        _setup_webengine_env(sp)
        _extend_pyqt6_path(sp)
        qt_bin = os.path.join(sp, "PyQt6", "Qt6", "bin")
        if os.path.isdir(qt_bin) and qt_bin not in os.environ.get("PATH", ""):
            os.environ["PATH"] = qt_bin + ";" + os.environ.get("PATH", "")
    return importlib.util.find_spec('PyQt6.QtWebEngineWidgets') is not None


def _read_webengine_config():
    """读取安装时保存的 site-packages 路径。"""
    import configparser
    cfg = configparser.ConfigParser()
    cfg_path = os.path.join(os.path.dirname(sys.executable), "config.ini") \
        if getattr(sys, 'frozen', False) else os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.ini")
    if os.path.exists(cfg_path):
        cfg.read(cfg_path)
        sp = cfg.get("WebEngine", "site_packages", fallback="")
        if sp and os.path.isdir(sp):
            return sp
    return ""


def _write_webengine_config(site_packages_path):
    """保存 site-packages 路径到配置文件。"""
    import configparser
    cfg = configparser.ConfigParser()
    cfg_path = os.path.join(os.path.dirname(sys.executable), "config.ini") \
        if getattr(sys, 'frozen', False) else os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.ini")
    if os.path.exists(cfg_path):
        cfg.read(cfg_path)
    if not cfg.has_section("WebEngine"):
        cfg.add_section("WebEngine")
    cfg.set("WebEngine", "site_packages", site_packages_path)
    with open(cfg_path, "w", encoding="utf-8") as f:
        cfg.write(f)
    # 记录日志
    try:
        log_path = os.path.join(os.path.dirname(sys.executable), "webengine.log") \
            if getattr(sys, 'frozen', False) else \
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "webengine.log")
        with open(log_path, "a", encoding="utf-8", buffering=1) as f:
            f.write(f"[{__import__('datetime').datetime.now().strftime('%H:%M:%S')}] "
                    f"config saved: site_packages={site_packages_path}\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


def _setup_webengine_env(site_packages):
    """设置 WebEngine 所需的环境变量和 DLL 搜索路径。"""
    qt6_dir = os.path.join(site_packages, "PyQt6", "Qt6")
    if sys.platform == "win32":
        qt_bin = os.path.join(qt6_dir, "bin")
        if os.path.isdir(qt_bin):
            try:
                os.add_dll_directory(qt_bin)
            except Exception:
                pass
    else:
        qt_lib = os.path.join(qt6_dir, "lib")
        if os.path.isdir(qt_lib):
            current = os.environ.get("LD_LIBRARY_PATH", "")
            if qt_lib not in current:
                os.environ["LD_LIBRARY_PATH"] = f"{qt_lib}:{current}" if current else qt_lib
    proc_name = "QtWebEngineProcess.exe" if sys.platform == "win32" else "QtWebEngineProcess"
    # Windows PyQt6 wheel: bin/QtWebEngineProcess.exe
    # Linux PyQt6 wheel & PyInstaller 6.5+: libexec/QtWebEngineProcess
    for _sub in ("libexec", "bin"):
        proc_path = os.path.join(qt6_dir, _sub, proc_name)
        if os.path.exists(proc_path):
            if "QTWEBENGINEPROCESS_PATH" not in os.environ:
                os.environ["QTWEBENGINEPROCESS_PATH"] = proc_path
            break
    for sub, var in [("resources", "QTWEBENGINE_RESOURCES_PATH"),
                      ("translations/qtwebengine_locales", "QTWEBENGINE_LOCALES_PATH")]:
        p = os.path.join(qt6_dir, sub)
        if os.path.isdir(p) and var not in os.environ:
            os.environ[var] = p


def _extend_pyqt6_path(site_packages):
    """扩展 PyQt6.__path__ 以包含外部安装的 WebEngine 子模块。"""
    sys_pyqt6 = os.path.join(site_packages, "PyQt6")
    if os.path.isdir(sys_pyqt6):
        try:
            import PyQt6
            if sys_pyqt6 not in PyQt6.__path__:
                PyQt6.__path__.append(sys_pyqt6)
        except ImportError:
            pass


def _load_webengine_from_system():
    """从系统 site-packages 手动加载 PyQt6-WebEngine 及其全部依赖。
    同时设置 QtWebEngine 所需的环境变量（进程路径、资源路径）。
    跨平台支持 Windows (.pyd) 和 Linux (.abi3.so)。"""
    import importlib.util
    import platform as _platform
    _is_win = _platform.system() == "Windows"

    # 先找到系统的 PyQt6 Qt6 目录
    qt6_dir = None
    for sp in sys.path:
        candidate = os.path.join(sp, 'PyQt6', 'Qt6')
        if os.path.isdir(candidate):
            qt6_dir = candidate
            break

    if qt6_dir:
        # 设置 Chromium 进程路径
        proc_name = 'QtWebEngineProcess.exe' if _is_win else 'QtWebEngineProcess'
        for _sub in ('libexec', 'bin'):
            proc = os.path.join(qt6_dir, _sub, proc_name)
            if os.path.exists(proc):
                os.environ['QTWEBENGINEPROCESS_PATH'] = proc
                break
        # 设置资源路径
        res = os.path.join(qt6_dir, 'resources')
        if os.path.isdir(res):
            os.environ['QTWEBENGINE_RESOURCES_PATH'] = res
        # 设置翻译路径
        loc = os.path.join(qt6_dir, 'translations', 'qtwebengine_locales')
        if os.path.isdir(loc):
            os.environ['QTWEBENGINE_LOCALES_PATH'] = loc

    # WebEngine 需要的 PyQt6 子模块（按依赖顺序）
    _WEBENGINE_MODULES = [
        'QtCore', 'QtGui', 'QtWidgets', 'QtNetwork',
        'QtDBus', 'QtPrintSupport', 'QtOpenGL',
        'QtQml', 'QtQuick', 'QtQuickWidgets',
        'QtWebChannel', 'QtPositioning',
        'QtWebEngineCore', 'QtWebEngineWidgets',
    ]

    _suffix = '.pyd' if _is_win else '.abi3.so'

    for name in _WEBENGINE_MODULES:
        mod_name = f'PyQt6.{name}'
        if mod_name in sys.modules:
            continue
        for sp in sys.path:
            fpath = os.path.join(sp, 'PyQt6', f'{name}{_suffix}')
            if os.path.isfile(fpath):
                try:
                    spec = importlib.util.spec_from_file_location(mod_name, fpath)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[mod_name] = module
                        spec.loader.exec_module(module)
                        break
                except Exception:
                    continue

    return 'PyQt6.QtWebEngineWidgets' in sys.modules

class AppController(QObject):  # 继承 QObject 以使用事件过滤器
    def __init__(self):
        super().__init__()
        self.app = None
        self.window = None
        self.shared_memory = None

    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

    def get_app_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def initialize_application(self):
        # 必须在 QApplication 创建之前设置，否则 QWebEngineView 无法使用
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
        self.app = QApplication(sys.argv)
        self.app.installEventFilter(self)  # 安装事件过滤器

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('gmstools.app.1')
        except:
            pass

        icon_path = self.resource_path('app.ico')
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file not found at {icon_path}")

        font = QFont("Microsoft YaHei", 14)
        self.app.setFont(font)

        # 单实例检查（自动清理异常退出残留的共享内存）
        self.shared_memory = QSharedMemory("GMStools_SingleInstance")
        if self.shared_memory.attach():
            # 上一个实例可能已崩溃，尝试分离后重建
            self.shared_memory.detach()
            if self.shared_memory.create(1):
                print("已清理残留共享内存")
            else:
                # 另一个实例确实在运行
                print("程序已在运行，退出当前实例")
                sys.exit(0)
        else:
            if not self.shared_memory.create(1):
                print("警告：无法创建共享内存，多实例可能不受限制")
            else:
                print("第一个实例已创建共享内存")

        return self.app

    def eventFilter(self, obj, event):
        """捕获所有对象的 Show 事件"""
        if event.type() == QEvent.Type.Show:
            # 打印显示窗口的信息
            print(f"[EventFilter] Show event: object={obj}, class={obj.metaObject().className()}, parent={obj.parent()}")
        return super().eventFilter(obj, event)

    def create_main_window(self):
        app_dir = self.get_app_dir()
        config_path = os.path.join(app_dir, "config.ini")
        settings = QSettings(config_path, QSettings.Format.IniFormat)

        signed_value = settings.value("disclaimer_accepted", "", type=str)
        if signed_value and verify_disclaimer_accepted(signed_value):
            disclaimer_accepted = True
        else:
            disclaimer_accepted = False

        self.window = WindowManager(disclaimer_already_accepted=disclaimer_accepted, config_path=config_path)
        return self.window

    def run_application(self):
        if self.window:
            self.window.show()
            sys.exit(self.app.exec())

def main():
    # 双击启动时工作目录可能是 $HOME，切换到程序所在目录
    # 确保 platform-tools/、unlock/、config.ini 等相对路径正确
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

    has_webengine = _ensure_webengine()

    try:
        controller = AppController()
        controller.initialize_application()

        # 未安装 PyQt6-WebEngine 时弹窗引导安装
        if not has_webengine:
            _offer_webengine_install()

        controller.create_main_window()
        controller.run_application()
    except Exception as e:
        with open("crash.log", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        QMessageBox.critical(
            None,
            "GMStools 启动失败",
            f"程序启动时发生未捕获的异常，已保存错误信息到 crash.log 文件。\n\n"
            f"错误类型：{type(e).__name__}\n"
            f"错误信息：{str(e)}\n\n"
            f"请将 crash.log 文件发送给开发者。"
        )
        sys.exit(1)


def _get_installed_pyqt6_version():
    """检测系统已安装的 PyQt6 版本号，用于版本对齐安装 WebEngine。"""
    
    import json
    import platform as _platform

    interpreters = []
    # 非打包模式用当前 Python，打包模式找系统 Python（避免用 PyInstaller 二进制）
    if not getattr(sys, 'frozen', False):
        interpreters.append(sys.executable)
    if _platform.system() == "Windows":
        try:
            r = _sp.run(
                ["where", "python"], capture_output=True, text=True, timeout=5, **_SP_KWARGS
            )
            for line in r.stdout.strip().splitlines():
                p = line.strip()
                if p and p not in interpreters:
                    interpreters.append(p)
        except Exception:
            pass
    else:
        # 优先 conda（双击启动时 PATH 无 conda，which 只返回系统 Python）
        for conda_base in [
            os.path.join(os.path.expanduser("~"), "anaconda3"),
            os.path.join(os.path.expanduser("~"), "miniconda3"),
            os.path.join(os.path.expanduser("~"), "miniforge3"),
            os.path.join(os.path.expanduser("~"), "micromamba"),
            "/opt/anaconda3",
            "/opt/miniconda3",
        ]:
            cp = os.path.join(conda_base, "bin", "python")
            if os.path.exists(cp) and cp not in interpreters:
                interpreters.append(cp)
        for p in ["python3", "python"]:
            try:
                r = _sp.run(
                    ["which", p], capture_output=True, text=True, timeout=3, **_SP_KWARGS
                )
                if r.returncode == 0:
                    p2 = r.stdout.strip()
                    if p2 not in interpreters:
                        interpreters.append(p2)
            except Exception:
                pass

    for py in interpreters:
        try:
            r = _sp.run(
                [py, "-m", "pip", "show", "PyQt6", "--format=json"],
                capture_output=True, text=True, timeout=15, **_SP_KWARGS
            )
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout)
                return data.get("version", "")
        except Exception:
            continue
    return ""


def _offer_webengine_install():
    """弹窗引导安装 PyQt6-WebEngine 到系统 Python 环境。
    跨平台支持 Windows / Linux，自动版本对齐，优先使用国内镜像。"""
    
    import platform as _platform
    _is_win = _platform.system() == "Windows"

    size_hint = "约 100MB" if _is_win else "约 80MB"
    msg = (
        "检测到未安装内嵌浏览器组件 (PyQt6-WebEngine)。\n\n"
        "安装后可在程序内直接查看网页内容。\n"
        "不安装则使用系统浏览器打开网页。\n\n"
        f"是否现在安装？({size_hint}，需联网)"
    )
    reply = QMessageBox.question(
        None, "GMStools — 安装内嵌浏览器",
        msg,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    if reply != QMessageBox.StandardButton.Yes:
        return

    # 检测已装的 PyQt6 版本，确保 WebEngine 版本匹配
    version = _get_installed_pyqt6_version()
    if not version:
        version = "6.11.0"  # fallback 版本

    # 四个包必须版本严格对齐
    packages = [
        f"PyQt6=={version}",
        f"PyQt6-Qt6=={version}",
        f"PyQt6-WebEngine=={version}",
        f"PyQt6-WebEngine-Qt6=={version}",
    ]

    # 收集可用的 Python 解释器
    #  非打包模式：优先用当前 Python (sys.executable)
    #  打包模式：不能用 sys.executable（PyInstaller 二进制），pip 会装到
    #           临时解压目录，进程退出即消失。改用系统 Python 解释器。
    interpreters = []
    if not getattr(sys, 'frozen', False):
        interpreters.append(sys.executable)
    if _is_win:
        try:
            r = _sp.run(
                ["where", "python"], capture_output=True, text=True, timeout=5, **_SP_KWARGS
            )
            for line in r.stdout.strip().splitlines():
                p = line.strip()
                if p and p not in interpreters:
                    interpreters.append(p)
        except Exception:
            pass
    else:
        # 优先 conda（双击启动时 PATH 无 conda，which 只返回系统 Python）
        for conda_base in [
            os.path.join(os.path.expanduser("~"), "anaconda3"),
            os.path.join(os.path.expanduser("~"), "miniconda3"),
            os.path.join(os.path.expanduser("~"), "miniforge3"),
            os.path.join(os.path.expanduser("~"), "micromamba"),
            "/opt/anaconda3",
            "/opt/miniconda3",
        ]:
            cp = os.path.join(conda_base, "bin", "python")
            if os.path.exists(cp) and cp not in interpreters:
                interpreters.append(cp)
        for p in ["python3", "python"]:
            try:
                r = _sp.run(
                    ["which", p], capture_output=True, text=True, timeout=3, **_SP_KWARGS
                )
                if r.returncode == 0:
                    p2 = r.stdout.strip()
                    if p2 not in interpreters:
                        interpreters.append(p2)
            except Exception:
                pass

    base_flags = [
        "--disable-pip-version-check", "--no-warn-script-location",
        "--default-timeout=120",
        "--force-reinstall",  # 覆盖 conda 旧版 Qt6 C++ 库，确保符号一致
    ]

    # 尝试顺序：清华源 → 官方 PyPI
    mirrors = [
        ("https://pypi.tuna.tsinghua.edu.cn/simple", "pypi.tuna.tsinghua.edu.cn"),
        (None, None),  # 官方 PyPI
    ]

    # 显示安装进度对话框
    progress = QProgressDialog(
        "正在下载内嵌浏览器组件...\n(约 80-100MB，请耐心等待)", "取消", 0, 0
    )
    progress.setWindowTitle("GMStools — 安装中")
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.show()
    QApplication.processEvents()

    installed = False
    for index_url, trusted_host in mirrors:
        if progress.wasCanceled():
            break
        for py in interpreters:
            try:
                cmd = [py, "-m", "pip", "install"] + packages + base_flags
                if index_url:
                    cmd += ["-i", index_url, "--trusted-host", trusted_host]

                proc = _sp.Popen(
                    cmd,
                    stdout=_sp.PIPE, stderr=_sp.STDOUT,
                    text=True, bufsize=1, **_SP_KWARGS
                )
                last_line = ""
                while True:
                    line = proc.stdout.readline()
                    if not line and proc.poll() is not None:
                        break
                    if line:
                        last_line = line.strip()
                        # 只显示有意义的状态行 (下载进度 / 安装状态)
                        if any(kw in last_line for kw in
                               ("Downloading", "Installing", "Successfully",
                                "already", "Requirement", "Collecting",
                                "Downloaded", "Preparing", "Building",
                                "ERROR", "WARNING")):
                            progress.setLabelText(f"正在安装...\n{last_line[:120]}")
                    QApplication.processEvents()
                    if progress.wasCanceled():
                        proc.terminate()
                        break

                if proc.poll() == 0:
                    installed = True
                    break
            except Exception:
                continue
        if installed or progress.wasCanceled():
            break

    progress.close()

    if progress.wasCanceled():
        return

    if not installed:
        # 给出清晰的命令行供用户手动执行
        pkgs_str = " ".join(packages)
        QMessageBox.warning(
            None, "安装失败",
            "自动安装失败，请手动在终端执行：\n\n"
            f"    pip install {pkgs_str}\n\n"
            "提示：如遇网络问题，可使用国内镜像：\n"
            "    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple "
            "--trusted-host pypi.tuna.tsinghua.edu.cn "
            f"{pkgs_str}"
        )
        return

    # 记录安装路径到配置文件，下次启动直接加载
    for py in interpreters:
        try:
            r = _sp.run(
                [py, "-c",
                 "import site; print([p for p in site.getsitepackages() if 'site-packages' in p][0])"],
                capture_output=True, text=True, timeout=10,
                env={**os.environ, "PYTHONPATH": ""}, **_SP_KWARGS
            )
            sp = r.stdout.strip()
            if sp and os.path.isdir(sp):
                _write_webengine_config(sp)
                break
        except Exception:
            continue

    QMessageBox.information(
        None, "安装完成",
        "内嵌浏览器组件安装成功！\n\n"
        "请重启 GMStools 以启用内嵌网页浏览功能。"
    )

if __name__ == "__main__":
    main()