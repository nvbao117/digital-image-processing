# processors/__init__.py
# Import builtin processors so they self-register when this package is imported.
from . import builtin   # noqa: F401 — side-effect import triggers @register_processor
