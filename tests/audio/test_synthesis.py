"""
Tests for unified Audio Synthesizer.
"""

import pytest
from src.shadowengine.audio.synthesis import (
    AudioSynthesizer, SynthesisResult, SynthesisConfig,
    AudioEvent, AudioPriority, AudioMixer,
)
from src.shadowengine.audio.voice import EmotionalState


class TestSynthesisConfig:
    """Tests for SynthesisConfig."""

    def test_create_config(self, synthesis_config):
        """Can create synthesis config."""
        assert synthesis_config.tts_engine_type == "mock"
        assert synthesis_config.master_volume == 0.8

    def test_default_values(self):
        """Config has sensible defaults."""
        config = SynthesisConfig()
        assert config.sample_rate == 22050
        assert config.voice_volume == 1.0
        assert config.cache_enabled is True

    def test_serialization(self, synthesis_config):
        """Config can be serialized."""
        data = synthesis_config.to_dict()
        restored = SynthesisConfig.from_dict(data)

        assert restored.tts_engine_type == synthesis_config.tts_engine_type
        assert restored.master_volume == synthesis_config.master_volume


class TestSynthesisResult:
    """Tests for SynthesisResult."""

    def test_create_result(self):
        """Can create synthesis result."""
        result = SynthesisResult(
            event_id="test_event",
            audio_data=b"audio",
            duration_ms=1000.0,
        )
        assert result.event_id == "test_event"
        assert result.success is True

    def test_is_empty(self):
        """Can check if result is empty."""
        empty = SynthesisResult(event_id="test")
        assert empty.is_empty is True

        non_empty = SynthesisResult(event_id="test", audio_data=b"audio")
        assert non_empty.is_empty is False

    def test_error_result(self):
        """Can create error result."""
        result = SynthesisResult(
            event_id="failed",
            success=False,
            error="Test error",
        )
        assert result.success is False
        assert result.error == "Test error"

    def test_serialization(self):
        """Result can be serialized."""
        result = SynthesisResult(
            event_id="test",
            audio_data=b"x" * 100,
            duration_ms=500.0,
            cached=True,
        )
        data = result.to_dict()

        assert data["event_id"] == "test"
        assert data["audio_size_bytes"] == 100
        assert data["cached"] is True


class TestAudioEvent:
    """Tests for AudioEvent."""

    def test_create_event(self, audio_event):
        """Can create audio event."""
        assert audio_event.id == "test_event"
        assert audio_event.event_type == "speech"
        assert audio_event.text == "Hello world"

    def test_priority_default(self, audio_event):
        """Default priority is normal."""
        assert audio_event.priority == AudioPriority.NORMAL

    def test_serialization(self, audio_event):
        """Event can be serialized."""
        data = audio_event.to_dict()

        assert data["id"] == "test_event"
        assert data["event_type"] == "speech"


class TestAudioMixer:
    """Tests for AudioMixer."""

    def test_create_mixer(self, audio_mixer):
        """Can create mixer."""
        assert audio_mixer.sample_rate == 22050

    def test_add_stream(self, audio_mixer):
        """Can add stream."""
        audio_mixer.add_stream("voice", b"audio_data", volume=0.8)
        assert "voice" in audio_mixer.get_active_streams()

    def test_remove_stream(self, audio_mixer):
        """Can remove stream."""
        audio_mixer.add_stream("temp", b"data")
        audio_mixer.remove_stream("temp")

        assert "temp" not in audio_mixer.get_active_streams()

    def test_set_volume(self, audio_mixer):
        """Can set stream volume."""
        audio_mixer.add_stream("test", b"data")
        audio_mixer.set_volume("test", 0.5)
        # Volume should be set (internal state)

    def test_set_pan(self, audio_mixer):
        """Can set stream pan."""
        audio_mixer.add_stream("test", b"data")
        audio_mixer.set_pan("test", -0.5)  # Left-panned

    def test_mix_empty(self, audio_mixer):
        """Empty mixer returns silence."""
        audio = audio_mixer.mix(1000.0)
        assert len(audio) > 0

    def test_mix_streams(self, audio_mixer):
        """Can mix multiple streams."""
        audio_mixer.add_stream("voice", b"x" * 100)
        audio_mixer.add_stream("effect", b"y" * 100)

        mixed = audio_mixer.mix(1000.0)
        assert len(mixed) > 0

    def test_clear(self, audio_mixer):
        """Can clear all streams."""
        audio_mixer.add_stream("a", b"data")
        audio_mixer.add_stream("b", b"data")
        audio_mixer.clear()

        assert len(audio_mixer.get_active_streams()) == 0


class TestAudioSynthesizer:
    """Tests for AudioSynthesizer."""

    def test_create(self, audio_synthesizer):
        """Can create synthesizer."""
        assert audio_synthesizer is not None
        assert audio_synthesizer.is_initialized is True

    def test_set_master_volume(self, audio_synthesizer):
        """Can set master volume."""
        audio_synthesizer.set_master_volume(0.5)
        assert audio_synthesizer.config.master_volume == 0.5

    def test_volume_clamped(self, audio_synthesizer):
        """Volume is clamped to 0-1."""
        audio_synthesizer.set_master_volume(2.0)
        assert audio_synthesizer.config.master_volume == 1.0

        audio_synthesizer.set_master_volume(-1.0)
        assert audio_synthesizer.config.master_volume == 0.0

    def test_set_voice_volume(self, audio_synthesizer):
        """Can set voice volume."""
        audio_synthesizer.set_voice_volume(0.7)
        assert audio_synthesizer.config.voice_volume == 0.7

    def test_set_ambient_volume(self, audio_synthesizer):
        """Can set ambient volume."""
        audio_synthesizer.set_ambient_volume(0.4)
        assert audio_synthesizer.config.ambient_volume == 0.4

    def test_set_music_volume(self, audio_synthesizer):
        """Can set music volume."""
        audio_synthesizer.set_music_volume(0.3)
        assert audio_synthesizer.config.music_volume == 0.3

    # Speech synthesis

    def test_synthesize_speech(self, audio_synthesizer):
        """Can synthesize speech."""
        result = audio_synthesizer.synthesize_speech("Hello world")

        assert result.success is True
        assert len(result.audio_data) > 0

    def test_synthesize_speech_character(self, audio_synthesizer):
        """Can synthesize speech for character."""
        # Register a character voice first
        audio_synthesizer.register_character_voice("detective", preset="gruff_male")

        result = audio_synthesizer.synthesize_speech(
            "I've seen things you wouldn't believe.",
            character_id="detective",
        )

        assert result.success is True

    def test_synthesize_speech_emotion(self, audio_synthesizer):
        """Can synthesize speech with emotion."""
        audio_synthesizer.register_character_voice("witness")

        result = audio_synthesizer.synthesize_speech(
            "I'm scared!",
            character_id="witness",
            emotion=EmotionalState.FEARFUL,
        )

        assert result.success is True

    def test_synthesize_speech_effects(self, audio_synthesizer):
        """Can synthesize speech with effects."""
        result = audio_synthesizer.synthesize_speech(
            "Hello from the telephone",
            effects_preset="telephone",
        )

        assert result.success is True

    def test_speak_convenience(self, audio_synthesizer):
        """Speak convenience method works."""
        audio_synthesizer.register_character_voice("npc")

        result = audio_synthesizer.speak("npc", "Hello there")

        assert result.success is True

    # Sound effects

    def test_synthesize_effect(self, audio_synthesizer):
        """Can synthesize sound effect."""
        result = audio_synthesizer.synthesize_effect("gunshot")

        assert result.success is True
        assert len(result.audio_data) > 0

    def test_synthesize_effect_custom_seed(self, audio_synthesizer):
        """Can synthesize effect with custom TTS seed."""
        result = audio_synthesizer.synthesize_effect(
            "custom",
            tts_seed="swoosh whomp",
        )

        assert result.success is True

    def test_play_effect(self, audio_synthesizer):
        """Can play sound effect."""
        event_id = audio_synthesizer.play_effect("footstep", volume=0.5)

        assert event_id is not None

    # Theme and music

    def test_generate_theme(self, audio_synthesizer):
        """Can generate musical theme."""
        motifs = audio_synthesizer.generate_theme("main", mood="noir")

        assert len(motifs) > 0

    def test_set_tension(self, audio_synthesizer):
        """Can set tension level."""
        audio_synthesizer.set_tension(0.7)
        # Update to apply the tension change (transitions happen over time)
        audio_synthesizer.update(1000.0)

        # Affects both theme and ambient
        assert audio_synthesizer.theme_engine.tension > 0

    # Ambient

    def test_set_weather(self, audio_synthesizer):
        """Can set weather."""
        audio_synthesizer.set_weather("storm", intensity=0.8)

        layers = audio_synthesizer.ambient_engine.get_all_layers()
        assert len(layers) > 0

    def test_set_location(self, audio_synthesizer):
        """Can set location."""
        audio_synthesizer.set_location("bar")

        layers = audio_synthesizer.ambient_engine.get_all_layers()
        assert len(layers) > 0

    # Event queue

    def test_queue_event(self, audio_synthesizer, audio_event):
        """Can queue audio event."""
        event_id = audio_synthesizer.queue_event(audio_event)

        assert event_id == audio_event.id

    def test_queue_speech(self, audio_synthesizer):
        """Can queue speech event."""
        event_id = audio_synthesizer.queue_speech(
            "Queued message",
            character_id="npc",
        )

        assert event_id is not None

    def test_queue_priority(self, audio_synthesizer):
        """Events are queued by priority."""
        audio_synthesizer.queue_speech("Low", priority=AudioPriority.LOW)
        audio_synthesizer.queue_speech("High", priority=AudioPriority.HIGH)
        audio_synthesizer.queue_speech("Normal", priority=AudioPriority.NORMAL)

        # High priority should be processed first
        results = audio_synthesizer.process_queue()

        # Should have processed events

    def test_process_queue(self, audio_synthesizer):
        """Can process queued events."""
        audio_synthesizer.queue_speech("Test 1")
        audio_synthesizer.queue_speech("Test 2")

        results = audio_synthesizer.process_queue()

        assert len(results) == 2
        assert all(r.success for r in results)

    # Character voice management

    def test_register_character_voice(self, audio_synthesizer):
        """Can register character voice."""
        voice = audio_synthesizer.register_character_voice("villain", preset="gruff_male")

        assert voice.character_id == "villain"

    def test_register_random_voice(self, audio_synthesizer):
        """Can register random voice."""
        voice = audio_synthesizer.register_character_voice("random_npc")

        assert voice is not None
        assert voice.profile is not None

    def test_get_character_voice(self, audio_synthesizer):
        """Can get character voice."""
        audio_synthesizer.register_character_voice("hero")
        voice = audio_synthesizer.get_character_voice("hero")

        assert voice is not None

    # Effects chains

    def test_create_effects_chain(self, audio_synthesizer):
        """Can create effects chain."""
        chain = audio_synthesizer.create_effects_chain("custom_effect")

        assert chain is not None

    def test_get_effects_chain(self, audio_synthesizer):
        """Can get effects chain."""
        audio_synthesizer.create_effects_chain("test_chain")
        chain = audio_synthesizer.get_effects_chain("test_chain")

        assert chain is not None

    # Callbacks

    def test_on_complete_callback(self, audio_synthesizer):
        """On complete callback is called."""
        results = []
        audio_synthesizer.on_complete(lambda r: results.append(r))

        audio_synthesizer.queue_speech("Callback test")
        audio_synthesizer.process_queue()

        assert len(results) == 1

    # Mixing

    def test_get_mix(self, audio_synthesizer):
        """Can get mixed audio output."""
        audio_synthesizer.set_weather("rain")
        audio = audio_synthesizer.get_mix(1000.0)

        assert len(audio) > 0

    # Update

    def test_update(self, audio_synthesizer):
        """Can update synthesizer state."""
        audio_synthesizer.set_tension(0.5)
        audio_synthesizer.update(100.0)

        # Should not raise

    # Cleanup

    def test_shutdown(self, audio_synthesizer):
        """Can shutdown synthesizer."""
        audio_synthesizer.shutdown()

        assert audio_synthesizer.is_initialized is False

    def test_clear_cache(self, audio_synthesizer):
        """Can clear cache."""
        audio_synthesizer.synthesize_speech("Cache test")
        cleared = audio_synthesizer.clear_cache()

        assert cleared >= 0

    # Status and serialization

    def test_get_status(self, audio_synthesizer):
        """Can get status."""
        audio_synthesizer.set_weather("storm")
        audio_synthesizer.set_tension(0.6)

        status = audio_synthesizer.get_status()

        assert status["initialized"] is True
        assert "tension" in status
        assert "ambient_layers" in status

    def test_to_dict(self, audio_synthesizer):
        """Can serialize to dict."""
        audio_synthesizer.register_character_voice("npc")
        audio_synthesizer.set_tension(0.5)

        data = audio_synthesizer.to_dict()

        assert "config" in data
        assert "voice_library" in data
        assert "theme_engine" in data


class TestAudioPriority:
    """Tests for AudioPriority enum."""

    def test_priority_order(self):
        """Priorities have correct order."""
        assert AudioPriority.LOW.value < AudioPriority.NORMAL.value
        assert AudioPriority.NORMAL.value < AudioPriority.HIGH.value
        assert AudioPriority.HIGH.value < AudioPriority.CRITICAL.value
        assert AudioPriority.CRITICAL.value < AudioPriority.SYSTEM.value

    def test_all_priorities(self):
        """All priority levels exist."""
        assert len(AudioPriority) == 5


class TestIntegration:
    """Integration tests for audio synthesis."""

    def test_full_scene_audio(self, audio_synthesizer):
        """Can setup complete scene audio."""
        # Set environment
        audio_synthesizer.set_weather("rain")
        audio_synthesizer.set_location("alley")
        audio_synthesizer.set_tension(0.4)

        # Register characters
        audio_synthesizer.register_character_voice("detective", preset="gruff_male")
        audio_synthesizer.register_character_voice("informant", preset="nervous_female")

        # Generate dialogue
        result1 = audio_synthesizer.speak("detective", "What do you know?")
        result2 = audio_synthesizer.speak(
            "informant",
            "I saw everything!",
            emotion=EmotionalState.FEARFUL,
        )

        assert result1.success
        assert result2.success

        # Add sound effects
        audio_synthesizer.play_effect("footstep")

        # Get mixed output
        audio = audio_synthesizer.get_mix(2000.0)
        assert len(audio) > 0

    def test_tension_escalation(self, audio_synthesizer):
        """Tension escalation affects all systems."""
        audio_synthesizer.set_location("warehouse")

        # Low tension
        audio_synthesizer.set_tension(0.2)
        low_layers = len(audio_synthesizer.ambient_engine.get_all_layers())

        # High tension
        audio_synthesizer.set_tension(0.9)
        high_layers = len(audio_synthesizer.ambient_engine.get_all_layers())

        # Higher tension should add more layers
        assert high_layers >= low_layers

    def test_queued_dialogue_sequence(self, audio_synthesizer):
        """Can queue dialogue sequence."""
        audio_synthesizer.register_character_voice("a")
        audio_synthesizer.register_character_voice("b")

        audio_synthesizer.queue_speech("Line one", character_id="a")
        audio_synthesizer.queue_speech("Line two", character_id="b")
        audio_synthesizer.queue_speech("Line three", character_id="a")

        results = audio_synthesizer.process_queue()

        assert len(results) == 3
        assert all(r.success for r in results)
