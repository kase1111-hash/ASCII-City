"""
Static art for non-interactive visual elements.
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import uuid

from .art import ASCIIArt, ArtCategory
from .tags import ArtTags, ObjectType, Size, Placement, InteractionType


class RenderLayer(Enum):
    """Rendering layer for depth ordering."""
    GROUND = 0       # Below everything (grass, paths)
    FLOOR = 1        # Floor decorations
    OBJECT = 2       # Normal objects (furniture, items)
    STRUCTURE = 3    # Buildings, walls
    OVERLAY = 4      # Above objects (canopy, ceiling)
    EFFECT = 5       # Visual effects (weather, particles)
    UI = 6           # UI elements


class TileCoverage(Enum):
    """How art covers its tiles."""
    SINGLE = auto()      # Single tile only
    MULTI_TILE = auto()  # Spans multiple tiles
    ANCHOR = auto()      # Has anchor point for placement


@dataclass
class StaticArt(ASCIIArt):
    """
    Non-interactive visual element.

    Static art is purely visual - it doesn't have behavior or
    state beyond its visual representation. Used for decorations,
    terrain features, backgrounds, etc.

    Attributes:
        render_layer: Drawing order layer
        tile_coverage: How it covers tiles
        anchor_point: Reference point for placement (x, y)
        blocks_movement: Whether entities can move through
        blocks_vision: Whether it blocks line of sight
        provides_cover: Amount of cover (0.0 to 1.0)
        spawn_weight: Likelihood of spawning (higher = more common)
        variants: List of variant art IDs
        collision_mask: Which tiles are solid for collision
    """
    render_layer: RenderLayer = RenderLayer.OBJECT
    tile_coverage: TileCoverage = TileCoverage.SINGLE
    anchor_point: Tuple[int, int] = (0, 0)
    blocks_movement: bool = False
    blocks_vision: bool = False
    provides_cover: float = 0.0
    spawn_weight: float = 1.0
    variants: List[str] = field(default_factory=list)
    collision_mask: Optional[List[List[bool]]] = None

    def __post_init__(self):
        """Initialize and validate static art."""
        super().__post_init__()
        self.category = ArtCategory.STATIC

        # Validate cover value
        if not 0.0 <= self.provides_cover <= 1.0:
            raise ValueError("provides_cover must be between 0.0 and 1.0")

        # Auto-generate collision mask if not provided
        if self.collision_mask is None and self.blocks_movement:
            self.collision_mask = self._generate_collision_mask()

    def _generate_collision_mask(self) -> List[List[bool]]:
        """Generate collision mask from non-space tiles."""
        mask = []
        for row in self.tiles:
            mask_row = []
            for char in row:
                mask_row.append(char != " ")
            mask.append(mask_row)
        return mask

    def is_solid_at(self, x: int, y: int) -> bool:
        """Check if position is solid for collision."""
        if not self.blocks_movement:
            return False

        if self.collision_mask is None:
            return False

        if 0 <= y < len(self.collision_mask):
            if 0 <= x < len(self.collision_mask[y]):
                return self.collision_mask[y][x]

        return False

    def get_world_bounds(self, world_x: int, world_y: int) -> Tuple[int, int, int, int]:
        """
        Get world-space bounds when placed at position.

        Returns:
            (min_x, min_y, max_x, max_y)
        """
        ax, ay = self.anchor_point
        min_x = world_x - ax
        min_y = world_y - ay
        max_x = min_x + self.width - 1
        max_y = min_y + self.height - 1
        return (min_x, min_y, max_x, max_y)

    def get_tiles_covered(self, world_x: int, world_y: int) -> List[Tuple[int, int]]:
        """
        Get list of tile positions covered when placed.

        Args:
            world_x: World X position
            world_y: World Y position

        Returns:
            List of (x, y) tuples for covered tiles
        """
        ax, ay = self.anchor_point
        base_x = world_x - ax
        base_y = world_y - ay

        covered = []
        for dy in range(self.height):
            for dx in range(self.width):
                if self.get_tile(dx, dy) != " ":
                    covered.append((base_x + dx, base_y + dy))

        return covered

    def can_place_at(
        self,
        world_x: int,
        world_y: int,
        occupied_tiles: set
    ) -> bool:
        """
        Check if art can be placed at position.

        Args:
            world_x: World X position
            world_y: World Y position
            occupied_tiles: Set of already occupied (x, y) positions

        Returns:
            True if placement is valid
        """
        for pos in self.get_tiles_covered(world_x, world_y):
            if pos in occupied_tiles:
                return False
        return True

    def add_variant(self, variant_id: str) -> None:
        """Add a variant art ID."""
        if variant_id not in self.variants:
            self.variants.append(variant_id)

    def remove_variant(self, variant_id: str) -> bool:
        """Remove a variant art ID."""
        if variant_id in self.variants:
            self.variants.remove(variant_id)
            return True
        return False

    def to_dict(self) -> dict:
        """Serialize static art to dictionary."""
        data = super().to_dict()
        data.update({
            "render_layer": self.render_layer.name,
            "tile_coverage": self.tile_coverage.name,
            "anchor_point": self.anchor_point,
            "blocks_movement": self.blocks_movement,
            "blocks_vision": self.blocks_vision,
            "provides_cover": self.provides_cover,
            "spawn_weight": self.spawn_weight,
            "variants": self.variants,
            "collision_mask": self.collision_mask
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "StaticArt":
        """Create static art from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            tiles=data["tiles"],
            tags=ArtTags.from_dict(data["tags"]),
            player_id=data.get("player_id", "system"),
            version=data.get("version", 1),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            color_hints=data.get("color_hints"),
            description=data.get("description"),
            original_creator=data.get("original_creator"),
            imported_from=data.get("imported_from"),
            render_layer=RenderLayer[data.get("render_layer", "OBJECT")],
            tile_coverage=TileCoverage[data.get("tile_coverage", "SINGLE")],
            anchor_point=tuple(data.get("anchor_point", (0, 0))),
            blocks_movement=data.get("blocks_movement", False),
            blocks_vision=data.get("blocks_vision", False),
            provides_cover=data.get("provides_cover", 0.0),
            spawn_weight=data.get("spawn_weight", 1.0),
            variants=data.get("variants", []),
            collision_mask=data.get("collision_mask")
        )

    @classmethod
    def from_string(
        cls,
        name: str,
        art_string: str,
        tags: ArtTags,
        **kwargs
    ) -> "StaticArt":
        """Create static art from multi-line string."""
        tiles = [list(line) for line in art_string.split("\n")]
        return cls(name=name, tiles=tiles, tags=tags, **kwargs)

    def copy(self) -> "StaticArt":
        """Create a deep copy of the static art."""
        return StaticArt(
            id=str(uuid.uuid4()),
            name=f"{self.name} (copy)",
            tiles=[row.copy() for row in self.tiles],
            tags=ArtTags.from_dict(self.tags.to_dict()),
            player_id=self.player_id,
            version=1,
            color_hints=self.color_hints.copy() if self.color_hints else None,
            description=self.description,
            original_creator=self.original_creator or self.player_id,
            imported_from=self.id,
            render_layer=self.render_layer,
            tile_coverage=self.tile_coverage,
            anchor_point=self.anchor_point,
            blocks_movement=self.blocks_movement,
            blocks_vision=self.blocks_vision,
            provides_cover=self.provides_cover,
            spawn_weight=self.spawn_weight,
            variants=self.variants.copy(),
            collision_mask=[row.copy() for row in self.collision_mask] if self.collision_mask else None
        )


# Predefined static art templates
STATIC_ART_TEMPLATES: Dict[str, dict] = {
    "small_tree": {
        "name": "Small Tree",
        "art": """  ^
 /|\\
  |""",
        "object_type": ObjectType.TREE,
        "render_layer": RenderLayer.STRUCTURE,
        "blocks_movement": True,
        "blocks_vision": False,
        "provides_cover": 0.3,
    },
    "large_rock": {
        "name": "Large Rock",
        "art": """ ___
/   \\
\\___/""",
        "object_type": ObjectType.ROCK,
        "render_layer": RenderLayer.OBJECT,
        "blocks_movement": True,
        "blocks_vision": True,
        "provides_cover": 0.8,
    },
    "bush": {
        "name": "Bush",
        "art": """%%%
%%%""",
        "object_type": ObjectType.PLANT,
        "render_layer": RenderLayer.OBJECT,
        "blocks_movement": False,
        "blocks_vision": False,
        "provides_cover": 0.5,
    },
    "grass_patch": {
        "name": "Grass Patch",
        "art": "\"\"\"",
        "object_type": ObjectType.TERRAIN,
        "render_layer": RenderLayer.GROUND,
        "blocks_movement": False,
        "blocks_vision": False,
    },
    "wooden_fence": {
        "name": "Wooden Fence",
        "art": "|=|=|=|",
        "object_type": ObjectType.STRUCTURE,
        "render_layer": RenderLayer.OBJECT,
        "blocks_movement": True,
        "blocks_vision": False,
        "provides_cover": 0.2,
    },
}


def create_from_template(template_name: str, player_id: str = "system") -> Optional[StaticArt]:
    """Create static art from a predefined template."""
    if template_name not in STATIC_ART_TEMPLATES:
        return None

    template = STATIC_ART_TEMPLATES[template_name]
    tags = ArtTags(
        object_type=template["object_type"],
        size=Size.SMALL,
        placement=Placement.FLOOR
    )

    return StaticArt.from_string(
        name=template["name"],
        art_string=template["art"],
        tags=tags,
        player_id=player_id,
        render_layer=template.get("render_layer", RenderLayer.OBJECT),
        blocks_movement=template.get("blocks_movement", False),
        blocks_vision=template.get("blocks_vision", False),
        provides_cover=template.get("provides_cover", 0.0)
    )
