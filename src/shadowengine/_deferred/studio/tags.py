"""
Semantic tagging system for ASCII art classification.
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Set, List


class ObjectType(Enum):
    """Primary classification of art objects."""
    TREE = auto()
    ROCK = auto()
    PLANT = auto()
    WATER = auto()
    STRUCTURE = auto()
    FURNITURE = auto()
    ITEM = auto()
    NPC = auto()
    CREATURE = auto()
    VEHICLE = auto()
    DECORATION = auto()
    TERRAIN = auto()
    EFFECT = auto()
    OTHER = auto()


class Size(Enum):
    """Size classification for art."""
    TINY = auto()       # 1x1 to 2x2
    SMALL = auto()      # 3x3 to 5x5
    MEDIUM = auto()     # 6x6 to 10x10
    LARGE = auto()      # 11x11 to 20x20
    HUGE = auto()       # 21x21+
    MULTI_TILE = auto()  # Spans multiple grid tiles


class Placement(Enum):
    """Where the art can be placed."""
    FLOOR = auto()      # On ground level
    WALL = auto()       # On vertical surfaces
    CEILING = auto()    # Hanging from above
    FLOATING = auto()   # Mid-air (clouds, flying)
    WATER = auto()      # In water bodies
    UNDERGROUND = auto()  # Below ground


class InteractionType(Enum):
    """Types of interactions possible with art."""
    NONE = auto()          # No interaction (purely visual)
    CLIMBABLE = auto()     # Can be climbed
    COLLECTIBLE = auto()   # Can be picked up
    HIDEABLE = auto()      # Can hide behind/in
    SEARCHABLE = auto()    # Can be searched
    BREAKABLE = auto()     # Can be broken/destroyed
    FLAMMABLE = auto()     # Can catch fire
    PUSHABLE = auto()      # Can be pushed/moved
    OPENABLE = auto()      # Can be opened (doors, chests)
    READABLE = auto()      # Has text content
    TALKABLE = auto()      # Can converse (NPCs)
    RIDEABLE = auto()      # Can be ridden
    WEARABLE = auto()      # Can be worn
    CONSUMABLE = auto()    # Can be consumed
    TRIGGERABLE = auto()   # Activates something


class EnvironmentType(Enum):
    """Environment contexts where art fits."""
    FOREST = auto()
    URBAN = auto()
    CAVE = auto()
    RIVER = auto()
    MOUNTAIN = auto()
    DESERT = auto()
    OCEAN = auto()
    SWAMP = auto()
    PLAINS = auto()
    DUNGEON = auto()
    CASTLE = auto()
    VILLAGE = auto()
    RUINS = auto()
    UNDERGROUND = auto()
    SKY = auto()
    INDOOR = auto()
    OUTDOOR = auto()


@dataclass
class ArtTags:
    """
    Semantic tags for ASCII art classification.

    Attributes:
        object_type: Primary classification (tree, rock, NPC, etc.)
        interaction_types: What can be done with/to it
        environment_types: Where it fits in the world
        size: Size classification
        placement: Where it can be placed
        mood: Optional emotional tone
        era: Optional time period
        material: Optional material composition
        custom_tags: Additional free-form tags
    """
    object_type: ObjectType
    interaction_types: Set[InteractionType] = field(default_factory=set)
    environment_types: Set[EnvironmentType] = field(default_factory=set)
    size: Size = Size.MEDIUM
    placement: Placement = Placement.FLOOR
    mood: Optional[str] = None
    era: Optional[str] = None
    material: Optional[str] = None
    custom_tags: Set[str] = field(default_factory=set)

    def add_interaction(self, interaction: InteractionType) -> None:
        """Add an interaction type."""
        self.interaction_types.add(interaction)

    def remove_interaction(self, interaction: InteractionType) -> None:
        """Remove an interaction type."""
        self.interaction_types.discard(interaction)

    def add_environment(self, environment: EnvironmentType) -> None:
        """Add an environment type."""
        self.environment_types.add(environment)

    def remove_environment(self, environment: EnvironmentType) -> None:
        """Remove an environment type."""
        self.environment_types.discard(environment)

    def add_custom_tag(self, tag: str) -> None:
        """Add a custom tag."""
        self.custom_tags.add(tag.lower().strip())

    def has_interaction(self, interaction: InteractionType) -> bool:
        """Check if has specific interaction."""
        return interaction in self.interaction_types

    def fits_environment(self, environment: EnvironmentType) -> bool:
        """Check if fits an environment."""
        return environment in self.environment_types

    def get_affordances(self) -> List[str]:
        """Convert interaction types to affordance strings."""
        affordance_map = {
            InteractionType.CLIMBABLE: "climbable",
            InteractionType.COLLECTIBLE: "collectible",
            InteractionType.HIDEABLE: "hideable",
            InteractionType.SEARCHABLE: "searchable",
            InteractionType.BREAKABLE: "breakable",
            InteractionType.FLAMMABLE: "flammable",
            InteractionType.PUSHABLE: "pushable",
            InteractionType.OPENABLE: "openable",
            InteractionType.READABLE: "readable",
            InteractionType.TALKABLE: "talkable",
            InteractionType.RIDEABLE: "rideable",
            InteractionType.WEARABLE: "wearable",
            InteractionType.CONSUMABLE: "consumable",
            InteractionType.TRIGGERABLE: "triggerable",
        }
        return [affordance_map[i] for i in self.interaction_types if i in affordance_map]

    def to_dict(self) -> dict:
        """Serialize tags to dictionary."""
        return {
            "object_type": self.object_type.name,
            "interaction_types": [i.name for i in self.interaction_types],
            "environment_types": [e.name for e in self.environment_types],
            "size": self.size.name,
            "placement": self.placement.name,
            "mood": self.mood,
            "era": self.era,
            "material": self.material,
            "custom_tags": list(self.custom_tags)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArtTags":
        """Create tags from dictionary."""
        return cls(
            object_type=ObjectType[data["object_type"]],
            interaction_types={InteractionType[i] for i in data.get("interaction_types", [])},
            environment_types={EnvironmentType[e] for e in data.get("environment_types", [])},
            size=Size[data.get("size", "MEDIUM")],
            placement=Placement[data.get("placement", "FLOOR")],
            mood=data.get("mood"),
            era=data.get("era"),
            material=data.get("material"),
            custom_tags=set(data.get("custom_tags", []))
        )

    def matches_query(self, query: "TagQuery") -> bool:
        """Check if tags match a query."""
        if query.object_type and self.object_type != query.object_type:
            return False

        if query.required_interactions:
            if not query.required_interactions.issubset(self.interaction_types):
                return False

        if query.required_environments:
            if not query.required_environments.intersection(self.environment_types):
                return False

        if query.size and self.size != query.size:
            return False

        if query.placement and self.placement != query.placement:
            return False

        if query.material and self.material != query.material:
            return False

        return True


@dataclass
class TagQuery:
    """Query object for filtering art by tags."""
    object_type: Optional[ObjectType] = None
    required_interactions: Optional[Set[InteractionType]] = None
    required_environments: Optional[Set[EnvironmentType]] = None
    size: Optional[Size] = None
    placement: Optional[Placement] = None
    material: Optional[str] = None
    custom_tags: Optional[Set[str]] = None
