"""
Inventory - Player item storage and management.

Manages:
- Item collection and removal
- Item examination and use
- Item combination
- Evidence tracking
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from .item import Item, Evidence, ItemType


@dataclass
class Inventory:
    """
    Player inventory for managing collected items.

    Supports categorization, searching, and item interactions.
    """

    items: dict[str, Item] = field(default_factory=dict)
    max_capacity: int = 50

    # Callbacks for inventory events
    _on_add_callbacks: list[Callable[[Item], None]] = field(
        default_factory=list, repr=False
    )
    _on_remove_callbacks: list[Callable[[Item], None]] = field(
        default_factory=list, repr=False
    )

    def add(self, item: Item) -> bool:
        """
        Add an item to inventory.

        Returns True if successful.
        """
        if len(self.items) >= self.max_capacity:
            return False

        self.items[item.id] = item

        for callback in self._on_add_callbacks:
            callback(item)

        return True

    def remove(self, item_id: str) -> Optional[Item]:
        """
        Remove an item from inventory.

        Returns the removed item or None if not found.
        """
        if item_id not in self.items:
            return None

        item = self.items.pop(item_id)

        for callback in self._on_remove_callbacks:
            callback(item)

        return item

    def get(self, item_id: str) -> Optional[Item]:
        """Get an item by ID."""
        return self.items.get(item_id)

    def has(self, item_id: str) -> bool:
        """Check if inventory contains an item."""
        return item_id in self.items

    def count(self) -> int:
        """Get number of items in inventory."""
        return len(self.items)

    def is_full(self) -> bool:
        """Check if inventory is at capacity."""
        return len(self.items) >= self.max_capacity

    def get_all(self) -> list[Item]:
        """Get all items."""
        return list(self.items.values())

    def get_by_type(self, item_type: ItemType) -> list[Item]:
        """Get all items of a specific type."""
        return [
            item for item in self.items.values()
            if item.item_type == item_type
        ]

    def get_evidence(self) -> list[Evidence]:
        """Get all evidence items."""
        return [
            item for item in self.items.values()
            if isinstance(item, Evidence)
        ]

    def get_presentable_evidence(self) -> list[Evidence]:
        """Get evidence that can be presented to NPCs."""
        return [
            item for item in self.get_evidence()
            if item.can_be_presented
        ]

    def get_keys(self) -> list[Item]:
        """Get all key items."""
        return self.get_by_type(ItemType.KEY)

    def get_usable_on(self, target_id: str) -> list[Item]:
        """Get items that can be used on a target."""
        return [
            item for item in self.items.values()
            if item.can_use_on(target_id)
        ]

    def get_unlocking_item(self, hotspot_id: str) -> Optional[Item]:
        """Get item that unlocks a specific hotspot."""
        for item in self.items.values():
            if item.unlocks == hotspot_id:
                return item
        return None

    def examine(self, item_id: str) -> Optional[str]:
        """
        Examine an item.

        Returns examination text or None if not found.
        """
        item = self.get(item_id)
        if item:
            return item.examine()
        return None

    def use_item(self, item_id: str, target_id: str = None) -> tuple[bool, str]:
        """
        Use an item, optionally on a target.

        Returns (success, message).
        """
        item = self.get(item_id)
        if not item:
            return False, "You don't have that item."

        if not item.usable:
            return False, f"You can't use the {item.name} like that."

        if target_id and not item.can_use_on(target_id):
            return False, f"The {item.name} doesn't work on that."

        message = item.use_text or f"You use the {item.name}."

        if item.consumed_on_use:
            self.remove(item_id)
            message += f" The {item.name} is consumed."

        return True, message

    def combine(
        self,
        item1_id: str,
        item2_id: str,
        result_factory: Callable[[Item, Item], Item] = None
    ) -> tuple[bool, Optional[Item], str]:
        """
        Combine two items.

        Returns (success, new_item_or_None, message).
        """
        item1 = self.get(item1_id)
        item2 = self.get(item2_id)

        if not item1:
            return False, None, f"You don't have the first item."
        if not item2:
            return False, None, f"You don't have the second item."

        if not item1.can_combine_with(item2_id):
            return False, None, f"These items can't be combined."

        # Create result item
        if result_factory:
            result = result_factory(item1, item2)
        elif item1.combination_result:
            # Simple result - create a generic combined item
            result = Item(
                id=item1.combination_result,
                name=f"Combined {item1.name}",
                description=f"A combination of {item1.name} and {item2.name}",
                item_type=item1.item_type
            )
        else:
            return False, None, "No result defined for this combination."

        # Remove source items and add result
        self.remove(item1_id)
        self.remove(item2_id)
        self.add(result)

        return True, result, f"You combine the items into {result.name}."

    def search(self, query: str) -> list[Item]:
        """Search items by name or description."""
        query_lower = query.lower()
        return [
            item for item in self.items.values()
            if query_lower in item.name.lower()
            or query_lower in item.description.lower()
        ]

    def on_add(self, callback: Callable[[Item], None]) -> None:
        """Register callback for when items are added."""
        self._on_add_callbacks.append(callback)

    def on_remove(self, callback: Callable[[Item], None]) -> None:
        """Register callback for when items are removed."""
        self._on_remove_callbacks.append(callback)

    def get_display_list(self) -> list[str]:
        """Get a formatted list for display."""
        if not self.items:
            return ["(empty)"]

        lines = []
        for item in self.items.values():
            type_indicator = ""
            if item.item_type == ItemType.KEY:
                type_indicator = " [key]"
            elif item.item_type == ItemType.EVIDENCE:
                type_indicator = " [evidence]"
            elif item.item_type == ItemType.DOCUMENT:
                type_indicator = " [document]"

            lines.append(f"- {item.name}{type_indicator}")

        return lines

    def to_dict(self) -> dict:
        """Serialize inventory."""
        items_data = {}
        for item_id, item in self.items.items():
            if isinstance(item, Evidence):
                items_data[item_id] = {
                    "type": "Evidence",
                    "data": item.to_dict()
                }
            else:
                items_data[item_id] = {
                    "type": "Item",
                    "data": item.to_dict()
                }

        return {
            "items": items_data,
            "max_capacity": self.max_capacity
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Inventory":
        """Deserialize inventory."""
        inventory = cls(max_capacity=data.get("max_capacity", 50))

        for item_id, item_data in data.get("items", {}).items():
            if item_data["type"] == "Evidence":
                item = Evidence.from_dict(item_data["data"])
            else:
                item = Item.from_dict(item_data["data"])
            inventory.items[item_id] = item

        return inventory
