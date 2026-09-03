from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class DecisionRecommendation(str, Enum):
    APPROVE = "APPROVE"
    ESCALATE = "ESCALATE"
    REJECT = "REJECT"


# ==========================================
# Agent 1: Headhunting Agent (Developer 1)
# ==========================================

class CandidateBase(BaseModel):
    """Shared candidate data used across multiple agents.
    This exactly matches the fields stored in MongoDB by persistence.py."""
    
    # Identification & Raw Data (For Downstream Agents)
    candidate_id: str = Field(..., description="The LinkedIn profile URL acting as the unique ID.")
    first_name: str = Field(..., description="First name of the candidate.")
    last_name: str = Field(..., description="Last name of the candidate.")
    email: str = Field("N/A (LinkedIn Sourced)", description="Email if available, otherwise N/A.")
    resume_text: str = Field("", description="The raw scraped LinkedIn profile text used for screening.")
    
    # Enriched Evaluation Data (Matches DB keys exactly)
    profile_url: str = Field(..., description="The URL of the candidate's LinkedIn profile.")
    full_name: str = Field(..., description="The full name of the candidate.")
    match_score: float = Field(..., ge=0.0, le=100.0, description="A score from 0 to 100 representing how well the candidate matches the job.")
    matched_skills: List[str] = Field(default_factory=list, description="List of must-have and nice-to-have skills the candidate possesses.")
    missing_skills: List[str] = Field(default_factory=list, description="List of required or preferred skills missing from the candidate's profile.")
    skill_assessment: str = Field("", description="A brief rating and evaluation of the candidate's skills quality and relevance.")
    reasons: List[str] = Field(default_factory=list, description="Detailed reasoning explaining exactly why the match_score was given.")
    concerns: List[str] = Field(default_factory=list, description="List of potential concerns or gaps in the candidate's profile.")
    recommended: bool = Field(False, description="Boolean indicating if the agent recommends this candidate for outreach.")
    rank: Optional[int] = Field(None, description="The numerical rank of the candidate compared to others.")


class OutreachMessageBase(BaseModel):
    """Standardized outreach message data.
    This exactly matches the fields stored in MongoDB by persistence.py."""
    candidate_url: str = Field(..., description="The URL of the candidate's profile being messaged.")
    full_name: str = Field(..., description="The full name of the candidate to address the message to.")
    subject: str = Field(..., description="The subject line of the outreach message.")
    body: str = Field(..., description="The main content/body of the personalized outreach message.")
    tone: str = Field("professional-warm", description="The desired tone of the message (e.g., professional, warm).")


class HeadhuntingOutput(BaseModel):
    """Output from Agent 1: A sourced candidate ready for screening."""
    job_id: Optional[str] = Field(None, description="The job ID this candidate was sourced for.")
    candidate: CandidateBase = Field(..., description="The sourced candidate profile and AI evaluation data.")
    source_platform: str = Field("LinkedIn", description="e.g., LinkedIn, Internal DB")
    match_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the match, scaled from 0.0 to 1.0 (match_score / 100).")
    sourced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when the candidate was sourced.")
    outreach_message: Optional[OutreachMessageBase] = Field(None, description="The drafted outreach message for this candidate, if generated.")


# ==========================================
# Agent 2: CV Screening Agent (NEW SIMPLIFIED)
# ==========================================

class CVScreeningOutput(BaseModel):
    """Output from CV Screening Agent - Updated for simplified version"""
    
    # Identification
    candidate_id: str = Field(..., description="Unique candidate ID")
    job_id: str = Field(default="JOB-UNKNOWN", description="Job ID")
    
    # Screening Score
    cv_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="CV matching score (0-100). Threshold: >= 70% to proceed"
    )
    
    # Analysis Results
    strengths: List[str] = Field(
        default_factory=list,
        description="Candidate strengths from CV"
    )
    gaps: List[str] = Field(
        default_factory=list,
        description="Candidate gaps/weaknesses"
    )
    matched_skills: List[str] = Field(
        default_factory=list,
        description="Skills found in CV"
    )
    missing_skills: List[str] = Field(
        default_factory=list,
        description="Required skills missing from CV"
    )
    
    # Red Flags
    has_fatal_red_flag: bool = Field(
        default=False,
        description="True if candidate has disqualifying factors"
    )
    concerns: List[str] = Field(
        default_factory=list,
        description="Concerns or ambiguities"
    )
    
    # Decision
    recommendation: str = Field(
        default="PROCEED",
        description="PROCEED or REJECT"
    )
    reasoning: str = Field(
        default="",
        description="LLM justification"
    )
    
    # Metadata
    status: str = Field(
        default="SCREENED",
        description="Status (always SCREENED for this agent)"
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp"
    )
    mongo_id: Optional[str] = Field(
        None,
        description="MongoDB document ID"
    )

# ==========================================
# Agent 3: Assessment / Interview Agent (Developer 3)
# ==========================================

class InterviewOutput(BaseModel):
    """Output from Agent 3 (Assessment / Interview Agent) consumed by Agent 4 (Decision-Maker Agent)."""
    candidate_id: str
    
    # Dual-Track & Composite Scores
    technical_score: float = Field(..., ge=0.0, le=100.0, description="Technical assessment score (0-100)")
    hr_score: float = Field(..., ge=0.0, le=100.0, description="Behavioral / HR assessment score (0-100)")
    interview_score: float = Field(..., ge=0.0, le=100.0, description="Weighted total score: (technical * 0.70) + (hr * 0.30)")
    
    # Gate & Assessment Outcomes
    gate_status: str = Field(..., description="'PASSED' or 'REJECTED' based on >= 70% threshold on both tracks")
    strengths: List[str] = Field(default_factory=list, description="Validated technical and behavioral strengths")
    remaining_gaps: List[str] = Field(default_factory=list, description="Identified technical/competency gaps")
    behavioral_red_flags: List[str] = Field(default_factory=list, description="Critical behavioral or leadership red flags")
    
    # Reasoning, Probing & Confidence
    evaluation_confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence in grading (0.0 - 1.0)")
    reasoning: str = Field(..., min_length=20, description="Executive justification synthesized across technical and HR tracks")
    probing_questions_for_manager: List[str] = Field(default_factory=list, description="Recommended 1-on-1 questions for the Hiring Manager")
    
    # Artifacts & Timestamp
    excel_report_name: Optional[str] = Field(default=None, description="Persisted Excel dossier filename in MongoDB")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==========================================
# Agent 4: Decision-Maker Agent (Developer 4)
# ==========================================

class DecisionOutput(BaseModel):
    """Output from Agent 4: Final deterministic mathematical recommendation."""
    candidate_id: str
    base_score: float = Field(..., ge=0.0, le=100.0, description="Upstream composite score")
    final_score: float = Field(..., ge=0.0, le=100.0, description="Vector-adjusted final score")
    recommendation: DecisionRecommendation = Field(..., description="APPROVE, ESCALATE, or REJECT")
    veto_reason: Optional[str] = Field(default=None, description="Populated if a hard mathematical veto occurred")
    ai_confidence_penalty_applied: bool = Field(default=False)
    probing_questions: str = Field(..., description="Questions aggregated for the human manager")
    excel_report_name: Optional[str] = Field(default=None, description="Reference to the generated dossier")
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==========================================
# Master State Document
# ==========================================

class CandidatePipelineState(BaseModel):
    """
    The master document stored in MongoDB. 
    It updates as the candidate moves through each agent.
    """
    candidate_id: str
    job_id: str
    
    # Handoff Payloads populated sequentially
    headhunting_data: Optional[HeadhuntingOutput] = None
    cv_screening_data: Optional[CVScreeningOutput] = None
    interview_data: Optional[InterviewOutput] = None
    final_decision_data: Optional[DecisionOutput] = None
    
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
