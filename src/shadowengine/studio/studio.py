"""
Main Studio interface for ASCII art creation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Callable
from datetime import datetime
from enum import Enum, auto
import uuid

from .art import ASCIIArt, ArtCategory
from .static_art import StaticArt, RenderLayer, TileCoverage, STATIC_ART_TEMPLATES
from .entity import DynamicEntity, EntityState, ENTITY_TEMPLATES
from .tags import (
    ArtTags, ObjectType, Size, Placement,
    InteractionType, EnvironmentType
)
from .personality import PersonalityTemplate, PERSONALITY_TEMPLATES
from .animation import Animation, AnimationFrame, AnimationTrigger
from .asset_pool import AssetPool
from .gallery import Gallery, GalleryEntry, ContentRating
from .usage_stats import UsageStats


class StudioMode(Enum):
    """Current mode of the studio."""
    DRAW = auto()         # Drawing ASCII art
    TAG = auto()          # Tagging/classifying
    ANIMATE = auto()      # Creating animations
    PERSONALITY = auto()  # Configuring entity personality
    PREVIEW = auto()      # Previewing art
    EXPORT = auto()       # Export/save mode


class Tool(Enum):
    """Drawing tools available."""
    PENCIL = auto()       # Single character
    LINE = auto()         # Draw lines
    RECTANGLE = auto()    # Draw rectangles
    FILL = auto()         # Flood fill
    ERASER = auto()       # Erase (set to space)
    SELECT = auto()       # Select region
    MOVE = auto()         # Move selection
    COPY = auto()         # Copy selection
    PASTE = auto()        # Paste clipboard


@dataclass
class Selection:
    """Selection region in the canvas."""
    x: int
    y: int
    width: int
    height: int
    content: Optional[List[List[str]]] = None

    def contains(self, px: int, py: int) -> bool:
        """Check if point is in selection."""
        return (self.x <= px < self.x + self.width and
                self.y <= py < self.y + self.height)

    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Get (x, y, width, height) bounds."""
        return (self.x, self.y, self.width, self.height)


@dataclass
class HistoryEntry:
    """Entry in undo/redo history."""
    tiles: List[List[str]]
    description: str
    timestamp: datetime = field(default_factory=datetime.now)


class Studio:
    """
    Main ASCII Art Studio interface.

    Provides tools for creating, editing, and managing
    ASCII art assets for the game world.
    """

    def __init__(
        self,
        player_id: str,
        asset_pool: Optional[AssetPool] = None,
        gallery: Optional[Gallery] = None,
        usage_stats: Optional[UsageStats] = None
    ):
        self.player_id = player_id
        self.asset_pool = asset_pool if asset_pool is not None else AssetPool()
        self.gallery = gallery if gallery is not None else Gallery()
        self.usage_stats = usage_stats if usage_stats is not None else UsageStats()

        # Current work
        self._current_art: Optional[ASCIIArt] = None
        self._mode = StudioMode.DRAW
        self._tool = Tool.PENCIL
        self._current_char = "#"

        # Canvas state
        self._canvas_width = 40
        self._canvas_height = 20
        self._cursor_x = 0
        self._cursor_y = 0

        # Selection and clipboard
        self._selection: Optional[Selection] = None
        self._clipboard: Optional[List[List[str]]] = None

        # History for undo/redo
        self._history: List[HistoryEntry] = []
        self._history_index = -1
        self._max_history = 50

        # Preview state
        self._preview_frame = 0
        self._animation_playing = False

    @property
    def mode(self) -> StudioMode:
        """Current studio mode."""
        return self._mode

    @property
    def tool(self) -> Tool:
        """Current drawing tool."""
        return self._tool

    @property
    def current_art(self) -> Optional[ASCIIArt]:
        """Currently edited art."""
        return self._current_art

    @property
    def cursor_position(self) -> Tuple[int, int]:
        """Current cursor position."""
        return (self._cursor_x, self._cursor_y)

    def set_mode(self, mode: StudioMode) -> None:
        """Change studio mode."""
        self._mode = mode

    def set_tool(self, tool: Tool) -> None:
        """Change drawing tool."""
        self._tool = tool

    def set_char(self, char: str) -> None:
        """Set current drawing character."""
        if char and len(char) == 1:
            self._current_char = char

    # === Canvas Operations ===

    def new_canvas(
        self,
        width: int = 40,
        height: int = 20,
        name: str = "Untitled"
    ) -> ASCIIArt:
        """
        Create a new blank canvas.

        Args:
            width: Canvas width
            height: Canvas height
            name: Art name

        Returns:
            New ASCIIArt instance
        """
        tags = ArtTags(object_type=ObjectType.OTHER)
        self._current_art = ASCIIArt.create_blank(name, width, height, tags)
        self._current_art.player_id = self.player_id
        self._canvas_width = width
        self._canvas_height = height
        self._cursor_x = 0
        self._cursor_y = 0
        self._clear_history()
        self._save_history("New canvas")
        return self._current_art

    def load_art(self, art: ASCIIArt) -> None:
        """Load existing art for editing."""
        self._current_art = art
        self._canvas_width = art.width
        self._canvas_height = art.height
        self._cursor_x = 0
        self._cursor_y = 0
        self._clear_history()
        self._save_history("Loaded art")

    def load_from_string(self, name: str, art_string: str) -> ASCIIArt:
        """Load art from a multi-line string."""
        tags = ArtTags(object_type=ObjectType.OTHER)
        art = ASCIIArt.from_string(name, art_string, tags)
        art.player_id = self.player_id
        self.load_art(art)
        return art

    def load_template(self, template_name: str) -> Optional[ASCIIArt]:
        """Load a predefined template."""
        if template_name in STATIC_ART_TEMPLATES:
            from .static_art import create_from_template
            art = create_from_template(template_name, self.player_id)
            if art:
                self.load_art(art)
            return art
        elif template_name in ENTITY_TEMPLATES:
            from .entity import create_entity_from_template
            art = create_entity_from_template(template_name, self.player_id)
            if art:
                self.load_art(art)
            return art
        return None

    def resize_canvas(self, width: int, height: int) -> None:
        """Resize the current canvas."""
        if not self._current_art:
            return

        old_tiles = self._current_art.tiles
        new_tiles = [[" " for _ in range(width)] for _ in range(height)]

        # Copy existing content
        for y in range(min(len(old_tiles), height)):
            for x in range(min(len(old_tiles[y]), width)):
                new_tiles[y][x] = old_tiles[y][x]

        self._current_art.tiles = new_tiles
        self._canvas_width = width
        self._canvas_height = height
        self._save_history("Resize canvas")

    # === Drawing Operations ===

    def move_cursor(self, dx: int, dy: int) -> Tuple[int, int]:
        """Move cursor by delta."""
        self._cursor_x = max(0, min(self._canvas_width - 1, self._cursor_x + dx))
        self._cursor_y = max(0, min(self._canvas_height - 1, self._cursor_y + dy))
        return self.cursor_position

    def set_cursor(self, x: int, y: int) -> Tuple[int, int]:
        """Set cursor position."""
        self._cursor_x = max(0, min(self._canvas_width - 1, x))
        self._cursor_y = max(0, min(self._canvas_height - 1, y))
        return self.cursor_position

    def draw_at_cursor(self, char: Optional[str] = None) -> None:
        """Draw character at cursor position."""
        if not self._current_art:
            return

        char = char or self._current_char
        self._current_art.set_tile(self._cursor_x, self._cursor_y, char)

    def draw_at(self, x: int, y: int, char: Optional[str] = None) -> None:
        """Draw character at specific position."""
        if not self._current_art:
            return

        char = char or self._current_char
        self._current_art.set_tile(x, y, char)

    def draw_line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        char: Optional[str] = None
    ) -> None:
        """Draw a line between two points using Bresenham's algorithm."""
        if not self._current_art:
            return

        char = char or self._current_char
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1
        while True:
            self._current_art.set_tile(x, y, char)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

        self._save_history("Draw line")

    def draw_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        char: Optional[str] = None,
        filled: bool = False
    ) -> None:
        """Draw a rectangle."""
        if not self._current_art:
            return

        char = char or self._current_char

        if filled:
            for dy in range(height):
                for dx in range(width):
                    self._current_art.set_tile(x + dx, y + dy, char)
        else:
            # Top and bottom
            for dx in range(width):
                self._current_art.set_tile(x + dx, y, char)
                self._current_art.set_tile(x + dx, y + height - 1, char)
            # Left and right
            for dy in range(height):
                self._current_art.set_tile(x, y + dy, char)
                self._current_art.set_tile(x + width - 1, y + dy, char)

        self._save_history("Draw rectangle")

    def flood_fill(self, x: int, y: int, char: Optional[str] = None) -> int:
        """
        Flood fill from position.

        Returns:
            Number of tiles filled
        """
        if not self._current_art:
            return 0

        char = char or self._current_char
        target_char = self._current_art.get_tile(x, y)

        if target_char == char:
            return 0

        filled = 0
        stack = [(x, y)]
        visited = set()

        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue

            if cx < 0 or cx >= self._canvas_width:
                continue
            if cy < 0 or cy >= self._canvas_height:
                continue

            if self._current_art.get_tile(cx, cy) != target_char:
                continue

            visited.add((cx, cy))
            self._current_art.set_tile(cx, cy, char)
            filled += 1

            stack.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])

        self._save_history(f"Fill ({filled} tiles)")
        return filled

    def erase_at(self, x: int, y: int) -> None:
        """Erase (set to space) at position."""
        self.draw_at(x, y, " ")

    # === Selection Operations ===

    def select_region(self, x: int, y: int, width: int, height: int) -> Selection:
        """Select a region of the canvas."""
        self._selection = Selection(x, y, width, height)

        # Copy content
        if self._current_art:
            content = []
            for dy in range(height):
                row = []
                for dx in range(width):
                    row.append(self._current_art.get_tile(x + dx, y + dy))
                content.append(row)
            self._selection.content = content

        return self._selection

    def clear_selection(self) -> None:
        """Clear current selection."""
        self._selection = None

    def copy_selection(self) -> bool:
        """Copy selection to clipboard."""
        if not self._selection or not self._selection.content:
            return False

        self._clipboard = [row.copy() for row in self._selection.content]
        return True

    def cut_selection(self) -> bool:
        """Cut selection to clipboard."""
        if not self.copy_selection():
            return False

        # Clear selected region
        if self._current_art and self._selection:
            for dy in range(self._selection.height):
                for dx in range(self._selection.width):
                    self._current_art.set_tile(
                        self._selection.x + dx,
                        self._selection.y + dy,
                        " "
                    )
            self._save_history("Cut selection")

        return True

    def paste(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """Paste clipboard at position (or cursor)."""
        if not self._clipboard or not self._current_art:
            return False

        x = x if x is not None else self._cursor_x
        y = y if y is not None else self._cursor_y

        for dy, row in enumerate(self._clipboard):
            for dx, char in enumerate(row):
                if char != " ":  # Don't paste spaces
                    self._current_art.set_tile(x + dx, y + dy, char)

        self._save_history("Paste")
        return True

    # === History Operations ===

    def _clear_history(self) -> None:
        """Clear history."""
        self._history.clear()
        self._history_index = -1

    def _save_history(self, description: str) -> None:
        """Save current state to history."""
        if not self._current_art:
            return

        # Remove any redo history
        if self._history_index < len(self._history) - 1:
            self._history = self._history[:self._history_index + 1]

        entry = HistoryEntry(
            tiles=[row.copy() for row in self._current_art.tiles],
            description=description
        )
        self._history.append(entry)
        self._history_index = len(self._history) - 1

        # Limit history size
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
            self._history_index = len(self._history) - 1

    def undo(self) -> bool:
        """Undo last action."""
        if self._history_index <= 0 or not self._current_art:
            return False

        self._history_index -= 1
        entry = self._history[self._history_index]
        self._current_art.tiles = [row.copy() for row in entry.tiles]
        return True

    def redo(self) -> bool:
        """Redo last undone action."""
        if self._history_index >= len(self._history) - 1 or not self._current_art:
            return False

        self._history_index += 1
        entry = self._history[self._history_index]
        self._current_art.tiles = [row.copy() for row in entry.tiles]
        return True

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self._history_index > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self._history_index < len(self._history) - 1

    # === Tagging Operations ===

    def set_object_type(self, object_type: ObjectType) -> None:
        """Set the object type tag."""
        if self._current_art:
            self._current_art.tags.object_type = object_type

    def set_size(self, size: Size) -> None:
        """Set the size tag."""
        if self._current_art:
            self._current_art.tags.size = size

    def set_placement(self, placement: Placement) -> None:
        """Set the placement tag."""
        if self._current_art:
            self._current_art.tags.placement = placement

    def add_interaction(self, interaction: InteractionType) -> None:
        """Add an interaction type."""
        if self._current_art:
            self._current_art.tags.add_interaction(interaction)

    def remove_interaction(self, interaction: InteractionType) -> None:
        """Remove an interaction type."""
        if self._current_art:
            self._current_art.tags.remove_interaction(interaction)

    def add_environment(self, environment: EnvironmentType) -> None:
        """Add an environment type."""
        if self._current_art:
            self._current_art.tags.add_environment(environment)

    def remove_environment(self, environment: EnvironmentType) -> None:
        """Remove an environment type."""
        if self._current_art:
            self._current_art.tags.remove_environment(environment)

    def add_custom_tag(self, tag: str) -> None:
        """Add a custom tag."""
        if self._current_art:
            self._current_art.tags.add_custom_tag(tag)

    # === Conversion Operations ===

    def convert_to_static(self) -> Optional[StaticArt]:
        """Convert current art to StaticArt."""
        if not self._current_art:
            return None

        static = StaticArt(
            name=self._current_art.name,
            tiles=[row.copy() for row in self._current_art.tiles],
            tags=ArtTags.from_dict(self._current_art.tags.to_dict()),
            player_id=self.player_id,
            description=self._current_art.description
        )
        self._current_art = static
        return static

    def convert_to_entity(
        self,
        personality_name: str = "curious_neutral"
    ) -> Optional[DynamicEntity]:
        """Convert current art to DynamicEntity."""
        if not self._current_art:
            return None

        personality = PERSONALITY_TEMPLATES.get(personality_name)
        if not personality:
            personality = PersonalityTemplate(name="Custom")
        else:
            personality = personality.copy()

        entity = DynamicEntity(
            name=self._current_art.name,
            tiles=[row.copy() for row in self._current_art.tiles],
            tags=ArtTags.from_dict(self._current_art.tags.to_dict()),
            player_id=self.player_id,
            description=self._current_art.description,
            personality=personality
        )
        self._current_art = entity
        return entity

    # === Save and Export ===

    def save_to_pool(self) -> Optional[str]:
        """
        Save current art to asset pool.

        Returns:
            Asset ID or None if failed
        """
        if not self._current_art:
            return None

        self.asset_pool.add_asset(self._current_art)
        return self._current_art.id

    def submit_to_gallery(
        self,
        title: str,
        description: str = "",
        tags: set = None,
        creator_name: str = "Anonymous"
    ) -> Optional[GalleryEntry]:
        """
        Submit current art to gallery.

        Returns:
            GalleryEntry or None if failed
        """
        if not self._current_art:
            return None

        return self.gallery.submit(
            art=self._current_art.copy(),
            title=title,
            creator_id=self.player_id,
            creator_name=creator_name,
            description=description,
            tags=tags or set()
        )

    def export_to_string(self) -> Optional[str]:
        """Export current art as rendered string."""
        if not self._current_art:
            return None
        return self._current_art.render()

    def export_to_dict(self) -> Optional[dict]:
        """Export current art as dictionary."""
        if not self._current_art:
            return None
        return self._current_art.to_dict()

    # === Template Listing ===

    @staticmethod
    def list_static_templates() -> List[str]:
        """List available static art templates."""
        return list(STATIC_ART_TEMPLATES.keys())

    @staticmethod
    def list_entity_templates() -> List[str]:
        """List available entity templates."""
        return list(ENTITY_TEMPLATES.keys())

    @staticmethod
    def list_personality_templates() -> List[str]:
        """List available personality templates."""
        return list(PERSONALITY_TEMPLATES.keys())

    # === Render ===

    def render_preview(self) -> str:
        """Render current art preview."""
        if not self._current_art:
            return "(no art loaded)"

        lines = []

        # Header
        lines.append(f"╔{'═' * (self._canvas_width + 2)}╗")
        lines.append(f"║ {self._current_art.name[:self._canvas_width]:<{self._canvas_width}} ║")
        lines.append(f"╠{'═' * (self._canvas_width + 2)}╣")

        # Art content
        for y, row in enumerate(self._current_art.tiles):
            row_str = "".join(row)
            if len(row_str) < self._canvas_width:
                row_str += " " * (self._canvas_width - len(row_str))

            # Highlight cursor position
            if y == self._cursor_y:
                row_list = list(row_str)
                if 0 <= self._cursor_x < len(row_list):
                    # Mark cursor with brackets
                    pass  # In actual UI, cursor would be highlighted
                row_str = "".join(row_list)

            lines.append(f"║ {row_str} ║")

        lines.append(f"╚{'═' * (self._canvas_width + 2)}╝")

        # Footer with info
        lines.append(f"Mode: {self._mode.name} | Tool: {self._tool.name} | Char: '{self._current_char}'")
        lines.append(f"Cursor: ({self._cursor_x}, {self._cursor_y}) | Size: {self._canvas_width}x{self._canvas_height}")

        return "\n".join(lines)

    def get_status(self) -> Dict[str, Any]:
        """Get current studio status."""
        return {
            "mode": self._mode.name,
            "tool": self._tool.name,
            "current_char": self._current_char,
            "cursor": self.cursor_position,
            "canvas_size": (self._canvas_width, self._canvas_height),
            "has_art": self._current_art is not None,
            "art_name": self._current_art.name if self._current_art else None,
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo(),
            "has_selection": self._selection is not None,
            "has_clipboard": self._clipboard is not None
        }
