"""Tests for the audio engine."""

import pytest
from src.shadowengine.audio.audio_engine import (
    AudioEngine,
    AudioChannel,
    ChannelSettings,
    SpeechRequest,
    AudioState,
    create_audio_engine
)
from src.shadowengine.audio.voice import (
    CharacterVoice,
    VoiceParameters,
    EmotionalState,
    VoiceFactory
)
from src.shadowengine.audio.ambience import WeatherType, TimeOfDay
from src.shadowengine.audio.library import SoundID
from src.shadowengine.audio.effects import EffectsChain, DistortionEffect


class TestChannelSettings:
    """Tests for ChannelSettings."""

    def test_default_settings(self):
        """Test default channel settings."""
        settings = ChannelSettings()
        assert settings.volume == 1.0
        assert settings.muted is False
        assert settings.effects_chain is None

    def test_effective_volume_normal(self):
        """Test effective volume when not muted."""
        settings = ChannelSettings(volume=0.5)
        assert settings.get_effective_volume() == 0.5

    def test_effective_volume_muted(self):
        """Test effective volume when muted."""
        settings = ChannelSettings(volume=0.5, muted=True)
        assert settings.get_effective_volume() == 0.0


class TestAudioState:
    """Tests for AudioState."""

    def test_default_state(self):
        """Test default audio state."""
        state = AudioState()
        assert state.is_playing is False
        assert state.tension == 0.0
        assert state.master_volume == 1.0

    def test_to_dict(self):
        """Test state serialization."""
        state = AudioState(
            tension=0.5,
            weather=WeatherType.RAIN_LIGHT,
            time_of_day=TimeOfDay.DUSK
        )
        d = state.to_dict()

        assert d['tension'] == 0.5
        assert d['weather'] == 'rain_light'
        assert d['time_of_day'] == 'dusk'


class TestAudioEngine:
    """Tests for AudioEngine."""

    def test_create_engine(self):
        """Test creating an audio engine."""
        engine = AudioEngine(use_mock_tts=True)
        assert engine is not None
        assert not engine.is_initialized()

    def test_initialize(self):
        """Test engine initialization."""
        engine = AudioEngine(use_mock_tts=True)
        result = engine.initialize()

        assert result is True
        assert engine.is_initialized()

    def test_shutdown(self):
        """Test engine shutdown."""
        engine = AudioEngine(use_mock_tts=True)
        engine.initialize()
        engine.shutdown()

        assert not engine.is_initialized()

    # Voice Management Tests

    def test_register_voice(self):
        """Test registering a voice."""
        engine = AudioEngine(use_mock_tts=True)
        voice = CharacterVoice(character_id="c1", name="Test")

        engine.register_voice(voice)
        assert engine.get_voice("c1") == voice

    def test_get_nonexistent_voice(self):
        """Test getting nonexistent voice."""
        engine = AudioEngine(use_mock_tts=True)
        assert engine.get_voice("nonexistent") is None

    def test_create_voice_from_archetype(self):
        """Test creating voice from archetype."""
        engine = AudioEngine(use_mock_tts=True)
        voice = engine.create_voice_from_archetype(
            "det_1", "Sam Spade", "detective", seed=42
        )

        assert voice is not None
        assert engine.get_voice("det_1") == voice

    def test_set_voice_emotion(self):
        """Test setting voice emotion."""
        engine = AudioEngine(use_mock_tts=True)
        engine.register_voice(CharacterVoice(character_id="c1", name="Test"))

        result = engine.set_voice_emotion("c1", EmotionalState.ANGRY, 0.8)
        assert result is True

        voice = engine.get_voice("c1")
        assert voice.emotional_state == EmotionalState.ANGRY
        assert voice.emotion_intensity == 0.8

    def test_set_emotion_nonexistent_voice(self):
        """Test setting emotion for nonexistent voice."""
        engine = AudioEngine(use_mock_tts=True)
        result = engine.set_voice_emotion("nonexistent", EmotionalState.HAPPY)
        assert result is False

    # Speech Synthesis Tests

    def test_speak(self):
        """Test basic speech synthesis."""
        engine = AudioEngine(use_mock_tts=True)
        engine.initialize()
        engine.register_voice(CharacterVoice(character_id="c1", name="Test"))

        audio = engine.speak("c1", "Hello world")
        assert audio is not None
        assert len(audio.data) > 0

    def test_speak_with_emotion(self):
        """Test speaking with emotion."""
        engine = AudioEngine(use_mock_tts=True)
        engine.initialize()
        engine.register_voice(CharacterVoice(character_id="c1", name="Test"))

        audio = engine.speak("c1", "I'm so happy!", emotion=EmotionalState.HAPPY)
        assert audio is not None

    def test_speak_with_effects(self):
        """Test speaking with effects preset."""
        engine = AudioEngine(use_mock_tts=True)
        engine.initialize()
        engine.register_voice(CharacterVoice(character_id="c1", name="Test"))

        audio = engine.speak("c1", "Hello", effects_preset="telephone")
        assert audio is not None

    def test_speak_nonexistent_voice(self):
        """Test speaking with nonexistent voice."""
        engine = AudioEngine(use_mock_tts=True)
        engine.initialize()

        audio = engine.speak("nonexistent", "Hello")
        assert audio is None

    def test_queue_speech(self):
        """Test speech queue."""
        engine = AudioEngine(use_mock_tts=True)
        engine.initialize()
        engine.register_voice(CharacterVoice(character_id="c1", name="Test"))

        request = SpeechRequest(
            character_id="c1",
            text="Queued speech"
        )
        engine.queue_speech(request)

        assert len(engine._speech_queue) == 1

    def test_process_speech_queue(self):
        """Test processing speech queue."""
        engine = AudioEngine(use_mock_tts=True)
        engine.initialize()
        engine.register_voice(CharacterVoice(character_id="c1", name="Test"))

        completed = []
        request = SpeechRequest(
            character_id="c1",
            text="Test speech",
            on_complete=lambda audio: completed.append(audio)
        )
        engine.queue_speech(request)

        audio = engine.process_speech_queue()
        assert audio is not None
        assert len(completed) == 1
        assert len(engine._speech_queue) == 0

    # Sound Effects Tests

    def test_play_sound(self):
        """Test playing a library sound."""
        engine = AudioEngine(use_mock_tts=True)
        instance_id = engine.play_sound(SoundID.FOOTSTEP_WOOD)

        assert instance_id is not None
        assert instance_id.startswith("snd_")

    def test_play_generated_sound(self):
        """Test playing a generated sound."""
        engine = AudioEngine(use_mock_tts=True)
        instance_id = engine.play_generated_sound("thunder", duration_ms=1000)

        assert instance_id is not None

    def test_stop_sound(self):
        """Test stopping a sound."""
        engine = AudioEngine(use_mock_tts=True)
        instance_id = engine.play_sound(SoundID.FOOTSTEP_WOOD)

        engine.stop_sound(instance_id)
        engine.update(0)  # Process stop

        # Sound should be stopped (removed from mixer)

    def test_stop_all_sounds(self):
        """Test stopping all sounds."""
        engine = AudioEngine(use_mock_tts=True)
        engine.play_sound(SoundID.FOOTSTEP_WOOD)
        engine.play_sound(SoundID.RAIN_LIGHT)

        engine.stop_all_sounds()
        engine.update(0)

        assert engine.sound_mixer.get_playing_count() == 0

    # Ambience Tests

    def test_set_ambience(self):
        """Test setting ambience preset."""
        engine = AudioEngine(use_mock_tts=True)

        result = engine.set_ambience("city_night")
        assert result is True
        assert engine._state.ambience_preset == "city_night"

    def test_set_invalid_ambience(self):
        """Test setting invalid ambience."""
        engine = AudioEngine(use_mock_tts=True)

        result = engine.set_ambience("nonexistent")
        assert result is False

    def test_set_weather(self):
        """Test setting weather."""
        engine = AudioEngine(use_mock_tts=True)
        engine.set_weather(WeatherType.STORM, 0.9)

        assert engine._state.weather == WeatherType.STORM

    def test_set_time_of_day(self):
        """Test setting time of day."""
        engine = AudioEngine(use_mock_tts=True)
        engine.set_time_of_day(TimeOfDay.DAWN)

        assert engine._state.time_of_day == TimeOfDay.DAWN

    def test_set_tension(self):
        """Test setting tension."""
        engine = AudioEngine(use_mock_tts=True)
        engine.set_tension(0.8)

        assert engine._state.tension == 0.8

    def test_get_ambient_audio(self):
        """Test getting ambient audio."""
        engine = AudioEngine(use_mock_tts=True)
        engine.set_ambience("alley")

        audio = engine.get_ambient_audio(duration_ms=1000)
        assert audio is not None
        assert len(audio.data) > 0

    # Channel Control Tests

    def test_set_channel_volume(self):
        """Test setting channel volume."""
        engine = AudioEngine(use_mock_tts=True)
        engine.set_channel_volume(AudioChannel.VOICE, 0.5)

        assert engine.get_channel_volume(AudioChannel.VOICE) == 0.5

    def test_volume_clamping(self):
        """Test volume clamping."""
        engine = AudioEngine(use_mock_tts=True)
        engine.set_channel_volume(AudioChannel.VOICE, 1.5)
        assert engine.get_channel_volume(AudioChannel.VOICE) == 1.0

        engine.set_channel_volume(AudioChannel.VOICE, -0.5)
        assert engine.get_channel_volume(AudioChannel.VOICE) == 0.0

    def test_mute_channel(self):
        """Test muting a channel."""
        engine = AudioEngine(use_mock_tts=True)

        engine.mute_channel(AudioChannel.EFFECTS)
        assert engine.is_channel_muted(AudioChannel.EFFECTS)

        engine.unmute_channel(AudioChannel.EFFECTS)
        assert not engine.is_channel_muted(AudioChannel.EFFECTS)

    def test_set_channel_effects(self):
        """Test setting channel effects."""
        engine = AudioEngine(use_mock_tts=True)
        chain = EffectsChain()
        chain.add_effect(DistortionEffect())

        engine.set_channel_effects(AudioChannel.VOICE, chain)
        assert engine._channels[AudioChannel.VOICE].effects_chain == chain

    def test_master_volume(self):
        """Test master volume control."""
        engine = AudioEngine(use_mock_tts=True)
        engine.set_master_volume(0.5)

        assert engine.get_master_volume() == 0.5
        assert engine._state.master_volume == 0.5
        assert engine.sound_mixer.master_volume == 0.5

    # State Tests

    def test_get_state(self):
        """Test getting audio state."""
        engine = AudioEngine(use_mock_tts=True)
        engine.set_tension(0.5)
        engine.set_weather(WeatherType.RAIN_LIGHT)

        state = engine.get_state()
        assert state.tension == 0.5
        assert state.weather == WeatherType.RAIN_LIGHT

    def test_update(self):
        """Test update method."""
        engine = AudioEngine(use_mock_tts=True)
        engine.initialize()
        engine.play_sound(SoundID.FOOTSTEP_WOOD)

        # Should not raise
        engine.update(16.67)  # ~60 FPS

    # Serialization Tests

    def test_save_state(self):
        """Test saving state."""
        engine = AudioEngine(use_mock_tts=True)
        engine.initialize()
        engine.set_tension(0.7)
        engine.set_weather(WeatherType.STORM)
        engine.set_ambience("rain")
        engine.register_voice(CharacterVoice(character_id="c1", name="Test"))

        state = engine.save_state()

        assert 'state' in state
        assert 'voices' in state
        assert 'channels' in state
        assert state['state']['tension'] == 0.7

    def test_load_state(self):
        """Test loading state."""
        engine = AudioEngine(use_mock_tts=True)
        engine.initialize()

        saved_state = {
            'state': {
                'tension': 0.6,
                'weather': 'rain_heavy',
                'time_of_day': 'dusk',
                'master_volume': 0.8
            },
            'voices': {
                'c1': {
                    'character_id': 'c1',
                    'name': 'Loaded Voice',
                    'gender': 'male',
                    'age': 'adult',
                    'accent': 'neutral',
                    'base_params': {},
                    'emotional_state': 'neutral',
                    'emotion_intensity': 0.5,
                    'speech_quirks': [],
                    'catchphrases': []
                }
            },
            'channels': {
                'voice': {'volume': 0.7, 'muted': False}
            }
        }

        engine.load_state(saved_state)

        assert engine._state.tension == 0.6
        assert engine._state.weather == WeatherType.RAIN_HEAVY
        assert engine._state.master_volume == 0.8
        assert engine.get_voice('c1') is not None


class TestCreateAudioEngine:
    """Tests for create_audio_engine function."""

    def test_create_with_defaults(self):
        """Test creating engine with defaults."""
        engine = create_audio_engine()
        assert engine.is_initialized()

    def test_create_without_auto_init(self):
        """Test creating without auto-initialize."""
        engine = create_audio_engine(auto_initialize=False)
        assert not engine.is_initialized()

    def test_create_with_mock_tts(self):
        """Test creating with mock TTS."""
        engine = create_audio_engine(use_mock_tts=True)
        assert engine.is_initialized()

        # Should have mock engine
        from src.shadowengine.audio.tts_engine import TTSEngineType
        mock = engine.tts_manager.get_engine(TTSEngineType.MOCK)
        assert mock is not None
