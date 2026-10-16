/* ==========================================================================
   STUDENT ACADEMIC DASHBOARD - MODULAR JAVASCRIPT ENGINE
   ========================================================================== */

const ROLE = document.body.dataset.role;
const STUDENT_ID = document.body.dataset.studentId;
const STUDENT_NAME = document.body.dataset.studentName;

let chartAttInstance = null;
let chartAssInstance = null;

let cacheAssignments = [];
let cacheDocuments = [];

// --------------------------------------------------------------------------
// INITIALIZATION & EVENT LISTENERS
// --------------------------------------------------------------------------
window.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initSidebar();

  // Attach nav item click handlers
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach((btn) => {
    btn.addEventListener("click", () => {
      switchTab(btn.dataset.tab);
    });
  });

  // Load default initial tab
  const defaultTab = ROLE === 'admin' ? 'tab-admin-overview' : 'tab-dashboard';
  switchTab(defaultTab);

  // Cache-bust admin signature preview image on load
  if (ROLE === 'admin') {
    const preview = document.getElementById("admin-signature-preview");
    if (preview) {
      preview.src = "/static/uploads/digital_signature.jpg?t=" + new Date().getTime();
    }
  }

  // Initial notification count badge update
  updateNotificationBadge();
});

// --------------------------------------------------------------------------
// CORE HELPERS & API UTILITIES
// --------------------------------------------------------------------------
async function apiCall(url, method = "GET", body = null, isFormData = false) {
  const options = { method };
  if (body) {
    if (isFormData) {
      options.body = body;
    } else {
      options.headers = { "Content-Type": "application/json" };
      options.body = JSON.stringify(body);
    }
  }
  try {
    const res = await fetch(url, options);
    const data = await res.json();
    return data;
  } catch (err) {
    console.error(`API Error on ${url}:`, err);
    showToast("Network or server connection error.", "error");
    return null;
  }
}

function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function openModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.classList.add("active");
}

function closeModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.classList.remove("active");
}

// --------------------------------------------------------------------------
// THEME & SIDEBAR DRAWER CONTROLLER
// --------------------------------------------------------------------------
function initTheme() {
  const themeToggle = document.getElementById("theme-toggle");
  const savedTheme = localStorage.getItem("portal_theme") || "light-theme";
  document.body.className = savedTheme;
  updateThemeIcons(savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const current = document.body.classList.contains("dark-theme") ? "dark-theme" : "light-theme";
      const next = current === "dark-theme" ? "light-theme" : "dark-theme";
      document.body.className = next;
      localStorage.setItem("portal_theme", next);
      updateThemeIcons(next);
    });
  }
}

function updateThemeIcons(theme) {
  const moon = document.getElementById("theme-moon");
  const sun = document.getElementById("theme-sun");
  if (!moon || !sun) return;
  if (theme === "dark-theme") {
    moon.style.display = "none";
    sun.style.display = "inline-block";
  } else {
    moon.style.display = "inline-block";
    sun.style.display = "none";
  }
}

function initSidebar() {
  const toggleBtn = document.getElementById("sidebar-toggle");
  const sidebar = document.getElementById("sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("active");
    });
  }
}

function switchTab(tabId) {
  const navItems = document.querySelectorAll(".nav-item");
  const panes = document.querySelectorAll(".tab-pane");

  navItems.forEach((b) => {
    if (b.dataset.tab === tabId) b.classList.add("active");
    else b.classList.remove("active");
  });

  panes.forEach((p) => {
    if (p.id === tabId) p.classList.add("active");
    else p.classList.remove("active");
  });

  // Update breadcrumb title
  const activeBtn = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  const breadcrumb = document.getElementById("breadcrumb-title");
  if (activeBtn && breadcrumb) {
    breadcrumb.textContent = activeBtn.textContent.trim();
  }

  // Load Tab Specific Data
  loadTabData(tabId);
}

function loadTabData(tabId) {
  switch (tabId) {
    // Student Tabs
    case "tab-dashboard": loadDashboardSummary(); break;
    case "tab-profile": loadProfile(); break;
    case "tab-assignments": loadAssignments(); break;
    case "tab-announcements": loadAnnouncements(); break;
    case "tab-documents": loadDocuments(); break;
    case "tab-assessment": loadAssessment(); break;
    case "tab-results": loadStudentResults(); break;
    case "tab-attendance": loadAttendance(); break;
    case "tab-placement": loadPlacement(); break;
    case "tab-clinical": loadClinical(); break;
    case "tab-library": loadLibrary(); break;
    case "tab-leave": loadLeave(); break;
    // Admin Tabs
    case "tab-admin-overview": loadAdminOverview(); break;
    case "tab-admin-students": loadAdminStudents(); break;
    case "tab-admin-attendance": loadAdminAttendance(); break;
    case "tab-admin-assessment": loadAdminAssessment(); break;
    case "tab-admin-results": loadAdminResults(); break;
    case "tab-admin-assignments": loadAdminAssignments(); break;
    case "tab-admin-announcements": loadAdminAnnouncements(); break;
    case "tab-admin-documents": loadAdminDocuments(); break;
    case "tab-admin-placements": loadAdminPlacements(); break;
    case "tab-admin-clinical": loadAdminClinical(); break;
    case "tab-admin-library": loadAdminLibrary(); break;
    case "tab-admin-leave": loadAdminLeave(); break;
    case "tab-admin-profile": loadAdminProfile(); break;
    case "tab-admin-manage-admins": loadAdminsList(); break;
  }
}

// --------------------------------------------------------------------------
// MODULE 1: DASHBOARD SUMMARY
// --------------------------------------------------------------------------
async function loadDashboardSummary() {
  const data = await apiCall("/api/dashboard/summary");
  if (!data) return;

  document.getElementById("dash-att-pct").textContent = `${data.overall_attendance}%`;
  
  if (document.getElementById("dash-cgpa")) {
    document.getElementById("dash-cgpa").textContent = data.profile.cgpa || "0.0";
  }
  if (document.getElementById("dash-sgpa")) {
    document.getElementById("dash-sgpa").textContent = data.profile.sgpa || "0.0";
  }
  if (document.getElementById("dash-semester")) {
    document.getElementById("dash-semester").textContent = data.profile.semester || "N/A";
  }
  if (document.getElementById("dash-mentor")) {
    document.getElementById("dash-mentor").textContent = data.profile.mentor_name || "Not Assigned";
  }
  if (document.getElementById("dash-pending-leaves")) {
    document.getElementById("dash-pending-leaves").textContent = data.pending_leaves_count || 0;
  }

  // Mentor Card details in Profile Section
  const mName = document.getElementById("prof-mentor-name");
  if (mName) {
    mName.textContent = data.profile.mentor_name || "Not Assigned";
  }
  const mDept = document.getElementById("prof-mentor-dept");
  if (mDept) {
    mDept.textContent = data.profile.mentor_dept || "-";
  }
  const mEmail = document.getElementById("prof-mentor-email");
  if (mEmail) {
    mEmail.textContent = data.profile.mentor_email || "-";
  }
  const mPhone = document.getElementById("prof-mentor-phone");
  if (mPhone) {
    mPhone.textContent = data.profile.mentor_phone || "-";
  }

  // Unread notification badge count
  const notifBadge = document.getElementById("notif-count");
  if (notifBadge) {
    if (data.unread_notifications > 0) {
      notifBadge.textContent = data.unread_notifications;
      notifBadge.style.display = "flex";
    } else {
      notifBadge.style.display = "none";
    }
  }

  // Render Schedule
  const scheduleContainer = document.getElementById("dash-schedule-list");
  if (scheduleContainer && data.today_schedule) {
    scheduleContainer.innerHTML = data.today_schedule.map(s => `
      <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--border-color);">
        <div>
          <div style="font-weight: 700; font-size: 0.9rem;">${s.subject}</div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">${s.instructor} • ${s.room}</div>
        </div>
        <span class="badge badge-good">${s.time}</span>
      </div>
    `).join("");
  }

  // Render Recent Results list
  const recentResultsContainer = document.getElementById("dash-recent-results-list");
  if (recentResultsContainer) {
    if (data.recent_results && data.recent_results.length > 0) {
      recentResultsContainer.innerHTML = data.recent_results.map(r => `
        <div style="padding: 10px; border-radius: var(--radius-md); background: var(--bg-body); border-left: 4px solid ${r.status.toLowerCase() === 'pass' ? 'var(--green-main)' : 'var(--red-main)'}; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="font-weight: 700; font-size: 0.85rem;">${r.semester} - ${r.exam_type}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">SGPA: ${r.sgpa} | CGPA: ${r.cgpa}</div>
          </div>
          <span class="badge ${r.status.toLowerCase() === 'pass' ? 'badge-good' : 'badge-critical'}">${r.status}</span>
        </div>
      `).join("");
    } else {
      recentResultsContainer.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px;">No results published yet.</div>`;
    }
  }

  // Render Attendance Chart
  renderAttendanceChart([78, 80, 82, 85, 84, 86, 85]);
}

function renderAttendanceChart(dataPoints) {
  const ctx = document.getElementById("dash-chart-att");
  if (!ctx) return;
  if (chartAttInstance) chartAttInstance.destroy();

  chartAttInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Today'],
      datasets: [{
        label: 'Attendance Rate %',
        data: dataPoints,
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79, 70, 229, 0.1)',
        fill: true,
        tension: 0.3,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { min: 50, max: 100 }
      }
    }
  });
}

// --------------------------------------------------------------------------
// MODULE 2: PROFILE
// --------------------------------------------------------------------------
async function loadProfile() {
  const data = await apiCall("/api/profile");
  if (!data) return;

  const grid = document.getElementById("profile-details-grid");
  if (grid) {
    const fields = [
      { label: "Roll Number", val: data.roll_number },
      { label: "PRN Number", val: data.prn_number },
      { label: "Course / Branch", val: `${data.course} ${data.branch || ''}` },
      { label: "Academic Year", val: data.year },
      { label: "CGPA", val: data.cgpa || "8.5" },
      { label: "Email Address", val: data.email },
      { label: "Phone Number", val: data.phone },
      { label: "Date of Birth", val: data.dob },
      { label: "Blood Group", val: data.blood_group },
      { label: "Address", val: data.address }
    ];

    grid.innerHTML = fields.map(f => `
      <div style="background: var(--bg-main); padding: 12px; border-radius: var(--radius-md);">
        <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">${f.label}</div>
        <div style="font-size: 0.9rem; font-weight: 700; color: var(--text-main);">${f.val || '-'}</div>
      </div>
    `).join("");
  }
}

async function handlePasswordChange(e) {
  e.preventDefault();
  const old_pass = document.getElementById("pass-old").value;
  const new_pass = document.getElementById("pass-new").value;

  const res = await apiCall("/api/profile/change-password", "POST", { old_password: old_pass, new_password: new_pass });
  if (res && res.success) {
    showToast("Password updated successfully!", "success");
    document.getElementById("change-pass-form").reset();
  } else {
    showToast(res.message || "Failed to update password.", "error");
  }
}

async function uploadAvatar() {
  const input = document.getElementById("avatar-input");
  if (!input.files || !input.files[0]) return;

  const formData = new FormData();
  formData.append("avatar", input.files[0]);

  const res = await apiCall("/api/profile/avatar", "POST", formData, true);
  if (res && res.success) {
    showToast("Avatar updated!", "success");
    location.reload();
  } else {
    showToast(res.message || "Avatar upload failed.", "error");
  }
}

// --------------------------------------------------------------------------
// MODULE 3: ASSIGNMENTS
// --------------------------------------------------------------------------
async function loadAssignments() {
  const data = await apiCall("/api/assignments");
  if (!data) return;
  cacheAssignments = data;
  renderAssignmentsTable(data);
}

function renderAssignmentsTable(items) {
  const tbody = document.querySelector("#assignments-table tbody");
  if (!tbody) return;

  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7">No assignments found.</td></tr>`;
    return;
  }

  tbody.innerHTML = items.map(a => `
    <tr>
      <td><strong>${a.subject}</strong></td>
      <td>
        <div style="font-weight: 700;">${a.title}</div>
        <div style="font-size: 0.78rem; color: var(--text-muted);">${a.description}</div>
      </td>
      <td>${a.assigned_date}</td>
      <td>${a.due_date}</td>
      <td><span class="badge badge-${a.status.toLowerCase()}">${a.status}</span></td>
      <td>${a.marks_obtained !== null ? a.marks_obtained : '-'} / ${a.total_marks}</td>
      <td>
        ${a.status === 'Pending' || a.status === 'Overdue' ? 
          `<button class="btn btn-primary btn-sm" onclick="openSubmitAssignModal(${a.id})">Submit</button>` : 
          `<span style="font-size: 0.8rem; color: var(--accent-green); font-weight: 700;">Done</span>`}
      </td>
    </tr>
  `).join("");
}

function filterAssignments() {
  const q = document.getElementById("assign-search").value.toLowerCase();
  const filtered = cacheAssignments.filter(a => 
    a.subject.toLowerCase().includes(q) || a.title.toLowerCase().includes(q)
  );
  renderAssignmentsTable(filtered);
}

function openSubmitAssignModal(assignId) {
  document.getElementById("sub-assign-id").value = assignId;
  openModal("modal-submit-assign");
}

async function handleAssignmentSubmit(e) {
  e.preventDefault();
  const assignId = document.getElementById("sub-assign-id").value;
  const fileInput = document.getElementById("sub-assign-file");
  const comments = document.getElementById("sub-assign-comments").value;

  const formData = new FormData();
  formData.append("comments", comments);
  if (fileInput.files[0]) {
    formData.append("file", fileInput.files[0]);
  }

  const res = await apiCall(`/api/assignments/${assignId}/submit`, "POST", formData, true);
  if (res && res.success) {
    showToast("Assignment submitted!", "success");
    closeModal("modal-submit-assign");
    loadAssignments();
  } else {
    showToast(res.message || "Submission failed.", "error");
  }
}

// --------------------------------------------------------------------------
// MODULE 4: ANNOUNCEMENTS
// --------------------------------------------------------------------------
async function loadAnnouncements() {
  const data = await apiCall("/api/announcements");
  if (!data) return;

  const container = document.getElementById("announcements-container");
  if (!container) return;

  if (data.length === 0) {
    container.innerHTML = `<div>No campus announcements.</div>`;
    return;
  }

  container.innerHTML = data.map(a => `
    <div class="content-card" style="margin-bottom: 0;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
          <span class="badge badge-good" style="margin-bottom: 6px;">${a.category}</span>
          <h3 style="font-size: 1.1rem; font-weight: 700;">${a.title}</h3>
        </div>
        <span style="font-size: 0.8rem; color: var(--text-muted);">${a.date}</span>
      </div>
      <p style="margin-top: 8px; font-size: 0.9rem; color: var(--text-main);">${a.message}</p>
    </div>
  `).join("");
}

// --------------------------------------------------------------------------
// MODULE 5: DOCUMENTS
// --------------------------------------------------------------------------
async function loadDocuments() {
  const data = await apiCall("/api/documents");
  if (!data) return;
  cacheDocuments = data;
  renderDocumentsGrid(data);
}

function renderDocumentsGrid(docs) {
  const grid = document.getElementById("documents-grid");
  if (!grid) return;

  if (docs.length === 0) {
    grid.innerHTML = `<div>No study documents available.</div>`;
    return;
  }

  grid.innerHTML = docs.map(d => `
    <div class="content-card" style="margin-bottom: 0;">
      <span class="badge badge-warning" style="margin-bottom: 8px;">${d.category}</span>
      <h4 style="font-weight: 700; font-size: 1rem; margin-bottom: 6px;">${d.title}</h4>
      <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 12px;">${d.description || ''}</p>
      <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem; color: var(--text-muted);">
        <span>${d.file_size}</span>
        <a href="/static/${d.file_path}" download class="btn btn-secondary btn-sm">Download</a>
      </div>
    </div>
  `).join("");
}

function filterDocuments() {
  const q = document.getElementById("doc-search").value.toLowerCase();
  const filtered = cacheDocuments.filter(d => 
    d.title.toLowerCase().includes(q) || d.category.toLowerCase().includes(q)
  );
  renderDocumentsGrid(filtered);
}

// --------------------------------------------------------------------------
// MODULE 6: ASSESSMENT
// --------------------------------------------------------------------------
async function loadAssessment() {
  const data = await apiCall("/api/assessment");
  if (!data) return;

  const tbody = document.querySelector("#assessment-table tbody");
  if (tbody) {
    tbody.innerHTML = data.map(a => `
      <tr>
        <td><strong>${a.subject}</strong></td>
        <td>${a.assessment_type}</td>
        <td>${a.marks_obtained}</td>
        <td>${a.max_marks}</td>
        <td><strong>${a.percentage}%</strong></td>
        <td><span class="badge ${a.percentage >= 65 ? 'badge-good' : 'badge-critical'}">${a.grade}</span></td>
        <td>${a.date}</td>
      </tr>
    `).join("");
  }

  // Chart
  const ctx = document.getElementById("assessment-chart");
  if (ctx) {
    if (chartAssInstance) chartAssInstance.destroy();
    chartAssInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map(d => `${d.subject} (${d.assessment_type})`),
        datasets: [{
          label: 'Percentage %',
          data: data.map(d => d.percentage),
          backgroundColor: '#3b82f6',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { max: 100 } }
      }
    });
  }
}

// --------------------------------------------------------------------------
// MODULE 7: ATTENDANCE
// --------------------------------------------------------------------------
async function loadAttendance() {
  const data = await apiCall("/api/attendance");
  if (!data) return;

  document.getElementById("att-total-cnt").textContent = data.total;
  document.getElementById("att-present-cnt").textContent = data.present;
  document.getElementById("att-absent-cnt").textContent = data.absent;

  const badgeEl = document.getElementById("attendance-status-badge");
  if (badgeEl) {
    const cls = data.attendance_status === 'Good' ? 'badge-good' : (data.attendance_status === 'Warning' ? 'badge-warning' : 'badge-critical');
    badgeEl.innerHTML = `<span class="badge ${cls}" style="font-size: 0.9rem; padding: 6px 14px;">Status: ${data.attendance_status} (${data.percentage}%)</span>`;
  }

  const list = document.getElementById("subject-attendance-list");
  if (list && data.subject_breakdown) {
    list.innerHTML = data.subject_breakdown.map(s => `
      <div>
        <div style="display: flex; justify-content: space-between; font-weight: 700; font-size: 0.88rem; margin-bottom: 4px;">
          <span>${s.subject}</span>
          <span>${s.percentage}% (${s.present}/${s.total})</span>
        </div>
        <div style="height: 8px; background: var(--border-color); border-radius: var(--radius-full); overflow: hidden;">
          <div style="height: 100%; width: ${s.percentage}%; background: ${s.percentage >= 75 ? 'var(--accent-green)' : (s.percentage >= 65 ? 'var(--accent-amber)' : 'var(--accent-rose)')};"></div>
        </div>
      </div>
    `).join("");
  }
}

// --------------------------------------------------------------------------
// MODULE 8: PLACEMENT
// --------------------------------------------------------------------------
async function loadPlacement() {
  const data = await apiCall("/api/placement");
  if (!data) return;

  // Eligibility badge
  const eligBadge = document.getElementById("placement-eligibility-badge");
  if (eligBadge) {
    eligBadge.innerHTML = data.eligible ? 
      `<span class="badge badge-good">Eligible for Placements (CGPA ${data.cgpa})</span>` :
      `<span class="badge badge-critical">Ineligible for Placements</span>`;
  }

  // Skills
  const skillsContainer = document.getElementById("skills-tags-container");
  if (skillsContainer) {
    skillsContainer.innerHTML = data.skills.map(s => `
      <span class="badge badge-good" style="padding: 6px 12px; font-size: 0.82rem;">
        ${s.skill_name} (${s.proficiency_level})
        <i data-lucide="x" size="12" style="cursor: pointer; margin-left: 4px;" onclick="removeSkill(${s.id})"></i>
      </span>
    `).join("");
    lucide.createIcons();
  }

  // Drives
  const drivesContainer = document.getElementById("drives-list-container");
  if (drivesContainer && data.drives) {
    drivesContainer.innerHTML = data.drives.map(d => `
      <div class="content-card" style="margin-bottom: 0;">
        <span class="badge badge-good" style="margin-bottom: 6px;">${d.package_lpa} LPA CTC</span>
        <h3 style="font-size: 1.1rem; font-weight: 700;">${d.company_name}</h3>
        <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 8px;">${d.job_role} • ${d.location}</div>
        <p style="font-size: 0.8rem; margin-bottom: 12px;"><strong>Eligibility:</strong> ${d.eligibility_criteria}</p>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 0.78rem; color: var(--text-muted);">Deadline: ${d.deadline}</span>
          ${d.application_status === 'Not Applied' ?
            `<button class="btn btn-primary btn-sm" onclick="openApplyDriveModal(${d.id}, '${d.company_name}')">Apply Now</button>` :
            `<span class="badge badge-approved">${d.application_status}</span>`}
        </div>
      </div>
    `).join("");
  }
}

async function handleAddSkill(e) {
  e.preventDefault();
  const name = document.getElementById("skill-name").value;
  const category = document.getElementById("skill-category").value;
  const level = document.getElementById("skill-level").value;

  const res = await apiCall("/api/placement/skills", "POST", { skill_name: name, category, proficiency_level: level });
  if (res && res.success) {
    showToast("Skill added!", "success");
    closeModal("modal-add-skill");
    loadPlacement();
  }
}

async function removeSkill(id) {
  const res = await apiCall("/api/placement/skills", "DELETE", { skill_id: id });
  if (res && res.success) {
    showToast("Skill removed!", "success");
    loadPlacement();
  }
}

function openApplyDriveModal(driveId, companyName) {
  document.getElementById("drive-apply-id").value = driveId;
  document.getElementById("drive-modal-title").textContent = `Apply for ${companyName}`;
  openModal("modal-apply-drive");
}

async function handleApplyDrive(e) {
  e.preventDefault();
  const driveId = document.getElementById("drive-apply-id").value;
  const resumeInput = document.getElementById("drive-resume-file");

  const formData = new FormData();
  formData.append("drive_id", driveId);
  if (resumeInput.files[0]) {
    formData.append("resume", resumeInput.files[0]);
  }

  const res = await apiCall("/api/placement/apply", "POST", formData, true);
  if (res && res.success) {
    showToast("Application submitted!", "success");
    closeModal("modal-apply-drive");
    loadPlacement();
  } else {
    showToast(res.message || "Application failed.", "error");
  }
}

// --------------------------------------------------------------------------
// MODULE 9: CLINICAL
// --------------------------------------------------------------------------
async function loadClinical() {
  const data = await apiCall("/api/clinical");
  if (!data) return;

  document.getElementById("clinical-completed-hrs").textContent = `${data.total_completed} / ${data.total_assigned} hrs`;

  const tbody = document.querySelector("#clinical-table tbody");
  if (tbody) {
    tbody.innerHTML = data.records.map(c => `
      <tr>
        <td>${c.date}</td>
        <td><strong>${c.ward_lab}</strong></td>
        <td>${c.assigned_hours} hrs</td>
        <td>${c.completed_hours} hrs</td>
        <td><span class="badge badge-${c.status.toLowerCase()}">${c.status}</span></td>
      </tr>
    `).join("");
  }
}

// --------------------------------------------------------------------------
// MODULE 10: LIBRARY
// --------------------------------------------------------------------------
async function loadLibrary() {
  const data = await apiCall("/api/library");
  if (!data) return;

  const tbody = document.querySelector("#issued-books-table tbody");
  if (tbody && data.issued_books) {
    if (data.issued_books.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6">No books currently issued.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.issued_books.map(b => `
      <tr>
        <td><strong>${b.title}</strong></td>
        <td>${b.author}</td>
        <td>${b.issue_date}</td>
        <td>${b.due_date}</td>
        <td>${b.fine_amount > 0 ? `<span style="color: var(--accent-rose); font-weight: 700;">Rs ${b.fine_amount}</span>` : 'Rs 0'}</td>
        <td><span class="badge badge-${b.status.toLowerCase()}">${b.status}</span></td>
      </tr>
    `).join("");
  }
}

// --------------------------------------------------------------------------
// MODULE 11: LEAVE APPLICATION
// --------------------------------------------------------------------------
async function loadLeave() {
  const data = await apiCall("/api/leave");
  if (!data) return;

  const tbody = document.querySelector("#leave-history-table tbody");
  if (tbody) {
    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4">No leave applications submitted.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.map(l => `
      <tr>
        <td><strong>${l.from_date}</strong> to <strong>${l.to_date}</strong></td>
        <td>${l.reason}</td>
        <td><span class="badge badge-${l.status.toLowerCase()}">${l.status}</span></td>
        <td>${l.admin_remarks || '-'}</td>
      </tr>
    `).join("");
  }
}

async function handleLeaveSubmit(e) {
  e.preventDefault();
  const from_date = document.getElementById("leave-from").value;
  const to_date = document.getElementById("leave-to").value;
  const reason = document.getElementById("leave-reason").value;

  const res = await apiCall("/api/leave", "POST", { from_date, to_date, reason });
  if (res && res.success) {
    showToast("Leave application submitted!", "success");
    document.getElementById("leave-form").reset();
    loadLeave();
  } else {
    showToast(res.message || "Failed to submit leave.", "error");
  }
}

// --------------------------------------------------------------------------
// ADMIN PORTAL CONTROLLERS
// --------------------------------------------------------------------------
async function loadAdminOverview() {
  const data = await apiCall("/api/admin/stats");
  if (!data) return;

  document.getElementById("adm-total-students").textContent = data.total_students;
  document.getElementById("adm-avg-att").textContent = `${data.avg_attendance}%`;
  document.getElementById("adm-pending-leaves").textContent = data.pending_leaves;
  document.getElementById("adm-active-drives").textContent = data.active_drives;
  
  if (document.getElementById("adm-results-uploaded")) {
    document.getElementById("adm-results-uploaded").textContent = data.results_uploaded || 0;
  }
  if (document.getElementById("adm-today-logins")) {
    document.getElementById("adm-today-logins").textContent = data.today_logins || 0;
  }
  
  populateAdminStudentSelectors();
}

async function loadAdminStudents() {
  const searchInput = document.getElementById("admin-student-search");
  const deptFilter = document.getElementById("admin-student-filter-dept");
  const yearFilter = document.getElementById("admin-student-filter-year");
  
  const q = searchInput ? searchInput.value.trim() : "";
  const dept = deptFilter ? deptFilter.value : "";
  const year = yearFilter ? yearFilter.value : "";
  
  const url = `/api/admin/students?q=${encodeURIComponent(q)}&department=${encodeURIComponent(dept)}&year=${encodeURIComponent(year)}`;
  const data = await apiCall(url);
  if (!data) return;

  const tbody = document.querySelector("#admin-students-table tbody");
  if (tbody) {
    if (data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center;">No students found matching your criteria.</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map(s => `
      <tr>
        <td><strong>${s.student_id}</strong></td>
        <td>${s.prn_number || '-'}</td>
        <td>
          <div style="display: flex; align-items: center; gap: 8px;">
            ${s.avatar_url ? 
              `<img src="${s.avatar_url}" style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover; cursor: pointer; border: 1px solid var(--border-color);" onclick="expandImage('${s.avatar_url}')" />` : 
              `<div class="user-avatar" style="width: 32px; height: 32px; font-size: 0.8rem; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: var(--bg-main); color: var(--primary-color); font-weight: 700;">${s.name[0]}</div>`
            }
            <span>${s.name}</span>
          </div>
        </td>
        <td>${s.course}</td>
        <td>${s.year}</td>
        <td>${s.email || '-'}</td>
        <td>
          <div style="display: flex; gap: 6px;">
            <button class="btn btn-secondary btn-sm" onclick="openEditStudentModal('${s.student_id}')">Edit</button>
            <button class="btn btn-secondary btn-sm" onclick="resetStudentPassword('${s.student_id}')">Reset Pass</button>
            <button class="btn btn-danger btn-sm" onclick="deleteStudent('${s.student_id}')">Delete</button>
          </div>
        </td>
      </tr>
    `).join("");
  }
}

function openAddStudentModal() {
  const form = document.getElementById("admin-student-form");
  if (form) form.reset();
  
  document.getElementById("adm-st-modal-title").textContent = "Add New Student Account";
  document.getElementById("adm-st-mode").value = "add";
  
  const idField = document.getElementById("adm-st-id");
  idField.readOnly = false;
  idField.style.opacity = "1";
  idField.required = true;
  
  document.getElementById("adm-st-pass-label").textContent = "Password";
  document.getElementById("adm-st-pass").required = true;
  document.getElementById("adm-st-pass").placeholder = "e.g. pass123";
  
  document.getElementById("adm-st-admission-group").style.display = "block";
  document.getElementById("adm-st-submit-btn").textContent = "Create Student";

  const avatarContainer = document.getElementById("adm-st-avatar-container");
  if (avatarContainer) avatarContainer.style.display = "none";
  
  openModal("modal-admin-student");
}

async function openEditStudentModal(sid) {
  const form = document.getElementById("admin-student-form");
  if (form) form.reset();
  
  // Fetch details from backend
  const data = await apiCall(`/api/admin/students?q=${sid}`);
  if (!data || data.length === 0) {
    showToast("Error retrieving student details.", "error");
    return;
  }
  
  const s = data.find(item => item.student_id === sid) || data[0];
  
  document.getElementById("adm-st-modal-title").textContent = "Edit Student Profile";
  document.getElementById("adm-st-mode").value = "edit";
  
  const idField = document.getElementById("adm-st-id");
  idField.value = s.student_id;
  idField.readOnly = true;
  idField.style.opacity = "0.7";
  idField.required = false;
  
  document.getElementById("adm-st-name").value = s.name;
  document.getElementById("adm-st-prn").value = s.prn_number || "";

  const avatarContainer = document.getElementById("adm-st-avatar-container");
  const avatarImg = document.getElementById("adm-st-avatar-img");
  if (avatarContainer && avatarImg) {
    if (s.avatar_url) {
      avatarImg.src = s.avatar_url;
      avatarContainer.style.display = "block";
    } else {
      avatarContainer.style.display = "none";
    }
  }
  
  document.getElementById("adm-st-pass-label").textContent = "Password (Optional)";
  document.getElementById("adm-st-pass").required = false;
  document.getElementById("adm-st-pass").placeholder = "Leave blank to keep unchanged";
  
  document.getElementById("adm-st-course").value = s.course;
  document.getElementById("adm-st-year").value = s.year || "3rd Year";
  document.getElementById("adm-st-semester").value = s.semester || "Sem 6";
  document.getElementById("adm-st-dept").value = s.department || "CSE";
  document.getElementById("adm-st-email").value = s.email || "";
  document.getElementById("adm-st-phone").value = s.phone || "";
  document.getElementById("adm-st-dob").value = s.dob || "";
  document.getElementById("adm-st-blood").value = s.blood_group || "";
  document.getElementById("adm-st-cgpa").value = s.cgpa || "8.5";
  document.getElementById("adm-st-address").value = s.address || "";
  document.getElementById("adm-st-admission-year").value = s.admission_year || "2023";
  document.getElementById("adm-st-admission-group").style.display = "none";
  
  document.getElementById("adm-st-submit-btn").textContent = "Save Changes";
  
  openModal("modal-admin-student");
}

async function handleAdminStudentSubmit(e) {
  e.preventDefault();
  const mode = document.getElementById("adm-st-mode").value;
  const sid = document.getElementById("adm-st-id").value.trim();
  const name = document.getElementById("adm-st-name").value.trim();
  const prn_number = document.getElementById("adm-st-prn").value.trim();
  const password = document.getElementById("adm-st-pass").value;
  const course = document.getElementById("adm-st-course").value.trim();
  const year = document.getElementById("adm-st-year").value;
  const semester = document.getElementById("adm-st-semester").value.trim();
  const department = document.getElementById("adm-st-dept").value;
  const email = document.getElementById("adm-st-email").value.trim();
  const phone = document.getElementById("adm-st-phone").value.trim();
  const dob = document.getElementById("adm-st-dob").value;
  const blood_group = document.getElementById("adm-st-blood").value.trim();
  const cgpa = document.getElementById("adm-st-cgpa").value;
  const address = document.getElementById("adm-st-address").value.trim();
  const admission_year = document.getElementById("adm-st-admission-year").value.trim();

  // Basic validation
  if (mode === "add" && !password) {
    showToast("Password is required for new students.", "error");
    return;
  }

  const payload = {
    student_id: sid,
    name: name,
    prn_number: prn_number,
    password: password,
    course: course,
    year: year,
    semester: semester,
    department: department,
    email: email,
    phone: phone,
    dob: dob,
    blood_group: blood_group,
    cgpa: parseFloat(cgpa) || 8.5,
    address: address,
    admission_year: admission_year
  };

  const method = mode === "add" ? "POST" : "PUT";
  const res = await apiCall("/api/admin/students", method, payload);
  if (res && res.success) {
    showToast(mode === "add" ? "Student created successfully!" : "Student record updated!", "success");
    closeModal("modal-admin-student");
    loadAdminStudents();
  } else {
    showToast(res.message || "Error processing student record.", "error");
  }
}

async function resetStudentPassword(sid) {
  const newPass = prompt(`Enter new password for student ${sid}:`);
  if (newPass === null) return; // cancelled
  if (newPass.trim() === "") {
    showToast("Password cannot be empty.", "error");
    return;
  }
  
  const res = await apiCall("/api/admin/students/reset-password", "POST", { student_id: sid, password: newPass.trim() });
  if (res && res.success) {
    showToast(`Password for ${sid} reset successfully!`, "success");
  } else {
    showToast(res.message || "Error resetting password.", "error");
  }
}

function exportStudents() {
  window.location.href = "/api/admin/students/export";
}

function triggerImportFile() {
  document.getElementById("admin-student-import-file").click();
}

async function importStudents(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  const formData = new FormData();
  formData.append("file", file);
  
  showToast("Uploading and importing students...", "info");
  
  try {
    const response = await fetch("/api/admin/students/import", {
      method: "POST",
      body: formData
    });
    const res = await response.json();
    
    if (response.ok && res.success) {
      showToast(res.message || "Students imported successfully!", "success");
      loadAdminStudents();
    } else {
      showToast(res.message || "Error importing excel.", "error");
    }
  } catch (err) {
    showToast("Network error uploading file.", "error");
  } finally {
    document.getElementById("admin-student-import-file").value = "";
  }
}

async function deleteStudent(sid) {
  if (!confirm(`Are you sure you want to delete student ${sid}?`)) return;
  const res = await apiCall("/api/admin/students", "DELETE", { student_id: sid });
  if (res && res.success) {
    showToast("Student deleted!", "success");
    loadAdminStudents();
  }
}

async function populateAdminStudentSelectors() {
  const students = await apiCall("/api/admin/students");
  if (!students) return;

  const attSelect = document.getElementById("admin-attendance-student-select");
  const assSelect = document.getElementById("admin-assessment-student-select");

  const optionsHTML = `
    <option value="">-- Select a Student --</option>
    ${students.map(s => `<option value="${s.student_id}">${s.name} (${s.student_id})</option>`).join("")}
  `;

  if (attSelect) {
    const currentVal = attSelect.value;
    attSelect.innerHTML = optionsHTML;
    attSelect.value = currentVal;
  }
  if (assSelect) {
    const currentVal = assSelect.value;
    assSelect.innerHTML = optionsHTML;
    assSelect.value = currentVal;
  }
}

async function loadAdminAttendance() {
  await populateAdminStudentSelectors();
  const select = document.getElementById("admin-attendance-student-select");
  const sid = select ? select.value : "";
  await loadAdminAttendanceForStudent(sid);
}

async function loadAdminAttendanceForStudent(studentId) {
  const tbody = document.querySelector("#admin-attendance-table tbody");
  if (!tbody) return;

  if (!studentId) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center;">Please select a student to load attendance logs.</td></tr>`;
    return;
  }

  tbody.innerHTML = `<tr><td colspan="5" style="text-align: center;">Loading attendance records...</td></tr>`;

  const data = await apiCall(`/api/admin/attendance?student_id=${studentId}`);
  if (!data) return;

  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center;">No attendance records found for this student.</td></tr>`;
    return;
  }

  tbody.innerHTML = data.map(a => `
    <tr>
      <td><strong>${a.student_name}</strong> <span style="font-size: 0.8rem; color: var(--text-muted);">(${a.student_id})</span></td>
      <td>${a.date}</td>
      <td>${a.subject}</td>
      <td><span class="badge badge-${a.status === 'Present' ? 'present' : 'absent'}">${a.status}</span></td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="deleteAttendance(${a.id})">Delete</button>
      </td>
    </tr>
  `).join("");
}

async function handleAdminAddAttendance(e) {
  e.preventDefault();
  const sid = document.getElementById("adm-att-sid").value;
  const date = document.getElementById("adm-att-date").value;
  const subject = document.getElementById("adm-att-sub").value;
  const status = document.getElementById("adm-att-status").value;

  const res = await apiCall("/api/admin/attendance", "POST", { student_id: sid, date, subject, status });
  if (res && res.success) {
    showToast("Attendance logged!", "success");
    closeModal("modal-admin-attendance");
    const select = document.getElementById("admin-attendance-student-select");
    if (select) {
      select.value = sid;
    }
    loadAdminAttendanceForStudent(sid);
  }
}

async function deleteAttendance(id) {
  if (!confirm("Are you sure you want to delete this attendance record?")) return;
  const res = await apiCall("/api/admin/attendance", "DELETE", { id });
  if (res && res.success) {
    showToast("Record deleted!", "success");
    const select = document.getElementById("admin-attendance-student-select");
    const sid = select ? select.value : "";
    loadAdminAttendanceForStudent(sid);
  }
}

async function loadAdminAssessment() {
  await populateAdminStudentSelectors();
  const select = document.getElementById("admin-assessment-student-select");
  const sid = select ? select.value : "";
  await loadAdminAssessmentForStudent(sid);
}

async function loadAdminAssessmentForStudent(studentId) {
  const tbody = document.querySelector("#admin-assessment-table tbody");
  if (!tbody) return;

  if (!studentId) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center;">Please select a student to load assessments.</td></tr>`;
    return;
  }

  tbody.innerHTML = `<tr><td colspan="7" style="text-align: center;">Loading assessments...</td></tr>`;

  const data = await apiCall(`/api/admin/assessment?student_id=${studentId}`);
  if (!data) return;

  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center;">No assessment records found for this student.</td></tr>`;
    return;
  }

  tbody.innerHTML = data.map(r => `
    <tr>
      <td><strong>${r.student_name}</strong> <span style="font-size: 0.8rem; color: var(--text-muted);">(${r.student_id})</span></td>
      <td>${r.subject}</td>
      <td>${r.assessment_type}</td>
      <td>${r.marks_obtained}</td>
      <td>${r.max_marks}</td>
      <td>${r.date}</td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="deleteAssessment(${r.id})">Delete</button>
      </td>
    </tr>
  `).join("");
}

async function handleAdminAddAssessment(e) {
  e.preventDefault();
  const sid = document.getElementById("adm-ass-sid").value;
  const subject = document.getElementById("adm-ass-sub").value;
  const type = document.getElementById("adm-ass-type").value;
  const marks = document.getElementById("adm-ass-ob").value;
  const max_marks = document.getElementById("adm-ass-mx").value;
  const date = document.getElementById("adm-ass-date").value;

  const res = await apiCall("/api/admin/assessment", "POST", { student_id: sid, subject, type, marks, max_marks, date });
  if (res && res.success) {
    showToast("Marks recorded!", "success");
    closeModal("modal-admin-assessment");
    const select = document.getElementById("admin-assessment-student-select");
    if (select) {
      select.value = sid;
    }
    loadAdminAssessmentForStudent(sid);
  } else {
    showToast(res.message || "Error recording marks.", "error");
  }
}

async function deleteAssessment(id) {
  if (!confirm("Are you sure you want to delete this assessment record?")) return;
  const res = await apiCall("/api/admin/assessment", "DELETE", { id });
  if (res && res.success) {
    showToast("Marks deleted!", "success");
    const select = document.getElementById("admin-assessment-student-select");
    const sid = select ? select.value : "";
    loadAdminAssessmentForStudent(sid);
  }
}

async function loadAdminAssignments() {
  const data = await apiCall("/api/admin/assignments");
  if (!data) return;
  const tbody = document.querySelector("#admin-assignments-table tbody");
  if (tbody) {
    tbody.innerHTML = data.map(a => `
      <tr>
        <td><strong>${a.subject}</strong></td>
        <td>${a.title}</td>
        <td>${a.due_date}</td>
        <td>${a.total_marks}</td>
        <td><button class="btn btn-danger btn-sm" onclick="deleteAssignment(${a.id})">Delete</button></td>
      </tr>
    `).join("");
  }
}

async function deleteAssignment(id) {
  const res = await apiCall("/api/admin/assignments", "DELETE", { id });
  if (res && res.success) {
    showToast("Assignment deleted!", "success");
    loadAdminAssignments();
  }
}

async function loadAdminAnnouncements() {
  const data = await apiCall("/api/admin/announcements");
  if (!data) return;
  const tbody = document.querySelector("#admin-announcements-table tbody");
  if (tbody) {
    tbody.innerHTML = data.map(a => `
      <tr>
        <td><strong>${a.title}</strong></td>
        <td>${a.category}</td>
        <td><span class="badge badge-warning">${a.priority}</span></td>
        <td>${a.date}</td>
        <td><button class="btn btn-danger btn-sm" onclick="deleteAnnouncement(${a.id})">Delete</button></td>
      </tr>
    `).join("");
  }
}

async function deleteAnnouncement(id) {
  const res = await apiCall("/api/admin/announcements", "DELETE", { id });
  if (res && res.success) {
    showToast("Broadcast deleted!", "success");
    loadAdminAnnouncements();
  }
}

async function loadAdminDocuments() {
  const data = await apiCall("/api/admin/documents");
  if (!data) return;
  const tbody = document.querySelector("#admin-documents-table tbody");
  if (tbody) {
    tbody.innerHTML = data.map(d => `
      <tr>
        <td><strong>${d.title}</strong></td>
        <td>${d.category}</td>
        <td>${d.file_size}</td>
        <td>${d.uploaded_date}</td>
        <td><button class="btn btn-danger btn-sm" onclick="deleteDocument(${d.id})">Delete</button></td>
      </tr>
    `).join("");
  }
}

async function deleteDocument(id) {
  const res = await apiCall("/api/admin/documents", "DELETE", { id });
  if (res && res.success) {
    showToast("Document deleted!", "success");
    loadAdminDocuments();
  }
}

async function loadAdminPlacements() {
  const data = await apiCall("/api/admin/placements");
  if (!data) return;
  const tbody = document.querySelector("#admin-placements-table tbody");
  if (tbody) {
    tbody.innerHTML = data.map(p => `
      <tr>
        <td><strong>${p.company_name}</strong></td>
        <td>${p.job_role}</td>
        <td>${p.package_lpa} LPA</td>
        <td>${p.location}</td>
        <td>${p.deadline}</td>
        <td><span class="badge badge-good">${p.status}</span></td>
        <td><button class="btn btn-danger btn-sm" onclick="deletePlacement(${p.id})">Delete</button></td>
      </tr>
    `).join("");
  }
}

async function deletePlacement(id) {
  const res = await apiCall("/api/admin/placements", "DELETE", { id });
  if (res && res.success) {
    showToast("Placement drive deleted!", "success");
    loadAdminPlacements();
  }
}

async function loadAdminClinical() {
  const data = await apiCall("/api/admin/clinical");
  if (!data) return;
  const tbody = document.querySelector("#admin-clinical-table tbody");
  if (tbody) {
    tbody.innerHTML = data.map(c => `
      <tr>
        <td><strong>${c.student_name} (${c.student_id})</strong></td>
        <td>${c.date}</td>
        <td>${c.ward_lab}</td>
        <td>${c.assigned_hours} hrs</td>
        <td><span class="badge badge-${c.status.toLowerCase()}">${c.status}</span></td>
        <td><button class="btn btn-danger btn-sm" onclick="deleteClinical(${c.id})">Delete</button></td>
      </tr>
    `).join("");
  }
}

async function deleteClinical(id) {
  const res = await apiCall("/api/admin/clinical", "DELETE", { id });
  if (res && res.success) {
    showToast("Clinical record deleted!", "success");
    loadAdminClinical();
  }
}

async function loadAdminLibrary() {
  const data = await apiCall("/api/admin/library");
  if (!data) return;

  const tbody = document.querySelector("#admin-issued-books-table tbody");
  if (tbody && data.issued_books) {
    tbody.innerHTML = data.issued_books.map(b => `
      <tr>
        <td><strong>${b.title}</strong></td>
        <td>${b.student_name} (${b.student_id})</td>
        <td>${b.issue_date}</td>
        <td>${b.due_date}</td>
        <td><span class="badge badge-${b.status.toLowerCase()}">${b.status}</span></td>
        <td>
          ${b.status !== 'Returned' ? 
            `<button class="btn btn-secondary btn-sm" onclick="returnBook(${b.id})">Process Return</button>` : 
            `<span style="color: var(--accent-green); font-weight: 700;">Returned</span>`}
        </td>
      </tr>
    `).join("");
  }

  const catalogTbody = document.querySelector("#admin-books-catalog-table tbody");
  if (catalogTbody && data.books) {
    if (data.books.length === 0) {
      catalogTbody.innerHTML = `<tr><td colspan="6" style="text-align: center;">No books in catalog.</td></tr>`;
    } else {
      catalogTbody.innerHTML = data.books.map(b => `
        <tr>
          <td><strong>${b.title}</strong></td>
          <td>${b.author}</td>
          <td>${b.isbn || '-'}</td>
          <td>${b.category}</td>
          <td>${b.available_copies} / ${b.total_copies}</td>
          <td>
            <button class="btn btn-danger btn-sm" onclick="deleteBook(${b.id})">Delete</button>
          </td>
        </tr>
      `).join("");
    }
  }
}

async function returnBook(issueId) {
  const res = await apiCall("/api/admin/library", "PUT", { issue_id: issueId });
  if (res && res.success) {
    showToast("Book returned!", "success");
    loadAdminLibrary();
  }
}

async function loadAdminLeave() {
  const data = await apiCall("/api/admin/leave");
  if (!data) return;

  const tbody = document.querySelector("#admin-leave-table tbody");
  if (tbody) {
    tbody.innerHTML = data.map(l => `
      <tr>
        <td><strong>${l.student_name} (${l.student_id})</strong></td>
        <td>${l.from_date} to ${l.to_date}</td>
        <td>${l.reason}</td>
        <td><span class="badge badge-${l.status.toLowerCase()}">${l.status}</span></td>
        <td>
          ${l.status === 'Pending' ? `
            <button class="btn btn-primary btn-sm" onclick="actionLeave(${l.id}, 'Approved')">Approve</button>
            <button class="btn btn-danger btn-sm" onclick="actionLeave(${l.id}, 'Rejected')">Reject</button>
          ` : `<span>Done</span>`}
        </td>
      </tr>
    `).join("");
  }
}

async function actionLeave(leaveId, action) {
  const remarks = prompt(`Admin remarks for ${action.toLowerCase()} leave:`);
  const res = await apiCall("/api/admin/leave/action", "POST", { leave_id: leaveId, action, admin_remarks: remarks || "" });
  if (res && res.success) {
    showToast(`Leave application ${action.toLowerCase()}!`, "success");
    loadAdminLeave();
  }
}

// Admin form submission helpers and profile managers
function loadAdminProfile() {}

async function handleAdminProfileUpdate(e) {
  e.preventDefault();
  const name = document.getElementById("adm-profile-name").value.trim();
  const res = await apiCall("/api/profile", "PUT", { name });
  if (res && res.success) {
    showToast("Profile name updated successfully!", "success");
    document.querySelectorAll(".profile-trigger span").forEach(el => el.textContent = name);
  } else {
    showToast(res.message || "Failed to update profile.", "error");
  }
}

async function handleAdminPasswordChange(e) {
  e.preventDefault();
  const oldPass = document.getElementById("adm-old-pass").value;
  const newPass = document.getElementById("adm-new-pass").value;

  const res = await apiCall("/api/profile/change-password", "POST", {
    old_password: oldPass,
    new_password: newPass
  });
  if (res && res.success) {
    showToast("Password updated successfully!", "success");
    document.getElementById("admin-change-pass-form").reset();
  } else {
    showToast(res.message || "Failed to change password.", "error");
  }
}

async function handleAdminAddAnnouncement(e) {
  e.preventDefault();
  const title = document.getElementById("adm-ann-title").value.trim();
  const category = document.getElementById("adm-ann-cat").value;
  const priority = document.getElementById("adm-ann-prio").value;
  const message = document.getElementById("adm-ann-msg").value.trim();
  
  const res = await apiCall("/api/admin/announcements", "POST", {
    title, category, priority, message
  });
  if (res && res.success) {
    showToast("Announcement broadcasted successfully!", "success");
    closeModal("modal-admin-announcement");
    loadAdminAnnouncements();
    document.getElementById("admin-ann-form").reset();
  } else {
    showToast(res.message || "Failed to post announcement.", "error");
  }
}

async function handleAdminAddAssignment(e) {
  e.preventDefault();
  const subject = document.getElementById("adm-assign-sub").value.trim();
  const title = document.getElementById("adm-assign-title").value.trim();
  const description = document.getElementById("adm-assign-desc").value.trim();
  const dueDate = document.getElementById("adm-assign-due").value;
  const totalMarks = document.getElementById("adm-assign-marks").value;

  const res = await apiCall("/api/admin/assignments", "POST", {
    subject, title, description, due_date: dueDate, total_marks: parseFloat(totalMarks)
  });
  if (res && res.success) {
    showToast("Assignment created successfully!", "success");
    closeModal("modal-admin-assignment");
    loadAdminAssignments();
    document.getElementById("admin-assign-form").reset();
  } else {
    showToast(res.message || "Failed to create assignment.", "error");
  }
}

async function handleAdminAddDocument(e) {
  e.preventDefault();
  const title = document.getElementById("adm-doc-title").value.trim();
  const category = document.getElementById("adm-doc-cat").value;
  const description = document.getElementById("adm-doc-desc").value.trim();
  const fileInput = document.getElementById("adm-doc-file");
  const file = fileInput.files[0];

  if (!file) {
    showToast("Please select a file to upload.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("title", title);
  formData.append("category", category);
  formData.append("description", description);
  formData.append("file", file);

  showToast("Uploading document...", "info");
  try {
    const response = await fetch("/api/admin/documents", {
      method: "POST",
      body: formData
    });
    const res = await response.json();
    if (response.ok && res.success) {
      showToast("Document uploaded successfully!", "success");
      closeModal("modal-admin-document");
      loadAdminDocuments();
      document.getElementById("admin-doc-form").reset();
    } else {
      showToast(res.message || "Failed to upload document.", "error");
    }
  } catch (err) {
    showToast("Network error uploading document.", "error");
  }
}

async function handleAdminAddPlacement(e) {
  e.preventDefault();
  const companyName = document.getElementById("adm-place-comp").value.trim();
  const jobRole = document.getElementById("adm-place-role").value.trim();
  const eligibility = document.getElementById("adm-place-elig").value.trim();
  const packageLpa = document.getElementById("adm-place-pkg").value;
  const location = document.getElementById("adm-place-loc").value.trim();
  const deadline = document.getElementById("adm-place-deadline").value;
  const status = document.getElementById("adm-place-status").value;

  const res = await apiCall("/api/admin/placements", "POST", {
    company_name: companyName,
    job_role: jobRole,
    eligibility_criteria: eligibility,
    package_lpa: parseFloat(packageLpa),
    location,
    deadline: deadline,
    status
  });
  if (res && res.success) {
    showToast("Placement drive created!", "success");
    closeModal("modal-admin-placement");
    loadAdminPlacements();
    document.getElementById("admin-placement-form").reset();
  } else {
    showToast(res.message || "Failed to create placement drive.", "error");
  }
}

async function handleAdminAddBook(e) {
  e.preventDefault();
  const title = document.getElementById("adm-book-title").value.trim();
  const author = document.getElementById("adm-book-author").value.trim();
  const isbn = document.getElementById("adm-book-isbn").value.trim();
  const category = document.getElementById("adm-book-cat").value.trim();
  const copies = document.getElementById("adm-book-copies").value;

  const res = await apiCall("/api/admin/library", "POST", {
    action: "add_book",
    title, author, isbn, category, total_copies: parseInt(copies)
  });
  if (res && res.success) {
    showToast("Book added to catalog successfully!", "success");
    closeModal("modal-admin-book");
    loadAdminLibrary();
    document.getElementById("admin-book-form").reset();
  } else {
    showToast(res.message || "Failed to add book.", "error");
  }
}

async function openIssueBookModal() {
  const select = document.getElementById("adm-issue-book-select");
  if (select) {
    select.innerHTML = '<option value="">Loading books...</option>';
    const data = await apiCall("/api/admin/library");
    if (data && data.books) {
      select.innerHTML = '<option value="">-- Select a Book --</option>' + 
        data.books.map(b => `<option value="${b.id}">${b.title} by ${b.author} (${b.available_copies}/${b.total_copies} available)</option>`).join("");
    } else {
      select.innerHTML = '<option value="">Error loading catalog</option>';
    }
  }
  openModal("modal-issue-book");
}

async function handleAdminIssueBook(e) {
  e.preventDefault();
  const bookId = document.getElementById("adm-issue-book-select").value;
  const studentId = document.getElementById("adm-issue-sid").value.trim();

  if (!bookId) {
    showToast("Please select a book.", "error");
    return;
  }

  const res = await apiCall("/api/admin/library", "POST", {
    action: "issue_book",
    book_id: parseInt(bookId),
    student_id: studentId
  });
  if (res && res.success) {
    showToast("Book issued successfully!", "success");
    closeModal("modal-issue-book");
    loadAdminLibrary();
    document.getElementById("admin-issue-book-form").reset();
  } else {
    showToast(res.message || "Failed to issue book.", "error");
  }
}

async function deleteBook(id) {
  if (!confirm("Are you sure you want to delete this book from the catalog?")) return;
  const res = await apiCall("/api/admin/library", "DELETE", { id: id });
  if (res && res.success) {
    showToast("Book deleted from catalog!", "success");
    loadAdminLibrary();
  }
}

function triggerImportAttendanceFile() {
  document.getElementById("admin-attendance-import-file").click();
}

async function importAttendance(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  const overlay = document.getElementById("loading-overlay");
  const loadingText = document.getElementById("loading-text");
  if (overlay) {
    overlay.style.display = "flex";
    if (loadingText) loadingText.textContent = "Importing cumulative student attendance spreadsheet...";
  }

  try {
    const response = await fetch("/api/admin/attendance/import", {
      method: "POST",
      body: formData
    });
    const res = await response.json();

    if (response.ok && res.success) {
      showToast(res.message || "Attendance imported successfully!", "success");
      const select = document.getElementById("admin-attendance-student-select");
      const sid = select ? select.value : "";
      if (sid) {
        loadAdminAttendanceForStudent(sid);
      }
    } else {
      showToast(res.message || "Error importing attendance.", "error");
    }
  } catch (err) {
    showToast("Network error uploading file.", "error");
  } finally {
    if (overlay) overlay.style.display = "none";
    document.getElementById("admin-attendance-import-file").value = "";
  }
}

function triggerImportResultFile() {
  document.getElementById("admin-result-import-file").click();
}

async function importResults(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  const overlay = document.getElementById("loading-overlay");
  const loadingText = document.getElementById("loading-text");
  if (overlay) {
    overlay.style.display = "flex";
    if (loadingText) loadingText.textContent = "Importing assessment records sheet...";
  }

  try {
    const response = await fetch("/api/admin/assessment/import", {
      method: "POST",
      body: formData
    });
    const res = await response.json();

    if (response.ok && res.success) {
      showToast(res.message || "Results imported successfully!", "success");
      const select = document.getElementById("admin-assessment-student-select");
      const sid = select ? select.value : "";
      if (sid) {
        loadAdminAssessmentForStudent(sid);
      }
    } else {
      showToast(res.message || "Error importing results.", "error");
    }
  } catch (err) {
    showToast("Network error uploading file.", "error");
  } finally {
    if (overlay) overlay.style.display = "none";
    document.getElementById("admin-result-import-file").value = "";
  }
}

let notifDropdownOpen = false;

function toggleNotifDrawer(e) {
  if (e) e.stopPropagation();
  const dropdown = document.getElementById("notif-dropdown");
  if (!dropdown) return;
  
  if (dropdown.style.display === "none") {
    dropdown.style.display = "flex";
    loadNotifications();
    notifDropdownOpen = true;
  } else {
    dropdown.style.display = "none";
    notifDropdownOpen = false;
  }
}

async function loadNotifications() {
  const notifList = document.getElementById("notif-list");
  if (!notifList) return;
  
  notifList.innerHTML = `<div style="text-align: center; padding: 20px; color: var(--text-muted);">Loading...</div>`;
  
  const data = await apiCall("/api/notifications");
  if (!data) {
    notifList.innerHTML = `<div class="notif-empty">Error loading notifications</div>`;
    return;
  }

  // Update badge count
  const unreadCount = data.filter(n => n.is_read === 0).length;
  const notifBadge = document.getElementById("notif-count");
  if (notifBadge) {
    if (unreadCount > 0) {
      notifBadge.textContent = unreadCount;
      notifBadge.style.display = "flex";
    } else {
      notifBadge.style.display = "none";
    }
  }

  if (data.length === 0) {
    notifList.innerHTML = `<div class="notif-empty">No notifications</div>`;
    return;
  }

  notifList.innerHTML = data.map(n => `
    <div class="notif-item ${n.is_read === 0 ? 'unread' : ''}" onclick="markSingleRead(${n.id})">
      <div class="notif-item-title">${n.title}</div>
      <div class="notif-item-message">${n.message}</div>
      <div class="notif-item-time">${n.created_at}</div>
    </div>
  `).join("");
}

async function markSingleRead(id) {
  const res = await apiCall("/api/notifications/read", "POST", { id: id });
  if (res && res.success) {
    loadNotifications();
  }
}

async function markAllNotificationsRead(e) {
  if (e) e.stopPropagation();
  const res = await apiCall("/api/notifications/read-all", "POST");
  if (res && res.success) {
    loadNotifications();
    showToast("All notifications marked as read", "success");
  }
}

async function updateNotificationBadge() {
  const data = await apiCall("/api/notifications");
  if (!data) return;
  const unreadCount = data.filter(n => n.is_read === 0).length;
  const notifBadge = document.getElementById("notif-count");
  if (notifBadge) {
    if (unreadCount > 0) {
      notifBadge.textContent = unreadCount;
      notifBadge.style.display = "flex";
    } else {
      notifBadge.style.display = "none";
    }
  }
}

// Close notifications dropdown on clicking outside
document.addEventListener("click", (e) => {
  const dropdown = document.getElementById("notif-dropdown");
  const toggle = document.getElementById("notif-toggle");
  
  if (dropdown && dropdown.style.display !== "none") {
    // Check if click was outside the dropdown and outside the toggle button
    if (!dropdown.contains(e.target) && (!toggle || !toggle.contains(e.target))) {
      dropdown.style.display = "none";
      notifDropdownOpen = false;
    }
  }
});

function expandImage(url) {
  const modal = document.getElementById("modal-image-viewer");
  const img = document.getElementById("expanded-image");
  if (modal && img) {
    img.src = url;
    openModal("modal-image-viewer");
  }
}

function expandStudentAvatar() {
  const img = document.getElementById("adm-st-avatar-img");
  if (img && img.src) {
    expandImage(img.src);
  }
}


// --------------------------------------------------------------------------
// MODULE 14: RESULTS & MDM ALLOCATION MANAGEMENT (STUDENT & ADMIN)
// --------------------------------------------------------------------------

// 1. Student Results Tab Viewer
async function loadStudentResults() {
  const container = document.getElementById("student-results-container");
  if (!container) return;

  container.innerHTML = `
    <div style="text-align: center; color: var(--text-muted); padding: 40px;">
      <div class="spinner" style="margin: 0 auto 10px auto;"></div>
      Loading your results scorecard...
    </div>
  `;

  const results = await apiCall("/api/results");
  if (!results || results.length === 0) {
    container.innerHTML = `
      <div class="content-card" style="text-align: center; padding: 40px; color: var(--text-muted);">
        <i data-lucide="award" size="48" style="margin: 0 auto 1rem auto; opacity: 0.5; display: block;"></i>
        <h3>No Published Results Found</h3>
        <p style="margin-top: 0.5rem; font-size: 0.9rem;">Your semester grades and results sheets have not been published by the administration yet.</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  container.innerHTML = results.map(r => `
    <div class="content-card" style="margin-bottom: 2rem; border-left: 5px solid ${r.status.toLowerCase() === 'pass' ? 'var(--green-main)' : 'var(--red-main)'}; position: relative;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem; margin-bottom: 1rem;">
        <div>
          <h3 style="font-size: 1.25rem; font-weight: 700; color: var(--text-main);">${r.semester} - ${r.exam_type}</h3>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">Academic Year: ${r.academic_year}</p>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
          <button class="btn btn-secondary btn-sm" onclick="printStudentResultCard(${r.id})" style="display: flex; align-items: center; gap: 6px;">
            <i data-lucide="printer" size="14"></i> Print Card
          </button>
          <span class="badge ${r.status.toLowerCase() === 'pass' ? 'badge-good' : 'badge-critical'}" style="font-size: 0.9rem; padding: 6px 12px;">${r.status}</span>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem; background: var(--bg-body); padding: 1rem; border-radius: var(--radius-md);">
        <div>
          <span style="font-size: 0.8rem; color: var(--text-muted); display: block;">Semester SGPA</span>
          <strong style="font-size: 1.35rem; color: var(--text-main);">${r.sgpa}</strong>
        </div>
        <div>
          <span style="font-size: 0.8rem; color: var(--text-muted); display: block;">Cumulative CGPA</span>
          <strong style="font-size: 1.35rem; color: var(--text-main);">${r.cgpa}</strong>
        </div>
      </div>

      <div class="table-responsive">
        <table class="custom-table">
          <thead>
            <tr>
              <th>Subject Code</th>
              <th>Subject Name</th>
              <th style="text-align: center;">Internal Marks</th>
              <th style="text-align: center;">External Marks</th>
              <th style="text-align: center;">Practical Marks</th>
              <th style="text-align: center;">Total Marks</th>
              <th style="text-align: center;">Grade</th>
            </tr>
          </thead>
          <tbody>
            ${r.subjects.map(s => `
              <tr>
                <td><strong>${s.subject_code}</strong></td>
                <td>${s.subject_name}</td>
                <td style="text-align: center;">${s.internal_marks !== null ? s.internal_marks : '-'}</td>
                <td style="text-align: center;">${s.external_marks !== null ? s.external_marks : '-'}</td>
                <td style="text-align: center;">${s.practical_marks !== null ? s.practical_marks : '-'}</td>
                <td style="text-align: center;"><strong>${s.total_marks !== null ? s.total_marks : '-'}</strong></td>
                <td style="text-align: center;"><span class="badge ${['O','A+','A','B+','B'].includes(s.grade) ? 'badge-good' : (s.grade === 'F' ? 'badge-critical' : 'badge-warning')}" style="padding: 4px 8px;">${s.grade}</span></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </div>
  `).join("");

  // Store globally for printing
  window.studentResultsCache = results;
  lucide.createIcons();
}

function printStudentResultCard(resultId) {
  const result = window.studentResultsCache.find(r => r.id === resultId);
  if (!result) return;

  const printArea = document.getElementById("print-report-card-area");
  if (!printArea) return;

  // Build a formal report card HTML for printing
  printArea.innerHTML = `
    <div style="padding: 12px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: black; background: white; border: 4px double #1e3a8a; border-radius: 12px; max-width: 850px; margin: 0 auto; box-sizing: border-box;">
      <div style="padding: 30px; border: 1px solid #1e3a8a; border-radius: 6px; box-sizing: border-box;">
        <div style="display: flex; align-items: center; gap: 20px; border-bottom: 3px double #1e3a8a; padding-bottom: 15px; margin-bottom: 20px;">
          <img src="/static/uploads/college_logo.jpg?t=${new Date().getTime()}" style="height: 90px; width: 90px; object-fit: contain;" onerror="this.style.display='none';">
          <div style="text-align: center; flex: 1;">
            <h4 style="font-size: 0.75rem; font-weight: 600; margin: 0; color: #555; text-transform: uppercase;">G.K. Gujar Memorial Charitable Trust's</h4>
            <h2 style="font-size: 1.05rem; font-weight: 700; margin: 2px 0; color: #1e3a8a; text-transform: uppercase;">Dr. Ashok Gujar Technical Institute's</h2>
            <h1 style="font-size: 1.2rem; font-weight: 800; margin: 2px 0; color: #1e3a8a; text-transform: uppercase; letter-spacing: 0.5px;">Dr. Daulatrao Aher College of Engineering, Karad</h1>
            <p style="font-size: 0.8rem; font-weight: 700; margin: 2px 0; color: #e11d48; text-transform: uppercase;">Accreditation by NAAC with 'A' Grade</p>
            <p style="font-size: 0.7rem; color: #444; margin: 2px 0; font-weight: 500;">AICTE & DTE approved, Affiliated to Ch. Shivaji University, Kolhapur</p>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px; font-size: 0.95rem; line-height: 1.6;">
          <div>
            <div><strong>Student Name:</strong> ${document.getElementById("prof-name")?.textContent || "Student"}</div>
            <div><strong>Course / Program:</strong> B.Tech Computer Science</div>
          </div>
          <div>
            <div><strong>Semester:</strong> ${result.semester}</div>
            <div><strong>Exam Type:</strong> ${result.exam_type}</div>
            <div><strong>Academic Year:</strong> ${result.academic_year}</div>
          </div>
        </div>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 0.9rem;">
          <thead>
            <tr style="background: #f2f2f2; border-top: 1px solid #333; border-bottom: 1px solid #333;">
              <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Subject Code</th>
              <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Subject Name</th>
              <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Internal</th>
              <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">External</th>
              <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Practical</th>
              <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Total</th>
              <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Grade</th>
            </tr>
          </thead>
          <tbody>
            ${result.subjects.map(s => `
              <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>${s.subject_code}</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">${s.subject_name}</td>
                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">${s.internal_marks !== null ? s.internal_marks : '-'}</td>
                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">${s.external_marks !== null ? s.external_marks : '-'}</td>
                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">${s.practical_marks !== null ? s.practical_marks : '-'}</td>
                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;"><strong>${s.total_marks !== null ? s.total_marks : '-'}</strong></td>
                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;"><strong>${s.grade}</strong></td>
              </tr>
            `).join("")}
          </tbody>
        </table>

        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 20px; border-top: 1px solid #333; padding-top: 15px; font-size: 1rem;">
          <div><strong>SGPA:</strong> ${result.sgpa}</div>
          <div><strong>CGPA:</strong> ${result.cgpa}</div>
          <div><strong>Result Status:</strong> <span style="font-weight: bold; color: ${result.status.toLowerCase() === 'pass' ? '#16a34a' : '#dc2626'}">${result.status}</span></div>
        </div>

        <div style="margin-top: 40px; display: flex; justify-content: space-between; align-items: flex-end; font-size: 0.85rem;">
          <div>
            <div>Date Generated: <strong>${new Date().toLocaleDateString()}</strong></div>
          </div>
          <div style="text-align: center;">
            <img src="/static/uploads/digital_signature.jpg?t=${new Date().getTime()}" style="max-height: 60px; max-width: 180px; display: block; margin: 0 auto 5px auto;" onerror="this.style.display='none';">
            <div style="width: 170px; border-bottom: 1px solid #000; margin: 0 auto 5px auto;"></div>
            <div style="font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">Controller of Examinations</div>
          </div>
        </div>
      </div>
    </div>
  `;

  // Hide page contents, show print card, print and restore
  const originalDisplay = printArea.style.display;
  printArea.style.display = "block";
  window.print();
  printArea.style.display = originalDisplay;
  printArea.innerHTML = "";
}

// 2. Admin Result Management Loader
async function loadAdminResults() {
  const years = await apiCall("/api/years");
  const semesters = await apiCall("/api/semesters");

  if (years) {
    const uploadYearSelect = document.getElementById("results-upload-year");
    const filterYearSelect = document.getElementById("filter-results-year");
    
    if (uploadYearSelect) {
      uploadYearSelect.innerHTML = years.map(y => `<option value="${y.id}">${y.name}</option>`).join("");
    }
    if (filterYearSelect) {
      filterYearSelect.innerHTML = `<option value="">All Years</option>` + years.map(y => `<option value="${y.id}">${y.name}</option>`).join("");
    }
  }

  if (semesters) {
    const uploadSemSelect = document.getElementById("results-upload-semester");
    const filterSemSelect = document.getElementById("filter-results-semester");

    if (uploadSemSelect) {
      uploadSemSelect.innerHTML = semesters.map(s => `<option value="${s.id}">${s.name}</option>`).join("");
    }
    if (filterSemSelect) {
      filterSemSelect.innerHTML = `<option value="">All Semesters</option>` + semesters.map(s => `<option value="${s.id}">${s.name}</option>`).join("");
    }
  }

  queryAdminResults();
}

async function queryAdminResults() {
  const q = document.getElementById("filter-results-search").value;
  const yearId = document.getElementById("filter-results-year").value;
  const semId = document.getElementById("filter-results-semester").value;
  const exam = document.getElementById("filter-results-exam").value;
  const subject = document.getElementById("filter-results-subject").value;

  const url = `/api/admin/results?q=${encodeURIComponent(q)}&academic_year_id=${yearId}&semester_id=${semId}&exam_type=${encodeURIComponent(exam)}&subject_name=${encodeURIComponent(subject)}`;
  const records = await apiCall(url);

  const tbody = document.querySelector("#admin-results-table tbody");
  if (!tbody) return;

  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="13" style="text-align: center; color: var(--text-muted);">No result records matched the current filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = records.map(r => `
    <tr>
      <td><strong>${r.roll_number}</strong></td>
      <td>${r.prn_number}</td>
      <td>${r.name}</td>
      <td>${r.semester}<br><span style="font-size: 0.75rem; color: var(--text-muted);">${r.exam_type}</span></td>
      <td><strong>${r.subject_code}</strong><br><span style="font-size: 0.8rem;">${r.subject_name}</span></td>
      <td style="text-align: center;">${r.internal_marks !== null ? r.internal_marks : '-'}</td>
      <td style="text-align: center;">${r.external_marks !== null ? r.external_marks : '-'}</td>
      <td style="text-align: center;">${r.practical_marks !== null ? r.practical_marks : '-'}</td>
      <td style="text-align: center;"><strong>${r.total_marks !== null ? r.total_marks : '-'}</strong></td>
      <td style="text-align: center;"><span class="badge badge-amber" style="padding: 4px 8px;">${r.grade || 'F'}</span></td>
      <td>SGPA: ${r.sgpa}<br>CGPA: ${r.cgpa}</td>
      <td><span class="badge ${r.status.toLowerCase() === 'pass' ? 'badge-good' : 'badge-critical'}">${r.status}</span></td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="deleteResultRecord(${r.id})" style="padding: 4px 8px; color: var(--red-main); background: none; border: none; cursor: pointer;">
          <i data-lucide="trash-2" size="14"></i>
        </button>
      </td>
    </tr>
  `).join("");

  lucide.createIcons();
}

async function deleteResultRecord(id) {
  if (!confirm("Are you sure you want to delete this result entry? All subject marks linked to this student for this semester exam will be permanently removed.")) return;
  const res = await apiCall(`/api/admin/results/delete/${id}`, "DELETE");
  if (res && res.success) {
    showToast("Result record successfully deleted.", "success");
    queryAdminResults();
  } else {
    showToast(res ? res.message : "Error deleting result record.", "error");
  }
}

function exportResultsToExcel() {
  const q = document.getElementById("filter-results-search").value;
  const yearId = document.getElementById("filter-results-year").value;
  const semId = document.getElementById("filter-results-semester").value;
  const exam = document.getElementById("filter-results-exam").value;
  const subject = document.getElementById("filter-results-subject").value;

  window.location.href = `/api/admin/results/export?q=${encodeURIComponent(q)}&academic_year_id=${yearId}&semester_id=${semId}&exam_type=${encodeURIComponent(exam)}&subject_name=${encodeURIComponent(subject)}`;
}

// 3. Form Upload Handlers
async function handleResultsUpload(e) {
  e.preventDefault();
  const fileInput = document.getElementById("results-upload-file");
  const yearSelect = document.getElementById("results-upload-year");
  const semSelect = document.getElementById("results-upload-semester");
  const examSelect = document.getElementById("results-upload-exam");

  if (!fileInput.files[0]) return;

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("academic_year_id", yearSelect.value);
  formData.append("semester_id", semSelect.value);
  formData.append("exam_type", examSelect.value);

  const overlay = document.getElementById("loading-overlay");
  const loadingText = document.getElementById("loading-text");
  if (overlay) {
    overlay.style.display = "flex";
    if (loadingText) loadingText.textContent = "Processing result Excel sheet, matching subject headers and performing database operations...";
  }

  try {
    const response = await fetch("/api/admin/results/import", {
      method: "POST",
      body: formData
    });
    const res = await response.json();

    if (response.ok && res.success) {
      showToast(res.message || "Results imported successfully!", "success");
      e.target.reset();
      queryAdminResults();
    } else {
      showToast(res.message || "Error importing results.", "error");
    }
  } catch (err) {
    showToast("Network error uploading result file.", "error");
  } finally {
    if (overlay) overlay.style.display = "none";
  }
}

async function handleMdmUpload(e) {
  e.preventDefault();
  const fileInput = document.getElementById("mdm-upload-file");

  if (!fileInput.files[0]) return;

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const overlay = document.getElementById("loading-overlay");
  const loadingText = document.getElementById("loading-text");
  if (overlay) {
    overlay.style.display = "flex";
    if (loadingText) loadingText.textContent = "Uploading MDM PDF / Excel sheet, extracting faculty structures and updating student mentors...";
  }

  try {
    const response = await fetch("/api/admin/mdm/import", {
      method: "POST",
      body: formData
    });
    const res = await response.json();

    if (response.ok && res.success) {
      showToast(res.message || "MDM Faculty Allocations imported successfully!", "success");
      e.target.reset();
    } else {
      showToast(res.message || "Error importing MDM allocation.", "error");
    }
  } catch (err) {
    showToast("Network error uploading MDM allocations.", "error");
  } finally {
    if (overlay) overlay.style.display = "none";
  }
}

async function handleSignatureUpload(e) {
  e.preventDefault();
  const fileInput = document.getElementById("signature-upload-file");
  if (!fileInput.files[0]) return;

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const overlay = document.getElementById("loading-overlay");
  const loadingText = document.getElementById("loading-text");
  if (overlay) {
    overlay.style.display = "flex";
    if (loadingText) loadingText.textContent = "Uploading new digital signature image...";
  }

  try {
    const response = await fetch("/api/admin/signature/upload", {
      method: "POST",
      body: formData
    });
    const res = await response.json();

    if (response.ok && res.success) {
      showToast(res.message || "Digital Signature uploaded successfully!", "success");
      e.target.reset();
      
      // Update preview immediately with a cache-buster timestamp
      const preview = document.getElementById("admin-signature-preview");
      if (preview) {
        preview.src = "/static/uploads/digital_signature.jpg?t=" + new Date().getTime();
      }
    } else {
      showToast(res.message || "Error uploading digital signature.", "error");
    }
  } finally {
    if (overlay) overlay.style.display = "none";
  }
}

// =====================================================================
// HEAD ADMIN MANAGEMENT FUNCTIONS
// =====================================================================
async function loadAdminsList() {
  const tableBody = document.querySelector("#head-admins-table tbody");
  if (!tableBody) return;

  tableBody.innerHTML = `<tr><td colspan="5" style="text-align: center;">Loading administrators...</td></tr>`;

  try {
    const response = await fetch("/api/admin/list");
    if (!response.ok) {
      tableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--accent-rose);">Access Denied or Session Expired.</td></tr>`;
      return;
    }
    const admins = await response.json();

    if (admins.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="5" style="text-align: center;">No administrative users found.</td></tr>`;
      return;
    }

    tableBody.innerHTML = "";
    admins.forEach((adm) => {
      const isSelf = adm.admin_id === document.body.dataset.studentId;
      const isPrimaryHead = adm.admin_id === "HEAD01";
      const deleteButton = (isSelf || isPrimaryHead) 
        ? `<span style="color: var(--text-muted); font-size: 0.85rem; font-style: italic;">Protected</span>`
        : `<button class="btn btn-secondary btn-sm" style="color: var(--accent-rose); border-color: var(--accent-rose); background: transparent;" onclick="deleteAdmin('${adm.admin_id}')">Delete</button>`;

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${adm.admin_id}</strong></td>
        <td>${adm.name}</td>
        <td><span style="padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; background: ${adm.department_code === 'HEAD' ? 'rgba(79, 70, 229, 0.15)' : 'rgba(100, 116, 139, 0.15)'}; color: ${adm.department_code === 'HEAD' ? 'var(--primary)' : 'var(--text-main)'}">${adm.department}</span></td>
        <td>${adm.created_at}</td>
        <td>${deleteButton}</td>
      `;
      tableBody.appendChild(tr);
    });
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--accent-rose);">Error loading administrators.</td></tr>`;
  }
}

async function handleCreateAdmin(e) {
  e.preventDefault();
  const idInput = document.getElementById("new-adm-id");
  const nameInput = document.getElementById("new-adm-name");
  const passInput = document.getElementById("new-adm-password");
  const deptSelect = document.getElementById("new-adm-dept");

  if (!idInput || !nameInput || !passInput || !deptSelect) return;

  const data = {
    admin_id: idInput.value.trim(),
    name: nameInput.value.trim(),
    password: passInput.value,
    department_code: deptSelect.value
  };

  try {
    const response = await fetch("/api/admin/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const res = await response.json();

    if (response.ok && res.success) {
      showToast(res.message || "Admin account created!", "success");
      e.target.reset();
      loadAdminsList();
    } else {
      showToast(res.message || "Failed to create admin.", "error");
    }
  } catch (err) {
    showToast("Network error creating admin.", "error");
  }
}

async function deleteAdmin(adminId) {
  if (!confirm(`Are you sure you want to delete administrator "${adminId}"?`)) return;

  try {
    const response = await fetch("/api/admin/delete", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ admin_id: adminId })
    });
    const res = await response.json();

    if (response.ok && res.success) {
      showToast(res.message || "Admin deleted successfully.", "success");
      loadAdminsList();
    } else {
      showToast(res.message || "Failed to delete admin.", "error");
    }
  } catch (err) {
    showToast("Network error deleting admin.", "error");
  }
}

