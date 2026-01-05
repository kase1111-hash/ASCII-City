"""
Shared test fixtures for audio synthesis tests.
"""

import pytest
from src.shadowengine.audio.tts import (
    TTSEngine, TTSResult, TTSConfig,
    MockTTSEngine, CoquiTTSEngine, PiperTTSEngine,
)
from src.shadowengine.audio.voice import (
    VoiceProfile, VoiceParameter, EmotionalState,
    VoiceModulator, VoiceLibrary, CharacterVoiceTTS as CharacterVoice,
)
from src.shadowengine.audio.effects import (
    Effect, EffectsChain, EffectPreset,
    PitchShift, TimeStretch, Reverb, Distortion,
    EQ, Delay, Compression, Tremolo,
)
from src.shadowengine.audio.motif import (
    Motif, MotifType, MusicalKey, TimeSignature,
    MotifGenerator, ThemeEngine, TensionMapper,
    Note, Chord, Rhythm,
)
from src.shadowengine.audio.ambient import (
    AmbientLayer, AmbientConfig, AmbientType,
    AmbientEngine, WeatherAudio, LocationAudio, TensionAudio,
)
from src.shadowengine.audio.synthesis import (
    AudioSynthesizer, SynthesisResult, SynthesisConfig,
    AudioEvent, AudioPriority, AudioMixer,
)


# =============================================================================
# TTS Fixtures
# =============================================================================

@pytest.fixture
def tts_config():
    """Basic TTS configuration."""
    return TTSConfig(
        model_name="test",
        sample_rate=22050,
        cache_enabled=True,
    )


@pytest.fixture
def mock_tts(tts_config):
    """Mock TTS engine."""
    engine = MockTTSEngine(tts_config)
    engine.initialize()
    return engine


@pytest.fixture
def coqui_tts(tts_config):
    """Coqui TTS engine."""
    engine = CoquiTTSEngine(tts_config)
    engine.initialize()
    return engine


@pytest.fixture
def piper_tts(tts_config):
    """Piper TTS engine."""
    engine = PiperTTSEngine(tts_config)
    engine.initialize()
    return engine


# =============================================================================
# Voice Fixtures
# =============================================================================

@pytest.fixture
def voice_profile():
    """Basic voice profile."""
    return VoiceProfile(
        voice_id="test_voice",
        base_voice="male_1",
        name="Test Voice",
        pitch=0.0,
        speed=0.0,
    )


@pytest.fixture
def gruff_voice_profile():
    """Gruff male voice profile."""
    return VoiceProfile(
        voice_id="gruff_male",
        base_voice="male_1",
        name="Gruff Male",
        pitch=-0.3,
        speed=-0.1,
        roughness=0.5,
        resonance=0.3,
        age_modifier=0.3,
    )


@pytest.fixture
def character_voice(voice_profile):
    """Character voice with profile."""
    return CharacterVoice(
        character_id="test_char",
        profile=voice_profile,
    )


@pytest.fixture
def voice_library():
    """Voice library with presets."""
    return VoiceLibrary()


@pytest.fixture
def voice_modulator():
    """Voice modulator with fixed seed."""
    return VoiceModulator(seed=42)


# =============================================================================
# Effects Fixtures
# =============================================================================

@pytest.fixture
def pitch_shift():
    """Pitch shift effect."""
    return PitchShift(semitones=2)


@pytest.fixture
def reverb():
    """Reverb effect."""
    return Reverb(room_size=0.5, damping=0.5)


@pytest.fixture
def distortion():
    """Distortion effect."""
    return Distortion(drive=0.5, tone=0.5)


@pytest.fixture
def effects_chain():
    """Empty effects chain."""
    return EffectsChain()


@pytest.fixture
def populated_effects_chain():
    """Effects chain with several effects."""
    chain = EffectsChain()
    chain.add_effect(PitchShift(semitones=-2))
    chain.add_effect(Reverb(room_size=0.7))
    chain.add_effect(Compression(threshold=-10, ratio=4))
    return chain


# =============================================================================
# Motif Fixtures
# =============================================================================

@pytest.fixture
def note():
    """Basic note."""
    return Note(pitch="C", octave=4, duration=1.0, velocity=0.8)


@pytest.fixture
def chord():
    """Basic chord."""
    return Chord(root="C", quality="minor", octave=4)


@pytest.fixture
def rhythm():
    """Basic rhythm pattern."""
    return Rhythm(
        pattern=[1.0, 0.5, 0.5, 1.0, 1.0],
        time_signature=TimeSignature.FOUR_FOUR,
        tempo=120,
    )


@pytest.fixture
def motif_generator():
    """Motif generator with fixed seed."""
    return MotifGenerator(seed=42)


@pytest.fixture
def theme_engine():
    """Theme engine with fixed seed."""
    return ThemeEngine(seed=42)


@pytest.fixture
def tension_mapper():
    """Tension mapper."""
    return TensionMapper()


# =============================================================================
# Ambient Fixtures
# =============================================================================

@pytest.fixture
def ambient_config():
    """Ambient sound configuration."""
    return AmbientConfig(
        master_volume=0.7,
        fade_time_ms=2000.0,
        max_layers=8,
    )


@pytest.fixture
def ambient_layer():
    """Basic ambient layer."""
    return AmbientLayer(
        id="test_ambient",
        ambient_type=AmbientType.RAIN,
        volume=0.5,
    )


@pytest.fixture
def ambient_engine(ambient_config):
    """Ambient sound engine."""
    return AmbientEngine(ambient_config)


@pytest.fixture
def weather_audio():
    """Weather audio manager."""
    return WeatherAudio()


@pytest.fixture
def location_audio():
    """Location audio manager."""
    return LocationAudio()


@pytest.fixture
def tension_audio():
    """Tension audio manager."""
    return TensionAudio()


# =============================================================================
# Synthesis Fixtures
# =============================================================================

@pytest.fixture
def synthesis_config():
    """Synthesis configuration."""
    return SynthesisConfig(
        tts_engine_type="mock",
        sample_rate=22050,
        master_volume=0.8,
    )


@pytest.fixture
def audio_mixer():
    """Audio mixer."""
    return AudioMixer(sample_rate=22050)


@pytest.fixture
def audio_synthesizer(synthesis_config):
    """Audio synthesizer."""
    return AudioSynthesizer(synthesis_config)


@pytest.fixture
def audio_event():
    """Basic audio event."""
    return AudioEvent(
        id="test_event",
        event_type="speech",
        text="Hello world",
        priority=AudioPriority.NORMAL,
    )
