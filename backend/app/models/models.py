"""
EduOS AI Backend — SQLAlchemy ORM Models
Mirrors the Supabase schema used by the Streamlit app.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime
from sqlalchemy.sql import func
from app.database.database import Base


class Student(Base):
    __tablename__ = "students"

    id              = Column(String, primary_key=True, index=True)
    name            = Column(String, nullable=False)
    roll_no         = Column(String, nullable=True)
    class_name      = Column("class", String, nullable=False)
    parent_name     = Column(String, nullable=True)
    parent_phone    = Column(String, nullable=True)
    parent_email    = Column(String, nullable=True)
    attendance_pct  = Column(Float, default=100.0)
    fee_status      = Column(String, default="pending")
    fee_amount_due  = Column(Integer, default=0)
    gpa             = Column(Float, default=4.0)
    risk_level      = Column(String, default="low")
    assigned_room   = Column(String, nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


class Teacher(Base):
    __tablename__ = "teachers"

    id               = Column(String, primary_key=True, index=True)
    name             = Column(String, nullable=False)
    subject          = Column(String, nullable=False)
    email            = Column(String, nullable=True)
    assigned_classes = Column(String, nullable=True)
    status           = Column(String, default="active")
    created_at       = Column(DateTime(timezone=True), server_default=func.now())


class TeacherAvailability(Base):
    __tablename__ = "teacher_availability"

    id            = Column(String, primary_key=True, index=True)
    teacher_id    = Column(String, nullable=True)
    teacher_name  = Column(String, nullable=False)
    day_of_week   = Column(String, nullable=True)
    specific_date = Column(String, nullable=True)
    period        = Column(Integer, nullable=True)
    status        = Column(String, default="available")
    notes         = Column(Text, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())


class TimetableSlot(Base):
    __tablename__ = "timetable"

    id                 = Column(String, primary_key=True, index=True)
    period             = Column(Integer, nullable=False)
    time               = Column(String, default="08:30 AM")
    class_name         = Column(String, nullable=False)
    subject            = Column(String, nullable=False)
    teacher_id         = Column(String, nullable=True)
    teacher_name       = Column(String, nullable=True)
    room               = Column(String, nullable=True)
    has_conflict       = Column(Boolean, default=False)
    conflict_reason    = Column(String, nullable=True)
    is_substitute      = Column(Boolean, default=False)
    substitute_teacher = Column(String, nullable=True)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())


class Document(Base):
    __tablename__ = "documents"

    id                = Column(String, primary_key=True, index=True)
    source_type       = Column(String, default="file")
    doc_type          = Column(String, default="admission_form")
    filename          = Column(String, nullable=False)
    ocr_raw_text      = Column(Text, default="")
    fields            = Column(Text, default="{}")   # JSON string
    confidence        = Column(Float, default=90.0)
    status            = Column(String, default="review_required")
    validation_errors = Column(Text, nullable=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id         = Column(String, primary_key=True, index=True)
    type       = Column(String, nullable=False)
    priority   = Column(String, default="medium")
    title      = Column(String, nullable=False)
    message    = Column(Text, nullable=False)
    timestamp  = Column(String, nullable=True)
    resolved   = Column(Boolean, default=False)
    student_id = Column(String, nullable=True)
    action     = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id            = Column(String, primary_key=True, index=True)
    username      = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role          = Column(String, nullable=False)   # admin | teacher | student | parent
    linked_id     = Column(String, nullable=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
