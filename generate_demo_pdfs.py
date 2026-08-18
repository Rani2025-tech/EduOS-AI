from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_samples")
os.makedirs(BASE, exist_ok=True)

def make_pdf(filename, lines):
    path = os.path.join(BASE, filename)
    c = canvas.Canvas(path, pagesize=A4)
    y = 800
    for line in lines:
        c.setFont("Helvetica-Bold" if y == 800 else "Helvetica", 12 if y == 800 else 11)
        c.drawString(50, y, line)
        y -= 20
    c.save()
    print(f"Created: {path}")

# ── Admission Form ────────────────────────────────────────────────────────────
make_pdf("admission_form_aryan_sharma.pdf", [
    "STUDENT ADMISSION FORM",
    "Academic Year: 2024-2025  |  School: Greenfield Public School",
    "",
    "Student Name: Aryan Sharma",
    "Date of Birth: 12-March-2011",
    "Gender: Male",
    "Class: 8A",
    "Roll Number: 2024-8A-017",
    "Assigned Room: Room 204",
    "",
    "Parent Name: Suresh Sharma",
    "Contact Phone: +91 98201 45678",
    "Email Address: suresh.sharma@gmail.com",
    "",
    "Fee Status: pending",
    "Fee Amount Due: 18500 INR",
    "GPA: 3.8",
    "Risk Level: low",
    "Notes: Student has opted for Science stream electives.",
])

# ── Fee Receipt ───────────────────────────────────────────────────────────────
make_pdf("fee_receipt_priya_mehta.pdf", [
    "FEE RECEIPT",
    "Receipt No: RCP-2024-00892  |  Date: 15-November-2024",
    "School: Greenfield Public School",
    "",
    "Student Name: Priya Mehta",
    "Class: 9B",
    "Roll Number: 2024-9B-005",
    "Assigned Room: Room 310",
    "",
    "Parent Name: Anita Mehta",
    "Phone: +91 99887 23456",
    "Email: anita.mehta@yahoo.com",
    "",
    "Fee Status: paid",
    "Fee Amount Due: 0 INR",
    "Total Fee Paid: 16700 INR",
    "Payment Mode: UPI",
    "Transaction ID: UPI20241115089234",
    "GPA: 4.2",
    "Risk Level: low",
    "Remarks: Full fee cleared for Term 2. No dues pending.",
])

# ── Teacher Roster ────────────────────────────────────────────────────────────
make_pdf("teacher_roster_greenfield.pdf", [
    "TEACHER ROSTER — Greenfield Public School",
    "Academic Year: 2024-2025",
    "",
    "1. Dr. Sunita Mehta",
    "   Subject: Mathematics",
    "   Assigned Classes: 8A, 8B, 9A",
    "   Email: sunita.mehta@greenfield.edu",
    "   Status: available",
    "   Unavailability: Monday Period 1 (personal commitment)",
    "",
    "2. Prof. Rajesh Gupta",
    "   Subject: Science",
    "   Assigned Classes: 8A, 9B, 10A",
    "   Email: rajesh.gupta@greenfield.edu",
    "   Status: available",
    "   Unavailability: Wednesday Period 3 (lab maintenance)",
    "",
    "3. Mrs. Kavita Singh",
    "   Subject: English",
    "   Assigned Classes: 8B, 9A, 9B",
    "   Email: kavita.singh@greenfield.edu",
    "   Status: available",
    "   Unavailability: Friday Period 5 (department meeting)",
    "",
    "4. Mr. Anil Verma",
    "   Subject: Social Studies",
    "   Assigned Classes: 8A, 8B, 10B",
    "   Email: anil.verma@greenfield.edu",
    "   Status: available",
    "   Unavailability: None",
    "",
    "5. Ms. Pooja Nair",
    "   Subject: Computer Science",
    "   Assigned Classes: 9A, 9B, 10A, 10B",
    "   Email: pooja.nair@greenfield.edu",
    "   Status: available",
    "   Unavailability: Tuesday Period 2 (training session)",
    "",
    "Notes: All teachers are available as substitutes for adjacent subjects.",
    "Contact HR for emergency leave requests.",
])

# ── Timetable Schedule ────────────────────────────────────────────────────────
make_pdf("timetable_schedule_greenfield.pdf", [
    "MASTER TIMETABLE — Greenfield Public School",
    "Academic Year: 2024-2025  |  Term 2",
    "",
    "CLASS 8A",
    "  Period 1 | 08:00-08:45 | Mathematics    | Dr. Sunita Mehta   | Room 201",
    "  Period 2 | 08:45-09:30 | Science        | Prof. Rajesh Gupta | Science Lab",
    "  Period 3 | 09:45-10:30 | English        | Mrs. Kavita Singh  | Room 201",
    "  Period 4 | 10:30-11:15 | Social Studies | Mr. Anil Verma     | Room 201",
    "  Period 5 | 11:30-12:15 | Computer Sci.  | Ms. Pooja Nair     | Computer Lab",
    "",
    "CLASS 8B",
    "  Period 1 | 08:00-08:45 | English        | Mrs. Kavita Singh  | Room 202",
    "  Period 2 | 08:45-09:30 | Mathematics    | Dr. Sunita Mehta   | Room 202",
    "  Period 3 | 09:45-10:30 | Social Studies | Mr. Anil Verma     | Room 202",
    "  Period 4 | 10:30-11:15 | Science        | Prof. Rajesh Gupta | Science Lab",
    "  Period 5 | 11:30-12:15 | Computer Sci.  | Ms. Pooja Nair     | Computer Lab",
    "",
    "CLASS 9A",
    "  Period 1 | 08:00-08:45 | Science        | Prof. Rajesh Gupta | Room 301",
    "  Period 2 | 08:45-09:30 | English        | Mrs. Kavita Singh  | Room 301",
    "  Period 3 | 09:45-10:30 | Mathematics    | Dr. Sunita Mehta   | Room 301",
    "  Period 4 | 10:30-11:15 | Computer Sci.  | Ms. Pooja Nair     | Computer Lab",
    "  Period 5 | 11:30-12:15 | Social Studies | Mr. Anil Verma     | Room 301",
    "",
    "CLASS 9B",
    "  Period 1 | 08:00-08:45 | Computer Sci.  | Ms. Pooja Nair     | Computer Lab",
    "  Period 2 | 08:45-09:30 | Science        | Prof. Rajesh Gupta | Science Lab",
    "  Period 3 | 09:45-10:30 | English        | Mrs. Kavita Singh  | Room 302",
    "  Period 4 | 10:30-11:15 | Mathematics    | Dr. Sunita Mehta   | Room 302",
    "  Period 5 | 11:30-12:15 | Social Studies | Mr. Anil Verma     | Room 302",
    "",
    "Conflict Rules: No teacher assigned to two classes in the same period.",
    "Substitute Pool: All available teachers eligible for cross-subject cover.",
])
