import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFileDialog,
    QSizePolicy, QTextEdit, QMessageBox, QApplication, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, QSize, QPoint, QEvent
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen  # 添加 QPen
from ..Ctsverifierdb.device_manager import DeviceManager


class CVAutomation(QWidget):
    def __init__(self):
        super().__init__()
        self.device_manager = DeviceManager()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setup_ui()

        QTimer.singleShot(0, self.delayed_adb_check)

    def delayed_adb_check(self):
        self.device_manager.check_adb_environment(self.refresh_device_list, self.show_adb_error)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # 第一组：设备选择
        device_layout = QHBoxLayout()
        device_layout.setSpacing(6)

        self.device_btn = QPushButton("未选择设备")
        self.device_btn.setFixedHeight(36)
        self.device_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(0, 0, 0, 80);
                padding: 5px 12px;
                color: #333;
                font-size: 14px;
                border-radius: 0px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 200);
            }
            QPushButton:pressed {
                background-color: rgba(240, 240, 240, 200);
            }
        """)
        self.device_btn.clicked.connect(self.show_device_list)
        device_layout.addWidget(self.device_btn)

        self.refresh_btn = QPushButton("刷新设备")
        self.refresh_btn.setFixedSize(140, 36)
        self.refresh_btn.setStyleSheet(self.get_button_style())
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        device_layout.addWidget(self.refresh_btn)

        layout.addLayout(device_layout)

        # 第二组：目录选择
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(6)

        self.dir_path_edit = QLineEdit()
        self.dir_path_edit.setFixedHeight(36)
        self.dir_path_edit.setReadOnly(True)
        self.dir_path_edit.setStyleSheet(self.get_path_style())
        dir_layout.addWidget(self.dir_path_edit)

        self.select_dir_btn = QPushButton("选择目录")
        self.select_dir_btn.setFixedSize(140, 36)
        self.select_dir_btn.setStyleSheet(self.get_button_style())
        self.select_dir_btn.clicked.connect(self.on_select_dir_clicked)
        dir_layout.addWidget(self.select_dir_btn)

        layout.addLayout(dir_layout)

        # 第三组：测试控制
        test_layout = QHBoxLayout()
        test_layout.setSpacing(6)

        self.start_btn = QPushButton("开始测试")
        self.start_btn.setFixedHeight(36)
        self.start_btn.setStyleSheet(self.get_button_style())
        self.start_btn.clicked.connect(self.on_start_test_clicked)
        self.start_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        test_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("结束测试")
        self.stop_btn.setFixedHeight(36)
        self.stop_btn.setStyleSheet(self.get_button_style())
        self.stop_btn.clicked.connect(self.on_stop_test_clicked)
        self.stop_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        test_layout.addWidget(self.stop_btn)

        layout.addLayout(test_layout)

        # 第四组：信息输出
        self.info_output = QTextEdit()
        self.info_output.setReadOnly(True)
        self.info_output.setStyleSheet(self.get_output_style())
        self.info_output.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.info_output)

        self.info_output.append("欢迎使用 CV 自动化工具")
        self.info_output.append("请选择设备、目录后点击「开始测试」")

    # ---------- 样式 ----------
    def get_button_style(self) -> str:
        return """
            QPushButton {
                background-color: #3498db;
                border: 1px solid #bdc3c7;
                border-radius: 0px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover { color: red; }
            QPushButton:pressed { background-color: #2980b9; }
        """

    def get_path_style(self) -> str:
        return """
            QLineEdit {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(0, 0, 0, 80);
                padding: 5px 12px;
                color: #333;
                font-size: 14px;
                border-radius: 0px;
            }
        """

    def get_output_style(self) -> str:
        return """
            QTextEdit {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid rgba(0, 0, 0, 80);
                padding: 8px;
                color: #333;
                font-size: 12px;
                border-radius: 0px;
            }
        """

    # ---------- 设备管理 ----------
    def on_refresh_clicked(self):
        self.refresh_btn.setStyleSheet(self.get_button_style().replace("#3498db", "#2980b9"))
        self.refresh_device_list()
        QTimer.singleShot(1000, lambda: self.refresh_btn.setStyleSheet(self.get_button_style()))

    def refresh_device_list(self):
        try:
            devices = self.device_manager.get_adb_devices()
            self.devices = devices
            if not devices:
                self.device_btn.setText("未检测到设备")
                self.add_status_message("未检测到设备")
                return
            if len(devices) == 1:
                self.device_btn.setText(devices[0])
                self.add_status_message(f"单台设备，已自动选择: {devices[0]}")
            else:
                self.device_btn.setText("请选择设备...")
                self.add_status_message(f"多台设备，需要用户选择: {', '.join(devices)}")
        except Exception as e:
            self.add_status_message(f"刷新设备列表失败: {e}")

    def show_device_list(self):
        """自定义下拉列表，无滚动条但支持滚轮滚动，背景半透白（通过 paintEvent 绘制）"""
        if not hasattr(self, 'devices') or not self.devices:
            return

        # 定义内部 Popup 类，用于自定义绘制半透白背景
        class Popup(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent, Qt.WindowType.Popup)
                # 启用透明背景，以便绘制半透明颜色
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            def paintEvent(self, event):
                painter = QPainter(self)
                # 绘制半透白背景 (alpha=180)
                painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
                painter.setPen(QPen(QColor(0, 0, 0, 80), 1))
                painter.drawRect(self.rect())

        popup = Popup(self)

        layout = QVBoxLayout(popup)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 列表控件：滚动条完全隐藏，但滚轮可用
        list_widget = QListWidget()
        list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        list_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        list_widget.setMouseTracking(True)

        list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 12px;
                min-height: 30px;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: rgba(224, 224, 224, 200);
            }
            QListWidget::item:hover {
                background-color: rgba(224, 224, 224, 150);
            }
        """)

        # 填充设备列表
        for device in self.devices:
            item = QListWidgetItem(device)
            list_widget.addItem(item)

        def on_item_clicked(item):
            self.on_device_selected(item.text())
            popup.close()

        list_widget.itemClicked.connect(on_item_clicked)
        layout.addWidget(list_widget)

        # 设置弹出窗口宽度与按钮一致
        popup.setFixedWidth(self.device_btn.width())

        # 计算弹出位置（按钮正下方）
        pos = self.device_btn.mapToGlobal(self.device_btn.rect().bottomLeft())
        popup.move(pos)

        # 限制最大高度为84px，超出则自动滚动（无滚动条）
        popup.setMaximumHeight(84)
        item_height = list_widget.sizeHintForRow(0)
        list_widget.setFixedHeight(min(item_height * list_widget.count(), 84))

        # 显示并激活弹出窗口
        popup.show()
        popup.activateWindow()
        list_widget.setFocus()

        # 保存引用并安装事件过滤器（用于点击外部关闭）
        self.device_popup = popup
        popup.installEventFilter(self)

    def on_device_selected(self, device_text):
        self.device_btn.setText(device_text)
        self.add_status_message(f"设备已切换至: {device_text}")

    def show_adb_error(self, message):
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setWindowTitle("ADB环境错误")
        error_msg.setText(message)
        error_msg.setInformativeText("请确保已安装Android SDK并配置ADB环境变量")
        error_msg.exec()
        self.device_btn.setText("ADB环境异常")
        self.add_status_message("ADB环境异常: " + message)

    # ---------- 目录选择 ----------
    def on_select_dir_clicked(self):
        directory = QFileDialog.getExistingDirectory(
            None,
            "选择目录",
            self.dir_path_edit.text() or os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.dir_path_edit.setText(directory)
            self.info_output.append(f"已选择目录: {directory}")

    # ---------- 测试控制 ----------
    def on_start_test_clicked(self):
        self.info_output.append("开始测试...")

    def on_stop_test_clicked(self):
        self.info_output.append("结束测试...")

    # ---------- 辅助方法 ----------
    def add_status_message(self, message):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.info_output.append(f"[{timestamp}] {message}")

    def eventFilter(self, obj, event):
        """用于关闭弹出窗口（点击外部）"""
        if hasattr(self, 'device_popup') and obj is self.device_popup:
            if event.type() == QEvent.Type.WindowDeactivate:
                self.device_popup.close()
                return True
        return super().eventFilter(obj, event)