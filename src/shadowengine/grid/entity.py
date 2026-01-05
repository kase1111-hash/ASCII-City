"""
Entity classes for objects that can be placed on tiles.
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .position import Position


class EntityType(Enum):
    """Types of entities that can exist on tiles."""
    CHARACTER = auto()      # NPCs and player
    CREATURE = auto()       # Animals, monsters
    ITEM = auto()           # Collectible objects
    FURNITURE = auto()      # Tables, chairs, etc.
    DECORATION = auto()     # Visual elements
    TRIGGER = auto()        # Buttons, plates, etc.
    LIGHT_SOURCE = auto()   # Lamps, torches, etc.
    CONTAINER = auto()      # Chests, boxes, etc.


class Layer(Enum):
    """Layer for entity placement on tiles."""
    GROUND = 0      # Floor items, rugs, markings
    OBJECT = 1      # Furniture, creatures, characters
    CEILING = 2     # Hanging items, lights, signs


# Maximum size units per layer on a single tile
MAX_LAYER_SIZE = 4


@dataclass
class Entity:
    """
    Base class for tile contents.

    Attributes:
        id: Unique identifier
        name: Display name
        entity_type: Type of entity
        position: Current position in the grid
        size: How much space it occupies (1-4)
        layer: Which layer it occupies
        passable: Whether entities can move through it
        opaque: Whether it blocks line of sight
        own_affordances: Affordances this entity provides
        blocked_affordances: Affordances this entity blocks
        movement_modifiers: Cost modifiers for different terrain types
    """
    id: str
    name: str
    entity_type: EntityType
    position: Optional["Position"] = None
    size: int = 1
    layer: Layer = Layer.OBJECT
    passable: bool = True
    opaque: bool = False
    own_affordances: Set[str] = field(default_factory=set)
    blocked_affordances: Set[str] = field(default_factory=set)
    movement_modifiers: dict = field(default_factory=dict)
    requires_passable: bool = True

    def __post_init__(self):
        """Validate entity values."""
        if not 1 <= self.size <= MAX_LAYER_SIZE:
            raise ValueError(f"Entity size must be between 1 and {MAX_LAYER_SIZE}, got {self.size}")

    def can_be_placed_on(self, terrain_passable: bool) -> bool:
        """Check if entity can be placed based on terrain passability."""
        if self.requires_passable and not terrain_passable:
            return False
        return True

    def get_affordances(self) -> Set[str]:
        """Get affordances this entity provides."""
        return self.own_affordances.copy()

    def blocks_affordance(self, affordance: str) -> bool:
        """Check if entity blocks a specific affordance."""
        return affordance in self.blocked_affordances

    def serialize(self) -> dict:
        """Serialize entity to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type.name,
            "position": self.position.to_tuple() if self.position else None,
            "size": self.size,
            "layer": self.layer.name,
            "passable": self.passable,
            "opaque": self.opaque,
            "own_affordances": list(self.own_affordances),
            "blocked_affordances": list(self.blocked_affordances),
            "movement_modifiers": self.movement_modifiers,
            "requires_passable": self.requires_passable
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Entity":
        """Create entity from dictionary."""
        from .position import Position

        position = None
        if data.get("position"):
            position = Position.from_tuple(tuple(data["position"]))

        return cls(
            id=data["id"],
            name=data["name"],
            entity_type=EntityType[data["entity_type"]],
            position=position,
            size=data.get("size", 1),
            layer=Layer[data.get("layer", "OBJECT")],
            passable=data.get("passable", True),
            opaque=data.get("opaque", False),
            own_affordances=set(data.get("own_affordances", [])),
            blocked_affordances=set(data.get("blocked_affordances", [])),
            movement_modifiers=data.get("movement_modifiers", {}),
            requires_passable=data.get("requires_passable", True)
        )

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


def conflicts(entity1: Entity, entity2: Entity) -> bool:
    """
    Check if two entities conflict when placed on the same tile.

    Returns:
        True if entities conflict
    """
    # Entities on different layers don't conflict
    if entity1.layer != entity2.layer:
        return False

    # Characters always conflict with other characters
    if entity1.entity_type == EntityType.CHARACTER and entity2.entity_type == EntityType.CHARACTER:
        return True

    # Check if either entity is impassable
    if not entity1.passable or not entity2.passable:
        return True

    return False
