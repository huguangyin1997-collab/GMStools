import subprocess
import os
import re
import sys
from datetime import datetime

# ---------- 隐藏子进程窗口的辅助函数 ----------
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

class OperationHandler:
    """操作处理类"""
    
    def __init__(self, device_manager, directory_manager):
        self.device_manager = device_manager
        self.directory_manager = directory_manager
    
    def perform_import(self, device, file_path):
        """执行导入操作 - 基于shell脚本改写，使用列表参数"""
        try:
            # 检查设备是否仍然连接
            if not self.device_manager.is_device_connected(device):
                return False, f"设备 {device} 已断开连接"
            
            adb_path = self.device_manager.get_detected_adb_path()
            if not adb_path:
                return False, "ADB路径未找到，请检查ADB环境"
            
            kwargs = _get_subprocess_kwargs()
            
            # 1. 推送数据库文件到设备临时目录
            push_cmd = [adb_path, "-s", device, "push", file_path, "/data/local/tmp/db"]
            result = subprocess.run(push_cmd, capture_output=True, text=True, timeout=30, **kwargs)
            if result.returncode != 0:
                raise Exception(f"推送文件失败: {result.stderr}")
            
            # 2. 备份原数据库到临时文件
            backup_cmd = [adb_path, "-s", device, "shell", "run-as com.android.cts.verifier cat /data/data/com.android.cts.verifier/databases/results.db > /data/local/tmp/db.bkp"]
            result = subprocess.run(backup_cmd, capture_output=True, text=True, timeout=30, **kwargs)
            if result.returncode != 0:
                raise Exception(f"备份数据库失败: {result.stderr}")
            
            # 3. 替换数据库
            replace_cmd = [adb_path, "-s", device, "shell", "run-as com.android.cts.verifier cp /data/local/tmp/db /data/data/com.android.cts.verifier/databases/results.db"]
            result = subprocess.run(replace_cmd, capture_output=True, text=True, timeout=30, **kwargs)
            if result.returncode != 0:
                raise Exception(f"替换数据库失败: {result.stderr}")
            
            # 4. 清理临时文件
            clean_cmd = [adb_path, "-s", device, "shell", "rm -f /data/local/tmp/db /data/local/tmp/db.bkp"]
            subprocess.run(clean_cmd, capture_output=True, text=True, timeout=30, **kwargs)  # 忽略清理错误
            
            return True, f"成功导入数据库到设备 {device}"
            
        except Exception as e:
            return False, f"导入过程中出现错误: {str(e)}"
    
    def perform_export(self, device, directory):
        """执行导出操作 - 使用列表参数"""
        try:
            # 检查设备是否仍然连接
            if not self.device_manager.is_device_connected(device):
                return False, f"设备 {device} 已断开连接"
            
            adb_path = self.device_manager.get_detected_adb_path()
            if not adb_path:
                return False, "ADB路径未找到，请检查ADB环境"
            
            kwargs = _get_subprocess_kwargs()
            
            # 生成文件名
            file_name = self._generate_filename(device)
            full_path = os.path.join(directory, file_name)
            
            # 1. 创建临时文件（确保存在）
            touch_cmd = [adb_path, "-s", device, "shell", "touch /data/local/tmp/db"]
            subprocess.run(touch_cmd, capture_output=True, text=True, timeout=30, **kwargs)  # 忽略错误
            
            # 2. 检查CTS Verifier进程（可选，忽略错误）
            ps_cmd = [adb_path, "-s", device, "shell", "ps | grep com.android.cts.verifier"]
            subprocess.run(ps_cmd, capture_output=True, text=True, timeout=30, **kwargs)
            
            # 3. 备份数据库到临时文件
            backup_cmd = [adb_path, "-s", device, "shell", "run-as com.android.cts.verifier cat /data/data/com.android.cts.verifier/databases/results.db > /data/local/tmp/db"]
            result = subprocess.run(backup_cmd, capture_output=True, text=True, timeout=30, **kwargs)
            if result.returncode != 0:
                raise Exception(f"备份数据库失败: {result.stderr}")
            
            # 4. 拉取文件到本地
            pull_cmd = [adb_path, "-s", device, "pull", "/data/local/tmp/db", full_path]
            result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=30, **kwargs)
            if result.returncode != 0:
                raise Exception(f"拉取文件失败: {result.stderr}")
            
            return True, f"成功导出数据库到: {full_path}"
            
        except Exception as e:
            return False, f"导出过程中出现错误: {str(e)}"
    
    def _generate_filename(self, device):
        """生成导出文件名"""
        # 获取当前日期和时间
        now = datetime.now()
        date_str = now.strftime('%Y%m%d')
        time_str = now.strftime('%H%M%S')
        
        # 获取设备属性
        try:
            product_name = self._run_adb_command(device, "shell getprop ro.build.product").strip()
            release_version = self._run_adb_command(device, "shell getprop ro.build.version.incremental").strip()
            
            # 清理字符串中的特殊字符
            product_name = re.sub(r'[^\w\-_.]', '_', product_name)
            release_version = re.sub(r'[^\w\-_.]', '_', release_version)
            
            file_name = f"{product_name}-{release_version}-{date_str}-{time_str}.db"
        except Exception as e:
            # 如果获取设备属性失败，使用默认文件名
            file_name = f"cts_verifier_backup-{date_str}-{time_str}.db"
        
        return file_name
    
    def _run_adb_command(self, device, command):
        """执行ADB命令（已修改为列表参数）"""
        adb_path = self.device_manager.get_detected_adb_path()
        if not adb_path:
            raise Exception("ADB路径未找到")
        
        # 将命令字符串拆分为列表（注意：命令可能包含参数，但这里简单处理）
        # 对于复杂命令（如带管道的），我们保留原始方式，但这种情况较少。
        # 这里假设 command 是一个简单的参数列表（如 "shell getprop ro.build.product"）
        parts = command.split()
        cmd = [adb_path, "-s", device] + parts
        
        kwargs = _get_subprocess_kwargs()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, **kwargs)
            if result.returncode != 0:
                raise Exception(f"ADB命令执行失败: {result.stderr}")
            return result.stdout
        except subprocess.TimeoutExpired:
            raise Exception("ADB命令执行超时")
        except Exception as e:
            raise Exception(f"执行ADB命令时出错: {str(e)}")