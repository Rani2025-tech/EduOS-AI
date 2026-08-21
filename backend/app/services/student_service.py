import json
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Student


def get_all(db: Session) -> List[Student]:
    return db.query(Student).order_by(Student.created_at.desc()).all()


def get_by_id(db: Session, student_id: str) -> Optional[Student]:
    return db.query(Student).filter(Student.id == student_id).first()


def create(db: Session, data: dict) -> Student:
    student = Student(**data)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def update(db: Session, student_id: str, data: dict) -> Optional[Student]:
    student = get_by_id(db, student_id)
    if not student:
        return None
    for key, value in data.items():
        setattr(student, key, value)
    db.commit()
    db.refresh(student)
    return student


def delete(db: Session, student_id: str) -> bool:
    student = get_by_id(db, student_id)
    if not student:
        return False
    db.delete(student)
    db.commit()
    return True
