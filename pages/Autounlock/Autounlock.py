import html
import os
import sys
import re
import subprocess
import threading
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDialog,
    QListWidget, QListWidgetItem, QAbstractItemView, QLabel,
    QSizePolicy, QLineEdit, QFileDialog, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QEvent, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen
from ..Ctsverifierdb.device_manager import DeviceManager


def _get_app_dir():
    """Return the directory containing the executable (frozen) or the project root (dev)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_project_root():
    """Return the project root directory, works both in dev and frozen mode."""
    app_dir = _get_app_dir()
    # In frozen mode, unlock/ is next to the EXE
    if getattr(sys, 'frozen', False):
        if os.path.isdir(os.path.join(app_dir, 'unlock')):
            return app_dir
        return app_dir  # fallback to app dir even if unlock/ missing
    # Dev mode: walk up from __file__ until we find unlock/
    base = os.path.dirname(os.path.abspath(__file__))
    while base != os.path.dirname(base):
        if os.path.isdir(os.path.join(base, 'unlock')):
            return base
        base = os.path.dirname(base)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_unlock_dir():
    return os.path.join(_get_project_root(), 'unlock')


def _get_fastboot_path():
    unlock_dir = _get_unlock_dir()
    fastboot_name = "fastboot.exe" if sys.platform == "win32" else "fastboot"
    path = os.path.join(unlock_dir, fastboot_name)
    if os.path.isfile(path):
        return path
    return None


def _run_command(cmd, timeout=30):
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            shell=False
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return -1, "", str(e)


def _sign_identifier_token(token, pem_path, sign_bin_path):
    """Sign identifier token with RSA-SHA256, replacing the shell script.
    Cross-platform: works on Linux, macOS, and Windows without bash/openssl.
    """
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
    except ImportError:
        raise ImportError(
            "缺少 cryptography 库，请运行: pip install cryptography"
        )

    # Convert hex token to binary, pad to 64 bytes (matching shell script logic)
    try:
        token_bytes = bytes.fromhex(token)
    except ValueError:
        raise ValueError(f"Token 不是有效的十六进制: {token}")

    if len(token_bytes) > 64:
        raise ValueError(f"Token 过长: {len(token_bytes)} bytes (最大 64)")

    padded = token_bytes.ljust(64, b'\x00')

    # Load RSA private key
    with open(pem_path, 'rb') as f:
        private_key = load_pem_private_key(f.read(), password=None)

    # Sign with RSA-SHA256 (PKCS#1 v1.5), equivalent to:
    #   openssl dgst -sha256 -sign <key> <data>
    signature = private_key.sign(
        padded,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    with open(sign_bin_path, 'wb') as f:
        f.write(signature)


def _run_command_stream(cmd, timeout=60, log_callback=None):
    """Run a command and stream stdout/stderr line by line to log_callback."""
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )
        try:
            for line in iter(proc.stdout.readline, ''):
                if log_callback:
                    log_callback(line.rstrip('\n'))
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            if log_callback:
                log_callback("[ERROR] 命令超时")
            return -1
        return proc.returncode
    except FileNotFoundError:
        if log_callback:
            log_callback(f"[ERROR] 命令未找到: {cmd[0]}")
        return -1
    except Exception as e:
        if log_callback:
            log_callback(f"[ERROR] {e}")
        return -1


class UnlockSignals(QObject):
    log = pyqtSignal(str, str, bool)    # (device_sn, message, is_error)
    finished = pyqtSignal(str, bool, str)  # (device_sn, success, message)


class UnlockRunner:
    """Runs unlock operations in a background thread."""

    def __init__(self, signals, device_sn, adb_path, pem_path=None):
        self.signals = signals
        self.device_sn = device_sn
        self.adb_path = adb_path
        self.pem_path = pem_path
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    # Harmless fastboot noise — still logged but not treated as errors
    _FASTBOOT_NOISE = [
        "Invalid sparse file format at header magic",
    ]

    def _log(self, msg, is_error=False):
        if not self._cancelled:
            self.signals.log.emit(self.device_sn, msg, is_error)

    def _log_clean(self, msg):
        """Log fastboot output, highlighting any non-OKAY lines in red."""
        if not msg:
            return
        for line in msg.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue
            if any(noise in stripped for noise in self._FASTBOOT_NOISE):
                self._log(stripped)
                continue
            # Detect flash status lines: each should end with "OKAY [time]" or "FAILED [...]"
            # Lines like: "Sending sparse 'system_a' 1/7 ... OKAY [ 10.122s]"
            if re.search(r'\b(OKAY|FAILED|FAIL)\b', stripped, re.IGNORECASE):
                if not re.search(r'\bOKAY\b', stripped, re.IGNORECASE):
                    # Any status that is NOT OKAY → flash failure, show prominently
                    self._log(stripped, is_error=True)
                else:
                    self._log(stripped)
            else:
                self._log(stripped)

    def _run(self, cmd, timeout=30):
        return _run_command(cmd, timeout)

    def run_mtk_unlock(self):
        """MTK unlock: adb reboot bootloader → fastboot flashing unlock"""
        try:
            fastboot = _get_fastboot_path()
            if not fastboot:
                self._done(False, "未找到 fastboot 工具，请将 fastboot 放入 unlock/ 目录")
                return

            self._log("=== MTK 解锁开始 ===")
            self._log("步骤 1/3: 重启到 bootloader 模式...")
            rc, out, err = self._run([self.adb_path, '-s', self.device_sn, 'reboot', 'bootloader'])
            if rc != 0 and err:
                self._log(f"[WARNING] adb reboot bootloader: {err.strip()}")

            self._log("步骤 2/3: 等待 fastboot 设备就绪...")
            if not self._wait_fastboot_device(120):
                self._done(False, "等待 fastboot 设备超时")
                return

            self._log("步骤 3/3: 执行 fastboot flashing unlock...")
            self._log("[提示] 请在设备上按音量上键确认解锁")
            rc, out, err = self._run([fastboot, '-s', self.device_sn,'flashing', 'unlock'], timeout=60)
            self._log(out.strip() if out.strip() else (err.strip() if err else "命令完成"))
            if rc != 0 and err:
                self._log(f"[WARNING] flashing unlock 返回非零: {err.strip()}")

            self._done(True, "MTK 解锁完成")
        except Exception as e:
            self._done(False, f"MTK 解锁异常: {e}")

    def run_spd_unlock(self):
        """Spreadtrum unlock: get token → sign → flashing unlock_bootloader"""
        try:
            fastboot = _get_fastboot_path()
            unlock_dir = _get_unlock_dir()

            if not fastboot:
                self._done(False, "未找到 fastboot 工具，请将 fastboot 放入 unlock/ 目录")
                return

            pem = self.pem_path
            if not pem or not os.path.isfile(pem):
                # 尝试使用 unlock 目录下默认的 pem
                default_pem = os.path.join(unlock_dir, 'rsa4096_vbmeta.pem')
                if os.path.isfile(default_pem):
                    pem = default_pem
                    self._log(f"[INFO] 未选择 PEM 文件，使用默认: {default_pem}")
                else:
                    self._done(False, "未选择展讯解锁文件(.pem)，请先选择 PEM 文件")
                    return

            # unique sign.bin per device to avoid conflicts
            sign_bin = os.path.join(unlock_dir, f'sign_{self.device_sn.replace(":", "_")}.bin')

            self._log("=== 展讯解锁开始 ===")
            self._log(f"使用 PEM: {pem}")

            self._log("步骤 1/5: 重启到 bootloader 模式...")
            rc, out, err = self._run([self.adb_path, '-s', self.device_sn, 'reboot', 'bootloader'])
            if rc != 0 and err:
                self._log(f"[WARNING] adb reboot bootloader: {err.strip()}")

            self._log("步骤 2/5: 等待 fastboot 设备就绪...")
            if not self._wait_fastboot_device(120):
                self._done(False, "等待 fastboot 设备超时")
                return

            self._log("步骤 3/5: 获取 identifier token...")
            token = self._get_identifier_token(fastboot)
            if not token:
                self._done(False, "获取 identifier token 失败")
                return
            self._log(f"获取到 token (长度: {len(token)})")

            self._log("步骤 4/5: 签名 token...")
            try:
                _sign_identifier_token(token, pem, sign_bin)
                self._log("签名完成")
            except Exception as e:
                self._log(f"[ERROR] 签名失败: {e}")
                self._done(False, "签名 token 失败")
                return

            self._log("步骤 5/5: 执行 fastboot flashing unlock_bootloader...")
            self._log("[提示] 请在设备上按音量下键确认解锁")
            rc, out, err = self._run(
                [fastboot, '-s', self.device_sn,'flashing', 'unlock_bootloader', sign_bin],
                timeout=60
            )
            self._log(out.strip() if out.strip() else (err.strip() if err else "命令完成"))
            if rc != 0 and err:
                self._log(f"[WARNING] unlock_bootloader 返回非零: {err.strip()}")

            # cleanup
            try:
                os.remove(sign_bin)
            except OSError:
                pass

            self._done(True, "展讯解锁完成")
        except Exception as e:
            self._done(False, f"展讯解锁异常: {e}")

    def _wait_fastboot_device(self, timeout_sec):
        fastboot = _get_fastboot_path()
        if not fastboot:
            return False
        waited = 0
        while waited < timeout_sec and not self._cancelled:
            rc, out, err = self._run([fastboot, 'devices'], timeout=10)
            for line in out.strip().split('\n'):
                if line.strip() and ('fastboot' in line.lower() or self.device_sn in line):
                    self._log(f"检测到 fastboot 设备: {line.strip()}")
                    return True
            self._log(f"等待 fastboot 设备... ({waited}s)")
            # sleep 3 seconds between checks
            for _ in range(30):
                if self._cancelled:
                    return False
                import time
                time.sleep(0.1)
            waited += 3
        return False

    def _get_identifier_token(self, fastboot_path):
        """Get identifier token from fastboot oem get_identifier_token output."""
        rc, out, err = self._run(
            [fastboot_path, '-s', self.device_sn, 'oem', 'get_identifier_token'],
            timeout=30
        )
        # fastboot sends most output to stderr, combine both for parsing
        combined = (out + err).strip()
        if rc != 0 and not combined:
            self._log(f"[ERROR] 获取 token 失败: {err.strip() or out.strip()}")
            return None

        # Parse token: only extract from (bootloader) lines before the OKAY marker
        lines = combined.split('\n')
        token = ''
        for line in lines:
            line = line.strip().replace('\r', '')
            if not line:
                continue
            # OKAY marks end of command data — stop parsing here
            if re.match(r'^OKAY\b', line, re.IGNORECASE):
                break
            # Remove known prefixes
            line = re.sub(r'^\(bootloader\)\s*', '', line)
            line = re.sub(r'^Identifier token:\s*', '', line, flags=re.IGNORECASE)
            # Skip known non-data lines
            if line.upper() in ('OKAY', 'FAILED', 'FINISHED'):
                continue
            # Only keep hex characters (token is a continuous hex string)
            hex_only = re.sub(r'[^0-9a-fA-F]', '', line)
            if hex_only:
                token += hex_only

        self._log(f"解析到 token 长度: {len(token)}")
        if not token:
            self._log(f"[DEBUG] 原始输出(stdout+stderr):\n{combined}")
        return token if len(token) >= 10 else None

    def _reboot_to(self, fastboot, target):
        """Reboot to target mode. Auto-detect: if device is already in fastboot, use
        fastboot reboot; otherwise use adb reboot."""
        in_fastboot = self._check_fastboot_device(fastboot)
        if in_fastboot:
            self._log(f"设备已在 fastboot 模式，使用 fastboot reboot {target}")
            rc, out, err = self._run(
                [fastboot, '-s', self.device_sn,'reboot', target], timeout=30
            )
        else:
            self._log(f"设备在 ADB 模式，使用 adb reboot {target}")
            rc, out, err = self._run(
                [self.adb_path, '-s', self.device_sn, 'reboot', target], timeout=30
            )
        if rc != 0 and err:
            self._log(f"[WARNING] reboot {target}: {err.strip()}")

    def _check_fastboot_device(self, fastboot):
        """Check if device is currently in fastboot mode."""
        rc, out, err = self._run([fastboot, 'devices'], timeout=10)
        for line in out.strip().split('\n'):
            if line.strip() and self.device_sn in line:
                return True
        return False

    def _check_device_unlocked(self, fastboot):
        """Check if the device bootloader is unlocked. Returns True if unlocked, False if locked."""
        rc, out, err = self._run(
            [fastboot, '-s', self.device_sn, 'getvar', 'unlocked'],
            timeout=10
        )
        combined = (out + err).lower()
        if 'unlocked: yes' in combined:
            self._log("设备已解锁 ✓")
            return True
        if 'unlocked: no' in combined or 'locked' in combined:
            self._log("设备未解锁 ✗ — bootloader 处于锁定状态")
            return False
        # Some devices don't support getvar unlocked, try alternative
        self._log("[INFO] 无法通过 getvar 确定解锁状态，继续执行")
        return True  # assume unlocked if we can't determine

    def run_flash_system(self, img_path):
        """Flash system image (MTK & Spreadtrum).
        Steps: reboot fastboot → delete/create logical partition → erase userdata → flash system_a"""
        try:
            fastboot = _get_fastboot_path()
            if not fastboot:
                self._done(False, "未找到 fastboot 工具")
                return

            self._log("=== 刷入 system 镜像 ===")
            self._log(f"镜像: {img_path}")

            self._log("步骤 1/5: 重启到 fastbootd 模式...")
            self._reboot_to(fastboot, 'fastboot')

            self._log("步骤 2/5: 等待 fastboot 设备...")
            if not self._wait_fastboot_device(120):
                self._done(False, "等待 fastboot 设备超时")
                return

            if not self._check_device_unlocked(fastboot):
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return

            self._log("步骤 3/5: 重建 product_a 逻辑分区...")
            rc, out, err = self._run(
                [fastboot, '-s', self.device_sn,'delete-logical-partition', 'product_a'],
                timeout=30
            )
            out_err = (out + err).lower()
            self._log(out.strip() if out.strip() else (err.strip() if err else "delete-logical-partition product_a 完成"))
            if 'locked' in out_err:
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return

            rc, out, err = self._run(
                [fastboot, '-s', self.device_sn,'create-logical-partition', 'product_a', '0'],
                timeout=30
            )
            out_err = (out + err).lower()
            self._log(out.strip() if out.strip() else (err.strip() if err else "create-logical-partition product_a 0 完成"))
            if 'locked' in out_err:
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return

            self._log("步骤 4/5: 清除 userdata...")
            rc, out, err = self._run(
                [fastboot, '-s', self.device_sn,'erase', 'userdata'],
                timeout=60
            )
            out_err = (out + err).lower()
            self._log(out.strip() if out.strip() else (err.strip() if err else "erase userdata 完成"))
            if 'locked' in out_err:
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return

            self._log("步骤 5/5: 刷入 system_a 镜像...")
            rc, out, err = self._run(
                [fastboot, '-s', self.device_sn,'flash', 'system_a', img_path],
                timeout=600
            )
            out_err = (out + err).lower()
            self._log_clean(out.strip() or err.strip())
            if 'locked' in out_err:
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return
            if rc != 0:
                self._log(f"[WARNING] flash system_a 返回非零: {err.strip() if err else ''}")

            self._done(True, "system 镜像刷入完成")
        except Exception as e:
            self._done(False, f"刷入 system 异常: {e}")

    def run_flash_vendor_boot(self, img_path):
        """Flash vendor_boot image (MTK & Spreadtrum).
        Steps: reboot bootloader → check unlock → erase userdata → flash vendor_boot_a"""
        try:
            fastboot = _get_fastboot_path()
            if not fastboot:
                self._done(False, "未找到 fastboot 工具")
                return

            self._log("=== 刷入 vendor_boot 镜像 ===")
            self._log(f"镜像: {img_path}")

            self._log("步骤 1/4: 重启到 bootloader 模式...")
            self._reboot_to(fastboot, 'bootloader')

            self._log("步骤 2/4: 等待 fastboot 设备...")
            if not self._wait_fastboot_device(120):
                self._done(False, "等待 fastboot 设备超时")
                return

            if not self._check_device_unlocked(fastboot):
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return

            self._log("步骤 3/4: 清除 userdata...")
            rc, out, err = self._run(
                [fastboot, '-s', self.device_sn,'erase', 'userdata'],
                timeout=60
            )
            out_err = (out + err).lower()
            self._log(out.strip() if out.strip() else (err.strip() if err else "erase userdata 完成"))
            if 'locked' in out_err:
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return

            self._log("步骤 4/4: 刷入 vendor_boot_a 镜像...")
            rc, out, err = self._run(
                [fastboot, '-s', self.device_sn,'flash', 'vendor_boot_a', img_path],
                timeout=120
            )
            out_err = (out + err).lower()
            self._log_clean(out.strip() or err.strip())
            if 'locked' in out_err:
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return
            if rc != 0:
                self._log(f"[WARNING] flash vendor_boot_a 返回非零: {err.strip() if err else ''}")

            self._done(True, "vendor_boot 镜像刷入完成")
        except Exception as e:
            self._done(False, f"刷入 vendor_boot 异常: {e}")

    def _done(self, success, message):
        if not self._cancelled:
            self._log(f"=== {'成功' if success else '失败'}: {message} ===")
            self.signals.finished.emit(self.device_sn, success, message)


class Autounlock(QWidget):
    def __init__(self):
        super().__init__()
        self.device_manager = DeviceManager()
        self.selected_devices = []
        self.all_devices = []
        self._active_workers = []  # keep references to prevent GC
        self._device_logs = {}     # device_sn -> QTextEdit
        self._device_log_buffers = {}  # device_sn -> list of log lines (before widget is created)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setup_ui()
        self.update_device_button_text()
        QTimer.singleShot(0, self.delayed_adb_check)

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
                background-color: rgba(255, 255, 255, 100);
                border: 1px solid #39C5BB;
                padding: 5px 12px;
                color: #333;
                font-size: 14px;
                border-radius: 0px;
            }
            QLineEdit:hover {
                background-color: rgba(255, 255, 255, 200);
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
                background-color: #39C5BB;
                border: 1px solid #bdc3c7;
                border-radius: 0px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover { color: red; }
            QPushButton:pressed { background-color: #259990; }
        """

    def _flash_button_green(self, button, original_style):
        green_style = original_style.replace("#39C5BB", "#27ae60")
        button.setStyleSheet(green_style)
        QTimer.singleShot(1000, lambda: button.setStyleSheet(original_style))

    # ---------- device selection ----------

    def on_refresh_clicked(self):
        self.selected_devices = []
        self.update_device_button_text()
        green_style = self.refresh_btn_original_style.replace("#39C5BB", "#27ae60")
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
        # check if in fastboot mode
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
            tooltip = ""
            border_color = "#39C5BB"
        else:
            devices_str = ", ".join(self.selected_devices)
            text = f"{devices_str} (已选{count}台)"
            tooltip = text
            border_color = "#27ae60"

        style = f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 100);
                border: 1px solid {border_color};
                padding: 5px 12px;
                color: #333;
                font-size: 14px;
                border-radius: 0px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 200);
            }}
            QPushButton:pressed {{
                background-color: rgba(240, 240, 240, 200);
            }}
        """
        self.device_btn.setText(text)
        self.device_btn.setToolTip(tooltip)
        self.device_btn.setStyleSheet(style)
        self.rebuild_display_boxes()

    def rebuild_display_boxes(self):
        self._device_logs.clear()
        while self.display_layout.count():
            item = self.display_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.selected_devices:
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
                    background-color: rgba(255, 255, 255, 140);
                    border: 1px solid #39C5BB;
                    color: #333;
                    font-size: 14px;
                    border-radius: 0px;
                }
            """)
            self.display_layout.addWidget(intro_edit)
            return

        fastboot = _get_fastboot_path()
        adb_path = self.device_manager.get_detected_adb_path()

        for device_sn in self.selected_devices:
            # vertical wrapper: text edit + reboot button
            wrapper = QVBoxLayout()
            wrapper.setContentsMargins(0, 0, 0, 0)
            wrapper.setSpacing(4)

            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlaceholderText(f"{device_sn} 的日志输出...")
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: rgba(255, 255, 255, 140);
                    border: 1px solid #39C5BB;
                    color: #333;
                    font-size: 12px;
                    border-radius: 0px;
                }
            """)
            text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            wrapper.addWidget(text_edit, 1)
            self._device_logs[device_sn] = text_edit

            reboot_btn = QPushButton(f"重启 {device_sn}")
            reboot_btn.setFixedHeight(28)
            reboot_btn.setStyleSheet(self.get_button_style())
            reboot_btn.clicked.connect(lambda checked, sn=device_sn: self._reboot_single_device(sn, fastboot, adb_path))
            wrapper.addWidget(reboot_btn)

            # wrap layout in a widget to add to the display layout
            wrap_widget = QWidget()
            wrap_widget.setLayout(wrapper)
            self.display_layout.addWidget(wrap_widget)

            # flush buffered logs
            if device_sn in self._device_log_buffers:
                for msg in self._device_log_buffers[device_sn]:
                    text_edit.append(msg)
                del self._device_log_buffers[device_sn]

    def _get_fastboot_devices(self):
        """Get devices currently in fastboot mode."""
        fastboot = _get_fastboot_path()
        if not fastboot:
            return []
        try:
            rc, out, err = _run_command([fastboot, 'devices'], timeout=10)
            if rc != 0:
                return []
            devices = []
            for line in out.strip().split('\n'):
                line = line.strip()
                if line and '\t' in line:
                    sn = line.split('\t')[0].strip()
                    if sn:
                        devices.append(sn)
            return devices
        except Exception:
            return []

    def refresh_device_list(self):
        try:
            adb_devices = self.device_manager.get_adb_devices()
            fb_devices = self._get_fastboot_devices()

            # merge, deduplicate, adb first then fastboot
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

        class Popup(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent, Qt.WindowType.Popup)
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
                painter.setPen(QPen(QColor(0, 0, 0, 80), 1))
                painter.drawRect(self.rect())

        popup = Popup(self)
        popup_layout = QVBoxLayout(popup)
        popup_layout.setContentsMargins(8, 8, 8, 8)
        popup_layout.setSpacing(6)

        tip_label = QLabel("⚡ 最多可同时选择 4 台设备 (实时生效)")
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip_label.setStyleSheet("color: #666; font-size: 12px; padding: 2px;")
        popup_layout.addWidget(tip_label)

        list_widget = QListWidget()
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 12px;
                min-height: 30px;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: rgba(224, 224, 224, 200);
            }
            QListWidget::item:hover {
                background-color: rgba(224, 224, 224, 150);
            }
        """)

        for device in self.all_devices:
            item = QListWidgetItem(device)
            list_widget.addItem(item)
            if device in self.selected_devices:
                item.setSelected(True)

        last_valid_selected = list(self.selected_devices)

        def on_selection_changed():
            nonlocal last_valid_selected
            selected = [item.text() for item in list_widget.selectedItems()]
            if len(selected) > 4:
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    item.setSelected(item.text() in last_valid_selected)
                tip_label.setText("⚠️ 最多只能选择 4 台设备！")
                tip_label.setStyleSheet("color: red; font-size: 12px; padding: 2px;")
                QTimer.singleShot(1500, lambda: (
                    tip_label.setText("⚡ 最多可同时选择 4 台设备 (实时生效)"),
                    tip_label.setStyleSheet("color: #666; font-size: 12px; padding: 2px;")
                ))
            else:
                last_valid_selected = list(selected)
                self.selected_devices = list(selected)
                self.update_device_button_text()
                self.add_status_message(f"设备选择已更新: {', '.join(selected) if selected else '无'}")

        list_widget.itemSelectionChanged.connect(on_selection_changed)
        popup_layout.addWidget(list_widget)

        popup.setFixedWidth(self.device_btn.width())
        item_height = list_widget.sizeHintForRow(0) if list_widget.count() > 0 else 30
        visible_items = min(list_widget.count(), 5)
        list_widget.setFixedHeight(item_height * visible_items + 4)
        popup.adjustSize()
        popup.setMaximumHeight(400)

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
            self._show_styled_message("未选择设备", "请先在设备列表中选择至少一台设备", "warning")
            return False
        return True

    def _start_unlock_thread(self, device_sn, unlock_method, description):
        signals = UnlockSignals()

        pem_path = self.file_path_edit.text().strip() or None
        adb_path = self.device_manager.get_detected_adb_path()
        if not adb_path:
            self._show_styled_message("ADB 错误", "未检测到 ADB 路径", "critical")
            return

        runner = UnlockRunner(signals, device_sn, adb_path, pem_path)
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
            # check if there's a default pem in unlock dir
            default_pem = os.path.join(_get_unlock_dir(), 'rsa4096_vbmeta.pem')
            if os.path.isfile(default_pem):
                self.add_status_message(f"未选择 PEM 文件，将使用默认: {default_pem}")
            else:
                self._show_styled_message(
                    "未选择解锁文件",
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
            self._show_styled_message("未选择镜像", "请选择 system 镜像文件 (*.img *.simg)", "warning")
            return
        self.add_status_message("开始刷入 system 镜像...")
        for sn in self.selected_devices:
            self._start_unlock_thread(sn, lambda r: r.run_flash_system(img), "刷入system")

    def on_flash_vendor_boot(self):
        if not self._check_devices_selected():
            return
        img = self.file_path_edit.text().strip()
        if not img:
            self._show_styled_message("未选择镜像", "请选择 boot 镜像文件 (*.img)", "warning")
            return
        self.add_status_message("开始刷入 vendor_boot 镜像...")
        for sn in self.selected_devices:
            self._start_unlock_thread(sn, lambda r: r.run_flash_vendor_boot(img), "刷入vendor_boot")

    # ---------- log routing ----------

    def _on_device_log(self, device_sn, message, is_error=False):
        self._log_to_device(device_sn, message, is_error)

    def _log_to_device(self, device_sn, message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        safe_msg = html.escape(message)
        if is_error:
            line = (
                f'<span style="color: #FF0000; font-weight: bold;'
                f' font-size: 14px;">[{timestamp}] FAILED → {safe_msg}</span>'
            )
        else:
            line = f'<span style="color: #333; font-size: 12px;">[{timestamp}] {safe_msg}</span>'

        if device_sn in self._device_logs:
            self._device_logs[device_sn].append(line)
        else:
            # buffer for when widget isn't created yet
            self._device_log_buffers.setdefault(device_sn, []).append(line)

        # also print to console
        print(f"[{device_sn}] {message}")

    def _on_unlock_finished(self, device_sn, success, message):
        self.add_status_message(f"{device_sn}: {message}")

    # ---------- helpers ----------

    def _show_styled_message(self, title, message, icon_type="warning"):
        """Show a themed dialog matching the app's visual style."""
        accent_map = {
            "critical": ("#E91E63", "✕"),
            "warning": ("#39C5BB", "!"),
            "info": ("#39C5BB", "i"),
        }
        accent, icon_char = accent_map.get(icon_type, accent_map["warning"])

        dlg = QDialog(self)
        dlg.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        dlg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        dlg.setModal(True)
        dlg.setFixedWidth(400)

        # --- card ---
        card = QFrame()
        card.setObjectName("styledCard")
        card.setStyleSheet("""
            QFrame#styledCard {
                background-color: white;
                border: 1px solid #dcdde1;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # accent bar
        bar = QLabel()
        bar.setFixedHeight(3)
        bar.setStyleSheet(f"background-color: {accent}; border: none;")
        card_layout.addWidget(bar)

        # body
        body = QHBoxLayout()
        body.setContentsMargins(20, 18, 20, 12)
        body.setSpacing(14)

        icon_lbl = QLabel(icon_char)
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            QLabel {{
                background-color: {accent};
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }}
        """)
        body.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignTop)

        text_block = QVBoxLayout()
        text_block.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #2c3e50; border: none;")
        title_lbl.setWordWrap(True)
        text_block.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet("font-size: 13px; color: #636e72; border: none;")
        msg_lbl.setWordWrap(True)
        text_block.addWidget(msg_lbl)

        body.addLayout(text_block, 1)
        card_layout.addLayout(body)

        # button row
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(20, 4, 20, 16)
        btn_row.addStretch()

        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(80, 30)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent};
                border: none;
                color: white;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ color: #ecf0f1; }}
            QPushButton:pressed {{ background-color: {accent}; opacity: 0.85; }}
        """)
        ok_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(ok_btn)
        card_layout.addLayout(btn_row)

        main_layout = QVBoxLayout(dlg)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(card)

        dlg.adjustSize()
        parent_widget = self.window() if self.window() else self
        pc = parent_widget.geometry().center()
        dlg.move(pc.x() - dlg.width() // 2, pc.y() - dlg.height() // 2)

        dlg.exec()

    def show_adb_error(self, message):
        self._show_styled_message(
            "ADB环境错误",
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
