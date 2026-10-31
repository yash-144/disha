# 06 · Ingestion and Rules Engine

## 1. Import contract

**Current implementation:** `app/services/ingestion.py`, `app/schemas/ingestion.py`.

### 1.1 Request

```json
{
  "source_system": "lms_export",
  "schema_version": "1.0",
  "observations": [
    {
      "external_student_ref": "STU-1007",
      "domain": "attendance",
      "metric_key": "attendance_rate",
      "value": 0.71,
      "unit": "ratio",
      "quality_state": "valid",
      "event_at": "2026-09-30T00:00:00Z",
      "available_at": "2026-10-01T06:00:00Z",
      "source_system": "lms_export",
      "source_record_ref": "att-2026-09-STU-1007",
      "source_version": 1
    }
  ],
  "finance_observations": [
    {
      "external_student_ref": "STU-1007",
      "fee_support_status": "review_requested",
      "quality_state": "valid",
      "event_at": "…", "available_at": "…",
      "source_system": "fees", "source_record_ref": "…", "source_version": 1
    }
  ]
}
```

### 1.2 Processing rules

| Step | Rule | Row error code |
|---|---|---|
| 1 | Same `Idempotency-Key` for the campus → return the stored import result | — |
| 2 | Compute SHA-256 of canonical JSON payload → `file_digest` | — |
| 3 | Student ref must exist in campus | `UNKNOWN_STUDENT_REFERENCE` |
| 4 | `available_at` ≥ `event_at` (if `available_at` missing, set to `event_at`) | `INVALID_TEMPORAL_SEQUENCE` |
| 5 | Domain in allowed set; metric key in the metric registry for that domain (new) | `UNKNOWN_DOMAIN`, `UNKNOWN_METRIC` |
| 6 | Value type matches metric registry (new) | `INVALID_VALUE_TYPE` |
| 7 | `(source_system, source_record_ref, source_version)` already present → count as duplicate | — |
| 8 | Insert accepted rows; finance rows go to the restricted table | — |
| 9 | Write `source_imports` row with counts and errors | — |

**Requirements:**
- **ING-01** Steps 3–7 run as set-based queries (one query per batch, not per
  row). Current code runs one duplicate query per row.
- **ING-02** Maximum batch size is configured; larger files go through an async
  import job with status polling.
- **ING-03** A metric registry table defines `(domain, metric_key, value_type,
  unit, description)`. The current system has no registry; metric keys are free
  text.
- **ING-04** CSV upload is converted to the same JSON contract before
  validation.
- **ING-05** Roster import (students) is a separate import type with its own
  contract (new; students are seeded only today).

## 2. Temporal integrity

- **TMP-01** Every evaluation has a cutoff `T`. Only rows with
  `available_at ≤ T` are visible.
- **TMP-02** When several rows exist for the same metric, the most recent
  `event_at` among visible rows is used.
- **TMP-03** Rows with `quality_state` in `stale`, `missing`, `conflicting` are
  not used as evidence for a rule; their presence yields `unknown`.
- **TMP-04** Model features are computed with the same cutoff rule
  ([08](08-ml-subsystem.md)).

## 3. Policy definition

**Current implementation:** `app/services/policy_engine.py`. If a campus has
no published policy, the engine creates version 1 of `ug_attendance_academic_v1`
with these rules (evaluator version `2.0.0`):

| rule_key | domain | metric_key | operator | threshold | suggested_intervention | rationale_code |
|---|---|---|---|---|---|---|
| `attendance_concern` | attendance | `attendance_rate` | `<` | 0.75 | `mentor_check_in` | `ATTENDANCE_BELOW_THRESHOLD_75` |
| `assignment_backlog` | academic | `missing_assignments_count` | `>=` | 2 | `academic_tutoring_offer` | `MULTIPLE_MISSING_ASSIGNMENTS` |
| `faculty_feedback_concern` | faculty_feedback | `support_check_requested` | `==` | true | `mentor_check_in` | `FACULTY_SUPPORT_REQUESTED` |

**Requirements:**
- **POL-01** Policies are created and published by `institution_admin`
  through the API, not auto-created inside an evaluation.
- **POL-02** A published version is immutable; changes create a new version.
- **POL-03** Checksum = SHA-256 of canonical (sorted-key) JSON of the
  definition.
- **POL-04** Supported operators: `<`, `<=`, `>`, `>=`, `==`, `!=`, `in`.
  Rule schema is validated on publish.
- **POL-05** Each rule may declare `window` (aggregate over a time window, for
  example mean attendance over the last 28 days) and `min_observations`. The
  current engine compares only the latest value.
- **POL-06** Each triggered rule records its own rationale code and suggested
  intervention key, which must exist in the active catalogue.

## 4. Evaluation algorithm

```
evaluate(campus, student, cutoff T, policy_version P):
  rows   ← observations(campus, student) where available_at ≤ T
  latest ← for each metric_key, the row with max event_at
  if rows is empty:                    result=unknown, quality=insufficient_evidence
  elif any used row is stale/conflicting: result=unknown, quality=stale_source
  else:
     triggered ← rules r in P where latest[r.metric] satisfies r
     if triggered non-empty:           result=attention_suggested, quality=sufficient
     elif any rule metric missing:     result=unknown, quality=insufficient_evidence
     else:                             result=no_rule_triggered, quality=sufficient
  snapshot ← {student_id, external_ref, T, observation ids, metrics, triggered, policy key+version}
  digest   ← SHA-256(canonical snapshot)
  persist EvidencePacket(snapshot, digest) and Signal(result, quality, explanation)
```

**Current implementation notes (facts):**
- The ordering above matches the current code.
- Each triggered rule's attribution is set to the constant `0.35` in the
  evidence card. **Requirement EV-01:** rule evidence cards show the rule,
  threshold and observed value; no numeric attribution unless computed.
- If all 25 model features are present among the metrics and the model is
  loaded, the engine also calls the ML service and stores the ML evidence card
  inside the signal explanation; errors are logged and skipped.
  **Requirement EV-02:** ML scoring is a separate step with its own log row and
  explicit `ml_applicability` status; it never alters the rule result.
- The evaluation commits in the request. **Requirement EV-03:** bulk
  evaluation (whole cohort) runs as a background job.

## 5. Signal review

**Current implementation:** `POST /signals/{id}/review` with decision
`approve`, `modify`, `dismiss`, `request_more_data`. `approve`/`modify` call
`CaseService.create_case_from_signal`, which returns an existing case if one
exists for the signal, else creates one in state `action_planned` with event
`CASE_CREATED_FROM_SIGNAL` and outbox intent `CASE_ACTION_PLANNED`. If no
intervention is chosen, it defaults to `mentor_check_in`.

**Requirements:**
- **REV-01** `selected_intervention_key` is required for `approve`/`modify`
  and must be active in the campus catalogue; no silent default.
- **REV-02** The intervention's `required_purpose_key` must have an active
  processing authorisation for the student; otherwise 422.
- **REV-03** Review decision, case creation, case event and outbox row are
  committed in one transaction.
- **REV-04** Only signals with `result = attention_suggested` can be approved.
- **REV-05** Re-review of a decided signal is rejected with 409 unless the
  previous decision was `request_more_data`.

## 6. Evidence card format

```json
{
  "card_type": "deterministic_rule_evidence | ml_risk_evidence",
  "source": {"policy_key": "…", "policy_version": 3} ,
  "cutoff": "2026-10-01T00:00:00Z",
  "classification": "attention_suggested",
  "items": [
    {"metric_key": "attendance_rate", "observed": 0.71, "rule": "< 0.75", "observation_id": "…"}
  ],
  "limitations": [
    "Uses only data available on or before the cutoff.",
    "Indicates a need for review; it is not a diagnosis."
  ],
  "digest": "sha256…"
}
```

ML evidence cards use the fields in [08](08-ml-subsystem.md) §6.
