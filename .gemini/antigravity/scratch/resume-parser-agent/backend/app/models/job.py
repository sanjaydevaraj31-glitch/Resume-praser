"""Job and JobSkill models with relational mappings and indexes."""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=True)
    job_type = Column(String(50), default="FULL_TIME", nullable=True)
    status = Column(String(50), default="OPEN", nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    company = relationship("Company", back_populates="jobs")
    creator = relationship("User", back_populates="created_jobs", foreign_keys=[created_by])
    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(job_id={self.job_id}, title='{self.title}', status='{self.status}')>"


class JobSkill(Base):
    __tablename__ = "job_skills"

    skill_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(150), nullable=False, index=True)
    is_required = Column(Boolean, default=True, nullable=False)
    min_experience_years = Column(Float, default=0.0, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    job = relationship("Job", back_populates="skills")

    def __repr__(self):
        return f"<JobSkill(skill_id={self.skill_id}, skill='{self.skill_name}', required={self.is_required})>"
