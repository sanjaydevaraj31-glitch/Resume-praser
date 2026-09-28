"""Application model representing a candidate applying to a job posting."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint, text, func
from sqlalchemy.orm import relationship
from ..database import Base


class Application(Base):
    __tablename__ = "applications"

    application_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.resume_id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), default="SUBMITTED", nullable=False, index=True)  # SUBMITTED, IN_REVIEW, SHORTLISTED, REJECTED, WITHDRAWN
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    job = relationship("Job", back_populates="applications")
    user = relationship("User", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")

    __table_args__ = (
        # Unique constraint to prevent duplicate active applications for the same job by the same user
        Index(
            "uq_user_job_active_app_idx",
            "user_id",
            "job_id",
            unique=True,
            sqlite_where=text("is_active = 1")
        ),
        # Fallback multi-column index for quick lookup
        Index("ix_applications_user_job", "user_id", "job_id"),
    )

    def __repr__(self):
        return f"<Application(application_id={self.application_id}, user_id={self.user_id}, job_id={self.job_id}, status='{self.status}', is_active={self.is_active})>"
