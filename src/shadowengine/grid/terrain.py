"""
Terrain types and modifiers for the tile grid system.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Set


class TerrainType(Enum):
    """Types of terrain that can exist on a tile."""
    ROCK = auto()
    WATER = auto()
    SOIL = auto()
    METAL = auto()
    VOID = auto()
    WOOD = auto()
    GLASS = auto()

    def get_default_properties(self) -> dict:
        """Get default properties for this terrain type."""
        return TERRAIN_DEFAULTS.get(self, {
            "passable": True,
            "opaque": False,
            "affordances": set(),
            "movement_cost": 1.0
        })

    def is_passable_by_default(self) -> bool:
        """Check if this terrain is passable by default."""
        return self.get_default_properties().get("passable", True)

    def is_opaque_by_default(self) -> bool:
        """Check if this terrain blocks line of sight by default."""
        return self.get_default_properties().get("opaque", False)

    def get_default_affordances(self) -> Set[str]:
        """Get default affordances for this terrain type."""
        return self.get_default_properties().get("affordances", set()).copy()


# Default terrain properties
TERRAIN_DEFAULTS: dict[TerrainType, dict] = {
    TerrainType.ROCK: {
        "passable": False,
        "opaque": True,
        "affordances": {"climbable", "breakable", "solid", "mineable"},
        "movement_cost": 999.0  # Impassable
    },
    TerrainType.WATER: {
        "passable": True,  # Partial - requires swimming
        "opaque": False,
        "affordances": {"swimmable", "splashable", "drownable"},
        "movement_cost": 2.0
    },
    TerrainType.SOIL: {
        "passable": True,
        "opaque": False,
        "affordances": {"diggable", "plantable", "trackable"},
        "movement_cost": 1.0
    },
    TerrainType.METAL: {
        "passable": True,
        "opaque": True,
        "affordances": {"conductive", "climbable", "resonant"},
        "movement_cost": 1.0
    },
    TerrainType.VOID: {
        "passable": False,
        "opaque": False,
        "affordances": {"fallable", "echoing"},
        "movement_cost": 999.0  # Impassable
    },
    TerrainType.WOOD: {
        "passable": True,
        "opaque": True,
        "affordances": {"flammable", "climbable", "breakable"},
        "movement_cost": 1.0
    },
    TerrainType.GLASS: {
        "passable": False,
        "opaque": False,  # Partial - transparent but can block
        "affordances": {"breakable", "transparent", "reflective"},
        "movement_cost": 999.0  # Impassable
    }
}

# Movement cost multipliers by terrain type
TERRAIN_COST: dict[TerrainType, float] = {
    TerrainType.ROCK: 999.0,  # Impassable
    TerrainType.WATER: 2.0,   # Slow
    TerrainType.SOIL: 1.0,    # Normal
    TerrainType.METAL: 1.0,   # Normal
    TerrainType.VOID: 999.0,  # Impassable
    TerrainType.WOOD: 1.0,    # Normal
    TerrainType.GLASS: 999.0  # Impassable
}


class FluidType(Enum):
    """Types of fluid that can be present on a tile."""
    NONE = auto()
    WATER = auto()
    LAVA = auto()
    GAS = auto()
    OIL = auto()
    ACID = auto()

    def get_properties(self) -> dict:
        """Get properties for this fluid type."""
        return FLUID_PROPERTIES.get(self, {
            "dangerous": False,
            "movement_modifier": 1.0,
            "visibility_modifier": 1.0
        })


FLUID_PROPERTIES: dict[FluidType, dict] = {
    FluidType.NONE: {
        "dangerous": False,
        "movement_modifier": 1.0,
        "visibility_modifier": 1.0
    },
    FluidType.WATER: {
        "dangerous": False,
        "movement_modifier": 1.5,
        "visibility_modifier": 0.8
    },
    FluidType.LAVA: {
        "dangerous": True,
        "movement_modifier": 3.0,
        "visibility_modifier": 0.5,
        "damage_per_turn": 50
    },
    FluidType.GAS: {
        "dangerous": True,
        "movement_modifier": 1.0,
        "visibility_modifier": 0.3
    },
    FluidType.OIL: {
        "dangerous": False,
        "movement_modifier": 1.2,
        "visibility_modifier": 0.7,
        "flammable": True
    },
    FluidType.ACID: {
        "dangerous": True,
        "movement_modifier": 1.5,
        "visibility_modifier": 0.6,
        "damage_per_turn": 20
    }
}


@dataclass
class TerrainModifier:
    """
    A modifier that affects terrain properties.

    Attributes:
        type: The type of modifier (wet, frozen, cracked, overgrown)
        intensity: How strong the modifier is (0.0 to 1.0)
        affects: Which properties are modified
    """
    type: str
    intensity: float = 1.0
    affects: Set[str] = field(default_factory=set)

    def __post_init__(self):
        """Validate modifier values."""
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(f"Intensity must be between 0.0 and 1.0, got {self.intensity}")

        valid_types = {"wet", "frozen", "cracked", "overgrown", "scorched", "rusty", "mossy", "collapsed"}
        if self.type not in valid_types:
            raise ValueError(f"Invalid modifier type: {self.type}. Must be one of {valid_types}")

        # Set default affects based on type if not provided
        if not self.affects:
            self.affects = MODIFIER_DEFAULTS.get(self.type, {}).get("affects", set())

    def get_effects(self) -> dict:
        """Get the effects this modifier applies."""
        base_effects = MODIFIER_DEFAULTS.get(self.type, {})
        # Scale effects by intensity
        effects = {}
        for key, value in base_effects.items():
            if key == "affects":
                effects[key] = value
            elif isinstance(value, (int, float)):
                effects[key] = value * self.intensity
            else:
                effects[key] = value
        return effects

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "type": self.type,
            "intensity": self.intensity,
            "affects": list(self.affects)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TerrainModifier":
        """Create from dictionary."""
        return cls(
            type=data["type"],
            intensity=data.get("intensity", 1.0),
            affects=set(data.get("affects", []))
        )


# Default effects for modifier types
MODIFIER_DEFAULTS: dict[str, dict] = {
    "wet": {
        "affects": {"passable", "affordances"},
        "adds_affordances": {"slippery"},
        "removes_affordances": set(),
        "movement_cost_modifier": 1.2
    },
    "frozen": {
        "affects": {"passable", "affordances"},
        "adds_affordances": {"slippery", "breakable"},
        "removes_affordances": {"swimmable", "drownable"},
        "movement_cost_modifier": 1.3,
        "makes_passable": True  # Frozen water becomes passable
    },
    "cracked": {
        "affects": {"stability", "affordances"},
        "adds_affordances": {"unstable", "fallable"},
        "removes_affordances": set(),
        "stability_reduction": 0.5
    },
    "overgrown": {
        "affects": {"visibility", "affordances"},
        "adds_affordances": {"hideable", "searchable"},
        "removes_affordances": set(),
        "visibility_modifier": 0.7
    },
    "scorched": {
        "affects": {"affordances"},
        "adds_affordances": {"damaged", "ashy"},
        "removes_affordances": {"flammable", "plantable"},
        "movement_cost_modifier": 1.1
    },
    "rusty": {
        "affects": {"affordances", "stability"},
        "adds_affordances": {"damaged", "breakable"},
        "removes_affordances": {"conductive"},
        "stability_reduction": 0.3
    },
    "mossy": {
        "affects": {"affordances", "visibility"},
        "adds_affordances": {"slippery", "hideable"},
        "removes_affordances": set(),
        "movement_cost_modifier": 1.1
    }
}
