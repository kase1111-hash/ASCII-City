"""
Character Relationships - NPC-to-NPC interactions and relationships.

Manages how NPCs relate to and interact with each other:
- Relationship tracking (friend, enemy, neutral, etc.)
- NPC-to-NPC conversation simulation
- Group dynamics
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto
import random


class RelationType(Enum):
    """Types of relationships between characters."""
    STRANGER = auto()      # No significant relationship
    ACQUAINTANCE = auto()  # Know each other casually
    COLLEAGUE = auto()     # Work together
    FRIEND = auto()        # Friendly relationship
    CLOSE_FRIEND = auto()  # Very close friends
    RIVAL = auto()         # Competitive rivalry
    ENEMY = auto()         # Active hostility
    LOVER = auto()         # Romantic relationship
    FAMILY = auto()        # Family members
    SUBORDINATE = auto()   # Works under them
    SUPERIOR = auto()      # They work under this person
    ALLY = auto()          # Aligned interests
    CONSPIRATOR = auto()   # Secretly working together


@dataclass
class Relationship:
    """A relationship between two characters."""
    target_id: str
    relation_type: RelationType = RelationType.STRANGER
    affinity: int = 0      # -100 to 100, how much they like them
    trust: int = 0         # -100 to 100, how much they trust them
    tension: int = 0       # 0 to 100, current tension
    shared_secrets: list[str] = field(default_factory=list)
    history: list[str] = field(default_factory=list)

    def modify_affinity(self, amount: int) -> None:
        """Modify affinity, clamped to -100 to 100."""
        self.affinity = max(-100, min(100, self.affinity + amount))
        self._update_type()

    def modify_trust(self, amount: int) -> None:
        """Modify trust, clamped to -100 to 100."""
        self.trust = max(-100, min(100, self.trust + amount))

    def modify_tension(self, amount: int) -> None:
        """Modify tension, clamped to 0 to 100."""
        self.tension = max(0, min(100, self.tension + amount))

    def _update_type(self) -> None:
        """Update relationship type based on affinity."""
        # Don't override special types
        if self.relation_type in (
            RelationType.FAMILY,
            RelationType.LOVER,
            RelationType.SUBORDINATE,
            RelationType.SUPERIOR,
            RelationType.CONSPIRATOR
        ):
            return

        if self.affinity >= 60:
            self.relation_type = RelationType.CLOSE_FRIEND
        elif self.affinity >= 30:
            self.relation_type = RelationType.FRIEND
        elif self.affinity >= -20:
            self.relation_type = RelationType.ACQUAINTANCE
        elif self.affinity >= -50:
            self.relation_type = RelationType.RIVAL
        else:
            self.relation_type = RelationType.ENEMY

    def add_shared_secret(self, secret: str) -> None:
        """Add a shared secret between characters."""
        if secret not in self.shared_secrets:
            self.shared_secrets.append(secret)
            self.modify_trust(10)

    def add_to_history(self, event: str) -> None:
        """Record a significant event in the relationship."""
        self.history.append(event)

    def to_dict(self) -> dict:
        """Serialize relationship."""
        return {
            "target_id": self.target_id,
            "relation_type": self.relation_type.name,
            "affinity": self.affinity,
            "trust": self.trust,
            "tension": self.tension,
            "shared_secrets": self.shared_secrets,
            "history": self.history
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Relationship":
        """Deserialize relationship."""
        return cls(
            target_id=data["target_id"],
            relation_type=RelationType[data.get("relation_type", "STRANGER")],
            affinity=data.get("affinity", 0),
            trust=data.get("trust", 0),
            tension=data.get("tension", 0),
            shared_secrets=data.get("shared_secrets", []),
            history=data.get("history", [])
        )


@dataclass
class NPCInteractionResult:
    """Result of an NPC-to-NPC interaction."""
    character1_id: str
    character2_id: str
    interaction_type: str
    description: str
    affinity_change_1: int = 0
    affinity_change_2: int = 0
    tension_change: int = 0
    information_shared: list[str] = field(default_factory=list)
    witnessed_by: list[str] = field(default_factory=list)


class RelationshipManager:
    """
    Manages all relationships between characters.

    Provides methods for simulating NPC-to-NPC interactions
    and tracking relationship dynamics.
    """

    def __init__(self):
        # relationships[char_id][target_id] = Relationship
        self.relationships: dict[str, dict[str, Relationship]] = {}

        # Interaction history
        self.interaction_log: list[NPCInteractionResult] = []

        # RNG for interaction simulation
        self._rng = random.Random()

    def set_seed(self, seed: int) -> None:
        """Set RNG seed for deterministic interactions."""
        self._rng.seed(seed)

    def register_character(self, character_id: str) -> None:
        """Register a new character in the relationship system."""
        if character_id not in self.relationships:
            self.relationships[character_id] = {}

    def set_relationship(
        self,
        char1_id: str,
        char2_id: str,
        relation_type: RelationType,
        affinity: int = 0,
        trust: int = 0,
        bidirectional: bool = True
    ) -> None:
        """Set a relationship between two characters."""
        self.register_character(char1_id)
        self.register_character(char2_id)

        self.relationships[char1_id][char2_id] = Relationship(
            target_id=char2_id,
            relation_type=relation_type,
            affinity=affinity,
            trust=trust
        )

        if bidirectional:
            # Reverse relationship (may be different type for hierarchies)
            reverse_type = relation_type
            if relation_type == RelationType.SUBORDINATE:
                reverse_type = RelationType.SUPERIOR
            elif relation_type == RelationType.SUPERIOR:
                reverse_type = RelationType.SUBORDINATE

            self.relationships[char2_id][char1_id] = Relationship(
                target_id=char1_id,
                relation_type=reverse_type,
                affinity=affinity,
                trust=trust
            )

    def get_relationship(
        self,
        char1_id: str,
        char2_id: str
    ) -> Optional[Relationship]:
        """Get the relationship from char1 to char2."""
        if char1_id in self.relationships:
            return self.relationships[char1_id].get(char2_id)
        return None

    def get_all_relationships(self, character_id: str) -> dict[str, Relationship]:
        """Get all relationships for a character."""
        return self.relationships.get(character_id, {})

    def simulate_interaction(
        self,
        char1_id: str,
        char2_id: str,
        location: str,
        witnesses: list[str] = None,
        context: dict = None
    ) -> NPCInteractionResult:
        """
        Simulate an interaction between two NPCs.

        Returns the result of the interaction including any changes
        to relationships and information shared.
        """
        witnesses = witnesses or []
        context = context or {}

        rel1 = self.get_relationship(char1_id, char2_id)
        rel2 = self.get_relationship(char2_id, char1_id)

        # Create relationships if they don't exist
        if not rel1:
            self.set_relationship(char1_id, char2_id, RelationType.STRANGER)
            rel1 = self.get_relationship(char1_id, char2_id)
        if not rel2:
            rel2 = self.get_relationship(char2_id, char1_id)

        # Determine interaction type based on relationship
        interaction_type = self._determine_interaction_type(rel1, rel2, context)

        # Simulate the interaction
        result = self._simulate_interaction_outcome(
            char1_id, char2_id, rel1, rel2, interaction_type, location, witnesses
        )

        # Apply changes
        if rel1:
            rel1.modify_affinity(result.affinity_change_1)
            rel1.modify_tension(result.tension_change)
        if rel2:
            rel2.modify_affinity(result.affinity_change_2)
            rel2.modify_tension(result.tension_change)

        # Log interaction
        self.interaction_log.append(result)

        return result

    def _determine_interaction_type(
        self,
        rel1: Relationship,
        rel2: Relationship,
        context: dict
    ) -> str:
        """Determine what kind of interaction will occur."""
        # Check for high tension
        if rel1 and rel1.tension > 70:
            return "confrontation"

        # Check relationship types
        if rel1 and rel1.relation_type == RelationType.ENEMY:
            return "hostile_exchange"

        if rel1 and rel1.relation_type == RelationType.CONSPIRATOR:
            return "secret_meeting"

        if rel1 and rel1.relation_type in (
            RelationType.FRIEND, RelationType.CLOSE_FRIEND, RelationType.LOVER
        ):
            return "friendly_chat"

        if rel1 and rel1.relation_type in (
            RelationType.SUBORDINATE, RelationType.SUPERIOR
        ):
            return "work_discussion"

        # Default to casual
        return "casual_greeting"

    def _simulate_interaction_outcome(
        self,
        char1_id: str,
        char2_id: str,
        rel1: Relationship,
        rel2: Relationship,
        interaction_type: str,
        location: str,
        witnesses: list[str]
    ) -> NPCInteractionResult:
        """Simulate the outcome of an interaction."""
        descriptions = {
            "casual_greeting": [
                f"exchanged brief pleasantries",
                f"nodded to each other in passing",
                f"had a brief, formal conversation"
            ],
            "friendly_chat": [
                f"had an animated conversation",
                f"shared a laugh together",
                f"spoke warmly to each other"
            ],
            "hostile_exchange": [
                f"exchanged cold glances",
                f"had a tense, brief interaction",
                f"barely acknowledged each other"
            ],
            "confrontation": [
                f"had a heated argument",
                f"confronted each other loudly",
                f"had a visible altercation"
            ],
            "secret_meeting": [
                f"spoke quietly together",
                f"had a hushed conversation",
                f"whispered to each other conspiratorially"
            ],
            "work_discussion": [
                f"discussed business matters",
                f"reviewed work responsibilities",
                f"had a professional exchange"
            ]
        }

        desc_options = descriptions.get(interaction_type, ["interacted"])
        description = self._rng.choice(desc_options)

        # Calculate relationship changes
        affinity_changes = {
            "casual_greeting": (1, 1),
            "friendly_chat": (3, 3),
            "hostile_exchange": (-2, -2),
            "confrontation": (-5, -5),
            "secret_meeting": (2, 2),
            "work_discussion": (1, 1)
        }

        tension_changes = {
            "casual_greeting": -2,
            "friendly_chat": -5,
            "hostile_exchange": 5,
            "confrontation": 15,
            "secret_meeting": 0,
            "work_discussion": -1
        }

        aff1, aff2 = affinity_changes.get(interaction_type, (0, 0))
        tension = tension_changes.get(interaction_type, 0)

        # Information sharing for friendly/secret interactions
        info_shared = []
        if interaction_type in ("friendly_chat", "secret_meeting"):
            if rel1 and rel1.shared_secrets:
                # Might share a secret
                if self._rng.random() < 0.3:
                    info_shared.append(self._rng.choice(rel1.shared_secrets))

        return NPCInteractionResult(
            character1_id=char1_id,
            character2_id=char2_id,
            interaction_type=interaction_type,
            description=description,
            affinity_change_1=aff1,
            affinity_change_2=aff2,
            tension_change=tension,
            information_shared=info_shared,
            witnessed_by=witnesses
        )

    def get_characters_in_location(
        self,
        location: str,
        character_locations: dict[str, str]
    ) -> list[str]:
        """Get all characters in a location."""
        return [
            char_id for char_id, loc in character_locations.items()
            if loc == location
        ]

    def simulate_location_interactions(
        self,
        location: str,
        character_locations: dict[str, str],
        max_interactions: int = 3
    ) -> list[NPCInteractionResult]:
        """
        Simulate all NPC interactions at a location.

        Returns list of interaction results.
        """
        characters = self.get_characters_in_location(location, character_locations)
        results = []

        if len(characters) < 2:
            return results

        # Simulate some interactions
        pairs_tried = set()
        for _ in range(min(max_interactions, len(characters))):
            # Pick two random characters
            if len(characters) < 2:
                break

            char1 = self._rng.choice(characters)
            remaining = [c for c in characters if c != char1]
            if not remaining:
                break
            char2 = self._rng.choice(remaining)

            pair = tuple(sorted([char1, char2]))
            if pair in pairs_tried:
                continue
            pairs_tried.add(pair)

            # Get witnesses (other characters in location)
            witnesses = [c for c in characters if c not in (char1, char2)]

            result = self.simulate_interaction(
                char1, char2, location, witnesses
            )
            results.append(result)

        return results

    def to_dict(self) -> dict:
        """Serialize relationship manager."""
        return {
            "relationships": {
                char_id: {
                    target_id: rel.to_dict()
                    for target_id, rel in rels.items()
                }
                for char_id, rels in self.relationships.items()
            },
            "interaction_log": [
                {
                    "character1_id": r.character1_id,
                    "character2_id": r.character2_id,
                    "interaction_type": r.interaction_type,
                    "description": r.description,
                    "affinity_change_1": r.affinity_change_1,
                    "affinity_change_2": r.affinity_change_2,
                    "tension_change": r.tension_change,
                    "information_shared": r.information_shared,
                    "witnessed_by": r.witnessed_by
                }
                for r in self.interaction_log[-50:]  # Keep last 50
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RelationshipManager":
        """Deserialize relationship manager."""
        manager = cls()

        for char_id, rels in data.get("relationships", {}).items():
            manager.relationships[char_id] = {
                target_id: Relationship.from_dict(rel_data)
                for target_id, rel_data in rels.items()
            }

        for log_entry in data.get("interaction_log", []):
            manager.interaction_log.append(NPCInteractionResult(
                character1_id=log_entry["character1_id"],
                character2_id=log_entry["character2_id"],
                interaction_type=log_entry["interaction_type"],
                description=log_entry["description"],
                affinity_change_1=log_entry.get("affinity_change_1", 0),
                affinity_change_2=log_entry.get("affinity_change_2", 0),
                tension_change=log_entry.get("tension_change", 0),
                information_shared=log_entry.get("information_shared", []),
                witnessed_by=log_entry.get("witnessed_by", [])
            ))

        return manager
