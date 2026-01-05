"""
Twist System - Narrative surprises and story reversals.

Provides:
- Twist types and definitions
- Twist triggering conditions
- Twist revelation mechanics
- Story impact of twists
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum, auto
import random


class TwistType(Enum):
    """Types of narrative twists."""
    # Character twists
    HIDDEN_IDENTITY = "hidden_identity"      # Character isn't who they seem
    SECRET_ALLY = "secret_ally"              # Enemy is actually helping
    BETRAYAL = "betrayal"                    # Ally is actually working against
    REDEMPTION = "redemption"                # Villain has sympathetic side

    # Plot twists
    WRONG_CRIME = "wrong_crime"              # The crime isn't what it appeared
    MULTIPLE_CULPRITS = "multiple_culprits"  # More than one person responsible
    NO_CRIME = "no_crime"                    # What seemed criminal wasn't
    DEEPER_CONSPIRACY = "deeper_conspiracy"  # Crime is part of something bigger

    # Evidence twists
    PLANTED_EVIDENCE = "planted_evidence"    # Key evidence was fabricated
    MISINTERPRETED = "misinterpreted"        # Evidence means something else
    MISSING_PIECE = "missing_piece"          # Critical evidence was hidden

    # Personal twists
    PLAYER_CONNECTION = "player_connection"  # Player character has hidden stake
    PAST_RETURNS = "past_returns"            # Old case/event becomes relevant
    TIME_PRESSURE = "time_pressure"          # Stakes suddenly escalate


@dataclass
class TwistCondition:
    """Condition that must be met for a twist to trigger."""
    type: str  # "progress", "decision", "time", "discovery", "random"
    value: any
    description: str = ""

    def check(self, game_state: dict) -> bool:
        """Check if condition is met."""
        if self.type == "progress":
            return game_state.get("progress", 0) >= self.value
        elif self.type == "decision":
            return self.value in game_state.get("decisions", [])
        elif self.type == "time":
            return game_state.get("time_elapsed", 0) >= self.value
        elif self.type == "discovery":
            return self.value in game_state.get("discoveries", [])
        elif self.type == "random":
            return random.random() < self.value
        return False

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "value": self.value,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TwistCondition":
        return cls(**data)


@dataclass
class Twist:
    """A narrative twist that can be triggered."""
    id: str
    twist_type: TwistType
    name: str
    description: str

    # When it triggers
    trigger_conditions: list[TwistCondition] = field(default_factory=list)
    require_all_conditions: bool = True  # If False, any condition can trigger

    # What it reveals
    revelation_text: str = ""
    affected_characters: list[str] = field(default_factory=list)
    changes_culprit: bool = False
    new_culprit_id: Optional[str] = None

    # Effects
    tension_change: float = 0.2
    reveals_facts: list[str] = field(default_factory=list)
    hides_facts: list[str] = field(default_factory=list)
    unlocks_locations: list[str] = field(default_factory=list)
    unlocks_dialogues: list[str] = field(default_factory=list)

    # State
    triggered: bool = False
    revealed: bool = False

    def check_trigger(self, game_state: dict) -> bool:
        """Check if twist should trigger."""
        if self.triggered:
            return False

        if not self.trigger_conditions:
            return False

        if self.require_all_conditions:
            return all(c.check(game_state) for c in self.trigger_conditions)
        else:
            return any(c.check(game_state) for c in self.trigger_conditions)

    def trigger(self) -> None:
        """Mark twist as triggered."""
        self.triggered = True

    def reveal(self) -> str:
        """Reveal the twist and return revelation text."""
        self.revealed = True
        return self.revelation_text

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "twist_type": self.twist_type.value,
            "name": self.name,
            "description": self.description,
            "trigger_conditions": [c.to_dict() for c in self.trigger_conditions],
            "require_all_conditions": self.require_all_conditions,
            "revelation_text": self.revelation_text,
            "affected_characters": self.affected_characters,
            "changes_culprit": self.changes_culprit,
            "new_culprit_id": self.new_culprit_id,
            "tension_change": self.tension_change,
            "reveals_facts": self.reveals_facts,
            "hides_facts": self.hides_facts,
            "unlocks_locations": self.unlocks_locations,
            "unlocks_dialogues": self.unlocks_dialogues,
            "triggered": self.triggered,
            "revealed": self.revealed
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Twist":
        twist = cls(
            id=data["id"],
            twist_type=TwistType(data["twist_type"]),
            name=data["name"],
            description=data["description"],
            require_all_conditions=data.get("require_all_conditions", True),
            revelation_text=data.get("revelation_text", ""),
            affected_characters=data.get("affected_characters", []),
            changes_culprit=data.get("changes_culprit", False),
            new_culprit_id=data.get("new_culprit_id"),
            tension_change=data.get("tension_change", 0.2),
            reveals_facts=data.get("reveals_facts", []),
            hides_facts=data.get("hides_facts", []),
            unlocks_locations=data.get("unlocks_locations", []),
            unlocks_dialogues=data.get("unlocks_dialogues", []),
            triggered=data.get("triggered", False),
            revealed=data.get("revealed", False)
        )
        twist.trigger_conditions = [
            TwistCondition.from_dict(c)
            for c in data.get("trigger_conditions", [])
        ]
        return twist


class TwistManager:
    """
    Manages narrative twists for a game session.

    Handles twist triggering, revelation, and story impact.
    """

    def __init__(self):
        self.twists: list[Twist] = []
        self._on_trigger: list[Callable[[Twist], None]] = []
        self._on_reveal: list[Callable[[Twist], None]] = []

    def add_twist(self, twist: Twist) -> None:
        """Add a potential twist to the story."""
        self.twists.append(twist)

    def remove_twist(self, twist_id: str) -> bool:
        """Remove a twist by ID."""
        for i, twist in enumerate(self.twists):
            if twist.id == twist_id:
                self.twists.pop(i)
                return True
        return False

    def get_twist(self, twist_id: str) -> Optional[Twist]:
        """Get a twist by ID."""
        for twist in self.twists:
            if twist.id == twist_id:
                return twist
        return None

    def check_triggers(self, game_state: dict) -> list[Twist]:
        """
        Check all twists for trigger conditions.

        Returns list of newly triggered twists.
        """
        newly_triggered = []

        for twist in self.twists:
            if twist.check_trigger(game_state):
                twist.trigger()
                newly_triggered.append(twist)

                for callback in self._on_trigger:
                    callback(twist)

        return newly_triggered

    def reveal_twist(self, twist_id: str) -> Optional[str]:
        """
        Reveal a triggered twist.

        Returns revelation text or None if twist doesn't exist.
        """
        twist = self.get_twist(twist_id)
        if twist and twist.triggered and not twist.revealed:
            text = twist.reveal()

            for callback in self._on_reveal:
                callback(twist)

            return text
        return None

    def get_pending_revelations(self) -> list[Twist]:
        """Get twists that are triggered but not revealed."""
        return [t for t in self.twists if t.triggered and not t.revealed]

    def get_triggered_twists(self) -> list[Twist]:
        """Get all triggered twists."""
        return [t for t in self.twists if t.triggered]

    def get_revealed_twists(self) -> list[Twist]:
        """Get all revealed twists."""
        return [t for t in self.twists if t.revealed]

    def on_trigger(self, callback: Callable[[Twist], None]) -> None:
        """Register callback for when twists trigger."""
        self._on_trigger.append(callback)

    def on_reveal(self, callback: Callable[[Twist], None]) -> None:
        """Register callback for when twists are revealed."""
        self._on_reveal.append(callback)

    def get_story_impact(self) -> dict:
        """Get the cumulative impact of all revealed twists."""
        impact = {
            "tension_change": 0.0,
            "revealed_facts": [],
            "hidden_facts": [],
            "unlocked_locations": [],
            "unlocked_dialogues": [],
            "culprit_changed": False,
            "current_culprit": None
        }

        for twist in self.get_revealed_twists():
            impact["tension_change"] += twist.tension_change
            impact["revealed_facts"].extend(twist.reveals_facts)
            impact["hidden_facts"].extend(twist.hides_facts)
            impact["unlocked_locations"].extend(twist.unlocks_locations)
            impact["unlocked_dialogues"].extend(twist.unlocks_dialogues)

            if twist.changes_culprit:
                impact["culprit_changed"] = True
                impact["current_culprit"] = twist.new_culprit_id

        return impact

    def to_dict(self) -> dict:
        return {
            "twists": [t.to_dict() for t in self.twists]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TwistManager":
        manager = cls()
        manager.twists = [Twist.from_dict(t) for t in data.get("twists", [])]
        return manager


class TwistGenerator:
    """Generates twists for narrative spines."""

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate_character_twist(
        self,
        character_id: str,
        twist_type: TwistType = None
    ) -> Twist:
        """Generate a character-related twist."""
        if twist_type is None:
            twist_type = random.choice([
                TwistType.HIDDEN_IDENTITY,
                TwistType.SECRET_ALLY,
                TwistType.BETRAYAL,
                TwistType.REDEMPTION
            ])

        templates = {
            TwistType.HIDDEN_IDENTITY: {
                "name": "Hidden Identity",
                "description": f"{character_id} is not who they claim to be",
                "revelation": f"The truth emerges: {character_id} has been living a lie."
            },
            TwistType.SECRET_ALLY: {
                "name": "Secret Ally",
                "description": f"{character_id} has been helping all along",
                "revelation": f"It becomes clear: {character_id} was on your side from the start."
            },
            TwistType.BETRAYAL: {
                "name": "Betrayal",
                "description": f"{character_id} has been working against you",
                "revelation": f"The knife in the back: {character_id} was never your ally."
            },
            TwistType.REDEMPTION: {
                "name": "Redemption Arc",
                "description": f"{character_id} has a sympathetic motivation",
                "revelation": f"Understanding dawns: {character_id} had reasons you never knew."
            }
        }

        template = templates.get(twist_type, templates[TwistType.HIDDEN_IDENTITY])

        return Twist(
            id=f"twist_{character_id}_{twist_type.value}",
            twist_type=twist_type,
            name=template["name"],
            description=template["description"],
            revelation_text=template["revelation"],
            affected_characters=[character_id],
            trigger_conditions=[
                TwistCondition(
                    type="progress",
                    value=0.6,
                    description="Story progress threshold"
                )
            ]
        )

    def generate_plot_twist(
        self,
        twist_type: TwistType = None
    ) -> Twist:
        """Generate a plot-related twist."""
        if twist_type is None:
            twist_type = random.choice([
                TwistType.WRONG_CRIME,
                TwistType.MULTIPLE_CULPRITS,
                TwistType.DEEPER_CONSPIRACY
            ])

        templates = {
            TwistType.WRONG_CRIME: {
                "name": "Wrong Crime",
                "description": "The crime isn't what it appeared to be",
                "revelation": "Everything you thought you knew was wrong. The real crime is far different."
            },
            TwistType.MULTIPLE_CULPRITS: {
                "name": "Multiple Culprits",
                "description": "More than one person is responsible",
                "revelation": "They worked together. This was never a solo operation."
            },
            TwistType.DEEPER_CONSPIRACY: {
                "name": "Deeper Conspiracy",
                "description": "The crime is part of something larger",
                "revelation": "This goes deeper than you imagined. The crime is just the surface."
            },
            TwistType.NO_CRIME: {
                "name": "No Crime",
                "description": "What seemed criminal wasn't",
                "revelation": "There was no crime after all. Just a series of misunderstandings."
            }
        }

        template = templates.get(twist_type, templates[TwistType.WRONG_CRIME])

        return Twist(
            id=f"twist_plot_{twist_type.value}",
            twist_type=twist_type,
            name=template["name"],
            description=template["description"],
            revelation_text=template["revelation"],
            tension_change=0.3,
            trigger_conditions=[
                TwistCondition(
                    type="progress",
                    value=0.7,
                    description="Late-game revelation"
                )
            ]
        )

    def generate_evidence_twist(
        self,
        evidence_id: str = None,
        twist_type: TwistType = None
    ) -> Twist:
        """Generate an evidence-related twist."""
        if twist_type is None:
            twist_type = random.choice([
                TwistType.PLANTED_EVIDENCE,
                TwistType.MISINTERPRETED,
                TwistType.MISSING_PIECE
            ])

        evidence_id = evidence_id or "key_evidence"

        templates = {
            TwistType.PLANTED_EVIDENCE: {
                "name": "Planted Evidence",
                "description": f"The {evidence_id} was fabricated",
                "revelation": f"The {evidence_id} was planted. Someone wanted you to find it."
            },
            TwistType.MISINTERPRETED: {
                "name": "Misinterpreted",
                "description": f"The {evidence_id} means something else entirely",
                "revelation": f"You had it all wrong. The {evidence_id} tells a different story."
            },
            TwistType.MISSING_PIECE: {
                "name": "Missing Piece",
                "description": "Critical evidence was hidden",
                "revelation": "There was something you were never meant to find. Until now."
            }
        }

        template = templates.get(twist_type, templates[TwistType.PLANTED_EVIDENCE])

        return Twist(
            id=f"twist_evidence_{twist_type.value}",
            twist_type=twist_type,
            name=template["name"],
            description=template["description"],
            revelation_text=template["revelation"],
            trigger_conditions=[
                TwistCondition(
                    type="discovery",
                    value=evidence_id,
                    description="Evidence must be found first"
                ),
                TwistCondition(
                    type="progress",
                    value=0.5,
                    description="Mid-game revelation"
                )
            ]
        )
