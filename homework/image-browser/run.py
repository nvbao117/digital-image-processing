#!/usr/bin/env python
"""Wrapper script to fix Qt plugin path conflicts with OpenCV."""

import os
import sys
import subprocess

# Linux-specific fixes for Qt/OpenCV conflicts
if sys.platform.startswith("linux"):
    # Remove OpenCV's Qt plugin path to avoid conflicts
    os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

    # On Wayland, use xcb platform if needed
    if os.environ.get("XDG_SESSION_TYPE") == "wayland":
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    # Ensure PyQt5 uses system Qt plugins on Debian/Ubuntu
    qt_plugin_path = "/usr/lib/x86_64-linux-gnu/qt5/plugins"
    if os.path.isdir(qt_plugin_path):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_plugin_path

# Run main.py with subprocess to ensure clean environment
result = subprocess.run([sys.executable, "-c", """
import sys
from PyQt5.QtWidgets import QApplication
from app.core.constants import WINDOW_TITLE
from app.main_window import MainWindow

app = QApplication(sys.argv)
app.setApplicationName(WINDOW_TITLE)
window = MainWindow()
window.show()
sys.exit(app.exec_())
"""], cwd=os.path.dirname(os.path.abspath(__file__)))

sys.exit(result.returncode)
