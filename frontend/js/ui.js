/**
 * UI controller module for Resume Parser Agent.
 * Handles subtab switching, counters, sample data loading,
 * alert banners, and interactive state management.
 */

export class UIManager {
  constructor() {
    this.jdTextarea = document.getElementById('jd-textarea');
    this.charCountEl = document.getElementById('char-count');
    this.wordCountEl = document.getElementById('word-count');
    this.btnLoadSample = document.getElementById('btn-load-sample-jd');
    this.btnClearJd = document.getElementById('btn-clear-jd');
    this.btnAnalyze = document.getElementById('btn-analyze');
    this.alertBanner = document.getElementById('alert-banner');
    this.alertMessage = document.getElementById('alert-message');
    this.alertIcon = document.getElementById('alert-icon');

    this.sampleJobDescription = `Senior Full-Stack AI Engineer

Role Overview:
We are looking for an experienced Senior Full-Stack AI Engineer to design and scale intelligent enterprise web applications. You will work closely with product managers and ML researchers to integrate LLM pipelines, build responsive web interfaces, and develop high-throughput backend APIs.

Key Responsibilities:
- Architect and develop scalable RESTful and GraphQL APIs using Python (FastAPI, Flask) or Node.js.
- Build clean, modern, and accessible frontend interfaces with modern JavaScript frameworks (React, Vue, or TypeScript).
- Design and implement AI agent workflows, prompt chaining, and vector database embeddings (PostgreSQL pgvector, Pinecone, FAISS).
- Implement automated document extraction, text parsing (PDF/DOCX), and evidence-based matching algorithms.
- Establish robust CI/CD pipelines, containerization (Docker, Kubernetes), and cloud deployments on AWS or GCP.

Requirements & Qualifications:
- 5+ years of software engineering experience in full-stack web development.
- Strong proficiency in Python, modern JavaScript/TypeScript, and relational/NoSQL databases.
- Practical experience with LLM integration, RAG (Retrieval-Augmented Generation), and LangChain / LlamaIndex.
- Solid understanding of data structures, distributed systems, and API design.
- B.S. or M.S. in Computer Science, Software Engineering, or equivalent practical experience.`;

    this.init();
  }

  init() {
    // Textarea counters
    if (this.jdTextarea) {
      this.jdTextarea.addEventListener('input', () => this.updateCounters());
      this.updateCounters();
    }

    // Sample JD loader
    if (this.btnLoadSample) {
      this.btnLoadSample.addEventListener('click', () => {
        if (this.jdTextarea) {
          this.jdTextarea.value = this.sampleJobDescription;
          this.updateCounters();
          this.showAlert('Sample Job Description loaded successfully.', 'info');
        }
      });
    }

    // Clear JD button
    if (this.btnClearJd) {
      this.btnClearJd.addEventListener('click', () => {
        if (this.jdTextarea) {
          this.jdTextarea.value = '';
          this.updateCounters();
        }
      });
    }

    // Extracted Data subtabs
    this.initSubtabs();
  }

  initSubtabs() {
    const tabButtons = document.querySelectorAll('.subtab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabButtons.forEach((button) => {
      button.addEventListener('click', () => {
        const targetTab = button.getAttribute('data-tab');

        tabButtons.forEach((b) => b.classList.remove('active'));
        tabPanes.forEach((p) => p.classList.remove('active'));

        button.classList.add('active');
        const activePane = document.getElementById(`tab-${targetTab}`);
        if (activePane) {
          activePane.classList.add('active');
        }
      });
    });
  }

  updateCounters() {
    if (!this.jdTextarea) return;
    const text = this.jdTextarea.value;
    const charCount = text.length;
    const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

    if (this.charCountEl) this.charCountEl.textContent = `${charCount} characters`;
    if (this.wordCountEl) this.wordCountEl.textContent = `${wordCount} words`;
  }

  setAnalyzeLoading(isLoading) {
    if (!this.btnAnalyze) return;
    if (isLoading) {
      this.btnAnalyze.classList.add('loading');
      this.btnAnalyze.disabled = true;
      const textSpan = this.btnAnalyze.querySelector('.btn-text');
      if (textSpan) textSpan.textContent = 'Validating & Preparing...';
    } else {
      this.btnAnalyze.classList.remove('loading');
      this.btnAnalyze.disabled = false;
      const textSpan = this.btnAnalyze.querySelector('.btn-text');
      if (textSpan) textSpan.textContent = 'Analyze Resume';
    }
  }

  showAlert(message, type = 'info') {
    if (!this.alertBanner || !this.alertMessage) return;

    this.alertBanner.className = `alert-banner active alert-${type}`;
    this.alertMessage.textContent = message;

    // Auto dismiss after 6 seconds
    if (this.alertTimeout) clearTimeout(this.alertTimeout);
    this.alertTimeout = setTimeout(() => {
      this.hideAlert();
    }, 6000);
  }

  hideAlert() {
    if (this.alertBanner) {
      this.alertBanner.classList.remove('active');
    }
  }

  getJobDescription() {
    return this.jdTextarea ? this.jdTextarea.value.trim() : '';
  }
}
