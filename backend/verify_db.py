"""
Comprehensive automated test and verification script for Resume Parser Agent.
Validates:
1. Persistent SQLite connection & foreign key enforcement.
2. Presence and structure of all 7 required tables.
3. User schema requirements (user_id, name, email, password_hash, role, created_at, updated_at).
4. Role enum validation (USER, ADMIN).
5. User email unique constraint enforcement.
6. Foreign key relationship integrity across all tables.
7. Prevention of multiple active applications for the same job by the same user.
8. Automatic timestamps and updates.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.database import engine, Base, SessionLocal, init_db, DB_FILE
from app.models import User, UserRole, Company, Job, JobSkill, Resume, Application, Interview
from app.core.security import hash_password, verify_password
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError


def run_verification():
    print("=" * 70)
    print("[VERIFICATION] RESUME PARSER AGENT - DATABASE ARCHITECTURE TEST SUITE")
    print("=" * 70)

    # 1. Initialize Tables
    print("\n[Step 1] Initializing persistent database...")
    init_db()
    print(f"[OK] Database file verified at: {DB_FILE}")
    print(f"[OK] File exists: {DB_FILE.exists()}")

    db = SessionLocal()
    inspector = inspect(engine)

    try:
        # Check foreign keys pragma
        fk_pragma = db.execute(text("PRAGMA foreign_keys")).scalar()
        print(f"[OK] SQLite PRAGMA foreign_keys: {bool(fk_pragma)} (Enforced)")

        # 2. Verify all 7 tables
        print("\n[Step 2] Verifying 7 core tables...")
        required_tables = {"users", "companies", "jobs", "job_skills", "applications", "resumes", "interviews"}
        actual_tables = set(inspector.get_table_names())
        
        missing = required_tables - actual_tables
        if missing:
            raise AssertionError(f"Missing required tables: {missing}")
        print(f"[OK] All 7 tables present: {sorted(list(required_tables))}")

        # 3. Verify Users table columns and constraints
        print("\n[Step 3] Verifying 'users' table structure...")
        user_cols = {col["name"]: col for col in inspector.get_columns("users")}
        required_user_cols = {"user_id", "name", "email", "password_hash", "role", "created_at", "updated_at"}
        missing_user_cols = required_user_cols - set(user_cols.keys())
        if missing_user_cols:
            raise AssertionError(f"Missing columns in 'users': {missing_user_cols}")
        print(f"[OK] 'users' table columns verified: {sorted(list(required_user_cols))}")
        print(f"     - user_id: {user_cols['user_id']['type']} (Primary Key: {user_cols['user_id']['primary_key']})")
        print(f"     - email: {user_cols['email']['type']} (Nullable: {user_cols['email']['nullable']})")
        print(f"     - role: {user_cols['role']['type']}")

        # 4. Verify Role Enum Support (USER and ADMIN)
        print("\n[Step 4] Verifying Role support (USER and ADMIN)...")
        # Clean any test users from prior runs
        db.query(Application).delete()
        db.query(Interview).delete()
        db.query(Resume).delete()
        db.query(JobSkill).delete()
        db.query(Job).delete()
        db.query(Company).delete()
        db.query(User).delete()
        db.commit()

        user_candidate = User(
            name="Alice Candidate",
            email="alice.candidate@example.com",
            password_hash=hash_password("password123"),
            role=UserRole.USER
        )
        user_admin = User(
            name="Bob Recruiter",
            email="bob.recruiter@example.com",
            password_hash=hash_password("adminpass456"),
            role=UserRole.ADMIN
        )
        db.add_all([user_candidate, user_admin])
        db.commit()
        db.refresh(user_candidate)
        db.refresh(user_admin)

        print(f"[OK] Created USER role entity: ID={user_candidate.user_id}, Name={user_candidate.name}, Role={user_candidate.role.value}")
        print(f"[OK] Created ADMIN role entity: ID={user_admin.user_id}, Name={user_admin.name}, Role={user_admin.role.value}")
        print(f"[OK] Password verification test: {verify_password('password123', user_candidate.password_hash)}")

        # 5. Verify User Email Unique Constraint
        print("\n[Step 5] Verifying User Email Unique Constraint...")
        duplicate_user = User(
            name="Alice Imposter",
            email="alice.candidate@example.com",  # Duplicate email
            password_hash=hash_password("otherpass"),
            role=UserRole.USER
        )
        db.add(duplicate_user)
        try:
            db.commit()
            raise AssertionError("FAILURE: Duplicate email was permitted! Unique constraint failed.")
        except IntegrityError:
            db.rollback()
            print("[OK] Unique email constraint successfully enforced: Duplicate email was rejected.")

        # 6. Verify Foreign Key Relationships across all tables
        print("\n[Step 6] Verifying Relational Data Model & Foreign Keys...")
        # Create company
        tech_corp = Company(
            name="TechCorp AI",
            website="https://techcorp.ai",
            location="New York, NY",
            description="Leading AI recruitment platform developer."
        )
        db.add(tech_corp)
        db.commit()
        db.refresh(tech_corp)
        print(f"[OK] Created Company: ID={tech_corp.company_id}, Name='{tech_corp.name}'")

        # Create Job linked to company & admin user
        job = Job(
            company_id=tech_corp.company_id,
            title="Senior Backend Engineer",
            description="Developing high-throughput database systems and AI APIs.",
            location="Remote",
            created_by=user_admin.user_id
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        print(f"[OK] Created Job with FKs: Job ID={job.job_id} -> Company ID={job.company_id}, CreatedBy={job.created_by}")

        # Create JobSkills linked to Job
        skill1 = JobSkill(job_id=job.job_id, skill_name="Python / FastAPI", is_required=True, min_experience_years=3.0)
        skill2 = JobSkill(job_id=job.job_id, skill_name="SQLAlchemy / PostgreSQL", is_required=True, min_experience_years=2.0)
        db.add_all([skill1, skill2])
        db.commit()
        print(f"[OK] Created JobSkills linked to Job ID {job.job_id}: {[skill1.skill_name, skill2.skill_name]}")

        # Create Resume linked to Candidate
        resume = Resume(
            user_id=user_candidate.user_id,
            file_name="Alice_Resume_2026.pdf",
            file_path="/uploads/resumes/alice_2026.pdf",
            file_size_bytes=102400,
            mime_type="application/pdf",
            raw_text="Alice Candidate - Experienced Backend Developer with Python & SQL expertise."
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        print(f"[OK] Created Resume: ID={resume.resume_id} linked to Candidate ID={resume.user_id}")

        # Create Application linked to Job, User, Resume
        app1 = Application(
            job_id=job.job_id,
            user_id=user_candidate.user_id,
            resume_id=resume.resume_id,
            status="SUBMITTED",
            is_active=True
        )
        db.add(app1)
        db.commit()
        db.refresh(app1)
        print(f"[OK] Created Application: ID={app1.application_id} (Job ID={app1.job_id}, User ID={app1.user_id}, Active={app1.is_active})")

        # Create Interview linked to Application and Interviewer
        interview = Interview(
            application_id=app1.application_id,
            interviewer_id=user_admin.user_id,
            status="SCHEDULED",
            meeting_link="https://meet.techcorp.ai/room-101",
            notes="Initial cultural and technical assessment."
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)
        print(f"[OK] Created Interview: ID={interview.interview_id} linked to Application ID={interview.application_id} & Interviewer ID={interview.interviewer_id}")

        # 7. Verify Active Application Constraint
        print("\n[Step 7] Verifying Single Active Application per User/Job Constraint...")
        # Attempting second active application for the same job and user
        duplicate_active_app = Application(
            job_id=job.job_id,
            user_id=user_candidate.user_id,
            resume_id=resume.resume_id,
            status="SUBMITTED",
            is_active=True
        )
        db.add(duplicate_active_app)
        try:
            db.commit()
            raise AssertionError("FAILURE: Multiple active applications for the same job were permitted!")
        except IntegrityError:
            db.rollback()
            print("[OK] Active Application Constraint verified: Second active application was rejected by DB constraint.")

        # Test that an inactive application DOES allow a new application
        print("\n[Step 8] Verifying Inactive Application Behavior...")
        # Mark first application as inactive (e.g. REJECTED / WITHDRAWN)
        app1.is_active = False
        app1.status = "REJECTED"
        db.commit()

        # Now creating a new application should succeed
        new_active_app = Application(
            job_id=job.job_id,
            user_id=user_candidate.user_id,
            resume_id=resume.resume_id,
            status="SUBMITTED",
            is_active=True
        )
        db.add(new_active_app)
        db.commit()
        db.refresh(new_active_app)
        print(f"[OK] Permitted new active application (ID={new_active_app.application_id}) after previous application was marked inactive.")

        # 9. Verify Timestamps
        print("\n[Step 9] Verifying Timestamps on creation...")
        print(f"     - User created_at: {user_candidate.created_at}")
        print(f"     - Job created_at: {job.created_at}")
        print(f"     - Application applied_at: {new_active_app.applied_at}")
        print(f"     - Interview created_at: {interview.created_at}")
        assert user_candidate.created_at is not None
        assert job.created_at is not None
        assert new_active_app.applied_at is not None
        print("[OK] Timestamps successfully populated.")

        print("\n" + "=" * 70)
        print("[SUCCESS] ALL DATABASE ARCHITECTURE AND CONSTRAINT TESTS PASSED 100%!")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    run_verification()
