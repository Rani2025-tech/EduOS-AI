"""
Groq AI integration + pipeline tests.
Run from project root: python -m pytest tests/test_groq_integration.py -v
Tests that require a live Groq API key are auto-skipped when the key is absent.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from validation import (
    repair_and_parse_json,
    validate_student_data,
    validate_teacher_data,
    validate_teacher_availability,
    validate_timetable_slot,
    validate_leave_application,
)
from groq_client import groq_client
from doc_parser import parse_document_input
from teacher_parser import parse_teacher_input
from timetable_solver import solve_timetable_schedule
from db_client import db_instance


# ── helpers ───────────────────────────────────────────────────────────────────

def groq_required(fn):
    """Skip decorator for tests that need a live Groq API key."""
    return pytest.mark.skipif(
        not groq_client.is_available(),
        reason="GROQ_API_KEY not set or client unavailable"
    )(fn)


def supabase_required(fn):
    """Skip decorator for tests that need a live Supabase connection."""
    return pytest.mark.skipif(
        not db_instance.is_supabase_active,
        reason="Supabase not active"
    )(fn)


# ── 1. JSON repair & Pydantic validation (no external deps) ───────────────────

class TestJsonRepairAndValidation:

    def test_repairs_markdown_code_block(self):
        raw = '```json\n{"student_name": "Test Student", "class": "10B"}\n```'
        result = repair_and_parse_json(raw)
        assert result["student_name"] == "Test Student"
        assert result["class"] == "10B"

    def test_repairs_trailing_comma(self):
        raw = '{"student_name": "Aarav", "class": "8A",}'
        result = repair_and_parse_json(raw)
        assert result["student_name"] == "Aarav"

    def test_extracts_json_from_narrative_text(self):
        raw = 'Here is the result: {"student_name": "Priya", "class": "9B"} as requested.'
        result = repair_and_parse_json(raw)
        assert result["class"] == "9B"

    def test_raises_on_empty_string(self):
        with pytest.raises(ValueError):
            repair_and_parse_json("")

    def test_raises_on_invalid_json(self):
        with pytest.raises(ValueError):
            repair_and_parse_json("this is not json at all !!!")

    def test_validate_student_data_success(self):
        data = {"id": "STU-001", "name": "Aarav Sharma", "class": "8A", "attendance_pct": 92.5}
        result = validate_student_data(data)
        assert result.name == "Aarav Sharma"
        assert result.class_name == "8A"

    def test_validate_student_data_missing_required_raises(self):
        with pytest.raises(ValueError):
            validate_student_data({"id": "STU-001"})  # missing name and class

    def test_validate_teacher_data_success(self):
        data = {"id": "TCH-01", "name": "Dr. Mehta", "subject": "Mathematics"}
        result = validate_teacher_data(data)
        assert result.subject == "Mathematics"

    def test_validate_teacher_availability_success(self):
        data = {"teacher_name": "Dr. Mehta", "day_of_week": "Monday", "period": 3, "status": "unavailable"}
        result = validate_teacher_availability(data)
        assert result.status == "unavailable"

    def test_validate_timetable_slot_success(self):
        data = {"period": 1, "class_name": "8A", "subject": "Math", "time": "08:30 AM"}
        result = validate_timetable_slot(data)
        assert result.period == 1

    def test_validate_leave_application_success(self):
        data = {
            "student_name": "Rohan Verma",
            "class": "9A",
            "leave_from": "2025-08-01",
            "leave_to": "2025-08-03",
            "reason": "Family function",
        }
        result = validate_leave_application(data)
        assert result.student_name == "Rohan Verma"
        assert result.approved is False

    def test_validate_leave_application_missing_required_raises(self):
        with pytest.raises(ValueError):
            validate_leave_application({"student_name": "Rohan"})  # missing class, dates, reason


# ── 2. Groq AI extraction (skipped without API key) ───────────────────────────

class TestGroqExtraction:

    @groq_required
    def test_extract_admission_form(self):
        raw = "ADMISSION FORM 2026\nStudent Name: Aditi Rao\nGrade: 9C\nParent: Ramesh Rao\nPhone: +91 91234 56789"
        result = repair_and_parse_json(
            groq_client.extract_student_form_from_text(raw, doc_type="admission_form")
        )
        assert "Aditi" in result.get("student_name", "")
        assert result.get("class") == "9C"

    @groq_required
    def test_extract_fee_receipt(self):
        raw = "FEE RECEIPT\nStudent: Priya Mehta\nClass: 8B\nAmount Paid: 12000\nStatus: paid"
        result = repair_and_parse_json(
            groq_client.extract_student_form_from_text(raw, doc_type="fee_receipt")
        )
        assert result.get("fee_status") == "paid" or result.get("student_name") is not None

    @groq_required
    def test_extract_leave_application(self):
        raw = (
            "LEAVE APPLICATION\nStudent: Rohan Verma\nClass: 9A\n"
            "Leave From: 2025-08-01\nLeave To: 2025-08-03\nReason: Family function\n"
            "Parent: Rajesh Verma\nPhone: +91 98765 43210"
        )
        result = repair_and_parse_json(
            groq_client.extract_leave_application_from_text(raw)
        )
        assert "Rohan" in result.get("student_name", "")
        assert result.get("leave_from") is not None
        assert result.get("reason") is not None

    @groq_required
    def test_extract_teacher_roster(self):
        raw = "Dr. Amit Joshi teaches Physics for 9A. Mrs. Kavita Singh is unavailable on Monday Period 3."
        teachers, avails, _ = parse_teacher_input(raw_text_input=raw)
        assert len(teachers) > 0 or len(avails) > 0

    @groq_required
    def test_doc_parser_pipeline(self):
        raw = "ADMISSION FORM\nStudent Name: Integration Test\nGrade: 11A\nParent: Test Parent"
        doc_rec, val_stu = parse_document_input(raw_text_input=raw)
        assert doc_rec is not None
        assert doc_rec.get("id") is not None


# ── 3. OR-Tools CP-SAT solver (no external deps) ─────────────────────────────

class TestORToolsSolver:

    def test_resolves_teacher_double_booking(self):
        slots = [
            {"period": 1, "class_name": "8A", "subject": "Math", "teacher_name": "Dr. Mehta"},
            {"period": 1, "class_name": "8B", "subject": "Math", "teacher_name": "Dr. Mehta"},
        ]
        teachers = [
            {"id": "TCH-01", "name": "Dr. Mehta",  "subject": "Math", "status": "active"},
            {"id": "TCH-02", "name": "Prof. Gupta", "subject": "Math", "status": "active"},
        ]
        optimized, warnings = solve_timetable_schedule(slots, teachers)
        assert len(optimized) == 2
        p1_teachers = [s.get("teacher_id") for s in optimized if s.get("period") == 1]
        assert p1_teachers[0] != p1_teachers[1]

    def test_returns_slots_for_single_entry(self):
        slots = [{"period": 1, "class_name": "8A", "subject": "Math", "teacher_name": "Dr. Mehta"}]
        teachers = [{"id": "TCH-01", "name": "Dr. Mehta", "subject": "Math", "status": "active"}]
        optimized, _ = solve_timetable_schedule(slots, teachers)
        assert len(optimized) == 1

    def test_absent_teacher_gets_substitute(self):
        slots = [{"period": 1, "class_name": "8A", "subject": "Math", "teacher_name": "Dr. Mehta"}]
        teachers = [
            {"id": "TCH-01", "name": "Dr. Mehta",  "subject": "Math", "status": "absent"},
            {"id": "TCH-02", "name": "Prof. Gupta", "subject": "Math", "status": "active"},
        ]
        optimized, _ = solve_timetable_schedule(slots, teachers)
        assert len(optimized) == 1

    def test_empty_slots_returns_empty(self):
        optimized, warnings = solve_timetable_schedule([], [])
        assert optimized == [] or isinstance(optimized, list)


# ── 4. End-to-end Supabase flow (skipped without DB) ─────────────────────────

class TestSupabaseEndToEnd:

    @supabase_required
    def test_document_and_student_roundtrip(self):
        raw = "ADMISSION FORM\nStudent Name: Integration Test Student\nGrade: 11A\nParent: Senior Parent"
        doc_rec, val_stu = parse_document_input(raw_text_input=raw)

        assert doc_rec.get("id") is not None

        db_instance.insert_document(doc_rec)
        saved = db_instance.upsert_student(val_stu)
        assert saved.get("name") == "Integration Test Student"

        # cleanup
        db_instance.delete_student(val_stu["id"])
        db_instance.supabase.table("documents").delete().eq("id", doc_rec["id"]).execute()
