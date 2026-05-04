from PyQt5.QtCore import QThread, pyqtSignal

from .constants import THUMB_SIZE
from .image_loader import make_thumbnail


class ThumbnailWorker(QThread):
    finished = pyqtSignal(int, str, object)

    def __init__(self, row, path, size=THUMB_SIZE):
        super().__init__()
        self.row = row
        self.path = path
        self.size = size

    def run(self):
        pix = make_thumbnail(self.path, self.size)
        self.finished.emit(self.row, self.path, pix)
