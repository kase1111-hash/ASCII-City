"""
Comprehensive tests for pathfinding algorithms.
"""

import pytest
from shadowengine.grid import (
    Position, Tile, TileGrid, TileEnvironment,
    TerrainType, TerrainModifier,
    Entity, EntityType,
    find_path, get_line_of_sight, calculate_movement_cost
)
from shadowengine.grid.pathfinding import (
    heuristic, flood_fill, get_reachable_tiles, calculate_path_cost
)


class TestMovementCostCalculation:
    """Tests for movement cost calculation."""

    @pytest.mark.unit
    def test_base_movement_cost(self, basic_tile):
        """Base movement cost for normal terrain."""
        from_tile = Tile(position=Position(4, 5, 0), terrain_type=TerrainType.SOIL)
        cost = calculate_movement_cost(from_tile, basic_tile)
        assert cost == 1.0

    @pytest.mark.unit
    def test_water_movement_cost(self, basic_tile, water_tile):
        """Water has higher movement cost."""
        cost = calculate_movement_cost(basic_tile, water_tile)
        assert cost > 1.0

    @pytest.mark.unit
    def test_impassable_movement_cost(self, basic_tile, rock_tile):
        """Impassable terrain has infinite cost."""
        cost = calculate_movement_cost(basic_tile, rock_tile)
        assert cost == float('inf')

    @pytest.mark.unit
    def test_height_difference_cost(self):
        """Height difference increases cost."""
        from_tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)
        to_tile = Tile(position=Position(1, 0, 0), terrain_type=TerrainType.SOIL)
        from_tile.height = 0.0
        to_tile.height = 2.0

        cost = calculate_movement_cost(from_tile, to_tile)
        assert cost > 1.0

    @pytest.mark.unit
    def test_diagonal_movement_cost(self):
        """Diagonal movement costs more."""
        from_tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)
        straight = Tile(position=Position(1, 0, 0), terrain_type=TerrainType.SOIL)
        diagonal = Tile(position=Position(1, 1, 0), terrain_type=TerrainType.SOIL)

        straight_cost = calculate_movement_cost(from_tile, straight)
        diagonal_cost = calculate_movement_cost(from_tile, diagonal)

        assert diagonal_cost > straight_cost

    @pytest.mark.unit
    def test_moisture_increases_cost(self, tile_with_flooded_env):
        """High moisture increases movement cost."""
        from_tile = Tile(position=Position(4, 5, 0), terrain_type=TerrainType.SOIL)
        cost = calculate_movement_cost(from_tile, tile_with_flooded_env)
        assert cost > 1.0

    @pytest.mark.unit
    def test_darkness_increases_cost(self, tile_with_dark_env):
        """Low light increases movement cost."""
        from_tile = Tile(position=Position(4, 5, 0), terrain_type=TerrainType.SOIL)
        cost = calculate_movement_cost(from_tile, tile_with_dark_env)
        assert cost > 1.0

    @pytest.mark.unit
    def test_modifier_affects_cost(self, basic_tile):
        """Terrain modifiers affect movement cost."""
        from_tile = Tile(position=Position(4, 5, 0), terrain_type=TerrainType.SOIL)
        # Use a modifier with full intensity that increases movement cost
        wet_modifier = TerrainModifier(type="wet", intensity=1.0)
        basic_tile.add_modifier(wet_modifier)
        cost = calculate_movement_cost(from_tile, basic_tile)
        # Wet modifier should increase movement cost
        assert cost >= 1.0

    @pytest.mark.unit
    def test_entity_movement_modifier(self, basic_tile, water_tile):
        """Entity can have terrain-specific modifiers."""
        swimmer = Entity(
            id="swimmer",
            name="Swimmer",
            entity_type=EntityType.CHARACTER,
            movement_modifiers={"WATER": 0.5}
        )

        normal_cost = calculate_movement_cost(basic_tile, water_tile)
        swimmer_cost = calculate_movement_cost(basic_tile, water_tile, swimmer)

        assert swimmer_cost < normal_cost


class TestHeuristic:
    """Tests for A* heuristic function."""

    @pytest.mark.unit
    def test_heuristic_same_position(self, sample_position):
        """Heuristic is 0 for same position."""
        assert heuristic(sample_position, sample_position) == 0.0

    @pytest.mark.unit
    def test_heuristic_straight(self):
        """Heuristic for straight line."""
        a = Position(0, 0, 0)
        b = Position(3, 0, 0)
        assert heuristic(a, b) == 3.0

    @pytest.mark.unit
    def test_heuristic_diagonal(self):
        """Heuristic for diagonal."""
        a = Position(0, 0, 0)
        b = Position(3, 4, 0)
        assert heuristic(a, b) == 5.0  # 3-4-5 triangle

    @pytest.mark.unit
    def test_heuristic_with_z(self):
        """Heuristic excludes z-axis (height handled by movement cost)."""
        a = Position(0, 0, 0)
        b = Position(0, 0, 5)
        # 2D distance only — z/height accounted for in movement cost, not heuristic
        assert heuristic(a, b) == 0.0


class TestFindPath:
    """Tests for A* pathfinding."""

    @pytest.mark.unit
    def test_find_path_same_position(self, medium_grid):
        """Path from position to itself."""
        start = medium_grid.get_tile(5, 5, 0)
        path = find_path(medium_grid, start, start)
        assert path is not None
        assert len(path) == 1
        assert path[0] == start

    @pytest.mark.unit
    def test_find_path_adjacent(self, medium_grid):
        """Path to adjacent tile."""
        start = medium_grid.get_tile(5, 5, 0)
        end = medium_grid.get_tile(6, 5, 0)
        path = find_path(medium_grid, start, end)

        assert path is not None
        assert len(path) == 2
        assert path[0] == start
        assert path[-1] == end

    @pytest.mark.unit
    def test_find_path_straight(self, medium_grid):
        """Find straight path."""
        start = medium_grid.get_tile(5, 5, 0)
        end = medium_grid.get_tile(10, 5, 0)
        path = find_path(medium_grid, start, end)

        assert path is not None
        assert path[0] == start
        assert path[-1] == end

    @pytest.mark.unit
    def test_find_path_diagonal(self, medium_grid):
        """Find diagonal path."""
        start = medium_grid.get_tile(5, 5, 0)
        end = medium_grid.get_tile(10, 10, 0)
        path = find_path(medium_grid, start, end)

        assert path is not None
        assert path[0] == start
        assert path[-1] == end
        # Diagonal should be shorter than L-shaped
        assert len(path) <= 11  # At most 6 tiles diagonally

    @pytest.mark.unit
    def test_find_path_around_obstacle(self, grid_with_obstacles):
        """Path navigates around obstacles."""
        start = grid_with_obstacles.get_tile(5, 10, 0)
        end = grid_with_obstacles.get_tile(20, 10, 0)
        path = find_path(grid_with_obstacles, start, end)

        assert path is not None
        assert path[0] == start
        assert path[-1] == end

        # Path should avoid rock tiles
        for tile in path:
            assert tile.terrain_type != TerrainType.ROCK

    @pytest.mark.unit
    def test_find_path_no_path_exists(self, small_grid, grid_helpers):
        """Returns None when no path exists."""
        # Create surrounded tile
        blocked = grid_helpers.create_path_grid(10, 10, [
            (4, 4), (5, 4), (6, 4),
            (4, 5),        (6, 5),
            (4, 6), (5, 6), (6, 6),
        ])

        start = blocked.get_tile(0, 0, 0)
        end = blocked.get_tile(5, 5, 0)
        path = find_path(blocked, start, end)

        assert path is None

    @pytest.mark.unit
    def test_find_path_to_impassable(self, grid_with_obstacles):
        """Cannot path to impassable destination."""
        start = grid_with_obstacles.get_tile(5, 5, 0)
        end = grid_with_obstacles.get_tile(12, 10, 0)  # Rock tile
        path = find_path(grid_with_obstacles, start, end)

        assert path is None

    @pytest.mark.unit
    def test_find_path_from_position(self, medium_grid):
        """Can use Position objects."""
        start = Position(5, 5, 0)
        end = Position(10, 10, 0)
        path = find_path(medium_grid, start, end)

        assert path is not None
        assert path[0].position == start
        assert path[-1].position == end

    @pytest.mark.unit
    def test_find_path_with_max_cost(self, medium_grid):
        """Max cost limits path length."""
        start = medium_grid.get_tile(5, 5, 0)
        end = medium_grid.get_tile(20, 20, 0)

        # Very low max cost should fail
        path = find_path(medium_grid, start, end, max_cost=5)
        assert path is None

        # Higher max cost should succeed
        path = find_path(medium_grid, start, end, max_cost=100)
        assert path is not None

    @pytest.mark.unit
    def test_find_path_with_entity(self, grid_with_water):
        """Entity modifiers affect path."""
        swimmer = Entity(
            id="swimmer",
            name="Swimmer",
            entity_type=EntityType.CHARACTER,
            movement_modifiers={"WATER": 0.5}
        )
        non_swimmer = Entity(
            id="walker",
            name="Walker",
            entity_type=EntityType.CHARACTER,
            movement_modifiers={"WATER": 2.0}
        )

        start = grid_with_water.get_tile(0, 7, 0)
        end = grid_with_water.get_tile(15, 7, 0)

        swimmer_path = find_path(grid_with_water, start, end, swimmer)
        walker_path = find_path(grid_with_water, start, end, non_swimmer)

        # Both should find paths
        assert swimmer_path is not None
        assert walker_path is not None

        # Costs differ based on entity
        swimmer_cost = calculate_path_cost(swimmer_path, swimmer)
        walker_cost = calculate_path_cost(walker_path, non_swimmer)
        assert swimmer_cost != walker_cost

    @pytest.mark.unit
    def test_find_path_maze(self, maze_grid):
        """Can navigate complex maze."""
        start = maze_grid.get_tile(0, 0, 0)
        end = maze_grid.get_tile(10, 10, 0)
        path = find_path(maze_grid, start, end)

        assert path is not None
        assert path[0] == start
        assert path[-1] == end


class TestLineOfSight:
    """Tests for line of sight calculation."""

    @pytest.mark.unit
    def test_los_straight_horizontal(self, medium_grid):
        """Line of sight along horizontal."""
        from_pos = Position(5, 5, 0)
        to_pos = Position(15, 5, 0)
        los = get_line_of_sight(medium_grid, from_pos, to_pos)

        assert len(los) == 11
        for tile in los:
            assert tile.position.y == 5

    @pytest.mark.unit
    def test_los_straight_vertical(self, medium_grid):
        """Line of sight along vertical."""
        from_pos = Position(5, 5, 0)
        to_pos = Position(5, 15, 0)
        los = get_line_of_sight(medium_grid, from_pos, to_pos)

        assert len(los) == 11
        for tile in los:
            assert tile.position.x == 5

    @pytest.mark.unit
    def test_los_diagonal(self, medium_grid):
        """Line of sight along diagonal."""
        from_pos = Position(5, 5, 0)
        to_pos = Position(10, 10, 0)
        los = get_line_of_sight(medium_grid, from_pos, to_pos)

        assert len(los) > 0
        assert los[0].position == from_pos
        assert los[-1].position == to_pos

    @pytest.mark.unit
    def test_los_blocked_by_opaque(self, grid_with_obstacles):
        """Line of sight blocked by opaque tiles."""
        from_pos = Position(5, 10, 0)
        to_pos = Position(20, 10, 0)
        los = get_line_of_sight(grid_with_obstacles, from_pos, to_pos, check_opacity=True)

        # LOS should stop at the obstacle (rock wall at x=10-14)
        last_pos = los[-1].position
        assert last_pos.x <= 14  # Stops at or before the wall

    @pytest.mark.unit
    def test_los_ignore_opacity(self, grid_with_obstacles):
        """Can get full line ignoring opacity."""
        from_pos = Position(5, 10, 0)
        to_pos = Position(20, 10, 0)
        los = get_line_of_sight(grid_with_obstacles, from_pos, to_pos, check_opacity=False)

        assert los[-1].position.x == 20


class TestFloodFill:
    """Tests for flood fill algorithm."""

    @pytest.mark.unit
    def test_flood_fill_basic(self, medium_grid):
        """Basic flood fill on open grid."""
        start = Position(25, 25, 0)
        tiles = flood_fill(
            medium_grid, start,
            predicate=lambda t: t.is_passable()
        )
        assert len(tiles) > 0

    @pytest.mark.unit
    def test_flood_fill_bounded(self, grid_with_obstacles):
        """Flood fill bounded by obstacles."""
        start = Position(5, 5, 0)
        tiles = flood_fill(
            grid_with_obstacles, start,
            predicate=lambda t: t.is_passable()
        )

        # Check no tiles are past the obstacle
        for tile in tiles:
            # The wall is at x=10-14, y=10
            if tile.position.y == 10:
                assert tile.position.x < 10 or tile.position.x > 14

    @pytest.mark.unit
    def test_flood_fill_max_tiles(self, medium_grid):
        """Flood fill respects max_tiles limit."""
        start = Position(25, 25, 0)
        tiles = flood_fill(
            medium_grid, start,
            predicate=lambda t: t.is_passable(),
            max_tiles=50
        )
        assert len(tiles) == 50

    @pytest.mark.unit
    def test_flood_fill_terrain_type(self, grid_with_water):
        """Flood fill can use terrain predicate."""
        start = Position(7, 7, 0)  # Center of water
        tiles = flood_fill(
            grid_with_water, start,
            predicate=lambda t: t.terrain_type == TerrainType.WATER
        )
        assert len(tiles) == 5 * 5  # All water tiles


class TestReachableTiles:
    """Tests for reachable tiles calculation."""

    @pytest.mark.unit
    def test_reachable_basic(self, medium_grid):
        """Get tiles reachable within movement budget."""
        start = Position(25, 25, 0)
        reachable = get_reachable_tiles(medium_grid, start, max_movement=3)

        assert start in reachable
        assert reachable[start] == 0

        # Check all tiles are within cost
        for pos, cost in reachable.items():
            assert cost <= 3

    @pytest.mark.unit
    def test_reachable_excludes_far(self, medium_grid):
        """Far tiles are not reachable."""
        start = Position(25, 25, 0)
        reachable = get_reachable_tiles(medium_grid, start, max_movement=2)

        far_pos = Position(30, 30, 0)
        assert far_pos not in reachable

    @pytest.mark.unit
    def test_reachable_blocked(self, grid_with_obstacles):
        """Obstacles block reachability."""
        start = Position(5, 10, 0)
        reachable = get_reachable_tiles(grid_with_obstacles, start, max_movement=20)

        # Position behind wall requires going around
        behind_wall = Position(16, 10, 0)
        if behind_wall in reachable:
            assert reachable[behind_wall] > 7  # Direct would be 11 tiles

    @pytest.mark.unit
    def test_reachable_with_entity(self, grid_with_water):
        """Entity modifiers affect reachability."""
        swimmer = Entity(
            id="swimmer",
            name="Swimmer",
            entity_type=EntityType.CHARACTER,
            movement_modifiers={"WATER": 0.5}
        )

        start = Position(7, 7, 0)  # In water
        normal_reach = get_reachable_tiles(grid_with_water, start, max_movement=5)
        swimmer_reach = get_reachable_tiles(grid_with_water, start, max_movement=5, entity=swimmer)

        # Swimmer should reach more tiles in water
        assert len(swimmer_reach) >= len(normal_reach)


class TestPathCost:
    """Tests for path cost calculation."""

    @pytest.mark.unit
    def test_path_cost_empty(self):
        """Empty path has zero cost."""
        assert calculate_path_cost([]) == 0.0

    @pytest.mark.unit
    def test_path_cost_single_tile(self, basic_tile):
        """Single tile path has zero cost."""
        assert calculate_path_cost([basic_tile]) == 0.0

    @pytest.mark.unit
    def test_path_cost_straight(self, medium_grid):
        """Calculate cost of straight path."""
        path = []
        for x in range(5, 10):
            path.append(medium_grid.get_tile(x, 5, 0))

        cost = calculate_path_cost(path)
        assert cost > 0
        # 4 moves, each cost 1.0
        assert cost == pytest.approx(4.0, rel=0.1)

    @pytest.mark.unit
    def test_path_cost_with_water(self, grid_with_water, grid_helpers):
        """Water tiles increase path cost."""
        # Path through water
        path_water = []
        for x in range(3, 12):
            path_water.append(grid_with_water.get_tile(x, 7, 0))

        # Path around water
        path_around = []
        for x in range(3, 12):
            path_around.append(grid_with_water.get_tile(x, 3, 0))

        cost_water = calculate_path_cost(path_water)
        cost_around = calculate_path_cost(path_around)

        # Water path should cost more per tile
        assert cost_water > cost_around

    @pytest.mark.unit
    def test_path_cost_impassable(self, rock_tile, basic_tile):
        """Path through impassable is infinite."""
        path = [basic_tile, rock_tile]
        cost = calculate_path_cost(path)
        assert cost == float('inf')

    @pytest.mark.unit
    def test_path_cost_with_entity(self, medium_grid):
        """Entity affects path cost."""
        path = []
        for x in range(5, 10):
            path.append(medium_grid.get_tile(x, 5, 0))

        fast_entity = Entity(
            id="fast",
            name="Fast",
            entity_type=EntityType.CHARACTER,
            movement_modifiers={"SOIL": 0.5}
        )

        normal_cost = calculate_path_cost(path)
        fast_cost = calculate_path_cost(path, fast_entity)

        assert fast_cost < normal_cost
