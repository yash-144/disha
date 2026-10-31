# 13 · Quality, CI/CD and Operations

## 1. Facts about the current state

| Suite | Command | Result (19 Oct 2026, audit) | Notes |
|---|---|---|---|
| Main backend | `pytest tests` | 200 passed | In-memory SQLite; schema from `create_all`; migrations not exercised |
| ML package | `pytest ml/tests` | 145 passed, 16 skipped | Skips need raw OULAD data |
| Legacy backend | `pytest backend/tests` | 155 passed, 1 skipped | Superseded code |
| Frontend | `tsc --noEmit` | Passes | Unit tests not run |
| Rust CLI | `cargo test` | Not run | |

Other facts: no CI configuration, no Dockerfile or compose file, no deployment
config, no infrastructure code (audit T1). Python dependencies use `>=` with no
lockfile; `openai` missing (audit T4). No rate limiting; free-text f-string
logs; `redact_sensitive_data` exists but is not used by the request
middleware; no error tracking, metrics or tracing; `/health` and `/ready`
exist (audit T3). Five model tables have no migration (audit D1). Migration
`0006` exists only to patch SQLite timestamp defaults.

## 2. Test strategy

| Layer | Scope | Database | Required |
|---|---|---|---|
| Unit | Pure functions: rule evaluation, state machine, scoring, hashing, permission resolution | None | Yes |
| Integration | API routes through the HTTP client with real DB | Postgres (container), schema from migrations | Yes (audit D4) |
| Authorisation matrix | Every route × every role + outsider + anonymous | Postgres | Yes (audit T2) |
| Concurrency | Parallel transitions, parallel redemptions, parallel escalation scans | Postgres | Yes (audit A3) |
| Migration | `upgrade head` from empty; `downgrade -1`/`upgrade` round trip; model-vs-migration diff is empty | Postgres | Yes (audit D1) |
| RLS | Every exposed table has RLS enabled; anon role cannot read any table | Postgres with RLS | Yes (audit S6) |
| Contract | OpenAPI diff against previous release | — | Yes |
| Worker | Outbox delivery with fake adapter; escalation idempotency | Postgres | Yes (audit A2) |
| ML | Leakage test, feature contract test, reproducibility test, fairness report generation | Fixture data | Yes |
| Smart contracts | Unit tests per function including authorisation | Local chain | If module kept |
| Frontend unit | Components and hooks | — | Yes (audit F4) |
| E2E | Core journey per role in a browser | Seeded test env | Yes |
| Bundle scan | No JWTs, secret names or demo personas in production build | — | Yes (audit S2) |

**Core journey (E2E):** admin invites faculty → faculty accepts → admin
imports roster and observations → faculty evaluates student → signal
`attention_suggested` → faculty approves with intervention → HOD assigns owner
with due date → owner accepts → follow-up recorded → outcome recorded → case
closed → history shows unbroken audit chain. Second run: deadline passes →
worker escalates once → notification delivered by in-app adapter.

**Rules carried from `AGENTS.md`:** a defect fix starts with a failing test;
existing tests are not weakened, skipped or deleted to make a change pass;
test counts are never hand-written into docs.

## 3. CI pipeline

```
on pull request:
  lint            ruff / mypy (api, worker, ml) · eslint + tsc (web) · cargo clippy (cli) · solhint (contracts)
  secrets         secret scan on diff and history
  deps            lockfile check · vulnerability audit
  unit            all unit suites
  integration     Postgres service → migrate from empty → integration + authz matrix + RLS + worker
  migration       alembic check (or equivalent) → fails on drift
  build           container images · web production build
  bundle-scan     scan built web assets
  e2e             deploy to ephemeral env → Playwright
on main:
  all of the above
  publish images with immutable tags
  deploy to staging automatically
on release tag:
  manual approval → deploy to production
```

Branch protection: required checks above; at least one review.

## 4. Environments

| Env | Data | Notes |
|---|---|---|
| development | Synthetic only | Local containers |
| test (CI) | Synthetic, created per run | Ephemeral |
| staging | Synthetic or anonymised | Same infra shape as production |
| demo (optional) | Synthetic only | Separate deployment and database; demo personas allowed here only (audit A5) |
| production | Real | No demo code paths, no seeded personas |

## 5. Deployment

| ID | Requirement | Audit |
|---|---|---|
| DEP-01 | Dockerfiles for API, worker, web | T1 |
| DEP-02 | Infrastructure as code for database, storage, secrets, compute, DNS | T1 |
| DEP-03 | Migrations run as a separate release step before new API instances start | D1 |
| DEP-04 | Secrets from a secret manager; rotation documented | S2 |
| DEP-05 | Runbook: deploy, rollback, rotate JWT/keys, restore DB backup, re-drive dead-letter queue | — |
| DEP-06 | Backups: daily snapshot + point-in-time recovery; restore tested quarterly | — |

## 6. Observability

| ID | Requirement | Audit |
|---|---|---|
| OBS-01 | Structured JSON logs with request id, user id hash, campus id hash, route, status, latency | T3 |
| OBS-02 | Redaction applied in the logging layer: tokens, cookies, names, notes, reflections | T3, S8 |
| OBS-03 | Error tracking (for example Sentry) with PII scrubbing | T3 |
| OBS-04 | Metrics: request rate/latency/errors per route; outbox depth, dead letters; escalations; model alert rate | T3 |
| OBS-05 | Tracing across web → API → DB (OpenTelemetry) | T3 |
| OBS-06 | Alerts: error rate, outbox backlog age, worker heartbeat stale, dead-letter count > 0, chain relayer balance low | A2 |
| OBS-07 | Rate limiting per user and IP with stricter limits on prediction, AI, upload, translation, mint | T3 |

## 7. Dependency management

| ID | Requirement | Audit |
|---|---|---|
| DEPM-01 | Python: lockfile (`uv.lock` or `pip-tools` output); exact pins for serving and training together | T4, M5 |
| DEPM-02 | Node and Rust: committed lockfiles (already present today) | — |
| DEPM-03 | Automated update PRs (Dependabot or Renovate) | T4 |
| DEPM-04 | Every imported package is a declared dependency | T4 |

## 8. Repository hygiene

| ID | Requirement | Audit |
|---|---|---|
| HYG-01 | No phase reports, agent-tool folders or symlinks at the root | A8 |
| HYG-02 | No phase numbers in module or test names | A8 |
| HYG-03 | README describes only merged, tested behaviour; no hand-written test counts | A8 |
| HYG-04 | ADRs record decisions with status and date; superseded ADRs marked | — |
| HYG-05 | Generated artifacts (models, builds, `.next`, `target`) not committed | M5 |
