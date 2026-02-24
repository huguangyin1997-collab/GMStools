from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextBrowser, QPushButton, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

class Disclaimer(QWidget):
    agreed = pyqtSignal()
    rejected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("免责声明")
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

        # 免责声明文本区域（可滚动）
        self.disclaimer_text = QTextBrowser()
        self.disclaimer_text.setOpenExternalLinks(True)
        disclaimer_content = """
<h3>GMStools 工具软件免责声明</h3>

<p><strong>重要提示：</strong>在使用本软件之前，请仔细阅读以下免责声明。使用本软件即表示您已阅读、理解并同意接受本声明的所有条款和条件。如果您不同意本声明的任何部分，请勿使用本软件。</p>

<h4>1. 软件使用许可</h4>
<p>本软件按“原样”授予您非独占的、不可转让的个人使用许可。您不得对本软件进行反向工程、反编译、修改、复制、分发或用于任何商业目的，除非获得开发者的明确书面许可。</p>

<h4>2. 免责保证</h4>
<p>本软件按“原样”提供，不附带任何明示或暗示的保证，包括但不限于对适销性、特定用途适用性、所有权和不侵权的保证。开发者不保证软件的功能将满足您的要求，不保证软件的操作不会中断或无错误，也不保证缺陷将被纠正。</p>

<h4>3. 责任限制</h4>
<p>在任何情况下，软件开发者和分发者均不对因使用或无法使用本软件而导致的任何直接、间接、偶然、特殊、惩罚性或后果性损害承担责任，包括但不限于利润损失、数据丢失、业务中断或其他商业损害，即使已被告知可能发生此类损害。</p>

<h4>4. 数据准确性与第三方内容</h4>
<p>本软件可能提供数据处理、分析或转换功能，但开发者不保证输出结果的绝对准确性、完整性或可靠性。用户应自行验证关键数据的准确性，并对基于软件输出所做的任何决策承担全部责任。本软件可能包含指向第三方网站或资源的链接，开发者对其内容、准确性或可用性不承担任何责任。</p>

<h4>5. 专业建议</h4>
<p>本软件提供的信息、建议或计算结果仅供参考，不应被视为专业工程、法律、金融或其他专业领域的建议。对于重要的技术或业务决策，建议咨询合格的专业人员。</p>

<h4>6. 系统兼容性与安全性</h4>
<p>用户有责任确保本软件与其系统环境兼容。开发者不保证本软件不包含任何病毒、恶意代码或其他有害组件。用户应自行采取适当的安全措施，如定期备份数据和使用杀毒软件。</p>

<h4>7. 更新与支持</h4>
<p>开发者保留随时修改、更新或停止提供本软件及其任何功能的权利，恕不另行通知。开发者没有义务提供技术支持、错误修复或新版本发布。</p>

<h4>8. 法律合规</h4>
<p>用户应遵守所有适用法律法规使用本软件。开发者不承担因用户违反法律而产生的任何责任。</p>

<h4>9. 适用法律与争议解决</h4>
<p>本免责声明受中华人民共和国法律管辖。因本软件引起的或与本软件有关的任何争议，应友好协商解决；协商不成的，任何一方均可向开发者所在地有管辖权的人民法院提起诉讼。</p>

<p><strong>最后更新日期：</strong> 2026年2月24日</p>
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
        layout.addWidget(self.disclaimer_text, stretch=1)  # stretch=1 使其占据所有额外空间

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
        """)
        self.accept_btn.clicked.connect(self.on_accept)

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
        # 注意：不再添加额外的 addStretch()，否则按钮下方会有空白

    def on_accept(self):
        self.agreed.emit()

    def on_reject(self):
        reply = QMessageBox.question(
            self,
            "确认退出",
            "您拒绝了免责声明，将退出程序。确定吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.rejected.emit()

    def set_readonly_mode(self, readonly: bool):
        """设置只读模式（隐藏同意/拒绝按钮）"""
        self.accept_btn.setVisible(not readonly)
        self.reject_btn.setVisible(not readonly)