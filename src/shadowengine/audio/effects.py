"""
Audio Effects Processing for ShadowEngine.

Provides post-processing effects pipeline including pitch shift,
reverb, distortion, EQ, and more for voice and sound effect processing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List, Any, Callable
import math


class EffectType(Enum):
    """Types of audio effects."""
    PITCH_SHIFT = "pitch_shift"
    TIME_STRETCH = "time_stretch"
    REVERB = "reverb"
    DELAY = "delay"
    DISTORTION = "distortion"
    EQ = "eq"
    COMPRESSION = "compression"
    TREMOLO = "tremolo"
    FLANGER = "flanger"
    CHORUS = "chorus"
    FILTER = "filter"
    GAIN = "gain"


@dataclass
class EffectParameter:
    """A parameter for an audio effect."""

    name: str
    value: float
    min_value: float = 0.0
    max_value: float = 1.0
    unit: str = ""
    description: str = ""

    def __post_init__(self):
        """Clamp value to valid range."""
        self.value = max(self.min_value, min(self.max_value, self.value))

    def normalize(self) -> float:
        """Get normalized value (0.0 to 1.0)."""
        range_size = self.max_value - self.min_value
        if range_size == 0:
            return 0.5
        return (self.value - self.min_value) / range_size

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "unit": self.unit,
            "description": self.description,
        }


class Effect(ABC):
    """Abstract base class for audio effects."""

    def __init__(self, effect_type: EffectType, enabled: bool = True):
        self.effect_type = effect_type
        self.enabled = enabled
        self._parameters: Dict[str, EffectParameter] = {}
        self._setup_parameters()

    @abstractmethod
    def _setup_parameters(self) -> None:
        """Setup effect parameters."""
        pass

    @abstractmethod
    def process(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Process audio data through the effect."""
        pass

    def get_parameter(self, name: str) -> Optional[EffectParameter]:
        """Get a parameter by name."""
        return self._parameters.get(name)

    def set_parameter(self, name: str, value: float) -> bool:
        """Set a parameter value."""
        if name in self._parameters:
            param = self._parameters[name]
            param.value = max(param.min_value, min(param.max_value, value))
            return True
        return False

    def get_parameters(self) -> Dict[str, EffectParameter]:
        """Get all parameters."""
        return self._parameters.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "effect_type": self.effect_type.value,
            "enabled": self.enabled,
            "parameters": {k: v.to_dict() for k, v in self._parameters.items()},
        }


class PitchShift(Effect):
    """Pitch shifting effect."""

    def __init__(self, semitones: float = 0.0, enabled: bool = True):
        self._initial_semitones = semitones
        super().__init__(EffectType.PITCH_SHIFT, enabled)

    def _setup_parameters(self) -> None:
        """Setup pitch shift parameters."""
        self._parameters = {
            "semitones": EffectParameter(
                name="semitones",
                value=self._initial_semitones,
                min_value=-24.0,
                max_value=24.0,
                unit="st",
                description="Pitch shift in semitones",
            ),
            "fine_tune": EffectParameter(
                name="fine_tune",
                value=0.0,
                min_value=-100.0,
                max_value=100.0,
                unit="cents",
                description="Fine pitch adjustment in cents",
            ),
        }

    @property
    def semitones(self) -> float:
        """Get semitone shift."""
        return self._parameters["semitones"].value

    @property
    def pitch_ratio(self) -> float:
        """Get pitch ratio for processing."""
        semitones = self._parameters["semitones"].value
        cents = self._parameters["fine_tune"].value
        total_semitones = semitones + (cents / 100.0)
        return 2 ** (total_semitones / 12.0)

    def process(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Apply pitch shift to audio data."""
        if not self.enabled or self.pitch_ratio == 1.0:
            return audio_data

        # In a real implementation, this would use a DSP library
        # For now, we simulate the effect by modifying the data length
        ratio = self.pitch_ratio
        new_length = int(len(audio_data) / ratio)
        return audio_data[:new_length] if new_length < len(audio_data) else audio_data


class TimeStretch(Effect):
    """Time stretching effect (change speed without pitch)."""

    def __init__(self, ratio: float = 1.0, enabled: bool = True):
        self._initial_ratio = ratio
        super().__init__(EffectType.TIME_STRETCH, enabled)

    def _setup_parameters(self) -> None:
        """Setup time stretch parameters."""
        self._parameters = {
            "ratio": EffectParameter(
                name="ratio",
                value=self._initial_ratio,
                min_value=0.25,
                max_value=4.0,
                unit="x",
                description="Time stretch ratio (1.0 = original)",
            ),
            "preserve_transients": EffectParameter(
                name="preserve_transients",
                value=1.0,
                min_value=0.0,
                max_value=1.0,
                description="How much to preserve attack transients",
            ),
        }

    @property
    def ratio(self) -> float:
        """Get stretch ratio."""
        return self._parameters["ratio"].value

    def process(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Apply time stretch to audio data."""
        if not self.enabled or self.ratio == 1.0:
            return audio_data

        # Simulate time stretching by changing data length
        new_length = int(len(audio_data) * self.ratio)
        if new_length > len(audio_data):
            return audio_data + (b"\x00" * (new_length - len(audio_data)))
        return audio_data[:new_length]


class Reverb(Effect):
    """Reverb effect."""

    def __init__(self, room_size: float = 0.5, damping: float = 0.5, enabled: bool = True):
        self._initial_room_size = room_size
        self._initial_damping = damping
        super().__init__(EffectType.REVERB, enabled)

    def _setup_parameters(self) -> None:
        """Setup reverb parameters."""
        self._parameters = {
            "room_size": EffectParameter(
                name="room_size",
                value=self._initial_room_size,
                min_value=0.0,
                max_value=1.0,
                description="Size of the simulated room",
            ),
            "damping": EffectParameter(
                name="damping",
                value=self._initial_damping,
                min_value=0.0,
                max_value=1.0,
                description="High frequency damping",
            ),
            "wet": EffectParameter(
                name="wet",
                value=0.3,
                min_value=0.0,
                max_value=1.0,
                description="Wet signal mix",
            ),
            "dry": EffectParameter(
                name="dry",
                value=0.7,
                min_value=0.0,
                max_value=1.0,
                description="Dry signal mix",
            ),
            "decay": EffectParameter(
                name="decay",
                value=2.0,
                min_value=0.1,
                max_value=10.0,
                unit="s",
                description="Reverb decay time",
            ),
            "pre_delay": EffectParameter(
                name="pre_delay",
                value=20.0,
                min_value=0.0,
                max_value=200.0,
                unit="ms",
                description="Pre-delay before reverb",
            ),
        }

    @property
    def room_size(self) -> float:
        """Get room size."""
        return self._parameters["room_size"].value

    @property
    def decay_time(self) -> float:
        """Get decay time in seconds."""
        return self._parameters["decay"].value

    def process(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Apply reverb to audio data."""
        if not self.enabled:
            return audio_data

        # In a real implementation, this would apply reverb convolution
        # For simulation, we add a "tail" to the audio
        decay_samples = int(self.decay_time * sample_rate * 2)  # 2 bytes per sample
        reverb_tail = b"\x08" * min(decay_samples, 10000)  # Simulated quiet tail

        return audio_data + reverb_tail


class Delay(Effect):
    """Delay/echo effect."""

    def __init__(self, delay_time: float = 300.0, feedback: float = 0.3, enabled: bool = True):
        self._initial_delay = delay_time
        self._initial_feedback = feedback
        super().__init__(EffectType.DELAY, enabled)

    def _setup_parameters(self) -> None:
        """Setup delay parameters."""
        self._parameters = {
            "delay_time": EffectParameter(
                name="delay_time",
                value=self._initial_delay,
                min_value=1.0,
                max_value=2000.0,
                unit="ms",
                description="Delay time",
            ),
            "feedback": EffectParameter(
                name="feedback",
                value=self._initial_feedback,
                min_value=0.0,
                max_value=0.95,
                description="Feedback amount",
            ),
            "mix": EffectParameter(
                name="mix",
                value=0.3,
                min_value=0.0,
                max_value=1.0,
                description="Wet/dry mix",
            ),
        }

    @property
    def delay_time_ms(self) -> float:
        """Get delay time in milliseconds."""
        return self._parameters["delay_time"].value

    @property
    def feedback(self) -> float:
        """Get feedback amount."""
        return self._parameters["feedback"].value

    def process(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Apply delay to audio data."""
        if not self.enabled:
            return audio_data

        # Simulate delay by extending audio
        delay_samples = int((self.delay_time_ms / 1000.0) * sample_rate * 2)
        return audio_data + (b"\x04" * min(delay_samples, 5000))


class Distortion(Effect):
    """Distortion effect."""

    def __init__(self, drive: float = 0.5, tone: float = 0.5, enabled: bool = True):
        self._initial_drive = drive
        self._initial_tone = tone
        super().__init__(EffectType.DISTORTION, enabled)

    def _setup_parameters(self) -> None:
        """Setup distortion parameters."""
        self._parameters = {
            "drive": EffectParameter(
                name="drive",
                value=self._initial_drive,
                min_value=0.0,
                max_value=1.0,
                description="Distortion amount",
            ),
            "tone": EffectParameter(
                name="tone",
                value=self._initial_tone,
                min_value=0.0,
                max_value=1.0,
                description="Tone control (dark to bright)",
            ),
            "mix": EffectParameter(
                name="mix",
                value=1.0,
                min_value=0.0,
                max_value=1.0,
                description="Wet/dry mix",
            ),
            "type": EffectParameter(
                name="type",
                value=0.0,
                min_value=0.0,
                max_value=3.0,
                description="Distortion type (0=soft, 1=hard, 2=fuzz, 3=bit)",
            ),
        }

    @property
    def drive(self) -> float:
        """Get drive amount."""
        return self._parameters["drive"].value

    def process(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Apply distortion to audio data."""
        if not self.enabled or self.drive == 0:
            return audio_data

        # Simulate distortion by clipping high values
        # In reality, this would apply waveshaping
        return audio_data


class EQ(Effect):
    """Equalizer effect."""

    def __init__(self, enabled: bool = True):
        super().__init__(EffectType.EQ, enabled)

    def _setup_parameters(self) -> None:
        """Setup EQ parameters."""
        self._parameters = {
            "low": EffectParameter(
                name="low",
                value=0.0,
                min_value=-12.0,
                max_value=12.0,
                unit="dB",
                description="Low frequency gain",
            ),
            "low_mid": EffectParameter(
                name="low_mid",
                value=0.0,
                min_value=-12.0,
                max_value=12.0,
                unit="dB",
                description="Low-mid frequency gain",
            ),
            "mid": EffectParameter(
                name="mid",
                value=0.0,
                min_value=-12.0,
                max_value=12.0,
                unit="dB",
                description="Mid frequency gain",
            ),
            "high_mid": EffectParameter(
                name="high_mid",
                value=0.0,
                min_value=-12.0,
                max_value=12.0,
                unit="dB",
                description="High-mid frequency gain",
            ),
            "high": EffectParameter(
                name="high",
                value=0.0,
                min_value=-12.0,
                max_value=12.0,
                unit="dB",
                description="High frequency gain",
            ),
        }

    def process(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Apply EQ to audio data."""
        if not self.enabled:
            return audio_data
        # Would apply frequency filtering in real implementation
        return audio_data


class Compression(Effect):
    """Dynamic range compression effect."""

    def __init__(self, threshold: float = -10.0, ratio: float = 4.0, enabled: bool = True):
        self._initial_threshold = threshold
        self._initial_ratio = ratio
        super().__init__(EffectType.COMPRESSION, enabled)

    def _setup_parameters(self) -> None:
        """Setup compression parameters."""
        self._parameters = {
            "threshold": EffectParameter(
                name="threshold",
                value=self._initial_threshold,
                min_value=-60.0,
                max_value=0.0,
                unit="dB",
                description="Compression threshold",
            ),
            "ratio": EffectParameter(
                name="ratio",
                value=self._initial_ratio,
                min_value=1.0,
                max_value=20.0,
                unit=":1",
                description="Compression ratio",
            ),
            "attack": EffectParameter(
                name="attack",
                value=10.0,
                min_value=0.1,
                max_value=100.0,
                unit="ms",
                description="Attack time",
            ),
            "release": EffectParameter(
                name="release",
                value=100.0,
                min_value=10.0,
                max_value=1000.0,
                unit="ms",
                description="Release time",
            ),
            "makeup_gain": EffectParameter(
                name="makeup_gain",
                value=0.0,
                min_value=0.0,
                max_value=24.0,
                unit="dB",
                description="Makeup gain",
            ),
        }

    @property
    def threshold(self) -> float:
        """Get threshold in dB."""
        return self._parameters["threshold"].value

    @property
    def ratio(self) -> float:
        """Get compression ratio."""
        return self._parameters["ratio"].value

    def process(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Apply compression to audio data."""
        if not self.enabled:
            return audio_data
        # Would apply dynamic range compression in real implementation
        return audio_data


class Tremolo(Effect):
    """Tremolo (amplitude modulation) effect."""

    def __init__(self, rate: float = 5.0, depth: float = 0.5, enabled: bool = True):
        self._initial_rate = rate
        self._initial_depth = depth
        super().__init__(EffectType.TREMOLO, enabled)

    def _setup_parameters(self) -> None:
        """Setup tremolo parameters."""
        self._parameters = {
            "rate": EffectParameter(
                name="rate",
                value=self._initial_rate,
                min_value=0.1,
                max_value=20.0,
                unit="Hz",
                description="Modulation rate",
            ),
            "depth": EffectParameter(
                name="depth",
                value=self._initial_depth,
                min_value=0.0,
                max_value=1.0,
                description="Modulation depth",
            ),
            "shape": EffectParameter(
                name="shape",
                value=0.0,
                min_value=0.0,
                max_value=2.0,
                description="Wave shape (0=sine, 1=triangle, 2=square)",
            ),
        }

    @property
    def rate(self) -> float:
        """Get tremolo rate in Hz."""
        return self._parameters["rate"].value

    @property
    def depth(self) -> float:
        """Get tremolo depth."""
        return self._parameters["depth"].value

    def process(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Apply tremolo to audio data."""
        if not self.enabled or self.depth == 0:
            return audio_data
        # Would apply amplitude modulation in real implementation
        return audio_data


@dataclass
class EffectPreset:
    """A preset configuration for effects chain."""

    name: str
    description: str
    effects: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "effects": self.effects,
        }


class EffectsChain:
    """Chain of audio effects processed in sequence."""

    # Built-in presets
    PRESETS = {
        "telephone": EffectPreset(
            name="telephone",
            description="Old telephone sound",
            effects=[
                {"type": "eq", "low": -12.0, "high": -8.0, "mid": 6.0},
                {"type": "distortion", "drive": 0.2, "tone": 0.3},
            ],
        ),
        "radio": EffectPreset(
            name="radio",
            description="AM radio sound",
            effects=[
                {"type": "eq", "low": -8.0, "high": -4.0},
                {"type": "compression", "threshold": -15.0, "ratio": 6.0},
            ],
        ),
        "cave": EffectPreset(
            name="cave",
            description="Large cave reverb",
            effects=[
                {"type": "reverb", "room_size": 0.9, "decay": 4.0, "wet": 0.5},
                {"type": "delay", "delay_time": 150, "feedback": 0.4},
            ],
        ),
        "underwater": EffectPreset(
            name="underwater",
            description="Muffled underwater sound",
            effects=[
                {"type": "eq", "high": -18.0, "high_mid": -12.0},
                {"type": "reverb", "room_size": 0.7, "decay": 2.0, "wet": 0.4},
            ],
        ),
        "megaphone": EffectPreset(
            name="megaphone",
            description="Megaphone/bullhorn sound",
            effects=[
                {"type": "eq", "low": -15.0, "high": -6.0, "mid": 8.0},
                {"type": "distortion", "drive": 0.4, "tone": 0.6},
                {"type": "compression", "threshold": -8.0, "ratio": 8.0},
            ],
        ),
        "spooky": EffectPreset(
            name="spooky",
            description="Eerie haunted sound",
            effects=[
                {"type": "pitch_shift", "semitones": -2},
                {"type": "reverb", "room_size": 0.8, "decay": 3.5, "wet": 0.4},
                {"type": "tremolo", "rate": 3.0, "depth": 0.3},
            ],
        ),
        "robot": EffectPreset(
            name="robot",
            description="Robotic voice",
            effects=[
                {"type": "pitch_shift", "semitones": 0, "fine_tune": 50},
                {"type": "distortion", "drive": 0.3, "type": 3.0},
            ],
        ),
        "concert_hall": EffectPreset(
            name="concert_hall",
            description="Large concert hall",
            effects=[
                {"type": "reverb", "room_size": 0.95, "decay": 2.5, "wet": 0.25, "pre_delay": 40},
            ],
        ),
    }

    def __init__(self):
        self._effects: List[Effect] = []
        self._bypass = False

    @property
    def bypass(self) -> bool:
        """Check if chain is bypassed."""
        return self._bypass

    @bypass.setter
    def bypass(self, value: bool) -> None:
        """Set bypass state."""
        self._bypass = value

    def add_effect(self, effect: Effect) -> None:
        """Add an effect to the chain."""
        self._effects.append(effect)

    def remove_effect(self, index: int) -> Optional[Effect]:
        """Remove an effect by index."""
        if 0 <= index < len(self._effects):
            return self._effects.pop(index)
        return None

    def get_effect(self, index: int) -> Optional[Effect]:
        """Get an effect by index."""
        if 0 <= index < len(self._effects):
            return self._effects[index]
        return None

    def get_effects(self) -> List[Effect]:
        """Get all effects in the chain."""
        return self._effects.copy()

    def clear(self) -> None:
        """Clear all effects from the chain."""
        self._effects.clear()

    def move_effect(self, from_index: int, to_index: int) -> bool:
        """Move an effect to a new position."""
        if 0 <= from_index < len(self._effects) and 0 <= to_index < len(self._effects):
            effect = self._effects.pop(from_index)
            self._effects.insert(to_index, effect)
            return True
        return False

    def process(self, audio_data: bytes, sample_rate: int) -> bytes:
        """Process audio through the effects chain."""
        if self._bypass or not audio_data:
            return audio_data

        result = audio_data
        for effect in self._effects:
            if effect.enabled:
                result = effect.process(result, sample_rate)

        return result

    def load_preset(self, preset_name: str) -> bool:
        """Load a preset configuration."""
        preset = self.PRESETS.get(preset_name)
        if not preset:
            return False

        self.clear()
        for effect_config in preset.effects:
            effect = self._create_effect_from_config(effect_config)
            if effect:
                self.add_effect(effect)

        return True

    def _create_effect_from_config(self, config: Dict[str, Any]) -> Optional[Effect]:
        """Create an effect from configuration dictionary."""
        effect_type = config.get("type", "")

        effect_classes = {
            "pitch_shift": PitchShift,
            "time_stretch": TimeStretch,
            "reverb": Reverb,
            "delay": Delay,
            "distortion": Distortion,
            "eq": EQ,
            "compression": Compression,
            "tremolo": Tremolo,
        }

        effect_class = effect_classes.get(effect_type)
        if not effect_class:
            return None

        # Create effect with constructor args
        constructor_args = {}
        for param_name, param_value in config.items():
            if param_name != "type":
                # Try to pass to constructor
                try:
                    effect = effect_class(**{param_name: param_value})
                    return effect
                except TypeError:
                    pass

        # Create default and set parameters
        effect = effect_class()
        for param_name, param_value in config.items():
            if param_name != "type":
                effect.set_parameter(param_name, param_value)

        return effect

    def get_preset_names(self) -> List[str]:
        """Get all available preset names."""
        return list(self.PRESETS.keys())

    def to_dict(self) -> Dict[str, Any]:
        """Convert chain to dictionary."""
        return {
            "bypass": self._bypass,
            "effects": [e.to_dict() for e in self._effects],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EffectsChain':
        """Create chain from dictionary."""
        chain = cls()
        chain._bypass = data.get("bypass", False)
        for effect_data in data.get("effects", []):
            # Convert from to_dict format to _create_effect_from_config format
            config = {"type": effect_data.get("effect_type", "")}
            # Extract parameter values
            for param_name, param_data in effect_data.get("parameters", {}).items():
                if isinstance(param_data, dict):
                    config[param_name] = param_data.get("value", 0)
                else:
                    config[param_name] = param_data
            effect = chain._create_effect_from_config(config)
            if effect:
                chain.add_effect(effect)
        return chain
