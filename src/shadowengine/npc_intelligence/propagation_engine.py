"""
PropagationEngine - Main engine for NPC intelligence.

Coordinates all NPC intelligence systems: memory formation, rumor
propagation, behavior updates, and social network dynamics.
"""

from dataclasses import dataclass
from typing import Optional, Any
import random

from .world_event import WorldEvent
from .npc_memory import NPCMemory, NPCMemoryBank, MemorySource
from .npc_bias import NPCBias, BiasProcessor
from .rumor import Rumor, RumorPropagation, PropagationTrigger
from .tile_memory import TileMemory, TileMemoryManager
from .behavior_mapping import MemoryBehaviorSystem, BehaviorModifier
from .social_network import SocialNetwork


@dataclass
class NPCIntelligenceState:
    """Complete intelligence state for an NPC."""
    npc_id: str
    npc_type: str = "default"
    memory_bank: NPCMemoryBank = None
    bias: NPCBias = None
    behavior_modifier: BehaviorModifier = None

    def __post_init__(self):
        if self.memory_bank is None:
            self.memory_bank = NPCMemoryBank(self.npc_id, self.npc_type)
        if self.bias is None:
            self.bias = NPCBias()
        if self.behavior_modifier is None:
            self.behavior_modifier = BehaviorModifier()


class PropagationEngine:
    """
    Main engine for NPC intelligence.

    Coordinates:
    - Event witnessing and memory formation
    - Rumor propagation between NPCs
    - Behavior updates based on memories
    - Social network dynamics
    - Tile memory updates
    """

    def __init__(self):
        # Core systems
        self.bias_processor = BiasProcessor()
        self.rumor_propagation = RumorPropagation()
        self.behavior_system = MemoryBehaviorSystem()
        self.social_network = SocialNetwork()
        self.tile_manager = TileMemoryManager()

        # NPC state
        self.npc_states: dict[str, NPCIntelligenceState] = {}

        # Event history
        self.events: list[WorldEvent] = []

        # Time tracking
        self.current_time: float = 0.0

    def register_npc(
        self,
        npc_id: str,
        npc_type: str = "default",
        bias: Optional[NPCBias] = None
    ) -> NPCIntelligenceState:
        """Register an NPC with the intelligence system."""
        if npc_id in self.npc_states:
            return self.npc_states[npc_id]

        state = NPCIntelligenceState(
            npc_id=npc_id,
            npc_type=npc_type,
            bias=bias or NPCBias.from_archetype(npc_type)
        )
        self.npc_states[npc_id] = state
        return state

    def get_npc_state(self, npc_id: str) -> Optional[NPCIntelligenceState]:
        """Get intelligence state for an NPC."""
        return self.npc_states.get(npc_id)

    def process_event(self, event: WorldEvent) -> list[NPCMemory]:
        """
        Process a world event through the intelligence system.

        1. Records event in history
        2. Creates memories for witnesses
        3. Updates tile memory
        4. Returns created memories
        """
        self.events.append(event)
        memories = []

        # Update tile memory
        self.tile_manager.record_event(
            location=event.location,
            location_name=event.location_name,
            event_id=event.id,
            event_type=event.event_type,
            tags=[],  # Tags come from memories
            timestamp=event.timestamp,
            severity=event.notability
        )

        # Create memories for each witness
        for witness in event.witnesses:
            npc_id = witness.npc_id

            # Ensure NPC is registered
            if npc_id not in self.npc_states:
                self.register_npc(npc_id)

            state = self.npc_states[npc_id]

            # Form memory using bias processor
            memory = self.bias_processor.form_memory_from_event(
                event=event,
                bias=state.bias,
                witness_type=witness.witness_type,
                npc_id=npc_id
            )

            # Add to NPC's memory bank
            state.memory_bank.add_memory(memory)
            memories.append(memory)

            # Update behavior based on new memory
            self.behavior_system.add_memory_effect(npc_id, memory)

            # Update tile memory with memory tags
            tile_mem = self.tile_manager.get_or_create(
                event.location, event.location_name
            )
            tile_mem.event_tags.update(memory.tags)

        return memories

    def simulate_interaction(
        self,
        npc_a: str,
        npc_b: str,
        trigger: PropagationTrigger = PropagationTrigger.CONVERSATION,
        location: Optional[tuple[int, int]] = None
    ) -> dict[str, Any]:
        """
        Simulate an interaction between two NPCs.

        May result in:
        - Rumor sharing
        - Memory sharing
        - Relationship changes
        """
        result = {
            "rumor_shared": False,
            "memory_shared": False,
            "relationship_changed": False,
            "details": {}
        }

        state_a = self.npc_states.get(npc_a)
        state_b = self.npc_states.get(npc_b)

        if not state_a or not state_b:
            return result

        # Record interaction in social network
        self.social_network.record_interaction(
            from_npc=npc_a,
            to_npc=npc_b,
            interaction_type=trigger.value,
            timestamp=self.current_time
        )
        result["relationship_changed"] = True

        # Check for rumor propagation
        shareable_memories = state_a.memory_bank.get_shareable_memories()
        if shareable_memories:
            # Convert memory to rumor if needed
            memory_to_share = random.choice(shareable_memories)

            # Check if already a rumor
            rumor = None
            existing_rumors = self.rumor_propagation.get_rumors_known_by(npc_a)
            for r in existing_rumors:
                if r.origin_memory == memory_to_share.memory_id:
                    rumor = r
                    break

            if not rumor:
                rumor = self.rumor_propagation.convert_memory_to_rumor(
                    memory_to_share, npc_a
                )

            # Attempt propagation
            propagated = self.rumor_propagation.propagate(
                rumor=rumor,
                source_id=npc_a,
                source_bias=state_a.bias,
                target_id=npc_b,
                target_bias=state_b.bias,
                trigger=trigger,
                current_time=self.current_time
            )

            if propagated:
                result["rumor_shared"] = True
                result["details"]["rumor_id"] = propagated.rumor_id
                result["details"]["rumor_claim"] = propagated.core_claim

                # Create memory in recipient from rumor
                recipient_memory = self._rumor_to_memory(propagated, npc_a, npc_b)
                state_b.memory_bank.add_memory(recipient_memory)
                result["memory_shared"] = True

                # Record in social network
                self.social_network.share_rumor_between(
                    npc_a, npc_b, propagated.rumor_id, self.current_time
                )

                # Update tile memory if at a location
                if location:
                    tile_mem = self.tile_manager.get_or_create(location)
                    tile_mem.add_rumor_activity()

        return result

    def _rumor_to_memory(
        self,
        rumor: Rumor,
        source_npc: str,
        target_npc: str
    ) -> NPCMemory:
        """Convert a received rumor into a memory."""
        target_state = self.npc_states.get(target_npc)

        # Determine source type based on relationship
        relation = self.social_network.get_relation(target_npc, source_npc)
        if relation and relation.trust > 50:
            source = MemorySource.FRIEND
        elif relation and relation.trust > 0:
            source = MemorySource.ACQUAINTANCE
        elif relation and relation.trust < -20:
            source = MemorySource.ENEMY
        else:
            source = MemorySource.RUMOR

        # Confidence based on source and target's trusting nature
        base_confidence = rumor.confidence
        if target_state:
            base_confidence *= (0.5 + target_state.bias.trusting * 0.5)

        return NPCMemory(
            event_id=rumor.origin_event,
            summary=rumor.core_claim,
            tags=rumor.tags.copy(),
            confidence=base_confidence,
            emotional_weight=0.4,  # Rumors less emotional than direct experience
            source=source,
            source_npc=source_npc,
            timestamp=self.current_time,
            location=rumor.origin_location,
            decay_rate=0.02,  # Rumors decay faster
            actors=[]
        )

    def update(self, dt: float) -> dict[str, Any]:
        """
        Update all intelligence systems.

        Should be called each game tick.
        """
        self.current_time += dt
        result = {
            "memories_decayed": 0,
            "social_events": [],
            "behaviors_updated": 0
        }

        # Update each NPC's memory bank
        for npc_id, state in self.npc_states.items():
            old_count = len(state.memory_bank.memories)
            state.memory_bank.update(dt)
            result["memories_decayed"] += old_count - len(state.memory_bank.memories)

            # Update behavior based on current memories
            state.behavior_modifier = self.behavior_system.update_npc_behavior(
                npc_id,
                state.memory_bank.memories,
                self.current_time
            )
            result["behaviors_updated"] += 1

        # Update tile memories
        self.tile_manager.update(dt)

        # Update social network
        social_events = self.social_network.update(dt)
        result["social_events"] = social_events

        # Decay rumors
        self.rumor_propagation.decay_rumors(dt)

        return result

    def get_npc_behavior_hints(self, npc_id: str) -> dict[str, Any]:
        """Get behavior hints for an NPC."""
        return self.behavior_system.get_npc_dialogue_hints(npc_id)

    def will_npc_cooperate(self, npc_id: str) -> bool:
        """Check if NPC will cooperate."""
        return self.behavior_system.will_npc_cooperate(npc_id)

    def will_npc_share_info(self, npc_id: str) -> bool:
        """Check if NPC will share information."""
        return self.behavior_system.will_npc_share(npc_id)

    def get_rumors_about(self, topic: str) -> list[Rumor]:
        """Get all rumors with a specific tag/topic."""
        return self.rumor_propagation.get_rumors_by_tag(topic)

    def get_rumors_at_location(self, location: str) -> list[Rumor]:
        """Get all rumors from a location."""
        return self.rumor_propagation.get_rumors_about_location(location)

    def get_npc_memories(self, npc_id: str) -> list[NPCMemory]:
        """Get all memories for an NPC."""
        state = self.npc_states.get(npc_id)
        if state:
            return state.memory_bank.memories
        return []

    def get_npc_memories_about(
        self,
        npc_id: str,
        subject: str
    ) -> list[NPCMemory]:
        """Get NPC's memories about a specific subject."""
        state = self.npc_states.get(npc_id)
        if state:
            return state.memory_bank.get_memories_about(subject)
        return []

    def get_emergent_storylines(self) -> list[dict]:
        """Get emergent storylines from social dynamics."""
        return self.social_network.get_emergent_storylines()

    def get_dangerous_locations(self) -> list[TileMemory]:
        """Get locations considered dangerous."""
        return self.tile_manager.get_dangerous_locations()

    def get_atmosphere_at(
        self,
        location: tuple[int, int]
    ) -> list[str]:
        """Get atmospheric hints at a location."""
        return self.tile_manager.get_all_hints_at(location)

    def player_spreads_rumor(
        self,
        target_npc: str,
        rumor_content: str,
        player_credibility: float = 0.5
    ) -> Rumor:
        """Player deliberately spreads a rumor."""
        rumor = Rumor(
            core_claim=rumor_content,
            tags=["player_spread"],
            confidence=player_credibility,
            distortion=0.0,  # Player knows it might be false
            origin_npc="player",
            origin_timestamp=self.current_time,
            is_active=True
        )
        rumor.add_carrier(target_npc)

        self.rumor_propagation.active_rumors[rumor.rumor_id] = rumor

        # Create memory in target
        target_state = self.npc_states.get(target_npc)
        if target_state:
            memory = NPCMemory(
                summary=rumor_content,
                tags=["player_said"],
                confidence=player_credibility * target_state.bias.trusting,
                source=MemorySource.ACQUAINTANCE,
                source_npc="player",
                timestamp=self.current_time
            )
            target_state.memory_bank.add_memory(memory)

        return rumor

    def to_dict(self) -> dict:
        """Serialize engine state."""
        return {
            "npc_states": {
                npc_id: {
                    "npc_id": state.npc_id,
                    "npc_type": state.npc_type,
                    "memory_bank": state.memory_bank.to_dict(),
                    "bias": state.bias.to_dict(),
                    "behavior_modifier": state.behavior_modifier.to_dict()
                }
                for npc_id, state in self.npc_states.items()
            },
            "events": [e.to_dict() for e in self.events],
            "active_rumors": {
                k: v.to_dict()
                for k, v in self.rumor_propagation.active_rumors.items()
            },
            "social_network": self.social_network.to_dict(),
            "tile_manager": self.tile_manager.to_dict(),
            "behavior_system": self.behavior_system.to_dict(),
            "current_time": self.current_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PropagationEngine':
        """Deserialize engine state."""
        engine = cls()

        # Restore NPC states
        for npc_id, state_data in data.get("npc_states", {}).items():
            state = NPCIntelligenceState(
                npc_id=state_data["npc_id"],
                npc_type=state_data.get("npc_type", "default"),
                memory_bank=NPCMemoryBank.from_dict(state_data["memory_bank"]),
                bias=NPCBias.from_dict(state_data["bias"]),
                behavior_modifier=BehaviorModifier.from_dict(
                    state_data["behavior_modifier"]
                )
            )
            engine.npc_states[npc_id] = state

        # Restore events
        engine.events = [
            WorldEvent.from_dict(e) for e in data.get("events", [])
        ]

        # Restore rumors
        engine.rumor_propagation.active_rumors = {
            k: Rumor.from_dict(v)
            for k, v in data.get("active_rumors", {}).items()
        }

        # Restore other systems
        engine.social_network = SocialNetwork.from_dict(
            data.get("social_network", {})
        )
        engine.tile_manager = TileMemoryManager.from_dict(
            data.get("tile_manager", {})
        )
        engine.behavior_system = MemoryBehaviorSystem.from_dict(
            data.get("behavior_system", {})
        )
        engine.current_time = data.get("current_time", 0.0)

        return engine
