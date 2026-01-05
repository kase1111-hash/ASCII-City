"""
Cross-system integration tests for Modding with other ShadowEngine systems.

Tests the integration between modding/extensibility and other game systems
including audio, studio, and voice components.
"""

import pytest
import json

from src.shadowengine.modding.registry import ModRegistry, ModInfo, ModType
from src.shadowengine.modding.theme_pack import (
    ThemePack, VocabularyConfig, WeatherConfig, AtmosphereConfig,
    NOIR_THEME, CYBERPUNK_THEME,
)
from src.shadowengine.modding.archetype import (
    ArchetypeDefinition, MotivationPreset, BehaviorPattern,
    BehaviorTendency, ResponseStyle, ArchetypeRegistry,
    FEMME_FATALE, CORRUPT_COP, STREET_INFORMANT,
)
from src.shadowengine.modding.scenario import (
    ScenarioScript, CharacterTemplate, LocationTemplate, ConflictTemplate,
    ScriptedEvent, EventTrigger, EventAction, TriggerType, ActionType,
)

# Audio system imports
from src.shadowengine.audio.synthesis import (
    AudioSynthesizer, SynthesisConfig,
)
from src.shadowengine.audio.voice import (
    VoiceProfile, VoiceLibrary, EmotionalState,
)
from src.shadowengine.audio.effects import EffectsChain, Reverb, PitchShift

# Studio system imports
from src.shadowengine.studio.entity import (
    DynamicEntity, EntityState, EntityStats,
    create_entity_from_template,
)
from src.shadowengine.studio.personality import (
    PersonalityTemplate, PERSONALITY_TEMPLATES, ThreatResponse,
)
from src.shadowengine.studio.asset_pool import AssetPool, AssetQuery
from src.shadowengine.studio.tags import ObjectType, EnvironmentType

# Voice system imports
from src.shadowengine.voice.stt import create_stt_engine
from src.shadowengine.voice.realtime import RealtimeHandler


class TestThemePackAudioIntegration:
    """Integration tests for theme pack + audio systems."""

    def test_theme_atmosphere_affects_audio(self):
        """Theme pack atmosphere settings affect audio synthesis."""
        # Get noir theme
        noir = NOIR_THEME

        # Create audio synthesizer
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Apply theme atmosphere to audio
        if noir.atmosphere:
            # Set tension based on theme effect intensity
            synth.set_tension(noir.atmosphere.effect_intensity)

            # Use theme ambient sounds
            for sound in noir.atmosphere.ambient_sounds[:3]:
                synth.play_effect(sound, volume=0.3)

        # Update synthesizer
        synth.update(100.0)

        # Generate theme music based on theme tempo
        if noir.atmosphere:
            theme = synth.generate_theme("noir_ambient", mood="noir")
            assert len(theme) > 0

        synth.shutdown()

    def test_theme_weather_affects_ambient(self):
        """Theme weather configuration affects ambient audio."""
        # Get cyberpunk theme
        cyberpunk = CYBERPUNK_THEME

        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Apply theme weather
        if cyberpunk.weather:
            # Get most likely weather for this theme
            weights = cyberpunk.weather.weather_weights
            dominant_weather = max(weights.keys(), key=lambda k: weights[k])

            synth.set_weather(dominant_weather)
            synth.set_location("street")
            synth.update(100.0)

            # Get ambient mix
            mix = synth.get_mix(500.0)
            assert len(mix) > 0

        synth.shutdown()

    def test_theme_vocabulary_for_narration(self):
        """Theme vocabulary used in audio narration."""
        noir = NOIR_THEME
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))
        synth.register_character_voice("narrator")

        # Use theme vocabulary in narration
        verb = noir.vocabulary.get_verb("examine")
        narration = f"You {verb} the room carefully."

        result = synth.speak("narrator", narration)
        assert result.success

        synth.shutdown()


class TestArchetypeEntityIntegration:
    """Integration tests for archetype + entity systems."""

    def test_archetype_personality_mapping(self):
        """Map archetype behavior to entity personality."""
        # Get archetype
        ff = FEMME_FATALE

        # Map archetype behavior to personality traits
        behavior_to_personality = {
            BehaviorTendency.AGGRESSIVE: "aggressive_hostile",
            BehaviorTendency.PROTECTIVE: "defensive_protective",
            BehaviorTendency.EVASIVE: "timid_fearful",
            BehaviorTendency.COOPERATIVE: "curious_neutral",
        }

        personality_name = behavior_to_personality.get(
            ff.behavior.tendency,
            "curious_neutral"
        )

        # Find matching personality template
        personality = None
        for template in PERSONALITY_TEMPLATES.values():
            if template.name == personality_name:
                personality = template
                break

        # Create entity stats based on archetype motivations
        stats = EntityStats(
            health=100.0,
            attack_power=float(ff.motivations.ambition / 10),
            defense=float(ff.motivations.survival / 10),
            speed=float(ff.motivations.greed / 10),
        )

        # Verify mapping worked
        assert stats.attack_power > 0

    def test_archetype_voice_profile_mapping(self):
        """Map archetype to voice profile for audio."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Map archetypes to voice presets
        archetype_voices = {
            FEMME_FATALE.id: "confident_female",
            CORRUPT_COP.id: "gruff_male",
            STREET_INFORMANT.id: "nervous_male",
        }

        for arch_id, voice_preset in archetype_voices.items():
            voice = synth.register_character_voice(arch_id, preset=voice_preset)
            assert voice is not None

        # Use archetype dialogue templates with voices
        for greeting in FEMME_FATALE.greeting_templates[:2]:
            result = synth.speak(FEMME_FATALE.id, greeting)
            assert result.success

        synth.shutdown()

    def test_archetype_emotional_responses(self):
        """Archetype behavior affects voice emotional state."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Create voice for street informant (cracks easily)
        voice = synth.register_character_voice(
            STREET_INFORMANT.id,
            preset="nervous_male"
        )

        # Map archetype thresholds to emotional states
        pressure = 0.5

        if pressure > STREET_INFORMANT.behavior.fear_threshold:
            voice.set_emotion(EmotionalState.FEARFUL)
        elif pressure > STREET_INFORMANT.behavior.anger_threshold:
            voice.set_emotion(EmotionalState.ANGRY)
        else:
            voice.set_emotion(EmotionalState.NEUTRAL)

        # Speak with emotional voice
        result = synth.speak(
            STREET_INFORMANT.id,
            "I... I don't know anything!"
        )
        assert result.success

        synth.shutdown()


class TestScenarioGameIntegration:
    """Integration tests for scenario + game systems."""

    def test_scenario_location_to_ambient(self):
        """Scenario locations affect ambient audio."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Create scenario locations
        locations = [
            LocationTemplate(
                id="dark_alley",
                name="Dark Alley",
                is_outdoor=True,
                base_light_level=0.2,
            ),
            LocationTemplate(
                id="jazz_club",
                name="Jazz Club",
                is_outdoor=False,
                base_light_level=0.4,
            ),
        ]

        # Map locations to audio settings
        location_audio = {
            "dark_alley": ("alley", "rain", 0.6),
            "jazz_club": ("bar", "clear", 0.3),
        }

        for loc in locations:
            if loc.id in location_audio:
                audio_loc, weather, tension = location_audio[loc.id]
                synth.set_location(audio_loc)
                synth.set_weather(weather)
                synth.set_tension(tension)
                synth.update(100.0)

                mix = synth.get_mix(500.0)
                assert len(mix) > 0

        synth.shutdown()

    def test_scenario_events_trigger_audio(self):
        """Scenario events trigger audio cues."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))
        synth.register_character_voice("narrator")

        # Create events with audio actions
        events = [
            ScriptedEvent(
                id="thunder",
                name="Thunder Strike",
                triggers=[EventTrigger(trigger_type=TriggerType.ON_GAME_START)],
                actions=[
                    EventAction(action_type=ActionType.PLAY_SOUND, value="thunder"),
                    EventAction(action_type=ActionType.SET_TENSION, value=0.7),
                ],
            ),
            ScriptedEvent(
                id="revelation",
                name="Major Revelation",
                triggers=[EventTrigger(trigger_type=TriggerType.ON_REVELATION)],
                actions=[
                    EventAction(action_type=ActionType.PLAY_MUSIC, value="revelation_sting"),
                    EventAction(action_type=ActionType.SHOW_NARRATION, value="The truth emerges..."),
                ],
            ),
        ]

        # Simulate event execution with audio
        for event in events:
            for action in event.actions:
                if action.action_type == ActionType.PLAY_SOUND:
                    synth.play_effect(action.value, volume=0.8)
                elif action.action_type == ActionType.PLAY_MUSIC:
                    synth.generate_theme(action.value, mood="tense")
                elif action.action_type == ActionType.SET_TENSION:
                    synth.set_tension(action.value)
                elif action.action_type == ActionType.SHOW_NARRATION:
                    synth.speak("narrator", action.value)

        synth.shutdown()

    def test_scenario_character_audio_mapping(self):
        """Scenario characters get voice profiles."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Create scenario with characters
        characters = [
            CharacterTemplate(
                id="detective",
                name="Detective Stone",
                archetype="corrupt_cop",
                starting_mood="stressed",
            ),
            CharacterTemplate(
                id="femme",
                name="Lady Noir",
                archetype="femme_fatale",
                starting_mood="confident",
            ),
        ]

        # Map characters to voices based on archetype
        archetype_voice_map = {
            "corrupt_cop": "gruff_male",
            "femme_fatale": "confident_female",
            "street_informant": "nervous_male",
            "grieving_widow": "sad_female",
        }

        # Map moods to emotions
        mood_emotion_map = {
            "stressed": EmotionalState.NERVOUS,
            "confident": EmotionalState.CONFIDENT,
            "angry": EmotionalState.ANGRY,
            "sad": EmotionalState.SAD,
        }

        for char in characters:
            # Get voice preset from archetype
            preset = archetype_voice_map.get(char.archetype, "neutral")
            voice = synth.register_character_voice(char.id, preset=preset)

            # Set emotion from mood
            emotion = mood_emotion_map.get(char.starting_mood, EmotionalState.NEUTRAL)
            voice.set_emotion(emotion)

            # Speak dialogue
            for dialogue in char.dialogue_pool[:2] if char.dialogue_pool else ["Hello."]:
                result = synth.speak(char.id, dialogue)
                assert result.success

        synth.shutdown()


class TestModRegistryContentIntegration:
    """Integration tests for mod registry + content systems."""

    def test_registry_manages_audio_themes(self):
        """Mod registry manages theme packs that affect audio."""
        registry = ModRegistry()
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Register mod with theme pack
        mod = ModInfo(
            id="audio_theme_mod",
            name="Audio Theme Mod",
            version="1.0.0",
            mod_type=ModType.THEME_PACK,
        )
        registry.register_mod(mod)

        # Create custom theme with audio settings
        theme = ThemePack(
            id="custom_audio_theme",
            name="Custom Audio Theme",
            atmosphere=AtmosphereConfig(
                ambient_sounds=["rain", "thunder", "wind"],
                effect_intensity=0.8,
                tempo_base=90,
            ),
        )
        registry.register_theme_pack(theme, mod.id)

        # Retrieve and apply to audio
        loaded_theme = registry.get_theme_pack(theme.id)
        assert loaded_theme is not None

        if loaded_theme.atmosphere:
            synth.set_tension(loaded_theme.atmosphere.effect_intensity)
            for sound in loaded_theme.atmosphere.ambient_sounds:
                synth.play_effect(sound, volume=0.3)

        synth.shutdown()

    def test_registry_manages_character_voices(self):
        """Mod registry manages archetypes that affect character voices."""
        registry = ModRegistry()
        arch_registry = ArchetypeRegistry()
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Register mod with archetype
        mod = ModInfo(
            id="character_mod",
            name="Character Mod",
            version="1.0.0",
            mod_type=ModType.ARCHETYPE,
        )
        registry.register_mod(mod)

        # Create custom archetype
        archetype = ArchetypeDefinition(
            id="tech_noir_hacker",
            name="Tech Noir Hacker",
            behavior=BehaviorPattern(
                tendency=BehaviorTendency.EVASIVE,
                response_style=ResponseStyle.TERSE,
            ),
            greeting_templates=["System online.", "Query accepted."],
        )
        registry.register_archetype(archetype, mod.id)
        arch_registry.register(archetype)

        # Create voice for archetype
        voice = synth.register_character_voice(
            archetype.id,
            preset="neutral"  # Tech voice
        )

        # Apply effects for "digital" voice
        chain = synth.create_effects_chain("digital")
        chain.add_effect(PitchShift(semitones=-2))
        chain.add_effect(Reverb(room_size=0.3))

        # Speak with archetype dialogue
        for greeting in archetype.greeting_templates:
            result = synth.synthesize_speech(
                greeting,
                character_id=archetype.id,
                effects_preset="digital",
            )
            assert result.success

        synth.shutdown()


class TestVoiceInputModIntegration:
    """Integration tests for voice input + modding systems."""

    def test_voice_commands_with_theme_vocabulary(self):
        """Voice commands use theme vocabulary for recognition."""
        # Create STT engine
        stt = create_stt_engine("mock")
        stt.initialize()

        # Get theme vocabulary
        noir = NOIR_THEME
        vocab = noir.vocabulary

        # Set up expected voice commands using theme verbs
        commands = []
        for verb_type in ["examine", "talk", "take", "use", "go"]:
            verb = vocab.get_verb(verb_type)
            commands.append(f"{verb} the evidence")

        # Mock STT responses
        for cmd in commands:
            stt.set_response(cmd)
            result = stt.transcribe(b"fake_audio")
            assert result.text == cmd

        stt.shutdown()

    def test_realtime_input_with_scenario_context(self):
        """Realtime handler uses scenario context."""
        handler = RealtimeHandler()

        # Create scenario with location
        scenario = ScenarioScript(
            id="context_test",
            name="Context Test",
            locations=[
                LocationTemplate(
                    id="office",
                    name="Detective's Office",
                    items=["desk", "files", "telephone"],
                ),
            ],
        )

        # Set context from scenario
        location = scenario.get_location("office")
        if location:
            context = {
                "current_location": location.name,
                "available_items": location.items,
                "exits": list(location.exits.keys()) if location.exits else [],
            }
            handler.set_context(context)

        handler.start()

        # Submit command related to context
        handler.submit_keyboard_input("examine the desk")

        # Context should be available
        current_context = handler._context
        assert "current_location" in current_context

        handler.stop()


class TestFullSystemIntegration:
    """Full integration tests across all systems."""

    def test_complete_noir_scene(self):
        """Complete noir scene with all systems integrated."""
        # Step 1: Set up mod registry
        registry = ModRegistry()

        # Step 2: Load noir theme
        noir = NOIR_THEME

        # Step 3: Set up audio
        synth = AudioSynthesizer(SynthesisConfig(
            tts_engine_type="mock",
            master_volume=0.9,
        ))

        # Step 4: Apply theme to audio
        synth.set_tension(noir.atmosphere.effect_intensity)
        synth.set_weather("rain")
        synth.set_location("office")

        # Step 5: Create characters from archetypes
        characters = [
            ("detective", CORRUPT_COP, "gruff_male"),
            ("suspect", FEMME_FATALE, "confident_female"),
            ("witness", STREET_INFORMANT, "nervous_male"),
        ]

        for char_id, archetype, voice_preset in characters:
            voice = synth.register_character_voice(char_id, preset=voice_preset)

            # Set emotion based on archetype
            if archetype.behavior.cracks_easily:
                voice.set_emotion(EmotionalState.NERVOUS)
            elif archetype.behavior.tendency == BehaviorTendency.AGGRESSIVE:
                voice.set_emotion(EmotionalState.ANGRY)
            else:
                voice.set_emotion(EmotionalState.CONFIDENT)

        # Step 6: Create scenario
        scenario = ScenarioScript(
            id="noir_interrogation",
            name="Noir Interrogation",
            theme_pack="noir",
            starting_tension=0.4,
        )

        # Step 7: Simulate scene with dialogue
        scene_dialogue = [
            ("detective", "Where were you last night?"),
            ("suspect", "At home. Alone."),
            ("detective", "That's not what the witness says."),
            ("witness", "I... I saw her at the docks!"),
            ("suspect", "That nervous little rat is lying!"),
        ]

        # Increase tension through scene
        tension = 0.4
        for char_id, line in scene_dialogue:
            synth.set_tension(tension)
            result = synth.speak(char_id, line)
            assert result.success
            tension = min(1.0, tension + 0.1)

        # Step 8: Generate ambient mix
        mix = synth.get_mix(500.0)
        assert len(mix) > 0

        # Step 9: Final state check
        status = synth.get_status()
        assert status["initialized"]

        synth.shutdown()

    def test_scenario_with_audio_and_entities(self):
        """Scenario integrates with audio and entity systems."""
        synth = AudioSynthesizer(SynthesisConfig(tts_engine_type="mock"))

        # Create entity from template
        guard = create_entity_from_template("village_guard")
        assert guard is not None

        # Create voice for entity
        synth.register_character_voice(guard.id, preset="gruff_male")

        # Create scenario event that affects entity
        event = ScriptedEvent(
            id="guard_alert",
            name="Guard Alert",
            triggers=[
                EventTrigger(
                    trigger_type=TriggerType.ON_ENTER_LOCATION,
                    target="restricted_area",
                )
            ],
            actions=[
                EventAction(
                    action_type=ActionType.SET_CHARACTER_STATE,
                    target=guard.id,
                    value="alert",
                ),
                EventAction(
                    action_type=ActionType.SHOW_DIALOGUE,
                    target=guard.id,
                    value="Halt! Who goes there?",
                ),
                EventAction(
                    action_type=ActionType.SET_TENSION,
                    value=0.7,
                ),
            ],
        )

        # Simulate event execution
        for action in event.actions:
            if action.action_type == ActionType.SET_CHARACTER_STATE:
                guard.state = EntityState.ATTACKING  # Map to entity state
            elif action.action_type == ActionType.SHOW_DIALOGUE:
                result = synth.speak(guard.id, action.value)
                assert result.success
            elif action.action_type == ActionType.SET_TENSION:
                synth.set_tension(action.value)

        synth.shutdown()


class TestSerializationIntegration:
    """Integration tests for serialization across systems."""

    def test_save_load_complete_game_state(self):
        """Save and load complete game state with mods."""
        # Create all systems
        registry = ModRegistry()
        arch_registry = ArchetypeRegistry()

        # Register mod
        mod = ModInfo(id="save_test_mod", name="Save Test", version="1.0.0")
        registry.register_mod(mod)

        # Register theme
        theme = ThemePack(id="save_test_theme", name="Save Theme")
        registry.register_theme_pack(theme, mod.id)

        # Register archetype
        archetype = ArchetypeDefinition(
            id="save_test_arch",
            name="Save Archetype",
            greeting_templates=["Hello."],
        )
        arch_registry.register(archetype)

        # Create scenario
        scenario = ScenarioScript(
            id="save_test_scenario",
            name="Save Test Scenario",
            starting_tension=0.5,
        )

        # Serialize everything
        game_state = {
            "mod_registry": registry.to_dict(),
            "archetype_registry": arch_registry.to_dict(),
            "scenario": scenario.to_dict(),
            "game_progress": 0.5,
            "player_position": {"x": 10, "y": 5},
        }

        # Convert to JSON
        json_str = json.dumps(game_state)

        # Restore from JSON
        loaded = json.loads(json_str)

        # Restore registries
        restored_registry = ModRegistry.from_dict(loaded["mod_registry"])
        restored_arch = ArchetypeRegistry.from_dict(loaded["archetype_registry"])
        restored_scenario = ScenarioScript.from_dict(loaded["scenario"])

        # Verify restoration
        assert restored_registry.get_mod("save_test_mod") is not None
        assert restored_arch.get("save_test_arch") is not None
        assert restored_scenario.id == "save_test_scenario"


# Run all integration tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
