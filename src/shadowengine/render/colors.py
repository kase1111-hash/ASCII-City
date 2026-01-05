"""
ANSI Color System - Terminal color support for atmosphere.

Provides:
- ANSI escape code generation
- Color themes for different moods/times
- Graceful fallback for unsupported terminals
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
import os
import sys


class ColorSupport(Enum):
    """Level of color support available."""
    NONE = auto()       # No color support
    BASIC = auto()      # 8 colors
    EXTENDED = auto()   # 256 colors
    TRUECOLOR = auto()  # 24-bit RGB


@dataclass
class Color:
    """An ANSI color value."""
    r: int = 255
    g: int = 255
    b: int = 255

    @classmethod
    def from_hex(cls, hex_code: str) -> "Color":
        """Create color from hex code (#RRGGBB)."""
        hex_code = hex_code.lstrip("#")
        return cls(
            r=int(hex_code[0:2], 16),
            g=int(hex_code[2:4], 16),
            b=int(hex_code[4:6], 16)
        )

    def to_ansi_fg(self) -> str:
        """Get ANSI escape sequence for foreground."""
        return f"\033[38;2;{self.r};{self.g};{self.b}m"

    def to_ansi_bg(self) -> str:
        """Get ANSI escape sequence for background."""
        return f"\033[48;2;{self.r};{self.g};{self.b}m"


# Standard ANSI colors
class ANSI:
    """ANSI escape codes."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    # Basic foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


@dataclass
class ColorTheme:
    """A color theme for rendering."""
    name: str

    # Text colors
    text: str = ANSI.WHITE
    text_dim: str = ANSI.BRIGHT_BLACK
    text_emphasis: str = ANSI.BRIGHT_WHITE

    # Dialogue colors
    dialogue: str = ANSI.CYAN
    dialogue_speaker: str = ANSI.BRIGHT_CYAN

    # Narration colors
    narration: str = ANSI.BRIGHT_BLACK
    narration_emphasis: str = ANSI.WHITE

    # UI colors
    ui_border: str = ANSI.BRIGHT_BLACK
    ui_highlight: str = ANSI.YELLOW
    ui_error: str = ANSI.RED
    ui_success: str = ANSI.GREEN

    # Atmosphere colors
    atmosphere: str = ANSI.BLUE
    tension_low: str = ANSI.GREEN
    tension_medium: str = ANSI.YELLOW
    tension_high: str = ANSI.RED

    # Scene element colors
    person: str = ANSI.BRIGHT_YELLOW
    item: str = ANSI.GREEN
    evidence: str = ANSI.BRIGHT_MAGENTA
    exit: str = ANSI.CYAN
    object: str = ANSI.WHITE


# Predefined themes
THEMES = {
    "noir": ColorTheme(
        name="noir",
        text=ANSI.WHITE,
        text_dim=ANSI.BRIGHT_BLACK,
        dialogue=ANSI.BRIGHT_WHITE,
        narration=ANSI.BRIGHT_BLACK,
        atmosphere=ANSI.BLUE,
    ),
    "horror": ColorTheme(
        name="horror",
        text=ANSI.WHITE,
        text_dim=ANSI.BRIGHT_BLACK,
        dialogue=ANSI.BRIGHT_RED,
        narration=ANSI.RED,
        atmosphere=ANSI.MAGENTA,
        tension_high=ANSI.BRIGHT_RED,
    ),
    "mystery": ColorTheme(
        name="mystery",
        text=ANSI.WHITE,
        text_dim=ANSI.BRIGHT_BLACK,
        dialogue=ANSI.CYAN,
        narration=ANSI.BRIGHT_CYAN,
        atmosphere=ANSI.BLUE,
        evidence=ANSI.YELLOW,
    ),
    "default": ColorTheme(name="default"),
}


class ColorManager:
    """
    Manages color output for the renderer.

    Detects terminal capabilities and provides
    appropriate color codes.
    """

    def __init__(self, force_color: bool = False, force_no_color: bool = False):
        self.force_color = force_color
        self.force_no_color = force_no_color
        self.theme: ColorTheme = THEMES["default"]
        self._support = self._detect_support()
        self._enabled = self._support != ColorSupport.NONE

    def _detect_support(self) -> ColorSupport:
        """Detect terminal color support level."""
        if self.force_no_color:
            return ColorSupport.NONE

        if self.force_color:
            return ColorSupport.TRUECOLOR

        # Check for NO_COLOR environment variable
        if os.environ.get("NO_COLOR"):
            return ColorSupport.NONE

        # Check if stdout is a terminal
        if not sys.stdout.isatty():
            return ColorSupport.NONE

        # Check COLORTERM for truecolor support
        colorterm = os.environ.get("COLORTERM", "")
        if colorterm in ("truecolor", "24bit"):
            return ColorSupport.TRUECOLOR

        # Check TERM for color support
        term = os.environ.get("TERM", "")
        if "256color" in term:
            return ColorSupport.EXTENDED
        if term in ("xterm", "screen", "vt100", "linux"):
            return ColorSupport.BASIC

        # Default to basic if on a known platform
        if sys.platform != "win32" or os.environ.get("ANSICON"):
            return ColorSupport.BASIC

        return ColorSupport.NONE

    @property
    def enabled(self) -> bool:
        """Check if colors are enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable color output."""
        self._enabled = True

    def disable(self) -> None:
        """Disable color output."""
        self._enabled = False

    def set_theme(self, theme_name: str) -> bool:
        """Set the color theme."""
        if theme_name in THEMES:
            self.theme = THEMES[theme_name]
            return True
        return False

    def colorize(self, text: str, color: str) -> str:
        """Apply color to text."""
        if not self._enabled:
            return text
        return f"{color}{text}{ANSI.RESET}"

    def bold(self, text: str) -> str:
        """Make text bold."""
        if not self._enabled:
            return text
        return f"{ANSI.BOLD}{text}{ANSI.RESET}"

    def dim(self, text: str) -> str:
        """Make text dim."""
        if not self._enabled:
            return text
        return f"{ANSI.DIM}{text}{ANSI.RESET}"

    def italic(self, text: str) -> str:
        """Make text italic."""
        if not self._enabled:
            return text
        return f"{ANSI.ITALIC}{text}{ANSI.RESET}"

    # Themed color methods
    def text(self, text: str) -> str:
        """Regular text color."""
        return self.colorize(text, self.theme.text)

    def dialogue(self, text: str) -> str:
        """Dialogue text color."""
        return self.colorize(text, self.theme.dialogue)

    def speaker(self, text: str) -> str:
        """Speaker name color."""
        return self.colorize(text, self.theme.dialogue_speaker)

    def narration(self, text: str) -> str:
        """Narration text color."""
        return self.colorize(text, self.theme.narration)

    def error(self, text: str) -> str:
        """Error text color."""
        return self.colorize(text, self.theme.ui_error)

    def success(self, text: str) -> str:
        """Success text color."""
        return self.colorize(text, self.theme.ui_success)

    def highlight(self, text: str) -> str:
        """Highlighted text color."""
        return self.colorize(text, self.theme.ui_highlight)

    def border(self, text: str) -> str:
        """Border/frame color."""
        return self.colorize(text, self.theme.ui_border)

    def tension(self, text: str, level: float) -> str:
        """Color based on tension level (0.0 to 1.0)."""
        if level < 0.33:
            color = self.theme.tension_low
        elif level < 0.66:
            color = self.theme.tension_medium
        else:
            color = self.theme.tension_high
        return self.colorize(text, color)

    def hotspot(self, text: str, hotspot_type: str) -> str:
        """Color based on hotspot type."""
        type_colors = {
            "person": self.theme.person,
            "item": self.theme.item,
            "evidence": self.theme.evidence,
            "exit": self.theme.exit,
            "object": self.theme.object,
        }
        color = type_colors.get(hotspot_type, self.theme.text)
        return self.colorize(text, color)

    def atmosphere(self, text: str) -> str:
        """Atmospheric text color."""
        return self.colorize(text, self.theme.atmosphere)

    def rgb(self, text: str, r: int, g: int, b: int) -> str:
        """Apply RGB color (requires truecolor support)."""
        if not self._enabled or self._support != ColorSupport.TRUECOLOR:
            return text
        return f"\033[38;2;{r};{g};{b}m{text}{ANSI.RESET}"
