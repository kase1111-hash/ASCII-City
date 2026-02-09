"""
ShadowEngine - A Procedural ASCII Storytelling Game Engine

Memory-driven procedural storytelling with environmental simulation.
"""

import logging

__version__ = "0.1.0"

# Configure package-level logging (NullHandler by default; callers configure output)
logging.getLogger(__name__).addHandler(logging.NullHandler())

from .world_state import WorldState, StoryThread, GenerationMemory

__all__ = ["WorldState", "StoryThread", "GenerationMemory"]
