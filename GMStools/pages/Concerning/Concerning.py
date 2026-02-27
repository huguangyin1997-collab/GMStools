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
    QPushButton, QHBoxLayout, QApplication,
    QTextEdit, QDialog, QVBoxLayout as QVBoxLayoutDlg,
    QDialog, QPushButton, QLabel, QHBoxLayout, QVBoxLayout,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl, QStandardPaths, QTimer, QPoint
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QColor, QMouseEvent
from CustomTitle.titleWindowControlButtons import WindowControlButtons

# ==================== 当前程序版本 ====================
APP_VERSION = "1.2.9"

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


class MikuDialog(QDialog):
    def __init__(self, parent=None, title="提示", message="", buttons=QMessageBox.StandardButton.Ok):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setMinimumSize(400, 200)

        # 加载背景图片
        img_path = self.get_resource_path("Miku.jpg")
        self.bg_pixmap = QPixmap(img_path)
        if self.bg_pixmap.isNull():
            self.bg_pixmap = QPixmap(400, 200)
            self.bg_pixmap.fill(Qt.GlobalColor.darkCyan)

        self.update_background()
        self.setup_ui(title, message, buttons)
        self.drag_position = None

    def get_resource_path(self, relative_path: str) -> str:
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base, relative_path)

    def update_background(self):
        if not hasattr(self, 'bg_pixmap') or self.bg_pixmap.isNull():
            return
        scaled = self.bg_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        if scaled.width() > self.width() or scaled.height() > self.height():
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            scaled = scaled.copy(x, y, self.width(), self.height())
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_background()

    def setup_ui(self, title, message, buttons):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏（透明）
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(44)
        self.title_bar.setStyleSheet("background-color: transparent;")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(12, 0, 12, 0)
        title_layout.setSpacing(0)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #000000;
                font-size: 18px;
                font-weight: 900;
                font-family: "Microsoft YaHei", "Segoe UI";
                padding: 0 6px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        self.control_buttons = WindowControlButtons()
        self.control_buttons.minimize_signal.connect(self.showMinimized)
        self.control_buttons.maximize_signal.connect(self.toggle_maximize)
        self.control_buttons.close_signal.connect(self.reject)
        title_layout.addWidget(self.control_buttons)
        main_layout.addWidget(self.title_bar)

        # 内容区域
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # 消息标签
        self.label = QLabel(message)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: black;
                font-weight: bold;
                background-color: rgba(255, 255, 255, 0.8);
                padding: 15px;
                border-radius: 8px;
                font-size: 14px;
            }
        """)
        content_layout.addWidget(self.label)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 创建按钮并设置唯一对象名
        if buttons & QMessageBox.StandardButton.Ok:
            btn = QPushButton("确定")
            btn.setObjectName("okBtn")
            btn.clicked.connect(lambda: self.done(QMessageBox.StandardButton.Ok))
            self._apply_button_style(btn)
            button_layout.addWidget(btn)

        if buttons & QMessageBox.StandardButton.Yes:
            btn = QPushButton("是")
            btn.setObjectName("yesBtn")
            btn.clicked.connect(lambda: self.done(QMessageBox.StandardButton.Yes))
            self._apply_button_style(btn)
            button_layout.addWidget(btn)

        if buttons & QMessageBox.StandardButton.No:
            btn = QPushButton("否")
            btn.setObjectName("noBtn")
            btn.clicked.connect(lambda: self.done(QMessageBox.StandardButton.No))
            self._apply_button_style(btn)
            button_layout.addWidget(btn)

        if buttons & QMessageBox.StandardButton.Cancel:
            btn = QPushButton("取消")
            btn.setObjectName("cancelBtn")
            btn.clicked.connect(lambda: self.done(QMessageBox.StandardButton.Cancel))
            self._apply_button_style(btn)
            button_layout.addWidget(btn)

        button_layout.addStretch()
        content_layout.addLayout(button_layout)
        main_layout.addWidget(content_widget)

    def _apply_button_style(self, btn):
        """为按钮应用统一样式（对象名选择器 + !important）"""
        # 使用对象名选择器提高优先级，避免被全局样式覆盖
        style = """
            QPushButton#okBtn, QPushButton#yesBtn, QPushButton#noBtn, QPushButton#cancelBtn {
                text-align: center;
                padding: 8px 16px;
                border: 2px solid #bdc3c7;
                color: white;
                background-color: #3498db !important;
                font-size: 14px;
                font-weight: bold;
                border-radius: 15px;          /* 一点圆角 */
                min-width: 120px;
                min-height: 30px;
                margin: 0px;
            }
            QPushButton#okBtn:hover, QPushButton#yesBtn:hover, QPushButton#noBtn:hover, QPushButton#cancelBtn:hover {
                color: red;
                background-color: #27ae60 !important;  /* 悬停背景不变，文字变红 */
                border: 2px solid #bdc3c7;
            }
            QPushButton#okBtn:pressed, QPushButton#yesBtn:pressed, QPushButton#noBtn:pressed, QPushButton#cancelBtn:pressed {
                color: red;
                background-color: #16d8de !important;  /* 按下背景变深蓝 */
            }
        """
        btn.setStyleSheet(style)
        btn.setAutoFillBackground(True)
        btn.setFlat(False)
        # print(f"[MikuDialog] 按钮 '{btn.text()}' 样式已应用。")

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.title_bar.geometry().contains(event.pos()):
            window = self.window()
            if window and window.windowHandle():
                window.windowHandle().startSystemMove()
            event.accept()
        else:
            super().mousePressEvent(event)


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

        # 启动后1分钟删除更新日志（如果存在）
        self.schedule_delete_update_log()

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
                dlg = MikuDialog(self, "提示", f"本地缓存提示有新版本 {latest_version}，正在联网确认...", QMessageBox.StandardButton.Ok)
                dlg.exec()
            else:
                dlg = MikuDialog(self, "提示", "正在联网检查最新版本...", QMessageBox.StandardButton.Ok)
                dlg.exec()

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
                dlg = MikuDialog(self, "检查更新", "当前已是最新版本。", QMessageBox.StandardButton.Ok)
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
                dlg = MikuDialog(self, "提示", "未找到明确匹配当前平台的更新包，将使用第一个附件，请确保其适用于您的系统。", QMessageBox.StandardButton.Ok)
                dlg.exec()

            if not target_asset:
                dlg = MikuDialog(self, "检查更新", f"发现新版本 {latest_version}，但未找到任何更新包。\n请手动访问 Releases 页面下载：\nhttps://github.com/huguangyin1997-collab/GMStools/releases", QMessageBox.StandardButton.Ok)
                dlg.exec()
                return

            msg = (f"发现新版本 {latest_version}！\n\n更新内容：\n{release_notes}\n\n是否立即下载并安装更新？")
            dlg = MikuDialog(self, "发现新版本", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if dlg.exec() == QMessageBox.StandardButton.Yes:
                self.download_update(target_asset)

        except json.JSONDecodeError:
            self._show_response_error(f"服务器返回的不是有效的 JSON。\n返回内容预览：{text[:500]}")
        except Exception as e:
            dlg = MikuDialog(self, "解析失败", f"版本信息处理出错：{str(e)}", QMessageBox.StandardButton.Ok)
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
                    dlg = MikuDialog(self, "检查更新", "GitHub API 访问次数已达上限（每小时60次），请稍后再试。\n您也可以直接访问 Releases 页面查看最新版本。", QMessageBox.StandardButton.Ok)
                    dlg.exec()
                    return
            except:
                pass
            dlg = MikuDialog(self, "检查更新", f"访问被拒绝 (HTTP 403)。请稍后重试。\n响应预览：{response_text[:200]}", QMessageBox.StandardButton.Ok)
            dlg.exec()
        elif http_status == 404:
            dlg = MikuDialog(self, "检查更新", "GitHub 仓库中尚未发布任何版本。\n请访问 Releases 页面关注后续更新。", QMessageBox.StandardButton.Ok)
            dlg.exec()
        else:
            dlg = MikuDialog(self, "检查失败", f"网络错误 (HTTP {http_status}): {error_str}\n\n响应预览：{response_text[:200]}", QMessageBox.StandardButton.Ok)
            dlg.exec()

    def _show_response_error(self, details: str):
        dlg = MikuDialog(self, "响应内容异常", details, QMessageBox.StandardButton.Ok)
        dlg.resize(600, 400)
        dlg.exec()

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
                dlg = MikuDialog(self, "校验成功", "文件完整性验证通过。", QMessageBox.StandardButton.Ok)
                dlg.exec()

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

    # ---------- 核心更新逻辑（双平台最终版）----------
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
            # Windows 全自动更新（完整复制 + 环境清理 + 进程终止 + 日志保存）
            log_file = os.path.join(self.temp_dir, "update.log")
            script_path = os.path.join(self.temp_dir, "update.bat")
            with open(script_path, 'w') as f:
                src = new_files_dir.replace('/', '\\')
                dst = install_dir.replace('/', '\\')
                exclude_option = ' '.join([f'/XF {file}' for file in keep_files])
                f.write(f"""@echo off
setlocal enabledelayedexpansion
echo %DATE% %TIME% 开始更新 > "{log_file}" 2>&1

:: 记录当前环境变量（用于诊断）
echo %DATE% %TIME% 当前环境变量: >> "{log_file}" 2>&1
set >> "{log_file}" 2>&1

:: 强制结束所有相关进程（避免文件占用和环境残留）
echo %DATE% %TIME% 强制结束所有 GMStools.exe 进程... >> "{log_file}" 2>&1
taskkill /f /im GMStools.exe >> "{log_file}" 2>&1 2>&1
echo %DATE% %TIME% 强制结束所有 adb.exe 进程... >> "{log_file}" 2>&1
taskkill /f /im adb.exe >> "{log_file}" 2>&1 2>&1

:: 等待进程完全退出
timeout /t 2 /nobreak >nul

:: 复制新文件（使用 /MIR 确保目标与源完全一致）
echo %DATE% %TIME% 开始复制文件从 "{src}" 到 "{dst}" >> "{log_file}" 2>&1
robocopy "{src}" "{dst}" /MIR {exclude_option} /R:3 /W:3 /NP /NDL /NFL /LOG+:"{log_file}"
set COPY_RESULT=%errorlevel%
echo %DATE% %TIME% robocopy 返回码: !COPY_RESULT! >> "{log_file}" 2>&1
:: 返回码大于7表示有错误，但大于等于8才表示严重错误
if !COPY_RESULT! geq 8 (
    echo %DATE% %TIME% 复制过程中出现严重错误，将继续尝试启动程序。 >> "{log_file}" 2>&1
)

:: 列出目标目录内容以便验证
echo %DATE% %TIME% 目标目录内容: >> "{log_file}" 2>&1
dir "{dst}" /s /b >> "{log_file}" 2>&1

:: 清理系统临时目录下的所有旧解压目录（避免加载错误的DLL）
echo %DATE% %TIME% 清理旧解压目录... >> "{log_file}" 2>&1
if exist "%TEMP%\\_MEI*" (
    echo 删除 %TEMP%\\_MEI* >> "{log_file}" 2>&1
    del /f /s /q "%TEMP%\\_MEI*" >nul 2>&1
    rmdir /s /q "%TEMP%\\_MEI*" >nul 2>&1
)
if exist "%LOCALAPPDATA%\\Temp\\_MEI*" (
    echo 删除 %LOCALAPPDATA%\\Temp\\_MEI* >> "{log_file}" 2>&1
    del /f /s /q "%LOCALAPPDATA%\\Temp\\_MEI*" >nul 2>&1
    rmdir /s /q "%LOCALAPPDATA%\\Temp\\_MEI*" >nul 2>&1
)

:: 清除可能干扰的环境变量
set _MEIPASS=
set PYTHONHOME=
set PYTHONPATH=
set TMP=%USERPROFILE%\\AppData\\Local\\Temp
set TEMP=%USERPROFILE%\\AppData\\Local\\Temp

:: 启动新程序（使用 /B 后台启动，并重定向所有输出）
set "EXE={install_dir}\\GMStools.exe"
echo %DATE% %TIME% 启动新版本: !EXE! >> "{log_file}" 2>&1
start /B "" "!EXE!" >nul 2>&1

:: 等待新程序初始化（给足时间解压和启动）
echo %DATE% %TIME% 等待 15 秒让新程序初始化... >> "{log_file}" 2>&1
timeout /t 15 /nobreak >nul

:: 检查新程序是否仍在运行
tasklist /fi "imagename eq GMStools.exe" >> "{log_file}" 2>&1

:: 复制日志到安装目录
copy "{log_file}" "{install_dir}\\update.log" /Y

:: 清理临时目录
echo %DATE% %TIME% 清理临时目录: {self.temp_dir} >> "{log_file}" 2>&1
rmdir /s /q "{self.temp_dir}" 2>> "{log_file}"
del "%~f0"
""")
            # 显示自定义对话框（带 Miku 背景）
            try:
                dlg = MikuDialog(self, "提示", "更新脚本即将运行，程序将退出。新版本将自动启动。", QMessageBox.StandardButton.Ok)
                if dlg.exec() == QMessageBox.StandardButton.Ok:
                    # 使用 PowerShell 无窗口启动批处理
                    ps_command = f'Start-Process cmd -ArgumentList "/c {script_path}" -WindowStyle Hidden'
                    subprocess.Popen(
                        ['powershell', '-Command', ps_command],
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    QApplication.quit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"启动更新脚本失败：{str(e)}")
        else:
            # Linux 自动更新（干净环境启动）
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

# 等待旧程序完全退出
if kill -0 {old_pid} 2>/dev/null; then
    echo "等待旧程序 (PID {old_pid}) 退出..."
    while kill -0 {old_pid} 2>/dev/null; do
        sleep 0.5
    done
    echo "旧程序已退出"
fi
sleep 1

# 复制新文件到安装目录（排除 config.ini）
cd "{new_files_dir}" || {{ echo "无法进入目录 {new_files_dir}"; exit 1; }}
echo "开始复制文件..."
for item in *; do
    if [[ "$item" == "config.ini" ]]; then
        continue
    fi
    echo "复制 $item 到 {install_dir}/"
    cp -rf "$item" "{install_dir}/"
done

# 设置可执行权限
if [ -f "{install_dir}/GMStools" ]; then
    chmod +x "{install_dir}/GMStools"
    echo "已设置可执行权限"
fi

# 切换到安装目录
cd "{install_dir}"

# 清理可能存在的旧解压目录
echo "清理旧解压目录..."
rm -rf /tmp/_MEI* "$TMPDIR"/_MEI* 2>/dev/null

# 使用干净环境启动新程序
echo "启动新版本（干净环境）..."
env -i DISPLAY="{display}" XAUTHORITY="{xauthority}" DBUS_SESSION_BUS_ADDRESS="{dbus}" XDG_RUNTIME_DIR="{xdg_runtime}" HOME="{home}" USER="{user}" PATH="{path}" LANG="{lang}" ./GMStools > "{app_log_file}" 2>&1 &
LAUNCH_PID=$!
echo "新程序启动PID: $LAUNCH_PID"

# 等待几秒检查解压目录
sleep 5
if [ -d /tmp/_MEI* ] || [ -d "$TMPDIR"/_MEI* ]; then
    echo "解压目录已创建，启动成功"
else
    echo "警告：未发现解压目录，可能启动失败"
    echo "应用日志："
    cat "{app_log_file}"
fi

# 复制日志到安装目录
cp "{log_file}" "{install_dir}/update.log"
echo "日志已保存到 {install_dir}/update.log"

# 清理临时目录
rm -rf "{self.temp_dir}"
rm -- "$0"
""")
            os.chmod(script_path, 0o755)

            try:
                dlg = MikuDialog(self, "提示", "更新脚本即将运行，程序将退出。新版本将自动启动。", QMessageBox.StandardButton.Ok)
                if dlg.exec() == QMessageBox.StandardButton.Ok:
                    subprocess.Popen(['/bin/bash', script_path], start_new_session=True)
                    QApplication.quit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"启动更新脚本失败：{str(e)}")

    # ---------- 自动删除更新日志 ----------
    def schedule_delete_update_log(self):
        """检查安装目录下的 update.log，1分钟后删除"""
        if getattr(sys, 'frozen', False):
            install_dir = os.path.dirname(sys.executable)
        else:
            install_dir = os.path.dirname(os.path.abspath(__file__))  # 与 perform_update 保持一致
        log_path = os.path.join(install_dir, "update.log")
        if os.path.exists(log_path):
            print(f"[Concerning] 发现更新日志 {log_path}，1分钟后删除")
            QTimer.singleShot(60000, lambda: self.delete_update_log(log_path))

    def delete_update_log(self, log_path):
        """删除指定的日志文件"""
        try:
            os.remove(log_path)
            print(f"[Concerning] 已删除更新日志: {log_path}")
        except Exception as e:
            print(f"[Concerning] 删除更新日志失败: {e}")