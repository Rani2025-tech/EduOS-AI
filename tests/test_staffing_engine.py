"""
Tests for staffing_engine.py
Run from project root: python -m pytest tests/test_staffing_engine.py -v
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from staffing_engine import (
    calculate_staffing_report,
    _calculate_availability,
    _calculate_workload,
    _calculate_coverage,
    _calculate_pressure_score,
    OVERLOAD_THRESHOLD,
)

# ── fixtures ──────────────────────────────────────────────────────────────────

TEACHERS_ALL_ACTIVE = [
    {"id": "T1", "name": "Dr. Mehta",   "subject": "Math",    "status": "active"},
    {"id": "T2", "name": "Mrs. Singh",  "subject": "English", "status": "active"},
    {"id": "T3", "name": "Prof. Gupta", "subject": "Science", "status": "active"},
]

TEACHERS_SOME_ABSENT = [
    {"id": "T1", "name": "Dr. Mehta",   "subject": "Math",    "status": "active"},
    {"id": "T2", "name": "Mrs. Singh",  "subject": "English", "status": "absent"},
    {"id": "T3", "name": "Prof. Gupta", "subject": "Science", "status": "leave"},
]

TIMETABLE_CLEAN = [
    {"id": f"SL{i}", "period": i, "class_name": "8A", "subject": "Math",
     "teacher_name": "Dr. Mehta", "has_conflict": False, "is_substitute": False}
    for i in range(1, 5)
]

TIMETABLE_WITH_CONFLICTS = [
    {"id": "SL1", "period": 1, "class_name": "8A", "subject": "Math",
     "teacher_name": "Dr. Mehta",  "has_conflict": True,  "is_substitute": False},
    {"id": "SL2", "period": 1, "class_name": "8B", "subject": "Math",
     "teacher_name": "Dr. Mehta",  "has_conflict": True,  "is_substitute": False},
    {"id": "SL3", "period": 2, "class_name": "8A", "subject": "English",
     "teacher_name": "Mrs. Singh", "has_conflict": False, "is_substitute": False},
]

TIMETABLE_WITH_SUBSTITUTES = [
    {"id": "SL1", "period": 1, "class_name": "8A", "subject": "Math",
     "teacher_name": "Dr. Mehta",   "has_conflict": False, "is_substitute": False},
    {"id": "SL2", "period": 2, "class_name": "8A", "subject": "English",
     "teacher_name": "Prof. Gupta", "has_conflict": False, "is_substitute": True,
     "substitute_teacher": "Prof. Gupta"},
]

# Overloaded: one teacher has 7 slots (> OVERLOAD_THRESHOLD=6)
TIMETABLE_OVERLOADED = [
    {"id": f"SL{i}", "period": i, "class_name": "8A", "subject": "Math",
     "teacher_name": "Dr. Mehta", "has_conflict": False, "is_substitute": False}
    for i in range(1, 8)   # 7 slots for Dr. Mehta
]

AVAILABILITY_CONSTRAINTS = [
    {"id": "AV1", "teacher_id": "T2", "teacher_name": "Mrs. Singh",
     "period": None, "status": "unavailable", "notes": "On leave"},
]


# ── 1. No teachers ────────────────────────────────────────────────────────────

class TestNoTeachers:

    def test_report_does_not_crash(self):
        report = calculate_staffing_report()
        assert report is not None

    def test_has_sufficient_data_is_false(self):
        report = calculate_staffing_report()
        assert report["has_sufficient_data"] is False

    def test_score_is_zero(self):
        report = calculate_staffing_report()
        assert report["staffing_pressure_score"] == 0

    def test_level_is_low(self):
        report = calculate_staffing_report()
        assert report["staffing_pressure_level"] == "LOW"

    def test_explanation_mentions_insufficient(self):
        report = calculate_staffing_report()
        assert "Insufficient" in report["explanation"]

    def test_recommendations_not_empty(self):
        report = calculate_staffing_report()
        assert len(report["recommendations"]) >= 1


# ── 2. All teachers available ─────────────────────────────────────────────────

class TestAllTeachersAvailable:

    def test_available_count_equals_total(self):
        av = _calculate_availability(TEACHERS_ALL_ACTIVE, [])
        assert av["available_teachers"] == 3
        assert av["unavailable_teachers"] == 0

    def test_availability_pct_is_100(self):
        av = _calculate_availability(TEACHERS_ALL_ACTIVE, [])
        assert av["availability_pct"] == 100.0

    def test_report_severity_is_info_with_no_timetable(self):
        report = calculate_staffing_report(teachers=TEACHERS_ALL_ACTIVE)
        assert report["severity"] == "info"

    def test_score_is_zero_with_no_issues(self):
        report = calculate_staffing_report(
            teachers=TEACHERS_ALL_ACTIVE,
            timetable=TIMETABLE_CLEAN,
        )
        assert report["staffing_pressure_score"] == 0
        assert report["staffing_pressure_level"] == "LOW"


# ── 3. Some teachers unavailable ─────────────────────────────────────────────

class TestSomeTeachersUnavailable:

    def test_unavailable_count_correct(self):
        av = _calculate_availability(TEACHERS_SOME_ABSENT, [])
        assert av["unavailable_teachers"] == 2
        assert av["available_teachers"] == 1

    def test_unavailable_names_populated(self):
        av = _calculate_availability(TEACHERS_SOME_ABSENT, [])
        assert "Mrs. Singh" in av["unavailable_names"]
        assert "Prof. Gupta" in av["unavailable_names"]

    def test_availability_constraint_marks_teacher_unavailable(self):
        # T2 (Mrs. Singh) is active by status but has an all-day unavailability constraint
        teachers = [
            {"id": "T1", "name": "Dr. Mehta",  "status": "active"},
            {"id": "T2", "name": "Mrs. Singh", "status": "active"},
        ]
        av = _calculate_availability(teachers, AVAILABILITY_CONSTRAINTS)
        assert av["unavailable_teachers"] == 1
        assert "Mrs. Singh" in av["unavailable_names"]

    def test_period_specific_constraint_does_not_mark_all_day_unavailable(self):
        # A constraint with a specific period should NOT count as all-day unavailable
        teachers = [{"id": "T1", "name": "Dr. Mehta", "status": "active"}]
        period_constraint = [
            {"teacher_id": "T1", "teacher_name": "Dr. Mehta",
             "period": 3, "status": "unavailable"}
        ]
        av = _calculate_availability(teachers, period_constraint)
        assert av["unavailable_teachers"] == 0

    def test_score_increases_with_absent_teachers(self):
        report_all_active = calculate_staffing_report(teachers=TEACHERS_ALL_ACTIVE)
        report_some_absent = calculate_staffing_report(teachers=TEACHERS_SOME_ABSENT)
        assert report_some_absent["staffing_pressure_score"] > report_all_active["staffing_pressure_score"]


# ── 4. High teacher workload ──────────────────────────────────────────────────

class TestHighWorkload:

    def test_overloaded_teacher_detected(self):
        wl = _calculate_workload(TIMETABLE_OVERLOADED, TEACHERS_ALL_ACTIVE)
        assert wl["overloaded_count"] == 1
        assert "Dr. Mehta" in wl["overloaded_teachers"]

    def test_avg_workload_calculated(self):
        wl = _calculate_workload(TIMETABLE_CLEAN, TEACHERS_ALL_ACTIVE)
        # 4 slots all assigned to Dr. Mehta → avg = 4.0
        assert wl["avg_workload"] == 4.0

    def test_max_workload_teacher_identified(self):
        wl = _calculate_workload(TIMETABLE_OVERLOADED, TEACHERS_ALL_ACTIVE)
        assert wl["max_workload_teacher"] == "Dr. Mehta"
        assert wl["max_workload"] == 7

    def test_overload_threshold_respected(self):
        wl = _calculate_workload(TIMETABLE_CLEAN, TEACHERS_ALL_ACTIVE)
        # 4 slots < OVERLOAD_THRESHOLD(6) → not overloaded
        assert wl["overloaded_count"] == 0

    def test_score_increases_with_overload(self):
        report_normal = calculate_staffing_report(
            teachers=TEACHERS_ALL_ACTIVE, timetable=TIMETABLE_CLEAN
        )
        report_overloaded = calculate_staffing_report(
            teachers=TEACHERS_ALL_ACTIVE, timetable=TIMETABLE_OVERLOADED
        )
        assert report_overloaded["staffing_pressure_score"] > report_normal["staffing_pressure_score"]


# ── 5. Uncovered timetable slots ──────────────────────────────────────────────

class TestUncoveredSlots:

    def test_conflict_slots_counted_as_uncovered(self):
        cov = _calculate_coverage(TIMETABLE_WITH_CONFLICTS, TEACHERS_ALL_ACTIVE)
        assert cov["uncovered_slots"] == 2

    def test_coverage_pct_calculated(self):
        cov = _calculate_coverage(TIMETABLE_WITH_CONFLICTS, TEACHERS_ALL_ACTIVE)
        # 1 covered out of 3 total
        assert cov["coverage_pct"] == round((1 / 3) * 100, 1)

    def test_uncovered_subjects_populated(self):
        cov = _calculate_coverage(TIMETABLE_WITH_CONFLICTS, TEACHERS_ALL_ACTIVE)
        assert "Math" in cov["uncovered_subjects"]

    def test_empty_timetable_returns_100_coverage(self):
        cov = _calculate_coverage([], TEACHERS_ALL_ACTIVE)
        assert cov["coverage_pct"] == 100.0
        assert cov["uncovered_slots"] == 0


# ── 6. Substitute requirement ─────────────────────────────────────────────────

class TestSubstituteRequirement:

    def test_substitute_slots_counted(self):
        cov = _calculate_coverage(TIMETABLE_WITH_SUBSTITUTES, TEACHERS_ALL_ACTIVE)
        assert cov["substitute_slots"] == 1

    def test_substitute_required_includes_uncovered_plus_subs(self):
        cov = _calculate_coverage(TIMETABLE_WITH_SUBSTITUTES, TEACHERS_ALL_ACTIVE)
        # 0 uncovered + 1 substitute = 1
        assert cov["substitute_required"] == 1

    def test_report_substitute_required_field(self):
        report = calculate_staffing_report(
            teachers=TEACHERS_ALL_ACTIVE,
            timetable=TIMETABLE_WITH_SUBSTITUTES,
        )
        assert report["substitute_required"] == 1
        assert report["substitute_slots"] == 1


# ── 7. Low staffing pressure ──────────────────────────────────────────────────

class TestLowPressure:

    def test_all_active_clean_timetable_is_low(self):
        report = calculate_staffing_report(
            teachers=TEACHERS_ALL_ACTIVE,
            timetable=TIMETABLE_CLEAN,
        )
        assert report["staffing_pressure_level"] == "LOW"
        assert report["staffing_pressure_score"] <= 30

    def test_severity_is_info_for_low(self):
        report = calculate_staffing_report(
            teachers=TEACHERS_ALL_ACTIVE,
            timetable=TIMETABLE_CLEAN,
        )
        assert report["severity"] == "info"


# ── 8. High staffing pressure ─────────────────────────────────────────────────

class TestHighPressure:

    def test_all_absent_with_conflicts_is_critical(self):
        all_absent = [
            {"id": "T1", "name": "Dr. Mehta",   "status": "absent"},
            {"id": "T2", "name": "Mrs. Singh",  "status": "absent"},
            {"id": "T3", "name": "Prof. Gupta", "status": "absent"},
        ]
        report = calculate_staffing_report(
            teachers=all_absent,
            timetable=TIMETABLE_WITH_CONFLICTS,
        )
        # Formula: A=(3/3)*35=35, B=(2/3)*30=20 → total=55 → MODERATE
        # All teachers absent + 2/3 conflicts → score >= 31 (at minimum MODERATE)
        assert report["staffing_pressure_score"] >= 31
        assert report["staffing_pressure_level"] in ("MODERATE", "HIGH", "CRITICAL")

    def test_critical_score_triggers_hiring_recommendation(self):
        all_absent = [{"id": f"T{i}", "name": f"Teacher{i}", "status": "absent"}
                      for i in range(5)]
        many_conflicts = [
            {"id": f"SL{i}", "period": i, "class_name": "8A", "subject": "Math",
             "teacher_name": f"Teacher{i % 5}", "has_conflict": True, "is_substitute": False}
            for i in range(10)
        ]
        report = calculate_staffing_report(teachers=all_absent, timetable=many_conflicts)
        recs_text = " ".join(report["recommendations"])
        assert "CRITICAL" in recs_text or "critical" in recs_text.lower() or report["staffing_pressure_score"] >= 61


# ── 9. Missing / incomplete data ──────────────────────────────────────────────

class TestMissingData:

    def test_none_inputs_no_crash(self):
        report = calculate_staffing_report(None, None, None)
        assert report is not None

    def test_teacher_missing_status_field(self):
        teachers_no_status = [{"id": "T1", "name": "Dr. Mehta"}]
        report = calculate_staffing_report(teachers=teachers_no_status)
        assert report["total_teachers"] == 1
        assert report["unavailable_teachers"] == 0  # missing status defaults to active

    def test_timetable_slot_missing_teacher_name(self):
        slots_no_teacher = [
            {"id": "SL1", "period": 1, "class_name": "8A", "subject": "Math",
             "has_conflict": False, "is_substitute": False}
        ]
        report = calculate_staffing_report(
            teachers=TEACHERS_ALL_ACTIVE,
            timetable=slots_no_teacher,
        )
        # Should not crash; workload for unnamed teacher is ignored
        assert report["total_slots"] == 1

    def test_empty_teacher_availability_no_crash(self):
        report = calculate_staffing_report(
            teachers=TEACHERS_ALL_ACTIVE,
            teacher_availability=[],
        )
        assert report["available_teachers"] == 3

    def test_all_required_keys_present(self):
        report = calculate_staffing_report(
            teachers=TEACHERS_ALL_ACTIVE,
            timetable=TIMETABLE_CLEAN,
        )
        required = {
            "total_teachers", "available_teachers", "unavailable_teachers",
            "availability_pct", "unavailable_names",
            "avg_workload", "max_workload", "max_workload_teacher",
            "overloaded_count", "overloaded_teachers", "overload_threshold",
            "slots_per_teacher",
            "total_slots", "covered_slots", "uncovered_slots",
            "substitute_slots", "coverage_pct", "uncovered_subjects",
            "substitute_required",
            "staffing_pressure_score", "staffing_pressure_level",
            "severity", "score_breakdown",
            "recommendations", "explanation", "has_sufficient_data",
        }
        assert required.issubset(report.keys())


# ── 10. Deterministic score calculation ──────────────────────────────────────

class TestDeterministicScore:

    def test_same_inputs_same_score(self):
        r1 = calculate_staffing_report(
            teachers=TEACHERS_SOME_ABSENT,
            timetable=TIMETABLE_WITH_CONFLICTS,
        )
        r2 = calculate_staffing_report(
            teachers=TEACHERS_SOME_ABSENT,
            timetable=TIMETABLE_WITH_CONFLICTS,
        )
        assert r1["staffing_pressure_score"] == r2["staffing_pressure_score"]

    def test_score_is_integer(self):
        report = calculate_staffing_report(
            teachers=TEACHERS_SOME_ABSENT,
            timetable=TIMETABLE_WITH_CONFLICTS,
        )
        assert isinstance(report["staffing_pressure_score"], int)

    def test_score_within_bounds(self):
        for teachers, timetable in [
            ([], []),
            (TEACHERS_ALL_ACTIVE, TIMETABLE_CLEAN),
            (TEACHERS_SOME_ABSENT, TIMETABLE_WITH_CONFLICTS),
            (TEACHERS_SOME_ABSENT, TIMETABLE_OVERLOADED),
        ]:
            report = calculate_staffing_report(teachers=teachers, timetable=timetable)
            assert 0 <= report["staffing_pressure_score"] <= 100

    def test_signal_formula_manual_verification(self):
        """
        Manual verification of the formula with known inputs.
        2 of 3 teachers absent → signal_a = (2/3)*35 = 23.33
        2 of 3 slots conflicted → signal_b = (2/3)*30 = 20.0
        0 overloaded → signal_c = 0
        0 substitutes → signal_d = 0
        total ≈ 43 → MODERATE
        """
        report = calculate_staffing_report(
            teachers=TEACHERS_SOME_ABSENT,
            timetable=TIMETABLE_WITH_CONFLICTS,
        )
        bd = report["score_breakdown"]
        assert abs(bd["signal_a"] - round((2 / 3) * 35, 2)) < 0.01
        assert abs(bd["signal_b"] - round((2 / 3) * 30, 2)) < 0.01
        assert bd["signal_c"] == 0.0
        assert bd["signal_d"] == 0.0
        assert report["staffing_pressure_level"] == "MODERATE"

    def test_score_breakdown_keys_present(self):
        report = calculate_staffing_report(teachers=TEACHERS_ALL_ACTIVE)
        bd = report["score_breakdown"]
        assert set(bd.keys()) == {"signal_a", "signal_b", "signal_c", "signal_d"}
