from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://username:password@localhost:5432/agentforge_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8001

    # Auth
    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRE_MINUTES: int = 1440

    # AI — GROQ (not OpenAI)
    GROQ_API_KEY: str = "groq_api"
    GROQ_MODEL: str = "llama3-70b-8192"  # Best free Groq model

    # Search
    SERPAPI_KEY: str = "provide_serpapi"
    HUNTER_API_KEY: str = "provide_hunter_api"

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # Feature flags
    USE_MOCK_DATA: bool = False  # Force mock even if keys set (for testing)
    MOCK_COMPANY_COUNT: int = 20  # Number of companies for dynamic mock generator

    class Config:
        env_file = "backend/.env"
        extra = "ignore"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Backward-compatible singleton alias
settings = get_settings()
