import json
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import TimetableSlot, Document, Alert


# ── Timetable ─────────────────────────────────────────────────────────────────

def get_timetable(db: Session) -> List[TimetableSlot]:
    return db.query(TimetableSlot).order_by(TimetableSlot.period).all()


def replace_timetable(db: Session, slots: List[dict]) -> List[TimetableSlot]:
    db.query(TimetableSlot).delete()
    created = []
    for slot in slots:
        record = TimetableSlot(**slot)
        db.add(record)
        created.append(record)
    db.commit()
    return created


def get_slot_by_id(db: Session, slot_id: str) -> Optional[TimetableSlot]:
    return db.query(TimetableSlot).filter(TimetableSlot.id == slot_id).first()


# ── Documents ─────────────────────────────────────────────────────────────────

def get_all_documents(db: Session) -> List[Document]:
    return db.query(Document).order_by(Document.created_at.desc()).all()


def get_document_by_id(db: Session, doc_id: str) -> Optional[Document]:
    return db.query(Document).filter(Document.id == doc_id).first()


def insert_document(db: Session, data: dict) -> Document:
    if isinstance(data.get("fields"), dict):
        data["fields"] = json.dumps(data["fields"])
    doc = Document(**data)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_document(db: Session, doc_id: str, data: dict) -> Optional[Document]:
    doc = get_document_by_id(db, doc_id)
    if not doc:
        return None
    if isinstance(data.get("fields"), dict):
        data["fields"] = json.dumps(data["fields"])
    for key, value in data.items():
        setattr(doc, key, value)
    db.commit()
    db.refresh(doc)
    return doc


# ── Alerts ────────────────────────────────────────────────────────────────────

def get_all_alerts(db: Session) -> List[Alert]:
    return db.query(Alert).order_by(Alert.created_at.desc()).all()


def insert_alert(db: Session, data: dict) -> Alert:
    alert = Alert(**data)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def resolve_alert(db: Session, alert_id: str) -> bool:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return False
    alert.resolved = True
    db.commit()
    return True
