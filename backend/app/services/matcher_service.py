"""
Job Matcher Service Stub (Stage 1).
Provides modular interface for comparing extracted resume data against a Job Description.
"""

from typing import List, Optional
from ..models.schemas import ExtractedResumeData, JobMatchCriterion, FitScoreBreakdown


class JobMatcherService:
    """Service responsible for matching candidate qualifications against job requirements."""

    @classmethod
    def match_qualifications(
        cls, resume_data: ExtractedResumeData, job_description: str
    ) -> List[JobMatchCriterion]:
        """
        Stage 2/3 entry point: Extracts criteria from JD and matches against candidate profile.
        """
        # Kept unpopulated in Stage 1 per requirements
        return []

    @classmethod
    def calculate_fit_score(
        cls, match_criteria: List[JobMatchCriterion]
    ) -> Optional[FitScoreBreakdown]:
        """
        Stage 3 entry point: Calculates composite fit score with category breakdowns.
        """
        # Kept unpopulated in Stage 1 per requirements
        return None
