"""
Entity class for tile contents.

Entities are objects, creatures, or items that exist on tiles
and can be interacted with via behavioral circuits.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any, TYPE_CHECKING
import time
import uuid

if TYPE_CHECKING:
    from ..circuits.circuit import BehaviorCircuit
    from .tile import Position


class Layer(Enum):
    """Vertical layer within a tile."""
    GROUND = 0    # Floor items, rugs, markings
    OBJECT = 1    # Furniture, creatures, characters
    CEILING = 2   # Hanging items, lights, signs


class EntityType(Enum):
    """Categories of entities."""
    ITEM = "item"           # Collectible objects
    FURNITURE = "furniture" # Fixed objects (tables, chairs)
    CREATURE = "creature"   # Living beings
    CHARACTER = "character" # NPCs and player
    FEATURE = "feature"     # Permanent terrain features (doors, switches)
    EFFECT = "effect"       # Temporary visual effects


@dataclass
class Size:
    """Size of an entity in tile units."""
    width: float = 1.0   # X dimension
    height: float = 1.0  # Y dimension (vertical)
    depth: float = 1.0   # Z dimension (depth into tile)

    def volume(self) -> float:
        """Calculate volume."""
        return self.width * self.height * self.depth

    def to_tuple(self) -> tuple[float, float, float]:
        return (self.width, self.height, self.depth)

    @classmethod
    def from_tuple(cls, t: tuple) -> 'Size':
        return cls(t[0], t[1], t[2] if len(t) > 2 else 1.0)


# Maximum size allowed per layer on a tile
MAX_LAYER_SIZE = 4.0


@dataclass
class Entity:
    """
    Base class for all entities that can exist on tiles.

    Entities have a behavioral circuit for interaction,
    a position, size, and layer placement.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""

    # Type and classification
    entity_type: EntityType = EntityType.ITEM
    layer: Layer = Layer.OBJECT

    # Spatial properties
    size: Size = field(default_factory=Size)

    # Movement requirements
    requires_passable: bool = True  # Needs passable tile to exist
    blocks_movement: bool = False   # Blocks other entities from entering

    # Affordances
    own_affordances: list[str] = field(default_factory=list)
    blocked_affordances: list[str] = field(default_factory=list)

    # Circuit reference (ID, not the circuit itself)
    circuit_id: Optional[str] = None

    # Movement modifiers by terrain type
    movement_modifiers: dict[str, float] = field(default_factory=dict)

    # Custom entity data
    custom: dict = field(default_factory=dict)

    # Timestamps
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

    def get_effective_affordances(self, tile_affordances: list[str]) -> list[str]:
        """
        Calculate effective affordances combining tile and entity.

        Entity can add to or block tile affordances.
        """
        result = set(tile_affordances)
        result.update(self.own_affordances)
        result -= set(self.blocked_affordances)
        return list(result)

    def has_affordance(self, affordance: str) -> bool:
        """Check if entity has a specific affordance."""
        return affordance in self.own_affordances

    def blocks_affordance(self, affordance: str) -> bool:
        """Check if entity blocks an affordance."""
        return affordance in self.blocked_affordances

    def add_affordance(self, affordance: str) -> None:
        """Add an affordance."""
        if affordance not in self.own_affordances:
            self.own_affordances.append(affordance)
            self.last_updated = time.time()

    def remove_affordance(self, affordance: str) -> None:
        """Remove an affordance."""
        if affordance in self.own_affordances:
            self.own_affordances.remove(affordance)
            self.last_updated = time.time()

    def block_affordance(self, affordance: str) -> None:
        """Block an affordance from being inherited."""
        if affordance not in self.blocked_affordances:
            self.blocked_affordances.append(affordance)
            self.last_updated = time.time()

    def unblock_affordance(self, affordance: str) -> None:
        """Unblock an affordance."""
        if affordance in self.blocked_affordances:
            self.blocked_affordances.remove(affordance)
            self.last_updated = time.time()

    def get_movement_modifier(self, terrain_type: str) -> float:
        """Get movement modifier for a terrain type."""
        return self.movement_modifiers.get(terrain_type, 1.0)

    def conflicts_with(self, other: 'Entity') -> bool:
        """Check if this entity conflicts with another on the same tile."""
        # Same layer, check size
        if self.layer == other.layer:
            # Both block movement = conflict
            if self.blocks_movement and other.blocks_movement:
                return True
        return False

    def to_dict(self) -> dict:
        """Serialize entity to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "entity_type": self.entity_type.value,
            "layer": self.layer.value,
            "size": self.size.to_tuple(),
            "requires_passable": self.requires_passable,
            "blocks_movement": self.blocks_movement,
            "own_affordances": self.own_affordances.copy(),
            "blocked_affordances": self.blocked_affordances.copy(),
            "circuit_id": self.circuit_id,
            "movement_modifiers": self.movement_modifiers.copy(),
            "custom": self.custom.copy(),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Entity':
        """Deserialize entity from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            description=data.get("description", ""),
            entity_type=EntityType(data.get("entity_type", "item")),
            layer=Layer(data.get("layer", 1)),
            size=Size.from_tuple(data.get("size", (1.0, 1.0, 1.0))),
            requires_passable=data.get("requires_passable", True),
            blocks_movement=data.get("blocks_movement", False),
            own_affordances=data.get("own_affordances", []),
            blocked_affordances=data.get("blocked_affordances", []),
            circuit_id=data.get("circuit_id"),
            movement_modifiers=data.get("movement_modifiers", {}),
            custom=data.get("custom", {}),
            created_at=data.get("created_at", time.time()),
        )


# Factory functions for common entity types

def create_item(
    name: str,
    description: str = "",
    affordances: Optional[list[str]] = None,
    **kwargs
) -> Entity:
    """Create a collectible item entity."""
    return Entity(
        name=name,
        description=description,
        entity_type=EntityType.ITEM,
        layer=Layer.GROUND,
        size=Size(0.5, 0.5, 0.5),
        blocks_movement=False,
        own_affordances=affordances or ["collectible", "usable", "droppable"],
        **kwargs
    )


def create_furniture(
    name: str,
    description: str = "",
    blocks: bool = True,
    affordances: Optional[list[str]] = None,
    **kwargs
) -> Entity:
    """Create a furniture entity."""
    return Entity(
        name=name,
        description=description,
        entity_type=EntityType.FURNITURE,
        layer=Layer.OBJECT,
        size=Size(1.0, 1.0, 1.0),
        blocks_movement=blocks,
        own_affordances=affordances or ["usable"],
        **kwargs
    )


def create_creature(
    name: str,
    description: str = "",
    affordances: Optional[list[str]] = None,
    **kwargs
) -> Entity:
    """Create a creature entity."""
    return Entity(
        name=name,
        description=description,
        entity_type=EntityType.CREATURE,
        layer=Layer.OBJECT,
        size=Size(1.0, 1.0, 1.0),
        blocks_movement=True,
        own_affordances=affordances or ["talkable", "fightable", "observable"],
        **kwargs
    )


def create_feature(
    name: str,
    description: str = "",
    blocks: bool = False,
    affordances: Optional[list[str]] = None,
    **kwargs
) -> Entity:
    """Create a permanent terrain feature entity."""
    return Entity(
        name=name,
        description=description,
        entity_type=EntityType.FEATURE,
        layer=Layer.OBJECT,
        requires_passable=False,
        blocks_movement=blocks,
        own_affordances=affordances or [],
        **kwargs
    )
