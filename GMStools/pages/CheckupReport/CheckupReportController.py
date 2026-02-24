import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QTimer

from .ReportAnalyzer import ReportAnalyzer


class CheckupReportController:
    """检查报告控制器 - 负责处理用户交互和业务逻辑"""
    
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.analyzer = None
        self.setup_connections()
    
    def setup_connections(self):
        """设置信号连接"""
        self.ui.select_directory_btn.clicked.connect(self.select_directory)
        self.ui.analyze_btn.clicked.connect(self.start_analysis)
        self.ui.clear_btn.clicked.connect(self.ui.clear_results)

    
    def select_directory(self):
        """选择报告目录"""
        directory = QFileDialog.getExistingDirectory(
            self.ui, 
            "选择报告目录",
            "",
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if directory:
            abs_path = os.path.abspath(directory)
            self.ui.directory_path.setText(abs_path)
            self.ui.analyze_btn.setEnabled(True)
            self.ui.result_text.clear()
            self.ui.result_text.append(f"已选择目录: {abs_path}")
            
            # 显示当前分析模式
            mode = self.ui.get_android_version_mode()
            if mode == "GO":
                mode_text = "GO版本模式 - 将检查APTS报告"
            elif mode == "FULL":
                mode_text = "FULL版本模式 - 不检查APTS报告"
            else:
                mode_text = "默认模式 - 检查所有报告（包括APTS）"
            
            self.ui.result_text.append(f"当前分析模式: {mode_text}")
            self.ui.result_text.append("点击'开始分析'按钮进行分析...")
    
    def start_analysis(self):
        """开始分析报告"""
        directory = self.ui.directory_path.text()
        if not directory or not os.path.exists(directory):
            QMessageBox.warning(self.ui, "错误", "请选择有效的目录!")
            return
        
        # 禁用按钮
        self.ui.set_analysis_state(False)
        
        # 清空结果区域
        self.ui.clear_results()
        self.ui.result_text.append("开始分析报告...")
        
        # 获取当前分析模式
        check_apts = self.ui.should_check_apts()
        mode = self.ui.get_android_version_mode()
        
        if mode == "GO":
            mode_text = "GO版本模式 - 检查APTS报告"
        elif mode == "FULL":
            mode_text = "FULL版本模式 - 不检查APTS报告"
        else:
            mode_text = "默认模式 - 检查所有报告（包括APTS）"
        
        self.ui.result_text.append(f"分析模式: {mode_text}")
        
        # 显示APTS检查规则
        if mode == "GO":
            self.ui.result_text.append("规则: GO版本必须包含APTS报告")
        elif mode == "FULL":
            self.ui.result_text.append("规则: FULL版本不应包含APTS报告")
        
        self.ui.result_text.append("=" * 50)
        
        # 创建并启动分析线程，传递check_apts参数
        self.analyzer = ReportAnalyzer(directory, check_apts)
        self.analyzer.analysis_finished.connect(self.on_analysis_finished)
        self.analyzer.error_occurred.connect(self.on_analysis_error)
        self.analyzer.start()
    
    def on_analysis_finished(self, full_results, error_results):
        """分析完成处理"""
        self.ui.update_results(full_results, error_results)
        self.ui.set_analysis_state(True)
        
        # 在UI中显示完成状态
        self.ui.result_text.append("\n" + "="*50)
        self.ui.result_text.append("*** 分析完成 ***")
        self.ui.result_text.append("提示: 右键点击错误行可选择PASS/FAIL状态")
        self.ui.result_text.append("="*50)
        
        # 滚动到底部
        self.ui.result_text.verticalScrollBar().setValue(
            self.ui.result_text.verticalScrollBar().maximum()
        )
    
    def on_analysis_error(self, error_msg):
        """分析错误处理"""
        self.ui.handle_analysis_error(error_msg)
        self.ui.set_analysis_state(True)
