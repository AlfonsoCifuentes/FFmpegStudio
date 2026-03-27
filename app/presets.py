"""FFmpeg encoding presets for common use cases."""

from dataclasses import dataclass, field


@dataclass
class Preset:
    name: str
    category: str
    description: str
    extension: str
    ffmpeg_args: list[str] = field(default_factory=list)


PRESETS: list[Preset] = [
    # ── Mobile ───────────────────────────────────────────────────────
    Preset(
        name="MP4 Android Full Compatible",
        category="Mobile",
        description=(
            "Maximum compatibility with Android devices. "
            "H.264 Baseline profile, Level 3.0, 720×480, 23.976 fps, "
            "AAC stereo 128 kbps, faststart enabled."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "baseline", "-level", "3.0",
            "-s", "720x480", "-r", "24000/1001", "-pix_fmt", "yuv420p",
            "-b:v", "1200k",
            "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "48000",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="MP4 iPhone / iPad",
        category="Mobile",
        description=(
            "Optimized for Apple iOS devices. "
            "H.264 High profile, 1080p, AAC 192 kbps, faststart."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.1",
            "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "medium",
            "-s", "1920x1080",
            "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="MP4 WhatsApp",
        category="Mobile",
        description=(
            "Compressed for WhatsApp sharing (16 MB limit). "
            "H.264 Baseline, 480p, low bitrate, AAC mono 64 kbps."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "baseline", "-level", "3.1",
            "-pix_fmt", "yuv420p", "-b:v", "600k", "-maxrate", "600k",
            "-bufsize", "1200k", "-s", "854x480",
            "-c:a", "aac", "-b:a", "64k", "-ac", "1", "-ar", "44100",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="MP4 Telegram",
        category="Mobile",
        description=(
            "Optimized for Telegram (up to 2 GB). "
            "H.264 Main profile, 720p, CRF 24, AAC stereo 128 kbps."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "main", "-level", "4.0",
            "-pix_fmt", "yuv420p", "-crf", "24", "-preset", "medium",
            "-s", "1280x720",
            "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "48000",
            "-movflags", "+faststart",
        ],
    ),

    # ── Social Media ─────────────────────────────────────────────────
    Preset(
        name="MP4 YouTube Upload",
        category="Social Media",
        description=(
            "YouTube recommended settings. "
            "H.264 High, 1080p, CRF 18, AAC 384 kbps, faststart."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.2",
            "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow",
            "-g", "30", "-bf", "2",
            "-c:a", "aac", "-b:a", "384k", "-ac", "2", "-ar", "48000",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="MP4 YouTube 4K",
        category="Social Media",
        description=(
            "YouTube 4K upload settings. "
            "H.264 High, 3840×2160, CRF 16, AAC 384 kbps."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "high", "-level", "5.1",
            "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "slow",
            "-s", "3840x2160",
            "-c:a", "aac", "-b:a", "384k", "-ac", "2", "-ar", "48000",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="MP4 Instagram Reels / Stories",
        category="Social Media",
        description=(
            "Vertical 9:16 for Instagram Reels/Stories. "
            "H.264 Main, 1080×1920, 30 fps, AAC 128 kbps."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "main", "-level", "4.0",
            "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "medium",
            "-s", "1080x1920", "-r", "30",
            "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="MP4 Instagram Feed",
        category="Social Media",
        description=(
            "Square 1:1 for Instagram Feed posts. "
            "H.264 Main, 1080×1080, 30 fps, AAC 128 kbps."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "main", "-level", "4.0",
            "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "medium",
            "-s", "1080x1080", "-r", "30",
            "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="MP4 TikTok",
        category="Social Media",
        description=(
            "Vertical 9:16 optimized for TikTok. "
            "H.264, 1080×1920, 30 fps, high bitrate, AAC stereo."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.0",
            "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
            "-s", "1080x1920", "-r", "30",
            "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "44100",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="MP4 Twitter / X",
        category="Social Media",
        description=(
            "Twitter/X compatible. "
            "H.264 Main, 1280×720, CRF 23, AAC 128 kbps, faststart."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "main", "-level", "3.1",
            "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "medium",
            "-s", "1280x720", "-r", "30",
            "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
            "-movflags", "+faststart",
        ],
    ),

    # ── Web ──────────────────────────────────────────────────────────
    Preset(
        name="MP4 Web / HTML5",
        category="Web",
        description=(
            "Universal web browser playback. "
            "H.264 Main, 720p, CRF 22, AAC 128 kbps, faststart."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "main", "-level", "3.1",
            "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "medium",
            "-s", "1280x720",
            "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="WebM VP9 (Web)",
        category="Web",
        description=(
            "VP9 + Opus for modern browsers. "
            "Excellent compression, 720p, CRF 30."
        ),
        extension=".webm",
        ffmpeg_args=[
            "-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0",
            "-s", "1280x720", "-pix_fmt", "yuv420p",
            "-c:a", "libopus", "-b:a", "128k", "-ac", "2", "-ar", "48000",
        ],
    ),
    Preset(
        name="GIF Animated (480p)",
        category="Web",
        description=(
            "Generate animated GIF at 480p, 10 fps. "
            "Uses palettegen for good quality."
        ),
        extension=".gif",
        ffmpeg_args=[
            "-vf", "fps=10,scale=854:-2:flags=lanczos,split[s0][s1];"
                   "[s0]palettegen[p];[s1][p]paletteuse",
            "-loop", "0",
        ],
    ),

    # ── Professional / Editing ───────────────────────────────────────
    Preset(
        name="MOV ProRes 422 (Editing)",
        category="Professional",
        description=(
            "Apple ProRes 422 for professional NLE editing. "
            "Visually lossless, very large files."
        ),
        extension=".mov",
        ffmpeg_args=[
            "-c:v", "prores_ks", "-profile:v", "2", "-pix_fmt", "yuv422p10le",
            "-c:a", "pcm_s16le",
        ],
    ),
    Preset(
        name="MOV ProRes 4444 (VFX)",
        category="Professional",
        description=(
            "Apple ProRes 4444 with alpha channel support. "
            "For compositing and VFX workflows."
        ),
        extension=".mov",
        ffmpeg_args=[
            "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
            "-c:a", "pcm_s24le",
        ],
    ),
    Preset(
        name="MKV DNxHR HQ (DaVinci Resolve)",
        category="Professional",
        description=(
            "DNxHR HQ for DaVinci Resolve and Avid. "
            "High quality intermediate codec."
        ),
        extension=".mkv",
        ffmpeg_args=[
            "-c:v", "dnxhd", "-profile:v", "dnxhr_hq",
            "-pix_fmt", "yuv422p",
            "-c:a", "pcm_s16le",
        ],
    ),

    # ── Archival / Lossless ──────────────────────────────────────────
    Preset(
        name="MKV Lossless (FFV1)",
        category="Archival",
        description=(
            "FFV1 lossless compression inside MKV. "
            "Perfect quality preservation, large files."
        ),
        extension=".mkv",
        ffmpeg_args=[
            "-c:v", "ffv1", "-level", "3", "-coder", "1",
            "-context", "1", "-slicecrc", "1",
            "-c:a", "flac",
        ],
    ),
    Preset(
        name="MKV H.265 Archival",
        category="Archival",
        description=(
            "H.265/HEVC near-lossless archival. "
            "CRF 14, veryslow preset for best compression."
        ),
        extension=".mkv",
        ffmpeg_args=[
            "-c:v", "libx265", "-crf", "14", "-preset", "veryslow",
            "-pix_fmt", "yuv420p",
            "-c:a", "flac",
        ],
    ),
    Preset(
        name="MKV H.264 Archival",
        category="Archival",
        description=(
            "High quality H.264 archival. "
            "CRF 16, veryslow, 10-bit if possible."
        ),
        extension=".mkv",
        ffmpeg_args=[
            "-c:v", "libx264", "-crf", "16", "-preset", "veryslow",
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-c:a", "flac",
        ],
    ),

    # ── Streaming ────────────────────────────────────────────────────
    Preset(
        name="MP4 Streaming (Low Latency)",
        category="Streaming",
        description=(
            "Low-latency streaming ready. "
            "H.264, 720p, keyframe every 2s, faststart."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "main", "-level", "3.1",
            "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "veryfast",
            "-g", "60", "-keyint_min", "60", "-sc_threshold", "0",
            "-s", "1280x720",
            "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "44100",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="MP4 HLS / DASH Ready",
        category="Streaming",
        description=(
            "Prepared for HLS/DASH segmentation. "
            "H.264 Main, 1080p, fixed GOP, CBR."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "main", "-level", "4.0",
            "-pix_fmt", "yuv420p", "-b:v", "4500k", "-maxrate", "4500k",
            "-bufsize", "9000k", "-preset", "medium",
            "-g", "48", "-keyint_min", "48", "-sc_threshold", "0",
            "-s", "1920x1080",
            "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000",
            "-movflags", "+faststart",
        ],
    ),

    # ── Low Bandwidth / Compression ──────────────────────────────────
    Preset(
        name="MP4 Ultra Compressed",
        category="Low Bandwidth",
        description=(
            "Maximum compression for email/slow networks. "
            "H.264 Baseline, 360p, CRF 32, AAC 64 kbps."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "baseline",
            "-pix_fmt", "yuv420p", "-crf", "32", "-preset", "veryslow",
            "-s", "640x360",
            "-c:a", "aac", "-b:a", "64k", "-ac", "1", "-ar", "22050",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="MP4 Balanced (1080p)",
        category="Low Bandwidth",
        description=(
            "Good quality/size ratio for general use. "
            "H.264 High, 1080p, CRF 24, AAC 128 kbps."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-crf", "24", "-preset", "medium",
            "-s", "1920x1080",
            "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "48000",
            "-movflags", "+faststart",
        ],
    ),

    # ── Legacy / Compatibility ──────────────────────────────────────
    Preset(
        name="AVI Legacy Compatible",
        category="Legacy",
        description=(
            "AVI with MPEG-4 + MP3 for old systems. "
            "Maximum backward compatibility."
        ),
        extension=".avi",
        ffmpeg_args=[
            "-c:v", "mpeg4", "-q:v", "5", "-s", "720x480",
            "-c:a", "libmp3lame", "-b:a", "192k", "-ac", "2", "-ar", "44100",
        ],
    ),
    Preset(
        name="MP4 DVD Standard (NTSC)",
        category="Legacy",
        description=(
            "DVD-like NTSC settings. "
            "720×480, 29.97 fps, MPEG-4, AC3 audio."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "mpeg4", "-b:v", "5000k", "-s", "720x480",
            "-r", "29.97", "-pix_fmt", "yuv420p",
            "-c:a", "ac3", "-b:a", "384k", "-ac", "6", "-ar", "48000",
        ],
    ),
    Preset(
        name="MP4 DVD Standard (PAL)",
        category="Legacy",
        description=(
            "DVD-like PAL settings. "
            "720×576, 25 fps, MPEG-4, AC3 audio."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "mpeg4", "-b:v", "5000k", "-s", "720x576",
            "-r", "25", "-pix_fmt", "yuv420p",
            "-c:a", "ac3", "-b:a", "384k", "-ac", "6", "-ar", "48000",
        ],
    ),

    # ── Audio Only ───────────────────────────────────────────────────
    Preset(
        name="MP3 High Quality (320 kbps)",
        category="Audio",
        description="Extract audio as high-quality MP3, 320 kbps, stereo, 48 kHz.",
        extension=".mp3",
        ffmpeg_args=[
            "-vn",
            "-c:a", "libmp3lame", "-b:a", "320k", "-ac", "2", "-ar", "48000",
        ],
    ),
    Preset(
        name="MP3 Podcast (128 kbps Mono)",
        category="Audio",
        description="Podcast-optimized MP3. Mono, 128 kbps, 44.1 kHz.",
        extension=".mp3",
        ffmpeg_args=[
            "-vn",
            "-c:a", "libmp3lame", "-b:a", "128k", "-ac", "1", "-ar", "44100",
        ],
    ),
    Preset(
        name="AAC High Quality (256 kbps)",
        category="Audio",
        description="Extract audio as AAC, 256 kbps, stereo, 48 kHz.",
        extension=".aac",
        ffmpeg_args=[
            "-vn",
            "-c:a", "aac", "-b:a", "256k", "-ac", "2", "-ar", "48000",
        ],
    ),
    Preset(
        name="FLAC Lossless",
        category="Audio",
        description="Lossless audio extraction as FLAC. No quality loss.",
        extension=".flac",
        ffmpeg_args=[
            "-vn",
            "-c:a", "flac",
        ],
    ),
    Preset(
        name="WAV Uncompressed (16-bit)",
        category="Audio",
        description="Uncompressed PCM 16-bit WAV. Studio quality, large files.",
        extension=".wav",
        ffmpeg_args=[
            "-vn",
            "-c:a", "pcm_s16le", "-ar", "48000",
        ],
    ),
    Preset(
        name="Opus Voice (48 kbps)",
        category="Audio",
        description="Opus codec optimized for voice. Extremely efficient at 48 kbps.",
        extension=".ogg",
        ffmpeg_args=[
            "-vn",
            "-c:a", "libopus", "-b:a", "48k", "-ac", "1",
            "-application", "voip",
        ],
    ),
    Preset(
        name="Opus Music (192 kbps)",
        category="Audio",
        description="Opus codec for music. Excellent quality at 192 kbps.",
        extension=".ogg",
        ffmpeg_args=[
            "-vn",
            "-c:a", "libopus", "-b:a", "192k", "-ac", "2",
            "-application", "audio",
        ],
    ),

    # ── Presentation / Special ───────────────────────────────────────
    Preset(
        name="MP4 Presentation / Screencast",
        category="Special",
        description=(
            "Screencast with sharp text and low frame rate. "
            "H.264, 1080p, 15 fps, CRF 20, AAC 96 kbps."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-tune", "stillimage",
            "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "slow",
            "-r", "15", "-s", "1920x1080",
            "-c:a", "aac", "-b:a", "96k", "-ac", "2", "-ar", "44100",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="MP4 Surveillance / CCTV",
        category="Special",
        description=(
            "Low bitrate long-recording style. "
            "H.264 Baseline, 480p, 10 fps, 400 kbps."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "baseline",
            "-pix_fmt", "yuv420p", "-b:v", "400k",
            "-r", "10", "-s", "854x480",
            "-c:a", "aac", "-b:a", "48k", "-ac", "1", "-ar", "22050",
            "-movflags", "+faststart",
        ],
    ),
    Preset(
        name="MP4 Slow Motion (60 fps)",
        category="Special",
        description=(
            "High frame rate for smooth slow-motion playback. "
            "H.264 High, 1080p, 60 fps, CRF 18."
        ),
        extension=".mp4",
        ffmpeg_args=[
            "-c:v", "libx264", "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow",
            "-r", "60", "-s", "1920x1080",
            "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000",
            "-movflags", "+faststart",
        ],
    ),
]

# Categories in display order
PRESET_CATEGORIES = [
    "Mobile",
    "Social Media",
    "Web",
    "Professional",
    "Archival",
    "Streaming",
    "Low Bandwidth",
    "Legacy",
    "Audio",
    "Special",
]
