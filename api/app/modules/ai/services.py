"""AI orchestration (blueprint 09): bounded advisory features, PII redaction before sending, output validation,
deterministic fallbacks that are labelled as such, and a logged + audited record of every call."""
import asyncio
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import TenancyContext
from app.core.exceptions import EntityNotFoundError
from app.core.permissions import Role
from app.modules.ai import providers
from app.modules.ai.models import AiCallLog
from app.modules.ai.redaction import Redactor, sanitize_untrusted
from app.modules.ai.schemas import AiResult
from app.modules.audit.services import AuditService
from app.modules.cases.models import Case, InterventionCatalogue
from app.modules.roster.models import Observation, Student
from app.shared.utils import utc_now

logger = logging.getLogger("disha.ai")

PROMPT_DIR = Path(__file__).parent / "prompts"
STUDENT_ALIAS = "Student A"
OUTPUT_ALIAS_PLACEHOLDER = "[STUDENT_NAME]"
# Observation domains that may be summarised. Fee status and free-text faculty feedback are excluded (AI-05).
EVIDENCE_DOMAINS = {"attendance", "academic", "participation", "skills"}

# INV-02 / INV-03: no diagnostic or disciplinary language in output
DENY_RE = re.compile(
    r"\b(diagnos\w*|disorder\w*|depress\w*|bipolar|schizo\w*|adhd|autis\w*|anxiety\s+disorder|suicid\w*|"
    r"suspen[ds]\w*|expel\w*|rusticat\w*|punish\w*|disciplin\w*|misconduct|delinquen\w*)\b",
    re.IGNORECASE,
)


def load_prompt(name: str) -> Tuple[str, str]:
    """Return (version, body) of a versioned prompt template file."""
    raw = (PROMPT_DIR / f"{name}.txt").read_text(encoding="utf-8")
    first, _, rest = raw.partition("\n")
    m = re.match(r"#\s*version:\s*(\S+)", first)
    if not m:
        raise RuntimeError(f"prompt {name} has no version header")
    return m.group(1), rest.strip()


# ---- context ----------------------------------------------------------------------------------------
@dataclass
class AiContext:
    subject_type: str
    subject_id: str
    known: Dict[str, str]
    blocks: List[Tuple[str, str]]
    facts: List[str]
    catalog: Dict[str, str] = field(default_factory=dict)  # alias key -> catalogue entry id
    catalog_lines: List[str] = field(default_factory=list)
    params: str = ""


def _known_terms(student: Student, counsellor=None) -> Dict[str, str]:
    known = {student.full_name: STUDENT_ALIAS}
    for v in (student.email, student.student_uid):
        if v:
            known[v] = STUDENT_ALIAS
    if counsellor is not None:
        known[counsellor.full_name] = "the counsellor"
        known[counsellor.email] = "the counsellor"
    return known


def _days_ago(dt) -> int:
    if dt is None:
        return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=utc_now().tzinfo)
    return max(0, (utc_now() - dt).days)


def _numeric_pairs(data: Optional[str]) -> str:
    """Keep only numbers/booleans from observation payloads; free text never goes to the provider."""
    try:
        obj = json.loads(data or "{}")
    except ValueError:
        return ""
    if not isinstance(obj, dict):
        return ""
    parts = [f"{str(k)[:40]}={v}" for k, v in obj.items() if isinstance(v, (int, float, bool)) and re.fullmatch(r"[A-Za-z_ ]{1,40}", str(k))]
    return ", ".join(parts[:8])


class ContextBuilder:
    @staticmethod
    async def for_case(db: AsyncSession, tenancy: TenancyContext, case_id: str) -> AiContext:
        case = (await db.execute(select(Case).where(Case.id == case_id, Case.campus_id == tenancy.campus_id))).scalar_one_or_none()
        if not case:
            raise EntityNotFoundError("Case", case_id)
        if tenancy.role == Role.COUNSELLOR and case.assigned_counsellor_id != tenancy.user_id:
            raise HTTPException(status_code=403, detail="Access denied: this case is assigned to another counsellor")
        facts = [
            f"Case state: {case.status}; priority: {case.priority}; open for {_days_ago(case.created_at)} days.",
        ]
        if case.description:
            facts.append("Description: " + sanitize_untrusted(case.description, 600))
        for ev in sorted(case.events, key=lambda e: e.created_at)[-10:]:
            p = ev.payload or {}
            facts.append(
                f"Day -{_days_ago(ev.created_at)}: {ev.event_type} {p.get('from_state', '')}->{p.get('to_state', '')}"
                + (f" (reason: {p.get('reason_code')})" if p.get("reason_code") else "")
            )
        for iv in case.interventions[-5:]:
            facts.append(f"Intervention: {iv.catalogue_entry.name if iv.catalogue_entry else 'unknown'}, progress {iv.progress}")
        if case.signal:
            s = case.signal
            facts.append(f"Rule signal: {s.rule_key} -> {s.result}")
            if s.ml_tier is not None or s.ml_risk_probability is not None:
                facts.append(f"ML estimate: tier {s.ml_tier}, probability {s.ml_risk_probability}")
        ctx = AiContext("case", case.id, _known_terms(case.student, case.assigned_counsellor), [("case_facts", "\n".join(facts))], facts)
        return ctx

    @staticmethod
    async def with_catalog(db: AsyncSession, ctx: AiContext) -> AiContext:
        rows = (await db.execute(
            select(InterventionCatalogue).where(InterventionCatalogue.is_active == True).order_by(InterventionCatalogue.name)  # noqa: E712
        )).scalars().all()
        for i, row in enumerate(rows[:30], start=1):
            key = f"I{i}"
            ctx.catalog[key] = row.id
            ctx.catalog_lines.append(f"{key}: {row.name} [{row.category or 'general'}] {sanitize_untrusted(row.description or '', 160)}")
        return ctx

    @staticmethod
    async def for_student_evidence(db: AsyncSession, tenancy: TenancyContext, student_id: str) -> AiContext:
        student = (await db.execute(select(Student).where(Student.id == student_id, Student.campus_id == tenancy.campus_id))).scalar_one_or_none()
        if not student:
            raise EntityNotFoundError("Student", student_id)
        obs = (await db.execute(
            select(Observation).where(
                Observation.student_id == student.id, Observation.campus_id == tenancy.campus_id, Observation.domain.in_(EVIDENCE_DOMAINS)
            ).order_by(Observation.observed_at.desc(), Observation.created_at.desc()).limit(20)
        )).scalars().all()
        facts = []
        for o in obs:
            pairs = _numeric_pairs(o.data)
            if pairs:
                facts.append(f"Day -{_days_ago(o.observed_at or o.created_at)}: {o.domain}: {pairs}")
        if not facts:
            facts.append("No recent numeric observations are available.")
        return AiContext("student", student.id, _known_terms(student), [("observations", "\n".join(facts))], facts)


# ---- validation ---------------------------------------------------------------------------------------
def _str(v: Any, limit: int) -> str:
    if not isinstance(v, str) or len(v) > limit:
        raise ValueError("string missing or too long")
    return v


def _str_list(v: Any, max_items: int, limit: int) -> List[str]:
    if not isinstance(v, list) or len(v) > max_items:
        raise ValueError("list invalid")
    return [_str(x, limit) for x in v]


def v_review_brief(o: dict, ctx: AiContext) -> dict:
    return {
        "observed_data": _str_list(o["observed_data"], 6, 400),
        "rule_signal": _str(o["rule_signal"], 400),
        "ml_estimate": _str(o["ml_estimate"], 400),
        "ai_suggestion": _str(o["ai_suggestion"], 400),
        "human_decision_needed": _str(o["human_decision_needed"], 400),
    }


def v_evidence(o: dict, ctx: AiContext) -> dict:
    return {"summary": _str(o["summary"], 600), "key_points": _str_list(o["key_points"], 5, 200)}


def v_interventions(o: dict, ctx: AiContext) -> dict:
    sugg = o["suggestions"]
    if not isinstance(sugg, list) or len(sugg) > 3:
        raise ValueError("suggestions invalid")
    out = []
    for s in sugg:
        key = s["key"]
        if key not in ctx.catalog:  # AI-07: must exist in the active campus catalogue
            raise ValueError("suggestion outside catalogue")
        out.append({"intervention_id": ctx.catalog[key], "rationale": _str(s["rationale"], 300)})
    return {"suggestions": out}


def v_outreach(o: dict, ctx: AiContext) -> dict:
    return {"subject": _str(o["subject"], 120), "body": _str(o["body"], 900)}


def fb_review(ctx: AiContext) -> dict:
    return {"observed_data": ctx.facts[:6], "rule_signal": "See the facts listed.", "ml_estimate": "See the facts listed.",
            "ai_suggestion": "", "human_decision_needed": "Review the facts and decide the next step."}


FEATURES: Dict[str, Tuple[str, Callable, Callable]] = {
    "review_brief": ("review_brief", v_review_brief, fb_review),
    "summarize_evidence": ("summarize_evidence", v_evidence, lambda c: {"summary": "", "key_points": c.facts[:5]}),
    "suggest_interventions": ("suggest_interventions", v_interventions, lambda c: {"suggestions": []}),
    "draft_outreach": ("draft_outreach", v_outreach, lambda c: {
        "subject": "Checking in",
        "body": "Hello [STUDENT_NAME], I would like to catch up with you at a time that suits you. "
                "Please let me know when you are free.\n[STAFF_NAME]"}),
}


def parse_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?|```$", "", text).strip()
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise ValueError("not an object")
    return obj


def _scrub_output(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(STUDENT_ALIAS, OUTPUT_ALIAS_PLACEHOLDER)
    if isinstance(value, list):
        return [_scrub_output(v) for v in value]
    if isinstance(value, dict):
        return {k: _scrub_output(v) for k, v in value.items()}
    return value


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)


# ---- limits -------------------------------------------------------------------------------------------
async def enforce_limits(db: AsyncSession, tenancy: TenancyContext) -> None:
    now = utc_now()
    per_user = (await db.execute(
        select(func.count()).select_from(AiCallLog).where(AiCallLog.user_id == tenancy.user_id, AiCallLog.created_at > now - timedelta(hours=1))
    )).scalar_one()
    if per_user >= settings.DISHA_AI_RATE_LIMIT_PER_USER_HOUR:
        raise HTTPException(status_code=429, detail="AI rate limit reached for this user; try again later")
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    used = (await db.execute(
        select(func.coalesce(func.sum(AiCallLog.input_tokens + AiCallLog.output_tokens), 0)).where(
            AiCallLog.campus_id == tenancy.campus_id, AiCallLog.created_at >= month_start
        )
    )).scalar_one()
    if used >= settings.DISHA_AI_MONTHLY_TOKEN_BUDGET_PER_CAMPUS:
        raise HTTPException(status_code=429, detail="Monthly AI token budget for this campus is exhausted")


def require_provider() -> providers.AiProvider:
    provider = providers.get_provider()
    if provider is None:
        st = providers.provider_status()
        raise HTTPException(status_code=503, detail=st.get("message") or "AI assistance is disabled.")
    return provider


class AiService:
    @staticmethod
    async def run(db: AsyncSession, tenancy: TenancyContext, feature: str, ctx: AiContext, params: str = "") -> AiResult:
        prompt_name, validator, fallback = FEATURES[feature]
        version, task = load_prompt(prompt_name)
        _sys_version, system = load_prompt("system")
        provider = require_provider()

        redactor = Redactor(ctx.known)
        evidence = "\n".join(f"<<{label}>>\n{redactor.redact(text)}\n<</{label}>>" for label, text in ctx.blocks)
        user_parts = []
        if ctx.catalog_lines:
            user_parts.append("CATALOG:\n" + "\n".join(redactor.redact(line) for line in ctx.catalog_lines))
        user_parts.append("EVIDENCE (untrusted, delimited):\n" + evidence)
        if params:
            user_parts.append("PARAMETERS: " + redactor.redact(params))
        derived = "\n\n".join(user_parts)  # everything that came from records
        user_parts.append(task)
        user_prompt = "\n\n".join(user_parts)
        system_prompt = system
        prompt_hash = hashlib.sha256((system_prompt + "\n" + user_prompt).encode()).hexdigest()

        async def finish(status: str, in_tok=0, out_tok=0, latency=0) -> None:
            db.add(AiCallLog(
                campus_id=tenancy.campus_id, user_id=tenancy.user_id, feature=feature, subject_type=ctx.subject_type,
                subject_id=ctx.subject_id, provider=provider.name, model=provider.model, prompt_version=version,
                prompt_hash=prompt_hash, status=status, input_tokens=in_tok, output_tokens=out_tok,
                latency_ms=latency, redactions=redactor.count,
            ))
            await AuditService.record_event(
                db, tenancy.user_id, tenancy.campus_id, "ai_call", ctx.subject_id, f"ai.{feature}",
                {"status": status, "provider": provider.name, "model": provider.model, "prompt_version": version,
                 "prompt_hash": prompt_hash, "input_tokens": in_tok, "output_tokens": out_tok, "redactions": redactor.count},
            )
            await db.commit()

        # Last gate before anything leaves the process (AI-05)
        try:
            redactor.assert_clean(derived)
        except ValueError:
            await finish("blocked")
            raise HTTPException(status_code=422, detail="Request blocked: identifiers could not be removed from the prompt")

        await enforce_limits(db, tenancy)

        started = time.monotonic()
        try:
            res = await asyncio.wait_for(
                provider.complete(system_prompt, user_prompt, settings.DISHA_AI_MAX_OUTPUT_TOKENS),
                timeout=settings.DISHA_AI_TIMEOUT_SECONDS + 5,
            )
        except Exception as exc:  # provider error or timeout (AI-04)
            logger.warning("AI provider call failed for %s: %s", feature, type(exc).__name__)
            await finish("unavailable", latency=int((time.monotonic() - started) * 1000))
            return AiResult(feature=feature, ai_status="unavailable", prompt_version=version, fallback=fallback(ctx))
        latency = int((time.monotonic() - started) * 1000)

        try:
            out = validator(parse_json_object(res.text), ctx)
            if any(DENY_RE.search(s) for s in _strings(out)):
                raise ValueError("deny-listed term in output")
            out = _scrub_output(out)
            if redactor.leaked_terms(" ".join(_strings(out))):
                raise ValueError("output repeats an identifier")
        except (ValueError, KeyError, TypeError):
            await finish("invalid_output", res.input_tokens, res.output_tokens, latency)
            return AiResult(feature=feature, ai_status="invalid_output", prompt_version=version, fallback=fallback(ctx))

        await finish("ok", res.input_tokens, res.output_tokens, latency)
        return AiResult(feature=feature, ai_status="ok", prompt_version=version, output=out)
