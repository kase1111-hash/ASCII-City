"""
Ambient Audio System - Environmental and atmospheric sounds.

Creates layered ambient soundscapes that respond to
game state, weather, time, and tension.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
import random
import math

from .sound import SoundGenerator, SoundCategory, SoundProperties, SoundEffect, SoundTrigger
from .tts_engine import AudioData, AudioFormat


class AmbienceType(Enum):
    """Types of ambient sound environments."""
    CITY_NIGHT = "city_night"
    CITY_DAY = "city_day"
    RAIN = "rain"
    STORM = "storm"
    INDOOR_QUIET = "indoor_quiet"
    INDOOR_BUSY = "indoor_busy"
    ALLEY = "alley"
    WATERFRONT = "waterfront"
    OFFICE = "office"
    BAR = "bar"
    STREET = "street"
    SUBWAY = "subway"


class WeatherType(Enum):
    """Weather conditions affecting audio."""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN_LIGHT = "rain_light"
    RAIN_HEAVY = "rain_heavy"
    STORM = "storm"
    FOG = "fog"
    SNOW = "snow"
    WIND = "wind"


class TimeOfDay(Enum):
    """Time periods affecting ambience."""
    DAWN = "dawn"
    MORNING = "morning"
    NOON = "noon"
    AFTERNOON = "afternoon"
    DUSK = "dusk"
    EVENING = "evening"
    NIGHT = "night"
    LATE_NIGHT = "late_night"


@dataclass
class AmbientLayer:
    """
    A single layer of ambient sound.

    Multiple layers combine to create complex soundscapes.
    """
    id: str
    name: str
    sound_type: str  # Corresponds to SoundGenerator sound types

    # Volume and mixing
    base_volume: float = 0.5
    current_volume: float = 0.5

    # Modulation
    volume_mod_speed: float = 0.1  # How fast volume changes
    volume_mod_range: float = 0.2  # Range of volume modulation

    # Playback
    is_active: bool = True
    loop: bool = True
    duration_ms: int = 5000

    # Conditions
    weather_types: List[WeatherType] = field(default_factory=list)
    time_periods: List[TimeOfDay] = field(default_factory=list)
    min_tension: float = 0.0
    max_tension: float = 1.0

    # Random events
    event_chance: float = 0.0  # Chance per second of random sound
    event_sounds: List[str] = field(default_factory=list)

    def should_play(
        self,
        weather: WeatherType,
        time: TimeOfDay,
        tension: float
    ) -> bool:
        """Check if this layer should be active given conditions."""
        if not self.is_active:
            return False

        # Check weather
        if self.weather_types and weather not in self.weather_types:
            return False

        # Check time
        if self.time_periods and time not in self.time_periods:
            return False

        # Check tension
        if tension < self.min_tension or tension > self.max_tension:
            return False

        return True

    def update_volume(self, delta_seconds: float) -> None:
        """Update volume with natural variation."""
        # Simple sine-based modulation
        mod = math.sin(delta_seconds * self.volume_mod_speed * 2 * math.pi)
        mod *= self.volume_mod_range
        self.current_volume = max(0, min(1, self.base_volume + mod))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'sound_type': self.sound_type,
            'base_volume': self.base_volume,
            'loop': self.loop,
            'duration_ms': self.duration_ms,
            'weather_types': [w.value for w in self.weather_types],
            'time_periods': [t.value for t in self.time_periods],
            'min_tension': self.min_tension,
            'max_tension': self.max_tension,
            'event_chance': self.event_chance,
            'event_sounds': self.event_sounds
        }


@dataclass
class AmbiencePreset:
    """
    A preset ambient environment with multiple layers.
    """
    id: str
    name: str
    ambience_type: AmbienceType
    layers: List[AmbientLayer] = field(default_factory=list)

    # Overall settings
    master_volume: float = 1.0
    crossfade_ms: int = 2000

    # Tension response
    tension_layer_id: Optional[str] = None  # Layer that responds to tension

    def get_active_layers(
        self,
        weather: WeatherType,
        time: TimeOfDay,
        tension: float
    ) -> List[AmbientLayer]:
        """Get layers that should be active given conditions."""
        return [
            layer for layer in self.layers
            if layer.should_play(weather, time, tension)
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'ambience_type': self.ambience_type.value,
            'layers': [l.to_dict() for l in self.layers],
            'master_volume': self.master_volume,
            'crossfade_ms': self.crossfade_ms,
            'tension_layer_id': self.tension_layer_id
        }


class WeatherAudio:
    """
    Manages weather-specific audio.

    Generates and mixes weather sounds based on conditions.
    """

    def __init__(self, generator: Optional[SoundGenerator] = None):
        self.generator = generator or SoundGenerator()
        self._current_weather = WeatherType.CLEAR
        self._intensity = 0.5
        self._cached_audio: Dict[str, AudioData] = {}

    def set_weather(self, weather: WeatherType, intensity: float = 0.5) -> None:
        """Set current weather conditions."""
        self._current_weather = weather
        self._intensity = max(0.0, min(1.0, intensity))

    def get_weather_audio(self, duration_ms: int = 5000) -> Optional[AudioData]:
        """
        Generate audio for current weather.

        Returns None for clear weather.
        """
        if self._current_weather == WeatherType.CLEAR:
            return None

        weather_sounds = {
            WeatherType.RAIN_LIGHT: ('rain', 0.4),
            WeatherType.RAIN_HEAVY: ('rain', 0.8),
            WeatherType.STORM: ('thunder', 1.0),
            WeatherType.WIND: ('wind', 0.6),
            WeatherType.FOG: ('wind', 0.2),
            WeatherType.SNOW: ('wind', 0.3),
            WeatherType.CLOUDY: ('wind', 0.1),
        }

        if self._current_weather not in weather_sounds:
            return None

        sound_type, base_intensity = weather_sounds[self._current_weather]
        effective_intensity = base_intensity * self._intensity

        # Generate or retrieve cached audio
        cache_key = f"{sound_type}_{duration_ms}"
        if cache_key not in self._cached_audio:
            self._cached_audio[cache_key] = self.generator.generate(
                sound_type, duration_ms
            )

        audio = self._cached_audio[cache_key]

        # Apply intensity (volume scaling)
        if effective_intensity < 1.0:
            audio = self._scale_volume(audio, effective_intensity)

        return audio

    def _scale_volume(self, audio: AudioData, scale: float) -> AudioData:
        """Scale audio volume."""
        import struct

        samples = []
        for i in range(0, len(audio.data) - 1, 2):
            sample = struct.unpack('<h', audio.data[i:i+2])[0]
            scaled = int(sample * scale)
            samples.append(max(-32768, min(32767, scaled)))

        new_data = bytearray()
        for sample in samples:
            new_data.extend(struct.pack('<h', sample))

        return AudioData(
            data=bytes(new_data),
            format=audio.format,
            sample_rate=audio.sample_rate,
            channels=audio.channels,
            bit_depth=audio.bit_depth,
            duration_ms=audio.duration_ms
        )

    def should_play_thunder(self) -> bool:
        """Check if thunder should play (random during storm)."""
        if self._current_weather != WeatherType.STORM:
            return False
        return random.random() < 0.1 * self._intensity

    def get_thunder_audio(self, seed: Optional[int] = None) -> AudioData:
        """Generate a thunder sound."""
        duration = random.randint(2000, 5000)
        return self.generator.generate('thunder', duration, seed)


class TensionAudio:
    """
    Manages tension-responsive audio.

    Creates audio elements that respond to game tension level.
    """

    def __init__(self, generator: Optional[SoundGenerator] = None):
        self.generator = generator or SoundGenerator()
        self._tension = 0.0
        self._heartbeat_enabled = True
        self._drone_enabled = True

    def set_tension(self, tension: float) -> None:
        """Set current tension level (0.0 to 1.0)."""
        self._tension = max(0.0, min(1.0, tension))

    def get_tension(self) -> float:
        """Get current tension level."""
        return self._tension

    def should_play_heartbeat(self) -> bool:
        """Check if heartbeat should play based on tension."""
        if not self._heartbeat_enabled:
            return False
        return self._tension > 0.7

    def get_heartbeat_audio(self, duration_ms: int = 1000) -> AudioData:
        """Generate heartbeat audio at current tension."""
        # Heartbeat speed increases with tension
        # At tension 0.7: ~60 BPM, at 1.0: ~120 BPM
        bpm = 60 + (self._tension - 0.7) * 200
        beat_duration = int(60000 / bpm)
        return self.generator.generate('heartbeat', min(duration_ms, beat_duration * 2))

    def get_tension_drone(self, duration_ms: int = 5000) -> Optional[AudioData]:
        """Generate low tension drone sound."""
        if not self._drone_enabled or self._tension < 0.3:
            return None

        # Low frequency drone that increases with tension
        samples = []
        sample_rate = 22050
        num_samples = int((duration_ms / 1000.0) * sample_rate)

        base_freq = 30 + self._tension * 20  # 30-50 Hz

        for i in range(num_samples):
            t = i / sample_rate
            # Multiple harmonics
            sample = (
                math.sin(2 * math.pi * base_freq * t) * 0.5 +
                math.sin(2 * math.pi * base_freq * 1.5 * t) * 0.3 +
                math.sin(2 * math.pi * base_freq * 2 * t) * 0.2
            )
            # Slow amplitude modulation
            mod = (math.sin(t * 0.5) + 1) / 2 * 0.3 + 0.7
            sample *= mod * self._tension * 8000
            samples.append(int(sample))

        import struct
        data = bytearray()
        for s in samples:
            s = max(-32768, min(32767, s))
            data.extend(struct.pack('<h', s))

        return AudioData(
            data=bytes(data),
            format=AudioFormat.RAW,
            sample_rate=sample_rate,
            channels=1,
            bit_depth=16,
            duration_ms=duration_ms
        )

    def get_scare_sting(self) -> AudioData:
        """Generate a sudden scare audio sting."""
        # Sharp, dissonant sound for jump scares
        samples = []
        sample_rate = 22050
        duration_ms = 500
        num_samples = int((duration_ms / 1000.0) * sample_rate)

        for i in range(num_samples):
            t = i / num_samples
            time = i / sample_rate

            # Quick attack, fast decay
            if t < 0.05:
                env = t / 0.05
            else:
                env = math.exp(-(t - 0.05) * 5)

            # Dissonant frequencies
            f1 = math.sin(2 * math.pi * 200 * time)
            f2 = math.sin(2 * math.pi * 283 * time)  # Tritone
            f3 = math.sin(2 * math.pi * 400 * time)
            noise = random.uniform(-0.3, 0.3)

            sample = (f1 + f2 + f3 + noise) * env * 24000
            samples.append(int(max(-32768, min(32767, sample))))

        import struct
        data = bytearray()
        for s in samples:
            data.extend(struct.pack('<h', s))

        return AudioData(
            data=bytes(data),
            format=AudioFormat.RAW,
            sample_rate=sample_rate,
            channels=1,
            bit_depth=16,
            duration_ms=duration_ms
        )


class AmbienceManager:
    """
    Manages ambient audio for the game.

    Coordinates weather, tension, and environmental ambience.
    """

    def __init__(self):
        self.generator = SoundGenerator()
        self.weather_audio = WeatherAudio(self.generator)
        self.tension_audio = TensionAudio(self.generator)

        self._current_preset: Optional[AmbiencePreset] = None
        self._presets: Dict[str, AmbiencePreset] = {}
        self._time_of_day = TimeOfDay.NIGHT
        self._master_volume = 1.0

        # Initialize default presets
        self._init_default_presets()

    def _init_default_presets(self) -> None:
        """Initialize built-in ambience presets."""
        # City Night
        city_night = AmbiencePreset(
            id="city_night",
            name="City Night",
            ambience_type=AmbienceType.CITY_NIGHT,
            layers=[
                AmbientLayer(
                    id="traffic_distant",
                    name="Distant Traffic",
                    sound_type="wind",
                    base_volume=0.2,
                    duration_ms=8000
                ),
                AmbientLayer(
                    id="city_hum",
                    name="City Hum",
                    sound_type="static",
                    base_volume=0.1,
                    duration_ms=10000
                ),
                AmbientLayer(
                    id="night_events",
                    name="Night Events",
                    sound_type="footstep",
                    base_volume=0.3,
                    event_chance=0.05,
                    event_sounds=['footstep', 'door', 'drip']
                )
            ],
            tension_layer_id="night_events"
        )
        self._presets[city_night.id] = city_night

        # Rain
        rain = AmbiencePreset(
            id="rain",
            name="Rain",
            ambience_type=AmbienceType.RAIN,
            layers=[
                AmbientLayer(
                    id="rain_base",
                    name="Rain",
                    sound_type="rain",
                    base_volume=0.6,
                    duration_ms=10000,
                    weather_types=[WeatherType.RAIN_LIGHT, WeatherType.RAIN_HEAVY]
                ),
                AmbientLayer(
                    id="rain_drips",
                    name="Drips",
                    sound_type="drip",
                    base_volume=0.3,
                    event_chance=0.2,
                    event_sounds=['drip'],
                    weather_types=[WeatherType.RAIN_LIGHT, WeatherType.RAIN_HEAVY]
                )
            ]
        )
        self._presets[rain.id] = rain

        # Storm
        storm = AmbiencePreset(
            id="storm",
            name="Storm",
            ambience_type=AmbienceType.STORM,
            layers=[
                AmbientLayer(
                    id="storm_rain",
                    name="Heavy Rain",
                    sound_type="rain",
                    base_volume=0.8,
                    duration_ms=8000,
                    weather_types=[WeatherType.STORM]
                ),
                AmbientLayer(
                    id="storm_wind",
                    name="Wind",
                    sound_type="wind",
                    base_volume=0.5,
                    duration_ms=6000,
                    weather_types=[WeatherType.STORM]
                ),
                AmbientLayer(
                    id="storm_thunder",
                    name="Thunder",
                    sound_type="thunder",
                    base_volume=0.9,
                    event_chance=0.1,
                    event_sounds=['thunder'],
                    weather_types=[WeatherType.STORM]
                )
            ]
        )
        self._presets[storm.id] = storm

        # Indoor Quiet
        indoor = AmbiencePreset(
            id="indoor_quiet",
            name="Indoor Quiet",
            ambience_type=AmbienceType.INDOOR_QUIET,
            layers=[
                AmbientLayer(
                    id="room_tone",
                    name="Room Tone",
                    sound_type="static",
                    base_volume=0.05,
                    duration_ms=10000
                ),
                AmbientLayer(
                    id="indoor_creaks",
                    name="Creaks",
                    sound_type="creak",
                    base_volume=0.2,
                    event_chance=0.02,
                    event_sounds=['creak']
                )
            ]
        )
        self._presets[indoor.id] = indoor

        # Alley
        alley = AmbiencePreset(
            id="alley",
            name="Alley",
            ambience_type=AmbienceType.ALLEY,
            layers=[
                AmbientLayer(
                    id="alley_wind",
                    name="Wind",
                    sound_type="wind",
                    base_volume=0.3,
                    duration_ms=7000
                ),
                AmbientLayer(
                    id="alley_drips",
                    name="Drips",
                    sound_type="drip",
                    base_volume=0.25,
                    event_chance=0.08,
                    event_sounds=['drip']
                ),
                AmbientLayer(
                    id="alley_distant",
                    name="Distant Sounds",
                    sound_type="footstep",
                    base_volume=0.15,
                    event_chance=0.03,
                    event_sounds=['footstep', 'door']
                )
            ]
        )
        self._presets[alley.id] = alley

    def set_preset(self, preset_id: str) -> bool:
        """Set the active ambience preset."""
        if preset_id in self._presets:
            self._current_preset = self._presets[preset_id]
            return True
        return False

    def get_preset(self, preset_id: str) -> Optional[AmbiencePreset]:
        """Get a preset by ID."""
        return self._presets.get(preset_id)

    def add_preset(self, preset: AmbiencePreset) -> None:
        """Add a custom ambience preset."""
        self._presets[preset.id] = preset

    def set_weather(self, weather: WeatherType, intensity: float = 0.5) -> None:
        """Set weather conditions."""
        self.weather_audio.set_weather(weather, intensity)

    def set_tension(self, tension: float) -> None:
        """Set tension level."""
        self.tension_audio.set_tension(tension)

    def set_time_of_day(self, time: TimeOfDay) -> None:
        """Set time of day."""
        self._time_of_day = time

    def set_master_volume(self, volume: float) -> None:
        """Set master volume."""
        self._master_volume = max(0.0, min(1.0, volume))

    def get_active_layers(self) -> List[AmbientLayer]:
        """Get currently active ambient layers."""
        if not self._current_preset:
            return []

        return self._current_preset.get_active_layers(
            self.weather_audio._current_weather,
            self._time_of_day,
            self.tension_audio.get_tension()
        )

    def generate_ambient_mix(self, duration_ms: int = 5000) -> AudioData:
        """
        Generate mixed ambient audio for current conditions.

        Combines all active layers into a single output.
        """
        sample_rate = 22050
        num_samples = int((duration_ms / 1000.0) * sample_rate)
        mixed = [0.0] * num_samples

        # Add ambient layers
        for layer in self.get_active_layers():
            layer_audio = self.generator.generate(
                layer.sound_type,
                layer.duration_ms
            )

            # Mix layer into output
            layer_samples = self._audio_to_samples(layer_audio)
            volume = layer.current_volume * self._master_volume

            for i in range(min(len(mixed), len(layer_samples))):
                mixed[i] += layer_samples[i] * volume

        # Add weather
        weather_audio = self.weather_audio.get_weather_audio(duration_ms)
        if weather_audio:
            weather_samples = self._audio_to_samples(weather_audio)
            for i in range(min(len(mixed), len(weather_samples))):
                mixed[i] += weather_samples[i] * 0.5 * self._master_volume

        # Add tension
        if self.tension_audio.should_play_heartbeat():
            hb = self.tension_audio.get_heartbeat_audio(duration_ms)
            hb_samples = self._audio_to_samples(hb)
            for i in range(min(len(mixed), len(hb_samples))):
                mixed[i] += hb_samples[i] * 0.3

        # Normalize and convert
        max_val = max(abs(s) for s in mixed) if mixed else 1
        if max_val > 32767:
            mixed = [s * 32767 / max_val for s in mixed]

        import struct
        data = bytearray()
        for s in mixed:
            s = int(max(-32768, min(32767, s)))
            data.extend(struct.pack('<h', s))

        return AudioData(
            data=bytes(data),
            format=AudioFormat.RAW,
            sample_rate=sample_rate,
            channels=1,
            bit_depth=16,
            duration_ms=duration_ms
        )

    def _audio_to_samples(self, audio: AudioData) -> List[float]:
        """Convert AudioData to sample list."""
        import struct
        samples = []
        for i in range(0, len(audio.data) - 1, 2):
            sample = struct.unpack('<h', audio.data[i:i+2])[0]
            samples.append(float(sample))
        return samples

    def get_random_event_sound(self) -> Optional[AudioData]:
        """Get a random event sound if one should play."""
        for layer in self.get_active_layers():
            if layer.event_chance > 0 and random.random() < layer.event_chance:
                if layer.event_sounds:
                    sound_type = random.choice(layer.event_sounds)
                    return self.generator.generate(sound_type, 500)
        return None
