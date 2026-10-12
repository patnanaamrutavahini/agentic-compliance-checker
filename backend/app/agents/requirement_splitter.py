"""Split compound requirement sentences into atomic, independently checkable requirements.

Pure Python (no framework imports) so it can be unit-tested in isolation.

Example
-------
"The submitted report must contain design calculations, material specifications,
inspection requirements, and testing procedures."
-> 4 requirements, each of the form "The submitted report must contain <item>."

The splitter is deliberately conservative: it only splits an obvious
"<subject> must <contain|include|...> A, B[, and C]" list of short items. Anything else is returned unchanged, so it is safe to apply to
requirements that are already atomic (idempotent) and to LLM output.
"""
import re
from typing import List

_LEAD_VERBS = (
    "contain|include|provide|document|specify|define|describe|present|demonstrate|"
    "address|have|state|list|identify|cover"
)
_MODALS = r"must|shall|should|will|is\s+required\s+to|are\s+required\s+to|needs?\s+to"

_COMPOUND_RE = re.compile(
    rf"^(?P<prefix>.*?\b(?:{_MODALS})\s+(?:also\s+)?(?:{_LEAD_VERBS})\s+)(?P<items>.+?)[.;:]?\s*$",
    re.IGNORECASE | re.DOTALL,
)
_ITEM_BLOCKERS = re.compile(
    r"\b(?:must|shall|should|which|that|when|where|if|unless|because|while)\b", re.IGNORECASE
)
# An item that starts like this elaborates the previous item; it is not a requirement of its own.
_ELABORATION = re.compile(r"^(?:including|includes|such\s+as|e\.g\.?|for\s+example|especially|particularly)\b", re.IGNORECASE)
MAX_ITEM_WORDS = 12          # items in a comma-separated list
MAX_PAIR_ITEM_WORDS = 5     # items in a bare "A and B" pair (stricter: "and" is often idiomatic)
# Fixed pairs that are ONE thing, not two requirements.
_IDIOMS = {
    "terms and conditions", "rules and regulations", "health and safety", "research and development",
    "roles and responsibilities", "policies and procedures", "checks and balances", "terms and condition",
    "operation and maintenance", "operations and maintenance", "quality assurance and control",
}


def _clean_items(parts: List[str]) -> List[str]:
    return [re.sub(r"^(?:and|or)\s+", "", p.strip(), flags=re.IGNORECASE).strip() for p in parts]


def split_compound_requirement(text: str) -> List[str]:
    """Return atomic requirement sentences, or [text] when it is not an obvious list."""
    clean = re.sub(r"\s+", " ", (text or "").strip())
    match = _COMPOUND_RE.match(clean)
    if not match:
        return [text.strip()] if text and text.strip() else []

    prefix = match.group("prefix").strip() + " "
    body = match.group("items")
    items = _clean_items(re.split(r"[;,]", body))
    limit = MAX_ITEM_WORDS

    if len(items) == 1:
        # bare pair: "design calculations and material specifications"
        if body.strip().lower() in _IDIOMS:
            return [clean]
        pair = re.split(r"\s+and\s+", items[0], flags=re.IGNORECASE)
        if len(pair) != 2:
            return [clean]
        items, limit = [p.strip() for p in pair], MAX_PAIR_ITEM_WORDS
    elif len(items) >= 2 and " and " in items[-1].lower() and not re.match(r"(?i)^and\s", body.split(",")[-1].strip()):
        # list without an Oxford comma: "A, B and C"
        tail = re.split(r"\s+and\s+", items[-1], flags=re.IGNORECASE)
        if len(tail) == 2:
            items = items[:-1] + [t.strip() for t in tail]

    if len(items) < 2 or any(not i for i in items):
        return [clean]
    if any(_ELABORATION.match(i) for i in items):
        return [clean]
    if any(len(i.split()) > limit or _ITEM_BLOCKERS.search(i) for i in items):
        return [clean]
    return [f"{prefix}{item}." for item in items]


def infer_category(text: str) -> str:
    """Cheap keyword category used by the offline engine and for split requirements."""
    low = (text or "").lower()
    if any(k in low for k in ("material", "dimension", "tolerance", "tensile", "temperature")):
        return "Material & Physical Specs"
    if any(k in low for k in ("test", "procedure", "inspection", "verification", "audit")):
        return "Verification & Quality Assurance"
    if any(k in low for k in ("retention", "security", "encryption", "privacy", "gdpr", "consent")):
        return "Governance & Data Protection"
    if any(k in low for k in ("calculation", "design", "stress", "simulation")):
        return "Design Calculations"
    return "Functional Requirement"
