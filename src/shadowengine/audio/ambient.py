"""
Ambient Sound System for ShadowEngine.

Provides environmental and atmospheric audio generation including
weather sounds, location ambience, and tension-based audio layers.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List, Any, Callable
import random
import math


class AmbientType(Enum):
    """Types of ambient sounds."""
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    THUNDER = "thunder"
    WIND = "wind"
    FOG_DRIP = "fog_drip"
    CITY_TRAFFIC = "city_traffic"
    CROWD_MURMUR = "crowd_murmur"
    MACHINERY = "machinery"
    WATER_FLOW = "water_flow"
    FOOTSTEPS_DISTANT = "footsteps_distant"
    CLOCK_TICK = "clock_tick"
    FIRE_CRACKLE = "fire_crackle"
    ELECTRIC_HUM = "electric_hum"
    HEARTBEAT = "heartbeat"
    SILENCE = "silence"


@dataclass
class AmbientConfig:
    """Configuration for ambient sound system."""

    master_volume: float = 0.7
    fade_time_ms: float = 2000.0
    max_layers: int = 8
    sample_rate: int = 22050

    # Tension-based settings
    tension_affects_volume: bool = True
    tension_affects_pitch: bool = False

    # Weather settings
    weather_crossfade_ms: float = 5000.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "master_volume": self.master_volume,
            "fade_time_ms": self.fade_time_ms,
            "max_layers": self.max_layers,
            "sample_rate": self.sample_rate,
            "tension_affects_volume": self.tension_affects_volume,
            "tension_affects_pitch": self.tension_affects_pitch,
            "weather_crossfade_ms": self.weather_crossfade_ms,
        }


@dataclass
class AmbientLayer:
    """A single layer of ambient sound."""

    id: str
    ambient_type: AmbientType

    # Volume and mix
    volume: float = 0.5          # 0.0 to 1.0
    target_volume: float = 0.5   # For fading
    pan: float = 0.0             # -1.0 (left) to 1.0 (right)

    # Variation
    variation: float = 0.1       # Random volume variation
    pitch_variation: float = 0.0  # Random pitch variation

    # Playback
    looping: bool = True
    fade_in_ms: float = 1000.0
    fade_out_ms: float = 1000.0

    # Stereo spread
    stereo_width: float = 1.0    # 0.0 (mono) to 1.0 (full stereo)

    # State
    is_playing: bool = False
    current_fade: float = 1.0    # 0.0 to 1.0 for fading

    # TTS seed for generation
    tts_seed: str = ""           # Base TTS sound to process
    processing_preset: str = ""   # Effects preset to apply

    @property
    def effective_volume(self) -> float:
        """Get volume including fade."""
        return self.volume * self.current_fade

    def start_fade_in(self) -> None:
        """Start fading in."""
        self.current_fade = 0.0
        self.is_playing = True

    def start_fade_out(self) -> None:
        """Start fading out."""
        self.target_volume = 0.0

    def update_fade(self, dt_ms: float) -> bool:
        """Update fade progress. Returns True if still fading."""
        if self.current_fade < 1.0 and self.volume > 0:
            # Fading in
            self.current_fade = min(1.0, self.current_fade + (dt_ms / self.fade_in_ms))
            return True
        elif self.target_volume < self.volume:
            # Fading out
            fade_amount = dt_ms / self.fade_out_ms
            self.volume = max(self.target_volume, self.volume - fade_amount)
            if self.volume <= 0:
                self.is_playing = False
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "ambient_type": self.ambient_type.value,
            "volume": self.volume,
            "target_volume": self.target_volume,
            "pan": self.pan,
            "variation": self.variation,
            "pitch_variation": self.pitch_variation,
            "looping": self.looping,
            "fade_in_ms": self.fade_in_ms,
            "fade_out_ms": self.fade_out_ms,
            "stereo_width": self.stereo_width,
            "is_playing": self.is_playing,
            "tts_seed": self.tts_seed,
            "processing_preset": self.processing_preset,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AmbientLayer':
        """Create from dictionary."""
        data = data.copy()
        data["ambient_type"] = AmbientType(data["ambient_type"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# Preset ambient layer configurations
AMBIENT_PRESETS = {
    AmbientType.RAIN: AmbientLayer(
        id="rain_default",
        ambient_type=AmbientType.RAIN,
        volume=0.4,
        tts_seed="shhhhh",
        processing_preset="rain",
        stereo_width=1.0,
        variation=0.15,
    ),
    AmbientType.HEAVY_RAIN: AmbientLayer(
        id="heavy_rain_default",
        ambient_type=AmbientType.HEAVY_RAIN,
        volume=0.6,
        tts_seed="shhhhhh patter patter",
        processing_preset="heavy_rain",
        stereo_width=1.0,
        variation=0.2,
    ),
    AmbientType.THUNDER: AmbientLayer(
        id="thunder_default",
        ambient_type=AmbientType.THUNDER,
        volume=0.7,
        tts_seed="boom rumble",
        processing_preset="cave",
        looping=False,
        fade_in_ms=100.0,
        fade_out_ms=3000.0,
    ),
    AmbientType.WIND: AmbientLayer(
        id="wind_default",
        ambient_type=AmbientType.WIND,
        volume=0.3,
        tts_seed="whoooosh",
        processing_preset="wind",
        variation=0.25,
    ),
    AmbientType.CITY_TRAFFIC: AmbientLayer(
        id="traffic_default",
        ambient_type=AmbientType.CITY_TRAFFIC,
        volume=0.25,
        tts_seed="vroom honk",
        processing_preset="city",
        stereo_width=0.8,
    ),
    AmbientType.CROWD_MURMUR: AmbientLayer(
        id="crowd_default",
        ambient_type=AmbientType.CROWD_MURMUR,
        volume=0.3,
        tts_seed="murmur murmur chatter",
        processing_preset="crowd",
        stereo_width=0.9,
    ),
    AmbientType.HEARTBEAT: AmbientLayer(
        id="heartbeat_default",
        ambient_type=AmbientType.HEARTBEAT,
        volume=0.5,
        tts_seed="thump thump",
        processing_preset="heartbeat",
        pan=0.0,
        stereo_width=0.3,
    ),
    AmbientType.CLOCK_TICK: AmbientLayer(
        id="clock_default",
        ambient_type=AmbientType.CLOCK_TICK,
        volume=0.2,
        tts_seed="tick tock",
        processing_preset="clock",
        pan=-0.3,
    ),
}


class WeatherAudio:
    """Manages weather-related ambient sounds."""

    def __init__(self):
        self._layers: Dict[str, AmbientLayer] = {}
        self._current_weather: Optional[str] = None

    @property
    def current_weather(self) -> Optional[str]:
        """Get current weather type."""
        return self._current_weather

    def set_weather(self, weather_type: str, intensity: float = 1.0) -> List[AmbientLayer]:
        """Set weather and return appropriate ambient layers."""
        self._current_weather = weather_type
        layers = []

        if weather_type == "clear":
            # Minimal ambient
            pass

        elif weather_type == "rain":
            rain_layer = AmbientLayer(
                id="weather_rain",
                ambient_type=AmbientType.RAIN,
                volume=0.3 + (intensity * 0.2),
                tts_seed="shhh patter",
                processing_preset="rain",
            )
            layers.append(rain_layer)

        elif weather_type == "heavy_rain":
            rain_layer = AmbientLayer(
                id="weather_heavy_rain",
                ambient_type=AmbientType.HEAVY_RAIN,
                volume=0.5 + (intensity * 0.2),
                tts_seed="shhhh splash patter",
                processing_preset="heavy_rain",
            )
            layers.append(rain_layer)

        elif weather_type == "storm":
            rain_layer = AmbientLayer(
                id="weather_storm_rain",
                ambient_type=AmbientType.HEAVY_RAIN,
                volume=0.6,
                tts_seed="shhhh crash",
                processing_preset="heavy_rain",
            )
            wind_layer = AmbientLayer(
                id="weather_storm_wind",
                ambient_type=AmbientType.WIND,
                volume=0.4,
                tts_seed="whoooosh howl",
                processing_preset="wind",
            )
            layers.extend([rain_layer, wind_layer])

        elif weather_type == "fog":
            drip_layer = AmbientLayer(
                id="weather_fog_drip",
                ambient_type=AmbientType.FOG_DRIP,
                volume=0.15,
                tts_seed="drip drip",
                processing_preset="fog",
            )
            layers.append(drip_layer)

        elif weather_type == "wind":
            wind_layer = AmbientLayer(
                id="weather_wind",
                ambient_type=AmbientType.WIND,
                volume=0.3 + (intensity * 0.3),
                tts_seed="whoosh whistle",
                processing_preset="wind",
            )
            layers.append(wind_layer)

        # Store layers
        for layer in layers:
            self._layers[layer.id] = layer

        return layers

    def add_thunder(self, distance: float = 0.5) -> AmbientLayer:
        """Add a thunder sound effect."""
        # Closer thunder = louder, shorter delay
        volume = 0.8 - (distance * 0.4)
        delay_ms = distance * 3000  # Sound delay based on distance

        thunder = AmbientLayer(
            id=f"thunder_{random.randint(0, 1000)}",
            ambient_type=AmbientType.THUNDER,
            volume=volume,
            looping=False,
            tts_seed="boom crack rumble",
            processing_preset="cave",
            fade_out_ms=2000 + (distance * 2000),
        )

        self._layers[thunder.id] = thunder
        return thunder

    def get_layers(self) -> List[AmbientLayer]:
        """Get all weather-related layers."""
        return list(self._layers.values())

    def clear(self) -> None:
        """Clear all weather layers."""
        self._layers.clear()
        self._current_weather = None


class LocationAudio:
    """Manages location-specific ambient sounds."""

    # Location presets
    LOCATION_PRESETS = {
        "street": [
            AmbientLayer(
                id="street_traffic",
                ambient_type=AmbientType.CITY_TRAFFIC,
                volume=0.25,
                tts_seed="vroom honk",
            ),
            AmbientLayer(
                id="street_footsteps",
                ambient_type=AmbientType.FOOTSTEPS_DISTANT,
                volume=0.1,
                tts_seed="tap tap",
            ),
        ],
        "bar": [
            AmbientLayer(
                id="bar_crowd",
                ambient_type=AmbientType.CROWD_MURMUR,
                volume=0.35,
                tts_seed="murmur chatter laugh",
            ),
            AmbientLayer(
                id="bar_glasses",
                ambient_type=AmbientType.MACHINERY,
                volume=0.1,
                tts_seed="clink clink",
            ),
        ],
        "office": [
            AmbientLayer(
                id="office_hum",
                ambient_type=AmbientType.ELECTRIC_HUM,
                volume=0.1,
                tts_seed="hmmmm",
            ),
            AmbientLayer(
                id="office_clock",
                ambient_type=AmbientType.CLOCK_TICK,
                volume=0.15,
                tts_seed="tick tock",
            ),
        ],
        "warehouse": [
            AmbientLayer(
                id="warehouse_echo",
                ambient_type=AmbientType.SILENCE,
                volume=0.05,
                processing_preset="cave",
            ),
            AmbientLayer(
                id="warehouse_creak",
                ambient_type=AmbientType.WIND,
                volume=0.1,
                tts_seed="creak",
            ),
        ],
        "docks": [
            AmbientLayer(
                id="docks_water",
                ambient_type=AmbientType.WATER_FLOW,
                volume=0.3,
                tts_seed="splash lap",
            ),
            AmbientLayer(
                id="docks_gulls",
                ambient_type=AmbientType.CROWD_MURMUR,
                volume=0.15,
                tts_seed="caw caw",
            ),
        ],
        "alley": [
            AmbientLayer(
                id="alley_drip",
                ambient_type=AmbientType.FOG_DRIP,
                volume=0.1,
                tts_seed="drip",
            ),
            AmbientLayer(
                id="alley_distant",
                ambient_type=AmbientType.CITY_TRAFFIC,
                volume=0.1,
                tts_seed="distant rumble",
            ),
        ],
    }

    def __init__(self):
        self._current_location: Optional[str] = None
        self._layers: List[AmbientLayer] = []

    @property
    def current_location(self) -> Optional[str]:
        """Get current location."""
        return self._current_location

    def set_location(self, location_type: str) -> List[AmbientLayer]:
        """Set location and return appropriate ambient layers."""
        self._current_location = location_type
        self._layers = []

        preset_layers = self.LOCATION_PRESETS.get(location_type, [])
        for preset in preset_layers:
            # Create a copy of the preset layer
            layer = AmbientLayer(
                id=preset.id,
                ambient_type=preset.ambient_type,
                volume=preset.volume,
                tts_seed=preset.tts_seed,
                processing_preset=preset.processing_preset,
            )
            layer.start_fade_in()
            self._layers.append(layer)

        return self._layers

    def get_layers(self) -> List[AmbientLayer]:
        """Get location ambient layers."""
        return self._layers.copy()

    def add_custom_layer(self, layer: AmbientLayer) -> None:
        """Add a custom ambient layer to the location."""
        self._layers.append(layer)

    def get_location_types(self) -> List[str]:
        """Get all available location types."""
        return list(self.LOCATION_PRESETS.keys())


class TensionAudio:
    """Manages tension-based ambient sounds."""

    def __init__(self):
        self._tension: float = 0.0
        self._layers: List[AmbientLayer] = []

    @property
    def tension(self) -> float:
        """Get current tension level."""
        return self._tension

    def set_tension(self, tension: float) -> List[AmbientLayer]:
        """Set tension level and return appropriate layers."""
        old_tension = self._tension
        self._tension = max(0.0, min(1.0, tension))

        self._layers = []

        # Low tension: subtle unease
        if self._tension > 0.2:
            hum_layer = AmbientLayer(
                id="tension_hum",
                ambient_type=AmbientType.ELECTRIC_HUM,
                volume=0.05 + (self._tension * 0.1),
                tts_seed="hmmm",
                pitch_variation=self._tension * 0.1,
            )
            self._layers.append(hum_layer)

        # Medium tension: heartbeat
        if self._tension > 0.5:
            heartbeat = AmbientLayer(
                id="tension_heartbeat",
                ambient_type=AmbientType.HEARTBEAT,
                volume=0.2 + ((self._tension - 0.5) * 0.6),
                tts_seed="thump thump",
                processing_preset="heartbeat",
            )
            self._layers.append(heartbeat)

        # High tension: breathing, subtle distortion
        if self._tension > 0.7:
            breath = AmbientLayer(
                id="tension_breath",
                ambient_type=AmbientType.WIND,
                volume=0.15 + ((self._tension - 0.7) * 0.3),
                tts_seed="hah hah",
                processing_preset="breathing",
                stereo_width=0.3,
            )
            self._layers.append(breath)

        # Critical tension: everything intensifies
        if self._tension > 0.9:
            for layer in self._layers:
                layer.volume *= 1.3
                layer.pitch_variation += 0.1

        return self._layers

    def get_layers(self) -> List[AmbientLayer]:
        """Get tension ambient layers."""
        return self._layers.copy()

    def get_heartbeat_rate(self) -> float:
        """Get suggested heartbeat rate based on tension."""
        base_bpm = 60
        max_bpm = 140
        return base_bpm + (self._tension * (max_bpm - base_bpm))


class AmbientEngine:
    """Main ambient sound engine coordinating all ambient sources."""

    def __init__(self, config: Optional[AmbientConfig] = None):
        self.config = config or AmbientConfig()
        self._weather = WeatherAudio()
        self._location = LocationAudio()
        self._tension = TensionAudio()
        self._custom_layers: Dict[str, AmbientLayer] = {}
        self._master_volume = self.config.master_volume
        self._muted = False

    @property
    def master_volume(self) -> float:
        """Get master volume."""
        return self._master_volume

    @master_volume.setter
    def master_volume(self, value: float) -> None:
        """Set master volume."""
        self._master_volume = max(0.0, min(1.0, value))

    @property
    def muted(self) -> bool:
        """Check if muted."""
        return self._muted

    def mute(self) -> None:
        """Mute all ambient audio."""
        self._muted = True

    def unmute(self) -> None:
        """Unmute ambient audio."""
        self._muted = False

    def set_weather(self, weather_type: str, intensity: float = 1.0) -> None:
        """Set current weather."""
        self._weather.set_weather(weather_type, intensity)

    def set_location(self, location_type: str) -> None:
        """Set current location."""
        self._location.set_location(location_type)

    def set_tension(self, tension: float) -> None:
        """Set tension level."""
        self._tension.set_tension(tension)

    def add_thunder(self, distance: float = 0.5) -> AmbientLayer:
        """Add thunder effect."""
        return self._weather.add_thunder(distance)

    def add_custom_layer(self, layer: AmbientLayer) -> None:
        """Add a custom ambient layer."""
        self._custom_layers[layer.id] = layer

    def remove_custom_layer(self, layer_id: str) -> Optional[AmbientLayer]:
        """Remove a custom layer."""
        return self._custom_layers.pop(layer_id, None)

    def get_all_layers(self) -> List[AmbientLayer]:
        """Get all active ambient layers."""
        layers = []
        layers.extend(self._weather.get_layers())
        layers.extend(self._location.get_layers())
        layers.extend(self._tension.get_layers())
        layers.extend(self._custom_layers.values())

        # Apply master volume
        for layer in layers:
            if not self._muted:
                layer.volume *= self._master_volume
            else:
                layer.volume = 0.0

        return layers

    def get_layer_count(self) -> int:
        """Get total number of active layers."""
        return len(self.get_all_layers())

    def update(self, dt_ms: float) -> None:
        """Update all ambient layers."""
        for layer in self.get_all_layers():
            layer.update_fade(dt_ms)

    def generate_mix(self, duration_ms: float, sample_rate: Optional[int] = None) -> bytes:
        """Generate mixed ambient audio data."""
        sample_rate = sample_rate or self.config.sample_rate
        layers = self.get_all_layers()

        if not layers or self._muted:
            # Return silence
            num_samples = int((duration_ms / 1000.0) * sample_rate)
            return b"\x00" * (num_samples * 2)

        # In a real implementation, this would mix all layer audio
        # For simulation, return placeholder data
        num_samples = int((duration_ms / 1000.0) * sample_rate)
        return b"\x10" * (num_samples * 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config": self.config.to_dict(),
            "master_volume": self._master_volume,
            "muted": self._muted,
            "weather": self._weather.current_weather,
            "location": self._location.current_location,
            "tension": self._tension.tension,
            "custom_layers": {k: v.to_dict() for k, v in self._custom_layers.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AmbientEngine':
        """Create from dictionary."""
        config = AmbientConfig(**data.get("config", {}))
        engine = cls(config)
        engine._master_volume = data.get("master_volume", 0.7)
        engine._muted = data.get("muted", False)

        if data.get("weather"):
            engine.set_weather(data["weather"])
        if data.get("location"):
            engine.set_location(data["location"])
        if data.get("tension"):
            engine.set_tension(data["tension"])

        for layer_data in data.get("custom_layers", {}).values():
            engine.add_custom_layer(AmbientLayer.from_dict(layer_data))

        return engine
