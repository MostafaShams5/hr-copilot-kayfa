from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from handoff import InterviewOutput
from .engine import DecisionRanker
from .excel_builder import ExcelReportBuilder

# Setup the router for Developer 4's specific domain
router = APIRouter(prefix="/api/v1/decision-maker", tags=["Decision Maker"])
ranker = DecisionRanker()

@router.post("/rank-and-export")
async def rank_candidates_and_export(payload: List[InterviewOutput]):
    """
    Ingests upstream AI evaluations, ranks them mathematically via Vector embeddings, 
    and returns a downloadable Excel dossier.
    """
    if not payload:
        raise HTTPException(status_code=400, detail="Empty candidate list provided.")

    try:
        # 1. Run the deterministic math engine
        evaluated_decisions = [ranker.evaluate(candidate) for candidate in payload]
        
        # 2. Build the in-memory artifact
        excel_buffer = ExcelReportBuilder.generate_dossier(evaluated_decisions, payload)
        
        # 3. Stream back to the Orchestrator/Client
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"HR_Decision_Dossier_{timestamp}.xlsx"

        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ranking pipeline failed: {str(e)}")
