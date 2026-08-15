# EduOS AI — The Autonomous School Operating System
### Product Requirements Document + Execution Plan

---

## 1. Product Overview

EduOS AI is an AI-powered school operations platform that unifies fragmented administrative, academic, scheduling, documentation, and resource-management workflows into a single intelligent system. It converts raw school data into automated workflows, proactive alerts, optimized schedules, predictive insights, and AI-assisted decisions.

## 2. Problem Statement

Schools run on disconnected systems and manual processes:

1. **Manual Documentation** — physical forms/PDFs need manual entry; repetitive entry causes errors and wastes admin time.
2. **Scheduling Conflicts** — teachers, classrooms, labs, and classes are scheduled separately; changes create timetable clashes.
3. **Siloed Systems** — student, attendance, fee, academic, and timetable data live in separate systems that don't talk to each other.
4. **Reactive Administration** — problems surface only after they've happened; no proactive monitoring.
5. **No Predictive Intelligence** — historical data is stored but never used to forecast staffing, enrollment, attendance, or resource needs.

**Result:** more admin work, slower decisions, duplicated effort, higher error rates.

## 3. Product Vision

> Turn school data into intelligent, proactive action.

| From | To |
|---|---|
| Manual | Digital |
| Reactive | Proactive |
| Fragmented | Unified |
| Data Storage | Data Intelligence |

## 4. Target Users / Personas

### Persona 1 — School Administrator
- **Goals:** manage operations, monitor problems, generate reports, decide faster
- **Pain points:** paperwork overload, scattered data, hard to spot problems early
- **Needs:** central dashboard, automated alerts, AI Copilot, predictive insights

### Persona 2 — Teacher
- **Goals:** manage classes, record attendance, track performance, view timetable
- **Pain points:** manual attendance, timetable churn, hard to monitor students
- **Needs:** simple attendance UI, smart timetable, student insights

### Persona 3 — Student
- **Goals:** view timetable, monitor progress, get relevant notifications
- **Needs:** personal dashboard, attendance, academic info, schedule

### Persona 4 — Parent
- **Goals:** monitor child's progress, receive important alerts
- **Needs:** attendance updates, academic reports, notifications

## 5. Product Goals

**Primary goals**
- Centralize school operational data
- Automate document processing
- Reduce manual administrative work
- Generate conflict-free timetables
- Provide proactive alerts
- Use historical data for predictions
- Provide natural-language access to school data (AI Copilot / NLQ over school data)

**Non-goals for MVP**
- Full accounting system
- Complete ERP replacement
- Advanced biometric attendance
- Mobile applications
- Complex parent communication system
- Fully autonomous decision-making (human stays in the loop)

## 6. Core Features

### Feature 1 — AI Document Reader (MVP anchor feature)
**Objective:** convert unstructured documents into structured school data.

**Input:** PDF, image, scanned form

**Pipeline:**
```
Document → OCR → Text Extraction → LLM/Information Extraction
→ Structured JSON → Validation → Database
```

**Example**
Input (Admission Form): `Name: Rahul, Class: 8A, Parent: XYZ`
Output:
```json
{
  "student_name": "Rahul",
  "class": "8A",
  "parent_name": "XYZ"
}
```

**Acceptance criteria**
- User can upload a document
- System extracts relevant fields
- Extracted data can be reviewed before commit
- Valid data is stored in the database
- Invalid/missing fields generate warnings, not silent failures

**Suggested implementation:** Tesseract/PaddleOCR (or a hosted OCR API) for text extraction on scanned inputs → Claude API for schema-guided field extraction (structured JSON output, prompted per document type: admission form, fee receipt, leave application, etc.) → a Pydantic schema validation layer → human-in-the-loop review screen → Postgres write.

### Feature 2 — Smart Timetable Engine
**Objective:** generate and maintain conflict-free timetables across teachers, classrooms, labs, and sections.
- Constraint-based scheduling (teacher availability, room capacity, subject-hour requirements, no double-booking)
- Auto-detects and flags conflicts when a manual edit is made
- Re-optimizes affected slots only (not a full regenerate) when a teacher is absent or a room is unavailable
- **Acceptance criteria:** zero double-bookings in generated output; edits are validated in real time; substitution suggestions offered when a teacher is marked absent

### Feature 3 — Unified Data Layer
**Objective:** single source of truth joining student, attendance, fee-status, academic, and timetable records that today live in silos.
- Common student/staff ID across modules
- Read APIs that let every other feature (alerts, copilot, predictions) query across domains without custom integrations
- **Acceptance criteria:** a single query can return a student's attendance + academic + fee status together

### Feature 4 — Proactive Alerts & Monitoring
**Objective:** surface problems before they escalate, instead of after.
- Rule-based triggers to start (e.g., attendance drops below threshold, fee overdue, grade decline over N assessments, room/teacher conflict introduced)
- Alerts routed to the right persona (admin, teacher, or parent) with context
- **Acceptance criteria:** alert fires within a defined SLA of the triggering event; no duplicate alerts for the same unresolved condition

### Feature 5 — Predictive Insights (post-MVP, data-dependent)
**Objective:** use historical data to forecast attendance trends, at-risk students, enrollment, and staffing/resource needs.
- Starts as simple statistical baselines (moving averages, trend lines) before any ML model, since there won't be enough historical data at launch to train reliably
- **Acceptance criteria:** predictions ship with a confidence indicator and are clearly labeled as forecasts, not facts

### Feature 6 — AI Copilot (Natural-Language Query over School Data)
**Objective:** let admins/teachers ask questions in plain language ("Which students in 8A have attendance below 75% this month?") and get answers grounded in the Unified Data Layer.
- RAG-style retrieval over structured records (query translated to a safe, scoped DB query — not free-form SQL execution) plus LLM for summarization/explanation
- **Acceptance criteria:** answers are traceable to underlying records; the copilot never writes to the database, only reads

## 7. Non-Functional Requirements
- **Data privacy:** student data is sensitive (minors) — role-based access control is mandatory from day one, not a later add-on
- **Auditability:** every automated write (document extraction, alert, timetable change) should be traceable to its source
- **Human-in-the-loop:** AI Document Reader and Predictive Insights must always have a review/override step before data is treated as authoritative
- **Availability:** core scheduling and attendance flows should degrade gracefully (read-only fallback) if the AI layer is down

## 8. Suggested Tech Stack

Given your existing stack (FastAPI, React/Vite, LangChain/RAG, FAISS, Claude API), a natural fit is:

| Layer | Choice | Why |
|---|---|---|
| Backend API | FastAPI | You already build full-stack apps on this; async support suits document pipelines |
| Frontend | React + Vite | Consistent with your other projects |
| Database | PostgreSQL | Relational integrity for student/attendance/fee/timetable joins; Unified Data Layer needs this |
| OCR | Tesseract / PaddleOCR (self-hosted) or a hosted OCR API | Start free/self-hosted; swap later if accuracy demands it |
| Extraction LLM | Claude API (structured/JSON output) | Already in your toolkit, good at schema-constrained extraction |
| Copilot retrieval | LangChain + a scoped query layer (not raw FAISS over documents — this data is structured, so retrieval is mostly SQL-backed, with FAISS reserved for any unstructured doc search) | Matches your RAG experience while fitting structured data |
| Scheduling engine | Constraint solver (e.g., Google OR-Tools CP-SAT) | Purpose-built for conflict-free timetabling, not something to hand-roll |
| Auth | JWT + role-based access (admin/teacher/student/parent) | Required given FERPA-style sensitivity of student data |

## 9. MVP Scope (what ships first)

To keep this buildable solo, MVP = **Feature 1 (AI Document Reader) + Feature 3 (Unified Data Layer, minimal) + Feature 2 (basic Smart Timetable)**. Alerts, Predictive Insights, and the Copilot are v2/v3 — they all depend on the Unified Data Layer existing first, so sequencing matters more than parallelizing.

## 10. Execution Plan / Roadmap

### Phase 0 — Foundations (Week 1–2)
- Define core data model: Student, Staff, Class/Section, Attendance, Timetable, Document
- Set up FastAPI + Postgres skeleton, auth, and role-based access
- Set up React/Vite shell with routing for the 4 personas

### Phase 1 — AI Document Reader (Week 3–5)
- OCR pipeline for PDF/image input
- Claude-based extraction with a per-document-type prompt/schema (start with admission form only, then expand)
- Validation layer + review-before-commit UI
- Store into Unified Data Layer

### Phase 2 — Unified Data Layer + Basic Dashboards (Week 6–7)
- Cross-domain read APIs (attendance + fee + academic joined by student ID)
- Minimal admin dashboard, teacher attendance UI, student/parent read-only views

### Phase 3 — Smart Timetable Engine (Week 8–10)
- Constraint model (teachers, rooms, subject-hours) via OR-Tools
- Conflict detection on manual edits
- Substitution suggestion on teacher absence

### Phase 4 — Proactive Alerts (Week 11–12)
- Rule engine on top of the Unified Data Layer (attendance threshold, fee overdue, conflict introduced)
- Notification routing by persona

### Phase 5 — AI Copilot (Week 13–15, post-MVP)
- Natural-language → scoped query translation over the Unified Data Layer
- Read-only, source-traceable answers

### Phase 6 — Predictive Insights (Week 16+, data-dependent)
- Ship only once there's enough historical data collected through Phases 1–4 to make baselines meaningful

## 11. Success Metrics
- % reduction in manual data-entry time (Document Reader adoption)
- Timetable conflicts per term (target: zero at generation, near-zero after edits)
- Alert lead time (how early a problem is flagged vs. when it would've been noticed manually)
- Copilot query accuracy / traceability rate

## 12. Key Risks
- **OCR accuracy on messy handwritten forms** — mitigate with mandatory human review step, not full automation
- **Data privacy for minors** — RBAC and audit logging must exist before any real student data touches the system
- **Solo-build scope creep** — the 6-feature list is large; MVP scope in §9 is deliberately narrow to avoid stalling
- **Cold-start for predictions** — no useful historical data at launch; Phase 6 is explicitly gated on data accumulation