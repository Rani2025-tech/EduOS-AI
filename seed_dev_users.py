"""
EduOS AI — Development User Seed Script
========================================
Creates DEVELOPMENT-ONLY login accounts and minimal linked domain records
so authentication works on a fresh Supabase database.

⚠️  DEVELOPMENT ONLY — never run against production with default credentials.

Usage (from project root):
    set DEV_SEED_PASSWORD=your-local-dev-password   # Windows
    export DEV_SEED_PASSWORD=your-local-dev-password  # macOS/Linux
    python seed_dev_users.py

Requirements:
    - .env with SUPABASE_URL and SUPABASE_KEY configured
    - schema.sql applied (including RLS policies)
    - DEV_SEED_PASSWORD set in the environment (never committed to git)

Accounts created (idempotent — skips existing usernames):
    dev_admin   → role: admin
    dev_teacher → role: teacher  (linked to DEV-TCH-001)
    dev_student → role: student  (linked to DEV-STU-001)
    dev_parent  → role: parent   (linked to DEV-STU-001)

Linked domain records (created if missing):
    DEV-STU-001  sample student for dev_student / dev_parent
    DEV-TCH-001  sample teacher for dev_teacher
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from auth import hash_password
from db_client import db_instance, DB_STATUS_CONNECTED, DB_STATUS_MISSING_CONFIG, DB_STATUS_CONN_FAILED
from env_config import get_missing_vars, format_env_summary

# ── Development persona definitions ───────────────────────────────────────────

DEV_STUDENT_ID = "DEV-STU-001"
DEV_TEACHER_ID = "DEV-TCH-001"

DEV_STUDENT = {
    "id": DEV_STUDENT_ID,
    "name": "Dev Sample Student",
    "roll_no": "DEV-8A-001",
    "class": "8A",
    "parent_name": "Dev Sample Parent",
    "parent_phone": "+91 90000 00001",
    "parent_email": "dev.parent@eduos.test",
    "attendance_pct": 88.0,
    "fee_status": "pending",
    "fee_amount_due": 5000,
    "gpa": 3.2,
    "risk_level": "low",
    "assigned_room": "Room 201",
}

DEV_TEACHER = {
    "id": DEV_TEACHER_ID,
    "name": "Dev Sample Teacher",
    "subject": "Mathematics",
    "email": "dev.teacher@eduos.test",
    "assigned_classes": "8A",
    "status": "active",
}

DEV_USERS = [
    {
        "id": "DEV-USR-ADMIN",
        "username": "dev_admin",
        "role": "admin",
        "linked_id": None,
    },
    {
        "id": "DEV-USR-TEACHER",
        "username": "dev_teacher",
        "role": "teacher",
        "linked_id": DEV_TEACHER_ID,
    },
    {
        "id": "DEV-USR-STUDENT",
        "username": "dev_student",
        "role": "student",
        "linked_id": DEV_STUDENT_ID,
    },
    {
        "id": "DEV-USR-PARENT",
        "username": "dev_parent",
        "role": "parent",
        "linked_id": DEV_STUDENT_ID,
    },
]


def _fail(msg: str, code: int = 1) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(code)


def _check_prerequisites() -> str:
    missing_db = get_missing_vars(for_db=True)
    if missing_db:
        _fail(
            "Missing database environment variables:\n"
            + format_env_summary()
            + "\nCopy .env.example to .env and fill in Supabase credentials."
        )

    if db_instance.connection_status == DB_STATUS_MISSING_CONFIG:
        _fail("Supabase credentials not configured.")
    if db_instance.connection_status == DB_STATUS_CONN_FAILED:
        _fail("Supabase connection failed. Check SUPABASE_URL and SUPABASE_KEY.")

    password = os.getenv("DEV_SEED_PASSWORD", "").strip()
    if not password:
        _fail(
            "DEV_SEED_PASSWORD is not set.\n"
            "Set a local development password in your environment, e.g.:\n"
            "  Windows:   set DEV_SEED_PASSWORD=your-local-dev-password\n"
            "  macOS/Linux: export DEV_SEED_PASSWORD=your-local-dev-password\n"
            "Never commit this value to version control."
        )
    if len(password) < 8:
        _fail("DEV_SEED_PASSWORD must be at least 8 characters for development accounts.")

    return password


def seed_domain_records() -> None:
    """Upsert minimal student/teacher records required for linked_id references."""
    db_instance.upsert_student(DEV_STUDENT)
    print(f"[OK]   student record upserted: {DEV_STUDENT_ID}")
    db_instance.upsert_teacher(DEV_TEACHER)
    print(f"[OK]   teacher record upserted: {DEV_TEACHER_ID}")


def seed_users(password: str) -> None:
    """Create development user accounts with bcrypt password hashes."""
    password_hash = hash_password(password)

    for spec in DEV_USERS:
        existing = db_instance.get_user_by_username(spec["username"])
        if existing:
            print(f"[SKIP] user already exists: {spec['username']} (role={spec['role']})")
            continue

        user_data = {
            "id": spec["id"],
            "username": spec["username"],
            "password_hash": password_hash,
            "role": spec["role"],
            "linked_id": spec["linked_id"],
            "is_active": True,
        }
        created = db_instance.create_user(user_data)
        if created:
            print(f"[OK]   user created: {spec['username']} (role={spec['role']})")
        else:
            _fail(f"Failed to create user: {spec['username']}")


def main() -> None:
    print("=" * 55)
    print("  EduOS AI — Development User Seed")
    print("  ⚠️  DEVELOPMENT ONLY")
    print("=" * 55)

    password = _check_prerequisites()
    print(f"[INFO] Supabase connected: {db_instance.supabase_url}")
    print("[INFO] Seeding linked domain records...")
    seed_domain_records()
    print("[INFO] Seeding development user accounts...")
    seed_users(password)

    print("\n[PASS] Development seed completed.")
    print("[INFO] Login with any of these usernames and your DEV_SEED_PASSWORD:")
    for spec in DEV_USERS:
        print(f"       - {spec['username']} ({spec['role']})")
    print("[INFO] Password value is NOT printed — use the DEV_SEED_PASSWORD you set.")


if __name__ == "__main__":
    main()
