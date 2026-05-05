"""
processors/builtin.py — Built-in processors (shipped with the app).

All processors here are auto-registered via @register_processor.
They appear in the UI in the order they are defined in this file.

To disable one temporarily, comment out the @register_processor decorator.
To add more, see processors/base.py for instructions.
"""

import cv2
import numpy as np

from .base import ImageProcessor, register_processor


# ─────────────────────────────────────────────
# RGB Channel Split
# ─────────────────────────────────────────────
@register_processor
class RGBChannels(ImageProcessor):
    label    = "RGB Split"
    category = "Color Analysis"
    tooltip  = "Split image into R, G, B channels as a 2×2 grid"

    def apply(self, img: np.ndarray) -> np.ndarray:
        if img.ndim == 2:
            return img.copy()

        b, g, r = cv2.split(img)
        zeros   = np.zeros_like(b)
        r_img   = cv2.merge([zeros, zeros, r])
        g_img   = cv2.merge([zeros, g, zeros])
        b_img   = cv2.merge([b, zeros, zeros])

        h, w    = img.shape[:2]
        sh, sw  = h // 2, w // 2

        def _labeled(src, text):
            out = cv2.resize(src, (sw, sh))
            cv2.putText(out, text, (6, 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (255, 255, 255), 2, cv2.LINE_AA)
            return out

        top = np.hstack([_labeled(img,   "Original"), _labeled(r_img, "Red")])
        bot = np.hstack([_labeled(g_img, "Green"),    _labeled(b_img, "Blue")])
        return np.vstack([top, bot])


# ─────────────────────────────────────────────
# Grayscale
# ─────────────────────────────────────────────
@register_processor
class Grayscale(ImageProcessor):
    label    = "Grayscale"
    category = "Color Analysis"
    tooltip  = "Convert image to grayscale"

    def apply(self, img: np.ndarray) -> np.ndarray:
        if img.ndim == 2:
            return img.copy()
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


# ─────────────────────────────────────────────
# RGB to HSV
# ─────────────────────────────────────────────
@register_processor
class RGBtoHSV(ImageProcessor):
    label    = "RGB → HSV"
    category = "Color Analysis"
    tooltip  = "Convert image from RGB to HSV color space"

    def apply(self, img: np.ndarray) -> np.ndarray:
        if img.ndim == 2:
            return img.copy()
        return cv2.cvtColor(img, cv2.COLOR_BGR2HSV)


# ─────────────────────────────────────────────
# HSV to RGB
# ─────────────────────────────────────────────
@register_processor
class HSVtoRGB(ImageProcessor):
    label    = "HSV → RGB"
    category = "Color Analysis"
    tooltip  = "Convert image from HSV to RGB color space"

    def apply(self, img: np.ndarray) -> np.ndarray:
        if img.ndim == 2:
            return img.copy()
        return cv2.cvtColor(img, cv2.COLOR_HSV2BGR)


# ─────────────────────────────────────────────
# Center Crop
# ─────────────────────────────────────────────
@register_processor
class CenterCrop(ImageProcessor):
    label    = "Crop"
    category = "Transform"
    tooltip  = "Crop the center 50% of the image"

    def apply(self, img: np.ndarray) -> np.ndarray:
        h, w   = img.shape[:2]
        ch, cw = h // 2, w // 2
        y1, x1 = (h - ch) // 2, (w - cw) // 2
        return img[y1:y1 + ch, x1:x1 + cw].copy()


# ─────────────────────────────────────────────
# Flip Horizontal
# ─────────────────────────────────────────────
@register_processor
class FlipHorizontal(ImageProcessor):
    label    = "Flip"
    category = "Transform"
    tooltip  = "Flip image horizontally"

    def apply(self, img: np.ndarray) -> np.ndarray:
        return cv2.flip(img, 1)


# ─────────────────────────────────────────────
# Histogram Equalization
# ─────────────────────────────────────────────
@register_processor
class HistogramEqualize(ImageProcessor):
    label    = "Equalize"
    category = "Enhancement"
    tooltip  = "Apply histogram equalization (CLAHE on luminance)"

    def apply(self, img: np.ndarray) -> np.ndarray:
        if img.ndim == 2:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(img)
        lab   = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l     = clahe.apply(l)
        return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)


# ─────────────────────────────────────────────
# Rotate & Zoom  (animated — no static output)
# ─────────────────────────────────────────────
@register_processor
class RotateZoom(ImageProcessor):
    """
    Rotation + zoom-in/out animation.
    The UI detects `animated = True` and routes the button click
    to the panel's internal animation loop instead of calling .apply().
    """
    label    = "Rotate"
    category = "Transform"
    tooltip  = "Animated rotation + zoom effect"
    animated = True   # signals to PreviewPanel to start _anim_timer

    def apply(self, img: np.ndarray) -> np.ndarray:
        # Not called by UI — animation is driven by PreviewPanel._anim_step()
        return img.copy()

