"""
InspectionTool - Tools that enhance inspection capabilities.

Different tools allow different kinds of inspection:
- Magnifying glass: See fine details (fibers, tiny marks) - CLOSE to FINE
- Telescope: See distant objects at CLOSE detail level
- Lantern: See in darkness
- Special lenses: See hidden markings

Note: Tools provide realistic magnification. A magnifying glass lets you
see wood fibers and fine scratches, but not microscopic/cellular details.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ToolType(Enum):
    """Types of inspection tools."""
    MAGNIFYING_GLASS = "magnifying_glass"
    TELESCOPE = "telescope"
    LANTERN = "lantern"
    SPECTACLES = "spectacles"       # For reading small text
    UV_LIGHT = "uv_light"           # Reveals hidden markings
    MIRROR = "mirror"               # See around corners
    STETHOSCOPE = "stethoscope"     # Listen to internals
    PROBE = "probe"                 # Physical inspection


class ToolAffordance(Enum):
    """What a tool enables."""
    MAGNIFY = "magnify"             # See small things larger
    DISTANT_VIEW = "distant_view"   # See far things clearly
    ILLUMINATE = "illuminate"       # See in darkness
    READ_SMALL = "read_small"       # Read tiny text
    REVEAL_HIDDEN = "reveal_hidden" # See invisible markings
    INDIRECT_VIEW = "indirect_view" # See around obstacles
    LISTEN = "listen"               # Hear internal sounds
    PHYSICAL = "physical"           # Touch/probe


@dataclass
class InspectionTool:
    """
    A tool that enhances inspection capabilities.

    Tools modify what details can be seen and at what zoom levels.
    """
    id: str
    name: str
    tool_type: ToolType
    description: str

    # Capabilities
    affordances: list[ToolAffordance] = field(default_factory=list)
    zoom_bonus: int = 0             # Extra zoom levels enabled
    detail_multiplier: float = 1.0  # Multiplier for detail revelation

    # Requirements
    requires_light: bool = False    # Needs light to work
    requires_proximity: bool = True # Must be close to target
    consumable: bool = False        # Used up after use

    # Constraints
    effective_range: float = 1.0    # Max effective distance (1.0 = adjacent)
    min_size: float = 0.0           # Minimum object size (0 = any)

    # Flavor
    use_text: str = ""              # Text shown when using tool
    fail_text: str = ""             # Text shown when tool can't help

    def can_inspect(
        self,
        distance: float = 0.0,
        object_size: float = 1.0,
        has_light: bool = True
    ) -> bool:
        """Check if this tool can be used for inspection."""
        if self.requires_light and not has_light:
            return False
        if self.requires_proximity and distance > self.effective_range:
            return False
        if object_size < self.min_size:
            return False
        return True

    def has_affordance(self, affordance: ToolAffordance) -> bool:
        """Check if tool has a specific affordance."""
        return affordance in self.affordances

    def get_effective_zoom_bonus(self, distance: float = 0.0) -> int:
        """Get zoom bonus adjusted for distance."""
        if distance > self.effective_range:
            return 0
        # Reduce bonus as distance increases
        distance_factor = 1.0 - (distance / (self.effective_range + 0.1))
        return int(self.zoom_bonus * distance_factor)

    def get_inspection_text(self, target_name: str) -> str:
        """Get text describing using this tool."""
        if self.use_text:
            return self.use_text.format(target=target_name, tool=self.name)
        return f"You use the {self.name} to examine {target_name}."

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "tool_type": self.tool_type.value,
            "description": self.description,
            "affordances": [a.value for a in self.affordances],
            "zoom_bonus": self.zoom_bonus,
            "detail_multiplier": self.detail_multiplier,
            "requires_light": self.requires_light,
            "requires_proximity": self.requires_proximity,
            "consumable": self.consumable,
            "effective_range": self.effective_range,
            "min_size": self.min_size,
            "use_text": self.use_text,
            "fail_text": self.fail_text
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'InspectionTool':
        """Deserialize from dictionary."""
        data["tool_type"] = ToolType(data["tool_type"])
        data["affordances"] = [ToolAffordance(a) for a in data.get("affordances", [])]
        return cls(**data)


# Predefined inspection tools
INSPECTION_TOOLS = {
    "magnifying_glass": InspectionTool(
        id="magnifying_glass",
        name="Magnifying Glass",
        tool_type=ToolType.MAGNIFYING_GLASS,
        description="A brass-rimmed magnifying glass for examining fine details like fibers and tiny marks.",
        affordances=[ToolAffordance.MAGNIFY, ToolAffordance.READ_SMALL],
        zoom_bonus=1,  # Enables CLOSE -> FINE (see fibers, fine scratches)
        detail_multiplier=1.5,
        effective_range=0.5,
        use_text="You peer through the {tool} at {target}, bringing fine details into focus...",
        fail_text="The {tool} can't help with something this large."
    ),

    "telescope": InspectionTool(
        id="telescope",
        name="Telescope",
        tool_type=ToolType.TELESCOPE,
        description="A collapsible brass telescope for viewing distant objects as if they were close.",
        affordances=[ToolAffordance.DISTANT_VIEW],
        zoom_bonus=2,  # Allows distant objects to be seen at CLOSE detail
        detail_multiplier=1.3,
        requires_proximity=False,
        effective_range=100.0,
        use_text="You extend the {tool} and focus on {target}, bringing it into clear view...",
        fail_text="The {tool} is meant for distant objects."
    ),

    "lantern": InspectionTool(
        id="lantern",
        name="Oil Lantern",
        tool_type=ToolType.LANTERN,
        description="A small oil lantern that casts warm light, revealing details hidden in shadow.",
        affordances=[ToolAffordance.ILLUMINATE],
        zoom_bonus=0,
        detail_multiplier=1.2,
        requires_light=False,  # Provides its own light
        effective_range=3.0,
        use_text="You hold up the {tool}, casting warm light over {target}...",
        fail_text="The light doesn't reveal anything new."
    ),

    "spectacles": InspectionTool(
        id="spectacles",
        name="Reading Spectacles",
        tool_type=ToolType.SPECTACLES,
        description="Wire-framed spectacles for reading fine print and small text.",
        affordances=[ToolAffordance.READ_SMALL],
        zoom_bonus=1,  # Helps with small text at FINE level
        detail_multiplier=1.4,
        effective_range=0.3,
        use_text="You put on the {tool} and lean in to examine {target}...",
        fail_text="The spectacles are for reading, not general inspection."
    ),

    "uv_light": InspectionTool(
        id="uv_light",
        name="Ultraviolet Lamp",
        tool_type=ToolType.UV_LIGHT,
        description="A special lamp that reveals hidden markings, stains, and fluorescent residue.",
        affordances=[ToolAffordance.REVEAL_HIDDEN, ToolAffordance.ILLUMINATE],
        zoom_bonus=0,
        detail_multiplier=1.0,
        effective_range=2.0,
        use_text="You switch on the {tool}, bathing {target} in purple light...",
        fail_text="Nothing fluoresces under the light."
    ),

    "mirror": InspectionTool(
        id="mirror",
        name="Small Mirror",
        tool_type=ToolType.MIRROR,
        description="A small hand mirror for seeing around corners and behind objects.",
        affordances=[ToolAffordance.INDIRECT_VIEW],
        zoom_bonus=0,
        detail_multiplier=0.8,  # Slight reduction due to reflection
        effective_range=2.0,
        use_text="You angle the {tool} to get a view of {target}...",
        fail_text="You can't get the right angle with the mirror."
    ),

    "stethoscope": InspectionTool(
        id="stethoscope",
        name="Stethoscope",
        tool_type=ToolType.STETHOSCOPE,
        description="A medical stethoscope for listening to internal sounds and mechanisms.",
        affordances=[ToolAffordance.LISTEN],
        zoom_bonus=0,
        detail_multiplier=1.0,
        effective_range=0.1,  # Must touch the object
        use_text="You press the {tool} against {target} and listen carefully...",
        fail_text="You can't hear anything useful through the stethoscope."
    ),

    "probe": InspectionTool(
        id="probe",
        name="Investigation Probe",
        tool_type=ToolType.PROBE,
        description="A thin metal probe for physical inspection of crevices and hidden spaces.",
        affordances=[ToolAffordance.PHYSICAL],
        zoom_bonus=0,
        detail_multiplier=1.3,
        effective_range=0.2,
        use_text="You carefully probe {target}...",
        fail_text="The probe can't reach anything useful."
    ),

    "jewelers_loupe": InspectionTool(
        id="jewelers_loupe",
        name="Jeweler's Loupe",
        tool_type=ToolType.MAGNIFYING_GLASS,
        description="A high-powered loupe for examining gems, engravings, and very fine details.",
        affordances=[ToolAffordance.MAGNIFY],
        zoom_bonus=1,  # Same zoom as magnifying glass, but better detail multiplier
        detail_multiplier=2.0,  # Higher quality magnification
        effective_range=0.1,
        min_size=0.0,  # Can examine very small things
        use_text="You hold the {tool} to your eye and examine {target} in fine detail...",
        fail_text="You need something much smaller for the loupe."
    ),
}


def get_tool(tool_id: str) -> Optional[InspectionTool]:
    """Get a tool by ID."""
    return INSPECTION_TOOLS.get(tool_id)


def get_tools_with_affordance(affordance: ToolAffordance) -> list[InspectionTool]:
    """Get all tools with a specific affordance."""
    return [t for t in INSPECTION_TOOLS.values() if t.has_affordance(affordance)]


def get_best_tool_for_inspection(
    tools: list[InspectionTool],
    distance: float = 0.0,
    object_size: float = 1.0,
    has_light: bool = True,
    needs_magnification: bool = False,
    needs_distant_view: bool = False
) -> Optional[InspectionTool]:
    """
    Find the best tool for a given inspection scenario.

    Returns the tool with the highest effective zoom bonus that
    can be used in the given conditions.
    """
    valid_tools = []

    for tool in tools:
        if not tool.can_inspect(distance, object_size, has_light):
            continue

        if needs_magnification and not tool.has_affordance(ToolAffordance.MAGNIFY):
            continue

        if needs_distant_view and not tool.has_affordance(ToolAffordance.DISTANT_VIEW):
            continue

        valid_tools.append((tool, tool.get_effective_zoom_bonus(distance)))

    if not valid_tools:
        return None

    # Return tool with highest effective zoom bonus
    valid_tools.sort(key=lambda x: x[1], reverse=True)
    return valid_tools[0][0]
