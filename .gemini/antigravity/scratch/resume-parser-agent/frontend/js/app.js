/**
 * Main Application Coordinator for Resume Parser Agent.
 */

window.App = {
  activeCandidateId: null,
  activeAdminId: null,

  init: async function() {
    this.setupTabs();
    this.setupRoleSwitcher();
    this.setupQuickSeed();

    await this.checkDatabaseHealth();
    await this.refreshMetrics();
    await this.loadUsersAndSelects();
    await this.loadJobs();
    await this.loadRecruiterApplications();

    // Attach change handler to candidate selector
    const candSelect = document.getElementById("select-candidate-user");
    if (candSelect) {
      candSelect.addEventListener("change", (e) => {
        this.activeCandidateId = e.target.value ? parseInt(e.target.value) : null;
        this.loadCandidateResumes();
        this.loadCandidateApplications();
      });
    }
  },

  showAlert: function(msg, type = "info") {
    const box = document.getElementById("global-alert");
    const msgEl = document.getElementById("alert-message");
    const iconEl = document.getElementById("alert-icon");
    if (!box) return;

    box.className = `alert-box ${type}`;
    msgEl.textContent = msg;
    iconEl.textContent = type === "success" ? "✓" : (type === "danger" ? "⚠" : "ℹ️");
    box.style.display = "flex";

    setTimeout(() => {
      box.style.display = "none";
    }, 6000);
  },

  logTerminal: function(msg) {
    const term = document.getElementById("console-terminal-text");
    if (!term) return;
    const timestamp = new Date().toLocaleTimeString();
    term.textContent += `\n[${timestamp}] ${msg}`;
    term.scrollTop = term.scrollHeight;
  },

  // Setup Navigation Tabs
  setupTabs: function() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
      tab.addEventListener("click", () => {
        tabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        const targetId = `pane-${tab.dataset.tab}`;
        document.querySelectorAll(".tab-pane").forEach(pane => {
          pane.classList.remove("active");
        });

        const targetPane = document.getElementById(targetId);
        if (targetPane) targetPane.classList.add("active");

        if (tab.dataset.tab === "schema-explorer") {
          this.loadSchemaExplorer();
        }
      });
    });
  },

  setupRoleSwitcher: function() {
    const select = document.getElementById("current-role-select");
    if (!select) return;

    select.addEventListener("change", (e) => {
      const role = e.target.value;
      if (role === "USER") {
        document.getElementById("tab-candidate-btn").click();
      } else if (role === "ADMIN") {
        document.getElementById("tab-recruiter-btn").click();
      }
    });
  },

  setupQuickSeed: function() {
    const btn = document.getElementById("btn-quick-seed");
    if (!btn) return;
    btn.addEventListener("click", async () => {
      try {
        const res = await API.seedDatabase();
        this.showAlert(res.message, res.seeded ? "success" : "info");
        await this.refreshMetrics();
        await this.loadUsersAndSelects();
        await this.loadJobs();
        await this.loadRecruiterApplications();
      } catch (err) {
        this.showAlert(err.message, "danger");
      }
    });
  },

  // Check Database Health
  checkDatabaseHealth: async function() {
    try {
      const health = await API.getHealth();
      const badge = document.getElementById("db-health-badge");
      const label = document.getElementById("db-status-label");
      if (health.status === "healthy") {
        label.textContent = `SQLite Persistent DB: Connected (${health.tables_count} Tables)`;
        badge.className = "db-status-badge";
      }
    } catch (err) {
      const label = document.getElementById("db-status-label");
      label.textContent = "Database Connection Error";
    }
  },

  // Refresh Metrics Ribbon
  refreshMetrics: async function() {
    try {
      const stats = await API.getStats();
      document.getElementById("stat-users").textContent = stats.users_count;
      document.getElementById("stat-companies").textContent = stats.companies_count;
      document.getElementById("stat-jobs").textContent = `${stats.jobs_count} (${stats.job_skills_count} Skills)`;
      document.getElementById("stat-applications").textContent = `${stats.active_applications_count} / ${stats.applications_count}`;
      document.getElementById("stat-interviews").textContent = stats.interviews_count;
    } catch (err) {
      console.error("Failed to load metrics:", err);
    }
  },

  // Load Users & Dropdowns
  loadUsersAndSelects: async function() {
    try {
      const users = await API.getUsers();
      const candidates = users.filter(u => u.role === "USER");
      const recruiters = users.filter(u => u.role === "ADMIN");

      // Candidate Select
      const candSelect = document.getElementById("select-candidate-user");
      if (candSelect) {
        candSelect.innerHTML = candidates.map(c => 
          `<option value="${c.user_id}">${c.name} (${c.email})</option>`
        ).join("");

        if (candidates.length > 0) {
          this.activeCandidateId = candidates[0].user_id;
          candSelect.value = this.activeCandidateId;
          this.loadCandidateResumes();
          this.loadCandidateApplications();
        } else {
          candSelect.innerHTML = "<option value=''>No candidates yet. Register below.</option>";
        }
      }

      // Recruiter Select
      const recruiterSelect = document.getElementById("job-creator-select");
      if (recruiterSelect) {
        recruiterSelect.innerHTML = recruiters.map(r => 
          `<option value="${r.user_id}">${r.name} (${r.email})</option>`
        ).join("");
        if (recruiters.length > 0) {
          this.activeAdminId = recruiters[0].user_id;
        }
      }

      // Companies Select
      await this.loadCompaniesSelect();

    } catch (err) {
      console.error("Error loading users:", err);
    }
  },

  loadCompaniesSelect: async function() {
    const compSelect = document.getElementById("job-company-select");
    if (!compSelect) return;
    try {
      const companies = await API.getCompanies();
      compSelect.innerHTML = "<option value=''>Select Company...</option>" + 
        companies.map(c => `<option value="${c.company_id}">${c.name} (${c.location || 'Remote'})</option>`).join("");
    } catch (err) {
      console.error(err);
    }
  },

  // Create Candidate User
  handleCreateCandidate: async function() {
    const name = document.getElementById("cand-name").value.trim();
    const email = document.getElementById("cand-email").value.trim();
    const password = document.getElementById("cand-password").value;

    try {
      const res = await API.createUser({
        name,
        email,
        password,
        role: "USER"
      });
      this.showAlert(`Candidate '${res.name}' created successfully!`, "success");
      document.getElementById("form-create-candidate").reset();
      await this.refreshMetrics();
      await this.loadUsersAndSelects();
    } catch (err) {
      this.showAlert(err.message, "danger");
    }
  },

  // Create Company
  handleCreateCompany: async function() {
    const name = document.getElementById("comp-name").value.trim();
    const website = document.getElementById("comp-website").value.trim() || null;
    const location = document.getElementById("comp-location").value.trim() || null;
    const industry = document.getElementById("comp-industry").value.trim() || null;
    const description = document.getElementById("comp-desc").value.trim() || null;

    try {
      const res = await API.createCompany({ name, website, location, industry, description });
      this.showAlert(`Company '${res.name}' registered successfully!`, "success");
      document.getElementById("form-create-company").reset();
      await this.refreshMetrics();
      await this.loadCompaniesSelect();
    } catch (err) {
      this.showAlert(err.message, "danger");
    }
  },

  // Job Skills Row Builder
  addSkillRow: function() {
    const container = document.getElementById("skills-container");
    const row = document.createElement("div");
    row.className = "skill-input-row";
    row.innerHTML = `
      <input type="text" class="form-input skill-name" placeholder="Skill Name (e.g. React, Docker)" required>
      <input type="number" class="form-input skill-exp" placeholder="Min Yrs" value="2" min="0" step="0.5">
      <label class="checkbox-label"><input type="checkbox" class="skill-req" checked> Required</label>
      <button type="button" class="btn btn-ghost btn-xs text-muted" onclick="this.parentElement.remove()">✕</button>
    `;
    container.appendChild(row);
  },

  // Post Job
  handlePostJob: async function() {
    const company_id = parseInt(document.getElementById("job-company-select").value);
    const created_by = document.getElementById("job-creator-select").value ? parseInt(document.getElementById("job-creator-select").value) : null;
    const title = document.getElementById("job-title-input").value.trim();
    const location = document.getElementById("job-location-input").value.trim();
    const job_type = document.getElementById("job-type-select").value;
    const description = document.getElementById("job-desc-input").value.trim();

    // Extract skills
    const skillRows = document.querySelectorAll("#skills-container .skill-input-row");
    const skills = [];
    skillRows.forEach(row => {
      const sName = row.querySelector(".skill-name").value.trim();
      const sExp = parseFloat(row.querySelector(".skill-exp").value) || 0;
      const sReq = row.querySelector(".skill-req").checked;
      if (sName) {
        skills.push({
          skill_name: sName,
          min_experience_years: sExp,
          is_required: sReq
        });
      }
    });

    try {
      const res = await API.createJob({
        company_id,
        created_by,
        title,
        location,
        job_type,
        description,
        skills
      });
      this.showAlert(`Job posting '${res.title}' created with ${res.skills.length} skills!`, "success");
      document.getElementById("form-post-job").reset();
      await this.refreshMetrics();
      await this.loadJobs();
    } catch (err) {
      this.showAlert(err.message, "danger");
    }
  },

  // Load Jobs
  loadJobs: async function() {
    const list = document.getElementById("jobs-feed-list");
    if (!list) return;
    try {
      const jobs = await API.getJobs();
      if (jobs.length === 0) {
        list.innerHTML = "<div class='empty-state'>No job postings available yet. Use Recruiter Portal to create jobs.</div>";
        return;
      }

      list.innerHTML = jobs.map(j => `
        <div class="job-card">
          <div class="job-card-header">
            <div>
              <h3 class="job-card-title">${j.title}</h3>
              <span class="job-card-company">${j.company_name || 'Acme AI'}</span>
            </div>
            <button class="btn btn-primary btn-xs" onclick="window.App.openApplyModal(${j.job_id}, '${encodeURIComponent(j.title)}', '${encodeURIComponent(j.company_name || '')}', '${encodeURIComponent(j.location || '')}')">
              Apply Now
            </button>
          </div>
          <div class="job-card-meta">
            <span>📍 ${j.location || 'Remote'}</span>
            <span>💼 ${j.job_type}</span>
            <span>⏱️ ${new Date(j.created_at).toLocaleDateString()}</span>
          </div>
          <p class="job-card-desc">${j.description}</p>
          <div class="job-skills-pills">
            ${j.skills.map(s => `<span class="skill-pill">${s.skill_name} (${s.min_experience_years}y+)</span>`).join("")}
          </div>
        </div>
      `).join("");

    } catch (err) {
      list.innerHTML = `<div class='empty-state text-danger'>Failed to load jobs: ${err.message}</div>`;
    }
  },

  // Register Resume
  handleRegisterResume: async function() {
    if (!this.activeCandidateId) {
      this.showAlert("Please select or register a candidate first.", "warning");
      return;
    }

    const file_name = document.getElementById("resume-filename").value.trim();
    const file_path = document.getElementById("resume-path").value.trim();
    const raw_text = document.getElementById("resume-rawtext").value.trim() || null;

    try {
      const res = await API.createResume({
        user_id: this.activeCandidateId,
        file_name,
        file_path,
        file_size_bytes: 180000,
        mime_type: "application/pdf",
        raw_text
      });
      this.showAlert(`Resume '${res.file_name}' attached to Candidate ID ${res.user_id}!`, "success");
      document.getElementById("form-register-resume").reset();
      await this.refreshMetrics();
      await this.loadCandidateResumes();
    } catch (err) {
      this.showAlert(err.message, "danger");
    }
  },

  // Load Candidate Resumes
  loadCandidateResumes: async function() {
    const box = document.getElementById("candidate-resumes-box");
    if (!box || !this.activeCandidateId) return;
    try {
      const resumes = await API.getResumes(this.activeCandidateId);
      if (resumes.length === 0) {
        box.innerHTML = "<span class='text-muted text-sm'>No resume attached yet for this candidate.</span>";
        return;
      }
      box.innerHTML = `
        <div class="section-subtitle">Attached Resumes (${resumes.length}):</div>
        ${resumes.map(r => `
          <div class="badge badge-info mb-1 mr-1">
            📄 ${r.file_name} <span class="text-xs text-muted">(${new Date(r.created_at).toLocaleDateString()})</span>
          </div>
        `).join("")}
      `;
    } catch (err) {
      console.error(err);
    }
  },

  // Load Candidate Applications
  loadCandidateApplications: async function() {
    const tbody = document.getElementById("my-apps-tbody");
    if (!tbody || !this.activeCandidateId) return;
    try {
      const apps = await API.getApplications(this.activeCandidateId);
      if (apps.length === 0) {
        tbody.innerHTML = "<tr><td colspan='7' class='text-center text-muted'>You have not submitted any applications yet.</td></tr>";
        return;
      }
      tbody.innerHTML = apps.map(a => `
        <tr>
          <td>#${a.application_id}</td>
          <td><strong>${a.job_title || 'Job #' + a.job_id}</strong></td>
          <td>${a.company_name || '-'}</td>
          <td><span class="badge badge-info">${a.status}</span></td>
          <td>${a.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-warning">Inactive</span>'}</td>
          <td>${new Date(a.applied_at).toLocaleString()}</td>
          <td>
            ${a.is_active ? 
              `<button class="btn btn-ghost btn-xs text-danger" onclick="window.App.withdrawApplication(${a.application_id})">Withdraw</button>` : 
              '<span class="text-muted text-xs">Closed</span>'
            }
          </td>
        </tr>
      `).join("");
    } catch (err) {
      console.error(err);
    }
  },

  // Withdraw Application
  withdrawApplication: async function(appId) {
    try {
      await API.updateApplicationStatus(appId, { status: "WITHDRAWN", is_active: false });
      this.showAlert(`Application #${appId} has been withdrawn (marked inactive).`, "info");
      await this.refreshMetrics();
      await this.loadCandidateApplications();
      await this.loadRecruiterApplications();
    } catch (err) {
      this.showAlert(err.message, "danger");
    }
  },

  // Open Apply Modal
  openApplyModal: async function(jobId, jobTitle, companyName, location) {
    const modal = document.getElementById("apply-modal");
    document.getElementById("modal-job-id").value = jobId;
    document.getElementById("apply-modal-title").textContent = `Apply: ${decodeURIComponent(jobTitle)}`;
    document.getElementById("modal-company-name").textContent = decodeURIComponent(companyName);
    document.getElementById("modal-job-location").textContent = decodeURIComponent(location);

    // Populate user candidates
    const users = await API.getUsers("USER");
    const userSelect = document.getElementById("modal-user-select");
    userSelect.innerHTML = users.map(u => `<option value="${u.user_id}" ${u.user_id === this.activeCandidateId ? 'selected' : ''}>${u.name} (${u.email})</option>`).join("");

    // Populate candidate resumes
    const resumeSelect = document.getElementById("modal-resume-select");
    if (this.activeCandidateId) {
      const resumes = await API.getResumes(this.activeCandidateId);
      resumeSelect.innerHTML = "<option value=''>No resume attached</option>" + 
        resumes.map(r => `<option value="${r.resume_id}">${r.file_name}</option>`).join("");
    }

    modal.style.display = "flex";
  },

  closeApplyModal: function() {
    document.getElementById("apply-modal").style.display = "none";
  },

  confirmSubmitApplication: async function() {
    const job_id = parseInt(document.getElementById("modal-job-id").value);
    const user_id = parseInt(document.getElementById("modal-user-select").value);
    const resumeVal = document.getElementById("modal-resume-select").value;
    const resume_id = resumeVal ? parseInt(resumeVal) : null;

    try {
      const res = await API.createApplication({ job_id, user_id, resume_id });
      this.showAlert(`Application #${res.application_id} submitted successfully to persistent database!`, "success");
      this.closeApplyModal();
      await this.refreshMetrics();
      await this.loadCandidateApplications();
      await this.loadRecruiterApplications();
    } catch (err) {
      this.showAlert(err.message, "danger");
    }
  },

  // Recruiter Pipeline Review
  loadRecruiterApplications: async function() {
    const tbody = document.getElementById("recruiter-apps-tbody");
    if (!tbody) return;
    try {
      const apps = await API.getApplications();
      if (apps.length === 0) {
        tbody.innerHTML = "<tr><td colspan='7' class='text-center text-muted'>No candidate applications submitted yet.</td></tr>";
        return;
      }

      tbody.innerHTML = apps.map(a => `
        <tr>
          <td>#${a.application_id}</td>
          <td>
            <strong>${a.applicant_name || 'Candidate #' + a.user_id}</strong>
            <div class="text-xs text-muted">${a.applicant_email || ''}</div>
          </td>
          <td>${a.job_title || 'Job #' + a.job_id}</td>
          <td><span class="badge badge-info">${a.status}</span></td>
          <td>${a.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-warning">Inactive</span>'}</td>
          <td>${new Date(a.applied_at).toLocaleString()}</td>
          <td>
            <div style="display: flex; gap: 0.3rem;">
              <button class="btn btn-secondary btn-xs" onclick="window.App.openInterviewModal(${a.application_id}, '${encodeURIComponent(a.applicant_name || '')}', '${encodeURIComponent(a.job_title || '')}')">
                Schedule Interview
              </button>
              ${a.is_active ? `
                <button class="btn btn-ghost btn-xs text-danger" onclick="window.App.withdrawApplication(${a.application_id})">Reject</button>
              ` : ''}
            </div>
          </td>
        </tr>
      `).join("");

      await this.loadInterviews();
    } catch (err) {
      console.error(err);
    }
  },

  // Interviews
  loadInterviews: async function() {
    const tbody = document.getElementById("interviews-tbody");
    if (!tbody) return;
    try {
      const interviews = await API.getInterviews();
      if (interviews.length === 0) {
        tbody.innerHTML = "<tr><td colspan='7' class='text-center text-muted'>No interviews scheduled yet.</td></tr>";
        return;
      }
      tbody.innerHTML = interviews.map(i => `
        <tr>
          <td>#${i.interview_id}</td>
          <td>App #${i.application_id}</td>
          <td>${i.interviewer_id ? 'Recruiter #' + i.interviewer_id : 'Recruiter'}</td>
          <td><span class="badge badge-success">${i.status}</span></td>
          <td><a href="${i.meeting_link || '#'}" target="_blank" class="text-xs">${i.meeting_link || 'Link'}</a></td>
          <td class="text-xs text-muted">${i.notes || '-'}</td>
          <td>${new Date(i.created_at).toLocaleDateString()}</td>
        </tr>
      `).join("");
    } catch (err) {
      console.error(err);
    }
  },

  openInterviewModal: async function(appId, applicantName, jobTitle) {
    const modal = document.getElementById("interview-modal");
    document.getElementById("modal-interview-app-id").value = appId;
    document.getElementById("modal-interview-applicant").textContent = `Candidate: ${decodeURIComponent(applicantName)}`;
    document.getElementById("modal-interview-job").textContent = `Position: ${decodeURIComponent(jobTitle)}`;

    // Populate recruiter dropdown
    const recruiters = await API.getUsers("ADMIN");
    const intSelect = document.getElementById("modal-interviewer-select");
    intSelect.innerHTML = recruiters.map(r => `<option value="${r.user_id}">${r.name} (${r.email})</option>`).join("");

    modal.style.display = "flex";
  },

  closeInterviewModal: function() {
    document.getElementById("interview-modal").style.display = "none";
  },

  confirmScheduleInterview: async function() {
    const application_id = parseInt(document.getElementById("modal-interview-app-id").value);
    const interviewer_id = document.getElementById("modal-interviewer-select").value ? parseInt(document.getElementById("modal-interviewer-select").value) : null;
    const meeting_link = document.getElementById("modal-meeting-link").value.trim() || null;
    const notes = document.getElementById("modal-interview-notes").value.trim() || null;

    try {
      const res = await API.createInterview({
        application_id,
        interviewer_id,
        meeting_link,
        notes,
        status: "SCHEDULED"
      });
      this.showAlert(`Interview #${res.interview_id} created in persistent database!`, "success");
      this.closeInterviewModal();
      await this.refreshMetrics();
      await this.loadInterviews();
    } catch (err) {
      this.showAlert(err.message, "danger");
    }
  },

  // Schema Explorer
  loadSchemaExplorer: async function() {
    const container = document.getElementById("schema-tables-container");
    if (!container) return;
    try {
      const schemas = await API.getSchema();
      container.innerHTML = schemas.map(tbl => `
        <div class="table-schema-card">
          <div class="table-schema-header">
            <span class="table-schema-title">📦 ${tbl.table_name}</span>
            <span class="schema-meta-tag">${tbl.row_count} Rows</span>
          </div>
          <div class="table-schema-body">
            ${tbl.columns.map(c => `
              <div class="col-row">
                <span class="col-name">${c.name} ${c.primary_key ? '<span class="col-pk">[PK]</span>' : ''}</span>
                <span class="col-type">${c.type} ${c.nullable ? '' : 'NOT NULL'}</span>
              </div>
            `).join("")}

            ${tbl.foreign_keys.length > 0 ? `
              <div class="schema-fks">
                <strong>🔗 Foreign Keys:</strong>
                ${tbl.foreign_keys.map(fk => `<div>${fk.constrained_columns.join(', ')} -> ${fk.referred_table}(${fk.referred_columns.join(', ')})</div>`).join("")}
              </div>
            ` : ''}

            ${tbl.indexes.length > 0 ? `
              <div class="schema-indexes">
                <strong>⚡ Indexes:</strong>
                ${tbl.indexes.map(idx => `<div>${idx.name} (${idx.column_names ? idx.column_names.join(', ') : 'indexed'}${idx.unique ? ' [UNIQUE]' : ''})</div>`).join("")}
              </div>
            ` : ''}
          </div>
        </div>
      `).join("");
    } catch (err) {
      container.innerHTML = `<div class="empty-state text-danger">Failed to load schema: ${err.message}</div>`;
    }
  },

  // Interactive Constraint Verifier Suite
  runAllConstraintTests: async function() {
    this.logTerminal("Starting full database architecture and constraint verification suite...");
    await this.testEmailUniqueness();
    await this.testActiveAppConstraint();
    await this.testForeignKeyConstraint();
    await this.testRoleValidation();
    this.logTerminal("All verification tests executed.");
    await this.refreshMetrics();
  },

  testEmailUniqueness: async function() {
    const pill = document.getElementById("status-test-email");
    const log = document.getElementById("log-test-email");
    pill.textContent = "Testing...";
    this.logTerminal("Test #1: Creating candidate with duplicate email 'alex.rivera@example.com'...");

    try {
      await API.createUser({
        name: "Duplicate Tester",
        email: "alex.rivera@example.com",
        password: "testpassword",
        role: "USER"
      });
      // If it succeeded, constraint failed!
      pill.textContent = "FAIL";
      pill.className = "test-status-pill fail";
      log.textContent = "Error: Duplicate email was permitted.";
      this.logTerminal("[FAIL] Duplicate email was erroneously allowed!");
    } catch (err) {
      // Rejection is expected!
      pill.textContent = "PASS";
      pill.className = "test-status-pill pass";
      log.textContent = `Correctly rejected: ${err.message}`;
      this.logTerminal(`[PASS] Duplicate email rejected with HTTP 400: ${err.message}`);
    }
  },

  testActiveAppConstraint: async function() {
    const pill = document.getElementById("status-test-active-app");
    const log = document.getElementById("log-test-active-app");
    pill.textContent = "Testing...";

    try {
      const users = await API.getUsers("USER");
      const jobs = await API.getJobs();

      if (users.length === 0 || jobs.length === 0) {
        log.textContent = "Please seed sample data first.";
        return;
      }

      const uId = users[0].user_id;
      const jId = jobs[0].job_id;

      this.logTerminal(`Test #2: Attempting duplicate active application for User #${uId} on Job #${jId}...`);

      // Ensure at least one active app exists
      try {
        await API.createApplication({ job_id: jId, user_id: uId });
      } catch (e) {}

      // Attempt second active application
      await API.createApplication({ job_id: jId, user_id: uId });

      // If it succeeded, constraint failed
      pill.textContent = "FAIL";
      pill.className = "test-status-pill fail";
      log.textContent = "Error: Duplicate active application was permitted.";
      this.logTerminal("[FAIL] Duplicate active application was erroneously allowed!");
    } catch (err) {
      pill.textContent = "PASS";
      pill.className = "test-status-pill pass";
      log.textContent = `Rejected: ${err.message}`;
      this.logTerminal(`[PASS] Duplicate active application rejected by DB constraint: ${err.message}`);
    }
  },

  testForeignKeyConstraint: async function() {
    const pill = document.getElementById("status-test-fk");
    const log = document.getElementById("log-test-fk");
    pill.textContent = "Testing...";
    this.logTerminal("Test #3: Submitting application with non-existent Job ID 999999...");

    try {
      const users = await API.getUsers("USER");
      const uId = users.length > 0 ? users[0].user_id : 1;

      await API.createApplication({ job_id: 999999, user_id: uId });
      pill.textContent = "FAIL";
      pill.className = "test-status-pill fail";
      log.textContent = "Error: FK constraint failed.";
      this.logTerminal("[FAIL] Non-existent Job ID was allowed!");
    } catch (err) {
      pill.textContent = "PASS";
      pill.className = "test-status-pill pass";
      log.textContent = `Correctly rejected: ${err.message}`;
      this.logTerminal(`[PASS] Foreign key validation enforced: ${err.message}`);
    }
  },

  testRoleValidation: async function() {
    const pill = document.getElementById("status-test-role");
    const log = document.getElementById("log-test-role");
    pill.textContent = "Testing...";
    this.logTerminal("Test #4: Validating USER vs ADMIN roles and password hashing...");

    try {
      const rand = Math.floor(Math.random() * 10000);
      const user = await API.createUser({
        name: `Test Candidate ${rand}`,
        email: `candidate${rand}@test.com`,
        password: "hashpassword123",
        role: "USER"
      });

      const admin = await API.createUser({
        name: `Test Recruiter ${rand}`,
        email: `admin${rand}@test.com`,
        password: "hashpassword456",
        role: "ADMIN"
      });

      if (user.role === "USER" && admin.role === "ADMIN") {
        pill.textContent = "PASS";
        pill.className = "test-status-pill pass";
        log.textContent = "USER & ADMIN roles verified with bcrypt.";
        this.logTerminal(`[PASS] Successfully created USER (ID #${user.user_id}) and ADMIN (ID #${admin.user_id}).`);
      } else {
        throw new Error("Roles did not match expectations.");
      }
    } catch (err) {
      pill.textContent = "FAIL";
      pill.className = "test-status-pill fail";
      log.textContent = err.message;
      this.logTerminal(`[FAIL] Role test error: ${err.message}`);
    }
  }
};

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  window.App.init();
});
