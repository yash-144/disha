import os
from pathlib import Path
from typing import List

try:  # the shared repo-root .env holds DATABASE_URL, JWT secret, etc.; real environment variables win
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)
except ImportError:
    pass

import sys
_ML_DIR = Path(__file__).resolve().parents[3] / "ml"
if _ML_DIR.is_dir() and str(_ML_DIR) not in sys.path:  # the rolling model package (disha_ml) lives beside the api
    sys.path.append(str(_ML_DIR))

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
    DISHA_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    DISHA_DATABASE_URL: str = os.getenv("DISHA_DATABASE_URL", "postgresql+asyncpg://disha_user:disha_password@localhost:5432/disha_db")
    DISHA_REDIS_URL: str = os.getenv("DISHA_REDIS_URL", "redis://localhost:6379/0")
    DISHA_JWT_SECRET: str = os.getenv("DISHA_JWT_SECRET", "dev_secret_key_change_in_production")
    DISHA_JWT_ALGORITHM: str = os.getenv("DISHA_JWT_ALGORITHM", "HS256")
    DISHA_JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("DISHA_JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    DISHA_LOG_LEVEL: str = os.getenv("DISHA_LOG_LEVEL", "INFO")
    # Outbox / escalation (blueprint 07 OUT-07)
    DISHA_OUTBOX_BATCH_SIZE: int = int(os.getenv("DISHA_OUTBOX_BATCH_SIZE", "50"))
    DISHA_OUTBOX_MAX_ATTEMPTS: int = int(os.getenv("DISHA_OUTBOX_MAX_ATTEMPTS", "5"))
    DISHA_OUTBOX_BASE_BACKOFF_SECONDS: int = int(os.getenv("DISHA_OUTBOX_BASE_BACKOFF_SECONDS", "5"))
    DISHA_ESCALATION_TARGET: str = os.getenv("DISHA_ESCALATION_TARGET", "role:hod")
    # Local IndicTrans2 translation (optional extra: pip install -e "api[translate]")
    DISHA_TRANSLATE_ENABLED: bool = os.getenv("DISHA_TRANSLATE_ENABLED", "false").lower() in ("1", "true", "yes")

    # Documents (blueprint 11). Local filesystem by default; S3-compatible when a bucket is set (pip install -e "api[s3]")
    DISHA_DOCUMENTS_STORAGE_DIR: str = os.getenv("DISHA_DOCUMENTS_STORAGE_DIR", "storage/documents")
    DISHA_DOCUMENTS_MAX_BYTES: int = int(os.getenv("DISHA_DOCUMENTS_MAX_BYTES", str(10 * 1024 * 1024)))
    DISHA_DOCUMENTS_ALLOWED_MIME: str = os.getenv(
        "DISHA_DOCUMENTS_ALLOWED_MIME", "application/pdf,image/png,image/jpeg,text/plain,text/csv"
    )
    DISHA_DOCUMENTS_S3_BUCKET: str = os.getenv("DISHA_DOCUMENTS_S3_BUCKET", "")
    DISHA_DOCUMENTS_S3_ENDPOINT_URL: str = os.getenv("DISHA_DOCUMENTS_S3_ENDPOINT_URL", "")
    DISHA_DOCUMENTS_S3_REGION: str = os.getenv("DISHA_DOCUMENTS_S3_REGION", "")
    DISHA_DOCUMENTS_S3_ACCESS_KEY_ID: str = os.getenv("DISHA_DOCUMENTS_S3_ACCESS_KEY_ID", "")
    DISHA_DOCUMENTS_S3_SECRET_ACCESS_KEY: str = os.getenv("DISHA_DOCUMENTS_S3_SECRET_ACCESS_KEY", "")
    DISHA_DOCUMENTS_SIGNED_URL_TTL_SECONDS: int = int(os.getenv("DISHA_DOCUMENTS_SIGNED_URL_TTL_SECONDS", "300"))

    # Blockchain anchoring and student identity collectible (blueprint 11). All empty = disabled; nothing is
    # ever recorded as anchored/minted without a confirmed chain receipt. Needs: pip install -e "api[chain]"
    DISHA_BLOCKCHAIN_RPC_URL: str = os.getenv("DISHA_BLOCKCHAIN_RPC_URL", "")
    DISHA_BLOCKCHAIN_CHAIN_ID: int = int(os.getenv("DISHA_BLOCKCHAIN_CHAIN_ID", "84532"))
    DISHA_ANCHOR_PRIVATE_KEY: str = os.getenv("DISHA_ANCHOR_PRIVATE_KEY", "")  # use a secret manager in production (DOC-08)
    DISHA_DOCUMENT_REGISTRY_ADDRESS: str = os.getenv("DISHA_DOCUMENT_REGISTRY_ADDRESS", "")
    DISHA_IDENTITY_NFT_ADDRESS: str = os.getenv("DISHA_IDENTITY_NFT_ADDRESS", "")
    DISHA_ANCHOR_CONFIRM_TIMEOUT_SECONDS: int = int(os.getenv("DISHA_ANCHOR_CONFIRM_TIMEOUT_SECONDS", "1800"))

    # AI assistance (blueprint 09). Empty provider/key = disabled (endpoints answer 503).
    DISHA_AI_PROVIDER: str = os.getenv("DISHA_AI_PROVIDER", "")  # "anthropic" or "" (disabled)
    DISHA_AI_API_KEY: str = os.getenv("DISHA_AI_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    DISHA_AI_MODEL: str = os.getenv("DISHA_AI_MODEL", "claude-sonnet-5-5")
    DISHA_AI_BASE_URL: str = os.getenv("DISHA_AI_BASE_URL", "https://api.anthropic.com")
    DISHA_AI_TIMEOUT_SECONDS: float = float(os.getenv("DISHA_AI_TIMEOUT_SECONDS", "30"))
    DISHA_AI_MAX_OUTPUT_TOKENS: int = int(os.getenv("DISHA_AI_MAX_OUTPUT_TOKENS", "800"))
    DISHA_AI_RATE_LIMIT_PER_USER_HOUR: int = int(os.getenv("DISHA_AI_RATE_LIMIT_PER_USER_HOUR", "30"))
    DISHA_AI_MONTHLY_TOKEN_BUDGET_PER_CAMPUS: int = int(os.getenv("DISHA_AI_MONTHLY_TOKEN_BUDGET_PER_CAMPUS", "2000000"))
    # AI-12: set true only once a data-processing agreement with the provider exists
    DISHA_AI_DPA_CONFIRMED: bool = os.getenv("DISHA_AI_DPA_CONFIRMED", "false").lower() in ("1", "true", "yes")

    # ML pipeline (rolling risk model). The bundle is a folder with model.joblib + manifest.json.
    DISHA_ML_BUNDLE_PATH: str = os.getenv(
        "DISHA_ML_BUNDLE_PATH", str(Path(__file__).resolve().parents[3] / "ml" / "artifacts_rolling"))
    DISHA_ML_MEKO_HOOKS: bool = os.getenv("DISHA_ML_MEKO_HOOKS", "true").lower() in ("1", "true", "yes")
    DISHA_ML_SCHEDULED_SCORING: bool = os.getenv("DISHA_ML_SCHEDULED_SCORING", "true").lower() in ("1", "true", "yes")
    DISHA_INGEST_MAX_BYTES: int = int(os.getenv("DISHA_INGEST_MAX_BYTES", str(50 * 1024 * 1024)))  # per uploaded file
    # Secret for pseudonymising campus student ids in score rows (falls back to MEKO_PII_SALT, then the JWT secret).
    DISHA_STUDENT_REF_SALT: str = os.getenv("DISHA_STUDENT_REF_SALT", "")

    # Supabase Auth: used to verify the Google sign-in token before issuing a DISHA JWT.
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://endyirtqxbepbndqayrh.supabase.co")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")  # only for legacy HS256 projects

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # shared .env also holds MEKO_*, web and worker keys
        case_sensitive = True

def _normalise_db_url(url: str) -> str:
    """Accept the plain `postgresql://` string Supabase shows and make it the asyncpg dialect."""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix):]
    return url


settings = Settings()
settings.DISHA_DATABASE_URL = _normalise_db_url(settings.DISHA_DATABASE_URL)
