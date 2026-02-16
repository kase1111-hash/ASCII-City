"""
TileGrid class - the main grid container and spatial query system.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Iterator, Callable, Dict
import math

from .position import Position
from .tile import Tile
from .terrain import TerrainType
from .entity import Entity
from .events import TileEventManager, TileEvent, TileEventType


@dataclass
class TileGrid:
    """
    The main tile grid container.

    Provides spatial queries, entity management, and pathfinding.

    Attributes:
        width: Grid width (x-axis)
        height: Grid height (y-axis)
        depth: Grid depth (z-axis, number of levels)
        default_terrain: Default terrain for new tiles
    """
    width: int
    height: int
    depth: int = 1
    default_terrain: TerrainType = TerrainType.SOIL

    _tiles: Dict[tuple, Tile] = field(default_factory=dict, repr=False)
    _entities: Dict[str, Entity] = field(default_factory=dict, repr=False)
    _event_manager: TileEventManager = field(default_factory=TileEventManager, repr=False)

    def __post_init__(self):
        """Validate grid dimensions."""
        if self.width <= 0 or self.height <= 0 or self.depth <= 0:
            raise ValueError("Grid dimensions must be positive")

    def _pos_key(self, x: int, y: int, z: int = 0) -> tuple:
        """Create position key for internal storage."""
        return (x, y, z)

    def is_valid_position(self, x: int, y: int, z: int = 0) -> bool:
        """Check if position is within grid bounds."""
        return (0 <= x < self.width and
                0 <= y < self.height and
                0 <= z < self.depth)

    def get_tile(self, x: int, y: int, z: int = 0) -> Optional[Tile]:
        """
        Get tile at position.

        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate (default 0)

        Returns:
            Tile at position, or None if out of bounds
        """
        if not self.is_valid_position(x, y, z):
            return None

        key = self._pos_key(x, y, z)
        if key not in self._tiles:
            # Create tile on demand with default terrain
            position = Position(x, y, z)
            self._tiles[key] = Tile(
                position=position,
                terrain_type=self.default_terrain
            )
        return self._tiles[key]

    def get_tile_at_position(self, position: Position) -> Optional[Tile]:
        """Get tile at a Position object."""
        return self.get_tile(position.x, position.y, position.z)

    def set_tile(self, tile: Tile) -> bool:
        """
        Set a tile in the grid.

        Args:
            tile: Tile to set

        Returns:
            True if tile was set successfully
        """
        pos = tile.position
        if not self.is_valid_position(pos.x, pos.y, pos.z):
            return False

        key = self._pos_key(pos.x, pos.y, pos.z)
        self._tiles[key] = tile
        return True

    def get_adjacent(self, tile: Tile, include_diagonals: bool = True) -> List[Tile]:
        """
        Get tiles adjacent to the given tile.

        Args:
            tile: Center tile
            include_diagonals: Include diagonal neighbors

        Returns:
            List of adjacent tiles
        """
        adjacent = []
        pos = tile.position

        for adj_pos in pos.get_adjacent_positions(include_diagonals=include_diagonals):
            adj_tile = self.get_tile(adj_pos.x, adj_pos.y, adj_pos.z)
            if adj_tile:
                adjacent.append(adj_tile)

        return adjacent

    def get_in_radius(
        self,
        center: Tile | Position,
        radius: float,
        include_center: bool = False
    ) -> List[Tile]:
        """
        Get all tiles within radius of center.

        Args:
            center: Center tile or position
            radius: Radius to search
            include_center: Whether to include center tile

        Returns:
            List of tiles within radius
        """
        if isinstance(center, Tile):
            center_pos = center.position
        else:
            center_pos = center

        tiles = []
        int_radius = int(math.ceil(radius))

        for dx in range(-int_radius, int_radius + 1):
            for dy in range(-int_radius, int_radius + 1):
                x = center_pos.x + dx
                y = center_pos.y + dy
                z = center_pos.z

                if not self.is_valid_position(x, y, z):
                    continue

                pos = Position(x, y, z)
                distance = center_pos.distance_to(pos, include_z=False)

                if distance <= radius:
                    if not include_center and pos == center_pos:
                        continue
                    tile = self.get_tile(x, y, z)
                    if tile:
                        tiles.append(tile)

        return tiles

    def get_line_of_sight(
        self,
        from_tile: Tile,
        to_tile: Tile,
        check_opacity: bool = True
    ) -> List[Tile]:
        """
        Get tiles along line of sight between two tiles.

        Uses Bresenham's line algorithm.

        Args:
            from_tile: Starting tile
            to_tile: Ending tile
            check_opacity: Whether to stop at opaque tiles

        Returns:
            List of tiles along the line (may be truncated if blocked)
        """
        tiles = []

        x0, y0 = from_tile.position.x, from_tile.position.y
        x1, y1 = to_tile.position.x, to_tile.position.y
        z = from_tile.position.z

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            tile = self.get_tile(x0, y0, z)
            if tile:
                tiles.append(tile)

                # Check if blocked by opacity (but not first tile)
                if check_opacity and len(tiles) > 1 and tile.is_opaque():
                    break

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

        return tiles

    def has_line_of_sight(self, from_tile: Tile, to_tile: Tile) -> bool:
        """
        Check if there is unobstructed line of sight between tiles.

        Args:
            from_tile: Starting tile
            to_tile: Ending tile

        Returns:
            True if line of sight exists
        """
        tiles = self.get_line_of_sight(from_tile, to_tile, check_opacity=True)
        if not tiles:
            return False

        # Check if we reached the destination
        return tiles[-1].position == to_tile.position

    def find_path(
        self,
        start: Tile | Position,
        end: Tile | Position,
        entity: Optional[Entity] = None,
        max_cost: float = float('inf')
    ) -> Optional[List[Tile]]:
        """
        Find path between two tiles using A* algorithm.

        Args:
            start: Starting tile or position
            end: Ending tile or position
            entity: Entity that will traverse (affects movement costs)
            max_cost: Maximum path cost allowed

        Returns:
            List of tiles forming path, or None if no path exists
        """
        from .pathfinding import find_path as pathfind
        return pathfind(self, start, end, entity, max_cost)

    def place_entity(self, entity: Entity, position: Position) -> bool:
        """
        Place an entity on the grid.

        Args:
            entity: Entity to place
            position: Position to place at

        Returns:
            True if entity was placed successfully
        """
        tile = self.get_tile_at_position(position)
        if not tile:
            return False

        if not tile.can_place_entity(entity):
            return False

        # Remove from old position if exists
        if entity.id in self._entities:
            old_entity = self._entities[entity.id]
            if old_entity.position:
                old_tile = self.get_tile_at_position(old_entity.position)
                if old_tile:
                    old_tile.remove_entity(old_entity)
                    self._emit_event(TileEventType.EXITED, old_tile, entity)

        # Place on new tile
        if tile.add_entity(entity):
            self._entities[entity.id] = entity
            self._emit_event(TileEventType.ENTERED, tile, entity)
            return True

        return False

    def remove_entity(self, entity: Entity) -> bool:
        """
        Remove an entity from the grid.

        Args:
            entity: Entity to remove

        Returns:
            True if entity was removed
        """
        if entity.id not in self._entities:
            return False

        if entity.position:
            tile = self.get_tile_at_position(entity.position)
            if tile:
                tile.remove_entity(entity)
                self._emit_event(TileEventType.ENTITY_REMOVED, tile, entity)

        del self._entities[entity.id]
        return True

    def move_entity(
        self,
        entity: Entity,
        to_position: Position,
        validate_path: bool = False
    ) -> bool:
        """
        Move an entity to a new position.

        Args:
            entity: Entity to move
            to_position: Destination position
            validate_path: Whether to check for valid path

        Returns:
            True if entity was moved successfully
        """
        if entity.id not in self._entities:
            return False

        from_tile = None
        if entity.position:
            from_tile = self.get_tile_at_position(entity.position)

        to_tile = self.get_tile_at_position(to_position)
        if not to_tile:
            return False

        # Check valid path if requested
        if validate_path and from_tile:
            path = self.find_path(from_tile, to_tile, entity)
            if not path:
                return False

        # Check if can place on destination
        if not to_tile.can_place_entity(entity):
            return False

        # Remove from old tile
        if from_tile:
            from_tile.remove_entity(entity)
            self._emit_event(TileEventType.EXITED, from_tile, entity)

        # Add to new tile
        if not to_tile.add_entity(entity):
            # Placement failed — restore entity to old tile
            if from_tile:
                from_tile.add_entity(entity)
            return False

        self._emit_event(TileEventType.ENTERED, to_tile, entity)
        return True

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def get_entities_at(self, position: Position) -> List[Entity]:
        """Get all entities at a position."""
        tile = self.get_tile_at_position(position)
        if tile:
            return tile.entities.copy()
        return []

    def get_all_entities(self) -> List[Entity]:
        """Get all entities in the grid."""
        return list(self._entities.values())

    def _emit_event(
        self,
        event_type: TileEventType,
        tile: Tile,
        cause: Optional[Entity] = None,
        data: Optional[dict] = None
    ) -> None:
        """Emit a tile event."""
        event = TileEvent(
            event_type=event_type,
            tile=tile,
            cause=cause,
            data=data or {}
        )
        self._event_manager.emit(event)

    def subscribe_to_event(
        self,
        event_type: TileEventType,
        handler: Callable[[TileEvent], None]
    ) -> None:
        """Subscribe to tile events."""
        self._event_manager.subscribe(event_type, handler)

    def unsubscribe_from_event(
        self,
        event_type: TileEventType,
        handler: Callable[[TileEvent], None]
    ) -> bool:
        """Unsubscribe from tile events."""
        return self._event_manager.unsubscribe(event_type, handler)

    def all_tiles(self) -> Iterator[Tile]:
        """Iterate over all tiles in the grid."""
        for z in range(self.depth):
            for y in range(self.height):
                for x in range(self.width):
                    tile = self.get_tile(x, y, z)
                    if tile:
                        yield tile

    def find_tiles(
        self,
        predicate: Callable[[Tile], bool],
        limit: Optional[int] = None
    ) -> List[Tile]:
        """
        Find tiles matching a predicate.

        Args:
            predicate: Function that returns True for matching tiles
            limit: Maximum tiles to return

        Returns:
            List of matching tiles
        """
        results = []
        for tile in self.all_tiles():
            if predicate(tile):
                results.append(tile)
                if limit and len(results) >= limit:
                    break
        return results

    def find_tiles_by_terrain(self, terrain_type: TerrainType) -> List[Tile]:
        """Find all tiles of a specific terrain type."""
        return self.find_tiles(lambda t: t.terrain_type == terrain_type)

    def find_tiles_with_affordance(self, affordance: str) -> List[Tile]:
        """Find all tiles with a specific affordance."""
        return self.find_tiles(lambda t: affordance in t.get_affordances())

    def get_passable_tiles(self) -> List[Tile]:
        """Get all passable tiles."""
        return self.find_tiles(lambda t: t.is_passable())

    def fill_rect(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        terrain_type: TerrainType,
        z: int = 0
    ) -> int:
        """
        Fill a rectangular region with a terrain type.

        Args:
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
            terrain_type: Terrain to fill with
            z: Z level

        Returns:
            Number of tiles filled
        """
        count = 0
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if self.is_valid_position(x, y, z):
                    tile = self.get_tile(x, y, z)
                    if tile:
                        tile.terrain_type = terrain_type
                        # Reset to terrain defaults
                        defaults = terrain_type.get_default_properties()
                        tile.passable = defaults.get("passable", True)
                        tile.opaque = defaults.get("opaque", False)
                        count += 1
        return count

    def serialize(self) -> dict:
        """Serialize grid to dictionary."""
        return {
            "dimensions": [self.width, self.height, self.depth],
            "default_terrain": self.default_terrain.name,
            "tiles": {
                f"{k[0]},{k[1]},{k[2]}": v.serialize()
                for k, v in self._tiles.items()
            },
            "entities": {
                eid: e.serialize()
                for eid, e in self._entities.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TileGrid":
        """Create grid from dictionary."""
        dims = data["dimensions"]
        grid = cls(
            width=dims[0],
            height=dims[1],
            depth=dims[2] if len(dims) > 2 else 1,
            default_terrain=TerrainType[data.get("default_terrain", "SOIL")]
        )

        # Load entities first
        for entity_data in data.get("entities", {}).values():
            entity = Entity.from_dict(entity_data)
            grid._entities[entity.id] = entity

        # Load tiles with entity references
        for pos_key, tile_data in data.get("tiles", {}).items():
            tile = Tile.from_dict(tile_data, grid._entities)
            grid._tiles[tuple(map(int, pos_key.split(",")))] = tile

        return grid

    def __repr__(self):
        return f"TileGrid({self.width}x{self.height}x{self.depth})"
