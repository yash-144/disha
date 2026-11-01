"""Policy engine: turns ML risk flags into cases (blueprint 06 §3-6, 16 §7/§12, 07).

Guarantees
* Nothing opens a case without a policy: with no active version evaluation is refused (POL-01).
* A student with an open case is never re-flagged; a recently closed/dismissed case imposes a
  cooldown; capacity caps keep the highest-probability flags (16 §7 capacity cap).
* Cases start in `suggested` by default so a person still reviews each one (INV-01).
* Every case carries an evidence packet (06 §6) with a SHA-256 digest; policy changes are audited.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DishaBaseException, EntityNotFoundError
from app.modules.audit.services import AuditService
from app.modules.cases.models import Case, Signal
from app.modules.cases.schemas import CaseCreateRequest
from app.modules.cases.services import CaseService
from app.modules.policy.models import PolicyDecision, PolicyEvaluation, PolicyVersion
from app.modules.policy.schemas import (
    PRIORITY_RANK,
    TIER_RANK,
    DecisionResponse,
    PolicyDefinition,
    PolicyEvaluationResult,
    PolicyVersionCreate,
    PolicyVersionUpdate,
    RiskFlagIn,
)
from app.modules.roster.models import Student
from app.shared.enums import CaseState, map_status_to_state
from app.shared.utils import utc_now

TERMINAL_STATES = {CaseState.CLOSED, CaseState.DISMISSED}
LIMITATIONS = [
    "Uses only data available on or before the cutoff.",
    "Indicates a need for review; it is not a diagnosis.",
]


class PolicyError(DishaBaseException):
    pass


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def checksum_of(definition: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(definition).encode("utf-8")).hexdigest()


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _actor_roles(actor: Any) -> List[str]:
    role = getattr(actor, "role", None)
    roles = [role.value if hasattr(role, "value") else str(role)] if role else []
    if getattr(actor, "is_platform_admin", False):
        roles.append("platform_admin")
    return roles


class PolicyService:
    """CRUD for versioned policies. Published versions are immutable (POL-02)."""

    @staticmethod
    async def _get(db: AsyncSession, campus_id: str, version_id: str) -> PolicyVersion:
        res = await db.execute(
            select(PolicyVersion).where(PolicyVersion.id == version_id, PolicyVersion.campus_id == campus_id)
        )
        pv = res.scalar_one_or_none()
        if not pv:
            raise EntityNotFoundError("PolicyVersion", version_id)
        return pv

    get_version = _get

    @staticmethod
    async def list_versions(db: AsyncSession, campus_id: str, status: Optional[str] = None) -> List[PolicyVersion]:
        stmt = select(PolicyVersion).where(PolicyVersion.campus_id == campus_id)
        if status:
            stmt = stmt.where(PolicyVersion.status == status)
        res = await db.execute(stmt.order_by(PolicyVersion.version.desc()))
        return list(res.scalars().all())

    @staticmethod
    async def get_active(db: AsyncSession, campus_id: str) -> Optional[PolicyVersion]:
        res = await db.execute(
            select(PolicyVersion).where(PolicyVersion.campus_id == campus_id, PolicyVersion.status == "active")
        )
        return res.scalars().first()

    @staticmethod
    async def create_version(db: AsyncSession, campus_id: str, actor_id: str, data: PolicyVersionCreate) -> PolicyVersion:
        next_v = (await db.scalar(
            select(func.coalesce(func.max(PolicyVersion.version), 0)).where(PolicyVersion.campus_id == campus_id)
        )) + 1
        definition = data.definition.model_dump(mode="json")
        pv = PolicyVersion(
            campus_id=campus_id, version=next_v, status="draft", definition=definition,
            checksum=checksum_of(definition), note=data.note, created_by=actor_id,
        )
        db.add(pv)
        await db.flush()
        await AuditService.record_event(
            db, actor_id, campus_id, "policy_version", pv.id, "POLICY_VERSION_CREATED",
            {"version": pv.version, "checksum": pv.checksum},
        )
        return pv

    @staticmethod
    async def update_version(
        db: AsyncSession, campus_id: str, actor_id: str, version_id: str, data: PolicyVersionUpdate
    ) -> PolicyVersion:
        pv = await PolicyService._get(db, campus_id, version_id)
        if pv.status != "draft":
            raise PolicyError("Published policy versions are immutable; create a new version", 409)
        if data.definition is not None:
            pv.definition = data.definition.model_dump(mode="json")
            pv.checksum = checksum_of(pv.definition)
        if data.note is not None:
            pv.note = data.note
        await db.flush()
        await AuditService.record_event(
            db, actor_id, campus_id, "policy_version", pv.id, "POLICY_VERSION_UPDATED",
            {"version": pv.version, "checksum": pv.checksum},
        )
        return pv

    @staticmethod
    async def delete_version(db: AsyncSession, campus_id: str, actor_id: str, version_id: str) -> None:
        pv = await PolicyService._get(db, campus_id, version_id)
        if pv.status != "draft":
            raise PolicyError("Only draft policy versions can be deleted", 409)
        await AuditService.record_event(
            db, actor_id, campus_id, "policy_version", pv.id, "POLICY_VERSION_DELETED",
            {"version": pv.version, "checksum": pv.checksum},
        )
        await db.delete(pv)
        await db.flush()

    @staticmethod
    async def publish_version(db: AsyncSession, campus_id: str, actor_id: str, version_id: str) -> PolicyVersion:
        pv = await PolicyService._get(db, campus_id, version_id)
        if pv.status != "draft":
            raise PolicyError("Only a draft policy version can be published", 409)
        PolicyDefinition.model_validate(pv.definition)  # schema re-validated on publish (POL-04)
        now = utc_now()
        previous = await PolicyService.get_active(db, campus_id)
        if previous:
            previous.status = "retired"
            previous.retired_at = now
            await db.flush()  # retire first so the one-active-per-campus index is never violated
        pv.status = "active"
        pv.published_by = actor_id
        pv.published_at = now
        await db.flush()
        await AuditService.record_event(
            db, actor_id, campus_id, "policy_version", pv.id, "POLICY_VERSION_PUBLISHED",
            {"version": pv.version, "checksum": pv.checksum, "retired_version": previous.version if previous else None},
        )
        return pv

    @staticmethod
    async def list_evaluations(db: AsyncSession, campus_id: str, limit: int = 50, offset: int = 0) -> List[PolicyEvaluation]:
        res = await db.execute(
            select(PolicyEvaluation).where(PolicyEvaluation.campus_id == campus_id)
            .order_by(PolicyEvaluation.created_at.desc(), PolicyEvaluation.id.desc()).limit(limit).offset(offset)
        )
        return list(res.scalars().all())

    @staticmethod
    async def get_evaluation(db: AsyncSession, campus_id: str, evaluation_id: str):
        res = await db.execute(
            select(PolicyEvaluation).where(PolicyEvaluation.id == evaluation_id, PolicyEvaluation.campus_id == campus_id)
        )
        ev = res.scalar_one_or_none()
        if not ev:
            raise EntityNotFoundError("PolicyEvaluation", evaluation_id)
        dres = await db.execute(
            select(PolicyDecision).where(PolicyDecision.evaluation_id == ev.id).order_by(PolicyDecision.created_at, PolicyDecision.id)
        )
        return ev, list(dres.scalars().all())


# ---- evaluation --------------------------------------------------------------------------

def _qualify(flag: Any, policy: PolicyDefinition):
    """Return (qualifies, priority, due_in_days, matched_rule_keys, via) for one flag."""
    tier = flag.tier
    prob = float(flag.probability)
    cfg = policy.tiers.get(tier) if tier in ("high", "medium", "watch") else None
    by_tier = bool(cfg and cfg.enabled and prob >= cfg.min_probability)
    priority = cfg.priority if by_tier else None
    due = cfg.due_in_days if by_tier else None

    matched = []
    opened_by_rule = False
    for rule in policy.reason_rules:
        if TIER_RANK.get(tier, 0) < TIER_RANK[rule.min_tier]:
            continue
        hit = any(
            r.get("group") in rule.reason_groups and abs(float(r.get("effect_pts") or 0)) >= rule.min_effect_pts
            for r in (flag.reasons or [])
        )
        if not hit:
            continue
        if rule.action == "open_case":
            opened_by_rule = True
            matched.append(rule.rule_key)
            priority = priority if priority and PRIORITY_RANK[priority] >= PRIORITY_RANK[rule.priority] else rule.priority
        elif by_tier:
            matched.append(rule.rule_key)
            if PRIORITY_RANK[rule.priority] > PRIORITY_RANK[priority]:
                priority = rule.priority
    qualifies = by_tier or opened_by_rule
    return qualifies, priority, due, matched, ("tier" if by_tier else "rule")


def build_evidence_packet(flag: Any, pv: PolicyVersion, priority: str, matched: List[str], via: str) -> Dict[str, Any]:
    as_of = getattr(flag, "as_of", None)
    items = [{
        "metric_key": "risk_probability",
        "observed": round(float(flag.probability), 4),
        "rule": f"tier={flag.tier}",
        "source": "ml_model",
    }]
    for r in (flag.reasons or [])[:5]:
        items.append({
            "metric_key": r.get("group"), "observed": r.get("values"), "text": r.get("text"),
            "effect_pts": r.get("effect_pts"), "source": "ml_reason",
        })
    packet = {
        "card_type": "ml_risk_evidence",
        "source": {"policy_version_id": pv.id, "policy_version": pv.version, "policy_checksum": pv.checksum},
        "cutoff": as_of.isoformat() if hasattr(as_of, "isoformat") else (str(as_of) if as_of is not None else None),
        "classification": "attention_suggested",
        "tier": flag.tier,
        "opened_via": via,
        "priority": priority,
        "matched_rules": matched,
        "model_version": flag.model_version,
        "score_id": flag.score_id,
        "course_ref": flag.course_ref,
        "external_student_ref_hash": flag.external_student_ref_hash,
        "items": items,
        "limitations": LIMITATIONS,
    }
    packet["digest"] = hashlib.sha256(canonical_json(packet).encode("utf-8")).hexdigest()
    return packet


async def _open_and_recent(db: AsyncSession, campus_id: str, student_ids: Sequence[str]):
    """-> (students with an open case, {student: latest terminal-case timestamp}, total open cases)."""
    open_students: set = set()
    last_closed: Dict[str, datetime] = {}
    if student_ids:
        res = await db.execute(
            select(Case.student_id, Case.status, Case.closed_at, Case.updated_at)
            .where(Case.campus_id == campus_id, Case.student_id.in_(list(student_ids)))
        )
        for sid, status, closed_at, updated_at in res.all():
            if map_status_to_state(status) in TERMINAL_STATES:
                ts = _aware(closed_at or updated_at)
                if ts and (sid not in last_closed or ts > last_closed[sid]):
                    last_closed[sid] = ts
            else:
                open_students.add(sid)
    open_total = 0
    res = await db.execute(select(Case.status, func.count()).where(Case.campus_id == campus_id).group_by(Case.status))
    for status, n in res.all():
        if map_status_to_state(status) not in TERMINAL_STATES:
            open_total += n
    return open_students, last_closed, open_total


async def evaluate_risk_flags(
    session: AsyncSession,
    campus_id: str,
    flags: List[RiskFlagIn],
    actor: Any,
    *,
    dry_run: bool = False,
    policy_version_id: Optional[str] = None,
    commit: bool = True,
) -> PolicyEvaluationResult:
    """Apply the campus's active policy (or `policy_version_id`) to ML risk flags.

    `actor` needs `.user_id` and `.role` (a TenancyContext works). With dry_run nothing is written.
    With commit=False the caller owns the transaction (work is flushed, not committed).
    """
    if policy_version_id:
        pv = await PolicyService.get_version(session, campus_id, policy_version_id)
    else:
        pv = await PolicyService.get_active(session, campus_id)
        if pv is None:
            raise PolicyError("No active policy for this campus; publish a policy version first", 409)
    policy = PolicyDefinition.model_validate(pv.definition)
    actor_id = actor.user_id
    roles = _actor_roles(actor)
    now = utc_now()

    skipped: Dict[str, int] = {}
    outcomes: List[Dict[str, Any]] = []

    def skip(flag: Any, code: str) -> None:
        skipped[code] = skipped.get(code, 0) + 1
        outcomes.append({"flag": flag, "decision": "skipped", "reason_code": code})

    # 1. Cheap per-flag screening and in-batch dedupe (keep the highest probability per student).
    candidates: List[Any] = []
    for f in sorted(flags, key=lambda x: float(x.probability), reverse=True):
        if f.tier == "none":
            continue  # nothing to explain for on-track students
        if f.campus_id != campus_id:
            skip(f, "campus_mismatch")
        elif not f.student_id:
            skip(f, "unlinked_student")
        else:
            candidates.append(f)

    known: set = set()
    if candidates:
        res = await session.execute(
            select(Student.id).where(Student.campus_id == campus_id, Student.id.in_({f.student_id for f in candidates}))
        )
        known = set(res.scalars().all())
    seen: set = set()
    eligible: List[Any] = []
    for f in candidates:
        if f.student_id not in known:
            skip(f, "unknown_student")
        elif f.student_id in seen:
            skip(f, "duplicate_in_batch")
        else:
            seen.add(f.student_id)
            eligible.append(f)

    open_students, last_closed, open_total = await _open_and_recent(session, campus_id, [f.student_id for f in eligible])
    cooldown = timedelta(days=policy.cooldown_days)
    created = 0
    cap_run = policy.capacity.max_new_cases_per_evaluation
    cap_open = policy.capacity.max_open_cases

    for f in eligible:  # already ordered by probability desc
        qualifies, priority, due_days, matched, via = _qualify(f, policy)
        if not qualifies:
            skip(f, "below_threshold")
            continue
        if f.student_id in open_students:
            skip(f, "open_case_exists")
            continue
        closed_ts = last_closed.get(f.student_id)
        if closed_ts and policy.cooldown_days and now - closed_ts < cooldown:
            skip(f, "cooldown_active")
            continue
        if cap_run is not None and created >= cap_run:
            skip(f, "capacity_per_evaluation")
            continue
        if cap_open is not None and open_total + created >= cap_open:
            skip(f, "capacity_open_cases")
            continue

        packet = build_evidence_packet(f, pv, priority, matched, via)
        outcome = {"flag": f, "decision": "case_created", "reason_code": "policy_match", "packet": packet}
        if not dry_run:
            reasons_txt = "; ".join(str(r.get("text")) for r in (f.reasons or [])[:3] if r.get("text"))
            title = f"{f.tier.capitalize()} risk flag: support review suggested"
            signal = Signal(
                campus_id=campus_id, student_id=f.student_id, rule_key=f"ml_risk_{f.tier}",
                result="attention_suggested", ml_risk_probability=float(f.probability), ml_tier=f.tier,
                evidence_snapshot=canonical_json(packet),
            )
            session.add(signal)
            await session.flush()
            case = await CaseService.create_case(
                db=session, campus_id=campus_id, actor_id=actor_id, actor_roles=roles,
                data=CaseCreateRequest(
                    student_id=f.student_id, title=title,
                    description=(reasons_txt or "Flagged by the risk model; see evidence packet.") +
                                f"\nPolicy v{pv.version}, model {f.model_version}.",
                    priority=priority, initial_state=policy.initial_state,
                    due_date=(now + timedelta(days=due_days)) if due_days else None,
                ),
            )
            case.originating_signal_id = signal.id
            await session.flush()
            outcome.update(case_id=case.id, signal_id=signal.id)
        created += 1
        open_students.add(f.student_id)
        outcomes.append(outcome)

    evaluation_id: Optional[str] = None
    decisions: List[DecisionResponse] = []
    if not dry_run:
        ev = PolicyEvaluation(
            campus_id=campus_id, policy_version_id=pv.id, actor_id=actor_id,
            flags_received=len(flags), cases_created=created, skipped_summary=skipped,
        )
        session.add(ev)
        await session.flush()
        evaluation_id = ev.id
    for o in outcomes:
        f = o["flag"]
        packet = o.get("packet")
        row = PolicyDecision(
            evaluation_id=evaluation_id or "", campus_id=campus_id, student_id=f.student_id,
            external_student_ref_hash=f.external_student_ref_hash, course_ref=f.course_ref, tier=f.tier,
            probability=float(f.probability), score_id=f.score_id, decision=o["decision"],
            reason_code=o["reason_code"], case_id=o.get("case_id"), signal_id=o.get("signal_id"),
            evidence=packet, digest=packet["digest"] if packet else None,
        )
        if not dry_run:
            session.add(row)
        decisions.append(DecisionResponse(
            student_id=f.student_id, external_student_ref_hash=f.external_student_ref_hash, course_ref=f.course_ref,
            tier=f.tier, probability=float(f.probability), decision=o["decision"], reason_code=o["reason_code"],
            case_id=o.get("case_id"), digest=row.digest, evidence=packet,
        ))
    if not dry_run:
        await session.flush()
        await AuditService.record_event(
            session, actor_id, campus_id, "policy_evaluation", evaluation_id, "POLICY_EVALUATED",
            {"policy_version": pv.version, "flags_received": len(flags), "cases_created": created, "skipped": skipped},
        )
        if commit:
            await session.commit()

    return PolicyEvaluationResult(
        evaluation_id=evaluation_id, policy_version_id=pv.id, policy_version=pv.version, dry_run=dry_run,
        flags_received=len(flags), cases_created=created, skipped=skipped, decisions=decisions,
    )
