from PyQt6.QtWidgets import QWidget, QVBoxLayout
from .CheckupReportUI import CheckupReportUI
from .CheckupReportController import CheckupReportController

class CheckupReport(QWidget):
    """检查报告页面 - 整合UI和控制器"""
    
    def __init__(self):
        super().__init__()
        # 创建UI实例
        self.ui = CheckupReportUI()
        # 创建控制器实例并传入UI
        self.controller = CheckupReportController(self.ui)
        
        # 设置当前widget的布局
        layout = QVBoxLayout(self)
        layout.addWidget(self.ui)
        layout.setContentsMargins(0, 0, 0, 0)
    
    def get_widget(self):
        """获取UI组件
        
        Returns:
            QWidget: UI组件实例
        """
        return self.ui