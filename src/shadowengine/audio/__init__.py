"""
Audio Synthesis System - Phase 9: Audio & TTS

This module provides comprehensive audio synthesis capabilities for the ShadowEngine,
including text-to-speech for character voices, procedural sound generation,
post-processing effects, and atmospheric audio.

Key Components:
- TTSEngine: Text-to-speech synthesis with multiple backend support
- VoiceProfile: Character voice personality customization
- EffectsChain: Post-processing pipeline for audio effects
- MotifGenerator: Procedural music/theme generation
- AmbientEngine: Environmental and atmospheric sound
- AudioSynthesizer: Unified synthesis coordinator
"""

from .tts import (
    TTSEngine, TTSResult, TTSStatus, TTSConfig,
    CoquiTTSEngine, PiperTTSEngine, MockTTSEngine,
    create_tts_engine
)
from .voice import (
    VoiceProfile, VoiceParameter, EmotionalState,
    VoiceModulator, VoiceLibrary, CharacterVoice
)
from .effects import (
    Effect, EffectType, EffectParameter,
    EffectsChain, EffectPreset,
    PitchShift, TimeStretch, Reverb, Distortion,
    EQ, Delay, Compression, Tremolo
)
from .motif import (
    Motif, MotifType, MusicalKey, TimeSignature,
    MotifGenerator, ThemeEngine, TensionMapper,
    Note, Chord, Rhythm
)
from .ambient import (
    AmbientLayer, AmbientConfig, AmbientType,
    AmbientEngine, WeatherAudio, LocationAudio,
    TensionAudio
)
from .synthesis import (
    AudioSynthesizer, SynthesisResult, SynthesisConfig,
    AudioEvent, AudioPriority, AudioMixer
)

__all__ = [
    # TTS
    'TTSEngine', 'TTSResult', 'TTSStatus', 'TTSConfig',
    'CoquiTTSEngine', 'PiperTTSEngine', 'MockTTSEngine',
    'create_tts_engine',
    # Voice
    'VoiceProfile', 'VoiceParameter', 'EmotionalState',
    'VoiceModulator', 'VoiceLibrary', 'CharacterVoice',
    # Effects
    'Effect', 'EffectType', 'EffectParameter',
    'EffectsChain', 'EffectPreset',
    'PitchShift', 'TimeStretch', 'Reverb', 'Distortion',
    'EQ', 'Delay', 'Compression', 'Tremolo',
    # Motif
    'Motif', 'MotifType', 'MusicalKey', 'TimeSignature',
    'MotifGenerator', 'ThemeEngine', 'TensionMapper',
    'Note', 'Chord', 'Rhythm',
    # Ambient
    'AmbientLayer', 'AmbientConfig', 'AmbientType',
    'AmbientEngine', 'WeatherAudio', 'LocationAudio',
    'TensionAudio',
    # Synthesis
    'AudioSynthesizer', 'SynthesisResult', 'SynthesisConfig',
    'AudioEvent', 'AudioPriority', 'AudioMixer',
]
