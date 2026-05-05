"""
theme.py — Centralized visual language for Image Browser.

Concept: "Pacific Chrome"
─────────────────────────
Inspired by the Teal+Orange/Coral color grade — the most iconic
photography LUT used in cinema and editorial photography.
Two opposing hues at maximum tension: deep aqua vs warm coral.

Light and vivid:
  • Backgrounds: open-water whites with aqua tint (instantly distinctive)
  • Primary accent: #0090A8 — vivid deep aqua (not teal, not cyan — in between)
  • Pop accent: #FF6040 — coral-orange for primary actions and badges
  • Text: near-black ocean ink (#021E28) — warm dark, not neutral gray
  • Hover: bright aqua wash — tangible and alive

Why this is NOT generic:
  • Pure cyan (#00FFFF) or pure teal (#008080) — both overused
  • #0090A8 sits between them at a specific saturation that reads as premium
  • Coral (#FF6040) as the action color is rare in tooling UIs
  • The combination directly references the photography/cinema color science
    context this app lives in
"""

# ─────────────────────────────────────────────
# COLOR TOKENS
# ─────────────────────────────────────────────
C_BG_DEEP    = "#E4F4F8"   # open-water light — vivid aqua tinted bg
C_BG_BASE    = "#EEF8FB"   # base panel — aqua-white
C_BG_SURFACE = "#FFFFFF"   # raised surface — clean white

C_BG_HOVER   = "#C4E8F0"   # bright aqua wash on hover
C_BG_ACTIVE  = "#9AD8E6"   # selected — deeper aqua, saturated

C_BORDER     = "#AADAE6"   # panel separators
C_BORDER_MID = "#6ABECF"   # visible border
C_BORDER_HI  = "#0090A8"   # focus ring — same as accent

# Primary accent — vivid deep aqua
C_ACCENT     = "#0090A8"
C_ACCENT_DIM = "#006B7E"   # deeper pressed / tree selection
C_ACCENT_HOT = "#00B0CC"   # brighter hover

# Pop accent — coral-orange (primary actions, badges)
C_POP        = "#FF6040"   # ← the coral moment
C_POP_DIM    = "#CC4020"   # pressed coral
C_POP_HOT    = "#FF7A5C"   # hover coral

# Text — warm ocean-ink family
C_TEXT_HI    = "#021E28"   # near-black with deep teal undertone
C_TEXT_MID   = "#0A4D60"   # dark ocean teal (panel labels, secondary)
C_TEXT_LOW   = "#3A8A9A"   # muted mid-teal (tertiary, hints)
C_TEXT_DEAD  = "#9CCDD8"   # disabled — clearly inactive

C_STATUS_OK  = "#1A9B5A"   # success green
C_STATUS_ERR = "#D43F3F"   # error red

# ─────────────────────────────────────────────
# FONT TOKENS
# ─────────────────────────────────────────────
FONT_DISPLAY = "Georgia"      # brand / header — serif presence
FONT_UI      = "Segoe UI"     # UI text — Windows-native
FONT_MONO    = "Consolas"     # data, filenames, status

# ─────────────────────────────────────────────
# SIZES
# ─────────────────────────────────────────────
RADIUS   = "4px"
RADIUS_L = "8px"


# ─────────────────────────────────────────────
# GLOBAL QSS
# ─────────────────────────────────────────────
def global_stylesheet() -> str:
    return f"""
/* ══ WINDOW & GENERAL ═══════════════════════════════════════════════════ */
QMainWindow, QWidget {{
    background-color: {C_BG_DEEP};
    color: {C_TEXT_HI};
    font-family: "{FONT_UI}";
    font-size: 14px;
}}

/* ══ PUSH BUTTONS ════════════════════════════════════════════════════════
   States:
     default  → white surface, dark teal text, aqua border
     hover    → bright aqua wash bg, accent text, accent border
     pressed  → accent fill, white text               ← vivid inversion
     disabled → base bg, dead text, no visible border
*/
QPushButton {{
    background: {C_BG_SURFACE};
    color: {C_TEXT_MID};
    border: 1px solid {C_BORDER_MID};
    border-radius: {RADIUS};
    padding: 5px 14px;
    font-family: "{FONT_UI}";
    font-size: 13px;
    letter-spacing: 0;
}}
QPushButton:hover {{
    background: {C_BG_HOVER};
    color: {C_ACCENT};
    border-color: {C_ACCENT};
}}
QPushButton:pressed {{
    background: {C_ACCENT};
    color: {C_BG_SURFACE};
    border-color: {C_ACCENT_DIM};
}}
QPushButton:disabled {{
    background: {C_BG_BASE};
    color: {C_TEXT_DEAD};
    border-color: {C_BORDER};
}}

/* ══ SPLITTER ════════════════════════════════════════════════════════════ */
QSplitter::handle {{
    background: {C_BORDER};
    width: 1px;
}}
QSplitter::handle:hover {{
    background: {C_ACCENT};
}}

/* ══ TREE VIEW ═══════════════════════════════════════════════════════════ */
QTreeView {{
    background-color: {C_BG_BASE};
    color: {C_TEXT_MID};
    border: none;
    font-family: "{FONT_UI}";
    font-size: 13px;
    outline: none;
    padding-top: 4px;
}}
QTreeView::item {{
    padding: 5px 8px;
    border-radius: 3px;
}}
QTreeView::item:hover {{
    background: {C_BG_HOVER};
    color: {C_TEXT_HI};
}}
QTreeView::item:selected {{
    background: {C_BG_ACTIVE};
    color: {C_ACCENT_DIM};
}}
QTreeView::branch {{ background: transparent; }}

/* ══ LIST VIEW ═══════════════════════════════════════════════════════════ */
QListView {{
    background-color: {C_BG_DEEP};
    border: none;
    outline: none;
    padding: 12px;
}}
QListView::item {{
    background: {C_BG_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: {RADIUS};
    padding: 4px;
    margin: 4px;
    color: {C_TEXT_LOW};
    font-family: "{FONT_UI}";
    font-size: 11px;
}}
QListView::item:hover {{
    background: {C_BG_HOVER};
    border-color: {C_BORDER_MID};
    color: {C_TEXT_MID};
}}
QListView::item:selected {{
    background: {C_BG_ACTIVE};
    border-color: {C_ACCENT};
    color: {C_ACCENT_DIM};
}}

/* ══ SCROLLBARS ══════════════════════════════════════════════════════════ */
QScrollBar:vertical {{
    background: {C_BG_BASE};
    width: 6px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {C_BORDER_MID};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {C_ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{
    background: {C_BG_BASE};
    height: 6px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {C_BORDER_MID};
    border-radius: 3px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{ background: {C_ACCENT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ══ STATUS BAR ══════════════════════════════════════════════════════════ */
QStatusBar {{
    background: {C_BG_BASE};
    color: {C_TEXT_LOW};
    border-top: 1px solid {C_BORDER};
    font-family: "{FONT_MONO}";
    font-size: 12px;
    padding: 0 8px;
}}
QStatusBar::item {{ border: none; }}

/* ══ TOOLTIP ══════════════════════════════════════════════════════════════ */
QToolTip {{
    background: {C_BG_SURFACE};
    color: {C_TEXT_HI};
    border: 1px solid {C_BORDER_MID};
    border-radius: {RADIUS};
    padding: 4px 8px;
    font-family: "{FONT_MONO}";
    font-size: 11px;
}}

/* ══ LABEL ════════════════════════════════════════════════════════════════ */
QLabel {{
    background: transparent;
    color: {C_TEXT_HI};
}}
"""
