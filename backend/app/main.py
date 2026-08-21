from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import Base, engine
from app.api import (
    students_router, teachers_router, availability_router,
    timetable_router, docs_router, alerts_router,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EduOS AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (students_router, teachers_router, availability_router,
               timetable_router, docs_router, alerts_router):
    app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "EduOS AI Backend", "version": "1.0.0"}
