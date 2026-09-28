"""Interview model for scheduled candidate evaluations."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base


class Interview(Base):
    __tablename__ = "interviews"

    interview_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.application_id", ondelete="CASCADE"), nullable=False, index=True)
    interviewer_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="SCHEDULED", nullable=False, index=True)  # SCHEDULED, COMPLETED, CANCELLED, RESCHEDULED
    meeting_link = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    application = relationship("Application", back_populates="interviews")
    interviewer = relationship("User", back_populates="interviews_conducted", foreign_keys=[interviewer_id])

    def __repr__(self):
        return f"<Interview(interview_id={self.interview_id}, application_id={self.application_id}, status='{self.status}')>"
