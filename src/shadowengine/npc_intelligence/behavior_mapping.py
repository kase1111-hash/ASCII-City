"""
MemoryBehaviorMapping - Translates memories into behavior changes.

NPC memories directly alter their affordances toward the player and
other NPCs. This is the bridge between what NPCs believe and how
they act.
"""

from dataclasses import dataclass
from typing import Optional, Any
from enum import Enum

from .npc_memory import NPCMemory


class BehaviorType(Enum):
    """Types of NPC behaviors."""
    AVOID_AREA = "avoid_area"
    WARN_PLAYER = "warn_player"
    HELP_PLAYER = "help_player"
    LIE_TO_PLAYER = "lie_to_player"
    FLEE_FROM_PLAYER = "flee_from_player"
    CONFIDE_IN_PLAYER = "confide_in_player"
    SILENCE = "silence"             # Won't share information
    ACT_NORMAL = "act_normal"       # Pretend nothing's wrong
    ATTACK = "attack"               # Become hostile
    INVESTIGATE = "investigate"     # Seek more information
    GOSSIP = "gossip"               # Share with others freely


@dataclass
class BehaviorModifier:
    """
    Modification to NPC behavior based on memories.

    These modifiers stack and are applied when determining
    NPC responses to player interactions.
    """

    # Trust modifiers (-1.0 to 1.0)
    trusts: float = 0.0             # How much they trust player
    reveals: float = 0.0            # How likely to share info
    cooperates: float = 0.0         # How likely to help

    # Fear modifiers
    fears: float = 0.0              # Fear of player
    threatens: float = 0.0          # Feels threatened

    # Social modifiers
    respects: float = 0.0           # Respect for player
    suspicious_of: float = 0.0      # Suspicion level

    def apply(self, other: 'BehaviorModifier') -> 'BehaviorModifier':
        """Combine this modifier with another."""
        return BehaviorModifier(
            trusts=max(-1.0, min(1.0, self.trusts + other.trusts)),
            reveals=max(-1.0, min(1.0, self.reveals + other.reveals)),
            cooperates=max(-1.0, min(1.0, self.cooperates + other.cooperates)),
            fears=max(-1.0, min(1.0, self.fears + other.fears)),
            threatens=max(-1.0, min(1.0, self.threatens + other.threatens)),
            respects=max(-1.0, min(1.0, self.respects + other.respects)),
            suspicious_of=max(-1.0, min(1.0, self.suspicious_of + other.suspicious_of))
        )

    def scale(self, factor: float) -> 'BehaviorModifier':
        """Scale all modifiers by a factor."""
        return BehaviorModifier(
            trusts=self.trusts * factor,
            reveals=self.reveals * factor,
            cooperates=self.cooperates * factor,
            fears=self.fears * factor,
            threatens=self.threatens * factor,
            respects=self.respects * factor,
            suspicious_of=self.suspicious_of * factor
        )

    def to_dict(self) -> dict:
        return {
            "trusts": self.trusts,
            "reveals": self.reveals,
            "cooperates": self.cooperates,
            "fears": self.fears,
            "threatens": self.threatens,
            "respects": self.respects,
            "suspicious_of": self.suspicious_of
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BehaviorModifier':
        return cls(**data)


# Memory tag -> behavior mappings
MEMORY_TAG_BEHAVIORS = {
    # Danger perception
    "danger": {
        "behavior": BehaviorType.AVOID_AREA,
        "modifier": BehaviorModifier(cooperates=-0.3)
    },
    "death_here": {
        "behavior": BehaviorType.WARN_PLAYER,
        "modifier": BehaviorModifier(cooperates=0.1, reveals=0.1)
    },
    "violence": {
        "behavior": BehaviorType.AVOID_AREA,
        "modifier": BehaviorModifier(fears=0.2, cooperates=-0.2)
    },

    # Player perception
    "player_suspicious": {
        "behavior": BehaviorType.LIE_TO_PLAYER,
        "modifier": BehaviorModifier(trusts=-0.4, reveals=-0.5, suspicious_of=0.3)
    },
    "player_violent": {
        "behavior": BehaviorType.FLEE_FROM_PLAYER,
        "modifier": BehaviorModifier(threatens=0.3, cooperates=-0.6, fears=0.4)
    },
    "player_helpful": {
        "behavior": BehaviorType.HELP_PLAYER,
        "modifier": BehaviorModifier(trusts=0.3, reveals=0.2, respects=0.2)
    },
    "player_trustworthy": {
        "behavior": BehaviorType.CONFIDE_IN_PLAYER,
        "modifier": BehaviorModifier(reveals=0.5, trusts=0.4)
    },
    "player_threatening": {
        "behavior": BehaviorType.SILENCE,
        "modifier": BehaviorModifier(fears=0.5, reveals=-0.4)
    },

    # External threats
    "mob_involved": {
        "behavior": BehaviorType.SILENCE,
        "modifier": BehaviorModifier(reveals=-0.8, fears=0.5)
    },
    "cops_watching": {
        "behavior": BehaviorType.ACT_NORMAL,
        "modifier": BehaviorModifier(reveals=-0.3)
    },
    "conspiracy": {
        "behavior": BehaviorType.SILENCE,
        "modifier": BehaviorModifier(reveals=-0.4, suspicious_of=0.3)
    },

    # Information types
    "valuable_info": {
        "behavior": BehaviorType.SILENCE,
        "modifier": BehaviorModifier(reveals=-0.2)
    },
    "crime": {
        "behavior": BehaviorType.GOSSIP,
        "modifier": BehaviorModifier(reveals=0.2)
    },
    "interesting": {
        "behavior": BehaviorType.INVESTIGATE,
        "modifier": BehaviorModifier(reveals=0.1)
    }
}


class MemoryBehaviorMapping:
    """
    System for translating NPC memories into behavior changes.

    Aggregates effects from all memories to determine how an NPC
    will respond in any given situation.
    """

    def __init__(self):
        self.tag_behaviors = MEMORY_TAG_BEHAVIORS.copy()
        self.recency_weight_decay = 0.1  # How much recency matters

    def calculate_recency_weight(
        self,
        memory_timestamp: float,
        current_time: float
    ) -> float:
        """Calculate weight based on how recent the memory is."""
        age = current_time - memory_timestamp
        return max(0.1, 1.0 - (age * self.recency_weight_decay))

    def get_behavior_from_memory(
        self,
        memory: NPCMemory
    ) -> tuple[Optional[BehaviorType], BehaviorModifier]:
        """
        Get behavior and modifier from a single memory.

        Returns (behavior_type, modifier) tuple.
        """
        total_modifier = BehaviorModifier()
        primary_behavior = None

        for tag in memory.tags:
            if tag in self.tag_behaviors:
                mapping = self.tag_behaviors[tag]
                behavior = mapping["behavior"]
                modifier = mapping["modifier"]

                # Weight by memory confidence
                weighted = modifier.scale(memory.confidence)
                total_modifier = total_modifier.apply(weighted)

                # Higher priority behaviors override
                if primary_behavior is None:
                    primary_behavior = behavior

        return primary_behavior, total_modifier

    def aggregate_modifiers(
        self,
        memories: list[NPCMemory],
        current_time: float
    ) -> BehaviorModifier:
        """
        Aggregate behavior modifiers from all memories.

        Takes into account recency and confidence.
        """
        total = BehaviorModifier()

        for memory in memories:
            _, modifier = self.get_behavior_from_memory(memory)

            # Weight by recency
            recency = self.calculate_recency_weight(memory.timestamp, current_time)
            weighted = modifier.scale(recency)

            total = total.apply(weighted)

        return total

    def get_response_type(self, modifier: BehaviorModifier) -> str:
        """
        Determine NPC's response type based on aggregated modifiers.

        Returns one of: flee, help, lie, refuse, neutral
        """
        if modifier.fears > 0.5:
            return "flee"
        if modifier.trusts > 0.5:
            return "help"
        if modifier.reveals < -0.5:
            return "lie"
        if modifier.cooperates < -0.3:
            return "refuse"
        return "neutral"

    def will_share_information(self, modifier: BehaviorModifier) -> bool:
        """Check if NPC will share information based on modifiers."""
        return modifier.reveals > -0.3

    def will_cooperate(self, modifier: BehaviorModifier) -> bool:
        """Check if NPC will cooperate based on modifiers."""
        return modifier.cooperates > -0.2 and modifier.fears < 0.5

    def get_dialogue_modifiers(
        self,
        modifier: BehaviorModifier
    ) -> dict[str, Any]:
        """
        Get dialogue system modifiers based on behavior.

        Returns hints for dialogue generation.
        """
        hints = {
            "tone": "neutral",
            "willingness": "medium",
            "honesty": "honest",
            "detail_level": "normal"
        }

        # Tone
        if modifier.fears > 0.3:
            hints["tone"] = "fearful"
        elif modifier.trusts > 0.3:
            hints["tone"] = "friendly"
        elif modifier.threatens > 0.3:
            hints["tone"] = "hostile"
        elif modifier.suspicious_of > 0.3:
            hints["tone"] = "suspicious"

        # Willingness to engage
        if modifier.cooperates > 0.3:
            hints["willingness"] = "high"
        elif modifier.cooperates < -0.3:
            hints["willingness"] = "low"

        # Honesty
        if modifier.reveals < -0.3 or modifier.trusts < -0.3:
            hints["honesty"] = "evasive"
        if modifier.reveals < -0.5:
            hints["honesty"] = "lying"

        # Detail level
        if modifier.reveals > 0.3:
            hints["detail_level"] = "high"
        elif modifier.reveals < -0.3:
            hints["detail_level"] = "sparse"

        return hints


class MemoryBehaviorSystem:
    """
    High-level system for managing memory-based behavior.

    Integrates with NPC system to update behaviors based on memories.
    """

    def __init__(self):
        self.mapping = MemoryBehaviorMapping()
        self.npc_modifiers: dict[str, BehaviorModifier] = {}

    def update_npc_behavior(
        self,
        npc_id: str,
        memories: list[NPCMemory],
        current_time: float
    ) -> BehaviorModifier:
        """
        Update NPC behavior based on their memories.

        Returns the aggregated behavior modifier.
        """
        modifier = self.mapping.aggregate_modifiers(memories, current_time)
        self.npc_modifiers[npc_id] = modifier
        return modifier

    def get_npc_response(
        self,
        npc_id: str,
        context: Optional[str] = None
    ) -> str:
        """Get NPC's behavioral response type."""
        modifier = self.npc_modifiers.get(npc_id, BehaviorModifier())
        return self.mapping.get_response_type(modifier)

    def get_npc_dialogue_hints(
        self,
        npc_id: str
    ) -> dict[str, Any]:
        """Get dialogue hints for an NPC."""
        modifier = self.npc_modifiers.get(npc_id, BehaviorModifier())
        return self.mapping.get_dialogue_modifiers(modifier)

    def will_npc_share(self, npc_id: str) -> bool:
        """Check if NPC will share information."""
        modifier = self.npc_modifiers.get(npc_id, BehaviorModifier())
        return self.mapping.will_share_information(modifier)

    def will_npc_cooperate(self, npc_id: str) -> bool:
        """Check if NPC will cooperate."""
        modifier = self.npc_modifiers.get(npc_id, BehaviorModifier())
        return self.mapping.will_cooperate(modifier)

    def add_memory_effect(
        self,
        npc_id: str,
        memory: NPCMemory
    ) -> None:
        """Add effect of a single new memory."""
        _, modifier = self.mapping.get_behavior_from_memory(memory)
        current = self.npc_modifiers.get(npc_id, BehaviorModifier())
        self.npc_modifiers[npc_id] = current.apply(modifier)

    def clear_npc(self, npc_id: str) -> None:
        """Clear modifiers for an NPC."""
        if npc_id in self.npc_modifiers:
            del self.npc_modifiers[npc_id]

    def to_dict(self) -> dict:
        """Serialize behavior system."""
        return {
            "npc_modifiers": {
                k: v.to_dict() for k, v in self.npc_modifiers.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MemoryBehaviorSystem':
        """Deserialize behavior system."""
        system = cls()
        system.npc_modifiers = {
            k: BehaviorModifier.from_dict(v)
            for k, v in data.get("npc_modifiers", {}).items()
        }
        return system
