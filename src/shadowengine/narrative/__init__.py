"""
Narrative Engine

Story structure generation and management.
"""

from .spine import (
    NarrativeSpine, ConflictType, SpineGenerator,
    TrueResolution, Revelation, RedHerring
)

__all__ = [
    'NarrativeSpine', 'ConflictType', 'SpineGenerator',
    'TrueResolution', 'Revelation', 'RedHerring'
]
