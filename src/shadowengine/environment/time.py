"""
Time System - Day/night cycle and time progression.

Manages game time with:
- Configurable time periods (morning, afternoon, evening, night)
- Time-gated events and triggers
- Time passage effects on gameplay
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable, Any


class TimePeriod(Enum):
    """Time periods of the day."""
    DAWN = auto()       # 5:00 - 7:59
    MORNING = auto()    # 8:00 - 11:59
    AFTERNOON = auto()  # 12:00 - 16:59
    EVENING = auto()    # 17:00 - 20:59
    NIGHT = auto()      # 21:00 - 4:59

    @classmethod
    def from_hour(cls, hour: int) -> "TimePeriod":
        """Get period from hour (0-23)."""
        if 5 <= hour < 8:
            return cls.DAWN
        elif 8 <= hour < 12:
            return cls.MORNING
        elif 12 <= hour < 17:
            return cls.AFTERNOON
        elif 17 <= hour < 21:
            return cls.EVENING
        else:
            return cls.NIGHT

    def get_description(self) -> str:
        """Get atmospheric description for this period."""
        descriptions = {
            TimePeriod.DAWN: "The first light of dawn creeps across the sky.",
            TimePeriod.MORNING: "Morning light streams through the windows.",
            TimePeriod.AFTERNOON: "The afternoon sun casts long shadows.",
            TimePeriod.EVENING: "Evening shadows gather in the corners.",
            TimePeriod.NIGHT: "Darkness presses against the windows.",
        }
        return descriptions.get(self, "")

    def get_visibility_modifier(self) -> float:
        """Get visibility modifier (1.0 = normal, 0.5 = reduced)."""
        modifiers = {
            TimePeriod.DAWN: 0.7,
            TimePeriod.MORNING: 1.0,
            TimePeriod.AFTERNOON: 1.0,
            TimePeriod.EVENING: 0.8,
            TimePeriod.NIGHT: 0.5,
        }
        return modifiers.get(self, 1.0)


@dataclass
class TimeEvent:
    """An event triggered at a specific time."""
    id: str
    trigger_hour: int
    trigger_minute: int = 0
    description: str = ""
    callback: Optional[Callable[[], Any]] = None
    repeating: bool = False
    triggered: bool = False

    def matches_time(self, hour: int, minute: int) -> bool:
        """Check if event should trigger at this time."""
        if self.triggered and not self.repeating:
            return False
        return hour == self.trigger_hour and minute >= self.trigger_minute

    def trigger(self) -> Optional[Any]:
        """Trigger the event."""
        self.triggered = True
        if self.callback:
            return self.callback()
        return None

    def reset(self) -> None:
        """Reset for repeating events."""
        if self.repeating:
            self.triggered = False


@dataclass
class TimeSystem:
    """
    Manages game time progression.

    Time is tracked in game-minutes, with configurable
    real-to-game time ratio.
    """

    # Current time (in game minutes from midnight)
    current_minutes: int = 480  # Default: 8:00 AM

    # Minutes per real second (0 = paused)
    time_scale: float = 1.0

    # Events scheduled to trigger
    events: list[TimeEvent] = field(default_factory=list)

    # History of period changes
    period_history: list[tuple[int, TimePeriod]] = field(default_factory=list)

    # Callbacks for period changes
    _period_callbacks: list[Callable[[TimePeriod, TimePeriod], None]] = field(
        default_factory=list, repr=False
    )

    def __post_init__(self):
        """Initialize with current period recorded."""
        if not self.period_history:
            self.period_history.append((self.current_minutes, self.current_period))

    @property
    def hour(self) -> int:
        """Current hour (0-23)."""
        return (self.current_minutes // 60) % 24

    @property
    def minute(self) -> int:
        """Current minute (0-59)."""
        return self.current_minutes % 60

    @property
    def current_period(self) -> TimePeriod:
        """Get current time period."""
        return TimePeriod.from_hour(self.hour)

    @property
    def day_number(self) -> int:
        """Get current day number (starting from 1)."""
        return (self.current_minutes // 1440) + 1

    def get_time_string(self) -> str:
        """Get formatted time string (HH:MM)."""
        return f"{self.hour:02d}:{self.minute:02d}"

    def get_display_string(self) -> str:
        """Get time with period description."""
        period_names = {
            TimePeriod.DAWN: "Dawn",
            TimePeriod.MORNING: "Morning",
            TimePeriod.AFTERNOON: "Afternoon",
            TimePeriod.EVENING: "Evening",
            TimePeriod.NIGHT: "Night",
        }
        return f"{self.get_time_string()} ({period_names[self.current_period]})"

    def advance(self, minutes: int) -> list[TimeEvent]:
        """
        Advance time by specified minutes.

        Returns list of triggered events.
        """
        old_period = self.current_period
        triggered_events = []

        # Advance minute by minute to catch events
        for _ in range(minutes):
            self.current_minutes += 1

            # Check for triggered events
            for event in self.events:
                if event.matches_time(self.hour, self.minute):
                    event.trigger()
                    triggered_events.append(event)

            # Check for period change
            new_period = self.current_period
            if new_period != old_period:
                self.period_history.append((self.current_minutes, new_period))
                for callback in self._period_callbacks:
                    callback(old_period, new_period)
                old_period = new_period

        # Reset repeating events at day boundary
        if self.minute == 0 and self.hour == 0:
            for event in self.events:
                event.reset()

        return triggered_events

    def advance_to(self, hour: int, minute: int = 0) -> list[TimeEvent]:
        """Advance time to specific hour:minute."""
        target_minutes = hour * 60 + minute

        # If target is earlier, advance to next day
        current_day_minutes = self.current_minutes % 1440
        if target_minutes <= current_day_minutes:
            target_minutes += 1440

        minutes_to_advance = target_minutes - current_day_minutes
        return self.advance(minutes_to_advance)

    def advance_to_period(self, period: TimePeriod) -> list[TimeEvent]:
        """Advance time to the start of a period."""
        period_starts = {
            TimePeriod.DAWN: 5,
            TimePeriod.MORNING: 8,
            TimePeriod.AFTERNOON: 12,
            TimePeriod.EVENING: 17,
            TimePeriod.NIGHT: 21,
        }
        return self.advance_to(period_starts[period])

    def add_event(self, event: TimeEvent) -> None:
        """Schedule a time event."""
        self.events.append(event)

    def remove_event(self, event_id: str) -> bool:
        """Remove a scheduled event."""
        for i, event in enumerate(self.events):
            if event.id == event_id:
                self.events.pop(i)
                return True
        return False

    def on_period_change(
        self, callback: Callable[[TimePeriod, TimePeriod], None]
    ) -> None:
        """Register callback for period changes."""
        self._period_callbacks.append(callback)

    def set_time(self, hour: int, minute: int = 0, day: int = 1) -> None:
        """Set absolute time (mainly for testing/initialization)."""
        self.current_minutes = ((day - 1) * 1440) + (hour * 60) + minute
        self.period_history = [(self.current_minutes, self.current_period)]

    def is_dark(self) -> bool:
        """Check if it's dark (reduced visibility)."""
        return self.current_period in (TimePeriod.NIGHT, TimePeriod.DAWN)

    def to_dict(self) -> dict:
        """Serialize time state."""
        return {
            "current_minutes": self.current_minutes,
            "time_scale": self.time_scale,
            "events": [
                {
                    "id": e.id,
                    "trigger_hour": e.trigger_hour,
                    "trigger_minute": e.trigger_minute,
                    "description": e.description,
                    "repeating": e.repeating,
                    "triggered": e.triggered,
                }
                for e in self.events
            ],
            "period_history": self.period_history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TimeSystem":
        """Deserialize time state."""
        system = cls(
            current_minutes=data["current_minutes"],
            time_scale=data.get("time_scale", 1.0),
        )

        system.events = [
            TimeEvent(
                id=e["id"],
                trigger_hour=e["trigger_hour"],
                trigger_minute=e.get("trigger_minute", 0),
                description=e.get("description", ""),
                repeating=e.get("repeating", False),
                triggered=e.get("triggered", False),
            )
            for e in data.get("events", [])
        ]

        system.period_history = [
            (m, TimePeriod[p] if isinstance(p, str) else p)
            for m, p in data.get("period_history", [])
        ]

        return system
