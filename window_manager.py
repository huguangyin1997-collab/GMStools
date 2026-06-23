import sys
import os
import ctypes
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, QSettings, QAbstractNativeEventFilter
<<<<<<< HEAD
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QColor, QIcon, QImage
=======
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QColor, QIcon
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30

from CustomTitle import CustomTitleBar
from PageManager import PageManager
from usekey import sign_disclaimer_accepted


class _X11IconGuard(QAbstractNativeEventFilter):
<<<<<<< HEAD
    """X11 Native Event Filter：同时监听 _NET_WM_ICON 和 WM_CLASS 属性变化。
    Chromium 子进程启动时可能分别修改这两个属性，任意一个被改动都立即恢复。"""
=======
    """X11 Native Event Filter：监听 _NET_WM_ICON 属性变化，
    一旦被 Chromium 子进程清除/覆盖，立刻恢复。"""
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30

    def __init__(self, restore_callback):
        super().__init__()
        self._callback = restore_callback
        self._atom_net_wm_icon = None
<<<<<<< HEAD
        self._atom_wm_class = None
=======
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30
        self._setup_x11()

    def _setup_x11(self):
        try:
            xlib = ctypes.cdll.LoadLibrary('libX11.so.6')
            display = xlib.XOpenDisplay(None)
            if display:
                self._atom_net_wm_icon = xlib.XInternAtom(
                    ctypes.c_void_p(display), b'_NET_WM_ICON', 1)
<<<<<<< HEAD
                self._atom_wm_class = xlib.XInternAtom(
                    ctypes.c_void_p(display), b'WM_CLASS', 1)
=======
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30
                xlib.XCloseDisplay(ctypes.c_void_p(display))
        except Exception:
            pass

    def nativeEventFilter(self, eventType, message):
        if sys.platform == 'win32' or self._atom_net_wm_icon is None:
            return False, 0
        try:
            # xcb_generic_event_t 结构 (32 bytes):
            # uint8_t response_type (offset 0)
            # uint8_t pad0 (offset 1)
            # uint16_t sequence (offset 2)
            # ... (varies by event type)
            # For PropertyNotify (response_type = 28):
            # uint32_t window (offset 8)
            # uint32_t atom (offset 16)
            # ...
            data = ctypes.string_at(message, 32)
            response_type = data[0] & 0x7F  # 去掉高位 send_event 标志
            if response_type == 28:  # PropertyNotify
                atom = int.from_bytes(data[16:20], 'little')
<<<<<<< HEAD
                if atom == self._atom_net_wm_icon or atom == self._atom_wm_class:
=======
                if atom == self._atom_net_wm_icon:
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30
                    self._callback()
        except Exception:
            pass
        return False, 0

class WindowManager(QMainWindow):
    def __init__(self, disclaimer_already_accepted=False, config_path=None):
        super().__init__()
<<<<<<< HEAD
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
=======
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30
        self.setWindowTitle("GMStools工具")
        self.resize(1200, 800)

        self.disclaimer_already_accepted = disclaimer_already_accepted
        self.config_path = config_path

        # 立即设置临时背景色，避免白色闪现
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(44, 62, 80))
        self.setPalette(palette)

        self.setup_ui()

        # 设置窗口图标（仅一次）
        self.setWindowIconFromFile()

        if self.disclaimer_already_accepted:
            self.on_disclaimer_agreed(skip_save=True)
        else:
            self.connect_disclaimer_signals()

        # 延迟加载背景图片和完整初始化，不阻塞界面显示
        QTimer.singleShot(0, self._complete_initialization)

    def _install_icon_guard(self):
        """安装 X11 原生事件过滤器，实时监控 _NET_WM_ICON 属性。
        一旦被外部修改（Chromium 子进程），毫秒级恢复。"""
        if sys.platform == 'win32' or hasattr(self, '_guard_installed'):
            return
        self._guard_installed = True
        try:
            win_id = int(self.winId())
            # 设置 PropertyChangeMask 以接收 PropertyNotify 事件
            xlib = ctypes.cdll.LoadLibrary('libX11.so.6')
            disp = xlib.XOpenDisplay(None)
            if disp:
                xlib.XSelectInput(ctypes.c_void_p(disp), ctypes.c_ulong(win_id),
                                  ctypes.c_ulong(0x00400000))  # PropertyChangeMask
                xlib.XFlush(ctypes.c_void_p(disp))
                xlib.XCloseDisplay(ctypes.c_void_p(disp))
            self._icon_guard = _X11IconGuard(self.restoreWindowIcon)
            QApplication.instance().installNativeEventFilter(self._icon_guard)
        except Exception:
            pass

    def _prewarm_webengine(self):
<<<<<<< HEAD
        """在 Windows 上通过创建原生子窗口来触发 taskbar 图标注册。

        Windows Shell 在首次 show 窗口时可能忽略 WM_SETICON（taskbar
        button 尚未就绪）。创建并显示一个原生子 widget 会触发 Shell 重新
        评估父窗口的 taskbar 入口，此时 restoreWindowIcon() 才能生效。

        优先使用 QWebEngineView（已安装时），否则用普通 QWidget 强制
        创建原生窗口达到同样效果。
        """
        if sys.platform != 'win32':
            return
        try:
            view = None
            try:
                from PyQt6.QtWebEngineWidgets import QWebEngineView
                view = QWebEngineView(self)
                view.setHtml("<html></html>")
            except ImportError:
                # 未安装 WebEngine：用普通 QWidget 强制创建原生子窗口
                view = QWidget(self, Qt.WindowType.Widget)
                view.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
            view.setGeometry(0, 0, 2, 2)
            view.lower()
            view.show()  # ← 触发 CreateWindowEx，Shell 重评估 taskbar
            QApplication.processEvents()
            view.hide()
            self._prewarm_view = view  # 保持引用防 GC
            self.restoreWindowIcon()
        except Exception:
            pass

    def _force_x11_wm_class(self):
        """Linux X11: 强制注入 WM_CLASS 属性到窗口。

        动态加载外部 WebEngine .so 后，X11 窗口管理器（Mutter / kwin / GNOME）
        检测到动态链接库的所有者发生变更，会基于安全策略重新评估进程归属。
        此时 WM_CLASS 可能被剥离或重置，导致窗口无法关联到
        ~/.local/share/applications/GMStools.desktop 中的 StartupWMClass，
        任务栏图标因此丢失（即便 _NET_WM_ICON 已正确设置）。

        此方法完全绕过 Qt 的 WM_CLASS 推导逻辑，直接用 ctypes 向 X11
        XChangeProperty 写入正确值，确保窗口管理器始终能匹配 .desktop 文件。
        """
        if sys.platform == 'win32':
            return
        try:
            import ctypes as _ctypes
            win_id = int(self.winId())
            if not win_id:
                return

            xlib = _ctypes.cdll.LoadLibrary('libX11.so.6')
            display = xlib.XOpenDisplay(None)
            if not display:
                return

            # XA_STRING = 31（X11 预定义原子，表示字符串类型）
            XA_STRING = 31
            wm_class_atom = xlib.XInternAtom(
                _ctypes.c_void_p(display), b'WM_CLASS', 0)

            # WM_CLASS 格式: "instance_name\0class_name\0"
            # Qt 将 instance 设为 argv[0] basename 的小写，class 为 applicationName
            wm_class_value = b'gmstools\x00GMStools\x00'

            xlib.XChangeProperty(
                _ctypes.c_void_p(display),
                _ctypes.c_ulong(win_id),
                wm_class_atom,
                XA_STRING,
                8,  # format: 8-bit chars
                0,  # mode: PropModeReplace
                _ctypes.c_char_p(wm_class_value),
                len(wm_class_value),
            )
            xlib.XFlush(_ctypes.c_void_p(display))
            xlib.XCloseDisplay(_ctypes.c_void_p(display))
            print("✅ [X11] WM_CLASS 已强制注入: GMStools")
        except Exception as e:
            print(f"⚠ [X11] WM_CLASS 注入失败: {e}")

    def _force_x11_icon(self, icon_path=None):
        """Linux X11: 直接通过 _NET_WM_ICON 属性强行写入窗口图标的 ARGB 像素数据。

        完全绕过 Qt 图标传递链路（Qt → XCB → X11），在当前进程的 X11 窗口上
        直接设置 _NET_WM_ICON。当动态加载外部 .so 导致 Qt setWindowIcon /
        QWindow.setIcon 失效（CWD 偏移 / Qt 内部路径解析失败）时，
        这是最后一道保险。

        使用 PNG 绝对路径 → QPixmap → QImage → ARGB32 像素 → XChangeProperty
        的完整链路，确保图标数据以 X11 原生格式抵达窗口管理器。
        """
        if sys.platform == 'win32':
            return
        try:
            import ctypes as _ctypes

            # 解析图标绝对路径
            if icon_path is None:
                for name in ['app.png', 'app.ico']:
                    p = self.get_resource_path(name)
                    if os.path.exists(p):
                        icon_path = os.path.abspath(p)
                        break
            if not icon_path or not os.path.exists(icon_path):
                return

            win_id = int(self.winId())
            if not win_id:
                return

            # 加载 → 缩放 → ARGB32（任务栏图标建议 64x64 兼顾清晰度和内存）
            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                return
            pixmap = pixmap.scaled(64, 64,
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
            width, height = image.width(), image.height()

            # _NET_WM_ICON 格式: CARDINAL[2 + width*height]
            # 前两元素为 width, height，后续为 0xAARRGGBB 像素值
            pixel_count = width * height
            CArray = _ctypes.c_ulong * (2 + pixel_count)
            data = CArray()
            data[0] = width
            data[1] = height
            for i in range(pixel_count):
                y, x = divmod(i, width)
                data[2 + i] = image.pixel(x, y)  # QImage.pixel 返回 QRgb = 0xAARRGGBB

            xlib = _ctypes.cdll.LoadLibrary('libX11.so.6')
            display = xlib.XOpenDisplay(None)
            if not display:
                return

            # XA_CARDINAL = 6（X11 预定义原子，表示 32-bit 无符号整数数组）
            XA_CARDINAL = 6
            net_wm_icon_atom = xlib.XInternAtom(
                _ctypes.c_void_p(display), b'_NET_WM_ICON', 0)

            xlib.XChangeProperty(
                _ctypes.c_void_p(display),
                _ctypes.c_ulong(win_id),
                net_wm_icon_atom,
                XA_CARDINAL,
                32,  # format: 32-bit per element
                0,   # mode: PropModeReplace
                _ctypes.cast(data, _ctypes.c_void_p),
                2 + pixel_count,
            )
            xlib.XFlush(_ctypes.c_void_p(display))
            xlib.XCloseDisplay(_ctypes.c_void_p(display))
            print(f"✅ [X11] _NET_WM_ICON 直接写入 ({width}x{height})")
        except Exception as e:
            print(f"⚠ [X11] _NET_WM_ICON 写入失败: {e}")

=======
        """提前创建 WebEngine 实例启动 Chromium 进程，
        此时icon被干扰后立刻恢复，用户不可见。"""
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            return
        try:
            view = QWebEngineView()
            view.setHtml("<html></html>")
            self._prewarm_view = view  # 保持引用防止 GC
        except Exception:
            pass

>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30
    def get_resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    def setWindowIconFromFile(self):
        # 按平台选择图标格式：Linux 优先 png，Windows 用 ico
<<<<<<< HEAD
        icon_name = 'app.ico' if sys.platform == 'win32' else 'app.png'
        icon_path = self.get_resource_path(icon_name)
        if not os.path.exists(icon_path):
            icon_path = self.get_resource_path('app.png' if sys.platform == 'win32' else 'app.ico')
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            if not icon.isNull():
                self._persist_icon = icon
                self.setWindowIcon(icon)
                self._debug_icon("setWindowIcon", icon_path, icon)
                return
            else:
                self._debug_icon("QIcon.isNull", icon_path, None)
=======
        icon_candidates = ['app.png', 'app.ico'] if sys.platform != 'win32' else ['app.ico', 'app.png']
        for icon_name in icon_candidates:
            icon_path = self.get_resource_path(icon_name)
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                if not icon.isNull():
                    self._persist_icon = icon  # 保持 Python 引用，防止 GC 回收
                    self.setWindowIcon(icon)
                    if not hasattr(self, '_icon_logged'):
                        self._icon_logged = True
                        print(f"窗口图标已设置: {icon_path}")
                    return
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30
        # 兜底：从 app_miku.jpg / Miku.jpg 生成图标
        for fallback in ['app_miku.jpg', 'Miku.jpg']:
            fallback_path = self.get_resource_path(fallback)
            if os.path.exists(fallback_path):
                pixmap = QPixmap(fallback_path)
                if not pixmap.isNull():
                    icon = QIcon(pixmap)
                    self._persist_icon = icon
                    self.setWindowIcon(icon)
<<<<<<< HEAD
                    self._debug_icon("fallback", fallback_path, icon)
                    return
        self._debug_icon("FAILED", icon_path, None)
        print("警告: 未能加载任何图标文件")

    def _debug_icon(self, stage, path, icon):
        """诊断日志：记录图标加载各阶段的结果，方便排查 Windows 任务栏图标问题。"""
        try:
            import datetime
            log_path = os.path.join(os.path.dirname(sys.executable), 'icon_debug.log')
            if not os.path.exists(os.path.dirname(sys.executable)):
                log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon_debug.log')
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] stage={stage}\n")
                f.write(f"  path={path}\n")
                f.write(f"  file_exists={os.path.exists(path) if path else 'N/A'}\n")
                if icon is not None:
                    f.write(f"  isNull={icon.isNull()}\n")
                    # 检查可用尺寸
                    try:
                        sizes = icon.availableSizes()
                        f.write(f"  availableSizes={[(s.width(), s.height()) for s in sizes]}\n")
                    except Exception:
                        pass
                    # 取一个实际 pixmap 看是否有效
                    try:
                        pm = icon.pixmap(64, 64)
                        f.write(f"  pixmap(64,64).isNull={pm.isNull()}\n")
                    except Exception:
                        pass
                f.write(f"  sys.platform={sys.platform}\n")
                f.write(f"  frozen={getattr(sys, 'frozen', False)}\n")
                if hasattr(sys, '_MEIPASS'):
                    f.write(f"  _MEIPASS={sys._MEIPASS}\n")
                f.write("\n")
        except Exception:
            pass

    def init_webengine_pages(self):
        """窗口亮相后、WebEngine 就绪时调用，重新加载内嵌浏览器页面"""
        for name in ('GMSAnalysis', 'EnvironmentSetup'):
            page = self.page_manager.get_page(name)
            if page and hasattr(page, 'reload_webengine'):
                page.reload_webengine()

    def setup_background(self):
        image_path = self.get_resource_path("Miku.jpg")
        # 用 QImageReader 在解码时直接缩到屏幕 2 倍尺寸，避免先加载
        # 原始 6016×4016 再在主线程缩放导致 UI 卡顿
        from PyQt6.QtGui import QImageReader
        from PyQt6.QtCore import QSize
        reader = QImageReader(image_path)
        w, h = self.width(), self.height()
        reader.setScaledSize(QSize(max(w * 2, 2560), max(h * 2, 1440)))
        self.background_original = QPixmap.fromImageReader(reader)
        if self.background_original.isNull():
            print(f"❌ 背景图片加载失败: {image_path}")
            self.background_original = QPixmap(w, h)
=======
                    return
        print("警告: 未能加载任何图标文件")

    def setup_background(self):
        image_path = self.get_resource_path("Miku.jpg")
        self.background_original = QPixmap(image_path)
        if self.background_original.isNull():
            print(f"❌ 背景图片加载失败: {image_path}")
            self.background_original = QPixmap(1200, 800)
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30
            self.background_original.fill(QColor(57, 197, 187))
        self.update_background()

    def update_background(self, smooth=True):
        if not hasattr(self, 'background_original'):
            return
        new_size = self.size()
        # skip if size unchanged
        if hasattr(self, '_last_bg_size') and self._last_bg_size == new_size:
            return
        self._last_bg_size = new_size

        mode = Qt.TransformationMode.SmoothTransformation if smooth else Qt.TransformationMode.FastTransformation
        scaled_pixmap = self.background_original.scaled(
            new_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            mode
        )
        if scaled_pixmap.width() > new_size.width() or scaled_pixmap.height() > new_size.height():
            x = (scaled_pixmap.width() - new_size.width()) // 2
            y = (scaled_pixmap.height() - new_size.height()) // 2
            scaled_pixmap = scaled_pixmap.copy(x, y, new_size.width(), new_size.height())
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
        self.setPalette(palette)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar()
        self.title_bar.minimize_signal.connect(self.showMinimized)
        self.title_bar.maximize_signal.connect(self.toggle_maximize)
        self.title_bar.close_signal.connect(self.close)
        main_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.1);
                border-bottom-left-radius: 15px;
                border-bottom-right-radius: 15px;
            }
        """)
        main_layout.addWidget(content_widget)

        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.page_manager = PageManager(parent_widget=content_widget)

        if not self.disclaimer_already_accepted:
            self.page_manager.left_menu.setVisible(False)
        else:
            self.page_manager.left_menu.setVisible(True)
            self.page_manager.disclaimer_accepted = True
            disclaimer_page = self.page_manager.get_page("Disclaimer")
            if disclaimer_page:
                disclaimer_page.set_readonly_mode(True)

        content_layout.addWidget(self.page_manager.left_menu)
        content_layout.addWidget(self.page_manager.stacked_widget)

    def _complete_initialization(self):
        self.setup_background()

    def connect_disclaimer_signals(self):
        disclaimer_page = self.page_manager.get_page("Disclaimer")
        if disclaimer_page:
            disclaimer_page.agreed.connect(self.on_disclaimer_agreed)
            disclaimer_page.rejected.connect(self.close)

    def on_disclaimer_agreed(self, skip_save=False):
        if not skip_save and self.config_path:
            settings = QSettings(self.config_path, QSettings.Format.IniFormat)
            signed = sign_disclaimer_accepted(True)
            settings.setValue("disclaimer_accepted", signed)
            settings.sync()

        self.page_manager.left_menu.setVisible(True)
        self.page_manager.disclaimer_accepted = True
        disclaimer_page = self.page_manager.get_page("Disclaimer")
        if disclaimer_page:
            disclaimer_page.set_readonly_mode(True)
        self.page_manager.set_current_page("CheckupReport")

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # fast preview during active resize
        self.update_background(smooth=False)
        # smooth re-render when resize settles
        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()
        else:
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(lambda: self.update_background(smooth=True))
        self._resize_timer.start(150)

    def restoreWindowIcon(self):
<<<<<<< HEAD
        """跨平台恢复窗口/应用图标。Windows: 检查窗口样式 → 强制 WS_EX_APPWINDOW
        → EXE 内嵌资源图标 → WM_SETICON → SWP_FRAMECHANGED 刷新 taskbar。"""
        import ctypes as _ctypes
        app = QApplication.instance()

        # Qt 层
=======
        """跨平台恢复窗口/应用图标（保持 Python 引用防 GC 回收）。"""
        import ctypes as _ctypes
        app = QApplication.instance()

        # 所有平台：重新设置窗口级图标
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30
        self.setWindowIconFromFile()

        if sys.platform == "win32":
            try:
<<<<<<< HEAD
                hwnd = int(self.winId())
                hmod = _ctypes.windll.kernel32.GetModuleHandleW(None)
                pid = os.getpid()

                # === 诊断：枚举本进程所有顶层窗口 ===
                _probe_windows = []
                def _enum_proc(h, _):
                    _probe_windows.append(h)
                    return True
                _CBFUNC = _ctypes.WINFUNCTYPE(_ctypes.c_bool, _ctypes.c_void_p, _ctypes.c_void_p)
                _ctypes.windll.user32.EnumWindows(_CBFUNC(_enum_proc), 0)
                with open(os.path.join(os.path.dirname(sys.executable), 'icon_debug.log'), 'a', encoding='utf-8') as _f:
                    _f.write(f"  [scan] pid={pid}  myHwnd={hwnd}\n")
                    for h in _probe_windows:
                        try:
                            _pid = _ctypes.c_ulong()
                            _ctypes.windll.user32.GetWindowThreadProcessId(h, _ctypes.byref(_pid))
                            if _pid.value == pid:
                                txt = _ctypes.create_unicode_buffer(256)
                                _ctypes.windll.user32.GetWindowTextW(h, txt, 256)
                                ex_st = _ctypes.windll.user32.GetWindowLongPtrW(h, -20)
                                st = _ctypes.windll.user32.GetWindowLongPtrW(h, -16)
                                vis = _ctypes.windll.user32.IsWindowVisible(h)
                                _f.write(f"    hwnd={h} txt='{txt.value}' vis={vis}"
                                         f" style={st:#x} ex={ex_st:#x}"
                                         f" APPWINDOW={'Y' if ex_st & 0x40000 else 'N'}"
                                         f" TOOLWINDOW={'Y' if ex_st & 0x80 else 'N'}"
                                         f" {'← MAIN' if h == hwnd else ''}\n")
                        except Exception:
                            pass
                    _f.write("\n")

                # === 强制 WS_EX_APPWINDOW，移除 WS_EX_TOOLWINDOW ===
                ex_style = _ctypes.windll.user32.GetWindowLongPtrW(hwnd, -20)
                if ex_style:
                    need_change = False
                    if not (ex_style & 0x40000):   # 缺少 WS_EX_APPWINDOW
                        ex_style |= 0x40000
                        need_change = True
                    if ex_style & 0x80:            # 有 WS_EX_TOOLWINDOW（隐藏 taskbar）
                        ex_style &= ~0x80
                        need_change = True
                    if need_change:
                        _ctypes.windll.user32.SetWindowLongPtrW(hwnd, -20, ex_style)

                # === 加载 EXE 内嵌图标资源 ===
                hicon_small = _ctypes.windll.user32.LoadImageW(hmod, 1, 1, 16, 16, 0)
                hicon_big   = _ctypes.windll.user32.LoadImageW(hmod, 1, 1, 32, 32, 0)
                if hicon_small:
                    _ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon_small)
                if hicon_big:
                    _ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon_big)

                # === SWP_FRAMECHANGED 强制 Shell 刷新 ===
                _ctypes.windll.user32.SetWindowPos(
                    hwnd, 0, 0, 0, 0, 0, 0x0037)

                self._debug_icon("Win32_WM_SETICON+FRAMECHANGED",
                    f"hwnd={hwnd} exStyle={ex_style:#x}", None)
            except Exception:
                pass

        # 应用级图标 & QWindow 级图标
        if app:
            icon_name = 'app.ico' if sys.platform == 'win32' else 'app.png'
            icon_path = self.get_resource_path(icon_name)
            if not os.path.exists(icon_path):
                icon_path = self.get_resource_path('app.png' if sys.platform == 'win32' else 'app.ico')
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                if not icon.isNull():
                    self._persist_app_icon = icon
                    app.setWindowIcon(icon)
=======
                _ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('gmstools.app.1')
            except Exception:
                pass

        # 所有平台：重新设置应用级图标，保持引用
        if app:
            for icon_name in (['app.ico', 'app.png'] if sys.platform == 'win32' else ['app.png', 'app.ico']):
                icon_path = self.get_resource_path(icon_name)
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    if not icon.isNull():
                        self._persist_app_icon = icon
                        app.setWindowIcon(icon)
                        break
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30

        # 强制刷新平台窗口属性
        try:
            handle = self.windowHandle()
            if handle is not None:
                handle.setIcon(self.windowIcon())
        except Exception:
            pass

<<<<<<< HEAD

=======
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30
    def showEvent(self, event):
        super().showEvent(event)
        self.update_background()
        if not hasattr(self, '_icon_set'):
            self._icon_set = True
<<<<<<< HEAD
            # 先预热 WebEngine（启动 Chromium 子进程），再恢复图标。
            # 这与点击 GMSAnalysis/EnvironmentSetup 页面时的路径一致：
            # QWebEngineView 创建 → Chromium 干扰 → restoreWindowIcon 修复。
            # 如果不预热，WM_SETICON 在 taskbar 按钮创建阶段发送会被静默丢弃。
            self._prewarm_webengine()
            self.restoreWindowIcon()
=======
            self.setWindowIconFromFile()
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30

    def closeEvent(self, event):
        """窗口直接关闭，不进行任何ADB清理"""
        print("closeEvent 触发，程序即将退出")
        event.accept()