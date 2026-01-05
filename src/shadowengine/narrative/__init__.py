"""
Narrative Engine

Story structure generation and management.
"""

from .spine import (
    NarrativeSpine, ConflictType, SpineGenerator,
    TrueResolution, Revelation, RedHerring
)
from .shades import (
    MoralShade, MoralDecision, ShadeProfile,
    ShadeNarrator, NarrationStyle, Ending, EndingDeterminator,
    DECISION_TEMPLATES, SHADE_STYLES, ENDINGS
)
from .twists import (
    TwistType, TwistCondition, Twist,
    TwistManager, TwistGenerator
)

__all__ = [
    # Spine
    'NarrativeSpine', 'ConflictType', 'SpineGenerator',
    'TrueResolution', 'Revelation', 'RedHerring',
    # Shades
    'MoralShade', 'MoralDecision', 'ShadeProfile',
    'ShadeNarrator', 'NarrationStyle', 'Ending', 'EndingDeterminator',
    'DECISION_TEMPLATES', 'SHADE_STYLES', 'ENDINGS',
    # Twists
    'TwistType', 'TwistCondition', 'Twist',
    'TwistManager', 'TwistGenerator'
]
