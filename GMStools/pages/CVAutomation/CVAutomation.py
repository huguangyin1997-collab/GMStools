from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QFileDialog
from PyQt6.QtCore import Qt

class CVAutomation(QWidget):
    """CV自动化页面"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """设置CV自动化页面UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 页面标题
        title = QLabel("CV自动化工具")
        title.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #2c3e50;
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.8);
            border-radius: 8px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 功能介绍
        intro_text = QLabel("CTSV（Compatibility Test Suite Verifier）")
        intro_text.setStyleSheet("font-size: 14px; color: #34495e; padding: 10px;")
        intro_text.setWordWrap(True)
        layout.addWidget(intro_text)
        
        # 配置输入区域
        self.config_area = QTextEdit()  # 改为实例变量以便后续访问
        self.config_area.setPlaceholderText("CV配置输入区域...\n\n请输入或粘贴配置信息")
        self.config_area.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 15px;
                font-size: 14px;
                min-height: 150px;
            }
        """)
        layout.addWidget(self.config_area)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.load_config_btn = QPushButton("加载配置")  # 改为实例变量
        self.load_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        button_layout.addWidget(self.load_config_btn)
        
        self.run_cv_btn = QPushButton("运行CV验证")
        self.run_cv_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        button_layout.addWidget(self.run_cv_btn)
        
        layout.addLayout(button_layout)
        
        # 结果展示区域
        result_label = QLabel("验证结果:")
        result_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-top: 15px;")
        layout.addWidget(result_label)
        
        self.result_area = QTextEdit()  # 改为实例变量
        self.result_area.setPlaceholderText("CV验证结果将显示在这里...")
        self.result_area.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 15px;
                font-size: 14px;
                min-height: 150px;
            }
        """)
        layout.addWidget(self.result_area)
        
        # 添加弹性空间
        layout.addStretch()
    
    def connect_signals(self):
        """连接信号与槽"""
        self.load_config_btn.clicked.connect(self.load_config)
    
    def load_config(self):
        """加载配置文件内容到配置输入区域"""
        # 打开文件对话框，选择配置文件
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择配置文件",
            "",  # 默认目录，可根据需要修改
            "配置文件 (*.conf *.ini *.txt);;所有文件 (*.*)"
        )
        
        if file_path:  # 如果用户选择了文件（未取消）
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                self.config_area.setPlainText(content)
            except Exception as e:
                # 如果读取失败，可以在结果区域显示错误信息
                self.result_area.setPlainText(f"读取文件失败: {str(e)}")