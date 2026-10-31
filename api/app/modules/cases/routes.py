from typing import List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import campus_role
from app.core.meko import catalog_entries, fire_and_forget, get_meko
from app.core.permissions import STAFF_ROLES
from app.modules.cases import schemas as sc
from app.modules.cases.repository import CaseRepository
from app.modules.cases.services import CasesService, allowed_targets
from app.core.exceptions import EntityNotFoundError

try:
    from disha_meko import playbook as pb
except ImportError:  # Meko is optional
    pb = None

router = APIRouter()
staff = campus_role(*STAFF_ROLES)  # staff role AND membership of the X-Campus-ID campus


def _campus(request: Request) -> str:
    return request.state.campus_id


def _actor(user: dict) -> Optional[str]:
    return str(user["sub"]) if user.get("sub") else None


@router.get("/", response_model=List[sc.CaseOut])
async def list_cases(request: Request, state: Optional[str] = None, db: AsyncSession = Depends(get_db),
                     _=Depends(staff)):
    return await CaseRepository(db).list(_campus(request), state)


@router.get("/outcomes/stats")
async def outcome_stats(request: Request, db: AsyncSession = Depends(get_db), _=Depends(staff)):
    """Outcome counts per (intervention, reason-code pattern): the Postgres source for Meko promotion."""
    return {"stats": await CaseRepository(db).outcome_counts(_campus(request))}


@router.post("/", response_model=sc.CaseOut, status_code=201)
async def create_case(body: sc.CaseCreate, request: Request, db: AsyncSession = Depends(get_db),
                      user: dict = Depends(staff)):
    return await CasesService(db).create_from_flag(
        _campus(request), _actor(user), body.flag_id, body.student_id, body.intervention_id,
        body.reason_codes, body.tier)


@router.get("/{case_id}")
async def get_case(case_id: str, request: Request, db: AsyncSession = Depends(get_db), _=Depends(staff)):
    repo = CaseRepository(db)
    case = await repo.get(_campus(request), case_id)
    if not case:
        raise EntityNotFoundError("Case", case_id)
    return {"case": sc.CaseOut.model_validate(case), "next_states": allowed_targets(case.state),
            "events": [sc.EventOut.model_validate(e) for e in await repo.events(case.campus_id, case_id)],
            "tasks": [sc.TaskOut.model_validate(t) for t in await repo.tasks(case.campus_id, case_id)]}


@router.post("/{case_id}/transition", response_model=sc.CaseOut)
async def transition_case(case_id: str, body: sc.Transition, request: Request, db: AsyncSession = Depends(get_db),
                          user: dict = Depends(staff)):
    return await CasesService(db).transition(_campus(request), case_id, _actor(user), user.get("roles", []),
                                             body.to_state, body.version, body.reason_code)


@router.post("/{case_id}/assign", response_model=sc.CaseOut)
async def assign_case(case_id: str, body: sc.Assign, request: Request, db: AsyncSession = Depends(get_db),
                      user: dict = Depends(staff)):
    return await CasesService(db).assign(_campus(request), case_id, _actor(user), body.owner_id, body.due_at,
                                         body.version, body.reason_code)


@router.post("/{case_id}/tasks", response_model=sc.TaskOut, status_code=201)
async def add_task(case_id: str, body: sc.TaskCreate, request: Request, db: AsyncSession = Depends(get_db),
                   user: dict = Depends(staff)):
    return await CasesService(db).add_task(_campus(request), case_id, _actor(user), body.domain, body.generic_label,
                                           body.assignee_id, body.due_at, body.restricted_details)


@router.post("/tasks/{task_id}/state", response_model=sc.TaskOut)
async def set_task_state(task_id: str, body: sc.TaskState, request: Request, db: AsyncSession = Depends(get_db),
                         user: dict = Depends(staff)):
    return await CasesService(db).set_task_state(_campus(request), task_id, _actor(user), body.to_state)


class FlagReview(BaseModel):
    flag_id: str
    student_id: str
    action: Literal["accept", "dismiss", "open_case", "start_intervention"]
    reason_codes: List[str] = Field(default_factory=list)
    tier: Optional[str] = None
    note: Optional[str] = Field(default=None, max_length=500)
    intervention_id: Optional[str] = None


@router.post("/flags/review")
async def review_flag(body: FlagReview, request: Request, tasks: BackgroundTasks,
                      db: AsyncSession = Depends(get_db), user: dict = Depends(staff), meko=Depends(get_meko)):
    """A human decides what to do with an ML flag (No Alert Without Action).

    open_case / start_intervention create the case (idempotent per flag); every decision is also recorded
    as a Meko decision trace so outcomes can later inform "what worked for similar profiles". IDs are hashed.
    """
    case_id = None
    if body.action in ("open_case", "start_intervention"):
        case = await CasesService(db).create_from_flag(_campus(request), _actor(user), body.flag_id, body.student_id,
                                                       body.intervention_id, body.reason_codes, body.tier)
        case_id = case.id
    role = (user.get("roles") or ["unknown"])[0]
    evidence = {"flag_id": body.flag_id, "student_id": body.student_id, "tier": body.tier,
                "reason_codes": body.reason_codes, "campus_id": getattr(request.state, "campus_id", None)}
    fire_and_forget(tasks, meko.trace_decision(
        decision=f"{role} chose '{body.action}' on an ML flag",
        rationale=(body.note or "") + f" Reason codes: {', '.join(body.reason_codes) or 'none'}.",
        outcome=f"Action '{body.action}' recorded for the flag (tier {body.tier or 'n/a'}).",
        plan=["Show the ML flag with its reason codes.", f"Human ({role}) chooses '{body.action}'.",
              "Record the decision so outcomes can inform later recalls."],
        evidence=evidence, actor=role))
    return {"flag_id": body.flag_id, "action": body.action, "recorded": True, "case_id": case_id}


@router.post("/{case_id}/outcome")
async def close_case(case_id: str, body: sc.CaseOutcomeIn, request: Request, tasks: BackgroundTasks,
                     db: AsyncSession = Depends(get_db), user: dict = Depends(staff), meko=Depends(get_meko)):
    """Persist the case outcome (Postgres is the source of truth), then feed Meko. The outcome becomes a Meko
    memory (hashed case id only); recurring good outcomes are promoted into the shared playbook (MEKO_PROMOTE_MIN).
    """
    entries = catalog_entries()
    if entries and body.intervention_id not in {str(e["id"]) for e in entries if e.get("active", True)}:
        raise HTTPException(422, "intervention_id is not an active intervention in the campus catalogue")
    campus = _campus(request)
    await CasesService(db).record_outcome(campus, case_id, _actor(user), body.outcome, body.intervention_id,
                                          body.reason_codes, body.tier, body.checkpoint)
    if pb is not None and meko.active:
        fire_and_forget(tasks, pb.record_outcome(
            meko, case_id=case_id, outcome=body.outcome, intervention_id=body.intervention_id,
            reason_codes=body.reason_codes, tier=body.tier, checkpoint=body.checkpoint, campus_id=campus))
    return {"case_id": case_id, "outcome": body.outcome, "recorded": True}
