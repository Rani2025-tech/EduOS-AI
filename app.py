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
    initial_sidebar_state="expanded"
)

# ── 2. Bootstrap auth + CSS ───────────────────────────────────────────────────
init_auth_session()
inject_global_styles()

# ── 3. Login gate ────────────────────────────────────────────────────────────
if not is_authenticated():
    st.markdown("""
        <div style="max-width:420px;margin:80px auto 0;">
            <div style="text-align:center;margin-bottom:32px;">
                <div style="font-size:2rem;font-weight:800;color:#17365D;">
                    EduOS <span style="color:#2563EB;">AI</span>
                </div>
                <div style="font-size:0.85rem;color:#5B6B7F;margin-top:4px;">
                    School Operations Platform
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        st.markdown("#### Sign in to your account")
        username_input = st.text_input("Username", placeholder="Enter your username")
        password_input = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

        if submitted:
            if login_user(username_input, password_input):
                init_session_state()
                st.rerun()
            else:
                st.error(st.session_state.get("auth_error", "Login failed."))

    if not db_instance.is_supabase_active:
        st.warning(
            "Supabase is not connected. Fix your `.env` configuration before logging in.",
            icon="⚠️",
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
    st.markdown("""
        <div style="padding: 8px 0 4px;">
            <div style="font-size:1.5rem;font-weight:800;color:#17365D;letter-spacing:-0.02em;line-height:1.2;">
                EduOS <span style="color:#2563EB;">AI</span>
            </div>
            <div style="font-size:0.8rem;color:#5B6B7F;font-weight:500;margin-top:2px;">School Operations Platform</div>
        </div>
    """, unsafe_allow_html=True)
with col_status:
    render_db_status_bar(
        db_instance.connection_status, unresolved_count,
        DB_STATUS_CONNECTED, DB_STATUS_MISSING_CONFIG
    )

st.markdown("<hr style='border:none;border-top:1px solid #D9E2EC;margin:8px 0 16px;'>", unsafe_allow_html=True)

# ── 5. Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:16px 0 12px;border-bottom:1px solid #D9E2EC;margin-bottom:12px;">
            <div style="font-size:1.1rem;font-weight:800;color:#17365D;">EduOS AI</div>
            <div style="font-size:0.72rem;color:#5B6B7F;font-weight:500;margin-top:2px;">School Operations Platform</div>
        </div>
    """, unsafe_allow_html=True)

    # ── Signed-in user badge (read-only — no free persona switching) ────────────
    role_icon  = ROLE_ICONS.get(active_role, "👤")
    role_label = ROLE_LABELS.get(active_role, active_role.title())
    st.markdown(
        f"""
        <div style="background:#F0F4FF;border:1px solid #C7D7F5;border-radius:8px;
                    padding:10px 14px;margin-bottom:12px;">
            <div style="font-size:0.78rem;color:#5B6B7F;font-weight:500;">Signed in as</div>
            <div style="font-size:0.95rem;font-weight:700;color:#17365D;margin-top:2px;">
                {role_icon} {auth['username']}
            </div>
            <div style="font-size:0.75rem;color:#2563EB;margin-top:2px;">{role_label}</div>
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

    st.markdown("<hr style='border:none;border-top:1px solid #D9E2EC;margin:10px 0;'>", unsafe_allow_html=True)
    with st.expander("Database & AI Status"):
        st.write(f"**Supabase Host:** `{db_instance.supabase_url or 'Not configured'}`")
        st.write(f"**Groq Model:** `llama-3.3-70b-versatile`")
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

    st.markdown("<hr style='border:none;border-top:1px solid #D9E2EC;margin:10px 0;'>", unsafe_allow_html=True)
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
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            render_kpi_card(
                "Students Enrolled",
                str(len(students_list)) if students_list else "0",
                "Active records" if students_list else "No records yet",
                "good" if students_list else "",
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
            live_insights = st.session_state.insights
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
                st.markdown(
                    f"""
<div style="background:#FFFFFF;border:1px solid #D9E2EC;border-left:3px solid {'#16A34A' if att_pct >= 80 else ('#D97706' if att_pct >= 60 else '#DC2626')};
            border-radius:8px;padding:12px 18px;margin-bottom:8px;
            box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;">
        <div style="flex:1;">
            <div style="font-size:0.9rem;font-weight:700;color:#17365D;">{stu['name']}</div>
            <div style="font-size:0.78rem;color:#5B6B7F;margin-top:2px;">Class {stu.get('class', '—')} &nbsp;·&nbsp; Attendance: <strong>{att_pct}%</strong></div>
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
        img_file = st.file_uploader("Drop image (PNG, JPG, WEBP, PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key="doc_img_slot")
        if img_file and st.button("Run OCR & Groq AI Form Extraction", key="btn_doc_img"):
            doc_rec, val_stu = process_and_save_document_input(file_obj=img_file, doc_type=doc_type_choice)
            st.success(f"Parsed `{img_file.name}` via Groq AI! Saved audit trail in Supabase. Added to review inbox below.")
            st.rerun()

    with doc_tab2:
        render_section_header("Slot 2: Upload Document File (TXT, CSV, PDF)")
        doc_file = st.file_uploader("Drop document file:", type=["txt", "csv", "pdf"], key="doc_file_slot")
        if doc_file and st.button("Extract Document via Groq AI", key="btn_doc_file"):
            doc_rec, val_stu = process_and_save_document_input(file_obj=doc_file, doc_type=doc_type_choice)
            st.success(f"Extracted `{doc_file.name}`! Added to review inbox below.")
            st.rerun()

    with doc_tab3:
        render_section_header("Slot 3: Paste User-Defined Raw Text")
        paste_text = st.text_area(
            "Paste form text (e.g. 'ADMISSION FORM: Student Rahul Verma, Class 8A, Parent Rajesh Verma, Phone +91 98765 12345'):",
            height=120,
            key="doc_text_slot"
        )
        if paste_text and st.button("Extract Raw Text via Groq AI", key="btn_doc_text"):
            doc_rec, val_stu = process_and_save_document_input(raw_text_input=paste_text, doc_type=doc_type_choice)
            st.success("Extracted user text via Groq AI! Saved audit trail in Supabase.")
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
        t_file = st.file_uploader("Upload Roster File (TXT, CSV, Image):", type=["txt", "csv", "png", "jpg"], key="tch_file_slot")
        if t_file and st.button("Parse Roster File via Groq AI", key="btn_tch_file"):
            n_tch, n_av, text = process_and_save_teacher_input(file_obj=t_file)
            st.success(f"Parsed `{t_file.name}`! Created {n_tch} teacher record(s) and {n_av} availability rule(s) in Supabase. Timetable re-optimized via OR-Tools!")
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
        if img_tt and st.button("Extract & Solve Timetable Picture", key="btn_tt_img"):
            slots, warnings = process_and_save_timetable_input(file_obj=img_tt)
            st.success(f"Generated {len(slots)} conflict-free slots using Google OR-Tools! Saved to Supabase.")
            if warnings:
                for w in warnings:
                    st.warning(w)
            st.rerun()

    with tt_tab2:
        render_section_header("Slot 2: Document / CSV Timetable File")
        doc_tt = st.file_uploader("Upload document file (TXT, CSV):", type=["txt", "csv"], key="tt_doc_slot")
        if doc_tt and st.button("Extract & Solve Document Timetable", key="btn_tt_doc"):
            slots, warnings = process_and_save_timetable_input(file_obj=doc_tt)
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
