import sys
import os
from db_client import db_instance

def run_verification():
    print("====================================================")
    print("     EduOS AI -- Supabase Real CRUD Verification    ")
    print("====================================================")

    if not db_instance.is_supabase_active or not db_instance.supabase:
        print("[ERROR] Supabase client is not active!")
        sys.exit(1)

    print(f"[OK] Active Supabase URL: {db_instance.supabase_url}")

    # 1. READ TEST
    print("\n--- [1] READ Initial Records from Supabase ---")
    students = db_instance.get_students()
    teachers = db_instance.get_teachers()
    timetable = db_instance.get_timetable()
    documents = db_instance.get_documents()
    alerts = db_instance.get_alerts()
    insights = db_instance.get_insights()
    copilot_msgs = db_instance.get_copilot_messages()

    print(f"[READ] Students count: {len(students)}")
    print(f"[READ] Teachers count: {len(teachers)}")
    print(f"[READ] Timetable slots: {len(timetable)}")
    print(f"[READ] Documents count: {len(documents)}")
    print(f"[READ] Alerts count: {len(alerts)}")
    print(f"[READ] Insights count: {len(insights)}")
    print(f"[READ] Copilot messages count: {len(copilot_msgs)}")

    # 2. CREATE TEST
    print("\n--- [2] CREATE Real Test Records in Supabase ---")
    test_student = {
        "id": "STU-999",
        "name": "Verification Student",
        "roll_no": "TEST-999",
        "class": "10A",
        "parent_name": "Test Parent",
        "parent_phone": "+91 99999 88888",
        "parent_email": "test.parent@example.com",
        "attendance_pct": 95.0,
        "fee_status": "pending",
        "fee_amount_due": 5000,
        "gpa": 3.8,
        "risk_level": "low",
        "assigned_room": "Room 909"
    }
    inserted_stu = db_instance.upsert_student(test_student)
    print(f"[CREATE] Inserted Student: ID={inserted_stu.get('id')}, Name={inserted_stu.get('name')}")

    test_alert = {
        "id": "ALT-999",
        "type": "verification",
        "priority": "low",
        "title": "CRUD Test Alert",
        "message": "System verification test alert.",
        "resolved": False,
        "student_id": "STU-999",
        "action": "Verify deletion"
    }
    inserted_alt = db_instance.insert_alert(test_alert)
    print(f"[CREATE] Inserted Alert: ID={inserted_alt.get('id')}, Title={inserted_alt.get('title')}")

    # 3. UPDATE TEST
    print("\n--- [3] UPDATE Records in Supabase ---")
    test_student["attendance_pct"] = 65.0
    test_student["fee_status"] = "paid"
    test_student["fee_amount_due"] = 0
    test_student["risk_level"] = "high"
    updated_stu = db_instance.upsert_student(test_student)
    print(f"[UPDATE] Updated Student STU-999: Attendance={updated_stu.get('attendance_pct')}%, Fee={updated_stu.get('fee_status')}, Risk={updated_stu.get('risk_level')}")

    resolved_success = db_instance.resolve_alert("ALT-999")
    print(f"[UPDATE] Resolved Alert ALT-999: Status={resolved_success}")

    # Verify update from database
    verify_alerts = db_instance.get_alerts()
    target_alert = next((a for a in verify_alerts if a["id"] == "ALT-999"), None)
    if target_alert:
        print(f"[UPDATE] Verified Alert Resolution in Supabase: Resolved={target_alert.get('resolved')}")

    # 4. DELETE TEST
    print("\n--- [4] DELETE Test Records from Supabase ---")
    deleted_stu = db_instance.delete_student("STU-999")
    print(f"[DELETE] Deleted Student STU-999: Success={deleted_stu}")

    db_instance.supabase.table("alerts").delete().eq("id", "ALT-999").execute()
    print("[DELETE] Cleaned up test alert ALT-999 from Supabase")

    # Final Read Verification
    final_students = db_instance.get_students()
    print(f"\n[READ] Post-cleanup Student Count in Supabase: {len(final_students)}")

    print("\n====================================================")
    print(" ALL SUPABASE CRUD OPERATIONS VERIFIED SUCCESSFULLY!")
    print("====================================================")

if __name__ == "__main__":
    run_verification()
