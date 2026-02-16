"""
Circuit Processor - Evaluates signals across multiple circuits.

Handles signal propagation, context-aware processing, and LLM integration
for emergent behavioral responses.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import time

from .signals import SignalType, InputSignal, OutputSignal
from .circuit import BehaviorCircuit, CircuitType


class ProcessingMode(Enum):
    """How signals should be processed."""
    IMMEDIATE = "immediate"      # Process instantly, no LLM
    QUEUED = "queued"            # Queue for batch processing
    LLM_EVALUATED = "llm"        # Send to LLM for evaluation


@dataclass
class ProcessingContext:
    """
    Context for circuit processing, providing environmental
    and situational information.
    """
    # Location context
    position: tuple[int, int, int] = (0, 0, 0)  # x, y, z
    tile_type: str = ""
    environment: str = ""  # "forest", "cave", "urban", etc.

    # Time context
    time_of_day: float = 12.0  # 0-24 hour
    weather: str = "clear"

    # Entity context
    nearby_entities: list[str] = field(default_factory=list)
    player_visible: bool = False
    player_distance: float = float('inf')

    # Memory context (for LLM)
    recent_events: list[str] = field(default_factory=list)
    entity_memories: dict = field(default_factory=dict)

    # Custom context data
    custom: dict = field(default_factory=dict)

    def to_prompt_context(self) -> str:
        """Convert context to LLM prompt format."""
        lines = [
            f"Location: {self.environment} at ({self.position[0]}, {self.position[1]})",
            f"Time: {self.time_of_day:.1f} hours, weather: {self.weather}",
            f"Nearby: {', '.join(self.nearby_entities) if self.nearby_entities else 'none'}",
        ]

        if self.player_visible:
            lines.append(f"Player visible at distance {self.player_distance:.1f}")

        if self.recent_events:
            lines.append(f"Recent events: {', '.join(self.recent_events[-3:])}")

        return "\n".join(lines)


@dataclass
class ProcessingResult:
    """Result of processing a signal through one or more circuits."""
    # The circuit that was processed
    circuit_id: str

    # Original input signal
    input_signal: InputSignal

    # Output signals generated
    output_signals: list[OutputSignal] = field(default_factory=list)

    # State changes that occurred
    state_changes: dict = field(default_factory=dict)

    # Narrative description (from LLM or templates)
    narrative: str = ""

    # Processing metadata
    processing_time: float = 0.0
    mode_used: ProcessingMode = ProcessingMode.IMMEDIATE

    # Whether processing was successful
    success: bool = True
    error: Optional[str] = None

    def has_outputs(self) -> bool:
        """Check if any output signals were generated."""
        return len(self.output_signals) > 0

    def get_signals_of_type(self, signal_type: SignalType) -> list[OutputSignal]:
        """Get output signals of a specific type."""
        return [s for s in self.output_signals if s.type == signal_type]


class CircuitProcessor:
    """
    Processes signals through circuits, handling propagation
    and enabling LLM-driven evaluation.
    """

    def __init__(self):
        # Registered circuits by ID
        self.circuits: dict[str, BehaviorCircuit] = {}

        # Signal propagation rules
        self.propagation_rules: dict[SignalType, list[SignalType]] = {
            # Sound can trigger alert
            SignalType.SOUND: [SignalType.ALERT],
            # Emit (light/particles) can trigger visual detection
            SignalType.EMIT: [SignalType.ALERT],
            # Damage can trigger collapse or flee
            SignalType.DAMAGE: [SignalType.COLLAPSE, SignalType.FLEE],
            # Activate can trigger movement or state change
            SignalType.ACTIVATE: [SignalType.MOVE, SignalType.CHANGE_STATE],
        }

        # LLM evaluator callback (set externally)
        self._llm_evaluator: Optional[Callable] = None

        # Processing statistics
        self.stats = {
            "signals_processed": 0,
            "outputs_generated": 0,
            "llm_calls": 0,
            "total_processing_time": 0.0
        }

    def register_circuit(self, circuit: BehaviorCircuit) -> None:
        """Register a circuit for processing."""
        self.circuits[circuit.id] = circuit

    def unregister_circuit(self, circuit_id: str) -> Optional[BehaviorCircuit]:
        """Unregister and return a circuit."""
        return self.circuits.pop(circuit_id, None)

    def get_circuit(self, circuit_id: str) -> Optional[BehaviorCircuit]:
        """Get a circuit by ID."""
        return self.circuits.get(circuit_id)

    def set_llm_evaluator(self, evaluator: Callable) -> None:
        """
        Set LLM evaluator function.

        The evaluator should accept (circuit, signal, context) and return
        a tuple of (list[OutputSignal], narrative: str).
        """
        self._llm_evaluator = evaluator

    def process_signal(
        self,
        circuit_id: str,
        signal: InputSignal,
        context: Optional[ProcessingContext] = None,
        mode: ProcessingMode = ProcessingMode.IMMEDIATE
    ) -> ProcessingResult:
        """
        Process a signal through a specific circuit.

        Args:
            circuit_id: ID of circuit to process
            signal: Input signal to process
            context: Optional processing context
            mode: Processing mode to use

        Returns:
            ProcessingResult with outputs and metadata
        """
        start_time = time.time()

        circuit = self.circuits.get(circuit_id)
        if not circuit:
            return ProcessingResult(
                circuit_id=circuit_id,
                input_signal=signal,
                success=False,
                error=f"Circuit not found: {circuit_id}"
            )

        context = context or ProcessingContext()

        try:
            if mode == ProcessingMode.LLM_EVALUATED and self._llm_evaluator:
                outputs, narrative = self._llm_evaluator(circuit, signal, context)
                self.stats["llm_calls"] += 1
            else:
                outputs = circuit.receive_signal(signal)
                narrative = self._generate_default_narrative(circuit, signal, outputs)

            # Track state changes
            state_changes = self._capture_state_changes(circuit, signal)

            processing_time = time.time() - start_time

            # Update stats
            self.stats["signals_processed"] += 1
            self.stats["outputs_generated"] += len(outputs)
            self.stats["total_processing_time"] += processing_time

            return ProcessingResult(
                circuit_id=circuit_id,
                input_signal=signal,
                output_signals=outputs,
                state_changes=state_changes,
                narrative=narrative,
                processing_time=processing_time,
                mode_used=mode,
                success=True
            )

        except Exception as e:
            return ProcessingResult(
                circuit_id=circuit_id,
                input_signal=signal,
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )

    def broadcast_signal(
        self,
        signal: InputSignal,
        context: Optional[ProcessingContext] = None,
        radius: Optional[float] = None
    ) -> list[ProcessingResult]:
        """
        Broadcast a signal to all circuits that respond to it.

        Args:
            signal: Signal to broadcast
            context: Optional processing context
            radius: Optional radius limit (uses signal.radius if not specified)

        Returns:
            List of processing results from all affected circuits
        """
        results = []
        radius = radius or getattr(signal, 'radius', float('inf'))

        for circuit_id, circuit in self.circuits.items():
            # Skip the circuit that emitted this signal (prevent self-triggering)
            if signal.source_id and circuit_id == signal.source_id:
                continue

            # Skip circuits that don't respond to this signal type
            if not circuit.responds_to(signal.type):
                continue

            # Apply distance filtering if context provides positions
            # (simplified - full implementation would use grid positions)

            result = self.process_signal(circuit_id, signal, context)
            if result.success:
                results.append(result)

        return results

    def propagate_outputs(
        self,
        results: list[ProcessingResult],
        context: Optional[ProcessingContext] = None,
        max_depth: int = 3
    ) -> list[ProcessingResult]:
        """
        Propagate output signals as new inputs to create chain reactions.

        Args:
            results: Initial processing results
            context: Processing context
            max_depth: Maximum propagation depth to prevent infinite loops

        Returns:
            All results including propagated ones
        """
        all_results = list(results)
        current_results = results
        depth = 0

        while current_results and depth < max_depth:
            next_results = []

            for result in current_results:
                for output in result.output_signals:
                    # Convert output to input for propagation
                    propagated_input = InputSignal(
                        type=output.type,
                        strength=output.strength * 0.8,  # Decay
                        source_id=output.source_id,
                        data=output.data
                    )

                    # Broadcast to nearby circuits
                    propagated = self.broadcast_signal(
                        propagated_input,
                        context,
                        radius=output.radius
                    )
                    next_results.extend(propagated)

            all_results.extend(next_results)
            current_results = next_results
            depth += 1

        return all_results

    def update_all(self, delta_time: float) -> list[OutputSignal]:
        """
        Update all circuits over time.

        Args:
            delta_time: Time elapsed since last update

        Returns:
            Any output signals generated during updates
        """
        all_outputs = []

        for circuit in self.circuits.values():
            outputs = circuit.update(delta_time)
            all_outputs.extend(outputs)

        return all_outputs

    def _generate_default_narrative(
        self,
        circuit: BehaviorCircuit,
        signal: InputSignal,
        outputs: list[OutputSignal]
    ) -> str:
        """Generate default narrative for non-LLM processing."""
        action_verbs = {
            SignalType.KICK: "is kicked",
            SignalType.PUSH: "is pushed",
            SignalType.PRESS: "is pressed",
            SignalType.LOOK: "is examined",
            SignalType.SAY: "is spoken to",
            SignalType.DAMAGE: "takes damage",
        }

        action = action_verbs.get(signal.type, f"receives {signal.type.value}")

        parts = [f"The {circuit.name} {action}."]

        if outputs:
            if SignalType.SOUND in [o.type for o in outputs]:
                parts.append("A sound echoes.")
            if SignalType.COLLAPSE in [o.type for o in outputs]:
                parts.append("It crumbles!")
            if SignalType.ACTIVATE in [o.type for o in outputs]:
                parts.append("Something activates.")

        return " ".join(parts)

    def _capture_state_changes(
        self,
        circuit: BehaviorCircuit,
        signal: InputSignal
    ) -> dict:
        """Capture notable state changes for the result."""
        changes = {}

        # Note health changes from damage signals
        if signal.type in (SignalType.DAMAGE, SignalType.KICK, SignalType.PUSH):
            if circuit.state.health < 1.0:
                changes["health"] = circuit.state.health

        # Note fatigue changes
        if circuit.state.fatigue > 0:
            changes["fatigue"] = circuit.state.fatigue

        # Note if circuit became inactive
        if not circuit.state.active:
            changes["active"] = False

        return changes

    def get_circuits_by_type(self, circuit_type: CircuitType) -> list[BehaviorCircuit]:
        """Get all circuits of a specific type."""
        return [c for c in self.circuits.values() if c.circuit_type == circuit_type]

    def get_circuits_with_affordance(self, affordance: str) -> list[BehaviorCircuit]:
        """Get all circuits with a specific affordance."""
        return [c for c in self.circuits.values() if c.has_affordance(affordance)]

    def get_stats(self) -> dict:
        """Get processing statistics."""
        return dict(self.stats)

    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self.stats = {
            "signals_processed": 0,
            "outputs_generated": 0,
            "llm_calls": 0,
            "total_processing_time": 0.0
        }

    def clear(self) -> None:
        """Clear all registered circuits."""
        self.circuits.clear()
        self.reset_stats()
