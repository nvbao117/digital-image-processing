"""
preview_panel.py — Image preview with info hierarchy.

Layout (top → bottom)
─────────────────────
  ┌─ Panel header (36px) ───────────────────────────┐
  │  "PREVIEW"                   filename · w×h · Nch │
  ├─ Canvas ────────────────────────────────────────┤
  │  Placeholder canvas (crosshair dot-grid)         │
  │  OR scaled image                                 │
  ├─ Info strip (28px) ─────────────────────────────┤
  │  File size · Zoom · Color mode                   │
  └──────────────────────────────────────────────────┘

Processing operations have been moved to ProcessingSidebar (right panel).
This widget exposes a clean public API called by MainWindow:
  show_image(path)   — load and display an image
  clear()            — reset to placeholder
  display_cv(img)    — show a processed cv2 array
  start_rotate()     — start rotation animation
  reset_to_original() — restore original image
"""

import os

import cv2
import numpy as np

from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QImage, QPixmap, QColor, QPainter
from PyQt5.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..core.image_loader import load_qpixmap
from ..icons import IC, ICON_SIZE_SM
from ..theme import (
    C_ACCENT, C_ACCENT_DIM, C_ACCENT_HOT,
    C_BG_BASE, C_BG_DEEP, C_BG_HOVER, C_BG_SURFACE,
    C_BORDER, C_BORDER_MID,
    C_TEXT_HI, C_TEXT_LOW, C_TEXT_MID, C_TEXT_DEAD,
    FONT_MONO,
)


# ─────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────
def _cv_to_qpixmap(img: np.ndarray) -> QPixmap:
    if img is None:
        return QPixmap()
    if img.ndim == 2:
        h, w = img.shape
        qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8).copy()
    else:
        rgb  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(qimg)


def _human_size(path: str) -> str:
    try:
        b = os.path.getsize(path)
        if b < 1024:
            return f"{b} B"
        if b < 1024 ** 2:
            return f"{b / 1024:.1f} KB"
        return f"{b / 1024**2:.1f} MB"
    except OSError:
        return ""


# ─────────────────────────────────────────────
# Placeholder canvas (painted crosshair + dots)
# ─────────────────────────────────────────────
class PlaceholderCanvas(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setStyleSheet(f"background: {C_BG_DEEP}; border: none;")

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        # Dot-grid
        grid_c = QColor(C_BORDER)
        grid_c.setAlpha(70)
        p.setPen(grid_c)
        sp = 40
        for x in range(0, w, sp):
            for y in range(0, h, sp):
                p.drawPoint(x, y)

        # Crosshair
        arm_c = QColor(C_ACCENT_DIM)
        arm_c.setAlpha(140)
        p.setPen(arm_c)
        arm, gap = 32, 14
        p.drawLine(cx - arm - gap, cy, cx - gap, cy)
        p.drawLine(cx + gap,       cy, cx + arm + gap, cy)
        p.drawLine(cx, cy - arm - gap, cx, cy - gap)
        p.drawLine(cx, cy + gap,       cx, cy + arm + gap)

        # Centre dot
        p.setBrush(QColor(C_ACCENT_DIM))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx - 3, cy - 3, 6, 6)

        # Hint text
        p.setPen(QColor(C_TEXT_LOW))
        f = QFont(FONT_MONO, 9)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 3)
        p.setFont(f)
        p.drawText(0, cy + 52, w, 20, Qt.AlignCenter, "SELECT AN IMAGE")
        p.end()


# ─────────────────────────────────────────────
# Image canvas (scales pixmap to widget size)
# ─────────────────────────────────────────────
class ImageCanvas(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"background: {C_BG_DEEP}; border: none;")
        self._src = QPixmap()

    def set_pixmap(self, pix: QPixmap):
        self._src = pix
        self._rescale()

    def clear_pixmap(self):
        self._src = QPixmap()
        self.setPixmap(QPixmap())

    def _rescale(self):
        if self._src.isNull():
            return
        self.setPixmap(
            self._src.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale()

    def zoom_ratio(self) -> float | None:
        """Return display/original width ratio for zoom indicator."""
        if self._src.isNull() or self.width() == 0:
            return None
        pix = self._src.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pix.width() / self._src.width()


# ─────────────────────────────────────────────
# Preview Panel
# ─────────────────────────────────────────────
class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C_BG_DEEP};")

        self._orig_pixmap: QPixmap = QPixmap()
        self._cv_image: np.ndarray | None = None
        self._current_path: str = ""

        # Rotation animation state
        self._anim_timer  = QTimer(self)
        self._anim_timer.timeout.connect(self._anim_step)
        self._anim_frame  = 0
        self._anim_angle  = 0.0

        self._build_ui()

    # ──────────────────────────────────────────
    # Build
    # ──────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Panel header ──────────────────────
        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet(f"""
            background: {C_BG_BASE};
            border-bottom: 1px solid {C_BORDER};
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(0)

        panel_lbl = QLabel("Preview")
        panel_lbl.setFont(QFont(FONT_MONO, 12))
        panel_lbl.setStyleSheet(f"color: {C_TEXT_MID}; background: transparent;")

        icon_lbl = QLabel()
        icon_lbl.setPixmap(IC.preview().pixmap(ICON_SIZE_SM))
        icon_lbl.setStyleSheet("background: transparent;")
        hl.addWidget(icon_lbl)
        hl.addSpacing(5)
        hl.addWidget(panel_lbl)
        hl.addStretch()

        # Filename label (right-aligned, truncated)
        self.filename_lbl = QLabel("")
        self.filename_lbl.setFont(QFont(FONT_MONO, 9))
        self.filename_lbl.setStyleSheet(f"color: {C_TEXT_HI}; background: transparent;")
        self.filename_lbl.setMaximumWidth(220)
        hl.addWidget(self.filename_lbl)

        root.addWidget(header)

        # ── Canvas area ───────────────────────
        self._canvas_wrap = QWidget()
        self._canvas_wrap.setStyleSheet(f"background: {C_BG_DEEP};")
        self._cw_layout = QVBoxLayout(self._canvas_wrap)
        self._cw_layout.setContentsMargins(0, 0, 0, 0)

        self.placeholder = PlaceholderCanvas()
        self.image_canvas = ImageCanvas()
        self.image_canvas.setVisible(False)

        self._cw_layout.addWidget(self.placeholder)
        self._showing_image = False

        root.addWidget(self._canvas_wrap, stretch=1)

        # ── Info strip ────────────────────────
        info_strip = QWidget()
        info_strip.setFixedHeight(28)
        info_strip.setStyleSheet(f"""
            background: {C_BG_BASE};
            border-top: 1px solid {C_BORDER};
            border-left: 1px solid {C_BORDER};
        """)
        il = QHBoxLayout(info_strip)
        il.setContentsMargins(12, 0, 12, 0)
        il.setSpacing(16)

        def _info_lbl(text=""):
            lbl = QLabel(text)
            lbl.setFont(QFont(FONT_MONO, 11))
            lbl.setStyleSheet(f"color: {C_TEXT_LOW}; background: transparent;")
            return lbl

        self.info_dim  = _info_lbl()   # "1920 × 1080"
        self.info_ch   = _info_lbl()   # "RGB" / "Grayscale"
        self.info_size = _info_lbl()   # "2.4 MB"
        self.info_zoom = _info_lbl()   # "zoom 48%"

        for lbl in (self.info_dim, self.info_ch, self.info_size, self.info_zoom):
            il.addWidget(lbl)
        il.addStretch()

        root.addWidget(info_strip)

    # ──────────────────────────────────────────
    # Canvas switching
    # ──────────────────────────────────────────
    def _switch_to_image(self):
        if not self._showing_image:
            self._cw_layout.removeWidget(self.placeholder)
            self.placeholder.setVisible(False)
            self._cw_layout.addWidget(self.image_canvas)
            self.image_canvas.setVisible(True)
            self._showing_image = True

    def _switch_to_placeholder(self):
        if self._showing_image:
            self._cw_layout.removeWidget(self.image_canvas)
            self.image_canvas.setVisible(False)
            self._cw_layout.addWidget(self.placeholder)
            self.placeholder.setVisible(True)
            self._showing_image = False

    # ──────────────────────────────────────────
    # Public API (called by MainWindow)
    # ──────────────────────────────────────────
    def show_image(self, path: str):
        self._stop_animation()
        pix = load_qpixmap(path)
        if pix.isNull():
            self.clear()
            return

        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is not None and img.ndim > 2 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        self._cv_image   = img
        self._orig_pixmap = pix
        self._current_path = path

        self._switch_to_image()
        self.image_canvas.set_pixmap(pix)
        self._fade_in()
        self._update_meta(path, img)

    def clear(self):
        self._stop_animation()
        self._cv_image     = None
        self._orig_pixmap  = QPixmap()
        self._current_path = ""
        self._switch_to_placeholder()
        self.filename_lbl.setText("")
        for lbl in (self.info_dim, self.info_ch, self.info_size, self.info_zoom):
            lbl.setText("")

    def display_cv(self, img: np.ndarray):
        """Show a processed cv2 array without changing _cv_image / _orig_pixmap."""
        self._stop_animation()
        pix = _cv_to_qpixmap(img)
        if not pix.isNull():
            self._switch_to_image()
            self.image_canvas.set_pixmap(pix)

    def reset_to_original(self):
        self._stop_animation()
        if not self._orig_pixmap.isNull():
            self._switch_to_image()
            self.image_canvas.set_pixmap(self._orig_pixmap)

    def start_rotate(self):
        if self._cv_image is None:
            return
        self._anim_frame = 0
        self._anim_angle = 0.0
        self._anim_timer.start(50)

    @property
    def cv_image(self) -> np.ndarray | None:
        return self._cv_image

    # ──────────────────────────────────────────
    # Metadata display
    # ──────────────────────────────────────────
    def _update_meta(self, path: str, img):
        name = os.path.basename(path)
        # Truncate long names
        if len(name) > 28:
            name = name[:25] + "…"
        self.filename_lbl.setText(name)

        if img is not None:
            h, w  = img.shape[:2]
            nch   = 1 if img.ndim == 2 else img.shape[2]
            mode  = "Grayscale" if nch == 1 else ("RGBA" if nch == 4 else "RGB")
            self.info_dim.setText(f"{w} × {h}")
            self.info_ch.setText(mode)
        else:
            self.info_dim.setText("")
            self.info_ch.setText("")

        self.info_size.setText(_human_size(path))

        # Update zoom after canvas has been shown
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, self._update_zoom)

    def _update_zoom(self):
        ratio = self.image_canvas.zoom_ratio()
        if ratio is not None:
            self.info_zoom.setText(f"zoom {ratio * 100:.0f}%")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_zoom()

    # ──────────────────────────────────────────
    # Fade-in
    # ──────────────────────────────────────────
    def _fade_in(self):
        effect = QGraphicsOpacityEffect(self.image_canvas)
        self.image_canvas.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(250)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.finished.connect(lambda: self.image_canvas.setGraphicsEffect(None))
        anim.start()
        self._fade_anim = anim

    # ──────────────────────────────────────────
    # Rotation animation
    # ──────────────────────────────────────────
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
            self.reset_to_original()
            return

        h, w   = img.shape[:2]
        center = (w // 2, h // 2)
        scale  = 1.0 - 0.7 * (i / 49.0) if i < 50 else 0.3 + 0.7 * ((i - 50) / 49.0)
        self._anim_angle += 15.0
        M       = cv2.getRotationMatrix2D(center, self._anim_angle, scale)
        rotated = cv2.warpAffine(img, M, (w, h))
        pix     = _cv_to_qpixmap(rotated)
        if not pix.isNull():
            self.image_canvas.set_pixmap(pix)
        self._anim_frame += 1
