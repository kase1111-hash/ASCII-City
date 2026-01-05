"""
Position class for 3D coordinate system in the tile grid.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import math


@dataclass(frozen=True)
class Position:
    """
    Represents a 3D position in the tile grid.

    Attributes:
        x: Horizontal coordinate (east-west)
        y: Vertical coordinate (north-south)
        z: Height coordinate (ground level = 0, up = positive)
    """
    x: int
    y: int
    z: int = 0

    def __post_init__(self):
        """Validate coordinates are integers."""
        if not isinstance(self.x, int) or not isinstance(self.y, int) or not isinstance(self.z, int):
            raise TypeError("Position coordinates must be integers")

    def __add__(self, other: Position) -> Position:
        """Add two positions."""
        if not isinstance(other, Position):
            raise TypeError(f"Cannot add Position and {type(other)}")
        return Position(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Position) -> Position:
        """Subtract two positions."""
        if not isinstance(other, Position):
            raise TypeError(f"Cannot subtract {type(other)} from Position")
        return Position(self.x - other.x, self.y - other.y, self.z - other.z)

    def __neg__(self) -> Position:
        """Negate position."""
        return Position(-self.x, -self.y, -self.z)

    def distance_to(self, other: Position, include_z: bool = True) -> float:
        """
        Calculate Euclidean distance to another position.

        Args:
            other: Target position
            include_z: Whether to include z-axis in calculation

        Returns:
            Euclidean distance between positions
        """
        if not isinstance(other, Position):
            raise TypeError(f"Expected Position, got {type(other)}")

        dx = self.x - other.x
        dy = self.y - other.y

        if include_z:
            dz = self.z - other.z
            return math.sqrt(dx * dx + dy * dy + dz * dz)
        return math.sqrt(dx * dx + dy * dy)

    def manhattan_distance(self, other: Position, include_z: bool = True) -> int:
        """
        Calculate Manhattan distance to another position.

        Args:
            other: Target position
            include_z: Whether to include z-axis in calculation

        Returns:
            Manhattan distance between positions
        """
        if not isinstance(other, Position):
            raise TypeError(f"Expected Position, got {type(other)}")

        distance = abs(self.x - other.x) + abs(self.y - other.y)
        if include_z:
            distance += abs(self.z - other.z)
        return distance

    def chebyshev_distance(self, other: Position, include_z: bool = True) -> int:
        """
        Calculate Chebyshev distance (diagonal distance) to another position.

        Args:
            other: Target position
            include_z: Whether to include z-axis in calculation

        Returns:
            Chebyshev distance between positions
        """
        if not isinstance(other, Position):
            raise TypeError(f"Expected Position, got {type(other)}")

        if include_z:
            return max(abs(self.x - other.x), abs(self.y - other.y), abs(self.z - other.z))
        return max(abs(self.x - other.x), abs(self.y - other.y))

    def is_adjacent_to(self, other: Position, include_diagonals: bool = True, include_z: bool = False) -> bool:
        """
        Check if another position is adjacent.

        Args:
            other: Target position
            include_diagonals: Whether diagonal positions count as adjacent
            include_z: Whether to include vertical adjacency

        Returns:
            True if positions are adjacent
        """
        if not isinstance(other, Position):
            raise TypeError(f"Expected Position, got {type(other)}")

        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)
        dz = abs(self.z - other.z) if include_z else 0

        if include_z and dz > 1:
            return False
        elif not include_z and self.z != other.z:
            return False

        if include_diagonals:
            return dx <= 1 and dy <= 1 and (dx > 0 or dy > 0 or dz > 0)
        return (dx + dy + dz) == 1

    def get_adjacent_positions(self, include_diagonals: bool = True, include_z: bool = False) -> list[Position]:
        """
        Get all adjacent positions.

        Args:
            include_diagonals: Whether to include diagonal positions
            include_z: Whether to include vertical neighbors

        Returns:
            List of adjacent positions
        """
        neighbors = []

        # Cardinal directions
        offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        if include_diagonals:
            offsets.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])

        for dx, dy in offsets:
            neighbors.append(Position(self.x + dx, self.y + dy, self.z))

        if include_z:
            # Above and below
            neighbors.append(Position(self.x, self.y, self.z + 1))
            neighbors.append(Position(self.x, self.y, self.z - 1))

            if include_diagonals:
                # Diagonal above/below
                for dx, dy in offsets:
                    neighbors.append(Position(self.x + dx, self.y + dy, self.z + 1))
                    neighbors.append(Position(self.x + dx, self.y + dy, self.z - 1))

        return neighbors

    def to_tuple(self) -> Tuple[int, int, int]:
        """Convert to tuple representation."""
        return (self.x, self.y, self.z)

    def to_2d_tuple(self) -> Tuple[int, int]:
        """Convert to 2D tuple representation."""
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, coords: Tuple[int, int, int] | Tuple[int, int]) -> Position:
        """
        Create position from tuple.

        Args:
            coords: Tuple of (x, y) or (x, y, z)

        Returns:
            New Position instance
        """
        if len(coords) == 2:
            return cls(coords[0], coords[1], 0)
        elif len(coords) == 3:
            return cls(coords[0], coords[1], coords[2])
        else:
            raise ValueError(f"Invalid coordinate tuple length: {len(coords)}")

    @classmethod
    def origin(cls) -> Position:
        """Create position at origin (0, 0, 0)."""
        return cls(0, 0, 0)

    def __repr__(self) -> str:
        return f"Position({self.x}, {self.y}, {self.z})"

    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.z})"
