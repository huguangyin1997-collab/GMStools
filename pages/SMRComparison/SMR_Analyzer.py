import os
import sys
from datetime import datetime
from .SMR_FileUtils import SMR_FileUtils
from .BCompare_Feature import FeatureComparator
from .BCompare_Package import PackageComparator
from .SMR_InfoExtractor import SMR_InfoExtractor
from .SMR_Comparator import SMR_Comparator
from .SMR_ReportGenerator import SMR_ReportGenerator
from .SMR_PatchChecker import SMR_PatchChecker


class SMR_Analyzer:
    """SMR对比分析器 - 主控制器"""
    
    def __init__(self):
        """
        初始化分析器（不再使用网络时间参数）
        """
        self.file_utils = SMR_FileUtils()
        self.feature_comparator = FeatureComparator()
        self.package_comparator = PackageComparator()
        self.info_extractor = SMR_InfoExtractor(self.file_utils)
        self.comparator = SMR_Comparator(self.file_utils)
        self.report_generator = SMR_ReportGenerator()
        self.patch_checker = SMR_PatchChecker()  # 不再传递参数
    
    def analyze_directories(self, mr_dir, smr_dir):
        """分析两个目录中的JSON文件"""
        # 检查目录是否存在
        if not os.path.exists(mr_dir):
            return None, f"错误: MR报告目录不存在\n目录: {mr_dir}"
        
        if not os.path.exists(smr_dir):
            return None, f"错误: SMR报告目录不存在\n目录: {smr_dir}"
        
        try:
            # 开始分析
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 获取安全补丁日期
            mr_security_patch = self.info_extractor.extract_security_patch(mr_dir)
            smr_security_patch = self.info_extractor.extract_security_patch(smr_dir)
            
            # 获取详细的验证结果
            strict_patch_result = self.patch_checker.compare_patches(
                mr_security_patch, smr_security_patch
            )
            
            # 获取MR报告的Fingerprint和SMR的GenericDeviceInfo信息
            mr_fingerprint = self.info_extractor.extract_fingerprint_from_html(mr_dir)
            smr_generic_info = self.info_extractor.extract_generic_info(smr_dir)
            
            # 分析MR报告文件（用于日志记录，不在GUI显示）
            mr_report_info = self.info_extractor.analyze_report_files(
                "MR报告", mr_dir, "MR", mr_security_patch, mr_fingerprint
            )
            
            # 分析SMR报告文件（用于日志记录，不在GUI显示）
            smr_report_info = self.info_extractor.analyze_report_files(
                "SMR报告", smr_dir, "SMR", smr_security_patch, smr_generic_info
            )
            
            # 执行对比分析，返回三个值：对比文本、所有检查结果、警告字典
            comparison_text, all_check_results, warnings_dict = self._perform_comparison_analysis(
                mr_dir, smr_dir, 
                mr_security_patch, smr_security_patch,
                mr_fingerprint, smr_generic_info,
                strict_patch_result
            )
            
            # 生成最终综合判定结果
            final_verdict_text = self._add_final_comprehensive_verdict(strict_patch_result, all_check_results, warnings_dict)
            
            # 创建完整的分析日志（不包含final_verdict_text，只包含分析过程的详细信息）
            complete_log = f"分析开始时间: {current_time}\n"
            complete_log += "=" * 50 + "\n"
            complete_log += mr_report_info
            complete_log += smr_report_info
            complete_log += comparison_text
            complete_log += f"\n分析完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 将最终判定结果返回到错误信息区域
            return complete_log, final_verdict_text
            
        except Exception as e:
            # 捕获分析过程中的异常
            error_msg = f"分析过程中发生错误:\n{str(e)}"
            import traceback
            error_details = traceback.format_exc()
            print(f"详细错误信息:\n{error_details}")  # 调试信息
            return None, error_msg
    
    def _perform_comparison_analysis(self, mr_dir, smr_dir, mr_security_patch, 
                                    smr_security_patch, mr_fingerprint, smr_generic_info,
                                    strict_patch_result):
        """执行对比分析，返回分析文本、所有检查结果和警告字典"""
        result_text = "对比分析结果:\n"
        result_text += "-" * 30 + "\n"
        
        # 初始化警告字典
        warnings_dict = {}
        
        # 安全补丁对比 - 使用严格验证结果
        security_patch_result = "PASS" if strict_patch_result['all_checks_passed'] else "FAIL"
        result_text += "安全补丁日期对比:\n"
        result_text += f"  MR安全补丁:  {mr_security_patch}\n"
        result_text += f"  SMR安全补丁: {smr_security_patch}\n"
        result_text += f"  参考时间: {self.patch_checker.reference_time.strftime('%Y-%m-%d %H:%M:%S')} ({self.patch_checker.time_message})\n"
        
        if strict_patch_result['all_checks_passed']:
            if strict_patch_result.get('has_warning', False):
                # 收集警告信息
                warning_msg = ""
                if strict_patch_result['smr'].get('warning'):
                    warning_msg = strict_patch_result['smr']['message']
                elif strict_patch_result['mr'].get('warning'):
                    warning_msg = strict_patch_result['mr']['message']
                else:
                    warning_msg = "安全补丁存在警告（超过30天但未超过40天）"
                warnings_dict["安全补丁"] = warning_msg
                
                result_text += "  ⚠️ PASS with warning: 安全补丁检查通过但存在警告（请查看详细信息）\n"
                if strict_patch_result['smr'].get('warning'):
                    result_text += f"      SMR警告: {strict_patch_result['smr']['message']}\n"
                if strict_patch_result['mr'].get('warning'):
                    result_text += f"      MR警告: {strict_patch_result['mr']['message']}\n"
            else:
                result_text += "  ✅ PASS: 所有安全补丁检查通过\n"
        else:
            result_text += "  ❌ FAIL: 安全补丁检查未通过\n"
            # 显示失败原因
            fail_reasons = []
            if not strict_patch_result['mr']['is_valid']:
                fail_reasons.append(f"MR: {strict_patch_result['mr']['message']}")
            if not strict_patch_result['smr']['is_valid']:
                fail_reasons.append(f"SMR: {strict_patch_result['smr']['message']}")
            if not strict_patch_result['comparison']['is_valid']:
                fail_reasons.append(f"对比: {strict_patch_result['comparison']['message']}")
            if fail_reasons:
                result_text += "    失败原因:\n"
                for reason in fail_reasons:
                    result_text += f"      - {reason}\n"
        
        result_text += "\n"
        
        # GMS包版本对比
        mr_gms_version = self.info_extractor.extract_gms_version(mr_dir)
        smr_gms_version = self.info_extractor.extract_gms_version(smr_dir)
        gms_result = "PASS" if mr_gms_version == smr_gms_version else "FAIL"
        
        result_text += "GMS包版本对比:\n"
        result_text += f"  MR GMS包版本:   {mr_gms_version}\n"
        result_text += f"  SMR GMS包版本:  {smr_gms_version}\n"
        if gms_result == "PASS":
            result_text += "  ✅ PASS: GMS包版本严格相等\n"
        else:
            result_text += "  ❌ FAIL: GMS包版本不相等\n"
            result_text += "     注意: GMS包版本不一致，不能走SMR流程\n"
        result_text += "\n"
        
        # Mainline版本对比
        mr_mainline_info = self.info_extractor.extract_mainline_version(mr_dir)
        smr_mainline_info = self.info_extractor.extract_mainline_version(smr_dir)
        
        mainline_result = "PASS"
        if mr_mainline_info["type"] != smr_mainline_info["type"]:
            mainline_result = "FAIL"
            mainline_message = f"类型不一致: MR是{mr_mainline_info['type']}，SMR是{smr_mainline_info['type']}"
        elif mr_mainline_info["version"] != smr_mainline_info["version"]:
            mainline_result = "FAIL"
            mainline_message = f"版本不一致: MR={mr_mainline_info['version']}，SMR={smr_mainline_info['version']}"
        elif mr_mainline_info["version"] == "未找到" or smr_mainline_info["version"] == "未找到":
            mainline_result = "FAIL"
            mainline_message = "未找到Mainline版本信息"
        else:
            mainline_message = "类型和版本都严格一致"
        
        result_text += "Mainline版本对比:\n"
        result_text += f"  MR Mainline:  {mr_mainline_info['type']} - {mr_mainline_info['module_name']} - {mr_mainline_info['version']}\n"
        result_text += f"  SMR Mainline: {smr_mainline_info['type']} - {smr_mainline_info['module_name']} - {smr_mainline_info['version']}\n"
        if mainline_result == "PASS":
            result_text += f"  ✅ PASS: {mainline_message}\n"
        else:
            result_text += f"  ❌ FAIL: {mainline_message}\n"
        result_text += "\n"
        
        # 对比Fingerprint信息
        fingerprint_result_text, fingerprint_result = self.comparator.compare_fingerprint_info(
            mr_fingerprint, smr_generic_info
        )
        result_text += fingerprint_result_text + "\n"
        
        # 收集所有检查结果 - 注意：不包含"安全补丁"，因为我们会单独处理
        all_check_results = {
            "Base_OS Fingerprint": fingerprint_result,
            "GMS包版本": gms_result,
            "Mainline版本": mainline_result
        }
        
        # 初始化feature和package结果状态
        feature_result_status = "PASS"
        package_result_status = "PASS"
        
        # 检查文件是否存在
        file_check = self.comparator.check_file_existence(mr_dir, smr_dir)
        
        if file_check["missing_files"]:
            result_text += "警告: 以下文件未找到:\n"
            for missing_file in file_check["missing_files"]:
                result_text += f"  - {missing_file}\n"
            result_text += "\n"
            
            feature_result_status = "FAIL"
            package_result_status = "FAIL"
            feature_result_text = ""
            package_summary_text = ""
        else:
            result_text += "✓ 所有目标文件都已找到\n\n"
            
            # 对比Feature文件
            feature_result_status, feature_result_text = self._compare_feature_files(
                file_check["mr_feature_file"], file_check["smr_feature_file"]
            )
            result_text += feature_result_text + "\n" + "=" * 50 + "\n\n"
            
            # 对比Package文件
            package_result_status, package_summary_text = self._compare_package_files(
                file_check["mr_package_file"], file_check["smr_package_file"]
            )
            result_text += package_summary_text + "\n" + "=" * 50 + "\n\n"
        
        # 添加Feature和Package结果到检查结果中
        all_check_results["Feature DeviceInfo"] = feature_result_status
        all_check_results["Package DeviceInfo"] = package_result_status
        
        return result_text, all_check_results, warnings_dict
    
    def _add_final_comprehensive_verdict(self, strict_patch_result, all_check_results=None, warnings_dict=None):
        """添加最终综合判定结果（按照要求的格式）"""
        if warnings_dict is None:
            warnings_dict = {}
            
        result = "=" * 50 + "\n"
        result += "最终综合判定结果: "
        
        # 判断是否能走SMR
        can_pass_smr = True
        
        # 1. 检查安全补丁
        if not strict_patch_result['all_checks_passed']:
            can_pass_smr = False
        
        # 2. 检查其他检查项
        if all_check_results:
            for check_result in all_check_results.values():
                if check_result == "FAIL":
                    can_pass_smr = False
                    break
        
        # 输出判定结果
        if can_pass_smr:
            if warnings_dict:
                result += "⚠️ 能走smr（存在警告项）\n"
            else:
                result += "✅ 能走smr\n"
        else:
            result += "❌ 不能走smr\n"
        
        result += "=" * 50 + "\n"
        
        # 显示所有检查项结果
        result += "所有检查项结果:\n"
        result += "=" * 50 + "\n"
        
        # 安全补丁检查结果（带警告处理）
        if strict_patch_result['all_checks_passed']:
            if strict_patch_result.get('has_warning', False):
                warning_msg = warnings_dict.get("安全补丁", "存在警告")
                result += f"⚠️ 安全补丁: PASS ({warning_msg})\n"
            else:
                result += "✅ 安全补丁: PASS\n"
        else:
            result += "❌ 安全补丁: FAIL\n"
        
        # 其他检查项结果
        if all_check_results:
            # 按特定顺序显示检查项
            display_order = [
                "Base_OS Fingerprint",
                "GMS包版本", 
                "Mainline版本",
                "Feature DeviceInfo",
                "Package DeviceInfo"
            ]
            
            # 先按指定顺序显示
            processed_checks = set()
            for check_name in display_order:
                if check_name in all_check_results:
                    check_result = all_check_results[check_name]
                    # 检查是否有警告（目前只有安全补丁有，其他项可扩展）
                    warning_msg = warnings_dict.get(check_name, "")
                    if warning_msg:
                        result += f"⚠️ {check_name}: {check_result} ({warning_msg})\n"
                    else:
                        if check_result == "PASS":
                            result += f"✅ {check_name}: PASS\n"
                        elif check_result == "FAIL":
                            result += f"❌ {check_name}: FAIL\n"
                    processed_checks.add(check_name)
            
            # 显示其他未在指定顺序中的检查项
            for check_name, check_result in all_check_results.items():
                if check_name not in processed_checks:
                    warning_msg = warnings_dict.get(check_name, "")
                    if warning_msg:
                        result += f"⚠️ {check_name}: {check_result} ({warning_msg})\n"
                    else:
                        if check_result == "PASS":
                            result += f"✅ {check_name}: PASS\n"
                        elif check_result == "FAIL":
                            result += f"❌ {check_name}: FAIL\n"
        
        result += "=" * 50
        return result
    
    def _compare_feature_files(self, mr_feature_file, smr_feature_file):
        """对比Feature文件"""
        feature_result_status = "未知"
        
        # 读取JSON数据
        mr_feature_data = self.file_utils.read_json_file(mr_feature_file)
        smr_feature_data = self.file_utils.read_json_file(smr_feature_file)
        
        if mr_feature_data and smr_feature_data:
            feature_result_text = self.feature_comparator.compare(mr_feature_data, smr_feature_data)
            
            # 从Feature对比结果中提取状态
            if "失败" in feature_result_text or "FAIL" in feature_result_text:
                feature_result_status = "FAIL"
            elif "成功" in feature_result_text or "PASS" in feature_result_text:
                feature_result_status = "PASS"
            else:
                feature_result_status = "未知"
        else:
            feature_result_text = "Feature文件读取失败"
            feature_result_status = "FAIL"
        
        return feature_result_status, feature_result_text
    
    def _compare_package_files(self, mr_package_file, smr_package_file):
        """对比Package文件"""
        try:
            # 使用新的compare_files方法
            package_result_obj = self.package_comparator.compare_files(mr_package_file, smr_package_file)
            
            # 生成详细的差异包列表
            package_summary_text, package_overall_result = self._generate_detailed_package_summary(package_result_obj)
            
            # 生成HTML报告
            output_dir = os.path.join(os.getcwd(), "comparison_reports")
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"Package_Comparison_{timestamp}.html")
            
            # 生成HTML报告
            html_report_info = self.package_comparator.generate_html_report(package_result_obj, output_path)
            package_summary_text += f"\n{html_report_info}\n"
            
            return package_overall_result, package_summary_text
            
        except Exception as e:
            error_text = f"Package文件对比失败: {str(e)}\n"
            return "FAIL", error_text
    
    def _generate_detailed_package_summary(self, package_result_obj):
        """生成详细的差异包列表"""
        summary = package_result_obj.summary
        
        result = "=" * 70 + "\n"
        result += "PACKAGE DEVICEINFO 详细差异包列表\n"
        result += "=" * 70 + "\n\n"
        
        # 统计信息
        result += "【统计概览】\n"
        result += f"  MR文件包数量: {len(package_result_obj.old_packages)}\n"
        result += f"  SMR文件包数量: {len(package_result_obj.new_packages)}\n"
        result += f"  对比包总数: {len(package_result_obj.changes)}\n\n"
        
        # 变更统计
        result += "【变更统计】\n"
        result += f"  相同: {summary.get('same', 0)} 个包\n"
        result += f"  修改: {summary.get('modified', 0)} 个包\n"
        result += f"  新增: {summary.get('added', 0)} 个包\n"
        result += f"  删除: {summary.get('removed', 0)} 个包\n\n"
        
        # 获取所有有差异的包
        modified_packages = [change for change in package_result_obj.changes 
                            if change.change_type.name != "SAME"]
        
        # 定义关注字段映射
        special_fields = {
            "最小SDK": "min_sdk",
            "目标SDK": "target_sdk",
            "共享安装包权限": "shares_install_packages_permission",
            "默认通知访问": "has_default_notification_access",
            "是否为活动管理员": "is_active_admin",
            "是否为默认无障碍服务": "is_default_accessibility_service"
        }
        
        # 定义字段显示名称
        field_display_names = {
            "apk版本号": "apk版本号",
            "最小SDK": "最小SDK",
            "目标SDK": "目标SDK",
            "共享安装包权限": "共享安装包权限",
            "默认通知访问": "通知访问更新",
            "是否为活动管理员": "活动管理员更新",
            "是否为默认无障碍服务": "无障碍服务更新"
        }
        
        # 判断整体结果
        added_pkgs = [p for p in modified_packages if p.change_type.name == "ADDED"]
        removed_pkgs = [p for p in modified_packages if p.change_type.name == "REMOVED"]
        
        # 检查是否有系统级应用权限变更
        has_system_permission_change = False
        system_permission_changes_count = 0
        
        for change in modified_packages:
            if change.change_type.name == "MODIFIED":
                old_pkg = change.old_package
                # 检查是否有权限变更
                has_permission_change = False
                for diff in change.differences:
                    if diff[0] == "请求的权限":
                        has_permission_change = True
                        break
                
                is_system = old_pkg.get("system_priv", False) if old_pkg else False
                if has_permission_change and is_system:
                    has_system_permission_change = True
                    system_permission_changes_count += 1
        
        # 判断整体结果
        overall_result = "PASS"
        if len(added_pkgs) > 0 or len(removed_pkgs) > 0 or has_system_permission_change:
            overall_result = "FAIL"
        
        result += f"【整体判定结果】: {overall_result}\n"
        if overall_result == "FAIL":
            result += f"  原因: "
            reasons = []
            if len(added_pkgs) > 0:
                reasons.append(f"新增{len(added_pkgs)}个apk")
            if len(removed_pkgs) > 0:
                reasons.append(f"删除{len(removed_pkgs)}个apk")
            if has_system_permission_change:
                reasons.append(f"有{system_permission_changes_count}个系统级应用权限变更")
            result += "，".join(reasons) + "\n"
        result += "\n"
        
        if not modified_packages:
            result += "✅ 所有包都相同，没有发现任何差异\n"
            result += "\n" + "=" * 70 + "\n"
            return result, overall_result
        
        # 分类处理不同的变更类型
        modified_pkgs = [p for p in modified_packages if p.change_type.name == "MODIFIED"]
        
        # 在修改的包中，进一步分类：
        # 1. 有权限变更的包（分为系统级和非系统级）
        # 2. 没有权限变更但有其他字段变更的包
        
        # 权限变更的包
        permission_changes = []
        for change in modified_pkgs:
            # 检查是否有权限变更
            has_permission_change = False
            for diff in change.differences:
                if diff[0] == "请求的权限":
                    has_permission_change = True
                    break
            
            if has_permission_change:
                permission_changes.append(change)
        
        # 将权限变更包分为系统级和非系统级
        non_system_permission_changes = []
        system_permission_changes = []
        
        for change in permission_changes:
            old_pkg = change.old_package
            is_system = old_pkg.get("system_priv", False) if old_pkg else False
            
            if is_system:
                system_permission_changes.append(change)
            else:
                non_system_permission_changes.append(change)
        
        # 输出非系统级应用权限变更
        if non_system_permission_changes:
            result += "非系统级应用权限变更\n"
            for i, change in enumerate(non_system_permission_changes, 1):
                old_pkg = change.old_package
                new_pkg = change.new_package
                
                result += f"第{i}个\n"
                result += f"包名:{change.package_name}\n"
                
                # 获取版本信息
                old_version = old_pkg.get("version_name", "未知") if old_pkg else "未知"
                new_version = new_pkg.get("version_name", "未知") if new_pkg else "未知"
                if old_version != new_version:
                    result += f"apk版本号更新: {old_version} → {new_version}\n"
                else:
                    result += f"apk版本号: {old_version}\n"
                
                # 检查是否有实际的权限变更
                old_permissions = old_pkg.get("requested_permissions", []) if old_pkg else []
                new_permissions = new_pkg.get("requested_permissions", []) if new_pkg else []
                
                # 比较权限列表
                old_perm_names = [p.get("name", "未知权限") for p in old_permissions]
                new_perm_names = [p.get("name", "未知权限") for p in new_permissions]
                
                added_permissions = set(new_perm_names) - set(old_perm_names)
                removed_permissions = set(old_perm_names) - set(new_perm_names)
                
                # 检查是否只是顺序不同
                if old_perm_names != new_perm_names:
                    result += "权限変更：\n"
                    if added_permissions:
                        result += f"  新增权限 ({len(added_permissions)}个):\n"
                        for perm in sorted(added_permissions):
                            result += f"    + {perm}\n"
                    
                    if removed_permissions:
                        result += f"  删除权限 ({len(removed_permissions)}个):\n"
                        for perm in sorted(removed_permissions):
                            result += f"    - {perm}\n"
                    
                    # 如果只是顺序变化
                    if not added_permissions and not removed_permissions:
                        result += f"  权限顺序变化 ({len(old_perm_names)}个权限)\n"
                        # 显示前5个权限的顺序变化
                        if len(old_perm_names) > 0:
                            result += f"    旧顺序示例: {', '.join(old_perm_names[:min(5, len(old_perm_names))])}{'...' if len(old_perm_names) > 5 else ''}\n"
                            result += f"    新顺序示例: {', '.join(new_perm_names[:min(5, len(new_perm_names))])}{'...' if len(new_perm_names) > 5 else ''}\n"
                else:
                    # 权限列表完全相同，但被标记为有权限变更
                    # 可能是权限的其他属性发生了变化（如权限描述、保护级别等）
                    result += "权限変更：\n"
                    result += f"  权限列表相同，但其他属性可能发生变化 ({len(old_permissions)}个权限)\n"
                    result += f"  权限列表: {', '.join(old_perm_names[:min(5, len(old_perm_names))])}{'...' if len(old_perm_names) > 5 else ''}\n"
                
                # 检查是否有其他关注字段变更
                special_field_changes = []
                for diff in change.differences:
                    if diff[0] in special_fields.keys():
                        special_field_changes.append(diff)
                
                if special_field_changes:
                    result += "其他关注字段变更：\n"
                    for diff in special_field_changes:
                        field_name = diff[0]
                        if field_name in field_display_names:
                            display_name = field_display_names[field_name]
                        else:
                            display_name = field_name
                        result += f"  {display_name}: {diff[1]} → {diff[2]}\n"
                
                result += "\n"
        
        # 输出系统级应用权限变更
        if system_permission_changes:
            result += "系统级应用权限变更\n"
            for i, change in enumerate(system_permission_changes, 1):
                old_pkg = change.old_package
                new_pkg = change.new_package
                
                result += f"第{i}个\n"
                result += f"包名:{change.package_name}\n"
                
                # 获取版本信息
                old_version = old_pkg.get("version_name", "未知") if old_pkg else "未知"
                new_version = new_pkg.get("version_name", "未知") if new_pkg else "未知"
                if old_version != new_version:
                    result += f"apk版本号: {old_version} → {new_version}\n"
                else:
                    result += f"apk版本号: {old_version}\n"
                
                # 检查是否有实际的权限变更
                old_permissions = old_pkg.get("requested_permissions", []) if old_pkg else []
                new_permissions = new_pkg.get("requested_permissions", []) if new_pkg else []
                
                # 比较权限列表
                old_perm_names = [p.get("name", "未知权限") for p in old_permissions]
                new_perm_names = [p.get("name", "未知权限") for p in new_permissions]
                
                added_permissions = set(new_perm_names) - set(old_perm_names)
                removed_permissions = set(old_perm_names) - set(new_perm_names)
                
                # 检查是否只是顺序不同
                if old_perm_names != new_perm_names:
                    result += "权限変更：\n"
                    if added_permissions:
                        result += f"  新增权限 ({len(added_permissions)}个):\n"
                        for perm in sorted(added_permissions):
                            result += f"    + {perm}\n"
                    
                    if removed_permissions:
                        result += f"  删除权限 ({len(removed_permissions)}个):\n"
                        for perm in sorted(removed_permissions):
                            result += f"    - {perm}\n"
                    
                    # 如果只是顺序变化
                    if not added_permissions and not removed_permissions:
                        result += f"  权限顺序变化 ({len(old_perm_names)}个权限)\n"
                        # 显示前5个权限的顺序变化
                        if len(old_perm_names) > 0:
                            result += f"    旧顺序示例: {', '.join(old_perm_names[:min(5, len(old_perm_names))])}{'...' if len(old_perm_names) > 5 else ''}\n"
                            result += f"    新顺序示例: {', '.join(new_perm_names[:min(5, len(new_perm_names))])}{'...' if len(new_perm_names) > 5 else ''}\n"
                else:
                    # 权限列表完全相同，但被标记为有权限变更
                    # 可能是权限的其他属性发生了变化（如权限描述、保护级别等）
                    result += "权限変更：\n"
                    result += f"  权限列表相同，但其他属性可能发生变化 ({len(old_permissions)}个权限)\n"
                    result += f"  权限列表: {', '.join(old_perm_names[:min(5, len(old_perm_names))])}{'...' if len(old_perm_names) > 5 else ''}\n"
                
                # 检查是否有其他关注字段变更
                special_field_changes = []
                for diff in change.differences:
                    if diff[0] in special_fields.keys():
                        special_field_changes.append(diff)
                
                if special_field_changes:
                    result += "其他关注字段变更：\n"
                    for diff in special_field_changes:
                        field_name = diff[0]
                        if field_name in field_display_names:
                            display_name = field_display_names[field_name]
                        else:
                            display_name = field_name
                        result += f"  {display_name}: {diff[1]} → {diff[2]}\n"
                
                result += "\n"
        
        # 没有权限变更的包
        no_permission_changes = []
        for change in modified_pkgs:
            # 检查是否有权限变更
            has_permission_change = False
            for diff in change.differences:
                if diff[0] == "请求的权限":
                    has_permission_change = True
                    break
            
            if not has_permission_change:
                no_permission_changes.append(change)
        
        # 先处理所有修改的包，按包名分组收集所有变更
        package_changes_dict = {}
        for change in no_permission_changes:
            package_name = change.package_name
            if package_name not in package_changes_dict:
                package_changes_dict[package_name] = {
                    "change": change,
                    "old_package": change.old_package,
                    "new_package": change.new_package,
                    "differences": [],
                    "old_version": change.old_package.get("version_name", "未知") if change.old_package else "未知",
                    "new_version": change.new_package.get("version_name", "未知") if change.new_package else "未知"
                }
            
            # 收集所有差异
            for diff in change.differences:
                if diff not in package_changes_dict[package_name]["differences"]:
                    package_changes_dict[package_name]["differences"].append(diff)
        
        # 现在按类别输出
        version_only_changes = []
        special_field_changes_list = []
        other_field_changes_list = []
        
        for package_name, data in package_changes_dict.items():
            # 检查是否只有版本更新
            version_only = False
            if len(data["differences"]) == 1 and data["differences"][0][0] == "apk版本号更新":
                version_only = True
                version_only_changes.append(data)
            else:
                # 检查是否有特殊字段变更
                has_special_field = False
                special_fields_in_pkg = []
                other_fields_in_pkg = []
                
                for diff in data["differences"]:
                    if diff[0] in special_fields.keys():
                        has_special_field = True
                        special_fields_in_pkg.append(diff)
                    elif diff[0] != "apk版本号更新" and diff[0] != "安装路径":
                        other_fields_in_pkg.append(diff)
                
                if has_special_field:
                    special_field_changes_list.append({
                        "package_name": package_name,
                        "data": data,
                        "special_fields": special_fields_in_pkg,
                        "other_fields": other_fields_in_pkg
                    })
                elif other_fields_in_pkg:
                    other_field_changes_list.append({
                        "package_name": package_name,
                        "data": data,
                        "fields": other_fields_in_pkg
                    })
                else:
                    # 只有安装路径变更或其他非关注字段
                    other_field_changes_list.append({
                        "package_name": package_name,
                        "data": data,
                        "fields": data["differences"]
                    })
        
        # 输出版本名称更新
        if version_only_changes:
            result += "apk版本名称更新\n"
            for i, data in enumerate(version_only_changes, 1):
                old_version = data["old_version"]
                new_version = data["new_version"]
                result += f"第{i}个\n"
                result += f"包名:{data['change'].package_name}\n"
                if old_version != new_version:
                    result += f"apk版本号: {old_version} → {new_version}\n"
                else:
                    result += f"apk版本号: {old_version}\n"
                result += "\n"
        
        # 输出特殊字段更新（按字段分组）
        special_field_groups = {}
        for item in special_field_changes_list:
            for field in item["special_fields"]:
                field_name = field[0]
                if field_name not in special_field_groups:
                    special_field_groups[field_name] = []
                
                special_field_groups[field_name].append({
                    "package_name": item["package_name"],
                    "data": item["data"],
                    "old_value": field[1],
                    "new_value": field[2]
                })
        
        # 输出各个特殊字段的更新
        for field_name in special_fields.keys():
            if field_name in special_field_groups and special_field_groups[field_name]:
                display_name = field_display_names.get(field_name, field_name)
                result += f"{display_name}\n"
                
                for i, item in enumerate(special_field_groups[field_name], 1):
                    data = item["data"]
                    result += f"第{i}个\n"
                    result += f"包名:{item['package_name']}\n"
                    result += f"版本名称: {data['old_version']}\n"
                    result += f"{display_name}: {item['old_value']} → {item['new_value']}\n\n"
        
        # 输出其他字段更新（不在特殊字段列表中的）
        if other_field_changes_list:
            result += "apk有其他更新（无权限变更和关注字段变更）\n"
            
            # 按包名分组，显示每个包的所有变更
            for i, item in enumerate(other_field_changes_list, 1):
                data = item["data"]
                result += f"第{i}个\n"
                result += f"包名:{item['package_name']}\n"
                result += f"apk版本号: {data['old_version']}\n"
                
                # 显示所有字段变更
                for field in item["fields"]:
                    if field[0] != "安装路径":  # 安装路径变更单独处理
                        result += f"  {field[0]}: {field[1]} → {field[2]}\n"
                    else:
                        result += f"  安装路径更新: {field[1]} → {field[2]}\n"
                
                result += "\n"
        
        # 输出新增的包
        if added_pkgs:
            result += "新增加apk\n"
            for i, change in enumerate(added_pkgs, 1):
                result += f"第{i}个\n"
                result += f"包名:{change.package_name}\n"
                
                if change.new_package:
                    version = change.new_package.get("version_name", "未知")
                    result += f"apk版本号: {version}\n"
                
                result += "\n"
        
        # 输出删除的包
        if removed_pkgs:
            result += "删除apk\n"
            for i, change in enumerate(removed_pkgs, 1):
                result += f"第{i}个\n"
                result += f"包名:{change.package_name}\n"
                
                if change.old_package:
                    version = change.old_package.get("version_name", "未知")
                    result += f"apk版本号: {version}\n"
                
                result += "\n"
        
        # 总结报告
        result += "\n" + "=" * 70 + "\n"
        result += "对比总结\n"
        result += "=" * 70 + "\n"
        result += f"对比包总数: {len(package_result_obj.changes)}\n"
        result += f"发现差异总数: {len(modified_packages)} (修改:{len(modified_pkgs)} + 新增:{len(added_pkgs)} + 删除:{len(removed_pkgs)})\n"
        
        # 详细分类统计
        result += "\n【详细分类统计】\n"
        result += f"  非系统级应用权限变更: {len(non_system_permission_changes)} 个\n"
        result += f"  系统级应用权限变更: {len(system_permission_changes)} 个\n"
        result += f"  新增apk: {len(added_pkgs)} 个\n"
        result += f"  删除apk: {len(removed_pkgs)} 个\n"
        result += f"  apk版本号更新: {len(version_only_changes)} 个\n"
        
        # 统计各个关注字段的更新数量
        for field_name in special_fields.keys():
            if field_name in special_field_groups:
                count = len(special_field_groups[field_name])
                if count > 0:
                    display_name = field_display_names.get(field_name, field_name)
                    result += f"  {display_name}: {count} 个\n"
        
        # 统计其他字段更新
        other_fields_count = len(other_field_changes_list)
        if other_fields_count > 0:
            result += f"  其他字段更新: {other_fields_count} 个\n"
        
        if overall_result == "PASS":
            result += "✅ 所有差异均为允许的类型\n"
        else:
            result += "❌ 发现不允许的差异类型（新增/删除apk或系统级应用权限变更）\n"
        
        return result, overall_result