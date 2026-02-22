"""
Memory Bank - The unified memory system.

Coordinates all three memory layers and provides save/load functionality.
"""

from typing import Optional
import json
import os

from .world_memory import WorldMemory, Event, EventType
from .character_memory import CharacterMemory, BeliefConfidence
from .player_memory import PlayerMemory


class MemoryBank:
    """
    The central memory system coordinating all memory layers.

    Provides high-level operations that update multiple memory layers
    appropriately, and handles persistence.
    """

    def __init__(self):
        self.world = WorldMemory()
        self.characters: dict[str, CharacterMemory] = {}
        self.player = PlayerMemory()
        self.game_seed: Optional[int] = None

    def register_character(self, character_id: str) -> CharacterMemory:
        """Register a new character and create their memory."""
        memory = CharacterMemory(character_id)
        self.characters[character_id] = memory
        return memory

    def get_character_memory(self, character_id: str) -> Optional[CharacterMemory]:
        """Get a character's memory."""
        return self.characters.get(character_id)

    def record_witnessed_event(
        self,
        event_type: EventType,
        description: str,
        location: str,
        actors: list[str] = None,
        witnesses: list[str] = None,
        player_witnessed: bool = False,
        details: dict = None
    ) -> Event:
        """
        Record an event and update all relevant memory layers.

        This is the primary method for recording things that happen.
        It updates:
        - World memory (always)
        - Character memory (for each witness)
        - Player memory (if player witnessed)
        """
        actors = actors or []
        witnesses = witnesses or []
        details = details or {}

        # Record in world memory (objective truth)
        event = self.world.record(
            event_type=event_type,
            description=description,
            location=location,
            actors=actors,
            witnesses=witnesses,
            details=details
        )

        # Update character memories for witnesses and actors
        involved = set(witnesses) | set(actors)
        for char_id in involved:
            if char_id in self.characters:
                char_memory = self.characters[char_id]
                source = "acted" if char_id in actors else "witnessed"
                char_memory.add_belief(
                    subject=event.id,
                    content=description,
                    confidence=BeliefConfidence.CERTAIN,
                    source=source,
                    timestamp=event.timestamp,
                    is_true=True
                )

        # Update player memory if they witnessed
        if player_witnessed:
            # Create a discovery from the event
            self.player.add_discovery(
                fact_id=f"witnessed_{event.id}",
                description=description,
                location=location,
                timestamp=event.timestamp,
                source="witnessed",
                related_to=actors
            )

        return event

    def character_tells_player(
        self,
        character_id: str,
        information: str,
        is_true: bool,
        topic: str = None
    ) -> None:
        """
        Record a character telling the player something.

        The information may be true or false (a lie).
        """
        timestamp = self.world.current_time

        # Record the dialogue event
        self.world.record(
            event_type=EventType.DIALOGUE,
            description=f"{character_id} told player: {information}",
            location="conversation",
            actors=[character_id, "player"],
            witnesses=[character_id, "player"],
            details={"topic": topic, "is_true": is_true}
        )

        # Player forms a belief (they don't know if it's true)
        self.player.add_discovery(
            fact_id=f"told_{character_id}_{timestamp}",
            description=information,
            location="conversation",
            timestamp=timestamp,
            source=f"told by {character_id}",
            related_to=[character_id]
        )

        # Record interaction in character's memory
        if character_id in self.characters:
            self.characters[character_id].record_player_interaction(
                timestamp=timestamp,
                interaction_type="told",
                topic=topic,
                player_tone="neutral",
                outcome="shared_info",
                trust_change=0
            )

    def player_discovers(
        self,
        fact_id: str,
        description: str,
        location: str,
        source: str,
        is_evidence: bool = False,
        related_to: list[str] = None
    ) -> None:
        """Record the player discovering something."""
        timestamp = self.world.current_time

        # Record in world memory
        self.world.record(
            event_type=EventType.DISCOVERY,
            description=f"Player discovered: {description}",
            location=location,
            actors=["player"],
            witnesses=["player"],
            details={"fact_id": fact_id, "is_evidence": is_evidence}
        )

        # Add to player memory
        self.player.add_discovery(
            fact_id=fact_id,
            description=description,
            location=location,
            timestamp=timestamp,
            source=source,
            is_evidence=is_evidence,
            related_to=related_to or []
        )

    def advance_time(self, units: int = 1) -> None:
        """Advance game time across all systems."""
        self.world.advance_time(units)

    @property
    def current_time(self) -> int:
        """Get current game time."""
        return self.world.current_time

    def save(self, filepath: str) -> None:
        """Save the entire memory bank to a JSON file."""
        data = {
            "game_seed": self.game_seed,
            "world": self.world.to_dict(),
            "characters": {
                cid: mem.to_dict()
                for cid, mem in self.characters.items()
            },
            "player": self.player.to_dict()
        }

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    _REQUIRED_SAVE_KEYS = {"world", "player"}

    @classmethod
    def load(cls, filepath: str) -> 'MemoryBank':
        """Load memory bank from a JSON file with validation."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid save file: expected dict, got {type(data).__name__}")

        # Verify required sections exist so we don't silently load empty state
        missing = cls._REQUIRED_SAVE_KEYS - data.keys()
        if missing:
            raise ValueError(f"Save file missing required sections: {', '.join(sorted(missing))}")

        bank = cls()

        # Validate game_seed type
        seed = data.get("game_seed")
        if seed is not None and not isinstance(seed, (int, float)):
            seed = None
        bank.game_seed = seed

        # Validate nested structures are dicts before deserializing
        world_data = data.get("world", {})
        if not isinstance(world_data, dict):
            world_data = {}
        bank.world = WorldMemory.from_dict(world_data)

        characters_data = data.get("characters", {})
        if not isinstance(characters_data, dict):
            characters_data = {}
        bank.characters = {
            str(cid): CharacterMemory.from_dict(mem_data)
            for cid, mem_data in characters_data.items()
            if isinstance(mem_data, dict)
        }

        player_data = data.get("player", {})
        if not isinstance(player_data, dict):
            player_data = {}
        bank.player = PlayerMemory.from_dict(player_data)

        return bank

    def get_summary(self) -> dict:
        """Get a summary of the memory bank state."""
        return {
            "current_time": self.current_time,
            "total_events": len(self.world.events),
            "characters_tracked": len(self.characters),
            "player_discoveries": len(self.player.discoveries),
            "player_dominant_shade": self.player.get_dominant_shade().value,
            "locations_visited": len(self.player.visited_locations)
        }
