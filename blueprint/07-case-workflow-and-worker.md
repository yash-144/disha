# 07 · Case Workflow and Worker

> **Status (2026-11-01).** Sections 1 to 7 are the target specification and
> describe the earlier SUTRA code as "Current implementation". The new backend
> (`api/app/modules/cases/`, `worker/`) implements most of it; section 8 lists
> exactly what is built and what is not. Where they differ, section 8 wins.

## 1. Case state machine

**Earlier (SUTRA) implementation:** `ALLOWED_TRANSITIONS` in
`app/services/case_service.py` (14 states); the new `TRANSITIONS` table in
`api/app/modules/cases/services.py` has the same transitions (§8). Cases are created directly in
`action_planned` from an approved signal.

```mermaid
stateDiagram-v2
  [*] --> suggested
  suggested --> under_review
  under_review --> action_planned
  under_review --> dismissed
  action_planned --> assigned
  assigned --> assigned: reassign
  assigned --> accepted
  accepted --> contact_attempted
  contact_attempted --> support_in_progress
  contact_attempted --> failed_contact
  support_in_progress --> follow_up_due
  support_in_progress --> service_unavailable
  follow_up_due --> outcome_reviewed
  outcome_reviewed --> closed
  failed_contact --> closed
  service_unavailable --> closed
  closed --> reopened
  reopened --> assigned
  reopened --> action_planned
  dismissed --> [*]
```

### 1.1 Transition events (current)

| From → To | Event type |
|---|---|
| suggested → under_review | `CASE_REVIEW_STARTED` |
| under_review → action_planned | `INTERVENTION_APPROVED` |
| under_review → dismissed | `SIGNAL_DISMISSED` |
| action_planned → assigned | `OWNER_ASSIGNED` |
| assigned → assigned | `OWNER_REASSIGNED` |
| assigned → accepted | `ASSIGNMENT_ACCEPTED` |
| accepted → contact_attempted | `CONTACT_ATTEMPTED` |
| contact_attempted → support_in_progress | `SUPPORT_STARTED` |
| contact_attempted → failed_contact | `CONTACT_FAILED` |
| support_in_progress → follow_up_due | `SUPPORT_DELIVERED` |
| support_in_progress → service_unavailable | `SERVICE_UNAVAILABLE` |
| follow_up_due → outcome_reviewed | `OUTCOME_RECORDED` |
| outcome_reviewed / failed_contact / service_unavailable → closed | `CASE_CLOSED` |
| closed → reopened | `CASE_REOPENED` |
| (creation) | `CASE_CREATED_FROM_SIGNAL` |
| (worker) | `CASE_ESCALATED` |

### 1.2 Requirements

| ID | Requirement | Audit |
|---|---|---|
| CASE-SM-01 | The transition table is data (one module constant or table) and the only place transitions are defined | — |
| CASE-SM-02 | Each transition declares the permission action and scope rule required ([04](04-security-and-access.md)) | S4 |
| CASE-SM-03 | Each transition declares guards. Minimum: `→ assigned` needs owner and `due_at`; `→ accepted` only by owner; `→ follow_up_due` needs ≥ 1 follow-up of type `support_delivered`; `→ outcome_reviewed` needs an outcome row; `→ closed` from `outcome_reviewed` needs an outcome | — |
| CASE-SM-04 | Version check and write are one statement: `UPDATE cases SET …, version = version + 1 WHERE id = :id AND institution_id = :c AND version = :v`; 0 rows → 409 | A3 |
| CASE-SM-05 | Clients must send the version on every mutating case call | A3 |
| CASE-SM-06 | State change, case event and outbox intent commit in one transaction | — |
| CASE-SM-07 | Override records the prior state and reason; it may move to any state permitted by an explicit override table | — |
| CASE-SM-08 | Terminal states: `closed` (reopenable), `dismissed` (not reopenable) | — |

**Open decision:** whether `suggested` and `under_review` remain case states
when review already happens on the signal. In the current code no case is
created in those states.

## 2. Tasks

- Task states: `pending → accepted → in_progress → completed`, plus
  `cancelled` from any non-terminal state.
- A task in a restricted domain (`finance`, `counselling`) stores sensitive
  context in `restricted_task_details`; the task row holds only
  `generic_label`.
- Reading restricted details writes an access audit event.
- Each task has its own `due_at` and `deadline_version` and is escalated by
  the same scheduler as cases.

## 3. Follow-ups and outcomes

- A follow-up with `contact_status = attempted` does not imply support was
  delivered (requirement R14 in `docs/docs/01_SCOPE_AND_REQUIREMENTS.md`).
- An outcome can be recorded once per case cycle; reopen starts a new cycle.
- Notes are stored as entered by staff. **Open decision:** whether notes pass
  through automated PII redaction before storage (field name
  `sanitized_note` exists today; no redaction is performed).

## 4. Deadlines and escalation

**Earlier (SUTRA) implementation, superseded by §8:** `scan_and_escalate_overdue_cases` selects
non-terminal cases with `due_at < now` and `is_escalated = false`, sets
`is_escalated = true`, increments version, writes `CASE_ESCALATED` with
`actor_kind = system_worker` and an outbox intent
`CASE_ESCALATION_SUPERVISOR`. It is not run by any process (audit A2).

**Requirements:**

| ID | Requirement |
|---|---|
| ESC-01 | A scheduler runs the scan at a configured interval in every environment except unit tests |
| ESC-02 | Idempotency key per escalation = `(case_id, deadline_version)`; changing `due_at` increments `deadline_version` and re-arms escalation |
| ESC-03 | Escalation target is resolved from configuration: owner's HOD or a campus escalation contact. **Open decision:** escalation chain per campus |
| ESC-04 | Multi-level escalation (for example +24 h → HOD, +72 h → institution admin) is configurable |
| ESC-05 | The scan uses `FOR UPDATE SKIP LOCKED` so multiple workers do not double-escalate |
| ESC-06 | Tasks follow the same rules |

## 5. Outbox and delivery

**Earlier (SUTRA) implementation, superseded by §8:** `OutboxWorker.process_outbox_batch` locks up to 50
due `pending` rows (`SKIP LOCKED`), calls an optional dispatcher, marks `sent`
even without a dispatcher, retries with backoff `5 s × 2^(attempt-1)`, and sets
`dead_letter` after 5 attempts (audit A2).

**Requirements:**

| ID | Requirement |
|---|---|
| OUT-01 | Adapter registry keyed by `adapter_key`; unknown key → `dead_letter` with code `UNKNOWN_ADAPTER` |
| OUT-02 | No adapter → item stays `pending`; never marked `sent` |
| OUT-03 | Adapters: `in_app` (writes `notifications` rows) required; `email`, `sms`, `whatsapp` optional per campus |
| OUT-04 | Payload contains IDs and template keys only; adapters render content at send time with the recipient's permissions |
| OUT-05 | Each delivery attempt is logged with provider message id |
| OUT-06 | Dead-letter items are visible to `institution_admin` with a retry action |
| OUT-07 | Retry policy (max attempts, base backoff) is configuration |

## 6. Worker process

```
loop every OUTBOX_INTERVAL:     process_outbox_batch(batch_size)
loop every ESCALATION_INTERVAL: scan_and_escalate(cases), scan_and_escalate(tasks)
loop every ANCHOR_INTERVAL:     confirm_pending_anchors()
daily:                          purge_expired(retention classes), purge_idempotency()
```

- One entry point (`worker` command) in the same code base as the API.
- Graceful shutdown: finish the current batch, release locks.
- Health: the worker writes a heartbeat row; `/ready` on the API reports
  worker staleness.
- Metrics: items processed, failed, dead-lettered, escalations created,
  loop duration.

## 7. Audit chain

**Requirement AUD-01 (audit D3):** `case_events` (and other audit tables)
form a hash chain per campus: `hash = SHA-256(prev_hash || canonical_row)`.
A verification endpoint (admin only) recomputes the chain and reports the first
break. The application database role has `INSERT` and `SELECT` only on audit
tables. The superseded prototype (`backend/`) contained a hash-chained
"Support Evidence Ledger"; `app/` has none.

## 8. Implementation status (API `modules/cases`, worker)

Built in `api/app/modules/cases/` and `worker/jobs/`; tables are in migration `0001` (`disha_cases`,
`disha_case_tasks`, `disha_restricted_task_details`, `disha_case_events`, `disha_case_outcomes`, `disha_outbox`,
`disha_campus_memberships`).

- **State machine**: `TRANSITIONS` in `services.py` is the only definition (CASE-SM-01). Cases start in
  `action_planned` (`POST /cases`, or `flags/review` with `open_case` / `start_intervention`; one case per flag).
  Guards: `→ assigned` only via `POST /{id}/assign` (owner and `due_at`), `→ accepted` only by the owner or
  `institution_admin`, `→ outcome_reviewed` and `outcome_reviewed → closed` need an outcome row.
- **Concurrency and audit**: the version check is part of the `UPDATE` (409 on mismatch); clients send `version`
  (CASE-SM-04/05). State change, `case_events` row and `disha_outbox` row commit together (CASE-SM-06).
  `case_events` is append-only (ORM refuses update/delete); hash chain (AUD-01) is not built.
- **Outcomes**: `POST /{id}/outcome` persists one `case_outcomes` row per case cycle (reopen = new cycle), moves
  `follow_up_due → outcome_reviewed`, then feeds Meko. `GET /cases/outcomes/stats` returns counts per
  `(intervention_id, reason_pattern)` for the campus, so promotion can rely on Postgres.
- **Outbox** (`outbox.py`, job every 10 s): due rows only, `SKIP LOCKED`; failure *k* waits `base × 2^(k-1)` s;
  the `DISHA_OUTBOX_MAX_ATTEMPTS`-th failure sets `dead_letter`; unknown adapter → `dead_letter UNKNOWN_ADAPTER`;
  no adapters configured → rows stay `pending`. Only `in_app` exists (the outbox row is the notification).
- **Escalation** (`escalate_overdue`, job every 60 s): non-terminal cases and unfinished tasks with `due_at` in the
  past get `is_escalated`, a `CASE_ESCALATED` / `TASK_ESCALATED` event (`actor_kind = system_worker`) and a
  `*_ESCALATION_SUPERVISOR` outbox row to `DISHA_ESCALATION_TARGET`. Key is `(id, deadline_version)`; a new
  `due_at` bumps `deadline_version` and re-arms (ESC-02).
- **Not built**: multi-level escalation (ESC-04), per-campus escalation chain (ESC-03), email/SMS adapters,
  dead-letter admin retry (OUT-06), restricted-detail read audit, override table (CASE-SM-07), worker heartbeat.
- **Campus access**: every cases route uses `campus_role(*STAFF_ROLES)`; the `X-Campus-ID` header is honoured only
  when the token's `sub` has an active `disha_campus_memberships` row for that campus (else 403; header missing → 400).
- **HTTP surface**: `GET /cases`, `GET /cases/outcomes/stats`, `POST /cases`, `GET /cases/{id}`,
  `POST /cases/{id}/transition`, `/assign`, `/tasks`, `POST /cases/tasks/{id}/state`, `POST /cases/flags/review`,
  `POST /cases/{id}/outcome`. Request bodies: [05](05-api-specification.md) §4.2.
- **Meko feed** (optional, background): `flags/review` writes a decision trace for every human decision; `/outcome`
  writes an outcome memory (hashed case id) and promotes a recurring good outcome into the shared playbook
  (`MEKO_PROMOTE_MIN`, default 3). `intervention_id` must be active in the campus catalogue when one is configured
  (AI-07). Postgres stays the source of truth for outcome counts.
- **Worker** (`worker/scheduler.py`, APScheduler, one run per job at a time): `outbox_dispatch` every 10 s,
  `deadline_escalation` every 60 s, `anchor_confirmation` every 300 s, `retention_purge` and `model_drift_report`
  daily, `meko_weekly_outcomes` weekly. **Only the first two do work.** `anchor_confirmation`, `retention_purge` and
  `model_drift_report` only log a line; `meko_weekly_outcomes` is wired but `fetch_weekly_outcomes()` returns `[]`
  (TODO), so it writes nothing yet. Repo docs are no longer synced to Meko.
- **Migration**: `api/migrations/versions/0001_cases_outbox_membership.py` (Alembic; `cd api && alembic upgrade head`,
  uses `DISHA_DATABASE_URL`). Tests: `api/tests/unit/test_case_lifecycle.py`, `api/tests/migrations/test_case_migration.py`,
  `worker/tests/test_worker_jobs.py`.
- **Not built (extra)**: follow-up rows and the `→ follow_up_due needs a follow-up` guard (CASE-SM-03), the
  `suggested` / `under_review` entry path (no case is created in those states), notification rows beyond the outbox,
  and any worker call to the ML scorer ([05](05-api-specification.md) §4.5).

