import json
import re
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ValidationError

# Configure logger
logger = logging.getLogger("EduOS_Validation")
logger.setLevel(logging.INFO)

# ----------------------------------------------------
# 1. Pydantic Models for Schema Enforcement
# ----------------------------------------------------

class StudentSchema(BaseModel):
    id: str = Field(..., description="Unique student ID")
    name: str = Field(..., description="Student full name")
    roll_no: Optional[str] = Field(None, description="Roll number")
    class_name: str = Field(..., alias="class", description="Class / Grade section")
    parent_name: Optional[str] = Field(None, description="Parent or guardian name")
    parent_phone: Optional[str] = Field(None, description="Parent phone number")
    parent_email: Optional[str] = Field(None, description="Parent email address")
    attendance_pct: float = Field(100.0, description="Attendance percentage")
    fee_status: str = Field("paid", description="Fee payment status: paid, pending, overdue")
    fee_amount_due: int = Field(0, description="Fee amount due in INR")
    gpa: float = Field(4.0, description="GPA score")
    risk_level: str = Field("low", description="Academic/attendance risk level: low, medium, high")
    assigned_room: Optional[str] = Field(None, description="Assigned room")

    class Config:
        populate_by_name = True

class TeacherSchema(BaseModel):
    id: str = Field(..., description="Teacher ID")
    name: str = Field(..., description="Teacher full name")
    subject: str = Field(..., description="Primary subject taught")
    email: Optional[str] = Field(None, description="Teacher email")
    assigned_classes: Optional[str] = Field(None, description="Comma separated assigned classes")
    status: str = Field("active", description="Status: active, absent, leave")

class TeacherAvailabilitySchema(BaseModel):
    id: Optional[str] = Field(None, description="Availability record ID")
    teacher_id: Optional[str] = Field(None, description="Teacher ID reference")
    teacher_name: str = Field(..., description="Teacher name")
    day_of_week: Optional[str] = Field(None, description="Day of week")
    specific_date: Optional[str] = Field(None, description="Specific date (YYYY-MM-DD)")
    period: Optional[int] = Field(None, description="Period number (1 to 6)")
    status: str = Field("available", description="Status: available, unavailable, preferred")
    notes: Optional[str] = Field(None, description="Additional notes or reason")

class TimetableSlotSchema(BaseModel):
    id: Optional[str] = Field(None, description="Slot ID")
    period: int = Field(..., description="Period number")
    time: str = Field("08:30 AM", description="Slot time range")
    class_name: str = Field(..., description="Class name (e.g. 8A)")
    subject: str = Field(..., description="Subject name")
    teacher_id: Optional[str] = Field(None, description="Teacher ID")
    teacher_name: Optional[str] = Field(None, description="Teacher Name")
    room: Optional[str] = Field(None, description="Room number / lab")
    has_conflict: bool = Field(False, description="Has scheduling conflict")
    conflict_reason: Optional[str] = Field(None, description="Conflict explanation")
    is_substitute: bool = Field(False, description="Is substitute assigned")
    substitute_teacher: Optional[str] = Field(None, description="Substitute teacher name")

class DocumentSchema(BaseModel):
    id: str = Field(..., description="Document ID")
    source_type: str = Field("file", description="Source type: image, file, text_paste")
    doc_type: str = Field("admission_form", description="Document type")
    filename: str = Field(..., description="File name or document title")
    ocr_raw_text: str = Field("", description="Raw text extracted")
    fields: Dict[str, Any] = Field(default_factory=dict, description="Structured extracted fields")
    confidence: float = Field(90.0, description="Extraction confidence percentage")
    status: str = Field("review_required", description="Review status: review_required, committed, rejected")
    validation_errors: Optional[str] = Field(None, description="Validation error logs if any")

# ----------------------------------------------------
# 2. Robust Repair & Parsing Utilities
# ----------------------------------------------------

def repair_and_parse_json(raw_text: str) -> Any:
    """
    Safely extracts and repairs JSON objects/arrays from Groq AI output.
    Handles markdown code blocks (```json ... ```), trailing commas, and unescaped quotes.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Empty string received for JSON parsing")

    text = raw_text.strip()

    # 1. Strip markdown code block wrappers if present
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if code_block_match:
        text = code_block_match.group(1).strip()

    # 2. If text contains extraneous narrative text, find outer JSON brackets [ ... ] or { ... }
    if not (text.startswith('{') or text.startswith('[')):
        json_search = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
        if json_search:
            text = json_search.group(1).strip()

    # 3. Clean up common LLM JSON formatting issues (trailing commas)
    text = re.sub(r',\s*([\]}])', r'\1', text)

    # 4. Parse JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError during parsing: {e}. Raw text sample: {text[:200]}")
        raise ValueError(f"Invalid JSON content from Groq AI response: {str(e)}")

# ----------------------------------------------------
# 3. Model Validation Helpers
# ----------------------------------------------------

def validate_student_data(data: Dict[str, Any]) -> StudentSchema:
    """Validates student record data against StudentSchema."""
    try:
        validated = StudentSchema(**data)
        logger.info(f"Student validation successful for ID={validated.id}, Name={validated.name}")
        return validated
    except ValidationError as e:
        logger.error(f"Student validation failure: {e.errors()}")
        raise ValueError(f"Student validation failed: {e.errors()}")

def validate_teacher_data(data: Dict[str, Any]) -> TeacherSchema:
    """Validates teacher record data against TeacherSchema."""
    try:
        validated = TeacherSchema(**data)
        logger.info(f"Teacher validation successful for ID={validated.id}, Name={validated.name}")
        return validated
    except ValidationError as e:
        logger.error(f"Teacher validation failure: {e.errors()}")
        raise ValueError(f"Teacher validation failed: {e.errors()}")

def validate_teacher_availability(data: Dict[str, Any]) -> TeacherAvailabilitySchema:
    """Validates teacher availability data against TeacherAvailabilitySchema."""
    try:
        validated = TeacherAvailabilitySchema(**data)
        return validated
    except ValidationError as e:
        logger.error(f"Teacher availability validation failure: {e.errors()}")
        raise ValueError(f"Teacher availability validation failed: {e.errors()}")

def validate_timetable_slot(data: Dict[str, Any]) -> TimetableSlotSchema:
    """Validates timetable slot data against TimetableSlotSchema."""
    try:
        validated = TimetableSlotSchema(**data)
        return validated
    except ValidationError as e:
        logger.error(f"Timetable slot validation failure: {e.errors()}")
        raise ValueError(f"Timetable slot validation failed: {e.errors()}")
