"""
Matching what the player typed against things in the scene.

Whole words beat fragments: "alley" is the Dark Alley, never O'Malley's
Bar (where it merely hides inside a word). A fragment only counts when it
starts a word, so "bart" still finds the bartender.
"""

import re
from typing import Optional, Sequence

# Words that never name anything: articles, possessives, little
# directions ("go down the alley" is about the alley)
FILLER = {
    "the", "a", "an", "at", "to", "with", "on", "in", "my", "your", "his",
    "her", "their", "up", "down", "into", "inside", "through", "via", "out",
    "outside", "of", "onto", "toward", "towards",
}


def label_words(text: str) -> list[str]:
    """Lowercase words with filler dropped; apostrophes don't split words."""
    return [
        w for w in re.findall(r"[a-z0-9]+", text.lower().replace("'", "").replace("’", ""))
        if w not in FILLER
    ]


def match_rank(query: str, label: str) -> Optional[float]:
    """
    How well the player's words name a label, lower is better:
    0 exactly, 1 by whole words (one set inside the other), 1.5 sharing
    at least half the query's words, 2 by word beginnings ("bart"),
    None not at all.
    """
    q, lab = label_words(query), label_words(label)
    if not q or not lab:
        return None
    q_set, lab_set = set(q), set(lab)
    if q == lab:
        return 0
    if q_set <= lab_set or lab_set <= q_set:
        return 1
    shared = q_set & lab_set
    if shared and len(shared) * 2 >= len(q_set):
        # More shared words is a better match, still worse than a subset
        return 1.5 - min(len(shared), 4) * 0.1
    if all(any(word.startswith(part) for word in lab) for part in q):
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
