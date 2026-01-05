"""
Tile events system for the grid.
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Callable, List, TYPE_CHECKING
import time

if TYPE_CHECKING:
    from .tile import Tile
    from .entity import Entity


class TileEventType(Enum):
    """Types of tile events."""
    ENTERED = auto()        # Entity entered the tile
    EXITED = auto()         # Entity exited the tile
    DAMAGED = auto()        # Tile received damage
    FLOODED = auto()        # Tile became flooded
    FROZEN = auto()         # Tile became frozen
    HEATED = auto()         # Tile temperature increased
    LIT = auto()            # Light level changed
    MODIFIED = auto()       # Modifier applied/removed
    ENTITY_ADDED = auto()   # Entity placed on tile
    ENTITY_REMOVED = auto() # Entity removed from tile
    COLLAPSED = auto()      # Tile stability failed
    TRIGGERED = auto()      # Triggerable activated


@dataclass
class TileEvent:
    """
    Represents an event that occurred on a tile.

    Attributes:
        event_type: Type of event
        tile: The tile where event occurred
        cause: Entity that caused the event (if any)
        timestamp: When the event occurred
        data: Additional event data
    """
    event_type: TileEventType
    tile: "Tile"
    cause: Optional["Entity"] = None
    timestamp: float = field(default_factory=time.time)
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize event to dictionary."""
        return {
            "event_type": self.event_type.name,
            "tile_position": self.tile.position.to_tuple(),
            "cause_id": self.cause.id if self.cause else None,
            "timestamp": self.timestamp,
            "data": self.data
        }


# Type alias for event handlers
EventHandler = Callable[["TileEvent"], None]


class TileEventManager:
    """
    Manages tile event subscription and dispatching.
    """

    def __init__(self):
        self._handlers: dict[TileEventType, List[EventHandler]] = {
            event_type: [] for event_type in TileEventType
        }
        self._event_history: List[TileEvent] = []
        self._max_history: int = 1000

    def subscribe(self, event_type: TileEventType, handler: EventHandler) -> None:
        """
        Subscribe to a tile event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event occurs
        """
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: TileEventType, handler: EventHandler) -> bool:
        """
        Unsubscribe from a tile event type.

        Args:
            event_type: Type of event
            handler: Handler to remove

        Returns:
            True if handler was removed
        """
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            return True
        return False

    def emit(self, event: TileEvent) -> None:
        """
        Emit a tile event to all subscribers.

        Args:
            event: Event to emit
        """
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Call handlers
        for handler in self._handlers[event.event_type]:
            try:
                handler(event)
            except Exception:
                # Log error but continue processing
                pass

    def get_history(
        self,
        event_type: Optional[TileEventType] = None,
        limit: int = 100
    ) -> List[TileEvent]:
        """
        Get event history.

        Args:
            event_type: Filter by event type (optional)
            limit: Maximum events to return

        Returns:
            List of events, most recent first
        """
        events = self._event_history.copy()

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events[-limit:][::-1]

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()


# Default event handlers

def on_tile_entered(event: TileEvent) -> None:
    """Handle entity entering a tile."""
    tile = event.tile
    entity = event.cause

    if not entity:
        return

    # Check for triggers
    if "triggerable" in tile.get_affordances():
        # Emit triggered event
        trigger_event = TileEvent(
            event_type=TileEventType.TRIGGERED,
            tile=tile,
            cause=entity,
            data={"trigger_type": "pressure_plate"}
        )
        # This would be emitted through the grid's event manager

    # Notify entities on tile about proximity
    for other_entity in tile.entities:
        if other_entity != entity:
            # Signal proximity to other entities
            pass


def on_tile_damaged(event: TileEvent) -> None:
    """Handle tile taking damage."""
    tile = event.tile
    damage = event.data.get("damage", 0)

    # Check for glass shattering
    from .terrain import TerrainType
    if tile.terrain_type == TerrainType.GLASS and damage > 10:
        # Glass shatters
        tile.passable = True
        tile.add_modifier(
            __import__("shadowengine.grid.terrain", fromlist=["TerrainModifier"]).TerrainModifier(
                type="cracked",
                intensity=1.0
            )
        )

    # Check for collapse
    if tile.stability < (damage / 100):
        # Tile collapses
        pass


def on_tile_flooded(event: TileEvent) -> None:
    """Handle tile becoming flooded."""
    tile = event.tile

    # Update moisture
    tile.environment.moisture = 1.0

    # Add slippery affordance (already handled in get_affordances)
    # Extinguish fires (remove flammable entities)
    pass
