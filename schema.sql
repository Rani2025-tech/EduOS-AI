-- EduOS AI — Supabase PostgreSQL Schema

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

-- 3. Timetable Table
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

-- 4. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'review_required',
    ocr_raw_text TEXT,
    fields JSONB DEFAULT '{}'::jsonb,
    confidence NUMERIC(5,2) DEFAULT 90.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Alerts Table
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

-- 6. Insights Table
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

-- 7. Copilot Messages Table
CREATE TABLE IF NOT EXISTS copilot_messages (
    id TEXT PRIMARY KEY,
    sender TEXT NOT NULL,
    text TEXT NOT NULL,
    sql TEXT,
    table_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE teachers ENABLE ROW LEVEL SECURITY;
ALTER TABLE timetable ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE copilot_messages ENABLE ROW LEVEL SECURITY;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_students_class ON students(class);
CREATE INDEX IF NOT EXISTS idx_students_attendance ON students(attendance_pct);
CREATE INDEX IF NOT EXISTS idx_timetable_class_period ON timetable(class_name, period);
CREATE INDEX IF NOT EXISTS idx_timetable_teacher ON timetable(teacher_id);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved);
