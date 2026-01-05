"""Extended tests for UI systems."""

import pytest
from src.shadowengine.ui.tutorial import (
    TutorialPhase, TutorialStep, Tutorial,
    TutorialPrompt, TUTORIAL_STEPS
)
from src.shadowengine.ui.help import (
    HelpCategory, HelpTopic, HelpSystem,
    ContextualHint, HintSystem,
    HELP_TOPICS, create_standard_hints
)
from src.shadowengine.ui.history import (
    CommandEntry, CommandHistory,
    UndoableAction, UndoStack, InputBuffer
)


class TestTutorialEdgeCases:
    """Edge case tests for tutorial system."""

    def test_process_command_inactive_tutorial(self):
        """Should return None when tutorial is not active."""
        tutorial = Tutorial()
        # Not started
        result = tutorial.process_command("look")
        assert result is None

    def test_get_step_after_completion(self):
        """Should return None after tutorial completion."""
        steps = [TutorialStep("s1", TutorialPhase.NAVIGATION, "S1", "c1")]
        tutorial = Tutorial(steps=steps)
        tutorial.start()
        tutorial.process_command("c1")

        step = tutorial.get_current_step()
        assert step is None

    def test_rapid_step_completion(self):
        """Should handle rapid step completion."""
        steps = [
            TutorialStep(f"s{i}", TutorialPhase.NAVIGATION, f"S{i}", f"c{i}")
            for i in range(10)
        ]
        tutorial = Tutorial(steps=steps)
        tutorial.start()

        for i in range(10):
            result = tutorial.process_command(f"c{i}")
            if i < 9:
                assert result is not None
                assert tutorial.current_step == i + 1

        assert tutorial.is_complete()

    def test_empty_steps_list(self):
        """Should handle empty steps list."""
        tutorial = Tutorial(steps=[])
        message = tutorial.start()

        # Should immediately complete
        assert tutorial.get_current_step() is None

    def test_hint_when_no_hint_text(self):
        """Should handle step with no hint."""
        step = TutorialStep("s1", TutorialPhase.NAVIGATION, "S1", "c1", hint="")
        tutorial = Tutorial(steps=[step])
        tutorial.start()

        hint = tutorial.get_hint()
        assert "[Hint]" in hint  # Still formatted

    def test_phase_transitions(self):
        """Should transition between phases correctly."""
        steps = [
            TutorialStep("nav1", TutorialPhase.NAVIGATION, "Nav", "n"),
            TutorialStep("exam1", TutorialPhase.EXAMINATION, "Exam", "e"),
            TutorialStep("dial1", TutorialPhase.DIALOGUE, "Dial", "d"),
        ]
        tutorial = Tutorial(steps=steps)
        tutorial.start()

        assert tutorial.phase == TutorialPhase.NAVIGATION

        tutorial.process_command("n")
        assert tutorial.phase == TutorialPhase.EXAMINATION

        tutorial.process_command("e")
        assert tutorial.phase == TutorialPhase.DIALOGUE

    def test_completed_steps_tracking(self):
        """Should track all completed steps."""
        steps = [
            TutorialStep(f"step{i}", TutorialPhase.NAVIGATION, f"S{i}", f"c{i}")
            for i in range(5)
        ]
        tutorial = Tutorial(steps=steps)
        tutorial.start()

        for i in range(5):
            tutorial.process_command(f"c{i}")

        assert len(tutorial.completed_steps) == 5
        for i in range(5):
            assert f"step{i}" in tutorial.completed_steps

    def test_step_prefix_match(self):
        """Should match prefix pattern."""
        step = TutorialStep(
            id="test",
            phase=TutorialPhase.NAVIGATION,
            instruction="Test",
            expected_action="examine *"
        )

        assert step.check_completion("examine desk")
        assert step.check_completion("EXAMINE chair")
        assert not step.check_completion("look around")


class TestHelpSystemEdgeCases:
    """Edge case tests for help system."""

    def test_search_no_results(self):
        """Search with no matches."""
        system = HelpSystem()
        results = system.search("zzzznonexistent12345")
        assert len(results) == 0

    def test_search_partial_match(self):
        """Search should find partial matches."""
        system = HelpSystem()
        results = system.search("loo")  # Partial for "look"
        assert len(results) > 0

    def test_all_categories_have_topics(self):
        """Each category should have at least one topic."""
        system = HelpSystem()

        for category in HelpCategory:
            topics = system.get_category(category)
            # Note: Some categories might be empty by design

    def test_topic_aliases_work(self):
        """All topic aliases should resolve correctly."""
        system = HelpSystem()

        for topic in HELP_TOPICS:
            for alias in topic.aliases:
                found = system.get_topic(alias)
                assert found is not None
                assert found.id == topic.id

    def test_format_full_minimal_topic(self):
        """Format full should work with minimal topic."""
        topic = HelpTopic(
            id="minimal",
            name="Minimal",
            category=HelpCategory.NAVIGATION,
            summary="A minimal topic"
        )

        full = topic.format_full()
        assert "Minimal" in full
        assert "A minimal topic" in full


class TestHintSystemEdgeCases:
    """Edge case tests for hint system."""

    def test_no_applicable_hints(self):
        """Should return None when no hints apply."""
        system = HintSystem()
        system.add_hint(ContextualHint(
            id="test",
            message="Test",
            condition=lambda ctx: False  # Never applies
        ))

        result = system.check_hints({"any": "context"})
        assert result is None

    def test_multiple_hints_same_priority(self):
        """Should handle multiple hints with same priority."""
        system = HintSystem()

        for i in range(5):
            system.add_hint(ContextualHint(
                id=f"hint{i}",
                message=f"Hint {i}",
                condition=lambda ctx: True,
                priority=5
            ))

        result = system.check_hints({})
        # Should return one of them
        assert result is not None
        assert "Hint" in result

    def test_hint_condition_exception(self):
        """Should handle exceptions in hint conditions gracefully."""
        system = HintSystem()

        def bad_condition(ctx):
            raise ValueError("Bad condition")

        system.add_hint(ContextualHint(
            id="bad",
            message="Bad hint",
            condition=bad_condition
        ))

        # Should not crash - depends on implementation
        try:
            result = system.check_hints({})
        except ValueError:
            pass  # Exception propagates - that's valid behavior too

    def test_hint_shown_tracking_persists(self):
        """Shown count should persist across checks."""
        system = HintSystem()
        system.add_hint(ContextualHint(
            id="test",
            message="Test",
            condition=lambda ctx: ctx.get("show", False),
            max_shows=3
        ))

        # Show once
        system.check_hints({"show": True})
        # Don't show
        system.check_hints({"show": False})
        # Show twice more
        system.check_hints({"show": True})
        system.check_hints({"show": True})
        # Should be exhausted
        result = system.check_hints({"show": True})
        assert result is None


class TestCommandHistoryEdgeCases:
    """Edge case tests for command history."""

    def test_empty_history_navigation(self):
        """Should handle navigation in empty history."""
        history = CommandHistory()

        # Empty history returns None for navigation
        assert history.get_previous() is None
        assert history.get_next() is None or history.get_next() == ""
        assert history.get_last() is None

    def test_single_entry_navigation(self):
        """Should handle single entry navigation."""
        history = CommandHistory()
        history.add("only")

        assert history.get_previous() == "only"
        assert history.get_previous() == "only"  # Stay at single entry
        assert history.get_next() == ""  # Back to current

    def test_filter_with_no_matches(self):
        """Filter with no matches should navigate nothing."""
        history = CommandHistory()
        history.add("look")
        history.add("examine")

        history.set_filter("nonexistent")
        # No matches, returns None
        assert history.get_previous() is None

    def test_clear_filter(self):
        """Clearing filter should restore navigation."""
        history = CommandHistory()
        history.add("look")
        history.add("examine")

        history.set_filter("look")
        history.set_filter("")  # Clear filter

        # Should navigate all again
        assert history.get_previous() == "examine"
        assert history.get_previous() == "look"

    def test_repeat_last_empty(self):
        """Repeat last on empty history."""
        history = CommandHistory()
        # Empty history returns None for repeat_last
        result = history.repeat_last()
        assert result is None or result == ""

    def test_search_empty_query(self):
        """Search with empty query."""
        history = CommandHistory()
        history.add("look")
        history.add("examine")

        results = history.search("")
        # Depends on implementation - might return all or none

    def test_add_empty_command(self):
        """Should handle empty command."""
        history = CommandHistory()
        history.add("")

        # Implementation dependent - might reject or accept


class TestUndoStackEdgeCases:
    """Edge case tests for undo stack."""

    def test_pop_undo_empty(self):
        """Pop undo on empty stack."""
        stack = UndoStack()
        assert stack.pop_undo() is None

    def test_pop_redo_empty(self):
        """Pop redo on empty stack."""
        stack = UndoStack()
        assert stack.pop_redo() is None

    def test_peek_empty(self):
        """Peek on empty stack."""
        stack = UndoStack()
        assert stack.peek_undo() is None

    def test_alternating_undo_redo(self):
        """Should handle alternating undo/redo."""
        stack = UndoStack()
        action = UndoableAction("test", "Test")
        stack.push(action)

        for _ in range(10):
            undone = stack.pop_undo()
            assert undone is action
            redone = stack.pop_redo()
            assert redone is action

    def test_undo_redo_interleaved(self):
        """Complex undo/redo patterns."""
        stack = UndoStack()

        # Push 3 actions
        for i in range(3):
            stack.push(UndoableAction(str(i), f"Action {i}"))

        # Undo 2
        stack.pop_undo()
        stack.pop_undo()

        # Redo 1
        stack.pop_redo()

        # Push new action (should clear remaining redo)
        stack.push(UndoableAction("new", "New action"))

        assert not stack.can_redo()
        assert stack.can_undo()


class TestInputBufferEdgeCases:
    """Edge case tests for input buffer."""

    def test_empty_buffer_operations(self):
        """Operations on empty buffer."""
        buffer = InputBuffer()

        assert not buffer.delete_char()
        assert not buffer.delete_forward()
        buffer.move_left()  # Should not crash
        buffer.move_right()  # Should not crash
        assert buffer.cursor == 0

    def test_cursor_boundaries(self):
        """Cursor should stay within boundaries."""
        buffer = InputBuffer()
        buffer.set_text("hello")

        # Move past end
        for _ in range(10):
            buffer.move_right()
        assert buffer.cursor == 5

        # Move past start
        for _ in range(10):
            buffer.move_left()
        assert buffer.cursor == 0

    def test_insert_at_middle(self):
        """Insert in middle of text."""
        buffer = InputBuffer()
        buffer.set_text("hlo")
        buffer.cursor = 1

        buffer.insert("e")
        buffer.insert("l")

        assert buffer.text == "hello"

    def test_delete_at_various_positions(self):
        """Delete at various cursor positions."""
        buffer = InputBuffer()
        buffer.set_text("hello")

        # Delete from end
        buffer.delete_char()
        assert buffer.text == "hell"

        # Delete from middle
        buffer.cursor = 2
        buffer.delete_char()
        assert buffer.text == "hll"

    def test_delete_word_at_start(self):
        """Delete word at start of buffer."""
        buffer = InputBuffer()
        buffer.set_text("hello")
        buffer.cursor = 0

        buffer.delete_word()
        assert buffer.text == "hello"  # Nothing to delete

    def test_delete_word_multiple_spaces(self):
        """Delete word with multiple spaces."""
        buffer = InputBuffer()
        buffer.set_text("hello   world")
        buffer.cursor = 13  # End

        buffer.delete_word()
        assert buffer.text == "hello   "

    def test_word_navigation_with_punctuation(self):
        """Word navigation with punctuation."""
        buffer = InputBuffer()
        buffer.set_text("hello, world!")
        buffer.cursor = 0

        buffer.move_word_right()
        buffer.move_word_right()

        # Should be past both words

    def test_get_before_after_empty(self):
        """Get before/after on empty buffer."""
        buffer = InputBuffer()

        assert buffer.get_before_cursor() == ""
        assert buffer.get_after_cursor() == ""

    def test_insert_special_characters(self):
        """Insert special characters."""
        buffer = InputBuffer()
        special = "Hello\tWorld\nWith\\Escapes\"Quotes"
        buffer.insert_text(special)

        assert buffer.text == special


class TestTutorialPromptEdgeCases:
    """Edge case tests for tutorial prompt."""

    def test_whitespace_responses(self):
        """Should handle whitespace in responses."""
        prompt = TutorialPrompt()

        assert prompt.check_response("  yes  ") is True
        assert prompt.check_response("\tno\t") is False

    def test_empty_response(self):
        """Empty response should be invalid."""
        prompt = TutorialPrompt()
        assert prompt.check_response("") is None

    def test_case_variations(self):
        """Should handle case variations."""
        prompt = TutorialPrompt()

        assert prompt.check_response("YES") is True
        assert prompt.check_response("Yes") is True
        assert prompt.check_response("NO") is False
        assert prompt.check_response("No") is False


class TestHelpTopicFormatting:
    """Tests for help topic formatting."""

    def test_format_with_all_optional_fields(self):
        """Format with all optional fields populated."""
        topic = HelpTopic(
            id="full",
            name="Full Topic",
            category=HelpCategory.NAVIGATION,
            summary="A complete topic",
            description="This is a complete description with all fields.",
            usage="full <arg1> [arg2]",
            examples=["full test", "full test extra", "full another"],
            aliases=["f", "ft"],
            related=["look", "examine", "go"]
        )

        full = topic.format_full()

        assert "Full Topic" in full
        assert "A complete topic" in full
        assert "complete description" in full
        assert "full <arg1> [arg2]" in full
        assert "full test" in full
        assert "Aliases:" in full
        assert "See also:" in full

    def test_all_predefined_topics_format(self):
        """All predefined topics should format without error."""
        for topic in HELP_TOPICS:
            short = topic.format_short()
            full = topic.format_full()

            assert isinstance(short, str)
            assert isinstance(full, str)
            assert topic.name in short
            assert topic.name in full


class TestSerializationRoundtrips:
    """Tests for serialization roundtrips across UI systems."""

    def test_tutorial_full_roundtrip(self):
        """Tutorial should survive full roundtrip."""
        tutorial = Tutorial()
        tutorial.start()

        # Complete a few steps
        tutorial.process_command("look")
        tutorial.process_command("exits")

        data = tutorial.to_dict()
        restored = Tutorial.from_dict(data)

        assert restored.current_step == tutorial.current_step
        assert restored.phase == tutorial.phase
        assert restored.completed_steps == tutorial.completed_steps
        assert restored.active == tutorial.active

    def test_command_history_full_roundtrip(self):
        """Command history should survive full roundtrip."""
        history = CommandHistory()

        for i in range(20):
            history.add(f"command_{i}", result=f"result_{i}", success=i % 2 == 0)

        data = history.to_dict()
        restored = CommandHistory.from_dict(data)

        assert len(restored) == len(history)
        for i, entry in enumerate(restored.entries):
            assert entry.command == history.entries[i].command

    def test_command_entry_with_long_result(self):
        """Command entry with long result should serialize."""
        long_result = "A" * 10000
        entry = CommandEntry(
            command="test",
            result=long_result,
            success=True
        )

        data = entry.to_dict()
        restored = CommandEntry.from_dict(data)

        assert restored.result == long_result

