"""Presets page – one-click encoding with predefined profiles."""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QTreeWidget, QTreeWidgetItem, QCheckBox, QPushButton,
    QFileDialog, QComboBox, QLineEdit,
)

from app.presets import PRESETS, PRESET_CATEGORIES
from app.ffmpeg_backend import (
    AUDIO_ONLY_EXTENSIONS, TEXT_SUBTITLE_CODECS,
    build_batch_output_path, build_preset_command, ensure_output_parent,
    get_primary_video_stream_index,
    output_overwrites_input,
    FFmpegWorker, BatchFFmpegWorker, probe_file,
)
from app.widgets.common import FileDropZone, OutputSelector, ProcessRunner, SectionHeader
from app.styles import (
    ACCENT, ACCENT2, ACCENT3, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    BG_CARD, BG_ELEVATED, BG_HOVER, BORDER, RADIUS_SM,
)


class PresetsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._media_info = None
        self._selected_preset = None
        self._input_files = []

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        title = QLabel("Encoding Presets")
        title.setProperty("class", "heading")
        layout.addWidget(title)

        subtitle = QLabel(
            "Select a preset for one-click encoding. "
            "Presets are optimized for specific devices, platforms, and use cases."
        )
        subtitle.setProperty("class", "subheading")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Input
        layout.addSpacing(4)
        layout.addWidget(SectionHeader("Input"))
        self.drop = FileDropZone(
            accept_multiple=True,
            file_filter="Media Files (*.mp4 *.m4v *.mkv *.avi *.mov *.webm *.flv *.ts *.mts *.m2ts *.wmv *.mpg *.mpeg *.vob *.3gp *.mp3 *.aac *.flac *.wav *.ogg);;All Files (*)"
        )
        self.drop.file_dropped.connect(self._on_file)
        self.drop.files_dropped.connect(self._on_files)
        layout.addWidget(self.drop)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12px; padding: 4px 0; background: transparent;"
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Preset selector
        layout.addWidget(SectionHeader("Select Preset"))

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setAnimated(True)
        self.tree.setMinimumHeight(280)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_SM};
                padding: 4px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 6px 8px;
                border-radius: {RADIUS_SM};
                color: {TEXT_PRIMARY};
            }}
            QTreeWidget::item:selected {{
                background-color: {ACCENT};
                color: #FFFFFF;
            }}
            QTreeWidget::item:hover:!selected {{
                background-color: {BG_HOVER};
            }}
            QTreeWidget::branch {{
                background: transparent;
            }}
        """)
        self.tree.currentItemChanged.connect(self._on_preset_selected)
        self._populate_tree()
        layout.addWidget(self.tree)

        # Preset details
        self.detail_label = QLabel("Select a preset to see its details.")
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12px; padding: 10px; "
            f"background: {BG_ELEVATED}; border: 1px solid {BORDER}; "
            f"border-radius: {RADIUS_SM};"
        )
        layout.addWidget(self.detail_label)

        # Output
        layout.addWidget(SectionHeader("Output"))
        self.output = OutputSelector(".mp4")
        from app.widgets.common import ParamRow
        self.output_row = ParamRow("Output File", self.output)
        layout.addWidget(self.output_row)

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
        self.subtitle_file.setPlaceholderText("External subtitle file (.srt, .ass, .ssa, .vtt)")
        subtitle_file_layout.addWidget(self.subtitle_file, 1)
        self.subtitle_browse = QPushButton("Browse...")
        self.subtitle_browse.clicked.connect(self._browse_subtitle_file)
        subtitle_file_layout.addWidget(self.subtitle_browse)
        self.subtitle_file_row = ParamRow("Subtitle File", subtitle_file_widget)
        layout.addWidget(self.subtitle_file_row)
        self._populate_subtitle_tracks(None)
        self._on_subtitle_controls_change()

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

    def _populate_tree(self):
        preset_by_cat = {}
        for p in PRESETS:
            preset_by_cat.setdefault(p.category, []).append(p)

        for cat in PRESET_CATEGORIES:
            presets = preset_by_cat.get(cat, [])
            if not presets:
                continue
            cat_item = QTreeWidgetItem([f"  {cat}  ({len(presets)})"])
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsSelectable)
            font = cat_item.font(0)
            font.setBold(True)
            cat_item.setFont(0, font)
            self.tree.addTopLevelItem(cat_item)
            for p in presets:
                child = QTreeWidgetItem([p.name])
                child.setData(0, Qt.UserRole, p)
                cat_item.addChild(child)
            cat_item.setExpanded(True)

    def _on_preset_selected(self, current, _previous):
        if current is None:
            return
        preset = current.data(0, Qt.UserRole)
        if preset is None:
            self.detail_label.setText("Select a preset to see its details.")
            self._selected_preset = None
            return
        self._selected_preset = preset
        args_str = " ".join(preset.ffmpeg_args)
        self.detail_label.setText(
            f"<b style='color:{ACCENT}'>{preset.name}</b><br>"
            f"<span style='color:{TEXT_SECONDARY}'>{preset.description}</span><br><br>"
            f"<span style='color:{TEXT_MUTED}; font-family:Consolas,monospace; font-size:11px'>"
            f"ffmpeg -i input {args_str} output{preset.extension}</span>"
        )
        self.output.set_suffix(preset.extension)
        if self.output.is_directory_mode():
            self.output.suggest_directory(self.drop.filepath)
        elif self.drop.filepath:
            self.output.suggest_path(self.drop.filepath, preset.extension)
        self._on_subtitle_controls_change()

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
        if self._selected_preset:
            self.output.suggest_path(path, self._selected_preset.extension)
        else:
            self.output.suggest_path(path)

    def _on_files(self, paths):
        self._input_files = paths
        self._sync_output_mode()

    def _sync_output_mode(self):
        is_batch = len(self._input_files) > 1
        self.output.set_directory_mode(is_batch)
        self.output_row.set_label("Output Folder" if is_batch else "Output File")
        if is_batch:
            self.output.suggest_directory(self._input_files[0], force=True)
        elif self.drop.filepath:
            suffix = self._selected_preset.extension if self._selected_preset else ".mp4"
            self.output.suggest_path(self.drop.filepath, suffix)

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
                if codec not in TEXT_SUBTITLE_CODECS:
                    label += " - not text-based"
                self.subtitle_track.addItem(
                    label,
                    {"type": "embedded", "index": subtitle_index, "codec": codec},
                )

        self.subtitle_track.addItem("External subtitle file", {"type": "external"})
        self.subtitle_track.blockSignals(False)

    def _on_subtitle_controls_change(self):
        enabled = self.burn_subtitles.isChecked()
        preset_ext = self._selected_preset.extension if self._selected_preset else ".mp4"
        can_burn = preset_ext not in AUDIO_ONLY_EXTENSIONS
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
            "Subtitle Files (*.srt *.ass *.ssa *.vtt);;All Files (*)",
        )
        if path:
            self.subtitle_file.setText(path)

    def _subtitle_selection(self, file_info=None):
        if not self.burn_subtitles.isChecked():
            return None

        if not self._selected_preset or self._selected_preset.extension in AUDIO_ONLY_EXTENSIONS:
            raise ValueError("Subtitle burn-in requires a video preset.")

        data = self.subtitle_track.currentData()
        if not isinstance(data, dict):
            raise ValueError("Select a subtitle track or external subtitle file to burn.")

        if data.get("type") == "external":
            subtitle_path = self.subtitle_file.text().strip()
            if not subtitle_path:
                raise ValueError("Select an external subtitle file to burn.")
            if not os.path.isfile(subtitle_path):
                raise ValueError("External subtitle file does not exist.")
            return {"subtitle_path": subtitle_path, "subtitle_stream_index": None}

        subtitle_index = int(data.get("index", 0))
        info = file_info or self._media_info
        if not info or len(info.subtitle_streams) <= subtitle_index:
            raise ValueError(f"Subtitle track {subtitle_index + 1} was not found in the input file.")

        stream = info.subtitle_streams[subtitle_index]
        codec = str(stream.get("codec_name", "")).lower()
        if codec not in TEXT_SUBTITLE_CODECS:
            raise ValueError(
                f"Subtitle track {subtitle_index + 1} uses '{codec}', which cannot be burned with the text subtitle renderer."
            )

        return {"subtitle_path": "", "subtitle_stream_index": subtitle_index}

    def _build_args(self, inp, out, file_info=None):
        video_stream_index = get_primary_video_stream_index(file_info)
        if (
            file_info
            and self._selected_preset.extension not in AUDIO_ONLY_EXTENSIONS
            and video_stream_index is None
        ):
            raise ValueError(f"{os.path.basename(inp)} does not contain a video stream for this preset.")

        subtitle = self._subtitle_selection(file_info)
        return build_preset_command(
            input_path=inp,
            output_path=out,
            preset_args=list(self._selected_preset.ffmpeg_args),
            burn_subtitles=subtitle is not None,
            subtitle_path=subtitle["subtitle_path"] if subtitle else "",
            subtitle_stream_index=subtitle["subtitle_stream_index"] if subtitle else None,
            video_stream_index=video_stream_index,
        )

    def _start(self):
        inp = self.drop.filepath
        if not inp:
            self.runner.set_error("No input file selected.")
            return
        if not self._selected_preset:
            self.runner.set_error("No preset selected.")
            return

        input_files = self._input_files or [inp]

        if len(input_files) > 1:
            # Batch mode
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
                out = build_batch_output_path(
                    f, out_dir, self._selected_preset.extension, reserved_outputs
                )
                try:
                    args = self._build_args(f, out, info)
                except ValueError as e:
                    self.runner.set_error(str(e))
                    return
                reserved_outputs.add(os.path.normcase(os.path.abspath(out)))
                tasks.append((args, dur))
            self._worker = BatchFFmpegWorker(tasks)
            self.runner.connect_worker(self._worker)
            self.runner.set_running(True)
            self._worker.start()
        else:
            # Single file mode
            out = self.output.output_path
            if not out:
                self.runner.set_error("No output path specified.")
                return
            if output_overwrites_input(inp, out):
                self.runner.set_error("Output path must be different from the input file.")
                return
            try:
                ensure_output_parent(out)
            except OSError as e:
                self.runner.set_error(f"Could not create output folder: {e}")
                return
            try:
                args = self._build_args(inp, out, self._media_info)
            except ValueError as e:
                self.runner.set_error(str(e))
                return
            dur = self._media_info.duration if self._media_info else 0
            self._worker = FFmpegWorker(args, dur)
            self.runner.connect_worker(self._worker)
            self.runner.set_running(True)
            self._worker.start()
