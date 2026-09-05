"""Pydantic AI Screening Agent."""

import json
import logging
import uuid
from typing import Optional
from app.services.mongodb_service import db
from datetime import datetime

from pydantic import ValidationError
from pydantic_ai import Agent, ModelRetry, RunContext

from app.agents.models import (
    Candidate,
    CandidateExperience,
    Job,
    Screening,
    ScreeningHandoffPayload,
    AssessmentConfig,
    Policy,
    Versions,
)
from app.agents.prompts import get_system_prompt
from app.agents.tools import skill_matcher, experience_analyzer, red_flag_detector
from app.config import settings
from app.models.schemas import ParsedCV
from app.utils.logger import log_error, log_info

logger = logging.getLogger(__name__)


class ScreeningAgentError(Exception):
    """Raised when agent screening fails."""
    pass


class ScreeningAgent:
    """Main screening agent using Pydantic AI."""

    def __init__(self):
        """Initialize the screening agent."""
        self.agent = self._build_agent()
        self.model_name = settings.LLM_MODEL

    def _build_agent(self) -> Agent:
        """Build the Pydantic AI agent."""
        # Determine model string based on provider
        if settings.LLM_PROVIDER == "anthropic":
            model = f"claude:{settings.LLM_MODEL}"
        elif settings.LLM_PROVIDER == "openai":
            model = f"openai:{settings.LLM_MODEL}"
        elif settings.LLM_PROVIDER == "groq":
            model = f"groq:{settings.LLM_MODEL}"
        elif settings.LLM_PROVIDER == "openai-oss":
            model = f"openai:{settings.LLM_MODEL}"
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

        agent = Agent(
            model=model,
            system_prompt=get_system_prompt(),
            output_type=Screening,
            tools=[
                skill_matcher,
                experience_analyzer,
                red_flag_detector,
            ],
        )

        return agent

    async def screen_candidate(
        self,
        parsed_cv: ParsedCV,
        job: Job,
        candidate_id: Optional[str] = None,
    ) -> ScreeningHandoffPayload:
        """
        Screen a candidate against a job.

        Args:
            parsed_cv: Extracted CV data
            job: Job requisition
            candidate_id: Optional candidate ID (auto-generated if not provided)

        Returns:
            Complete ScreeningHandoffPayload for next agent

        Raises:
            ScreeningAgentError if screening fails
        """
        try:
            # Generate candidate ID if not provided
            if not candidate_id:
                candidate_id = f"CAND-{uuid.uuid4().hex[:8].upper()}"

            # Build candidate object from parsed CV
            candidate = self._build_candidate(parsed_cv, candidate_id)

            # Build screening prompt
            screening_prompt = self._build_screening_prompt(candidate, job)

            log_info(
                "Starting screening",
                candidate_id=candidate_id,
                job_id=job.job_id,
                model=self.model_name,
            )

            # Run agent (with retries for malformed output)
            screening_result = await self._run_screening_with_retry(
                screening_prompt
            )

            # Build complete handoff payload
            payload = ScreeningHandoffPayload(
                candidate=candidate,
                job=job,
                screening=screening_result,
                config=self._build_assessment_config(screening_result.recommendation),
                policy=self._build_policy(screening_result.matching_score),
                versions=self._build_versions(),
            )

            log_info(
                "Screening complete",
                candidate_id=candidate_id,
                score=screening_result.matching_score,
                recommendation=screening_result.recommendation,
            )

            return payload

        except ValidationError as e:
            error_msg = f"Validation error in screening: {str(e)}"
            log_error(error_msg, exception=e)
            raise ScreeningAgentError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during screening: {str(e)}"
            log_error(error_msg, exception=e)
            raise ScreeningAgentError(error_msg) from e
        

    async def _run_screening_with_retry(
            self,
            prompt: str,
            max_retries: int = 2,
        ) -> Screening:
            """
            Run screening with retry logic for malformed output.

            Args:
                prompt: Screening prompt
                max_retries: Max retry attempts

            Returns:
                Screening result

            Raises:
                ScreeningAgentError if all retries fail
            """
            for attempt in range(max_retries + 1):
                try:
                    log_info(
                        f"Screening attempt {attempt + 1}/{max_retries + 1}",
                        attempt=attempt + 1,
                    )

                    # Call agent
                    result = await self.agent.run(prompt)

                    # Handle the result - Pydantic AI returns the output directly
                    # when output_type is specified in Agent init
                    screening_output = result.output if hasattr(result, 'output') else result
                    
                    if isinstance(screening_output, Screening):
                        return screening_output

                    raise ScreeningAgentError(
                        f"Expected Screening, got {type(screening_output)}"
                    )

                except (ValidationError, ValueError) as e:
                    if attempt < max_retries:
                        log_info(
                            f"Screening validation failed, retrying...",
                            attempt=attempt + 1,
                            error=str(e),
                        )
                        continue
                    else:
                        raise ScreeningAgentError(
                            f"Screening failed after {max_retries + 1} attempts: {str(e)}"
                        ) from e

    def _build_candidate(
        self,
        parsed_cv: ParsedCV,
        candidate_id: str,
    ) -> Candidate:
        """Build Candidate object from ParsedCV."""
        # Convert work experiences
        experiences = [
            CandidateExperience(
                company=exp.company,
                role=exp.title,
                duration_years=exp.duration_years,
                responsibilities=[exp.description] if exp.description else [],
            )
            for exp in parsed_cv.work_history
        ]

        # Convert education
        educations = [
            f"{edu.degree} in {edu.field} from {edu.institution}"
            for edu in parsed_cv.education
        ]

        return Candidate(
            candidate_id=candidate_id,
            name=parsed_cv.name,
            email=parsed_cv.email,
            phone=parsed_cv.phone,
            skills=parsed_cv.skills,
            experience=experiences,
            education=educations,
            certifications=[],  # Could extract from parsed_cv if available
        )

    def _build_screening_prompt(self, candidate: Candidate, job: Job) -> str:
        """Build the screening prompt for the agent."""
        return f"""
Please evaluate the following candidate for the position:

## CANDIDATE PROFILE
{json.dumps(candidate.model_dump(), indent=2)}

## JOB REQUISITION
{json.dumps(job.model_dump(), indent=2)}

Provide a comprehensive screening evaluation:

1. **Skill Match**: Compare candidate's skills against required and preferred skills.
2. **Experience**: Evaluate if their experience level matches the seniority requirement.
3. **Strengths**: List 3-5 key strengths relevant to the role.
4. **Gaps**: Identify 3-5 key skill or experience gaps.
5. **Concerns**: Any red flags or ambiguities?
6. **Score**: Provide a matching score (0-100) with clear reasoning.
7. **Recommendation**: Should we proceed to assessment, request a review, or reject?

Be specific, fair, and objective. Explain your reasoning clearly.
"""

    def _build_assessment_config(
        self,
        recommendation: str,
    ) -> AssessmentConfig:
        """Build assessment config based on recommendation."""
        # Adjust config based on recommendation
        if recommendation == "reject":
            return AssessmentConfig(
                duration_minutes=0,
                include_mcq=False,
                include_typed_questions=False,
                include_hr_questions=False,
            )

        return AssessmentConfig(
            duration_minutes=30,
            technical_question_count=8,
            hr_question_count=5,
            difficulty="adaptive",
            include_mcq=True,
            include_typed_questions=True,
            include_hr_questions=True,
            access_duration_days=3,
        )

    def _build_policy(self, score: float) -> Policy:
        """Build policy based on screening score."""
        return Policy(
            screening_threshold=70.0,
            assessment_pass_threshold=85.0,
            max_assessment_attempts=1 if score >= 75 else 2,
            allow_resume=True,
            require_all_questions=True,
        )

    def _build_versions(self) -> Versions:
        """Build version information."""
        return Versions(
            job_description_version="v1.0",
            screening_version=settings.APP_VERSION,
            assessment_rubric_version="v1.0",
        )
    
def save_screening_to_mongo(screening_output):
    collection = db["cv_screenings"]
    
    result = collection.insert_one({
        "candidate_id": screening_output.candidate_id,
        "cv_score": screening_output.cv_score,
        "recommendation": screening_output.recommendation,
        "reasoning": screening_output.reasoning,
        "status": screening_output.status,
        "evaluated_at": screening_output.evaluated_at,
        "created_at": datetime.utcnow()
    })
    
    return str(result.inserted_id) 
    