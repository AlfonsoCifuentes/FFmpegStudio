"""Trim/Cut page – extract segments from media files."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QScrollArea, QFrame,
)

from app.ffmpeg_backend import build_trim_command, FFmpegWorker, probe_file
from app.widgets.common import (
    FileDropZone, OutputSelector, ParamRow, ProcessRunner, SectionHeader,
)
from app.styles import TEXT_SECONDARY


class TrimPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._media_info = None

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Trim / Cut")
        title.setProperty("class", "heading")
        layout.addWidget(title)

        subtitle = QLabel("Extract a segment from your media file by specifying start and end times. Stream copy mode is ultra-fast with no quality loss.")
        subtitle.setProperty("class", "subheading")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Input
        layout.addSpacing(8)
        layout.addWidget(SectionHeader("Input"))
        self.drop = FileDropZone(file_filter="Media Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.ts *.wmv *.mpg);;All Files (*)")
        self.drop.file_dropped.connect(self._on_file)
        layout.addWidget(self.drop)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Timing
        layout.addWidget(SectionHeader("Time Range"))

        self.start_time = QLineEdit()
        self.start_time.setPlaceholderText("HH:MM:SS.mmm  (e.g. 00:01:30.000)")
        layout.addWidget(ParamRow("Start Time", self.start_time))

        self.end_time = QLineEdit()
        self.end_time.setPlaceholderText("HH:MM:SS.mmm  (e.g. 00:05:00.000)")
        layout.addWidget(ParamRow("End Time", self.end_time))

        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText("Alternative: duration in seconds (e.g. 30)")
        layout.addWidget(ParamRow("Duration (alt.)", self.duration_input))

        self.copy_check = QCheckBox("Stream copy (no re-encoding – fast, lossless)")
        self.copy_check.setChecked(True)
        layout.addWidget(self.copy_check)

        # Output
        layout.addWidget(SectionHeader("Output"))
        self.output = OutputSelector(".mp4")
        layout.addWidget(ParamRow("Output File", self.output))

        # Runner
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
                f"Duration: {info.duration_str}  •  {info.resolution}  •  "
                f"Video: {info.video_codec}  •  Audio: {info.audio_codec}"
            )
        self.output.suggest_path(path)

    def _start(self):
        inp = self.drop.filepath
        out = self.output.output_path
        if not inp:
            self.runner.set_error("No input file selected.")
            return
        if not out:
            self.runner.set_error("No output path specified.")
            return

        args = build_trim_command(
            input_path=inp,
            output_path=out,
            start_time=self.start_time.text().strip(),
            end_time=self.end_time.text().strip(),
            duration=self.duration_input.text().strip(),
            copy_codec=self.copy_check.isChecked(),
        )

        dur = self._media_info.duration if self._media_info else 0
        self._worker = FFmpegWorker(args, dur)
        self.runner.connect_worker(self._worker)
        self.runner.set_running(True)
        self._worker.start()
