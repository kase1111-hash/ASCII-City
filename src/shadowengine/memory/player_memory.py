"""
Player Memory - The protagonist's perception and discoveries.

This is what the player character knows, suspects, and has done.
It drives available dialogue options, narration tone, and endings.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class MoralShade(Enum):
    """The five moral shades."""
    PRAGMATIC = "pragmatic"
    CORRUPT = "corrupt"
    COMPASSIONATE = "compassionate"
    RUTHLESS = "ruthless"
    IDEALISTIC = "idealistic"


@dataclass
class Discovery:
    """A fact or clue the player has discovered."""

    fact_id: str                # Unique identifier
    description: str            # What was discovered
    location: str               # Where it was found
    timestamp: int              # When it was found
    source: str                 # How it was discovered (examined, told, etc.)
    is_evidence: bool = False   # Is this usable as evidence?
    related_to: list[str] = field(default_factory=list)  # Related character/item IDs

    def to_dict(self) -> dict:
        return {
            "fact_id": self.fact_id,
            "description": self.description,
            "location": self.location,
            "timestamp": self.timestamp,
            "source": self.source,
            "is_evidence": self.is_evidence,
            "related_to": self.related_to
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Discovery':
        return cls(**data)


@dataclass
class MoralAction:
    """A morally significant action taken by the player."""

    action_type: str            # threatened, helped, lied, etc.
    description: str            # What happened
    timestamp: int
    target: Optional[str]       # Who was affected
    shade_effects: dict = field(default_factory=dict)  # shade -> change amount
    weight: float = 1.0         # Significance of action

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "description": self.description,
            "timestamp": self.timestamp,
            "target": self.target,
            "shade_effects": self.shade_effects,
            "weight": self.weight
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MoralAction':
        return cls(**data)


class PlayerMemory:
    """
    The player character's memory and moral state.

    Tracks discoveries, suspicions, relationships, and moral choices.
    """

    def __init__(self):
        self.discoveries: dict[str, Discovery] = {}  # fact_id -> Discovery
        self.suspicions: dict[str, float] = {}  # character_id -> confidence
        self.relationships: dict[str, int] = {}  # character_id -> trust level
        self.moral_actions: list[MoralAction] = []
        self.shade_scores: dict[str, float] = {
            MoralShade.PRAGMATIC.value: 0.2,
            MoralShade.CORRUPT.value: 0.2,
            MoralShade.COMPASSIONATE.value: 0.2,
            MoralShade.RUTHLESS.value: 0.2,
            MoralShade.IDEALISTIC.value: 0.2
        }
        self.notes: list[str] = []  # Player's mental notes
        self.visited_locations: set[str] = set()
        self.talked_to: set[str] = set()  # NPCs player has spoken with

    def add_discovery(
        self,
        fact_id: str,
        description: str,
        location: str,
        timestamp: int,
        source: str,
        is_evidence: bool = False,
        related_to: list[str] = None
    ) -> Discovery:
        """Record a new discovery."""
        discovery = Discovery(
            fact_id=fact_id,
            description=description,
            location=location,
            timestamp=timestamp,
            source=source,
            is_evidence=is_evidence,
            related_to=related_to or []
        )
        self.discoveries[fact_id] = discovery
        return discovery

    def has_discovered(self, fact_id: str) -> bool:
        """Check if player has discovered a fact."""
        return fact_id in self.discoveries

    def get_discovery(self, fact_id: str) -> Optional[Discovery]:
        """Get a specific discovery."""
        return self.discoveries.get(fact_id)

    def get_evidence(self) -> list[Discovery]:
        """Get all discoveries that are evidence."""
        return [d for d in self.discoveries.values() if d.is_evidence]

    def add_suspicion(self, character_id: str, confidence: float) -> None:
        """Add or update suspicion about a character."""
        current = self.suspicions.get(character_id, 0)
        self.suspicions[character_id] = min(1.0, max(0.0, current + confidence))

    def get_suspicion(self, character_id: str) -> float:
        """Get suspicion level for a character."""
        return self.suspicions.get(character_id, 0.0)

    def update_relationship(self, character_id: str, change: int) -> None:
        """Update relationship with a character."""
        current = self.relationships.get(character_id, 0)
        self.relationships[character_id] = current + change

    def get_relationship(self, character_id: str) -> int:
        """Get relationship level with a character."""
        return self.relationships.get(character_id, 0)

    def record_moral_action(
        self,
        action_type: str,
        description: str,
        timestamp: int,
        target: str = None,
        shade_effects: dict = None,
        weight: float = 1.0
    ) -> MoralAction:
        """Record a morally significant action."""
        action = MoralAction(
            action_type=action_type,
            description=description,
            timestamp=timestamp,
            target=target,
            shade_effects=shade_effects or {},
            weight=weight
        )
        self.moral_actions.append(action)

        # Update shade scores
        for shade, change in action.shade_effects.items():
            if shade in self.shade_scores:
                self.shade_scores[shade] += change * weight

        # Normalize scores
        self._normalize_shades()

        return action

    def _normalize_shades(self) -> None:
        """Normalize shade scores to sum to 1.0."""
        total = sum(self.shade_scores.values())
        if total > 0:
            for shade in self.shade_scores:
                self.shade_scores[shade] /= total

    def get_dominant_shade(self) -> MoralShade:
        """Get the player's dominant moral shade."""
        max_shade = max(self.shade_scores, key=self.shade_scores.get)
        return MoralShade(max_shade)

    def get_secondary_shade(self) -> MoralShade:
        """Get the player's secondary moral shade."""
        sorted_shades = sorted(
            self.shade_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return MoralShade(sorted_shades[1][0])

    def add_note(self, note: str) -> None:
        """Add a mental note."""
        self.notes.append(note)

    def visit_location(self, location_id: str) -> None:
        """Mark a location as visited."""
        self.visited_locations.add(location_id)

    def has_visited(self, location_id: str) -> bool:
        """Check if player has visited a location."""
        return location_id in self.visited_locations

    def mark_talked_to(self, character_id: str) -> None:
        """Mark that player has talked to an NPC."""
        self.talked_to.add(character_id)

    def has_talked_to(self, character_id: str) -> bool:
        """Check if player has talked to an NPC."""
        return character_id in self.talked_to

    def to_dict(self) -> dict:
        """Serialize player memory."""
        return {
            "discoveries": {k: v.to_dict() for k, v in self.discoveries.items()},
            "suspicions": self.suspicions,
            "relationships": self.relationships,
            "moral_actions": [a.to_dict() for a in self.moral_actions],
            "shade_scores": self.shade_scores,
            "notes": self.notes,
            "visited_locations": list(self.visited_locations),
            "talked_to": list(self.talked_to)
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PlayerMemory':
        """Deserialize player memory."""
        memory = cls()
        memory.discoveries = {
            k: Discovery.from_dict(v)
            for k, v in data.get("discoveries", {}).items()
        }
        memory.suspicions = data.get("suspicions", {})
        memory.relationships = data.get("relationships", {})
        memory.moral_actions = [
            MoralAction.from_dict(a)
            for a in data.get("moral_actions", [])
        ]
        memory.shade_scores = data.get("shade_scores", memory.shade_scores)
        memory.notes = data.get("notes", [])
        memory.visited_locations = set(data.get("visited_locations", []))
        memory.talked_to = set(data.get("talked_to", []))
        return memory
