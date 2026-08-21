from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Teacher, TeacherAvailability


# ── Teacher ───────────────────────────────────────────────────────────────────

def get_all_teachers(db: Session) -> List[Teacher]:
    return db.query(Teacher).order_by(Teacher.id).all()


def get_teacher_by_id(db: Session, teacher_id: str) -> Optional[Teacher]:
    return db.query(Teacher).filter(Teacher.id == teacher_id).first()


def create_teacher(db: Session, data: dict) -> Teacher:
    teacher = Teacher(**data)
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def update_teacher(db: Session, teacher_id: str, data: dict) -> Optional[Teacher]:
    teacher = get_teacher_by_id(db, teacher_id)
    if not teacher:
        return None
    for key, value in data.items():
        setattr(teacher, key, value)
    db.commit()
    db.refresh(teacher)
    return teacher


def delete_teacher(db: Session, teacher_id: str) -> bool:
    teacher = get_teacher_by_id(db, teacher_id)
    if not teacher:
        return False
    db.delete(teacher)
    db.commit()
    return True


# ── Teacher Availability ──────────────────────────────────────────────────────

def get_all_availability(db: Session) -> List[TeacherAvailability]:
    return db.query(TeacherAvailability).order_by(TeacherAvailability.created_at.desc()).all()


def upsert_availability(db: Session, data: dict) -> TeacherAvailability:
    existing = db.query(TeacherAvailability).filter(
        TeacherAvailability.id == data.get("id")
    ).first() if data.get("id") else None

    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing

    record = TeacherAvailability(**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
