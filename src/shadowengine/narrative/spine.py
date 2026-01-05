"""
Narrative Spine - The hidden truth of the story.

Generates the core conflict, resolution, red herrings, and required
revelations that ensure story coherence.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import random


class ConflictType(Enum):
    """Types of central conflicts."""
    MURDER = "murder"
    THEFT = "theft"
    BETRAYAL = "betrayal"
    CONSPIRACY = "conspiracy"
    DISAPPEARANCE = "disappearance"
    BLACKMAIL = "blackmail"
    SABOTAGE = "sabotage"


@dataclass
class RedHerring:
    """A false lead in the story."""

    suspect_id: str             # Who it points to
    description: str            # What makes them suspicious
    plausibility: float         # How believable (0-1)
    reveal_condition: str       # When this red herring is revealed
    debunk_fact: str           # Fact that proves it false

    def to_dict(self) -> dict:
        return {
            "suspect_id": self.suspect_id,
            "description": self.description,
            "plausibility": self.plausibility,
            "reveal_condition": self.reveal_condition,
            "debunk_fact": self.debunk_fact
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RedHerring':
        return cls(**data)


@dataclass
class Revelation:
    """A piece of truth that must be discovered."""

    id: str
    description: str            # What is revealed
    importance: int             # 1-3, how critical to solution
    prerequisites: list[str] = field(default_factory=list)  # Other revelations needed first
    source: str = ""           # How to discover (examine X, talk to Y, etc.)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "importance": self.importance,
            "prerequisites": self.prerequisites,
            "source": self.source
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Revelation':
        return cls(**data)


@dataclass
class TrueResolution:
    """The actual truth of the conflict."""

    culprit_id: str             # Who is responsible
    motive: str                 # Why they did it
    method: str                 # How they did it
    opportunity: str            # When/where they did it
    evidence_chain: list[str]   # Facts that prove it

    def to_dict(self) -> dict:
        return {
            "culprit_id": self.culprit_id,
            "motive": self.motive,
            "method": self.method,
            "opportunity": self.opportunity,
            "evidence_chain": self.evidence_chain
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TrueResolution':
        return cls(**data)


@dataclass
class NarrativeSpine:
    """
    The hidden structure of the story.

    This is generated at game start and drives all story coherence.
    The player never sees this directly, but all generated content
    must be consistent with it.
    """

    # Core conflict
    conflict_type: ConflictType
    conflict_description: str

    # Resolution
    true_resolution: TrueResolution

    # False leads
    red_herrings: list[RedHerring] = field(default_factory=list)

    # Required discoveries
    revelations: list[Revelation] = field(default_factory=list)

    # Twist potential
    twist_probability: float = 0.0
    twist_type: Optional[str] = None
    twist_description: Optional[str] = None

    # Game state
    is_solved: bool = False
    revealed_facts: set[str] = field(default_factory=set)

    def check_revelation(self, revelation_id: str) -> bool:
        """Check if a revelation can be made (prerequisites met)."""
        revelation = self.get_revelation(revelation_id)
        if not revelation:
            return False

        for prereq in revelation.prerequisites:
            if prereq not in self.revealed_facts:
                return False

        return True

    def make_revelation(self, revelation_id: str) -> bool:
        """Mark a revelation as discovered."""
        if self.check_revelation(revelation_id):
            self.revealed_facts.add(revelation_id)
            return True
        return False

    def get_revelation(self, revelation_id: str) -> Optional[Revelation]:
        """Get a revelation by ID."""
        for r in self.revelations:
            if r.id == revelation_id:
                return r
        return None

    def get_available_revelations(self) -> list[Revelation]:
        """Get revelations that can currently be discovered."""
        available = []
        for r in self.revelations:
            if r.id not in self.revealed_facts and self.check_revelation(r.id):
                available.append(r)
        return available

    def check_solution(self, accused_id: str, evidence: set[str]) -> tuple[bool, str]:
        """
        Check if the player has correctly solved the mystery.

        Returns (is_correct, explanation)
        """
        if accused_id != self.true_resolution.culprit_id:
            return False, "That's not the right person."

        # Check if player has enough evidence
        required = set(self.true_resolution.evidence_chain)
        found = required.intersection(evidence)

        if len(found) >= len(required) * 0.7:  # Need 70% of evidence
            self.is_solved = True
            return True, "You've correctly identified the culprit with sufficient evidence!"

        return False, "You might be right, but you don't have enough evidence to prove it."

    def get_progress(self) -> float:
        """Get story progress as percentage of revelations discovered."""
        if not self.revelations:
            return 0.0
        return len(self.revealed_facts) / len(self.revelations)

    def should_trigger_twist(self) -> bool:
        """Check if a twist should be triggered."""
        if self.twist_probability <= 0:
            return False
        if self.get_progress() < 0.6:  # Twists happen late game
            return False
        return random.random() < self.twist_probability

    def to_dict(self) -> dict:
        """Serialize narrative spine."""
        return {
            "conflict_type": self.conflict_type.value,
            "conflict_description": self.conflict_description,
            "true_resolution": self.true_resolution.to_dict(),
            "red_herrings": [rh.to_dict() for rh in self.red_herrings],
            "revelations": [r.to_dict() for r in self.revelations],
            "twist_probability": self.twist_probability,
            "twist_type": self.twist_type,
            "twist_description": self.twist_description,
            "is_solved": self.is_solved,
            "revealed_facts": list(self.revealed_facts)
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'NarrativeSpine':
        """Deserialize narrative spine."""
        spine = cls(
            conflict_type=ConflictType(data["conflict_type"]),
            conflict_description=data["conflict_description"],
            true_resolution=TrueResolution.from_dict(data["true_resolution"]),
            twist_probability=data.get("twist_probability", 0),
            twist_type=data.get("twist_type"),
            twist_description=data.get("twist_description"),
            is_solved=data.get("is_solved", False)
        )
        spine.red_herrings = [RedHerring.from_dict(rh) for rh in data.get("red_herrings", [])]
        spine.revelations = [Revelation.from_dict(r) for r in data.get("revelations", [])]
        spine.revealed_facts = set(data.get("revealed_facts", []))
        return spine


class SpineGenerator:
    """
    Generates narrative spines for new games.
    """

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        if seed is not None:
            random.seed(seed)

    def generate(
        self,
        conflict_type: ConflictType = None,
        characters: list[str] = None,
        twist_chance: float = 0.3
    ) -> NarrativeSpine:
        """
        Generate a new narrative spine.

        Args:
            conflict_type: Type of conflict (random if None)
            characters: List of character IDs to use
            twist_chance: Probability of a twist (0-1)

        Returns:
            A new NarrativeSpine
        """
        characters = characters or []

        # Choose conflict type
        if conflict_type is None:
            conflict_type = random.choice(list(ConflictType))

        # Generate based on conflict type
        if conflict_type == ConflictType.THEFT:
            return self._generate_theft_spine(characters, twist_chance)
        elif conflict_type == ConflictType.MURDER:
            return self._generate_murder_spine(characters, twist_chance)
        else:
            return self._generate_generic_spine(conflict_type, characters, twist_chance)

    def _generate_theft_spine(self, characters: list[str], twist_chance: float) -> NarrativeSpine:
        """Generate a theft-based narrative spine."""
        if len(characters) < 2:
            characters = ["suspect_a", "suspect_b", "victim"]

        culprit = random.choice(characters[:-1]) if len(characters) > 1 else characters[0]

        return NarrativeSpine(
            conflict_type=ConflictType.THEFT,
            conflict_description="Something valuable has been stolen.",
            true_resolution=TrueResolution(
                culprit_id=culprit,
                motive="financial desperation",
                method="took it when no one was looking",
                opportunity="was alone with the item",
                evidence_chain=["had_access", "has_motive", "seen_near_item"]
            ),
            revelations=[
                Revelation(
                    id="had_access",
                    description=f"{culprit} had access to the location",
                    importance=2,
                    source=f"Talk to {culprit} or examine the area"
                ),
                Revelation(
                    id="has_motive",
                    description=f"{culprit} needed money",
                    importance=3,
                    source="Investigate their background"
                ),
                Revelation(
                    id="seen_near_item",
                    description=f"{culprit} was seen near the item",
                    importance=2,
                    prerequisites=["had_access"],
                    source="Ask witnesses"
                )
            ],
            twist_probability=twist_chance
        )

    def _generate_murder_spine(self, characters: list[str], twist_chance: float) -> NarrativeSpine:
        """Generate a murder-based narrative spine."""
        if len(characters) < 2:
            characters = ["suspect_a", "suspect_b", "victim"]

        culprit = random.choice(characters[:-1]) if len(characters) > 1 else characters[0]

        return NarrativeSpine(
            conflict_type=ConflictType.MURDER,
            conflict_description="Someone has been killed.",
            true_resolution=TrueResolution(
                culprit_id=culprit,
                motive="revenge for a past wrong",
                method="poison",
                opportunity="was alone with the victim",
                evidence_chain=["method_known", "had_motive", "had_opportunity", "physical_evidence"]
            ),
            revelations=[
                Revelation(
                    id="method_known",
                    description="The victim was poisoned",
                    importance=2,
                    source="Examine the body or scene"
                ),
                Revelation(
                    id="had_motive",
                    description=f"{culprit} had reason to want revenge",
                    importance=3,
                    source="Investigate their history"
                ),
                Revelation(
                    id="had_opportunity",
                    description=f"{culprit} was alone with the victim",
                    importance=2,
                    prerequisites=["method_known"],
                    source="Ask about the timeline"
                ),
                Revelation(
                    id="physical_evidence",
                    description=f"Evidence linking {culprit} to the poison",
                    importance=3,
                    prerequisites=["method_known", "had_opportunity"],
                    source="Search their belongings"
                )
            ],
            twist_probability=twist_chance,
            twist_type="sympathetic_motive",
            twist_description="The victim had done something terrible"
        )

    def _generate_generic_spine(
        self,
        conflict_type: ConflictType,
        characters: list[str],
        twist_chance: float
    ) -> NarrativeSpine:
        """Generate a generic narrative spine for other conflict types."""
        if len(characters) < 2:
            characters = ["suspect_a", "suspect_b"]

        culprit = random.choice(characters)

        return NarrativeSpine(
            conflict_type=conflict_type,
            conflict_description=f"A case of {conflict_type.value}.",
            true_resolution=TrueResolution(
                culprit_id=culprit,
                motive="personal gain",
                method="deception",
                opportunity="exploited trust",
                evidence_chain=["first_clue", "second_clue", "final_proof"]
            ),
            revelations=[
                Revelation(
                    id="first_clue",
                    description="Initial evidence pointing to wrongdoing",
                    importance=1,
                    source="Examine the scene"
                ),
                Revelation(
                    id="second_clue",
                    description="Evidence connecting to the culprit",
                    importance=2,
                    prerequisites=["first_clue"],
                    source="Follow up on first clue"
                ),
                Revelation(
                    id="final_proof",
                    description="Definitive proof of guilt",
                    importance=3,
                    prerequisites=["second_clue"],
                    source="Confront with evidence"
                )
            ],
            twist_probability=twist_chance
        )
