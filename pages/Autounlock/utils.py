import os
import sys
import subprocess
import traceback


def get_app_dir():
    """Return the directory containing the executable (frozen) or the project root (dev)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_project_root():
    """Return the project root directory, works both in dev and frozen mode."""
    app_dir = get_app_dir()
    if getattr(sys, 'frozen', False):
        if os.path.isdir(os.path.join(app_dir, 'unlock')):
            return app_dir
        return app_dir
    base = os.path.dirname(os.path.abspath(__file__))
    while base != os.path.dirname(base):
        if os.path.isdir(os.path.join(base, 'unlock')):
            return base
        base = os.path.dirname(base)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_unlock_dir():
    return os.path.join(get_project_root(), 'unlock')


def get_fastboot_path():
    unlock_dir = get_unlock_dir()
    fastboot_name = "fastboot.exe" if sys.platform == "win32" else "fastboot"
    path = os.path.join(unlock_dir, fastboot_name)
    if os.path.isfile(path):
        return path
    return None


def run_command(cmd, timeout=30):
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


def sign_identifier_token(token, pem_path, sign_bin_path):
    """Sign identifier token with RSA-SHA256, replacing the shell script.
    Cross-platform: works on Linux, macOS, and Windows without bash/openssl.

    Falls back to signidentifier_unlockbootloader.sh if the cryptography library
    or its dependencies (e.g. email module) are unavailable in frozen builds.
    """
    # --- attempt 1: Python / cryptography ---
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        try:
            token_bytes = bytes.fromhex(token)
        except ValueError:
            raise ValueError(f"Token 不是有效的十六进制: {token}")

        if len(token_bytes) > 64:
            raise ValueError(f"Token 过长: {len(token_bytes)} bytes (最大 64)")

        padded = token_bytes.ljust(64, b'\x00')

        with open(pem_path, 'rb') as f:
            private_key = load_pem_private_key(f.read(), password=None)

        signature = private_key.sign(
            padded,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        with open(sign_bin_path, 'wb') as f:
            f.write(signature)
        return  # success — done

    except (ImportError, ModuleNotFoundError):
        # cryptography or a dependency (e.g. email in frozen builds) is missing
        pass
    except Exception:
        # Other errors from the Python path — still try the shell fallback
        traceback.print_exc()

    # --- attempt 2: shell script fallback ---
    unlock_dir = os.path.dirname(pem_path) or get_unlock_dir()
    script = os.path.join(unlock_dir, 'signidentifier_unlockbootloader.sh')
    if not os.path.isfile(script):
        raise RuntimeError(
            "签名 token 失败: cryptography 库不可用，且未找到 "
            f"signidentifier_unlockbootloader.sh (已搜索: {script})"
        )

    result = subprocess.run(
        ['bash', script, token, pem_path, sign_bin_path],
        capture_output=True, text=True, timeout=30,
        cwd=unlock_dir
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Shell 签名脚本失败 (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    if not os.path.isfile(sign_bin_path) or os.path.getsize(sign_bin_path) == 0:
        raise RuntimeError(
            f"Shell 签名脚本未生成有效签名文件: {sign_bin_path}"
        )


def run_command_stream(cmd, timeout=60, log_callback=None):
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


# Backward-compatible aliases for Autounlock.py
_get_app_dir = get_app_dir
_get_project_root = get_project_root
_get_unlock_dir = get_unlock_dir
_get_fastboot_path = get_fastboot_path
_run_command = run_command
_run_command_stream = run_command_stream
_sign_identifier_token = sign_identifier_token
