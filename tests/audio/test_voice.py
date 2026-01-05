"""Tests for the voice system."""

import pytest
from src.shadowengine.audio.voice import (
    CharacterVoice,
    VoiceParameters,
    VoiceGender,
    VoiceAge,
    Accent,
    EmotionalState,
    VoiceFactory,
    ARCHETYPE_VOICE_TEMPLATES,
    EMOTION_MODULATIONS
)


class TestVoiceParameters:
    """Tests for VoiceParameters."""

    def test_default_parameters(self):
        """Test default parameter values."""
        params = VoiceParameters()
        assert params.pitch == 0.5
        assert params.speed == 0.5
        assert params.volume == 0.8
        assert params.breathiness == 0.2
        assert params.roughness == 0.1

    def test_parameter_clamping(self):
        """Test that parameters are clamped to valid range."""
        params = VoiceParameters(pitch=1.5, speed=-0.5, volume=2.0)
        assert params.pitch == 1.0
        assert params.speed == 0.0
        assert params.volume == 1.0

    def test_to_dict(self):
        """Test serialization to dictionary."""
        params = VoiceParameters(pitch=0.3, speed=0.7)
        d = params.to_dict()
        assert d['pitch'] == 0.3
        assert d['speed'] == 0.7

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        d = {'pitch': 0.4, 'speed': 0.6, 'breathiness': 0.3}
        params = VoiceParameters.from_dict(d)
        assert params.pitch == 0.4
        assert params.speed == 0.6
        assert params.breathiness == 0.3

    def test_blend(self):
        """Test blending two parameter sets."""
        params1 = VoiceParameters(pitch=0.0, speed=1.0)
        params2 = VoiceParameters(pitch=1.0, speed=0.0)

        blended = params1.blend(params2, 0.5)
        assert blended.pitch == pytest.approx(0.5)
        assert blended.speed == pytest.approx(0.5)

    def test_blend_factor_extremes(self):
        """Test blend at factor extremes."""
        params1 = VoiceParameters(pitch=0.2)
        params2 = VoiceParameters(pitch=0.8)

        assert params1.blend(params2, 0.0).pitch == pytest.approx(0.2)
        assert params1.blend(params2, 1.0).pitch == pytest.approx(0.8)


class TestCharacterVoice:
    """Tests for CharacterVoice."""

    def test_create_voice(self):
        """Test creating a character voice."""
        voice = CharacterVoice(
            character_id="char_001",
            name="Detective Smith"
        )
        assert voice.character_id == "char_001"
        assert voice.name == "Detective Smith"
        assert voice.gender == VoiceGender.NEUTRAL
        assert voice.emotional_state == EmotionalState.NEUTRAL

    def test_voice_with_parameters(self):
        """Test voice with custom parameters."""
        params = VoiceParameters(pitch=0.3, roughness=0.4)
        voice = CharacterVoice(
            character_id="char_002",
            name="Gangster Tony",
            gender=VoiceGender.MALE,
            age=VoiceAge.ADULT,
            accent=Accent.BROOKLYN,
            base_params=params
        )
        assert voice.base_params.pitch == 0.3
        assert voice.base_params.roughness == 0.4
        assert voice.accent == Accent.BROOKLYN

    def test_set_emotion(self):
        """Test setting emotional state."""
        voice = CharacterVoice(character_id="c1", name="Test")
        voice.set_emotion(EmotionalState.ANGRY, 0.8)
        assert voice.emotional_state == EmotionalState.ANGRY
        assert voice.emotion_intensity == 0.8

    def test_emotion_intensity_clamping(self):
        """Test emotion intensity is clamped."""
        voice = CharacterVoice(character_id="c1", name="Test")
        voice.set_emotion(EmotionalState.FEARFUL, 1.5)
        assert voice.emotion_intensity == 1.0

        voice.set_emotion(EmotionalState.SAD, -0.5)
        assert voice.emotion_intensity == 0.0

    def test_get_effective_params_neutral(self):
        """Test effective params with neutral emotion."""
        voice = CharacterVoice(
            character_id="c1",
            name="Test",
            base_params=VoiceParameters(pitch=0.5)
        )
        params = voice.get_effective_params()
        assert params.pitch == pytest.approx(0.5, abs=0.01)

    def test_get_effective_params_emotional(self):
        """Test effective params with emotional modulation."""
        voice = CharacterVoice(
            character_id="c1",
            name="Test",
            base_params=VoiceParameters(pitch=0.5, speed=0.5)
        )
        voice.set_emotion(EmotionalState.ANGRY, 1.0)
        params = voice.get_effective_params()

        # Angry should increase roughness and emphasis
        assert params.roughness > voice.base_params.roughness
        assert params.emphasis_strength > voice.base_params.emphasis_strength

    def test_serialization(self):
        """Test voice serialization round-trip."""
        original = CharacterVoice(
            character_id="c1",
            name="Test Voice",
            gender=VoiceGender.FEMALE,
            age=VoiceAge.YOUNG,
            accent=Accent.SOUTHERN,
            base_params=VoiceParameters(pitch=0.6, breathiness=0.3),
            speech_quirks=["drawl", "elongation"],
            catchphrases=["Well, I declare..."]
        )
        original.set_emotion(EmotionalState.HAPPY, 0.7)

        d = original.to_dict()
        restored = CharacterVoice.from_dict(d)

        assert restored.character_id == original.character_id
        assert restored.name == original.name
        assert restored.gender == original.gender
        assert restored.age == original.age
        assert restored.accent == original.accent
        assert restored.base_params.pitch == pytest.approx(original.base_params.pitch)
        assert restored.emotional_state == original.emotional_state
        assert restored.speech_quirks == original.speech_quirks


class TestVoiceFactory:
    """Tests for VoiceFactory."""

    def test_create_from_archetype_detective(self):
        """Test creating detective voice."""
        voice = VoiceFactory.create_from_archetype(
            "det_001", "Sam Spade", "detective", seed=42
        )
        assert voice.character_id == "det_001"
        assert voice.name == "Sam Spade"
        assert voice.gender == VoiceGender.MALE
        assert voice.age == VoiceAge.MIDDLE

    def test_create_from_archetype_femme_fatale(self):
        """Test creating femme fatale voice."""
        voice = VoiceFactory.create_from_archetype(
            "ff_001", "Veronica Lake", "femme_fatale", seed=42
        )
        assert voice.gender == VoiceGender.FEMALE
        assert voice.age == VoiceAge.YOUNG
        assert voice.base_params.breathiness > 0.3

    def test_create_from_archetype_gangster(self):
        """Test creating gangster voice."""
        voice = VoiceFactory.create_from_archetype(
            "gang_001", "Big Tony", "gangster", seed=42
        )
        assert voice.accent == Accent.BROOKLYN
        assert voice.base_params.roughness > 0.2

    def test_create_from_unknown_archetype(self):
        """Test fallback for unknown archetype."""
        voice = VoiceFactory.create_from_archetype(
            "unk_001", "Unknown", "nonexistent_archetype", seed=42
        )
        # Should use default template
        assert voice.character_id == "unk_001"

    def test_create_random(self):
        """Test creating random voice."""
        voice = VoiceFactory.create_random("rand_001", "Random Character", seed=42)
        assert voice.character_id == "rand_001"
        # Should have some variation from defaults
        assert voice.gender in list(VoiceGender)
        assert voice.age in list(VoiceAge)

    def test_seed_reproducibility(self):
        """Test that seed produces reproducible results."""
        voice1 = VoiceFactory.create_from_archetype("c1", "Test", "detective", seed=123)
        voice2 = VoiceFactory.create_from_archetype("c1", "Test", "detective", seed=123)

        assert voice1.base_params.pitch == pytest.approx(voice2.base_params.pitch)
        assert voice1.base_params.speed == pytest.approx(voice2.base_params.speed)

    def test_different_seeds_different_voices(self):
        """Test that different seeds produce different voices."""
        voice1 = VoiceFactory.create_random("c1", "Test", seed=100)
        voice2 = VoiceFactory.create_random("c1", "Test", seed=200)

        # At least some parameters should differ
        params_differ = (
            voice1.base_params.pitch != voice2.base_params.pitch or
            voice1.base_params.speed != voice2.base_params.speed or
            voice1.gender != voice2.gender
        )
        assert params_differ


class TestArchetypeTemplates:
    """Tests for archetype voice templates."""

    def test_all_archetypes_exist(self):
        """Test that expected archetypes are defined."""
        expected = [
            'default', 'detective', 'femme_fatale', 'gangster',
            'informant', 'bartender', 'politician', 'elderly_witness',
            'street_kid', 'corrupt_cop', 'nightclub_singer'
        ]
        for archetype in expected:
            assert archetype in ARCHETYPE_VOICE_TEMPLATES

    def test_template_has_required_fields(self):
        """Test templates have minimum required fields."""
        for name, template in ARCHETYPE_VOICE_TEMPLATES.items():
            assert 'pitch' in template, f"{name} missing pitch"
            assert 'speed' in template, f"{name} missing speed"
            assert 'breathiness' in template, f"{name} missing breathiness"
            assert 'roughness' in template, f"{name} missing roughness"

    def test_template_values_in_range(self):
        """Test template values are in valid range."""
        for name, template in ARCHETYPE_VOICE_TEMPLATES.items():
            assert 0 <= template['pitch'] <= 1, f"{name} pitch out of range"
            assert 0 <= template['speed'] <= 1, f"{name} speed out of range"


class TestEmotionModulations:
    """Tests for emotion modulation values."""

    def test_all_emotions_have_modulation(self):
        """Test all emotions have modulation defined."""
        for emotion in EmotionalState:
            assert emotion in EMOTION_MODULATIONS

    def test_neutral_is_empty(self):
        """Test neutral emotion has no modulation."""
        assert EMOTION_MODULATIONS[EmotionalState.NEUTRAL] == {}

    def test_modulation_values_reasonable(self):
        """Test modulation values are within reasonable range."""
        for emotion, mods in EMOTION_MODULATIONS.items():
            for param, value in mods.items():
                assert -0.5 <= value <= 0.5, f"{emotion}.{param} = {value} out of range"
