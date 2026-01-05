"""
Terrain types and modifiers for the tile grid system.

Terrain determines base properties and affordances of tiles.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TerrainType(Enum):
    """Types of terrain that can exist on a tile."""
    ROCK = "rock"
    WATER = "water"
    SOIL = "soil"
    METAL = "metal"
    VOID = "void"
    WOOD = "wood"
    GLASS = "glass"
    FLOOR = "floor"        # Generic indoor floor
    GRASS = "grass"        # Natural ground
    SAND = "sand"          # Desert terrain
    ICE = "ice"            # Frozen surface


class FluidType(Enum):
    """Types of fluids that can exist on a tile."""
    WATER = "water"
    LAVA = "lava"
    GAS = "gas"
    OIL = "oil"
    ACID = "acid"


# Default properties for each terrain type
TERRAIN_PROPERTIES = {
    TerrainType.ROCK: {
        "passable": False,
        "opaque": True,
        "movement_cost": float('inf'),
        "affordances": ["climbable", "breakable", "solid", "mineable"],
    },
    TerrainType.WATER: {
        "passable": True,  # Partial - requires swimming
        "opaque": False,
        "movement_cost": 2.0,
        "affordances": ["swimmable", "splashable", "drownable", "drinkable"],
    },
    TerrainType.SOIL: {
        "passable": True,
        "opaque": False,
        "movement_cost": 1.0,
        "affordances": ["diggable", "plantable", "trackable"],
    },
    TerrainType.METAL: {
        "passable": True,
        "opaque": True,
        "movement_cost": 1.0,
        "affordances": ["conductive", "climbable", "resonant", "magnetic"],
    },
    TerrainType.VOID: {
        "passable": False,
        "opaque": False,
        "movement_cost": float('inf'),
        "affordances": ["fallable", "echoing"],
    },
    TerrainType.WOOD: {
        "passable": True,
        "opaque": True,
        "movement_cost": 1.0,
        "affordances": ["flammable", "climbable", "breakable", "carvable"],
    },
    TerrainType.GLASS: {
        "passable": False,
        "opaque": False,  # Partial - transparent
        "movement_cost": float('inf'),
        "affordances": ["breakable", "transparent", "reflective"],
    },
    TerrainType.FLOOR: {
        "passable": True,
        "opaque": False,
        "movement_cost": 1.0,
        "affordances": [],
    },
    TerrainType.GRASS: {
        "passable": True,
        "opaque": False,
        "movement_cost": 1.1,
        "affordances": ["flammable", "trackable", "hideable"],
    },
    TerrainType.SAND: {
        "passable": True,
        "opaque": False,
        "movement_cost": 1.3,
        "affordances": ["diggable", "trackable"],
    },
    TerrainType.ICE: {
        "passable": True,
        "opaque": False,
        "movement_cost": 0.8,  # Fast but slippery
        "affordances": ["slippery", "breakable", "cold"],
    },
}


@dataclass
class TerrainModifier:
    """
    Modifier that affects terrain base properties.

    Examples: wet, frozen, cracked, overgrown, rusted
    """
    type: str
    intensity: float = 1.0  # 0.0 to 1.0
    affects: list[str] = field(default_factory=list)

    # Affordance modifications
    adds_affordances: list[str] = field(default_factory=list)
    removes_affordances: list[str] = field(default_factory=list)

    # Property modifications
    movement_cost_modifier: float = 1.0
    passable_override: Optional[bool] = None
    opaque_override: Optional[bool] = None

    def apply_to_affordances(self, affordances: set[str]) -> set[str]:
        """Apply modifier to a set of affordances."""
        result = affordances.copy()
        result.update(self.adds_affordances)
        result -= set(self.removes_affordances)
        return result

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "intensity": self.intensity,
            "affects": self.affects,
            "adds_affordances": self.adds_affordances,
            "removes_affordances": self.removes_affordances,
            "movement_cost_modifier": self.movement_cost_modifier,
            "passable_override": self.passable_override,
            "opaque_override": self.opaque_override,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TerrainModifier':
        return cls(
            type=data["type"],
            intensity=data.get("intensity", 1.0),
            affects=data.get("affects", []),
            adds_affordances=data.get("adds_affordances", []),
            removes_affordances=data.get("removes_affordances", []),
            movement_cost_modifier=data.get("movement_cost_modifier", 1.0),
            passable_override=data.get("passable_override"),
            opaque_override=data.get("opaque_override"),
        )


# Predefined terrain modifiers
TERRAIN_MODIFIERS = {
    "wet": TerrainModifier(
        type="wet",
        affects=["movement", "flammability"],
        adds_affordances=["slippery", "conductive"],
        removes_affordances=["flammable"],
        movement_cost_modifier=1.2,
    ),
    "frozen": TerrainModifier(
        type="frozen",
        affects=["movement", "passability"],
        adds_affordances=["slippery", "breakable", "cold"],
        removes_affordances=["swimmable", "drownable"],
        movement_cost_modifier=0.9,
    ),
    "cracked": TerrainModifier(
        type="cracked",
        affects=["stability"],
        adds_affordances=["unstable", "breakable"],
        movement_cost_modifier=1.1,
    ),
    "overgrown": TerrainModifier(
        type="overgrown",
        affects=["visibility", "movement"],
        adds_affordances=["hideable", "flammable"],
        movement_cost_modifier=1.3,
    ),
    "rusted": TerrainModifier(
        type="rusted",
        affects=["durability"],
        adds_affordances=["weak", "rough"],
        removes_affordances=["conductive"],
    ),
    "hot": TerrainModifier(
        type="hot",
        affects=["temperature", "safety"],
        adds_affordances=["dangerous", "glowing"],
    ),
    "electrified": TerrainModifier(
        type="electrified",
        affects=["safety"],
        adds_affordances=["dangerous", "conductive", "glowing"],
    ),
    "flooded": TerrainModifier(
        type="flooded",
        affects=["movement", "visibility"],
        adds_affordances=["swimmable", "drownable"],
        removes_affordances=["flammable"],
        movement_cost_modifier=2.0,
    ),
}


def get_terrain_properties(terrain_type: TerrainType) -> dict:
    """Get default properties for a terrain type."""
    return TERRAIN_PROPERTIES.get(terrain_type, {
        "passable": True,
        "opaque": False,
        "movement_cost": 1.0,
        "affordances": [],
    }).copy()


def get_predefined_modifier(modifier_type: str) -> Optional[TerrainModifier]:
    """Get a predefined terrain modifier by type."""
    return TERRAIN_MODIFIERS.get(modifier_type)


def create_modifier(
    modifier_type: str,
    intensity: float = 1.0,
    **overrides
) -> TerrainModifier:
    """Create a terrain modifier, optionally based on a predefined type."""
    base = get_predefined_modifier(modifier_type)
    if base:
        # Copy and modify
        return TerrainModifier(
            type=modifier_type,
            intensity=intensity,
            affects=overrides.get("affects", base.affects),
            adds_affordances=overrides.get("adds_affordances", base.adds_affordances),
            removes_affordances=overrides.get("removes_affordances", base.removes_affordances),
            movement_cost_modifier=overrides.get("movement_cost_modifier", base.movement_cost_modifier),
            passable_override=overrides.get("passable_override", base.passable_override),
            opaque_override=overrides.get("opaque_override", base.opaque_override),
        )
    else:
        return TerrainModifier(type=modifier_type, intensity=intensity, **overrides)
