from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent

from CustomTitle.titleWindowControlButtons import WindowControlButtons


class CustomTitleBar(QWidget):
    """标题栏类 - 使用窗口句柄实现拖动"""
    
    # 定义信号：最小化、最大化/还原、关闭窗口
    minimize_signal = pyqtSignal()
    maximize_signal = pyqtSignal()
    close_signal = pyqtSignal()

    def __init__(self, parent=None):
        """初始化自定义标题栏
        
        Args:
            parent: 父窗口组件
        """
        super().__init__(parent)
        self.setFixedHeight(44)
        
        # 设置标题栏样式 - 将颜色改为黑色并加粗
        self.setStyleSheet("""
            CustomTitleBar {
                background-color: #2c3e50;
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
            }
            QLabel {
                background-color: transparent;
                color: #000000;  /* 改为黑色 */
                font-size: 18px;
                font-weight: 900;  /* 改为900，更粗 */
                font-family: "Microsoft YaHei", "Segoe UI";
                padding: 0 6px;
            }
        """)
        
        # 创建水平布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(0)

        # 创建标题标签
        title_label = QLabel("GMStools工具")
        title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title_label)

        layout.addStretch()  # 添加弹性空间，将控制按钮推到右侧

        # 创建窗口控制按钮组件
        self.control_buttons = WindowControlButtons()
        # 连接控制按钮的信号到标题栏的信号
        self.control_buttons.minimize_signal.connect(self.minimize_signal.emit)
        self.control_buttons.maximize_signal.connect(self.maximize_signal.emit)
        self.control_buttons.close_signal.connect(self.close_signal.emit)
        
        layout.addWidget(self.control_buttons)
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件处理 - 开始窗口拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 使用窗口句柄开始系统拖动
            window = self.window()
            if window and window.windowHandle():
                window.windowHandle().startSystemMove()
            event.accept()
        else:
            super().mousePressEvent(event)