import os
from typing import List

class Settings:
    DISHA_ENV: str = os.getenv("DISHA_ENV", "development")
    DISHA_APP_NAME: str = os.getenv("DISHA_APP_NAME", "DISHA")
    DISHA_API_PORT: int = int(os.getenv("DISHA_API_PORT", "8000"))
    DISHA_API_HOST: str = os.getenv("DISHA_API_HOST", "0.0.0.0")
    DISHA_API_URL: str = os.getenv("DISHA_API_URL", "http://localhost:8000")
    DISHA_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    DISHA_DATABASE_URL: str = os.getenv("DISHA_DATABASE_URL", "sqlite:///./disha.db")
    DISHA_REDIS_URL: str = os.getenv("DISHA_REDIS_URL", "redis://localhost:6379/0")
    DISHA_JWT_SECRET: str = os.getenv("DISHA_JWT_SECRET", "disha_secure_development_jwt_secret_key_2026")
    DISHA_JWT_ALGORITHM: str = os.getenv("DISHA_JWT_ALGORITHM", "HS256")
    DISHA_JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("DISHA_JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    DISHA_LOG_LEVEL: str = os.getenv("DISHA_LOG_LEVEL", "INFO")

settings = Settings()
