# 🎓 Student Dashboard (Flask + Excel Database)

Ek complete Student Dashboard web app — login system ke saath, jisme har student
sirf apna hi data dekh sakta hai: **Profile, Assessment, Announcement, Attendance,
Clinical, aur Leave**.

- **Backend:** Python (Flask)
- **Database:** Excel file (`data/students_data.xlsx`) — pandas + openpyxl se read/write
- **Frontend:** HTML, CSS, JavaScript (no framework, fully custom UI)

---

## 📁 Folder Structure

```
student_dashboard/
├── app.py                  # Flask backend (routes + API)
├── create_database.py      # Run this to (re)generate the Excel database
├── requirements.txt        # Python dependencies
├── data/
│   └── students_data.xlsx  # Excel database (auto-created)
├── templates/
│   ├── login.html
│   └── dashboard.html
└── static/
    ├── css/style.css
    └── js/script.js
```

---

## 🚀 How to Run (VS Code)

1. **Extract this ZIP** and open the `student_dashboard` folder in VS Code.

2. **Open terminal in VS Code** (`` Ctrl + ` ``) and create a virtual environment (recommended):
   ```bash
   python -m venv venv
   ```
   Activate it:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **(Already included)** The Excel database `data/students_data.xlsx` is already
   generated with sample data. If you ever want to reset it, run:
   ```bash
   python create_database.py
   ```

5. **Run the app:**
   ```bash
   python app.py
   ```

6. Open your browser at **http://127.0.0.1:5000**

---

## 🔑 Demo Login Credentials

| Student ID | Password |
|------------|----------|
| STU001     | pass123  |
| STU002     | pass123  |
| STU003     | pass123  |

---

## ✏️ How to Add / Edit Students (Excel Database)

Open `data/students_data.xlsx` in Excel. It has 7 sheets:

| Sheet Name     | Purpose                                      |
|----------------|-----------------------------------------------|
| `Login`        | StudentID, hashed Password, Name (for login)  |
| `Profile`      | Full profile details of each student          |
| `Attendance`   | Date-wise attendance per subject               |
| `Assessment`   | Marks / test records                           |
| `Announcement` | Common announcements (visible to all students) |
| `Clinical`     | Clinical posting / ward duty records           |
| `Leave`        | Leave applications (auto-updated when a student applies via the dashboard) |

⚠️ **Important:** Passwords in the `Login` sheet are stored as **hashed** values
(not plain text), for security. To add a new student, easiest way is to edit
`create_database.py` — add a new row using `generate_password_hash("your_password")`
and re-run the script. Directly typing a plain password into the Excel `Password`
column will NOT work for login (it must be hashed).

---

## 🧩 How It Works

- Login checks credentials against the `Login` sheet in Excel.
- After login, a session is created (`Flask session`) storing the `StudentID`.
- Every API route (`/api/profile`, `/api/attendance`, etc.) filters the Excel
  data using the **logged-in student's ID only** — so no student can see
  another student's data.
- The **Leave** tab lets a student apply for leave — this appends a new row
  directly into the `Leave` sheet of the Excel file.
- Announcements are common for all students (not filtered by StudentID).

---

## 🛠️ Tech Stack

- Python 3.10+
- Flask (backend & routing)
- Pandas + Openpyxl (Excel database read/write)
- Werkzeug (secure password hashing)
- HTML5, CSS3, Vanilla JavaScript (fetch API) for the frontend

---

## 📌 Notes

- This is a demo/learning project — for production use, consider migrating from
  Excel to a proper database (SQLite/PostgreSQL/MySQL) and moving `app.secret_key`
  to an environment variable.
- Excel file gets locked if opened in Excel while the app is writing to it
  (e.g., submitting a leave application) — close the Excel file before applying leave.
