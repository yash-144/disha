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
| 05 | [05-api-specification.md](05-api-specification.md) | API conventions and the endpoint catalogue |
| 06 | [06-ingestion-and-rules-engine.md](06-ingestion-and-rules-engine.md) | Import contract, temporal integrity, policy evaluation, evidence packets, signals |
| 07 | [07-case-workflow-and-worker.md](07-case-workflow-and-worker.md) | Case state machine, tasks, follow-ups, outcomes, deadlines, outbox, scheduler |
| 08 | [08-ml-subsystem.md](08-ml-subsystem.md) | Feature contract, training, evaluation gates, fairness, registry, serving |
| 09 | [09-ai-assistance.md](09-ai-assistance.md) | Bounded LLM features, provider abstraction, prompt safety, audit |
| 10 | [10-wellbeing-pulse-and-rewards.md](10-wellbeing-pulse-and-rewards.md) | Weekly pulse scoring, privacy thresholds, points ledger, redemption |
| 11 | [11-documents-and-anchoring.md](11-documents-and-anchoring.md) | Document lifecycle, hashing, storage, on-chain anchoring, identity collectible |
| 12 | [12-frontend-architecture.md](12-frontend-architecture.md) | Web app structure, session handling, data fetching, localisation |
| 13 | [13-quality-and-operations.md](13-quality-and-operations.md) | Testing strategy, CI/CD, environments, observability, dependencies |
| 14 | [14-audit-traceability.md](14-audit-traceability.md) | Every audit finding mapped to the requirements that close it |
| 15 | [15-build-sequence.md](15-build-sequence.md) | Order of construction with exit criteria per stage |

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
