import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kagaz_ml import synthetic  # noqa: E402


@pytest.fixture(scope="session")
def sample_csv(tmp_path_factory) -> Path:
    return synthetic.write(tmp_path_factory.mktemp("data") / "sample.csv", n=1500, seed=0)
