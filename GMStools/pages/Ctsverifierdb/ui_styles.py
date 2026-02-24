class UIStyles:
    """UI样式管理类"""
    
    def get_combo_style(self, is_selected=False):
        """获取组合框样式"""
        if is_selected:
            return """
                QComboBox {
                    padding: 8px;
                    font-size: 14px;
                    border: 2px solid #27ae60;
                    border-radius: 4px;
                    background-color: white;
                    color: black;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 1px solid #ccc;
                    padding-left: 5px;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: black;
                    selection-background-color: #27ae60;
                    selection-color: white;
                    border: 1px solid #ccc;
                    outline: none;
                }
                QComboBox QAbstractItemView::item {
                    padding: 5px;
                }
            """
        else:
            return """
                QComboBox {
                    padding: 8px;
                    font-size: 14px;
                    border: 2px solid #3498db;
                    border-radius: 4px;
                    background-color: white;
                    color: black;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 1px solid #ccc;
                    padding-left: 5px;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: black;
                    selection-background-color: #3498db;
                    selection-color: white;
                    border: 1px solid #ccc;
                    outline: none;
                }
                QComboBox QAbstractItemView::item {
                    padding: 5px;
                }
            """
    
    def get_button_style(self, is_selected=False):
        """获取按钮样式"""
        if is_selected:
            return """
                QPushButton {
                    padding: 8px 15px;
                    font-size: 14px;
                    border: 2px solid #27ae60;
                    border-radius: 4px;
                    background-color: #27ae60;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #219653;
                }
                QPushButton:pressed {
                    background-color: #1e8449;
                }
            """
        else:
            return """
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
            """
    
    def get_action_button_style(self, is_selected=False):
        """获取操作按钮样式"""
        if is_selected:
            return """
                QPushButton {
                    padding: 8px 15px;
                    font-size: 16px;
                    font-weight: bold;
                    border: 2px solid #27ae60;
                    border-radius: 6px;
                    background-color: #27ae60;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #219653;
                }
                QPushButton:pressed {
                    background-color: #1e8449;
                }
            """
        else:
            return """
                QPushButton {
                    padding: 8px 15px;
                    font-size: 16px;
                    font-weight: bold;
                    border: 2px solid #3498db;
                    border-radius: 6px;
                    background-color: #3498db;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #2471a3;
                }
            """
    
    def get_line_edit_style(self, is_selected=False):
        """获取行编辑框样式"""
        if is_selected:
            return """
                QLineEdit {
                    padding: 8px;
                    font-size: 14px;
                    border: 2px solid #27ae60;
                    border-radius: 4px;
                    background-color: white;
                    color: black;
                }
            """
        else:
            return """
                QLineEdit {
                    padding: 8px;
                    font-size: 14px;
                    border: 2px solid #3498db;
                    border-radius: 4px;
                    background-color: white;
                    color: black;
                }
            """
    
    def get_status_text_style(self, has_output=False):
        """获取状态文本框样式"""
        if has_output:
            return """
                QTextEdit {
                    background-color: rgba(255, 255, 255, 0.8);
                    border: 2px solid #27ae60;
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 12px;
                    color: #2c3e50;
                    font-family: "Consolas", "Monaco", "Courier New", monospace;
                }
            """
        else:
            return """
                QTextEdit {
                    background-color: rgba(255, 255, 255, 0.8);
                    border: 2px solid #3498db;
                    border-radius: 8px;
                    padding: 12px;
                    font-size: 12px;
                    color: #2c3e50;
                    font-family: "Consolas", "Monaco", "Courier New", monospace;
                }
            """
    
    def get_default_text_style(self):
        """获取默认文本框样式"""
        return """
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.8);
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
                color: #2c3e50;
                font-family: "Consolas", "Monaco", "Courier New", monospace;
            }
        """
    
    def get_import_text_style(self):
        """获取导入状态文本框样式"""
        return """
            QTextEdit {
                background-color: rgba(46, 204, 113, 0.8);
                border: 2px solid #2ecc71;
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
                color: #2c3e50;
                font-family: "Consolas", "Monaco", "Courier New", monospace;
            }
        """
    
    def get_export_text_style(self):
        """获取导出状态文本框样式"""
        return """
            QTextEdit {
                background-color: rgba(241, 196, 15, 0.8);
                border: 2px solid #f1c40f;
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
                color: #2c3e50;
                font-family: "Consolas", "Monaco", "Courier New", monospace;
            }
        """
    
    # 以下方法保留但不使用，以防其他地方引用
    def get_frame_style(self):
        """获取框架样式"""
        return """
            QFrame {
                background-color: rgba(52, 152, 219, 0.2);
                border: 2px solid #3498db;
                border-radius: 8px;
            }
        """
    
    def get_import_frame_style(self):
        """获取导入状态框架样式"""
        return """
            QFrame {
                background-color: rgba(46, 204, 113, 0.3);
                border: 2px solid #2ecc71;
                border-radius: 8px;
            }
        """
    
    def get_export_frame_style(self):
        """获取导出状态框架样式"""
        return """
            QFrame {
                background-color: rgba(241, 196, 15, 0.3);
                border: 2px solid #f1c40f;
                border-radius: 8px;
            }
        """