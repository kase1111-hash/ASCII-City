"""Tests for the command history system."""

import pytest
from src.shadowengine.ui.history import (
    CommandEntry, CommandHistory,
    UndoableAction, UndoStack, InputBuffer
)


class TestCommandEntry:
    """Tests for CommandEntry."""

    def test_creation(self):
        """Should create command entry."""
        entry = CommandEntry(command="look")
        assert entry.command == "look"
        assert entry.success is True

    def test_serialization(self):
        """Should serialize and deserialize."""
        entry = CommandEntry(
            command="examine desk",
            timestamp=123.0,
            result="You see a desk.",
            success=True
        )

        data = entry.to_dict()
        restored = CommandEntry.from_dict(data)

        assert restored.command == "examine desk"
        assert restored.timestamp == 123.0


class TestCommandHistory:
    """Tests for CommandHistory."""

    def test_creation(self):
        """Should create empty history."""
        history = CommandHistory()
        assert len(history) == 0

    def test_add_command(self):
        """Should add command to history."""
        history = CommandHistory()
        history.add("look")

        assert len(history) == 1

    def test_get_previous(self):
        """Should get previous commands."""
        history = CommandHistory()
        history.add("look")
        history.add("examine")
        history.add("go north")

        assert history.get_previous() == "go north"
        assert history.get_previous() == "examine"
        assert history.get_previous() == "look"
        # At start, should stay at first
        assert history.get_previous() == "look"

    def test_get_next(self):
        """Should get next commands."""
        history = CommandHistory()
        history.add("look")
        history.add("examine")

        # Navigate to start
        history.get_previous()
        history.get_previous()

        assert history.get_next() == "examine"
        # At end, returns empty
        result = history.get_next()
        assert result == ""

    def test_navigation_reset_on_add(self):
        """Adding command should reset navigation."""
        history = CommandHistory()
        history.add("look")
        history.get_previous()

        history.add("examine")

        assert history.get_previous() == "examine"

    def test_set_filter(self):
        """Should filter navigation."""
        history = CommandHistory()
        history.add("look")
        history.add("examine desk")
        history.add("go north")
        history.add("examine chair")

        history.set_filter("examine")

        assert history.get_previous() == "examine chair"
        assert history.get_previous() == "examine desk"

    def test_search(self):
        """Should search history."""
        history = CommandHistory()
        history.add("look")
        history.add("examine desk")
        history.add("examine chair")

        results = history.search("examine")
        assert len(results) == 2

    def test_get_recent(self):
        """Should get recent commands."""
        history = CommandHistory()
        for i in range(20):
            history.add(f"cmd{i}")

        recent = history.get_recent(5)
        assert len(recent) == 5
        assert recent[-1].command == "cmd19"

    def test_get_last(self):
        """Should get last command."""
        history = CommandHistory()
        history.add("first")
        history.add("last")

        last = history.get_last()
        assert last.command == "last"

    def test_repeat_last(self):
        """Should get last command for repeat."""
        history = CommandHistory()
        history.add("look")

        assert history.repeat_last() == "look"

    def test_get_unique_commands(self):
        """Should get unique commands."""
        history = CommandHistory()
        history.add("look")
        history.add("examine desk")
        history.add("look")
        history.add("examine chair")

        unique = history.get_unique_commands()
        assert "look" in unique
        assert "examine" in unique

    def test_get_command_counts(self):
        """Should count command usage."""
        history = CommandHistory()
        history.add("look")
        history.add("look")
        history.add("examine")

        counts = history.get_command_counts()
        assert counts["look"] == 2
        assert counts["examine"] == 1

    def test_max_size(self):
        """Should respect max size."""
        history = CommandHistory(max_size=5)
        for i in range(10):
            history.add(f"cmd{i}")

        assert len(history) == 5
        assert history.entries[0].command == "cmd5"

    def test_clear(self):
        """Should clear history."""
        history = CommandHistory()
        history.add("look")
        history.clear()

        assert len(history) == 0

    def test_serialization(self):
        """Should serialize and deserialize."""
        history = CommandHistory()
        history.add("look")
        history.add("examine")

        data = history.to_dict()
        restored = CommandHistory.from_dict(data)

        assert len(restored) == 2


class TestUndoableAction:
    """Tests for UndoableAction."""

    def test_creation(self):
        """Should create undoable action."""
        action = UndoableAction(
            action_type="move",
            description="Moved north",
            undo_data={"from": "room1"},
            redo_data={"to": "room2"}
        )
        assert action.action_type == "move"


class TestUndoStack:
    """Tests for UndoStack."""

    def test_creation(self):
        """Should create empty stack."""
        stack = UndoStack()
        assert not stack.can_undo()
        assert not stack.can_redo()

    def test_push(self):
        """Should push action."""
        stack = UndoStack()
        action = UndoableAction("test", "Test action")

        stack.push(action)

        assert stack.can_undo()

    def test_pop_undo(self):
        """Should pop for undo."""
        stack = UndoStack()
        action = UndoableAction("test", "Test action")
        stack.push(action)

        popped = stack.pop_undo()

        assert popped is action
        assert not stack.can_undo()
        assert stack.can_redo()

    def test_pop_redo(self):
        """Should pop for redo."""
        stack = UndoStack()
        action = UndoableAction("test", "Test")
        stack.push(action)
        stack.pop_undo()

        popped = stack.pop_redo()

        assert popped is action
        assert stack.can_undo()
        assert not stack.can_redo()

    def test_new_action_clears_redo(self):
        """New action should clear redo stack."""
        stack = UndoStack()
        stack.push(UndoableAction("1", "First"))
        stack.pop_undo()

        stack.push(UndoableAction("2", "Second"))

        assert not stack.can_redo()

    def test_peek_undo(self):
        """Should peek without popping."""
        stack = UndoStack()
        action = UndoableAction("test", "Test")
        stack.push(action)

        peeked = stack.peek_undo()

        assert peeked is action
        assert stack.can_undo()  # Still available

    def test_max_size(self):
        """Should respect max size."""
        stack = UndoStack(max_size=3)

        for i in range(5):
            stack.push(UndoableAction(str(i), f"Action {i}"))

        assert len(stack.undo_stack) == 3

    def test_clear(self):
        """Should clear stacks."""
        stack = UndoStack()
        stack.push(UndoableAction("test", "Test"))
        stack.pop_undo()

        stack.clear()

        assert not stack.can_undo()
        assert not stack.can_redo()


class TestInputBuffer:
    """Tests for InputBuffer."""

    def test_creation(self):
        """Should create empty buffer."""
        buffer = InputBuffer()
        assert buffer.text == ""
        assert buffer.cursor == 0

    def test_set_text(self):
        """Should set text."""
        buffer = InputBuffer()
        buffer.set_text("hello")

        assert buffer.text == "hello"
        assert buffer.cursor == 5

    def test_insert(self):
        """Should insert character."""
        buffer = InputBuffer()
        buffer.insert("a")
        buffer.insert("b")

        assert buffer.text == "ab"
        assert buffer.cursor == 2

    def test_insert_text(self):
        """Should insert text."""
        buffer = InputBuffer()
        buffer.insert_text("hello")

        assert buffer.text == "hello"

    def test_delete_char(self):
        """Should delete character before cursor."""
        buffer = InputBuffer()
        buffer.set_text("hello")
        buffer.delete_char()

        assert buffer.text == "hell"

    def test_delete_char_at_start(self):
        """Should not delete at start."""
        buffer = InputBuffer()
        buffer.set_text("hello")
        buffer.cursor = 0

        result = buffer.delete_char()

        assert result is False
        assert buffer.text == "hello"

    def test_delete_forward(self):
        """Should delete character at cursor."""
        buffer = InputBuffer()
        buffer.set_text("hello")
        buffer.cursor = 2

        buffer.delete_forward()

        assert buffer.text == "helo"

    def test_delete_word(self):
        """Should delete word before cursor."""
        buffer = InputBuffer()
        buffer.set_text("hello world")

        buffer.delete_word()

        assert buffer.text == "hello "

    def test_clear(self):
        """Should clear buffer."""
        buffer = InputBuffer()
        buffer.set_text("hello")
        buffer.clear()

        assert buffer.text == ""
        assert buffer.cursor == 0

    def test_move_left(self):
        """Should move cursor left."""
        buffer = InputBuffer()
        buffer.set_text("hello")

        buffer.move_left()

        assert buffer.cursor == 4

    def test_move_right(self):
        """Should move cursor right."""
        buffer = InputBuffer()
        buffer.set_text("hello")
        buffer.cursor = 2

        buffer.move_right()

        assert buffer.cursor == 3

    def test_move_to_start(self):
        """Should move to start."""
        buffer = InputBuffer()
        buffer.set_text("hello")
        buffer.move_to_start()

        assert buffer.cursor == 0

    def test_move_to_end(self):
        """Should move to end."""
        buffer = InputBuffer()
        buffer.set_text("hello")
        buffer.cursor = 0
        buffer.move_to_end()

        assert buffer.cursor == 5

    def test_move_word_left(self):
        """Should move to previous word."""
        buffer = InputBuffer()
        buffer.set_text("hello world")

        buffer.move_word_left()

        assert buffer.cursor == 6  # Start of "world"

    def test_move_word_right(self):
        """Should move to next word."""
        buffer = InputBuffer()
        buffer.set_text("hello world")
        buffer.cursor = 0

        buffer.move_word_right()

        assert buffer.cursor == 6  # After "hello "

    def test_get_before_cursor(self):
        """Should get text before cursor."""
        buffer = InputBuffer()
        buffer.set_text("hello world")
        buffer.cursor = 6

        assert buffer.get_before_cursor() == "hello "

    def test_get_after_cursor(self):
        """Should get text after cursor."""
        buffer = InputBuffer()
        buffer.set_text("hello world")
        buffer.cursor = 6

        assert buffer.get_after_cursor() == "world"
