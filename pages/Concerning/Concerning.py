# concerning.py
import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, QStandardPaths

from .constants import APP_VERSION
from .miku_dialog import MikuDialog
from .update_manager import UpdateManager


class Concerning(QWidget):
    """关于开发页面（带滚动区域）"""

    def __init__(self):
        super().__init__()

        self.app_data_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppLocalDataLocation
        )
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir)

        # 创建更新管理器，传入自身作为父窗口（用于对话框）
        self.update_manager = UpdateManager(parent_widget=self)
        self.update_manager.cleanup_pending_temp()  # 清理上次更新遗留的临时目录

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(0)
        main_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("关于 GMStools")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50; padding: 15px; background-color: rgba(255, 255, 255, 0.7); border-radius: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version_card = QWidget()
        version_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border: 2px solid #bdc3c7; border-radius: 8px; padding: 15px;")
        version_layout = QVBoxLayout(version_card)

        version_title = QLabel("版本信息")
        version_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        version_layout.addWidget(version_title)

        self.version_label = QLabel(f"当前版本：{APP_VERSION}")
        self.version_label.setStyleSheet("font-size: 14px; color: #34495e;")
        version_layout.addWidget(self.version_label)

        build_label = QLabel(f"构建版本：Release {APP_VERSION}")
        build_label.setStyleSheet("font-size: 14px; color: #34495e;")
        version_layout.addWidget(build_label)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        self.check_btn = QPushButton("检查更新")
        self.check_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-size: 14px; font-weight: bold; padding: 8px 16px; border-radius: 5px; border: none; } QPushButton:hover { background-color: #2980b9; } QPushButton:pressed { background-color: #216694; }")
        self.check_btn.clicked.connect(self.check_for_updates)
        button_layout.addStretch()
        button_layout.addWidget(self.check_btn)
        button_layout.addStretch()

        version_layout.addLayout(button_layout)
        layout.addWidget(version_card)

        developer_card = QWidget()
        developer_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border: 2px solid #bdc3c7; border-radius: 8px; padding: 15px;")
        dev_layout = QVBoxLayout(developer_card)
        dev_title = QLabel("开发团队")
        dev_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        dev_layout.addWidget(dev_title)
        dev_info = QLabel("主程序：GMStools 开发组<br>贡献者：Huguangyin<br>特别感谢：所有测试用户")
        dev_info.setTextFormat(Qt.TextFormat.RichText)
        dev_info.setStyleSheet("font-size: 14px; color: #34495e; line-height: 1.6;")
        dev_layout.addWidget(dev_info)
        layout.addWidget(developer_card)

        contact_card = QWidget()
        contact_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border: 2px solid #bdc3c7; border-radius: 8px; padding: 15px;")
        contact_layout = QVBoxLayout(contact_card)
        contact_title = QLabel("联系与支持")
        contact_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        contact_layout.addWidget(contact_title)
        contact_info = QLabel("邮箱：1737660582@qq.com<br>github：https://github.com/huguangyin1997-collab/GMStools.git<br>问题反馈：请邮箱或 GitHub")
        contact_info.setTextFormat(Qt.TextFormat.RichText)
        contact_info.setStyleSheet("font-size: 14px; color: #34495e; line-height: 1.6;")
        contact_layout.addWidget(contact_info)
        layout.addWidget(contact_card)

        copyright_card = QWidget()
        copyright_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border: 2px solid #bdc3c7; border-radius: 8px; padding: 15px;")
        copyright_layout = QVBoxLayout(copyright_card)
        copyright_title = QLabel("版权声明")
        copyright_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        copyright_layout.addWidget(copyright_title)
        copyright_text = QLabel("© 2026 GMStools 开发组。保留所有权利。<br>本软件按“原样”提供，详情请参阅免责声明。")
        copyright_text.setTextFormat(Qt.TextFormat.RichText)
        copyright_text.setStyleSheet("font-size: 14px; color: #34495e; line-height: 1.6;")
        copyright_layout.addWidget(copyright_text)
        layout.addWidget(copyright_card)

    def check_for_updates(self):
        """点击按钮时调用更新管理器进行检查"""
        self.update_manager.check_for_updates(button=self.check_btn)