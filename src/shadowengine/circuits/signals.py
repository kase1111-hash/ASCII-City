"""
Signal system for behavioral circuits.

Signals are the communication mechanism between entities and the world.
Input signals trigger circuit evaluation, output signals affect the world.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class SignalType(Enum):
    """Types of signals that can be sent/received."""
    # Physical input signals
    PRESS = "press"
    KICK = "kick"
    PUSH = "push"
    PULL = "pull"
    POKE = "poke"
    THROW = "throw"
    CLIMB = "climb"

    # Sensory input signals
    LOOK = "look"
    LISTEN = "listen"
    SMELL = "smell"

    # Social input signals
    SAY = "say"
    SHOUT = "shout"
    WHISPER = "whisper"

    # Environmental input signals
    HEAT = "heat"
    COLD = "cold"
    WET = "wet"
    ELECTRIC = "electric"
    PROXIMITY = "proximity"
    TIME = "time"
    DAMAGE = "damage"

    # Output signals
    MOVE = "move"
    SOUND = "sound"
    CHANGE_STATE = "change_state"
    EMIT = "emit"
    TRIGGER = "trigger"
    COLLAPSE = "collapse"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    ALERT = "alert"
    FLEE = "flee"
    ATTACK = "attack"
    SPEAK = "speak"


class SignalStrength(Enum):
    """Strength/intensity of a signal."""
    MINIMAL = 0.1
    WEAK = 0.3
    NORMAL = 0.5
    STRONG = 0.7
    MAXIMUM = 1.0


@dataclass
class Signal:
    """Base signal class."""
    type: SignalType
    strength: float = 0.5          # 0.0 to 1.0
    source_id: Optional[str] = None  # ID of entity that created signal
    timestamp: float = field(default_factory=time.time)
    data: dict = field(default_factory=dict)  # Additional signal data

    def attenuate(self, factor: float) -> 'Signal':
        """Create a new signal with reduced strength."""
        return Signal(
            type=self.type,
            strength=self.strength * factor,
            source_id=self.source_id,
            timestamp=self.timestamp,
            data=self.data.copy()
        )

    def to_dict(self) -> dict:
        """Serialize signal to dictionary."""
        return {
            "type": self.type.value,
            "strength": self.strength,
            "source_id": self.source_id,
            "timestamp": self.timestamp,
            "data": self.data
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Signal':
        """Deserialize signal from dictionary."""
        return cls(
            type=SignalType(data["type"]),
            strength=data.get("strength", 0.5),
            source_id=data.get("source_id"),
            timestamp=data.get("timestamp", time.time()),
            data=data.get("data", {})
        )


@dataclass
class InputSignal(Signal):
    """Signal received by a circuit."""
    direction: Optional[tuple[float, float]] = None  # Source direction (x, y)
    distance: float = 0.0  # Distance from source

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        result = super().to_dict()
        result["direction"] = self.direction
        result["distance"] = self.distance
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'InputSignal':
        """Deserialize from dictionary."""
        return cls(
            type=SignalType(data["type"]),
            strength=data.get("strength", 0.5),
            source_id=data.get("source_id"),
            timestamp=data.get("timestamp", time.time()),
            data=data.get("data", {}),
            direction=tuple(data["direction"]) if data.get("direction") else None,
            distance=data.get("distance", 0.0)
        )


@dataclass
class OutputSignal(Signal):
    """Signal emitted by a circuit."""
    radius: float = 1.0            # How far the signal reaches
    propagates: bool = True        # Whether it propagates to adjacent tiles
    target_id: Optional[str] = None  # Specific target (if any)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        result = super().to_dict()
        result["radius"] = self.radius
        result["propagates"] = self.propagates
        result["target_id"] = self.target_id
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'OutputSignal':
        """Deserialize from dictionary."""
        return cls(
            type=SignalType(data["type"]),
            strength=data.get("strength", 0.5),
            source_id=data.get("source_id"),
            timestamp=data.get("timestamp", time.time()),
            data=data.get("data", {}),
            radius=data.get("radius", 1.0),
            propagates=data.get("propagates", True),
            target_id=data.get("target_id")
        )


# Common signal presets
def create_physical_signal(
    signal_type: SignalType,
    strength: float = 0.5,
    source_id: Optional[str] = None
) -> InputSignal:
    """Create a physical input signal."""
    return InputSignal(
        type=signal_type,
        strength=strength,
        source_id=source_id
    )


def create_sound_output(
    volume: float = 0.5,
    source_id: Optional[str] = None,
    sound_data: Optional[dict] = None
) -> OutputSignal:
    """Create a sound output signal."""
    return OutputSignal(
        type=SignalType.SOUND,
        strength=volume,
        source_id=source_id,
        radius=volume * 10,  # Louder = further
        propagates=True,
        data=sound_data or {}
    )


def create_movement_output(
    direction: tuple[float, float],
    speed: float = 1.0,
    source_id: Optional[str] = None
) -> OutputSignal:
    """Create a movement output signal."""
    return OutputSignal(
        type=SignalType.MOVE,
        strength=speed,
        source_id=source_id,
        propagates=False,
        data={"direction": direction, "speed": speed}
    )
