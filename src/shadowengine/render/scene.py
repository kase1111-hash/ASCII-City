"""
Scene and Location definitions.
"""

from dataclasses import dataclass, field
from typing import Optional
from ..interaction.hotspot import Hotspot, HotspotType


@dataclass
class Location:
    """A game location that can be visited."""

    id: str
    name: str
    description: str
    art: list[str] = field(default_factory=list)    # ASCII art lines
    hotspots: list[Hotspot] = field(default_factory=list)
    exits: dict[str, str] = field(default_factory=dict)  # direction -> location_id

    # Atmosphere
    is_outdoor: bool = False
    base_light_level: float = 1.0   # 0.0 = dark, 1.0 = bright
    ambient_description: str = ""    # Atmospheric text

    def add_hotspot(self, hotspot: Hotspot) -> None:
        """Add a hotspot to this location."""
        self.hotspots.append(hotspot)

    def add_exit(self, direction: str, destination_id: str) -> None:
        """Add an exit to another location."""
        self.exits[direction] = destination_id

    def get_visible_hotspots(self) -> list[Hotspot]:
        """Get all currently visible hotspots."""
        return [h for h in self.hotspots if h.visible and h.active]

    def get_hotspot_by_id(self, hotspot_id: str) -> Optional[Hotspot]:
        """Get a hotspot by its ID."""
        for h in self.hotspots:
            if h.id == hotspot_id:
                return h
        return None

    def get_hotspot_by_number(self, number: int) -> Optional[Hotspot]:
        """Get a hotspot by its display number."""
        for h in self.hotspots:
            if h.number == number and h.visible and h.active:
                return h
        return None

    def get_hotspot_by_label(self, label: str) -> Optional[Hotspot]:
        """Get a hotspot by its label (partial match)."""
        label_lower = label.lower()
        for h in self.hotspots:
            if h.visible and h.active:
                if label_lower in h.label.lower() or h.label.lower() in label_lower:
                    return h
        return None

    def get_people(self) -> list[Hotspot]:
        """Get all person hotspots in this location."""
        return [
            h for h in self.hotspots
            if h.hotspot_type == HotspotType.PERSON and h.visible and h.active
        ]

    def get_exits_list(self) -> list[Hotspot]:
        """Get all exit hotspots."""
        return [
            h for h in self.hotspots
            if h.hotspot_type == HotspotType.EXIT and h.visible and h.active
        ]

    def to_dict(self) -> dict:
        """Serialize location."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "art": self.art,
            "hotspots": [h.to_dict() for h in self.hotspots],
            "exits": self.exits,
            "is_outdoor": self.is_outdoor,
            "base_light_level": self.base_light_level,
            "ambient_description": self.ambient_description
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Location':
        """Deserialize location."""
        location = cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            art=data.get("art", []),
            exits=data.get("exits", {}),
            is_outdoor=data.get("is_outdoor", False),
            base_light_level=data.get("base_light_level", 1.0),
            ambient_description=data.get("ambient_description", "")
        )
        location.hotspots = [
            Hotspot.from_dict(h) for h in data.get("hotspots", [])
        ]
        return location


@dataclass
class Scene:
    """
    A renderable scene combining location, state, and overlays.
    """

    location: Location
    width: int = 120  # Default wider (overridden by game config with actual terminal size)
    height: int = 40

    # Current state
    weather_overlay: Optional[str] = None
    time_period: str = "day"
    tension_level: float = 0.0

    # Rendered output
    _rendered_art: list[str] = field(default_factory=list)
    _hotspot_legend: list[str] = field(default_factory=list)

    def number_hotspots(self) -> None:
        """Assign numbers to visible hotspots."""
        visible = self.location.get_visible_hotspots()
        for i, hotspot in enumerate(visible, 1):
            hotspot.number = i

    def get_hotspot_legend(self) -> list[str]:
        """Generate legend showing what's in the scene."""
        visible = self.location.get_visible_hotspots()
        if not visible:
            return []

        # Group by type for cleaner display
        people = [h for h in visible if h.hotspot_type.value == "person"]
        exits = [h for h in visible if h.hotspot_type.value == "exit"]
        objects = [h for h in visible if h.hotspot_type.value not in ("person", "exit")]

        lines = [""]

        if people:
            lines.append("People here: " + ", ".join(h.label for h in people))

        if objects:
            lines.append("You notice: " + ", ".join(h.label for h in objects))

        if exits:
            lines.append("Exits: " + ", ".join(h.label for h in exits))

        return lines

    def get_rendered_scene(self) -> list[str]:
        """Get the complete rendered scene with art and legend."""
        self.number_hotspots()

        lines = []

        # Location header
        lines.append("=" * self.width)
        lines.append(f" {self.location.name} ".center(self.width))
        lines.append("=" * self.width)
        lines.append("")

        # Location description
        lines.append(self.location.description)
        lines.append("")

        # ASCII art if present
        if self.location.art:
            for art_line in self.location.art:
                lines.append(art_line)
            lines.append("")

        # Ambient description
        if self.location.ambient_description:
            lines.append(self.location.ambient_description)
            lines.append("")

        # Hotspot legend
        legend = self.get_hotspot_legend()
        lines.extend(legend)

        # Exits
        if self.location.exits:
            lines.append("")
            exits_str = ", ".join(
                f"{direction} to {dest}"
                for direction, dest in self.location.exits.items()
            )
            lines.append(f"Exits: {exits_str}")

        lines.append("")
        lines.append("-" * self.width)

        return lines
