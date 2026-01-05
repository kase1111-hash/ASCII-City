"""Tests for TileGrid class."""

import pytest

from src.shadowengine.grid.grid import TileGrid, GridDimensions
from src.shadowengine.grid.tile import Position, Tile
from src.shadowengine.grid.terrain import TerrainType, TerrainModifier
from src.shadowengine.grid.entity import Entity, Layer, create_item, create_creature
from src.shadowengine.grid.events import TileEventType


class TestGridDimensions:
    """Test GridDimensions class."""

    def test_dimensions_creation(self):
        """Test creating dimensions."""
        dims = GridDimensions(100, 50, 3)
        assert dims.width == 100
        assert dims.height == 50
        assert dims.depth == 3

    def test_contains_valid(self):
        """Test valid position is contained."""
        dims = GridDimensions(10, 10, 1)
        assert dims.contains(Position(0, 0, 0))
        assert dims.contains(Position(9, 9, 0))
        assert dims.contains(Position(5, 5, 0))

    def test_contains_invalid(self):
        """Test invalid position is not contained."""
        dims = GridDimensions(10, 10, 1)
        assert not dims.contains(Position(-1, 0, 0))
        assert not dims.contains(Position(10, 0, 0))
        assert not dims.contains(Position(0, 0, 1))


class TestTileGrid:
    """Test TileGrid class."""

    def test_grid_creation(self):
        """Test creating a grid."""
        grid = TileGrid(20, 15, 3)
        assert grid.width == 20
        assert grid.height == 15
        assert grid.depth == 3

    def test_get_tile_creates(self):
        """Test get_tile creates tile if needed."""
        grid = TileGrid(10, 10)
        tile = grid.get_tile(5, 5, 0)
        assert tile is not None
        assert tile.position == Position(5, 5, 0)
        assert grid.stats["tiles_created"] == 1

    def test_get_tile_returns_same(self):
        """Test get_tile returns same tile object."""
        grid = TileGrid(10, 10)
        tile1 = grid.get_tile(5, 5, 0)
        tile2 = grid.get_tile(5, 5, 0)
        assert tile1 is tile2
        assert grid.stats["tiles_created"] == 1

    def test_get_tile_out_of_bounds(self):
        """Test get_tile returns None for out of bounds."""
        grid = TileGrid(10, 10)
        assert grid.get_tile(-1, 0, 0) is None
        assert grid.get_tile(10, 0, 0) is None
        assert grid.get_tile(0, 10, 0) is None

    def test_get_tile_at(self):
        """Test get_tile_at with Position."""
        grid = TileGrid(10, 10)
        tile = grid.get_tile_at(Position(3, 4, 0))
        assert tile is not None
        assert tile.position == Position(3, 4, 0)

    def test_set_tile(self):
        """Test setting a tile."""
        grid = TileGrid(10, 10)
        tile = Tile(position=Position(5, 5, 0), terrain_type=TerrainType.WATER)
        assert grid.set_tile(tile)
        retrieved = grid.get_tile(5, 5, 0)
        assert retrieved.terrain_type == TerrainType.WATER

    def test_set_tile_out_of_bounds(self):
        """Test setting tile out of bounds fails."""
        grid = TileGrid(10, 10)
        tile = Tile(position=Position(15, 15, 0))
        assert not grid.set_tile(tile)

    def test_has_tile(self):
        """Test checking if tile exists."""
        grid = TileGrid(10, 10)
        assert not grid.has_tile(5, 5, 0)
        grid.get_tile(5, 5, 0)  # Creates tile
        assert grid.has_tile(5, 5, 0)

    def test_remove_tile(self):
        """Test removing a tile."""
        grid = TileGrid(10, 10)
        grid.get_tile(5, 5, 0)
        removed = grid.remove_tile(5, 5, 0)
        assert removed is not None
        assert not grid.has_tile(5, 5, 0)

    def test_default_terrain(self):
        """Test default terrain type."""
        grid = TileGrid(10, 10, default_terrain=TerrainType.GRASS)
        tile = grid.get_tile(5, 5, 0)
        assert tile.terrain_type == TerrainType.GRASS


class TestGridSpatialQueries:
    """Test grid spatial query methods."""

    def test_get_adjacent(self):
        """Test getting adjacent tiles."""
        grid = TileGrid(10, 10)
        center = grid.get_tile(5, 5, 0)
        adjacent = grid.get_adjacent(center)
        # 8 adjacent tiles with diagonals
        assert len(adjacent) == 8

    def test_get_adjacent_no_diagonals(self):
        """Test getting adjacent without diagonals."""
        grid = TileGrid(10, 10)
        center = grid.get_tile(5, 5, 0)
        adjacent = grid.get_adjacent(center, include_diagonals=False)
        assert len(adjacent) == 4

    def test_get_adjacent_at_edge(self):
        """Test getting adjacent at grid edge."""
        grid = TileGrid(10, 10)
        corner = grid.get_tile(0, 0, 0)
        adjacent = grid.get_adjacent(corner)
        assert len(adjacent) == 3  # Only NE, E, SE exist

    def test_get_neighbors(self):
        """Test get_neighbors by coordinates."""
        grid = TileGrid(10, 10)
        neighbors = grid.get_neighbors(5, 5, 0)
        assert len(neighbors) == 8

    def test_get_in_radius(self):
        """Test getting tiles in radius."""
        grid = TileGrid(20, 20)
        center = Position(10, 10, 0)
        tiles = grid.get_in_radius(center, 2.5)
        # Should include center and tiles within 2.5 units
        assert len(tiles) > 0
        for tile in tiles:
            assert center.distance_to(tile.position) <= 2.5

    def test_get_in_radius_excludes_center(self):
        """Test excluding center from radius."""
        grid = TileGrid(20, 20)
        center = Position(10, 10, 0)
        tiles = grid.get_in_radius(center, 1.5, include_center=False)
        center_positions = [t.position for t in tiles]
        assert center not in center_positions

    def test_get_in_rect(self):
        """Test getting tiles in rectangle."""
        grid = TileGrid(20, 20)
        tiles = grid.get_in_rect(5, 5, 7, 7, 0)
        assert len(tiles) == 9  # 3x3 rectangle

    def test_get_line_of_sight(self):
        """Test getting tiles in line."""
        grid = TileGrid(20, 20)
        tiles = grid.get_line_of_sight(Position(0, 0, 0), Position(5, 0, 0))
        assert len(tiles) == 6  # 0-5 inclusive
        for i, tile in enumerate(tiles):
            assert tile.position.x == i

    def test_has_line_of_sight_clear(self):
        """Test clear line of sight."""
        grid = TileGrid(20, 20)
        assert grid.has_line_of_sight(Position(0, 0, 0), Position(5, 5, 0))

    def test_has_line_of_sight_blocked(self):
        """Test blocked line of sight."""
        grid = TileGrid(20, 20)
        # Place rock in the middle
        wall = grid.get_tile(2, 2, 0)
        wall.set_terrain(TerrainType.ROCK)
        assert not grid.has_line_of_sight(Position(0, 0, 0), Position(4, 4, 0))


class TestGridPathfinding:
    """Test grid pathfinding."""

    def test_find_path_simple(self):
        """Test simple pathfinding."""
        grid = TileGrid(10, 10)
        path = grid.find_path(Position(0, 0, 0), Position(5, 0, 0))
        assert len(path) > 0
        assert path[0].position == Position(0, 0, 0)
        assert path[-1].position == Position(5, 0, 0)

    def test_find_path_around_obstacle(self):
        """Test pathfinding around obstacle."""
        grid = TileGrid(10, 10)
        # Create wall
        for y in range(3, 7):
            wall = grid.get_tile(5, y, 0)
            wall.set_terrain(TerrainType.ROCK)

        path = grid.find_path(Position(3, 5, 0), Position(7, 5, 0))
        assert len(path) > 0
        # Path should go around
        for tile in path:
            assert tile.passable

    def test_find_path_no_path(self):
        """Test pathfinding with no path."""
        grid = TileGrid(10, 10)
        # Create wall around destination
        for x in range(7, 10):
            for y in range(7, 10):
                if (x, y) != (8, 8):
                    wall = grid.get_tile(x, y, 0)
                    wall.set_terrain(TerrainType.ROCK)

        path = grid.find_path(Position(0, 0, 0), Position(8, 8, 0))
        assert len(path) == 0

    def test_find_path_with_entity(self):
        """Test pathfinding considering entity modifiers."""
        grid = TileGrid(10, 10)
        entity = Entity(
            name="Test",
            movement_modifiers={"water": 2.0},
        )
        # Place water
        water = grid.get_tile(2, 0, 0)
        water.set_terrain(TerrainType.WATER)

        path = grid.find_path(Position(0, 0, 0), Position(5, 0, 0), entity)
        assert len(path) > 0


class TestGridEntityManagement:
    """Test grid entity management."""

    def test_add_entity(self):
        """Test adding entity to grid."""
        grid = TileGrid(10, 10)
        entity = create_item("Key")
        assert grid.add_entity(entity, Position(5, 5, 0))
        assert grid.stats["entities_placed"] == 1

    def test_add_entity_at_position(self):
        """Test entity is at correct position."""
        grid = TileGrid(10, 10)
        entity = create_item("Key")
        grid.add_entity(entity, Position(5, 5, 0))
        pos = grid.get_entity_position(entity.id)
        assert pos == Position(5, 5, 0)

    def test_add_entity_on_tile(self):
        """Test entity appears on tile."""
        grid = TileGrid(10, 10)
        entity = create_item("Key")
        grid.add_entity(entity, Position(5, 5, 0))
        tile = grid.get_tile(5, 5, 0)
        assert entity.id in tile.entity_ids

    def test_get_entity(self):
        """Test retrieving entity by ID."""
        grid = TileGrid(10, 10)
        entity = create_item("Key")
        grid.add_entity(entity, Position(5, 5, 0))
        retrieved = grid.get_entity(entity.id)
        assert retrieved is entity

    def test_get_entities_at(self):
        """Test getting entities at position."""
        grid = TileGrid(10, 10)
        item1 = create_item("Key1")
        item2 = create_item("Key2")
        grid.add_entity(item1, Position(5, 5, 0))
        grid.add_entity(item2, Position(5, 5, 0))

        entities = grid.get_entities_at(Position(5, 5, 0))
        assert len(entities) == 2

    def test_remove_entity(self):
        """Test removing entity from grid."""
        grid = TileGrid(10, 10)
        entity = create_item("Key")
        grid.add_entity(entity, Position(5, 5, 0))
        removed = grid.remove_entity(entity.id)
        assert removed is entity
        assert grid.get_entity(entity.id) is None

    def test_move_entity(self):
        """Test moving entity to new position."""
        grid = TileGrid(10, 10)
        entity = create_item("Key")
        grid.add_entity(entity, Position(5, 5, 0))

        assert grid.move_entity(entity.id, Position(7, 7, 0))

        pos = grid.get_entity_position(entity.id)
        assert pos == Position(7, 7, 0)
        assert not grid.get_tile(5, 5, 0).has_entity(entity.id)
        assert grid.get_tile(7, 7, 0).has_entity(entity.id)

    def test_move_entity_blocked(self):
        """Test moving entity to impassable tile fails."""
        grid = TileGrid(10, 10)
        entity = create_item("Key")
        grid.add_entity(entity, Position(5, 5, 0))

        wall = grid.get_tile(7, 7, 0)
        wall.set_terrain(TerrainType.ROCK)

        assert not grid.move_entity(entity.id, Position(7, 7, 0))
        assert grid.get_entity_position(entity.id) == Position(5, 5, 0)

    def test_can_place_entity(self):
        """Test placement validation."""
        grid = TileGrid(10, 10)
        tile = grid.get_tile(5, 5, 0)

        item = create_item("Key")
        assert grid.can_place_entity(tile, item)

        # On rock (not passable)
        rock = grid.get_tile(3, 3, 0)
        rock.set_terrain(TerrainType.ROCK)
        assert not grid.can_place_entity(rock, item)

    def test_get_entities_in_radius(self):
        """Test getting entities within radius."""
        grid = TileGrid(20, 20)
        entity1 = create_item("Near")
        entity2 = create_item("Far")
        grid.add_entity(entity1, Position(10, 10, 0))
        grid.add_entity(entity2, Position(18, 18, 0))

        nearby = grid.get_entities_in_radius(Position(10, 10, 0), 3.0)
        entity_ids = [e.id for e, _ in nearby]
        assert entity1.id in entity_ids
        assert entity2.id not in entity_ids


class TestGridEvents:
    """Test grid event integration."""

    def test_entity_entered_event(self):
        """Test entity entered event is emitted."""
        grid = TileGrid(10, 10)
        received = []

        grid.events.subscribe(TileEventType.ENTITY_ENTERED, lambda e: received.append(e))

        entity = create_item("Key")
        grid.add_entity(entity, Position(5, 5, 0))

        assert len(received) == 1
        assert received[0].cause_id == entity.id
        assert received[0].tile_position == (5, 5, 0)

    def test_entity_exited_event(self):
        """Test entity exited event is emitted."""
        grid = TileGrid(10, 10)
        received = []

        grid.events.subscribe(TileEventType.ENTITY_EXITED, lambda e: received.append(e))

        entity = create_item("Key")
        grid.add_entity(entity, Position(5, 5, 0))
        grid.remove_entity(entity.id)

        assert len(received) == 1
        assert received[0].cause_id == entity.id

    def test_move_emits_both_events(self):
        """Test move emits exit and enter events."""
        grid = TileGrid(10, 10)
        exits = []
        enters = []

        grid.events.subscribe(TileEventType.ENTITY_EXITED, lambda e: exits.append(e))
        grid.events.subscribe(TileEventType.ENTITY_ENTERED, lambda e: enters.append(e))

        entity = create_item("Key")
        grid.add_entity(entity, Position(5, 5, 0))
        enters.clear()  # Clear initial enter

        grid.move_entity(entity.id, Position(7, 7, 0))

        assert len(exits) == 1
        assert exits[0].tile_position == (5, 5, 0)
        assert len(enters) == 1
        assert enters[0].tile_position == (7, 7, 0)


class TestGridTerrainModification:
    """Test grid terrain modification."""

    def test_set_terrain(self):
        """Test setting terrain type."""
        grid = TileGrid(10, 10)
        assert grid.set_terrain(5, 5, 0, TerrainType.WATER)
        tile = grid.get_tile(5, 5, 0)
        assert tile.terrain_type == TerrainType.WATER

    def test_set_terrain_emits_event(self):
        """Test terrain change emits event."""
        grid = TileGrid(10, 10)
        received = []

        grid.events.subscribe(TileEventType.TERRAIN_CHANGED, lambda e: received.append(e))

        grid.set_terrain(5, 5, 0, TerrainType.ROCK)

        assert len(received) == 1
        assert received[0].data["terrain"] == "rock"

    def test_add_modifier(self):
        """Test adding terrain modifier."""
        grid = TileGrid(10, 10)
        mod = TerrainModifier(type="wet")
        assert grid.add_modifier(5, 5, 0, mod)
        tile = grid.get_tile(5, 5, 0)
        assert tile.has_modifier("wet")

    def test_remove_modifier(self):
        """Test removing terrain modifier."""
        grid = TileGrid(10, 10)
        mod = TerrainModifier(type="wet")
        grid.add_modifier(5, 5, 0, mod)
        assert grid.remove_modifier(5, 5, 0, "wet")
        tile = grid.get_tile(5, 5, 0)
        assert not tile.has_modifier("wet")


class TestGridIteration:
    """Test grid iteration methods."""

    def test_all_tiles(self):
        """Test iterating all tiles."""
        grid = TileGrid(10, 10)
        grid.get_tile(0, 0, 0)
        grid.get_tile(5, 5, 0)
        grid.get_tile(9, 9, 0)

        tiles = list(grid.all_tiles())
        assert len(tiles) == 3

    def test_all_entities(self):
        """Test iterating all entities."""
        grid = TileGrid(10, 10)
        for i in range(5):
            entity = create_item(f"Item_{i}")
            grid.add_entity(entity, Position(i, 0, 0))

        entities = list(grid.all_entities())
        assert len(entities) == 5

    def test_tiles_matching(self):
        """Test finding tiles matching predicate."""
        grid = TileGrid(10, 10)
        grid.set_terrain(0, 0, 0, TerrainType.WATER)
        grid.set_terrain(1, 0, 0, TerrainType.WATER)
        grid.set_terrain(2, 0, 0, TerrainType.ROCK)

        water_tiles = grid.tiles_matching(lambda t: t.terrain_type == TerrainType.WATER)
        assert len(water_tiles) == 2

    def test_entities_matching(self):
        """Test finding entities matching predicate."""
        grid = TileGrid(10, 10)
        item = create_item("Key")
        creature = create_creature("Wolf")
        grid.add_entity(item, Position(0, 0, 0))
        grid.add_entity(creature, Position(1, 0, 0))

        creatures = grid.entities_matching(lambda e: "fightable" in e.own_affordances)
        assert len(creatures) == 1
        assert creatures[0].name == "Wolf"


class TestGridSerialization:
    """Test grid serialization."""

    def test_grid_to_dict(self):
        """Test serializing grid."""
        grid = TileGrid(10, 10, 2)
        grid.set_terrain(5, 5, 0, TerrainType.WATER)
        entity = create_item("Key")
        grid.add_entity(entity, Position(3, 3, 0))

        data = grid.to_dict()

        assert data["dimensions"]["width"] == 10
        assert data["dimensions"]["height"] == 10
        assert data["dimensions"]["depth"] == 2
        assert len(data["tiles"]) == 2  # Two tiles created
        assert len(data["entities"]) == 1

    def test_grid_from_dict(self):
        """Test deserializing grid."""
        original = TileGrid(20, 15, 3)
        original.set_terrain(5, 5, 0, TerrainType.ROCK)
        entity = create_item("Key")
        original.add_entity(entity, Position(3, 3, 0))

        data = original.to_dict()
        restored = TileGrid.from_dict(data)

        assert restored.width == 20
        assert restored.height == 15
        assert restored.depth == 3
        assert restored.get_tile(5, 5, 0).terrain_type == TerrainType.ROCK
        assert len(list(restored.all_entities())) == 1

    def test_clear(self):
        """Test clearing the grid."""
        grid = TileGrid(10, 10)
        grid.get_tile(5, 5, 0)
        entity = create_item("Key")
        grid.add_entity(entity, Position(3, 3, 0))

        grid.clear()

        assert len(list(grid.all_tiles())) == 0
        assert len(list(grid.all_entities())) == 0

    def test_get_stats(self):
        """Test getting grid statistics."""
        grid = TileGrid(10, 10)
        grid.get_tile(0, 0, 0)
        grid.get_tile(1, 1, 0)
        entity = create_item("Key")
        grid.add_entity(entity, Position(0, 0, 0))

        stats = grid.get_stats()
        assert stats["tiles_count"] == 2
        assert stats["entities_count"] == 1
        assert stats["tiles_created"] == 2
        assert stats["entities_placed"] == 1
