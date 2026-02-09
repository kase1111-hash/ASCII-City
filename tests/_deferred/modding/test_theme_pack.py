"""
Tests for the theme pack system.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.shadowengine.modding.theme_pack import (
    ThemePack, ThemeConfig, VocabularyConfig,
    WeatherConfig, AtmosphereConfig,
    load_theme_pack, save_theme_pack, create_theme_pack,
    NOIR_THEME, CYBERPUNK_THEME, GOTHIC_HORROR_THEME,
    get_builtin_theme, list_builtin_themes,
)


class TestVocabularyConfig:
    """Tests for VocabularyConfig."""

    def test_create_default(self, vocabulary_config):
        """Default vocabulary config has values."""
        assert len(vocabulary_config.examine_verbs) > 0
        assert len(vocabulary_config.talk_verbs) > 0

    def test_get_verb(self, vocabulary_config):
        """Can get verb by type and index."""
        verb = vocabulary_config.get_verb("examine", 0)
        assert verb in vocabulary_config.examine_verbs

    def test_get_random_verb(self, vocabulary_config):
        """Can get random verb."""
        import random
        rng = random.Random(42)
        verb = vocabulary_config.get_random_verb("talk", rng)
        assert verb in vocabulary_config.talk_verbs

    def test_custom_terms(self):
        """Can define custom terms."""
        vocab = VocabularyConfig(
            custom_terms={
                "money": ["credits", "creds"],
                "computer": ["deck", "rig"],
            }
        )
        assert "credits" in vocab.custom_terms["money"]

    def test_serialization(self, vocabulary_config):
        """VocabularyConfig can be serialized."""
        data = vocabulary_config.to_dict()
        restored = VocabularyConfig.from_dict(data)

        assert restored.examine_verbs == vocabulary_config.examine_verbs
        assert restored.talk_verbs == vocabulary_config.talk_verbs


class TestWeatherConfig:
    """Tests for WeatherConfig."""

    def test_create_default(self, weather_config):
        """Default weather config has values."""
        assert len(weather_config.weather_weights) > 0

    def test_weights_sum_to_one(self, weather_config):
        """Default weights sum to approximately 1.0."""
        total = sum(weather_config.weather_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_get_weather_probability(self, weather_config):
        """Can get weather probability."""
        prob = weather_config.get_weather_probability("clear")
        assert prob > 0

    def test_get_description(self, weather_config):
        """Can get weather description."""
        desc = weather_config.get_description("rain")
        assert "rain" in desc.lower()

    def test_custom_weather(self):
        """Can define custom weather types."""
        weather = WeatherConfig(
            weather_weights={"clear": 0.5, "acid_rain": 0.5},
            custom_weather={
                "acid_rain": {
                    "damage_modifier": 0.1,
                    "visibility": 0.3,
                }
            },
        )
        assert "acid_rain" in weather.weather_weights

    def test_serialization(self, weather_config):
        """WeatherConfig can be serialized."""
        data = weather_config.to_dict()
        restored = WeatherConfig.from_dict(data)

        assert restored.weather_weights == weather_config.weather_weights


class TestAtmosphereConfig:
    """Tests for AtmosphereConfig."""

    def test_create_default(self, atmosphere_config):
        """Default atmosphere config has values."""
        assert atmosphere_config.primary_color is not None
        assert atmosphere_config.effect_intensity > 0

    def test_get_tension_color(self, atmosphere_config):
        """Can get color for tension level."""
        low = atmosphere_config.get_tension_color(0.1)
        high = atmosphere_config.get_tension_color(0.9)

        assert low is not None
        assert high is not None

    def test_particle_effects(self, atmosphere_config):
        """Particle effects can be configured."""
        assert isinstance(atmosphere_config.particle_effects, dict)

    def test_serialization(self, atmosphere_config):
        """AtmosphereConfig can be serialized."""
        data = atmosphere_config.to_dict()
        restored = AtmosphereConfig.from_dict(data)

        assert restored.primary_color == atmosphere_config.primary_color


class TestThemeConfig:
    """Tests for ThemeConfig."""

    def test_create_default(self, theme_config):
        """Default theme config has values."""
        assert len(theme_config.time_periods) > 0
        assert len(theme_config.location_types) > 0

    def test_time_periods(self, theme_config):
        """Time periods are tuples."""
        for period, (start, end) in theme_config.time_periods.items():
            assert isinstance(start, int)
            assert isinstance(end, int)

    def test_serialization(self, theme_config):
        """ThemeConfig can be serialized."""
        data = theme_config.to_dict()
        restored = ThemeConfig.from_dict(data)

        assert restored.narration_style == theme_config.narration_style


class TestThemePack:
    """Tests for ThemePack."""

    def test_create_theme_pack(self, theme_pack):
        """Can create a theme pack."""
        assert theme_pack.id == "test_theme"
        assert theme_pack.name == "Test Theme"

    def test_get_vocabulary(self, theme_pack):
        """Can get vocabulary config."""
        vocab = theme_pack.get_vocabulary()
        assert vocab is not None

    def test_get_weather(self, theme_pack):
        """Can get weather config."""
        weather = theme_pack.get_weather()
        assert weather is not None

    def test_get_atmosphere(self, theme_pack):
        """Can get atmosphere config."""
        atmos = theme_pack.get_atmosphere()
        assert atmos is not None

    def test_has_custom_archetypes(self, theme_pack):
        """Can check for custom archetypes."""
        assert not theme_pack.has_custom_archetypes()

        theme_pack.archetypes = ["custom_archetype"]
        assert theme_pack.has_custom_archetypes()

    def test_get_location_template(self, theme_pack):
        """Can get location template."""
        theme_pack.location_templates = {
            "office": {"name": "Office", "art": ["###"]}
        }
        template = theme_pack.get_location_template("office")
        assert template is not None
        assert template["name"] == "Office"

    def test_get_art_template(self, theme_pack):
        """Can get ASCII art template."""
        theme_pack.art_templates = {
            "tree": ["  ^  ", " /|\\ ", "  |  "]
        }
        art = theme_pack.get_art_template("tree")
        assert art is not None
        assert len(art) == 3

    def test_serialization(self, theme_pack):
        """ThemePack can be serialized."""
        data = theme_pack.to_dict()
        restored = ThemePack.from_dict(data)

        assert restored.id == theme_pack.id
        assert restored.name == theme_pack.name
        assert restored.author == theme_pack.author

    def test_full_serialization(self, cyberpunk_theme):
        """Complex theme pack can be serialized."""
        data = cyberpunk_theme.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = ThemePack.from_dict(restored_data)

        assert restored.id == cyberpunk_theme.id
        assert restored.vocabulary.examine_verbs == cyberpunk_theme.vocabulary.examine_verbs


class TestFileOperations:
    """Tests for theme pack file operations."""

    def test_save_and_load(self, theme_pack, temp_mod_dir):
        """Can save and load theme pack."""
        file_path = temp_mod_dir / "test_theme.json"

        save_theme_pack(theme_pack, str(file_path))
        assert file_path.exists()

        loaded = load_theme_pack(str(file_path))
        assert loaded.id == theme_pack.id
        assert loaded.name == theme_pack.name

    def test_load_nonexistent(self):
        """Loading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_theme_pack("nonexistent.json")

    def test_create_theme_pack_function(self):
        """Can use create_theme_pack helper."""
        pack = create_theme_pack(
            id="new_theme",
            name="New Theme",
            author="Author",
            description="A new theme",
        )
        assert pack.id == "new_theme"
        assert pack.name == "New Theme"


class TestBuiltinThemes:
    """Tests for built-in themes."""

    def test_noir_theme_exists(self):
        """Noir theme exists and is valid."""
        assert NOIR_THEME is not None
        assert NOIR_THEME.id == "noir"

    def test_cyberpunk_theme_exists(self):
        """Cyberpunk theme exists and is valid."""
        assert CYBERPUNK_THEME is not None
        assert CYBERPUNK_THEME.id == "cyberpunk"

    def test_gothic_horror_theme_exists(self):
        """Gothic horror theme exists and is valid."""
        assert GOTHIC_HORROR_THEME is not None
        assert GOTHIC_HORROR_THEME.id == "gothic_horror"

    def test_get_builtin_theme(self):
        """Can get builtin theme by ID."""
        noir = get_builtin_theme("noir")
        assert noir is not None
        assert noir.id == "noir"

    def test_list_builtin_themes(self):
        """Can list builtin themes."""
        themes = list_builtin_themes()
        assert len(themes) >= 3
        assert "noir" in themes
        assert "cyberpunk" in themes

    def test_cyberpunk_has_custom_vocabulary(self):
        """Cyberpunk theme has custom vocabulary."""
        vocab = CYBERPUNK_THEME.vocabulary
        assert "scan" in vocab.examine_verbs
        assert "ping" in vocab.talk_verbs

    def test_gothic_has_atmosphere_settings(self):
        """Gothic theme has atmosphere settings."""
        atmos = GOTHIC_HORROR_THEME.atmosphere
        assert atmos.particle_effects.get("fog") is True
