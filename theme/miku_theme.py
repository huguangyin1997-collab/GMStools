# Miku Hatsune theme color constants and QSS helpers for GMStools

# === Signature Miku Teal (Primary Accent) ===
MIKU_TEAL = "#39C5BB"
MIKU_TEAL_HOVER = "#2FAFA6"
MIKU_TEAL_PRESSED = "#259990"

# === Green (Active / Selected / Success) ===
GREEN = "#27AE60"
GREEN_HOVER = "#219653"
GREEN_PRESSED = "#1E8449"

# === Miku Pink (Danger / Error / Critical) ===
MIKU_PINK = "#E91E63"
MIKU_PINK_HOVER = "#C2185B"
MIKU_PINK_PRESSED = "#AD1457"

# === Neutrals ===
DARK_TEXT = "#2C3E50"
BORDER_GRAY = "#BDC3C7"
WHITE = "#FFFFFF"
TEXT_SECONDARY = "#636E72"
TEXT_LIGHT = "#7F8C8D"

# === Backgrounds ===
CARD_BG = "rgba(255, 255, 255, 0.7)"
CARD_BG_LIGHTER = "rgba(255, 255, 255, 0.4)"
TEAL_BG_ALPHA = "rgba(57, 197, 187, 0.15)"
TEAL_BG_ALPHA_STRONG = "rgba(57, 197, 187, 0.25)"


def get_button_style(selected=False):
    """Standard Miku-themed button style."""
    if selected:
        return f"""
            QPushButton {{
                background-color: {GREEN};
                border: 2px solid {GREEN};
                color: {WHITE};
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {GREEN_HOVER};
                border-color: {GREEN_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {GREEN_PRESSED};
                border-color: {GREEN_PRESSED};
            }}
        """
    return f"""
        QPushButton {{
            background-color: {MIKU_TEAL};
            border: 2px solid {MIKU_TEAL};
            color: {WHITE};
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {MIKU_TEAL_HOVER};
            border-color: {MIKU_TEAL_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {MIKU_TEAL_PRESSED};
            border-color: {MIKU_TEAL_PRESSED};
        }}
    """


def get_danger_button_style():
    """Miku pink danger button."""
    return f"""
        QPushButton {{
            background-color: {MIKU_PINK};
            border: 2px solid {MIKU_PINK};
            color: {WHITE};
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {MIKU_PINK_HOVER};
            border-color: {MIKU_PINK_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {MIKU_PINK_PRESSED};
            border-color: {MIKU_PINK_PRESSED};
        }}
    """


def get_line_edit_style(has_content=False):
    """Miku-themed QLineEdit style."""
    border = GREEN if has_content else MIKU_TEAL
    return f"""
        QLineEdit {{
            background-color: {WHITE};
            border: 2px solid {border};
            color: {DARK_TEXT};
            font-size: 14px;
            padding: 5px 10px;
        }}
        QLineEdit:focus {{
            border-color: {MIKU_TEAL};
        }}
    """


def get_text_edit_style(has_content=False):
    """Miku-themed QTextEdit style."""
    border = GREEN if has_content else MIKU_TEAL
    return f"""
        QTextEdit {{
            background-color: {CARD_BG};
            border: 2px solid {border};
            color: {DARK_TEXT};
            font-size: 14px;
        }}
        QTextEdit:focus {{
            border-color: {MIKU_TEAL};
        }}
    """


def get_combo_box_style(is_selected=False):
    """Miku-themed QComboBox style."""
    border = GREEN if is_selected else MIKU_TEAL
    return f"""
        QComboBox {{
            background-color: {WHITE};
            border: 2px solid {border};
            color: {DARK_TEXT};
            font-size: 14px;
            padding: 5px 10px;
        }}
        QComboBox:hover {{
            border-color: {MIKU_TEAL_HOVER};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 10px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {WHITE};
            border: 1px solid {MIKU_TEAL};
            selection-background-color: {MIKU_TEAL};
            selection-color: {WHITE};
            color: {DARK_TEXT};
        }}
    """


def get_menu_style():
    """Miku-themed QMenu (right-click context menu) style."""
    return f"""
        QMenu {{
            background-color: {MIKU_TEAL};
            border: 1px solid {MIKU_TEAL_HOVER};
            color: {WHITE};
            font-size: 13px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 20px;
        }}
        QMenu::item:selected {{
            background-color: {MIKU_TEAL_HOVER};
        }}
        QMenu::item:disabled {{
            color: {BORDER_GRAY};
        }}
    """
