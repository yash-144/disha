# DISHA ML Subsystem

Isolated machine learning pipelines for predicting student dropout and academic success.

## Requirements
* Strict temporal separation: No data leakage.
* Auditable feature contracts.
* Human-in-the-loop: ML predictions attach as auxiliary evidence cards; they never trigger cases automatically.

## Data Directories
* `data/raw/` — Immutable source datasets (UCI Student Dropout dataset).
* `data/processed/` — Normalized and validated datasets ready for training.
