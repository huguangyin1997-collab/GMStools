# Package_file_utils.py
import json
import hashlib
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, List


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> Tuple[str, str, int]:
        """计算文件的哈希值和大小"""
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        file_size = 0
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)
                    file_size += len(chunk)
        except Exception as e:
            print(f"文件哈希计算失败: {e}")
            return "", "", 0
        
        return md5_hash.hexdigest(), sha256_hash.hexdigest(), file_size
    
    @staticmethod
    def load_json_file(file_path: str) -> Optional[Dict]:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"错误: 文件 {file_path} 不存在")
            return None
        except json.JSONDecodeError:
            print(f"错误: 文件 {file_path} 不是有效的JSON格式")
            return None
    
    @staticmethod
    def get_file_info(file_path: str, package_count: int = 0) -> Dict[str, Any]:
        """获取文件信息"""
        path = Path(file_path).resolve()
        md5, sha256, size = FileUtils.calculate_file_hash(file_path)
        
        return {
            "path": str(path),
            "name": path.name,
            "size": size,
            "md5": md5,
            "sha256": sha256,
            "package_count": package_count,
            "directory": str(path.parent)
        }
    
    @staticmethod
    def format_value_for_html(value: Any) -> str:
        """格式化值用于HTML显示"""
        if value is None:
            return "<i>null</i>"
        elif isinstance(value, bool):
            return "是" if value else "否"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return value
        elif isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False, indent=2)[:100] + ("..." if len(json.dumps(value, ensure_ascii=False)) > 100 else "")
        else:
            return str(value)
    
    @staticmethod
    def format_package_for_html(package: Dict) -> str:
        """格式化包信息用于HTML显示"""
        if not package:
            return ""
        
        lines = []
        
        # 关键字段
        fields = [
            ("版本名称", "version_name"),
            ("安装路径", "dir"),
            ("系统权限标志", "system_priv"),
            ("最小SDK", "min_sdk"),
            ("目标SDK", "target_sdk"),
            ("共享安装包权限", "shares_install_packages_permission"),
            ("默认通知访问", "has_default_notification_access"),
            ("是否为活动管理员", "is_active_admin"),
            ("是否为默认无障碍服务", "is_default_accessibility_service")
        ]
        
        for display_name, field_key in fields:
            value = package.get(field_key)
            if value is not None:
                formatted_value = FileUtils.format_value_for_html(value)
                lines.append(f"<b>{display_name}:</b> {formatted_value}")
        
        # 权限信息
        perms = package.get("requested_permissions", [])
        if perms:
            perm_names = [p.get("name", "未知权限") for p in perms]
            lines.append(f"<b>请求权限:</b> {len(perms)}个")
            if len(perm_names) <= 5:
                lines.append(f"  {', '.join(perm_names)}")
            else:
                lines.append(f"  {', '.join(perm_names[:5])}...")
        
        return "<br>".join(lines)
    
    @staticmethod
    def get_field_display_name(field_key: str) -> str:
        """获取字段的显示名称"""
        field_mapping = {
            "version_name": "版本名称",
            "dir": "安装路径",
            "system_priv": "系统权限标志",
            "min_sdk": "最小SDK",
            "target_sdk": "目标SDK",
            "shares_install_packages_permission": "共享安装包权限",
            "has_default_notification_access": "默认通知访问",
            "is_active_admin": "是否为活动管理员",
            "is_default_accessibility_service": "是否为默认无障碍服务",
            "requested_permissions": "请求的权限"
        }
        return field_mapping.get(field_key, field_key)
    
    @staticmethod
    def get_field_key(display_name: str) -> str:
        """获取显示名称对应的字段键"""
        field_mapping = {
            "版本名称": "version_name",
            "安装路径": "dir",
            "系统权限标志": "system_priv",
            "最小SDK": "min_sdk",
            "目标SDK": "target_sdk",
            "共享安装包权限": "shares_install_packages_permission",
            "默认通知访问": "has_default_notification_access",
            "是否为活动管理员": "is_active_admin",
            "是否为默认无障碍服务": "is_default_accessibility_service",
            "请求的权限": "requested_permissions"
        }
        return field_mapping.get(display_name, display_name)
    
    @staticmethod
    def format_permission_summary(permissions: List[Dict]) -> str:
        """格式化权限摘要"""
        if not permissions:
            return "无权限"
        
        perm_names = [p.get("name", "未知权限") for p in permissions]
        count = len(permissions)
        if count <= 3:
            return f"{count}个权限: {', '.join(perm_names)}"
        else:
            return f"{count}个权限: {', '.join(perm_names[:3])}..."