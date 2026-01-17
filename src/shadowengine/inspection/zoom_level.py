"""
ZoomLevel - Defines the zoom level system for inspection.

Zoom levels represent how closely the player is examining something:
- COARSE: General overview, basic shape and form (across the room)
- MEDIUM: More detail visible, texture and features (arm's length)
- CLOSE: Close inspection, fine textures like woodgrain visible (inches away)
- FINE: Magnified view with tool, fibers and tiny details visible (magnifying glass)

Note: Maximum detail is what you could see with a magnifying glass - not microscopic.
You can see wood fibers but not wood cells. Fine stitching but not thread fibers.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class ZoomLevel(Enum):
    """
    Zoom levels for progressive detail revelation.

    Each level represents a different scale of observation:
    - COARSE: Room-level view, basic shapes and colors
    - MEDIUM: Arm's length, features and general textures
    - CLOSE: Inches away, fine details like woodgrain (naked eye limit)
    - FINE: Magnified, fibers and tiny markings (requires magnifying glass)

    This does NOT go to microscopic level - the finest detail is what
    a magnifying glass reveals (fibers, fine scratches, small text).
    """
    COARSE = 1      # Overview - basic shape, general appearance
    MEDIUM = 2      # Detailed - textures, features, patterns
    CLOSE = 3       # Close - woodgrain, fine textures, small details
    FINE = 4        # Magnified - fibers, tiny markings (needs tool)

    @property
    def description(self) -> str:
        """Human-readable description of zoom level."""
        descriptions = {
            ZoomLevel.COARSE: "general overview",
            ZoomLevel.MEDIUM: "detailed view",
            ZoomLevel.CLOSE: "close inspection",
            ZoomLevel.FINE: "magnified view"
        }
        return descriptions[self]

    @property
    def detail_multiplier(self) -> float:
        """How much detail is visible at this zoom level (0-1)."""
        multipliers = {
            ZoomLevel.COARSE: 0.2,
            ZoomLevel.MEDIUM: 0.5,
            ZoomLevel.CLOSE: 0.8,
            ZoomLevel.FINE: 1.0
        }
        return multipliers[self]

    @property
    def viewing_description(self) -> str:
        """Description of what can be seen at this level."""
        descriptions = {
            ZoomLevel.COARSE: "basic shapes, colors, and general form",
            ZoomLevel.MEDIUM: "textures, features, and surface patterns",
            ZoomLevel.CLOSE: "fine details like woodgrain, weave patterns, small scratches",
            ZoomLevel.FINE: "tiny details like individual fibers, hairline cracks, minute inscriptions"
        }
        return descriptions[self]

    def can_zoom_in(self) -> bool:
        """Check if we can zoom in further."""
        return self.value < ZoomLevel.FINE.value

    def can_zoom_out(self) -> bool:
        """Check if we can zoom out further."""
        return self.value > ZoomLevel.COARSE.value

    def zoom_in(self) -> 'ZoomLevel':
        """Get the next zoom level in."""
        if self == ZoomLevel.COARSE:
            return ZoomLevel.MEDIUM
        elif self == ZoomLevel.MEDIUM:
            return ZoomLevel.CLOSE
        elif self == ZoomLevel.CLOSE:
            return ZoomLevel.FINE
        return ZoomLevel.FINE

    def zoom_out(self) -> 'ZoomLevel':
        """Get the next zoom level out."""
        if self == ZoomLevel.FINE:
            return ZoomLevel.CLOSE
        elif self == ZoomLevel.CLOSE:
            return ZoomLevel.MEDIUM
        elif self == ZoomLevel.MEDIUM:
            return ZoomLevel.COARSE
        return ZoomLevel.COARSE

    @classmethod
    def from_string(cls, s: str) -> Optional['ZoomLevel']:
        """Parse zoom level from string."""
        mapping = {
            "coarse": cls.COARSE,
            "overview": cls.COARSE,
            "general": cls.COARSE,
            "far": cls.COARSE,
            "medium": cls.MEDIUM,
            "detailed": cls.MEDIUM,
            "normal": cls.MEDIUM,
            "close": cls.CLOSE,
            "near": cls.CLOSE,
            "woodgrain": cls.CLOSE,
            "fine": cls.FINE,
            "magnified": cls.FINE,
            "magnify": cls.FINE,
            "fiber": cls.FINE,
            "fibers": cls.FINE,
        }
        return mapping.get(s.lower())

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {"level": self.value, "name": self.name}

    @classmethod
    def from_dict(cls, data: dict) -> 'ZoomLevel':
        """Deserialize from dictionary."""
        return cls(data["level"])


class ZoomDirection(Enum):
    """Direction of zoom change."""
    IN = auto()     # Zoom in (more detail)
    OUT = auto()    # Zoom out (less detail)
    RESET = auto()  # Reset to coarse


@dataclass
class ZoomConstraints:
    """
    Constraints on zooming for a specific object.

    Some objects may not support all zoom levels, or may require
    special tools to access certain levels.

    Zoom level accessibility:
    - COARSE, MEDIUM, CLOSE: Generally accessible without tools (naked eye)
    - FINE: Requires magnifying glass or similar tool for most objects
    """
    min_level: ZoomLevel = ZoomLevel.COARSE
    max_level: ZoomLevel = ZoomLevel.FINE
    requires_tool_for_fine: bool = True  # Default: need tool for FINE (magnified)
    required_tool_type: Optional[str] = "magnifying_glass"
    # Maximum level reachable without any tools
    max_unaided_level: ZoomLevel = ZoomLevel.CLOSE

    def is_level_accessible(
        self,
        level: ZoomLevel,
        has_required_tool: bool = False
    ) -> bool:
        """Check if a zoom level is accessible."""
        if level.value < self.min_level.value:
            return False
        if level.value > self.max_level.value:
            return False
        # FINE level requires tool by default
        if level == ZoomLevel.FINE and self.requires_tool_for_fine:
            return has_required_tool
        return True

    def get_max_accessible_level(self, has_required_tool: bool = False) -> ZoomLevel:
        """Get the maximum accessible zoom level."""
        if self.max_level.value > self.max_unaided_level.value and not has_required_tool:
            if self.requires_tool_for_fine:
                return self.max_unaided_level
        return self.max_level

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "min_level": self.min_level.value,
            "max_level": self.max_level.value,
            "requires_tool_for_fine": self.requires_tool_for_fine,
            "required_tool_type": self.required_tool_type,
            "max_unaided_level": self.max_unaided_level.value
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ZoomConstraints':
        """Deserialize from dictionary."""
        return cls(
            min_level=ZoomLevel(data["min_level"]),
            max_level=ZoomLevel(data["max_level"]),
            requires_tool_for_fine=data.get("requires_tool_for_fine", True),
            required_tool_type=data.get("required_tool_type", "magnifying_glass"),
            max_unaided_level=ZoomLevel(data.get("max_unaided_level", ZoomLevel.CLOSE.value))
        )


# Default constraints for different object categories
DEFAULT_CONSTRAINTS = {
    # Standard objects: can zoom to CLOSE with naked eye, FINE needs magnifying glass
    "standard": ZoomConstraints(
        max_level=ZoomLevel.FINE,
        requires_tool_for_fine=True,
        required_tool_type="magnifying_glass",
        max_unaided_level=ZoomLevel.CLOSE
    ),
    # Small objects: need magnifying glass to see fine detail
    "small": ZoomConstraints(
        max_level=ZoomLevel.FINE,
        requires_tool_for_fine=True,
        required_tool_type="magnifying_glass",
        max_unaided_level=ZoomLevel.CLOSE
    ),
    # Large objects: easy to see details, can reach CLOSE without issue
    "large": ZoomConstraints(
        max_level=ZoomLevel.FINE,
        requires_tool_for_fine=True,
        required_tool_type="magnifying_glass",
        max_unaided_level=ZoomLevel.CLOSE
    ),
    # Distant objects: limited view, telescope helps
    "distant": ZoomConstraints(
        max_level=ZoomLevel.MEDIUM,
        requires_tool_for_fine=False,
        max_unaided_level=ZoomLevel.MEDIUM
    ),
    # Distant with telescope: can see more with proper tool
    "distant_with_telescope": ZoomConstraints(
        max_level=ZoomLevel.CLOSE,
        requires_tool_for_fine=True,
        required_tool_type="telescope",
        max_unaided_level=ZoomLevel.COARSE
    ),
    # Surface only: can't get close (dangerous, protected, etc.)
    "surface_only": ZoomConstraints(
        max_level=ZoomLevel.COARSE,
        requires_tool_for_fine=False,
        max_unaided_level=ZoomLevel.COARSE
    ),
    # Detailed surface: can see woodgrain etc without tools
    "detailed_surface": ZoomConstraints(
        max_level=ZoomLevel.CLOSE,
        requires_tool_for_fine=False,
        max_unaided_level=ZoomLevel.CLOSE
    ),
}


def get_default_constraints(category: str) -> ZoomConstraints:
    """Get default constraints for an object category."""
    return DEFAULT_CONSTRAINTS.get(category, DEFAULT_CONSTRAINTS["standard"])
