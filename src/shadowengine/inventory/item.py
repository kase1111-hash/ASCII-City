"""
Item System - Items and evidence that can be collected.

Items can be:
- Regular items (keys, tools, etc.)
- Evidence items (link to facts in the narrative)
- Combinable items (can be combined for new items/discoveries)
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto


class ItemType(Enum):
    """Types of items."""
    GENERIC = auto()      # Regular item
    KEY = auto()          # Opens something
    TOOL = auto()         # Can be used on things
    DOCUMENT = auto()     # Contains information
    EVIDENCE = auto()     # Links to narrative facts
    CONTAINER = auto()    # Can hold other items
    CONSUMABLE = auto()   # Can be used up


@dataclass
class Item:
    """
    A collectible item.

    Items can be taken, examined, used, and shown to NPCs.
    """

    id: str
    name: str
    description: str
    item_type: ItemType = ItemType.GENERIC

    # Examination
    examine_text: str = ""
    examined: bool = False

    # Usage
    usable: bool = False
    use_text: str = ""
    use_target: Optional[str] = None  # What it can be used on
    consumed_on_use: bool = False

    # Combination
    combinable: bool = False
    combines_with: list[str] = field(default_factory=list)
    combination_result: Optional[str] = None

    # Unlock
    unlocks: Optional[str] = None  # Hotspot ID it can unlock

    # Hidden properties (discovered on examine)
    hidden_properties: dict = field(default_factory=dict)

    def examine(self) -> str:
        """
        Examine the item, potentially revealing hidden properties.

        Returns examination text.
        """
        self.examined = True
        return self.examine_text or self.description

    def can_use_on(self, target_id: str) -> bool:
        """Check if item can be used on a target."""
        if not self.usable:
            return False
        if self.use_target is None:
            return True  # Can be used on anything
        return self.use_target == target_id

    def can_combine_with(self, other_id: str) -> bool:
        """Check if item can combine with another item."""
        return self.combinable and other_id in self.combines_with

    def to_dict(self) -> dict:
        """Serialize item."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type.name,
            "examine_text": self.examine_text,
            "examined": self.examined,
            "usable": self.usable,
            "use_text": self.use_text,
            "use_target": self.use_target,
            "consumed_on_use": self.consumed_on_use,
            "combinable": self.combinable,
            "combines_with": self.combines_with,
            "combination_result": self.combination_result,
            "unlocks": self.unlocks,
            "hidden_properties": self.hidden_properties
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        """Deserialize item."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            item_type=ItemType[data.get("item_type", "GENERIC")],
            examine_text=data.get("examine_text", ""),
            examined=data.get("examined", False),
            usable=data.get("usable", False),
            use_text=data.get("use_text", ""),
            use_target=data.get("use_target"),
            consumed_on_use=data.get("consumed_on_use", False),
            combinable=data.get("combinable", False),
            combines_with=data.get("combines_with", []),
            combination_result=data.get("combination_result"),
            unlocks=data.get("unlocks"),
            hidden_properties=data.get("hidden_properties", {})
        )


@dataclass
class Evidence(Item):
    """
    An evidence item that links to narrative facts.

    Evidence can be presented to NPCs for reactions
    and is tracked by the narrative spine.
    """

    # Link to narrative
    fact_id: str = ""                # Revelation/fact this proves
    related_facts: list[str] = field(default_factory=list)

    # NPC reactions
    implicates: list[str] = field(default_factory=list)  # NPCs this evidence implicates
    exonerates: list[str] = field(default_factory=list)  # NPCs this evidence clears

    # Presentation effects
    presentation_text: str = ""       # What to say when presenting
    can_be_presented: bool = True

    def __post_init__(self):
        """Ensure evidence type is set."""
        self.item_type = ItemType.EVIDENCE

    def get_presentation_intro(self) -> str:
        """Get intro text for presenting evidence."""
        return self.presentation_text or f"You show the {self.name}."

    def to_dict(self) -> dict:
        """Serialize evidence."""
        data = super().to_dict()
        data.update({
            "fact_id": self.fact_id,
            "related_facts": self.related_facts,
            "implicates": self.implicates,
            "exonerates": self.exonerates,
            "presentation_text": self.presentation_text,
            "can_be_presented": self.can_be_presented
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Evidence":
        """Deserialize evidence."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            examine_text=data.get("examine_text", ""),
            examined=data.get("examined", False),
            usable=data.get("usable", False),
            use_text=data.get("use_text", ""),
            use_target=data.get("use_target"),
            consumed_on_use=data.get("consumed_on_use", False),
            combinable=data.get("combinable", False),
            combines_with=data.get("combines_with", []),
            combination_result=data.get("combination_result"),
            unlocks=data.get("unlocks"),
            hidden_properties=data.get("hidden_properties", {}),
            fact_id=data.get("fact_id", ""),
            related_facts=data.get("related_facts", []),
            implicates=data.get("implicates", []),
            exonerates=data.get("exonerates", []),
            presentation_text=data.get("presentation_text", ""),
            can_be_presented=data.get("can_be_presented", True)
        )


# Factory functions

def create_key(
    id: str,
    name: str,
    description: str,
    unlocks: str,
    examine_text: str = ""
) -> Item:
    """Create a key item."""
    return Item(
        id=id,
        name=name,
        description=description,
        item_type=ItemType.KEY,
        examine_text=examine_text or f"A key that might unlock something.",
        usable=True,
        use_target=unlocks,
        unlocks=unlocks
    )


def create_document(
    id: str,
    name: str,
    description: str,
    content: str,
    fact_id: str = "",
    implicates: list[str] = None
) -> Evidence:
    """Create a document evidence item."""
    return Evidence(
        id=id,
        name=name,
        description=description,
        examine_text=content,
        fact_id=fact_id,
        implicates=implicates or [],
        presentation_text=f"You present the {name} and point to its contents."
    )


def create_physical_evidence(
    id: str,
    name: str,
    description: str,
    examine_text: str,
    fact_id: str,
    implicates: list[str] = None,
    exonerates: list[str] = None
) -> Evidence:
    """Create physical evidence."""
    return Evidence(
        id=id,
        name=name,
        description=description,
        examine_text=examine_text,
        fact_id=fact_id,
        implicates=implicates or [],
        exonerates=exonerates or [],
        presentation_text=f"You show the {name} and watch for a reaction."
    )
