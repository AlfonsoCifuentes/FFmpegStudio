"""FFmpeg Studio – Entry point."""

import os
import sys
import traceback
import logging


def _setup_logging():
    """Configure logging to a file in APPDATA so crashes are traceable."""
    log_dir = os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")), "FFmpegStudio"
    )
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "ffmpegstudio.log")
    logging.basicConfig(
        filename=log_path,
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    return log_path


def main():
    log_path = _setup_logging()
    logging.info("FFmpeg Studio starting – Python %s", sys.version)

    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont

        from app.styles import GLOBAL_STYLE
        from app.main_window import MainWindow

        # High-DPI support
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        app = QApplication(sys.argv)
        app.setApplicationName("FFmpeg Studio")
        app.setOrganizationName("FFmpegStudio")

        # Set default font
        font = QFont("Segoe UI", 10)
        font.setHintingPreference(QFont.PreferFullHinting)
        app.setFont(font)

        # Apply global stylesheet
        app.setStyleSheet(GLOBAL_STYLE)

        window = MainWindow()
        window.show()

        sys.exit(app.exec())

    except Exception:
        err = traceback.format_exc()
        logging.critical("Fatal error:\n%s", err)
        # Try to show a dialog; if Qt itself failed, fall back to writing the log
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None, "FFmpeg Studio – Error",
                f"The application could not start.\n\n{err}\n\nLog: {log_path}",
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
