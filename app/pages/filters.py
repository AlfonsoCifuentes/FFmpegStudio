"""Filters & Effects page – video and audio filters with live preview of the command."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame, QCheckBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QGridLayout, QComboBox,
)

from app.ffmpeg_backend import (
    VIDEO_FILTERS, AUDIO_FILTERS, FFmpegWorker, probe_file,
    OUTPUT_FORMATS,
)
from app.widgets.common import (
    FileDropZone, OutputSelector, ParamRow, ProcessRunner,
    SectionHeader, make_combo, Card,
)
from app.styles import TEXT_SECONDARY, ACCENT, ACCENT2


class FilterCheckbox(QWidget):
    """A single filter toggle with a description."""

    def __init__(self, name, ffmpeg_value, description, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        self.cb = QCheckBox(name)
        self.cb.setToolTip(description)
        self._ffmpeg_value = ffmpeg_value
        layout.addWidget(self.cb)
        desc = QLabel(f"– {description}")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; background:transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc, 1)

    @property
    def is_checked(self):
        return self.cb.isChecked()

    @property
    def filter_value(self):
        return self._ffmpeg_value


class FiltersPage(QWidget):
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

        title = QLabel("Filters & Effects")
        title.setProperty("class", "heading")
        layout.addWidget(title)

        subtitle = QLabel(
            "Apply video and audio filters. Check the filters you want, configure custom values, and run."
        )
        subtitle.setProperty("class", "subheading")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)
        layout.addWidget(SectionHeader("Input"))
        self.drop = FileDropZone(
            file_filter="Media Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.ts *.wmv *.mpg);;All Files (*)"
        )
        self.drop.file_dropped.connect(self._on_file)
        layout.addWidget(self.drop)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; background:transparent;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # ── Video Filters ──────────────────────────
        layout.addWidget(SectionHeader("Video Filters"))
        self.video_checks = []
        for name, ffval in VIDEO_FILTERS.items():
            fc = FilterCheckbox(name, ffval, ffval)
            self.video_checks.append(fc)
            layout.addWidget(fc)

        self.custom_vf = QLineEdit()
        self.custom_vf.setPlaceholderText("Additional -vf value  (e.g.  eq=brightness=0.06:contrast=1.5)")
        layout.addWidget(ParamRow("Custom -vf", self.custom_vf))

        # ── Audio Filters ──────────────────────────
        layout.addWidget(SectionHeader("Audio Filters"))
        self.audio_checks = []
        for name, ffval in AUDIO_FILTERS.items():
            fc = FilterCheckbox(name, ffval, ffval)
            self.audio_checks.append(fc)
            layout.addWidget(fc)

        self.custom_af = QLineEdit()
        self.custom_af.setPlaceholderText("Additional -af value  (e.g.  equalizer=f=1000:t=q:w=1:g=2)")
        layout.addWidget(ParamRow("Custom -af", self.custom_af))

        # ── Output ─────────────────────────────────
        layout.addWidget(SectionHeader("Output"))

        self.output_fmt = make_combo(OUTPUT_FORMATS)
        self.output_fmt.currentIndexChanged.connect(self._on_format_change)
        layout.addWidget(ParamRow("Format", self.output_fmt))

        self.output = OutputSelector(".mp4")
        layout.addWidget(ParamRow("Output File", self.output))

        self.extra_args = QLineEdit()
        self.extra_args.setPlaceholderText("Extra ffmpeg arguments (optional)")
        layout.addWidget(ParamRow("Extra Args", self.extra_args))

        layout.addSpacing(8)
        self.runner = ProcessRunner()
        self.runner.run_requested.connect(self._start)
        layout.addWidget(self.runner)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    # ── helpers ─────────────────────────────────────

    def _on_file(self, path):
        info = probe_file(path)
        self._media_info = info
        if info:
            self.info_label.setText(
                f"Duration: {info.duration_str}  •  Video: {info.video_codec}  •  "
                f"Audio: {info.audio_codec}  •  Res: {info.resolution}"
            )
        ext = self.output_fmt.currentData()
        self.output.suggest_path(path, ext)

    def _on_format_change(self):
        ext = self.output_fmt.currentData()
        self.output.set_suffix(ext)
        if self.drop.filepath:
            self.output.suggest_path(self.drop.filepath, ext)

    def _build_vf(self):
        parts = [fc.filter_value for fc in self.video_checks if fc.is_checked]
        custom = self.custom_vf.text().strip()
        if custom:
            parts.append(custom)
        return ",".join(parts) if parts else ""

    def _build_af(self):
        parts = [fc.filter_value for fc in self.audio_checks if fc.is_checked]
        custom = self.custom_af.text().strip()
        if custom:
            parts.append(custom)
        return ",".join(parts) if parts else ""

    def _start(self):
        inp = self.drop.filepath
        out = self.output.output_path
        if not inp:
            self.runner.set_error("No input file selected.")
            return
        if not out:
            self.runner.set_error("No output path specified.")
            return

        args = ["-i", inp]

        vf = self._build_vf()
        af = self._build_af()
        if vf:
            args += ["-vf", vf]
        if af:
            args += ["-af", af]

        extra = self.extra_args.text().strip()
        if extra:
            args += extra.split()

        args.append(out)

        dur = self._media_info.duration if self._media_info else 0
        self._worker = FFmpegWorker(args, dur)
        self.runner.connect_worker(self._worker)
        self.runner.set_running(True)
        self._worker.start()
