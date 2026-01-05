"""
End-to-end pipeline tests for the Audio Synthesis system.

These tests verify complete workflows from voice synthesis through
ambient sound, covering all major user journeys.
"""

import pytest
import time
import json

from src.shadowengine.audio.tts import (
    TTSEngine, TTSResult, TTSConfig, TTSStatus,
    MockTTSEngine, CoquiTTSEngine, PiperTTSEngine,
    create_tts_engine,
)
from src.shadowengine.audio.voice import (
    VoiceProfile, VoiceParameter, EmotionalState,
    VoiceModulator, VoiceLibrary, CharacterVoiceTTS as CharacterVoice,
    EMOTION_MODIFIERS,
)
from src.shadowengine.audio.effects import (
    Effect, EffectType, EffectParameter,
    EffectsChain, EffectPreset,
    PitchShift, TimeStretch, Reverb, Distortion,
    EQ, Delay, Compression, Tremolo,
)
from src.shadowengine.audio.motif import (
    Note, Chord, Rhythm, Motif,
    MusicalKey, TimeSignature, MotifType,
    MotifGenerator, ThemeEngine, TensionMapper,
    NOTE_FREQUENCIES, SCALE_PATTERNS,
)
from src.shadowengine.audio.ambient import (
    AmbientLayer, AmbientConfig, AmbientType,
    WeatherAudio, LocationAudio, TensionAudio,
    AmbientEngine,
)
from src.shadowengine.audio.synthesis import (
    AudioSynthesizer, SynthesisResult, SynthesisConfig,
    AudioEvent, AudioPriority, AudioMixer,
)


class TestTTSPipeline:
    """E2E tests for the TTS synthesis workflow."""

    def test_create_tts_and_synthesize(self):
        """Complete pipeline: create TTS engine and synthesize speech."""
        # Step 1: Create engine
        engine = create_tts_engine("mock", sample_rate=22050, cache_enabled=True)

        # Step 2: Initialize
        assert engine.initialize() is True
        assert engine.is_initialized is True

        # Step 3: Synthesize basic text
        result = engine.synthesize("Hello, world!")

        assert not result.is_empty
        assert len(result.audio_data) > 0
        assert result.duration_ms > 0

        # Step 4: Synthesize with parameters
        result2 = engine.synthesize(
            "How are you?",
            voice_id="male_1",
            speed=1.2,
            pitch=0.9,
        )
        assert not result2.is_empty

        # Step 5: Verify caching
        result3 = engine.synthesize("Hello, world!")
        assert result3.cached is True

        # Step 6: Shutdown
        engine.shutdown()
        assert engine.is_initialized is False

    def test_tts_with_voice_profiles(self):
        """Pipeline: TTS with voice personality profiles."""
        # Step 1: Create engine and voice library
        engine = create_tts_engine("mock")
        engine.initialize()
        library = VoiceLibrary()

        # Step 2: Get preset voice profiles
        gruff = library.get_preset("gruff_male")
        young = library.get_preset("young_female")

        assert gruff is not None
        assert young is not None

        # Step 3: Create character voices
        detective = library.create_character_voice("detective", gruff)
        witness = library.create_character_voice("witness", young)

        # Step 4: Synthesize with character voices
        det_profile = detective.get_effective_profile()
        result1 = engine.synthesize(
            "I've been investigating this case.",
            voice_id=det_profile.base_voice,
            pitch=det_profile.get_pitch_multiplier(),
            speed=det_profile.get_speed_multiplier(),
        )

        wit_profile = witness.get_effective_profile()
        result2 = engine.synthesize(
            "I didn't see anything!",
            voice_id=wit_profile.base_voice,
            pitch=wit_profile.get_pitch_multiplier(),
            speed=wit_profile.get_speed_multiplier(),
        )

        assert not result1.is_empty
        assert not result2.is_empty

        engine.shutdown()

    def test_tts_with_emotional_states(self):
        """Pipeline: TTS with emotional state modulation."""
        engine = create_tts_engine("mock")
        engine.initialize()
        library = VoiceLibrary()

        # Create character with neutral emotion
        profile = library.generate_random_profile(seed=42)
        character = library.create_character_voice("npc", profile)

        # Synthesize in different emotional states
        emotions = [
            EmotionalState.NEUTRAL,
            EmotionalState.ANGRY,
            EmotionalState.FEARFUL,
            EmotionalState.HAPPY,
            EmotionalState.SAD,
        ]

        results = []
        for emotion in emotions:
            character.set_emotion(emotion)
            effective = character.get_effective_profile()

            result = engine.synthesize(
                f"I am feeling {emotion.value}.",
                pitch=effective.get_pitch_multiplier(),
                speed=effective.get_speed_multiplier(),
            )
            results.append(result)

        # All should succeed
        assert all(not r.is_empty for r in results)

        engine.shutdown()


class TestEffectsPipeline:
    """E2E tests for audio effects processing workflow."""

    def test_create_and_apply_effects_chain(self):
        """Complete pipeline: create effects chain and process audio."""
        # Step 1: Create chain
        chain = EffectsChain()

        # Step 2: Add effects
        pitch = PitchShift(semitones=-2)
        reverb = Reverb(room_size=0.7, damping=0.5)
        compression = Compression(threshold=-10.0, ratio=4.0)

        chain.add_effect(pitch)
        chain.add_effect(reverb)
        chain.add_effect(compression)

        assert len(chain.get_effects()) == 3

        # Step 3: Process audio
        test_audio = b"x" * 1000
        processed = chain.process(test_audio, 22050)

        assert len(processed) > 0

        # Step 4: Modify effect parameters
        chain.get_effect(0).set_parameter("semitones", -4)
        chain.get_effect(1).set_parameter("wet", 0.6)

        processed2 = chain.process(test_audio, 22050)
        assert len(processed2) > 0

        # Step 5: Bypass chain
        chain.bypass = True
        processed3 = chain.process(test_audio, 22050)
        assert processed3 == test_audio

    def test_effects_presets_workflow(self):
        """Pipeline: load and modify effects presets."""
        chain = EffectsChain()

        # Load each preset and process
        presets = chain.get_preset_names()
        assert len(presets) >= 8

        test_audio = b"audio_data_sample" * 100

        for preset in presets:
            chain.clear()
            assert chain.load_preset(preset) is True
            assert len(chain.get_effects()) > 0

            processed = chain.process(test_audio, 22050)
            assert len(processed) > 0

    def test_effects_serialization_workflow(self):
        """Pipeline: serialize and restore effects chain."""
        # Create and configure chain
        chain = EffectsChain()
        chain.add_effect(PitchShift(semitones=3))
        chain.add_effect(Reverb(room_size=0.8))

        # Process original
        test_audio = b"original_audio" * 50
        original_processed = chain.process(test_audio, 22050)

        # Serialize
        data = chain.to_dict()
        json_str = json.dumps(data)

        # Restore
        restored_data = json.loads(json_str)
        restored_chain = EffectsChain.from_dict(restored_data)

        # Verify restoration (pitch_shift and reverb should restore)
        assert len(restored_chain.get_effects()) >= 2

        # Process with restored chain
        restored_processed = restored_chain.process(test_audio, 22050)
        assert len(restored_processed) > 0


class TestMotifGenerationPipeline:
    """E2E tests for procedural music generation workflow."""

    def test_generate_complete_theme(self):
        """Complete pipeline: generate musical theme with motifs."""
        # Step 1: Create generators
        generator = MotifGenerator(seed=42)
        theme_engine = ThemeEngine(seed=42)

        # Step 2: Generate theme components
        melodic = generator.generate_melodic_motif(
            key=MusicalKey.C_MINOR,
            length=4,
            tension=0.5,
        )
        bass = generator.generate_bass_motif(key=MusicalKey.C_MINOR)
        chords = generator.generate_chord_progression(
            key=MusicalKey.C_MINOR,
            tension=0.5,
        )

        assert melodic.motif_type == MotifType.MELODIC
        assert bass.motif_type == MotifType.BASS
        assert chords.motif_type == MotifType.HARMONIC

        # Step 3: Verify musical properties
        assert len(melodic.notes) > 0
        assert len(bass.notes) > 0
        assert len(chords.chords) > 0

        # Step 4: Generate full theme
        theme = theme_engine.generate_theme("noir_theme", mood="noir")
        assert len(theme) >= 3  # At least melodic, bass, and chords

        # Step 5: Transpose theme
        transposed = melodic.transpose(5)  # Up a fourth
        assert transposed.notes[0].pitch != melodic.notes[0].pitch

    def test_tension_mapped_music(self):
        """Pipeline: generate music based on tension levels."""
        theme_engine = ThemeEngine(seed=123)

        # Generate at different tension levels
        tension_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
        themes = []

        for tension in tension_levels:
            theme_engine.set_tension(tension, immediate=True)
            theme = theme_engine.generate_theme(f"theme_{tension}", mood="noir")
            themes.append((tension, theme))

        # Higher tension should produce faster tempos
        low_tension_tempo = themes[0][1][0].tempo
        high_tension_tempo = themes[-1][1][0].tempo
        assert high_tension_tempo >= low_tension_tempo

    def test_motif_serialization_workflow(self):
        """Pipeline: serialize and restore musical motifs."""
        generator = MotifGenerator(seed=789)

        # Generate complex motif
        motif = generator.generate_melodic_motif(
            key=MusicalKey.D_MINOR,
            length=8,
            tension=0.6,
        )

        # Add rhythm
        motif.rhythm = Rhythm(
            pattern=[1.0, 0.5, 0.5, 1.0],
            tempo=90,
        )

        # Serialize
        data = motif.to_dict()
        json_str = json.dumps(data)

        # Restore
        restored_data = json.loads(json_str)
        restored = Motif.from_dict(restored_data)

        # Verify
        assert restored.id == motif.id
        assert restored.key == motif.key
        assert len(restored.notes) == len(motif.notes)
        assert restored.rhythm.tempo == 90


class TestAmbientSoundPipeline:
    """E2E tests for ambient sound workflow."""

    def test_setup_ambient_scene(self):
        """Complete pipeline: setup ambient audio for a scene."""
        # Step 1: Create ambient engine
        config = AmbientConfig(master_volume=0.8, sample_rate=22050)
        engine = AmbientEngine(config)

        # Step 2: Set weather
        engine.set_weather("rain", intensity=0.7)

        layers = engine.get_all_layers()
        assert len(layers) > 0

        # Step 3: Set location
        engine.set_location("bar")

        layers = engine.get_all_layers()
        assert len(layers) > 0

        # Step 4: Set tension
        engine.set_tension(0.5)

        # Step 5: Generate mix
        mix = engine.generate_mix(1000.0, 22050)
        assert len(mix) > 0

        # Step 6: Update engine
        engine.update(100.0)

    def test_ambient_weather_transitions(self):
        """Pipeline: transition between weather conditions."""
        engine = AmbientEngine(AmbientConfig())

        # Start with clear weather
        engine.set_weather("clear")
        initial_layers = engine.get_layer_count()

        # Transition through weather types
        weather_sequence = ["rain", "storm", "fog", "clear"]

        for weather in weather_sequence:
            engine.set_weather(weather, intensity=0.8)
            # Simulate time passing
            for _ in range(5):
                engine.update(100.0)

            layers = engine.get_all_layers()
            assert len(layers) > 0

    def test_ambient_location_changes(self):
        """Pipeline: changing locations affects ambient audio."""
        engine = AmbientEngine(AmbientConfig())

        locations = ["street", "bar", "alley", "office", "warehouse"]

        for location in locations:
            engine.set_location(location)

            layers = engine.get_all_layers()
            assert len(layers) > 0

            # Generate audio for each location
            mix = engine.generate_mix(500.0, 22050)
            assert len(mix) > 0


class TestAudioSynthesizerPipeline:
    """E2E tests for unified audio synthesizer workflow."""

    def test_complete_dialogue_scene(self):
        """Complete pipeline: synthesize a full dialogue scene."""
        # Step 1: Create synthesizer
        config = SynthesisConfig(
            tts_engine_type="mock",
            sample_rate=22050,
            master_volume=0.8,
        )
        synth = AudioSynthesizer(config)

        # Step 2: Set up scene environment
        synth.set_weather("rain", intensity=0.6)
        synth.set_location("bar")
        synth.set_tension(0.3)

        # Step 3: Register character voices
        detective = synth.register_character_voice("detective", preset="gruff_male")
        witness = synth.register_character_voice("witness", preset="nervous_female")

        assert detective is not None
        assert witness is not None

        # Step 4: Synthesize dialogue exchange
        dialogue = [
            ("detective", "Where were you last night?", EmotionalState.NEUTRAL),
            ("witness", "I... I was at home!", EmotionalState.FEARFUL),
            ("detective", "Don't lie to me.", EmotionalState.ANGRY),
            ("witness", "Okay, okay! I was at the docks!", EmotionalState.NERVOUS),
        ]

        results = []
        for character_id, text, emotion in dialogue:
            result = synth.synthesize_speech(
                text,
                character_id=character_id,
                emotion=emotion,
            )
            results.append(result)

        # All dialogue should synthesize successfully
        assert all(r.success for r in results)
        assert all(len(r.audio_data) > 0 for r in results)

        # Step 5: Add sound effects
        synth.play_effect("footstep", volume=0.4)

        # Step 6: Get final mix
        final_mix = synth.get_mix(5000.0)
        assert len(final_mix) > 0

        # Step 7: Clean up
        synth.shutdown()

    def test_tension_escalation_scene(self):
        """Pipeline: simulate tension escalation in a scene."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        synth.set_location("warehouse")
        synth.register_character_voice("protagonist")

        # Simulate tension escalation
        tension_stages = [
            (0.1, "Something doesn't feel right."),
            (0.3, "I heard a noise."),
            (0.5, "Who's there?"),
            (0.7, "Show yourself!"),
            (0.9, "I know you're here!"),
        ]

        for tension, line in tension_stages:
            synth.set_tension(tension)
            synth.update(500.0)  # Let tension update

            result = synth.synthesize_speech(
                line,
                character_id="protagonist",
            )
            assert result.success

            # Theme engine should reflect tension
            assert synth.theme_engine.tension > 0 or tension == 0.1

        # High tension should have more ambient layers
        high_tension_layers = synth.ambient_engine.get_layer_count()

        synth.set_tension(0.1)
        synth.update(1000.0)
        low_tension_layers = synth.ambient_engine.get_layer_count()

        assert high_tension_layers >= low_tension_layers

        synth.shutdown()

    def test_queued_dialogue_processing(self):
        """Pipeline: queue and process dialogue in order."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Register characters
        synth.register_character_voice("a")
        synth.register_character_voice("b")
        synth.register_character_voice("c")

        # Queue dialogue with different priorities
        synth.queue_speech("This is low priority.", character_id="c", priority=AudioPriority.LOW)
        synth.queue_speech("This is normal priority.", character_id="b", priority=AudioPriority.NORMAL)
        synth.queue_speech("This is high priority!", character_id="a", priority=AudioPriority.HIGH)
        synth.queue_speech("This is critical!", character_id="a", priority=AudioPriority.CRITICAL)

        # Process queue
        results = synth.process_queue()

        # All should be processed
        assert len(results) == 4
        assert all(r.success for r in results)

        synth.shutdown()

    def test_full_serialization_workflow(self):
        """Pipeline: save and restore synthesizer state."""
        # Create and configure synthesizer
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        synth.register_character_voice("hero", preset="confident_male")
        synth.register_character_voice("villain", preset="gruff_male")

        synth.set_tension(0.6)
        synth.set_weather("storm")
        synth.set_location("rooftop")

        # Serialize
        data = synth.to_dict()

        # Verify serialized data
        assert "config" in data
        assert "voice_library" in data
        assert "theme_engine" in data

        # Create new synthesizer with same config
        synth2 = AudioSynthesizer(SynthesisConfig.from_dict(data["config"]))

        # Voices should be registerered separately
        synth2.register_character_voice("hero", preset="confident_male")
        synth2.register_character_voice("villain", preset="gruff_male")

        # Should be able to use it
        result = synth2.speak("hero", "I will stop you!")
        assert result.success

        synth.shutdown()
        synth2.shutdown()


class TestCrossSystemIntegration:
    """E2E tests for integration across audio subsystems."""

    def test_tts_to_effects_pipeline(self):
        """Pipeline: TTS -> Effects -> Output."""
        # Create components
        engine = create_tts_engine("mock")
        engine.initialize()

        chain = EffectsChain()
        chain.load_preset("telephone")

        # Synthesize speech
        result = engine.synthesize("Hello from the telephone!")
        assert not result.is_empty

        # Process through effects
        processed = chain.process(result.audio_data, 22050)
        assert len(processed) > 0

        engine.shutdown()

    def test_voice_personality_to_tts_pipeline(self):
        """Pipeline: Voice Library -> TTS with parameters."""
        library = VoiceLibrary()
        engine = create_tts_engine("mock")
        engine.initialize()
        modulator = VoiceModulator(seed=42)

        # Create and modulate voice
        profile = library.get_preset("gruff_male")
        whispered = modulator.apply_whisper(profile)
        aged = modulator.age_voice(profile, 30)

        # Synthesize with different modulations
        results = []
        for p in [profile, whispered, aged]:
            result = engine.synthesize(
                "Testing voice modulation.",
                pitch=p.get_pitch_multiplier(),
                speed=p.get_speed_multiplier(),
            )
            results.append(result)

        assert all(not r.is_empty for r in results)

        engine.shutdown()

    def test_motif_to_ambient_integration(self):
        """Pipeline: Theme Engine tension maps to ambient."""
        theme_engine = ThemeEngine(seed=42)
        ambient_engine = AmbientEngine(AmbientConfig())

        # Set up location first (needed for ambient layers)
        ambient_engine.set_location("bar")

        # Set shared tension
        for tension in [0.2, 0.5, 0.8]:
            theme_engine.set_tension(tension, immediate=True)
            ambient_engine.set_tension(tension)

            # Both should respond
            theme = theme_engine.generate_theme(f"theme_{tension}", mood="noir")
            ambient_engine.update(100.0)

            assert len(theme) > 0
            # Location ambient layers should exist
            assert ambient_engine.get_layer_count() > 0

    def test_full_audio_scene_simulation(self):
        """Complete simulation: full scene with all audio systems."""
        # Initialize synthesizer
        synth = AudioSynthesizer(SynthesisConfig(
            tts_engine_type="mock",
            master_volume=0.9,
            ambient_volume=0.6,
            music_volume=0.4,
        ))

        # Scene: Rainy night at a bar
        synth.set_weather("rain", intensity=0.7)
        synth.set_location("bar")
        synth.set_tension(0.2)

        # Register characters
        synth.register_character_voice("bartender", preset="gruff_male")
        synth.register_character_voice("stranger", preset="nervous_female")

        # Generate theme music
        theme = synth.generate_theme("bar_theme", mood="noir")
        assert len(theme) > 0

        # Scene plays out
        dialogue_sequence = [
            ("bartender", "What'll it be?", EmotionalState.NEUTRAL, "cave"),
            ("stranger", "Just water.", EmotionalState.NERVOUS, None),
            ("bartender", "Rough night?", EmotionalState.NEUTRAL, None),
            ("stranger", "You have no idea...", EmotionalState.SAD, None),
        ]

        for char_id, text, emotion, effect in dialogue_sequence:
            result = synth.synthesize_speech(
                text,
                character_id=char_id,
                emotion=emotion,
                effects_preset=effect,
            )
            assert result.success

            # Simulate time passing
            synth.update(500.0)

        # Tension rises
        synth.set_tension(0.6)
        synth.update(1000.0)

        # Sound effect
        synth.play_effect("door_slam", volume=0.8)

        # Get final mix
        final_mix = synth.get_mix(10000.0)
        assert len(final_mix) > 0

        # Check status
        status = synth.get_status()
        assert status["initialized"]
        assert status["tension"] > 0

        synth.shutdown()


class TestErrorHandlingPipeline:
    """E2E tests for error handling in audio pipelines."""

    def test_graceful_engine_failures(self):
        """Pipeline handles engine failures gracefully."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Operations should work normally
        result = synth.synthesize_speech("Normal operation")
        assert result.success

        # Shutdown and verify graceful handling
        synth.shutdown()
        assert not synth.is_initialized

    def test_invalid_preset_handling(self):
        """Pipeline handles invalid presets gracefully."""
        chain = EffectsChain()

        # Invalid preset should return False
        result = chain.load_preset("nonexistent_preset")
        assert result is False

        # Chain should still be usable
        chain.add_effect(Reverb())
        audio = chain.process(b"test", 22050)
        assert len(audio) > 0

    def test_empty_audio_handling(self):
        """Pipeline handles empty audio gracefully."""
        chain = EffectsChain()
        chain.load_preset("cave")

        # Empty audio
        result = chain.process(b"", 22050)
        assert result == b""

        # None bypass
        chain.bypass = True
        result = chain.process(b"test", 22050)
        assert result == b"test"


class TestPerformancePipeline:
    """E2E tests for performance-related scenarios."""

    def test_batch_synthesis_performance(self):
        """Pipeline: batch synthesize multiple texts efficiently."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        texts = [f"This is test sentence number {i}." for i in range(20)]

        start = time.time()
        results = []
        for text in texts:
            result = synth.synthesize_speech(text)
            results.append(result)
        elapsed = time.time() - start

        # All should succeed
        assert all(r.success for r in results)

        # Should complete reasonably fast (mock engine)
        assert elapsed < 5.0

        synth.shutdown()

    def test_cache_effectiveness(self):
        """Pipeline: verify caching improves performance."""
        synth = AudioSynthesizer(SynthesisConfig(
            tts_engine_type="mock",
            cache_enabled=True,
        ))

        text = "This text will be cached."

        # First synthesis (uncached)
        result1 = synth.synthesize_speech(text)
        assert result1.success

        # Second synthesis (should be cached)
        result2 = synth.synthesize_speech(text)
        assert result2.success
        assert result2.cached

        # Clear cache
        cleared = synth.clear_cache()
        assert cleared >= 0

        # Third synthesis (cache cleared, uncached again)
        result3 = synth.synthesize_speech(text)
        assert result3.success
        assert not result3.cached

        synth.shutdown()

    def test_concurrent_audio_streams(self):
        """Pipeline: handle multiple concurrent audio streams."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Set up ambient
        synth.set_weather("rain")
        synth.set_location("street")

        # Multiple characters
        for i in range(5):
            synth.register_character_voice(f"npc_{i}")

        # Multiple effects playing
        for i in range(3):
            synth.play_effect("footstep", volume=0.3)

        # Get mix with all streams
        mix = synth.get_mix(2000.0)
        assert len(mix) > 0

        status = synth.get_status()
        assert status["mixer_streams"] > 0

        synth.shutdown()


# Run all E2E tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
