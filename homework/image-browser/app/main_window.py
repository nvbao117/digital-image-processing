"""
main_window.py — MainWindow with 4-panel layout.

Layout (left → right)
──────────────────────
  ① Explorer    (1): Folder tree  +  [Open Folder] button IN panel header
  ② Collection  (2): Thumbnail grid + empty state
  ③ Preview     (2): Image canvas + info strip
  ④ Process     (1): Processing sidebar (registry-driven)

Header bar:
  FRAME / image browser  (branding only — no action buttons)
  Open Folder lives inside the Explorer panel header (logical UX).
  Close button removed — Windows frame handles it.
"""

import os

from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, Qt
from PyQt5.QtGui import QColor, QFont, QKeySequence, QPainter
from PyQt5.QtWidgets import (
    QFileDialog,
    QDialog,
    QTextEdit,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QShortcut,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .core.constants import (
    DEFAULT_DIR,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    WINDOW_TITLE,
)
from .theme import (
    C_ACCENT, C_ACCENT_DIM, C_ACCENT_HOT,
    C_BG_BASE, C_BG_DEEP, C_BG_HOVER, C_BG_SURFACE, C_BG_ACTIVE,
    C_BORDER, C_BORDER_MID,
    C_POP, C_POP_DIM, C_POP_HOT,
    C_TEXT_HI, C_TEXT_LOW, C_TEXT_MID,
    FONT_DISPLAY, FONT_MONO, FONT_UI,
)
from .widgets.folder_tree import FolderTree
from .widgets.preview_panel import PreviewPanel
from .widgets.thumbnail_grid import ThumbnailGrid
from .widgets.processing_sidebar import ProcessingSidebar
from .icons import IC, ICON_SIZE_SM, ICON_SIZE_MD, ICON_SIZE_LG

# 4-column ratio: Explorer : Collection : Preview : Process
SPLITTER_RATIO = (2, 3, 5, 3)


# ─────────────────────────────────────────────────────────────
# Header bar — branding only
# ─────────────────────────────────────────────────────────────
class HeaderBar(QWidget):
    """
    Thin branded strip at the top.
    No action buttons — Open Folder is in the Explorer panel header.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setStyleSheet(f"""
            HeaderBar {{
                background-color: {C_BG_SURFACE};
                border-bottom: 3px solid {C_ACCENT};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(0)

        brand = QLabel("FRAME")
        brand.setFont(QFont(FONT_DISPLAY, 19, QFont.Bold))
        brand.setStyleSheet(f"color: {C_ACCENT}; letter-spacing: 3px; background: transparent;")

        sub = QLabel("/ image browser")
        sub.setFont(QFont(FONT_MONO, 10))
        sub.setStyleSheet(f"color: {C_TEXT_LOW}; background: transparent; padding: 6px 0 0 8px;")

        layout.addWidget(brand)
        layout.addWidget(sub)
        layout.addStretch()

        hint = QLabel("Ctrl+O  ·  Open Folder")
        hint.setFont(QFont(FONT_UI, 11))
        hint.setStyleSheet(f"color: {C_TEXT_LOW}; background: transparent;")
        layout.addWidget(hint)


# ─────────────────────────────────────────────────────────────
# Shared panel header factory
# ─────────────────────────────────────────────────────────────
def _panel_header(title: str, right_widget: QWidget = None,
                  icon_func=None) -> QWidget:
    h = QWidget()
    h.setFixedHeight(36)
    h.setStyleSheet(f"""
        background: {C_BG_BASE};
        border-bottom: 1px solid {C_BORDER};
    """)
    hl = QHBoxLayout(h)
    hl.setContentsMargins(10, 0, 8, 0)
    hl.setSpacing(6)

    if icon_func:
        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon_func().pixmap(ICON_SIZE_SM))
        icon_lbl.setStyleSheet("background: transparent;")
        hl.addWidget(icon_lbl)

    # Short title text — no letter-spacing since icon already gives context
    lbl = QLabel(title)
    lbl.setFont(QFont(FONT_UI, 11, QFont.Medium if hasattr(QFont, 'Medium') else QFont.Normal))
    lbl.setStyleSheet(f"color: {C_TEXT_MID}; background: transparent;")
    hl.addWidget(lbl)
    hl.addStretch()

    if right_widget:
        hl.addWidget(right_widget)

    return h


# ─────────────────────────────────────────────────────────────
# Folder panel — Open Folder button lives HERE
# ─────────────────────────────────────────────────────────────
class FolderPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C_BG_BASE};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn_open = QPushButton("Open Folder")
        self.btn_open.setIcon(IC.folder_open())
        self.btn_open.setIconSize(ICON_SIZE_MD)
        self.btn_open.setFont(QFont(FONT_UI, 11, QFont.Bold))
        self.btn_open.setFixedHeight(24)
        self.btn_open.setToolTip("Open Folder  (Ctrl+O)")
        self.btn_open.setStyleSheet(f"""
            QPushButton {{
                background: {C_POP};
                color: #FFFFFF;
                border: none;
                border-radius: 3px;
                padding: 0 10px;
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
        """)

        layout.addWidget(_panel_header("EXPLORER", self.btn_open, IC.explorer))

        self.tree = FolderTree()
        layout.addWidget(self.tree)

    def set_root(self, path):
        self.tree.set_root(path)


# ─────────────────────────────────────────────────────────────
# Grid panel with empty state
# ─────────────────────────────────────────────────────────────
class GridEmptyState(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(f"background: {C_BG_DEEP};")

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Dot-grid
        dot_c = QColor(C_BORDER)
        dot_c.setAlpha(180)
        p.setPen(dot_c)
        sp = 36
        for x in range(0, w, sp):
            for y in range(0, h, sp):
                p.drawPoint(x, y)

        # 3 ghost thumbnail outlines
        thumb = 88
        gap   = 16
        total = 3 * thumb + 2 * gap
        ox    = (w - total) // 2
        cy_t  = h // 2 - thumb // 2 - 18

        rect_c   = QColor(C_BG_SURFACE)
        border_c = QColor(C_BORDER_MID)
        cross_c  = QColor(C_BORDER_MID)

        for i in range(3):
            x = ox + i * (thumb + gap)
            p.setBrush(rect_c)
            p.setPen(border_c)
            p.drawRoundedRect(x, cy_t, thumb, thumb, 4, 4)
            mx, my = x + thumb // 2, cy_t + thumb // 2
            p.setPen(cross_c)
            p.drawLine(mx - 10, my, mx + 10, my)
            p.drawLine(mx, my - 10, mx, my + 10)

        p.setPen(QColor(C_TEXT_LOW))
        f = QFont(FONT_MONO, 8)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        p.setFont(f)
        p.drawText(0, cy_t + thumb + 18, w, 20, Qt.AlignCenter,
                   "SELECT A FOLDER TO BROWSE IMAGES")
        p.end()


class GridPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C_BG_DEEP};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.count_badge = QLabel("")
        self.count_badge.setFont(QFont(FONT_MONO, 8))
        self.count_badge.setStyleSheet(f"""
            color: #FFFFFF;
            background: {C_POP};
            border: none;
            border-radius: 9px;
            padding: 1px 8px;
        """)
        self.count_badge.setVisible(False)
        layout.addWidget(_panel_header("COLLECTION", self.count_badge, IC.collection))

        self._stack = QWidget()
        self._stack.setStyleSheet(f"background: {C_BG_DEEP};")
        self._sl = QVBoxLayout(self._stack)
        self._sl.setContentsMargins(0, 0, 0, 0)

        self._empty = GridEmptyState()
        self.grid   = ThumbnailGrid()
        self.grid.setVisible(False)
        self._sl.addWidget(self._empty)
        self._grid_visible = False

        layout.addWidget(self._stack)

    def update_count(self, folder: str, count: int):
        if count > 0:
            self.count_badge.setText(f"{count} frames")
            self.count_badge.setVisible(True)
            self._show_grid()
        else:
            self.count_badge.setVisible(False)
            self._show_empty()

    def _show_grid(self):
        if not self._grid_visible:
            self._sl.removeWidget(self._empty)
            self._empty.setVisible(False)
            self._sl.addWidget(self.grid)
            self.grid.setVisible(True)
            self._grid_visible = True

    def _show_empty(self):
        if self._grid_visible:
            self._sl.removeWidget(self.grid)
            self.grid.setVisible(False)
            self._sl.addWidget(self._empty)
            self._empty.setVisible(True)
            self._grid_visible = False


# ─────────────────────────────────────────────────────────────
# Main Window
# ─────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(IC.app())
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self.setUnifiedTitleAndToolBarOnMac(False)

        self._build_ui()
        self._wire_signals()
        self._animate_startup()

        self.statusBar().showMessage("Ready  ·  Select a folder to begin")
        self.folder_panel.set_root(DEFAULT_DIR)

    def _build_ui(self):
        root = QWidget()
        rl = QVBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        self.setCentralWidget(root)

        self.header = HeaderBar()
        rl.addWidget(self.header)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        rl.addWidget(splitter)

        self.folder_panel = FolderPanel()
        self.grid_panel   = GridPanel()
        self.preview      = PreviewPanel()
        self.sidebar      = ProcessingSidebar()

        splitter.addWidget(self.folder_panel)
        splitter.addWidget(self.grid_panel)
        splitter.addWidget(self.preview)
        splitter.addWidget(self.sidebar)

        for i in range(4):
            splitter.setCollapsible(i, False)

        total = sum(SPLITTER_RATIO)
        sizes = [int(DEFAULT_WIDTH * w / total) for w in SPLITTER_RATIO]
        splitter.setSizes(sizes)

    def _wire_signals(self):
        # Open Folder is now in FolderPanel
        self.folder_panel.btn_open.clicked.connect(self._on_open_folder)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self._on_open_folder)

        tree = self.folder_panel.tree
        grid = self.grid_panel.grid

        tree.folderSelected.connect(grid.load_folder)
        tree.folderSelected.connect(self._on_folder_changed)
        grid.imageSelected.connect(self._on_image_selected)
        grid.folderLoaded.connect(self.grid_panel.update_count)
        grid.folderLoaded.connect(self._on_folder_loaded)

        self.preview.image_canvas.roiChanged.connect(self._on_roi_changed)

        self.sidebar.resetRequested.connect(self._on_reset)
        self.sidebar.applyRequested.connect(self._on_apply)
        self.sidebar.saveRequested.connect(self._on_save)
        self.sidebar.processRequested.connect(self._on_process)
        self.sidebar.processWithParamsRequested.connect(self._on_process_with_params)
        self.sidebar.animateRequested.connect(self._on_animate)
        self.sidebar.infoRequested.connect(self._on_info)
        
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._on_save)

    def _animate_startup(self):
        self.setWindowOpacity(0.0)
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(400)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._startup_anim = anim

    # ──────────────────────────────────────────
    def _on_open_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Image Folder", DEFAULT_DIR, QFileDialog.ShowDirsOnly,
        )
        if not folder:
            return
        self.folder_panel.set_root(folder)
        self.grid_panel.grid.load_folder(folder)
        self.preview.clear()
        self.sidebar.set_enabled(False)
        self._on_folder_changed(folder)

    def _on_image_selected(self, path: str):
        self._current_proc_label = None
        self._current_proc_params = None
        self._last_processed_cv = None
        self.preview.show_image(path)
        self.sidebar.set_enabled(True)

    def _on_folder_changed(self, folder: str):
        self.preview.clear()
        self.sidebar.set_enabled(False)
        self.statusBar().showMessage(f"→  {folder.replace(chr(92), '/')}")

    def _on_folder_loaded(self, folder: str, count: int):
        name = os.path.basename(folder.rstrip(os.sep)) or folder
        noun = "frame" if count == 1 else "frames"
        self.statusBar().showMessage(f"→  {name}   ·   {count} {noun}")

    def _on_reset(self):
        self._current_proc_label = None
        self._current_proc_params = None
        self._last_processed_cv = None
        self.preview.reset_to_original()

    def _on_apply(self):
        if hasattr(self, '_last_processed_cv') and self._last_processed_cv is not None:
            self.preview.commit_processed_image(self._last_processed_cv)
            self._current_proc_label = None
            self._current_proc_params = None
            self._last_processed_cv = None

    def _on_roi_changed(self):
        if not hasattr(self, '_current_proc_label') or not self._current_proc_label:
            return
        if hasattr(self, '_current_proc_params') and self._current_proc_params is not None:
            self._on_process_with_params(self._current_proc_label, self._current_proc_params)
        else:
            self._on_process(self._current_proc_label)

    def _blend_with_roi(self, original, processed):
        import numpy as np
        import cv2
        mask = self.preview.image_canvas.get_image_mask()
        if mask is None:
            return processed
            
        if original.ndim == 3 and mask.ndim == 2:
            mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            
        mask_f = mask.astype(np.float32) / 255.0
        
        if original.ndim == 3 and processed.ndim == 2:
            processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
        elif original.ndim == 2 and processed.ndim == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            
        blended = (processed.astype(np.float32) * mask_f + original.astype(np.float32) * (1.0 - mask_f))
        return np.clip(blended, 0, 255).astype(np.uint8)

    def _on_process(self, label: str):
        img = self.preview.cv_image
        if img is None:
            return
        from .processors.base import get_processor
        proc = get_processor(label)
        if proc:
            self._current_proc_label = label
            self._current_proc_params = None
            res = proc.apply(img)
            self._last_processed_cv = self._blend_with_roi(img, res)
            self.preview.display_cv(self._last_processed_cv)

    def _on_process_with_params(self, label: str, params: dict):
        img = self.preview.cv_image
        if img is None:
            return
        from .processors.base import get_processor
        proc = get_processor(label)
        if proc:
            self._current_proc_label = label
            self._current_proc_params = params
            res = proc.apply(img, **params)
            self._last_processed_cv = self._blend_with_roi(img, res)
            self.preview.display_cv(self._last_processed_cv)

    def _on_animate(self, label: str):
        self.preview.start_rotate()

    def _on_save(self):
        img = self.preview.cv_image
        if img is None:
            return
            
        default_name = "processed_image.jpg"
        if hasattr(self.preview, 'current_path') and self.preview.current_path:
            base, ext = os.path.splitext(os.path.basename(self.preview.current_path))
            default_name = f"{base}_processed{ext}"
            
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", os.path.join(DEFAULT_DIR, default_name),
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not path:
            return
            
        import cv2
        cv2.imwrite(path, img)
        self.statusBar().showMessage(f"✓  Saved: {os.path.basename(path)}")

    def _on_info(self, label: str):
        from .processors.base import get_processor
        import inspect
        
        proc = get_processor(label)
        if not proc:
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Info: {proc.label}")
        dialog.resize(600, 450)
        dialog.setStyleSheet(f"background: {C_BG_DEEP}; color: {C_TEXT_HI};")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        
        title = QLabel(f"{proc.label} ({proc.category})")
        title.setFont(QFont(FONT_UI, 14, QFont.Bold))
        title.setStyleSheet(f"color: {C_ACCENT};")
        layout.addWidget(title)
        
        desc = QLabel(proc.tooltip or "No description available.")
        desc.setFont(QFont(FONT_UI, 11))
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {C_TEXT_MID};")
        layout.addWidget(desc)
        
        layout.addSpacing(10)
        code_lbl = QLabel("Source Code:")
        code_lbl.setFont(QFont(FONT_UI, 10, QFont.Bold))
        layout.addWidget(code_lbl)
        
        try:
            source = inspect.getsource(proc.__class__)
        except Exception as e:
            source = f"# Could not load source code:\n{e}"
            
        code_view = QTextEdit()
        code_view.setReadOnly(True)
        code_view.setFont(QFont(FONT_MONO, 10))
        code_view.setStyleSheet(f"""
            QTextEdit {{
                background: {C_BG_BASE}; 
                color: {C_TEXT_MID}; 
                border: 1px solid {C_BORDER};
                padding: 8px;
                border-radius: 4px;
            }}
        """)
        code_view.setPlainText(source)
        layout.addWidget(code_view, stretch=1)
        
        layout.addSpacing(10)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_BG_SURFACE}; 
                color: {C_TEXT_HI}; 
                padding: 6px; 
                border: 1px solid {C_BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {C_BG_HOVER};
            }}
        """)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec_()
