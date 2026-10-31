"""Model pipelines. Both run on CPU in seconds on ~4,400 rows."""
from __future__ import annotations

from typing import List

from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

MODELS = ("hgb", "logreg")


def _onehot() -> OneHotEncoder:
    return OneHotEncoder(handle_unknown="ignore", sparse_output=False)


def build_estimator(model: str, numeric: List[str], categorical: List[str], seed: int) -> Pipeline:
    if model == "hgb":
        # Gradient-boosted trees handle missing values (NaN) natively.
        pre = ColumnTransformer([
            ("num", "passthrough", numeric),
            ("cat", _onehot(), categorical),
        ])
        clf = HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_iter=300,
            max_leaf_nodes=15,
            min_samples_leaf=30,
            l2_regularization=1.0,
            early_stopping=True,
            validation_fraction=0.15,
            random_state=seed,
        )
    elif model == "logreg":
        pre = ColumnTransformer([
            ("num", Pipeline([
                ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                ("scale", StandardScaler()),
            ]), numeric),
            ("cat", _onehot(), categorical),
        ])
        clf = LogisticRegression(max_iter=2000, C=1.0)
    else:
        raise ValueError(f"model must be one of {MODELS}")
    return Pipeline([("pre", pre), ("clf", clf)])


def calibrated(estimator: Pipeline, method: str, folds: int, seed: int) -> CalibratedClassifierCV:
    """Wrap a model so its probabilities match observed rates (see training guide)."""
    return CalibratedClassifierCV(
        estimator=estimator,
        method=method,
        cv=StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed),
    )
