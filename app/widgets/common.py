"""Reusable UI widgets for FFmpeg Studio."""

import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QColor, QFont, QPen
from PySide6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QProgressBar, QPlainTextEdit, QWidget,
    QComboBox, QLineEdit, QSizePolicy, QGraphicsDropShadowEffect,
)

from app.styles import (
    ACCENT, ACCENT2, ACCENT3, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    BG_CARD, BG_INPUT, BORDER, DROP_ZONE_STYLE, LOG_STYLE, CARD_STYLE,
    DANGER, WARN,
)


# ── File Drop Zone ───────────────────────────────────────────────
class FileDropZone(QFrame):
    """Drag-and-drop area for selecting input files."""

    file_dropped = Signal(str)

    def __init__(self, accept_multiple=False, file_filter="All Files (*)", parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setStyleSheet(DROP_ZONE_STYLE)
        self.setAcceptDrops(True)
        self._accept_multiple = accept_multiple
        self._file_filter = file_filter
        self._filepath = ""

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        self._icon_label = QLabel("📂")
        self._icon_label.setAlignment(Qt.AlignCenter)
        self._icon_label.setStyleSheet("font-size: 36px; background: transparent;")
        layout.addWidget(self._icon_label)

        self._text_label = QLabel("Drag & drop a file here")
        self._text_label.setAlignment(Qt.AlignCenter)
        self._text_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; font-weight: 600; background: transparent;")
        layout.addWidget(self._text_label)

        self._sub_label = QLabel("or click to browse")
        self._sub_label.setAlignment(Qt.AlignCenter)
        self._sub_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
        layout.addWidget(self._sub_label)

        self._file_label = QLabel("")
        self._file_label.setAlignment(Qt.AlignCenter)
        self._file_label.setStyleSheet(f"color: {ACCENT}; font-size: 12px; font-weight: 600; background: transparent;")
        self._file_label.setWordWrap(True)
        self._file_label.hide()
        layout.addWidget(self._file_label)

        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(140)

    @property
    def filepath(self):
        return self._filepath

    def set_file(self, path: str):
        self._filepath = path
        name = os.path.basename(path)
        self._file_label.setText(f"✅  {name}")
        self._file_label.show()
        self._text_label.setText("File selected")
        self._sub_label.setText("Click or drop to change")
        self.file_dropped.emit(path)

    def mousePressEvent(self, event):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", self._file_filter)
        if path:
            self.set_file(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(DROP_ZONE_STYLE.replace("dashed", "solid").replace(BORDER, ACCENT))

    def dragLeaveEvent(self, event):
        self.setStyleSheet(DROP_ZONE_STYLE)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(DROP_ZONE_STYLE)
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if os.path.isfile(path):
                self.set_file(path)


class MultiFileDropZone(QFrame):
    """Drag-and-drop area for multiple files."""

    files_changed = Signal(list)

    def __init__(self, file_filter="All Files (*)", parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setStyleSheet(DROP_ZONE_STYLE)
        self.setAcceptDrops(True)
        self._files: list[str] = []
        self._file_filter = file_filter

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        icon = QLabel("📁")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 36px; background: transparent;")
        layout.addWidget(icon)

        self._text = QLabel("Drag & drop multiple files here")
        self._text.setAlignment(Qt.AlignCenter)
        self._text.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; font-weight: 600; background: transparent;")
        layout.addWidget(self._text)

        self._count = QLabel("or click to browse")
        self._count.setAlignment(Qt.AlignCenter)
        self._count.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
        layout.addWidget(self._count)

        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(120)

    @property
    def files(self):
        return self._files

    @property
    def filepaths(self):
        return self._files

    def mousePressEvent(self, event):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", self._file_filter)
        if paths:
            self._files = paths
            self._update_label()
            self.files_changed.emit(self._files)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        self._files = [u.toLocalFile() for u in urls if os.path.isfile(u.toLocalFile())]
        self._update_label()
        self.files_changed.emit(self._files)

    def _update_label(self):
        n = len(self._files)
        self._text.setText(f"{n} file{'s' if n != 1 else ''} selected")
        names = ", ".join(os.path.basename(f) for f in self._files[:3])
        if n > 3:
            names += f" + {n - 3} more"
        self._count.setText(names)
        self._count.setStyleSheet(f"color: {ACCENT}; font-size: 12px; font-weight: 600; background: transparent;")


# ── Card Frame ───────────────────────────────────────────────────
class Card(QFrame):
    """A styled card container."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(CARD_STYLE)


# ── Output selector ──────────────────────────────────────────────
class OutputSelector(QWidget):
    """Widget for selecting output file path."""

    def __init__(self, default_suffix=".mp4", parent=None):
        super().__init__(parent)
        self._suffix = default_suffix
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Output file path...")
        layout.addWidget(self.path_edit, 1)

        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.clicked.connect(self._browse)
        layout.addWidget(self.browse_btn)

        # Alias for compatible access
        self.line = self.path_edit

    def _browse(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Output", "", f"Media Files (*{self._suffix});;All Files (*)"
        )
        if path:
            self.path_edit.setText(path)

    @property
    def output_path(self) -> str:
        return self.path_edit.text().strip()

    def suggest_path(self, input_path: str, suffix: str = ""):
        """Auto-generate output path from input path."""
        if not input_path:
            return
        p = Path(input_path)
        ext = suffix or self._suffix
        out = p.parent / f"{p.stem}_output{ext}"
        self.path_edit.setText(str(out))

    def set_suffix(self, suffix: str):
        self._suffix = suffix


# ── Param Row ────────────────────────────────────────────────────
class ParamRow(QWidget):
    """A label + widget row used within forms."""

    def __init__(self, label_text: str, widget: QWidget, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        label = QLabel(label_text)
        label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 600; min-width: 130px; background: transparent;")
        label.setFixedWidth(140)
        layout.addWidget(label)
        layout.addWidget(widget, 1)


# ── Log Console ──────────────────────────────────────────────────
class LogConsole(QPlainTextEdit):
    """Read-only log console showing ffmpeg output."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logPanel")
        self.setStyleSheet(LOG_STYLE)
        self.setReadOnly(True)
        self.setMaximumHeight(180)
        self.setPlaceholderText("Command output will appear here…")

    def append_line(self, text: str):
        self.appendPlainText(text.rstrip())
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())


# ── Process Runner Widget ────────────────────────────────────────
class ProcessRunner(QWidget):
    """Progress bar + Run/Cancel buttons + log console."""

    run_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancel_connection = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Progress row
        prog_row = QHBoxLayout()
        prog_row.setSpacing(12)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        prog_row.addWidget(self.progress, 1)

        self.pct_label = QLabel("0%")
        self.pct_label.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: 700; font-size: 12px; min-width: 40px; background: transparent;")
        prog_row.addWidget(self.pct_label)

        layout.addLayout(prog_row)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self.run_btn = QPushButton("▶  Start Processing")
        self.run_btn.setProperty("class", "primary")
        self.run_btn.setCursor(Qt.PointingHandCursor)
        self.run_btn.setMinimumWidth(200)
        self.run_btn.clicked.connect(self.run_requested.emit)
        btn_row.addWidget(self.run_btn)

        self.cancel_btn = QPushButton("✕  Cancel")
        self.cancel_btn.setProperty("class", "danger")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.hide()
        btn_row.addWidget(self.cancel_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"font-size: 12px; font-weight: 600; background: transparent;")
        layout.addWidget(self.status_label)

        # Log
        self.log = LogConsole()
        layout.addWidget(self.log)

    def set_progress(self, pct: float):
        self.progress.setValue(int(pct))
        self.pct_label.setText(f"{pct:.0f}%")

    def set_running(self, running: bool):
        self.run_btn.setVisible(not running)
        self.cancel_btn.setVisible(running)
        self.run_btn.setEnabled(not running)
        if running:
            self.status_label.setText("")
            self.status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 600; background: transparent;")
            self.set_progress(0)
            self.log.clear()

    def set_success(self, msg: str = "Processing complete!"):
        self.set_running(False)
        self.set_progress(100)
        self.status_label.setText(f"✅  {msg}")
        self.status_label.setStyleSheet(f"color: {ACCENT3}; font-size: 13px; font-weight: 700; background: transparent;")

    def set_error(self, msg: str):
        self.set_running(False)
        self.status_label.setText(f"❌  {msg}")
        self.status_label.setStyleSheet(f"color: {DANGER}; font-size: 13px; font-weight: 700; background: transparent;")

    def connect_worker(self, worker):
        """Connect a FFmpegWorker to this runner, handling signal cleanup."""
        # Disconnect previous cancel connection if any
        if self._cancel_connection is not None:
            try:
                self.cancel_btn.clicked.disconnect(self._cancel_connection)
            except RuntimeError:
                pass
        self._cancel_connection = worker.cancel
        worker.progress.connect(self.set_progress)
        worker.log_output.connect(self.log.append_line)
        worker.finished_ok.connect(lambda m: self.set_success(m))
        worker.finished_error.connect(lambda m: self.set_error(m))
        self.cancel_btn.clicked.connect(self._cancel_connection)


# ── Labelled combo with helper ───────────────────────────────────
def make_combo(items: list[tuple[str, str]], parent=None) -> QComboBox:
    """Create a QComboBox from a list of (display, value) pairs."""
    combo = QComboBox(parent)
    for display, value in items:
        combo.addItem(display, value)
    return combo


# ── Section Header ───────────────────────────────────────────────
class SectionHeader(QLabel):
    """Small uppercase section divider label."""

    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setProperty("class", "section")
        self.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 800; "
            f"letter-spacing: 2px; padding: 8px 0 4px 0; background: transparent;"
        )
