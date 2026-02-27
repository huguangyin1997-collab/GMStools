from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QHBoxLayout, QPushButton, QMessageBox, QTextEdit, QLabel
from PyQt6.QtCore import Qt, QTimer
import os

from .device_manager import DeviceManager
from .directory_manager import DirectoryManager
from .ui_styles import UIStyles
from .operation_handler import OperationHandler

class MainWindow(QWidget):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.device_manager = DeviceManager()
        self.ui_styles = UIStyles()
        self.directory_manager = DirectoryManager(self)
        self.operation_handler = OperationHandler(self.device_manager, self.directory_manager)
        self.setup_ui()
        
        # 使用单次定时器延迟执行 ADB 检查，避免阻塞 GUI 启动
        QTimer.singleShot(0, self.delayed_adb_check)
    
    def delayed_adb_check(self):
        """延迟执行的 ADB 环境检查"""
        self.device_manager.check_adb_environment(self.refresh_device_list, self.show_adb_error)
    
    def setup_ui(self):
        """设置主界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # 设备选择区域
        self.setup_device_selection(layout)
        
        # 路径选择区域
        self.directory_manager.setup_directory_ui(layout)
        
        # 导入导出按钮区域
        self.setup_action_buttons(layout)
        
        # 状态显示区域
        self.setup_status_frame(layout)
        
        # 功能介绍区域
        self.setup_info_section(layout)
        
        # 添加拉伸因子
        layout.addStretch(1)
    
    def setup_device_selection(self, layout):
        """设置设备选择区域"""
        device_layout = QHBoxLayout()
        device_layout.setSpacing(6)
        
        self.device_combo = QComboBox()
        self.device_combo.setFixedHeight(36)
        self.device_combo.setStyleSheet(self.ui_styles.get_combo_style(False))
        self.device_combo.currentTextChanged.connect(self.on_device_changed)
        
        self.refresh_btn = QPushButton("刷新设备")
        self.refresh_btn.setFixedSize(140, 36)
        self.refresh_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        
        # 新增清除记录按钮
        self.clear_log_btn = QPushButton("清除记录")
        self.clear_log_btn.setFixedSize(140, 36)
        self.clear_log_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        self.clear_log_btn.clicked.connect(self.clear_status_messages)
        
        device_layout.addWidget(self.device_combo)
        device_layout.addWidget(self.refresh_btn)
        device_layout.addWidget(self.clear_log_btn)
        layout.addLayout(device_layout)
    
    def setup_action_buttons(self, layout):
        """设置操作按钮区域"""
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        # 交换按钮位置：先添加导出按钮，再添加导入按钮
        self.export_btn = QPushButton("开始导出")
        self.export_btn.setFixedHeight(36)
        self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))  # 初始为未选中状态
        self.export_btn.clicked.connect(self.start_export)
        
        self.import_btn = QPushButton("开始导入")
        self.import_btn.setFixedHeight(36)
        self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))  # 初始为未选中状态
        self.import_btn.clicked.connect(self.start_import)
        
        action_layout.addWidget(self.export_btn)
        action_layout.addWidget(self.import_btn)
        layout.addLayout(action_layout)
    
    def setup_status_frame(self, layout):
        """设置状态显示区域"""
        # 创建文本框用于显示状态
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet(self.ui_styles.get_status_text_style(False))  # 初始为蓝色边框
        self.status_text.setMinimumHeight(200)
        
        # 设置初始文本
        self.status_text.setPlainText("操作日志将显示在这里...\n\n")
        
        # 直接添加文本框到布局，不使用外部框架
        layout.addWidget(self.status_text, 2)
    
    def setup_info_section(self, layout):
        """设置功能介绍区域"""
        # 创建介绍文本
        info_label = QLabel()
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 8px;
                font-size: 13px;
                font-weight: bold;
                color: #2c3e50;
                line-height: 1.4;
            }
        """)
        
        info_text = "• 导出：从设备导出CTS Verifier测试数据库<br>• 导入：将数据库文件导入到设备"
        
        info_label.setText(info_text)
        layout.addWidget(info_label)
    
    def on_refresh_clicked(self):
        """刷新设备按钮点击事件"""
        # 先将刷新按钮变为绿色（选中状态）
        self.refresh_btn.setStyleSheet(self.ui_styles.get_button_style(True))
        
        # 重置操作按钮颜色为蓝色
        self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        
        # 执行刷新操作
        self.refresh_device_list()
        
        # 使用定时器在1秒后将按钮恢复为蓝色（未选中状态）
        QTimer.singleShot(1000, lambda: self.refresh_btn.setStyleSheet(self.ui_styles.get_button_style(False)))
    
    def clear_status_messages(self):
        """清除状态显示区域的所有消息"""
        # 将清除记录按钮变为绿色（选中状态）并保持
        self.clear_log_btn.setStyleSheet(self.ui_styles.get_button_style(True))
        
        # 重置操作按钮颜色为蓝色
        self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        
        # 完全清空状态文本
        self.status_text.setPlainText("")
        
        # 设置状态显示区域边框为蓝色
        self.status_text.setStyleSheet(self.ui_styles.get_status_text_style(False))
    
    def refresh_device_list(self):
        """刷新设备列表"""
        # 重置清除记录按钮颜色为蓝色
        self.clear_log_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        
        devices = self.device_manager.get_adb_devices()
        
        current_text = self.device_combo.currentText()
        self.device_combo.clear()
        
        if not devices:
            self.device_combo.addItem("未检测到设备")
            self.set_ui_color(False)
            self.add_status_message("未检测到设备")
            return
        
        # 单台设备的情况
        if len(devices) == 1:
            device_id = devices[0]
            self.device_combo.addItem(device_id)
            self.device_combo.setCurrentIndex(0)
            self.set_ui_color(True)
            self.add_status_message(f"单台设备，已自动选择: {device_id}")
        # 多台设备的情况
        else:
            self.device_combo.addItem("请选择设备...")
            for device in devices:
                self.device_combo.addItem(device)
            
            # 默认选择"请选择设备..."
            self.device_combo.setCurrentIndex(0)
            self.set_ui_color(False)
            self.add_status_message(f"多台设备，需要用户选择: {', '.join(devices)}")
    
    def on_device_changed(self, device_text):
        """设备选择变化时的处理"""
        devices = self.device_manager.get_adb_devices()
        
        if not device_text or device_text == "未检测到设备" or device_text == "请选择设备...":
            self.set_ui_color(False)
        else:
            self.set_ui_color(True)
        
        if device_text and device_text != "未检测到设备" and device_text != "请选择设备...":
            self.add_status_message(f"设备已切换至: {device_text}")
    
    def set_ui_color(self, is_selected):
        """设置UI元素的颜色（设备选择框）"""
        self.device_combo.setStyleSheet(self.ui_styles.get_combo_style(is_selected))
        # 刷新按钮不需要根据设备选择状态改变颜色，保持当前状态
    
    def show_adb_error(self, message):
        """显示ADB错误消息"""
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setWindowTitle("ADB环境错误")
        error_msg.setText(message)
        error_msg.setInformativeText("请确保已安装Android SDK并配置ADB环境变量")
        error_msg.exec()
        
        # 更新界面显示
        self.device_combo.clear()
        self.device_combo.addItem("ADB环境异常")
        self.set_ui_color(False)
        self.add_status_message("ADB环境异常: " + message)
    
    def start_import(self):
        """开始导入功能"""
        # 重置所有普通按钮颜色为蓝色
        self.refresh_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        self.clear_log_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        
        # 设置导入按钮为绿色（表示正在执行），导出按钮为蓝色
        self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(True))
        self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        
        device = self.get_selected_device()
        
        # 验证设备
        if not device:
            self.add_status_message("错误: 请选择设备")
            # 验证失败，将导入按钮恢复为蓝色
            self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
            return
        
        # 验证路径
        is_valid, message = self.directory_manager.validate_path_for_import()
        if not is_valid:
            self.add_status_message(f"错误: {message}")
            # 验证失败，将导入按钮恢复为蓝色
            self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
            return
        
        path = self.directory_manager.get_selected_path()
        
        # 验证文件是否存在
        if not os.path.isfile(path):
            self.add_status_message(f"错误: 文件不存在: {path}")
            # 验证失败，将导入按钮恢复为蓝色
            self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
            return
        
        # 添加导入开始消息
        self.add_status_message(f"开始导入: 设备={device}, 文件={path}")
        
        # 执行导入操作
        success, result_message = self.operation_handler.perform_import(device, path)
        if success:
            self.add_status_message(f"导入成功: {result_message}")
            # 导入成功后保持导入按钮为绿色
            self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(True))
        else:
            self.add_status_message(f"导入失败: {result_message}")
            # 导入失败，将导入按钮恢复为蓝色
            self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
    
    def start_export(self):
        """开始导出功能"""
        # 重置所有普通按钮颜色为蓝色
        self.refresh_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        self.clear_log_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        
        # 设置导出按钮为绿色（表示正在执行），导入按钮为蓝色
        self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(True))
        self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        
        device = self.get_selected_device()
        
        # 验证设备
        if not device:
            self.add_status_message("错误: 请选择设备")
            # 验证失败，将导出按钮恢复为蓝色
            self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
            return
        
        # 验证路径
        is_valid, message = self.directory_manager.validate_path_for_export()
        if not is_valid:
            self.add_status_message(f"错误: {message}")
            # 验证失败，将导出按钮恢复为蓝色
            self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
            return
        
        path = self.directory_manager.get_selected_path()
        
        # 添加导出开始消息
        self.add_status_message(f"开始导出: 设备={device}, 目录={path}")
        
        # 执行导出操作
        success, result_message = self.operation_handler.perform_export(device, path)
        if success:
            self.add_status_message(f"导出成功: {result_message}")
            # 导出成功后保持导出按钮为绿色
            self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(True))
        else:
            self.add_status_message(f"导出失败: {result_message}")
            # 导出失败，将导出按钮恢复为蓝色
            self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
    
    def get_selected_device(self):
        """获取当前选择的设备"""
        current_text = self.device_combo.currentText()
        if (current_text and 
            current_text != "未检测到设备" and 
            current_text != "请选择设备..." and 
            current_text != "ADB环境异常"):
            return current_text
        return None
    
    def add_status_message(self, message):
        """添加状态消息到状态显示区域"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # 将新消息添加到文本框
        current_text = self.status_text.toPlainText()
        if current_text == "操作日志将显示在这里...\n\n":
            current_text = formatted_message
        else:
            current_text += f"\n{formatted_message}"
        
        self.status_text.setPlainText(current_text)
        
        # 设置状态显示区域边框为绿色（表示有信息输出）
        self.status_text.setStyleSheet(self.ui_styles.get_status_text_style(True))
        
        # 滚动到底部
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.status_text.setTextCursor(cursor)