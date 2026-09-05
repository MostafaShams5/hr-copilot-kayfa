"""Tools available to the screening agent."""

import logging
from typing import Any

from pydantic_ai import RunContext
from pydantic_ai.tools import Tool

logger = logging.getLogger(__name__)


def skill_matcher(
    ctx: RunContext[Any],
    candidate_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
) -> dict[str, Any]:
    """
    Match candidate skills against job requirements.
    
    Returns:
        {
            "matched_required": [skills],
            "matched_preferred": [skills],
            "missing_required": [skills],
            "matched_count": int,
            "required_coverage": float (0-1),
        }
    """
    candidate_skills_lower = [s.lower() for s in candidate_skills]
    
    matched_required = []
    for skill in required_skills:
        if skill.lower() in candidate_skills_lower:
            matched_required.append(skill)
    
    matched_preferred = []
    for skill in preferred_skills:
        if skill.lower() in candidate_skills_lower:
            matched_preferred.append(skill)
    
    missing_required = [
        skill for skill in required_skills
        if skill.lower() not in candidate_skills_lower
    ]
    
    coverage = (
        len(matched_required) / len(required_skills)
        if required_skills
        else 0.0
    )
    
    return {
        "matched_required": matched_required,
        "matched_preferred": matched_preferred,
        "missing_required": missing_required,
        "matched_count": len(matched_required) + len(matched_preferred),
        "required_coverage": round(coverage, 2),
    }


def experience_analyzer(
    ctx: RunContext[Any],
    candidate_years: float,
    required_years: float,
    candidate_seniority: str,
    job_seniority: str,
) -> dict[str, Any]:
    """
    Analyze experience alignment.
    
    Returns:
        {
            "years_delta": float,
            "years_below_requirement": bool,
            "seniority_match": str,
            "experience_score_adjustment": int (-20 to +10),
        }
    """
    years_delta = candidate_years - required_years
    is_below = years_delta < 0
    
    # Seniority mapping for comparison
    seniority_levels = {
        "entry": 0,
        "mid": 1,
        "senior": 2,
        "lead": 3,
    }
    
    candidate_level = seniority_levels.get(candidate_seniority.lower(), 0)
    job_level = seniority_levels.get(job_seniority.lower(), 0)
    
    if candidate_level < job_level:
        seniority_match = "below"
        adjustment = -15
    elif candidate_level > job_level + 1:
        seniority_match = "overqualified"
        adjustment = -5
    else:
        seniority_match = "aligned"
        adjustment = 0
    
    # Adjust for years below requirement
    if is_below:
        adjustment -= min(abs(years_delta) * 5, 10)
    
    return {
        "years_delta": round(years_delta, 1),
        "years_below_requirement": is_below,
        "seniority_match": seniority_match,
        "experience_score_adjustment": adjustment,
    }


def red_flag_detector(
    ctx: RunContext[Any],
    work_history: list[dict[str, Any]],
    experience_gaps: bool = False,
    cv_extraction_confidence: float = 1.0,
) -> dict[str, Any]:
    """
    Detect potential red flags in candidate profile.
    
    Returns:
        {
            "flags": [flag descriptions],
            "severity": "low" | "medium" | "high",
            "score_penalty": int,
        }
    """
    flags = []
    score_penalty = 0
    
    # Check for frequent job changes
    if work_history and len(work_history) >= 4:
        recent_roles = work_history[:4]
        short_stints = [
            exp for exp in recent_roles
            if isinstance(exp.get("duration_years"), (int, float))
            and exp.get("duration_years", 0) < 1
        ]
        if len(short_stints) >= 2:
            flags.append("Job hopper: Multiple roles under 1 year")
            score_penalty -= 10
    
    # Check for gaps
    if experience_gaps:
        flags.append("Unexplained employment gaps")
        score_penalty -= 5
    
    # Check extraction confidence
    if cv_extraction_confidence < 0.5:
        flags.append("Low confidence in CV extraction (may be malformed)")
        score_penalty -= 5
    
    severity = (
        "high" if score_penalty <= -15
        else "medium" if score_penalty <= -5
        else "low"
    )
    
    return {
        "flags": flags,
        "severity": severity,
        "score_penalty": score_penalty,
    }


# Define tools for the agent
tools = [
    Tool(skill_matcher, description="Match candidate skills against job requirements"),
    Tool(experience_analyzer, description="Analyze experience level alignment"),
    Tool(red_flag_detector, description="Detect potential red flags"),
]