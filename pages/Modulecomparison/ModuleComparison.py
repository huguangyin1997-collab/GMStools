from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
import os

# 导入各个模块
from .ui_components import (create_file_selection_combo, create_file_selection_button, 
                           create_action_button, create_display_textedit, 
                           create_command_textedit, get_combo_box_style, get_text_edit_style)
from .button_manager import ButtonManager
from .file_dialog_manager import FileDialogManager
from .comparison_engine import ComparisonEngine

class Modulecomparison(QWidget):
    """对比模块页面"""
    
    def __init__(self):
        super().__init__()
        self.button_manager = ButtonManager()
        self.file_dialog_manager = FileDialogManager(self)
        self.comparison_engine = ComparisonEngine()
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # 创建UI组件
        self.create_file_selection_ui(layout)
        self.create_action_buttons_ui(layout)
        self.create_display_areas_ui(layout)
        self.create_command_areas_ui(layout)
        
        # 连接按钮事件
        self.connect_button_events()
        
        # 初始状态更新 - 两个按钮都设为蓝色
        self.set_initial_button_styles()
    
    def create_file_selection_ui(self, layout):
        """创建文件选择UI"""
        # 旧文件选择
        old_file_layout = QHBoxLayout()
        self.old_file_combo_box = create_file_selection_combo("选择旧文件/目前支持xml,html,txt格式")
        self.select_old_file_btn = create_file_selection_button("选择旧文件")
        old_file_layout.addWidget(self.old_file_combo_box, 1)
        old_file_layout.addWidget(self.select_old_file_btn)
        layout.addLayout(old_file_layout)
        
        # 新文件选择
        new_file_layout = QHBoxLayout()
        self.new_file_combo_box = create_file_selection_combo("选择新文件/目前支持xml,html,txt格式")
        self.select_new_file_btn = create_file_selection_button("选择新文件")
        new_file_layout.addWidget(self.new_file_combo_box, 1)
        new_file_layout.addWidget(self.select_new_file_btn)
        layout.addLayout(new_file_layout)
    
    def create_action_buttons_ui(self, layout):
        """创建操作按钮UI - 各占一半宽度，高度36"""
        action_layout = QHBoxLayout()
        self.start_compare_btn = create_action_button("开始对比")
        self.clear_log_btn = create_action_button("清除记录")
        action_layout.addWidget(self.start_compare_btn, 1)  # 拉伸因子为1，占一半宽度
        action_layout.addWidget(self.clear_log_btn, 1)      # 拉伸因子为1，占一半宽度
        layout.addLayout(action_layout)
    
    def create_display_areas_ui(self, layout):
        """创建显示区域UI"""
        display_layout = QHBoxLayout()
        self.left_display = create_display_textedit("旧文件独有模块将显示在这里")
        self.right_display = create_display_textedit("新文件独有模块将显示在这里")
        display_layout.addWidget(self.left_display, 1)
        display_layout.addWidget(self.right_display, 1)
        layout.addLayout(display_layout, 3)
    
    def create_command_areas_ui(self, layout):
        """创建命令区域UI"""
        command_layout = QHBoxLayout()
        
        left_command_layout = QVBoxLayout()
        self.left_import_display = create_command_textedit("旧文件独有的模块引入命令将显示在这里")
        left_command_layout.addWidget(self.left_import_display)
        
        right_command_layout = QVBoxLayout()
        self.right_import_display = create_command_textedit("新文件独有的模块引入命令将显示在这里")
        right_command_layout.addWidget(self.right_import_display)
        
        command_layout.addLayout(left_command_layout, 1)
        command_layout.addLayout(right_command_layout, 1)
        layout.addLayout(command_layout, 2)
    
    def connect_button_events(self):
        """连接按钮事件"""
        self.select_old_file_btn.clicked.connect(
            lambda: self.on_file_select_button_clicked('select_old_file', 
                self.old_file_combo_box, "选择旧文件"))
        
        self.select_new_file_btn.clicked.connect(
            lambda: self.on_file_select_button_clicked('select_new_file', 
                self.new_file_combo_box, "选择新文件"))
        
        # 操作按钮保持原有功能，不改变样式
        self.start_compare_btn.clicked.connect(self.start_comparison)
        self.clear_log_btn.clicked.connect(self.on_clear_log_clicked)
    
    def on_file_select_button_clicked(self, button_type, combo_box, dialog_title):
        """处理文件选择按钮点击事件"""
        # 先执行文件选择
        file_selected = self.file_dialog_manager.open_file_dialog(combo_box, dialog_title)
        
        # 只有成功选择了文件，才更新按钮和文件选择框的样式
        if file_selected:
            # 切换按钮状态
            new_state = self.button_manager.toggle_button_state(button_type)
            
            # 更新按钮样式
            button = self.get_button_by_type(button_type)
            if button:
                button.setStyleSheet(self.button_manager.get_file_button_style(new_state))
            
            # 更新文件选择框样式
            combo_box.setStyleSheet(get_combo_box_style(new_state))
    
    def get_button_by_type(self, button_type):
        """根据按钮类型获取按钮对象"""
        button_map = {
            'select_old_file': self.select_old_file_btn,
            'select_new_file': self.select_new_file_btn,
            'start_compare': self.start_compare_btn,
            'clear_log': self.clear_log_btn
        }
        return button_map.get(button_type)
    
    def start_comparison(self):
        """开始对比"""
        old_file_path = self.old_file_combo_box.currentText()
        new_file_path = self.new_file_combo_box.currentText()
        
        self.set_buttons_enabled(False)
        comparison_result = self.comparison_engine.perform_comparison(old_file_path, new_file_path)
        
        if comparison_result:
            self.update_displays(comparison_result)
        
        self.set_buttons_enabled(True)
    
    def update_displays(self, comparison_result):
        """更新显示区域"""
        if comparison_result.get('is_xml_comparison', False):
            same_modules = comparison_result.get('same_modules', [])
            same_text = self.comparison_engine.format_same_modules_text(same_modules)
            
            # 更新显示内容
            self.left_display.setText("\n".join(comparison_result['old_raw']))
            self.right_display.setText("\n".join(comparison_result['new_raw']))
            self.left_import_display.setText(same_text)
            self.right_import_display.setText(same_text)
            
            # 更新边框颜色状态
            has_old_content = len(comparison_result['old_raw']) > 0
            has_new_content = len(comparison_result['new_raw']) > 0
            has_same_content = len(same_text.strip()) > 0
            
            self.left_display.setStyleSheet(get_text_edit_style(has_old_content))
            self.right_display.setStyleSheet(get_text_edit_style(has_new_content))
            self.left_import_display.setStyleSheet(get_text_edit_style(has_same_content))
            self.right_import_display.setStyleSheet(get_text_edit_style(has_same_content))
        else:
            # 更新显示内容
            self.left_display.setText("\n".join(comparison_result['old_raw']))
            self.right_display.setText("\n".join(comparison_result['new_raw']))
            self.left_import_display.setText(comparison_result['old_command'])
            self.right_import_display.setText(comparison_result['new_command'])
            
            # 更新边框颜色状态
            has_old_display = len(comparison_result['old_raw']) > 0
            has_new_display = len(comparison_result['new_raw']) > 0
            has_old_command = comparison_result['old_command'] != "无"
            has_new_command = comparison_result['new_command'] != "无"
            
            self.left_display.setStyleSheet(get_text_edit_style(has_old_display))
            self.right_display.setStyleSheet(get_text_edit_style(has_new_display))
            self.left_import_display.setStyleSheet(get_text_edit_style(has_old_command))
            self.right_import_display.setStyleSheet(get_text_edit_style(has_new_command))
        
        # 更新按钮样式 - 有内容时
        self.update_buttons_style_has_content()
    
    def set_buttons_enabled(self, enabled):
        """设置按钮启用状态"""
        self.start_compare_btn.setEnabled(enabled)
        self.clear_log_btn.setEnabled(enabled)
        self.select_old_file_btn.setEnabled(enabled)
        self.select_new_file_btn.setEnabled(enabled)
    
    def on_clear_log_clicked(self):
        """清除记录按钮点击事件"""
        self.clear_all_displays()
        # 更新按钮样式 - 无内容时
        self.update_buttons_style_no_content()
    
    def clear_all_displays(self):
        """清除所有显示区域"""
        self.left_display.clear()
        self.right_display.clear()
        self.left_import_display.clear()
        self.right_import_display.clear()
        
        # 重置所有信息框的边框颜色为默认蓝色
        self.left_display.setStyleSheet(get_text_edit_style(False))
        self.right_display.setStyleSheet(get_text_edit_style(False))
        self.left_import_display.setStyleSheet(get_text_edit_style(False))
        self.right_import_display.setStyleSheet(get_text_edit_style(False))
    
    def set_initial_button_styles(self):
        """设置初始按钮样式 - 两个按钮都为蓝色"""
        blue_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """
        self.start_compare_btn.setStyleSheet(blue_style)
        self.clear_log_btn.setStyleSheet(blue_style)
    
    def update_buttons_style_has_content(self):
        """更新按钮样式 - 有内容时"""
        # 开始对比按钮：绿色
        self.start_compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        
        # 清除记录按钮：蓝色
        self.clear_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
    
    def update_buttons_style_no_content(self):
        """更新按钮样式 - 无内容时"""
        # 开始对比按钮：蓝色
        self.start_compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        # 清除记录按钮：绿色
        self.clear_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)