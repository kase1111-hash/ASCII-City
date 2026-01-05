"""
Atmosphere System - Tension-based visual rendering.

Provides:
- Tension level visualization
- Mood-based rendering adjustments
- Dynamic atmosphere effects
- Visual urgency indicators
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum, auto


class Mood(Enum):
    """Overall mood for atmosphere rendering."""
    NEUTRAL = auto()
    CALM = auto()
    TENSE = auto()
    DANGEROUS = auto()
    MYSTERIOUS = auto()
    HOPEFUL = auto()
    DREAD = auto()
    URGENT = auto()


@dataclass
class AtmosphereConfig:
    """Configuration for mood-based atmosphere."""
    border_char: str = '│'
    corner_chars: tuple[str, str, str, str] = ('┌', '┐', '└', '┘')
    horizontal_char: str = '─'
    pulse_enabled: bool = False
    pulse_rate: float = 1.0
    dim_background: bool = False
    highlight_interactables: bool = True
    shake_intensity: float = 0.0
    flicker_rate: float = 0.0


# Mood-specific configurations
MOOD_CONFIGS: dict[Mood, AtmosphereConfig] = {
    Mood.NEUTRAL: AtmosphereConfig(),
    Mood.CALM: AtmosphereConfig(
        border_char='│',
        dim_background=False,
        highlight_interactables=True
    ),
    Mood.TENSE: AtmosphereConfig(
        border_char='║',
        corner_chars=('╔', '╗', '╚', '╝'),
        horizontal_char='═',
        pulse_enabled=True,
        pulse_rate=0.5
    ),
    Mood.DANGEROUS: AtmosphereConfig(
        border_char='┃',
        corner_chars=('┏', '┓', '┗', '┛'),
        horizontal_char='━',
        pulse_enabled=True,
        pulse_rate=2.0,
        shake_intensity=0.3,
        flicker_rate=0.1
    ),
    Mood.MYSTERIOUS: AtmosphereConfig(
        border_char='░',
        corner_chars=('░', '░', '░', '░'),
        horizontal_char='░',
        dim_background=True
    ),
    Mood.HOPEFUL: AtmosphereConfig(
        border_char='│',
        highlight_interactables=True
    ),
    Mood.DREAD: AtmosphereConfig(
        border_char='▓',
        corner_chars=('▓', '▓', '▓', '▓'),
        horizontal_char='▓',
        dim_background=True,
        pulse_enabled=True,
        pulse_rate=0.3,
        flicker_rate=0.05
    ),
    Mood.URGENT: AtmosphereConfig(
        border_char='!',
        corner_chars=('!', '!', '!', '!'),
        horizontal_char='!',
        pulse_enabled=True,
        pulse_rate=3.0,
        shake_intensity=0.5
    )
}


@dataclass
class TensionMeter:
    """
    Tracks and visualizes tension level.

    Tension affects visual rendering and atmosphere.
    """

    current: float = 0.0  # 0.0 to 1.0
    target: float = 0.0
    decay_rate: float = 0.01
    build_rate: float = 0.05
    max_tension: float = 1.0
    min_tension: float = 0.0

    # Thresholds for mood changes
    tense_threshold: float = 0.3
    dangerous_threshold: float = 0.6
    critical_threshold: float = 0.85

    def add_tension(self, amount: float) -> None:
        """Add tension (will build toward target)."""
        self.target = min(self.max_tension, self.target + amount)

    def reduce_tension(self, amount: float) -> None:
        """Reduce tension target."""
        self.target = max(self.min_tension, self.target - amount)

    def set_tension(self, value: float) -> None:
        """Set tension to specific value immediately."""
        self.current = max(self.min_tension, min(self.max_tension, value))
        self.target = self.current

    def update(self) -> None:
        """Update tension toward target with appropriate rate."""
        if self.current < self.target:
            self.current = min(
                self.target,
                self.current + self.build_rate
            )
        elif self.current > self.target:
            self.current = max(
                self.target,
                self.current - self.decay_rate
            )

    def get_level(self) -> str:
        """Get tension level as string."""
        if self.current >= self.critical_threshold:
            return "critical"
        elif self.current >= self.dangerous_threshold:
            return "dangerous"
        elif self.current >= self.tense_threshold:
            return "tense"
        else:
            return "calm"

    def get_mood(self) -> Mood:
        """Get appropriate mood for current tension."""
        if self.current >= self.critical_threshold:
            return Mood.URGENT
        elif self.current >= self.dangerous_threshold:
            return Mood.DANGEROUS
        elif self.current >= self.tense_threshold:
            return Mood.TENSE
        else:
            return Mood.CALM

    def get_visual_bar(self, width: int = 20) -> str:
        """Get ASCII visual representation of tension."""
        filled = int(self.current * width)
        empty = width - filled

        # Different fill characters based on level
        if self.current >= self.critical_threshold:
            fill_char = '█'
        elif self.current >= self.dangerous_threshold:
            fill_char = '▓'
        elif self.current >= self.tense_threshold:
            fill_char = '▒'
        else:
            fill_char = '░'

        return f"[{fill_char * filled}{'·' * empty}]"


@dataclass
class AtmosphereManager:
    """
    Manages atmosphere and tension-based rendering.

    Coordinates mood, tension, and visual effects.
    """

    tension: TensionMeter = field(default_factory=TensionMeter)
    current_mood: Mood = Mood.NEUTRAL
    override_mood: Optional[Mood] = None
    config: AtmosphereConfig = field(default_factory=AtmosphereConfig)

    # Animation state
    _tick: int = 0
    _pulse_phase: float = 0.0

    def update(self) -> None:
        """Update atmosphere state."""
        self.tension.update()
        self._tick += 1

        # Update mood based on tension (unless overridden)
        if self.override_mood is None:
            self.current_mood = self.tension.get_mood()

        # Update config for current mood
        self.config = MOOD_CONFIGS.get(self.current_mood, AtmosphereConfig())

        # Update pulse phase
        if self.config.pulse_enabled:
            self._pulse_phase += self.config.pulse_rate * 0.1
            if self._pulse_phase >= 1.0:
                self._pulse_phase -= 1.0

    def set_mood(self, mood: Mood) -> None:
        """Set mood override."""
        self.override_mood = mood
        self.current_mood = mood
        self.config = MOOD_CONFIGS.get(mood, AtmosphereConfig())

    def clear_mood_override(self) -> None:
        """Clear mood override, return to tension-based mood."""
        self.override_mood = None

    def get_border_chars(self) -> dict[str, str]:
        """Get border characters for current atmosphere."""
        return {
            'vertical': self.config.border_char,
            'horizontal': self.config.horizontal_char,
            'top_left': self.config.corner_chars[0],
            'top_right': self.config.corner_chars[1],
            'bottom_left': self.config.corner_chars[2],
            'bottom_right': self.config.corner_chars[3]
        }

    def should_pulse(self) -> bool:
        """Check if pulsing effect should be visible this tick."""
        if not self.config.pulse_enabled:
            return False
        return self._pulse_phase < 0.5

    def should_flicker(self) -> bool:
        """Check if flicker effect should occur this tick."""
        if self.config.flicker_rate <= 0:
            return False
        import random
        return random.random() < self.config.flicker_rate

    def get_shake_offset(self) -> tuple[int, int]:
        """Get screen shake offset for current tick."""
        if self.config.shake_intensity <= 0:
            return (0, 0)

        import random
        intensity = self.config.shake_intensity
        return (
            int(random.uniform(-intensity, intensity)),
            int(random.uniform(-intensity, intensity))
        )

    def get_tension_indicator(self) -> str:
        """Get tension level indicator for UI."""
        level = self.tension.get_level()
        indicators = {
            'calm': '○',
            'tense': '◐',
            'dangerous': '◕',
            'critical': '●'
        }
        return indicators.get(level, '○')

    def trigger_tension_spike(self, amount: float = 0.3) -> None:
        """Trigger a sudden tension spike."""
        self.tension.add_tension(amount)

    def trigger_relief(self, amount: float = 0.2) -> None:
        """Trigger tension relief."""
        self.tension.reduce_tension(amount)

    def get_atmosphere_description(self) -> str:
        """Get narrative description of current atmosphere."""
        descriptions = {
            Mood.NEUTRAL: "The air is still.",
            Mood.CALM: "A sense of peace settles over the scene.",
            Mood.TENSE: "An uneasy feeling hangs in the air.",
            Mood.DANGEROUS: "Danger lurks in every shadow.",
            Mood.MYSTERIOUS: "Something strange permeates the atmosphere.",
            Mood.HOPEFUL: "A glimmer of hope pierces the darkness.",
            Mood.DREAD: "An oppressive dread weighs heavily.",
            Mood.URGENT: "Every second counts!"
        }
        return descriptions.get(self.current_mood, "")

    def to_dict(self) -> dict:
        """Serialize atmosphere state."""
        return {
            'tension_current': self.tension.current,
            'tension_target': self.tension.target,
            'mood': self.current_mood.name if self.current_mood else None,
            'override_mood': self.override_mood.name if self.override_mood else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AtmosphereManager":
        """Deserialize atmosphere state."""
        manager = cls()
        manager.tension.current = data.get('tension_current', 0.0)
        manager.tension.target = data.get('tension_target', 0.0)

        if data.get('mood'):
            manager.current_mood = Mood[data['mood']]
        if data.get('override_mood'):
            manager.override_mood = Mood[data['override_mood']]
            manager.set_mood(manager.override_mood)

        return manager


# Tension triggers for common game events
TENSION_TRIGGERS: dict[str, float] = {
    'discovered_body': 0.4,
    'caught_lying': 0.2,
    'found_evidence': 0.15,
    'confrontation': 0.25,
    'time_pressure': 0.1,
    'near_culprit': 0.3,
    'accusation_wrong': 0.2,
    'accusation_right': -0.3,
    'npc_hostile': 0.15,
    'clue_connection': 0.1,
    'safe_location': -0.15,
    'ally_support': -0.1,
    'mystery_deepens': 0.2
}


def get_tension_for_event(event: str) -> float:
    """Get tension change for a game event."""
    return TENSION_TRIGGERS.get(event, 0.0)
