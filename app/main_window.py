"""Main application window with sidebar navigation."""

import os
import sys

from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QFont, QColor, QPainter, QLinearGradient, QPen, QCloseEvent, QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
)


def _asset_path(filename: str) -> str:
    """Return the absolute path to an asset file, works both in dev and PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", filename)

from app.styles import (
    GLOBAL_STYLE, SIDEBAR_STYLE,
    BG_DARKEST, BG_DARK, BG_CARD, BG_ELEVATED, BG_HOVER,
    ACCENT, ACCENT_HOVER, ACCENT2, ACCENT3,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    BORDER, RADIUS,
)
from app.pages.convert import ConvertPage
from app.pages.trim import TrimPage
from app.pages.audio import AudioPage
from app.pages.filters import FiltersPage
from app.pages.merge import MergePage
from app.pages.resize import ResizePage
from app.pages.screenshots import ScreenshotsPage
from app.pages.metadata import MetadataPage
from app.pages.advanced import AdvancedPage
from app.pages.presets import PresetsPage
from app.pages.about import AboutPage


# ── SVG icons (inline, no external files needed) ───────────────────────

# Each icon is a simple SVG path rendered via QIcon
ICONS = {
    "convert": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/>'
        '<polyline points="8 21 3 21 3 16"/><line x1="20" y1="4" x2="3" y2="21"/></svg>'
    ),
    "trim": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/>'
        '<line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/>'
        '<line x1="8.12" y1="8.12" x2="12" y2="12"/></svg>'
    ),
    "audio": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>'
    ),
    "filters": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>'
    ),
    "merge": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="15 4 20 4 20 9"/><line x1="14" y1="10" x2="20" y2="4"/>'
        '<polyline points="15 20 20 20 20 15"/><line x1="14" y1="14" x2="20" y2="20"/>'
        '<line x1="4" y1="12" x2="14" y2="12"/></svg>'
    ),
    "resize": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/>'
        '<line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>'
    ),
    "screenshots": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>'
        '<circle cx="12" cy="13" r="4"/></svg>'
    ),
    "metadata": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>'
        '<line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>'
    ),
    "advanced": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>'
    ),
    "presets": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="2" y="3" width="20" height="18" rx="2" ry="2"/>'
        '<line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/>'
        '<line x1="8" y1="16" x2="12" y2="16"/></svg>'
    ),
    "about": (
        '<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/>'
        '<line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
    ),
}


def _svg_icon(name: str, color: str = TEXT_PRIMARY, size: int = 20) -> QIcon:
    """Create a QIcon from an inline SVG string."""
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtGui import QPixmap, QPainter
    from PySide6.QtCore import QByteArray

    svg_str = ICONS.get(name, ICONS["convert"]).replace("{color}", color)
    renderer = QSvgRenderer(QByteArray(svg_str.encode()))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


# ── Page definitions ────────────────────────────────────────────────────

PAGE_DEFS = [
    ("presets",     "Presets",      PresetsPage),
    ("convert",     "Convert",      ConvertPage),
    ("trim",        "Trim / Cut",   TrimPage),
    ("audio",       "Audio",        AudioPage),
    ("filters",     "Filters",      FiltersPage),
    ("merge",       "Merge",        MergePage),
    ("resize",      "Resize",       ResizePage),
    ("screenshots", "Screenshots",  ScreenshotsPage),
    ("metadata",    "Metadata",     MetadataPage),
    ("advanced",    "Advanced",     AdvancedPage),
    ("about",       "About",        AboutPage),
]


# ── Sidebar button ──────────────────────────────────────────────────────

class SidebarButton(QPushButton):
    """A stylish sidebar navigation button."""

    def __init__(self, icon_name: str, label: str, parent=None):
        super().__init__(parent)
        self._icon_name = icon_name
        self._label_text = label
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(46)
        self.setMinimumWidth(200)

        self.setText(f"  {label}")
        self.setIcon(_svg_icon(icon_name, TEXT_SECONDARY))
        self.setIconSize(QSize(20, 20))

        self.setStyleSheet(self._base_style(False))

    def _base_style(self, active: bool) -> str:
        if active:
            return (
                f"QPushButton {{ background: {BG_ELEVATED}; color: {TEXT_PRIMARY}; "
                f"border: none; border-left: 3px solid {ACCENT}; border-radius: 0px; "
                f"text-align: left; padding: 0 16px; font-size: 13px; font-weight: 600; }}"
            )
        return (
            f"QPushButton {{ background: transparent; color: {TEXT_SECONDARY}; "
            f"border: none; border-left: 3px solid transparent; border-radius: 0px; "
            f"text-align: left; padding: 0 16px; font-size: 13px; font-weight: 500; }}"
            f"QPushButton:hover {{ background: {BG_HOVER}; color: {TEXT_PRIMARY}; }}"
        )

    def set_active(self, active: bool):
        self.setChecked(active)
        self.setStyleSheet(self._base_style(active))
        color = ACCENT if active else TEXT_SECONDARY
        self.setIcon(_svg_icon(self._icon_name, color))


# ── Accent stripe (decorative gradient bar at top of sidebar) ───────────

class GradientStripe(QWidget):
    """Thin decorative gradient line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, QColor(ACCENT))
        grad.setColorAt(0.5, QColor(ACCENT2))
        grad.setColorAt(1.0, QColor(ACCENT3))
        p.fillRect(self.rect(), grad)
        p.end()


# ── Main Window ─────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFmpeg Studio")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)

        # Window icon (from asset file)
        self.setWindowIcon(QIcon(_asset_path("icon.ico")))

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(
            f"QFrame {{ background: {BG_DARK}; border-right: 1px solid {BORDER}; }}"
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Gradient stripe at top
        sidebar_layout.addWidget(GradientStripe())

        # Logo / brand
        brand = QWidget()
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(16, 16, 16, 8)

        logo_pixmap = QPixmap(_asset_path("logo.png"))
        logo_label = QLabel()
        logo_label.setPixmap(logo_pixmap.scaledToWidth(180, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        brand_layout.addWidget(logo_label)

        version = QLabel("v1.0  ·  Professional Edition")
        version.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; background: transparent; "
            f"letter-spacing: 0.3px;"
        )
        brand_layout.addWidget(version)
        sidebar_layout.addWidget(brand)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {BORDER}; border: none; max-height: 1px;")
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(8)

        # Navigation buttons
        self._nav_buttons: list[SidebarButton] = []
        for icon_name, label, _ in PAGE_DEFS:
            btn = SidebarButton(icon_name, label)
            btn.clicked.connect(lambda checked, n=icon_name: self._nav_to(n))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Bottom info
        info = QLabel("Requires ffmpeg in PATH")
        info.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; padding: 12px 16px; background: transparent;"
        )
        info.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(info)

        root.addWidget(sidebar)

        # ── Content area ───────────────────────────
        content_frame = QFrame()
        content_frame.setStyleSheet(f"background: {BG_DARKEST};")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        self._page_map = {}

        for icon_name, label, PageClass in PAGE_DEFS:
            page = PageClass()
            idx = self._stack.addWidget(page)
            self._page_map[icon_name] = idx

        content_layout.addWidget(self._stack)
        root.addWidget(content_frame, 1)

        # Start on Presets page
        self._nav_to("presets")

    def _nav_to(self, name: str):
        idx = self._page_map.get(name, 0)
        self._stack.setCurrentIndex(idx)

        for i, (icon_name, _, _) in enumerate(PAGE_DEFS):
            self._nav_buttons[i].set_active(icon_name == name)

    def closeEvent(self, event: QCloseEvent):
        """Ensure worker threads are stopped before closing."""
        for i in range(self._stack.count()):
            page = self._stack.widget(i)
            worker = getattr(page, "_worker", None)
            if worker is not None and worker.isRunning():
                worker.cancel()
                worker.wait(3000)
        event.accept()
