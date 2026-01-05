"""
Audio & TTS System - Full audio experience.

Phase 9 Implementation: Text-to-speech character voices,
sound effects, ambient audio, and atmospheric soundscapes.

Core principle: Each character has a distinct voice,
and the world sounds alive.
"""

# Voice System
from .voice import (
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

# TTS Engines
from .tts_engine import (
    TTSEngine,
    TTSEngineType,
    TTSEngineManager,
    TTSEngineError,
    TTSRequest,
    AudioData,
    AudioFormat,
    MockTTSEngine,
    CoquiTTSEngine,
    PiperTTSEngine
)

# Effects
from .effects import (
    AudioEffect,
    EffectsChain,
    EffectType,
    EffectParameters,
    PitchShiftEffect,
    PitchShiftParams,
    DistortionEffect,
    DistortionParams,
    ReverbEffect,
    ReverbParams,
    DelayEffect,
    DelayParams,
    FilterEffect,
    FilterParams,
    TelephoneEffect,
    RadioEffect,
    create_preset_chain,
    EFFECT_PRESETS
)

# Sound System
from .sound import (
    SoundEffect,
    SoundCategory,
    SoundTrigger,
    SoundProperties,
    SoundGenerator,
    SoundInstance,
    SoundMixer
)

# Ambience
from .ambience import (
    AmbientLayer,
    AmbiencePreset,
    AmbienceType,
    AmbienceManager,
    WeatherType,
    TimeOfDay,
    WeatherAudio,
    TensionAudio
)

# Sound Library
from .library import (
    SoundLibrary,
    SoundID,
    SoundDefinition,
    SOUND_LIBRARY
)

# Audio Engine
from .audio_engine import (
    AudioEngine,
    AudioChannel,
    ChannelSettings,
    SpeechRequest,
    AudioState,
    create_audio_engine
)

__all__ = [
    # Voice
    "CharacterVoice",
    "VoiceParameters",
    "VoiceGender",
    "VoiceAge",
    "Accent",
    "EmotionalState",
    "VoiceFactory",
    "ARCHETYPE_VOICE_TEMPLATES",
    "EMOTION_MODULATIONS",

    # TTS
    "TTSEngine",
    "TTSEngineType",
    "TTSEngineManager",
    "TTSEngineError",
    "TTSRequest",
    "AudioData",
    "AudioFormat",
    "MockTTSEngine",
    "CoquiTTSEngine",
    "PiperTTSEngine",

    # Effects
    "AudioEffect",
    "EffectsChain",
    "EffectType",
    "EffectParameters",
    "PitchShiftEffect",
    "PitchShiftParams",
    "DistortionEffect",
    "DistortionParams",
    "ReverbEffect",
    "ReverbParams",
    "DelayEffect",
    "DelayParams",
    "FilterEffect",
    "FilterParams",
    "TelephoneEffect",
    "RadioEffect",
    "create_preset_chain",
    "EFFECT_PRESETS",

    # Sound
    "SoundEffect",
    "SoundCategory",
    "SoundTrigger",
    "SoundProperties",
    "SoundGenerator",
    "SoundInstance",
    "SoundMixer",

    # Ambience
    "AmbientLayer",
    "AmbiencePreset",
    "AmbienceType",
    "AmbienceManager",
    "WeatherType",
    "TimeOfDay",
    "WeatherAudio",
    "TensionAudio",

    # Library
    "SoundLibrary",
    "SoundID",
    "SoundDefinition",
    "SOUND_LIBRARY",

    # Engine
    "AudioEngine",
    "AudioChannel",
    "ChannelSettings",
    "SpeechRequest",
    "AudioState",
    "create_audio_engine",
]
