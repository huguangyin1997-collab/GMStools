import hmac
import hashlib

# 固定密钥（可自行修改，建议包含大小写字母和数字）
SECRET_KEY = b"GMStools_S3cr3t_K3y_2026"

def sign_disclaimer_accepted(value: bool) -> str:
    """生成带签名的字符串：布尔值|签名"""
    data = str(value).encode('utf-8')
    signature = hmac.new(SECRET_KEY, data, hashlib.sha256).hexdigest()
    return f"{value}|{signature}"

def verify_disclaimer_accepted(signed_value: str) -> bool:
    """验证签名，成功返回布尔值，否则返回 False"""
    try:
        val_str, sig = signed_value.split('|', 1)
        data = val_str.encode('utf-8')
        expected = hmac.new(SECRET_KEY, data, hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected):
            return val_str == "True"
    except Exception:
        pass
    return False