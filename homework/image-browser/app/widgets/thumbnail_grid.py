"""
thumbnail_grid.py — Themed thumbnail grid with styled placeholder icon.
"""

import os

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QListView, QSizePolicy

from ..core.constants import THUMB_SIZE
from ..core.image_loader import list_images
from ..theme import C_BG_SURFACE, C_BORDER, C_TEXT_LOW, FONT_MONO

PATH_ROLE = Qt.UserRole + 1


def _make_placeholder_icon(size: int) -> QIcon:
    """Draw a subtle placeholder icon instead of a plain dark square."""
    pix = QPixmap(size, size)
    pix.fill(QColor(C_BG_SURFACE))
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    # border
    p.setPen(QColor(C_BORDER))
    p.setBrush(Qt.NoBrush)
    p.drawRect(1, 1, size - 2, size - 2)
    # crosshair
    cx, cy = size // 2, size // 2
    p.drawLine(cx - 10, cy, cx + 10, cy)
    p.drawLine(cx, cy - 10, cx, cy + 10)
    p.end()
    return QIcon(pix)


class ThumbnailGrid(QListView):
    imageSelected = pyqtSignal(str)
    folderLoaded  = pyqtSignal(str, int)   # folder, count

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = QStandardItemModel(self)
        self.setModel(self._model)

        self.setViewMode(QListView.IconMode)
        self.setIconSize(QSize(THUMB_SIZE, THUMB_SIZE))
        self.setGridSize(QSize(THUMB_SIZE + 32, THUMB_SIZE + 44))
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setSpacing(8)
        self.setUniformItemSizes(True)
        self.setWordWrap(True)
        self.setSelectionMode(QListView.SingleSelection)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._placeholder_icon = _make_placeholder_icon(THUMB_SIZE)
        self.clicked.connect(self._emit_selection)

    def load_folder(self, folder: str):
        self._model.clear()
        if not folder or not os.path.isdir(folder):
            self.folderLoaded.emit(folder or "", 0)
            return

        paths = list_images(folder)
        for path in paths:
            name = os.path.basename(path)
            item = QStandardItem(name)
            item.setEditable(False)
            item.setFont(QFont(FONT_MONO, 8))

            from ..core.image_loader import make_thumbnail
            thumb = make_thumbnail(path, THUMB_SIZE)
            item.setIcon(QIcon(thumb) if not thumb.isNull() else self._placeholder_icon)
            item.setData(path, PATH_ROLE)
            item.setToolTip(path)
            item.setTextAlignment(Qt.AlignCenter)
            self._model.appendRow(item)

        self.folderLoaded.emit(folder, len(paths))

    def _emit_selection(self, index):
        path = index.data(PATH_ROLE)
        if path:
            self.imageSelected.emit(path)
