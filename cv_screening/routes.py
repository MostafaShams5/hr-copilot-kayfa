"""API routes for CV Screening Agent."""

import logging
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    File,
    Form,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from app.agents.models import ScreeningHandoffPayload, Job as AgentJob
from app.api.dependencies import BearerToken, ScreeningAgentDep
from app.api.errors import (
    FileTooLargeError,
    InvalidFileTypeError,
    InvalidJobRequisitionError,
    MissingFileError,
    ScreeningAgentError,
)
from app.config import settings
from app.models.schemas import CVScreeningOutput, JobRequisition, ParsedCV
from app.tools.cv_parser import CVParser, CVParseError
from app.utils.logger import log_error, log_info

logger = logging.getLogger(__name__)
from app.agents.screening_agent import ScreeningAgent

router = APIRouter(prefix="/cv-screening", tags=["cv-screening"])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def validate_file_upload(file: UploadFile) -> tuple[str, str]:
    """
    Validate uploaded file.

    Args:
        file: Uploaded file

    Returns:
        Tuple of (file_type, temp_file_path)

    Raises:
        MissingFileError: If file is missing
        InvalidFileTypeError: If file type not supported
        FileTooLargeError: If file exceeds size limit
    """
    if not file or not file.filename:
        raise MissingFileError("No CV file provided")

    # Extract file extension
    filename = file.filename.lower()
    if "." not in filename:
        raise InvalidFileTypeError(
            f"File must have extension. Received: {file.filename}"
        )

    file_ext = filename.split(".")[-1]
    if file_ext not in settings.ALLOWED_FILE_TYPES:
        raise InvalidFileTypeError(
            f"File type '.{file_ext}' not supported. Allowed: {', '.join(settings.ALLOWED_FILE_TYPES)}",
            received_type=file_ext,
        )

    # Note: File size validation happens in FastAPI's default handling
    # but we can add explicit check if needed
    return file_ext, filename


async def parse_job_requisition(job_json: str) -> JobRequisition:
    """
    Parse job requisition from JSON string.

    Args:
        job_json: JSON string of job requisition

    Returns:
        Validated JobRequisition

    Raises:
        InvalidJobRequisitionError: If parsing fails
    """
    try:
        import json
        job_dict = json.loads(job_json)
        job = JobRequisition.model_validate(job_dict)
        return job
    except json.JSONDecodeError as e:
        raise InvalidJobRequisitionError(
            f"Invalid JSON in job_requisition: {str(e)}"
        )
    except Exception as e:
        raise InvalidJobRequisitionError(
            f"Invalid job requisition: {str(e)}",
            details={"error": str(e)},
        )


def convert_handoff_to_api_response(
    result: ScreeningHandoffPayload,
    parsed_cv: ParsedCV,
    job: AgentJob,
) -> CVScreeningOutput:
    """
    Convert ScreeningHandoffPayload (internal agent output) to CVScreeningOutput 
    (shared handoff schema consumed by next agents).
    """
    # Determine recommendation based on score and concerns
    is_passing = (result.screening.matching_score >= 70.0 and 
                  len(result.screening.concerns) == 0)
    recommendation = "PROCEED_TO_ASSESSMENT" if is_passing else "REJECT"
    
    return CVScreeningOutput(
        candidate_id=result.candidate.candidate_id,
        cv_score=result.screening.matching_score,
        strengths=result.screening.strengths,
        gaps=result.screening.gaps,
        matched_skills=result.screening.matched_skills,
        missing_skills=result.screening.missing_skills,
        has_fatal_red_flag=len(result.screening.concerns) > 0,
        concerns=result.screening.concerns,
        recommendation=recommendation,
        reasoning=result.screening.screening_summary,
        status="SCREENED",
    )
# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post(
    "/analyze",
    response_model=CVScreeningOutput, 
    status_code=status.HTTP_200_OK,
    summary="Analyze CV against job requisition",
    description="Screen a candidate's CV and provide quantified evaluation",
)
async def analyze_cv(
    token: BearerToken,
    agent: ScreeningAgentDep,
    cv_file: UploadFile = File(..., description="CV file (PDF or DOCX)"),
    job_requisition: str = Form(
        ...,
        description="Job requisition as JSON string",
    ),
    candidate_id: str | None = Form(
        None,
        description="Optional candidate ID from Headhunting Agent",
    ), 
):
    """
    Screen a candidate's CV against a job requisition.
    Results are saved to MongoDB.
    """
    try:
        log_info(
            "CV screening request received",
            candidate_id=candidate_id or "auto-generate",
            has_file=cv_file is not None,
        )

        # 1. Validate file
        file_ext, filename = validate_file_upload(cv_file)

        # 2. Read file content
        file_content = await cv_file.read()
        if not file_content:
            raise MissingFileError("Uploaded file is empty")

        # 3. Save to temporary file for parsing
        import tempfile
        from pathlib import Path
        from datetime import datetime

        with tempfile.NamedTemporaryFile(
            suffix=f".{file_ext}",
            delete=False,
        ) as tmp_file:
            tmp_file.write(file_content)
            temp_path = tmp_file.name

        try:
            # 4. Parse CV
            log_info("Parsing CV", file_type=file_ext)
            parsed_cv = CVParser.parse(temp_path, file_ext)

            # 5. Parse job requisition
            log_info("Parsing job requisition")
            job_req = await parse_job_requisition(job_requisition)

            # Convert JobRequisition to Job (agent model)
            job = AgentJob(
                job_id=job_req.job_id,
                role=job_req.role,
                description=job_req.description or "",
                seniority=job_req.seniority.value if hasattr(job_req.seniority, 'value') else str(job_req.seniority),
                required_skills=job_req.required_skills,
                preferred_skills=job_req.nice_to_have_skills,
                responsibilities=[],
                qualifications=[f"{job_req.min_years_experience}+ years experience"],
            )

            # 6. Run screening agent
            log_info(
                "Starting screening agent",
                job_id=job.job_id,
                model=agent.model_name,
            )
            result = await agent.screen_candidate(
                parsed_cv=parsed_cv,
                job=job,
                candidate_id=candidate_id,
            )

            api_response = convert_handoff_to_api_response(result, parsed_cv, job)

            try:
                from app.services.mongodb_service import db
                
                collection = db["cv_screenings"]
                
                screening_data = {
                    "candidate_id": api_response.candidate_id,
                    "job_id": job.job_id,
                    "cv_score": api_response.cv_score,
                    "recommendation": api_response.recommendation,
                    "strengths": api_response.strengths,
                    "gaps": api_response.gaps,
                    "matched_skills": api_response.matched_skills,
                    "missing_skills": api_response.missing_skills,
                    "has_fatal_red_flag": api_response.has_fatal_red_flag,
                    "concerns": api_response.concerns,
                    "reasoning": api_response.reasoning,
                    "status": api_response.status,
                    "evaluated_at": datetime.utcnow().isoformat(),
                    "created_at": datetime.utcnow(),
                    "parsed_cv": {
                        "name": parsed_cv.name,
                        "email": parsed_cv.email,
                        "phone": parsed_cv.phone,
                        "experience_years": parsed_cv.experience_years,
                        "skills": parsed_cv.skills,
                    }
                }
                
                result_mongo = collection.insert_one(screening_data)
                log_info(
                    "Screening saved to MongoDB",
                    mongo_id=str(result_mongo.inserted_id),
                    candidate_id=api_response.candidate_id,
                )
                
            except Exception as e:
                log_error(
                    f"Failed to save screening to MongoDB: {str(e)}",
                    exception=e
                )
                # Don't fail the request if MongoDB save fails
                # Just log the error
            # ============================================================================

            log_info(
                "Screening completed successfully",
                candidate_id=api_response.candidate_id,
                score=api_response.cv_score,
            )

            return api_response

        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

    except (
        MissingFileError,
        InvalidFileTypeError,
        FileTooLargeError,
        InvalidJobRequisitionError,
    ) as e:
        log_error(f"Validation error: {e.message}", exception=e)
        raise

    except CVParseError as e:
        error_msg = f"Failed to parse CV: {str(e)}"
        log_error(error_msg, exception=e)
        raise ScreeningAgentError(error_msg) from e

    except Exception as e:
        error_msg = f"Unexpected error during screening: {str(e)}"
        log_error(error_msg, exception=e)
        raise ScreeningAgentError(error_msg) from e

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check service health and configuration",
)
async def health_check(token: BearerToken):
    """
    Health check endpoint.

    Returns service status, version, and LLM model info.
    """
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "agent_model": settings.LLM_MODEL,
        "llm_provider": settings.LLM_PROVIDER,
        "environment": settings.ENV,
    }


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Service info",
    description="Get service information",
)
async def service_info(token: BearerToken):
    """
    Get service information.

    Returns basic service details.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "CV Screening Agent - Quantified CV evaluation",
        "endpoints": {
            "health": "/cv-screening/health",
            "analyze": "/cv-screening/analyze",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }