import sys
import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QColor

from CustomTitle import CustomTitleBar
from PageManager import PageManager
from usekey import sign_disclaimer_accepted  # 修改为 usekey

class WindowManager(QMainWindow):
    def __init__(self, disclaimer_already_accepted=False, config_path=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("GMStools工具")
        self.resize(1200, 800)

        self.disclaimer_already_accepted = disclaimer_already_accepted
        self.config_path = config_path

        self.setup_background()
        self.setup_ui()

        if self.disclaimer_already_accepted:
            self.on_disclaimer_agreed(skip_save=True)
        else:
            self.connect_disclaimer_signals()

    def get_resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    def setup_background(self):
        image_path = self.get_resource_path("Miku.jpg")
        self.background_original = QPixmap(image_path)
        if self.background_original.isNull():
            print(f"❌ 背景图片加载失败: {image_path}")
            self.background_original = QPixmap(1200, 800)
            self.background_original.fill(QColor(52, 152, 219))
        self.update_background()

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

        self.page_manager = PageManager()

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

    def connect_disclaimer_signals(self):
        disclaimer_page = self.page_manager.get_page("Disclaimer")
        if disclaimer_page:
            disclaimer_page.agreed.connect(self.on_disclaimer_agreed)
            disclaimer_page.rejected.connect(self.close)

    def on_disclaimer_agreed(self, skip_save=False):
        if not skip_save and self.config_path:
            # 生成带签名的字符串并保存
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

    def update_background(self):
        if not hasattr(self, 'background_original'):
            return
        scaled_pixmap = self.background_original.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        if scaled_pixmap.width() > self.width() or scaled_pixmap.height() > self.height():
            x = (scaled_pixmap.width() - self.width()) // 2
            y = (scaled_pixmap.height() - self.height()) // 2
            scaled_pixmap = scaled_pixmap.copy(x, y, self.width(), self.height())
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
        self.setPalette(palette)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()
        else:
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self.update_background)
        self._resize_timer.start(100)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_background()

    def closeEvent(self, event):
        event.accept()