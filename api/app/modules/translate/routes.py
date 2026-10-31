import asyncio
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.modules.translate import service
from app.modules.translate.languages import to_flores

router = APIRouter()
MAX_TEXTS, MAX_CHARS = 32, 2000


class TranslateRequest(BaseModel):
    text: Optional[str] = Field(default=None, min_length=1, max_length=MAX_CHARS)
    texts: Optional[List[str]] = Field(default=None, min_length=1, max_length=MAX_TEXTS)
    source_lang: str  # FLORES (hin_Deva) or BCP-47 (hi-IN)
    target_lang: str

    @model_validator(mode="after")
    def _check(self):
        if (self.text is None) == (self.texts is None):
            raise ValueError("Send exactly one of 'text' or 'texts'")
        if self.texts and any(not t.strip() or len(t) > MAX_CHARS for t in self.texts):
            raise ValueError(f"Each text must be 1-{MAX_CHARS} characters")
        try:
            self.source_lang, self.target_lang = to_flores(self.source_lang), to_flores(self.target_lang)
            service.direction(self.source_lang, self.target_lang)
        except ValueError as exc:
            raise ValueError(str(exc)) from None
        return self


class TranslateResponse(BaseModel):
    source_lang: str
    target_lang: str
    translations: List[str]


@router.post("", response_model=TranslateResponse)
async def translate(body: TranslateRequest, _=Depends(get_current_user)):
    """Translate English <-> Indic text locally with IndicTrans2 (flag DISHA_TRANSLATE_ENABLED)."""
    if not settings.DISHA_TRANSLATE_ENABLED:
        raise HTTPException(503, "Translation is disabled (set DISHA_TRANSLATE_ENABLED=true)")
    texts = [body.text] if body.text is not None else body.texts
    try:
        out = await asyncio.to_thread(service.translate, texts, body.source_lang, body.target_lang)
    except RuntimeError as exc:  # optional extra not installed
        raise HTTPException(503, str(exc))
    return TranslateResponse(source_lang=body.source_lang, target_lang=body.target_lang, translations=out)
