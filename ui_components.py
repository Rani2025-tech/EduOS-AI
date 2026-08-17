"""
EduOS-AI — UI Components & Theme
==================================
Centralized light-enterprise theme CSS and reusable HTML component builders.
No business logic. No database calls. Pure presentation helpers.
"""

import streamlit as st

# ── Color tokens ──────────────────────────────────────────────────────────────
C = {
    "navy":        "#1e3a5f",
    "blue":        "#2563eb",
    "blue_light":  "#eff6ff",
    "blue_mid":    "#dbeafe",
    "bg":          "#f8f9fb",
    "surface":     "#ffffff",
    "border":      "#e2e8f0",
    "border_dark": "#cbd5e1",
    "text":        "#1e293b",
    "text_muted":  "#64748b",
    "text_light":  "#94a3b8",
    "success":     "#16a34a",
    "success_bg":  "#f0fdf4",
    "success_bd":  "#bbf7d0",
    "warning":     "#d97706",
    "warning_bg":  "#fffbeb",
    "warning_bd":  "#fde68a",
    "danger":      "#dc2626",
    "danger_bg":   "#fef2f2",
    "danger_bd":   "#fecaca",
    "info":        "#0369a1",
    "info_bg":     "#f0f9ff",
    "info_bd":     "#bae6fd",
}

# ── Severity → color mapping ──────────────────────────────────────────────────
SEV_COLORS = {
    "critical": (C["danger"],   C["danger_bg"],  C["danger_bd"]),
    "warning":  (C["warning"],  C["warning_bg"], C["warning_bd"]),
    "info":     (C["success"],  C["success_bg"], C["success_bd"]),
}

SEV_LABEL = {
    "critical": "Critical",
    "warning":  "Warning",
    "info":     "Healthy",
}

LEVEL_COLORS = {
    "LOW":      (C["success"],  C["success_bg"],  C["success_bd"]),
    "MODERATE": (C["warning"],  C["warning_bg"],  C["warning_bd"]),
    "HIGH":     ("#ea580c",     "#fff7ed",         "#fed7aa"),
    "CRITICAL": (C["danger"],   C["danger_bg"],   C["danger_bd"]),
}

CAT_LABEL = {
    "attendance": "Attendance",
    "fees":       "Fee Collection",
    "academic":   "Academic",
    "documents":  "Documents",
    "timetable":  "Timetable",
}


# ── Global CSS injection ──────────────────────────────────────────────────────
def inject_theme():
    st.markdown(f"""
<style>
/* ── Reset & base ── */
.stApp {{
    background-color: {C['bg']};
    color: {C['text']};
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background-color: {C['navy']};
    border-right: none;
}}
section[data-testid="stSidebar"] * {{
    color: #e2e8f0 !important;
}}
section[data-testid="stSidebar"] .stRadio label {{
    color: #cbd5e1 !important;
    font-size: 0.875rem;
    padding: 4px 0;
}}
section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {{
    color: #94a3b8 !important;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 16px 0 4px 0;
}}
section[data-testid="stSidebar"] hr {{
    border-color: rgba(255,255,255,0.1) !important;
    margin: 12px 0;
}}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSelectbox div {{
    color: #e2e8f0 !important;
}}
section[data-testid="stSidebar"] .stButton > button {{
    background: rgba(255,255,255,0.1) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    width: 100%;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(255,255,255,0.18) !important;
}}

/* ── Main content area ── */
.main .block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}}

/* ── Metric cards ── */
div[data-testid="stMetricValue"] {{
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    color: {C['navy']} !important;
}}
div[data-testid="stMetricLabel"] {{
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: {C['text_muted']} !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
div[data-testid="stMetricDelta"] {{
    font-size: 0.78rem !important;
}}
div[data-testid="metric-container"] {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}}

/* ── Buttons ── */
.stButton > button {{
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.875rem;
    border: 1px solid {C['border_dark']};
    background: {C['surface']};
    color: {C['text']};
    transition: all 0.15s ease;
}}
.stButton > button:hover {{
    border-color: {C['blue']};
    color: {C['blue']};
    background: {C['blue_light']};
}}
.stButton > button[kind="primary"] {{
    background: {C['blue']};
    color: white;
    border-color: {C['blue']};
}}
.stButton > button[kind="primary"]:hover {{
    background: {C['navy']};
    border-color: {C['navy']};
    color: white;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: {C['surface']};
    border-bottom: 2px solid {C['border']};
    gap: 0;
}}
.stTabs [data-baseweb="tab"] {{
    font-size: 0.875rem;
    font-weight: 500;
    color: {C['text_muted']};
    padding: 10px 20px;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
}}
.stTabs [aria-selected="true"] {{
    color: {C['blue']} !important;
    border-bottom: 2px solid {C['blue']} !important;
    font-weight: 600;
}}

/* ── Dataframe ── */
.stDataFrame {{
    border: 1px solid {C['border']};
    border-radius: 8px;
    overflow: hidden;
}}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
    border-color: {C['border_dark']} !important;
    border-radius: 6px !important;
    background: {C['surface']} !important;
    color: {C['text']} !important;
    font-size: 0.875rem !important;
}}

/* ── Alerts / callouts ── */
.stAlert {{
    border-radius: 6px;
    font-size: 0.875rem;
}}

/* ── Expander ── */
.streamlit-expanderHeader {{
    font-weight: 600;
    font-size: 0.875rem;
    color: {C['text']};
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 6px;
}}

/* ── Divider ── */
hr {{
    border-color: {C['border']} !important;
    margin: 20px 0 !important;
}}

/* ── Chat messages ── */
.stChatMessage {{
    background: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 8px;
}}

/* ── Progress bar ── */
.stProgress > div > div {{
    background-color: {C['blue']} !important;
}}

/* ── Spinner ── */
.stSpinner > div {{
    border-top-color: {C['blue']} !important;
}}

/* ── File uploader ── */
.stFileUploader {{
    border: 2px dashed {C['border_dark']};
    border-radius: 8px;
    background: {C['bg']};
}}
</style>
""", unsafe_allow_html=True)


# ── Reusable HTML components ──────────────────────────────────────────────────

def page_header(title: str, subtitle: str = ""):
    """Renders a clean page-level header."""
    sub_html = f'<p style="margin:4px 0 0;font-size:0.875rem;color:{C["text_muted"]};">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
<div style="margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid {C['border']};">
    <h2 style="margin:0;font-size:1.4rem;font-weight:700;color:{C['navy']};">{title}</h2>
    {sub_html}
</div>
""", unsafe_allow_html=True)


def section_header(title: str):
    """Renders a section-level subheader."""
    st.markdown(f"""
<h3 style="font-size:1rem;font-weight:700;color:{C['navy']};
           margin:20px 0 12px;letter-spacing:-0.01em;">{title}</h3>
""", unsafe_allow_html=True)


def kpi_card(label: str, value: str, description: str = "", status: str = ""):
    """
    Renders a KPI card using st.metric (styled via CSS).
    status: 'good' | 'warning' | 'danger' | '' for neutral
    """
    status_colors = {
        "good":    C["success"],
        "warning": C["warning"],
        "danger":  C["danger"],
        "":        C["text_muted"],
    }
    color = status_colors.get(status, C["text_muted"])
    desc_html = f'<div style="font-size:0.75rem;color:{color};margin-top:2px;">{description}</div>' if description else ""
    st.markdown(f"""
<div style="background:{C['surface']};border:1px solid {C['border']};border-radius:8px;
            padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
    <div style="font-size:0.72rem;font-weight:700;color:{C['text_muted']};
                text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">{label}</div>
    <div style="font-size:1.75rem;font-weight:700;color:{C['navy']};line-height:1.1;">{value}</div>
    {desc_html}
</div>
""", unsafe_allow_html=True)


def status_badge(text: str, level: str = "info"):
    """Returns an inline HTML badge string. level: info|success|warning|danger|neutral"""
    palette = {
        "info":    (C["info"],    C["info_bg"],    C["info_bd"]),
        "success": (C["success"], C["success_bg"], C["success_bd"]),
        "warning": (C["warning"], C["warning_bg"], C["warning_bd"]),
        "danger":  (C["danger"],  C["danger_bg"],  C["danger_bd"]),
        "neutral": (C["text_muted"], C["bg"],      C["border"]),
    }
    fg, bg, bd = palette.get(level, palette["neutral"])
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:4px;'
        f'font-size:0.72rem;font-weight:700;color:{fg};background:{bg};'
        f'border:1px solid {bd};letter-spacing:0.03em;">{text}</span>'
    )


def insight_card(ins: dict):
    """Renders a single analytics insight card in the light enterprise style."""
    sev = ins.get("severity", "info")
    fg, bg, bd = SEV_COLORS.get(sev, SEV_COLORS["info"])
    cat = ins.get("category", "")
    cat_label = CAT_LABEL.get(cat, cat.title())
    sev_label = SEV_LABEL.get(sev, sev.title())
    conf = ins.get("confidence", 100)

    st.markdown(f"""
<div style="background:{C['surface']};border:1px solid {C['border']};
            border-left:4px solid {fg};border-radius:8px;
            padding:16px 20px;margin-bottom:12px;
            box-shadow:0 1px 3px rgba(0,0,0,0.05);">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
        <div>
            <span style="font-size:0.7rem;font-weight:700;color:{C['text_muted']};
                         text-transform:uppercase;letter-spacing:0.06em;">{cat_label}</span>
            <div style="font-size:0.975rem;font-weight:700;color:{C['text']};margin-top:2px;">
                {ins.get('title','')}
            </div>
        </div>
        <div style="text-align:right;flex-shrink:0;margin-left:12px;">
            <span style="display:inline-block;padding:3px 10px;border-radius:4px;
                         font-size:0.7rem;font-weight:700;color:{fg};
                         background:{bg};border:1px solid {bd};">{sev_label}</span>
            <div style="font-size:0.68rem;color:{C['text_light']};margin-top:3px;">{conf}% confidence</div>
        </div>
    </div>
    <div style="font-size:1.05rem;font-weight:700;color:{fg};margin-bottom:6px;">
        {ins.get('metric','')}
    </div>
    <div style="font-size:0.85rem;color:{C['text_muted']};margin-bottom:6px;line-height:1.5;">
        {ins.get('forecast','')}
    </div>
    <div style="font-size:0.8rem;color:{C['info']};border-top:1px solid {C['border']};
                padding-top:8px;margin-top:4px;">
        Recommended action: {ins.get('recommendation','')}
    </div>
</div>
""", unsafe_allow_html=True)


def staffing_score_banner(sr: dict):
    """Renders the staffing pressure score banner in light enterprise style."""
    score = sr["staffing_pressure_score"]
    level = sr["staffing_pressure_level"]
    fg, bg, bd = LEVEL_COLORS.get(level, LEVEL_COLORS["LOW"])

    st.markdown(f"""
<div style="background:{bg};border:1px solid {bd};border-left:5px solid {fg};
            border-radius:8px;padding:20px 24px;margin-bottom:16px;">
    <div style="font-size:0.7rem;font-weight:700;color:{C['text_muted']};
                text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">
        Staffing Pressure Score
    </div>
    <div style="display:flex;align-items:baseline;gap:12px;margin-bottom:8px;">
        <span style="font-size:2.5rem;font-weight:800;color:{fg};line-height:1;">{score}</span>
        <span style="font-size:0.95rem;font-weight:700;color:{fg};">/100 &nbsp;·&nbsp; {level}</span>
    </div>
    <div style="font-size:0.85rem;color:{C['text_muted']};line-height:1.5;">{sr['explanation']}</div>
</div>
""", unsafe_allow_html=True)


def alert_card(alt: dict):
    """Renders a single alert card."""
    priority = str(alt.get("priority", "medium")).lower()
    level_map = {"high": "danger", "critical": "danger", "medium": "warning", "low": "info"}
    level = level_map.get(priority, "warning")
    fg, bg, bd = SEV_COLORS.get(
        "critical" if level == "danger" else ("warning" if level == "warning" else "info"),
        SEV_COLORS["warning"]
    )
    label_map = {"danger": "High Priority", "warning": "Medium Priority", "info": "Low Priority"}
    badge_html = status_badge(label_map.get(level, "Alert"), level)

    action = alt.get("action", "")
    action_html = (
        f'<div style="font-size:0.78rem;color:{C["info"]};margin-top:8px;'
        f'border-top:1px solid {C["border"]};padding-top:6px;">'
        f'Action required: {action}</div>'
    ) if action else ""

    st.markdown(f"""
<div style="background:{C['surface']};border:1px solid {C['border']};
            border-left:4px solid {fg};border-radius:8px;
            padding:14px 18px;margin-bottom:10px;
            box-shadow:0 1px 3px rgba(0,0,0,0.05);">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
        <div style="font-size:0.9rem;font-weight:700;color:{C['text']};">{alt.get('title','Alert')}</div>
        {badge_html}
    </div>
    <div style="font-size:0.83rem;color:{C['text_muted']};line-height:1.5;">{alt.get('message','')}</div>
    {action_html}
</div>
""", unsafe_allow_html=True)


def empty_state(title: str, description: str):
    """Renders a professional empty state."""
    st.markdown(f"""
<div style="background:{C['surface']};border:1px solid {C['border']};border-radius:8px;
            padding:40px 24px;text-align:center;margin:8px 0;">
    <div style="font-size:0.975rem;font-weight:600;color:{C['text_muted']};margin-bottom:6px;">
        {title}
    </div>
    <div style="font-size:0.83rem;color:{C['text_light']};">{description}</div>
</div>
""", unsafe_allow_html=True)


def db_status_bar(connection_status: str, unresolved_count: int,
                  DB_STATUS_CONNECTED: str, DB_STATUS_MISSING_CONFIG: str):
    """Renders the top-right database + alert status strip."""
    if connection_status == DB_STATUS_CONNECTED:
        badge = status_badge("Database Connected", "success")
    elif connection_status == DB_STATUS_MISSING_CONFIG:
        badge = status_badge("Database Not Configured", "warning")
    else:
        badge = status_badge("Database Connection Failed", "danger")

    alert_badge = (
        status_badge(f"{unresolved_count} Active Alert{'s' if unresolved_count != 1 else ''}", "danger")
        if unresolved_count > 0
        else status_badge("No Active Alerts", "success")
    )

    st.markdown(f"""
<div style="display:flex;justify-content:flex-end;align-items:center;
            gap:10px;padding:8px 0 4px;">
    {badge}&nbsp;{alert_badge}
</div>
""", unsafe_allow_html=True)


def recommendation_item(index: int, text: str):
    """Renders a single staffing recommendation row."""
    st.markdown(f"""
<div style="background:{C['blue_light']};border:1px solid {C['blue_mid']};
            border-left:3px solid {C['blue']};border-radius:6px;
            padding:10px 16px;margin-bottom:8px;font-size:0.85rem;color:{C['text']};">
    <strong style="color:{C['navy']};">{index}.</strong>&nbsp; {text}
</div>
""", unsafe_allow_html=True)


def step_indicator(steps: list, current: int):
    """Renders a horizontal step progress indicator. steps = list of step labels."""
    items = []
    for i, label in enumerate(steps):
        if i < current:
            color = C["success"]
            dot = "✓"
            weight = "600"
        elif i == current:
            color = C["blue"]
            dot = str(i + 1)
            weight = "700"
        else:
            color = C["text_light"]
            dot = str(i + 1)
            weight = "400"

        connector = (
            f'<div style="flex:1;height:2px;background:{"#bbf7d0" if i < current else C["border"]};'
            f'margin:0 4px;align-self:center;"></div>'
            if i < len(steps) - 1 else ""
        )
        items.append(f"""
<div style="display:flex;flex-direction:column;align-items:center;min-width:60px;">
    <div style="width:28px;height:28px;border-radius:50%;background:{color};
                color:white;display:flex;align-items:center;justify-content:center;
                font-size:0.75rem;font-weight:700;">{dot}</div>
    <div style="font-size:0.7rem;font-weight:{weight};color:{color};
                margin-top:4px;text-align:center;white-space:nowrap;">{label}</div>
</div>{connector}""")

    st.markdown(f"""
<div style="display:flex;align-items:flex-start;padding:16px 0 20px;
            background:{C['surface']};border:1px solid {C['border']};
            border-radius:8px;padding:16px 24px;margin-bottom:20px;">
    {''.join(items)}
</div>
""", unsafe_allow_html=True)


def health_card(title: str, status_label: str, metric: str, detail: str, level: str = "info"):
    """Renders a compact operational health card."""
    fg, bg, bd = LEVEL_COLORS.get(level.upper(), LEVEL_COLORS["LOW"])
    st.markdown(f"""
<div style="background:{C['surface']};border:1px solid {C['border']};border-radius:8px;
            padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <span style="font-size:0.78rem;font-weight:700;color:{C['text_muted']};
                     text-transform:uppercase;letter-spacing:0.05em;">{title}</span>
        <span style="padding:2px 10px;border-radius:4px;font-size:0.7rem;font-weight:700;
                     color:{fg};background:{bg};border:1px solid {bd};">{status_label}</span>
    </div>
    <div style="font-size:1.2rem;font-weight:700;color:{C['navy']};margin-bottom:4px;">{metric}</div>
    <div style="font-size:0.78rem;color:{C['text_muted']};">{detail}</div>
</div>
""", unsafe_allow_html=True)
