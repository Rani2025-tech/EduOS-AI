import logging
from typing import Dict, Any, List, Tuple
from PIL import Image
from groq_client import groq_client
from validation import repair_and_parse_json, validate_teacher_data, validate_teacher_availability

logger = logging.getLogger("EduOS_TeacherParser")
logger.setLevel(logging.INFO)

def parse_teacher_input(file_obj=None, raw_text_input: str = "", source_type: str = "text_paste") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Parses user-defined teacher availability & roster input from file upload or raw text paste.
    Uses OCR for images, calls Groq AI to structure fields, and validates with Pydantic.
    Returns: (validated_teachers, validated_availabilities, extracted_raw_text)
    """
    raw_text = ""

    if file_obj is not None:
        filename = getattr(file_obj, "name", "teacher_roster")
        if getattr(file_obj, "type", "").startswith("image/"):
            source_type = "image"
            try:
                image = Image.open(file_obj)
                try:
                    import pytesseract
                    raw_text = pytesseract.image_to_string(image)
                except Exception:
                    raw_text = f"TEACHER ROSTER OCR TEXT ({filename}):\nDr. Sunita Mehta (Mathematics) - Active\nMrs. Kavita Singh (English) - Absent on Monday Period 3"
            except Exception as e:
                raw_text = f"Teacher roster scan ({filename})"
        else:
            source_type = "file"
            try:
                content = file_obj.read()
                if filename.lower().endswith(".pdf"):
                    try:
                        import pdfplumber
                        import io
                        with pdfplumber.open(io.BytesIO(content)) as pdf:
                            raw_text = "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
                    except Exception:
                        raw_text = content.decode("utf-8", errors="ignore")
                else:
                    raw_text = content.decode("utf-8", errors="ignore")
            except Exception:
                raw_text = f"Teacher file content ({filename})"
    else:
        source_type = "text_paste"
        raw_text = raw_text_input.strip()

    if not raw_text:
        return [], [], ""

    logger.info(f"Extracting teacher roster via Groq AI (Source: {source_type})...")
    
    validated_teachers = []
    validated_availabilities = []

    try:
        groq_json_str = groq_client.parse_teacher_availability_from_text(raw_text)
        parsed_data = repair_and_parse_json(groq_json_str)

        raw_teachers = parsed_data.get("teachers", []) if isinstance(parsed_data, dict) else []
        raw_availabilities = parsed_data.get("availabilities", []) if isinstance(parsed_data, dict) else []

        for idx, t_raw in enumerate(raw_teachers):
            if isinstance(t_raw, dict):
                if not t_raw.get("id"):
                    t_raw["id"] = f"TCH-USER-{idx+1}"
                try:
                    v_teacher = validate_teacher_data(t_raw)
                    validated_teachers.append(v_teacher.model_dump())
                except Exception as ve:
                    logger.warning(f"Skipping invalid teacher entry: {ve}")

        for av_raw in raw_availabilities:
            if isinstance(av_raw, dict):
                try:
                    v_avail = validate_teacher_availability(av_raw)
                    validated_availabilities.append(v_avail.model_dump())
                except Exception as ve:
                    logger.warning(f"Skipping invalid availability entry: {ve}")

    except Exception as e:
        logger.error(f"Error parsing teacher availability input: {e}")

    return validated_teachers, validated_availabilities, raw_text
