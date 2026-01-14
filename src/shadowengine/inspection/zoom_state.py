"""
ZoomState - Persistent zoom state tracking per object.

Tracks what zoom level has been reached for each object,
what has been discovered, and inspection history.
"""

from dataclasses import dataclass, field
from typing import Optional, Any

from .zoom_level import ZoomLevel


@dataclass
class ZoomHistory:
    """Record of a zoom action."""
    timestamp: float
    object_id: str
    from_level: ZoomLevel
    to_level: ZoomLevel
    tool_used: Optional[str] = None
    discoveries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "timestamp": self.timestamp,
            "object_id": self.object_id,
            "from_level": self.from_level.value,
            "to_level": self.to_level.value,
            "tool_used": self.tool_used,
            "discoveries": self.discoveries
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ZoomHistory':
        """Deserialize from dictionary."""
        return cls(
            timestamp=data["timestamp"],
            object_id=data["object_id"],
            from_level=ZoomLevel(data["from_level"]),
            to_level=ZoomLevel(data["to_level"]),
            tool_used=data.get("tool_used"),
            discoveries=data.get("discoveries", [])
        )


@dataclass
class ZoomState:
    """
    Zoom state for a single object.

    Tracks:
    - Current zoom level
    - Maximum zoom level reached
    - What has been discovered
    - When it was last inspected
    """
    object_id: str
    current_level: ZoomLevel = ZoomLevel.COARSE
    max_level_reached: ZoomLevel = ZoomLevel.COARSE

    # Discovery tracking
    discovered_facts: set[str] = field(default_factory=set)
    discovered_items: set[str] = field(default_factory=set)
    discovered_hotspots: set[str] = field(default_factory=set)

    # Timestamps
    first_inspected: Optional[float] = None
    last_inspected: Optional[float] = None
    inspection_count: int = 0

    # Tool tracking
    tools_used: set[str] = field(default_factory=set)

    def record_inspection(
        self,
        zoom_level: ZoomLevel,
        timestamp: float,
        tool_used: Optional[str] = None,
        discoveries: dict[str, list[str]] = None
    ) -> list[str]:
        """
        Record an inspection and return newly discovered items.

        Returns list of all new discoveries.
        """
        new_discoveries = []

        # Update timing
        if self.first_inspected is None:
            self.first_inspected = timestamp
        self.last_inspected = timestamp
        self.inspection_count += 1

        # Update zoom levels
        self.current_level = zoom_level
        if zoom_level.value > self.max_level_reached.value:
            self.max_level_reached = zoom_level

        # Track tool
        if tool_used:
            self.tools_used.add(tool_used)

        # Process discoveries
        if discoveries:
            for fact in discoveries.get("facts", []):
                if fact not in self.discovered_facts:
                    self.discovered_facts.add(fact)
                    new_discoveries.append(f"fact:{fact}")

            for item in discoveries.get("items", []):
                if item not in self.discovered_items:
                    self.discovered_items.add(item)
                    new_discoveries.append(f"item:{item}")

            for hotspot in discoveries.get("hotspots", []):
                if hotspot not in self.discovered_hotspots:
                    self.discovered_hotspots.add(hotspot)
                    new_discoveries.append(f"hotspot:{hotspot}")

        return new_discoveries

    def has_discovered(self, discovery_type: str, discovery_id: str) -> bool:
        """Check if something has been discovered."""
        if discovery_type == "fact":
            return discovery_id in self.discovered_facts
        elif discovery_type == "item":
            return discovery_id in self.discovered_items
        elif discovery_type == "hotspot":
            return discovery_id in self.discovered_hotspots
        return False

    def is_first_time_at_level(self, zoom_level: ZoomLevel) -> bool:
        """Check if this is the first time reaching this zoom level."""
        return zoom_level.value > self.max_level_reached.value

    def get_time_since_last_inspection(self, current_time: float) -> Optional[float]:
        """Get time since last inspection."""
        if self.last_inspected is None:
            return None
        return current_time - self.last_inspected

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "object_id": self.object_id,
            "current_level": self.current_level.value,
            "max_level_reached": self.max_level_reached.value,
            "discovered_facts": list(self.discovered_facts),
            "discovered_items": list(self.discovered_items),
            "discovered_hotspots": list(self.discovered_hotspots),
            "first_inspected": self.first_inspected,
            "last_inspected": self.last_inspected,
            "inspection_count": self.inspection_count,
            "tools_used": list(self.tools_used)
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ZoomState':
        """Deserialize from dictionary."""
        return cls(
            object_id=data["object_id"],
            current_level=ZoomLevel(data["current_level"]),
            max_level_reached=ZoomLevel(data["max_level_reached"]),
            discovered_facts=set(data.get("discovered_facts", [])),
            discovered_items=set(data.get("discovered_items", [])),
            discovered_hotspots=set(data.get("discovered_hotspots", [])),
            first_inspected=data.get("first_inspected"),
            last_inspected=data.get("last_inspected"),
            inspection_count=data.get("inspection_count", 0),
            tools_used=set(data.get("tools_used", []))
        )


class ZoomStateManager:
    """
    Manages zoom state for all inspectable objects.

    Provides a central registry for tracking inspection progress
    across all objects in the game.
    """

    def __init__(self):
        self.states: dict[str, ZoomState] = {}
        self.history: list[ZoomHistory] = []
        self.current_time: float = 0.0

    def get_state(self, object_id: str) -> ZoomState:
        """Get or create zoom state for an object."""
        if object_id not in self.states:
            self.states[object_id] = ZoomState(object_id=object_id)
        return self.states[object_id]

    def has_state(self, object_id: str) -> bool:
        """Check if we have state for an object."""
        return object_id in self.states

    def get_current_zoom(self, object_id: str) -> ZoomLevel:
        """Get current zoom level for an object."""
        if object_id not in self.states:
            return ZoomLevel.COARSE
        return self.states[object_id].current_level

    def get_max_zoom_reached(self, object_id: str) -> ZoomLevel:
        """Get maximum zoom level reached for an object."""
        if object_id not in self.states:
            return ZoomLevel.COARSE
        return self.states[object_id].max_level_reached

    def record_zoom(
        self,
        object_id: str,
        new_level: ZoomLevel,
        tool_used: Optional[str] = None,
        discoveries: dict[str, list[str]] = None
    ) -> list[str]:
        """
        Record a zoom action and return new discoveries.

        Returns list of newly discovered items.
        """
        state = self.get_state(object_id)
        old_level = state.current_level

        # Record in state
        new_discoveries = state.record_inspection(
            zoom_level=new_level,
            timestamp=self.current_time,
            tool_used=tool_used,
            discoveries=discoveries
        )

        # Add to history
        self.history.append(ZoomHistory(
            timestamp=self.current_time,
            object_id=object_id,
            from_level=old_level,
            to_level=new_level,
            tool_used=tool_used,
            discoveries=new_discoveries
        ))

        return new_discoveries

    def zoom_in(self, object_id: str, tool_used: Optional[str] = None) -> Optional[ZoomLevel]:
        """
        Zoom in one level on an object.

        Returns the new zoom level, or None if already at max.
        """
        state = self.get_state(object_id)

        if not state.current_level.can_zoom_in():
            return None

        new_level = state.current_level.zoom_in()
        self.record_zoom(object_id, new_level, tool_used)

        return new_level

    def zoom_out(self, object_id: str) -> Optional[ZoomLevel]:
        """
        Zoom out one level on an object.

        Returns the new zoom level, or None if already at min.
        """
        state = self.get_state(object_id)

        if not state.current_level.can_zoom_out():
            return None

        new_level = state.current_level.zoom_out()
        self.record_zoom(object_id, new_level)

        return new_level

    def reset_zoom(self, object_id: str) -> ZoomLevel:
        """Reset zoom to coarse level."""
        self.record_zoom(object_id, ZoomLevel.COARSE)
        return ZoomLevel.COARSE

    def set_time(self, time: float) -> None:
        """Update current time."""
        self.current_time = time

    def advance_time(self, dt: float) -> None:
        """Advance time by delta."""
        self.current_time += dt

    def get_recently_inspected(
        self,
        time_window: float,
        limit: int = 10
    ) -> list[str]:
        """Get objects inspected within a time window."""
        threshold = self.current_time - time_window
        recent = [
            (obj_id, state.last_inspected)
            for obj_id, state in self.states.items()
            if state.last_inspected and state.last_inspected > threshold
        ]
        recent.sort(key=lambda x: x[1], reverse=True)
        return [obj_id for obj_id, _ in recent[:limit]]

    def get_fully_inspected(self) -> list[str]:
        """Get objects that have been inspected at all zoom levels."""
        return [
            obj_id for obj_id, state in self.states.items()
            if state.max_level_reached == ZoomLevel.FINE
        ]

    def get_never_inspected_beyond_coarse(self) -> list[str]:
        """Get objects only inspected at coarse level."""
        return [
            obj_id for obj_id, state in self.states.items()
            if state.max_level_reached == ZoomLevel.COARSE
        ]

    def get_all_discoveries(self) -> dict[str, set[str]]:
        """Get all discoveries across all objects."""
        facts = set()
        items = set()
        hotspots = set()

        for state in self.states.values():
            facts.update(state.discovered_facts)
            items.update(state.discovered_items)
            hotspots.update(state.discovered_hotspots)

        return {
            "facts": facts,
            "items": items,
            "hotspots": hotspots
        }

    def get_inspection_statistics(self) -> dict[str, Any]:
        """Get statistics about inspections."""
        total_inspections = sum(s.inspection_count for s in self.states.values())
        objects_inspected = len(self.states)
        fully_inspected = len(self.get_fully_inspected())

        zoom_distribution = {
            ZoomLevel.COARSE: 0,
            ZoomLevel.MEDIUM: 0,
            ZoomLevel.FINE: 0
        }
        for state in self.states.values():
            zoom_distribution[state.max_level_reached] += 1

        all_discoveries = self.get_all_discoveries()

        return {
            "total_inspections": total_inspections,
            "objects_inspected": objects_inspected,
            "fully_inspected": fully_inspected,
            "zoom_distribution": {k.name: v for k, v in zoom_distribution.items()},
            "total_facts_discovered": len(all_discoveries["facts"]),
            "total_items_discovered": len(all_discoveries["items"]),
            "total_hotspots_discovered": len(all_discoveries["hotspots"]),
            "unique_tools_used": len(set().union(*(s.tools_used for s in self.states.values())))
        }

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "states": {k: v.to_dict() for k, v in self.states.items()},
            "history": [h.to_dict() for h in self.history],
            "current_time": self.current_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ZoomStateManager':
        """Deserialize from dictionary."""
        manager = cls()
        manager.states = {
            k: ZoomState.from_dict(v)
            for k, v in data.get("states", {}).items()
        }
        manager.history = [
            ZoomHistory.from_dict(h)
            for h in data.get("history", [])
        ]
        manager.current_time = data.get("current_time", 0.0)
        return manager
