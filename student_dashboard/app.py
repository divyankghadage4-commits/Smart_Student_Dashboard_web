"""
Student Academic Dashboard - Flask Backend with SQLite and Flask-SQLAlchemy
"""
import os
import io
import pandas as pd
from functools import wraps
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for, session, jsonify, send_file
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from config import Config
from database import db
from models import (
    Department, User, Student, Admin, AcademicYear, Semester, Subject,
    DailyAttendance, Attendance, AttendanceSubject, Assessment, Result, ResultSubject,
    MDMFaculty, ImportHistory, Announcement, AnnouncementRead, ClinicalAttendance,
    LeaveApplication, Assignment, AssignmentSubmission, Document,
    StudentSkill, PlacementDrive, PlacementApplication, LibraryBook,
    IssuedBook, Notification
)
from utils.excel_importer import ExcelImportService

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Helper function to check allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'zip', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create uploads directories on startup
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
for sub in ["assignments", "documents", "resumes", "avatars"]:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], sub), exist_ok=True)


# ---------------------------------------------------------------------
# AUTHENTICATION & DECORATORS
# ---------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "student_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "student_id" not in session or session.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------
# INITIAL DATABASE SETUP AND IMPORT
# ---------------------------------------------------------------------
def seed_other_tables(cse_dept_id, get_or_create_subject):
    # Seed Assignments
    if Assignment.query.first() is None:
        assignments_data = [
            ("Computer Networks", "Assignment 1: TCP/IP & Socket Programming", "Implement a simple Multi-client Chat Server in Python using socket API. Include socket bind, listen, and accept implementation.", "2026-07-10", "2026-07-25", 50.0),
            ("Operating Systems", "Assignment 2: Process Scheduling Algorithms", "Write programs to simulate FCFS, SJF, and Round Robin scheduling algorithms. Calculate average waiting time and turnaround time.", "2026-07-12", "2026-07-28", 50.0),
            ("Database Systems", "Assignment 1: ER Diagram & Normalization", "Design ER diagram for a University Management System and normalize schema up to 3NF/BCNF with SQL statements.", "2026-07-05", "2026-07-20", 30.0),
            ("Artificial Intelligence", "Mini Project: Search Algorithms", "Implement A* Search and BFS algorithms to solve 8-Puzzle problem with heuristics comparison.", "2026-07-14", "2026-08-05", 100.0)
        ]
        for sub_name, title, desc, adate, ddate, marks in assignments_data:
            sub_id = get_or_create_subject(sub_name)
            a = Assignment(
                subject_id=sub_id,
                title=title,
                description=desc,
                assigned_date=adate,
                due_date=ddate,
                total_marks=marks,
                created_by="ADMIN01"
            )
            db.session.add(a)
        db.session.commit()
        
        # Seed Submissions for student 240101001 if they exist
        st = Student.query.get("240101001")
        if st:
            sub1 = AssignmentSubmission(
                assignment_id=3,
                student_id="240101001",
                submission_date="2026-07-19",
                file_path="uploads/assignments/db_assignment1_240101001.pdf",
                comments="Submitted on time.",
                status="Graded",
                marks_obtained=28.5
            )
            sub2 = AssignmentSubmission(
                assignment_id=1,
                student_id="240101001",
                submission_date="2026-07-21",
                file_path="uploads/assignments/cn_socket_240101001.zip",
                comments="Completed chat server code.",
                status="Submitted"
            )
            db.session.add(sub1)
            db.session.add(sub2)
        db.session.commit()
        
    # Seed Documents
    if Document.query.first() is None:
        documents_data = [
            ("Computer Networks Lecture Notes - Unit 1 to 3", "Comprehensive notes covering OSI Model, TCP/IP, Ethernet, and Routing protocols.", "Notes", "uploads/documents/notes_cn_unit1_3.pdf", "4.2 MB", "2026-07-01"),
            ("B.Tech CSE 6th Semester Syllabus 2026", "Official course curriculum, exam pattern, reference books, and lab regulations.", "Syllabus", "uploads/documents/cse_sem6_syllabus.pdf", "1.5 MB", "2026-06-15"),
            ("Operating Systems Lab Manual & Practice Code", "Lab exercises for process management, semaphores, deadlock detection, and memory allocation.", "Study Material", "uploads/documents/os_lab_manual.pdf", "3.1 MB", "2026-07-05"),
            ("Mid-Term Exam Time Table & Seating Plan", "Detailed schedule and room allocations for Mid-Semester examinations.", "Exam Documents", "uploads/documents/midterm_exam_schedule.pdf", "850 KB", "2026-07-15"),
            ("NOC Certificate Template for Internship", "Official format for applying No Objection Certificate for summer industry training.", "Certificates", "uploads/documents/noc_format.docx", "350 KB", "2026-07-02")
        ]
        for title, desc, cat, path, sz, dt in documents_data:
            d = Document(
                title=title,
                description=desc,
                category=cat,
                file_path=path,
                file_size=sz,
                uploaded_date=dt,
                uploaded_by="ADMIN01"
            )
            db.session.add(d)
        db.session.commit()
        
    # Seed Placement Drives
    if PlacementDrive.query.first() is None:
        drives_data = [
            ("TechCorp Systems", "Software Development Engineer (SDE-1)", "B.Tech CSE/IT with CGPA >= 7.5, No Active Backlogs", 12.0, "Pune / Bangalore", "2026-07-28", "Active"),
            ("Infosys Limited", "System Engineer Specialist", "B.Tech all branches with CGPA >= 6.5", 6.5, "Pune / Hyderabad", "2026-08-05", "Active"),
            ("Cognizant Technology", "GenC Next Developer", "B.Tech CSE/ECE with CGPA >= 7.0", 8.0, "Mumbai / Remote", "2026-08-15", "Upcoming"),
            ("Tata Consultancy Services (TCS)", "Ninja / Digital Developer", "B.Tech all branches", 7.0, "Pan India", "2026-07-10", "Closed")
        ]
        for comp, role, elig, pkg, loc, dline, st in drives_data:
            pd = PlacementDrive(
                company_name=comp,
                job_role=role,
                eligibility_criteria=elig,
                package_lpa=pkg,
                location=loc,
                deadline=dline,
                status=st
            )
            db.session.add(pd)
        db.session.commit()
        
        # Seed placement apps for 240101001 if they exist
        st = Student.query.get("240101001")
        if st:
            pa1 = PlacementApplication(
                drive_id=1,
                student_id="240101001",
                applied_date="2026-07-19",
                status="Shortlisted",
                resume_path="uploads/resumes/resume_240101001.pdf"
            )
            pa2 = PlacementApplication(
                drive_id=4,
                student_id="240101001",
                applied_date="2026-07-08",
                status="Applied",
                resume_path="uploads/resumes/resume_240101001.pdf"
            )
            db.session.add(pa1)
            db.session.add(pa2)
        db.session.commit()
        
    # Seed Library Books
    if LibraryBook.query.first() is None:
        books_data = [
            ("Computer Networking: A Top-Down Approach", "James F. Kurose & Keith W. Ross", "978-0133594140", "Computer Science", 10, 7),
            ("Operating System Concepts", "Abraham Silberschatz, Peter B. Galvin", "978-1118063330", "Computer Science", 8, 4),
            ("Database System Concepts", "Henry F. Korth & S. Sudarshan", "978-0073523323", "Database", 12, 9),
            ("Artificial Intelligence: A Modern Approach", "Stuart Russell & Peter Norvig", "978-0134610993", "AI & Robotics", 6, 2),
            ("Clean Code: A Handbook of Agile Software Craftsmanship", "Robert C. Martin", "978-0132350884", "Software Engineering", 5, 3)
        ]
        for title, author, isbn, cat, tot, avail in books_data:
            b = LibraryBook(
                title=title,
                author=author,
                isbn=isbn,
                category=cat,
                total_copies=tot,
                available_copies=avail
            )
            db.session.add(b)
        db.session.commit()
        
        # Seed issued books for 240101001 if they exist
        st = Student.query.get("240101001")
        if st:
            ib1 = IssuedBook(
                book_id=1,
                student_id="240101001",
                issue_date="2026-07-05",
                due_date="2026-07-25",
                status="Issued"
            )
            ib2 = IssuedBook(
                book_id=2,
                student_id="240101001",
                issue_date="2026-06-15",
                due_date="2026-07-05",
                fine_amount=50.0,
                status="Overdue"
            )
            db.session.add(ib1)
            db.session.add(ib2)
        db.session.commit()
        
    # Seed skills for 240101001 if they exist
    st = Student.query.get("240101001")
    if st and StudentSkill.query.filter_by(student_id="240101001").first() is None:
        sk1 = StudentSkill(student_id="240101001", skill_name="Python", category="Programming", proficiency_level="Advanced")
        sk2 = StudentSkill(student_id="240101001", skill_name="SQL & Database", category="Technical", proficiency_level="Intermediate")
        sk3 = StudentSkill(student_id="240101001", skill_name="Problem Solving", category="Soft Skills", proficiency_level="Advanced")
        db.session.add(sk1)
        db.session.add(sk2)
        db.session.add(sk3)
        db.session.commit()

    # Seed Notifications for 240101001
    if st and Notification.query.filter_by(user_id="240101001").first() is None:
        notifications_data = [
            ("240101001", "Shortlisted for TechCorp Drive", "Congratulations! You have been shortlisted for the online technical assessment.", "success", 0, "2026-07-20 10:30:00"),
            ("240101001", "Library Book Overdue Warning", "Book 'Operating System Concepts' is overdue by 16 days. Current fine: Rs 50.", "warning", 0, "2026-07-19 09:00:00"),
            ("240101001", "New Assignment Posted", "Assignment 2 for Operating Systems has been published. Due on July 28.", "info", 1, "2026-07-12 14:15:00")
        ]
        for uid, title, msg, ntype, read, cat_dt in notifications_data:
            n = Notification(
                user_id=uid,
                title=title,
                message=msg,
                type=ntype,
                is_read=read,
                created_at=cat_dt
            )
            db.session.add(n)
        db.session.commit()


def import_excel_if_empty():
    # If the user table is already populated, skip auto-import
    if User.query.first() is not None:
        return

    excel_path = os.path.join(app.config['BASE_DIR'], 'data', 'students_data.xlsx')
    if not os.path.exists(excel_path):
        print(f"No excel data found at {excel_path}. Creating clean database.")
        return

    print(f"Excel database found! Automatically importing records from {excel_path}...")
    try:
        xl = pd.ExcelFile(excel_path)
        
        # 1. Create default CSE department
        cse_dept = Department.query.filter_by(code='CSE').first()
        if not cse_dept:
            cse_dept = Department(code='CSE', name='Computer Science & Engineering')
            db.session.add(cse_dept)
            db.session.commit()
            
        academic_years = {}
        semesters = {}
        subjects = {}
        
        def get_or_create_year(year_name):
            if not year_name:
                return None
            year_name = str(year_name).strip()
            if year_name not in academic_years:
                ay = AcademicYear.query.filter_by(name=year_name).first()
                if not ay:
                    ay = AcademicYear(name=year_name)
                    db.session.add(ay)
                    db.session.commit()
                academic_years[year_name] = ay.id
            return academic_years[year_name]
            
        def get_or_create_semester(sem_name):
            if not sem_name:
                return None
            sem_name = str(sem_name).strip()
            if sem_name not in semesters:
                sem = Semester.query.filter_by(name=sem_name).first()
                if not sem:
                    sem = Semester(name=sem_name)
                    db.session.add(sem)
                    db.session.commit()
                semesters[sem_name] = sem.id
            return semesters[sem_name]
            
        def get_or_create_subject(sub_name):
            if not sub_name:
                return None
            sub_name = str(sub_name).strip()
            if sub_name not in subjects:
                sub = Subject.query.filter_by(name=sub_name).first()
                if not sub:
                    # Generate unique subject code
                    words = [w for w in sub_name.split() if w.isalnum()]
                    code = "".join([w[0] for w in words]).upper() if words else "SUB"
                    base_code = code
                    count = 1
                    while Subject.query.filter_by(code=code).first():
                        code = f"{base_code}{count}"
                        count += 1
                    sub = Subject(code=code, name=sub_name, department_id=cse_dept.id)
                    db.session.add(sub)
                    db.session.commit()
                subjects[sub_name] = sub.id
            return subjects[sub_name]

        # Import Login (Users)
        if 'Login' in xl.sheet_names:
            df_login = pd.read_excel(excel_path, sheet_name='Login')
            df_login.columns = [c.strip() for c in df_login.columns]
            for _, row in df_login.iterrows():
                uid = str(row['StudentID']).strip()
                pwd = str(row['Password']).strip()
                name = str(row['Name']).strip()
                role = str(row['Role']).strip()
                if not User.query.get(uid):
                    u = User(id=uid, password_hash=pwd, name=name, role=role)
                    db.session.add(u)
            db.session.commit()
            
        # Import Profile (Students)
        if 'Profile' in xl.sheet_names:
            df_profile = pd.read_excel(excel_path, sheet_name='Profile')
            df_profile.columns = [c.strip() for c in df_profile.columns]
            for _, row in df_profile.iterrows():
                sid = str(row['StudentID']).strip()
                name = str(row['Name']).strip()
                course = str(row['Course']).strip() if 'Course' in row else 'B.Tech'
                year_name = str(row['Year']).strip() if 'Year' in row else '3rd Year'
                email = str(row['Email']).strip() if 'Email' in row else ''
                phone = str(row['Phone']).strip() if 'Phone' in row else ''
                address = str(row['Address']).strip() if 'Address' in row else ''
                dob = str(row['DOB']).strip() if 'DOB' in row else ''
                blood = str(row['BloodGroup']).strip() if 'BloodGroup' in row else ''
                prn = str(row['PRN']).strip() if 'PRN' in row else (str(row['PRNNumber']).strip() if 'PRNNumber' in row else (str(row['PRN Number']).strip() if 'PRN Number' in row else ''))
                if prn == 'nan':
                    prn = ''
                
                u = User.query.get(sid)
                if u and u.role == 'student':
                    year_id = get_or_create_year(year_name)
                    sem_id = get_or_create_semester('Sem 6') # Default to Sem 6
                    st = Student(
                        student_id=sid,
                        roll_number=sid,
                        prn_number=prn,
                        course=course,
                        year_id=year_id,
                        semester_id=sem_id,
                        email=email,
                        phone=phone,
                        dob=dob,
                        blood_group=blood,
                        address=address,
                        admission_year='2023',
                        cgpa=8.5,
                        department_id=cse_dept.id
                    )
                    db.session.add(st)
            
            # Ensure admin accounts have their profile
            admins = User.query.filter_by(role='admin').all()
            for adm in admins:
                if not Admin.query.get(adm.id):
                    a = Admin(admin_id=adm.id, department_id=cse_dept.id)
                    db.session.add(a)
            db.session.commit()
            
        # Import Attendance
        if 'Attendance' in xl.sheet_names:
            df_att = pd.read_excel(excel_path, sheet_name='Attendance')
            df_att.columns = [c.strip() for c in df_att.columns]
            for _, row in df_att.iterrows():
                sid = str(row['StudentID']).strip()
                dt_val = str(row['Date']).strip()
                sub_name = str(row['Subject']).strip()
                status = str(row['Status']).strip()
                
                sub_id = get_or_create_subject(sub_name)
                if Student.query.get(sid):
                    att = Attendance(student_id=sid, date=dt_val, subject_id=sub_id, status=status)
                    db.session.add(att)
            db.session.commit()
            
        # Import Assessment
        if 'Assessment' in xl.sheet_names:
            df_ass = pd.read_excel(excel_path, sheet_name='Assessment')
            df_ass.columns = [c.strip() for c in df_ass.columns]
            for _, row in df_ass.iterrows():
                sid = str(row['StudentID']).strip()
                sub_name = str(row['Subject']).strip()
                atype = str(row['Type']).strip()
                marks = float(row['Marks'])
                max_marks = float(row['MaxMarks'])
                dt_val = str(row['Date']).strip()
                
                sub_id = get_or_create_subject(sub_name)
                if Student.query.get(sid):
                    ass = Assessment(
                        student_id=sid,
                        subject_id=sub_id,
                        assessment_type=atype,
                        marks_obtained=marks,
                        max_marks=max_marks,
                        date=dt_val
                    )
                    db.session.add(ass)
            db.session.commit()
            
        # Import Announcement
        if 'Announcement' in xl.sheet_names:
            df_ann = pd.read_excel(excel_path, sheet_name='Announcement')
            df_ann.columns = [c.strip() for c in df_ann.columns]
            for _, row in df_ann.iterrows():
                title = str(row['Title']).strip()
                msg = str(row['Message']).strip()
                dt_val = str(row['Date']).strip()
                
                ann = Announcement(
                    title=title,
                    message=msg,
                    category='General',
                    priority='Medium',
                    date=dt_val,
                    created_by='ADMIN01'
                )
                db.session.add(ann)
            db.session.commit()
            
        # Import Clinical
        if 'Clinical' in xl.sheet_names:
            df_clin = pd.read_excel(excel_path, sheet_name='Clinical')
            df_clin.columns = [c.strip() for c in df_clin.columns]
            for _, row in df_clin.iterrows():
                sid = str(row['StudentID']).strip()
                dt_val = str(row['Date']).strip()
                ward = str(row['Ward']).strip()
                hours = float(row['Hours'])
                status = str(row['Status']).strip()
                
                if Student.query.get(sid):
                    clin = ClinicalAttendance(
                        student_id=sid,
                        date=dt_val,
                        ward_lab=ward,
                        assigned_hours=hours,
                        completed_hours=hours if status == 'Completed' else 0.0,
                        status=status
                    )
                    db.session.add(clin)
            db.session.commit()
            
        # Import Leave
        if 'Leave' in xl.sheet_names:
            df_leave = pd.read_excel(excel_path, sheet_name='Leave')
            df_leave.columns = [c.strip() for c in df_leave.columns]
            for _, row in df_leave.iterrows():
                sid = str(row['StudentID']).strip()
                from_dt = str(row['FromDate']).strip()
                to_dt = str(row['ToDate']).strip()
                reason = str(row['Reason']).strip()
                status = str(row['Status']).strip()
                
                if Student.query.get(sid):
                    lv = LeaveApplication(
                        student_id=sid,
                        from_date=from_dt,
                        to_date=to_dt,
                        reason=reason,
                        status=status,
                        created_at=from_dt
                    )
                    db.session.add(lv)
            db.session.commit()
            
        # Seed other structural elements (Library, Placements, Assignments)
        seed_other_tables(cse_dept.id, get_or_create_subject)
        print("Excel data migration complete!")
    except Exception as e:
        print(f"Error migrating Excel data: {e}")
        db.session.rollback()


with app.app_context():
    db.create_all()
    # Migration: Add prn_number column if not present in students table
    try:
        db.session.execute(db.text("ALTER TABLE students ADD COLUMN prn_number VARCHAR(50)"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # Migration: Add mentor_id column if not present in students table
    try:
        db.session.execute(db.text("ALTER TABLE students ADD COLUMN mentor_id INTEGER REFERENCES mdm_faculties(id) ON DELETE SET NULL"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # Migration: Add last_login_date column if not present in users table
    try:
        db.session.execute(db.text("ALTER TABLE users ADD COLUMN last_login_date VARCHAR(50)"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    import_excel_if_empty()

    # Get CSE Department for ADMIN01 mapping
    cse_dept = Department.query.filter_by(code='CSE').first()
    cse_dept_id = cse_dept.id if cse_dept else None

    # Ensure ADMIN01 password matches "admin123" and is linked to CSE Department
    admin_user = User.query.get("ADMIN01")
    if not admin_user:
        admin_user = User(
            id="ADMIN01",
            password_hash=generate_password_hash("admin123"),
            name="CSE Admin",
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()
    else:
        admin_user.name = "CSE Admin"
        if not check_password_hash(admin_user.password_hash, "admin123"):
            admin_user.password_hash = generate_password_hash("admin123")
        db.session.commit()
        
    admin_profile = Admin.query.get("ADMIN01")
    if not admin_profile:
        admin_profile = Admin(admin_id="ADMIN01", department_id=cse_dept_id)
        db.session.add(admin_profile)
    else:
        admin_profile.department_id = cse_dept_id
    db.session.commit()

    # Ensure HEAD01 (Head Admin) exists and has department_id = None
    head_user = User.query.get("HEAD01")
    if not head_user:
        head_user = User(
            id="HEAD01",
            password_hash=generate_password_hash("admin123"),
            name="Head Admin",
            role="admin"
        )
        db.session.add(head_user)
        db.session.commit()
    else:
        head_user.name = "Head Admin"
        if not check_password_hash(head_user.password_hash, "admin123"):
            head_user.password_hash = generate_password_hash("admin123")
        db.session.commit()

    head_profile = Admin.query.get("HEAD01")
    if not head_profile:
        head_profile = Admin(admin_id="HEAD01", department_id=None)
        db.session.add(head_profile)
    else:
        head_profile.department_id = None
    db.session.commit()
    print("Default Admin profiles (ADMIN01 and HEAD01) verified/seeded.")


# ---------------------------------------------------------------------
# MAIN APP WEB ROUTES
# ---------------------------------------------------------------------
@app.route("/")
def index():
    if "student_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        password = request.form.get("password", "")

        user = User.query.get(student_id)
        if user and check_password_hash(user.password_hash, password):
            user.last_login_date = datetime.now().strftime("%Y-%m-%d")
            db.session.commit()
            
            session["student_id"] = user.id
            session["student_name"] = user.name
            
            if user.role == 'admin':
                session["role"] = 'admin'
                admin_profile = Admin.query.get(user.id)
                if admin_profile and admin_profile.department_id is not None:
                    session["admin_type"] = "dept_admin"
                    session["department_id"] = admin_profile.department_id
                else:
                    session["admin_type"] = "head_admin"
                    session["department_id"] = None
            else:
                session["role"] = 'student'
                session["admin_type"] = ""
                session["department_id"] = None
                
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid Credentials. Please try again."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "student_id" not in session:
        return redirect(url_for("login"))

    student_id = session["student_id"]
    role = session.get("role", "student")
    admin_type = session.get("admin_type", "")

    avatar_url = None
    if role == "student":
        st = Student.query.get(student_id)
        if st:
            avatar_url = st.avatar_url

    return render_template(
        "dashboard.html",
        student_id=student_id,
        student_name=session.get("student_name", "User"),
        role=role,
        admin_type=admin_type,
        avatar_url=avatar_url
    )


# ---------------------------------------------------------------------
# MODULE 1: DASHBOARD SUMMARY API
# ---------------------------------------------------------------------
@app.route("/api/dashboard/summary")
@login_required
def api_dashboard_summary():
    student_id = session["student_id"]
    
    st = Student.query.get(student_id)
    if not st:
        return jsonify({"error": "Student profile not found"}), 404

    # Latest CGPA/SGPA from Results table
    latest_res = Result.query.filter_by(student_id=student_id).order_by(Result.id.desc()).first()
    cgpa_val = latest_res.cgpa if latest_res and latest_res.cgpa else st.cgpa
    sgpa_val = latest_res.sgpa if latest_res and latest_res.sgpa else 0.0

    # Profile summary
    profile_data = {
        "student_id": st.student_id,
        "roll_number": st.roll_number,
        "course": st.course,
        "year": st.academic_year.name if st.academic_year else "",
        "semester": st.semester.name if st.semester else "",
        "email": st.email,
        "phone": st.phone,
        "dob": st.dob,
        "blood_group": st.blood_group,
        "address": st.address,
        "admission_year": st.admission_year,
        "avatar_url": st.avatar_url,
        "cgpa": cgpa_val,
        "sgpa": sgpa_val,
        "mentor_name": st.mentor.name if st.mentor else "Not Assigned",
        "mentor_dept": st.mentor.department if st.mentor else "-",
        "mentor_email": st.mentor.email if st.mentor else "-",
        "mentor_phone": st.mentor.phone if st.mentor else "-",
        "name": st.user.name
    }

    # Attendance overall (read from cumulative attendance summary first)
    cum_att = Attendance.query.filter_by(student_id=student_id).order_by(Attendance.id.desc()).first()
    att_percentage = cum_att.overall_percentage if cum_att else 0.0

    # Pending Assignments
    submitted_ids = [s.assignment_id for s in AssignmentSubmission.query.filter_by(student_id=student_id).all()]
    if submitted_ids:
        pending_assignments = Assignment.query.filter(~Assignment.id.in_(submitted_ids)).count()
    else:
        pending_assignments = Assignment.query.count()

    # Average Assessment Score % (fallback or kept for compatibility)
    assessments = Assessment.query.filter_by(student_id=student_id).all()
    if assessments:
        total_ob = sum(r.marks_obtained for r in assessments)
        total_mx = sum(r.max_marks for r in assessments)
        avg_score = round((total_ob / total_mx) * 100, 1) if total_mx else 0.0
    else:
        avg_score = 0.0

    # Clinical hours completed vs assigned
    clinical = ClinicalAttendance.query.filter_by(student_id=student_id).all()
    completed_clinical_hours = sum(r.completed_hours for r in clinical)
    total_clinical_hours = sum(r.assigned_hours for r in clinical)

    # Issued books count
    issued_count = IssuedBook.query.filter_by(student_id=student_id, status='Issued').count()

    # Upcoming placement drives
    active_drives = PlacementDrive.query.filter_by(status='Active').count()

    # Today's classes schedule (mock dynamic)
    today_schedule = [
        {"time": "09:00 AM - 10:00 AM", "subject": "Computer Networks", "room": "Lab 301", "instructor": "Dr. R. Sharma"},
        {"time": "10:15 AM - 11:15 AM", "subject": "Operating Systems", "room": "Hall B", "instructor": "Prof. S. Patil"},
        {"time": "11:30 AM - 12:30 PM", "subject": "Database Systems", "room": "Lab 102", "instructor": "Dr. A. Verma"},
        {"time": "02:00 PM - 04:00 PM", "subject": "AI & ML Practical", "room": "AI Lab", "instructor": "Prof. M. Kulkarni"}
    ]

    # Recent announcements
    anns = Announcement.query.order_by(Announcement.id.desc()).limit(4).all()
    recent_announcements = []
    for a in anns:
        recent_announcements.append({
            "id": a.id,
            "title": a.title,
            "message": a.message,
            "category": a.category,
            "priority": a.priority,
            "date": a.date,
            "created_by": a.created_by
        })

    # Recent Results
    recent_results = []
    results_records = Result.query.filter_by(student_id=student_id).order_by(Result.id.desc()).limit(3).all()
    for r in results_records:
        recent_results.append({
            "id": r.id,
            "semester": r.semester.name if r.semester else "N/A",
            "exam_type": r.exam_type,
            "sgpa": r.sgpa,
            "cgpa": r.cgpa,
            "status": r.status
        })

    # Unread notifications count
    unread_count = Notification.query.filter_by(user_id=student_id, is_read=0).count()
    pending_leaves = LeaveApplication.query.filter_by(student_id=student_id, status='Pending').count()

    return jsonify({
        "profile": profile_data,
        "overall_attendance": att_percentage,
        "pending_assignments": pending_assignments,
        "avg_assessment_score": avg_score,
        "clinical_hours": {"completed": completed_clinical_hours, "total": total_clinical_hours},
        "issued_books_count": issued_count,
        "active_placement_drives": active_drives,
        "today_schedule": today_schedule,
        "recent_announcements": recent_announcements,
        "recent_results": recent_results,
        "pending_leaves_count": pending_leaves,
        "unread_notifications": unread_count
    })


# ---------------------------------------------------------------------
# MODULE 2: PROFILE API
# ---------------------------------------------------------------------
@app.route("/api/profile", methods=["GET", "PUT"])
@login_required
def api_profile():
    student_id = session["student_id"]
    role = session.get("role", "student")

    if role == "admin":
        user = User.query.get(student_id)
        if not user:
            return jsonify({"error": "Admin not found"}), 404

        if request.method == "GET":
            return jsonify({
                "id": user.id,
                "name": user.name,
                "role": user.role
            })
        elif request.method == "PUT":
            data = request.get_json() or {}
            name = data.get("name", "").strip()
            if not name:
                return jsonify({"success": False, "message": "Name is required."}), 400
            user.name = name
            session["student_name"] = name
            db.session.commit()
            return jsonify({"success": True, "message": "Profile updated successfully!"})
    else:
        st = Student.query.get(student_id)
        if not st:
            return jsonify({"error": "Student not found"}), 404

        if request.method == "GET":
            return jsonify({
                "student_id": st.student_id,
                "roll_number": st.roll_number,
                "prn_number": st.prn_number,
                "course": st.course,
                "year": st.academic_year.name if st.academic_year else "",
                "semester": st.semester.name if st.semester else "",
                "email": st.email,
                "phone": st.phone,
                "dob": st.dob,
                "blood_group": st.blood_group,
                "address": st.address,
                "admission_year": st.admission_year,
                "avatar_url": st.avatar_url,
                "cgpa": st.cgpa,
                "name": st.user.name
            })

        elif request.method == "PUT":
            data = request.get_json() or {}
            st.email = data.get("email", "").strip()
            st.phone = data.get("phone", "").strip()
            st.address = data.get("address", "").strip()
            st.dob = data.get("dob", "").strip()
            st.blood_group = data.get("blood_group", "").strip()
            db.session.commit()
            return jsonify({"success": True, "message": "Profile updated successfully!"})


@app.route("/api/profile/change-password", methods=["POST"])
@login_required
def api_change_password():
    student_id = session["student_id"]
    data = request.get_json() or {}
    old_pass = data.get("old_password", "")
    new_pass = data.get("new_password", "")

    if not old_pass or not new_pass:
        return jsonify({"success": False, "message": "Both old and new passwords are required."}), 400

    user = User.query.get(student_id)
    if not user or not check_password_hash(user.password_hash, old_pass):
        return jsonify({"success": False, "message": "Incorrect existing password."}), 400

    user.password_hash = generate_password_hash(new_pass)
    db.session.commit()
    return jsonify({"success": True, "message": "Password changed successfully!"})


@app.route("/api/profile/avatar", methods=["POST"])
@login_required
def api_upload_avatar():
    student_id = session["student_id"]
    if 'avatar' not in request.files:
        return jsonify({"success": False, "message": "No avatar file provided."}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected."}), 400

    if file and allowed_file(file.filename):
        filename = f"avatar_{student_id}_{secure_filename(file.filename)}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], "avatars", filename)
        file.save(save_path)

        avatar_url = f"/static/uploads/avatars/{filename}"
        st = Student.query.get(student_id)
        if st:
            st.avatar_url = avatar_url
            db.session.commit()
        return jsonify({"success": True, "avatar_url": avatar_url, "message": "Avatar uploaded successfully!"})

    return jsonify({"success": False, "message": "Invalid file type."}), 400


# ---------------------------------------------------------------------
# MODULE 3: ASSIGNMENT API
# ---------------------------------------------------------------------
@app.route("/api/assignments")
@login_required
def api_assignments():
    student_id = session["student_id"]
    assignments = Assignment.query.order_by(Assignment.due_date.asc()).all()

    now = datetime.now().strftime("%Y-%m-%d")
    res = []
    for a in assignments:
        sub = AssignmentSubmission.query.filter_by(assignment_id=a.id, student_id=student_id).first()
        item = {
            "id": a.id,
            "subject": a.subject.name,
            "title": a.title,
            "description": a.description,
            "assigned_date": a.assigned_date,
            "due_date": a.due_date,
            "total_marks": a.total_marks,
            "attachment_path": a.attachment_path,
            "created_by": a.created_by,
            "submission_date": sub.submission_date if sub else None,
            "submission_file": sub.file_path if sub else None,
            "submission_status": sub.status if sub else None,
            "marks_obtained": sub.marks_obtained if sub else None,
            "comments": sub.comments if sub else None,
        }
        if not item["submission_status"]:
            if a.due_date < now:
                item["status"] = "Overdue"
            else:
                item["status"] = "Pending"
        else:
            item["status"] = item["submission_status"]
        res.append(item)

    return jsonify(res)


@app.route("/api/assignments/<int:assignment_id>/submit", methods=["POST"])
@login_required
def api_submit_assignment(assignment_id):
    student_id = session["student_id"]
    comments = request.form.get("comments", "").strip()
    sub_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    file_path = None
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = f"assign_{assignment_id}_{student_id}_{secure_filename(file.filename)}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], "assignments", filename)
            file.save(save_path)
            file_path = f"uploads/assignments/{filename}"

    sub = AssignmentSubmission.query.filter_by(assignment_id=assignment_id, student_id=student_id).first()
    if sub:
        sub.submission_date = sub_date
        if file_path:
            sub.file_path = file_path
        sub.comments = comments
        sub.status = 'Submitted'
    else:
        sub = AssignmentSubmission(
            assignment_id=assignment_id,
            student_id=student_id,
            submission_date=sub_date,
            file_path=file_path,
            comments=comments,
            status='Submitted'
        )
        db.session.add(sub)
    db.session.commit()

    return jsonify({"success": True, "message": "Assignment submitted successfully!"})


# ---------------------------------------------------------------------
# MODULE 4: ANNOUNCEMENTS API
# ---------------------------------------------------------------------
@app.route("/api/announcements")
@login_required
def api_announcements():
    student_id = session["student_id"]
    announcements = Announcement.query.order_by(Announcement.id.desc()).all()
    res = []
    for a in announcements:
        read = AnnouncementRead.query.filter_by(announcement_id=a.id, student_id=student_id).first()
        res.append({
            "id": a.id,
            "title": a.title,
            "message": a.message,
            "category": a.category,
            "priority": a.priority,
            "date": a.date,
            "created_by": a.created_by,
            "is_read": 1 if read else 0
        })
    return jsonify(res)


@app.route("/api/announcements/<int:announcement_id>/mark-read", methods=["POST"])
@login_required
def api_mark_announcement_read(announcement_id):
    student_id = session["student_id"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    read = AnnouncementRead.query.filter_by(announcement_id=announcement_id, student_id=student_id).first()
    if not read:
        read = AnnouncementRead(announcement_id=announcement_id, student_id=student_id, read_at=now_str)
        db.session.add(read)
        db.session.commit()

    return jsonify({"success": True})


# ---------------------------------------------------------------------
# MODULE 5: DOCUMENT MODULE API
# ---------------------------------------------------------------------
@app.route("/api/documents")
@login_required
def api_documents():
    docs = Document.query.order_by(Document.id.desc()).all()
    res = []
    for d in docs:
        res.append({
            "id": d.id,
            "title": d.title,
            "description": d.description,
            "category": d.category,
            "file_path": d.file_path,
            "file_size": d.file_size,
            "uploaded_date": d.uploaded_date,
            "uploaded_by": d.uploaded_by
        })
    return jsonify(res)


# ---------------------------------------------------------------------
# MODULE 6: STUDENT ASSESSMENT API
# ---------------------------------------------------------------------
@app.route("/api/assessment")
@login_required
def api_assessment():
    student_id = session["student_id"]
    assessments = Assessment.query.filter_by(student_id=student_id).order_by(Assessment.date.desc()).all()

    res = []
    for a in assessments:
        pct = round((a.marks_obtained / a.max_marks) * 100, 1) if a.max_marks else 0
        if pct >= 85:
            grade = "A+"
        elif pct >= 75:
            grade = "A"
        elif pct >= 65:
            grade = "B"
        elif pct >= 50:
            grade = "C"
        else:
            grade = "F"
            
        res.append({
            "id": a.id,
            "student_id": a.student_id,
            "subject": a.subject.name,
            "assessment_type": a.assessment_type,
            "marks_obtained": a.marks_obtained,
            "max_marks": a.max_marks,
            "date": a.date,
            "percentage": pct,
            "grade": grade
        })

    return jsonify(res)


# ---------------------------------------------------------------------
# MODULE 7: ATTENDANCE API
# ---------------------------------------------------------------------
@app.route("/api/attendance")
@login_required
def api_attendance():
    student_id = session["student_id"]
    
    # 1. Try cumulative attendance summary
    cum_att = Attendance.query.filter_by(student_id=student_id).order_by(Attendance.id.desc()).first()
    if cum_att:
        percentage = cum_att.overall_percentage
        if percentage >= 75.0:
            attendance_status = "Good"
        elif percentage >= 65.0:
            attendance_status = "Warning"
        else:
            attendance_status = "Critical"

        subject_breakdown = []
        for s in cum_att.subjects:
            total_classes = s.theory_conducted + s.practical_conducted
            attended_classes = s.theory_attended + s.practical_attended
            sub_pct = round((attended_classes / total_classes) * 100, 1) if total_classes else 0.0
            subject_breakdown.append({
                "subject": s.subject_name,
                "total": total_classes,
                "present": attended_classes,
                "percentage": sub_pct,
                "status": "Good" if sub_pct >= 75 else ("Warning" if sub_pct >= 65 else "Critical")
            })

        rec_list = [{
            "id": cum_att.id,
            "student_id": cum_att.student_id,
            "date": cum_att.as_of_date or "N/A",
            "subject": f"Batch: {cum_att.batch or 'General'}",
            "status": cum_att.remark or "Pass"
        }]

        return jsonify({
            "records": rec_list,
            "total": cum_att.total_theory_conducted + cum_att.total_practical_conducted,
            "present": cum_att.total_theory_attended + cum_att.total_practical_attended,
            "absent": (cum_att.total_theory_conducted + cum_att.total_practical_conducted) - (cum_att.total_theory_attended + cum_att.total_practical_attended),
            "percentage": percentage,
            "attendance_status": attendance_status,
            "subject_breakdown": subject_breakdown
        })

    # 2. Fallback to daily logs
    records = DailyAttendance.query.filter_by(student_id=student_id).order_by(DailyAttendance.date.desc()).all()

    rec_list = []
    total = len(records)
    present = 0
    for r in records:
        if r.status == "Present":
            present += 1
        rec_list.append({
            "id": r.id,
            "student_id": r.student_id,
            "date": r.date,
            "subject": r.subject.name,
            "status": r.status
        })

    percentage = round((present / total) * 100, 1) if total else 0.0

    if percentage >= 75.0:
        attendance_status = "Good"
    elif percentage >= 65.0:
        attendance_status = "Warning"
    else:
        attendance_status = "Critical"

    # Subject breakdown
    subject_map = {}
    for r in records:
        s = r.subject.name
        if s not in subject_map:
            subject_map[s] = {"total": 0, "present": 0}
        subject_map[s]["total"] += 1
        if r.status == "Present":
            subject_map[s]["present"] += 1

    subject_breakdown = []
    for sub, val in subject_map.items():
        pct = round((val["present"] / val["total"]) * 100, 1) if val["total"] else 0
        subject_breakdown.append({
            "subject": sub,
            "total": val["total"],
            "present": val["present"],
            "percentage": pct,
            "status": "Good" if pct >= 75 else ("Warning" if pct >= 65 else "Critical")
        })

    return jsonify({
        "records": rec_list,
        "total": total,
        "present": present,
        "absent": total - present,
        "percentage": percentage,
        "attendance_status": attendance_status,
        "subject_breakdown": subject_breakdown
    })


# ---------------------------------------------------------------------
# MODULE 8: PLACEMENT MODULE API
# ---------------------------------------------------------------------
@app.route("/api/placement")
@login_required
def api_placement():
    student_id = session["student_id"]

    skills = StudentSkill.query.filter_by(student_id=student_id).all()
    skills_list = []
    for sk in skills:
        skills_list.append({
            "id": sk.id,
            "skill_name": sk.skill_name,
            "category": sk.category,
            "proficiency_level": sk.proficiency_level
        })

    drives = PlacementDrive.query.order_by(PlacementDrive.id.desc()).all()
    drives_list = []
    for d in drives:
        app_sub = PlacementApplication.query.filter_by(drive_id=d.id, student_id=student_id).first()
        drives_list.append({
            "id": d.id,
            "company_name": d.company_name,
            "job_role": d.job_role,
            "eligibility_criteria": d.eligibility_criteria,
            "package_lpa": d.package_lpa,
            "location": d.location,
            "deadline": d.deadline,
            "status": d.status,
            "application_status": app_sub.status if app_sub else "Not Applied",
            "applied_date": app_sub.applied_date if app_sub else None
        })

    st = Student.query.get(student_id)
    cgpa = st.cgpa if st else 8.0

    total_att = Attendance.query.filter_by(student_id=student_id).count()
    present_att = Attendance.query.filter_by(student_id=student_id, status="Present").count()
    att_pct = round((present_att / total_att) * 100, 1) if total_att else 0.0

    return jsonify({
        "cgpa": cgpa,
        "attendance_percentage": att_pct,
        "eligible": cgpa >= 6.5 and att_pct >= 75.0,
        "skills": skills_list,
        "drives": drives_list
    })


@app.route("/api/placement/skills", methods=["POST", "DELETE"])
@login_required
def api_placement_skills():
    student_id = session["student_id"]

    if request.method == "POST":
        data = request.get_json() or {}
        name = data.get("skill_name", "").strip()
        category = data.get("category", "Technical").strip()
        level = data.get("proficiency_level", "Intermediate").strip()

        if not name:
            return jsonify({"success": False, "message": "Skill name is required."}), 400

        sk = StudentSkill(student_id=student_id, skill_name=name, category=category, proficiency_level=level)
        db.session.add(sk)
        db.session.commit()
        return jsonify({"success": True, "message": "Skill added!"})

    elif request.method == "DELETE":
        data = request.get_json() or {}
        skill_id = data.get("skill_id")
        sk = StudentSkill.query.filter_by(id=skill_id, student_id=student_id).first()
        if sk:
            db.session.delete(sk)
            db.session.commit()
        return jsonify({"success": True, "message": "Skill removed!"})


@app.route("/api/placement/apply", methods=["POST"])
@login_required
def api_apply_placement():
    student_id = session["student_id"]
    drive_id = request.form.get("drive_id")
    sub_date = datetime.now().strftime("%Y-%m-%d")

    resume_path = None
    if 'resume' in request.files:
        file = request.files['resume']
        if file and allowed_file(file.filename):
            filename = f"resume_{student_id}_{secure_filename(file.filename)}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], "resumes", filename)
            file.save(save_path)
            resume_path = f"uploads/resumes/{filename}"

    existing = PlacementApplication.query.filter_by(drive_id=drive_id, student_id=student_id).first()
    if existing:
        return jsonify({"success": False, "message": "Already applied to this placement drive."}), 400

    pa = PlacementApplication(
        drive_id=drive_id,
        student_id=student_id,
        applied_date=sub_date,
        status='Applied',
        resume_path=resume_path
    )
    db.session.add(pa)
    db.session.commit()

    return jsonify({"success": True, "message": "Application submitted successfully!"})


# ---------------------------------------------------------------------
# MODULE 9: CLINICAL ATTENDANCE API
# ---------------------------------------------------------------------
@app.route("/api/clinical")
@login_required
def api_clinical():
    student_id = session["student_id"]
    records = ClinicalAttendance.query.filter_by(student_id=student_id).order_by(ClinicalAttendance.date.desc()).all()

    rec_list = []
    total_assigned = 0.0
    total_completed = 0.0
    for r in records:
        total_assigned += r.assigned_hours
        total_completed += r.completed_hours
        rec_list.append({
            "id": r.id,
            "student_id": r.student_id,
            "date": r.date,
            "ward_lab": r.ward_lab,
            "assigned_hours": r.assigned_hours,
            "completed_hours": r.completed_hours,
            "status": r.status
        })
        
    pending_hours = max(0.0, total_assigned - total_completed)
    pct = round((total_completed / total_assigned) * 100, 1) if total_assigned else 0.0

    return jsonify({
        "records": rec_list,
        "total_assigned": total_assigned,
        "total_completed": total_completed,
        "pending_hours": pending_hours,
        "percentage": pct
    })


# ---------------------------------------------------------------------
# MODULE 10: LIBRARY API
# ---------------------------------------------------------------------
@app.route("/api/library")
@login_required
def api_library():
    student_id = session["student_id"]

    issued = IssuedBook.query.filter_by(student_id=student_id).order_by(IssuedBook.id.desc()).all()
    issued_list = []
    
    now = datetime.now()
    for ib in issued:
        fine = ib.fine_amount
        status = ib.status
        
        # Calculate fine dynamically if overdue
        if ib.status == "Issued" and ib.due_date:
            due_dt = datetime.strptime(ib.due_date, "%Y-%m-%d")
            if now > due_dt:
                days_overdue = (now - due_dt).days
                fine = float(days_overdue * 10.0)
                status = "Overdue"
                
        issued_list.append({
            "id": ib.id,
            "book_id": ib.book_id,
            "student_id": ib.student_id,
            "title": ib.book.title,
            "author": ib.book.author,
            "isbn": ib.book.isbn,
            "category": ib.book.category,
            "issue_date": ib.issue_date,
            "due_date": ib.due_date,
            "return_date": ib.return_date,
            "fine_amount": fine,
            "status": status
        })

    catalog = LibraryBook.query.order_by(LibraryBook.title.asc()).all()
    catalog_list = []
    for b in catalog:
        catalog_list.append({
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "isbn": b.isbn,
            "category": b.category,
            "total_copies": b.total_copies,
            "available_copies": b.available_copies
        })

    return jsonify({
        "issued_books": issued_list,
        "catalog": catalog_list
    })


# ---------------------------------------------------------------------
# MODULE 11: LEAVE APPLICATION API
# ---------------------------------------------------------------------
@app.route("/api/leave", methods=["GET", "POST"])
@login_required
def api_leave():
    student_id = session["student_id"]

    if request.method == "POST":
        data = request.get_json() or {}
        from_date = data.get("from_date", "").strip()
        to_date = data.get("to_date", "").strip()
        reason = data.get("reason", "").strip()
        created_at = datetime.now().strftime("%Y-%m-%d")

        if not from_date or not to_date or not reason:
            return jsonify({"success": False, "message": "All fields are required."}), 400

        lv = LeaveApplication(
            student_id=student_id,
            from_date=from_date,
            to_date=to_date,
            reason=reason,
            status='Pending',
            created_at=created_at
        )
        db.session.add(lv)
        db.session.commit()
        return jsonify({"success": True, "message": "Leave application submitted!"})

    leaves = LeaveApplication.query.filter_by(student_id=student_id).order_by(LeaveApplication.id.desc()).all()
    res = []
    for l in leaves:
        res.append({
            "id": l.id,
            "student_id": l.student_id,
            "from_date": l.from_date,
            "to_date": l.to_date,
            "reason": l.reason,
            "status": l.status,
            "admin_remarks": l.admin_remarks,
            "created_at": l.created_at
        })
    return jsonify(res)


# ---------------------------------------------------------------------
# MODULE 12: NOTIFICATIONS API
# ---------------------------------------------------------------------
@app.route("/api/notifications")
@login_required
def api_notifications():
    student_id = session["student_id"]
    notifs = Notification.query.filter_by(user_id=student_id).order_by(Notification.id.desc()).limit(15).all()
    res = []
    for n in notifs:
        res.append({
            "id": n.id,
            "user_id": n.user_id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "is_read": n.is_read,
            "created_at": n.created_at
        })
    return jsonify(res)


@app.route("/api/notifications/read-all", methods=["POST"])
@login_required
def api_read_all_notifications():
    student_id = session["student_id"]
    Notification.query.filter_by(user_id=student_id).update({Notification.is_read: 1})
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/notifications/read", methods=["POST"])
@login_required
def api_read_notification():
    student_id = session["student_id"]
    data = request.get_json() or {}
    nid = data.get("id")
    notif = Notification.query.filter_by(id=nid, user_id=student_id).first()
    if notif:
        notif.is_read = 1
        db.session.commit()
    return jsonify({"success": True})


# ---------------------------------------------------------------------
# MODULE 13: ADMIN MANAGEMENT API
# ---------------------------------------------------------------------
@app.route("/api/admin/stats")
@admin_required
def api_admin_stats():
    admin_type = session.get("admin_type")
    dept_id = session.get("department_id")

    if admin_type == "dept_admin":
        total_students = Student.query.filter_by(department_id=dept_id).count()
        pending_leaves = LeaveApplication.query.join(Student).filter(
            LeaveApplication.status == 'Pending',
            Student.department_id == dept_id
        ).count()
        issued_books = IssuedBook.query.join(Student).filter(
            IssuedBook.status == 'Issued',
            Student.department_id == dept_id
        ).count()
        
        # Cumulative stats
        attendance_uploaded = Attendance.query.join(Student).filter(Student.department_id == dept_id).count()
        results_uploaded = Result.query.join(Student).filter(Student.department_id == dept_id).count()
        
        # Average attendance percentage
        all_atts = Attendance.query.join(Student).filter(Student.department_id == dept_id).all()
        avg_att = round(sum([a.overall_percentage for a in all_atts]) / len(all_atts), 1) if all_atts else 0.0
        
        # Average SGPA
        all_results = Result.query.join(Student).filter(Student.department_id == dept_id).all()
        valid_sgpas = [r.sgpa for r in all_results if r.sgpa is not None]
        avg_sgpa = round(sum(valid_sgpas) / len(valid_sgpas), 2) if valid_sgpas else 0.0
        
        # Today's logins
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_logins = User.query.join(Student, User.id == Student.student_id).filter(
            User.last_login_date == today_str,
            Student.department_id == dept_id
        ).count()
    else:
        # head_admin has access to everything
        total_students = Student.query.count()
        pending_leaves = LeaveApplication.query.filter_by(status='Pending').count()
        issued_books = IssuedBook.query.filter_by(status='Issued').count()
        
        # Cumulative stats
        attendance_uploaded = Attendance.query.count()
        results_uploaded = Result.query.count()
        
        # Average attendance percentage
        all_atts = Attendance.query.all()
        avg_att = round(sum([a.overall_percentage for a in all_atts]) / len(all_atts), 1) if all_atts else 0.0
        
        # Average SGPA
        all_results = Result.query.all()
        valid_sgpas = [r.sgpa for r in all_results if r.sgpa is not None]
        avg_sgpa = round(sum(valid_sgpas) / len(valid_sgpas), 2) if valid_sgpas else 0.0
        
        # Today's logins
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_logins = User.query.filter_by(last_login_date=today_str).count()

    total_announcements = Announcement.query.count()
    active_drives = PlacementDrive.query.filter_by(status='Active').count()

    return jsonify({
        "total_students": total_students,
        "pending_leaves": pending_leaves,
        "attendance_uploaded": attendance_uploaded,
        "results_uploaded": results_uploaded,
        "avg_attendance": avg_att,
        "avg_sgpa": avg_sgpa,
        "today_logins": today_logins,
        "total_announcements": total_announcements,
        "active_drives": active_drives,
        "issued_books": issued_books
    })


@app.route("/api/admin/students", methods=["GET", "POST", "PUT", "DELETE"])
@admin_required
def api_admin_students():
    """
    CRUD Endpoint for Students.
    Supports query parameter search & filters:
    - q: string (searches ID, name, email)
    - department: string (department code, e.g. CSE)
    - year: string (academic year, e.g. 3rd Year)
    """
    admin_type = session.get("admin_type")
    dept_id = session.get("department_id")

    if request.method == "GET":
        q = request.args.get("q", "").strip()
        dept_code = request.args.get("department", "").strip()
        year_name = request.args.get("year", "").strip()
        
        query = db.session.query(Student).join(User)
        
        if admin_type == "dept_admin":
            query = query.filter(Student.department_id == dept_id)
        elif dept_code:
            query = query.join(Department).filter(Department.code == dept_code)

        if q:
            query = query.filter(
                (Student.student_id.like(f"%{q}%")) |
                (User.name.like(f"%{q}%")) |
                (Student.email.like(f"%{q}%"))
            )
        if year_name:
            query = query.join(AcademicYear).filter(AcademicYear.name == year_name)
            
        students = query.order_by(Student.student_id.asc()).all()
        res = []
        for s in students:
            res.append({
                "student_id": s.student_id,
                "roll_number": s.roll_number,
                "prn_number": s.prn_number,
                "name": s.user.name,
                "course": s.course,
                "year": s.academic_year.name if s.academic_year else "",
                "semester": s.semester.name if s.semester else "",
                "email": s.email,
                "phone": s.phone,
                "dob": s.dob,
                "blood_group": s.blood_group,
                "address": s.address,
                "admission_year": s.admission_year,
                "avatar_url": s.avatar_url,
                "cgpa": s.cgpa,
                "department": s.department.code if s.department else ""
            })
        return jsonify(res)

    elif request.method == "POST":
        data = request.get_json() or {}
        sid = data.get("student_id", "").strip()
        name = data.get("name", "").strip()
        password = data.get("password", "")

        if not sid or not name or not password:
            return jsonify({"success": False, "message": "Student ID, Name and Password are required."}), 400

        existing = User.query.get(sid)
        if existing:
            return jsonify({"success": False, "message": "Student ID already exists."}), 400

        # Get or create AcademicYear
        year_name = data.get("year", "1st Year")
        year = AcademicYear.query.filter_by(name=year_name).first()
        if not year:
            year = AcademicYear(name=year_name)
            db.session.add(year)
            db.session.commit()
            
        # Get or create Semester
        sem_name = data.get("semester", "Sem 1")
        sem = Semester.query.filter_by(name=sem_name).first()
        if not sem:
            sem = Semester(name=sem_name)
            db.session.add(sem)
            db.session.commit()

        # Get department ID
        if admin_type == "dept_admin":
            target_dept_id = dept_id
        else:
            dept_code = data.get("department", "CSE")
            dept = Department.query.filter_by(code=dept_code).first()
            if not dept:
                dept = Department(code=dept_code, name=f"{dept_code} Department")
                db.session.add(dept)
                db.session.commit()
            target_dept_id = dept.id

        # Save base user credentials
        pass_hash = generate_password_hash(password)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        u = User(id=sid, password_hash=pass_hash, name=name, role='student', created_at=now_str)
        db.session.add(u)

        st = Student(
            student_id=sid,
            roll_number=sid,
            prn_number=data.get("prn_number", "").strip(),
            course=data.get("course", "B.Tech"),
            year_id=year.id,
            semester_id=sem.id,
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            dob=data.get("dob", ""),
            blood_group=data.get("blood_group", ""),
            address=data.get("address", ""),
            admission_year=data.get("admission_year", datetime.now().strftime("%Y")),
            cgpa=float(data.get("cgpa", 8.5)),
            department_id=target_dept_id
        )
        db.session.add(st)
        db.session.commit()

        return jsonify({"success": True, "message": "Student added successfully!"})

    elif request.method == "PUT":
        data = request.get_json() or {}
        sid = data.get("student_id", "").strip()
        name = data.get("name", "").strip()

        if not sid or not name:
            return jsonify({"success": False, "message": "Student ID and Name required."}), 400

        u = User.query.get(sid)
        if not u:
            return jsonify({"success": False, "message": "Student account not found."}), 404
            
        st = Student.query.get(sid)
        if not st:
            return jsonify({"success": False, "message": "Student record not found."}), 404

        if admin_type == "dept_admin" and st.department_id != dept_id:
            return jsonify({"success": False, "message": "Access Denied. You do not have permission to modify this student."}), 403

        u.name = name

        # Password optional update
        password = data.get("password", "").strip()
        if password:
            u.password_hash = generate_password_hash(password)

        st.course = data.get("course", st.course)
        
        # Academic Year update
        year_name = data.get("year", "")
        if year_name:
            year = AcademicYear.query.filter_by(name=year_name).first()
            if not year:
                year = AcademicYear(name=year_name)
                db.session.add(year)
                db.session.commit()
            st.year_id = year.id

        # Semester update
        sem_name = data.get("semester", "")
        if sem_name:
            sem = Semester.query.filter_by(name=sem_name).first()
            if not sem:
                sem = Semester(name=sem_name)
                db.session.add(sem)
                db.session.commit()
            st.semester_id = sem.id

        # Department update (dept_admin cannot move students out of their department)
        if admin_type != "dept_admin":
            dept_code = data.get("department", "")
            if dept_code:
                dept = Department.query.filter_by(code=dept_code).first()
                if not dept:
                    dept = Department(code=dept_code, name=f"{dept_code} Department")
                    db.session.add(dept)
                    db.session.commit()
                st.department_id = dept.id

        st.prn_number = data.get("prn_number", st.prn_number)
        st.email = data.get("email", st.email)
        st.phone = data.get("phone", st.phone)
        st.dob = data.get("dob", st.dob)
        st.blood_group = data.get("blood_group", st.blood_group)
        st.address = data.get("address", st.address)
        st.admission_year = data.get("admission_year", st.admission_year)
        if "cgpa" in data:
            st.cgpa = float(data["cgpa"])

        db.session.commit()
        return jsonify({"success": True, "message": "Student record updated!"})

    elif request.method == "DELETE":
        data = request.get_json() or {}
        sid = data.get("student_id", "").strip()
        
        st = Student.query.get(sid)
        if not st:
            return jsonify({"success": False, "message": "Student record not found."}), 404

        if admin_type == "dept_admin" and st.department_id != dept_id:
            return jsonify({"success": False, "message": "Access Denied. You do not have permission to delete this student."}), 403

        u = User.query.get(sid)
        if u:
            db.session.delete(u)
            db.session.commit()
        return jsonify({"success": True, "message": f"Student {sid} deleted."})


@app.route("/api/admin/students/reset-password", methods=["POST"])
@admin_required
def api_admin_reset_password():
    data = request.get_json() or {}
    sid = data.get("student_id", "").strip()
    new_pass = data.get("password", "").strip()
    if not sid or not new_pass:
        return jsonify({"success": False, "message": "Student ID and new password are required."}), 400

    u = User.query.get(sid)
    if not u:
        return jsonify({"success": False, "message": "Student not found."}), 404

    u.password_hash = generate_password_hash(new_pass)
    db.session.commit()
    return jsonify({"success": True, "message": "Password reset successfully!"})


@app.route("/api/admin/students/export")
@admin_required
def api_admin_export_students():
    students = Student.query.all()
    data_list = []
    for s in students:
        data_list.append({
            "StudentID": s.student_id,
            "PRNNumber": s.prn_number,
            "Name": s.user.name,
            "Course": s.course,
            "Year": s.academic_year.name if s.academic_year else "",
            "Semester": s.semester.name if s.semester else "",
            "Email": s.email,
            "Phone": s.phone,
            "DOB": s.dob,
            "BloodGroup": s.blood_group,
            "Address": s.address,
            "AdmissionYear": s.admission_year,
            "CGPA": s.cgpa,
            "Department": s.department.code if s.department else ""
        })
    df = pd.DataFrame(data_list)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Students')
    output.seek(0)
    
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="students_export.xlsx"
    )


@app.route("/api/admin/students/import", methods=["POST"])
@admin_required
def api_admin_import_students():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected."}), 400
        
    try:
        df = pd.read_excel(file)
        df.columns = [c.strip() for c in df.columns]
        
        # Ensure default CSE Department exists
        cse_dept = Department.query.filter_by(code='CSE').first()
        if not cse_dept:
            cse_dept = Department(code='CSE', name='Computer Science & Engineering')
            db.session.add(cse_dept)
            db.session.commit()
            
        import_count = 0
        for _, row in df.iterrows():
            sid = str(row.get('StudentID', '')).strip()
            name = str(row.get('Name', '')).strip()
            if not sid or not name:
                continue
                
            u = User.query.get(sid)
            if not u:
                pwd = str(row.get('Password', 'pass123')).strip()
                if not (pwd.startswith('scrypt:') or pwd.startswith('pbkdf2:')):
                    pwd = generate_password_hash(pwd)
                u = User(id=sid, password_hash=pwd, name=name, role='student')
                db.session.add(u)
            else:
                u.name = name
                
            # Academic Year
            year_name = str(row.get('Year', '3rd Year')).strip()
            year = AcademicYear.query.filter_by(name=year_name).first()
            if not year:
                year = AcademicYear(name=year_name)
                db.session.add(year)
                db.session.commit()
                
            # Semester
            sem_name = str(row.get('Semester', 'Sem 6')).strip()
            sem = Semester.query.filter_by(name=sem_name).first()
            if not sem:
                sem = Semester(name=sem_name)
                db.session.add(sem)
                db.session.commit()
                
            # Department
            dept_code = str(row.get('Department', 'CSE')).strip()
            dept = Department.query.filter_by(code=dept_code).first()
            if not dept:
                dept = Department(code=dept_code, name=f"{dept_code} Department")
                db.session.add(dept)
                db.session.commit()
                
            st = Student.query.get(sid)
            if not st:
                st = Student(student_id=sid, roll_number=sid)
                db.session.add(st)
                
            st.prn_number = str(row.get('PRNNumber', row.get('PRN Number', row.get('PRN', '')))).strip()
            if st.prn_number == 'nan':
                st.prn_number = ''
            st.course = str(row.get('Course', 'B.Tech')).strip()
            st.year_id = year.id
            st.semester_id = sem.id
            st.email = str(row.get('Email', '')).strip()
            st.phone = str(row.get('Phone', '')).strip()
            st.dob = str(row.get('DOB', '')).strip()
            st.blood_group = str(row.get('BloodGroup', '')).strip()
            st.address = str(row.get('Address', '')).strip()
            st.admission_year = str(row.get('AdmissionYear', '2023')).strip()
            st.cgpa = float(row.get('CGPA', 8.5))
            st.department_id = dept.id
            
            import_count += 1
            
        db.session.commit()
        return jsonify({"success": True, "message": f"Successfully imported/updated {import_count} student profiles!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error parsing Excel: {str(e)}"}), 500


@app.route("/api/admin/attendance", methods=["GET", "POST", "DELETE"])
@admin_required
def api_admin_attendance():
    admin_type = session.get("admin_type")
    dept_id = session.get("department_id")

    if request.method == "GET":
        student_id = request.args.get("student_id")
        query = DailyAttendance.query
        
        if admin_type == "dept_admin":
            query = query.join(Student).filter(Student.department_id == dept_id)
            
        if student_id:
            query = query.filter_by(student_id=student_id)
        records = query.order_by(DailyAttendance.id.desc()).all()
        res = []
        for r in records:
            res.append({
                "id": r.id,
                "student_id": r.student_id,
                "date": r.date,
                "subject": r.subject.name,
                "status": r.status,
                "student_name": r.student.user.name
            })
        return jsonify(res)

    elif request.method == "POST":
        data = request.get_json() or {}
        sid = data.get("student_id", "").strip()
        date = data.get("date", "").strip()
        subject_name = data.get("subject", "").strip()
        status = data.get("status", "").strip()

        if not sid or not date or not subject_name or not status:
            return jsonify({"success": False, "message": "All fields required."}), 400

        st = Student.query.get(sid)
        if not st:
            return jsonify({"success": False, "message": "Student not found."}), 404

        if admin_type == "dept_admin" and st.department_id != dept_id:
            return jsonify({"success": False, "message": "Access Denied. You do not have permission to manage this student's attendance."}), 403

        # Get or create subject
        sub = Subject.query.filter_by(name=subject_name).first()
        if not sub:
            words = [w for w in subject_name.split() if w.isalnum()]
            code = "".join([w[0] for w in words]).upper() if words else "SUB"
            sub = Subject(code=code, name=subject_name, department_id=st.department_id)
            db.session.add(sub)
            db.session.commit()

        att = DailyAttendance(student_id=sid, date=date, subject_id=sub.id, status=status)
        db.session.add(att)
        db.session.commit()
        return jsonify({"success": True, "message": "Attendance record added!"})

    elif request.method == "DELETE":
        data = request.get_json() or {}
        rec_id = data.get("id")
        att = DailyAttendance.query.get(rec_id)
        if att:
            if admin_type == "dept_admin" and att.student.department_id != dept_id:
                return jsonify({"success": False, "message": "Access Denied. You do not have permission to delete this attendance record."}), 403
            db.session.delete(att)
            db.session.commit()
        return jsonify({"success": True, "message": "Attendance deleted!"})


@app.route("/api/admin/attendance/import", methods=["POST"])
@admin_required
def api_admin_import_attendance():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected."}), 400

    academic_year_id = request.form.get("academic_year_id")
    semester_id = request.form.get("semester_id")
    as_of_date = request.form.get("as_of_date", "").strip()

    temp_dir = os.path.join(app.root_path, "static", "uploads", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    filepath = os.path.join(temp_dir, secure_filename(file.filename))
    file.save(filepath)

    try:
        res = ExcelImportService.import_attendance(
            filepath,
            academic_year_id=int(academic_year_id) if academic_year_id else None,
            semester_id=int(semester_id) if semester_id else None,
            as_of_date=as_of_date
        )
        
        # Log to Import History
        history = ImportHistory(
            import_type="attendance",
            filename=file.filename,
            success_count=res["imported"],
            updated_count=res["updated"],
            skipped_count=res["skipped"],
            failed_count=res["failed"],
            summary="\n".join(res["details"]) if res["details"] else "Attendance cumulative sheet imported successfully."
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify(res)
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Attendance import failed: {str(e)}"}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route("/api/admin/assessment", methods=["GET", "POST", "DELETE"])
@admin_required
def api_admin_assessment():
    admin_type = session.get("admin_type")
    dept_id = session.get("department_id")

    if request.method == "GET":
        student_id = request.args.get("student_id")
        query = Assessment.query
        
        if admin_type == "dept_admin":
            query = query.join(Student).filter(Student.department_id == dept_id)
            
        if student_id:
            query = query.filter_by(student_id=student_id)
        records = query.order_by(Assessment.id.desc()).all()
        res = []
        for r in records:
            res.append({
                "id": r.id,
                "student_id": r.student_id,
                "subject": r.subject.name,
                "assessment_type": r.assessment_type,
                "marks_obtained": r.marks_obtained,
                "max_marks": r.max_marks,
                "date": r.date,
                "student_name": r.student.user.name
            })
        return jsonify(res)

    elif request.method == "POST":
        data = request.get_json() or {}
        sid = data.get("student_id", "").strip()
        subject_name = data.get("subject", "").strip()
        atype = data.get("type", "").strip()
        marks = float(data.get("marks", 0))
        max_marks = float(data.get("max_marks", 100))
        date = data.get("date", "").strip()

        if marks > max_marks:
            return jsonify({"success": False, "message": "Obtained marks cannot exceed maximum marks."}), 400

        st = Student.query.get(sid)
        if not st:
            return jsonify({"success": False, "message": "Student not found."}), 404

        if admin_type == "dept_admin" and st.department_id != dept_id:
            return jsonify({"success": False, "message": "Access Denied. You do not have permission to manage this student's assessment."}), 403

        # Get or create subject
        sub = Subject.query.filter_by(name=subject_name).first()
        if not sub:
            words = [w for w in subject_name.split() if w.isalnum()]
            code = "".join([w[0] for w in words]).upper() if words else "SUB"
            sub = Subject(code=code, name=subject_name, department_id=st.department_id)
            db.session.add(sub)
            db.session.commit()

        ass = Assessment(
            student_id=sid,
            subject_id=sub.id,
            assessment_type=atype,
            marks_obtained=marks,
            max_marks=max_marks,
            date=date
        )
        db.session.add(ass)
        db.session.commit()
        return jsonify({"success": True, "message": "Assessment marks recorded!"})

    elif request.method == "DELETE":
        data = request.get_json() or {}
        rec_id = data.get("id")
        ass = Assessment.query.get(rec_id)
        if ass:
            if admin_type == "dept_admin" and ass.student.department_id != dept_id:
                return jsonify({"success": False, "message": "Access Denied. You do not have permission to delete this assessment record."}), 403
            db.session.delete(ass)
            db.session.commit()
        return jsonify({"success": True, "message": "Assessment record deleted!"})


@app.route("/api/admin/assessment/import", methods=["POST"])
@admin_required
def api_admin_import_assessment():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected."}), 400
        
    try:
        df = pd.read_excel(file)
        df.columns = [c.strip() for c in df.columns]
        
        import_count = 0
        date_val = datetime.now().strftime("%Y-%m-%d")
        
        has_mse = any(c.upper() in ['MSE', 'MIDSEM', 'MID SEMESTER', 'MID-SEM'] for c in df.columns)
        has_ise = any(c.upper() in ['ISE', 'INTERNAL', 'CLASS TEST'] for c in df.columns)
        has_endsem = any(c.upper() in ['ENDSEM', 'END SEMESTER', 'END-SEM', 'END SEM'] for c in df.columns)
        
        for _, row in df.iterrows():
            sid = str(row.get('StudentID', '')).strip()
            if not sid or sid == 'nan':
                sid = str(row.get('Student ID', '')).strip()
            if not sid or sid == 'nan':
                sid = str(row.get('RollNumber', '')).strip()
                
            subject_name = str(row.get('Subject', '')).strip()
            
            if not sid or sid == 'nan' or not subject_name or subject_name == 'nan':
                continue
                
            st = Student.query.get(sid)
            if not st:
                st = Student.query.filter_by(roll_number=sid).first()
                if not st:
                    continue
                    
            sub = Subject.query.filter_by(name=subject_name).first()
            if not sub:
                words = [w for w in subject_name.split() if w.isalnum()]
                code = "".join([w[0] for w in words]).upper() if words else "SUB"
                sub = Subject(code=code, name=subject_name, department_id=st.department_id)
                db.session.add(sub)
                db.session.commit()
                
            def upsert_assessment(a_type, ob_marks, max_m):
                ass = Assessment.query.filter_by(
                    student_id=st.student_id, 
                    subject_id=sub.id, 
                    assessment_type=a_type
                ).first()
                if ass:
                    ass.marks_obtained = ob_marks
                    ass.max_marks = max_m
                else:
                    ass = Assessment(
                        student_id=st.student_id,
                        subject_id=sub.id,
                        assessment_type=a_type,
                        marks_obtained=ob_marks,
                        max_marks=max_m,
                        date=date_val
                    )
                    db.session.add(ass)
            
            if has_mse or has_ise or has_endsem:
                for col in df.columns:
                    col_upper = col.upper()
                    val = row.get(col)
                    if pd.isna(val):
                        continue
                    try:
                        val_float = float(val)
                    except ValueError:
                        continue
                        
                    if col_upper in ['MSE', 'MIDSEM', 'MID SEMESTER', 'MID-SEM']:
                        upsert_assessment("MSE", val_float, 30.0)
                        import_count += 1
                    elif col_upper in ['ISE', 'INTERNAL', 'CLASS TEST']:
                        upsert_assessment("ISE", val_float, 20.0)
                        import_count += 1
                    elif col_upper in ['ENDSEM', 'END SEMESTER', 'END-SEM', 'END SEM']:
                        upsert_assessment("End Semester", val_float, 100.0)
                        import_count += 1
            else:
                a_type = str(row.get('ExamType', row.get('AssessmentType', 'Unit Test'))).strip()
                ob_marks = row.get('MarksObtained', row.get('Marks', None))
                max_m = row.get('MaxMarks', 50)
                if ob_marks is not None and not pd.isna(ob_marks):
                    upsert_assessment(a_type, float(ob_marks), float(max_m))
                    import_count += 1
                    
        db.session.commit()
        return jsonify({"success": True, "message": f"Successfully imported/updated {import_count} result entries!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error parsing Excel: {str(e)}"}), 500


@app.route("/api/admin/assignments", methods=["GET", "POST", "DELETE"])
@admin_required
def api_admin_assignments():
    if request.method == "GET":
        assignments = Assignment.query.order_by(Assignment.id.desc()).all()
        res = []
        for a in assignments:
            res.append({
                "id": a.id,
                "subject": a.subject.name,
                "title": a.title,
                "description": a.description,
                "assigned_date": a.assigned_date,
                "due_date": a.due_date,
                "total_marks": a.total_marks,
                "attachment_path": a.attachment_path,
                "created_by": a.created_by
            })
        return jsonify(res)

    elif request.method == "POST":
        data = request.get_json() or {}
        subject_name = data.get("subject", "").strip()
        title = data.get("title", "").strip()
        desc = data.get("description", "").strip()
        adate = data.get("assigned_date", datetime.now().strftime("%Y-%m-%d"))
        ddate = data.get("due_date", "").strip()
        marks = float(data.get("total_marks", 50))

        if not subject_name or not title or not ddate:
            return jsonify({"success": False, "message": "Subject, title, and due date are required."}), 400

        # Get default cse dept or create
        dept = Department.query.filter_by(code='CSE').first()
        dept_id = dept.id if dept else None

        # Get or create subject
        sub = Subject.query.filter_by(name=subject_name).first()
        if not sub:
            words = [w for w in subject_name.split() if w.isalnum()]
            code = "".join([w[0] for w in words]).upper() if words else "SUB"
            sub = Subject(code=code, name=subject_name, department_id=dept_id)
            db.session.add(sub)
            db.session.commit()

        a = Assignment(
            subject_id=sub.id,
            title=title,
            description=desc,
            assigned_date=adate,
            due_date=ddate,
            total_marks=marks,
            created_by='ADMIN01'
        )
        db.session.add(a)
        db.session.commit()
        return jsonify({"success": True, "message": "Assignment created successfully!"})

    elif request.method == "DELETE":
        data = request.get_json() or {}
        aid = data.get("id")
        a = Assignment.query.get(aid)
        if a:
            db.session.delete(a)
            db.session.commit()
        return jsonify({"success": True, "message": "Assignment deleted!"})


@app.route("/api/admin/announcements", methods=["GET", "POST", "DELETE"])
@admin_required
def api_admin_announcements():
    if request.method == "GET":
        anns = Announcement.query.order_by(Announcement.id.desc()).all()
        res = []
        for a in anns:
            res.append({
                "id": a.id,
                "title": a.title,
                "message": a.message,
                "category": a.category,
                "priority": a.priority,
                "date": a.date,
                "created_by": a.created_by
            })
        return jsonify(res)

    elif request.method == "POST":
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        msg = data.get("message", "").strip()
        cat = data.get("category", "General").strip()
        prio = data.get("priority", "Medium").strip()
        date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

        if not title or not msg:
            return jsonify({"success": False, "message": "Title and Message are required."}), 400

        ann = Announcement(
            title=title,
            message=msg,
            category=cat,
            priority=prio,
            date=date,
            created_by='ADMIN01'
        )
        db.session.add(ann)
        db.session.commit()
        return jsonify({"success": True, "message": "Announcement broadcasted!"})

    elif request.method == "DELETE":
        data = request.get_json() or {}
        aid = data.get("id")
        ann = Announcement.query.get(aid)
        if ann:
            db.session.delete(ann)
            db.session.commit()
        return jsonify({"success": True, "message": "Announcement deleted!"})


@app.route("/api/admin/documents", methods=["GET", "POST", "DELETE"])
@admin_required
def api_admin_documents():
    if request.method == "GET":
        docs = Document.query.order_by(Document.id.desc()).all()
        res = []
        for d in docs:
            res.append({
                "id": d.id,
                "title": d.title,
                "description": d.description,
                "category": d.category,
                "file_path": d.file_path,
                "file_size": d.file_size,
                "uploaded_date": d.uploaded_date,
                "uploaded_by": d.uploaded_by
            })
        return jsonify(res)

    elif request.method == "POST":
        title = request.form.get("title", "").strip()
        desc = request.form.get("description", "").strip()
        category = request.form.get("category", "Study Material").strip()
        date = datetime.now().strftime("%Y-%m-%d")

        if 'file' not in request.files or not title:
            return jsonify({"success": False, "message": "Title and document file are required."}), 400

        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = f"doc_{secure_filename(file.filename)}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], "documents", filename)
            file.save(save_path)
            file_path = f"uploads/documents/{filename}"
            size_mb = f"{round(os.path.getsize(save_path) / (1024 * 1024), 1)} MB"

            d = Document(
                title=title,
                description=desc,
                category=category,
                file_path=file_path,
                file_size=size_mb,
                uploaded_date=date,
                uploaded_by="ADMIN01"
            )
            db.session.add(d)
            db.session.commit()
            return jsonify({"success": True, "message": "Document uploaded!"})

        return jsonify({"success": False, "message": "Invalid file type."}), 400

    elif request.method == "DELETE":
        data = request.get_json() or {}
        did = data.get("id")
        d = Document.query.get(did)
        if d:
            db.session.delete(d)
            db.session.commit()
        return jsonify({"success": True, "message": "Document deleted!"})


@app.route("/api/admin/placements", methods=["GET", "POST", "DELETE"])
@admin_required
def api_admin_placements():
    if request.method == "GET":
        drives = PlacementDrive.query.order_by(PlacementDrive.id.desc()).all()
        res = []
        for d in drives:
            res.append({
                "id": d.id,
                "company_name": d.company_name,
                "job_role": d.job_role,
                "eligibility_criteria": d.eligibility_criteria,
                "package_lpa": d.package_lpa,
                "location": d.location,
                "deadline": d.deadline,
                "status": d.status
            })
        return jsonify(res)

    elif request.method == "POST":
        data = request.get_json() or {}
        comp = data.get("company_name", "").strip()
        role = data.get("job_role", "").strip()
        elig = data.get("eligibility_criteria", "").strip()
        pkg = float(data.get("package_lpa", 0))
        loc = data.get("location", "").strip()
        deadline = data.get("deadline", "").strip()
        status = data.get("status", "Active").strip()

        pd = PlacementDrive(
            company_name=comp,
            job_role=role,
            eligibility_criteria=elig,
            package_lpa=pkg,
            location=loc,
            deadline=deadline,
            status=status
        )
        db.session.add(pd)
        db.session.commit()
        return jsonify({"success": True, "message": "Placement drive created!"})

    elif request.method == "DELETE":
        data = request.get_json() or {}
        did = data.get("id")
        pd = PlacementDrive.query.get(did)
        if pd:
            db.session.delete(pd)
            db.session.commit()
        return jsonify({"success": True, "message": "Drive deleted!"})


@app.route("/api/admin/clinical", methods=["GET", "POST", "DELETE"])
@admin_required
def api_admin_clinical():
    if request.method == "GET":
        records = ClinicalAttendance.query.order_by(ClinicalAttendance.id.desc()).limit(100).all()
        res = []
        for r in records:
            res.append({
                "id": r.id,
                "student_id": r.student_id,
                "date": r.date,
                "ward_lab": r.ward_lab,
                "assigned_hours": r.assigned_hours,
                "completed_hours": r.completed_hours,
                "status": r.status,
                "student_name": r.student.user.name
            })
        return jsonify(res)

    elif request.method == "POST":
        data = request.get_json() or {}
        sid = data.get("student_id", "").strip()
        date = data.get("date", "").strip()
        ward = data.get("ward_lab", "").strip()
        hours = float(data.get("assigned_hours", 4.0))
        status = data.get("status", "Scheduled").strip()

        st = Student.query.get(sid)
        if not st:
            return jsonify({"success": False, "message": "Student not found."}), 404

        clin = ClinicalAttendance(
            student_id=sid,
            date=date,
            ward_lab=ward,
            assigned_hours=hours,
            completed_hours=hours if status == "Completed" else 0.0,
            status=status
        )
        db.session.add(clin)
        db.session.commit()
        return jsonify({"success": True, "message": "Clinical duty scheduled!"})

    elif request.method == "DELETE":
        data = request.get_json() or {}
        cid = data.get("id")
        clin = ClinicalAttendance.query.get(cid)
        if clin:
            db.session.delete(clin)
            db.session.commit()
        return jsonify({"success": True, "message": "Clinical record deleted!"})


@app.route("/api/admin/library", methods=["GET", "POST", "PUT", "DELETE"])
@admin_required
def api_admin_library():
    if request.method == "GET":
        catalog = LibraryBook.query.order_by(LibraryBook.id.desc()).all()
        catalog_list = []
        for b in catalog:
            catalog_list.append({
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "isbn": b.isbn,
                "category": b.category,
                "total_copies": b.total_copies,
                "available_copies": b.available_copies
            })

        issued = IssuedBook.query.order_by(IssuedBook.id.desc()).all()
        issued_list = []
        for ib in issued:
            issued_list.append({
                "id": ib.id,
                "book_id": ib.book_id,
                "student_id": ib.student_id,
                "title": ib.book.title,
                "student_name": ib.student.user.name,
                "issue_date": ib.issue_date,
                "due_date": ib.due_date,
                "return_date": ib.return_date,
                "fine_amount": ib.fine_amount,
                "status": ib.status
            })
        return jsonify({"books": catalog_list, "issued_books": issued_list})

    elif request.method == "POST":
        data = request.get_json() or {}
        action = data.get("action", "add_book")

        if action == "add_book":
            title = data.get("title", "").strip()
            author = data.get("author", "").strip()
            isbn = data.get("isbn", "").strip()
            cat = data.get("category", "General").strip()
            copies = int(data.get("total_copies", 5))

            b = LibraryBook(
                title=title,
                author=author,
                isbn=isbn,
                category=cat,
                total_copies=copies,
                available_copies=copies
            )
            db.session.add(b)
            db.session.commit()
            return jsonify({"success": True, "message": "Book added to catalog!"})

        elif action == "issue_book":
            book_id = data.get("book_id")
            sid = data.get("student_id", "").strip()
            
            st = Student.query.get(sid)
            if not st:
                return jsonify({"success": False, "message": "Student not found."}), 404

            book = LibraryBook.query.get(book_id)
            if not book or book.available_copies <= 0:
                return jsonify({"success": False, "message": "Book not available."}), 400

            idate = datetime.now().strftime("%Y-%m-%d")
            ddate = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

            ib = IssuedBook(book_id=book_id, student_id=sid, issue_date=idate, due_date=ddate, status='Issued')
            book.available_copies = max(0, book.available_copies - 1)
            
            db.session.add(ib)
            db.session.commit()
            return jsonify({"success": True, "message": "Book issued to student!"})

    elif request.method == "PUT":
        # Return issued book
        data = request.get_json() or {}
        issue_id = data.get("issue_id")
        rdate = datetime.now().strftime("%Y-%m-%d")

        ib = IssuedBook.query.get(issue_id)
        if ib:
            ib.return_date = rdate
            ib.status = 'Returned'
            ib.fine_amount = 0.0
            ib.book.available_copies += 1
            db.session.commit()

        return jsonify({"success": True, "message": "Book return processed!"})

    elif request.method == "DELETE":
        data = request.get_json() or {}
        bid = data.get("id")
        book = LibraryBook.query.get(bid)
        if book:
            db.session.delete(book)
            db.session.commit()
        return jsonify({"success": True, "message": "Book deleted!"})


@app.route("/api/admin/leave", methods=["GET"])
@admin_required
def api_admin_leave():
    admin_type = session.get("admin_type")
    dept_id = session.get("department_id")

    query = LeaveApplication.query
    if admin_type == "dept_admin":
        query = query.join(Student).filter(Student.department_id == dept_id)
        
    leaves = query.order_by(LeaveApplication.id.desc()).all()
    res = []
    for l in leaves:
        res.append({
            "id": l.id,
            "student_id": l.student_id,
            "from_date": l.from_date,
            "to_date": l.to_date,
            "reason": l.reason,
            "status": l.status,
            "admin_remarks": l.admin_remarks,
            "created_at": l.created_at,
            "student_name": l.student.user.name,
            "course": l.student.course,
            "year": l.student.academic_year.name if l.student.academic_year else ""
        })
    return jsonify(res)


@app.route("/api/admin/leave/action", methods=["POST"])
@admin_required
def api_admin_leave_action():
    admin_type = session.get("admin_type")
    dept_id = session.get("department_id")

    data = request.get_json() or {}
    leave_id = data.get("leave_id")
    action = data.get("action", "").strip()  # 'Approved' or 'Rejected'
    remarks = data.get("admin_remarks", "").strip()

    if not leave_id or not action:
        return jsonify({"success": False, "message": "Leave ID and action required."}), 400

    lv = LeaveApplication.query.get(leave_id)
    if not lv:
        return jsonify({"success": False, "message": "Leave request not found."}), 404

    if admin_type == "dept_admin" and lv.student.department_id != dept_id:
        return jsonify({"success": False, "message": "Access Denied. You do not have permission to modify this leave request."}), 403

    lv.status = action
    lv.admin_remarks = remarks

    # Send notification to student
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    n = Notification(
        user_id=lv.student_id,
        title=f"Leave Request {action}",
        message=f"Your leave request has been {action.lower()}. Remarks: {remarks or 'None'}",
        type="success" if action == "Approved" else "warning",
        created_at=now_str
    )
    db.session.add(n)
    db.session.commit()

    return jsonify({"success": True, "message": f"Leave application {action.lower()}!"})


# ---------------------------------------------------------------------
# MODULE 14: RESULTS & MDM ALLOCATION MANAGEMENT APIs
# ---------------------------------------------------------------------

@app.route("/api/admin/results/import", methods=["POST"])
@admin_required
def api_admin_import_results():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected."}), 400

    academic_year_id = request.form.get("academic_year_id")
    semester_id = request.form.get("semester_id")
    exam_type = request.form.get("exam_type", "End Semester")

    temp_dir = os.path.join(app.root_path, "static", "uploads", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    filepath = os.path.join(temp_dir, secure_filename(file.filename))
    file.save(filepath)

    try:
        res = ExcelImportService.import_results(
            filepath,
            academic_year_id=int(academic_year_id) if academic_year_id else None,
            semester_id=int(semester_id) if semester_id else None,
            exam_type=exam_type
        )
        
        # Log to Import History
        history = ImportHistory(
            import_type="results",
            filename=file.filename,
            success_count=res["imported"],
            updated_count=res["updated"],
            skipped_count=res["skipped"],
            failed_count=res["failed"],
            summary="\n".join(res["details"]) if res["details"] else "All result records imported successfully."
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify(res)
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Result import failed: {str(e)}"}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route("/api/admin/results", methods=["GET"])
@admin_required
def api_admin_get_results():
    admin_type = session.get("admin_type")
    dept_id = session.get("department_id")

    search = request.args.get("q", "").strip()
    year_id = request.args.get("academic_year_id")
    sem_id = request.args.get("semester_id")
    exam = request.args.get("exam_type")
    subj_name = request.args.get("subject_name", "").strip()

    query = ResultSubject.query.join(Result).join(Student)
    
    if admin_type == "dept_admin":
        query = query.filter(Student.department_id == dept_id)
        
    if search:
        query = query.filter(
            (Student.roll_number.like(f"%{search}%")) |
            (Student.prn_number.like(f"%{search}%")) |
            (Student.student_id.like(f"%{search}%"))
        )
    if year_id:
        query = query.filter(Result.academic_year_id == int(year_id))
    if sem_id:
        query = query.filter(Result.semester_id == int(sem_id))
    if exam:
        query = query.filter(Result.exam_type == exam)
    if subj_name:
        query = query.filter(ResultSubject.subject_name.ilike(f"%{subj_name}%"))

    records = query.order_by(Result.id.desc()).all()
    
    res = []
    for r in records:
        res.append({
            "id": r.result.id,
            "subject_record_id": r.id,
            "student_id": r.result.student_id,
            "roll_number": r.result.student.roll_number or r.result.student_id,
            "prn_number": r.result.student.prn_number or "-",
            "name": r.result.student.user.name,
            "semester": r.result.semester.name if r.result.semester else "N/A",
            "academic_year": r.result.academic_year.name if r.result.academic_year else "N/A",
            "exam_type": r.result.exam_type,
            "subject_name": r.subject_name,
            "subject_code": r.subject_code or "-",
            "internal_marks": r.internal_marks,
            "external_marks": r.external_marks,
            "practical_marks": r.practical_marks,
            "total_marks": r.total_marks,
            "grade": r.grade or "F",
            "sgpa": r.result.sgpa or "-",
            "cgpa": r.result.cgpa or "-",
            "status": r.result.status or "Pass"
        })
    return jsonify(res)


@app.route("/api/admin/results/delete/<int:rid>", methods=["DELETE"])
@admin_required
def api_admin_delete_result(rid):
    admin_type = session.get("admin_type")
    dept_id = session.get("department_id")

    r = Result.query.get(rid)
    if r:
        if admin_type == "dept_admin" and r.student.department_id != dept_id:
            return jsonify({"success": False, "message": "Access Denied. You do not have permission to delete this result."}), 403
        db.session.delete(r)
        db.session.commit()
        return jsonify({"success": True, "message": "Student result record deleted successfully."})
    return jsonify({"success": False, "message": "Result record not found."}), 404


@app.route("/api/admin/results/export", methods=["GET"])
@admin_required
def api_admin_export_results():
    search = request.args.get("q", "").strip()
    year_id = request.args.get("academic_year_id")
    sem_id = request.args.get("semester_id")
    exam = request.args.get("exam_type")
    subj_name = request.args.get("subject_name", "").strip()

    query = ResultSubject.query.join(Result).join(Student)
    
    if search:
        query = query.filter(
            (Student.roll_number.like(f"%{search}%")) |
            (Student.prn_number.like(f"%{search}%")) |
            (User.name.like(f"%{search}%"))
        )
    if year_id:
        query = query.filter(Result.academic_year_id == int(year_id))
    if sem_id:
        query = query.filter(Result.semester_id == int(sem_id))
    if exam:
        query = query.filter(Result.exam_type == exam)
    if subj_name:
        query = query.filter(ResultSubject.subject_name.ilike(f"%{subj_name}%"))

    records = query.all()
    
    data = []
    for r in records:
        data.append({
            "Roll Number": r.result.student.roll_number or r.result.student_id,
            "PRN": r.result.student.prn_number or "",
            "Student Name": r.result.student.user.name,
            "Academic Year": r.result.academic_year.name if r.result.academic_year else "",
            "Semester": r.result.semester.name if r.result.semester else "",
            "Exam Type": r.result.exam_type,
            "Subject Code": r.subject_code or "",
            "Subject Name": r.subject_name,
            "Internal Marks": r.internal_marks,
            "External Marks": r.external_marks,
            "Practical Marks": r.practical_marks,
            "Total": r.total_marks,
            "Grade": r.grade,
            "SGPA": r.result.sgpa,
            "CGPA": r.result.cgpa,
            "Status": r.result.status
        })
        
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')
    output.seek(0)
    
    return send_file(
        output,
        download_name=f"student_results_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/api/admin/mdm/import", methods=["POST"])
@admin_required
def api_admin_import_mdm():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected."}), 400

    temp_dir = os.path.join(app.root_path, "static", "uploads", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    filepath = os.path.join(temp_dir, secure_filename(file.filename))
    file.save(filepath)

    try:
        res = ExcelImportService.import_mdm(filepath)
        
        # Log to Import History
        history = ImportHistory(
            import_type="mdm",
            filename=file.filename,
            success_count=res["imported"],
            updated_count=res["updated"],
            skipped_count=res["skipped"],
            failed_count=res["failed"],
            summary="\n".join(res["details"]) if res["details"] else "MDM allocations imported successfully."
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify(res)
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"MDM import failed: {str(e)}"}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route("/api/admin/signature/upload", methods=["POST"])
@admin_required
def api_admin_upload_signature():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded."}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected."}), 400
    
    uploads_dir = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    filepath = os.path.join(uploads_dir, "digital_signature.jpg")
    
    try:
        file.save(filepath)
        return jsonify({"success": True, "message": "Digital Signature uploaded successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Signature save failed: {str(e)}"}), 500


@app.route("/api/results", methods=["GET"])
@login_required
def api_get_student_results():
    student_id = session["student_id"]
    results_records = Result.query.filter_by(student_id=student_id).order_by(Result.id.desc()).all()
    
    res = []
    for r in results_records:
        subjects_list = []
        for s in r.subjects:
            subjects_list.append({
                "subject_code": s.subject_code or "-",
                "subject_name": s.subject_name,
                "internal_marks": s.internal_marks,
                "external_marks": s.external_marks,
                "practical_marks": s.practical_marks,
                "total_marks": s.total_marks,
                "grade": s.grade
            })
            
        res.append({
            "id": r.id,
            "semester": r.semester.name if r.semester else "N/A",
            "academic_year": r.academic_year.name if r.academic_year else "N/A",
            "exam_type": r.exam_type,
            "sgpa": r.sgpa or "-",
            "cgpa": r.cgpa or "-",
            "status": r.status or "Pass",
            "subjects": subjects_list
        })
    return jsonify(res)


@app.route("/api/years", methods=["GET"])
@login_required
def api_get_years():
    years = AcademicYear.query.all()
    return jsonify([{"id": y.id, "name": y.name} for y in years])


@app.route("/api/semesters", methods=["GET"])
@login_required
def api_get_semesters():
    sems = Semester.query.all()
    return jsonify([{"id": s.id, "name": s.name} for s in sems])


# ---------------------------------------------------------------------
# MODULE 15: HEAD ADMIN MANAGEMENT ENDPOINTS
# ---------------------------------------------------------------------
@app.route("/api/admin/list", methods=["GET"])
@admin_required
def api_list_admins():
    if session.get("admin_type") != "head_admin":
        return jsonify({"error": "Unauthorized. Head Admin only."}), 403
    
    admins = db.session.query(Admin).join(User).all()
    res = []
    for a in admins:
        dept = Department.query.get(a.department_id) if a.department_id else None
        res.append({
            "admin_id": a.admin_id,
            "name": a.user.name,
            "department": dept.name if dept else "Head Admin",
            "department_code": dept.code if dept else "HEAD",
            "created_at": a.user.created_at
        })
    return jsonify(res)


@app.route("/api/admin/create", methods=["POST"])
@admin_required
def api_create_admin():
    if session.get("admin_type") != "head_admin":
        return jsonify({"success": False, "message": "Unauthorized. Head Admin only."}), 403
        
    data = request.get_json() or {}
    admin_id = data.get("admin_id", "").strip()
    name = data.get("name", "").strip()
    password = data.get("password", "")
    dept_code = data.get("department_code", "").strip()
    
    if not admin_id or not name or not password:
        return jsonify({"success": False, "message": "Admin ID, Name and Password are required."}), 400
        
    existing = User.query.get(admin_id)
    if existing:
        return jsonify({"success": False, "message": "Admin ID already exists."}), 400
        
    dept = None
    if dept_code and dept_code != "HEAD":
        dept = Department.query.filter_by(code=dept_code).first()
        if not dept:
            dept = Department(code=dept_code, name=f"{dept_code} Department")
            db.session.add(dept)
            db.session.commit()
            
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    u = User(
        id=admin_id,
        password_hash=generate_password_hash(password),
        name=name,
        role="admin",
        created_at=now_str
    )
    db.session.add(u)
    db.session.commit()
    
    a = Admin(
        admin_id=admin_id,
        department_id=dept.id if dept else None
    )
    db.session.add(a)
    db.session.commit()
    
    return jsonify({"success": True, "message": f"Admin {name} created successfully!"})


@app.route("/api/admin/delete", methods=["DELETE"])
@admin_required
def api_delete_admin():
    if session.get("admin_type") != "head_admin":
        return jsonify({"success": False, "message": "Unauthorized. Head Admin only."}), 403
        
    data = request.get_json() or {}
    admin_id = data.get("admin_id", "").strip()
    
    if admin_id == "HEAD01" or admin_id == session.get("student_id"):
        return jsonify({"success": False, "message": "Cannot delete primary Head Admin or yourself."}), 400
        
    u = User.query.get(admin_id)
    if u:
        db.session.delete(u)
        db.session.commit()
        return jsonify({"success": True, "message": f"Admin {admin_id} deleted successfully."})
    return jsonify({"success": False, "message": "Admin not found."}), 404



# ---------------------------------------------------------------------
# CLOUD INTEGRATION API (private Supabase Storage + Firebase Firestore)
# These routes are additive; existing local-upload routes remain unchanged.
# ---------------------------------------------------------------------
@app.route("/api/cloud-files/upload", methods=["POST"])
@login_required
def api_cloud_file_upload():
    """Upload a private file. Storage path is namespaced by the authenticated user."""
    import uuid
    from cloud_integrations import upload_private_file
    if "file" not in request.files:
        return jsonify({"success": False, "message": "Choose a file to upload."}), 400
    file = request.files["file"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"success": False, "message": "File type is not allowed."}), 400
    student_id = str(session.get("student_id", ""))
    role = "admin" if session.get("role") == "admin" else "student"
    safe_name = secure_filename(file.filename)
    object_path = f"{role}/{student_id}/{uuid.uuid4().hex}_{safe_name}"
    try:
        upload_private_file(file.stream, object_path, file.mimetype or "application/octet-stream")
        # Store only non-sensitive metadata in Firestore when credentials are configured.
        try:
            from cloud_integrations import get_firestore_client
            get_firestore_client().collection("file_metadata").document(uuid.uuid4().hex).set({
                "owner_id": student_id, "owner_role": role, "object_path": object_path,
                "original_name": safe_name, "content_type": file.mimetype or "application/octet-stream",
                "created_at": datetime.utcnow().isoformat() + "Z"
            })
        except RuntimeError:
            # Storage upload can still work when Firestore is not yet configured.
            pass
        return jsonify({"success": True, "object_path": object_path, "filename": safe_name,
                        "message": "File uploaded to private cloud storage."}), 201
    except Exception as exc:
        app.logger.exception("Cloud file upload failed")
        return jsonify({"success": False, "message": "Cloud upload failed. Check server configuration."}), 503

@app.route("/api/cloud-files/signed-url", methods=["POST"])
@login_required
def api_cloud_file_signed_url():
    """Create short-lived download URL only after ownership/admin authorization."""
    from cloud_integrations import create_private_download_url
    data = request.get_json(silent=True) or {}
    object_path = str(data.get("object_path", ""))
    if not object_path or object_path.startswith("/") or ".." in object_path.split("/"):
        return jsonify({"success": False, "message": "Invalid file path."}), 400
    student_id = str(session.get("student_id", ""))
    is_admin = session.get("role") == "admin"
    if not is_admin and not object_path.startswith(f"student/{student_id}/"):
        return jsonify({"success": False, "message": "You are not allowed to access this file."}), 403
    try:
        signed_url = create_private_download_url(object_path, expires_in=120)
        if not signed_url:
            raise RuntimeError("Storage did not return a signed URL")
        return jsonify({"success": True, "signed_url": signed_url, "expires_in": 120})
    except Exception:
        app.logger.exception("Cloud signed URL creation failed")
        return jsonify({"success": False, "message": "Could not create download link."}), 503

@app.route("/api/messages", methods=["GET", "POST"])
@login_required
def api_cloud_messages():
    """Basic Firestore-backed messaging API; authenticated users only."""
    from cloud_integrations import get_firestore_client
    student_id = str(session.get("student_id", ""))
    role = "admin" if session.get("role") == "admin" else "student"
    try:
        store = get_firestore_client()
        conversation_id = str(request.args.get("conversation_id") or (request.get_json(silent=True) or {}).get("conversation_id") or "general")
        if len(conversation_id) > 100 or not conversation_id.replace("-", "").replace("_", "").isalnum():
            return jsonify({"success": False, "message": "Invalid conversation ID."}), 400
        messages = store.collection("conversations").document(conversation_id).collection("messages")
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            body = str(data.get("message", "")).strip()
            if not body or len(body) > 4000:
                return jsonify({"success": False, "message": "Message must be between 1 and 4000 characters."}), 400
            doc = messages.document()
            doc.set({"sender_id": student_id, "sender_role": role, "message": body,
                    "created_at": datetime.utcnow().isoformat() + "Z"})
            return jsonify({"success": True, "message_id": doc.id}), 201
        rows = messages.order_by("created_at").limit(100).stream()
        return jsonify({"success": True, "messages": [{"id": row.id, **row.to_dict()} for row in rows]})
    except Exception:
        app.logger.exception("Firestore messaging request failed")
        return jsonify({"success": False, "message": "Messaging service is not configured or unavailable."}), 503


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
