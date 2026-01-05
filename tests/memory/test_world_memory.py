"""
Tests for World Memory - the objective truth layer.

These tests verify that world memory correctly:
- Records events with all metadata
- Tracks time progression
- Queries events by various criteria
- Serializes/deserializes correctly
"""

import pytest
from shadowengine.memory import WorldMemory, Event, EventType


class TestWorldMemoryBasics:
    """Basic world memory functionality."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_create_empty_world_memory(self, world_memory):
        """World memory starts empty."""
        assert len(world_memory.events) == 0
        assert world_memory.current_time == 0

    @pytest.mark.unit
    @pytest.mark.memory
    def test_record_event(self, world_memory):
        """Can record a basic event."""
        event = world_memory.record(
            event_type=EventType.ACTION,
            description="Something happened",
            location="test_location"
        )

        assert len(world_memory.events) == 1
        assert event.description == "Something happened"
        assert event.location == "test_location"
        assert event.timestamp == 0

    @pytest.mark.unit
    @pytest.mark.memory
    def test_record_event_with_actors_and_witnesses(self, world_memory):
        """Events can have actors and witnesses."""
        event = world_memory.record(
            event_type=EventType.ACTION,
            description="Alice talked to Bob",
            location="study",
            actors=["alice"],
            witnesses=["bob", "charlie"]
        )

        assert "alice" in event.actors
        assert "bob" in event.witnesses
        assert "charlie" in event.witnesses

    @pytest.mark.unit
    @pytest.mark.memory
    def test_time_advances(self, world_memory):
        """Time advances correctly."""
        assert world_memory.current_time == 0

        world_memory.advance_time(5)
        assert world_memory.current_time == 5

        world_memory.advance_time(3)
        assert world_memory.current_time == 8

    @pytest.mark.unit
    @pytest.mark.memory
    def test_event_timestamps(self, world_memory):
        """Events get correct timestamps."""
        world_memory.record(
            event_type=EventType.ACTION,
            description="First event",
            location="test"
        )

        world_memory.advance_time(10)

        world_memory.record(
            event_type=EventType.ACTION,
            description="Second event",
            location="test"
        )

        assert world_memory.events[0].timestamp == 0
        assert world_memory.events[1].timestamp == 10


class TestWorldMemoryQueries:
    """Query functionality for world memory."""

    @pytest.fixture
    def populated_world(self, world_memory):
        """World memory with multiple events."""
        world_memory.record(
            event_type=EventType.ACTION,
            description="Event in study",
            location="study",
            actors=["alice"],
            witnesses=["bob"]
        )
        world_memory.advance_time(5)

        world_memory.record(
            event_type=EventType.DIALOGUE,
            description="Conversation in hallway",
            location="hallway",
            actors=["bob", "charlie"],
            witnesses=["alice"]
        )
        world_memory.advance_time(5)

        world_memory.record(
            event_type=EventType.DISCOVERY,
            description="Found clue in study",
            location="study",
            actors=["alice"]
        )

        return world_memory

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_events_at_location(self, populated_world):
        """Can query events by location."""
        study_events = populated_world.get_events_at_location("study")
        assert len(study_events) == 2

        hallway_events = populated_world.get_events_at_location("hallway")
        assert len(hallway_events) == 1

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_events_involving_actor(self, populated_world):
        """Can query events by actor."""
        alice_events = populated_world.get_events_involving("alice")
        assert len(alice_events) == 2

        bob_events = populated_world.get_events_involving("bob")
        assert len(bob_events) == 1

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_events_witnessed_by(self, populated_world):
        """Can query events by witness."""
        bob_witnessed = populated_world.get_events_witnessed_by("bob")
        assert len(bob_witnessed) == 1
        assert bob_witnessed[0].location == "study"

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_events_since_time(self, populated_world):
        """Can query events since a timestamp."""
        recent_events = populated_world.get_events_since(5)
        assert len(recent_events) == 2

        very_recent = populated_world.get_events_since(10)
        assert len(very_recent) == 1

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_events_by_type(self, populated_world):
        """Can query events by type."""
        actions = populated_world.get_events_by_type(EventType.ACTION)
        assert len(actions) == 1

        discoveries = populated_world.get_events_by_type(EventType.DISCOVERY)
        assert len(discoveries) == 1


class TestWorldMemoryEvidence:
    """Evidence and location state tracking."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_evidence_state_tracking(self, world_memory):
        """Can track evidence state."""
        world_memory.set_evidence_state("knife", {
            "location": "study",
            "condition": "clean",
            "discovered": False
        })

        state = world_memory.get_evidence_state("knife")
        assert state["location"] == "study"
        assert state["condition"] == "clean"
        assert state["discovered"] is False

    @pytest.mark.unit
    @pytest.mark.memory
    def test_location_state_tracking(self, world_memory):
        """Can track location state."""
        world_memory.set_location_state("study", {
            "lights": "on",
            "door": "locked",
            "searched": False
        })

        state = world_memory.get_location_state("study")
        assert state["lights"] == "on"
        assert state["door"] == "locked"

    @pytest.mark.unit
    @pytest.mark.memory
    def test_missing_state_returns_none(self, world_memory):
        """Querying non-existent state returns None."""
        assert world_memory.get_evidence_state("nonexistent") is None
        assert world_memory.get_location_state("nonexistent") is None


class TestWorldMemorySerialization:
    """Serialization and deserialization."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_serialize_empty_memory(self, world_memory):
        """Can serialize empty world memory."""
        data = world_memory.to_dict()

        assert "events" in data
        assert "evidence_states" in data
        assert "location_states" in data
        assert "current_time" in data
        assert len(data["events"]) == 0

    @pytest.mark.unit
    @pytest.mark.memory
    def test_serialize_populated_memory(self, world_memory):
        """Can serialize world memory with content."""
        world_memory.record(
            event_type=EventType.ACTION,
            description="Test event",
            location="test"
        )
        world_memory.set_evidence_state("item", {"found": True})
        world_memory.advance_time(10)

        data = world_memory.to_dict()

        assert len(data["events"]) == 1
        assert data["current_time"] == 10
        assert "item" in data["evidence_states"]

    @pytest.mark.unit
    @pytest.mark.memory
    def test_deserialize_memory(self, world_memory):
        """Can deserialize world memory."""
        world_memory.record(
            event_type=EventType.DISCOVERY,
            description="Found something",
            location="study"
        )
        world_memory.advance_time(25)

        data = world_memory.to_dict()
        restored = WorldMemory.from_dict(data)

        assert len(restored.events) == 1
        assert restored.events[0].event_type == EventType.DISCOVERY
        assert restored.current_time == 25

    @pytest.mark.unit
    @pytest.mark.memory
    def test_roundtrip_serialization(self, world_memory):
        """Serialization roundtrip preserves all data."""
        # Add complex data
        world_memory.record(
            event_type=EventType.DEATH,
            description="Someone died",
            location="library",
            actors=["victim"],
            witnesses=["witness1", "witness2"],
            details={"weapon": "candlestick", "time": "midnight"}
        )
        world_memory.set_evidence_state("candlestick", {"bloody": True})
        world_memory.set_location_state("library", {"crime_scene": True})
        world_memory.advance_time(100)

        # Roundtrip
        data = world_memory.to_dict()
        restored = WorldMemory.from_dict(data)

        # Verify
        assert len(restored.events) == 1
        event = restored.events[0]
        assert event.event_type == EventType.DEATH
        assert event.details["weapon"] == "candlestick"
        assert restored.evidence_states["candlestick"]["bloody"] is True
        assert restored.current_time == 100
