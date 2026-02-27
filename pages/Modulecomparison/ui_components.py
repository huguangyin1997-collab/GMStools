from PyQt6.QtWidgets import (QComboBox, QPushButton, QTextEdit, QHBoxLayout, 
                             QVBoxLayout, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt

def create_file_selection_combo(placeholder_text):
    """创建文件选择下拉框"""
    combo = QComboBox()
    combo.setEditable(True)  # 设置为可编辑，以便显示占位文本
    combo.lineEdit().setPlaceholderText(placeholder_text)
    combo.setFixedHeight(36)
    combo.setStyleSheet(get_combo_box_style(False))  # 初始状态为未选择
    return combo

def create_file_selection_button(text, width=140, height=36):
    """创建文件选择按钮（使用新样式）"""
    button = QPushButton(text)
    button.setFixedSize(width, height)
    button.setStyleSheet("""
        QPushButton {
            padding: 8px 15px;
            font-size: 14px;
            border: 2px solid #3498db;
            border-radius: 4px;
            background-color: #3498db;
            color: white;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #2471a3;
        }
    """)
    return button

def create_action_button(text):
    """创建操作按钮（初始为蓝色背景）"""
    button = QPushButton(text)
    button.setFixedHeight(36)  # 只设置高度，宽度由布局控制
    button.setStyleSheet("""
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
    return button

def create_display_textedit(placeholder_text):
    """创建显示文本区域"""
    text_edit = QTextEdit()
    text_edit.setPlaceholderText(placeholder_text)
    text_edit.setStyleSheet(get_text_edit_style(False))  # 初始状态为无内容
    return text_edit

def create_command_textedit(placeholder_text):
    """创建命令显示文本区域"""
    text_edit = QTextEdit()
    text_edit.setPlaceholderText(placeholder_text)
    text_edit.setStyleSheet(get_text_edit_style(False))  # 初始状态为无内容
    return text_edit

def get_combo_box_style(is_selected=False):
    """获取文件选择框样式"""
    if is_selected:
        return """
            QComboBox {
                background-color: white;
                border: 2px solid #27ae60;
                border-radius: 4px;
                padding: 5px;
                min-width: 200px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 1px solid #27ae60;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #3498db;
                selection-background-color: #3498db;
                font-size: 14px;
            }
        """
    else:
        return """
            QComboBox {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 4px;
                padding: 5px;
                min-width: 200px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 1px solid #3498db;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #3498db;
                selection-background-color: #3498db;
                font-size: 14px;
            }
        """

def get_text_edit_style(has_content=False):
    """获取文本编辑框样式"""
    if has_content:
        return """
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.6);
                border: 2px solid #27ae60;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
        """
    else:
        return """
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.6);
                border: 2px solid #3498db;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
        """
