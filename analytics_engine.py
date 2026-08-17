"""
EduOS AI — Analytics Engine
============================
Pure calculation layer. No Streamlit, no database, no side effects.
Accepts plain Python lists (from session state or anywhere else).
Returns a list of insight dicts compatible with the existing `insights`
table schema and the existing UI rendering conventions.

Each insight dict:
{
    "id":             str   — stable deterministic ID
    "category":       str   — "attendance" | "fees" | "academic" | "documents" | "timetable"
    "title":          str   — short display title
    "severity":       str   — "info" | "warning" | "critical"
    "metric":         str   — human-readable key metric value
    "trend":          str   — direction label e.g. "declining" | "stable" | "improving"
    "forecast":       str   — one-sentence description of the finding
    "recommendation": str   — one-sentence actionable recommendation
    "confidence":     int   — 0-100 (rule-based = 100, statistical = lower)
    "data":           dict  — raw numbers used in the calculation (for tests / copilot)
}
"""

import datetime
from typing import List, Dict, Any

# ── helpers ───────────────────────────────────────────────────────────────────

def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _ts() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── 1. Attendance Risk ────────────────────────────────────────────────────────

def calculate_attendance_insight(students: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates attendance risk across all students.
    Threshold: 75% (standard Indian school regulation).
    """
    if not students:
        return {
            "id": "INS-ATT-001",
            "category": "attendance",
            "title": "Attendance Risk Analysis",
            "severity": "info",
            "metric": "No data",
            "trend": "unknown",
            "forecast": "No attendance data available yet. Enroll students to begin tracking.",
            "recommendation": "Add student records via the AI Document Reader.",
            "confidence": 100,
            "data": {},
        }

    total = len(students)
    attendance_values = [_safe_float(s.get("attendance_pct"), 100.0) for s in students]
    avg_att = round(sum(attendance_values) / total, 1)
    below_threshold = [s for s in students if _safe_float(s.get("attendance_pct"), 100.0) < 75.0]
    below_count = len(below_threshold)
    below_pct = round((below_count / total) * 100, 1)

    if below_count == 0:
        severity = "info"
        trend = "stable"
        forecast = (
            f"All {total} students are above the 75% attendance threshold. "
            f"School average attendance is {avg_att}%."
        )
        recommendation = "Continue monitoring. No immediate action required."
    elif below_pct <= 20:
        severity = "warning"
        trend = "declining"
        forecast = (
            f"{below_count} of {total} students ({below_pct}%) are below the 75% attendance threshold. "
            f"School average is {avg_att}%."
        )
        recommendation = (
            f"Review attendance records for {below_count} at-risk student(s) and notify parents."
        )
    else:
        severity = "critical"
        trend = "declining"
        forecast = (
            f"{below_count} of {total} students ({below_pct}%) are critically below the 75% threshold. "
            f"School average attendance has dropped to {avg_att}%."
        )
        recommendation = (
            "Immediate administrative review required. Issue attendance warnings and schedule "
            "parent meetings for all students below threshold."
        )

    return {
        "id": "INS-ATT-001",
        "category": "attendance",
        "title": "Attendance Risk Analysis",
        "severity": severity,
        "metric": f"{avg_att}% avg · {below_count} at-risk",
        "trend": trend,
        "forecast": forecast,
        "recommendation": recommendation,
        "confidence": 100,
        "data": {
            "total_students": total,
            "avg_attendance_pct": avg_att,
            "below_threshold_count": below_count,
            "below_threshold_pct": below_pct,
            "at_risk_students": [s.get("name", "Unknown") for s in below_threshold],
        },
    }


# ── 2. Fee Collection ─────────────────────────────────────────────────────────

def calculate_fee_insight(students: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates fee collection status across all students.
    """
    if not students:
        return {
            "id": "INS-FEE-001",
            "category": "fees",
            "title": "Fee Collection Status",
            "severity": "info",
            "metric": "No data",
            "trend": "unknown",
            "forecast": "No fee data available yet.",
            "recommendation": "Add student records via the AI Document Reader.",
            "confidence": 100,
            "data": {},
        }

    students_with_fee = [s for s in students if s.get("fee_status")]
    total = len(students_with_fee)

    if total == 0:
        return {
            "id": "INS-FEE-001",
            "category": "fees",
            "title": "Fee Collection Status",
            "severity": "info",
            "metric": "No fee data",
            "trend": "unknown",
            "forecast": "No fee status information found in student records.",
            "recommendation": "Ensure fee_status is populated when enrolling students.",
            "confidence": 100,
            "data": {},
        }

    paid_count    = sum(1 for s in students_with_fee if s.get("fee_status") == "paid")
    pending_count = sum(1 for s in students_with_fee if s.get("fee_status") == "pending")
    overdue_count = sum(1 for s in students_with_fee if s.get("fee_status") == "overdue")
    total_due     = sum(_safe_int(s.get("fee_amount_due", 0)) for s in students_with_fee)
    collection_pct = round((paid_count / total) * 100, 1)

    if overdue_count == 0 and pending_count == 0:
        severity = "info"
        trend = "stable"
        forecast = f"100% fee collection achieved. All {total} students have paid fees."
        recommendation = "No action required. Fee collection is complete."
    elif overdue_count > 0:
        severity = "critical" if overdue_count > total * 0.2 else "warning"
        trend = "declining"
        forecast = (
            f"{overdue_count} student(s) have overdue fees totalling ₹{total_due:,}. "
            f"Collection rate is {collection_pct}% ({paid_count}/{total} paid)."
        )
        recommendation = (
            f"Send fee overdue notices to {overdue_count} student(s) immediately. "
            "Escalate to administration if unpaid after 7 days."
        )
    else:
        severity = "warning"
        trend = "stable"
        forecast = (
            f"{pending_count} student(s) have pending fees. "
            f"Current collection rate: {collection_pct}% ({paid_count}/{total} paid)."
        )
        recommendation = f"Follow up with {pending_count} student(s) with pending fee status."

    return {
        "id": "INS-FEE-001",
        "category": "fees",
        "title": "Fee Collection Status",
        "severity": severity,
        "metric": f"{collection_pct}% collected · ₹{total_due:,} outstanding",
        "trend": trend,
        "forecast": forecast,
        "recommendation": recommendation,
        "confidence": 100,
        "data": {
            "total_students": total,
            "paid_count": paid_count,
            "pending_count": pending_count,
            "overdue_count": overdue_count,
            "total_amount_due": total_due,
            "collection_pct": collection_pct,
        },
    }


# ── 3. Academic / GPA Performance ────────────────────────────────────────────

def calculate_academic_insight(students: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates academic performance distribution from GPA data.
    GPA threshold for concern: below 2.5 on a 4.0 scale.
    """
    if not students:
        return {
            "id": "INS-ACA-001",
            "category": "academic",
            "title": "Academic Performance Trend",
            "severity": "info",
            "metric": "No data",
            "trend": "unknown",
            "forecast": "No academic data available yet.",
            "recommendation": "Add student records to begin academic tracking.",
            "confidence": 100,
            "data": {},
        }

    students_with_gpa = [
        s for s in students
        if s.get("gpa") is not None and _safe_float(s.get("gpa"), -1.0) >= 0.0
    ]

    if not students_with_gpa:
        return {
            "id": "INS-ACA-001",
            "category": "academic",
            "title": "Academic Performance Trend",
            "severity": "info",
            "metric": "Insufficient data",
            "trend": "unknown",
            "forecast": "Insufficient academic data available for this analysis.",
            "recommendation": "Ensure GPA data is populated in student records.",
            "confidence": 100,
            "data": {"students_with_gpa": 0},
        }

    gpa_values = [_safe_float(s.get("gpa"), 0.0) for s in students_with_gpa]
    avg_gpa = round(sum(gpa_values) / len(gpa_values), 2)
    below_threshold = [s for s in students_with_gpa if _safe_float(s.get("gpa"), 4.0) < 2.5]
    below_count = len(below_threshold)
    total = len(students_with_gpa)

    top_performers = sorted(students_with_gpa, key=lambda s: _safe_float(s.get("gpa"), 0.0), reverse=True)
    top_name = top_performers[0].get("name", "N/A") if top_performers else "N/A"
    top_gpa  = _safe_float(top_performers[0].get("gpa"), 0.0) if top_performers else 0.0

    if below_count == 0:
        severity = "info"
        trend = "stable"
        forecast = (
            f"School average GPA is {avg_gpa}/4.0 across {total} students. "
            f"No students are below the 2.5 GPA threshold."
        )
        recommendation = f"Top performer: {top_name} ({top_gpa}/4.0). Maintain current academic standards."
    elif below_count <= total * 0.15:
        severity = "warning"
        trend = "declining"
        forecast = (
            f"{below_count} of {total} students are below the 2.5 GPA threshold. "
            f"School average GPA: {avg_gpa}/4.0."
        )
        recommendation = (
            f"Schedule academic support sessions for {below_count} underperforming student(s)."
        )
    else:
        severity = "critical"
        trend = "declining"
        forecast = (
            f"{below_count} of {total} students ({round(below_count/total*100,1)}%) are below 2.5 GPA. "
            f"School average has dropped to {avg_gpa}/4.0."
        )
        recommendation = (
            "Initiate school-wide academic intervention programme. "
            "Review teaching effectiveness and curriculum delivery."
        )

    return {
        "id": "INS-ACA-001",
        "category": "academic",
        "title": "Academic Performance Trend",
        "severity": severity,
        "metric": f"{avg_gpa}/4.0 avg GPA · {below_count} below threshold",
        "trend": trend,
        "forecast": forecast,
        "recommendation": recommendation,
        "confidence": 90,
        "data": {
            "total_students_with_gpa": total,
            "avg_gpa": avg_gpa,
            "below_threshold_count": below_count,
            "top_performer_name": top_name,
            "top_performer_gpa": top_gpa,
        },
    }


# ── 4. Document Processing ────────────────────────────────────────────────────

def calculate_document_insight(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyses the document audit queue for pending/failed records.
    """
    if not documents:
        return {
            "id": "INS-DOC-001",
            "category": "documents",
            "title": "Document Processing Queue",
            "severity": "info",
            "metric": "No documents",
            "trend": "stable",
            "forecast": "No documents have been processed yet.",
            "recommendation": "Upload admission forms or fee receipts via the AI Document Reader.",
            "confidence": 100,
            "data": {},
        }

    total         = len(documents)
    pending       = sum(1 for d in documents if d.get("status") == "review_required")
    committed     = sum(1 for d in documents if d.get("status") == "committed")
    rejected      = sum(1 for d in documents if d.get("status") == "rejected")
    with_errors   = sum(1 for d in documents if d.get("validation_errors"))

    if pending == 0 and with_errors == 0:
        severity = "info"
        trend = "stable"
        forecast = (
            f"All {total} document(s) have been processed. "
            f"{committed} committed, {rejected} rejected."
        )
        recommendation = "Document queue is clear. No action required."
    elif with_errors > 0:
        severity = "warning"
        trend = "stable"
        forecast = (
            f"{pending} document(s) pending human review. "
            f"{with_errors} document(s) have validation errors requiring attention."
        )
        recommendation = (
            f"Review {with_errors} document(s) with validation errors in the AI Document Reader tab."
        )
    else:
        severity = "warning"
        trend = "stable"
        forecast = (
            f"{pending} document(s) are awaiting human review before student enrollment. "
            f"Total processed: {total}."
        )
        recommendation = (
            f"Open the AI Document Reader tab and confirm {pending} pending document(s)."
        )

    return {
        "id": "INS-DOC-001",
        "category": "documents",
        "title": "Document Processing Queue",
        "severity": severity,
        "metric": f"{pending} pending · {with_errors} errors · {committed} committed",
        "trend": trend,
        "forecast": forecast,
        "recommendation": recommendation,
        "confidence": 100,
        "data": {
            "total": total,
            "pending_review": pending,
            "committed": committed,
            "rejected": rejected,
            "with_validation_errors": with_errors,
        },
    }


# ── 5. Timetable / Staffing Signal ───────────────────────────────────────────

def calculate_timetable_insight(
    timetable: List[Dict[str, Any]],
    teachers: List[Dict[str, Any]],
    teacher_availability: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculates timetable health and staffing availability signals.
    """
    if not timetable:
        return {
            "id": "INS-TT-001",
            "category": "timetable",
            "title": "Timetable & Staffing Signal",
            "severity": "info",
            "metric": "No timetable",
            "trend": "unknown",
            "forecast": "No timetable data available yet.",
            "recommendation": "Upload a timetable via the Smart Timetable Engine tab.",
            "confidence": 100,
            "data": {},
        }

    total_slots     = len(timetable)
    conflict_slots  = [s for s in timetable if s.get("has_conflict")]
    substitute_slots = [s for s in timetable if s.get("is_substitute")]
    conflict_count  = len(conflict_slots)
    substitute_count = len(substitute_slots)

    absent_teachers = [t for t in teachers if t.get("status") in ("absent", "leave")]
    unavailable_constraints = [
        a for a in teacher_availability if a.get("status") == "unavailable"
    ]

    if conflict_count == 0 and not absent_teachers:
        severity = "info"
        trend = "stable"
        forecast = (
            f"Timetable is fully optimised. {total_slots} slots scheduled with zero conflicts. "
            f"{substitute_count} substitute assignment(s) active."
        )
        recommendation = "No timetable action required. All teachers are available."
    elif conflict_count > 0:
        severity = "critical" if conflict_count > total_slots * 0.1 else "warning"
        trend = "declining"
        forecast = (
            f"{conflict_count} of {total_slots} timetable slot(s) have unresolved conflicts. "
            f"{len(absent_teachers)} teacher(s) currently marked absent."
        )
        recommendation = (
            "Run the OR-Tools Solver in the Smart Timetable Engine tab to auto-assign substitutes."
        )
    else:
        severity = "warning"
        trend = "stable"
        forecast = (
            f"{len(absent_teachers)} teacher(s) are absent. "
            f"{substitute_count} substitute(s) have been assigned. "
            f"Timetable has {conflict_count} unresolved conflict(s)."
        )
        recommendation = (
            f"Monitor {len(absent_teachers)} absent teacher(s). "
            "Re-run the solver if new absences are added."
        )

    return {
        "id": "INS-TT-001",
        "category": "timetable",
        "title": "Timetable & Staffing Signal",
        "severity": severity,
        "metric": f"{conflict_count} conflicts · {len(absent_teachers)} absent teachers",
        "trend": trend,
        "forecast": forecast,
        "recommendation": recommendation,
        "confidence": 100,
        "data": {
            "total_slots": total_slots,
            "conflict_count": conflict_count,
            "substitute_count": substitute_count,
            "absent_teacher_count": len(absent_teachers),
            "unavailable_constraints": len(unavailable_constraints),
        },
    }


# ── Public API ────────────────────────────────────────────────────────────────

def generate_all_insights(
    students: List[Dict[str, Any]] = None,
    teachers: List[Dict[str, Any]] = None,
    teacher_availability: List[Dict[str, Any]] = None,
    timetable: List[Dict[str, Any]] = None,
    documents: List[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Runs all 5 analytics calculations and returns a list of insight dicts.
    Safe to call with any combination of empty/None inputs.
    """
    students            = students or []
    teachers            = teachers or []
    teacher_availability = teacher_availability or []
    timetable           = timetable or []
    documents           = documents or []

    return [
        calculate_attendance_insight(students),
        calculate_fee_insight(students),
        calculate_academic_insight(students),
        calculate_document_insight(documents),
        calculate_timetable_insight(timetable, teachers, teacher_availability),
    ]
