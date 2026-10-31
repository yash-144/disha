# 15 · Build Sequence

Order of construction for a from-scratch build. Each stage ends at an exit
check; the next stage starts when the check passes. Optional modules come last
because the core loop (observation → signal → review → case → action →
outcome) does not depend on them.

## Stage 0 · Decisions

Resolve the open decisions that block the core. Record each as an ADR.

| Decision | Doc |
|---|---|
| Canonical role list and permission matrix | [04](04-security-and-access.md) §3 |
| Source of faculty/mentor → student scoping | [04](04-security-and-access.md) §3.2 |
| Minimum aggregate cell size | [01](01-product-requirements.md) FR-ANA-02 |
| Retention period per class | [03](03-domain-model.md) §14 |
| Escalation chain per campus | [07](07-case-workflow-and-worker.md) ESC-03 |
| Whether `suggested`/`under_review` remain case states | [07](07-case-workflow-and-worker.md) §1.2 |
| Notification channels for first release | [07](07-case-workflow-and-worker.md) OUT-03 |
| Optional modules in scope for first release | [01](01-product-requirements.md) §3.8 |

**Exit:** ADRs merged.

## Stage 1 · Foundation

- Repository layout, lockfiles, linters, CI skeleton ([13](13-quality-and-operations.md) §3).
- Typed settings with startup validation (CFG-01…05).
- Database, migration tool, first migration (institutions, user profiles,
  memberships, invites, idempotency).
- Auth: JWKS verification, pinned issuer/audience, fail closed (NFR-SEC-01…04).
- Permission table + enforcement dependency + route-declaration check
  (AUTHZ-01…04).
- Error envelope, request id, structured logging with redaction, rate limiter.
- `/health`, `/ready`, `/auth/me`, invites.
- Authorisation matrix test harness (initially covering these routes).

**Exit:** CI green on Postgres; migration-from-empty passes; anonymous and
outsider tests pass; no secret defaults.

## Stage 2 · Roster and ingestion

- Students, account links, processing authorisations.
- Metric registry; import endpoint; roster import (ING-01…05).
- RLS policies generated for all tables so far; RLS test in CI.

**Exit:** import of a synthetic campus produces correct counts and errors;
cross-campus and duplicate tests pass.

## Stage 3 · Rules and signals

- Policy versions (create, publish, retire), evaluation, evidence packets,
  signals, review (POL-*, TMP-*, REV-*).
- Intervention catalogue management.

**Exit:** replay test reproduces stored results; temporal cutoff tests pass;
review creates exactly one case under concurrent requests.

## Stage 4 · Cases and audit chain

- State machine with guards and permissions; atomic versioning
  (CASE-SM-*).
- Tasks, restricted details, follow-ups, outcomes, override, reopen.
- Hash-chained case events; DB grants revoke update/delete (AUD-01).

**Exit:** full matrix test for case routes; concurrency tests; chain
verification endpoint detects a tampered row in a test.

## Stage 5 · Worker and notifications

- Worker process, outbox dispatcher, in-app adapter, notifications inbox.
- Deadline escalation with deadline versions; heartbeat; alerts
  (ESC-*, OUT-*, OBS-06).

**Exit:** E2E escalation scenario passes; dead-letter path tested; worker
runs in staging.

## Stage 6 · Web app core

- Session middleware, route groups, generated API client, query cache
  (FE-01…13).
- Staff queue, signal review, case detail, student support view, admin
  screens.
- i18n catalogues (FE-18…21).
- Unit, accessibility and E2E tests (FE-22…26).

**Exit:** core journey E2E passes for each role; bundle scan clean.

## Stage 7 · Analytics

- Cohort summary, risk trends, outcome rates from stored data with
  suppression (FR-ANA-*).

**Exit:** every number in an analytics response is reproducible from a SQL
query in the test.

## Stage 8 · Deployment and operations

- Containers, IaC, staging and production environments, secret manager,
  backups, runbooks (DEP-*, OBS-*).

**Exit:** staging deploy from CI; restore-from-backup drill completed.

## Stage 9 · Optional modules

Each module follows its own document and adds its routes to the
authorisation matrix test before release.

| Module | Doc | Precondition |
|---|---|---|
| Counselling support | [03](03-domain-model.md) §8, [05](05-api-specification.md) §2.8 | Stage 4 |
| Wellbeing pulse | [10](10-wellbeing-pulse-and-rewards.md) | Safeguarding procedure for reflections (PUL-04) |
| Points and rewards | [10](10-wellbeing-pulse-and-rewards.md) | Pulse or verified activities |
| AI assistance | [09](09-ai-assistance.md) | Data-processing agreement (AI-12) |
| Documents | [11](11-documents-and-anchoring.md) | Object storage |
| On-chain anchoring | [11](11-documents-and-anchoring.md) | Contract with bound anchor key (DOC-07) |
| Identity collectible | [11](11-documents-and-anchoring.md) | Policy approval; wallet proof (NFT-01) |
| ML risk scoring | [08](08-ml-subsystem.md) | ML-PRE-01…03 |
| CLI | [02](02-system-architecture.md) §6.2 | Stable API |
| Avatar editor | [02](02-system-architecture.md) §6.3 | Identity module |

## Pilot gate

Before any real student data is loaded:

- All Critical and High requirements in [14](14-audit-traceability.md) are
  implemented and tested.
- RLS verified on the live database.
- Penetration test or external security review completed.
- DPDP Act compliance review completed (NFR-PRIV-01).
- Data-sharing agreement signed with the partner institution.
