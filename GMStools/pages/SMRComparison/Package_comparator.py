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
        
        # 比较权限列表
        perms_diff = self._compare_permissions_for_change(mr_package, smr_package)
        if perms_diff:
            differences.append(("请求的权限", perms_diff[0], perms_diff[1]))
        
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
    
    def _compare_permissions_for_change(self, mr_package: Dict, smr_package: Dict) -> Optional[Tuple[str, str]]:
        """比较权限列表，返回差异摘要"""
        mr_perms = mr_package.get("requested_permissions", [])
        smr_perms = smr_package.get("requested_permissions", [])
        
        if mr_perms == smr_perms:
            return None
        
        # 获取权限摘要
        mr_summary = self.file_utils.format_permission_summary(mr_perms)
        smr_summary = self.file_utils.format_permission_summary(smr_perms)
        
        return (mr_summary, smr_summary)
    
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
        
        # 对比权限列表
        requested_perms_diff = self._compare_permissions_list("请求的权限", "requested_permissions", 
                                                            mr_package, smr_package)
        if requested_perms_diff:
            differences.append(f"  {len(fields_to_check)+1:2d}. 请求的权限差异:\n{requested_perms_diff}")
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
        """对比权限列表"""
        mr_perms = mr_package.get(list_key, [])
        smr_perms = smr_package.get(list_key, [])
        
        # 如果没有权限，直接返回
        if not mr_perms and not smr_perms:
            return ""
        
        result_lines = []
        
        # 检查权限数量差异
        if len(mr_perms) != len(smr_perms):
            result_lines.append(f"     权限数量: MR={len(mr_perms)}, SMR={len(smr_perms)}")
        
        # 创建权限名映射
        mr_perm_dict = {self._get_permission_name(perm): perm for perm in mr_perms}
        smr_perm_dict = {self._get_permission_name(perm): perm for perm in smr_perms}
        
        all_perm_names = set(mr_perm_dict.keys()) | set(smr_perm_dict.keys())
        
        # 检查缺失的权限
        missing_in_mr = sorted([p for p in all_perm_names if p not in mr_perm_dict])
        missing_in_smr = sorted([p for p in all_perm_names if p not in smr_perm_dict])
        
        if missing_in_mr:
            result_lines.append(f"     MR缺失权限 ({len(missing_in_mr)}个):")
            for perm in missing_in_mr[:5]:  # 只显示前5个，避免过长
                result_lines.append(f"        - {perm}")
            if len(missing_in_mr) > 5:
                result_lines.append(f"         ... 还有 {len(missing_in_mr) - 5} 个权限")
        
        if missing_in_smr:
            result_lines.append(f"     SMR缺失权限 ({len(missing_in_smr)}个):")
            for perm in missing_in_smr[:5]:
                result_lines.append(f"        - {perm}")
            if len(missing_in_smr) > 5:
                result_lines.append(f"         ... 还有 {len(missing_in_smr) - 5} 个权限")
        
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