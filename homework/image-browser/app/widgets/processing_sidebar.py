"""
widgets/processing_sidebar.py — Right-side processing panel.

Architecture
────────────
Processors are grouped by `category` into collapsible sections.
Click a category header to expand/collapse its list of operations.

To add a new processor:
    1. Create app/processors/my_filter.py
    2. Subclass ImageProcessor, set label/category/tooltip
    3. Decorate with @register_processor
    → A new button appears automatically in the correct category section.

Signals (emitted to MainWindow)
────────────────────────────────
    resetRequested          — restore original image
    processRequested(label) — run a static processor
    animateRequested(label) — run an animated processor
"""

from PyQt5.QtCore import (
    QEasingCurve, QParallelAnimationGroup,
    QPropertyAnimation, Qt, pyqtSignal,
)
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..processors import builtin as _  # noqa — trigger self-registration
from ..processors.base import get_all_processors
from ..icons import IC, ICON_SIZE_SM, ICON_SIZE_MD, CATEGORY_ICONS, PROC_ICONS
from ..theme import (
    C_ACCENT, C_ACCENT_DIM, C_ACCENT_HOT,
    C_BG_ACTIVE, C_BG_BASE, C_BG_DEEP, C_BG_HOVER, C_BG_SURFACE,
    C_BORDER, C_BORDER_MID,
    C_POP, C_POP_DIM, C_POP_HOT,
    C_TEXT_HI, C_TEXT_LOW, C_TEXT_MID, C_TEXT_DEAD,
    FONT_MONO,
)


# ─────────────────────────────────────────────
# Collapsible section
# ─────────────────────────────────────────────
class CollapsibleSection(QWidget):
    """
    A category header that expands/collapses its child buttons with animation.

    Usage
    ─────
        section = CollapsibleSection("Transform", start_expanded=True)
        section.add_button(btn)
        layout.addWidget(section)
    """

    def __init__(self, title: str, start_expanded: bool = True,
                 icon_func=None, parent=None):
        super().__init__(parent)
        self._expanded = start_expanded
        self._buttons: list[QPushButton] = []
        self._icon_func = icon_func

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Toggle header ─────────────────────
        self._header = QPushButton()
        self._header.setCheckable(False)
        self._header.setFixedHeight(30)
        self._header.setCursor(Qt.PointingHandCursor)
        if icon_func:
            from ..icons import ICON_SIZE_SM
            self._header.setIcon(icon_func())
            self._header.setIconSize(ICON_SIZE_SM)
        self._header.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C_TEXT_MID};
                border: none;
                border-left: 3px solid {C_ACCENT};
                border-radius: 0;
                text-align: left;
                padding: 0 10px;
                margin-top: 6px;
                font-family: "{FONT_MONO}";
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {C_BG_HOVER};
                color: {C_ACCENT};
                border-left-color: {C_ACCENT_HOT};
            }}
        """)
        self._header.clicked.connect(self._toggle)
        self._update_header_text(title)
        self._title = title
        outer.addWidget(self._header)

        # ── Content container ─────────────────
        self._content = QWidget()
        self._content.setStyleSheet(f"background: {C_BG_BASE};")
        self._cl = QVBoxLayout(self._content)
        self._cl.setContentsMargins(8, 4, 8, 6)
        self._cl.setSpacing(4)
        outer.addWidget(self._content)

        if not start_expanded:
            self._content.setMaximumHeight(0)
            self._content.setVisible(False)

    def _update_header_text(self, title: str):
        arrow = "▼" if self._expanded else "▶"
        self._header.setText(f"{arrow}  {title}")

    def add_button(self, btn: QPushButton):
        self._cl.addWidget(btn)
        self._buttons.append(btn)

    def set_buttons_enabled(self, enabled: bool):
        for btn in self._buttons:
            btn.setEnabled(enabled)

    def _toggle(self):
        self._expanded = not self._expanded
        self._update_header_text(self._title)

        if self._expanded:
            # Expand: show content, animate height 0 → natural height
            self._content.setVisible(True)
            # Compute natural height
            self._content.setMaximumHeight(16_777_215)
            target = self._content.sizeHint().height()
            self._content.setMaximumHeight(0)

            anim = QPropertyAnimation(self._content, b"maximumHeight", self)
            anim.setStartValue(0)
            anim.setEndValue(target)
            anim.setDuration(180)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
            self._anim = anim
        else:
            # Collapse: animate height → 0, then hide
            current = self._content.height()
            anim = QPropertyAnimation(self._content, b"maximumHeight", self)
            anim.setStartValue(current)
            anim.setEndValue(0)
            anim.setDuration(160)
            anim.setEasingCurve(QEasingCurve.InCubic)
            anim.finished.connect(lambda: self._content.setVisible(False))
            anim.start()
            self._anim = anim


# ─────────────────────────────────────────────
# Button factories
# ─────────────────────────────────────────────
def _proc_btn(label: str, tooltip: str = "") -> QPushButton:
    btn = QPushButton(label)
    btn.setFont(QFont(FONT_MONO, 11))
    btn.setFixedHeight(32)
    btn.setToolTip(tooltip)
    btn.setEnabled(False)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            color: {C_TEXT_MID};
            border: none;
            border-bottom: 1px solid {C_BORDER};
            border-radius: 0;
            padding: 0 8px;
            text-align: left;
        }}
        QPushButton:hover {{
            background: {C_BG_HOVER};
            color: {C_ACCENT};
            border-bottom-color: {C_ACCENT};
            border-radius: 4px;
        }}
        QPushButton:pressed {{
            background: {C_BG_ACTIVE};
            color: {C_ACCENT_DIM};
            border-radius: 4px;
        }}
        QPushButton:disabled {{
            background: transparent;
            color: {C_TEXT_DEAD};
            border-bottom-color: {C_BORDER};
        }}
    """)
    return btn


def _reset_btn() -> QPushButton:
    btn = QPushButton("Reset")
    btn.setFont(QFont(FONT_MONO, 11, QFont.Bold))
    btn.setFixedHeight(32)
    btn.setEnabled(False)
    btn.setToolTip("Restore original image")
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {C_POP};
            color: #FFFFFF;
            border: none;
            border-radius: 3px;
            padding: 0 8px;
            letter-spacing: 0.5px;
        }}
        QPushButton:hover {{
            background: {C_POP_HOT};
            color: #FFFFFF;
        }}
        QPushButton:pressed {{
            background: {C_POP_DIM};
            color: #FFFFFF;
        }}
        QPushButton:disabled {{
            background: {C_BG_BASE};
            color: {C_TEXT_DEAD};
            border: 1px solid {C_BORDER};
        }}
    """)
    return btn


def _save_btn() -> QPushButton:
    btn = QPushButton("Save")
    btn.setFont(QFont(FONT_MONO, 11, QFont.Bold))
    btn.setFixedHeight(32)
    btn.setEnabled(False)
    btn.setToolTip("Save current image (Ctrl+S)")
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {C_ACCENT};
            color: #FFFFFF;
            border: none;
            border-radius: 3px;
            padding: 0 8px;
            letter-spacing: 0.5px;
        }}
        QPushButton:hover {{
            background: {C_ACCENT_HOT};
            color: #FFFFFF;
        }}
        QPushButton:pressed {{
            background: {C_ACCENT_DIM};
            color: #FFFFFF;
        }}
        QPushButton:disabled {{
            background: {C_BG_BASE};
            color: {C_TEXT_DEAD};
            border: 1px solid {C_BORDER};
        }}
    """)
    return btn

# ─────────────────────────────────────────────
# Processing Sidebar
# ─────────────────────────────────────────────
class ProcessingSidebar(QWidget):
    """
    Right-side panel with collapsible category sections.

    Signals
    ───────
    resetRequested          — user clicked Reset
    processRequested(label) — user clicked a static processor
    animateRequested(label) — user clicked an animated processor
    """

    resetRequested   = pyqtSignal()
    saveRequested    = pyqtSignal()
    processRequested = pyqtSignal(str)
    animateRequested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(165)
        self.setMaximumWidth(220)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setStyleSheet(f"""
            ProcessingSidebar {{
                background: {C_BG_BASE};
            }}
        """)


        # Track all proc buttons for enable/disable
        self._sections: list[CollapsibleSection] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Panel header ──────────────────────
        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet(f"""
            background: {C_BG_DEEP};
            border-bottom: 1px solid {C_BORDER};
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 0, 12, 0)
        lbl = QLabel("Process")
        lbl.setFont(QFont(FONT_MONO, 12))
        lbl.setStyleSheet(f"color: {C_TEXT_MID}; background: transparent;")

        proc_icon_lbl = QLabel()
        proc_icon_lbl.setPixmap(IC.process().pixmap(ICON_SIZE_SM))
        proc_icon_lbl.setStyleSheet("background: transparent;")
        hl.addWidget(proc_icon_lbl)
        hl.addSpacing(5)
        hl.addWidget(lbl)
        root.addWidget(header)

        # ── Scrollable content ────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"background: {C_BG_BASE}; border: none;")

        content = QWidget()
        content.setStyleSheet(f"background: {C_BG_BASE};")
        self._cl = QVBoxLayout(content)
        self._cl.setContentsMargins(8, 8, 8, 8)
        self._cl.setSpacing(0)

        # Action buttons (Reset & Save)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(4)
        
        self.btn_reset = _reset_btn()
        self.btn_reset.setIcon(IC.reset())
        self.btn_reset.setIconSize(ICON_SIZE_MD)
        self.btn_reset.clicked.connect(self.resetRequested)
        
        self.btn_save = _save_btn()
        self.btn_save.setIcon(IC.save())
        self.btn_save.setIconSize(ICON_SIZE_MD)
        self.btn_save.clicked.connect(self.saveRequested)

        action_layout.addWidget(self.btn_reset)
        action_layout.addWidget(self.btn_save)
        
        self._cl.addLayout(action_layout)
        self._cl.addSpacing(8)

        # ── Collapsible category sections ─────
        self._build_sections()

        # ── Future placeholder ────────────────
        self._cl.addStretch()
        hint = QLabel("More tools\ncoming soon")
        hint.setAlignment(Qt.AlignCenter)
        hint.setFont(QFont(FONT_MONO, 8))
        hint.setStyleSheet(f"""
            color: {C_TEXT_DEAD};
            border: 1px dashed {C_BORDER};
            border-radius: 4px;
            padding: 12px 8px;
            margin-top: 8px;
            background: transparent;
        """)
        self._cl.addWidget(hint)

        scroll.setWidget(content)
        root.addWidget(scroll)

    # ──────────────────────────────────────────
    def _build_sections(self):
        """
        Group processors by category, create one CollapsibleSection per category.
        First category starts expanded; rest start collapsed.
        """
        processors = get_all_processors()

        # Collect categories preserving registration order
        categories: dict[str, list] = {}
        for proc in processors:
            categories.setdefault(proc.category, []).append(proc)

        for idx, (cat, procs) in enumerate(categories.items()):
            section = CollapsibleSection(
                title=cat,
                start_expanded=(idx == 0),
                icon_func=CATEGORY_ICONS.get(cat),
            )

            for proc in procs:
                btn = _proc_btn(proc.label, proc.tooltip)
                # Add icon if we have one for this processor
                if proc.label in PROC_ICONS:
                    btn.setIcon(PROC_ICONS[proc.label]())
                    btn.setIconSize(ICON_SIZE_MD)
                if proc.animated:
                    btn.clicked.connect(self._make_animate_handler(proc.label))
                else:
                    btn.clicked.connect(self._make_process_handler(proc.label))
                section.add_button(btn)

            self._sections.append(section)
            self._cl.addWidget(section)
            self._cl.addSpacing(2)

    def _make_process_handler(self, label: str):
        def h(): self.processRequested.emit(label)
        return h

    def _make_animate_handler(self, label: str):
        def h(): self.animateRequested.emit(label)
        return h

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────
    def set_enabled(self, enabled: bool):
        """Enable/disable all buttons when an image loads or is cleared."""
        self.btn_reset.setEnabled(enabled)
        self.btn_save.setEnabled(enabled)
        for section in self._sections:
            section.set_buttons_enabled(enabled)
