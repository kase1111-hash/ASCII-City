"""
Behavioral Circuits - Universal entity interaction model.

Every interactive entity in the world uses this unified structure,
enabling consistent evaluation and emergent behavior.
"""

from .circuit import (
    BehaviorCircuit,
    CircuitType,
    CircuitState,
)
from .signals import (
    Signal,
    SignalType,
    InputSignal,
    OutputSignal,
    SignalStrength,
)
from .types import (
    MechanicalCircuit,
    BiologicalCircuit,
    EnvironmentalCircuit,
)
from .affordances import (
    Affordance,
    AffordanceSet,
    DEFAULT_AFFORDANCES,
)
from .processor import (
    CircuitProcessor,
    ProcessingContext,
    ProcessingResult,
)

__all__ = [
    # Core
    'BehaviorCircuit',
    'CircuitType',
    'CircuitState',
    # Signals
    'Signal',
    'SignalType',
    'InputSignal',
    'OutputSignal',
    'SignalStrength',
    # Types
    'MechanicalCircuit',
    'BiologicalCircuit',
    'EnvironmentalCircuit',
    # Affordances
    'Affordance',
    'AffordanceSet',
    'DEFAULT_AFFORDANCES',
    # Processing
    'CircuitProcessor',
    'ProcessingContext',
    'ProcessingResult',
]
