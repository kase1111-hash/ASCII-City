"""
Weather System - Dynamic weather simulation.

Provides atmospheric conditions that affect gameplay:
- Weather states (clear, rain, fog, storm)
- Weather effects on visibility, evidence, NPCs
- Procedural weather transitions
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar, Optional
import random


class WeatherType(Enum):
    """Types of weather conditions."""
    CLEAR = auto()
    CLOUDY = auto()
    OVERCAST = auto()
    LIGHT_RAIN = auto()
    HEAVY_RAIN = auto()
    STORM = auto()
    FOG = auto()
    MIST = auto()
    SNOW = auto()
    WIND = auto()


@dataclass
class WeatherEffect:
    """Effects of weather on gameplay."""

    # Visibility modifier (1.0 = normal)
    visibility: float = 1.0

    # Noise modifier (1.0 = normal, higher = more background noise)
    ambient_noise: float = 1.0

    # Movement speed modifier
    movement_speed: float = 1.0

    # Evidence degradation rate modifier
    evidence_degradation: float = 1.0

    # NPC behavior modifiers
    npc_indoor_preference: float = 0.0  # 0-1, chance NPCs stay inside
    npc_conversation_penalty: float = 0.0  # Reduces trust gain

    # Descriptive effects
    outdoor_description: str = ""
    indoor_description: str = ""
    sound_description: str = ""


# Predefined weather effects
WEATHER_EFFECTS: dict[WeatherType, WeatherEffect] = {
    WeatherType.CLEAR: WeatherEffect(
        visibility=1.0,
        ambient_noise=0.8,
        outdoor_description="The sky is clear.",
        indoor_description="Sunlight streams through the windows.",
        sound_description="Birds chirp outside.",
    ),
    WeatherType.CLOUDY: WeatherEffect(
        visibility=0.9,
        ambient_noise=0.9,
        outdoor_description="Clouds drift across the sky.",
        indoor_description="Gray light filters through the windows.",
    ),
    WeatherType.OVERCAST: WeatherEffect(
        visibility=0.8,
        ambient_noise=1.0,
        outdoor_description="Heavy clouds blanket the sky.",
        indoor_description="The light is dim and gray.",
    ),
    WeatherType.LIGHT_RAIN: WeatherEffect(
        visibility=0.7,
        ambient_noise=1.3,
        movement_speed=0.9,
        evidence_degradation=1.5,
        npc_indoor_preference=0.6,
        outdoor_description="A gentle rain falls.",
        indoor_description="Rain patters against the windows.",
        sound_description="The soft rhythm of raindrops.",
    ),
    WeatherType.HEAVY_RAIN: WeatherEffect(
        visibility=0.5,
        ambient_noise=1.8,
        movement_speed=0.7,
        evidence_degradation=2.5,
        npc_indoor_preference=0.9,
        npc_conversation_penalty=0.2,
        outdoor_description="Rain pours down in sheets.",
        indoor_description="Rain drums heavily on the roof.",
        sound_description="The roar of falling rain drowns out other sounds.",
    ),
    WeatherType.STORM: WeatherEffect(
        visibility=0.3,
        ambient_noise=2.5,
        movement_speed=0.5,
        evidence_degradation=3.0,
        npc_indoor_preference=1.0,
        npc_conversation_penalty=0.4,
        outdoor_description="Thunder rolls as lightning splits the sky.",
        indoor_description="The building shudders with each thunderclap.",
        sound_description="Thunder and howling wind fill the air.",
    ),
    WeatherType.FOG: WeatherEffect(
        visibility=0.3,
        ambient_noise=0.6,
        movement_speed=0.8,
        npc_indoor_preference=0.3,
        outdoor_description="Thick fog obscures everything beyond a few feet.",
        indoor_description="Mist presses against the windows.",
        sound_description="An eerie silence hangs in the fog.",
    ),
    WeatherType.MIST: WeatherEffect(
        visibility=0.6,
        ambient_noise=0.7,
        outdoor_description="A light mist hangs in the air.",
        indoor_description="Moisture beads on the windows.",
    ),
    WeatherType.SNOW: WeatherEffect(
        visibility=0.6,
        ambient_noise=0.5,
        movement_speed=0.7,
        evidence_degradation=2.0,
        npc_indoor_preference=0.7,
        outdoor_description="Snow falls silently from the gray sky.",
        indoor_description="Snowflakes drift past the windows.",
        sound_description="A hushed quiet blankets everything.",
    ),
    WeatherType.WIND: WeatherEffect(
        visibility=0.9,
        ambient_noise=1.5,
        movement_speed=0.85,
        evidence_degradation=1.3,
        npc_indoor_preference=0.4,
        outdoor_description="A strong wind whips through the area.",
        indoor_description="Wind rattles the windows.",
        sound_description="The wind howls and moans.",
    ),
}


@dataclass
class WeatherState:
    """Current weather state with intensity and duration."""

    weather_type: WeatherType
    intensity: float = 1.0  # 0.0 to 1.0
    duration_remaining: int = 60  # minutes
    transitioning_to: Optional[WeatherType] = None
    transition_progress: float = 0.0

    def get_effect(self) -> WeatherEffect:
        """Get current weather effect, accounting for intensity."""
        base_effect = WEATHER_EFFECTS[self.weather_type]

        # Interpolate effect based on intensity
        return WeatherEffect(
            visibility=1.0 - (1.0 - base_effect.visibility) * self.intensity,
            ambient_noise=1.0 + (base_effect.ambient_noise - 1.0) * self.intensity,
            movement_speed=1.0 - (1.0 - base_effect.movement_speed) * self.intensity,
            evidence_degradation=1.0 + (base_effect.evidence_degradation - 1.0) * self.intensity,
            npc_indoor_preference=base_effect.npc_indoor_preference * self.intensity,
            npc_conversation_penalty=base_effect.npc_conversation_penalty * self.intensity,
            outdoor_description=base_effect.outdoor_description,
            indoor_description=base_effect.indoor_description,
            sound_description=base_effect.sound_description,
        )

    def get_description(self, is_indoor: bool = False) -> str:
        """Get weather description based on location."""
        effect = self.get_effect()
        if is_indoor:
            return effect.indoor_description
        return effect.outdoor_description


@dataclass
class WeatherSystem:
    """
    Manages weather simulation and transitions.

    Weather changes based on:
    - Random transitions with weighted probabilities
    - Seed-based deterministic generation
    - Manual weather setting for scenarios
    """

    current_state: WeatherState = field(
        default_factory=lambda: WeatherState(WeatherType.CLEAR)
    )

    # Seed for deterministic weather
    seed: Optional[int] = None
    _rng: random.Random = field(default_factory=random.Random, repr=False)

    # Weather history for atmosphere
    history: list[tuple[int, WeatherType]] = field(default_factory=list)

    # Current game time (updated externally)
    current_time: int = 0

    # Transition probabilities (from -> to -> probability)
    _transition_weights: dict[WeatherType, dict[WeatherType, float]] = field(
        default_factory=dict, repr=False
    )

    def __post_init__(self):
        """Initialize RNG and default transitions."""
        if self.seed is not None:
            self._rng.seed(self.seed)

        self._setup_default_transitions()

        if not self.history:
            self.history.append((0, self.current_state.weather_type))

    def _setup_default_transitions(self) -> None:
        """Set up default weather transition probabilities."""
        # Each weather type has weights for what it might change to
        self._transition_weights = {
            WeatherType.CLEAR: {
                WeatherType.CLEAR: 0.6,
                WeatherType.CLOUDY: 0.25,
                WeatherType.MIST: 0.1,
                WeatherType.WIND: 0.05,
            },
            WeatherType.CLOUDY: {
                WeatherType.CLEAR: 0.2,
                WeatherType.CLOUDY: 0.4,
                WeatherType.OVERCAST: 0.25,
                WeatherType.LIGHT_RAIN: 0.1,
                WeatherType.WIND: 0.05,
            },
            WeatherType.OVERCAST: {
                WeatherType.CLOUDY: 0.2,
                WeatherType.OVERCAST: 0.3,
                WeatherType.LIGHT_RAIN: 0.3,
                WeatherType.FOG: 0.1,
                WeatherType.HEAVY_RAIN: 0.1,
            },
            WeatherType.LIGHT_RAIN: {
                WeatherType.CLOUDY: 0.15,
                WeatherType.OVERCAST: 0.2,
                WeatherType.LIGHT_RAIN: 0.35,
                WeatherType.HEAVY_RAIN: 0.2,
                WeatherType.MIST: 0.1,
            },
            WeatherType.HEAVY_RAIN: {
                WeatherType.LIGHT_RAIN: 0.3,
                WeatherType.HEAVY_RAIN: 0.3,
                WeatherType.STORM: 0.25,
                WeatherType.OVERCAST: 0.15,
            },
            WeatherType.STORM: {
                WeatherType.HEAVY_RAIN: 0.4,
                WeatherType.STORM: 0.3,
                WeatherType.OVERCAST: 0.2,
                WeatherType.WIND: 0.1,
            },
            WeatherType.FOG: {
                WeatherType.FOG: 0.4,
                WeatherType.MIST: 0.3,
                WeatherType.CLOUDY: 0.2,
                WeatherType.CLEAR: 0.1,
            },
            WeatherType.MIST: {
                WeatherType.MIST: 0.3,
                WeatherType.CLEAR: 0.3,
                WeatherType.FOG: 0.2,
                WeatherType.CLOUDY: 0.2,
            },
            WeatherType.SNOW: {
                WeatherType.SNOW: 0.5,
                WeatherType.OVERCAST: 0.25,
                WeatherType.CLOUDY: 0.15,
                WeatherType.CLEAR: 0.1,
            },
            WeatherType.WIND: {
                WeatherType.WIND: 0.3,
                WeatherType.CLEAR: 0.25,
                WeatherType.CLOUDY: 0.25,
                WeatherType.STORM: 0.1,
                WeatherType.OVERCAST: 0.1,
            },
        }

    def set_seed(self, seed: int) -> None:
        """Set RNG seed for deterministic weather."""
        self.seed = seed
        self._rng.seed(seed)

    def update(self, minutes_passed: int) -> Optional[WeatherType]:
        """
        Update weather state. Returns new weather type if changed.
        """
        self.current_time += minutes_passed
        old_weather = self.current_state.weather_type

        # Handle ongoing transition
        if self.current_state.transitioning_to:
            transition_rate = 0.02 * minutes_passed  # ~50 min for full transition
            self.current_state.transition_progress += transition_rate

            if self.current_state.transition_progress >= 1.0:
                # Complete transition
                new_weather = self.current_state.transitioning_to
                self.current_state = WeatherState(
                    weather_type=new_weather,
                    intensity=self._rng.uniform(0.5, 1.0),
                    duration_remaining=self._rng.randint(30, 180),
                )
                self.history.append((self.current_time, new_weather))
                return new_weather
        else:
            # Decrease duration
            self.current_state.duration_remaining -= minutes_passed

            # Time for a change?
            if self.current_state.duration_remaining <= 0:
                new_weather = self._select_next_weather()
                if new_weather != old_weather:
                    self.current_state.transitioning_to = new_weather
                    self.current_state.transition_progress = 0.0
                else:
                    # Same weather, extend duration
                    self.current_state.duration_remaining = self._rng.randint(30, 120)

        return None

    # Map ThemeConfig weather_weights keys to WeatherType values
    _THEME_KEY_MAP: ClassVar[dict[str, list]] = {
        "clear": [WeatherType.CLEAR],
        "rain": [WeatherType.LIGHT_RAIN, WeatherType.HEAVY_RAIN],
        "fog": [WeatherType.FOG, WeatherType.MIST],
        "storm": [WeatherType.STORM],
        "heat": [WeatherType.CLEAR],  # no dedicated type — bias clear
        "cold": [WeatherType.SNOW, WeatherType.OVERCAST],
    }

    def apply_theme_weights(self, theme_weights: dict[str, float]) -> None:
        """Bias transition probabilities toward the theme's preferred weather.

        ``theme_weights`` comes from ``ThemeConfig.weather_weights`` and maps
        category names (e.g. "rain", "fog") to desired prevalence (0-1).
        We scale existing transition probabilities so that weather types
        belonging to more-prevalent categories become more likely targets.
        """
        # Build per-WeatherType multiplier from the theme weights
        type_multiplier: dict[WeatherType, float] = {}
        for category, weight in theme_weights.items():
            for wt in self._THEME_KEY_MAP.get(category, []):
                type_multiplier[wt] = type_multiplier.get(wt, 0.0) + weight

        if not type_multiplier:
            return

        # Scale each transition row so theme-preferred targets are boosted
        for source, targets in self._transition_weights.items():
            for target in targets:
                if target in type_multiplier:
                    targets[target] *= 1.0 + type_multiplier[target]

            # Re-normalize so row sums to ~1
            total = sum(targets.values())
            if total > 0:
                for target in targets:
                    targets[target] /= total

    def _select_next_weather(self) -> WeatherType:
        """Select next weather based on transition probabilities."""
        current = self.current_state.weather_type
        weights = self._transition_weights.get(current, {WeatherType.CLEAR: 1.0})

        choices = list(weights.keys())
        probs = list(weights.values())

        return self._rng.choices(choices, weights=probs, k=1)[0]

    def set_weather(
        self,
        weather_type: WeatherType,
        intensity: float = 1.0,
        duration: int = 60,
        immediate: bool = False
    ) -> None:
        """
        Manually set weather.

        Args:
            weather_type: The weather to set
            intensity: Weather intensity (0.0 to 1.0)
            duration: How long before natural transition
            immediate: If True, skip transition
        """
        if immediate:
            self.current_state = WeatherState(
                weather_type=weather_type,
                intensity=intensity,
                duration_remaining=duration,
            )
            self.history.append((self.current_time, weather_type))
        else:
            self.current_state.transitioning_to = weather_type
            self.current_state.transition_progress = 0.0

    def get_effect(self) -> WeatherEffect:
        """Get current weather effect."""
        return self.current_state.get_effect()

    def get_description(self, is_indoor: bool = False) -> str:
        """Get weather description."""
        return self.current_state.get_description(is_indoor)

    def get_visibility(self) -> float:
        """Get current visibility modifier."""
        return self.get_effect().visibility

    def is_outdoor_dangerous(self) -> bool:
        """Check if weather makes outdoor activity dangerous."""
        return self.current_state.weather_type in (
            WeatherType.STORM,
            WeatherType.HEAVY_RAIN,
        )

    def to_dict(self) -> dict:
        """Serialize weather state."""
        return {
            "current_state": {
                "weather_type": self.current_state.weather_type.name,
                "intensity": self.current_state.intensity,
                "duration_remaining": self.current_state.duration_remaining,
                "transitioning_to": (
                    self.current_state.transitioning_to.name
                    if self.current_state.transitioning_to else None
                ),
                "transition_progress": self.current_state.transition_progress,
            },
            "seed": self.seed,
            "history": [
                (t, w.name if isinstance(w, WeatherType) else w)
                for t, w in self.history
            ],
            "current_time": self.current_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WeatherSystem":
        """Deserialize weather state."""
        state_data = data["current_state"]

        transitioning = None
        if state_data.get("transitioning_to"):
            transitioning = WeatherType[state_data["transitioning_to"]]

        state = WeatherState(
            weather_type=WeatherType[state_data["weather_type"]],
            intensity=state_data.get("intensity", 1.0),
            duration_remaining=state_data.get("duration_remaining", 60),
            transitioning_to=transitioning,
            transition_progress=state_data.get("transition_progress", 0.0),
        )

        system = cls(
            current_state=state,
            seed=data.get("seed"),
            current_time=data.get("current_time", 0),
        )

        system.history = [
            (t, WeatherType[w] if isinstance(w, str) else w)
            for t, w in data.get("history", [])
        ]

        return system
