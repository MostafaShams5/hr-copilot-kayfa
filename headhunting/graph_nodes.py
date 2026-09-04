import asyncio
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
from .models import RecruitingState
from .agents import run_job_analyst, run_evaluator, run_outreach
from .scraper import execute_real_scrape_sync, SAMPLE_CANDIDATES
from .persistence import persist_candidates, persist_outreach, persist_job
from .utils import hard_filter, rank_candidates

from .models import RankedCandidate, JobInput
from .config import cands_coll, jobs_coll

from typing import Optional

class JobAnalystNode(BaseNode[RecruitingState, None, None]):
    async def run(self, ctx: GraphRunContext[RecruitingState, None]):
        state = ctx.state
        crit = await run_job_analyst(state.job)
        state.criteria = crit
        state.notes.append(f"Job analysis done. Keywords: {', '.join(crit.keywords[:5])}")
        return SearchPlannerNode()

class SearchPlannerNode(BaseNode[RecruitingState, None, None]):
    async def run(self, ctx: GraphRunContext[RecruitingState, None]):
        state = ctx.state
        assert state.criteria is not None
        profiles = await asyncio.to_thread(execute_real_scrape_sync, state.criteria)
        if not profiles:
            state.notes.append("Real scrape returned nothing — using SAMPLE_CANDIDATES.")
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