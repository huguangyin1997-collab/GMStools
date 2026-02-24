import subprocess
import os
import sys
import platform

# ---------- 新增：隐藏子进程窗口的辅助函数 ----------
def _get_subprocess_kwargs():
    """返回用于隐藏 Windows 控制台窗口的参数"""
    kwargs = {}
    if sys.platform == 'win32':
        if hasattr(subprocess, 'CREATE_NO_WINDOW'):   # Python 3.7+
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        else:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = startupinfo
    return kwargs
# ------------------------------------------------

class DeviceManager:
    """设备管理类"""
    
    def __init__(self):
        self.devices = []  # 存储设备列表
        self.adb_path = None  # 存储检测到的ADB路径
        self.adb_source = None  # 记录ADB来源
    
    def _get_bundled_adb_path(self):
        """获取打包后的ADB路径 - 优先使用打包的ADB"""
        try:
            # 获取基础路径
            if getattr(sys, 'frozen', False):
                # 打包后的路径 - PyInstaller 单文件模式
                base_path = sys._MEIPASS
                print(f"MEIPASS路径: {base_path}")
            else:
                # 开发环境路径 - 使用脚本所在目录
                base_path = os.path.dirname(os.path.abspath(__file__))
                # 在开发环境中，pages/Ctsverifierdb/device_manager.py
                # 需要向上两级到项目根目录
                base_path = os.path.dirname(os.path.dirname(base_path))
            
            system = platform.system()
            
            if system == "Windows":
                # Windows 平台 - 先检查打包后的路径
                # 方案1: platform-tools/windows/adb.exe
                adb_relative_path = os.path.join("platform-tools", "windows", "adb.exe")
                bundled_adb_path = os.path.join(base_path, adb_relative_path)
                
                # 如果方案1不存在，尝试方案2: _internal/platform-tools/windows/adb.exe
                if not os.path.isfile(bundled_adb_path) and getattr(sys, 'frozen', False):
                    bundled_adb_path = os.path.join(base_path, "_internal", adb_relative_path)
                
                # 如果方案2不存在，尝试方案3: 从可执行文件所在目录查找
                if not os.path.isfile(bundled_adb_path) and getattr(sys, 'frozen', False):
                    exe_dir = os.path.dirname(sys.executable)
                    bundled_adb_path = os.path.join(exe_dir, adb_relative_path)
                
                print(f"Windows ADB路径: {bundled_adb_path}")
                
            else:  # Linux
                # Linux 平台
                adb_relative_path = os.path.join("platform-tools", "linux", "adb")
                bundled_adb_path = os.path.join(base_path, adb_relative_path)
                
                # 如果不存在，尝试其他路径
                if not os.path.isfile(bundled_adb_path) and getattr(sys, 'frozen', False):
                    bundled_adb_path = os.path.join(base_path, "_internal", adb_relative_path)
                
                if not os.path.isfile(bundled_adb_path) and getattr(sys, 'frozen', False):
                    exe_dir = os.path.dirname(sys.executable)
                    bundled_adb_path = os.path.join(exe_dir, adb_relative_path)
                
                # 设置执行权限
                if os.path.isfile(bundled_adb_path):
                    try:
                        os.chmod(bundled_adb_path, 0o755)
                        print(f"设置ADB执行权限: {bundled_adb_path}")
                    except Exception as e:
                        print(f"设置ADB执行权限失败: {e}")
            
            if os.path.isfile(bundled_adb_path):
                print(f"找到打包的ADB: {bundled_adb_path}")
                return bundled_adb_path
            else:
                print(f"未找到打包的ADB: {bundled_adb_path}")
                # 尝试在项目根目录查找
                project_root = self._find_project_root()
                if project_root:
                    test_path = os.path.join(project_root, adb_relative_path)
                    if os.path.isfile(test_path):
                        print(f"在项目根目录找到ADB: {test_path}")
                        return test_path
                
                raise Exception(f"打包的ADB未找到: {adb_relative_path}")
                
        except Exception as e:
            print(f"获取打包ADB路径失败: {e}")
            raise
    
    def _find_project_root(self):
        """查找项目根目录"""
        try:
            # 从当前文件位置向上查找，直到找到 platform-tools 目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 最多向上查找5层
            for _ in range(5):
                if os.path.exists(os.path.join(current_dir, "platform-tools")):
                    return current_dir
                parent_dir = os.path.dirname(current_dir)
                if parent_dir == current_dir:  # 到达根目录
                    break
                current_dir = parent_dir
            
            return None
        except Exception as e:
            return None
    
    def _find_system_adb(self):
        """查找系统ADB路径"""
        try:
            system = platform.system()
            kwargs = _get_subprocess_kwargs()  # 隐藏窗口
            
            if system == "Windows":
                # Windows: 使用 where 命令
                result = subprocess.run(
                    ['where', 'adb'], 
                    capture_output=True, 
                    text=True, 
                    timeout=5,
                    shell=True,
                    **kwargs
                )
            else:
                # Linux: 使用 which 命令
                result = subprocess.run(
                    ['which', 'adb'], 
                    capture_output=True, 
                    text=True, 
                    timeout=5,
                    **kwargs
                )
            
            if result.returncode == 0:
                paths = result.stdout.strip().split('\n')
                for path in paths:
                    path = path.strip()
                    if os.path.isfile(path):
                        return path
                        
        except subprocess.TimeoutExpired:
            print("查找系统ADB超时")
        except Exception as e:
            print(f"查找系统ADB失败: {e}")
        
        return None
    
    def _find_adb_path(self):
        """查找ADB路径 - 优先使用打包的ADB"""
        # 方法1: 优先使用打包的ADB
        try:
            bundled_path = self._get_bundled_adb_path()
            if bundled_path and os.path.isfile(bundled_path):
                self.adb_source = "bundled"
                return bundled_path
        except Exception as e:
            print(f"查找打包ADB失败: {e}")
        
        # 方法2: 如果打包的ADB不存在，再尝试系统ADB
        system_adb = self._find_system_adb()
        if system_adb:
            self.adb_source = "system_path"
            return system_adb
        
        # 方法3: 尝试在当前目录查找
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if platform.system() == "Windows":
                local_adb = os.path.join(current_dir, "adb.exe")
            else:
                local_adb = os.path.join(current_dir, "adb")
            
            if os.path.isfile(local_adb):
                self.adb_source = "local"
                return local_adb
        except Exception as e:
            print(f"查找本地ADB失败: {e}")
        
        raise Exception("未找到ADB路径")
    
    def check_adb_environment(self, refresh_callback, error_callback):
        """检查ADB环境是否可用"""
        try:
            # 获取ADB路径
            self.adb_path = self._find_adb_path()
            
            if not self.adb_path or not os.path.isfile(self.adb_path):
                raise Exception("ADB未找到或不可用")
            
            # 验证ADB是否可用（已添加窗口隐藏）
            kwargs = _get_subprocess_kwargs()
            result = subprocess.run(
                [self.adb_path, 'version'], 
                capture_output=True, 
                text=True, 
                timeout=5,
                **kwargs
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
        """设置自定义ADB路径"""
        if not custom_path or not os.path.isfile(custom_path):
            raise Exception("自定义ADB路径无效")
        
        self.adb_path = custom_path
        self.adb_source = "custom"
        print(f"设置自定义ADB: {custom_path}")
        return True
    
    def get_adb_devices(self):
        """从adb devices获取设备列表"""
        try:
            if not self.adb_path:
                self.adb_path = self._find_adb_path()
            
            kwargs = _get_subprocess_kwargs()
            result = subprocess.run(
                [self.adb_path, 'devices'], 
                capture_output=True, 
                text=True, 
                timeout=10,
                **kwargs
            )
            
            if result.returncode != 0:
                raise Exception(f"ADB命令执行失败: {result.stderr}")
            
            devices = []
            lines = result.stdout.strip().split('\n')
            
            # 跳过第一行标题行
            for line in lines[1:]:
                if line.strip() and '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
            
            self.devices = devices
            print(f"找到设备: {devices}")
            return devices
            
        except subprocess.TimeoutExpired:
            raise Exception("ADB devices 命令超时")
        except Exception as e:
            print(f"获取设备列表失败: {e}")
            raise
    
    def is_device_connected(self, device_id):
        """检查特定设备是否连接"""
        try:
            devices = self.get_adb_devices()
            return device_id in devices
        except Exception as e:
            print(f"检查设备连接失败: {e}")
            return False
    
    def get_detected_adb_path(self):
        """获取检测到的ADB路径"""
        return self.adb_path
    
    def get_adb_info(self):
        """获取ADB信息"""
        info = {
            'path': self.adb_path,
            'source': self.adb_source,
            'is_bundled': False,
            'version': '未知'
        }
        
        if self.adb_path:
            info['is_bundled'] = (self.adb_source == "bundled")
            
            try:
                kwargs = _get_subprocess_kwargs()
                result = subprocess.run(
                    [self.adb_path, 'version'], 
                    capture_output=True, 
                    text=True, 
                    timeout=5,
                    **kwargs
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        info['version'] = lines[0]
            except Exception as e:
                print(f"获取ADB版本失败: {e}")
        
        return info