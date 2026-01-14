"""
Custom Archetype System for ShadowEngine.

Allows creation of new character archetypes beyond the built-in
types, with custom motivation presets, behavior patterns, and
dialogue tendencies.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any


@dataclass
class MotivationPreset:
    """
    Preset motivation values for an archetype.

    Motivations drive character behavior during interrogation
    and determine how they respond to pressure.
    """

    # Core motivations (0-100 scale)
    fear: int = 50
    greed: int = 50
    loyalty: int = 50
    pride: int = 50
    guilt: int = 50

    # Additional motivations for extended archetypes
    ambition: int = 50
    revenge: int = 50
    love: int = 50
    duty: int = 50
    survival: int = 50

    def get_motivation(self, name: str) -> int:
        """Get a motivation value by name."""
        return getattr(self, name, 50)

    def set_motivation(self, name: str, value: int) -> None:
        """Set a motivation value."""
        value = max(0, min(100, value))
        if hasattr(self, name):
            setattr(self, name, value)

    def get_dominant_motivation(self) -> str:
        """Get the strongest motivation."""
        motivations = {
            "fear": self.fear,
            "greed": self.greed,
            "loyalty": self.loyalty,
            "pride": self.pride,
            "guilt": self.guilt,
            "ambition": self.ambition,
            "revenge": self.revenge,
            "love": self.love,
            "duty": self.duty,
            "survival": self.survival,
        }
        return max(motivations, key=motivations.get)

    def get_weakness(self) -> str:
        """Get the motivation that makes character most vulnerable."""
        # High fear, guilt, or low pride makes vulnerable
        if self.fear > 70:
            return "fear"
        if self.guilt > 70:
            return "guilt"
        if self.pride < 30:
            return "pride"
        return self.get_dominant_motivation()

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "fear": self.fear,
            "greed": self.greed,
            "loyalty": self.loyalty,
            "pride": self.pride,
            "guilt": self.guilt,
            "ambition": self.ambition,
            "revenge": self.revenge,
            "love": self.love,
            "duty": self.duty,
            "survival": self.survival,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'MotivationPreset':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class BehaviorTendency(Enum):
    """Behavioral tendencies for archetypes."""
    COOPERATIVE = auto()     # Tends to cooperate
    EVASIVE = auto()         # Avoids direct answers
    AGGRESSIVE = auto()      # Confrontational
    MANIPULATIVE = auto()    # Tries to manipulate
    PASSIVE = auto()         # Goes along with things
    PROTECTIVE = auto()      # Protects others
    SELF_SERVING = auto()    # Only cares about self
    TRUTHFUL = auto()        # Generally honest
    DECEPTIVE = auto()       # Tends to lie


class ResponseStyle(Enum):
    """How the archetype responds to questioning."""
    DIRECT = auto()          # Gives straight answers
    RAMBLING = auto()        # Long-winded responses
    TERSE = auto()           # Short, clipped answers
    EMOTIONAL = auto()       # Responds with emotion
    CALCULATED = auto()      # Careful, measured responses
    DEFENSIVE = auto()       # Immediately defensive
    HELPFUL = auto()         # Tries to be helpful
    HOSTILE = auto()         # Openly hostile


@dataclass
class BehaviorPattern:
    """
    Behavior pattern definition for an archetype.

    Defines how the archetype behaves in various situations.
    """

    # Core tendencies
    tendency: BehaviorTendency = BehaviorTendency.EVASIVE
    response_style: ResponseStyle = ResponseStyle.DIRECT

    # Interrogation behavior
    cracks_easily: bool = False
    trust_threshold: int = 50  # 0-100, higher = harder to crack
    pressure_resistance: float = 0.5  # 0.0-1.0

    # Dialogue behavior
    will_lie: bool = True
    lie_probability: float = 0.5  # 0.0-1.0
    deflect_probability: float = 0.3
    reveal_on_crack: bool = True

    # Emotional responses
    anger_threshold: float = 0.7  # When they get angry
    fear_threshold: float = 0.5  # When they get scared
    breakdown_threshold: float = 0.9  # When they break down

    # Social behavior
    trusts_authority: bool = False
    trusts_strangers: bool = False
    protects_allies: bool = True
    betrays_under_pressure: bool = False

    def should_lie(self, pressure: float, rng=None) -> bool:
        """Determine if archetype should lie given current pressure."""
        import random
        rng = rng or random
        if not self.will_lie:
            return False
        # Less likely to lie under high pressure if they crack easily
        if self.cracks_easily and pressure > 0.5:
            return rng.random() < self.lie_probability * 0.5
        return rng.random() < self.lie_probability

    def should_deflect(self, topic_importance: float, rng=None) -> bool:
        """Determine if archetype should deflect a question."""
        import random
        rng = rng or random
        # More important topics = more likely to deflect
        adjusted_prob = self.deflect_probability * (0.5 + topic_importance * 0.5)
        return rng.random() < adjusted_prob

    def get_mood_modifier(self, pressure: float) -> str:
        """Get mood based on current pressure level."""
        if pressure >= self.breakdown_threshold:
            return "broken"
        if pressure >= self.anger_threshold:
            return "angry" if not self.cracks_easily else "terrified"
        if pressure >= self.fear_threshold:
            return "nervous"
        return "calm"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tendency": self.tendency.name,
            "response_style": self.response_style.name,
            "cracks_easily": self.cracks_easily,
            "trust_threshold": self.trust_threshold,
            "pressure_resistance": self.pressure_resistance,
            "will_lie": self.will_lie,
            "lie_probability": self.lie_probability,
            "deflect_probability": self.deflect_probability,
            "reveal_on_crack": self.reveal_on_crack,
            "anger_threshold": self.anger_threshold,
            "fear_threshold": self.fear_threshold,
            "breakdown_threshold": self.breakdown_threshold,
            "trusts_authority": self.trusts_authority,
            "trusts_strangers": self.trusts_strangers,
            "protects_allies": self.protects_allies,
            "betrays_under_pressure": self.betrays_under_pressure,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BehaviorPattern':
        """Create from dictionary."""
        data = data.copy()
        if "tendency" in data and isinstance(data["tendency"], str):
            data["tendency"] = BehaviorTendency[data["tendency"]]
        if "response_style" in data and isinstance(data["response_style"], str):
            data["response_style"] = ResponseStyle[data["response_style"]]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ArchetypeDefinition:
    """
    Complete definition of a custom archetype.

    Combines motivations, behaviors, and metadata to create
    a reusable character template.
    """

    # Identity
    id: str
    name: str
    description: str = ""

    # Character properties
    motivations: MotivationPreset = field(default_factory=MotivationPreset)
    behavior: BehaviorPattern = field(default_factory=BehaviorPattern)

    # Role in narrative
    can_be_culprit: bool = True
    can_be_witness: bool = True
    can_be_victim: bool = True
    can_be_red_herring: bool = True

    # Dialogue templates
    greeting_templates: List[str] = field(default_factory=list)
    farewell_templates: List[str] = field(default_factory=list)
    deflection_templates: List[str] = field(default_factory=list)
    confession_templates: List[str] = field(default_factory=list)
    denial_templates: List[str] = field(default_factory=list)

    # Appearance hints
    appearance_hints: List[str] = field(default_factory=list)
    mannerism_hints: List[str] = field(default_factory=list)

    # Relationships
    typical_relationships: Dict[str, float] = field(default_factory=dict)

    # Theme compatibility
    compatible_themes: List[str] = field(default_factory=list)

    def get_greeting(self, mood: str = "neutral", rng=None) -> str:
        """Get a greeting template based on mood."""
        import random
        rng = rng or random
        if self.greeting_templates:
            return rng.choice(self.greeting_templates)
        return "Hello."

    def get_deflection(self, rng=None) -> str:
        """Get a deflection template."""
        import random
        rng = rng or random
        if self.deflection_templates:
            return rng.choice(self.deflection_templates)
        return "I don't want to talk about that."

    def get_confession(self, rng=None) -> str:
        """Get a confession template."""
        import random
        rng = rng or random
        if self.confession_templates:
            return rng.choice(self.confession_templates)
        return "Fine, I'll tell you everything..."

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "motivations": self.motivations.to_dict(),
            "behavior": self.behavior.to_dict(),
            "can_be_culprit": self.can_be_culprit,
            "can_be_witness": self.can_be_witness,
            "can_be_victim": self.can_be_victim,
            "can_be_red_herring": self.can_be_red_herring,
            "greeting_templates": self.greeting_templates,
            "farewell_templates": self.farewell_templates,
            "deflection_templates": self.deflection_templates,
            "confession_templates": self.confession_templates,
            "denial_templates": self.denial_templates,
            "appearance_hints": self.appearance_hints,
            "mannerism_hints": self.mannerism_hints,
            "typical_relationships": self.typical_relationships,
            "compatible_themes": self.compatible_themes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArchetypeDefinition':
        """Create from dictionary."""
        data = data.copy()
        if "motivations" in data and isinstance(data["motivations"], dict):
            data["motivations"] = MotivationPreset.from_dict(data["motivations"])
        if "behavior" in data and isinstance(data["behavior"], dict):
            data["behavior"] = BehaviorPattern.from_dict(data["behavior"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class CustomArchetype:
    """
    Wrapper for using custom archetypes with the game's character system.

    Provides compatibility with the existing Archetype enum-based system.
    """

    def __init__(self, definition: ArchetypeDefinition):
        self.definition = definition
        self.id = definition.id
        self.name = definition.name
        self.value = definition.id  # For enum compatibility

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"CustomArchetype({self.id!r})"

    def __eq__(self, other) -> bool:
        if isinstance(other, CustomArchetype):
            return self.id == other.id
        if hasattr(other, 'value'):
            return self.id == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.id)

    def get_motivations(self) -> MotivationPreset:
        """Get motivation preset."""
        return self.definition.motivations

    def get_behavior(self) -> BehaviorPattern:
        """Get behavior pattern."""
        return self.definition.behavior


class ArchetypeRegistry:
    """
    Registry for custom archetypes.

    Manages registration and retrieval of custom archetype definitions.
    """

    def __init__(self):
        self._archetypes: Dict[str, ArchetypeDefinition] = {}
        self._by_theme: Dict[str, List[str]] = {}

    def register(self, archetype: ArchetypeDefinition) -> bool:
        """
        Register a custom archetype.

        Args:
            archetype: Archetype definition to register

        Returns:
            True if registered successfully
        """
        if archetype.id in self._archetypes:
            return False

        self._archetypes[archetype.id] = archetype

        # Index by compatible themes
        for theme in archetype.compatible_themes:
            if theme not in self._by_theme:
                self._by_theme[theme] = []
            self._by_theme[theme].append(archetype.id)

        return True

    def unregister(self, archetype_id: str) -> bool:
        """Unregister an archetype."""
        if archetype_id not in self._archetypes:
            return False

        archetype = self._archetypes[archetype_id]

        # Remove from theme index
        for theme in archetype.compatible_themes:
            if theme in self._by_theme:
                self._by_theme[theme] = [
                    aid for aid in self._by_theme[theme] if aid != archetype_id
                ]

        del self._archetypes[archetype_id]
        return True

    def get(self, archetype_id: str) -> Optional[ArchetypeDefinition]:
        """Get an archetype by ID."""
        return self._archetypes.get(archetype_id)

    def get_custom(self, archetype_id: str) -> Optional[CustomArchetype]:
        """Get a CustomArchetype wrapper by ID."""
        definition = self.get(archetype_id)
        if definition:
            return CustomArchetype(definition)
        return None

    def list_all(self) -> List[str]:
        """List all registered archetype IDs."""
        return list(self._archetypes.keys())

    def list_for_theme(self, theme_id: str) -> List[str]:
        """List archetypes compatible with a theme."""
        return self._by_theme.get(theme_id, [])

    def list_culprits(self) -> List[str]:
        """List archetypes that can be culprits."""
        return [
            aid for aid, a in self._archetypes.items()
            if a.can_be_culprit
        ]

    def list_witnesses(self) -> List[str]:
        """List archetypes that can be witnesses."""
        return [
            aid for aid, a in self._archetypes.items()
            if a.can_be_witness
        ]

    def list_victims(self) -> List[str]:
        """List archetypes that can be victims."""
        return [
            aid for aid, a in self._archetypes.items()
            if a.can_be_victim
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert registry to dictionary."""
        return {
            "archetypes": {
                aid: a.to_dict() for aid, a in self._archetypes.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArchetypeRegistry':
        """Create registry from dictionary."""
        registry = cls()
        for aid, adata in data.get("archetypes", {}).items():
            archetype = ArchetypeDefinition.from_dict(adata)
            registry.register(archetype)
        return registry


# Global registry instance
_global_registry = ArchetypeRegistry()


def create_archetype(
    id: str,
    name: str,
    description: str = "",
    **kwargs
) -> ArchetypeDefinition:
    """
    Create a new archetype definition.

    Args:
        id: Unique identifier
        name: Display name
        description: Description of the archetype
        **kwargs: Additional configuration

    Returns:
        New ArchetypeDefinition
    """
    return ArchetypeDefinition(
        id=id,
        name=name,
        description=description,
        **kwargs
    )


def register_archetype(archetype: ArchetypeDefinition) -> bool:
    """Register an archetype with the global registry."""
    return _global_registry.register(archetype)


def get_archetype(archetype_id: str) -> Optional[ArchetypeDefinition]:
    """Get an archetype from the global registry."""
    return _global_registry.get(archetype_id)


def list_archetypes() -> List[str]:
    """List all registered archetypes."""
    return _global_registry.list_all()


# Predefined custom archetypes

FEMME_FATALE = ArchetypeDefinition(
    id="femme_fatale",
    name="Femme Fatale",
    description="A mysterious, seductive figure with hidden agendas and dangerous secrets.",
    motivations=MotivationPreset(
        fear=30,
        greed=70,
        loyalty=20,
        pride=80,
        guilt=20,
        ambition=90,
        love=40,
    ),
    behavior=BehaviorPattern(
        tendency=BehaviorTendency.MANIPULATIVE,
        response_style=ResponseStyle.CALCULATED,
        cracks_easily=False,
        trust_threshold=75,
        will_lie=True,
        lie_probability=0.7,
    ),
    greeting_templates=[
        "Well, well... what brings you here?",
        "I've been expecting someone like you.",
        "You look like you have questions.",
    ],
    deflection_templates=[
        "Wouldn't you like to know?",
        "Some secrets are meant to stay buried.",
        "Let's talk about something more... interesting.",
    ],
    compatible_themes=["noir", "gothic_horror"],
)

CORRUPT_COP = ArchetypeDefinition(
    id="corrupt_cop",
    name="Corrupt Cop",
    description="A law enforcement officer who has crossed the line too many times.",
    motivations=MotivationPreset(
        fear=60,
        greed=80,
        loyalty=40,
        pride=50,
        guilt=70,
        survival=80,
    ),
    behavior=BehaviorPattern(
        tendency=BehaviorTendency.AGGRESSIVE,
        response_style=ResponseStyle.DEFENSIVE,
        cracks_easily=False,
        trust_threshold=60,
        will_lie=True,
        lie_probability=0.6,
        trusts_authority=True,
        betrays_under_pressure=True,
    ),
    greeting_templates=[
        "You shouldn't be here.",
        "What do you want?",
        "Make it quick.",
    ],
    confession_templates=[
        "I did what I had to do...",
        "You don't understand the pressures...",
    ],
    compatible_themes=["noir", "cyberpunk"],
)

STREET_INFORMANT = ArchetypeDefinition(
    id="street_informant",
    name="Street Informant",
    description="A well-connected figure who trades in secrets and information.",
    motivations=MotivationPreset(
        fear=70,
        greed=90,
        loyalty=10,
        pride=30,
        guilt=20,
        survival=85,
    ),
    behavior=BehaviorPattern(
        tendency=BehaviorTendency.SELF_SERVING,
        response_style=ResponseStyle.TERSE,
        cracks_easily=True,
        trust_threshold=30,
        will_lie=True,
        lie_probability=0.4,
        betrays_under_pressure=True,
    ),
    greeting_templates=[
        "You got something for me?",
        "*looks around nervously* What do you need?",
        "Information ain't free...",
    ],
    deflection_templates=[
        "I don't know nothing about that.",
        "You didn't hear this from me...",
        "That's above my pay grade.",
    ],
    compatible_themes=["noir", "cyberpunk"],
)

GRIEVING_WIDOW = ArchetypeDefinition(
    id="grieving_widow",
    name="Grieving Widow/Widower",
    description="Someone dealing with loss, who may know more than they admit.",
    motivations=MotivationPreset(
        fear=40,
        greed=30,
        loyalty=70,
        pride=40,
        guilt=50,
        love=90,
        revenge=60,
    ),
    behavior=BehaviorPattern(
        tendency=BehaviorTendency.PROTECTIVE,
        response_style=ResponseStyle.EMOTIONAL,
        cracks_easily=True,
        trust_threshold=40,
        will_lie=True,
        lie_probability=0.3,
        protects_allies=True,
    ),
    greeting_templates=[
        "*wipes eyes* Yes?",
        "I've already spoken to the police...",
        "What more do you want from me?",
    ],
    compatible_themes=["noir", "gothic_horror"],
)

# Register predefined archetypes
register_archetype(FEMME_FATALE)
register_archetype(CORRUPT_COP)
register_archetype(STREET_INFORMANT)
register_archetype(GRIEVING_WIDOW)
