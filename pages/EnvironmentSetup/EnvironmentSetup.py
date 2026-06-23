import os
import sys
import webbrowser
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QUrl, Qt


class EnvironmentSetup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded = False
        self._html_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'html', 'XTS测试环境配置---胡光银.html')
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._placeholder = self._create_fallback()
        layout.addWidget(self._placeholder)

    def showEvent(self, event):
        if not self._loaded:
            self._loaded = True
            web_view = self._create_web_view()
            if web_view is not None:
                w = self.window()
                if w:
                    w.setUpdatesEnabled(False)  # 防止 Windows 原生窗口切换闪屏
                layout = self.layout()
                if layout:
                    layout.replaceWidget(self._placeholder, web_view)
                    self._placeholder.deleteLater()
                    self._placeholder = web_view
                if w:
                    w.setUpdatesEnabled(True)
        super().showEvent(event)
        try:
            w = self.window()
            if w and hasattr(w, 'restoreWindowIcon'):
                w.restoreWindowIcon()
        except Exception:
            pass

<<<<<<< HEAD
    def reload_webengine(self):
        """WebEngine 安装完成后，重新尝试加载内嵌浏览器"""
        self._loaded = False
        web_view = self._create_web_view()
        if web_view is not None:
            layout = self.layout()
            if layout:
                layout.replaceWidget(self._placeholder, web_view)
                self._placeholder.deleteLater()
                self._placeholder = web_view

=======
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30
    def _create_web_view(self):
        import os as _os
        html_path = self._html_path
        for sp in sys.path:
            qt6 = _os.path.join(sp, 'PyQt6', 'Qt6')
            if _os.path.isdir(qt6):
                lib = _os.path.join(qt6, 'lib')
                if _os.path.isdir(lib):
                    lp = _os.environ.get('LD_LIBRARY_PATH', '')
                    if lib not in lp:
                        _os.environ['LD_LIBRARY_PATH'] = f"{lib}:{lp}" if lp else lib
                for sub in ('libexec', 'bin'):
                    proc = _os.path.join(qt6, sub,
                        'QtWebEngineProcess.exe' if sys.platform == 'win32'
                        else 'QtWebEngineProcess')
                    if _os.path.exists(proc) and 'QTWEBENGINEPROCESS_PATH' not in _os.environ:
                        _os.environ['QTWEBENGINEPROCESS_PATH'] = proc
                for sub, var in [('resources', 'QTWEBENGINE_RESOURCES_PATH'),
                                 ('translations/qtwebengine_locales', 'QTWEBENGINE_LOCALES_PATH')]:
                    p = _os.path.join(qt6, sub)
                    if _os.path.isdir(p) and var not in _os.environ:
                        _os.environ[var] = p
                break
        if getattr(sys, 'frozen', False):
            try:
                import PyQt6
                for sp in sys.path:
                    sp_pyqt6 = _os.path.join(sp, 'PyQt6')
                    if _os.path.isdir(sp_pyqt6) and sp_pyqt6 not in PyQt6.__path__:
                        PyQt6.__path__.append(sp_pyqt6)
            except ImportError:
                pass
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            return None
        try:
            view = QWebEngineView()
            view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            view.page().setBackgroundColor(Qt.GlobalColor.transparent)
            view.setStyleSheet("background: transparent")
            if os.path.exists(html_path):
                view.load(QUrl.fromLocalFile(os.path.abspath(html_path)))
            else:
                view.setHtml("<p>页面加载失败：文件不存在</p>")
            return view
        except Exception:
            return None

    def _create_fallback(self):
        widget = QWidget()
        widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel("内嵌浏览器组件不可用，请使用系统浏览器打开")
        hint.setStyleSheet("color: white; font-size: 16px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        path = os.path.abspath(self._html_path)
        file_exists = os.path.exists(path)
        if not file_exists:
            tip = QLabel("（HTML 文件不存在）")
            tip.setStyleSheet("color: #e74c3c; font-size: 13px;")
            tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(tip)
        btn = QPushButton("在浏览器中打开")
        btn.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white;
                border: none; padding: 10px 30px; border-radius: 6px; font-size: 15px; }
<<<<<<< HEAD
            QPushButton:hover { color: black;   background- }
=======
            QPushButton:hover { background-color: #2980b9; }
>>>>>>> 8b50fe45e3323742a9544b3fc2ba97e31b3e5c30
            QPushButton:pressed { background-color: #1c6ea4; }""")
        btn.setEnabled(file_exists)
        btn.clicked.connect(lambda: webbrowser.open(f"file://{path}"))
        layout.addWidget(btn)
        return widget
