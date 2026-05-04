import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..core.constants import PLACEHOLDER_TEXT
from ..core.image_loader import load_qpixmap

_BTN_STYLE = (
    "QPushButton {"
    " background:#2d2d2d; color:#ddd; border:1px solid #555;"
    " padding:4px 10px; border-radius:3px; font-size:12px;"
    "}"
    "QPushButton:hover { background:#3a3a3a; }"
    "QPushButton:pressed { background:#222; }"
    "QPushButton:disabled { color:#555; border-color:#333; }"
)


def _cv_to_qpixmap(img):
    if img is None:
        return QPixmap()
    if img.ndim == 2:
        h, w = img.shape
        qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8).copy()
    else:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(qimg)


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._orig_pixmap = QPixmap()
        self._pixmap = QPixmap()
        self._cv_image = None

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._anim_step)
        self._anim_frame = 0
        self._anim_angle = 0.0

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

        self.btn_rgb = QPushButton("RGB Channels")
        self.btn_gray = QPushButton("Grayscale")
        self.btn_rotate = QPushButton("Rotate & Zoom")
        self.btn_crop = QPushButton("Crop Center")
        self.btn_reset = QPushButton("Reset")

        self._proc_buttons = (
            self.btn_rgb,
            self.btn_gray,
            self.btn_rotate,
            self.btn_crop,
            self.btn_reset,
        )
        for btn in self._proc_buttons:
            btn.setEnabled(False)
            btn.setStyleSheet(_BTN_STYLE)

        self.btn_rgb.clicked.connect(self._show_rgb_channels)
        self.btn_gray.clicked.connect(self._show_grayscale)
        self.btn_rotate.clicked.connect(self._start_rotation)
        self.btn_crop.clicked.connect(self._show_crop)
        self.btn_reset.clicked.connect(self._show_original)

        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(6, 4, 6, 6)
        btn_bar.setSpacing(6)
        for btn in self._proc_buttons:
            btn_bar.addWidget(btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.label)
        layout.addLayout(btn_bar)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_image(self, path):
        self._stop_animation()
        pix = load_qpixmap(path)
        if pix.isNull():
            self.clear()
            self.label.setText(f"Cannot load: {path}")
            return

        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is not None and img.ndim > 2 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        self._cv_image = img

        self._orig_pixmap = pix
        self._pixmap = pix
        self._render()

        for btn in self._proc_buttons:
            btn.setEnabled(img is not None)

    def clear(self):
        self._stop_animation()
        self._cv_image = None
        self._orig_pixmap = QPixmap()
        self._pixmap = QPixmap()
        self.label.setText(PLACEHOLDER_TEXT)
        self.label.setPixmap(QPixmap())
        for btn in self._proc_buttons:
            btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

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

    def _display_cv(self, img):
        """Render a cv2 numpy array into the label without touching _orig_pixmap."""
        self._stop_animation()
        pix = _cv_to_qpixmap(img)
        if pix.isNull():
            return
        self._pixmap = pix
        self._render()

    # ------------------------------------------------------------------
    # Processing operations
    # ------------------------------------------------------------------

    def _show_original(self):
        self._stop_animation()
        self._pixmap = self._orig_pixmap
        self._render()

    def _show_rgb_channels(self):
        img = self._cv_image
        if img is None:
            return
        if img.ndim == 2:
            self._display_cv(img)
            return

        b, g, r = cv2.split(img)
        zeros = np.zeros_like(b)

        r_img = cv2.merge([zeros, zeros, r])
        g_img = cv2.merge([zeros, g, zeros])
        b_img = cv2.merge([b, zeros, zeros])

        h, w = img.shape[:2]
        sh, sw = h // 2, w // 2

        def _label(src, text):
            out = cv2.resize(src, (sw, sh))
            cv2.putText(out, text, (6, 22), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255, 255, 255), 2, cv2.LINE_AA)
            return out

        top = np.hstack([_label(img, "Original"), _label(r_img, "Red")])
        bot = np.hstack([_label(g_img, "Green"), _label(b_img, "Blue")])
        composite = np.vstack([top, bot])
        self._display_cv(composite)

    def _show_grayscale(self):
        img = self._cv_image
        if img is None:
            return
        gray = img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self._display_cv(gray)

    def _show_crop(self):
        img = self._cv_image
        if img is None:
            return
        h, w = img.shape[:2]
        crop_h, crop_w = h // 2, w // 2
        y1 = (h - crop_h) // 2
        x1 = (w - crop_w) // 2
        self._display_cv(img[y1:y1 + crop_h, x1:x1 + crop_w])

    # ------------------------------------------------------------------
    # Rotation animation
    # ------------------------------------------------------------------

    def _start_rotation(self):
        if self._cv_image is None:
            return
        self._anim_frame = 0
        self._anim_angle = 0.0
        self._anim_timer.start(100)

    def _stop_animation(self):
        self._anim_timer.stop()
        self._anim_frame = 0
        self._anim_angle = 0.0

    def _anim_step(self):
        img = self._cv_image
        if img is None:
            self._stop_animation()
            return

        i = self._anim_frame
        if i >= 100:
            self._stop_animation()
            self._pixmap = self._orig_pixmap
            self._render()
            return

        h, w = img.shape[:2]
        center = (w // 2, h // 2)

        if i < 50:
            scale = 1.0 - 0.7 * (i / 49.0)
        else:
            scale = 0.3 + 0.7 * ((i - 50) / 49.0)

        self._anim_angle += 15.0
        M = cv2.getRotationMatrix2D(center, self._anim_angle, scale)
        rotated = cv2.warpAffine(img, M, (w, h))

        pix = _cv_to_qpixmap(rotated)
        if not pix.isNull():
            self._pixmap = pix
            self._render()

        self._anim_frame += 1
