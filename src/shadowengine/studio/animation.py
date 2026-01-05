"""
Animation system for ASCII art.
"""

from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import time


class AnimationTrigger(Enum):
    """When animation should play."""
    ALWAYS = auto()        # Continuous loop
    ON_IDLE = auto()       # When entity is idle
    ON_MOVE = auto()       # When entity moves
    ON_ACTION = auto()     # When action is performed
    ON_INTERACT = auto()   # When player interacts
    ON_DAMAGE = auto()     # When damaged
    ON_STATE = auto()      # When in specific state
    ON_WEATHER = auto()    # Weather-triggered (rain, wind)
    ON_TIME = auto()       # Time-triggered (day/night)
    MANUAL = auto()        # Manually triggered only


@dataclass
class AnimationFrame:
    """
    Single frame of an animation.

    Attributes:
        tiles: ASCII art for this frame
        duration: How long this frame shows (seconds)
        offset: Position offset from base (x, y)
        sound: Optional sound effect name
    """
    tiles: List[List[str]]
    duration: float = 0.2
    offset: Tuple[int, int] = (0, 0)
    sound: Optional[str] = None

    @property
    def width(self) -> int:
        """Frame width."""
        return max(len(row) for row in self.tiles) if self.tiles else 0

    @property
    def height(self) -> int:
        """Frame height."""
        return len(self.tiles)

    def render(self) -> str:
        """Render frame as string."""
        return "\n".join("".join(row) for row in self.tiles)

    def to_dict(self) -> dict:
        """Serialize frame to dictionary."""
        return {
            "tiles": self.tiles,
            "duration": self.duration,
            "offset": self.offset,
            "sound": self.sound
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AnimationFrame":
        """Create frame from dictionary."""
        return cls(
            tiles=data["tiles"],
            duration=data.get("duration", 0.2),
            offset=tuple(data.get("offset", (0, 0))),
            sound=data.get("sound")
        )

    @classmethod
    def from_string(cls, art_string: str, duration: float = 0.2) -> "AnimationFrame":
        """Create frame from multi-line string."""
        tiles = [list(line) for line in art_string.split("\n")]
        return cls(tiles=tiles, duration=duration)


@dataclass
class Animation:
    """
    Frame-based ASCII animation.

    Attributes:
        name: Animation identifier (idle, walk, attack, etc.)
        frames: List of animation frames
        duration: Total animation time (auto-calculated if not set)
        loop: Whether animation repeats
        trigger: When to play animation
        state_condition: State name that triggers (for ON_STATE)
    """
    name: str
    frames: List[AnimationFrame]
    loop: bool = True
    trigger: AnimationTrigger = AnimationTrigger.ALWAYS
    state_condition: Optional[str] = None

    def __post_init__(self):
        """Validate animation."""
        if not self.frames:
            raise ValueError("Animation must have at least one frame")

    @property
    def duration(self) -> float:
        """Total animation duration."""
        return sum(frame.duration for frame in self.frames)

    @property
    def frame_count(self) -> int:
        """Number of frames."""
        return len(self.frames)

    def get_frame_at_time(self, elapsed_time: float) -> AnimationFrame:
        """Get frame for given elapsed time."""
        if not self.frames:
            raise ValueError("No frames in animation")

        if self.loop:
            elapsed_time = elapsed_time % self.duration

        current_time = 0.0
        for frame in self.frames:
            current_time += frame.duration
            if elapsed_time < current_time:
                return frame

        return self.frames[-1]

    def get_frame_index_at_time(self, elapsed_time: float) -> int:
        """Get frame index for given elapsed time."""
        if not self.frames:
            return 0

        if self.loop:
            elapsed_time = elapsed_time % self.duration

        current_time = 0.0
        for i, frame in enumerate(self.frames):
            current_time += frame.duration
            if elapsed_time < current_time:
                return i

        return len(self.frames) - 1

    def should_play(self, current_state: str, event: Optional[str] = None) -> bool:
        """Check if animation should play given state/event."""
        if self.trigger == AnimationTrigger.ALWAYS:
            return True

        if self.trigger == AnimationTrigger.ON_STATE:
            return current_state == self.state_condition

        if self.trigger == AnimationTrigger.ON_IDLE:
            return current_state == "idle"

        if self.trigger == AnimationTrigger.ON_MOVE:
            return current_state in ("moving", "walking", "running")

        if self.trigger == AnimationTrigger.ON_ACTION:
            return event == "action"

        if self.trigger == AnimationTrigger.ON_INTERACT:
            return event == "interact"

        if self.trigger == AnimationTrigger.ON_DAMAGE:
            return event == "damage"

        return False

    def to_dict(self) -> dict:
        """Serialize animation to dictionary."""
        return {
            "name": self.name,
            "frames": [f.to_dict() for f in self.frames],
            "loop": self.loop,
            "trigger": self.trigger.name,
            "state_condition": self.state_condition
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Animation":
        """Create animation from dictionary."""
        return cls(
            name=data["name"],
            frames=[AnimationFrame.from_dict(f) for f in data["frames"]],
            loop=data.get("loop", True),
            trigger=AnimationTrigger[data.get("trigger", "ALWAYS")],
            state_condition=data.get("state_condition")
        )


class AnimationPlayer:
    """Manages animation playback for an entity."""

    def __init__(self):
        self.animations: dict[str, Animation] = {}
        self.current_animation: Optional[str] = None
        self.start_time: float = 0.0
        self.paused: bool = False
        self.pause_time: float = 0.0

    def add_animation(self, animation: Animation) -> None:
        """Add animation to player."""
        self.animations[animation.name] = animation

    def remove_animation(self, name: str) -> bool:
        """Remove animation by name."""
        if name in self.animations:
            del self.animations[name]
            if self.current_animation == name:
                self.current_animation = None
            return True
        return False

    def play(self, name: str) -> bool:
        """Start playing an animation."""
        if name not in self.animations:
            return False

        self.current_animation = name
        self.start_time = time.time()
        self.paused = False
        return True

    def stop(self) -> None:
        """Stop current animation."""
        self.current_animation = None

    def pause(self) -> None:
        """Pause current animation."""
        if not self.paused:
            self.paused = True
            self.pause_time = time.time()

    def resume(self) -> None:
        """Resume paused animation."""
        if self.paused:
            pause_duration = time.time() - self.pause_time
            self.start_time += pause_duration
            self.paused = False

    def get_current_frame(self) -> Optional[AnimationFrame]:
        """Get current animation frame."""
        if not self.current_animation:
            return None

        animation = self.animations.get(self.current_animation)
        if not animation:
            return None

        if self.paused:
            elapsed = self.pause_time - self.start_time
        else:
            elapsed = time.time() - self.start_time

        # Check if non-looping animation finished
        if not animation.loop and elapsed >= animation.duration:
            return animation.frames[-1]

        return animation.get_frame_at_time(elapsed)

    def is_finished(self) -> bool:
        """Check if current animation finished (non-looping only)."""
        if not self.current_animation:
            return True

        animation = self.animations.get(self.current_animation)
        if not animation:
            return True

        if animation.loop:
            return False

        elapsed = time.time() - self.start_time
        return elapsed >= animation.duration

    def update_for_state(self, state: str, event: Optional[str] = None) -> None:
        """Update animation based on state/event."""
        for name, animation in self.animations.items():
            if animation.should_play(state, event):
                if self.current_animation != name:
                    self.play(name)
                return
