"""Deterministic evidence rules used to keep compliance verdicts grounded.

Pure-Python (no framework imports) so the rules are easy to unit-test:

* explicit-omission detection  - the submission itself says evidence is missing/pending
* numeric deviation detection  - a stated value violates a min/max bound in the requirement
* offset -> chunk lookup       - maps a verbatim quote back to page/section metadata
"""
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

TOPIC_TERMS = {
    "inspection": ("inspection", "x-ray", "radiography", "fpi", "penetrant", "nde", "non-destructive"),
    "material": ("material", "heat treatment", "chemical composition", "batch record"),
    "testing": ("testing", "test procedure", "thermal cycling", "hydrostatic", "leak rate", "proof pressure"),
    "design": ("design calculation", "finite element", "fea", "stress analysis", "safety margin", "burst pressure"),
}
OMISSION_SIGNALS = (
    "omitted", "missing", "not included", "pending", "not provided", "unavailable", "awaiting",
    "not available", "not yet", "tbd", "to be provided", "to be submitted", "not supplied", "not attached",
)


def find_explicit_omission(requirement_context: str, submitted_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (topic, verbatim_sentence) when a requirement's topic is explicitly omitted."""
    context = (requirement_context or "").casefold()
    topic = next((t for t, terms in TOPIC_TERMS.items() if any(term in context for term in terms)), None)
    if not topic:
        return None, None
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", submitted_text or ""):
        low = sentence.casefold()
        if any(term in low for term in TOPIC_TERMS[topic]) and any(sig in low for sig in OMISSION_SIGNALS):
            return topic, sentence.strip()
    return None, None


def find_omission_in_documents(
    requirement_context: str, documents: Sequence[Tuple[str, str]]
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Search each (name, text) submitted document. Returns (topic, sentence, document_name)."""
    for name, text in documents:
        topic, sentence = find_explicit_omission(requirement_context, text)
        if sentence:
            return topic, sentence, name
    return None, None, None


# --------------------------------------------------------------------- numerics
_MIN_WORDS = r"at\s+least|minimum(?:\s+of)?|no\s+less\s+than|not\s+less\s+than|exceed(?:ing|s)?|greater\s+than|more\s+than|above|over|>=|≥"
_MAX_WORDS = r"at\s+most|maximum(?:\s+of)?|no\s+more\s+than|not\s+more\s+than|not\s+exceed|within|less\s+than|below|under|up\s+to|no\s+later\s+than|<=|≤"
_UNITS = (
    r"business\s+days?|working\s+days?|calendar\s+days?|days?|hours?|hrs?|weeks?|months?|years?|minutes?|mins?"
    r"|percent|%|x|×|bar|mpa|kpa|psi|°c|°f|mm|cm"
)
_BOUND_RE = re.compile(
    rf"(?P<cmp>{_MIN_WORDS}|{_MAX_WORDS})\s*(?:of\s+)?(?:[A-Za-z\-]+\s+){{0,2}}?(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>{_UNITS})(?![A-Za-z])",
    re.IGNORECASE,
)
_VALUE_RE = re.compile(rf"(?<![\w.])(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>{_UNITS})(?![A-Za-z])", re.IGNORECASE)


def _norm_unit(unit: str) -> str:
    u = re.sub(r"\s+", " ", unit.lower().strip())
    if re.search(r"\bdays?$", u):
        return "day"
    if u in ("%", "percent"):
        return "%"
    if u in ("x", "×"):
        return "x"
    if u in ("hr", "hrs", "hour", "hours"):
        return "hour"
    return u.rstrip("s")


def _is_min(cmp_text: str) -> bool:
    return re.fullmatch(_MIN_WORDS, re.sub(r"\s+", " ", cmp_text.strip()), re.IGNORECASE) is not None


def detect_numeric_deviation(requirement_text: str, evidence_text: str) -> List[str]:
    """Flag when every comparable value in the evidence violates a numeric bound.

    Conservative by design: values equal to the bound (a restatement of the
    requirement) are ignored, and nothing is flagged if any comparable value
    satisfies the bound or if there is no comparable value at all.
    """
    findings: List[str] = []
    if not requirement_text or not evidence_text:
        return findings
    for m in _BOUND_RE.finditer(requirement_text):
        bound = float(m.group("num"))
        unit = _norm_unit(m.group("unit"))
        is_min = _is_min(m.group("cmp"))
        candidates = [
            float(v.group("num"))
            for v in _VALUE_RE.finditer(evidence_text)
            if _norm_unit(v.group("unit")) == unit and float(v.group("num")) != bound
        ]
        if not candidates:
            continue
        violating = [c for c in candidates if (c < bound if is_min else c > bound)]
        if len(violating) == len(candidates):
            direction = "at least" if is_min else "at most"
            label = {"day": "days", "hour": "hours"}.get(unit, unit)
            sep = "" if unit in ("%", "x") else " "
            vals = ", ".join(f"{c:g}{sep}{label}" for c in violating)
            findings.append(
                f"Requirement demands {direction} {bound:g}{sep}{label}; submission states {vals}."
            )
    return findings


# ----------------------------------------------------------------- chunk lookup
def locate_chunk(chunks: Sequence[Dict[str, Any]], document_name: str, offset: int) -> Optional[Dict[str, Any]]:
    """Return the chunk dict of `document_name` whose [start_char, end_char] span contains offset."""
    best = None
    for chunk in chunks:
        if chunk.get("document_name") != document_name:
            continue
        if chunk.get("start_char", 0) <= offset <= chunk.get("end_char", 0):
            if best is None or (chunk["end_char"] - chunk["start_char"]) < (best["end_char"] - best["start_char"]):
                best = chunk
    return best
