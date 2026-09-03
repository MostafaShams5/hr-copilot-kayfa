import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "REPLACE_WITH_GROQ_KEY")
MONGO_URL    = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME      = "kayfa_headhunter"

# Use specific collection names for your agent in the shared DB
COLL_CANDS   = "headhunting_candidates"
COLL_JOBS    = "headhunting_jobs"
COLL_OUTREACH= "headhunting_outreach"

# Double check if you actually meant 120b. If it fails, change back to 20b
MODEL_NAME = "openai/gpt-oss-120b"

groq_model = GroqModel(
    model_name=MODEL_NAME,
    provider=GroqProvider(api_key=GROQ_API_KEY),
)

COMPANY_ABOUT = (
    "Kayfa Academy is an AI-powered e-learning platform built for Arabic "
    "speakers — equipping students, professionals, and organizations across "
    "the MENA region with future-ready skills."
)

mongo = AsyncIOMotorClient(MONGO_URL)
db    = mongo[DB_NAME]
cands_coll = db[COLL_CANDS]
jobs_coll  = db[COLL_JOBS]
outreach_coll = db[COLL_OUTREACH]

async def init_db() -> None:
    # Drop the old strict unique index if it exists from previous runs
    try:
        await cands_coll.drop_index("profile_url_1")
    except Exception:
        pass
        
    # Create a compound unique index so a candidate can exist for multiple jobs, 
    # but can't be duplicated for the SAME job.
    await cands_coll.create_index([("profile_url", 1), ("job_id", 1)], unique=True)
    await cands_coll.create_index("job_id")
    await jobs_coll.create_index("job_id", unique=True)
    await outreach_coll.create_index("candidate_url")