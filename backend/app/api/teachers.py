from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.utils.deps import get_db
from app.utils.schemas import TeacherOut, TeacherCreate, AvailabilityOut, AvailabilityCreate
from app.services import teacher_service

router = APIRouter(prefix="/api/teachers", tags=["teachers"])


@router.get("/", response_model=List[TeacherOut])
def list_teachers(db: Session = Depends(get_db)):
    return teacher_service.get_all_teachers(db)


@router.get("/{teacher_id}", response_model=TeacherOut)
def get_teacher(teacher_id: str, db: Session = Depends(get_db)):
    t = teacher_service.get_teacher_by_id(db, teacher_id)
    if not t:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return t


@router.post("/", response_model=TeacherOut, status_code=201)
def create_teacher(payload: TeacherCreate, db: Session = Depends(get_db)):
    return teacher_service.create_teacher(db, payload.model_dump())


@router.patch("/{teacher_id}", response_model=TeacherOut)
def update_teacher(teacher_id: str, payload: dict, db: Session = Depends(get_db)):
    t = teacher_service.update_teacher(db, teacher_id, payload)
    if not t:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return t


@router.delete("/{teacher_id}")
def delete_teacher(teacher_id: str, db: Session = Depends(get_db)):
    if not teacher_service.delete_teacher(db, teacher_id):
        raise HTTPException(status_code=404, detail="Teacher not found")
    return {"message": "Deleted", "success": True}


# ── Availability sub-routes ───────────────────────────────────────────────────

avail_router = APIRouter(prefix="/api/availability", tags=["availability"])


@avail_router.get("/", response_model=List[AvailabilityOut])
def list_availability(db: Session = Depends(get_db)):
    return teacher_service.get_all_availability(db)


@avail_router.post("/", response_model=AvailabilityOut, status_code=201)
def upsert_availability(payload: AvailabilityCreate, db: Session = Depends(get_db)):
    return teacher_service.upsert_availability(db, payload.model_dump())
