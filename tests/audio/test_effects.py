"""
Tests for Audio Effects processing.
"""

import pytest
from src.shadowengine.audio.effects import (
    Effect, EffectType, EffectParameter,
    EffectsChain, EffectPreset,
    PitchShift, TimeStretch, Reverb, Distortion,
    EQ, Delay, Compression, Tremolo,
)


class TestEffectParameter:
    """Tests for EffectParameter."""

    def test_create_parameter(self):
        """Can create effect parameter."""
        param = EffectParameter(
            name="mix",
            value=0.5,
            min_value=0.0,
            max_value=1.0,
            unit="%",
        )
        assert param.name == "mix"
        assert param.value == 0.5
        assert param.unit == "%"

    def test_clamp_value(self):
        """Value is clamped to range."""
        param = EffectParameter("test", 2.0, 0.0, 1.0)
        assert param.value == 1.0

        param = EffectParameter("test", -1.0, 0.0, 1.0)
        assert param.value == 0.0

    def test_normalize(self):
        """Can normalize value."""
        param = EffectParameter("test", 50.0, 0.0, 100.0)
        assert param.normalize() == 0.5

    def test_serialization(self):
        """Parameter can be serialized."""
        param = EffectParameter("gain", 0.8, 0.0, 2.0, "dB", "Output gain")
        data = param.to_dict()

        assert data["name"] == "gain"
        assert data["value"] == 0.8
        assert data["description"] == "Output gain"


class TestPitchShift:
    """Tests for PitchShift effect."""

    def test_create(self, pitch_shift):
        """Can create pitch shift effect."""
        assert pitch_shift.effect_type == EffectType.PITCH_SHIFT
        assert pitch_shift.semitones == 2

    def test_pitch_ratio(self):
        """Pitch ratio is calculated correctly."""
        shift = PitchShift(semitones=12)
        assert abs(shift.pitch_ratio - 2.0) < 0.01  # Octave up

        shift = PitchShift(semitones=-12)
        assert abs(shift.pitch_ratio - 0.5) < 0.01  # Octave down

        shift = PitchShift(semitones=0)
        assert shift.pitch_ratio == 1.0

    def test_fine_tune(self):
        """Can use fine tune parameter."""
        shift = PitchShift(semitones=0)
        shift.set_parameter("fine_tune", 100)  # +100 cents = +1 semitone

        expected = 2 ** (1 / 12.0)
        assert abs(shift.pitch_ratio - expected) < 0.01

    def test_process_audio(self, pitch_shift):
        """Can process audio data."""
        audio = b"x" * 1000
        result = pitch_shift.process(audio, 22050)
        assert len(result) > 0

    def test_bypass(self, pitch_shift):
        """Bypassed effect returns original audio."""
        pitch_shift.enabled = False
        audio = b"original_audio"
        result = pitch_shift.process(audio, 22050)
        assert result == audio

    def test_no_change_returns_original(self):
        """Zero semitones returns original audio."""
        shift = PitchShift(semitones=0)
        audio = b"unchanged"
        result = shift.process(audio, 22050)
        assert result == audio


class TestTimeStretch:
    """Tests for TimeStretch effect."""

    def test_create(self):
        """Can create time stretch effect."""
        stretch = TimeStretch(ratio=1.5)
        assert stretch.ratio == 1.5

    def test_process_slower(self):
        """Slowing down increases length."""
        stretch = TimeStretch(ratio=2.0)
        audio = b"x" * 100
        result = stretch.process(audio, 22050)
        assert len(result) > len(audio)

    def test_process_faster(self):
        """Speeding up decreases length."""
        stretch = TimeStretch(ratio=0.5)
        audio = b"x" * 100
        result = stretch.process(audio, 22050)
        assert len(result) < len(audio)

    def test_no_change_returns_original(self):
        """Ratio 1.0 returns original."""
        stretch = TimeStretch(ratio=1.0)
        audio = b"unchanged"
        result = stretch.process(audio, 22050)
        assert result == audio


class TestReverb:
    """Tests for Reverb effect."""

    def test_create(self, reverb):
        """Can create reverb effect."""
        assert reverb.effect_type == EffectType.REVERB
        assert reverb.room_size == 0.5

    def test_decay_time(self):
        """Can get decay time."""
        reverb = Reverb(room_size=0.5, damping=0.5)
        reverb.set_parameter("decay", 3.0)
        assert reverb.decay_time == 3.0

    def test_process_adds_tail(self, reverb):
        """Reverb adds tail to audio."""
        audio = b"x" * 100
        result = reverb.process(audio, 22050)
        assert len(result) > len(audio)

    def test_parameters(self, reverb):
        """Has expected parameters."""
        params = reverb.get_parameters()
        assert "room_size" in params
        assert "damping" in params
        assert "wet" in params
        assert "dry" in params
        assert "decay" in params
        assert "pre_delay" in params


class TestDelay:
    """Tests for Delay effect."""

    def test_create(self):
        """Can create delay effect."""
        delay = Delay(delay_time=500.0, feedback=0.5)
        assert delay.delay_time_ms == 500.0
        assert delay.feedback == 0.5

    def test_feedback_limit(self):
        """Feedback is limited to prevent runaway."""
        delay = Delay(delay_time=300.0, feedback=0.99)
        delay.set_parameter("feedback", 0.99)
        assert delay.feedback <= 0.95

    def test_process_extends_audio(self):
        """Delay extends audio length."""
        delay = Delay(delay_time=500.0)
        audio = b"x" * 100
        result = delay.process(audio, 22050)
        assert len(result) > len(audio)


class TestDistortion:
    """Tests for Distortion effect."""

    def test_create(self, distortion):
        """Can create distortion effect."""
        assert distortion.effect_type == EffectType.DISTORTION
        assert distortion.drive == 0.5

    def test_no_drive_returns_original(self):
        """Zero drive returns original."""
        dist = Distortion(drive=0.0)
        audio = b"clean"
        result = dist.process(audio, 22050)
        assert result == audio

    def test_parameters(self, distortion):
        """Has expected parameters."""
        params = distortion.get_parameters()
        assert "drive" in params
        assert "tone" in params
        assert "type" in params


class TestEQ:
    """Tests for EQ effect."""

    def test_create(self):
        """Can create EQ effect."""
        eq = EQ()
        assert eq.effect_type == EffectType.EQ

    def test_bands(self):
        """EQ has frequency bands."""
        eq = EQ()
        params = eq.get_parameters()
        assert "low" in params
        assert "mid" in params
        assert "high" in params

    def test_band_range(self):
        """Bands have proper dB range."""
        eq = EQ()
        low_param = eq.get_parameter("low")
        assert low_param.min_value == -12.0
        assert low_param.max_value == 12.0


class TestCompression:
    """Tests for Compression effect."""

    def test_create(self):
        """Can create compression effect."""
        comp = Compression(threshold=-10.0, ratio=4.0)
        assert comp.threshold == -10.0
        assert comp.ratio == 4.0

    def test_parameters(self):
        """Has expected parameters."""
        comp = Compression()
        params = comp.get_parameters()
        assert "threshold" in params
        assert "ratio" in params
        assert "attack" in params
        assert "release" in params
        assert "makeup_gain" in params


class TestTremolo:
    """Tests for Tremolo effect."""

    def test_create(self):
        """Can create tremolo effect."""
        trem = Tremolo(rate=5.0, depth=0.5)
        assert trem.rate == 5.0
        assert trem.depth == 0.5

    def test_no_depth_returns_original(self):
        """Zero depth returns original."""
        trem = Tremolo(rate=5.0, depth=0.0)
        audio = b"static"
        result = trem.process(audio, 22050)
        assert result == audio


class TestEffectsChain:
    """Tests for EffectsChain."""

    def test_create_empty(self, effects_chain):
        """Can create empty chain."""
        assert len(effects_chain.get_effects()) == 0

    def test_add_effect(self, effects_chain, pitch_shift):
        """Can add effect to chain."""
        effects_chain.add_effect(pitch_shift)
        assert len(effects_chain.get_effects()) == 1

    def test_remove_effect(self, effects_chain, pitch_shift, reverb):
        """Can remove effect by index."""
        effects_chain.add_effect(pitch_shift)
        effects_chain.add_effect(reverb)

        removed = effects_chain.remove_effect(0)
        assert removed == pitch_shift
        assert len(effects_chain.get_effects()) == 1

    def test_get_effect(self, effects_chain, pitch_shift):
        """Can get effect by index."""
        effects_chain.add_effect(pitch_shift)
        assert effects_chain.get_effect(0) == pitch_shift
        assert effects_chain.get_effect(1) is None

    def test_clear(self, populated_effects_chain):
        """Can clear all effects."""
        populated_effects_chain.clear()
        assert len(populated_effects_chain.get_effects()) == 0

    def test_move_effect(self, effects_chain, pitch_shift, reverb, distortion):
        """Can move effect position."""
        effects_chain.add_effect(pitch_shift)
        effects_chain.add_effect(reverb)
        effects_chain.add_effect(distortion)

        effects_chain.move_effect(0, 2)

        effects = effects_chain.get_effects()
        assert effects[0] == reverb
        assert effects[2] == pitch_shift

    def test_process_chain(self, populated_effects_chain):
        """Chain processes audio through all effects."""
        audio = b"x" * 1000
        result = populated_effects_chain.process(audio, 22050)
        assert len(result) > 0

    def test_bypass(self, populated_effects_chain):
        """Bypassed chain returns original."""
        populated_effects_chain.bypass = True
        audio = b"original"
        result = populated_effects_chain.process(audio, 22050)
        assert result == audio

    def test_load_preset(self, effects_chain):
        """Can load preset configuration."""
        success = effects_chain.load_preset("telephone")
        assert success is True
        assert len(effects_chain.get_effects()) > 0

    def test_load_unknown_preset(self, effects_chain):
        """Unknown preset returns False."""
        success = effects_chain.load_preset("nonexistent_preset")
        assert success is False

    def test_preset_names(self, effects_chain):
        """Can get available preset names."""
        presets = effects_chain.get_preset_names()
        assert "telephone" in presets
        assert "radio" in presets
        assert "cave" in presets
        assert "underwater" in presets

    def test_serialization(self, populated_effects_chain):
        """Chain can be serialized."""
        data = populated_effects_chain.to_dict()
        restored = EffectsChain.from_dict(data)

        assert len(restored.get_effects()) == len(populated_effects_chain.get_effects())


class TestEffectsPresets:
    """Tests for built-in effects presets."""

    @pytest.mark.parametrize("preset", [
        "telephone", "radio", "cave", "underwater",
        "megaphone", "spooky", "robot", "concert_hall"
    ])
    def test_preset_loads(self, preset):
        """All presets load successfully."""
        chain = EffectsChain()
        assert chain.load_preset(preset) is True
        assert len(chain.get_effects()) > 0

    def test_telephone_preset(self):
        """Telephone preset has EQ and distortion."""
        chain = EffectsChain()
        chain.load_preset("telephone")

        effect_types = [e.effect_type for e in chain.get_effects()]
        assert EffectType.EQ in effect_types
        assert EffectType.DISTORTION in effect_types

    def test_cave_preset(self):
        """Cave preset has reverb."""
        chain = EffectsChain()
        chain.load_preset("cave")

        effect_types = [e.effect_type for e in chain.get_effects()]
        assert EffectType.REVERB in effect_types

    def test_spooky_preset(self):
        """Spooky preset has pitch shift, reverb, and tremolo."""
        chain = EffectsChain()
        chain.load_preset("spooky")

        effect_types = [e.effect_type for e in chain.get_effects()]
        assert EffectType.PITCH_SHIFT in effect_types
        assert EffectType.REVERB in effect_types
        assert EffectType.TREMOLO in effect_types
