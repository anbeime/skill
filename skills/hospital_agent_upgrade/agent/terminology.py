"""Optional terminology matching helpers.

The project can use ``rapidfuzz`` when it is available, and falls back to a
small pure-Python scorer otherwise.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Iterable, List, Tuple

try:  # pragma: no cover - optional dependency
    from rapidfuzz import fuzz as _rapidfuzz_fuzz
except Exception:  # pragma: no cover - optional dependency
    _rapidfuzz_fuzz = None


def normalize_term(value: Any) -> str:
    text = str(value or "").lower()
    return re.sub(r"[\s\-_/，,。.;；:：、（）()\[\]【】]+", "", text)


def alnum_signature(value: Any) -> str:
    return "".join(ch for ch in normalize_term(value) if ch.isalnum())


def best_match(value: Any, choices: Iterable[Any], *, score_cutoff: float = 0.84) -> str:
    query = str(value or "").strip()
    if not query:
        return ""

    normalized_choices: List[Tuple[str, str, str]] = []
    for choice in choices:
        text = str(choice or "").strip()
        if not text:
            continue
        normalized_choices.append((text, normalize_term(text), alnum_signature(text)))

    if not normalized_choices:
        return ""

    query_norm = normalize_term(query)
    query_sig = alnum_signature(query)
    best_choice = ""
    best_score = 0.0
    for choice_text, choice_norm, choice_sig in normalized_choices:
        score = _score_pair(query_norm, choice_norm, query_sig, choice_sig)
        if score > best_score:
            best_choice = choice_text
            best_score = score
    return best_choice if best_score >= score_cutoff else ""


def _score_pair(query_norm: str, choice_norm: str, query_sig: str, choice_sig: str) -> float:
    if not query_norm or not choice_norm:
        return 0.0
    if query_norm == choice_norm:
        return 1.0
    if query_norm in choice_norm or choice_norm in query_norm:
        return 0.99
    if query_sig and choice_sig:
        if query_sig == choice_sig:
            return 0.98
        if query_sig in choice_sig or choice_sig in query_sig:
            return 0.95

    if _rapidfuzz_fuzz is not None:
        score = max(
            _rapidfuzz_fuzz.ratio(query_norm, choice_norm),
            _rapidfuzz_fuzz.partial_ratio(query_norm, choice_norm),
        )
        if query_sig and choice_sig:
            score = max(
                score,
                _rapidfuzz_fuzz.ratio(query_sig, choice_sig),
                _rapidfuzz_fuzz.partial_ratio(query_sig, choice_sig),
            )
        return score / 100.0

    score = SequenceMatcher(None, query_norm, choice_norm).ratio()
    if query_sig and choice_sig:
        score = max(score, SequenceMatcher(None, query_sig, choice_sig).ratio())
    return score
