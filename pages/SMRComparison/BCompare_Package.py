import json
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import hashlib
from pathlib import Path

class modelsChangeType(Enum):
    """变更类型"""
    SAME = "same"           # 相同
    MODIFIED = "modified"   # 修改
    ADDED = "added"         # 新增
    REMOVED = "removed"     # 删除

@dataclass
class PackageChange:
    """包变更信息"""
    change_type: modelsChangeType
    package_name: str
    old_package: Optional[Dict]
    new_package: Optional[Dict]
    differences: List[Tuple[str, Any, Any]] = None  # 字段名, 旧值, 新值
    old_index: Optional[int] = None
    new_index: Optional[int] = None
    
    def __post_init__(self):
        if self.differences is None:
            self.differences = []

@dataclass
class PackageComparisonResult:
    """包比较结果"""
    is_identical: bool
    status: str
    summary: Dict[str, int]
    changes: List[PackageChange]
    old_file_stats: Dict[str, Any]
    new_file_stats: Dict[str, Any]
    old_packages: List[Dict]
    new_packages: List[Dict]
    comparison_text: str = ""

class PackageComparator:
    """Package JSON文件对比器 - 支持HTML报告"""
    
    def __init__(self):
        self.differences_found = False
        self.total_differences = 0
        self.total_packages_compared = 0
        self.comparison_result = None
    
    def _calculate_file_hash(self, file_path: str) -> Tuple[str, str, int]:
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
    
    def load_json_file(self, file_path: str) -> Dict:
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
    
    def compare_files(self, mr_file_path: str, smr_file_path: str) -> PackageComparisonResult:
        """比较两个Package JSON文件，返回结构化结果"""
        # 重置统计
        self.differences_found = False
        self.total_differences = 0
        self.total_packages_compared = 0
        
        # 获取文件信息
        old_file_path = Path(mr_file_path).resolve()
        new_file_path = Path(smr_file_path).resolve()
        
        # 文件基础信息
        old_file_info = {
            "path": str(old_file_path),
            "name": old_file_path.name,
            "size": 0,
            "md5": "",
            "sha256": "",
            "package_count": 0,
            "directory": str(old_file_path.parent)
        }
        
        new_file_info = {
            "path": str(new_file_path),
            "name": new_file_path.name,
            "size": 0,
            "md5": "",
            "sha256": "",
            "package_count": 0,
            "directory": str(new_file_path.parent)
        }
        
        # 计算文件哈希
        md5_old, sha256_old, size_old = self._calculate_file_hash(mr_file_path)
        md5_new, sha256_new, size_new = self._calculate_file_hash(smr_file_path)
        
        old_file_info.update({
            "size": size_old,
            "md5": md5_old,
            "sha256": sha256_old
        })
        
        new_file_info.update({
            "size": size_new,
            "md5": md5_new,
            "sha256": sha256_new
        })
        
        # 加载数据
        mr_data = self.load_json_file(mr_file_path)
        smr_data = self.load_json_file(smr_file_path)
        
        if mr_data is None or smr_data is None:
            return PackageComparisonResult(
                is_identical=False,
                status="FAIL",
                summary={},
                changes=[],
                old_file_stats=old_file_info,
                new_file_stats=new_file_info,
                old_packages=[],
                new_packages=[],
                comparison_text="无法比较：文件加载失败\n"
            )
        
        # 执行比较
        result = self._compare_structured(mr_data, smr_data, old_file_info, new_file_info)
        self.comparison_result = result
        return result
    
    def _compare_structured(self, mr_data: Dict, smr_data: Dict, 
                          old_file_info: Dict, new_file_info: Dict) -> PackageComparisonResult:
        """结构化比较两个Package数据"""
        # 获取包列表
        mr_packages = mr_data.get("package", [])
        smr_packages = smr_data.get("package", [])
        
        # 更新文件信息中的包数量
        old_file_info["package_count"] = len(mr_packages)
        new_file_info["package_count"] = len(smr_packages)
        
        # 创建包名到包信息的映射
        mr_package_dict = {pkg["name"]: pkg for pkg in mr_packages}
        smr_package_dict = {pkg["name"]: pkg for pkg in smr_packages}
        
        # 获取所有包名
        all_package_names = set(mr_package_dict.keys()) | set(smr_package_dict.keys())
        self.total_packages_compared = len(all_package_names)
        
        # 生成文本报告
        text_result = self._generate_text_report(mr_packages, smr_packages, 
                                               mr_package_dict, smr_package_dict, 
                                               all_package_names)
        
        # 构建变更列表
        changes = []
        summary = {
            "same": 0,
            "modified": 0,
            "added": 0,
            "removed": 0
        }
        
        # 对比每个包
        for package_name in sorted(all_package_names):
            mr_package = mr_package_dict.get(package_name)
            smr_package = smr_package_dict.get(package_name)
            
            change = self._create_package_change(package_name, mr_package, smr_package)
            changes.append(change)
            
            # 更新统计
            if change.change_type == modelsChangeType.SAME:
                summary["same"] += 1
            elif change.change_type == modelsChangeType.MODIFIED:
                summary["modified"] += 1
            elif change.change_type == modelsChangeType.ADDED:
                summary["added"] += 1
            elif change.change_type == modelsChangeType.REMOVED:
                summary["removed"] += 1
        
        # 检查是否完全相同
        is_identical = (summary["same"] == len(all_package_names))
        
        return PackageComparisonResult(
            is_identical=is_identical,
            status="PASS" if is_identical else "FAIL",
            summary=summary,
            changes=changes,
            old_file_stats=old_file_info,
            new_file_stats=new_file_info,
            old_packages=mr_packages,
            new_packages=smr_packages,
            comparison_text=text_result
        )
    
    def _create_package_change(self, package_name: str, mr_package: Optional[Dict], 
                              smr_package: Optional[Dict]) -> PackageChange:
        """创建包变更对象"""
        # 检查包是否存在
        if mr_package is None:
            return PackageChange(
                change_type=modelsChangeType.ADDED,
                package_name=package_name,
                old_package=None,
                new_package=smr_package
            )
        
        if smr_package is None:
            return PackageChange(
                change_type=modelsChangeType.REMOVED,
                package_name=package_name,
                old_package=mr_package,
                new_package=None
            )
        
        # 比较字段
        differences = []
        fields_to_check = [
            ("apk版本号更新", "version_name"),
            ("安装路径", "dir"),
            ("系统权限标志", "system_priv"),
            ("最小SDK", "min_sdk"),
            ("目标SDK", "target_sdk"),
            ("共享安装包权限", "shares_install_packages_permission"),
            ("默认通知访问", "has_default_notification_access"),
            ("是否为活动管理员", "is_active_admin"),
            ("是否为默认无障碍服务", "is_default_accessibility_service")
        ]
        
        for display_name, field_key in fields_to_check:
            mr_value = mr_package.get(field_key)
            smr_value = smr_package.get(field_key)
            
            if mr_value != smr_value:
                differences.append((display_name, mr_value, smr_value))
        
        # 自动扫描所有 list-of-dicts 字段做深层比较（不硬编码字段名）
        all_keys = set(mr_package.keys()) | set(smr_package.keys())
        already_checked = {f[1] for f in fields_to_check}
        for key in sorted(all_keys):
            if key in already_checked:
                continue
            mr_val = mr_package.get(key)
            smr_val = smr_package.get(key)
            # 只在两侧都是 list-of-dicts 时做深层比较
            if isinstance(mr_val, list) or isinstance(smr_val, list):
                mr_list = mr_val if isinstance(mr_val, list) else []
                smr_list = smr_val if isinstance(smr_val, list) else []
                if mr_list or smr_list:
                    # 检查列表元素是否为 dict
                    sample = next((x for x in mr_list + smr_list if x is not None), None)
                    if isinstance(sample, dict):
                        diff = self._deep_compare_permissions_list(mr_list, smr_list)
                        if diff:
                            differences.append((key, diff, None))

        if differences:
            return PackageChange(
                change_type=modelsChangeType.MODIFIED,
                package_name=package_name,
                old_package=mr_package,
                new_package=smr_package,
                differences=differences
            )
        else:
            return PackageChange(
                change_type=modelsChangeType.SAME,
                package_name=package_name,
                old_package=mr_package,
                new_package=smr_package
            )
    
    def _deep_compare_permissions_list(self, mr_perms: List[Dict], smr_perms: List[Dict]) -> Optional[Dict]:
        """通用权限深层比较：动态收集所有字段名，逐字段比较，不硬编码字段列表"""
        if not mr_perms and not smr_perms:
            return None

        # 按权限名称建立字典映射
        mr_map = {p.get("name", ""): p for p in mr_perms}
        smr_map = {p.get("name", ""): p for p in smr_perms}

        mr_names = set(mr_map.keys())
        smr_names = set(smr_map.keys())

        added = sorted(smr_names - mr_names)
        removed = sorted(mr_names - smr_names)

        # 同名权限：动态收集所有字段名，逐字段深层比较
        field_diffs = []
        for perm_name in sorted(mr_names & smr_names):
            mr_perm = mr_map[perm_name]
            smr_perm = smr_map[perm_name]
            # 动态收集两个对象的所有字段名
            all_keys = set(mr_perm.keys()) | set(smr_perm.keys())
            for key in sorted(all_keys):
                mr_val = mr_perm.get(key)
                smr_val = smr_perm.get(key)
                if mr_val != smr_val:
                    field_diffs.append((perm_name, key, mr_val, smr_val))

        if added or removed or field_diffs:
            result = {
                "added": added,
                "removed": removed,
                "field_diffs": field_diffs,
            }
            return result

        return None

    def _compare_permissions_for_change(self, mr_package: Dict, smr_package: Dict) -> Optional[Dict]:
        """比较请求权限列表（使用深层比较）"""
        mr_perms = mr_package.get("requested_permissions", [])
        smr_perms = smr_package.get("requested_permissions", [])
        return self._deep_compare_permissions_list(mr_perms, smr_perms)

    def _compare_defined_permissions_for_change(self, mr_package: Dict, smr_package: Dict) -> Optional[Dict]:
        """比较定义权限列表（使用深层比较）"""
        mr_perms = mr_package.get("defined_permissions", [])
        smr_perms = smr_package.get("defined_permissions", [])
        return self._deep_compare_permissions_list(mr_perms, smr_perms)

    def _compare_requested_roles_for_change(self, mr_package: Dict, smr_package: Dict) -> Optional[Dict]:
        """比较请求角色列表（使用深层比较）"""
        mr_roles = mr_package.get("requested_roles", [])
        smr_roles = smr_package.get("requested_roles", [])
        return self._deep_compare_permissions_list(mr_roles, smr_roles)
    
    def _generate_text_report(self, mr_packages: List[Dict], smr_packages: List[Dict],
                            mr_package_dict: Dict, smr_package_dict: Dict,
                            all_package_names: Set[str]) -> str:
        """生成文本格式的报告"""
        result = "=" * 70 + "\n"
        result += "PACKAGE DEVICEINFO 详细对比报告\n"
        result += "=" * 70 + "\n\n"
        
        # 统计信息
        result += "【统计概览】\n"
        result += f"  MR文件包数量: {len(mr_packages)}\n"
        result += f"  SMR文件包数量: {len(smr_packages)}\n"
        result += f"  对比包总数: {len(all_package_names)}\n"
        
        # 检查是否有包名差异
        mr_only_names = set(mr_package_dict.keys()) - set(smr_package_dict.keys())
        smr_only_names = set(smr_package_dict.keys()) - set(mr_package_dict.keys())
        
        if mr_only_names:
            result += f"  MR独有包数: {len(mr_only_names)}\n"
        if smr_only_names:
            result += f"  SMR独有包数: {len(smr_only_names)}\n"
        
        result += "\n"
        
        # 对比每个包
        for package_name in sorted(all_package_names):
            package_result = self._compare_package_detailed(package_name, 
                                                          mr_package_dict.get(package_name), 
                                                          smr_package_dict.get(package_name))
            if package_result:
                result += package_result
        
        # 总结报告
        result += "\n" + "=" * 70 + "\n"
        result += "对比总结\n"
        result += "=" * 70 + "\n"
        result += f"对比包总数: {self.total_packages_compared}\n"
        result += f"发现差异总数: {self.total_differences}\n"
        
        if self.total_differences == 0:
            result += "✅ 所有包完全相同，无差异发现\n"
        else:
            result += "⚠️  发现差异，请查看上面的详细报告\n"
        
        return result
    
    def _compare_package_detailed(self, package_name: str, mr_package: Optional[Dict], 
                                smr_package: Optional[Dict]) -> str:
        """详细比较单个包的所有关键字段（用于文本报告）"""
        result = f"📦 包名: {package_name}\n"
        result += "-" * 60 + "\n"
        
        # 检查包是否存在
        if mr_package is None:
            result += "❌ 此包仅存在于 SMR 文件中\n"
            result += self._format_package_details(smr_package, "SMR")
            self.differences_found = True
            self.total_differences += 1
            return result + "\n"
        
        if smr_package is None:
            result += "❌ 此包仅存在于 MR 文件中\n"
            result += self._format_package_details(mr_package, "MR")
            self.differences_found = True
            self.total_differences += 1
            return result + "\n"
        
        # 初始化差异计数器和列表
        package_diff_count = 0
        differences = []
        
        # 比较字段
        fields_to_check = [
            ("apk版本号更新", "version_name"),
            ("安装路径", "dir"),
            ("系统权限标志", "system_priv"),
            ("最小SDK", "min_sdk"),
            ("目标SDK", "target_sdk"),
            ("共享安装包权限", "shares_install_packages_permission"),
            ("默认通知访问", "has_default_notification_access"),
            ("是否为活动管理员", "is_active_admin"),
            ("是否为默认无障碍服务", "is_default_accessibility_service")
        ]
        
        for i, (display_name, field_key) in enumerate(fields_to_check, 1):
            diff = self._compare_field(display_name, field_key, mr_package, smr_package)
            if diff:
                differences.append(f"  {i:2d}. {diff}")
                package_diff_count += 1
        
        # 自动扫描所有 list-of-dicts 字段做深层比较（不硬编码字段名）
        item_idx = len(fields_to_check)
        all_keys = set(mr_package.keys()) | set(smr_package.keys())
        already_checked = {f[1] for f in fields_to_check}
        for key in sorted(all_keys):
            if key in already_checked:
                continue
            mr_val = mr_package.get(key)
            smr_val = smr_package.get(key)
            if isinstance(mr_val, list) or isinstance(smr_val, list):
                list_diff = self._compare_permissions_list(key, key, mr_package, smr_package)
                if list_diff:
                    item_idx += 1
                    differences.append(f"  {item_idx:2d}. {key}差异:\n{list_diff}")
                    package_diff_count += 1

        # 输出所有差异
        if differences:
            result += "\n".join(differences) + "\n"
            self.differences_found = True
            self.total_differences += 1
            result += f"\n  此包共发现 {package_diff_count} 处差异\n"
        else:
            result += "✅ 此包所有字段完全相同\n"
        
        return result + "\n"
    
    def _compare_field(self, field_name: str, field_key: str, 
                      mr_package: Dict, smr_package: Dict) -> str:
        """对比单个字段"""
        mr_value = mr_package.get(field_key)
        smr_value = smr_package.get(field_key)
        
        if mr_value != smr_value:
            # 格式化布尔值
            mr_display = str(mr_value)
            smr_display = str(smr_value)
            if isinstance(mr_value, bool):
                mr_display = "是" if mr_value else "否"
            if isinstance(smr_value, bool):
                smr_display = "是" if smr_value else "否"
            
            return f"{field_name}: MR={mr_display}, SMR={smr_display}"
        
        return ""
    
    def _compare_permissions_list(self, list_name: str, list_key: str,
                                 mr_package: Dict, smr_package: Dict) -> str:
        """对比权限列表 - 使用深层比较，动态收集所有字段名逐一比对"""
        mr_perms = mr_package.get(list_key, [])
        smr_perms = smr_package.get(list_key, [])

        # 如果没有权限，直接返回
        if not mr_perms and not smr_perms:
            return ""

        # 使用通用深层比较
        diff = self._deep_compare_permissions_list(mr_perms, smr_perms)
        if diff is None:
            return ""

        result_lines = []

        # 检查权限数量差异
        if len(mr_perms) != len(smr_perms):
            result_lines.append(f"     权限数量: MR={len(mr_perms)}, SMR={len(smr_perms)}")

        # 新增/删除权限
        added = diff.get("added", [])
        removed = diff.get("removed", [])
        field_diffs = diff.get("field_diffs", [])

        if removed:
            result_lines.append(f"     MR独有权限 ({len(removed)}个):")
            for perm in removed[:5]:
                result_lines.append(f"        - {perm}")
            if len(removed) > 5:
                result_lines.append(f"         ... 还有 {len(removed) - 5} 个权限")

        if added:
            result_lines.append(f"     SMR独有权限 ({len(added)}个):")
            for perm in added[:5]:
                result_lines.append(f"        + {perm}")
            if len(added) > 5:
                result_lines.append(f"         ... 还有 {len(added) - 5} 个权限")

        # 同名权限内部字段变更
        if field_diffs:
            # 按权限名分组
            by_perm = {}
            for perm_name, key, mr_val, smr_val in field_diffs:
                if perm_name not in by_perm:
                    by_perm[perm_name] = []
                by_perm[perm_name].append((key, mr_val, smr_val))

            result_lines.append(f"     权限字段变更 ({len(by_perm)}个权限):")
            for perm_name in sorted(by_perm.keys())[:10]:
                changes = by_perm[perm_name]
                for key, mr_val, smr_val in changes:
                    result_lines.append(f"        {perm_name}.{key}: {mr_val} → {smr_val}")
            if len(by_perm) > 10:
                result_lines.append(f"         ... 还有 {len(by_perm) - 10} 个权限有字段变更")

        if not result_lines:
            return ""

        return "     " + "\n     ".join(result_lines)
    
    def _get_permission_name(self, permission: Dict) -> str:
        """从权限字典中获取权限名称"""
        return permission.get("name", "未知权限")
    
    def _format_package_details(self, package: Dict, source: str) -> str:
        """格式化包详细信息"""
        if not package:
            return ""
        
        details = []
        
        # 提取所有关键字段
        fields = [
            ("apk版本号更新", "version_name"),
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
                # 格式化布尔值
                if isinstance(value, bool):
                    formatted_value = "是" if value else "否"
                else:
                    formatted_value = str(value)
                details.append(f"    {display_name}: {formatted_value}")
        
        # 权限信息
        perms = package.get("requested_permissions", [])
        if perms:
            details.append(f"    请求权限数量: {len(perms)}")
        
        return "\n".join(details)
    
    def generate_html_report(self, result: PackageComparisonResult, output_path: str) -> str:
        """生成HTML格式的报告"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 准备数据
        total_old = result.old_file_stats['package_count']
        total_new = result.new_file_stats['package_count']
        summary = result.summary
        
        # 构建HTML
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Package JSON 对比报告</title>
    <style>
        :root {{
            --color-same: #4CAF50;
            --color-modified: #FF9800;
            --color-added: #8BC34A;
            --color-removed: #F44336;
            --color-bg-light: #f8f9fa;
            --color-bg-white: #ffffff;
            --color-border: #dee2e6;
            --color-text: #333;
            --color-text-light: #666;
            --color-diff-red: #ff4444;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--color-text);
            background-color: #f5f7fa;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 10px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        /* 头部样式 */
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.2rem;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        .header .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
            margin-bottom: 15px;
        }}
        
        .timestamp {{
            background: rgba(255,255,255,0.15);
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.9rem;
        }}
        
        /* 结果摘要 */
        .result-summary {{
            padding: 20px 40px;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .result-badge {{
            display: inline-block;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: bold;
        }}
        
        .result-pass {{
            background-color: var(--color-same);
            color: white;
        }}
        
        .result-fail {{
            background-color: var(--color-modified);
            color: white;
        }}
        
        /* 文件信息 */
        .file-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            padding: 30px 40px;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .file-card {{
            background: var(--color-bg-light);
            border-radius: 8px;
            padding: 25px;
            border: 1px solid var(--color-border);
        }}
        
        .file-card.old {{
            border-left: 4px solid var(--color-removed);
        }}
        
        .file-card.new {{
            border-left: 4px solid var(--color-added);
        }}
        
        .file-card h3 {{
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #4A90D9;
        }}
        
        .info-item {{
            margin-bottom: 12px;
            display: flex;
        }}
        
        .info-label {{
            font-weight: 600;
            min-width: 100px;
            color: var(--color-text-light);
        }}
        
        .info-value {{
            color: var(--color-text);
            flex: 1;
            word-break: break-all;
            font-family: 'Consolas', monospace;
            font-size: 0.9rem;
        }}
        
        /* 统计卡片 */
        .stats-section {{
            padding: 30px 40px;
            border-bottom: 1px solid var(--color-border);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-top: 20px;
        }}
        
        .stat-card {{
            text-align: center;
            padding: 25px 15px;
            border-radius: 8px;
            background: var(--color-bg-light);
            border: 1px solid var(--color-border);
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .stat-number {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .stat-same {{ color: var(--color-same); }}
        .stat-modified {{ color: var(--color-modified); }}
        .stat-added {{ color: var(--color-added); }}
        .stat-removed {{ color: var(--color-removed); }}
        
        .stat-label {{
            font-size: 1rem;
            color: var(--color-text-light);
        }}
        
        /* 对比表格 */
        .comparison-section {{
            padding: 30px 40px;
        }}
        
        .section-title {{
            font-size: 1.5rem;
            color: #2c3e50;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 2px solid #4A90D9;
        }}
        
        .legend {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            padding: 15px;
            background: var(--color-bg-light);
            border-radius: 8px;
            border: 1px solid var(--color-border);
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            font-size: 0.9rem;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            margin-right: 8px;
        }}
        
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 0.9rem;
        }}
        
        .comparison-table th {{
            background-color: #f1f5f9;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #2c3e50;
            border-bottom: 2px solid var(--color-border);
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        .comparison-table td {{
            padding: 15px;
            border-bottom: 1px solid var(--color-border);
            vertical-align: top;
        }}
        
        .comparison-table tr:hover {{
            background-color: #f8fafc;
        }}
        
        .index-col {{
            width: 60px;
            text-align: center;
            font-weight: bold;
            color: var(--color-text-light);
        }}
        
        .status-col {{
            width: 100px;
            text-align: center;
        }}
        
        .package-name-col {{
            width: 250px;
        }}
        
        .change-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            color: white;
        }}
        
        .badge-same {{ background-color: var(--color-same); }}
        .badge-modified {{ background-color: var(--color-modified); }}
        .badge-added {{ background-color: var(--color-added); }}
        .badge-removed {{ background-color: var(--color-removed); }}
        
        .package-info {{
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.85rem;
        }}
        
        .package-name {{
            font-weight: bold;
            margin-bottom: 5px;
            color: #2c3e50;
        }}
        
        .package-details {{
            background: var(--color-bg-light);
            padding: 10px;
            border-radius: 5px;
            border: 1px solid var(--color-border);
            margin-top: 5px;
            max-height: 150px;
            overflow-y: auto;
            font-size: 0.8rem;
        }}
        
        .changes-list {{
            margin-top: 10px;
            padding-left: 20px;
        }}
        
        .change-item {{
            margin-bottom: 8px;
            padding: 8px;
            background-color: rgba(255, 68, 68, 0.05);
            border-radius: 4px;
            border-left: 3px solid var(--color-diff-red);
            color: var(--color-text-light);
        }}
        
        .change-old {{
            color: var(--color-diff-red);
            text-decoration: line-through;
            margin-right: 5px;
            font-weight: bold;
        }}
        
        .change-new {{
            color: var(--color-diff-red);
            margin-left: 5px;
            font-weight: bold;
        }}
        
        .arrow {{
            color: var(--color-diff-red);
            margin: 0 5px;
            font-weight: bold;
        }}

        /* 差异字段在MR/SMR列中的高亮样式 */
        .diff-field-item {{
            padding: 3px 5px;
            margin-bottom: 2px;
            border-radius: 3px;
            background-color: rgba(255, 68, 68, 0.08);
            border-left: 3px solid var(--color-diff-red);
        }}

        .diff-field {{
            color: var(--color-diff-red);
            font-weight: bold;
        }}

        /* 控制按钮 */
        .controls {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            border: 1px solid var(--color-border);
            background: rgba(255, 255, 255, 0.7);
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .filter-btn:hover {{
            background: var(--color-bg-light);
        }}
        
        .filter-btn.active {{
            background: #4A90D9;
            color: white;
            border-color: #4A90D9;
        }}
        
        /* 页脚 */
        .footer {{
            text-align: center;
            padding: 20px 40px;
            background-color: var(--color-bg-light);
            color: var(--color-text-light);
            border-top: 1px solid var(--color-border);
            font-size: 0.9rem;
        }}
        
        /* 响应式设计 */
        @media (max-width: 1200px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .file-info {{
                grid-template-columns: 1fr;
            }}
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .header, .file-info, .stats-section, .comparison-section {{
                padding: 20px;
            }}
            
            .comparison-table {{
                font-size: 0.8rem;
            }}
        }}
        
        @media (max-width: 480px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Package JSON 对比报告</h1>
            <div class="subtitle">MR vs SMR 包信息详细对比 - 差异项显示为红色</div>
            <div class="timestamp">生成时间: {now}</div>
        </div>
        
        <div class="result-summary">
'''
        
        if result.is_identical:
            html += f'''            <div class="result-badge result-pass">✅ PASS - 所有包完全相同</div>
'''
        else:
            html += f'''            <div class="result-badge result-fail">❌ 发现差异 - 详细对比如下</div>
'''
        
        html += f'''        </div>
        
        <div class="file-info">
            <div class="file-card old">
                <h3>📁 MR文件 (基准)</h3>
                <div class="info-item">
                    <div class="info-label">文件名:</div>
                    <div class="info-value">{result.old_file_stats['name']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">路径:</div>
                    <div class="info-value">{result.old_file_stats['directory']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">大小:</div>
                    <div class="info-value">{result.old_file_stats['size']:,} 字节</div>
                </div>
                <div class="info-item">
                    <div class="info-label">MD5:</div>
                    <div class="info-value">{result.old_file_stats['md5'][:16]}...</div>
                </div>
                <div class="info-item">
                    <div class="info-label">包数量:</div>
                    <div class="info-value">{total_old} 个</div>
                </div>
            </div>
            
            <div class="file-card new">
                <h3>📁 SMR文件 (对比)</h3>
                <div class="info-item">
                    <div class="info-label">文件名:</div>
                    <div class="info-value">{result.new_file_stats['name']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">路径:</div>
                    <div class="info-value">{result.new_file_stats['directory']}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">大小:</div>
                    <div class="info-value">{result.new_file_stats['size']:,} 字节</div>
                </div>
                <div class="info-item">
                    <div class="info-label">MD5:</div>
                    <div class="info-value">{result.new_file_stats['md5'][:16]}...</div>
                </div>
                <div class="info-item">
                    <div class="info-label">包数量:</div>
                    <div class="info-value">{total_new} 个</div>
                </div>
            </div>
        </div>
        
        <div class="stats-section">
            <h2 class="section-title">📊 变更统计</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number stat-same">{summary.get('same', 0)}</div>
                    <div class="stat-label">相同</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number stat-modified">{summary.get('modified', 0)}</div>
                    <div class="stat-label">修改</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number stat-added">{summary.get('added', 0)}</div>
                    <div class="stat-label">新增</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number stat-removed">{summary.get('removed', 0)}</div>
                    <div class="stat-label">删除</div>
                </div>
            </div>
        </div>
        
        <div class="comparison-section">
            <h2 class="section-title">🔍 详细对比 - <span style="color: var(--color-diff-red);">差异项已标红</span></h2>

            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: var(--color-same);"></div>
                    <span>相同 - 两个文件中完全相同</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: var(--color-modified);"></div>
                    <span>修改 - 内容发生变化</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: var(--color-diff-red);"></div>
                    <span><strong>差异项 - 显示为红色</strong></span>
                </div>
            </div>
            
            <div class="controls">
                <button class="filter-btn active" onclick="filterChanges('all')">显示全部</button>
                <button class="filter-btn" onclick="filterChanges('same')">仅显示相同</button>
                <button class="filter-btn" onclick="filterChanges('modified')">仅显示修改</button>
                <button class="filter-btn" onclick="filterChanges('added')">仅显示新增</button>
                <button class="filter-btn" onclick="filterChanges('removed')">仅显示删除</button>
            </div>
            
            <table class="comparison-table" id="comparison-table">
                <thead>
                    <tr>
                        <th class="index-col">#</th>
                        <th class="status-col">状态</th>
                        <th class="package-name-col">包名</th>
                        <th>MR版本</th>
                        <th>SMR版本</th>
                        <th>变更详情</th>
                    </tr>
                </thead>
                <tbody>
'''
        
        # 生成表格行
        for i, change in enumerate(result.changes):
            # 确定状态类名和显示文本
            status_class = f"badge-{change.change_type.value}"
            status_text = {
                "same": "相同",
                "modified": "修改",
                "added": "新增",
                "removed": "删除"
            }.get(change.change_type.value, change.change_type.value)
            
            # MR版本信息
            mr_info = ""
            if change.old_package:
                # 构建差异信息：字段名 → 具体差异数据
                mr_diff_info = {}
                if change.differences:
                    for field, old_val, new_val in change.differences:
                        mr_diff_info[field] = old_val
                formatted_mr = self._format_package_for_html(change.old_package, diff_info=mr_diff_info, is_mr_side=True)
                mr_info = f'''
                    <div class="package-info">
                        <div class="package-details">{formatted_mr}</div>
                    </div>
                '''

            # SMR版本信息
            smr_info = ""
            if change.new_package:
                smr_diff_info = {}
                if change.differences:
                    for field, old_val, new_val in change.differences:
                        smr_diff_info[field] = new_val if not isinstance(old_val, dict) else old_val
                formatted_smr = self._format_package_for_html(change.new_package, diff_info=smr_diff_info, is_mr_side=False)
                smr_info = f'''
                    <div class="package-info">
                        <div class="package-details">{formatted_smr}</div>
                    </div>
                '''
            
            # 变更详情
            change_details = ""
            if change.differences:
                change_details = '<div class="changes-list">'
                for field, old_val, new_val in change.differences:
                    # 特殊处理权限字段（list-of-dicts）- 显示具体新增/移除/字段变更
                    if isinstance(old_val, dict):
                        removed_perms = old_val.get("removed", [])
                        added_perms = old_val.get("added", [])
                        field_diffs = old_val.get("field_diffs", [])
                        perm_parts = []
                        if removed_perms:
                            removed_html = ", ".join(f'<span class="diff-field">{p}</span>' for p in removed_perms)
                            perm_parts.append(f'<span>MR移除权限: {removed_html}</span>')
                        if added_perms:
                            added_html = ", ".join(f'<span class="diff-field">{p}</span>' for p in added_perms)
                            perm_parts.append(f'<span>SMR新增权限: {added_html}</span>')
                        # 显示字段级变更
                        if field_diffs:
                            for fd in field_diffs[:20]:  # 最多显示20条
                                pname, fkey, mv, sv = fd
                                perm_parts.append(f'<span>{pname}.<span class="diff-field">{fkey}</span>: <span class="change-old">{mv}</span> <span class="arrow">→</span> <span class="change-new">{sv}</span></span>')
                            if len(field_diffs) > 20:
                                perm_parts.append(f'<span>... 还有 {len(field_diffs) - 20} 处字段变更</span>')
                        perm_detail = "<br>".join(perm_parts)
                        change_details += f'''
                            <div class="change-item">
                                <span class="change-field">{field}:</span><br>
                                {perm_detail}
                            </div>
                        '''
                    else:
                        old_str = self._format_value_for_html(old_val)
                        new_str = self._format_value_for_html(new_val)
                        change_details += f'''
                            <div class="change-item">
                                <span class="change-field">{field}:</span>
                                <span class="change-old">{old_str}</span>
                                <span class="arrow">→</span>
                                <span class="change-new">{new_str}</span>
                            </div>
                        '''
                change_details += '</div>'
            
            html += f'''
                    <tr class="change-row" data-change-type="{change.change_type.value}">
                        <td class="index-col">{i+1}</td>
                        <td class="status-col">
                            <span class="change-badge {status_class}">{status_text}</span>
                        </td>
                        <td class="package-name-col">
                            <div class="package-name">{change.package_name}</div>
                        </td>
                        <td>{mr_info}</td>
                        <td>{smr_info}</td>
                        <td>{change_details}</td>
                    </tr>
'''
        
        html += '''
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>生成时间: ''' + now + ''' | 对比算法: PackageComparator | 版本: 2.0</p>
            <p style="margin-top: 5px; font-size: 0.8rem; color: #888;">
                说明：此报告比较两个JSON文件中的package信息，<strong style="color: var(--color-diff-red);">差异项已用红色突出显示</strong>。
            </p>
        </div>
    </div>
    
    <script>
        // 过滤功能
        function filterChanges(type) {
            const rows = document.querySelectorAll('.change-row');
            const buttons = document.querySelectorAll('.filter-btn');
            
            // 更新按钮状态
            buttons.forEach(btn => {
                if (btn.textContent.includes(type) || (type === 'all' && btn.textContent.includes('全部'))) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            
            // 显示/隐藏行
            rows.forEach(row => {
                if (type === 'all') {
                    row.style.display = '';
                } else {
                    const rowType = row.getAttribute('data-change-type');
                    if (rowType === type) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            });
        }
        
        // 默认展开所有行
        document.addEventListener('DOMContentLoaded', function() {
            // 可以添加其他初始化代码
        });
        
        // 点击包详情展开/收起
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('package-name')) {
                const details = e.target.nextElementSibling;
                if (details.style.display === 'none') {
                    details.style.display = 'block';
                } else {
                    details.style.display = 'none';
                }
            }
        });
    </script>
</body>
</html>'''
        
        # 保存HTML文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            return f"HTML报告已生成: {output_path}"
        except Exception as e:
            return f"生成HTML报告失败: {e}"
    
    def _format_package_for_html(self, package: Dict, diff_info: dict = None, is_mr_side: bool = True) -> str:
        """格式化包信息用于HTML显示，支持差异字段标红，权限逐个标红"""
        if not package:
            return ""

        if diff_info is None:
            diff_info = {}

        lines = []

        # 关键字段
        fields = [
            ("apk版本号更新", "version_name"),
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
                formatted_value = self._format_value_for_html(value)

                if display_name in diff_info:
                    lines.append(f"<div class='diff-field-item'><b>{display_name}:</b> <span class='diff-field'>{formatted_value}</span></div>")
                else:
                    lines.append(f"<b>{display_name}:</b> {formatted_value}")

        # 自动扫描所有 list-of-dicts 字段，逐个权限标红（不硬编码字段名）
        scalar_fields = {f[1] for f in fields}
        for key in sorted(package.keys()):
            if key in scalar_fields:
                continue
            val = package.get(key)
            if not isinstance(val, list) or not val:
                continue
            if not isinstance(val[0], dict):
                continue

            perm_names = [p.get("name", "未知权限") for p in val]
            perm_count = len(perm_names)

            if key in diff_info:
                perm_diff = diff_info[key]
                if isinstance(perm_diff, dict):
                    removed_set = set(perm_diff.get("removed", []))
                    added_set = set(perm_diff.get("added", []))
                    field_diff_names = set(fd[0] for fd in perm_diff.get("field_diffs", []))

                    highlighted = []
                    for pname in perm_names:
                        if is_mr_side:
                            is_changed = pname in removed_set or pname in field_diff_names
                        else:
                            is_changed = pname in added_set or pname in field_diff_names
                        if is_changed:
                            highlighted.append(f"<span class='diff-field'>{pname}</span>")
                        else:
                            highlighted.append(pname)

                    perm_str = ", ".join(highlighted)
                    perm_display = f"{perm_count}个 ({perm_str})"
                    lines.append(f"<div class='diff-field-item'><b>{key}:</b> {perm_display}</div>")
                else:
                    perm_display = f"{perm_count}个"
                    if perm_count <= 5:
                        perm_display += f" ({', '.join(perm_names)})"
                    else:
                        perm_display += f" ({', '.join(perm_names[:5])}...)"
                    lines.append(f"<div class='diff-field-item'><b>{key}:</b> {perm_display}</div>")
            else:
                perm_display = f"{perm_count}个"
                if perm_count <= 5:
                    perm_display += f" ({', '.join(perm_names)})"
                else:
                    perm_display += f" ({', '.join(perm_names[:5])}...)"
                lines.append(f"<b>{key}:</b> {perm_display}")

        return "<br>".join(lines)
    
    def _format_value_for_html(self, value: Any) -> str:
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
