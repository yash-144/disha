"""BCP-47 -> FLORES-200 codes for the 22 scheduled Indian languages IndicTrans2 covers (plus English)."""
FLORES = {
    "en": "eng_Latn", "hi": "hin_Deva", "bn": "ben_Beng", "ta": "tam_Taml", "te": "tel_Telu", "mr": "mar_Deva",
    "gu": "guj_Gujr", "kn": "kan_Knda", "ml": "mal_Mlym", "pa": "pan_Guru", "or": "ory_Orya", "as": "asm_Beng",
    "ur": "urd_Arab", "ne": "npi_Deva", "sa": "san_Deva", "sd": "snd_Arab", "ks": "kas_Arab", "kok": "gom_Deva",
    "mai": "mai_Deva", "doi": "doi_Deva", "brx": "brx_Deva", "mni": "mni_Mtei", "sat": "sat_Olck",
}
SUPPORTED = set(FLORES.values())


def to_flores(code: str) -> str:
    """'hi-IN' / 'hi' / 'hin_Deva' -> 'hin_Deva'. ValueError if unsupported."""
    if code in SUPPORTED:
        return code
    flores = FLORES.get(code.replace("_", "-").split("-")[0].lower())
    if not flores:
        raise ValueError(f"Unsupported language '{code}'")
    return flores
