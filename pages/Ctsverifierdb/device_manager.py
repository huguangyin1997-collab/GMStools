import subprocess
import os
import sys
import platform

def _get_subprocess_kwargs():
    """返回用于隐藏 Windows 控制台窗口的参数"""
    kwargs = {}
    if sys.platform == 'win32':
        if hasattr(subprocess, 'CREATE_NO_WINDOW'):
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        else:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = startupinfo
    return kwargs

class DeviceManager:
    """设备管理类 - 优先系统 ADB，其次外部同级 platform-tools，绝不使用打包的 ADB"""

    def __init__(self):
        self.devices = []
        self.adb_path = None
        self.adb_source = None

    def _find_system_adb(self):
        """查找系统ADB路径"""
        try:
            system = platform.system()
            kwargs = _get_subprocess_kwargs()
            if system == "Windows":
                result = subprocess.run(
                    ['where', 'adb'],
                    capture_output=True, text=True, timeout=5,
                    shell=True, **kwargs
                )
            else:
                result = subprocess.run(
                    ['which', 'adb'],
                    capture_output=True, text=True, timeout=5, **kwargs
                )
            if result.returncode == 0:
                paths = result.stdout.strip().split('\n')
                for path in paths:
                    path = path.strip()
                    if os.path.isfile(path):
                        return path
        except Exception as e:
            print(f"查找系统ADB失败: {e}")
        return None

    def _find_adb_path(self):
        """查找ADB路径 - 优先系统ADB，其次外部同级platform-tools"""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(os.path.dirname(base_dir))

        system = platform.system()
        adb_filename = "adb.exe" if system == "Windows" else "adb"

        # 1. 先尝试系统ADB
        system_adb = self._find_system_adb()
        if system_adb:
            self.adb_source = "system"
            print(f"使用系统 ADB: {system_adb}")
            return system_adb

        # 2. 再尝试外部同级 platform-tools
        external_adb = os.path.join(base_dir, "platform-tools", adb_filename)
        if os.path.isfile(external_adb):
            self.adb_source = "external"
            print(f"使用外部 ADB: {external_adb}")
            return external_adb

        raise Exception(
            f"未找到 ADB 工具。请确保：\n"
            f"1. 系统环境变量中包含 adb (如 Android SDK 已安装)\n"
            f"2. 或将 platform-tools 文件夹放在程序同一目录下（包含 {adb_filename}）"
        )

    def check_adb_environment(self, refresh_callback, error_callback):
        try:
            self.adb_path = self._find_adb_path()
            print(f"最终选择的 ADB 路径: {self.adb_path}")
            print(f"ADB 来源: {self.adb_source}")

            kwargs = _get_subprocess_kwargs()
            result = subprocess.run(
                [self.adb_path, 'version'],
                capture_output=True, text=True, timeout=5, **kwargs
            )
            if result.returncode != 0:
                raise Exception(f"ADB验证失败: {result.stderr}")
            if 'Android Debug Bridge' not in result.stdout:
                raise Exception("不是有效的ADB程序")

            print(f"ADB验证成功: {self.adb_path}")
            refresh_callback()
            return True
        except Exception as e:
            error_message = f"ADB环境检查失败: {str(e)}"
            print(f" {error_message}")
            error_callback(error_message)
            return False

    def set_adb_path(self, custom_path):
        raise NotImplementedError("不支持自定义ADB路径")

    def get_adb_devices(self):
        try:
            if not self.adb_path:
                self.adb_path = self._find_adb_path()
            kwargs = _get_subprocess_kwargs()
            result = subprocess.run(
                [self.adb_path, 'devices'],
                capture_output=True, text=True, timeout=10, **kwargs
            )
            if result.returncode != 0:
                raise Exception(f"ADB命令执行失败: {result.stderr}")
            devices = []
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:
                if line.strip() and '\tdevice' in line:
                    devices.append(line.split('\t')[0])
            self.devices = devices
            print(f"找到设备: {devices}")
            return devices
        except Exception as e:
            print(f"获取设备列表失败: {e}")
            raise

    def is_device_connected(self, device_id):
        try:
            devices = self.get_adb_devices()
            return device_id in devices
        except Exception:
            return False

    def get_detected_adb_path(self):
        return self.adb_path

    def get_adb_info(self):
        info = {'path': self.adb_path, 'source': self.adb_source, 'version': '未知'}
        if self.adb_path:
            try:
                kwargs = _get_subprocess_kwargs()
                result = subprocess.run(
                    [self.adb_path, 'version'],
                    capture_output=True, text=True, timeout=5, **kwargs
                )
                if result.returncode == 0 and result.stdout:
                    info['version'] = result.stdout.splitlines()[0]
            except Exception:
                pass
        return info