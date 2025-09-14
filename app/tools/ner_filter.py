"""
spaCy-based NER filter and de-identification utilities.

Features:
- Language support: English (en_core_web_sm) and Turkish (tr_core_news_sm)
- Whitelist/blacklist entity filtering
- De-identification strategies (placeholder, full, partial)
- Provider-style interface for easy swapping
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import hashlib
import os

import spacy
import re


# Default configuration aligned to medical admissions domain
# We want to keep domain-relevant entities, but still mask sensitive PII in text
DEFAULT_WHITELIST = {"PERSON", "ORG", "LOCATION", "DATE", "TIME", "EVENT"}
DEFAULT_BLACKLIST = {"PERSON", "PER", "GPE", "LOC", "LOCATION", "EMAIL", "PHONE", "CARD", "MONEY"}

# Domain keywords and id patterns we care about
DOMAIN_KEYWORDS = {
    # English
    "patient", "hospital", "admission", "discharge", "doctor", "provider", "diagnosis", "disease",
    "subject_id", "hadm_id", "provider_id", "transfer", "careunit", "insurance", "age", "gender",
    "admittime", "dischtime",
    # Turkish
    "hasta", "hastane", "yatış", "çıkış", "doktor", "personel", "tanı", "hastalık",
}


def _normalize_label(label: str) -> str:
    mapping = {
        "GPE": "LOCATION",
        "LOC": "LOCATION",
        "NORP": "GROUP",
        # WikiNER / multilingual labels
        "PER": "PERSON",
        "ORG": "ORG",
        "MISC": "MISC",
    }
    return mapping.get(label, label)


def _mask_value(label: str, value: str, strategy: str = "placeholder") -> str:
    if strategy == "placeholder":
        h = hashlib.sha1(value.encode()).hexdigest()[:6]
        return f"[{label}_{h}]"
    if strategy == "full":
        return f"[{label}]"
    if strategy == "partial":
        if "@" in value:
            name, domain = value.split("@", 1)
            return f"{name[:1]}***@{domain}"
        return value[:2] + "***"
    return f"[{label}]"


@dataclass
class NERResult:
    sanitized_text: str
    desired_entities: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.desired_entities is None:
            self.desired_entities = []


class SpaCyNERProvider:
    """Thin wrapper around spaCy to extract entities for TR/EN."""

    def __init__(
        self,
        language_code: str = "tr",
        whitelist: Optional[set] = None,
        blacklist: Optional[set] = None,
        deid_strategy: str = "placeholder",
    ) -> None:
        self.language_code = language_code
        self.whitelist = whitelist or DEFAULT_WHITELIST
        self.blacklist = blacklist or DEFAULT_BLACKLIST
        self.deid_strategy = deid_strategy
        self._nlp = self._load_model(language_code)

    def _load_model(self, lang: str):
        preferred = []
        if lang.startswith("tr"):
            preferred = ["tr_core_news_sm", "xx_ent_wiki_sm", "en_core_web_sm"]
        else:
            preferred = ["en_core_web_sm", "xx_ent_wiki_sm"]

        last_error: Optional[Exception] = None
        for name in preferred:
            try:
                return spacy.load(name)
            except Exception as e:  # model not installed or incompatible
                last_error = e
                continue

        # If none loaded, raise helpful guidance
        raise RuntimeError(
            "No compatible spaCy model is installed. Try one of:\n"
            "  python -m spacy download xx_ent_wiki_sm\n"
            "  python -m spacy download en_core_web_sm\n"
            "For Turkish-specific pipeline, if available for your spaCy version:\n"
            "  python -m spacy download tr_core_news_sm\n"
            f"Last error: {last_error}"
        )

    def extract_entities(self, text: str) -> List[Dict[str, object]]:
        doc = self._nlp(text)
        return [
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            }
            for ent in doc.ents
        ]

    def filter_and_deidentify(self, text: str) -> NERResult:
        ents = self.extract_entities(text)
        desired: List[Dict[str, str]] = []
        sanitized_text = text
        offset_shift = 0

        # First pass: mask entity-based blacklist using offsets from original text
        for ent in ents:
            label = _normalize_label(str(ent["label"]))
            value = str(ent["text"])  # original span text

            if label in self.blacklist:
                masked = _mask_value(label, value, strategy=self.deid_strategy)
                start = int(ent["start"]) + offset_shift
                end = int(ent["end"]) + offset_shift
                sanitized_text = sanitized_text[:start] + masked + sanitized_text[end:]
                offset_shift += len(masked) - (end - start)

            if label in self.whitelist:
                desired.append({"label": label, "value": value})

        # Second pass: regex-based PII masking (emails, phones) on the already-sanitized text
        sanitized_text = _regex_mask_pii(sanitized_text, strategy=self.deid_strategy)

        # Third pass: domain keyword/ID extraction
        desired.extend(_extract_domain_terms_and_ids(text))

        return NERResult(sanitized_text=sanitized_text, desired_entities=desired)


def _regex_mask_pii(text: str, strategy: str = "placeholder") -> str:
    # Basic email
    email_re = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.IGNORECASE)
    # Basic international phone (very permissive, matches +90 ... and similar)
    phone_re = re.compile(r"(?:(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3}[\s-]?\d{2,4}[\s-]?\d{2,4})")

    def _mask_email(m: re.Match) -> str:
        return _mask_value("EMAIL", m.group(0), strategy=strategy)

    def _mask_phone(m: re.Match) -> str:
        # Avoid masking parts of already masked tokens
        g = m.group(0)
        if g.startswith("[") and g.endswith("]"):
            return g
        return _mask_value("PHONE", g, strategy=strategy)

    masked = email_re.sub(_mask_email, text)
    masked = phone_re.sub(_mask_phone, masked)
    return masked


def _extract_domain_terms_and_ids(text: str) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    lowered = text.lower()

    # Keyword hits (de-duplicated)
    hits = set(k for k in DOMAIN_KEYWORDS if k in lowered)
    for k in sorted(hits):
        results.append({"label": "DOMAIN_TERM", "value": k})

    # Common ID patterns: subject_id/hadm_id/provider_id followed by number or alphanum
    id_re = re.compile(r"\b(subject_id|hadm_id|provider_id)\b\s*[:=#-]?\s*([A-Za-z0-9_-]{1,64})", re.IGNORECASE)
    for m in id_re.finditer(text):
        key = m.group(1)
        val = m.group(2)
        results.append({"label": key.upper(), "value": val})

    # Date fields by explicit column names without NER (admittime/dischtime) capturing ISO-like
    dt_re = re.compile(r"\b(admittime|dischtime)\b\s*[:=#-]?\s*([0-9T:\-\s/]{5,25})", re.IGNORECASE)
    for m in dt_re.finditer(text):
        key = m.group(1).upper()
        val = m.group(2).strip()
        results.append({"label": key, "value": val})

    return results


def build_system_context_block(desired_entities: List[Dict[str, str]]) -> str:
    if not desired_entities:
        return "None"

    # Group entities
    domain_terms = sorted({e["value"] for e in desired_entities if e.get("label") == "DOMAIN_TERM"})
    id_labels = {"SUBJECT_ID", "HADM_ID", "PROVIDER_ID", "ADMITTIME", "DISCHTIME"}
    ids: List[str] = []
    others: List[str] = []

    for e in desired_entities:
        label = e.get("label", "")
        value = e.get("value", "")
        if label == "DOMAIN_TERM":
            continue
        if label in id_labels:
            ids.append(f"- {label}: {value}")
        else:
            others.append(f"- {label}: {value}")

    blocks: List[str] = []
    if domain_terms:
        blocks.append("Domain terms: " + ", ".join(domain_terms))
    if ids:
        blocks.append("Identifiers/Times:\n" + "\n".join(ids))
    if others:
        blocks.append("Other entities:\n" + "\n".join(others))

    return "\n\n".join(blocks)
