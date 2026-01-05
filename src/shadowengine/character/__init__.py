"""
Character Simulation Engine

Autonomous NPCs with psychology, secrets, and memory-driven behavior.
"""

from .character import Character, CharacterState, Archetype, Mood, Motivations
from .dialogue import DialogueManager, DialogueTopic, DialogueResponse
from .schedule import (
    Schedule, ScheduleEntry, ScheduleOverride, Activity,
    create_servant_schedule, create_guest_schedule
)
from .relationships import (
    RelationshipManager, Relationship, RelationType, NPCInteractionResult
)

__all__ = [
    # Character core
    'Character', 'CharacterState', 'Archetype', 'Mood', 'Motivations',
    # Dialogue
    'DialogueManager', 'DialogueTopic', 'DialogueResponse',
    # Schedule
    'Schedule', 'ScheduleEntry', 'ScheduleOverride', 'Activity',
    'create_servant_schedule', 'create_guest_schedule',
    # Relationships
    'RelationshipManager', 'Relationship', 'RelationType', 'NPCInteractionResult',
]
