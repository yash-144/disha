# 01 · Product Requirements

## 1. Purpose

The system converts observations about students (attendance, academic work,
participation, skills, faculty feedback, fee status) into reviewable signals,
routes every accepted signal into an owned case with a deadline, and records
what support was given and whether it helped.

Operating principle used throughout: **every alert must lead to a recorded human
decision and, if accepted, to an owned action with a deadline** ("No Alert
Without Action").

## 2. Users and roles

| Role key | Who | Primary use |
|---|---|---|
| `student` | Enrolled student | Own cases and support requests, wellbeing pulse, own identity profile, points |
| `faculty` | Course instructor | Observations, signal review for own students, case work |
| `mentor` | Assigned mentor | Case work for mentees |
| `hod` | Head of department | Department oversight, assignment, overrides |
| `counsellor` | Counselling staff | Counselling tasks, call requests, authority escalation |
| `finance` | Fee / finance office | Finance-domain tasks only |
| `placement` | Placement office | Placement-domain tasks only |
| `leadership` | Dean / executive | Aggregated, suppressed analytics only; no identifiable records |
| `institution_admin` | Campus administrator | Roster, memberships, catalogue, policy configuration |
| `platform_admin` | Operator of the platform | Campus provisioning; no student-data access by default |

**Current implementation:** role strings are inconsistent across the code base.
Backend route guards use `faculty`, `hod`, `mentor`, `counsellor`,
`institution_admin`, `leadership`, `dean`, `superadmin`. The authorisation design
doc lists `faculty, hod, mentor, counsellor, placement, finance, leadership,
institution_admin`. The frontend uses `student, faculty, counselor, dean,
leadership, superadmin`. No `student` membership is created outside seed data
(audit S1).

**Requirement FR-ROLE-01:** one canonical role enumeration, defined once and
shared by backend, database policies and frontend types.

## 3. Functional requirements

### 3.1 Tenancy and membership

- **FR-TEN-01** Every student-related record belongs to exactly one campus
  (`institution_id`).
- **FR-TEN-02** A user acts in a campus only through an active membership
  record with one or more roles.
- **FR-TEN-03** Memberships are created only by an `institution_admin` invite,
  a verified roster import, or a `platform_admin` bootstrap action. No
  membership is created as a side effect of signing in (audit S1).
- **FR-TEN-04** A student user account is linked to a student record only by an
  explicit, admin-verified link (audit S7). Email prefix or any string
  similarity is never used for matching.

### 3.2 Roster and observations

- **FR-OBS-01** Admins can create, update and deactivate student records
  (external reference, display name, cohort, enrolment status).
  *Current implementation:* students are created only by seed scripts
  (`scripts/seed_demo_data.py`, `scripts/seed_pitch_fixtures.py`).
- **FR-OBS-02** Batch import of observations across five general domains
  (`attendance`, `academic`, `participation`, `skills`, `faculty_feedback`) and
  one restricted domain (fee support status).
- **FR-OBS-03** Each observation stores `event_at`, `available_at` and
  `ingested_at`, a source system, a source record reference, a source version
  and a quality state (`valid`, `stale`, `missing`, `conflicting`).
- **FR-OBS-04** Re-importing the same (source system, record ref, version) is a
  no-op counted as duplicate.
- **FR-OBS-05** Every import returns per-row accept / duplicate / reject counts
  and per-row error codes.

### 3.3 Signals

- **FR-SIG-01** A versioned, deterministic rule policy evaluates a student's
  observations as of a cutoff time and produces a signal with result
  `attention_suggested`, `no_rule_triggered` or `unknown`.
- **FR-SIG-02** Observations with `available_at` after the cutoff are excluded.
- **FR-SIG-03** Missing, stale or conflicting evidence yields `unknown`, never
  an imputed value.
- **FR-SIG-04** Each signal stores a frozen evidence snapshot and its SHA-256
  digest so the evaluation can be replayed.
- **FR-SIG-05** A human reviews each `attention_suggested` signal with one of
  `approve`, `modify`, `dismiss`, `request_more_data`, plus a reason code.
- **FR-SIG-06** `approve` or `modify` creates exactly one case per signal.
- **FR-SIG-07** Optional ML risk scores attach to a signal as a separate
  evidence card; they never create a signal or case by themselves.

### 3.4 Cases

- **FR-CASE-01** A case has one accountable primary owner, a due date, a
  selected intervention from the campus catalogue, and a state from the state
  machine in [07](07-case-workflow-and-worker.md).
- **FR-CASE-02** Assignment and acceptance are separate steps; only the
  assignee (or an authorised override) accepts.
- **FR-CASE-03** Cases contain tasks per domain (`academic`, `mentor`,
  `finance`, `placement`, `counselling`). Sensitive task details are stored
  separately and visible only to the authorised domain role.
- **FR-CASE-04** Follow-ups record type, contact status, proof kind, time and a
  sanitised note.
- **FR-CASE-05** Outcomes record `helped`, `not_helped`, `mixed` or `unknown`,
  an evidence kind and a rationale. `unknown` stays in reporting denominators.
- **FR-CASE-06** Override and reopen require a reason code and rationale and
  preserve the prior history.
- **FR-CASE-07** Every state change writes an append-only audit event.
- **FR-CASE-08** Overdue cases are escalated automatically by a scheduled
  process, exactly once per deadline (audit A2).
- **FR-CASE-09** Concurrent edits to the same case are detected atomically; the
  client must send the version it read (audit A3).

### 3.5 Notifications

- **FR-NOT-01** Business transactions write notification intents to an outbox
  table in the same transaction.
- **FR-NOT-02** A running worker delivers outbox items through real channel
  adapters (in-app, email, SMS, or other chosen channels), with retries and a
  dead-letter state (audit A2).
- **FR-NOT-03** An item is marked `sent` only after the adapter confirms
  delivery.

### 3.6 Counselling support

- **FR-COU-01** Counsellor profile onboarding with states `NOT_STARTED`,
  `INCOMPLETE`, `PENDING_VERIFICATION`, `APPROVED`, `REJECTED`, `SUSPENDED`;
  approval by an authorised role.
- **FR-COU-02** Campus directory of authority contacts by escalation category
  (`academic_support`, `student_welfare`, `counseling_supervisor`,
  `institutional_emergency`, `campus_medical`).
- **FR-COU-03** Escalation records linking student, optional case, contact,
  reason and status (`initiated`, `contact_attempted`, `contact_confirmed`,
  `follow_up_required`, `resolved`).
- **FR-COU-04** Students can request a counsellor call (preferred method and
  slot, optional note). Status values: `requested`, `awaiting_assignment`,
  `assigned`, `contact_attempted`, `contact_completed`, `closed`.

### 3.7 Analytics

- **FR-ANA-01** Cohort operational metrics computed from stored rows only
  (signals, cases, outcomes, pulse submissions). No hardcoded figures (audit D2).
- **FR-ANA-02** Groups below the minimum cell size are suppressed and marked as
  suppressed. **Open decision:** a single minimum cell size. The current code
  uses 5 for cohort analytics (`app/api/v1/analytics.py:271`) and 10 for
  happiness aggregates (`frontend/lib/happinessScoring.ts`).
- **FR-ANA-03** Leadership sees aggregates only.
- **FR-ANA-04** Any illustrative or sample figure is labelled as such in the
  API response and the UI.

### 3.8 Optional modules

These exist in the current system. Each is optional for a first release and is
specified in its own document.

| Module | Spec | Note |
|---|---|---|
| ML risk scoring | [08](08-ml-subsystem.md) | Requires partner-campus training data (audit M1) |
| AI review briefs | [09](09-ai-assistance.md) | Advisory only |
| Wellbeing pulse | [10](10-wellbeing-pulse-and-rewards.md) | Holds sensitive free text |
| Points and rewards shop | [10](10-wellbeing-pulse-and-rewards.md) | Currently frontend-only with in-memory ledger |
| Document integrity and anchoring | [11](11-documents-and-anchoring.md) | Uses a public test chain |
| Student identity collectible (NFT) | [11](11-documents-and-anchoring.md) | Uses a public test chain |
| CBDC voucher boundary | [02](02-system-architecture.md) §7 | Simulated provider only |
| Courses, community, messages, internships, calendar | [12](12-frontend-architecture.md) | Currently UI with bundled static data, no backend |
| Command-line client | [02](02-system-architecture.md) §6 | Rust |
| 3D avatar customiser | [02](02-system-architecture.md) §6 | Separate Next.js app |
| UI localisation (Indian languages) | [12](12-frontend-architecture.md) | Must not send record data to a third party (audit F1) |

## 4. Product invariants

- **INV-01** No rule, model or AI output creates a case, contacts a student or
  changes a record without a human action.
- **INV-02** No disciplinary sanction workflow exists in the system.
- **INV-03** No rule, model or AI output assigns a clinical or psychological
  label.
- **INV-04** Protected attributes (gender, disability, age band, deprivation
  index, caste, religion, region or equivalents) are never model inputs; they
  may be used only for fairness auditing (audit M2).
- **INV-05** Finance and counselling details are never included in general
  DTOs, logs, AI prompts or third-party calls.
- **INV-06** Every figure shown as data is computed from storage or labelled
  illustrative.
- **INV-07** Production builds contain no demo personas, demo tokens, mock API
  responses or runtime demo toggles (audit A5, S2).

## 5. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-REP-01 | Replaying a stored evidence snapshot against its policy version produces the same result |
| NFR-IDEM-01 | Consequential POSTs accept an `Idempotency-Key`; a repeat with the same key and body returns the stored response; a repeat with a different body returns 409 |
| NFR-CONC-01 | Case mutations use atomic optimistic locking (`UPDATE … WHERE version = :v`) |
| NFR-DUR-01 | All production state is in the database or object storage; nothing in process memory or local disk (audit A4) |
| NFR-ASYNC-01 | No blocking network, file or CPU-heavy call runs on the async event loop (audit A6) |
| NFR-SCALE-01 | All list endpoints paginate; no N+1 query patterns on list endpoints (audit D5) |
| NFR-SEC-* | See [04](04-security-and-access.md) |
| NFR-OPS-* | See [13](13-quality-and-operations.md) |
| NFR-PRIV-01 | Compliance review against India's Digital Personal Data Protection Act 2023 before processing data of minors (audit M2) |

## 6. Out of scope

- Replacing a student information system or learning management system.
- Clinical records.
- Automated parent or guardian contact.
- Autonomous agents with write access.
- Claims of causal retention uplift from correlational model metrics.
- Live integration with a vendor system without an official schema and sandbox.

## 7. Glossary

| Term | Meaning |
|---|---|
| Observation | One timestamped fact about a student from a source system |
| Cutoff | The time "as of" which an evaluation is made; later data is invisible |
| Policy version | Immutable, checksummed set of rules |
| Evidence packet | Frozen snapshot of inputs to one evaluation, with digest |
| Signal | Result of one evaluation for one student |
| Case | Owned unit of support work created from a reviewed signal |
| Task | Domain-specific piece of work inside a case |
| Follow-up | Record of a contact or support action |
| Outcome | Recorded judgement of whether support helped |
| Outbox | Table of pending side effects written transactionally |
| Small-cell suppression | Hiding aggregates for groups below a minimum size |
| Anchoring | Writing a document hash to a blockchain to prove later integrity |
