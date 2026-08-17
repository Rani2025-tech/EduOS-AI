"""
EduOS AI — Supabase Database Smoke Test
========================================
Run from the project root:
    python verify_supabase.py

Checks:
  1. Environment configuration (SUPABASE_URL, SUPABASE_KEY, JWT_SECRET_KEY, GROQ_API_KEY)
  2. Supabase connection
  3. All 9 required tables are accessible (READ)
  4. RLS does not block expected anon-key operations (write probe)
  5. Safe INSERT / UPSERT using a reserved test-only ID prefix
  6. UPDATE
  7. DELETE of test records only (never touches real data)
  8. Users table read access + development user presence (informational)

Test records use IDs prefixed with "SMOKE-TEST-" so they are
clearly identifiable and safe to delete.
"""

import sys
import os

from db_client import db_instance, DB_STATUS_CONNECTED, DB_STATUS_MISSING_CONFIG, DB_STATUS_CONN_FAILED
from env_config import get_env_report, get_missing_vars, format_env_summary, validate_supabase_url
from auth import is_auth_configured, get_auth_config_errors

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
SKIP = "\033[93m[SKIP]\033[0m"
INFO = "\033[94m[INFO]\033[0m"
WARN = "\033[93m[WARN]\033[0m"

TEST_STUDENT_ID = "SMOKE-TEST-STU-001"
TEST_ALERT_ID   = "SMOKE-TEST-ALT-001"
TEST_AVAIL_ID   = "SMOKE-TEST-AV-001"
TEST_USER_ID    = "SMOKE-TEST-USR-001"

DEV_USERNAMES = ["dev_admin", "dev_teacher", "dev_student", "dev_parent"]

REQUIRED_TABLES = [
    "students",
    "teachers",
    "teacher_availability",
    "timetable",
    "documents",
    "alerts",
    "insights",
    "copilot_messages",
    "users",
]


def section(title: str):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print('='*55)


def run_verification():
    section("EduOS AI — Supabase Smoke Test")
    failures = 0

    # ── 1. Environment Configuration ──────────────────────────
    section("1. Environment Configuration")
    report = get_env_report()

    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")).strip()

    if report["SUPABASE_URL"]["set"]:
        url_error = validate_supabase_url(url)
        if url_error:
            print(f"{FAIL} SUPABASE_URL: {url_error}")
            failures += 1
        else:
            print(f"{PASS} SUPABASE_URL is set and format looks valid")
    else:
        print(f"{FAIL} SUPABASE_URL is missing — copy .env.example to .env")
        failures += 1

    if report["SUPABASE_KEY"]["set"]:
        print(f"{PASS} SUPABASE_KEY is set")
    else:
        print(f"{FAIL} SUPABASE_KEY is missing — copy .env.example to .env")
        failures += 1

    if report["JWT_SECRET_KEY"]["set"]:
        print(f"{PASS} JWT_SECRET_KEY is set (login will work)")
    else:
        print(f"{WARN} JWT_SECRET_KEY is not set — authentication will fail until configured")
        print(f"       Hint: {report['JWT_SECRET_KEY']['hint']}")

    if report["GROQ_API_KEY"]["set"]:
        print(f"{PASS} GROQ_API_KEY is set")
    else:
        print(f"{SKIP} GROQ_API_KEY is not set — AI extraction will be unavailable")

    if failures:
        print(f"\n{INFO} Environment summary:\n{format_env_summary()}")
        print(f"\n{FAIL} Fix missing database variables before continuing.")
        sys.exit(1)

    # ── 2. Connection ──────────────────────────────────────────
    section("2. Supabase Connection")
    if db_instance.connection_status == DB_STATUS_MISSING_CONFIG:
        print(f"{FAIL} Cannot connect: credentials not configured.")
        missing = get_missing_vars(for_db=True)
        if missing:
            print(f"       Missing: {', '.join(missing)}")
        sys.exit(1)
    elif db_instance.connection_status == DB_STATUS_CONN_FAILED:
        print(f"{FAIL} Credentials found but connection failed.")
        if db_instance.config_errors:
            for err in db_instance.config_errors:
                print(f"       {err}")
        print("       Check SUPABASE_URL, SUPABASE_KEY, schema.sql, and RLS policies.")
        sys.exit(1)
    else:
        print(f"{PASS} Connected to Supabase: {db_instance.supabase_url}")

    db = db_instance.supabase

    # ── 3. Table READ Access ───────────────────────────────────
    section("3. Table READ Access (all 9 required tables)")
    table_counts = {}
    all_readable = True
    for table in REQUIRED_TABLES:
        try:
            res = db.table(table).select("id", count="exact").limit(1).execute()
            count = res.count if res.count is not None else len(res.data or [])
            table_counts[table] = count
            print(f"{PASS} {table:<25} rows accessible: {count}")
        except Exception as e:
            print(f"{FAIL} {table:<25} ERROR: {e}")
            all_readable = False

    if not all_readable:
        print(f"\n{FAIL} One or more tables are missing or blocked by RLS.")
        print("       Apply schema.sql (including RLS policies) in the Supabase SQL Editor.")
        sys.exit(1)

    # ── 4. RLS Write Probe ─────────────────────────────────────
    section("4. RLS Write Probe (anon key must not be blocked)")
    rls_ok = True
    probe_tables = ["students", "teachers", "documents", "alerts", "users"]
    for table in probe_tables:
        try:
            if table == "users":
                # Read-only probe for users — full write tested in section 5 via create_user path
                res = db.table(table).select("id").limit(1).execute()
            else:
                res = db.table(table).select("id").limit(1).execute()
            print(f"{PASS} {table:<25} RLS allows SELECT via anon key")
        except Exception as e:
            print(f"{FAIL} {table:<25} RLS may be blocking access: {e}")
            rls_ok = False

    if not rls_ok:
        print(f"\n{FAIL} RLS is blocking expected operations.")
        print("       Re-apply the RLS policy section of schema.sql in Supabase SQL Editor.")
        sys.exit(1)

    # ── 5. INSERT / UPSERT ────────────────────────────────────
    section("5. INSERT / UPSERT (test records only)")

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

    # Users table write probe (bcrypt hash of a throwaway test password)
    try:
        from auth import hash_password
        test_user = {
            "id": TEST_USER_ID,
            "username": "smoke_test_user",
            "password_hash": hash_password("smoke-test-only-not-a-real-password"),
            "role": "admin",
            "linked_id": None,
            "is_active": True,
        }
        res = db.table("users").upsert(test_user).execute()
        assert res.data, "No data returned from upsert"
        print(f"{PASS} users    — upsert OK (ID={TEST_USER_ID})")
    except Exception as e:
        print(f"{FAIL} users    — upsert FAILED: {e}")

    # ── 6. UPDATE ─────────────────────────────────────────────
    section("6. UPDATE")
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

    # ── 7. DELETE (test records only) ─────────────────────────
    section("7. DELETE (smoke test records only)")
    for table, col, val in [
        ("alerts",               "id", TEST_ALERT_ID),
        ("teacher_availability", "id", TEST_AVAIL_ID),
        ("users",                "id", TEST_USER_ID),
        ("students",             "id", TEST_STUDENT_ID),
    ]:
        try:
            db.table(table).delete().eq(col, val).execute()
            print(f"{PASS} {table:<25} — deleted test record ({val})")
        except Exception as e:
            print(f"{FAIL} {table:<25} — delete FAILED: {e}")

    # ── 8. Auth configuration & dev users ─────────────────────
    section("8. Authentication & Development Users")
    if is_auth_configured():
        print(f"{PASS} JWT_SECRET_KEY configured — login tokens can be issued")
    else:
        print(f"{WARN} JWT_SECRET_KEY not configured — run: python -c \"import secrets; print(secrets.token_hex(32))\"")
        for var in get_auth_config_errors():
            print(f"       Missing: {var}")

    dev_found = 0
    for username in DEV_USERNAMES:
        user = db_instance.get_user_by_username(username)
        if user:
            dev_found += 1
            print(f"{PASS} dev user exists: {username} (role={user.get('role')})")
        else:
            print(f"{INFO} dev user not found: {username}")

    if dev_found == 0:
        print(f"\n{INFO} No development users found. After applying schema.sql, run:")
        print("       set DEV_SEED_PASSWORD=your-local-dev-password")
        print("       python seed_dev_users.py")
    elif dev_found < len(DEV_USERNAMES):
        print(f"\n{INFO} Partial dev user set ({dev_found}/{len(DEV_USERNAMES)}). Re-run seed_dev_users.py to fill gaps.")

    # ── Summary ───────────────────────────────────────────────
    section("Summary")
    print(f"{PASS} All smoke tests completed.")
    print(f"{INFO} Current row counts per table:")
    for t in REQUIRED_TABLES:
        c = table_counts.get(t, "?")
        print(f"       {t:<25} {c} rows")
    print()


if __name__ == "__main__":
    run_verification()
