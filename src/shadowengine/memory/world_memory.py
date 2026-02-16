"""
World Memory - Objective truth of what happened.

This is the "god view" of events - what actually occurred regardless
of who witnessed it or what anyone believes.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class EventType(Enum):
    """Categories of events that can occur."""
    ACTION = "action"           # Someone did something
    DIALOGUE = "dialogue"       # Something was said
    DISCOVERY = "discovery"     # Something was found/revealed
    MOVEMENT = "movement"       # Someone moved locations
    WEATHER = "weather"         # Weather changed
    TIME = "time"               # Significant time passed
    DEATH = "death"             # Someone died
    EVIDENCE = "evidence"       # Evidence state changed


@dataclass
class Event:
    """A single objective event in world history."""

    event_type: EventType
    timestamp: int              # Game time units
    description: str            # What happened
    location: str               # Where it happened
    actors: list[str] = field(default_factory=list)      # Who was involved
    witnesses: list[str] = field(default_factory=list)   # Who saw it
    details: dict = field(default_factory=dict)          # Additional data
    id: str = ""                # Unique identifier

    def __post_init__(self):
        if not self.id:
            # Generate ID from timestamp and description hash
            self.id = f"evt_{self.timestamp}_{hash(self.description) % 10000:04d}"

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "description": self.description,
            "location": self.location,
            "actors": self.actors,
            "witnesses": self.witnesses,
            "details": self.details
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        """Deserialize from dictionary."""
        data = dict(data)  # Don't mutate the input dictionary
        data["event_type"] = EventType(data["event_type"])
        return cls(**data)


class WorldMemory:
    """
    The objective record of everything that has happened.

    This is the source of truth - hidden from the player but used
    to validate discoveries and resolve conflicts.
    """

    def __init__(self):
        self.events: list[Event] = []
        self.evidence_states: dict[str, dict] = {}  # evidence_id -> state
        self.location_states: dict[str, dict] = {}  # location_id -> state
        self.current_time: int = 0

    def record_event(self, event: Event) -> None:
        """Record an event in world history."""
        self.events.append(event)

    def record(
        self,
        event_type: EventType,
        description: str,
        location: str,
        actors: list[str] = None,
        witnesses: list[str] = None,
        details: dict = None
    ) -> Event:
        """Convenience method to create and record an event."""
        event = Event(
            event_type=event_type,
            timestamp=self.current_time,
            description=description,
            location=location,
            actors=actors or [],
            witnesses=witnesses or [],
            details=details or {}
        )
        self.record_event(event)
        return event

    def advance_time(self, units: int = 1) -> None:
        """Advance game time."""
        self.current_time += units

    def get_events_at_location(self, location: str) -> list[Event]:
        """Get all events that occurred at a location."""
        return [e for e in self.events if e.location == location]

    def get_events_involving(self, actor: str) -> list[Event]:
        """Get all events involving a specific actor."""
        return [e for e in self.events if actor in e.actors]

    def get_events_witnessed_by(self, witness: str) -> list[Event]:
        """Get all events witnessed by someone."""
        return [e for e in self.events if witness in e.witnesses]

    def get_events_since(self, timestamp: int) -> list[Event]:
        """Get all events since a given time."""
        return [e for e in self.events if e.timestamp >= timestamp]

    def get_events_by_type(self, event_type: EventType) -> list[Event]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.event_type == event_type]

    def set_evidence_state(self, evidence_id: str, state: dict) -> None:
        """Update the state of a piece of evidence."""
        self.evidence_states[evidence_id] = state

    def get_evidence_state(self, evidence_id: str) -> Optional[dict]:
        """Get the current state of evidence."""
        return self.evidence_states.get(evidence_id)

    def set_location_state(self, location_id: str, state: dict) -> None:
        """Update the state of a location."""
        self.location_states[location_id] = state

    def get_location_state(self, location_id: str) -> Optional[dict]:
        """Get the current state of a location."""
        return self.location_states.get(location_id)

    def to_dict(self) -> dict:
        """Serialize world memory."""
        return {
            "events": [e.to_dict() for e in self.events],
            "evidence_states": self.evidence_states,
            "location_states": self.location_states,
            "current_time": self.current_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'WorldMemory':
        """Deserialize world memory."""
        memory = cls()
        memory.events = [Event.from_dict(e) for e in data.get("events", [])]
        memory.evidence_states = data.get("evidence_states", {})
        memory.location_states = data.get("location_states", {})
        memory.current_time = data.get("current_time", 0)
        return memory
