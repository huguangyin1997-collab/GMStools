import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextBrowser, QPushButton, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

# 使用相对导入导入 MikuDialog（必须在包内运行）
from ..Concerning import MikuDialog

class Disclaimer(QDialog):
    """
    免责声明对话框，用户必须阅读并同意后方可继续使用软件。
    增加了滚动到底部才能启用同意按钮的机制，确保用户已阅读全文。
    """
    agreed = pyqtSignal()      # 用户同意时发出
    rejected = pyqtSignal()    # 用户拒绝时发出

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用协议与免责声明")
        self.setModal(True)                     # 设置为模态对话框
        self.resize(800, 600)                    # 设置合适的初始大小
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("使用协议与免责声明")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.8);
            border-radius: 8px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 协议文本区域（可滚动）
        self.disclaimer_text = QTextBrowser()
        self.disclaimer_text.setOpenExternalLinks(True)
        disclaimer_content = """
<h3>GMStools 工具软件使用协议与免责声明</h3>

<p><strong style="color:#c0392b;">重要提示：使用本软件即表示您已阅读、理解并无条件同意本协议的全部内容。如果您不同意，请立即停止使用并删除本软件。</strong></p>

<p>本项目基于 Apache License 2.0 许可证发行，以下协议是对于 Apache License 2.0 的补充，如有冲突，以本协议为准。</p>

<h4>词语约定</h4>
<p>本协议中的“本项目”指 GMStools 工具软件；“使用者”指签署本协议的使用者；“第三方服务”指本项目可能调用的外部 API、数据源或服务；“用户数据”指使用者在使用本软件过程中产生的包括但不限于配置、列表、文件等数据。</p>

<h4>1. 软件许可与“按原样”提供</h4>
<p>本软件按“原样”授予您非独占的、不可转让的个人使用许可。您不得对本软件进行反向工程、反编译、修改、复制、分发或用于任何商业目的，除非获得开发者的明确书面许可。本软件包括所有源代码、目标代码、文档及相关材料均按“原样”提供，不附带任何形式的保证。</p>

<h4>2. 数据来源</h4>
<p>2.1 本软件的部分功能可能从公开的第三方服务或 API 获取数据（如在线信息查询、文件格式转换等），其原理是从其公开服务器中拉取数据，经过处理后展示。本项目不对这些数据的准确性、合法性、完整性或及时性负责，数据仅供参考。</p>
<p>2.2 本软件本身不存储任何第三方提供的数据，使用者在使用过程中产生的用户数据（如配置文件、本地列表等）仅存储在用户本地设备或用户指定的同步服务中，本项目不对这些数据的安全性、合法性、丢失或损坏承担责任。</p>

<h4>3. 版权与用户内容</h4>
<p>3.1 使用本软件的过程中可能会产生或涉及受版权保护的内容（例如通过软件处理他人作品）。对于这些内容，本项目不拥有其所有权。使用者应确保其使用行为符合相关版权法律法规，并自行承担全部责任。</p>
<p>3.2 若本软件内使用了任何第三方资源（包括但不限于图标、字体、图片等），均来自互联网公开渠道，如有侵权，请联系我们移除。</p>

<h4>4. 免责保证</h4>
<p>在法律允许的最大范围内，开发者明确否认所有明示或暗示的保证，包括但不限于对适销性、特定用途适用性、所有权和不侵权的暗示保证。开发者不保证软件的功能将满足您的要求，不保证软件的操作不会中断或无错误，不保证缺陷将被纠正，也不保证软件中不包含病毒或其他有害组件。您理解并同意，使用本软件的风险由您自行承担。</p>

<h4>5. 责任限制</h4>
<p>在任何情况下，开发者均不对因使用或无法使用本软件而导致的任何直接、间接、偶然、特殊、惩罚性或后果性损害承担责任，包括但不限于利润损失、数据丢失、业务中断、人身伤害或财产损失，即使开发者已被告知可能发生此类损害。如果您对本软件的任何部分不满意，您的唯一补救措施是停止使用本软件。</p>

<h4>6. 使用限制</h4>
<p>6.1 您不得将本软件用于任何非法目的或以任何违反适用法律法规的方式使用本软件。对于使用者在明知或不知当地法律法规不允许的情况下使用本软件所造成的任何违法违规行为，由使用者独立承担全部责任。</p>
<p>6.2 您不得利用本软件侵犯任何第三方的合法权益，包括但不限于知识产权、隐私权等。</p>

<h4>7. 非商业性质</h4>
<p>本项目完全免费，仅用于对技术可行性的探索、研究及个人使用，不接受任何商业合作、广告投放或捐赠。未经开发者明确许可，不得将本软件或其任何部分用于商业用途。</p>

<h4>8. 更新与支持</h4>
<p>开发者保留随时修改、更新或停止提供本软件及其任何功能的权利，恕不另行通知。开发者没有义务提供技术支持、错误修复或新版本发布。您承认开发者没有义务维护或更新本软件。</p>

<h4>9. 适用法律与争议解决</h4>
<p>本协议受中华人民共和国法律管辖。因本软件引起的或与本软件有关的任何争议，双方应首先友好协商解决；协商不成的，任何一方均可向被告所在地有管辖权的人民法院提起诉讼。若本条款因任何原因被认定为无效或不可执行，则争议应提交开发者所在地有管辖权的人民法院解决。</p>

<h4>10. 完整协议与可分割性</h4>
<p>本协议构成您与开发者之间关于使用本软件的完整协议，并取代所有先前的口头或书面协议。如果本协议的任何部分被认定为无效或不可执行，其余部分仍应具有完全效力。</p>

<p><strong>最后更新日期：</strong> 2026年3月16日</p>
"""
        self.disclaimer_text.setHtml(disclaimer_content)
        self.disclaimer_text.setStyleSheet("""
            QTextBrowser {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 20px;
                font-size: 14px;
                line-height: 1.5;
            }
        """)

        # 让文本区域占满剩余空间
        self.disclaimer_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.disclaimer_text, stretch=1)

        # 按钮布局
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(20)

        self.accept_btn = QPushButton("同意")
        self.accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.accept_btn.setEnabled(False)  # 初始禁用，必须滚动到底部才能启用

        self.reject_btn = QPushButton("拒绝")
        self.reject_btn.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.reject_btn.clicked.connect(self.on_reject)

        self.button_layout.addStretch()
        self.button_layout.addWidget(self.accept_btn)
        self.button_layout.addWidget(self.reject_btn)
        self.button_layout.addStretch()

        layout.addLayout(self.button_layout)

    def connect_signals(self):
        """连接信号与槽"""
        # 滚动条值变化时检查是否已滚动到底部
        self.disclaimer_text.verticalScrollBar().valueChanged.connect(self.check_scroll)
        self.accept_btn.clicked.connect(self.on_accept)

    def check_scroll(self, value):
        """检查是否已经滚动到底部，如果是则启用同意按钮"""
        scrollbar = self.disclaimer_text.verticalScrollBar()
        if value >= scrollbar.maximum():
            self.accept_btn.setEnabled(True)
        else:
            self.accept_btn.setEnabled(False)

    def on_accept(self):
        """用户点击同意按钮"""
        self.agreed.emit()
        self.accept()  # 关闭对话框并返回 QDialog.Accepted

    def on_reject(self):
        """用户点击拒绝按钮，弹出二次确认对话框"""
        dialog = MikuDialog(
            self,
            title="确认退出",
            message="您拒绝了使用协议，将退出程序。确定吗？",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        result = dialog.exec()
        if result == QMessageBox.StandardButton.Yes:
            self.rejected.emit()
            self.reject()  # 关闭对话框并返回 QDialog.Rejected

    def set_readonly_mode(self, readonly: bool):
        """设置只读模式（隐藏同意/拒绝按钮）"""
        self.accept_btn.setVisible(not readonly)
        self.reject_btn.setVisible(not readonly)
