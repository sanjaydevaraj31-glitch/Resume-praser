"""
Data models and schemas for Resume Parser Agent.
Defines typed structures for candidate profile, extracted resume data,
evidence citations, job matching criteria, fit scoring, and final reports.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    email: Optional[str] = Field(None, description="Candidate contact email")
    phone: Optional[str] = Field(None, description="Candidate contact phone number")
    location: Optional[str] = Field(None, description="City, State / Country")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
    portfolio: Optional[str] = Field(None, description="Portfolio website URL")


class CandidateProfile(BaseModel):
    full_name: Optional[str] = Field(None, description="Full name of the candidate")
    professional_title: Optional[str] = Field(None, description="Current or target professional title")
    summary: Optional[str] = Field(None, description="Executive summary or professional overview")
    contact: Optional[ContactInfo] = Field(default_factory=ContactInfo, description="Candidate contact info")
    total_experience_years: Optional[float] = Field(None, description="Estimated total years of relevant experience")
    primary_skills: List[str] = Field(default_factory=list, description="Top highlighted primary skills")


class WorkExperience(BaseModel):
    company: str = Field(..., description="Company or organization name")
    role: str = Field(..., description="Job title / role")
    location: Optional[str] = Field(None, description="Location of the role")
    start_date: Optional[str] = Field(None, description="Start date (e.g. Jan 2021)")
    end_date: Optional[str] = Field(None, description="End date or 'Present'")
    is_current: bool = Field(False, description="Whether this is the current job")
    responsibilities: List[str] = Field(default_factory=list, description="Key duties and responsibilities")
    technologies: List[str] = Field(default_factory=list, description="Technologies and tools used")


class Education(BaseModel):
    institution: str = Field(..., description="University, College, or Institute name")
    degree: Optional[str] = Field(None, description="Degree earned (e.g. B.S., M.S., Ph.D.)")
    field_of_study: Optional[str] = Field(None, description="Major / Field of study")
    graduation_year: Optional[str] = Field(None, description="Year of graduation")
    gpa: Optional[str] = Field(None, description="GPA if reported")


class ExtractedResumeData(BaseModel):
    profile: Optional[CandidateProfile] = None
    experiences: List[WorkExperience] = Field(default_factory=list, description="List of work experiences")
    education: List[Education] = Field(default_factory=list, description="List of educational qualifications")
    technical_skills: List[str] = Field(default_factory=list, description="Extracted technical skills")
    soft_skills: List[str] = Field(default_factory=list, description="Extracted soft / leadership skills")
    certifications: List[str] = Field(default_factory=list, description="Certifications and licenses")
    languages: List[str] = Field(default_factory=list, description="Languages spoken/written")


class EvidenceCitation(BaseModel):
    claim: str = Field(..., description="The qualification or requirement claim being verified")
    verbatim_quote: str = Field(..., description="Exact textual excerpt from the resume providing evidence")
    section: str = Field(..., description="Resume section (e.g., Experience at Acme Corp, Education)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")


class JobMatchCriterion(BaseModel):
    requirement_id: str = Field(..., description="Unique identifier for the JD requirement")
    requirement_text: str = Field(..., description="The stated requirement from the job description")
    category: str = Field("Required Skill", description="Category: Required Skill, Experience, Education, Preferred")
    status: str = Field("unmatched", description="Match status: matched, partial, missing")
    evidence: Optional[EvidenceCitation] = Field(None, description="Supporting evidence from resume if matched")
    notes: Optional[str] = Field(None, description="Brief justification of the match status")


class FitScoreBreakdown(BaseModel):
    overall_score: int = Field(..., ge=0, le=100, description="Composite fit score (0-100)")
    skills_score: int = Field(..., ge=0, le=100, description="Skills alignment score (0-100)")
    experience_score: int = Field(..., ge=0, le=100, description="Experience level alignment score (0-100)")
    education_score: int = Field(..., ge=0, le=100, description="Educational alignment score (0-100)")
    tier: str = Field("Unassessed", description="Match tier: Strong Match, Moderate Match, Potential Match, Low Match")


class FinalReport(BaseModel):
    executive_summary: str = Field(..., description="High-level synthesis of candidate fit")
    top_strengths: List[str] = Field(default_factory=list, description="Key candidate strengths relative to JD")
    potential_gaps: List[str] = Field(default_factory=list, description="Identified qualification or experience gaps")
    interview_recommendations: List[str] = Field(default_factory=list, description="Suggested deep-dive interview questions")
    overall_verdict: str = Field("Pending Analysis", description="Hiring decision recommendation")


class AnalysisStatus(BaseModel):
    stage: str = Field("Stage 1 - Foundation", description="Current application milestone")
    is_ready_for_parsing: bool = Field(True, description="Indicates system is ready for Stage 2 parser integration")
    file_received: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_content_type: Optional[str] = None
    jd_word_count: Optional[int] = None
    message: str = Field("Foundation ready. AI parsing engine will be enabled in subsequent stage.", description="Status message")


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str = "Resume Parser Agent"
    version: str = "1.0.0-stage1"
    supported_formats: List[str] = [".pdf", ".docx"]
