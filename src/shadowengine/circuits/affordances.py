"""
Affordance system for behavioral circuits.

Affordances define what can be done to/with an entity.
They are inherited from terrain and can be overridden by entities.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


@dataclass
class Affordance:
    """A single affordance (interaction possibility)."""
    name: str
    description: str = ""
    requires_tool: Optional[str] = None  # Tool needed to use this affordance
    skill_required: float = 0.0          # Skill level needed (0-1)
    energy_cost: float = 0.0             # Energy cost to use
    cooldown: float = 0.0                # Seconds before can use again

    def can_use(
        self,
        has_tool: bool = True,
        skill_level: float = 1.0,
        energy: float = 1.0
    ) -> bool:
        """Check if this affordance can be used."""
        if self.requires_tool and not has_tool:
            return False
        if skill_level < self.skill_required:
            return False
        if energy < self.energy_cost:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "requires_tool": self.requires_tool,
            "skill_required": self.skill_required,
            "energy_cost": self.energy_cost,
            "cooldown": self.cooldown
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Affordance':
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            requires_tool=data.get("requires_tool"),
            skill_required=data.get("skill_required", 0.0),
            energy_cost=data.get("energy_cost", 0.0),
            cooldown=data.get("cooldown", 0.0)
        )


class AffordanceSet:
    """A collection of affordances that can be modified."""

    def __init__(self, affordances: Optional[list[str]] = None):
        self._affordances: set[str] = set(affordances or [])
        self._blocked: set[str] = set()
        self._details: dict[str, Affordance] = {}

    def add(self, affordance: str, details: Optional[Affordance] = None) -> None:
        """Add an affordance."""
        self._affordances.add(affordance)
        if details:
            self._details[affordance] = details

    def remove(self, affordance: str) -> None:
        """Remove an affordance."""
        self._affordances.discard(affordance)

    def block(self, affordance: str) -> None:
        """Block an affordance (prevents inheritance)."""
        self._blocked.add(affordance)
        self._affordances.discard(affordance)

    def unblock(self, affordance: str) -> None:
        """Unblock an affordance."""
        self._blocked.discard(affordance)

    def has(self, affordance: str) -> bool:
        """Check if affordance is available."""
        return affordance in self._affordances and affordance not in self._blocked

    def get_all(self) -> list[str]:
        """Get all available affordances."""
        return list(self._affordances - self._blocked)

    def get_blocked(self) -> list[str]:
        """Get all blocked affordances."""
        return list(self._blocked)

    def get_details(self, affordance: str) -> Optional[Affordance]:
        """Get detailed affordance info if available."""
        return self._details.get(affordance)

    def inherit_from(self, parent: 'AffordanceSet') -> None:
        """Inherit affordances from parent (e.g., tile to entity)."""
        for aff in parent.get_all():
            if aff not in self._blocked:
                self._affordances.add(aff)
                if aff in parent._details:
                    self._details[aff] = parent._details[aff]

    def merge_with(self, other: 'AffordanceSet') -> 'AffordanceSet':
        """Create new set merging this with another."""
        result = AffordanceSet(list(self._affordances))
        result._blocked = self._blocked.copy()
        result._details = self._details.copy()
        result.inherit_from(other)
        return result

    def to_dict(self) -> dict:
        return {
            "affordances": list(self._affordances),
            "blocked": list(self._blocked),
            "details": {k: v.to_dict() for k, v in self._details.items()}
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AffordanceSet':
        aff_set = cls(data.get("affordances", []))
        aff_set._blocked = set(data.get("blocked", []))
        aff_set._details = {
            k: Affordance.from_dict(v)
            for k, v in data.get("details", {}).items()
        }
        return aff_set

    def __len__(self) -> int:
        return len(self._affordances - self._blocked)

    def __contains__(self, item: str) -> bool:
        return self.has(item)

    def __iter__(self):
        return iter(self.get_all())


# Default affordances by terrain/material type
DEFAULT_AFFORDANCES = {
    # Terrain types
    "rock": ["climbable", "breakable", "solid", "mineable"],
    "water": ["swimmable", "splashable", "drownable", "drinkable"],
    "soil": ["diggable", "plantable", "trackable"],
    "metal": ["conductive", "climbable", "resonant", "magnetic"],
    "wood": ["flammable", "climbable", "breakable", "carvable"],
    "glass": ["breakable", "transparent", "reflective"],
    "void": ["fallable", "echoing"],

    # Material modifiers
    "wet": ["slippery", "conductive"],
    "frozen": ["slippery", "breakable"],
    "hot": ["dangerous", "glowing"],
    "rusted": ["weak", "rough"],

    # Object types
    "door": ["openable", "closable", "lockable"],
    "container": ["openable", "searchable", "storable"],
    "button": ["pressable", "activatable"],
    "lever": ["pullable", "activatable"],
    "ladder": ["climbable"],
    "chair": ["sittable", "movable"],
    "table": ["usable", "hideable"],

    # Entity types
    "creature": ["talkable", "fightable", "tradeable"],
    "npc": ["talkable", "tradeable", "followable"],
    "item": ["collectible", "usable", "droppable"],
}


def get_default_affordances(category: str) -> list[str]:
    """Get default affordances for a category."""
    return DEFAULT_AFFORDANCES.get(category, []).copy()


def create_affordance_set(categories: list[str]) -> AffordanceSet:
    """Create an affordance set from multiple categories."""
    affordances = []
    for cat in categories:
        affordances.extend(get_default_affordances(cat))
    return AffordanceSet(list(set(affordances)))
