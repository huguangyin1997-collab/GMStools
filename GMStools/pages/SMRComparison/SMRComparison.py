from PyQt6.QtWidgets import QWidget
from datetime import datetime
from .Select_directory import Select_directory
from .SMR_UI import SMR_UI
from .SMR_Analyzer import SMR_Analyzer
from .SMR_EventHandler import SMR_EventHandler

class SMRComparison(QWidget, SMR_UI):
    """SMR对比页面"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # 初始化分析器和事件处理器
        self.analyzer = SMR_Analyzer()
        self.event_handler = SMR_EventHandler(
            ui=self, 
            analyzer=self.analyzer,
            select_directory_func=Select_directory
        )
    
    def setup_ui(self):
        """设置SMR对比页面UI"""
        self.create_ui_components()