"""
Pathfinding algorithms for the tile grid system.
"""

from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
import heapq
import math

if TYPE_CHECKING:
    from .grid import TileGrid
    from .tile import Tile
    from .entity import Entity

from .position import Position
from .terrain import TERRAIN_COST


def calculate_movement_cost(
    from_tile: "Tile",
    to_tile: "Tile",
    entity: Optional["Entity"] = None
) -> float:
    """
    Calculate movement cost between two adjacent tiles.

    Args:
        from_tile: Source tile
        to_tile: Destination tile
        entity: Entity that will traverse (affects movement costs)

    Returns:
        Movement cost (1.0 is standard, higher is slower, 999+ is impassable)
    """
    # Check if destination is passable
    if not to_tile.is_passable():
        return float('inf')

    # Base cost from terrain
    base_cost = TERRAIN_COST.get(to_tile.terrain_type, 1.0)

    if base_cost >= 999.0:
        return float('inf')

    # Height difference cost
    height_diff = abs(to_tile.height - from_tile.height)
    base_cost += height_diff * 0.5

    # Diagonal movement cost (slightly higher)
    dx = abs(to_tile.position.x - from_tile.position.x)
    dy = abs(to_tile.position.y - from_tile.position.y)
    if dx > 0 and dy > 0:
        base_cost *= 1.414  # sqrt(2) for diagonal

    # Environmental modifiers
    if to_tile.environment.moisture > 0.7:
        base_cost *= 1.5  # Harder to move in water

    if to_tile.environment.light_level < 0.2:
        base_cost *= 1.2  # Slower in darkness

    # Terrain modifier effects
    for modifier in to_tile.modifiers:
        effects = modifier.get_effects()
        if "movement_cost_modifier" in effects:
            base_cost *= effects["movement_cost_modifier"]

    # Entity-specific modifiers
    if entity and entity.movement_modifiers:
        terrain_mod = entity.movement_modifiers.get(to_tile.terrain_type.name, 1.0)
        base_cost *= terrain_mod

    return base_cost


def heuristic(a: Position, b: Position) -> float:
    """
    Calculate heuristic distance for A* pathfinding.

    Uses Euclidean distance.
    """
    return a.distance_to(b, include_z=True)


def find_path(
    grid: "TileGrid",
    start: "Tile" | Position,
    end: "Tile" | Position,
    entity: Optional["Entity"] = None,
    max_cost: float = float('inf')
) -> Optional[List["Tile"]]:
    """
    Find path between two positions using A* algorithm.

    Args:
        grid: The tile grid
        start: Starting tile or position
        end: Ending tile or position
        entity: Entity that will traverse (affects movement costs)
        max_cost: Maximum total path cost allowed

    Returns:
        List of tiles forming path (including start and end),
        or None if no path exists
    """
    # Convert positions to tiles
    if isinstance(start, Position):
        start_tile = grid.get_tile_at_position(start)
    else:
        start_tile = start

    if isinstance(end, Position):
        end_tile = grid.get_tile_at_position(end)
    else:
        end_tile = end

    if not start_tile or not end_tile:
        return None

    # Check if end is reachable (passable or entity at destination)
    if not end_tile.is_passable():
        return None

    start_pos = start_tile.position
    end_pos = end_tile.position

    # A* algorithm
    open_set = []
    heapq.heappush(open_set, (0, id(start_tile), start_tile))

    came_from: dict[Position, "Tile"] = {}
    g_score: dict[Position, float] = {start_pos: 0}
    f_score: dict[Position, float] = {start_pos: heuristic(start_pos, end_pos)}

    closed_set: set[Position] = set()

    while open_set:
        _, _, current = heapq.heappop(open_set)
        current_pos = current.position

        if current_pos in closed_set:
            continue

        if current_pos == end_pos:
            # Reconstruct path
            path = [current]
            while current_pos in came_from:
                current = came_from[current_pos]
                current_pos = current.position
                path.append(current)
            path.reverse()
            return path

        closed_set.add(current_pos)

        # Check max cost
        if g_score.get(current_pos, float('inf')) > max_cost:
            continue

        # Explore neighbors
        for neighbor in grid.get_adjacent(current, include_diagonals=True):
            neighbor_pos = neighbor.position

            if neighbor_pos in closed_set:
                continue

            # Calculate movement cost
            move_cost = calculate_movement_cost(current, neighbor, entity)
            if move_cost >= float('inf'):
                continue

            tentative_g = g_score.get(current_pos, float('inf')) + move_cost

            if tentative_g < g_score.get(neighbor_pos, float('inf')):
                came_from[neighbor_pos] = current
                g_score[neighbor_pos] = tentative_g
                f = tentative_g + heuristic(neighbor_pos, end_pos)
                f_score[neighbor_pos] = f
                heapq.heappush(open_set, (f, id(neighbor), neighbor))

    return None  # No path found


def get_line_of_sight(
    grid: "TileGrid",
    from_pos: Position,
    to_pos: Position,
    check_opacity: bool = True
) -> List["Tile"]:
    """
    Get tiles along line of sight between two positions.

    Uses Bresenham's line algorithm.

    Args:
        grid: The tile grid
        from_pos: Starting position
        to_pos: Ending position
        check_opacity: Whether to stop at opaque tiles

    Returns:
        List of tiles along the line (may be truncated if blocked)
    """
    from_tile = grid.get_tile_at_position(from_pos)
    to_tile = grid.get_tile_at_position(to_pos)

    if not from_tile or not to_tile:
        return []

    return grid.get_line_of_sight(from_tile, to_tile, check_opacity)


def flood_fill(
    grid: "TileGrid",
    start: Position,
    predicate: callable,
    max_tiles: int = 1000
) -> List["Tile"]:
    """
    Perform flood fill from a starting position.

    Args:
        grid: The tile grid
        start: Starting position
        predicate: Function(tile) -> bool to determine if tile is included
        max_tiles: Maximum tiles to include

    Returns:
        List of tiles reachable by flood fill
    """
    start_tile = grid.get_tile_at_position(start)
    if not start_tile or not predicate(start_tile):
        return []

    visited: set[Position] = set()
    result: List["Tile"] = []
    queue: List["Tile"] = [start_tile]

    while queue and len(result) < max_tiles:
        current = queue.pop(0)
        current_pos = current.position

        if current_pos in visited:
            continue

        visited.add(current_pos)

        if predicate(current):
            result.append(current)

            # Add neighbors to queue
            for neighbor in grid.get_adjacent(current, include_diagonals=False):
                if neighbor.position not in visited:
                    queue.append(neighbor)

    return result


def get_reachable_tiles(
    grid: "TileGrid",
    start: Position,
    max_movement: float,
    entity: Optional["Entity"] = None
) -> dict[Position, float]:
    """
    Get all tiles reachable within a movement budget.

    Uses Dijkstra's algorithm.

    Args:
        grid: The tile grid
        start: Starting position
        max_movement: Maximum movement cost allowed
        entity: Entity that will traverse

    Returns:
        Dictionary mapping positions to their movement cost from start
    """
    start_tile = grid.get_tile_at_position(start)
    if not start_tile:
        return {}

    distances: dict[Position, float] = {start: 0}
    visited: set[Position] = set()
    heap = [(0, id(start_tile), start_tile)]

    while heap:
        dist, _, current = heapq.heappop(heap)
        current_pos = current.position

        if current_pos in visited:
            continue

        visited.add(current_pos)

        for neighbor in grid.get_adjacent(current, include_diagonals=True):
            neighbor_pos = neighbor.position

            if neighbor_pos in visited:
                continue

            move_cost = calculate_movement_cost(current, neighbor, entity)
            if move_cost >= float('inf'):
                continue

            new_dist = dist + move_cost
            if new_dist <= max_movement and new_dist < distances.get(neighbor_pos, float('inf')):
                distances[neighbor_pos] = new_dist
                heapq.heappush(heap, (new_dist, id(neighbor), neighbor))

    return distances


def calculate_path_cost(
    path: List["Tile"],
    entity: Optional["Entity"] = None
) -> float:
    """
    Calculate total movement cost for a path.

    Args:
        path: List of tiles forming the path
        entity: Entity that will traverse

    Returns:
        Total movement cost
    """
    if len(path) < 2:
        return 0.0

    total = 0.0
    for i in range(len(path) - 1):
        cost = calculate_movement_cost(path[i], path[i + 1], entity)
        if cost >= float('inf'):
            return float('inf')
        total += cost

    return total
