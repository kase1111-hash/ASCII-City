"""
Cross-system integration tests for Audio with other ShadowEngine systems.

Tests the integration between audio synthesis and other game systems
including studio assets, voice input, and game state.
"""

import pytest
import json

from src.shadowengine.audio.synthesis import (
    AudioSynthesizer, SynthesisConfig, AudioPriority, AudioEvent,
)
from src.shadowengine.audio.voice import (
    VoiceProfile, VoiceLibrary, EmotionalState, CharacterVoiceTTS as CharacterVoice,
)
from src.shadowengine.audio.effects import EffectsChain, PitchShift, Reverb
from src.shadowengine.audio.motif import ThemeEngine, MotifGenerator, MusicalKey
from src.shadowengine.audio.ambient import AmbientEngine, AmbientConfig
from src.shadowengine.audio.tts import create_tts_engine, TTSStatus

# Import studio components
from src.shadowengine.studio.entity import (
    DynamicEntity, EntityState, EntityStats,
    create_entity_from_template,
)
from src.shadowengine.studio.personality import (
    PersonalityTemplate, PERSONALITY_TEMPLATES, ThreatResponse,
)
from src.shadowengine.studio.asset_pool import AssetPool, AssetQuery
from src.shadowengine.studio.tags import ObjectType, EnvironmentType

# Import voice/STT components
from src.shadowengine.voice.stt import create_stt_engine, STTResult
from src.shadowengine.voice.realtime import RealtimeHandler, InputMode


class TestEntityAudioIntegration:
    """Integration tests for entity + audio systems."""

    def test_entity_with_voice_profile(self):
        """Entity characters can have associated voice profiles."""
        # Create entity from template
        guard = create_entity_from_template("village_guard")
        assert guard is not None

        # Create synthesizer and register voice for entity
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Use entity personality to select voice preset
        personality_to_voice = {
            "aggressive_hostile": "gruff_male",
            "defensive_protective": "confident_male",
            "timid_fearful": "nervous_female",
            "curious_neutral": "young_female",
        }

        voice_preset = personality_to_voice.get(
            guard.personality.name,
            "gruff_male"  # Default
        )

        voice = synth.register_character_voice(guard.id, preset=voice_preset)
        assert voice is not None

        # Entity dialogue should use the voice
        for dialogue in guard.dialogue_pool:
            result = synth.speak(guard.id, dialogue)
            assert result.success

        synth.shutdown()

    def test_entity_state_affects_voice(self):
        """Entity state changes affect voice synthesis."""
        # Create entity
        deer = create_entity_from_template("forest_deer")
        assert deer is not None

        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))
        voice = synth.register_character_voice(deer.id, preset="nervous_female")

        # Map entity states to emotions
        state_to_emotion = {
            EntityState.IDLE: EmotionalState.NEUTRAL,
            EntityState.FLEEING: EmotionalState.FEARFUL,
            EntityState.ATTACKING: EmotionalState.ANGRY,
            EntityState.DEAD: EmotionalState.SAD,
            EntityState.MOVING: EmotionalState.HAPPY,
        }

        # Simulate state changes and voice adaptation
        for state, emotion in state_to_emotion.items():
            deer.state = state
            voice.set_emotion(emotion)

            # Effective profile changes with emotion
            profile = voice.get_effective_profile()

            result = synth.synthesize_speech(
                f"I am {state.value}",
                character_id=deer.id,
                emotion=emotion,
            )
            assert result.success

        synth.shutdown()

    def test_entity_combat_audio(self):
        """Combat between entities triggers appropriate audio."""
        guard = create_entity_from_template("village_guard")
        deer = create_entity_from_template("forest_deer")

        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))
        synth.set_tension(0.7)

        synth.register_character_voice(guard.id, preset="gruff_male")
        synth.register_character_voice(deer.id, preset="nervous_female")

        # Guard attacks deer
        initial_health = deer.stats.health
        damage = guard.attack(deer)

        if damage > 0:
            # Play attack sound
            synth.play_effect("combat", volume=0.8)

            # Guard battle cry
            result = synth.speak(guard.id, "Attack!")
            assert result.success

            # Deer fear response
            deer_voice = synth.get_character_voice(deer.id)
            deer_voice.set_emotion(EmotionalState.FEARFUL)

            result = synth.speak(deer.id, "*frightened cry*")
            assert result.success

        synth.shutdown()


class TestEnvironmentAudioIntegration:
    """Integration tests for environment + audio systems."""

    def test_location_ambient_mapping(self):
        """Game locations map to ambient sound configurations."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Map game location types to audio configurations
        location_configs = {
            EnvironmentType.FOREST: ("forest", "rain", 0.3),
            EnvironmentType.CAVE: ("cave", None, 0.5),
            EnvironmentType.VILLAGE: ("street", "clear", 0.2),
            EnvironmentType.MOUNTAIN: ("outdoor", "wind", 0.4),
        }

        for env_type, (location, weather, tension) in location_configs.items():
            synth.set_location(location)
            if weather:
                synth.set_weather(weather)
            synth.set_tension(tension)
            synth.update(100.0)

            # Verify ambient layers are set
            layers = synth.ambient_engine.get_all_layers()
            assert len(layers) > 0

            # Get mix for this environment
            mix = synth.get_mix(500.0)
            assert len(mix) > 0

        synth.shutdown()

    def test_time_of_day_affects_ambient(self):
        """Time of day affects ambient audio."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Day time - street sounds
        synth.set_location("street")
        synth.set_tension(0.2)
        day_mix = synth.get_mix(500.0)

        # Night time - different mood
        synth.set_tension(0.5)  # More tense at night
        night_mix = synth.get_mix(500.0)

        assert len(day_mix) > 0
        assert len(night_mix) > 0

        synth.shutdown()


class TestAssetPoolAudioIntegration:
    """Integration tests for asset pool + audio systems."""

    def test_asset_audio_properties(self):
        """Assets can have associated audio properties."""
        pool = AssetPool()
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Query for creatures (could have voices)
        query = AssetQuery(object_type=ObjectType.CREATURE)
        creatures = pool.query(query)

        # For each creature-type asset, we could assign voices
        voice_library = VoiceLibrary()

        for creature in creatures[:5]:  # Limit for test
            # Generate random voice for creature
            profile = voice_library.generate_random_profile(
                seed=hash(creature.id) % 10000
            )
            voice = voice_library.create_character_voice(creature.id, profile)
            assert voice is not None

        synth.shutdown()


class TestSTTAudioIntegration:
    """Integration tests for STT + TTS audio round-trip."""

    def test_stt_to_tts_pipeline(self):
        """Speech recognition -> response -> speech synthesis."""
        # Create STT engine
        stt_engine = create_stt_engine("mock")
        stt_engine.initialize()

        # Create TTS synthesizer
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))
        synth.register_character_voice("assistant")

        # Simulate STT receiving input
        stt_engine.set_response("Hello, how are you?")

        # Recognize speech
        audio_data = b"fake_audio_data"
        stt_result = stt_engine.transcribe(audio_data)

        if stt_result.text:
            # Generate response (in real system, would use LLM)
            response = f"You said: {stt_result.text}"

            # Synthesize response
            tts_result = synth.speak("assistant", response)
            assert tts_result.success

        stt_engine.shutdown()
        synth.shutdown()

    def test_realtime_handler_with_audio_response(self):
        """Realtime handler processes input and triggers audio response."""
        # Create handler
        handler = RealtimeHandler()

        # Create synthesizer
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))
        synth.register_character_voice("game_narrator")

        handler.start()

        # Simulate keyboard input
        handler.submit_keyboard_input("examine the room")

        # Process and get audio response
        result = synth.speak(
            "game_narrator",
            "You look around the dimly lit room. A desk sits in the corner."
        )
        assert result.success

        handler.stop()
        synth.shutdown()


class TestNarrativeAudioIntegration:
    """Integration tests for narrative + audio systems."""

    def test_tension_from_narrative_to_audio(self):
        """Narrative tension affects audio systems."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Simulate narrative tension stages
        narrative_stages = [
            ("introduction", 0.1, "calm"),
            ("rising_action", 0.4, "uneasy"),
            ("confrontation", 0.7, "tense"),
            ("climax", 0.9, "intense"),
            ("resolution", 0.2, "relieved"),
        ]

        for stage_name, tension, mood in narrative_stages:
            # Update audio tension
            synth.set_tension(tension)
            synth.update(200.0)

            # Generate appropriate theme
            theme = synth.generate_theme(stage_name, mood="noir")

            # Verify tension is reflected
            status = synth.get_status()

            # Ambient should adapt
            mix = synth.get_mix(500.0)
            assert len(mix) > 0

        synth.shutdown()

    def test_revelation_audio_cues(self):
        """Major revelations trigger audio cues."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Simulate revelation discovery
        synth.set_tension(0.5)

        # Create dramatic effect chain for revelations
        chain = synth.create_effects_chain("revelation")
        chain.add_effect(Reverb(room_size=0.9))
        chain.add_effect(PitchShift(semitones=-1))

        # Synthesize revelation
        result = synth.synthesize_speech(
            "The truth was hidden in plain sight all along.",
            effects_preset="revelation",
        )
        assert result.success

        # Build tension
        synth.set_tension(0.8)
        synth.update(500.0)

        # Musical sting
        theme = synth.generate_theme("revelation_sting", mood="tense")
        assert len(theme) > 0

        synth.shutdown()


class TestDialogueSystemAudioIntegration:
    """Integration tests for dialogue + audio systems."""

    def test_multi_character_conversation(self):
        """Multiple characters in conversation with distinct voices."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Register distinct voices for each character
        characters = {
            "detective": ("gruff_male", EmotionalState.CONFIDENT),
            "suspect": ("nervous_female", EmotionalState.NERVOUS),
            "witness": ("elderly_male", EmotionalState.FEARFUL),
        }

        for char_id, (preset, emotion) in characters.items():
            voice = synth.register_character_voice(char_id, preset=preset)
            voice.set_emotion(emotion)

        # Conversation script
        conversation = [
            ("detective", "Where were you at 9 PM last night?"),
            ("suspect", "I... I was at home."),
            ("detective", "Anyone who can confirm that?"),
            ("suspect", "No, I live alone."),
            ("witness", "Actually, I saw her at the docks."),
            ("suspect", "That's a lie!"),
            ("detective", "Interesting..."),
        ]

        results = []
        for char_id, line in conversation:
            result = synth.speak(char_id, line)
            results.append(result)
            assert result.success

        # All lines should synthesize
        assert len(results) == len(conversation)
        assert all(r.success for r in results)

        synth.shutdown()

    def test_dialogue_with_environmental_audio(self):
        """Dialogue plays over environmental audio."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Set up environment
        synth.set_weather("storm", intensity=0.8)
        synth.set_location("alley")
        synth.set_tension(0.6)

        synth.register_character_voice("character")

        # Synthesize dialogue over environment
        for i in range(3):
            result = synth.speak("character", f"Line {i + 1} in the storm.")
            assert result.success

            # Environment audio should continue
            mix = synth.get_mix(500.0)
            assert len(mix) > 0

        synth.shutdown()


class TestSerializationIntegration:
    """Integration tests for serializing audio state with game state."""

    def test_save_load_audio_with_game_state(self):
        """Audio state can be saved and loaded with game state."""
        # Create and configure synthesizer
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        synth.register_character_voice("hero", preset="confident_male")
        synth.register_character_voice("villain", preset="gruff_male")

        synth.set_tension(0.7)
        synth.set_weather("storm")
        synth.set_location("rooftop")

        # Serialize audio state
        audio_state = synth.to_dict()

        # Simulate saving full game state
        game_state = {
            "player_position": (10, 5),
            "current_location": "rooftop",
            "story_progress": 0.75,
            "audio_state": audio_state,
        }

        # Save to JSON
        saved_json = json.dumps(game_state)

        # Load game state
        loaded_state = json.loads(saved_json)

        # Restore audio
        restored_config = SynthesisConfig.from_dict(
            loaded_state["audio_state"]["config"]
        )
        restored_synth = AudioSynthesizer(restored_config)

        # Re-register voices (would restore from voice_library in full impl)
        restored_synth.register_character_voice("hero", preset="confident_male")
        restored_synth.register_character_voice("villain", preset="gruff_male")

        # Should work
        result = restored_synth.speak("hero", "I'm back!")
        assert result.success

        synth.shutdown()
        restored_synth.shutdown()


class TestCompleteGameScenario:
    """Full integration test simulating a complete game scenario."""

    def test_noir_investigation_scene(self):
        """Complete noir investigation scene with all audio systems."""
        # Initialize all systems
        synth = AudioSynthesizer(SynthesisConfig(
            tts_engine_type="mock",
            master_volume=0.9,
            ambient_volume=0.7,
            music_volume=0.5,
        ))

        # Scene: Rainy night, detective interrogates witness

        # 1. Set up environment
        synth.set_weather("rain", intensity=0.6)
        synth.set_location("office")
        synth.set_tension(0.3)

        # 2. Create character voices
        detective = synth.register_character_voice("detective", preset="gruff_male")
        witness = synth.register_character_voice("witness", preset="nervous_female")

        # 3. Generate ambient theme
        theme = synth.generate_theme("noir_office", mood="noir")
        assert len(theme) > 0

        # 4. Scene plays out
        scene_script = [
            # (character, line, emotion, tension_change, sound_effect)
            ("detective", "Take a seat.", EmotionalState.NEUTRAL, 0, None),
            ("witness", "What's this about?", EmotionalState.NERVOUS, 0.1, None),
            ("detective", "You know exactly what.", EmotionalState.CONFIDENT, 0, None),
            ("witness", "I swear, I don't know anything!", EmotionalState.FEARFUL, 0.2, None),
            (None, None, None, 0.3, "thunder"),  # Sound effect only
            ("detective", "Then explain this.", EmotionalState.ANGRY, 0.2, None),
            ("witness", "Where did you get that?!", EmotionalState.SURPRISED, 0.1, None),
            ("detective", "You left it at the scene.", EmotionalState.CONFIDENT, 0, None),
            ("witness", "I... I had no choice!", EmotionalState.SAD, -0.1, None),
        ]

        current_tension = 0.3
        for char_id, line, emotion, tension_delta, sfx in scene_script:
            # Update tension
            current_tension = max(0, min(1, current_tension + tension_delta))
            synth.set_tension(current_tension)
            synth.update(200.0)

            # Sound effect
            if sfx:
                synth.play_effect(sfx, volume=0.9)

            # Dialogue
            if char_id and line:
                voice = synth.get_character_voice(char_id)
                if voice and emotion:
                    voice.set_emotion(emotion)

                result = synth.speak(char_id, line)
                assert result.success

            # Generate ambient mix
            mix = synth.get_mix(500.0)
            assert len(mix) > 0

        # 5. Verify final state
        status = synth.get_status()
        assert status["initialized"]
        assert status["tension"] > 0

        synth.shutdown()


# Run all integration tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
