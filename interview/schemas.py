import uuid
from datetime import datetime, timezone
import uuid
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class AnswerItem(BaseModel):
    question_id: str = Field(..., description="ID of the question being answered")
    selected_option: Optional[str] = Field(None, description="Selected option text for MCQs")
    answer_text: Optional[str] = Field("", description="Detailed typed answer or code snippet")


class CandidateSubmission(BaseModel):
    candidate_id: str = Field(..., description="Candidate unique identifier")
    answers: List[AnswerItem] = Field(..., description="List of submitted answers")
    client_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class QuestionModel(BaseModel):
    question_id: str = Field(..., description="Unique Question Identifier (e.g. TECH-CORE-01)")
    question_type: Literal["mcq", "typed"] = Field(..., description="Type of question UI component")
    prompt: str = Field(..., description="Full text prompt for the candidate")
    track: Literal["TECHNICAL", "BEHAVIORAL"] = Field(..., description="Evaluation track")
    seniority_target: Literal["JUNIOR", "MID", "SENIOR", "STAFF_PRINCIPAL"] = Field(default="SENIOR")
    options: Optional[List[str]] = Field(default=None, description="Available options if MCQ")
    ideal_rubric: Optional[str] = Field(default=None, description="Internal evaluation ground truth")
    required_keywords: List[str] = Field(default_factory=list)
    weight: float = Field(default=1.0, ge=0.1, le=5.0)


class JobContextModel(BaseModel):
    job_id: str = Field(..., description="Job opening identifier")
    title: str = Field(default="Senior AI Solutions Architect")
    seniority_level: Literal["JUNIOR", "MID", "SENIOR", "STAFF_PRINCIPAL"] = Field(default="SENIOR")
    required_skills: List[str] = Field(
        default_factory=lambda: ["Python", "FastAPI", "Redis", "PostgreSQL", "Distributed Systems"]
    )
    domain: str = Field(default="Cloud Infrastructure & AI Engineering")
    job_description: Optional[str] = Field(default="", description="Detailed job description and responsibilities")
    candidate_cv_summary: Optional[str] = Field(default="", description="Candidate background or CV summary for personalized assessment")


class CVScreeningOutput(BaseModel):
    """Exact schema contract received from Agent 2 (CV Screening Agent)."""
    candidate_id: str = Field(..., description="Unique candidate ID from Headhunting Agent")
    cv_score: float = Field(..., ge=0.0, le=100.0, description="CV matching score (0-100). Threshold: >= 70%")
    strengths: List[str] = Field(default_factory=list, description="Validated candidate strengths from CV analysis")
    gaps: List[str] = Field(default_factory=list, description="Candidate gaps/weaknesses to address in assessment")
    matched_skills: List[str] = Field(default_factory=list, description="Required and nice-to-have skills found in CV")
    missing_skills: List[str] = Field(default_factory=list, description="Critical required skills not found in CV")
    has_fatal_red_flag: bool = Field(default=False, description="True if candidate has disqualifying factors")
    concerns: List[str] = Field(default_factory=list, description="List of concerns or ambiguities in CV")
    recommendation: str = Field(default="PROCEED_TO_ASSESSMENT", description="'PROCEED_TO_ASSESSMENT' or 'REJECT'")
    reasoning: str = Field(..., min_length=20, description="LLM justification for the CV score and recommendation")
    status: str = Field(default="SCREENED", description="Status flag for workflow")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssessmentInitRequest(BaseModel):
    """
    Ingestion Adapter: Ingests structured CVScreeningOutput from Agent 2 (DocuAnalyze / cv_screening).
    """
    candidate_id: str = Field(..., description="Unique Candidate identifier")
    job_id: str = Field(default="JOB-SENIOR-ARCH-01", description="Job opening identifier")
    candidate_name: Optional[str] = Field(default="Candidate")
    candidate_email: Optional[str] = Field(default="candidate@example.com")
    job_context: Optional[JobContextModel] = None
    cv_screening_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured CV analysis payload matching CVScreeningOutput from Agent 2"
    )

    def get_parsed_skills(self) -> List[str]:
        """Extracts matched skills from CVScreeningOutput."""
        if not self.cv_screening_data:
            return []
        return (
            self.cv_screening_data.get("matched_skills") or
            self.cv_screening_data.get("verified_skills") or
            self.cv_screening_data.get("skills") or
            []
        )

    def get_screening_score(self) -> float:
        """Extracts cv_score from CVScreeningOutput."""
        if not self.cv_screening_data:
            return 75.0
        val = (
            self.cv_screening_data.get("cv_score") or
            self.cv_screening_data.get("score") or
            self.cv_screening_data.get("match_score") or
            75.0
        )
        try:
            return float(val)
        except Exception:
            return 75.0

    def get_identified_gaps(self) -> List[str]:
        """Extracts candidate gaps and missing skills identified by Agent 2 for assessment probe generation."""
        if not self.cv_screening_data:
            return []
        gaps = self.cv_screening_data.get("gaps") or []
        missing = self.cv_screening_data.get("missing_skills") or []
        combined = list(set(gaps + missing))
        return combined if combined else (self.cv_screening_data.get("technical_gaps") or [])

    def get_concerns(self) -> List[str]:
        """Extracts concerns and red flags from CVScreeningOutput."""
        if not self.cv_screening_data:
            return []
        return self.cv_screening_data.get("concerns") or []


class SubScoreBreakdown(BaseModel):
    dimension: str
    score: float = Field(ge=0.0, le=100.0)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    feedback: Optional[str] = None


class InterviewOutput(BaseModel):
    """Output from Agent 3 (Assessment / Interview Agent) consumed by Agent 4 (Decision-Maker Agent)."""
    candidate_id: str
    assessment_id: Optional[str] = None
    candidate_name: Optional[str] = None
    assessment_token: Optional[str] = None

    # Dual-Track & Composite Scores
    technical_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Technical assessment score (0-100)")
    hr_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Behavioral / HR assessment score (0-100)")
    interview_score: float = Field(..., ge=0.0, le=100.0, description="Weighted total score: (technical * 0.70) + (hr * 0.30)")

    # Gate & Assessment Outcomes
    gate_status: str = Field(default="PASSED", description="'PASSED' or 'REJECTED' based on >= 70% threshold on both tracks")
    anti_cheat_passed: bool = Field(default=True, description="Proctoring & zero-tolerance anti-cheat pass flag")
    strengths: List[str] = Field(default_factory=list, description="Validated technical and behavioral strengths")
    remaining_gaps: List[str] = Field(default_factory=list, description="Identified technical/competency gaps")
    resolved_gaps: List[str] = Field(default_factory=list, description="Gaps from CVScreeningOutput proven resolved in assessment")
    behavioral_red_flags: List[str] = Field(default_factory=list, description="Critical behavioral or leadership red flags")
    sub_scores: List[SubScoreBreakdown] = Field(default_factory=list, description="Rubric competency category breakdown")

    # Reasoning, Probing & Confidence
    evaluation_confidence: float = Field(default=0.90, ge=0.0, le=1.0, description="Model confidence in grading (0.0 - 1.0)")
    reasoning: str = Field(..., min_length=20, description="Executive justification synthesized across technical and HR tracks")
    probing_questions_for_manager: List[str] = Field(default_factory=list, description="Recommended 1-on-1 questions for the Hiring Manager")

    # Artifacts & Timestamp
    excel_report_name: Optional[str] = Field(default=None, description="Persisted Excel dossier filename in MongoDB")
    status: str = Field(default="ASSESSED", description="Status flag for workflow")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("interview_score")
    @classmethod
    def validate_composite(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError("Score must be bounded between 0 and 100")
        return v


class InterviewAgentState(BaseModel):
    candidate_id: str
    candidate_name: str = "Candidate"
    candidate_email: str = "candidate@example.com"
    job_id: str
    job_context: JobContextModel = Field(default_factory=JobContextModel)
    assessment_id: str = Field(default_factory=lambda: f"ASM-{uuid.uuid4().hex[:8].upper()}")
    cv_data: Dict[str, Any] = Field(default_factory=dict)
    questions: List[QuestionModel] = Field(default_factory=list)
    answers: List[AnswerItem] = Field(default_factory=list)
    technical_token: Optional[str] = None
    hr_token: Optional[str] = None
    output: Optional[InterviewOutput] = None
    created_at: int = Field(default_factory=lambda: int(uuid.uuid1().time))
    metadata: Dict[str, Any] = Field(default_factory=dict)

