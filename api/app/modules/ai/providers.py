"""Swappable LLM providers. There is no mock/fallback provider here (AI-03): tests inject their own through
`set_provider_override`. If configuration is incomplete the AI feature is disabled, never faked."""
import logging
from dataclasses import dataclass
from typing import List, Optional, Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger("disha.ai")


class ProviderError(Exception):
    pass


@dataclass
class ProviderResult:
    text: str
    input_tokens: int
    output_tokens: int


class AiProvider(Protocol):
    name: str
    model: str

    async def complete(self, system: str, user: str, max_tokens: int) -> ProviderResult: ...


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float):
        self._key = api_key
        self.model = model
        self._url = base_url.rstrip("/") + "/v1/messages"
        self._timeout = timeout

    async def complete(self, system: str, user: str, max_tokens: int) -> ProviderResult:
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {"x-api-key": self._key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(self._url, json=body, headers=headers)
        except httpx.HTTPError as exc:
            raise ProviderError(f"provider request failed: {type(exc).__name__}") from exc
        if resp.status_code != 200:
            raise ProviderError(f"provider returned HTTP {resp.status_code}")
        try:
            data = resp.json()
            text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
            usage = data.get("usage", {})
            return ProviderResult(text, int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0)))
        except (ValueError, AttributeError, TypeError) as exc:
            raise ProviderError("provider response was not understood") from exc


_override: Optional[AiProvider] = None


def set_provider_override(provider: Optional[AiProvider]) -> None:
    """Test hook / explicit injection of any object implementing AiProvider."""
    global _override
    _override = provider


def ai_missing_settings() -> List[str]:
    missing: List[str] = []
    provider = (settings.DISHA_AI_PROVIDER or "").strip().lower()
    if not provider:
        missing.append("DISHA_AI_PROVIDER")
    elif provider != "anthropic":
        missing.append(f"DISHA_AI_PROVIDER (unknown provider '{provider}'; supported: anthropic)")
    if not settings.DISHA_AI_API_KEY:
        missing.append("DISHA_AI_API_KEY")
    if not settings.DISHA_AI_DPA_CONFIRMED:
        missing.append("DISHA_AI_DPA_CONFIRMED (data-processing agreement, AI-12)")
    return missing


def get_provider() -> Optional[AiProvider]:
    if _override is not None:
        return _override
    if ai_missing_settings():
        return None
    return AnthropicProvider(
        settings.DISHA_AI_API_KEY, settings.DISHA_AI_MODEL, settings.DISHA_AI_BASE_URL, settings.DISHA_AI_TIMEOUT_SECONDS
    )


def provider_status() -> dict:
    if _override is not None:
        return {"enabled": True, "provider": _override.name, "model": _override.model, "missing": []}
    missing = ai_missing_settings()
    if missing:
        return {
            "enabled": False, "missing": missing,
            "message": "AI assistance is disabled: set " + ", ".join(missing) + ".",
        }
    return {"enabled": True, "provider": settings.DISHA_AI_PROVIDER.lower(), "model": settings.DISHA_AI_MODEL, "missing": []}
