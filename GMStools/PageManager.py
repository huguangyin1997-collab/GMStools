from PyQt6.QtWidgets import QStackedWidget, QMessageBox
from left_menu import LeftMenu
from pages import Ctsverifierdb, Modulecomparison, Concerning, CheckupReport, SMRComparison, CVAutomation, Disclaimer

class PageManager:
    def __init__(self):
        self.left_menu = None
        self.stacked_widget = None
        self.pages = {}
        
        # 免责声明是否已被同意
        self.disclaimer_accepted = False
        
        self.setup_ui()
        self.create_pages()
        self.add_menu_items()
    
    def setup_ui(self):
        self.left_menu = LeftMenu()
        self.left_menu.item_clicked.connect(self.on_menu_item_clicked)
        self.stacked_widget = QStackedWidget()
    
    def create_pages(self):
        self.pages["CheckupReport"] = CheckupReport()
        self.stacked_widget.addWidget(self.pages["CheckupReport"])
        
        self.pages["Ctsverifierdb"] = Ctsverifierdb()
        self.stacked_widget.addWidget(self.pages["Ctsverifierdb"])
        
        self.pages["Modulecomparison"] = Modulecomparison()
        self.stacked_widget.addWidget(self.pages["Modulecomparison"])
        
        self.pages["SMRComparison"] = SMRComparison()
        self.stacked_widget.addWidget(self.pages["SMRComparison"])
        
        self.pages["CVAutomation"] = CVAutomation()
        self.stacked_widget.addWidget(self.pages["CVAutomation"])
        
        self.pages["Disclaimer"] = Disclaimer()
        self.stacked_widget.addWidget(self.pages["Disclaimer"])
        
        self.pages["Concerning"] = Concerning()
        self.stacked_widget.addWidget(self.pages["Concerning"])
    
    def add_menu_items(self):
        self.left_menu.add_item("CheckupReport", "检查报告")
        self.left_menu.add_item("Ctsverifierdb", "DB工具")
        self.left_menu.add_item("Modulecomparison", "模块对比")
        self.left_menu.add_item("SMRComparison", "SMR对比")
        self.left_menu.add_item("CVAutomation", "CV自动化")
        self.left_menu.add_item("Disclaimer", "免责声明")
        self.left_menu.add_item("Concerning", "关于我们")
        
        # 默认显示免责声明页面（索引5）
        self.stacked_widget.setCurrentIndex(5)
    
    def on_menu_item_clicked(self, key):
        if key == "Disclaimer":
            disclaimer_page = self.pages.get("Disclaimer")
            if disclaimer_page:
                disclaimer_page.set_readonly_mode(self.disclaimer_accepted)
            self.stacked_widget.setCurrentIndex(5)
            self.left_menu.set_active(key)
            return
        
        if not self.disclaimer_accepted:
            QMessageBox.warning(
                self.left_menu,
                "操作受限",
                "请先阅读并同意免责声明后再使用其他功能。"
            )
            return
        
        page_mapping = {
            "CheckupReport": 0,
            "Ctsverifierdb": 1,
            "Modulecomparison": 2,
            "SMRComparison": 3,
            "CVAutomation": 4,
            "Disclaimer": 5,
            "Concerning": 6
        }
        if key in page_mapping:
            self.stacked_widget.setCurrentIndex(page_mapping[key])
            self.left_menu.set_active(key)
    
    def get_page(self, page_name):
        return self.pages.get(page_name)
    
    def set_current_page(self, page_name):
        page_mapping = {
            "CheckupReport": 0,
            "Ctsverifierdb": 1,
            "Modulecomparison": 2,
            "SMRComparison": 3,
            "CVAutomation": 4,
            "Disclaimer": 5,
            "Concerning": 6
        }
        if page_name in page_mapping:
            self.stacked_widget.setCurrentIndex(page_mapping[page_name])
            self.left_menu.set_active(page_name)