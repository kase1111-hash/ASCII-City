"""
Environment Coordinator - Combines time and weather systems.

Provides unified environmental state for the game:
- Synchronized time and weather updates
- Location-specific environmental conditions
- Environmental effects on gameplay systems
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Any

from .time import TimeSystem, TimePeriod, TimeEvent
from .weather import WeatherSystem, WeatherType, WeatherEffect


@dataclass
class LocationEnvironment:
    """Environment state for a specific location."""

    location_id: str
    is_indoor: bool = True

    # Location-specific overrides
    has_lighting: bool = True  # Artificial lighting negates darkness
    has_shelter: bool = True   # Protected from weather effects
    temperature_modifier: float = 0.0  # Relative to outdoor temp

    # Special conditions
    is_noisy: bool = False  # Machinery, crowds, etc.
    is_dark: bool = False   # Basement, no windows, etc.

    def get_visibility(
        self,
        time: TimeSystem,
        weather: WeatherSystem
    ) -> float:
        """Calculate visibility for this location."""
        base_visibility = 1.0

        # Time effects (only if no lighting)
        if not self.has_lighting or self.is_dark:
            base_visibility *= time.current_period.get_visibility_modifier()

        # Weather effects (only if outdoor/exposed)
        if not self.has_shelter:
            base_visibility *= weather.get_visibility()

        # Permanent darkness
        if self.is_dark and not self.has_lighting:
            base_visibility *= 0.3

        return max(0.1, min(1.0, base_visibility))

    def get_ambient_noise(self, weather: WeatherSystem) -> float:
        """Calculate ambient noise level."""
        base_noise = 1.0

        if self.is_noisy:
            base_noise = 1.5

        # Weather noise (reduced if indoors)
        weather_noise = weather.get_effect().ambient_noise
        if self.is_indoor:
            weather_noise = 1.0 + (weather_noise - 1.0) * 0.3

        return base_noise * weather_noise

    def get_description_modifiers(
        self,
        time: TimeSystem,
        weather: WeatherSystem
    ) -> list[str]:
        """Get environmental description modifiers."""
        modifiers = []

        # Time-based
        if not self.has_lighting:
            if time.is_dark():
                modifiers.append("It's dark in here.")

        # Weather-based
        if self.is_indoor:
            desc = weather.get_description(is_indoor=True)
            if desc:
                modifiers.append(desc)
        else:
            desc = weather.get_description(is_indoor=False)
            if desc:
                modifiers.append(desc)

        # Special conditions
        if self.is_noisy:
            modifiers.append("Background noise makes it hard to hear clearly.")

        return modifiers


@dataclass
class Environment:
    """
    Master environment coordinator.

    Manages time and weather systems together,
    providing a unified interface for environmental effects.
    """

    time: TimeSystem = field(default_factory=TimeSystem)
    weather: WeatherSystem = field(default_factory=WeatherSystem)

    # Location-specific environments
    locations: dict[str, LocationEnvironment] = field(default_factory=dict)

    # Event callbacks
    _update_callbacks: list[Callable[[int], None]] = field(
        default_factory=list, repr=False
    )

    def __post_init__(self):
        """Synchronize systems."""
        # Sync time to weather system
        self.weather.current_time = self.time.current_minutes

    def set_seed(self, seed: int) -> None:
        """Set seed for deterministic environmental generation."""
        self.weather.set_seed(seed)

    def update(self, minutes: int) -> dict[str, Any]:
        """
        Update all environmental systems.

        Returns dict of what changed:
        {
            "time_events": [...],
            "weather_changed": WeatherType or None,
            "period_changed": TimePeriod or None,
        }
        """
        old_period = self.time.current_period

        # Update time
        time_events = self.time.advance(minutes)

        # Sync and update weather
        self.weather.current_time = self.time.current_minutes
        weather_changed = self.weather.update(minutes)

        # Check for period change
        new_period = self.time.current_period
        period_changed = new_period if new_period != old_period else None

        # Notify callbacks
        for callback in self._update_callbacks:
            callback(minutes)

        return {
            "time_events": time_events,
            "weather_changed": weather_changed,
            "period_changed": period_changed,
        }

    def advance_to_time(self, hour: int, minute: int = 0) -> dict[str, Any]:
        """Advance to specific time, collecting all changes."""
        target_minutes = hour * 60 + minute
        current_day_minutes = self.time.current_minutes % 1440

        if target_minutes <= current_day_minutes:
            target_minutes += 1440

        minutes_to_advance = target_minutes - current_day_minutes
        return self.update(minutes_to_advance)

    def register_location(
        self,
        location_id: str,
        is_indoor: bool = True,
        **kwargs
    ) -> LocationEnvironment:
        """Register a location for environmental tracking."""
        env = LocationEnvironment(
            location_id=location_id,
            is_indoor=is_indoor,
            **kwargs
        )
        self.locations[location_id] = env
        return env

    def get_location_environment(
        self,
        location_id: str
    ) -> Optional[LocationEnvironment]:
        """Get environment for a location."""
        return self.locations.get(location_id)

    def get_visibility(self, location_id: Optional[str] = None) -> float:
        """Get visibility at a location (or global if no location)."""
        if location_id and location_id in self.locations:
            return self.locations[location_id].get_visibility(
                self.time, self.weather
            )

        # Global visibility (outdoor)
        time_vis = self.time.current_period.get_visibility_modifier()
        weather_vis = self.weather.get_visibility()
        return time_vis * weather_vis

    def get_ambient_noise(self, location_id: Optional[str] = None) -> float:
        """Get ambient noise level at a location."""
        if location_id and location_id in self.locations:
            return self.locations[location_id].get_ambient_noise(self.weather)
        return self.weather.get_effect().ambient_noise

    def get_weather_effect(self) -> WeatherEffect:
        """Get current weather effect."""
        return self.weather.get_effect()

    def get_display_status(self) -> str:
        """Get formatted environment status for display."""
        time_str = self.time.get_display_string()
        weather_name = self.weather.current_state.weather_type.name.replace("_", " ").title()
        return f"{time_str} | {weather_name}"

    def get_atmospheric_description(
        self,
        location_id: Optional[str] = None
    ) -> list[str]:
        """Get atmospheric description lines for current environment."""
        lines = []

        # Time description
        lines.append(self.time.current_period.get_description())

        # Weather description
        is_indoor = True
        if location_id and location_id in self.locations:
            is_indoor = self.locations[location_id].is_indoor
            # Add location-specific modifiers
            modifiers = self.locations[location_id].get_description_modifiers(
                self.time, self.weather
            )
            lines.extend(modifiers)
        else:
            lines.append(self.weather.get_description(is_indoor=is_indoor))

        # Filter empty lines
        return [line for line in lines if line]

    def on_update(self, callback: Callable[[int], None]) -> None:
        """Register callback for environment updates."""
        self._update_callbacks.append(callback)

    def schedule_event(
        self,
        event_id: str,
        hour: int,
        minute: int = 0,
        description: str = "",
        callback: Optional[Callable[[], Any]] = None,
        repeating: bool = False,
    ) -> TimeEvent:
        """Schedule a time-based event."""
        event = TimeEvent(
            id=event_id,
            trigger_hour=hour,
            trigger_minute=minute,
            description=description,
            callback=callback,
            repeating=repeating,
        )
        self.time.add_event(event)
        return event

    def set_weather(
        self,
        weather_type: WeatherType,
        immediate: bool = True,
        **kwargs
    ) -> None:
        """Set weather condition."""
        self.weather.set_weather(weather_type, immediate=immediate, **kwargs)

    def to_dict(self) -> dict:
        """Serialize environment state."""
        return {
            "time": self.time.to_dict(),
            "weather": self.weather.to_dict(),
            "locations": {
                loc_id: {
                    "location_id": env.location_id,
                    "is_indoor": env.is_indoor,
                    "has_lighting": env.has_lighting,
                    "has_shelter": env.has_shelter,
                    "temperature_modifier": env.temperature_modifier,
                    "is_noisy": env.is_noisy,
                    "is_dark": env.is_dark,
                }
                for loc_id, env in self.locations.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Environment":
        """Deserialize environment state."""
        env = cls(
            time=TimeSystem.from_dict(data["time"]),
            weather=WeatherSystem.from_dict(data["weather"]),
        )

        for loc_id, loc_data in data.get("locations", {}).items():
            env.locations[loc_id] = LocationEnvironment(**loc_data)

        return env
