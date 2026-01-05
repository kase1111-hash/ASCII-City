"""
Tests for Time System - Day/night cycle and time progression.

These tests verify that the time system correctly:
- Tracks time in periods (dawn, morning, afternoon, evening, night)
- Advances time and triggers events
- Provides visibility modifiers
- Serializes/deserializes state
"""

import pytest
from shadowengine.environment import TimeSystem, TimePeriod, TimeEvent


class TestTimePeriod:
    """Time period enum tests."""

    @pytest.mark.unit
    @pytest.mark.environment
    def test_from_hour_dawn(self):
        """Dawn is 5-7."""
        assert TimePeriod.from_hour(5) == TimePeriod.DAWN
        assert TimePeriod.from_hour(6) == TimePeriod.DAWN
        assert TimePeriod.from_hour(7) == TimePeriod.DAWN

    @pytest.mark.unit
    @pytest.mark.environment
    def test_from_hour_morning(self):
        """Morning is 8-11."""
        assert TimePeriod.from_hour(8) == TimePeriod.MORNING
        assert TimePeriod.from_hour(11) == TimePeriod.MORNING

    @pytest.mark.unit
    @pytest.mark.environment
    def test_from_hour_afternoon(self):
        """Afternoon is 12-16."""
        assert TimePeriod.from_hour(12) == TimePeriod.AFTERNOON
        assert TimePeriod.from_hour(16) == TimePeriod.AFTERNOON

    @pytest.mark.unit
    @pytest.mark.environment
    def test_from_hour_evening(self):
        """Evening is 17-20."""
        assert TimePeriod.from_hour(17) == TimePeriod.EVENING
        assert TimePeriod.from_hour(20) == TimePeriod.EVENING

    @pytest.mark.unit
    @pytest.mark.environment
    def test_from_hour_night(self):
        """Night is 21-4."""
        assert TimePeriod.from_hour(21) == TimePeriod.NIGHT
        assert TimePeriod.from_hour(0) == TimePeriod.NIGHT
        assert TimePeriod.from_hour(4) == TimePeriod.NIGHT

    @pytest.mark.unit
    @pytest.mark.environment
    def test_period_has_description(self):
        """Each period has a description."""
        for period in TimePeriod:
            desc = period.get_description()
            assert len(desc) > 0

    @pytest.mark.unit
    @pytest.mark.environment
    def test_visibility_modifiers(self):
        """Periods have appropriate visibility modifiers."""
        # Daytime periods should have full visibility
        assert TimePeriod.MORNING.get_visibility_modifier() == 1.0
        assert TimePeriod.AFTERNOON.get_visibility_modifier() == 1.0

        # Night should have reduced visibility
        assert TimePeriod.NIGHT.get_visibility_modifier() < 1.0

        # Dawn/evening are in between
        assert TimePeriod.DAWN.get_visibility_modifier() < 1.0
        assert TimePeriod.EVENING.get_visibility_modifier() < 1.0


class TestTimeSystem:
    """Time system functionality tests."""

    @pytest.mark.unit
    @pytest.mark.environment
    def test_create_time_system(self):
        """Can create a time system."""
        ts = TimeSystem()
        assert ts.current_minutes >= 0
        assert ts.current_period is not None

    @pytest.mark.unit
    @pytest.mark.environment
    def test_default_start_time(self):
        """Default start is 8:00 AM."""
        ts = TimeSystem()
        assert ts.hour == 8
        assert ts.minute == 0
        assert ts.current_period == TimePeriod.MORNING

    @pytest.mark.unit
    @pytest.mark.environment
    def test_set_time(self):
        """Can set specific time."""
        ts = TimeSystem()
        ts.set_time(14, 30)

        assert ts.hour == 14
        assert ts.minute == 30
        assert ts.current_period == TimePeriod.AFTERNOON

    @pytest.mark.unit
    @pytest.mark.environment
    def test_advance_time(self):
        """Can advance time."""
        ts = TimeSystem()
        ts.set_time(8, 0)

        ts.advance(30)

        assert ts.hour == 8
        assert ts.minute == 30

    @pytest.mark.unit
    @pytest.mark.environment
    def test_advance_crosses_hour(self):
        """Time advancement crosses hour boundary."""
        ts = TimeSystem()
        ts.set_time(8, 45)

        ts.advance(30)

        assert ts.hour == 9
        assert ts.minute == 15

    @pytest.mark.unit
    @pytest.mark.environment
    def test_advance_crosses_midnight(self):
        """Time advancement crosses midnight."""
        ts = TimeSystem()
        ts.set_time(23, 30)

        ts.advance(60)

        assert ts.hour == 0
        assert ts.minute == 30
        assert ts.day_number == 2

    @pytest.mark.unit
    @pytest.mark.environment
    def test_day_number(self):
        """Day number increments correctly."""
        ts = TimeSystem()
        ts.set_time(8, 0, day=1)
        assert ts.day_number == 1

        ts.set_time(8, 0, day=3)
        assert ts.day_number == 3

    @pytest.mark.unit
    @pytest.mark.environment
    def test_get_time_string(self):
        """Time string is formatted correctly."""
        ts = TimeSystem()
        ts.set_time(9, 5)

        assert ts.get_time_string() == "09:05"

    @pytest.mark.unit
    @pytest.mark.environment
    def test_get_display_string(self):
        """Display string includes period."""
        ts = TimeSystem()
        ts.set_time(14, 0)

        display = ts.get_display_string()
        assert "14:00" in display
        assert "Afternoon" in display

    @pytest.mark.unit
    @pytest.mark.environment
    def test_is_dark(self):
        """is_dark returns True for night/dawn."""
        ts = TimeSystem()

        ts.set_time(2, 0)  # Night
        assert ts.is_dark() is True

        ts.set_time(6, 0)  # Dawn
        assert ts.is_dark() is True

        ts.set_time(12, 0)  # Afternoon
        assert ts.is_dark() is False


class TestTimeEvents:
    """Time event functionality tests."""

    @pytest.mark.unit
    @pytest.mark.environment
    def test_create_event(self):
        """Can create a time event."""
        event = TimeEvent(
            id="test_event",
            trigger_hour=12,
            trigger_minute=30,
            description="Test event"
        )

        assert event.id == "test_event"
        assert event.trigger_hour == 12
        assert not event.triggered

    @pytest.mark.unit
    @pytest.mark.environment
    def test_event_triggers(self):
        """Events trigger at correct time."""
        callback_called = []

        def on_trigger():
            callback_called.append(True)

        ts = TimeSystem()
        ts.set_time(11, 55)

        event = TimeEvent(
            id="lunch",
            trigger_hour=12,
            trigger_minute=0,
            callback=on_trigger
        )
        ts.add_event(event)

        # Advance to trigger time
        triggered = ts.advance(10)

        assert len(triggered) == 1
        assert triggered[0].id == "lunch"
        assert len(callback_called) == 1

    @pytest.mark.unit
    @pytest.mark.environment
    def test_event_only_triggers_once(self):
        """Non-repeating events only trigger once."""
        ts = TimeSystem()
        ts.set_time(11, 58)

        event = TimeEvent(
            id="once",
            trigger_hour=12,
            trigger_minute=0,
            repeating=False
        )
        ts.add_event(event)

        # First advancement triggers
        triggered1 = ts.advance(5)
        assert len(triggered1) == 1

        # Second advancement doesn't re-trigger
        ts.set_time(11, 58)
        triggered2 = ts.advance(5)
        assert len(triggered2) == 0

    @pytest.mark.unit
    @pytest.mark.environment
    def test_remove_event(self):
        """Can remove an event."""
        ts = TimeSystem()
        event = TimeEvent(id="removable", trigger_hour=12)
        ts.add_event(event)

        assert len(ts.events) == 1

        result = ts.remove_event("removable")
        assert result is True
        assert len(ts.events) == 0

    @pytest.mark.unit
    @pytest.mark.environment
    def test_advance_to_time(self):
        """Can advance to specific time."""
        ts = TimeSystem()
        ts.set_time(8, 0)

        ts.advance_to(14, 30)

        assert ts.hour == 14
        assert ts.minute == 30

    @pytest.mark.unit
    @pytest.mark.environment
    def test_advance_to_next_day(self):
        """Advancing to earlier time goes to next day."""
        ts = TimeSystem()
        ts.set_time(20, 0, day=1)

        ts.advance_to(8, 0)

        assert ts.hour == 8
        assert ts.day_number == 2

    @pytest.mark.unit
    @pytest.mark.environment
    def test_advance_to_period(self):
        """Can advance to start of period."""
        ts = TimeSystem()
        ts.set_time(8, 0)

        ts.advance_to_period(TimePeriod.EVENING)

        assert ts.current_period == TimePeriod.EVENING
        assert ts.hour == 17


class TestTimePeriodCallbacks:
    """Period change callback tests."""

    @pytest.mark.unit
    @pytest.mark.environment
    def test_period_change_callback(self):
        """Callbacks fire on period change."""
        changes = []

        def on_change(old_period, new_period):
            changes.append((old_period, new_period))

        ts = TimeSystem()
        ts.set_time(11, 55)
        ts.on_period_change(on_change)

        # Advance to afternoon
        ts.advance(10)

        assert len(changes) == 1
        assert changes[0] == (TimePeriod.MORNING, TimePeriod.AFTERNOON)

    @pytest.mark.unit
    @pytest.mark.environment
    def test_period_history(self):
        """Period changes are recorded in history."""
        ts = TimeSystem()
        ts.set_time(11, 55)

        # Advance through multiple periods
        ts.advance_to(18, 0)

        # Should have recorded the changes
        assert len(ts.period_history) >= 2


class TestTimeSerialization:
    """Time system serialization tests."""

    @pytest.mark.unit
    @pytest.mark.environment
    def test_serialize_time(self):
        """Can serialize time state."""
        ts = TimeSystem()
        ts.set_time(14, 30)
        ts.add_event(TimeEvent(id="test", trigger_hour=18))

        data = ts.to_dict()

        assert data["current_minutes"] == 14 * 60 + 30
        assert len(data["events"]) == 1

    @pytest.mark.unit
    @pytest.mark.environment
    def test_deserialize_time(self):
        """Can deserialize time state."""
        ts = TimeSystem()
        ts.set_time(14, 30)
        ts.add_event(TimeEvent(
            id="dinner",
            trigger_hour=18,
            description="Dinner time"
        ))

        data = ts.to_dict()
        restored = TimeSystem.from_dict(data)

        assert restored.hour == 14
        assert restored.minute == 30
        assert len(restored.events) == 1
        assert restored.events[0].id == "dinner"

    @pytest.mark.unit
    @pytest.mark.environment
    def test_roundtrip_preserves_state(self):
        """Roundtrip preserves all state."""
        ts = TimeSystem(time_scale=2.0)
        ts.set_time(22, 15, day=3)
        ts.add_event(TimeEvent(
            id="event1",
            trigger_hour=8,
            repeating=True,
            triggered=True
        ))

        data = ts.to_dict()
        restored = TimeSystem.from_dict(data)

        assert restored.time_scale == 2.0
        assert restored.day_number == 3
        assert restored.events[0].repeating is True
