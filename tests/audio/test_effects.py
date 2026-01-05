"""Tests for the audio effects system."""

import pytest
import struct
from src.shadowengine.audio.effects import (
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
from src.shadowengine.audio.tts_engine import AudioData, AudioFormat


def create_test_audio(duration_ms: int = 500, frequency: float = 440.0) -> AudioData:
    """Create test audio data with a sine wave."""
    import math
    sample_rate = 22050
    num_samples = int((duration_ms / 1000.0) * sample_rate)

    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = int(math.sin(2 * math.pi * frequency * t) * 16000)
        samples.append(sample)

    data = bytearray()
    for sample in samples:
        data.extend(struct.pack('<h', sample))

    return AudioData(
        data=bytes(data),
        format=AudioFormat.RAW,
        sample_rate=sample_rate,
        channels=1,
        bit_depth=16,
        duration_ms=duration_ms
    )


class TestEffectParameters:
    """Tests for EffectParameters."""

    def test_default_parameters(self):
        """Test default parameter values."""
        params = EffectParameters()
        assert params.enabled is True
        assert params.mix == 1.0

    def test_to_dict(self):
        """Test serialization."""
        params = EffectParameters(enabled=True, mix=0.5)
        d = params.to_dict()
        assert d['enabled'] is True
        assert d['mix'] == 0.5


class TestPitchShiftEffect:
    """Tests for PitchShiftEffect."""

    def test_no_shift(self):
        """Test with zero semitone shift."""
        effect = PitchShiftEffect(PitchShiftParams(semitones=0))
        audio = create_test_audio()
        result = effect.process(audio)

        # Should be identical
        assert len(result.data) == len(audio.data)

    def test_pitch_up(self):
        """Test pitch shift up."""
        effect = PitchShiftEffect(PitchShiftParams(semitones=12))  # One octave up
        audio = create_test_audio()
        result = effect.process(audio)

        # Pitched up audio should be shorter
        assert len(result.data) < len(audio.data)

    def test_pitch_down(self):
        """Test pitch shift down."""
        effect = PitchShiftEffect(PitchShiftParams(semitones=-12))  # One octave down
        audio = create_test_audio()
        result = effect.process(audio)

        # Pitched down audio should be longer
        assert len(result.data) > len(audio.data)

    def test_effect_disabled(self):
        """Test disabled effect passes through."""
        effect = PitchShiftEffect(PitchShiftParams(semitones=12, enabled=False))
        audio = create_test_audio()
        result = effect.process(audio)

        assert result.data == audio.data

    def test_effect_properties(self):
        """Test effect properties."""
        effect = PitchShiftEffect()
        assert effect.effect_type == EffectType.PITCH_SHIFT
        assert effect.name == "Pitch Shift"


class TestDistortionEffect:
    """Tests for DistortionEffect."""

    def test_soft_distortion(self):
        """Test soft clipping distortion."""
        effect = DistortionEffect(DistortionParams(drive=0.5, type="soft"))
        audio = create_test_audio()
        result = effect.process(audio)

        assert len(result.data) == len(audio.data)

    def test_hard_distortion(self):
        """Test hard clipping distortion."""
        effect = DistortionEffect(DistortionParams(drive=0.8, type="hard"))
        audio = create_test_audio()
        result = effect.process(audio)

        assert len(result.data) == len(audio.data)

    def test_fuzz_distortion(self):
        """Test fuzz distortion."""
        effect = DistortionEffect(DistortionParams(drive=0.7, type="fuzz"))
        audio = create_test_audio()
        result = effect.process(audio)

        assert len(result.data) == len(audio.data)

    def test_drive_changes_output(self):
        """Test that drive level changes output."""
        low_drive = DistortionEffect(DistortionParams(drive=0.1))
        high_drive = DistortionEffect(DistortionParams(drive=0.9))

        audio = create_test_audio()
        low_result = low_drive.process(audio)
        high_result = high_drive.process(audio)

        # Results should be different
        assert low_result.data != high_result.data

    def test_effect_properties(self):
        """Test effect properties."""
        effect = DistortionEffect()
        assert effect.effect_type == EffectType.DISTORTION
        assert effect.name == "Distortion"


class TestReverbEffect:
    """Tests for ReverbEffect."""

    def test_reverb_extends_audio(self):
        """Test that reverb adds tail to audio."""
        effect = ReverbEffect(ReverbParams(room_size=0.8, mix=1.0))
        audio = create_test_audio(duration_ms=200)
        result = effect.process(audio)

        # Output should have reverb tail
        assert len(result.data) >= len(audio.data)

    def test_room_size_affects_output(self):
        """Test room size parameter affects output."""
        small_room = ReverbEffect(ReverbParams(room_size=0.1, mix=1.0))
        large_room = ReverbEffect(ReverbParams(room_size=0.9, mix=1.0))

        audio = create_test_audio()
        small_result = small_room.process(audio)
        large_result = large_room.process(audio)

        assert small_result.data != large_result.data

    def test_effect_properties(self):
        """Test effect properties."""
        effect = ReverbEffect()
        assert effect.effect_type == EffectType.REVERB
        assert effect.name == "Reverb"


class TestDelayEffect:
    """Tests for DelayEffect."""

    def test_delay_effect(self):
        """Test basic delay."""
        effect = DelayEffect(DelayParams(time_ms=100, feedback=0.3))
        audio = create_test_audio()
        result = effect.process(audio)

        assert len(result.data) == len(audio.data)

    def test_feedback_affects_output(self):
        """Test feedback parameter."""
        low_feedback = DelayEffect(DelayParams(time_ms=100, feedback=0.1))
        high_feedback = DelayEffect(DelayParams(time_ms=100, feedback=0.7))

        audio = create_test_audio()
        low_result = low_feedback.process(audio)
        high_result = high_feedback.process(audio)

        assert low_result.data != high_result.data

    def test_effect_properties(self):
        """Test effect properties."""
        effect = DelayEffect()
        assert effect.effect_type == EffectType.DELAY
        assert effect.name == "Delay"


class TestFilterEffect:
    """Tests for FilterEffect."""

    def test_lowpass_filter(self):
        """Test lowpass filter."""
        effect = FilterEffect(FilterParams(filter_type="lowpass", frequency=1000))
        audio = create_test_audio()
        result = effect.process(audio)

        assert len(result.data) == len(audio.data)

    def test_highpass_filter(self):
        """Test highpass filter."""
        effect = FilterEffect(FilterParams(filter_type="highpass", frequency=500))
        audio = create_test_audio()
        result = effect.process(audio)

        assert len(result.data) == len(audio.data)

    def test_bandpass_filter(self):
        """Test bandpass filter."""
        effect = FilterEffect(FilterParams(filter_type="bandpass", frequency=1500))
        audio = create_test_audio()
        result = effect.process(audio)

        assert len(result.data) == len(audio.data)

    def test_frequency_affects_output(self):
        """Test that frequency changes output."""
        low_freq = FilterEffect(FilterParams(filter_type="lowpass", frequency=200))
        high_freq = FilterEffect(FilterParams(filter_type="lowpass", frequency=5000))

        audio = create_test_audio()
        low_result = low_freq.process(audio)
        high_result = high_freq.process(audio)

        assert low_result.data != high_result.data

    def test_effect_properties(self):
        """Test effect properties."""
        effect = FilterEffect()
        assert effect.effect_type == EffectType.FILTER
        assert effect.name == "Filter"


class TestTelephoneEffect:
    """Tests for TelephoneEffect."""

    def test_telephone_effect(self):
        """Test telephone effect."""
        effect = TelephoneEffect()
        audio = create_test_audio()
        result = effect.process(audio)

        assert len(result.data) == len(audio.data)

    def test_effect_properties(self):
        """Test effect properties."""
        effect = TelephoneEffect()
        assert effect.effect_type == EffectType.TELEPHONE
        assert effect.name == "Telephone"


class TestRadioEffect:
    """Tests for RadioEffect."""

    def test_radio_effect(self):
        """Test radio effect."""
        effect = RadioEffect()
        audio = create_test_audio()
        result = effect.process(audio)

        assert len(result.data) == len(audio.data)

    def test_effect_properties(self):
        """Test effect properties."""
        effect = RadioEffect()
        assert effect.effect_type == EffectType.RADIO
        assert effect.name == "Radio"


class TestEffectsChain:
    """Tests for EffectsChain."""

    def test_empty_chain(self):
        """Test empty chain passes through."""
        chain = EffectsChain()
        audio = create_test_audio()
        result = chain.process(audio)

        assert result.data == audio.data

    def test_single_effect(self):
        """Test chain with single effect."""
        chain = EffectsChain()
        chain.add_effect(DistortionEffect(DistortionParams(drive=0.5)))

        audio = create_test_audio()
        result = chain.process(audio)

        assert result.data != audio.data

    def test_multiple_effects(self):
        """Test chain with multiple effects."""
        chain = EffectsChain()
        chain.add_effect(DistortionEffect(DistortionParams(drive=0.3)))
        chain.add_effect(ReverbEffect(ReverbParams(room_size=0.5)))

        audio = create_test_audio()
        result = chain.process(audio)

        assert result.data != audio.data

    def test_effect_order_matters(self):
        """Test that effect order affects output."""
        chain1 = EffectsChain()
        chain1.add_effect(DistortionEffect(DistortionParams(drive=0.5)))
        chain1.add_effect(FilterEffect(FilterParams(frequency=500)))

        chain2 = EffectsChain()
        chain2.add_effect(FilterEffect(FilterParams(frequency=500)))
        chain2.add_effect(DistortionEffect(DistortionParams(drive=0.5)))

        audio = create_test_audio()
        result1 = chain1.process(audio)
        result2 = chain2.process(audio)

        # Different order should give different results
        assert result1.data != result2.data

    def test_remove_effect(self):
        """Test removing effects."""
        chain = EffectsChain()
        chain.add_effect(DistortionEffect())
        chain.add_effect(ReverbEffect())

        assert len(chain.get_effects()) == 2

        removed = chain.remove_effect(EffectType.DISTORTION)
        assert removed is True
        assert len(chain.get_effects()) == 1

    def test_remove_nonexistent(self):
        """Test removing nonexistent effect."""
        chain = EffectsChain()
        chain.add_effect(DistortionEffect())

        removed = chain.remove_effect(EffectType.REVERB)
        assert removed is False

    def test_clear_chain(self):
        """Test clearing all effects."""
        chain = EffectsChain()
        chain.add_effect(DistortionEffect())
        chain.add_effect(ReverbEffect())
        chain.clear()

        assert len(chain.get_effects()) == 0

    def test_disable_chain(self):
        """Test disabling entire chain."""
        chain = EffectsChain()
        chain.add_effect(DistortionEffect(DistortionParams(drive=0.8)))
        chain.set_enabled(False)

        audio = create_test_audio()
        result = chain.process(audio)

        # Should pass through unchanged
        assert result.data == audio.data

    def test_to_dict(self):
        """Test serialization."""
        chain = EffectsChain()
        chain.add_effect(DistortionEffect(DistortionParams(drive=0.5)))

        d = chain.to_dict()
        assert d['enabled'] is True
        assert len(d['effects']) == 1
        assert d['effects'][0]['type'] == EffectType.DISTORTION.value


class TestEffectPresets:
    """Tests for effect presets."""

    def test_preset_exists(self):
        """Test expected presets exist."""
        expected = ['telephone', 'radio', 'distant', 'megaphone', 'whisper', 'spooky']
        for preset in expected:
            assert preset in EFFECT_PRESETS

    def test_create_preset_chain(self):
        """Test creating chain from preset."""
        chain = create_preset_chain('telephone')
        assert chain is not None
        assert len(chain.get_effects()) > 0

    def test_create_invalid_preset(self):
        """Test creating chain from invalid preset."""
        chain = create_preset_chain('nonexistent_preset')
        assert chain is None

    def test_preset_processes_audio(self):
        """Test that presets process audio correctly."""
        for preset_name in EFFECT_PRESETS:
            chain = create_preset_chain(preset_name)
            assert chain is not None

            audio = create_test_audio()
            result = chain.process(audio)

            # Should produce valid output
            assert len(result.data) > 0
