import subprocess
import os
import re
import sys
from datetime import datetime

# ---------- 新增：隐藏子进程窗口的辅助函数（与device_manager保持一致） ----------
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
        """执行导入操作 - 基于shell脚本改写"""
        try:
            # 检查设备是否仍然连接
            if not self.device_manager.is_device_connected(device):
                return False, f"设备 {device} 已断开连接"
            
            adb_path = self.device_manager.get_detected_adb_path()
            if not adb_path:
                return False, "ADB路径未找到，请检查ADB环境"
            
            # 执行完整的导入命令序列
            commands = [
                # 推送数据库文件到设备
                f"\"{adb_path}\" -s {device} push \"{file_path}\" /data/local/tmp/db",
                # 备份原数据库
                f"\"{adb_path}\" -s {device} shell \"run-as com.android.cts.verifier cat /data/data/com.android.cts.verifier/databases/results.db > /data/local/tmp/db.bkp\"",
                # 替换数据库
                f"\"{adb_path}\" -s {device} shell \"run-as com.android.cts.verifier cp /data/local/tmp/db /data/data/com.android.cts.verifier/databases/results.db\"",
                # 清理临时文件
                f"\"{adb_path}\" -s {device} shell \"rm -f /data/local/tmp/db /data/local/tmp/db.bkp\""
            ]
            
            kwargs = _get_subprocess_kwargs()
            # 执行所有命令
            for cmd in commands:
                print(f"执行命令: {cmd}")
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=30,
                    **kwargs
                )
                
                if result.returncode != 0:
                    raise Exception(f"命令执行失败: {result.stderr}")
            
            return True, f"成功导入数据库到设备 {device}"
            
        except Exception as e:
            return False, f"导入过程中出现错误: {str(e)}"
    
    def perform_export(self, device, directory):
        """执行导出操作 - 使用命令列表方式"""
        try:
            # 检查设备是否仍然连接
            if not self.device_manager.is_device_connected(device):
                return False, f"设备 {device} 已断开连接"
            
            adb_path = self.device_manager.get_detected_adb_path()
            if not adb_path:
                return False, "ADB路径未找到，请检查ADB环境"
            
            # 生成文件名
            file_name = self._generate_filename(device)
            full_path = os.path.join(directory, file_name)
            
            # 执行完整的导出命令序列
            commands = [
                # 创建临时文件
                f"\"{adb_path}\" -s {device} shell \"touch /data/local/tmp/db\"",
                # 检查CTS Verifier进程
                f"\"{adb_path}\" -s {device} shell \"ps | grep com.android.cts.verifier\"",
                # 备份数据库到临时文件
                f"\"{adb_path}\" -s {device} shell \"run-as com.android.cts.verifier cat /data/data/com.android.cts.verifier/databases/results.db > /data/local/tmp/db\"",
                # 拉取文件到本地
                f"\"{adb_path}\" -s {device} pull /data/local/tmp/db \"{full_path}\""
            ]
            
            kwargs = _get_subprocess_kwargs()
            # 执行所有命令
            for cmd in commands:
                print(f"执行命令: {cmd}")
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=30,
                    **kwargs
                )
                
                # 忽略检查进程命令的错误，因为grep可能找不到进程
                if result.returncode != 0 and "ps | grep" not in cmd:
                    raise Exception(f"命令执行失败: {result.stderr}")
            
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
        """执行ADB命令"""
        adb_path = self.device_manager.get_detected_adb_path()
        if not adb_path:
            raise Exception("ADB路径未找到")
        
        full_command = f"\"{adb_path}\" -s {device} {command}"
        
        try:
            kwargs = _get_subprocess_kwargs()
            result = subprocess.run(
                full_command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30,
                **kwargs
            )
            
            if result.returncode != 0:
                raise Exception(f"ADB命令执行失败: {result.stderr}")
            
            return result.stdout
        except subprocess.TimeoutExpired:
            raise Exception("ADB命令执行超时")
        except Exception as e:
            raise Exception(f"执行ADB命令时出错: {str(e)}")