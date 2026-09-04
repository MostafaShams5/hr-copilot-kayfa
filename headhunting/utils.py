from .models import JobInput, Candidate, CandidateEvaluation, RankedCandidate

def hard_filter(job: JobInput, cands: list[Candidate]) -> list[Candidate]:
    kept: list[Candidate] = []
    for c in cands:
        # 1. Country Filter
        if c.country and job.country and job.country.lower() not in c.country.lower():
            continue
            
        # 2. Experience Filter
        if c.experience_years:
            if job.min_experience_years and c.experience_years < job.min_experience_years:
                continue
            if job.max_experience_years and c.experience_years > job.max_experience_years:
                continue
                
        # 3. Must-have skills Filter (SOFT FILTER)
        if job.must_have_skills:
            # Combine skills list and summary text for searching
            text_to_search = (c.summary or "").lower() + " " + " ".join(c.skills).lower()
            # FIX: Use any() instead of all(). If the candidate has AT LEAST ONE of the required skills, keep them.
            if not any(ms.lower() in text_to_search for ms in job.must_have_skills):
                continue
                
        kept.append(c)
    return kept

def rank_candidates(evals: list[CandidateEvaluation], top_k: int = 20) -> list[RankedCandidate]:
    sorted_e = sorted(evals, key=lambda e: (-e.match_score, e.full_name.lower()))
    ranked = [RankedCandidate(**e.model_dump(), rank=i + 1) for i, e in enumerate(sorted_e)]
    return ranked[:top_k]