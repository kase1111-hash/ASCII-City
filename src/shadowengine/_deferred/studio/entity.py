"""
Dynamic entity system for interactive ASCII art with behavior.
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import uuid

from .art import ASCIIArt, ArtCategory
from .tags import ArtTags, ObjectType, InteractionType
from .personality import PersonalityTemplate, IdleBehavior, ThreatResponse, Attitude
from .animation import Animation, AnimationPlayer, AnimationFrame


class EntityState(Enum):
    """Current state of an entity."""
    IDLE = auto()
    MOVING = auto()
    INTERACTING = auto()
    ATTACKING = auto()
    FLEEING = auto()
    HIDING = auto()
    SLEEPING = auto()
    DEAD = auto()
    CUSTOM = auto()


@dataclass
class EntityStats:
    """Combat and interaction stats for entities."""
    health: float = 100.0
    max_health: float = 100.0
    energy: float = 100.0
    max_energy: float = 100.0
    speed: float = 1.0
    attack_power: float = 10.0
    defense: float = 5.0
    perception: float = 5.0  # Detection range

    def is_alive(self) -> bool:
        """Check if entity is alive."""
        return self.health > 0

    def take_damage(self, amount: float) -> float:
        """Apply damage and return actual damage taken."""
        effective_damage = max(0, amount - self.defense * 0.5)
        self.health = max(0, self.health - effective_damage)
        return effective_damage

    def heal(self, amount: float) -> float:
        """Heal and return actual healing done."""
        old_health = self.health
        self.health = min(self.max_health, self.health + amount)
        return self.health - old_health

    def use_energy(self, amount: float) -> bool:
        """Use energy if available."""
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False

    def restore_energy(self, amount: float) -> float:
        """Restore energy and return actual amount restored."""
        old_energy = self.energy
        self.energy = min(self.max_energy, self.energy + amount)
        return self.energy - old_energy

    def to_dict(self) -> dict:
        """Serialize stats to dictionary."""
        return {
            "health": self.health,
            "max_health": self.max_health,
            "energy": self.energy,
            "max_energy": self.max_energy,
            "speed": self.speed,
            "attack_power": self.attack_power,
            "defense": self.defense,
            "perception": self.perception
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EntityStats":
        """Create stats from dictionary."""
        return cls(**data)


@dataclass
class EntityMemory:
    """Memory system for entities to remember events and entities."""
    memories: List[Dict[str, Any]] = field(default_factory=list)
    grudges: Dict[str, float] = field(default_factory=dict)  # entity_id -> grudge_level
    friends: Dict[str, float] = field(default_factory=dict)  # entity_id -> friendship_level
    max_memories: int = 100

    def add_memory(
        self,
        event_type: str,
        details: Dict[str, Any],
        timestamp: float
    ) -> None:
        """Add a memory of an event."""
        memory = {
            "type": event_type,
            "details": details,
            "timestamp": timestamp
        }
        self.memories.append(memory)

        # Trim old memories
        if len(self.memories) > self.max_memories:
            self.memories = self.memories[-self.max_memories:]

    def add_grudge(self, entity_id: str, amount: float) -> None:
        """Add or increase grudge against entity."""
        current = self.grudges.get(entity_id, 0.0)
        self.grudges[entity_id] = min(1.0, current + amount)

    def reduce_grudge(self, entity_id: str, amount: float) -> None:
        """Reduce grudge against entity."""
        if entity_id in self.grudges:
            self.grudges[entity_id] = max(0.0, self.grudges[entity_id] - amount)
            if self.grudges[entity_id] <= 0:
                del self.grudges[entity_id]

    def add_friendship(self, entity_id: str, amount: float) -> None:
        """Add or increase friendship with entity."""
        current = self.friends.get(entity_id, 0.0)
        self.friends[entity_id] = min(1.0, current + amount)

    def get_attitude_toward(self, entity_id: str) -> float:
        """Get combined attitude toward entity (-1 to 1)."""
        grudge = self.grudges.get(entity_id, 0.0)
        friendship = self.friends.get(entity_id, 0.0)
        return friendship - grudge

    def has_memory_of(self, event_type: str, since: float) -> bool:
        """Check if entity remembers event type since timestamp."""
        for memory in self.memories:
            if memory["type"] == event_type and memory["timestamp"] >= since:
                return True
        return False

    def clear_old_memories(self, before: float) -> int:
        """Clear memories older than timestamp."""
        original_count = len(self.memories)
        self.memories = [m for m in self.memories if m["timestamp"] >= before]
        return original_count - len(self.memories)

    def to_dict(self) -> dict:
        """Serialize memory to dictionary."""
        return {
            "memories": self.memories,
            "grudges": self.grudges,
            "friends": self.friends,
            "max_memories": self.max_memories
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EntityMemory":
        """Create memory from dictionary."""
        return cls(
            memories=data.get("memories", []),
            grudges=data.get("grudges", {}),
            friends=data.get("friends", {}),
            max_memories=data.get("max_memories", 100)
        )


@dataclass
class DynamicEntity(ASCIIArt):
    """
    Interactive entity with behavior and state.

    Dynamic entities have AI behavior, can move, interact with
    the world and player, and maintain state over time.

    Attributes:
        personality: Behavioral template
        state: Current entity state
        stats: Combat and interaction stats
        memory: Memory of events and entities
        animations: Dict of named animations
        dialogue_pool: Available dialogue lines
        loot_table: Items dropped on death
        spawn_conditions: When entity can spawn
        home_position: Position entity returns to
        wander_radius: How far entity wanders from home
    """
    personality: PersonalityTemplate = field(default_factory=lambda: PersonalityTemplate(name="Default"))
    state: EntityState = EntityState.IDLE
    stats: EntityStats = field(default_factory=EntityStats)
    memory: EntityMemory = field(default_factory=EntityMemory)
    animations: Dict[str, Animation] = field(default_factory=dict)
    dialogue_pool: List[str] = field(default_factory=list)
    loot_table: Dict[str, float] = field(default_factory=dict)  # item_id -> drop_chance
    spawn_conditions: Dict[str, Any] = field(default_factory=dict)
    home_position: Optional[Tuple[int, int]] = None
    wander_radius: float = 10.0

    # Runtime state (not serialized)
    _animation_player: AnimationPlayer = field(default_factory=AnimationPlayer, repr=False)
    _current_target: Optional[Tuple[int, int]] = field(default=None, repr=False)
    _state_time: float = field(default=0.0, repr=False)

    def __post_init__(self):
        """Initialize entity."""
        super().__post_init__()
        self.category = ArtCategory.DYNAMIC

        # Add animations to player
        for animation in self.animations.values():
            self._animation_player.add_animation(animation)

    def update(self, delta_time: float, world_context: Dict[str, Any] = None) -> None:
        """
        Update entity state.

        Args:
            delta_time: Time since last update (seconds)
            world_context: Optional world state information
        """
        self._state_time += delta_time

        # Restore energy over time
        if self.state == EntityState.SLEEPING:
            self.stats.restore_energy(delta_time * 10)
        else:
            self.stats.restore_energy(delta_time * 1)

        # Update animation based on state
        self._animation_player.update_for_state(self.state.name.lower())

    def set_state(self, new_state: EntityState) -> None:
        """Change entity state."""
        if self.state != new_state:
            self.state = new_state
            self._state_time = 0.0
            self._animation_player.update_for_state(new_state.name.lower())

    def get_current_frame(self) -> Optional[AnimationFrame]:
        """Get current animation frame."""
        return self._animation_player.get_current_frame()

    def add_animation(self, animation: Animation) -> None:
        """Add animation to entity."""
        self.animations[animation.name] = animation
        self._animation_player.add_animation(animation)

    def play_animation(self, name: str) -> bool:
        """Play a specific animation."""
        return self._animation_player.play(name)

    def respond_to_threat(self, threat_level: float, threat_source: Optional[str] = None) -> ThreatResponse:
        """
        Determine response to a threat.

        Args:
            threat_level: How dangerous the threat is (0.0 to 1.0)
            threat_source: Optional entity ID of threat source

        Returns:
            ThreatResponse indicating how entity will respond
        """
        # Check if we have a grudge against the threat source
        attitude_modifier = 0.0
        if threat_source and threat_source in self.memory.grudges:
            attitude_modifier = self.memory.grudges[threat_source] * 0.2

        effective_threat = min(1.0, threat_level + attitude_modifier)
        response = self.personality.calculate_response(effective_threat)

        # Update state based on response
        state_map = {
            ThreatResponse.FLEE: EntityState.FLEEING,
            ThreatResponse.HIDE: EntityState.HIDING,
            ThreatResponse.ATTACK: EntityState.ATTACKING,
            ThreatResponse.CHALLENGE: EntityState.INTERACTING,
            ThreatResponse.PROTECT: EntityState.ATTACKING,
        }
        if response in state_map:
            self.set_state(state_map[response])

        return response

    def decide_idle_action(self, has_target: bool = False) -> IdleBehavior:
        """Decide what to do when idle."""
        return self.personality.calculate_idle_action(has_target)

    def get_dialogue(self, context: str = "default") -> Optional[str]:
        """Get a dialogue line for context."""
        # Filter dialogue by context if available
        contextual = [d for d in self.dialogue_pool if context in d.lower()]
        if contextual:
            import random
            return random.choice(contextual)
        elif self.dialogue_pool:
            import random
            return random.choice(self.dialogue_pool)
        return None

    def add_dialogue(self, line: str) -> None:
        """Add dialogue line to pool."""
        if line not in self.dialogue_pool:
            self.dialogue_pool.append(line)

    def take_damage(self, amount: float, source: Optional[str] = None) -> float:
        """
        Take damage from a source.

        Args:
            amount: Damage amount
            source: Optional entity ID of damage source

        Returns:
            Actual damage taken
        """
        damage_taken = self.stats.take_damage(amount)

        # Remember being attacked
        if source:
            import time
            self.memory.add_memory(
                "attacked",
                {"source": source, "damage": damage_taken},
                time.time()
            )
            self.memory.add_grudge(source, self.personality.grudge_factor * 0.2)

        # Check for death
        if not self.stats.is_alive():
            self.set_state(EntityState.DEAD)

        return damage_taken

    def attack(self, target: "DynamicEntity") -> float:
        """
        Attack another entity.

        Args:
            target: Entity to attack

        Returns:
            Damage dealt
        """
        if not self.stats.use_energy(10):
            return 0.0

        damage = self.stats.attack_power
        return target.take_damage(damage, self.id)

    def interact_with(self, interactor_id: str) -> Dict[str, Any]:
        """
        Handle interaction from another entity.

        Args:
            interactor_id: ID of entity interacting

        Returns:
            Interaction result
        """
        attitude = self.memory.get_attitude_toward(interactor_id)
        base_attitude = self.personality.player_attitude

        result = {
            "attitude": attitude,
            "base_attitude": base_attitude.name,
            "dialogue": self.get_dialogue(),
            "available_actions": []
        }

        # Determine available actions based on attitude
        if attitude > 0.5 or base_attitude == Attitude.FRIENDLY:
            result["available_actions"].extend(["trade", "help", "follow"])
        elif attitude > 0 or base_attitude == Attitude.NEUTRAL:
            result["available_actions"].extend(["trade", "info"])
        elif attitude > -0.5 or base_attitude in (Attitude.SUSPICIOUS, Attitude.CURIOUS):
            result["available_actions"].extend(["info", "bribe"])
        else:
            result["available_actions"].extend(["fight", "flee"])

        return result

    def get_loot(self) -> List[str]:
        """Get loot drops based on loot table."""
        import random
        drops = []
        for item_id, chance in self.loot_table.items():
            if random.random() < chance:
                drops.append(item_id)
        return drops

    def can_spawn_in(self, environment: str, time_of_day: str = "day") -> bool:
        """Check if entity can spawn in conditions."""
        if not self.spawn_conditions:
            return True

        if "environments" in self.spawn_conditions:
            if environment not in self.spawn_conditions["environments"]:
                return False

        if "time_of_day" in self.spawn_conditions:
            if time_of_day not in self.spawn_conditions["time_of_day"]:
                return False

        return True

    def to_dict(self) -> dict:
        """Serialize entity to dictionary."""
        data = super().to_dict()
        data.update({
            "personality": self.personality.to_dict(),
            "state": self.state.name,
            "stats": self.stats.to_dict(),
            "memory": self.memory.to_dict(),
            "animations": {name: anim.to_dict() for name, anim in self.animations.items()},
            "dialogue_pool": self.dialogue_pool,
            "loot_table": self.loot_table,
            "spawn_conditions": self.spawn_conditions,
            "home_position": self.home_position,
            "wander_radius": self.wander_radius
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "DynamicEntity":
        """Create entity from dictionary."""
        from .animation import Animation

        animations = {}
        for name, anim_data in data.get("animations", {}).items():
            animations[name] = Animation.from_dict(anim_data)

        return cls(
            id=data["id"],
            name=data["name"],
            tiles=data["tiles"],
            tags=ArtTags.from_dict(data["tags"]),
            player_id=data.get("player_id", "system"),
            version=data.get("version", 1),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            color_hints=data.get("color_hints"),
            description=data.get("description"),
            original_creator=data.get("original_creator"),
            imported_from=data.get("imported_from"),
            personality=PersonalityTemplate.from_dict(data["personality"]) if "personality" in data else PersonalityTemplate(name="Default"),
            state=EntityState[data.get("state", "IDLE")],
            stats=EntityStats.from_dict(data["stats"]) if "stats" in data else EntityStats(),
            memory=EntityMemory.from_dict(data["memory"]) if "memory" in data else EntityMemory(),
            animations=animations,
            dialogue_pool=data.get("dialogue_pool", []),
            loot_table=data.get("loot_table", {}),
            spawn_conditions=data.get("spawn_conditions", {}),
            home_position=tuple(data["home_position"]) if data.get("home_position") else None,
            wander_radius=data.get("wander_radius", 10.0)
        )

    @classmethod
    def from_string(
        cls,
        name: str,
        art_string: str,
        tags: ArtTags,
        personality: PersonalityTemplate = None,
        **kwargs
    ) -> "DynamicEntity":
        """Create entity from multi-line string."""
        tiles = [list(line) for line in art_string.split("\n")]
        if personality is None:
            personality = PersonalityTemplate(name=f"{name} personality")
        return cls(name=name, tiles=tiles, tags=tags, personality=personality, **kwargs)

    def copy(self) -> "DynamicEntity":
        """Create a deep copy of the entity."""
        return DynamicEntity(
            id=str(uuid.uuid4()),
            name=f"{self.name} (copy)",
            tiles=[row.copy() for row in self.tiles],
            tags=ArtTags.from_dict(self.tags.to_dict()),
            player_id=self.player_id,
            version=1,
            color_hints=self.color_hints.copy() if self.color_hints else None,
            description=self.description,
            original_creator=self.original_creator or self.player_id,
            imported_from=self.id,
            personality=self.personality.copy(),
            state=EntityState.IDLE,
            stats=EntityStats(**self.stats.to_dict()),
            memory=EntityMemory(),  # Fresh memory for copy
            animations={name: Animation.from_dict(anim.to_dict()) for name, anim in self.animations.items()},
            dialogue_pool=self.dialogue_pool.copy(),
            loot_table=self.loot_table.copy(),
            spawn_conditions=self.spawn_conditions.copy(),
            home_position=self.home_position,
            wander_radius=self.wander_radius
        )


# Predefined entity templates
ENTITY_TEMPLATES: Dict[str, dict] = {
    "forest_deer": {
        "name": "Forest Deer",
        "art": """ /\\
(oo)
 ||""",
        "object_type": ObjectType.CREATURE,
        "personality": "timid_prey",
        "stats": {"health": 50, "max_health": 50, "speed": 1.5},
        "spawn_conditions": {"environments": ["forest", "plains"]},
    },
    "cave_bat": {
        "name": "Cave Bat",
        "art": """\\v/
 W""",
        "object_type": ObjectType.CREATURE,
        "personality": "curious_neutral",
        "stats": {"health": 20, "max_health": 20, "speed": 2.0},
        "spawn_conditions": {"environments": ["cave", "dungeon"], "time_of_day": ["night"]},
    },
    "village_guard": {
        "name": "Village Guard",
        "art": """ O
/|\\
/ \\""",
        "object_type": ObjectType.NPC,
        "personality": "loyal_guardian",
        "stats": {"health": 100, "max_health": 100, "attack_power": 15, "defense": 10},
        "dialogue_pool": ["Halt! State your business.", "The village is safe under my watch."],
        "spawn_conditions": {"environments": ["village", "castle"]},
    },
    "merchant": {
        "name": "Traveling Merchant",
        "art": """ @
[+]
 A""",
        "object_type": ObjectType.NPC,
        "personality": "paranoid_merchant",
        "stats": {"health": 60, "max_health": 60},
        "dialogue_pool": ["Looking to buy? Or sell?", "Best prices in the land!", "I don't trust easily..."],
        "spawn_conditions": {"environments": ["village", "road"]},
    },
}


def create_entity_from_template(
    template_name: str,
    player_id: str = "system"
) -> Optional[DynamicEntity]:
    """Create entity from a predefined template."""
    from .personality import PERSONALITY_TEMPLATES

    if template_name not in ENTITY_TEMPLATES:
        return None

    template = ENTITY_TEMPLATES[template_name]

    # Get personality
    personality_name = template.get("personality", "curious_neutral")
    personality = PERSONALITY_TEMPLATES.get(personality_name)
    if personality:
        personality = personality.copy()
    else:
        personality = PersonalityTemplate(name=f"{template['name']} personality")

    tags = ArtTags(
        object_type=template["object_type"],
        interaction_types={InteractionType.TALKABLE} if template["object_type"] == ObjectType.NPC else set()
    )

    # Create stats
    stats_data = template.get("stats", {})
    stats = EntityStats(**stats_data)

    entity = DynamicEntity.from_string(
        name=template["name"],
        art_string=template["art"],
        tags=tags,
        personality=personality,
        player_id=player_id,
        stats=stats,
        dialogue_pool=template.get("dialogue_pool", []),
        spawn_conditions=template.get("spawn_conditions", {})
    )

    return entity
