"""
Tests for Environment System - Combined time and weather.

These tests verify that the environment coordinator correctly:
- Synchronizes time and weather systems
- Manages location-specific environments
- Provides unified visibility and atmosphere
- Serializes/deserializes state
"""

import pytest
from shadowengine.environment import (
    Environment, LocationEnvironment,
    TimeSystem, TimePeriod,
    WeatherSystem, WeatherType
)


class TestLocationEnvironment:
    """Location environment tests."""

    @pytest.mark.unit
    @pytest.mark.environment
    def test_create_location_environment(self):
        """Can create location environment."""
        env = LocationEnvironment(
            location_id="study",
            is_indoor=True
        )

        assert env.location_id == "study"
        assert env.is_indoor is True

    @pytest.mark.unit
    @pytest.mark.environment
    def test_indoor_has_shelter(self):
        """Indoor locations have shelter by default."""
        env = LocationEnvironment(location_id="room", is_indoor=True)

        assert env.has_shelter is True

    @pytest.mark.unit
    @pytest.mark.environment
    def test_visibility_with_lighting(self):
        """Lit rooms have good visibility at night."""
        time = TimeSystem()
        time.set_time(23, 0)  # Night

        weather = WeatherSystem()

        env = LocationEnvironment(
            location_id="lit_room",
            is_indoor=True,
            has_lighting=True
        )

        vis = env.get_visibility(time, weather)
        assert vis >= 0.8  # Still good visibility

    @pytest.mark.unit
    @pytest.mark.environment
    def test_visibility_without_lighting(self):
        """Dark rooms have poor visibility at night."""
        time = TimeSystem()
        time.set_time(23, 0)  # Night

        weather = WeatherSystem()

        env = LocationEnvironment(
            location_id="dark_room",
            is_indoor=True,
            has_lighting=False
        )

        vis = env.get_visibility(time, weather)
        assert vis < 1.0  # Reduced visibility

    @pytest.mark.unit
    @pytest.mark.environment
    def test_outdoor_affected_by_weather(self):
        """Outdoor locations affected by weather."""
        time = TimeSystem()
        time.set_time(12, 0)  # Noon

        weather = WeatherSystem()
        weather.set_weather(WeatherType.FOG, immediate=True)

        env = LocationEnvironment(
            location_id="garden",
            is_indoor=False,
            has_shelter=False
        )

        vis = env.get_visibility(time, weather)
        assert vis < 0.5  # Fog reduces visibility

    @pytest.mark.unit
    @pytest.mark.environment
    def test_ambient_noise(self):
        """Ambient noise calculated correctly."""
        weather = WeatherSystem()
        weather.set_weather(WeatherType.STORM, immediate=True)

        quiet_room = LocationEnvironment(location_id="quiet", is_indoor=True)
        noisy_room = LocationEnvironment(
            location_id="noisy",
            is_indoor=True,
            is_noisy=True
        )

        quiet_noise = quiet_room.get_ambient_noise(weather)
        noisy_noise = noisy_room.get_ambient_noise(weather)

        assert noisy_noise > quiet_noise

    @pytest.mark.unit
    @pytest.mark.environment
    def test_description_modifiers(self):
        """Get description modifiers for location."""
        time = TimeSystem()
        time.set_time(22, 0)  # Night

        weather = WeatherSystem()
        weather.set_weather(WeatherType.LIGHT_RAIN, immediate=True)

        env = LocationEnvironment(
            location_id="room",
            is_indoor=True,
            has_lighting=False
        )

        modifiers = env.get_description_modifiers(time, weather)

        # Should have darkness and weather modifiers
        assert len(modifiers) >= 1


class TestEnvironment:
    """Environment coordinator tests."""

    @pytest.mark.unit
    @pytest.mark.environment
    def test_create_environment(self):
        """Can create environment coordinator."""
        env = Environment()

        assert env.time is not None
        assert env.weather is not None

    @pytest.mark.unit
    @pytest.mark.environment
    def test_set_seed(self):
        """Can set seed for deterministic environment."""
        env = Environment()
        env.set_seed(42)

        assert env.weather.seed == 42

    @pytest.mark.unit
    @pytest.mark.environment
    def test_update_advances_both(self):
        """Update advances both time and weather."""
        env = Environment()
        env.time.set_time(8, 0)
        initial_time = env.time.current_minutes
        initial_weather_time = env.weather.current_time

        env.update(30)

        assert env.time.current_minutes > initial_time
        # Weather time should have advanced by 30 minutes
        assert env.weather.current_time > initial_weather_time

    @pytest.mark.unit
    @pytest.mark.environment
    def test_update_returns_changes(self):
        """Update returns what changed."""
        env = Environment()
        env.time.set_time(11, 55)

        changes = env.update(10)

        assert "time_events" in changes
        assert "weather_changed" in changes
        assert "period_changed" in changes

    @pytest.mark.unit
    @pytest.mark.environment
    def test_period_change_detected(self):
        """Period changes are detected."""
        env = Environment()
        env.time.set_time(11, 58)

        changes = env.update(5)

        assert changes["period_changed"] == TimePeriod.AFTERNOON

    @pytest.mark.unit
    @pytest.mark.environment
    def test_register_location(self):
        """Can register locations."""
        env = Environment()

        loc_env = env.register_location(
            "study",
            is_indoor=True,
            has_lighting=True
        )

        assert "study" in env.locations
        assert loc_env.has_lighting is True

    @pytest.mark.unit
    @pytest.mark.environment
    def test_get_location_environment(self):
        """Can get location environment."""
        env = Environment()
        env.register_location("study")

        loc_env = env.get_location_environment("study")

        assert loc_env is not None
        assert loc_env.location_id == "study"

    @pytest.mark.unit
    @pytest.mark.environment
    def test_get_visibility_global(self):
        """Get global visibility without location."""
        env = Environment()
        env.time.set_time(12, 0)  # Noon
        env.weather.set_weather(WeatherType.CLEAR, immediate=True)

        vis = env.get_visibility()

        assert vis == 1.0

    @pytest.mark.unit
    @pytest.mark.environment
    def test_get_visibility_location(self):
        """Get visibility for specific location."""
        env = Environment()
        env.time.set_time(23, 0)  # Night
        env.register_location("dark_alley", is_indoor=False, has_lighting=False)

        vis = env.get_visibility("dark_alley")

        assert vis < 1.0

    @pytest.mark.unit
    @pytest.mark.environment
    def test_get_display_status(self):
        """Get formatted display status."""
        env = Environment()
        env.time.set_time(14, 30)
        env.weather.set_weather(WeatherType.CLOUDY, immediate=True)

        status = env.get_display_status()

        assert "14:30" in status
        assert "Cloudy" in status

    @pytest.mark.unit
    @pytest.mark.environment
    def test_get_atmospheric_description(self):
        """Get atmospheric description."""
        env = Environment()
        env.time.set_time(22, 0)
        env.weather.set_weather(WeatherType.LIGHT_RAIN, immediate=True)
        env.register_location("room", is_indoor=True)

        desc = env.get_atmospheric_description("room")

        assert len(desc) >= 1


class TestEnvironmentEvents:
    """Environment event scheduling tests."""

    @pytest.mark.unit
    @pytest.mark.environment
    def test_schedule_event(self):
        """Can schedule time events."""
        env = Environment()

        event = env.schedule_event(
            event_id="dinner",
            hour=18,
            minute=0,
            description="Dinner is served"
        )

        assert len(env.time.events) == 1
        assert event.id == "dinner"

    @pytest.mark.unit
    @pytest.mark.environment
    def test_scheduled_event_triggers(self):
        """Scheduled events trigger correctly."""
        env = Environment()
        env.time.set_time(17, 55)

        triggered_events = []

        def on_dinner():
            triggered_events.append("dinner")

        env.schedule_event(
            event_id="dinner",
            hour=18,
            minute=0,
            callback=on_dinner
        )

        changes = env.update(10)

        assert len(triggered_events) == 1
        assert len(changes["time_events"]) == 1

    @pytest.mark.unit
    @pytest.mark.environment
    def test_advance_to_time(self):
        """Can advance to specific time."""
        env = Environment()
        env.time.set_time(8, 0)

        changes = env.advance_to_time(14, 0)

        assert env.time.hour == 14
        # Should have recorded period changes
        assert "period_changed" in changes


class TestEnvironmentWeatherControl:
    """Environment weather control tests."""

    @pytest.mark.unit
    @pytest.mark.environment
    def test_set_weather(self):
        """Can set weather through environment."""
        env = Environment()
        env.set_weather(WeatherType.STORM)

        assert env.weather.current_state.weather_type == WeatherType.STORM

    @pytest.mark.unit
    @pytest.mark.environment
    def test_get_weather_effect(self):
        """Can get weather effect."""
        env = Environment()
        env.set_weather(WeatherType.FOG)

        effect = env.get_weather_effect()

        assert effect.visibility < 1.0


class TestEnvironmentSerialization:
    """Environment serialization tests."""

    @pytest.mark.unit
    @pytest.mark.environment
    def test_serialize_environment(self):
        """Can serialize environment."""
        env = Environment()
        env.time.set_time(14, 30)
        env.weather.set_weather(WeatherType.CLOUDY, immediate=True)
        env.register_location("study", is_indoor=True)

        data = env.to_dict()

        assert "time" in data
        assert "weather" in data
        assert "locations" in data
        assert "study" in data["locations"]

    @pytest.mark.unit
    @pytest.mark.environment
    def test_deserialize_environment(self):
        """Can deserialize environment."""
        env = Environment()
        env.time.set_time(14, 30)
        env.weather.set_weather(WeatherType.FOG, immediate=True)
        env.register_location(
            "garden",
            is_indoor=False,
            has_lighting=False
        )

        data = env.to_dict()
        restored = Environment.from_dict(data)

        assert restored.time.hour == 14
        assert restored.weather.current_state.weather_type == WeatherType.FOG
        assert "garden" in restored.locations
        assert restored.locations["garden"].is_indoor is False

    @pytest.mark.unit
    @pytest.mark.environment
    def test_roundtrip_preserves_all_state(self):
        """Roundtrip preserves all state."""
        env = Environment()
        env.time.set_time(22, 15, day=2)
        env.time.time_scale = 2.0
        env.weather.set_weather(WeatherType.STORM, immediate=True, intensity=0.8)
        env.register_location(
            "basement",
            is_indoor=True,
            has_lighting=False,
            is_dark=True,
            is_noisy=True
        )

        data = env.to_dict()
        restored = Environment.from_dict(data)

        assert restored.time.day_number == 2
        assert restored.time.time_scale == 2.0
        assert restored.locations["basement"].is_dark is True
        assert restored.locations["basement"].is_noisy is True


class TestEnvironmentGameplayIntegration:
    """Tests for gameplay integration scenarios."""

    @pytest.mark.unit
    @pytest.mark.environment
    def test_visibility_combined_effects(self):
        """Visibility combines time and weather effects."""
        env = Environment()
        env.time.set_time(22, 0)  # Night
        env.weather.set_weather(WeatherType.FOG, immediate=True)
        env.register_location("alley", is_indoor=False, has_lighting=False, has_shelter=False)

        vis = env.get_visibility("alley")

        # Should be low - night + fog + no lights (minimum is 0.1)
        assert vis < 0.5

    @pytest.mark.unit
    @pytest.mark.environment
    def test_indoor_protected_from_weather(self):
        """Indoor locations protected from weather."""
        env = Environment()
        env.time.set_time(12, 0)  # Noon
        env.weather.set_weather(WeatherType.STORM, immediate=True)

        env.register_location("library", is_indoor=True, has_shelter=True)
        env.register_location("courtyard", is_indoor=False, has_shelter=False)

        indoor_vis = env.get_visibility("library")
        outdoor_vis = env.get_visibility("courtyard")

        assert indoor_vis > outdoor_vis
