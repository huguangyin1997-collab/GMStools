from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont

class Concerning(QWidget):
    """关于开发页面"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("关于 GMStools")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            padding: 15px;
            background-color: rgba(255, 255, 255, 0.7);  /* 透明度调整为0.7 */
            border-radius: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 版本信息卡片
        version_card = QWidget()
        version_card.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.7);  /* 透明度调整为0.7 */
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            padding: 15px;
        """)
        version_layout = QVBoxLayout(version_card)
        
        version_title = QLabel("版本信息")
        version_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        version_layout.addWidget(version_title)
        
        version_label = QLabel("当前版本：v1.0.0 (2026.02.24)")
        version_label.setStyleSheet("font-size: 14px; color: #34495e;")
        version_layout.addWidget(version_label)
        
        build_label = QLabel("构建版本：Release 1.0.240224")
        build_label.setStyleSheet("font-size: 14px; color: #34495e;")
        version_layout.addWidget(build_label)
        
        layout.addWidget(version_card)

        # 开发者信息卡片
        developer_card = QWidget()
        developer_card.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.7);  /* 透明度调整为0.7 */
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            padding: 15px;
        """)
        dev_layout = QVBoxLayout(developer_card)
        
        dev_title = QLabel("开发团队")
        dev_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        dev_layout.addWidget(dev_title)
        
        dev_info = QLabel(
            "主程序：GMStools 开发组<br>"
            "贡献者：Your Name<br>"
            "特别感谢：所有测试用户"
        )
        dev_info.setTextFormat(Qt.TextFormat.RichText)
        dev_info.setStyleSheet("font-size: 14px; color: #34495e; line-height: 1.6;")
        dev_layout.addWidget(dev_info)
        
        layout.addWidget(developer_card)

        # 联系与支持卡片
        contact_card = QWidget()
        contact_card.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.7);  /* 透明度调整为0.7 */
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            padding: 15px;
        """)
        contact_layout = QVBoxLayout(contact_card)
        
        contact_title = QLabel("联系与支持")
        contact_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        contact_layout.addWidget(contact_title)
        
        contact_info = QLabel(
            "邮箱：support@gmstools.com<br>"
            "官网：https://www.gmstools.com<br>"
            "问题反馈：请在 GitHub 提交 issue"
        )
        contact_info.setTextFormat(Qt.TextFormat.RichText)
        contact_info.setStyleSheet("font-size: 14px; color: #34495e; line-height: 1.6;")
        contact_layout.addWidget(contact_info)
        
        layout.addWidget(contact_card)

        # 版权信息卡片
        copyright_card = QWidget()
        copyright_card.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.7);  /* 透明度调整为0.7 */
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            padding: 15px;
        """)
        copyright_layout = QVBoxLayout(copyright_card)
        
        copyright_title = QLabel("版权声明")
        copyright_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        copyright_layout.addWidget(copyright_title)
        
        copyright_text = QLabel(
            "© 2026 GMStools 开发组。保留所有权利。<br>"
            "本软件按“原样”提供，详情请参阅免责声明。"
        )
        copyright_text.setTextFormat(Qt.TextFormat.RichText)
        copyright_text.setStyleSheet("font-size: 14px; color: #34495e; line-height: 1.6;")
        copyright_layout.addWidget(copyright_text)
        
        layout.addWidget(copyright_card)

        # 添加弹性空间使内容靠上
        layout.addStretch()