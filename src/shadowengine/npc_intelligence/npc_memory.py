"""
NPCMemory - What an NPC believes happened.

Each NPC stores subjective memory objects - their interpretation of events,
not facts. Memories decay over time, are affected by emotion, and can be
distorted by bias.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid


class MemorySource(Enum):
    """How the NPC learned this information."""
    SELF = "self"               # Witnessed it directly
    FRIEND = "friend"           # Told by someone they trust
    ACQUAINTANCE = "acquaintance"  # Told by someone they know
    RUMOR = "rumor"             # Heard through gossip
    ENEMY = "enemy"             # Told by someone they distrust


@dataclass
class NPCMemory:
    """
    What an NPC believes happened.

    This is subjective - not truth. The summary is the NPC's interpretation,
    which may be wrong, incomplete, biased, or outdated.
    """

    # Reference
    memory_id: str = ""
    event_id: Optional[str] = None  # May be null for pure rumors

    # Subjective content
    summary: str = ""               # NPC's interpretation, NOT fact
    tags: list[str] = field(default_factory=list)  # ["danger", "water", "death"]

    # Confidence & emotion
    confidence: float = 1.0         # 0.0-1.0: How sure they are
    emotional_weight: float = 0.5   # 0.0-1.0: How much it affects them
    fear: float = 0.0               # 0.0-1.0: Fear associated
    anger: float = 0.0              # 0.0-1.0: Anger associated
    sadness: float = 0.0            # 0.0-1.0: Sadness associated
    curiosity: float = 0.0          # 0.0-1.0: Curiosity associated

    # Source
    source: MemorySource = MemorySource.SELF
    source_npc: Optional[str] = None  # Who told them (if not self)

    # Metadata
    timestamp: float = 0.0          # When they learned it
    location: Optional[str] = None  # Where it happened
    location_coords: Optional[tuple[int, int]] = None
    last_recalled: float = 0.0      # Last time they thought about it

    # Decay
    decay_rate: float = 0.01        # How fast confidence drops per time unit
    is_traumatic: bool = False      # Traumatic memories decay slower

    # Actor references
    actors: list[str] = field(default_factory=list)  # Who was involved

    def __post_init__(self):
        if not self.memory_id:
            self.memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        if self.location_coords is not None and isinstance(self.location_coords, list):
            self.location_coords = tuple(self.location_coords)

    def recall(self, current_time: float) -> None:
        """Mark this memory as recalled, slowing its decay."""
        self.last_recalled = current_time

    def get_retention_priority(self) -> float:
        """
        Calculate how important this memory is to keep.
        Higher = kept longer when pruning.
        """
        return (
            self.confidence * 0.3 +
            self.emotional_weight * 0.4 +
            self.fear * 0.2 +
            (0.1 if self.source == MemorySource.SELF else 0.05)
        )

    def get_share_probability(self) -> float:
        """
        Calculate likelihood of sharing this memory.
        Higher = more likely to tell others.
        """
        return (
            self.emotional_weight * 0.5 +
            self.confidence * 0.3 +
            (self.fear + self.anger) * 0.2
        )

    def has_tag(self, tag: str) -> bool:
        """Check if memory has a specific tag."""
        return tag in self.tags

    def add_tag(self, tag: str) -> None:
        """Add a tag to this memory."""
        if tag not in self.tags:
            self.tags.append(tag)

    def involves_actor(self, actor_id: str) -> bool:
        """Check if memory involves a specific actor."""
        return actor_id in self.actors

    def to_dict(self) -> dict:
        """Serialize memory to dictionary."""
        return {
            "memory_id": self.memory_id,
            "event_id": self.event_id,
            "summary": self.summary,
            "tags": self.tags,
            "confidence": self.confidence,
            "emotional_weight": self.emotional_weight,
            "fear": self.fear,
            "anger": self.anger,
            "sadness": self.sadness,
            "curiosity": self.curiosity,
            "source": self.source.value,
            "source_npc": self.source_npc,
            "timestamp": self.timestamp,
            "location": self.location,
            "location_coords": list(self.location_coords) if self.location_coords else None,
            "last_recalled": self.last_recalled,
            "decay_rate": self.decay_rate,
            "is_traumatic": self.is_traumatic,
            "actors": self.actors
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'NPCMemory':
        """Deserialize memory from dictionary."""
        data = dict(data)  # Don't mutate the input dictionary
        data["source"] = MemorySource(data["source"])
        if data.get("location_coords"):
            data["location_coords"] = tuple(data["location_coords"])
        return cls(**data)


# Memory capacity by NPC type
NPC_MEMORY_CAPACITY = {
    "civilian": 10,
    "bartender": 25,
    "informant": 40,
    "cop": 35,
    "mob_boss": 60,
    "street_urchin": 15,
    "detective": 50,
    "politician": 45,
    "journalist": 40,
    "default": 20
}


class MemoryDecaySystem:
    """
    Manages memory decay over time.

    Memories fade naturally, but emotional memories decay slower,
    and traumatic memories barely decay at all.
    """

    def __init__(self):
        self.base_decay_rate = 0.01
        self.emotional_decay_reduction = 0.5  # 50% slower for emotional
        self.traumatic_decay_reduction = 0.9  # 90% slower for traumatic

    def decay_memory(self, memory: NPCMemory, dt: float) -> float:
        """
        Apply decay to a single memory.

        Returns the new confidence value.
        """
        # Base decay
        decay = memory.decay_rate * dt

        # Emotional memories decay slower
        decay *= (1.0 - memory.emotional_weight * self.emotional_decay_reduction)

        # Traumatic memories barely decay
        if memory.is_traumatic or memory.fear > 0.8:
            decay *= (1.0 - self.traumatic_decay_reduction)

        # High-tag memories decay slower (they're more distinctive)
        if len(memory.tags) > 3:
            decay *= 0.8

        memory.confidence = max(0.0, memory.confidence - decay)
        return memory.confidence

    def decay_all_memories(
        self,
        memories: list[NPCMemory],
        dt: float
    ) -> list[NPCMemory]:
        """Apply decay to all memories, returning those still remembered."""
        result = []
        for memory in memories:
            new_confidence = self.decay_memory(memory, dt)
            if new_confidence > 0.05:  # Threshold for "forgotten"
                result.append(memory)
        return result

    def prune_memories(
        self,
        memories: list[NPCMemory],
        capacity: int
    ) -> list[NPCMemory]:
        """
        Remove lowest priority memories when over capacity.

        Returns the pruned list.
        """
        if len(memories) <= capacity:
            return memories

        # Sort by retention priority (lowest first)
        sorted_memories = sorted(
            memories,
            key=lambda m: m.get_retention_priority()
        )

        # Remove lowest priority until under capacity
        return sorted_memories[-(capacity):]

    def get_memory_capacity(self, npc_type: str) -> int:
        """Get memory capacity for an NPC type."""
        return NPC_MEMORY_CAPACITY.get(npc_type, NPC_MEMORY_CAPACITY["default"])


class NPCMemoryBank:
    """
    Complete memory system for a single NPC.

    Manages memory storage, decay, retrieval, and capacity limits.
    """

    def __init__(self, npc_id: str, npc_type: str = "default"):
        self.npc_id = npc_id
        self.npc_type = npc_type
        self.memories: list[NPCMemory] = []
        self.decay_system = MemoryDecaySystem()
        self.capacity = self.decay_system.get_memory_capacity(npc_type)
        self.current_time: float = 0.0

    def add_memory(self, memory: NPCMemory) -> None:
        """Add a memory, pruning if over capacity."""
        self.memories.append(memory)
        if len(self.memories) > self.capacity:
            self.memories = self.decay_system.prune_memories(
                self.memories, self.capacity
            )

    def update(self, dt: float) -> None:
        """Update all memories with decay."""
        self.current_time += dt
        self.memories = self.decay_system.decay_all_memories(self.memories, dt)

    def get_memories_about(self, subject: str) -> list[NPCMemory]:
        """Get all memories about a subject (by tag or actor)."""
        return [
            m for m in self.memories
            if subject in m.tags or subject in m.actors or subject in m.summary.lower()
        ]

    def get_memories_at_location(self, location: str) -> list[NPCMemory]:
        """Get all memories at a location."""
        return [m for m in self.memories if m.location == location]

    def get_memories_by_tag(self, tag: str) -> list[NPCMemory]:
        """Get all memories with a specific tag."""
        return [m for m in self.memories if tag in m.tags]

    def get_recent_memories(self, count: int = 5) -> list[NPCMemory]:
        """Get most recent memories."""
        sorted_memories = sorted(
            self.memories,
            key=lambda m: m.timestamp,
            reverse=True
        )
        return sorted_memories[:count]

    def get_emotional_memories(self, threshold: float = 0.5) -> list[NPCMemory]:
        """Get memories with high emotional weight."""
        return [
            m for m in self.memories
            if m.emotional_weight >= threshold
        ]

    def get_shareable_memories(self, threshold: float = 0.3) -> list[NPCMemory]:
        """Get memories likely to be shared."""
        return [
            m for m in self.memories
            if m.get_share_probability() >= threshold
        ]

    def recall_memory(self, memory_id: str) -> Optional[NPCMemory]:
        """Recall a specific memory, slowing its decay."""
        for memory in self.memories:
            if memory.memory_id == memory_id:
                memory.recall(self.current_time)
                return memory
        return None

    def has_memory_of_event(self, event_id: str) -> bool:
        """Check if NPC has a memory of a specific event."""
        return any(m.event_id == event_id for m in self.memories)

    def get_memory_of_event(self, event_id: str) -> Optional[NPCMemory]:
        """Get memory of a specific event."""
        for memory in self.memories:
            if memory.event_id == event_id:
                return memory
        return None

    def to_dict(self) -> dict:
        """Serialize memory bank."""
        return {
            "npc_id": self.npc_id,
            "npc_type": self.npc_type,
            "memories": [m.to_dict() for m in self.memories],
            "capacity": self.capacity,
            "current_time": self.current_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'NPCMemoryBank':
        """Deserialize memory bank."""
        bank = cls(data["npc_id"], data.get("npc_type", "default"))
        bank.memories = [NPCMemory.from_dict(m) for m in data.get("memories", [])]
        bank.capacity = data.get("capacity", bank.capacity)
        bank.current_time = data.get("current_time", 0.0)
        return bank
