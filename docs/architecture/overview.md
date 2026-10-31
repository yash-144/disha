# DISHA System Architecture Overview

DISHA operates on a multi-tiered architecture:
1. Client: Next.js 14 web app and Rust CLI.
2. API Gateway & Logic: Modular FastAPI backend with domain-driven boundaries.
3. Event Processing & Async Tasks: Background worker with transactional outbox.
4. Persistence: PostgreSQL with Row-Level Security (RLS) for strict multi-campus isolation.
5. Trust Layer: On-chain immutable hash anchoring.

## Case lifecycle, campus access, outbox and translation

- **Cases** (`api/app/modules/cases`, backend team's implementation): 14-state lifecycle (`state_machine.py`,
  `services.py`) with `CaseEvent`, `InterventionOutcome` and `FollowUp`, plus the `modules/audit` module.
  Details: `blueprint/07-case-workflow-and-worker.md` section 8.
- **Auth and campus access**: `get_tenancy_context` in `api/app/core/dependencies.py` honours `X-Campus-ID` only for
  an active `Membership` (`modules/identity/models.py`); routes use `require_role` / `require_permission`
  (`Role`/`Action` in `core/permissions.py`).
- **Worker**: `worker/scheduler.py` runs APScheduler jobs. **Not yet implemented (stubs):** `outbox_dispatch` and
  `deadline_escalation`; the case service writes notification outbox rows but nothing dispatches them.
- **Translation** (optional, `DISHA_TRANSLATE_ENABLED`): `POST /api/v1/translate` runs AI4Bharat IndicTrans2
  distilled 200M models locally on CPU, loaded on first use, no result cache. Install with
  `pip install -e "api[translate]"`. The ai4bharat repos are gated: accept the terms on Hugging Face and set `HF_TOKEN`. Student text never leaves the campus machine. English <-> Indic only.
- **Migrations**: `cd api && alembic upgrade head` (reads `DISHA_DATABASE_URL`;
  `api/migrations/versions/001_counsellor_module_initial.py`, `002_student_faculty_module_initial.py`).

## ML: rolling risk model (primary)

`ml/disha_ml/rolling/` scores a student at every assessment due date from six canonical, level-agnostic tables
(`students`, `enrolments`, `assessments`, `results`, `activity`, `withdrawals`) and returns an insights payload.
Trained on OULAD (train 2013B/2013J/2014B, test 2014J; test ROC AUC 0.857). Contract:
`score_snapshot(tables, as_of) -> InsightsPayload`, CLI `python -m disha_ml.rolling.score`; every field is in
[INSIGHTS_SPEC.md](INSIGHTS_SPEC.md) (source of truth). The legacy semester models (`cp0`/`cp1`/`cp2`, UCI and
UPV) remain in `ml/artifacts/` and `ml/artifacts_upv/` as secondary. **Not yet implemented:** no API route or
worker job calls the scorer (`api/app/modules/ml/routes.py` is a stub). See `blueprint/08-ml-subsystem.md` §0.

## Meko (optional)

Routes under `/api/v1/meko/*` (health, tools, recall, knowledge upload/search/delete, playbook) and
`POST /api/v1/meko/flags/review` and `/outcomes` feed and read the shared memory; the rolling scorer writes tier-change memories.
Repo docs are not synced to Meko. Details: [MEKO_INTEGRATION.md](MEKO_INTEGRATION.md). Full endpoint list:
`blueprint/05-api-specification.md` §4.

## Where else to look

[DISHA_System_Flow.md](DISHA_System_Flow.md) (diagrams, built vs planned), [INSIGHTS_SPEC.md](INSIGHTS_SPEC.md),
`blueprint/README.md` (index and 2026-11-01 changelog).
