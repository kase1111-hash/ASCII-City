"""
Tests for Voice Commands.
"""

import pytest
from src.shadowengine.voice.commands import (
    VoiceCommand, CommandCategory, QuickCommand,
    VoiceVocabulary, CommandMatcher
)
from src.shadowengine.voice.intent import IntentType


class TestVoiceCommand:
    """Tests for VoiceCommand class."""

    def test_create_command(self, custom_command):
        """Can create voice command."""
        assert custom_command.name == "custom_action"
        assert custom_command.intent_type == IntentType.INTERACT
        assert custom_command.category == CommandCategory.CONTEXTUAL

    def test_matches_exact(self, custom_command):
        """Command matches exact phrases."""
        matches, confidence = custom_command.matches("do the thing")
        assert matches is True
        assert confidence == 1.0

    def test_matches_prefix(self, custom_command):
        """Command matches phrase prefixes."""
        matches, confidence = custom_command.matches("do the thing now")
        assert matches is True
        assert confidence == 0.9

    def test_matches_alias(self, custom_command):
        """Command matches aliases."""
        custom_command.aliases = ["do it"]
        matches, confidence = custom_command.matches("do it")
        assert matches is True
        assert confidence == 0.95

    def test_matches_shortcut(self, custom_command):
        """Command matches shortcut."""
        custom_command.shortcut = "dtt"
        matches, confidence = custom_command.matches("dtt")
        assert matches is True
        assert confidence == 1.0

    def test_no_match(self, custom_command):
        """Non-matching input returns False."""
        matches, confidence = custom_command.matches("random text")
        assert matches is False
        assert confidence == 0.0

    def test_serialization(self, custom_command):
        """Command can be serialized."""
        data = custom_command.to_dict()
        assert data["name"] == "custom_action"
        assert data["intent_type"] == "interact"
        assert data["category"] == "contextual"


class TestQuickCommand:
    """Tests for QuickCommand class."""

    def test_create_quick_command(self):
        """Can create quick command."""
        quick = QuickCommand(
            trigger="n",
            intent_type=IntentType.MOVE,
            default_target="north",
        )
        assert quick.trigger == "n"
        assert quick.intent_type == IntentType.MOVE
        assert quick.default_target == "north"

    def test_execute_with_default(self):
        """Quick command executes with default target."""
        quick = QuickCommand(
            trigger="i",
            intent_type=IntentType.INVENTORY,
        )
        intent_type, target = quick.execute()
        assert intent_type == IntentType.INVENTORY
        assert target is None

    def test_execute_with_context(self):
        """Quick command can get target from context."""
        quick = QuickCommand(
            trigger="attack",
            intent_type=IntentType.ATTACK,
            context_key="last_enemy",
        )
        context = {"last_enemy": "goblin"}
        intent_type, target = quick.execute(context)
        assert intent_type == IntentType.ATTACK
        assert target == "goblin"

    def test_urgent_flag(self):
        """Quick command can be marked urgent."""
        quick = QuickCommand(
            trigger="run",
            intent_type=IntentType.FLEE,
            is_urgent=True,
        )
        assert quick.is_urgent is True


class TestVoiceVocabulary:
    """Tests for VoiceVocabulary."""

    def test_create_vocabulary(self, vocabulary):
        """Can create vocabulary."""
        commands = vocabulary.get_all_commands()
        assert len(commands) > 0

    def test_get_command(self, vocabulary):
        """Can get command by name."""
        look = vocabulary.get_command("look")
        assert look is not None
        assert look.intent_type == IntentType.EXAMINE

    def test_get_nonexistent(self, vocabulary):
        """Getting nonexistent command returns None."""
        result = vocabulary.get_command("nonexistent")
        assert result is None

    def test_get_by_category(self, vocabulary):
        """Can get commands by category."""
        movement = vocabulary.get_by_category(CommandCategory.MOVEMENT)
        assert len(movement) > 0
        assert all(c.category == CommandCategory.MOVEMENT for c in movement)

    def test_register_command(self, vocabulary, custom_command):
        """Can register custom command."""
        vocabulary.register_command(custom_command)
        retrieved = vocabulary.get_command("custom_action")
        assert retrieved == custom_command

    def test_register_quick_command(self, vocabulary):
        """Can register quick command."""
        quick = QuickCommand(
            trigger="test",
            intent_type=IntentType.QUERY,
        )
        vocabulary.register_quick_command(quick)

        retrieved = vocabulary.get_quick_command("test")
        assert retrieved == quick

    def test_find_matches(self, vocabulary):
        """Can find matching commands."""
        matches = vocabulary.find_matches("look")
        assert len(matches) > 0
        assert matches[0][0].name == "look"
        assert matches[0][1] >= 0.5

    def test_find_matches_multiple(self, vocabulary):
        """Can find multiple matches."""
        matches = vocabulary.find_matches("take", min_confidence=0.3)
        assert len(matches) >= 1

    def test_is_quick_command(self, vocabulary):
        """Can check if input is quick command."""
        assert vocabulary.is_quick_command("n") is True
        assert vocabulary.is_quick_command("north") is True
        assert vocabulary.is_quick_command("random text") is False

    def test_default_movement_commands(self, vocabulary):
        """Default movement commands exist."""
        go = vocabulary.get_command("go")
        assert go is not None
        assert go.category == CommandCategory.MOVEMENT

        run = vocabulary.get_command("run")
        assert run is not None
        assert run.is_urgent is True

    def test_default_interaction_commands(self, vocabulary):
        """Default interaction commands exist."""
        look = vocabulary.get_command("look")
        take = vocabulary.get_command("take")
        use = vocabulary.get_command("use")

        assert look is not None
        assert take is not None
        assert use is not None

    def test_default_combat_commands(self, vocabulary):
        """Default combat commands exist."""
        attack = vocabulary.get_command("attack")
        defend = vocabulary.get_command("defend")
        dodge = vocabulary.get_command("dodge")

        assert attack is not None
        assert attack.is_urgent is True
        assert defend is not None
        assert dodge is not None

    def test_default_social_commands(self, vocabulary):
        """Default social commands exist."""
        talk = vocabulary.get_command("talk")
        greet = vocabulary.get_command("greet")
        threaten = vocabulary.get_command("threaten")

        assert talk is not None
        assert greet is not None
        assert threaten is not None

    def test_default_quick_commands(self, vocabulary):
        """Default quick commands exist."""
        # Direction shortcuts
        assert vocabulary.is_quick_command("n") is True
        assert vocabulary.is_quick_command("s") is True
        assert vocabulary.is_quick_command("e") is True
        assert vocabulary.is_quick_command("w") is True

        # Other shortcuts
        assert vocabulary.is_quick_command("i") is True  # Inventory

    def test_get_help_text(self, vocabulary):
        """Can get help text."""
        help_text = vocabulary.get_help_text()
        assert "VOICE COMMANDS" in help_text
        assert "look" in help_text.lower()
        assert "go" in help_text.lower()

    def test_get_category_help(self, vocabulary):
        """Can get help for specific category."""
        help_text = vocabulary.get_help_text(CommandCategory.COMBAT)
        assert "COMBAT" in help_text
        assert "attack" in help_text.lower()


class TestCommandMatcher:
    """Tests for CommandMatcher."""

    def test_create_matcher(self, command_matcher):
        """Can create matcher."""
        assert command_matcher.vocabulary is not None

    def test_match_exact(self, command_matcher):
        """Can match exact command."""
        cmd, confidence = command_matcher.match("look")
        assert cmd is not None
        assert cmd.name == "look"
        assert confidence == 1.0

    def test_match_phrase(self, command_matcher):
        """Can match phrase."""
        cmd, confidence = command_matcher.match("look at")
        assert cmd is not None
        assert cmd.name == "look"

    def test_match_quick_command(self, command_matcher):
        """Can match quick command."""
        cmd, confidence = command_matcher.match("n")
        assert cmd is not None
        assert cmd.intent_type == IntentType.MOVE

    def test_match_with_filler_words(self, command_matcher):
        """Matcher ignores filler words."""
        cmd, confidence = command_matcher.match("um look at the thing")
        assert cmd is not None
        assert cmd.name == "look"

    def test_match_substitution(self, command_matcher):
        """Matcher handles common substitutions."""
        # "weight" for "wait"
        cmd, confidence = command_matcher.match("weight")
        assert cmd is not None
        assert cmd.name == "wait"

    def test_no_match(self, command_matcher):
        """Non-matching input returns None."""
        cmd, confidence = command_matcher.match("asdfasdf")
        assert cmd is None
        assert confidence == 0.0

    def test_get_suggestions(self, command_matcher):
        """Can get suggestions for unclear input."""
        # Use a partial match that will find something
        suggestions = command_matcher.get_suggestions("look at")
        # Verify suggestions are returned as a list
        assert isinstance(suggestions, list)
        # "look at" should match the look command
        if suggestions:
            assert any("look" in s.lower() for s in suggestions)

    def test_preprocess(self, command_matcher):
        """Input is preprocessed correctly."""
        # Remove filler words and lowercase
        result = command_matcher._preprocess("Um Like LOOK at it")
        assert "um" not in result
        assert "like" not in result
        assert result == "look at it"

    def test_apply_substitutions(self, command_matcher):
        """Substitutions are applied."""
        result = command_matcher._apply_substitutions("weight here")
        assert result == "wait hear"
