import os
import sys

# Prevent TensorFlow from loading to avoid protobuf version conflicts
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

import asyncio
import io
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from decision_maker.excel_builder import ExcelReportBuilder
from handoff import HeadhuntingOutput, CandidateBase, OutreachMessageBase, CVScreeningOutput, DecisionOutput, DecisionRecommendation
# Headhunting (Agent 1) imports
from headhunting.config import init_db as init_headhunting_db
from headhunting.models import RecruitingState
from headhunting.graph_nodes import recruiting_graph, JobAnalystNode
from headhunting.agents import run_job_extractor, run_outreach
from headhunting.persistence import get_job_by_id, get_candidates_by_urls, persist_outreach
from pydantic_graph import End, GraphRunContext

# CV Screening (Agent 2) imports
from cv_screening.cv_parser import CVParser
from cv_screening.agent import ScreeningAgent

# Interview (Agent 3) imports
from interview.services import LLMService
from interview.database import db as interview_db
from interview.schemas import CandidateSubmission

# Decision Maker (Agent 4) imports
from decision_maker.engine import DecisionRanker
from decision_maker.excel_builder import ExcelReportBuilder

# Chatbot imports
from chatbot.chatbot import ask_kayfa, ChatResponse

# Shared Schemas
from handoff import HeadhuntingOutput, CandidateBase, OutreachMessageBase, CVScreeningOutput, DecisionOutput

# Fix for Windows Playwright subprocess issue
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="Kayfa Recruitment Orchestrator API")

# Enable CORS so your React frontend can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NOTE: We no longer include the interview_router and decision_router directly 
# because we are merging their logic into a single unified endpoint below.
# However, we still include the interview_router if it has other endpoints (like /start) you want to keep.
from interview.routes import router as interview_router
from decision_maker.api import router as decision_router
app.include_router(interview_router)
app.include_router(decision_router)

ranker = DecisionRanker()

@app.on_event("startup")
async def startup_event():
    await init_headhunting_db()

# ==========================================
# 1. HEADHUNTING ENDPOINTS (Agent 1)
# ==========================================
class HiringPrompt(BaseModel):
    prompt: str

class OutreachRequest(BaseModel):
    job_id: str
    candidate_urls: List[str]

@app.post("/sourcing", response_model=List[HeadhuntingOutput], tags=["1. Headhunting"])
async def run_sourcing_pipeline(request: HiringPrompt):
    """Scrapes LinkedIn, evaluates candidates, and returns ranked lists."""
    job = await run_job_extractor(request.prompt)
    state = RecruitingState(job=job, auto_mode=True, skip_outreach=True)
    current_node = JobAnalystNode()
    while not isinstance(current_node, End):
        ctx = GraphRunContext(state=state, deps=None)
        current_node = await current_node.run(ctx)

    team_outputs = []
    for r in state.ranked:
        name_parts = r.full_name.split(" ", 1)
        cand_base = CandidateBase(
            candidate_id=r.profile_url, first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
            email="N/A", resume_text="", profile_url=r.profile_url, full_name=r.full_name,
            match_score=r.match_score, matched_skills=r.matched_skills, missing_skills=r.missing_skills,
            skill_assessment=r.skill_assessment, reasons=r.reasons, concerns=r.concerns,
            recommended=r.recommended, rank=r.rank
        )
        team_outputs.append(HeadhuntingOutput(
            job_id=job.job_id, candidate=cand_base, source_platform="LinkedIn",
            match_confidence=r.match_score / 100.0, outreach_message=None
        ))
    return team_outputs

@app.post("/outreach", response_model=List[OutreachMessageBase], tags=["1. Headhunting"])
async def run_outreach_pipeline(request: OutreachRequest):
    """Fetches specific candidates from DB and generates outreach messages."""
    job = await get_job_by_id(request.job_id)
    if not job: raise HTTPException(status_code=404, detail="Job ID not found.")
    candidates = await get_candidates_by_urls(request.job_id, request.candidate_urls)
    if not candidates: raise HTTPException(status_code=404, detail="No candidates found.")
    msgs = await run_outreach(job, candidates)
    if msgs: await persist_outreach(msgs)
    return msgs

# ==========================================
# 2. CV SCREENING ENDPOINT (Agent 2)
# ==========================================
@app.post("/cv-screening", response_model=CVScreeningOutput, tags=["2. CV Screening"])
async def screen_cv_endpoint(
    file: UploadFile = File(...),
    job_id: str = Form(...),
    role: str = Form(...),
    required_skills: str = Form(...),
    min_years_experience: int = Form(0)
):
    """Parses a PDF/DOCX CV and screens it against job requirements."""
    try:
        contents = await file.read()
        filename = file.filename
        cv_text = CVParser.extract_text(filename, contents)
        parsed_cv = CVParser.parse(cv_text)
        job_data = {
            "job_id": job_id, "role": role,
            "required_skills": [s.strip() for s in required_skills.split(",")],
            "min_years_experience": min_years_experience
        }
        agent = ScreeningAgent()
        result = await agent.screen_candidate_async(parsed_cv, job_data)
        return CVScreeningOutput(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 3. UNIFIED INTERVIEW & DECISION ENDPOINT (Agent 3 & 4)
# ==========================================
@app.post("/api/candidate/assessment/{token}/submit-and-decide", tags=["3. Interview & Decision"])
async def submit_and_decide(token: str, submission: CandidateSubmission):
    """
    Unified Endpoint: Receives candidate answers, evaluates them (Agent 3),
    automatically passes them to the Decision Maker (Agent 4), 
    and returns the final decision grouped as JSON (mirroring the Excel sheets).
    """
    try:
        asm_data = interview_db.get_by_token(token)
        candidate_id = submission.candidate_id
        if (not candidate_id or candidate_id in ["CAND-ONLINE", "CAND-EVAL"]) and asm_data:
            candidate_id = asm_data.get("candidate_id", submission.candidate_id)
        candidate_name = asm_data.get("candidate_name", candidate_id) if asm_data else candidate_id
        seniority = asm_data.get("seniority_level", "SENIOR") if asm_data else "SENIOR"
        questions = asm_data.get("questions", []) if asm_data else []

        # 1. Agent 3: Evaluate Answers via Groq LLM
        evaluation = LLMService.evaluate_answers(
            questions=questions,
            answers=submission.answers,
            seniority_level=seniority,
            candidate_id=candidate_id,
            candidate_name=candidate_name
        )
        
        # Save Agent 3 evaluation to database
        interview_db.save_evaluation_result(
            assessment_id=asm_data.get("assessment_id", "ASM-SUBMITTED") if asm_data else "ASM-SUBMITTED",
            candidate_id=candidate_id,
            result=evaluation.model_dump()
        )

        # 2. Agent 4: Decision Maker Engine
        decision = ranker.evaluate(evaluation)
        decision_json = decision.model_dump(mode="json")

        # 3. Structure the JSON to exactly mirror the Excel dossier sheets
        # Excel Sheet 1: Shortlist (Hire)
        # Excel Sheet 2: Manual Review
        # Excel Sheet 3: Rejected
        response_data = {
            "shortlist_hire": [],
            "manual_review": [],
            "rejected": []
        }

        if decision.recommendation == DecisionRecommendation.APPROVE:
            response_data["shortlist_hire"].append(decision_json)
        elif decision.recommendation == DecisionRecommendation.ESCALATE:
            response_data["manual_review"].append(decision_json)
        elif decision.recommendation == DecisionRecommendation.REJECT:
            response_data["rejected"].append(decision_json)

        # 4. Return the structured JSON
        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unified pipeline failed: {str(e)}")
# ==========================================
# 4. CHATBOT ENDPOINT
# ==========================================
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default_user_session"

@app.post("/chat", response_model=ChatResponse, tags=["5. Chatbot"])
async def chat_endpoint(request: ChatRequest):
    """Handles user queries for the Kayfa Academy assistant."""
    try:
        response = await ask_kayfa(request.query, request.session_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))