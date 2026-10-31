# DISHA — Student Early-Warning & Intervention Platform

**DISHA** is an enterprise-grade, multi-campus student early-warning and accountable intervention platform. It transforms disparate academic, attendance, feedback, and financial indicators into reviewable signals, routes accepted signals into owned cases with deadlines, and records auditable interventions to prevent student dropout.

Operating Principle: **"No Alert Without Action"** — Every signal leads to a recorded human decision, an accountable owner, and a tracked deadline.

## Architecture & Monorepo Overview

The repository is organized as a production-grade monorepo:

* `api/` — Modular FastAPI backend with domain-driven modules, row-level security, and audit logging.
* `worker/` — Standalone background task worker for outbox dispatch, deadline escalations, and retention purges.
* `web/` — Next.js 14 frontend with role-based routing (`(public)`, `(staff)`, `(student)`, `(admin)`).
* `cli/` — High-performance Rust CLI (`disha`) for operator sync and management.
* `ml/` — Isolated ML training pipeline for student academic success prediction and model governance.
* `contracts/` — Smart contracts for verifiable document anchoring and non-transferable student identity.
* `infra/` — Docker, Docker Compose, monitoring, and deployment configurations.
* `docs/` — Architecture decision records (ADRs), API specs, security policies, and audit documentation.
* `blueprint/` — Rebuild specifications and architectural requirements.
* `tests/` — End-to-end, contract, and dataset integrity verification suites.

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
```

## License
Proprietary — All rights reserved.
