import os
import re
import datetime
import traceback
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
                            QPushButton, QLineEdit, QTextEdit, QProgressBar,
                            QFrame, QFileDialog, QMessageBox, QMenu)
from PyQt6.QtGui import QFont, QAction, QPainter, QColor
from PyQt6.QtCore import Qt, QPoint


# ============================ 自定义下拉框 ============================

class CustomComboBox(QPushButton):
    """自定义下拉选择器 - 使用单个按钮实现，包含三角形指示器"""
    
    currentTextChanged = pyqtSignal(str)
    
    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self.items = items or []
        self.current_text = ""
        self.is_selected = False
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setFixedHeight(36)
        self.setStyleSheet("""
            CustomComboBox {
                background-color: #3498db;
                color: white;
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 6px 35px 6px 12px;
                font-size: 14px;
                text-align: left;
            }
            CustomComboBox:hover {
                background-color: #3498db;
                color: red;
                border: 2px solid #3498db;
            }
            CustomComboBox:pressed {
                background-color: #2980b9;
                color: red;
                border: 2px solid #2980b9;
            }
        """)
        
        self.setText("选择ARM架构")
        self.setFont(QFont("Arial", 10))
        
        # 创建下拉菜单
        self.menu = QMenu(self)
        self.menu.setStyleSheet("""
            QMenu {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e0f7fa, stop:0.5 #b2ebf2, stop:1 #80deea);
                border: 2px solid #4dd0e1;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                background-color: rgba(52, 152, 219, 0.8);
                color: white;
                padding: 8px 12px;
                border-radius: 3px;
                font-size: 14px;
                margin: 2px;
            }
            QMenu::item:hover {
                background-color: rgba(52, 152, 219, 0.9);
                color: red;
            }
            QMenu::item:pressed {
                background-color: rgba(41, 128, 185, 0.9);
                color: red;
            }
            QMenu::item:selected {
                background-color: rgba(39, 174, 96, 0.9);
                color: white;
                font-weight: bold;
            }
        """)
        
        # 添加菜单项
        for item in self.items:
            action = QAction(item, self)
            action.triggered.connect(lambda checked, text=item: self.on_item_selected(text))
            self.menu.addAction(action)
        
        self.clicked.connect(self.show_menu)
    
    def show_menu(self):
        """显示下拉菜单"""
        self.menu.exec(self.mapToGlobal(self.rect().bottomLeft()))
    
    def on_item_selected(self, text):
        """处理菜单项选择"""
        self.current_text = text
        self.is_selected = True
        
        bold_font = QFont("Arial", 10)
        bold_font.setBold(True)
        self.setFont(bold_font)
        
        self.setText(text)
        self.currentTextChanged.emit(text)
        
        self.setStyleSheet("""
            CustomComboBox {
                background-color: #27ae60;
                color: white;
                border: 2px solid #27ae60;
                border-radius: 5px;
                padding: 6px 35px 6px 12px;
                font-size: 14px;
                text-align: left;
                font-weight: bold;
            }
            CustomComboBox:hover {
                background-color: #27ae60;
                color: red;
                border: 2px solid #27ae60;
            }
            CustomComboBox:pressed {
                background-color: #27ae60;
                color: red;
                border: 2px solid #27ae60;
            }
        """)
    
    def currentText(self):
        """获取当前文本"""
        return self.current_text
    
    def setCurrentText(self, text):
        """设置当前文本"""
        self.current_text = text
        self.is_selected = True
        
        bold_font = QFont("Arial", 10)
        bold_font.setBold(True)
        self.setFont(bold_font)
        
        self.setText(text)
        
        self.setStyleSheet("""
            CustomComboBox {
                background-color: #27ae60;
                color: white;
                border: 2px solid #27ae60;
                border-radius: 5px;
                padding: 6px 35px 6px 12px;
                font-size: 14px;
                text-align: left;
                font-weight: bold;
            }
            CustomComboBox:hover {
                background-color: #27ae60;
                color: red;
                border: 2px solid #27ae60;
            }
            CustomComboBox:pressed {
                background-color: #27ae60;
                color: red;
                border: 2px solid #27ae60;
            }
        """)
    
    def addItems(self, items):
        """添加项目"""
        for item in items:
            action = QAction(item, self)
            action.triggered.connect(lambda checked, text=item: self.on_item_selected(text))
            self.menu.addAction(action)
        self.items.extend(items)
    
    def paintEvent(self, event):
        """重绘事件，添加自定义三角形指示器"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.underMouse():
            triangle_color = QColor(255, 0, 0)
        elif self.is_selected:
            triangle_color = QColor(255, 255, 255)
        else:
            triangle_color = QColor(255, 255, 255)
            
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(triangle_color)
        
        triangle_size = 6
        right_margin = 12
        center_x = self.width() - right_margin
        center_y = self.height() // 2
        
        points = [
            QPoint(center_x - triangle_size, center_y - triangle_size // 2),
            QPoint(center_x + triangle_size, center_y - triangle_size // 2),
            QPoint(center_x, center_y + triangle_size // 2)
        ]
        
        painter.drawPolygon(points)