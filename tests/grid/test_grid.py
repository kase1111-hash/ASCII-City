"""
Comprehensive tests for TileGrid class.
"""

import pytest
from shadowengine.grid import (
    Position, Tile, TileGrid, TileEnvironment,
    TerrainType, TerrainModifier,
    Entity, EntityType, Layer,
    TileEventType
)


class TestTileGridCreation:
    """Tests for TileGrid creation."""

    @pytest.mark.unit
    def test_create_small_grid(self, small_grid):
        """Can create a small grid."""
        assert small_grid.width == 10
        assert small_grid.height == 10
        assert small_grid.depth == 1

    @pytest.mark.unit
    def test_create_medium_grid(self, medium_grid):
        """Can create a medium grid."""
        assert medium_grid.width == 50
        assert medium_grid.height == 50

    @pytest.mark.unit
    def test_create_multi_level_grid(self, multi_level_grid):
        """Can create a multi-level grid."""
        assert multi_level_grid.depth == 3

    @pytest.mark.unit
    def test_create_grid_with_default_terrain(self):
        """Grid can have custom default terrain."""
        grid = TileGrid(width=10, height=10, default_terrain=TerrainType.ROCK)
        assert grid.default_terrain == TerrainType.ROCK

    @pytest.mark.unit
    def test_invalid_dimensions(self):
        """Invalid dimensions raise error."""
        with pytest.raises(ValueError):
            TileGrid(width=0, height=10)

        with pytest.raises(ValueError):
            TileGrid(width=10, height=0)

        with pytest.raises(ValueError):
            TileGrid(width=10, height=10, depth=0)

        with pytest.raises(ValueError):
            TileGrid(width=-1, height=10)


class TestTileGridPositionValidation:
    """Tests for position validation."""

    @pytest.mark.unit
    def test_valid_position(self, small_grid):
        """Valid positions are recognized."""
        assert small_grid.is_valid_position(0, 0, 0) is True
        assert small_grid.is_valid_position(5, 5, 0) is True
        assert small_grid.is_valid_position(9, 9, 0) is True

    @pytest.mark.unit
    def test_invalid_position_negative(self, small_grid):
        """Negative positions are invalid."""
        assert small_grid.is_valid_position(-1, 0, 0) is False
        assert small_grid.is_valid_position(0, -1, 0) is False
        assert small_grid.is_valid_position(0, 0, -1) is False

    @pytest.mark.unit
    def test_invalid_position_out_of_bounds(self, small_grid):
        """Out of bounds positions are invalid."""
        assert small_grid.is_valid_position(10, 0, 0) is False
        assert small_grid.is_valid_position(0, 10, 0) is False
        assert small_grid.is_valid_position(0, 0, 1) is False

    @pytest.mark.unit
    def test_multi_level_valid_z(self, multi_level_grid):
        """Multi-level grid accepts valid z values."""
        assert multi_level_grid.is_valid_position(5, 5, 0) is True
        assert multi_level_grid.is_valid_position(5, 5, 1) is True
        assert multi_level_grid.is_valid_position(5, 5, 2) is True
        assert multi_level_grid.is_valid_position(5, 5, 3) is False


class TestTileGridTileAccess:
    """Tests for tile access."""

    @pytest.mark.unit
    def test_get_tile(self, small_grid):
        """Can get tile at position."""
        tile = small_grid.get_tile(5, 5, 0)
        assert tile is not None
        assert tile.position == Position(5, 5, 0)

    @pytest.mark.unit
    def test_get_tile_default_terrain(self, small_grid):
        """New tiles have default terrain."""
        tile = small_grid.get_tile(5, 5, 0)
        assert tile.terrain_type == TerrainType.SOIL

    @pytest.mark.unit
    def test_get_tile_out_of_bounds(self, small_grid):
        """Out of bounds returns None."""
        assert small_grid.get_tile(100, 100, 0) is None
        assert small_grid.get_tile(-1, 5, 0) is None

    @pytest.mark.unit
    def test_get_tile_at_position(self, small_grid, sample_position):
        """Can get tile using Position object."""
        tile = small_grid.get_tile_at_position(sample_position)
        assert tile is not None

    @pytest.mark.unit
    def test_get_same_tile_twice(self, small_grid):
        """Getting same position returns same tile."""
        tile1 = small_grid.get_tile(5, 5, 0)
        tile2 = small_grid.get_tile(5, 5, 0)
        assert tile1 is tile2

    @pytest.mark.unit
    def test_set_tile(self, small_grid):
        """Can set a tile in the grid."""
        tile = Tile(
            position=Position(5, 5, 0),
            terrain_type=TerrainType.WATER
        )
        assert small_grid.set_tile(tile) is True

        retrieved = small_grid.get_tile(5, 5, 0)
        assert retrieved.terrain_type == TerrainType.WATER

    @pytest.mark.unit
    def test_set_tile_out_of_bounds(self, small_grid):
        """Setting tile out of bounds fails."""
        tile = Tile(
            position=Position(100, 100, 0),
            terrain_type=TerrainType.WATER
        )
        assert small_grid.set_tile(tile) is False


class TestTileGridAdjacency:
    """Tests for tile adjacency queries."""

    @pytest.mark.unit
    def test_get_adjacent_tiles(self, small_grid):
        """Can get adjacent tiles."""
        center = small_grid.get_tile(5, 5, 0)
        adjacent = small_grid.get_adjacent(center)

        # Should have 8 adjacent tiles (with diagonals)
        assert len(adjacent) == 8

    @pytest.mark.unit
    def test_get_adjacent_cardinal_only(self, small_grid):
        """Can get cardinal adjacent tiles only."""
        center = small_grid.get_tile(5, 5, 0)
        adjacent = small_grid.get_adjacent(center, include_diagonals=False)

        assert len(adjacent) == 4

    @pytest.mark.unit
    def test_get_adjacent_at_corner(self, small_grid):
        """Corner tiles have fewer neighbors."""
        corner = small_grid.get_tile(0, 0, 0)
        adjacent = small_grid.get_adjacent(corner)

        # Corner has only 3 neighbors (with diagonals)
        assert len(adjacent) == 3

    @pytest.mark.unit
    def test_get_adjacent_at_edge(self, small_grid):
        """Edge tiles have fewer neighbors."""
        edge = small_grid.get_tile(5, 0, 0)
        adjacent = small_grid.get_adjacent(edge)

        # Edge has 5 neighbors (with diagonals)
        assert len(adjacent) == 5


class TestTileGridRadiusQuery:
    """Tests for radius-based queries."""

    @pytest.mark.unit
    def test_get_in_radius(self, medium_grid):
        """Can get tiles within radius."""
        center = medium_grid.get_tile(25, 25, 0)
        tiles = medium_grid.get_in_radius(center, radius=2)

        # Radius 2 circle, excluding center
        assert len(tiles) > 0
        for tile in tiles:
            dist = center.position.distance_to(tile.position, include_z=False)
            assert dist <= 2.0

    @pytest.mark.unit
    def test_get_in_radius_include_center(self, medium_grid):
        """Can include center tile in radius query."""
        center = medium_grid.get_tile(25, 25, 0)
        tiles_without = medium_grid.get_in_radius(center, radius=1, include_center=False)
        tiles_with = medium_grid.get_in_radius(center, radius=1, include_center=True)

        assert len(tiles_with) == len(tiles_without) + 1
        assert center in tiles_with
        assert center not in tiles_without

    @pytest.mark.unit
    def test_get_in_radius_zero(self, medium_grid):
        """Radius 0 returns empty or center only."""
        center = medium_grid.get_tile(25, 25, 0)
        tiles = medium_grid.get_in_radius(center, radius=0, include_center=True)
        assert len(tiles) == 1
        assert tiles[0] == center

    @pytest.mark.unit
    def test_get_in_radius_position(self, medium_grid):
        """Can use Position object for center."""
        pos = Position(25, 25, 0)
        tiles = medium_grid.get_in_radius(pos, radius=1)
        assert len(tiles) > 0


class TestTileGridLineOfSight:
    """Tests for line of sight queries."""

    @pytest.mark.unit
    def test_get_line_of_sight_straight(self, medium_grid):
        """Can get tiles along straight line."""
        from_tile = medium_grid.get_tile(5, 5, 0)
        to_tile = medium_grid.get_tile(10, 5, 0)
        los = medium_grid.get_line_of_sight(from_tile, to_tile)

        assert len(los) == 6  # 5 to 10 inclusive
        assert los[0] == from_tile
        assert los[-1] == to_tile

    @pytest.mark.unit
    def test_get_line_of_sight_diagonal(self, medium_grid):
        """Can get tiles along diagonal line."""
        from_tile = medium_grid.get_tile(5, 5, 0)
        to_tile = medium_grid.get_tile(10, 10, 0)
        los = medium_grid.get_line_of_sight(from_tile, to_tile)

        assert len(los) > 0
        assert los[0] == from_tile
        assert los[-1] == to_tile

    @pytest.mark.unit
    def test_line_of_sight_blocked(self, grid_with_obstacles):
        """Line of sight is blocked by opaque tiles."""
        from_tile = grid_with_obstacles.get_tile(5, 10, 0)
        to_tile = grid_with_obstacles.get_tile(20, 10, 0)
        los = grid_with_obstacles.get_line_of_sight(from_tile, to_tile)

        # Should stop at the rock wall
        assert los[-1].position.x < 15

    @pytest.mark.unit
    def test_has_line_of_sight_clear(self, medium_grid):
        """Check clear line of sight."""
        from_tile = medium_grid.get_tile(5, 5, 0)
        to_tile = medium_grid.get_tile(10, 5, 0)
        assert medium_grid.has_line_of_sight(from_tile, to_tile) is True

    @pytest.mark.unit
    def test_has_line_of_sight_blocked(self, grid_with_obstacles):
        """Check blocked line of sight."""
        from_tile = grid_with_obstacles.get_tile(5, 10, 0)
        to_tile = grid_with_obstacles.get_tile(20, 10, 0)
        assert grid_with_obstacles.has_line_of_sight(from_tile, to_tile) is False


class TestTileGridEntityManagement:
    """Tests for entity management in grid."""

    @pytest.mark.unit
    def test_place_entity(self, small_grid, basic_entity):
        """Can place entity on grid."""
        pos = Position(5, 5, 0)
        assert small_grid.place_entity(basic_entity, pos) is True
        assert basic_entity.position == pos

    @pytest.mark.unit
    def test_place_entity_out_of_bounds(self, small_grid, basic_entity):
        """Cannot place entity out of bounds."""
        pos = Position(100, 100, 0)
        assert small_grid.place_entity(basic_entity, pos) is False

    @pytest.mark.unit
    def test_place_entity_on_impassable(self, grid_with_obstacles, basic_entity):
        """Cannot place entity on impassable tile."""
        pos = Position(12, 10, 0)  # On rock wall
        assert grid_with_obstacles.place_entity(basic_entity, pos) is False

    @pytest.mark.unit
    def test_get_entity(self, populated_grid, basic_entity):
        """Can get entity by ID."""
        found = populated_grid.get_entity("test_entity")
        assert found == basic_entity

    @pytest.mark.unit
    def test_get_nonexistent_entity(self, small_grid):
        """Getting nonexistent entity returns None."""
        assert small_grid.get_entity("nonexistent") is None

    @pytest.mark.unit
    def test_get_entities_at(self, populated_grid):
        """Can get entities at position."""
        entities = populated_grid.get_entities_at(Position(2, 2, 0))
        assert len(entities) == 1
        assert entities[0].id == "test_entity"

    @pytest.mark.unit
    def test_get_all_entities(self, populated_grid):
        """Can get all entities in grid."""
        entities = populated_grid.get_all_entities()
        assert len(entities) == 2

    @pytest.mark.unit
    def test_remove_entity(self, populated_grid, basic_entity):
        """Can remove entity from grid."""
        assert populated_grid.remove_entity(basic_entity) is True
        assert populated_grid.get_entity("test_entity") is None

    @pytest.mark.unit
    def test_remove_nonexistent_entity(self, small_grid, basic_entity):
        """Removing nonexistent entity returns False."""
        assert small_grid.remove_entity(basic_entity) is False

    @pytest.mark.unit
    def test_move_entity(self, populated_grid, basic_entity):
        """Can move entity to new position."""
        new_pos = Position(7, 7, 0)
        assert populated_grid.move_entity(basic_entity, new_pos) is True
        assert basic_entity.position == new_pos

    @pytest.mark.unit
    def test_move_entity_to_impassable(self, grid_with_obstacles, basic_entity):
        """Cannot move entity to impassable tile."""
        grid_with_obstacles.place_entity(basic_entity, Position(5, 5, 0))
        result = grid_with_obstacles.move_entity(basic_entity, Position(12, 10, 0))
        assert result is False


class TestTileGridEvents:
    """Tests for tile grid event system."""

    @pytest.mark.unit
    def test_subscribe_to_event(self, small_grid):
        """Can subscribe to tile events."""
        events_received = []

        def handler(event):
            events_received.append(event)

        small_grid.subscribe_to_event(TileEventType.ENTERED, handler)

        entity = Entity(id="test", name="Test", entity_type=EntityType.ITEM)
        small_grid.place_entity(entity, Position(5, 5, 0))

        assert len(events_received) == 1
        assert events_received[0].event_type == TileEventType.ENTERED

    @pytest.mark.unit
    def test_unsubscribe_from_event(self, small_grid):
        """Can unsubscribe from tile events."""
        events_received = []

        def handler(event):
            events_received.append(event)

        small_grid.subscribe_to_event(TileEventType.ENTERED, handler)
        small_grid.unsubscribe_from_event(TileEventType.ENTERED, handler)

        entity = Entity(id="test", name="Test", entity_type=EntityType.ITEM)
        small_grid.place_entity(entity, Position(5, 5, 0))

        assert len(events_received) == 0

    @pytest.mark.unit
    def test_move_entity_emits_events(self, small_grid):
        """Moving entity emits exit and enter events."""
        entered_events = []
        exited_events = []

        small_grid.subscribe_to_event(TileEventType.ENTERED, lambda e: entered_events.append(e))
        small_grid.subscribe_to_event(TileEventType.EXITED, lambda e: exited_events.append(e))

        entity = Entity(id="test", name="Test", entity_type=EntityType.ITEM)
        small_grid.place_entity(entity, Position(5, 5, 0))
        small_grid.move_entity(entity, Position(6, 6, 0))

        assert len(entered_events) == 2  # Initial placement + move
        assert len(exited_events) == 1   # Move


class TestTileGridIteration:
    """Tests for grid iteration and queries."""

    @pytest.mark.unit
    def test_all_tiles_iteration(self, small_grid):
        """Can iterate over all tiles."""
        count = 0
        for tile in small_grid.all_tiles():
            count += 1

        assert count == 10 * 10 * 1

    @pytest.mark.unit
    def test_find_tiles_by_predicate(self, grid_with_water):
        """Can find tiles matching predicate."""
        water_tiles = grid_with_water.find_tiles(
            lambda t: t.terrain_type == TerrainType.WATER
        )
        assert len(water_tiles) == 5 * 5  # 5x5 water region

    @pytest.mark.unit
    def test_find_tiles_with_limit(self, grid_with_water):
        """Can limit find results."""
        water_tiles = grid_with_water.find_tiles(
            lambda t: t.terrain_type == TerrainType.WATER,
            limit=5
        )
        assert len(water_tiles) == 5

    @pytest.mark.unit
    def test_find_tiles_by_terrain(self, grid_with_obstacles):
        """Can find tiles by terrain type."""
        rock_tiles = grid_with_obstacles.find_tiles_by_terrain(TerrainType.ROCK)
        assert len(rock_tiles) == 5  # 5 tiles in wall

    @pytest.mark.unit
    def test_find_tiles_with_affordance(self, medium_grid):
        """Can find tiles with specific affordance."""
        # Soil tiles have "diggable"
        diggable = medium_grid.find_tiles_with_affordance("diggable")
        assert len(diggable) > 0

    @pytest.mark.unit
    def test_get_passable_tiles(self, grid_with_obstacles):
        """Can get all passable tiles."""
        passable = grid_with_obstacles.get_passable_tiles()
        # Total tiles minus rock wall
        expected = 50 * 50 - 5
        assert len(passable) == expected


class TestTileGridFillRect:
    """Tests for fill_rect operation."""

    @pytest.mark.unit
    def test_fill_rect(self, medium_grid):
        """Can fill rectangular region."""
        count = medium_grid.fill_rect(5, 5, 10, 10, TerrainType.WATER)
        assert count == 6 * 6  # 6x6 area

        for x in range(5, 11):
            for y in range(5, 11):
                tile = medium_grid.get_tile(x, y, 0)
                assert tile.terrain_type == TerrainType.WATER

    @pytest.mark.unit
    def test_fill_rect_reversed_coords(self, medium_grid):
        """Fill rect works with reversed coordinates."""
        count = medium_grid.fill_rect(10, 10, 5, 5, TerrainType.ROCK)
        assert count == 6 * 6


class TestTileGridSerialization:
    """Tests for grid serialization."""

    @pytest.mark.unit
    def test_serialize_grid(self, populated_grid):
        """Can serialize grid to dict."""
        data = populated_grid.serialize()
        assert "dimensions" in data
        assert "default_terrain" in data
        assert "tiles" in data
        assert "entities" in data

    @pytest.mark.unit
    def test_serialize_dimensions(self, multi_level_grid):
        """Dimensions are correctly serialized."""
        data = multi_level_grid.serialize()
        assert data["dimensions"] == [20, 20, 3]

    @pytest.mark.unit
    def test_from_dict(self, populated_grid):
        """Can deserialize grid from dict."""
        data = populated_grid.serialize()
        restored = TileGrid.from_dict(data)

        assert restored.width == populated_grid.width
        assert restored.height == populated_grid.height
        assert restored.depth == populated_grid.depth

    @pytest.mark.unit
    def test_grid_roundtrip(self, grid_with_water):
        """Grid survives serialization roundtrip."""
        data = grid_with_water.serialize()
        restored = TileGrid.from_dict(data)

        # Check water tiles are preserved
        water_tiles = restored.find_tiles_by_terrain(TerrainType.WATER)
        assert len(water_tiles) == 5 * 5


class TestTileGridPathfinding:
    """Tests for pathfinding integration."""

    @pytest.mark.unit
    def test_find_path_straight(self, medium_grid):
        """Can find straight path."""
        start = medium_grid.get_tile(5, 5, 0)
        end = medium_grid.get_tile(10, 5, 0)
        path = medium_grid.find_path(start, end)

        assert path is not None
        assert path[0] == start
        assert path[-1] == end

    @pytest.mark.unit
    def test_find_path_around_obstacle(self, grid_with_obstacles):
        """Can find path around obstacles."""
        start = grid_with_obstacles.get_tile(5, 10, 0)
        end = grid_with_obstacles.get_tile(20, 10, 0)
        path = grid_with_obstacles.find_path(start, end)

        assert path is not None
        assert path[0] == start
        assert path[-1] == end
        # Path should avoid rock tiles
        for tile in path:
            assert tile.terrain_type != TerrainType.ROCK

    @pytest.mark.unit
    def test_find_path_no_path(self, small_grid, grid_helpers):
        """Returns None when no path exists."""
        # Block off the destination completely
        blocked = grid_helpers.create_path_grid(10, 10, [
            (4, 4), (5, 4), (6, 4),
            (4, 5),        (6, 5),
            (4, 6), (5, 6), (6, 6),
        ])
        blocked.get_tile(5, 5, 0)  # Ensure center exists but is surrounded

        start = blocked.get_tile(0, 0, 0)
        end = blocked.get_tile(5, 5, 0)
        path = blocked.find_path(start, end)

        assert path is None
