# 10 · Wellbeing Pulse and Rewards

Two optional, related modules. The pulse collects self-reported wellbeing; the
rewards module awards points for participation. Points never depend on what a
student answers.

## 1. Facts about the current implementation

| Item | Location | Fact |
|---|---|---|
| Pulse storage | `app/api/v1/happiness.py` | Module-level Python lists; lost on restart; differs per instance (audit A4) |
| Submission auth | same | None; falls back to a fixed demo user id (audit S5) |
| Reset route | same | `POST /happiness/reset` wipes all submissions, unauthenticated (audit S5) |
| Status route | same | Reports completed if anyone has submitted (audit S5) |
| Aggregate and trends | same, `app/schemas/happiness.py` | Hardcoded index 74.5, six dimension scores, five past weeks; `response_count = 48 + submissions`; `is_demo_data=False` (audit D2) |
| Scoring rules | `frontend/lib/happinessScoring.ts` | Implemented in the browser bundle (audit F5) |
| Questionnaire | `frontend/lib/happinessData.ts` | 6 dimensions, 1 question each |
| Points ledger, stock, redemptions | `frontend/lib/shop-data.ts` | Next.js server singleton in memory (audit A4) |
| Redeem route | `frontend/app/api/shop/redeem/route.ts` | Accepts any `studentId` from the client (audit S5) |
| Rewards rules | `frontend/lib/rewardsScoring.ts` | Activity points, catalogue, leaderboard ranking in client code |

## 2. Pulse questionnaire

Dimensions in the current questionnaire (`v1.0-weekly`):

| Key | Name |
|---|---|
| `emotional_wellbeing` | Emotional wellbeing |
| `belonging_community` | Belonging and community |
| `academic_experience` | Academic experience |
| `support_trust` | Support and trust |
| `safety_respect` | Safety and respect |
| `growth_confidence` | Growth and confidence |

Each question uses a 1–5 Likert scale. An optional free-text reflection
(max 2,000 characters) is accepted.

**Requirements:**
- **PUL-01** Questionnaires are versioned records; submissions reference the
  version they answered.
- **PUL-02** One submission per student per period (unique constraint).
- **PUL-03** The submitting student is resolved from the verified account link;
  no client-supplied student id.
- **PUL-04** Reflections are restricted data: encrypted at rest, excluded from
  aggregates, AI prompts, translation and logs. **Open decision:** who, if
  anyone, may read individual reflections, and the safeguarding procedure for
  reflections indicating risk of harm.
- **PUL-05** Periods are records with start and end; "current period" is
  computed from them, not hardcoded (current schema defaults `period_id = "w6"`).

## 3. Pulse scoring (rules carried over from `happinessScoring.ts`)

| Step | Rule |
|---|---|
| Validate | Response must be an integer 1–5; others are excluded, never treated as 0 or 50 |
| Normalise | `(r − 1) / 4 × 100` → 1→0, 2→25, 3→50, 4→75, 5→100 |
| Dimension score | Mean of valid normalised responses; null if none; rounded to 1 decimal |
| Index | Equal-weighted mean of non-null dimension scores; null if none; rounded to 1 decimal |
| Change | Absolute point change vs previous period (not percentage) |
| Bands | `strong` 80–100 · `positive` 65–79.99 · `needs_attention` 50–64.99 · `priority_review` 0–49.99 |
| Display threshold | Aggregates shown only when respondents ≥ 10 (`HAPPINESS_MIN_SAMPLE_THRESHOLD`) |

**Requirements:**
- **PUL-06** Scoring runs in the API; the web app only displays results.
- **PUL-07** Aggregates report `response_count`, `eligible_count` (active
  students in scope) and `participation_rate`, all computed.
- **PUL-08** Below the threshold, the API returns `suppressed: true` and no
  scores.
- **Open decision:** the bands are labelled "provisional product-design" in
  the current code; their validity as a measurement instrument is not
  established.

## 4. Points

Activities in the current catalogue (`ELIGIBLE_ACTIVITIES`):

| Key | Points | Frequency |
|---|---|---|
| `weekly_pulse` | 10 | Once per reporting week |
| `daily_micro_challenge` | 5 | Once per challenge |
| `approved_workshop` | 15 | Once per event |
| `student_development` | 10 | Once per activity |
| `verified_learning` | 10 | Once per activity |
| `campus_improvement` | 20 | Once per initiative |

Invariant in current code: pulse points are always 10, independent of answers
(`assertPulseDecoupling`).

**Requirements:**
- **PTS-01** Points are an append-only ledger in the database; balance is the
  sum of entries.
- **PTS-02** Award entries carry an idempotency key `(student, activity_key,
  source_ref)`, so an activity cannot be claimed twice.
- **PTS-03** Only the system (for pulse) or an authorised staff role (for
  verified activities) creates award entries.
- **PTS-04** Points amount never depends on pulse answers.

## 5. Rewards catalogue and redemption

Current catalogue items include a digital badge (100 points) and a sticker
pack (200 points); `shop-data.ts` defines `ELIGIBILITY_THRESHOLD_POINTS = 500`
and a merchandise catalogue with categories `apparel`, `stationery`,
`desk-tech`, `accessories`.

Redemption checks in current code: item available; stock > 0; balance ≥ cost.

**Requirements:**
- **RED-01** Redemption is a database transaction: lock item row, check
  stock and balance, insert negative ledger entry and redemption row, decrement
  stock.
- **RED-02** Student from verified link only; idempotency key required.
- **RED-03** Fulfilment status updated by staff.

## 6. Leaderboard

Current rules: rank by points in period (desc), then activity count (desc),
then display name; standard competition ranking; display name reduced to
first name + last initial.

**Open decision:** whether a public leaderboard is kept. A leaderboard of
named minors is personal data processing; if kept, it must be opt-in.
