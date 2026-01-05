"""
NPC Intelligence - Deep NPC memory and social dynamics.

Phase 7 Implementation: Persistent NPC memory, rumor propagation,
trust/fear modeling, NPC relationships, and emergent social storylines.

Core principle: NPCs respond to what they believe is true, not what is true.
"""

from .world_event import WorldEvent, WitnessType
from .npc_memory import NPCMemory, MemorySource, MemoryDecaySystem
from .npc_bias import NPCBias, BiasProcessor
from .rumor import Rumor, RumorMutation, RumorPropagation
from .tile_memory import TileMemory, TileMemoryManager
from .behavior_mapping import (
    MemoryBehaviorMapping,
    BehaviorModifier,
    MEMORY_TAG_BEHAVIORS
)
from .social_network import (
    SocialNetwork,
    SocialRelation,
    RelationshipDynamics
)
from .propagation_engine import PropagationEngine

__all__ = [
    # World Events
    "WorldEvent",
    "WitnessType",
    # NPC Memory
    "NPCMemory",
    "MemorySource",
    "MemoryDecaySystem",
    # NPC Bias
    "NPCBias",
    "BiasProcessor",
    # Rumors
    "Rumor",
    "RumorMutation",
    "RumorPropagation",
    # Tile Memory
    "TileMemory",
    "TileMemoryManager",
    # Behavior Mapping
    "MemoryBehaviorMapping",
    "BehaviorModifier",
    "MEMORY_TAG_BEHAVIORS",
    # Social Network
    "SocialNetwork",
    "SocialRelation",
    "RelationshipDynamics",
    # Engine
    "PropagationEngine",
]
