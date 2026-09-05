"""Structured schemas for agent communication."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CandidateExperience(BaseModel):
    """Candidate's work experience entry."""
    company: str = Field(..., description="Company name")
    role: str = Field(..., description="Job title/role")
    duration_years: float = Field(..., ge=0, description="Years in this role")
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Key responsibilities and achievements"
    )


class Candidate(BaseModel):
    """Structured candidate information for agent."""
    candidate_id: str = Field(..., description="Unique candidate ID")
    name: str = Field(..., description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    skills: list[str] = Field(default_factory=list, description="Technical skills")
    experience: list[CandidateExperience] = Field(
        default_factory=list,
        description="Work experience"
    )
    education: list[str] = Field(
        default_factory=list,
        description="Education (degrees, schools)"
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="Professional certifications"
    )

    class Config:
        use_enum_values = False


class Job(BaseModel):
    """Structured job requisition for agent."""
    job_id: str = Field(..., description="Unique job ID")
    role: str = Field(..., description="Job title")
    description: str = Field(..., description="Full job description")
    seniority: str = Field(..., description="e.g., entry, mid, senior, lead")
    required_skills: list[str] = Field(..., description="Must-have skills")
    preferred_skills: list[str] = Field(
        default_factory=list,
        description="Nice-to-have skills"
    )
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Key job responsibilities"
    )
    qualifications: list[str] = Field(
        default_factory=list,
        description="Minimum qualifications (e.g., years of experience)"
    )

    class Config:
        use_enum_values = False



class Screening(BaseModel):
    """Screening evaluation result."""
    screening_id: str = Field(..., description="Unique screening ID")
    candidate_id: str = Field(..., description="Candidate ID")
    matching_score: float = Field(
        ..., ge=0.0, le=100.0,
        description="Overall matching score (0-100)"
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Candidate's key strengths"
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Skill gaps and concerns"
    )
    matched_skills: list[str] = Field(
        default_factory=list,
        description="Skills found in candidate"
    )
    missing_skills: list[str] = Field(
        default_factory=list,
        description="Required skills not found"
    )
    screening_summary: str = Field(
        ...,
        min_length=10,
        description="Concise summary of screening decision"
    )
    concerns: list[str] = Field(
        default_factory=list,
        description="Specific concerns or red flags"
    )
    recommendation: str = Field(
        ...,
        pattern="^(proceed|reject|review)$",
        description="Next action: proceed to assessment, reject, or manual review"
    )

    class Config:
        use_enum_values = False



class AssessmentConfig(BaseModel):
    """Configuration for assessment/interview stage."""
    duration_minutes: int = Field(default=30, description="Interview duration")
    technical_question_count: int = Field(default=8, description="Technical questions")
    hr_question_count: int = Field(default=5, description="HR/soft skill questions")
    difficulty: str = Field(default="adaptive", description="Difficulty level")
    include_mcq: bool = Field(default=True, description="Multiple choice questions?")
    include_typed_questions: bool = Field(default=True, description="Typed answers?")
    include_hr_questions: bool = Field(default=True, description="HR questions?")
    access_duration_days: int = Field(default=3, description="Days to complete")


class Policy(BaseModel):
    """Policies for downstream agents."""
    screening_threshold: float = Field(
        default=70.0,
        ge=0.0, le=100.0,
        description="Minimum score to proceed"
    )
    assessment_pass_threshold: float = Field(
        default=85.0,
        ge=0.0, le=100.0,
        description="Assessment passing score"
    )
    max_assessment_attempts: int = Field(default=1, description="Retry limit")
    allow_resume: bool = Field(default=True, description="Resume during assessment?")
    require_all_questions: bool = Field(default=True, description="All questions required?")


class Versions(BaseModel):
    """Version information for traceability."""
    job_description_version: str = Field(default="v1.0")
    screening_version: str = Field(default="v1.0")
    assessment_rubric_version: str = Field(default="v1.0")


class ScreeningHandoffPayload(BaseModel):
    """Complete structured output for next agent."""
    candidate: Candidate = Field(..., description="Candidate information")
    job: Job = Field(..., description="Job requisition")
    screening: Screening = Field(..., description="Screening evaluation")
    config: AssessmentConfig = Field(..., description="Assessment config")
    policy: Policy = Field(..., description="Policies")
    versions: Versions = Field(..., description="Version information")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When screening was performed"
    )

    class Config:
        use_enum_values = False