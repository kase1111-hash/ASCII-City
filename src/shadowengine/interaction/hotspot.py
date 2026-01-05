"""
Hotspot System - Interactive elements in scenes.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum


class HotspotType(Enum):
    """Types of interactive hotspots."""
    PERSON = "person"           # An NPC
    OBJECT = "object"           # Examinable object
    ITEM = "item"               # Takeable item
    CONTAINER = "container"     # Something that opens
    EXIT = "exit"               # Way to another location
    EVIDENCE = "evidence"       # Evidence item


@dataclass
class Hotspot:
    """An interactive element in a scene."""

    id: str
    label: str                          # Short description shown to player
    hotspot_type: HotspotType
    position: tuple[int, int]           # (x, y) in scene
    description: str = ""               # Full description when examined

    # State
    number: int = 0                     # Display number (assigned at render)
    visible: bool = True                # Currently visible
    discovered: bool = False            # Player has seen it
    active: bool = True                 # Can be interacted with

    # Connections
    target_id: Optional[str] = None     # What it connects to (character, location, etc.)
    contents: list[str] = field(default_factory=list)  # Items inside (for containers)

    # Interaction
    examine_text: str = ""              # Text shown when examined
    take_text: str = ""                 # Text shown when taken (for items)
    use_text: str = ""                  # Text shown when used

    # Requirements
    requires_item: Optional[str] = None     # Item needed to interact
    requires_discovery: Optional[str] = None  # Fact needed to see

    # Results
    reveals_fact: Optional[str] = None      # Fact revealed on examine
    gives_item: Optional[str] = None        # Item received on take

    def get_default_action(self) -> str:
        """Get the default action for this hotspot type."""
        defaults = {
            HotspotType.PERSON: "talk",
            HotspotType.OBJECT: "examine",
            HotspotType.ITEM: "take",
            HotspotType.CONTAINER: "open",
            HotspotType.EXIT: "go",
            HotspotType.EVIDENCE: "examine"
        }
        return defaults.get(self.hotspot_type, "examine")

    def get_available_actions(self) -> list[str]:
        """Get all available actions for this hotspot."""
        actions = ["examine"]

        if self.hotspot_type == HotspotType.PERSON:
            actions.extend(["talk", "show"])
        elif self.hotspot_type == HotspotType.ITEM:
            actions.append("take")
        elif self.hotspot_type == HotspotType.CONTAINER:
            actions.append("open")
        elif self.hotspot_type == HotspotType.EXIT:
            actions.append("go")

        return actions

    def can_interact(self, player_items: set[str] = None, player_discoveries: set[str] = None) -> bool:
        """Check if player can currently interact with this hotspot."""
        if not self.active or not self.visible:
            return False

        player_items = player_items or set()
        player_discoveries = player_discoveries or set()

        if self.requires_item and self.requires_item not in player_items:
            return False

        if self.requires_discovery and self.requires_discovery not in player_discoveries:
            return False

        return True

    def mark_discovered(self) -> None:
        """Mark this hotspot as discovered by the player."""
        self.discovered = True

    def hide(self) -> None:
        """Hide this hotspot."""
        self.visible = False

    def show(self) -> None:
        """Show this hotspot."""
        self.visible = True

    def deactivate(self) -> None:
        """Deactivate this hotspot (e.g., item taken)."""
        self.active = False

    def to_dict(self) -> dict:
        """Serialize hotspot."""
        return {
            "id": self.id,
            "label": self.label,
            "hotspot_type": self.hotspot_type.value,
            "position": self.position,
            "description": self.description,
            "number": self.number,
            "visible": self.visible,
            "discovered": self.discovered,
            "active": self.active,
            "target_id": self.target_id,
            "contents": self.contents,
            "examine_text": self.examine_text,
            "take_text": self.take_text,
            "use_text": self.use_text,
            "requires_item": self.requires_item,
            "requires_discovery": self.requires_discovery,
            "reveals_fact": self.reveals_fact,
            "gives_item": self.gives_item
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Hotspot':
        """Deserialize hotspot."""
        data["hotspot_type"] = HotspotType(data["hotspot_type"])
        data["position"] = tuple(data["position"])
        return cls(**data)

    @classmethod
    def create_person(
        cls,
        id: str,
        name: str,
        position: tuple[int, int],
        character_id: str,
        description: str = ""
    ) -> 'Hotspot':
        """Factory method for creating a person hotspot."""
        return cls(
            id=id,
            label=name,
            hotspot_type=HotspotType.PERSON,
            position=position,
            description=description or f"You see {name}.",
            target_id=character_id,
            examine_text=description or f"{name} stands here."
        )

    @classmethod
    def create_exit(
        cls,
        id: str,
        label: str,
        position: tuple[int, int],
        destination: str,
        description: str = ""
    ) -> 'Hotspot':
        """Factory method for creating an exit hotspot."""
        return cls(
            id=id,
            label=label,
            hotspot_type=HotspotType.EXIT,
            position=position,
            description=description or f"This leads to {destination}.",
            target_id=destination,
            examine_text=description or f"A way to {destination}."
        )

    @classmethod
    def create_item(
        cls,
        id: str,
        label: str,
        position: tuple[int, int],
        description: str,
        item_id: str,
        take_text: str = ""
    ) -> 'Hotspot':
        """Factory method for creating a takeable item hotspot."""
        return cls(
            id=id,
            label=label,
            hotspot_type=HotspotType.ITEM,
            position=position,
            description=description,
            examine_text=description,
            take_text=take_text or f"You take the {label}.",
            gives_item=item_id
        )

    @classmethod
    def create_evidence(
        cls,
        id: str,
        label: str,
        position: tuple[int, int],
        description: str,
        fact_id: str
    ) -> 'Hotspot':
        """Factory method for creating an evidence hotspot."""
        return cls(
            id=id,
            label=label,
            hotspot_type=HotspotType.EVIDENCE,
            position=position,
            description=description,
            examine_text=description,
            reveals_fact=fact_id
        )

    def __repr__(self) -> str:
        return f"Hotspot({self.id}, {self.label}, {self.hotspot_type.value})"
