"""
processors/base.py — Processor registry and base class.

HOW TO ADD A NEW PROCESSOR
───────────────────────────
1. Create a file in app/processors/, e.g. app/processors/my_filter.py
2. Define a class that inherits from ImageProcessor
3. Decorate it with @register_processor
4. That's it — the UI will auto-discover and render the button.

Example:
    from .base import ImageProcessor, register_processor

    @register_processor
    class SobelEdge(ImageProcessor):
        label    = "Sobel Edge"
        category = "Edge Detection"
        tooltip  = "Detect edges using Sobel operator"

        def apply(self, img: np.ndarray) -> np.ndarray:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            sx   = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sy   = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            return cv2.convertScaleAbs(np.sqrt(sx**2 + sy**2))
"""

from __future__ import annotations

import numpy as np
from typing import ClassVar, Dict, List, Optional, Type


# ─────────────────────────────────────────────
# Registry (module-level singleton dict)
# ─────────────────────────────────────────────
_REGISTRY: Dict[str, "ImageProcessor"] = {}   # label → instance


def get_all_processors() -> List["ImageProcessor"]:
    """Return all registered processor instances, in registration order."""
    return list(_REGISTRY.values())


def get_processor(label: str) -> Optional["ImageProcessor"]:
    return _REGISTRY.get(label)


def register_processor(cls: Type["ImageProcessor"]) -> Type["ImageProcessor"]:
    """
    Class decorator.  Instantiates and registers a processor by its label.

    Usage::

        @register_processor
        class MyFilter(ImageProcessor):
            label = "My Filter"
            ...
    """
    instance = cls()
    _REGISTRY[instance.label] = instance
    return cls


# ─────────────────────────────────────────────
# Base class
# ─────────────────────────────────────────────
class ImageProcessor:
    """
    Abstract base for all image processing operations.

    Subclass this, set class attributes, implement `apply()`, and
    decorate with @register_processor.

    Attributes
    ----------
    label    : str  — Button text shown in the UI  (must be unique)
    category : str  — Grouping label (used for future menu organisation)
    tooltip  : str  — Tooltip shown on hover
    """

    label:    ClassVar[str] = "Unnamed"
    category: ClassVar[str] = "General"
    tooltip:  ClassVar[str] = ""
    animated: ClassVar[bool] = False  # True → UI calls on_animate() instead of apply()
    
    # Dictionary of hyperparameters. Example:
    # {"gamma": {"label": "Gamma", "min": 1, "max": 50, "default": 10, "factor": 10.0}}
    params: ClassVar[Dict[str, Dict]] = {}

    def apply(self, img: np.ndarray, **kwargs) -> np.ndarray:
        """
        Process the image and return a new numpy array (BGR or grayscale).

        Parameters
        ----------
        img : np.ndarray
            Input image as returned by cv2.imread (BGR, uint8).
            May be 2-D (grayscale) or 3-D (BGR).

        Returns
        -------
        np.ndarray
            Processed image.  Return a copy; do not modify `img` in-place.
        """
        raise NotImplementedError
