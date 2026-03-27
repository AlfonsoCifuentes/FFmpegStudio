"""FFmpeg command builder and process executor."""

import json
import os
import re
import subprocess
import shutil
from dataclasses import dataclass, field
from typing import Optional

from PySide6.QtCore import QObject, QProcess, Signal, QThread


@dataclass
class MediaInfo:
    """Parsed media file information."""
    filepath: str = ""
    format_name: str = ""
    format_long_name: str = ""
    duration: float = 0.0
    size: int = 0
    bit_rate: int = 0
    streams: list = field(default_factory=list)

    @property
    def video_streams(self):
        return [s for s in self.streams if s.get("codec_type") == "video"]

    @property
    def audio_streams(self):
        return [s for s in self.streams if s.get("codec_type") == "audio"]

    @property
    def subtitle_streams(self):
        return [s for s in self.streams if s.get("codec_type") == "subtitle"]

    @property
    def resolution(self):
        for s in self.video_streams:
            w = s.get("width", 0)
            h = s.get("height", 0)
            if w and h:
                return f"{w}x{h}"
        return "N/A"

    @property
    def video_codec(self):
        for s in self.video_streams:
            return s.get("codec_name", "N/A")
        return "N/A"

    @property
    def audio_codec(self):
        for s in self.audio_streams:
            return s.get("codec_name", "N/A")
        return "N/A"

    @property
    def duration_str(self):
        if self.duration <= 0:
            return "N/A"
        h = int(self.duration // 3600)
        m = int((self.duration % 3600) // 60)
        s = self.duration % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}"


def find_ffmpeg() -> Optional[str]:
    """Find ffmpeg executable in PATH."""
    return shutil.which("ffmpeg")


def find_ffprobe() -> Optional[str]:
    """Find ffprobe executable in PATH."""
    return shutil.which("ffprobe")


def probe_file(filepath: str) -> Optional[MediaInfo]:
    """Use ffprobe to get media file information."""
    ffprobe = find_ffprobe()
    if not ffprobe:
        return None
    try:
        result = subprocess.run(
            [
                ffprobe, "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                filepath,
            ],
            capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        fmt = data.get("format", {})
        info = MediaInfo(
            filepath=filepath,
            format_name=fmt.get("format_name", ""),
            format_long_name=fmt.get("format_long_name", ""),
            duration=float(fmt.get("duration", 0)),
            size=int(fmt.get("size", 0)),
            bit_rate=int(fmt.get("bit_rate", 0)),
            streams=data.get("streams", []),
        )
        return info
    except Exception:
        return None


# Common video codecs
VIDEO_CODECS = [
    ("Auto (copy)", "copy"),
    ("H.264 (libx264)", "libx264"),
    ("H.265/HEVC (libx265)", "libx265"),
    ("VP9 (libvpx-vp9)", "libvpx-vp9"),
    ("AV1 (libaom-av1)", "libaom-av1"),
    ("AV1 (libsvtav1)", "libsvtav1"),
    ("MPEG-4", "mpeg4"),
    ("ProRes (prores_ks)", "prores_ks"),
    ("DNxHD (dnxhd)", "dnxhd"),
    ("FFV1 (Lossless)", "ffv1"),
]

# Common audio codecs
AUDIO_CODECS = [
    ("Auto (copy)", "copy"),
    ("AAC", "aac"),
    ("MP3 (libmp3lame)", "libmp3lame"),
    ("Opus (libopus)", "libopus"),
    ("Vorbis (libvorbis)", "libvorbis"),
    ("FLAC", "flac"),
    ("WAV (pcm_s16le)", "pcm_s16le"),
    ("AC3", "ac3"),
    ("E-AC3", "eac3"),
    ("ALAC", "alac"),
]

# Common output formats
OUTPUT_FORMATS = [
    ("MP4 (.mp4)", ".mp4"),
    ("MKV (.mkv)", ".mkv"),
    ("WebM (.webm)", ".webm"),
    ("AVI (.avi)", ".avi"),
    ("MOV (.mov)", ".mov"),
    ("FLV (.flv)", ".flv"),
    ("TS (.ts)", ".ts"),
    ("MP3 (.mp3)", ".mp3"),
    ("AAC (.aac)", ".aac"),
    ("FLAC (.flac)", ".flac"),
    ("WAV (.wav)", ".wav"),
    ("OGG (.ogg)", ".ogg"),
    ("OPUS (.opus)", ".opus"),
    ("GIF (.gif)", ".gif"),
]

# Common resolutions
RESOLUTIONS = [
    ("Original", ""),
    ("3840x2160 (4K)", "3840x2160"),
    ("2560x1440 (2K)", "2560x1440"),
    ("1920x1080 (Full HD)", "1920x1080"),
    ("1280x720 (HD)", "1280x720"),
    ("854x480 (480p)", "854x480"),
    ("640x360 (360p)", "640x360"),
    ("426x240 (240p)", "426x240"),
]

# Common frame rates
FRAME_RATES = [
    ("Original", ""),
    ("60", "60"),
    ("30", "30"),
    ("29.97", "29.97"),
    ("25", "25"),
    ("24", "24"),
    ("23.976", "23.976"),
    ("15", "15"),
]

# Audio sample rates
SAMPLE_RATES = [
    ("Original", ""),
    ("48000 Hz", "48000"),
    ("44100 Hz", "44100"),
    ("22050 Hz", "22050"),
    ("16000 Hz", "16000"),
    ("8000 Hz", "8000"),
]

# Audio channels
AUDIO_CHANNELS = [
    ("Original", ""),
    ("Mono (1)", "1"),
    ("Stereo (2)", "2"),
    ("5.1 Surround (6)", "6"),
    ("7.1 Surround (8)", "8"),
]

# Video presets (for libx264/libx265)
ENCODING_PRESETS = [
    ("ultrafast", "ultrafast"),
    ("superfast", "superfast"),
    ("veryfast", "veryfast"),
    ("faster", "faster"),
    ("fast", "fast"),
    ("medium (default)", "medium"),
    ("slow", "slow"),
    ("slower", "slower"),
    ("veryslow", "veryslow"),
]

# Video filters
VIDEO_FILTERS = {
    "Deinterlace (yadif)": "yadif",
    "Denoise (hqdn3d)": "hqdn3d",
    "Sharpen (unsharp)": "unsharp=5:5:1.0:5:5:0.0",
    "Blur (boxblur)": "boxblur=2:1",
    "Mirror Horizontal": "hflip",
    "Mirror Vertical": "vflip",
    "Rotate 90° CW": "transpose=1",
    "Rotate 90° CCW": "transpose=2",
    "Rotate 180°": "transpose=1,transpose=1",
    "Grayscale": "colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3",
    "Sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131",
    "Vignette": "vignette",
    "Fade In (2s)": "fade=t=in:st=0:d=2",
    "Vintage": "curves=vintage",
    "Negate/Invert": "negate",
    "Edge Detection": "edgedetect",
    "Stabilize (vidstabdetect)": "vidstabdetect",
}

# Audio filters
AUDIO_FILTERS = {
    "Normalize Volume": "loudnorm",
    "Increase Volume (+10dB)": "volume=10dB",
    "Decrease Volume (-10dB)": "volume=-10dB",
    "Bass Boost": "bass=g=10",
    "Treble Boost": "treble=g=5",
    "Echo": "aecho=0.8:0.88:60:0.4",
    "Fade In (3s)": "afade=t=in:st=0:d=3",
    "Fade Out (3s)": "afade=t=out:st=0:d=3",
    "Tempo x1.5": "atempo=1.5",
    "Tempo x2.0": "atempo=2.0",
    "Tempo x0.5": "atempo=0.5",
    "High Pass (200Hz)": "highpass=f=200",
    "Low Pass (3000Hz)": "lowpass=f=3000",
    "Noise Reduction": "afftdn=nf=-25",
    "Stereo to Mono": "pan=mono|c0=0.5*c0+0.5*c1",
}


class FFmpegWorker(QThread):
    """Runs ffmpeg in a background thread, emitting progress signals."""

    progress = Signal(float)       # 0.0 - 100.0
    log_output = Signal(str)       # raw stderr line
    finished_ok = Signal(str)      # output path
    finished_error = Signal(str)   # error message

    def __init__(self, args: list[str], duration: float = 0.0, parent=None):
        super().__init__(parent)
        self.args = args
        self.duration = duration
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            self.finished_error.emit("ffmpeg not found in PATH. Please install ffmpeg.")
            return

        cmd = [ffmpeg, "-y", "-hide_banner"] + self.args
        self.log_output.emit(f"$ {' '.join(cmd)}\n")

        try:
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            proc = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                creationflags=creation_flags,
            )

            time_re = re.compile(r"time=(\d+):(\d+):(\d+\.?\d*)")
            for line in proc.stderr:
                if self._cancelled:
                    proc.kill()
                    proc.wait()
                    self.finished_error.emit("Cancelled by user.")
                    return
                self.log_output.emit(line)
                match = time_re.search(line)
                if match and self.duration > 0:
                    h, m, s = float(match.group(1)), float(match.group(2)), float(match.group(3))
                    current = h * 3600 + m * 60 + s
                    pct = min(100.0, (current / self.duration) * 100)
                    self.progress.emit(pct)

            proc.wait()
            if self._cancelled:
                self.finished_error.emit("Cancelled by user.")
            elif proc.returncode == 0:
                self.progress.emit(100.0)
                self.finished_ok.emit("Done!")
            else:
                self.finished_error.emit(f"ffmpeg exited with code {proc.returncode}")
        except Exception as e:
            self.finished_error.emit(str(e))


def build_convert_command(
    input_path: str,
    output_path: str,
    video_codec: str = "",
    audio_codec: str = "",
    video_bitrate: str = "",
    audio_bitrate: str = "",
    resolution: str = "",
    frame_rate: str = "",
    sample_rate: str = "",
    channels: str = "",
    preset: str = "",
    crf: str = "",
    extra_args: str = "",
) -> list[str]:
    """Build an ffmpeg conversion command from parameters."""
    args = ["-i", input_path]

    if video_codec:
        args += ["-c:v", video_codec]
    if audio_codec:
        args += ["-c:a", audio_codec]
    if video_bitrate:
        args += ["-b:v", video_bitrate]
    if audio_bitrate:
        args += ["-b:a", audio_bitrate]
    if resolution:
        args += ["-s", resolution]
    if frame_rate:
        args += ["-r", frame_rate]
    if sample_rate:
        args += ["-ar", sample_rate]
    if channels:
        args += ["-ac", channels]
    if preset:
        args += ["-preset", preset]
    if crf:
        args += ["-crf", crf]
    if extra_args:
        args += extra_args.split()

    args.append(output_path)
    return args


def build_trim_command(
    input_path: str,
    output_path: str,
    start_time: str = "",
    end_time: str = "",
    duration: str = "",
    copy_codec: bool = True,
) -> list[str]:
    """Build ffmpeg trim/cut command."""
    args = []
    if start_time:
        args += ["-ss", start_time]
    args += ["-i", input_path]
    if end_time:
        args += ["-to", end_time]
    elif duration:
        args += ["-t", duration]
    if copy_codec:
        args += ["-c", "copy"]
    args.append(output_path)
    return args


def build_extract_audio_command(
    input_path: str,
    output_path: str,
    audio_codec: str = "",
    bitrate: str = "",
    sample_rate: str = "",
    channels: str = "",
) -> list[str]:
    """Build ffmpeg extract audio command."""
    args = ["-i", input_path, "-vn"]
    if audio_codec and audio_codec != "copy":
        args += ["-c:a", audio_codec]
    elif audio_codec == "copy":
        args += ["-c:a", "copy"]
    if bitrate:
        args += ["-b:a", bitrate]
    if sample_rate:
        args += ["-ar", sample_rate]
    if channels:
        args += ["-ac", channels]
    args.append(output_path)
    return args


def build_merge_command(
    input_paths: list[str],
    output_path: str,
    reencode: bool = False,
) -> list[str]:
    """Build ffmpeg merge/concatenate command."""
    if not reencode:
        # concat demuxer – fast, stream copy
        import tempfile
        concat_file = os.path.join(tempfile.gettempdir(), "ffmpeg_concat.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            for p in input_paths:
                safe = p.replace("'", "'\\''") 
                f.write(f"file '{safe}'\n")
        return ["-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", output_path]
    else:
        # concat filter – re-encodes, works with mixed formats
        args = []
        for p in input_paths:
            args += ["-i", p]
        n = len(input_paths)
        filter_str = "".join(f"[{i}:v][{i}:a]" for i in range(n))
        filter_str += f"concat=n={n}:v=1:a=1[outv][outa]"
        args += ["-filter_complex", filter_str, "-map", "[outv]", "-map", "[outa]", output_path]
        return args


def build_resize_command(
    input_path: str,
    output_path: str,
    resolution: str = "",
    width: int = -1,
    height: int = -1,
    keep_aspect: bool = True,
) -> list[str]:
    """Build ffmpeg resize/scale command."""
    if resolution:
        # Accept "WxH" or "W:H" format
        parts = resolution.replace("x", ":").split(":")
        if len(parts) == 2:
            w, h = parts[0].strip(), parts[1].strip()
            scale = f"scale={w}:{h}"
        else:
            scale = f"scale={resolution}"
    elif keep_aspect:
        if width > 0 and height <= 0:
            scale = f"scale={width}:-2"
        elif height > 0 and width <= 0:
            scale = f"scale=-2:{height}"
        else:
            scale = f"scale={width}:{height}:force_original_aspect_ratio=decrease"
    else:
        scale = f"scale={width}:{height}"
    return ["-i", input_path, "-vf", scale, output_path]


def build_screenshot_command(
    input_path: str,
    output_path: str,
    timestamp: str = "00:00:01",
    count: int = 1,
) -> list[str]:
    """Extract frame(s) from video."""
    if count == 1:
        return ["-ss", timestamp, "-i", input_path, "-frames:v", "1", output_path]
    else:
        return ["-i", input_path, "-vf", f"fps=1/{max(1, count)}", output_path]
