"""
Renderer - Main rendering engine for terminal output.
"""

import os
import sys

from .scene import Scene


class Renderer:
    """
    Terminal renderer for ShadowEngine.

    Handles screen output, clearing, and formatting.
    """

    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
        self.use_clear = True   # Whether to clear screen between renders

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        if not self.use_clear:
            return

        if sys.platform == "win32":
            os.system("cls")
        else:
            os.system("clear")

    def render_scene(self, scene: Scene) -> None:
        """Render a complete scene to the terminal."""
        if self.use_clear:
            self.clear_screen()

        lines = scene.get_rendered_scene()
        for line in lines:
            print(line)

    def render_text(self, text: str, wrap: bool = True) -> None:
        """Render text with optional word wrapping."""
        if wrap:
            lines = self._word_wrap(text, self.width - 4)
            for line in lines:
                print(f"  {line}")
        else:
            print(text)

    def render_dialogue(self, speaker: str, text: str, mood: str = "") -> None:
        """Render dialogue from a character."""
        print()
        if mood:
            print(f'{speaker} says {mood}:')
        else:
            print(f'{speaker} says:')
        print()

        lines = self._word_wrap(text, self.width - 6)
        for line in lines:
            print(f'  "{line}"')
        print()

    def render_narration(self, text: str) -> None:
        """Render narrative text (italicized in supporting terminals)."""
        print()
        lines = self._word_wrap(text, self.width - 4)
        for line in lines:
            print(f"  {line}")
        print()

    def render_action_result(self, text: str) -> None:
        """Render the result of a player action."""
        print()
        lines = self._word_wrap(text, self.width - 2)
        for line in lines:
            print(line)
        print()

    def render_error(self, text: str) -> None:
        """Render an error message."""
        print()
        print(f"[!] {text}")
        print()

    def render_prompt(self) -> str:
        """Render the input prompt and get player input."""
        try:
            return input("> ").strip()
        except EOFError:
            return "quit"
        except KeyboardInterrupt:
            print()
            return "quit"

    def render_dialogue_prompt(self, speaker: str) -> str:
        """Render prompt during conversation."""
        try:
            return input(f"[talking to {speaker}] > ").strip()
        except EOFError:
            return "leave"
        except KeyboardInterrupt:
            print()
            return "leave"

    def render_topics(self, topics: list, exhausted: set) -> None:
        """Render available conversation topics."""
        print()
        print("Topics you can discuss:")
        for i, topic in enumerate(topics, 1):
            status = " (already discussed)" if topic.id in exhausted else ""
            print(f"  [{i}] {topic.name}{status}")
        print()
        print("Or: accuse, threaten, show [item], leave")
        print()

    def render_inventory(self, items: list) -> None:
        """Render player inventory."""
        print()
        if not items:
            print("Your inventory is empty.")
        else:
            print("You are carrying:")
            for item in items:
                print(f"  - {item}")
        print()

    def render_discovery(self, text: str) -> None:
        """Render a discovery notification."""
        print()
        print("*" * 40)
        print("  DISCOVERED:")
        lines = self._word_wrap(text, 36)
        for line in lines:
            print(f"  {line}")
        print("*" * 40)
        print()

    def render_title_screen(self, title: str, subtitle: str = "") -> None:
        """Render a title screen."""
        self.clear_screen()
        print()
        print("=" * self.width)
        print()
        print(title.center(self.width))
        if subtitle:
            print(subtitle.center(self.width))
        print()
        print("=" * self.width)
        print()

    def render_game_over(self, ending_text: str) -> None:
        """Render game over screen."""
        print()
        print("=" * self.width)
        print(" GAME OVER ".center(self.width))
        print("=" * self.width)
        print()
        lines = self._word_wrap(ending_text, self.width - 4)
        for line in lines:
            print(f"  {line}")
        print()
        print("=" * self.width)

    def render_separator(self) -> None:
        """Render a visual separator."""
        print("-" * self.width)

    def render_status_bar(self, location: str, time: str, tension: float = 0) -> None:
        """Render a status bar."""
        tension_str = "!" * int(tension * 5) if tension > 0 else ""
        left = f" {location}"
        right = f"{time} {tension_str} "
        padding = self.width - len(left) - len(right)
        print(f"{left}{' ' * padding}{right}")

    def wait_for_key(self, prompt: str = "Press Enter to continue...") -> None:
        """Wait for player to press a key."""
        try:
            input(prompt)
        except (EOFError, KeyboardInterrupt):
            pass

    def _word_wrap(self, text: str, width: int) -> list[str]:
        """Wrap text to specified width."""
        if not text:
            return []

        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        return lines


# Global renderer instance - uses default terminal size from config
from ..config import get_terminal_size
_width, _height = get_terminal_size()
renderer = Renderer(width=_width, height=_height)
