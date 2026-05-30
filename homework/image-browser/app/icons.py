"""
app/icons.py — Centralized icon registry using qtawesome (Font Awesome 5).

All icons are defined here so they stay consistent across the app.
Colors are imported from theme so icons automatically match the palette.

Usage:
    from app.icons import IC
    btn.setIcon(IC.folder_open())
    btn.setIconSize(QSize(14, 14))
"""

import qtawesome as qta
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

from .theme import (
    C_ACCENT, C_ACCENT_DIM, C_ACCENT_HOT,
    C_POP, C_POP_HOT,
    C_TEXT_MID, C_TEXT_LOW, C_TEXT_HI,
    C_BG_SURFACE,
)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _icon(name: str, color: str, size: int = 14) -> QIcon:
    return qta.icon(name, color=color, scale_factor=1.0)

def _icon2(name: str, active: str, color: str, active_color: str) -> QIcon:
    """Icon with separate active/hover state color."""
    return qta.icon(name, color=color, color_active=active_color)


# ─────────────────────────────────────────────
# Icon catalogue  (call each as a function)
# ─────────────────────────────────────────────
class _Icons:
    # ── App brand ────────────────────────────
    def app(self):         return _icon("fa5s.camera-retro",   C_ACCENT)

    # ── Panel headers ─────────────────────────
    def explorer(self):    return _icon("fa5s.folder",         C_TEXT_LOW)
    def collection(self):  return _icon("fa5s.th",             C_TEXT_LOW)
    def preview(self):     return _icon("fa5s.eye",            C_TEXT_LOW)
    def process(self):     return _icon("fa5s.sliders-h",      C_TEXT_LOW)

    # ── Header bar actions ───────────────────
    def folder_open(self): return _icon("fa5s.folder-open",    C_BG_SURFACE)

    # ── Processor operations ─────────────────
    def rgb(self):         return _icon("fa5s.adjust",         C_TEXT_MID)
    def grayscale(self):   return _icon("fa5s.circle",         C_TEXT_MID)
    def rgb_to_hsv(self):  return _icon("fa5s.tint",           C_TEXT_MID)
    def hsv_to_rgb(self):  return _icon("fa5s.tint-slash",     C_TEXT_MID)
    def crop(self):        return _icon("fa5s.crop-alt",       C_TEXT_MID)
    def flip(self):        return _icon("fa5s.exchange-alt",   C_TEXT_MID)
    def equalize(self):    return _icon("fa5s.chart-bar",      C_TEXT_MID)
    def rotate(self):      return _icon("fa5s.sync-alt",       C_TEXT_MID)
    def reset(self):       return _icon("fa5s.undo",           C_BG_SURFACE)
    def save(self):        return _icon("fa5s.save",           C_BG_SURFACE)

    # ── Category section headers ─────────────
    def cat_color(self):   return _icon("fa5s.palette",        C_TEXT_LOW)
    def cat_transform(self): return _icon("fa5s.crop-alt",     C_TEXT_LOW)
    def cat_enhance(self): return _icon("fa5s.magic",          C_TEXT_LOW)
    def cat_sharpen(self): return _icon("fa5s.bolt",           C_TEXT_LOW)
    def cat_filter(self):  return _icon("fa5s.filter",         C_TEXT_LOW)
    def cat_morphology(self): return _icon("fa5s.shapes",      C_TEXT_LOW)
    def cat_segmentation(self): return _icon("fa5s.project-diagram", C_TEXT_LOW)
    def cat_detection(self): return _icon("fa5s.search",       C_TEXT_LOW)

    # ── Tree / file system ───────────────────
    def folder(self):      return _icon("fa5s.folder",         C_ACCENT_DIM)
    def folder_active(self): return _icon("fa5s.folder-open",  C_ACCENT)

    # ── Misc UI ──────────────────────────────
    def image(self):       return _icon("fa5s.image",          C_TEXT_MID)
    def info(self):        return _icon("fa5s.info-circle",    C_TEXT_LOW)
    def chevron_down(self): return _icon("fa5s.chevron-down",  C_TEXT_LOW)
    def chevron_right(self): return _icon("fa5s.chevron-right",C_TEXT_LOW)

    # ── New Processors ───────────────────────
    def sharpen(self):     return _icon("fa5s.adjust",         C_TEXT_MID)
    def dilation(self):    return _icon("fa5s.expand-arrows-alt", C_TEXT_MID)
    def erosion(self):     return _icon("fa5s.compress-arrows-alt", C_TEXT_MID)
    def opening(self):     return _icon("fa5s.unlock",         C_TEXT_MID)
    def closing(self):     return _icon("fa5s.lock",           C_TEXT_MID)
    def boundary(self):    return _icon("fa5s.draw-polygon",   C_TEXT_MID)
    def region_fill(self): return _icon("fa5s.fill-drip",      C_TEXT_MID)
    def component(self):   return _icon("fa5s.project-diagram", C_TEXT_MID)
    def convex_hull(self): return _icon("fa5s.vector-square",  C_TEXT_MID)
    def thinning(self):    return _icon("fa5s.minus",          C_TEXT_MID)
    def thickening(self):  return _icon("fa5s.plus",           C_TEXT_MID)
    def skeleton(self):    return _icon("fa5s.stream",         C_TEXT_MID)
    def hit_or_miss(self): return _icon("fa5s.bullseye",       C_TEXT_MID)
    def threshold(self):   return _icon("fa5s.sliders-h",      C_TEXT_MID)
    def otsu(self):        return _icon("fa5s.adjust",         C_TEXT_MID)
    def adaptive_threshold(self): return _icon("fa5s.th-large", C_TEXT_MID)
    def kmeans(self):      return _icon("fa5s.layer-group",    C_TEXT_MID)
    def watershed(self):   return _icon("fa5s.water",          C_TEXT_MID)
    def point_detection(self): return _icon("fa5s.crosshairs", C_TEXT_MID)
    def line_detection(self): return _icon("fa5s.grip-lines",  C_TEXT_MID)
    def edge_detection(self): return _icon("fa5s.bolt",        C_TEXT_MID)


# Singleton — import and use as:  IC.folder_open()
IC = _Icons()

# ─────────────────────────────────────────────
# Processor label → icon mapping
# ─────────────────────────────────────────────
PROC_ICONS: dict[str, callable] = {
    "RGB Split":  lambda: IC.rgb(),
    "Grayscale":  lambda: IC.grayscale(),
    "RGB → HSV":  lambda: IC.rgb_to_hsv(),
    "HSV → RGB":  lambda: IC.hsv_to_rgb(),
    "Crop":       lambda: IC.crop(),
    "Flip":       lambda: IC.flip(),
    "Equalize":   lambda: IC.equalize(),
    "Rotate":     lambda: IC.rotate(),
    "Laplace Sharpen": lambda: IC.sharpen(),
    "Gradient Sharpen": lambda: IC.sharpen(),
    "Dilation": lambda: IC.dilation(),
    "Erosion": lambda: IC.erosion(),
    "Opening": lambda: IC.opening(),
    "Closing": lambda: IC.closing(),
    "Boundary Extraction": lambda: IC.boundary(),
    "Region Filling": lambda: IC.region_fill(),
    "Connected Component": lambda: IC.component(),
    "Convex Hull": lambda: IC.convex_hull(),
    "Thinning": lambda: IC.thinning(),
    "Thickening": lambda: IC.thickening(),
    "Skeleton": lambda: IC.skeleton(),
    "Hit-or-Miss": lambda: IC.hit_or_miss(),
    "Binary Threshold": lambda: IC.threshold(),
    "Otsu Threshold": lambda: IC.otsu(),
    "Adaptive Threshold": lambda: IC.adaptive_threshold(),
    "K-Means Segmentation": lambda: IC.kmeans(),
    "Watershed": lambda: IC.watershed(),
    "Point Detection": lambda: IC.point_detection(),
    "Line Detection": lambda: IC.line_detection(),
    "Edge Detection": lambda: IC.edge_detection(),
}

CATEGORY_ICONS: dict[str, callable] = {
    "Color Analysis": lambda: IC.cat_color(),
    "Transform":      lambda: IC.cat_transform(),
    "Enhancement":    lambda: IC.cat_enhance(),
    "Sharpening":     lambda: IC.cat_sharpen(),
    "Filters":        lambda: IC.cat_filter(),
    "Morphology":     lambda: IC.cat_morphology(),
    "Segmentation":   lambda: IC.cat_segmentation(),
    "Detection":      lambda: IC.cat_detection(),
}

ICON_SIZE_SM  = QSize(13, 13)   # panel header labels
ICON_SIZE_MD  = QSize(15, 15)   # buttons
ICON_SIZE_LG  = QSize(18, 18)   # primary action buttons
