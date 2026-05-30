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
# Local Histogram Equalization (CLAHE)
# ─────────────────────────────────────────────
@register_processor
class CLAHEProcessor(ImageProcessor):
    label    = "Local Equalize"
    category = "Enhancement"
    tooltip  = "Contrast Limited Adaptive Histogram Equalization (Nâng cao chất lượng ảnh cục bộ)"

    params = {
        "clip_limit": {"label": "Clip Limit", "min": 1, "max": 40, "default": 20, "factor": 10.0},
        "grid_size": {"label": "Grid Size", "min": 2, "max": 16, "default": 8, "factor": 1.0}
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        clip = kwargs.get("clip_limit", 2.0)
        grid = int(kwargs.get("grid_size", 8))
        clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(grid, grid))
        
        if img.ndim == 2:
            return clahe.apply(img)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = clahe.apply(l)
        return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)


# ─────────────────────────────────────────────
# Global Histogram Equalization
# ─────────────────────────────────────────────
@register_processor
class GlobalHistogramEqualize(ImageProcessor):
    label    = "Global Equalize"
    category = "Enhancement"
    tooltip  = "Global Histogram Equalization (Cân bằng Histogram toàn cục)"

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        if img.ndim == 2:
            return cv2.equalizeHist(img)
        yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        yuv[:,:,0] = cv2.equalizeHist(yuv[:,:,0])
        return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)


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


# ─────────────────────────────────────────────
# Image Negative (Âm ảnh)
# ─────────────────────────────────────────────
@register_processor
class Negative(ImageProcessor):
    label    = "Negative"
    category = "Enhancement"
    tooltip  = "Image Negative (Âm ảnh)"

    def apply(self, img: np.ndarray) -> np.ndarray:
        L = 256  # Số lượng mức xám (2^8 cho ảnh 8-bit)
        return (L - 1) - img


# ─────────────────────────────────────────────
# Logarithmic Transformation (Biến đổi logarit)
# ─────────────────────────────────────────────
@register_processor
class LogTransform(ImageProcessor):
    label    = "Log Transform"
    category = "Enhancement"
    tooltip  = "Logarithmic Transformation (Biến đổi logarit)"
    
    params = {
        "c_multiplier": {"label": "C Multiplier", "min": 1, "max": 50, "default": 10, "factor": 10.0}
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        c_mul = kwargs.get("c_multiplier", 1.0)
        # Avoid log(0) and perform log transformation
        c = (255 / np.log(1 + np.max(img))) * c_mul
        log_img = c * (np.log(1 + img.astype(np.float32)))
        log_img = np.clip(log_img, 0, 255)
        return np.array(log_img, dtype=np.uint8)


# ─────────────────────────────────────────────
# Power-law (Gamma) Transformation (Biến đổi lũy thừa)
# ─────────────────────────────────────────────
@register_processor
class GammaTransform(ImageProcessor):
    label    = "Gamma Transform"
    category = "Enhancement"
    tooltip  = "Power-law / Gamma Transformation (Biến đổi lũy thừa)"
    
    params = {
        "gamma": {"label": "Gamma", "min": 1, "max": 50, "default": 5, "factor": 10.0},
        "c_multiplier": {"label": "C Multiplier", "min": 1, "max": 50, "default": 10, "factor": 10.0}
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        gamma = kwargs.get("gamma", 0.5)
        c = kwargs.get("c_multiplier", 1.0)
        # Power-law formula: c * r^gamma
        # Using Look-Up Table (LUT) for efficiency
        table = np.array([np.clip(c * (((i / 255.0) ** gamma) * 255), 0, 255)
                          for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(img, table)


# ─────────────────────────────────────────────
# Piecewise-Linear Transformation (Biến đổi tuyến tính từng phần)
# ─────────────────────────────────────────────
@register_processor
class ContrastStretching(ImageProcessor):
    label    = "Contrast Stretch"
    category = "Enhancement"
    tooltip  = "Piecewise-Linear / Contrast Stretching (Biến đổi tuyến tính từng phần)"
    
    params = {
        "min_val": {"label": "Min Val", "min": 0, "max": 255, "default": 0, "factor": 1.0},
        "max_val": {"label": "Max Val", "min": 0, "max": 255, "default": 255, "factor": 1.0}
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        min_in = kwargs.get("min_val", 0)
        max_in = kwargs.get("max_val", 255)
        
        if max_in <= min_in:
            return img.copy()
            
        stretched = (img.astype(np.float32) - min_in) * (255.0 / (max_in - min_in))
        stretched = np.clip(stretched, 0, 255)
        return np.array(stretched, dtype=np.uint8)

# ─────────────────────────────────────────────
# Mean Filter
# ─────────────────────────────────────────────
@register_processor
class MeanFilter(ImageProcessor):
    label    = "Mean Filter"
    category = "Filters"
    tooltip  = "Mean Filter (Lọc trung bình)"
    
    params = {
        "radius": {"label": "Radius", "min": 1, "max": 15, "default": 1, "factor": 1.0}
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        r = int(kwargs.get("radius", 1))
        k = r * 2 + 1
        return cv2.blur(img, (k, k))


# ─────────────────────────────────────────────
# Gaussian Filter
# ─────────────────────────────────────────────
@register_processor
class GaussianFilter(ImageProcessor):
    label    = "Gaussian Filter"
    category = "Filters"
    tooltip  = "Gaussian Filter (Lọc Gaussian)"
    
    params = {
        "radius": {"label": "Radius", "min": 1, "max": 15, "default": 2, "factor": 1.0},
        "sigma": {"label": "Sigma", "min": 0, "max": 50, "default": 0, "factor": 10.0}
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        r = int(kwargs.get("radius", 2))
        k = r * 2 + 1
        sigma = kwargs.get("sigma", 0.0)
        return cv2.GaussianBlur(img, (k, k), sigma)


# ─────────────────────────────────────────────
# Median Filter
# ─────────────────────────────────────────────
@register_processor
class MedianFilter(ImageProcessor):
    label    = "Median Filter"
    category = "Filters"
    tooltip  = "Median Filter (Lọc trung vị)"
    
    params = {
        "radius": {"label": "Radius", "min": 1, "max": 15, "default": 1, "factor": 1.0}
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        r = int(kwargs.get("radius", 1))
        k = r * 2 + 1
        return cv2.medianBlur(img, k)


# ─────────────────────────────────────────────
# Max Filter
# ─────────────────────────────────────────────
@register_processor
class MaxFilter(ImageProcessor):
    label    = "Max Filter"
    category = "Filters"
    tooltip  = "Max Filter (Lọc Max - Dilate)"
    
    params = {
        "radius": {"label": "Radius", "min": 1, "max": 15, "default": 1, "factor": 1.0}
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        r = int(kwargs.get("radius", 1))
        k = r * 2 + 1
        kernel = np.ones((k, k), np.uint8)
        return cv2.dilate(img, kernel)


# ─────────────────────────────────────────────
# Min Filter
# ─────────────────────────────────────────────
@register_processor
class MinFilter(ImageProcessor):
    label    = "Min Filter"
    category = "Filters"
    tooltip  = "Min Filter (Lọc Min - Erode)"
    
    params = {
        "radius": {"label": "Radius", "min": 1, "max": 15, "default": 1, "factor": 1.0}
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        r = int(kwargs.get("radius", 1))
        k = r * 2 + 1
        kernel = np.ones((k, k), np.uint8)
        return cv2.erode(img, kernel)


# ─────────────────────────────────────────────
# Dilation
# ─────────────────────────────────────────────
@register_processor
class Dilation(ImageProcessor):
    label    = "Dilation"
    category = "Morphology"
    tooltip  = "Morphological dilation using cv2.dilate"

    params = {
        "radius": {"label": "Radius", "min": 1, "max": 15, "default": 1, "factor": 1.0},
        "iterations": {"label": "Iterations", "min": 1, "max": 10, "default": 1, "factor": 1.0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        r = int(kwargs.get("radius", 1))
        iterations = int(kwargs.get("iterations", 1))
        k = r * 2 + 1
        kernel = np.ones((k, k), np.uint8)
        return cv2.dilate(img, kernel, iterations=iterations)


# ─────────────────────────────────────────────
# Erosion
# ─────────────────────────────────────────────
@register_processor
class Erosion(ImageProcessor):
    label    = "Erosion"
    category = "Morphology"
    tooltip  = "Morphological erosion using cv2.erode"

    params = {
        "radius": {"label": "Radius", "min": 1, "max": 15, "default": 1, "factor": 1.0},
        "iterations": {"label": "Iterations", "min": 1, "max": 10, "default": 1, "factor": 1.0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        r = int(kwargs.get("radius", 1))
        iterations = int(kwargs.get("iterations", 1))
        k = r * 2 + 1
        kernel = np.ones((k, k), np.uint8)
        return cv2.erode(img, kernel, iterations=iterations)


# ─────────────────────────────────────────────
# Opening
# ─────────────────────────────────────────────
@register_processor
class Opening(ImageProcessor):
    label    = "Opening"
    category = "Morphology"
    tooltip  = "Morphological opening: erosion followed by dilation"

    params = {
        "radius": {"label": "Radius", "min": 1, "max": 15, "default": 1, "factor": 1.0},
        "iterations": {"label": "Iterations", "min": 1, "max": 10, "default": 1, "factor": 1.0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        r = int(kwargs.get("radius", 1))
        iterations = int(kwargs.get("iterations", 1))
        k = r * 2 + 1
        kernel = np.ones((k, k), np.uint8)
        return cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel, iterations=iterations)


# ─────────────────────────────────────────────
# Closing
# ─────────────────────────────────────────────
@register_processor
class Closing(ImageProcessor):
    label    = "Closing"
    category = "Morphology"
    tooltip  = "Morphological closing: dilation followed by erosion"

    params = {
        "radius": {"label": "Radius", "min": 1, "max": 15, "default": 1, "factor": 1.0},
        "iterations": {"label": "Iterations", "min": 1, "max": 10, "default": 1, "factor": 1.0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        r = int(kwargs.get("radius", 1))
        iterations = int(kwargs.get("iterations", 1))
        k = r * 2 + 1
        kernel = np.ones((k, k), np.uint8)
        return cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=iterations)


def _binary_from_image(img: np.ndarray, threshold: float) -> np.ndarray:
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    return np.where(gray > threshold, 255, 0).astype(np.uint8)


def _seed_mask(shape: tuple[int, int], seed_x_percent: float, seed_y_percent: float) -> np.ndarray:
    h, w = shape
    x = int(round(np.clip(seed_x_percent, 0, 100) / 100.0 * (w - 1)))
    y = int(round(np.clip(seed_y_percent, 0, 100) / 100.0 * (h - 1)))
    seed = np.zeros((h, w), dtype=np.uint8)
    seed[y, x] = 255
    return seed


def _iterate_dilate_intersection(seed: np.ndarray, limit: np.ndarray, kernel: np.ndarray, max_iterations: int) -> np.ndarray:
    current = cv2.bitwise_and(seed, limit)
    for _ in range(max_iterations):
        grown = cv2.dilate(current, kernel)
        grown = cv2.bitwise_and(grown, limit)
        if np.array_equal(grown, current):
            break
        current = grown
    return current


def _zhang_suen_thinning(binary: np.ndarray, max_iterations: int) -> np.ndarray:
    img = (binary > 0).astype(np.uint8)
    max_iterations = max(1, int(max_iterations))

    for _ in range(max_iterations):
        before = img.copy()

        p = np.pad(img, 1, mode="constant")
        p2 = p[:-2, 1:-1]
        p3 = p[:-2, 2:]
        p4 = p[1:-1, 2:]
        p5 = p[2:, 2:]
        p6 = p[2:, 1:-1]
        p7 = p[2:, :-2]
        p8 = p[1:-1, :-2]
        p9 = p[:-2, :-2]

        neighbors = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
        transitions = (
            ((p2 == 0) & (p3 == 1)).astype(np.uint8) +
            ((p3 == 0) & (p4 == 1)).astype(np.uint8) +
            ((p4 == 0) & (p5 == 1)).astype(np.uint8) +
            ((p5 == 0) & (p6 == 1)).astype(np.uint8) +
            ((p6 == 0) & (p7 == 1)).astype(np.uint8) +
            ((p7 == 0) & (p8 == 1)).astype(np.uint8) +
            ((p8 == 0) & (p9 == 1)).astype(np.uint8) +
            ((p9 == 0) & (p2 == 1)).astype(np.uint8)
        )

        remove = (
            (img == 1) &
            (neighbors >= 2) & (neighbors <= 6) &
            (transitions == 1) &
            ((p2 * p4 * p6) == 0) &
            ((p4 * p6 * p8) == 0)
        )
        img[remove] = 0

        p = np.pad(img, 1, mode="constant")
        p2 = p[:-2, 1:-1]
        p3 = p[:-2, 2:]
        p4 = p[1:-1, 2:]
        p5 = p[2:, 2:]
        p6 = p[2:, 1:-1]
        p7 = p[2:, :-2]
        p8 = p[1:-1, :-2]
        p9 = p[:-2, :-2]

        neighbors = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
        transitions = (
            ((p2 == 0) & (p3 == 1)).astype(np.uint8) +
            ((p3 == 0) & (p4 == 1)).astype(np.uint8) +
            ((p4 == 0) & (p5 == 1)).astype(np.uint8) +
            ((p5 == 0) & (p6 == 1)).astype(np.uint8) +
            ((p6 == 0) & (p7 == 1)).astype(np.uint8) +
            ((p7 == 0) & (p8 == 1)).astype(np.uint8) +
            ((p8 == 0) & (p9 == 1)).astype(np.uint8) +
            ((p9 == 0) & (p2 == 1)).astype(np.uint8)
        )

        remove = (
            (img == 1) &
            (neighbors >= 2) & (neighbors <= 6) &
            (transitions == 1) &
            ((p2 * p4 * p8) == 0) &
            ((p2 * p6 * p8) == 0)
        )
        img[remove] = 0

        if np.array_equal(img, before):
            break

    return (img * 255).astype(np.uint8)


def _morphological_skeleton(binary: np.ndarray, kernel: np.ndarray, max_iterations: int) -> np.ndarray:
    current = binary.copy()
    skeleton = np.zeros_like(binary)
    max_iterations = max(1, int(max_iterations))

    for _ in range(max_iterations):
        opened = cv2.morphologyEx(current, cv2.MORPH_OPEN, kernel)
        residue = cv2.subtract(current, opened)
        skeleton = cv2.bitwise_or(skeleton, residue)
        current = cv2.erode(current, kernel)
        if cv2.countNonZero(current) == 0:
            break

    return skeleton


# ─────────────────────────────────────────────
# Boundary Extraction
# ─────────────────────────────────────────────
@register_processor
class BoundaryExtraction(ImageProcessor):
    label    = "Boundary Extraction"
    category = "Morphology"
    tooltip  = "Extract object boundary: A - erosion(A)"

    params = {
        "threshold": {"label": "Threshold", "min": 0, "max": 255, "default": 127, "factor": 1.0},
        "radius": {"label": "Radius", "min": 1, "max": 15, "default": 1, "factor": 1.0},
        "iterations": {"label": "Iterations", "min": 1, "max": 10, "default": 1, "factor": 1.0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        threshold = kwargs.get("threshold", 127)
        r = int(kwargs.get("radius", 1))
        iterations = int(kwargs.get("iterations", 1))
        k = r * 2 + 1
        kernel = np.ones((k, k), np.uint8)

        binary = _binary_from_image(img, threshold)
        eroded = cv2.erode(binary, kernel, iterations=iterations)
        return cv2.subtract(binary, eroded)


# ─────────────────────────────────────────────
# Region Filling
# ─────────────────────────────────────────────
@register_processor
class RegionFilling(ImageProcessor):
    label    = "Region Filling"
    category = "Morphology"
    tooltip  = "Fill a closed region from a seed point: Xk = dilate(Xk-1) intersect Ac"

    params = {
        "threshold": {"label": "Threshold", "min": 0, "max": 255, "default": 127, "factor": 1.0},
        "seed_x": {"label": "Seed X (%)", "min": 0, "max": 100, "default": 50, "factor": 1.0},
        "seed_y": {"label": "Seed Y (%)", "min": 0, "max": 100, "default": 50, "factor": 1.0},
        "radius": {"label": "Radius", "min": 1, "max": 5, "default": 1, "factor": 1.0},
        "max_iterations": {"label": "Max Iter", "min": 10, "max": 1000, "default": 200, "factor": 1.0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        threshold = kwargs.get("threshold", 127)
        seed_x = kwargs.get("seed_x", 50)
        seed_y = kwargs.get("seed_y", 50)
        r = int(kwargs.get("radius", 1))
        max_iterations = int(kwargs.get("max_iterations", 200))
        k = r * 2 + 1
        kernel = np.ones((k, k), np.uint8)

        boundary = _binary_from_image(img, threshold)
        allowed = cv2.bitwise_not(boundary)
        seed = _seed_mask(boundary.shape, seed_x, seed_y)
        filled = _iterate_dilate_intersection(seed, allowed, kernel, max_iterations)
        return cv2.bitwise_or(boundary, filled)


# ─────────────────────────────────────────────
# Connected Component Extraction
# ─────────────────────────────────────────────
@register_processor
class ConnectedComponentExtraction(ImageProcessor):
    label    = "Connected Component"
    category = "Morphology"
    tooltip  = "Extract connected component from a seed point: Xk = dilate(Xk-1) intersect A"

    params = {
        "threshold": {"label": "Threshold", "min": 0, "max": 255, "default": 127, "factor": 1.0},
        "seed_x": {"label": "Seed X (%)", "min": 0, "max": 100, "default": 50, "factor": 1.0},
        "seed_y": {"label": "Seed Y (%)", "min": 0, "max": 100, "default": 50, "factor": 1.0},
        "radius": {"label": "Radius", "min": 1, "max": 5, "default": 1, "factor": 1.0},
        "max_iterations": {"label": "Max Iter", "min": 10, "max": 1000, "default": 200, "factor": 1.0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        threshold = kwargs.get("threshold", 127)
        seed_x = kwargs.get("seed_x", 50)
        seed_y = kwargs.get("seed_y", 50)
        r = int(kwargs.get("radius", 1))
        max_iterations = int(kwargs.get("max_iterations", 200))
        k = r * 2 + 1
        kernel = np.ones((k, k), np.uint8)

        binary = _binary_from_image(img, threshold)
        seed = _seed_mask(binary.shape, seed_x, seed_y)
        return _iterate_dilate_intersection(seed, binary, kernel, max_iterations)


# ─────────────────────────────────────────────
# Convex Hull
# ─────────────────────────────────────────────
@register_processor
class ConvexHullProcessor(ImageProcessor):
    label    = "Convex Hull"
    category = "Morphology"
    tooltip  = "Fill each object's convex hull"

    params = {
        "threshold": {"label": "Threshold", "min": 0, "max": 255, "default": 127, "factor": 1.0},
        "mode": {"label": "Mode", "type": "choice", "choices": ["External", "All Contours"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        threshold = kwargs.get("threshold", 127)
        mode = int(kwargs.get("mode", 0))
        binary = _binary_from_image(img, threshold)
        contour_mode = cv2.RETR_EXTERNAL if mode == 0 else cv2.RETR_LIST
        contours, _ = cv2.findContours(binary, contour_mode, cv2.CHAIN_APPROX_SIMPLE)

        out = np.zeros_like(binary)
        for contour in contours:
            if len(contour) >= 3:
                hull = cv2.convexHull(contour)
                cv2.drawContours(out, [hull], -1, 255, thickness=-1)
        return out


# ─────────────────────────────────────────────
# Thinning
# ─────────────────────────────────────────────
@register_processor
class Thinning(ImageProcessor):
    label    = "Thinning"
    category = "Morphology"
    tooltip  = "Thin binary objects using the Zhang-Suen algorithm"

    params = {
        "threshold": {"label": "Threshold", "min": 0, "max": 255, "default": 127, "factor": 1.0},
        "max_iterations": {"label": "Max Iter", "min": 1, "max": 500, "default": 100, "factor": 1.0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        threshold = kwargs.get("threshold", 127)
        max_iterations = int(kwargs.get("max_iterations", 100))
        binary = _binary_from_image(img, threshold)
        return _zhang_suen_thinning(binary, max_iterations)


# ─────────────────────────────────────────────
# Thickening
# ─────────────────────────────────────────────
@register_processor
class Thickening(ImageProcessor):
    label    = "Thickening"
    category = "Morphology"
    tooltip  = "Thicken binary objects using the dual of thinning"

    params = {
        "threshold": {"label": "Threshold", "min": 0, "max": 255, "default": 127, "factor": 1.0},
        "max_iterations": {"label": "Max Iter", "min": 1, "max": 200, "default": 20, "factor": 1.0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        threshold = kwargs.get("threshold", 127)
        max_iterations = int(kwargs.get("max_iterations", 20))
        binary = _binary_from_image(img, threshold)
        background = cv2.bitwise_not(binary)
        thinned_background = _zhang_suen_thinning(background, max_iterations)
        return cv2.bitwise_not(thinned_background)


# ─────────────────────────────────────────────
# Skeleton
# ─────────────────────────────────────────────
@register_processor
class Skeleton(ImageProcessor):
    label    = "Skeleton"
    category = "Morphology"
    tooltip  = "Extract morphological skeleton by repeated erosion and opening"

    params = {
        "threshold": {"label": "Threshold", "min": 0, "max": 255, "default": 127, "factor": 1.0},
        "radius": {"label": "Radius", "min": 1, "max": 5, "default": 1, "factor": 1.0},
        "max_iterations": {"label": "Max Iter", "min": 1, "max": 500, "default": 200, "factor": 1.0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        threshold = kwargs.get("threshold", 127)
        r = int(kwargs.get("radius", 1))
        max_iterations = int(kwargs.get("max_iterations", 200))
        k = r * 2 + 1
        kernel = np.ones((k, k), np.uint8)
        binary = _binary_from_image(img, threshold)
        return _morphological_skeleton(binary, kernel, max_iterations)


# ─────────────────────────────────────────────
# Hit-or-Miss
# ─────────────────────────────────────────────
@register_processor
class HitOrMiss(ImageProcessor):
    label    = "Hit-or-Miss"
    category = "Morphology"
    tooltip  = "Detect exact binary patterns using hit-or-miss transform"

    params = {
        "threshold": {"label": "Threshold", "min": 0, "max": 255, "default": 127, "factor": 1.0},
        "polarity": {"label": "Polarity", "type": "choice", "choices": ["White Objects", "Black Objects"], "default": 0},
        "pattern": {
            "label": "Pattern",
            "type": "choice",
            "choices": [
                "Isolated Point",
                "Endpoint North",
                "Endpoint South",
                "Endpoint East",
                "Endpoint West",
                "Corner NE",
                "Corner NW",
                "Cross Center",
                "T Junction",
            ],
            "default": 0,
        },
    }

    _KERNELS = [
        np.array([[-1, -1, -1],
                  [-1,  1, -1],
                  [-1, -1, -1]], dtype=np.int8),
        np.array([[-1, -1, -1],
                  [-1,  1, -1],
                  [ 0,  1,  0]], dtype=np.int8),
        np.array([[ 0,  1,  0],
                  [-1,  1, -1],
                  [-1, -1, -1]], dtype=np.int8),
        np.array([[ 0, -1, -1],
                  [ 1,  1, -1],
                  [ 0, -1, -1]], dtype=np.int8),
        np.array([[-1, -1,  0],
                  [-1,  1,  1],
                  [-1, -1,  0]], dtype=np.int8),
        np.array([[-1,  1,  0],
                  [-1,  1,  1],
                  [-1, -1, -1]], dtype=np.int8),
        np.array([[ 0,  1, -1],
                  [ 1,  1, -1],
                  [-1, -1, -1]], dtype=np.int8),
        np.array([[ 0,  1,  0],
                  [ 1,  1,  1],
                  [ 0,  1,  0]], dtype=np.int8),
        np.array([[ 1,  1,  1],
                  [-1,  1, -1],
                  [ 0,  1,  0]], dtype=np.int8),
    ]

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        threshold = kwargs.get("threshold", 127)
        polarity = int(kwargs.get("polarity", 0))
        pattern = int(kwargs.get("pattern", 0))

        binary = _binary_from_image(img, threshold)
        if polarity == 1:
            binary = cv2.bitwise_not(binary)

        src = (binary > 0).astype(np.uint8)
        kernel = self._KERNELS[np.clip(pattern, 0, len(self._KERNELS) - 1)]
        result = cv2.morphologyEx(src, cv2.MORPH_HITMISS, kernel)
        return (result * 255).astype(np.uint8)


# ─────────────────────────────────────────────
# Binary Threshold Segmentation
# ─────────────────────────────────────────────
@register_processor
class BinaryThresholdSegmentation(ImageProcessor):
    label    = "Binary Threshold"
    category = "Segmentation"
    tooltip  = "Segment image by a fixed grayscale threshold"

    params = {
        "threshold": {"label": "Threshold", "min": 0, "max": 255, "default": 127, "factor": 1.0},
        "mode": {"label": "Mode", "type": "choice", "choices": ["Object Bright", "Object Dark"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        threshold = kwargs.get("threshold", 127)
        mode = int(kwargs.get("mode", 0))
        binary = _binary_from_image(img, threshold)
        if mode == 1:
            binary = cv2.bitwise_not(binary)
        return binary


# ─────────────────────────────────────────────
# Otsu Threshold Segmentation
# ─────────────────────────────────────────────
@register_processor
class OtsuThresholdSegmentation(ImageProcessor):
    label    = "Otsu Threshold"
    category = "Segmentation"
    tooltip  = "Automatically segment image using Otsu thresholding"

    params = {
        "mode": {"label": "Mode", "type": "choice", "choices": ["Object Bright", "Object Dark"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        mode = int(kwargs.get("mode", 0))
        if img.ndim == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        threshold_type = cv2.THRESH_BINARY_INV if mode == 1 else cv2.THRESH_BINARY
        _, binary = cv2.threshold(gray, 0, 255, threshold_type | cv2.THRESH_OTSU)
        return binary


# ─────────────────────────────────────────────
# Adaptive Threshold Segmentation
# ─────────────────────────────────────────────
@register_processor
class AdaptiveThresholdSegmentation(ImageProcessor):
    label    = "Adaptive Threshold"
    category = "Segmentation"
    tooltip  = "Segment image using local adaptive thresholding"

    params = {
        "block_size": {"label": "Block Size", "min": 3, "max": 101, "default": 21, "factor": 1.0},
        "c_value": {"label": "C", "min": 0, "max": 30, "default": 5, "factor": 1.0},
        "method": {"label": "Method", "type": "choice", "choices": ["Mean", "Gaussian"], "default": 1},
        "mode": {"label": "Mode", "type": "choice", "choices": ["Object Bright", "Object Dark"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        block_size = int(kwargs.get("block_size", 21))
        c_value = kwargs.get("c_value", 5)
        method = int(kwargs.get("method", 1))
        mode = int(kwargs.get("mode", 0))

        if img.ndim == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        block_size = max(3, block_size)
        if block_size % 2 == 0:
            block_size += 1

        adaptive_method = cv2.ADAPTIVE_THRESH_MEAN_C if method == 0 else cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        threshold_type = cv2.THRESH_BINARY_INV if mode == 1 else cv2.THRESH_BINARY
        return cv2.adaptiveThreshold(gray, 255, adaptive_method, threshold_type, block_size, c_value)


# ─────────────────────────────────────────────
# K-Means Segmentation
# ─────────────────────────────────────────────
@register_processor
class KMeansSegmentation(ImageProcessor):
    label    = "K-Means Segmentation"
    category = "Segmentation"
    tooltip  = "Segment image into K color/intensity clusters"

    params = {
        "clusters": {"label": "Clusters K", "min": 2, "max": 8, "default": 3, "factor": 1.0},
        "attempts": {"label": "Attempts", "min": 1, "max": 10, "default": 3, "factor": 1.0},
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Segmented Color", "Label Mask"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        k = max(2, int(kwargs.get("clusters", 3)))
        attempts = max(1, int(kwargs.get("attempts", 3)))
        display_mode = int(kwargs.get("display_mode", 0))

        if img.ndim == 2:
            samples = img.reshape((-1, 1)).astype(np.float32)
            shape = img.shape
        else:
            samples = img.reshape((-1, 3)).astype(np.float32)
            shape = img.shape[:2]

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(samples, k, None, criteria, attempts, cv2.KMEANS_PP_CENTERS)
        labels = labels.reshape(shape)

        if display_mode == 1:
            scale = 255.0 / max(1, k - 1)
            return np.clip(labels * scale, 0, 255).astype(np.uint8)

        centers = np.clip(centers, 0, 255).astype(np.uint8)
        segmented = centers[labels.reshape(-1)].reshape(img.shape)
        return segmented


# ─────────────────────────────────────────────
# Watershed Segmentation
# ─────────────────────────────────────────────
@register_processor
class WatershedSegmentation(ImageProcessor):
    label    = "Watershed"
    category = "Segmentation"
    tooltip  = "Separate touching bright objects using watershed markers"

    params = {
        "threshold": {"label": "Threshold", "min": 0, "max": 255, "default": 127, "factor": 1.0},
        "radius": {"label": "Radius", "min": 1, "max": 5, "default": 1, "factor": 1.0},
        "distance_ratio": {"label": "Dist Ratio", "min": 1, "max": 90, "default": 40, "factor": 100.0},
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Boundary Overlay", "Label Mask"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        threshold = kwargs.get("threshold", 127)
        r = int(kwargs.get("radius", 1))
        distance_ratio = kwargs.get("distance_ratio", 0.4)
        display_mode = int(kwargs.get("display_mode", 0))

        binary = _binary_from_image(img, threshold)
        k = r * 2 + 1
        kernel = np.ones((k, k), np.uint8)
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
        sure_bg = cv2.dilate(opened, kernel, iterations=3)
        dist = cv2.distanceTransform(opened, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist, distance_ratio * dist.max(), 255, 0)
        sure_fg = sure_fg.astype(np.uint8)
        unknown = cv2.subtract(sure_bg, sure_fg)

        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0

        if img.ndim == 2:
            color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            color = img.copy()

        markers = cv2.watershed(color, markers.astype(np.int32))

        if display_mode == 1:
            labels = markers.astype(np.float32)
            labels[labels < 0] = 0
            if labels.max() > 0:
                labels = labels * (255.0 / labels.max())
            return labels.astype(np.uint8)

        out = color.copy()
        out[markers == -1] = [0, 0, 255]
        return out


# ─────────────────────────────────────────────
# Midpoint Filter
# ─────────────────────────────────────────────
@register_processor
class MidpointFilter(ImageProcessor):
    label    = "Midpoint Filter"
    category = "Filters"
    tooltip  = "Midpoint Filter (Lọc Midpoint: (Max + Min) / 2)"
    
    params = {
        "radius": {"label": "Radius", "min": 1, "max": 15, "default": 1, "factor": 1.0}
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        r = int(kwargs.get("radius", 1))
        k = r * 2 + 1
        kernel = np.ones((k, k), np.uint8)
        img_max = cv2.dilate(img, kernel).astype(np.float32)
        img_min = cv2.erode(img, kernel).astype(np.float32)
        midpoint = (img_max + img_min) / 2.0
        return np.clip(midpoint, 0, 255).astype(np.uint8)


# ─────────────────────────────────────────────
# Custom Convolution (From Scratch)
# ─────────────────────────────────────────────
def custom_convolve2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """
    Perform 2D convolution from scratch using array slicing.
    """
    k_h, k_w = kernel.shape
    pad_top = k_h // 2
    pad_bottom = k_h - 1 - pad_top
    pad_left = k_w // 2
    pad_right = k_w - 1 - pad_left
    
    padded = np.pad(image, ((pad_top, pad_bottom), (pad_left, pad_right)), mode='edge')
    output = np.zeros_like(image, dtype=np.float32)
    
    for i in range(k_h):
        for j in range(k_w):
            output += padded[i:i+image.shape[0], j:j+image.shape[1]] * kernel[i, j]
            
    return output


def _gray_uint8(img: np.ndarray) -> np.ndarray:
    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img.copy()


def _normalize_response(response: np.ndarray) -> np.ndarray:
    response = np.abs(response).astype(np.float32)
    max_val = response.max()
    if max_val > 0:
        response = response * (255.0 / max_val)
    return np.clip(response, 0, 255).astype(np.uint8)


# ─────────────────────────────────────────────
# Point Detection
# ─────────────────────────────────────────────
@register_processor
class PointDetection(ImageProcessor):
    label    = "Point Detection"
    category = "Detection"
    tooltip  = "Detect isolated points using a Laplacian point mask"

    params = {
        "threshold": {"label": "Threshold", "min": 0, "max": 255, "default": 80, "factor": 1.0},
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Binary Points", "Response"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        threshold = kwargs.get("threshold", 80)
        display_mode = int(kwargs.get("display_mode", 0))
        gray = _gray_uint8(img).astype(np.float32)
        kernel = np.array([
            [-1, -1, -1],
            [-1,  8, -1],
            [-1, -1, -1],
        ], dtype=np.float32)

        response = _normalize_response(custom_convolve2d(gray, kernel))
        if display_mode == 1:
            return response
        return np.where(response >= threshold, 255, 0).astype(np.uint8)


# ─────────────────────────────────────────────
# Line Detection
# ─────────────────────────────────────────────
@register_processor
class LineDetection(ImageProcessor):
    label    = "Line Detection"
    category = "Detection"
    tooltip  = "Detect horizontal, vertical, or diagonal lines using line masks"

    params = {
        "direction": {
            "label": "Direction",
            "type": "choice",
            "choices": ["Horizontal", "Vertical", "+45 Degree", "-45 Degree", "Max Response"],
            "default": 4,
        },
        "threshold": {"label": "Threshold", "min": 0, "max": 255, "default": 80, "factor": 1.0},
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Binary Lines", "Response"], "default": 0},
    }

    _KERNELS = [
        np.array([[-1, -1, -1],
                  [ 2,  2,  2],
                  [-1, -1, -1]], dtype=np.float32),
        np.array([[-1,  2, -1],
                  [-1,  2, -1],
                  [-1,  2, -1]], dtype=np.float32),
        np.array([[-1, -1,  2],
                  [-1,  2, -1],
                  [ 2, -1, -1]], dtype=np.float32),
        np.array([[ 2, -1, -1],
                  [-1,  2, -1],
                  [-1, -1,  2]], dtype=np.float32),
    ]

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        direction = int(kwargs.get("direction", 4))
        threshold = kwargs.get("threshold", 80)
        display_mode = int(kwargs.get("display_mode", 0))
        gray = _gray_uint8(img).astype(np.float32)

        if direction == 4:
            responses = [np.abs(custom_convolve2d(gray, kernel)) for kernel in self._KERNELS]
            response = np.maximum.reduce(responses)
            response = _normalize_response(response)
        else:
            kernel = self._KERNELS[np.clip(direction, 0, len(self._KERNELS) - 1)]
            response = _normalize_response(custom_convolve2d(gray, kernel))

        if display_mode == 1:
            return response
        return np.where(response >= threshold, 255, 0).astype(np.uint8)


# ─────────────────────────────────────────────
# Edge Detection
# ─────────────────────────────────────────────
@register_processor
class EdgeDetection(ImageProcessor):
    label    = "Edge Detection"
    category = "Detection"
    tooltip  = "Detect edges using Sobel, Prewitt, Roberts, Laplacian, or Canny"

    params = {
        "operator": {
            "label": "Operator",
            "type": "choice",
            "choices": ["Sobel", "Prewitt", "Roberts", "Laplacian", "Canny"],
            "default": 0,
        },
        "low_threshold": {"label": "Low Thresh", "min": 0, "max": 255, "default": 50, "factor": 1.0},
        "high_threshold": {"label": "High Thresh", "min": 0, "max": 255, "default": 120, "factor": 1.0},
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Binary Edges", "Response"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        operator = int(kwargs.get("operator", 0))
        low_threshold = kwargs.get("low_threshold", 50)
        high_threshold = kwargs.get("high_threshold", 120)
        display_mode = int(kwargs.get("display_mode", 0))
        gray = _gray_uint8(img)

        if operator == 4:
            low = int(min(low_threshold, high_threshold))
            high = int(max(low_threshold, high_threshold))
            return cv2.Canny(gray, low, high)

        gray_f = gray.astype(np.float32)
        if operator == 0:
            kx = np.array([[-1,  0,  1], [-2,  0,  2], [-1,  0,  1]], dtype=np.float32)
            ky = np.array([[-1, -2, -1], [ 0,  0,  0], [ 1,  2,  1]], dtype=np.float32)
            gx = custom_convolve2d(gray_f, kx)
            gy = custom_convolve2d(gray_f, ky)
            response = _normalize_response(np.sqrt(gx**2 + gy**2))
        elif operator == 1:
            kx = np.array([[-1,  0,  1], [-1,  0,  1], [-1,  0,  1]], dtype=np.float32)
            ky = np.array([[-1, -1, -1], [ 0,  0,  0], [ 1,  1,  1]], dtype=np.float32)
            gx = custom_convolve2d(gray_f, kx)
            gy = custom_convolve2d(gray_f, ky)
            response = _normalize_response(np.sqrt(gx**2 + gy**2))
        elif operator == 2:
            kx = np.array([[ 1,  0],
                           [ 0, -1]], dtype=np.float32)
            ky = np.array([[ 0,  1],
                           [-1,  0]], dtype=np.float32)
            gx = custom_convolve2d(gray_f, kx)
            gy = custom_convolve2d(gray_f, ky)
            response = _normalize_response(np.sqrt(gx**2 + gy**2))
        else:
            kernel = np.array([[-1, -1, -1],
                               [-1,  8, -1],
                               [-1, -1, -1]], dtype=np.float32)
            response = _normalize_response(custom_convolve2d(gray_f, kernel))

        if display_mode == 1:
            return response
        return np.where(response >= high_threshold, 255, 0).astype(np.uint8)


# ─────────────────────────────────────────────
# Laplace Enhancement (2nd Order Derivative)
# ─────────────────────────────────────────────
@register_processor
class LaplaceEnhancement(ImageProcessor):
    label    = "Laplace Sharpen"
    category = "Sharpening"
    tooltip  = "Cải thiện ảnh bằng đạo hàm cấp 2 (Laplace) - from scratch"
    
    params = {
        "kernel_type": {
            "label": "Kernel Type",
            "type": "choice",
            "choices": ["4-neighbor", "8-neighbor"],
            "default": 1,
        },
        "scale": {"label": "Scale (c)", "min": 0, "max": 50, "default": 10, "factor": 10.0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        kernel_type = int(kwargs.get("kernel_type", 1))
        scale = kwargs.get("scale", 1.0)
        
        if kernel_type == 0:
            kernel = np.array([
                [ 0, -1,  0],
                [-1,  4, -1],
                [ 0, -1,  0]
            ], dtype=np.float32)
        else:
            kernel = np.array([
                [-1, -1, -1],
                [-1,  8, -1],
                [-1, -1, -1]
            ], dtype=np.float32)
            
        def process_channel(c):
            laplacian = custom_convolve2d(c, kernel)
            enhanced = c.astype(np.float32) + scale * laplacian
            return np.clip(enhanced, 0, 255).astype(np.uint8)
            
        if img.ndim == 2:
            return process_channel(img)
        else:
            b, g, r = cv2.split(img)
            return cv2.merge([process_channel(b), process_channel(g), process_channel(r)])


# ─────────────────────────────────────────────
# First-Order Enhancement (Sobel, Prewitt, Robert)
# ─────────────────────────────────────────────
@register_processor
class GradientEnhancement(ImageProcessor):
    label    = "Gradient Sharpen"
    category = "Sharpening"
    tooltip  = "Cải thiện ảnh bằng đạo hàm cấp 1 (Sobel/Prewitt/Robert) - from scratch"
    
    params = {
        "operator": {
            "label": "Operator",
            "type": "choice",
            "choices": ["Sobel", "Prewitt", "Robert"],
            "default": 0,
        },
        "scale": {"label": "Scale (c)", "min": 0, "max": 50, "default": 10, "factor": 10.0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        op = int(kwargs.get("operator", 0))
        scale = kwargs.get("scale", 1.0)
        
        if op == 0:  # Sobel
            kx = np.array([[-1,  0,  1], [-2,  0,  2], [-1,  0,  1]], dtype=np.float32)
            ky = np.array([[-1, -2, -1], [ 0,  0,  0], [ 1,  2,  1]], dtype=np.float32)
        elif op == 1:  # Prewitt
            kx = np.array([[-1,  0,  1], [-1,  0,  1], [-1,  0,  1]], dtype=np.float32)
            ky = np.array([[-1, -1, -1], [ 0,  0,  0], [ 1,  1,  1]], dtype=np.float32)
        else:  # Robert (padded to 3x3)
            kx = np.array([[ 0,  0,  0], [ 0,  1,  0], [ 0,  0, -1]], dtype=np.float32)
            ky = np.array([[ 0,  0,  0], [ 0,  0,  1], [ 0, -1,  0]], dtype=np.float32)
            
        def process_channel(c):
            gx = custom_convolve2d(c, kx)
            gy = custom_convolve2d(c, ky)
            magnitude = np.sqrt(gx**2 + gy**2)
            enhanced = c.astype(np.float32) + scale * magnitude
            return np.clip(enhanced, 0, 255).astype(np.uint8)
            
        if img.ndim == 2:
            return process_channel(img)
        else:
            b, g, r = cv2.split(img)
            return cv2.merge([process_channel(b), process_channel(g), process_channel(r)])


# ─────────────────────────────────────────────
# Custom Kernel Filter (User-defined)
# ─────────────────────────────────────────────
@register_processor
class CustomKernelFilter(ImageProcessor):
    label    = "Custom Kernel"
    category = "Sharpening"
    tooltip  = "Áp dụng kernel tự nhập vào ảnh bằng tích chập from scratch"

    # No params dict — uses its own UI widget via the special flag
    custom_ui = True

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        kernel_str = kwargs.get("kernel", "0 0 0\n0 1 0\n0 0 0")
        try:
            rows = [list(map(float, r.split())) for r in kernel_str.strip().splitlines() if r.strip()]
            kernel = np.array(rows, dtype=np.float32)
            if kernel.ndim != 2 or kernel.shape[0] == 0:
                raise ValueError("Invalid kernel")
        except Exception:
            return img  # return unchanged if kernel is invalid

        def process_channel(c):
            result = custom_convolve2d(c, kernel)
            return np.clip(result, 0, 255).astype(np.uint8)

        if img.ndim == 2:
            return process_channel(img)
        else:
            b, g, r = cv2.split(img)
            return cv2.merge([process_channel(b), process_channel(g), process_channel(r)])


# ═══════════════════════════════════════════════════════════
#  FREQUENCY DOMAIN FILTERS
# ═══════════════════════════════════════════════════════════

def _to_gray_float(img: np.ndarray) -> np.ndarray:
    """Convert BGR/Gray image to float32 grayscale [0,255]."""
    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    return img.astype(np.float32)


def _apply_freq_filter_multichannel(img: np.ndarray, mask: np.ndarray, display_mode: int = 0) -> np.ndarray:
    """
    Apply a frequency-domain mask (same size as image) to every channel.
    mask: 2-D float array in [0, 1].
    display_mode: 0 for Result Only, 1 for Grid View.
    Returns uint8 output with same number of channels as input.
    """
    def _filter_channel(ch: np.ndarray) -> np.ndarray:
        f = np.fft.fft2(ch.astype(np.float32))
        fshift = np.fft.fftshift(f)
        filtered = fshift * mask
        f_ishift = np.fft.ifftshift(filtered)
        img_back = np.fft.ifft2(f_ishift)
        img_back = np.abs(img_back)
        return np.clip(img_back, 0, 255).astype(np.uint8)

    if img.ndim == 2:
        result = _filter_channel(img)
    else:
        channels = cv2.split(img)
        result = cv2.merge([_filter_channel(c) for c in channels])
        
    if display_mode == 0:
        return result

    # Grid View
    h, w = img.shape[:2]
    gray = _to_gray_float(img)
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    mag = 20 * np.log(np.abs(fshift) + 1)
    mag = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    mask_vis = (mask * 255).astype(np.uint8)
    
    is_color = (img.ndim == 3)
    def _to_bgr(arr):
        if is_color and arr.ndim == 2:
            return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
        return arr

    mag_bgr = _to_bgr(mag)
    mask_bgr = _to_bgr(mask_vis)
    orig_bgr = _to_bgr(img)
    res_bgr = _to_bgr(result)

    sh, sw = max(1, h // 2), max(1, w // 2)

    def _labeled(src, text):
        out = cv2.resize(src, (sw, sh))
        font_scale = max(0.5, sw / 500.0)
        cv2.putText(out, text, (10, int(30 * font_scale)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), max(1, int(2*font_scale)), cv2.LINE_AA)
        return out

    top = np.hstack([_labeled(orig_bgr, "Original"), _labeled(mag_bgr, "Input Spectrum")])
    bot = np.hstack([_labeled(mask_bgr, "Filter Mask"), _labeled(res_bgr, "Result")])
    return np.vstack([top, bot])


def _distance_map(rows: int, cols: int) -> np.ndarray:
    """Return distance-from-center 2-D array of shape (rows, cols)."""
    u = np.fft.fftfreq(rows) * rows
    v = np.fft.fftfreq(cols) * cols
    u = np.fft.fftshift(u)
    v = np.fft.fftshift(v)
    V, U = np.meshgrid(v, u)
    return np.sqrt(U**2 + V**2)


# ─────────────────────────────────────────────
# Ideal Low-pass Filter  (Lọc thông thấp lý tưởng)
# ─────────────────────────────────────────────
@register_processor
class IdealLowPass(ImageProcessor):
    label    = "Ideal Low-pass"
    category = "Frequency Domain"
    tooltip  = "Lọc thông thấp lý tưởng — chặn tất cả tần số cao hơn ngưỡng D0"

    params = {
        "cutoff": {
            "label": "Cutoff D0",
            "min": 1, "max": 200, "default": 30, "factor": 1.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        D0 = max(1.0, kwargs.get("cutoff", 30))
        h, w = img.shape[:2]
        D = _distance_map(h, w)
        mask = (D <= D0).astype(np.float32)
        display_mode = int(kwargs.get("display_mode", 0))
        return _apply_freq_filter_multichannel(img, mask, display_mode)


# ─────────────────────────────────────────────
# Ideal High-pass Filter  (Lọc thông cao lý tưởng)
# ─────────────────────────────────────────────
@register_processor
class IdealHighPass(ImageProcessor):
    label    = "Ideal High-pass"
    category = "Frequency Domain"
    tooltip  = "Lọc thông cao lý tưởng — chặn tất cả tần số thấp hơn ngưỡng D0"

    params = {
        "cutoff": {
            "label": "Cutoff D0",
            "min": 1, "max": 200, "default": 30, "factor": 1.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        D0 = max(1.0, kwargs.get("cutoff", 30))
        h, w = img.shape[:2]
        D = _distance_map(h, w)
        mask = (D > D0).astype(np.float32)
        display_mode = int(kwargs.get("display_mode", 0))
        return _apply_freq_filter_multichannel(img, mask, display_mode)


# ─────────────────────────────────────────────
# Gaussian Low-pass Filter  (Lọc Gaussian thông thấp)
# ─────────────────────────────────────────────
@register_processor
class GaussianLowPass(ImageProcessor):
    label    = "Gaussian Low-pass"
    category = "Frequency Domain"
    tooltip  = "Lọc Gaussian thông thấp trong miền tần số — làm mờ mượt mà"

    params = {
        "sigma": {
            "label": "Sigma D0",
            "min": 1, "max": 200, "default": 30, "factor": 1.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        D0 = max(1.0, kwargs.get("sigma", 30))
        h, w = img.shape[:2]
        D = _distance_map(h, w)
        mask = np.exp(-(D**2) / (2 * D0**2))
        display_mode = int(kwargs.get("display_mode", 0))
        return _apply_freq_filter_multichannel(img, mask, display_mode)


# ─────────────────────────────────────────────
# Gaussian High-pass Filter  (Lọc Gaussian thông cao)
# ─────────────────────────────────────────────
@register_processor
class GaussianHighPass(ImageProcessor):
    label    = "Gaussian High-pass"
    category = "Frequency Domain"
    tooltip  = "Lọc Gaussian thông cao trong miền tần số — làm sắc nét"

    params = {
        "sigma": {
            "label": "Sigma D0",
            "min": 1, "max": 200, "default": 30, "factor": 1.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        D0 = max(1.0, kwargs.get("sigma", 30))
        h, w = img.shape[:2]
        D = _distance_map(h, w)
        mask = 1.0 - np.exp(-(D**2) / (2 * D0**2))
        display_mode = int(kwargs.get("display_mode", 0))
        return _apply_freq_filter_multichannel(img, mask, display_mode)


# ─────────────────────────────────────────────
# Butterworth Low-pass Filter  (Lọc Butterworth thông thấp)
# ─────────────────────────────────────────────
@register_processor
class ButterworthLowPass(ImageProcessor):
    label    = "Butterworth Low-pass"
    category = "Frequency Domain"
    tooltip  = "Lọc Butterworth thông thấp — có thể điều chỉnh độ dốc (order)"

    params = {
        "cutoff": {
            "label": "Cutoff D0",
            "min": 1, "max": 200, "default": 30, "factor": 1.0,
        },
        "order": {
            "label": "Order n",
            "min": 1, "max": 10, "default": 2, "factor": 1.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        D0 = max(1.0, kwargs.get("cutoff", 30))
        n  = max(1, int(kwargs.get("order", 2)))
        h, w = img.shape[:2]
        D = _distance_map(h, w)
        mask = 1.0 / (1.0 + (D / D0) ** (2 * n))
        display_mode = int(kwargs.get("display_mode", 0))
        return _apply_freq_filter_multichannel(img, mask, display_mode)


# ─────────────────────────────────────────────
# Butterworth High-pass Filter  (Lọc Butterworth thông cao)
# ─────────────────────────────────────────────
@register_processor
class ButterworthHighPass(ImageProcessor):
    label    = "Butterworth High-pass"
    category = "Frequency Domain"
    tooltip  = "Lọc Butterworth thông cao — có thể điều chỉnh độ dốc (order)"

    params = {
        "cutoff": {
            "label": "Cutoff D0",
            "min": 1, "max": 200, "default": 30, "factor": 1.0,
        },
        "order": {
            "label": "Order n",
            "min": 1, "max": 10, "default": 2, "factor": 1.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        D0 = max(1.0, kwargs.get("cutoff", 30))
        n  = max(1, int(kwargs.get("order", 2)))
        h, w = img.shape[:2]
        D = _distance_map(h, w)
        mask = 1.0 - 1.0 / (1.0 + (D / D0) ** (2 * n))
        display_mode = int(kwargs.get("display_mode", 0))
        return _apply_freq_filter_multichannel(img, mask, display_mode)


# ─────────────────────────────────────────────
# Ideal Band-pass Filter  (Lọc thông khe lý tưởng)
# ─────────────────────────────────────────────
@register_processor
class IdealBandPass(ImageProcessor):
    label    = "Ideal Band-pass"
    category = "Frequency Domain"
    tooltip  = "Lọc thông khe lý tưởng — chỉ cho qua dải tần số trong [D_low, D_high]"

    params = {
        "d_low": {
            "label": "D_low",
            "min": 0, "max": 200, "default": 10, "factor": 1.0,
        },
        "d_high": {
            "label": "D_high",
            "min": 1, "max": 300, "default": 60, "factor": 1.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        D_low  = max(0.0, kwargs.get("d_low", 10))
        D_high = max(D_low + 1, kwargs.get("d_high", 60))
        h, w   = img.shape[:2]
        D      = _distance_map(h, w)
        mask   = ((D >= D_low) & (D <= D_high)).astype(np.float32)
        display_mode = int(kwargs.get("display_mode", 0))
        return _apply_freq_filter_multichannel(img, mask, display_mode)


# ─────────────────────────────────────────────
# Ideal Band-stop (Notch) Filter  (Lọc chặn khe lý tưởng)
# ─────────────────────────────────────────────
@register_processor
class IdealBandStop(ImageProcessor):
    label    = "Ideal Band-stop"
    category = "Frequency Domain"
    tooltip  = "Lọc chặn khe lý tưởng — chặn dải tần số trong [D_low, D_high], cho qua phần còn lại"

    params = {
        "d_low": {
            "label": "D_low",
            "min": 0, "max": 200, "default": 10, "factor": 1.0,
        },
        "d_high": {
            "label": "D_high",
            "min": 1, "max": 300, "default": 60, "factor": 1.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        D_low  = max(0.0, kwargs.get("d_low", 10))
        D_high = max(D_low + 1, kwargs.get("d_high", 60))
        h, w   = img.shape[:2]
        D      = _distance_map(h, w)
        mask   = 1.0 - ((D >= D_low) & (D <= D_high)).astype(np.float32)
        display_mode = int(kwargs.get("display_mode", 0))
        return _apply_freq_filter_multichannel(img, mask, display_mode)


# ─────────────────────────────────────────────
# Gaussian Band-pass Filter  (Lọc thông khe Gaussian)
# ─────────────────────────────────────────────
@register_processor
class GaussianBandPass(ImageProcessor):
    label    = "Gaussian Band-pass"
    category = "Frequency Domain"
    tooltip  = "Lọc thông khe Gaussian — cho qua dải tần xung quanh D0 với độ rộng W"

    params = {
        "center": {
            "label": "Center D0",
            "min": 1, "max": 200, "default": 40, "factor": 1.0,
        },
        "width": {
            "label": "Width W",
            "min": 1, "max": 100, "default": 20, "factor": 1.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        D0 = max(1.0, kwargs.get("center", 40))
        W  = max(1.0, kwargs.get("width", 20))
        h, w = img.shape[:2]
        D    = _distance_map(h, w)
        # Gaussian band-pass: 1 - exp(-(D-D0)^2 / (2*(W/2)^2))
        # Actually standard formula: H = exp(-(D-D0)^2 / (2*sigma^2)) where sigma = W/2
        sigma = W / 2.0
        mask  = np.exp(-((D - D0)**2) / (2 * sigma**2))
        display_mode = int(kwargs.get("display_mode", 0))
        return _apply_freq_filter_multichannel(img, mask, display_mode)


# ─────────────────────────────────────────────
# Gaussian Band-stop Filter  (Lọc chặn khe Gaussian)
# ─────────────────────────────────────────────
@register_processor
class GaussianBandStop(ImageProcessor):
    label    = "Gaussian Band-stop"
    category = "Frequency Domain"
    tooltip  = "Lọc chặn khe Gaussian — chặn dải tần xung quanh D0 với độ rộng W"

    params = {
        "center": {
            "label": "Center D0",
            "min": 1, "max": 200, "default": 40, "factor": 1.0,
        },
        "width": {
            "label": "Width W",
            "min": 1, "max": 100, "default": 20, "factor": 1.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        D0    = max(1.0, kwargs.get("center", 40))
        W     = max(1.0, kwargs.get("width", 20))
        h, w  = img.shape[:2]
        D     = _distance_map(h, w)
        sigma = W / 2.0
        mask  = 1.0 - np.exp(-((D - D0)**2) / (2 * sigma**2))
        display_mode = int(kwargs.get("display_mode", 0))
        return _apply_freq_filter_multichannel(img, mask, display_mode)


# ─────────────────────────────────────────────
# Butterworth Band-pass Filter  (Lọc thông khe Butterworth)
# ─────────────────────────────────────────────
@register_processor
class ButterworthBandPass(ImageProcessor):
    label    = "Butterworth Band-pass"
    category = "Frequency Domain"
    tooltip  = "Lọc thông khe Butterworth — cho qua dải tần xung quanh D0 với độ rộng W"

    params = {
        "center": {
            "label": "Center D0",
            "min": 1, "max": 200, "default": 40, "factor": 1.0,
        },
        "width": {
            "label": "Width W",
            "min": 1, "max": 100, "default": 20, "factor": 1.0,
        },
        "order": {
            "label": "Order n",
            "min": 1, "max": 10, "default": 2, "factor": 1.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        D0 = max(1.0, kwargs.get("center", 40))
        W  = max(1.0, kwargs.get("width", 20))
        n  = max(1, int(kwargs.get("order", 2)))
        h, w = img.shape[:2]
        D    = _distance_map(h, w)
        # Prevent division by zero at D=0
        D_safe = np.where(D == 0, 1e-10, D)
        mask   = 1.0 / (1.0 + ((D_safe * W) / (D_safe**2 - D0**2 + 1e-10))**(2 * n))
        display_mode = int(kwargs.get("display_mode", 0))
        return _apply_freq_filter_multichannel(img, mask, display_mode)


# ─────────────────────────────────────────────
# Butterworth Band-stop Filter  (Lọc chặn khe Butterworth)
# ─────────────────────────────────────────────
@register_processor
class ButterworthBandStop(ImageProcessor):
    label    = "Butterworth Band-stop"
    category = "Frequency Domain"
    tooltip  = "Lọc chặn khe Butterworth — chặn dải tần xung quanh D0 với độ rộng W"

    params = {
        "center": {
            "label": "Center D0",
            "min": 1, "max": 200, "default": 40, "factor": 1.0,
        },
        "width": {
            "label": "Width W",
            "min": 1, "max": 100, "default": 20, "factor": 1.0,
        },
        "order": {
            "label": "Order n",
            "min": 1, "max": 10, "default": 2, "factor": 1.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        D0 = max(1.0, kwargs.get("center", 40))
        W  = max(1.0, kwargs.get("width", 20))
        n  = max(1, int(kwargs.get("order", 2)))
        h, w = img.shape[:2]
        D    = _distance_map(h, w)
        D_safe = np.where(D == 0, 1e-10, D)
        H_bp   = 1.0 / (1.0 + ((D_safe * W) / (D_safe**2 - D0**2 + 1e-10))**(2 * n))
        mask   = 1.0 - H_bp
        display_mode = int(kwargs.get("display_mode", 0))
        return _apply_freq_filter_multichannel(img, mask, display_mode)


# ─────────────────────────────────────────────
# Motion Blur Removal (Wiener Deconvolution)
# (Khử nhiễu chuyển động)
# ─────────────────────────────────────────────
@register_processor
class MotionBlurRemoval(ImageProcessor):
    label    = "Motion Deblur"
    category = "Frequency Domain"
    tooltip  = "Khử nhiễu/mờ chuyển động bằng lọc Wiener trong miền tần số"

    params = {
        "length": {
            "label": "Blur Length",
            "min": 1, "max": 60, "default": 15, "factor": 1.0,
        },
        "angle": {
            "label": "Angle (°)",
            "min": 0, "max": 179, "default": 0, "factor": 1.0,
        },
        "noise_ratio": {
            "label": "Noise K (×0.01)",
            "min": 1, "max": 100, "default": 10, "factor": 100.0,
        },
        "display_mode": {"label": "Display", "type": "choice", "choices": ["Result Only", "Grid View"], "default": 0},
    }

    @staticmethod
    def _make_psf(shape, length: int, angle: float) -> np.ndarray:
        """Create a motion-blur PSF of given shape."""
        psf = np.zeros(shape, dtype=np.float32)
        cx, cy = shape[1] // 2, shape[0] // 2
        ang_rad = np.deg2rad(angle)
        half = length // 2
        for i in range(-half, half + 1):
            dx = int(round(i * np.cos(ang_rad)))
            dy = int(round(i * np.sin(ang_rad)))
            x, y = cx + dx, cy + dy
            if 0 <= x < shape[1] and 0 <= y < shape[0]:
                psf[y, x] = 1.0
        s = psf.sum()
        if s > 0:
            psf /= s
        return psf

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        length = max(1, int(kwargs.get("length", 15)))
        angle  = kwargs.get("angle", 0.0)
        K      = max(1e-6, kwargs.get("noise_ratio", 0.1))
        display_mode = int(kwargs.get("display_mode", 0))

        def _deblur_channel(ch: np.ndarray) -> np.ndarray:
            h, w = ch.shape
            psf = self._make_psf((h, w), length, angle)
            PSF = np.fft.fft2(psf)
            IMG = np.fft.fft2(ch.astype(np.float32))
            # Wiener filter: H* / (|H|^2 + K)
            PSF_conj = np.conj(PSF)
            denom    = PSF_conj * PSF + K
            W_filt   = PSF_conj / denom
            restored = np.fft.ifft2(W_filt * IMG)
            restored = np.abs(restored)
            return np.clip(restored, 0, 255).astype(np.uint8)

        if img.ndim == 2:
            result = _deblur_channel(img)
        else:
            channels = cv2.split(img)
            result = cv2.merge([_deblur_channel(c) for c in channels])

        if display_mode == 0:
            return result

        h, w = img.shape[:2]
        gray = _to_gray_float(img)
        psf = self._make_psf((h, w), length, angle)
        PSF = np.fft.fft2(psf)
        IMG = np.fft.fft2(gray)
        PSF_conj = np.conj(PSF)
        denom    = PSF_conj * PSF + K
        W_filt   = PSF_conj / denom
        
        fshift = np.fft.fftshift(IMG)
        mag = 20 * np.log(np.abs(fshift) + 1)
        mag = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        mask_vis = np.fft.fftshift(np.abs(W_filt))
        mask_vis = cv2.normalize(mask_vis, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        is_color = (img.ndim == 3)
        def _to_bgr(arr):
            if is_color and arr.ndim == 2:
                return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
            return arr

        mag_bgr = _to_bgr(mag)
        mask_bgr = _to_bgr(mask_vis)
        orig_bgr = _to_bgr(img)
        res_bgr = _to_bgr(result)

        sh, sw = max(1, h // 2), max(1, w // 2)

        def _labeled(src, text):
            out = cv2.resize(src, (sw, sh))
            font_scale = max(0.5, sw / 500.0)
            cv2.putText(out, text, (10, int(30 * font_scale)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), max(1, int(2*font_scale)), cv2.LINE_AA)
            return out

        top = np.hstack([_labeled(orig_bgr, "Original"), _labeled(mag_bgr, "Input Spectrum")])
        bot = np.hstack([_labeled(mask_bgr, "Wiener Filter"), _labeled(res_bgr, "Result")])
        return np.vstack([top, bot])


