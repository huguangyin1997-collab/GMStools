from PyQt6.QtWidgets import QStackedWidget
from left_menu import LeftMenu
from pages import (
    CheckupReport, Ctsverifierdb, Modulecomparison, Concerning,
    SMRComparison, CVAutomation, Disclaimer, Autounlock, Newfeatures
)

class PageManager:
    def __init__(self, parent_widget=None):
        self.left_menu = None
        self.stacked_widget = None
        self.pages = {}
        self.disclaimer_accepted = False
        self.parent_widget = parent_widget
        self.setup_ui()
        self.create_pages()
        self.add_menu_items()

    def setup_ui(self):
        self.left_menu = LeftMenu(self.parent_widget)
        self.left_menu.item_clicked.connect(self.on_menu_item_clicked)
        self.stacked_widget = QStackedWidget(self.parent_widget)

    def create_pages(self):
        # 原有页面
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

        # 新增两个页面
        self.pages["Autounlock"] = Autounlock()
        self.stacked_widget.addWidget(self.pages["Autounlock"])

        self.pages["Newfeatures"] = Newfeatures()
        self.stacked_widget.addWidget(self.pages["Newfeatures"])

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
        self.left_menu.add_item("Autounlock", "解锁与镜像")
        self.left_menu.add_item("Newfeatures", "新功能")
        self.left_menu.add_item("Disclaimer", "免责声明")
        self.left_menu.add_item("Concerning", "关于我们")

        # 默认显示免责声明页面（索引7）
        self.stacked_widget.setCurrentIndex(7)

    def on_menu_item_clicked(self, key):
        if key == "Disclaimer":
            disclaimer_page = self.pages.get("Disclaimer")
            if disclaimer_page:
                disclaimer_page.set_readonly_mode(self.disclaimer_accepted)
            self.stacked_widget.setCurrentIndex(7)
            self.left_menu.set_active(key)
            return

        if not self.disclaimer_accepted:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.left_menu,
                "操作受限",
                "请先阅读并同意免责声明后再使用其他功能。"
            )
            return

        # 页面索引映射
        page_mapping = {
            "CheckupReport": 0,
            "Ctsverifierdb": 1,
            "Modulecomparison": 2,
            "SMRComparison": 3,
            "CVAutomation": 4,
            "Autounlock": 5,
            "Newfeatures": 6,
            "Disclaimer": 7,
            "Concerning": 8
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
            "Autounlock": 5,
            "Newfeatures": 6,
            "Disclaimer": 7,
            "Concerning": 8
        }
        if page_name in page_mapping:
            self.stacked_widget.setCurrentIndex(page_mapping[page_name])
            self.left_menu.set_active(page_name)