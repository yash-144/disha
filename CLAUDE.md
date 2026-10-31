# DISHA agent notes

## Meko memory (datapack `disha`)

DISHA uses Meko as shared memory for humans and coding agents. Server config is in `.mcp.json` (needs `MEKO_API_KEY` in your environment; never write the token into files).

- **Before an ML experiment** (training, threshold or feature changes): recall from the `disha` datapack, e.g. "label=dropout model=hgb cutoffs fairness", and read what was tried before. The same lookup from a shell: `python -m disha_meko recall "<query>"`.
- **After an experiment**: store the learning as a memory (dataset, config, key metrics, what to try or avoid next). The legacy `python -m disha_ml.train` already records run summaries and threshold decisions, and `python -m disha_ml.rolling.score` writes tier-change memories (tagged `journey:<hash>`); neither knows the *why*, so add that and any surprises yourself.
- Record non-obvious design decisions as decision traces.
- **Never** send student names, emails, roll numbers or raw IDs, or raw marks. Aggregates and hashed IDs only. Do not upload repo docs to Meko (the docs sync was removed); only campus-owned knowledge goes through `POST /api/v1/meko/knowledge`.
- If Meko is down or the key is missing, carry on; all DISHA code treats Meko as optional. Check with `make meko-doctor`.

Details: `docs/architecture/MEKO_INTEGRATION.md`.

## ML and specs

The primary model is the rolling risk model (`ml/disha_ml/rolling/`); the semester `cp0`/`cp1`/`cp2` models are legacy. Its output contract is `docs/architecture/INSIGHTS_SPEC.md` (source of truth; link, do not copy). Never call 94.5% or 97.6% "accuracy": they are alert precision (see `ml/README.md` §18). Docs index and changelog: `blueprint/README.md`.
