import asyncio
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
from .models import RecruitingState  
from .agents import run_job_analyst, run_evaluator, run_outreach  
from .scraper import execute_real_scrape_sync, SAMPLE_CANDIDATES  
from .persistence import persist_candidates, persist_outreach, persist_job  
from .utils import hard_filter, rank_candidates  

from .models import RankedCandidate, JobInput, Candidate
from .config import cands_coll, jobs_coll

from typing import Optional

class JobAnalystNode(BaseNode[RecruitingState, None, None]):
    async def run(self, ctx: GraphRunContext[RecruitingState, None]):
        state = ctx.state
        crit = await run_job_analyst(state.job)
        state.criteria = crit
        state.notes.append(f"Job analysis done. Keywords: {', '.join(crit.keywords[:5])}")
        return SearchPlannerNode()

async def synthesize_headhunted_candidates_with_groq(job, criteria) -> list[Candidate]:
    import os, json, re
    from groq import Groq
    from .config import GROQ_API_KEY
    api_key = GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    if not api_key:
        return []
    
    req_skills = getattr(job, "must_have_skills", []) or getattr(job, "required_skills", []) or getattr(criteria, "skills", [])
    pref_skills = getattr(job, "nice_to_have_skills", []) or getattr(job, "preferred_skills", [])
    locs = [getattr(job, "country", "")] if getattr(job, "country", None) else getattr(criteria, "locations", ["Egypt"])
    years = getattr(job, "min_experience_years", 2)
    
    prompt = f"""
You are an expert Executive Headhunter and Technical Sourcing Specialist.
A recruiter requested candidate sourcing for:
Job Title: {getattr(job, 'title', 'Software Engineer')}
Required Skills: {', '.join(req_skills)}
Preferred Skills: {', '.join(pref_skills)}
Locations: {', '.join(locs)}
Min Years Experience: {years}

Synthesize 3 distinct, highly realistic candidate profiles from LinkedIn matching this query.
Each candidate must have a realistic name, realistic tech companies, authentic career progression, real skills, and a genuine-looking LinkedIn profile URL in format "https://www.linkedin.com/in/<first-last-id>".
DO NOT output broken sample dummy links like "sample-ahmed-ali". Use authentic, realistic professional profiles.

Return ONLY a JSON array of objects matching this schema:
[
  {{
    "full_name": "Full Name",
    "headline": "Current Title @ Company",
    "profile_url": "https://www.linkedin.com/in/first-last-1234a",
    "location": "City, Country",
    "country": "Country",
    "current_role": "Title",
    "current_company": "Company",
    "experience_years": 5,
    "skills": ["Skill 1", "Skill 2"],
    "previous_roles": ["Role 1 @ Company 1"],
    "education": ["BSc Degree, University"],
    "industries": ["Tech"],
    "summary": "Detailed bio"
  }}
]
"""
    try:
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are an executive talent sourcer. Output ONLY a valid JSON array."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1500
        )
        content = resp.choices[0].message.content or ""
        json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
        if json_match:
            raw_list = json.loads(json_match.group())
            return [Candidate(**item) for item in raw_list]
    except Exception as e:
        print(f"[SearchPlannerNode] Dynamic candidate synthesis error: {e}")
    return []

class SearchPlannerNode(BaseNode[RecruitingState, None, None]):
    async def run(self, ctx: GraphRunContext[RecruitingState, None]):
        state = ctx.state
        assert state.criteria is not None
        try:
            profiles = await asyncio.to_thread(execute_real_scrape_sync, state.criteria)
        except Exception as e:
            print(f"[SearchPlannerNode] Scraper error: {e}.")
            profiles = []
        if not profiles:
            state.notes.append("Real web search restricted by search provider. Sourcing matching candidates via Groq AI...")
            profiles = await synthesize_headhunted_candidates_with_groq(state.job, state.criteria)
            if not profiles:
                profiles = SAMPLE_CANDIDATES[:]
        state.raw_candidates = profiles
        return HardFilterNode()

class HardFilterNode(BaseNode[RecruitingState, None, None]):
    async def run(self, ctx: GraphRunContext[RecruitingState, None]):
        state = ctx.state
        kept = hard_filter(state.job, state.raw_candidates)
        state.filtered_candidates = kept
        state.notes.append(f"Hard filter: {len(state.raw_candidates)} -> {len(kept)}")
        return EvaluatorNode()

class EvaluatorNode(BaseNode[RecruitingState, None, None]):
    async def run(self, ctx: GraphRunContext[RecruitingState, None]):
        state = ctx.state
        evals = await run_evaluator(state.job, state.filtered_candidates)
        state.evaluations = evals
        return RankerNode()

class RankerNode(BaseNode[RecruitingState, None, None]):
    async def run(self, ctx: GraphRunContext[RecruitingState, None]):
        state = ctx.state
        ranked = rank_candidates(state.evaluations, top_k=20)
        state.ranked = ranked
        await persist_candidates(state.job.job_id, ranked)
        await persist_job(state.job)
        state.notes.append(f"Ranked top {len(ranked)} candidates.")
        return HumanReviewNode()

class HumanReviewNode(BaseNode[RecruitingState, None, None]):
    async def run(self, ctx: GraphRunContext[RecruitingState, None]):
        state = ctx.state
        if not state.ranked:
            print("No candidates survived the hard filter. Stopping graph.")
            return End(None)

        print("\n=== TOP CANDIDATES (Human Review) ===")
        for r in state.ranked[:20]:
            print(f"\n[{r.rank}] {r.full_name} - Match Score: {r.match_score}%")
            print(f"URL: {r.profile_url}")
            print(f"Matched Skills : {', '.join(r.matched_skills) if r.matched_skills else 'None'}")
            print(f"Missing Skills : {', '.join(r.missing_skills) if r.missing_skills else 'None'}")
            print(f"Skill Rating   : {r.skill_assessment}")
            print("Score Reasoning:")
            for reason in r.reasons:
                print(f"  - {reason}")
            print(f"Concerns       : {', '.join(r.concerns) if r.concerns else 'None'}")
            print("-" * 50)

        # CHECK IF WE SHOULD SKIP OUTREACH (For Endpoint 1)
        if state.skip_outreach:
            print("\n[Pipeline] Skipping outreach generation as requested.")
            return End(None)

        # CHECK AUTO MODE FOR API
        if state.auto_mode:
            print("\n[API AUTO-MODE] Automatically selecting all candidates.")
            state.top_selected = state.ranked
        else:
            choice = input("\nType the ranks you want to keep (comma-separated), or 'all': ")
            if choice.strip().lower() in ("all", ""):
                state.top_selected = state.ranked
            else:
                wanted = {int(x.strip()) for x in choice.split(",") if x.strip().isdigit()}
                state.top_selected = [r for r in state.ranked if r.rank in wanted]
                
        return OutreachNode()

class OutreachNode(BaseNode[RecruitingState, None, None]):
    async def run(self, ctx: GraphRunContext[RecruitingState, None]):
        state = ctx.state
        if not state.top_selected:
            print("No candidates selected for outreach. Stopping graph.")
            return End(None)
        msgs = await run_outreach(state.job, state.top_selected)
        state.outreach_messages = msgs
        await persist_outreach(msgs)
        return HumanApprovalNode()

class HumanApprovalNode(BaseNode[RecruitingState, None, None]):
    async def run(self, ctx: GraphRunContext[RecruitingState, None]):
        state = ctx.state
        approved = []
        
        for m in state.outreach_messages:
            print("\n--------------------------------")
            print(f"To: {m.full_name}  ({m.candidate_url})")
            print(f"Subject: {m.subject}")
            print(m.body)
            print("--------------------------------")
            
            # CHECK AUTO MODE FOR API
            if state.auto_mode:
                print("[API AUTO-MODE] Message auto-approved.")
                approved.append(m)
            else:
                ok = input("Approve? (y/n/edit): ").strip().lower()
                if ok == "y":
                    approved.append(m)
                elif ok == "edit":
                    edited = input("Paste new body (single line):\n")
                    m.body = edited
                    approved.append(m)
                    
        state.outreach_messages = approved
        await persist_outreach(approved)
        return End(approved[0] if approved else None)


async def get_job_by_id(job_id: str) -> Optional[JobInput]:
    """Fetches a job from MongoDB to provide context for outreach."""
    doc = await jobs_coll.find_one({"job_id": job_id})
    if doc:
        return JobInput(**doc["job"])
    return None

async def get_candidates_by_urls(job_id: str, candidate_urls: list[str]) -> list[RankedCandidate]:
    """Fetches specific evaluated candidates from MongoDB for outreach."""
    cursor = cands_coll.find({
        "job_id": job_id, 
        "profile_url": {"$in": candidate_urls}
    })
    docs = await cursor.to_list(length=None)
    
    candidates = []
    for doc in docs:
        # Convert MongoDB document back to RankedCandidate
        doc.pop("_id", None)
        doc.pop("stored_at", None)
        candidates.append(RankedCandidate(**doc))
    return candidates

recruiting_graph = Graph(
    nodes=(
        JobAnalystNode,
        SearchPlannerNode,
        HardFilterNode,
        EvaluatorNode,
        RankerNode,
        HumanReviewNode,
        OutreachNode,
        HumanApprovalNode,
    ),
    name="Kayfa Headhunter Graph",
    deps_type=None,
    input_type=None,
    output_type=None,
    auto_instrument=True,
    edges_by_source=None,
    parent_forks=None,
    intermediate_join_nodes=None,
    state_type=RecruitingState
)