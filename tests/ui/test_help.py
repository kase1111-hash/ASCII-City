"""Tests for the help system."""

import pytest
from src.shadowengine.ui.help import (
    HelpCategory, HelpTopic, HelpSystem,
    ContextualHint, HintSystem,
    HELP_TOPICS, create_standard_hints
)


class TestHelpTopic:
    """Tests for HelpTopic."""

    def test_creation(self):
        """Should create a help topic."""
        topic = HelpTopic(
            id="test",
            name="Test Command",
            category=HelpCategory.NAVIGATION,
            summary="A test command"
        )
        assert topic.id == "test"
        assert topic.category == HelpCategory.NAVIGATION

    def test_format_short(self):
        """Should format short help."""
        topic = HelpTopic(
            id="test",
            name="Test",
            category=HelpCategory.NAVIGATION,
            summary="Test summary"
        )

        short = topic.format_short()
        assert "Test" in short
        assert "Test summary" in short

    def test_format_full(self):
        """Should format full help."""
        topic = HelpTopic(
            id="test",
            name="Test",
            category=HelpCategory.NAVIGATION,
            summary="Test summary",
            description="Full description",
            usage="test <arg>",
            examples=["test foo", "test bar"],
            aliases=["t"],
            related=["other"]
        )

        full = topic.format_full()
        assert "Test" in full
        assert "Test summary" in full
        assert "Full description" in full
        assert "Usage:" in full
        assert "test <arg>" in full
        assert "Examples:" in full
        assert "test foo" in full
        assert "Aliases:" in full
        assert "See also:" in full


class TestPredefinedTopics:
    """Tests for predefined help topics."""

    def test_topics_exist(self):
        """Should have predefined topics."""
        assert len(HELP_TOPICS) > 0

    def test_navigation_topics(self):
        """Should have navigation topics."""
        nav_topics = [t for t in HELP_TOPICS if t.category == HelpCategory.NAVIGATION]
        assert len(nav_topics) > 0

    def test_topics_have_content(self):
        """All topics should have required fields."""
        for topic in HELP_TOPICS:
            assert topic.id
            assert topic.name
            assert topic.summary


class TestHelpSystem:
    """Tests for HelpSystem."""

    def test_creation(self):
        """Should create help system."""
        system = HelpSystem()
        assert len(system.topics) > 0

    def test_get_topic_by_id(self):
        """Should get topic by ID."""
        system = HelpSystem()
        topic = system.get_topic("look")
        assert topic is not None
        assert topic.id == "look"

    def test_get_topic_by_alias(self):
        """Should get topic by alias."""
        system = HelpSystem()
        topic = system.get_topic("l")  # Alias for look
        assert topic is not None
        assert topic.id == "look"

    def test_get_topic_not_found(self):
        """Should return None for unknown topic."""
        system = HelpSystem()
        topic = system.get_topic("nonexistent")
        assert topic is None

    def test_search(self):
        """Should search topics."""
        system = HelpSystem()
        results = system.search("look")
        assert len(results) > 0

    def test_get_category(self):
        """Should get topics by category."""
        system = HelpSystem()
        nav = system.get_category(HelpCategory.NAVIGATION)
        assert len(nav) > 0
        for topic in nav:
            assert topic.category == HelpCategory.NAVIGATION

    def test_get_all_commands(self):
        """Should get list of all commands."""
        system = HelpSystem()
        commands = system.get_all_commands()
        assert "look" in commands
        assert "l" in commands  # Alias

    def test_format_command_list(self):
        """Should format command list."""
        system = HelpSystem()
        output = system.format_command_list()
        assert "Available Commands" in output
        assert "Navigation" in output

    def test_format_quick_reference(self):
        """Should format quick reference."""
        system = HelpSystem()
        ref = system.format_quick_reference()
        assert "Quick Reference" in ref
        assert "MOVEMENT" in ref


class TestContextualHint:
    """Tests for ContextualHint."""

    def test_creation(self):
        """Should create a hint."""
        hint = ContextualHint(
            id="test",
            message="Test hint",
            condition=lambda ctx: True
        )
        assert hint.id == "test"
        assert not hint.shown

    def test_condition_check(self):
        """Condition should determine applicability."""
        hint = ContextualHint(
            id="test",
            message="Test",
            condition=lambda ctx: ctx.get("value", 0) > 5
        )

        # Condition not met
        assert not hint.condition({"value": 3})
        # Condition met
        assert hint.condition({"value": 10})


class TestHintSystem:
    """Tests for HintSystem."""

    def test_creation(self):
        """Should create hint system."""
        system = HintSystem()
        assert len(system.hints) == 0

    def test_add_hint(self):
        """Should add hint."""
        system = HintSystem()
        hint = ContextualHint(
            id="test",
            message="Test hint",
            condition=lambda ctx: True
        )

        system.add_hint(hint)
        assert len(system.hints) == 1

    def test_check_hints(self):
        """Should return applicable hint."""
        system = HintSystem()
        system.add_hint(ContextualHint(
            id="test",
            message="Test message",
            condition=lambda ctx: ctx.get("trigger", False)
        ))

        # Not triggered
        result = system.check_hints({"trigger": False})
        assert result is None

        # Triggered
        result = system.check_hints({"trigger": True})
        assert result == "Test message"

    def test_max_shows(self):
        """Should respect max shows."""
        system = HintSystem()
        system.add_hint(ContextualHint(
            id="test",
            message="Test",
            condition=lambda ctx: True,
            max_shows=2
        ))

        # First show
        assert system.check_hints({}) == "Test"
        # Second show
        assert system.check_hints({}) == "Test"
        # Third show - should be None
        assert system.check_hints({}) is None

    def test_priority_ordering(self):
        """Should return highest priority hint."""
        system = HintSystem()
        system.add_hint(ContextualHint(
            id="low",
            message="Low priority",
            condition=lambda ctx: True,
            priority=1
        ))
        system.add_hint(ContextualHint(
            id="high",
            message="High priority",
            condition=lambda ctx: True,
            priority=10
        ))

        result = system.check_hints({})
        assert result == "High priority"

    def test_reset(self):
        """Should reset shown counts."""
        system = HintSystem()
        system.add_hint(ContextualHint(
            id="test",
            message="Test",
            condition=lambda ctx: True,
            max_shows=1
        ))

        system.check_hints({})
        assert system.check_hints({}) is None

        system.reset()
        assert system.check_hints({}) == "Test"


class TestCreateStandardHints:
    """Tests for create_standard_hints."""

    def test_creates_hints(self):
        """Should create standard hints."""
        hints = create_standard_hints()
        assert len(hints) > 0

    def test_hints_have_conditions(self):
        """All hints should have conditions."""
        hints = create_standard_hints()
        for hint in hints:
            assert hint.condition is not None
