import os

from PyQt5.QtCore import QDir, Qt
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QMainWindow,
    QSplitter,
    QStyle,
    QToolBar,
)

from .core.constants import (
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    SPLITTER_RATIO,
    WINDOW_TITLE,
)
from .widgets.folder_tree import FolderTree
from .widgets.preview_panel import PreviewPanel
from .widgets.thumbnail_grid import ThumbnailGrid


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        self._build_toolbar()
        self._build_central()
        self._wire_signals()

        self.statusBar().showMessage("Chọn một folder để bắt đầu duyệt ảnh.")
        self.tree.set_root(QDir.homePath())

    def _build_toolbar(self):
        toolbar = QToolBar("Main", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        style = self.style()
        open_icon = style.standardIcon(QStyle.SP_DirOpenIcon)
        close_icon = style.standardIcon(QStyle.SP_DialogCloseButton)

        self.action_open = QAction(open_icon, "Folder selection", self)
        self.action_open.setShortcut("Ctrl+O")
        self.action_open.triggered.connect(self._on_open_folder)
        toolbar.addAction(self.action_open)

        self.action_close = QAction(close_icon, "Close", self)
        self.action_close.setShortcut("Ctrl+Q")
        self.action_close.triggered.connect(self.close)
        toolbar.addAction(self.action_close)

    def _build_central(self):
        self.tree = FolderTree(self)
        self.grid = ThumbnailGrid(self)
        self.preview = PreviewPanel(self)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.grid)
        splitter.addWidget(self.preview)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setCollapsible(2, False)

        for index, weight in enumerate(SPLITTER_RATIO):
            splitter.setStretchFactor(index, weight)

        total = sum(SPLITTER_RATIO)
        sizes = [int(DEFAULT_WIDTH * w / total) for w in SPLITTER_RATIO]
        splitter.setSizes(sizes)

        self.setCentralWidget(splitter)

    def _wire_signals(self):
        self.tree.folderSelected.connect(self.grid.load_folder)
        self.tree.folderSelected.connect(self._on_folder_changed)
        self.grid.imageSelected.connect(self.preview.show_image)
        self.grid.folderLoaded.connect(self._on_folder_loaded)

    def _on_open_folder(self):
        start_dir = QDir.homePath()
        folder = QFileDialog.getExistingDirectory(
            self,
            "Chọn folder ảnh",
            start_dir,
            QFileDialog.ShowDirsOnly,
        )
        if not folder:
            return
        self.tree.set_root(folder)
        self.grid.load_folder(folder)
        self.preview.clear()
        self._on_folder_changed(folder)

    def _on_folder_changed(self, folder):
        self.preview.clear()
        self.statusBar().showMessage(f"Folder: {folder}")

    def _on_folder_loaded(self, folder, count):
        name = os.path.basename(folder.rstrip(os.sep)) or folder
        self.statusBar().showMessage(f"Folder: {name} — {count} ảnh")
