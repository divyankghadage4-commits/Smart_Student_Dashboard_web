from datetime import datetime
from database import db

# -------------------------------------------------------------
# 1. CORE RELATIONSHIPS & METADATA MODELS
# -------------------------------------------------------------

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False) # e.g. "CSE"
    name = db.Column(db.String(100), nullable=False) # e.g. "Computer Science & Engineering"

    # Relationships
    students = db.relationship('Student', back_populates='department', lazy=True)
    admins = db.relationship('Admin', back_populates='department', lazy=True)
    subjects = db.relationship('Subject', back_populates='department', lazy=True)


class AcademicYear(db.Model):
    __tablename__ = 'academic_years'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # e.g. "3rd Year", "2023-2024"

    students = db.relationship('Student', back_populates='academic_year', lazy=True)


class Semester(db.Model):
    __tablename__ = 'semesters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # e.g. "Sem 6", "Semester 6"

    students = db.relationship('Student', back_populates='semester', lazy=True)


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=True) # e.g. "CS301"
    name = db.Column(db.String(100), nullable=False) # e.g. "Computer Networks"
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)

    # Relationships
    department = db.relationship('Department', back_populates='subjects')
    daily_attendances = db.relationship('DailyAttendance', back_populates='subject', cascade='all, delete-orphan', lazy=True)
    assessments = db.relationship('Assessment', back_populates='subject', cascade='all, delete-orphan', lazy=True)
    assignments = db.relationship('Assignment', back_populates='subject', cascade='all, delete-orphan', lazy=True)


# -------------------------------------------------------------
# 2. USER AUTHENTICATION & PROFILE MODELS
# -------------------------------------------------------------

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(50), primary_key=True) # ID/StudentID/AdminID
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student') # 'student' or 'admin'
    created_at = db.Column(db.String(50), nullable=False, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_login_date = db.Column(db.String(50), nullable=True)

    # Relationships
    student_profile = db.relationship('Student', back_populates='user', uselist=False, cascade='all, delete-orphan')
    admin_profile = db.relationship('Admin', back_populates='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan', lazy=True)


class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    roll_number = db.Column(db.String(50), nullable=True)
    prn_number = db.Column(db.String(50), nullable=True)
    course = db.Column(db.String(100), nullable=True)
    year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=True)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    dob = db.Column(db.String(20), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    address = db.Column(db.Text, nullable=True)
    admission_year = db.Column(db.String(10), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    cgpa = db.Column(db.Float, default=8.5)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('mdm_faculties.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    user = db.relationship('User', back_populates='student_profile')
    department = db.relationship('Department', back_populates='students')
    academic_year = db.relationship('AcademicYear', back_populates='students')
    semester = db.relationship('Semester', back_populates='students')
    mentor = db.relationship('MDMFaculty', back_populates='students')
    
    daily_attendances = db.relationship('DailyAttendance', back_populates='student', cascade='all, delete-orphan', lazy=True)
    cumulative_attendances = db.relationship('Attendance', back_populates='student', cascade='all, delete-orphan', lazy=True)
    results = db.relationship('Result', back_populates='student', cascade='all, delete-orphan', lazy=True)
    
    assessments = db.relationship('Assessment', back_populates='student', cascade='all, delete-orphan', lazy=True)
    announcement_reads = db.relationship('AnnouncementRead', back_populates='student', cascade='all, delete-orphan', lazy=True)
    clinical_attendances = db.relationship('ClinicalAttendance', back_populates='student', cascade='all, delete-orphan', lazy=True)
    leave_applications = db.relationship('LeaveApplication', back_populates='student', cascade='all, delete-orphan', lazy=True)
    assignment_submissions = db.relationship('AssignmentSubmission', back_populates='student', cascade='all, delete-orphan', lazy=True)
    skills = db.relationship('StudentSkill', back_populates='student', cascade='all, delete-orphan', lazy=True)
    placement_applications = db.relationship('PlacementApplication', back_populates='student', cascade='all, delete-orphan', lazy=True)
    issued_books = db.relationship('IssuedBook', back_populates='student', cascade='all, delete-orphan', lazy=True)


class Admin(db.Model):
    __tablename__ = 'admins'
    admin_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)

    # Relationships
    user = db.relationship('User', back_populates='admin_profile')
    department = db.relationship('Department', back_populates='admins')


# -------------------------------------------------------------
# 3. ACADEMIC & ATTENDANCE MODULES
# -------------------------------------------------------------

class DailyAttendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), nullable=False) # 'Present', 'Absent'

    # Relationships
    student = db.relationship('Student', back_populates='daily_attendances')
    subject = db.relationship('Subject', back_populates='daily_attendances')


class Assessment(db.Model):
    __tablename__ = 'assessments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False) # 'Unit Test', 'Mid-Term', etc.
    marks_obtained = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)

    # Relationships
    student = db.relationship('Student', back_populates='assessments')
    subject = db.relationship('Subject', back_populates='assessments')


class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False) # 'Academic', 'Placement', etc.
    priority = db.Column(db.String(20), nullable=False, default='Medium') # 'Low', 'Medium', 'High', 'Urgent'
    date = db.Column(db.String(20), nullable=False)
    created_by = db.Column(db.String(50), nullable=True)

    # Relationships
    reads = db.relationship('AnnouncementRead', back_populates='announcement', cascade='all, delete-orphan', lazy=True)


class AnnouncementRead(db.Model):
    __tablename__ = 'announcement_reads'
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcements.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    read_at = db.Column(db.String(50), nullable=False)

    # Relationships
    announcement = db.relationship('Announcement', back_populates='reads')
    student = db.relationship('Student', back_populates='announcement_reads')


class ClinicalAttendance(db.Model):
    __tablename__ = 'clinical_attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    ward_lab = db.Column(db.String(100), nullable=False) # e.g. "OS Lab"
    assigned_hours = db.Column(db.Float, nullable=False)
    completed_hours = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False) # 'Scheduled', 'Present', 'Absent', 'Completed'

    # Relationships
    student = db.relationship('Student', back_populates='clinical_attendances')


class LeaveApplication(db.Model):
    __tablename__ = 'leave_applications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    from_date = db.Column(db.String(20), nullable=False)
    to_date = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending') # 'Pending', 'Approved', 'Rejected'
    admin_remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.String(50), nullable=False)

    # Relationships
    student = db.relationship('Student', back_populates='leave_applications')


# -------------------------------------------------------------
# 4. ASSIGNMENTS, PLACEMENTS, LIBRARY & NOTIFICATION MODULES
# -------------------------------------------------------------

class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    assigned_date = db.Column(db.String(20), nullable=False)
    due_date = db.Column(db.String(20), nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    attachment_path = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.String(50), nullable=True)

    # Relationships
    subject = db.relationship('Subject', back_populates='assignments')
    submissions = db.relationship('AssignmentSubmission', back_populates='assignment', cascade='all, delete-orphan', lazy=True)


class AssignmentSubmission(db.Model):
    __tablename__ = 'assignment_submissions'
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    submission_date = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    comments = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Submitted') # 'Pending', 'Submitted', 'Late', 'Graded'
    marks_obtained = db.Column(db.Float, nullable=True)

    # Relationships
    assignment = db.relationship('Assignment', back_populates='submissions')
    student = db.relationship('Student', back_populates='assignment_submissions')


class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=False) # 'Notes', 'Syllabus', etc.
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.String(50), nullable=True)
    uploaded_date = db.Column(db.String(20), nullable=False)
    uploaded_by = db.Column(db.String(50), nullable=True)


class StudentSkill(db.Model):
    __tablename__ = 'student_skills'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False) # 'Programming', 'Technical', etc.
    proficiency_level = db.Column(db.String(50), nullable=True, default='Intermediate')

    # Relationships
    student = db.relationship('Student', back_populates='skills')


class PlacementDrive(db.Model):
    __tablename__ = 'placement_drives'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False)
    job_role = db.Column(db.String(150), nullable=False)
    eligibility_criteria = db.Column(db.Text, nullable=False)
    package_lpa = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    deadline = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Active') # 'Active', 'Upcoming', 'Closed'

    # Relationships
    applications = db.relationship('PlacementApplication', back_populates='drive', cascade='all, delete-orphan', lazy=True)


class PlacementApplication(db.Model):
    __tablename__ = 'placement_applications'
    id = db.Column(db.Integer, primary_key=True)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    applied_date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Applied') # 'Applied', 'Shortlisted', etc.
    resume_path = db.Column(db.String(255), nullable=True)

    # Relationships
    drive = db.relationship('PlacementDrive', back_populates='applications')
    student = db.relationship('Student', back_populates='placement_applications')


class LibraryBook(db.Model):
    __tablename__ = 'library_books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(100), nullable=False)
    total_copies = db.Column(db.Integer, nullable=False, default=5)
    available_copies = db.Column(db.Integer, nullable=False, default=5)

    # Relationships
    issues = db.relationship('IssuedBook', back_populates='book', cascade='all, delete-orphan', lazy=True)


class IssuedBook(db.Model):
    __tablename__ = 'issued_books'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('library_books.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    issue_date = db.Column(db.String(20), nullable=False)
    due_date = db.Column(db.String(20), nullable=False)
    return_date = db.Column(db.String(20), nullable=True)
    fine_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), nullable=False, default='Issued') # 'Issued', 'Overdue', 'Returned'

    # Relationships
    book = db.relationship('LibraryBook', back_populates='issues')
    student = db.relationship('Student', back_populates='issued_books')


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=True, default='info') # 'info', 'warning', 'success', 'urgent'
    is_read = db.Column(db.Integer, default=0) # 0 for false, 1 for true
    created_at = db.Column(db.String(50), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='notifications')


# -------------------------------------------------------------
# 4. NEW BATCH IMPORT & MANAGEMENT MODELS (MDM, Cumulative Attendance, Results)
# -------------------------------------------------------------

class MDMFaculty(db.Model):
    __tablename__ = 'mdm_faculties'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(50), nullable=True)

    # Relationships
    students = db.relationship('Student', back_populates='mentor')


class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id', ondelete='CASCADE'), nullable=True)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=True)
    exam_type = db.Column(db.String(50), nullable=False) # e.g. "MSE", "ISE", "End Semester"
    sgpa = db.Column(db.Float, nullable=True)
    cgpa = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=True) # 'Pass', 'Fail'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', back_populates='results')
    semester = db.relationship('Semester')
    academic_year = db.relationship('AcademicYear')
    subjects = db.relationship('ResultSubject', back_populates='result', cascade='all, delete-orphan')


class ResultSubject(db.Model):
    __tablename__ = 'result_subjects'
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('results.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True)
    subject_code = db.Column(db.String(50), nullable=True)
    subject_name = db.Column(db.String(100), nullable=False)
    internal_marks = db.Column(db.Float, nullable=True)
    external_marks = db.Column(db.Float, nullable=True)
    practical_marks = db.Column(db.Float, nullable=True)
    total_marks = db.Column(db.Float, nullable=True)
    grade = db.Column(db.String(10), nullable=True)

    # Relationships
    result = db.relationship('Result', back_populates='subjects')
    subject = db.relationship('Subject')


class Attendance(db.Model):
    __tablename__ = 'cumulative_attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=True)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id', ondelete='CASCADE'), nullable=True)
    batch = db.Column(db.String(50), nullable=True) # e.g. "S3 Batch"
    as_of_date = db.Column(db.String(50), nullable=True) # e.g. "till 31st March, 2026"
    total_theory_conducted = db.Column(db.Integer, default=0)
    total_theory_attended = db.Column(db.Integer, default=0)
    theory_percentage = db.Column(db.Float, default=0.0)
    total_practical_conducted = db.Column(db.Integer, default=0)
    total_practical_attended = db.Column(db.Integer, default=0)
    practical_percentage = db.Column(db.Float, default=0.0)
    overall_percentage = db.Column(db.Float, default=0.0)
    remark = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', back_populates='cumulative_attendances')
    semester = db.relationship('Semester')
    academic_year = db.relationship('AcademicYear')
    subjects = db.relationship('AttendanceSubject', back_populates='attendance', cascade='all, delete-orphan')


class AttendanceSubject(db.Model):
    __tablename__ = 'attendance_subjects'
    id = db.Column(db.Integer, primary_key=True)
    attendance_id = db.Column(db.Integer, db.ForeignKey('cumulative_attendance.id', ondelete='CASCADE'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True)
    subject_code = db.Column(db.String(50), nullable=True)
    subject_name = db.Column(db.String(100), nullable=False)
    theory_conducted = db.Column(db.Integer, default=0)
    theory_attended = db.Column(db.Integer, default=0)
    practical_conducted = db.Column(db.Integer, default=0)
    practical_attended = db.Column(db.Integer, default=0)

    # Relationships
    attendance = db.relationship('Attendance', back_populates='subjects')
    subject = db.relationship('Subject')


class ImportHistory(db.Model):
    __tablename__ = 'import_history'
    id = db.Column(db.Integer, primary_key=True)
    import_type = db.Column(db.String(50), nullable=False) # 'results', 'attendance', 'students', 'mdm'
    filename = db.Column(db.String(255), nullable=True)
    success_count = db.Column(db.Integer, default=0)
    updated_count = db.Column(db.Integer, default=0)
    skipped_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
