"""
Character Schedule System - NPC movement and activity patterns.

Manages where NPCs are at different times:
- Time-based location schedules
- Activity states
- Schedule overrides for events
"""

from dataclasses import dataclass, field
from enum import Enum, auto


class Activity(Enum):
    """What a character is currently doing."""
    IDLE = auto()
    WALKING = auto()
    TALKING = auto()
    WORKING = auto()
    EATING = auto()
    SLEEPING = auto()
    HIDING = auto()
    SEARCHING = auto()
    WAITING = auto()


@dataclass
class ScheduleEntry:
    """A single entry in a character's schedule."""
    start_hour: int
    end_hour: int
    location_id: str
    activity: Activity = Activity.IDLE
    description: str = ""
    interruptible: bool = True

    def matches_time(self, hour: int) -> bool:
        """Check if this entry matches the given hour."""
        if self.start_hour <= self.end_hour:
            return self.start_hour <= hour < self.end_hour
        else:
            # Wraps around midnight
            return hour >= self.start_hour or hour < self.end_hour


@dataclass
class ScheduleOverride:
    """A temporary override to a character's schedule."""
    location_id: str
    activity: Activity
    reason: str
    duration_minutes: int = 30
    elapsed_minutes: int = 0
    priority: int = 1  # Higher priority overrides take precedence

    def is_active(self) -> bool:
        """Check if override is still active."""
        return self.elapsed_minutes < self.duration_minutes

    def update(self, minutes: int) -> bool:
        """Update override, return True if still active."""
        self.elapsed_minutes += minutes
        return self.is_active()


@dataclass
class Schedule:
    """
    A character's daily schedule.

    Defines where the character should be at different times,
    with support for overrides and interruptions.
    """

    character_id: str
    entries: list[ScheduleEntry] = field(default_factory=list)
    overrides: list[ScheduleOverride] = field(default_factory=list)

    # Default location if no schedule entry matches
    default_location: str = ""
    default_activity: Activity = Activity.IDLE

    def add_entry(
        self,
        start_hour: int,
        end_hour: int,
        location_id: str,
        activity: Activity = Activity.IDLE,
        description: str = "",
        interruptible: bool = True
    ) -> None:
        """Add a schedule entry."""
        self.entries.append(ScheduleEntry(
            start_hour=start_hour,
            end_hour=end_hour,
            location_id=location_id,
            activity=activity,
            description=description,
            interruptible=interruptible
        ))

    def add_override(
        self,
        location_id: str,
        activity: Activity,
        reason: str,
        duration_minutes: int = 30,
        priority: int = 1
    ) -> ScheduleOverride:
        """Add a temporary schedule override."""
        override = ScheduleOverride(
            location_id=location_id,
            activity=activity,
            reason=reason,
            duration_minutes=duration_minutes,
            priority=priority
        )
        self.overrides.append(override)
        return override

    def clear_overrides(self) -> None:
        """Clear all overrides."""
        self.overrides.clear()

    def update(self, minutes: int) -> None:
        """Update override timers."""
        # Update and filter expired overrides
        self.overrides = [o for o in self.overrides if o.update(minutes)]

    def get_current_state(self, hour: int) -> tuple[str, Activity]:
        """
        Get current location and activity for given hour.

        Returns (location_id, activity).
        """
        # Check for active overrides (highest priority first)
        active_overrides = [o for o in self.overrides if o.is_active()]
        if active_overrides:
            override = max(active_overrides, key=lambda o: o.priority)
            return override.location_id, override.activity

        # Check schedule entries
        for entry in self.entries:
            if entry.matches_time(hour):
                return entry.location_id, entry.activity

        # Default
        return self.default_location, self.default_activity

    def get_location(self, hour: int) -> str:
        """Get current location for given hour."""
        location, _ = self.get_current_state(hour)
        return location

    def get_activity(self, hour: int) -> Activity:
        """Get current activity for given hour."""
        _, activity = self.get_current_state(hour)
        return activity

    def is_interruptible(self, hour: int) -> bool:
        """Check if character can be interrupted at this time."""
        # Overrides can be interrupted
        active_overrides = [o for o in self.overrides if o.is_active()]
        if active_overrides:
            return True

        # Check schedule entry
        for entry in self.entries:
            if entry.matches_time(hour):
                return entry.interruptible

        return True

    def to_dict(self) -> dict:
        """Serialize schedule."""
        return {
            "character_id": self.character_id,
            "default_location": self.default_location,
            "default_activity": self.default_activity.name,
            "entries": [
                {
                    "start_hour": e.start_hour,
                    "end_hour": e.end_hour,
                    "location_id": e.location_id,
                    "activity": e.activity.name,
                    "description": e.description,
                    "interruptible": e.interruptible
                }
                for e in self.entries
            ],
            "overrides": [
                {
                    "location_id": o.location_id,
                    "activity": o.activity.name,
                    "reason": o.reason,
                    "duration_minutes": o.duration_minutes,
                    "elapsed_minutes": o.elapsed_minutes,
                    "priority": o.priority
                }
                for o in self.overrides
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Schedule":
        """Deserialize schedule."""
        schedule = cls(
            character_id=data["character_id"],
            default_location=data.get("default_location", ""),
            default_activity=Activity[data.get("default_activity", "IDLE")]
        )

        for entry_data in data.get("entries", []):
            schedule.entries.append(ScheduleEntry(
                start_hour=entry_data["start_hour"],
                end_hour=entry_data["end_hour"],
                location_id=entry_data["location_id"],
                activity=Activity[entry_data.get("activity", "IDLE")],
                description=entry_data.get("description", ""),
                interruptible=entry_data.get("interruptible", True)
            ))

        for override_data in data.get("overrides", []):
            schedule.overrides.append(ScheduleOverride(
                location_id=override_data["location_id"],
                activity=Activity[override_data.get("activity", "IDLE")],
                reason=override_data.get("reason", ""),
                duration_minutes=override_data.get("duration_minutes", 30),
                elapsed_minutes=override_data.get("elapsed_minutes", 0),
                priority=override_data.get("priority", 1)
            ))

        return schedule


# Factory functions for common schedule patterns

def create_servant_schedule(character_id: str, quarters: str, work_location: str) -> Schedule:
    """Create a typical servant schedule."""
    schedule = Schedule(character_id=character_id, default_location=quarters)

    # Early morning - quarters
    schedule.add_entry(5, 7, quarters, Activity.IDLE, "Getting ready")

    # Morning - work
    schedule.add_entry(7, 12, work_location, Activity.WORKING, "Morning duties")

    # Lunch - servants' area
    schedule.add_entry(12, 13, quarters, Activity.EATING, "Lunch break")

    # Afternoon - work
    schedule.add_entry(13, 18, work_location, Activity.WORKING, "Afternoon duties")

    # Evening - quarters
    schedule.add_entry(18, 22, quarters, Activity.IDLE, "Evening rest")

    # Night - sleeping
    schedule.add_entry(22, 5, quarters, Activity.SLEEPING, "Sleeping", interruptible=False)

    return schedule


def create_guest_schedule(character_id: str, room: str, common_areas: list[str]) -> Schedule:
    """Create a typical guest schedule."""
    schedule = Schedule(character_id=character_id, default_location=room)

    # Morning - room
    schedule.add_entry(8, 10, room, Activity.IDLE, "Morning routine")

    # Late morning - common area
    if common_areas:
        schedule.add_entry(10, 12, common_areas[0], Activity.IDLE, "Socializing")

    # Lunch
    if len(common_areas) > 1:
        schedule.add_entry(12, 14, common_areas[1], Activity.EATING, "Lunch")
    elif common_areas:
        schedule.add_entry(12, 14, common_areas[0], Activity.EATING, "Lunch")

    # Afternoon - various activities
    if common_areas:
        schedule.add_entry(14, 18, common_areas[0], Activity.IDLE, "Afternoon activities")

    # Evening - common area
    if common_areas:
        schedule.add_entry(18, 22, common_areas[0], Activity.IDLE, "Evening gathering")

    # Night - room
    schedule.add_entry(22, 8, room, Activity.SLEEPING, "Sleeping", interruptible=False)

    return schedule
