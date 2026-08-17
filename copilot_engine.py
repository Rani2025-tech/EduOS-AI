"""
EduOS AI — Copilot Engine
==========================
Grounded natural-language interface over EduOS-AI's intelligence layer.

Architecture:
  User question
    → intent classification (keyword-weighted scoring, no brittle exact match)
    → structured context retrieval (analytics_engine + staffing_engine, no duplication)
    → Groq LLM call with grounded system prompt
    → natural-language answer

Hallucination controls:
  - LLM receives ONLY pre-calculated facts; it cannot invent numbers.
  - System prompt explicitly forbids inventing statistics.
  - If data is absent, a deterministic "unavailable" message is returned
    before the LLM is ever called.
  - No credentials are ever included in context or responses.

Pure module: no Streamlit, no DB, no side effects.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from analytics_engine import (
    calculate_attendance_insight,
    calculate_fee_insight,
    calculate_academic_insight,
    calculate_document_insight,
    calculate_timetable_insight,
)
from staffing_engine import calculate_staffing_report

logger = logging.getLogger("EduOS_CopilotEngine")
logger.setLevel(logging.INFO)

# ── Intent taxonomy ───────────────────────────────────────────────────────────
# Each intent maps to a list of weighted keyword signals.
# Score = sum of weights for matched tokens. Highest score wins.
# Ties broken by order (first defined wins).

_INTENT_SIGNALS: Dict[str, List[Tuple[str, int]]] = {
    "students": [
        ("student", 10), ("students", 10), ("enrolled", 8), ("enrollment", 8),
        ("how many student", 12), ("total student", 12),
    ],
    "attendance": [
        ("attendance", 10), ("present", 6), ("75%", 8),
        ("below 75", 10), ("attendance risk", 15), ("low attendance", 12),
        ("attendance rate", 10), ("skipping", 6), ("truant", 6),
        ("at attendance", 12),
    ],
    "fees": [
        ("fee", 10), ("fees", 10), ("overdue", 8), ("pending fee", 12),
        ("fee collection", 12), ("unpaid", 8), ("payment", 6),
        ("outstanding", 8), ("fee rate", 10), ("tuition", 6),
    ],
    "academic": [
        ("gpa", 10), ("academic", 10), ("grade", 8), ("performance", 8),
        ("marks", 6), ("score", 6), ("below 2.5", 10), ("underperform", 10),
        ("academic risk", 12), ("low gpa", 12), ("failing", 8),
    ],
    "documents": [
        ("document", 10), ("documents", 10), ("pending review", 12),
        ("validation", 8), ("review queue", 10), ("doc", 6),
        ("form", 6), ("uploaded", 6), ("admission form", 8),
    ],
    "timetable": [
        ("timetable", 10), ("schedule", 8), ("conflict", 10),
        ("clash", 10), ("slot", 6), ("period", 6), ("class schedule", 10),
        ("timetable conflict", 12), ("double booked", 10),
    ],
    "teacher_availability": [
        ("teacher available", 12), ("teacher unavailable", 12),
        ("absent teacher", 15), ("teacher absent", 15),
        ("how many teacher", 10), ("available teacher", 12),
        ("teacher on leave", 12), ("teacher status", 8),
        ("who is absent", 10), ("teacher", 5),
        ("teachers are absent", 15), ("which teacher", 10),
    ],
    "teacher_workload": [
        ("workload", 12), ("overloaded", 12), ("overload", 12),
        ("teaching load", 12), ("heaviest load", 12), ("most classes", 10),
        ("too many class", 10), ("too many slot", 10), ("busiest teacher", 10),
        ("who teaches most", 10), ("max workload", 10),
    ],
    "staffing": [
        ("staffing", 12), ("understaffed", 12), ("staffing risk", 12),
        ("staffing situation", 12), ("staffing pressure", 12),
        ("staff shortage", 10), ("hiring", 8), ("workforce", 8),
        ("substitute", 8), ("coverage", 8), ("staffing score", 12),
    ],
    "summary": [
        ("summary", 12), ("overview", 10), ("situation", 8),
        ("overall", 8), ("what should", 10), ("look at first", 10),
        ("school status", 10), ("give me a", 6), ("how is the school", 12),
        ("school operations", 10), ("everything", 6), ("all issues", 8),
    ],
}


def classify_intent(question: str) -> str:
    """
    Classifies the user's question into one of the supported intents.
    Uses weighted keyword scoring — not brittle exact matching.
    Returns 'unknown' if no intent scores above zero.
    """
    lower = question.lower()
    scores: Dict[str, int] = {intent: 0 for intent in _INTENT_SIGNALS}

    for intent, signals in _INTENT_SIGNALS.items():
        for phrase, weight in signals:
            if phrase in lower:
                scores[intent] += weight

    best_intent = max(scores, key=lambda k: scores[k])
    return best_intent if scores[best_intent] > 0 else "unknown"


# ── Structured context builder ────────────────────────────────────────────────

def build_context(
    students: List[Dict[str, Any]],
    teachers: List[Dict[str, Any]],
    teacher_availability: List[Dict[str, Any]],
    timetable: List[Dict[str, Any]],
    documents: List[Dict[str, Any]],
    existing_insights: Optional[List[Dict[str, Any]]] = None,
    existing_staffing_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Builds a structured context dict from real application data.
    Reuses existing calculated insights/staffing report when available
    to avoid duplicate computation.
    Never fabricates data.
    """
    # Reuse pre-calculated insights if available, otherwise calculate fresh
    if existing_insights and len(existing_insights) >= 5:
        att_ins  = next((i for i in existing_insights if i["category"] == "attendance"), None)
        fee_ins  = next((i for i in existing_insights if i["category"] == "fees"), None)
        aca_ins  = next((i for i in existing_insights if i["category"] == "academic"), None)
        doc_ins  = next((i for i in existing_insights if i["category"] == "documents"), None)
        tt_ins   = next((i for i in existing_insights if i["category"] == "timetable"), None)
    else:
        att_ins  = calculate_attendance_insight(students)
        fee_ins  = calculate_fee_insight(students)
        aca_ins  = calculate_academic_insight(students)
        doc_ins  = calculate_document_insight(documents)
        tt_ins   = calculate_timetable_insight(timetable, teachers, teacher_availability)

    sr = existing_staffing_report or calculate_staffing_report(
        teachers=teachers,
        teacher_availability=teacher_availability,
        timetable=timetable,
    )

    return {
        "student_metrics": {
            "total_students": len(students),
            "has_data": bool(students),
        },
        "attendance_metrics": att_ins.get("data", {}) if att_ins else {},
        "attendance_insight": {
            "severity": att_ins.get("severity") if att_ins else "info",
            "metric": att_ins.get("metric") if att_ins else "No data",
            "forecast": att_ins.get("forecast") if att_ins else "No data",
            "recommendation": att_ins.get("recommendation") if att_ins else "",
        },
        "fee_metrics": fee_ins.get("data", {}) if fee_ins else {},
        "fee_insight": {
            "severity": fee_ins.get("severity") if fee_ins else "info",
            "metric": fee_ins.get("metric") if fee_ins else "No data",
            "forecast": fee_ins.get("forecast") if fee_ins else "No data",
            "recommendation": fee_ins.get("recommendation") if fee_ins else "",
        },
        "academic_metrics": aca_ins.get("data", {}) if aca_ins else {},
        "academic_insight": {
            "severity": aca_ins.get("severity") if aca_ins else "info",
            "metric": aca_ins.get("metric") if aca_ins else "No data",
            "forecast": aca_ins.get("forecast") if aca_ins else "No data",
            "recommendation": aca_ins.get("recommendation") if aca_ins else "",
        },
        "document_metrics": doc_ins.get("data", {}) if doc_ins else {},
        "document_insight": {
            "severity": doc_ins.get("severity") if doc_ins else "info",
            "metric": doc_ins.get("metric") if doc_ins else "No data",
            "forecast": doc_ins.get("forecast") if doc_ins else "No data",
            "recommendation": doc_ins.get("recommendation") if doc_ins else "",
        },
        "timetable_metrics": tt_ins.get("data", {}) if tt_ins else {},
        "timetable_insight": {
            "severity": tt_ins.get("severity") if tt_ins else "info",
            "metric": tt_ins.get("metric") if tt_ins else "No data",
            "forecast": tt_ins.get("forecast") if tt_ins else "No data",
            "recommendation": tt_ins.get("recommendation") if tt_ins else "",
        },
        "staffing_metrics": {
            "total_teachers":          sr.get("total_teachers", 0),
            "available_teachers":      sr.get("available_teachers", 0),
            "unavailable_teachers":    sr.get("unavailable_teachers", 0),
            "unavailable_names":       sr.get("unavailable_names", []),
            "availability_pct":        sr.get("availability_pct", 0.0),
            "avg_workload":            sr.get("avg_workload", 0.0),
            "max_workload":            sr.get("max_workload", 0),
            "max_workload_teacher":    sr.get("max_workload_teacher"),
            "overloaded_count":        sr.get("overloaded_count", 0),
            "overloaded_teachers":     sr.get("overloaded_teachers", []),
            "overload_threshold":      sr.get("overload_threshold", 6),
            "slots_per_teacher":       sr.get("slots_per_teacher", {}),
            "total_slots":             sr.get("total_slots", 0),
            "uncovered_slots":         sr.get("uncovered_slots", 0),
            "substitute_slots":        sr.get("substitute_slots", 0),
            "coverage_pct":            sr.get("coverage_pct", 100.0),
            "staffing_pressure_score": sr.get("staffing_pressure_score", 0),
            "staffing_pressure_level": sr.get("staffing_pressure_level", "LOW"),
            "recommendations":         sr.get("recommendations", []),
            "explanation":             sr.get("explanation", ""),
            "has_sufficient_data":     sr.get("has_sufficient_data", False),
        },
    }


# ── Context → focused text for LLM ───────────────────────────────────────────

def _context_to_text(context: Dict[str, Any], intent: str) -> str:
    """
    Converts the structured context into a focused plain-text block
    relevant to the detected intent. Keeps the prompt tight.
    """
    sm  = context["student_metrics"]
    am  = context["attendance_metrics"]
    ai  = context["attendance_insight"]
    fm  = context["fee_metrics"]
    fi  = context["fee_insight"]
    acm = context["academic_metrics"]
    aci = context["academic_insight"]
    dm  = context["document_metrics"]
    di  = context["document_insight"]
    tm  = context["timetable_metrics"]
    ti  = context["timetable_insight"]
    stm = context["staffing_metrics"]

    lines: List[str] = []

    # Always include student count — it's a universal anchor
    lines.append(f"TOTAL ENROLLED STUDENTS: {sm['total_students']}")

    if intent in ("students", "summary"):
        lines.append(f"STUDENT DATA AVAILABLE: {sm['has_data']}")

    if intent in ("attendance", "summary"):
        lines.append(f"\nATTENDANCE:")
        lines.append(f"  Severity: {ai['severity'].upper()}")
        lines.append(f"  Metric: {ai['metric']}")
        lines.append(f"  Finding: {ai['forecast']}")
        lines.append(f"  Recommendation: {ai['recommendation']}")
        if am:
            lines.append(f"  Average attendance: {am.get('avg_attendance_pct', 'N/A')}%")
            lines.append(f"  Students below 75% threshold: {am.get('below_threshold_count', 'N/A')}")
            at_risk = am.get("at_risk_students", [])
            if at_risk:
                lines.append(f"  At-risk student names: {', '.join(at_risk)}")

    if intent in ("fees", "summary"):
        lines.append(f"\nFEE COLLECTION:")
        lines.append(f"  Severity: {fi['severity'].upper()}")
        lines.append(f"  Metric: {fi['metric']}")
        lines.append(f"  Finding: {fi['forecast']}")
        lines.append(f"  Recommendation: {fi['recommendation']}")
        if fm:
            lines.append(f"  Paid: {fm.get('paid_count', 'N/A')}")
            lines.append(f"  Pending: {fm.get('pending_count', 'N/A')}")
            lines.append(f"  Overdue: {fm.get('overdue_count', 'N/A')}")
            lines.append(f"  Total outstanding: ₹{fm.get('total_amount_due', 0):,}")
            lines.append(f"  Collection rate: {fm.get('collection_pct', 'N/A')}%")

    if intent in ("academic", "summary"):
        lines.append(f"\nACADEMIC PERFORMANCE:")
        lines.append(f"  Severity: {aci['severity'].upper()}")
        lines.append(f"  Metric: {aci['metric']}")
        lines.append(f"  Finding: {aci['forecast']}")
        lines.append(f"  Recommendation: {aci['recommendation']}")
        if acm:
            lines.append(f"  Average GPA: {acm.get('avg_gpa', 'N/A')}/4.0")
            lines.append(f"  Students below 2.5 GPA: {acm.get('below_threshold_count', 'N/A')}")

    if intent in ("documents", "summary"):
        lines.append(f"\nDOCUMENT QUEUE:")
        lines.append(f"  Severity: {di['severity'].upper()}")
        lines.append(f"  Metric: {di['metric']}")
        lines.append(f"  Finding: {di['forecast']}")
        lines.append(f"  Recommendation: {di['recommendation']}")
        if dm:
            lines.append(f"  Total documents: {dm.get('total', 'N/A')}")
            lines.append(f"  Pending review: {dm.get('pending_review', 'N/A')}")
            lines.append(f"  Validation errors: {dm.get('with_validation_errors', 'N/A')}")
            lines.append(f"  Committed: {dm.get('committed', 'N/A')}")

    if intent in ("timetable", "summary"):
        lines.append(f"\nTIMETABLE:")
        lines.append(f"  Severity: {ti['severity'].upper()}")
        lines.append(f"  Metric: {ti['metric']}")
        lines.append(f"  Finding: {ti['forecast']}")
        lines.append(f"  Recommendation: {ti['recommendation']}")
        if tm:
            lines.append(f"  Total slots: {tm.get('total_slots', 'N/A')}")
            lines.append(f"  Conflict slots: {tm.get('conflict_count', 'N/A')}")
            lines.append(f"  Absent teachers: {tm.get('absent_teacher_count', 'N/A')}")

    if intent in ("teacher_availability", "teacher_workload", "staffing", "summary"):
        lines.append(f"\nSTAFFING & TEACHERS:")
        lines.append(f"  Data available: {stm['has_sufficient_data']}")
        lines.append(f"  Total teachers: {stm['total_teachers']}")
        lines.append(f"  Available teachers: {stm['available_teachers']}")
        lines.append(f"  Unavailable teachers: {stm['unavailable_teachers']}")
        if stm["unavailable_names"]:
            lines.append(f"  Unavailable names: {', '.join(stm['unavailable_names'])}")
        lines.append(f"  Availability: {stm['availability_pct']}%")
        lines.append(f"  Staffing pressure score: {stm['staffing_pressure_score']}/100")
        lines.append(f"  Staffing pressure level: {stm['staffing_pressure_level']}")
        lines.append(f"  Explanation: {stm['explanation']}")

    if intent in ("teacher_workload", "staffing", "summary"):
        lines.append(f"  Average workload: {stm['avg_workload']} slots/teacher")
        lines.append(f"  Max workload: {stm['max_workload']} slots ({stm['max_workload_teacher']})")
        lines.append(f"  Overloaded teachers (>{stm['overload_threshold']} slots): {stm['overloaded_count']}")
        if stm["overloaded_teachers"]:
            lines.append(f"  Overloaded names: {', '.join(stm['overloaded_teachers'])}")
        lines.append(f"  Uncovered timetable slots: {stm['uncovered_slots']}")
        lines.append(f"  Substitute slots: {stm['substitute_slots']}")
        lines.append(f"  Coverage: {stm['coverage_pct']}%")
        if stm["recommendations"]:
            lines.append(f"  Staffing recommendations:")
            for rec in stm["recommendations"]:
                lines.append(f"    - {rec}")

    if intent == "teacher_workload" and stm["slots_per_teacher"]:
        lines.append(f"\nWORKLOAD PER TEACHER:")
        for name, slots in sorted(stm["slots_per_teacher"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {name}: {slots} slot(s)")

    return "\n".join(lines)


# ── Groq call ─────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are EduOS-AI's administrative Copilot — an AI assistant for school administrators.

The following information has been retrieved from the school's live operational data.
Answer ONLY using the provided information.
If specific information is not provided, say it is unavailable — do not guess or invent it.
Never invent student counts, teacher counts, attendance percentages, fee amounts, \
staffing scores, timetable conflicts, names, or recommendations based on unavailable data.

Response format:
- For simple factual questions: give a short direct answer (1–3 sentences).
- For complex questions: use this structure:
    [Direct answer]

    Key findings:
    - ...

    Recommended action:
    - ...

Keep responses concise and administrator-friendly. Do not repeat the data verbatim.\
"""


def _call_groq_copilot(
    context_text: str,
    question: str,
    conversation_history: List[Dict[str, str]],
    groq_client_instance: Any,
) -> str:
    """
    Calls Groq with the grounded context + conversation history.
    Returns the LLM's response string.
    Raises RuntimeError if Groq is unavailable.
    """
    if not groq_client_instance.is_available():
        raise RuntimeError("Groq API key is missing or client is unavailable.")

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]

    # Inject grounded context as the first user turn
    messages.append({
        "role": "user",
        "content": f"CURRENT SCHOOL DATA:\n{context_text}"
    })
    messages.append({
        "role": "assistant",
        "content": "Understood. I have the current school data. Please ask your question."
    })

    # Append recent conversation history (last 6 turns = 3 exchanges)
    for turn in conversation_history[-6:]:
        messages.append(turn)

    # Append the current question
    messages.append({"role": "user", "content": question})

    try:
        response = groq_client_instance.client.chat.completions.create(
            model=groq_client_instance.model,
            messages=messages,
            temperature=0.2,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq copilot call failed: {e}")
        raise RuntimeError(f"Groq API error: {e}")


# ── Public API ────────────────────────────────────────────────────────────────

def answer_question(
    question: str,
    students: List[Dict[str, Any]],
    teachers: List[Dict[str, Any]],
    teacher_availability: List[Dict[str, Any]],
    timetable: List[Dict[str, Any]],
    documents: List[Dict[str, Any]],
    conversation_history: List[Dict[str, str]],
    groq_client_instance: Any,
    existing_insights: Optional[List[Dict[str, Any]]] = None,
    existing_staffing_report: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """
    Main entry point for the Copilot.

    Returns:
        (answer_text, intent)

    Grounding guarantee:
        - All numerical facts come from analytics_engine / staffing_engine.
        - The LLM only receives pre-calculated facts; it cannot invent numbers.
        - If no data exists, returns a deterministic message without calling the LLM.
    """
    intent = classify_intent(question)
    logger.info(f"Copilot intent: {intent} | question: {question[:80]}")

    # Build structured context from real data
    context = build_context(
        students=students,
        teachers=teachers,
        teacher_availability=teacher_availability,
        timetable=timetable,
        documents=documents,
        existing_insights=existing_insights,
        existing_staffing_report=existing_staffing_report,
    )

    # Grounding check: if no data at all, return deterministic message
    has_any_data = (
        bool(students) or bool(teachers) or bool(timetable) or bool(documents)
    )
    if not has_any_data and intent != "unknown":
        return (
            "I don't have enough current data to answer that reliably. "
            "The school database appears to be empty or disconnected. "
            "Please add data via the AI Document Reader or Teacher Roster tabs, "
            "or connect Supabase in the sidebar.",
            intent,
        )

    if intent == "unknown":
        return (
            "I'm not sure what you're asking about. "
            "I can answer questions about students, attendance, fees, academic performance, "
            "documents, timetable conflicts, teacher availability, workload, and staffing. "
            "Try: \"How is our staffing situation?\" or \"Are there timetable conflicts?\"",
            intent,
        )

    # Convert context to focused text for the LLM
    context_text = _context_to_text(context, intent)

    # Call Groq with grounded context
    if not groq_client_instance.is_available():
        # Groq unavailable — return deterministic answer from context
        return _deterministic_fallback(context, intent), intent

    try:
        answer = _call_groq_copilot(
            context_text=context_text,
            question=question,
            conversation_history=conversation_history,
            groq_client_instance=groq_client_instance,
        )
        return answer, intent
    except RuntimeError as e:
        logger.warning(f"Groq unavailable, using deterministic fallback: {e}")
        return _deterministic_fallback(context, intent), intent


def _deterministic_fallback(context: Dict[str, Any], intent: str) -> str:
    """
    Returns a grounded plain-text answer without the LLM.
    Used when Groq is unavailable. All numbers come from context.
    """
    sm  = context["student_metrics"]
    ai  = context["attendance_insight"]
    fi  = context["fee_insight"]
    aci = context["academic_insight"]
    di  = context["document_insight"]
    ti  = context["timetable_insight"]
    stm = context["staffing_metrics"]
    am  = context["attendance_metrics"]
    fm  = context["fee_metrics"]

    if intent == "students":
        return f"There are {sm['total_students']} enrolled student(s) in the system."

    if intent == "attendance":
        below = am.get("below_threshold_count", "N/A")
        avg   = am.get("avg_attendance_pct", "N/A")
        return (
            f"Attendance status: {ai['severity'].upper()}. "
            f"{ai['forecast']} "
            f"Average attendance: {avg}%. Students below 75%: {below}."
        )

    if intent == "fees":
        overdue = fm.get("overdue_count", "N/A")
        total   = fm.get("total_amount_due", 0)
        rate    = fm.get("collection_pct", "N/A")
        return (
            f"Fee collection: {fi['severity'].upper()}. "
            f"{fi['forecast']} "
            f"Collection rate: {rate}%. Overdue: {overdue}. Outstanding: ₹{total:,}."
        )

    if intent == "academic":
        return f"Academic performance: {aci['severity'].upper()}. {aci['forecast']}"

    if intent == "documents":
        return f"Document queue: {di['severity'].upper()}. {di['forecast']}"

    if intent == "timetable":
        conflicts = context["timetable_metrics"].get("conflict_count", "N/A")
        return (
            f"Timetable status: {ti['severity'].upper()}. "
            f"{ti['forecast']} Conflicts: {conflicts}."
        )

    if intent == "teacher_availability":
        return (
            f"{stm['available_teachers']} of {stm['total_teachers']} teacher(s) are available "
            f"({stm['availability_pct']}%). "
            f"Unavailable: {stm['unavailable_teachers']}."
            + (f" Names: {', '.join(stm['unavailable_names'])}." if stm["unavailable_names"] else "")
        )

    if intent == "teacher_workload":
        overloaded = stm["overloaded_teachers"]
        return (
            f"Average teaching load: {stm['avg_workload']} slots/teacher. "
            f"Max: {stm['max_workload']} slots ({stm['max_workload_teacher']}). "
            f"Overloaded teachers (>{stm['overload_threshold']} slots): {stm['overloaded_count']}."
            + (f" Names: {', '.join(overloaded)}." if overloaded else "")
        )

    if intent == "staffing":
        return (
            f"Staffing pressure: {stm['staffing_pressure_level']} "
            f"(score {stm['staffing_pressure_score']}/100). "
            f"{stm['explanation']}"
        )

    if intent == "summary":
        issues = []
        if context["attendance_metrics"].get("below_threshold_count", 0):
            issues.append(f"{context['attendance_metrics']['below_threshold_count']} student(s) at attendance risk")
        if fm.get("overdue_count", 0):
            issues.append(f"{fm['overdue_count']} overdue fee(s)")
        if context["timetable_metrics"].get("conflict_count", 0):
            issues.append(f"{context['timetable_metrics']['conflict_count']} timetable conflict(s)")
        if stm["unavailable_teachers"]:
            issues.append(f"{stm['unavailable_teachers']} teacher(s) unavailable")
        if context["document_metrics"].get("pending_review", 0):
            issues.append(f"{context['document_metrics']['pending_review']} document(s) pending review")

        if not issues:
            return (
                f"School operations look healthy. "
                f"{sm['total_students']} student(s) enrolled. "
                f"Staffing pressure: {stm['staffing_pressure_level']}. No critical issues detected."
            )
        return (
            f"School operations summary — {sm['total_students']} student(s) enrolled. "
            f"Active issues: {'; '.join(issues)}. "
            f"Staffing pressure: {stm['staffing_pressure_level']} ({stm['staffing_pressure_score']}/100)."
        )

    return "I don't have enough current data to answer that reliably."
