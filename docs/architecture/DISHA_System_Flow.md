---
title: DISHA System Flow
tags: [disha, architecture, flow]
---

# DISHA — How the Whole System Works

A visual map of DISHA from start to finish: who uses it, how a college's data
gets in, how a student gets flagged, and what happens after. Every section has
one diagram and a short plain-language explanation.

> [!info] How to read the diagrams
> - Read **top to bottom** or **left to right**, following the arrows.
> - 🟩 **Green** = built and working today.
> - 🟨 **Yellow** = planned (designed in `blueprint/`, folder exists, logic not written yet).
> - 🟦 **Blue** = a person does this.
> - 🟥 **Red** = sensitive data with extra protection.

## Contents

1. [[#1. The big picture]]
2. [[#2. Who uses DISHA]]
3. [[#3. How a college's data gets in (ingestion)]]
4. [[#4. What data we take in]]
5. [[#5. Inside the import check]]
6. [[#6. How a student gets flagged (signals)]]
7. [[#7. The ML model up close]]
8. [[#8. How the ML model is trained and updated]]
9. [[#9. Review, cases and follow-up]]
10. [[#10. Deadlines, reminders and escalation]]
11. [[#11. Security on every request]]
12. [[#12. Reports and the learning loop]]
13. [[#13. Extra modules]]
14. [[#14. One student, start to finish]]
15. [[#15. What is built vs planned]]

---

## 1. The big picture

```mermaid
flowchart TB
    subgraph IN["A. Data comes in"]
        direction LR
        SRC["College systems<br/>ERP, exam cell, attendance,<br/>LMS, fee office"]:::planned
        ING["1. Ingestion<br/>bring data in and check it"]:::planned
        DB[("2. Database<br/>students and observations")]:::planned
        SRC --> ING --> DB
    end
    subgraph DEC["B. DISHA decides who needs help"]
        direction LR
        SIG["3. Signal engine<br/>rules + ML model"]:::built
        REV["4. Human review<br/>mentor approves or dismisses"]:::human
        SIG --> REV
    end
    subgraph ACT["C. People act, results are tracked"]
        direction LR
        CASE["5. Case<br/>owner, tasks, deadline"]:::built
        WRK["6. Worker<br/>reminders and escalation"]:::built
        OUT["7. Outcome<br/>did the support help?"]:::human
        ANA["8. Analytics<br/>dashboards"]:::planned
        WRK --> CASE --> OUT --> ANA
    end

    LEARN["Outcomes become new training data<br/>so the ML model improves each term"]:::built

    IN --> DEC --> ACT
    ACT -.-> LEARN

    classDef built fill:#d4edda,stroke:#2e7d32,color:#1b1b1b
    classDef planned fill:#fff3cd,stroke:#b8860b,color:#1b1b1b
    classDef human fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
```

**In one sentence:** college data comes in, DISHA spots students who may be at
risk, a person decides what to do, the action is tracked until it is done, and
the result teaches the system for next time.

**Golden rule — "No Alert Without Action":** every alert must lead to a human
decision and, if accepted, to an owned task with a deadline.

---

## 2. Who uses DISHA

```mermaid
flowchart TB
    subgraph STAFF["Staff who act on students"]
        direction LR
        FAC["Faculty<br/>teacher"]:::human
        MEN["Mentor"]:::human
        HOD["Head of<br/>department"]:::human
        COU["Counsellor"]:::human
        FIN["Finance<br/>office"]:::human
        PLA["Placement<br/>office"]:::human
        FAC ~~~ MEN ~~~ HOD ~~~ COU ~~~ FIN ~~~ PLA
    end
    subgraph OVERSIGHT["Oversight"]
        direction LR
        LEAD["Leadership / Dean<br/>sees totals only"]:::human
        ADM["Campus admin<br/>sets up the campus"]:::human
        ADM ~~~ LEAD
    end
    STU["Student"]:::human
    PLAT["Platform admin<br/>creates new campuses"]:::human

    PLAT --> OVERSIGHT
    OVERSIGHT -->|"admin invites staff, uploads data, sets rules;<br/>leadership reads dashboards"| STAFF
    STAFF -->|"review alerts, run cases"| STU
    STU -->|"requests help, weekly pulse"| STAFF

    classDef human fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
```

| Role | Main job in DISHA | Can see |
|---|---|---|
| Student | Ask for help, see own case status, weekly wellbeing pulse | Only their own records |
| Faculty | Raise concerns, review alerts for their students | Their students |
| Mentor | Work on cases of assigned mentees | Assigned students |
| Head of department (HOD) | Assign cases, override, oversee department | Whole department |
| Counsellor | Counselling tasks, call requests, escalations | Counselling details of their cases |
| Finance / Placement | Their own type of task only | Only their task details |
| Leadership | Department and campus trends | **Totals only, never individual students** |
| Campus admin | Invite users, upload data, manage rules and catalogue | Settings, not private student details |
| Platform admin | Create campuses | No student data by default |

> [!warning] Nobody gets access by just signing up
> A person only gets a role through an **invite** from the campus admin or a
> **verified roster**. A student account is linked to a student record only by
> an admin.

---

## 3. How a college's data gets in (ingestion)

Different colleges keep data in different ways, so DISHA accepts several
**ways in**. Every way ends up in the **same import check**, so the rest of the
system works the same whatever the college uses.

```mermaid
flowchart TB
    subgraph WAYS["Ways a college can send data"]
        W1["A. Upload a file<br/>CSV or Excel in the web app<br/>+ column-matching step"]:::planned
        W2["B. Connect their system<br/>ERP / SIS sends JSON<br/>to the DISHA API"]:::planned
        W3["C. Scheduled file drop<br/>nightly export to a shared folder"]:::planned
        W4["D. Typed in by staff<br/>concerns, feedback, attendance"]:::planned
        W5["E. Command-line tool<br/>for technical staff"]:::planned
    end

    MAP["Column matching<br/>their headers -> DISHA fields<br/>their grade scale -> 0-20<br/>their outcome words -> standard"]:::built
    CON["One standard format<br/>the Import Contract"]:::planned
    CHK["Import check<br/>see section 5"]:::planned
    REP["Import report<br/>accepted / duplicate / rejected<br/>+ reason for each bad row"]:::planned

    W1 --> MAP
    W3 --> MAP
    MAP --> CON
    W2 --> CON
    W4 --> CON
    W5 --> CON
    CON --> CHK --> REP
```

| Way in | Best for | What the college does | Status |
|---|---|---|---|
| **A. File upload** | Most colleges (data lives in Excel) | Download from their system, upload, match columns once | Planned. Column matching already works in the ML tool (`mapping.json`) |
| **B. API (JSON)** | Colleges with a modern ERP | Their IT connects to `POST /api/v1/imports` | Planned (designed in blueprint 05, 06) |
| **C. Scheduled drop** | Regular nightly or weekly updates | Their system saves a file to a shared folder every night | Planned (optional) |
| **D. Typed in** | Things not in any system: a teacher's concern, feedback | Staff fill a form in DISHA | Planned |
| **E. CLI** | Admins comfortable with a terminal | Run one command with the file | Planned (folder exists) |

**Accepted file formats:** CSV (comma or semicolon), Excel (`.xlsx`, converted
to CSV), JSON. Headers can be in any wording; the column-matching step maps
them once and remembers the mapping.

> [!tip] Column matching already exists
> The ML tool can already read any college's file with a small mapping file:
> their column names, their grade scale (SGPA 0–10, percent 0–100) and their
> outcome words ("Dropped out", "Passed out"). See `ml/README.md` §17. The
> planned upload screen reuses the same idea.

---

## 4. What data we take in

```mermaid
flowchart TB
    subgraph GEN["General data"]
        R["Roster<br/>student id, name, course, year"]:::planned
        P["Prior marks<br/>class 12 %, entrance score"]:::planned
        A["Academic results<br/>subjects registered, passed,<br/>exams sat, SGPA / grade"]:::built
        AT["Attendance<br/>% per subject or month"]:::planned
        IM["Internal marks<br/>mid-semester tests"]:::planned
        PA["Participation<br/>LMS logins, activities"]:::planned
        FB["Faculty feedback<br/>support check requested"]:::planned
    end
    subgraph RES["Restricted data"]
        FE["Fee status<br/>finance office only"]:::restricted
        CN["Counselling notes<br/>counsellor only"]:::restricted
    end
    subgraph LBL["Outcome"]
        OUT["Final outcome<br/>graduated / dropped out /<br/>still enrolled late"]:::built
    end

    classDef built fill:#d4edda,stroke:#2e7d32,color:#1b1b1b
    classDef planned fill:#fff3cd,stroke:#b8860b,color:#1b1b1b
    classDef restricted fill:#fde2e1,stroke:#c62828,color:#1b1b1b
```

- **General data:** staff can see it (within their role), and the rules and ML model use it.
- **Restricted data:** only the right office sees it; it is never sent to AI or shown in reports.
- **Outcome:** used only to train and test the ML model.

| Data | Example fields | How often | Used by | Needed? |
|---|---|---|---|---|
| Roster | student id, name, course, year, status | Start of term | Everything | **Required** |
| Academic results | subjects registered, subjects passed, exams sat, absent, SGPA | Each semester | ML model + rules | **Required for ML** |
| Final outcome | graduated / dropped out / still enrolled | End of programme | Training only | **Required to train** |
| Prior marks | class 10/12 %, entrance score | Once | ML (admission check) | Recommended |
| Attendance | attendance % | Weekly or monthly | Rules today, ML later | Recommended |
| Internal marks | mid-sem test marks | Mid-semester | Rules, ML later (earlier warning) | Recommended |
| Faculty feedback | "needs support" yes/no | Any time | Rules | Optional |
| Participation | LMS logins, activities | Weekly | Rules, ML later | Optional |
| Fee status 🟥 | review requested / in progress / resolved | Any time | Finance tasks only | Optional |
| Gender, age, disability | as recorded | Once | **Fairness check only, never the model** | Optional |

**Every observation carries two dates:**

- **When it happened** (`event_at`), e.g. the exam date.
- **When staff could see it** (`available_at`), e.g. the result publication date.

DISHA only uses data that was **available** at the moment it makes a
decision. This stops the system from "cheating" with results nobody had yet.

---

## 5. Inside the import check

```mermaid
flowchart TD
    IN["Import arrives<br/>with an Idempotency-Key"]:::planned
    Q1{"Same key<br/>seen before?"}
    OLD["Return the earlier result<br/>nothing is added twice"]
    Q2{"Student exists<br/>in this campus?"}
    E1["Reject row<br/>UNKNOWN_STUDENT"]:::bad
    Q3{"Dates make sense?<br/>available after event"}
    E2["Reject row<br/>INVALID_DATES"]:::bad
    Q4{"Known field<br/>and right type?"}
    E3["Reject row<br/>UNKNOWN_FIELD / BAD_VALUE"]:::bad
    Q5{"Exact same record<br/>already stored?"}
    DUP["Count as duplicate<br/>skip"]
    Q6{"Restricted<br/>data?"}
    RSTORE[("Restricted table<br/>fees, counselling")]:::restricted
    STORE[("Observations table")]:::planned
    REPORT["Import report<br/>counts + error per row"]:::planned

    IN --> Q1
    Q1 -- yes --> OLD
    Q1 -- no --> Q2
    Q2 -- no --> E1
    Q2 -- yes --> Q3
    Q3 -- no --> E2
    Q3 -- yes --> Q4
    Q4 -- no --> E3
    Q4 -- yes --> Q5
    Q5 -- yes --> DUP
    Q5 -- no --> Q6
    Q6 -- yes --> RSTORE
    Q6 -- no --> STORE
    STORE --> REPORT
    RSTORE --> REPORT
    E1 --> REPORT
    E2 --> REPORT
    E3 --> REPORT
    DUP --> REPORT

    classDef planned fill:#fff3cd,stroke:#b8860b,color:#1b1b1b
    classDef restricted fill:#fde2e1,stroke:#c62828,color:#1b1b1b
    classDef bad fill:#f8d7da,stroke:#a71d2a,color:#1b1b1b
```

- A bad row never blocks the good rows; the college gets a clear list of what
  to fix.
- Sending the same file twice is safe: duplicates are detected, not doubled.
- Data cleaning already built in the ML tool: a semester with every field 0 is
  treated as **missing**, impossible counts are capped, and a grade of 0 with
  nothing passed is treated as "no grade".

---

## 6. How a student gets flagged (signals)

Two checkers look at every student. They work separately, then their results
are combined.

```mermaid
flowchart TB
    OBS[("Student's data<br/>only what was available<br/>at this moment")]

    subgraph RULES["Rules checker (simple, readable)"]
        R1["Attendance below 75%?"]:::planned
        R2["Passed under half the subjects?"]:::built
        R3["Skipped any exam?"]:::built
        R4["2+ subjects failed?"]:::built
        R5["Grade dropped 2+ points?"]:::built
    end

    subgraph ML["ML model (combines many signs)"]
        M1["Build warning signs"]:::built
        M2["Model gives % chance<br/>of dropping out"]:::built
    end

    OBS --> RULES
    OBS --> ML
    RULES --> COMB{"Combine"}
    ML --> COMB

    COMB --> HIGH["HIGH<br/>very likely at risk<br/>-> alert"]:::high
    COMB --> MED["MEDIUM<br/>likely AND a rule agrees<br/>-> alert"]:::med
    COMB --> WATCH["WATCH<br/>some risk<br/>-> listed, no alert"]:::watch
    COMB --> OK["ON TRACK<br/>-> nothing"]:::ok

    HIGH --> CAP["Capacity cap<br/>max 15% of students alerted"]
    MED --> CAP
    CAP --> REVIEW["Mentor review queue<br/>with plain-language reasons"]:::human

    classDef built fill:#d4edda,stroke:#2e7d32,color:#1b1b1b
    classDef planned fill:#fff3cd,stroke:#b8860b,color:#1b1b1b
    classDef human fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
    classDef high fill:#f8d7da,stroke:#a71d2a,color:#1b1b1b
    classDef med fill:#ffe5cc,stroke:#cc6600,color:#1b1b1b
    classDef watch fill:#fff9db,stroke:#b8860b,color:#1b1b1b
    classDef ok fill:#e8f5e9,stroke:#2e7d32,color:#1b1b1b
```

- **Rules** give exact, checkable reasons ("passed 2 of 6 subjects").
- **The ML model** weighs many signs at once and gives a percentage.
- An alert needs either a **very high** model score, or a **fairly high**
  score **plus** a rule agreeing. This keeps false alarms low.
- The **capacity cap** makes sure mentors can follow up on every alert.
- The picture shows the legacy semester models (15% cap). The primary rolling
  model uses the same tier logic with a 25% cap per course, term and day; see
  section 7.

---

## 7. The ML model up close

```mermaid
flowchart TB
    subgraph WHEN["1. When it runs"]
        direction LR
        C0["cp0<br/>at admission"]:::built
        C1["cp1<br/>after semester 1<br/>MAIN CHECK"]:::built
        C2["cp2<br/>after semester 2"]:::built
        C0 ~~~ C1 ~~~ C2
    end

    subgraph SIGNS["2. Warning signs it calculates"]
        direction LR
        F1["Pass rate<br/>passed / registered"]
        F2["Exams<br/>skipped"]
        F3["Subjects<br/>failed"]
        F4["Average<br/>grade"]
        F5["Change since<br/>last semester"]
        F6["Prior marks<br/>+ course"]
        F1 ~~~ F2 ~~~ F3 ~~~ F4 ~~~ F5 ~~~ F6
    end

    subgraph MODEL["3. The model"]
        direction LR
        GB["Gradient boosting<br/>a few hundred small<br/>decision trees"]:::built
        CAL["Calibration<br/>80% means 8 in 10"]:::built
        CUT["Cutoff<br/>alert only if 85% of<br/>such students really<br/>are at risk"]:::built
        GB --> CAL --> CUT
    end

    subgraph RESULT["4. What it outputs"]
        direction LR
        P["Risk %"]
        T["Tier<br/>HIGH / MEDIUM /<br/>WATCH / ON TRACK"]
        WHY["Top 3 reasons"]
        P ~~~ T ~~~ WHY
    end

    WHEN --> SIGNS --> MODEL --> RESULT

    classDef built fill:#d4edda,stroke:#2e7d32,color:#1b1b1b
```

### 7a. The primary model: rolling risk (scores whenever marks arrive)

Instead of three fixed checkpoints, the rolling model scores a student at
**every assessment due date** ("whenever marks reach the ERP"), using only data
up to that day, and skips students who have already withdrawn.

```mermaid
flowchart LR
    T["Six tables from the ERP<br/>students, enrolments, assessments,<br/>results, activity, withdrawals"]:::built
    S["Snapshot at day t<br/>only data up to t"]:::built
    M["23 features -> calibrated model<br/>risk of Fail or Withdrawn"]:::built
    P["Insights payload (JSON)<br/>tier, change, history, reasons,<br/>drift events, next check,<br/>course views, data drift"]:::built
    H["Mentor review queue"]:::human
    K["Meko memory<br/>only when tier changes<br/>or drift event"]:::built
    T --> S --> M --> P --> H
    P -.-> K
    classDef built fill:#d4edda,stroke:#2e7d32,color:#1b1b1b
    classDef human fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
```

| Measured on the held-out 2014J term (OULAD) | Result |
|---|---|
| Ranking quality (ROC AUC) | 0.857 overall; 0.727 at 10% of the term, 0.809 at 25%, 0.881 at 50%, 0.933 at 75% |
| Accuracy over all snapshots | 79.0% (always predicting "fine" scores 64.6%) |
| Withdrawn students flagged before leaving | 70.5%, a median 54 days ahead |
| Overfit check (train / grouped CV / test AUC) | 0.894 / 0.883 / 0.857 |

What the backend receives per student: risk %, tier, change since last marks,
history, top reasons, what is going well, drift events and the next check date.
The full field list is in [INSIGHTS_SPEC.md](INSIGHTS_SPEC.md). **Not yet
implemented:** an API route or worker job that runs the scorer; today it is a
library call and a CLI (`python -m disha_ml.rolling.score`).

### 7b. Legacy semester models (secondary)

| Checkpoint | Sees | Alert precision* | Catches (recall) | Accuracy, all 851 students | Use? |
|---|---|---|---|---|---|
| cp0 — admission | Prior marks, course | 65% (only 20 alerts) | 5% | not computed | Not approved (too weak) |
| cp1 — after semester 1 | + semester 1 results | 94.5% | 46% | about 84% | ✅ Approved |
| cp2 — after semester 2 | + semester 2 + change | 97.6% | 47% | about 88% | ✅ Approved |

\* Precision = of the students who received an alert (after the capacity cap),
the share who really were at risk. It is **not** accuracy. Always predicting
"not at risk" would be right 69% of the time on this test group. Most cp2 alerts
were students who had already passed zero semester-2 subjects, so cp2 mostly
confirms students who have stopped; that is why the rolling model drops
withdrawn students and scores earlier.

> [!note] Never used as model inputs
> Gender, age, disability, family background and fees. Gender, age and
> disability are used only to **check fairness** after scoring.

Full explanation: `docs/DISHA_ML_Team_Brief.pdf` and `ml/README.md`.

---

## 8. How the ML model is trained and updated

Training happens **outside** the live platform (on Kaggle or a laptop), and
only a checked model is allowed in.

```mermaid
flowchart TD
    D1["Past students with<br/>known outcomes<br/>CSV file"]:::built
    MP["Column matching<br/>mapping.json<br/>for a college's own format"]:::built
    CL["Clean the data<br/>missing semesters,<br/>impossible values"]:::built
    SPLIT["Split students<br/>80% learn / 20% test"]:::built
    TR["Train + calibrate<br/>about 10 seconds on CPU"]:::built
    CUTS["Choose cutoffs<br/>from the 85% target"]:::built
    TEST["Test once on the 20%<br/>never seen before"]:::built
    GATE{"Release check<br/>85% target met?<br/>beats simple rules?"}
    REJ["Not approved<br/>scores marked<br/>review only"]:::bad
    SAVE["Save model + manifest<br/>+ fingerprint SHA-256<br/>+ report"]:::built
    LIVE["Platform loads model<br/>checks fingerprint<br/>scores students"]:::planned
    NEW["New outcomes recorded<br/>in cases each term"]:::planned

    D1 --> CL
    MP --> CL
    CL --> SPLIT --> TR --> CUTS --> TEST --> GATE
    GATE -- no --> REJ
    GATE -- yes --> SAVE --> LIVE
    LIVE --> NEW -. "retrain each term" .-> D1

    classDef built fill:#d4edda,stroke:#2e7d32,color:#1b1b1b
    classDef planned fill:#fff3cd,stroke:#b8860b,color:#1b1b1b
    classDef bad fill:#f8d7da,stroke:#a71d2a,color:#1b1b1b
```

| Step | Command (in `ml/`) |
|---|---|
| Train everything (Kaggle or laptop) | `python kaggle_train.py` |
| Train on a college's own file | `python -m disha_ml.train --data file.csv --mapping mapping.json` |
| Make a mapping template | `python -m disha_ml.mapping --data file.csv` |
| Score students | `python -m disha_ml.score --model artifacts/cp1 --input students.csv` |

Legacy training data: UCI "Predict Students' Dropout and Academic Success",
4,424 real students from a Portuguese institution, in `ml/data/processed/data.csv`
(and a Spanish UPV file for a time-based check).

**Rolling model (primary):**

| Step | Command (in `ml/`) |
|---|---|
| Convert OULAD into the six tables | `python -m disha_ml.converters.oulad` |
| Train (about 107 s on CPU) | `python -m disha_ml.rolling.train --data data/raw/oulad` |
| Score one day | `python -m disha_ml.rolling.score --tables <dir> --as-of 120` |

Trained on terms 2013B, 2013J and 2014B, tested once on 2014J. OULAD source,
licence and checksum: `ml/data/raw/oulad/SOURCE.md`. The rolling trainer has no
automatic release check yet (**Not yet implemented**).

---

## 9. Review, cases and follow-up

```mermaid
flowchart TD
    A["Alert in review queue<br/>risk %, tier, reasons"]:::built
    R{"Mentor or faculty<br/>reviews"}:::human
    DIS["Dismiss<br/>with a reason"]
    MORE["Ask for more data"]
    APP["Approve<br/>choose a support action<br/>from the campus list"]
    CASE["Case created"]:::built
    ASG["HOD assigns an owner<br/>and a deadline"]:::human
    ACC["Owner accepts"]:::human
    CON["Contact the student"]:::human
    Q{"Reached?"}
    FAIL["Could not reach<br/>-> close with reason"]
    SUP["Support given<br/>tutoring, mentoring,<br/>counselling, fee help"]:::human
    FU["Follow-up recorded<br/>with proof"]:::human
    OUT["Outcome<br/>helped / not helped /<br/>mixed / unknown"]:::human
    CLOSE["Case closed<br/>can be reopened"]

    A --> R
    R --> DIS
    R --> MORE
    R --> APP --> CASE --> ASG --> ACC --> CON --> Q
    Q -- no --> FAIL
    Q -- yes --> SUP --> FU --> OUT --> CLOSE

    classDef built fill:#d4edda,stroke:#2e7d32,color:#1b1b1b
    classDef planned fill:#fff3cd,stroke:#b8860b,color:#1b1b1b
    classDef human fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
```

- Every step is written to an **audit trail** that cannot be edited or deleted.
- Sensitive parts of a task (fee details, counselling notes) are visible only
  to that office; others see a generic label like "finance support".
- If two people edit the same case at once, the second is told to reload, so
  nothing is silently overwritten.

---

## 10. Deadlines, reminders and escalation

A background **worker** runs all the time, separate from the website.

```mermaid
flowchart TB
    ACT["Something happens<br/>case created, assigned,<br/>deadline set"]:::built
    BOX[("Outbox<br/>list of messages<br/>to send")]:::built
    W["Worker<br/>outbox every 10 s"]:::built
    SEND["Send<br/>in-app today;<br/>email, SMS planned"]:::planned
    OK2["Marked sent<br/>only after delivery"]
    RETRY["Failed -> retry later<br/>after 5 tries -> dead-letter"]:::bad
    SCAN["Worker scans every minute<br/>for overdue cases and tasks"]:::built
    ESC["Escalate once<br/>notify HOD / supervisor"]:::built

    ACT --> BOX --> W --> SEND
    SEND -- delivered --> OK2
    SEND -- failed --> RETRY --> BOX
    W --> SCAN --> ESC --> BOX

    classDef planned fill:#fff3cd,stroke:#b8860b,color:#1b1b1b
    classDef bad fill:#f8d7da,stroke:#a71d2a,color:#1b1b1b
    classDef built fill:#d4edda,stroke:#2e7d32,color:#1b1b1b
```

- Messages are saved **together with** the action, so a crash never loses one.
- An overdue case escalates **once** per deadline. If the deadline is changed,
  escalation can happen again for the new deadline.

---

## 11. Security on every request

```mermaid
flowchart TD
    U["User clicks something"]:::human
    L{"Logged in?<br/>valid token"}
    N1["401 - please log in"]:::bad
    M{"Member of<br/>this campus?"}
    N2["404 - not found<br/>nothing revealed"]:::bad
    P{"Role allowed<br/>this action?"}
    N3["403 - not allowed"]:::bad
    F["Fetch data<br/>filtered to this campus<br/>+ database row security"]:::planned
    S["Show only the fields<br/>this role may see"]:::planned

    U --> L
    L -- no --> N1
    L -- yes --> M
    M -- no --> N2
    M -- yes --> P
    P -- no --> N3
    P -- yes --> F --> S

    classDef planned fill:#fff3cd,stroke:#b8860b,color:#1b1b1b
    classDef human fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
    classDef bad fill:#f8d7da,stroke:#a71d2a,color:#1b1b1b
```

- One central permission list says which role can do which action.
- Error messages never reveal IDs, campuses or roles.
- Student data is never sent to outside services (translation, AI) without an
  agreement, and restricted data never at all.

---

## 12. Reports and the learning loop

```mermaid
flowchart LR
    CASES[("Cases and outcomes")]:::planned
    SIGS[("Signals and<br/>model scores")]:::planned
    PULSE[("Wellbeing pulse<br/>answers")]:::planned
    AGG["Count and average<br/>from real rows only"]:::planned
    SUP{"Group smaller<br/>than minimum size?"}
    HIDE["Hidden<br/>marked suppressed"]
    DASH["Dashboards<br/>leadership, HOD, admin"]:::human
    LEARN["Outcomes become<br/>labels for retraining"]:::planned
    MLB["ML model<br/>next version"]:::built

    CASES --> AGG
    SIGS --> AGG
    PULSE --> AGG
    AGG --> SUP
    SUP -- yes --> HIDE
    SUP -- no --> DASH
    CASES --> LEARN --> MLB

    classDef built fill:#d4edda,stroke:#2e7d32,color:#1b1b1b
    classDef planned fill:#fff3cd,stroke:#b8860b,color:#1b1b1b
    classDef human fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
```

- No number on a dashboard is typed by hand; everything is counted from stored data.
- Small groups are hidden so no individual student can be identified.

---

## 13. Extra modules

These sit around the core flow. Each is optional for the first version.

```mermaid
flowchart LR
    CORE(["Core flow<br/>data -> alert -> review -> case -> outcome"])
    AI["AI review brief<br/>summary for the mentor<br/>advice only"]:::planned
    WB["Wellbeing pulse<br/>6 questions weekly"]:::planned
    RW["Points and rewards<br/>for participation"]:::planned
    CO["Counselling desk<br/>call requests, escalation contacts"]:::planned
    DOC["Documents<br/>tamper-proof fingerprints"]:::planned
    I18N["Indian languages<br/>local translation"]:::built
    CLI2["Command-line tool"]:::planned

    CORE --- AI
    CORE --- WB
    WB --- RW
    CORE --- CO
    CORE --- DOC
    CORE --- I18N
    CORE --- CLI2

    classDef planned fill:#fff3cd,stroke:#b8860b,color:#1b1b1b
    classDef built fill:#d4edda,stroke:#2e7d32,color:#1b1b1b
```

| Module | What it does | Safety rule |
|---|---|---|
| AI review brief | Summarises a student's evidence for the mentor | Advice only; never sees fee or counselling data; cannot change anything |
| Wellbeing pulse | Weekly 6-question check-in | Results shown only for groups of 10+; reflections are private |
| Points and rewards | Points for taking part | Points never depend on how a student answers |
| Counselling desk | Students request a call; counsellors escalate emergencies | Only counselling staff see the details |
| Documents | Support plans get a tamper-proof fingerprint | No personal data stored on the blockchain |
| Indian languages | Translates text locally with IndicTrans2 (`POST /api/v1/translate`, off by default). Built in the API | Runs on the campus machine; nothing is sent to an outside translator |

---

## 14. One student, start to finish

```mermaid
sequenceDiagram
    autonumber
    participant C as College admin
    participant D as DISHA
    participant M as ML model
    participant F as Faculty mentor
    participant H as HOD
    participant S as Student

    C->>D: Upload semester 1 results (CSV)
    D->>D: Check and store, send import report
    D->>M: Score all students (cp1)
    M-->>D: Asha: 81% risk, HIGH, reasons
    D->>F: Alert in review queue
    F->>D: Approve, choose "mentor check-in"
    D->>H: New case needs an owner
    H->>D: Assign mentor, deadline in 7 days
    D->>F: You own this case
    F->>S: Meets the student
    F->>D: Record follow-up and support given
    Note over D: If the deadline passes, the worker escalates to the HOD
    F->>D: Outcome: helped
    D->>D: Close case, update dashboards, save as future training data
```

*(Asha is an example name, not a real student.)*

---

## 15. What is built vs planned

| Part | Status | Where |
|---|---|---|
| Rolling risk model: canonical tables, snapshots, features, calibrated model, tiers, reasons, drift, insights payload | ✅ Built and tested; results in `ml/artifacts_rolling/` | `ml/disha_ml/rolling/`, `ml/disha_ml/converters/oulad.py` |
| Legacy semester models (cleaning, features, cutoffs, tiers, reports) on UCI and UPV | ✅ Built and tested (secondary) | `ml/disha_ml/` |
| Training on Kaggle in one command (legacy models) | ✅ Built, run on Kaggle | `ml/kaggle_train.py` |
| Column matching for a college's own file format (legacy models) | ✅ Built (in the ML tool) | `ml/disha_ml/mapping.py` |
| Training datasets | ✅ In repo: UCI, UPV converted; OULAD raw files are git-ignored with a tracked source note | `ml/data/` |
| Design of every module | ✅ Written | `blueprint/` |
| Cases: state machine, `case_events`, tasks, outcomes, campus membership check | ✅ Built | `api/app/modules/cases/` |
| Outbox (retries, dead-letter) and deadline escalation | ✅ Built; only the in-app adapter exists | `api/app/modules/cases/outbox.py`, `worker/jobs/` |
| Database migration for cases, outbox, membership | ✅ Alembic `0001` | `api/migrations/versions/` |
| Translation (local IndicTrans2, flag) | ✅ Built | `api/app/modules/translate/` |
| Meko routes and memory hooks (optional) | ✅ Built | `api/app/modules/meko/`, `meko/`, `ml/disha_ml/meko_hooks.py` |
| Run the rolling scorer from the platform (route or job) | 🟨 Not yet implemented | `api/app/modules/ml/` is a stub |
| Backend ingestion, analytics, roster, wellbeing, identity | 🟨 Stubs (one `GET /` each) | `api/app/modules/` |
| Other worker jobs (anchor confirmation, retention purge, model drift report, Meko weekly outcomes) | 🟨 Log-only or no data source | `worker/jobs/` |
| Web app | 🟨 Started | `web/` |
| CLI, smart contracts, infra | 🟨 Skeletons | `cli/`, `contracts/`, `infra/` |

**Suggested build order:** login and campus setup → data upload and import
check → connect the ML model to stored data → review queue → cases and
deadlines → worker → dashboards → extra modules.
See `blueprint/15-build-sequence.md`.
