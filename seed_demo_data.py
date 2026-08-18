"""
EduOS AI — Demo Data Seed Script
==================================
Pre-populates realistic school data so judges/reviewers can immediately
see all features working without entering any data manually.

Usage (from project root):
    python seed_demo_data.py

What gets seeded (idempotent — safe to re-run):
    - 9 students  (mix of attendance, fee status, GPA, risk levels)
    - 5 teachers  (mix of present/absent, subjects)
    - 6 teacher availability rules (leave constraints)
    - 14 timetable slots (2 with conflicts pre-set)
    - 3 alerts (attendance, fee, staffing)
    - 3 documents (2 review_required, 1 committed)

Linked accounts (from seed_dev_users.py):
    dev_student → DEV-STU-001  (updated to realistic values)
    dev_parent  → DEV-STU-001  (same student)
    dev_teacher → DEV-TCH-001  (updated to realistic values)
"""

from __future__ import annotations
import sys
from dotenv import load_dotenv
load_dotenv()

from db_client import db_instance, DB_STATUS_CONNECTED, DB_STATUS_CONN_FAILED, DB_STATUS_MISSING_CONFIG

def _fail(msg: str) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(1)

def _check() -> None:
    if db_instance.connection_status == DB_STATUS_MISSING_CONFIG:
        _fail("Supabase not configured. Copy .env.example to .env and fill in credentials.")
    if db_instance.connection_status == DB_STATUS_CONN_FAILED:
        _fail("Supabase connection failed. Check SUPABASE_URL and SUPABASE_KEY.")

# ── 1. STUDENTS ───────────────────────────────────────────────────────────────
STUDENTS = [
    # dev_student / dev_parent linked account — updated to realistic values
    {
        "id": "DEV-STU-001",
        "name": "Arjun Sharma",
        "roll_no": "8A-001",
        "class": "8A",
        "parent_name": "Rajesh Sharma",
        "parent_phone": "+91 98765 43210",
        "parent_email": "rajesh.sharma@gmail.com",
        "attendance_pct": 72.0,   # below 75% — triggers alert
        "fee_status": "overdue",
        "fee_amount_due": 12000,
        "gpa": 2.8,
        "risk_level": "high",
        "assigned_room": "Room 201",
    },
    {
        "id": "DEMO-STU-002",
        "name": "Priya Patel",
        "roll_no": "8A-002",
        "class": "8A",
        "parent_name": "Suresh Patel",
        "parent_phone": "+91 91234 56789",
        "parent_email": "suresh.patel@gmail.com",
        "attendance_pct": 91.5,
        "fee_status": "paid",
        "fee_amount_due": 0,
        "gpa": 3.8,
        "risk_level": "low",
        "assigned_room": "Room 201",
    },
    {
        "id": "DEMO-STU-003",
        "name": "Rohan Mehta",
        "roll_no": "8B-001",
        "class": "8B",
        "parent_name": "Vikram Mehta",
        "parent_phone": "+91 99887 76655",
        "parent_email": "vikram.mehta@gmail.com",
        "attendance_pct": 68.0,   # below 75% — triggers alert
        "fee_status": "pending",
        "fee_amount_due": 8500,
        "gpa": 2.4,
        "risk_level": "high",
        "assigned_room": "Room 202",
    },
    {
        "id": "DEMO-STU-004",
        "name": "Sneha Iyer",
        "roll_no": "8B-002",
        "class": "8B",
        "parent_name": "Ramesh Iyer",
        "parent_phone": "+91 88776 65544",
        "parent_email": "ramesh.iyer@gmail.com",
        "attendance_pct": 85.0,
        "fee_status": "paid",
        "fee_amount_due": 0,
        "gpa": 3.5,
        "risk_level": "low",
        "assigned_room": "Room 202",
    },
    {
        "id": "DEMO-STU-005",
        "name": "Karan Singh",
        "roll_no": "9A-001",
        "class": "9A",
        "parent_name": "Gurpreet Singh",
        "parent_phone": "+91 77665 54433",
        "parent_email": "gurpreet.singh@gmail.com",
        "attendance_pct": 78.5,
        "fee_status": "pending",
        "fee_amount_due": 4000,
        "gpa": 3.1,
        "risk_level": "medium",
        "assigned_room": "Room 301",
    },
    {
        "id": "DEMO-STU-006",
        "name": "Ananya Reddy",
        "roll_no": "9A-002",
        "class": "9A",
        "parent_name": "Venkat Reddy",
        "parent_phone": "+91 66554 43322",
        "parent_email": "venkat.reddy@gmail.com",
        "attendance_pct": 95.0,
        "fee_status": "paid",
        "fee_amount_due": 0,
        "gpa": 3.9,
        "risk_level": "low",
        "assigned_room": "Room 301",
    },
    {
        "id": "DEMO-STU-007",
        "name": "Dev Kapoor",
        "roll_no": "9B-001",
        "class": "9B",
        "parent_name": "Anil Kapoor",
        "parent_phone": "+91 55443 32211",
        "parent_email": "anil.kapoor@gmail.com",
        "attendance_pct": 60.0,   # critically low
        "fee_status": "overdue",
        "fee_amount_due": 18000,
        "gpa": 2.1,
        "risk_level": "critical",
        "assigned_room": "Room 302",
    },
    {
        "id": "DEMO-STU-008",
        "name": "Meera Nair",
        "roll_no": "9B-002",
        "class": "9B",
        "parent_name": "Sunil Nair",
        "parent_phone": "+91 44332 21100",
        "parent_email": "sunil.nair@gmail.com",
        "attendance_pct": 88.0,
        "fee_status": "paid",
        "fee_amount_due": 0,
        "gpa": 3.6,
        "risk_level": "low",
        "assigned_room": "Room 302",
    },
    {
        "id": "DEMO-STU-009",
        "name": "Rahul Verma",
        "roll_no": "10A-001",
        "class": "10A",
        "parent_name": "Manoj Verma",
        "parent_phone": "+91 33221 10099",
        "parent_email": "manoj.verma@gmail.com",
        "attendance_pct": 82.0,
        "fee_status": "pending",
        "fee_amount_due": 6000,
        "gpa": 3.3,
        "risk_level": "low",
        "assigned_room": "Room 401",
    },
]

# ── 2. TEACHERS ───────────────────────────────────────────────────────────────
TEACHERS = [
    # dev_teacher linked account
    {
        "id": "DEV-TCH-001",
        "name": "Dr. Sunita Mehta",
        "subject": "Mathematics",
        "email": "sunita.mehta@eduos.school",
        "assigned_classes": "8A,8B,9A",
        "status": "active",
    },
    {
        "id": "DEMO-TCH-002",
        "name": "Prof. Rajesh Gupta",
        "subject": "Science",
        "email": "rajesh.gupta@eduos.school",
        "assigned_classes": "8A,8B",
        "status": "absent",   # absent — triggers substitution engine
    },
    {
        "id": "DEMO-TCH-003",
        "name": "Mrs. Kavita Singh",
        "subject": "English",
        "email": "kavita.singh@eduos.school",
        "assigned_classes": "9A,9B,10A",
        "status": "active",
    },
    {
        "id": "DEMO-TCH-004",
        "name": "Mr. Arun Kumar",
        "subject": "Social Studies",
        "email": "arun.kumar@eduos.school",
        "assigned_classes": "9B,10A",
        "status": "active",
    },
    {
        "id": "DEMO-TCH-005",
        "name": "Ms. Deepa Nair",
        "subject": "Computer Science",
        "email": "deepa.nair@eduos.school",
        "assigned_classes": "8A,9A,10A",
        "status": "absent",   # absent — triggers staffing pressure score
    },
]

# ── 3. TEACHER AVAILABILITY ───────────────────────────────────────────────────
AVAILABILITY = [
    {
        "id": "DEMO-AV-001",
        "teacher_id": "DEMO-TCH-002",
        "teacher_name": "Prof. Rajesh Gupta",
        "day_of_week": "Monday",
        "period": None,
        "status": "unavailable",
        "notes": "Medical leave — full day",
    },
    {
        "id": "DEMO-AV-002",
        "teacher_id": "DEMO-TCH-005",
        "teacher_name": "Ms. Deepa Nair",
        "day_of_week": "Monday",
        "period": None,
        "status": "unavailable",
        "notes": "Personal leave approved",
    },
    {
        "id": "DEMO-AV-003",
        "teacher_id": "DEV-TCH-001",
        "teacher_name": "Dr. Sunita Mehta",
        "day_of_week": "Wednesday",
        "period": 5,
        "status": "unavailable",
        "notes": "Department meeting Period 5",
    },
    {
        "id": "DEMO-AV-004",
        "teacher_id": "DEMO-TCH-003",
        "teacher_name": "Mrs. Kavita Singh",
        "day_of_week": "Friday",
        "period": 1,
        "status": "preferred",
        "notes": "Prefers morning slots on Fridays",
    },
    {
        "id": "DEMO-AV-005",
        "teacher_id": "DEMO-TCH-004",
        "teacher_name": "Mr. Arun Kumar",
        "day_of_week": "Thursday",
        "period": 3,
        "status": "unavailable",
        "notes": "External training session",
    },
    {
        "id": "DEMO-AV-006",
        "teacher_id": "DEMO-TCH-002",
        "teacher_name": "Prof. Rajesh Gupta",
        "day_of_week": "Tuesday",
        "period": 4,
        "status": "unavailable",
        "notes": "Lab maintenance period",
    },
]

# ── 4. TIMETABLE ──────────────────────────────────────────────────────────────
TIMETABLE = [
    # 8A slots
    {"id": "TT-001", "period": 1, "time": "08:00 - 08:45", "class_name": "8A", "subject": "Mathematics",      "teacher_id": "DEV-TCH-001",  "teacher_name": "Dr. Sunita Mehta",   "room": "Room 201", "has_conflict": False, "is_substitute": False, "substitute_teacher": None},
    {"id": "TT-002", "period": 2, "time": "08:45 - 09:30", "class_name": "8A", "subject": "Science",          "teacher_id": "DEMO-TCH-002", "teacher_name": "Prof. Rajesh Gupta", "room": "Science Lab", "has_conflict": True,  "is_substitute": False, "substitute_teacher": None, "conflict_reason": "Teacher absent"},
    {"id": "TT-003", "period": 3, "time": "09:45 - 10:30", "class_name": "8A", "subject": "English",          "teacher_id": "DEMO-TCH-003", "teacher_name": "Mrs. Kavita Singh",  "room": "Room 201", "has_conflict": False, "is_substitute": False, "substitute_teacher": None},
    {"id": "TT-004", "period": 4, "time": "10:30 - 11:15", "class_name": "8A", "subject": "Computer Science", "teacher_id": "DEMO-TCH-005", "teacher_name": "Ms. Deepa Nair",    "room": "Computer Lab", "has_conflict": True,  "is_substitute": False, "substitute_teacher": None, "conflict_reason": "Teacher absent"},
    # 8B slots
    {"id": "TT-005", "period": 1, "time": "08:00 - 08:45", "class_name": "8B", "subject": "English",          "teacher_id": "DEMO-TCH-003", "teacher_name": "Mrs. Kavita Singh",  "room": "Room 202", "has_conflict": False, "is_substitute": False, "substitute_teacher": None},
    {"id": "TT-006", "period": 2, "time": "08:45 - 09:30", "class_name": "8B", "subject": "Mathematics",      "teacher_id": "DEV-TCH-001",  "teacher_name": "Dr. Sunita Mehta",   "room": "Room 202", "has_conflict": False, "is_substitute": False, "substitute_teacher": None},
    {"id": "TT-007", "period": 3, "time": "09:45 - 10:30", "class_name": "8B", "subject": "Science",          "teacher_id": "DEMO-TCH-002", "teacher_name": "Prof. Rajesh Gupta", "room": "Science Lab", "has_conflict": False, "is_substitute": True,  "substitute_teacher": "Mr. Arun Kumar"},
    # 9A slots
    {"id": "TT-008", "period": 1, "time": "08:00 - 08:45", "class_name": "9A", "subject": "Mathematics",      "teacher_id": "DEV-TCH-001",  "teacher_name": "Dr. Sunita Mehta",   "room": "Room 301", "has_conflict": False, "is_substitute": False, "substitute_teacher": None},
    {"id": "TT-009", "period": 2, "time": "08:45 - 09:30", "class_name": "9A", "subject": "English",          "teacher_id": "DEMO-TCH-003", "teacher_name": "Mrs. Kavita Singh",  "room": "Room 301", "has_conflict": False, "is_substitute": False, "substitute_teacher": None},
    {"id": "TT-010", "period": 3, "time": "09:45 - 10:30", "class_name": "9A", "subject": "Computer Science", "teacher_id": "DEMO-TCH-005", "teacher_name": "Ms. Deepa Nair",    "room": "Computer Lab", "has_conflict": False, "is_substitute": True,  "substitute_teacher": "Mrs. Kavita Singh"},
    # 9B slots
    {"id": "TT-011", "period": 1, "time": "08:00 - 08:45", "class_name": "9B", "subject": "Social Studies",   "teacher_id": "DEMO-TCH-004", "teacher_name": "Mr. Arun Kumar",    "room": "Room 302", "has_conflict": False, "is_substitute": False, "substitute_teacher": None},
    {"id": "TT-012", "period": 2, "time": "08:45 - 09:30", "class_name": "9B", "subject": "English",          "teacher_id": "DEMO-TCH-003", "teacher_name": "Mrs. Kavita Singh",  "room": "Room 302", "has_conflict": False, "is_substitute": False, "substitute_teacher": None},
    # 10A slots
    {"id": "TT-013", "period": 1, "time": "08:00 - 08:45", "class_name": "10A", "subject": "Computer Science","teacher_id": "DEMO-TCH-005", "teacher_name": "Ms. Deepa Nair",    "room": "Computer Lab", "has_conflict": False, "is_substitute": True,  "substitute_teacher": "Mr. Arun Kumar"},
    {"id": "TT-014", "period": 2, "time": "08:45 - 09:30", "class_name": "10A", "subject": "Social Studies",  "teacher_id": "DEMO-TCH-004", "teacher_name": "Mr. Arun Kumar",    "room": "Room 401", "has_conflict": False, "is_substitute": False, "substitute_teacher": None},
]

# ── 5. ALERTS ─────────────────────────────────────────────────────────────────
ALERTS = [
    {
        "id": "DEMO-ALT-001",
        "type": "attendance",
        "priority": "high",
        "title": "Low Attendance — Arjun Sharma (8A)",
        "message": "Arjun Sharma's attendance has dropped to 72.0%, below the 75% mandatory threshold. Immediate intervention required.",
        "resolved": False,
        "student_id": "DEV-STU-001",
        "action": "Contact parent Rajesh Sharma (+91 98765 43210) and schedule a counselling session.",
    },
    {
        "id": "DEMO-ALT-002",
        "type": "fee",
        "priority": "high",
        "title": "Fee Overdue — Dev Kapoor (9B)",
        "message": "Dev Kapoor has an outstanding fee of ₹18,000 marked as overdue. Payment is 30+ days past due.",
        "resolved": False,
        "student_id": "DEMO-STU-007",
        "action": "Send formal fee reminder notice to parent Anil Kapoor and escalate to accounts department.",
    },
    {
        "id": "DEMO-ALT-003",
        "type": "staffing",
        "priority": "critical",
        "title": "2 Teachers Absent — Timetable Conflicts Detected",
        "message": "Prof. Rajesh Gupta and Ms. Deepa Nair are absent today. 2 timetable slots have unresolved conflicts affecting classes 8A and 9A.",
        "resolved": False,
        "student_id": None,
        "action": "Run the OR-Tools Substitute Solver in the Smart Timetable Engine to auto-assign free teachers.",
    },
]

# ── 6. DOCUMENTS ──────────────────────────────────────────────────────────────
DOCUMENTS = [
    {
        "id": "DEMO-DOC-001",
        "filename": "admission_form_rahul_verma.pdf",
        "doc_type": "admission_form",
        "source_type": "file",
        "status": "review_required",
        "ocr_raw_text": "ADMISSION FORM\nStudent Name: Rahul Verma\nClass: 10A\nRoll No: 10A-002\nParent Name: Manoj Verma\nPhone: +91 33221 10099\nEmail: manoj.verma@gmail.com\nDate of Birth: 2009-03-15\nAddress: 42 MG Road, Bangalore",
        "fields": {
            "name": "Rahul Verma",
            "class": "10A",
            "roll_no": "10A-002",
            "parent_name": "Manoj Verma",
            "parent_phone": "+91 33221 10099",
            "parent_email": "manoj.verma@gmail.com",
            "date_of_birth": "2009-03-15",
            "address": "42 MG Road, Bangalore"
        },
        "confidence": 94.5,
        "validation_errors": None,
    },
    {
        "id": "DEMO-DOC-002",
        "filename": "fee_receipt_sneha_iyer.jpg",
        "doc_type": "fee_receipt",
        "source_type": "image",
        "status": "review_required",
        "ocr_raw_text": "FEE RECEIPT\nStudent: Sneha Iyer\nClass: 8B\nAmount Paid: Rs. 15000\nDate: 2024-11-01\nReceipt No: RCP-2024-0892\nMode: Online Transfer\nRemarks: Full semester fee",
        "fields": {
            "student_name": "Sneha Iyer",
            "class": "8B",
            "amount_paid": "15000",
            "payment_date": "2024-11-01",
            "receipt_no": "RCP-2024-0892",
            "payment_mode": "Online Transfer"
        },
        "confidence": 88.0,
        "validation_errors": None,
    },
    {
        "id": "DEMO-DOC-003",
        "filename": "admission_form_priya_patel.txt",
        "doc_type": "admission_form",
        "source_type": "text_paste",
        "status": "committed",
        "ocr_raw_text": "ADMISSION FORM: Student Priya Patel, Class 8A, Roll 8A-002, Parent Suresh Patel, Phone +91 91234 56789",
        "fields": {
            "name": "Priya Patel",
            "class": "8A",
            "roll_no": "8A-002",
            "parent_name": "Suresh Patel",
            "parent_phone": "+91 91234 56789"
        },
        "confidence": 97.0,
        "validation_errors": None,
    },
]


# ── Seed functions ─────────────────────────────────────────────────────────────

def seed_students() -> None:
    print("\n[INFO] Seeding students...")
    for s in STUDENTS:
        db_instance.upsert_student(s)
        print(f"  [OK] {s['id']} — {s['name']} ({s['class']}) | att:{s['attendance_pct']}% fee:{s['fee_status']}")

def seed_teachers() -> None:
    print("\n[INFO] Seeding teachers...")
    for t in TEACHERS:
        db_instance.upsert_teacher(t)
        print(f"  [OK] {t['id']} — {t['name']} ({t['subject']}) | status:{t['status']}")

def seed_availability() -> None:
    print("\n[INFO] Seeding teacher availability...")
    for a in AVAILABILITY:
        db_instance.upsert_teacher_availability(a)
        print(f"  [OK] {a['id']} — {a['teacher_name']} | {a['day_of_week']} P{a['period']} → {a['status']}")

def seed_timetable() -> None:
    print("\n[INFO] Seeding timetable...")
    db_instance.replace_timetable(TIMETABLE)
    conflicts = sum(1 for t in TIMETABLE if t["has_conflict"])
    subs = sum(1 for t in TIMETABLE if t["is_substitute"])
    print(f"  [OK] {len(TIMETABLE)} slots inserted | {conflicts} conflicts | {subs} substitutes")

def seed_alerts() -> None:
    print("\n[INFO] Seeding alerts...")
    for a in ALERTS:
        db_instance.insert_alert(a)
        print(f"  [OK] {a['id']} — [{a['priority'].upper()}] {a['title']}")

def seed_documents() -> None:
    print("\n[INFO] Seeding documents...")
    for d in DOCUMENTS:
        db_instance.insert_document(d)
        print(f"  [OK] {d['id']} — {d['filename']} | status:{d['status']}")


def main() -> None:
    print("=" * 60)
    print("  EduOS AI — Demo Data Seed")
    print("  Populating realistic school data for judges/reviewers")
    print("=" * 60)

    _check()
    print(f"\n[INFO] Connected to Supabase: {db_instance.supabase_url}")

    seed_students()
    seed_teachers()
    seed_availability()
    seed_timetable()
    seed_alerts()
    seed_documents()

    print("\n" + "=" * 60)
    print("  [PASS] Demo data seed completed successfully.")
    print("=" * 60)
    print("\n  Login at: https://eduos-ai-9ccfhasj4dkbznvatlpc7a.streamlit.app/")
    print("  Username: dev_admin  |  Password: password123")
    print("\n  What to explore:")
    print("  - Dashboard     → 3 active alerts, KPI cards with live data")
    print("  - Data Layer    → 9 students across 4 classes")
    print("  - Timetable     → 2 conflicts, run OR-Tools solver")
    print("  - Insights      → Click Recalculate to see analytics")
    print("  - Documents     → 2 records awaiting human review")
    print("  - AI Copilot    → Ask 'How is our staffing situation?'")
    print("  - dev_student   → Arjun Sharma (72% attendance, overdue fees)")
    print("  - dev_parent    → Same student monitoring view")
    print("  - dev_teacher   → Dr. Sunita Mehta class attendance view")


if __name__ == "__main__":
    main()
