# miku_dialog.py
import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QMouseEvent
from CustomTitle.titleWindowControlButtons import WindowControlButtons


class MikuDialog(QDialog):
    def __init__(self, parent=None, title="提示", message="",
                 buttons=QMessageBox.StandardButton.Ok):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setMinimumSize(400, 200)

        # 加载背景图片
        img_path = self.get_resource_path("Miku.jpg")
        self.bg_pixmap = QPixmap(img_path)
        if self.bg_pixmap.isNull():
            self.bg_pixmap = QPixmap(400, 200)
            self.bg_pixmap.fill(Qt.GlobalColor.darkCyan)

        self.update_background()
        self.setup_ui(title, message, buttons)
        self.drag_position = None

    def get_resource_path(self, relative_path: str) -> str:
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base, relative_path)

    def update_background(self):
        if not hasattr(self, 'bg_pixmap') or self.bg_pixmap.isNull():
            return
        scaled = self.bg_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        if scaled.width() > self.width() or scaled.height() > self.height():
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            scaled = scaled.copy(x, y, self.width(), self.height())
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_background()

    def setup_ui(self, title, message, buttons):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(44)
        self.title_bar.setStyleSheet("background-color: transparent;")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(12, 0, 12, 0)
        title_layout.setSpacing(0)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #000000;
                font-size: 18px;
                font-weight: 900;
                font-family: "Microsoft YaHei", "Segoe UI";
                padding: 0 6px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        self.control_buttons = WindowControlButtons()
        self.control_buttons.minimize_signal.connect(self.showMinimized)
        self.control_buttons.maximize_signal.connect(self.toggle_maximize)
        self.control_buttons.close_signal.connect(self.reject)
        title_layout.addWidget(self.control_buttons)
        main_layout.addWidget(self.title_bar)

        # 内容区域
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        self.label = QLabel(message)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: black;
                font-weight: bold;
                background-color: rgba(255, 255, 255, 0.8);
                padding: 15px;
                border-radius: 8px;
                font-size: 14px;
            }
        """)
        content_layout.addWidget(self.label)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        if buttons & QMessageBox.StandardButton.Ok:
            btn = QPushButton("确定")
            btn.setObjectName("okBtn")
            btn.clicked.connect(lambda: self.done(QMessageBox.StandardButton.Ok))
            self._apply_button_style(btn)
            button_layout.addWidget(btn)

        if buttons & QMessageBox.StandardButton.Yes:
            btn = QPushButton("是")
            btn.setObjectName("yesBtn")
            btn.clicked.connect(lambda: self.done(QMessageBox.StandardButton.Yes))
            self._apply_button_style(btn)
            button_layout.addWidget(btn)

        if buttons & QMessageBox.StandardButton.No:
            btn = QPushButton("否")
            btn.setObjectName("noBtn")
            btn.clicked.connect(lambda: self.done(QMessageBox.StandardButton.No))
            self._apply_button_style(btn)
            button_layout.addWidget(btn)

        if buttons & QMessageBox.StandardButton.Cancel:
            btn = QPushButton("取消")
            btn.setObjectName("cancelBtn")
            btn.clicked.connect(lambda: self.done(QMessageBox.StandardButton.Cancel))
            self._apply_button_style(btn)
            button_layout.addWidget(btn)

        button_layout.addStretch()
        content_layout.addLayout(button_layout)
        main_layout.addWidget(content_widget)

    def _apply_button_style(self, btn):
        style = """
            QPushButton#okBtn, QPushButton#yesBtn, QPushButton#noBtn, QPushButton#cancelBtn {
                text-align: center;
                padding: 8px 16px;
                border: 2px solid #bdc3c7;
                color: white;
                background-color: #3498db !important;
                font-size: 14px;
                font-weight: bold;
                border-radius: 15px;
                min-width: 120px;
                min-height: 30px;
                margin: 0px;
            }
            QPushButton#okBtn:hover, QPushButton#yesBtn:hover, QPushButton#noBtn:hover, QPushButton#cancelBtn:hover {
                color: red;
                background-color: #27ae60 !important;
                border: 2px solid #bdc3c7;
            }
            QPushButton#okBtn:pressed, QPushButton#yesBtn:pressed, QPushButton#noBtn:pressed, QPushButton#cancelBtn:pressed {
                color: red;
                background-color: #16d8de !important;
            }
        """
        btn.setStyleSheet(style)
        btn.setAutoFillBackground(True)
        btn.setFlat(False)

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event: QMouseEvent):
        if (event.button() == Qt.MouseButton.LeftButton and
                self.title_bar.geometry().contains(event.pos())):
            window = self.window()
            if window and window.windowHandle():
                window.windowHandle().startSystemMove()
            event.accept()
        else:
            super().mousePressEvent(event)