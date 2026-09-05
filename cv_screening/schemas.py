"""Pydantic models for CV Screening Agent."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.models.enums import CandidateIDSource, FlagType, Seniority, SkillProficiency


class SkillMatch(BaseModel):
    """A single skill with proficiency and presence in CV."""

    name: str = Field(..., min_length=1, description="Skill name")
    required: bool = Field(..., description="Is this a required skill for the job?")
    found_in_cv: bool = Field(..., description="Was this skill found in the CV?")
    proficiency_level: Optional[SkillProficiency] = Field(
        None, description="Inferred proficiency level"
    )
    years_experience: Optional[float] = Field(
        None, ge=0, description="Years of experience with this skill"
    )
    evidence: str = Field(
        ...,
        min_length=1,
        description="Evidence from CV or explanation if not found",
    )

    class Config:
        use_enum_values = False


class WorkExperience(BaseModel):
    """A single work experience entry."""

    company: str = Field(..., min_length=1, description="Company name")
    title: str = Field(..., min_length=1, description="Job title")
    start_date: str = Field(..., description="Start date (YYYY-MM or YYYY format)")
    end_date: Optional[str] = Field(
        None, description="End date (YYYY-MM or YYYY format, None = current role)"
    )
    duration_years: float = Field(
        ..., ge=0, description="Duration in years (calculated)"
    )
    description: Optional[str] = Field(
        None, description="Job description/responsibilities"
    )
    is_current: bool = Field(..., description="Is this the current role?")

    @field_validator("duration_years")
    @classmethod
    def validate_duration(cls, v: float) -> float:
        """Ensure duration is reasonable (not exceeding 80 years)."""
        if v > 80:
            raise ValueError("Duration cannot exceed 80 years")
        return v


class Education(BaseModel):
    """A single education entry."""

    institution: str = Field(..., min_length=1, description="Institution name")
    degree: str = Field(
        ..., min_length=1, description="Degree (e.g., Bachelor of Science)"
    )
    field: str = Field(..., min_length=1, description="Field of study")
    graduation_year: Optional[int] = Field(
        None, ge=1950, le=2100, description="Graduation year"
    )
    is_currently_studying: bool = Field(
        False, description="Is candidate still studying?"
    )


class ParsedCV(BaseModel):
    """Extracted and structured CV data."""

    name: str = Field(..., min_length=1, description="Candidate name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Location/city")
    summary: Optional[str] = Field(None, description="Professional summary/objective")
    work_history: List[WorkExperience] = Field(
        default_factory=list, description="List of work experiences"
    )
    education: List[Education] = Field(
        default_factory=list, description="List of education entries"
    )
    skills: List[str] = Field(
        default_factory=list, description="List of skills/technologies"
    )
    total_years_experience: float = Field(
        ..., ge=0, le=80, description="Total years of experience (calculated)"
    )
    raw_text: Optional[str] = Field(
        None, description="Full extracted text for agent context (may be large)"
    )
    extraction_confidence: float = Field(
        default=1.0, ge=0, le=1, description="Confidence score of extraction (0-1)"
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Basic email format validation."""
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v

    class Config:
        use_enum_values = False


class JobRequisition(BaseModel):
    """Upstream context from Headhunting Agent."""

    job_id: str = Field(..., min_length=1, description="Unique job requisition ID")
    role: str = Field(..., min_length=1, description="Job role/title")
    description: Optional[str] = Field(None, description="Full job description")
    required_skills: List[str] = Field(
        ..., description="Required skills (non-negotiable)"
    )
    nice_to_have_skills: List[str] = Field(
        default_factory=list, description="Nice-to-have skills"
    )
    min_years_experience: float = Field(
        default=0.0, ge=0, description="Minimum years of experience required"
    )
    preferred_years_experience: Optional[float] = Field(
        None, ge=0, description="Preferred years of experience"
    )
    seniority: Seniority = Field(..., description="Seniority level required")
    max_salary: Optional[float] = Field(None, ge=0, description="Maximum salary")
    location: Optional[str] = Field(None, description="Job location")
    remote_friendly: bool = Field(False, description="Is the role remote-friendly?")

    @model_validator(mode="after")
    def validate_years_experience(self) -> "JobRequisition":
        """Ensure preferred >= minimum years."""
        if (
            self.preferred_years_experience
            and self.preferred_years_experience < self.min_years_experience
        ):
            raise ValueError(
                "preferred_years_experience cannot be less than min_years_experience"
            )
        return self

    class Config:
        use_enum_values = False


class ScreeningFlag(BaseModel):
    """A concern or insight about the candidate."""

    flag_type: FlagType = Field(..., description="Type of flag")
    message: str = Field(..., min_length=1, description="Human-readable flag message")
    severity: str = Field(
        default="info",
        pattern="^(info|warning|critical)$",
        description="Flag severity level",
    )

    class Config:
        use_enum_values = False


class ScreeningResult(BaseModel):
    """Standard handoff payload: context① + score② + reasoning③."""

    candidate_id: str = Field(..., min_length=1, description="Unique candidate ID")
    candidate_id_source: CandidateIDSource = Field(
        ..., description="Source of candidate ID"
    )
    job_id: str = Field(
        ..., min_length=1, description="Corresponding job requisition ID"
    )
    parsed_cv: ParsedCV = Field(..., description="Parsed and structured CV")
    score: int = Field(..., ge=0, le=100, description="Screening score (0-100)")
    reasoning: str = Field(
        ..., min_length=10, description="Detailed explanation of the score"
    )
    pros: List[str] = Field(
        default_factory=list, description="Strengths/positive aspects"
    )
    cons: List[str] = Field(default_factory=list, description="Weaknesses/concerns")
    skill_matches: List[SkillMatch] = Field(
        ..., description="Detailed skill breakdown"
    )
    flags: List[ScreeningFlag] = Field(
        default_factory=list, description="Flags and concerns"
    )
    screened_at: datetime = Field(
        default_factory=datetime.utcnow, description="Screening timestamp"
    )
    agent_model: str = Field(
        ..., description="LLM model used (e.g., claude-3-5-sonnet-20241022)"
    )
    agent_version: str = Field(default="1.0.0", description="Agent version")

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: int) -> int:
        """Validate score is reasonable."""
        if not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100")
        return v

    @model_validator(mode="after")
    def validate_reasoning_length(self) -> "ScreeningResult":
        """Ensure reasoning is substantive."""
        if len(self.reasoning) < 10:
            raise ValueError("Reasoning must be at least 10 characters")
        return self

    class Config:
        use_enum_values = False


class ScreeningInput(BaseModel):
    """Request payload for /cv-screening/analyze endpoint."""

    job_requisition: JobRequisition = Field(..., description="Job requisition details")
    candidate_id: Optional[str] = Field(
        None, description="Optional candidate ID (if from Headhunting Agent)"
    )

    class Config:
        use_enum_values = False


class BatchScreeningInput(BaseModel):
    """Request for batch screening endpoint."""

    job_requisition: JobRequisition = Field(..., description="Job requisition")
    candidate_ids: Optional[List[str]] = Field(
        None, description="Optional list of candidate IDs"
    )


class BatchScreeningResult(BaseModel):
    """Response for batch screening endpoint."""

    job_id: str = Field(..., min_length=1, description="Job requisition ID")
    results: List[ScreeningResult] = Field(
        default_factory=list, description="Results ranked by score descending"
    )
    total_screened: int = Field(..., ge=0, description="Total candidates screened")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Batch timestamp"
    )

    @model_validator(mode="after")
    def validate_results_sorted(self) -> "BatchScreeningResult":
        """Ensure results are sorted by score descending."""
        if self.results:
            sorted_results = sorted(self.results, key=lambda x: x.score, reverse=True)
            if self.results != sorted_results:
                self.results = sorted_results
        return self

    class Config:
        use_enum_values = False


class HealthCheckResponse(BaseModel):
    """Response for health check endpoint."""

    status: str = Field(..., pattern="^(ok|degraded|error)$")
    version: str = Field(...)
    agent_model: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    error: dict = Field(..., description="Error details")


class ScreeningResultCompactForLLM(BaseModel):
    """Compact JSON format sent to LLM (token-efficient)."""
    cid: str
    jid: str
    s: int
    r: str
    sm: List[dict]
    fl: List[dict]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cid": "cand_001",
                "jid": "job_001",
                "s": 85,
                "r": "Strong Python/FastAPI match. Missing K8s.",
                "sm": [
                    {"n": "Python", "f": True, "p": "expert"},
                    {"n": "Kubernetes", "f": False, "p": None}
                ],
                "fl": [
                    {"t": "missing_required_skill", "m": "Missing Kubernetes"}
                ]
            }
        }
    )


class ScreeningResultForFrontend(BaseModel):
    """Human-readable version for frontend display."""
    candidate_id: str
    job_id: str
    parsed_cv: ParsedCV
    score: int
    reasoning: str
    pros: List[str]
    cons: List[str]
    skill_matches: List[SkillMatch]
    flags: List[ScreeningFlag]
    screened_at: datetime
    agent_model: str
    agent_version: str


class CVScreeningOutput(BaseModel):
    """
    Output from Agent 2 (CV Screening Agent): Quantified CV evaluation.
    
    This is the standardized handoff format consumed by:
    - Agent 3 (Assessment/Interview Agent)
    - Agent 4 (Decision-Maker Agent)
    
    Stored in MongoDB as: CandidatePipelineState.cv_screening_data
    """
    
    # Identification (Required)
    candidate_id: str = Field(
        ...,
        min_length=1,
        description="Unique candidate ID"
    )
    
    # Screening Score & Gate
    cv_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="CV matching score (0-100). Threshold: >= 70% to proceed to assessment"
    )
    
    # Skill & Experience Analysis
    strengths: List[str] = Field(
        default_factory=list,
        description="Validated candidate strengths from CV analysis"
    )
    gaps: List[str] = Field(
        ...,
        description="Candidate gaps/weaknesses to address in assessment or training"
    )
    matched_skills: List[str] = Field(
        default_factory=list,
        description="Required and nice-to-have skills found in CV"
    )
    missing_skills: List[str] = Field(
        default_factory=list,
        description="Critical required skills not found in CV"
    )
    
    # Red Flags & Concerns
    has_fatal_red_flag: bool = Field(
        default=False,
        description="True if candidate has disqualifying factors"
    )
    concerns: List[str] = Field(
        default_factory=list,
        description="List of concerns or ambiguities in CV"
    )
    
    # Decision & Justification
    recommendation: str = Field(
        default="PROCEED_TO_ASSESSMENT",
        description="'PROCEED_TO_ASSESSMENT' if cv_score >= 70% and no fatal red flags, else 'REJECT'"
    )
    reasoning: str = Field(
        ...,
        min_length=20,
        description="LLM justification for the CV score and recommendation"
    )
    
    # Metadata
    status: str = Field(
        default="SCREENED",
        description="Status flag for workflow (always 'SCREENED' for this agent)"
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when screening was performed"
    )
    
    class Config:
        use_enum_values = False