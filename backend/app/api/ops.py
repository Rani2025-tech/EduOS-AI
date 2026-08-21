from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.utils.deps import get_db
from app.utils.schemas import TimetableSlotOut, TimetableSlotCreate, DocumentOut, AlertOut
from app.services import ops_service

# ── Timetable ─────────────────────────────────────────────────────────────────

timetable_router = APIRouter(prefix="/api/timetable", tags=["timetable"])


@timetable_router.get("/", response_model=List[TimetableSlotOut])
def get_timetable(db: Session = Depends(get_db)):
    return ops_service.get_timetable(db)


@timetable_router.post("/replace", response_model=List[TimetableSlotOut])
def replace_timetable(slots: List[TimetableSlotCreate], db: Session = Depends(get_db)):
    return ops_service.replace_timetable(db, [s.model_dump() for s in slots])


@timetable_router.get("/{slot_id}", response_model=TimetableSlotOut)
def get_slot(slot_id: str, db: Session = Depends(get_db)):
    slot = ops_service.get_slot_by_id(db, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return slot


# ── Documents ─────────────────────────────────────────────────────────────────

docs_router = APIRouter(prefix="/api/documents", tags=["documents"])


@docs_router.get("/", response_model=List[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return ops_service.get_all_documents(db)


@docs_router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = ops_service.get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@docs_router.post("/", response_model=DocumentOut, status_code=201)
def create_document(payload: dict, db: Session = Depends(get_db)):
    return ops_service.insert_document(db, payload)


@docs_router.patch("/{doc_id}", response_model=DocumentOut)
def update_document(doc_id: str, payload: dict, db: Session = Depends(get_db)):
    doc = ops_service.update_document(db, doc_id, payload)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


# ── Alerts ────────────────────────────────────────────────────────────────────

alerts_router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@alerts_router.get("/", response_model=List[AlertOut])
def list_alerts(db: Session = Depends(get_db)):
    return ops_service.get_all_alerts(db)


@alerts_router.post("/", response_model=AlertOut, status_code=201)
def create_alert(payload: dict, db: Session = Depends(get_db)):
    return ops_service.insert_alert(db, payload)


@alerts_router.patch("/{alert_id}/resolve")
def resolve_alert(alert_id: str, db: Session = Depends(get_db)):
    if not ops_service.resolve_alert(db, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert resolved", "success": True}
