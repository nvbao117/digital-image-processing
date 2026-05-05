import os as _os

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

THUMB_SIZE = 128

PLACEHOLDER_TEXT = "NO IMAGE AVAILABLE"

WINDOW_TITLE = "Image Browser"
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720



# Default root folder shown in the tree on startup.
# Resolves to: constants.py → core/ → app/ → image-browser/ → homework/ → digital-image-processing/
_PROJECT_ROOT = _os.path.normpath(
    _os.path.join(_os.path.dirname(__file__), "..", "..", "..", "..")
)
DEFAULT_DIR = _PROJECT_ROOT if _os.path.isdir(_PROJECT_ROOT) else _os.path.expanduser("~")
