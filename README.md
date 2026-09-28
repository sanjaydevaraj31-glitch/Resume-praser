# Resume Parser Agent (Stage 1 Foundation)

An AI-ready recruitment assistant web application designed to intake candidate resumes (PDF / DOCX) and Job Descriptions, extract structured candidate data with evidence citations, and compute evidence-backed fit reports.

---

## 🎯 Stage 1 Objectives Completed
- [x] **Modern Responsive Web Application**: Decoupled HTML5, CSS3, and ES6 JavaScript frontend.
- [x] **Branded Dashboard**: Titled **"Resume Parser Agent"** with status pill and hero introduction.
- [x] **Resume Upload Dropzone**: Drag-and-drop & file picker supporting `.pdf` and `.docx` with validation and file preview info card.
- [x] **Job Description Input Area**: Textarea with character & word counter and sample JD pre-fill helper.
- [x] **Interactive Action Controls**: "Analyze Resume" button with loading spinners and input validation.
- [x] **6 Required Placeholder Sections**:
  1. **Candidate Profile** (Avatar, name, title, contact pills, overview)
  2. **Extracted Resume Data** (Subtabs for Work Experience, Education, Skills & Tools, Certifications)
  3. **Evidence** (Verbatim citation cards, confidence metrics, and source links)
  4. **Job Match** (Requirement matching criteria table with status indicators)
  5. **Fit Score** (Composite score dial with categorical breakdown progress indicators)
  6. **Final Report** (Executive summary, strengths, risk flags, and interview recommendations)
- [x] **Zero Mock/Fake Candidate Results**: Pure schema placeholders and empty state guides without hallucinated data.
- [x] **Modular Backend Architecture**: Python FastAPI structure with typed Pydantic models and service stubs ready for Stage 2 parsing integration.

---

## 📁 Project Structure

```
resume-parser-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry point with static asset mounting
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py            # Endpoints: GET /api/health, POST /api/analyze
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py           # Pydantic schemas (CandidateProfile, Match, FitReport, etc.)
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── parser_service.py    # Document validation & extraction stubs
│   │       ├── matcher_service.py   # Job description matcher stubs
│   │       └── report_service.py    # Fit report generation stubs
│   ├── requirements.txt             # Backend dependencies (fastapi, uvicorn, pydantic)
│   └── run.py                       # Server runner with fallback support
├── frontend/
│   ├── index.html                   # Responsive landing & dashboard
│   ├── css/
│   │   ├── main.css                 # Base theme variables, layout grid, typography
│   │   ├── components.css           # Dropzone, buttons, badges, placeholder cards
│   │   └── responsive.css           # Mobile and tablet media queries
│   └── js/
│       ├── app.js                   # Application coordinator
│       ├── upload.js                # Drag & drop and file handling
│       ├── ui.js                    # UI state transitions, counters, and tabs
│       └── api.js                   # API client interface
└── README.md
```

---

## 🚀 Running the Application

### Option 1: Full Backend & Frontend (FastAPI)
1. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. Start the FastAPI development server:
   ```bash
   python run.py
   ```
3. Open `http://127.0.0.1:8000` in your web browser.

### Option 2: Lightweight Frontend Preview
You can also launch a standard Python HTTP server directly from the `frontend` folder:
```bash
cd frontend
python -m http.server 8000
```
Then open `http://127.0.0.1:8000` in any browser.
