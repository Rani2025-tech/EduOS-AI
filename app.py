import streamlit as st
import pandas as pd
import datetime
from ui_components import (
    inject_global_styles, render_page_header, render_section_header,
    render_kpi_card, render_status_badge, render_health_card,
    render_alert_card, render_insight_card, render_empty_state,
    render_db_status_bar, render_staffing_banner, render_recommendation_item,
    render_copilot_prompt_card, C,
)
from data_store import (
    init_session_state,
    init_auth_session,
    login_user,
    logout_user,
    is_authenticated,
    toggle_teacher,
    solve_timetable_reassignment,
    mark_attendance,
    pay_fee,
    commit_doc,
    refresh_from_db,
    process_and_save_document_input,
    process_and_save_teacher_input,
    process_and_save_timetable_input,
    add_copilot_message,
)
from copilot_engine import answer_question, classify_intent
from groq_client import groq_client
from db_client import db_instance, DB_STATUS_CONNECTED, DB_STATUS_MISSING_CONFIG, DB_STATUS_CONN_FAILED
from analytics_engine import generate_all_insights
from staffing_engine import calculate_staffing_report
from auth import (
    has_permission, scope_students, scope_alerts, scope_timetable,
    ROLE_LABELS, ROLE_ICONS,
)

# ── Tab Navigation Constants ──────────────────────────────────────────────────
TAB_DASHBOARD  = "📊 Persona Dashboard"
TAB_DOCUMENTS  = "📄 AI Document Reader (Multi-Slot Forms)"
TAB_TEACHERS   = "👩‍🏫 Teacher Availability & Roster"
TAB_TIMETABLE  = "🗓️ Smart Timetable Engine (OR-Tools Solver)"
TAB_DATA_LAYER = "🗄️ Unified Data Layer"
TAB_ALERTS     = "🚨 Proactive Alerts Center"
TAB_INSIGHTS   = "📈 Predictive Insights"
TAB_COPILOT    = "🤖 AI Copilot (NLQ)"

# ── 1. Page Configuration ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="EduOS AI — Autonomous School Operating System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── 2. Bootstrap auth + CSS ───────────────────────────────────────────────────
init_auth_session()
inject_global_styles()

# ── 3. Login gate ────────────────────────────────────────────────────────────
if not is_authenticated():
    # ── Login page scoped CSS ────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* Hide Streamlit sidebar and top chrome on login page */
    section[data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }

    /* Full-bleed Canvas */
    .stApp, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > section {
        background-color: #F8FAFC !important;
    }
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        background-color: #F8FAFC !important;
    }
    
    /* 50/50 Split Column Layout */
    [data-testid="column"]:first-child {
        background-color: #F8FAFC !important;
        min-height: 100vh;
        padding: 48px 56px !important;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    [data-testid="column"]:last-child {
        background-color: #0E4B5B !important;
        min-height: 100vh;
        padding: 48px 40px !important;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    /* Unified floating card container for the login panel */
    div[data-testid="stForm"] {
        background: #133E4B !important;
        border: 1.5px solid #1E5869 !important;
        border-radius: 16px !important;
        padding: 36px 32px 28px !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35), 0 0 30px rgba(76, 201, 240, 0.10) !important;
        box-sizing: border-box !important;
    }

    /* Input label overrides for dark teal login panel */
    .stTextInput label {
        font-size: 0.74rem !important;
        font-weight: 700 !important;
        color: #E2E8F0 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }

    /* ── Dark teal card inputs: Username & Password ── */
    div[data-baseweb="input"] {
        border: 1.5px solid #1E5869 !important;
        border-radius: 8px !important;
        background: #0B2A34 !important;
        transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
    }
    div[data-baseweb="input"]:hover {
        border-color: #4CC9F0 !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #4CC9F0 !important;
        box-shadow: 0 0 0 3px rgba(76, 201, 240, 0.25) !important;
    }
    /* Input field typography */
    div[data-baseweb="input"] > input {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
        caret-color: #4CC9F0 !important;
        -webkit-text-fill-color: #FFFFFF !important;
        padding: 12px 14px !important;
        background: #0B2A34 !important;
    }
    div[data-baseweb="input"] > input::placeholder {
        color: #94A3B8 !important;
        -webkit-text-fill-color: #94A3B8 !important;
        font-weight: 400 !important;
    }
    /* Autofill override for dark input background */
    div[data-baseweb="input"] > input:-webkit-autofill,
    div[data-baseweb="input"] > input:-webkit-autofill:hover,
    div[data-baseweb="input"] > input:-webkit-autofill:focus,
    div[data-baseweb="input"] > input:-webkit-autofill:active,
    input:-webkit-autofill,
    input:-webkit-autofill:hover,
    input:-webkit-autofill:focus,
    input:-webkit-autofill:active {
        -webkit-box-shadow: 0 0 0 1000px #0B2A34 inset !important;
        box-shadow: 0 0 0 1000px #0B2A34 inset !important;
        -webkit-text-fill-color: #FFFFFF !important;
        caret-color: #4CC9F0 !important;
        font-weight: 600 !important;
        background-color: #0B2A34 !important;
        transition: background-color 9999s ease-in-out 0s !important;
    }

    /* ── Luminous Cyan CTA Submit Button ─────────── */
    .stButton > button[kind="primary"],
    button[kind="primaryFormSubmit"] {
        background: #4CC9F0 !important;
        color: #0A232C !important;
        -webkit-text-fill-color: #0A232C !important;
        border: 1px solid #4CC9F0 !important;
        border-radius: 8px !important;
        font-size: 0.98rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.02em !important;
        padding: 13px 20px !important;
        box-shadow: 0 4px 20px rgba(76, 201, 240, 0.40) !important;
        transition: all 0.18s ease !important;
    }
    .stButton > button[kind="primary"]:hover,
    button[kind="primaryFormSubmit"]:hover {
        background: #56CFE1 !important;
        color: #0A232C !important;
        -webkit-text-fill-color: #0A232C !important;
        border-color: #56CFE1 !important;
        box-shadow: 0 0 25px rgba(76, 201, 240, 0.65) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="primary"]:active,
    button[kind="primaryFormSubmit"]:active {
        background: #38B6DB !important;
        box-shadow: none !important;
    }

    /* Feature value bullet item */
    .edu-bullet-item {
        display: flex;
        align-items: flex-start;
        gap: 14px;
        margin-bottom: 18px;
    }
    .edu-bullet-icon {
        width: 34px;
        height: 34px;
        border-radius: 8px;
        background: #F1F5F9;
        border: 1px solid #E2E8F0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.05rem;
        flex-shrink: 0;
        margin-top: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1])

    # ── LEFT PANEL — Platform Value & Minimalist Architecture (Light Canvas) ──
    with col_left:
        st.markdown(
            '<div style="height:100%;display:flex;flex-direction:column;justify-content:space-between;">'
            '<div>'
            '<div style="display:flex;align-items:center;gap:12px;margin-bottom:44px;">'
            '<div style="width:38px;height:38px;background:#0E4B5B;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.15rem;color:#F59E0B;box-shadow:0 4px 12px rgba(14,75,91,0.25);">&#9889;</div>'
            '<div>'
            '<div style="font-size:1.15rem;font-weight:900;color:#0F172A;letter-spacing:-0.02em;line-height:1;">EduOS <span style="color:#0E4B5B;">AI</span></div>'
            '<div style="font-size:0.62rem;font-weight:700;color:#94A3B8;letter-spacing:0.14em;text-transform:uppercase;margin-top:3px;">School Operations Platform</div>'
            '</div>'
            '</div>'
            '<div style="margin-bottom:36px;">'
            '<div style="font-size:2.25rem;font-weight:900;color:#0F172A;letter-spacing:-0.035em;line-height:1.15;margin-bottom:14px;">THE INTELLIGENT<br>OPERATING SYSTEM<br><span style="color:#0E4B5B;">FOR SCHOOLS.</span></div>'
            '<div style="font-size:0.92rem;color:#475569;line-height:1.6;max-width:440px;">One AI-powered command center that transforms everyday school operations.</div>'
            '</div>'
            '<div style="margin-bottom:32px;max-width:460px;">'
            '<div class="edu-bullet-item"><div class="edu-bullet-icon">&#128196;</div><div><div style="font-size:0.88rem;font-weight:700;color:#0F172A;margin-bottom:2px;">Automated Document Intelligence</div><div style="font-size:0.78rem;color:#64748B;line-height:1.45;">Instant, structured extraction from admission forms, fee receipts, and student files.</div></div></div>'
            '<div class="edu-bullet-item"><div class="edu-bullet-icon">&#129504;</div><div><div style="font-size:0.88rem;font-weight:700;color:#0F172A;margin-bottom:2px;">Conflict-Free Smart Scheduling</div><div style="font-size:0.78rem;color:#64748B;line-height:1.45;">Mathematical OR-Tools optimization balancing teacher workload and classroom capacity.</div></div></div>'
            '<div class="edu-bullet-item"><div class="edu-bullet-icon">&#128202;</div><div><div style="font-size:0.88rem;font-weight:700;color:#0F172A;margin-bottom:2px;">Predictive Resource Allocation</div><div style="font-size:0.78rem;color:#64748B;line-height:1.45;">Forecasting staffing pressure and attendance anomalies before operational bottlenecks occur.</div></div></div>'
            '</div>'
            '<div style="margin-top:12px;opacity:0.85;">'
            '<svg width="280" height="70" viewBox="0 0 280 70" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M10 35H60L75 15L95 55L115 25L130 35H180" stroke="#0E4B5B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
            '<circle cx="180" cy="35" r="4" fill="#F59E0B" />'
            '<path d="M184 35H240" stroke="#94A3B8" stroke-width="1.5" stroke-dasharray="4 4"/>'
            '<circle cx="245" cy="35" r="8" stroke="#0E4B5B" stroke-width="2" fill="#FFFFFF"/>'
            '<circle cx="245" cy="35" r="3" fill="#4CC9F0"/>'
            '</svg>'
            '</div>'
            '</div>'
            '<div style="border-top:1px solid #E2E8F0;padding-top:16px;margin-top:28px;">'
            '<div style="font-size:0.75rem;font-weight:900;color:#0F172A;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:3px;">ONE LOGIN. ONE COMMAND CENTER.</div>'
            '<div style="font-size:0.75rem;font-weight:600;color:#334155;">Connected school operations. Intelligent decisions. Minimal clicks.</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

    # ── RIGHT PANEL — Floating Dark Teal Glass Container ──────────────────────
    with col_right:
        # Centered card column
        _, card_col, _ = st.columns([1, 12, 1])
        with card_col:

            # ── Unified card: header + form fields + footer in floating glass panel ──
            with st.form("login_form", clear_on_submit=False):
                st.markdown(
                    '<div style="margin-bottom:20px;">'
                    '<div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">'
                    '<span style="display:inline-block;width:7px;height:7px;border-radius:2px;background:#4CC9F0;box-shadow:0 0 8px rgba(76,201,240,0.6);"></span>'
                    '<span style="font-size:0.65rem;font-weight:800;color:#4CC9F0;letter-spacing:0.14em;text-transform:uppercase;">SCHOOL OPERATIONS</span>'
                    '</div>'
                    '<div style="margin-bottom:14px;">'
                    '<div style="font-size:1.75rem;font-weight:900;color:#FFFFFF;letter-spacing:-0.03em;line-height:1.2;margin-bottom:6px;">Welcome back</div>'
                    '<div style="font-size:0.86rem;color:#94A3B8;line-height:1.55;">Access your school operations command center.</div>'
                    '</div>'
                    '<div style="height:1px;background:#1E5869;margin-top:16px;"></div>'
                    '</div>',
                    unsafe_allow_html=True
                )

                username_input = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    key="login_username",
                )
                password_input = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password",
                )

                st.markdown(
                    '<div style="display:flex;justify-content:flex-end;margin-top:-6px;margin-bottom:14px;">'
                    '<span style="font-size:0.75rem;color:#4CC9F0;font-weight:600;cursor:pointer;letter-spacing:0.01em;">Forgot password?</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

                submitted = st.form_submit_button(
                    "Enter Command Center  →",
                    type="primary",
                    use_container_width=True,
                )

                if submitted:
                    if login_user(username_input, password_input):
                        init_session_state()
                        st.rerun()
                    else:
                        st.error(st.session_state.get("auth_error", "Login failed."))

            # ── Supabase / system warning (conditional — logic unchanged) ────────
            if not db_instance.is_supabase_active:
                st.markdown(
                    '<div style="margin-top:14px;background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.35);border-left:4px solid #F59E0B;border-radius:8px;padding:14px 16px;display:flex;align-items:flex-start;gap:12px;">'
                    '<span style="font-size:1.05rem;flex-shrink:0;color:#F59E0B;margin-top:1px;">⚠</span>'
                    '<div>'
                    '<div style="font-size:0.72rem;font-weight:800;color:#F59E0B;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">System Configuration</div>'
                    '<div style="font-size:0.78rem;color:#CBD5E1;line-height:1.5;">School data services are currently unavailable. Please verify the system configuration before signing in.</div>'
                    '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

            # ── Security footer ────────────────────────────────────────────────
            st.markdown(
                '<div style="margin-top:20px;padding-top:14px;text-align:center;">'
                '<div style="font-size:0.82rem;font-weight:800;color:#000000;margin-bottom:4px;display:flex;align-items:center;justify-content:center;gap:6px;">'
                '<span>🔒</span> <span>Secure role-based access</span>'
                '</div>'
                '<div style="font-size:0.76rem;font-weight:600;color:#1E293B;line-height:1.5;max-width:340px;margin:0 auto;">'
                'Your school data stays within the authorized operational environment.'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )

    st.stop()

# ── Authenticated from here down ─────────────────────────────────────────────────
auth        = st.session_state.auth
active_role = auth["role"]          # admin | teacher | student | parent
linked_id   = auth.get("linked_id") # student_id / teacher_id or None

# Scope data to what this role is allowed to see
visible_students  = scope_students(st.session_state.get("students", []),  active_role, linked_id)
visible_alerts    = scope_alerts(st.session_state.get("alerts", []),      active_role, linked_id)
visible_timetable = scope_timetable(
    st.session_state.get("timetable", []), active_role, linked_id,
    st.session_state.get("students", [])
)

# ── 4. Top header ───────────────────────────────────────────────────────────
unresolved_count = len([a for a in visible_alerts if not a.get("resolved")])

col_header, col_status = st.columns([3, 1])
with col_header:
    st.markdown(f"""
        <div style="padding: 8px 0 4px;">
            <div style="font-size:1.5rem;font-weight:800;color:{C['navy']};letter-spacing:-0.02em;line-height:1.2;">
                EduOS <span style="color:{C['blue']};">AI</span>
            </div>
            <div style="font-size:0.8rem;color:{C['text_muted']};font-weight:500;margin-top:2px;">School Operations Platform</div>
        </div>
    """, unsafe_allow_html=True)
with col_status:
    render_db_status_bar(
        db_instance.connection_status, unresolved_count,
        DB_STATUS_CONNECTED, DB_STATUS_MISSING_CONFIG
    )

st.markdown(f"<hr style='border:none;border-top:1px solid {C['border']};margin:8px 0 16px;'>", unsafe_allow_html=True)

# ── 5. Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:16px 0 12px;border-bottom:1px solid rgba(255,255,255,0.12);margin-bottom:12px;">
            <div style="font-size:1.1rem;font-weight:800;color:#FFFFFF;letter-spacing:-0.01em;">EduOS AI</div>
            <div style="font-size:0.72rem;color:rgba(255,255,255,0.72);font-weight:500;margin-top:2px;">School Operations Platform</div>
        </div>
    """, unsafe_allow_html=True)

    # ── Signed-in user badge (read-only — no free persona switching) ────────────
    role_icon  = ROLE_ICONS.get(active_role, "👤")
    role_label = ROLE_LABELS.get(active_role, active_role.title())
    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:8px;
                    padding:10px 14px;margin-bottom:12px;">
            <div style="font-size:0.75rem;color:rgba(255,255,255,0.65);font-weight:500;">Signed in as</div>
            <div style="font-size:0.95rem;font-weight:700;color:#FFFFFF;margin-top:2px;">
                {role_icon} {auth['username']}
            </div>
            <div style="font-size:0.75rem;color:{C['action_blue']};margin-top:2px;font-weight:600;">{role_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Role-scoped navigation ───────────────────────────────────────────────
    st.markdown("**Navigation**")

    # Build the tab list based on what the current role can access
    _all_tabs = [
        (TAB_DASHBOARD,   None),                 # always visible
        (TAB_DOCUMENTS,   "documents:write"),    # admin only
        (TAB_TEACHERS,    "teachers:write"),     # admin only
        (TAB_TIMETABLE,   "timetable:write"),    # admin only
        (TAB_DATA_LAYER,  "students:read_all"),  # admin + teacher
        (TAB_ALERTS,      None),                 # always visible (scoped)
        (TAB_INSIGHTS,    "analytics:read_all"), # admin only
        (TAB_COPILOT,     "copilot:use"),        # admin + teacher
    ]
    visible_tabs = [
        label for label, perm in _all_tabs
        if perm is None or has_permission(active_role, perm)
    ]

    # Handle programmatic navigation from session state (_nav)
    nav_target = st.session_state.pop("_nav", None)
    if nav_target and nav_target in visible_tabs:
        st.session_state["nav_radio"] = nav_target
    elif "nav_radio" not in st.session_state or st.session_state["nav_radio"] not in visible_tabs:
        st.session_state["nav_radio"] = visible_tabs[0]

    selected_tab = st.radio("Module:", visible_tabs, key="nav_radio")

    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.12);margin:10px 0;'>", unsafe_allow_html=True)
    with st.expander("Database & AI Status"):
        st.write(f"**Supabase Host:** `{db_instance.supabase_url or 'Not configured'}`")
        st.write(f"**Groq Model:** `{groq_client.model}`")
        st.write(f"**Timetable Solver:** `Google OR-Tools CP-SAT`")
        if db_instance.connection_status == DB_STATUS_MISSING_CONFIG:
            st.warning(
                "**Database not configured.**\n\n"
                "Copy `.env.example` to `.env` and fill in:\n"
                "- `SUPABASE_URL`\n"
                "- `SUPABASE_KEY`\n"
                "- `GROQ_API_KEY`"
            )
        elif db_instance.connection_status == DB_STATUS_CONN_FAILED:
            st.error("Supabase credentials were found but the connection failed. Check your URL and key.")
        if st.button("Refresh Live DB"):
            refresh_from_db()
            st.rerun()

    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.12);margin:10px 0;'>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        logout_user()
        st.rerun()

# ── 6. Render Selected Tab Module ────────────────────────────────────────────

# ----------------------------------------------------
# TAB 1: Persona Dashboard
# ----------------------------------------------------
if selected_tab == TAB_DASHBOARD:

    if active_role == "admin":
        students_list = visible_students
        avg_att = round(
            sum(float(s.get("attendance_pct", 0)) for s in students_list)
            / max(1, len(students_list)), 1
        ) if students_list else 0.0
        conflicts = len([t for t in st.session_state.timetable if t.get("has_conflict")])
        pending_docs = len([d for d in st.session_state.documents if d.get("status") == "review_required"])
        unresolved = [a for a in visible_alerts if not a.get("resolved")]

        # ── Dashboard header ──────────────────────────────────────────────────
        hdr_col, btn_col = st.columns([4, 1])
        with hdr_col:
            render_page_header(
                "School Operations Overview",
                "Monitor student, academic, staffing and administrative operations from one place."
            )
        with btn_col:
            if st.button("Refresh Data", type="primary", use_container_width=True):
                refresh_from_db()
                st.session_state.insights = generate_all_insights(
                    students=st.session_state.get("students", []),
                    teachers=st.session_state.get("teachers", []),
                    teacher_availability=st.session_state.get("teacher_availability", []),
                    timetable=st.session_state.get("timetable", []),
                    documents=st.session_state.get("documents", []),
                )
                st.rerun()

        # ── KPI Cards ─────────────────────────────────────────────────────────
        _sr = st.session_state.get("staffing_report") or calculate_staffing_report(
            teachers=st.session_state.get("teachers", []),
            teacher_availability=st.session_state.get("teacher_availability", []),
            timetable=st.session_state.get("timetable", []),
        )
        _score = _sr.get("staffing_pressure_score", 0)
        _level = _sr.get("staffing_pressure_level", "LOW")
        _staff_status = "good" if _level == "LOW" else ("warning" if _level == "MODERATE" else "danger")

        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            render_kpi_card(
                "Students Enrolled",
                str(len(students_list)) if students_list else "0",
                "Active records" if students_list else "No records yet",
                "good" if students_list else "",
                accent_bg=C["kpi_cream"],
            )
        with k2:
            att_status = "good" if avg_att >= 80 else ("warning" if avg_att >= 60 else "danger")
            render_kpi_card(
                "Average Attendance",
                f"{avg_att}%" if students_list else "0%",
                "School-wide average" if students_list else "No attendance data",
                att_status if students_list else "",
            )
        with k3:
            render_kpi_card(
                "Timetable Conflicts",
                str(conflicts),
                "Active conflicts" if conflicts else "No conflicts detected",
                "danger" if conflicts > 0 else "good",
            )
        with k4:
            render_kpi_card(
                "Documents Pending Review",
                str(pending_docs),
                "Awaiting human review" if pending_docs else "Queue is clear",
                "warning" if pending_docs > 0 else "good",
            )
        with k5:
            render_kpi_card(
                "Staffing Pressure",
                f"{_score}/100",
                f"{_level} — View Insights for details",
                _staff_status,
                accent_bg=C["kpi_cyan"] if _level == "LOW" else "",
            )

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

        # ── Operational Status ────────────────────────────────────────────────
        render_section_header("Operational Status", "Live status across all school modules.")
        op1, op2, op3, op4 = st.columns(4)

        with op1:
            att_level = "LOW" if avg_att >= 80 else ("MODERATE" if avg_att >= 60 else "HIGH")
            render_health_card(
                "Attendance",
                "Healthy" if avg_att >= 80 else ("At Risk" if avg_att >= 60 else "Critical"),
                f"{avg_att}%" if students_list else "0%",
                f"{len(students_list)} students tracked" if students_list else "No attendance data",
                att_level,
            )
            if st.button("View Attendance", key="op_att", use_container_width=True):
                st.session_state["_nav"] = TAB_DATA_LAYER
                st.rerun()

        with op2:
            tt_level = "LOW" if conflicts == 0 else ("MODERATE" if conflicts <= 2 else "HIGH")
            render_health_card(
                "Timetable",
                "No Conflicts" if conflicts == 0 else f"{conflicts} Conflict(s)",
                f"{len(st.session_state.timetable)} slots" if st.session_state.timetable else "0 slots",
                "Schedule is clean" if conflicts == 0 else "Conflicts need resolution",
                tt_level,
            )
            if st.button("View Timetable", key="op_tt", use_container_width=True):
                st.session_state["_nav"] = TAB_TIMETABLE
                st.rerun()

        with op3:
            doc_level = "LOW" if pending_docs == 0 else ("MODERATE" if pending_docs <= 3 else "HIGH")
            render_health_card(
                "Document Processing",
                "Queue Clear" if pending_docs == 0 else f"{pending_docs} Pending",
                f"{len(st.session_state.documents)} total docs" if st.session_state.documents else "0 docs",
                "No documents awaiting review" if pending_docs == 0 else "Review required",
                doc_level,
            )
            if st.button("View Documents", key="op_doc", use_container_width=True):
                st.session_state["_nav"] = TAB_DOCUMENTS
                st.rerun()

        with op4:
            teachers_list = st.session_state.teachers
            absent_count = len([t for t in teachers_list if t.get("status") == "absent"])
            staff_level = "LOW" if absent_count == 0 else ("MODERATE" if absent_count <= 2 else "HIGH")
            render_health_card(
                "Staffing",
                "Fully Staffed" if absent_count == 0 else f"{absent_count} Absent",
                f"{len(teachers_list)} teachers" if teachers_list else "0 teachers",
                "All teachers available" if absent_count == 0 else f"{absent_count} teacher(s) unavailable",
                staff_level,
            )
            if st.button("View Staffing", key="op_staff", use_container_width=True):
                st.session_state["_nav"] = TAB_TEACHERS
                st.rerun()

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

        # ── Priority Alerts + AI Insights ─────────────────────────────────────
        left_col, right_col = st.columns([1, 1])

        with left_col:
            render_section_header("Priority Alerts")
            if unresolved:
                for alt in unresolved:
                    render_alert_card(alt)
                    if st.button("Review", key=f"review_{alt.get('id', alt['title'])}", use_container_width=True):
                        st.session_state["_nav"] = TAB_ALERTS
                        st.rerun()
            else:
                render_empty_state("No active alerts", "All systems are operating normally.", "")
                if st.button("View Alert Center", key="view_alerts", use_container_width=True):
                    st.session_state["_nav"] = TAB_ALERTS
                    st.rerun()

        with right_col:
            render_section_header("AI Analytics Insights")
            live_insights = st.session_state.get("insights", [])
            if live_insights:
                for ins in live_insights[:3]:
                    render_insight_card(ins)
                if st.button("View All Insights", key="view_insights", use_container_width=True):
                    st.session_state["_nav"] = TAB_INSIGHTS
                    st.rerun()
            else:
                render_empty_state(
                    "No insights available",
                    "Click Refresh Data to generate AI analytics.",
                    ""
                )

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

        # ── Quick Actions ─────────────────────────────────────────────────────
        render_section_header("Quick Actions", "Jump directly to key workflows.")
        qa1, qa2, qa3, qa4, qa5, qa6 = st.columns(6)
        with qa1:
            if st.button("Add Student", key="qa_student", type="primary", use_container_width=True):
                st.session_state["_nav"] = TAB_DATA_LAYER
                st.rerun()
        with qa2:
            if st.button("Process Document", key="qa_doc", type="primary", use_container_width=True):
                st.session_state["_nav"] = TAB_DOCUMENTS
                st.rerun()
        with qa3:
            if st.button("Manage Teachers", key="qa_teacher", use_container_width=True):
                st.session_state["_nav"] = TAB_TEACHERS
                st.rerun()
        with qa4:
            if st.button("Generate Timetable", key="qa_tt", use_container_width=True):
                st.session_state["_nav"] = TAB_TIMETABLE
                st.rerun()
        with qa5:
            if st.button("View Alerts", key="qa_alerts", use_container_width=True):
                st.session_state["_nav"] = TAB_ALERTS
                st.rerun()
        with qa6:
            if st.button("Ask AI Copilot", key="qa_copilot", use_container_width=True):
                st.session_state["_nav"] = TAB_COPILOT
                st.rerun()

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

        # ── Live Data Previews ────────────────────────────────────────────────
        prev_left, prev_right = st.columns([3, 2])

        with prev_left:
            render_section_header("Student Records", "Live enrollment data — attendance, fees & risk levels.")
            df_prev = pd.DataFrame(students_list)
            if not df_prev.empty:
                preview_cols = [c for c in ["name", "class", "roll_no", "attendance_pct", "fee_status", "fee_amount_due", "gpa", "risk_level"] if c in df_prev.columns]
                st.dataframe(
                    df_prev[preview_cols].rename(columns={
                        "name": "Name", "class": "Class", "roll_no": "Roll No",
                        "attendance_pct": "Attendance %", "fee_status": "Fee Status",
                        "fee_amount_due": "Amount Due (₹)", "gpa": "GPA", "risk_level": "Risk"
                    }),
                    use_container_width=True, hide_index=True
                )
                if st.button("Open Full Data Layer →", key="prev_data_layer", use_container_width=True):
                    st.session_state["_nav"] = TAB_DATA_LAYER
                    st.rerun()
            else:
                render_empty_state("No student records", "Run the demo seed script to populate data.", "")

        with prev_right:
            render_section_header("Faculty Status", "Live teacher roster and availability.")
            teachers_prev = st.session_state.get("teachers", [])
            if teachers_prev:
                df_tch = pd.DataFrame(teachers_prev)
                tch_cols = [c for c in ["name", "subject", "assigned_classes", "status"] if c in df_tch.columns]
                st.dataframe(
                    df_tch[tch_cols].rename(columns={
                        "name": "Teacher", "subject": "Subject",
                        "assigned_classes": "Classes", "status": "Status"
                    }),
                    use_container_width=True, hide_index=True
                )
                if st.button("Open Teacher Roster →", key="prev_teachers", use_container_width=True):
                    st.session_state["_nav"] = TAB_TEACHERS
                    st.rerun()
            else:
                render_empty_state("No teacher records", "Run the demo seed script to populate data.", "")

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        render_section_header("Master Timetable", "Live schedule — conflicts and substitute assignments highlighted.")
        df_tt_prev = pd.DataFrame(st.session_state.get("timetable", []))
        if not df_tt_prev.empty:
            tt_cols = [c for c in ["class_name", "period", "time", "subject", "teacher_name", "room", "has_conflict", "is_substitute", "substitute_teacher"] if c in df_tt_prev.columns]
            st.dataframe(
                df_tt_prev[tt_cols].rename(columns={
                    "class_name": "Class", "period": "Period", "time": "Time",
                    "subject": "Subject", "teacher_name": "Teacher", "room": "Room",
                    "has_conflict": "Conflict?", "is_substitute": "Substitute?",
                    "substitute_teacher": "Substitute Teacher"
                }),
                use_container_width=True, hide_index=True
            )
            if st.button("Open Timetable Engine →", key="prev_timetable", use_container_width=True):
                st.session_state["_nav"] = TAB_TIMETABLE
                st.rerun()
        else:
            render_empty_state("No timetable slots", "Run the demo seed script to populate data.", "")

    elif active_role == "teacher":
        render_page_header(
            "Teacher Dashboard",
            "Manage class attendance and monitor student records in real time."
        )
        render_section_header("Class Attendance", "Mark present or absent — updates Supabase instantly.")

        students_list = visible_students
        if students_list:
            for stu in students_list:
                att_pct = float(stu.get('attendance_pct', 0))
                att_status = "good" if att_pct >= 80 else ("warning" if att_pct >= 60 else "danger")
                badge_level = "success" if att_pct >= 80 else ("warning" if att_pct >= 60 else "danger")
                card_accent = C["success"] if att_pct >= 80 else (C["warning"] if att_pct >= 60 else C["danger"])
                st.markdown(
                    f"""
<div style="background:{C['surface']};border:1px solid {C['border']};border-left:3px solid {card_accent};
            border-radius:8px;padding:12px 18px;margin-bottom:8px;
            box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;">
        <div style="flex:1;">
            <div style="font-size:0.9rem;font-weight:700;color:{C['navy']};">{stu['name']}</div>
            <div style="font-size:0.78rem;color:{C['text_muted']};margin-top:2px;">Class {stu.get('class', '—')} &nbsp;·&nbsp; Attendance: <strong>{att_pct}%</strong></div>
        </div>
    </div>
</div>""",
                    unsafe_allow_html=True
                )
                c1, c2, c3 = st.columns([2, 1, 1])
                with c2:
                    if st.button("Mark Present", key=f"pres_{stu['id']}", type="primary", use_container_width=True):
                        mark_attendance(stu['id'], True)
                        st.rerun()
                with c3:
                    if st.button("Mark Absent", key=f"abs_{stu['id']}", use_container_width=True):
                        mark_attendance(stu['id'], False)
                        st.rerun()
        else:
            render_empty_state(
                "No enrolled students",
                "Add students via the AI Document Reader tab to begin marking attendance.",
                ""
            )

    elif active_role == "student":
        if visible_students:
            stu = visible_students[0]
            render_page_header(
                f"Welcome, {stu['name']}",
                f"Class {stu.get('class', '—')}  ·  Roll No: {stu.get('roll_no', 'N/A')}"
            )

            att_pct = float(stu.get('attendance_pct', 0))
            gpa_val = stu.get('gpa', 0)
            fee_due = stu.get('fee_amount_due', 0)
            fee_status = str(stu.get('fee_status', '')).lower()

            k1, k2, k3 = st.columns(3)
            with k1:
                att_status = "good" if att_pct >= 80 else ("warning" if att_pct >= 60 else "danger")
                render_kpi_card(
                    "My Attendance",
                    f"{att_pct}%",
                    "Above threshold" if att_pct >= 75 else "Below 75% — action required",
                    att_status,
                )
            with k2:
                gpa_status = "good" if float(gpa_val or 0) >= 3.0 else ("warning" if float(gpa_val or 0) >= 2.0 else "danger")
                render_kpi_card(
                    "Academic GPA",
                    f"{gpa_val} / 4.0",
                    "Current semester GPA",
                    gpa_status,
                )
            with k3:
                fee_card_status = "good" if fee_status == "paid" else ("warning" if fee_status == "pending" else "danger")
                render_kpi_card(
                    "Fee Status",
                    f"\u20b9{fee_due:,}" if fee_due else "\u20b90",
                    fee_status.upper() if fee_status else "No data",
                    fee_card_status,
                )

            render_section_header("My Class Timetable", "Live schedule from Supabase.")
            df_t = pd.DataFrame(visible_timetable)
            if not df_t.empty:
                cols_to_show = [c for c in ["period", "time", "subject", "teacher_name", "room"] if c in df_t.columns]
                st.dataframe(df_t[cols_to_show], use_container_width=True)
            else:
                render_empty_state("No timetable available", "No active schedule in Supabase.", "")
        else:
            render_empty_state("No student records", "No student records found in Supabase.", "")

    else:  # parent
        if visible_students:
            stu = visible_students[0]
            render_page_header(
                "Parent Portal",
                f"Monitoring: {stu['name']}  ·  Class {stu.get('class', '—')}"
            )

            fee_due = stu.get('fee_amount_due', 0)
            fee_status = str(stu.get('fee_status', '')).lower()
            att_pct = float(stu.get('attendance_pct', 100.0))

            c1, c2 = st.columns(2)
            with c1:
                render_section_header("Tuition Fee Invoice")
                fee_card_status = "good" if fee_status == "paid" else ("warning" if fee_status == "pending" else "danger")
                render_kpi_card(
                    "Amount Due",
                    f"\u20b9{fee_due:,}",
                    fee_status.upper() if fee_status else "No data",
                    fee_card_status,
                )
                st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
                if stu.get("fee_status") != "paid":
                    if st.button("Pay Fee Online", type="primary", use_container_width=True):
                        pay_fee(stu["id"])
                        st.success("Payment successful. Fee ledger updated in Supabase.")
                        st.rerun()
                else:
                    st.markdown(
                        render_status_badge("All Fees Paid", "success"),
                        unsafe_allow_html=True
                    )

            with c2:
                render_section_header("Attendance Status")
                att_status = "good" if att_pct >= 80 else ("warning" if att_pct >= 60 else "danger")
                render_kpi_card(
                    "Attendance",
                    f"{att_pct}%",
                    "Above threshold" if att_pct >= 75 else "Below 75% — contact class teacher",
                    att_status,
                )
                st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
                st.progress(min(1.0, att_pct / 100.0))
                if att_pct < 75:
                    st.warning("Attendance is below the 75% threshold. Please contact the class teacher.")
        else:
            render_empty_state("No student records", "No student records found in Supabase database.", "")

# ----------------------------------------------------
# TAB 2: AI Document Reader (Multi-Slot Form Inputs)
# ----------------------------------------------------
elif selected_tab == TAB_DOCUMENTS:
    render_page_header(
        "AI Document Reader",
        "Upload admission forms, fee receipts, or paste raw text. OCR + Groq AI extracts structured JSON with full Pydantic validation & audit trail."
    )

    doc_type_choice = st.selectbox("Document Category:", ["admission_form", "fee_receipt", "leave_application"])

    doc_tab1, doc_tab2, doc_tab3 = st.tabs(["📷 Slot 1: Form Picture Upload", "📄 Slot 2: Document File Upload", "✍️ Slot 3: Paste Raw Form Text"])

    with doc_tab1:
        render_section_header("Slot 1: Upload Admission Form / Receipt Image")
        img_file = st.file_uploader("Drop image or document (PNG, JPG, WEBP, PDF, TXT, CSV):", type=["png", "jpg", "jpeg", "webp", "pdf", "txt", "csv"], key="doc_img_slot")
        if img_file:
            st.session_state["_doc_img_file"] = img_file
        if st.session_state.get("_doc_img_file") and st.button("Run OCR & Groq AI Form Extraction", key="btn_doc_img"):
            f = st.session_state.pop("_doc_img_file")
            with st.spinner("Extracting fields via Groq AI..."):
                try:
                    doc_rec, val_stu = process_and_save_document_input(file_obj=f, doc_type=doc_type_choice)
                    if doc_rec:
                        st.success(f"Parsed `{f.name}` via Groq AI! Added to review inbox below.")
                    else:
                        st.error("Extraction returned empty. Check your file content.")
                except Exception as e:
                    st.error(f"Extraction failed: {e}")
            st.rerun()

    with doc_tab2:
        render_section_header("Slot 2: Upload Document File (TXT, CSV, PDF)")
        doc_file = st.file_uploader("Drop document file (TXT, CSV, PDF):", type=["txt", "csv", "pdf"], key="doc_file_slot")
        if doc_file:
            st.session_state["_doc_file"] = doc_file
        if st.session_state.get("_doc_file") and st.button("Extract Document via Groq AI", key="btn_doc_file"):
            f = st.session_state.pop("_doc_file")
            with st.spinner("Extracting fields via Groq AI..."):
                try:
                    doc_rec, val_stu = process_and_save_document_input(file_obj=f, doc_type=doc_type_choice)
                    if doc_rec:
                        st.success(f"Extracted `{f.name}`! Added to review inbox below.")
                    else:
                        st.error("Extraction returned empty. Check your file content.")
                except Exception as e:
                    st.error(f"Extraction failed: {e}")
            st.rerun()

    with doc_tab3:
        render_section_header("Slot 3: Paste User-Defined Raw Text")
        paste_text = st.text_area(
            "Paste form text (e.g. 'ADMISSION FORM: Student Rahul Verma, Class 8A, Parent Rajesh Verma, Phone +91 98765 12345'):",
            height=120,
            key="doc_text_slot"
        )
        if paste_text and st.button("Extract Raw Text via Groq AI", key="btn_doc_text"):
            with st.spinner("Extracting fields via Groq AI..."):
                try:
                    doc_rec, val_stu = process_and_save_document_input(raw_text_input=paste_text, doc_type=doc_type_choice)
                    if doc_rec:
                        st.success("Extracted via Groq AI! Added to review inbox below.")
                    else:
                        st.error("Extraction returned empty. Check your input text.")
                except Exception as e:
                    st.error(f"Extraction failed: {e}")
            st.rerun()

    render_section_header("Human-in-the-Loop Review & Audit Queue", "Review and confirm AI-extracted fields before committing to Supabase.")
    docs_list = st.session_state.documents
    if docs_list:
        c_sel, c_view = st.columns([1, 2])
        with c_sel:
            render_section_header("Document Inbox")
            doc_options = [f"{d['id']} - {d['filename']} [{d.get('source_type', 'file')}]" for d in docs_list]
            selected_option = st.selectbox("Select document record:", doc_options)
            sel_id = selected_option.split(" - ")[0]
            selected_doc = next(d for d in docs_list if d["id"] == sel_id)

            render_section_header("Audit Trail Details")
            st.write(f"**Source Type:** `{selected_doc.get('source_type')}`")
            st.write(f"**Status:** `{selected_doc.get('status')}`")
            if selected_doc.get("validation_errors"):
                st.error(f"Validation Warning: {selected_doc.get('validation_errors')}")

            render_section_header("Raw Extracted OCR Stream")
            st.code(selected_doc.get("ocr_raw_text", ""), language="text")

        with c_view:
            render_section_header(f"Human Review: {selected_doc['filename']}")
            st.caption("Review or edit Groq AI extracted fields before permanent student enrollment in Supabase.")

            fields = selected_doc.get("fields", {}) or {}
            updated_fields = {}
            for k, v in fields.items():
                updated_fields[k] = st.text_input(f"Field: {k.replace('_', ' ').title()}", value=str(v) if v is not None else "", key=f"field_{selected_doc['id']}_{k}")

            if st.button("💾 Confirm & Save Student to Supabase", key=f"btn_commit_{selected_doc['id']}"):
                commit_doc(selected_doc["id"], updated_fields)
                st.success("Extracted Student Record committed to Supabase Database!")
                st.rerun()
    else:
        st.info("No document audit records in database yet. Use input slots above to upload.")

# ----------------------------------------------------
# TAB 3: Teacher Availability & Roster Manager (NEW)
# ----------------------------------------------------
elif selected_tab == TAB_TEACHERS:
    render_page_header(
        "Teacher Availability & Roster",
        "Upload teacher roster files or paste custom availability instructions. Groq AI parses roster & constraints, then OR-Tools solver re-assigns schedules."
    )

    t_slot1, t_slot2 = st.tabs(["📄 Slot 1: Upload Roster File", "✍️ Slot 2: Paste Teacher Availability Text"])

    with t_slot1:
        render_section_header("Slot 1: Upload Roster / Availability File")
        t_file = st.file_uploader("Upload Roster File (TXT, CSV, PDF, Image):", type=["txt", "csv", "pdf", "png", "jpg"], key="tch_file_slot")
        if t_file:
            st.session_state["_tch_file"] = t_file
        if st.session_state.get("_tch_file") and st.button("Parse Roster File via Groq AI", key="btn_tch_file"):
            f = st.session_state.pop("_tch_file")
            n_tch, n_av, text = process_and_save_teacher_input(file_obj=f)
            st.success(f"Parsed `{f.name}`! Created {n_tch} teacher record(s) and {n_av} availability rule(s) in Supabase. Timetable re-optimized via OR-Tools!")
            st.rerun()

    with t_slot2:
        render_section_header("Slot 2: Paste Custom Teacher Availability Text")
        t_text = st.text_area(
            "Paste teacher info (e.g. 'Dr. Sunita Mehta teaches Mathematics for 8A and 8B. Mrs. Kavita Singh is unavailable on Monday Period 3'):",
            height=120,
            key="tch_text_slot"
        )
        if t_text and st.button("Process Teacher Info via Groq AI", key="btn_tch_text"):
            n_tch, n_av, text = process_and_save_teacher_input(raw_text_input=t_text)
            st.success(f"Processed teacher text! Saved {n_tch} teacher(s) & {n_av} availability rule(s) in Supabase. Timetable re-optimized via OR-Tools!")
            st.rerun()

    render_section_header("Faculty Directory & Availability Rules", "Live records from Supabase.")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        render_section_header("Faculty Directory")
        teachers_list = st.session_state.teachers
        if teachers_list:
            df_t = pd.DataFrame(teachers_list)
            cols_t = [c for c in ["id", "name", "subject", "email", "assigned_classes", "status"] if c in df_t.columns]
            st.dataframe(df_t[cols_t], use_container_width=True)
        else:
            st.info("No teachers enrolled in Supabase yet. Use input slots above to add teachers.")

    with col_t2:
        render_section_header("Availability & Leave Constraints")
        avails_list = st.session_state.teacher_availability
        if avails_list:
            df_av = pd.DataFrame(avails_list)
            cols_av = [c for c in ["teacher_name", "day_of_week", "period", "status", "notes"] if c in df_av.columns]
            st.dataframe(df_av[cols_av], use_container_width=True)
        else:
            st.info("No availability constraints in Supabase.")

# ----------------------------------------------------
# TAB 4: Smart Timetable Engine (OR-Tools Solver)
# ----------------------------------------------------
elif selected_tab == TAB_TIMETABLE:
    render_page_header(
        "Smart Timetable Engine",
        "Upload timetable schedules via Picture, File, or Raw Text. Groq AI extracts slot constraints → Pydantic validates → Google OR-Tools solves conflicts → Supabase stores result."
    )

    tt_tab1, tt_tab2, tt_tab3 = st.tabs(["📷 Slot 1: Timetable Picture Image", "📄 Slot 2: Document / CSV File", "✍️ Slot 3: Paste Schedule Text"])

    with tt_tab1:
        render_section_header("Slot 1: Timetable Picture Upload")
        img_tt = st.file_uploader("Upload timetable image (PNG, JPG, PDF):", type=["png", "jpg", "jpeg", "pdf"], key="tt_img_slot")
        if img_tt:
            st.session_state["_tt_img"] = img_tt
        if st.session_state.get("_tt_img") and st.button("Extract & Solve Timetable Picture", key="btn_tt_img"):
            f = st.session_state.pop("_tt_img")
            slots, warnings = process_and_save_timetable_input(file_obj=f)
            st.success(f"Generated {len(slots)} conflict-free slots using Google OR-Tools! Saved to Supabase.")
            if warnings:
                for w in warnings:
                    st.warning(w)
            st.rerun()

    with tt_tab2:
        render_section_header("Slot 2: Document / CSV Timetable File")
        doc_tt = st.file_uploader("Upload document file (TXT, CSV, PDF):", type=["txt", "csv", "pdf"], key="tt_doc_slot")
        if doc_tt:
            st.session_state["_tt_doc"] = doc_tt
        if st.session_state.get("_tt_doc") and st.button("Extract & Solve Document Timetable", key="btn_tt_doc"):
            f = st.session_state.pop("_tt_doc")
            slots, warnings = process_and_save_timetable_input(file_obj=f)
            st.success(f"Generated {len(slots)} slots using OR-Tools Solver! Saved to Supabase.")
            st.rerun()

    with tt_tab3:
        render_section_header("Slot 3: Paste Schedule Text")
        paste_tt = st.text_area(
            "Paste timetable text (e.g. '8A, Mathematics, Dr. Sunita Mehta, Room 201\n8A, Science, Prof. Rajesh Gupta, Science Lab'):",
            height=120,
            key="tt_text_slot"
        )
        if paste_tt and st.button("Solve Schedule Text via OR-Tools", key="btn_tt_text"):
            slots, warnings = process_and_save_timetable_input(raw_text_input=paste_tt)
            st.success(f"Solved schedule via OR-Tools! Saved to Supabase.")
            st.rerun()

    render_section_header("Faculty Absence & Substitution Controller")
    teachers_list = st.session_state.teachers
    if teachers_list:
        cols = st.columns(len(teachers_list))
        for idx, t in enumerate(teachers_list):
            with cols[idx]:
                is_abs = t.get("status") == "absent"
                lbl = f"❌ {t['name']} (Absent)" if is_abs else f"✅ {t['name']}"
                if st.button(lbl, key=f"t_btn_{t['id']}"):
                    toggle_teacher(t["id"])
                    st.rerun()

    # Show solver warnings from last toggle_teacher() call
    solver_warnings = st.session_state.pop("solver_warnings", None)
    if solver_warnings:
        for w in solver_warnings:
            st.warning(f"⚠️ Solver: {w}")

    conflicts = [slot for slot in st.session_state.timetable if slot.get("has_conflict")]
    if conflicts:
        st.error(f"⚠️ {len(conflicts)} Timetable Conflict(s) Detected!")
        if st.button("⚡ Run Google OR-Tools Solver to Auto-Assign Free Substitutes"):
            solve_timetable_reassignment()
            st.success("Google OR-Tools CP-SAT Solver re-assigned free substitute teachers in Supabase!")
            st.rerun()
    else:
        st.success("✅ Zero Conflicts — Schedule fully optimized by Google OR-Tools Solver in Supabase Database")

    render_section_header("Master Timetable Grid", "Live schedule from Supabase.")
    df = pd.DataFrame(st.session_state.timetable)
    if not df.empty:
        cols_to_show = [c for c in ["period", "time", "class_name", "subject", "teacher_name", "room", "has_conflict", "is_substitute", "substitute_teacher"] if c in df.columns]
        st.dataframe(df[cols_to_show], use_container_width=True)
    else:
        st.info("No timetable slots in Supabase database. Upload schedule above.")

# ----------------------------------------------------
# TAB 5: Unified Data Layer
# ----------------------------------------------------
elif selected_tab == TAB_DATA_LAYER:
    render_page_header(
        "Unified Data Layer",
        "Single source of truth in Supabase joining Student ID ↔ Attendance ↔ Fees ↔ Schedule."
    )

    df_stu = pd.DataFrame(st.session_state.students)
    if not df_stu.empty:
        cols_to_show = [c for c in ["id", "name", "roll_no", "class", "parent_name", "parent_phone", "attendance_pct", "fee_status", "fee_amount_due", "gpa", "risk_level"] if c in df_stu.columns]
        st.dataframe(df_stu[cols_to_show], use_container_width=True)
    else:
        st.info("No student records in Supabase.")

# ----------------------------------------------------
# TAB 6: Proactive Alerts Center
# ----------------------------------------------------
elif selected_tab == TAB_ALERTS:
    render_page_header(
        "Proactive Alerts Center",
        "Rule-based monitoring across attendance, fees, timetable, and staffing. Alerts are routed by role."
    )
    unresolved_alerts = [a for a in visible_alerts if not a.get("resolved")]
    if unresolved_alerts:
        for alt in unresolved_alerts:
            render_alert_card(alt)
    else:
        st.success("✅ All alerts resolved in Supabase database.")

# ----------------------------------------------------
# TAB 7: Predictive Insights Engine
# ----------------------------------------------------
elif selected_tab == TAB_INSIGHTS:
    render_page_header(
        "Predictive Insights",
        "Real-time calculations over live school data. Works with or without Supabase. Click Recalculate after any data change."
    )

    col_btn, col_src = st.columns([1, 3])
    with col_btn:
        if st.button("⚡ Recalculate Insights"):
            st.session_state.insights = generate_all_insights(
                students=st.session_state.get("students", []),
                teachers=st.session_state.get("teachers", []),
                teacher_availability=st.session_state.get("teacher_availability", []),
                timetable=st.session_state.get("timetable", []),
                documents=st.session_state.get("documents", []),
            )
            st.session_state.staffing_report = calculate_staffing_report(
                teachers=st.session_state.get("teachers", []),
                teacher_availability=st.session_state.get("teacher_availability", []),
                timetable=st.session_state.get("timetable", []),
            )
            st.rerun()
    with col_src:
        src = "⚡ Supabase DB" if db_instance.is_supabase_active else "💻 In-Memory (DB offline)"
        st.caption(f"Data source: {src} · {len(st.session_state.get('students', []))} students · "
                   f"{len(st.session_state.get('teachers', []))} teachers · "
                   f"{len(st.session_state.get('timetable', []))} timetable slots")

    st.markdown("---")

    insights_list = st.session_state.get("insights", [])
    if not insights_list:
        st.info("📊 No insights available. Click ‘Recalculate Insights’ to generate analytics.")
    else:
        for ins in insights_list:
            render_insight_card(ins)

    # ── Smart Staffing Forecast ──────────────────────────────────────────────
    render_section_header("Smart Staffing Risk Score", "Projected staffing pressure based on current workload and availability. Deterministic rule-based score — not a machine-learning model.")

    sr = st.session_state.get("staffing_report") or calculate_staffing_report(
        teachers=st.session_state.get("teachers", []),
        teacher_availability=st.session_state.get("teacher_availability", []),
        timetable=st.session_state.get("timetable", []),
    )

    if not sr.get("has_sufficient_data"):
        st.info(
            "📊 Insufficient teacher data to generate a staffing forecast. "
            "Add teacher records via the Teacher Availability & Roster tab."
        )
    else:
        # Score banner
        render_staffing_banner(sr)

        # Four KPI tiles
        k1, k2, k3, k4 = st.columns(4)
        k1.metric(
            "Available Teachers",
            f"{sr['available_teachers']} / {sr['total_teachers']}",
            f"{sr['availability_pct']}%",
        )
        k2.metric(
            "Avg Teaching Load",
            f"{sr['avg_workload']} slots",
            f"Max: {sr['max_workload']}",
        )
        k3.metric(
            "Coverage Risk",
            f"{sr['uncovered_slots']} uncovered",
            f"{sr['coverage_pct']}% covered",
            delta_color="inverse",
        )
        k4.metric(
            "Substitute Requirement",
            f"{sr['substitute_required']} slot(s)",
            f"{sr['substitute_slots']} active subs",
        )

        # Score breakdown expander
        with st.expander("🔍 Score Breakdown (formula details)"):
            bd = sr["score_breakdown"]
            st.markdown(
                f"""| Signal | Weight | Value | Contribution |
| --- | --- | --- | --- |
| A — Unavailability ratio | 35 | {sr['unavailable_teachers']}/{sr['total_teachers']} teachers | {bd['signal_a']} |
| B — Timetable conflict ratio | 30 | {sr['uncovered_slots']}/{sr['total_slots']} slots | {bd['signal_b']} |
| C — Workload overload ratio | 20 | {sr['overloaded_count']}/{sr['total_teachers']} teachers | {bd['signal_c']} |
| D — Substitute dependency ratio | 15 | {sr['substitute_slots']}/{sr['total_slots']} slots | {bd['signal_d']} |
| **Total** | **100** | | **{sr['staffing_pressure_score']}** |"""
            )

        # Workload per teacher
        if sr["slots_per_teacher"]:
            with st.expander("📊 Teacher Workload Breakdown"):
                wl_df = pd.DataFrame(
                    [{"Teacher": k, "Slots": v,
                      "Status": "⚠️ Overloaded" if v > sr["overload_threshold"] else "✅ Normal"}
                     for k, v in sorted(sr["slots_per_teacher"].items(),
                                        key=lambda x: x[1], reverse=True)]
                )
                st.dataframe(wl_df, use_container_width=True, hide_index=True)

        # Recommendations
        render_section_header("Staffing Recommendations")
        for i, rec in enumerate(sr["recommendations"], 1):
            render_recommendation_item(i, rec)

# ----------------------------------------------------
# TAB 8: AI Copilot (NLQ) — Grounded Intelligence Layer
# ----------------------------------------------------
elif selected_tab == TAB_COPILOT:
    render_page_header(
        "AI Copilot",
        "Grounded natural-language interface over live school data. All numerical answers come from the Analytics & Staffing engines — the LLM only explains them."
    )

    # Example questions
    render_copilot_prompt_card([
        "How is our staffing situation?",
        "Which teachers are overloaded?",
        "Are there any timetable conflicts?",
        "How many students are at attendance risk?",
        "Give me a school operations summary.",
    ])

    # Groq status badge
    if groq_client.is_available():
        st.markdown(render_status_badge("⚡ Groq LLM Active", "success"), unsafe_allow_html=True)
    else:
        st.markdown(
            render_status_badge("⚙️ Groq API key missing — deterministic fallback active", "warning"),
            unsafe_allow_html=True,
        )

    st.markdown("")

    # Render conversation history
    for msg in st.session_state.copilot_messages:
        sender = msg.get("sender", "user")
        with st.chat_message(sender):
            st.write(msg.get("text", ""))

    # Chat input
    prompt = st.chat_input("Ask about students, attendance, fees, teachers, timetable, staffing...")
    if prompt:
        # 1. Save user message
        add_copilot_message({"sender": "user", "text": prompt})

        # 2. Build conversation history for context (exclude current prompt)
        history = [
            {"role": "user" if m["sender"] == "user" else "assistant", "content": m["text"]}
            for m in st.session_state.copilot_messages[:-1]  # exclude the message just added
            if m.get("text")
        ]

        # 3. Get grounded answer from copilot engine
        with st.spinner("Thinking..."):
            answer, intent = answer_question(
                question=prompt,
                students=st.session_state.get("students", []),
                teachers=st.session_state.get("teachers", []),
                teacher_availability=st.session_state.get("teacher_availability", []),
                timetable=st.session_state.get("timetable", []),
                documents=st.session_state.get("documents", []),
                conversation_history=history,
                groq_client_instance=groq_client,
                existing_insights=st.session_state.get("insights"),
                existing_staffing_report=st.session_state.get("staffing_report"),
            )

        # 4. Save and display AI response
        add_copilot_message({"sender": "ai", "text": answer})
        st.rerun()
