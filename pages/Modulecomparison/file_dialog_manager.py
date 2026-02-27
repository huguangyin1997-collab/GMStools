from PyQt6.QtWidgets import QFileDialog, QMessageBox

class FileDialogManager:
    """文件对话框管理器"""
    
    def __init__(self, parent_widget):
        self.parent = parent_widget
    
    def open_file_dialog(self, combo_box, dialog_title):
        """打开文件选择对话框，返回是否成功选择了文件"""
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(
                self.parent,
                dialog_title,
                "",
                "All Files (*);;Text Files (*.txt);;Python Files (*.py);;HTML Files (*.html *.htm);;XML Files (*.xml)"
            )
            
            if file_path:
                combo_box.clear()
                combo_box.addItem(file_path)
                combo_box.setCurrentText(file_path)
                # 设置选中后的文本样式
                combo_box.setStyleSheet("""
                    QComboBox {
                        background-color: white;
                        border: 2px solid #27ae60;
                        border-radius: 4px;
                        padding: 5px;
                        min-width: 200px;
                        font-size: 12px;
                        color: #333333;
                    }
                    QComboBox::drop-down {
                        border: none;
                    }
                    QComboBox::down-arrow {
                        image: none;
                        border-left: 1px solid #27ae60;
                        width: 20px;
                    }
                """)
                return True  # 成功选择了文件
            else:
                return False  # 用户取消了选择
                
        except Exception as e:
            QMessageBox.critical(self.parent, "错误", f"选择文件时出错: {str(e)}")
            return False  # 选择文件时出错