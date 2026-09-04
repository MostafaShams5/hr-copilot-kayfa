from datetime import datetime
from typing import Optional, List
from .models import RankedCandidate, OutreachMessage, JobInput
from .config import cands_coll, outreach_coll, jobs_coll

async def persist_candidates(job_id: str, ranked: list[RankedCandidate]) -> None:
    """
    Saves the ranked candidates to MongoDB.
    The document structure exactly matches the HeadhuntingOutput JSON schema.
    """
    docs = []
    for r in ranked:
        # Build the document strictly matching the JSON output keys
        doc = {
            "job_id": job_id,
            "profile_url": r.profile_url,
            "full_name": r.full_name,
            "match_score": r.match_score,
            "matched_skills": r.matched_skills,
            "missing_skills": r.missing_skills,
            "skill_assessment": r.skill_assessment,
            "reasons": r.reasons,
            "concerns": r.concerns,
            "recommended": r.recommended,
            "rank": r.rank,
            "stored_at": datetime.utcnow()
        }
        docs.append(doc)
        
    if docs:
        for d in docs:
            # Upsert based on the profile_url and job_id so we don't duplicate
            await cands_coll.update_one(
                {"profile_url": d["profile_url"], "job_id": d["job_id"]},
                {"$set": d},
                upsert=True,
            )

async def persist_outreach(msgs: list[OutreachMessage]) -> None:
    """
    Saves the generated outreach messages to MongoDB.
    """
    for m in msgs:
        doc = {
            "candidate_url": m.candidate_url,
            "full_name": m.full_name,
            "subject": m.subject,
            "body": m.body,
            "tone": m.tone,
            "stored_at": datetime.utcnow()
        }
        await outreach_coll.update_one(
            {"candidate_url": m.candidate_url},
            {"$set": doc},
            upsert=True,
        )

async def persist_job(job: JobInput) -> None:
    """
    Saves the job input details to MongoDB.
    """
    doc = {
        "job_id": job.job_id,
        "title": job.title,
        "description": job.description,
        "requirements": job.requirements,
        "country": job.country,
        "must_have_skills": job.must_have_skills,
        "nice_to_have_skills": job.nice_to_have_skills,
        "updated_at": datetime.utcnow(),
        "job": job.model_dump(mode="json")  # Save the full job object for easy retrieval later
    }
    
    await jobs_coll.update_one(
        {"job_id": job.job_id},
        {"$set": doc},
        upsert=True,
    )

# ==========================================
# NEW: Fetching functions for Endpoint 2
# ==========================================

async def get_job_by_id(job_id: str) -> Optional[JobInput]:
    """Fetches a job from MongoDB to provide context for outreach."""
    doc = await jobs_coll.find_one({"job_id": job_id})
    if doc and "job" in doc:
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
        # Remove MongoDB specific fields before passing to Pydantic
        doc.pop("_id", None)
        doc.pop("stored_at", None)
        candidates.append(RankedCandidate(**doc))
    return candidates