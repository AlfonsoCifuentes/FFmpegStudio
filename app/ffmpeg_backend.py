"""FFmpeg command builder and process executor."""

import json
import os
import re
import shlex
import subprocess
import shutil
import sys
from dataclasses import dataclass, field
from typing import Optional

from PySide6.QtCore import Signal, QThread


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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


def _config_dir() -> str:
    """Return the app config directory, creating it if needed."""
    d = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "FFmpegStudio")
    os.makedirs(d, exist_ok=True)
    return d


def _config_file() -> str:
    return os.path.join(_config_dir(), "config.json")


def _load_config() -> dict:
    try:
        with open(_config_file(), "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_config(cfg: dict):
    with open(_config_file(), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_custom_ffmpeg_dir() -> str:
    """Get user-configured FFmpeg directory."""
    return _load_config().get("ffmpeg_dir", "")


def set_custom_ffmpeg_dir(path: str):
    """Save user-configured FFmpeg directory."""
    cfg = _load_config()
    cfg["ffmpeg_dir"] = path
    _save_config(cfg)


def _common_ffmpeg_paths() -> list[str]:
    """Return common FFmpeg installation directories on Windows."""
    dirs = []
    for env_var in ("LOCALAPPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "USERPROFILE"):
        base = os.environ.get(env_var, "")
        if base:
            dirs.append(os.path.join(base, "ffmpeg", "bin"))
            dirs.append(os.path.join(base, "ffmpeg"))
    dirs.append(os.path.join("C:\\", "ffmpeg", "bin"))
    dirs.append(os.path.join("C:\\", "ffmpeg"))
    program_data = os.environ.get("PROGRAMDATA", "")
    if program_data:
        dirs.append(os.path.join(program_data, "chocolatey", "bin"))
    return dirs


def _is_executable_candidate(path: str) -> bool:
    if not path or not os.path.isfile(path):
        return False
    if os.name == "nt":
        return os.path.splitext(path)[1].lower() == ".exe"
    return os.access(path, os.X_OK)


def _tool_reports_expected_version(path: str, name: str) -> bool:
    """Return True only for real ffmpeg/ffprobe executables."""
    if not _is_executable_candidate(path):
        return False
    try:
        result = subprocess.run(
            [path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    output = result.stdout or ""
    return result.returncode == 0 and re.search(
        rf"\b{re.escape(name)}\s+version\b", output, re.IGNORECASE
    ) is not None


def _candidate_paths(name: str) -> list[str]:
    exe_name = f"{name}.exe" if os.name == "nt" else name
    candidates: list[str] = []

    custom = get_custom_ffmpeg_dir()
    if custom:
        if os.path.isfile(custom):
            candidates.append(custom)
        elif os.path.isdir(custom):
            candidates.append(os.path.join(custom, exe_name))
            candidates.append(os.path.join(custom, "bin", exe_name))

    path_names = [exe_name]
    if exe_name != name:
        path_names.append(name)
    for path_name in path_names:
        found = shutil.which(path_name)
        if found:
            candidates.append(found)

    if os.name == "nt":
        for d in _common_ffmpeg_paths():
            candidates.append(os.path.join(d, exe_name))

    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(os.path.dirname(sys.executable), exe_name))

    seen = set()
    unique = []
    for candidate in candidates:
        normalized = os.path.normcase(os.path.abspath(candidate))
        if normalized not in seen:
            seen.add(normalized)
            unique.append(candidate)
    return unique


def _find_executable(name: str) -> Optional[str]:
    """Find a valid executable, ignoring same-named scripts/wrappers."""
    for candidate in _candidate_paths(name):
        if _tool_reports_expected_version(candidate, name):
            return candidate
    return None


def find_ffmpeg() -> Optional[str]:
    """Find ffmpeg executable: custom path > PATH > common locations > app dir."""
    return _find_executable("ffmpeg")


def find_ffprobe() -> Optional[str]:
    """Find ffprobe executable: custom path > PATH > common locations > app dir."""
    return _find_executable("ffprobe")


def valid_ffmpeg_directory(path: str) -> Optional[str]:
    """Return the directory containing a valid ffmpeg executable under path, if any."""
    exe_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    for directory in (path, os.path.join(path, "bin")):
        candidate = os.path.join(directory, exe_name)
        if _tool_reports_expected_version(candidate, "ffmpeg"):
            return directory
    return None


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
            duration=_safe_float(fmt.get("duration", 0)),
            size=_safe_int(fmt.get("size", 0)),
            bit_rate=_safe_int(fmt.get("bit_rate", 0)),
            streams=data.get("streams", []),
        )
        return info
    except Exception:
        return None


# Output format groups used by conversion helpers
AUDIO_ONLY_EXTENSIONS = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav", ".wma"}
VIDEO_ONLY_EXTENSIONS = {".gif"}
TEXT_SUBTITLE_CODECS = {
    "ass", "ssa", "subrip", "text", "webvtt", "mov_text", "srt", "microdvd",
    "mpl2", "subviewer", "subviewer1", "vplayer", "realtext", "jacosub",
}


DEFAULT_VIDEO_CODEC_BY_EXTENSION = {
    ".avi": "mpeg4",
    ".flv": "libx264",
    ".mkv": "libx264",
    ".mov": "libx264",
    ".mp4": "libx264",
    ".ts": "libx264",
    ".webm": "libvpx-vp9",
    ".wmv": "mpeg4",
}


DEFAULT_AUDIO_CODEC_BY_EXTENSION = {
    ".aac": "aac",
    ".avi": "libmp3lame",
    ".flac": "flac",
    ".flv": "aac",
    ".m4a": "aac",
    ".mkv": "aac",
    ".mov": "aac",
    ".mp3": "libmp3lame",
    ".mp4": "aac",
    ".ogg": "libvorbis",
    ".opus": "libopus",
    ".ts": "aac",
    ".wav": "pcm_s16le",
    ".webm": "libopus",
    ".wma": "wmav2",
}


# Common video codecs
VIDEO_CODECS = [
    ("Auto (compatible)", ""),
    ("Stream copy", "copy"),
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
    ("Auto (compatible)", ""),
    ("Stream copy", "copy"),
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
            self.finished_error.emit("ffmpeg not found or invalid. Configure FFmpeg path in the sidebar.")
            return

        cmd = [ffmpeg, "-y", "-hide_banner"] + self.args
        self.log_output.emit(f"$ {' '.join(cmd)}\n")

        try:
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            proc = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
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


class BatchFFmpegWorker(QThread):
    """Runs ffmpeg for multiple files sequentially."""

    batch_progress = Signal(int, int)  # (current_1based, total)
    progress = Signal(float)           # 0.0 - 100.0 overall
    log_output = Signal(str)
    finished_ok = Signal(str)
    finished_error = Signal(str)

    def __init__(self, tasks: list[tuple[list, float]], parent=None):
        """tasks: list of (ffmpeg_args, duration) tuples."""
        super().__init__(parent)
        self.tasks = tasks
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            self.finished_error.emit("ffmpeg not found. Configure FFmpeg path in the sidebar.")
            return

        total = len(self.tasks)
        errors = []

        for i, (args, duration) in enumerate(self.tasks):
            if self._cancelled:
                self.finished_error.emit("Cancelled by user.")
                return

            self.batch_progress.emit(i + 1, total)
            self.log_output.emit(f"\n{'='*50}\n  File {i + 1} / {total}\n{'='*50}\n")

            cmd = [ffmpeg, "-y", "-hide_banner"] + args
            self.log_output.emit(f"$ {' '.join(cmd)}\n")

            try:
                creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                proc = subprocess.Popen(
                    cmd,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
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
                    if match and duration > 0:
                        h, m, s = float(match.group(1)), float(match.group(2)), float(match.group(3))
                        current = h * 3600 + m * 60 + s
                        file_pct = min(1.0, current / duration)
                        overall = ((i + file_pct) / total) * 100
                        self.progress.emit(overall)

                proc.wait()
                self.progress.emit(((i + 1) / total) * 100)
                if proc.returncode != 0:
                    errors.append(f"File {i + 1}: exit code {proc.returncode}")

            except Exception as e:
                errors.append(f"File {i + 1}: {str(e)}")

        if errors:
            self.progress.emit(100.0)
            self.finished_error.emit(f"Completed with {len(errors)} error(s): " + "; ".join(errors))
        else:
            self.progress.emit(100.0)
            self.finished_ok.emit(f"Batch complete: {total} file{'s' if total > 1 else ''} processed!")


def _extension(path_or_suffix: str) -> str:
    if not path_or_suffix:
        return ""
    suffix = path_or_suffix if path_or_suffix.startswith(".") else os.path.splitext(path_or_suffix)[1]
    return suffix.lower()


def _same_path(left: str, right: str) -> bool:
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(os.path.abspath(right))


def build_batch_output_path(input_path: str, output_dir: str, suffix: str) -> str:
    """Build a batch output path inside output_dir without overwriting the source."""
    ext = _extension(suffix) or os.path.splitext(input_path)[1]
    source = os.path.abspath(input_path)
    output = os.path.abspath(os.path.join(output_dir, f"{os.path.splitext(os.path.basename(input_path))[0]}{ext}"))

    if _same_path(source, output):
        stem = os.path.splitext(os.path.basename(input_path))[0]
        output = os.path.abspath(os.path.join(output_dir, f"{stem}_output{ext}"))

    return output


def ensure_output_parent(output_path: str):
    """Create the parent directory for an output file if it does not exist."""
    parent = os.path.dirname(os.path.abspath(output_path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def output_overwrites_input(input_path: str, output_path: str) -> bool:
    if not input_path or not output_path:
        return False
    return _same_path(input_path, output_path)


def split_command_args(extra_args: str) -> list[str]:
    """Split user-provided ffmpeg arguments while preserving Windows backslashes."""
    lexer = shlex.shlex(extra_args, posix=True)
    lexer.whitespace_split = True
    lexer.escape = ""
    return list(lexer)


def _escape_subtitles_filter_path(path: str) -> str:
    normalized = os.path.abspath(path).replace("\\", "/")
    return normalized.replace(":", r"\:").replace("'", r"\'")


def build_subtitles_filter(
    input_path: str,
    subtitle_path: str = "",
    subtitle_stream_index: int | None = None,
) -> str:
    """Build a subtitles filter for external files or embedded text subtitle streams."""
    source = subtitle_path or input_path
    filter_value = f"subtitles=filename='{_escape_subtitles_filter_path(source)}'"
    if subtitle_stream_index is not None:
        filter_value += f":si={int(subtitle_stream_index)}"
    return filter_value


def _auto_video_codec(output_ext: str) -> str:
    if output_ext in AUDIO_ONLY_EXTENSIONS or output_ext in VIDEO_ONLY_EXTENSIONS:
        return ""
    return DEFAULT_VIDEO_CODEC_BY_EXTENSION.get(output_ext, "")


def _auto_audio_codec(output_ext: str) -> str:
    if output_ext in VIDEO_ONLY_EXTENSIONS:
        return ""
    return DEFAULT_AUDIO_CODEC_BY_EXTENSION.get(output_ext, "")


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
    burn_subtitles: bool = False,
    subtitle_path: str = "",
    subtitle_stream_index: int | None = None,
) -> list[str]:
    """Build an ffmpeg conversion command from parameters."""
    output_ext = _extension(output_path)
    video_codec = video_codec or _auto_video_codec(output_ext)
    audio_codec = audio_codec or _auto_audio_codec(output_ext)
    has_video_output = output_ext not in AUDIO_ONLY_EXTENSIONS
    has_audio_output = output_ext not in VIDEO_ONLY_EXTENSIONS
    should_burn_subtitles = burn_subtitles and (bool(subtitle_path) or subtitle_stream_index is not None)

    if should_burn_subtitles and not has_video_output:
        raise ValueError("Subtitle burn-in requires a video output format.")

    if should_burn_subtitles and video_codec == "copy":
        video_codec = _auto_video_codec(output_ext) or "libx264"

    args = ["-i", input_path]
    args += ["-sn"]

    if not has_video_output:
        args += ["-vn"]
    elif video_codec:
        args += ["-c:v", video_codec]

    if should_burn_subtitles:
        args += ["-vf", build_subtitles_filter(input_path, subtitle_path, subtitle_stream_index)]

    if not has_audio_output:
        args += ["-an"]
    elif audio_codec:
        args += ["-c:a", audio_codec]

    if video_bitrate and has_video_output:
        args += ["-b:v", video_bitrate]
    if audio_bitrate and has_audio_output:
        args += ["-b:a", audio_bitrate]
    if resolution and has_video_output:
        args += ["-s", resolution]
    if frame_rate and has_video_output:
        args += ["-r", frame_rate]
    if sample_rate and has_audio_output:
        args += ["-ar", sample_rate]
    if channels and has_audio_output:
        args += ["-ac", channels]
    if preset and has_video_output:
        args += ["-preset", preset]
    if crf and has_video_output:
        args += ["-crf", crf]
    if extra_args:
        args += split_command_args(extra_args)

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
