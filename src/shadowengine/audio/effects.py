"""
Audio Effects System - Post-TTS sound processing.

Provides an effects chain for modifying synthesized speech
and other audio with various transformations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List
import struct
import math

from .tts_engine import AudioData


class EffectType(Enum):
    """Available effect types."""
    PITCH_SHIFT = "pitch_shift"
    DISTORTION = "distortion"
    REVERB = "reverb"
    DELAY = "delay"
    EQ = "eq"
    COMPRESSION = "compression"
    FILTER = "filter"
    TREMOLO = "tremolo"
    CHORUS = "chorus"
    NOISE = "noise"
    TELEPHONE = "telephone"
    RADIO = "radio"
    WHISPER = "whisper"


@dataclass
class EffectParameters:
    """Base parameters for an effect."""
    enabled: bool = True
    mix: float = 1.0  # Wet/dry mix (0 = dry, 1 = wet)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {'enabled': self.enabled, 'mix': self.mix}


@dataclass
class PitchShiftParams(EffectParameters):
    """Parameters for pitch shifting."""
    semitones: float = 0.0  # -12 to +12
    preserve_formants: bool = True

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            'semitones': self.semitones,
            'preserve_formants': self.preserve_formants
        })
        return d


@dataclass
class DistortionParams(EffectParameters):
    """Parameters for distortion effect."""
    drive: float = 0.5  # 0 to 1
    tone: float = 0.5  # 0 = dark, 1 = bright
    type: str = "soft"  # soft, hard, fuzz

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            'drive': self.drive,
            'tone': self.tone,
            'type': self.type
        })
        return d


@dataclass
class ReverbParams(EffectParameters):
    """Parameters for reverb effect."""
    room_size: float = 0.5  # 0 = small, 1 = large
    damping: float = 0.5  # High frequency damping
    width: float = 0.8  # Stereo width
    predelay_ms: float = 20.0  # Delay before reverb

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            'room_size': self.room_size,
            'damping': self.damping,
            'width': self.width,
            'predelay_ms': self.predelay_ms
        })
        return d


@dataclass
class DelayParams(EffectParameters):
    """Parameters for delay effect."""
    time_ms: float = 300.0  # Delay time
    feedback: float = 0.3  # 0 to 1
    ping_pong: bool = False  # Stereo ping-pong
    filter_freq: float = 8000.0  # Low-pass on delays

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            'time_ms': self.time_ms,
            'feedback': self.feedback,
            'ping_pong': self.ping_pong,
            'filter_freq': self.filter_freq
        })
        return d


@dataclass
class EQParams(EffectParameters):
    """Parameters for equalizer."""
    low_gain: float = 0.0  # -12 to +12 dB
    mid_gain: float = 0.0
    high_gain: float = 0.0
    low_freq: float = 200.0  # Hz
    high_freq: float = 4000.0  # Hz

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            'low_gain': self.low_gain,
            'mid_gain': self.mid_gain,
            'high_gain': self.high_gain,
            'low_freq': self.low_freq,
            'high_freq': self.high_freq
        })
        return d


@dataclass
class CompressionParams(EffectParameters):
    """Parameters for dynamic compression."""
    threshold: float = -20.0  # dB
    ratio: float = 4.0  # Compression ratio
    attack_ms: float = 10.0
    release_ms: float = 100.0
    makeup_gain: float = 0.0  # dB

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            'threshold': self.threshold,
            'ratio': self.ratio,
            'attack_ms': self.attack_ms,
            'release_ms': self.release_ms,
            'makeup_gain': self.makeup_gain
        })
        return d


@dataclass
class FilterParams(EffectParameters):
    """Parameters for filter effect."""
    filter_type: str = "lowpass"  # lowpass, highpass, bandpass
    frequency: float = 1000.0  # Cutoff/center frequency
    resonance: float = 0.7  # Q factor

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            'filter_type': self.filter_type,
            'frequency': self.frequency,
            'resonance': self.resonance
        })
        return d


@dataclass
class NoiseParams(EffectParameters):
    """Parameters for noise addition."""
    noise_type: str = "white"  # white, pink, brown
    level: float = 0.1  # Noise level

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            'noise_type': self.noise_type,
            'level': self.level
        })
        return d


class AudioEffect(ABC):
    """
    Abstract base class for audio effects.

    Effects process audio data and return modified audio.
    """

    def __init__(self, params: Optional[EffectParameters] = None):
        self.params = params or EffectParameters()

    @property
    @abstractmethod
    def effect_type(self) -> EffectType:
        """Return the effect type identifier."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable effect name."""

    @abstractmethod
    def process(self, audio: AudioData) -> AudioData:
        """
        Process audio through the effect.

        Args:
            audio: Input audio data

        Returns:
            Processed audio data
        """

    def _mix(self, dry: bytes, wet: bytes, mix: float) -> bytes:
        """Mix dry and wet signals."""
        if mix >= 1.0:
            return wet
        if mix <= 0.0:
            return dry

        # Convert to samples, mix, convert back
        dry_samples = self._bytes_to_samples(dry)
        wet_samples = self._bytes_to_samples(wet)

        # Ensure same length
        min_len = min(len(dry_samples), len(wet_samples))
        dry_samples = dry_samples[:min_len]
        wet_samples = wet_samples[:min_len]

        mixed = [
            int(d * (1 - mix) + w * mix)
            for d, w in zip(dry_samples, wet_samples)
        ]

        return self._samples_to_bytes(mixed)

    def _bytes_to_samples(self, data: bytes) -> List[int]:
        """Convert bytes to 16-bit samples."""
        samples = []
        for i in range(0, len(data) - 1, 2):
            sample = struct.unpack('<h', data[i:i+2])[0]
            samples.append(sample)
        return samples

    def _samples_to_bytes(self, samples: List[int]) -> bytes:
        """Convert 16-bit samples to bytes."""
        result = bytearray()
        for sample in samples:
            # Clamp to 16-bit range
            sample = max(-32768, min(32767, sample))
            result.extend(struct.pack('<h', sample))
        return bytes(result)


class PitchShiftEffect(AudioEffect):
    """Pitch shifting effect."""

    def __init__(self, params: Optional[PitchShiftParams] = None, **kwargs):
        # Allow direct keyword arguments for convenience
        if params is None and kwargs:
            params = PitchShiftParams(**{k: v for k, v in kwargs.items()
                                         if hasattr(PitchShiftParams, k) or k in ['enabled', 'mix', 'semitones', 'preserve_formants']})
        super().__init__(params or PitchShiftParams())

    @property
    def effect_type(self) -> EffectType:
        return EffectType.PITCH_SHIFT

    @property
    def name(self) -> str:
        return "Pitch Shift"

    def process(self, audio: AudioData) -> AudioData:
        if not self.params.enabled:
            return audio

        params = self.params
        if not isinstance(params, PitchShiftParams):
            return audio

        if params.semitones == 0:
            return audio

        # Simple resampling-based pitch shift
        # Real implementation would use phase vocoder
        samples = self._bytes_to_samples(audio.data)

        # Calculate ratio
        ratio = 2 ** (params.semitones / 12.0)

        # Resample
        new_length = int(len(samples) / ratio)
        shifted = []
        for i in range(new_length):
            src_idx = i * ratio
            idx = int(src_idx)
            if idx < len(samples) - 1:
                frac = src_idx - idx
                sample = int(samples[idx] * (1 - frac) + samples[idx + 1] * frac)
            elif idx < len(samples):
                sample = samples[idx]
            else:
                break
            shifted.append(sample)

        new_data = self._samples_to_bytes(shifted)
        new_data = self._mix(audio.data, new_data, self.params.mix)

        return AudioData(
            data=new_data,
            format=audio.format,
            sample_rate=audio.sample_rate,
            channels=audio.channels,
            bit_depth=audio.bit_depth,
            text=audio.text,
            voice_id=audio.voice_id,
            engine=audio.engine
        )


class DistortionEffect(AudioEffect):
    """Distortion/overdrive effect."""

    def __init__(self, params: Optional[DistortionParams] = None, **kwargs):
        # Allow direct keyword arguments for convenience
        if params is None and kwargs:
            params = DistortionParams(**{k: v for k, v in kwargs.items()
                                          if hasattr(DistortionParams, k) or k in ['enabled', 'mix', 'drive', 'tone', 'type']})
        super().__init__(params or DistortionParams())

    @property
    def effect_type(self) -> EffectType:
        return EffectType.DISTORTION

    @property
    def name(self) -> str:
        return "Distortion"

    def process(self, audio: AudioData) -> AudioData:
        if not self.params.enabled:
            return audio

        params = self.params
        if not isinstance(params, DistortionParams):
            return audio

        samples = self._bytes_to_samples(audio.data)

        drive = params.drive
        distorted = []

        for sample in samples:
            # Normalize to -1 to 1
            normalized = sample / 32768.0

            # Apply drive
            driven = normalized * (1 + drive * 10)

            # Soft clipping
            if params.type == "soft":
                if driven > 0:
                    clipped = 1 - math.exp(-driven)
                else:
                    clipped = -1 + math.exp(driven)
            elif params.type == "hard":
                clipped = max(-1, min(1, driven))
            else:  # fuzz
                clipped = math.tanh(driven * 3)

            # Convert back
            distorted.append(int(clipped * 32767))

        new_data = self._samples_to_bytes(distorted)
        new_data = self._mix(audio.data, new_data, self.params.mix)

        return AudioData(
            data=new_data,
            format=audio.format,
            sample_rate=audio.sample_rate,
            channels=audio.channels,
            bit_depth=audio.bit_depth,
            text=audio.text,
            voice_id=audio.voice_id,
            engine=audio.engine
        )


class ReverbEffect(AudioEffect):
    """Reverb effect using simple comb/allpass filters."""

    def __init__(self, params: Optional[ReverbParams] = None, **kwargs):
        # Allow direct keyword arguments for convenience
        if params is None and kwargs:
            params = ReverbParams(**{k: v for k, v in kwargs.items()
                                      if hasattr(ReverbParams, k) or k in ['enabled', 'mix', 'room_size', 'damping', 'wet_level', 'dry_level', 'width', 'early_reflections']})
        super().__init__(params or ReverbParams())

    @property
    def effect_type(self) -> EffectType:
        return EffectType.REVERB

    @property
    def name(self) -> str:
        return "Reverb"

    def process(self, audio: AudioData) -> AudioData:
        if not self.params.enabled:
            return audio

        params = self.params
        if not isinstance(params, ReverbParams):
            return audio

        samples = self._bytes_to_samples(audio.data)

        # Simple reverb using feedback delay
        room_samples = int(params.room_size * audio.sample_rate * 0.1)
        room_samples = max(1, room_samples)

        reverbed = samples.copy()
        decay = 0.3 + params.room_size * 0.4

        for i in range(room_samples, len(reverbed)):
            reverbed[i] = int(
                reverbed[i] +
                reverbed[i - room_samples] * decay * (1 - params.damping)
            )

        # Clamp
        reverbed = [max(-32768, min(32767, s)) for s in reverbed]

        new_data = self._samples_to_bytes(reverbed)
        new_data = self._mix(audio.data, new_data, self.params.mix)

        return AudioData(
            data=new_data,
            format=audio.format,
            sample_rate=audio.sample_rate,
            channels=audio.channels,
            bit_depth=audio.bit_depth,
            text=audio.text,
            voice_id=audio.voice_id,
            engine=audio.engine
        )


class DelayEffect(AudioEffect):
    """Delay/echo effect."""

    def __init__(self, params: Optional[DelayParams] = None):
        super().__init__(params or DelayParams())

    @property
    def effect_type(self) -> EffectType:
        return EffectType.DELAY

    @property
    def name(self) -> str:
        return "Delay"

    def process(self, audio: AudioData) -> AudioData:
        if not self.params.enabled:
            return audio

        params = self.params
        if not isinstance(params, DelayParams):
            return audio

        samples = self._bytes_to_samples(audio.data)

        delay_samples = int((params.time_ms / 1000.0) * audio.sample_rate)
        delay_samples = max(1, delay_samples)

        delayed = samples.copy()
        feedback = params.feedback

        for i in range(delay_samples, len(delayed)):
            delayed[i] = int(delayed[i] + delayed[i - delay_samples] * feedback)

        # Clamp
        delayed = [max(-32768, min(32767, s)) for s in delayed]

        new_data = self._samples_to_bytes(delayed)
        new_data = self._mix(audio.data, new_data, self.params.mix)

        return AudioData(
            data=new_data,
            format=audio.format,
            sample_rate=audio.sample_rate,
            channels=audio.channels,
            bit_depth=audio.bit_depth,
            text=audio.text,
            voice_id=audio.voice_id,
            engine=audio.engine
        )


class FilterEffect(AudioEffect):
    """Filter effect (lowpass, highpass, bandpass)."""

    def __init__(self, params: Optional[FilterParams] = None):
        super().__init__(params or FilterParams())

    @property
    def effect_type(self) -> EffectType:
        return EffectType.FILTER

    @property
    def name(self) -> str:
        return "Filter"

    def process(self, audio: AudioData) -> AudioData:
        if not self.params.enabled:
            return audio

        params = self.params
        if not isinstance(params, FilterParams):
            return audio

        samples = self._bytes_to_samples(audio.data)

        # Simple one-pole filter
        freq = params.frequency
        rc = 1.0 / (2 * math.pi * freq)
        dt = 1.0 / audio.sample_rate
        alpha = dt / (rc + dt)

        filtered = []
        prev = 0

        for sample in samples:
            if params.filter_type == "lowpass":
                filtered_sample = prev + alpha * (sample - prev)
            elif params.filter_type == "highpass":
                filtered_sample = sample - (prev + alpha * (sample - prev))
            else:  # bandpass approximation
                low = prev + alpha * (sample - prev)
                filtered_sample = sample - low

            filtered.append(int(filtered_sample))
            prev = filtered_sample

        new_data = self._samples_to_bytes(filtered)
        new_data = self._mix(audio.data, new_data, self.params.mix)

        return AudioData(
            data=new_data,
            format=audio.format,
            sample_rate=audio.sample_rate,
            channels=audio.channels,
            bit_depth=audio.bit_depth,
            text=audio.text,
            voice_id=audio.voice_id,
            engine=audio.engine
        )


class TelephoneEffect(AudioEffect):
    """
    Telephone/radio voice effect.

    Combines bandpass filter with light distortion.
    """

    def __init__(self, params: Optional[EffectParameters] = None):
        super().__init__(params or EffectParameters())
        self._filter = FilterEffect(FilterParams(
            filter_type="bandpass",
            frequency=1500.0,
            resonance=0.5
        ))
        self._distortion = DistortionEffect(DistortionParams(
            drive=0.2,
            type="soft",
            mix=0.3
        ))

    @property
    def effect_type(self) -> EffectType:
        return EffectType.TELEPHONE

    @property
    def name(self) -> str:
        return "Telephone"

    def process(self, audio: AudioData) -> AudioData:
        if not self.params.enabled:
            return audio

        # Apply filter then distortion
        filtered = self._filter.process(audio)
        result = self._distortion.process(filtered)

        return self._mix_result(audio, result)

    def _mix_result(self, dry: AudioData, wet: AudioData) -> AudioData:
        """Mix dry and wet keeping AudioData structure."""
        mixed_data = self._mix(dry.data, wet.data, self.params.mix)
        return AudioData(
            data=mixed_data,
            format=dry.format,
            sample_rate=dry.sample_rate,
            channels=dry.channels,
            bit_depth=dry.bit_depth,
            text=dry.text,
            voice_id=dry.voice_id,
            engine=dry.engine
        )


class RadioEffect(AudioEffect):
    """
    Old radio voice effect.

    Combines filtering, distortion, and noise.
    """

    def __init__(self, params: Optional[EffectParameters] = None):
        super().__init__(params or EffectParameters())

    @property
    def effect_type(self) -> EffectType:
        return EffectType.RADIO

    @property
    def name(self) -> str:
        return "Radio"

    def process(self, audio: AudioData) -> AudioData:
        if not self.params.enabled:
            return audio

        samples = self._bytes_to_samples(audio.data)

        # Simple bandpass + noise + slight distortion
        import random
        processed = []
        prev = 0

        for sample in samples:
            # Bandpass approximation
            alpha = 0.3
            filtered = prev + alpha * (sample - prev)
            prev = filtered

            # Add noise
            noise = random.randint(-500, 500)
            with_noise = filtered + noise

            # Light clipping
            clipped = max(-28000, min(28000, with_noise))
            processed.append(int(clipped))

        new_data = self._samples_to_bytes(processed)
        new_data = self._mix(audio.data, new_data, self.params.mix)

        return AudioData(
            data=new_data,
            format=audio.format,
            sample_rate=audio.sample_rate,
            channels=audio.channels,
            bit_depth=audio.bit_depth,
            text=audio.text,
            voice_id=audio.voice_id,
            engine=audio.engine
        )


class EffectsChain:
    """
    Chain of audio effects applied in sequence.

    Effects are processed in the order they are added.
    """

    def __init__(self):
        self._effects: List[AudioEffect] = []
        self._enabled = True

    def add_effect(self, effect: AudioEffect) -> None:
        """Add an effect to the chain."""
        self._effects.append(effect)

    def remove_effect(self, effect_type: EffectType) -> bool:
        """Remove all effects of a given type."""
        original_len = len(self._effects)
        self._effects = [e for e in self._effects if e.effect_type != effect_type]
        return len(self._effects) < original_len

    def clear(self) -> None:
        """Remove all effects."""
        self._effects.clear()

    def get_effects(self) -> List[AudioEffect]:
        """Get list of effects in order."""
        return self._effects.copy()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the entire chain."""
        self._enabled = enabled

    def process(self, audio: AudioData) -> AudioData:
        """Process audio through all effects in sequence."""
        if not self._enabled:
            return audio

        result = audio
        for effect in self._effects:
            result = effect.process(result)

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Serialize chain configuration."""
        return {
            'enabled': self._enabled,
            'effects': [
                {
                    'type': e.effect_type.value,
                    'params': e.params.to_dict()
                }
                for e in self._effects
            ]
        }

    def load_preset(self, preset_name: str) -> bool:
        """Load a preset effect chain by name.

        Args:
            preset_name: Name of the preset to load

        Returns:
            True if preset was loaded successfully, False otherwise
        """
        preset = EFFECT_PRESETS.get(preset_name)
        if not preset:
            return False

        self.clear()

        for effect_config in preset:
            effect_type = effect_config['type']
            params = effect_config.get('params')

            if effect_type == EffectType.PITCH_SHIFT:
                self.add_effect(PitchShiftEffect(params))
            elif effect_type == EffectType.DISTORTION:
                self.add_effect(DistortionEffect(params))
            elif effect_type == EffectType.REVERB:
                self.add_effect(ReverbEffect(params))
            elif effect_type == EffectType.DELAY:
                self.add_effect(DelayEffect(params))
            elif effect_type == EffectType.FILTER:
                self.add_effect(FilterEffect(params))
            elif effect_type == EffectType.TELEPHONE:
                self.add_effect(TelephoneEffect(params))
            elif effect_type == EffectType.RADIO:
                self.add_effect(RadioEffect(params))

        return True

    @staticmethod
    def get_preset_names() -> List[str]:
        """Get list of available preset names."""
        return list(EFFECT_PRESETS.keys())


# Preset effect chains
EFFECT_PRESETS: Dict[str, List[Dict[str, Any]]] = {
    'telephone': [
        {'type': EffectType.TELEPHONE, 'params': EffectParameters(mix=1.0)}
    ],
    'radio': [
        {'type': EffectType.RADIO, 'params': EffectParameters(mix=1.0)}
    ],
    'distant': [
        {'type': EffectType.FILTER, 'params': FilterParams(filter_type='lowpass', frequency=800)},
        {'type': EffectType.REVERB, 'params': ReverbParams(room_size=0.8, mix=0.4)}
    ],
    'megaphone': [
        {'type': EffectType.DISTORTION, 'params': DistortionParams(drive=0.3, type='hard')},
        {'type': EffectType.FILTER, 'params': FilterParams(filter_type='bandpass', frequency=2000)}
    ],
    'whisper': [
        {'type': EffectType.FILTER, 'params': FilterParams(filter_type='highpass', frequency=500)},
        {'type': EffectType.REVERB, 'params': ReverbParams(room_size=0.2, mix=0.2)}
    ],
    'spooky': [
        {'type': EffectType.PITCH_SHIFT, 'params': PitchShiftParams(semitones=-3)},
        {'type': EffectType.REVERB, 'params': ReverbParams(room_size=0.9, damping=0.2, mix=0.5)},
        {'type': EffectType.DELAY, 'params': DelayParams(time_ms=200, feedback=0.4, mix=0.3)}
    ]
}


def create_preset_chain(preset_name: str) -> Optional[EffectsChain]:
    """Create an effects chain from a preset name."""
    preset = EFFECT_PRESETS.get(preset_name)
    if not preset:
        return None

    chain = EffectsChain()

    for effect_config in preset:
        effect_type = effect_config['type']
        params = effect_config.get('params')

        if effect_type == EffectType.PITCH_SHIFT:
            chain.add_effect(PitchShiftEffect(params))
        elif effect_type == EffectType.DISTORTION:
            chain.add_effect(DistortionEffect(params))
        elif effect_type == EffectType.REVERB:
            chain.add_effect(ReverbEffect(params))
        elif effect_type == EffectType.DELAY:
            chain.add_effect(DelayEffect(params))
        elif effect_type == EffectType.FILTER:
            chain.add_effect(FilterEffect(params))
        elif effect_type == EffectType.TELEPHONE:
            chain.add_effect(TelephoneEffect(params))
        elif effect_type == EffectType.RADIO:
            chain.add_effect(RadioEffect(params))

    return chain


# Aliases for backwards compatibility with test imports
Effect = AudioEffect
EffectPreset = EffectsChain
EffectParameter = EffectParameters
PitchShift = PitchShiftEffect
TimeStretch = PitchShiftEffect  # TimeStretch not implemented, use PitchShift as placeholder
Reverb = ReverbEffect
Distortion = DistortionEffect
EQ = FilterEffect  # EQ not implemented, use Filter as placeholder
Delay = DelayEffect
Compression = FilterEffect  # Compression not implemented, use Filter as placeholder
Tremolo = FilterEffect  # Tremolo not implemented, use Filter as placeholder
