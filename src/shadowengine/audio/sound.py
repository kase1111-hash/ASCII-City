"""
Sound Effect System - Sound generation and playback.

Provides sound effect generation, mixing, and spatial audio
for creating immersive audio environments.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
import random
import math
import struct

from .tts_engine import AudioData, AudioFormat


class SoundCategory(Enum):
    """Categories of sound effects."""
    AMBIENCE = "ambience"
    FOOTSTEPS = "footsteps"
    IMPACTS = "impacts"
    WEATHER = "weather"
    VOICE = "voice"
    MECHANICAL = "mechanical"
    NATURE = "nature"
    MUSIC = "music"
    UI = "ui"
    HORROR = "horror"


class SoundTrigger(Enum):
    """How a sound is triggered."""
    ONESHOT = "oneshot"  # Play once
    LOOP = "loop"  # Loop continuously
    RANDOM = "random"  # Random interval
    EVENT = "event"  # Triggered by game event


@dataclass
class SoundProperties:
    """Properties of a sound effect."""
    # Playback
    volume: float = 1.0  # 0.0 to 1.0
    pitch: float = 1.0  # 0.5 to 2.0
    pan: float = 0.0  # -1.0 (left) to 1.0 (right)

    # Variation
    volume_variation: float = 0.0  # Random volume variation
    pitch_variation: float = 0.0  # Random pitch variation

    # Spatial
    is_3d: bool = False
    max_distance: float = 100.0  # Distance at which sound is silent
    rolloff_factor: float = 1.0  # How quickly volume drops with distance

    # Timing
    delay_ms: float = 0.0  # Delay before playing
    fade_in_ms: float = 0.0
    fade_out_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'volume': self.volume,
            'pitch': self.pitch,
            'pan': self.pan,
            'volume_variation': self.volume_variation,
            'pitch_variation': self.pitch_variation,
            'is_3d': self.is_3d,
            'max_distance': self.max_distance,
            'rolloff_factor': self.rolloff_factor,
            'delay_ms': self.delay_ms,
            'fade_in_ms': self.fade_in_ms,
            'fade_out_ms': self.fade_out_ms
        }

    def apply_variation(self, seed: Optional[int] = None) -> 'SoundProperties':
        """Create a new instance with random variations applied."""
        if seed is not None:
            random.seed(seed)

        return SoundProperties(
            volume=self.volume + random.uniform(-self.volume_variation, self.volume_variation),
            pitch=self.pitch + random.uniform(-self.pitch_variation, self.pitch_variation),
            pan=self.pan,
            volume_variation=self.volume_variation,
            pitch_variation=self.pitch_variation,
            is_3d=self.is_3d,
            max_distance=self.max_distance,
            rolloff_factor=self.rolloff_factor,
            delay_ms=self.delay_ms,
            fade_in_ms=self.fade_in_ms,
            fade_out_ms=self.fade_out_ms
        )


@dataclass
class SoundEffect:
    """
    A single sound effect definition.

    Can be procedurally generated or loaded from data.
    """
    id: str
    name: str
    category: SoundCategory
    trigger: SoundTrigger = SoundTrigger.ONESHOT
    properties: SoundProperties = field(default_factory=SoundProperties)

    # Audio data (may be None if procedurally generated)
    _audio_data: Optional[AudioData] = None

    # Tags for filtering
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value,
            'trigger': self.trigger.value,
            'properties': self.properties.to_dict(),
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SoundEffect':
        """Deserialize from dictionary."""
        props_data = data.get('properties', {})
        return cls(
            id=data['id'],
            name=data['name'],
            category=SoundCategory(data.get('category', 'ambience')),
            trigger=SoundTrigger(data.get('trigger', 'oneshot')),
            properties=SoundProperties(**props_data),
            tags=data.get('tags', [])
        )


class SoundGenerator:
    """
    Procedural sound generator.

    Creates various types of sounds algorithmically.
    """

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def generate(
        self,
        sound_type: str,
        duration_ms: int = 500,
        seed: Optional[int] = None
    ) -> AudioData:
        """
        Generate a procedural sound.

        Args:
            sound_type: Type of sound to generate
            duration_ms: Duration in milliseconds
            seed: Random seed for reproducibility

        Returns:
            Generated audio data
        """
        if seed is not None:
            random.seed(seed)

        generators = {
            'tone': self._generate_tone,
            'noise': self._generate_noise,
            'click': self._generate_click,
            'footstep': self._generate_footstep,
            'rain': self._generate_rain,
            'thunder': self._generate_thunder,
            'wind': self._generate_wind,
            'door': self._generate_door,
            'gunshot': self._generate_gunshot,
            'heartbeat': self._generate_heartbeat,
            'static': self._generate_static,
            'drip': self._generate_drip,
            'creak': self._generate_creak,
            'whisper': self._generate_whisper_sound,
        }

        generator = generators.get(sound_type, self._generate_noise)
        samples = generator(duration_ms)

        return self._samples_to_audio(samples)

    def _generate_tone(self, duration_ms: int, frequency: float = 440.0) -> List[int]:
        """Generate a pure sine tone."""
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)
        samples = []

        for i in range(num_samples):
            t = i / self.sample_rate
            sample = math.sin(2 * math.pi * frequency * t)
            samples.append(int(sample * 16000))

        return self._apply_envelope(samples, 10, 50)

    def _generate_noise(self, duration_ms: int) -> List[int]:
        """Generate white noise."""
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)
        return [random.randint(-16000, 16000) for _ in range(num_samples)]

    def _generate_click(self, duration_ms: int) -> List[int]:
        """Generate a short click sound."""
        duration_ms = min(duration_ms, 50)
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)

        samples = []
        for i in range(num_samples):
            # Exponential decay
            decay = math.exp(-i / (num_samples * 0.1))
            noise = random.randint(-16000, 16000)
            samples.append(int(noise * decay))

        return samples

    def _generate_footstep(self, duration_ms: int) -> List[int]:
        """Generate a footstep sound."""
        duration_ms = min(duration_ms, 200)
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)

        samples = []
        # Low thump + high scuff
        for i in range(num_samples):
            t = i / self.sample_rate
            decay = math.exp(-i / (num_samples * 0.15))

            # Low frequency thump
            low = math.sin(2 * math.pi * 80 * t) * decay

            # High frequency noise (scuff)
            high = random.uniform(-1, 1) * decay * 0.3

            sample = (low + high) * 20000
            samples.append(int(sample))

        return samples

    def _generate_rain(self, duration_ms: int) -> List[int]:
        """Generate rain ambience."""
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)

        samples = []
        # Brown noise for rain base
        prev = 0
        for i in range(num_samples):
            noise = random.uniform(-1, 1)
            prev = (prev + (0.02 * noise)) / 1.02
            sample = prev * 8000

            # Occasional louder drops
            if random.random() < 0.001:
                sample += random.uniform(-1, 1) * 12000

            samples.append(int(sample))

        return samples

    def _generate_thunder(self, duration_ms: int) -> List[int]:
        """Generate thunder rumble."""
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)

        samples = []
        for i in range(num_samples):
            t = i / num_samples

            # Initial crack
            if t < 0.05:
                crack = random.uniform(-1, 1) * (1 - t * 20)
            else:
                crack = 0

            # Low rumble
            decay = math.exp(-t * 3)
            freq = 30 + random.uniform(-5, 5)
            rumble = math.sin(2 * math.pi * freq * (i / self.sample_rate)) * decay

            # Random variations
            noise = random.uniform(-0.2, 0.2) * decay

            sample = (crack * 0.5 + rumble * 0.8 + noise) * 24000
            samples.append(int(sample))

        return samples

    def _generate_wind(self, duration_ms: int) -> List[int]:
        """Generate wind ambience."""
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)

        samples = []
        # Filtered noise with slow modulation
        prev = 0
        mod_phase = random.uniform(0, 2 * math.pi)

        for i in range(num_samples):
            t = i / self.sample_rate

            # Slow modulation
            mod = (math.sin(mod_phase + t * 0.5) + 1) / 2 * 0.5 + 0.5

            # Filtered noise
            noise = random.uniform(-1, 1)
            prev = prev * 0.95 + noise * 0.05
            sample = prev * mod * 10000

            samples.append(int(sample))

        return samples

    def _generate_door(self, duration_ms: int) -> List[int]:
        """Generate door creak/close sound."""
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)

        samples = []
        for i in range(num_samples):
            t = i / num_samples

            # Frequency sweep (creak)
            freq = 200 + t * 300 + random.uniform(-50, 50)
            tone = math.sin(2 * math.pi * freq * (i / self.sample_rate))

            # Envelope
            env = math.sin(math.pi * t)

            sample = tone * env * 12000
            samples.append(int(sample))

        return samples

    def _generate_gunshot(self, duration_ms: int) -> List[int]:
        """Generate gunshot sound."""
        duration_ms = min(duration_ms, 500)
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)

        samples = []
        for i in range(num_samples):
            t = i / num_samples

            # Initial crack (first 5%)
            if t < 0.05:
                crack = random.uniform(-1, 1)
                crack_env = 1 - (t / 0.05)
            else:
                crack = 0
                crack_env = 0

            # Decay tail
            decay = math.exp(-t * 8)
            noise = random.uniform(-1, 1) * decay * 0.3

            # Low boom
            boom = math.sin(2 * math.pi * 60 * (i / self.sample_rate)) * decay * 0.5

            sample = (crack * crack_env + noise + boom) * 28000
            samples.append(int(max(-32767, min(32767, sample))))

        return samples

    def _generate_heartbeat(self, duration_ms: int) -> List[int]:
        """Generate heartbeat sound."""
        # Two beats per cycle
        beat_ms = duration_ms // 2
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)
        beat_samples = int((beat_ms / 1000.0) * self.sample_rate)

        samples = []
        for beat in range(2):
            for i in range(beat_samples):
                t = i / beat_samples

                # Double bump envelope
                if t < 0.15:
                    env = t / 0.15
                elif t < 0.3:
                    env = 1 - (t - 0.15) / 0.15
                elif t < 0.4:
                    env = (t - 0.3) / 0.1 * 0.7
                elif t < 0.55:
                    env = 0.7 * (1 - (t - 0.4) / 0.15)
                else:
                    env = 0

                freq = 40 + beat * 10
                tone = math.sin(2 * math.pi * freq * (i / self.sample_rate))
                sample = tone * env * 18000

                samples.append(int(sample))

        # Pad to full duration
        while len(samples) < num_samples:
            samples.append(0)

        return samples[:num_samples]

    def _generate_static(self, duration_ms: int) -> List[int]:
        """Generate static/interference sound."""
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)

        samples = []
        for i in range(num_samples):
            # Pink-ish noise with occasional crackles
            noise = random.uniform(-1, 1)

            if random.random() < 0.01:
                # Crackle
                noise *= 3

            samples.append(int(noise * 8000))

        return samples

    def _generate_drip(self, duration_ms: int) -> List[int]:
        """Generate water drip sound."""
        duration_ms = min(duration_ms, 300)
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)

        samples = []
        base_freq = 800 + random.uniform(-200, 200)

        for i in range(num_samples):
            t = i / num_samples

            # Quick attack, exponential decay
            if t < 0.02:
                env = t / 0.02
            else:
                env = math.exp(-(t - 0.02) * 10)

            # Frequency drops as drop "settles"
            freq = base_freq * (1 - t * 0.3)
            tone = math.sin(2 * math.pi * freq * (i / self.sample_rate))

            sample = tone * env * 12000
            samples.append(int(sample))

        return samples

    def _generate_creak(self, duration_ms: int) -> List[int]:
        """Generate creaking sound."""
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)

        samples = []
        base_freq = 150 + random.uniform(-50, 50)

        for i in range(num_samples):
            t = i / num_samples

            # Irregular frequency modulation
            freq_mod = math.sin(t * 20 + random.uniform(-0.5, 0.5))
            freq = base_freq + freq_mod * 100

            tone = math.sin(2 * math.pi * freq * (i / self.sample_rate))

            # Add harmonics
            harm = math.sin(4 * math.pi * freq * (i / self.sample_rate)) * 0.3

            # Envelope
            env = math.sin(math.pi * t)

            sample = (tone + harm) * env * 10000
            samples.append(int(sample))

        return samples

    def _generate_whisper_sound(self, duration_ms: int) -> List[int]:
        """Generate whisper/breath sound."""
        num_samples = int((duration_ms / 1000.0) * self.sample_rate)

        samples = []
        prev = 0

        for i in range(num_samples):
            t = i / num_samples

            # Filtered noise
            noise = random.uniform(-1, 1)
            prev = prev * 0.9 + noise * 0.1

            # Breath envelope
            env = math.sin(math.pi * t) ** 0.5

            sample = prev * env * 6000
            samples.append(int(sample))

        return samples

    def _apply_envelope(
        self,
        samples: List[int],
        attack_ms: int,
        release_ms: int
    ) -> List[int]:
        """Apply attack/release envelope to samples."""
        attack_samples = int((attack_ms / 1000.0) * self.sample_rate)
        release_samples = int((release_ms / 1000.0) * self.sample_rate)

        result = samples.copy()

        # Attack
        for i in range(min(attack_samples, len(result))):
            result[i] = int(result[i] * (i / attack_samples))

        # Release
        release_start = max(0, len(result) - release_samples)
        for i in range(release_start, len(result)):
            progress = (i - release_start) / release_samples
            result[i] = int(result[i] * (1 - progress))

        return result

    def _samples_to_audio(self, samples: List[int]) -> AudioData:
        """Convert sample list to AudioData."""
        data = bytearray()
        for sample in samples:
            sample = max(-32768, min(32767, sample))
            data.extend(struct.pack('<h', sample))

        return AudioData(
            data=bytes(data),
            format=AudioFormat.RAW,
            sample_rate=self.sample_rate,
            channels=1,
            bit_depth=16
        )


@dataclass
class SoundInstance:
    """
    A playing instance of a sound effect.

    Tracks playback state and position.
    """
    sound: SoundEffect
    id: str
    properties: SoundProperties

    # Playback state
    is_playing: bool = True
    is_paused: bool = False
    position_ms: float = 0.0
    loop_count: int = 0

    # Spatial position (if 3D)
    position_3d: Optional[Tuple[float, float, float]] = None

    def update(self, delta_ms: float) -> None:
        """Update playback position."""
        if self.is_playing and not self.is_paused:
            self.position_ms += delta_ms

    def stop(self) -> None:
        """Stop playback."""
        self.is_playing = False

    def pause(self) -> None:
        """Pause playback."""
        self.is_paused = True

    def resume(self) -> None:
        """Resume playback."""
        self.is_paused = False


class SoundMixer:
    """
    Mixes multiple sound instances together.

    Handles volume, panning, and spatial positioning.
    """

    def __init__(self, master_volume: float = 1.0):
        self.master_volume = master_volume
        self._instances: Dict[str, SoundInstance] = {}
        self._instance_counter = 0
        self._category_volumes: Dict[SoundCategory, float] = {}

    def play(
        self,
        sound: SoundEffect,
        properties: Optional[SoundProperties] = None
    ) -> str:
        """
        Play a sound effect.

        Args:
            sound: Sound effect to play
            properties: Optional property overrides

        Returns:
            Instance ID for tracking
        """
        self._instance_counter += 1
        instance_id = f"snd_{self._instance_counter}"

        props = properties or sound.properties.apply_variation()

        instance = SoundInstance(
            sound=sound,
            id=instance_id,
            properties=props
        )

        self._instances[instance_id] = instance
        return instance_id

    def stop(self, instance_id: str) -> None:
        """Stop a specific sound instance."""
        if instance_id in self._instances:
            self._instances[instance_id].stop()

    def stop_all(self) -> None:
        """Stop all playing sounds."""
        for instance in self._instances.values():
            instance.stop()

    def stop_category(self, category: SoundCategory) -> None:
        """Stop all sounds in a category."""
        for instance in self._instances.values():
            if instance.sound.category == category:
                instance.stop()

    def set_category_volume(self, category: SoundCategory, volume: float) -> None:
        """Set volume multiplier for a category."""
        self._category_volumes[category] = max(0.0, min(1.0, volume))

    def get_category_volume(self, category: SoundCategory) -> float:
        """Get volume multiplier for a category."""
        return self._category_volumes.get(category, 1.0)

    def get_instance(self, instance_id: str) -> Optional[SoundInstance]:
        """Get a sound instance by ID."""
        return self._instances.get(instance_id)

    def get_playing_count(self) -> int:
        """Get count of currently playing sounds."""
        return sum(1 for i in self._instances.values() if i.is_playing)

    def update(self, delta_ms: float) -> None:
        """Update all sound instances."""
        # Update positions
        for instance in self._instances.values():
            instance.update(delta_ms)

        # Remove stopped instances
        self._instances = {
            k: v for k, v in self._instances.items()
            if v.is_playing
        }

    def mix_output(self, duration_ms: int, sample_rate: int = 22050) -> AudioData:
        """
        Mix all playing sounds into a single output.

        This is a simplified mixer - real implementation would
        handle proper sample-accurate mixing.
        """
        num_samples = int((duration_ms / 1000.0) * sample_rate)
        mixed = [0.0] * num_samples

        for instance in self._instances.values():
            if not instance.is_playing or instance.is_paused:
                continue

            # Get instance audio (simplified - assumes pre-generated)
            if instance.sound._audio_data:
                instance.sound._audio_data
                # Mix in at current position...
                # (Full implementation would be more complex)

        # Convert to output
        output = bytearray()
        for sample in mixed:
            s = int(max(-32768, min(32767, sample * self.master_volume * 32767)))
            output.extend(struct.pack('<h', s))

        return AudioData(
            data=bytes(output),
            format=AudioFormat.RAW,
            sample_rate=sample_rate,
            channels=1,
            bit_depth=16,
            duration_ms=duration_ms
        )
