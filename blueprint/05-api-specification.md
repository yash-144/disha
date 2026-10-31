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
| GET | `/identity/art/{sutra_id}.png` | none | Public, non-PII |
| GET | `/identity/metadata/{sutra_id}` | none | Public, non-PII |

### 2.15 Removed or not carried forward

| Current path | Reason |
|---|---|
| `POST /happiness/reset` | No legitimate production use (audit S5) |
| `GET /datasets/research/oulad/{id}`, `/datasets/research/synthetic/{id}`, `/datasets/provenance` | Research lookups; belong in the offline ML tooling |
| Root-level ML aliases (`/model-info`, `/predict`, `/predict/batch`) | ADR-005 compatibility aliases; one path per operation |
| `POST /documents/cbdc/issue-voucher` | Simulated provider only |
| Next.js `/api/translate`, `/api/shop/*` | Business logic and third-party proxy outside the API (audit S5, F5) |
| `POST /ml/predict/student/{id}` | Duplicate of `/students/{id}/predict` |

## 3. OpenAPI

The OpenAPI document is generated from code and checked into CI as an
artifact. A contract test fails when a response model changes without a
version or changelog entry. Clients (web, CLI) generate their types from it.
