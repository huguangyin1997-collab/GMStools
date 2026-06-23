from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QStackedWidget, QWidget, QLabel, QVBoxLayout
from left_menu import LeftMenu
from pages import (
    CheckupReport, Ctsverifierdb, Modulecomparison, Concerning,
    SMRComparison, CVAutomation, Disclaimer, Autounlock, Newfeatures,
    GMSAnalysis, EnvironmentSetup
)


class _Placeholder(QWidget):
    """占位页面，显示加载中标识"""
    def __init__(self, name):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel(name)
        label.setStyleSheet("color: rgba(255,255,255,80); font-size: 20px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


class PageManager:
    # 页面类注册表 + 顺序（决定 QStackedWidget 索引）
    _PAGE_SPEC = [
        ("CheckupReport",   CheckupReport,   "检查报告"),
        ("Ctsverifierdb",   Ctsverifierdb,   "DB工具"),
        ("Modulecomparison", Modulecomparison, "模块对比"),
        ("SMRComparison",   SMRComparison,   "SMR&&VBA对比"),
        ("CVAutomation",    CVAutomation,    "CV自动化"),
        ("Autounlock",      Autounlock,      "解锁与镜像"),
        ("GMSAnalysis",     GMSAnalysis,     "GMS简析"),
        ("EnvironmentSetup", EnvironmentSetup, "环境搭建"),
        ("Newfeatures",     Newfeatures,     "新功能"),
        ("Disclaimer",      Disclaimer,      "免责声明"),
        ("Concerning",      Concerning,      "关于我们"),
    ]

    def __init__(self, parent_widget=None):
        self.left_menu = None
        self.stacked_widget = None
        self.pages = {}          # name → widget (None=placeholder)
        self._page_idx = {}      # name → stacked index
        self.disclaimer_accepted = False
        self.parent_widget = parent_widget
        self.setup_ui()
        self.create_pages()
        self.add_menu_items()

    def setup_ui(self):
        self.left_menu = LeftMenu(self.parent_widget)
        self.left_menu.item_clicked.connect(self.on_menu_item_clicked)
        self.stacked_widget = QStackedWidget(self.parent_widget)
        self.stacked_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def create_pages(self):
        """延迟加载：启动时只创建占位 widget 和默认显示的 Disclaimer 页面。
        其余页面首次点击时才实例化，大幅减少启动耗时。"""
        for idx, (name, _cls, _label) in enumerate(self._PAGE_SPEC):
            self._page_idx[name] = idx
            if name == "Disclaimer":
                # 默认显示页：直接创建真实页面
                page = Disclaimer()
                self.pages[name] = page
                self.stacked_widget.addWidget(page)
            else:
                # 其余页面：先放占位，首次点击时替换
                placeholder = _Placeholder(name)
                self.pages[name] = placeholder     # 初始存占位
                self.stacked_widget.addWidget(placeholder)
        # 默认显示免责声明
        self.stacked_widget.setCurrentIndex(self._page_idx["Disclaimer"])

    def _ensure_page_loaded(self, name):
        """如果页面还是占位 widget，替换为真实页面"""
        widget = self.pages.get(name)
        if widget is None or not isinstance(widget, _Placeholder):
            return
        # 找到页面类并实例化
        for n, cls, _label in self._PAGE_SPEC:
            if n == name:
                real_page = cls()
                break
        else:
            return
        idx = self._page_idx[name]
        # 先移除占位再插入真实页面，保持索引不变
        self.stacked_widget.removeWidget(widget)
        self.stacked_widget.insertWidget(idx, real_page)
        widget.deleteLater()
        self.pages[name] = real_page

    def add_menu_items(self):
        for name, _cls, label in self._PAGE_SPEC:
            self.left_menu.add_item(name, label)

    def on_menu_item_clicked(self, key):
        if key == "Disclaimer":
            disclaimer_page = self.pages.get("Disclaimer")
            if disclaimer_page:
                disclaimer_page.set_readonly_mode(self.disclaimer_accepted)
            self.stacked_widget.setCurrentIndex(self._page_idx["Disclaimer"])
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

        # 首次点击：替换占位为真实页面
        self._ensure_page_loaded(key)
        self.stacked_widget.setCurrentIndex(self._page_idx[key])
        self.left_menu.set_active(key)

    def get_page(self, page_name):
        self._ensure_page_loaded(page_name)
        return self.pages.get(page_name)

    def set_current_page(self, page_name):
        self._ensure_page_loaded(page_name)
        idx = self._page_idx.get(page_name)
        if idx is not None:
            self.stacked_widget.setCurrentIndex(idx)
            self.left_menu.set_active(page_name)
