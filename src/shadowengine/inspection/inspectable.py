"""
InspectableObject - Objects that support progressive detail revelation.

Each inspectable object has multiple layers of detail that are
revealed as the player zooms in closer.
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid

from .zoom_level import ZoomLevel, ZoomConstraints


@dataclass
class DetailLayer:
    """
    A layer of detail revealed at a specific zoom level.

    Detail layers contain:
    - Visual ASCII art at this zoom level
    - Text description
    - Hidden elements that may be discovered
    - Facts that can be learned
    """
    zoom_level: ZoomLevel
    description: str                        # Text description at this level
    ascii_art: Optional[str] = None         # ASCII representation (if any)

    # Discoveries
    reveals_facts: list[str] = field(default_factory=list)  # Facts learned
    reveals_items: list[str] = field(default_factory=list)  # Items found
    reveals_hotspots: list[str] = field(default_factory=list)  # New hotspots

    # Conditions
    requires_tool: Optional[str] = None     # Tool needed to see this layer
    requires_light: bool = False            # Needs light to see
    requires_fact: Optional[str] = None     # Fact needed to notice this

    # Narrative
    first_time_text: Optional[str] = None   # Special text on first viewing
    return_text: Optional[str] = None       # Text on subsequent viewings

    # Tags for detail generation
    tags: list[str] = field(default_factory=list)

    def get_description(self, first_time: bool = True) -> str:
        """Get appropriate description text."""
        if first_time and self.first_time_text:
            return self.first_time_text
        if not first_time and self.return_text:
            return self.return_text
        return self.description

    def can_view(
        self,
        has_tool: bool = False,
        tool_type: Optional[str] = None,
        has_light: bool = True,
        known_facts: set[str] = None
    ) -> bool:
        """Check if this layer can be viewed."""
        if self.requires_light and not has_light:
            return False
        if self.requires_tool:
            if not has_tool or tool_type != self.requires_tool:
                return False
        if self.requires_fact:
            known_facts = known_facts or set()
            if self.requires_fact not in known_facts:
                return False
        return True

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "zoom_level": self.zoom_level.value,
            "description": self.description,
            "ascii_art": self.ascii_art,
            "reveals_facts": self.reveals_facts,
            "reveals_items": self.reveals_items,
            "reveals_hotspots": self.reveals_hotspots,
            "requires_tool": self.requires_tool,
            "requires_light": self.requires_light,
            "requires_fact": self.requires_fact,
            "first_time_text": self.first_time_text,
            "return_text": self.return_text,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DetailLayer':
        """Deserialize from dictionary."""
        data["zoom_level"] = ZoomLevel(data["zoom_level"])
        return cls(**data)


@dataclass
class InspectableObject:
    """
    An object that supports progressive detail revelation.

    Inspectable objects have:
    - Multiple detail layers at different zoom levels
    - Constraints on zooming
    - Persistent state tracking what has been seen
    """
    id: str = ""
    name: str = ""
    category: str = "standard"              # For default constraints
    base_description: str = ""              # Basic description

    # Detail layers
    layers: dict[ZoomLevel, DetailLayer] = field(default_factory=dict)

    # Position in world
    position: Optional[tuple[int, int]] = None
    location_id: Optional[str] = None

    # Physical properties
    size: float = 1.0                       # Relative size (1.0 = normal)
    is_distant: bool = False                # Requires telescope
    is_dark: bool = False                   # In darkness

    # Constraints
    constraints: ZoomConstraints = field(default_factory=ZoomConstraints)

    # Tags for detail generation
    tags: list[str] = field(default_factory=list)
    material: Optional[str] = None          # wood, metal, stone, etc.
    era: Optional[str] = None               # ancient, medieval, modern, etc.

    # Generation hints
    allow_generated_details: bool = True    # Can LLM generate micro-details
    detail_seed: Optional[int] = None       # Seed for deterministic generation

    def __post_init__(self):
        if not self.id:
            self.id = f"insp_{uuid.uuid4().hex[:12]}"

    def get_layer(self, zoom_level: ZoomLevel) -> Optional[DetailLayer]:
        """Get detail layer for a zoom level."""
        return self.layers.get(zoom_level)

    def add_layer(self, layer: DetailLayer) -> None:
        """Add a detail layer."""
        self.layers[layer.zoom_level] = layer

    def has_layer(self, zoom_level: ZoomLevel) -> bool:
        """Check if a layer exists for this zoom level."""
        return zoom_level in self.layers

    def get_visible_layers(
        self,
        max_zoom: ZoomLevel,
        has_tool: bool = False,
        tool_type: Optional[str] = None,
        has_light: bool = True,
        known_facts: set[str] = None
    ) -> list[DetailLayer]:
        """Get all layers visible up to max_zoom level."""
        visible = []
        for level in [ZoomLevel.COARSE, ZoomLevel.MEDIUM, ZoomLevel.CLOSE, ZoomLevel.FINE]:
            if level.value > max_zoom.value:
                break
            layer = self.layers.get(level)
            if layer and layer.can_view(has_tool, tool_type, has_light, known_facts):
                visible.append(layer)
        return visible

    def get_description_at_zoom(
        self,
        zoom_level: ZoomLevel,
        first_time: bool = True,
        has_tool: bool = False,
        tool_type: Optional[str] = None,
        has_light: bool = True,
        known_facts: set[str] = None
    ) -> str:
        """Get combined description at a zoom level."""
        layers = self.get_visible_layers(
            zoom_level, has_tool, tool_type, has_light, known_facts
        )

        if not layers:
            return self.base_description

        descriptions = [self.base_description] if zoom_level == ZoomLevel.COARSE else []
        for layer in layers:
            descriptions.append(layer.get_description(first_time))

        return "\n\n".join(descriptions)

    def get_ascii_at_zoom(self, zoom_level: ZoomLevel) -> Optional[str]:
        """Get ASCII art at a specific zoom level."""
        layer = self.layers.get(zoom_level)
        if layer:
            return layer.ascii_art
        return None

    def get_all_reveals(
        self,
        max_zoom: ZoomLevel,
        has_tool: bool = False,
        tool_type: Optional[str] = None,
        has_light: bool = True,
        known_facts: set[str] = None
    ) -> dict[str, list[str]]:
        """Get all facts, items, and hotspots revealed up to zoom level."""
        reveals = {
            "facts": [],
            "items": [],
            "hotspots": []
        }

        for layer in self.get_visible_layers(
            max_zoom, has_tool, tool_type, has_light, known_facts
        ):
            reveals["facts"].extend(layer.reveals_facts)
            reveals["items"].extend(layer.reveals_items)
            reveals["hotspots"].extend(layer.reveals_hotspots)

        return reveals

    def can_zoom_to(
        self,
        zoom_level: ZoomLevel,
        has_tool: bool = False,
        tool_type: Optional[str] = None
    ) -> bool:
        """Check if we can zoom to a specific level."""
        # Check if tool allows fine zoom
        has_required = (
            tool_type == self.constraints.required_tool_type
            if self.constraints.required_tool_type
            else has_tool
        )
        return self.constraints.is_level_accessible(zoom_level, has_required)

    def get_max_zoom_with_tool(
        self,
        has_tool: bool = False,
        tool_type: Optional[str] = None
    ) -> ZoomLevel:
        """Get maximum zoom level with current tools."""
        has_required = (
            tool_type == self.constraints.required_tool_type
            if self.constraints.required_tool_type
            else has_tool
        )
        return self.constraints.get_max_accessible_level(has_required)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "base_description": self.base_description,
            "layers": {
                k.value: v.to_dict() for k, v in self.layers.items()
            },
            "position": list(self.position) if self.position else None,
            "location_id": self.location_id,
            "size": self.size,
            "is_distant": self.is_distant,
            "is_dark": self.is_dark,
            "constraints": self.constraints.to_dict(),
            "tags": self.tags,
            "material": self.material,
            "era": self.era,
            "allow_generated_details": self.allow_generated_details,
            "detail_seed": self.detail_seed
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'InspectableObject':
        """Deserialize from dictionary."""
        data = dict(data)  # Don't mutate the input dictionary
        layers_data = data.pop("layers", {})
        layers = {
            ZoomLevel(int(k)): DetailLayer.from_dict(v)
            for k, v in layers_data.items()
        }
        data["layers"] = layers

        if data.get("position"):
            data["position"] = tuple(data["position"])

        data["constraints"] = ZoomConstraints.from_dict(data.get("constraints", {}))

        return cls(**data)


class InspectableFactory:
    """Factory for creating inspectable objects."""

    @staticmethod
    def create_simple(
        name: str,
        description: str,
        detailed_description: str = "",
        close_description: str = "",
        fine_description: str = "",
        tags: list[str] = None,
        category: str = "standard"
    ) -> InspectableObject:
        """
        Create a simple inspectable with basic layers.

        Zoom levels:
        - COARSE: Basic description (across the room)
        - MEDIUM: Detailed view (arm's length)
        - CLOSE: Close inspection, woodgrain visible (inches away, naked eye)
        - FINE: Magnified view, fibers visible (requires magnifying glass)
        """
        obj = InspectableObject(
            name=name,
            base_description=description,
            category=category,
            tags=tags or []
        )

        # Coarse layer - basic overview
        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.COARSE,
            description=description
        ))

        # Medium layer - detailed view
        if detailed_description:
            obj.add_layer(DetailLayer(
                zoom_level=ZoomLevel.MEDIUM,
                description=detailed_description
            ))

        # Close layer - fine textures like woodgrain (naked eye limit)
        if close_description:
            obj.add_layer(DetailLayer(
                zoom_level=ZoomLevel.CLOSE,
                description=close_description
            ))

        # Fine layer - magnified (fibers, tiny marks - needs tool)
        if fine_description:
            obj.add_layer(DetailLayer(
                zoom_level=ZoomLevel.FINE,
                description=fine_description,
                requires_tool="magnifying_glass"
            ))

        return obj

    @staticmethod
    def create_with_hidden(
        name: str,
        description: str,
        hidden_fact: str,
        hidden_description: str,
        requires_tool: str = "magnifying_glass"
    ) -> InspectableObject:
        """Create an inspectable with a hidden detail at fine (magnified) zoom."""
        from .zoom_level import ZoomConstraints

        obj = InspectableObject(
            name=name,
            base_description=description,
            category="small",
            constraints=ZoomConstraints(
                requires_tool_for_fine=True,
                required_tool_type=requires_tool,
                max_unaided_level=ZoomLevel.CLOSE
            )
        )

        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.COARSE,
            description=description
        ))

        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.FINE,
            description=hidden_description,
            reveals_facts=[hidden_fact],
            requires_tool=requires_tool,
            first_time_text=f"With the {requires_tool}, you notice something! {hidden_description}"
        ))

        return obj

    @staticmethod
    def create_distant(
        name: str,
        description: str,
        telescope_description: str,
        position: tuple[int, int] = None
    ) -> InspectableObject:
        """Create a distant object requiring telescope to see clearly."""
        from .zoom_level import ZoomConstraints

        obj = InspectableObject(
            name=name,
            base_description=description,
            category="distant_with_telescope",
            is_distant=True,
            position=position,
            constraints=ZoomConstraints(
                max_level=ZoomLevel.FINE,  # Telescope brings distant to FINE detail
                requires_tool_for_fine=True,
                required_tool_type="telescope",
                max_unaided_level=ZoomLevel.COARSE
            )
        )

        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.COARSE,
            description=description
        ))

        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.MEDIUM,
            description="Squinting, you can make out some general features..."
        ))

        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.CLOSE,
            description=telescope_description,
            requires_tool="telescope",
            first_time_text=f"Through the telescope: {telescope_description}"
        ))

        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.FINE,
            description=f"Fine details: {telescope_description}",
            requires_tool="telescope",
            first_time_text=f"With the telescope, you can see even finer details: {telescope_description}"
        ))

        return obj

    @staticmethod
    def create_evidence(
        name: str,
        description: str,
        evidence_fact: str,
        evidence_description: str,
        character_related: Optional[str] = None
    ) -> InspectableObject:
        """Create an evidence item with facts revealed on close inspection."""
        obj = InspectableObject(
            name=name,
            base_description=description,
            category="standard",
            tags=["evidence"]
        )

        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.COARSE,
            description=description
        ))

        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.CLOSE,
            description=evidence_description,
            reveals_facts=[evidence_fact],
            first_time_text=f"On closer inspection: {evidence_description}",
            tags=["clue", character_related] if character_related else ["clue"]
        ))

        return obj

    @staticmethod
    def create_detailed_surface(
        name: str,
        description: str,
        medium_description: str,
        close_description: str,
        fine_description: str = "",
        material: str = "wood",
        tags: list[str] = None
    ) -> InspectableObject:
        """
        Create an object with rich surface detail at all zoom levels.

        Example: A wooden desk where you can see:
        - COARSE: "A sturdy oak desk"
        - MEDIUM: "The desktop shows signs of use, with some scratches"
        - CLOSE: "The wood grain flows in elegant patterns, with tiny scratches"
        - FINE: "Individual wood fibers are visible, along with hairline cracks"
        """
        from .zoom_level import ZoomConstraints

        obj = InspectableObject(
            name=name,
            base_description=description,
            category="standard",
            material=material,
            tags=tags or [material, "furniture"],
            constraints=ZoomConstraints(
                max_level=ZoomLevel.FINE,
                requires_tool_for_fine=True,
                required_tool_type="magnifying_glass",
                max_unaided_level=ZoomLevel.CLOSE
            )
        )

        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.COARSE,
            description=description
        ))

        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.MEDIUM,
            description=medium_description
        ))

        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.CLOSE,
            description=close_description
        ))

        if fine_description:
            obj.add_layer(DetailLayer(
                zoom_level=ZoomLevel.FINE,
                description=fine_description,
                requires_tool="magnifying_glass",
                first_time_text=f"Through the magnifying glass: {fine_description}"
            ))

        return obj
