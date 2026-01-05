"""
Grid System Module - Tile-based spatial foundation for ASCII-City.

This module provides the spatial grid system including:
- Position: 3D coordinate system
- Tile: Rich spatial data containers
- TileGrid: Spatial queries and pathfinding
- Entity placement and affordance management
"""

from .position import Position
from .terrain import TerrainType, TerrainModifier, FluidType
from .tile import Tile, TileEnvironment, Layer
from .entity import Entity, EntityType
from .grid import TileGrid
from .events import TileEvent, TileEventType
from .pathfinding import find_path, get_line_of_sight, calculate_movement_cost

__all__ = [
    # Core classes
    "Position",
    "Tile",
    "TileGrid",
    "TileEnvironment",
    "Entity",

    # Enums
    "TerrainType",
    "TerrainModifier",
    "FluidType",
    "Layer",
    "EntityType",
    "TileEventType",

    # Events
    "TileEvent",

    # Functions
    "find_path",
    "get_line_of_sight",
    "calculate_movement_cost",
]
