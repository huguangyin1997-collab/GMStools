import sys
import os
import ctypes
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, QSettings, QAbstractNativeEventFilter
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QColor, QIcon

from CustomTitle import CustomTitleBar
from PageManager import PageManager
from usekey import sign_disclaimer_accepted


class _X11IconGuard(QAbstractNativeEventFilter):
    """X11 Native Event Filter：监听 _NET_WM_ICON 属性变化，
    一旦被 Chromium 子进程清除/覆盖，立刻恢复。"""

    def __init__(self, restore_callback):
        super().__init__()
        self._callback = restore_callback
        self._atom_net_wm_icon = None
        self._setup_x11()

    def _setup_x11(self):
        try:
            xlib = ctypes.cdll.LoadLibrary('libX11.so.6')
            display = xlib.XOpenDisplay(None)
            if display:
                self._atom_net_wm_icon = xlib.XInternAtom(
                    ctypes.c_void_p(display), b'_NET_WM_ICON', 1)
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
                if atom == self._atom_net_wm_icon:
                    self._callback()
        except Exception:
            pass
        return False, 0

class WindowManager(QMainWindow):
    def __init__(self, disclaimer_already_accepted=False, config_path=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
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

    def get_resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    def setWindowIconFromFile(self):
        # 按平台选择图标格式：Linux 优先 png，Windows 用 ico
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
        # 兜底：从 app_miku.jpg / Miku.jpg 生成图标
        for fallback in ['app_miku.jpg', 'Miku.jpg']:
            fallback_path = self.get_resource_path(fallback)
            if os.path.exists(fallback_path):
                pixmap = QPixmap(fallback_path)
                if not pixmap.isNull():
                    icon = QIcon(pixmap)
                    self._persist_icon = icon
                    self.setWindowIcon(icon)
                    return
        print("警告: 未能加载任何图标文件")

    def setup_background(self):
        image_path = self.get_resource_path("Miku.jpg")
        self.background_original = QPixmap(image_path)
        if self.background_original.isNull():
            print(f"❌ 背景图片加载失败: {image_path}")
            self.background_original = QPixmap(1200, 800)
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
        """跨平台恢复窗口/应用图标（保持 Python 引用防 GC 回收）。"""
        import ctypes as _ctypes
        app = QApplication.instance()

        # 所有平台：重新设置窗口级图标
        self.setWindowIconFromFile()

        if sys.platform == "win32":
            try:
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

        # 强制刷新平台窗口属性
        try:
            handle = self.windowHandle()
            if handle is not None:
                handle.setIcon(self.windowIcon())
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self.update_background()
        if not hasattr(self, '_icon_set'):
            self._icon_set = True
            self.setWindowIconFromFile()

    def closeEvent(self, event):
        """窗口直接关闭，不进行任何ADB清理"""
        print("closeEvent 触发，程序即将退出")
        event.accept()