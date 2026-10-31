# 05 · API Specification

## 1. Conventions

| Topic | Rule |
|---|---|
| Base path | `/api/v1` |
| Format | JSON, UTF-8; timestamps ISO 8601 UTC |
| Auth | `Authorization: Bearer <JWT>` (CLI) or session cookie exchanged server-side (web) |
| Campus context | `X-Campus-Id` header, validated against membership |
| Idempotency | `Idempotency-Key` header on every POST that creates or changes state; same key + same body → stored response; same key + different body → 409 `IDEMPOTENCY_KEY_REUSED` |
| Concurrency | Case mutations require `If-Match: <version>` (or `expected_version` in body); mismatch → 409 `CONCURRENT_CASE_MODIFICATION` |
| Pagination | Cursor-based: `?limit=` (max 100) and `?cursor=`; response `{items, next_cursor}` |
| IDs in paths | UUID only. Lookups by external reference use a separate query parameter (audit D5: student routes accept either in one path segment) |
| Request tracing | `X-Request-Id` accepted or generated; echoed in response |
| DTOs | Explicit allow-listed response models; ORM objects never returned |

### 1.1 Error envelope

**Current implementation:** `ErrorEnvelope` is used by most handlers; 12 places
raise bare `HTTPException` with a different shape (audit D6).

**Requirement:** every error, including validation and framework errors, uses:

```json
{
  "error": {
    "code": "CASE_TRANSITION_NOT_ALLOWED",
    "message": "Transition not allowed from the current state.",
    "request_id": "6f1c…",
    "details": [{"field": "to_state", "message": "…"}]
  }
}
```

| HTTP | Typical codes |
|---|---|
| 400 | `INVALID_REQUEST`, `CAMPUS_HEADER_REQUIRED` |
| 401 | `AUTHENTICATION_REQUIRED`, `TOKEN_EXPIRED`, `INVALID_CREDENTIALS` |
| 403 | `PERMISSION_DENIED`, `INACTIVE_MEMBERSHIP`, `CAMPUS_MEMBERSHIP_NOT_FOUND` |
| 404 | `RESOURCE_NOT_FOUND` (also used for cross-campus) |
| 409 | `STATE_CONFLICT`, `CASE_TRANSITION_NOT_ALLOWED`, `CONCURRENT_CASE_MODIFICATION`, `IDEMPOTENCY_KEY_REUSED` |
| 422 | `VALIDATION_FAILED`, `ML_FEATURES_UNAVAILABLE`, `DOCUMENT_NOT_FINALIZED` |
| 429 | `RATE_LIMITED` |
| 503 | `SERVICE_UNAVAILABLE` (for example chain registry not configured) |

## 2. Endpoint catalogue

"Action" refers to the permission matrix in [04](04-security-and-access.md).
"Current" shows the existing path when it differs or when a defect is noted.

### 2.1 Platform

| Method | Path | Action | Notes |
|---|---|---|---|
| GET | `/health` | none | Liveness |
| GET | `/ready` | none | DB reachable, migrations at head, model registry entry verified |
| GET | `/auth/me` | authenticated | Profile + memberships |
| GET | `/campuses/active` | authenticated | Campuses where the caller has a membership |
| GET | `/campuses/{id}` | member | |

### 2.2 Membership and roster (new)

| Method | Path | Action |
|---|---|---|
| POST | `/memberships/invites` | `membership.manage` |
| POST | `/memberships/invites/accept` | authenticated + valid token |
| GET / PATCH | `/memberships` , `/memberships/{id}` | `membership.manage` |
| POST | `/students` , PATCH `/students/{id}` | `student.write` |
| POST | `/students/{id}/account-link` | `student.write` |
| GET | `/me/student` | `student` with verified link |

### 2.3 Ingestion

| Method | Path | Action | Notes |
|---|---|---|---|
| POST | `/imports` | `import.create` | Body: `ImportBatchRequest` ([06](06-ingestion-and-rules-engine.md)); returns 201 with counts |
| GET | `/imports/{id}` | `import.create` | |

### 2.4 Students

| Method | Path | Action | Notes |
|---|---|---|---|
| GET | `/students` | `student.read` | Paginated; filters `cohort`, `status`, `q` |
| GET | `/students/{id}` | `student.read` | |
| GET | `/students/{id}/support-view` | `student.read` | Role-filtered DTO; no restricted fields |
| GET | `/students/{id}/observations` | `observation.read` | Paginated; `domain`, `from`, `to` |
| GET | `/students/{id}/finance` | `finance.read` | Current: also aliased as `/finance-view` |
| GET | `/students/{id}/readiness` | `ml.predict` | Which model features are present |
| POST | `/students/{id}/predict` | `ml.predict` | 422 if feature contract unmet |
| GET | `/students/{id}/evidence-summary` | `ai.brief` | |
| POST | `/students/{id}/simulate-scenario` | `ml.predict` | What-if on allowed features only |

### 2.5 Signals

| Method | Path | Action | Notes |
|---|---|---|---|
| POST | `/students/{id}/signals/evaluate` | `signal.evaluate` | Body `{as_of_at?, policy_version_id?}` |
| GET | `/signals` | `signal.read` | Paginated; filters `result`, `reviewed` |
| GET | `/signals/{id}` | `signal.read` | Includes evidence card(s) and digest |
| POST | `/signals/{id}/review` | `signal.review` | Body `{decision, reason_code, selected_intervention_key?}`; returns `{signal_id, decision, case_id?}` |

### 2.6 Interventions

| Method | Path | Action |
|---|---|---|
| GET | `/interventions/catalog` | member |
| POST / PATCH | `/interventions/catalog` | `catalog.manage` (new) |

### 2.7 Cases

| Method | Path | Action | Body |
|---|---|---|---|
| GET | `/cases` | `case.read` | Query: `state`, `owner`, `overdue`, paginated |
| GET | `/cases/mine` | `case.read` (student: own) | Current `/cases/my-cases` uses email-prefix matching and an N+1 task query (audit S7, D5) |
| GET | `/cases/{id}` | `case.read` | |
| GET | `/cases/{id}/history` | `case.read` | Events in order with chain hash |
| POST | `/cases/{id}/transition` | `case.transition` | `{to_state, reason_code, metadata}` + version |
| POST | `/cases/{id}/assignment` | `case.assign` | `{primary_owner_user_id, due_at, reason_code}` + version |
| POST | `/cases/{id}/accept-assignment` | `case.accept` | `{acceptance_note?}` + version |
| POST | `/cases/{id}/tasks` | `case.task.create` | `{domain, generic_label, assignee_user_id?, due_at?, restricted_details?}` |
| GET | `/cases/{id}/tasks/{task_id}/restricted` | `case.task.restricted.read` | Access is audited |
| POST | `/cases/{id}/follow-ups` | `case.followup.create` | `{follow_up_type, contact_status?, proof_kind, occurred_at, note?, proof_ref?}` |
| POST | `/cases/{id}/outcome` | `case.outcome.create` | `{outcome_status, rationale, evidence_kind, follow_up_window_end?}` |
| POST | `/cases/{id}/override` | `case.override` | `{override_action, to_state, reason_code, rationale}` + version |
| POST | `/cases/{id}/reopen` | `case.reopen` | `{reopen_reason_code, next_action}` + version |

### 2.8 Counselling

| Method | Path | Action | Notes |
|---|---|---|---|
| GET | `/counselors/profile` | `counsellor.onboard` | Own profile |
| POST | `/counselors/onboarding` | `counsellor.onboard` | Campus from header only (audit S4) |
| POST | `/counselors/onboarding/{profile_id}/decision` | `counsellor.approve` | `{decision: approve\|reject\|suspend, reason?}`. Current path `/onboarding/approve` |
| GET | `/counselors/authority-contacts` | `escalation.create` | |
| POST | `/counselors/escalations` | `escalation.create` | Student id must exist in campus (audit D4: random UUID stored today). Current path `/escalate` |
| GET | `/counselors/escalations` | `escalation.read` | Paginated |
| POST | `/counselors/call-requests` | `call_request.create` | |
| GET | `/counselors/call-requests` | `call_request.update` | Paginated |
| PATCH | `/counselors/call-requests/{id}` | `call_request.update` | Exact UUID match (audit D5: 6-hex-prefix match today) |

### 2.9 Analytics

| Method | Path | Action | Notes |
|---|---|---|---|
| GET | `/analytics/cohort-summary` | `analytics.cohort` | Suppressed cells flagged |
| GET | `/analytics/risk-trends` | `analytics.cohort` | From stored signals |
| GET | `/analytics/student-risk-trajectory/{student_id}` | `ml.predict` | From inference log |
| GET | `/analytics/model-performance` | `analytics.cohort` | From registry entry metrics only |
| GET | `/analytics/performance-monitoring` | `analytics.cohort` | From stored outcomes vs predictions. Current returns hardcoded cohort metrics and an invented date (audit D2) |

### 2.10 ML

| Method | Path | Action | Notes |
|---|---|---|---|
| GET | `/ml/model-info` | authenticated | Registry entry: version, sha256, feature contract, threshold, threshold basis, calibration method |
| POST | `/ml/predict` | `ml.predict` | Feature vector by external ref; logs inference |
| POST | `/ml/predict/batch` | `ml.predict` | Max batch size configured; rate-limited |
| GET | `/ml/supported-scenario-features` | authenticated | |
| POST | `/ml/simulate-scenario` | `ml.predict` | |

### 2.11 AI

| Method | Path | Action |
|---|---|---|
| GET | `/ai/status` | authenticated |
| POST | `/ai/review-brief` | `ai.brief` |
| POST | `/ai/summarize-evidence` | `ai.brief` |
| POST | `/ai/suggest-interventions` | `ai.brief` |

### 2.12 Wellbeing and rewards

**Current implementation:** `/happiness/submissions` and `/happiness/reset` are
unauthenticated; `/happiness/my-status` reports completion if anyone has
submitted; `/happiness/aggregate` and `/trends` return hardcoded figures marked
`is_demo_data=false`; rewards routes live in Next.js (`/api/shop/*`) and
accept any `studentId` (audit S5, D2, A4, F5).

| Method | Path | Action | Notes |
|---|---|---|---|
| GET | `/wellbeing/pulse/current` | `pulse.submit` | Active questionnaire + period |
| POST | `/wellbeing/pulse/submissions` | `pulse.submit` | Student from verified link; one per period |
| GET | `/wellbeing/pulse/status` | `pulse.submit` | Caller's own completion |
| GET | `/wellbeing/pulse/aggregate` | `pulse.aggregate` | Computed; suppressed below threshold |
| GET | `/wellbeing/pulse/trends` | `pulse.aggregate` | Computed per period |
| GET | `/rewards/balance` | `points.read` | Sum of ledger |
| GET | `/rewards/history` | `points.read` | |
| GET | `/rewards/catalog` | authenticated | |
| POST | `/rewards/redemptions` | `redemption.create` | Student from verified link, never from body |

### 2.13 Documents

| Method | Path | Action | Notes |
|---|---|---|---|
| GET | `/documents` | `document.verify` | Paginated |
| POST | `/documents/generate` | `document.create` | Generates PDF; stores to object storage |
| POST | `/documents/upload` | `document.create` | Multipart; limits per HARD-07 |
| GET | `/documents/{id}` | `document.verify` | |
| POST | `/documents/{id}/finalize` | `document.create` | Freezes bytes and hash |
| POST | `/documents/{id}/anchor` | `document.anchor` | Submits or confirms tx; returns 202 and confirms in worker (audit A6) |
| POST | `/documents/{id}/verify` | `document.verify` | Recomputes hash, compares with DB and chain |
| GET | `/documents/{id}/download` | `document.verify` | Signed URL redirect |

### 2.14 Student identity (optional)

| Method | Path | Action | Notes |
|---|---|---|---|
| GET | `/identity/me` | `identity.self` | |
| POST | `/identity/provision` | `identity.self` | Idempotent |
| PUT | `/identity/avatar` | `identity.self` | Validated against catalogue |
| POST | `/identity/wallet/challenge` + `/identity/wallet/verify` | `identity.self` | New: signed-message proof of wallet ownership (audit S8) |
| POST | `/identity/mint` | `identity.self` | Only to verified wallet; rate-limited |
| GET | `/identity/art/{disha_id}.png` | none | Public, non-PII |
| GET | `/identity/metadata/{disha_id}` | none | Public, non-PII |

### 2.15 Removed or not carried forward

| Current path | Reason |
|---|---|
| `POST /happiness/reset` | No legitimate production use (audit S5) |
| `GET /datasets/research/oulad/{id}`, `/datasets/research/synthetic/{id}`, `/datasets/provenance` | Research lookups; belong in the offline ML tooling |
| Root-level ML aliases (`/model-info`, `/predict`, `/predict/batch`) | ADR-005 compatibility aliases; one path per operation |
| `POST /documents/cbdc/issue-voucher` | Simulated provider only |
| Next.js `/api/translate` (third-party proxy), `/api/shop/*` | Business logic and third-party proxy outside the API (audit S5, F5). Translation is now `POST /api/v1/translate` (section 4.4) |
| `POST /ml/predict/student/{id}` | Duplicate of `/students/{id}/predict` |

Note: the third-party-backed Next.js `/api/translate` is replaced by the local
IndicTrans2 route `POST /api/v1/translate` (section 4.4).

## 3. OpenAPI

The OpenAPI document is generated from code and checked into CI as an
artifact. A contract test fails when a response model changes without a
version or changelog entry. Clients (web, CLI) generate their types from it.

## 4. Implementation status (2026-11-01)

Sections 1 and 2 are the target contract. This section lists what the code in
`api/app/` serves **today** (source: `api/app/main.py` and the module
`routes.py` files). Where it differs from section 2, the code wins until the
route is brought in line. Everything is mounted under `/api/v1`.

| Router | Prefix | State |
|---|---|---|
| Cases | `/cases` | Built (section 4.2) |
| Meko | `/meko` | Built (section 4.3) |
| Translate | `/translate` | Built, behind a flag (section 4.4) |
| Identity, roster, ingestion, analytics, wellbeing | `/identity`, `/roster`, `/ingestion`, `/analytics`, `/wellbeing` | Stubs: each has only `GET /` |
| ML | none | `modules/ml/routes.py` is a stub (`GET /` returns `{"module": "ml", "status": "active"}`) and is not mounted. **Not yet implemented:** `/ml/*` and any insights route |
| System | `GET /health` (outside `/api/v1`) | Built |

### 4.1 Conventions as implemented

| Topic | Today |
|---|---|
| Campus context | Header `X-Campus-ID`. `get_tenancy_context` (`api/app/core/dependencies.py`) checks the user is active and has an active `Membership` for that campus (platform admins excepted); `require_role(...)` / `require_permission(Action)` then gate the route and return a `TenancyContext`. Meko routes use `require_role`; `/translate` needs only a valid token |
| Auth | HS256 JWT (`DISHA_JWT_SECRET`); roles from the `roles` claim; staff roles are faculty, mentor, hod, counsellor, finance, placement, leadership, institution_admin |
| Concurrency | `version` in the request body (not `If-Match`); the check is part of the `UPDATE`; mismatch → 409 |
| Idempotency | Not via `Idempotency-Key`: case creation is idempotent per `(campus, flag_id)` |
| Errors | `DishaBaseException` and `HTTPException`; the envelope in §1.1 is **not** uniform yet |
| Migrations | `cd api && alembic upgrade head` (`api/migrations/versions/001_counsellor_module_initial.py`, `002_student_faculty_module_initial.py`; reads `DISHA_DATABASE_URL`) |

### 4.2 Cases (`/api/v1/cases`, backend team's implementation)

Routes in `api/app/modules/cases/routes.py`; lifecycle in `state_machine.py` and `services.py` (14 states,
`CaseState` in `api/app/shared/enums.py`). Request and response shapes: `cases/schemas.py`.

| Method | Path | Notes |
|---|---|---|
| POST | `/` (201) | Create a case |
| GET | `/` | List cases |
| GET | `/{case_id}` | Case detail |
| PATCH | `/{case_id}` | Update case fields |
| POST | `/{case_id}/transition` | Move to another state (rules in `state_machine.py`) |
| POST | `/{case_id}/assign` | Assign an owner |
| POST | `/{case_id}/accept` | Owner accepts the assignment |
| POST | `/{case_id}/reopen` | Reopen a case |
| POST | `/{case_id}/dismiss` | Dismiss a case |
| POST | `/{case_id}/close` | Close a case |
| GET | `/{case_id}/events` | `CaseEvent` history |

Not implemented: `/outcomes/stats`, `/flags/review` and `/{id}/outcome` under `/cases` (removed in the merge; Meko
feeds are in §4.3). Escalation and notification dispatch are worker stubs: [07](07-case-workflow-and-worker.md) §8.

### 4.3 Meko (`/api/v1/meko`)

Meko is optional; without `MEKO_API_KEY` reads return empty results and writes are no-ops.

| Method | Path | Who | Notes |
|---|---|---|---|
| GET | `/health` | no auth | `{configured, reachable, datapack, tool_count, last_error}`; never fails |
| GET | `/tools` | staff (campus from `TenancyContext`) | Discovered Meko tools and the logical-op mapping |
| POST | `/recall` | staff (campus from `TenancyContext`) | `{query (3-500 chars), k (1-20)}` → `{answer, sources[]}`. The query is redacted first; do not paste student names |
| POST | `/knowledge` | admin, HoD (campus from `TenancyContext`) | Multipart upload of campus knowledge: `file` (pdf, txt, md, json, csv; max `MEKO_KB_MAX_BYTES`, default 5 MiB), `doc_type`, `intervention_id?`, `reason_codes`. 415 wrong type, 413 too large, 422 if the PII guard finds an email, phone number or student id, 503 if Meko is off, 502 if Meko fails. Never used for repo docs |
| GET | `/knowledge/search` | staff (campus from `TenancyContext`) | `q`, `limit` → chunks with `document_id` |
| DELETE | `/knowledge/{document_id}` | admin, HoD (campus from `TenancyContext`) | |
| POST | `/flags/review` | staff | `{flag_id, student_id, action, reason_codes[], tier?, note?, case_id?}`. Writes a Meko decision trace only (background, IDs hashed); creates no case. Returns `{flag_id, action, recorded, case_id}` |
| POST | `/outcomes` | staff | `{case_id, outcome, intervention_id, reason_codes[], tier?, checkpoint?}`. 422 if `intervention_id` is not active in the campus catalogue (when configured); writes an outcome memory and may promote it. Returns `{case_id, outcome, recorded}`. The cases module stays the source of truth for outcomes |
| GET | `/playbook` | staff (campus from `TenancyContext`) | `reason_codes` (comma list), `tier?` → interventions that improved similar profiles, limited to the active campus catalogue (`MEKO_CATALOG_PATH`); advice only |

### 4.4 Translate (`POST /api/v1/translate`)

Local AI4Bharat IndicTrans2 distilled 200M models on CPU, loaded on first use. No result cache, no third-party
translation API; student text never leaves the machine. Enabled by `DISHA_TRANSLATE_ENABLED=true` (default false →
503). Needs the extra `pip install -e "api[translate]"` and a Hugging Face token for the gated models (`HF_TOKEN`).

Request: exactly one of `text` (1-2000 chars) or `texts` (1-32 items, each 1-2000 chars); `source_lang`, `target_lang` as
FLORES codes (`hin_Deva`) or BCP-47 (`hi-IN`). One side must be English (`eng_Latn`); Indic to Indic is rejected (422).
Response: `{source_lang, target_lang, translations[]}` (FLORES codes). Any valid bearer token works (no campus
header). 503 when disabled or when the extra is missing.

### 4.5 ML scoring contract and insights payload (library, not yet an endpoint)

The scoring contract is a Python library call and CLI in `ml/`, not an HTTP route:

```python
from disha_ml.rolling.score import score_snapshot
payload = score_snapshot(tables, as_of)        # -> InsightsPayload
```

```bash
python -m disha_ml.rolling.score --tables <dir> --as-of <day> [--model <dir>] [--out file.json] [--no-meko]
```

* `tables`: dict of DataFrames in the six canonical tables (`students`, `enrolments`, `assessments`, `results`,
  `activity`, `withdrawals`; [18](18-dataset-requirements.md) §7) or a folder of `<table>.csv[.gz]`.
* `as_of`: integer day since term start; applies to every course-term in `tables`.
* Result `payload.to_dict()`: `schema_version`, `as_of_day`, `model`, `n_students`, `students[]`, `cohorts[]`,
  `data_drift`. Every field, JSON path and definition:
  [`docs/architecture/INSIGHTS_SPEC.md`](../docs/architecture/INSIGHTS_SPEC.md) (source of truth).
* Call once per assessment due date, optionally weekly for engagement. Scoring all 32k OULAD enrolments takes about 15 s.
* Students are keyed by the caller's `student_id`; hash it before logging elsewhere.

**Not yet implemented:** an HTTP route (for example `POST /ml/insights`) or worker job that loads the canonical tables
from Postgres, calls `score_snapshot`, stores the payload, and turns tier changes into reviewable flags for
`/api/v1/meko/flags/review` or the cases module. §2.4 and §2.10 stay as the target for per-student prediction; the backend team should agree
whether those routes return `StudentInsight` entries from the payload.

### 4.6 CLO insights contract (backend to expose)

Course-outcome insights for faculty, as a library call and CLI in `ml/` (not yet an HTTP route):

```python
from disha_ml.clo.analyze import analyze_course
payload = analyze_course(tables, course_id, term_id)     # -> CloPayload; payload.to_dict()
```

```bash
python -m disha_ml.clo.analyze --tables <dir> --course <id> --term <id> [--as-of <day>] [--out f.json] [--no-meko]
```

Suggested routes: `GET /api/v1/courses/{course_id}/terms/{term_id}/clo` (faculty roles; everything except `student_gaps`) and `GET .../clo/student-gaps` (mentor role only, `audience: mentor`). Top-level fields: `co_attainment`, `items`, `bloom`, `misconceptions`, `trends`, `section_comparison`, `muddiest`, `learnings`, `recommendations`, `student_gaps`, `context` (`context.recalled` = Meko hits verbatim for display), `suppressed`. Every field, threshold and visual: [`docs/architecture/CLO_SPEC.md`](../docs/architecture/CLO_SPEC.md). Input tables: [18](18-dataset-requirements.md) §10.

### 4.7 Student journey in Meko (Backend to expose)

Wrappers over `MekoClient` (`meko/disha_meko`); not yet HTTP routes. Spec: [`docs/architecture/MEKO_INTEGRATION.md`](../docs/architecture/MEKO_INTEGRATION.md) "Student academic journey". The student id in the path is the raw ERP id; the backend hashes it (needs `MEKO_PII_SALT`). Without Meko or a salt, reads return empty results.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/v1/students/{id}/journey` | `limit` (default 100) | `{"turns": [{input, output, reasoning, metadata: {event_type, kind, student, course?, term?, day?, tier?, ...}, ...}]}` in order, as Meko returned them (`client.journey_timeline`) |
| GET | `/api/v1/students/{id}/briefing` | `meko=on\|off` (default on), `q?` | `{"enabled": bool, "student": "s_<12 hex>", "question": str\|null, "items": [{"id": str, "source": "memory"\|"conversation", "text": str}]}`; `meko=off` gives empty `items` (`client.journey_briefing`) |
| PATCH | `/api/v1/meko/memories/{memory_id}` | `{"text": str}` | `{"ok": bool}`; the text passes the PII guard; 422 if empty after cleaning |
| DELETE | `/api/v1/meko/memories/{memory_id}` | | `{"ok": bool}` |
| DELETE | `/api/v1/students/{id}/meko` | | `{"student": hash, "memories_deleted": int, "conversation_deleted": bool}`; right to erasure (DPDP Act): `erase_student` deletes every memory extracted from the journey, then the conversation. Admin or data-protection officer only; audit-logged |

Roles: the mentor or counsellor assigned to that student only (campus membership checked); other staff get 403. Briefing items are returned verbatim with their Meko `id` and `source`, never rewritten, so the UI can show provenance and offer correct/forget on each item.

