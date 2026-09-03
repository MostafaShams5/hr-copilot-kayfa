

import os
import re
import math
import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from pymongo import MongoClient
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart
from openai import OpenAI

from .prompt import KAYFA_CHATBOT_SYSTEM_PROMPT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("KayfaChatbot")

# --- Singleton MongoDB Client ---
_mongo_client: Optional[MongoClient] = None

def get_mongo_db(uri: str, db_name: str):
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000, maxPoolSize=20)
        except Exception as e:
            logger.warning(f"⚠️ MongoDB connection failed: {e}")
            return None
    return _mongo_client[db_name]

# --- Lightweight Root Word & Parameter Normalizer ---
def sanitize_tool_arg(val: Optional[str]) -> Optional[str]:
    """Sanitizes tool arguments, strips Arabic diacritics, and handles root-word fallbacks."""
    if not val or str(val).strip().lower() in ["none", "null", "undefined", ""]:
        return None

    cleaned = val.strip()
    # Strip Arabic diacritics / Tashkeel
    cleaned = re.sub(r'[\u064B-\u0652\u0640]', '', cleaned)

    # City & Location root-word fallback
    location_roots = {
        "رياض": "Riyadh",
        "سعودي": "Saudi Arabia",
        "دبي": "Dubai",
        "امارات": "UAE",
        "إمارات": "UAE",
        "قاهر": "Cairo",
        "مصر": "Egypt",
        "ريموت": "Remote",
        "عن بعد": "Remote",
        "اونلاين": "Remote"
    }
    for root, en_name in location_roots.items():
        if root in cleaned:
            return en_name

    # Keyword root-word fallback
    keyword_roots = {
        "ذكاء": "AI",
        "فرونت": "Frontend",
        "واجهات": "Frontend",
        "باك": "Backend",
        "خوادم": "Backend",
        "بيانات": "Data",
        "أمن": "Security",
        "امن": "Security",
        "سيبراني": "Cybersecurity",
        "تصميم": "Designer",
        "مصمم": "Designer",
        "فيديو": "Video",
        "مونتاج": "Video",
        "توظيف": "Recruiter",
        "مدرب": "Instructor",
        "محاضر": "Instructor",
        "برمج": "Engineer",
        "مهندس": "Engineer",
        "مطور": "Engineer"
    }
    for root, en_term in keyword_roots.items():
        if root in cleaned:
            return en_term

    return cleaned

# --- Structured Output Schema ---
class ReferencedJob(BaseModel):
    job_id: str = Field(description="Unique Job ID e.g. JOB-AI-01")
    title: str = Field(description="Job title in English and Arabic")
    location: str = Field(description="Job location city & country")
    salary_range: Optional[str] = Field(None, description="Salary range")

class ChatResponse(BaseModel):
    tool_used: str = Field(description="'rag_company_knowledge', 'fetch_available_jobs', 'both', or 'none'")
    detected_dialect_or_lang: str = Field(description="Detected language/dialect")
    reply: str = Field(description="Conversational markdown reply")
    referenced_jobs: List[ReferencedJob] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    confidence_score: float = Field(1.0)

# --- Dependencies & Runtime State ---
@dataclass
class ChatDeps:
    mongo_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name: str = os.getenv("MONGODB_DB_NAME", "recruitment_ai")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    session_id: str = "default_session"
    active_tools_invoked: List[str] = field(default_factory=list)
    retrieved_jobs: List[Dict[str, Any]] = field(default_factory=list)
    retrieved_sources: List[str] = field(default_factory=list)

    def get_db(self):
        return get_mongo_db(self.mongo_uri, self.db_name)

    def get_openai(self):
        return OpenAI(api_key=self.openai_api_key) if self.openai_api_key else OpenAI()

# --- Initialize Agent ---
default_model = os.getenv("PYDANTIC_AI_MODEL", "openai:gpt-4o-mini")

kayfa_agent = Agent(
    model=default_model,
    deps_type=ChatDeps,
    system_prompt=KAYFA_CHATBOT_SYSTEM_PROMPT
)

# --- Similarity Functions ---
def get_embedding(client: OpenAI, text: str) -> List[float]:
    try:
        res = client.embeddings.create(model="text-embedding-3-small", input=text, timeout=10.0)
        return res.data[0].embedding
    except Exception as e:
        logger.error(f"❌ OpenAI embedding error: {e}")
        return []

def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

# --- Tool 1: Company Knowledge Tool ---
@kayfa_agent.tool
def rag_company_knowledge(ctx: RunContext[ChatDeps], query: str) -> str:
    """
    Search institutional facts about Kayfa Academy (tracks, courses, 5-stage learning model,
    accreditations IAO/CPD/NAITS, 'Teach on Kayfa' instructor program, contact info, payment methods).

    Args:
        query: Short English search query (e.g. 'web development tracks', 'IAO accreditations', 'fawry payment').
    """
    start_t = time.time()
    ctx.deps.active_tools_invoked.append("rag_company_knowledge")
    logger.info(f"🔍 [TOOL INVOCATION] `rag_company_knowledge` | Query: \"{query}\"")

    db = ctx.deps.get_db()
    if db is None:
        return "Kayfa Academy is an AI-powered EdTech institution in the MENA region."

    all_chunks = list(db.knowledge_chunks.find({"embedding": {"$exists": True}}))
    if not all_chunks:
        kb_doc = db.knowledge_base.find_one({"doc_id": "kayfa_company_profile"})
        return kb_doc.get("content", "")[:2500] if kb_doc else "Knowledge base empty."

    openai_client = ctx.deps.get_openai()
    query_emb = get_embedding(openai_client, query)

    scored = []
    query_words = [w.lower() for w in query.split() if len(w) > 2]

    for chunk in all_chunks:
        vec_sim = cosine_similarity(query_emb, chunk.get("embedding", [])) if query_emb else 0.0
        
        # Simple keyword presence boost
        content_lower = chunk.get("content", "").lower() + " " + chunk.get("headline", "").lower()
        kw_matches = sum(1 for w in query_words if w in content_lower)
        final_score = vec_sim + (kw_matches * 0.12)
        
        scored.append((final_score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_matches = [c for _, c in scored[:3]]

    ctx.deps.retrieved_sources.extend([c.get("headline", "") for c in top_matches])

    elapsed_ms = (time.time() - start_t) * 1000
    logger.info(f"📊 [RAG METRICS] Top Match: '{top_matches[0]['headline']}' in {elapsed_ms:.1f}ms")

    return "\n\n---\n\n".join([f"### {c['headline']}\n{c['content']}" for c in top_matches])

# --- Tool 2: Job Search Tool ---
@kayfa_agent.tool
def fetch_available_jobs(
    ctx: RunContext[ChatDeps],
    keyword: Optional[str] = None,
    location: Optional[str] = None,
    department: Optional[str] = None
) -> str:
    """
    Search live job vacancies, salaries, experience requirements, and hiring status at Kayfa Academy.

    Args:
        keyword: Role title or skill in English (e.g. 'AI', 'Frontend', 'Backend', 'Data Science', 'Security').
        location: Target city or model in English: 'Riyadh', 'Dubai', 'Cairo', or 'Remote'. Pass None if unspecified.
        department: Department name in English (e.g. 'Engineering & AI', 'Education'). Pass None if unspecified.
    """
    start_t = time.time()
    ctx.deps.active_tools_invoked.append("fetch_available_jobs")

    norm_kw = sanitize_tool_arg(keyword)
    norm_loc = sanitize_tool_arg(location)
    norm_dept = sanitize_tool_arg(department)

    logger.info(f"💼 [TOOL INVOCATION] `fetch_available_jobs` | (kw='{norm_kw}', loc='{norm_loc}', dept='{norm_dept}')")

    db = ctx.deps.get_db()
    if db is None:
        return "Jobs database unavailable."

    and_conditions = [{"status": "ACTIVE"}]

    if norm_loc:
        and_conditions.append({
            "$or": [
                {"location": {"$regex": norm_loc, "$options": "i"}},
                {"location_city": {"$regex": norm_loc, "$options": "i"}},
                {"location_country": {"$regex": norm_loc, "$options": "i"}}
            ]
        })

    if norm_dept:
        and_conditions.append({
            "$or": [
                {"department": {"$regex": norm_dept, "$options": "i"}},
                {"department_ar": {"$regex": norm_dept, "$options": "i"}}
            ]
        })

    if norm_kw:
        and_conditions.append({
            "$or": [
                {"title": {"$regex": norm_kw, "$options": "i"}},
                {"title_ar": {"$regex": norm_kw, "$options": "i"}},
                {"description": {"$regex": norm_kw, "$options": "i"}},
                {"required_skills": {"$regex": norm_kw, "$options": "i"}},
                {"track_alignment": {"$regex": norm_kw, "$options": "i"}}
            ]
        })

    final_query = {"$and": and_conditions} if len(and_conditions) > 1 else and_conditions[0]
    jobs_list = list(db.jobs.find(final_query).limit(5))

    elapsed_ms = (time.time() - start_t) * 1000
    logger.info(f"📊 [JOBS METRICS] Found {len(jobs_list)} active matching jobs in {elapsed_ms:.1f}ms")

    ctx.deps.retrieved_jobs.extend(jobs_list)

    if not jobs_list:
        return "No open positions currently match the specified criteria in the database."

    summary = []
    for j in jobs_list:
        summary.append(
            f"**Job ID**: {j.get('job_id')} | **Title**: {j.get('title')} ({j.get('title_ar')})\n"
            f"- **Location**: {j.get('location')}\n"
            f"- **Experience**: {j.get('experience_level')}\n"
            f"- **Salary**: {j.get('salary_range')}\n"
            f"- **Required Skills**: {', '.join(j.get('required_skills', []))}\n"
            f"- **Description**: {j.get('description')}\n"
        )
    return "\n\n".join(summary)

# --- Multi-Turn Session Persistence ---
def build_native_message_history(db, session_id: str) -> List[Any]:
    if db is None:
        return []
    doc = db.chat_sessions.find_one({"session_id": session_id})
    if not doc or "messages" not in doc:
        return []

    native_history = []
    for m in doc["messages"][-6:]:  # Last 3 conversational turns
        if m["role"] == "user":
            native_history.append(ModelRequest(parts=[UserPromptPart(content=m["content"])]))
        elif m["role"] == "assistant":
            native_history.append(ModelResponse(parts=[TextPart(content=m["content"])]))
    return native_history

def persist_session_turn(db, session_id: str, user_q: str, assistant_reply: str):
    if db is None:
        return
    db.chat_sessions.update_one(
        {"session_id": session_id},
        {
            "$push": {
                "messages": {
                    "$each": [
                        {"role": "user", "content": user_q},
                        {"role": "assistant", "content": assistant_reply}
                    ],
                    "$slice": -10
                }
            }
        },
        upsert=True
    )

# --- Primary Chat Entrypoint ---
async def ask_kayfa(query: str, session_id: str = "default_user_session") -> ChatResponse:
    t0 = time.time()
    deps = ChatDeps(session_id=session_id)
    db = deps.get_db()

    message_history = build_native_message_history(db, session_id)

    logger.info("=" * 65)
    logger.info(f"📨 [QUERY RECEIVED] (Session: {session_id}): \"{query}\"")

    result = await kayfa_agent.run(query, deps=deps, message_history=message_history)

    # Determine tool usage
    invoked = deps.active_tools_invoked
    if "rag_company_knowledge" in invoked and "fetch_available_jobs" in invoked:
        tool_decision = "both"
    elif "rag_company_knowledge" in invoked:
        tool_decision = "rag_company_knowledge"
    elif "fetch_available_jobs" in invoked:
        tool_decision = "fetch_available_jobs"
    else:
        tool_decision = "none"

    # Dialect detection
    lower_q = query.lower()
    if any(w in query for w in ["وش", "يا هلا", "عندكم", "ابشر", "أبشر", "حياك"]):
        dialect = "Gulf / Saudi Arabic"
    elif any(w in query for w in ["إيه", "ايه", "ازاي", "عاملين", "أهلاً", "اهل", "منين"]):
        dialect = "Egyptian Arabic"
    elif any(w in query for w in ["شو", "بتحب", "تكرم", "عنا"]):
        dialect = "Levantine Arabic"
    elif re.search(r"[a-zA-Z]", query):
        dialect = "English"
    else:
        dialect = "Modern Standard Arabic"

    reply_str = str(getattr(result, "data", getattr(result, "output", result)))

    ref_jobs = [
        ReferencedJob(
            job_id=j.get("job_id", ""),
            title=f"{j.get('title', '')} ({j.get('title_ar', '')})",
            location=j.get("location", ""),
            salary_range=j.get("salary_range")
        )
        for j in deps.retrieved_jobs
    ]

    response_data = ChatResponse(
        tool_used=tool_decision,
        detected_dialect_or_lang=dialect,
        reply=reply_str,
        referenced_jobs=ref_jobs,
        sources=list(set(deps.retrieved_sources)),
        confidence_score=1.0
    )

    total_latency_ms = (time.time() - t0) * 1000
    logger.info(f"🎯 [DECISION] Tool: {tool_decision} | Dialect: {dialect} | Latency: {total_latency_ms:.1f}ms")
    logger.info("=" * 65)

    persist_session_turn(db, session_id, query, reply_str)

    return response_data
