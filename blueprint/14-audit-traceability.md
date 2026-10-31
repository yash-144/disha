# 14 · Audit Traceability

Each of the 38 findings in `docs/audit/AUDIT.md` mapped to the blueprint
requirements that prevent it in a rebuild. Severity is as stated in the audit.

Status of the current repository at commit `7df0b08`: S1 has been fixed in
`app/` (just-in-time membership provisioning removed from
`get_campus_membership`). All other findings are open in the audit tracker.

## Critical

| ID | Finding (short) | Blueprint requirements |
|---|---|---|
| S1 | Any signed-up user becomes faculty in any campus | FR-TEN-03, NFR-TEN-04, `membership_invites` table ([03](03-domain-model.md) §2), negative test 4 ([04](04-security-and-access.md) §6) |
| S2 | Pre-issued persona tokens in the JS bundle; default JWT secret | INV-07, NFR-SEC-04, NFR-SEC-05, NFR-SEC-06, CFG-02, FE-10, bundle-scan CI step |
| A2 | Outbox delivery and deadline escalation never run | FR-CASE-08, FR-NOT-02, FR-NOT-03, ARCH-03, ESC-01…06, OUT-01…07, OBS-06 |
| M1 | Model needs features no campus collects | ML-PRE-01…03, ML-FC-01…03 |

## High

| ID | Finding (short) | Blueprint requirements |
|---|---|---|
| S3 | JWKS failure falls back to hardcoded key; issuer optional | NFR-SEC-01, NFR-SEC-02, NFR-SEC-03 |
| S4 | Missing role checks on writes; campus id from body | AUTHZ-01…04, CASE-SM-02, NFR-TEN-01, permission matrix ([04](04-security-and-access.md) §3.2) |
| S5 | Unauthenticated happiness, shop, translate routes | HARD-11, PUL-03, RED-02, FE-12, removed routes ([05](05-api-specification.md) §2.15) |
| S6 | RLS script fails and skips 13 tables | NFR-TEN-05, referential rules ([03](03-domain-model.md) §13), RLS test ([13](13-quality-and-operations.md) §2) |
| S7 | Students matched to accounts by email prefix | FR-TEN-04, `student_account_links` table, negative test 13 |
| A3 | Case version check is a race | FR-CASE-09, NFR-CONC-01, CASE-SM-04, CASE-SM-05, FE-13, concurrency tests |
| A4 | Production state in process memory and local disk | NFR-DUR-01, DOC-01, PTS-01, pulse tables ([03](03-domain-model.md) §10) |
| A5 | Demo and production share one runtime path | INV-07, FE-03, FE-10, demo environment ([13](13-quality-and-operations.md) §4) |
| D1 | Five tables have no migration | Referential rules ([03](03-domain-model.md) §13), migration CI job, DEP-03 |
| D2 | Hardcoded figures served as real data | FR-ANA-01, FR-ANA-04, INV-06, PUL-07, ML monitoring ([08](08-ml-subsystem.md) §7) |
| D3 | Audit events cascade-delete and are editable | AUD-01, `case_events` RESTRICT + hash chain ([03](03-domain-model.md) §6, §13) |
| M2 | Protected attributes as inputs; 3.5× false-positive gap | INV-04, ML-FC-04, fairness gate ([08](08-ml-subsystem.md) §5), NFR-PRIV-01 |
| M3 | 51% flagged at 56% precision | Capacity threshold gate ([08](08-ml-subsystem.md) §5) |
| M4 | "Platt calibrated" label on uncalibrated model | Calibration gate, `calibration_method` in evidence card |
| F1 | All on-screen text sent to Sarvam | FE-18…21, INV-05, AI-12 |
| F2 | Access control only in the browser | FE-01…03, FE-06 |
| T1 | No CI or deployment definition | CI pipeline ([13](13-quality-and-operations.md) §3), DEP-01…06 |
| T2 | No negative authorisation tests | AUTHZ-03, negative tests ([04](04-security-and-access.md) §6) |

## Medium

| ID | Finding (short) | Blueprint requirements |
|---|---|---|
| A1 | Superseded `backend/` prototype in repo | ARCH-01 |
| A6 | Blocking I/O in async routes | NFR-ASYNC-01, DOC-05, DOC-06, ML-SRV-03 |
| A7 | Config split; `.env` AI settings ignored | CFG-01…05, AI-01 |
| A8 | Root clutter and stale claims in docs | HYG-01…05 |
| S8 | CORS, error leaks, header logging, token storage, image proxy, registry front-running, relayer mint, public docs | HARD-01…05, NFR-SEC-07, NFR-SEC-08, DOC-07, NFT-01…03 |
| D4 | SQLite tests hide Postgres failures | Integration tests on Postgres ([13](13-quality-and-operations.md) §2) |
| D5 | N+1 queries, no pagination, ID-prefix matching | NFR-SCALE-01, pagination convention ([05](05-api-specification.md) §1), ING-01 |
| M5 | Serving model not in git, unpinned, unverified | `model_registry_entries`, ML-SRV-01, ML-SRV-02, ML-TRN-02, DEPM-01 |
| M6 | 23 research phases, no promotion path | ML-TRN-01, ML-TRN-03, promotion gate |
| F3 | 2,187-line global store; 1,907-line API client | FE-04, FE-05, FE-07, FE-08 |
| F4 | ESLint skipped; unit tests not run | FE-22…26 |
| F5 | Business rules in the UI layer | FE-11, FE-12, PUL-06 |
| T3 | No rate limits, structured logs or tracing | OBS-01…07, HARD-06 |
| T4 | Unpinned Python deps; `openai` missing | DEPM-01…04, AI-02 |

## Low

| ID | Finding (short) | Blueprint requirements |
|---|---|---|
| D6 | Two error formats; hardcoded display strings; hardcoded model version | Error envelope ([05](05-api-specification.md) §1.1), `user_profiles` table, ML-SRV-02 |
| F6 | Translation mutates React-managed DOM | FE-18, FE-19 |

## Components the audit lists as worth keeping

From the audit section "What to keep". These are design elements, carried
into the blueprint as follows:

| Element | Blueprint location |
|---|---|
| Case state machine and transition table | [07](07-case-workflow-and-worker.md) §1 |
| Pydantic contracts and error envelope | [05](05-api-specification.md) §1 |
| Idempotency design | NFR-IDEM-01, `idempotency_records` |
| Leakage-aware ML evaluation code | [08](08-ml-subsystem.md) §1, §4 |
| Rust CLI session handling (0600 files, atomic writes) | CLI-01 |
| Document-integrity verification logic | [11](11-documents-and-anchoring.md) |
