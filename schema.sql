-- EduOS AI — Supabase PostgreSQL Schema
-- Apply this file in the Supabase SQL Editor.
-- Run once per project. Safe to re-run (uses IF NOT EXISTS).

-- 1. Students Table
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    roll_no TEXT UNIQUE,
    class TEXT NOT NULL,
    parent_name TEXT,
    parent_phone TEXT,
    parent_email TEXT,
    attendance_pct NUMERIC(5,2) DEFAULT 100.0,
    fee_status TEXT DEFAULT 'paid',
    fee_amount_due INTEGER DEFAULT 0,
    gpa NUMERIC(3,2) DEFAULT 4.0,
    risk_level TEXT DEFAULT 'low',
    assigned_room TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Teachers Table
CREATE TABLE IF NOT EXISTS teachers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    subject TEXT NOT NULL,
    email TEXT UNIQUE,
    assigned_classes TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Teacher Availability Table
-- Stores per-teacher availability constraints and absence records.
-- Used by: db_client.py (get/upsert_teacher_availability),
--          timetable_solver.py (unavailable_matrix),
--          teacher_parser.py (TeacherAvailabilitySchema),
--          data_store.py (toggle_teacher absence record).
CREATE TABLE IF NOT EXISTS teacher_availability (
    id TEXT PRIMARY KEY,
    teacher_id TEXT REFERENCES teachers(id) ON DELETE CASCADE,
    teacher_name TEXT NOT NULL,
    day_of_week TEXT,                        -- e.g. 'Monday'
    specific_date DATE,                      -- optional specific date (YYYY-MM-DD)
    period INTEGER,                          -- period number 1-6; NULL means all periods
    status TEXT NOT NULL DEFAULT 'available',-- 'available' | 'unavailable' | 'preferred'
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Timetable Table
CREATE TABLE IF NOT EXISTS timetable (
    id TEXT PRIMARY KEY,
    period INTEGER NOT NULL,
    time TEXT NOT NULL,
    class_name TEXT NOT NULL,
    subject TEXT NOT NULL,
    teacher_id TEXT REFERENCES teachers(id) ON DELETE SET NULL,
    teacher_name TEXT,
    room TEXT,
    has_conflict BOOLEAN DEFAULT FALSE,
    conflict_reason TEXT,
    is_substitute BOOLEAN DEFAULT FALSE,
    substitute_teacher TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    source_type TEXT DEFAULT 'file',         -- 'image' | 'file' | 'text_paste'
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'review_required',   -- 'review_required' | 'committed' | 'rejected'
    ocr_raw_text TEXT,
    fields JSONB DEFAULT '{}'::jsonb,
    confidence NUMERIC(5,2) DEFAULT 90.0,
    validation_errors TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    student_id TEXT REFERENCES students(id) ON DELETE SET NULL,
    action TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Insights Table
CREATE TABLE IF NOT EXISTS insights (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    metric TEXT NOT NULL,
    trend TEXT NOT NULL,
    forecast TEXT NOT NULL,
    confidence INTEGER DEFAULT 90,
    recommendation TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Copilot Messages Table
CREATE TABLE IF NOT EXISTS copilot_messages (
    id TEXT PRIMARY KEY,
    sender TEXT NOT NULL,
    text TEXT NOT NULL,
    sql TEXT,
    table_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Users Table (Authentication)
-- Stores application user accounts with hashed passwords.
-- linked_id references the relevant domain record:
--   admin   -> NULL (no linked domain record)
--   teacher -> teachers.id
--   student -> students.id
--   parent  -> students.id  (the child they monitor)
CREATE TABLE IF NOT EXISTS users (
    id           TEXT PRIMARY KEY,
    username     TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role         TEXT NOT NULL CHECK (role IN ('admin', 'teacher', 'student', 'parent')),
    linked_id    TEXT,          -- FK enforced at application layer (cross-table)
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role     ON users(role);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_students_class ON students(class);
CREATE INDEX IF NOT EXISTS idx_students_attendance ON students(attendance_pct);
CREATE INDEX IF NOT EXISTS idx_teacher_availability_teacher ON teacher_availability(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_availability_status ON teacher_availability(status);
CREATE INDEX IF NOT EXISTS idx_timetable_class_period ON timetable(class_name, period);
CREATE INDEX IF NOT EXISTS idx_timetable_teacher ON timetable(teacher_id);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved);

-- ─────────────────────────────────────────────────────────────────────────────
-- Row Level Security (RLS)
-- ─────────────────────────────────────────────────────────────────────────────
-- EduOS AI uses application-layer RBAC (auth.py) with a custom JWT login flow.
-- The Streamlit server connects via the Supabase anon key (role: anon).
-- Fine-grained admin / teacher / student / parent permissions are enforced in
-- Python — NOT via Supabase Auth session claims.
--
-- These policies therefore grant the anon/authenticated roles the CRUD access
-- that db_client.py already performs. This unblocks fresh installs where RLS
-- was previously enabled with zero policies (which denies all anon access).
--
-- Re-run safe: policies are dropped and recreated idempotently.
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE students              ENABLE ROW LEVEL SECURITY;
ALTER TABLE teachers              ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_availability  ENABLE ROW LEVEL SECURITY;
ALTER TABLE timetable             ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents             ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts                ENABLE ROW LEVEL SECURITY;
ALTER TABLE insights              ENABLE ROW LEVEL SECURITY;
ALTER TABLE copilot_messages      ENABLE ROW LEVEL SECURITY;
ALTER TABLE users                 ENABLE ROW LEVEL SECURITY;

-- Helper: drop existing app-server policies so this file is safe to re-run.
DO $$
DECLARE
  tbl  TEXT;
  pol  TEXT;
BEGIN
  FOREACH tbl IN ARRAY ARRAY[
    'students', 'teachers', 'teacher_availability', 'timetable',
    'documents', 'alerts', 'insights', 'copilot_messages', 'users'
  ] LOOP
    FOREACH pol IN ARRAY ARRAY[
      'app_server_select', 'app_server_insert',
      'app_server_update', 'app_server_delete'
    ] LOOP
      EXECUTE format('DROP POLICY IF EXISTS %I ON %I', pol, tbl);
    END LOOP;
  END LOOP;
END $$;

-- ── School operational data ──────────────────────────────────────────────────
-- Mirrors auth.py permissions at the transport layer: the trusted app server
-- (Streamlit + db_client.py) performs all reads/writes on behalf of logged-in
-- users after RBAC checks in Python.

CREATE POLICY app_server_select ON students
  FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY app_server_insert ON students
  FOR INSERT TO anon, authenticated WITH CHECK (true);

CREATE POLICY app_server_update ON students
  FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);

CREATE POLICY app_server_delete ON students
  FOR DELETE TO anon, authenticated USING (true);

CREATE POLICY app_server_select ON teachers
  FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY app_server_insert ON teachers
  FOR INSERT TO anon, authenticated WITH CHECK (true);

CREATE POLICY app_server_update ON teachers
  FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);

CREATE POLICY app_server_delete ON teachers
  FOR DELETE TO anon, authenticated USING (true);

CREATE POLICY app_server_select ON teacher_availability
  FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY app_server_insert ON teacher_availability
  FOR INSERT TO anon, authenticated WITH CHECK (true);

CREATE POLICY app_server_update ON teacher_availability
  FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);

CREATE POLICY app_server_delete ON teacher_availability
  FOR DELETE TO anon, authenticated USING (true);

CREATE POLICY app_server_select ON timetable
  FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY app_server_insert ON timetable
  FOR INSERT TO anon, authenticated WITH CHECK (true);

CREATE POLICY app_server_update ON timetable
  FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);

CREATE POLICY app_server_delete ON timetable
  FOR DELETE TO anon, authenticated USING (true);

-- Documents: admin-only writes in auth.py; app server mediates all access.
CREATE POLICY app_server_select ON documents
  FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY app_server_insert ON documents
  FOR INSERT TO anon, authenticated WITH CHECK (true);

CREATE POLICY app_server_update ON documents
  FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);

CREATE POLICY app_server_delete ON documents
  FOR DELETE TO anon, authenticated USING (true);

-- Alerts: read/write for admin + teacher in auth.py; app server mediates.
CREATE POLICY app_server_select ON alerts
  FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY app_server_insert ON alerts
  FOR INSERT TO anon, authenticated WITH CHECK (true);

CREATE POLICY app_server_update ON alerts
  FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);

CREATE POLICY app_server_delete ON alerts
  FOR DELETE TO anon, authenticated USING (true);

-- Insights: admin analytics reads; writes reserved for future persistence.
CREATE POLICY app_server_select ON insights
  FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY app_server_insert ON insights
  FOR INSERT TO anon, authenticated WITH CHECK (true);

CREATE POLICY app_server_update ON insights
  FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);

CREATE POLICY app_server_delete ON insights
  FOR DELETE TO anon, authenticated USING (true);

-- Copilot messages: admin + teacher in auth.py; app server mediates.
CREATE POLICY app_server_select ON copilot_messages
  FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY app_server_insert ON copilot_messages
  FOR INSERT TO anon, authenticated WITH CHECK (true);

CREATE POLICY app_server_update ON copilot_messages
  FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);

CREATE POLICY app_server_delete ON copilot_messages
  FOR DELETE TO anon, authenticated USING (true);

-- Users: login lookup (SELECT by username) + admin user management via app.
-- Password hashes are never exposed in the UI; only db_client reads them server-side.
CREATE POLICY app_server_select ON users
  FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY app_server_insert ON users
  FOR INSERT TO anon, authenticated WITH CHECK (true);

CREATE POLICY app_server_update ON users
  FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);

CREATE POLICY app_server_delete ON users
  FOR DELETE TO anon, authenticated USING (true);
