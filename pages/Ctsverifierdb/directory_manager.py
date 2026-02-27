from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
import os

from .ui_styles import UIStyles

class DirectoryManager:
    """目录管理类"""
    
    def __init__(self, main_window=None):
        self.selected_path = ""  # 存储选择的路径
        self.directory_line = None
        self.select_file_btn = None
        self.select_directory_btn = None
        self.ui_styles = UIStyles()
        self.main_window = main_window  # 保存主窗口引用
        self.current_selection_type = None  # 记录当前选择的类型：'file' 或 'directory'
    
    def setup_directory_ui(self, layout):
        """设置路径选择UI"""
        # 路径选择区域 - 水平布局
        directory_layout = QHBoxLayout()
        directory_layout.setSpacing(6)
        
        # 路径显示框
        self.directory_line = QLineEdit()
        self.directory_line.setFixedHeight(36)
        self.directory_line.setPlaceholderText("请选择数据库文件或目录...")
        self.directory_line.setReadOnly(True)  # 设置为只读，只能通过选择按钮修改
        self.directory_line.setStyleSheet(self.ui_styles.get_line_edit_style(False))
        
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
    
    def select_file(self):
        """选择.db文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "选择数据库文件",
            os.path.expanduser("~"),
            "数据库文件 (*.db);;所有文件 (*)"
        )
        
        if file_path:
            self.selected_path = file_path
            self.directory_line.setText(file_path)
            self.current_selection_type = 'file'
            self.set_directory_ui_color()
            if self.main_window:
                self.main_window.add_status_message(f"已选择文件: {file_path}")
    
    def select_directory(self):
        """选择目录"""
        directory = QFileDialog.getExistingDirectory(
            None,
            "选择导出目录",
            os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if directory:
            self.selected_path = directory
            self.directory_line.setText(directory)
            self.current_selection_type = 'directory'
            self.set_directory_ui_color()
            if self.main_window:
                self.main_window.add_status_message(f"已选择目录: {directory}")
    
    def set_directory_ui_color(self):
        """设置路径选择UI元素的颜色"""
        # 设置路径显示框的颜色
        self.directory_line.setStyleSheet(self.ui_styles.get_line_edit_style(True))
        
        # 根据当前选择的类型设置按钮颜色
        if self.current_selection_type == 'file':
            self.select_file_btn.setStyleSheet(self.ui_styles.get_button_style(True))
            self.select_directory_btn.setStyleSheet(self.ui_styles.get_button_style(False))
        elif self.current_selection_type == 'directory':
            self.select_file_btn.setStyleSheet(self.ui_styles.get_button_style(False))
            self.select_directory_btn.setStyleSheet(self.ui_styles.get_button_style(True))
        else:
            # 没有选择时，两个按钮都使用未选中样式
            self.select_file_btn.setStyleSheet(self.ui_styles.get_button_style(False))
            self.select_directory_btn.setStyleSheet(self.ui_styles.get_button_style(False))
    
    def get_selected_path(self):
        """获取当前选择的路径（供外部调用）"""
        return self.selected_path
    
    def validate_path_for_import(self):
        """验证路径是否适合导入操作（必须是.db文件）"""
        if not self.selected_path:
            return False, "请选择路径"
        
        if not os.path.isfile(self.selected_path):
            return False, "选择的路径不是文件"
        
        if not self.selected_path.lower().endswith('.db'):
            return False, "导入操作需要选择.db文件"
        
        return True, "路径有效"
    
    def validate_path_for_export(self):
        """验证路径是否适合导出操作（必须是目录）"""
        if not self.selected_path:
            return False, "请选择路径"
        
        if not os.path.isdir(self.selected_path):
            return False, "导出操作需要选择目录"
        
        return True, "路径有效"