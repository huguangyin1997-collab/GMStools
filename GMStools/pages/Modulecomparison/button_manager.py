class ButtonManager:
    """按钮状态管理器"""
    
    def __init__(self):
        self.button_states = {
            'select_old_file': False,
            'select_new_file': False,
            'start_compare': False,
            'clear_log': False
        }
    
    def toggle_button_state(self, button_type):
        """切换按钮状态"""
        self.button_states[button_type] = not self.button_states[button_type]
        return self.button_states[button_type]
    
    def get_button_state(self, button_type):
        """获取按钮状态"""
        return self.button_states.get(button_type, False)
    
    def get_file_button_style(self, is_selected=False):
        """获取文件选择按钮样式"""
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