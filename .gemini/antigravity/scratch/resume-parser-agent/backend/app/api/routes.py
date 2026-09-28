"""
API routes for Resume Parser Agent.
Exposes database health, schema inspection, authentication, companies, jobs, applications, resumes, and interviews.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text, inspect
from sqlite3 import IntegrityError as SQLiteIntegrityError
from sqlalchemy.exc import IntegrityError

from ..database import get_db, engine, DB_FILE
from ..models import User, UserRole, Company, Job, JobSkill, Resume, Application, Interview
from ..schemas.schemas import (
    UserCreate, UserLogin, UserResponse,
    CompanyCreate, CompanyResponse,
    JobCreate, JobResponse, JobSkillResponse,
    ResumeCreate, ResumeResponse,
    ApplicationCreate, ApplicationResponse, ApplicationStatusUpdate,
    InterviewCreate, InterviewResponse,
    DatabaseHealthResponse, DatabaseStatsResponse, TableSchemaInfo, ColumnSchemaInfo
)
from ..core.security import hash_password, verify_password

router = APIRouter(prefix="/api", tags=["Resume Parser Agent API"])


# ==============================================================================
# Database Health & Schema Inspection
# ==============================================================================

@router.get("/database/health", response_model=DatabaseHealthResponse)
def get_database_health(db: Session = Depends(get_db)):
    """Verify database connection and foreign key pragma status."""
    try:
        # Check connection
        db.execute(text("SELECT 1")).scalar()
        
        # Check SQLite foreign keys pragma
        fk_status = False
        if str(engine.url).startswith("sqlite"):
            fk_res = db.execute(text("PRAGMA foreign_keys")).scalar()
            fk_status = bool(fk_res)
        else:
            fk_status = True

        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        return DatabaseHealthResponse(
            status="healthy",
            engine="SQLite (Persistent File)",
            database_file=str(DB_FILE),
            tables_count=len(table_names),
            tables=table_names,
            foreign_keys_enabled=fk_status
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database health check failed: {str(e)}"
        )


@router.get("/database/schema", response_model=List[TableSchemaInfo])
def get_database_schema(db: Session = Depends(get_db)):
    """Introspect all tables, column types, foreign keys, indexes, and row counts."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    results = []

    model_mapping = {
        "users": User,
        "companies": Company,
        "jobs": Job,
        "job_skills": JobSkill,
        "resumes": Resume,
        "applications": Application,
        "interviews": Interview
    }

    for table in table_names:
        cols_info = []
        for col in inspector.get_columns(table):
            cols_info.append(ColumnSchemaInfo(
                name=col["name"],
                type=str(col["type"]),
                nullable=bool(col.get("nullable", True)),
                primary_key=bool(col.get("primary_key", False)),
                default=str(col.get("default")) if col.get("default") is not None else None
            ))

        fks = []
        for fk in inspector.get_foreign_keys(table):
            fks.append({
                "constrained_columns": fk.get("constrained_columns", []),
                "referred_table": fk.get("referred_table", ""),
                "referred_columns": fk.get("referred_columns", [])
            })

        indexes = []
        for idx in inspector.get_indexes(table):
            indexes.append({
                "name": idx.get("name"),
                "column_names": idx.get("column_names", []),
                "unique": idx.get("unique", False)
            })

        # Calculate row count
        count = 0
        if table in model_mapping:
            count = db.query(model_mapping[table]).count()
        else:
            count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0

        results.append(TableSchemaInfo(
            table_name=table,
            columns=cols_info,
            foreign_keys=fks,
            indexes=indexes,
            row_count=count
        ))

    return results


@router.get("/database/stats", response_model=DatabaseStatsResponse)
def get_database_stats(db: Session = Depends(get_db)):
    """Get live record counts across all primary entities."""
    return DatabaseStatsResponse(
        users_count=db.query(User).count(),
        companies_count=db.query(Company).count(),
        jobs_count=db.query(Job).count(),
        job_skills_count=db.query(JobSkill).count(),
        applications_count=db.query(Application).count(),
        active_applications_count=db.query(Application).filter(Application.is_active == True).count(),
        resumes_count=db.query(Resume).count(),
        interviews_count=db.query(Interview).count()
    )


# ==============================================================================
# Authentication & Users
# ==============================================================================

@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (USER / CANDIDATE or ADMIN / RECRUITER)."""
    # Check if email is already registered
    existing = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{payload.email}' is already registered."
        )

    try:
        user_role = UserRole(payload.role.value)
    except Exception:
        user_role = UserRole.USER

    hashed_pw = hash_password(payload.password)

    new_user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        password_hash=hashed_pw,
        role=user_role
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity constraint violation: user email must be unique."
        )


@router.post("/auth/login")
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return profile data."""
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    return {
        "status": "authenticated",
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role)
    }


@router.get("/users", response_model=List[UserResponse])
def list_users(role: Optional[str] = None, db: Session = Depends(get_db)):
    """List all registered users, optionally filtered by role."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role.upper())
    return query.order_by(User.created_at.desc()).all()


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific user profile by user_id."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


# ==============================================================================
# Companies
# ==============================================================================

@router.get("/companies", response_model=List[CompanyResponse])
def list_companies(db: Session = Depends(get_db)):
    """List all registered companies."""
    return db.query(Company).order_by(Company.created_at.desc()).all()


@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    """Create a new company / employer profile."""
    company = Company(
        name=payload.name.strip(),
        website=payload.website,
        location=payload.location,
        description=payload.description,
        industry=payload.industry
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    """Get company details by ID."""
    company = db.query(Company).filter(Company.company_id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return company


# ==============================================================================
# Jobs & Job Skills
# ==============================================================================

@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(company_id: Optional[int] = None, status_filter: Optional[str] = None, db: Session = Depends(get_db)):
    """List open job postings with company and required skill metadata."""
    query = db.query(Job)
    if company_id:
        query = query.filter(Job.company_id == company_id)
    if status_filter:
        query = query.filter(Job.status == status_filter.upper())

    jobs = query.order_by(Job.created_at.desc()).all()
    results = []
    for j in jobs:
        results.append(JobResponse(
            job_id=j.job_id,
            company_id=j.company_id,
            title=j.title,
            description=j.description,
            location=j.location,
            job_type=j.job_type,
            status=j.status,
            created_by=j.created_by,
            created_at=j.created_at,
            updated_at=j.updated_at,
            company_name=j.company.name if j.company else None,
            skills=[
                JobSkillResponse(
                    skill_id=s.skill_id,
                    job_id=s.job_id,
                    skill_name=s.skill_name,
                    is_required=s.is_required,
                    min_experience_years=s.min_experience_years,
                    created_at=s.created_at,
                    updated_at=s.updated_at
                ) for s in j.skills
            ]
        ))
    return results


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    """Create a new job posting with optional required skills."""
    # Verify company exists
    company = db.query(Company).filter(Company.company_id == payload.company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Company ID {payload.company_id} does not exist.")

    # If created_by is supplied, verify user exists
    if payload.created_by:
        creator = db.query(User).filter(User.user_id == payload.created_by).first()
        if not creator:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User ID {payload.created_by} does not exist.")

    job = Job(
        company_id=payload.company_id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        location=payload.location,
        job_type=payload.job_type,
        status=payload.status or "OPEN",
        created_by=payload.created_by
    )
    db.add(job)
    db.flush()

    # Add skills if provided
    if payload.skills:
        for sk in payload.skills:
            skill_obj = JobSkill(
                job_id=job.job_id,
                skill_name=sk.skill_name.strip(),
                is_required=sk.is_required,
                min_experience_years=sk.min_experience_years
            )
            db.add(skill_obj)

    db.commit()
    db.refresh(job)

    return JobResponse(
        job_id=job.job_id,
        company_id=job.company_id,
        title=job.title,
        description=job.description,
        location=job.location,
        job_type=job.job_type,
        status=job.status,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at,
        company_name=company.name,
        skills=[
            JobSkillResponse(
                skill_id=s.skill_id,
                job_id=s.job_id,
                skill_name=s.skill_name,
                is_required=s.is_required,
                min_experience_years=s.min_experience_years,
                created_at=s.created_at,
                updated_at=s.updated_at
            ) for s in job.skills
        ]
    )


# ==============================================================================
# Resumes
# ==============================================================================

@router.get("/resumes", response_model=List[ResumeResponse])
def list_resumes(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List resume documents, optionally filtered by user_id."""
    query = db.query(Resume)
    if user_id:
        query = query.filter(Resume.user_id == user_id)
    return query.order_by(Resume.created_at.desc()).all()


@router.post("/resumes", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def create_resume_record(payload: ResumeCreate, db: Session = Depends(get_db)):
    """Register a resume document reference linked to a user."""
    # Verify user exists
    user = db.query(User).filter(User.user_id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User ID {payload.user_id} does not exist.")

    resume = Resume(
        user_id=payload.user_id,
        file_name=payload.file_name,
        file_path=payload.file_path,
        file_size_bytes=payload.file_size_bytes,
        mime_type=payload.mime_type,
        raw_text=payload.raw_text
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


# ==============================================================================
# Applications (With Duplicate Active Application Prevention)
# ==============================================================================

@router.get("/applications", response_model=List[ApplicationResponse])
def list_applications(user_id: Optional[int] = None, job_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List job applications."""
    query = db.query(Application)
    if user_id:
        query = query.filter(Application.user_id == user_id)
    if job_id:
        query = query.filter(Application.job_id == job_id)

    apps = query.order_by(Application.created_at.desc()).all()
    results = []
    for app in apps:
        results.append(ApplicationResponse(
            application_id=app.application_id,
            job_id=app.job_id,
            user_id=app.user_id,
            resume_id=app.resume_id,
            status=app.status,
            is_active=app.is_active,
            applied_at=app.applied_at,
            created_at=app.created_at,
            updated_at=app.updated_at,
            job_title=app.job.title if app.job else None,
            company_name=app.job.company.name if (app.job and app.job.company) else None,
            applicant_name=app.user.name if app.user else None,
            applicant_email=app.user.email if app.user else None
        ))
    return results


@router.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def submit_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    """
    Submit a new job application.
    Enforces the architectural rule: A user CANNOT have multiple active applications for the same job.
    """
    # 1. Validate User
    user = db.query(User).filter(User.user_id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User ID {payload.user_id} does not exist.")

    # 2. Validate Job
    job = db.query(Job).filter(Job.job_id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job ID {payload.job_id} does not exist.")

    # 3. Validate Resume if provided
    if payload.resume_id:
        resume = db.query(Resume).filter(Resume.resume_id == payload.resume_id).first()
        if not resume:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Resume ID {payload.resume_id} does not exist.")

    # 4. Check for active application constraint
    active_app = db.query(Application).filter(
        Application.user_id == payload.user_id,
        Application.job_id == payload.job_id,
        Application.is_active == True
    ).first()

    if active_app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Candidate (User ID {payload.user_id}) already has an active application (Application ID {active_app.application_id}) for Job ID {payload.job_id}."
        )

    # 5. Insert application record
    new_app = Application(
        job_id=payload.job_id,
        user_id=payload.user_id,
        resume_id=payload.resume_id,
        status="SUBMITTED",
        is_active=True
    )

    try:
        db.add(new_app)
        db.commit()
        db.refresh(new_app)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database constraint violation: duplicate active application detected for this user and job."
        )

    return ApplicationResponse(
        application_id=new_app.application_id,
        job_id=new_app.job_id,
        user_id=new_app.user_id,
        resume_id=new_app.resume_id,
        status=new_app.status,
        is_active=new_app.is_active,
        applied_at=new_app.applied_at,
        created_at=new_app.created_at,
        updated_at=new_app.updated_at,
        job_title=job.title,
        company_name=job.company.name if job.company else None,
        applicant_name=user.name,
        applicant_email=user.email
    )


@router.patch("/applications/{application_id}/status", response_model=ApplicationResponse)
def update_application_status(application_id: int, payload: ApplicationStatusUpdate, db: Session = Depends(get_db)):
    """Update application workflow status or toggle active flag."""
    app = db.query(Application).filter(Application.application_id == application_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    app.status = payload.status
    if payload.is_active is not None:
        app.is_active = payload.is_active

    db.commit()
    db.refresh(app)

    return ApplicationResponse(
        application_id=app.application_id,
        job_id=app.job_id,
        user_id=app.user_id,
        resume_id=app.resume_id,
        status=app.status,
        is_active=app.is_active,
        applied_at=app.applied_at,
        created_at=app.created_at,
        updated_at=app.updated_at,
        job_title=app.job.title if app.job else None,
        company_name=app.job.company.name if (app.job and app.job.company) else None,
        applicant_name=app.user.name if app.user else None,
        applicant_email=app.user.email if app.user else None
    )


# ==============================================================================
# Interviews
# ==============================================================================

@router.get("/interviews", response_model=List[InterviewResponse])
def list_interviews(application_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List interview records."""
    query = db.query(Interview)
    if application_id:
        query = query.filter(Interview.application_id == application_id)
    return query.order_by(Interview.created_at.desc()).all()


@router.post("/interviews", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
def create_interview_record(payload: InterviewCreate, db: Session = Depends(get_db)):
    """Create an interview record linked to an application."""
    # Verify application exists
    app = db.query(Application).filter(Application.application_id == payload.application_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Application ID {payload.application_id} does not exist.")

    if payload.interviewer_id:
        interviewer = db.query(User).filter(User.user_id == payload.interviewer_id).first()
        if not interviewer:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Interviewer User ID {payload.interviewer_id} does not exist.")

    interview = Interview(
        application_id=payload.application_id,
        interviewer_id=payload.interviewer_id,
        scheduled_at=payload.scheduled_at,
        status=payload.status or "SCHEDULED",
        meeting_link=payload.meeting_link,
        notes=payload.notes
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


# ==============================================================================
# Seed Initial Real Data (Optional helper to test real database persistence)
# ==============================================================================

@router.post("/database/seed")
def seed_database(db: Session = Depends(get_db)):
    """Seed initial persistent records into the database if empty."""
    if db.query(User).count() > 0:
        return {"message": "Database already contains data.", "seeded": False}

    # 1. Create Admin Recruiter
    admin_user = User(
        name="Sarah Jenkins (Recruiter)",
        email="recruiter@acmecorp.com",
        password_hash=hash_password("admin123"),
        role=UserRole.ADMIN
    )
    # 2. Create Candidate User
    candidate_user = User(
        name="Alex Rivera (Candidate)",
        email="alex.rivera@example.com",
        password_hash=hash_password("candidate123"),
        role=UserRole.USER
    )
    db.add_all([admin_user, candidate_user])
    db.flush()

    # 3. Create Company
    company = Company(
        name="Acme AI Technologies",
        website="https://acmeai.example.com",
        location="San Francisco, CA / Remote",
        description="Pioneering next-generation intelligence platforms.",
        industry="Artificial Intelligence / Software"
    )
    db.add(company)
    db.flush()

    # 4. Create Jobs with Skills
    job1 = Job(
        company_id=company.company_id,
        title="Senior Full-Stack AI Engineer",
        description="Looking for an experienced engineer to architect scalable AI-driven web systems and microservices.",
        location="Remote (Global)",
        job_type="FULL_TIME",
        status="OPEN",
        created_by=admin_user.user_id
    )
    job2 = Job(
        company_id=company.company_id,
        title="Machine Learning Systems Architect",
        description="Design and optimize distributed model pipelines and backend orchestration services.",
        location="Hybrid - San Francisco",
        job_type="FULL_TIME",
        status="OPEN",
        created_by=admin_user.user_id
    )
    db.add_all([job1, job2])
    db.flush()

    # Skills for Job 1
    skills1 = [
        JobSkill(job_id=job1.job_id, skill_name="Python / FastAPI", is_required=True, min_experience_years=4.0),
        JobSkill(job_id=job1.job_id, skill_name="PostgreSQL / SQLAlchemy", is_required=True, min_experience_years=3.0),
        JobSkill(job_id=job1.job_id, skill_name="TypeScript / Modern Web", is_required=True, min_experience_years=3.0),
    ]
    # Skills for Job 2
    skills2 = [
        JobSkill(job_id=job2.job_id, skill_name="PyTorch / TensorFlow", is_required=True, min_experience_years=5.0),
        JobSkill(job_id=job2.job_id, skill_name="Distributed Systems", is_required=True, min_experience_years=4.0),
    ]
    db.add_all(skills1 + skills2)
    db.flush()

    # 5. Create Resume Record
    resume = Resume(
        user_id=candidate_user.user_id,
        file_name="Alex_Rivera_Senior_Resume.pdf",
        file_path="/storage/resumes/alex_rivera_senior.pdf",
        file_size_bytes=245000,
        mime_type="application/pdf",
        raw_text="Senior Full-Stack Engineer with 6 years experience in Python, FastAPI, React, and cloud databases."
    )
    db.add(resume)
    db.flush()

    # 6. Create Application
    application = Application(
        job_id=job1.job_id,
        user_id=candidate_user.user_id,
        resume_id=resume.resume_id,
        status="SUBMITTED",
        is_active=True
    )
    db.add(application)
    db.flush()

    # 7. Create Interview
    interview = Interview(
        application_id=application.application_id,
        interviewer_id=admin_user.user_id,
        status="SCHEDULED",
        meeting_link="https://meet.example.com/interview-alex-rivera",
        notes="Technical architecture screen."
    )
    db.add(interview)
    db.commit()

    return {"message": "Database successfully initialized with real persistent entities across all 7 tables.", "seeded": True}
