# backend/ is deprecated

`backend/` (the "Counsellor Module" app) is superseded by `api/`. Its data came from an in-memory
singleton that seeded fake users, imports, invitations, cases and notifications; it must not be deployed.
`api/` is database-backed (PostgreSQL, Alembic), campus-scoped, role-checked and audited.
Nothing here is maintained; the directory stays only for reference until the web client has moved.

Authentication is Google sign-in through Supabase in `api/`. `backend/app/api/auth.py` was not ported.

All new paths are under `/api/v1`. Write requests that create something need an `X-Idempotency-Key` header.

| backend/ endpoint | api/ replacement |
|---|---|
| `GET /counsellor/dashboard` (+ `/summary`, `/upcoming-followups`, `/overdue-cases`) | `GET /counselling/dashboard`; overdue cases: `GET /counselling/caseload?overdue_only=true` |
| `GET/PATCH /counsellor/profile` | `GET/PUT /counselling/profile` |
| `GET /counsellor/students` | `GET /counselling/students` |
| `GET /counsellor/students/{id}`, `/observations`, `/support-history` | not ported as such: support history is `GET /cases?student_id=`; observations belong to the roster/faculty modules |
| `GET /counsellor/followups`, `/followups/history` | `GET /counselling/followups?upcoming_only=true\|false` |
| `GET /cases`, `GET /cases/{id}`, `POST /cases/{id}/accept`, `PATCH /cases/{id}/status`, `POST /cases/{id}/close` | `GET /cases`, `GET /cases/{id}`, `POST /cases/{id}/accept`, `POST /cases/{id}/transition`, `POST /cases/{id}/close` (14-state machine) |
| `GET /cases/{id}/timeline` | `GET /cases/{id}/events` |
| `POST/GET /cases/{id}/notes` | confidential notes: `POST /counselling/notes`, `GET /counselling/students/{student_id}/notes` (counsellors only; reads are audited) |
| `POST/GET /cases/{id}/interventions` | `POST/GET /cases/{id}/interventions`, `PATCH /cases/{id}/interventions/{intervention_id}` |
| `POST /cases/{id}/outcome`, `POST /interventions/{id}/outcome` | `POST /cases/{id}/outcome` |
| `POST/GET /cases/{id}/followups` | `POST/GET /cases/{id}/follow-ups` |
| `PATCH /followups/{id}/complete`, `POST /followups/{id}/notes` | `POST /cases/{id}/follow-ups/{followup_id}/complete`, `.../notes`; also `PATCH` (reschedule) and `.../cancel` |
| `GET /interventions/catalogue` | `GET /interventions/catalog`; managing it: `POST /interventions/catalog`, `PATCH /interventions/catalog/{id}` (institution admin) |
| `GET /notifications`, `PATCH /notifications/{id}/read` | same paths; plus `GET /notifications/unread-count`, `POST /notifications/read-all`; admins: `GET /notifications/outbox`, `POST /notifications/outbox/{id}/retry` |
| `GET /admin/dashboard` (+ `/summary`, `/counsellor-workload`) | `GET /campus/dashboard` |
| `GET /admin/users`, `GET /admin/users/{id}`, `GET /admin/campus/memberships` | `GET /campus/memberships` |
| `PATCH /admin/memberships/{id}` | `PATCH /campus/memberships/{id}` (role, department, active; last-admin and self-edit guarded) |
| `POST/GET /admin/invitations` | `POST/GET /campus/invitations`, `DELETE /campus/invitations/{id}`. Invitations are by email + role + campus only (no password or token); the invitee is linked on first Google sign-in via `InviteService.claim_for_email` |
| `GET/PATCH /admin/campus` | `GET /campus`, `PATCH /campus` (name, settings: escalation levels, channels, follow-up grace) |
| `GET /admin/cases`, `/cases/overdue`, `/cases/{id}`, `POST /admin/cases/{id}/reassign`, `/timeline`, `/interventions` | `GET /cases`, `GET /counselling/caseload?counsellor_id=&overdue_only=`, `POST /cases/{id}/assign`, `GET /cases/{id}/events`, `GET /cases/{id}/interventions` |
| `GET /admin/audit`, `/admin/audit/{id}` | `/audit` (audit module) |
| `GET /admin/analytics/*` | analytics module (not part of this port) |
| `GET/PATCH /admin/profile`, `POST /admin/profile/change-password` | not ported (identity is Google sign-in; no passwords) |
| `POST /auth/*` | not ported |

Behaviour that changed on purpose (blueprint wins over `backend/`): no seed data of any kind; every write is audited
through the hash-chained audit service; delivery goes through the notification outbox and the worker (not
direct inserts); `institution_admin` cannot read counselling notes or modify active case work; cross-campus access is 404.
