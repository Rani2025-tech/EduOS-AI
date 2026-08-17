"""
Tests for analytics_engine.py
Run from project root: python -m pytest tests/test_analytics_engine.py -v
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from analytics_engine import (
    calculate_attendance_insight,
    calculate_fee_insight,
    calculate_academic_insight,
    calculate_document_insight,
    calculate_timetable_insight,
    generate_all_insights,
)

# ── fixtures ──────────────────────────────────────────────────────────────────

STUDENTS_HEALTHY = [
    {"id": "S1", "name": "Aarav",  "attendance_pct": 92.0, "fee_status": "paid",    "fee_amount_due": 0,     "gpa": 3.8},
    {"id": "S2", "name": "Priya",  "attendance_pct": 88.0, "fee_status": "paid",    "fee_amount_due": 0,     "gpa": 3.5},
    {"id": "S3", "name": "Rohan",  "attendance_pct": 95.0, "fee_status": "pending", "fee_amount_due": 5000,  "gpa": 3.2},
]

STUDENTS_AT_RISK = [
    {"id": "S1", "name": "Aarav",  "attendance_pct": 60.0, "fee_status": "overdue", "fee_amount_due": 15000, "gpa": 2.1},
    {"id": "S2", "name": "Priya",  "attendance_pct": 72.0, "fee_status": "overdue", "fee_amount_due": 12000, "gpa": 1.8},
    {"id": "S3", "name": "Rohan",  "attendance_pct": 90.0, "fee_status": "paid",    "fee_amount_due": 0,     "gpa": 3.9},
]

TEACHERS = [
    {"id": "T1", "name": "Dr. Mehta",  "subject": "Math",    "status": "active"},
    {"id": "T2", "name": "Mrs. Singh", "subject": "English", "status": "absent"},
]

TIMETABLE_CLEAN = [
    {"id": "SL1", "period": 1, "class_name": "8A", "subject": "Math",    "teacher_name": "Dr. Mehta",  "has_conflict": False, "is_substitute": False},
    {"id": "SL2", "period": 2, "class_name": "8A", "subject": "English", "teacher_name": "Mrs. Singh", "has_conflict": False, "is_substitute": True},
]

TIMETABLE_CONFLICT = [
    {"id": "SL1", "period": 1, "class_name": "8A", "subject": "Math",    "teacher_name": "Dr. Mehta",  "has_conflict": True,  "is_substitute": False},
    {"id": "SL2", "period": 1, "class_name": "8B", "subject": "Math",    "teacher_name": "Dr. Mehta",  "has_conflict": True,  "is_substitute": False},
]

DOCUMENTS_PENDING = [
    {"id": "D1", "filename": "form1.pdf", "status": "review_required", "validation_errors": None},
    {"id": "D2", "filename": "form2.pdf", "status": "committed",       "validation_errors": None},
    {"id": "D3", "filename": "form3.pdf", "status": "review_required", "validation_errors": "Missing parent_phone"},
]


# ── 1. Attendance Risk ────────────────────────────────────────────────────────

class TestAttendanceInsight:

    def test_healthy_students_returns_info(self):
        result = calculate_attendance_insight(STUDENTS_HEALTHY)
        assert result["severity"] == "info"
        assert result["data"]["below_threshold_count"] == 0
        assert result["data"]["avg_attendance_pct"] == 91.7

    def test_at_risk_students_returns_warning_or_critical(self):
        result = calculate_attendance_insight(STUDENTS_AT_RISK)
        assert result["severity"] in ("warning", "critical")
        assert result["data"]["below_threshold_count"] == 2
        assert "Aarav" in result["data"]["at_risk_students"]
        assert "Priya" in result["data"]["at_risk_students"]

    def test_empty_students_returns_info_no_crash(self):
        result = calculate_attendance_insight([])
        assert result["severity"] == "info"
        assert "No attendance data" in result["forecast"]
        assert result["data"] == {}

    def test_metric_string_is_populated(self):
        result = calculate_attendance_insight(STUDENTS_HEALTHY)
        assert "%" in result["metric"]

    def test_all_below_threshold_is_critical(self):
        all_low = [
            {"id": f"S{i}", "name": f"Student{i}", "attendance_pct": 50.0}
            for i in range(10)
        ]
        result = calculate_attendance_insight(all_low)
        assert result["severity"] == "critical"
        assert result["data"]["below_threshold_count"] == 10


# ── 2. Fee Collection ─────────────────────────────────────────────────────────

class TestFeeInsight:

    def test_all_paid_returns_info(self):
        paid_students = [
            {"id": "S1", "fee_status": "paid", "fee_amount_due": 0},
            {"id": "S2", "fee_status": "paid", "fee_amount_due": 0},
        ]
        result = calculate_fee_insight(paid_students)
        assert result["severity"] == "info"
        assert result["data"]["collection_pct"] == 100.0

    def test_overdue_fees_returns_warning_or_critical(self):
        result = calculate_fee_insight(STUDENTS_AT_RISK)
        assert result["severity"] in ("warning", "critical")
        assert result["data"]["overdue_count"] == 2
        assert result["data"]["total_amount_due"] == 27000

    def test_empty_students_returns_info_no_crash(self):
        result = calculate_fee_insight([])
        assert result["severity"] == "info"
        assert "No fee data" in result["forecast"]

    def test_pending_fees_returns_warning(self):
        result = calculate_fee_insight(STUDENTS_HEALTHY)
        # 1 pending, 0 overdue → warning
        assert result["severity"] == "warning"
        assert result["data"]["pending_count"] == 1

    def test_total_amount_due_calculation(self):
        result = calculate_fee_insight(STUDENTS_AT_RISK)
        assert result["data"]["total_amount_due"] == 15000 + 12000


# ── 3. Academic / GPA ─────────────────────────────────────────────────────────

class TestAcademicInsight:

    def test_healthy_gpa_returns_info(self):
        result = calculate_academic_insight(STUDENTS_HEALTHY)
        assert result["severity"] == "info"
        assert result["data"]["below_threshold_count"] == 0

    def test_low_gpa_returns_warning_or_critical(self):
        result = calculate_academic_insight(STUDENTS_AT_RISK)
        assert result["severity"] in ("warning", "critical")
        assert result["data"]["below_threshold_count"] == 2

    def test_empty_students_no_crash(self):
        result = calculate_academic_insight([])
        assert result["severity"] == "info"
        assert "No academic data" in result["forecast"]

    def test_missing_gpa_field_no_crash(self):
        students_no_gpa = [
            {"id": "S1", "name": "Aarav", "attendance_pct": 90.0},
            {"id": "S2", "name": "Priya", "attendance_pct": 85.0},
        ]
        result = calculate_academic_insight(students_no_gpa)
        assert result["severity"] == "info"
        assert "Insufficient" in result["forecast"]

    def test_none_gpa_values_no_crash(self):
        students_none_gpa = [
            {"id": "S1", "name": "Aarav", "gpa": None},
            {"id": "S2", "name": "Priya", "gpa": None},
        ]
        result = calculate_academic_insight(students_none_gpa)
        assert "Insufficient" in result["forecast"]

    def test_avg_gpa_calculation(self):
        result = calculate_academic_insight(STUDENTS_HEALTHY)
        assert result["data"]["avg_gpa"] == round((3.8 + 3.5 + 3.2) / 3, 2)


# ── 4. Document Processing ────────────────────────────────────────────────────

class TestDocumentInsight:

    def test_pending_documents_returns_warning(self):
        result = calculate_document_insight(DOCUMENTS_PENDING)
        assert result["severity"] == "warning"
        assert result["data"]["pending_review"] == 2
        assert result["data"]["with_validation_errors"] == 1

    def test_empty_documents_returns_info(self):
        result = calculate_document_insight([])
        assert result["severity"] == "info"
        assert "No documents" in result["forecast"]

    def test_all_committed_returns_info(self):
        committed = [
            {"id": "D1", "status": "committed", "validation_errors": None},
            {"id": "D2", "status": "committed", "validation_errors": None},
        ]
        result = calculate_document_insight(committed)
        assert result["severity"] == "info"
        assert result["data"]["pending_review"] == 0


# ── 5. Timetable / Staffing Signal ───────────────────────────────────────────

class TestTimetableInsight:

    def test_clean_timetable_returns_info(self):
        result = calculate_timetable_insight(TIMETABLE_CLEAN, TEACHERS, [])
        # 1 absent teacher → warning
        assert result["severity"] in ("info", "warning")
        assert result["data"]["conflict_count"] == 0

    def test_conflict_timetable_returns_warning_or_critical(self):
        result = calculate_timetable_insight(TIMETABLE_CONFLICT, TEACHERS, [])
        assert result["severity"] in ("warning", "critical")
        assert result["data"]["conflict_count"] == 2

    def test_empty_timetable_returns_info_no_crash(self):
        result = calculate_timetable_insight([], [], [])
        assert result["severity"] == "info"
        assert "No timetable data" in result["forecast"]

    def test_absent_teacher_counted(self):
        result = calculate_timetable_insight(TIMETABLE_CLEAN, TEACHERS, [])
        assert result["data"]["absent_teacher_count"] == 1

    def test_no_teachers_no_crash(self):
        result = calculate_timetable_insight(TIMETABLE_CLEAN, [], [])
        assert result["data"]["conflict_count"] == 0


# ── 6. generate_all_insights ──────────────────────────────────────────────────

class TestGenerateAllInsights:

    def test_returns_five_insights(self):
        result = generate_all_insights(
            students=STUDENTS_HEALTHY,
            teachers=TEACHERS,
            timetable=TIMETABLE_CLEAN,
            documents=DOCUMENTS_PENDING,
        )
        assert len(result) == 5

    def test_all_none_inputs_no_crash(self):
        result = generate_all_insights()
        assert len(result) == 5
        for ins in result:
            assert ins["severity"] == "info"

    def test_each_insight_has_required_keys(self):
        result = generate_all_insights(students=STUDENTS_AT_RISK)
        required_keys = {"id", "category", "title", "severity", "metric",
                         "trend", "forecast", "recommendation", "confidence", "data"}
        for ins in result:
            assert required_keys.issubset(ins.keys()), f"Missing keys in {ins['id']}"

    def test_categories_are_distinct(self):
        result = generate_all_insights()
        categories = [ins["category"] for ins in result]
        assert len(set(categories)) == 5
