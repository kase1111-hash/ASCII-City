"""
Rumor - A propagating, mutating piece of information.

A rumor is a memory that has left its original owner and mutated through
retelling. Each transmission applies mutation - details change, emotions
shift, attributions wander.

None are lies. None are true. All are dangerous.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
from copy import deepcopy
import random
import uuid

from .npc_memory import NPCMemory, MemorySource
from .npc_bias import NPCBias


@dataclass
class Rumor:
    """
    A propagating, mutating piece of information.

    Rumors spread through the NPC network, changing with each retelling.
    They are the primary mechanism for emergent storylines.
    """

    rumor_id: str = ""

    # Content
    core_claim: str = ""            # The main assertion
    details: list[str] = field(default_factory=list)  # Supporting details
    tags: list[str] = field(default_factory=list)

    # Propagation state
    confidence: float = 0.5         # How believed it is
    distortion: float = 0.0         # How far from truth (0.0 = accurate)
    spread_count: int = 0           # How many times retold
    carrier_count: int = 1          # How many NPCs know it

    # Carriers
    carriers: set[str] = field(default_factory=set)  # NPCs who know this rumor

    # Origin
    origin_event: Optional[str] = None  # Original event ID (may be lost)
    origin_memory: Optional[str] = None  # Original memory ID
    origin_npc: Optional[str] = None     # Who started it
    origin_location: str = ""
    origin_timestamp: float = 0.0

    # Current state
    last_updated: float = 0.0
    is_active: bool = True          # Still spreading?

    # Mutation history
    mutation_history: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.rumor_id:
            self.rumor_id = f"rum_{uuid.uuid4().hex[:12]}"
        if isinstance(self.carriers, list):
            self.carriers = set(self.carriers)

    def add_carrier(self, npc_id: str) -> None:
        """Add an NPC as a carrier of this rumor."""
        if npc_id not in self.carriers:
            self.carriers.add(npc_id)
            self.carrier_count = len(self.carriers)

    def is_carrier(self, npc_id: str) -> bool:
        """Check if NPC knows this rumor."""
        return npc_id in self.carriers

    def has_tag(self, tag: str) -> bool:
        """Check if rumor has a specific tag."""
        return tag in self.tags

    def add_tag(self, tag: str) -> None:
        """Add a tag to this rumor."""
        if tag not in self.tags:
            self.tags.append(tag)

    def record_mutation(self, mutation_type: str) -> None:
        """Record that a mutation occurred."""
        self.mutation_history.append(mutation_type)

    def to_dict(self) -> dict:
        """Serialize rumor to dictionary."""
        return {
            "rumor_id": self.rumor_id,
            "core_claim": self.core_claim,
            "details": self.details,
            "tags": self.tags,
            "confidence": self.confidence,
            "distortion": self.distortion,
            "spread_count": self.spread_count,
            "carrier_count": self.carrier_count,
            "carriers": list(self.carriers),
            "origin_event": self.origin_event,
            "origin_memory": self.origin_memory,
            "origin_npc": self.origin_npc,
            "origin_location": self.origin_location,
            "origin_timestamp": self.origin_timestamp,
            "last_updated": self.last_updated,
            "is_active": self.is_active,
            "mutation_history": self.mutation_history
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Rumor':
        """Deserialize rumor from dictionary."""
        data["carriers"] = set(data.get("carriers", []))
        return cls(**data)

    @classmethod
    def from_memory(cls, memory: NPCMemory, npc_id: str) -> 'Rumor':
        """Create a rumor from an NPC's memory."""
        rumor = cls(
            core_claim=memory.summary,
            details=[],
            tags=memory.tags.copy(),
            confidence=memory.confidence * 0.9,  # Slight confidence loss
            distortion=0.0,
            spread_count=0,
            carrier_count=1,
            carriers={npc_id},
            origin_event=memory.event_id,
            origin_memory=memory.memory_id,
            origin_npc=npc_id,
            origin_location=memory.location or "",
            origin_timestamp=memory.timestamp,
            last_updated=memory.timestamp,
            is_active=True
        )
        return rumor


class RumorMutation:
    """
    How rumors change as they spread.

    Each transmission applies mutation - details change, emotions shift,
    attributions wander. This creates the "telephone game" effect.
    """

    # Exaggeration mappings
    EXAGGERATIONS = {
        "someone got hurt": "someone nearly died",
        "someone nearly died": "someone died",
        "there was a shooting": "there was a massacre",
        "something was stolen": "there was a major robbery",
        "they were arguing": "they were fighting",
        "suspicious activity": "criminal activity",
        "someone was seen": "someone was caught",
        "there was an accident": "there was a terrible accident"
    }

    # Misattribution mappings
    MISATTRIBUTIONS = {
        "accident": "murder",
        "fell": "was pushed",
        "stranger": "that detective",
        "someone": "the mob",
        "argument": "conspiracy",
        "robbery": "mob hit"
    }

    # Simplification - details to drop
    DROPPABLE_DETAILS = [
        "at night",
        "in the rain",
        "quietly",
        "nervously",
        "alone"
    ]

    def mutate(
        self,
        rumor: Rumor,
        source_bias: NPCBias,
        target_bias: NPCBias,
        current_time: float
    ) -> Rumor:
        """
        Apply mutation when rumor transfers between NPCs.

        Returns a new, mutated rumor.
        """
        mutated = Rumor(
            rumor_id=rumor.rumor_id,  # Same rumor, just mutated
            core_claim=rumor.core_claim,
            details=rumor.details.copy(),
            tags=rumor.tags.copy(),
            confidence=rumor.confidence,
            distortion=rumor.distortion,
            spread_count=rumor.spread_count,
            carrier_count=rumor.carrier_count,
            carriers=rumor.carriers.copy(),
            origin_event=rumor.origin_event,
            origin_memory=rumor.origin_memory,
            origin_npc=rumor.origin_npc,
            origin_location=rumor.origin_location,
            origin_timestamp=rumor.origin_timestamp,
            last_updated=current_time,
            is_active=rumor.is_active,
            mutation_history=rumor.mutation_history.copy()
        )

        # Confidence decreases slightly with each retelling
        mutated.confidence *= 0.9

        # Distortion increases
        mutated.distortion = min(1.0, mutated.distortion + 0.1)

        # Track spread
        mutated.spread_count += 1

        # Apply source bias to content
        mutated.core_claim = self._apply_source_bias(
            mutated.core_claim,
            source_bias
        )

        # Apply target bias to reception
        mutated.details = self._filter_by_target_bias(
            mutated.details,
            target_bias
        )

        # Random mutations based on probability
        if random.random() < 0.2:
            mutated = self._simplify(mutated)
        if random.random() < 0.15:
            mutated = self._exaggerate(mutated, source_bias)
        if random.random() < 0.1:
            mutated = self._personalize(mutated, source_bias)
        if random.random() < 0.1:
            mutated = self._misattribute(mutated)

        return mutated

    def _apply_source_bias(self, claim: str, bias: NPCBias) -> str:
        """Apply source NPC's bias to the claim."""
        # Dramatic sources exaggerate
        if bias.dramatic > 0.6:
            lower_claim = claim.lower()
            for old, new in self.EXAGGERATIONS.items():
                if old in lower_claim:
                    return claim.lower().replace(old, new).capitalize()

        # Paranoid sources add suspicion
        if bias.paranoid > 0.7 and random.random() < 0.3:
            if "they" not in claim.lower():
                return f"Word is, {claim.lower()}"

        return claim

    def _filter_by_target_bias(
        self,
        details: list[str],
        bias: NPCBias
    ) -> list[str]:
        """Filter details based on target's reception bias."""
        if not details:
            return details

        filtered = details.copy()

        # Cynical targets filter out hopeful details
        if bias.cynical > 0.6:
            filtered = [d for d in filtered if "help" not in d.lower()]

        # Forgetful targets lose details
        if bias.forgetful > 0.5 and len(filtered) > 1:
            if random.random() < bias.forgetful:
                filtered.pop(random.randint(0, len(filtered) - 1))

        return filtered

    def _simplify(self, rumor: Rumor) -> Rumor:
        """Remove details, keep core claim."""
        if rumor.details:
            # Keep at least one detail
            rumor.details = rumor.details[:max(1, len(rumor.details) - 1)]
            rumor.record_mutation("simplified")
        return rumor

    def _exaggerate(self, rumor: Rumor, bias: NPCBias) -> Rumor:
        """Make it more dramatic."""
        lower_claim = rumor.core_claim.lower()

        for old, new in self.EXAGGERATIONS.items():
            if old in lower_claim:
                if bias.fearful > 0.5 or bias.dramatic > 0.5:
                    rumor.core_claim = lower_claim.replace(old, new).capitalize()
                    rumor.distortion += 0.1
                    rumor.record_mutation("exaggerated")
                    break

        return rumor

    def _personalize(self, rumor: Rumor, source_bias: NPCBias) -> Rumor:
        """Add personal connection."""
        if "stranger" in rumor.core_claim.lower():
            if random.random() < 0.3:
                rumor.details.append("Someone I know was there")
                rumor.record_mutation("personalized")
        return rumor

    def _misattribute(self, rumor: Rumor) -> Rumor:
        """Blame the wrong person/cause."""
        lower_claim = rumor.core_claim.lower()

        for old, new in self.MISATTRIBUTIONS.items():
            if old in lower_claim:
                if random.random() < 0.3:
                    rumor.core_claim = lower_claim.replace(old, new).capitalize()
                    rumor.distortion += 0.2
                    rumor.record_mutation("misattributed")
                    break

        return rumor


class PropagationTrigger(Enum):
    """Conditions that cause rumor transmission."""
    CONVERSATION = "conversation"       # Natural conversation
    OVERHEAR = "overhear"              # One NPC near another
    DRINKING = "drinking"              # At bar, alcohol loosens tongues
    GOSSIP = "gossip"                  # Idle chatter
    THREATENED = "threatened"          # Fear makes them talk
    BRIBED = "bribed"                  # Money makes them talk
    INTERROGATED = "interrogated"      # Pressure makes them talk


class RumorPropagation:
    """
    Engine for spreading rumors between NPCs.

    Handles when and how rumors spread, and applies mutations.
    """

    # Base probabilities by trigger
    TRIGGER_PROBABILITIES = {
        PropagationTrigger.CONVERSATION: 0.3,
        PropagationTrigger.OVERHEAR: 0.15,
        PropagationTrigger.DRINKING: 0.6,
        PropagationTrigger.GOSSIP: 0.8,
        PropagationTrigger.THREATENED: 0.9,
        PropagationTrigger.BRIBED: 0.95,
        PropagationTrigger.INTERROGATED: 0.85
    }

    def __init__(self):
        self.mutation_system = RumorMutation()
        self.active_rumors: dict[str, Rumor] = {}  # rumor_id -> Rumor

    def should_propagate(
        self,
        source_bias: NPCBias,
        target_id: str,
        trigger: PropagationTrigger
    ) -> bool:
        """Determine if rumor spreads in this interaction."""
        base_prob = self.TRIGGER_PROBABILITIES.get(trigger, 0.2)

        # Modify by relationship
        if target_id in source_bias.allies:
            base_prob *= 1.5
        if target_id in source_bias.enemies:
            base_prob *= 0.3

        # Modify by source personality
        base_prob *= source_bias.get_share_probability_modifier()

        return random.random() < min(1.0, base_prob)

    def select_rumor_to_share(
        self,
        source_rumors: list[Rumor],
        source_bias: NPCBias,
        context_tags: list[str] = None
    ) -> Optional[Rumor]:
        """
        Select which rumor to share based on context and bias.

        Returns the selected rumor or None if nothing to share.
        """
        if not source_rumors:
            return None

        # Filter by context if provided
        if context_tags:
            relevant = [
                r for r in source_rumors
                if any(tag in r.tags for tag in context_tags)
            ]
            if relevant:
                source_rumors = relevant

        # Weight by emotional value and bias
        weighted = []
        for rumor in source_rumors:
            weight = rumor.confidence

            # Dramatic NPCs prefer dramatic rumors
            if source_bias.dramatic > 0.5:
                if "death" in rumor.tags or "violence" in rumor.tags:
                    weight *= 1.5

            # Paranoid NPCs prefer conspiracy rumors
            if source_bias.paranoid > 0.5:
                if "conspiracy" in rumor.tags or "suspicious" in rumor.tags:
                    weight *= 1.5

            # Recent rumors preferred
            recency_bonus = 1.0  # Could factor in rumor age

            weighted.append((rumor, weight * recency_bonus))

        # Weighted random selection
        total = sum(w for _, w in weighted)
        if total == 0:
            return random.choice(source_rumors) if source_rumors else None

        r = random.random() * total
        cumulative = 0
        for rumor, weight in weighted:
            cumulative += weight
            if r <= cumulative:
                return rumor

        return source_rumors[0] if source_rumors else None

    def propagate(
        self,
        rumor: Rumor,
        source_id: str,
        source_bias: NPCBias,
        target_id: str,
        target_bias: NPCBias,
        trigger: PropagationTrigger,
        current_time: float
    ) -> Optional[Rumor]:
        """
        Attempt to propagate a rumor from source to target.

        Returns the (possibly mutated) rumor if successful, None otherwise.
        """
        # Check if should propagate
        if not self.should_propagate(source_bias, target_id, trigger):
            return None

        # Target already knows this rumor
        if rumor.is_carrier(target_id):
            return None

        # Apply mutation
        mutated = self.mutation_system.mutate(
            rumor,
            source_bias,
            target_bias,
            current_time
        )

        # Add target as carrier
        mutated.add_carrier(target_id)

        # Update tracking
        self.active_rumors[mutated.rumor_id] = mutated

        return mutated

    def convert_memory_to_rumor(
        self,
        memory: NPCMemory,
        npc_id: str
    ) -> Rumor:
        """Convert an NPC's memory into a shareable rumor."""
        rumor = Rumor.from_memory(memory, npc_id)
        self.active_rumors[rumor.rumor_id] = rumor
        return rumor

    def get_rumors_by_tag(self, tag: str) -> list[Rumor]:
        """Get all active rumors with a specific tag."""
        return [r for r in self.active_rumors.values() if r.has_tag(tag)]

    def get_rumors_about_location(self, location: str) -> list[Rumor]:
        """Get all rumors originating from a location."""
        return [
            r for r in self.active_rumors.values()
            if r.origin_location == location
        ]

    def get_rumors_known_by(self, npc_id: str) -> list[Rumor]:
        """Get all rumors an NPC knows."""
        return [
            r for r in self.active_rumors.values()
            if r.is_carrier(npc_id)
        ]

    def decay_rumors(self, dt: float) -> None:
        """Decay inactive rumors over time."""
        for rumor in list(self.active_rumors.values()):
            # Rumors become inactive if confidence drops too low
            if rumor.confidence < 0.1:
                rumor.is_active = False

            # Remove very old, inactive rumors
            if not rumor.is_active and rumor.carrier_count < 2:
                del self.active_rumors[rumor.rumor_id]
