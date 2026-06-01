# SMR_EventHandler.py
from datetime import datetime

# Pre-computed stylesheets — built once, reused everywhere
_STYLE_ACTIVE = """
    QPushButton {
        background-color: #27ae60; color: white; border: none;
        padding: 0 15px; border-radius: 4px; font-weight: bold; font-size: 14px;
    }
    QPushButton:hover { background-color: #2FAFA6; }
    QPushButton:pressed { background-color: #27ae60; }
"""

_STYLE_INACTIVE = """
    QPushButton {
        background-color: #39C5BB; color: white; border: none;
        padding: 0 15px; border-radius: 4px; font-weight: bold; font-size: 14px;
    }
    QPushButton:hover { background-color: #2FAFA6; }
    QPushButton:pressed { background-color: #27ae60; }
"""


class SMR_EventHandler:
    """SMR对比页面事件处理器"""

    def __init__(self, ui, analyzer, select_directory_func):
        self.ui = ui
        self.analyzer = analyzer
        self.select_directory = select_directory_func
        # Track current button states to avoid redundant setStyleSheet calls
        self._btn_state = {"select_mr": False, "select_smr": False, "analyze": False, "clear": False}

        self.ui.select_mr_btn.clicked.connect(self.select_mr_directory)
        self.ui.select_smr_btn.clicked.connect(self.select_smr_directory)
        self.ui.analyze_btn.clicked.connect(self.start_analysis)
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
        if st["analyze"] != has_result:
            st["analyze"] = has_result
            self._set_btn_style(self.ui.analyze_btn, has_result)

        has_error = bool(self.ui.error_info_display.toPlainText().strip())
        if st["clear"] != has_error:
            st["clear"] = has_error
            self._set_btn_style(self.ui.clear_btn, has_error)

    def select_mr_directory(self):
        directory = self.select_directory("选择MR报告目录", self.ui)
        if directory:
            self.ui.mr_directory_input.setText(directory)
            print(f"选择的MR报告目录: {directory}")
            self.update_button_styles()

    def select_smr_directory(self):
        directory = self.select_directory("选择SMR报告目录", self.ui)
        if directory:
            self.ui.smr_directory_input.setText(directory)
            print(f"选择的SMR报告目录: {directory}")
            self.update_button_styles()

    def start_analysis(self):
        print("开始分析...")
        self.ui.analysis_result_display.clear()
        self.ui.error_info_display.clear()

        mr_dir = self.ui.mr_directory_input.text()
        smr_dir = self.ui.smr_directory_input.text()

        if not mr_dir or not smr_dir:
            error_msg = "错误: 请先选择MR和SMR报告目录\n\n请点击上方按钮选择对应的报告目录。"
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
