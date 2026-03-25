from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QHBoxLayout, QPushButton, QMessageBox, QTextEdit, QLabel, QSizePolicy, QFileDialog
from PyQt6.QtCore import Qt, QTimer
import os

from .device_manager import DeviceManager
from .directory_manager import DirectoryManager
from .ui_styles import UIStyles
from .operation_handler import OperationHandler
from .Operationdatabase import DatabaseExporter, DatabaseImporter

class MainWindow(QWidget):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.device_manager = DeviceManager()
        self.ui_styles = UIStyles()
        self.directory_manager = DirectoryManager(self)
        self.operation_handler = OperationHandler(self.device_manager, self.directory_manager)
        self.setup_ui()
        
        QTimer.singleShot(0, self.delayed_adb_check)
    
    def delayed_adb_check(self):
        self.device_manager.check_adb_environment(self.refresh_device_list, self.show_adb_error)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)
        
        self.setup_device_selection(layout)
        self.directory_manager.setup_directory_ui(layout)
        self.setup_action_buttons(layout)
        self.setup_extra_buttons(layout)
        self.setup_status_frame(layout)
        self.setup_info_section(layout)
    
    def setup_device_selection(self, layout):
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
        
        self.clear_log_btn = QPushButton("清除记录")
        self.clear_log_btn.setFixedSize(140, 36)
        self.clear_log_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        self.clear_log_btn.clicked.connect(self.clear_status_messages)
        
        device_layout.addWidget(self.device_combo)
        device_layout.addWidget(self.refresh_btn)
        device_layout.addWidget(self.clear_log_btn)
        layout.addLayout(device_layout)
    
    def setup_action_buttons(self, layout):
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        self.export_btn = QPushButton("开始导出")
        self.export_btn.setFixedHeight(36)
        self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        self.export_btn.clicked.connect(self.start_export)
        
        self.import_btn = QPushButton("开始导入")
        self.import_btn.setFixedHeight(36)
        self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        self.import_btn.clicked.connect(self.start_import)
        
        action_layout.addWidget(self.export_btn)
        action_layout.addWidget(self.import_btn)
        layout.addLayout(action_layout)
    
    def setup_extra_buttons(self, layout):
        extra_layout = QHBoxLayout()
        extra_layout.setSpacing(10)

        self.export_info_btn = QPushButton("导出数据库信息")
        self.export_info_btn.setFixedHeight(36)
        self.export_info_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        self.export_info_btn.clicked.connect(self.on_export_info_clicked)

        self.import_info_btn = QPushButton("导入数据库信息")
        self.import_info_btn.setFixedHeight(36)
        self.import_info_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        self.import_info_btn.clicked.connect(self.on_import_info_clicked)

        extra_layout.addWidget(self.export_info_btn)
        extra_layout.addWidget(self.import_info_btn)
        layout.addLayout(extra_layout)
    
    def setup_status_frame(self, layout):
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet(self.ui_styles.get_status_text_style(False))
        self.status_text.setPlainText("操作日志将显示在这里...\n\n")
        self.status_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.status_text, 1)
    
    def setup_info_section(self, layout):
        info_label = QLabel()
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
                color: #2c3e50;
                line-height: 1;
            }
        """)
        info_label.setText("• 导出：从设备导出CTS Verifier测试数据库<br>• 导入：将数据库文件导入到设备")
        layout.addWidget(info_label)
        
    def on_refresh_clicked(self):
        self.refresh_btn.setStyleSheet(self.ui_styles.get_button_style(True))
        self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        self.refresh_device_list()
        QTimer.singleShot(1000, lambda: self.refresh_btn.setStyleSheet(self.ui_styles.get_button_style(False)))
    
    def clear_status_messages(self):
        self.clear_log_btn.setStyleSheet(self.ui_styles.get_button_style(True))
        self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        self.status_text.setPlainText("")
        self.status_text.setStyleSheet(self.ui_styles.get_status_text_style(False))
    
    def refresh_device_list(self):
        self.clear_log_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        devices = self.device_manager.get_adb_devices()
        
        current_text = self.device_combo.currentText()
        self.device_combo.clear()
        
        if not devices:
            self.device_combo.addItem("未检测到设备")
            self.set_ui_color(False)
            self.add_status_message("未检测到设备")
            return
        
        if len(devices) == 1:
            device_id = devices[0]
            self.device_combo.addItem(device_id)
            self.device_combo.setCurrentIndex(0)
            self.set_ui_color(True)
            self.add_status_message(f"单台设备，已自动选择: {device_id}")
        else:
            self.device_combo.addItem("请选择设备...")
            for device in devices:
                self.device_combo.addItem(device)
            self.device_combo.setCurrentIndex(0)
            self.set_ui_color(False)
            self.add_status_message(f"多台设备，需要用户选择: {', '.join(devices)}")
    
    def on_device_changed(self, device_text):
        if not device_text or device_text in ("未检测到设备", "请选择设备..."):
            self.set_ui_color(False)
        else:
            self.set_ui_color(True)
            self.add_status_message(f"设备已切换至: {device_text}")
    
    def set_ui_color(self, is_selected):
        self.device_combo.setStyleSheet(self.ui_styles.get_combo_style(is_selected))
    
    def show_adb_error(self, message):
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Icon.Critical)
        error_msg.setWindowTitle("ADB环境错误")
        error_msg.setText(message)
        error_msg.setInformativeText("请确保已安装Android SDK并配置ADB环境变量")
        error_msg.exec()
        
        self.device_combo.clear()
        self.device_combo.addItem("ADB环境异常")
        self.set_ui_color(False)
        self.add_status_message("ADB环境异常: " + message)
    
    def start_import(self):
        self.refresh_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        self.clear_log_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(True))
        self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        
        device = self.get_selected_device()
        if not device:
            self.add_status_message("错误: 请选择设备")
            self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
            return
        
        is_valid, message = self.directory_manager.validate_path_for_import()
        if not is_valid:
            self.add_status_message(f"错误: {message}")
            self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
            return
        
        path = self.directory_manager.get_selected_path()
        if not os.path.isfile(path):
            self.add_status_message(f"错误: 文件不存在: {path}")
            self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
            return
        
        self.add_status_message(f"开始导入: 设备={device}, 文件={path}")
        success, result_message = self.operation_handler.perform_import(device, path)
        if success:
            self.add_status_message(f"导入成功: {result_message}")
            self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(True))
        else:
            self.add_status_message(f"导入失败: {result_message}")
            self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
    
    def start_export(self):
        self.refresh_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        self.clear_log_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(True))
        self.import_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
        
        device = self.get_selected_device()
        if not device:
            self.add_status_message("错误: 请选择设备")
            self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
            return
        
        is_valid, message = self.directory_manager.validate_path_for_export()
        if not is_valid:
            self.add_status_message(f"错误: {message}")
            self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
            return
        
        path = self.directory_manager.get_selected_path()
        self.add_status_message(f"开始导出: 设备={device}, 目录={path}")
        success, result_message = self.operation_handler.perform_export(device, path)
        if success:
            self.add_status_message(f"导出成功: {result_message}")
            self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(True))
        else:
            self.add_status_message(f"导出失败: {result_message}")
            self.export_btn.setStyleSheet(self.ui_styles.get_action_button_style(False))
    
    def get_selected_device(self):
        current_text = self.device_combo.currentText()
        if current_text and current_text not in ("未检测到设备", "请选择设备...", "ADB环境异常"):
            return current_text
        return None
    
    def add_status_message(self, message):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        current_text = self.status_text.toPlainText()
        if current_text == "操作日志将显示在这里...\n\n":
            current_text = formatted_message
        else:
            current_text += f"\n{formatted_message}"
        
        self.status_text.setPlainText(current_text)
        self.status_text.setStyleSheet(self.ui_styles.get_status_text_style(True))
        
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.status_text.setTextCursor(cursor)
    
    # ========== 额外按钮功能（纯本地操作） ==========
    def on_export_info_clicked(self):
        """导出数据库信息：从本地 .db 文件导出 db_new.xls（覆盖，不备份）"""
        self.export_info_btn.setStyleSheet(self.ui_styles.get_action_button_style(True))
        try:
            path = self.directory_manager.get_selected_path()
            if not path:
                self.add_status_message("导出数据库信息失败: 未选择文件")
                return
            if not os.path.isfile(path):
                self.add_status_message(f"导出数据库信息失败: 文件不存在: {path}")
                return
            if not path.lower().endswith('.db'):
                self.add_status_message("导出数据库信息失败: 请选择 .db 数据库文件")
                return

            base_dir = os.path.dirname(path)
            new_excel = os.path.join(base_dir, "db_new.xls")

            # 如果已存在，直接删除
            if os.path.isfile(new_excel):
                os.remove(new_excel)
                self.add_status_message("已删除旧的 db_new.xls")

            self.add_status_message(f"开始导出数据库信息: {path} → {new_excel}")
            success, msg, out_file = DatabaseExporter.export_results_to_excel(path)
            if success:
                self.add_status_message(f"导出成功: {msg}")
            else:
                self.add_status_message(f"导出失败: {msg}")
        finally:
            QTimer.singleShot(1000, lambda: self.export_info_btn.setStyleSheet(
                self.ui_styles.get_action_button_style(False)))
    def on_import_info_clicked(self):
        """导入数据库信息：自动使用 db_new.xlsx 对比更新数据库（无弹框）"""
        self.import_info_btn.setStyleSheet(self.ui_styles.get_action_button_style(True))
        try:
            db_path = self.directory_manager.get_selected_path()
            if not db_path:
                self.add_status_message("导入数据库信息失败: 未选择数据库文件")
                return
            if not os.path.isfile(db_path):
                self.add_status_message(f"导入数据库信息失败: 数据库文件不存在: {db_path}")
                return
            if not db_path.lower().endswith('.db'):
                self.add_status_message("导入数据库信息失败: 请选择 .db 数据库文件")
                return

            base_dir = os.path.dirname(db_path)
            new_excel = os.path.join(base_dir, "db_new.xlsx")
            if not os.path.isfile(new_excel):
                self.add_status_message("导入数据库信息失败: 未找到 db_new.xlsx 文件")
                return

            old_excel = os.path.join(base_dir, "db_old.xlsx")
            if os.path.isfile(old_excel):
                os.remove(old_excel)
                self.add_status_message("已删除旧的 db_old.xlsx")

            self.add_status_message(f"正在导出当前数据库内容到 {old_excel}...")
            success, msg, out_file = DatabaseExporter.export_results_to_excel(db_path, output_filename="db_old.xlsx")
            if not success:
                self.add_status_message(f"导出旧数据失败: {msg}")
                return
            self.add_status_message(f"已导出旧数据: {msg}")

            self.add_status_message(f"开始对比更新: {new_excel} vs {old_excel} → {db_path}")
            success, msg = DatabaseImporter.compare_and_update(new_excel, old_excel, db_path)
            if success:
                self.add_status_message(f"更新成功: {msg}")
            else:
                self.add_status_message(f"更新失败: {msg}")
        finally:
            QTimer.singleShot(1000, lambda: self.import_info_btn.setStyleSheet(
                self.ui_styles.get_action_button_style(False)))
    def closeEvent(self, event):
        print("窗口关闭，程序退出")