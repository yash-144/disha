from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CaseAiRequest(BaseModel):
    case_id: str


class OutreachRequest(BaseModel):
    case_id: str
    channel: str = "email"  # email | sms | call_script
    tone: str = "supportive"  # supportive | formal


class EvidenceRequest(BaseModel):
    student_id: str


class AiResult(BaseModel):
    feature: str
    ai_status: str  # ok | unavailable | invalid_output
    advisory_only: bool = True
    prompt_version: str
    output: Optional[Dict[str, Any]] = None
    fallback: Optional[Dict[str, Any]] = None
    notice: str = "AI-generated suggestion. A staff member must review it; nothing here is acted on automatically."


class AiStatusResponse(BaseModel):
    enabled: bool
    provider: Optional[str] = None
    model: Optional[str] = None
    missing: List[str] = []
    message: Optional[str] = None
    governance: List[str] = [
        "Advisory text only; no tools and no write path",
        "Names, emails, roll numbers and phone numbers are redacted before sending",
        "Confidential counselling notes and fee data are never sent",
        "Every call is logged with a prompt hash, not the prompt",
    ]
