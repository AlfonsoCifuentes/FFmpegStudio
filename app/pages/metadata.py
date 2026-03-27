"""Metadata viewer / editor page."""

import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton,
)

from app.ffmpeg_backend import find_ffprobe, FFmpegWorker, probe_file
from app.widgets.common import (
    FileDropZone, OutputSelector, ParamRow, ProcessRunner,
    SectionHeader,
)
from app.styles import TEXT_SECONDARY, ACCENT, BG_INPUT, TEXT_PRIMARY, BORDER


# Common metadata fields
METADATA_FIELDS = [
    ("title", "Title"),
    ("artist", "Artist"),
    ("album", "Album"),
    ("album_artist", "Album Artist"),
    ("date", "Date / Year"),
    ("track", "Track Number"),
    ("genre", "Genre"),
    ("composer", "Composer"),
    ("comment", "Comment"),
    ("description", "Description"),
    ("copyright", "Copyright"),
    ("encoder", "Encoder"),
]


class MetadataPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._media_info = None
        self._raw_tags = {}

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Metadata Editor")
        title.setProperty("class", "heading")
        layout.addWidget(title)

        subtitle = QLabel("View and edit metadata tags embedded in media files.")
        subtitle.setProperty("class", "subheading")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)
        layout.addWidget(SectionHeader("Input"))
        self.drop = FileDropZone(
            file_filter="Media Files (*.mp4 *.mkv *.avi *.mov *.mp3 *.flac *.ogg *.m4a *.wav);;All Files (*)"
        )
        self.drop.file_dropped.connect(self._on_file)
        layout.addWidget(self.drop)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; background:transparent;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # ── Current tags table ──────────────────────
        layout.addWidget(SectionHeader("Current Tags"))
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Tag", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setMinimumHeight(180)
        self.table.setMaximumHeight(300)
        layout.addWidget(self.table)

        # ── Editable fields ────────────────────────
        layout.addWidget(SectionHeader("Edit Tags"))
        self._edits = {}
        for key, label in METADATA_FIELDS:
            le = QLineEdit()
            le.setPlaceholderText(f"Enter {label}")
            self._edits[key] = le
            layout.addWidget(ParamRow(label, le))

        self.custom_tags = QLineEdit()
        self.custom_tags.setPlaceholderText("key1=value1;key2=value2  (additional custom tags)")
        layout.addWidget(ParamRow("Custom Tags", self.custom_tags))

        layout.addWidget(SectionHeader("Output"))
        self.output = OutputSelector(".mp4")
        layout.addWidget(ParamRow("Output File", self.output))

        layout.addSpacing(8)
        self.runner = ProcessRunner()
        self.runner.run_requested.connect(self._start)
        layout.addWidget(self.runner)

        layout.addStretch()
        scroll.setWidget(container)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(scroll)

    def _on_file(self, path):
        info = probe_file(path)
        self._media_info = info
        if info:
            self.info_label.setText(
                f"Duration: {info.duration_str}  •  Format: {info.format_name}  •  "
                f"Size: {info.size/(1024*1024):.1f} MB"
            )

        # Load existing tags via ffprobe JSON output
        import subprocess, os, sys
        ffprobe = find_ffprobe()
        try:
            result = subprocess.run(
                [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", path],
                capture_output=True, text=True, timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            data = json.loads(result.stdout)
            tags = data.get("format", {}).get("tags", {})
        except Exception:
            tags = {}

        self._raw_tags = tags

        # Fill table
        self.table.setRowCount(len(tags))
        for i, (k, v) in enumerate(tags.items()):
            self.table.setItem(i, 0, QTableWidgetItem(k))
            self.table.setItem(i, 1, QTableWidgetItem(str(v)))

        # Pre-fill edit fields
        for key, le in self._edits.items():
            val = tags.get(key, "") or tags.get(key.upper(), "")
            le.setText(str(val) if val else "")

        import os
        ext = os.path.splitext(path)[1]
        self.output.set_suffix(ext)
        self.output.suggest_path(path, ext)

    def _start(self):
        inp = self.drop.filepath
        out = self.output.output_path
        if not inp:
            self.runner.set_error("No input file selected.")
            return
        if not out:
            self.runner.set_error("No output path specified.")
            return

        args = ["-i", inp, "-c", "copy", "-map_metadata", "0"]

        # Add user-edited tags
        for key, le in self._edits.items():
            val = le.text().strip()
            if val:
                args += ["-metadata", f"{key}={val}"]

        # Parse custom tags
        custom = self.custom_tags.text().strip()
        if custom:
            for pair in custom.split(";"):
                pair = pair.strip()
                if "=" in pair:
                    args += ["-metadata", pair]

        args.append(out)

        self._worker = FFmpegWorker(args, 0)
        self.runner.connect_worker(self._worker)
        self.runner.set_running(True)
        self._worker.start()
