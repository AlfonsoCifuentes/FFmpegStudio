"""About page – author info, version details, and update checker."""

import json
import urllib.request
import urllib.error

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QSizePolicy,
)

from app.styles import (
    ACCENT, ACCENT2, ACCENT3, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    BG_CARD, BG_ELEVATED, BG_HOVER, BORDER, RADIUS, RADIUS_SM, RADIUS_LG,
    DANGER, WARN,
)

APP_VERSION = "1.0.0"
GITHUB_REPO = "AlfonsoCifuentes/FFmpegStudio"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


class _UpdateChecker(QThread):
    """Background thread that queries GitHub for the latest release."""
    result = Signal(str, str)  # (latest_version, download_url)  or ("error", message)

    def run(self):
        try:
            req = urllib.request.Request(
                RELEASES_API,
                headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "FFmpegStudio"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "").lstrip("vV")
            assets = data.get("assets", [])
            dl = ""
            for a in assets:
                if a.get("name", "").lower().endswith(".exe"):
                    dl = a.get("browser_download_url", "")
                    break
            if not dl:
                dl = data.get("html_url", GITHUB_URL + "/releases")
            self.result.emit(tag, dl)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.result.emit("error", "No releases published yet.")
            else:
                self.result.emit("error", f"GitHub API error: {e.code}")
        except Exception as exc:
            self.result.emit("error", str(exc))


class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checker = None

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # ── Logo + title area ──────────────────────
        header = QWidget()
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignCenter)
        h_layout.setSpacing(10)

        # Logo
        from app.main_window import _asset_path
        logo_path = _asset_path("logo.png")
        if os.path.exists(logo_path):
            logo_pix = QPixmap(logo_path)
            logo_lbl = QLabel()
            logo_lbl.setPixmap(logo_pix.scaledToWidth(220, Qt.SmoothTransformation))
            logo_lbl.setAlignment(Qt.AlignCenter)
            logo_lbl.setStyleSheet("background: transparent;")
            h_layout.addWidget(logo_lbl)

        ver_label = QLabel(f"Version {APP_VERSION}")
        ver_label.setAlignment(Qt.AlignCenter)
        ver_label.setStyleSheet(
            f"color: {ACCENT}; font-size: 16px; font-weight: 700; background: transparent;"
        )
        h_layout.addWidget(ver_label)

        layout.addWidget(header)

        # ── Author card ────────────────────────────
        author_card = QFrame()
        author_card.setStyleSheet(
            f"QFrame {{ background: {BG_CARD}; border: 1px solid {BORDER}; "
            f"border-radius: {RADIUS_LG}; padding: 24px; }}"
        )
        ac_layout = QVBoxLayout(author_card)
        ac_layout.setSpacing(8)

        ac_title = QLabel("AUTHOR")
        ac_title.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 800; "
            f"letter-spacing: 2px; background: transparent;"
        )
        ac_layout.addWidget(ac_title)

        name = QLabel("Alfonso Cifuentes Alonso")
        name.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 20px; font-weight: 700; background: transparent;"
        )
        ac_layout.addWidget(name)

        desc = QLabel(
            "FFmpeg Studio is a free, open-source graphical frontend for FFmpeg "
            "designed to make media encoding accessible to everyone. "
            "Built with Python and PySide6."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.5; background: transparent;")
        ac_layout.addWidget(desc)

        layout.addWidget(author_card)

        # ── Links card ──────────────────────────────
        links_card = QFrame()
        links_card.setStyleSheet(
            f"QFrame {{ background: {BG_CARD}; border: 1px solid {BORDER}; "
            f"border-radius: {RADIUS_LG}; padding: 24px; }}"
        )
        lc_layout = QVBoxLayout(links_card)
        lc_layout.setSpacing(8)

        lc_title = QLabel("LINKS")
        lc_title.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 800; "
            f"letter-spacing: 2px; background: transparent;"
        )
        lc_layout.addWidget(lc_title)

        gh_btn = QPushButton(f"  GitHub Repository  —  {GITHUB_REPO}")
        gh_btn.setCursor(Qt.PointingHandCursor)
        gh_btn.setStyleSheet(
            f"QPushButton {{ background: {BG_ELEVATED}; color: {ACCENT2}; "
            f"border: 1px solid {BORDER}; border-radius: {RADIUS_SM}; padding: 10px 16px; "
            f"font-size: 13px; font-weight: 600; text-align: left; }}"
            f"QPushButton:hover {{ background: {BG_HOVER}; border-color: {ACCENT2}; }}"
        )
        gh_btn.clicked.connect(lambda: QDesktopServices.openUrl(GITHUB_URL))
        lc_layout.addWidget(gh_btn)

        issues_btn = QPushButton("  Report a Bug / Request a Feature")
        issues_btn.setCursor(Qt.PointingHandCursor)
        issues_btn.setStyleSheet(
            f"QPushButton {{ background: {BG_ELEVATED}; color: {TEXT_SECONDARY}; "
            f"border: 1px solid {BORDER}; border-radius: {RADIUS_SM}; padding: 10px 16px; "
            f"font-size: 13px; font-weight: 600; text-align: left; }}"
            f"QPushButton:hover {{ background: {BG_HOVER}; border-color: {TEXT_MUTED}; }}"
        )
        issues_btn.clicked.connect(lambda: QDesktopServices.openUrl(GITHUB_URL + "/issues"))
        lc_layout.addWidget(issues_btn)

        layout.addWidget(links_card)

        # ── Update checker card ─────────────────────
        update_card = QFrame()
        update_card.setStyleSheet(
            f"QFrame {{ background: {BG_CARD}; border: 1px solid {BORDER}; "
            f"border-radius: {RADIUS_LG}; padding: 24px; }}"
        )
        uc_layout = QVBoxLayout(update_card)
        uc_layout.setSpacing(10)

        uc_title = QLabel("UPDATES")
        uc_title.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 800; "
            f"letter-spacing: 2px; background: transparent;"
        )
        uc_layout.addWidget(uc_title)

        self._update_label = QLabel(f"Current version: {APP_VERSION}")
        self._update_label.setWordWrap(True)
        self._update_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 13px; background: transparent;"
        )
        uc_layout.addWidget(self._update_label)

        btn_row = QHBoxLayout()
        self._check_btn = QPushButton("  Check for Updates")
        self._check_btn.setProperty("class", "primary")
        self._check_btn.setCursor(Qt.PointingHandCursor)
        self._check_btn.clicked.connect(self._check_updates)
        btn_row.addWidget(self._check_btn)

        self._download_btn = QPushButton("  Download Update")
        self._download_btn.setProperty("class", "success")
        self._download_btn.setCursor(Qt.PointingHandCursor)
        self._download_btn.hide()
        btn_row.addWidget(self._download_btn)
        btn_row.addStretch()

        uc_layout.addLayout(btn_row)
        layout.addWidget(update_card)

        # ── License card ────────────────────────────
        lic_card = QFrame()
        lic_card.setStyleSheet(
            f"QFrame {{ background: {BG_CARD}; border: 1px solid {BORDER}; "
            f"border-radius: {RADIUS_LG}; padding: 24px; }}"
        )
        lic_layout = QVBoxLayout(lic_card)
        lic_layout.setSpacing(8)

        lic_title = QLabel("LICENSE")
        lic_title.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 800; "
            f"letter-spacing: 2px; background: transparent;"
        )
        lic_layout.addWidget(lic_title)

        lic_text = QLabel(
            "FFmpeg Studio is released under the MIT License.\n"
            "FFmpeg is a trademark of Fabrice Bellard and is licensed under LGPL/GPL.\n"
            "This application does not bundle FFmpeg — it must be installed separately."
        )
        lic_text.setWordWrap(True)
        lic_text.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        lic_layout.addWidget(lic_text)

        layout.addWidget(lic_card)

        # ── Tech stack ──────────────────────────────
        tech_card = QFrame()
        tech_card.setStyleSheet(
            f"QFrame {{ background: {BG_CARD}; border: 1px solid {BORDER}; "
            f"border-radius: {RADIUS_LG}; padding: 24px; }}"
        )
        tc_layout = QVBoxLayout(tech_card)
        tc_layout.setSpacing(8)

        tc_title = QLabel("BUILT WITH")
        tc_title.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 800; "
            f"letter-spacing: 2px; background: transparent;"
        )
        tc_layout.addWidget(tc_title)

        techs = "Python  •  PySide6 (Qt6)  •  FFmpeg  •  PyInstaller  •  Inno Setup"
        tc_text = QLabel(techs)
        tc_text.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        tc_layout.addWidget(tc_text)

        layout.addWidget(tech_card)

        layout.addStretch()
        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _check_updates(self):
        self._check_btn.setEnabled(False)
        self._check_btn.setText("  Checking…")
        self._update_label.setText("Connecting to GitHub…")
        self._update_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 13px; background: transparent;"
        )
        self._download_btn.hide()

        self._checker = _UpdateChecker()
        self._checker.result.connect(self._on_update_result)
        self._checker.start()

    def _on_update_result(self, version_or_error: str, url_or_msg: str):
        self._check_btn.setEnabled(True)
        self._check_btn.setText("  Check for Updates")

        if version_or_error == "error":
            self._update_label.setText(f"Could not check for updates: {url_or_msg}")
            self._update_label.setStyleSheet(
                f"color: {DANGER}; font-size: 13px; background: transparent;"
            )
            return

        latest = version_or_error
        if latest and latest != APP_VERSION and latest > APP_VERSION:
            self._update_label.setText(
                f"New version available: <b style='color:{ACCENT3}'>{latest}</b> "
                f"(current: {APP_VERSION})"
            )
            self._update_label.setStyleSheet(
                f"color: {TEXT_PRIMARY}; font-size: 13px; background: transparent;"
            )
            self._download_btn.show()
            # Disconnect old connections safely
            try:
                self._download_btn.clicked.disconnect()
            except RuntimeError:
                pass
            download_url = url_or_msg
            self._download_btn.clicked.connect(
                lambda: QDesktopServices.openUrl(download_url)
            )
        else:
            self._update_label.setText(
                f"You are up to date!  (v{APP_VERSION})"
            )
            self._update_label.setStyleSheet(
                f"color: {ACCENT3}; font-size: 13px; font-weight: 600; background: transparent;"
            )
