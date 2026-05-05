from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtGui import QColor, QPalette

DEFAULT_THEME: dict[str, str | int] = {
    "app_background": "#f5f7f8",
    "text_color": "#182026",
    "menu_background": "#ffffff",
    "panel_background": "#ffffff",
    "panel_header_background": "#ffffff",
    "input_background": "#ffffff",
    "border_color": "#d9e0e5",
    "muted_text": "#63707a",
    "sidebar_background": "#1a3a4a",
    "brand_text": "#ffffff",
    "sidebar_subtitle_text": "#adb8bd",
    "nav_text": "#d6dde1",
    "nav_active_text": "#ffffff",
    "nav_active_background": "#2e5060",
    "page_title_text": "#182026",
    "section_title_text": "#182026",
    "metric_value_text": "#182026",
    "accent_color": "#0e6b52",
    "primary_button_text": "#ffffff",
    "danger_color": "#b42318",
    "table_alt_background": "#f8fafb",
    "table_header_background": "#eef3f5",
    "table_header_text": "#63707a",
    "disabled_text": "#a0aab2",
    "font_family": "Segoe UI",
    "base_font_size": 14,
}

DARK_THEME: dict[str, str | int] = {
    "app_background": "#12151c",
    "text_color": "#dde3ed",
    "menu_background": "#1c2130",
    "panel_background": "#1c2130",
    "panel_header_background": "#1c2130",
    "input_background": "#252d3d",
    "border_color": "#313d52",
    "muted_text": "#7a8799",
    "sidebar_background": "#0b0e16",
    "brand_text": "#ffffff",
    "sidebar_subtitle_text": "#45526a",
    "nav_text": "#8d9db5",
    "nav_active_text": "#ffffff",
    "nav_active_background": "#2a3548",
    "page_title_text": "#dde3ed",
    "section_title_text": "#dde3ed",
    "metric_value_text": "#dde3ed",
    "accent_color": "#10b981",
    "primary_button_text": "#ffffff",
    "danger_color": "#f87171",
    "table_alt_background": "#1a2133",
    "table_header_background": "#1c2130",
    "table_header_text": "#7a8799",
    "disabled_text": "#3d4d63",
    "font_family": "Segoe UI",
    "base_font_size": 14,
}

STYLE_TEMPLATE = """
/* ── Base ─────────────────────────────────────────────────────────────── */
QWidget {{
    background: __APP_BACKGROUND__;
    color: __TEXT_COLOR__;
    font-family: "__FONT_FAMILY__", "San Francisco", Arial, sans-serif;
    font-size: __BASE_FONT_SIZE__px;
}}

QDialog {{
    background: __APP_BACKGROUND__;
}}

/* ── Menú ─────────────────────────────────────────────────────────────── */
QMenuBar {{
    background: __MENU_BACKGROUND__;
    border-bottom: 1px solid __BORDER_COLOR__;
    color: __TEXT_COLOR__;
}}

QMenuBar::item:selected {{
    background: __ACCENT_COLOR__;
    color: __PRIMARY_BUTTON_TEXT__;
    border-radius: 4px;
}}

QMenu {{
    background: __PANEL_BACKGROUND__;
    color: __TEXT_COLOR__;
    border: 1px solid __BORDER_COLOR__;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background: __ACCENT_COLOR__;
    color: __PRIMARY_BUTTON_TEXT__;
}}

QMenu::separator {{
    height: 1px;
    background: __BORDER_COLOR__;
    margin: 4px 8px;
}}

/* ── Botones ──────────────────────────────────────────────────────────── */
QPushButton {{
    min-height: 34px;
    border: 1px solid __BORDER_COLOR__;
    border-radius: 8px;
    background: __PANEL_BACKGROUND__;
    color: __TEXT_COLOR__;
    padding: 0 12px;
}}

QPushButton:hover {{
    border-color: __ACCENT_COLOR__;
}}

QPushButton:pressed {{
    background: __BORDER_COLOR__;
}}

QPushButton:disabled {{
    color: __DISABLED_TEXT__;
    border-color: __BORDER_COLOR__;
}}

QPushButton#primaryButton {{
    border-color: __ACCENT_COLOR__;
    background: __ACCENT_COLOR__;
    color: __PRIMARY_BUTTON_TEXT__;
}}

QPushButton#primaryButton:hover {{
    background: __ACCENT_COLOR__;
    border-color: __ACCENT_COLOR__;
}}

QPushButton#dangerButton {{
    border-color: __DANGER_COLOR__;
    color: __DANGER_COLOR__;
    background: __PANEL_BACKGROUND__;
}}

/* ── Inputs ───────────────────────────────────────────────────────────── */
QLineEdit {{
    min-height: 34px;
    border: 1px solid __BORDER_COLOR__;
    border-radius: 8px;
    background: __INPUT_BACKGROUND__;
    color: __TEXT_COLOR__;
    padding: 0 12px;
}}

QLineEdit:focus {{
    border-color: __ACCENT_COLOR__;
}}

QComboBox,
QDateEdit,
QDoubleSpinBox,
QSpinBox {{
    min-height: 34px;
    border: 1px solid __BORDER_COLOR__;
    border-radius: 8px;
    background: __INPUT_BACKGROUND__;
    color: __TEXT_COLOR__;
    padding: 0 8px;
}}

QTextEdit,
QListWidget {{
    border: 1px solid __BORDER_COLOR__;
    border-radius: 8px;
    background: __INPUT_BACKGROUND__;
    color: __TEXT_COLOR__;
    padding: 6px 8px;
}}

QComboBox:focus, QDateEdit:focus,
QDoubleSpinBox:focus, QSpinBox:focus {{
    border-color: __ACCENT_COLOR__;
}}

/* Botón desplegable del ComboBox/DateEdit */
QComboBox::drop-down, QDateEdit::drop-down {{
    border: none;
    width: 24px;
}}

/* Lista desplegable (crítica para dark mode) */
QComboBox QAbstractItemView,
QAbstractItemView {{
    background: __INPUT_BACKGROUND__;
    color: __TEXT_COLOR__;
    border: 1px solid __BORDER_COLOR__;
    selection-background-color: __ACCENT_COLOR__;
    selection-color: __PRIMARY_BUTTON_TEXT__;
    outline: none;
}}

QComboBox QAbstractItemView::item {{
    padding: 6px 8px;
    min-height: 28px;
}}

QComboBox QAbstractItemView::item:hover {{
    background: __NAV_ACTIVE_BG__;
    color: __TEXT_COLOR__;
}}

/* SpinBox buttons */
QAbstractSpinBox::up-button,
QAbstractSpinBox::down-button {{
    background: __INPUT_BACKGROUND__;
    border: none;
}}

/* ── Scrollbars ───────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: __APP_BACKGROUND__;
    width: 8px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: __BORDER_COLOR__;
    border-radius: 4px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: __MUTED_TEXT__;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: __APP_BACKGROUND__;
    height: 8px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: __BORDER_COLOR__;
    border-radius: 4px;
    min-width: 24px;
}}

QScrollBar::handle:horizontal:hover {{
    background: __MUTED_TEXT__;
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── Tooltip ──────────────────────────────────────────────────────────── */
QToolTip {{
    background: __PANEL_BACKGROUND__;
    color: __TEXT_COLOR__;
    border: 1px solid __BORDER_COLOR__;
    padding: 4px 8px;
}}

/* ── Checkbox ─────────────────────────────────────────────────────────── */
QCheckBox {{
    background: transparent;
    spacing: 8px;
    color: __TEXT_COLOR__;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid __BORDER_COLOR__;
    border-radius: 4px;
    background: __INPUT_BACKGROUND__;
}}

QCheckBox::indicator:hover {{
    border-color: __ACCENT_COLOR__;
}}

QCheckBox::indicator:checked {{
    border-color: __ACCENT_COLOR__;
    background: __ACCENT_COLOR__;
}}

QCheckBox::indicator:disabled {{
    border-color: __BORDER_COLOR__;
    background: __APP_BACKGROUND__;
}}

/* ── Frames y paneles ─────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: none;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QFrame#sidebar {{
    background: __SIDEBAR_BACKGROUND__;
}}

QFrame#topbar,
QFrame#panel,
QFrame#metric {{
    background: __PANEL_BACKGROUND__;
    border: 1px solid __BORDER_COLOR__;
}}

QFrame#topbar {{
    border-left: none;
    border-right: none;
    border-top: none;
}}

QFrame#panel,
QFrame#metric {{
    border-radius: 8px;
}}

QFrame#panelHeader {{
    min-height: 56px;
    background: __PANEL_HEADER_BACKGROUND__;
    border-bottom: 1px solid __BORDER_COLOR__;
}}

/* ── Labels ───────────────────────────────────────────────────────────── */
QLabel#brand {{
    background: transparent;
    color: __BRAND_TEXT__;
    font-size: 15px;
    font-weight: 700;
}}

QLabel#sidebarSubtitle {{
    background: transparent;
    color: __SIDEBAR_SUBTITLE_TEXT__;
    font-size: 12px;
}}

QPushButton#navButton,
QPushButton#navButtonActive {{
    min-height: 36px;
    border: none;
    border-radius: 8px;
    color: __SIDEBAR_TEXT__;
    text-align: left;
    padding-left: 12px;
    background: transparent;
}}

QPushButton#navButton:hover,
QPushButton#navButtonActive {{
    background: __SIDEBAR_HOVER_BACKGROUND__;
    color: __SIDEBAR_ACTIVE_TEXT__;
}}

QLabel#pageTitle {{
    background: transparent;
    color: __PAGE_TITLE_TEXT__;
    font-size: 20px;
    font-weight: 700;
}}

QLabel#sectionTitle {{
    background: transparent;
    color: __SECTION_TITLE_TEXT__;
    font-size: 16px;
    font-weight: 700;
}}

QLabel#muted {{
    background: transparent;
    color: __MUTED_TEXT__;
    font-size: 12px;
}}

QLabel#metricValue {{
    background: transparent;
    color: __METRIC_VALUE_TEXT__;
    font-size: 24px;
    font-weight: 700;
}}

QWidget#actionButtons {{
    background: transparent;
}}

/* ── Tabla ────────────────────────────────────────────────────────────── */
QTableWidget {{
    background: __PANEL_BACKGROUND__;
    alternate-background-color: __TABLE_ALT_BACKGROUND__;
    color: __TEXT_COLOR__;
    border: none;
    gridline-color: __BORDER_COLOR__;
    selection-background-color: __ACCENT_COLOR__;
    selection-color: __PRIMARY_BUTTON_TEXT__;
}}

QTableWidget::item {{
    padding: 4px;
    color: __TEXT_COLOR__;
    border: none;
}}

QTableWidget::item:selected {{
    background: __ACCENT_COLOR__;
    color: __PRIMARY_BUTTON_TEXT__;
}}

QHeaderView::section {{
    background: __TABLE_HEADER_BACKGROUND__;
    color: __TABLE_HEADER_TEXT__;
    border: none;
    border-bottom: 1px solid __BORDER_COLOR__;
    padding: 10px;
    font-size: 12px;
    font-weight: 700;
}}

QHeaderView::section:checked {{
    background: __ACCENT_COLOR__;
}}

/* ── DialogButtonBox ──────────────────────────────────────────────────── */
QDialogButtonBox QPushButton {{
    min-width: 80px;
}}
"""


def default_theme() -> dict[str, str | int]:
    return DEFAULT_THEME.copy()


def dark_theme() -> dict[str, str | int]:
    return DARK_THEME.copy()


def get_theme(mode: str) -> dict[str, str | int]:
    return dark_theme() if mode == "dark" else default_theme()


def load_theme_colors(theme_path: Path, base_theme: dict[str, str | int]) -> dict[str, str | int]:
    """Aplica colores guardados desde theme.json sobre base_theme."""
    result = base_theme.copy()
    if not theme_path.exists():
        return result
    try:
        data = json.loads(theme_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return result
    for key, value in data.items():
        if key.startswith("_") or key not in result:
            continue
        if key == "base_font_size":
            try:
                result[key] = int(value)
            except (ValueError, TypeError):
                pass
        else:
            result[key] = str(value)
    return result


def save_theme_colors(theme_path: Path, theme: dict[str, str | int]) -> None:
    """Guarda todos los colores del tema en theme.json, preservando _mode."""
    data: dict[str, object] = {}
    if theme_path.exists():
        try:
            data = json.loads(theme_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    for key, value in theme.items():
        data[key] = value
    theme_path.parent.mkdir(parents=True, exist_ok=True)
    theme_path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def load_theme_mode(theme_path: Path) -> str:
    if not theme_path.exists():
        return "light"
    try:
        data = json.loads(theme_path.read_text(encoding="utf-8"))
        mode = data.get("_mode", "light")
        return "dark" if mode == "dark" else "light"
    except (json.JSONDecodeError, OSError):
        return "light"


def save_theme_mode(theme_path: Path, mode: str) -> None:
    data: dict[str, object] = {}
    if theme_path.exists():
        try:
            data = json.loads(theme_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data["_mode"] = mode
    theme_path.parent.mkdir(parents=True, exist_ok=True)
    theme_path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def build_app_styles(theme: dict[str, str | int]) -> str:
    replacements = {
        "__APP_BACKGROUND__": str(theme["app_background"]),
        "__TEXT_COLOR__": str(theme["text_color"]),
        "__MENU_BACKGROUND__": str(theme["menu_background"]),
        "__PANEL_BACKGROUND__": str(theme["panel_background"]),
        "__PANEL_HEADER_BACKGROUND__": str(theme["panel_header_background"]),
        "__INPUT_BACKGROUND__": str(theme["input_background"]),
        "__BORDER_COLOR__": str(theme["border_color"]),
        "__MUTED_TEXT__": str(theme["muted_text"]),
        "__SIDEBAR_BACKGROUND__": str(theme["sidebar_background"]),
        "__BRAND_TEXT__": str(theme["brand_text"]),
        "__SIDEBAR_SUBTITLE_TEXT__": str(theme["sidebar_subtitle_text"]),
        "__SIDEBAR_TEXT__": str(theme["nav_text"]),
        "__SIDEBAR_ACTIVE_TEXT__": str(theme["nav_active_text"]),
        "__SIDEBAR_HOVER_BACKGROUND__": str(theme["nav_active_background"]),
        "__NAV_ACTIVE_BG__": str(theme["nav_active_background"]),
        "__PAGE_TITLE_TEXT__": str(theme["page_title_text"]),
        "__SECTION_TITLE_TEXT__": str(theme["section_title_text"]),
        "__METRIC_VALUE_TEXT__": str(theme["metric_value_text"]),
        "__ACCENT_COLOR__": str(theme["accent_color"]),
        "__PRIMARY_BUTTON_TEXT__": str(theme["primary_button_text"]),
        "__DANGER_COLOR__": str(theme["danger_color"]),
        "__TABLE_ALT_BACKGROUND__": str(theme["table_alt_background"]),
        "__TABLE_HEADER_BACKGROUND__": str(theme["table_header_background"]),
        "__TABLE_HEADER_TEXT__": str(theme["table_header_text"]),
        "__DISABLED_TEXT__": str(theme.get("disabled_text", "#a0aab2")),
        "__FONT_FAMILY__": str(theme["font_family"]),
        "__BASE_FONT_SIZE__": str(theme["base_font_size"]),
    }

    stylesheet = STYLE_TEMPLATE
    for placeholder, value in replacements.items():
        stylesheet = stylesheet.replace(placeholder, value)
    return stylesheet


def build_app_palette(theme: dict[str, str | int]) -> QPalette:
    t = theme
    c = QColor

    bg        = c(str(t["app_background"]))
    panel     = c(str(t["panel_background"]))
    inp       = c(str(t["input_background"]))
    alt       = c(str(t["table_alt_background"]))
    text      = c(str(t["text_color"]))
    muted     = c(str(t["muted_text"]))
    border    = c(str(t["border_color"]))
    accent    = c(str(t["accent_color"]))
    btn_text  = c(str(t["primary_button_text"]))
    disabled  = c(str(t.get("disabled_text", "#a0aab2")))

    # Derive shadow/mid colors from background
    dark_v   = bg.darker(130)
    mid_v    = bg.darker(110)
    shadow_v = bg.darker(180)
    light_v  = panel.lighter(115)

    palette = QPalette()
    R = QPalette.ColorRole
    G = QPalette.ColorGroup

    # Active group (normal state)
    palette.setColor(R.Window,          bg)
    palette.setColor(R.WindowText,      text)
    palette.setColor(R.Base,            inp)
    palette.setColor(R.AlternateBase,   alt)
    palette.setColor(R.Text,            text)
    palette.setColor(R.BrightText,      btn_text)
    palette.setColor(R.Button,          panel)
    palette.setColor(R.ButtonText,      text)
    palette.setColor(R.Highlight,       accent)
    palette.setColor(R.HighlightedText, btn_text)
    palette.setColor(R.Link,            accent)
    palette.setColor(R.LinkVisited,     accent)
    palette.setColor(R.ToolTipBase,     panel)
    palette.setColor(R.ToolTipText,     text)
    palette.setColor(R.Light,           light_v)
    palette.setColor(R.Midlight,        mid_v.lighter(110))
    palette.setColor(R.Mid,             mid_v)
    palette.setColor(R.Dark,            dark_v)
    palette.setColor(R.Shadow,          shadow_v)

    # Placeholder text (PySide6 6.x)
    try:
        palette.setColor(R.PlaceholderText, muted)  # type: ignore[attr-defined]
    except AttributeError:
        pass

    # Disabled group
    palette.setColor(G.Disabled, R.WindowText,  disabled)
    palette.setColor(G.Disabled, R.Text,        disabled)
    palette.setColor(G.Disabled, R.ButtonText,  disabled)
    palette.setColor(G.Disabled, R.Highlight,   border)
    palette.setColor(G.Disabled, R.Base,        bg)
    palette.setColor(G.Disabled, R.Button,      bg)

    return palette
