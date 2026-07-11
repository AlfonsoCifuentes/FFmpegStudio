"""Convert page – format conversion with full codec/bitrate/resolution control."""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QScrollArea, QFrame, QCheckBox, QPushButton, QFileDialog,
)

from app.ffmpeg_backend import (
    AUDIO_ONLY_EXTENSIONS, build_folder_output_path, detect_subtitle_codec,
    get_primary_video_stream_index, is_text_subtitle_codec,
    VIDEO_CODECS, AUDIO_CODECS, OUTPUT_FORMATS, RESOLUTIONS,
    FRAME_RATES, SAMPLE_RATES, AUDIO_CHANNELS, ENCODING_PRESETS,
    build_convert_command, FFmpegWorker, BatchFFmpegWorker, probe_file,
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
        self._input_files = []

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
        self.drop = FileDropZone(accept_multiple=True, file_filter="Media Files (*.mp4 *.m4v *.mkv *.avi *.mov *.webm *.flv *.ts *.mts *.m2ts *.wmv *.mpg *.mpeg *.vob *.3gp *.mp3 *.aac *.flac *.wav *.ogg);;All Files (*)")
        self.drop.file_dropped.connect(self._on_file)
        self.drop.files_dropped.connect(self._on_files)
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
        self.output.set_directory_mode(True)
        self.output_row = ParamRow("Output Folder", self.output)
        layout.addWidget(self.output_row)

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

        # Subtitles
        layout.addWidget(SectionHeader("Subtitles"))

        self.burn_subtitles = QCheckBox("Burn subtitles into the video image")
        self.burn_subtitles.stateChanged.connect(self._on_subtitle_controls_change)
        layout.addWidget(self.burn_subtitles)

        self.subtitle_track = QComboBox()
        self.subtitle_track.currentIndexChanged.connect(self._on_subtitle_controls_change)
        layout.addWidget(ParamRow("Subtitle Track", self.subtitle_track))

        subtitle_file_widget = QWidget()
        subtitle_file_layout = QHBoxLayout(subtitle_file_widget)
        subtitle_file_layout.setContentsMargins(0, 0, 0, 0)
        subtitle_file_layout.setSpacing(8)
        self.subtitle_file = QLineEdit()
        self.subtitle_file.setPlaceholderText("External subtitle file (.srt, .ass, .ssa, .vtt, .sup, .sub, .idx)")
        subtitle_file_layout.addWidget(self.subtitle_file, 1)
        self.subtitle_browse = QPushButton("Browse...")
        self.subtitle_browse.clicked.connect(self._browse_subtitle_file)
        subtitle_file_layout.addWidget(self.subtitle_browse)
        self.subtitle_file_row = ParamRow("Subtitle File", subtitle_file_widget)
        layout.addWidget(self.subtitle_file_row)
        self._populate_subtitle_tracks(None)
        self._on_subtitle_controls_change()

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
            if info.subtitle_streams:
                parts.append(f"Subtitles: {len(info.subtitle_streams)}")
            self.info_label.setText("  •  ".join(parts))
        else:
            self.info_label.setText("Could not probe file (ffprobe not found or invalid file)")

        self._populate_subtitle_tracks(info)
        self.output.suggest_directory(path, subdirectory="FFmpeg Studio Output")

    def _on_files(self, paths):
        self._input_files = paths
        self._sync_output_mode()

    def _on_format_change(self):
        ext = self.fmt_combo.currentData()
        self.output.set_suffix(ext)
        self.output.suggest_directory(self.drop.filepath, subdirectory="FFmpeg Studio Output")
        self._on_subtitle_controls_change()

    def _sync_output_mode(self):
        self.output.set_directory_mode(True)
        self.output_row.set_label("Output Folder")
        if self._input_files:
            self.output.suggest_directory(
                self._input_files[0], subdirectory="FFmpeg Studio Output"
            )

    def _populate_subtitle_tracks(self, info):
        self.subtitle_track.blockSignals(True)
        self.subtitle_track.clear()
        self.subtitle_track.addItem("No subtitle track", None)

        if info:
            for subtitle_index, stream in enumerate(info.subtitle_streams):
                codec = str(stream.get("codec_name", "unknown")).lower()
                tags = stream.get("tags", {}) or {}
                lang = tags.get("language") or tags.get("LANGUAGE") or "und"
                title = tags.get("title") or tags.get("TITLE") or ""
                label = f"Embedded {subtitle_index + 1}: {codec} ({lang})"
                if title:
                    label += f" - {title}"
                label += " - text" if is_text_subtitle_codec(codec) else " - image-based"
                self.subtitle_track.addItem(
                    label,
                    {"type": "embedded", "index": subtitle_index, "codec": codec},
                )

        self.subtitle_track.addItem("External subtitle file", {"type": "external"})
        self.subtitle_track.blockSignals(False)

    def _on_subtitle_controls_change(self):
        enabled = self.burn_subtitles.isChecked()
        can_burn = self.fmt_combo.currentData() not in AUDIO_ONLY_EXTENSIONS
        if not can_burn and self.burn_subtitles.isChecked():
            self.burn_subtitles.blockSignals(True)
            self.burn_subtitles.setChecked(False)
            self.burn_subtitles.blockSignals(False)
        self.burn_subtitles.setEnabled(can_burn)
        if not can_burn:
            enabled = False
        self.subtitle_track.setEnabled(enabled)
        data = self.subtitle_track.currentData() if enabled else None
        uses_external = isinstance(data, dict) and data.get("type") == "external"
        self.subtitle_file_row.setVisible(enabled and uses_external)

    def _browse_subtitle_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Subtitle File",
            "",
            "Subtitle Files (*.srt *.ass *.ssa *.vtt *.sup *.sub *.idx);;All Files (*)",
        )
        if path:
            self.subtitle_file.setText(path)

    def _subtitle_selection(self, file_info=None):
        if not self.burn_subtitles.isChecked():
            return None

        if self.fmt_combo.currentData() in AUDIO_ONLY_EXTENSIONS:
            raise ValueError("Subtitle burn-in requires a video output format.")

        data = self.subtitle_track.currentData()
        if not isinstance(data, dict):
            raise ValueError("Select a subtitle track or external subtitle file to burn.")

        if data.get("type") == "external":
            subtitle_path = self.subtitle_file.text().strip()
            if not subtitle_path:
                raise ValueError("Select an external subtitle file to burn.")
            if not os.path.isfile(subtitle_path):
                raise ValueError("External subtitle file does not exist.")
            return {
                "subtitle_path": subtitle_path,
                "subtitle_stream_index": None,
                "subtitle_codec": detect_subtitle_codec(subtitle_path),
            }

        subtitle_index = int(data.get("index", 0))
        info = file_info or self._media_info
        if not info or len(info.subtitle_streams) <= subtitle_index:
            raise ValueError(f"Subtitle track {subtitle_index + 1} was not found in the input file.")

        stream = info.subtitle_streams[subtitle_index]
        codec = str(stream.get("codec_name", "")).lower()
        return {
            "subtitle_path": "",
            "subtitle_stream_index": subtitle_index,
            "subtitle_codec": codec,
        }

    def _build_args(self, inp, out, file_info=None):
        subtitle = self._subtitle_selection(file_info)
        video_stream_index = get_primary_video_stream_index(file_info)
        return build_convert_command(
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
            burn_subtitles=subtitle is not None,
            subtitle_path=subtitle["subtitle_path"] if subtitle else "",
            subtitle_stream_index=subtitle["subtitle_stream_index"] if subtitle else None,
            subtitle_codec=subtitle["subtitle_codec"] if subtitle else "subrip",
            video_stream_index=video_stream_index,
        )

    def _start(self):
        inp = self.drop.filepath
        if not inp:
            self.runner.set_error("No input file selected.")
            return

        fmt_ext = self.fmt_combo.currentData()
        input_files = self._input_files or [inp]

        out_dir = self.output.output_path
        if not out_dir:
            self.runner.set_error("No output folder specified.")
            return
        try:
            os.makedirs(out_dir, exist_ok=True)
        except OSError as e:
            self.runner.set_error(f"Could not create output folder: {e}")
            return

        tasks = []
        reserved_outputs = set()
        for f in input_files:
            info = probe_file(f)
            dur = info.duration if info else 0
            try:
                out = build_folder_output_path(f, out_dir, fmt_ext, reserved_outputs)
                args = self._build_args(f, out, info)
            except ValueError as e:
                self.runner.set_error(str(e))
                return
            reserved_outputs.add(os.path.normcase(os.path.abspath(out)))
            tasks.append((args, dur))

        if len(tasks) == 1:
            self._worker = FFmpegWorker(*tasks[0])
        else:
            self._worker = BatchFFmpegWorker(tasks)
        self.runner.connect_worker(self._worker)
        self.runner.set_running(True)
        self._worker.start()
