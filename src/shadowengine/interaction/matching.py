"""
Matching what the player typed against things in the scene.

Whole words beat fragments: "alley" is the Dark Alley, never O'Malley's
Bar (where it merely hides inside a word). A fragment only counts when it
starts a word, so "bart" still finds the bartender, and only where the
caller allows fragments at all (never for movement).
"""

import re
from typing import Optional, Sequence

# Words that never name anything: articles and possessives
FILLER = {
    "the", "a", "an", "at", "to", "with", "on", "in", "my", "your", "his",
    "her", "their", "of", "this", "that",
}

# Little directions: "go down the alley" is about the alley — unless a
# label uses the word ("Stairs Down" vs "Stairs Up"), when it decides
DIRECTION_WORDS = {
    "up", "down", "out", "outside", "inside", "into", "through", "via",
    "onto", "toward", "towards",
}

# Words that carry how you go, not where: "head over to the bar again"
MOVEMENT_FILLER = {
    "over", "across", "around", "round", "straight", "right", "now",
    "again", "quickly", "quick", "then", "on", "there", "along", "ahead",
    "home", "immediately", "fast",
}

# Rank thresholds callers can pass as max_rank
WHOLE_WORDS = 1.0
FRAGMENTS = 2.0


def label_words(text: str, variants: bool = False) -> list[str]:
    """
    Lowercase words with filler dropped; apostrophes don't split words
    ("O'Malley's" is "omalleys"). With variants, a name also answers to
    its other everyday spellings: "omalley", "malleys", "malley".
    """
    lowered = text.lower().replace("\u2019", "'")
    words = re.findall(r"[a-z0-9]+", lowered.replace("'", ""))
    if variants:
        for token in re.findall(r"[a-z0-9']+", lowered):
            forms = {token}
            if token.endswith("'s"):
                forms.add(token[:-2])
            for form in list(forms):
                if re.match(r"^[od]'", form):
                    forms.add(form[2:])
            words += [f.replace("'", "") for f in forms]
    seen = []
    for w in words:
        if w not in FILLER and w not in seen:
            seen.append(w)
    return seen


def match_rank(query: str, label: str) -> Optional[float]:
    """
    How well the player's words name a label, lower is better:
    0 exactly; 0.9 every word (directions included) is in the label;
    1 by whole words once little directions are set aside; 2 by word
    beginnings ("bart"); None not at all.
    """
    q_all = label_words(query)
    lab = label_words(label)
    if not q_all or not lab:
        return None
    if q_all == lab:
        return 0
    lab_set = set(label_words(label, variants=True))
    if set(q_all) <= lab_set:
        return 0.9
    q = [w for w in q_all if w not in DIRECTION_WORDS]
    if not q:
        return None
    q_set = set(q)
    lab_core = set(lab) - DIRECTION_WORDS
    if q_set <= lab_set or (lab_core and lab_core <= q_set):
        return WHOLE_WORDS
    if all(any(word.startswith(part) for word in lab) for part in q):
        return FRAGMENTS
    return None


def best_match(
    query: str, labels: Sequence[str], max_rank: float = FRAGMENTS,
) -> Optional[int]:
    """Index of the label the query names best (first wins a tie), or None."""
    # A "Back to ..." exit only wins a tie when the player said "back"
    said_back = "back" in label_words(query)
    best = None
    for index, label in enumerate(labels):
        rank = match_rank(query, label)
        if rank is None or rank > max_rank:
            continue
        is_back = label.lower().startswith("back") and not said_back
        key = (rank, is_back)
        if best is None or key < best[0]:
            best = (key, index)
    return best[1] if best else None
