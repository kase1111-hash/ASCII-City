"""
Personality template system for dynamic entities.
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict


class IdleBehavior(Enum):
    """What entity does when idle."""
    STILL = auto()        # Stays in place
    WANDER = auto()       # Random movement
    PATROL = auto()       # Follow patrol route
    FORAGE = auto()       # Search for food/resources
    GUARD = auto()        # Watch surroundings
    SEARCH = auto()       # Actively seek things
    SLEEP = auto()        # Rest/hibernate
    SOCIALIZE = auto()    # Interact with others


class ThreatResponse(Enum):
    """How entity responds to threats."""
    IGNORE = auto()       # No response
    FLEE = auto()         # Run away
    HIDE = auto()         # Find cover
    ATTACK = auto()       # Fight back
    CHALLENGE = auto()    # Warn/display
    ALERT_OTHERS = auto()  # Call for help
    OBSERVE = auto()      # Watch from distance
    PROTECT = auto()      # Defend others
    PROTECT_HOARD = auto()  # Defend possessions
    BRIBE = auto()        # Offer items to leave


class Attitude(Enum):
    """Initial attitude toward player."""
    FRIENDLY = auto()     # Helpful, positive
    NEUTRAL = auto()      # No opinion
    SUSPICIOUS = auto()   # Wary, cautious
    HOSTILE = auto()      # Aggressive
    AFRAID = auto()       # Fearful
    CURIOUS = auto()      # Interested


@dataclass
class PersonalityTemplate:
    """
    Behavioral personality template for entities.

    Attributes:
        name: Template name
        traits: Core personality traits (0.0 to 1.0)
        idle_behavior: What entity does when nothing happens
        threat_response: How entity reacts to danger
        player_attitude: Initial attitude toward player
        memory_duration: How long entity remembers (hours)
        grudge_factor: How much bad experiences matter (0.0 to 1.0)
    """
    name: str
    traits: Dict[str, float] = field(default_factory=dict)
    idle_behavior: IdleBehavior = IdleBehavior.WANDER
    threat_response: ThreatResponse = ThreatResponse.FLEE
    player_attitude: Attitude = Attitude.NEUTRAL
    memory_duration: float = 24.0  # Hours
    grudge_factor: float = 0.5

    def __post_init__(self):
        """Initialize default traits if not provided."""
        default_traits = {
            "aggression": 0.5,
            "fear": 0.5,
            "curiosity": 0.5,
            "loyalty": 0.5,
            "greed": 0.5,
            "social": 0.5
        }
        for trait, default_value in default_traits.items():
            if trait not in self.traits:
                self.traits[trait] = default_value

        # Validate trait values
        for trait, value in self.traits.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Trait {trait} must be between 0.0 and 1.0")

    def get_trait(self, trait: str) -> float:
        """Get trait value with default."""
        return self.traits.get(trait, 0.5)

    def set_trait(self, trait: str, value: float) -> None:
        """Set trait value."""
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Trait value must be between 0.0 and 1.0")
        self.traits[trait] = value

    def modify_trait(self, trait: str, delta: float) -> float:
        """Modify trait by delta, clamping to valid range."""
        current = self.get_trait(trait)
        new_value = max(0.0, min(1.0, current + delta))
        self.traits[trait] = new_value
        return new_value

    def is_aggressive(self) -> bool:
        """Check if entity is likely to attack."""
        return self.get_trait("aggression") > 0.6

    def is_fearful(self) -> bool:
        """Check if entity is likely to flee."""
        return self.get_trait("fear") > 0.6

    def is_curious(self) -> bool:
        """Check if entity investigates."""
        return self.get_trait("curiosity") > 0.5

    def is_social(self) -> bool:
        """Check if entity interacts with others."""
        return self.get_trait("social") > 0.5

    def calculate_response(self, threat_level: float) -> ThreatResponse:
        """Calculate response based on traits and threat level."""
        aggression = self.get_trait("aggression")
        fear = self.get_trait("fear")
        loyalty = self.get_trait("loyalty")

        # High threat overrides normal behavior
        if threat_level > 0.8:
            if fear > aggression:
                return ThreatResponse.FLEE
            elif aggression > 0.7:
                return ThreatResponse.ATTACK
            else:
                return ThreatResponse.HIDE

        # Normal threat assessment
        if loyalty > 0.7:
            return ThreatResponse.PROTECT

        if aggression > fear and aggression > 0.5:
            return ThreatResponse.CHALLENGE if threat_level < 0.5 else ThreatResponse.ATTACK

        if fear > 0.6:
            return ThreatResponse.FLEE if threat_level > 0.3 else ThreatResponse.HIDE

        return self.threat_response

    def calculate_idle_action(self, has_target: bool = False) -> IdleBehavior:
        """Calculate idle behavior based on traits."""
        if has_target and self.get_trait("curiosity") > 0.6:
            return IdleBehavior.SEARCH

        if self.get_trait("social") > 0.7:
            return IdleBehavior.SOCIALIZE

        if self.get_trait("greed") > 0.7:
            return IdleBehavior.FORAGE

        if self.get_trait("aggression") > 0.6:
            return IdleBehavior.PATROL

        return self.idle_behavior

    def copy(self) -> "PersonalityTemplate":
        """Create a copy of this template."""
        return PersonalityTemplate(
            name=f"{self.name} (copy)",
            traits=self.traits.copy(),
            idle_behavior=self.idle_behavior,
            threat_response=self.threat_response,
            player_attitude=self.player_attitude,
            memory_duration=self.memory_duration,
            grudge_factor=self.grudge_factor
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "traits": self.traits,
            "idle_behavior": self.idle_behavior.name,
            "threat_response": self.threat_response.name,
            "player_attitude": self.player_attitude.name,
            "memory_duration": self.memory_duration,
            "grudge_factor": self.grudge_factor
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PersonalityTemplate":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            traits=data.get("traits", {}),
            idle_behavior=IdleBehavior[data.get("idle_behavior", "WANDER")],
            threat_response=ThreatResponse[data.get("threat_response", "FLEE")],
            player_attitude=Attitude[data.get("player_attitude", "NEUTRAL")],
            memory_duration=data.get("memory_duration", 24.0),
            grudge_factor=data.get("grudge_factor", 0.5)
        )


# Predefined personality templates
PERSONALITY_TEMPLATES: Dict[str, PersonalityTemplate] = {
    "timid_prey": PersonalityTemplate(
        name="Timid Prey",
        traits={"fear": 0.9, "curiosity": 0.3, "aggression": 0.1, "loyalty": 0.2, "greed": 0.4, "social": 0.6},
        idle_behavior=IdleBehavior.FORAGE,
        threat_response=ThreatResponse.FLEE,
        player_attitude=Attitude.AFRAID
    ),

    "territorial_predator": PersonalityTemplate(
        name="Territorial Predator",
        traits={"aggression": 0.8, "fear": 0.2, "curiosity": 0.4, "loyalty": 0.3, "greed": 0.6, "social": 0.2},
        idle_behavior=IdleBehavior.PATROL,
        threat_response=ThreatResponse.CHALLENGE,
        player_attitude=Attitude.HOSTILE
    ),

    "curious_neutral": PersonalityTemplate(
        name="Curious Neutral",
        traits={"curiosity": 0.8, "fear": 0.4, "social": 0.6, "aggression": 0.2, "loyalty": 0.4, "greed": 0.3},
        idle_behavior=IdleBehavior.WANDER,
        threat_response=ThreatResponse.OBSERVE,
        player_attitude=Attitude.CURIOUS
    ),

    "loyal_guardian": PersonalityTemplate(
        name="Loyal Guardian",
        traits={"loyalty": 0.9, "aggression": 0.5, "fear": 0.1, "curiosity": 0.3, "greed": 0.1, "social": 0.4},
        idle_behavior=IdleBehavior.GUARD,
        threat_response=ThreatResponse.PROTECT,
        player_attitude=Attitude.NEUTRAL
    ),

    "greedy_collector": PersonalityTemplate(
        name="Greedy Collector",
        traits={"greed": 0.9, "curiosity": 0.5, "aggression": 0.4, "fear": 0.5, "loyalty": 0.1, "social": 0.2},
        idle_behavior=IdleBehavior.SEARCH,
        threat_response=ThreatResponse.PROTECT_HOARD,
        player_attitude=Attitude.SUSPICIOUS
    ),

    "friendly_helper": PersonalityTemplate(
        name="Friendly Helper",
        traits={"social": 0.9, "loyalty": 0.7, "curiosity": 0.6, "aggression": 0.1, "fear": 0.3, "greed": 0.1},
        idle_behavior=IdleBehavior.SOCIALIZE,
        threat_response=ThreatResponse.ALERT_OTHERS,
        player_attitude=Attitude.FRIENDLY
    ),

    "paranoid_merchant": PersonalityTemplate(
        name="Paranoid Merchant",
        traits={"greed": 0.9, "fear": 0.8, "social": 0.6, "aggression": 0.4, "curiosity": 0.3, "loyalty": 0.0},
        idle_behavior=IdleBehavior.GUARD,
        threat_response=ThreatResponse.BRIBE,
        player_attitude=Attitude.SUSPICIOUS,
        memory_duration=168.0,  # One week
        grudge_factor=0.9
    ),

    "sleepy_creature": PersonalityTemplate(
        name="Sleepy Creature",
        traits={"fear": 0.3, "aggression": 0.2, "curiosity": 0.2, "loyalty": 0.5, "greed": 0.3, "social": 0.4},
        idle_behavior=IdleBehavior.SLEEP,
        threat_response=ThreatResponse.IGNORE,
        player_attitude=Attitude.NEUTRAL,
        memory_duration=1.0
    )
}


def get_template(name: str) -> Optional[PersonalityTemplate]:
    """Get a predefined template by name."""
    return PERSONALITY_TEMPLATES.get(name)


def list_templates() -> list[str]:
    """Get list of available template names."""
    return list(PERSONALITY_TEMPLATES.keys())
