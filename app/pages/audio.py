"""Audio extraction / conversion page."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QScrollArea, QFrame,
)

from app.ffmpeg_backend import (
    AUDIO_CODECS, SAMPLE_RATES, AUDIO_CHANNELS,
    build_extract_audio_command, FFmpegWorker, probe_file,
)
from app.widgets.common import (
    FileDropZone, OutputSelector, ParamRow, ProcessRunner,
    SectionHeader, make_combo,
)
from app.styles import TEXT_SECONDARY


AUDIO_FORMATS = [
    ("MP3 (.mp3)", ".mp3"),
    ("AAC (.aac)", ".aac"),
    ("FLAC (.flac)", ".flac"),
    ("WAV (.wav)", ".wav"),
    ("OGG (.ogg)", ".ogg"),
    ("Opus (.opus)", ".opus"),
    ("M4A (.m4a)", ".m4a"),
    ("WMA (.wma)", ".wma"),
]


class AudioPage(QWidget):
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

        title = QLabel("Audio Extraction")
        title.setProperty("class", "heading")
        layout.addWidget(title)

        subtitle = QLabel("Extract and convert the audio track from any video or audio file.")
        subtitle.setProperty("class", "subheading")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)
        layout.addWidget(SectionHeader("Input"))
        self.drop = FileDropZone(file_filter="Media Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.ts *.wmv *.mpg *.mp3 *.aac *.flac *.wav *.ogg);;All Files (*)")
        self.drop.file_dropped.connect(self._on_file)
        layout.addWidget(self.drop)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        layout.addWidget(SectionHeader("Output Format"))

        self.fmt_combo = make_combo(AUDIO_FORMATS)
        self.fmt_combo.currentIndexChanged.connect(self._on_format_change)
        layout.addWidget(ParamRow("Format", self.fmt_combo))

        self.output = OutputSelector(".mp3")
        layout.addWidget(ParamRow("Output File", self.output))

        layout.addWidget(SectionHeader("Audio Settings"))

        self.acodec = make_combo(AUDIO_CODECS)
        layout.addWidget(ParamRow("Codec", self.acodec))

        self.abitrate = QLineEdit()
        self.abitrate.setPlaceholderText("e.g. 192k, 320k")
        layout.addWidget(ParamRow("Bitrate", self.abitrate))

        self.sample_rate = make_combo(SAMPLE_RATES)
        layout.addWidget(ParamRow("Sample Rate", self.sample_rate))

        self.channels = make_combo(AUDIO_CHANNELS)
        layout.addWidget(ParamRow("Channels", self.channels))

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
                f"Duration: {info.duration_str}  •  Audio: {info.audio_codec}  •  "
                f"Size: {info.size/(1024*1024):.1f} MB"
            )
        ext = self.fmt_combo.currentData()
        self.output.suggest_path(path, ext)

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

        args = build_extract_audio_command(
            input_path=inp,
            output_path=out,
            audio_codec=self.acodec.currentData(),
            bitrate=self.abitrate.text().strip(),
            sample_rate=self.sample_rate.currentData(),
            channels=self.channels.currentData(),
        )

        dur = self._media_info.duration if self._media_info else 0
        self._worker = FFmpegWorker(args, dur)
        self.runner.connect_worker(self._worker)
        self.runner.set_running(True)
        self._worker.start()
