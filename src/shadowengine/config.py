"""
Game configuration and constants.
"""

from dataclasses import dataclass, field
from typing import Optional
import json
import os


@dataclass
class GameConfig:
    """Main game configuration."""

    # Display
    screen_width: int = 80
    screen_height: int = 24

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
