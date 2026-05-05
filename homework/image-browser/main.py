import os
import sys

# Fix Qt platform conflicts (Linux only)
if sys.platform.startswith("linux"):
    os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)
    if "QT_QPA_PLATFORM" not in os.environ:
        if os.environ.get("XDG_SESSION_TYPE") == "wayland":
            os.environ["QT_QPA_PLATFORM"] = "wayland"
        else:
            os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt5.QtWidgets import QApplication

from app.core.constants import WINDOW_TITLE
from app.main_window import MainWindow
from app.theme import global_stylesheet


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)
    app.setStyleSheet(global_stylesheet())   # apply theme globally
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
