"""
Command History - Track and recall previous commands.

Provides:
- Command history storage
- History navigation
- Command search
- Undo/redo support
"""

from dataclasses import dataclass, field
from typing import Optional
from collections import deque


@dataclass
class CommandEntry:
    """An entry in the command history."""
    command: str
    timestamp: float = 0.0
    result: str = ""
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "timestamp": self.timestamp,
            "result": self.result,
            "success": self.success
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CommandEntry":
        return cls(**data)


class CommandHistory:
    """
    Stores and navigates command history.

    Supports up/down navigation, search, and persistence.
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.entries: deque[CommandEntry] = deque(maxlen=max_size)
        self._position: int = -1  # Current navigation position
        self._search_filter: Optional[str] = None

    def add(self, command: str, result: str = "", success: bool = True) -> None:
        """Add a command to history."""
        import time
        entry = CommandEntry(
            command=command,
            timestamp=time.time(),
            result=result,
            success=success
        )
        self.entries.append(entry)
        self._position = -1  # Reset position after new entry

    def get_previous(self) -> Optional[str]:
        """Navigate to previous command."""
        if not self.entries:
            return None

        filtered = self._get_filtered_entries()
        if not filtered:
            return None

        if self._position < 0:
            self._position = len(filtered) - 1
        elif self._position > 0:
            self._position -= 1

        return filtered[self._position].command

    def get_next(self) -> Optional[str]:
        """Navigate to next command."""
        if not self.entries:
            return None

        filtered = self._get_filtered_entries()
        if not filtered:
            return None

        if self._position < 0:
            return None

        if self._position < len(filtered) - 1:
            self._position += 1
            return filtered[self._position].command
        else:
            self._position = -1
            return ""  # Return empty to clear input

    def _get_filtered_entries(self) -> list[CommandEntry]:
        """Get entries matching current filter."""
        if not self._search_filter:
            return list(self.entries)

        filter_lower = self._search_filter.lower()
        return [
            e for e in self.entries
            if filter_lower in e.command.lower()
        ]

    def set_filter(self, filter_str: Optional[str]) -> None:
        """Set search filter for navigation."""
        self._search_filter = filter_str
        self._position = -1

    def clear_filter(self) -> None:
        """Clear search filter."""
        self._search_filter = None
        self._position = -1

    def search(self, query: str) -> list[CommandEntry]:
        """Search history for matching commands."""
        query_lower = query.lower()
        return [
            e for e in self.entries
            if query_lower in e.command.lower()
        ]

    def get_recent(self, count: int = 10) -> list[CommandEntry]:
        """Get most recent commands."""
        entries = list(self.entries)
        return entries[-count:] if len(entries) > count else entries

    def get_by_index(self, index: int) -> Optional[CommandEntry]:
        """Get entry by index (0 = oldest)."""
        if 0 <= index < len(self.entries):
            return self.entries[index]
        return None

    def get_last(self) -> Optional[CommandEntry]:
        """Get the most recent command."""
        if self.entries:
            return self.entries[-1]
        return None

    def repeat_last(self) -> Optional[str]:
        """Get the last command for repeat."""
        last = self.get_last()
        return last.command if last else None

    def get_unique_commands(self) -> list[str]:
        """Get list of unique commands used."""
        seen = set()
        unique = []
        for entry in reversed(self.entries):
            cmd = entry.command.split()[0] if entry.command else ""
            if cmd and cmd not in seen:
                seen.add(cmd)
                unique.append(cmd)
        return unique

    def get_command_counts(self) -> dict[str, int]:
        """Get count of each command used."""
        counts: dict[str, int] = {}
        for entry in self.entries:
            cmd = entry.command.split()[0] if entry.command else ""
            if cmd:
                counts[cmd] = counts.get(cmd, 0) + 1
        return counts

    def clear(self) -> None:
        """Clear all history."""
        self.entries.clear()
        self._position = -1

    def __len__(self) -> int:
        return len(self.entries)

    def to_dict(self) -> dict:
        return {
            "entries": [e.to_dict() for e in self.entries],
            "max_size": self.max_size
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CommandHistory":
        history = cls(max_size=data.get("max_size", 1000))
        for entry_data in data.get("entries", []):
            history.entries.append(CommandEntry.from_dict(entry_data))
        return history


@dataclass
class UndoableAction:
    """An action that can be undone."""
    action_type: str
    description: str
    undo_data: dict = field(default_factory=dict)
    redo_data: dict = field(default_factory=dict)


class UndoStack:
    """
    Manages undo/redo for game actions.

    Stores reversible actions for undo support.
    """

    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self.undo_stack: list[UndoableAction] = []
        self.redo_stack: list[UndoableAction] = []

    def push(self, action: UndoableAction) -> None:
        """Push an undoable action."""
        self.undo_stack.append(action)
        self.redo_stack.clear()  # Clear redo on new action

        # Limit size
        while len(self.undo_stack) > self.max_size:
            self.undo_stack.pop(0)

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0

    def pop_undo(self) -> Optional[UndoableAction]:
        """Pop the last action for undo."""
        if not self.undo_stack:
            return None

        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        return action

    def pop_redo(self) -> Optional[UndoableAction]:
        """Pop the last undone action for redo."""
        if not self.redo_stack:
            return None

        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        return action

    def peek_undo(self) -> Optional[UndoableAction]:
        """Peek at the next undo action."""
        return self.undo_stack[-1] if self.undo_stack else None

    def peek_redo(self) -> Optional[UndoableAction]:
        """Peek at the next redo action."""
        return self.redo_stack[-1] if self.redo_stack else None

    def clear(self) -> None:
        """Clear all undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()


class InputBuffer:
    """
    Manages text input with editing support.

    Provides cursor movement, insertion, deletion.
    """

    def __init__(self):
        self.buffer: list[str] = []
        self.cursor: int = 0

    @property
    def text(self) -> str:
        """Get current buffer text."""
        return "".join(self.buffer)

    def set_text(self, text: str) -> None:
        """Set buffer contents."""
        self.buffer = list(text)
        self.cursor = len(self.buffer)

    def insert(self, char: str) -> None:
        """Insert character at cursor."""
        self.buffer.insert(self.cursor, char)
        self.cursor += 1

    def insert_text(self, text: str) -> None:
        """Insert text at cursor."""
        for char in text:
            self.insert(char)

    def delete_char(self) -> bool:
        """Delete character before cursor (backspace)."""
        if self.cursor > 0:
            self.buffer.pop(self.cursor - 1)
            self.cursor -= 1
            return True
        return False

    def delete_forward(self) -> bool:
        """Delete character at cursor (delete key)."""
        if self.cursor < len(self.buffer):
            self.buffer.pop(self.cursor)
            return True
        return False

    def delete_word(self) -> bool:
        """Delete word before cursor."""
        if self.cursor == 0:
            return False

        # Find start of previous word
        pos = self.cursor - 1
        while pos > 0 and self.buffer[pos - 1] == ' ':
            pos -= 1
        while pos > 0 and self.buffer[pos - 1] != ' ':
            pos -= 1

        # Delete from pos to cursor
        del self.buffer[pos:self.cursor]
        self.cursor = pos
        return True

    def clear(self) -> None:
        """Clear buffer."""
        self.buffer.clear()
        self.cursor = 0

    def move_left(self) -> bool:
        """Move cursor left."""
        if self.cursor > 0:
            self.cursor -= 1
            return True
        return False

    def move_right(self) -> bool:
        """Move cursor right."""
        if self.cursor < len(self.buffer):
            self.cursor += 1
            return True
        return False

    def move_to_start(self) -> None:
        """Move cursor to start."""
        self.cursor = 0

    def move_to_end(self) -> None:
        """Move cursor to end."""
        self.cursor = len(self.buffer)

    def move_word_left(self) -> None:
        """Move cursor to previous word."""
        while self.cursor > 0 and self.buffer[self.cursor - 1] == ' ':
            self.cursor -= 1
        while self.cursor > 0 and self.buffer[self.cursor - 1] != ' ':
            self.cursor -= 1

    def move_word_right(self) -> None:
        """Move cursor to next word."""
        while self.cursor < len(self.buffer) and self.buffer[self.cursor] != ' ':
            self.cursor += 1
        while self.cursor < len(self.buffer) and self.buffer[self.cursor] == ' ':
            self.cursor += 1

    def get_before_cursor(self) -> str:
        """Get text before cursor."""
        return "".join(self.buffer[:self.cursor])

    def get_after_cursor(self) -> str:
        """Get text after cursor."""
        return "".join(self.buffer[self.cursor:])
