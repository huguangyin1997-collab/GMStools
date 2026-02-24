# SMR_EventHandler.py
from datetime import datetime

class SMR_EventHandler:
    """SMR对比页面事件处理器"""
    
    def __init__(self, ui, analyzer, select_directory_func):
        self.ui = ui
        self.analyzer = analyzer
        self.select_directory = select_directory_func
        
        # 连接按钮点击事件
        self.ui.select_mr_btn.clicked.connect(self.select_mr_directory)
        self.ui.select_smr_btn.clicked.connect(self.select_smr_directory)
        self.ui.analyze_btn.clicked.connect(self.start_analysis)
        self.ui.clear_btn.clicked.connect(self.clear_records)
        
        # 初始时更新按钮样式
        self.update_button_styles()
        
        # 连接输入框文本变化信号
        self.ui.mr_directory_input.textChanged.connect(self.update_button_styles)
        self.ui.smr_directory_input.textChanged.connect(self.update_button_styles)
        self.ui.analysis_result_display.textChanged.connect(self.update_button_styles)
        self.ui.error_info_display.textChanged.connect(self.update_button_styles)
    
    def update_button_styles(self):
        """根据条件更新按钮样式"""
        # 1. 选择MR报告按钮
        if self.ui.mr_directory_input.text().strip():
            self.ui.select_mr_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 0 15px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #27ae60;
                }
            """)
        else:
            self.ui.select_mr_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 0 15px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #27ae60;
                }
            """)
        
        # 2. 选择SMR报告按钮
        if self.ui.smr_directory_input.text().strip():
            self.ui.select_smr_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 0 15px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #27ae60;
                }
            """)
        else:
            self.ui.select_smr_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 0 15px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #27ae60;
                }
            """)
        
        # 3. 开始分析按钮
        if self.ui.analysis_result_display.toPlainText().strip():
            self.ui.analyze_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 0 15px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #27ae60;
                }
            """)
        else:
            self.ui.analyze_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 0 15px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #27ae60;
                }
            """)
        
        # 4. 清除记录按钮
        if self.ui.error_info_display.toPlainText().strip():
            self.ui.clear_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    padding: 0 15px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #27ae60;
                }
            """)
        else:
            self.ui.clear_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 0 15px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #27ae60;
                }
            """)
    
    def select_mr_directory(self):
        """打开目录选择对话框 - MR报告"""
        directory = self.select_directory("选择MR报告目录", self.ui)
        if directory:
            self.ui.mr_directory_input.setText(directory)
            print(f"选择的MR报告目录: {directory}")
            # 更新按钮样式
            self.update_button_styles()
    
    def select_smr_directory(self):
        """打开目录选择对话框 - SMR报告"""
        directory = self.select_directory("选择SMR报告目录", self.ui)
        if directory:
            self.ui.smr_directory_input.setText(directory)
            print(f"选择的SMR报告目录: {directory}")
            # 更新按钮样式
            self.update_button_styles()
    
    def start_analysis(self):
        """开始分析按钮点击事件"""
        print("开始分析...")
        
        # 清除显示框内容
        self.ui.analysis_result_display.clear()
        self.ui.error_info_display.clear()
        
        # 获取目录路径
        mr_dir = self.ui.mr_directory_input.text()
        smr_dir = self.ui.smr_directory_input.text()
        
        if not mr_dir or not smr_dir:
            error_msg = "错误: 请先选择MR和SMR报告目录\n\n请点击上方按钮选择对应的报告目录。"
            self.ui.error_info_display.setPlainText(error_msg)
            self.update_button_styles()
            return
        
        self.update_button_styles()
        
        # 开始分析
        complete_log, final_verdict_text = self.analyzer.analyze_directories(mr_dir, smr_dir)
        
        # 显示完整日志在分析结果区域（不包含最终判定结果）
        if complete_log:
            self.ui.analysis_result_display.setPlainText(complete_log)
        
        # 显示最终的判定结果在错误信息区域
        if final_verdict_text:
            print(f"显示最终判定结果，长度: {len(final_verdict_text)}")
            self.ui.error_info_display.setPlainText(final_verdict_text)
        elif not complete_log:
            # 如果分析和日志都失败，显示错误信息
            self.ui.error_info_display.setPlainText("分析失败，请检查输入的目录是否正确。")
        else:
            # 如果有完整日志但没有最终判定，这是不应该发生的
            success_msg = "✓ 分析完成！但未生成最终判定结果。"
            self.ui.error_info_display.setPlainText(success_msg)
        
        self.update_button_styles()
    
    def clear_records(self):
        """清除记录按钮点击事件 - 完全重置到初始状态"""
        print("清除记录...")
        
        # 清除输入框内容
        self.ui.mr_directory_input.clear()
        self.ui.smr_directory_input.clear()
        
        # 清除显示框内容
        self.ui.analysis_result_display.clear()
        self.ui.error_info_display.clear()
        
        # 更新按钮样式
        self.update_button_styles()
        
        # 设置显示框的默认提示文本
        self.ui.analysis_result_display.setPlaceholderText("分析结果显示区域")
        self.ui.error_info_display.setPlaceholderText("错误信息显示区域")
        
        # 输出清除完成信息
        print("界面已完全重置到初始状态")