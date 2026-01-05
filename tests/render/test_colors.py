"""Tests for the ANSI color system."""

import pytest
from src.shadowengine.render.colors import (
    Color, ColorSupport, ColorTheme, ColorManager,
    ANSI, THEMES
)


class TestColor:
    """Tests for Color dataclass."""

    def test_default_color_is_white(self):
        """Default color should be white (255, 255, 255)."""
        color = Color()
        assert color.r == 255
        assert color.g == 255
        assert color.b == 255

    def test_color_from_hex(self):
        """Should create color from hex code."""
        color = Color.from_hex("#FF0000")
        assert color.r == 255
        assert color.g == 0
        assert color.b == 0

    def test_color_from_hex_without_hash(self):
        """Should handle hex code without # prefix."""
        color = Color.from_hex("00FF00")
        assert color.r == 0
        assert color.g == 255
        assert color.b == 0

    def test_color_to_ansi_fg(self):
        """Should generate foreground ANSI escape sequence."""
        color = Color(r=100, g=150, b=200)
        ansi = color.to_ansi_fg()
        assert ansi == "\033[38;2;100;150;200m"

    def test_color_to_ansi_bg(self):
        """Should generate background ANSI escape sequence."""
        color = Color(r=50, g=75, b=100)
        ansi = color.to_ansi_bg()
        assert ansi == "\033[48;2;50;75;100m"


class TestANSI:
    """Tests for ANSI escape codes."""

    def test_reset_code(self):
        """Reset should be standard ANSI reset."""
        assert ANSI.RESET == "\033[0m"

    def test_basic_colors_exist(self):
        """All basic colors should be defined."""
        assert ANSI.BLACK
        assert ANSI.RED
        assert ANSI.GREEN
        assert ANSI.YELLOW
        assert ANSI.BLUE
        assert ANSI.MAGENTA
        assert ANSI.CYAN
        assert ANSI.WHITE

    def test_bright_colors_exist(self):
        """All bright colors should be defined."""
        assert ANSI.BRIGHT_BLACK
        assert ANSI.BRIGHT_RED
        assert ANSI.BRIGHT_GREEN
        assert ANSI.BRIGHT_YELLOW
        assert ANSI.BRIGHT_BLUE
        assert ANSI.BRIGHT_MAGENTA
        assert ANSI.BRIGHT_CYAN
        assert ANSI.BRIGHT_WHITE

    def test_style_codes_exist(self):
        """Style codes should be defined."""
        assert ANSI.BOLD
        assert ANSI.DIM
        assert ANSI.ITALIC
        assert ANSI.UNDERLINE


class TestColorTheme:
    """Tests for ColorTheme."""

    def test_default_theme_values(self):
        """Default theme should have sensible defaults."""
        theme = ColorTheme(name="test")
        assert theme.text == ANSI.WHITE
        assert theme.ui_error == ANSI.RED
        assert theme.ui_success == ANSI.GREEN

    def test_theme_with_custom_values(self):
        """Should accept custom color values."""
        theme = ColorTheme(
            name="custom",
            text=ANSI.CYAN,
            dialogue=ANSI.YELLOW
        )
        assert theme.text == ANSI.CYAN
        assert theme.dialogue == ANSI.YELLOW


class TestPredefinedThemes:
    """Tests for predefined themes."""

    def test_noir_theme_exists(self):
        """Noir theme should be defined."""
        assert "noir" in THEMES
        assert THEMES["noir"].name == "noir"

    def test_horror_theme_exists(self):
        """Horror theme should be defined."""
        assert "horror" in THEMES
        assert THEMES["horror"].name == "horror"

    def test_mystery_theme_exists(self):
        """Mystery theme should be defined."""
        assert "mystery" in THEMES
        assert THEMES["mystery"].name == "mystery"

    def test_default_theme_exists(self):
        """Default theme should be defined."""
        assert "default" in THEMES


class TestColorManager:
    """Tests for ColorManager."""

    def test_manager_creation(self):
        """Should create color manager."""
        manager = ColorManager()
        assert manager is not None

    def test_force_no_color(self):
        """Forcing no color should disable colors."""
        manager = ColorManager(force_no_color=True)
        assert not manager.enabled

    def test_force_color(self):
        """Forcing color should enable truecolor support."""
        manager = ColorManager(force_color=True)
        assert manager._support == ColorSupport.TRUECOLOR

    def test_colorize_when_enabled(self):
        """Colorize should add color codes when enabled."""
        manager = ColorManager(force_color=True)
        result = manager.colorize("test", ANSI.RED)
        assert result == f"{ANSI.RED}test{ANSI.RESET}"

    def test_colorize_when_disabled(self):
        """Colorize should return plain text when disabled."""
        manager = ColorManager(force_no_color=True)
        result = manager.colorize("test", ANSI.RED)
        assert result == "test"

    def test_bold_method(self):
        """Bold should wrap text in bold codes."""
        manager = ColorManager(force_color=True)
        result = manager.bold("test")
        assert ANSI.BOLD in result
        assert ANSI.RESET in result

    def test_dim_method(self):
        """Dim should wrap text in dim codes."""
        manager = ColorManager(force_color=True)
        result = manager.dim("test")
        assert ANSI.DIM in result

    def test_italic_method(self):
        """Italic should wrap text in italic codes."""
        manager = ColorManager(force_color=True)
        result = manager.italic("test")
        assert ANSI.ITALIC in result

    def test_set_theme(self):
        """Should switch between themes."""
        manager = ColorManager()
        assert manager.set_theme("noir")
        assert manager.theme.name == "noir"

    def test_set_invalid_theme(self):
        """Setting invalid theme should return False."""
        manager = ColorManager()
        assert not manager.set_theme("nonexistent")

    def test_enable_disable(self):
        """Should toggle color output."""
        manager = ColorManager(force_color=True)
        assert manager.enabled

        manager.disable()
        assert not manager.enabled

        manager.enable()
        assert manager.enabled

    def test_themed_methods(self):
        """Themed color methods should work."""
        manager = ColorManager(force_color=True)

        assert manager.text("test")
        assert manager.dialogue("test")
        assert manager.speaker("test")
        assert manager.narration("test")
        assert manager.error("test")
        assert manager.success("test")
        assert manager.highlight("test")
        assert manager.border("test")

    def test_tension_colors(self):
        """Tension method should use appropriate colors."""
        manager = ColorManager(force_color=True)

        low = manager.tension("test", 0.1)
        medium = manager.tension("test", 0.5)
        high = manager.tension("test", 0.9)

        # All should contain the text
        assert "test" in low
        assert "test" in medium
        assert "test" in high

    def test_hotspot_colors(self):
        """Hotspot method should color by type."""
        manager = ColorManager(force_color=True)

        person = manager.hotspot("test", "person")
        item = manager.hotspot("test", "item")
        evidence = manager.hotspot("test", "evidence")
        exit_color = manager.hotspot("test", "exit")

        # All should contain the text
        assert "test" in person
        assert "test" in item
        assert "test" in evidence
        assert "test" in exit_color

    def test_atmosphere_color(self):
        """Atmosphere method should apply atmosphere color."""
        manager = ColorManager(force_color=True)
        result = manager.atmosphere("test")
        assert "test" in result

    def test_rgb_color(self):
        """RGB method should apply truecolor."""
        manager = ColorManager(force_color=True)
        result = manager.rgb("test", 100, 150, 200)
        assert "\033[38;2;100;150;200m" in result
        assert "test" in result

    def test_rgb_disabled_without_truecolor(self):
        """RGB should return plain text without truecolor support."""
        manager = ColorManager(force_no_color=True)
        result = manager.rgb("test", 100, 150, 200)
        assert result == "test"
