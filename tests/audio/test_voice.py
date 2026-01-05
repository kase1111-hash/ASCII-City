"""
Tests for Voice Personality system.
"""

import pytest
from src.shadowengine.audio.voice import (
    VoiceProfile, VoiceParameter, EmotionalState,
    VoiceModulator, VoiceLibrary, CharacterVoice,
    EMOTION_MODIFIERS,
)


class TestVoiceParameter:
    """Tests for VoiceParameter."""

    def test_create_parameter(self):
        """Can create voice parameter."""
        param = VoiceParameter(
            name="pitch",
            value=0.5,
            min_value=-1.0,
            max_value=1.0,
        )
        assert param.name == "pitch"
        assert param.value == 0.5

    def test_clamp_value(self):
        """Value is clamped to range."""
        param = VoiceParameter("test", value=2.0, max_value=1.0)
        assert param.value == 1.0

        param = VoiceParameter("test", value=-2.0, min_value=-1.0)
        assert param.value == -1.0

    def test_normalize(self):
        """Can normalize value to 0-1 range."""
        param = VoiceParameter("test", value=0.0, min_value=-1.0, max_value=1.0)
        assert param.normalize() == 0.5

        param = VoiceParameter("test", value=1.0, min_value=0.0, max_value=1.0)
        assert param.normalize() == 1.0

    def test_apply_modifier(self):
        """Can apply modifier to value."""
        param = VoiceParameter("test", value=0.5, min_value=0.0, max_value=1.0)

        new_value = param.apply_modifier(0.3)
        assert new_value == 0.8

        # Clamped to max
        new_value = param.apply_modifier(0.7)
        assert new_value == 1.0

    def test_serialization(self):
        """Parameter can be serialized."""
        param = VoiceParameter("pitch", 0.5, -1.0, 1.0, default=0.0)
        data = param.to_dict()

        assert data["name"] == "pitch"
        assert data["value"] == 0.5
        assert data["default"] == 0.0


class TestVoiceProfile:
    """Tests for VoiceProfile."""

    def test_create_profile(self, voice_profile):
        """Can create voice profile."""
        assert voice_profile.voice_id == "test_voice"
        assert voice_profile.base_voice == "male_1"
        assert voice_profile.pitch == 0.0

    def test_pitch_multiplier(self):
        """Can get pitch multiplier."""
        profile = VoiceProfile(voice_id="test", pitch=0.0)
        assert profile.get_pitch_multiplier() == 1.0

        profile = VoiceProfile(voice_id="test", pitch=1.0)
        assert profile.get_pitch_multiplier() == 1.5

        profile = VoiceProfile(voice_id="test", pitch=-1.0)
        assert profile.get_pitch_multiplier() == 0.5

    def test_speed_multiplier(self):
        """Can get speed multiplier."""
        profile = VoiceProfile(voice_id="test", speed=0.0)
        assert profile.get_speed_multiplier() == 1.0

        profile = VoiceProfile(voice_id="test", speed=0.5)
        assert profile.get_speed_multiplier() == 1.25

    def test_get_parameters(self, voice_profile):
        """Can get all parameters."""
        params = voice_profile.get_parameters()

        assert "pitch" in params
        assert "speed" in params
        assert "breathiness" in params
        assert "roughness" in params

    def test_apply_emotion(self, voice_profile):
        """Can apply emotional state."""
        happy_profile = voice_profile.apply_emotion(EmotionalState.HAPPY)

        # Happy should increase pitch
        assert happy_profile.pitch > voice_profile.pitch

    def test_apply_emotion_angry(self, voice_profile):
        """Angry emotion affects voice correctly."""
        angry_profile = voice_profile.apply_emotion(EmotionalState.ANGRY)

        # Angry should increase roughness
        assert angry_profile.roughness > voice_profile.roughness

    def test_apply_emotion_sad(self, voice_profile):
        """Sad emotion affects voice correctly."""
        sad_profile = voice_profile.apply_emotion(EmotionalState.SAD)

        # Sad should lower pitch and speed
        assert sad_profile.pitch < voice_profile.pitch
        assert sad_profile.speed < voice_profile.speed

    def test_emotional_range_scaling(self):
        """Emotional range scales effect of emotions."""
        low_range = VoiceProfile(voice_id="test", emotional_range=0.2)
        high_range = VoiceProfile(voice_id="test", emotional_range=1.0)

        low_happy = low_range.apply_emotion(EmotionalState.HAPPY)
        high_happy = high_range.apply_emotion(EmotionalState.HAPPY)

        # Higher range = bigger pitch change
        assert abs(high_happy.pitch) > abs(low_happy.pitch)

    def test_serialization(self, gruff_voice_profile):
        """Profile can be serialized and deserialized."""
        data = gruff_voice_profile.to_dict()
        restored = VoiceProfile.from_dict(data)

        assert restored.voice_id == gruff_voice_profile.voice_id
        assert restored.pitch == gruff_voice_profile.pitch
        assert restored.roughness == gruff_voice_profile.roughness


class TestCharacterVoice:
    """Tests for CharacterVoice."""

    def test_create_character_voice(self, character_voice):
        """Can create character voice."""
        assert character_voice.character_id == "test_char"
        assert character_voice.profile is not None

    def test_set_emotion(self, character_voice):
        """Can set emotion."""
        character_voice.set_emotion(EmotionalState.FEARFUL)
        assert character_voice.current_emotion == EmotionalState.FEARFUL

    def test_get_effective_profile(self, character_voice):
        """Can get effective profile with emotion applied."""
        character_voice.set_emotion(EmotionalState.NERVOUS)
        profile = character_voice.get_effective_profile()

        # Nervous should be reflected in profile
        assert profile.pitch > character_voice.profile.pitch

    def test_apply_stress(self, character_voice):
        """Can apply stress."""
        character_voice.apply_stress(0.5)
        assert character_voice.stress_level == 0.5

        # Stress affects effective profile
        profile = character_voice.get_effective_profile()
        assert profile.pitch > character_voice.profile.pitch

    def test_stress_clamped(self, character_voice):
        """Stress is clamped to 0-1."""
        character_voice.apply_stress(2.0)
        assert character_voice.stress_level == 1.0

        character_voice.apply_stress(-2.0)
        assert character_voice.stress_level == 0.0

    def test_apply_fatigue(self, character_voice):
        """Can apply fatigue."""
        character_voice.apply_fatigue(0.7)
        assert character_voice.fatigue_level == 0.7

        # Fatigue should slow down speech
        profile = character_voice.get_effective_profile()
        assert profile.speed < character_voice.profile.speed

    def test_recover(self, character_voice):
        """Can recover from stress and fatigue."""
        character_voice.apply_stress(0.8)
        character_voice.apply_fatigue(0.6)

        character_voice.recover(0.3)

        assert character_voice.stress_level == 0.5
        assert character_voice.fatigue_level == 0.3

    def test_serialization(self, character_voice):
        """Character voice can be serialized."""
        character_voice.set_emotion(EmotionalState.ANGRY)
        character_voice.apply_stress(0.4)

        data = character_voice.to_dict()
        restored = CharacterVoice.from_dict(data)

        assert restored.character_id == character_voice.character_id
        assert restored.current_emotion == EmotionalState.ANGRY
        assert restored.stress_level == 0.4


class TestVoiceModulator:
    """Tests for VoiceModulator."""

    def test_create_modulator(self, voice_modulator):
        """Can create modulator."""
        assert voice_modulator is not None

    def test_natural_variation(self, voice_modulator, voice_profile):
        """Can add natural variation."""
        varied = voice_modulator.add_natural_variation(voice_profile, 0.1)

        # Should be slightly different
        assert varied.pitch != voice_profile.pitch or varied.speed != voice_profile.speed

    def test_deterministic_variation(self, voice_profile):
        """Same seed produces same variation."""
        mod1 = VoiceModulator(seed=100)
        mod2 = VoiceModulator(seed=100)

        varied1 = mod1.add_natural_variation(voice_profile)
        varied2 = mod2.add_natural_variation(voice_profile)

        assert varied1.pitch == varied2.pitch

    def test_apply_whisper(self, voice_modulator, voice_profile):
        """Can apply whisper effect."""
        whispered = voice_modulator.apply_whisper(voice_profile)

        assert whispered.breathiness == 1.0
        assert whispered.pitch > voice_profile.pitch

    def test_apply_shout(self, voice_modulator, voice_profile):
        """Can apply shout effect."""
        shouted = voice_modulator.apply_shout(voice_profile)

        assert shouted.pitch > voice_profile.pitch
        assert shouted.roughness > voice_profile.roughness

    def test_age_voice_older(self, voice_modulator, voice_profile):
        """Can age voice older."""
        aged = voice_modulator.age_voice(voice_profile, 30)

        assert aged.pitch < voice_profile.pitch
        assert aged.speed < voice_profile.speed

    def test_age_voice_younger(self, voice_modulator, voice_profile):
        """Can de-age voice."""
        young = voice_modulator.age_voice(voice_profile, -20)

        assert young.pitch > voice_profile.pitch


class TestVoiceLibrary:
    """Tests for VoiceLibrary."""

    def test_create_library(self, voice_library):
        """Can create library."""
        assert voice_library is not None

    def test_has_presets(self, voice_library):
        """Library has presets."""
        presets = voice_library.get_preset_names()
        assert len(presets) >= 5
        assert "gruff_male" in presets
        assert "young_female" in presets

    def test_get_preset(self, voice_library):
        """Can get preset profile."""
        profile = voice_library.get_preset("gruff_male")
        assert profile is not None
        assert profile.roughness > 0

    def test_register_profile(self, voice_library, voice_profile):
        """Can register custom profile."""
        voice_library.register_profile(voice_profile)

        retrieved = voice_library.get_profile("test_voice")
        assert retrieved is not None
        assert retrieved.voice_id == "test_voice"

    def test_create_character_voice(self, voice_library, voice_profile):
        """Can create character voice from profile."""
        voice = voice_library.create_character_voice("detective", voice_profile)

        assert voice.character_id == "detective"
        assert voice.profile == voice_profile

    def test_get_character_voice(self, voice_library, voice_profile):
        """Can retrieve character voice."""
        voice_library.create_character_voice("suspect", voice_profile)

        voice = voice_library.get_character_voice("suspect")
        assert voice is not None
        assert voice.character_id == "suspect"

    def test_generate_random_profile(self, voice_library):
        """Can generate random profile."""
        profile = voice_library.generate_random_profile(seed=42)
        assert profile is not None
        assert profile.voice_id.startswith("random_")

    def test_generate_random_gender(self, voice_library):
        """Can generate random profile with gender."""
        male_profile = voice_library.generate_random_profile(seed=42, gender="male")
        assert male_profile.base_voice in ["male_1", "male_2"]

        female_profile = voice_library.generate_random_profile(seed=42, gender="female")
        assert female_profile.base_voice in ["female_1", "female_2"]

    def test_deterministic_random(self, voice_library):
        """Random profiles are deterministic with same seed."""
        profile1 = voice_library.generate_random_profile(seed=123)
        profile2 = voice_library.generate_random_profile(seed=123)

        assert profile1.pitch == profile2.pitch
        assert profile1.base_voice == profile2.base_voice

    def test_serialization(self, voice_library, voice_profile):
        """Library can be serialized."""
        voice_library.register_profile(voice_profile)
        voice_library.create_character_voice("npc", voice_profile)

        data = voice_library.to_dict()
        restored = VoiceLibrary.from_dict(data)

        assert restored.get_profile("test_voice") is not None
        assert restored.get_character_voice("npc") is not None


class TestEmotionModifiers:
    """Tests for emotion modifier constants."""

    def test_all_emotions_have_modifiers(self):
        """All emotional states have defined modifiers."""
        for emotion in EmotionalState:
            assert emotion in EMOTION_MODIFIERS

    def test_neutral_has_no_effect(self):
        """Neutral emotion has no modifiers."""
        assert EMOTION_MODIFIERS[EmotionalState.NEUTRAL] == {}

    def test_emotional_modifiers_in_range(self):
        """All modifier values are in reasonable range."""
        for emotion, modifiers in EMOTION_MODIFIERS.items():
            for key, value in modifiers.items():
                assert -1.0 <= value <= 1.0, f"{emotion}.{key} = {value} out of range"
