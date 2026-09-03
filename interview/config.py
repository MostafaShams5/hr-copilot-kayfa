import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "Kayfa Recruitment Workflow"
    APP_URL: str = os.getenv("APP_URL", os.getenv("APP_BASE_URL", "http://localhost:3000"))
    PORT: int = int(os.getenv("PORT", "3000"))
    HOST: str = "0.0.0.0"
    
    # AI Models
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    DB_NAME: str = os.getenv("MONGODB_DB_NAME", "recruitment_ai")
    
    # Token & Security
    TOKEN_SECRET: str = os.getenv("TOKEN_SECRET", "recruitment-secure-secret-key-32b")
    DEFAULT_TOKEN_EXPIRY_DAYS: int = int(os.getenv("ASSESSMENT_VALID_DAYS", "3"))
    
    # Workflow & Evaluation Thresholds (Centralized)
    SCREENING_THRESHOLD: float = float(os.getenv("SCREENING_THRESHOLD", "70.0"))
    TECHNICAL_PASS_THRESHOLD: float = float(os.getenv("TECHNICAL_PASS_THRESHOLD", "70.0"))
    HR_PASS_THRESHOLD: float = float(os.getenv("HR_PASS_THRESHOLD", "70.0"))
    FINAL_PASS_THRESHOLD: float = float(os.getenv("FINAL_PASS_THRESHOLD", "70.0"))
    DISTINCTION_THRESHOLD: float = float(os.getenv("DISTINCTION_THRESHOLD", "85.0"))
    SCORE_GATE_THRESHOLD: float = float(os.getenv("SCORE_GATE_THRESHOLD", "85.0"))
    TECHNICAL_WEIGHT: float = float(os.getenv("TECHNICAL_WEIGHT", "0.70"))
    HR_WEIGHT: float = float(os.getenv("HR_WEIGHT", "0.30"))

    # Semantic Cache Observability Constants
    CACHE_TOKENS_SAVED_TECH: int = int(os.getenv("CACHE_TOKENS_SAVED_TECH", "1250"))
    CACHE_TOKENS_SAVED_HR: int = int(os.getenv("CACHE_TOKENS_SAVED_HR", "800"))
    
    # Email / SMTP Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Kayfa Talent Acquisition")
    
    class Config:
        extra = "allow"

settings = Settings()

def get_settings() -> Settings:
    return settings
