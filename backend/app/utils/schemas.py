from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Student ───────────────────────────────────────────────────────────────────

class StudentBase(BaseModel):
    name:           str
    roll_no:        Optional[str] = None
    class_name:     str = Field(..., alias="class")
    parent_name:    Optional[str] = None
    parent_phone:   Optional[str] = None
    parent_email:   Optional[str] = None
    attendance_pct: float = 100.0
    fee_status:     str = "pending"
    fee_amount_due: int = 0
    gpa:            float = 4.0
    risk_level:     str = "low"
    assigned_room:  Optional[str] = None

    class Config:
        populate_by_name = True


class StudentCreate(StudentBase):
    id: str


class StudentOut(StudentCreate):
    class Config:
        from_attributes = True
        populate_by_name = True


# ── Teacher ───────────────────────────────────────────────────────────────────

class TeacherBase(BaseModel):
    name:             str
    subject:          str
    email:            Optional[str] = None
    assigned_classes: Optional[str] = None
    status:           str = "active"


class TeacherCreate(TeacherBase):
    id: str


class TeacherOut(TeacherCreate):
    class Config:
        from_attributes = True


# ── Teacher Availability ──────────────────────────────────────────────────────

class AvailabilityBase(BaseModel):
    teacher_id:    Optional[str] = None
    teacher_name:  str
    day_of_week:   Optional[str] = None
    specific_date: Optional[str] = None
    period:        Optional[int] = None
    status:        str = "available"
    notes:         Optional[str] = None


class AvailabilityCreate(AvailabilityBase):
    id: Optional[str] = None


class AvailabilityOut(AvailabilityCreate):
    class Config:
        from_attributes = True


# ── Timetable Slot ────────────────────────────────────────────────────────────

class TimetableSlotBase(BaseModel):
    period:             int
    time:               str = "08:30 AM"
    class_name:         str
    subject:            str
    teacher_id:         Optional[str] = None
    teacher_name:       Optional[str] = None
    room:               Optional[str] = None
    has_conflict:       bool = False
    conflict_reason:    Optional[str] = None
    is_substitute:      bool = False
    substitute_teacher: Optional[str] = None


class TimetableSlotCreate(TimetableSlotBase):
    id: Optional[str] = None


class TimetableSlotOut(TimetableSlotCreate):
    class Config:
        from_attributes = True


# ── Document ──────────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id:                str
    source_type:       str
    doc_type:          str
    filename:          str
    ocr_raw_text:      str
    fields:            str        # stored as JSON string
    confidence:        float
    status:            str
    validation_errors: Optional[str] = None

    class Config:
        from_attributes = True


# ── Alert ─────────────────────────────────────────────────────────────────────

class AlertOut(BaseModel):
    id:         str
    type:       str
    priority:   str
    title:      str
    message:    str
    timestamp:  Optional[str] = None
    resolved:   bool
    student_id: Optional[str] = None
    action:     Optional[str] = None

    class Config:
        from_attributes = True


# ── Generic ───────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True
