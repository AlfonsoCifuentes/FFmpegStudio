"""Merge / Concatenate files page."""

import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QScrollArea,
    QFrame, QCheckBox, QComboBox,
)

from app.ffmpeg_backend import (
    build_merge_command, FFmpegWorker, OUTPUT_FORMATS, probe_file,
)
from app.widgets.common import (
    MultiFileDropZone, OutputSelector, ParamRow, ProcessRunner,
    SectionHeader, make_combo,
)
from app.styles import TEXT_SECONDARY


class MergePage(QWidget):
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

        title = QLabel("Merge / Concatenate")
        title.setProperty("class", "heading")
        layout.addWidget(title)

        subtitle = QLabel(
            "Combine multiple media files into one. Files must share the same codec and parameters for the concat demuxer."
        )
        subtitle.setProperty("class", "subheading")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)
        layout.addWidget(SectionHeader("Input Files"))

        self.drop = MultiFileDropZone(
            file_filter="Media Files (*.mp4 *.mkv *.avi *.mov *.webm *.ts *.mp3 *.flac *.wav *.ogg);;All Files (*)"
        )
        layout.addWidget(self.drop)

        self.info_label = QLabel("Drag files in the desired order. You can reorder them in the list.")
        self.info_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; background:transparent;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        layout.addWidget(SectionHeader("Output"))

        self.output_fmt = make_combo(OUTPUT_FORMATS)
        self.output_fmt.currentIndexChanged.connect(self._on_format_change)
        layout.addWidget(ParamRow("Format", self.output_fmt))

        self.output = OutputSelector(".mp4")
        layout.addWidget(ParamRow("Output File", self.output))

        self.reencode = QCheckBox("Re-encode (slower but works with mixed formats)")
        layout.addWidget(self.reencode)

        layout.addSpacing(8)
        self.runner = ProcessRunner()
        self.runner.run_requested.connect(self._start)
        layout.addWidget(self.runner)

        layout.addStretch()
        scroll.setWidget(container)

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(scroll)

    def _on_format_change(self):
        ext = self.output_fmt.currentData()
        self.output.set_suffix(ext)

    def _start(self):
        files = self.drop.filepaths
        out = self.output.output_path
        if len(files) < 2:
            self.runner.set_error("Please add at least 2 files.")
            return
        if not out:
            self.runner.set_error("No output path specified.")
            return

        args = build_merge_command(
            input_paths=files,
            output_path=out,
            reencode=self.reencode.isChecked(),
        )

        self._worker = FFmpegWorker(args, 0)
        self.runner.connect_worker(self._worker)
        self.runner.set_running(True)
        self._worker.start()
