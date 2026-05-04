import os
import sys

# Fix Qt platform conflicts
os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)
os.environ.pop("QT_API", None)
os.environ.pop("DISPLAY", None)

# Use wayland if available (more reliable than xcb in modern GNOME)
if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "wayland"

from PyQt5.QtWidgets import QApplication

from app.core.constants import WINDOW_TITLE
from app.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
