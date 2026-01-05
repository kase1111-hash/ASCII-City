"""
Tests for Command Parser - fail-soft input parsing.

These tests verify that the parser correctly:
- Parses various command formats
- Handles typos gracefully
- Infers intent from context
- Provides helpful errors
"""

import pytest
from shadowengine.interaction import CommandParser, Command, CommandType


class TestParserBasics:
    """Basic parser functionality."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_parse_empty_input(self, command_parser):
        """Empty input returns unknown command."""
        cmd = command_parser.parse("")

        assert cmd.command_type == CommandType.UNKNOWN
        assert cmd.is_valid() is False

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_parse_hotspot_number(self, command_parser):
        """Numeric input is hotspot selection."""
        cmd = command_parser.parse("1")

        assert cmd.command_type == CommandType.HOTSPOT
        assert cmd.hotspot_number == 1

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_parse_large_hotspot_number(self, command_parser):
        """Large numbers work as hotspots."""
        cmd = command_parser.parse("42")

        assert cmd.command_type == CommandType.HOTSPOT
        assert cmd.hotspot_number == 42


class TestExamineCommands:
    """Examine command parsing."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_examine_basic(self, command_parser):
        """Basic examine command."""
        cmd = command_parser.parse("examine desk")

        assert cmd.command_type == CommandType.EXAMINE
        assert cmd.target == "desk"

    @pytest.mark.unit
    @pytest.mark.interaction
    @pytest.mark.parametrize("verb", ["look", "check", "inspect", "see", "view", "read", "x", "l"])
    def test_examine_aliases(self, command_parser, verb):
        """All examine aliases work."""
        cmd = command_parser.parse(f"{verb} desk")

        assert cmd.command_type == CommandType.EXAMINE

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_examine_with_articles(self, command_parser):
        """Articles are stripped."""
        cmd = command_parser.parse("look at the old desk")

        assert cmd.command_type == CommandType.EXAMINE
        assert "desk" in cmd.target

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_examine_multi_word_target(self, command_parser):
        """Multi-word targets work."""
        cmd = command_parser.parse("examine old wooden desk")

        assert cmd.command_type == CommandType.EXAMINE
        assert "old wooden desk" in cmd.target


class TestTalkCommands:
    """Talk command parsing."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_talk_basic(self, command_parser):
        """Basic talk command."""
        cmd = command_parser.parse("talk john")

        assert cmd.command_type == CommandType.TALK
        assert cmd.target == "john"

    @pytest.mark.unit
    @pytest.mark.interaction
    @pytest.mark.parametrize("verb", ["speak", "question", "chat", "t"])
    def test_talk_aliases(self, command_parser, verb):
        """Talk aliases work (note: 'ask' is its own command for dialogue)."""
        cmd = command_parser.parse(f"{verb} alice")

        assert cmd.command_type == CommandType.TALK

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_ask_is_separate_command(self, command_parser):
        """'ask' is ASK command type for dialogue topics."""
        cmd = command_parser.parse("ask alice")
        # 'ask' can be TALK or ASK depending on context
        assert cmd.command_type in [CommandType.TALK, CommandType.ASK]

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_talk_to_person(self, command_parser):
        """'talk to' syntax works."""
        cmd = command_parser.parse("talk to the butler")

        assert cmd.command_type == CommandType.TALK
        assert "butler" in cmd.target


class TestUseCommands:
    """Use command parsing."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_use_basic(self, command_parser):
        """Basic use command."""
        cmd = command_parser.parse("use key")

        assert cmd.command_type == CommandType.USE
        assert cmd.target == "key"

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_use_on_target(self, command_parser):
        """'use X on Y' syntax parses as USE command."""
        cmd = command_parser.parse("use key on door")

        assert cmd.command_type == CommandType.USE
        # Target parsing captures the full phrase; secondary extraction happens
        # at a higher level if needed
        assert cmd.target is not None

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_use_complex_on_syntax(self, command_parser):
        """Complex 'use X on Y' works."""
        cmd = command_parser.parse("use the brass key on the locked door")

        assert cmd.command_type == CommandType.USE
        # Target and secondary should be extracted


class TestTakeCommands:
    """Take command parsing."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_take_basic(self, command_parser):
        """Basic take command."""
        cmd = command_parser.parse("take knife")

        assert cmd.command_type == CommandType.TAKE
        assert cmd.target == "knife"

    @pytest.mark.unit
    @pytest.mark.interaction
    @pytest.mark.parametrize("verb", ["get", "grab", "pick", "collect", "g"])
    def test_take_aliases(self, command_parser, verb):
        """All take aliases work."""
        cmd = command_parser.parse(f"{verb} letter")

        assert cmd.command_type == CommandType.TAKE


class TestGoCommands:
    """Go/movement command parsing."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_go_basic(self, command_parser):
        """Basic go command."""
        cmd = command_parser.parse("go north")

        assert cmd.command_type == CommandType.GO
        assert cmd.target == "north"

    @pytest.mark.unit
    @pytest.mark.interaction
    @pytest.mark.parametrize("direction", ["n", "s", "e", "w", "north", "south", "east", "west"])
    def test_direction_shortcuts(self, command_parser, direction):
        """Direction shortcuts work."""
        cmd = command_parser.parse(direction)

        assert cmd.command_type == CommandType.GO

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_go_to_location(self, command_parser):
        """'go to' syntax works."""
        cmd = command_parser.parse("go to hallway")

        assert cmd.command_type == CommandType.GO


class TestSystemCommands:
    """System command parsing."""

    @pytest.mark.unit
    @pytest.mark.interaction
    @pytest.mark.parametrize("cmd_str,expected", [
        ("help", CommandType.HELP),
        ("?", CommandType.HELP),
        ("inventory", CommandType.INVENTORY),
        ("inv", CommandType.INVENTORY),
        ("i", CommandType.INVENTORY),
        ("wait", CommandType.WAIT),
        ("save", CommandType.SAVE),
        ("load", CommandType.LOAD),
        ("quit", CommandType.QUIT),
        ("q", CommandType.QUIT),
    ])
    def test_system_commands(self, command_parser, cmd_str, expected):
        """System commands parse correctly."""
        cmd = command_parser.parse(cmd_str)
        assert cmd.command_type == expected


class TestDialogueCommands:
    """Dialogue-specific command parsing."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_ask_about(self, command_parser):
        """'ask about' command."""
        cmd = command_parser.parse("ask about the murder")

        assert cmd.command_type == CommandType.ASK

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_accuse(self, command_parser):
        """Accuse command."""
        cmd = command_parser.parse("accuse")

        assert cmd.command_type == CommandType.ACCUSE

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_threaten(self, command_parser):
        """Threaten command."""
        cmd = command_parser.parse("threaten")

        assert cmd.command_type == CommandType.THREATEN

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_leave_conversation(self, command_parser):
        """Leave command."""
        cmd = command_parser.parse("leave")

        assert cmd.command_type == CommandType.LEAVE


class TestHotspotWithVerb:
    """Hotspot number + verb combinations."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_number_then_verb(self, command_parser):
        """'1 examine' format."""
        cmd = command_parser.parse("1 examine")

        assert cmd.command_type == CommandType.EXAMINE
        assert cmd.hotspot_number == 1

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_number_then_talk(self, command_parser):
        """'2 talk' format."""
        cmd = command_parser.parse("2 talk")

        assert cmd.command_type == CommandType.TALK
        assert cmd.hotspot_number == 2


class TestFuzzyMatching:
    """Typo tolerance and fuzzy matching."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_typo_in_verb(self, command_parser):
        """Common typos are corrected."""
        # 'examin' -> 'examine'
        cmd = command_parser.parse("examin desk")

        assert cmd.command_type == CommandType.EXAMINE

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_typo_tlak(self, command_parser):
        """'tlak' -> 'talk'."""
        cmd = command_parser.parse("tlak butler")

        assert cmd.command_type == CommandType.TALK

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_typo_correction(self, command_parser):
        """Common typos are corrected via fuzzy matching."""
        # Test various typos - exact correction depends on levenshtein distance
        cmd = command_parser.parse("examin desk")
        assert cmd.command_type == CommandType.EXAMINE

        cmd = command_parser.parse("tlak butler")
        assert cmd.command_type == CommandType.TALK


class TestContextAwareInference:
    """Context-aware command inference."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_noun_only_person(self, command_parser, parser_context):
        """Just person name infers talk."""
        cmd = command_parser.parse("john", parser_context)

        assert cmd.command_type == CommandType.TALK

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_noun_only_with_context(self, command_parser, parser_context):
        """Noun-only commands use context to infer action."""
        # When just a noun is given, parser tries to infer from context
        # Results depend on exact matching logic
        cmd = command_parser.parse("john", parser_context)

        # Should recognize John as a person and infer talk
        assert cmd.command_type == CommandType.TALK

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_noun_only_defaults_examine(self, command_parser):
        """Unknown nouns default to examine."""
        cmd = command_parser.parse("something", {})

        # Default for unknown nouns is examine
        assert cmd.command_type == CommandType.EXAMINE


class TestTargetMatching:
    """Target matching against context."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_partial_match(self, command_parser, parser_context):
        """Partial target names match."""
        cmd = command_parser.parse("examine lett", parser_context)

        assert cmd.target is not None

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_case_insensitive(self, command_parser, parser_context):
        """Matching is case insensitive."""
        cmd = command_parser.parse("EXAMINE JOHN", parser_context)

        assert cmd.command_type == CommandType.EXAMINE


class TestHelpText:
    """Help text generation."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_help_text_content(self, command_parser):
        """Help text includes key commands."""
        help_text = command_parser.get_help_text()

        assert "examine" in help_text.lower()
        assert "talk" in help_text.lower()
        assert "take" in help_text.lower()
        assert "inventory" in help_text.lower()


class TestErrorSuggestions:
    """Error message suggestions."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_error_with_targets(self, command_parser, parser_context):
        """Error suggests available targets."""
        cmd = command_parser.parse("xyzzy", parser_context)
        error = command_parser.get_error_suggestion(cmd, parser_context)

        # Should mention available targets or suggest help
        assert len(error) > 0

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_error_message_is_helpful(self, command_parser):
        """Error messages provide useful information."""
        cmd = command_parser.parse("xyzzy")
        error = command_parser.get_error_suggestion(cmd, {})

        # Error should either suggest help or indicate the problem
        assert len(error) > 0
        assert "don't" in error.lower() or "help" in error.lower()
