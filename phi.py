import re
from typing import List, Tuple

try:
    import spacy
except Exception:
    spacy = None

_NLP = None
LabelSpan = Tuple[int, int]


PHI_PATTERNS = [
    # Email addresses
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    # US phone numbers with optional country code and separators
    re.compile(r"\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"),
    # Social Security Number
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    # MRN/account/policy-like identifiers
    re.compile(
        r"\b(?:MRN|Medical Record|Acct|Account|Policy|Member|Subscriber|Claim|Case|Patient ID)[:\s#-]*[A-Z0-9-]{5,}\b",
        flags=re.IGNORECASE,
    ),
    # Long standalone numeric identifiers (conservative catch-all)
    re.compile(r"\b\d{7,}\b"),
    # Month-name dates (e.g., Jan 2, 1980)
    re.compile(
        r"\b(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+\d{1,2},?\s+\d{2,4}\b",
        flags=re.IGNORECASE,
    ),
    # DOB labels with free-form date text
    re.compile(r"\b(?:DOB|Date of Birth)[:\s-]+[A-Za-z0-9,/\- ]+\b", flags=re.IGNORECASE),
    # Street addresses with number + road type
    re.compile(
        r"\b\d{1,6}\s+[A-Za-z0-9.\- ]+\s(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court|Way|Pkwy|Parkway|Pl|Place)\b\.?",
        flags=re.IGNORECASE,
    ),
    # US ZIP (5-digit or ZIP+4)
    re.compile(r"\b\d{5}(?:-\d{4})?\b"),
    # Name labels commonly found in transcripts/notes
    re.compile(r"\b(?:Patient Name|Pt Name|Name)[:\s-]+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b"),
    # Conversational name disclosures (e.g., "my name is John Doe")
    re.compile(
        r"\b(?:my name is|i am|i'm|this is)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b",
        flags=re.IGNORECASE,
    ),
    # Spoken/segmented numeric identifiers after number-like labels
    re.compile(
        r"\b(?:phone|mobile|contact|member|policy|account|mrn|patient id)?\s*number\s*(?:is|:)?\s*(?:\d[\s,-]*){6,}\b",
        flags=re.IGNORECASE,
    ),
]


def _get_nlp():
    global _NLP
    if spacy is None:
        return None
    if _NLP is None:
        try:
            _NLP = spacy.load("en_core_web_sm")
        except Exception:
            _NLP = None
    return _NLP


def _ner_spans(text: str) -> List[LabelSpan]:
    nlp = _get_nlp()
    if nlp is None:
        return []

    doc = nlp(text)
    spans: List[LabelSpan] = []
    for ent in doc.ents:
        if ent.label_ in {"PERSON", "GPE", "LOC", "FAC", "DOB"}:
            spans.append((ent.start_char, ent.end_char))
    return spans


def _redact_spans(text: str, spans: List[LabelSpan]) -> str:
    if not spans:
        return text
    merged: List[LabelSpan] = []
    for start, end in sorted(spans):
        if start < 0 or end <= start or end > len(text):
            continue
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))

    out = []
    cursor = 0
    for start, end in merged:
        out.append(text[cursor:start])
        out.append("[REDACTED]")
        cursor = end
    out.append(text[cursor:])
    return "".join(out)


def redact_phi(text: str) -> str:
    # Lightweight NER first (names/locations/dates), regex second for IDs/contact fields.
    redacted = _redact_spans(text, _ner_spans(text))
    for pattern in PHI_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted
