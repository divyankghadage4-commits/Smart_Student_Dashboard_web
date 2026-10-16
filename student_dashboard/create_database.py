"""
Run this file to create or recreate the SQLite database with full sample data.
Usage: python create_database.py
"""
import os
import sqlite3
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "database.db")
UPLOADS_DIR = os.path.join(BASE_DIR, "static", "uploads")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOADS_DIR, "assignments"), exist_ok=True)
os.makedirs(os.path.join(UPLOADS_DIR, "documents"), exist_ok=True)
os.makedirs(os.path.join(UPLOADS_DIR, "resumes"), exist_ok=True)
os.makedirs(os.path.join(UPLOADS_DIR, "avatars"), exist_ok=True)

if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
    except Exception as e:
        print(f"Note: Could not remove old DB directly: {e}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON;")

# ---------------------------------------------------------
# TABLE SCHEMAS
# ---------------------------------------------------------
cursor.executescript("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    roll_number TEXT,
    course TEXT,
    branch TEXT,
    year TEXT,
    semester TEXT,
    email TEXT,
    phone TEXT,
    dob TEXT,
    blood_group TEXT,
    address TEXT,
    admission_year TEXT,
    avatar_url TEXT,
    cgpa REAL DEFAULT 8.5,
    FOREIGN KEY(student_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    date TEXT NOT NULL,
    subject TEXT NOT NULL,
    status TEXT NOT NULL, -- 'Present', 'Absent'
    FOREIGN KEY(student_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    assessment_type TEXT NOT NULL, -- 'Unit Test', 'Mid-Term', 'Practical', 'Assignment', 'Final Exam'
    marks_obtained REAL NOT NULL,
    max_marks REAL NOT NULL,
    date TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    category TEXT NOT NULL, -- 'Academic', 'Examination', 'Event', 'Placement', 'General', 'Emergency'
    priority TEXT NOT NULL DEFAULT 'Medium', -- 'Low', 'Medium', 'High', 'Urgent'
    date TEXT NOT NULL,
    created_by TEXT DEFAULT 'ADMIN01'
);

CREATE TABLE IF NOT EXISTS announcement_reads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    announcement_id INTEGER NOT NULL,
    student_id TEXT NOT NULL,
    read_at TEXT NOT NULL,
    FOREIGN KEY(announcement_id) REFERENCES announcements(id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS clinical_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    date TEXT NOT NULL,
    ward_lab TEXT NOT NULL,
    assigned_hours REAL NOT NULL,
    completed_hours REAL NOT NULL,
    status TEXT NOT NULL, -- 'Scheduled', 'Present', 'Absent', 'Completed'
    FOREIGN KEY(student_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS leave_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    from_date TEXT NOT NULL,
    to_date TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending', 'Approved', 'Rejected'
    admin_remarks TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    assigned_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    total_marks REAL NOT NULL,
    attachment_path TEXT,
    created_by TEXT DEFAULT 'ADMIN01'
);

CREATE TABLE IF NOT EXISTS assignment_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    student_id TEXT NOT NULL,
    submission_date TEXT NOT NULL,
    file_path TEXT,
    comments TEXT,
    status TEXT NOT NULL DEFAULT 'Submitted', -- 'Pending', 'Submitted', 'Late', 'Graded'
    marks_obtained REAL,
    FOREIGN KEY(assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL, -- 'Notes', 'Syllabus', 'Exam Documents', 'Circulars', 'Certificates', 'Study Material', 'Important Documents'
    file_path TEXT NOT NULL,
    file_size TEXT DEFAULT '1.2 MB',
    uploaded_date TEXT NOT NULL,
    uploaded_by TEXT DEFAULT 'ADMIN01'
);

CREATE TABLE IF NOT EXISTS student_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    category TEXT NOT NULL, -- 'Programming', 'Technical', 'Soft Skills', 'Certification'
    proficiency_level TEXT DEFAULT 'Intermediate', -- 'Beginner', 'Intermediate', 'Advanced', 'Expert'
    FOREIGN KEY(student_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS placement_drives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    job_role TEXT NOT NULL,
    eligibility_criteria TEXT NOT NULL,
    package_lpa REAL NOT NULL,
    location TEXT NOT NULL,
    deadline TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active' -- 'Active', 'Upcoming', 'Closed'
);

CREATE TABLE IF NOT EXISTS placement_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drive_id INTEGER NOT NULL,
    student_id TEXT NOT NULL,
    applied_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Applied', -- 'Applied', 'Shortlisted', 'Interview', 'Selected', 'Rejected'
    resume_path TEXT,
    FOREIGN KEY(drive_id) REFERENCES placement_drives(id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS library_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    isbn TEXT,
    category TEXT NOT NULL,
    total_copies INTEGER NOT NULL DEFAULT 5,
    available_copies INTEGER NOT NULL DEFAULT 5
);

CREATE TABLE IF NOT EXISTS issued_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    student_id TEXT NOT NULL,
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    return_date TEXT,
    fine_amount REAL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'Issued', -- 'Issued', 'Overdue', 'Returned'
    FOREIGN KEY(book_id) REFERENCES library_books(id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info', -- 'info', 'warning', 'success', 'urgent'
    is_read INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
""")

# ---------------------------------------------------------
# RAW STUDENT DATA MIGRATION
# ---------------------------------------------------------
raw_data = '''
1	240101001	Aga Mohammadsaad Jamir
2	240101002	Babar Atharv Sunil
3	240101004	Bhadi Huda Juber
4	240101006	Bhosale Siddharth Suresh
5	240101007	Chavan Shreya Gajanan
6	240101008	Chavan Shruti Satish
7	240101010	Dange Saniya Vajid
8	240101011	Dange Sifa Jamir
9	240101013	Dixit Pranav Prashant
10	240101014	Gaikwad Sneha Sampat
11	240101015	Gaikwad Vaishnavi Digambar
12	240101016	Ghadage Divyank Sunil
13	240101017	Giri Sanskruti Dattatray
14	240101018	Haral Punam Sharad
15	240101019	Ingole Dattatray Jyotiba
16	240101020	Jadhav Sahil Krishna
17	240101021	Jadhav Sakshi Santosh
18	240101022	Jadhav Santoshi Popat
19	240101023	Jadhav Shivam Vinayak
20	240101024	Jadhav Shraddha Uttam
21	240101025	Jagdale Pratiksha Ganesh
22	240101026	Kadam Shravani Shankar
23	240101027	Kalel Chaitanya Anil
24	240101029	Mane Juilee Kiran
25	240101030	Mane Mayuresh Suresh
26	240101031	Mende Dharshan Ashok
27	240101032	Mogare Swaraj Sharad
28	240101033	Mohite Pranali Dhanaji
29	240101034	More Sanika Laxman
30	240101035	Motiwale Sajida Riyaz
31	240101036	Mujawar Alfiya Firoj
32	240101037	Panikar Pranali Manikuttan
33	240101038	Patel Saniya Shabuddin
34	240101039	Patel Abhishek Prafulla
35	240101040	Patel Aditya Vijay
36	240101041	Patel Nikita Tukaram
37	240101042	Patel Vedant Vinod
38	240101043	Pawar Aryan Dattatray
39	240101044	Pawar Atharv Nandkumar
40	240101045	Pawar Gayatri Satish
41	240101046	Pawar Omkar Dinkar
42	240101047	Pawar Yash Hanmant
43	240101048	Phalle Mansvi Avinash
44	240101049	Sawant Pradnya Pradip
45	240101050	Sawant Sharvari Abhijit
46	240101051	Shaikh Aman Adam
47	240101052	Shaligram Saurabh Nitin
48	240101053	Shelar Rushikesh Ramchandra
49	240101054	Shembade Kiran Dhanaji
50	240101055	Shevale Shivraj Dattatray
51	240101056	Shinde Akshata Tukaram
52	240101057	Shinde Parth Maheshkumar
53	240101058	Shinde Shruti Maheshkumar
54	240101059	Surve Sakshi Govinda
55	240101062	Umardand Shruti Uttam
56	240101063	Vankhande Sharvar Prafullkumar
57	240101064	Vedpathak Shravani kiran
58	240101065	Yadav Shrutika Sandip
59	240101066	Jadhav Atharv Vinayak
60	240101067	Shaikh Sahid S.
61	240101068	Kureshi Abdulkalam A.
62	230101069	Desai Prathmesh Hanmant
63	230101070	Kolekar Sahil Vikas
64	230101071	Kumbhar Shravan Shankar
65	230101072	Kale Pavan Prakash
66	250201001	Jadhav Girija Vikas
67	250201002	Patel Anjum Sadik
68	250201003	Pol Vedantika Shankar
69	250201004	Thombare Vaishnavi Dipak
70	250201005	Patel Riya Hanmantrao
72	250201007	Supekar Sanket Ramesh
73	250201008	Awatade Sneha Jayram
74	250201009	Kale Viraj Gunvant
75	250201010	Lad Mansvi Sanjay
76	250201011	Bhandare Aditi Rajendra
77	250201012	Ingale Manali Vishwas
'''

students_list = []
for line in raw_data.strip().split('\n'):
    parts = line.split('\t')
    if len(parts) >= 3:
        students_list.append({
            "roll": parts[1].strip(),
            "name": parts[2].strip()
        })

default_student_pass = generate_password_hash("pass123")
default_admin_pass = generate_password_hash("admin123")
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Insert Admin
cursor.execute(
    "INSERT INTO users (user_id, password_hash, name, role, created_at) VALUES (?, ?, ?, ?, ?)",
    ("ADMIN01", default_admin_pass, "System Admin", "admin", now_str)
)

subjects = [
    "Computer Networks", "Operating Systems", "Database Systems", 
    "Software Engineering", "Artificial Intelligence", "Web Technologies"
]

wards = ["OS Lab", "CN Lab", "DBMS Lab", "AI Lab", "Software Testing Lab", "Cloud Computing Lab"]

blood_groups = ["O+", "A+", "B+", "AB+", "O-", "A-"]

# Insert Students
for idx, student in enumerate(students_list):
    sid = student["roll"]
    name = student["name"]
    first_name = name.split()[0].lower()
    email = f"{first_name}.{sid[-3:]}@university.edu"
    phone = f"98{random.randint(10000000, 99999999)}"
    dob = f"{random.randint(2002, 2005)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    blood = random.choice(blood_groups)
    
    # User entry
    cursor.execute(
        "INSERT INTO users (user_id, password_hash, name, role, created_at) VALUES (?, ?, ?, ?, ?)",
        (sid, default_student_pass, name, "student", now_str)
    )
    
    # Student profile
    cursor.execute(
        """INSERT INTO students 
           (student_id, roll_number, course, branch, year, semester, email, phone, dob, blood_group, address, admission_year, cgpa) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (sid, sid, "B.Tech", "Computer Science", "3rd Year", "Sem 6", email, phone, dob, blood, "Karad, Maharashtra", "2023", round(random.uniform(7.2, 9.8), 2))
    )

    # 1. Attendance Records (Last 15 days)
    for day in range(1, 16):
        date_str = (datetime.now() - timedelta(days=15 - day)).strftime("%Y-%m-%d")
        sub = subjects[day % len(subjects)]
        # Make student 240101001 & 240101002 have ~85% attendance
        status = "Present" if random.random() < 0.85 else "Absent"
        cursor.execute(
            "INSERT INTO attendance (student_id, date, subject, status) VALUES (?, ?, ?, ?)",
            (sid, date_str, sub, status)
        )

    # 2. Assessments
    for sub in subjects[:4]:
        marks = random.randint(14, 20)
        cursor.execute(
            "INSERT INTO assessments (student_id, subject, assessment_type, marks_obtained, max_marks, date) VALUES (?, ?, ?, ?, ?, ?)",
            (sid, sub, "Unit Test", marks, 20, "2026-06-10")
        )
        mid_marks = random.randint(32, 50)
        cursor.execute(
            "INSERT INTO assessments (student_id, subject, assessment_type, marks_obtained, max_marks, date) VALUES (?, ?, ?, ?, ?, ?)",
            (sid, sub, "Mid-Term", mid_marks, 50, "2026-06-25")
        )

    # 3. Clinical / Lab Postings
    for c_idx in range(4):
        c_date = (datetime.now() - timedelta(days=c_idx * 3)).strftime("%Y-%m-%d")
        ward = wards[c_idx % len(wards)]
        c_status = "Completed" if c_idx > 0 else "Scheduled"
        cursor.execute(
            "INSERT INTO clinical_attendance (student_id, date, ward_lab, assigned_hours, completed_hours, status) VALUES (?, ?, ?, ?, ?, ?)",
            (sid, c_date, ward, 4.0, 4.0 if c_status == "Completed" else 0.0, c_status)
        )

    # 4. Student Skills
    cursor.execute("INSERT INTO student_skills (student_id, skill_name, category, proficiency_level) VALUES (?, ?, ?, ?)",
                   (sid, "Python", "Programming", "Advanced"))
    cursor.execute("INSERT INTO student_skills (student_id, skill_name, category, proficiency_level) VALUES (?, ?, ?, ?)",
                   (sid, "SQL & Database", "Technical", "Intermediate"))
    cursor.execute("INSERT INTO student_skills (student_id, skill_name, category, proficiency_level) VALUES (?, ?, ?, ?)",
                   (sid, "Problem Solving", "Soft Skills", "Advanced"))

# ---------------------------------------------------------
# GLOBAL MODULES DATA (ANNOUNCEMENTS, ASSIGNMENTS, DOCUMENTS, PLACEMENT DRIVES, LIBRARY)
# ---------------------------------------------------------

# Announcements
announcements_data = [
    ("Mid-Semester Examination Schedule Announced", "The Mid-Semester exams for B.Tech 3rd Year will commence from August 10, 2026. Hall tickets are available for download in the portal.", "Examination", "High", "2026-07-20"),
    ("Campus Placement Drive: TechCorp India", "TechCorp India is visiting our campus for Software Engineer roles with 12 LPA CTC. Eligible students (CGPA >= 7.5) must register by July 28.", "Placement", "Urgent", "2026-07-18"),
    ("Annual Hackathon 2026 Registration Open", "Participate in HackSprint 2026! Cash prizes up to Rs 1,00,000. Form teams of 4 and register via the portal link.", "Event", "Medium", "2026-07-15"),
    ("Library Timings Extended for Exam Season", "The central library will remain open until 11:00 PM starting July 25 to assist students preparing for upcoming examinations.", "Academic", "Low", "2026-07-12"),
    ("Submission Deadline for Computer Networks Assignment", "All 3rd Year students must submit Assignment #2 by July 25, 2026 before 11:59 PM.", "Academic", "High", "2026-07-10")
]

for title, msg, cat, prio, dt in announcements_data:
    cursor.execute(
        "INSERT INTO announcements (title, message, category, priority, date, created_by) VALUES (?, ?, ?, ?, ?, ?)",
        (title, msg, cat, prio, dt, "ADMIN01")
    )

# Assignments
assignments_data = [
    ("Computer Networks", "Assignment 1: TCP/IP & Socket Programming", "Implement a simple Multi-client Chat Server in Python using socket API. Include socket bind, listen, and accept implementation.", "2026-07-10", "2026-07-25", 50),
    ("Operating Systems", "Assignment 2: Process Scheduling Algorithms", "Write programs to simulate FCFS, SJF, and Round Robin scheduling algorithms. Calculate average waiting time and turnaround time.", "2026-07-12", "2026-07-28", 50),
    ("Database Systems", "Assignment 1: ER Diagram & Normalization", "Design ER diagram for a University Management System and normalize schema up to 3NF/BCNF with SQL statements.", "2026-07-05", "2026-07-20", 30),
    ("Artificial Intelligence", "Mini Project: Search Algorithms", "Implement A* Search and BFS algorithms to solve 8-Puzzle problem with heuristics comparison.", "2026-07-14", "2026-08-05", 100)
]

for sub, title, desc, adate, ddate, marks in assignments_data:
    cursor.execute(
        "INSERT INTO assignments (subject, title, description, assigned_date, due_date, total_marks, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sub, title, desc, adate, ddate, marks, "ADMIN01")
    )

# Seed Submissions for first student (240101001)
cursor.execute(
    "INSERT INTO assignment_submissions (assignment_id, student_id, submission_date, file_path, comments, status, marks_obtained) VALUES (?, ?, ?, ?, ?, ?, ?)",
    (3, "240101001", "2026-07-19", "uploads/assignments/db_assignment1_240101001.pdf", "Submitted on time.", "Graded", 28.5)
)
cursor.execute(
    "INSERT INTO assignment_submissions (assignment_id, student_id, submission_date, file_path, comments, status) VALUES (?, ?, ?, ?, ?, ?)",
    (1, "240101001", "2026-07-21", "uploads/assignments/cn_socket_240101001.zip", "Completed chat server code.", "Submitted")
)

# Documents
documents_data = [
    ("Computer Networks Lecture Notes - Unit 1 to 3", "Comprehensive notes covering OSI Model, TCP/IP, Ethernet, and Routing protocols.", "Notes", "notes_cn_unit1_3.pdf", "4.2 MB", "2026-07-01"),
    ("B.Tech CSE 6th Semester Syllabus 2026", "Official course curriculum, exam pattern, reference books, and lab regulations.", "Syllabus", "cse_sem6_syllabus.pdf", "1.5 MB", "2026-06-15"),
    ("Operating Systems Lab Manual & Practice Code", "Lab exercises for process management, semaphores, deadlock detection, and memory allocation.", "Study Material", "os_lab_manual.pdf", "3.1 MB", "2026-07-05"),
    ("Mid-Term Exam Time Table & Seating Plan", "Detailed schedule and room allocations for Mid-Semester examinations.", "Exam Documents", "midterm_exam_schedule.pdf", "850 KB", "2026-07-15"),
    ("NOC Certificate Template for Internship", "Official format for applying No Objection Certificate for summer industry training.", "Certificates", "noc_format.docx", "350 KB", "2026-07-02")
]

for title, desc, cat, path, sz, dt in documents_data:
    cursor.execute(
        "INSERT INTO documents (title, description, category, file_path, file_size, uploaded_date, uploaded_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, desc, cat, f"uploads/documents/{path}", sz, dt, "ADMIN01")
    )

# Placement Drives
drives_data = [
    ("TechCorp Systems", "Software Development Engineer (SDE-1)", "B.Tech CSE/IT with CGPA >= 7.5, No Active Backlogs", 12.0, "Pune / Bangalore", "2026-07-28", "Active"),
    ("Infosys Limited", "System Engineer Specialist", "B.Tech all branches with CGPA >= 6.5", 6.5, "Pune / Hyderabad", "2026-08-05", "Active"),
    ("Cognizant Technology", "GenC Next Developer", "B.Tech CSE/ECE with CGPA >= 7.0", 8.0, "Mumbai / Remote", "2026-08-15", "Upcoming"),
    ("Tata Consultancy Services (TCS)", "Ninja / Digital Developer", "B.Tech all branches", 7.0, "Pan India", "2026-07-10", "Closed")
]

for comp, role, elig, pkg, loc, dline, st in drives_data:
    cursor.execute(
        "INSERT INTO placement_drives (company_name, job_role, eligibility_criteria, package_lpa, location, deadline, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (comp, role, elig, pkg, loc, dline, st)
    )

# Seed Placement Applications for 240101001
cursor.execute(
    "INSERT INTO placement_applications (drive_id, student_id, applied_date, status, resume_path) VALUES (?, ?, ?, ?, ?)",
    (1, "240101001", "2026-07-19", "Shortlisted", "uploads/resumes/resume_240101001.pdf")
)
cursor.execute(
    "INSERT INTO placement_applications (drive_id, student_id, applied_date, status, resume_path) VALUES (?, ?, ?, ?, ?)",
    (4, "240101001", "2026-07-08", "Applied", "uploads/resumes/resume_240101001.pdf")
)

# Library Books
books_data = [
    ("Computer Networking: A Top-Down Approach", "James F. Kurose & Keith W. Ross", "978-0133594140", "Computer Science", 10, 7),
    ("Operating System Concepts", "Abraham Silberschatz, Peter B. Galvin", "978-1118063330", "Computer Science", 8, 4),
    ("Database System Concepts", "Henry F. Korth & S. Sudarshan", "978-0073523323", "Database", 12, 9),
    ("Artificial Intelligence: A Modern Approach", "Stuart Russell & Peter Norvig", "978-0134610993", "AI & Robotics", 6, 2),
    ("Clean Code: A Handbook of Agile Software Craftsmanship", "Robert C. Martin", "978-0132350884", "Software Engineering", 5, 3)
]

for title, author, isbn, cat, tot, avail in books_data:
    cursor.execute(
        "INSERT INTO library_books (title, author, isbn, category, total_copies, available_copies) VALUES (?, ?, ?, ?, ?, ?)",
        (title, author, isbn, cat, tot, avail)
    )

# Seed Issued Books for 240101001
cursor.execute(
    "INSERT INTO issued_books (book_id, student_id, issue_date, due_date, status) VALUES (?, ?, ?, ?, ?)",
    (1, "240101001", "2026-07-05", "2026-07-25", "Issued")
)
cursor.execute(
    "INSERT INTO issued_books (book_id, student_id, issue_date, due_date, fine_amount, status) VALUES (?, ?, ?, ?, ?, ?)",
    (2, "240101001", "2026-06-15", "2026-07-05", 50.0, "Overdue")
)

# Leave Applications
cursor.execute(
    "INSERT INTO leave_applications (student_id, from_date, to_date, reason, status, admin_remarks, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
    ("240101001", "2026-06-01", "2026-06-03", "Medical Leave due to Viral Fever", "Approved", "Granted. Please submit medical certificate.", "2026-05-31")
)
cursor.execute(
    "INSERT INTO leave_applications (student_id, from_date, to_date, reason, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
    ("240101001", "2026-07-26", "2026-07-27", "Attending National Level Hackathon Competition", "Pending", "2026-07-21")
)
cursor.execute(
    "INSERT INTO leave_applications (student_id, from_date, to_date, reason, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
    ("240101002", "2026-07-10", "2026-07-11", "Family Event", "Approved", "2026-07-08")
)

# Seed Notifications for 240101001
notifications_data = [
    ("240101001", "Shortlisted for TechCorp Drive", "Congratulations! You have been shortlisted for the online technical assessment.", "success", 0, "2026-07-20 10:30:00"),
    ("240101001", "Library Book Overdue Warning", "Book 'Operating System Concepts' is overdue by 16 days. Current fine: Rs 50.", "warning", 0, "2026-07-19 09:00:00"),
    ("240101001", "New Assignment Posted", "Assignment 2 for Operating Systems has been published. Due on July 28.", "info", 1, "2026-07-12 14:15:00")
]

for uid, title, msg, ntype, read, cat_dt in notifications_data:
    cursor.execute(
        "INSERT INTO notifications (user_id, title, message, type, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (uid, title, msg, ntype, read, cat_dt)
    )

conn.commit()
conn.close()

print("=" * 60)
print("SQLite Database created successfully at: data/database.db")
print("All 16 tables initialized with sample data for 14 modules.")
print("Sample Student Credentials:")
print("  ID: 240101001  | Pass: pass123")
print("  ID: 240101002  | Pass: pass123")
print("Sample Admin Credentials:")
print("  ID: ADMIN01    | Pass: admin123")
print("=" * 60)
