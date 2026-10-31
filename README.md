# DISHA — Student Early-Warning & Intervention Platform

**DISHA** is an enterprise-grade, multi-campus student early-warning and accountable intervention platform. It transforms disparate academic, attendance, feedback, and financial indicators into reviewable signals, routes accepted signals into owned cases with deadlines, and records auditable interventions to prevent student dropout.

Operating Principle: **"No Alert Without Action"** — Every signal leads to a recorded human decision, an accountable owner, and a tracked deadline.

## Architecture & Monorepo Overview

The repository is organized as a production-grade monorepo:

* `api/` — Modular FastAPI backend with domain-driven modules, row-level security, and audit logging.
* `worker/` — Standalone background task worker for outbox dispatch, deadline escalations, and retention purges.
* `web/` — Next.js 14 frontend with role-based routing (`(public)`, `(staff)`, `(student)`, `(admin)`).
* `cli/` — High-performance Rust CLI (`disha`) for operator sync and management.
* `ml/` — Isolated ML pipeline. Primary model: the rolling risk model (`ml/disha_ml/rolling/`, trained on OULAD, scores at every assessment due date; contract in [docs/architecture/INSIGHTS_SPEC.md](docs/architecture/INSIGHTS_SPEC.md)). Legacy semester models (`cp0`/`cp1`/`cp2`, UCI and UPV) are secondary.
* `meko/` — Optional Meko client (`disha_meko`): fail-safe MCP client, PII guard, intervention catalogue, outcome playbook.
* `contracts/` — Smart contracts for verifiable document anchoring and non-transferable student identity.
* `infra/` — Docker, Docker Compose, monitoring, and deployment configurations.
* `docs/` — Architecture decision records (ADRs), API specs, security policies, and audit documentation.
* `blueprint/` — Rebuild specifications and architectural requirements.
* `tests/` — End-to-end, contract, and dataset integrity verification suites.

## Meko (agent memory & decision traces)

DISHA records ML experiments, per-student academic-story updates (on tier change or drift only, hashed ids, no raw marks), human decisions on flags and case outcomes in [Meko](https://cloud.mekodata.ai) (Yugabyte's agent context engine). Repo docs are not synced to it. It is optional and never blocks anything. See [docs/architecture/MEKO_INTEGRATION.md](docs/architecture/MEKO_INTEGRATION.md).

## Quickstart

### Prerequisites
* Python 3.12+
* Node.js 20+ & pnpm
* Rust 1.78+ (optional, for CLI)
* Docker & Docker Compose

### Environment Configuration
Copy the template configuration:
```bash
cp .env.example .env
```

### Local Development
```bash
# Start backend API
cd api && python -m uvicorn app.main:app --reload --port 8000

# Start frontend
cd web && pnpm dev

# Start worker
cd worker && python main.py

# Apply database migrations
cd api && alembic upgrade head

# Score a snapshot with the rolling model (writes insights JSON)
cd ml && python -m disha_ml.rolling.score --tables data/processed/oulad --as-of 120 --no-meko
```

Optional local translation (IndicTrans2): `pip install -e "api[translate]"`, set `DISHA_TRANSLATE_ENABLED=true` and `HF_TOKEN`, then `POST /api/v1/translate`. API endpoints: `blueprint/05-api-specification.md` §4.

## License
Proprietary — All rights reserved.
