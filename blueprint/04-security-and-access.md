# 04 · Security and Access Control

Data held: academic records, fee status, counselling notes and wellbeing
reflections of students, some of whom may be minors. Requirements here apply to
every module.

## 1. Authentication

**Current implementation** (`app/core/security.py`, `app/core/config.py`):
- Bearer JWT, algorithm allowlist (`HS256`, `ES256`, `RS256`), `none` rejected,
  separate key paths per algorithm family, `exp` and `aud` checked.
- If JWKS lookup fails, verification falls back to a hardcoded EC public key in
  config (audit S3).
- For ES256/RS256, issuer is verified only if the token contains `iss`
  (audit S3).
- `SUPABASE_JWT_SECRET` defaults to a public string; no startup check (audit S2).
- `frontend/lib/demo-auth.ts` contains 8 pre-issued JWTs; the API client sends
  one when no user is signed in; `?role=` selects a persona (audit S2, A5).

**Requirements:**

| ID | Requirement |
|---|---|
| NFR-SEC-01 | Production accepts only asymmetric algorithms from the identity provider's JWKS |
| NFR-SEC-02 | Issuer and audience are always required and pinned in configuration |
| NFR-SEC-03 | JWKS unavailable or unknown `kid` → 401. No fallback key |
| NFR-SEC-04 | Startup refuses to run outside `development`/`test` if any secret is missing or equals a placeholder |
| NFR-SEC-05 | No token, key or credential in source, tests, fixtures or client bundles. CI scans the built client bundle for JWT-shaped strings and known secret names |
| NFR-SEC-06 | Test tokens are minted at test time with a test-only key |
| NFR-SEC-07 | Sessions in the web app use HTTP-only, `Secure`, `SameSite` cookies managed server-side; bearer tokens are not stored in `localStorage` (audit S8) |
| NFR-SEC-08 | The API base URL is fixed at build time; it cannot be overridden from `localStorage` or a window global (audit S8) |

## 2. Tenancy

| ID | Requirement |
|---|---|
| NFR-TEN-01 | Campus context comes from a request header or path and is validated against the caller's active membership. It is never taken from a request body (audit S4: `POST /counselors/onboarding` reads `campus_id` from the body) |
| NFR-TEN-02 | Every query on campus-owned data filters by the validated campus id |
| NFR-TEN-03 | Cross-campus object access returns 404 |
| NFR-TEN-04 | No membership is created during authentication (audit S1) |
| NFR-TEN-05 | Database RLS mirrors tenancy for every exposed table as a second layer (audit S6) |

## 3. Authorisation

### 3.1 Mechanism

**Current implementation:** per-route `require_roles([...])` lists; 3 of 13
case routes check roles; any member can transition, add tasks, follow-ups and
outcomes; leadership is blocked from reading cases but not from changing them
(audit S4).

**Requirements:**

- **AUTHZ-01** One permission table: `(action) → allowed roles + scope rule`.
  Every route declares its action; a single dependency enforces it.
- **AUTHZ-02** Scope rules are evaluated on the object (for example
  "assignee of this case", "domain of this task", "own student record").
- **AUTHZ-03** A test enumerates every route × every role (+ outsider +
  anonymous) and asserts the expected status (audit T2).
- **AUTHZ-04** Startup fails if a route has no declared action, except
  `/health` and `/ready`.

### 3.2 Baseline permission matrix

**Open decision:** the matrix below is a baseline assembled from
`docs/docs/04_AUTHORIZATION_PRIVACY.md` and the route guards in `app/api/v1/`.
It must be confirmed by the product owner before implementation (per
`AGENTS.md`, "If the fix needs a decision … propose it before writing code").

Legend: ✔ allowed · S scoped (see note) · ✖ denied · A aggregates only

| Action | student | faculty | mentor | hod | counsellor | finance | placement | leadership | inst_admin |
|---|---|---|---|---|---|---|---|---|---|
| `student.read` | own | S¹ | S² | ✔ | S³ | ✖ | S³ | ✖ | ✔ |
| `student.write` (roster) | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✔ |
| `observation.read` | ✖ | S¹ | S² | ✔ | S³ | ✖ | S³ | ✖ | ✖ |
| `finance.read` | ✖ | ✖ | ✖ | ✖ | ✖ | ✔ | ✖ | ✖ | ✖ |
| `import.create` | ✖ | ✖ | ✖ | ✔ | ✖ | ✖ | ✖ | ✖ | ✔ |
| `signal.evaluate` | ✖ | S¹ | S² | ✔ | ✖ | ✖ | ✖ | ✖ | ✔ |
| `signal.read` | ✖ | S¹ | S² | ✔ | ✖ | ✖ | ✖ | ✖ | ✖ |
| `signal.review` | ✖ | S¹ | S² | ✔ | ✖ | ✖ | ✖ | ✖ | ✖ |
| `case.read` | own⁴ | S⁵ | S⁵ | ✔ | S⁵ | S⁵ | S⁵ | ✖ | ✖ |
| `case.assign` | ✖ | ✖ | ✖ | ✔ | ✖ | ✖ | ✖ | ✖ | ✔ |
| `case.accept` | ✖ | assignee | assignee | assignee | assignee | assignee | assignee | ✖ | ✖ |
| `case.transition` | ✖ | owner | owner | ✔ | owner | owner | owner | ✖ | ✖ |
| `case.task.create` | ✖ | owner | owner | ✔ | owner | ✖ | ✖ | ✖ | ✖ |
| `case.task.restricted.read` | ✖ | ✖ | ✖ | ✖ | domain | domain | domain | ✖ | ✖ |
| `case.followup.create` | ✖ | owner/assignee | owner/assignee | ✔ | domain task | domain task | domain task | ✖ | ✖ |
| `case.outcome.create` | ✖ | owner | owner | ✔ | domain task | domain task | domain task | ✖ | ✖ |
| `case.override` | ✖ | ✖ | ✖ | ✔ | ✖ | ✖ | ✖ | ✖ | ✔ |
| `case.reopen` | ✖ | ✖ | ✖ | ✔ | ✖ | ✖ | ✖ | ✖ | ✔ |
| `analytics.cohort` | ✖ | S¹ | S² | ✔ | A | A | A | A | ✔ |
| `catalog.manage` / `policy.manage` | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✔ |
| `membership.manage` | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✔ |
| `counsellor.onboard` (self) | ✖ | ✖ | ✖ | ✖ | ✔ | ✖ | ✖ | ✖ | ✖ |
| `counsellor.approve` | ✖ | ✖ | ✖ | ✔ | ✖ | ✖ | ✖ | ✖ | ✔ |
| `escalation.create` | ✖ | ✖ | ✖ | ✔ | ✔ | ✖ | ✖ | ✖ | ✖ |
| `escalation.read` | ✖ | ✖ | ✖ | ✔ | own⁶ | ✖ | ✖ | ✖ | ✔ |
| `call_request.create` | own | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ |
| `call_request.update` | ✖ | ✖ | ✖ | ✖ | assigned | ✖ | ✖ | ✖ | ✖ |
| `pulse.submit` | own | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ |
| `pulse.aggregate` | ✖ | ✖ | ✖ | A | A | ✖ | ✖ | A | A |
| `pulse.reset` | — | — | — | — | — | — | — | — | — (no such action; audit S5) |
| `points.read` | own | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✔ |
| `points.award` | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✔ (or system) |
| `redemption.create` | own | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ | ✖ |
| `ml.predict` | ✖ | S¹ | S² | ✔ | ✖ | ✖ | ✖ | ✖ | ✖ |
| `ai.brief` | ✖ | S¹ | S² | ✔ | ✖ | ✖ | ✖ | ✖ | ✖ |
| `document.create` / `finalize` | ✖ | owner | owner | ✔ | ✖ | ✖ | ✖ | ✖ | ✔ |
| `document.anchor` | ✖ | ✖ | ✖ | ✔ | ✖ | ✖ | ✖ | ✖ | ✔ |
| `document.verify` | ✖ | ✔ | ✔ | ✔ | ✔ | ✖ | ✖ | ✖ | ✔ |
| `identity.self` | own | own | own | own | own | own | own | own | own |

Notes: ¹ students in the faculty member's courses/cohorts; ² assigned mentees;
³ students with an open task in that domain; ⁴ via verified
`student_account_links`, limited fields; ⁵ cases where the user is owner or a
task assignee; ⁶ escalations the user initiated.

**Open decision:** the source of course/cohort assignment for scope ¹ and ²
(there is no such table in the current schema).

## 4. Data classification

| Class | Examples | Rules |
|---|---|---|
| Restricted | Finance observations, restricted task details, counselling notes, pulse reflections, call-request notes | Separate tables; dedicated routes; encrypted at rest at application level (recommended); never in logs, AI prompts, analytics rows or third-party calls (INV-05) |
| Confidential | Student names, external refs, observations, cases, follow-ups | Campus-scoped, role-scoped; never sent to third parties without a data-processing agreement (audit F1) |
| Internal | Policy definitions, catalogue, model metadata | Authenticated read |
| Public | Health probe, identity-collectible metadata (non-PII) | No auth |

## 5. Hardening checklist

| ID | Requirement | Audit |
|---|---|---|
| HARD-01 | CORS allows an explicit origin list per environment; no wildcard patterns with credentials | S8 |
| HARD-02 | Error responses contain a code, a generic message and a request id. No user ids, campus ids, role lists or library exception text | S8 |
| HARD-03 | Request logs exclude all headers except an allowlist (method, path, status, request id, user agent) | S8 |
| HARD-04 | API docs (`/docs`, `/redoc`, `/openapi.json`) disabled or authenticated outside development | S8 |
| HARD-05 | Image optimisation / proxy restricted to an explicit host list | S8 |
| HARD-06 | Rate limits per user and per IP on all routes; tighter limits on prediction, AI, upload, translation | T3 |
| HARD-07 | Uploads: size limit, MIME allowlist, content sniffing, virus scan hook, stored outside web root | — |
| HARD-08 | Security headers on web app: CSP, HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `frame-ancestors` | — |
| HARD-09 | Dependency and secret scanning in CI | T4 |
| HARD-10 | Service-role database keys exist only in backend and worker environments | — |
| HARD-11 | No unauthenticated route that reads or writes student data or money-like balances | S5 |

## 6. Required negative tests

At minimum (extends `docs/docs/04_AUTHORIZATION_PRIVACY.md` §6 and audit T2):

1. Anonymous request to every non-health route → 401.
2. Inactive membership → 403.
3. Cross-campus object access → 404.
4. Signed-in user with no membership calling a campus route → 403, and no
   membership row is created.
5. Mentor reading finance view → 403.
6. Faculty recording a counselling outcome → 403.
7. Leadership listing or mutating cases → 403.
8. Role field in request body ignored.
9. Withdrawn processing authorisation blocks intervention creation.
10. Built client bundle contains no JWTs or secret names.
11. Cohort of 3 → suppressed aggregate.
12. Campus id in request body ignored.
13. Student account cannot read another student's cases by registering a
    similar email.
14. Concurrent case transitions with the same version → exactly one succeeds.
15. Error bodies contain no UUIDs other than the request id.
