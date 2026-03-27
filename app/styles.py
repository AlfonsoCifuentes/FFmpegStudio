"""Premium dark theme styling for FFmpeg Studio."""

# ── Colour palette ───────────────────────────────────────────────
BG_DARKEST  = "#0B0E14"
BG_DARK     = "#0F1219"
BG_CARD     = "#161B26"
BG_ELEVATED = "#1C2333"
BG_HOVER    = "#232B3E"
BG_INPUT    = "#131824"

BORDER      = "#1E2738"
BORDER_FOCUS = "#6C5CE7"

ACCENT      = "#6C5CE7"   # Primary purple
ACCENT_HOVER = "#7E6FF2"
ACCENT2     = "#00B4D8"   # Teal accent
ACCENT3     = "#00D68F"   # Green / success
WARN        = "#FDCB6E"   # Warning yellow
DANGER      = "#FF6B6B"   # Error / danger

TEXT_PRIMARY   = "#E8ECF4"
TEXT_SECONDARY = "#8892A8"
TEXT_MUTED     = "#5A6478"
TEXT_ACCENT    = ACCENT

RADIUS  = "10px"
RADIUS_SM = "6px"
RADIUS_LG = "14px"


def _scrollbar():
    return f"""
    QScrollBar:vertical {{
        background: {BG_DARK};
        width: 8px;
        margin: 0;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        min-height: 40px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {TEXT_MUTED};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {BG_DARK};
        height: 8px;
        margin: 0;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER};
        min-width: 40px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {TEXT_MUTED};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    """


GLOBAL_STYLE = f"""
/* ── Global ──────────────────────────────────────────── */
* {{
    font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}

QMainWindow {{
    background-color: {BG_DARKEST};
}}

QWidget {{
    background-color: transparent;
}}

QToolTip {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SM};
    padding: 6px 10px;
}}

/* ── Labels ──────────────────────────────────────────── */
QLabel {{
    color: {TEXT_PRIMARY};
    background: transparent;
}}

QLabel[class="heading"] {{
    font-size: 22px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}

QLabel[class="subheading"] {{
    font-size: 14px;
    font-weight: 500;
    color: {TEXT_SECONDARY};
}}

QLabel[class="section"] {{
    font-size: 11px;
    font-weight: 700;
    color: {TEXT_MUTED};
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Buttons ─────────────────────────────────────────── */
QPushButton {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    padding: 9px 22px;
    font-weight: 600;
    font-size: 13px;
    min-height: 18px;
}}
QPushButton:hover {{
    background-color: {BG_HOVER};
    border-color: {TEXT_MUTED};
}}
QPushButton:pressed {{
    background-color: {BORDER};
}}
QPushButton:disabled {{
    color: {TEXT_MUTED};
    border-color: {BORDER};
}}

QPushButton[class="primary"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT}, stop:1 #8B7CF7);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 10px 28px;
}}
QPushButton[class="primary"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_HOVER}, stop:1 #9B8FFF);
}}
QPushButton[class="primary"]:pressed {{
    background: {ACCENT};
}}
QPushButton[class="primary"]:disabled {{
    background: {BG_ELEVATED};
    color: {TEXT_MUTED};
}}

QPushButton[class="danger"] {{
    background: {DANGER};
    color: #FFFFFF;
    border: none;
    font-weight: 700;
}}
QPushButton[class="danger"]:hover {{
    background: #FF8787;
}}

QPushButton[class="success"] {{
    background: {ACCENT3};
    color: #0B0E14;
    border: none;
    font-weight: 700;
}}
QPushButton[class="success"]:hover {{
    background: #33E0A5;
}}

/* ── Inputs / LineEdit ───────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SM};
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {BORDER_FOCUS};
}}
QLineEdit:disabled {{
    color: {TEXT_MUTED};
}}

/* ── ComboBox ────────────────────────────────────────── */
QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SM};
    padding: 8px 12px;
    min-width: 140px;
    font-size: 13px;
}}
QComboBox:hover {{
    border-color: {TEXT_MUTED};
}}
QComboBox:focus {{
    border-color: {BORDER_FOCUS};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 28px;
    border: none;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {TEXT_SECONDARY};
}}
QComboBox QAbstractItemView {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SM};
    selection-background-color: {ACCENT};
    selection-color: #FFFFFF;
    outline: none;
    padding: 4px;
}}

/* ── TextEdit / PlainTextEdit ────────────────────────── */
QTextEdit, QPlainTextEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SM};
    padding: 8px;
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 12px;
    selection-background-color: {ACCENT};
}}
QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {BORDER_FOCUS};
}}

/* ── CheckBox & Radio ────────────────────────────────── */
QCheckBox {{
    spacing: 8px;
    color: {TEXT_PRIMARY};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {BORDER};
    background: {BG_INPUT};
}}
QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
    image: none;
}}

QRadioButton {{
    spacing: 8px;
    color: {TEXT_PRIMARY};
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid {BORDER};
    background: {BG_INPUT};
}}
QRadioButton::indicator:hover {{
    border-color: {ACCENT};
}}
QRadioButton::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}

/* ── Slider ──────────────────────────────────────────── */
QSlider::groove:horizontal {{
    height: 6px;
    background: {BORDER};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    background: {ACCENT_HOVER};
}}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT}, stop:1 {ACCENT2});
    border-radius: 3px;
}}

/* ── ProgressBar ─────────────────────────────────────── */
QProgressBar {{
    background-color: {BG_INPUT};
    border: none;
    border-radius: 6px;
    text-align: center;
    color: {TEXT_PRIMARY};
    font-weight: 600;
    font-size: 11px;
    min-height: 12px;
    max-height: 12px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT}, stop:1 {ACCENT2});
    border-radius: 6px;
}}

/* ── TabWidget ───────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    background-color: {BG_CARD};
    padding: 8px;
}}
QTabBar::tab {{
    background: {BG_ELEVATED};
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: {RADIUS_SM};
    border-top-right-radius: {RADIUS_SM};
    padding: 8px 18px;
    margin-right: 2px;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    background: {BG_CARD};
    color: {TEXT_PRIMARY};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{
    background: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}

/* ── GroupBox ─────────────────────────────────────────── */
QGroupBox {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS};
    margin-top: 16px;
    padding: 20px 16px 16px 16px;
    font-weight: 600;
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 12px;
    color: {ACCENT};
    font-weight: 700;
    font-size: 12px;
}}

/* ── ListWidget ──────────────────────────────────────── */
QListWidget {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SM};
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 8px 12px;
    border-radius: {RADIUS_SM};
    color: {TEXT_PRIMARY};
}}
QListWidget::item:selected {{
    background-color: {ACCENT};
    color: #FFFFFF;
}}
QListWidget::item:hover:!selected {{
    background-color: {BG_HOVER};
}}

/* ── TableWidget ─────────────────────────────────────── */
QTableWidget {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SM};
    gridline-color: {BORDER};
    selection-background-color: {ACCENT};
    selection-color: #FFFFFF;
    outline: none;
}}
QTableWidget::item {{
    padding: 6px 10px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {ACCENT};
    color: #FFFFFF;
}}
QHeaderView::section {{
    background-color: {BG_ELEVATED};
    color: {TEXT_SECONDARY};
    border: none;
    border-bottom: 1px solid {BORDER};
    border-right: 1px solid {BORDER};
    padding: 8px 12px;
    font-weight: 700;
    font-size: 12px;
}}
QHeaderView::section:hover {{
    background-color: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}
QTableCornerButton::section {{
    background-color: {BG_ELEVATED};
    border: none;
    border-bottom: 1px solid {BORDER};
    border-right: 1px solid {BORDER};
}}

/* ── Scrollbars ──────────────────────────────────────── */
{_scrollbar()}

/* ── Splitter ────────────────────────────────────────── */
QSplitter::handle {{
    background: {BORDER};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}
"""

# ── Sidebar-specific styles ──────────────────────────────────────
SIDEBAR_STYLE = f"""
QFrame#sidebar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BG_DARK}, stop:1 #0A0D12);
    border-right: 1px solid {BORDER};
}}

QPushButton#sidebarBtn {{
    background: transparent;
    color: {TEXT_SECONDARY};
    border: none;
    border-radius: {RADIUS};
    padding: 11px 18px;
    text-align: left;
    font-weight: 500;
    font-size: 13px;
}}
QPushButton#sidebarBtn:hover {{
    background-color: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}
QPushButton#sidebarBtn[active="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(108, 92, 231, 0.20), stop:1 rgba(108, 92, 231, 0.05));
    color: {ACCENT};
    font-weight: 700;
    border-left: 3px solid {ACCENT};
    padding-left: 15px;
}}
"""

# ── Card / Panel ─────────────────────────────────────────────────
CARD_STYLE = f"""
QFrame#card {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_LG};
    padding: 0;
}}
"""

# ── Drop zone ────────────────────────────────────────────────────
DROP_ZONE_STYLE = f"""
QFrame#dropZone {{
    background-color: {BG_INPUT};
    border: 2px dashed {BORDER};
    border-radius: {RADIUS_LG};
    min-height: 120px;
}}
QFrame#dropZone:hover {{
    border-color: {ACCENT};
    background-color: rgba(108, 92, 231, 0.05);
}}
"""

# ── Log panel ────────────────────────────────────────────────────
LOG_STYLE = f"""
QPlainTextEdit#logPanel {{
    background-color: #0A0D11;
    color: {ACCENT3};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SM};
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 11px;
    padding: 10px;
}}
"""
