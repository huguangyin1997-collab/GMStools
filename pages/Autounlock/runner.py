import os
import re
import time
from datetime import datetime
from PyQt6.QtCore import pyqtSignal, QObject

from .utils import (
    _get_fastboot_path, _get_unlock_dir, _run_command, _sign_identifier_token,
    _get_project_root
)


class UnlockSignals(QObject):
    log = pyqtSignal(str, str, bool)    # (device_sn, message, is_error)
    finished = pyqtSignal(str, bool, str)  # (device_sn, success, message)


class UnlockRunner:
    """Runs unlock operations in a background thread."""

    def __init__(self, signals, device_sn, adb_path, pem_path=None, log_file=None, log_path=None):
        self.signals = signals
        self.device_sn = device_sn
        self.adb_path = adb_path
        self.pem_path = pem_path
        self._cancelled = False
        self._log_file = log_file       # session-scoped file handle (owned by Autounlock)
        self._log_path = log_path
        self._owns_log_file = False     # True only when we created the file ourselves

    def cancel(self):
        self._cancelled = True

    def _open_log(self):
        """Use session-scoped log file if provided; otherwise create a new one."""
        if self._log_file is not None:
            self._write_to_file(f"\n--- 新操作开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
            return

        log_dir = os.path.join(_get_project_root(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_sn = self.device_sn.replace(':', '_').replace('/', '_')
        self._log_path = os.path.join(log_dir, f'{safe_sn}_{ts}.log')
        self._log_file = open(self._log_path, 'w', encoding='utf-8')
        self._owns_log_file = True
        self._write_to_file(f"=== 日志文件: {self._log_path} ===")
        self._write_to_file(f"设备号: {self.device_sn}")
        self._write_to_file(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    def _write_to_file(self, msg):
        if self._log_file:
            self._log_file.write(msg + '\n')
            self._log_file.flush()

    def _close_log(self):
        """Close log file only if we created it; session-scoped files are managed externally."""
        if self._owns_log_file and self._log_file:
            self._log_file.close()
        self._log_file = None

    # Harmless fastboot noise — still logged but not treated as errors
    _FASTBOOT_NOISE = [
        "Invalid sparse file format at header magic",
    ]

    def _log(self, msg, is_error=False):
        if not self._cancelled:
            self.signals.log.emit(self.device_sn, msg, is_error)
        self._write_to_file(msg)

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
            if re.search(r'\b(OKAY|FAILED|FAIL)\b', stripped, re.IGNORECASE):
                if not re.search(r'\bOKAY\b', stripped, re.IGNORECASE):
                    self._log(stripped, is_error=True)
                else:
                    self._log(stripped)
            else:
                self._log(stripped)

    def _run(self, cmd, timeout=30, log_cmd=True):
        if log_cmd:
            if isinstance(log_cmd, str):
                self._log(f"> {log_cmd}")
            elif len(cmd) > 1 and '/' in str(cmd[-1]):
                self._log(f"> {' '.join(cmd[:-1])}\n  {cmd[-1]}")
            else:
                self._log(f"> {' '.join(cmd)}")
        return _run_command(cmd, timeout)

    def _wait_countdown(self, seconds, prompt_template):
        """Countdown before unlock, giving the user time to prepare the volume key."""
        for i in range(seconds, 0, -1):
            if self._cancelled:
                return False
            self._log(prompt_template.format(seconds=i))
            time.sleep(1)
        return True

    def _run_unlock_with_retry(self, fastboot, cmd, key_name, max_retries=3, retry_wait=2):
        """Send unlock command, verify with getvar unlocked, retry if still locked."""
        for attempt in range(1, max_retries + 1):
            if self._cancelled:
                return False
            if attempt > 1:
                self._log(f"[重试 {attempt}/{max_retries}] 设备仍处于锁定状态，再次尝试解锁...")
                self._log(f"[提示] 看到设备屏幕提示后请立刻按{key_name}键！")
                prompt = f"[倒计时 {{seconds}}秒] 准备按{key_name}键..."
                self._wait_countdown(retry_wait, prompt)
            self._log("[执行] fastboot flashing unlock...")
            rc, out, err = self._run(cmd, timeout=10)
            combined = (out + err).strip()
            if combined:
                self._log(combined)

            # 展讯设备: 解锁命令输出直接反映解锁状态
            # unlocking bootloader OKAY → 解锁成功（或已解锁）
            # cannot be unlocked repeatedly → 设备已经解锁
            if 'OKAY' in out and 'unlocking bootloader' in out:
                self._log("解锁命令执行成功 ✓")
                return True
            if 'Bootloader can not been unlocked repeatly' in combined:
                self._log("设备已解锁，无需重复解锁 ✓")
                return True

            time.sleep(2)
            if self._check_device_unlocked(fastboot):
                return True
        return False

    def run_mtk_unlock(self):
        """MTK unlock: adb reboot bootloader -> fastboot flashing unlock"""
        self._open_log()
        try:
            fastboot = _get_fastboot_path()
            if not fastboot:
                self._done(False, "未找到 fastboot 工具，请将 fastboot 放入 unlock/ 目录")
                return

            self._log("=== MTK 解锁开始 ===")
            self._log("步骤 1/3: 重启到 bootloader 模式...")
            if self._check_fastboot_device(fastboot):
                self._log("设备已在 fastboot 模式，跳过 adb reboot")
            else:
                rc, out, err = self._run([self.adb_path, '-s', self.device_sn, 'reboot', 'bootloader'])
                if rc != 0 and err:
                    self._log(f"[WARNING] adb reboot bootloader: {err.strip()}")

            self._log("步骤 2/3: 等待 fastboot 设备就绪...")
            if not self._wait_fastboot_device(120):
                self._done(False, "等待 fastboot 设备超时")
                return

            self._log("步骤 3/3: 执行解锁并验证...")
            self._log("[重要] 设备屏幕将出现解锁确认提示，见到提示请立刻按音量上键！")
            self._wait_countdown(3, "[倒计时 {seconds}秒] 请将手指放在音量上键上...")

            cmd = [fastboot, '-s', self.device_sn, 'flashing', 'unlock']
            if self._run_unlock_with_retry(fastboot, cmd, "音量上"):
                self._done(True, "MTK 解锁完成")
            else:
                self._done(False, "MTK 解锁失败: 设备仍未解锁，请检查设备状态后重试")
        except Exception as e:
            self._done(False, f"MTK 解锁异常: {e}")

    def run_spd_unlock(self):
        """Spreadtrum unlock: get token -> sign -> flashing unlock_bootloader"""
        self._open_log()
        try:
            fastboot = _get_fastboot_path()
            unlock_dir = _get_unlock_dir()

            if not fastboot:
                self._done(False, "未找到 fastboot 工具，请将 fastboot 放入 unlock/ 目录")
                return

            pem = self.pem_path
            if not pem or not os.path.isfile(pem):
                default_pem = os.path.join(unlock_dir, 'rsa4096_vbmeta.pem')
                if os.path.isfile(default_pem):
                    pem = default_pem
                    self._log(f"[INFO] 未选择 PEM 文件，使用默认: {default_pem}")
                else:
                    self._done(False, "未选择展讯解锁文件(.pem)，请先选择 PEM 文件")
                    return

            sign_bin = os.path.join(unlock_dir, f'sign_{self.device_sn.replace(":", "_")}.bin')

            self._log("=== 展讯解锁开始 ===")
            self._log(f"使用 PEM: {pem}")

            self._log("步骤 1/5: 重启到 bootloader 模式...")
            if self._check_fastboot_device(fastboot):
                self._log("设备已在 fastboot 模式，跳过 adb reboot")
            else:
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

            self._log("步骤 5/5: 执行解锁并验证...")
            self._log("[重要] 设备屏幕将出现解锁确认提示，见到提示请立刻按音量下键！")
            self._wait_countdown(3, "[倒计时 {seconds}秒] 请将手指放在音量下键上...")

            cmd = [fastboot, '-s', self.device_sn, 'flashing', 'unlock_bootloader', sign_bin]
            if self._run_unlock_with_retry(fastboot, cmd, "音量下", retry_wait=5):
                self._done(True, "展讯解锁完成")
            else:
                self._done(False, "展讯解锁失败: 设备仍未解锁，请检查设备状态后重试")

            try:
                os.remove(sign_bin)
            except OSError:
                pass
        except Exception as e:
            self._done(False, f"展讯解锁异常: {e}")

    def _wait_fastboot_device(self, timeout_sec):
        fastboot = _get_fastboot_path()
        if not fastboot:
            return False
        waited = 0
        while waited < timeout_sec and not self._cancelled:
            rc, out, err = self._run([fastboot, 'devices'], timeout=10, log_cmd=False)
            for line in out.strip().split('\n'):
                if line.strip() and self.device_sn in line:
                    self._log(f"检测到 fastboot 设备: {line.strip()}")
                    return True
            self._log(f"等待 fastboot 设备... ({waited}s)")
            for _ in range(30):
                if self._cancelled:
                    return False
                time.sleep(0.1)
            waited += 3
        return False

    def _get_identifier_token(self, fastboot_path):
        """Get identifier token from fastboot oem get_identifier_token output."""
        rc, out, err = self._run(
            [fastboot_path, '-s', self.device_sn, 'oem', 'get_identifier_token'],
            timeout=30
        )
        combined = (out + err).strip()
        if rc != 0 and not combined:
            self._log(f"[ERROR] 获取 token 失败: {err.strip() or out.strip()}")
            return None

        lines = combined.split('\n')
        token = ''
        for line in lines:
            line = line.strip().replace('\r', '')
            if not line:
                continue
            if re.match(r'^OKAY\b', line, re.IGNORECASE):
                break
            line = re.sub(r'^\(bootloader\)\s*', '', line)
            line = re.sub(r'^Identifier token:\s*', '', line, flags=re.IGNORECASE)
            if line.upper() in ('OKAY', 'FAILED', 'FINISHED'):
                continue
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
                [fastboot, '-s', self.device_sn, 'reboot', target], timeout=30
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
        rc, out, err = self._run([fastboot, 'devices'], timeout=10, log_cmd=False)
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
        self._log(f"[DEBUG] getvar unlocked 返回: {combined.strip()!r}")

        # Positive indicators: device IS unlocked
        if re.search(r'\bunlocked:\s*yes\b', combined):
            self._log("设备已解锁 ✓")
            return True

        # Negative indicators: device IS locked
        if re.search(r'\bunlocked:\s*no\b', combined):
            self._log("设备未解锁 ✗ — bootloader 处于锁定状态")
            return False

        # Some SPD devices use 'secure' variable: secure:no = unlocked
        rc2, out2, err2 = self._run(
            [fastboot, '-s', self.device_sn, 'getvar', 'secure'],
            timeout=10
        )
        combined2 = (out2 + err2).lower()
        self._log(f"[DEBUG] getvar secure 返回: {combined2.strip()!r}")
        if re.search(r'\bsecure:\s*no\b', combined2):
            self._log("设备已解锁 (via getvar secure) ✓")
            return True
        if re.search(r'\bsecure:\s*yes\b', combined2):
            self._log("设备未解锁 ✗ — bootloader 处于锁定状态 (via getvar secure)")
            return False

        # --- 展讯(SPD)平台兼容检测 ---
        # SPD fastboot 的 unlocked/secure 变量存在但值经常为空，
        # 且 oem device-info / getvar all 也不可用。
        # 请肉眼确认手机屏幕显示，解锁成功时 bootloader 界面会显示 info: unlock
        self._log("[INFO] 展讯设备 fastboot 无法查询解锁状态")
        self._log("[INFO] ★★★ 请肉眼确认手机屏幕 ★★★")
        self._log("[INFO] 解锁成功时 bootloader 界面会显示 info: unlock")
        self._log("[INFO] 确认已解锁则忽略此提示，继续执行")
        return True

    def run_flash_system(self, img_path):
        """Flash system image (MTK & Spreadtrum).
        Steps: reboot fastboot -> delete/create logical partition -> erase userdata -> flash system_a"""
        self._open_log()
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
                [fastboot, '-s', self.device_sn, 'delete-logical-partition', 'product_a'],
                timeout=30
            )
            out_err = (out + err).lower()
            self._log(out.strip() if out.strip() else (err.strip() if err else "delete-logical-partition product_a 完成"))
            if re.search(r'(?<!un)locked', out_err):
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return

            rc, out, err = self._run(
                [fastboot, '-s', self.device_sn, 'create-logical-partition', 'product_a', '0'],
                timeout=30
            )
            out_err = (out + err).lower()
            self._log(out.strip() if out.strip() else (err.strip() if err else "create-logical-partition product_a 0 完成"))
            if re.search(r'(?<!un)locked', out_err):
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return

            self._log("步骤 4/5: 清除 userdata...")
            rc, out, err = self._run(
                [fastboot, '-s', self.device_sn, 'erase', 'userdata'],
                timeout=60
            )
            out_err = (out + err).lower()
            self._log(out.strip() if out.strip() else (err.strip() if err else "erase userdata 完成"))
            if re.search(r'(?<!un)locked', out_err):
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return
            if rc != 0:
                self._log(f"[WARNING] erase userdata 返回非零: {err.strip() if err else out.strip()}")

            self._log("步骤 5/5: 刷入 system_a 镜像...")
            rc, out, err = self._run(
                [fastboot, '-s', self.device_sn, 'flash', 'system_a', img_path],
                timeout=600
            )
            out_err = (out + err).lower()
            self._log_clean(out.strip() or err.strip())
            if re.search(r'(?<!un)locked', out_err):
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return
            if rc != 0:
                self._log(f"[WARNING] flash system_a 返回非零: {err.strip() if err else ''}")
                self._done(False, "system 镜像刷入失败")
                return

            self._done(True, "system 镜像刷入完成")
        except Exception as e:
            self._done(False, f"刷入 system 异常: {e}")

    def run_flash_vendor_boot(self, img_path):
        """Flash vendor_boot image (MTK & Spreadtrum).
        Steps: reboot bootloader -> check unlock -> erase userdata -> flash vendor_boot_a"""
        self._open_log()
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
                [fastboot, '-s', self.device_sn, 'erase', 'userdata'],
                timeout=60
            )
            out_err = (out + err).lower()
            self._log(out.strip() if out.strip() else (err.strip() if err else "erase userdata 完成"))
            if re.search(r'(?<!un)locked', out_err):
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return
            if rc != 0:
                self._log(f"[WARNING] erase userdata 返回非零: {err.strip() if err else out.strip()}")

            self._log("步骤 4/4: 刷入 vendor_boot_a 镜像...")
            rc, out, err = self._run(
                [fastboot, '-s', self.device_sn, 'flash', 'vendor_boot_a', img_path],
                timeout=120
            )
            out_err = (out + err).lower()
            self._log_clean(out.strip() or err.strip())
            if re.search(r'(?<!un)locked', out_err):
                self._done(False, "设备 bootloader 未解锁，请先执行解锁操作后再刷入镜像")
                return
            if rc != 0:
                self._log(f"[WARNING] flash vendor_boot_a 返回非零: {err.strip() if err else ''}")
                self._done(False, "vendor_boot 镜像刷入失败")
                return

            self._done(True, "vendor_boot 镜像刷入完成")
        except Exception as e:
            self._done(False, f"刷入 vendor_boot 异常: {e}")

    def _done(self, success, message):
        if not self._cancelled:
            self._log(f"=== {'成功' if success else '失败'}: {message} ===")
            self.signals.finished.emit(self.device_sn, success, message)
        self._write_to_file(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._write_to_file(f"日志文件: {self._log_path}" if self._log_path else "")
        self._close_log()
