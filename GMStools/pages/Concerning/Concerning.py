import json
import os
import webbrowser
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea,
    QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl, QStandardPaths
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

# 当前程序版本（请与 usekey.py 中的 APP_VERSION 保持一致）
APP_VERSION = "1.0.0"

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

        self.setup_ui()

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

        build_label = QLabel("构建版本：Release 1.0.240224")
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

        # ---------- 初始化网络管理器 ----------
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_update_check_finished)

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
            'download_url': version_info.get('download_url', ''),
            'release_notes': version_info.get('release_notes', '')
        }
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败：{e}")

    # ---------- 检查更新 ----------
    def check_for_updates(self):
        """检查更新：先读缓存，若无有效缓存则发起网络请求"""
        # 先尝试读取缓存
        cache = self._load_cache()
        if cache:
            self._show_update_dialog_from_cache(cache)
            return

        # 无有效缓存，发起网络请求
        self.check_btn.setEnabled(False)
        self.check_btn.setText("检查中...")

        url = QUrl(GITHUB_API_URL)
        request = QNetworkRequest(url)
        # 设置更通用的 User-Agent 避免被 GitHub 拒绝
        request.setHeader(
            QNetworkRequest.KnownHeaders.UserAgentHeader,
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.network_manager.get(request)

    def _show_update_dialog_from_cache(self, cache: Dict[str, Any]):
        """使用缓存数据展示更新对话框"""
        latest_version = cache.get('latest_version', '')
        download_url = cache.get('download_url', '')
        release_notes = cache.get('release_notes', '暂无更新说明')

        # 版本比较（简单字符串比较）
        if latest_version > APP_VERSION:
            msg = (f"发现新版本 {latest_version}（来自本地缓存）！\n\n"
                   f"更新内容：\n{release_notes}\n\n"
                   f"是否前往下载？")
            user_choice = QMessageBox.question(
                self,
                "发现新版本",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if user_choice == QMessageBox.StandardButton.Yes and download_url:
                webbrowser.open(download_url)
        else:
            # 提示“已是最新”，同时告知检查时间
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

    # ---------- 网络请求完成处理 ----------
    def on_update_check_finished(self, reply: QNetworkReply):
        """处理 GitHub API 响应"""
        self.check_btn.setEnabled(True)
        self.check_btn.setText("检查更新")

        # 获取 HTTP 状态码
        http_status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error_str = reply.errorString()

        # 首先检查网络层错误
        if reply.error() != QNetworkReply.NetworkError.NoError:
            # 处理限流错误（403）
            if http_status == 403:
                # 尝试读取返回内容，看是否包含 rate limit 信息
                response_data = reply.readAll().data()
                try:
                    error_info = json.loads(response_data.decode('utf-8'))
                    if "rate limit" in error_info.get("message", "").lower():
                        QMessageBox.warning(
                            self,
                            "检查更新",
                            "GitHub API 访问次数已达上限（每小时60次），请稍后再试。\n"
                            "您也可以直接访问我们的 Releases 页面查看最新版本：\n"
                            "https://github.com/huguangyin1997-collab/GMStools/releases"
                        )
                        reply.deleteLater()
                        return
                except:
                    pass

            # 处理 404 Not Found（仓库没有 Release）
            if http_status == 404:
                QMessageBox.information(
                    self,
                    "检查更新",
                    "GitHub 仓库中尚未发布任何版本。\n"
                    "您可以访问 Releases 页面关注后续更新：\n"
                    "https://github.com/huguangyin1997-collab/GMStools/releases"
                )
                reply.deleteLater()
                return

            # 其他网络错误
            QMessageBox.warning(
                self,
                "检查失败",
                f"网络错误 (HTTP {http_status}): {error_str}\n\n请检查网络连接或稍后重试。"
            )
            reply.deleteLater()
            return

        # 读取响应数据
        data = reply.readAll().data()
        reply.deleteLater()

        try:
            info = json.loads(data.decode('utf-8'))

            # 从 API 响应中提取信息
            latest_tag = info.get("tag_name", "")
            if not latest_tag:
                QMessageBox.warning(self, "解析失败", "未能获取到版本信息。")
                return

            latest_version = latest_tag.lstrip('v')  # 去除可能的 v 前缀
            release_notes = info.get("body", "暂无更新说明")

            # 获取下载链接：优先查找 Windows 可执行文件（.exe）
            download_url = ""
            assets = info.get("assets", [])
            for asset in assets:
                name = asset.get("name", "")
                if name.endswith(".exe") or "windows" in name.lower():
                    download_url = asset.get("browser_download_url", "")
                    break
            if not download_url:
                download_url = info.get("html_url", "")  # 退回到 Releases 页面

            # 保存到缓存
            self._save_cache({
                'latest_version': latest_version,
                'download_url': download_url,
                'release_notes': release_notes
            })

            # 版本比较（简单字符串比较，如需精确比较请安装 packaging 库）
            if latest_version > APP_VERSION:
                msg = (f"发现新版本 {latest_version}！\n\n"
                       f"更新内容：\n{release_notes}\n\n"
                       f"是否前往下载？")
                user_choice = QMessageBox.question(
                    self,
                    "发现新版本",
                    msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if user_choice == QMessageBox.StandardButton.Yes and download_url:
                    webbrowser.open(download_url)
            else:
                QMessageBox.information(self, "检查更新", "当前已是最新版本。")

        except json.JSONDecodeError:
            QMessageBox.warning(self, "解析失败", "服务器返回的数据格式错误。")
        except Exception as e:
            QMessageBox.warning(self, "解析失败", f"版本信息解析出错：{str(e)}")