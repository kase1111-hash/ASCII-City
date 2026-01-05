"""
Inventory System - Item management and evidence presentation.

Provides:
- Item storage and management
- Evidence items with fact associations
- Evidence presentation to NPCs for reactions
"""

from .item import Item, ItemType, Evidence
from .inventory import Inventory
from .presentation import EvidencePresentation, PresentationResult

__all__ = [
    "Item",
    "ItemType",
    "Evidence",
    "Inventory",
    "EvidencePresentation",
    "PresentationResult",
]
