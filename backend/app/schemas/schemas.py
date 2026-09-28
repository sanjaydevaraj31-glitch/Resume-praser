"""
Pydantic schemas for data validation and API serialization.
"""

import re
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class UserRoleEnum(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


# ==========================================
# User Schemas
# ==========================================

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Full name of the user")
    email: str = Field(..., min_length=5, max_length=255, description="Unique email address")
    role: UserRoleEnum = Field(default=UserRoleEnum.USER, description="User role: USER or ADMIN")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, clean):
            raise ValueError("Invalid email format. Please provide a valid email address.")
        return clean

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2:
            raise ValueError("Full Name must be at least 2 characters long.")
        return clean


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Plaintext password (min 8 chars)")
    confirm_password: Optional[str] = Field(None, description="Password confirmation")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_login_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(UserBase):
    user_id: int
    created_at: datetime
    updated_at: datetime

    # Explicitly ensure password_hash is NEVER exposed
    class Config:
        from_attributes = True


# ==========================================
# Company Schemas
# ==========================================

class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    website: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Job & Skill Schemas
# ==========================================

class JobSkillBase(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=150)
    is_required: bool = True
    min_experience_years: Optional[float] = 0.0


class JobSkillCreate(JobSkillBase):
    pass


class JobSkillResponse(JobSkillBase):
    skill_id: int
    job_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobBase(BaseModel):
    company_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    location: Optional[str] = "Remote"
    job_type: Optional[str] = "FULL_TIME"
    status: Optional[str] = "OPEN"


class JobCreate(JobBase):
    created_by: Optional[int] = None
    skills: Optional[List[JobSkillCreate]] = []


class JobResponse(JobBase):
    job_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    company_name: Optional[str] = None
    skills: List[JobSkillResponse] = []

    class Config:
        from_attributes = True


# ==========================================
# Resume Schemas
# ==========================================

class ResumeBase(BaseModel):
    user_id: int
    file_name: str
    file_path: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    raw_text: Optional[str] = None


class ResumeCreate(ResumeBase):
    pass


class ResumeResponse(ResumeBase):
    resume_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Application Schemas
# ==========================================

class ApplicationBase(BaseModel):
    job_id: int
    user_id: int
    resume_id: Optional[int] = None
    status: Optional[str] = "SUBMITTED"
    is_active: Optional[bool] = True


class ApplicationCreate(BaseModel):
    job_id: int
    user_id: int
    resume_id: Optional[int] = None


class ApplicationStatusUpdate(BaseModel):
    status: str
    is_active: Optional[bool] = None


class ApplicationResponse(ApplicationBase):
    application_id: int
    applied_at: datetime
    created_at: datetime
    updated_at: datetime
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    applicant_name: Optional[str] = None
    applicant_email: Optional[str] = None

    class Config:
        from_attributes = True


# ==========================================
# Interview Schemas
# ==========================================

class InterviewBase(BaseModel):
    application_id: int
    interviewer_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = "SCHEDULED"
    meeting_link: Optional[str] = None
    notes: Optional[str] = None


class InterviewCreate(InterviewBase):
    pass


class InterviewResponse(InterviewBase):
    interview_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# Database Inspection & Health Schemas
# ==========================================

class ColumnSchemaInfo(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool
    default: Optional[str] = None


class TableSchemaInfo(BaseModel):
    table_name: str
    columns: List[ColumnSchemaInfo]
    foreign_keys: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    row_count: int


class DatabaseHealthResponse(BaseModel):
    status: str
    engine: str
    database_file: str
    tables_count: int
    tables: List[str]
    foreign_keys_enabled: bool


class DatabaseStatsResponse(BaseModel):
    users_count: int
    companies_count: int
    jobs_count: int
    job_skills_count: int
    applications_count: int
    active_applications_count: int
    resumes_count: int
    interviews_count: int
