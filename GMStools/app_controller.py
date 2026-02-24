import sys
import os
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QSharedMemory, QSettings
from window_manager import WindowManager
from usekey import verify_disclaimer_accepted  # 修改为 usekey

class AppController:
    def __init__(self):
        self.app = None
        self.window = None
        self.shared_memory = None

    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

    def get_app_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def initialize_application(self):
        self.app = QApplication(sys.argv)

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('gmstools.app.1')
        except:
            pass

        icon_path = self.resource_path('app.ico')
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file not found at {icon_path}")

        font = QFont("Microsoft YaHei", 14)
        self.app.setFont(font)

        # 单实例检查
        self.shared_memory = QSharedMemory("GMStools_SingleInstance")
        if self.shared_memory.attach():
            print("程序已在运行，退出当前实例")
            sys.exit(0)
        else:
            if not self.shared_memory.create(1):
                print("警告：无法创建共享内存，多实例可能不受限制")
            else:
                print("第一个实例已创建共享内存")

        return self.app

    def create_main_window(self):
        app_dir = self.get_app_dir()
        config_path = os.path.join(app_dir, "config.ini")
        settings = QSettings(config_path, QSettings.Format.IniFormat)

        # 读取带签名的字符串
        signed_value = settings.value("disclaimer_accepted", "", type=str)
        if signed_value and verify_disclaimer_accepted(signed_value):
            disclaimer_accepted = True
        else:
            disclaimer_accepted = False

        self.window = WindowManager(disclaimer_already_accepted=disclaimer_accepted, config_path=config_path)
        return self.window

    def run_application(self):
        if self.window:
            self.window.show()
            sys.exit(self.app.exec())

def main():
    controller = AppController()
    controller.initialize_application()
    controller.create_main_window()
    controller.run_application()

if __name__ == "__main__":
    main()