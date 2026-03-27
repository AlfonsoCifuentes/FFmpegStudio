# FFmpeg Studio

**A professional graphical frontend for FFmpeg on Windows.**

Created by **Alfonso Cifuentes Alonso**.

---

## Features

- **Encoding Presets** — 30+ one-click presets for Android, iPhone, YouTube, Instagram, TikTok, WhatsApp, Telegram, web, streaming, professional editing, archival, and more.
- **Format Conversion** — Convert between any media format with full control over codecs, bitrate, resolution, frame rate, and quality.
- **Trim / Cut** — Precision video trimming with stream copy for instant cuts.
- **Audio Extraction** — Extract and convert audio tracks to MP3, AAC, FLAC, WAV, Opus, and more.
- **Video Filters** — Apply filters like denoise, sharpen, blur, rotate, grayscale, sepia, vignette, stabilization, and more.
- **Merge / Concatenate** — Join multiple files with stream copy or re-encoding.
- **Resize / Scale** — Resize video to any resolution while preserving aspect ratio.
- **Screenshots** — Extract individual frames or generate frame sequences.
- **Metadata Editor** — View and edit media file metadata tags.
- **Advanced Mode** — Direct ffmpeg command-line input for power users.
- **About & Updates** — Built-in update checker that downloads directly from this GitHub repository.

## Screenshots

The application features a premium dark theme with purple, teal, and green accents, a sidebar navigation with SVG icons, and a modern card-based UI.

## Requirements

- **Windows 10/11** (64-bit)
- **FFmpeg** must be installed and available in your system PATH.  
  Download from: <https://www.gyan.dev/ffmpeg/builds/>

## Installation

### Installer (Recommended)

Download the latest `FFmpegStudio_Setup.exe` from [Releases](https://github.com/AlfonsoCifuentes/FFmpegStudio/releases) and run it. The installer supports English and Spanish and provides optional desktop shortcut creation.

### From Source

```bash
git clone https://github.com/AlfonsoCifuentes/FFmpegStudio.git
cd FFmpegStudio
pip install PySide6 Pillow
python main.py
```

## Building

### Executable (PyInstaller)

```bash
pip install pyinstaller
pyinstaller ffmpegstudio.spec --noconfirm
```

The built application will be in `dist/FFmpegStudio/`.

### Installer (Inno Setup)

Install [Inno Setup 6](https://jrsoftware.org/isdl.php), then compile `installer.iss`.

## Presets Included

| Category | Preset |
|----------|--------|
| Mobile | MP4 Android Full Compatible, MP4 iPhone/iPad, MP4 WhatsApp, MP4 Telegram |
| Social Media | YouTube Upload, YouTube 4K, Instagram Reels/Stories, Instagram Feed, TikTok, Twitter/X |
| Web | MP4 Web/HTML5, WebM VP9, GIF Animated |
| Professional | MOV ProRes 422, MOV ProRes 4444, MKV DNxHR HQ |
| Archival | MKV Lossless (FFV1), MKV H.265 Archival, MKV H.264 Archival |
| Streaming | MP4 Low Latency, MP4 HLS/DASH Ready |
| Low Bandwidth | MP4 Ultra Compressed, MP4 Balanced (1080p) |
| Legacy | AVI Legacy Compatible, DVD NTSC, DVD PAL |
| Audio | MP3 320 kbps, MP3 Podcast, AAC 256 kbps, FLAC Lossless, WAV 16-bit, Opus Voice, Opus Music |
| Special | Presentation/Screencast, Surveillance/CCTV, Slow Motion 60fps |

## Tech Stack

- **Python 3.14** — Application language
- **PySide6 (Qt6)** — GUI framework
- **FFmpeg** — Media processing engine
- **PyInstaller** — Executable bundling
- **Inno Setup 6** — Windows installer

## License

MIT License

Copyright (c) 2025-2026 Alfonso Cifuentes Alonso

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

**FFmpeg** is a trademark of Fabrice Bellard. This project is not affiliated with or endorsed by the FFmpeg project.
