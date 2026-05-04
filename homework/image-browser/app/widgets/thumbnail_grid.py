import os

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QListView, QSizePolicy

from ..core.constants import THUMB_SIZE
from ..core.image_loader import list_images

PATH_ROLE = Qt.UserRole + 1


class ThumbnailGrid(QListView):
    imageSelected = pyqtSignal(str)
    folderLoaded = pyqtSignal(str, int)  # folder, count

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = QStandardItemModel(self)
        self.setModel(self._model)

        self.setViewMode(QListView.IconMode)
        self.setIconSize(QSize(THUMB_SIZE, THUMB_SIZE))
        self.setGridSize(QSize(THUMB_SIZE + 32, THUMB_SIZE + 48))
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Static)
        self.setSpacing(8)
        self.setUniformItemSizes(True)
        self.setWordWrap(True)
        self.setSelectionMode(QListView.SingleSelection)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._placeholder_icon = self._build_placeholder_icon()

        self.clicked.connect(self._emit_selection)

    def _build_placeholder_icon(self):
        pix = QPixmap(THUMB_SIZE, THUMB_SIZE)
        pix.fill(Qt.darkGray)
        return QIcon(pix)

    def load_folder(self, folder):
        self._model.clear()
        if not folder or not os.path.isdir(folder):
            self.folderLoaded.emit(folder or "", 0)
            return

        paths = list_images(folder)
        for row, path in enumerate(paths):
            item = QStandardItem(os.path.basename(path))
            item.setEditable(False)

            # Load thumbnail synchronously (simple & reliable)
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
