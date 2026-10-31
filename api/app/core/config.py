import os
from typing import List

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel as BaseSettings

class Settings(BaseSettings):
    DISHA_ENV: str = os.getenv("DISHA_ENV", "development")
    DISHA_APP_NAME: str = os.getenv("DISHA_APP_NAME", "DISHA")
    DISHA_API_PORT: int = int(os.getenv("DISHA_API_PORT", "8000"))
    DISHA_API_HOST: str = os.getenv("DISHA_API_HOST", "0.0.0.0")
    DISHA_API_URL: str = os.getenv("DISHA_API_URL", "http://localhost:8000")
    DISHA_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    DISHA_DATABASE_URL: str = os.getenv("DISHA_DATABASE_URL", "postgresql+asyncpg://disha_user:disha_password@localhost:5432/disha_db")
    DISHA_REDIS_URL: str = os.getenv("DISHA_REDIS_URL", "redis://localhost:6379/0")
    DISHA_JWT_SECRET: str = os.getenv("DISHA_JWT_SECRET", "dev_secret_key_change_in_production")
    DISHA_JWT_ALGORITHM: str = os.getenv("DISHA_JWT_ALGORITHM", "HS256")
    DISHA_JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("DISHA_JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    DISHA_LOG_LEVEL: str = os.getenv("DISHA_LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
