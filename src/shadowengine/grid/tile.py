"""
Tile class representing a single cell in the grid.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Set, List, TYPE_CHECKING

from .position import Position
from .terrain import TerrainType, TerrainModifier, FluidType, MODIFIER_DEFAULTS
from .entity import Entity, Layer, MAX_LAYER_SIZE, conflicts

if TYPE_CHECKING:
    pass


@dataclass
class TileEnvironment:
    """
    Environmental properties of a tile.

    Attributes:
        fluid: Type of fluid present (None if no fluid)
        temperature: Temperature scale (-100 to 100)
        sound_level: Ambient noise level (0.0 to 1.0)
        light_level: Light level (0.0 to 1.0, 0=dark, 1=bright)
        moisture: Moisture level (0.0 to 1.0, 0=dry, 1=flooded)
    """
    fluid: FluidType = FluidType.NONE
    temperature: float = 20.0  # Room temperature
    sound_level: float = 0.0
    light_level: float = 0.5
    moisture: float = 0.3

    def __post_init__(self):
        """Validate environment values."""
        if not -100.0 <= self.temperature <= 100.0:
            raise ValueError(f"Temperature must be between -100 and 100, got {self.temperature}")
        if not 0.0 <= self.sound_level <= 1.0:
            raise ValueError(f"Sound level must be between 0.0 and 1.0, got {self.sound_level}")
        if not 0.0 <= self.light_level <= 1.0:
            raise ValueError(f"Light level must be between 0.0 and 1.0, got {self.light_level}")
        if not 0.0 <= self.moisture <= 1.0:
            raise ValueError(f"Moisture must be between 0.0 and 1.0, got {self.moisture}")

    def get_temperature_effect(self) -> str:
        """Get the temperature effect category."""
        temp = self.temperature
        if temp < -20:
            return "freezing"
        elif temp < 0:
            return "cold"
        elif temp < 30:
            return "comfortable"
        elif temp < 50:
            return "hot"
        else:
            return "extreme"

    def get_moisture_effect(self) -> str:
        """Get the moisture effect category."""
        if self.moisture < 0.2:
            return "dry"
        elif self.moisture < 0.5:
            return "normal"
        elif self.moisture < 0.8:
            return "damp"
        else:
            return "flooded"

    def get_light_effect(self) -> str:
        """Get the light effect category."""
        if self.light_level < 0.1:
            return "pitch_black"
        elif self.light_level < 0.3:
            return "dim"
        elif self.light_level < 0.7:
            return "normal"
        else:
            return "bright"

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "fluid": self.fluid.name,
            "temperature": self.temperature,
            "sound_level": self.sound_level,
            "light_level": self.light_level,
            "moisture": self.moisture
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TileEnvironment":
        """Create from dictionary."""
        return cls(
            fluid=FluidType[data.get("fluid", "NONE")],
            temperature=data.get("temperature", 20.0),
            sound_level=data.get("sound_level", 0.0),
            light_level=data.get("light_level", 0.5),
            moisture=data.get("moisture", 0.3)
        )


@dataclass
class Tile:
    """
    Represents a single tile in the grid.

    A tile contains terrain information, environmental data,
    entities, and affordances.

    Attributes:
        position: (x, y, z) coordinates
        terrain_type: Type of terrain
        passable: Whether entities can traverse
        opaque: Whether it blocks line of sight
        height: Z-level elevation within tile
        entities: Objects, creatures, items on the tile
        features: Permanent terrain features
        environment: Environmental properties
        modifiers: Terrain modifiers applied
    """
    position: Position
    terrain_type: TerrainType = TerrainType.SOIL
    passable: Optional[bool] = None  # None means use terrain default
    opaque: Optional[bool] = None    # None means use terrain default
    height: float = 0.0
    entities: List[Entity] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    environment: TileEnvironment = field(default_factory=TileEnvironment)
    modifiers: List[TerrainModifier] = field(default_factory=list)
    stability: float = 1.0  # 0.0 to 1.0, structural integrity

    def __post_init__(self):
        """Initialize tile with terrain defaults if not specified."""
        defaults = self.terrain_type.get_default_properties()

        if self.passable is None:
            self.passable = defaults.get("passable", True)
        if self.opaque is None:
            self.opaque = defaults.get("opaque", False)

    def is_passable(self) -> bool:
        """Check if tile is currently passable, considering modifiers."""
        base_passable = self.passable

        # Check modifiers
        for modifier in self.modifiers:
            effects = modifier.get_effects()
            if effects.get("makes_passable"):
                base_passable = True

        # Check environmental effects
        if self.environment.moisture >= 0.8:  # Flooded
            # Water tiles when flooded require swimming
            if self.terrain_type == TerrainType.WATER:
                return True  # Still passable with swimming

        return base_passable

    def is_opaque(self) -> bool:
        """Check if tile blocks line of sight."""
        # Glass is transparent even though impassable
        if self.terrain_type == TerrainType.GLASS:
            return False

        # Check if any opaque entities
        for entity in self.entities:
            if entity.opaque:
                return True

        return self.opaque

    def get_affordances(self) -> Set[str]:
        """
        Get all affordances available on this tile.

        Combines terrain affordances with entity affordances
        and applies environmental modifiers.
        """
        # Start with terrain affordances
        affordances = self.terrain_type.get_default_affordances()

        # Apply modifier affordances
        for modifier in self.modifiers:
            effects = MODIFIER_DEFAULTS.get(modifier.type, {})
            affordances.update(effects.get("adds_affordances", set()))
            affordances -= effects.get("removes_affordances", set())

        # Apply environmental modifications
        if self.environment.moisture > 0.7:
            affordances.add("slippery")
            affordances.discard("flammable")

        if self.environment.temperature < -20:
            affordances.add("freezing")
            if self.terrain_type == TerrainType.WATER:
                affordances.add("walkable")
                affordances.discard("drownable")

        if self.environment.light_level < 0.1:
            affordances.add("dark")
            affordances.add("hideable")

        # Add entity affordances
        for entity in self.entities:
            affordances.update(entity.get_affordances())
            # Remove blocked affordances
            for blocked in entity.blocked_affordances:
                affordances.discard(blocked)

        return affordances

    def get_entity_affordances(self, entity: Entity) -> Set[str]:
        """
        Calculate effective affordances for a specific entity on this tile.

        Args:
            entity: The entity to calculate affordances for

        Returns:
            Set of effective affordances
        """
        # Start with tile affordances
        affordances = self.get_affordances()

        # Add entity's own affordances
        affordances.update(entity.own_affordances)

        # Remove blocked affordances
        affordances -= entity.blocked_affordances

        return affordances

    def can_place_entity(self, entity: Entity) -> bool:
        """
        Check if an entity can be placed on this tile.

        Args:
            entity: Entity to place

        Returns:
            True if entity can be placed
        """
        # Check tile passability requirement
        if entity.requires_passable and not self.is_passable():
            return False

        # Check layer capacity
        same_layer_entities = [e for e in self.entities if e.layer == entity.layer]
        current_size = sum(e.size for e in same_layer_entities)

        if current_size + entity.size > MAX_LAYER_SIZE:
            return False

        # Check for conflicts with existing entities
        for existing in self.entities:
            if conflicts(existing, entity):
                return False

        return True

    def add_entity(self, entity: Entity) -> bool:
        """
        Add an entity to this tile.

        Args:
            entity: Entity to add

        Returns:
            True if entity was added successfully
        """
        if not self.can_place_entity(entity):
            return False

        entity.position = self.position
        self.entities.append(entity)
        return True

    def remove_entity(self, entity: Entity) -> bool:
        """
        Remove an entity from this tile.

        Args:
            entity: Entity to remove

        Returns:
            True if entity was removed
        """
        if entity in self.entities:
            self.entities.remove(entity)
            entity.position = None
            return True
        return False

    def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by its ID."""
        for entity in self.entities:
            if entity.id == entity_id:
                return entity
        return None

    def get_entities_by_layer(self, layer: Layer) -> List[Entity]:
        """Get all entities on a specific layer."""
        return [e for e in self.entities if e.layer == layer]

    def get_entities_by_type(self, entity_type) -> List[Entity]:
        """Get all entities of a specific type."""
        return [e for e in self.entities if e.entity_type == entity_type]

    def add_modifier(self, modifier: TerrainModifier) -> None:
        """Add a terrain modifier."""
        # Remove existing modifier of same type
        self.modifiers = [m for m in self.modifiers if m.type != modifier.type]
        self.modifiers.append(modifier)

        # Apply stability effects
        effects = modifier.get_effects()
        if "stability_reduction" in effects:
            self.stability = max(0.0, self.stability - effects["stability_reduction"])

    def remove_modifier(self, modifier_type: str) -> bool:
        """Remove a modifier by type."""
        original_len = len(self.modifiers)
        self.modifiers = [m for m in self.modifiers if m.type != modifier_type]
        return len(self.modifiers) < original_len

    def has_modifier(self, modifier_type: str) -> bool:
        """Check if tile has a specific modifier."""
        return any(m.type for m in self.modifiers if m.type == modifier_type)

    def get_movement_cost(self, from_tile: Optional["Tile"] = None, entity: Optional[Entity] = None) -> float:
        """
        Calculate movement cost to enter this tile.

        Args:
            from_tile: The tile being moved from (for height difference)
            entity: The entity moving (for entity-specific modifiers)

        Returns:
            Movement cost (1.0 is standard, higher is slower, 999+ is impassable)
        """
        from .terrain import TERRAIN_COST

        # Base cost from terrain
        base_cost = TERRAIN_COST.get(self.terrain_type, 1.0)

        if base_cost >= 999.0:
            return base_cost  # Impassable

        # Height difference cost
        if from_tile:
            height_diff = abs(self.height - from_tile.height)
            base_cost += height_diff * 0.5

        # Environmental modifiers
        if self.environment.moisture > 0.7:
            base_cost *= 1.5

        if self.environment.light_level < 0.2:
            base_cost *= 1.2

        # Terrain modifier effects
        for modifier in self.modifiers:
            effects = modifier.get_effects()
            if "movement_cost_modifier" in effects:
                base_cost *= effects["movement_cost_modifier"]

        # Entity-specific modifiers
        if entity and entity.movement_modifiers:
            terrain_mod = entity.movement_modifiers.get(self.terrain_type.name, 1.0)
            base_cost *= terrain_mod

        return base_cost

    def serialize(self) -> dict:
        """Serialize tile to dictionary."""
        return {
            "position": self.position.to_tuple(),
            "terrain": self.terrain_type.name,
            "passable": self.passable,
            "opaque": self.opaque,
            "height": self.height,
            "stability": self.stability,
            "modifiers": [m.to_dict() for m in self.modifiers],
            "environment": self.environment.to_dict(),
            "entities": [e.id for e in self.entities],
            "features": self.features,
            "affordances": list(self.get_affordances())
        }

    @classmethod
    def from_dict(cls, data: dict, entities_map: Optional[dict] = None) -> "Tile":
        """
        Create tile from dictionary.

        Args:
            data: Serialized tile data
            entities_map: Optional mapping of entity IDs to Entity objects
        """
        position = Position.from_tuple(tuple(data["position"]))
        terrain = TerrainType[data["terrain"]]
        environment = TileEnvironment.from_dict(data.get("environment", {}))
        modifiers = [TerrainModifier.from_dict(m) for m in data.get("modifiers", [])]

        tile = cls(
            position=position,
            terrain_type=terrain,
            passable=data.get("passable"),
            opaque=data.get("opaque"),
            height=data.get("height", 0.0),
            environment=environment,
            modifiers=modifiers,
            features=data.get("features", []),
            stability=data.get("stability", 1.0)
        )

        # Add entities if mapping provided
        if entities_map:
            for entity_id in data.get("entities", []):
                if entity_id in entities_map:
                    tile.entities.append(entities_map[entity_id])

        return tile

    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return self.position == other.position

    def __hash__(self):
        return hash(self.position)

    def __repr__(self):
        return f"Tile({self.position}, {self.terrain_type.name})"
