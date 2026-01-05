"""Tests for the signal system."""

import pytest
import time

from src.shadowengine.circuits.signals import (
    Signal,
    SignalType,
    SignalStrength,
    InputSignal,
    OutputSignal,
    create_physical_signal,
    create_sound_output,
    create_movement_output,
)


class TestSignalType:
    """Test SignalType enum."""

    def test_physical_signals_exist(self):
        """Test that physical signal types are defined."""
        assert SignalType.PRESS.value == "press"
        assert SignalType.KICK.value == "kick"
        assert SignalType.PUSH.value == "push"
        assert SignalType.PULL.value == "pull"
        assert SignalType.DAMAGE.value == "damage"

    def test_sensory_signals_exist(self):
        """Test that sensory signal types are defined."""
        assert SignalType.LOOK.value == "look"
        assert SignalType.LISTEN.value == "listen"
        assert SignalType.SMELL.value == "smell"

    def test_social_signals_exist(self):
        """Test that social signal types are defined."""
        assert SignalType.SAY.value == "say"
        assert SignalType.SHOUT.value == "shout"
        assert SignalType.WHISPER.value == "whisper"

    def test_output_signals_exist(self):
        """Test that output signal types are defined."""
        assert SignalType.SOUND.value == "sound"
        assert SignalType.MOVE.value == "move"
        assert SignalType.FLEE.value == "flee"
        assert SignalType.ATTACK.value == "attack"


class TestSignalStrength:
    """Test SignalStrength enum."""

    def test_predefined_strengths(self):
        """Test predefined strength values."""
        assert SignalStrength.MINIMAL.value == 0.1
        assert SignalStrength.WEAK.value == 0.3
        assert SignalStrength.NORMAL.value == 0.5
        assert SignalStrength.STRONG.value == 0.7
        assert SignalStrength.MAXIMUM.value == 1.0


class TestSignal:
    """Test base Signal dataclass."""

    def test_signal_creation(self):
        """Test creating a signal."""
        signal = Signal(
            type=SignalType.PRESS,
            strength=0.5,
            source_id="player"
        )
        assert signal.type == SignalType.PRESS
        assert signal.strength == 0.5
        assert signal.source_id == "player"

    def test_signal_with_data(self):
        """Test signal with custom data."""
        signal = Signal(
            type=SignalType.SAY,
            strength=0.5,
            source_id="npc_1",
            data={"message": "Hello there"}
        )
        assert signal.data["message"] == "Hello there"

    def test_signal_timestamp(self):
        """Test signal gets timestamp."""
        before = time.time()
        signal = Signal(type=SignalType.PRESS, strength=0.5, source_id="test")
        after = time.time()
        assert before <= signal.timestamp <= after

    def test_signal_serialization(self):
        """Test signal serialization."""
        signal = Signal(
            type=SignalType.KICK,
            strength=0.8,
            source_id="player",
            data={"force": "strong"}
        )
        data = signal.to_dict()
        assert data["type"] == "kick"
        assert data["strength"] == 0.8
        assert data["source_id"] == "player"
        assert data["data"]["force"] == "strong"

    def test_signal_deserialization(self):
        """Test signal deserialization."""
        data = {
            "type": "push",
            "strength": 0.6,
            "source_id": "npc",
            "data": {},
            "timestamp": time.time()
        }
        signal = Signal.from_dict(data)
        assert signal.type == SignalType.PUSH
        assert signal.strength == 0.6
        assert signal.source_id == "npc"

    def test_signal_attenuation(self):
        """Test signal attenuation."""
        signal = Signal(
            type=SignalType.SOUND,
            strength=1.0,
            source_id="bell"
        )
        attenuated = signal.attenuate(0.5)
        assert attenuated.strength == 0.5
        assert attenuated.type == signal.type


class TestInputSignal:
    """Test InputSignal dataclass."""

    def test_input_signal_creation(self):
        """Test creating an input signal."""
        signal = InputSignal(
            type=SignalType.LOOK,
            strength=0.5,
            source_id="player"
        )
        assert signal.type == SignalType.LOOK

    def test_input_signal_with_direction(self):
        """Test input signal with direction."""
        signal = InputSignal(
            type=SignalType.SOUND,
            strength=0.5,
            source_id="explosion",
            direction=(1.0, 0.0),
            distance=10.0
        )
        assert signal.direction == (1.0, 0.0)
        assert signal.distance == 10.0

    def test_input_signal_serialization(self):
        """Test input signal serialization."""
        signal = InputSignal(
            type=SignalType.PUSH,
            strength=0.7,
            source_id="player",
            direction=(0.5, 0.5),
            distance=2.0
        )
        data = signal.to_dict()
        assert data["direction"] == (0.5, 0.5)
        assert data["distance"] == 2.0


class TestOutputSignal:
    """Test OutputSignal dataclass."""

    def test_output_signal_creation(self):
        """Test creating an output signal."""
        signal = OutputSignal(
            type=SignalType.SOUND,
            strength=0.6,
            source_id="door"
        )
        assert signal.type == SignalType.SOUND

    def test_output_signal_with_radius(self):
        """Test output signal with propagation radius."""
        signal = OutputSignal(
            type=SignalType.SOUND,
            strength=0.8,
            source_id="explosion",
            radius=20.0
        )
        assert signal.radius == 20.0

    def test_output_signal_propagation(self):
        """Test output signal propagation setting."""
        signal = OutputSignal(
            type=SignalType.MOVE,
            strength=0.5,
            source_id="entity",
            propagates=False
        )
        assert signal.propagates is False

    def test_output_signal_target(self):
        """Test output signal with specific target."""
        signal = OutputSignal(
            type=SignalType.ATTACK,
            strength=0.8,
            source_id="guard",
            target_id="player"
        )
        assert signal.target_id == "player"


class TestSignalHelperFunctions:
    """Test signal creation helper functions."""

    def test_create_physical_signal(self):
        """Test creating physical input signals."""
        signal = create_physical_signal(
            signal_type=SignalType.KICK,
            strength=0.8,
            source_id="player"
        )
        assert signal.type == SignalType.KICK
        assert signal.strength == 0.8

    def test_create_physical_signal_default_strength(self):
        """Test physical signal with default strength."""
        signal = create_physical_signal(
            signal_type=SignalType.PUSH,
            source_id="player"
        )
        assert signal.strength == 0.5

    def test_create_sound_output(self):
        """Test creating sound output signal."""
        signal = create_sound_output(
            volume=0.7,
            source_id="bell",
            sound_data={"tone": "clear"}
        )
        assert signal.type == SignalType.SOUND
        assert signal.strength == 0.7
        assert signal.radius == 7.0  # volume * 10
        assert signal.data["tone"] == "clear"

    def test_create_movement_output(self):
        """Test creating movement output signal."""
        signal = create_movement_output(
            direction=(1.0, 0.0),
            speed=0.6,
            source_id="rat"
        )
        assert signal.type == SignalType.MOVE
        assert signal.data["direction"] == (1.0, 0.0)
        assert signal.data["speed"] == 0.6


class TestSignalComparison:
    """Test signal comparison and matching."""

    def test_signals_with_same_type(self):
        """Test comparing signals of the same type."""
        s1 = Signal(type=SignalType.PRESS, strength=0.5, source_id="a")
        s2 = Signal(type=SignalType.PRESS, strength=0.7, source_id="b")
        assert s1.type == s2.type

    def test_signals_with_different_type(self):
        """Test comparing signals of different types."""
        s1 = Signal(type=SignalType.PRESS, strength=0.5, source_id="a")
        s2 = Signal(type=SignalType.KICK, strength=0.5, source_id="a")
        assert s1.type != s2.type
