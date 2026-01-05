"""
Tile event system for the grid.

Events are emitted when tiles or entities change state,
enabling reactive behaviors and chain reactions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Any
import time


class TileEventType(Enum):
    """Types of tile events."""
    # Movement events
    ENTITY_ENTERED = "entity_entered"
    ENTITY_EXITED = "entity_exited"
    ENTITY_MOVED = "entity_moved"

    # State change events
    TILE_DAMAGED = "tile_damaged"
    TILE_DESTROYED = "tile_destroyed"
    TILE_REPAIRED = "tile_repaired"
    TERRAIN_CHANGED = "terrain_changed"
    MODIFIER_ADDED = "modifier_added"
    MODIFIER_REMOVED = "modifier_removed"

    # Environmental events
    FLOODED = "flooded"
    FROZEN = "frozen"
    HEATED = "heated"
    LIT = "lit"
    DARKENED = "darkened"

    # Interaction events
    TRIGGERED = "triggered"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"

    # Feature events
    FEATURE_ADDED = "feature_added"
    FEATURE_REMOVED = "feature_removed"

    # Custom events
    CUSTOM = "custom"


@dataclass
class TileEvent:
    """
    An event that occurred on a tile.

    Events contain information about what happened,
    who/what caused it, and when.
    """
    type: TileEventType
    tile_position: tuple[int, int, int]  # (x, y, z)
    timestamp: float = field(default_factory=time.time)

    # What caused the event
    cause_id: Optional[str] = None       # Entity ID that caused it
    cause_type: Optional[str] = None     # "entity", "weather", "time", "signal"

    # Additional event data
    data: dict = field(default_factory=dict)

    # For movement events
    from_position: Optional[tuple[int, int, int]] = None
    to_position: Optional[tuple[int, int, int]] = None

    # For damage events
    damage_amount: float = 0.0
    damage_type: str = ""

    def to_dict(self) -> dict:
        """Serialize event to dictionary."""
        return {
            "type": self.type.value,
            "tile_position": self.tile_position,
            "timestamp": self.timestamp,
            "cause_id": self.cause_id,
            "cause_type": self.cause_type,
            "data": self.data.copy(),
            "from_position": self.from_position,
            "to_position": self.to_position,
            "damage_amount": self.damage_amount,
            "damage_type": self.damage_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TileEvent':
        """Deserialize event from dictionary."""
        return cls(
            type=TileEventType(data["type"]),
            tile_position=tuple(data["tile_position"]),
            timestamp=data.get("timestamp", time.time()),
            cause_id=data.get("cause_id"),
            cause_type=data.get("cause_type"),
            data=data.get("data", {}),
            from_position=tuple(data["from_position"]) if data.get("from_position") else None,
            to_position=tuple(data["to_position"]) if data.get("to_position") else None,
            damage_amount=data.get("damage_amount", 0.0),
            damage_type=data.get("damage_type", ""),
        )


# Type alias for event handlers
EventHandler = Callable[[TileEvent], None]


class TileEventBus:
    """
    Event bus for tile events.

    Allows registering handlers for specific event types
    and dispatching events to them.
    """

    def __init__(self):
        # Handlers by event type
        self._handlers: dict[TileEventType, list[EventHandler]] = {}

        # Global handlers (receive all events)
        self._global_handlers: list[EventHandler] = []

        # Event history for debugging/replay
        self._history: list[TileEvent] = []
        self._max_history: int = 1000

        # Statistics
        self.stats = {
            "events_dispatched": 0,
            "handlers_called": 0,
        }

    def subscribe(
        self,
        event_type: TileEventType,
        handler: EventHandler
    ) -> None:
        """Subscribe to a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe to all events."""
        self._global_handlers.append(handler)

    def unsubscribe(
        self,
        event_type: TileEventType,
        handler: EventHandler
    ) -> bool:
        """Unsubscribe from an event type. Returns True if removed."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                return True
            except ValueError:
                pass
        return False

    def unsubscribe_all(self, handler: EventHandler) -> bool:
        """Unsubscribe from global events. Returns True if removed."""
        try:
            self._global_handlers.remove(handler)
            return True
        except ValueError:
            return False

    def dispatch(self, event: TileEvent) -> int:
        """
        Dispatch an event to all registered handlers.

        Returns the number of handlers that were called.
        """
        handlers_called = 0

        # Store in history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # Call type-specific handlers
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    handler(event)
                    handlers_called += 1
                except Exception:
                    pass  # Don't let one handler break others

        # Call global handlers
        for handler in self._global_handlers:
            try:
                handler(event)
                handlers_called += 1
            except Exception:
                pass

        # Update stats
        self.stats["events_dispatched"] += 1
        self.stats["handlers_called"] += handlers_called

        return handlers_called

    def emit_entered(
        self,
        tile_position: tuple[int, int, int],
        entity_id: str,
        from_position: Optional[tuple[int, int, int]] = None
    ) -> TileEvent:
        """Emit an entity entered event."""
        event = TileEvent(
            type=TileEventType.ENTITY_ENTERED,
            tile_position=tile_position,
            cause_id=entity_id,
            cause_type="entity",
            from_position=from_position,
            to_position=tile_position,
        )
        self.dispatch(event)
        return event

    def emit_exited(
        self,
        tile_position: tuple[int, int, int],
        entity_id: str,
        to_position: Optional[tuple[int, int, int]] = None
    ) -> TileEvent:
        """Emit an entity exited event."""
        event = TileEvent(
            type=TileEventType.ENTITY_EXITED,
            tile_position=tile_position,
            cause_id=entity_id,
            cause_type="entity",
            from_position=tile_position,
            to_position=to_position,
        )
        self.dispatch(event)
        return event

    def emit_damaged(
        self,
        tile_position: tuple[int, int, int],
        damage_amount: float,
        damage_type: str = "physical",
        cause_id: Optional[str] = None
    ) -> TileEvent:
        """Emit a tile damaged event."""
        event = TileEvent(
            type=TileEventType.TILE_DAMAGED,
            tile_position=tile_position,
            cause_id=cause_id,
            cause_type="entity" if cause_id else None,
            damage_amount=damage_amount,
            damage_type=damage_type,
        )
        self.dispatch(event)
        return event

    def emit_triggered(
        self,
        tile_position: tuple[int, int, int],
        trigger_id: str,
        cause_id: Optional[str] = None,
        data: Optional[dict] = None
    ) -> TileEvent:
        """Emit a trigger activated event."""
        event = TileEvent(
            type=TileEventType.TRIGGERED,
            tile_position=tile_position,
            cause_id=cause_id,
            cause_type="entity" if cause_id else None,
            data={"trigger_id": trigger_id, **(data or {})},
        )
        self.dispatch(event)
        return event

    def emit_custom(
        self,
        tile_position: tuple[int, int, int],
        event_name: str,
        data: Optional[dict] = None,
        cause_id: Optional[str] = None
    ) -> TileEvent:
        """Emit a custom event."""
        event = TileEvent(
            type=TileEventType.CUSTOM,
            tile_position=tile_position,
            cause_id=cause_id,
            data={"event_name": event_name, **(data or {})},
        )
        self.dispatch(event)
        return event

    def get_history(
        self,
        event_type: Optional[TileEventType] = None,
        tile_position: Optional[tuple[int, int, int]] = None,
        limit: int = 100
    ) -> list[TileEvent]:
        """Get event history, optionally filtered."""
        result = self._history

        if event_type:
            result = [e for e in result if e.type == event_type]

        if tile_position:
            result = [e for e in result if e.tile_position == tile_position]

        return result[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()

    def get_stats(self) -> dict:
        """Get event bus statistics."""
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = {
            "events_dispatched": 0,
            "handlers_called": 0,
        }


# Factory functions for common events

def create_movement_event(
    entity_id: str,
    from_pos: tuple[int, int, int],
    to_pos: tuple[int, int, int]
) -> TileEvent:
    """Create a movement event."""
    return TileEvent(
        type=TileEventType.ENTITY_MOVED,
        tile_position=to_pos,
        cause_id=entity_id,
        cause_type="entity",
        from_position=from_pos,
        to_position=to_pos,
    )


def create_damage_event(
    tile_pos: tuple[int, int, int],
    amount: float,
    damage_type: str = "physical",
    source_id: Optional[str] = None
) -> TileEvent:
    """Create a damage event."""
    return TileEvent(
        type=TileEventType.TILE_DAMAGED,
        tile_position=tile_pos,
        cause_id=source_id,
        damage_amount=amount,
        damage_type=damage_type,
    )


def create_environmental_event(
    tile_pos: tuple[int, int, int],
    event_type: TileEventType,
    intensity: float = 1.0,
    source: str = "environment"
) -> TileEvent:
    """Create an environmental event."""
    return TileEvent(
        type=event_type,
        tile_position=tile_pos,
        cause_type=source,
        data={"intensity": intensity},
    )
