"""
NPCBias - Personality traits that affect information processing.

Each NPC has bias coefficients that affect how they perceive events,
form memories, and retell information. The same event, witnessed by
different NPCs, will be remembered differently based on their biases.
"""

from dataclasses import dataclass, field
from typing import Optional
import copy
import random

from .npc_memory import NPCMemory, MemorySource
from .world_event import WorldEvent, WitnessType


@dataclass
class NPCBias:
    """
    Personality traits that affect information processing.

    All values range from 0.0 to 1.0.
    """

    # Fear & caution
    fearful: float = 0.5        # Sees danger everywhere
    paranoid: float = 0.3       # Suspects conspiracies

    # Social
    loyal: float = 0.5          # Protects allies in retelling
    talkative: float = 0.5      # Shares information freely

    # Self-interest
    greedy: float = 0.3         # Focuses on profit angles
    self_preserving: float = 0.5  # Omits self-incriminating details

    # Perception
    curious: float = 0.5        # Seeks more information
    dramatic: float = 0.3       # Exaggerates for effect
    cynical: float = 0.4        # Assumes worst motives

    # Trust
    trusting: float = 0.5       # Believes what they hear
    suspicious: float = 0.3     # Questions everything

    # Memory
    forgetful: float = 0.3      # How quickly memories decay
    obsessive: float = 0.2      # Fixates on certain topics

    # Relationships
    allies: list[str] = field(default_factory=list)
    enemies: list[str] = field(default_factory=list)

    def __post_init__(self):
        # Clamp all values to 0-1
        self.fearful = max(0.0, min(1.0, self.fearful))
        self.paranoid = max(0.0, min(1.0, self.paranoid))
        self.loyal = max(0.0, min(1.0, self.loyal))
        self.talkative = max(0.0, min(1.0, self.talkative))
        self.greedy = max(0.0, min(1.0, self.greedy))
        self.self_preserving = max(0.0, min(1.0, self.self_preserving))
        self.curious = max(0.0, min(1.0, self.curious))
        self.dramatic = max(0.0, min(1.0, self.dramatic))
        self.cynical = max(0.0, min(1.0, self.cynical))
        self.trusting = max(0.0, min(1.0, self.trusting))
        self.suspicious = max(0.0, min(1.0, self.suspicious))
        self.forgetful = max(0.0, min(1.0, self.forgetful))
        self.obsessive = max(0.0, min(1.0, self.obsessive))

    def get_memory_decay_modifier(self) -> float:
        """Get decay rate modifier based on forgetfulness."""
        return 1.0 + (self.forgetful * 0.5)  # Up to 50% faster decay

    def get_share_probability_modifier(self) -> float:
        """Get share probability modifier based on talkativeness."""
        return 0.5 + self.talkative  # 0.5 to 1.5x base probability

    def is_ally(self, npc_id: str) -> bool:
        """Check if someone is an ally."""
        return npc_id in self.allies

    def is_enemy(self, npc_id: str) -> bool:
        """Check if someone is an enemy."""
        return npc_id in self.enemies

    def to_dict(self) -> dict:
        """Serialize bias to dictionary."""
        return {
            "fearful": self.fearful,
            "paranoid": self.paranoid,
            "loyal": self.loyal,
            "talkative": self.talkative,
            "greedy": self.greedy,
            "self_preserving": self.self_preserving,
            "curious": self.curious,
            "dramatic": self.dramatic,
            "cynical": self.cynical,
            "trusting": self.trusting,
            "suspicious": self.suspicious,
            "forgetful": self.forgetful,
            "obsessive": self.obsessive,
            "allies": self.allies,
            "enemies": self.enemies
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'NPCBias':
        """Deserialize bias from dictionary."""
        return cls(**data)

    @classmethod
    def random(cls, seed: Optional[int] = None) -> 'NPCBias':
        """Generate random bias values."""
        rng = random.Random(seed)
        return cls(
            fearful=rng.random(),
            paranoid=rng.random(),
            loyal=rng.random(),
            talkative=rng.random(),
            greedy=rng.random(),
            self_preserving=rng.random(),
            curious=rng.random(),
            dramatic=rng.random(),
            cynical=rng.random(),
            trusting=rng.random(),
            suspicious=rng.random(),
            forgetful=rng.random(),
            obsessive=rng.random()
        )

    @classmethod
    def from_archetype(cls, archetype: str) -> 'NPCBias':
        """Generate bias from character archetype."""
        archetypes = {
            "bartender": cls(
                fearful=0.3, paranoid=0.4, loyal=0.4, talkative=0.8,
                greedy=0.5, self_preserving=0.7, curious=0.6, dramatic=0.4,
                cynical=0.6, trusting=0.4, suspicious=0.5, forgetful=0.2,
                obsessive=0.2
            ),
            "informant": cls(
                fearful=0.6, paranoid=0.7, loyal=0.2, talkative=0.9,
                greedy=0.8, self_preserving=0.9, curious=0.7, dramatic=0.5,
                cynical=0.8, trusting=0.2, suspicious=0.8, forgetful=0.1,
                obsessive=0.3
            ),
            "cop": cls(
                fearful=0.3, paranoid=0.5, loyal=0.6, talkative=0.4,
                greedy=0.3, self_preserving=0.5, curious=0.6, dramatic=0.2,
                cynical=0.6, trusting=0.3, suspicious=0.7, forgetful=0.2,
                obsessive=0.4
            ),
            "mobster": cls(
                fearful=0.4, paranoid=0.8, loyal=0.9, talkative=0.2,
                greedy=0.7, self_preserving=0.8, curious=0.4, dramatic=0.3,
                cynical=0.9, trusting=0.1, suspicious=0.9, forgetful=0.2,
                obsessive=0.3
            ),
            "civilian": cls(
                fearful=0.5, paranoid=0.3, loyal=0.5, talkative=0.5,
                greedy=0.4, self_preserving=0.6, curious=0.4, dramatic=0.4,
                cynical=0.4, trusting=0.5, suspicious=0.4, forgetful=0.4,
                obsessive=0.2
            ),
            "journalist": cls(
                fearful=0.4, paranoid=0.5, loyal=0.3, talkative=0.6,
                greedy=0.5, self_preserving=0.5, curious=0.9, dramatic=0.6,
                cynical=0.7, trusting=0.3, suspicious=0.7, forgetful=0.1,
                obsessive=0.7
            ),
            "drunk": cls(
                fearful=0.6, paranoid=0.4, loyal=0.3, talkative=0.9,
                greedy=0.5, self_preserving=0.4, curious=0.3, dramatic=0.8,
                cynical=0.5, trusting=0.6, suspicious=0.3, forgetful=0.7,
                obsessive=0.2
            ),
        }
        return archetypes.get(archetype.lower(), cls())


class BiasProcessor:
    """
    Applies NPC bias to information processing.

    This is where events become memories, and memories become
    different depending on who's remembering.
    """

    # Event interpretations by bias
    INTERPRETATIONS = {
        "injury": {
            "fearful": "Someone nearly died there",
            "curious": "There was an accident",
            "cynical": "Someone got what was coming to them",
            "default": "Someone got hurt"
        },
        "violence": {
            "paranoid": "The mob is killing people",
            "loyal_ally": "Someone was defending themselves",
            "cynical": "More violence in this rotten city",
            "default": "There was a shooting"
        },
        "theft": {
            "greedy": "Someone got robbed of something valuable",
            "cynical": "Another day, another theft",
            "paranoid": "Criminals are targeting people",
            "default": "Something was stolen"
        },
        "conversation": {
            "paranoid": "They were plotting something",
            "curious": "They were discussing something interesting",
            "suspicious": "They were being secretive",
            "default": "They were talking"
        },
        "movement": {
            "paranoid": "Someone suspicious was lurking around",
            "curious": "Someone was going somewhere in a hurry",
            "fearful": "Someone was running away from something",
            "default": "Someone passed by"
        }
    }

    # Tags added by bias
    BIAS_TAGS = {
        "fearful": ["danger", "threat", "warning"],
        "paranoid": ["conspiracy", "suspicious", "plot"],
        "greedy": ["money", "profit", "valuable"],
        "cynical": ["crime", "corruption", "typical"],
        "curious": ["interesting", "unusual", "investigate"]
    }

    def interpret_event(
        self,
        event: WorldEvent,
        bias: NPCBias,
        witness_type: WitnessType
    ) -> str:
        """
        Interpret an event through the lens of NPC bias.

        Returns a subjective summary.
        """
        event_type = event.event_type
        interpretations = self.INTERPRETATIONS.get(event_type, {})

        # Check bias-specific interpretations
        if bias.fearful > 0.7 and "fearful" in interpretations:
            return interpretations["fearful"]

        if bias.paranoid > 0.7 and "paranoid" in interpretations:
            return interpretations["paranoid"]

        if bias.cynical > 0.7 and "cynical" in interpretations:
            return interpretations["cynical"]

        if bias.curious > 0.7 and "curious" in interpretations:
            return interpretations["curious"]

        if bias.greedy > 0.7 and "greedy" in interpretations:
            return interpretations["greedy"]

        # Check ally protection
        if bias.loyal > 0.6:
            for actor in event.actors:
                if actor in bias.allies:
                    if "loyal_ally" in interpretations:
                        return interpretations["loyal_ally"]

        # Default interpretation
        return interpretations.get("default", f"Something happened at {event.location_name}")

    def extract_tags(
        self,
        event: WorldEvent,
        bias: NPCBias
    ) -> list[str]:
        """Extract tags from event, influenced by bias."""
        tags = []

        # Base tags from event type
        event_tags = {
            "injury": ["danger", "injury"],
            "violence": ["violence", "danger", "death"],
            "theft": ["crime", "theft"],
            "conversation": ["social"],
            "movement": ["movement"],
            "discovery": ["discovery"]
        }
        tags.extend(event_tags.get(event.event_type, []))

        # Add bias-influenced tags
        if bias.fearful > 0.6:
            tags.extend(["danger", "warning"])
        if bias.paranoid > 0.6:
            tags.append("suspicious")
        if bias.greedy > 0.6 and event.event_type in ["theft", "violence"]:
            tags.append("money")
        if bias.cynical > 0.6:
            tags.append("typical")

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags

    def calculate_emotional_weight(
        self,
        event: WorldEvent,
        bias: NPCBias,
        witness_type: WitnessType
    ) -> float:
        """Calculate how emotionally impactful this memory is."""
        base_weight = event.notability

        # Direct witnesses remember more emotionally
        if witness_type == WitnessType.DIRECT:
            base_weight *= 1.5
        elif witness_type == WitnessType.INDIRECT:
            base_weight *= 1.2

        # Fearful NPCs find scary events more impactful
        if event.event_type in ["violence", "injury"]:
            base_weight += bias.fearful * 0.3

        # Dramatic NPCs make everything more impactful
        base_weight += bias.dramatic * 0.2

        # Obsessive NPCs have higher emotional weight
        base_weight += bias.obsessive * 0.1

        return min(1.0, base_weight)

    def calculate_fear(
        self,
        event: WorldEvent,
        bias: NPCBias
    ) -> float:
        """Calculate fear associated with memory."""
        fear = 0.0

        # Violence and injury cause fear
        if event.event_type == "violence":
            fear = 0.5 + (bias.fearful * 0.3)
        elif event.event_type == "injury":
            fear = 0.3 + (bias.fearful * 0.2)

        # Paranoid NPCs fear conspiracies
        if bias.paranoid > 0.6:
            fear += 0.1

        return min(1.0, fear)

    def calculate_anger(
        self,
        event: WorldEvent,
        bias: NPCBias
    ) -> float:
        """Calculate anger associated with memory."""
        anger = 0.0

        # Violence against allies causes anger
        if event.event_type == "violence":
            for actor in event.actors:
                if actor in bias.allies:
                    anger += 0.3

        # Theft causes anger if cynical
        if event.event_type == "theft" and bias.cynical > 0.5:
            anger += 0.2

        return min(1.0, anger)

    def form_memory_from_event(
        self,
        event: WorldEvent,
        bias: NPCBias,
        witness_type: WitnessType,
        npc_id: str
    ) -> NPCMemory:
        """
        Form a memory from witnessing an event.

        This is where objective truth becomes subjective memory.
        """
        # Get witness info
        witness = event.get_witness(npc_id)
        clarity = witness.clarity if witness else 1.0

        # Direct witnesses have higher base confidence
        if witness_type == WitnessType.DIRECT:
            base_confidence = 0.9 * clarity
            source = MemorySource.SELF
        elif witness_type == WitnessType.INDIRECT:
            base_confidence = 0.5 * clarity
            source = MemorySource.SELF
        else:
            base_confidence = 0.3 * clarity
            source = MemorySource.SELF

        # Apply interpretation
        summary = self.interpret_event(event, bias, witness_type)
        tags = self.extract_tags(event, bias)
        emotional_weight = self.calculate_emotional_weight(event, bias, witness_type)
        fear = self.calculate_fear(event, bias)
        anger = self.calculate_anger(event, bias)

        # Create memory
        memory = NPCMemory(
            event_id=event.id,
            summary=summary,
            tags=tags,
            confidence=base_confidence,
            emotional_weight=emotional_weight,
            fear=fear,
            anger=anger,
            source=source,
            timestamp=event.timestamp,
            location=event.location_name,
            location_coords=event.location,
            last_recalled=event.timestamp,
            decay_rate=0.01 * bias.get_memory_decay_modifier(),
            is_traumatic=fear > 0.7,
            actors=event.actors.copy()
        )

        # Paranoid NPCs add conspiracy tags
        if bias.paranoid > 0.6 and random.random() < bias.paranoid:
            memory.add_tag("conspiracy")
            memory.summary = self._add_conspiracy_angle(memory.summary)

        return memory

    def apply_bias_to_retelling(
        self,
        memory: NPCMemory,
        bias: NPCBias
    ) -> NPCMemory:
        """
        Apply bias when an NPC retells a memory.

        Returns a modified copy — the original memory is not mutated.
        """
        memory = copy.deepcopy(memory)

        # Dramatic NPCs exaggerate
        if bias.dramatic > 0.6:
            memory.summary = self._dramatize(memory.summary)
            memory.emotional_weight = min(1.0, memory.emotional_weight + 0.1)

        # Greedy NPCs add profit angles
        if bias.greedy > 0.6 and random.random() < 0.4:
            memory.add_tag("money")

        # Self-preserving NPCs might omit certain details
        if bias.self_preserving > 0.7:
            # Could filter out self-incriminating details here
            pass

        # Loyal NPCs protect allies
        if bias.loyal > 0.6:
            for ally in bias.allies:
                if ally in memory.actors:
                    memory.summary = self._soften_ally_involvement(
                        memory.summary, ally
                    )

        return memory

    def _add_conspiracy_angle(self, summary: str) -> str:
        """Add conspiracy undertones to summary."""
        prefixes = [
            "They say ",
            "Word is ",
            "People are talking... ",
            "Something's not right - ",
        ]
        return random.choice(prefixes) + summary.lower()

    def _dramatize(self, summary: str) -> str:
        """Make summary more dramatic."""
        replacements = {
            "someone got hurt": "someone nearly died",
            "there was an accident": "there was a terrible accident",
            "something was stolen": "a valuable was taken",
            "they were talking": "they were having a heated discussion"
        }
        lower_summary = summary.lower()
        for old, new in replacements.items():
            if old in lower_summary:
                return summary.replace(old, new).replace(old.capitalize(), new.capitalize())
        return summary + " - it was quite something"

    def _soften_ally_involvement(self, summary: str, ally: str) -> str:
        """Soften how an ally is portrayed."""
        # Simple implementation - could be more sophisticated
        return summary.replace(
            f"{ally} attacked",
            f"{ally} defended themselves"
        ).replace(
            f"{ally} killed",
            f"{ally} was forced to act"
        )
