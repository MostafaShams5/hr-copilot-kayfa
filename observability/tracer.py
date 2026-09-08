"""
Observability & AI Operations Engine for Kayfa HR Agentic Platform.
Tracks: Agent Runs, Steps, Tool Calls, Tokens, Latency, AI Costs, Errors & Audit Logs.
"""
import time
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class RunStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRIED = "RETRIED"

@dataclass
class ToolCallRecord:
    tool_name: str
    agent_name: str
    calls_count: int
    success_rate: float
    avg_latency_s: float
    failures: int = 0
    retries: int = 0

@dataclass
class AgentStepRecord:
    step_name: str
    duration_ms: float
    tool: str
    input_meta: str
    output_meta: str
    tokens: int
    status: str

@dataclass
class AgentRunRecord:
    run_id: str
    agent_name: str
    campaign_id: str
    candidate_id: Optional[str]
    user_id: str
    status: RunStatus
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    latency_ms: float
    tool_calls_count: int
    created_at: str
    steps: List[AgentStepRecord] = field(default_factory=list)
    error_msg: Optional[str] = None
    retry_count: int = 0

class ObservabilityHub:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ObservabilityHub, cls).__new__(cls)
            cls._instance.runs: List[AgentRunRecord] = []
            cls._instance.tool_registry: Dict[str, ToolCallRecord] = {}
            cls._instance.errors: List[Dict[str, Any]] = []
            cls._instance.audit_logs: List[Dict[str, Any]] = []
            cls._instance._seed_baseline_observability()
        return cls._instance

    def _seed_baseline_observability(self):
        # 1. Seed Tool Calls
        tools = [
            ("PDF Parser", "CV Screening Agent", 1284, 99.8, 0.8, 2, 1),
            ("Document Parser", "CV Screening Agent", 840, 99.4, 0.6, 5, 2),
            ("Candidate Search Tool", "Headhunting Agent", 412, 98.1, 2.3, 8, 4),
            ("Email Dispatcher", "Interviewer Agent", 324, 97.5, 1.1, 8, 3),
            ("SentenceTransformer Vectorizer", "Decision Making Agent", 186, 100.0, 0.3, 0, 0),
            ("Excel Report Generator", "Headhunting Agent", 94, 100.0, 0.5, 0, 0),
            ("Groq Llama-3.3 LLM", "Shared Agent Layer", 2950, 99.1, 1.4, 26, 12),
        ]
        for name, agent, calls, succ, lat, fails, retries in tools:
            self.tool_registry[name] = ToolCallRecord(
                tool_name=name, agent_name=agent, calls_count=calls,
                success_rate=succ, avg_latency_s=lat, failures=fails, retries=retries
            )

        # 2. Seed Chronological Agent Runs with Detailed Steps
        sample_runs = [
            ("RUN #A82F91", "CV Screening Agent", "CAMP-BACKEND-01", "CAND-AHMED-01", "hr_ahmed", "groq:llama-3.3-70b", 940, 420, 1360, 0.0038, 1240, 2, "2026-09-06 13:42:10"),
            ("RUN #B94C12", "Interviewer Agent", "CAMP-BACKEND-01", "CAND-AHMED-01", "system_orchestrator", "openai:gpt-4o", 2400, 1150, 3550, 0.0152, 2890, 1, "2026-09-06 13:45:22"),
            ("RUN #C11D88", "Decision Making Agent", "CAMP-BACKEND-01", "CAND-AHMED-01", "system_orchestrator", "SentenceTransformer+VectorEngine", 310, 140, 450, 0.0004, 380, 1, "2026-09-06 13:48:05"),
            ("RUN #D44E09", "Headhunting Agent", "CAMP-BACKEND-01", None, "hr_sara", "groq:llama-3.3-70b", 4200, 1850, 6050, 0.0194, 4320, 4, "2026-09-06 13:12:40"),
            ("RUN #E77A34", "CV Screening Agent", "CAMP-BACKEND-01", "CAND-SARA-02", "hr_ahmed", "groq:llama-3.3-70b", 890, 380, 1270, 0.0035, 1180, 2, "2026-09-06 12:55:18"),
        ]
        
        for r_id, agent, camp, cand, user, model, in_tok, out_tok, tot_tok, cost, lat, tools_cnt, ts in sample_runs:
            steps = [
                AgentStepRecord("Parse CV", 240, "PDF Parser", "PDF 2.4MB", "Text 18.2KB", 0, "SUCCESS"),
                AgentStepRecord("Extract Skills & Experience", 380, "Groq LLM", "Raw text", "Skills JSON", in_tok // 2, "SUCCESS"),
                AgentStepRecord("Compare Against Job Requisition", 420, "Groq LLM", "Requirements", "Match Score 91%", in_tok // 2, "SUCCESS"),
                AgentStepRecord("Calculate Mathematical Vector", 120, "VectorEngine", "Qualitative notes", "Score: 91.5%", 0, "SUCCESS"),
                AgentStepRecord("Save Result & Next Stage Trigger", 80, "MongoDB Repository", "CVScreeningOutput", "ID saved", 0, "SUCCESS")
            ]
            record = AgentRunRecord(
                run_id=r_id, agent_name=agent, campaign_id=camp, candidate_id=cand,
                user_id=user, status=RunStatus.SUCCESS, model=model,
                input_tokens=in_tok, output_tokens=out_tok, total_tokens=tot_tok,
                estimated_cost_usd=cost, latency_ms=lat, tool_calls_count=tools_cnt,
                created_at=ts, steps=steps
            )
            self.runs.append(record)

        # 3. Seed Error Monitoring records
        self.errors = [
            {"timestamp": "12:42:15", "agent": "Interviewer Agent", "run_id": "RUN #A82F91", "user": "hr_ahmed", "campaign": "CAMP-BACKEND-01", "tool": "Email Dispatcher", "error_type": "SMTPTimeoutError", "message": "Email delivery timed out after 30s. Auto-retried successfully.", "retry_count": 1, "status": "RESOLVED"},
            {"timestamp": "11:15:02", "agent": "CV Screening Agent", "run_id": "RUN #X72A19", "user": "hr_sara", "campaign": "CAMP-AI-02", "tool": "PDF Parser", "error_type": "CVParseError", "message": "Corrupted or image-only PDF detected with zero extractable text.", "retry_count": 0, "status": "FLAGGED"}
        ]

        # 4. Seed Audit Logs
        self.audit_logs = [
            {"timestamp": "2026-09-06 13:48:10", "user": "HR Manager (Ahmed)", "action": "CANDIDATE_SHORTLISTED", "entity": "Candidate", "entity_id": "CAND-AHMED-01", "result": "SUCCESS"},
            {"timestamp": "2026-09-06 13:45:00", "user": "System Agent", "action": "INTERVIEW_INVITATION_SENT", "entity": "Candidate", "entity_id": "CAND-AHMED-01", "result": "SUCCESS"},
            {"timestamp": "2026-09-06 13:42:30", "user": "CV Screening Agent", "action": "SCREENING_PASSED", "entity": "ScreeningResult", "entity_id": "SCR-9182", "result": "SCORE_91%"},
            {"timestamp": "2026-09-06 13:00:15", "user": "HR Manager (Ahmed)", "action": "CAMPAIGN_CREATED", "entity": "Campaign", "entity_id": "CAMP-BACKEND-01", "result": "SUCCESS"},
            {"timestamp": "2026-09-06 09:12:00", "user": "Administrator", "action": "USER_ROLE_ASSIGNED", "entity": "User", "entity_id": "USR-402", "result": "HR_ROLE"}
        ]

    def start_run(self, agent_name: str, campaign_id: str, candidate_id: Optional[str] = None, user_id: str = "hr_manager", model: str = "groq:llama-3.3-70b") -> AgentRunRecord:
        r_id = f"RUN #{uuid.uuid4().hex[:6].upper()}"
        record = AgentRunRecord(
            run_id=r_id, agent_name=agent_name, campaign_id=campaign_id,
            candidate_id=candidate_id, user_id=user_id, status=RunStatus.RUNNING,
            model=model, input_tokens=0, output_tokens=0, total_tokens=0,
            estimated_cost_usd=0.0, latency_ms=0.0, tool_calls_count=0,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        )
        self.runs.insert(0, record)
        return record

    def end_run(self, run: AgentRunRecord, input_tokens: int, output_tokens: int, duration_ms: float, steps: List[AgentStepRecord] = None, status: RunStatus = RunStatus.SUCCESS, error: str = None):
        run.input_tokens = input_tokens
        run.output_tokens = output_tokens
        run.total_tokens = input_tokens + output_tokens
        run.latency_ms = round(duration_ms, 1)
        run.estimated_cost_usd = round((input_tokens * 0.0000015) + (output_tokens * 0.0000035), 6)
        run.status = status
        run.error_msg = error
        if steps:
            run.steps = steps
        self.log_audit(run.user_id, f"{run.agent_name.upper()}_COMPLETED", "Agent execution finalized", run.run_id)

    def log_audit(self, user: str, action: str, entity: str, entity_id: str, result: str = "SUCCESS"):
        self.audit_logs.insert(0, {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "user": user,
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "result": result
        })

    def get_kpis(self) -> Dict[str, Any]:
        total = len(self.runs)
        succ = sum(1 for r in self.runs if r.status == RunStatus.SUCCESS)
        fail = sum(1 for r in self.runs if r.status == RunStatus.FAILED)
        in_tok = sum(r.input_tokens for r in self.runs)
        out_tok = sum(r.output_tokens for r in self.runs)
        cost = sum(r.estimated_cost_usd for r in self.runs)
        latencies = [r.latency_ms for r in self.runs] or [0]
        avg_lat = sum(latencies) / len(latencies)
        sorted_lat = sorted(latencies)
        p95 = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0
        tool_calls = sum(t.calls_count for t in self.tool_registry.values())
        retries = sum(t.retries for t in self.tool_registry.values())
        return {
            "agent_runs": total,
            "success_rate": round((succ / total * 100), 1) if total else 100.0,
            "failure_rate": round((fail / total * 100), 1) if total else 0.0,
            "total_tokens": in_tok + out_tok,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "estimated_cost": round(cost, 4),
            "avg_latency": round(avg_lat / 1000, 2),
            "p95_latency": round(p95 / 1000, 2),
            "tool_calls": tool_calls,
            "retries": retries
        }

observability = ObservabilityHub()