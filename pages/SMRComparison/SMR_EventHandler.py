# SMR_EventHandler.py
from datetime import datetime

# Pre-computed stylesheets — built once, reused everywhere
_STYLE_ACTIVE = """
    QPushButton {
        background-color: #27ae60; color: white; border: none;
        padding: 0 15px; border-radius: 4px; font-weight: bold; font-size: 14px;
    }
    QPushButton:hover { color: black;  background- }
    QPushButton:pressed { background-color: #27ae60; }
"""

_STYLE_INACTIVE = """
    QPushButton {
        background-color: #4A90D9; color: white; border: none;
        padding: 0 15px; border-radius: 4px; font-weight: bold; font-size: 14px;
    }
    QPushButton:hover { color: black;  background- }
    QPushButton:pressed { background-color: #27ae60; }
"""


class SMR_EventHandler:
    """SMR对比页面事件处理器"""

    def __init__(self, ui, analyzer, select_directory_func):
        self.ui = ui
        self.analyzer = analyzer
        self.select_directory = select_directory_func
        # Track current button states to avoid redundant setStyleSheet calls
        self._btn_state = {"select_mr": False, "select_smr": False,
                           "smr_analyze": False, "vba_analyze": False, "clear": False}

        self.ui.select_mr_btn.clicked.connect(self.select_mr_directory)
        self.ui.select_smr_btn.clicked.connect(self.select_smr_directory)
        self.ui.smr_analyze_btn.clicked.connect(self.start_smr_analysis)
        self.ui.vba_analyze_btn.clicked.connect(self.start_vba_analysis)
        self.ui.clear_btn.clicked.connect(self.clear_records)

        self.update_button_styles()

        self.ui.mr_directory_input.textChanged.connect(self.update_button_styles)
        self.ui.smr_directory_input.textChanged.connect(self.update_button_styles)
        self.ui.analysis_result_display.textChanged.connect(self.update_button_styles)
        self.ui.error_info_display.textChanged.connect(self.update_button_styles)

    def _set_btn_style(self, btn, active):
        """Apply stylesheet only if state changed."""
        btn.setStyleSheet(_STYLE_ACTIVE if active else _STYLE_INACTIVE)

    def update_button_styles(self):
        """Update button styles — only when state actually changes."""
        st = self._btn_state

        mr_ok = bool(self.ui.mr_directory_input.text().strip())
        if st["select_mr"] != mr_ok:
            st["select_mr"] = mr_ok
            self._set_btn_style(self.ui.select_mr_btn, mr_ok)

        smr_ok = bool(self.ui.smr_directory_input.text().strip())
        if st["select_smr"] != smr_ok:
            st["select_smr"] = smr_ok
            self._set_btn_style(self.ui.select_smr_btn, smr_ok)

        has_result = bool(self.ui.analysis_result_display.toPlainText().strip())
        if st["smr_analyze"] != has_result:
            st["smr_analyze"] = has_result
            self._set_btn_style(self.ui.smr_analyze_btn, has_result)
        if st["vba_analyze"] != has_result:
            st["vba_analyze"] = has_result
            self._set_btn_style(self.ui.vba_analyze_btn, has_result)

        has_error = bool(self.ui.error_info_display.toPlainText().strip())
        if st["clear"] != has_error:
            st["clear"] = has_error
            self._set_btn_style(self.ui.clear_btn, has_error)

    def select_mr_directory(self):
        directory = self.select_directory("选择MR报告目录或full test测试报告", self.ui)
        if directory:
            self.ui.mr_directory_input.setText(directory)
            print(f"选择的MR报告目录: {directory}")
            self.update_button_styles()

    def select_smr_directory(self):
        directory = self.select_directory("选择SMR报告目录或VBA测试报告", self.ui)
        if directory:
            self.ui.smr_directory_input.setText(directory)
            print(f"选择的SMR报告目录: {directory}")
            self.update_button_styles()

    def start_smr_analysis(self):
        print("SMR报告分析开始...")
        self.ui.analysis_result_display.clear()
        self.ui.error_info_display.clear()

        mr_dir = self.ui.mr_directory_input.text()
        smr_dir = self.ui.smr_directory_input.text()

        if not mr_dir or not smr_dir:
            error_msg = "错误: 请先选择MR(full test)和SMR(VBA)报告目录\n\n请点击上方按钮选择对应的报告目录。"
            self.ui.error_info_display.setPlainText(error_msg)
            self.update_button_styles()
            return

        self.update_button_styles()

        complete_log, final_verdict_text = self.analyzer.analyze_directories(mr_dir, smr_dir)

        if complete_log:
            self.ui.analysis_result_display.setPlainText(complete_log)

        if final_verdict_text:
            print(f"显示最终判定结果，长度: {len(final_verdict_text)}")
            self.ui.error_info_display.setPlainText(final_verdict_text)
        elif not complete_log:
            self.ui.error_info_display.setPlainText("分析失败，请检查输入的目录是否正确。")
        else:
            success_msg = "✓ 分析完成！但未生成最终判定结果。"
            self.ui.error_info_display.setPlainText(success_msg)

        self.update_button_styles()

    def start_vba_analysis(self):
        """VBA报告分析：检查是否可以走VBA快速通道"""
        print("VBA报告分析开始...")
        self.ui.analysis_result_display.clear()
        self.ui.error_info_display.clear()

        mr_dir = self.ui.mr_directory_input.text()
        smr_dir = self.ui.smr_directory_input.text()

        if not mr_dir or not smr_dir:
            error_msg = "错误: 请先选择MR(full test)和SMR(VBA)报告目录\n\n请点击上方按钮选择对应的报告目录。"
            self.ui.error_info_display.setPlainText(error_msg)
            self.update_button_styles()
            return

        self.update_button_styles()

        try:
            from .VBA_Checker import VBA_Checker
            checker = VBA_Checker()
            result = checker.check_vba_from_directories(mr_dir, smr_dir)

            # 构建详细输出
            output = "=" * 50 + "\n"
            output += "VBA 快速通道检查报告\n"
            output += "=" * 50 + "\n\n"
            output += result.summary_text + "\n\n"

            # 输出 package 级别的详细对比
            pkg = result.details.get("package", {})
            if pkg:
                output += "-" * 50 + "\n"
                output += "Package DeviceInfo 详细对比:\n"
                output += "-" * 50 + "\n"
                output += f"  MR 包总数: {pkg.get('total_mr_packages', 'N/A')}\n"
                output += f"  SMR 包总数: {pkg.get('total_smr_packages', 'N/A')}\n\n"

                # 系统级变更
                output += "【系统级APK变更】（阻止VBA）:\n"
                output += f"  新增: {pkg.get('system_added_count', 0)} 个"
                if pkg.get('system_added'):
                    output += f" → {', '.join(pkg['system_added'])}"
                output += "\n"
                output += f"  删除: {pkg.get('system_removed_count', 0)} 个"
                if pkg.get('system_removed'):
                    output += f" → {', '.join(pkg['system_removed'])}"
                output += "\n"
                output += f"  权限变更: {pkg.get('system_permission_changed_count', 0)} 个"
                if pkg.get('system_permission_changed'):
                    output += f" → {', '.join(pkg['system_permission_changed'])}"
                output += "\n\n"

                # 非系统级变更
                output += "【非系统级APK变更】（允许VBA）:\n"
                output += f"  新增: {pkg.get('non_system_added_count', 0)} 个"
                if pkg.get('non_system_added'):
                    output += f" → {', '.join(pkg['non_system_added'])}"
                output += "\n"
                output += f"  删除: {pkg.get('non_system_removed_count', 0)} 个"
                if pkg.get('non_system_removed'):
                    output += f" → {', '.join(pkg['non_system_removed'])}"
                output += "\n"
                output += f"  权限变更: {pkg.get('non_system_permission_changed_count', 0)} 个"
                if pkg.get('non_system_permission_changed'):
                    output += f" → {', '.join(pkg['non_system_permission_changed'])}"
                output += "\n\n"

            # GMS / Mainline 信息
            gms = result.details.get("gms", {})
            if gms:
                output += "-" * 50 + "\n"
                output += "GMS版本:\n"
                output += f"  MR:  {gms.get('mr_version', 'N/A')}\n"
                output += f"  SMR: {gms.get('smr_version', 'N/A')}\n"
                output += f"  一致: {'✅ 是' if result.gms_check_pass else '❌ 否'}\n\n"

            ml = result.details.get("mainline", {})
            if ml:
                mr_ml = ml.get("mr_info", {}) or {}
                smr_ml = ml.get("smr_info", {}) or {}
                output += "Mainline版本:\n"
                output += f"  MR:  {mr_ml.get('type', 'N/A')} - {mr_ml.get('version', 'N/A')}\n"
                output += f"  SMR: {smr_ml.get('type', 'N/A')} - {smr_ml.get('version', 'N/A')}\n"
                output += f"  一致: {'✅ 是' if result.mainline_check_pass else '❌ 否'}\n\n"

            output += "=" * 50 + "\n"
            if result.can_use_vba:
                output += "✅ 最终判定: 可以走VBA快速通道"
            else:
                output += "❌ 最终判定: 不能走VBA快速通道"
            output += "\n" + "=" * 50 + "\n\n"

            # vbmeta 手动确认提示
            if result.vbmeta_warning:
                output += result.vbmeta_warning + "\n"

            self.ui.analysis_result_display.setPlainText(output)
            self.ui.error_info_display.setPlainText(result.summary_text)

        except Exception as e:
            import traceback
            error_msg = f"VBA分析过程中发生错误:\n{str(e)}\n\n{traceback.format_exc()}"
            self.ui.error_info_display.setPlainText(error_msg)

        self.update_button_styles()

    def clear_records(self):
        print("清除记录...")
        self.ui.mr_directory_input.clear()
        self.ui.smr_directory_input.clear()
        self.ui.analysis_result_display.clear()
        self.ui.error_info_display.clear()

        self.update_button_styles()

        self.ui.analysis_result_display.setPlaceholderText("分析结果显示区域")
        self.ui.error_info_display.setPlaceholderText("错误信息显示区域")

        print("界面已完全重置到初始状态")
