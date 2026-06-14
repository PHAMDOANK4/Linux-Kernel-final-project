COLORS = {
    "bg": "#0f172a",
    "bg_secondary": "#1e293b",
    "surface": "#1e293b",
    "card": "#1e293b",
    "border": "#334155",
    "accent": "#3b82f6",
    "accent_hover": "#2563eb",
    "accent_light": "#1e3a5f",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "danger_hover": "#dc2626",
    "text": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "input_bg": "#0f172a",
    "terminal_bg": "#0d1117",
    "terminal_text": "#c9d1d9",
    "table_header": "#334155",
    "table_row_alt": "#1a2332",
    "scrollbar": "#334155",
    "scrollbar_hover": "#475569",
}

TAB_STYLE = f"""
    QTabWidget::pane {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 16px;
    }}
    QTabWidget::tab-bar {{
        alignment: left;
    }}
    QTabBar::tab {{
        background: {COLORS["bg"]};
        color: {COLORS["text_secondary"]};
        padding: 10px 22px;
        font-size: 12px;
        font-weight: bold;
        border: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: {COLORS["surface"]};
        color: {COLORS["accent"]};
        border: 1px solid {COLORS["border"]};
        border-bottom: none;
    }}
    QTabBar::tab:hover:!selected {{
        background: {COLORS["bg_secondary"]};
        color: {COLORS["text"]};
    }}
"""

TABLE_STYLE = f"""
    QTableWidget {{
        background: {COLORS["bg"]};
        alternate-background-color: {COLORS["table_row_alt"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        font-size: 12px;
        color: {COLORS["text"]};
        gridline-color: {COLORS["border"]};
        selection-background-color: {COLORS["accent_light"]};
        selection-color: {COLORS["text"]};
    }}
    QTableWidget::item {{
        padding: 6px 8px;
    }}
    QHeaderView::section {{
        background: {COLORS["table_header"]};
        color: {COLORS["text_secondary"]};
        padding: 8px 8px;
        border: none;
        border-bottom: 2px solid {COLORS["border"]};
        font-weight: bold;
        font-size: 11px;
        text-transform: uppercase;
    }}
"""

BTN_PRIMARY = f"""
    QPushButton {{
        background: {COLORS["accent"]};
        color: white;
        padding: 7px 18px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
        border: none;
    }}
    QPushButton:hover {{
        background: {COLORS["accent_hover"]};
    }}
    QPushButton:disabled {{
        background: {COLORS["border"]};
        color: {COLORS["text_muted"]};
    }}
"""

BTN_DANGER = f"""
    QPushButton {{
        background: {COLORS["danger"]};
        color: white;
        padding: 7px 18px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
        border: none;
    }}
    QPushButton:hover {{
        background: {COLORS["danger_hover"]};
    }}
    QPushButton:disabled {{
        background: {COLORS["border"]};
        color: {COLORS["text_muted"]};
    }}
"""

BTN_SUCCESS = f"""
    QPushButton {{
        background: {COLORS["success"]};
        color: white;
        padding: 7px 18px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
        border: none;
    }}
    QPushButton:hover {{
        background: #16a34a;
    }}
"""

BTN_WARNING = f"""
    QPushButton {{
        background: {COLORS["warning"]};
        color: white;
        padding: 7px 18px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
        border: none;
    }}
    QPushButton:hover {{
        background: #d97706;
    }}
"""

BTN_GHOST = f"""
    QPushButton {{
        background: transparent;
        color: {COLORS["text_secondary"]};
        padding: 6px 16px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid {COLORS["border"]};
    }}
    QPushButton:hover {{
        background: {COLORS["bg_secondary"]};
        color: {COLORS["text"]};
    }}
"""

INPUT_STYLE = f"""
    QLineEdit {{
        padding: 7px 12px;
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        font-size: 13px;
        background: {COLORS["input_bg"]};
        color: {COLORS["text"]};
    }}
    QLineEdit:focus {{
        border-color: {COLORS["accent"]};
    }}
    QLineEdit::placeholder {{
        color: {COLORS["text_muted"]};
    }}
"""

TERMINAL_STYLE = f"""
    QTextEdit {{
        background: {COLORS["terminal_bg"]};
        color: {COLORS["terminal_text"]};
        border-radius: 6px;
        padding: 10px;
        font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
        font-size: 11px;
        border: 1px solid {COLORS["border"]};
    }}
"""

LABEL_STYLE = f"""
    color: {COLORS["text_secondary"]};
    font-size: 13px;
    font-weight: 500;
"""

TITLE_STYLE = f"""
    color: {COLORS["text"]};
    font-size: 20px;
    font-weight: bold;
    letter-spacing: -0.5px;
"""

SCROLLBAR_STYLE = f"""
    QScrollBar:vertical {{
        background: {COLORS["bg"]};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS["scrollbar"]};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS["scrollbar_hover"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {COLORS["bg"]};
        height: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLORS["scrollbar"]};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
"""
