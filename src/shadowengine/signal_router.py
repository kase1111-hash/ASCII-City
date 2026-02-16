"""
SignalRouter - Translates circuit output signals into game state changes.

When a BehaviorCircuit processes an InputSignal it produces OutputSignals.
The SignalRouter interprets those outputs and applies concrete effects:
  SOUND   → NPCs at the location form a witnessed-event belief
  COLLAPSE → the hotspot is deactivated (destroyed)
  ACTIVATE → a connected circuit receives an activation signal
  ALERT   → NPCs become aware of the player's action
  TRIGGER → a hidden hotspot or fact is revealed
"""

from typing import Optional, TYPE_CHECKING
import logging

from .circuits import (
    BehaviorCircuit, SignalType, InputSignal, OutputSignal,
    ProcessingResult,
)
from .interaction import Hotspot
from .memory import EventType

if TYPE_CHECKING:
    from .render import Renderer, Location

logger = logging.getLogger(__name__)


class SignalRouter:
    """
    Routes output signals from circuits to game-state effects.

    Keeps a reference to the renderer (for narration) and provides
    a single entry point — ``route_outputs`` — called by CommandHandler
    after a circuit processes a signal.
    """

    def __init__(self, renderer: 'Renderer'):
        self.renderer = renderer

    def route_outputs(
        self,
        result: ProcessingResult,
        hotspot: Hotspot,
        state: 'GameState',
        location: Optional['Location'] = None,
    ) -> None:
        """
        Route all output signals from a ProcessingResult to game effects.

        Args:
            result: The processing result from a circuit
            hotspot: The hotspot whose circuit produced these outputs
            state: Current game state
            location: The current location (for NPC lookups)
        """
        if not result.success or not result.has_outputs():
            return

        for output in result.output_signals:
            self._route_signal(output, hotspot, state, location)

    def _route_signal(
        self,
        output: OutputSignal,
        hotspot: Hotspot,
        state: 'GameState',
        location: Optional['Location'],
    ) -> None:
        """Route a single output signal to the appropriate handler."""
        handlers = {
            SignalType.SOUND: self._handle_sound,
            SignalType.COLLAPSE: self._handle_collapse,
            SignalType.ACTIVATE: self._handle_activate,
            SignalType.ALERT: self._handle_alert,
            SignalType.TRIGGER: self._handle_trigger,
            SignalType.EMIT: self._handle_emit,
        }

        handler = handlers.get(output.type)
        if handler:
            handler(output, hotspot, state, location)

    # ------------------------------------------------------------------
    # Individual signal handlers
    # ------------------------------------------------------------------

    def _handle_sound(
        self,
        output: OutputSignal,
        hotspot: Hotspot,
        state: 'GameState',
        location: Optional['Location'],
    ) -> None:
        """SOUND — NPCs at the location witness the noise."""
        description = output.data.get(
            "description",
            f"A sound comes from {hotspot.label}.",
        )

        if output.strength > 0.3:
            self.renderer.render_narration(description)

        # Record as witnessed event for NPCs present
        witness_ids = self._get_npc_ids(state, location)
        if witness_ids:
            state.memory.record_witnessed_event(
                event_type=EventType.DISCOVERY,
                description=f"Heard a sound from {hotspot.label}",
                location=state.current_location_id,
                actors=["player"],
                witnesses=witness_ids,
                player_witnessed=False,
            )

    def _handle_collapse(
        self,
        output: OutputSignal,
        hotspot: Hotspot,
        state: 'GameState',
        location: Optional['Location'],
    ) -> None:
        """COLLAPSE — the hotspot is destroyed."""
        self.renderer.render_narration(
            output.data.get("description", f"The {hotspot.label} breaks apart!")
        )
        hotspot.deactivate()

        # If collapsing reveals a fact, record it
        if hotspot.reveals_fact:
            state.memory.player_discovers(
                fact_id=hotspot.reveals_fact,
                description=hotspot.examine_text or f"Found something in the {hotspot.label}.",
                location=state.current_location_id,
                source=f"destroyed {hotspot.label}",
                is_evidence=True,
            )
            self.renderer.render_discovery(
                hotspot.examine_text or f"You find something in the wreckage."
            )

        # NPCs witness the destruction
        witness_ids = self._get_npc_ids(state, location)
        if witness_ids:
            state.memory.record_witnessed_event(
                event_type=EventType.DISCOVERY,
                description=f"Player destroyed {hotspot.label}",
                location=state.current_location_id,
                actors=["player"],
                witnesses=witness_ids,
                player_witnessed=False,
            )

    def _handle_activate(
        self,
        output: OutputSignal,
        hotspot: Hotspot,
        state: 'GameState',
        location: Optional['Location'],
    ) -> None:
        """ACTIVATE — trigger a connected circuit or reveal something."""
        target_id = output.target_id
        if not target_id or not location:
            return

        # Find connected hotspot by target_id
        for hs in location.hotspots:
            if hs.id == target_id and hs.circuit:
                activation = InputSignal(
                    type=SignalType.PRESS,
                    strength=output.strength,
                    source_id=hotspot.id,
                )
                cascaded_outputs = hs.circuit.receive_signal(activation)
                # Route cascaded outputs so chain reactions propagate
                if cascaded_outputs:
                    cascaded_result = ProcessingResult(
                        circuit_id=hs.circuit.id,
                        input_signal=activation,
                        output_signals=cascaded_outputs,
                        success=True,
                    )
                    self.route_outputs(cascaded_result, hs, state, location)
                break

    def _handle_alert(
        self,
        output: OutputSignal,
        hotspot: Hotspot,
        state: 'GameState',
        location: Optional['Location'],
    ) -> None:
        """ALERT — NPCs become aware of the player's action."""
        witness_ids = self._get_npc_ids(state, location)
        if witness_ids:
            state.memory.record_witnessed_event(
                event_type=EventType.DISCOVERY,
                description=output.data.get(
                    "description",
                    f"Noticed the player interacting with {hotspot.label}",
                ),
                location=state.current_location_id,
                actors=["player"],
                witnesses=witness_ids,
                player_witnessed=False,
            )

    def _handle_trigger(
        self,
        output: OutputSignal,
        hotspot: Hotspot,
        state: 'GameState',
        location: Optional['Location'],
    ) -> None:
        """TRIGGER — reveal a hidden hotspot or create a discovery."""
        fact_id = output.data.get("fact_id")
        if fact_id:
            description = output.data.get(
                "description",
                f"Something is revealed about {hotspot.label}.",
            )
            state.memory.player_discovers(
                fact_id=fact_id,
                description=description,
                location=state.current_location_id,
                source=f"triggered by {hotspot.label}",
                is_evidence=output.data.get("is_evidence", False),
            )
            self.renderer.render_discovery(description)

        # Reveal a hidden hotspot if specified
        reveal_id = output.data.get("reveal_hotspot")
        if reveal_id and location:
            for hs in location.hotspots:
                if hs.id == reveal_id:
                    hs.show()
                    self.renderer.render_narration(
                        output.data.get("reveal_text", f"You notice {hs.label}.")
                    )
                    break

    def _handle_emit(
        self,
        output: OutputSignal,
        hotspot: Hotspot,
        state: 'GameState',
        location: Optional['Location'],
    ) -> None:
        """EMIT — the entity emits light, particles, etc."""
        description = output.data.get(
            "description",
            f"The {hotspot.label} emits something.",
        )
        self.renderer.render_narration(description)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_npc_ids(
        state: 'GameState',
        location: Optional['Location'],
    ) -> list[str]:
        """Get NPC IDs present at the current location."""
        if not location:
            return []

        from .interaction import HotspotType

        npc_ids = []
        for hs in location.hotspots:
            if (
                hs.hotspot_type == HotspotType.PERSON
                and hs.target_id
                and hs.target_id in state.characters
                and hs.active
            ):
                npc_ids.append(hs.target_id)
        return npc_ids
