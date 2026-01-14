"""
Audio Engine - Central audio system orchestrator.

Coordinates TTS, sound effects, and ambient audio into
a unified audio experience.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import time

from .voice import CharacterVoice, VoiceFactory, EmotionalState
from .tts_engine import (
    TTSEngineManager,
    TTSRequest,
    AudioData,
    MockTTSEngine,
    TTSEngineError
)
from .effects import (
    EffectsChain,
    create_preset_chain
)
from .sound import (
    SoundEffect,
    SoundCategory,
    SoundGenerator,
    SoundMixer,
    SoundProperties
)
from .ambience import (
    AmbienceManager,
    WeatherType,
    TimeOfDay
)
from .library import SoundLibrary, SoundID


class AudioChannel(Enum):
    """Audio output channels."""
    MASTER = "master"
    VOICE = "voice"
    EFFECTS = "effects"
    AMBIENCE = "ambience"
    MUSIC = "music"
    UI = "ui"


@dataclass
class ChannelSettings:
    """Settings for an audio channel."""
    volume: float = 1.0
    muted: bool = False
    effects_chain: Optional[EffectsChain] = None

    def get_effective_volume(self) -> float:
        """Get volume considering mute state."""
        return 0.0 if self.muted else self.volume


@dataclass
class SpeechRequest:
    """Request for character speech synthesis."""
    character_id: str
    text: str
    emotion: Optional[EmotionalState] = None
    emotion_intensity: float = 0.5
    effects_preset: Optional[str] = None  # e.g., "telephone", "radio"

    # Callbacks
    on_start: Optional[Callable[[], None]] = None
    on_complete: Optional[Callable[[AudioData], None]] = None
    on_error: Optional[Callable[[Exception], None]] = None


@dataclass
class AudioState:
    """Current state of the audio engine."""
    is_playing: bool = False
    current_speech: Optional[str] = None
    active_sounds: int = 0
    ambience_preset: Optional[str] = None
    weather: WeatherType = WeatherType.CLEAR
    time_of_day: TimeOfDay = TimeOfDay.NIGHT
    tension: float = 0.0
    master_volume: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'is_playing': self.is_playing,
            'current_speech': self.current_speech,
            'active_sounds': self.active_sounds,
            'ambience_preset': self.ambience_preset,
            'weather': self.weather.value,
            'time_of_day': self.time_of_day.value,
            'tension': self.tension,
            'master_volume': self.master_volume
        }


class AudioEngine:
    """
    Central audio system orchestrator.

    Manages all audio subsystems and provides a unified
    interface for game audio.
    """

    def __init__(self, use_mock_tts: bool = True):
        """
        Initialize the audio engine.

        Args:
            use_mock_tts: If True, use mock TTS for testing
        """
        # Core systems
        self.tts_manager = TTSEngineManager()
        self.sound_generator = SoundGenerator()
        self.sound_mixer = SoundMixer()
        self.ambience_manager = AmbienceManager()
        self.sound_library = SoundLibrary()

        # Character voices
        self._voices: Dict[str, CharacterVoice] = {}

        # Channel settings
        self._channels: Dict[AudioChannel, ChannelSettings] = {
            channel: ChannelSettings() for channel in AudioChannel
        }

        # State
        self._state = AudioState()
        self._initialized = False

        # Speech queue
        self._speech_queue: List[SpeechRequest] = []
        self._current_speech: Optional[SpeechRequest] = None

        # Setup TTS
        if use_mock_tts:
            mock_engine = MockTTSEngine()
            self.tts_manager.register_engine(mock_engine, set_primary=True)

    def initialize(self) -> bool:
        """
        Initialize all audio subsystems.

        Returns True if successful.
        """
        # Initialize TTS engines
        self.tts_manager.initialize_all()

        # Check if at least one engine is available
        available = self.tts_manager.get_available_engines()
        if not available:
            return False

        self._initialized = True
        return True

    def shutdown(self) -> None:
        """Shutdown all audio subsystems."""
        self.tts_manager.shutdown_all()
        self.sound_mixer.stop_all()
        self._initialized = False

    def is_initialized(self) -> bool:
        """Check if engine is initialized."""
        return self._initialized

    # Voice Management

    def register_voice(self, voice: CharacterVoice) -> None:
        """Register a character voice."""
        self._voices[voice.character_id] = voice

    def create_voice_from_archetype(
        self,
        character_id: str,
        name: str,
        archetype: str,
        seed: Optional[int] = None
    ) -> CharacterVoice:
        """
        Create and register a voice from archetype.

        Args:
            character_id: Unique character identifier
            name: Character display name
            archetype: Voice archetype (detective, femme_fatale, etc.)
            seed: Random seed for reproducibility

        Returns:
            Created CharacterVoice
        """
        voice = VoiceFactory.create_from_archetype(
            character_id, name, archetype, seed
        )
        self.register_voice(voice)
        return voice

    def get_voice(self, character_id: str) -> Optional[CharacterVoice]:
        """Get a registered voice by character ID."""
        return self._voices.get(character_id)

    def set_voice_emotion(
        self,
        character_id: str,
        emotion: EmotionalState,
        intensity: float = 0.5
    ) -> bool:
        """
        Set a character's emotional state.

        Returns True if successful.
        """
        voice = self._voices.get(character_id)
        if not voice:
            return False

        voice.set_emotion(emotion, intensity)
        return True

    # Speech Synthesis

    def speak(
        self,
        character_id: str,
        text: str,
        emotion: Optional[EmotionalState] = None,
        effects_preset: Optional[str] = None
    ) -> Optional[AudioData]:
        """
        Synthesize speech for a character.

        Args:
            character_id: Character to speak
            text: Text to speak
            emotion: Optional emotional override
            effects_preset: Optional effects preset name

        Returns:
            Synthesized audio data, or None on error
        """
        voice = self._voices.get(character_id)
        if not voice:
            return None

        # Apply emotion if specified
        if emotion:
            voice.set_emotion(emotion)

        # Create TTS request
        request = TTSRequest(
            text=text,
            voice=voice
        )

        try:
            # Synthesize
            audio = self.tts_manager.synthesize(request)

            # Apply effects
            if effects_preset:
                chain = create_preset_chain(effects_preset)
                if chain:
                    audio = chain.process(audio)

            # Apply channel effects
            channel_settings = self._channels[AudioChannel.VOICE]
            if channel_settings.effects_chain:
                audio = channel_settings.effects_chain.process(audio)

            return audio

        except TTSEngineError:
            return None

    def queue_speech(self, request: SpeechRequest) -> None:
        """Add a speech request to the queue."""
        self._speech_queue.append(request)

    def process_speech_queue(self) -> Optional[AudioData]:
        """
        Process the next speech request in queue.

        Returns synthesized audio if available.
        """
        if not self._speech_queue:
            return None

        request = self._speech_queue.pop(0)
        self._current_speech = request

        if request.on_start:
            request.on_start()

        try:
            audio = self.speak(
                request.character_id,
                request.text,
                request.emotion,
                request.effects_preset
            )

            if audio and request.on_complete:
                request.on_complete(audio)

            self._current_speech = None
            return audio

        except Exception as e:
            if request.on_error:
                request.on_error(e)
            self._current_speech = None
            return None

    # Sound Effects

    def play_sound(
        self,
        sound_id: SoundID,
        properties: Optional[SoundProperties] = None
    ) -> str:
        """
        Play a sound effect from the library.

        Args:
            sound_id: Sound to play
            properties: Optional property overrides

        Returns:
            Instance ID for the playing sound
        """
        sound = self.sound_library.get_sound(sound_id)
        return self.sound_mixer.play(sound, properties)

    def play_generated_sound(
        self,
        sound_type: str,
        duration_ms: int = 500,
        properties: Optional[SoundProperties] = None,
        seed: Optional[int] = None
    ) -> str:
        """
        Play a procedurally generated sound.

        Args:
            sound_type: Type of sound to generate
            duration_ms: Duration in milliseconds
            properties: Sound properties
            seed: Random seed

        Returns:
            Instance ID
        """
        # Generate audio
        audio = self.sound_generator.generate(sound_type, duration_ms, seed)

        # Create temp sound effect
        sound = SoundEffect(
            id=f"gen_{sound_type}_{time.time()}",
            name=f"Generated {sound_type}",
            category=SoundCategory.AMBIENCE,
            properties=properties or SoundProperties()
        )
        sound._audio_data = audio

        return self.sound_mixer.play(sound, properties)

    def stop_sound(self, instance_id: str) -> None:
        """Stop a specific sound instance."""
        self.sound_mixer.stop(instance_id)

    def stop_all_sounds(self) -> None:
        """Stop all playing sounds."""
        self.sound_mixer.stop_all()

    # Ambience

    def set_ambience(self, preset_id: str) -> bool:
        """
        Set the ambient sound preset.

        Returns True if successful.
        """
        result = self.ambience_manager.set_preset(preset_id)
        if result:
            self._state.ambience_preset = preset_id
        return result

    def set_weather(self, weather: WeatherType, intensity: float = 0.5) -> None:
        """Set weather conditions for ambient audio."""
        self.ambience_manager.set_weather(weather, intensity)
        self._state.weather = weather

    def set_time_of_day(self, time: TimeOfDay) -> None:
        """Set time of day for ambient audio."""
        self.ambience_manager.set_time_of_day(time)
        self._state.time_of_day = time

    def set_tension(self, tension: float) -> None:
        """Set tension level (0.0 to 1.0)."""
        tension = max(0.0, min(1.0, tension))
        self.ambience_manager.set_tension(tension)
        self._state.tension = tension

    def get_ambient_audio(self, duration_ms: int = 5000) -> AudioData:
        """Generate ambient audio mix for current conditions."""
        return self.ambience_manager.generate_ambient_mix(duration_ms)

    # Channel Control

    def set_channel_volume(self, channel: AudioChannel, volume: float) -> None:
        """Set volume for an audio channel."""
        self._channels[channel].volume = max(0.0, min(1.0, volume))

    def get_channel_volume(self, channel: AudioChannel) -> float:
        """Get volume for an audio channel."""
        return self._channels[channel].volume

    def mute_channel(self, channel: AudioChannel) -> None:
        """Mute an audio channel."""
        self._channels[channel].muted = True

    def unmute_channel(self, channel: AudioChannel) -> None:
        """Unmute an audio channel."""
        self._channels[channel].muted = False

    def is_channel_muted(self, channel: AudioChannel) -> bool:
        """Check if a channel is muted."""
        return self._channels[channel].muted

    def set_channel_effects(
        self,
        channel: AudioChannel,
        effects: Optional[EffectsChain]
    ) -> None:
        """Set effects chain for a channel."""
        self._channels[channel].effects_chain = effects

    def set_master_volume(self, volume: float) -> None:
        """Set master volume."""
        volume = max(0.0, min(1.0, volume))
        self._channels[AudioChannel.MASTER].volume = volume
        self._state.master_volume = volume
        self.sound_mixer.master_volume = volume
        self.ambience_manager.set_master_volume(volume)

    def get_master_volume(self) -> float:
        """Get master volume."""
        return self._channels[AudioChannel.MASTER].volume

    # State

    def get_state(self) -> AudioState:
        """Get current audio state."""
        self._state.active_sounds = self.sound_mixer.get_playing_count()
        self._state.is_playing = (
            self._state.active_sounds > 0 or
            self._current_speech is not None
        )
        return self._state

    def update(self, delta_ms: float) -> None:
        """
        Update audio systems.

        Should be called each frame/tick.
        """
        # Update sound mixer
        self.sound_mixer.update(delta_ms)

        # Process speech queue if not currently speaking
        if not self._current_speech and self._speech_queue:
            self.process_speech_queue()

    # Serialization

    def save_state(self) -> Dict[str, Any]:
        """Save audio engine state for persistence."""
        return {
            'state': self._state.to_dict(),
            'voices': {
                cid: voice.to_dict()
                for cid, voice in self._voices.items()
            },
            'channels': {
                ch.value: {
                    'volume': settings.volume,
                    'muted': settings.muted
                }
                for ch, settings in self._channels.items()
            }
        }

    def load_state(self, data: Dict[str, Any]) -> None:
        """Load audio engine state from saved data."""
        # Restore state
        state_data = data.get('state', {})
        self._state.ambience_preset = state_data.get('ambience_preset')
        self._state.weather = WeatherType(state_data.get('weather', 'clear'))
        self._state.time_of_day = TimeOfDay(state_data.get('time_of_day', 'night'))
        self._state.tension = state_data.get('tension', 0.0)
        self._state.master_volume = state_data.get('master_volume', 1.0)

        # Apply state
        if self._state.ambience_preset:
            self.set_ambience(self._state.ambience_preset)
        self.set_weather(self._state.weather)
        self.set_time_of_day(self._state.time_of_day)
        self.set_tension(self._state.tension)
        self.set_master_volume(self._state.master_volume)

        # Restore voices
        voices_data = data.get('voices', {})
        for voice_data in voices_data.values():
            voice = CharacterVoice.from_dict(voice_data)
            self.register_voice(voice)

        # Restore channel settings
        channels_data = data.get('channels', {})
        for ch_name, ch_data in channels_data.items():
            try:
                channel = AudioChannel(ch_name)
                self._channels[channel].volume = ch_data.get('volume', 1.0)
                self._channels[channel].muted = ch_data.get('muted', False)
            except ValueError:
                pass


# Convenience function for creating configured engine
def create_audio_engine(
    use_mock_tts: bool = True,
    auto_initialize: bool = True
) -> AudioEngine:
    """
    Create and optionally initialize an audio engine.

    Args:
        use_mock_tts: Use mock TTS engine (for testing)
        auto_initialize: Automatically initialize on creation

    Returns:
        Configured AudioEngine instance
    """
    engine = AudioEngine(use_mock_tts=use_mock_tts)

    if auto_initialize:
        engine.initialize()

    return engine
