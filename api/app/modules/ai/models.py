import uuid

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base
from app.shared.utils import utc_now


class AiCallLog(Base):
    """One row per AI call (AI-10). Stores a hash of the prompt, never the prompt or the output."""

    __tablename__ = "disha_ai_call_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    feature = Column(String(50), nullable=False)
    subject_type = Column(String(20), nullable=True)
    subject_id = Column(String(36), nullable=True)
    provider = Column(String(30), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_version = Column(String(20), nullable=False)
    prompt_hash = Column(String(64), nullable=False)
    status = Column(String(30), nullable=False)  # ok | unavailable | invalid_output | blocked
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Integer, nullable=False, default=0)
    redactions = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


# Backwards compatibility alias for initial scaffold references
AiEntity = AiCallLog
