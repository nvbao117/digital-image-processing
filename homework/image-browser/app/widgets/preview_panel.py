from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from ..core.constants import PLACEHOLDER_TEXT
from ..core.image_loader import load_qpixmap


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()

        self.label = QLabel(PLACEHOLDER_TEXT)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label.setStyleSheet(
            "QLabel {"
            " color: #888;"
            " font-size: 22px;"
            " letter-spacing: 2px;"
            " background-color: #1e1e1e;"
            " border: 1px solid #333;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def show_image(self, path):
        pix = load_qpixmap(path)
        if pix.isNull():
            self.clear()
            self.label.setText(f"Cannot load: {path}")
            return
        self._pixmap = pix
        self._render()

    def clear(self):
        self._pixmap = QPixmap()
        self.label.setText(PLACEHOLDER_TEXT)
        self.label.setPixmap(QPixmap())

    def _render(self):
        if self._pixmap.isNull():
            return
        scaled = self._pixmap.scaled(
            self.label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render()
