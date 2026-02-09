"""Tests for the sound system."""

import pytest
from src.shadowengine.audio.sound import (
    SoundEffect,
    SoundCategory,
    SoundTrigger,
    SoundProperties,
    SoundGenerator,
    SoundInstance,
    SoundMixer
)
from src.shadowengine.audio.tts_engine import AudioFormat


class TestSoundProperties:
    """Tests for SoundProperties."""

    def test_default_properties(self):
        """Test default property values."""
        props = SoundProperties()
        assert props.volume == 1.0
        assert props.pitch == 1.0
        assert props.pan == 0.0
        assert props.is_3d is False

    def test_to_dict(self):
        """Test serialization."""
        props = SoundProperties(volume=0.5, pitch=1.2, pan=-0.5)
        d = props.to_dict()
        assert d['volume'] == 0.5
        assert d['pitch'] == 1.2
        assert d['pan'] == -0.5

    def test_apply_variation(self):
        """Test applying random variation."""
        props = SoundProperties(
            volume=0.5,
            pitch=1.0,
            volume_variation=0.2,
            pitch_variation=0.1
        )

        varied = props.apply_variation(seed=42)

        # Should be within variation range
        assert 0.3 <= varied.volume <= 0.7
        assert 0.9 <= varied.pitch <= 1.1

    def test_variation_seed_reproducibility(self):
        """Test seed produces reproducible variation."""
        props = SoundProperties(volume_variation=0.2, pitch_variation=0.1)

        v1 = props.apply_variation(seed=123)
        v2 = props.apply_variation(seed=123)

        assert v1.volume == pytest.approx(v2.volume)
        assert v1.pitch == pytest.approx(v2.pitch)


class TestSoundEffect:
    """Tests for SoundEffect."""

    def test_create_sound(self):
        """Test creating a sound effect."""
        sound = SoundEffect(
            id="test_sound",
            name="Test Sound",
            category=SoundCategory.AMBIENCE
        )
        assert sound.id == "test_sound"
        assert sound.name == "Test Sound"
        assert sound.category == SoundCategory.AMBIENCE
        assert sound.trigger == SoundTrigger.ONESHOT

    def test_sound_with_properties(self):
        """Test sound with custom properties."""
        props = SoundProperties(volume=0.7, pitch=1.2)
        sound = SoundEffect(
            id="s1",
            name="Test",
            category=SoundCategory.FOOTSTEPS,
            trigger=SoundTrigger.RANDOM,
            properties=props,
            tags=["footstep", "wood"]
        )
        assert sound.properties.volume == 0.7
        assert sound.trigger == SoundTrigger.RANDOM
        assert "footstep" in sound.tags

    def test_to_dict(self):
        """Test serialization."""
        sound = SoundEffect(
            id="s1",
            name="Test",
            category=SoundCategory.IMPACTS,
            tags=["tag1", "tag2"]
        )
        d = sound.to_dict()
        assert d['id'] == "s1"
        assert d['category'] == "impacts"
        assert d['tags'] == ["tag1", "tag2"]

    def test_from_dict(self):
        """Test deserialization."""
        d = {
            'id': 's1',
            'name': 'Test Sound',
            'category': 'weather',
            'trigger': 'loop',
            'properties': {'volume': 0.8},
            'tags': ['rain']
        }
        sound = SoundEffect.from_dict(d)
        assert sound.id == 's1'
        assert sound.category == SoundCategory.WEATHER
        assert sound.trigger == SoundTrigger.LOOP
        assert sound.properties.volume == 0.8


class TestSoundGenerator:
    """Tests for SoundGenerator."""

    def test_generate_tone(self):
        """Test tone generation."""
        gen = SoundGenerator()
        audio = gen.generate('tone', duration_ms=500)

        assert len(audio.data) > 0
        assert audio.format == AudioFormat.RAW
        assert audio.sample_rate == 22050

    def test_generate_noise(self):
        """Test noise generation."""
        gen = SoundGenerator()
        audio = gen.generate('noise', duration_ms=500)

        assert len(audio.data) > 0

    def test_generate_footstep(self):
        """Test footstep generation."""
        gen = SoundGenerator()
        audio = gen.generate('footstep', duration_ms=200)

        assert len(audio.data) > 0

    def test_generate_rain(self):
        """Test rain generation."""
        gen = SoundGenerator()
        audio = gen.generate('rain', duration_ms=1000)

        assert len(audio.data) > 0

    def test_generate_thunder(self):
        """Test thunder generation."""
        gen = SoundGenerator()
        audio = gen.generate('thunder', duration_ms=2000)

        assert len(audio.data) > 0

    def test_generate_wind(self):
        """Test wind generation."""
        gen = SoundGenerator()
        audio = gen.generate('wind', duration_ms=1000)

        assert len(audio.data) > 0

    def test_generate_gunshot(self):
        """Test gunshot generation."""
        gen = SoundGenerator()
        audio = gen.generate('gunshot', duration_ms=500)

        assert len(audio.data) > 0

    def test_generate_heartbeat(self):
        """Test heartbeat generation."""
        gen = SoundGenerator()
        audio = gen.generate('heartbeat', duration_ms=1000)

        assert len(audio.data) > 0

    def test_generate_drip(self):
        """Test drip generation."""
        gen = SoundGenerator()
        audio = gen.generate('drip', duration_ms=300)

        assert len(audio.data) > 0

    def test_generate_creak(self):
        """Test creak generation."""
        gen = SoundGenerator()
        audio = gen.generate('creak', duration_ms=500)

        assert len(audio.data) > 0

    def test_generate_unknown_type(self):
        """Test fallback for unknown type."""
        gen = SoundGenerator()
        audio = gen.generate('unknown_type', duration_ms=500)

        # Should fall back to noise
        assert len(audio.data) > 0

    def test_seed_reproducibility(self):
        """Test seed produces reproducible output."""
        gen = SoundGenerator()

        audio1 = gen.generate('footstep', duration_ms=200, seed=42)
        audio2 = gen.generate('footstep', duration_ms=200, seed=42)

        assert audio1.data == audio2.data

    def test_different_seeds(self):
        """Test different seeds produce different output."""
        gen = SoundGenerator()

        audio1 = gen.generate('footstep', duration_ms=200, seed=100)
        audio2 = gen.generate('footstep', duration_ms=200, seed=200)

        assert audio1.data != audio2.data

    def test_duration_affects_length(self):
        """Test duration affects audio length."""
        gen = SoundGenerator()

        short = gen.generate('tone', duration_ms=100)
        long = gen.generate('tone', duration_ms=1000)

        assert len(long.data) > len(short.data)


class TestSoundInstance:
    """Tests for SoundInstance."""

    def test_create_instance(self):
        """Test creating a sound instance."""
        sound = SoundEffect(id="s1", name="Test", category=SoundCategory.AMBIENCE)
        instance = SoundInstance(
            sound=sound,
            id="inst_1",
            properties=SoundProperties()
        )
        assert instance.is_playing is True
        assert instance.is_paused is False
        assert instance.position_ms == 0.0

    def test_update_position(self):
        """Test position updates."""
        sound = SoundEffect(id="s1", name="Test", category=SoundCategory.AMBIENCE)
        instance = SoundInstance(
            sound=sound,
            id="inst_1",
            properties=SoundProperties()
        )

        instance.update(100.0)
        assert instance.position_ms == 100.0

        instance.update(50.0)
        assert instance.position_ms == 150.0

    def test_pause_stops_update(self):
        """Test pause prevents position updates."""
        sound = SoundEffect(id="s1", name="Test", category=SoundCategory.AMBIENCE)
        instance = SoundInstance(
            sound=sound,
            id="inst_1",
            properties=SoundProperties()
        )

        instance.pause()
        instance.update(100.0)
        assert instance.position_ms == 0.0

        instance.resume()
        instance.update(100.0)
        assert instance.position_ms == 100.0

    def test_stop(self):
        """Test stopping instance."""
        sound = SoundEffect(id="s1", name="Test", category=SoundCategory.AMBIENCE)
        instance = SoundInstance(
            sound=sound,
            id="inst_1",
            properties=SoundProperties()
        )

        instance.stop()
        assert instance.is_playing is False


class TestSoundMixer:
    """Tests for SoundMixer."""

    def test_create_mixer(self):
        """Test creating a mixer."""
        mixer = SoundMixer()
        assert mixer.master_volume == 1.0
        assert mixer.get_playing_count() == 0

    def test_play_sound(self):
        """Test playing a sound."""
        mixer = SoundMixer()
        sound = SoundEffect(id="s1", name="Test", category=SoundCategory.AMBIENCE)

        instance_id = mixer.play(sound)
        assert instance_id.startswith("snd_")
        assert mixer.get_playing_count() == 1

    def test_stop_sound(self):
        """Test stopping a sound."""
        mixer = SoundMixer()
        sound = SoundEffect(id="s1", name="Test", category=SoundCategory.AMBIENCE)

        instance_id = mixer.play(sound)
        mixer.stop(instance_id)
        mixer.update(0)  # Clean up stopped instances

        assert mixer.get_playing_count() == 0

    def test_stop_all(self):
        """Test stopping all sounds."""
        mixer = SoundMixer()
        sound = SoundEffect(id="s1", name="Test", category=SoundCategory.AMBIENCE)

        mixer.play(sound)
        mixer.play(sound)
        mixer.play(sound)

        assert mixer.get_playing_count() == 3

        mixer.stop_all()
        mixer.update(0)

        assert mixer.get_playing_count() == 0

    def test_stop_category(self):
        """Test stopping sounds by category."""
        mixer = SoundMixer()
        ambience = SoundEffect(id="s1", name="Ambience", category=SoundCategory.AMBIENCE)
        footstep = SoundEffect(id="s2", name="Footstep", category=SoundCategory.FOOTSTEPS)

        mixer.play(ambience)
        mixer.play(ambience)
        mixer.play(footstep)

        mixer.stop_category(SoundCategory.AMBIENCE)
        mixer.update(0)

        assert mixer.get_playing_count() == 1

    def test_category_volume(self):
        """Test category volume control."""
        mixer = SoundMixer()

        mixer.set_category_volume(SoundCategory.AMBIENCE, 0.5)
        assert mixer.get_category_volume(SoundCategory.AMBIENCE) == 0.5

        # Unset category should default to 1.0
        assert mixer.get_category_volume(SoundCategory.FOOTSTEPS) == 1.0

    def test_get_instance(self):
        """Test getting instance by ID."""
        mixer = SoundMixer()
        sound = SoundEffect(id="s1", name="Test", category=SoundCategory.AMBIENCE)

        instance_id = mixer.play(sound)
        instance = mixer.get_instance(instance_id)

        assert instance is not None
        assert instance.sound == sound

    def test_get_invalid_instance(self):
        """Test getting nonexistent instance."""
        mixer = SoundMixer()
        instance = mixer.get_instance("nonexistent")
        assert instance is None

    def test_update_removes_stopped(self):
        """Test update removes stopped instances."""
        mixer = SoundMixer()
        sound = SoundEffect(id="s1", name="Test", category=SoundCategory.AMBIENCE)

        instance_id = mixer.play(sound)

        # Initially playing
        assert mixer.get_playing_count() == 1

        # Stop the instance
        instance = mixer.get_instance(instance_id)
        instance.stop()

        # After stop, is_playing is False so count is 0
        # But instance is still tracked until update cleans it
        assert instance.is_playing is False

        # After update, the stopped instance should be removed
        mixer.update(100)

        # Instance should no longer be retrievable
        assert mixer.get_instance(instance_id) is None

    def test_custom_properties(self):
        """Test playing with custom properties."""
        mixer = SoundMixer()
        sound = SoundEffect(
            id="s1",
            name="Test",
            category=SoundCategory.AMBIENCE,
            properties=SoundProperties(volume=1.0)
        )

        custom_props = SoundProperties(volume=0.5, pitch=1.2)
        instance_id = mixer.play(sound, properties=custom_props)
        instance = mixer.get_instance(instance_id)

        assert instance.properties.volume == 0.5
        assert instance.properties.pitch == 1.2
