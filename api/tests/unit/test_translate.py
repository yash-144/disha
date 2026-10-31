"""IndicTrans2 endpoint: request validation, feature flag, language mapping. The model is mocked."""
import contextlib
import sys
import types

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.modules.translate import service
from app.modules.translate.languages import to_flores
from .conftest import headers

URL = "/api/v1/translate"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "DISHA_TRANSLATE_ENABLED", True)
    calls = []
    monkeypatch.setattr(service, "translate", lambda texts, s, t: calls.append((texts, s, t)) or [f"[{t}] {x}" for x in texts])
    with TestClient(app) as c:
        c.calls = calls
        yield c


def post(client, **body):
    return client.post(URL, headers=headers(), json=body)


def test_bcp47_codes_map_to_flores():
    assert [to_flores(c) for c in ("hi-IN", "bn", "ta-IN", "en-US", "hin_Deva")] == [
        "hin_Deva", "ben_Beng", "tam_Taml", "eng_Latn", "hin_Deva"]
    with pytest.raises(ValueError):
        to_flores("xx-YY")


def test_translate_single_and_batch(client):
    r = post(client, text="Please meet your mentor", source_lang="en", target_lang="hi-IN")
    assert r.status_code == 200 and r.json() == {"source_lang": "eng_Latn", "target_lang": "hin_Deva",
                                                 "translations": ["[hin_Deva] Please meet your mentor"]}
    r = post(client, texts=["a", "b"], source_lang="ben_Beng", target_lang="eng_Latn")
    assert r.json()["translations"] == ["[eng_Latn] a", "[eng_Latn] b"]
    assert client.calls[-1] == (["a", "b"], "ben_Beng", "eng_Latn")


@pytest.mark.parametrize("body", [
    {"source_lang": "en", "target_lang": "hi"},                                        # no text
    {"text": "a", "texts": ["b"], "source_lang": "en", "target_lang": "hi"},           # both
    {"text": "a", "source_lang": "en", "target_lang": "en"},                           # same language
    {"text": "a", "source_lang": "hi", "target_lang": "ta"},                           # indic -> indic
    {"text": "a", "source_lang": "en", "target_lang": "klingon"},                      # unknown language
    {"text": "", "source_lang": "en", "target_lang": "hi"},                            # empty
    {"texts": [], "source_lang": "en", "target_lang": "hi"},
    {"texts": ["ok", "  "], "source_lang": "en", "target_lang": "hi"},                 # blank item
    {"text": "x" * 2001, "source_lang": "en", "target_lang": "hi"},                    # too long
    {"texts": ["a"] * 33, "source_lang": "en", "target_lang": "hi"},                   # too many
])
def test_invalid_requests_are_422(client, body):
    assert post(client, **body).status_code == 422
    assert client.calls == []


def test_requires_auth_and_feature_flag(client, monkeypatch):
    assert client.post(URL, json={"text": "a", "source_lang": "en", "target_lang": "hi"}).status_code == 401
    monkeypatch.setattr(settings, "DISHA_TRANSLATE_ENABLED", False)
    assert post(client, text="a", source_lang="en", target_lang="hi").status_code == 503


def test_missing_optional_extra_is_503(client, monkeypatch):
    def boom(*a):
        raise RuntimeError("Translation extra missing")
    monkeypatch.setattr(service, "translate", boom)
    assert post(client, text="a", source_lang="en", target_lang="hi").status_code == 503


def test_model_pipeline_is_lazy_and_picks_direction(monkeypatch):
    """Fake torch/tokenizer/model/processor: checks pre/post-processing order and per-direction lazy loading."""
    log = []

    class Tok:
        def __call__(self, batch, **kw):
            log.append(("tok", batch))
            return {"input_ids": batch}

        def batch_decode(self, ids, **kw):
            return [f"dec:{i}" for i in ids]

    class Model:
        def generate(self, **kw):
            return types.SimpleNamespace(detach=lambda: types.SimpleNamespace(cpu=lambda: types.SimpleNamespace(
                tolist=lambda: kw["input_ids"])))

    class Proc:
        def preprocess_batch(self, texts, src_lang, tgt_lang):
            return [f"{src_lang}>{tgt_lang} {t}" for t in texts]

        def postprocess_batch(self, out, lang):
            return [f"{lang}:{o}" for o in out]

    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace(no_grad=contextlib.nullcontext))
    monkeypatch.setattr(service, "_loaded", {})
    monkeypatch.setattr(service, "_processor", Proc())
    loads = []
    monkeypatch.setattr(service, "_load", lambda kind: loads.append(kind) or (Tok(), Model()))
    assert loads == []  # nothing loaded at import time
    out = service.translate(["hello"], "eng_Latn", "hin_Deva")
    assert out == ["hin_Deva:dec:eng_Latn>hin_Deva hello"] and loads == ["en-indic"]
    service.translate(["namaste"], "hin_Deva", "eng_Latn")
    assert loads == ["en-indic", "indic-en"]
