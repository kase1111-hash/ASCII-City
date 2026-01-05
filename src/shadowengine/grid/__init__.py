"""
Tile Grid System for the Emergent ASCII World.

This module provides the spatial foundation for the game world:
- Tiles with terrain, environment, and affordances
- Entities that exist on tiles
- Grid for spatial queries and pathfinding
- Event system for reactive behaviors
"""

from .terrain import (
    TerrainType,
    FluidType,
    TerrainModifier,
    TERRAIN_PROPERTIES,
    TERRAIN_MODIFIERS,
    get_terrain_properties,
    get_predefined_modifier,
    create_modifier,
)

from .tile import (
    Position,
    DIRECTIONS,
    TileEnvironment,
    Tile,
)

from .entity import (
    Layer,
    EntityType,
    Size,
    Entity,
    MAX_LAYER_SIZE,
    create_item,
    create_furniture,
    create_creature,
    create_feature,
)

from .events import (
    TileEventType,
    TileEvent,
    TileEventBus,
    EventHandler,
    create_movement_event,
    create_damage_event,
    create_environmental_event,
)

from .grid import (
    GridDimensions,
    TileGrid,
)


__all__ = [
    # Terrain
    "TerrainType",
    "FluidType",
    "TerrainModifier",
    "TERRAIN_PROPERTIES",
    "TERRAIN_MODIFIERS",
    "get_terrain_properties",
    "get_predefined_modifier",
    "create_modifier",

    # Tile
    "Position",
    "DIRECTIONS",
    "TileEnvironment",
    "Tile",

    # Entity
    "Layer",
    "EntityType",
    "Size",
    "Entity",
    "MAX_LAYER_SIZE",
    "create_item",
    "create_furniture",
    "create_creature",
    "create_feature",

    # Events
    "TileEventType",
    "TileEvent",
    "TileEventBus",
    "EventHandler",
    "create_movement_event",
    "create_damage_event",
    "create_environmental_event",

    # Grid
    "GridDimensions",
    "TileGrid",
]
