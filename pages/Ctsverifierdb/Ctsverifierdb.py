from .main_window import MainWindow

class Ctsverifierdb(MainWindow):
    """CTS Verifier DB 工具 - 主入口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CTS Verifier DB Tool")
        self.resize(600, 500)