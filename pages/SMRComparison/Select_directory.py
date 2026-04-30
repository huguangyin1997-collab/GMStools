from PyQt6.QtWidgets import QFileDialog

def Select_directory(title, parent_widget):
    """
    打开目录选择对话框
    
    Args:
        title: 对话框标题
        parent_widget: 父窗口部件
        
    Returns:
        str: 选择的目录路径，如果用户取消则为空
    """
    # 打开目录选择对话框
    directory = QFileDialog.getExistingDirectory(
        parent_widget,
        title,
        "",  # 起始目录为空，使用系统默认
        QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
    )
    
    return directory if directory else None