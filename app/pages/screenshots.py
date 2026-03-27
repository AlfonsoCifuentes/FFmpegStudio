"""Screenshots / Frame Extraction page."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QScrollArea,
    QFrame, QComboBox, QSpinBox,
)

from app.ffmpeg_backend import (
    build_screenshot_command, FFmpegWorker, probe_file,
)
from app.widgets.common import (
    FileDropZone, OutputSelector, ParamRow, ProcessRunner,
    SectionHeader, make_combo,
)
from app.styles import TEXT_SECONDARY


IMAGE_FORMATS = [
    ("PNG (.png)", ".png"),
    ("JPEG (.jpg)", ".jpg"),
    ("BMP (.bmp)", ".bmp"),
    ("WebP (.webp)", ".webp"),
]

MODES = [
    ("Single frame at timestamp", "single"),
    ("Multiple frames (every N seconds)", "interval"),
    ("Extract all frames", "all"),
]


class ScreenshotsPage(QWidget):
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

        title = QLabel("Screenshots / Frame Extraction")
        title.setProperty("class", "heading")
        layout.addWidget(title)

        subtitle = QLabel("Extract frames from a video as image files.")
        subtitle.setProperty("class", "subheading")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)
        layout.addWidget(SectionHeader("Input"))
        self.drop = FileDropZone(
            file_filter="Video Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.ts *.wmv *.mpg);;All Files (*)"
        )
        self.drop.file_dropped.connect(self._on_file)
        layout.addWidget(self.drop)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; background:transparent;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        layout.addWidget(SectionHeader("Extraction Mode"))

        self.mode = make_combo(MODES)
        self.mode.currentIndexChanged.connect(self._on_mode)
        layout.addWidget(ParamRow("Mode", self.mode))

        self.timestamp = QLineEdit("00:00:01.000")
        self.timestamp.setPlaceholderText("HH:MM:SS.mmm")
        layout.addWidget(ParamRow("Timestamp", self.timestamp))

        self.interval = QSpinBox()
        self.interval.setRange(1, 3600)
        self.interval.setValue(5)
        self.interval.setSuffix(" sec")
        layout.addWidget(ParamRow("Interval", self.interval))

        layout.addWidget(SectionHeader("Output"))

        self.img_fmt = make_combo(IMAGE_FORMATS)
        self.img_fmt.currentIndexChanged.connect(self._on_img_format_change)
        layout.addWidget(ParamRow("Image Format", self.img_fmt))

        self.output = OutputSelector(".png")
        layout.addWidget(ParamRow("Output Path", self.output))

        self.note_label = QLabel(
            "For multiple frames, use a pattern like output_%04d.png – the number placeholder will be auto-added."
        )
        self.note_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; background:transparent;")
        self.note_label.setWordWrap(True)
        layout.addWidget(self.note_label)

        layout.addSpacing(8)
        self.runner = ProcessRunner()
        self.runner.run_requested.connect(self._start)
        layout.addWidget(self.runner)

        layout.addStretch()
        scroll.setWidget(container)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(scroll)

        self._on_mode()

    def _on_mode(self):
        mode = self.mode.currentData()
        self.timestamp.setVisible(mode == "single")
        self.interval.setVisible(mode == "interval")

    def _on_img_format_change(self):
        ext = self.img_fmt.currentData()
        self.output.set_suffix(ext)
        if self.drop.filepath:
            self.output.suggest_path(self.drop.filepath, ext)

    def _on_file(self, path):
        info = probe_file(path)
        self._media_info = info
        if info:
            self.info_label.setText(
                f"Duration: {info.duration_str}  •  Resolution: {info.resolution}  •  "
                f"Codec: {info.video_codec}"
            )
        ext = self.img_fmt.currentData()
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

        mode = self.mode.currentData()

        if mode == "single":
            ts = self.timestamp.text().strip() or "00:00:01.000"
            args = build_screenshot_command(inp, out, timestamp=ts)
        elif mode == "interval":
            # Ensure output has frame pattern
            import os
            base, ext = os.path.splitext(out)
            if "%0" not in out:
                out = f"{base}_%04d{ext}"
                self.output.line.setText(out)

            fps = 1.0 / self.interval.value()
            args = ["-i", inp, "-vf", f"fps={fps}", out]
        else:  # all frames
            import os
            base, ext = os.path.splitext(out)
            if "%0" not in out:
                out = f"{base}_%06d{ext}"
                self.output.line.setText(out)

            args = ["-i", inp, out]

        dur = self._media_info.duration if self._media_info else 0
        self._worker = FFmpegWorker(args, dur)
        self.runner.connect_worker(self._worker)
        self.runner.set_running(True)
        self._worker.start()
