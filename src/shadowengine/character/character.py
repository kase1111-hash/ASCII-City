"""
Character - NPC model with psychology, secrets, and state.
"""

from dataclasses import dataclass
from enum import Enum


class Archetype(Enum):
    """Character archetypes that define base behavior patterns."""
    PROTECTOR = "protector"     # Loyal but secretive about those they protect
    OPPORTUNIST = "opportunist" # Helpful when beneficial, betrays when advantageous
    TRUE_BELIEVER = "true_believer"  # Ideologically driven, hard to crack
    SURVIVOR = "survivor"       # Self-preservation first, cracks easily
    AUTHORITY = "authority"     # Controls information, resents challenges
    OUTSIDER = "outsider"       # Knows things but isn't trusted by others
    INNOCENT = "innocent"       # Genuinely uninvolved, may have seen something
    GUILTY = "guilty"           # Has something to hide, defensive


class Mood(Enum):
    """Character's current emotional state."""
    CALM = "calm"
    NERVOUS = "nervous"
    ANGRY = "angry"
    SCARED = "scared"
    SUSPICIOUS = "suspicious"
    FRIENDLY = "friendly"
    HOSTILE = "hostile"
    DEFENSIVE = "defensive"


@dataclass
class Motivations:
    """Character motivation vectors (0-100 scale)."""
    fear: int = 50              # How much fear drives them
    greed: int = 50             # How much self-interest drives them
    loyalty: int = 50           # How loyal they are to others
    pride: int = 50             # How much pride/ego they have
    guilt: int = 0              # Guilt they carry (if guilty)

    def to_dict(self) -> dict:
        return {
            "fear": self.fear,
            "greed": self.greed,
            "loyalty": self.loyalty,
            "pride": self.pride,
            "guilt": self.guilt
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Motivations':
        return cls(**data)

    @classmethod
    def from_archetype(cls, archetype: Archetype) -> 'Motivations':
        """Generate motivations based on archetype."""
        presets = {
            Archetype.PROTECTOR: cls(fear=30, greed=20, loyalty=90, pride=60, guilt=0),
            Archetype.OPPORTUNIST: cls(fear=40, greed=80, loyalty=20, pride=50, guilt=10),
            Archetype.TRUE_BELIEVER: cls(fear=20, greed=10, loyalty=70, pride=80, guilt=0),
            Archetype.SURVIVOR: cls(fear=80, greed=60, loyalty=30, pride=30, guilt=20),
            Archetype.AUTHORITY: cls(fear=30, greed=50, loyalty=40, pride=90, guilt=0),
            Archetype.OUTSIDER: cls(fear=60, greed=40, loyalty=50, pride=40, guilt=0),
            Archetype.INNOCENT: cls(fear=50, greed=30, loyalty=60, pride=40, guilt=0),
            Archetype.GUILTY: cls(fear=70, greed=50, loyalty=40, pride=50, guilt=80),
        }
        return presets.get(archetype, cls())


@dataclass
class CharacterState:
    """Current state of a character."""
    location: str = ""
    mood: Mood = Mood.CALM
    is_cracked: bool = False        # Has revealed their secret
    is_alive: bool = True
    is_available: bool = True       # Can be interacted with
    pressure_accumulated: int = 0    # Pressure from interrogation
    times_talked: int = 0           # How many conversations with player

    def to_dict(self) -> dict:
        return {
            "location": self.location,
            "mood": self.mood.value,
            "is_cracked": self.is_cracked,
            "is_alive": self.is_alive,
            "is_available": self.is_available,
            "pressure_accumulated": self.pressure_accumulated,
            "times_talked": self.times_talked
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CharacterState':
        data["mood"] = Mood(data["mood"])
        return cls(**data)


class Character:
    """
    A fully-realized NPC with psychology, secrets, and behavior.
    """

    def __init__(
        self,
        id: str,
        name: str,
        archetype: Archetype,
        description: str = "",
        secret_truth: str = "",
        public_lie: str = "",
        role_in_spine: str = None,
        trust_threshold: int = 50,
        initial_location: str = ""
    ):
        self.id = id
        self.name = name
        self.archetype = archetype
        self.description = description

        # Secrets
        self.secret_truth = secret_truth
        self.public_lie = public_lie
        self.role_in_spine = role_in_spine

        # Psychology
        self.motivations = Motivations.from_archetype(archetype)
        self.trust_threshold = trust_threshold
        self.current_trust = 0  # Trust toward player

        # State
        self.state = CharacterState(location=initial_location)

        # Knowledge - things this character knows
        self.knowledge: set[str] = set()

        # Topics this character can discuss
        self.available_topics: set[str] = set()
        self.exhausted_topics: set[str] = set()

    def apply_pressure(self, amount: int) -> bool:
        """
        Apply interrogation pressure.

        Returns True if character cracks.
        """
        # Modify pressure based on motivations
        fear_modifier = self.motivations.fear / 50  # 0.0 to 2.0
        guilt_modifier = 1 + (self.motivations.guilt / 100)  # 1.0 to 2.0

        effective_pressure = amount * fear_modifier * guilt_modifier
        self.state.pressure_accumulated += int(effective_pressure)

        # Check if cracked
        if self.state.pressure_accumulated >= self.trust_threshold and not self.state.is_cracked:
            self.state.is_cracked = True
            self.state.mood = Mood.SCARED
            return True

        # Update mood based on pressure
        if self.state.pressure_accumulated > self.trust_threshold * 0.7:
            self.state.mood = Mood.DEFENSIVE
        elif self.state.pressure_accumulated > self.trust_threshold * 0.4:
            self.state.mood = Mood.NERVOUS

        return False

    def modify_trust(self, amount: int) -> None:
        """Modify the character's trust toward the player."""
        self.current_trust += amount

        # Trust affects mood
        if self.current_trust > 20:
            self.state.mood = Mood.FRIENDLY
        elif self.current_trust < -20:
            self.state.mood = Mood.HOSTILE

    def add_knowledge(self, fact: str) -> None:
        """Give the character knowledge of a fact."""
        self.knowledge.add(fact)

    def knows(self, fact: str) -> bool:
        """Check if character knows something."""
        return fact in self.knowledge

    def add_topic(self, topic: str) -> None:
        """Add a topic this character can discuss."""
        self.available_topics.add(topic)

    def exhaust_topic(self, topic: str) -> None:
        """Mark a topic as exhausted (discussed fully)."""
        if topic in self.available_topics:
            self.available_topics.remove(topic)
            self.exhausted_topics.add(topic)

    def get_available_topics(self) -> set[str]:
        """Get topics available for discussion."""
        return self.available_topics.copy()

    def get_response_mood_modifier(self) -> str:
        """Get a modifier string based on current mood."""
        modifiers = {
            Mood.CALM: "",
            Mood.NERVOUS: "nervously",
            Mood.ANGRY: "angrily",
            Mood.SCARED: "fearfully",
            Mood.SUSPICIOUS: "suspiciously",
            Mood.FRIENDLY: "warmly",
            Mood.HOSTILE: "coldly",
            Mood.DEFENSIVE: "defensively"
        }
        return modifiers.get(self.state.mood, "")

    def will_cooperate(self) -> bool:
        """
        Determine if character will cooperate based on trust and mood.
        """
        if self.state.mood == Mood.HOSTILE:
            return False
        if self.current_trust > 0:
            return True
        if self.state.mood == Mood.FRIENDLY:
            return True
        # Neutral - 50/50 based on archetype
        return self.archetype in [Archetype.INNOCENT, Archetype.OUTSIDER]

    def record_conversation(self) -> None:
        """Record that a conversation happened."""
        self.state.times_talked += 1

    def move_to(self, location: str) -> None:
        """Move character to a new location."""
        self.state.location = location

    def to_dict(self) -> dict:
        """Serialize character."""
        return {
            "id": self.id,
            "name": self.name,
            "archetype": self.archetype.value,
            "description": self.description,
            "secret_truth": self.secret_truth,
            "public_lie": self.public_lie,
            "role_in_spine": self.role_in_spine,
            "motivations": self.motivations.to_dict(),
            "trust_threshold": self.trust_threshold,
            "current_trust": self.current_trust,
            "state": self.state.to_dict(),
            "knowledge": list(self.knowledge),
            "available_topics": list(self.available_topics),
            "exhausted_topics": list(self.exhausted_topics)
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Character':
        """Deserialize character."""
        char = cls(
            id=data["id"],
            name=data["name"],
            archetype=Archetype(data["archetype"]),
            description=data.get("description", ""),
            secret_truth=data.get("secret_truth", ""),
            public_lie=data.get("public_lie", ""),
            role_in_spine=data.get("role_in_spine"),
            trust_threshold=data.get("trust_threshold", 50),
            initial_location=data.get("state", {}).get("location", "")
        )
        char.motivations = Motivations.from_dict(data.get("motivations", {}))
        char.current_trust = data.get("current_trust", 0)
        char.state = CharacterState.from_dict(data.get("state", {}))
        char.knowledge = set(data.get("knowledge", []))
        char.available_topics = set(data.get("available_topics", []))
        char.exhausted_topics = set(data.get("exhausted_topics", []))
        return char

    def __repr__(self) -> str:
        return f"Character({self.id}, {self.name}, {self.archetype.value})"
