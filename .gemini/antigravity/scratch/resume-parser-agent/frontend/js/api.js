/**
 * API client library for Resume Parser Agent.
 */

const API_BASE = "/api";

window.API = {
  // Database Health & Schema
  getHealth: async () => {
    const res = await fetch(`${API_BASE}/database/health`);
    return await res.json();
  },

  getSchema: async () => {
    const res = await fetch(`${API_BASE}/database/schema`);
    return await res.json();
  },

  getStats: async () => {
    const res = await fetch(`${API_BASE}/database/stats`);
    return await res.json();
  },

  seedDatabase: async () => {
    const res = await fetch(`${API_BASE}/database/seed`, { method: "POST" });
    return await res.json();
  },

  // Users
  getUsers: async (role = null) => {
    const url = role ? `${API_BASE}/users?role=${role}` : `${API_BASE}/users`;
    const res = await fetch(url);
    return await res.json();
  },

  createUser: async (userData) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create user");
    }
    return await res.json();
  },

  // Companies
  getCompanies: async () => {
    const res = await fetch(`${API_BASE}/companies`);
    return await res.json();
  },

  createCompany: async (companyData) => {
    const res = await fetch(`${API_BASE}/companies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(companyData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create company");
    }
    return await res.json();
  },

  // Jobs
  getJobs: async (companyId = null) => {
    const url = companyId ? `${API_BASE}/jobs?company_id=${companyId}` : `${API_BASE}/jobs`;
    const res = await fetch(url);
    return await res.json();
  },

  createJob: async (jobData) => {
    const res = await fetch(`${API_BASE}/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(jobData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create job");
    }
    return await res.json();
  },

  // Resumes
  getResumes: async (userId = null) => {
    const url = userId ? `${API_BASE}/resumes?user_id=${userId}` : `${API_BASE}/resumes`;
    const res = await fetch(url);
    return await res.json();
  },

  createResume: async (resumeData) => {
    const res = await fetch(`${API_BASE}/resumes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(resumeData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to attach resume");
    }
    return await res.json();
  },

  // Applications
  getApplications: async (userId = null, jobId = null) => {
    let url = `${API_BASE}/applications`;
    const params = [];
    if (userId) params.push(`user_id=${userId}`);
    if (jobId) params.push(`job_id=${jobId}`);
    if (params.length > 0) url += `?${params.join("&")}`;

    const res = await fetch(url);
    return await res.json();
  },

  createApplication: async (appData) => {
    const res = await fetch(`${API_BASE}/applications`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(appData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to submit application");
    }
    return await res.json();
  },

  updateApplicationStatus: async (applicationId, statusData) => {
    const res = await fetch(`${API_BASE}/applications/${applicationId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(statusData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to update application status");
    }
    return await res.json();
  },

  // Interviews
  getInterviews: async () => {
    const res = await fetch(`${API_BASE}/interviews`);
    return await res.json();
  },

  createInterview: async (interviewData) => {
    const res = await fetch(`${API_BASE}/interviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(interviewData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create interview");
    }
    return await res.json();
  }
};
