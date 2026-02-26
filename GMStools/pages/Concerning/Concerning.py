import json
import os
import sys
import webbrowser
import hashlib
import tempfile
import zipfile
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QPushButton, QHBoxLayout, QMessageBox, QApplication,
    QTextEdit, QDialog, QVBoxLayout as QVBoxLayoutDlg
)
from PyQt6.QtCore import Qt, QUrl, QStandardPaths, QTimer
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

# ==================== 当前程序版本 ====================
APP_VERSION = "1.2.3"

# GitHub API 地址（最新 Release）
GITHUB_API_URL = "https://api.github.com/repos/huguangyin1997-collab/GMStools/releases/latest"

# 缓存文件名（存放在用户数据目录）
CACHE_FILE = "version_cache.json"


def compare_versions(v1: str, v2: str) -> int:
    """语义化版本比较"""
    def normalize(v):
        return [int(x) for x in v.split('.')]
    parts1 = normalize(v1)
    parts2 = normalize(v2)
    for i in range(max(len(parts1), len(parts2))):
        n1 = parts1[i] if i < len(parts1) else 0
        n2 = parts2[i] if i < len(parts2) else 0
        if n1 != n2:
            return n1 - n2
    return 0


class Concerning(QWidget):
    """关于开发页面（带滚动区域）"""

    def __init__(self):
        super().__init__()
        self.app_data_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppLocalDataLocation
        )
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir)
        self.cache_path = os.path.join(self.app_data_dir, CACHE_FILE)

        # 网络管理器
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_update_check_finished)

        self.download_manager = QNetworkAccessManager()
        self.download_manager.finished.connect(self.on_download_finished)

        # 下载临时变量
        self.download_reply = None
        self.temp_dir = None
        self.download_path = None
        self.expected_sha256 = None

        self.setup_ui()

    # ---------- UI 构建 ----------
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(0)
        main_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("关于 GMStools")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50; padding: 15px; background-color: rgba(255, 255, 255, 0.7); border-radius: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 版本信息卡片
        version_card = QWidget()
        version_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border: 2px solid #bdc3c7; border-radius: 8px; padding: 15px;")
        version_layout = QVBoxLayout(version_card)

        version_title = QLabel("版本信息")
        version_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        version_layout.addWidget(version_title)

        self.version_label = QLabel(f"当前版本：{APP_VERSION}")
        self.version_label.setStyleSheet("font-size: 14px; color: #34495e;")
        version_layout.addWidget(self.version_label)

        build_label = QLabel(f"构建版本：Release {APP_VERSION}")
        build_label.setStyleSheet("font-size: 14px; color: #34495e;")
        version_layout.addWidget(build_label)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        self.check_btn = QPushButton("检查更新")
        self.check_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-size: 14px; font-weight: bold; padding: 8px 16px; border-radius: 5px; border: none; } QPushButton:hover { background-color: #2980b9; } QPushButton:pressed { background-color: #216694; }")
        self.check_btn.clicked.connect(self.check_for_updates)
        button_layout.addStretch()
        button_layout.addWidget(self.check_btn)
        button_layout.addStretch()

        version_layout.addLayout(button_layout)
        layout.addWidget(version_card)

        # 开发者卡片
        developer_card = QWidget()
        developer_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border: 2px solid #bdc3c7; border-radius: 8px; padding: 15px;")
        dev_layout = QVBoxLayout(developer_card)
        dev_title = QLabel("开发团队")
        dev_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        dev_layout.addWidget(dev_title)
        dev_info = QLabel("主程序：GMStools 开发组<br>贡献者：Huguangyin<br>特别感谢：所有测试用户")
        dev_info.setTextFormat(Qt.TextFormat.RichText)
        dev_info.setStyleSheet("font-size: 14px; color: #34495e; line-height: 1.6;")
        dev_layout.addWidget(dev_info)
        layout.addWidget(developer_card)

        # 联系与支持卡片
        contact_card = QWidget()
        contact_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border: 2px solid #bdc3c7; border-radius: 8px; padding: 15px;")
        contact_layout = QVBoxLayout(contact_card)
        contact_title = QLabel("联系与支持")
        contact_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        contact_layout.addWidget(contact_title)
        contact_info = QLabel("邮箱：1737660582@qq.com<br>电话：18334185042<br>github：https://github.com/huguangyin1997-collab/GMStools.git<br>问题反馈：请邮箱或 GitHub")
        contact_info.setTextFormat(Qt.TextFormat.RichText)
        contact_info.setStyleSheet("font-size: 14px; color: #34495e; line-height: 1.6;")
        contact_layout.addWidget(contact_info)
        layout.addWidget(contact_card)

        # 版权信息卡片
        copyright_card = QWidget()
        copyright_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.7); border: 2px solid #bdc3c7; border-radius: 8px; padding: 15px;")
        copyright_layout = QVBoxLayout(copyright_card)
        copyright_title = QLabel("版权声明")
        copyright_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        copyright_layout.addWidget(copyright_title)
        copyright_text = QLabel("© 2026 GMStools 开发组。保留所有权利。<br>本软件按“原样”提供，详情请参阅免责声明。")
        copyright_text.setTextFormat(Qt.TextFormat.RichText)
        copyright_text.setStyleSheet("font-size: 14px; color: #34495e; line-height: 1.6;")
        copyright_layout.addWidget(copyright_text)
        layout.addWidget(copyright_card)

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
    def check_for_updates(self):
        cache = self._load_cache()
        if cache:
            latest_version = cache.get('latest_version', '')
            if compare_versions(latest_version, APP_VERSION) > 0:
                QMessageBox.information(self, "提示", f"本地缓存提示有新版本 {latest_version}，正在联网确认...")
            else:
                QMessageBox.information(self, "提示", "正在联网检查最新版本...")

        self.check_btn.setEnabled(False)
        self.check_btn.setText("检查中...")

        url = QUrl(GITHUB_API_URL)
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader,
                          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.network_manager.get(request)

    def on_update_check_finished(self, reply: QNetworkReply):
        self.check_btn.setEnabled(True)
        self.check_btn.setText("检查更新")

        if reply.error() != QNetworkReply.NetworkError.NoError:
            self._handle_network_error(reply, reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute), reply.errorString())
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
                QMessageBox.warning(self, "解析失败", "未能获取到版本信息。")
                return

            latest_version = latest_tag.lstrip('v')
            release_notes = info.get("body", "暂无更新说明")
            assets = info.get("assets", [])

            self._save_cache({'latest_version': latest_version, 'release_notes': release_notes})

            if compare_versions(latest_version, APP_VERSION) <= 0:
                QMessageBox.information(self, "检查更新", "当前已是最新版本。")
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
                QMessageBox.information(self, "提示", "未找到明确匹配当前平台的更新包，将使用第一个附件，请确保其适用于您的系统。")

            if not target_asset:
                QMessageBox.warning(self, "检查更新", f"发现新版本 {latest_version}，但未找到任何更新包。\n请手动访问 Releases 页面下载：\nhttps://github.com/huguangyin1997-collab/GMStools/releases")
                return

            msg = (f"发现新版本 {latest_version}！\n\n更新内容：\n{release_notes}\n\n是否立即下载并安装更新？")
            user_choice = QMessageBox.question(self, "发现新版本", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if user_choice == QMessageBox.StandardButton.Yes:
                self.download_update(target_asset)

        except json.JSONDecodeError:
            self._show_response_error(f"服务器返回的不是有效的 JSON。\n返回内容预览：{text[:500]}")
        except Exception as e:
            QMessageBox.warning(self, "解析失败", f"版本信息处理出错：{str(e)}")

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
                    QMessageBox.warning(self, "检查更新", "GitHub API 访问次数已达上限（每小时60次），请稍后再试。\n您也可以直接访问 Releases 页面查看最新版本。")
                    return
            except:
                pass
            QMessageBox.warning(self, "检查更新", f"访问被拒绝 (HTTP 403)。请稍后重试。\n响应预览：{response_text[:200]}")
        elif http_status == 404:
            QMessageBox.information(self, "检查更新", "GitHub 仓库中尚未发布任何版本。\n请访问 Releases 页面关注后续更新。")
        else:
            QMessageBox.warning(self, "检查失败", f"网络错误 (HTTP {http_status}): {error_str}\n\n响应预览：{response_text[:200]}")

    def _show_response_error(self, details: str):
        dialog = QDialog(self)
        dialog.setWindowTitle("响应内容异常")
        layout = QVBoxLayoutDlg(dialog)
        label = QLabel("从服务器返回了意外的内容，无法解析版本信息。详细信息如下：")
        layout.addWidget(label)
        text_edit = QTextEdit()
        text_edit.setPlainText(details)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        btn = QPushButton("关闭")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.resize(600, 400)
        dialog.exec()

    # ---------- 下载更新 ----------
    def download_update(self, asset_info):
        url = asset_info['browser_download_url']
        expected_sha256 = asset_info.get('digest', '')
        if expected_sha256.startswith('sha256:'):
            expected_sha256 = expected_sha256[7:]

        self.expected_sha256 = expected_sha256 if expected_sha256 else None

        self.check_btn.setEnabled(False)
        self.check_btn.setText("下载更新中...")

        self.temp_dir = tempfile.mkdtemp(prefix="gmstools_update_")
        self.download_path = os.path.join(self.temp_dir, asset_info['name'])

        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"Accept", b"application/octet-stream")
        self.download_reply = self.download_manager.get(request)
        self.download_reply.downloadProgress.connect(self.on_download_progress)

    def on_download_progress(self, bytes_received, bytes_total):
        if bytes_total > 0:
            percent = int(bytes_received * 100 / bytes_total)
            self.check_btn.setText(f"下载中 {percent}%")
        else:
            self.check_btn.setText(f"下载中 {bytes_received/1024:.0f}KB")

    def on_download_finished(self):
        expected_sha256 = self.expected_sha256
        if not self.download_reply:
            return

        if self.download_reply.error() != QNetworkReply.NetworkError.NoError:
            QMessageBox.critical(self, "下载失败", f"网络错误：{self.download_reply.errorString()}")
            self._cleanup_temp()
            return

        http_status = self.download_reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if http_status != 200:
            error_data = self.download_reply.readAll().data()
            error_text = error_data.decode('utf-8', errors='replace')[:500]
            QMessageBox.critical(self, "下载失败", f"HTTP 状态码 {http_status}，期望 200。\n响应预览：\n{error_text}")
            self._cleanup_temp()
            return

        with open(self.download_path, 'wb') as f:
            f.write(self.download_reply.readAll().data())

        with open(self.download_path, 'rb') as f:
            header = f.read(2)
        if header != b'PK':
            QMessageBox.critical(self, "文件错误", "下载的文件不是有效的 ZIP 格式，可能为 HTML 错误页。")
            self._cleanup_temp()
            return

        if expected_sha256:
            sha256_hash = hashlib.sha256()
            with open(self.download_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            actual_hash = sha256_hash.hexdigest()
            if actual_hash != expected_sha256:
                QMessageBox.critical(self, "校验失败", f"文件校验和不匹配！\n期望：{expected_sha256}\n实际：{actual_hash}\n\n更新取消。")
                self._cleanup_temp()
                return
            else:
                QMessageBox.information(self, "校验成功", "文件完整性验证通过。")

        extract_to = os.path.join(self.temp_dir, "new_version")
        os.makedirs(extract_to, exist_ok=True)
        try:
            with zipfile.ZipFile(self.download_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        except Exception as e:
            QMessageBox.critical(self, "解压失败", f"解压更新包失败：{str(e)}")
            self._cleanup_temp()
            return

        contents = os.listdir(extract_to)
        if len(contents) == 1 and os.path.isdir(os.path.join(extract_to, contents[0])):
            extract_to = os.path.join(extract_to, contents[0])

        self.perform_update(extract_to)
        # 不再在这里清理临时目录，让更新脚本自己清理

    def _cleanup_temp(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.temp_dir = None
        self.download_path = None
        self.expected_sha256 = None
        self.download_reply = None

    # ---------- 核心更新逻辑（最终版，使用 env 设置 TMPDIR）----------
    def perform_update(self, new_files_dir):
        if getattr(sys, 'frozen', False):
            install_dir = os.path.dirname(sys.executable)
            old_pid = os.getpid()
        else:
            install_dir = os.path.dirname(os.path.abspath(__file__))
            old_pid = os.getpid()

        is_windows = sys.platform == "win32"
        keep_files = ['config.ini']
        log_file = os.path.join(self.temp_dir, "update.log")
        app_log_file = os.path.join(self.temp_dir, "app.log")

        if is_windows:
            script_path = os.path.join(self.temp_dir, "update.bat")
            with open(script_path, 'w') as f:
                src = new_files_dir.replace('/', '\\')
                if not src.endswith('\\'):
                    src += '\\'
                dst = install_dir.replace('/', '\\')
                exclude_option = ' '.join([f'/XF {file}' for file in keep_files])
                f.write(f"""@echo off
timeout /t 2 /nobreak >nul
echo 正在更新 GMStools... > "{log_file}" 2>&1
robocopy "{src}" "{dst}" /E {exclude_option} /R:1 /W:1 >> "{log_file}" 2>&1
if %errorlevel% geq 8 (
    echo 复制过程中出现错误，但将继续尝试启动程序。 >> "{log_file}" 2>&1
)
start "" "{install_dir}\\GMStools.exe"
del "%~f0"
rmdir /s /q "{self.temp_dir}"
""")
        else:  # Linux
            script_path = os.path.join(self.temp_dir, "update.sh")
            with open(script_path, 'w') as f:
                copy_cmd = f"""#!/bin/bash
exec > "{log_file}" 2>&1
echo "脚本开始执行于 $(date)"
echo "临时目录: {self.temp_dir}"
echo "新文件目录: {new_files_dir}"
echo "安装目录: {install_dir}"
echo "旧程序PID: {old_pid}"
sleep 2  # 给主程序退出留出时间

# 等待旧程序完全退出（避免单实例冲突）
if kill -0 {old_pid} 2>/dev/null; then
    echo "等待旧程序 (PID {old_pid}) 退出..."
    while kill -0 {old_pid} 2>/dev/null; do
        sleep 0.5
    done
    echo "旧程序已退出"
fi

# 额外等待一小段时间，确保文件句柄释放
sleep 1

cd "{new_files_dir}" || {{ echo "无法进入目录 {new_files_dir}"; exit 1; }}
echo "开始使用 tar 复制文件..."
tar cf - --exclude='config.ini' . | (cd "{install_dir}" && tar xf -)
TAR_EXIT=$?
echo "tar 退出码: $TAR_EXIT"

if [ $TAR_EXIT -eq 0 ]; then
    echo "文件复制成功。"
else
    echo "文件复制失败！"
    exit 1
fi

if [ -f "{install_dir}/GMStools" ]; then
    chmod +x "{install_dir}/GMStools"
    echo "已设置可执行权限。"
else
    echo "警告：未找到主程序文件 GMStools"
fi

# 创建独立的临时目录供新程序使用（避免 /tmp 冲突）
export TMPDIR="{install_dir}/tmp"
mkdir -p "$TMPDIR"
echo "设置 TMPDIR=$TMPDIR"

echo "启动新版本..."
env TMPDIR="{install_dir}/tmp" nohup "{install_dir}/GMStools" > "{app_log_file}" 2>&1 &
LAUNCH_PID=$!
echo "新程序启动PID: $LAUNCH_PID"

# 等待一会儿检查进程是否仍在运行
sleep 2
if kill -0 $LAUNCH_PID 2>/dev/null; then
    echo "新程序正在运行"
else
    echo "警告：新程序可能已退出"
    if [ -f "{app_log_file}" ]; then
        echo "应用日志内容:" >> "{log_file}"
        cat "{app_log_file}" >> "{log_file}"
    fi
fi

# 复制日志到安装目录
cp "{log_file}" "{install_dir}/update.log"

echo "日志已保存到 {install_dir}/update.log"
echo "脚本执行完毕，清理临时目录..."
rm -rf "{self.temp_dir}"
rm -- "$0"
"""
                f.write(copy_cmd)
            os.chmod(script_path, 0o755)

        # 确认脚本文件已成功创建
        if not os.path.exists(script_path):
            QMessageBox.critical(self, "错误", f"更新脚本未能创建: {script_path}")
            return

        # 弹出提示框，让用户选择手动或自动执行
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("更新准备就绪")
        msg_box.setText(
            f"更新脚本已生成，位于临时目录：\n{self.temp_dir}\n\n"
            f"您可以手动执行该目录下的 update.sh（Linux）或 update.bat（Windows）来调试。\n\n"
            f"点击“手动”将保持程序运行，您可以在终端中手动执行脚本；\n"
            f"点击“自动”将后台运行脚本并立即退出程序，更新完成后新程序将自动启动，日志将保存到安装目录。"
        )
        manual_btn = msg_box.addButton("手动", QMessageBox.ButtonRole.ActionRole)
        auto_btn = msg_box.addButton("自动", QMessageBox.ButtonRole.AcceptRole)
        msg_box.exec()

        if msg_box.clickedButton() == manual_btn:
            QMessageBox.information(self, "提示", f"请手动执行脚本：\n{script_path}\n\n执行后可在临时目录查看 update.log 和 app.log 日志。\n完成后可手动重启程序。")
            return
        else:
            # 自动模式：异步启动脚本，然后退出程序
            try:
                subprocess.Popen(['/bin/bash', script_path], start_new_session=True)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"启动更新脚本失败：{str(e)}")
                self.check_btn.setEnabled(True)
                self.check_btn.setText("检查更新")
                return

            # 提示用户并退出
            QMessageBox.information(self, "提示", "更新脚本已后台运行，程序将退出。新版本启动后请查看安装目录下的 update.log 了解详情。")
            QTimer.singleShot(1000, QApplication.quit)