"""Resize / Scale page."""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QScrollArea,
    QFrame,
)

from app.ffmpeg_backend import (
    RESOLUTIONS, build_resize_command, FFmpegWorker, probe_file,
    OUTPUT_FORMATS, build_folder_output_path,
)
from app.widgets.common import (
    FileDropZone, OutputSelector, ParamRow, ProcessRunner,
    SectionHeader, make_combo,
)
from app.styles import TEXT_SECONDARY


SCALE_ALGORITHMS = [
    ("Auto (default)", ""),
    ("Bicubic", "bicubic"),
    ("Bilinear", "bilinear"),
    ("Lanczos", "lanczos"),
    ("Neighbor (pixelated)", "neighbor"),
    ("Spline", "spline"),
]


class ResizePage(QWidget):
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

        title = QLabel("Resize / Scale")
        title.setProperty("class", "heading")
        layout.addWidget(title)

        subtitle = QLabel("Change the resolution of your video. Choose a preset or enter a custom size.")
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

        layout.addWidget(SectionHeader("Resolution"))

        self.preset = make_combo(RESOLUTIONS)
        layout.addWidget(ParamRow("Preset", self.preset))

        self.custom_w = QLineEdit()
        self.custom_w.setPlaceholderText("Width  (e.g. 1280, or -1 for auto)")
        self.custom_h = QLineEdit()
        self.custom_h.setPlaceholderText("Height (e.g. 720, or -1 for auto)")
        layout.addWidget(ParamRow("Custom W", self.custom_w))
        layout.addWidget(ParamRow("Custom H", self.custom_h))

        self.algorithm = make_combo(SCALE_ALGORITHMS)
        layout.addWidget(ParamRow("Algorithm", self.algorithm))

        layout.addWidget(SectionHeader("Output"))

        self.output_fmt = make_combo(OUTPUT_FORMATS)
        self.output_fmt.currentIndexChanged.connect(self._on_format_change)
        layout.addWidget(ParamRow("Format", self.output_fmt))

        self.output = OutputSelector(".mp4")
        self.output.set_directory_mode(True)
        layout.addWidget(ParamRow("Output Folder", self.output))

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
                f"Duration: {info.duration_str}  •  Resolution: {info.resolution}  •  "
                f"Codec: {info.video_codec}"
            )
        self.output.suggest_directory(path, subdirectory="FFmpeg Studio Output")

    def _on_format_change(self):
        ext = self.output_fmt.currentData()
        self.output.set_suffix(ext)
        self.output.suggest_directory(self.drop.filepath, subdirectory="FFmpeg Studio Output")

    def _start(self):
        inp = self.drop.filepath
        if not inp:
            self.runner.set_error("No input file selected.")
            return
        out_dir = self.output.output_path
        if not out_dir:
            self.runner.set_error("No output folder specified.")
            return
        try:
            os.makedirs(out_dir, exist_ok=True)
            out = build_folder_output_path(inp, out_dir, self.output_fmt.currentData())
        except OSError as e:
            self.runner.set_error(f"Could not create output folder: {e}")
            return
        except ValueError as e:
            self.runner.set_error(str(e))
            return

        # Determine resolution
        preset_val = self.preset.currentData()
        cw = self.custom_w.text().strip()
        ch = self.custom_h.text().strip()

        if cw and ch:
            resolution = f"{cw}:{ch}"
        elif preset_val:
            resolution = preset_val
        else:
            self.runner.set_error("Select a resolution preset or enter custom width/height.")
            return

        algo = self.algorithm.currentData()

        args = build_resize_command(
            input_path=inp,
            output_path=out,
            resolution=resolution,
        )
        # Insert scaling algorithm if selected
        if algo:
            for i, a in enumerate(args):
                if a == "-vf":
                    # Correct ffmpeg syntax: scale=W:H:flags=algo
                    args[i + 1] = args[i + 1] + f":flags={algo}"
                    break

        dur = self._media_info.duration if self._media_info else 0
        self._worker = FFmpegWorker(args, dur)
        self.runner.connect_worker(self._worker)
        self.runner.set_running(True)
        self._worker.start()
