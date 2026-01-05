"""
Tile class for the grid system.

Each tile represents a single cell in the game world with terrain,
environmental properties, and contents.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, TYPE_CHECKING
import time

from .terrain import (
    TerrainType,
    FluidType,
    TerrainModifier,
    get_terrain_properties,
    TERRAIN_PROPERTIES,
)

if TYPE_CHECKING:
    from .entity import Entity


@dataclass(frozen=True)
class Position:
    """3D position in the game world."""
    x: int
    y: int
    z: int = 0  # Ground level = 0, up = positive, down = negative

    def __add__(self, other: 'Position') -> 'Position':
        return Position(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Position') -> 'Position':
        return Position(self.x - other.x, self.y - other.y, self.z - other.z)

    def distance_to(self, other: 'Position') -> float:
        """Calculate Euclidean distance to another position."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return (dx * dx + dy * dy + dz * dz) ** 0.5

    def manhattan_distance(self, other: 'Position') -> int:
        """Calculate Manhattan distance to another position."""
        return abs(self.x - other.x) + abs(self.y - other.y) + abs(self.z - other.z)

    def to_tuple(self) -> tuple[int, int, int]:
        return (self.x, self.y, self.z)

    def to_key(self) -> str:
        """Get string key for dictionary storage."""
        return f"{self.x},{self.y},{self.z}"

    @classmethod
    def from_tuple(cls, t: tuple) -> 'Position':
        if len(t) == 2:
            return cls(t[0], t[1], 0)
        return cls(t[0], t[1], t[2])

    @classmethod
    def from_key(cls, key: str) -> 'Position':
        parts = key.split(',')
        return cls(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)


# Direction constants
DIRECTIONS = {
    "north": Position(0, -1, 0),
    "south": Position(0, 1, 0),
    "east": Position(1, 0, 0),
    "west": Position(-1, 0, 0),
    "up": Position(0, 0, 1),
    "down": Position(0, 0, -1),
    "northeast": Position(1, -1, 0),
    "northwest": Position(-1, -1, 0),
    "southeast": Position(1, 1, 0),
    "southwest": Position(-1, 1, 0),
}


@dataclass
class TileEnvironment:
    """Environmental state of a tile."""
    fluid: Optional[FluidType] = None
    temperature: float = 20.0      # Celsius, -100 to 100
    sound_level: float = 0.0       # 0.0 (silent) to 1.0 (loud)
    light_level: float = 0.5       # 0.0 (dark) to 1.0 (bright)
    moisture: float = 0.0          # 0.0 (dry) to 1.0 (flooded)

    def get_temperature_effect(self) -> str:
        """Get temperature effect category."""
        if self.temperature < -20:
            return "freezing"
        elif self.temperature < 0:
            return "cold"
        elif self.temperature < 30:
            return "comfortable"
        elif self.temperature < 50:
            return "hot"
        else:
            return "extreme"

    def get_moisture_effect(self) -> str:
        """Get moisture effect category."""
        if self.moisture < 0.2:
            return "dry"
        elif self.moisture < 0.5:
            return "normal"
        elif self.moisture < 0.8:
            return "damp"
        else:
            return "flooded"

    def get_light_effect(self) -> str:
        """Get light effect category."""
        if self.light_level < 0.1:
            return "pitch_black"
        elif self.light_level < 0.3:
            return "dim"
        elif self.light_level < 0.7:
            return "normal"
        else:
            return "bright"

    def to_dict(self) -> dict:
        return {
            "fluid": self.fluid.value if self.fluid else None,
            "temperature": self.temperature,
            "sound_level": self.sound_level,
            "light_level": self.light_level,
            "moisture": self.moisture,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TileEnvironment':
        return cls(
            fluid=FluidType(data["fluid"]) if data.get("fluid") else None,
            temperature=data.get("temperature", 20.0),
            sound_level=data.get("sound_level", 0.0),
            light_level=data.get("light_level", 0.5),
            moisture=data.get("moisture", 0.0),
        )


@dataclass
class Tile:
    """
    A single tile in the game world.

    Contains terrain info, environmental state, and references to entities.
    """
    position: Position

    # Core properties
    terrain_type: TerrainType = TerrainType.FLOOR
    height: float = 0.0  # Elevation within the tile

    # Modifiers that affect terrain properties
    modifiers: list[TerrainModifier] = field(default_factory=list)

    # Environmental state
    environment: TileEnvironment = field(default_factory=TileEnvironment)

    # Contents
    entity_ids: list[str] = field(default_factory=list)  # IDs of entities on this tile

    # Feature references (permanent terrain features like walls, doors)
    feature_ids: list[str] = field(default_factory=list)

    # Custom tile data
    custom: dict = field(default_factory=dict)

    # Timestamp for last modification
    last_modified: float = field(default_factory=time.time)

    def __post_init__(self):
        """Initialize computed properties."""
        self._cached_affordances: Optional[set[str]] = None
        self._cached_passable: Optional[bool] = None
        self._cached_opaque: Optional[bool] = None
        self._cached_movement_cost: Optional[float] = None

    def _invalidate_cache(self):
        """Invalidate computed property cache."""
        self._cached_affordances = None
        self._cached_passable = None
        self._cached_opaque = None
        self._cached_movement_cost = None
        self.last_modified = time.time()

    @property
    def passable(self) -> bool:
        """Check if tile is passable (considering modifiers)."""
        if self._cached_passable is not None:
            return self._cached_passable

        # Start with terrain base
        props = get_terrain_properties(self.terrain_type)
        result = props.get("passable", True)

        # Apply modifier overrides
        for modifier in self.modifiers:
            if modifier.passable_override is not None:
                result = modifier.passable_override

        self._cached_passable = result
        return result

    @property
    def opaque(self) -> bool:
        """Check if tile blocks line of sight (considering modifiers)."""
        if self._cached_opaque is not None:
            return self._cached_opaque

        # Start with terrain base
        props = get_terrain_properties(self.terrain_type)
        result = props.get("opaque", False)

        # Apply modifier overrides
        for modifier in self.modifiers:
            if modifier.opaque_override is not None:
                result = modifier.opaque_override

        self._cached_opaque = result
        return result

    @property
    def movement_cost(self) -> float:
        """Get movement cost (considering modifiers)."""
        if self._cached_movement_cost is not None:
            return self._cached_movement_cost

        # Start with terrain base
        props = get_terrain_properties(self.terrain_type)
        cost = props.get("movement_cost", 1.0)

        # Apply modifier multipliers
        for modifier in self.modifiers:
            cost *= modifier.movement_cost_modifier

        # Environmental effects
        if self.environment.moisture > 0.7:
            cost *= 1.5  # Harder to move in water
        if self.environment.light_level < 0.2:
            cost *= 1.2  # Slower in darkness

        self._cached_movement_cost = cost
        return cost

    @property
    def affordances(self) -> list[str]:
        """Get all affordances (terrain + modifiers + environment)."""
        if self._cached_affordances is not None:
            return list(self._cached_affordances)

        # Start with terrain affordances
        props = get_terrain_properties(self.terrain_type)
        result = set(props.get("affordances", []))

        # Apply modifiers
        for modifier in self.modifiers:
            result = modifier.apply_to_affordances(result)

        # Environmental effects on affordances
        if self.environment.moisture > 0.7:
            result.add("slippery")
            result.discard("flammable")
        if self.environment.temperature > 50:
            result.add("dangerous")
        if self.environment.temperature < -10:
            result.add("cold")
            result.add("slippery")
        if self.environment.light_level < 0.1:
            result.add("dark")

        self._cached_affordances = result
        return list(result)

    def has_affordance(self, affordance: str) -> bool:
        """Check if tile has a specific affordance."""
        return affordance in self.affordances

    def add_modifier(self, modifier: TerrainModifier) -> None:
        """Add a terrain modifier."""
        self.modifiers.append(modifier)
        self._invalidate_cache()

    def remove_modifier(self, modifier_type: str) -> bool:
        """Remove a modifier by type. Returns True if removed."""
        for i, mod in enumerate(self.modifiers):
            if mod.type == modifier_type:
                self.modifiers.pop(i)
                self._invalidate_cache()
                return True
        return False

    def has_modifier(self, modifier_type: str) -> bool:
        """Check if tile has a specific modifier."""
        return any(m.type == modifier_type for m in self.modifiers)

    def add_entity(self, entity_id: str) -> None:
        """Add an entity to this tile."""
        if entity_id not in self.entity_ids:
            self.entity_ids.append(entity_id)
            self._invalidate_cache()

    def remove_entity(self, entity_id: str) -> bool:
        """Remove an entity from this tile. Returns True if removed."""
        if entity_id in self.entity_ids:
            self.entity_ids.remove(entity_id)
            self._invalidate_cache()
            return True
        return False

    def has_entity(self, entity_id: str) -> bool:
        """Check if entity is on this tile."""
        return entity_id in self.entity_ids

    def add_feature(self, feature_id: str) -> None:
        """Add a permanent feature to this tile."""
        if feature_id not in self.feature_ids:
            self.feature_ids.append(feature_id)
            self._invalidate_cache()

    def remove_feature(self, feature_id: str) -> bool:
        """Remove a feature from this tile."""
        if feature_id in self.feature_ids:
            self.feature_ids.remove(feature_id)
            self._invalidate_cache()
            return True
        return False

    def is_empty(self) -> bool:
        """Check if tile has no entities or features."""
        return len(self.entity_ids) == 0 and len(self.feature_ids) == 0

    def set_terrain(self, terrain_type: TerrainType) -> None:
        """Change terrain type."""
        self.terrain_type = terrain_type
        self._invalidate_cache()

    def set_environment(self, **kwargs) -> None:
        """Update environmental properties."""
        for key, value in kwargs.items():
            if hasattr(self.environment, key):
                setattr(self.environment, key, value)
        self._invalidate_cache()

    def to_dict(self) -> dict:
        """Serialize tile to dictionary."""
        return {
            "position": self.position.to_tuple(),
            "terrain_type": self.terrain_type.value,
            "height": self.height,
            "modifiers": [m.to_dict() for m in self.modifiers],
            "environment": self.environment.to_dict(),
            "entity_ids": self.entity_ids.copy(),
            "feature_ids": self.feature_ids.copy(),
            "custom": self.custom.copy(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Tile':
        """Deserialize tile from dictionary."""
        tile = cls(
            position=Position.from_tuple(data["position"]),
            terrain_type=TerrainType(data["terrain_type"]),
            height=data.get("height", 0.0),
            environment=TileEnvironment.from_dict(data.get("environment", {})),
            entity_ids=data.get("entity_ids", []),
            feature_ids=data.get("feature_ids", []),
            custom=data.get("custom", {}),
        )
        tile.modifiers = [
            TerrainModifier.from_dict(m) for m in data.get("modifiers", [])
        ]
        return tile

    def clone(self, new_position: Optional[Position] = None) -> 'Tile':
        """Create a copy of this tile."""
        data = self.to_dict()
        if new_position:
            data["position"] = new_position.to_tuple()
        data["entity_ids"] = []  # Don't copy entities
        data["feature_ids"] = []  # Don't copy features
        return Tile.from_dict(data)
