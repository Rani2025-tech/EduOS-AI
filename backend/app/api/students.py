from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.utils.deps import get_db
from app.utils.schemas import StudentOut, StudentCreate
from app.services import student_service

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("/", response_model=List[StudentOut])
def list_students(db: Session = Depends(get_db)):
    return student_service.get_all(db)


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: str, db: Session = Depends(get_db)):
    s = student_service.get_by_id(db, student_id)
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    return s


@router.post("/", response_model=StudentOut, status_code=201)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    return student_service.create(db, payload.model_dump(by_alias=True))


@router.patch("/{student_id}", response_model=StudentOut)
def update_student(student_id: str, payload: dict, db: Session = Depends(get_db)):
    s = student_service.update(db, student_id, payload)
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    return s


@router.delete("/{student_id}")
def delete_student(student_id: str, db: Session = Depends(get_db)):
    if not student_service.delete(db, student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Deleted", "success": True}
