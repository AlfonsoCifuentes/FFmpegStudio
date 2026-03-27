"""Presets page – one-click encoding with predefined profiles."""

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QTreeWidget, QTreeWidgetItem, QSizePolicy,
)

from app.presets import PRESETS, PRESET_CATEGORIES
from app.ffmpeg_backend import FFmpegWorker, BatchFFmpegWorker, probe_file
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
            file_filter="Media Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.ts *.wmv *.mpg *.mp3 *.aac *.flac *.wav *.ogg);;All Files (*)"
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
        layout.addWidget(ParamRow("Output File", self.output))

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
        if self.drop.filepath:
            self.output.suggest_path(self.drop.filepath, preset.extension)

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

        if self._selected_preset:
            self.output.suggest_path(path, self._selected_preset.extension)
        else:
            self.output.suggest_path(path)

    def _on_files(self, paths):
        self._input_files = paths

    def _start(self):
        inp = self.drop.filepath
        if not inp:
            self.runner.set_error("No input file selected.")
            return
        if not self._selected_preset:
            self.runner.set_error("No preset selected.")
            return

        if len(self._input_files) > 1:
            # Batch mode
            tasks = []
            for f in self._input_files:
                info = probe_file(f)
                dur = info.duration if info else 0
                stem = os.path.splitext(f)[0]
                out = f"{stem}_output{self._selected_preset.extension}"
                args = ["-i", f] + list(self._selected_preset.ffmpeg_args) + [out]
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
            args = ["-i", inp] + list(self._selected_preset.ffmpeg_args) + [out]
            dur = self._media_info.duration if self._media_info else 0
            self._worker = FFmpegWorker(args, dur)
            self.runner.connect_worker(self._worker)
            self.runner.set_running(True)
            self._worker.start()
