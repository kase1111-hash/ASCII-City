"""
Core BehaviorCircuit class - the universal entity interaction model.

Every interactive entity uses this structure, enabling consistent
evaluation and emergent behavior.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Any
import time
import json

from .signals import Signal, SignalType, InputSignal, OutputSignal


class CircuitType(Enum):
    """Types of behavioral circuits."""
    MECHANICAL = "mechanical"      # Objects with physical mechanisms
    BIOLOGICAL = "biological"      # Living entities with psychology
    ENVIRONMENTAL = "environmental"  # Natural phenomena and terrain


@dataclass
class CircuitState:
    """Persistent state for a behavioral circuit."""
    health: float = 1.0            # 0.0 to 1.0
    power: float = 1.0             # Energy/charge level
    fatigue: float = 0.0           # Wear/tiredness (0.0 to 1.0)
    trust: float = 0.5             # For biological circuits
    age: float = 0.0               # Time since creation
    active: bool = True            # Whether circuit is operational
    last_interaction: float = field(default_factory=time.time)
    custom: dict = field(default_factory=dict)  # Entity-specific state

    def update_age(self, delta: float) -> None:
        """Update age by delta seconds."""
        self.age += delta

    def apply_damage(self, amount: float) -> bool:
        """Apply damage, return True if circuit is destroyed."""
        self.health = max(0.0, self.health - amount)
        return self.health <= 0.0

    def apply_fatigue(self, amount: float) -> None:
        """Apply fatigue."""
        self.fatigue = min(1.0, self.fatigue + amount)

    def recover(self, amount: float) -> None:
        """Recover from fatigue."""
        self.fatigue = max(0.0, self.fatigue - amount)

    def modify_trust(self, delta: float) -> None:
        """Modify trust level."""
        self.trust = max(0.0, min(1.0, self.trust + delta))

    def to_dict(self) -> dict:
        """Serialize state to dictionary."""
        return {
            "health": self.health,
            "power": self.power,
            "fatigue": self.fatigue,
            "trust": self.trust,
            "age": self.age,
            "active": self.active,
            "last_interaction": self.last_interaction,
            "custom": self.custom
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CircuitState':
        """Deserialize state from dictionary."""
        return cls(
            health=data.get("health", 1.0),
            power=data.get("power", 1.0),
            fatigue=data.get("fatigue", 0.0),
            trust=data.get("trust", 0.5),
            age=data.get("age", 0.0),
            active=data.get("active", True),
            last_interaction=data.get("last_interaction", time.time()),
            custom=data.get("custom", {})
        )


@dataclass
class BehaviorCircuit:
    """
    Universal behavioral circuit for all interactive entities.

    This is the core model that enables emergent behavior through
    consistent input/output signal processing.
    """
    id: str
    name: str
    circuit_type: CircuitType
    description: str = ""

    # What signals this circuit responds to
    input_signals: list[SignalType] = field(default_factory=list)

    # What signals this circuit can produce
    output_signals: list[SignalType] = field(default_factory=list)

    # Current state
    state: CircuitState = field(default_factory=CircuitState)

    # What can be done to/with this entity
    affordances: list[str] = field(default_factory=list)

    # Interaction history (limited)
    history: list[dict] = field(default_factory=list)
    max_history: int = 100

    # Processing callback (for custom logic)
    _processor: Optional[Callable] = field(default=None, repr=False)

    def responds_to(self, signal_type: SignalType) -> bool:
        """Check if this circuit responds to a signal type."""
        return signal_type in self.input_signals

    def can_emit(self, signal_type: SignalType) -> bool:
        """Check if this circuit can emit a signal type."""
        return signal_type in self.output_signals

    def has_affordance(self, affordance: str) -> bool:
        """Check if this circuit has an affordance."""
        return affordance in self.affordances

    def receive_signal(self, signal: InputSignal) -> list[OutputSignal]:
        """
        Process an incoming signal and return output signals.

        This is the core processing method that drives emergent behavior.
        """
        if not self.state.active:
            return []

        if not self.responds_to(signal.type):
            return []

        # Record interaction
        self._record_interaction(signal)

        # Update state
        self.state.last_interaction = time.time()

        # Process through custom processor if available
        if self._processor:
            return self._processor(self, signal)

        # Default processing based on circuit type
        return self._default_process(signal)

    def _default_process(self, signal: InputSignal) -> list[OutputSignal]:
        """Default signal processing based on circuit type."""
        outputs = []

        # Physical signals can cause state changes
        if signal.type in (SignalType.KICK, SignalType.PUSH, SignalType.DAMAGE):
            # Strong signals cause damage
            if signal.strength > 0.7:
                damaged = self.state.apply_damage(signal.strength * 0.2)
                if damaged:
                    outputs.append(OutputSignal(
                        type=SignalType.COLLAPSE,
                        strength=1.0,
                        source_id=self.id
                    ))

            # Generate sound on impact
            outputs.append(OutputSignal(
                type=SignalType.SOUND,
                strength=signal.strength * 0.5,
                source_id=self.id,
                radius=signal.strength * 5
            ))

        # Activation signals
        if signal.type == SignalType.PRESS:
            if SignalType.ACTIVATE in self.output_signals:
                outputs.append(OutputSignal(
                    type=SignalType.ACTIVATE,
                    strength=signal.strength,
                    source_id=self.id
                ))

        return outputs

    def _record_interaction(self, signal: InputSignal) -> None:
        """Record an interaction in history."""
        record = {
            "timestamp": time.time(),
            "signal_type": signal.type.value,
            "strength": signal.strength,
            "source_id": signal.source_id
        }
        self.history.append(record)

        # Trim history if too long
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_recent_history(self, count: int = 10) -> list[dict]:
        """Get recent interaction history."""
        return self.history[-count:]

    def update(self, delta_time: float) -> list[OutputSignal]:
        """
        Update circuit state over time.

        Returns any output signals generated during update.
        """
        if not self.state.active:
            return []

        self.state.update_age(delta_time)

        # Gradual recovery from fatigue
        if self.state.fatigue > 0:
            self.state.recover(delta_time * 0.01)

        return []

    def set_processor(self, processor: Callable) -> None:
        """Set custom signal processor."""
        self._processor = processor

    def to_dict(self) -> dict:
        """Serialize circuit to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "circuit_type": self.circuit_type.value,
            "description": self.description,
            "input_signals": [s.value for s in self.input_signals],
            "output_signals": [s.value for s in self.output_signals],
            "state": self.state.to_dict(),
            "affordances": self.affordances,
            "history": self.history[-self.max_history:]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BehaviorCircuit':
        """Deserialize circuit from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            circuit_type=CircuitType(data["circuit_type"]),
            description=data.get("description", ""),
            input_signals=[SignalType(s) for s in data.get("input_signals", [])],
            output_signals=[SignalType(s) for s in data.get("output_signals", [])],
            state=CircuitState.from_dict(data.get("state", {})),
            affordances=data.get("affordances", []),
            history=data.get("history", [])
        )

    def clone(self, new_id: str) -> 'BehaviorCircuit':
        """Create a copy of this circuit with a new ID."""
        data = self.to_dict()
        data["id"] = new_id
        data["history"] = []  # Fresh history for clone
        cloned = self.from_dict(data)
        cloned._processor = self._processor
        return cloned
