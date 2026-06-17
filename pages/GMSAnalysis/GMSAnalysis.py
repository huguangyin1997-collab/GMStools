import os
import webbrowser
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QUrl, Qt


class GMSAnalysis(QWidget):
    """GMS简析页面 - 展示GMS测试基础知识"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        html_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'html',
            'GMS测试基础知识---胡光银.html'
        )

        web_view = self._create_web_view(html_path)
        if web_view is not None:
            layout.addWidget(web_view)
        else:
            layout.addWidget(self._create_fallback(html_path))

    def _create_web_view(self, html_path):
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            return None

        try:
            web_view = QWebEngineView()
            web_view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            web_view.page().setBackgroundColor(Qt.GlobalColor.transparent)
            web_view.setStyleSheet("background: transparent")

            if os.path.exists(html_path):
                web_view.load(QUrl.fromLocalFile(os.path.abspath(html_path)))
            else:
                web_view.setHtml("<p>页面加载失败：文件不存在</p>")
            return web_view
        except Exception:
            return None

    def _create_fallback(self, html_path):
        widget = QWidget()
        widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hint = QLabel("内嵌浏览器组件不可用，请使用系统浏览器打开")
        hint.setStyleSheet("color: white; font-size: 16px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        file_exists = os.path.exists(html_path)
        if not file_exists:
            tip = QLabel("（HTML 文件不存在）")
            tip.setStyleSheet("color: #e74c3c; font-size: 13px;")
            tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(tip)

        btn = QPushButton("在浏览器中打开")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white;
                border: none; padding: 10px 30px;
                border-radius: 6px; font-size: 15px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #1c6ea4; }
        """)
        btn.setEnabled(file_exists)
        btn.clicked.connect(lambda: webbrowser.open(
            f"file://{os.path.abspath(html_path)}"))
        layout.addWidget(btn)

        return widget
