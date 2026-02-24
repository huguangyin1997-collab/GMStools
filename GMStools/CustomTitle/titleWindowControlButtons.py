from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal, pyqtProperty
from PyQt6.QtGui import QColor


class WindowControlButtons(QWidget):
    """窗口控制按钮组件 - 专门处理最小化、最大化和关闭按钮"""
    
    minimize_signal = pyqtSignal()
    maximize_signal = pyqtSignal()
    close_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_maximized = False
        
        # 设置样式
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent; /* 永远透明，避免黑色背景块 */
                color: #000000;  /* 未选中时为黑色 */
                font-size: 14px;  /* 使用适中的图标尺寸 */
                font-weight: normal;
                padding: 0px;
                margin: 0px;
                /* 优先使用非彩色的系统字体（DejaVu 在 Linux 上常见），避免回退到彩色 emoji */
                font-family: "DejaVu Sans", "Noto Sans", "Segoe UI Symbol", sans-serif;
                text-align: center;
                line-height: 50px;  /* 与放大后的按钮高度匹配 */
            }
            /* 悬停/按下时不改变背景，只改变图标颜色 */
            QPushButton:hover {
                background-color: transparent;
                color: #007BFF;  /* 悬停时为蓝色 */
            }
            QPushButton:pressed {
                background-color: transparent;
                color: #FF0000;  /* 按下/选中时为红色 */
            }
            /* 普通按钮（最小化/最大化）颜色规则 */
            QPushButton#minBtn, QPushButton#maxBtn {
                width: 70px;  /* 加大按钮宽度 */
                height: 50px; /* 加大按钮高度 */
            }
            /* 关闭按钮单独控制 */
            QPushButton#closeBtn {
                width: 70px;
                height: 50px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)  # 按钮之间留小间距

        # 最小化按钮
        min_btn = QPushButton("─")  # VS Code 风格的最小化图标
        min_btn.setObjectName("minBtn")
        min_btn.setFixedSize(60, 40)
        min_btn.setFlat(True)
        min_btn.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        min_btn.clicked.connect(self.minimize_signal.emit)
        layout.addWidget(min_btn)

        # 最大化按钮
        self.max_btn = QPushButton("□")  # VS Code 风格的最大化图标
        self.max_btn.setObjectName("maxBtn")
        self.max_btn.setFixedSize(60, 40)
        self.max_btn.setFlat(True)
        self.max_btn.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.max_btn.clicked.connect(self._handle_maximize)
        layout.addWidget(self.max_btn)

        # 关闭按钮
        close_btn = QPushButton("×")  # VS Code 风格的关闭图标
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(60, 40)
        close_btn.setFlat(True)
        close_btn.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        close_btn.clicked.connect(self.close_signal.emit)
        layout.addWidget(close_btn)
    
    def _handle_maximize(self):
        """处理最大化/还原按钮点击"""
        self._is_maximized = not self._is_maximized
        # 使用普通符号而非 Emoji，避免系统渲染出彩色/黑色块
        self.max_btn.setText("❐" if self._is_maximized else "□")  # 还原/最大化符号
        self.maximize_signal.emit()