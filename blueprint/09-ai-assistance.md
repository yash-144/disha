# 09 · AI Assistance

Optional module. Large-language-model output is advisory text shown to staff.
Source of current behaviour: `app/ai/`, `docs/decisions/ADR-006-ai-orchestration-safeguards.md`.

## 1. Features

| Feature | Endpoint | Output |
|---|---|---|
| Review brief | `POST /ai/review-brief` | Structured brief separated into tiers: observed data, rule signal, ML estimate, AI suggestion, human decision |
| Evidence summary | `POST /ai/summarize-evidence` | Short summary of a student's recent observations |
| Intervention suggestions | `POST /ai/suggest-interventions` | Ranked candidates from the campus catalogue |
| Status | `GET /ai/status` | Enabled flag, provider, model, governance rules |

**Current implementation facts:**
- Active provider is `DeterministicMockProvider` unless `AI_PROVIDER=openai` is
  exported to the process environment; values in `.env` are ignored because
  `providers.py` uses `os.getenv` (audit A7).
- `OpenAIProvider` imports `openai` inside `try`; the package is not in
  `requirements.txt`, so it falls back to the mock silently (audit T4).
- `GEMINI_API_KEY` exists in settings; no Gemini provider exists.
- When the campus catalogue is empty, the service uses a built-in fallback
  catalogue.
- `validate_and_filter_candidate_interventions` drops suggestions not in the
  catalogue.
- `prompt.py` sanitises untrusted text and wraps it in labelled delimiters.
- Each call writes `ai_orchestration_logs` (provider, model, tokens, latency,
  status).

## 2. Requirements

| ID | Requirement |
|---|---|
| AI-01 | Provider chosen from the typed settings object; unknown or misconfigured provider → startup error when `AI_ENABLED=true` |
| AI-02 | Provider SDKs are declared dependencies |
| AI-03 | A mock provider exists only in test code, never as a production fallback |
| AI-04 | Provider failure or timeout returns a deterministic rule-based explanation with `ai_status = unavailable`; it does not pretend to be AI output |
| AI-05 | Inputs exclude restricted data (finance, counselling, reflections) and direct identifiers (names, external refs); students are referenced by an opaque per-request alias (INV-05) |
| AI-06 | Outputs are validated against a JSON schema; invalid output → `ai_status = invalid_output` and the deterministic fallback |
| AI-07 | Suggested interventions must exist and be active in the campus catalogue; no built-in fallback catalogue |
| AI-08 | Output contains no diagnostic or disciplinary terms; a deny-list check runs on output (INV-02, INV-03) |
| AI-09 | AI has no tools and no write path; a human action is required to use any suggestion (INV-01) |
| AI-10 | Every call is logged with provider, model, token counts, latency, status, and a hash of the prompt (not the prompt) |
| AI-11 | Per-user and per-campus rate limits and a monthly token budget |
| AI-12 | A data-processing agreement with the provider exists before any student-derived text is sent (audit F1 principle) |
| AI-13 | Prompt templates are versioned files; the version is logged |

## 3. Prompt structure

```
SYSTEM: role, constraints (advisory only, no diagnosis, no discipline,
        choose only from CATALOG), output JSON schema
CATALOG: [{key, label, domain}]
EVIDENCE (untrusted, delimited):
  <<observations>> metric, value, date …
  <<rule_signal>>  result, triggered rules
  <<ml_estimate>>  probability, threshold, top features (if any)
TASK: produce brief per schema
```
