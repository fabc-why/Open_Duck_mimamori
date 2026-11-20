"""Reusable fuzzy matching for spoken text."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from collections.abc import Iterable


_PUNCTUATION = re.compile(r"[\s、。！？!?]+")


@dataclass(frozen=True, slots=True)
class FuzzyMatch:
    """The closest candidate and its similarity score."""

    candidate: str
    score: float


def normalize_for_fuzzy_matching(text: str) -> str:
    """Normalize Unicode, case, whitespace, and common spoken punctuation."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return _PUNCTUATION.sub("", normalized)


def find_fuzzy_match(
    text: str,
    candidates: Iterable[str],
    *,
    threshold: float = 0.8,
) -> FuzzyMatch | None:
    """Return the best candidate when its similarity reaches the threshold."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0")

    normalized_text = normalize_for_fuzzy_matching(text)
    if not normalized_text:
        return None

    best: FuzzyMatch | None = None
    for candidate in candidates:
        normalized_candidate = normalize_for_fuzzy_matching(candidate)
        if not normalized_candidate:
            continue
        score = SequenceMatcher(
            None,
            normalized_text,
            normalized_candidate,
        ).ratio()
        if best is None or score > best.score:
            best = FuzzyMatch(candidate=candidate, score=score)

    if best is None or best.score < threshold:
        return None
    return best
