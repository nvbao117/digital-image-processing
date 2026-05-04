from PyQt5.QtCore import QDir, pyqtSignal
from PyQt5.QtWidgets import QFileSystemModel, QSizePolicy, QTreeView


class FolderTree(QTreeView):
    folderSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = QFileSystemModel(self)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.model.setRootPath("")
        self.setModel(self.model)

        for col in range(1, self.model.columnCount()):
            self.hideColumn(col)
        self.setHeaderHidden(True)

        self.setAnimated(True)
        self.setIndentation(16)
        self.setUniformRowHeights(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.clicked.connect(self._emit_folder)

    def set_root(self, path):
        if not path:
            return
        index = self.model.setRootPath(path)
        self.setRootIndex(index)
        self.expand(index)

    def _emit_folder(self, index):
        path = self.model.filePath(index)
        if path:
            self.folderSelected.emit(path)
