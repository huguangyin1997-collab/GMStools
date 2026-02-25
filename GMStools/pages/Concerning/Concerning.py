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
from PyQt6.QtCore import Qt, QUrl, QStandardPaths
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

# ==================== 当前程序版本（与 GitHub Release 标签一致）====================

APP_VERSION = "1.2.3"

# GitHub API 地址（最新 Release）
GITHUB_API_URL = "https://api.github.com/repos/huguangyin1997-collab/GMStools/releases/latest"

# 缓存文件名（存放在用户数据目录）
CACHE_FILE = "version_cache.json"


class Concerning(QWidget):
    """关于开发页面（带滚动区域）"""

    def __init__(self):
        super().__init__()
        # 获取应用程序数据目录（用于存放缓存文件）
        self.app_data_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppLocalDataLocation
        )
        if not os.path.exists(self.app_data_dir):
            os.makedirs(self.app_data_dir)
        self.cache_path = os.path.join(self.app_data_dir, CACHE_FILE)

        # ---------- 网络管理器（分离版本检查与下载）----------
        # 用于版本检查（返回 JSON）
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_update_check_finished)

        # 用于下载更新包（返回二进制文件）
        self.download_manager = QNetworkAccessManager()
        self.download_manager.finished.connect(self.on_download_finished)

        # 下载相关的临时变量
        self.download_reply = None
        self.temp_dir = None
        self.download_path = None
        self.expected_sha256 = None   # 用于在下载回调中保存期望的 SHA256

        self.setup_ui()

    # ---------- UI 构建（保持不变，与之前完全相同）----------
    def setup_ui(self):
        # 主布局：将整个页面设置为一个滚动区域
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(0)
        main_layout.addWidget(scroll)

        # 内容容器
        content = QWidget()
        scroll.setWidget(content)

        # 内容容器的布局
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # ---------- 标题 ----------
        title = QLabel("关于 GMStools")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            padding: 15px;
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # ---------- 版本信息卡片 ----------
        version_card = QWidget()
        version_card.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.7);
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            padding: 15px;
        """)
        version_layout = QVBoxLayout(version_card)

        version_title = QLabel("版本信息")
        version_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        version_layout.addWidget(version_title)

        self.version_label = QLabel(f"当前版本：{APP_VERSION}")
        self.version_label.setStyleSheet("font-size: 14px; color: #34495e;")
        version_layout.addWidget(self.version_label)

        build_label = QLabel("构建版本：Release 1.2.2")
        build_label.setStyleSheet("font-size: 14px; color: #34495e;")
        version_layout.addWidget(build_label)

        # 检查更新按钮行
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        self.check_btn = QPushButton("检查更新")
        self.check_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #216694;
            }
        """)
        self.check_btn.clicked.connect(self.check_for_updates)
        button_layout.addStretch()
        button_layout.addWidget(self.check_btn)
        button_layout.addStretch()

        version_layout.addLayout(button_layout)
        layout.addWidget(version_card)

        # ---------- 开发者信息卡片 ----------
        developer_card = QWidget()
        developer_card.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.7);
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            padding: 15px;
        """)
        dev_layout = QVBoxLayout(developer_card)
        dev_title = QLabel("开发团队")
        dev_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        dev_layout.addWidget(dev_title)
        dev_info = QLabel(
            "主程序：GMStools 开发组<br>"
            "贡献者：Huguangyin<br>"
            "特别感谢：所有测试用户"
        )
        dev_info.setTextFormat(Qt.TextFormat.RichText)
        dev_info.setStyleSheet("font-size: 14px; color: #34495e; line-height: 1.6;")
        dev_layout.addWidget(dev_info)
        layout.addWidget(developer_card)

        # ---------- 联系与支持卡片 ----------
        contact_card = QWidget()
        contact_card.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.7);
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            padding: 15px;
        """)
        contact_layout = QVBoxLayout(contact_card)
        contact_title = QLabel("联系与支持")
        contact_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        contact_layout.addWidget(contact_title)
        contact_info = QLabel(
            "邮箱：1737660582@qq.com<br>"
            "电话：18334185042<br>"
            "github：https://github.com/huguangyin1997-collab/GMStools.git<br>"
            "问题反馈：请邮箱或 GitHub "
        )
        contact_info.setTextFormat(Qt.TextFormat.RichText)
        contact_info.setStyleSheet("font-size: 14px; color: #34495e; line-height: 1.6;")
        contact_layout.addWidget(contact_info)
        layout.addWidget(contact_card)

        # ---------- 版权信息卡片 ----------
        copyright_card = QWidget()
        copyright_card.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.7);
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            padding: 15px;
        """)
        copyright_layout = QVBoxLayout(copyright_card)
        copyright_title = QLabel("版权声明")
        copyright_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        copyright_layout.addWidget(copyright_title)
        copyright_text = QLabel(
            "© 2026 GMStools 开发组。保留所有权利。<br>"
            "本软件按“原样”提供，详情请参阅免责声明。"
        )
        copyright_text.setTextFormat(Qt.TextFormat.RichText)
        copyright_text.setStyleSheet("font-size: 14px; color: #34495e; line-height: 1.6;")
        copyright_layout.addWidget(copyright_text)
        layout.addWidget(copyright_card)

    # ---------- 缓存读写方法 ----------
    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """读取本地缓存，如果缓存有效（1小时内）则返回数据，否则返回 None"""
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
        """保存版本信息到缓存"""
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
        """检查更新：先读缓存，若无有效缓存则发起网络请求"""
        cache = self._load_cache()
        if cache:
            latest_version = cache.get('latest_version', '')
            release_notes = cache.get('release_notes', '')
            if latest_version > APP_VERSION:
                msg = (f"可能发现新版本 {latest_version}（来自本地缓存）！\n"
                       f"更新内容：\n{release_notes}\n\n"
                       f"是否联网检查最新版本？")
                user_choice = QMessageBox.question(
                    self,
                    "发现新版本",
                    msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if user_choice == QMessageBox.StandardButton.No:
                    return
            else:
                check_time = cache.get('check_time', '')
                if check_time:
                    try:
                        dt = datetime.fromisoformat(check_time)
                        time_str = dt.strftime("%Y-%m-%d %H:%M")
                        msg = f"当前已是最新版本（上次检查：{time_str}）"
                    except:
                        msg = "当前已是最新版本。"
                else:
                    msg = "当前已是最新版本。"
                QMessageBox.information(self, "检查更新", msg)
                return

        # 无有效缓存或用户选择联网，发起网络请求
        self.check_btn.setEnabled(False)
        self.check_btn.setText("检查中...")

        url = QUrl(GITHUB_API_URL)
        request = QNetworkRequest(url)
        request.setHeader(
            QNetworkRequest.KnownHeaders.UserAgentHeader,
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.network_manager.get(request)

    # ---------- 版本检查响应处理 ----------
    def on_update_check_finished(self, reply: QNetworkReply):
        """处理 GitHub API 响应（版本检查）"""
        self.check_btn.setEnabled(True)
        self.check_btn.setText("检查更新")

        http_status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error_str = reply.errorString()

        if reply.error() != QNetworkReply.NetworkError.NoError:
            self._handle_network_error(reply, http_status, error_str)
            reply.deleteLater()
            return

        data = reply.readAll().data()
        reply.deleteLater()

        # 安全解码
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

            # 保存到缓存
            self._save_cache({
                'latest_version': latest_version,
                'release_notes': release_notes
            })

            if latest_version <= APP_VERSION:
                QMessageBox.information(self, "检查更新", "当前已是最新版本。")
                return

            # 根据平台选择对应的 asset
            is_windows = sys.platform == "win32"
            target_asset = None
            for asset in assets:
                name = asset.get("name", "").lower()
                if is_windows and ("windows" in name or name.endswith(".exe")):
                    target_asset = asset
                    break
                elif not is_windows and "linux" in name:
                    target_asset = asset
                    break

            if not target_asset:
                QMessageBox.warning(
                    self,
                    "检查更新",
                    f"发现新版本 {latest_version}，但未找到适合当前平台的更新包。\n"
                    f"请手动访问 Releases 页面下载：\n"
                    f"https://github.com/huguangyin1997-collab/GMStools/releases"
                )
                return

            # 询问用户是否下载
            msg = (f"发现新版本 {latest_version}！\n\n"
                   f"更新内容：\n{release_notes}\n\n"
                   f"是否立即下载并安装更新？")
            user_choice = QMessageBox.question(
                self,
                "发现新版本",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if user_choice == QMessageBox.StandardButton.Yes:
                self.download_update(target_asset)

        except json.JSONDecodeError:
            self._show_response_error(f"服务器返回的不是有效的 JSON。\n返回内容预览：{text[:500]}")
        except Exception as e:
            QMessageBox.warning(self, "解析失败", f"版本信息处理出错：{str(e)}")

    def _handle_network_error(self, reply, http_status, error_str):
        """处理网络错误"""
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
                    QMessageBox.warning(
                        self,
                        "检查更新",
                        "GitHub API 访问次数已达上限（每小时60次），请稍后再试。\n"
                        "您也可以直接访问 Releases 页面查看最新版本：\n"
                        "https://github.com/huguangyin1997-collab/GMStools/releases"
                    )
                    return
            except:
                pass
            QMessageBox.warning(
                self,
                "检查更新",
                f"访问被拒绝 (HTTP 403)。请稍后重试，或检查网络设置。\n响应预览：{response_text[:200]}"
            )
        elif http_status == 404:
            QMessageBox.information(
                self,
                "检查更新",
                "GitHub 仓库中尚未发布任何版本。\n"
                "您可以访问 Releases 页面关注后续更新：\n"
                "https://github.com/huguangyin1997-collab/GMStools/releases"
            )
        else:
            QMessageBox.warning(
                self,
                "检查失败",
                f"网络错误 (HTTP {http_status}): {error_str}\n\n响应预览：{response_text[:200]}"
            )

    def _show_response_error(self, details: str):
        """显示详细的响应错误对话框"""
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
        """开始下载更新包（使用独立的下载管理器）"""
        url = asset_info['browser_download_url']
        # 提取 SHA256
        expected_sha256 = asset_info.get('digest', '')
        if expected_sha256.startswith('sha256:'):
            expected_sha256 = expected_sha256[7:]

        # 保存期望的哈希值，供下载回调使用
        self.expected_sha256 = expected_sha256

        self.check_btn.setEnabled(False)
        self.check_btn.setText("下载更新中...")

        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="gmstools_update_")
        self.download_path = os.path.join(self.temp_dir, asset_info['name'])

        # 发起下载请求（使用专用的下载管理器）
        request = QNetworkRequest(QUrl(url))
        # 告诉 GitHub 我们想要文件，而不是 HTML 页面
        request.setRawHeader(b"Accept", b"application/octet-stream")
        self.download_reply = self.download_manager.get(request)
        self.download_reply.downloadProgress.connect(self.on_download_progress)

    def on_download_progress(self, bytes_received, bytes_total):
        """下载进度更新"""
        if bytes_total > 0:
            percent = int(bytes_received * 100 / bytes_total)
            self.check_btn.setText(f"下载中 {percent}%")
        else:
            self.check_btn.setText(f"下载中 {bytes_received/1024:.0f}KB")

    def on_download_finished(self):
        """下载完成回调（独立下载管理器专用）"""
        expected_sha256 = self.expected_sha256
        if not self.download_reply:
            return

        # 检查网络错误
        if self.download_reply.error() != QNetworkReply.NetworkError.NoError:
            QMessageBox.critical(self, "下载失败", f"网络错误：{self.download_reply.errorString()}")
            self._cleanup_temp()
            return

        # 检查 HTTP 状态码
        http_status = self.download_reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if http_status != 200:
            error_data = self.download_reply.readAll().data()
            error_text = error_data.decode('utf-8', errors='replace')[:500]
            QMessageBox.critical(
                self,
                "下载失败",
                f"HTTP 状态码 {http_status}，期望 200。\n响应预览：\n{error_text}"
            )
            self._cleanup_temp()
            return

        # 保存文件
        with open(self.download_path, 'wb') as f:
            f.write(self.download_reply.readAll().data())

        # 验证 ZIP 头（魔数 PK）
        with open(self.download_path, 'rb') as f:
            header = f.read(2)
        if header != b'PK':
            QMessageBox.critical(
                self,
                "文件错误",
                "下载的文件不是有效的 ZIP 格式，可能为 HTML 错误页。"
            )
            self._cleanup_temp()
            return

        # 验证 SHA256
        if expected_sha256:
            sha256_hash = hashlib.sha256()
            with open(self.download_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            actual_hash = sha256_hash.hexdigest()
            if actual_hash != expected_sha256:
                QMessageBox.critical(
                    self,
                    "校验失败",
                    f"文件校验和不匹配！\n期望：{expected_sha256}\n实际：{actual_hash}\n\n更新取消。"
                )
                self._cleanup_temp()
                return

        # 解压到临时子目录
        extract_to = os.path.join(self.temp_dir, "new_version")
        os.makedirs(extract_to, exist_ok=True)
        try:
            with zipfile.ZipFile(self.download_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        except Exception as e:
            QMessageBox.critical(self, "解压失败", f"解压更新包失败：{str(e)}")
            self._cleanup_temp()
            return

        # 执行更新
        self.perform_update(extract_to)
        self._cleanup_temp()  # 清理（脚本也会清理，这里双重保险）

    def _cleanup_temp(self):
        """清理临时目录和变量"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.temp_dir = None
        self.download_path = None
        self.expected_sha256 = None
        self.download_reply = None

    # ---------- 核心更新逻辑 ----------
    def perform_update(self, new_files_dir):
        """
        执行更新：生成更新脚本，替换文件，重启程序
        new_files_dir: 解压后的新文件所在目录
        """
        # 获取当前程序所在目录（安装目录）
        if getattr(sys, 'frozen', False):
            install_dir = os.path.dirname(sys.executable)
        else:
            install_dir = os.path.dirname(os.path.abspath(__file__))

        is_windows = sys.platform == "win32"
        # 需要保留的配置文件（不覆盖）
        keep_files = ['config.ini']

        # 生成更新脚本
        if is_windows:
            script_path = os.path.join(self.temp_dir, "update.bat")
            with open(script_path, 'w') as f:
                f.write(f"""@echo off
timeout /t 2 /nobreak >nul
echo 正在更新 GMStools...
xcopy /y /e "{new_files_dir}" "{install_dir}" >nul
start "" "{install_dir}\\GMStools.exe"
del "%~f0"
rmdir /s /q "{self.temp_dir}"
""")
        else:  # Linux
            script_path = os.path.join(self.temp_dir, "update.sh")
            with open(script_path, 'w') as f:
                # 生成 shell 脚本，跳过保留文件
                copy_cmd = f"""#!/bin/bash
sleep 2
echo "正在更新 GMStools..."
# 复制所有文件，跳过保留的配置文件
for file in "{new_files_dir}"/*; do
    base=$(basename "$file")
    if [[ " {','.join(keep_files)} " != *" $base "* ]]; then
        cp -rf "$file" "{install_dir}/"
    fi
done
# 确保主程序可执行
chmod +x "{install_dir}/GMStools"
# 启动新程序
"{install_dir}/GMStools" &
# 清理临时目录
rm -rf "{self.temp_dir}"
rm -- "$0"
"""
                f.write(copy_cmd)
            os.chmod(script_path, 0o755)

        # 执行更新脚本并退出当前程序
        subprocess.Popen([script_path], shell=True, cwd=self.temp_dir)
        QApplication.quit()