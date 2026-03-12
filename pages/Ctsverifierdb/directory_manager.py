from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QFileDialog
import os

from .ui_styles import UIStyles

class DirectoryManager:
    """目录管理类"""
    
    def __init__(self, main_window=None):
        self.selected_path = ""                # 当前选择的路径
        self.directory_line = None
        self.select_file_btn = None
        self.select_directory_btn = None
        self.ui_styles = UIStyles()
        self.main_window = main_window          # 主窗口引用，用于输出日志
        self.current_selection_type = None      # 当前类型：'file' 或 'directory'
        self.last_logged_path = None             # 上次输出的路径（去重用）

    def setup_directory_ui(self, layout):
        """设置路径选择UI"""
        directory_layout = QHBoxLayout()
        directory_layout.setSpacing(6)

        # 路径输入框（允许手动输入）
        self.directory_line = QLineEdit()
        self.directory_line.setFixedHeight(36)
        self.directory_line.setPlaceholderText("请选择数据库文件或目录...")
        self.directory_line.setReadOnly(False)
        self.directory_line.setStyleSheet(self.ui_styles.get_line_edit_style(False))

        # 仅连接编辑完成信号
        self.directory_line.editingFinished.connect(self.on_editing_finished)

        # 选择文件按钮
        self.select_file_btn = QPushButton("选择文件")
        self.select_file_btn.setFixedSize(140, 36)
        self.select_file_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        self.select_file_btn.clicked.connect(self.select_file)

        # 选择目录按钮
        self.select_directory_btn = QPushButton("选择目录")
        self.select_directory_btn.setFixedSize(140, 36)
        self.select_directory_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        self.select_directory_btn.clicked.connect(self.select_directory)

        directory_layout.addWidget(self.directory_line)
        directory_layout.addWidget(self.select_file_btn)
        directory_layout.addWidget(self.select_directory_btn)
        layout.addLayout(directory_layout)

    def on_editing_finished(self):
        """编辑完成（回车或失去焦点）时更新颜色并输出日志（去重）"""
        path = self.directory_line.text().strip()
        self._update_path_type_and_color(path)

        # 仅当路径与上次输出不同时，才输出日志
        if path != self.last_logged_path and self.main_window:
            if self.current_selection_type == 'file':
                self.main_window.add_status_message(f"已识别文件: {path}")
            elif self.current_selection_type == 'directory':
                self.main_window.add_status_message(f"已识别目录: {path}")
            else:
                self.main_window.add_status_message(f"路径无效或不存在: {path}")
            self.last_logged_path = path

    def _update_path_type_and_color(self, path):
        """根据路径更新内部状态和按钮颜色"""
        if not path:
            self.selected_path = ""
            self.current_selection_type = None
            self.set_directory_ui_color()
            return

        exists = os.path.exists(path)
        if exists:
            self.selected_path = path
            if os.path.isfile(path):
                self.current_selection_type = 'file'
            elif os.path.isdir(path):
                self.current_selection_type = 'directory'
            else:
                self.current_selection_type = None
        else:
            self.selected_path = path
            self.current_selection_type = None

        self.set_directory_ui_color()

    def select_file(self):
        """通过按钮选择文件（立即输出日志）"""
        file_path, _ = QFileDialog.getOpenFileName(
            None, "选择数据库文件", os.path.expanduser("~"),
            "数据库文件 (*.db);;所有文件 (*)"
        )
        if file_path:
            self._set_path(file_path, 'file', f"已选择文件: {file_path}")

    def select_directory(self):
        """通过按钮选择目录（立即输出日志）"""
        directory = QFileDialog.getExistingDirectory(
            None, "选择导出目录", os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if directory:
            self._set_path(directory, 'directory', f"已选择目录: {directory}")

    def _set_path(self, path, path_type, log_message):
        """统一设置路径、更新UI、输出日志（用于按钮选择）"""
        self.selected_path = path
        self.directory_line.setText(path)
        self.current_selection_type = path_type
        self.set_directory_ui_color()
        if self.main_window:
            self.main_window.add_status_message(log_message)
        self.last_logged_path = path   # 记录，避免手动编辑后重复输出

    def set_directory_ui_color(self):
        """根据当前类型设置按钮颜色"""
        self.directory_line.setStyleSheet(self.ui_styles.get_line_edit_style(True))
        if self.current_selection_type == 'file':
            self.select_file_btn.setStyleSheet(self.ui_styles.get_button_style(True))
            self.select_directory_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        elif self.current_selection_type == 'directory':
            self.select_file_btn.setStyleSheet(self.ui_styles.get_button_style(False))
            self.select_directory_btn.setStyleSheet(self.ui_styles.get_button_style(True))
        else:
            self.select_file_btn.setStyleSheet(self.ui_styles.get_button_style(False))
            self.select_directory_btn.setStyleSheet(self.ui_styles.get_button_style(False))

    def get_selected_path(self):
        return self.selected_path

    def validate_path_for_import(self):
        if not self.selected_path:
            return False, "请选择路径"
        if not os.path.isfile(self.selected_path):
            return False, "选择的路径不是文件"
        if not self.selected_path.lower().endswith('.db'):
            return False, "导入操作需要选择.db文件"
        return True, "路径有效"

    def validate_path_for_export(self):
        if not self.selected_path:
            return False, "请选择路径"
        if not os.path.isdir(self.selected_path):
            return False, "导出操作需要选择目录"
        return True, "路径有效"