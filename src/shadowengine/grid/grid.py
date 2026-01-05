"""
TileGrid class for managing the game world.

Provides spatial queries, pathfinding, and entity management.
"""

from dataclasses import dataclass, field
from typing import Optional, Iterator, Callable
import heapq
import math

from .tile import Tile, Position, TileEnvironment, DIRECTIONS
from .terrain import TerrainType, TerrainModifier
from .entity import Entity, Layer, MAX_LAYER_SIZE
from .events import TileEventBus, TileEvent, TileEventType


@dataclass
class GridDimensions:
    """Dimensions of the grid."""
    width: int
    height: int
    depth: int = 1  # Number of Z levels (1 = single level)

    def contains(self, pos: Position) -> bool:
        """Check if position is within bounds."""
        return (
            0 <= pos.x < self.width and
            0 <= pos.y < self.height and
            0 <= pos.z < self.depth
        )

    def to_dict(self) -> dict:
        return {"width": self.width, "height": self.height, "depth": self.depth}


class TileGrid:
    """
    The game world grid.

    Manages tiles, entities, and provides spatial queries.
    """

    def __init__(
        self,
        width: int,
        height: int,
        depth: int = 1,
        default_terrain: TerrainType = TerrainType.FLOOR
    ):
        self.dimensions = GridDimensions(width, height, depth)
        self.default_terrain = default_terrain

        # Tile storage - sparse dict for memory efficiency
        self._tiles: dict[str, Tile] = {}

        # Entity storage
        self._entities: dict[str, Entity] = {}
        self._entity_positions: dict[str, Position] = {}

        # Event system
        self.events = TileEventBus()

        # Statistics
        self.stats = {
            "tiles_created": 0,
            "entities_placed": 0,
            "pathfinding_calls": 0,
        }

    @property
    def width(self) -> int:
        return self.dimensions.width

    @property
    def height(self) -> int:
        return self.dimensions.height

    @property
    def depth(self) -> int:
        return self.dimensions.depth

    def _pos_key(self, pos: Position) -> str:
        """Get storage key for a position."""
        return pos.to_key()

    def get_tile(self, x: int, y: int, z: int = 0) -> Optional[Tile]:
        """Get tile at position, creating if needed within bounds."""
        pos = Position(x, y, z)
        if not self.dimensions.contains(pos):
            return None

        key = self._pos_key(pos)
        if key not in self._tiles:
            # Create new tile with default terrain
            tile = Tile(position=pos, terrain_type=self.default_terrain)
            self._tiles[key] = tile
            self.stats["tiles_created"] += 1

        return self._tiles[key]

    def get_tile_at(self, pos: Position) -> Optional[Tile]:
        """Get tile at a Position object."""
        return self.get_tile(pos.x, pos.y, pos.z)

    def set_tile(self, tile: Tile) -> bool:
        """Set a tile at its position. Returns False if out of bounds."""
        if not self.dimensions.contains(tile.position):
            return False
        self._tiles[self._pos_key(tile.position)] = tile
        return True

    def has_tile(self, x: int, y: int, z: int = 0) -> bool:
        """Check if a tile exists (has been created) at position."""
        return self._pos_key(Position(x, y, z)) in self._tiles

    def remove_tile(self, x: int, y: int, z: int = 0) -> Optional[Tile]:
        """Remove and return tile at position."""
        key = self._pos_key(Position(x, y, z))
        return self._tiles.pop(key, None)

    def get_adjacent(self, tile: Tile, include_diagonals: bool = True) -> list[Tile]:
        """Get adjacent tiles."""
        adjacent = []
        directions = ["north", "south", "east", "west"]
        if include_diagonals:
            directions.extend(["northeast", "northwest", "southeast", "southwest"])

        for direction in directions:
            offset = DIRECTIONS[direction]
            new_pos = tile.position + offset
            adj_tile = self.get_tile_at(new_pos)
            if adj_tile:
                adjacent.append(adj_tile)

        return adjacent

    def get_neighbors(
        self,
        x: int,
        y: int,
        z: int = 0,
        include_diagonals: bool = True
    ) -> list[Tile]:
        """Get neighboring tiles at position."""
        tile = self.get_tile(x, y, z)
        if not tile:
            return []
        return self.get_adjacent(tile, include_diagonals)

    def get_in_radius(
        self,
        center: Position,
        radius: float,
        include_center: bool = True
    ) -> list[Tile]:
        """Get all tiles within a radius of center."""
        tiles = []
        r_int = int(math.ceil(radius))

        for dx in range(-r_int, r_int + 1):
            for dy in range(-r_int, r_int + 1):
                for dz in range(-r_int, r_int + 1):
                    pos = Position(center.x + dx, center.y + dy, center.z + dz)
                    if not include_center and pos == center:
                        continue
                    if center.distance_to(pos) <= radius:
                        tile = self.get_tile_at(pos)
                        if tile:
                            tiles.append(tile)

        return tiles

    def get_in_rect(
        self,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
        z: int = 0
    ) -> list[Tile]:
        """Get all tiles in a rectangular area."""
        tiles = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                tile = self.get_tile(x, y, z)
                if tile:
                    tiles.append(tile)
        return tiles

    def get_line_of_sight(
        self,
        from_pos: Position,
        to_pos: Position
    ) -> list[Tile]:
        """
        Get tiles along a line between two positions.

        Uses Bresenham's line algorithm.
        """
        tiles = []

        dx = abs(to_pos.x - from_pos.x)
        dy = abs(to_pos.y - from_pos.y)
        x, y = from_pos.x, from_pos.y
        sx = 1 if from_pos.x < to_pos.x else -1
        sy = 1 if from_pos.y < to_pos.y else -1

        if dx > dy:
            err = dx / 2
            while x != to_pos.x:
                tile = self.get_tile(x, y, from_pos.z)
                if tile:
                    tiles.append(tile)
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2
            while y != to_pos.y:
                tile = self.get_tile(x, y, from_pos.z)
                if tile:
                    tiles.append(tile)
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy

        # Add final tile
        tile = self.get_tile(to_pos.x, to_pos.y, to_pos.z)
        if tile:
            tiles.append(tile)

        return tiles

    def has_line_of_sight(
        self,
        from_pos: Position,
        to_pos: Position
    ) -> bool:
        """Check if there's an unobstructed line of sight between positions."""
        tiles = self.get_line_of_sight(from_pos, to_pos)
        # Check all tiles except start and end
        for tile in tiles[1:-1]:
            if tile.opaque:
                return False
        return True

    def find_path(
        self,
        start: Position,
        end: Position,
        entity: Optional[Entity] = None,
        max_cost: float = float('inf')
    ) -> list[Tile]:
        """
        Find path between two positions using A*.

        Returns list of tiles from start to end, or empty list if no path.
        """
        self.stats["pathfinding_calls"] += 1

        start_tile = self.get_tile_at(start)
        end_tile = self.get_tile_at(end)

        if not start_tile or not end_tile:
            return []

        # A* implementation
        open_set: list[tuple[float, int, Position]] = []
        counter = 0  # Tiebreaker for equal priorities
        heapq.heappush(open_set, (0, counter, start))

        came_from: dict[str, Position] = {}
        g_score: dict[str, float] = {start.to_key(): 0}
        f_score: dict[str, float] = {start.to_key(): start.distance_to(end)}

        while open_set:
            _, _, current = heapq.heappop(open_set)

            if current == end:
                # Reconstruct path
                path = []
                while current.to_key() in came_from:
                    tile = self.get_tile_at(current)
                    if tile:
                        path.append(tile)
                    current = came_from[current.to_key()]
                path.append(self.get_tile_at(start))
                path.reverse()
                return path

            current_tile = self.get_tile_at(current)
            if not current_tile:
                continue

            for neighbor_tile in self.get_adjacent(current_tile, include_diagonals=True):
                neighbor = neighbor_tile.position

                # Check passability
                if not neighbor_tile.passable:
                    continue

                # Check entity requirements
                if entity and entity.requires_passable and not neighbor_tile.passable:
                    continue

                # Calculate movement cost
                base_cost = neighbor_tile.movement_cost
                if entity:
                    base_cost *= entity.get_movement_modifier(
                        neighbor_tile.terrain_type.value
                    )

                # Diagonal movement costs more
                if neighbor.x != current.x and neighbor.y != current.y:
                    base_cost *= 1.414

                tentative_g = g_score[current.to_key()] + base_cost

                if tentative_g > max_cost:
                    continue

                neighbor_key = neighbor.to_key()
                if neighbor_key not in g_score or tentative_g < g_score[neighbor_key]:
                    came_from[neighbor_key] = current
                    g_score[neighbor_key] = tentative_g
                    f_score[neighbor_key] = tentative_g + neighbor.distance_to(end)
                    counter += 1
                    heapq.heappush(open_set, (f_score[neighbor_key], counter, neighbor))

        return []  # No path found

    # Entity management

    def add_entity(self, entity: Entity, position: Position) -> bool:
        """
        Add an entity to the grid at a position.

        Returns False if placement fails.
        """
        tile = self.get_tile_at(position)
        if not tile:
            return False

        # Check if placement is valid
        if not self.can_place_entity(tile, entity):
            return False

        # Store entity
        self._entities[entity.id] = entity
        self._entity_positions[entity.id] = position

        # Add to tile
        tile.add_entity(entity.id)

        # Emit event
        self.events.emit_entered(position.to_tuple(), entity.id)

        self.stats["entities_placed"] += 1
        return True

    def remove_entity(self, entity_id: str) -> Optional[Entity]:
        """Remove an entity from the grid."""
        if entity_id not in self._entities:
            return None

        entity = self._entities.pop(entity_id)
        position = self._entity_positions.pop(entity_id)

        # Remove from tile
        tile = self.get_tile_at(position)
        if tile:
            tile.remove_entity(entity_id)
            self.events.emit_exited(position.to_tuple(), entity_id)

        return entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self._entities.get(entity_id)

    def get_entity_position(self, entity_id: str) -> Optional[Position]:
        """Get entity's current position."""
        return self._entity_positions.get(entity_id)

    def get_entities_at(self, position: Position) -> list[Entity]:
        """Get all entities at a position."""
        tile = self.get_tile_at(position)
        if not tile:
            return []
        return [self._entities[eid] for eid in tile.entity_ids if eid in self._entities]

    def get_entities_in_radius(
        self,
        center: Position,
        radius: float
    ) -> list[tuple[Entity, Position]]:
        """Get all entities within radius with their positions."""
        result = []
        tiles = self.get_in_radius(center, radius)
        for tile in tiles:
            for entity_id in tile.entity_ids:
                if entity_id in self._entities:
                    result.append((self._entities[entity_id], tile.position))
        return result

    def move_entity(
        self,
        entity_id: str,
        new_position: Position
    ) -> bool:
        """Move an entity to a new position."""
        if entity_id not in self._entities:
            return False

        entity = self._entities[entity_id]
        old_position = self._entity_positions[entity_id]
        new_tile = self.get_tile_at(new_position)

        if not new_tile:
            return False

        if not self.can_place_entity(new_tile, entity):
            return False

        # Remove from old tile
        old_tile = self.get_tile_at(old_position)
        if old_tile:
            old_tile.remove_entity(entity_id)
            self.events.emit_exited(old_position.to_tuple(), entity_id, new_position.to_tuple())

        # Add to new tile
        new_tile.add_entity(entity_id)
        self._entity_positions[entity_id] = new_position
        self.events.emit_entered(new_position.to_tuple(), entity_id, old_position.to_tuple())

        return True

    def can_place_entity(self, tile: Tile, entity: Entity) -> bool:
        """Check if an entity can be placed on a tile."""
        # Check passability requirement
        if entity.requires_passable and not tile.passable:
            return False

        # Check layer conflicts
        same_layer_entities = [
            self._entities[eid] for eid in tile.entity_ids
            if eid in self._entities and self._entities[eid].layer == entity.layer
        ]

        # Check total size on layer
        total_size = sum(e.size.volume() for e in same_layer_entities)
        if total_size + entity.size.volume() > MAX_LAYER_SIZE:
            return False

        # Check specific conflicts
        for existing in same_layer_entities:
            if entity.conflicts_with(existing):
                return False

        return True

    # Iteration

    def all_tiles(self) -> Iterator[Tile]:
        """Iterate over all existing tiles."""
        return iter(self._tiles.values())

    def all_entities(self) -> Iterator[Entity]:
        """Iterate over all entities."""
        return iter(self._entities.values())

    def tiles_matching(
        self,
        predicate: Callable[[Tile], bool]
    ) -> list[Tile]:
        """Get all tiles matching a predicate."""
        return [t for t in self._tiles.values() if predicate(t)]

    def entities_matching(
        self,
        predicate: Callable[[Entity], bool]
    ) -> list[Entity]:
        """Get all entities matching a predicate."""
        return [e for e in self._entities.values() if predicate(e)]

    # Terrain modification

    def set_terrain(
        self,
        x: int,
        y: int,
        z: int,
        terrain_type: TerrainType
    ) -> bool:
        """Set terrain type at position."""
        tile = self.get_tile(x, y, z)
        if not tile:
            return False
        tile.set_terrain(terrain_type)
        self.events.dispatch(TileEvent(
            type=TileEventType.TERRAIN_CHANGED,
            tile_position=(x, y, z),
            data={"terrain": terrain_type.value},
        ))
        return True

    def add_modifier(
        self,
        x: int,
        y: int,
        z: int,
        modifier: TerrainModifier
    ) -> bool:
        """Add a terrain modifier at position."""
        tile = self.get_tile(x, y, z)
        if not tile:
            return False
        tile.add_modifier(modifier)
        self.events.dispatch(TileEvent(
            type=TileEventType.MODIFIER_ADDED,
            tile_position=(x, y, z),
            data={"modifier": modifier.type},
        ))
        return True

    def remove_modifier(
        self,
        x: int,
        y: int,
        z: int,
        modifier_type: str
    ) -> bool:
        """Remove a terrain modifier at position."""
        tile = self.get_tile(x, y, z)
        if not tile:
            return False
        if tile.remove_modifier(modifier_type):
            self.events.dispatch(TileEvent(
                type=TileEventType.MODIFIER_REMOVED,
                tile_position=(x, y, z),
                data={"modifier": modifier_type},
            ))
            return True
        return False

    # Serialization

    def to_dict(self) -> dict:
        """Serialize grid to dictionary."""
        return {
            "dimensions": self.dimensions.to_dict(),
            "default_terrain": self.default_terrain.value,
            "tiles": {key: tile.to_dict() for key, tile in self._tiles.items()},
            "entities": {eid: e.to_dict() for eid, e in self._entities.items()},
            "entity_positions": {
                eid: pos.to_tuple() for eid, pos in self._entity_positions.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TileGrid':
        """Deserialize grid from dictionary."""
        dims = data["dimensions"]
        grid = cls(
            width=dims["width"],
            height=dims["height"],
            depth=dims.get("depth", 1),
            default_terrain=TerrainType(data.get("default_terrain", "floor")),
        )

        # Load tiles
        for key, tile_data in data.get("tiles", {}).items():
            tile = Tile.from_dict(tile_data)
            grid._tiles[key] = tile

        # Load entities
        for entity_id, entity_data in data.get("entities", {}).items():
            entity = Entity.from_dict(entity_data)
            grid._entities[entity_id] = entity

        # Load entity positions
        for entity_id, pos_tuple in data.get("entity_positions", {}).items():
            grid._entity_positions[entity_id] = Position.from_tuple(pos_tuple)

        return grid

    def clear(self) -> None:
        """Clear all tiles and entities."""
        self._tiles.clear()
        self._entities.clear()
        self._entity_positions.clear()
        self.events.clear_history()

    def get_stats(self) -> dict:
        """Get grid statistics."""
        return {
            **self.stats,
            "tiles_count": len(self._tiles),
            "entities_count": len(self._entities),
        }
