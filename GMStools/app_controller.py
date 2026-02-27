import sys
import os
import ctypes
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
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

# def main():
#     controller = AppController()
#     controller.initialize_application()
#     controller.create_main_window()
#     controller.run_application()
def main():
    try:
        # ---------- 原有的启动代码 ----------
        controller = AppController()
        controller.initialize_application()
        controller.create_main_window()
        controller.run_application()
        # ----------------------------------
    except Exception as e:
        # 1. 将异常堆栈写入 crash.log 文件
        with open("crash.log", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        
        # 2. 尝试弹出错误对话框（即使 QApplication 未创建也能工作）
        #    如果 QApplication 已存在则复用，否则新建一个临时实例
        app = QApplication.instance()
        if app is None:
            app = QApplication([])  # 临时创建
        QMessageBox.critical(
            None,
            "GMStools 启动失败",
            f"程序启动时发生未捕获的异常，已保存错误信息到 crash.log 文件。\n\n"
            f"错误类型：{type(e).__name__}\n"
            f"错误信息：{str(e)}\n\n"
            f"请将 crash.log 文件发送给开发者。"
        )
        sys.exit(1)  # 终止程序
if __name__ == "__main__":
    main()