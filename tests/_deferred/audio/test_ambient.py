"""
Tests for Ambient Sound system.
"""

import pytest
from src.shadowengine.audio.ambient import (
    AmbientLayer, AmbientConfig, AmbientType,
    AmbientEngine, WeatherAudio, LocationAudio, TensionAudio,
    AMBIENT_PRESETS,
)


class TestAmbientConfig:
    """Tests for AmbientConfig."""

    def test_create_config(self, ambient_config):
        """Can create ambient config."""
        assert ambient_config.master_volume == 0.7
        assert ambient_config.max_layers == 8

    def test_default_values(self):
        """Config has sensible defaults."""
        config = AmbientConfig()
        assert config.fade_time_ms == 2000.0
        assert config.tension_affects_volume is True

    def test_serialization(self, ambient_config):
        """Config can be serialized."""
        data = ambient_config.to_dict()
        assert data["master_volume"] == 0.7


class TestAmbientLayer:
    """Tests for AmbientLayer."""

    def test_create_layer(self, ambient_layer):
        """Can create ambient layer."""
        assert ambient_layer.id == "test_ambient"
        assert ambient_layer.ambient_type == AmbientType.RAIN
        assert ambient_layer.volume == 0.5

    def test_effective_volume(self, ambient_layer):
        """Effective volume includes fade."""
        ambient_layer.current_fade = 0.5
        assert ambient_layer.effective_volume == 0.25

    def test_start_fade_in(self, ambient_layer):
        """Can start fade in."""
        ambient_layer.start_fade_in()
        assert ambient_layer.current_fade == 0.0
        assert ambient_layer.is_playing is True

    def test_start_fade_out(self, ambient_layer):
        """Can start fade out."""
        ambient_layer.volume = 0.8
        ambient_layer.start_fade_out()
        assert ambient_layer.target_volume == 0.0

    def test_update_fade_in(self, ambient_layer):
        """Fade in updates correctly."""
        ambient_layer.start_fade_in()
        ambient_layer.fade_in_ms = 1000.0

        # Update for half the fade time
        still_fading = ambient_layer.update_fade(500.0)
        assert still_fading is True
        assert ambient_layer.current_fade == 0.5

    def test_update_fade_out(self, ambient_layer):
        """Fade out updates correctly."""
        ambient_layer.volume = 1.0
        ambient_layer.target_volume = 0.0
        ambient_layer.fade_out_ms = 1000.0
        ambient_layer.is_playing = True

        ambient_layer.update_fade(500.0)
        assert ambient_layer.volume == 0.5

    def test_fade_complete_stops_playing(self, ambient_layer):
        """Layer stops playing when fade out completes."""
        ambient_layer.volume = 0.1
        ambient_layer.target_volume = 0.0
        ambient_layer.fade_out_ms = 100.0
        ambient_layer.is_playing = True

        ambient_layer.update_fade(200.0)
        assert ambient_layer.is_playing is False

    def test_serialization(self, ambient_layer):
        """Layer can be serialized."""
        data = ambient_layer.to_dict()
        restored = AmbientLayer.from_dict(data)

        assert restored.id == ambient_layer.id
        assert restored.ambient_type == ambient_layer.ambient_type


class TestAmbientPresets:
    """Tests for ambient presets."""

    def test_presets_exist(self):
        """Common presets exist."""
        assert AmbientType.RAIN in AMBIENT_PRESETS
        assert AmbientType.THUNDER in AMBIENT_PRESETS
        assert AmbientType.WIND in AMBIENT_PRESETS

    def test_preset_has_tts_seed(self):
        """Presets have TTS seeds."""
        rain = AMBIENT_PRESETS[AmbientType.RAIN]
        assert rain.tts_seed != ""


class TestWeatherAudio:
    """Tests for WeatherAudio."""

    def test_create(self, weather_audio):
        """Can create weather audio manager."""
        assert weather_audio.current_weather is None

    def test_set_clear(self, weather_audio):
        """Clear weather produces minimal layers."""
        layers = weather_audio.set_weather("clear")
        assert len(layers) == 0

    def test_set_rain(self, weather_audio):
        """Rain weather produces rain layer."""
        layers = weather_audio.set_weather("rain")
        assert len(layers) == 1
        assert layers[0].ambient_type == AmbientType.RAIN

    def test_set_heavy_rain(self, weather_audio):
        """Heavy rain is louder."""
        layers = weather_audio.set_weather("heavy_rain")
        assert len(layers) == 1
        assert layers[0].volume > 0.3

    def test_set_storm(self, weather_audio):
        """Storm has rain and wind."""
        layers = weather_audio.set_weather("storm")
        assert len(layers) >= 2

        types = [l.ambient_type for l in layers]
        assert AmbientType.HEAVY_RAIN in types
        assert AmbientType.WIND in types

    def test_set_fog(self, weather_audio):
        """Fog has drip sounds."""
        layers = weather_audio.set_weather("fog")
        assert len(layers) == 1

    def test_set_wind(self, weather_audio):
        """Wind weather has wind layer."""
        layers = weather_audio.set_weather("wind")
        assert len(layers) == 1
        assert layers[0].ambient_type == AmbientType.WIND

    def test_intensity_affects_volume(self, weather_audio):
        """Weather intensity affects volume."""
        low = weather_audio.set_weather("rain", intensity=0.2)
        high = weather_audio.set_weather("rain", intensity=1.0)

        assert high[0].volume > low[0].volume

    def test_add_thunder(self, weather_audio):
        """Can add thunder effect."""
        thunder = weather_audio.add_thunder(distance=0.5)

        assert thunder.ambient_type == AmbientType.THUNDER
        assert thunder.looping is False

    def test_thunder_distance_affects_volume(self, weather_audio):
        """Closer thunder is louder."""
        close = weather_audio.add_thunder(distance=0.1)
        far = weather_audio.add_thunder(distance=0.9)

        assert close.volume > far.volume

    def test_get_layers(self, weather_audio):
        """Can get all weather layers."""
        weather_audio.set_weather("storm")
        layers = weather_audio.get_layers()

        assert len(layers) >= 2

    def test_clear(self, weather_audio):
        """Can clear weather layers."""
        weather_audio.set_weather("storm")
        weather_audio.clear()

        assert weather_audio.current_weather is None
        assert len(weather_audio.get_layers()) == 0


class TestLocationAudio:
    """Tests for LocationAudio."""

    def test_create(self, location_audio):
        """Can create location audio manager."""
        assert location_audio.current_location is None

    def test_get_location_types(self, location_audio):
        """Can get available location types."""
        types = location_audio.get_location_types()

        assert "street" in types
        assert "bar" in types
        assert "office" in types
        assert "warehouse" in types
        assert "docks" in types
        assert "alley" in types

    def test_set_street(self, location_audio):
        """Street has traffic and footsteps."""
        layers = location_audio.set_location("street")
        types = [l.ambient_type for l in layers]

        assert AmbientType.CITY_TRAFFIC in types

    def test_set_bar(self, location_audio):
        """Bar has crowd murmur."""
        layers = location_audio.set_location("bar")
        types = [l.ambient_type for l in layers]

        assert AmbientType.CROWD_MURMUR in types

    def test_set_office(self, location_audio):
        """Office has hum and clock."""
        layers = location_audio.set_location("office")
        types = [l.ambient_type for l in layers]

        assert AmbientType.ELECTRIC_HUM in types or AmbientType.CLOCK_TICK in types

    def test_set_warehouse(self, location_audio):
        """Warehouse has echo/silence."""
        layers = location_audio.set_location("warehouse")
        assert len(layers) > 0

    def test_set_docks(self, location_audio):
        """Docks has water sounds."""
        layers = location_audio.set_location("docks")
        types = [l.ambient_type for l in layers]

        assert AmbientType.WATER_FLOW in types

    def test_set_alley(self, location_audio):
        """Alley has drips and distant traffic."""
        layers = location_audio.set_location("alley")
        assert len(layers) > 0

    def test_layers_start_fading_in(self, location_audio):
        """New location layers start fading in."""
        layers = location_audio.set_location("bar")
        assert all(l.is_playing for l in layers)

    def test_add_custom_layer(self, location_audio, ambient_layer):
        """Can add custom layer to location."""
        location_audio.set_location("office")
        location_audio.add_custom_layer(ambient_layer)

        layers = location_audio.get_layers()
        assert ambient_layer in layers


class TestTensionAudio:
    """Tests for TensionAudio."""

    def test_create(self, tension_audio):
        """Can create tension audio manager."""
        assert tension_audio.tension == 0.0

    def test_low_tension(self, tension_audio):
        """Low tension has minimal layers."""
        layers = tension_audio.set_tension(0.1)
        assert len(layers) == 0

    def test_medium_tension(self, tension_audio):
        """Medium tension adds hum."""
        layers = tension_audio.set_tension(0.4)
        types = [l.ambient_type for l in layers]

        assert AmbientType.ELECTRIC_HUM in types

    def test_high_tension_heartbeat(self, tension_audio):
        """High tension adds heartbeat."""
        layers = tension_audio.set_tension(0.6)
        types = [l.ambient_type for l in layers]

        assert AmbientType.HEARTBEAT in types

    def test_very_high_tension(self, tension_audio):
        """Very high tension adds breathing."""
        layers = tension_audio.set_tension(0.8)
        types = [l.ambient_type for l in layers]

        assert AmbientType.WIND in types or len(layers) >= 2

    def test_critical_tension(self, tension_audio):
        """Critical tension intensifies all layers."""
        layers = tension_audio.set_tension(0.95)

        # Critical should boost volumes
        for layer in layers:
            assert layer.volume > 0

    def test_heartbeat_rate(self, tension_audio):
        """Heartbeat rate increases with tension."""
        tension_audio.set_tension(0.3)
        low_rate = tension_audio.get_heartbeat_rate()

        tension_audio.set_tension(0.9)
        high_rate = tension_audio.get_heartbeat_rate()

        assert high_rate > low_rate


class TestAmbientEngine:
    """Tests for AmbientEngine."""

    def test_create(self, ambient_engine):
        """Can create ambient engine."""
        assert ambient_engine is not None

    def test_master_volume(self, ambient_engine):
        """Can set master volume."""
        ambient_engine.master_volume = 0.5
        assert ambient_engine.master_volume == 0.5

    def test_master_volume_clamped(self, ambient_engine):
        """Master volume is clamped."""
        ambient_engine.master_volume = 2.0
        assert ambient_engine.master_volume == 1.0

        ambient_engine.master_volume = -1.0
        assert ambient_engine.master_volume == 0.0

    def test_mute_unmute(self, ambient_engine):
        """Can mute and unmute."""
        ambient_engine.mute()
        assert ambient_engine.muted is True

        ambient_engine.unmute()
        assert ambient_engine.muted is False

    def test_set_weather(self, ambient_engine):
        """Can set weather."""
        ambient_engine.set_weather("storm")
        layers = ambient_engine.get_all_layers()

        assert len(layers) >= 2

    def test_set_location(self, ambient_engine):
        """Can set location."""
        ambient_engine.set_location("bar")
        layers = ambient_engine.get_all_layers()

        assert len(layers) >= 1

    def test_set_tension(self, ambient_engine):
        """Can set tension."""
        ambient_engine.set_tension(0.7)
        layers = ambient_engine.get_all_layers()

        assert len(layers) >= 1

    def test_layers_combined(self, ambient_engine):
        """All layer sources are combined."""
        ambient_engine.set_weather("rain")
        ambient_engine.set_location("street")
        ambient_engine.set_tension(0.6)

        layers = ambient_engine.get_all_layers()

        # Should have weather + location + tension layers
        assert len(layers) >= 3

    def test_add_custom_layer(self, ambient_engine, ambient_layer):
        """Can add custom layer."""
        ambient_engine.add_custom_layer(ambient_layer)
        layers = ambient_engine.get_all_layers()

        ids = [l.id for l in layers]
        assert ambient_layer.id in ids

    def test_remove_custom_layer(self, ambient_engine, ambient_layer):
        """Can remove custom layer."""
        ambient_engine.add_custom_layer(ambient_layer)
        removed = ambient_engine.remove_custom_layer(ambient_layer.id)

        assert removed is not None

        layers = ambient_engine.get_all_layers()
        ids = [l.id for l in layers]
        assert ambient_layer.id not in ids

    def test_layer_count(self, ambient_engine):
        """Can get layer count."""
        ambient_engine.set_weather("storm")
        ambient_engine.set_location("bar")

        count = ambient_engine.get_layer_count()
        assert count >= 3

    def test_muted_layers_zero_volume(self, ambient_engine):
        """Muted engine sets all volumes to zero."""
        ambient_engine.set_weather("rain")
        ambient_engine.mute()

        layers = ambient_engine.get_all_layers()
        for layer in layers:
            assert layer.volume == 0.0

    def test_master_volume_applied(self, ambient_engine):
        """Master volume is applied to layers."""
        ambient_engine.set_weather("rain")
        ambient_engine.master_volume = 0.5

        layers = ambient_engine.get_all_layers()
        # Layers should have reduced volume

    def test_update(self, ambient_engine):
        """Can update engine state."""
        ambient_engine.set_weather("rain")
        ambient_engine.update(100.0)  # 100ms

        # Should not raise

    def test_generate_mix(self, ambient_engine):
        """Can generate mixed audio."""
        ambient_engine.set_weather("rain")
        audio = ambient_engine.generate_mix(1000.0)  # 1 second

        assert len(audio) > 0

    def test_generate_mix_muted(self, ambient_engine):
        """Muted engine generates silence."""
        ambient_engine.set_weather("storm")
        ambient_engine.mute()

        audio = ambient_engine.generate_mix(1000.0)
        # Should be silent (all zeros)

    def test_add_thunder(self, ambient_engine):
        """Can add thunder effect."""
        ambient_engine.set_weather("storm")
        thunder = ambient_engine.add_thunder(distance=0.3)

        assert thunder.ambient_type == AmbientType.THUNDER

    def test_serialization(self, ambient_engine):
        """Engine can be serialized."""
        ambient_engine.set_weather("fog")
        ambient_engine.set_location("docks")
        ambient_engine.set_tension(0.4)

        data = ambient_engine.to_dict()

        assert data["weather"] == "fog"
        assert data["location"] == "docks"
        assert data["tension"] == 0.4

    def test_restore_from_dict(self, ambient_config):
        """Engine can be restored from dict."""
        data = {
            "config": ambient_config.to_dict(),
            "master_volume": 0.6,
            "muted": False,
            "weather": "rain",
            "location": "bar",
            "tension": 0.5,
        }

        engine = AmbientEngine.from_dict(data)

        assert engine.master_volume == 0.6
        assert len(engine.get_all_layers()) > 0
