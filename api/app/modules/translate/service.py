"""Local IndicTrans2 (AI4Bharat) translation on CPU. Models load lazily on first use; no caching of results.

Needs the optional extra: pip install -e "api[translate]". Student text never leaves the machine.
"""
import threading
from typing import Dict, List, Tuple

MODELS = {  # direction -> Hugging Face repo (gated: accept the terms, set HF_TOKEN)
    "en-indic": "ai4bharat/indictrans2-en-indic-dist-200M",
    "indic-en": "ai4bharat/indictrans2-indic-en-dist-200M",
}
# Pinned commits: these repos ship their own model code (trust_remote_code), so never pull an unreviewed update.
REVISIONS = {
    "en-indic": "2cfd0a20057756d756bf3e53528f492afc52f91a",
    "indic-en": "d66a2122ad6d28184f3dc3797b652bd80ae3f65f",
}
MAX_LENGTH = 256
_loaded: Dict[str, Tuple[object, object]] = {}
_processor = None
_lock = threading.Lock()  # one model load / generate at a time (CPU bound anyway)


def direction(src: str, tgt: str) -> str:
    if src == tgt:
        raise ValueError("source_lang and target_lang must differ")
    if src == "eng_Latn":
        return "en-indic"
    if tgt == "eng_Latn":
        return "indic-en"
    raise ValueError("One side must be English: IndicTrans2 distilled models do not translate Indic to Indic")


def _load(kind: str):
    global _processor
    try:
        import torch  # noqa: F401
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        try:
            from IndicTransToolkit.processor import IndicProcessor
        except ImportError:
            from IndicTransToolkit import IndicProcessor
    except ImportError as exc:
        raise RuntimeError('Translation extra missing: pip install -e "api[translate]"') from exc
    if _processor is None:
        _processor = IndicProcessor(inference=True)
    if kind not in _loaded:
        repo = MODELS[kind]
        rev = REVISIONS[kind]
        tok = AutoTokenizer.from_pretrained(repo, revision=rev, trust_remote_code=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(repo, revision=rev, trust_remote_code=True).to("cpu").eval()
        _loaded[kind] = (tok, model)
    return _loaded[kind]


def translate(texts: List[str], src: str, tgt: str) -> List[str]:
    """Translate FLORES-coded `texts` (blocking; call from a thread)."""
    import torch
    with _lock:
        tok, model = _load(direction(src, tgt))
        batch = _processor.preprocess_batch(texts, src_lang=src, tgt_lang=tgt)
        inputs = tok(batch, truncation=True, padding="longest", return_tensors="pt", return_attention_mask=True)
        # use_cache=False: the models' remote code breaks with the new transformers KV-cache objects (4.5x).
        with torch.no_grad():
            out = model.generate(**inputs, use_cache=False, min_length=0, max_length=MAX_LENGTH, num_beams=5,
                                 num_return_sequences=1)
        decoded = tok.batch_decode(out.detach().cpu().tolist(), skip_special_tokens=True,
                                   clean_up_tokenization_spaces=True)
        return _processor.postprocess_batch(decoded, lang=tgt)
