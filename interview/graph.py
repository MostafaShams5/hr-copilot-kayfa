import logging
from typing import Dict, Any, List
from .schemas import (
    InterviewAgentState,
    QuestionModel,
    JobContextModel
)
from .security import generate_assessment_tokens
from .services import LLMService, EmailService
from .database import db

logger = logging.getLogger("InterviewGraph")


import os
import re
import json

def synthesize_questions_with_groq(state: InterviewAgentState) -> List[QuestionModel]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return []

    ctx = state.job_context
    candidate_name = state.candidate_name or "Candidate"
    skills_str = ", ".join(ctx.required_skills) if ctx.required_skills else "Software Engineering"
    jd_str = getattr(ctx, "job_description", "") or f"High-scale engineering role for {ctx.title}"
    cv_str = getattr(ctx, "candidate_cv_summary", "") or "Demonstrated backend and systems background"

    prompt = f"""
You are a Staff Technical Assessment Designer at Kayfa Academy.
Generate a custom, high-signal technical and behavioral interview for:
Candidate Name: {candidate_name}
Target Role: {ctx.title}
Seniority Tier: {ctx.seniority_level}
Domain: {ctx.domain}
Required Skills: {skills_str}
Job Description Context: {jd_str}
Candidate Background: {cv_str}

Create exactly 4 tailored questions:
1. Technical MCQ: Hard architectural or distributed systems trade-off for {ctx.title}. 4 distinct options, exactly ONE correct answer.
2. Technical Open-Ended: In-depth design scenario question detailing architectural strategy, rollback, and data consistency.
3. Diagnostic MCQ: Real-world latency, debugging, or query optimization problem for {skills_str}. 4 distinct options, exactly ONE correct answer.
4. Behavioral Scenario: Conflict resolution, Sev-1 incident leadership, or stakeholder prioritization calibrated to {ctx.seniority_level}.

Return ONLY a valid JSON array of 4 objects matching this exact structure:
[
  {{
    "question_id": "TECH-CORE-01",
    "question_type": "mcq",
    "prompt": "...",
    "track": "TECHNICAL",
    "seniority_target": "{ctx.seniority_level}",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "ideal_rubric": "Explanation of correct choice",
    "required_keywords": ["keyword1", "keyword2"],
    "weight": 1.5
  }},
  {{
    "question_id": "TECH-CORE-02",
    "question_type": "typed",
    "prompt": "...",
    "track": "TECHNICAL",
    "seniority_target": "{ctx.seniority_level}",
    "options": null,
    "ideal_rubric": "Expected key design trade-offs",
    "required_keywords": ["keyword1", "keyword2"],
    "weight": 2.0
  }},
  {{
    "question_id": "TECH-DIAG-03",
    "question_type": "mcq",
    "prompt": "...",
    "track": "TECHNICAL",
    "seniority_target": "{ctx.seniority_level}",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "ideal_rubric": "Diagnostic rationale",
    "required_keywords": ["keyword1", "keyword2"],
    "weight": 1.0
  }},
  {{
    "question_id": "BEHAV-LEAD-04",
    "question_type": "typed",
    "prompt": "...",
    "track": "BEHAVIORAL",
    "seniority_target": "{ctx.seniority_level}",
    "options": null,
    "ideal_rubric": "Ownership, communication, and resolution approach",
    "required_keywords": ["keyword1", "keyword2"],
    "weight": 1.5
  }}
]
"""
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a professional technical interviewer. Output ONLY a valid JSON array."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        content = resp.choices[0].message.content or ""
        json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
        if json_match:
            raw_list = json.loads(json_match.group())
            return [QuestionModel(**q) for q in raw_list]
    except Exception as e:
        logger.warning(f"Groq question synthesis failed, falling back to calibrated template: {e}")
    return []


def question_synthesis_node(state: InterviewAgentState) -> InterviewAgentState:
    """
    Node 1: Synthesizes technical and behavioral questions tuned dynamically
    to the Job Role, Seniority Level (Junior/Mid/Senior/Staff), and JD Skill Requirements.
    Uses Groq LLM with deterministic rubric fallback.
    """
    ctx: JobContextModel = state.job_context
    seniority = ctx.seniority_level
    title = ctx.title

    logger.info(f"Synthesizing {seniority} level questions for role: '{title}' (Candidate: {state.candidate_name})")

    # 1. Try dynamic Groq LLM synthesis
    groq_questions = synthesize_questions_with_groq(state)
    if groq_questions and len(groq_questions) >= 3:
        state.questions = groq_questions
        return state

    questions: List[QuestionModel] = []

    # 2. Deterministic Template Fallback
    if seniority in ["SENIOR", "STAFF_PRINCIPAL"]:
        questions.append(
            QuestionModel(
                question_id="TECH-CORE-01",
                question_type="mcq",
                prompt=f"For a high-throughput {title} service, which mechanism prevents double-spending or duplicate writes across horizontally scaled instances without creating distributed database deadlocks?",
                track="TECHNICAL",
                seniority_target=seniority,
                options=[
                    "Implementing a Redis-based distributed lock with TTL leases (Redlock algorithm)",
                    "Relying strictly on synchronous HTTP retries with exponential backoff",
                    "Increasing the relational database connection pool size arbitrarily",
                    "Disabling read isolation on the primary database node"
                ],
                ideal_rubric="Selects Redlock / Redis distributed locking with TTL lease ownership.",
                required_keywords=["redis", "redlock", "distributed lock", "ttl"],
                weight=1.5
            )
        )
        questions.append(
            QuestionModel(
                question_id="TECH-CORE-02",
                question_type="typed",
                prompt=f"Design a zero-downtime database schema migration strategy for high-throughput Postgres tables serving active Redis caches. Detail your column migration phases, cache invalidation protocols, and how you handle rollback safety under live load.",
                track="TECHNICAL",
                seniority_target=seniority,
                ideal_rubric="Articulates expand/contract pattern, backward-compatible schemas, optimistic locking (OCC), and asynchronous cache invalidation.",
                required_keywords=["expand", "contract", "occ", "invalidation", "rollback"],
                weight=2.0
            )
        )
        questions.append(
            QuestionModel(
                question_id="TECH-CORE-03",
                question_type="mcq",
                prompt="When an analytical SQL query experiences severe latency spikes under peak concurrency, what is the most definitive first diagnostic step?",
                track="TECHNICAL",
                seniority_target=seniority,
                options=[
                    "Running EXPLAIN (ANALYZE, BUFFERS) to inspect sequential scans, buffer hits, and join algorithms",
                    "Adding composite B-Tree indexes on every foreign key column blindly",
                    "Restarting the database engine to flush OS page caches",
                    "Switching the database storage engine to MyISAM"
                ],
                ideal_rubric="Selects EXPLAIN (ANALYZE, BUFFERS).",
                required_keywords=["explain", "analyze", "buffers"],
                weight=1.0
            )
        )
    else:
        # Junior / Mid Level Track
        questions.append(
            QuestionModel(
                question_id="TECH-CORE-01",
                question_type="mcq",
                prompt=f"When building RESTful APIs in {ctx.required_skills[0] if ctx.required_skills else 'FastAPI'}, what is the most appropriate way to ensure database connection reuse across concurrent requests?",
                track="TECHNICAL",
                seniority_target=seniority,
                options=[
                    "Configuring an asynchronous Connection Pool (e.g. SQLAlchemy AsyncSession pool)",
                    "Opening a brand new database connection on every incoming HTTP request and closing it",
                    "Using a single global blocking connection shared by all threads",
                    "Disabling timeouts on all outgoing sockets"
                ],
                ideal_rubric="Selects Asynchronous Connection Pooling.",
                weight=1.0
            )
        )
        questions.append(
            QuestionModel(
                question_id="TECH-CORE-02",
                question_type="typed",
                prompt=f"Explain how you implement structured logging, error handling middleware, and input validation in your backend applications.",
                track="TECHNICAL",
                seniority_target=seniority,
                ideal_rubric="Mentions Pydantic validation schemas, centralized HTTP exception handlers, and correlation IDs.",
                weight=1.5
            )
        )

    # 2. Behavioral / Leadership Track (STAR Framework & Incident Management)
    if seniority in ["SENIOR", "STAFF_PRINCIPAL"]:
        questions.append(
            QuestionModel(
                question_id="HR-CORE-01",
                question_type="typed",
                prompt="Describe a critical production Sev-1 outage or high-stakes system degradation you owned. Detail your stakeholder communication cadence, containment actions (e.g. canary rollbacks), and how you led a blameless post-mortem yielding preventative safeguards.",
                track="BEHAVIORAL",
                seniority_target=seniority,
                ideal_rubric="Demonstrates STAR structure, incident commander leadership, transparent stakeholder cadences, and measurable preventative safeguards.",
                required_keywords=["incident commander", "stakeholder", "rollback", "post-mortem", "blameless"],
                weight=1.5
            )
        )
    else:
        questions.append(
            QuestionModel(
                question_id="HR-CORE-01",
                question_type="typed",
                prompt="Describe a situation where you encountered conflicting technical opinions with a teammate. How did you resolve the disagreement and ensure team velocity while maintaining quality?",
                track="BEHAVIORAL",
                seniority_target=seniority,
                ideal_rubric="Focuses on data-driven benchmarking, constructive communication, and team alignment.",
                weight=1.0
            )
        )

    state.questions = questions
    return state


def token_dispatch_node(state: InterviewAgentState) -> InterviewAgentState:
    """
    Node 2: Generates cryptographic 72-hour tokens and triggers the professional
    dual-track invitation email.
    """
    tech_token, hr_token = generate_assessment_tokens(state.candidate_id, state.assessment_id)
    state.technical_token = tech_token
    state.hr_token = hr_token

    payload = {
        "assessment_id": state.assessment_id,
        "candidate_id": state.candidate_id,
        "candidate_name": state.candidate_name,
        "candidate_email": state.candidate_email,
        "job_id": state.job_id,
        "job_title": state.job_context.title,
        "seniority_level": state.job_context.seniority_level,
        "technical_link_token": tech_token,
        "hr_link_token": hr_token,
        "questions": [q.model_dump() for q in state.questions]
    }

    db.save_assessment(state.assessment_id, payload)

    # Deliver Dual-Track Email
    EmailService.send_assessment_invite(
        candidate_name=state.candidate_name,
        candidate_email=state.candidate_email,
        job_title=state.job_context.title,
        tech_token=tech_token,
        hr_token=hr_token
    )

    logger.info(f"Tokens generated and email delivered for assessment {state.assessment_id}")
    return state


def evaluation_node(state: InterviewAgentState) -> InterviewAgentState:
    """
    Node 3: Executes multi-rubric evaluation with anti-cheat and seniority grading.
    """
    logger.info(f"Executing ultra-strict evaluation node for assessment {state.assessment_id}")
    state.output = LLMService.evaluate_answers(
        questions=state.questions,
        answers=state.answers,
        seniority_level=state.job_context.seniority_level
    )
    return state


def run_interview_pipeline(
    candidate_id: str,
    job_id: str,
    candidate_name: str = "Alex Rivera",
    candidate_email: str = "alex.rivera@example.com",
    job_context: JobContextModel = None,
    cv_data: Dict[str, Any] = None
) -> InterviewAgentState:
    """
    Main Pydantic Graph 2.0 pipeline entry point.
    """
    state = InterviewAgentState(
        candidate_id=candidate_id,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        job_id=job_id,
        job_context=job_context or JobContextModel(job_id=job_id),
        cv_data=cv_data or {}
    )
    state = question_synthesis_node(state)
    state = token_dispatch_node(state)
    return state