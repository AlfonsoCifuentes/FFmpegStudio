import sys
import types
import unittest


try:
    import PySide6.QtCore  # noqa: F401
except ModuleNotFoundError:
    pyside = types.ModuleType("PySide6")
    qtcore = types.ModuleType("PySide6.QtCore")

    class _Signal:
        def __init__(self, *args, **kwargs):
            pass

        def connect(self, *args, **kwargs):
            pass

        def emit(self, *args, **kwargs):
            pass

    class _QThread:
        def __init__(self, *args, **kwargs):
            pass

    qtcore.QObject = object
    qtcore.QProcess = object
    qtcore.QThread = _QThread
    qtcore.Signal = _Signal
    pyside.QtCore = qtcore
    sys.modules["PySide6"] = pyside
    sys.modules["PySide6.QtCore"] = qtcore


from app.ffmpeg_backend import (
    build_batch_output_path, build_convert_command, build_preset_command,
    build_subtitles_filter,
)
from app.presets import PRESETS


class ConvertCommandTests(unittest.TestCase):
    def test_auto_webm_uses_compatible_codecs(self):
        args = build_convert_command("input.mp4", "output.webm")

        self.assertIn("libvpx-vp9", args)
        self.assertIn("libopus", args)
        self.assertNotIn("copy", args)

    def test_audio_only_output_omits_video_options(self):
        args = build_convert_command(
            "input.mp4",
            "output.mp3",
            resolution="1280x720",
            frame_rate="30",
            video_bitrate="5M",
            audio_bitrate="192k",
        )

        self.assertIn("-vn", args)
        self.assertIn("libmp3lame", args)
        self.assertIn("192k", args)
        self.assertNotIn("-s", args)
        self.assertNotIn("-r", args)
        self.assertNotIn("-b:v", args)

    def test_video_only_output_omits_audio_options(self):
        args = build_convert_command(
            "input.mp4",
            "output.gif",
            audio_bitrate="192k",
            sample_rate="48000",
            channels="2",
        )

        self.assertIn("-an", args)
        self.assertNotIn("-c:a", args)
        self.assertNotIn("-b:a", args)
        self.assertNotIn("-ar", args)
        self.assertNotIn("-ac", args)

    def test_extra_args_keep_quoted_values_together(self):
        args = build_convert_command(
            "input.mp4",
            "output.mp4",
            extra_args='-metadata title="My Video"',
        )

        self.assertIn("title=My Video", args)

    def test_extra_args_preserve_quoted_windows_paths(self):
        args = build_convert_command(
            "input.mp4",
            "output.mp4",
            extra_args=r'-vf "subtitles=C:\Videos\sub file.srt"',
        )

        self.assertIn(r"subtitles=C:\Videos\sub file.srt", args)

    def test_burn_external_subtitles_reencodes_when_copy_selected(self):
        args = build_convert_command(
            r"C:\Videos\input.mkv",
            r"C:\Videos\output.mp4",
            video_codec="copy",
            burn_subtitles=True,
            subtitle_path=r"C:\Videos\sub file.srt",
        )

        self.assertIn("-vf", args)
        self.assertIn("-sn", args)
        self.assertNotIn("copy", args)
        self.assertIn("libx264", args)
        self.assertTrue(any("sub file.srt" in arg for arg in args))

    def test_burn_embedded_subtitles_uses_stream_index(self):
        args = build_convert_command(
            "input.mkv",
            "output.mp4",
            burn_subtitles=True,
            subtitle_stream_index=1,
        )

        self.assertIn("-vf", args)
        self.assertTrue(any(":si=1" in arg for arg in args))

    def test_burn_subtitles_rejects_audio_only_outputs(self):
        with self.assertRaises(ValueError):
            build_convert_command(
                "input.mkv",
                "output.mp3",
                burn_subtitles=True,
                subtitle_stream_index=0,
            )

    def test_subtitle_filter_escapes_windows_drive_colon(self):
        value = build_subtitles_filter(r"C:\Videos\input.mkv", subtitle_stream_index=0)

        self.assertIn(r"C\:/Videos/input.mkv", value)
        self.assertIn(":si=0", value)


class BatchOutputPathTests(unittest.TestCase):
    def test_same_folder_same_extension_does_not_overwrite_input(self):
        out = build_batch_output_path(r"C:\Videos\clip.mp4", r"C:\Videos", ".mp4")

        self.assertTrue(out.endswith(r"C:\Videos\clip_output.mp4"))

    def test_different_folder_uses_original_stem_and_target_extension(self):
        out = build_batch_output_path(r"C:\Videos\clip.mp4", r"D:\Out", ".webm")

        self.assertTrue(out.endswith(r"D:\Out\clip.webm"))


class PresetCommandTests(unittest.TestCase):
    def test_android_full_compatible_preset_exists(self):
        self.assertTrue(any(p.name == "MP4 Full Android Compatible" for p in PRESETS))

    def test_video_preset_maps_video_and_optional_audio(self):
        args = build_preset_command(
            "input.mkv",
            "output.mp4",
            ["-c:v", "libx264", "-c:a", "aac"],
        )

        self.assertEqual(args[:7], ["-i", "input.mkv", "-map", "0:v:0", "-map", "0:a?", "-sn"])
        self.assertEqual(args[-1], "output.mp4")

    def test_burn_subtitles_adds_filter_without_subtitle_output_stream(self):
        args = build_preset_command(
            "input.mkv",
            "output.mp4",
            ["-c:v", "libx264", "-c:a", "aac"],
            burn_subtitles=True,
            subtitle_stream_index=0,
        )

        self.assertIn("-sn", args)
        self.assertIn("-vf", args)
        self.assertTrue(any(":si=0" in arg for arg in args))

    def test_burn_subtitles_combines_with_existing_video_filter(self):
        args = build_preset_command(
            "input.mkv",
            "output.gif",
            ["-vf", "fps=10,scale=854:-2"],
            burn_subtitles=True,
            subtitle_stream_index=0,
        )

        vf = args[args.index("-vf") + 1]
        self.assertTrue(vf.startswith("subtitles="))
        self.assertIn(",fps=10,scale=854:-2", vf)

    def test_video_only_preset_does_not_map_audio(self):
        args = build_preset_command(
            "input.mkv",
            "output.gif",
            ["-vf", "fps=10,scale=854:-2"],
        )

        self.assertIn("-map", args)
        self.assertIn("0:v:0", args)
        self.assertNotIn("0:a?", args)

    def test_burn_subtitles_rejects_audio_preset(self):
        with self.assertRaises(ValueError):
            build_preset_command(
                "input.mkv",
                "output.mp3",
                ["-vn", "-c:a", "libmp3lame"],
                burn_subtitles=True,
                subtitle_stream_index=0,
            )


if __name__ == "__main__":
    unittest.main()
