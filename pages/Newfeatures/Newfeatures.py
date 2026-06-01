from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea,
                             QGridLayout, QFrame, QHBoxLayout)
from PyQt6.QtCore import Qt

class Newfeatures(QWidget):
    """新功能展示页面 - 展示新增功能列表"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("✨ 新功能 ✨")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 滚动区域（用于展示多个功能卡片）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        grid_layout = QGridLayout(content_widget)
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(10, 10, 10, 10)

        # 功能卡片数据 (标题, 描述, 版本)
        features = [
            ("解锁与镜像", "支持一键解锁设备并生成系统镜像，适用于开发和测试环境。", "v1.0"),
            ("日志查看器", "内置日志查看器，方便追踪程序运行状态和错误信息。", "v1.0"),
            ("数据导出", "支持导出检查报告、配置数据等为结构化文件。", "v1.0"),
            ("CV自动化增强", "优化了CV自动化流程，支持批量处理。", "v1.2"),
            ("暗色主题支持", "新增暗色主题，保护眼睛（即将推出）。", "v1.3"),
        ]

        for i, (title_text, desc, version) in enumerate(features):
            card = self.create_feature_card(title_text, desc, version)
            row = i // 2
            col = i % 2
            grid_layout.addWidget(card, row, col)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def create_feature_card(self, title_text, desc, version):
        """创建单个功能卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.7);
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                padding: 15px;
            }
            QFrame:hover {
                background-color: rgba(57, 197, 187, 0.08);
                border-color: #39C5BB;
            }
        """)
        layout = QVBoxLayout(card)

        title = QLabel(f"📌 {title_text}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #39C5BB;")
        layout.addWidget(title)

        desc_label = QLabel(desc)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(desc_label)

        version_label = QLabel(f"版本：{version}")
        version_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(version_label)

        return card