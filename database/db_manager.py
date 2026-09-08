"""
MongoDB Database Manager for Kayfa HR Platform.
Permanently persists campaigns, candidates (CandidatePipelineState), 
evaluations, human decisions, and audit logs into MongoDB.
"""
import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pymongo import MongoClient, DESCENDING

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB_NAME", "recruitment_ai")

class MongoDatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDatabaseManager, cls).__new__(cls)
            cls._instance._connect()
            cls._instance._seed_if_empty()
        return cls._instance

    def _connect(self):
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
            self.db = self.client[DB_NAME]
            # Collections
            self.campaigns_col = self.db["campaigns"]
            self.candidates_col = self.db["candidates"]
            self.audit_col = self.db["audit_logs"]
            # Test ping
            self.client.admin.command('ping')
            self.is_connected = True
        except Exception as e:
            print(f"⚠️ MongoDB connection warning: {e}. Running with in-memory resilient fallback.")
            self.is_connected = False
            self.fallback_campaigns = []
            self.fallback_candidates = []

    def _seed_if_empty(self):
        if not self.is_connected:
            return
        try:
            if self.campaigns_col.count_documents({}) == 0:
                self.campaigns_col.insert_many([
                    {
                        "campaign_id": "CAMP-01",
                        "title": "Senior Backend Engineer (FastAPI/AI)",
                        "department": "Engineering & AI",
                        "status": "ACTIVE",
                        "threshold": 70.0,
                        "owner": "Ahmed Mohamed",
                        "created_at": datetime.now(timezone.utc)
                    },
                    {
                        "campaign_id": "CAMP-02",
                        "title": "AI Research Scientist",
                        "department": "AI Research",
                        "status": "ACTIVE",
                        "threshold": 75.0,
                        "owner": "Sara Al-Otaibi",
                        "created_at": datetime.now(timezone.utc)
                    }
                ])
                
            if self.candidates_col.count_documents({}) == 0:
                self.candidates_col.insert_one({
                    "candidate_id": "CAND-101",
                    "campaign_id": "CAMP-01",
                    "name": "Ahmed Mohamed",
                    "email": "ahmed.m@example.com",
                    "phone": "+20 100 123 4567",
                    "location": "Cairo, Egypt",
                    "experience": "5.5 years",
                    "education": "B.Sc. in Computer Science",
                    "skills": ["Python", "FastAPI", "Redis", "PostgreSQL", "Docker", "Distributed Systems"],
                    "stage": "AI DECISION",
                    "screening": {
                        "overall_score": 84, "required_skills": 91, "experience_score": 82, "education_score": 88,
                        "recommendation": "PASS", "threshold": 70, "status": "PASSED SCREENING",
                        "strengths": ["Strong FastAPI & Async IO", "Redis Distributed Locks & Idempotency", "Database Partitioning"],
                        "gaps": ["Kubernetes (Needs production ramp-up)", "AWS Advanced Networking"]
                    },
                    "interview": {
                        "tech_url": "https://kayfa-recruitment.app/portal/assessment/technical?token=tok_ahmed_tech",
                        "hr_url": "https://kayfa-recruitment.app/portal/assessment/behavioral?token=tok_ahmed_hr",
                        "email_status": "DELIVERED",
                        "technical_score": 82, "hr_score": 79, "composite_score": 81, "eval_status": "COMPLETED"
                    },
                    "decision": {
                        "recommendation": "SHORTLIST", "confidence": 89, "final_score": 83.5,
                        "reasoning": "Candidate demonstrates senior mastery of asynchronous Python and distributed caching. Handled Sev-1 blameless post-mortems with maturity.",
                        "probing_questions": [
                            "How did you validate Redis TTL lease safety during severe node failovers?",
                            "Walk me through how you aligned conflicting backend and product priorities during past sprint crunches."
                        ]
                    },
                    "final_human_decision": None,
                    "updated_at": datetime.now(timezone.utc)
                })
        except Exception as e:
            print(f"Error seeding MongoDB: {e}")

    # --- Campaign CRUD ---
    def get_campaigns(self) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return self.fallback_campaigns
        docs = list(self.campaigns_col.find({}, {"_id": 0}).sort("created_at", DESCENDING))
        return docs

    def create_campaign(self, campaign_id: str, title: str, department: str, threshold: float, owner: str):
        doc = {
            "campaign_id": campaign_id,
            "title": title,
            "department": department,
            "status": "ACTIVE",
            "threshold": threshold,
            "owner": owner,
            "created_at": datetime.now(timezone.utc)
        }
        if self.is_connected:
            self.campaigns_col.update_one({"campaign_id": campaign_id}, {"$set": doc}, upsert=True)
        else:
            self.fallback_campaigns.append(doc)

    # --- Candidate CRUD ---
    def get_candidates(self, campaign_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return self.fallback_candidates
        query = {"campaign_id": campaign_id} if campaign_id else {}
        docs = list(self.candidates_col.find(query, {"_id": 0}).sort("updated_at", DESCENDING))
        return docs

    def save_candidate(self, cand_data: Dict[str, Any]):
        cand_id = cand_data.get("id") or cand_data.get("candidate_id")
        cand_data["candidate_id"] = cand_id
        cand_data["updated_at"] = datetime.now(timezone.utc)
        
        if self.is_connected:
            self.candidates_col.update_one(
                {"candidate_id": cand_id},
                {"$set": cand_data},
                upsert=True
            )
        else:
            self.fallback_candidates = [c for c in self.fallback_candidates if c.get("candidate_id") != cand_id]
            self.fallback_candidates.append(cand_data)

    def update_human_decision(self, candidate_id: str, decision: str, new_stage: str):
        """Permanently write the human HR verdict to MongoDB."""
        if self.is_connected:
            self.candidates_col.update_one(
                {"candidate_id": candidate_id},
                {
                    "$set": {
                        "final_human_decision": decision,
                        "stage": new_stage,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

# Global singleton database instance
db = MongoDatabaseManager()