"""
Matching what the player typed against things in the scene.

Whole words beat fragments: "alley" is the Dark Alley, not O'Malley's Bar
(where it merely hides inside a word). Substring matching is still the
last resort, so "bart" finds the bartender.
"""

import re
from typing import Optional, Sequence

# Words that never name anything
_FILLER = {"the", "a", "an", "at", "to", "with", "on", "in"}


def label_words(text: str) -> list[str]:
    """Lowercase words with filler dropped; apostrophes don't split words."""
    return [
        w for w in re.findall(r"[a-z0-9]+", text.lower().replace("'", "").replace("’", ""))
        if w not in _FILLER
    ]


def match_rank(query: str, label: str) -> Optional[int]:
    """
    How well the player's words name a label: 0 exactly, 1 by whole
    words, 2 by a fragment inside a word, None not at all.
    """
    q, lab = label_words(query), label_words(label)
    if not q or not lab:
        return None
    if q == lab:
        return 0
    if set(q) <= set(lab) or set(lab) <= set(q):
        return 1
    q_text, label_text = " ".join(q), " ".join(lab)
    if q_text in label_text or label_text in q_text:
        return 2
    return None


def best_match(query: str, labels: Sequence[str]) -> Optional[int]:
    """Index of the label the query names best (first wins a tie), or None."""
    best = None
    for index, label in enumerate(labels):
        rank = match_rank(query, label)
        if rank is not None and (best is None or rank < best[0]):
            best = (rank, index)
    return best[1] if best else None
