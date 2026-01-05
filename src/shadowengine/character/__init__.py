"""
Character Simulation Engine

Autonomous NPCs with psychology, secrets, and memory-driven behavior.
"""

from .character import Character, CharacterState, Archetype
from .dialogue import DialogueManager, DialogueTopic, DialogueResponse

__all__ = [
    'Character', 'CharacterState', 'Archetype',
    'DialogueManager', 'DialogueTopic', 'DialogueResponse'
]
