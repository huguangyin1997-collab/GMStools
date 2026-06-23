# SMR_UI.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QTextEdit
from PyQt6.QtCore import Qt

class SMR_UI:
    """SMR对比页面的UI组件"""
    
    def create_ui_components(self):
        """创建所有UI组件"""
        # 创建主垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)
        
        # 创建三行控制按钮
        self.create_control_rows(main_layout)
        
        # 创建结果显示区域
        self.create_result_displays(main_layout)
        
        return main_layout
    
    def create_control_rows(self, main_layout):
        """创建控制按钮行"""
        # 第一行：MR目录输入框 + MR按钮
        row1_container, self.mr_directory_input, self.select_mr_btn = self.create_directory_row(
            "请选择MR报告目录或full test测试报告", "选择MR/full test报告", "#4A90D9", "#3A7BC0", "#27ae60"
        )
        
        # 第二行：SMR目录输入框 + SMR按钮
        row2_container, self.smr_directory_input, self.select_smr_btn = self.create_directory_row(
            "请选择SMR报告目录或VBA测试报告", "选择SMR/VBA报告", "#4A90D9", "#3A7BC0", "#27ae60"
        )
        
        # 第三行：开始分析和清除记录按钮
        row3_container = self.create_action_row()
        
        # 将三行控制按钮添加到主垂直布局
        main_layout.addWidget(row1_container, 0, Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(row2_container, 0, Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(row3_container, 0, Qt.AlignmentFlag.AlignTop)
    
    def create_directory_row(self, placeholder, button_text, normal_color, hover_color, pressed_color):
        """创建目录选择行"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # 创建目录输入框
        directory_input = QLineEdit()
        directory_input.setPlaceholderText(placeholder)
        directory_input.setFixedHeight(36)
        directory_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 0 8px;
                font-size: 14px;
            }}
            QLineEdit:hover {{
                border-color: {normal_color};
            }}
            QLineEdit:focus {{
                border-color: {hover_color};
            }}
        """)
        
        # 创建选择按钮
        select_btn = QPushButton(button_text)
        select_btn.setFixedSize(190, 36)
        select_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {normal_color};
                color: white;
                border: none;
                padding: 0 15px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{ color: black; 
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
        """)
        
        # 将组件添加到布局
        layout.addWidget(directory_input, 1)
        layout.addWidget(select_btn, 0)
        
        return container, directory_input, select_btn
    
    def create_action_row(self):
        """创建操作按钮行"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        _btn_style = """
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 0 15px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{ color: black;
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: #27ae60;
            }}
        """

        # SMR报告分析按钮
        self.smr_analyze_btn = QPushButton("SMR报告分析")
        self.smr_analyze_btn.setFixedHeight(36)
        self.smr_analyze_btn.setStyleSheet(_btn_style.format(color="#4A90D9", hover="#3A7BC0"))

        # VBA报告分析按钮
        self.vba_analyze_btn = QPushButton("VBA报告分析")
        self.vba_analyze_btn.setFixedHeight(36)
        self.vba_analyze_btn.setStyleSheet(_btn_style.format(color="#4A90D9", hover="#3A7BC0"))

        # 清除记录按钮
        self.clear_btn = QPushButton("清除记录")
        self.clear_btn.setFixedHeight(36)
        self.clear_btn.setStyleSheet(_btn_style.format(color="#4A90D9", hover="#3A7BC0"))

        # 将按钮添加到布局
        layout.addWidget(self.smr_analyze_btn, 1)
        layout.addWidget(self.vba_analyze_btn, 1)
        layout.addWidget(self.clear_btn, 1)

        return container
    
    def create_result_displays(self, main_layout):
        """创建结果显示区域"""
        # 创建分析结果显示框
        self.analysis_result_display = QTextEdit()
        self.analysis_result_display.setPlaceholderText("分析结果显示区域")
        self.analysis_result_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(240, 248, 255, 0.7);
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        
        # 创建错误信息显示框
        self.error_info_display = QTextEdit()
        self.error_info_display.setPlaceholderText("错误信息显示区域")
        self.error_info_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        
        # 将显示框添加到布局
        main_layout.addWidget(self.analysis_result_display, 3)
        main_layout.addWidget(self.error_info_display, 2)