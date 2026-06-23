"""
VBA (Version Baseline Analysis) Checker
判断当前MR和SMR之间是否可以走VBA快速通道。

VBA 条件:
1. GMS包没有更新        → MR和SMR的GMS版本必须严格一致
2. Mainline没有更新      → MR和SMR的Mainline类型和版本必须严格一致
3. PrivApp权限没有变更   → 系统级APK(system_priv=true)的权限列表不能变更
4. 没有系统级APK增删     → 不允许新增或删除系统级APK
5. 允许非系统级APK增删   → 非系统级APK的新增/删除不阻止VBA
6. 允许非系统级APK权限变更 → 非系统级APK的权限变更不阻止VBA
7. Package DeviceInfo完整一致 → 以上条件全部满足，视为Package DeviceInfo一致，可走VBA
8. Vbmeta分区手动确认    → 需手动确认vbmetaDeviceInfo中仅tr_preload/tr_region/tr_product
   分区存在差异，此项为人工确认提示，程序中不做自动对比
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class VBABlockReason(Enum):
    """VBA 阻止原因枚举"""
    GMS_VERSION_MISMATCH = "GMS版本不一致"
    MAINLINE_MISMATCH = "Mainline版本不一致"
    SYSTEM_APK_PERMISSION_CHANGED = "系统级APK权限变更"
    SYSTEM_APK_ADDED = "系统级APK新增"
    SYSTEM_APK_REMOVED = "系统级APK删除"
    PACKAGE_DEVICEINFO_MISSING = "Package DeviceInfo数据缺失"


@dataclass
class VBACheckResult:
    """VBA 检查结果"""
    can_use_vba: bool = False                            # 是否可以走VBA
    all_checks_passed: bool = False                      # 所有检查是否通过
    gms_check_pass: bool = True                          # GMS包版本检查
    mainline_check_pass: bool = True                      # Mainline版本检查
    system_priv_permission_check_pass: bool = True         # 系统级权限变更检查
    system_apk_count_check_pass: bool = True               # 系统级APK增删检查
    block_reasons: List[VBABlockReason] = field(default_factory=list)  # 阻止原因列表
    details: Dict[str, Any] = field(default_factory=dict)              # 详细信息
    summary_text: str = ""                                # 中文摘要文本
    vbmeta_warning: str = ""                              # vbmeta分区差异提示（不阻止VBA）


class VBA_Checker:
    """
    VBA 检查器

    判断MR和SMR之间能否走VBA快速通道。
    核心逻辑：只有系统级(system_priv=true)的变更才会阻止VBA，
    非系统级APK的增删和权限变更都是允许的。

    用法:
        checker = VBA_Checker()
        result = checker.check_vba(
            mr_packages=MR的package列表,
            smr_packages=SMR的package列表,
            mr_gms_version=MR的GMS版本字符串,
            smr_gms_version=SMR的GMS版本字符串,
            mr_mainline_info=MR的mainline信息字典,
            smr_mainline_info=SMR的mainline信息字典,
        )
        if result.can_use_vba:
            print("可以走VBA")
        else:
            print(f"不能走VBA，原因: {result.summary_text}")
    """

    # ----------------------------------------------------------------
    # 公开入口
    # ----------------------------------------------------------------

    def check_vba(
        self,
        mr_packages: List[Dict],
        smr_packages: List[Dict],
        mr_gms_version: str,
        smr_gms_version: str,
        mr_mainline_info: Optional[Dict] = None,
        smr_mainline_info: Optional[Dict] = None,
    ) -> VBACheckResult:
        """
        执行完整的VBA可用性检查。

        Args:
            mr_packages: MR的package列表 (PackageDeviceInfo.deviceinfo.json 中的 "package" 数组)
            smr_packages: SMR的package列表
            mr_gms_version: MR的GMS版本 (如 "24.45.33")
            smr_gms_version: SMR的GMS版本
            mr_mainline_info: MR的Mainline信息字典，格式:
                {"type": "GO"|"non-GO", "version": "...", "module_name": "..."}
            smr_mainline_info: SMR的Mainline信息字典

        Returns:
            VBACheckResult: 包含所有检查结果的完整信息
        """
        result = VBACheckResult()

        # ---- 1. GMS包版本检查 ----
        result.gms_check_pass = self._check_gms_version(mr_gms_version, smr_gms_version)
        if not result.gms_check_pass:
            result.block_reasons.append(VBABlockReason.GMS_VERSION_MISMATCH)
            result.details["gms"] = {
                "mr_version": mr_gms_version,
                "smr_version": smr_gms_version,
            }

        # ---- 2. Mainline版本检查 ----
        result.mainline_check_pass = self._check_mainline_version(
            mr_mainline_info, smr_mainline_info
        )
        if not result.mainline_check_pass:
            result.block_reasons.append(VBABlockReason.MAINLINE_MISMATCH)
            result.details["mainline"] = {
                "mr_info": mr_mainline_info,
                "smr_info": smr_mainline_info,
            }

        # ---- 3-6. Package级别检查 ----
        (
            result.system_priv_permission_check_pass,
            result.system_apk_count_check_pass,
            pkg_details,
        ) = self._check_packages(mr_packages, smr_packages)

        if not result.system_priv_permission_check_pass:
            result.block_reasons.append(VBABlockReason.SYSTEM_APK_PERMISSION_CHANGED)
        if not result.system_apk_count_check_pass:
            # 进一步区分是新增还是删除
            if pkg_details.get("system_added_count", 0) > 0:
                result.block_reasons.append(VBABlockReason.SYSTEM_APK_ADDED)
            if pkg_details.get("system_removed_count", 0) > 0:
                result.block_reasons.append(VBABlockReason.SYSTEM_APK_REMOVED)

        result.details["package"] = pkg_details

        # ---- 8. Vbmeta分区手动确认提示（程序中不做自动对比） ----
        result.vbmeta_warning = (
            "⚠️ 请手动确认: 对比 Full Test 与 VBA 目录中的 vbmetaDeviceInfo.deviceinfo.json 文件，\n"
            "   确认各市场版本之间仅存在如下分区差异: tr_preload / tr_region / tr_product\n"
            "   如存在其他分区差异，请人工评估是否影响VBA判定。"
        )

        # ---- 综合判定 ----
        result.all_checks_passed = (
            result.gms_check_pass
            and result.mainline_check_pass
            and result.system_priv_permission_check_pass
            and result.system_apk_count_check_pass
        )
        result.can_use_vba = result.all_checks_passed

        # ---- 生成摘要 ----
        result.summary_text = self._generate_summary(result)

        return result

    # ----------------------------------------------------------------
    # 各项检查
    # ----------------------------------------------------------------

    def _check_gms_version(self, mr_gms_version: str, smr_gms_version: str) -> bool:
        """
        检查GMS版本是否一致。
        - 必须严格相等
        - '未找到' 视为不通过
        """
        if mr_gms_version == "未找到" or smr_gms_version == "未找到":
            return False
        return mr_gms_version == smr_gms_version

    def _check_mainline_version(
        self,
        mr_mainline_info: Optional[Dict],
        smr_mainline_info: Optional[Dict],
    ) -> bool:
        """
        检查Mainline版本是否一致。
        - type 必须相同 (GO / non-GO)
        - version 必须相同
        - 任一为None或version为'未找到' → 不通过
        """
        if mr_mainline_info is None or smr_mainline_info is None:
            return False

        mr_type = mr_mainline_info.get("type", "unknown")
        smr_type = smr_mainline_info.get("type", "unknown")
        mr_version = mr_mainline_info.get("version", "未找到")
        smr_version = smr_mainline_info.get("version", "未找到")

        if mr_version == "未找到" or smr_version == "未找到":
            return False
        if mr_type != smr_type:
            return False
        return mr_version == smr_version

    def _check_packages(
        self,
        mr_packages: List[Dict],
        smr_packages: List[Dict],
    ) -> Tuple[bool, bool, Dict[str, Any]]:
        """
        检查Package级别的VBA条件。

        对VBA可用的定义:
        - 系统级APK (system_priv=true):
            * 不能新增
            * 不能删除
            * 权限不能变更 (requested_permissions 必须完全相同)
            * 其他字段变更不阻止VBA (如版本号更新)
        - 非系统级APK:
            * 可以新增
            * 可以删除
            * 权限可以变更
            * 一切变更都允许

        Returns:
            (system_perm_pass, system_count_pass, details_dict)
        """
        # 构建包名→包信息的映射
        mr_pkg_dict: Dict[str, Dict] = {
            pkg["name"]: pkg for pkg in mr_packages
        }
        smr_pkg_dict: Dict[str, Dict] = {
            pkg["name"]: pkg for pkg in smr_packages
        }

        all_pkg_names = set(mr_pkg_dict.keys()) | set(smr_pkg_dict.keys())

        system_perm_changed_list: List[str] = []   # 权限变更的系统级APK名
        system_added_list: List[str] = []           # 新增的系统级APK名
        system_removed_list: List[str] = []          # 删除的系统级APK名
        non_system_added_list: List[str] = []        # 新增的非系统级APK名
        non_system_removed_list: List[str] = []      # 删除的非系统级APK名
        non_system_perm_changed_list: List[str] = [] # 权限变更的非系统级APK名

        for pkg_name in sorted(all_pkg_names):
            mr_pkg = mr_pkg_dict.get(pkg_name)
            smr_pkg = smr_pkg_dict.get(pkg_name)

            # --- 包只在MR存在 → SMR中删除 ---
            if smr_pkg is None:
                is_system = mr_pkg.get("system_priv", False) if mr_pkg else False
                if is_system:
                    system_removed_list.append(pkg_name)
                else:
                    non_system_removed_list.append(pkg_name)
                continue

            # --- 包只在SMR存在 → SMR中新增 ---
            if mr_pkg is None:
                is_system = smr_pkg.get("system_priv", False) if smr_pkg else False
                if is_system:
                    system_added_list.append(pkg_name)
                else:
                    non_system_added_list.append(pkg_name)
                continue

            # --- 包两边都存在 → 检查权限变更 ---
            is_system = mr_pkg.get("system_priv", False) or smr_pkg.get("system_priv", False)

            perms_changed = self._permissions_changed(mr_pkg, smr_pkg)

            if perms_changed:
                if is_system:
                    system_perm_changed_list.append(pkg_name)
                else:
                    non_system_perm_changed_list.append(pkg_name)

        # 判定
        system_perm_pass = len(system_perm_changed_list) == 0
        system_count_pass = (
            len(system_added_list) == 0
            and len(system_removed_list) == 0
        )

        details = {
            "total_mr_packages": len(mr_packages),
            "total_smr_packages": len(smr_packages),
            "system_added": system_added_list,
            "system_added_count": len(system_added_list),
            "system_removed": system_removed_list,
            "system_removed_count": len(system_removed_list),
            "system_permission_changed": system_perm_changed_list,
            "system_permission_changed_count": len(system_perm_changed_list),
            "non_system_added": non_system_added_list,
            "non_system_added_count": len(non_system_added_list),
            "non_system_removed": non_system_removed_list,
            "non_system_removed_count": len(non_system_removed_list),
            "non_system_permission_changed": non_system_perm_changed_list,
            "non_system_permission_changed_count": len(non_system_perm_changed_list),
        }

        return system_perm_pass, system_count_pass, details

    # ----------------------------------------------------------------
    # 辅助方法
    # ----------------------------------------------------------------

    @staticmethod
    def _permissions_changed(mr_pkg: Dict, smr_pkg: Dict) -> bool:
        """
        检查两个包的 requested_permissions 是否完全一致。

        比较逻辑:
        - 提取权限名称列表进行集合比较 (忽略顺序)
        - 如果权限数量不同 → 有变更
        - 如果权限名集合不同 → 有变更
        - 权限的附加属性（protection_level等）也参与比较
        """
        mr_perms = mr_pkg.get("requested_permissions", [])
        smr_perms = smr_pkg.get("requested_permissions", [])

        # 数量不同 → 有变更
        if len(mr_perms) != len(smr_perms):
            return True

        # 提取权限名称并比较集合
        mr_perm_names = set(p.get("name", "") for p in mr_perms)
        smr_perm_names = set(p.get("name", "") for p in smr_perms)

        if mr_perm_names != smr_perm_names:
            return True

        # 集合相同，进一步比较每个权限的完整内容
        mr_perm_map = {p.get("name", ""): p for p in mr_perms}
        smr_perm_map = {p.get("name", ""): p for p in smr_perms}

        for perm_name in mr_perm_names:
            if mr_perm_map.get(perm_name) != smr_perm_map.get(perm_name):
                return True

        return False

    @staticmethod
    def is_system_apk(pkg: Dict) -> bool:
        """判断APK是否为系统级 (system_priv=true)"""
        return pkg.get("system_priv", False) is True

    def _generate_summary(self, result: VBACheckResult) -> str:
        """生成中文摘要文本"""
        if result.can_use_vba:
            lines = ["✅ 可以走VBA快速通道"]
            lines.append("所有VBA条件检查通过:")
            lines.append("  ✅ GMS包版本一致")
            lines.append("  ✅ Mainline版本一致")
            lines.append("  ✅ 系统级APK权限无变更")
            lines.append("  ✅ 系统级APK无增删")

            # 附加说明非系统级的变更情况
            pkg = result.details.get("package", {})
            non_sys_add = pkg.get("non_system_added_count", 0)
            non_sys_rem = pkg.get("non_system_removed_count", 0)
            non_sys_perm = pkg.get("non_system_permission_changed_count", 0)

            if non_sys_add or non_sys_rem or non_sys_perm:
                lines.append("\n（以下非系统级变更在VBA中允许，仅供参考）:")
                if non_sys_add:
                    lines.append(f"  ℹ️ 非系统级APK新增: {non_sys_add} 个")
                if non_sys_rem:
                    lines.append(f"  ℹ️ 非系统级APK删除: {non_sys_rem} 个")
                if non_sys_perm:
                    lines.append(f"  ℹ️ 非系统级APK权限变更: {non_sys_perm} 个")

            # vbmeta 手动确认提示
            if result.vbmeta_warning:
                lines.append("\n" + result.vbmeta_warning)
        else:
            lines = ["❌ 不能走VBA快速通道"]
            lines.append("以下条件未满足:")

            if not result.gms_check_pass:
                lines.append("  ❌ GMS包版本不一致")
            if not result.mainline_check_pass:
                lines.append("  ❌ Mainline版本不一致")
            if not result.system_priv_permission_check_pass:
                pkg = result.details.get("package", {})
                changed = pkg.get("system_permission_changed", [])
                lines.append(f"  ❌ 系统级APK权限变更 ({len(changed)} 个):")
                for name in changed[:10]:
                    lines.append(f"      - {name}")
                if len(changed) > 10:
                    lines.append(f"      ... 还有 {len(changed) - 10} 个")
            if not result.system_apk_count_check_pass:
                pkg = result.details.get("package", {})
                added = pkg.get("system_added", [])
                removed = pkg.get("system_removed", [])
                if added:
                    lines.append(f"  ❌ 系统级APK新增 ({len(added)} 个):")
                    for name in added[:10]:
                        lines.append(f"      - {name}")
                if removed:
                    lines.append(f"  ❌ 系统级APK删除 ({len(removed)} 个):")
                    for name in removed[:10]:
                        lines.append(f"      - {name}")

            # vbmeta 手动确认提示
            if result.vbmeta_warning:
                lines.append("\n" + result.vbmeta_warning)

        return "\n".join(lines)

    # ----------------------------------------------------------------
    # 便捷方法：直接从文件路径或SMR_Analyzer结果构造检查
    # ----------------------------------------------------------------

    def check_vba_from_directories(
        self,
        mr_dir: str,
        smr_dir: str,
    ) -> VBACheckResult:
        """
        从MR和SMR目录直接执行VBA检查。
        自动提取所需的所有数据。

        Args:
            mr_dir: MR报告目录
            smr_dir: SMR报告目录

        Returns:
            VBACheckResult
        """
        from .SMR_FileUtils import SMR_FileUtils
        from .SMR_InfoExtractor import SMR_InfoExtractor

        file_utils = SMR_FileUtils()
        extractor = SMR_InfoExtractor(file_utils)

        # 提取 GMS 版本
        mr_gms = extractor.extract_gms_version(mr_dir)
        smr_gms = extractor.extract_gms_version(smr_dir)

        # 提取 Mainline 版本
        mr_mainline = extractor.extract_mainline_version(mr_dir)
        smr_mainline = extractor.extract_mainline_version(smr_dir)

        # 读取 Package 数据
        mr_feature_file, mr_package_file = file_utils.find_json_files_in_directory(mr_dir)
        _, smr_package_file = file_utils.find_json_files_in_directory(smr_dir)

        mr_packages: List[Dict] = []
        smr_packages: List[Dict] = []

        if mr_package_file:
            data = file_utils.read_json_file(mr_package_file)
            if data:
                mr_packages = data.get("package", [])

        if smr_package_file:
            data = file_utils.read_json_file(smr_package_file)
            if data:
                smr_packages = data.get("package", [])

        return self.check_vba(
            mr_packages=mr_packages,
            smr_packages=smr_packages,
            mr_gms_version=mr_gms,
            smr_gms_version=smr_gms,
            mr_mainline_info=mr_mainline,
            smr_mainline_info=smr_mainline,
        )
