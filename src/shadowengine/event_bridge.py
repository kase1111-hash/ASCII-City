"""
GameEventBridge - Connects MemoryBank events to NPC intelligence.

When the game records a witnessed event (via MemoryBank), this bridge
also feeds it into the PropagationEngine so NPCs form subjective
memories, rumors can spread, and tile atmosphere updates.
"""

from typing import Optional

from .npc_intelligence import PropagationEngine
from .npc_intelligence.world_event import WorldEvent, Witness, WitnessType


# Map MemoryBank EventType values to npc_intelligence event_type strings
_EVENT_TYPE_MAP = {
    "discovery": "discovery",
    "dialogue": "conversation",
    "movement": "movement",
    "action": "action",
    "combat": "violence",
    "death": "death",
    "injury": "injury",
    "theft": "theft",
}


class GameEventBridge:
    """
    Thin adapter that translates MemoryBank events into WorldEvents
    and feeds them to the PropagationEngine.
    """

    def __init__(self, propagation_engine: PropagationEngine):
        self.engine = propagation_engine

    def bridge_event(
        self,
        event_type: str,
        description: str,
        location: str,
        actors: list[str],
        witnesses: list[str],
        details: Optional[dict] = None,
        notability: float = 0.5,
    ) -> None:
        """
        Convert a game event into a WorldEvent and process it.

        Args:
            event_type: The EventType value string (e.g. "discovery")
            description: Human-readable description
            location: Location ID string
            actors: List of actor IDs
            witnesses: List of NPC IDs who witnessed it
            details: Additional event details
            notability: How noteworthy (0-1), affects rumor spread
        """
        if not witnesses:
            return

        world_event = WorldEvent(
            timestamp=self.engine.current_time,
            location=(0, 0),  # Grid coords not used yet
            location_name=location,
            event_type=_EVENT_TYPE_MAP.get(event_type, event_type),
            actors=actors,
            details=details or {},
            witnesses=[
                Witness(
                    npc_id=w,
                    witness_type=WitnessType.DIRECT,
                    clarity=1.0,
                )
                for w in witnesses
            ],
            notability=notability,
        )

        # Inject the description into details for the BiasProcessor
        world_event.details["description"] = description

        self.engine.process_event(world_event)

    def on_threaten(self, npc_id: str, by: str = "player") -> None:
        """Record that a player threatened an NPC — high notability."""
        self.bridge_event(
            event_type="violence",
            description=f"{by} threatened {npc_id}",
            location="",
            actors=[by, npc_id],
            witnesses=[npc_id],
            notability=0.8,
        )

    def on_accuse(self, npc_id: str, by: str = "player") -> None:
        """Record that a player accused an NPC."""
        self.bridge_event(
            event_type="conversation",
            description=f"{by} accused {npc_id}",
            location="",
            actors=[by, npc_id],
            witnesses=[npc_id],
            details={"topic": "accusation", "tone": "aggressive"},
            notability=0.7,
        )

    def trigger_gossip(self, npc_a: str, npc_b: str) -> dict:
        """
        Trigger gossip between two NPCs (e.g. when time passes).
        Returns the interaction result from PropagationEngine.
        """
        return self.engine.simulate_interaction(npc_a, npc_b)
