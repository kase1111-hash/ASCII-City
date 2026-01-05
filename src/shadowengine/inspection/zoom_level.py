"""
ZoomLevel - Defines the zoom level system for inspection.

Zoom levels represent how closely the player is examining something:
- COARSE: General overview, basic shape and form
- MEDIUM: More detail visible, texture and features
- FINE: Maximum detail, intricate patterns and micro-features
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class ZoomLevel(Enum):
    """
    Zoom levels for progressive detail revelation.

    Each level represents a different scale of observation.
    Higher levels reveal more detail but require closer focus.
    """
    COARSE = 1      # Overview - basic shape, general appearance
    MEDIUM = 2      # Detailed - textures, features, patterns
    FINE = 3        # Microscopic - intricate details, hidden elements

    @property
    def description(self) -> str:
        """Human-readable description of zoom level."""
        descriptions = {
            ZoomLevel.COARSE: "general overview",
            ZoomLevel.MEDIUM: "detailed view",
            ZoomLevel.FINE: "close examination"
        }
        return descriptions[self]

    @property
    def detail_multiplier(self) -> float:
        """How much detail is visible at this zoom level (0-1)."""
        multipliers = {
            ZoomLevel.COARSE: 0.3,
            ZoomLevel.MEDIUM: 0.6,
            ZoomLevel.FINE: 1.0
        }
        return multipliers[self]

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
            return ZoomLevel.FINE
        return ZoomLevel.FINE

    def zoom_out(self) -> 'ZoomLevel':
        """Get the next zoom level out."""
        if self == ZoomLevel.FINE:
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
            "medium": cls.MEDIUM,
            "detailed": cls.MEDIUM,
            "fine": cls.FINE,
            "close": cls.FINE,
            "micro": cls.FINE,
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
    """
    min_level: ZoomLevel = ZoomLevel.COARSE
    max_level: ZoomLevel = ZoomLevel.FINE
    requires_tool_for_fine: bool = False
    required_tool_type: Optional[str] = None

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
        if level == ZoomLevel.FINE and self.requires_tool_for_fine:
            return has_required_tool
        return True

    def get_max_accessible_level(self, has_required_tool: bool = False) -> ZoomLevel:
        """Get the maximum accessible zoom level."""
        if self.max_level == ZoomLevel.FINE and self.requires_tool_for_fine:
            if not has_required_tool:
                return ZoomLevel.MEDIUM
        return self.max_level

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "min_level": self.min_level.value,
            "max_level": self.max_level.value,
            "requires_tool_for_fine": self.requires_tool_for_fine,
            "required_tool_type": self.required_tool_type
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ZoomConstraints':
        """Deserialize from dictionary."""
        return cls(
            min_level=ZoomLevel(data["min_level"]),
            max_level=ZoomLevel(data["max_level"]),
            requires_tool_for_fine=data.get("requires_tool_for_fine", False),
            required_tool_type=data.get("required_tool_type")
        )


# Default constraints for different object categories
DEFAULT_CONSTRAINTS = {
    "standard": ZoomConstraints(),
    "small": ZoomConstraints(requires_tool_for_fine=True, required_tool_type="magnifying_glass"),
    "distant": ZoomConstraints(max_level=ZoomLevel.MEDIUM),
    "distant_with_telescope": ZoomConstraints(requires_tool_for_fine=True, required_tool_type="telescope"),
    "surface_only": ZoomConstraints(max_level=ZoomLevel.COARSE),
}


def get_default_constraints(category: str) -> ZoomConstraints:
    """Get default constraints for an object category."""
    return DEFAULT_CONSTRAINTS.get(category, ZoomConstraints())
