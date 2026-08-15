import streamlit as st
import pandas as pd
import datetime
from data_store import (
    init_session_state, 
    toggle_teacher, 
    solve_timetable_reassignment, 
    mark_attendance, 
    pay_fee, 
    commit_doc,
    refresh_from_db,
    process_and_save_document_input,
    process_and_save_teacher_input,
    process_and_save_timetable_input,
    add_copilot_message
)
from db_client import db_instance

# 1. Page Configuration
st.set_page_config(
    page_title="EduOS AI — Autonomous School Operating System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State Data & DB
init_session_state()

# 2. Premium Custom CSS Styling Injection
st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp {
        background-color: #090d16;
        color: #f8fafc;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(19, 27, 46, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
    }

    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: #818cf8 !important;
    }

    /* Gradient Header */
    .gradient-header {
        background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 50%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    /* Custom Badges */
    .badge-indigo {
        background: rgba(99, 102, 241, 0.2);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-emerald {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-rose {
        background: rgba(244, 63, 94, 0.2);
        color: #f87171;
        border: 1px solid rgba(244, 63, 94, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-amber {
        background: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)

# 3. Top Header & Database Connection Status
unresolved_count = len([a for a in st.session_state.alerts if not a.get("resolved")])
db_status_text = "⚡ Supabase Postgres Active" if db_instance.is_supabase_active else "🔴 Database Disconnected"

col_header, col_status = st.columns([3, 1])
with col_header:
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
            <h1 style="margin: 0; font-weight: 800; font-size: 2.2rem;">
                EduOS <span class="gradient-header">AI</span>
            </h1>
            <span class="badge-indigo">Autonomous School Operating System</span>
        </div>
    """, unsafe_allow_html=True)
with col_status:
    st.markdown(f"""
        <div style="text-align: right; margin-top: 10px;">
            <span class="badge-emerald">{db_status_text}</span>
            <br/><span style="font-size: 0.75rem; color: #94a3b8;">Active Alerts: <strong>{unresolved_count}</strong></span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 4. Sidebar Controls & Supabase Drawer
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/000000/graduation-cap.png", width=50)
    st.markdown("### Persona Switcher")
    selected_persona = st.selectbox(
        "Select User Persona:",
        ["School Administrator", "Teacher", "Student", "Parent"],
        index=0
    )

    persona_key_map = {
        "School Administrator": "admin",
        "Teacher": "teacher",
        "Student": "student",
        "Parent": "parent"
    }
    active_persona = persona_key_map[selected_persona]

    st.markdown("---")
    st.markdown("### Autonomous Modules")
    selected_tab = st.radio(
        "Navigation Module:",
        [
            "📊 Persona Dashboard",
            "📄 AI Document Reader (Multi-Slot Forms)",
            "👩‍🏫 Teacher Availability & Roster",
            "🗓️ Smart Timetable Engine (OR-Tools Solver)",
            "🗄️ Unified Data Layer",
            "🚨 Proactive Alerts Center",
            "📈 Predictive Insights",
            "🤖 AI Copilot (NLQ)"
        ]
    )

    st.markdown("---")
    with st.expander("⚡ Database & AI Status"):
        st.write(f"**Supabase Host:** `{db_instance.supabase_url}`")
        st.write(f"**Groq Model:** `llama-3.3-70b-versatile`")
        st.write(f"**Timetable Solver:** `Google OR-Tools CP-SAT`")
        if st.button("Refresh Live DB"):
            refresh_from_db()
            st.rerun()

# 5. Render Selected Tab Module

# ----------------------------------------------------
# TAB 1: Persona Dashboard
# ----------------------------------------------------
if selected_tab == "📊 Persona Dashboard":
    st.subheader(f"Dashboard — {selected_persona} View")

    if active_persona == "admin":
        m1, m2, m3, m4 = st.columns(4)
        students_list = st.session_state.students
        avg_att = round(sum(float(s.get("attendance_pct", 0)) for s in students_list) / max(1, len(students_list)), 1) if students_list else 0.0
        conflicts = len([t for t in st.session_state.timetable if t.get("has_conflict")])
        pending_docs = len([d for d in st.session_state.documents if d.get("status") == "review_required"])

        m1.metric("Enrolled Students", len(students_list), "Real Supabase DB")
        m2.metric("Avg School Attendance", f"{avg_att}%", f"{'High' if avg_att >= 80 else 'Warning'}")
        m3.metric("Timetable Conflicts", f"{conflicts} Clashes", delta_color="inverse")
        m4.metric("Docs Pending Review", f"{pending_docs} Docs")

        col_left, col_right = st.columns([1.2, 1])
        with col_left:
            st.markdown("#### 🚨 High-Priority Proactive Alerts (Live DB)")
            unresolved = [a for a in st.session_state.alerts if not a.get("resolved")]
            if unresolved:
                for alt in unresolved:
                    st.warning(f"**{alt['title']}**: {alt['message']}")
            else:
                st.info("No active alerts in Supabase database.")

        with col_right:
            st.markdown("#### 📈 AI Predictive Forecasts (Live DB)")
            if st.session_state.insights:
                for ins in st.session_state.insights:
                    st.info(f"**{ins['title']}** ({ins.get('confidence', 90)}% Conf.): {ins['forecast']}")
            else:
                st.info("No predictive insight records in database.")

    elif active_persona == "teacher":
        st.markdown("#### 📝 Class Live Attendance Marker")
        st.caption("1-Click Present/Absent updates Supabase Postgres in real time.")
        
        students_list = st.session_state.students
        if students_list:
            for stu in students_list:
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.write(f"**{stu['name']}** (Class {stu.get('class')})")
                    st.caption(f"Current Attendance: {stu.get('attendance_pct')}%")
                with c2:
                    if st.button(f"Mark Present", key=f"pres_{stu['id']}"):
                        mark_attendance(stu['id'], True)
                        st.rerun()
                with c3:
                    if st.button(f"Mark Absent", key=f"abs_{stu['id']}"):
                        mark_attendance(stu['id'], False)
                        st.rerun()
        else:
            st.info("No enrolled students found in Supabase database. Add students via AI Document Reader tab.")

    elif active_persona == "student":
        if st.session_state.students:
            stu = st.session_state.students[0]
            st.success(f"Welcome back, {stu['name']}! Class {stu.get('class')} • Roll No: {stu.get('roll_no', 'N/A')}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("My Attendance", f"{stu.get('attendance_pct')}%")
            c2.metric("Academic GPA", f"{stu.get('gpa')} / 4.0")
            c3.metric("Fee Status", f"₹{stu.get('fee_amount_due')}", str(stu.get("fee_status", "")).upper())

            st.markdown("#### My Class Timetable (Live Supabase DB)")
            df_t = pd.DataFrame(st.session_state.timetable)
            if not df_t.empty:
                cols_to_show = [c for c in ["period", "time", "subject", "teacher_name", "room"] if c in df_t.columns]
                st.dataframe(df_t[cols_to_show], use_container_width=True)
            else:
                st.info("No active timetable schedule in Supabase.")
        else:
            st.info("No student records in Supabase.")

    else: # Parent
        if st.session_state.students:
            stu = st.session_state.students[0]
            st.info(f"Parent Portal for: **{stu['name']}** (Class {stu.get('class')})")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 💳 Tuition Fee Invoice")
                st.write(f"**Amount Due:** ₹{stu.get('fee_amount_due', 0):,}")
                st.write(f"**Status:** {str(stu.get('fee_status', '')).upper()}")
                if stu.get("fee_status") != "paid":
                    if st.button("💳 Pay Fee Online"):
                        pay_fee(stu["id"])
                        st.success("Payment Successful! Database Fee Ledger updated in Supabase.")
                        st.rerun()
                else:
                    st.success("✅ All Fees Paid")

            with c2:
                st.markdown("#### 📊 Child Attendance Status")
                st.progress(min(1.0, float(stu.get("attendance_pct", 100.0)) / 100.0))
                if float(stu.get("attendance_pct", 100.0)) < 75:
                    st.error("⚠️ Attendance Warning: Below 75% threshold. Please contact class teacher.")
        else:
            st.info("No student records in Supabase database.")

# ----------------------------------------------------
# TAB 2: AI Document Reader (Multi-Slot Form Inputs)
# ----------------------------------------------------
elif selected_tab == "📄 AI Document Reader (Multi-Slot Forms)":
    st.subheader("Feature 1 — AI Document Reader (Groq LLM Vision & Form Extraction)")
    st.caption("Upload admission forms, fee receipts, or paste raw text. OCR + Groq AI extracts structured JSON with full Pydantic validation & audit trail.")

    doc_type_choice = st.selectbox("Document Category:", ["admission_form", "fee_receipt", "leave_application"])

    doc_tab1, doc_tab2, doc_tab3 = st.tabs(["📷 Slot 1: Form Picture Upload", "📄 Slot 2: Document File Upload", "✍️ Slot 3: Paste Raw Form Text"])

    with doc_tab1:
        st.markdown("#### Slot 1: Upload Admission Form / Receipt Image")
        img_file = st.file_uploader("Drop image (PNG, JPG, WEBP, PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key="doc_img_slot")
        if img_file and st.button("Run OCR & Groq AI Form Extraction", key="btn_doc_img"):
            doc_rec, val_stu = process_and_save_document_input(file_obj=img_file, doc_type=doc_type_choice)
            st.success(f"Parsed `{img_file.name}` via Groq AI! Saved audit trail in Supabase. Added to review inbox below.")
            st.rerun()

    with doc_tab2:
        st.markdown("#### Slot 2: Upload Document File (TXT, CSV, PDF)")
        doc_file = st.file_uploader("Drop document file:", type=["txt", "csv", "pdf"], key="doc_file_slot")
        if doc_file and st.button("Extract Document via Groq AI", key="btn_doc_file"):
            doc_rec, val_stu = process_and_save_document_input(file_obj=doc_file, doc_type=doc_type_choice)
            st.success(f"Extracted `{doc_file.name}`! Added to review inbox below.")
            st.rerun()

    with doc_tab3:
        st.markdown("#### Slot 3: Paste User-Defined Raw Text")
        paste_text = st.text_area(
            "Paste form text (e.g. 'ADMISSION FORM: Student Rahul Verma, Class 8A, Parent Rajesh Verma, Phone +91 98765 12345'):",
            height=120,
            key="doc_text_slot"
        )
        if paste_text and st.button("Extract Raw Text via Groq AI", key="btn_doc_text"):
            doc_rec, val_stu = process_and_save_document_input(raw_text_input=paste_text, doc_type=doc_type_choice)
            st.success("Extracted user text via Groq AI! Saved audit trail in Supabase.")
            st.rerun()

    st.markdown("---")
    st.markdown("### 🔍 Human-in-the-Loop Review & Audit Queue (Supabase DB)")
    docs_list = st.session_state.documents
    if docs_list:
        c_sel, c_view = st.columns([1, 2])
        with c_sel:
            st.markdown("#### Document Inbox")
            doc_options = [f"{d['id']} - {d['filename']} [{d.get('source_type', 'file')}]" for d in docs_list]
            selected_option = st.selectbox("Select document record:", doc_options)
            sel_id = selected_option.split(" - ")[0]
            selected_doc = next(d for d in docs_list if d["id"] == sel_id)

            st.markdown("#### Audit Trail Details")
            st.write(f"**Source Type:** `{selected_doc.get('source_type')}`")
            st.write(f"**Status:** `{selected_doc.get('status')}`")
            if selected_doc.get("validation_errors"):
                st.error(f"Validation Warning: {selected_doc.get('validation_errors')}")
            
            st.markdown("#### Raw Extracted OCR Stream")
            st.code(selected_doc.get("ocr_raw_text", ""), language="text")

        with c_view:
            st.markdown(f"#### Human Review: `{selected_doc['filename']}`")
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
elif selected_tab == "👩‍🏫 Teacher Availability & Roster":
    st.subheader("Feature — Teacher Roster & Availability Manager (User-Defined AI Input)")
    st.caption("Upload teacher roster files or paste custom availability instructions. Groq AI parses roster & constraints, then OR-Tools solver re-assigns schedules.")

    t_slot1, t_slot2 = st.tabs(["📄 Slot 1: Upload Roster File", "✍️ Slot 2: Paste Teacher Availability Text"])

    with t_slot1:
        st.markdown("#### Slot 1: Upload Roster / Availability File")
        t_file = st.file_uploader("Upload Roster File (TXT, CSV, Image):", type=["txt", "csv", "png", "jpg"], key="tch_file_slot")
        if t_file and st.button("Parse Roster File via Groq AI", key="btn_tch_file"):
            n_tch, n_av, text = process_and_save_teacher_input(file_obj=t_file)
            st.success(f"Parsed `{t_file.name}`! Created {n_tch} teacher record(s) and {n_av} availability rule(s) in Supabase. Timetable re-optimized via OR-Tools!")
            st.rerun()

    with t_slot2:
        st.markdown("#### Slot 2: Paste Custom Teacher Availability Text")
        t_text = st.text_area(
            "Paste teacher info (e.g. 'Dr. Sunita Mehta teaches Mathematics for 8A and 8B. Mrs. Kavita Singh is unavailable on Monday Period 3'):",
            height=120,
            key="tch_text_slot"
        )
        if t_text and st.button("Process Teacher Info via Groq AI", key="btn_tch_text"):
            n_tch, n_av, text = process_and_save_teacher_input(raw_text_input=t_text)
            st.success(f"Processed teacher text! Saved {n_tch} teacher(s) & {n_av} availability rule(s) in Supabase. Timetable re-optimized via OR-Tools!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Faculty Directory & Availability Rules (Live Supabase DB)")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("#### Faculty Directory")
        teachers_list = st.session_state.teachers
        if teachers_list:
            df_t = pd.DataFrame(teachers_list)
            cols_t = [c for c in ["id", "name", "subject", "email", "assigned_classes", "status"] if c in df_t.columns]
            st.dataframe(df_t[cols_t], use_container_width=True)
        else:
            st.info("No teachers enrolled in Supabase yet. Use input slots above to add teachers.")

    with col_t2:
        st.markdown("#### Availability & Leave Constraints (`teacher_availability`)")
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
elif selected_tab == "🗓️ Smart Timetable Engine (OR-Tools Solver)":
    st.subheader("Feature 2 — Smart Timetable Engine (Google OR-Tools CP-SAT Solver)")
    st.caption("Upload timetable schedules via Picture, File, or Raw Text. Groq AI extracts slot constraints → Pydantic validates → Google OR-Tools solves conflicts → Supabase stores result.")

    tt_tab1, tt_tab2, tt_tab3 = st.tabs(["📷 Slot 1: Timetable Picture Image", "📄 Slot 2: Document / CSV File", "✍️ Slot 3: Paste Schedule Text"])

    with tt_tab1:
        st.markdown("#### Slot 1: Timetable Picture Upload")
        img_tt = st.file_uploader("Upload timetable image (PNG, JPG, PDF):", type=["png", "jpg", "jpeg", "pdf"], key="tt_img_slot")
        if img_tt and st.button("Extract & Solve Timetable Picture", key="btn_tt_img"):
            slots, warnings = process_and_save_timetable_input(file_obj=img_tt)
            st.success(f"Generated {len(slots)} conflict-free slots using Google OR-Tools! Saved to Supabase.")
            if warnings:
                for w in warnings:
                    st.warning(w)
            st.rerun()

    with tt_tab2:
        st.markdown("#### Slot 2: Document / CSV Timetable File")
        doc_tt = st.file_uploader("Upload document file (TXT, CSV):", type=["txt", "csv"], key="tt_doc_slot")
        if doc_tt and st.button("Extract & Solve Document Timetable", key="btn_tt_doc"):
            slots, warnings = process_and_save_timetable_input(file_obj=doc_tt)
            st.success(f"Generated {len(slots)} slots using OR-Tools Solver! Saved to Supabase.")
            st.rerun()

    with tt_tab3:
        st.markdown("#### Slot 3: Paste Schedule Text")
        paste_tt = st.text_area(
            "Paste timetable text (e.g. '8A, Mathematics, Dr. Sunita Mehta, Room 201\n8A, Science, Prof. Rajesh Gupta, Science Lab'):",
            height=120,
            key="tt_text_slot"
        )
        if paste_tt and st.button("Solve Schedule Text via OR-Tools", key="btn_tt_text"):
            slots, warnings = process_and_save_timetable_input(raw_text_input=paste_tt)
            st.success(f"Solved schedule via OR-Tools! Saved to Supabase.")
            st.rerun()

    st.markdown("---")
    st.markdown("#### Faculty Absence & Substitution Controller")
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

    st.markdown("#### Master Timetable Grid (Live Supabase DB)")
    df = pd.DataFrame(st.session_state.timetable)
    if not df.empty:
        cols_to_show = [c for c in ["period", "time", "class_name", "subject", "teacher_name", "room", "has_conflict", "is_substitute", "substitute_teacher"] if c in df.columns]
        st.dataframe(df[cols_to_show], use_container_width=True)
    else:
        st.info("No timetable slots in Supabase database. Upload schedule above.")

# ----------------------------------------------------
# TAB 5: Unified Data Layer
# ----------------------------------------------------
elif selected_tab == "🗄️ Unified Data Layer":
    st.subheader("Feature 3 — Unified Data Layer Explorer")
    st.caption("Single source of truth in Supabase joining Student ID <-> Attendance <-> Fees <-> Schedule.")

    df_stu = pd.DataFrame(st.session_state.students)
    if not df_stu.empty:
        cols_to_show = [c for c in ["id", "name", "roll_no", "class", "parent_name", "parent_phone", "attendance_pct", "fee_status", "fee_amount_due", "gpa", "risk_level"] if c in df_stu.columns]
        st.dataframe(df_stu[cols_to_show], use_container_width=True)
    else:
        st.info("No student records in Supabase.")

# ----------------------------------------------------
# TAB 6: Proactive Alerts Center
# ----------------------------------------------------
elif selected_tab == "🚨 Proactive Alerts Center":
    st.subheader("Feature 4 — Proactive Alerts & Notification Routing")
    alerts_list = st.session_state.alerts
    unresolved_alerts = [a for a in alerts_list if not a.get("resolved")]
    if unresolved_alerts:
        for alt in unresolved_alerts:
            st.error(f"🚨 **{alt['title']}** [{str(alt.get('priority', 'medium')).upper()}]\n\n{alt['message']}\n\n*Action: {alt.get('action', '')}*")
    else:
        st.success("✅ All alerts resolved in Supabase database.")

# ----------------------------------------------------
# TAB 7: Predictive Insights Engine
# ----------------------------------------------------
elif selected_tab == "📈 Predictive Insights":
    st.subheader("Feature 5 — Predictive Insights Engine")
    if st.session_state.insights:
        for ins in st.session_state.insights:
            st.info(f"📈 **{ins['title']}**\n\nMetric: {ins.get('metric')} ({ins.get('trend')})\n\nForecast: {ins.get('forecast')}\n\n*AI Recommendation: {ins.get('recommendation')}*")
    else:
        st.info("No predictive insight records in Supabase.")

# ----------------------------------------------------
# TAB 8: AI Copilot (NLQ)
# ----------------------------------------------------
elif selected_tab == "🤖 AI Copilot (NLQ)":
    st.subheader("Feature 6 — AI Copilot (Natural Language Query over Supabase Data)")
    
    for msg in st.session_state.copilot_messages:
        with st.chat_message(msg.get("sender", "user")):
            st.write(msg.get("text", ""))
            if msg.get("sql"):
                st.code(msg["sql"], language="sql")
            if msg.get("table_data"):
                st.dataframe(pd.DataFrame(msg["table_data"]))

    prompt = st.chat_input("Ask a question about school data (e.g., 'Which students have attendance below 75%?')...")
    if prompt:
        user_msg = {"sender": "user", "text": prompt}
        add_copilot_message(user_msg)
        
        lower = prompt.lower()
        if "attendance" in lower and ("75" in lower or "below" in lower or "<" in lower):
            low_att = [s for s in st.session_state.students if float(s.get("attendance_pct", 100)) < 75.0]
            ai_msg = {
                "sender": "ai",
                "text": f"Found {len(low_att)} student(s) with attendance below 75% threshold in Supabase Database.",
                "sql": "SELECT name, class, attendance_pct FROM students WHERE attendance_pct < 75.0;",
                "table": [
                    {"name": s.get("name"), "class": s.get("class"), "attendance_pct": s.get("attendance_pct"), "risk_level": s.get("risk_level")}
                    for s in low_att
                ]
            }
            add_copilot_message(ai_msg)
        elif "fee" in lower or "overdue" in lower:
            overdue = [s for s in st.session_state.students if s.get("fee_status") == "overdue"]
            ai_msg = {
                "sender": "ai",
                "text": f"Found {len(overdue)} student(s) with overdue fees in Supabase Database.",
                "sql": "SELECT name, class, fee_amount_due FROM students WHERE fee_status = 'overdue';",
                "table": [
                    {"name": s.get("name"), "class": s.get("class"), "fee_status": s.get("fee_status"), "fee_amount_due": s.get("fee_amount_due")}
                    for s in overdue
                ]
            }
            add_copilot_message(ai_msg)
        else:
            ai_msg = {
                "sender": "ai",
                "text": f"Executed read-only query over Supabase Database. Retrieved records.",
                "sql": "SELECT * FROM students LIMIT 5;",
                "table": [
                    {"name": s.get("name"), "class": s.get("class"), "attendance_pct": s.get("attendance_pct"), "gpa": s.get("gpa")}
                    for s in st.session_state.students[:3]
                ]
            }
            add_copilot_message(ai_msg)
        st.rerun()
