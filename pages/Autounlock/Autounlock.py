import html
import os
import threading
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSizePolicy, QLineEdit, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, QEvent
from ..Ctsverifierdb.device_manager import DeviceManager
from .utils import _get_fastboot_path, _get_unlock_dir, _run_command
from .runner import UnlockSignals, UnlockRunner
from .dialogs import show_styled_message
from .device_panel import DeviceListPopup, build_device_panels, get_fastboot_devices


class Autounlock(QWidget):
    def __init__(self):
        super().__init__()
        self.device_manager = DeviceManager()
        self.selected_devices = []
        self.all_devices = []
        self._active_workers = []
        self._device_logs = {}
        self._device_log_buffers = {}
        self._device_log_files = {}   # device_sn -> open file handle (session-scoped)
        self._device_log_paths = {}   # device_sn -> file path

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setup_ui()
        self.update_device_button_text()
        QTimer.singleShot(500, self.delayed_adb_check)

    def delayed_adb_check(self):
        self.device_manager.check_adb_environment(self.refresh_device_list, self.show_adb_error)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ---------- 第一行：设备选择区 ----------
        device_layout = QHBoxLayout()
        device_layout.setSpacing(6)

        self.device_btn = QPushButton("未选择设备")
        self.device_btn.setFixedHeight(36)
        self.device_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.device_btn.clicked.connect(self.show_device_list)
        device_layout.addWidget(self.device_btn)

        self.refresh_btn = QPushButton("刷新设备")
        self.refresh_btn.setFixedSize(140, 36)
        self.refresh_btn.setStyleSheet(self.get_button_style())
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        device_layout.addWidget(self.refresh_btn)

        self.clear_btn = QPushButton("清除记录")
        self.clear_btn.setFixedSize(140, 36)
        self.clear_btn.setStyleSheet(self.get_button_style())
        self.clear_btn.clicked.connect(self.on_clear_records)
        device_layout.addWidget(self.clear_btn)

        layout.addLayout(device_layout)

        # ---------- 第二行：文件选择框 + 镜像按钮 ----------
        file_layout = QHBoxLayout()
        file_layout.setSpacing(6)

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setFixedHeight(36)
        self.file_path_edit.setPlaceholderText("未选择文件...")
        self.file_path_edit.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid #4A90D9;
                padding: 5px 12px;
                color: #333;
                font-size: 14px;
                border-radius: 0px;
            }
            QLineEdit:hover {
                background-color: rgba(255, 255, 255, 180);
            }
        """)
        file_layout.addWidget(self.file_path_edit)

        self.btn_unlock_file = QPushButton("展讯解锁文件")
        self.btn_unlock_file.setFixedSize(140, 36)
        self.btn_unlock_file.setStyleSheet(self.get_button_style())
        self.btn_unlock_file.clicked.connect(lambda: self.select_file("展讯解锁文件 (*.pem)"))
        file_layout.addWidget(self.btn_unlock_file)

        self.btn_system_img = QPushButton("system镜像")
        self.btn_system_img.setFixedSize(140, 36)
        self.btn_system_img.setStyleSheet(self.get_button_style())
        self.btn_system_img.clicked.connect(lambda: self.select_file("system镜像 (*.img *.simg)"))
        file_layout.addWidget(self.btn_system_img)

        self.btn_boot_img = QPushButton("boot镜像")
        self.btn_boot_img.setFixedSize(140, 36)
        self.btn_boot_img.setStyleSheet(self.get_button_style())
        self.btn_boot_img.clicked.connect(lambda: self.select_file("boot镜像 (*.img)"))
        file_layout.addWidget(self.btn_boot_img)

        layout.addLayout(file_layout)

        # ---------- 第三行：MTK解锁 / 展讯解锁 ----------
        unlock_layout = QHBoxLayout()
        unlock_layout.setSpacing(6)

        self.btn_mtk_unlock = QPushButton("MTK解锁")
        self.btn_mtk_unlock.setFixedHeight(36)
        self.btn_mtk_unlock.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_mtk_unlock.setStyleSheet(self.get_button_style())
        self.btn_mtk_unlock.clicked.connect(self.on_mtk_unlock)
        unlock_layout.addWidget(self.btn_mtk_unlock)

        self.btn_spd_unlock = QPushButton("展讯解锁")
        self.btn_spd_unlock.setFixedHeight(36)
        self.btn_spd_unlock.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_spd_unlock.setStyleSheet(self.get_button_style())
        self.btn_spd_unlock.clicked.connect(self.on_spd_unlock)
        unlock_layout.addWidget(self.btn_spd_unlock)

        layout.addLayout(unlock_layout)

        # ---------- 第四行：刷system文件 / 刷入vendor_boot文件 ----------
        flash_layout = QHBoxLayout()
        flash_layout.setSpacing(6)

        self.btn_flash_system = QPushButton("刷system镜像")
        self.btn_flash_system.setFixedHeight(36)
        self.btn_flash_system.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_flash_system.setStyleSheet(self.get_button_style())
        self.btn_flash_system.clicked.connect(self.on_flash_system)
        flash_layout.addWidget(self.btn_flash_system)

        self.btn_flash_vendor_boot = QPushButton("刷vendor_boot镜像")
        self.btn_flash_vendor_boot.setFixedHeight(36)
        self.btn_flash_vendor_boot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_flash_vendor_boot.setStyleSheet(self.get_button_style())
        self.btn_flash_vendor_boot.clicked.connect(self.on_flash_vendor_boot)
        flash_layout.addWidget(self.btn_flash_vendor_boot)

        layout.addLayout(flash_layout)

        # ---------- 第五部分：占满剩余空间的显示区 ----------
        self.display_container = QWidget()
        self.display_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.display_layout = QHBoxLayout(self.display_container)
        self.display_layout.setContentsMargins(0, 0, 0, 0)
        self.display_layout.setSpacing(6)
        layout.addWidget(self.display_container, 1)

        self.refresh_btn_original_style = self.get_button_style()

    def get_button_style(self) -> str:
        return """
            QPushButton {
                background-color: #4A90D9;
                border: 1px solid #bdc3c7;
                border-radius: 0px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover { color: black;   }
            QPushButton:pressed { background-color: #2E6AA8; }
        """

    def _flash_button_green(self, button, original_style):
        green_style = original_style.replace("#4A90D9", "#27ae60")
        button.setStyleSheet(green_style)
        QTimer.singleShot(1000, lambda: button.setStyleSheet(original_style))

    # ---------- device selection ----------

    def on_refresh_clicked(self):
        self.selected_devices = []
        self.update_device_button_text()
        green_style = self.refresh_btn_original_style.replace("#4A90D9", "#27ae60")
        self.refresh_btn.setStyleSheet(green_style)
        self.refresh_device_list()

    def on_clear_records(self):
        self._flash_button_green(self.clear_btn, self.get_button_style())
        self.selected_devices = []
        self.update_device_button_text()
        self.add_status_message("已清除设备选择记录")
        self.refresh_btn.setStyleSheet(self.refresh_btn_original_style)

    def _reboot_single_device(self, sn, fastboot, adb_path):
        """Reboot a single device, auto-detecting fastboot vs ADB mode."""
        in_fastboot = False
        rc, out, err = _run_command([fastboot, 'devices'], timeout=10)
        for line in out.strip().split('\n'):
            if line.strip() and sn in line:
                in_fastboot = True
                break

        if in_fastboot:
            self.add_status_message(f"{sn}: 在 fastboot 模式，执行 fastboot reboot")
            self._log_to_device(sn, "执行 fastboot reboot")
            rc, out, err = _run_command([fastboot, '-s', sn, 'reboot'], timeout=30)
        else:
            self.add_status_message(f"{sn}: 在 ADB 模式，执行 adb reboot")
            self._log_to_device(sn, "执行 adb reboot")
            rc, out, err = _run_command([adb_path, '-s', sn, 'reboot'], timeout=30)

        if rc != 0 and err:
            self.add_status_message(f"{sn}: 重启失败 - {err.strip()}")
            self._log_to_device(sn, f"重启失败: {err.strip()}")
        else:
            self.add_status_message(f"{sn}: 重启命令已发送")
            self._log_to_device(sn, "重启命令已发送")

    def update_device_button_text(self):
        count = len(self.selected_devices)
        if count == 0:
            text = "未选择设备"
            border_color = "#4A90D9"
        else:
            devices_str = ", ".join(self.selected_devices)
            text = f"{devices_str} (已选{count}台)"
            border_color = "#27ae60"

        style = f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid {border_color};
                padding: 5px 12px;
                color: #333;
                font-size: 14px;
                border-radius: 0px;
                text-align: left;
            }}
            QPushButton:hover {{ color: black; 
                background-color: #3A7BC0;
            }}
            QPushButton:pressed {{
                background-color: rgba(240, 240, 240, 200);
            }}
        """
        self.device_btn.setText(text)
        self.device_btn.setToolTip(text if count else "")
        self.device_btn.setStyleSheet(style)
        self.rebuild_display_boxes()

    def rebuild_display_boxes(self):
        if not self.selected_devices:
            self._device_logs.clear()
            while self.display_layout.count():
                item = self.display_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            intro_text = (
                "欢迎使用AutoUnlock工具\n\n"
                "功能介绍：\n"
                "• 设备选择：支持ADB连接，最多同时操作4台设备\n"
                "• 文件选择：可选择展讯解锁文件(.pem)、system镜像、boot镜像\n"
                "• MTK解锁：一键解锁Mediatek平台设备\n"
                "• 展讯解锁：一键解锁展讯平台设备\n"
                "• 刷入镜像：支持刷入system和vendor_boot分区\n\n"
                "操作提示：\n"
                "1. 请先刷新设备列表并勾选需要操作的设备（最多4台）\n"
                "2. 根据需要选择解锁文件或镜像文件\n"
                "3. 点击相应按钮开始操作\n"
                "4. 各设备的实时日志将在下方独立显示"
            )
            intro_edit = QTextEdit()
            intro_edit.setReadOnly(True)
            intro_edit.setPlainText(intro_text)
            intro_edit.setStyleSheet("""
                QTextEdit {
                    background-color: rgba(255, 255, 255, 180);
                    border: 1px solid #4A90D9;
                    color: #333;
                    font-size: 14px;
                    border-radius: 0px;
                }
            """)
            self.display_layout.addWidget(intro_edit)
            return

        adb_path = self.device_manager.get_detected_adb_path()
        build_device_panels(
            self.display_layout, self.selected_devices,
            self._device_logs, self._device_log_buffers,
            self.get_button_style, self._reboot_single_device,
            lambda: adb_path
        )

    def refresh_device_list(self):
        try:
            adb_devices = self.device_manager.get_adb_devices()
            fb_devices = get_fastboot_devices()

            merged = list(adb_devices)
            for sn in fb_devices:
                if sn not in merged:
                    merged.append(sn)
            self.all_devices = merged

            if not merged:
                self.selected_devices = []
                self.update_device_button_text()
                self.add_status_message("未检测到设备 (ADB / fastboot)")
                return
            if len(merged) == 1:
                self.selected_devices = [merged[0]]
                self.update_device_button_text()
                self.add_status_message(f"单台设备，已自动选择: {merged[0]}")
            else:
                self.selected_devices = []
                self.update_device_button_text()
                fb_info = f", fastboot {len(fb_devices)}台" if fb_devices else ""
                self.add_status_message(
                    f"检测到 {len(merged)} 台设备 (ADB {len(adb_devices)}台{fb_info})，最多可选4台，请点击按钮选择"
                )
        except Exception as e:
            self.add_status_message(f"刷新设备列表失败: {e}")

    def show_device_list(self):
        if not self.all_devices:
            return

        def on_selection(selected):
            self.selected_devices = list(selected)
            self.update_device_button_text()
            self.add_status_message(f"设备选择已更新: {', '.join(selected) if selected else '无'}")

        popup = DeviceListPopup(self, self.all_devices, self.selected_devices, on_selection)
        popup.setFixedWidth(self.device_btn.width())
        popup.adjustSize()

        pos = self.device_btn.mapToGlobal(self.device_btn.rect().bottomLeft())
        popup.move(pos)
        popup.show()
        popup.activateWindow()
        self.device_popup = popup
        popup.installEventFilter(self)

    def select_file(self, file_filter: str):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", file_filter)
        if file_path:
            self.file_path_edit.setText(file_path)
            self.add_status_message(f"已选择文件: {file_path}")

    # ---------- unlock operations ----------

    def _check_devices_selected(self):
        if not self.selected_devices:
            show_styled_message(self, "未选择设备", "请先在设备列表中选择至少一台设备", "warning")
            return False
        return True

    def _ensure_device_log_file(self, device_sn):
        """Return (log_file, log_path) for device_sn, creating the log file once per session."""
        if device_sn in self._device_log_files:
            return self._device_log_files[device_sn], self._device_log_paths[device_sn]

        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_sn = device_sn.replace(':', '_').replace('/', '_')
        path = os.path.join(log_dir, f'{safe_sn}_{ts}.log')
        f = open(path, 'w', encoding='utf-8')
        f.write(f"=== 日志文件: {path} ===\n")
        f.write(f"设备号: {device_sn}\n")
        f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.flush()
        self._device_log_files[device_sn] = f
        self._device_log_paths[device_sn] = path
        print(f"[LOG] 创建日志文件: {path}")
        return f, path

    def _close_device_log_files(self):
        for f in self._device_log_files.values():
            try:
                f.close()
            except Exception:
                pass
        self._device_log_files.clear()
        self._device_log_paths.clear()

    def closeEvent(self, event):
        self._close_device_log_files()
        super().closeEvent(event)

    def _start_unlock_thread(self, device_sn, unlock_method, description):
        signals = UnlockSignals()

        pem_path = self.file_path_edit.text().strip() or None
        adb_path = self.device_manager.get_detected_adb_path()
        if not adb_path:
            show_styled_message(self, "ADB 错误", "未检测到 ADB 路径", "critical")
            return

        log_file, log_path = self._ensure_device_log_file(device_sn)
        runner = UnlockRunner(signals, device_sn, adb_path, pem_path, log_file, log_path)
        self._active_workers.append(runner)

        signals.log.connect(self._on_device_log)
        signals.finished.connect(lambda sn, ok, msg, r=runner, s=signals: self._cleanup_worker(sn, ok, msg, r, s))

        thread = threading.Thread(
            target=unlock_method,
            args=(runner,),
            daemon=True
        )
        thread.start()

        self._log_to_device(device_sn, f"开始 {description}: {device_sn}")

    def _cleanup_worker(self, device_sn, success, message, runner, signals):
        self._on_unlock_finished(device_sn, success, message)
        try:
            signals.log.disconnect()
            signals.finished.disconnect()
        except Exception:
            pass
        if runner in self._active_workers:
            self._active_workers.remove(runner)

    def on_mtk_unlock(self):
        if not self._check_devices_selected():
            return
        self.add_status_message("开始 MTK 解锁...")
        for sn in self.selected_devices:
            self._start_unlock_thread(sn, lambda r: r.run_mtk_unlock(), "MTK解锁")

    def on_spd_unlock(self):
        if not self._check_devices_selected():
            return
        pem = self.file_path_edit.text().strip()
        if not pem:
            default_pem = os.path.join(_get_unlock_dir(), 'rsa4096_vbmeta.pem')
            if os.path.isfile(default_pem):
                self.add_status_message(f"未选择 PEM 文件，将使用默认: {default_pem}")
            else:
                show_styled_message(
                    self, "未选择解锁文件",
                    "展讯解锁需要选择 PEM 签名文件。\n\n"
                    "请点击「展讯解锁文件」按钮选择 .pem 文件，\n"
                    "或将 rsa4096_vbmeta.pem 放入 unlock/ 目录。",
                    "warning"
                )
                return
        self.add_status_message("开始展讯解锁...")
        for sn in self.selected_devices:
            self._start_unlock_thread(sn, lambda r: r.run_spd_unlock(), "展讯解锁")

    def on_flash_system(self):
        if not self._check_devices_selected():
            return
        img = self.file_path_edit.text().strip()
        if not img:
            show_styled_message(self, "未选择镜像", "请选择 system 镜像文件 (*.img *.simg)", "warning")
            return
        if 'system' not in os.path.basename(img).lower():
            show_styled_message(self, "镜像不匹配", "所选镜像文件名不含 system，请选择对应的 system 镜像文件", "warning")
            return
        self.add_status_message("开始刷入 system 镜像...")
        for sn in self.selected_devices:
            self._start_unlock_thread(sn, lambda r: r.run_flash_system(img), "刷入system")

    def on_flash_vendor_boot(self):
        if not self._check_devices_selected():
            return
        img = self.file_path_edit.text().strip()
        if not img:
            show_styled_message(self, "未选择镜像", "请选择 vendor_boot 镜像文件 (*.img)", "warning")
            return
        if 'vendor' not in os.path.basename(img).lower():
            show_styled_message(self, "镜像不匹配", "所选镜像文件名不含 vendor，请选择对应的 vendor_boot 镜像文件", "warning")
            return
        self.add_status_message("开始刷入 vendor_boot 镜像...")
        for sn in self.selected_devices:
            self._start_unlock_thread(sn, lambda r: r.run_flash_vendor_boot(img), "刷入vendor_boot")

    # ---------- log routing ----------

    def _on_device_log(self, device_sn, message, is_error=False):
        self._log_to_device(device_sn, message, is_error)

    def _log_to_device(self, device_sn, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        safe_msg = html.escape(message).replace('\n', '<br>')
        if is_error:
            line = (
                f'<span style="color: #FF0000; font-weight: bold;'
                f' font-size: 14px;">[{timestamp}] FAILED -> {safe_msg}</span>'
            )
        else:
            line = f'<span style="color: #333; font-size: 12px;">[{timestamp}] {safe_msg}</span>'

        if device_sn in self._device_logs:
            self._device_logs[device_sn].append(line)
        else:
            self._device_log_buffers.setdefault(device_sn, []).append(line)

        print(f"[{device_sn}] {message}")

    def _on_unlock_finished(self, device_sn, success, message):
        self.add_status_message(f"{device_sn}: {message}")

    # ---------- helpers ----------

    def show_adb_error(self, message):
        show_styled_message(
            self, "ADB环境错误",
            f"{message}\n\n请确保已安装Android SDK并配置ADB环境变量",
            "critical"
        )
        self.device_btn.setText("ADB环境异常")
        self.selected_devices = []
        self.update_device_button_text()
        self.add_status_message("ADB环境异常: " + message)

    def add_status_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def eventFilter(self, obj, event):
        if hasattr(self, 'device_popup') and obj is self.device_popup:
            if event.type() == QEvent.Type.WindowDeactivate:
                self.device_popup.close()
                return True
        return super().eventFilter(obj, event)
