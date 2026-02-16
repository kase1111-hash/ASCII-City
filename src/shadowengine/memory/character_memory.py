"""
Character Memory - What each NPC believes happened.

NPCs have incomplete, biased, or false beliefs about events.
Their memory drives their behavior and dialogue.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class BeliefConfidence(Enum):
    """How confident the character is in this belief."""
    CERTAIN = "certain"         # They saw it themselves
    CONFIDENT = "confident"     # Reliable source told them
    UNCERTAIN = "uncertain"     # Heard rumor or partial info
    SUSPICIOUS = "suspicious"   # They suspect but aren't sure


@dataclass
class Belief:
    """A single belief held by a character."""

    subject: str                # What/who the belief is about
    content: str                # What they believe
    confidence: BeliefConfidence
    source: str                 # How they know (witnessed, told, inferred)
    timestamp: int              # When they formed this belief
    is_true: bool = True        # Does this match world memory? (hidden)
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize belief."""
        return {
            "subject": self.subject,
            "content": self.content,
            "confidence": self.confidence.value,
            "source": self.source,
            "timestamp": self.timestamp,
            "is_true": self.is_true,
            "details": self.details
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Belief':
        """Deserialize belief."""
        data = dict(data)  # Don't mutate the input dictionary
        data["confidence"] = BeliefConfidence(data["confidence"])
        return cls(**data)


@dataclass
class PlayerInteraction:
    """Record of an interaction with the player."""

    timestamp: int
    interaction_type: str       # talked, threatened, helped, etc.
    topic: Optional[str]        # What was discussed
    player_tone: str            # friendly, aggressive, neutral
    outcome: str                # cooperated, refused, lied, etc.
    trust_change: int           # How much trust changed
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "interaction_type": self.interaction_type,
            "topic": self.topic,
            "player_tone": self.player_tone,
            "outcome": self.outcome,
            "trust_change": self.trust_change,
            "details": self.details
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PlayerInteraction':
        return cls(**data)


class CharacterMemory:
    """
    Memory system for a single NPC.

    Tracks their beliefs, knowledge, suspicions, and history
    with the player.
    """

    def __init__(self, character_id: str):
        self.character_id = character_id
        self.beliefs: list[Belief] = []
        self.knowledge: set[str] = set()  # Facts they know for certain
        self.suspicions: dict[str, float] = {}  # target -> confidence (0-1)
        self.player_interactions: list[PlayerInteraction] = []

    def add_belief(
        self,
        subject: str,
        content: str,
        confidence: BeliefConfidence,
        source: str,
        timestamp: int,
        is_true: bool = True,
        details: dict = None
    ) -> Belief:
        """Add a new belief."""
        belief = Belief(
            subject=subject,
            content=content,
            confidence=confidence,
            source=source,
            timestamp=timestamp,
            is_true=is_true,
            details=details or {}
        )
        self.beliefs.append(belief)
        return belief

    def add_knowledge(self, fact: str) -> None:
        """Add a known fact."""
        self.knowledge.add(fact)

    def knows(self, fact: str) -> bool:
        """Check if character knows a fact."""
        return fact in self.knowledge

    def add_suspicion(self, target: str, confidence: float) -> None:
        """Add or update suspicion about someone."""
        current = self.suspicions.get(target, 0)
        self.suspicions[target] = min(1.0, max(0.0, current + confidence))

    def get_suspicion(self, target: str) -> float:
        """Get suspicion level for a target."""
        return self.suspicions.get(target, 0.0)

    def record_player_interaction(
        self,
        timestamp: int,
        interaction_type: str,
        player_tone: str,
        outcome: str,
        trust_change: int,
        topic: str = None,
        details: dict = None
    ) -> PlayerInteraction:
        """Record an interaction with the player."""
        interaction = PlayerInteraction(
            timestamp=timestamp,
            interaction_type=interaction_type,
            topic=topic,
            player_tone=player_tone,
            outcome=outcome,
            trust_change=trust_change,
            details=details or {}
        )
        self.player_interactions.append(interaction)
        return interaction

    def get_beliefs_about(self, subject: str) -> list[Belief]:
        """Get all beliefs about a subject."""
        return [b for b in self.beliefs if b.subject == subject]

    def get_recent_interactions(self, count: int = 5) -> list[PlayerInteraction]:
        """Get most recent player interactions."""
        return self.player_interactions[-count:]

    def total_trust_change(self) -> int:
        """Calculate total trust change from all interactions."""
        return sum(i.trust_change for i in self.player_interactions)

    def to_dict(self) -> dict:
        """Serialize character memory."""
        return {
            "character_id": self.character_id,
            "beliefs": [b.to_dict() for b in self.beliefs],
            "knowledge": list(self.knowledge),
            "suspicions": self.suspicions,
            "player_interactions": [i.to_dict() for i in self.player_interactions]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CharacterMemory':
        """Deserialize character memory."""
        memory = cls(data["character_id"])
        memory.beliefs = [Belief.from_dict(b) for b in data.get("beliefs", [])]
        memory.knowledge = set(data.get("knowledge", []))
        memory.suspicions = data.get("suspicions", {})
        memory.player_interactions = [
            PlayerInteraction.from_dict(i)
            for i in data.get("player_interactions", [])
        ]
        return memory
