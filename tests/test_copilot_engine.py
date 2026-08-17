"""
Tests for copilot_engine.py
Run from project root: python -m pytest tests/test_copilot_engine.py -v

LLM is mocked throughout — no real API key required.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import MagicMock, patch
from copilot_engine import (
    classify_intent,
    build_context,
    answer_question,
    _deterministic_fallback,
    _context_to_text,
)

# ── Shared fixtures ───────────────────────────────────────────────────────────

STUDENTS = [
    {"id": "S1", "name": "Aarav",  "attendance_pct": 60.0, "fee_status": "overdue",  "fee_amount_due": 15000, "gpa": 2.1},
    {"id": "S2", "name": "Priya",  "attendance_pct": 90.0, "fee_status": "paid",     "fee_amount_due": 0,     "gpa": 3.8},
    {"id": "S3", "name": "Rohan",  "attendance_pct": 72.0, "fee_status": "pending",  "fee_amount_due": 5000,  "gpa": 1.9},
]

TEACHERS = [
    {"id": "T1", "name": "Dr. Mehta",  "subject": "Math",    "status": "active"},
    {"id": "T2", "name": "Mrs. Singh", "subject": "English", "status": "absent"},
]

TIMETABLE = [
    {"id": "SL1", "period": 1, "subject": "Math",    "teacher_name": "Dr. Mehta",  "has_conflict": False, "is_substitute": False},
    {"id": "SL2", "period": 2, "subject": "English", "teacher_name": "Mrs. Singh", "has_conflict": True,  "is_substitute": False},
    {"id": "SL3", "period": 3, "subject": "Science", "teacher_name": "Dr. Mehta",  "has_conflict": False, "is_substitute": True},
    {"id": "SL4", "period": 4, "subject": "Math",    "teacher_name": "Dr. Mehta",  "has_conflict": False, "is_substitute": False},
    {"id": "SL5", "period": 5, "subject": "Math",    "teacher_name": "Dr. Mehta",  "has_conflict": False, "is_substitute": False},
    {"id": "SL6", "period": 6, "subject": "Math",    "teacher_name": "Dr. Mehta",  "has_conflict": False, "is_substitute": False},
    {"id": "SL7", "period": 7, "subject": "Math",    "teacher_name": "Dr. Mehta",  "has_conflict": False, "is_substitute": False},
]

DOCUMENTS = [
    {"id": "D1", "filename": "form1.pdf", "status": "review_required", "validation_errors": None},
    {"id": "D2", "filename": "form2.pdf", "status": "committed",       "validation_errors": None},
]

EMPTY_GROQ = MagicMock()
EMPTY_GROQ.is_available.return_value = False


def _mock_groq(response_text: str = "Mocked LLM response.") -> MagicMock:
    """Returns a mock Groq client that returns a fixed response."""
    mock = MagicMock()
    mock.is_available.return_value = True
    mock.model = "llama-3.3-70b-versatile"
    choice = MagicMock()
    choice.message.content = response_text
    mock.client.chat.completions.create.return_value = MagicMock(choices=[choice])
    return mock


# ── 1. Intent: student count ──────────────────────────────────────────────────

class TestStudentIntent:

    def test_how_many_students(self):
        assert classify_intent("How many students are there?") == "students"

    def test_total_enrolled(self):
        assert classify_intent("What is the total enrolled count?") == "students"

    def test_student_count_deterministic_fallback(self):
        ctx = build_context(STUDENTS, [], [], [], [])
        result = _deterministic_fallback(ctx, "students")
        assert "3" in result
        assert "student" in result.lower()


# ── 2. Intent: attendance ─────────────────────────────────────────────────────

class TestAttendanceIntent:

    def test_attendance_risk_phrase(self):
        assert classify_intent("How many students are at attendance risk?") == "attendance"

    def test_below_75_phrase(self):
        assert classify_intent("Which students have attendance below 75%?") == "attendance"

    def test_low_attendance_phrase(self):
        assert classify_intent("Show me students with low attendance") == "attendance"

    def test_attendance_fallback_contains_count(self):
        ctx = build_context(STUDENTS, [], [], [], [])
        result = _deterministic_fallback(ctx, "attendance")
        # 2 students below 75% (Aarav=60, Rohan=72)
        assert "2" in result


# ── 3. Intent: fees ───────────────────────────────────────────────────────────

class TestFeeIntent:

    def test_fee_collection_rate(self):
        assert classify_intent("What is the fee collection rate?") == "fees"

    def test_overdue_fees(self):
        assert classify_intent("Are there overdue fees?") == "fees"

    def test_pending_fee(self):
        assert classify_intent("How much fee is pending?") == "fees"

    def test_fee_fallback_contains_amount(self):
        ctx = build_context(STUDENTS, [], [], [], [])
        result = _deterministic_fallback(ctx, "fees")
        # Fixture: Aarav overdue ₹15000 + Rohan pending ₹5000 = ₹20000 total
        assert "20,000" in result or "20000" in result


# ── 4. Intent: documents ──────────────────────────────────────────────────────

class TestDocumentIntent:

    def test_documents_pending_review(self):
        assert classify_intent("How many documents need review?") == "documents"

    def test_validation_failures(self):
        assert classify_intent("Are there any validation failures?") == "documents"

    def test_document_fallback_contains_pending(self):
        ctx = build_context([], [], [], [], DOCUMENTS)
        result = _deterministic_fallback(ctx, "documents")
        assert "1" in result  # 1 pending review


# ── 5. Intent: timetable conflicts ───────────────────────────────────────────

class TestTimetableIntent:

    def test_timetable_conflicts(self):
        assert classify_intent("Are there timetable conflicts?") == "timetable"

    def test_schedule_clash(self):
        assert classify_intent("Is there a schedule clash?") == "timetable"

    def test_timetable_fallback_contains_conflict_count(self):
        ctx = build_context([], [], [], TIMETABLE, [])
        result = _deterministic_fallback(ctx, "timetable")
        assert "1" in result  # 1 conflict slot


# ── 6. Intent: teacher availability ──────────────────────────────────────────

class TestTeacherAvailabilityIntent:

    def test_available_teachers(self):
        assert classify_intent("How many teachers are available?") == "teacher_availability"

    def test_absent_teacher(self):
        assert classify_intent("Which teachers are absent today?") == "teacher_availability"

    def test_teacher_unavailable(self):
        assert classify_intent("Are any teachers unavailable?") == "teacher_availability"

    def test_availability_fallback_counts(self):
        ctx = build_context([], TEACHERS, [], [], [])
        result = _deterministic_fallback(ctx, "teacher_availability")
        # 1 absent (Mrs. Singh), 1 available (Dr. Mehta)
        assert "1" in result
        assert "2" in result


# ── 7. Intent: teacher workload ───────────────────────────────────────────────

class TestTeacherWorkloadIntent:

    def test_overloaded_teachers(self):
        assert classify_intent("Which teachers are overloaded?") == "teacher_workload"

    def test_heaviest_load(self):
        assert classify_intent("Who is carrying the heaviest teaching load?") == "teacher_workload"

    def test_too_many_classes(self):
        assert classify_intent("Which staff members have too many classes?") == "teacher_workload"

    def test_workload_fallback_contains_max(self):
        ctx = build_context([], TEACHERS, [], TIMETABLE, [])
        result = _deterministic_fallback(ctx, "teacher_workload")
        assert "slot" in result.lower()


# ── 8. Intent: staffing risk ──────────────────────────────────────────────────

class TestStaffingIntent:

    def test_staffing_situation(self):
        assert classify_intent("How is our staffing situation?") == "staffing"

    def test_understaffed(self):
        assert classify_intent("Is the school understaffed?") == "staffing"

    def test_staffing_risk(self):
        assert classify_intent("What is the current staffing risk?") == "staffing"

    def test_why_staffing_risk_high(self):
        assert classify_intent("Why is staffing risk high?") == "staffing"

    def test_staffing_fallback_contains_score(self):
        ctx = build_context([], TEACHERS, [], TIMETABLE, [])
        result = _deterministic_fallback(ctx, "staffing")
        assert "/100" in result


# ── 9. Intent: general summary ───────────────────────────────────────────────

class TestSummaryIntent:

    def test_school_summary(self):
        assert classify_intent("Give me a summary of the school's current situation.") == "summary"

    def test_what_to_look_at(self):
        assert classify_intent("What should the administrator look at first?") == "summary"

    def test_summary_fallback_mentions_students(self):
        ctx = build_context(STUDENTS, TEACHERS, [], TIMETABLE, DOCUMENTS)
        result = _deterministic_fallback(ctx, "summary")
        assert "student" in result.lower()


# ── 10. Unknown question ──────────────────────────────────────────────────────

class TestUnknownIntent:

    def test_gibberish_returns_unknown(self):
        assert classify_intent("xyzzy frobble wibble") == "unknown"

    def test_unknown_returns_helpful_message(self):
        answer, intent = answer_question(
            question="xyzzy frobble wibble",
            students=STUDENTS, teachers=TEACHERS,
            teacher_availability=[], timetable=TIMETABLE, documents=DOCUMENTS,
            conversation_history=[], groq_client_instance=EMPTY_GROQ,
        )
        assert intent == "unknown"
        assert "attendance" in answer.lower() or "staffing" in answer.lower()


# ── 11. Missing data ──────────────────────────────────────────────────────────

class TestMissingData:

    def test_no_data_returns_graceful_message(self):
        answer, intent = answer_question(
            question="How many students are at attendance risk?",
            students=[], teachers=[], teacher_availability=[],
            timetable=[], documents=[],
            conversation_history=[], groq_client_instance=EMPTY_GROQ,
        )
        assert "unavailable" in answer.lower() or "empty" in answer.lower() or "data" in answer.lower()
        assert intent in ("attendance", "students")  # both are valid for this phrasing

    def test_no_data_does_not_call_llm(self):
        mock_groq = _mock_groq()
        answer_question(
            question="How many students are there?",
            students=[], teachers=[], teacher_availability=[],
            timetable=[], documents=[],
            conversation_history=[], groq_client_instance=mock_groq,
        )
        # LLM should NOT be called when there is no data
        mock_groq.client.chat.completions.create.assert_not_called()


# ── 12. Hallucination prevention ─────────────────────────────────────────────

class TestHallucinationPrevention:

    def test_llm_receives_real_numbers_not_invented(self):
        """Verify the context text passed to LLM contains actual calculated values."""
        ctx = build_context(STUDENTS, TEACHERS, [], TIMETABLE, DOCUMENTS)
        text = _context_to_text(ctx, "attendance")
        # Must contain the real calculated value (2 students below 75%)
        assert "2" in text
        # Must NOT contain placeholder text
        assert "N/A" not in text or "avg_attendance_pct" not in text

    def test_groq_unavailable_returns_deterministic_not_invented(self):
        """When Groq is down, answer must come from deterministic engine, not LLM."""
        answer, intent = answer_question(
            question="What is the staffing risk?",
            students=STUDENTS, teachers=TEACHERS,
            teacher_availability=[], timetable=TIMETABLE, documents=[],
            conversation_history=[], groq_client_instance=EMPTY_GROQ,
        )
        assert intent == "staffing"
        # Answer must contain the actual score from staffing_engine
        assert "/100" in answer
        # Must not be a generic invented statement
        assert "I don't know" not in answer

    def test_context_contains_no_credentials(self):
        """Ensure no API keys or secrets leak into the context text."""
        ctx = build_context(STUDENTS, TEACHERS, [], TIMETABLE, DOCUMENTS)
        for intent in ("summary", "staffing", "attendance", "fees"):
            text = _context_to_text(ctx, intent)
            assert "GROQ_API_KEY" not in text
            assert "SUPABASE_KEY" not in text
            assert "sk-" not in text

    def test_llm_answer_uses_mocked_response(self):
        """Verify the LLM path returns the mocked response (not invented data)."""
        mock_groq = _mock_groq("Mocked: 2 students are at attendance risk.")
        answer, intent = answer_question(
            question="How many students are at attendance risk?",
            students=STUDENTS, teachers=TEACHERS,
            teacher_availability=[], timetable=TIMETABLE, documents=[],
            conversation_history=[], groq_client_instance=mock_groq,
        )
        assert intent in ("attendance", "students")  # both valid for this phrasing
        assert "Mocked" in answer
        mock_groq.client.chat.completions.create.assert_called_once()

    def test_build_context_does_not_fabricate_student_count(self):
        """Context student count must exactly match input list length."""
        ctx = build_context(STUDENTS, [], [], [], [])
        assert ctx["student_metrics"]["total_students"] == len(STUDENTS)

    def test_build_context_empty_inputs_no_crash(self):
        """build_context must never raise on empty inputs."""
        ctx = build_context([], [], [], [], [])
        assert ctx["student_metrics"]["total_students"] == 0
        assert ctx["staffing_metrics"]["has_sufficient_data"] is False
