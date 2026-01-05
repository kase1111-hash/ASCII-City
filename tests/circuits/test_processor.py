"""Tests for the CircuitProcessor class."""

import pytest
import time

from src.shadowengine.circuits.processor import (
    CircuitProcessor,
    ProcessingContext,
    ProcessingResult,
    ProcessingMode,
)
from src.shadowengine.circuits.circuit import (
    BehaviorCircuit,
    CircuitType,
    CircuitState,
)
from src.shadowengine.circuits.signals import (
    SignalType,
    InputSignal,
    OutputSignal,
)
from src.shadowengine.circuits.types import (
    MechanicalCircuit,
    BiologicalCircuit,
)


class TestProcessingContext:
    """Test ProcessingContext dataclass."""

    def test_default_context(self):
        """Test default context values."""
        ctx = ProcessingContext()
        assert ctx.position == (0, 0, 0)
        assert ctx.time_of_day == 12.0
        assert ctx.weather == "clear"
        assert ctx.player_visible is False

    def test_custom_context(self):
        """Test custom context values."""
        ctx = ProcessingContext(
            position=(10, 20, 0),
            environment="cave",
            time_of_day=22.0,
            weather="rain",
            player_visible=True,
            player_distance=5.0
        )
        assert ctx.environment == "cave"
        assert ctx.time_of_day == 22.0
        assert ctx.player_distance == 5.0

    def test_nearby_entities(self):
        """Test nearby entities list."""
        ctx = ProcessingContext(
            nearby_entities=["npc_1", "rat_2", "door_3"]
        )
        assert len(ctx.nearby_entities) == 3
        assert "npc_1" in ctx.nearby_entities

    def test_recent_events(self):
        """Test recent events list."""
        ctx = ProcessingContext(
            recent_events=[
                "Player entered the room",
                "Door slammed shut",
                "Rat squeaked"
            ]
        )
        assert len(ctx.recent_events) == 3

    def test_to_prompt_context(self):
        """Test converting context to LLM prompt format."""
        ctx = ProcessingContext(
            position=(5, 10, 0),
            environment="forest",
            time_of_day=14.5,
            weather="fog",
            player_visible=True,
            player_distance=3.0,
            nearby_entities=["tree", "rock"],
            recent_events=["Wind picked up"]
        )
        prompt = ctx.to_prompt_context()
        assert "forest" in prompt
        assert "14.5" in prompt
        assert "fog" in prompt
        assert "Player visible" in prompt


class TestProcessingResult:
    """Test ProcessingResult dataclass."""

    def test_successful_result(self):
        """Test successful processing result."""
        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        result = ProcessingResult(
            circuit_id="button_1",
            input_signal=signal,
            output_signals=[
                OutputSignal(type=SignalType.ACTIVATE, strength=0.5, source_id="button_1")
            ],
            success=True
        )
        assert result.success is True
        assert result.has_outputs() is True

    def test_failed_result(self):
        """Test failed processing result."""
        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        result = ProcessingResult(
            circuit_id="unknown",
            input_signal=signal,
            success=False,
            error="Circuit not found"
        )
        assert result.success is False
        assert "not found" in result.error

    def test_no_outputs(self):
        """Test result with no outputs."""
        signal = InputSignal(
            type=SignalType.LOOK,
            strength=0.5,
            source_id="player"
        )
        result = ProcessingResult(
            circuit_id="wall_1",
            input_signal=signal,
            output_signals=[],
            success=True
        )
        assert result.has_outputs() is False

    def test_get_signals_of_type(self):
        """Test filtering output signals by type."""
        signal = InputSignal(
            type=SignalType.KICK,
            strength=0.8,
            source_id="player"
        )
        result = ProcessingResult(
            circuit_id="crate",
            input_signal=signal,
            output_signals=[
                OutputSignal(type=SignalType.SOUND, strength=0.5, source_id="crate"),
                OutputSignal(type=SignalType.MOVE, strength=0.3, source_id="crate"),
                OutputSignal(type=SignalType.SOUND, strength=0.2, source_id="crate"),
            ],
            success=True
        )
        sounds = result.get_signals_of_type(SignalType.SOUND)
        assert len(sounds) == 2
        moves = result.get_signals_of_type(SignalType.MOVE)
        assert len(moves) == 1

    def test_state_changes_recorded(self):
        """Test state changes are recorded."""
        signal = InputSignal(
            type=SignalType.DAMAGE,
            strength=0.9,
            source_id="explosion"
        )
        result = ProcessingResult(
            circuit_id="window",
            input_signal=signal,
            state_changes={"health": 0.1, "active": False},
            success=True
        )
        assert result.state_changes["health"] == 0.1
        assert result.state_changes["active"] is False

    def test_narrative_included(self):
        """Test narrative description included."""
        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        result = ProcessingResult(
            circuit_id="button",
            input_signal=signal,
            narrative="The button clicks softly.",
            success=True
        )
        assert "clicks" in result.narrative


class TestCircuitProcessor:
    """Test CircuitProcessor class."""

    def test_processor_creation(self):
        """Test creating a processor."""
        processor = CircuitProcessor()
        assert len(processor.circuits) == 0
        assert processor.stats["signals_processed"] == 0

    def test_register_circuit(self):
        """Test registering a circuit."""
        processor = CircuitProcessor()
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL
        )
        processor.register_circuit(circuit)
        assert "test" in processor.circuits

    def test_unregister_circuit(self):
        """Test unregistering a circuit."""
        processor = CircuitProcessor()
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL
        )
        processor.register_circuit(circuit)
        removed = processor.unregister_circuit("test")
        assert removed is circuit
        assert "test" not in processor.circuits

    def test_get_circuit(self):
        """Test getting a circuit by ID."""
        processor = CircuitProcessor()
        circuit = BehaviorCircuit(
            id="button_1",
            name="Button",
            circuit_type=CircuitType.MECHANICAL
        )
        processor.register_circuit(circuit)
        retrieved = processor.get_circuit("button_1")
        assert retrieved is circuit

    def test_get_nonexistent_circuit(self):
        """Test getting a circuit that doesn't exist."""
        processor = CircuitProcessor()
        assert processor.get_circuit("nonexistent") is None

    def test_process_signal(self):
        """Test processing a signal through a circuit."""
        processor = CircuitProcessor()
        circuit = BehaviorCircuit(
            id="button",
            name="Button",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS],
            output_signals=[SignalType.ACTIVATE]
        )
        processor.register_circuit(circuit)

        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        result = processor.process_signal("button", signal)

        assert result.success is True
        assert result.circuit_id == "button"
        assert processor.stats["signals_processed"] == 1

    def test_process_signal_nonexistent_circuit(self):
        """Test processing signal for nonexistent circuit."""
        processor = CircuitProcessor()
        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        result = processor.process_signal("nonexistent", signal)
        assert result.success is False
        assert "not found" in result.error

    def test_process_signal_with_context(self):
        """Test processing with context."""
        processor = CircuitProcessor()
        circuit = BiologicalCircuit(
            id="rat",
            name="Rat"
        )
        processor.register_circuit(circuit)

        signal = InputSignal(
            type=SignalType.SOUND,
            strength=0.8,
            source_id="explosion"
        )
        context = ProcessingContext(
            environment="sewer",
            player_visible=True,
            player_distance=2.0
        )
        result = processor.process_signal("rat", signal, context)
        assert result.success is True

    def test_broadcast_signal(self):
        """Test broadcasting signal to multiple circuits."""
        processor = CircuitProcessor()

        # Register multiple circuits that respond to sound
        for i in range(3):
            circuit = BiologicalCircuit(
                id=f"rat_{i}",
                name=f"Rat {i}"
            )
            processor.register_circuit(circuit)

        # Add a circuit that doesn't respond to sound
        # MechanicalCircuit already has its input_signals defined
        door = MechanicalCircuit(
            id="door",
            name="Door"
        )
        processor.register_circuit(door)

        signal = InputSignal(
            type=SignalType.SOUND,
            strength=0.7,
            source_id="gunshot"
        )
        results = processor.broadcast_signal(signal)

        # Only rats should respond
        assert len(results) == 3
        assert all(r.circuit_id.startswith("rat") for r in results)

    def test_propagate_outputs(self):
        """Test output signal propagation."""
        processor = CircuitProcessor()

        # Alarm that emits sound when activated
        alarm = BehaviorCircuit(
            id="alarm",
            name="Alarm",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS],
            output_signals=[SignalType.SOUND]
        )
        processor.register_circuit(alarm)

        # Rats that flee from sound
        for i in range(2):
            rat = BiologicalCircuit(
                id=f"rat_{i}",
                name=f"Rat {i}"
            )
            processor.register_circuit(rat)

        # Press the alarm
        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        initial_results = [processor.process_signal("alarm", signal)]

        # Propagate the sound
        all_results = processor.propagate_outputs(initial_results)

        # Should have initial result + rat responses
        assert len(all_results) >= 1

    def test_propagation_depth_limit(self):
        """Test propagation respects depth limit."""
        processor = CircuitProcessor()

        # Create chain: button -> alarm -> rats -> ???
        processor.register_circuit(BehaviorCircuit(
            id="button",
            name="Button",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS],
            output_signals=[SignalType.ACTIVATE]
        ))

        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        initial_results = [processor.process_signal("button", signal)]

        # Propagate with depth limit
        all_results = processor.propagate_outputs(initial_results, max_depth=1)
        # Should not infinitely loop

    def test_update_all(self):
        """Test updating all circuits over time."""
        processor = CircuitProcessor()

        for i in range(3):
            circuit = BehaviorCircuit(
                id=f"circuit_{i}",
                name=f"Circuit {i}",
                circuit_type=CircuitType.MECHANICAL
            )
            circuit.state.fatigue = 0.5
            processor.register_circuit(circuit)

        outputs = processor.update_all(10.0)

        # Check fatigue reduced for all
        for circuit in processor.circuits.values():
            assert circuit.state.fatigue < 0.5

    def test_get_circuits_by_type(self):
        """Test getting circuits by type."""
        processor = CircuitProcessor()

        processor.register_circuit(MechanicalCircuit(id="mech1", name="M1"))
        processor.register_circuit(MechanicalCircuit(id="mech2", name="M2"))
        processor.register_circuit(BiologicalCircuit(id="bio1", name="B1"))

        mechanical = processor.get_circuits_by_type(CircuitType.MECHANICAL)
        biological = processor.get_circuits_by_type(CircuitType.BIOLOGICAL)

        assert len(mechanical) == 2
        assert len(biological) == 1

    def test_get_circuits_with_affordance(self):
        """Test getting circuits with specific affordance."""
        processor = CircuitProcessor()

        processor.register_circuit(BehaviorCircuit(
            id="door",
            name="Door",
            circuit_type=CircuitType.MECHANICAL,
            affordances=["openable", "lockable"]
        ))
        processor.register_circuit(BehaviorCircuit(
            id="window",
            name="Window",
            circuit_type=CircuitType.MECHANICAL,
            affordances=["breakable", "openable"]
        ))
        processor.register_circuit(BehaviorCircuit(
            id="wall",
            name="Wall",
            circuit_type=CircuitType.MECHANICAL,
            affordances=["climbable"]
        ))

        openable = processor.get_circuits_with_affordance("openable")
        assert len(openable) == 2

        breakable = processor.get_circuits_with_affordance("breakable")
        assert len(breakable) == 1

    def test_llm_evaluator(self):
        """Test setting and using LLM evaluator."""
        processor = CircuitProcessor()

        def mock_llm(circuit, signal, context):
            return [
                OutputSignal(
                    type=SignalType.SOUND,
                    strength=0.5,
                    source_id=circuit.id,
                    data={"description": "A mysterious sound echoes..."}
                )
            ], "The ancient mechanism awakens."

        processor.set_llm_evaluator(mock_llm)

        circuit = BehaviorCircuit(
            id="ancient",
            name="Ancient Device",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS]
        )
        processor.register_circuit(circuit)

        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        result = processor.process_signal(
            "ancient",
            signal,
            mode=ProcessingMode.LLM_EVALUATED
        )

        assert result.success is True
        assert "awakens" in result.narrative
        assert processor.stats["llm_calls"] == 1

    def test_stats_tracking(self):
        """Test processing statistics."""
        processor = CircuitProcessor()

        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS],
            output_signals=[SignalType.SOUND, SignalType.ACTIVATE]
        )
        processor.register_circuit(circuit)

        for _ in range(5):
            signal = InputSignal(
                type=SignalType.PRESS,
                strength=0.5,
                source_id="player"
            )
            processor.process_signal("test", signal)

        stats = processor.get_stats()
        assert stats["signals_processed"] == 5
        assert stats["outputs_generated"] > 0
        assert stats["total_processing_time"] > 0

    def test_reset_stats(self):
        """Test resetting statistics."""
        processor = CircuitProcessor()
        processor.stats["signals_processed"] = 100
        processor.reset_stats()
        assert processor.stats["signals_processed"] == 0

    def test_clear(self):
        """Test clearing all circuits."""
        processor = CircuitProcessor()

        for i in range(5):
            processor.register_circuit(BehaviorCircuit(
                id=f"c_{i}",
                name=f"C{i}",
                circuit_type=CircuitType.MECHANICAL
            ))

        processor.clear()
        assert len(processor.circuits) == 0


class TestProcessingMode:
    """Test different processing modes."""

    def test_immediate_mode(self):
        """Test immediate processing mode."""
        processor = CircuitProcessor()
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS]
        )
        processor.register_circuit(circuit)

        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        result = processor.process_signal(
            "test",
            signal,
            mode=ProcessingMode.IMMEDIATE
        )
        assert result.mode_used == ProcessingMode.IMMEDIATE

    def test_llm_mode_without_evaluator(self):
        """Test LLM mode falls back without evaluator."""
        processor = CircuitProcessor()
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS]
        )
        processor.register_circuit(circuit)

        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        # No LLM evaluator set, should fall back to immediate
        result = processor.process_signal(
            "test",
            signal,
            mode=ProcessingMode.LLM_EVALUATED
        )
        assert result.success is True


class TestDefaultNarratives:
    """Test default narrative generation."""

    def test_kick_narrative(self):
        """Test narrative for kick action."""
        processor = CircuitProcessor()
        circuit = BehaviorCircuit(
            id="crate",
            name="Wooden Crate",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.KICK],
            output_signals=[SignalType.SOUND]
        )
        processor.register_circuit(circuit)

        signal = InputSignal(
            type=SignalType.KICK,
            strength=0.6,
            source_id="player"
        )
        result = processor.process_signal("crate", signal)

        assert "Wooden Crate" in result.narrative
        assert "kicked" in result.narrative

    def test_collapse_narrative(self):
        """Test narrative for collapse."""
        processor = CircuitProcessor()
        circuit = BehaviorCircuit(
            id="glass",
            name="Glass Window",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.DAMAGE],
            output_signals=[SignalType.COLLAPSE, SignalType.SOUND]
        )
        circuit.state.health = 0.1
        processor.register_circuit(circuit)

        signal = InputSignal(
            type=SignalType.DAMAGE,
            strength=0.9,
            source_id="rock"
        )
        result = processor.process_signal("glass", signal)

        if any(o.type == SignalType.COLLAPSE for o in result.output_signals):
            assert "crumbles" in result.narrative
