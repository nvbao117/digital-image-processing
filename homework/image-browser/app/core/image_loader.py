import os
import sys

# Prevent cv2 from interfering with PyQt5
import cv2
cv2.setNumThreads(1)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

from .constants import SUPPORTED_EXTS, THUMB_SIZE


def list_images(folder):
    if not folder or not os.path.isdir(folder):
        return []
    files = []
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext in SUPPORTED_EXTS:
            files.append(path)
    files.sort(key=lambda p: os.path.basename(p).lower())
    return files


def load_qpixmap(path):
    pix = QPixmap(path)
    if not pix.isNull():
        return pix
    # Fallback for formats Qt cannot decode natively (some TIFF variants, etc.).
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        return QPixmap()
    if img.ndim == 2:
        h, w = img.shape
        qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8).copy()
    else:
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
            fmt = QImage.Format_RGBA8888
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            fmt = QImage.Format_RGB888
        h, w, ch = img.shape
        qimg = QImage(img.data, w, h, ch * w, fmt).copy()
    return QPixmap.fromImage(qimg)


def make_thumbnail(path, size=THUMB_SIZE):
    pix = load_qpixmap(path)
    if pix.isNull():
        return pix
    return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
