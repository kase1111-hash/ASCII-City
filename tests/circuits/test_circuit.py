"""Tests for the core BehaviorCircuit class."""

import pytest
import time

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


class TestCircuitType:
    """Test CircuitType enum."""

    def test_mechanical_type(self):
        """Test mechanical circuit type."""
        assert CircuitType.MECHANICAL.value == "mechanical"

    def test_biological_type(self):
        """Test biological circuit type."""
        assert CircuitType.BIOLOGICAL.value == "biological"

    def test_environmental_type(self):
        """Test environmental circuit type."""
        assert CircuitType.ENVIRONMENTAL.value == "environmental"


class TestCircuitState:
    """Test CircuitState dataclass."""

    def test_default_state(self):
        """Test default circuit state values."""
        state = CircuitState()
        assert state.health == 1.0
        assert state.power == 1.0
        assert state.fatigue == 0.0
        assert state.trust == 0.5
        assert state.age == 0.0
        assert state.active is True

    def test_update_age(self):
        """Test aging the circuit."""
        state = CircuitState()
        state.update_age(10.0)
        assert state.age == 10.0
        state.update_age(5.0)
        assert state.age == 15.0

    def test_apply_damage(self):
        """Test applying damage."""
        state = CircuitState(health=1.0)
        destroyed = state.apply_damage(0.3)
        assert state.health == 0.7
        assert destroyed is False

    def test_apply_lethal_damage(self):
        """Test applying lethal damage."""
        state = CircuitState(health=0.5)
        destroyed = state.apply_damage(0.6)
        assert state.health == 0.0
        assert destroyed is True

    def test_apply_fatigue(self):
        """Test applying fatigue."""
        state = CircuitState()
        state.apply_fatigue(0.3)
        assert state.fatigue == 0.3
        state.apply_fatigue(0.8)
        assert state.fatigue == 1.0  # Capped

    def test_recover(self):
        """Test recovery from fatigue."""
        state = CircuitState(fatigue=0.5)
        state.recover(0.2)
        assert state.fatigue == 0.3
        state.recover(0.5)
        assert state.fatigue == 0.0  # Capped at 0

    def test_modify_trust(self):
        """Test modifying trust level."""
        state = CircuitState(trust=0.5)
        state.modify_trust(0.3)
        assert state.trust == 0.8
        state.modify_trust(0.5)
        assert state.trust == 1.0  # Capped

    def test_modify_trust_negative(self):
        """Test decreasing trust."""
        state = CircuitState(trust=0.5)
        state.modify_trust(-0.3)
        assert state.trust == 0.2
        state.modify_trust(-0.5)
        assert state.trust == 0.0  # Capped

    def test_state_serialization(self):
        """Test state serialization."""
        state = CircuitState(health=0.8, power=0.9, trust=0.7)
        data = state.to_dict()
        assert data["health"] == 0.8
        assert data["power"] == 0.9
        assert data["trust"] == 0.7

    def test_state_deserialization(self):
        """Test state deserialization."""
        data = {"health": 0.6, "fatigue": 0.2, "custom": {"mood": "angry"}}
        state = CircuitState.from_dict(data)
        assert state.health == 0.6
        assert state.fatigue == 0.2
        assert state.custom["mood"] == "angry"


class TestBehaviorCircuit:
    """Test BehaviorCircuit class."""

    def test_circuit_creation(self):
        """Test creating a behavior circuit."""
        circuit = BehaviorCircuit(
            id="button_1",
            name="Elevator Button",
            circuit_type=CircuitType.MECHANICAL
        )
        assert circuit.id == "button_1"
        assert circuit.name == "Elevator Button"
        assert circuit.circuit_type == CircuitType.MECHANICAL

    def test_circuit_with_signals(self):
        """Test circuit with input/output signals."""
        circuit = BehaviorCircuit(
            id="rat_1",
            name="Sewer Rat",
            circuit_type=CircuitType.BIOLOGICAL,
            input_signals=[SignalType.SOUND, SignalType.LOOK, SignalType.DAMAGE],
            output_signals=[SignalType.FLEE, SignalType.SOUND, SignalType.ATTACK]
        )
        assert SignalType.SOUND in circuit.input_signals
        assert SignalType.FLEE in circuit.output_signals

    def test_responds_to(self):
        """Test checking if circuit responds to signal type."""
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS, SignalType.KICK]
        )
        assert circuit.responds_to(SignalType.PRESS) is True
        assert circuit.responds_to(SignalType.SAY) is False

    def test_can_emit(self):
        """Test checking if circuit can emit signal type."""
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL,
            output_signals=[SignalType.SOUND, SignalType.ACTIVATE]
        )
        assert circuit.can_emit(SignalType.SOUND) is True
        assert circuit.can_emit(SignalType.FLEE) is False

    def test_has_affordance(self):
        """Test checking affordances."""
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL,
            affordances=["pressable", "breakable"]
        )
        assert circuit.has_affordance("pressable") is True
        assert circuit.has_affordance("climbable") is False

    def test_receive_signal_not_responding(self):
        """Test receiving signal circuit doesn't respond to."""
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS]
        )
        signal = InputSignal(
            type=SignalType.SAY,
            strength=0.5,
            source_id="player"
        )
        outputs = circuit.receive_signal(signal)
        assert outputs == []

    def test_receive_signal_inactive(self):
        """Test receiving signal when circuit is inactive."""
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS]
        )
        circuit.state.active = False
        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        outputs = circuit.receive_signal(signal)
        assert outputs == []

    def test_receive_press_signal(self):
        """Test receiving press signal generates activation."""
        circuit = BehaviorCircuit(
            id="button",
            name="Button",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS],
            output_signals=[SignalType.ACTIVATE]
        )
        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        outputs = circuit.receive_signal(signal)
        assert any(o.type == SignalType.ACTIVATE for o in outputs)

    def test_receive_kick_generates_sound(self):
        """Test kicking generates sound output."""
        circuit = BehaviorCircuit(
            id="crate",
            name="Wooden Crate",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.KICK],
            output_signals=[SignalType.SOUND]
        )
        signal = InputSignal(
            type=SignalType.KICK,
            strength=0.6,
            source_id="player"
        )
        outputs = circuit.receive_signal(signal)
        assert any(o.type == SignalType.SOUND for o in outputs)

    def test_strong_damage_destroys_circuit(self):
        """Test strong damage can destroy circuit."""
        circuit = BehaviorCircuit(
            id="glass",
            name="Glass Window",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.DAMAGE],
            output_signals=[SignalType.COLLAPSE, SignalType.SOUND]
        )
        circuit.state.health = 0.1  # Very low health
        signal = InputSignal(
            type=SignalType.DAMAGE,
            strength=0.9,
            source_id="player"
        )
        outputs = circuit.receive_signal(signal)
        assert any(o.type == SignalType.COLLAPSE for o in outputs)

    def test_history_recording(self):
        """Test interaction history is recorded."""
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS]
        )
        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        circuit.receive_signal(signal)
        assert len(circuit.history) == 1
        assert circuit.history[0]["signal_type"] == "press"

    def test_history_trimming(self):
        """Test history is trimmed when too long."""
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS],
            max_history=5
        )
        for i in range(10):
            signal = InputSignal(
                type=SignalType.PRESS,
                strength=0.5,
                source_id=f"source_{i}"
            )
            circuit.receive_signal(signal)
        assert len(circuit.history) == 5

    def test_get_recent_history(self):
        """Test getting recent history."""
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS]
        )
        for i in range(5):
            signal = InputSignal(
                type=SignalType.PRESS,
                strength=0.5,
                source_id=f"source_{i}"
            )
            circuit.receive_signal(signal)
        recent = circuit.get_recent_history(3)
        assert len(recent) == 3

    def test_update_reduces_fatigue(self):
        """Test update gradually reduces fatigue."""
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL
        )
        circuit.state.fatigue = 0.5
        circuit.update(10.0)
        assert circuit.state.fatigue < 0.5

    def test_update_advances_age(self):
        """Test update advances age."""
        circuit = BehaviorCircuit(
            id="test",
            name="Test",
            circuit_type=CircuitType.MECHANICAL
        )
        circuit.update(5.0)
        assert circuit.state.age == 5.0

    def test_custom_processor(self):
        """Test setting custom signal processor."""
        def custom_process(circuit, signal):
            return [OutputSignal(
                type=SignalType.EMIT,
                strength=1.0,
                source_id=circuit.id
            )]

        circuit = BehaviorCircuit(
            id="lamp",
            name="Magic Lamp",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS]
        )
        circuit.set_processor(custom_process)

        signal = InputSignal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        outputs = circuit.receive_signal(signal)
        assert any(o.type == SignalType.EMIT for o in outputs)

    def test_circuit_serialization(self):
        """Test circuit serialization."""
        circuit = BehaviorCircuit(
            id="test",
            name="Test Circuit",
            circuit_type=CircuitType.BIOLOGICAL,
            description="A test circuit",
            input_signals=[SignalType.LOOK, SignalType.SAY],
            output_signals=[SignalType.FLEE],
            affordances=["observable", "talkable"]
        )
        data = circuit.to_dict()
        assert data["id"] == "test"
        assert data["name"] == "Test Circuit"
        assert data["circuit_type"] == "biological"
        assert "look" in data["input_signals"]
        assert "observable" in data["affordances"]

    def test_circuit_deserialization(self):
        """Test circuit deserialization."""
        data = {
            "id": "restored",
            "name": "Restored Circuit",
            "circuit_type": "environmental",
            "description": "Restored from data",
            "input_signals": ["heat", "cold"],
            "output_signals": ["emit"],
            "affordances": [],
            "state": {"health": 0.8},
            "history": []
        }
        circuit = BehaviorCircuit.from_dict(data)
        assert circuit.id == "restored"
        assert circuit.circuit_type == CircuitType.ENVIRONMENTAL
        assert circuit.state.health == 0.8

    def test_circuit_cloning(self):
        """Test cloning a circuit."""
        original = BehaviorCircuit(
            id="original",
            name="Original",
            circuit_type=CircuitType.MECHANICAL,
            input_signals=[SignalType.PRESS]
        )
        # Add some history
        signal = InputSignal(type=SignalType.PRESS, strength=0.5, source_id="test")
        original.receive_signal(signal)

        clone = original.clone("cloned")
        assert clone.id == "cloned"
        assert clone.name == "Original"
        assert clone.input_signals == original.input_signals
        assert len(clone.history) == 0  # Fresh history
