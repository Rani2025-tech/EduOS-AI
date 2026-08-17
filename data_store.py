import streamlit as st
import datetime
from typing import Any, Optional, Dict
import logging

Tuple_Result = Any
from db_client import db_instance
from doc_parser import parse_document_input
from teacher_parser import parse_teacher_input
from timetable_parser import parse_and_solve_timetable
from analytics_engine import generate_all_insights
from staffing_engine import calculate_staffing_report
from auth import verify_password, issue_token, verify_token, TokenError, AuthError, is_auth_configured

logger = logging.getLogger("EduOS_DataStore")
logger.setLevel(logging.INFO)


# ── Authentication helpers ────────────────────────────────────────────────────

def init_auth_session():
    """Initialises auth-related session state keys. Called once at app startup."""
    if "auth" not in st.session_state:
        st.session_state.auth = None          # None = not logged in
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "auth_error" not in st.session_state:
        st.session_state.auth_error = ""


def login_user(username: str, password: str) -> bool:
    """
    Authenticates a user against the users table.
    On success: stores auth payload and JWT in session state, returns True.
    On failure: stores error message in session state, returns False.
    Never logs or exposes the plaintext password.
    """
    st.session_state.auth_error = ""

    if not is_auth_configured():
        st.session_state.auth_error = (
            "Authentication is not configured. Set JWT_SECRET_KEY in your .env file."
        )
        return False

    if not username or not password:
        st.session_state.auth_error = "Username and password are required."
        return False

    user = db_instance.get_user_by_username(username.strip())
    if not user:
        st.session_state.auth_error = "Invalid username or password."
        return False

    if not verify_password(password, user["password_hash"]):
        st.session_state.auth_error = "Invalid username or password."
        return False

    token = issue_token(
        user_id=user["id"],
        role=user["role"],
        linked_id=user.get("linked_id"),
    )
    st.session_state.auth_token = token
    st.session_state.auth = {
        "user_id":   user["id"],
        "username":  user["username"],
        "role":      user["role"],
        "linked_id": user.get("linked_id"),
    }
    logger.info(f"User logged in: {user['username']} (role={user['role']})")
    return True


def logout_user():
    """Clears auth session state and all cached school data."""
    for key in ["auth", "auth_token", "auth_error",
                "students", "teachers", "teacher_availability",
                "timetable", "documents", "alerts", "insights",
                "copilot_messages", "staffing_report", "db_connected"]:
        st.session_state.pop(key, None)


def get_current_auth() -> Optional[Dict]:
    """Returns the current auth payload or None if not logged in."""
    return st.session_state.get("auth")


def is_authenticated() -> bool:
    """Returns True if a valid auth session exists."""
    auth = st.session_state.get("auth")
    token = st.session_state.get("auth_token")
    if not auth or not token:
        return False
    try:
        verify_token(token)
        return True
    except TokenError:
        logout_user()
        return False


def init_session_state():
    """Initializes session state directly from real Supabase DB. No hardcoded dummy data."""
    if "db_connected" not in st.session_state:
        st.session_state.db_connected = db_instance.is_supabase_active

    if "students" not in st.session_state:
        st.session_state.students = db_instance.get_students()
        
    if "teachers" not in st.session_state:
        st.session_state.teachers = db_instance.get_teachers()

    if "teacher_availability" not in st.session_state:
        st.session_state.teacher_availability = db_instance.get_teacher_availability()

    if "timetable" not in st.session_state:
        st.session_state.timetable = db_instance.get_timetable()
        
    if "documents" not in st.session_state:
        st.session_state.documents = db_instance.get_documents()

    if "alerts" not in st.session_state:
        st.session_state.alerts = db_instance.get_alerts()

    if "insights" not in st.session_state:
        # Prefer live DB insights; fall back to calculated insights when DB is unavailable
        db_insights = db_instance.get_insights()
        if db_insights:
            st.session_state.insights = db_insights
        else:
            st.session_state.insights = generate_all_insights(
                students=st.session_state.get("students", []),
                teachers=st.session_state.get("teachers", []),
                teacher_availability=st.session_state.get("teacher_availability", []),
                timetable=st.session_state.get("timetable", []),
                documents=st.session_state.get("documents", []),
            )

    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = db_instance.get_copilot_messages()

    if "staffing_report" not in st.session_state:
        st.session_state.staffing_report = calculate_staffing_report(
            teachers=st.session_state.get("teachers", []),
            teacher_availability=st.session_state.get("teacher_availability", []),
            timetable=st.session_state.get("timetable", []),
        )

def refresh_from_db():
    """Refetches real live records from Supabase database."""
    st.session_state.students = db_instance.get_students()
    st.session_state.teachers = db_instance.get_teachers()
    st.session_state.teacher_availability = db_instance.get_teacher_availability()
    st.session_state.timetable = db_instance.get_timetable()
    st.session_state.documents = db_instance.get_documents()
    st.session_state.alerts = db_instance.get_alerts()
    db_insights = db_instance.get_insights()
    st.session_state.insights = db_insights if db_insights else generate_all_insights(
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
    st.session_state.copilot_messages = db_instance.get_copilot_messages()

def process_and_save_teacher_input(file_obj=None, raw_text_input: str = "") -> Tuple_Result:
    """
    Processes user-defined teacher roster/availability input (file or text paste)
    via OCR -> Groq AI -> Pydantic -> Supabase -> OR-Tools CP-SAT solver re-optimization.
    """
    teachers, availabilities, raw_text = parse_teacher_input(
        file_obj=file_obj,
        raw_text_input=raw_text_input
    )

    saved_teachers_count = 0
    saved_avails_count = 0

    for t in teachers:
        db_instance.upsert_teacher(t)
        saved_teachers_count += 1

    for av in availabilities:
        db_instance.upsert_teacher_availability(av)
        saved_avails_count += 1

    # Re-fetch latest teachers and availability from Supabase
    refresh_from_db()

    # Automatically trigger OR-Tools solver to re-optimize timetable with updated teacher availability
    if st.session_state.timetable:
        optimized_slots, solver_warnings = parse_and_solve_timetable(
            raw_text_input="Re-solve existing schedule",
            teachers_list=st.session_state.teachers,
            teacher_availabilities=st.session_state.teacher_availability
        )
        if optimized_slots:
            db_instance.replace_timetable(optimized_slots)
            refresh_from_db()

    return saved_teachers_count, saved_avails_count, raw_text

def process_and_save_document_input(file_obj=None, raw_text_input: str = "", doc_type: str = "admission_form"):
    """
    Processes user document input (Image / File / Raw Text) via Groq AI,
    validates with Pydantic, and saves audit trail document into Supabase.
    """
    doc_record, validated_student = parse_document_input(
        file_obj=file_obj,
        raw_text_input=raw_text_input,
        doc_type=doc_type
    )

    if doc_record:
        # Save audit record in Supabase
        db_instance.insert_document(doc_record)
        refresh_from_db()

    return doc_record, validated_student

def process_and_save_timetable_input(file_obj=None, raw_text_input: str = ""):
    """
    Processes timetable input via OCR -> Groq AI -> Pydantic -> OR-Tools CP-SAT Solver -> Supabase.
    """
    optimized_slots, warnings = parse_and_solve_timetable(
        file_obj=file_obj,
        raw_text_input=raw_text_input,
        teachers_list=st.session_state.teachers,
        teacher_availabilities=st.session_state.teacher_availability
    )

    if optimized_slots:
        db_instance.replace_timetable(optimized_slots)
        refresh_from_db()

    return optimized_slots, warnings

def toggle_teacher(teacher_id: str):
    target_teacher = None
    for t in st.session_state.teachers:
        if t["id"] == teacher_id:
            t["status"] = "absent" if t.get("status") == "active" else "active"
            target_teacher = t
            break

    if target_teacher:
        db_instance.upsert_teacher(target_teacher)
        
        # Save availability record for absent teacher
        if target_teacher["status"] == "absent":
            db_instance.upsert_teacher_availability({
                "teacher_id": target_teacher["id"],
                "teacher_name": target_teacher["name"],
                "status": "unavailable",
                "notes": f"Teacher marked absent on {datetime.datetime.now().strftime('%Y-%m-%d')}"
            })

        refresh_from_db()

        # Run Google OR-Tools Solver to reassign free substitutes for affected slots
        if st.session_state.timetable:
            optimized_slots, warnings = solve_timetable_reassignment()

def solve_timetable_reassignment():
    """Runs OR-Tools CP-SAT solver over current schedule to reassign substitutes for absent teachers."""
    optimized_slots, warnings = parse_and_solve_timetable(
        raw_text_input="Reassign timetable",
        teachers_list=st.session_state.teachers,
        teacher_availabilities=st.session_state.teacher_availability
    )
    if optimized_slots:
        db_instance.replace_timetable(optimized_slots)
        refresh_from_db()

    # Resolve timetable alerts
    for alt in st.session_state.alerts:
        if alt.get("type") == "timetable" and not alt.get("resolved"):
            db_instance.resolve_alert(alt["id"])

    return optimized_slots, warnings

def mark_attendance(student_id: str, is_present: bool):
    for s in st.session_state.students:
        if s["id"] == student_id:
            old_pct = float(s.get("attendance_pct", 100.0))
            new_pct = min(100.0, old_pct + 2.0) if is_present else max(50.0, old_pct - 5.0)
            s["attendance_pct"] = new_pct
            s["risk_level"] = "high" if new_pct < 75.0 else "low"

            db_instance.upsert_student(s)

            if new_pct < 75.0 and old_pct >= 75.0:
                new_alert = {
                    "id": f"ALT-{int(datetime.datetime.now().timestamp())}",
                    "type": "attendance",
                    "priority": "high",
                    "title": f"Low Attendance Warning: {s['name']}",
                    "message": f"{s['name']} attendance dropped to {new_pct}%. Below 75% threshold.",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "resolved": False,
                    "student_id": s["id"],
                    "action": "Send Warning Notice to Parent"
                }
                db_instance.insert_alert(new_alert)
            break

    refresh_from_db()

def pay_fee(student_id: str):
    for s in st.session_state.students:
        if s["id"] == student_id:
            s["fee_status"] = "paid"
            s["fee_amount_due"] = 0
            db_instance.upsert_student(s)
            break

    for alt in st.session_state.alerts:
        if alt.get("student_id") == student_id and alt.get("type") == "fee":
            db_instance.resolve_alert(alt["id"])

    refresh_from_db()

def commit_doc(doc_id: str, updated_fields: dict):
    """Commits reviewed document data and inserts student record into Supabase."""
    db_instance.update_document(doc_id, {
        "status": "committed",
        "fields": updated_fields
    })

    name = updated_fields.get("student_name", "User Enrolled Student")
    cls = updated_fields.get("class", "8A")
    parent = updated_fields.get("parent_name", "Parent")

    stu_count = len(st.session_state.students) + 1
    new_student = {
        "id": f"STU-{100 + stu_count}",
        "name": name,
        "roll_no": f"{cls}-0{stu_count}",
        "class": cls,
        "parent_name": parent,
        "parent_phone": updated_fields.get("parent_phone", "+91 98765 12345"),
        "parent_email": updated_fields.get("parent_email", f"{name.lower().replace(' ', '.')}@example.com"),
        "attendance_pct": 100.0,
        "fee_status": updated_fields.get("fee_status", "pending"),
        "fee_amount_due": int(updated_fields.get("fee_amount_due", 15000)) if str(updated_fields.get("fee_amount_due", "")).isdigit() else 15000,
        "gpa": 3.8,
        "risk_level": "low",
        "assigned_room": updated_fields.get("assigned_room", "Room 201")
    }

    db_instance.upsert_student(new_student)
    refresh_from_db()

def add_copilot_message(msg: dict):
    msg_to_save = {
        "id": f"MSG-{int(datetime.datetime.now().timestamp() * 1000)}",
        "sender": msg.get("sender", "user"),
        "text": msg.get("text", ""),
        "sql": msg.get("sql"),
        "table_data": msg.get("table")
    }
    db_instance.insert_copilot_message(msg_to_save)
    refresh_from_db()

