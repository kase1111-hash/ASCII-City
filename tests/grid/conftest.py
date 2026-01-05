"""
Shared test fixtures for grid system tests.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from shadowengine.grid import (
    Position, Tile, TileGrid, TileEnvironment,
    TerrainType, TerrainModifier, FluidType,
    Entity, EntityType, Layer,
    TileEvent, TileEventType,
    find_path, get_line_of_sight, calculate_movement_cost
)


# =============================================================================
# Position Fixtures
# =============================================================================

@pytest.fixture
def origin_position():
    """Position at origin."""
    return Position(0, 0, 0)


@pytest.fixture
def sample_position():
    """Standard test position (within 10x10 grid bounds)."""
    return Position(5, 5, 0)


@pytest.fixture
def elevated_position():
    """Position at height."""
    return Position(5, 5, 2)


@pytest.fixture
def adjacent_positions():
    """Set of adjacent positions around (5, 5, 0)."""
    return [
        Position(4, 5, 0),  # West
        Position(6, 5, 0),  # East
        Position(5, 4, 0),  # North
        Position(5, 6, 0),  # South
        Position(4, 4, 0),  # Northwest
        Position(6, 4, 0),  # Northeast
        Position(4, 6, 0),  # Southwest
        Position(6, 6, 0),  # Southeast
    ]


# =============================================================================
# Terrain Fixtures
# =============================================================================

@pytest.fixture
def all_terrain_types():
    """All available terrain types."""
    return list(TerrainType)


@pytest.fixture
def passable_terrains():
    """Terrain types that are passable by default."""
    return [TerrainType.SOIL, TerrainType.WOOD, TerrainType.METAL, TerrainType.WATER]


@pytest.fixture
def impassable_terrains():
    """Terrain types that are impassable by default."""
    return [TerrainType.ROCK, TerrainType.VOID, TerrainType.GLASS]


@pytest.fixture
def wet_modifier():
    """Wet terrain modifier."""
    return TerrainModifier(type="wet", intensity=0.8)


@pytest.fixture
def frozen_modifier():
    """Frozen terrain modifier."""
    return TerrainModifier(type="frozen", intensity=1.0)


@pytest.fixture
def cracked_modifier():
    """Cracked terrain modifier."""
    return TerrainModifier(type="cracked", intensity=0.5)


# =============================================================================
# Environment Fixtures
# =============================================================================

@pytest.fixture
def default_environment():
    """Default tile environment."""
    return TileEnvironment()


@pytest.fixture
def dark_environment():
    """Dark tile environment."""
    return TileEnvironment(light_level=0.05)


@pytest.fixture
def flooded_environment():
    """Flooded tile environment."""
    return TileEnvironment(moisture=0.9, fluid=FluidType.WATER)


@pytest.fixture
def freezing_environment():
    """Freezing tile environment."""
    return TileEnvironment(temperature=-30.0)


@pytest.fixture
def hot_environment():
    """Hot tile environment."""
    return TileEnvironment(temperature=45.0)


# =============================================================================
# Tile Fixtures
# =============================================================================

@pytest.fixture
def basic_tile():
    """Basic soil tile."""
    return Tile(
        position=Position(5, 5, 0),
        terrain_type=TerrainType.SOIL
    )


@pytest.fixture
def rock_tile():
    """Rock tile (impassable)."""
    return Tile(
        position=Position(5, 5, 0),
        terrain_type=TerrainType.ROCK
    )


@pytest.fixture
def water_tile():
    """Water tile."""
    return Tile(
        position=Position(5, 5, 0),
        terrain_type=TerrainType.WATER
    )


@pytest.fixture
def wood_tile():
    """Wood tile (flammable)."""
    return Tile(
        position=Position(5, 5, 0),
        terrain_type=TerrainType.WOOD
    )


@pytest.fixture
def glass_tile():
    """Glass tile (transparent but impassable)."""
    return Tile(
        position=Position(5, 5, 0),
        terrain_type=TerrainType.GLASS
    )


@pytest.fixture
def tile_with_dark_env(dark_environment):
    """Tile with dark environment."""
    return Tile(
        position=Position(5, 5, 0),
        terrain_type=TerrainType.SOIL,
        environment=dark_environment
    )


@pytest.fixture
def tile_with_flooded_env(flooded_environment):
    """Tile with flooded environment."""
    return Tile(
        position=Position(5, 5, 0),
        terrain_type=TerrainType.SOIL,
        environment=flooded_environment
    )


# =============================================================================
# Entity Fixtures
# =============================================================================

@pytest.fixture
def basic_entity():
    """Basic test entity."""
    return Entity(
        id="test_entity",
        name="Test Entity",
        entity_type=EntityType.ITEM,
        size=1,
        layer=Layer.OBJECT
    )


@pytest.fixture
def character_entity():
    """Character entity."""
    return Entity(
        id="test_character",
        name="Test Character",
        entity_type=EntityType.CHARACTER,
        size=2,
        layer=Layer.OBJECT,
        passable=False
    )


@pytest.fixture
def furniture_entity():
    """Furniture entity (impassable)."""
    return Entity(
        id="table",
        name="Table",
        entity_type=EntityType.FURNITURE,
        size=2,
        layer=Layer.OBJECT,
        passable=False,
        opaque=False
    )


@pytest.fixture
def light_source_entity():
    """Light source entity."""
    return Entity(
        id="torch",
        name="Torch",
        entity_type=EntityType.LIGHT_SOURCE,
        size=1,
        layer=Layer.CEILING,
        own_affordances={"illuminating", "flammable"}
    )


@pytest.fixture
def trigger_entity():
    """Trigger entity (pressure plate)."""
    return Entity(
        id="pressure_plate",
        name="Pressure Plate",
        entity_type=EntityType.TRIGGER,
        size=1,
        layer=Layer.GROUND,
        own_affordances={"triggerable"}
    )


# =============================================================================
# Grid Fixtures
# =============================================================================

@pytest.fixture
def small_grid():
    """Small 10x10 grid."""
    return TileGrid(width=10, height=10, depth=1)


@pytest.fixture
def medium_grid():
    """Medium 50x50 grid."""
    return TileGrid(width=50, height=50, depth=1)


@pytest.fixture
def multi_level_grid():
    """Multi-level 20x20x3 grid."""
    return TileGrid(width=20, height=20, depth=3)


@pytest.fixture
def populated_grid(small_grid, basic_entity, character_entity):
    """Grid with some entities placed."""
    small_grid.place_entity(basic_entity, Position(2, 2, 0))
    small_grid.place_entity(character_entity, Position(5, 5, 0))
    return small_grid


@pytest.fixture
def grid_with_obstacles(medium_grid):
    """Grid with rock obstacles."""
    # Create a wall of rocks
    for x in range(10, 15):
        tile = medium_grid.get_tile(x, 10, 0)
        tile.terrain_type = TerrainType.ROCK
        tile.passable = False
        tile.opaque = True
    return medium_grid


@pytest.fixture
def grid_with_water(medium_grid):
    """Grid with water region."""
    # Create a pool of water
    for x in range(5, 10):
        for y in range(5, 10):
            tile = medium_grid.get_tile(x, y, 0)
            tile.terrain_type = TerrainType.WATER
    return medium_grid


@pytest.fixture
def maze_grid():
    """Grid configured as a simple maze."""
    grid = TileGrid(width=11, height=11, depth=1)

    # Create walls (rock tiles)
    walls = [
        # Outer walls are implicitly handled by bounds
        # Internal walls
        (2, 1), (2, 2), (2, 3),
        (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
        (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
        (8, 5), (8, 6), (8, 7), (8, 8), (8, 9),
    ]

    for x, y in walls:
        tile = grid.get_tile(x, y, 0)
        tile.terrain_type = TerrainType.ROCK
        tile.passable = False
        tile.opaque = True

    return grid


# =============================================================================
# Helper Classes
# =============================================================================

class GridTestHelpers:
    """Helper methods for grid tests."""

    @staticmethod
    def create_path_grid(width: int, height: int, blocked_positions: list) -> TileGrid:
        """Create a grid with specific blocked positions."""
        grid = TileGrid(width=width, height=height)
        for x, y in blocked_positions:
            tile = grid.get_tile(x, y, 0)
            if tile:
                tile.terrain_type = TerrainType.ROCK
                tile.passable = False
        return grid

    @staticmethod
    def fill_rect_terrain(
        grid: TileGrid,
        x1: int, y1: int,
        x2: int, y2: int,
        terrain: TerrainType
    ):
        """Fill a rectangle with terrain."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                tile = grid.get_tile(x, y, 0)
                if tile:
                    tile.terrain_type = terrain
                    defaults = terrain.get_default_properties()
                    tile.passable = defaults.get("passable", True)

    @staticmethod
    def count_passable_tiles(grid: TileGrid) -> int:
        """Count passable tiles in grid."""
        return len(grid.get_passable_tiles())

    @staticmethod
    def get_path_positions(path: list) -> list:
        """Extract positions from path tiles."""
        return [tile.position for tile in path] if path else []


@pytest.fixture
def grid_helpers():
    """Grid test helper methods."""
    return GridTestHelpers()
