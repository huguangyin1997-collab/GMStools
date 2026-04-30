# update_manager.py
import json
import os
import sys
import hashlib
import tempfile
import zipfile
import subprocess
import shutil
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from PyQt6.QtCore import QObject, QUrl, QStandardPaths
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtWidgets import QApplication, QMessageBox

from .constants import APP_VERSION, GITHUB_API_URL, CACHE_FILE, compare_versions
from .miku_dialog import MikuDialog


class UpdateManager(QObject):
    def __init__(self, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget  # 用于显示对话框的父窗口

        self.app_data_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppLocalDataLocation
        )
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir)

        self.cache_path = os.path.join(self.app_data_dir, CACHE_FILE)
        self.pending_cleanup_file = os.path.join(self.app_data_dir, "pending_cleanup.txt")

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_update_check_finished)

        self.download_manager = QNetworkAccessManager()
        self.download_manager.finished.connect(self.on_download_finished)

        self.download_reply = None
        self.temp_dir = None
        self.download_path = None
        self.expected_sha256 = None

        self.current_button = None  # 用于更新按钮状态

    # ---------- 清理临时目录 ----------
    def cleanup_pending_temp(self):
        """清理上次更新后遗留的临时目录（启动时调用）"""
        if not os.path.exists(self.pending_cleanup_file):
            return
        try:
            with open(self.pending_cleanup_file, 'r', encoding='utf-8') as f:
                paths = [line.strip() for line in f if line.strip()]
            for path in paths:
                clean_path = path.strip('"')
                if os.path.exists(clean_path):
                    for attempt in range(3):
                        try:
                            shutil.rmtree(clean_path, ignore_errors=False)
                            print(f"已清理临时目录: {clean_path}")
                            break
                        except Exception as e:
                            if attempt == 2:
                                print(f"清理临时目录失败（尝试3次）: {clean_path}，错误: {e}")
                                shutil.rmtree(clean_path, ignore_errors=True)
                            else:
                                time.sleep(0.5)
            os.remove(self.pending_cleanup_file)
        except Exception as e:
            print(f"清理临时目录时出错: {e}")

    # ---------- 缓存 ----------
    def _load_cache(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.cache_path):
            return None
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            check_time = datetime.fromisoformat(cache['check_time'])
            if datetime.now() - check_time < timedelta(hours=1):
                return cache
        except Exception:
            pass
        return None

    def _save_cache(self, version_info: Dict[str, Any]):
        cache = {
            'check_time': datetime.now().isoformat(),
            'latest_version': version_info.get('latest_version', ''),
            'release_notes': version_info.get('release_notes', ''),
        }
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败：{e}")

    # ---------- 检查更新 ----------
    def check_for_updates(self, button=None):
        self.current_button = button
        if button:
            button.setEnabled(False)
            button.setText("检查中...")

        cache = self._load_cache()
        if cache:
            latest_version = cache.get('latest_version', '')
            if compare_versions(latest_version, APP_VERSION) > 0:
                dlg = MikuDialog(self.parent_widget, "提示",
                                 f"本地缓存提示有新版本 {latest_version}，正在联网确认...",
                                 QMessageBox.StandardButton.Ok)
                dlg.exec()
            else:
                dlg = MikuDialog(self.parent_widget, "提示",
                                 "正在联网检查最新版本...",
                                 QMessageBox.StandardButton.Ok)
                dlg.exec()

        url = QUrl(GITHUB_API_URL)
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader,
                          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.network_manager.get(request)

    def on_update_check_finished(self, reply: QNetworkReply):
        if self.current_button:
            self.current_button.setEnabled(True)
            self.current_button.setText("检查更新")

        if reply.error() != QNetworkReply.NetworkError.NoError:
            self._handle_network_error(reply,
                                       reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute),
                                       reply.errorString())
            reply.deleteLater()
            return

        data = reply.readAll().data()
        reply.deleteLater()

        try:
            text = data.decode('utf-8', errors='replace')
        except Exception as e:
            self._show_response_error(f"解码响应失败：{e}\n数据预览：{data[:200]}")
            return

        try:
            info = json.loads(text)
            latest_tag = info.get("tag_name", "")
            if not latest_tag:
                dlg = MikuDialog(self.parent_widget, "解析失败",
                                 "未能获取到版本信息。",
                                 QMessageBox.StandardButton.Ok)
                dlg.exec()
                return

            latest_version = latest_tag.lstrip('v')
            release_notes = info.get("body", "暂无更新说明")
            assets = info.get("assets", [])

            self._save_cache({'latest_version': latest_version, 'release_notes': release_notes})

            if compare_versions(latest_version, APP_VERSION) <= 0:
                dlg = MikuDialog(self.parent_widget, "检查更新",
                                 "当前已是最新版本。",
                                 QMessageBox.StandardButton.Ok)
                dlg.exec()
                return

            is_windows = sys.platform == "win32"
            target_asset = None
            for asset in assets:
                name = asset.get("name", "").lower()
                if is_windows:
                    if any(k in name for k in ["windows", "win32", "win64", ".exe"]):
                        target_asset = asset
                        break
                else:
                    if any(k in name for k in ["linux", "ubuntu", "debian"]):
                        target_asset = asset
                        break

            if not target_asset and assets:
                target_asset = assets[0]
                dlg = MikuDialog(self.parent_widget, "提示",
                                 "未找到明确匹配当前平台的更新包，将使用第一个附件，请确保其适用于您的系统。",
                                 QMessageBox.StandardButton.Ok)
                dlg.exec()

            if not target_asset:
                dlg = MikuDialog(self.parent_widget, "检查更新",
                                 f"发现新版本 {latest_version}，但未找到任何更新包。\n请手动访问 Releases 页面下载：\nhttps://github.com/huguangyin1997-collab/GMStools/releases",
                                 QMessageBox.StandardButton.Ok)
                dlg.exec()
                return

            msg = (f"发现新版本 {latest_version}！\n\n更新内容：\n{release_notes}\n\n是否立即下载并安装更新？")
            dlg = MikuDialog(self.parent_widget, "发现新版本", msg,
                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if dlg.exec() == QMessageBox.StandardButton.Yes:
                self.download_update(target_asset)

        except json.JSONDecodeError:
            self._show_response_error(f"服务器返回的不是有效的 JSON。\n返回内容预览：{text[:500]}")
        except Exception as e:
            dlg = MikuDialog(self.parent_widget, "解析失败",
                             f"版本信息处理出错：{str(e)}",
                             QMessageBox.StandardButton.Ok)
            dlg.exec()

    def _handle_network_error(self, reply, http_status, error_str):
        response_data = reply.readAll().data()
        response_text = ""
        if response_data:
            try:
                response_text = response_data.decode('utf-8', errors='replace')
            except:
                response_text = "<无法解码响应内容>"

        if http_status == 403:
            try:
                error_info = json.loads(response_text)
                if "rate limit" in error_info.get("message", "").lower():
                    dlg = MikuDialog(self.parent_widget, "检查更新",
                                     "GitHub API 访问次数已达上限（每小时60次），请稍后再试。\n您也可以直接访问 Releases 页面查看最新版本。",
                                     QMessageBox.StandardButton.Ok)
                    dlg.exec()
                    return
            except:
                pass
            dlg = MikuDialog(self.parent_widget, "检查更新",
                             f"访问被拒绝 (HTTP 403)。请稍后重试。\n响应预览：{response_text[:200]}",
                             QMessageBox.StandardButton.Ok)
            dlg.exec()
        elif http_status == 404:
            dlg = MikuDialog(self.parent_widget, "检查更新",
                             "GitHub 仓库中尚未发布任何版本。\n请访问 Releases 页面关注后续更新。",
                             QMessageBox.StandardButton.Ok)
            dlg.exec()
        else:
            dlg = MikuDialog(self.parent_widget, "检查失败",
                             f"网络错误 (HTTP {http_status}): {error_str}\n\n响应预览：{response_text[:200]}",
                             QMessageBox.StandardButton.Ok)
            dlg.exec()

    def _show_response_error(self, details: str):
        dlg = MikuDialog(self.parent_widget, "响应内容异常", details,
                         QMessageBox.StandardButton.Ok)
        dlg.resize(600, 400)
        dlg.exec()

    # ---------- 下载更新 ----------
    def download_update(self, asset_info):
        url = asset_info['browser_download_url']
        expected_sha256 = asset_info.get('digest', '')
        if expected_sha256.startswith('sha256:'):
            expected_sha256 = expected_sha256[7:]

        self.expected_sha256 = expected_sha256 if expected_sha256 else None

        if self.current_button:
            self.current_button.setEnabled(False)
            self.current_button.setText("下载更新中...")

        self.temp_dir = tempfile.mkdtemp(prefix="gmstools_update_")
        self.download_path = os.path.join(self.temp_dir, asset_info['name'])

        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"Accept", b"application/octet-stream")
        self.download_reply = self.download_manager.get(request)
        self.download_reply.downloadProgress.connect(self.on_download_progress)

    def on_download_progress(self, bytes_received, bytes_total):
        if self.current_button:
            if bytes_total > 0:
                percent = int(bytes_received * 100 / bytes_total)
                self.current_button.setText(f"下载中 {percent}%")
            else:
                self.current_button.setText(f"下载中 {bytes_received/1024:.0f}KB")

    def _reset_check_button(self):
        if self.current_button:
            self.current_button.setEnabled(True)
            self.current_button.setText("检查更新")

    def _cleanup_temp(self):
        if self.download_reply:
            self.download_reply.deleteLater()
            self.download_reply = None
        if self.temp_dir and os.path.exists(self.temp_dir):
            for attempt in range(3):
                try:
                    shutil.rmtree(self.temp_dir, ignore_errors=False)
                    print(f"临时目录清理成功: {self.temp_dir}")
                    break
                except Exception as e:
                    if attempt == 2:
                        print(f"临时目录清理失败（尝试3次）: {self.temp_dir}，错误: {e}")
                        shutil.rmtree(self.temp_dir, ignore_errors=True)
                    else:
                        time.sleep(0.5)
        self.temp_dir = None
        self.download_path = None
        self.expected_sha256 = None

    def on_download_finished(self):
        reply = self.download_reply
        if not reply:
            return

        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                dlg = MikuDialog(self.parent_widget, "下载失败",
                                 f"网络错误：{reply.errorString()}",
                                 QMessageBox.StandardButton.Ok)
                dlg.exec()
                self._cleanup_temp()
                self._reset_check_button()
                return

            http_status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            if http_status != 200:
                error_data = reply.readAll().data()
                error_text = error_data.decode('utf-8', errors='replace')[:500]
                dlg = MikuDialog(self.parent_widget, "下载失败",
                                 f"HTTP 状态码 {http_status}，期望 200。\n响应预览：\n{error_text}",
                                 QMessageBox.StandardButton.Ok)
                dlg.exec()
                self._cleanup_temp()
                self._reset_check_button()
                return

            # 保存文件
            with open(self.download_path, 'wb') as f:
                f.write(reply.readAll().data())

            # 检查 ZIP 头部
            with open(self.download_path, 'rb') as f:
                header = f.read(2)
            if header != b'PK':
                dlg = MikuDialog(self.parent_widget, "文件错误",
                                 "下载的文件不是有效的 ZIP 格式，可能为 HTML 错误页。",
                                 QMessageBox.StandardButton.Ok)
                dlg.exec()
                self._cleanup_temp()
                self._reset_check_button()
                return

            # 校验 SHA256
            if self.expected_sha256:
                sha256_hash = hashlib.sha256()
                with open(self.download_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        sha256_hash.update(chunk)
                actual_hash = sha256_hash.hexdigest()
                if actual_hash != self.expected_sha256:
                    dlg = MikuDialog(self.parent_widget, "校验失败",
                                     f"文件校验和不匹配！\n期望：{self.expected_sha256}\n实际：{actual_hash}\n\n更新取消。",
                                     QMessageBox.StandardButton.Ok)
                    dlg.exec()
                    self._cleanup_temp()
                    self._reset_check_button()
                    return
                else:
                    dlg = MikuDialog(self.parent_widget, "校验成功",
                                     "文件完整性验证通过。",
                                     QMessageBox.StandardButton.Ok)
                    dlg.exec()

            # 解压
            extract_to = os.path.join(self.temp_dir, "new_version")
            os.makedirs(extract_to, exist_ok=True)
            try:
                with zipfile.ZipFile(self.download_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
            except Exception as e:
                dlg = MikuDialog(self.parent_widget, "解压失败",
                                 f"解压更新包失败：{str(e)}",
                                 QMessageBox.StandardButton.Ok)
                dlg.exec()
                self._cleanup_temp()
                self._reset_check_button()
                return

            contents = os.listdir(extract_to)
            if len(contents) == 1 and os.path.isdir(os.path.join(extract_to, contents[0])):
                extract_to = os.path.join(extract_to, contents[0])

            self.perform_update(extract_to)

        finally:
            reply.deleteLater()
            self.download_reply = None

    # ---------- 核心更新逻辑 ----------
    def perform_update(self, new_files_dir):
        if getattr(sys, 'frozen', False):
            install_dir = os.path.dirname(sys.executable)
            old_pid = os.getpid()
        else:
            install_dir = os.path.dirname(os.path.abspath(__file__))
            old_pid = os.getpid()

        is_windows = sys.platform == "win32"
        keep_files = ['config.ini']

        if is_windows:
            log_file = os.path.join(self.temp_dir, "update.log")
            script_path = os.path.join(self.temp_dir, "update.bat")
            with open(script_path, 'w', encoding='utf-8') as f:
                src = new_files_dir.replace('/', '\\')
                dst = install_dir.replace('/', '\\')
                exclude_options = ' '.join([f'/XF "{file}"' for file in keep_files])
                f.write(f"""@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
echo %DATE% %TIME% 开始更新 > "{log_file}" 2>&1

if not exist "{src}\\*" (
    echo %DATE% %TIME% 错误：源目录 {src} 不存在或为空 >> "{log_file}" 2>&1
    exit /b 1
)

echo %DATE% %TIME% 强制结束 GMStools.exe 和 adb.exe ... >> "{log_file}" 2>&1
taskkill /f /im GMStools.exe >> "{log_file}" 2>&1
taskkill /f /im adb.exe >> "{log_file}" 2>&1
timeout /t 2 /nobreak >nul

echo %DATE% %TIME% 开始复制文件从 "{src}" 到 "{dst}" >> "{log_file}" 2>&1
robocopy "{src}" "{dst}" /E {exclude_options} /R:3 /W:3 /NP /NDL /NFL /LOG+:"{log_file}"
set COPY_RESULT=%errorlevel%
echo %DATE% %TIME% robocopy 返回码: !COPY_RESULT! >> "{log_file}" 2>&1
if !COPY_RESULT! geq 8 (
    echo %DATE% %TIME% 复制过程中出现严重错误 >> "{log_file}" 2>&1
)

echo %DATE% %TIME% 目标目录内容: >> "{log_file}" 2>&1
dir "{dst}" /s /b >> "{log_file}" 2>&1

echo %DATE% %TIME% 清理旧解压目录... >> "{log_file}" 2>&1
if exist "%TEMP%\\_MEI*" (
    del /f /s /q "%TEMP%\\_MEI*" >nul 2>&1
    rmdir /s /q "%TEMP%\\_MEI*" >nul 2>&1
)
if exist "%LOCALAPPDATA%\\Temp\\_MEI*" (
    del /f /s /q "%LOCALAPPDATA%\\Temp\\_MEI*" >nul 2>&1
    rmdir /s /q "%LOCALAPPDATA%\\Temp\\_MEI*" >nul 2>&1
)

set _MEIPASS=
set PYTHONHOME=
set PYTHONPATH=
set TMP=%USERPROFILE%\\AppData\\Local\\Temp
set TEMP=%USERPROFILE%\\AppData\\Local\\Temp

set "EXE={install_dir}\\GMStools.exe"
echo %DATE% %TIME% 启动新版本: !EXE! >> "{log_file}" 2>&1
start /B "" "!EXE!" >nul 2>&1

echo %DATE% %TIME% 等待 15 秒让新程序初始化... >> "{log_file}" 2>&1
timeout /t 15 /nobreak >nul

tasklist /fi "imagename eq GMStools.exe" >> "{log_file}" 2>&1

copy "{log_file}" "{install_dir}\\update.log" /Y

echo "{self.temp_dir}" >> "{self.pending_cleanup_file}"

del "%~f0"
""")
            try:
                dlg = MikuDialog(self.parent_widget, "提示",
                                 "更新脚本即将运行，程序将退出。新版本将自动启动。",
                                 QMessageBox.StandardButton.Ok)
                if dlg.exec() == QMessageBox.StandardButton.Ok:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                    subprocess.Popen(
                        ['cmd', '/c', script_path],
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    QApplication.quit()
            except Exception as e:
                dlg = MikuDialog(self.parent_widget, "错误",
                                 f"启动更新脚本失败：{str(e)}",
                                 QMessageBox.StandardButton.Ok)
                dlg.exec()
                self._cleanup_temp()
                self._reset_check_button()
        else:
            # Linux 部分（略作修改，与原逻辑一致）
            log_file = os.path.join(self.temp_dir, "update.log")
            app_log_file = os.path.join(self.temp_dir, "app.log")
            script_path = os.path.join(self.temp_dir, "update.sh")

            uid = os.getuid()
            home = os.path.expanduser('~')
            display = os.environ.get('DISPLAY', ':0')
            xauthority = os.environ.get('XAUTHORITY', f'{home}/.Xauthority')
            dbus = os.environ.get('DBUS_SESSION_BUS_ADDRESS', f'unix:path=/run/user/{uid}/bus')
            xdg_runtime = os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{uid}')
            lang = os.environ.get('LANG', 'C.UTF-8')
            path = os.environ.get('PATH', '/usr/local/bin:/usr/bin:/bin')
            user = os.environ.get('USER', os.environ.get('LOGNAME', ''))

            with open(script_path, 'w') as f:
                f.write(f"""#!/bin/bash
exec > "{log_file}" 2>&1
echo "脚本开始执行于 $(date)"
echo "临时目录: {self.temp_dir}"
echo "新文件目录: {new_files_dir}"
echo "安装目录: {install_dir}"
echo "旧程序PID: {old_pid}"

if kill -0 {old_pid} 2>/dev/null; then
    echo "等待旧程序 (PID {old_pid}) 退出..."
    while kill -0 {old_pid} 2>/dev/null; do
        sleep 0.5
    done
    echo "旧程序已退出"
fi
sleep 1

cd "{new_files_dir}" || {{ echo "无法进入目录 {new_files_dir}"; exit 1; }}
echo "开始复制文件..."
for item in *; do
    if [[ "$item" == "config.ini" ]]; then
        continue
    fi
    echo "复制 $item 到 {install_dir}/"
    cp -rf "$item" "{install_dir}/"
done

if [ -f "{install_dir}/GMStools" ]; then
    chmod +x "{install_dir}/GMStools"
    echo "已设置可执行权限"
fi

cd "{install_dir}"
rm -rf /tmp/_MEI* "$TMPDIR"/_MEI* 2>/dev/null

echo "启动新版本..."
env -i DISPLAY="{display}" XAUTHORITY="{xauthority}" DBUS_SESSION_BUS_ADDRESS="{dbus}" XDG_RUNTIME_DIR="{xdg_runtime}" HOME="{home}" USER="{user}" PATH="{path}" LANG="{lang}" ./GMStools > "{app_log_file}" 2>&1 &
LAUNCH_PID=$!
echo "新程序启动PID: $LAUNCH_PID"

sleep 5
if [ -d /tmp/_MEI* ] || [ -d "$TMPDIR"/_MEI* ]; then
    echo "解压目录已创建，启动成功"
else
    echo "警告：未发现解压目录，可能启动失败"
    echo "应用日志："
    cat "{app_log_file}"
fi

cp "{log_file}" "{install_dir}/update.log"
echo "日志已保存到 {install_dir}/update.log"

echo "{self.temp_dir}" >> "{self.pending_cleanup_file}"

rm -- "$0"
""")
            os.chmod(script_path, 0o755)

            try:
                dlg = MikuDialog(self.parent_widget, "提示",
                                 "更新脚本即将运行，程序将退出。新版本将自动启动。",
                                 QMessageBox.StandardButton.Ok)
                if dlg.exec() == QMessageBox.StandardButton.Ok:
                    subprocess.Popen(['/bin/bash', script_path], start_new_session=True)
                    QApplication.quit()
            except Exception as e:
                dlg = MikuDialog(self.parent_widget, "错误",
                                 f"启动更新脚本失败：{str(e)}",
                                 QMessageBox.StandardButton.Ok)
                dlg.exec()
                self._cleanup_temp()
                self._reset_check_button()