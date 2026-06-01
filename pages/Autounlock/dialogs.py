from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDialog,
    QLabel, QFrame
)
from PyQt6.QtCore import Qt


def show_styled_message(parent, title, message, icon_type="warning"):
    """Show a themed dialog matching the app's visual style."""
    accent_map = {
        "critical": ("#E91E63", "✕"),
        "warning": ("#39C5BB", "!"),
        "info": ("#39C5BB", "i"),
    }
    accent, icon_char = accent_map.get(icon_type, accent_map["warning"])

    dlg = QDialog(parent)
    dlg.setWindowFlags(
        Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
    )
    dlg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    dlg.setModal(True)
    dlg.setFixedWidth(400)

    card = QFrame()
    card.setObjectName("styledCard")
    card.setStyleSheet("""
        QFrame#styledCard {
            background-color: white;
            border: 1px solid #dcdde1;
        }
    """)

    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(0, 0, 0, 0)
    card_layout.setSpacing(0)

    bar = QLabel()
    bar.setFixedHeight(3)
    bar.setStyleSheet(f"background-color: {accent}; border: none;")
    card_layout.addWidget(bar)

    body = QHBoxLayout()
    body.setContentsMargins(20, 18, 20, 12)
    body.setSpacing(14)

    icon_lbl = QLabel(icon_char)
    icon_lbl.setFixedSize(36, 36)
    icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_lbl.setStyleSheet(f"""
        QLabel {{
            background-color: {accent};
            color: white;
            font-size: 16px;
            font-weight: bold;
            border: none;
        }}
    """)
    body.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignTop)

    text_block = QVBoxLayout()
    text_block.setSpacing(6)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #2c3e50; border: none;")
    title_lbl.setWordWrap(True)
    text_block.addWidget(title_lbl)

    msg_lbl = QLabel(message)
    msg_lbl.setStyleSheet("font-size: 13px; color: #636e72; border: none;")
    msg_lbl.setWordWrap(True)
    text_block.addWidget(msg_lbl)

    body.addLayout(text_block, 1)
    card_layout.addLayout(body)

    btn_row = QHBoxLayout()
    btn_row.setContentsMargins(20, 4, 20, 16)
    btn_row.addStretch()

    ok_btn = QPushButton("确定")
    ok_btn.setFixedSize(80, 30)
    ok_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {accent};
            border: none;
            color: white;
            font-size: 13px;
            font-weight: bold;
        }}
        QPushButton:hover {{ color: #ecf0f1; }}
        QPushButton:pressed {{ background-color: {accent}; opacity: 0.85; }}
    """)
    ok_btn.clicked.connect(dlg.accept)
    btn_row.addWidget(ok_btn)
    card_layout.addLayout(btn_row)

    main_layout = QVBoxLayout(dlg)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(card)

    dlg.adjustSize()
    parent_widget = parent.window() if parent.window() else parent
    pc = parent_widget.geometry().center()
    dlg.move(pc.x() - dlg.width() // 2, pc.y() - dlg.height() // 2)

    dlg.exec()
