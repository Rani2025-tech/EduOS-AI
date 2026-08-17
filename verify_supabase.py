"""
EduOS AI — Supabase Database Smoke Test
========================================
Run from the project root:
    python verify_supabase.py

Checks:
  1. Environment configuration
  2. Supabase connection
  3. All 8 required tables are accessible (READ)
  4. Safe INSERT / UPSERT using a reserved test-only ID prefix
  5. UPDATE
  6. DELETE of test records only (never touches real data)

Test records use IDs prefixed with "SMOKE-TEST-" so they are
clearly identifiable and safe to delete.
"""

import sys
import os
from db_client import db_instance, DB_STATUS_CONNECTED, DB_STATUS_MISSING_CONFIG, DB_STATUS_CONN_FAILED

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
SKIP = "\033[93m[SKIP]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

TEST_STUDENT_ID = "SMOKE-TEST-STU-001"
TEST_ALERT_ID   = "SMOKE-TEST-ALT-001"
TEST_AVAIL_ID   = "SMOKE-TEST-AV-001"

def section(title: str):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print('='*55)

def run_verification():
    section("EduOS AI — Supabase Smoke Test")

    # ── 1. Environment Configuration ──────────────────────────
    section("1. Environment Configuration")
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")).strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    if url:
        print(f"{PASS} SUPABASE_URL is set")
    else:
        print(f"{FAIL} SUPABASE_URL is missing — copy .env.example to .env")

    if key:
        print(f"{PASS} SUPABASE_KEY is set")
    else:
        print(f"{FAIL} SUPABASE_KEY is missing — copy .env.example to .env")

    if groq_key:
        print(f"{PASS} GROQ_API_KEY is set")
    else:
        print(f"{SKIP} GROQ_API_KEY is not set — AI extraction will be unavailable")

    # ── 2. Connection ──────────────────────────────────────────
    section("2. Supabase Connection")
    if db_instance.connection_status == DB_STATUS_MISSING_CONFIG:
        print(f"{FAIL} Cannot connect: credentials not configured.")
        print("       Set SUPABASE_URL and SUPABASE_KEY in your .env file.")
        sys.exit(1)
    elif db_instance.connection_status == DB_STATUS_CONN_FAILED:
        print(f"{FAIL} Credentials found but connection failed.")
        print("       Check that your SUPABASE_URL and SUPABASE_KEY are correct.")
        sys.exit(1)
    else:
        print(f"{PASS} Connected to Supabase: {db_instance.supabase_url}")

    db = db_instance.supabase

    # ── 3. Table READ Access ───────────────────────────────────
    section("3. Table READ Access (all 8 required tables)")
    required_tables = [
        "students",
        "teachers",
        "teacher_availability",
        "timetable",
        "documents",
        "alerts",
        "insights",
        "copilot_messages",
    ]
    table_counts = {}
    all_readable = True
    for table in required_tables:
        try:
            res = db.table(table).select("id", count="exact").limit(1).execute()
            count = res.count if res.count is not None else len(res.data or [])
            table_counts[table] = count
            print(f"{PASS} {table:<25} rows accessible: {count}")
        except Exception as e:
            print(f"{FAIL} {table:<25} ERROR: {e}")
            all_readable = False

    if not all_readable:
        print(f"\n{FAIL} One or more tables are missing. Apply schema.sql in the Supabase SQL Editor.")
        sys.exit(1)

    # ── 4. INSERT / UPSERT ────────────────────────────────────
    section("4. INSERT / UPSERT (test records only)")

    test_student = {
        "id": TEST_STUDENT_ID,
        "name": "Smoke Test Student",
        "roll_no": "SMOKE-ROLL-001",
        "class": "TEST-CLASS",
        "parent_name": "Smoke Parent",
        "parent_phone": "+91 00000 00000",
        "parent_email": "smoke.test@eduos.test",
        "attendance_pct": 95.0,
        "fee_status": "pending",
        "fee_amount_due": 1000,
        "gpa": 3.5,
        "risk_level": "low",
        "assigned_room": "Room SMOKE",
    }
    try:
        res = db.table("students").upsert(test_student).execute()
        assert res.data, "No data returned from upsert"
        print(f"{PASS} students — upsert OK (ID={TEST_STUDENT_ID})")
    except Exception as e:
        print(f"{FAIL} students — upsert FAILED: {e}")

    test_alert = {
        "id": TEST_ALERT_ID,
        "type": "smoke_test",
        "priority": "low",
        "title": "Smoke Test Alert",
        "message": "This is an automated smoke test record.",
        "resolved": False,
        "student_id": TEST_STUDENT_ID,
        "action": "Delete after test",
    }
    try:
        res = db.table("alerts").upsert(test_alert).execute()
        assert res.data, "No data returned from upsert"
        print(f"{PASS} alerts   — upsert OK (ID={TEST_ALERT_ID})")
    except Exception as e:
        print(f"{FAIL} alerts   — upsert FAILED: {e}")

    test_avail = {
        "id": TEST_AVAIL_ID,
        "teacher_name": "Smoke Test Teacher",
        "day_of_week": "Monday",
        "period": 1,
        "status": "unavailable",
        "notes": "Smoke test record",
    }
    try:
        res = db.table("teacher_availability").upsert(test_avail).execute()
        assert res.data, "No data returned from upsert"
        print(f"{PASS} teacher_availability — upsert OK (ID={TEST_AVAIL_ID})")
    except Exception as e:
        print(f"{FAIL} teacher_availability — upsert FAILED: {e}")

    # ── 5. UPDATE ─────────────────────────────────────────────
    section("5. UPDATE")
    try:
        res = db.table("students").update({"attendance_pct": 80.0, "risk_level": "medium"}).eq("id", TEST_STUDENT_ID).execute()
        assert res.data, "No data returned from update"
        updated_att = res.data[0].get("attendance_pct")
        print(f"{PASS} students — update OK (attendance_pct={updated_att})")
    except Exception as e:
        print(f"{FAIL} students — update FAILED: {e}")

    try:
        res = db.table("alerts").update({"resolved": True}).eq("id", TEST_ALERT_ID).execute()
        assert res.data, "No data returned from update"
        resolved = res.data[0].get("resolved")
        print(f"{PASS} alerts   — update OK (resolved={resolved})")
    except Exception as e:
        print(f"{FAIL} alerts   — update FAILED: {e}")

    # ── 6. DELETE (test records only) ─────────────────────────
    section("6. DELETE (smoke test records only)")
    for table, col, val in [
        ("alerts",               "id", TEST_ALERT_ID),
        ("teacher_availability", "id", TEST_AVAIL_ID),
        ("students",             "id", TEST_STUDENT_ID),
    ]:
        try:
            db.table(table).delete().eq(col, val).execute()
            print(f"{PASS} {table:<25} — deleted test record ({val})")
        except Exception as e:
            print(f"{FAIL} {table:<25} — delete FAILED: {e}")

    # ── Summary ───────────────────────────────────────────────
    section("Summary")
    print(f"{PASS} All smoke tests completed.")
    print(f"{INFO} Current row counts per table:")
    for t, c in table_counts.items():
        print(f"       {t:<25} {c} rows")
    print()

if __name__ == "__main__":
    run_verification()
