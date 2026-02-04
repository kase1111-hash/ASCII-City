"""
Game configuration and constants.
"""

from dataclasses import dataclass, field
from typing import Optional
import json
import os
import shutil


# =============================================================================
# Game Constants
# =============================================================================

# Time constants (in minutes)
WAIT_TIME_MINUTES = 15  # Time passed when player waits
TRAVEL_TIME_MULTIPLIER = 2  # Travel takes longer than normal actions

# Pressure/Trust constants
THREATEN_PRESSURE_AMOUNT = 20
THREATEN_TRUST_PENALTY = -10
ACCUSE_PRESSURE_AMOUNT = 30
ACCUSE_WRONG_TRUST_PENALTY = -20

# Moral action weights
THREATEN_MORAL_WEIGHT = 0.8
THREATEN_RUTHLESS_EFFECT = 0.3
THREATEN_COMPASSIONATE_EFFECT = -0.2
THREATEN_IDEALISTIC_EFFECT = -0.1

# Memory/History limits
MAX_DIALOGUE_HISTORY_PER_NPC = 50
MAX_LOCATION_DETAILS_HISTORY = 100
MAX_REVEALED_CLUES_HISTORY = 200
MAX_GENERATED_LORE_HISTORY = 100

# LLM context limits
MAX_LOCATIONS_IN_CONTEXT = 10
MAX_NPCS_IN_CONTEXT = 8
MAX_RECENT_EVENTS_IN_CONTEXT = 5
MAX_PUBLIC_FACTS_IN_CONTEXT = 5
MAX_ACTIVE_THREADS_IN_CONTEXT = 3

# Narrative adaptation thresholds
NARRATIVE_WEAK_CONNECTION_DISTANCE = 5
NARRATIVE_NO_CONNECTION_DISTANCE = 10


def get_terminal_size() -> tuple[int, int]:
    """Get the current terminal size, with fallback defaults."""
    try:
        size = shutil.get_terminal_size(fallback=(120, 40))
        # Ensure minimum usable size
        width = max(size.columns, 80)
        height = max(size.lines, 24)
        return width, height
    except Exception:
        return 120, 40


# Get terminal size at module load time
_TERMINAL_WIDTH, _TERMINAL_HEIGHT = get_terminal_size()


@dataclass
class GameConfig:
    """Main game configuration."""

    # Display - defaults to full terminal size
    screen_width: int = _TERMINAL_WIDTH
    screen_height: int = _TERMINAL_HEIGHT

    # Game settings
    seed: Optional[int] = None  # None = random seed
    auto_save: bool = True
    save_dir: str = "saves"

    # Debug
    debug_mode: bool = False
    show_world_memory: bool = False  # Reveal objective truth (cheating)

    # Timing
    time_passes_on_action: bool = True
    time_units_per_action: int = 1

    # Difficulty
    npc_trust_threshold_modifier: float = 1.0  # Higher = harder to crack NPCs
    evidence_decay_rate: float = 0.1  # How fast outdoor evidence degrades

    # Audio settings
    enable_audio: bool = True  # Enable audio engine
    enable_speech: bool = True  # Enable TTS for dialogue
    master_volume: float = 0.8
    speech_volume: float = 1.0
    ambient_volume: float = 0.5

    def save(self, path: str) -> None:
        """Save config to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'GameConfig':
        """Load config from JSON file."""
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                return cls(**data)
        return cls()


@dataclass
class ThemeConfig:
    """Theme-specific configuration (genre pack)."""

    name: str = "default"
    description: str = "Default theme"

    # Atmosphere
    weather_weights: dict = field(default_factory=lambda: {
        "clear": 0.4,
        "rain": 0.25,
        "fog": 0.15,
        "storm": 0.1,
        "heat": 0.05,
        "cold": 0.05
    })

    # Time periods
    time_periods: dict = field(default_factory=lambda: {
        "dawn": (5, 7),
        "morning": (7, 12),
        "afternoon": (12, 17),
        "evening": (17, 20),
        "night": (20, 23),
        "late_night": (23, 5)
    })

    # Vocabulary
    examine_verbs: list = field(default_factory=lambda: [
        "examine", "look", "check", "inspect", "see", "view", "read", "study"
    ])
    talk_verbs: list = field(default_factory=lambda: [
        "talk", "speak", "ask", "question", "interview", "chat", "converse"
    ])
    take_verbs: list = field(default_factory=lambda: [
        "take", "get", "grab", "pick", "collect", "acquire"
    ])
    use_verbs: list = field(default_factory=lambda: [
        "use", "apply", "put", "insert", "combine"
    ])
    go_verbs: list = field(default_factory=lambda: [
        "go", "walk", "move", "enter", "exit", "leave", "head"
    ])


# Default instances
DEFAULT_CONFIG = GameConfig()
DEFAULT_THEME = ThemeConfig()
