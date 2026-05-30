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
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSizePolicy,
    QTextEdit,
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
        self._widgets: list[QWidget] = []
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

    def add_widget(self, w: QWidget, btns: list[QPushButton]):
        self._cl.addWidget(w)
        self._widgets.append(w)
        self._buttons.extend(btns)

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
# Parameter Control Panel (Slider + ComboBox)
# ─────────────────────────────────────────────
class ParamControlPanel(QWidget):
    valueChanged = pyqtSignal(dict)

    def __init__(self, params: dict, parent=None):
        super().__init__(parent)
        self.params = params
        self.sliders  = {}  # p_name -> (slider, val_lbl, factor)
        self.combos   = {}  # p_name -> QComboBox

        from PyQt5.QtCore import QTimer
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)  # 250ms debounce
        self._timer.timeout.connect(self._emit_value_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 2, 8, 8)
        layout.setSpacing(4)

        for p_name, p_info in params.items():
            param_type = p_info.get("type", "slider")

            lbl = QLabel(f"{p_info['label']}:")
            lbl.setFont(QFont(FONT_MONO, 9))
            lbl.setStyleSheet(f"color: {C_TEXT_MID};")

            if param_type == "choice":
                combo = QComboBox()
                combo.setFont(QFont(FONT_MONO, 9))
                combo.setStyleSheet(f"""
                    QComboBox {{
                        background: {C_BG_DEEP};
                        color: {C_TEXT_HI};
                        border: 1px solid {C_BORDER};
                        border-radius: 3px;
                        padding: 2px 6px;
                    }}
                    QComboBox::drop-down {{ border: none; }}
                    QComboBox QAbstractItemView {{
                        background: {C_BG_SURFACE};
                        color: {C_TEXT_HI};
                        selection-background-color: {C_ACCENT_DIM};
                    }}
                """)
                for choice in p_info['choices']:
                    combo.addItem(choice)
                combo.setCurrentIndex(p_info.get('default', 0))
                combo.currentIndexChanged.connect(self._on_change)
                self.combos[p_name] = combo

                row = QHBoxLayout()
                row.addWidget(lbl)
                row.addWidget(combo)
                layout.addLayout(row)

            else:  # slider
                val_lbl = QLabel()
                val_lbl.setFont(QFont(FONT_MONO, 9))
                val_lbl.setStyleSheet(f"color: {C_ACCENT};")
                val_lbl.setFixedWidth(35)

                slider = QSlider(Qt.Horizontal)
                slider.setMinimum(p_info['min'])
                slider.setMaximum(p_info['max'])
                slider.setValue(p_info['default'])
                slider.setStyleSheet(f"""
                    QSlider::groove:horizontal {{
                        border: 1px solid {C_BORDER};
                        height: 4px;
                        background: {C_BG_DEEP};
                        margin: 2px 0;
                    }}
                    QSlider::handle:horizontal {{
                        background: {C_ACCENT};
                        border: 1px solid {C_ACCENT_HOT};
                        width: 12px;
                        margin: -4px 0;
                        border-radius: 6px;
                    }}
                """)

                row = QHBoxLayout()
                row.addWidget(lbl)
                row.addWidget(slider)
                row.addWidget(val_lbl)
                layout.addLayout(row)

                factor = p_info.get('factor', 1.0)
                self.sliders[p_name] = (slider, val_lbl, factor)
                val = p_info['default'] / factor
                val_lbl.setText(f"{val:g}")
                slider.valueChanged.connect(self._on_change)

    def _on_change(self):
        # Update text labels immediately so UI feels responsive
        for p_name, (slider, val_lbl, factor) in self.sliders.items():
            val = slider.value() / factor
            val_lbl.setText(f"{val:g}")
        # Restart debounce timer
        self._timer.start()

    def _emit_value_changed(self):
        self.valueChanged.emit(self.get_current_params())

    def get_current_params(self):
        result = {}
        for p_name, (slider, val_lbl, factor) in self.sliders.items():
            val = slider.value() / factor
            result[p_name] = val
        for p_name, combo in self.combos.items():
            result[p_name] = combo.currentIndex()
        return result


# ─────────────────────────────────────────────
# Custom Kernel Input Panel
# ─────────────────────────────────────────────
class CustomKernelPanel(QWidget):
    applyRequested = pyqtSignal(str, dict)  # (label, params)

    PRESETS = {
        "Identity":        "0 0 0\n0 1 0\n0 0 0",
        "Sharpen":         "0 -1 0\n-1 5 -1\n0 -1 0",
        "Edge (Laplace)":  "-1 -1 -1\n-1 8 -1\n-1 -1 -1",
        "Box Blur":        "1 1 1\n1 1 1\n1 1 1",
        "Emboss":          "-2 -1 0\n-1 1 1\n0 1 2",
    }

    def __init__(self, proc_label: str, parent=None):
        super().__init__(parent)
        self._proc_label = proc_label

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 4, 8, 8)
        layout.setSpacing(4)

        # Preset selector
        preset_row = QHBoxLayout()
        preset_lbl = QLabel("Preset:")
        preset_lbl.setFont(QFont(FONT_MONO, 9))
        preset_lbl.setStyleSheet(f"color: {C_TEXT_MID};")

        self.preset_combo = QComboBox()
        self.preset_combo.setFont(QFont(FONT_MONO, 9))
        self.preset_combo.setStyleSheet(f"""
            QComboBox {{
                background: {C_BG_DEEP};
                color: {C_TEXT_HI};
                border: 1px solid {C_BORDER};
                border-radius: 3px;
                padding: 2px 6px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background: {C_BG_SURFACE};
                color: {C_TEXT_HI};
                selection-background-color: {C_ACCENT_DIM};
            }}
        """)
        for name in self.PRESETS:
            self.preset_combo.addItem(name)
        self.preset_combo.currentTextChanged.connect(self._on_preset)
        preset_row.addWidget(preset_lbl)
        preset_row.addWidget(self.preset_combo)
        layout.addLayout(preset_row)

        # Text area for kernel values
        kernel_lbl = QLabel("Kernel (rows, space-separated):")
        kernel_lbl.setFont(QFont(FONT_MONO, 9))
        kernel_lbl.setStyleSheet(f"color: {C_TEXT_MID};")
        layout.addWidget(kernel_lbl)

        self.kernel_edit = QTextEdit()
        self.kernel_edit.setFont(QFont(FONT_MONO, 10))
        self.kernel_edit.setFixedHeight(72)
        self.kernel_edit.setPlaceholderText("e.g.\n-1 -1 -1\n-1  8 -1\n-1 -1 -1")
        self.kernel_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {C_BG_DEEP};
                color: {C_TEXT_HI};
                border: 1px solid {C_BORDER};
                border-radius: 3px;
                padding: 4px;
            }}
        """)
        self.kernel_edit.setText(self.PRESETS["Identity"])
        layout.addWidget(self.kernel_edit)

        # Apply button
        self.btn_apply = QPushButton("▶  Apply Kernel")
        self.btn_apply.setEnabled(False)
        self.btn_apply.setFont(QFont(FONT_MONO, 9, QFont.Bold))
        self.btn_apply.setFixedHeight(26)
        self.btn_apply.setStyleSheet(f"""
            QPushButton {{
                background: {C_ACCENT_DIM};
                color: #fff;
                border: none;
                border-radius: 3px;
                padding: 0 8px;
            }}
            QPushButton:hover {{ background: {C_ACCENT}; }}
            QPushButton:disabled {{ background: {C_BG_SURFACE}; color: {C_TEXT_DEAD}; }}
        """)
        self.btn_apply.clicked.connect(self._emit_apply)
        layout.addWidget(self.btn_apply)

    def set_enabled(self, enabled: bool):
        self.btn_apply.setEnabled(enabled)

    def _on_preset(self, name: str):
        if name in self.PRESETS:
            self.kernel_edit.setText(self.PRESETS[name])

    def _emit_apply(self):
        kernel_str = self.kernel_edit.toPlainText()
        self.applyRequested.emit(self._proc_label, {"kernel": kernel_str})


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
    processWithParamsRequested = pyqtSignal(str, dict)
    animateRequested = pyqtSignal(str)
    infoRequested    = pyqtSignal(str)
    applyRequested   = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
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

        # ── Action buttons ────────────────────
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(8, 8, 8, 8)
        action_layout.setSpacing(4)
        
        self.btn_reset = _reset_btn()
        self.btn_reset.setIcon(IC.reset())
        self.btn_reset.setIconSize(ICON_SIZE_MD)
        self.btn_reset.clicked.connect(lambda: self.resetRequested.emit())
        
        self.btn_apply = _save_btn()
        self.btn_apply.setText("Apply")
        self.btn_apply.setIcon(IC.save())
        self.btn_apply.setIconSize(ICON_SIZE_MD)
        self.btn_apply.clicked.connect(lambda: self.applyRequested.emit())
        
        self.btn_save = _save_btn()
        self.btn_save.setIcon(IC.save())
        self.btn_save.setIconSize(ICON_SIZE_MD)
        self.btn_save.clicked.connect(lambda: self.saveRequested.emit())

        action_layout.addWidget(self.btn_apply)
        action_layout.addWidget(self.btn_save)
        action_layout.addWidget(self.btn_reset)
        
        root.addLayout(action_layout)

        # ── Tabs ──────────────────────────────
        from PyQt5.QtWidgets import QTabWidget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                border-top: 1px solid {C_BORDER};
                background: {C_BG_BASE};
            }}
            QTabBar::tab {{
                background: {C_BG_DEEP};
                color: {C_TEXT_MID};
                padding: 6px 12px;
                border: none;
                font-family: "{FONT_MONO}";
                font-size: 11px;
            }}
            QTabBar::tab:selected {{
                color: {C_ACCENT};
                background: {C_BG_BASE};
                border-bottom: 2px solid {C_ACCENT};
            }}
            QTabBar::tab:hover:!selected {{
                color: {C_TEXT_HI};
                background: {C_BG_HOVER};
            }}
        """)
        root.addWidget(self.tabs)

        self._build_sections()

    # ──────────────────────────────────────────
    def _build_sections(self):
        """
        Group processors by category into Tabs, then into CollapsibleSections.
        """
        processors = get_all_processors()
        self._custom_kernel_panels: list[CustomKernelPanel] = []

        # Collect categories
        categories: dict[str, list] = {}
        for proc in processors:
            categories.setdefault(proc.category, []).append(proc)

        # Map categories to tabs
        TAB_MAPPING = {
            "Color Analysis": "Basic",
            "Transform": "Basic",
            "Enhancement": "Spatial",
            "Filters": "Spatial",
            "Morphology": "Spatial",
            "Segmentation": "Segmentation",
            "Detection": "Detection",
            "Sharpening": "Spatial",
            "Frequency Domain": "Frequency"
        }

        # Initialize tabs
        tab_layouts = {}
        for tab_name in ["Basic", "Spatial", "Segmentation", "Detection", "Frequency"]:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setStyleSheet(f"background: {C_BG_BASE}; border: none;")

            content = QWidget()
            content.setStyleSheet(f"background: {C_BG_BASE};")
            cl = QVBoxLayout(content)
            cl.setContentsMargins(8, 8, 8, 8)
            cl.setSpacing(0)
            
            scroll.setWidget(content)
            self.tabs.addTab(scroll, tab_name)
            tab_layouts[tab_name] = cl

        # Build sections inside tabs
        for cat, procs in categories.items():
            tab_name = TAB_MAPPING.get(cat, "Basic")
            cl = tab_layouts[tab_name]

            section = CollapsibleSection(
                title=cat,
                start_expanded=True,
                icon_func=CATEGORY_ICONS.get(cat),
            )

            for proc in procs:
                w_container = QWidget()
                w_layout = QHBoxLayout(w_container)
                w_layout.setContentsMargins(0, 0, 0, 0)
                w_layout.setSpacing(2)

                btn = _proc_btn(proc.label, proc.tooltip)
                if proc.label in PROC_ICONS:
                    btn.setIcon(PROC_ICONS[proc.label]())
                    btn.setIconSize(ICON_SIZE_MD)

                info_btn = QPushButton()
                info_btn.setIcon(IC.info())
                info_btn.setFixedSize(24, 32)
                info_btn.setToolTip(f"View details & code for {proc.label}")
                info_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        border: none;
                        border-bottom: 1px solid {C_BORDER};
                        border-radius: 0;
                    }}
                    QPushButton:hover {{
                        background: {C_BG_HOVER};
                        border-bottom: 1px solid {C_ACCENT};
                    }}
                """)
                info_btn.clicked.connect(self._make_info_handler(proc.label))

                w_layout.addWidget(btn, stretch=1)
                w_layout.addWidget(info_btn)

                # custom_ui processors
                if getattr(proc, 'custom_ui', False):
                    kernel_panel = CustomKernelPanel(proc.label)
                    kernel_panel.applyRequested.connect(
                        lambda lbl, params: self.processWithParamsRequested.emit(lbl, params)
                    )
                    self._custom_kernel_panels.append(kernel_panel)
                    btn.clicked.connect(self._make_process_with_kernel_handler(kernel_panel))

                    wrapper = QWidget()
                    wl = QVBoxLayout(wrapper)
                    wl.setContentsMargins(0, 0, 0, 0)
                    wl.setSpacing(0)
                    wl.addWidget(w_container)
                    wl.addWidget(kernel_panel)
                    section.add_widget(wrapper, [btn, info_btn])

                # processors with params
                elif hasattr(proc, 'params') and proc.params:
                    param_panel = ParamControlPanel(proc.params)
                    param_panel.valueChanged.connect(self._make_process_with_params_handler(proc.label))

                    if proc.animated:
                        btn.clicked.connect(self._make_animate_handler(proc.label))
                    else:
                        btn.clicked.connect(self._make_process_with_sliders_handler(proc.label, param_panel))

                    wrapper = QWidget()
                    wl = QVBoxLayout(wrapper)
                    wl.setContentsMargins(0, 0, 0, 0)
                    wl.setSpacing(0)
                    wl.addWidget(w_container)
                    wl.addWidget(param_panel)
                    section.add_widget(wrapper, [btn, info_btn])

                else:
                    if proc.animated:
                        btn.clicked.connect(self._make_animate_handler(proc.label))
                    else:
                        btn.clicked.connect(self._make_process_handler(proc.label))
                    section.add_widget(w_container, [btn, info_btn])

            self._sections.append(section)
            cl.addWidget(section)
            cl.addSpacing(2)

        # Add stretches to the bottom of all tabs
        for cl in tab_layouts.values():
            cl.addStretch()

    def _make_process_handler(self, label: str):
        def h(): self.processRequested.emit(label)
        return h

    def _make_process_with_sliders_handler(self, label: str, panel: ParamControlPanel):
        def h(): self.processWithParamsRequested.emit(label, panel.get_current_params())
        return h

    def _make_process_with_kernel_handler(self, panel: 'CustomKernelPanel'):
        def h(): panel._emit_apply()
        return h
        
    def _make_process_with_params_handler(self, label: str):
        def h(params: dict): self.processWithParamsRequested.emit(label, params)
        return h

    def _make_animate_handler(self, label: str):
        def h(): self.animateRequested.emit(label)
        return h
        
    def _make_info_handler(self, label: str):
        def h(): self.infoRequested.emit(label)
        return h

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────
    def set_enabled(self, enabled: bool):
        """Enable/disable all buttons when an image loads or is cleared."""
        self.btn_reset.setEnabled(enabled)
        self.btn_apply.setEnabled(enabled)
        self.btn_save.setEnabled(enabled)
        for section in self._sections:
            section.set_buttons_enabled(enabled)
        for panel in self._custom_kernel_panels:
            panel.set_enabled(enabled)
