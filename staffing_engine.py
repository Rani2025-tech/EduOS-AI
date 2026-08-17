"""
EduOS AI — Smart Staffing Engine
==================================
Deterministic, explainable workforce-planning analysis.
No machine learning. No fabricated data. No LLM calls.

Accepts plain Python lists from session state or any other source.
Returns a single structured StaffingReport dict.

─────────────────────────────────────────────────────────────
STAFFING PRESSURE SCORE FORMULA  (0 – 100, integer)
─────────────────────────────────────────────────────────────
Four independent signals, each capped at its maximum weight:

  Signal A — Unavailability ratio          weight 35
    = (unavailable_teachers / total_teachers) * 35
    Rationale: the most direct capacity signal.

  Signal B — Timetable conflict ratio      weight 30
    = (conflict_slots / total_slots) * 30
    Rationale: conflicts are the visible symptom of staffing gaps.

  Signal C — Workload imbalance            weight 20
    = (overloaded_teachers / total_teachers) * 20
    Overloaded = teacher slot count > OVERLOAD_THRESHOLD (default 6 slots).
    Rationale: overloaded teachers are a burnout and quality risk.

  Signal D — Substitute dependency ratio   weight 15
    = (substitute_slots / total_slots) * 15
    Rationale: high substitute usage signals structural understaffing.

  Total = A + B + C + D  (capped at 100)

Pressure levels:
   0 – 30  → LOW
  31 – 60  → MODERATE
  61 – 80  → HIGH
  81 – 100 → CRITICAL

When total_teachers == 0 or total_slots == 0 the affected signals
default to 0 (not an error) and the report notes insufficient data.
─────────────────────────────────────────────────────────────
"""

from typing import List, Dict, Any, Tuple
from collections import defaultdict

# ── Configurable thresholds (documented, not magic numbers) ──────────────────

# A teacher with more than this many timetable slots is considered overloaded.
# Typical Indian school day = 6–8 periods; 6 is a reasonable upper bound.
OVERLOAD_THRESHOLD: int = 6

# Pressure level boundaries
PRESSURE_LOW      = (0,  30)
PRESSURE_MODERATE = (31, 60)
PRESSURE_HIGH     = (61, 80)
PRESSURE_CRITICAL = (81, 100)


# ── helpers ───────────────────────────────────────────────────────────────────

def _safe_str(value, default: str = "") -> str:
    return str(value).strip() if value is not None else default


def _pressure_level(score: int) -> str:
    if score <= PRESSURE_LOW[1]:
        return "LOW"
    if score <= PRESSURE_MODERATE[1]:
        return "MODERATE"
    if score <= PRESSURE_HIGH[1]:
        return "HIGH"
    return "CRITICAL"


def _pressure_severity(score: int) -> str:
    """Maps pressure level to the existing severity vocabulary used by analytics_engine."""
    if score <= PRESSURE_LOW[1]:
        return "info"
    if score <= PRESSURE_MODERATE[1]:
        return "warning"
    return "critical"


# ── Sub-calculations (each independently testable) ───────────────────────────

def _calculate_availability(
    teachers: List[Dict[str, Any]],
    teacher_availability: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Returns teacher availability breakdown.
    A teacher is unavailable if:
      - their status field is 'absent' or 'leave', OR
      - they have at least one teacher_availability record with status='unavailable'
        and no period specified (meaning all-day unavailability).
    """
    total = len(teachers)
    if total == 0:
        return {
            "total_teachers": 0,
            "available_teachers": 0,
            "unavailable_teachers": 0,
            "availability_pct": 0.0,
            "unavailable_names": [],
        }

    # Build set of teacher names/IDs with all-day unavailability constraints
    constrained_ids: set = set()
    constrained_names: set = set()
    for av in teacher_availability:
        if av.get("status") == "unavailable" and av.get("period") is None:
            if av.get("teacher_id"):
                constrained_ids.add(_safe_str(av["teacher_id"]))
            if av.get("teacher_name"):
                constrained_names.add(_safe_str(av["teacher_name"]).lower())

    unavailable = []
    for t in teachers:
        status = _safe_str(t.get("status", "active")).lower()
        t_id   = _safe_str(t.get("id", ""))
        t_name = _safe_str(t.get("name", "")).lower()
        if (
            status in ("absent", "leave")
            or t_id in constrained_ids
            or t_name in constrained_names
        ):
            unavailable.append(t.get("name", t_id))

    unavailable_count = len(unavailable)
    available_count   = total - unavailable_count
    availability_pct  = round((available_count / total) * 100, 1)

    return {
        "total_teachers": total,
        "available_teachers": available_count,
        "unavailable_teachers": unavailable_count,
        "availability_pct": availability_pct,
        "unavailable_names": unavailable,
    }


def _calculate_workload(
    timetable: List[Dict[str, Any]],
    teachers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Counts timetable slots per teacher name.
    Uses teacher_name field from timetable slots (what the solver writes).
    """
    if not timetable:
        return {
            "slots_per_teacher": {},
            "avg_workload": 0.0,
            "max_workload": 0,
            "max_workload_teacher": None,
            "overloaded_teachers": [],
            "overloaded_count": 0,
            "overload_threshold": OVERLOAD_THRESHOLD,
        }

    slot_counts: Dict[str, int] = defaultdict(int)
    for slot in timetable:
        name = _safe_str(slot.get("teacher_name") or slot.get("substitute_teacher"))
        if name:
            slot_counts[name] += 1

    if not slot_counts:
        return {
            "slots_per_teacher": {},
            "avg_workload": 0.0,
            "max_workload": 0,
            "max_workload_teacher": None,
            "overloaded_teachers": [],
            "overloaded_count": 0,
            "overload_threshold": OVERLOAD_THRESHOLD,
        }

    counts = list(slot_counts.values())
    avg_workload = round(sum(counts) / len(counts), 1)
    max_workload = max(counts)
    max_teacher  = max(slot_counts, key=lambda k: slot_counts[k])
    overloaded   = [name for name, cnt in slot_counts.items() if cnt > OVERLOAD_THRESHOLD]

    return {
        "slots_per_teacher": dict(slot_counts),
        "avg_workload": avg_workload,
        "max_workload": max_workload,
        "max_workload_teacher": max_teacher,
        "overloaded_teachers": overloaded,
        "overloaded_count": len(overloaded),
        "overload_threshold": OVERLOAD_THRESHOLD,
    }


def _calculate_coverage(
    timetable: List[Dict[str, Any]],
    teachers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Analyses timetable slot coverage:
    - conflict slots (has_conflict=True) are uncovered
    - substitute slots (is_substitute=True) are covered but fragile
    """
    if not timetable:
        return {
            "total_slots": 0,
            "covered_slots": 0,
            "uncovered_slots": 0,
            "substitute_slots": 0,
            "coverage_pct": 100.0,
            "uncovered_subjects": [],
            "substitute_required": 0,
        }

    total          = len(timetable)
    conflict_slots = [s for s in timetable if s.get("has_conflict")]
    sub_slots      = [s for s in timetable if s.get("is_substitute")]
    uncovered      = len(conflict_slots)
    covered        = total - uncovered
    coverage_pct   = round((covered / total) * 100, 1) if total else 100.0

    uncovered_subjects = list({
        _safe_str(s.get("subject")) for s in conflict_slots if s.get("subject")
    })

    # Substitute requirement = slots where primary teacher is absent/unavailable
    # (already resolved as substitute) + still-conflicted slots
    substitute_required = len(sub_slots) + uncovered

    return {
        "total_slots": total,
        "covered_slots": covered,
        "uncovered_slots": uncovered,
        "substitute_slots": len(sub_slots),
        "coverage_pct": coverage_pct,
        "uncovered_subjects": uncovered_subjects,
        "substitute_required": substitute_required,
    }


def _calculate_pressure_score(
    availability: Dict[str, Any],
    workload: Dict[str, Any],
    coverage: Dict[str, Any],
) -> Tuple[int, Dict[str, float]]:
    """
    Computes the staffing pressure score (0–100) from four signals.
    Returns (score, signal_breakdown).

    Formula (see module docstring):
      A = unavailability ratio  × 35
      B = conflict ratio        × 30
      C = overload ratio        × 20
      D = substitute ratio      × 15
    """
    total_teachers = availability["total_teachers"]
    total_slots    = coverage["total_slots"]

    # Signal A — unavailability
    if total_teachers > 0:
        a = (availability["unavailable_teachers"] / total_teachers) * 35
    else:
        a = 0.0

    # Signal B — timetable conflicts
    if total_slots > 0:
        b = (coverage["uncovered_slots"] / total_slots) * 30
    else:
        b = 0.0

    # Signal C — workload overload
    if total_teachers > 0:
        c = (workload["overloaded_count"] / total_teachers) * 20
    else:
        c = 0.0

    # Signal D — substitute dependency
    if total_slots > 0:
        d = (coverage["substitute_slots"] / total_slots) * 15
    else:
        d = 0.0

    raw   = a + b + c + d
    score = min(100, round(raw))

    return score, {"signal_a": round(a, 2), "signal_b": round(b, 2),
                   "signal_c": round(c, 2), "signal_d": round(d, 2)}


def _build_recommendations(
    availability: Dict[str, Any],
    workload: Dict[str, Any],
    coverage: Dict[str, Any],
    score: int,
) -> List[str]:
    """
    Generates ordered, evidence-based recommendations.
    Each recommendation is only emitted when the underlying signal exists.
    """
    recs: List[str] = []

    # Uncovered slots — highest urgency
    if coverage["uncovered_slots"] > 0:
        subj_str = (
            f" ({', '.join(coverage['uncovered_subjects'][:3])})"
            if coverage["uncovered_subjects"] else ""
        )
        recs.append(
            f"Resolve {coverage['uncovered_slots']} uncovered timetable slot(s){subj_str} "
            "by running the OR-Tools Solver in the Smart Timetable Engine tab."
        )

    # Absent teachers
    if availability["unavailable_teachers"] > 0:
        names = ", ".join(availability["unavailable_names"][:3])
        suffix = " and others" if len(availability["unavailable_names"]) > 3 else ""
        recs.append(
            f"Arrange cover for {availability['unavailable_teachers']} unavailable teacher(s): "
            f"{names}{suffix}."
        )

    # Overloaded teachers
    if workload["overloaded_count"] > 0:
        names = ", ".join(workload["overloaded_teachers"][:3])
        recs.append(
            f"Review workload for {workload['overloaded_count']} overloaded teacher(s) "
            f"({names}) — each exceeds {OVERLOAD_THRESHOLD} slots."
        )

    # High substitute dependency
    if coverage["substitute_slots"] > 0 and score >= 31:
        recs.append(
            f"{coverage['substitute_slots']} slot(s) are currently covered by substitutes. "
            "If this is recurring, consider reviewing permanent staffing for affected subjects."
        )

    # Critical pressure — hiring signal
    if score >= 81:
        recs.append(
            "Staffing pressure is CRITICAL. Review whether additional permanent staff are required. "
            "Current data supports this concern but is not sufficient to specify exact hiring numbers."
        )
    elif score >= 61:
        recs.append(
            "Staffing pressure is HIGH. Monitor daily and escalate if unavailability persists "
            "beyond 3 consecutive school days."
        )

    # No issues found
    if not recs:
        recs.append(
            "No immediate staffing action required. "
            "Continue monitoring teacher availability and timetable coverage."
        )

    return recs


# ── Public API ────────────────────────────────────────────────────────────────

def calculate_staffing_report(
    teachers: List[Dict[str, Any]] = None,
    teacher_availability: List[Dict[str, Any]] = None,
    timetable: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Main entry point. Returns a single StaffingReport dict.

    Works with any combination of empty/None inputs — never raises.

    Return shape:
    {
        # availability
        "total_teachers":          int,
        "available_teachers":      int,
        "unavailable_teachers":    int,
        "availability_pct":        float,
        "unavailable_names":       List[str],

        # workload
        "avg_workload":            float,   # slots per teacher
        "max_workload":            int,
        "max_workload_teacher":    str | None,
        "overloaded_count":        int,
        "overloaded_teachers":     List[str],
        "overload_threshold":      int,
        "slots_per_teacher":       Dict[str, int],

        # coverage
        "total_slots":             int,
        "covered_slots":           int,
        "uncovered_slots":         int,
        "substitute_slots":        int,
        "coverage_pct":            float,
        "uncovered_subjects":      List[str],
        "substitute_required":     int,

        # pressure score
        "staffing_pressure_score": int,     # 0–100
        "staffing_pressure_level": str,     # LOW / MODERATE / HIGH / CRITICAL
        "severity":                str,     # info / warning / critical
        "score_breakdown":         Dict,    # signal_a … signal_d

        # narrative
        "recommendations":         List[str],
        "explanation":             str,
        "has_sufficient_data":     bool,
    }
    """
    teachers             = teachers or []
    teacher_availability = teacher_availability or []
    timetable            = timetable or []

    availability = _calculate_availability(teachers, teacher_availability)
    workload     = _calculate_workload(timetable, teachers)
    coverage     = _calculate_coverage(timetable, teachers)
    score, breakdown = _calculate_pressure_score(availability, workload, coverage)
    level        = _pressure_level(score)
    severity     = _pressure_severity(score)
    recs         = _build_recommendations(availability, workload, coverage, score)

    has_sufficient_data = bool(teachers)  # minimum requirement for a meaningful report

    # Build a one-paragraph plain-English explanation
    if not has_sufficient_data:
        explanation = (
            "Insufficient data to generate a staffing forecast. "
            "Add teacher records via the Teacher Availability & Roster tab."
        )
    else:
        avail_str = (
            f"{availability['available_teachers']} of {availability['total_teachers']} "
            f"teachers are available ({availability['availability_pct']}%)."
        )
        workload_str = (
            f"Average teaching load is {workload['avg_workload']} slot(s) per teacher."
            if workload["avg_workload"] > 0 else "No timetable workload data available."
        )
        coverage_str = (
            f"Timetable coverage is {coverage['coverage_pct']}% "
            f"({coverage['uncovered_slots']} uncovered slot(s))."
            if coverage["total_slots"] > 0 else "No timetable data available."
        )
        explanation = (
            f"Projected staffing pressure based on current workload and availability. "
            f"{avail_str} {workload_str} {coverage_str} "
            f"Overall staffing risk score: {score}/100 ({level})."
        )

    return {
        # availability
        "total_teachers":          availability["total_teachers"],
        "available_teachers":      availability["available_teachers"],
        "unavailable_teachers":    availability["unavailable_teachers"],
        "availability_pct":        availability["availability_pct"],
        "unavailable_names":       availability["unavailable_names"],
        # workload
        "avg_workload":            workload["avg_workload"],
        "max_workload":            workload["max_workload"],
        "max_workload_teacher":    workload["max_workload_teacher"],
        "overloaded_count":        workload["overloaded_count"],
        "overloaded_teachers":     workload["overloaded_teachers"],
        "overload_threshold":      workload["overload_threshold"],
        "slots_per_teacher":       workload["slots_per_teacher"],
        # coverage
        "total_slots":             coverage["total_slots"],
        "covered_slots":           coverage["covered_slots"],
        "uncovered_slots":         coverage["uncovered_slots"],
        "substitute_slots":        coverage["substitute_slots"],
        "coverage_pct":            coverage["coverage_pct"],
        "uncovered_subjects":      coverage["uncovered_subjects"],
        "substitute_required":     coverage["substitute_required"],
        # pressure
        "staffing_pressure_score": score,
        "staffing_pressure_level": level,
        "severity":                severity,
        "score_breakdown":         breakdown,
        # narrative
        "recommendations":         recs,
        "explanation":             explanation,
        "has_sufficient_data":     has_sufficient_data,
    }
