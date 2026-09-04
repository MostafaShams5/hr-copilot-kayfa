import json
import uuid
import asyncio # Make sure this is imported at the top of agents.py
from pydantic_ai import Agent
from .models import JobInput, CandidateCriteria, Candidate, CandidateEvaluation, RankedCandidate, OutreachMessage, EvalList, OutreachBatch
from .config import groq_model

# 1. Job Extractor Agent (for free-text prompts)
job_extractor = Agent(
    model=groq_model,
    output_type=JobInput,
    system_prompt=(
        "You extract structured job requirements from a recruiter's raw text prompt. "
        "Map the user's text to the JobInput schema. "
        "If the user doesn't specify a country, default to 'Egypt'. "
        "If they don't provide an application URL, use 'https://kayfa.academy/careers/apply'. "
        "If they don't specify min_experience_years, default to 2. "
        "Infer the must_have_skills and nice_to_have_skills from the text. "
        "For the job_id, just put 'placeholder' as it will be overwritten."
    )
)

async def run_job_extractor(user_prompt: str) -> JobInput:
    result = await job_extractor.run(user_prompt)
    job = result.output
    # Force a unique job_id for database tracking
    job.job_id = f"kayfa-hire-{str(uuid.uuid4())[:8]}"
    return job

# 2. Job Analysis Agent
job_analyst = Agent(
    model = groq_model,
    output_type=CandidateCriteria,
    system_prompt=(
        "You are a senior technical recruiter. Given a job title, description, "
        "requirements and company context, produce a precise candidate search "
        "criteria used to query LinkedIn. Always include country, role titles, "
        "core skills, industries and education keywords. Be conservative with "
        "experience range so we don't miss borderline matches."
    ),
)

async def run_job_analyst(job : JobInput) -> CandidateCriteria:
    user_prompt = (
        f"JOB TITLE: {job.title}\n"
        f"DESCRIPTION:\n{job.description}\n\n"
        f"REQUIREMENTS:\n- " + "\n- ".join(job.requirements) + "\n\n"
        f"COMPANY: {job.company_context}\n"
        f"TARGET COUNTRY: {job.country}\n"
        f"MIN EXPERIENCE (years): {job.min_experience_years}\n"
        f"MUST-HAVE SKILLS: {', '.join(job.must_have_skills)}\n"
        f"NICE-TO-HAVE: {', '.join(job.nice_to_have_skills)}\n"
        f"INDUSTRY: {job.industry or 'any'}\n"
        f"EDUCATION: {job.education_level or 'any'}\n"
    )
    result = await job_analyst.run(user_prompt=user_prompt)
    crit = result.output
    crit.min_experience_years = job.min_experience_years
    # Limit to 5 results to avoid Groq Token Limits
    crit.max_results = 7
    return crit

# 3. Candidate Evaluator Agent
candidate_evaluator = Agent(
    model=groq_model,
    output_type=EvalList,
    retries=3,
    system_prompt=(
        "You evaluate LinkedIn candidates against a job spec. "
        "You MUST return a JSON object containing an 'evaluations' list. "
        "Each object in the list MUST have EXACTLY these keys: "
        "'profile_url', 'full_name', 'match_score', 'matched_skills', 'missing_skills', "
        "'skill_assessment', 'reasons', 'concerns', 'recommended'. "
        "1. matched_skills: List skills from the candidate that match the job requirements. "
        "2. missing_skills: List required/nice-to-have skills the candidate lacks. "
        "3. skill_assessment: Provide a brief rating (e.g., Strong, Intermediate) and evaluation of their skills. "
        "4. reasons: Provide concrete bullet points explaining exactly why you gave the match_score (reference experience, skills, industry). "
        "5. concerns: Note any gaps or location mismatch. "
        "Be strict: recommend only profiles with score>=70."
    ),
)

async def run_evaluator(job: JobInput, cands: list[Candidate]) -> list[CandidateEvaluation]:
    if not cands:
        return []
        
    all_evals = []
    for cand in cands:
        print(f"[Evaluator] Evaluating {cand.full_name}...")
        
        # FIX 1: Truncate the summary to 8000 characters to avoid 413 Request Entity Too Large
        if cand.summary and len(cand.summary) > 8000:
            cand.summary = cand.summary[:8000]
            
        payload = {
            "job": job.model_dump(mode="json"),
            "candidates": [cand.model_dump(mode="json")],
        }
        try:
            res = await candidate_evaluator.run(json.dumps(payload, ensure_ascii=False))
            all_evals.extend(res.output.evaluations)
        except Exception as e:
            print(f"[Evaluator] Failed to evaluate {cand.full_name}: {e}")
            
        # FIX 2: Add a 2-second delay to respect the Groq Tokens Per Minute (TPM) limit
        await asyncio.sleep(2)
        
    return all_evals

# 4. Outreach Generator Agent
outreach_generator = Agent(
    model=groq_model,
    output_type=OutreachBatch,
    system_prompt=(
        "You write personalized LinkedIn outreach messages in English. "
        "You MUST return a JSON object containing a 'messages' list. "
        "Each object in the list MUST have EXACTLY these keys: "
        "'candidate_url', 'full_name', 'subject', 'body'. "
        "Do NOT use any other keys like 'message'. "
        "For each candidate: greet them by first name, mention their current role and one concrete reason they match "
        "the job, briefly introduce the company (Kayfa Academy), share the job "
        "title and application URL, and end with a soft CTA. Keep body under "
        "150 words, professional but warm. Do NOT invent skills the candidate "
        "doesn't have. Use the provided reasons verbatim where possible."
    ),
)

async def run_outreach(job: JobInput, ranked: list[RankedCandidate]) -> list[OutreachMessage]:
    if not ranked:
        return []
    payload = {
        "company": job.company_context,
        "job_title": job.title,
        "application_url": str(job.application_url),
        "candidates": [r.model_dump(mode="json") for r in ranked],
    }
    res = await outreach_generator.run(json.dumps(payload, ensure_ascii=False))
    return res.output.messages