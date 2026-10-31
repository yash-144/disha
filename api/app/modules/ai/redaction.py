"""PII redaction applied to every string before it can reach an AI provider (AI-05).

Known identifiers (the student's name, email, roll number, the counsellor's name...) are replaced by opaque
aliases; generic patterns (emails, phone numbers, long digit runs, URLs) are removed whatever they are.
`assert_clean` is a last gate: if a known identifier is still present the call is blocked.
"""
import re
from typing import Dict, List, Tuple

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<![\w])(?:\+?\d[\d\s\-().]{7,}\d)(?![\w])")
LONG_DIGITS_RE = re.compile(r"\b\d{6,}\b")
# Roll-number / enrolment-id shapes such as 21CS1045, BT2021-114, STU-001
ID_LIKE_RE = re.compile(
    r"\b(?=[A-Z0-9\-/]*\d)(?=[A-Z0-9\-/]*[A-Z])(?:[A-Z0-9]{5,}|[A-Z0-9]{2,}(?:[-/][A-Z0-9]+)+)\b"
)
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


class Redactor:
    def __init__(self, known: Dict[str, str]):
        """`known` maps an identifier (full name, email, roll number...) to its alias."""
        pairs: List[Tuple[str, str]] = []
        for term, alias in known.items():
            term = (term or "").strip()
            if len(term) < 2:
                continue
            pairs.append((term, alias))
            if " " in term and "@" not in term:  # each name part on its own as well
                pairs.extend((part, alias) for part in term.split() if len(part) >= 3)
        pairs.sort(key=lambda p: len(p[0]), reverse=True)  # longest first
        self._pairs = pairs
        self._compiled = [(re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)", re.IGNORECASE), a) for t, a in pairs]
        self.count = 0

    def _sub(self, pattern, repl, text: str) -> str:
        text, n = pattern.subn(repl, text)
        self.count += n
        return text

    def redact(self, text: str) -> str:
        if not text:
            return ""
        text = _CONTROL_RE.sub(" ", text)
        text = self._sub(EMAIL_RE, "[email removed]", text)
        for pattern, alias in self._compiled:
            text = self._sub(pattern, alias, text)
        text = self._sub(URL_RE, "[link removed]", text)
        text = self._sub(PHONE_RE, "[number removed]", text)
        text = self._sub(LONG_DIGITS_RE, "[number removed]", text)
        text = self._sub(ID_LIKE_RE, "[id removed]", text)
        return text

    def leaked_terms(self, text: str) -> List[str]:
        """Known identifiers still present in `text` (empty list means clean)."""
        return [t for (t, _a), (p, _b) in zip(self._pairs, self._compiled) if p.search(text)]

    def assert_clean(self, text: str) -> None:
        if self.leaked_terms(text) or EMAIL_RE.search(text):
            raise ValueError("identifier survived redaction")


def sanitize_untrusted(text: str, max_chars: int = 1500) -> str:
    """Neutralise prompt-injection scaffolding in untrusted text: delimiters, role markers, control chars."""
    text = _CONTROL_RE.sub(" ", text or "")
    text = text.replace("<<", "«").replace(">>", "»").replace("```", "'''")
    text = re.sub(r"(?im)^\s*(system|assistant|user|human)\s*:", r"\1 -", text)
    return text[:max_chars]

