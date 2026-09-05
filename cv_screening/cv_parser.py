"""CV parsing engine for PDF and DOCX files."""

import logging
from pathlib import Path
from typing import Optional

import pdfplumber
from docx import Document
from pydantic import ValidationError

from app.models.schemas import ParsedCV, WorkExperience, Education
from app.tools.validators import (
    DateParser,
    EmailValidator,
    LocationExtractor,
    PhoneValidator,
    SkillExtractor,
)

logger = logging.getLogger(__name__)


class CVParseError(Exception):
    """Raised when CV parsing fails."""

    pass


class PDFParser:
    """Extract text from PDF files."""

    @staticmethod
    def extract_text(file_path: str | Path) -> str:
        """
        Extract text from PDF.
        Raises: CVParseError if PDF is unreadable or image-only.
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise CVParseError(f"File not found: {file_path}")

            text_content = []

            try:
                with pdfplumber.open(file_path) as pdf:
                    if len(pdf.pages) == 0:
                        raise CVParseError("PDF has no pages")

                    for page_num, page in enumerate(pdf.pages, 1):
                        try:
                            page_text = page.extract_text()
                            if not page_text or not page_text.strip():
                                logger.warning(
                                    f"Page {page_num} extracted no text "
                                    "(possibly image-only)"
                                )
                            text_content.append(page_text or "")
                        except Exception as page_error:
                            logger.warning(
                                f"Failed to extract page {page_num}: "
                                f"{page_error}"
                            )
                            text_content.append("")

            except Exception as pdf_error:
                raise CVParseError(
                    f"Failed to read PDF: {str(pdf_error)}"
                ) from pdf_error

            full_text = "\n".join(text_content).strip()

            if not full_text:
                raise CVParseError(
                    "PDF contains no extractable text "
                    "(possibly scanned/image-only)"
                )

            return full_text

        except CVParseError:
            raise
        except Exception as e:
            raise CVParseError(f"Unexpected PDF parsing error: {str(e)}") from e


class DOCXParser:
    """Extract text from DOCX files."""

    @staticmethod
    def extract_text(file_path: str | Path) -> str:
        """
        Extract text from DOCX.
        Raises: CVParseError if DOCX is unreadable.
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise CVParseError(f"File not found: {file_path}")

            try:
                doc = Document(file_path)
            except Exception as e:
                raise CVParseError(
                    f"Failed to read DOCX: {str(e)}"
                ) from e

            paragraphs = [para.text for para in doc.paragraphs]
            text_content = "\n".join(paragraphs).strip()

            if not text_content:
                raise CVParseError("DOCX contains no text")

            return text_content

        except CVParseError:
            raise
        except Exception as e:
            raise CVParseError(
                f"Unexpected DOCX parsing error: {str(e)}"
            ) from e


class CVStructuredParser:
    """Parse extracted CV text into structured fields."""

    def __init__(self, raw_text: str):
        """Initialize with extracted raw text."""
        self.raw_text = raw_text
        self.lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

    def parse(self) -> ParsedCV:
        """
        Parse raw text into structured ParsedCV.
        Uses best-effort extraction + confidence scoring.
        """
        name = self._extract_name()
        email = EmailValidator.extract_from_text(self.raw_text)
        phone = PhoneValidator.extract_from_text(self.raw_text)
        location = LocationExtractor.extract(self.raw_text)
        summary = self._extract_summary()
        work_history = self._extract_work_history()
        education = self._extract_education()
        skills = SkillExtractor.extract(self.raw_text)
        total_years = self._calculate_total_years(work_history)
        confidence = self._calculate_confidence(
            name, email, work_history, education, skills
        )

        return ParsedCV(
            name=name,
            email=email,
            phone=phone,
            location=location,
            summary=summary,
            work_history=work_history,
            education=education,
            skills=skills,
            total_years_experience=total_years,
            raw_text=self.raw_text,
            extraction_confidence=confidence,
        )

    def _extract_name(self) -> str:
        """
        Extract candidate name (usually first non-empty line).
        Best-effort: returns first line if it looks like a name.
        """
        if not self.lines:
            return "Unknown Candidate"

        # Try first line
        first_line = self.lines[0]

        # Simple heuristic: if first line is short and not all caps/numbers,
        # it's probably a name
        if len(first_line) < 60 and not first_line.isupper():
            return first_line

        # Otherwise search for common name patterns
        for line in self.lines[:10]:
            if 1 < len(line.split()) <= 4:  # 1-4 words
                if not any(char.isdigit() for char in line):  # No numbers
                    return line

        return "Unknown Candidate"

    def _extract_summary(self) -> Optional[str]:
        """
        Extract professional summary or objective.
        Looks for common keywords.
        """
        summary_keywords = [
            'summary', 'objective', 'professional', 'about',
            'introduction', 'profile'
        ]

        text_lower = self.raw_text.lower()

        for keyword in summary_keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Get next ~200 chars
                start = idx
                end = min(start + 200, len(self.raw_text))
                snippet = self.raw_text[start:end]
                # Take first paragraph
                summary = snippet.split('\n\n')[0].strip()
                if len(summary) > 20:
                    return summary

        return None

    def _extract_work_history(self) -> list[WorkExperience]:
        """Extract work experience entries."""
        experiences = []

        work_keywords = {"experience", "employment", "work history", "professional"}

        lines = [line.strip() for line in self.raw_text.splitlines()]

        # Find the section heading by line, not substring.
        start = 0
        for i, line in enumerate(lines):
            if line.lower() in work_keywords:
                start = i + 1
                break

        section = lines[start:]

        # Group entries separated by blank lines.
        entries = []
        current = []

        for line in section:
            if line.strip():
                current.append(line.strip())
            elif current:
                entries.append(current)
                current = []

        if current:
            entries.append(current)

        for lines in entries[:10]:
            if len(lines) < 3:
                continue

            try:
                company = lines[0]
                title = lines[1]

                start_date = None
                end_date = None

                for line in lines[2:]:
                    if "20" not in line:
                        continue

                    # Split only on the separator between dates.
                    parts = line.split(" - ", 1)
                    if len(parts) != 2:
                        continue

                    start_date = DateParser.parse(parts[0].strip())

                    if "present" in parts[1].lower():
                        end_date = None
                    else:
                        end_date = DateParser.parse(parts[1].strip())

                    if start_date:
                        break

                if not start_date:
                    continue

                duration = DateParser.calculate_duration(start_date, end_date)

                experiences.append(
                    WorkExperience(
                        company=company,
                        title=title,
                        start_date=start_date,
                        end_date=end_date,
                        duration_years=duration,
                        is_current=end_date is None,
                        description="\n".join(lines[3:]) or None,
                    )
                )

            except (ValidationError, ValueError) as e:
                logger.warning(f"Failed to parse work entry: {e}")

        return experiences
    def _extract_education(self) -> list[Education]:
        """Extract education entries."""
        educations = []

        lines = [line.strip() for line in self.raw_text.splitlines()]

        # Find the actual Education heading.
        start = 0
        for i, line in enumerate(lines):
            if line.lower() == "education":
                start = i + 1
                break

        section = lines[start:]

        entries = []
        current = []

        for line in section:
            if line.strip():
                current.append(line.strip())
            elif current:
                entries.append(current)
                current = []

        if current:
            entries.append(current)

        for lines in entries[:5]:
            if len(lines) < 3:
                continue

            try:
                institution = lines[0]
                degree = lines[1]
                field = lines[2]

                graduation_year = None

                for line in lines[3:]:
                    parsed = DateParser.parse(line)
                    if parsed and len(parsed) == 4:
                        graduation_year = int(parsed)
                        break

                educations.append(
                    Education(
                        institution=institution,
                        degree=degree,
                        field=field,
                        graduation_year=graduation_year,
                    )
                )

            except (ValidationError, ValueError) as e:
                logger.warning(f"Failed to parse education entry: {e}")

        return educations

    def _calculate_total_years(
        self, work_history: list[WorkExperience]
    ) -> float:
        """
        Calculate total years of experience from work history.
        Accounts for overlaps and gaps.
        """
        if not work_history:
            return 0.0

        try:
            total = sum(exp.duration_years for exp in work_history)
            return round(total, 2)
        except Exception as e:
            logger.warning(f"Failed to calculate total years: {e}")
            return 0.0

    def _calculate_confidence(
        self,
        name: str,
        email: Optional[str],
        work_history: list[WorkExperience],
        education: list[Education],
        skills: list[str],
    ) -> float:
        """
        Calculate extraction confidence (0-1).
        Higher = more fields extracted, more complete CV.
        """
        extracted_fields = 0
        possible_fields = 5

        if name and name != "Unknown Candidate":
            extracted_fields += 1
        if email:
            extracted_fields += 1
        if work_history:
            extracted_fields += 1
        if education:
            extracted_fields += 1
        if skills:
            extracted_fields += 1

        confidence = extracted_fields / possible_fields
        return round(confidence, 2)


class CVParser:
    """Main CV parser (facade)."""

    @staticmethod
    def parse(file_path: str | Path, file_type: str) -> ParsedCV:
        """
        Parse CV from file (PDF or DOCX).
        Args:
            file_path: Path to CV file
            file_type: "pdf" or "docx"
        Returns:
            ParsedCV with structured data
        Raises:
            CVParseError if file is unreadable/unparseable
        """
        file_type = file_type.lower()

        # Extract text based on file type
        if file_type == "pdf":
            raw_text = PDFParser.extract_text(file_path)
        elif file_type == "docx":
            raw_text = DOCXParser.extract_text(file_path)
        else:
            raise CVParseError(f"Unsupported file type: {file_type}")

        # Parse structured data
        parser = CVStructuredParser(raw_text)
        parsed_cv = parser.parse()

        logger.info(
            f"Successfully parsed CV: {parsed_cv.name} "
            f"({parsed_cv.total_years_experience} years, "
            f"confidence={parsed_cv.extraction_confidence})"
        )

        return parsed_cv