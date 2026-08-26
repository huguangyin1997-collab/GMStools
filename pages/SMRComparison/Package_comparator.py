# Package_comparator.py
from typing import Dict, List, Set, Optional, Tuple, Any
from .Package_models import PackageChangeType, PackageChange, PackageComparisonResult
from .Package_file_utils import FileUtils


class PackageComparator:
    """Package JSON文件对比器 - 支持HTML报告"""
    
    def __init__(self):
        self.differences_found = False
        self.total_differences = 0
        self.total_packages_compared = 0
        self.comparison_result = None
        self.file_utils = FileUtils()
    
    def compare_files(self, mr_file_path: str, smr_file_path: str) -> PackageComparisonResult:
        """比较两个Package JSON文件，返回结构化结果"""
        # 重置统计
        self.differences_found = False
        self.total_differences = 0
        self.total_packages_compared = 0
        
        # 加载数据
        mr_data = self.file_utils.load_json_file(mr_file_path)
        smr_data = self.file_utils.load_json_file(smr_file_path)
        
        if mr_data is None or smr_data is None:
            return self._create_error_result(mr_file_path, smr_file_path)
        
        # 执行比较
        result = self._compare_structured(mr_data, smr_data, mr_file_path, smr_file_path)
        self.comparison_result = result
        return result
    
    def _create_error_result(self, mr_file_path: str, smr_file_path: str) -> PackageComparisonResult:
        """创建错误结果"""
        old_info = self.file_utils.get_file_info(mr_file_path)
        new_info = self.file_utils.get_file_info(smr_file_path)
        
        return PackageComparisonResult(
            is_identical=False,
            status="FAIL",
            summary={},
            changes=[],
            old_file_stats=old_info,
            new_file_stats=new_info,
            old_packages=[],
            new_packages=[],
            comparison_text="无法比较：文件加载失败\n"
        )
    
    def _compare_structured(self, mr_data: Dict, smr_data: Dict, 
                          mr_file_path: str, smr_file_path: str) -> PackageComparisonResult:
        """结构化比较两个Package数据"""
        # 获取包列表
        mr_packages = mr_data.get("package", [])
        smr_packages = smr_data.get("package", [])
        
        # 获取文件信息
        old_file_info = self.file_utils.get_file_info(mr_file_path, len(mr_packages))
        new_file_info = self.file_utils.get_file_info(smr_file_path, len(smr_packages))
        
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
            if change.change_type == PackageChangeType.SAME:
                summary["same"] += 1
            elif change.change_type == PackageChangeType.MODIFIED:
                summary["modified"] += 1
            elif change.change_type == PackageChangeType.ADDED:
                summary["added"] += 1
            elif change.change_type == PackageChangeType.REMOVED:
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
                change_type=PackageChangeType.ADDED,
                package_name=package_name,
                old_package=None,
                new_package=smr_package,
                differences=[]
            )
        
        if smr_package is None:
            return PackageChange(
                change_type=PackageChangeType.REMOVED,
                package_name=package_name,
                old_package=mr_package,
                new_package=None,
                differences=[]
            )
        
        # 比较字段
        differences = []
        fields_to_check = [
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
                change_type=PackageChangeType.MODIFIED,
                package_name=package_name,
                old_package=mr_package,
                new_package=smr_package,
                differences=differences
            )
        else:
            return PackageChange(
                change_type=PackageChangeType.SAME,
                package_name=package_name,
                old_package=mr_package,
                new_package=smr_package,
                differences=[]
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
            all_keys = set(mr_perm.keys()) | set(smr_perm.keys())
            for key in sorted(all_keys):
                mr_val = mr_perm.get(key)
                smr_val = smr_perm.get(key)
                if mr_val != smr_val:
                    field_diffs.append((perm_name, key, mr_val, smr_val))

        if added or removed or field_diffs:
            return {
                "added": added,
                "removed": removed,
                "field_diffs": field_diffs,
            }

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
                    result_lines.append(f"        {perm_name}.{key}: {mr_val} -> {smr_val}")
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