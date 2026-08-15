import os
import sys
import unittest

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from validation import (
    repair_and_parse_json, 
    validate_student_data, 
    validate_teacher_data, 
    validate_teacher_availability, 
    validate_timetable_slot
)
from groq_client import groq_client
from doc_parser import parse_document_input
from teacher_parser import parse_teacher_input
from timetable_parser import parse_and_solve_timetable
from timetable_solver import solve_timetable_schedule
from db_client import db_instance

class TestGroqIntegrationAndPipeline(unittest.TestCase):

    def test_01_json_repair_and_validation(self):
        print("\n--- Test 01: JSON Repair & Pydantic Validation ---")
        markdown_json = '```json\n{"student_name": "Test Student", "class": "10B", "parent_name": "John Doe",}\n```'
        repaired = repair_and_parse_json(markdown_json)
        self.assertEqual(repaired.get("student_name"), "Test Student")
        self.assertEqual(repaired.get("class"), "10B")
        print("✓ Successfully repaired markdown JSON with trailing comma.")

        student_dict = {
            "id": "STU-TEST-01",
            "name": "Test Student",
            "class": "10B",
            "attendance_pct": 92.5
        }
        v_stu = validate_student_data(student_dict)
        self.assertEqual(v_stu.name, "Test Student")
        self.assertEqual(v_stu.class_name, "10B")
        print("✓ Successfully validated student record with Pydantic.")

    def test_02_groq_student_extraction(self):
        print("\n--- Test 02: Groq AI Student Form Extraction ---")
        if not groq_client.is_available():
            self.skipTest("Groq API key not set or client unavailable.")

        raw_text = "ADMISSION FORM 2026\nStudent Name: Aditi Rao\nGrade/Class: 9C\nParent Name: Ramesh Rao\nContact: +91 91234 56789"
        json_out = groq_client.extract_student_form_from_text(raw_text, doc_type="admission_form")
        parsed = repair_and_parse_json(json_out)

        self.assertIn("Aditi", parsed.get("student_name", ""))
        self.assertEqual(parsed.get("class"), "9C")
        print(f"✓ Groq AI extracted student: Name={parsed.get('student_name')}, Class={parsed.get('class')}")

    def test_03_teacher_availability_parsing(self):
        print("\n--- Test 03: Teacher Availability Parsing ---")
        if not groq_client.is_available():
            self.skipTest("Groq API client unavailable.")

        t_text = "Dr. Amit Joshi teaches Physics for 9A. Mrs. Kavita Singh is unavailable on Monday Period 3."
        teachers, avails, text = parse_teacher_input(raw_text_input=t_text)

        self.assertTrue(len(teachers) > 0 or len(avails) > 0)
        print(f"✓ Parsed teacher availability via Groq: Teachers={len(teachers)}, Availabilities={len(avails)}")

    def test_04_ortools_timetable_solver(self):
        print("\n--- Test 04: Google OR-Tools CP-SAT Constraint Solver ---")
        requested_slots = [
            {"period": 1, "class_name": "8A", "subject": "Math", "teacher_name": "Dr. Sunita Mehta"},
            {"period": 1, "class_name": "8B", "subject": "Math", "teacher_name": "Dr. Sunita Mehta"} # Teacher conflict!
        ]
        teachers_list = [
            {"id": "TCH-01", "name": "Dr. Sunita Mehta", "subject": "Math", "status": "active"},
            {"id": "TCH-02", "name": "Prof. Rajesh Gupta", "subject": "Math", "status": "active"}
        ]
        
        optimized_slots, warnings = solve_timetable_schedule(requested_slots, teachers_list)
        self.assertEqual(len(optimized_slots), 2)
        
        # Verify no double booking for Dr. Sunita Mehta in period 1
        p1_teachers = [s.get("teacher_id") for s in optimized_slots if s.get("period") == 1]
        self.assertNotEqual(p1_teachers[0], p1_teachers[1])
        print("✓ OR-Tools successfully prevented teacher double-booking and assigned substitute!")

    def test_05_end_to_end_supabase_flow(self):
        print("\n--- Test 05: End-to-End User Input -> Groq -> Supabase ---")
        if not db_instance.is_supabase_active:
            self.skipTest("Supabase DB client not active.")

        raw_text = "ADMISSION FORM\nStudent Name: Integration Test Student\nGrade/Class: 11A\nParent Name: Senior Parent\nContact: +91 99999 11111"
        doc_rec, val_stu = parse_document_input(raw_text_input=raw_text)

        self.assertIsNotNone(doc_rec.get("id"))
        
        # Save audit record in Supabase
        db_instance.insert_document(doc_rec)
        
        # Save student record in Supabase
        inserted_stu = db_instance.upsert_student(val_stu)
        self.assertEqual(inserted_stu.get("name"), "Integration Test Student")
        print("✓ Saved document audit trail and student record to Supabase DB!")

        # Clean up integration test record
        db_instance.delete_student(val_stu["id"])
        db_instance.supabase.table("documents").delete().eq("id", doc_rec["id"]).execute()
        print("✓ Cleaned up integration test record from Supabase.")

if __name__ == "__main__":
    unittest.main()
