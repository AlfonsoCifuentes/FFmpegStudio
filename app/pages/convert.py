"""Convert page – format conversion with full codec/bitrate/resolution control."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QScrollArea, QFrame,
)

from app.ffmpeg_backend import (
    VIDEO_CODECS, AUDIO_CODECS, OUTPUT_FORMATS, RESOLUTIONS,
    FRAME_RATES, SAMPLE_RATES, AUDIO_CHANNELS, ENCODING_PRESETS,
    build_convert_command, FFmpegWorker, probe_file,
)
from app.widgets.common import (
    FileDropZone, OutputSelector, ParamRow, ProcessRunner,
    SectionHeader, make_combo,
)
from app.styles import TEXT_SECONDARY, ACCENT


class ConvertPage(QWidget):
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

        # Header
        title = QLabel("Format Conversion")
        title.setProperty("class", "heading")
        layout.addWidget(title)

        subtitle = QLabel("Convert between any media format with full control over codecs, quality, and resolution.")
        subtitle.setProperty("class", "subheading")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Input
        layout.addSpacing(8)
        layout.addWidget(SectionHeader("Input"))
        self.drop = FileDropZone(file_filter="Media Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.ts *.wmv *.mpg *.mp3 *.aac *.flac *.wav *.ogg);;All Files (*)")
        self.drop.file_dropped.connect(self._on_file)
        layout.addWidget(self.drop)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; padding: 4px 0; background: transparent;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Output format
        layout.addWidget(SectionHeader("Output"))

        self.fmt_combo = make_combo(OUTPUT_FORMATS)
        self.fmt_combo.currentIndexChanged.connect(self._on_format_change)
        layout.addWidget(ParamRow("Format", self.fmt_combo))

        self.output = OutputSelector(".mp4")
        layout.addWidget(ParamRow("Output File", self.output))

        # Video settings
        layout.addWidget(SectionHeader("Video"))

        self.vcodec = make_combo(VIDEO_CODECS)
        layout.addWidget(ParamRow("Video Codec", self.vcodec))

        self.resolution = make_combo(RESOLUTIONS)
        layout.addWidget(ParamRow("Resolution", self.resolution))

        self.fps = make_combo(FRAME_RATES)
        layout.addWidget(ParamRow("Frame Rate", self.fps))

        self.vbitrate = QLineEdit()
        self.vbitrate.setPlaceholderText("e.g. 5000k, 8M (leave empty for auto)")
        layout.addWidget(ParamRow("Video Bitrate", self.vbitrate))

        self.crf = QLineEdit()
        self.crf.setPlaceholderText("e.g. 23 (lower = better quality, 0-51)")
        layout.addWidget(ParamRow("CRF (Quality)", self.crf))

        self.preset = make_combo(ENCODING_PRESETS)
        self.preset.setCurrentIndex(5)  # medium
        layout.addWidget(ParamRow("Encoding Speed", self.preset))

        # Audio settings
        layout.addWidget(SectionHeader("Audio"))

        self.acodec = make_combo(AUDIO_CODECS)
        layout.addWidget(ParamRow("Audio Codec", self.acodec))

        self.abitrate = QLineEdit()
        self.abitrate.setPlaceholderText("e.g. 192k, 320k (leave empty for auto)")
        layout.addWidget(ParamRow("Audio Bitrate", self.abitrate))

        self.sample_rate = make_combo(SAMPLE_RATES)
        layout.addWidget(ParamRow("Sample Rate", self.sample_rate))

        self.channels = make_combo(AUDIO_CHANNELS)
        layout.addWidget(ParamRow("Channels", self.channels))

        # Extra
        layout.addWidget(SectionHeader("Advanced"))
        self.extra = QLineEdit()
        self.extra.setPlaceholderText("Additional ffmpeg arguments (optional)")
        layout.addWidget(ParamRow("Extra Args", self.extra))

        # Runner
        layout.addSpacing(8)
        self.runner = ProcessRunner()
        self.runner.run_requested.connect(self._start)
        layout.addWidget(self.runner)

        layout.addStretch()
        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _on_file(self, path):
        info = probe_file(path)
        self._media_info = info
        if info:
            parts = [
                f"Format: {info.format_long_name}",
                f"Duration: {info.duration_str}",
                f"Resolution: {info.resolution}",
                f"Video: {info.video_codec}",
                f"Audio: {info.audio_codec}",
                f"Size: {info.size / (1024*1024):.1f} MB",
            ]
            self.info_label.setText("  •  ".join(parts))
        else:
            self.info_label.setText("Could not probe file (ffprobe not found or invalid file)")

        fmt_ext = self.fmt_combo.currentData()
        self.output.suggest_path(path, fmt_ext)

    def _on_format_change(self):
        ext = self.fmt_combo.currentData()
        self.output.set_suffix(ext)
        if self.drop.filepath:
            self.output.suggest_path(self.drop.filepath, ext)

    def _start(self):
        inp = self.drop.filepath
        out = self.output.output_path
        if not inp:
            self.runner.set_error("No input file selected.")
            return
        if not out:
            self.runner.set_error("No output path specified.")
            return

        args = build_convert_command(
            input_path=inp,
            output_path=out,
            video_codec=self.vcodec.currentData() if self.vcodec.currentData() != "copy" else "copy",
            audio_codec=self.acodec.currentData() if self.acodec.currentData() != "copy" else "copy",
            video_bitrate=self.vbitrate.text().strip(),
            audio_bitrate=self.abitrate.text().strip(),
            resolution=self.resolution.currentData(),
            frame_rate=self.fps.currentData(),
            sample_rate=self.sample_rate.currentData(),
            channels=self.channels.currentData(),
            preset=self.preset.currentData() if self.vcodec.currentData() in ("libx264", "libx265") else "",
            crf=self.crf.text().strip(),
            extra_args=self.extra.text().strip(),
        )

        dur = self._media_info.duration if self._media_info else 0
        self._worker = FFmpegWorker(args, dur)
        self.runner.connect_worker(self._worker)
        self.runner.set_running(True)
        self._worker.start()
