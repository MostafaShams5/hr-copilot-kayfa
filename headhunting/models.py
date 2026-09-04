from dataclasses import dataclass, field
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl
from .config import COMPANY_ABOUT

class JobInput(BaseModel):
    job_id: str = Field(description="Unique identifier for the job posting.")
    title: str = Field(description="The official title of the job position.")
    description: str = Field(description="Detailed text describing the job role, responsibilities, and expectations.")
    requirements: list[str] = Field(description="List of mandatory requirements for the job (e.g., years of experience, certifications).")
    company_context: str = Field(default=COMPANY_ABOUT, description="Background information about the hiring company.")
    application_url: HttpUrl = Field(description="URL where candidates can apply or submit the hiring form.")
    country: str = Field(description="The target country where the candidate should be located.")
    min_experience_years: int = Field(default=2, description="Minimum number of years of experience required.")
    max_experience_years: Optional[int] = Field(default=None, description="Maximum number of years of experience allowed (optional).")
    must_have_skills: list[str] = Field(default_factory=list, description="List of skills that are strictly required for the job.")
    nice_to_have_skills: list[str] = Field(default_factory=list, description="List of skills that are preferred but not strictly mandatory.")
    industry: Optional[str] = Field(default=None, description="The specific industry the job belongs to (e.g., Tech, E-learning).")
    education_level: Optional[str] = Field(default=None, description="The minimum required education level (e.g., BSc Computer Science).")

class CandidateCriteria(BaseModel):
    keywords: list[str] = Field(description="General search keywords to use when looking for candidates.")
    titles: list[str] = Field(description="Job titles to search for (e.g., Senior Engineer, Product Manager).")
    locations: list[str] = Field(description="Geographic locations to target in the search.")
    companies: list[str] = Field(description="Target companies where candidates might currently work or have worked.")
    skills: list[str] = Field(description="Specific skills to look for in candidates.")
    industries: list[str] = Field(description="Industries the candidate should have experience in.")
    education_keywords: list[str] = Field(description="Keywords related to education, degrees, or universities.")
    min_experience_years: int = Field(description="Minimum years of experience to filter by.")
    max_results: int = Field(default=30, description="Maximum number of candidate profiles to retrieve.")

class Candidate(BaseModel):
    profile_url: str = Field(description="The URL of the candidate's LinkedIn profile.")
    full_name: str = Field(description="The full name of the candidate.")
    headline: str = Field(default="", description="The candidate's LinkedIn headline.")
    location: str = Field(default="", description="The candidate's specific city or region.")
    country: str = Field(default="", description="The candidate's country of residence.")
    summary: str = Field(default="", description="A brief summary of the candidate's background.")
    current_role: Optional[str] = Field(default=None, description="The candidate's current job title.")
    current_company: Optional[str] = Field(default=None, description="The candidate's current employer.")
    experience_years: Optional[int] = Field(default=None, description="Total years of professional experience the candidate has.")
    skills: list[str] = Field(default_factory=list, description="List of skills listed on the candidate's profile.")
    previous_roles: list[str] = Field(default_factory=list, description="List of previous job titles held by the candidate.")
    education: list[str] = Field(default_factory=list, description="List of educational qualifications or institutions attended.")
    industries: list[str] = Field(default_factory=list, description="Industries the candidate has worked in.")

class CandidateEvaluation(BaseModel):
    profile_url: str = Field(description="The URL of the evaluated candidate's profile.")
    full_name: str = Field(description="The full name of the evaluated candidate.")
    match_score: float = Field(ge=0, le=100, description="A score from 0 to 100 representing how well the candidate matches the job.")
    matched_skills: list[str] = Field(description="List of must-have and nice-to-have skills the candidate possesses.")
    missing_skills: list[str] = Field(description="List of required or preferred skills missing from the candidate's profile.")
    skill_assessment: str = Field(description="A brief rating and evaluation of the candidate's skills quality and relevance.")
    reasons: list[str] = Field(description="Detailed reasoning explaining exactly why this match_score was given.")
    concerns: list[str] = Field(description="List of potential concerns or gaps in the candidate's profile.")
    recommended: bool = Field(description="Boolean indicating if the agent recommends this candidate for outreach.")

class RankedCandidate(CandidateEvaluation):
    rank: int = Field(description="The numerical rank of the candidate based on their match score compared to others.")

class OutreachMessage(BaseModel):
    candidate_url: str = Field(description="The URL of the candidate's profile being messaged.")
    full_name: str = Field(description="The full name of the candidate to address the message to.")
    subject: str = Field(description="The subject line of the outreach message.")
    body: str = Field(description="The main content/body of the personalized outreach message.")
    tone: str = Field(default="professional-warm", description="The desired tone of the message (e.g., professional, warm).")

class EvalList(BaseModel):
    evaluations: list[CandidateEvaluation]

class OutreachBatch(BaseModel):
    messages: list[OutreachMessage]

@dataclass
class RecruitingState:
    job: JobInput
    criteria: Optional[CandidateCriteria] = None
    raw_candidates: list[Candidate] = field(default_factory=list)
    filtered_candidates: list[Candidate] = field(default_factory=list)
    evaluations: list[CandidateEvaluation] = field(default_factory=list)
    ranked: list[RankedCandidate] = field(default_factory=list)
    top_selected: list[RankedCandidate] = field(default_factory=list)
    outreach_messages: list[OutreachMessage] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    auto_mode: bool = False
    skip_outreach: bool = False  