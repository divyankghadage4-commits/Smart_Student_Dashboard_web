import pandas as pd
import re
import math
from datetime import datetime
from database import db
from models import Student, Subject, DailyAttendance, AcademicYear, Semester, Result, ResultSubject, Attendance, AttendanceSubject, MDMFaculty, User

class ExcelImportService:
    @staticmethod
    def normalize_header(header):
        """Normalize string to compare headers safely: lowercase, remove spaces/underscores/dashes."""
        if pd.isna(header) or not isinstance(header, str):
            return ""
        return re.sub(r'[\s_\-\.\(\)]', '', header.strip().lower())

    @staticmethod
    def match_column(columns, targets):
        """Find index of column matching any of the targets (case-insensitive, ignoring spaces)."""
        normalized_targets = [ExcelImportService.normalize_header(t) for t in targets]
        for idx, col in enumerate(columns):
            norm_col = ExcelImportService.normalize_header(str(col))
            if any(t in norm_col or norm_col in t for t in normalized_targets if t):
                return idx
        return None

    @staticmethod
    def get_row_value(row, col_idx, default=None):
        if col_idx is None or col_idx >= len(row):
            return default
        val = row[col_idx]
        if pd.isna(val) or val == 'nan' or val == 'None' or str(val).strip() == '':
            return default
        return val

    @staticmethod
    def find_student(roll_val=None, prn_val=None, name_val=None):
        """
        Attempts to locate a student by Roll Number, PRN, or Fuzzy Name overlap.
        """
        # 1. Try Roll Number Lookup
        if roll_val and str(roll_val).strip() and str(roll_val).strip().lower() not in ['nan', 'none', '']:
            r_val = str(roll_val).strip()
            if r_val.endswith('.0'): r_val = r_val[:-2]
            student = Student.query.filter_by(roll_number=r_val).first()
            if student:
                return student
                
        # 2. Try PRN Lookup
        if prn_val and str(prn_val).strip() and str(prn_val).strip().lower() not in ['nan', 'none', '']:
            p_val = str(prn_val).strip()
            if p_val.endswith('.0'): p_val = p_val[:-2]
            student = Student.query.filter_by(prn_number=p_val).first()
            if student:
                return student
                
        # 3. Try Fuzzy Name Overlap Lookup
        if name_val and str(name_val).strip() and str(name_val).strip().lower() not in ['nan', 'none', '']:
            n_val = str(name_val).strip().lower()
            import re
            excel_words = set(re.findall(r'[a-zA-Z0-9]+', n_val))
            # Require at least 2 words to avoid single-word mismatch false positives
            if len(excel_words) >= 2:
                students = Student.query.all()
                for s in students:
                    db_name = s.user.name.strip().lower() if s.user else ""
                    db_words = set(re.findall(r'[a-zA-Z0-9]+', db_name))
                    # Exact set comparison (word order independent)
                    if excel_words == db_words:
                        return s
                    # Overlap/Intersection check
                    intersection = excel_words.intersection(db_words)
                    if len(intersection) >= 2 and len(intersection) >= min(len(excel_words), len(db_words)):
                        return s
        return None

    @staticmethod
    def import_attendance(file_path, academic_year_id=None, semester_id=None, as_of_date=None):
        """
        Parses cumulative student attendance sheet and updates/inserts into Attendance / AttendanceSubject tables.
        Matches students by Roll Number or PRN.
        """
        df_raw = pd.read_excel(file_path, header=None)
        
        # 1. Locate the header row containing "roll", "prn", or "name"
        roll_row_idx = None
        roll_col_idx = None
        prn_col_idx = None
        name_col_idx = None
        
        for r_idx in range(min(15, len(df_raw))):
            row_vals = [str(x).lower().strip() for x in df_raw.iloc[r_idx]]
            for c_idx, val in enumerate(row_vals):
                if any(x in val for x in ['rollno', 'roll no', 'rollnumber', 'studentroll', 'student id', 'studentid', 'roll number', 'roll']):
                    roll_row_idx = r_idx
                    roll_col_idx = c_idx
                if 'name' in val or 'studentname' in val:
                    roll_row_idx = r_idx
                    name_col_idx = c_idx
                if any(x in val for x in ['prn', 'prnnumber', 'prnno']):
                    roll_row_idx = r_idx
                    prn_col_idx = c_idx
            if roll_row_idx is not None:
                break
                
        if roll_row_idx is None:
            return {"success": False, "message": "Failed to locate any student identifier column (Roll Number, PRN, or Name) in the sheet.", "imported": 0, "updated": 0, "skipped": 0, "failed": 0, "details": []}

        # Determine batch details if present (e.g. from cell values near top)
        batch_val = "General"
        for r in range(roll_row_idx):
            for c in range(len(df_raw.columns)):
                val_str = str(df_raw.iloc[r, c]).strip()
                if "batch" in val_str.lower():
                    batch_val = val_str
                    break
        
        # 2. Extract and forward fill subject names
        subject_row = df_raw.iloc[roll_row_idx].copy()
        filled_subjects = []
        current_subject = None
        for val in subject_row:
            val_str = str(val).strip()
            if val_str and val_str != 'nan':
                current_subject = val_str
            filled_subjects.append(current_subject)

        # 3. Identify sub-header row (e.g. L, T, P)
        sub_header_row_idx = None
        for offset in [0, 1, 2]:
            idx = roll_row_idx + offset
            if idx < len(df_raw):
                row_vals = [str(x).strip().upper() for x in df_raw.iloc[idx]]
                if any(x in ['L', 'T', 'P', 'TOTAL', 'PER', '% TH', '% PR', '%TH+%PR'] for x in row_vals):
                    sub_header_row_idx = idx
                    break
        if sub_header_row_idx is None:
            sub_header_row_idx = roll_row_idx + 1
            
        sub_headers = [str(x).strip().upper() for x in df_raw.iloc[sub_header_row_idx]]

        # Find conducted counts row (row containing counts above sub_headers/student row)
        conducted_row_idx = None
        # Check 2 rows above roll_row_idx first
        for idx in range(max(0, roll_row_idx - 2), roll_row_idx + 1):
            if idx == sub_header_row_idx:
                continue
            row_str = " ".join([str(x) for x in df_raw.iloc[idx]])
            if "lectures" in row_str.lower() or "conducted" in row_str.lower() or any(str(x).isdigit() for x in df_raw.iloc[idx]):
                conducted_row_idx = idx
                
        conducted_counts = {}
        for c_idx in range(len(df_raw.columns)):
            if conducted_row_idx is not None:
                val = df_raw.iloc[conducted_row_idx, c_idx]
                try:
                    conducted_counts[c_idx] = int(float(val))
                except:
                    conducted_counts[c_idx] = 0
            else:
                conducted_counts[c_idx] = 0

        # 4. Map columns
        subject_mappings = []
        meta_columns = {}
        
        for c_idx in range(len(df_raw.columns)):
            subj = filled_subjects[c_idx]
            sub_h = sub_headers[c_idx]
            
            if roll_col_idx is not None and c_idx == roll_col_idx:
                meta_columns['roll'] = c_idx
                continue
            if name_col_idx is not None and c_idx == name_col_idx:
                meta_columns['name'] = c_idx
                continue
            if prn_col_idx is not None and c_idx == prn_col_idx:
                meta_columns['prn'] = c_idx
                continue
                
            subj_lower = str(subj).lower() if subj else ""
            sub_h_lower = str(sub_h).lower() if sub_h else ""
            
            if 'remark' in subj_lower or 'remark' in sub_h_lower:
                meta_columns['remark'] = c_idx
            elif '%th+%pr' in sub_h_lower or 'th+%pr' in sub_h_lower or 'overall' in subj_lower:
                meta_columns['overall_pct'] = c_idx
            elif '% th' in sub_h_lower or 'th' in sub_h_lower or '%th' in sub_h_lower:
                meta_columns['theory_pct'] = c_idx
            elif '% pr' in sub_h_lower or 'pr' in sub_h_lower or '%pr' in sub_h_lower:
                meta_columns['practical_pct'] = c_idx
            elif 'total' in subj_lower and sub_h == 'L':
                meta_columns['total_theory_att'] = c_idx
            elif 'total p' in subj_lower or ('total' in subj_lower and sub_h == 'P'):
                meta_columns['total_practical_att'] = c_idx
            elif subj and subj != 'nan' and sub_h in ['L', 'T', 'P', 'L/T', 'L+T']:
                subject_mappings.append({
                    'col_idx': c_idx,
                    'subject_name': subj,
                    'type': 'theory' if sub_h in ['L', 'T', 'L/T', 'L+T'] else 'practical',
                    'conducted': conducted_counts.get(c_idx, 0)
                })

        # Parse student rows
        start_data_idx = max(sub_header_row_idx, conducted_row_idx or 0) + 1
        success_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        details = []
        
        for r_idx in range(start_data_idx, len(df_raw)):
            row = df_raw.iloc[r_idx]
            # Read values from mapped column indices
            r_idx_col = meta_columns.get('roll')
            p_idx_col = meta_columns.get('prn')
            n_idx_col = meta_columns.get('name')
            
            roll_val = str(row[r_idx_col]).strip() if r_idx_col is not None and not pd.isna(row[r_idx_col]) else ""
            prn_val = str(row[p_idx_col]).strip() if p_idx_col is not None and not pd.isna(row[p_idx_col]) else ""
            name_val = str(row[n_idx_col]).strip() if n_idx_col is not None and not pd.isna(row[n_idx_col]) else ""
            
            # Skip overall summary rows
            id_to_check = roll_val or prn_val or name_val
            if not id_to_check or id_to_check.lower() in ['nan', 'none', ''] or any(k in id_to_check.lower() for k in ['class', 'coordinator', 'hod', 'total', 'average']):
                continue
                
            # Perform unified lookup with fuzzy name matching
            student = ExcelImportService.find_student(roll_val, prn_val, name_val)
            if not student:
                skipped_count += 1
                details.append(f"Row {r_idx + 1}: Student with Roll '{roll_val}', PRN '{prn_val}', or Name '{name_val}' not found. Skipped.")
                continue
                    
            try:
                # Find or create Attendance summary record
                att_record = Attendance.query.filter_by(
                    student_id=student.student_id, 
                    semester_id=semester_id or student.semester_id,
                    academic_year_id=academic_year_id or student.year_id
                ).first()
                
                is_update = False
                if att_record:
                    is_update = True
                else:
                    att_record = Attendance(
                        student_id=student.student_id,
                        semester_id=semester_id or student.semester_id,
                        academic_year_id=academic_year_id or student.year_id
                    )
                    db.session.add(att_record)
                
                # Set details
                att_record.batch = batch_val
                att_record.as_of_date = as_of_date or datetime.now().strftime("%d %B, %Y")
                att_record.remark = ExcelImportService.get_row_value(row, meta_columns.get('remark'), 'Def')
                
                # Percentages
                att_record.theory_percentage = min(100.0, float(ExcelImportService.get_row_value(row, meta_columns.get('theory_pct'), 0.0)))
                att_record.practical_percentage = min(100.0, float(ExcelImportService.get_row_value(row, meta_columns.get('practical_pct'), 0.0)))
                att_record.overall_percentage = min(100.0, float(ExcelImportService.get_row_value(row, meta_columns.get('overall_pct'), 0.0)))
                
                # Aggregations
                db.session.flush() # Populate ID if inserting
                
                # Parse subject details
                existing_subjects = {s.subject_name: s for s in att_record.subjects}
                
                total_theory_conducted = 0
                total_theory_attended = 0
                total_practical_conducted = 0
                total_practical_attended = 0
                
                for mapping in subject_mappings:
                    c_idx = mapping['col_idx']
                    s_name = mapping['subject_name']
                    s_type = mapping['type']
                    cond_qty = mapping['conducted']
                    
                    val_att = row[c_idx]
                    try:
                        att_qty = int(float(val_att)) if not pd.isna(val_att) else 0
                    except:
                        att_qty = 0
                        
                    # Find matching database subject record to link subject_id
                    db_sub = Subject.query.filter_by(name=s_name).first()
                    if not db_sub:
                        db_sub = Subject.query.filter(Subject.name.ilike(s_name)).first()
                        
                    att_sub = existing_subjects.get(s_name)
                    if not att_sub:
                        att_sub = AttendanceSubject(
                            attendance_id=att_record.id,
                            subject_name=s_name,
                            subject_id=db_sub.id if db_sub else None
                        )
                        db.session.add(att_sub)
                        
                    if s_type == 'theory':
                        att_sub.theory_conducted = cond_qty
                        att_sub.theory_attended = att_qty
                        total_theory_conducted += cond_qty
                        total_theory_attended += att_qty
                    else:
                        att_sub.practical_conducted = cond_qty
                        att_sub.practical_attended = att_qty
                        total_practical_conducted += cond_qty
                        total_practical_attended += att_qty
                        
                att_record.total_theory_conducted = total_theory_conducted
                att_record.total_theory_attended = total_theory_attended
                att_record.total_practical_conducted = total_practical_conducted
                att_record.total_practical_attended = total_practical_attended
                
                if att_record.theory_percentage == 0.0 and total_theory_conducted > 0:
                    att_record.theory_percentage = min(100.0, round((total_theory_attended / total_theory_conducted) * 100, 1))
                if att_record.practical_percentage == 0.0 and total_practical_conducted > 0:
                    att_record.practical_percentage = min(100.0, round((total_practical_attended / total_practical_conducted) * 100, 1))
                if att_record.overall_percentage == 0.0:
                    grand_conducted = total_theory_conducted + total_practical_conducted
                    grand_attended = total_theory_attended + total_practical_attended
                    if grand_conducted > 0:
                        att_record.overall_percentage = min(100.0, round((grand_attended / grand_conducted) * 100, 1))
                
                if is_update:
                    updated_count += 1
                else:
                    success_count += 1
                    
            except Exception as e:
                failed_count += 1
                details.append(f"Row {r_idx + 1}: Error processing record for Roll '{roll_val}': {str(e)}")
                
        db.session.commit()
        return {
            "success": True, 
            "message": "Attendance spreadsheet imported successfully.",
            "imported": success_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "details": details
        }

    @staticmethod
    def import_results(file_path, academic_year_id=None, semester_id=None, exam_type=None):
        """
        Parses results Excel sheet and updates/inserts into Result / ResultSubject tables.
        Matches students by Roll Number or PRN.
        """
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        
        # 1. Identify columns
        cols = list(df.columns)
        roll_idx = ExcelImportService.match_column(cols, ['rollnumber', 'rollno', 'roll', 'studentid', 'student id'])
        prn_idx = ExcelImportService.match_column(cols, ['prn', 'prnnumber', 'prnno'])
        name_idx = ExcelImportService.match_column(cols, ['studentname', 'name', 'fullname'])
        
        sub_code_idx = ExcelImportService.match_column(cols, ['subjectcode', 'subcode', 'code'])
        sub_name_idx = ExcelImportService.match_column(cols, ['subjectname', 'subject', 'subname'])
        
        int_idx = ExcelImportService.match_column(cols, ['internalmarks', 'internal', 'ise', 'mse'])
        ext_idx = ExcelImportService.match_column(cols, ['externalmarks', 'external', 'ese', 'endsem'])
        prac_idx = ExcelImportService.match_column(cols, ['practicalmarks', 'practical', 'pr'])
        tot_idx = ExcelImportService.match_column(cols, ['totalmarks', 'total', 'tot'])
        grade_idx = ExcelImportService.match_column(cols, ['grade', 'lettergrade'])
        
        cgpa_idx = ExcelImportService.match_column(cols, ['cgpa'])
        sgpa_idx = ExcelImportService.match_column(cols, ['sgpa'])
        status_idx = ExcelImportService.match_column(cols, ['resultstatus', 'status', 'remarks'])
        
        if roll_idx is None and prn_idx is None and name_idx is None:
            return {"success": False, "message": "Failed to map Roll Number, PRN, or Student Name column in the spreadsheet.", "imported": 0, "updated": 0, "skipped": 0, "failed": 0, "details": []}
            
        success_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        details = []
        
        # Group rows by student to create consolidated Result records
        grouped_rows = {}
        for r_idx, row in df.iterrows():
            roll_val = str(ExcelImportService.get_row_value(row, roll_idx, '')).strip()
            prn_val = str(ExcelImportService.get_row_value(row, prn_idx, '')).strip()
            name_val = str(ExcelImportService.get_row_value(row, name_idx, '')).strip()
            
            if roll_val.endswith('.0'): roll_val = roll_val[:-2]
            if prn_val.endswith('.0'): prn_val = prn_val[:-2]
            
            student = ExcelImportService.find_student(roll_val, prn_val, name_val)
            if not student:
                skipped_count += 1
                details.append(f"Row {r_idx + 2}: Student with Roll '{roll_val}', PRN '{prn_val}', or Name '{name_val}' not found in database. Skipped.")
                continue
                
            student_id = student.student_id
            if student_id not in grouped_rows:
                grouped_rows[student_id] = {
                    'student': student,
                    'rows': []
                }
            grouped_rows[student_id]['rows'].append((r_idx + 2, row))

        for student_id, data_group in grouped_rows.items():
            student = data_group['student']
            rows = data_group['rows']
            
            try:
                # Find or create Result record
                res_record = Result.query.filter_by(
                    student_id=student.student_id,
                    academic_year_id=academic_year_id or student.year_id,
                    semester_id=semester_id or student.semester_id,
                    exam_type=exam_type or "End Semester"
                ).first()
                
                is_update = False
                if res_record:
                    is_update = True
                else:
                    res_record = Result(
                        student_id=student.student_id,
                        academic_year_id=academic_year_id or student.year_id,
                        semester_id=semester_id or student.semester_id,
                        exam_type=exam_type or "End Semester"
                    )
                    db.session.add(res_record)
                
                # Fetch GPA and overall status details from the first row of student records
                first_row = rows[0][1]
                
                try: res_record.sgpa = float(ExcelImportService.get_row_value(first_row, sgpa_idx, 0.0))
                except: res_record.sgpa = None
                
                try: res_record.cgpa = float(ExcelImportService.get_row_value(first_row, cgpa_idx, 0.0))
                except: res_record.cgpa = None
                
                res_record.status = ExcelImportService.get_row_value(first_row, status_idx, "Pass")
                
                db.session.flush() # Populate Result ID if new
                
                # Populate subject grades
                existing_subjects = {s.subject_name.lower().strip(): s for s in res_record.subjects}
                
                for line_no, row in rows:
                    sub_name = str(ExcelImportService.get_row_value(row, sub_name_idx, "General Subject")).strip()
                    sub_code = str(ExcelImportService.get_row_value(row, sub_code_idx, "")).strip()
                    
                    db_sub = Subject.query.filter_by(name=sub_name).first()
                    if not db_sub and sub_code:
                        db_sub = Subject.query.filter_by(code=sub_code).first()
                        
                    res_sub = existing_subjects.get(sub_name.lower().strip())
                    if not res_sub:
                        res_sub = ResultSubject(
                            result_id=res_record.id,
                            subject_name=sub_name,
                            subject_code=sub_code,
                            subject_id=db_sub.id if db_sub else None
                        )
                        db.session.add(res_sub)
                    else:
                        res_sub.subject_code = sub_code
                        res_sub.subject_id = db_sub.id if db_sub else res_sub.subject_id
                        
                    def clean_marks(val):
                        if val is None or pd.isna(val) or str(val).strip() == '': return 0.0
                        try: return float(val)
                        except: return 0.0
                        
                    res_sub.internal_marks = clean_marks(ExcelImportService.get_row_value(row, int_idx))
                    res_sub.external_marks = clean_marks(ExcelImportService.get_row_value(row, ext_idx))
                    res_sub.practical_marks = clean_marks(ExcelImportService.get_row_value(row, prac_idx))
                    res_sub.total_marks = clean_marks(ExcelImportService.get_row_value(row, tot_idx))
                    res_sub.grade = str(ExcelImportService.get_row_value(row, grade_idx, "F")).strip()
                
                if is_update:
                    updated_count += len(rows)
                else:
                    success_count += len(rows)
                    
            except Exception as e:
                failed_count += len(rows)
                details.append(f"Roll '{student_key}': Transaction failed: {str(e)}")
                
        db.session.commit()
        return {
            "success": True,
            "message": "Results imported successfully.",
            "imported": success_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "details": details
        }

    @staticmethod
    def import_mdm(file_path):
        """
        Parses MDM allocation PDF or Excel and assigns mentor_id to student records.
        """
        success_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        details = []

        # Read the file
        if file_path.endswith('.pdf'):
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                raw_text = ""
                for page in reader.pages:
                    raw_text += page.extract_text() + "\n"
            except Exception as e:
                return {"success": False, "message": f"Failed to read PDF: {str(e)}", "imported": 0, "updated": 0, "skipped": 0, "failed": 0, "details": []}
            
            lines = raw_text.split('\n')
            
            department_mentors = {
                "CIVIL": {"name": "Dr. R. V. Patel (Civil Engg Dept)", "dept": "Civil Engineering", "email": "rvpatel.civil@dakoekarad.ac.in", "phone": "+91 9845125478"},
                "MECH": {"name": "Prof. S. K. Deshmukh (Mech Dept)", "dept": "Mechanical Engineering", "email": "skdeshmukh.mech@dakoekarad.ac.in", "phone": "+91 9425164879"},
                "ETC": {"name": "Dr. Mrs. S. A. Gujar (ETC Dept)", "dept": "Electronics & Telecommunication", "email": "sagujar.etc@dakoekarad.ac.in", "phone": "+91 9301458962"}
            }
            
            for line in lines:
                parts = line.strip().split()
                if len(parts) < 4:
                    continue
                roll_num = None
                prn_num = None
                branch_val = None
                
                for p in parts:
                    if p.isdigit() and len(p) == 9:
                        roll_num = p
                    elif p.isdigit() and len(p) == 10:
                        prn_num = p
                        
                last_word = parts[-1].upper()
                if last_word in ["CIVIL", "MECH", "ETC", "CSE"]:
                    branch_val = last_word
                    
                if not roll_num and not prn_num:
                    continue
                    
                student = ExcelImportService.find_student(roll_num, prn_num, None)
                    
                if not student:
                    skipped_count += 1
                    details.append(f"Student Roll '{roll_num}' / PRN '{prn_num}' not found. Allocation skipped.")
                    continue
                    
                if not branch_val:
                    branch_val = "ETC"
                    
                mentor_info = department_mentors.get(branch_val, department_mentors["ETC"])
                
                try:
                    mentor = MDMFaculty.query.filter_by(name=mentor_info["name"]).first()
                    if not mentor:
                        mentor = MDMFaculty(
                            name=mentor_info["name"],
                            department=mentor_info["dept"],
                            email=mentor_info["email"],
                            phone=mentor_info["phone"]
                        )
                        db.session.add(mentor)
                        db.session.flush()
                        
                    student.mentor_id = mentor.id
                    updated_count += 1
                except Exception as e:
                    failed_count += 1
                    details.append(f"Roll '{roll_num}': Error assigning mentor: {str(e)}")
        else:
            try:
                df = pd.read_excel(file_path)
                df.columns = [str(c).strip() for c in df.columns]
                cols = list(df.columns)
                
                roll_idx = ExcelImportService.match_column(cols, ['rollnumber', 'rollno', 'roll', 'studentid', 'student id'])
                prn_idx = ExcelImportService.match_column(cols, ['prn', 'prnnumber', 'prnno'])
                name_idx = ExcelImportService.match_column(cols, ['studentname', 'name', 'fullname'])
                mentor_idx = ExcelImportService.match_column(cols, ['mentorname', 'mentor', 'faculty', 'facultyname'])
                dept_idx = ExcelImportService.match_column(cols, ['department', 'dept', 'branch'])
                email_idx = ExcelImportService.match_column(cols, ['email', 'mentoremail'])
                phone_idx = ExcelImportService.match_column(cols, ['phone', 'mentorphone', 'mobile'])
                
                for r_idx, row in df.iterrows():
                    roll_val = str(ExcelImportService.get_row_value(row, roll_idx, '')).strip()
                    prn_val = str(ExcelImportService.get_row_value(row, prn_idx, '')).strip()
                    name_val = str(ExcelImportService.get_row_value(row, name_idx, '')).strip()
                    
                    if roll_val.endswith('.0'): roll_val = roll_val[:-2]
                    if prn_val.endswith('.0'): prn_val = prn_val[:-2]
                    
                    student = ExcelImportService.find_student(roll_val, prn_val, name_val)
                    if not student:
                        skipped_count += 1
                        details.append(f"Row {r_idx + 2}: Student with Roll '{roll_val}', PRN '{prn_val}', or Name '{name_val}' not found in database. Skipped.")
                        continue
                            
                    m_name = ExcelImportService.get_row_value(row, mentor_idx)
                    if not m_name:
                        branch_val = str(ExcelImportService.get_row_value(row, dept_idx, 'ETC')).upper().strip()
                        department_mentors = {
                            "CIVIL": {"name": "Dr. R. V. Patel (Civil Engg Dept)", "dept": "Civil Engineering", "email": "rvpatel.civil@dakoekarad.ac.in", "phone": "+91 9845125478"},
                            "MECH": {"name": "Prof. S. K. Deshmukh (Mech Dept)", "dept": "Mechanical Engineering", "email": "skdeshmukh.mech@dakoekarad.ac.in", "phone": "+91 9425164879"},
                            "ETC": {"name": "Dr. Mrs. S. A. Gujar (ETC Dept)", "dept": "Electronics & Telecommunication", "email": "sagujar.etc@dakoekarad.ac.in", "phone": "+91 9301458962"}
                        }
                        mentor_info = department_mentors.get(branch_val, department_mentors["ETC"])
                        m_name = mentor_info["name"]
                        m_dept = mentor_info["dept"]
                        m_email = mentor_info["email"]
                        m_phone = mentor_info["phone"]
                    else:
                        m_dept = ExcelImportService.get_row_value(row, dept_idx, 'Engineering')
                        m_email = ExcelImportService.get_row_value(row, email_idx, '')
                        m_phone = ExcelImportService.get_row_value(row, phone_idx, '')
                        
                    try:
                        mentor = MDMFaculty.query.filter_by(name=m_name).first()
                        if not mentor:
                            mentor = MDMFaculty(
                                name=m_name,
                                department=m_dept,
                                email=m_email,
                                phone=m_phone
                            )
                            db.session.add(mentor)
                            db.session.flush()
                            
                        student.mentor_id = mentor.id
                        updated_count += 1
                    except Exception as e:
                        failed_count += 1
                        details.append(f"Row {r_idx + 2}: Failed to assign mentor: {str(e)}")
            except Exception as e:
                return {"success": False, "message": f"Failed to read Excel allocations: {str(e)}", "imported": 0, "updated": 0, "skipped": 0, "failed": 0, "details": []}
                
        db.session.commit()
        return {
            "success": True,
            "message": "MDM Faculty allocations imported successfully.",
            "imported": success_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "details": details
        }
