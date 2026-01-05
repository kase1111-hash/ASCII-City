"""
Unified Audio Synthesizer for ShadowEngine.

Coordinates all audio synthesis components including TTS,
effects processing, motif generation, and ambient sound.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List, Any, Callable
import time

from .tts import TTSEngine, TTSResult, TTSConfig, create_tts_engine
from .voice import VoiceProfile, VoiceLibrary, CharacterVoiceTTS as CharacterVoice, EmotionalState
from .effects import EffectsChain, Effect, EffectType
from .motif import Motif, MotifGenerator, ThemeEngine, TensionMapper
from .ambient import AmbientEngine, AmbientLayer, AmbientConfig


class AudioPriority(Enum):
    """Priority levels for audio playback."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
    SYSTEM = 4


@dataclass
class SynthesisConfig:
    """Configuration for audio synthesizer."""

    # Engine settings
    tts_engine_type: str = "mock"
    sample_rate: int = 22050
    buffer_size: int = 1024

    # Volume settings
    master_volume: float = 0.8
    voice_volume: float = 1.0
    effects_volume: float = 1.0
    ambient_volume: float = 0.7
    music_volume: float = 0.5

    # Quality
    quality: str = "medium"

    # Caching
    cache_enabled: bool = True
    cache_max_mb: int = 100

    # Playback
    max_simultaneous_sounds: int = 16

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tts_engine_type": self.tts_engine_type,
            "sample_rate": self.sample_rate,
            "buffer_size": self.buffer_size,
            "master_volume": self.master_volume,
            "voice_volume": self.voice_volume,
            "effects_volume": self.effects_volume,
            "ambient_volume": self.ambient_volume,
            "music_volume": self.music_volume,
            "quality": self.quality,
            "cache_enabled": self.cache_enabled,
            "cache_max_mb": self.cache_max_mb,
            "max_simultaneous_sounds": self.max_simultaneous_sounds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SynthesisConfig':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AudioEvent:
    """An audio event to be processed."""

    id: str
    event_type: str  # "speech", "effect", "ambient", "music"
    priority: AudioPriority = AudioPriority.NORMAL

    # Content
    text: Optional[str] = None
    character_id: Optional[str] = None
    effect_preset: Optional[str] = None
    ambient_type: Optional[str] = None
    motif_id: Optional[str] = None

    # Playback settings
    volume: float = 1.0
    pan: float = 0.0  # -1.0 left, 0.0 center, 1.0 right
    pitch: float = 1.0
    delay_ms: float = 0.0

    # State
    queued_at: float = 0.0
    started_at: Optional[float] = None
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "priority": self.priority.value,
            "text": self.text,
            "character_id": self.character_id,
            "effect_preset": self.effect_preset,
            "ambient_type": self.ambient_type,
            "motif_id": self.motif_id,
            "volume": self.volume,
            "pan": self.pan,
            "pitch": self.pitch,
            "delay_ms": self.delay_ms,
            "queued_at": self.queued_at,
            "started_at": self.started_at,
            "completed": self.completed,
        }


@dataclass
class SynthesisResult:
    """Result of audio synthesis."""

    event_id: str
    audio_data: bytes = b""
    sample_rate: int = 22050
    duration_ms: float = 0.0

    # Processing info
    synthesis_time_ms: float = 0.0
    cached: bool = False

    # Status
    success: bool = True
    error: Optional[str] = None

    @property
    def is_empty(self) -> bool:
        """Check if result is empty."""
        return len(self.audio_data) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "sample_rate": self.sample_rate,
            "duration_ms": self.duration_ms,
            "synthesis_time_ms": self.synthesis_time_ms,
            "cached": self.cached,
            "success": self.success,
            "error": self.error,
            "audio_size_bytes": len(self.audio_data),
        }


class AudioMixer:
    """Mixes multiple audio streams."""

    def __init__(self, sample_rate: int = 22050, channels: int = 2):
        self.sample_rate = sample_rate
        self.channels = channels
        self._active_streams: Dict[str, bytes] = {}
        self._volumes: Dict[str, float] = {}
        self._pans: Dict[str, float] = {}

    def add_stream(self, stream_id: str, audio_data: bytes,
                   volume: float = 1.0, pan: float = 0.0) -> None:
        """Add an audio stream to the mixer."""
        self._active_streams[stream_id] = audio_data
        self._volumes[stream_id] = volume
        self._pans[stream_id] = pan

    def remove_stream(self, stream_id: str) -> None:
        """Remove an audio stream."""
        self._active_streams.pop(stream_id, None)
        self._volumes.pop(stream_id, None)
        self._pans.pop(stream_id, None)

    def set_volume(self, stream_id: str, volume: float) -> None:
        """Set volume for a stream."""
        if stream_id in self._volumes:
            self._volumes[stream_id] = max(0.0, min(1.0, volume))

    def set_pan(self, stream_id: str, pan: float) -> None:
        """Set pan for a stream."""
        if stream_id in self._pans:
            self._pans[stream_id] = max(-1.0, min(1.0, pan))

    def get_active_streams(self) -> List[str]:
        """Get list of active stream IDs."""
        return list(self._active_streams.keys())

    def mix(self, duration_ms: float) -> bytes:
        """Mix all active streams for the given duration."""
        if not self._active_streams:
            # Return silence
            num_samples = int((duration_ms / 1000.0) * self.sample_rate) * self.channels
            return b"\x00" * (num_samples * 2)

        # In a real implementation, this would actually mix audio
        # For simulation, return combined size
        total_size = sum(len(data) for data in self._active_streams.values())
        return b"\x20" * min(total_size, int((duration_ms / 1000.0) * self.sample_rate * 4))

    def clear(self) -> None:
        """Clear all streams."""
        self._active_streams.clear()
        self._volumes.clear()
        self._pans.clear()


class AudioSynthesizer:
    """Main audio synthesis coordinator."""

    def __init__(self, config: Optional[SynthesisConfig] = None):
        self.config = config or SynthesisConfig()

        # Initialize components
        self._tts_engine = create_tts_engine(
            self.config.tts_engine_type,
            sample_rate=self.config.sample_rate,
            cache_enabled=self.config.cache_enabled,
        )

        self._voice_library = VoiceLibrary()
        self._effects_chains: Dict[str, EffectsChain] = {}
        self._theme_engine = ThemeEngine()
        self._ambient_engine = AmbientEngine(AmbientConfig(
            master_volume=self.config.ambient_volume,
            sample_rate=self.config.sample_rate,
        ))
        self._mixer = AudioMixer(self.config.sample_rate)

        # Event queue and state
        self._event_queue: List[AudioEvent] = []
        self._active_events: Dict[str, AudioEvent] = {}
        self._event_counter = 0

        # Callbacks
        self._on_complete_callbacks: List[Callable[[SynthesisResult], None]] = []

        # Initialize TTS
        self._tts_engine.initialize()

    @property
    def is_initialized(self) -> bool:
        """Check if synthesizer is initialized."""
        return self._tts_engine.is_initialized

    @property
    def voice_library(self) -> VoiceLibrary:
        """Get voice library."""
        return self._voice_library

    @property
    def theme_engine(self) -> ThemeEngine:
        """Get theme engine."""
        return self._theme_engine

    @property
    def ambient_engine(self) -> AmbientEngine:
        """Get ambient engine."""
        return self._ambient_engine

    def set_master_volume(self, volume: float) -> None:
        """Set master volume."""
        self.config.master_volume = max(0.0, min(1.0, volume))

    def set_voice_volume(self, volume: float) -> None:
        """Set voice volume."""
        self.config.voice_volume = max(0.0, min(1.0, volume))

    def set_ambient_volume(self, volume: float) -> None:
        """Set ambient volume."""
        self.config.ambient_volume = max(0.0, min(1.0, volume))
        self._ambient_engine.master_volume = volume

    def set_music_volume(self, volume: float) -> None:
        """Set music volume."""
        self.config.music_volume = max(0.0, min(1.0, volume))

    # Speech synthesis

    def synthesize_speech(self, text: str, character_id: Optional[str] = None,
                          emotion: Optional[EmotionalState] = None,
                          effects_preset: Optional[str] = None) -> SynthesisResult:
        """Synthesize speech for a character."""
        start_time = time.time()
        event_id = f"speech_{self._event_counter}"
        self._event_counter += 1

        # Get character voice
        voice_id = "default"
        pitch = 1.0
        speed = 1.0

        if character_id:
            char_voice = self._voice_library.get_character_voice(character_id)
            if char_voice:
                if emotion:
                    char_voice.set_emotion(emotion)
                profile = char_voice.get_effective_profile()
                voice_id = profile.base_voice
                pitch = profile.get_pitch_multiplier()
                speed = profile.get_speed_multiplier()

        # Generate TTS
        tts_result = self._tts_engine.synthesize(text, voice_id, speed, pitch)

        audio_data = tts_result.audio_data

        # Apply effects if specified
        if effects_preset:
            chain = self._get_or_create_effects_chain(effects_preset)
            audio_data = chain.process(audio_data, self.config.sample_rate)

        # Apply volume
        # In real implementation, would scale audio data

        synthesis_time = (time.time() - start_time) * 1000

        return SynthesisResult(
            event_id=event_id,
            audio_data=audio_data,
            sample_rate=self.config.sample_rate,
            duration_ms=tts_result.duration_ms,
            synthesis_time_ms=synthesis_time,
            cached=tts_result.cached,
            success=True,
        )

    def speak(self, character_id: str, text: str,
              emotion: Optional[EmotionalState] = None) -> SynthesisResult:
        """Convenient method to make a character speak."""
        return self.synthesize_speech(text, character_id, emotion)

    # Sound effects

    def synthesize_effect(self, effect_type: str, tts_seed: Optional[str] = None,
                          preset: Optional[str] = None) -> SynthesisResult:
        """Synthesize a sound effect using TTS and processing."""
        start_time = time.time()
        event_id = f"effect_{self._event_counter}"
        self._event_counter += 1

        # Default TTS seeds for effects
        effect_seeds = {
            "gunshot": "bang",
            "footstep": "tap",
            "door_slam": "boom",
            "glass_break": "crash tinkle",
            "splash": "splash",
            "thunder": "boom rumble",
            "scream": "ahhh",
            "whisper": "psst",
            "heartbeat": "thump thump",
            "breathing": "hah hah",
        }

        seed = tts_seed or effect_seeds.get(effect_type, effect_type)

        # Generate base audio from TTS
        tts_result = self._tts_engine.synthesize(seed)
        audio_data = tts_result.audio_data

        # Apply effect processing
        preset = preset or effect_type
        chain = self._get_or_create_effects_chain(preset)
        if chain:
            audio_data = chain.process(audio_data, self.config.sample_rate)

        synthesis_time = (time.time() - start_time) * 1000

        return SynthesisResult(
            event_id=event_id,
            audio_data=audio_data,
            sample_rate=self.config.sample_rate,
            duration_ms=tts_result.duration_ms,
            synthesis_time_ms=synthesis_time,
            success=True,
        )

    def play_effect(self, effect_type: str, volume: float = 1.0,
                    pan: float = 0.0) -> str:
        """Play a sound effect and return event ID."""
        result = self.synthesize_effect(effect_type)
        if result.success:
            self._mixer.add_stream(result.event_id, result.audio_data, volume, pan)
        return result.event_id

    # Music and themes

    def generate_theme(self, theme_id: str, mood: str = "noir") -> List[Motif]:
        """Generate a musical theme."""
        return self._theme_engine.generate_theme(theme_id, mood)

    def set_tension(self, tension: float) -> None:
        """Set tension level for music and ambient."""
        self._theme_engine.set_tension(tension)
        self._ambient_engine.set_tension(tension)

    # Ambient

    def set_weather(self, weather_type: str, intensity: float = 1.0) -> None:
        """Set weather for ambient sound."""
        self._ambient_engine.set_weather(weather_type, intensity)

    def set_location(self, location_type: str) -> None:
        """Set location for ambient sound."""
        self._ambient_engine.set_location(location_type)

    # Event queue

    def queue_event(self, event: AudioEvent) -> str:
        """Queue an audio event for processing."""
        event.queued_at = time.time()
        self._event_queue.append(event)
        self._event_queue.sort(key=lambda e: (e.priority.value, e.queued_at), reverse=True)
        return event.id

    def queue_speech(self, text: str, character_id: Optional[str] = None,
                     priority: AudioPriority = AudioPriority.NORMAL) -> str:
        """Queue a speech event."""
        event_id = f"speech_{self._event_counter}"
        self._event_counter += 1

        event = AudioEvent(
            id=event_id,
            event_type="speech",
            priority=priority,
            text=text,
            character_id=character_id,
        )

        return self.queue_event(event)

    def process_queue(self) -> List[SynthesisResult]:
        """Process queued events and return results."""
        results = []

        while self._event_queue and len(self._active_events) < self.config.max_simultaneous_sounds:
            event = self._event_queue.pop(0)
            event.started_at = time.time()

            if event.event_type == "speech":
                result = self.synthesize_speech(
                    event.text or "",
                    event.character_id,
                    effects_preset=event.effect_preset,
                )
            elif event.event_type == "effect":
                result = self.synthesize_effect(
                    event.effect_preset or "default",
                )
            else:
                # Unknown event type
                result = SynthesisResult(
                    event_id=event.id,
                    success=False,
                    error=f"Unknown event type: {event.event_type}",
                )

            results.append(result)
            event.completed = True

            for callback in self._on_complete_callbacks:
                callback(result)

        return results

    # Effects chain management

    def _get_or_create_effects_chain(self, preset_name: str) -> EffectsChain:
        """Get or create an effects chain for a preset."""
        if preset_name not in self._effects_chains:
            chain = EffectsChain()
            if not chain.load_preset(preset_name):
                # Create empty chain if preset doesn't exist
                pass
            self._effects_chains[preset_name] = chain

        return self._effects_chains[preset_name]

    def create_effects_chain(self, name: str) -> EffectsChain:
        """Create a new effects chain."""
        chain = EffectsChain()
        self._effects_chains[name] = chain
        return chain

    def get_effects_chain(self, name: str) -> Optional[EffectsChain]:
        """Get an effects chain by name."""
        return self._effects_chains.get(name)

    # Character voice management

    def register_character_voice(self, character_id: str,
                                  preset: Optional[str] = None,
                                  profile: Optional[VoiceProfile] = None) -> CharacterVoice:
        """Register a character's voice."""
        if profile is None:
            if preset:
                profile = self._voice_library.get_preset(preset)
            if profile is None:
                profile = self._voice_library.generate_random_profile()

        return self._voice_library.create_character_voice(character_id, profile)

    def get_character_voice(self, character_id: str) -> Optional[CharacterVoice]:
        """Get a character's voice configuration."""
        return self._voice_library.get_character_voice(character_id)

    # Callbacks

    def on_complete(self, callback: Callable[[SynthesisResult], None]) -> None:
        """Register a callback for completed synthesis."""
        self._on_complete_callbacks.append(callback)

    # Mixing

    def get_mix(self, duration_ms: float) -> bytes:
        """Get mixed audio output."""
        # Add ambient to mixer
        ambient_audio = self._ambient_engine.generate_mix(duration_ms, self.config.sample_rate)
        self._mixer.add_stream("ambient", ambient_audio,
                               self.config.ambient_volume * self.config.master_volume)

        return self._mixer.mix(duration_ms)

    def update(self, dt_ms: float) -> None:
        """Update synthesizer state."""
        self._theme_engine.update(dt_ms / 1000.0)
        self._ambient_engine.update(dt_ms)

    # Cleanup

    def shutdown(self) -> None:
        """Shutdown synthesizer."""
        self._tts_engine.shutdown()
        self._mixer.clear()

    def clear_cache(self) -> int:
        """Clear synthesis cache. Returns items cleared."""
        return self._tts_engine.clear_cache()

    # Serialization

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config": self.config.to_dict(),
            "voice_library": self._voice_library.to_dict(),
            "theme_engine": self._theme_engine.to_dict(),
            "ambient_engine": self._ambient_engine.to_dict(),
            "event_counter": self._event_counter,
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            "initialized": self.is_initialized,
            "queued_events": len(self._event_queue),
            "active_events": len(self._active_events),
            "mixer_streams": len(self._mixer.get_active_streams()),
            "ambient_layers": self._ambient_engine.get_layer_count(),
            "tension": self._theme_engine.tension,
            "master_volume": self.config.master_volume,
        }
