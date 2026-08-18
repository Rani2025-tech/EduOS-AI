"""
EduOS-AI — Design System  (ui_components.py)
=============================================
Single source of truth for all visual styling and reusable UI components.

Structure
---------
Part 1  Color tokens + inject_global_styles()
Part 2  Typography / layout helpers
Part 3  Data-display components  (KPI card, status badge, health card)
Part 4  Intelligence components  (alert card, insight card)
Part 5  Copilot + utility components + backward-compat aliases

Rules
-----
- No business logic.
- No database calls.
- No Streamlit session-state reads.
- Pure presentation: accept plain Python values, render HTML/CSS.
"""

import html
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — COLOR SYSTEM & GLOBAL STYLES
# ══════════════════════════════════════════════════════════════════════════════

# ── Primitive color tokens ────────────────────────────────────────────────────
# Every color used anywhere in the design system is defined exactly once here.

C: dict = {
    # Brand
    "navy":         "#17365D",   # primary brand / headings
    "blue":         "#2563EB",   # interactive / links / active states
    "blue_hover":   "#1D4ED8",   # button hover
    "blue_light":   "#EFF6FF",   # blue tint background
    "blue_mid":     "#DBEAFE",   # blue tint border / soft blue border
    "blue_border":  "#93C5FD",   # secondary button border

    # Backgrounds
    "bg":           "#F5F7FA",   # page background
    "bg_subtle":    "#F1F5F9",   # slightly darker surface (zebra rows, etc.)
    "surface":      "#FFFFFF",   # card / panel surface

    # Borders
    "border":       "#D9E2EC",   # default border
    "border_light": "#E6EDF5",   # light divider
    "border_dark":  "#C7D2E0",   # stronger border (inputs)

    # Text
    "text":         "#17365D",   # primary text (dark navy)
    "text_body":    "#5B6B7F",   # body text
    "text_muted":   "#5B6B7F",   # secondary / label text
    "text_light":   "#7A8797",   # placeholder / tertiary text

    # Semantic — success (green)
    "success":      "#16A34A",
    "success_bg":   "#ECFDF3",
    "success_bd":   "#BBF7D0",

    # Semantic — warning (amber)
    "warning":      "#D97706",
    "warning_bg":   "#FFF7ED",
    "warning_bd":   "#FED7AA",

    # Semantic — danger / critical (red)
    "danger":       "#DC2626",
    "danger_bg":    "#FEF2F2",
    "danger_bd":    "#FECACA",

    # Semantic — info (blue)
    "info":         "#2563EB",
    "info_bg":      "#EFF6FF",
    "info_bd":      "#DBEAFE",

    # Semantic — high / orange (between warning and danger)
    "high":         "#C2410C",
    "high_bg":      "#FFF7ED",
    "high_bd":      "#FED7AA",

    # Purple (for copilot / AI accent)
    "purple":       "#7C3AED",
    "purple_bg":    "#F5F3FF",
    "purple_bd":    "#DDD6FE",
}

# ── Semantic severity → (foreground, background, border) ─────────────────────
# Used by insight cards, alert cards, and any severity-aware component.
SEV_COLORS: dict = {
    "critical": (C["danger"],  C["danger_bg"],  C["danger_bd"]),
    "warning":  (C["warning"], C["warning_bg"], C["warning_bd"]),
    "info":     (C["success"], C["success_bg"], C["success_bd"]),
}

SEV_LABEL: dict = {
    "critical": "Critical",
    "warning":  "Warning",
    "info":     "Healthy",
}

# ── Staffing pressure level → (foreground, background, border) ───────────────
LEVEL_COLORS: dict = {
    "LOW":      (C["success"], C["success_bg"], C["success_bd"]),
    "MODERATE": (C["warning"], C["warning_bg"], C["warning_bd"]),
    "HIGH":     (C["high"],    C["high_bg"],    C["high_bd"]),
    "CRITICAL": (C["danger"],  C["danger_bg"],  C["danger_bd"]),
}

# ── Analytics category → display label ───────────────────────────────────────
CAT_LABEL: dict = {
    "attendance": "Attendance",
    "fees":       "Fee Collection",
    "academic":   "Academic Performance",
    "documents":  "Documents",
    "timetable":  "Timetable",
}

# ── Badge level → (foreground, background, border) ───────────────────────────
BADGE_PALETTE: dict = {
    "success": (C["success"], C["success_bg"], C["success_bd"]),
    "warning": (C["warning"], C["warning_bg"], C["warning_bd"]),
    "danger":  (C["danger"],  C["danger_bg"],  C["danger_bd"]),
    "info":    (C["info"],    C["info_bg"],    C["info_bd"]),
    "neutral": (C["text_muted"], C["bg_subtle"], C["border"]),
}


# ── Global CSS ────────────────────────────────────────────────────────────────

def inject_global_styles() -> None:
    """
    Injects the complete EduOS-AI light-enterprise CSS into the Streamlit page.
    Call once at the top of app.py, after st.set_page_config().

    Covers:
      - Page background and base typography (bright #F7F9FC)
      - Streamlit top chrome (white, no dark bar)
      - Sidebar (white background, dark navy text, blue active state)
      - Main content container width and padding
      - st.metric cards
      - Buttons (default secondary + primary blue)
      - Tabs
      - Dataframes
      - Text inputs, text areas, select boxes
      - Streamlit alert/callout boxes
      - Expanders
      - Horizontal rules
      - Chat messages
      - Progress bars
      - Spinners
      - File uploaders
    """
    st.markdown(f"""
<style>
/* ── 1. Font + page base ──────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {{
    font-family: Inter, ui-sans-serif, system-ui, -apple-system,
                 BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
.stApp {{
    background-color: {C['bg']};
    color: {C['text']};
}}

/* ── 2. Streamlit top chrome — remove dark bar ───────────────────────────── */
header[data-testid="stHeader"] {{
    background-color: {C['surface']} !important;
    border-bottom: 1px solid {C['border']} !important;
    box-shadow: none !important;
}}
header[data-testid="stHeader"] * {{
    color: {C['text']} !important;
}}

/* ── 3. Main content container ───────────────────────────────────────────── */
.main .block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2.5rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 1280px;
}}

/* ── 4. Sidebar — white, dark text, blue active nav ──────────────────────── */
section[data-testid="stSidebar"] {{
    background-color: {C['surface']} !important;
    border-right: 1px solid {C['border']} !important;
    min-width: 240px;
}}
section[data-testid="stSidebar"] * {{
    color: {C['text']} !important;
}}
/* Section label headings (Persona / Navigation) */
section[data-testid="stSidebar"] .stRadio > label,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
    color: {C['text_muted']} !important;
    margin: 16px 0 6px 0 !important;
}}
/* Nav radio items */
section[data-testid="stSidebar"] .stRadio label span {{
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: {C['text']} !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
}}
/* Sidebar dividers */
section[data-testid="stSidebar"] hr {{
    border-color: {C['border']} !important;
    margin: 10px 0 !important;
}}
/* Sidebar selectbox */
section[data-testid="stSidebar"] .stSelectbox label {{
    color: {C['text_muted']} !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}}
section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {{
    background: {C['bg']} !important;
    border-color: {C['border']} !important;
}}
/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {{
    background: {C['bg']} !important;
    color: {C['text']} !important;
    border: 1px solid {C['border']} !important;
    width: 100% !important;
    font-size: 0.8rem !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: {C['blue_light']} !important;
    border-color: {C['blue']} !important;
    color: {C['blue']} !important;
}}
/* Sidebar expander */
section[data-testid="stSidebar"] .streamlit-expanderHeader {{
    background: {C['bg']} !important;
    border-color: {C['border']} !important;
    color: {C['text']} !important;
    font-size: 0.8rem !important;
}}

/* ── 4. st.metric cards ──────────────────────────────────────────────────── */
div[data-testid="metric-container"] {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.04);
}}
div[data-testid="stMetricLabel"] {{
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    color: {C['text_muted']} !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}}
div[data-testid="stMetricValue"] {{
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    color: {C['navy']} !important;
    line-height: 1.15 !important;
}}
div[data-testid="stMetricDelta"] {{
    font-size: 0.75rem !important;
    font-weight: 600 !important;
}}

/* ── 5. Buttons ──────────────────────────────────────────────────────────── */
.stButton > button {{
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.875rem;
    padding: 8px 16px;
    border: 1px solid {C['border_dark']};
    background: {C['surface']};
    color: {C['text']};
    transition: border-color 0.15s, color 0.15s, background 0.15s;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}}
.stButton > button:hover {{
    border-color: {C['blue']};
    color: {C['blue']};
    background: {C['blue_light']};
    box-shadow: none;
}}
.stButton > button:focus {{
    outline: 2px solid {C['blue']};
    outline-offset: 2px;
}}
/* Primary variant — Streamlit uses kind="primary" */
.stButton > button[kind="primary"] {{
    background: {C['blue']};
    color: #ffffff;
    border-color: {C['blue']};
}}
.stButton > button[kind="primary"]:hover {{
    background: {C['blue_hover']};
    border-color: {C['blue_hover']};
    color: #ffffff;
}}

/* ── 6. Tabs ─────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background: {C['surface']};
    border-bottom: 2px solid {C['border']};
    gap: 0;
    padding: 0;
}}
.stTabs [data-baseweb="tab"] {{
    font-size: 0.875rem;
    font-weight: 500;
    color: {C['text_muted']};
    padding: 10px 20px;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    background: transparent;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: {C['text']};
    background: {C['bg_subtle']};
}}
.stTabs [aria-selected="true"] {{
    color: {C['blue']} !important;
    border-bottom: 2px solid {C['blue']} !important;
    font-weight: 600 !important;
    background: transparent !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 16px;
}}

/* ── 7. Dataframes ───────────────────────────────────────────────────────── */
.stDataFrame {{
    border: 1px solid {C['border']};
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.stDataFrame thead tr th {{
    background: {C['bg_subtle']} !important;
    color: {C['text_muted']} !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    border-bottom: 1px solid {C['border']} !important;
}}
.stDataFrame tbody tr:nth-child(even) {{
    background: {C['bg_subtle']} !important;
}}
.stDataFrame tbody tr:hover {{
    background: {C['blue_light']} !important;
}}

/* ── 8. Forms & Inputs ───────────────────────────────────────────────────── */
div[data-testid="stForm"] {{
    background: {C['surface']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 12px !important;
    padding: 24px 28px !important;
    box-shadow: 0 4px 20px -2px rgba(23, 54, 93, 0.06), 0 2px 6px -1px rgba(23, 54, 93, 0.03) !important;
}}

div[data-baseweb="input"] {{
    border: 1px solid {C['border_dark']} !important;
    border-radius: 8px !important;
    background: {C['surface']} !important;
    transition: border-color 0.15s, box-shadow 0.15s;
}}
div[data-baseweb="input"]:focus-within {{
    border-color: {C['blue']} !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
}}
div[data-baseweb="input"] > input {{
    color: {C['text']} !important;
    font-size: 0.875rem !important;
    padding: 8px 12px !important;
}}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
    color: {C['text']} !important;
    font-size: 0.875rem !important;
}}
.stTextArea > div > div > textarea {{
    border: 1px solid {C['border_dark']} !important;
    border-radius: 8px !important;
    background: {C['surface']} !important;
    padding: 10px 12px !important;
    transition: border-color 0.15s, box-shadow 0.15s;
}}
.stTextArea > div > div > textarea:focus {{
    border-color: {C['blue']} !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
}}
.stSelectbox [data-baseweb="select"] > div {{
    border: 1px solid {C['border_dark']} !important;
    border-radius: 8px !important;
    background: {C['surface']} !important;
    font-size: 0.875rem !important;
}}
.stSelectbox label,
.stTextInput label,
.stTextArea label,
.stFileUploader label {{
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: {C['text_muted']} !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-bottom: 4px !important;
}}

/* ── 9. Streamlit native alerts ──────────────────────────────────────────── */
.stAlert {{
    border-radius: 8px !important;
    font-size: 0.875rem !important;
    border-left-width: 4px !important;
}}

/* ── 10. Expanders ───────────────────────────────────────────────────────── */
.streamlit-expanderHeader {{
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    color: {C['text']} !important;
    background: {C['surface']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 6px !important;
    padding: 10px 14px !important;
}}
.streamlit-expanderHeader:hover {{
    background: {C['bg_subtle']} !important;
}}
.streamlit-expanderContent {{
    border: 1px solid {C['border']} !important;
    border-top: none !important;
    border-radius: 0 0 6px 6px !important;
    background: {C['surface']} !important;
    padding: 12px 14px !important;
}}

/* ── 11. Horizontal rules ────────────────────────────────────────────────── */
hr {{
    border: none !important;
    border-top: 1px solid {C['border']} !important;
    margin: 20px 0 !important;
}}

/* ── 12. Chat messages ───────────────────────────────────────────────────── */
.stChatMessage {{
    background: {C['surface']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    margin-bottom: 8px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}}
.stChatMessage [data-testid="chatAvatarIcon-user"] {{
    background: {C['blue']} !important;
}}
.stChatMessage [data-testid="chatAvatarIcon-assistant"] {{
    background: {C['navy']} !important;
}}

/* ── 13. Progress bars ───────────────────────────────────────────────────── */
.stProgress > div > div > div > div {{
    background-color: {C['blue']} !important;
    border-radius: 4px !important;
}}
.stProgress > div > div {{
    background-color: {C['border']} !important;
    border-radius: 4px !important;
}}

/* ── 14. Spinners ────────────────────────────────────────────────────────── */
.stSpinner > div {{
    border-top-color: {C['blue']} !important;
}}

/* ── 15. File uploader ───────────────────────────────────────────────────── */
.stFileUploader > div {{
    border: 2px dashed {C['border_dark']} !important;
    border-radius: 8px !important;
    background: {C['bg']} !important;
    padding: 20px !important;
    transition: border-color 0.15s;
}}
.stFileUploader > div:hover {{
    border-color: {C['blue']} !important;
    background: {C['blue_light']} !important;
}}

/* ── 16. Headings in main content ────────────────────────────────────────── */
.main h1 {{
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: {C['navy']} !important;
    letter-spacing: -0.02em !important;
}}
.main h2 {{
    font-size: 1.3rem !important;
    font-weight: 700 !important;
    color: {C['navy']} !important;
    letter-spacing: -0.01em !important;
}}
.main h3 {{
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: {C['navy']} !important;
}}
.main p, .main li {{
    font-size: 0.9rem !important;
    color: {C['text']} !important;
    line-height: 1.6 !important;
}}

/* ── 17. Code blocks ─────────────────────────────────────────────────────── */
.stCodeBlock {{
    border: 1px solid {C['border']} !important;
    border-radius: 6px !important;
    background: {C['bg_subtle']} !important;
    font-size: 0.8rem !important;
}}

/* ── 18. Captions ────────────────────────────────────────────────────────── */
.stCaption, [data-testid="stCaptionContainer"] {{
    font-size: 0.78rem !important;
    color: {C['text_muted']} !important;
}}

/* ── 19. Checkbox / radio in main content ────────────────────────────────── */
.main .stCheckbox label span,
.main .stRadio label span {{
    font-size: 0.875rem !important;
    color: {C['text']} !important;
}}

/* ── 20. Scrollbar (webkit) ──────────────────────────────────────────────── */
::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}
::-webkit-scrollbar-track {{
    background: {C['bg']};
}}
::-webkit-scrollbar-thumb {{
    background: {C['border_dark']};
    border-radius: 3px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: {C['text_light']};
}}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — TYPOGRAPHY & LAYOUT HELPERS
# ══════════════════════════════════════════════════════════════════════════════


def render_page_header(title: str, subtitle: str = "") -> None:
    """
    Renders the top-of-page title block.

    Parameters
    ----------
    title    : Main page title (e.g. "Dashboard", "AI Document Reader")
    subtitle : Optional one-line description shown below the title

    Visual structure
    ----------------
    [Title]
    [Subtitle]
    ─────────────────────────────────────────────
    """
    sub_html = (
        f'<p style="margin:5px 0 0;font-size:0.875rem;'
        f'color:{C["text_muted"]};line-height:1.4;">{subtitle}</p>'
        if subtitle else ""
    )
    st.markdown(
        f"""
<div style="margin-bottom:20px;padding-bottom:16px;
            border-bottom:1px solid {C['border']};">
    <h2 style="margin:0;font-size:1.4rem;font-weight:700;
               color:{C['navy']};letter-spacing:-0.02em;">{title}</h2>
    {sub_html}
</div>
""",
        unsafe_allow_html=True,
    )


def render_section_header(title: str, description: str = "") -> None:
    """
    Renders a mid-page section heading.

    Parameters
    ----------
    title       : Section title (e.g. "Operational Health", "AI Insights")
    description : Optional short description shown below the title

    Visual structure
    ----------------
    Section Title
    [Optional description]
    """
    desc_html = (
        f'<p style="margin:3px 0 0;font-size:0.8rem;'
        f'color:{C["text_muted"]};">{description}</p>'
        if description else ""
    )
    st.markdown(
        f"""
<div style="margin:24px 0 14px;">
    <h3 style="margin:0;font-size:1rem;font-weight:700;
               color:{C['navy']};letter-spacing:-0.01em;">{title}</h3>
    {desc_html}
</div>
""",
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, description: str, icon: str = "") -> None:
    """
    Renders a professional empty-state placeholder.

    Use this whenever a data list is empty or the database is disconnected.
    Never pass fabricated numbers — only call this when data is genuinely absent.

    Parameters
    ----------
    title       : Short label, e.g. "No student data available"
    description : Guidance text, e.g. "Connect the school database to view records."
    icon        : Optional single character or short text shown above the title

    Example output
    --------------
    ┌─────────────────────────────────────────┐
    │                                         │
    │              (icon)                     │
    │   No student data available             │
    │   Connect the school database to view   │
    │   live student records.                 │
    │                                         │
    └─────────────────────────────────────────┘
    """
    icon_html = (
        f'<div style="font-size:1.5rem;margin-bottom:10px;'
        f'color:{C["text_light"]};">{icon}</div>'
        if icon else ""
    )
    st.markdown(
        f'<div style="background:{C["surface"]};border:1px solid {C["border"]};border-radius:8px;padding:40px 24px;text-align:center;margin:8px 0;box-shadow:0 1px 2px rgba(0,0,0,0.04);">'
        f'{icon_html}'
        f'<div style="font-size:0.95rem;font-weight:600;color:{C["text_muted"]};margin-bottom:6px;">{title}</div>'
        f'<div style="font-size:0.82rem;color:{C["text_body"]};max-width:360px;margin:0 auto;line-height:1.5;">{description}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PART 3 — DATA DISPLAY COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════


def render_status_badge(text: str, level: str = "neutral") -> str:
    """
    Returns an inline HTML badge string (does NOT call st.markdown itself).
    Embed the return value inside a larger HTML block.

    Parameters
    ----------
    text  : Badge label, e.g. "Healthy", "Critical", "3 Active Alerts"
    level : "success" | "warning" | "danger" | "info" | "neutral"

    Returns
    -------
    str — self-contained <span> HTML element

    Usage
    -----
    badge = render_status_badge("Healthy", "success")
    st.markdown(f"Status: {badge}", unsafe_allow_html=True)

    Design
    ------
    - Pill shape with 4px border-radius (not fully rounded — enterprise style)
    - Color communicates meaning; text label also communicates meaning
    - No color-only reliance (accessibility)
    - Dot prefix for quick visual scanning
    """
    fg, bg, bd = BADGE_PALETTE.get(level, BADGE_PALETTE["neutral"])

    # Dot indicator prefix — provides non-color meaning signal
    dot_color = fg
    dot = f'<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:{dot_color};margin-right:5px;vertical-align:middle;"></span>'

    return (
        f'<span style="display:inline-flex;align-items:center;'
        f'padding:3px 10px;border-radius:4px;'
        f'font-size:0.72rem;font-weight:700;'
        f'color:{fg};background:{bg};border:1px solid {bd};'
        f'letter-spacing:0.03em;white-space:nowrap;">'
        f'{dot}{text}</span>'
    )


def render_kpi_card(
    label: str,
    value: str,
    description: str = "",
    status: str = "",
) -> None:
    """
    Renders a standalone KPI metric card.

    Parameters
    ----------
    label       : Short uppercase label, e.g. "ENROLLED STUDENTS"
    value       : Primary metric value, e.g. "1,248" or "Data unavailable"
    description : Supporting line below the value, e.g. "Active records"
    status      : "good" | "warning" | "danger" | "" (neutral)

    Design
    ------
    ┌──────────────────────────────┐
    │ LABEL                        │
    │                              │
    │ 1,248                        │
    │ Active records               │  ← colored by status
    └──────────────────────────────┘

    Empty-state contract
    --------------------
    If value is "Data unavailable", description should explain why.
    Never pass fabricated numbers.
    """
    status_fg = {
        "good":    C["success"],
        "warning": C["warning"],
        "danger":  C["danger"],
        "":        C["text_muted"],
    }.get(status, C["text_muted"])

    # Left accent bar color
    accent = {
        "good":    C["success"],
        "warning": C["warning"],
        "danger":  C["danger"],
        "":        C["border"],
    }.get(status, C["border"])

    desc_html = (
        f'<div style="font-size:0.75rem;font-weight:600;'
        f'color:{status_fg};margin-top:4px;line-height:1.3;">{description}</div>'
        if description else ""
    )

    st.markdown(
        f"""
<div style="background:{C['surface']};border:1px solid {C['border']};
            border-left:3px solid {accent};border-radius:8px;
            padding:16px 20px;
            box-shadow:0 1px 3px rgba(0,0,0,0.05),0 1px 2px rgba(0,0,0,0.04);">
    <div style="font-size:0.7rem;font-weight:700;color:{C['text_muted']};
                text-transform:uppercase;letter-spacing:0.07em;
                margin-bottom:8px;">{label}</div>
    <div style="font-size:1.75rem;font-weight:700;color:{C['navy']};
                line-height:1.1;letter-spacing:-0.02em;">{value}</div>
    {desc_html}
</div>
""",
        unsafe_allow_html=True,
    )


def render_health_card(
    title: str,
    status_label: str,
    metric: str,
    detail: str,
    level: str = "LOW",
) -> None:
    """
    Renders a compact operational health card.
    Used in the "Operational Health" dashboard section.

    Parameters
    ----------
    title        : Module name, e.g. "Attendance", "Staffing", "Timetable"
    status_label : Short status text, e.g. "Healthy", "High Risk", "2 Conflicts"
    metric       : Primary metric line, e.g. "86 / 90 teachers available"
    detail       : Supporting detail, e.g. "4 teachers unavailable today"
    level        : "LOW" | "MODERATE" | "HIGH" | "CRITICAL"
                   Controls the status badge color.

    Design
    ------
    ┌──────────────────────────────────────────┐
    │ ATTENDANCE                    [Healthy]  │
    │                                          │
    │ 91.2% average                            │
    │ 2 students below 75% threshold           │
    └──────────────────────────────────────────┘
    """
    fg, bg, bd = LEVEL_COLORS.get(level.upper(), LEVEL_COLORS["LOW"])

    st.markdown(
        f"""
<div style="background:{C['surface']};border:1px solid {C['border']};
            border-radius:8px;padding:16px 18px;
            box-shadow:0 1px 3px rgba(0,0,0,0.05);">
    <div style="display:flex;justify-content:space-between;
                align-items:center;margin-bottom:10px;">
        <span style="font-size:0.72rem;font-weight:700;color:{C['text_muted']};
                     text-transform:uppercase;letter-spacing:0.07em;">{title}</span>
        <span style="padding:3px 10px;border-radius:4px;
                     font-size:0.7rem;font-weight:700;
                     color:{fg};background:{bg};border:1px solid {bd};">
            {status_label}
        </span>
    </div>
    <div style="font-size:1.1rem;font-weight:700;color:{C['navy']};
                margin-bottom:4px;line-height:1.2;">{metric}</div>
    <div style="font-size:0.78rem;color:{C['text_body']};
                line-height:1.4;">{detail}</div>
</div>
""",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PART 4 — INTELLIGENCE COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════


def render_alert_card(alert: dict) -> None:
    """
    Renders a single proactive alert card.

    Parameters
    ----------
    alert : dict with keys from the existing alert schema:
        - title    (str)  : Alert title
        - message  (str)  : Alert body text
        - priority (str)  : "high" | "critical" | "medium" | "low"
        - action   (str)  : Optional recommended action text
        - type     (str)  : Optional alert type label

    Priority → visual level mapping
    --------------------------------
    high / critical  →  danger  (red left border)
    medium           →  warning (amber left border)
    low              →  info    (blue left border)

    Design
    ------
    ┌─────────────────────────────────────────────────────┐
    │ Alert Title                        [High Priority]  │
    │                                                     │
    │ Alert message body text here.                       │
    │                                                     │
    │ Action required: Send warning notice to parent.     │
    └─────────────────────────────────────────────────────┘
    """
    priority = str(alert.get("priority", "medium")).lower()

    # Map priority → severity vocabulary
    sev_map = {
        "critical": "critical",
        "high":     "critical",
        "medium":   "warning",
        "low":      "info",
    }
    sev = sev_map.get(priority, "warning")
    fg, bg, bd = SEV_COLORS.get(sev, SEV_COLORS["warning"])

    # Priority badge label
    badge_label_map = {
        "critical": "Critical",
        "high":     "High Priority",
        "medium":   "Medium Priority",
        "low":      "Low Priority",
    }
    badge_level_map = {
        "critical": "danger",
        "high":     "danger",
        "medium":   "warning",
        "low":      "info",
    }
    badge_html = render_status_badge(
        badge_label_map.get(priority, "Alert"),
        badge_level_map.get(priority, "warning"),
    )

    action = html.escape(str(alert.get("action", "")).strip())
    action_html = (
        f'<div style="font-size:0.78rem;color:{C["info"]};'
        f'border-top:1px solid {C["border"]};'
        f'padding-top:8px;margin-top:10px;line-height:1.4;">'
        f'<strong>Action required:</strong> {action}</div>'
    ) if action else ""

    title = html.escape(str(alert.get("title", "Alert")))
    message = html.escape(str(alert.get("message", "")))

    st.markdown(
        f"""
<div style="background:{C['surface']};border:1px solid {C['border']};
            border-left:4px solid {fg};border-radius:8px;
            padding:14px 18px;margin-bottom:10px;
            box-shadow:0 1px 3px rgba(0,0,0,0.05);">
    <div style="display:flex;justify-content:space-between;
                align-items:flex-start;margin-bottom:8px;gap:12px;">
        <div style="font-size:0.9rem;font-weight:700;
                    color:{C['text']};line-height:1.3;">{title}</div>
        <div style="flex-shrink:0;">{badge_html}</div>
    </div>
    <div style="font-size:0.83rem;color:{C['text_body']};
                line-height:1.5;">{message}</div>
    {action_html}
</div>
""",
        unsafe_allow_html=True,
    )


def render_insight_card(insight: dict) -> None:
    """
    Renders a single analytics insight card.
    Consumes the dict shape produced by analytics_engine.py.

    Parameters
    ----------
    insight : dict with keys:
        - category       (str) : "attendance"|"fees"|"academic"|"documents"|"timetable"
        - title          (str) : Insight title
        - severity       (str) : "info" | "warning" | "critical"
        - metric         (str) : Primary metric string, e.g. "91.2% avg · 2 at-risk"
        - forecast       (str) : One-sentence finding
        - recommendation (str) : One-sentence recommended action
        - confidence     (int) : 0–100 confidence score
        - trend          (str) : "stable" | "declining" | "improving"

    Design
    ------
    ┌─────────────────────────────────────────────────────────┐
    │ ATTENDANCE                                  [Warning]   │
    │ Attendance Risk Analysis                  90% confidence│
    │                                                         │
    │ 91.2% avg · 2 at-risk                                   │
    │                                                         │
    │ 2 of 30 students are below the 75% threshold...         │
    │                                                         │
    │ Recommended action: Review attendance records...        │
    └─────────────────────────────────────────────────────────┘
    """
    sev = str(insight.get("severity", "info")).lower()
    fg, bg, bd = SEV_COLORS.get(sev, SEV_COLORS["info"])

    cat = str(insight.get("category", ""))
    cat_display = html.escape(CAT_LABEL.get(cat, cat.replace("_", " ").title()))
    sev_display = SEV_LABEL.get(sev, sev.title())
    conf = insight.get("confidence", 100)
    trend = str(insight.get("trend", "stable"))

    # Trend indicator (text-only, no color-only reliance)
    trend_symbol = {"declining": "↓ Declining", "improving": "↑ Improving"}.get(
        trend, "→ Stable"
    )
    trend_color = {
        "declining": C["danger"],
        "improving": C["success"],
    }.get(trend, C["text_muted"])

    badge_level = {
        "critical": "danger",
        "warning":  "warning",
        "info":     "success",
    }.get(sev, "neutral")
    badge_html = render_status_badge(sev_display, badge_level)

    st.markdown(
        f"""
<div style="background:{C['surface']};border:1px solid {C['border']};
            border-left:4px solid {fg};border-radius:10px;
            padding:18px 20px;margin-bottom:12px;
            box-shadow:0 2px 8px rgba(15,23,42,0.04);">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;gap:12px;">
        <div>
            <div style="font-size:0.68rem;font-weight:700;color:{C['text_light']};
                        text-transform:uppercase;letter-spacing:0.08em;
                        margin-bottom:3px;">{cat_display}</div>
            <div style="font-size:0.95rem;font-weight:700;color:{C['text']};line-height:1.3;">{html.escape(str(insight.get('title', '')))}</div>
        </div>
        <div style="text-align:right;flex-shrink:0;">
            {badge_html}
            <div style="font-size:0.68rem;color:{C['text_light']};margin-top:4px;">{conf}% confidence</div>
        </div>
    </div>
    <div style="font-size:1.05rem;font-weight:700;color:{fg};margin-bottom:8px;line-height:1.2;">{html.escape(str(insight.get('metric', '')))}</div>
    <div style="font-size:0.85rem;color:{C['text_body']};margin-bottom:10px;line-height:1.55;">{html.escape(str(insight.get('forecast', '')))}</div>
    <div style="border-top:1px solid {C['border']};padding-top:10px;
                display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
        <div style="font-size:0.8rem;color:{C['blue']};line-height:1.4;flex:1;">
            <strong>Recommended action:</strong> {html.escape(str(insight.get('recommendation', '')))}
        </div>
        <div style="font-size:0.72rem;font-weight:600;color:{trend_color};flex-shrink:0;white-space:nowrap;">{trend_symbol}</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PART 5 — COPILOT + UTILITY COMPONENTS + BACKWARD-COMPAT ALIASES
# ══════════════════════════════════════════════════════════════════════════════


def render_copilot_prompt_card(example_questions: list) -> None:
    """
    Renders the AI Copilot introduction card with example question chips.

    Parameters
    ----------
    example_questions : list of str
        Short question strings to display as clickable-looking chips.
        These are display-only — clicking them does NOT auto-submit.
        The caller is responsible for wiring st.chat_input separately.

    Design
    ------
    ┌──────────────────────────────────────────────────────────────┐
    │  Ask EduOS-AI                                                │
    │  Get answers about students, staffing, timetables and        │
    │  school operations.                                          │
    │                                                              │
    │  Try asking:                                                 │
    │  [How is our staffing situation?]  [Are there conflicts?]    │
    │  [How many students need attention?]  [Fee collection rate?] │
    └──────────────────────────────────────────────────────────────┘
    """
    chips_html = "".join(
        f'<span style="display:inline-block;padding:5px 12px;'
        f'border:1px solid {C["border_dark"]};border-radius:4px;'
        f'font-size:0.78rem;font-weight:500;color:{C["text_muted"]};'
        f'background:{C["bg_subtle"]};margin:3px 4px 3px 0;'
        f'cursor:default;white-space:nowrap;">{q}</span>'
        for q in example_questions
    )

    st.markdown(
        f"""
<div style="background:{C['surface']};border:1px solid {C['border']};
            border-radius:8px;padding:20px 22px;margin-bottom:16px;
            box-shadow:0 1px 3px rgba(0,0,0,0.05);">
    <div style="font-size:1rem;font-weight:700;color:{C['navy']};
                margin-bottom:4px;">Ask EduOS-AI</div>
    <div style="font-size:0.83rem;color:{C['text_muted']};
                margin-bottom:14px;line-height:1.4;">
        Get answers about students, staffing, timetables and school operations.
        All answers are grounded in live school data.
    </div>
    <div style="font-size:0.72rem;font-weight:700;color:{C['text_muted']};
                text-transform:uppercase;letter-spacing:0.07em;
                margin-bottom:8px;">Try asking</div>
    <div style="line-height:2;">{chips_html}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_staffing_banner(staffing_report: dict) -> None:
    """
    Renders the staffing pressure score banner.
    Consumes the dict produced by staffing_engine.calculate_staffing_report().

    Parameters
    ----------
    staffing_report : dict with keys:
        - staffing_pressure_score (int)  : 0–100
        - staffing_pressure_level (str)  : LOW | MODERATE | HIGH | CRITICAL
        - explanation             (str)  : Plain-English summary sentence

    Design
    ------
    ┌──────────────────────────────────────────────────────────────┐
    │ STAFFING PRESSURE SCORE                                      │
    │                                                              │
    │  24  /100  ·  LOW                                            │
    │                                                              │
    │  2 of 8 teachers available (25%). Average teaching load...   │
    └──────────────────────────────────────────────────────────────┘
    """
    score = staffing_report.get("staffing_pressure_score", 0)
    level = str(staffing_report.get("staffing_pressure_level", "LOW")).upper()
    explanation = str(staffing_report.get("explanation", ""))

    fg, bg, bd = LEVEL_COLORS.get(level, LEVEL_COLORS["LOW"])

    st.markdown(
        f"""
<div style="background:{bg};border:1px solid {bd};
            border-left:5px solid {fg};border-radius:8px;
            padding:20px 24px;margin-bottom:16px;">
    <div style="font-size:0.68rem;font-weight:700;color:{C['text_muted']};
                text-transform:uppercase;letter-spacing:0.09em;
                margin-bottom:8px;">Staffing Pressure Score</div>
    <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:8px;">
        <span style="font-size:2.5rem;font-weight:800;
                     color:{fg};line-height:1;">{score}</span>
        <span style="font-size:0.95rem;font-weight:700;color:{fg};">
            / 100 &nbsp;&middot;&nbsp; {level}
        </span>
    </div>
    <div style="font-size:0.85rem;color:{C['text_body']};
                line-height:1.5;">{explanation}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_recommendation_item(index: int, text: str) -> None:
    """
    Renders a single numbered recommendation row.
    Used in the staffing recommendations list.

    Parameters
    ----------
    index : 1-based display number
    text  : Recommendation text
    """
    st.markdown(
        f"""
<div style="background:{C['blue_light']};border:1px solid {C['blue_mid']};
            border-left:3px solid {C['blue']};border-radius:6px;
            padding:10px 16px;margin-bottom:8px;
            font-size:0.85rem;color:{C['text']};line-height:1.5;">
    <strong style="color:{C['navy']};">{index}.</strong>&nbsp;{html.escape(str(text))}
</div>
""",
        unsafe_allow_html=True,
    )


def render_step_indicator(steps: list, current_step: int) -> None:
    """
    Renders a horizontal workflow step indicator.
    Used in the AI Document Reader to show upload → extract → validate → review → save.

    Parameters
    ----------
    steps        : list of str — step labels in order
    current_step : 0-based index of the active step

    Visual states
    -------------
    Completed (i < current_step) : green filled circle with checkmark
    Active    (i == current_step): blue filled circle with step number
    Pending   (i > current_step) : gray outlined circle with step number

    Connector line between steps reflects completion state.
    """
    items: list = []

    for i, label in enumerate(steps):
        if i < current_step:
            circle_bg = C["success"]
            circle_border = C["success"]
            dot_text = "&#10003;"          # ✓ checkmark
            label_color = C["success"]
            label_weight = "600"
            connector_bg = C["success_bd"]
        elif i == current_step:
            circle_bg = C["blue"]
            circle_border = C["blue"]
            dot_text = str(i + 1)
            label_color = C["blue"]
            label_weight = "700"
            connector_bg = C["border"]
        else:
            circle_bg = C["surface"]
            circle_border = C["border_dark"]
            dot_text = str(i + 1)
            label_color = C["text_light"]
            label_weight = "400"
            connector_bg = C["border"]

        connector = (
            f'<div style="flex:1;height:2px;background:{connector_bg};'
            f'margin:0 6px;align-self:center;min-width:16px;"></div>'
            if i < len(steps) - 1
            else ""
        )

        items.append(
            f"""
<div style="display:flex;flex-direction:column;align-items:center;min-width:56px;">
    <div style="width:28px;height:28px;border-radius:50%;
                background:{circle_bg};border:2px solid {circle_border};
                color:white;display:flex;align-items:center;
                justify-content:center;font-size:0.72rem;
                font-weight:700;flex-shrink:0;">{dot_text}</div>
    <div style="font-size:0.68rem;font-weight:{label_weight};
                color:{label_color};margin-top:5px;
                text-align:center;line-height:1.3;
                max-width:64px;">{label}</div>
</div>{connector}"""
        )

    st.markdown(
        f"""
<div style="display:flex;align-items:flex-start;
            background:{C['surface']};border:1px solid {C['border']};
            border-radius:8px;padding:16px 24px;margin-bottom:20px;
            box-shadow:0 1px 2px rgba(0,0,0,0.04);">
    {''.join(items)}
</div>
""",
        unsafe_allow_html=True,
    )


def render_db_status_bar(
    connection_status: str,
    unresolved_count: int,
    DB_STATUS_CONNECTED: str,
    DB_STATUS_MISSING_CONFIG: str,
) -> None:
    """
    Renders the top-right database connection + alert count status strip.

    Parameters
    ----------
    connection_status     : Value from db_client.connection_status
    unresolved_count      : Number of unresolved alerts
    DB_STATUS_CONNECTED   : The constant string from db_client
    DB_STATUS_MISSING_CONFIG : The constant string from db_client
    """
    if connection_status == DB_STATUS_CONNECTED:
        db_badge = render_status_badge("Database Connected", "success")
    elif connection_status == DB_STATUS_MISSING_CONFIG:
        db_badge = render_status_badge("Database Not Configured", "warning")
    else:
        db_badge = render_status_badge("Database Connection Failed", "danger")

    if unresolved_count > 0:
        noun = "Alert" if unresolved_count == 1 else "Alerts"
        alert_badge = render_status_badge(
            f"{unresolved_count} Active {noun}", "danger"
        )
    else:
        alert_badge = render_status_badge("No Active Alerts", "success")

    st.markdown(
        f"""
<div style="display:flex;justify-content:flex-end;align-items:center;
            gap:8px;padding:6px 0 4px;">
    {db_badge}&nbsp;{alert_badge}
</div>
""",
        unsafe_allow_html=True,
    )


# ── Backward-compatibility aliases ────────────────────────────────────────────
# These preserve any existing callers in app.py that use the old function names
# from the previous version of ui_components.py.
# New code should use the render_* names above.

def inject_theme() -> None:
    """Alias for inject_global_styles(). Preserved for backward compatibility."""
    inject_global_styles()

def page_header(title: str, subtitle: str = "") -> None:
    """Alias for render_page_header(). Preserved for backward compatibility."""
    render_page_header(title, subtitle)

def section_header(title: str) -> None:
    """Alias for render_section_header(). Preserved for backward compatibility."""
    render_section_header(title)

def kpi_card(label: str, value: str, description: str = "", status: str = "") -> None:
    """Alias for render_kpi_card(). Preserved for backward compatibility."""
    render_kpi_card(label, value, description, status)

def status_badge(text: str, level: str = "neutral") -> str:
    """Alias for render_status_badge(). Preserved for backward compatibility."""
    return render_status_badge(text, level)

def insight_card(ins: dict) -> None:
    """Alias for render_insight_card(). Preserved for backward compatibility."""
    render_insight_card(ins)

def staffing_score_banner(sr: dict) -> None:
    """Alias for render_staffing_banner(). Preserved for backward compatibility."""
    render_staffing_banner(sr)

def alert_card(alt: dict) -> None:
    """Alias for render_alert_card(). Preserved for backward compatibility."""
    render_alert_card(alt)

def empty_state(title: str, description: str) -> None:
    """Alias for render_empty_state(). Preserved for backward compatibility."""
    render_empty_state(title, description)

def db_status_bar(
    connection_status: str,
    unresolved_count: int,
    DB_STATUS_CONNECTED: str,
    DB_STATUS_MISSING_CONFIG: str,
) -> None:
    """Alias for render_db_status_bar(). Preserved for backward compatibility."""
    render_db_status_bar(
        connection_status, unresolved_count,
        DB_STATUS_CONNECTED, DB_STATUS_MISSING_CONFIG,
    )

def recommendation_item(index: int, text: str) -> None:
    """Alias for render_recommendation_item(). Preserved for backward compatibility."""
    render_recommendation_item(index, text)

def step_indicator(steps: list, current: int) -> None:
    """Alias for render_step_indicator(). Preserved for backward compatibility."""
    render_step_indicator(steps, current)

def health_card(
    title: str, status_label: str, metric: str, detail: str, level: str = "info"
) -> None:
    """Alias for render_health_card(). Preserved for backward compatibility."""
    render_health_card(title, status_label, metric, detail, level)
