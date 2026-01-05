"""Tests for the sound library."""

import pytest
from src.shadowengine.audio.library import (
    SoundLibrary,
    SoundID,
    SoundDefinition,
    SOUND_LIBRARY
)
from src.shadowengine.audio.sound import SoundCategory


class TestSoundDefinition:
    """Tests for SoundDefinition."""

    def test_definition_has_required_fields(self):
        """Test definitions have all required fields."""
        for sound_id, defn in SOUND_LIBRARY.items():
            assert defn.id == sound_id
            assert len(defn.name) > 0
            assert isinstance(defn.category, SoundCategory)
            assert len(defn.generator_type) > 0
            assert defn.duration_ms > 0


class TestSoundIDs:
    """Tests for SoundID enum."""

    def test_footstep_sounds_exist(self):
        """Test footstep sounds are defined."""
        footsteps = [
            SoundID.FOOTSTEP_WOOD,
            SoundID.FOOTSTEP_CONCRETE,
            SoundID.FOOTSTEP_GRAVEL,
            SoundID.FOOTSTEP_WATER
        ]
        for sound_id in footsteps:
            assert sound_id in SOUND_LIBRARY

    def test_door_sounds_exist(self):
        """Test door sounds are defined."""
        doors = [
            SoundID.DOOR_OPEN,
            SoundID.DOOR_CLOSE,
            SoundID.DOOR_CREAK,
            SoundID.DOOR_KNOCK
        ]
        for sound_id in doors:
            assert sound_id in SOUND_LIBRARY

    def test_weather_sounds_exist(self):
        """Test weather sounds are defined."""
        weather = [
            SoundID.RAIN_LIGHT,
            SoundID.RAIN_HEAVY,
            SoundID.THUNDER_DISTANT,
            SoundID.THUNDER_CLOSE,
            SoundID.WIND_LIGHT,
            SoundID.WIND_STRONG
        ]
        for sound_id in weather:
            assert sound_id in SOUND_LIBRARY

    def test_horror_sounds_exist(self):
        """Test horror sounds are defined."""
        horror = [
            SoundID.HEARTBEAT,
            SoundID.WHISPER,
            SoundID.CREAK_FLOOR,
            SoundID.DRIP_WATER
        ]
        for sound_id in horror:
            assert sound_id in SOUND_LIBRARY

    def test_ui_sounds_exist(self):
        """Test UI sounds are defined."""
        ui = [
            SoundID.UI_CLICK,
            SoundID.UI_SELECT,
            SoundID.UI_ERROR
        ]
        for sound_id in ui:
            assert sound_id in SOUND_LIBRARY


class TestSoundLibrary:
    """Tests for SoundLibrary."""

    def test_create_library(self):
        """Test creating a sound library."""
        library = SoundLibrary()
        assert library is not None

    def test_get_sound(self):
        """Test getting a sound effect."""
        library = SoundLibrary()
        sound = library.get_sound(SoundID.FOOTSTEP_WOOD)

        assert sound is not None
        assert sound.category == SoundCategory.FOOTSTEPS

    def test_get_sound_variant(self):
        """Test getting sound variants."""
        library = SoundLibrary()

        sound0 = library.get_sound(SoundID.FOOTSTEP_WOOD, variant=0)
        sound1 = library.get_sound(SoundID.FOOTSTEP_WOOD, variant=1)

        # Should be different instances
        assert sound0.id != sound1.id

    def test_get_invalid_sound(self):
        """Test getting invalid sound raises error."""
        library = SoundLibrary()

        with pytest.raises(ValueError):
            library.get_sound("not_a_real_sound")

    def test_get_audio(self):
        """Test getting audio for a sound."""
        library = SoundLibrary()
        audio = library.get_audio(SoundID.FOOTSTEP_WOOD)

        assert audio is not None
        assert len(audio.data) > 0

    def test_audio_caching(self):
        """Test audio is cached."""
        library = SoundLibrary()

        audio1 = library.get_audio(SoundID.FOOTSTEP_WOOD, variant=0, seed=42)
        audio2 = library.get_audio(SoundID.FOOTSTEP_WOOD, variant=0, seed=42)

        assert audio1 is audio2  # Same cached instance

    def test_get_random_variant(self):
        """Test getting random variant."""
        library = SoundLibrary()

        audio1 = library.get_random_variant(SoundID.FOOTSTEP_WOOD, seed=100)
        audio2 = library.get_random_variant(SoundID.FOOTSTEP_WOOD, seed=200)

        # Different seeds may produce different variants
        assert audio1 is not None
        assert audio2 is not None

    def test_get_by_category(self):
        """Test getting sounds by category."""
        library = SoundLibrary()

        footsteps = library.get_by_category(SoundCategory.FOOTSTEPS)
        assert len(footsteps) > 0
        assert SoundID.FOOTSTEP_WOOD in footsteps

        weather = library.get_by_category(SoundCategory.WEATHER)
        assert len(weather) > 0
        assert SoundID.RAIN_LIGHT in weather

    def test_get_by_tag(self):
        """Test getting sounds by tag."""
        library = SoundLibrary()

        rain_sounds = library.get_by_tag("rain")
        assert len(rain_sounds) > 0

        storm_sounds = library.get_by_tag("storm")
        assert len(storm_sounds) > 0

    def test_search_by_name(self):
        """Test searching by name."""
        library = SoundLibrary()

        results = library.search("footstep")
        assert len(results) > 0

        results = library.search("thunder")
        assert len(results) > 0

    def test_search_by_tag(self):
        """Test searching by tag."""
        library = SoundLibrary()

        results = library.search("horror")
        assert len(results) > 0

    def test_search_with_category(self):
        """Test searching with category filter."""
        library = SoundLibrary()

        results = library.search("", category=SoundCategory.WEATHER)
        assert len(results) > 0
        assert all(
            SOUND_LIBRARY[sid].category == SoundCategory.WEATHER
            for sid in results
        )

    def test_clear_cache(self):
        """Test clearing the cache."""
        library = SoundLibrary()

        library.get_audio(SoundID.FOOTSTEP_WOOD)
        assert len(library._cache) > 0

        library.clear_cache()
        assert len(library._cache) == 0

    def test_get_all_ids(self):
        """Test getting all sound IDs."""
        library = SoundLibrary()
        ids = library.get_all_ids()

        assert len(ids) == len(SOUND_LIBRARY)

    def test_get_definition(self):
        """Test getting a sound definition."""
        library = SoundLibrary()
        defn = library.get_definition(SoundID.GUNSHOT)

        assert defn is not None
        assert defn.id == SoundID.GUNSHOT
        assert defn.category == SoundCategory.IMPACTS

    def test_add_custom_definition(self):
        """Test adding a custom sound definition."""
        library = SoundLibrary()

        # Use an existing SoundID but with modified definition
        custom_id = SoundID.UI_SUCCESS

        custom_defn = SoundDefinition(
            id=custom_id,
            name="Custom Sound",
            category=SoundCategory.AMBIENCE,
            generator_type="noise",
            duration_ms=500,
            properties=library.get_definition(SoundID.FOOTSTEP_WOOD).properties,
            tags=["custom", "test"],
            variants=1
        )

        library.add_definition(custom_defn)
        retrieved = library.get_definition(custom_id)
        assert retrieved is not None
        assert retrieved.name == "Custom Sound"
