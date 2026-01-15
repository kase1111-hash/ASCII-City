"""
ShadowEngine - A Procedural ASCII Storytelling Game Engine

Memory-driven procedural storytelling with environmental simulation.
"""

__version__ = "0.1.0"

from .world_state import WorldState, StoryThread, GenerationMemory

__all__ = ["WorldState", "StoryThread", "GenerationMemory"]
