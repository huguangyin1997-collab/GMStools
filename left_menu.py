from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSizePolicy, QLabel, QScrollArea
from PyQt6.QtCore import pyqtSignal, Qt


class LeftMenu(QWidget):
    """
    左侧菜单栏类 - 负责左侧菜单的创建和交互
    采用初音未来主题风格设计
    """

    # 信号定义：当菜单项被点击时发射，携带菜单项的key
    item_clicked = pyqtSignal(str)

    def __init__(self, parent=None, width: int = 140):
        """初始化左侧菜单栏
        
        Args:
            parent: 父组件
            width: 菜单栏固定宽度，默认140像素
        """
        super().__init__(parent)
        self.setFixedWidth(width)  # 设置固定宽度
        self._items = []  # 存储菜单项列表，格式为[(key, button)]

        # 创建滚动区域，用于处理菜单项过多的情况
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)  # 设置窗口部件可调整大小
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # 隐藏水平滚动条
        self._scroll.setFrameStyle(0)  # 无边框样式

        # 创建容器窗口部件和垂直布局
        self._container = QWidget()
        self._vbox = QVBoxLayout(self._container)
        self._vbox.setContentsMargins(6, 6, 6, 6)  # 设置布局边距
        self._vbox.setSpacing(6)  # 设置组件间距
        self._vbox.addStretch()  # 添加弹性空间，将菜单项推向顶部

        self._scroll.setWidget(self._container)  # 将容器设置为滚动区域的窗口部件

        # 主布局设置
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 无边距
        layout.addWidget(self._scroll)  # 添加滚动区域到主布局

        # 设置样式表 - 初音未来主题风格
        self.setStyleSheet("""
        QWidget#LeftMenu {
            background-color: white;  /* 改为白色背景，与CheckupReportUI一致 */
        }

        QPushButton.menuItem {
            text-align: left;           /* 文字左对齐 */
            padding: 8px 16px;          /* 使用与CheckupReportUI按钮相同的内边距 */
            border: 2px solid #bdc3c7;  /* 使用与CheckupReportUI按钮相同的边框 */
            color: white;               /* 未选择时白色文字 */
            background-color: #3498db;  /* 未选择时背景为#3498db */
            font-size: 14px;            /* 使用与CheckupReportUI相同的字体大小 */
            font-weight: bold;          /* 使用与CheckupReportUI相同的字体粗细 */
            border-radius: 5px;         /* 使用与CheckupReportUI相同的圆角 */
            min-width: 120px;           /* 使用与CheckupReportUI按钮相同的最小宽度 */
            min-height: bold;           /* 确保按钮高度一致 */
        }

        QPushButton.menuItem:hover {
            color: red;                 /* 悬停时字体为红色 */
            background-color: #3498db;  /* 悬停时背景保持#3498db */
            border: 2px solid #bdc3c7;  /* 悬停时边框保持不变 */
        }

        QPushButton.menuItem:pressed {
            color: red;                 /* 按下时字体保持红色 */
            background-color: #2980b9;  /* 按下时背景变为更深的蓝色 */
        }

        QPushButton.menuItem[active="true"] {
            color: white;               /* 选中时白色文字 */
            font-weight: bold;          /* 加粗字体 */
            background-color: #27ae60;  /* 选中时背景变为#27ae60 */
            border: 2px solid #27ae60;  /* 选中时边框变为#27ae60 */
            border-radius: 5px;         /* 使用与CheckupReportUI相同的圆角 */
        }
    """)
        self.setObjectName("LeftMenu")  # 设置对象名称用于CSS选择器

    def add_item(self, key: str, label: str | None = None):
        """添加菜单项
        
        Args:
            key: 内部标识符，用于信号发射时识别
            label: 显示文本，默认为key值
            
        Returns:
            QPushButton: 创建的菜单按钮对象
        """
        if label is None:
            label = key

        # 移除弹性空间，以便新按钮位于顶部
        self._vbox.takeAt(self._vbox.count() - 1)

        # 创建菜单按钮
        btn = QPushButton(label, self._container)
        btn.setObjectName(f"menu_{key}")  # 设置对象名称
        btn.setProperty("class", "menuItem")  # 设置CSS类属性
        btn.setProperty("active", False)  # 设置激活状态属性
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # 设置大小策略：水平扩展，垂直固定
        btn.clicked.connect(lambda checked, k=key: self._on_item_clicked(k))  # 连接点击信号

        # 将按钮添加到布局并重新添加弹性空间
        self._vbox.addWidget(btn)
        self._vbox.addStretch()

        # 保存菜单项引用
        self._items.append((key, btn))
        return btn

    def _on_item_clicked(self, key: str):
        """处理菜单项点击事件
        
        Args:
            key: 被点击菜单项的标识符
        """
        # 更新所有按钮的激活状态
        for k, btn in self._items:
            is_active = (k == key)
            btn.setProperty("active", is_active)
            # 刷新样式以确保属性变化生效
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        # 发射点击信号
        self.item_clicked.emit(key)

    def clear(self):
        """清除所有菜单项"""
        for _k, btn in self._items:
            btn.setParent(None)  # 移除父组件关系
        self._items.clear()  # 清空菜单项列表
        # 确保弹性空间存在
        self._vbox.addStretch()

    def set_active(self, key: str):
        """以编程方式设置活动菜单项
        
        Args:
            key: 要设置为活动的菜单项标识符
        """
        for k, btn in self._items:
            is_active = (k == key)
            btn.setProperty("active", is_active)
            # 刷新样式以确保属性变化生效
            btn.style().unpolish(btn)
            btn.style().polish(btn)