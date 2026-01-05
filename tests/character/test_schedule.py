"""
Tests for Character Schedule System.

These tests verify that the schedule system correctly:
- Tracks character locations based on time
- Handles schedule overrides
- Supports activity states
- Serializes/deserializes properly
"""

import pytest
from shadowengine.character import (
    Schedule, ScheduleEntry, ScheduleOverride, Activity,
    create_servant_schedule, create_guest_schedule
)


class TestScheduleEntry:
    """Schedule entry tests."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_create_entry(self):
        """Can create a schedule entry."""
        entry = ScheduleEntry(
            start_hour=8,
            end_hour=12,
            location_id="kitchen",
            activity=Activity.WORKING
        )

        assert entry.start_hour == 8
        assert entry.end_hour == 12
        assert entry.location_id == "kitchen"

    @pytest.mark.unit
    @pytest.mark.character
    def test_matches_time_normal(self):
        """Entry matches times in range."""
        entry = ScheduleEntry(8, 12, "kitchen")

        assert entry.matches_time(8) is True
        assert entry.matches_time(10) is True
        assert entry.matches_time(11) is True
        assert entry.matches_time(12) is False
        assert entry.matches_time(7) is False

    @pytest.mark.unit
    @pytest.mark.character
    def test_matches_time_overnight(self):
        """Entry handles overnight ranges."""
        entry = ScheduleEntry(22, 6, "bedroom")

        assert entry.matches_time(22) is True
        assert entry.matches_time(0) is True
        assert entry.matches_time(5) is True
        assert entry.matches_time(6) is False
        assert entry.matches_time(12) is False


class TestScheduleOverride:
    """Schedule override tests."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_create_override(self):
        """Can create an override."""
        override = ScheduleOverride(
            location_id="study",
            activity=Activity.HIDING,
            reason="Avoiding someone",
            duration_minutes=30
        )

        assert override.is_active() is True

    @pytest.mark.unit
    @pytest.mark.character
    def test_override_expires(self):
        """Override expires after duration."""
        override = ScheduleOverride(
            location_id="study",
            activity=Activity.HIDING,
            reason="Test",
            duration_minutes=30
        )

        override.update(15)
        assert override.is_active() is True

        override.update(20)
        assert override.is_active() is False

    @pytest.mark.unit
    @pytest.mark.character
    def test_update_returns_status(self):
        """Update returns whether still active."""
        override = ScheduleOverride(
            location_id="study",
            activity=Activity.HIDING,
            reason="Test",
            duration_minutes=30
        )

        assert override.update(10) is True
        assert override.update(25) is False


class TestSchedule:
    """Schedule functionality tests."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_create_schedule(self):
        """Can create a schedule."""
        schedule = Schedule(character_id="butler")

        assert schedule.character_id == "butler"
        assert len(schedule.entries) == 0

    @pytest.mark.unit
    @pytest.mark.character
    def test_add_entry(self):
        """Can add entries to schedule."""
        schedule = Schedule(character_id="butler")
        schedule.add_entry(8, 12, "kitchen", Activity.WORKING)

        assert len(schedule.entries) == 1
        assert schedule.entries[0].location_id == "kitchen"

    @pytest.mark.unit
    @pytest.mark.character
    def test_get_location(self):
        """Can get location for a given hour."""
        schedule = Schedule(character_id="butler", default_location="quarters")
        schedule.add_entry(8, 12, "kitchen", Activity.WORKING)
        schedule.add_entry(12, 14, "dining", Activity.EATING)

        assert schedule.get_location(10) == "kitchen"
        assert schedule.get_location(13) == "dining"
        assert schedule.get_location(20) == "quarters"  # Default

    @pytest.mark.unit
    @pytest.mark.character
    def test_get_activity(self):
        """Can get activity for a given hour."""
        schedule = Schedule(character_id="butler")
        schedule.add_entry(8, 12, "kitchen", Activity.WORKING)
        schedule.add_entry(22, 6, "quarters", Activity.SLEEPING)

        assert schedule.get_activity(10) == Activity.WORKING
        assert schedule.get_activity(2) == Activity.SLEEPING

    @pytest.mark.unit
    @pytest.mark.character
    def test_override_takes_precedence(self):
        """Override takes precedence over schedule."""
        schedule = Schedule(character_id="butler")
        schedule.add_entry(8, 12, "kitchen", Activity.WORKING)

        schedule.add_override("garden", Activity.HIDING, "Avoiding player")

        assert schedule.get_location(10) == "garden"
        assert schedule.get_activity(10) == Activity.HIDING

    @pytest.mark.unit
    @pytest.mark.character
    def test_override_priority(self):
        """Higher priority overrides take precedence."""
        schedule = Schedule(character_id="butler")

        schedule.add_override("garden", Activity.HIDING, "Low priority", priority=1)
        schedule.add_override("cellar", Activity.SEARCHING, "High priority", priority=5)

        assert schedule.get_location(10) == "cellar"

    @pytest.mark.unit
    @pytest.mark.character
    def test_update_clears_expired_overrides(self):
        """Update clears expired overrides."""
        schedule = Schedule(character_id="butler")
        schedule.add_entry(8, 12, "kitchen", Activity.WORKING)
        schedule.add_override("garden", Activity.HIDING, "Test", duration_minutes=20)

        schedule.update(10)
        assert schedule.get_location(10) == "garden"

        schedule.update(15)  # Total 25 minutes, override expired
        assert schedule.get_location(10) == "kitchen"

    @pytest.mark.unit
    @pytest.mark.character
    def test_is_interruptible(self):
        """Interruptible flag works."""
        schedule = Schedule(character_id="butler")
        schedule.add_entry(22, 6, "quarters", Activity.SLEEPING, interruptible=False)
        schedule.add_entry(8, 12, "kitchen", Activity.WORKING, interruptible=True)

        assert schedule.is_interruptible(10) is True
        assert schedule.is_interruptible(2) is False


class TestScheduleFactories:
    """Schedule factory function tests."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_create_servant_schedule(self):
        """Servant schedule factory works."""
        schedule = create_servant_schedule(
            "butler",
            quarters="servants_quarters",
            work_location="kitchen"
        )

        assert schedule.character_id == "butler"
        assert len(schedule.entries) > 0

        # Check work hours
        assert schedule.get_location(10) == "kitchen"

        # Check night hours
        assert schedule.get_location(2) == "servants_quarters"

    @pytest.mark.unit
    @pytest.mark.character
    def test_create_guest_schedule(self):
        """Guest schedule factory works."""
        schedule = create_guest_schedule(
            "guest1",
            room="guest_room",
            common_areas=["parlor", "dining_room"]
        )

        assert schedule.character_id == "guest1"
        assert len(schedule.entries) > 0

        # Check night hours - in room
        assert schedule.get_location(2) == "guest_room"


class TestScheduleSerialization:
    """Schedule serialization tests."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_serialize_schedule(self):
        """Can serialize schedule."""
        schedule = Schedule(character_id="butler", default_location="quarters")
        schedule.add_entry(8, 12, "kitchen", Activity.WORKING, "Morning duties")

        data = schedule.to_dict()

        assert data["character_id"] == "butler"
        assert len(data["entries"]) == 1
        assert data["entries"][0]["activity"] == "WORKING"

    @pytest.mark.unit
    @pytest.mark.character
    def test_deserialize_schedule(self):
        """Can deserialize schedule."""
        schedule = Schedule(character_id="butler", default_location="quarters")
        schedule.add_entry(8, 12, "kitchen", Activity.WORKING)
        schedule.add_override("garden", Activity.HIDING, "Test", 30)

        data = schedule.to_dict()
        restored = Schedule.from_dict(data)

        assert restored.character_id == "butler"
        assert len(restored.entries) == 1
        assert len(restored.overrides) == 1

    @pytest.mark.unit
    @pytest.mark.character
    def test_roundtrip_preserves_state(self):
        """Roundtrip preserves all state."""
        schedule = Schedule(
            character_id="maid",
            default_location="quarters",
            default_activity=Activity.IDLE
        )
        schedule.add_entry(8, 12, "kitchen", Activity.WORKING, "Cooking", False)
        schedule.add_override(
            "cellar", Activity.SEARCHING, "Looking for something",
            duration_minutes=45, priority=3
        )
        schedule.overrides[0].elapsed_minutes = 15

        data = schedule.to_dict()
        restored = Schedule.from_dict(data)

        assert restored.default_activity == Activity.IDLE
        assert restored.entries[0].interruptible is False
        assert restored.overrides[0].elapsed_minutes == 15
        assert restored.overrides[0].priority == 3
