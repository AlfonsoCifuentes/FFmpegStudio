"""Advanced / Custom Command page – direct ffmpeg command-line interface."""

import shlex
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QScrollArea, QFrame, QPushButton,
)

from app.ffmpeg_backend import FFmpegWorker
from app.widgets.common import ProcessRunner, SectionHeader, LogConsole
from app.styles import (
    TEXT_SECONDARY, ACCENT, BG_INPUT, TEXT_PRIMARY, BORDER,
    BG_DARK, TEXT_MUTED,
)


EXAMPLES = [
    ("Convert MP4 → WebM VP9", 'ffmpeg -i input.mp4 -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus output.webm'),
    ("GIF from video", 'ffmpeg -i input.mp4 -vf "fps=10,scale=480:-1:flags=lanczos" -loop 0 output.gif'),
    ("Picture-in-picture", 'ffmpeg -i main.mp4 -i overlay.mp4 -filter_complex "[1:v]scale=320:-1[pip];[0:v][pip]overlay=W-w-10:H-h-10" output.mp4'),
    ("Speed up 2x", 'ffmpeg -i input.mp4 -vf "setpts=0.5*PTS" -af "atempo=2.0" output.mp4'),
    ("Add subtitles", 'ffmpeg -i input.mp4 -vf "subtitles=subs.srt" output.mp4'),
    ("Extract subtitle track", 'ffmpeg -i input.mkv -map 0:s:0 output.srt'),
    ("Audio normalization", 'ffmpeg -i input.mp4 -af loudnorm=I=-16:TP=-1.5:LRA=11 output.mp4'),
    ("Two-pass encode", 'ffmpeg -i input.mp4 -c:v libx264 -b:v 2M -pass 1 -f null NUL && ffmpeg -i input.mp4 -c:v libx264 -b:v 2M -pass 2 output.mp4'),
]


class AdvancedPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Advanced / Custom Command")
        title.setProperty("class", "heading")
        layout.addWidget(title)

        subtitle = QLabel(
            "Run any ffmpeg command directly. Type or paste the full command below."
        )
        subtitle.setProperty("class", "subheading")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)
        layout.addWidget(SectionHeader("Command"))

        self.cmd_edit = QPlainTextEdit()
        self.cmd_edit.setPlaceholderText(
            "Enter full ffmpeg command...\n\n"
            "Example: ffmpeg -i input.mp4 -c:v libx265 -crf 28 output.mp4\n\n"
            "The 'ffmpeg' prefix is optional – it will be auto-resolved."
        )
        self.cmd_edit.setMinimumHeight(120)
        self.cmd_edit.setMaximumHeight(200)
        self.cmd_edit.setStyleSheet(
            f"QPlainTextEdit {{ background: {BG_INPUT}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: 8px; padding: 12px; "
            f"font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 13px; }}"
        )
        layout.addWidget(self.cmd_edit)

        # ── Example commands ───────────────────────
        layout.addWidget(SectionHeader("Quick Examples"))
        for label, cmd in EXAMPLES:
            row = QHBoxLayout()
            btn = QPushButton(label)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("example_cmd", cmd)
            btn.clicked.connect(self._insert_example)
            row.addWidget(btn)
            desc = QLabel(cmd[:80] + ("..." if len(cmd) > 80 else ""))
            desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; background:transparent;")
            desc.setWordWrap(True)
            row.addWidget(desc, 1)
            layout.addLayout(row)

        layout.addSpacing(8)
        self.runner = ProcessRunner()
        self.runner.run_requested.connect(self._start)
        layout.addWidget(self.runner)

        layout.addStretch()
        scroll.setWidget(container)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(scroll)

    def _insert_example(self):
        btn = self.sender()
        cmd = btn.property("example_cmd")
        if cmd:
            self.cmd_edit.setPlainText(cmd)

    def _start(self):
        raw = self.cmd_edit.toPlainText().strip()
        if not raw:
            self.runner.set_error("No command entered.")
            return

        # Parse the command
        try:
            parts = shlex.split(raw, posix=False)
        except ValueError as e:
            self.runner.set_error(f"Invalid command syntax: {e}")
            return

        # Replace leading 'ffmpeg' — the worker will prepend the real path
        if parts and parts[0].lower() in ("ffmpeg", "ffmpeg.exe"):
            parts.pop(0)

        # Remove -y if present — the worker appends it
        parts = [p for p in parts if p != "-y"]

        self._worker = FFmpegWorker(parts, 0)
        self.runner.connect_worker(self._worker)
        self.runner.set_running(True)
        self._worker.start()
