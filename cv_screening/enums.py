"""Enums for CV Screening Agent."""

from enum import Enum


class Seniority(str, Enum):
    """Job seniority levels."""

    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class FileType(str, Enum):
    """Supported CV file types."""

    PDF = "pdf"
    DOCX = "docx"


class SkillProficiency(str, Enum):
    """Skill proficiency levels."""

    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class FlagType(str, Enum):
    """Types of screening flags/concerns."""

    MISSING_REQUIRED_SKILL = "missing_required_skill"
    WEAK_SKILL_MATCH = "weak_skill_match"
    OVERQUALIFIED = "overqualified"
    UNDERQUALIFIED = "underqualified"
    EXPERIENCE_GAP = "experience_gap"
    LOCATION_MISMATCH = "location_mismatch"
    SENIORITY_MISMATCH = "seniority_mismatch"
    AMBIGUOUS_DATES = "ambiguous_dates"
    OVERLAPPING_ROLES = "overlapping_roles"
    RECENT_JOB_HOPPER = "recent_job_hopper"
    MISSING_EDUCATION = "missing_education"
    DATE_PARSING_ISSUE = "date_parsing_issue"


class CandidateIDSource(str, Enum):
    """Source of candidate ID."""

    HEADHUNTING_AGENT = "headhunting_agent"
    GENERATED = "generated"
