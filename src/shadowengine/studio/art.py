"""
Base ASCIIArt class for all art types.
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from .tags import ArtTags, ObjectType


class ArtCategory(Enum):
    """Category of ASCII art."""
    STATIC = auto()   # Non-interactive visual elements
    DYNAMIC = auto()  # Interactive entities with behavior


@dataclass
class ASCIIArt:
    """
    Base class for ASCII art.

    Represents a 2D grid of characters with semantic tags
    and metadata for world integration.

    Attributes:
        id: Unique identifier
        name: Display name
        tiles: 2D character array
        tags: Semantic classification
        category: Static or Dynamic
        player_id: Creator's identifier
        version: Iteration count for variants
        created_at: Creation timestamp
        updated_at: Last modification timestamp
        color_hints: Optional color suggestions per character
        description: Optional text description
    """
    name: str
    tiles: List[List[str]]
    tags: ArtTags
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: ArtCategory = ArtCategory.STATIC
    player_id: str = "system"
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    color_hints: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    original_creator: Optional[str] = None  # For imported art
    imported_from: Optional[str] = None  # Original art ID if imported

    def __post_init__(self):
        """Validate art structure."""
        if not self.tiles:
            raise ValueError("Art must have at least one row of tiles")
        if not all(isinstance(row, list) for row in self.tiles):
            raise ValueError("Tiles must be a 2D list")

    @property
    def width(self) -> int:
        """Get art width (max row length)."""
        return max(len(row) for row in self.tiles) if self.tiles else 0

    @property
    def height(self) -> int:
        """Get art height (number of rows)."""
        return len(self.tiles)

    @property
    def dimensions(self) -> tuple[int, int]:
        """Get (width, height) tuple."""
        return (self.width, self.height)

    def get_tile(self, x: int, y: int) -> str:
        """Get character at position."""
        if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
            return self.tiles[y][x]
        return " "  # Return space for out of bounds

    def set_tile(self, x: int, y: int, char: str) -> bool:
        """Set character at position."""
        if not char or len(char) != 1:
            return False

        # Expand grid if necessary
        while y >= len(self.tiles):
            self.tiles.append([])

        while x >= len(self.tiles[y]):
            self.tiles[y].append(" ")

        self.tiles[y][x] = char
        self.updated_at = datetime.now()
        return True

    def render(self) -> str:
        """Render art as string."""
        return "\n".join("".join(row) for row in self.tiles)

    def render_tiles(self) -> List[str]:
        """Render art as list of strings (one per row)."""
        return ["".join(row) for row in self.tiles]

    def normalize(self) -> None:
        """Normalize tile array to consistent width."""
        max_width = self.width
        for row in self.tiles:
            while len(row) < max_width:
                row.append(" ")

    def trim(self) -> None:
        """Remove empty rows/columns from edges."""
        # Remove empty rows from top
        while self.tiles and all(c == " " for c in self.tiles[0]):
            self.tiles.pop(0)

        # Remove empty rows from bottom
        while self.tiles and all(c == " " for c in self.tiles[-1]):
            self.tiles.pop()

        if not self.tiles:
            self.tiles = [[" "]]
            return

        # Find non-empty column range
        min_col = float('inf')
        max_col = 0
        for row in self.tiles:
            for i, c in enumerate(row):
                if c != " ":
                    min_col = min(min_col, i)
                    max_col = max(max_col, i)

        if min_col == float('inf'):
            self.tiles = [[" "]]
            return

        # Trim columns
        self.tiles = [row[int(min_col):max_col + 1] for row in self.tiles]
        self.updated_at = datetime.now()

    def copy(self) -> "ASCIIArt":
        """Create a deep copy of the art."""
        return ASCIIArt(
            id=str(uuid.uuid4()),
            name=f"{self.name} (copy)",
            tiles=[row.copy() for row in self.tiles],
            tags=ArtTags.from_dict(self.tags.to_dict()),
            category=self.category,
            player_id=self.player_id,
            version=1,
            color_hints=self.color_hints.copy() if self.color_hints else None,
            description=self.description,
            original_creator=self.original_creator or self.player_id,
            imported_from=self.id
        )

    def create_variant(self, variant_tiles: List[List[str]], variant_num: int) -> "ASCIIArt":
        """Create a variant of this art with different tiles."""
        return ASCIIArt(
            id=str(uuid.uuid4()),
            name=f"{self.name} v{variant_num}",
            tiles=variant_tiles,
            tags=ArtTags.from_dict(self.tags.to_dict()),
            category=self.category,
            player_id=self.player_id,
            version=variant_num,
            color_hints=self.color_hints.copy() if self.color_hints else None,
            description=self.description,
            original_creator=self.player_id,
            imported_from=self.id
        )

    def to_dict(self) -> dict:
        """Serialize art to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "tiles": self.tiles,
            "tags": self.tags.to_dict(),
            "category": self.category.name,
            "player_id": self.player_id,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "color_hints": self.color_hints,
            "description": self.description,
            "original_creator": self.original_creator,
            "imported_from": self.imported_from
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ASCIIArt":
        """Create art from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            tiles=data["tiles"],
            tags=ArtTags.from_dict(data["tags"]),
            category=ArtCategory[data.get("category", "STATIC")],
            player_id=data.get("player_id", "system"),
            version=data.get("version", 1),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            color_hints=data.get("color_hints"),
            description=data.get("description"),
            original_creator=data.get("original_creator"),
            imported_from=data.get("imported_from")
        )

    @classmethod
    def from_string(cls, name: str, art_string: str, tags: ArtTags) -> "ASCIIArt":
        """Create art from a multi-line string."""
        tiles = [list(line) for line in art_string.split("\n")]
        return cls(name=name, tiles=tiles, tags=tags)

    @classmethod
    def create_blank(cls, name: str, width: int, height: int, tags: ArtTags) -> "ASCIIArt":
        """Create blank art canvas."""
        tiles = [[" " for _ in range(width)] for _ in range(height)]
        return cls(name=name, tiles=tiles, tags=tags)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ASCIIArt):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"ASCIIArt('{self.name}', {self.width}x{self.height})"
