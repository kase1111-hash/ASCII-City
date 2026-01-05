"""Tests for the ambience system."""

import pytest
from src.shadowengine.audio.ambience import (
    AmbientLayer,
    AmbiencePreset,
    AmbienceType,
    AmbienceManager,
    WeatherType,
    TimeOfDay,
    WeatherAudio,
    TensionAudio
)
from src.shadowengine.audio.sound import SoundGenerator


class TestAmbientLayer:
    """Tests for AmbientLayer."""

    def test_create_layer(self):
        """Test creating an ambient layer."""
        layer = AmbientLayer(
            id="rain",
            name="Rain",
            sound_type="rain"
        )
        assert layer.id == "rain"
        assert layer.name == "Rain"
        assert layer.is_active is True
        assert layer.loop is True

    def test_layer_with_conditions(self):
        """Test layer with weather/time conditions."""
        layer = AmbientLayer(
            id="night_crickets",
            name="Crickets",
            sound_type="static",
            weather_types=[WeatherType.CLEAR, WeatherType.CLOUDY],
            time_periods=[TimeOfDay.NIGHT, TimeOfDay.LATE_NIGHT]
        )

        # Should play in clear night
        assert layer.should_play(WeatherType.CLEAR, TimeOfDay.NIGHT, 0.0)

        # Should not play in rain
        assert not layer.should_play(WeatherType.RAIN_HEAVY, TimeOfDay.NIGHT, 0.0)

        # Should not play during day
        assert not layer.should_play(WeatherType.CLEAR, TimeOfDay.NOON, 0.0)

    def test_layer_tension_conditions(self):
        """Test layer with tension conditions."""
        layer = AmbientLayer(
            id="heartbeat",
            name="Heartbeat",
            sound_type="heartbeat",
            min_tension=0.7,
            max_tension=1.0
        )

        assert not layer.should_play(WeatherType.CLEAR, TimeOfDay.NIGHT, 0.3)
        assert layer.should_play(WeatherType.CLEAR, TimeOfDay.NIGHT, 0.8)

    def test_inactive_layer(self):
        """Test inactive layer doesn't play."""
        layer = AmbientLayer(
            id="test",
            name="Test",
            sound_type="noise",
            is_active=False
        )

        assert not layer.should_play(WeatherType.CLEAR, TimeOfDay.NIGHT, 0.0)

    def test_volume_update(self):
        """Test volume modulation."""
        layer = AmbientLayer(
            id="test",
            name="Test",
            sound_type="noise",
            base_volume=0.5,
            volume_mod_range=0.2
        )

        layer.update_volume(1.0)
        assert 0.3 <= layer.current_volume <= 0.7

    def test_to_dict(self):
        """Test serialization."""
        layer = AmbientLayer(
            id="test",
            name="Test",
            sound_type="rain",
            weather_types=[WeatherType.RAIN_LIGHT],
            time_periods=[TimeOfDay.NIGHT]
        )
        d = layer.to_dict()

        assert d['id'] == "test"
        assert d['sound_type'] == "rain"
        assert 'rain_light' in d['weather_types']


class TestAmbiencePreset:
    """Tests for AmbiencePreset."""

    def test_create_preset(self):
        """Test creating a preset."""
        preset = AmbiencePreset(
            id="city_night",
            name="City Night",
            ambience_type=AmbienceType.CITY_NIGHT
        )
        assert preset.id == "city_night"
        assert preset.ambience_type == AmbienceType.CITY_NIGHT
        assert len(preset.layers) == 0

    def test_preset_with_layers(self):
        """Test preset with multiple layers."""
        layers = [
            AmbientLayer(id="traffic", name="Traffic", sound_type="wind"),
            AmbientLayer(id="sirens", name="Sirens", sound_type="tone")
        ]
        preset = AmbiencePreset(
            id="city",
            name="City",
            ambience_type=AmbienceType.CITY_DAY,
            layers=layers
        )
        assert len(preset.layers) == 2

    def test_get_active_layers(self):
        """Test getting active layers."""
        preset = AmbiencePreset(
            id="test",
            name="Test",
            ambience_type=AmbienceType.CITY_NIGHT,
            layers=[
                AmbientLayer(
                    id="day_only",
                    name="Day",
                    sound_type="noise",
                    time_periods=[TimeOfDay.NOON]
                ),
                AmbientLayer(
                    id="night_only",
                    name="Night",
                    sound_type="noise",
                    time_periods=[TimeOfDay.NIGHT]
                ),
                AmbientLayer(
                    id="always",
                    name="Always",
                    sound_type="noise"
                )
            ]
        )

        active = preset.get_active_layers(
            WeatherType.CLEAR,
            TimeOfDay.NIGHT,
            0.0
        )

        ids = [l.id for l in active]
        assert "night_only" in ids
        assert "always" in ids
        assert "day_only" not in ids

    def test_to_dict(self):
        """Test serialization."""
        preset = AmbiencePreset(
            id="test",
            name="Test",
            ambience_type=AmbienceType.RAIN,
            master_volume=0.8
        )
        d = preset.to_dict()

        assert d['id'] == "test"
        assert d['ambience_type'] == "rain"
        assert d['master_volume'] == 0.8


class TestWeatherAudio:
    """Tests for WeatherAudio."""

    def test_create_weather_audio(self):
        """Test creating weather audio manager."""
        weather = WeatherAudio()
        assert weather._current_weather == WeatherType.CLEAR
        assert weather._intensity == 0.5

    def test_set_weather(self):
        """Test setting weather."""
        weather = WeatherAudio()
        weather.set_weather(WeatherType.RAIN_HEAVY, 0.8)

        assert weather._current_weather == WeatherType.RAIN_HEAVY
        assert weather._intensity == 0.8

    def test_clear_weather_no_audio(self):
        """Test clear weather produces no audio."""
        weather = WeatherAudio()
        weather.set_weather(WeatherType.CLEAR)

        audio = weather.get_weather_audio()
        assert audio is None

    def test_rain_produces_audio(self):
        """Test rain weather produces audio."""
        weather = WeatherAudio()
        weather.set_weather(WeatherType.RAIN_LIGHT)

        audio = weather.get_weather_audio(duration_ms=1000)
        assert audio is not None
        assert len(audio.data) > 0

    def test_storm_produces_audio(self):
        """Test storm weather produces audio."""
        weather = WeatherAudio()
        weather.set_weather(WeatherType.STORM)

        audio = weather.get_weather_audio(duration_ms=1000)
        assert audio is not None

    def test_wind_produces_audio(self):
        """Test wind weather produces audio."""
        weather = WeatherAudio()
        weather.set_weather(WeatherType.WIND)

        audio = weather.get_weather_audio(duration_ms=1000)
        assert audio is not None

    def test_thunder_check(self):
        """Test thunder playback check."""
        weather = WeatherAudio()

        # No thunder in clear weather
        weather.set_weather(WeatherType.CLEAR)
        assert not weather.should_play_thunder()

        # Possible thunder in storm
        weather.set_weather(WeatherType.STORM, intensity=1.0)
        # May or may not play (random), but should not raise

    def test_get_thunder_audio(self):
        """Test thunder audio generation."""
        weather = WeatherAudio()
        audio = weather.get_thunder_audio(seed=42)

        assert audio is not None
        assert len(audio.data) > 0


class TestTensionAudio:
    """Tests for TensionAudio."""

    def test_create_tension_audio(self):
        """Test creating tension audio manager."""
        tension = TensionAudio()
        assert tension.get_tension() == 0.0

    def test_set_tension(self):
        """Test setting tension level."""
        tension = TensionAudio()
        tension.set_tension(0.8)
        assert tension.get_tension() == 0.8

    def test_tension_clamping(self):
        """Test tension value clamping."""
        tension = TensionAudio()

        tension.set_tension(1.5)
        assert tension.get_tension() == 1.0

        tension.set_tension(-0.5)
        assert tension.get_tension() == 0.0

    def test_heartbeat_threshold(self):
        """Test heartbeat playback threshold."""
        tension = TensionAudio()

        tension.set_tension(0.5)
        assert not tension.should_play_heartbeat()

        tension.set_tension(0.8)
        assert tension.should_play_heartbeat()

    def test_heartbeat_audio(self):
        """Test heartbeat audio generation."""
        tension = TensionAudio()
        tension.set_tension(0.8)

        audio = tension.get_heartbeat_audio(duration_ms=1000)
        assert audio is not None
        assert len(audio.data) > 0

    def test_tension_drone_threshold(self):
        """Test tension drone threshold."""
        tension = TensionAudio()

        tension.set_tension(0.2)
        assert tension.get_tension_drone() is None

        tension.set_tension(0.5)
        drone = tension.get_tension_drone(duration_ms=1000)
        assert drone is not None

    def test_scare_sting(self):
        """Test scare sting generation."""
        tension = TensionAudio()
        audio = tension.get_scare_sting()

        assert audio is not None
        assert len(audio.data) > 0
        assert audio.duration_ms == 500


class TestAmbienceManager:
    """Tests for AmbienceManager."""

    def test_create_manager(self):
        """Test creating ambience manager."""
        manager = AmbienceManager()
        assert manager._master_volume == 1.0
        assert manager._time_of_day == TimeOfDay.NIGHT

    def test_default_presets(self):
        """Test default presets are loaded."""
        manager = AmbienceManager()

        assert manager.get_preset("city_night") is not None
        assert manager.get_preset("rain") is not None
        assert manager.get_preset("storm") is not None
        assert manager.get_preset("indoor_quiet") is not None
        assert manager.get_preset("alley") is not None

    def test_set_preset(self):
        """Test setting active preset."""
        manager = AmbienceManager()

        result = manager.set_preset("city_night")
        assert result is True
        assert manager._current_preset is not None

    def test_set_invalid_preset(self):
        """Test setting invalid preset."""
        manager = AmbienceManager()

        result = manager.set_preset("nonexistent")
        assert result is False

    def test_set_weather(self):
        """Test setting weather."""
        manager = AmbienceManager()
        manager.set_weather(WeatherType.RAIN_HEAVY, 0.8)

        assert manager.weather_audio._current_weather == WeatherType.RAIN_HEAVY

    def test_set_tension(self):
        """Test setting tension."""
        manager = AmbienceManager()
        manager.set_tension(0.7)

        assert manager.tension_audio.get_tension() == 0.7

    def test_set_time_of_day(self):
        """Test setting time of day."""
        manager = AmbienceManager()
        manager.set_time_of_day(TimeOfDay.DAWN)

        assert manager._time_of_day == TimeOfDay.DAWN

    def test_set_master_volume(self):
        """Test setting master volume."""
        manager = AmbienceManager()
        manager.set_master_volume(0.5)

        assert manager._master_volume == 0.5

    def test_get_active_layers(self):
        """Test getting active layers."""
        manager = AmbienceManager()
        manager.set_preset("city_night")

        layers = manager.get_active_layers()
        assert isinstance(layers, list)

    def test_generate_ambient_mix(self):
        """Test generating ambient audio mix."""
        manager = AmbienceManager()
        manager.set_preset("alley")

        audio = manager.generate_ambient_mix(duration_ms=1000)

        assert audio is not None
        assert len(audio.data) > 0

    def test_add_custom_preset(self):
        """Test adding custom preset."""
        manager = AmbienceManager()

        custom = AmbiencePreset(
            id="custom_preset",
            name="Custom",
            ambience_type=AmbienceType.INDOOR_QUIET
        )
        manager.add_preset(custom)

        assert manager.get_preset("custom_preset") is not None
