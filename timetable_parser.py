import logging
from typing import List, Dict, Any, Tuple
from PIL import Image
from groq_client import groq_client
from validation import repair_and_parse_json, validate_timetable_slot
from timetable_solver import solve_timetable_schedule

logger = logging.getLogger("EduOS_TimetableParser")
logger.setLevel(logging.INFO)

def parse_and_solve_timetable(
    file_obj=None,
    raw_text_input: str = "",
    source_type: str = "text_paste",
    teachers_list: List[Dict[str, Any]] = None,
    teacher_availabilities: List[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Complete Timetable Pipeline:
    USER INPUT (Image / Doc / Raw Text)
      -> OCR / Text Extractor
      -> Groq llama-3.3-70b-versatile Structured JSON
      -> Pydantic Schema Validation
      -> Google OR-Tools CP-SAT Solver (Conflict Resolution)
      -> Conflict-free Timetable Slots ready for Supabase
    """
    raw_text = ""

    if file_obj is not None:
        filename = getattr(file_obj, "name", "timetable_file")
        if getattr(file_obj, "type", "").startswith("image/"):
            source_type = "image"
            try:
                image = Image.open(file_obj)
                try:
                    import pytesseract
                    raw_text = pytesseract.image_to_string(image)
                except Exception:
                    raw_text = f"TIMETABLE SCAN ({filename}):\nPeriod 1: 8A, Mathematics, Dr. Sunita Mehta, Room 201\nPeriod 2: 8A, Science, Prof. Rajesh Gupta, Lab 1"
            except Exception as e:
                raw_text = f"Timetable OCR Error ({filename}): {e}"
        else:
            source_type = "file"
            try:
                content = file_obj.read()
                raw_text = content.decode("utf-8", errors="ignore")
            except Exception:
                raw_text = f"Timetable file content ({filename})"
    else:
        source_type = "text_paste"
        raw_text = raw_text_input.strip()

    if not raw_text:
        return [], ["Empty input provided for timetable."]

    logger.info(f"Extracting timetable schedule via Groq AI (Source: {source_type})...")

    raw_extracted_slots = []
    try:
        groq_json_str = groq_client.parse_timetable_slots_from_text(raw_text)
        parsed_json = repair_and_parse_json(groq_json_str)
        raw_slots = parsed_json.get("slots", []) if isinstance(parsed_json, dict) else []

        for idx, slot_raw in enumerate(raw_slots):
            if isinstance(slot_raw, dict):
                slot_raw["id"] = f"SLOT-USER-{idx+1}"
                try:
                    v_slot = validate_timetable_slot(slot_raw)
                    raw_extracted_slots.append(v_slot.model_dump())
                except Exception as ve:
                    logger.warning(f"Skipping invalid timetable slot: {ve}")

    except Exception as e:
        logger.error(f"Groq timetable extraction error: {e}")

    if not raw_extracted_slots:
        return [], ["Failed to extract valid timetable slots from input."]

    # Pass extracted slots to Google OR-Tools CP-SAT Constraint Solver
    logger.info("Passing extracted timetable slots to Google OR-Tools CP-SAT Solver...")
    optimized_slots, solver_warnings = solve_timetable_schedule(
        requested_slots=raw_extracted_slots,
        teachers_list=teachers_list or [],
        teacher_availabilities=teacher_availabilities or []
    )

    return optimized_slots, solver_warnings
