"""
Resume Parser Service Stub (Stage 1).
Provides modular interface for PDF and DOCX document extraction.
Actual AI and NLP parsing logic will be attached in subsequent stages.
"""

from typing import Optional, BinaryIO
from ..models.schemas import ExtractedResumeData, AnalysisStatus


class ResumeParserService:
    """Service responsible for loading and extracting structured data from resumes."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

    @classmethod
    def validate_file(cls, filename: str, content_type: Optional[str] = None) -> bool:
        """Validates that the file has a supported resume format."""
        if not filename:
            return False
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return ext in cls.SUPPORTED_EXTENSIONS

    @classmethod
    def inspect_upload(
        cls, filename: str, file_size: int, content_type: Optional[str], jd_text: str
    ) -> AnalysisStatus:
        """
        Stage 1 inspect handler: Confirms receipt and validation of file & job description
        without generating ungrounded or mock data.
        """
        is_valid = cls.validate_file(filename, content_type)
        jd_words = len(jd_text.strip().split()) if jd_text else 0

        if not is_valid:
            return AnalysisStatus(
                stage="Stage 1 - Foundation",
                is_ready_for_parsing=False,
                file_received=filename,
                file_size_bytes=file_size,
                file_content_type=content_type,
                jd_word_count=jd_words,
                message=f"Unsupported file format '{filename}'. Only PDF and DOCX documents are accepted."
            )

        return AnalysisStatus(
            stage="Stage 1 - Foundation",
            is_ready_for_parsing=True,
            file_received=filename,
            file_size_bytes=file_size,
            file_content_type=content_type,
            jd_word_count=jd_words,
            message="Resume document and Job Description successfully received and validated. Parser engine is ready for Stage 2 integration."
        )

    @classmethod
    async def parse_document(cls, file: BinaryIO, filename: str) -> Optional[ExtractedResumeData]:
        """
        Stage 2 entry point: Will parse raw text and structure it into ExtractedResumeData.
        """
        # Kept unpopulated in Stage 1 per requirements
        return None
