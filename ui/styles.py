"""Тёмная EVE-тема (QSS) для Fleet Manager.

Палитра и подход согласованы с EVE Jump Planner (Photon-стиль): тёмный фон,
акцентный цвет, тонкие рамки. Тема выбирается через apply_theme().
"""

# ── Palette ──────────────────────────────────────────────────────────────────
BG_DEEP   = "#060c12"
BG_PANEL  = "#0d1520"
BG_CARD   = "#111e2e"
BG_HEADER = "#0a1628"
BORDER    = "#1e3a4a"
BORDER_LT = "#2a5570"
ACCENT    = "#4fc3f7"
ACCENT2   = "#00bcd4"
TEXT      = "#c8d8e8"
TEXT_DIM  = "#6a8a9a"
YELLOW    = "#f0c040"
GREEN     = "#4caf50"
ORANGE    = "#ff9800"
RED       = "#ef5350"
AMBER     = "#e0a526"
# производные от акцента (задаются apply_theme)
SELECT_BG        = "#1a3550"
PRIMARY_BG       = "#0d3a5a"
PRIMARY_BG_HOVER = "#1a5070"


# ── Темы (фракции EVE) ────────────────────────────────────────────────────────
THEME_PRESETS = [
    {"id": "default",  "name": "Default",             "accent": "#4fc3f7", "accent2": "#00bcd4"},
    {"id": "amarr",    "name": "Amarr Empire",        "accent": "#e0b347", "accent2": "#caa030"},
    {"id": "gallente", "name": "Gallente Federation", "accent": "#34c79a", "accent2": "#26a37d"},
    {"id": "caldari",  "name": "Caldari State",       "accent": "#5b9bd5", "accent2": "#3f7fc0"},
    {"id": "minmatar", "name": "Minmatar Republic",   "accent": "#d4623a", "accent2": "#b54a28"},
]
THEMES = {p["id"]: p for p in THEME_PRESETS}


def _mix(hex_a: str, hex_b: str, t: float) -> str:
    """Линейная интерполяция двух hex-цветов (t=0 → a, t=1 → b)."""
    a = [int(hex_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_b[i:i + 2], 16) for i in (1, 3, 5)]
    c = [round(a[i] * (1 - t) + b[i] * t) for i in range(3)]
    return "#%02x%02x%02x" % tuple(c)


_QSS_TEMPLATE = """
QMainWindow, QDialog {{ background: {BG_DEEP}; }}

QWidget {{
    background: transparent;
    color: {TEXT};
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 12px;
}}

QFrame#panel {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 4px;
}}

QFrame#header_bar {{
    background: {BG_HEADER};
    border-bottom: 1px solid {BORDER};
}}

QLabel#title {{
    color: {ACCENT};
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 3px;
}}

QLabel#dim {{ color: {TEXT_DIM}; font-size: 11px; letter-spacing: 1px; }}
QLabel#accent {{ color: {ACCENT}; font-weight: bold; }}
QLabel#amber {{ color: {AMBER}; font-weight: bold; }}

QLabel#bignum {{ font-size: 30px; font-weight: bold; color: {ACCENT}; }}
QLabel#bignum_amber {{ font-size: 30px; font-weight: bold; color: {AMBER}; }}

QLabel#warn {{
    color: {AMBER};
    background: rgba(224, 165, 38, 0.08);
    border: 1px solid rgba(224, 165, 38, 0.45);
    border-radius: 3px;
    padding: 6px 10px;
    font-size: 11px;
}}

QLabel#capbadge {{
    color: {AMBER};
    border: 1px solid {AMBER};
    border-radius: 2px;
    padding: 1px 6px;
    font-size: 10px;
    font-weight: bold;
}}

QPushButton {{
    background: {BG_PANEL};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 5px 12px;
    font-size: 12px;
}}
QPushButton:hover {{ background: {BORDER}; border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton:pressed {{ background: {BORDER_LT}; }}

QPushButton#primary {{
    background: {PRIMARY_BG};
    color: {ACCENT};
    border: 1px solid {ACCENT};
    font-weight: bold;
    font-size: 13px;
    padding: 6px 20px;
}}
QPushButton#primary:hover {{ background: {PRIMARY_BG_HOVER}; }}

QPushButton#seg {{
    background: {BG_PANEL};
    color: {TEXT_DIM};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 4px 10px;
    font-size: 11px;
}}
QPushButton#seg:hover {{ color: {ACCENT}; border-color: {ACCENT2}; }}
QPushButton#seg:checked {{
    background: {PRIMARY_BG};
    color: {ACCENT};
    border: 1px solid {ACCENT};
}}

QPushButton#del {{
    background: transparent;
    border: none;
    color: {RED};
    font-size: 14px;
    font-weight: bold;
    padding: 0 6px;
}}
QPushButton#del:hover {{ color: #ff7b78; }}

QPushButton#stepMinus, QPushButton#stepPlus {{
    background: {BG_PANEL};
    border-radius: 3px;
    padding: 0;
    margin: 0;
    font-size: 15px;
    font-weight: bold;
    text-align: center;
}}
QPushButton#stepMinus {{ color: {RED};   border: 1px solid {RED}; }}
QPushButton#stepPlus  {{ color: {GREEN}; border: 1px solid {GREEN}; }}
QPushButton#stepMinus:hover {{ background: rgba(239, 83, 80, 0.18); }}
QPushButton#stepPlus:hover  {{ background: rgba(76, 175, 80, 0.18); }}
QPushButton#stepMinus:disabled, QPushButton#stepPlus:disabled {{
    color: {BORDER}; border: 1px solid {BORDER}; background: {BG_DEEP};
}}

QLineEdit, QSpinBox {{
    background: {BG_DEEP};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 5px 8px;
    selection-background-color: {SELECT_BG};
}}
QLineEdit:focus, QSpinBox:focus {{ border-color: {ACCENT}; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 0; border: none; }}

QTableWidget {{
    background: {BG_PANEL};
    color: {TEXT};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    border-radius: 3px;
    outline: none;
}}
QTableWidget::item {{ padding: 4px 8px; border: none; }}
QTableWidget::item:selected {{ background: {SELECT_BG}; color: {ACCENT}; }}

QHeaderView::section {{
    background: {BG_HEADER};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px 8px;
    font-size: 11px;
    font-weight: bold;
}}

QProgressBar {{
    background: {BG_DEEP};
    border: 1px solid {BORDER};
    border-radius: 3px;
    text-align: center;
    color: {TEXT};
    height: 10px;
    font-size: 10px;
}}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 2px; }}

QComboBox {{
    background: {BG_PANEL};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 4px 8px;
}}
QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox QAbstractItemView {{
    background: {BG_PANEL};
    color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: {SELECT_BG};
}}

QScrollBar:vertical {{ background: transparent; width: 8px; border: none; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; min-height: 20px; }}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QToolTip {{
    background: {BG_CARD};
    color: {TEXT};
    border: 1px solid {ACCENT};
    padding: 4px 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER_LT};
    background: {BG_DEEP};
    border-radius: 3px;
}}
QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
QCheckBox::indicator:checked {{
    background: {GREEN};
    border-color: {GREEN};
}}
"""


def _build_qss() -> str:
    return _QSS_TEMPLATE.format(
        BG_DEEP=BG_DEEP, BG_PANEL=BG_PANEL, BG_CARD=BG_CARD, BG_HEADER=BG_HEADER,
        BORDER=BORDER, BORDER_LT=BORDER_LT, ACCENT=ACCENT, ACCENT2=ACCENT2,
        TEXT=TEXT, TEXT_DIM=TEXT_DIM, YELLOW=YELLOW, GREEN=GREEN, ORANGE=ORANGE,
        RED=RED, AMBER=AMBER, SELECT_BG=SELECT_BG,
        PRIMARY_BG=PRIMARY_BG, PRIMARY_BG_HOVER=PRIMARY_BG_HOVER,
    )


def apply_theme(theme_id: str) -> str:
    """Применяет цветовую схему: мутирует палитру и пересобирает QSS. Возвращает QSS."""
    global ACCENT, ACCENT2, SELECT_BG, PRIMARY_BG, PRIMARY_BG_HOVER, MAIN_QSS
    t = THEMES.get(theme_id, THEMES["default"])
    ACCENT = t["accent"]
    ACCENT2 = t["accent2"]
    SELECT_BG = _mix(BG_DEEP, ACCENT, 0.32)
    PRIMARY_BG = _mix(BG_DEEP, ACCENT, 0.22)
    PRIMARY_BG_HOVER = _mix(BG_DEEP, ACCENT, 0.40)
    MAIN_QSS = _build_qss()
    return MAIN_QSS


MAIN_QSS = _build_qss()
