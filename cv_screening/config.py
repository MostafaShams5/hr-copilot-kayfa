"""Configuration"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "recruitment_ai")
    LLM_MODEL = "openai/gpt-oss-120b"
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

settings = Settings()