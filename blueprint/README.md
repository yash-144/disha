# Rebuild Blueprint

This folder is a specification for building a student early-warning and
intervention platform from an empty repository. It is derived from two sources:

1. The current repository (`app/`, `ml/`, `frontend/`, `contracts/`, `cli/`,
   `avatar-customizer/`) at commit `7df0b08`, read on 31 Oct 2026.
2. The engineering audit `docs/audit/AUDIT.md` (19 Oct 2026, 38 findings).

## How to read these documents

- Statements marked **Requirement** (with an ID such as `FR-CASE-04` or
  `NFR-SEC-02`) describe what the new system must do.
- Statements marked **Current implementation** describe what the existing code
  does today. They are reference facts, not recommendations.
- Statements marked **Open decision** need a choice by the product owner before
  code is written. No default is assumed for them.
- Audit finding IDs (`S1`, `A2`, `M1` …) are cited where a requirement exists
  because of that finding. The full mapping is in
  [14-audit-traceability.md](14-audit-traceability.md).

Technology names appear where the current system uses them or where a
requirement depends on a capability (for example "a relational database with
row-level security"). They are not endorsements; alternatives with the same
capability satisfy the requirement.

## Documents

| # | File | Contents |
|---|------|----------|
| 01 | [01-product-requirements.md](01-product-requirements.md) | Purpose, users, functional and non-functional requirements, invariants, out of scope, glossary |
| 02 | [02-system-architecture.md](02-system-architecture.md) | Components, boundaries, runtime topology, request and job flows, configuration |
| 03 | [03-domain-model.md](03-domain-model.md) | Entities, fields, relationships, enumerations, retention, audit immutability |
| 04 | [04-security-and-access.md](04-security-and-access.md) | Authentication, tenancy, roles, permission matrix, data classification, hardening |
| 05 | [05-api-specification.md](05-api-specification.md) | API conventions, the endpoint catalogue, and §4 what is built (cases, Meko, translate), the ML scoring contract and insights payload pointer |
| 06 | [06-ingestion-and-rules-engine.md](06-ingestion-and-rules-engine.md) | Import contract, temporal integrity, policy evaluation, evidence packets, signals |
| 07 | [07-case-workflow-and-worker.md](07-case-workflow-and-worker.md) | Case state machine, tasks, follow-ups, outcomes, deadlines, outbox, scheduler; §8 what is built |
| 08 | [08-ml-subsystem.md](08-ml-subsystem.md) | Rolling risk model (primary) and scoring contract, feature contract, training, evaluation gates, fairness, registry, serving |
| 09 | [09-ai-assistance.md](09-ai-assistance.md) | Bounded LLM features, provider abstraction, prompt safety, audit; local translation note |
| 10 | [10-wellbeing-pulse-and-rewards.md](10-wellbeing-pulse-and-rewards.md) | Weekly pulse scoring, privacy thresholds, points ledger, redemption |
| 11 | [11-documents-and-anchoring.md](11-documents-and-anchoring.md) | Document lifecycle, hashing, storage, on-chain anchoring, identity collectible |
| 12 | [12-frontend-architecture.md](12-frontend-architecture.md) | Web app structure, session handling, data fetching, localisation |
| 13 | [13-quality-and-operations.md](13-quality-and-operations.md) | Testing strategy, CI/CD, environments, observability, dependencies |
| 14 | [14-audit-traceability.md](14-audit-traceability.md) | Every audit finding mapped to the requirements that close it |
| 15 | [15-build-sequence.md](15-build-sequence.md) | Order of construction with exit criteria per stage |
| 16 | [16-risk-signal-pipeline.md](16-risk-signal-pipeline.md) | How a student gets flagged: legacy semester pipeline (§1-11) and the rolling risk model (§12) |
| 17 | [17-model-training-guide.md](17-model-training-guide.md) | Step-by-step training on Kaggle or locally, reports, release check, scoring; §13 rolling model |
| 18 | [18-dataset-requirements.md](18-dataset-requirements.md) | UCI and UPV datasets, requirements and checklist for any dataset, privacy rules; §7-9 canonical schema, OULAD, what a college must provide |

The ML training code that implements 16–18 is in `../ml/` (see `ml/README.md`).
Related architecture notes outside this folder:
[`docs/architecture/INSIGHTS_SPEC.md`](../docs/architecture/INSIGHTS_SPEC.md) (the insights payload; source of
truth), [`docs/architecture/MEKO_INTEGRATION.md`](../docs/architecture/MEKO_INTEGRATION.md),
[`docs/architecture/DISHA_System_Flow.md`](../docs/architecture/DISHA_System_Flow.md).

## Changelog (2026-11-01)

* **Primary model is now the rolling risk model** (`ml/disha_ml/rolling/`, OULAD via
  `ml/disha_ml/converters/oulad.py`). It scores at every assessment due date, excludes already-withdrawn enrolments,
  labels `at_risk` = Fail or Withdrawn, splits temporally (train 2013B/2013J/2014B, test 2014J), uses HGB with
  isotonic calibration (23 features, 44,340 parameters). Test ROC AUC 0.857. Docs: 08 §0, 16 §12, 17 §13, 18 §7-9,
  `ml/README.md` §27-34.
* **Canonical, level-agnostic input tables** (school / UG / PG): `students`, `enrolments`, `assessments`, `results`,
  `activity`, `withdrawals` (18 §7).
* **Scoring contract:** `score_snapshot(tables, as_of) -> InsightsPayload` and
  `python -m disha_ml.rolling.score` (05 §4.5). The payload (`schema_version`, `as_of_day`, `model`, `n_students`,
  `students[]`, `cohorts[]`, `data_drift`) is specified only in `docs/architecture/INSIGHTS_SPEC.md`.
* **Legacy semester models** (`cp0`/`cp1`/`cp2`, UCI and UPV) are secondary. The 94.5% and 97.6% figures are alert
  precision after the capacity cap, not accuracy (accuracy about 84% and 88% vs a 69% majority baseline); most `cp2`
  alerts were students who had passed zero semester-2 subjects.
* **Meko:** academic-story memories (`record_assessment_updates`) only on a tier change or drift event, hashed ids,
  `journey:<hash>` tags, no raw marks. Repo docs are no longer synced to Meko (`sync.py` and the nightly knowledge
  job were removed). The Meko client gained `guard.py`, `catalog.py`, `playbook.py`.
* **Backend already built** (documented, not changed): case lifecycle with `case_events`, campus membership checks
  (403), outbox with retries and dead-letter, deadline escalation, Alembic migration `0001` (07 §8); translate
  endpoint behind `DISHA_TRANSLATE_ENABLED` (local IndicTrans2); `/api/v1/meko/*`; `POST /api/v1/cases/{id}/outcome`
  (05 §4).
* **Contradictions removed:** accuracy wording; `make meko-sync` and nightly knowledge sync; the third-party
  translation provider as the translation path; "cases not built" in the system-flow status table.
* **Gaps called out as "Not yet implemented":** no API route or worker job calls `score_snapshot`; no release check
  or fairness bound for the rolling model; `meko_weekly_outcomes` has no data source; `anchor_confirmation`,
  `retention_purge`, `model_drift_report` are log-only stubs; identity, roster, ingestion, analytics, wellbeing and
  ml routers are stubs.

## Facts about the current repository (for scale reference)

From `docs/audit/AUDIT.md`, "Scope and method":

| Component | Path | Source lines | Stack |
| --- | --- | --- | --- |
| Web app | `frontend/` | 52,024 | Next.js 14, TypeScript |
| ML research and training | `ml/` | 19,964 | Python, scikit-learn, XGBoost |
| Superseded prototype backend | `backend/` | 18,520 | FastAPI, raw `sqlite3` |
| Main backend | `app/` | 13,346 | FastAPI, SQLAlchemy 2 async |
| Backend tests | `tests/` | 9,822 | pytest |
| CLI | `cli/` | 5,982 | Rust |
| Avatar customiser | `avatar-customizer/` | 3,582 | Next.js, VRM |
| Scripts | `scripts/` | 2,608 | Python |
| Migrations | `alembic/` | 853 | Alembic |
| Smart contracts | `contracts/` | 553 | Solidity |

Built by 6 contributors in 157 commits over 3 days (11–13 Oct 2026).
