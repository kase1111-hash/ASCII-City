"""
TileMemory - Environmental memory per location.

Places remember things too (Dwarf Fortress-inspired). Events that happen
at a location affect that location's "memory", which influences NPC
behavior and atmosphere when they visit.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import uuid


@dataclass
class TileMemory:
    """
    What has happened at a specific location.

    This affects how NPCs perceive and interact with the location,
    and provides atmospheric hints for rendering.
    """

    location: tuple[int, int] = (0, 0)
    location_name: str = ""

    # Events that happened here
    event_history: list[str] = field(default_factory=list)  # Event IDs
    event_tags: set[str] = field(default_factory=set)       # Aggregated tags

    # Derived metrics (0.0 - 1.0)
    rumor_density: float = 0.0      # How much people talk about this place
    danger_rating: float = 0.0      # Perceived danger
    activity_level: float = 0.5     # How busy/quiet
    crime_rating: float = 0.0       # Criminal activity history
    death_count: int = 0            # Number of deaths here

    # Effects on NPCs
    npc_avoidance: float = 0.0      # NPCs avoid this area
    npc_curiosity: float = 0.0      # NPCs investigate this area

    # Atmosphere
    mood_modifier: str = "neutral"  # neutral, ominous, peaceful, tense, etc.

    # Timestamps
    last_event: float = 0.0
    last_updated: float = 0.0
    decay_rate: float = 0.005       # How fast memories fade

    def __post_init__(self):
        if isinstance(self.location, list):
            self.location = tuple(self.location)
        if isinstance(self.event_tags, list):
            self.event_tags = set(self.event_tags)

    def add_event(
        self,
        event_id: str,
        event_type: str,
        tags: list[str],
        timestamp: float,
        severity: float = 0.5
    ) -> None:
        """Record an event at this location."""
        self.event_history.append(event_id)
        self.event_tags.update(tags)
        self.last_event = timestamp
        self.last_updated = timestamp

        # Update metrics based on event type
        if event_type == "violence":
            self.danger_rating = min(1.0, self.danger_rating + 0.3 * severity)
            self.crime_rating = min(1.0, self.crime_rating + 0.2 * severity)
            self.npc_avoidance = min(1.0, self.npc_avoidance + 0.2 * severity)

        elif event_type == "death":
            self.danger_rating = min(1.0, self.danger_rating + 0.5)
            self.death_count += 1
            self.npc_avoidance = min(1.0, self.npc_avoidance + 0.4)
            self.mood_modifier = "ominous"

        elif event_type == "injury":
            self.danger_rating = min(1.0, self.danger_rating + 0.2 * severity)
            self.npc_avoidance = min(1.0, self.npc_avoidance + 0.1 * severity)

        elif event_type == "theft":
            self.crime_rating = min(1.0, self.crime_rating + 0.3 * severity)

        elif event_type == "discovery":
            self.npc_curiosity = min(1.0, self.npc_curiosity + 0.2)

        elif event_type == "conversation":
            self.activity_level = min(1.0, self.activity_level + 0.1)
            self.rumor_density = min(1.0, self.rumor_density + 0.1)

        # Update mood based on accumulated state
        self._update_mood()

    def add_rumor_activity(self, amount: float = 0.1) -> None:
        """Increase rumor density when this place is discussed."""
        self.rumor_density = min(1.0, self.rumor_density + amount)

    def decay(self, dt: float) -> None:
        """Apply decay over time - locations heal."""
        # Danger and crime ratings decay slowly
        self.danger_rating = max(0.0, self.danger_rating - self.decay_rate * dt)
        self.crime_rating = max(0.0, self.crime_rating - self.decay_rate * dt)
        self.npc_avoidance = max(0.0, self.npc_avoidance - self.decay_rate * dt * 0.5)
        self.npc_curiosity = max(0.0, self.npc_curiosity - self.decay_rate * dt)
        self.rumor_density = max(0.0, self.rumor_density - self.decay_rate * dt * 0.5)

        # Update mood after decay
        self._update_mood()

    def _update_mood(self) -> None:
        """Update mood modifier based on current state."""
        if self.death_count > 0 or self.danger_rating > 0.7:
            self.mood_modifier = "ominous"
        elif self.danger_rating > 0.4 or self.crime_rating > 0.5:
            self.mood_modifier = "tense"
        elif self.activity_level > 0.7:
            self.mood_modifier = "busy"
        elif self.activity_level < 0.2:
            self.mood_modifier = "quiet"
        elif self.npc_curiosity > 0.5:
            self.mood_modifier = "mysterious"
        else:
            self.mood_modifier = "neutral"

    def get_atmosphere_hints(self) -> list[str]:
        """Get atmospheric hints for rendering/LLM."""
        hints = []

        if self.danger_rating > 0.5:
            hints.append("This place feels dangerous")
        if self.death_count > 0:
            hints.append("Death has visited here")
        if "blood" in self.event_tags:
            hints.append("There are dark stains on the ground")
        if self.npc_avoidance > 0.6:
            hints.append("People don't linger here")
        if self.rumor_density > 0.7:
            hints.append("This place has a reputation")
        if self.crime_rating > 0.5:
            hints.append("Criminal activity happens here")
        if self.activity_level < 0.2:
            hints.append("It's unusually quiet")
        if self.npc_curiosity > 0.5:
            hints.append("Something interesting happened here recently")

        return hints

    def get_dialogue_tone(self) -> str:
        """Get suggested dialogue tone for NPCs at this location."""
        if self.danger_rating > 0.7:
            return "whispered"      # NPCs speak quietly
        if self.rumor_density > 0.6:
            return "gossipy"        # NPCs share info freely
        if self.death_count > 0:
            return "somber"         # NPCs are subdued
        if self.activity_level > 0.7:
            return "lively"         # NPCs are animated
        return "neutral"

    def should_npc_avoid(self, npc_fear_level: float) -> bool:
        """Check if an NPC with given fear level should avoid this place."""
        return self.npc_avoidance * npc_fear_level > 0.4

    def to_dict(self) -> dict:
        """Serialize tile memory."""
        return {
            "location": list(self.location),
            "location_name": self.location_name,
            "event_history": self.event_history,
            "event_tags": list(self.event_tags),
            "rumor_density": self.rumor_density,
            "danger_rating": self.danger_rating,
            "activity_level": self.activity_level,
            "crime_rating": self.crime_rating,
            "death_count": self.death_count,
            "npc_avoidance": self.npc_avoidance,
            "npc_curiosity": self.npc_curiosity,
            "mood_modifier": self.mood_modifier,
            "last_event": self.last_event,
            "last_updated": self.last_updated,
            "decay_rate": self.decay_rate
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TileMemory':
        """Deserialize tile memory."""
        data["location"] = tuple(data["location"])
        data["event_tags"] = set(data.get("event_tags", []))
        return cls(**data)


class TileMemoryManager:
    """
    Manages environmental memory across the game world.

    Tracks what has happened at each location and provides
    queries for NPC pathfinding and atmosphere.
    """

    def __init__(self):
        self.tile_memories: dict[tuple[int, int], TileMemory] = {}
        self.location_name_index: dict[str, tuple[int, int]] = {}
        self.current_time: float = 0.0

    def get_or_create(
        self,
        location: tuple[int, int],
        location_name: str = ""
    ) -> TileMemory:
        """Get tile memory, creating if necessary."""
        if location not in self.tile_memories:
            self.tile_memories[location] = TileMemory(
                location=location,
                location_name=location_name
            )
            if location_name:
                self.location_name_index[location_name] = location
        return self.tile_memories[location]

    def get_by_name(self, location_name: str) -> Optional[TileMemory]:
        """Get tile memory by location name."""
        if location_name in self.location_name_index:
            return self.tile_memories.get(self.location_name_index[location_name])
        return None

    def record_event(
        self,
        location: tuple[int, int],
        location_name: str,
        event_id: str,
        event_type: str,
        tags: list[str],
        timestamp: float,
        severity: float = 0.5
    ) -> TileMemory:
        """Record an event at a location."""
        tile_memory = self.get_or_create(location, location_name)
        tile_memory.add_event(event_id, event_type, tags, timestamp, severity)
        return tile_memory

    def update(self, dt: float) -> None:
        """Update all tile memories with decay."""
        self.current_time += dt
        for tile_memory in self.tile_memories.values():
            tile_memory.decay(dt)

    def get_dangerous_locations(self, threshold: float = 0.5) -> list[TileMemory]:
        """Get locations above danger threshold."""
        return [
            tm for tm in self.tile_memories.values()
            if tm.danger_rating >= threshold
        ]

    def get_avoided_locations(self, threshold: float = 0.5) -> list[TileMemory]:
        """Get locations NPCs tend to avoid."""
        return [
            tm for tm in self.tile_memories.values()
            if tm.npc_avoidance >= threshold
        ]

    def get_rumor_hotspots(self, threshold: float = 0.5) -> list[TileMemory]:
        """Get locations with high rumor density."""
        return [
            tm for tm in self.tile_memories.values()
            if tm.rumor_density >= threshold
        ]

    def get_locations_with_deaths(self) -> list[TileMemory]:
        """Get all locations where deaths occurred."""
        return [
            tm for tm in self.tile_memories.values()
            if tm.death_count > 0
        ]

    def modify_path_for_npc(
        self,
        path: list[tuple[int, int]],
        npc_fear_level: float
    ) -> list[tuple[int, int]]:
        """
        Modify an NPC's path to avoid dangerous remembered locations.

        This is a simplified version - real implementation would do
        proper pathfinding with weighted costs.
        """
        modified = []
        for pos in path:
            tile_memory = self.tile_memories.get(pos)
            if tile_memory and tile_memory.should_npc_avoid(npc_fear_level):
                # In a real implementation, would find alternative route
                # For now, just note that NPC is hesitant
                modified.append(pos)  # Still add but could flag as "reluctant"
            else:
                modified.append(pos)
        return modified

    def get_all_hints_at(self, location: tuple[int, int]) -> list[str]:
        """Get all atmospheric hints at a location."""
        tile_memory = self.tile_memories.get(location)
        if tile_memory:
            return tile_memory.get_atmosphere_hints()
        return []

    def to_dict(self) -> dict:
        """Serialize all tile memories."""
        return {
            "tile_memories": {
                f"{k[0]},{k[1]}": v.to_dict()
                for k, v in self.tile_memories.items()
            },
            "location_name_index": {
                k: list(v) for k, v in self.location_name_index.items()
            },
            "current_time": self.current_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TileMemoryManager':
        """Deserialize tile memory manager."""
        manager = cls()
        for key, value in data.get("tile_memories", {}).items():
            x, y = map(int, key.split(","))
            manager.tile_memories[(x, y)] = TileMemory.from_dict(value)
        manager.location_name_index = {
            k: tuple(v)
            for k, v in data.get("location_name_index", {}).items()
        }
        manager.current_time = data.get("current_time", 0.0)
        return manager
