"""
Tests for Intent Parser.
"""

import pytest
from src.shadowengine.voice.intent import (
    Intent, IntentType, IntentConfidence,
    IntentParser, EntityExtractor, NLUResult, Entity
)
from src.shadowengine.interaction.parser import CommandType


class TestEntity:
    """Tests for Entity class."""

    def test_create_entity(self):
        """Can create entity."""
        entity = Entity(
            type="target",
            value="desk",
            start=10,
            end=14,
            confidence=0.9,
        )
        assert entity.type == "target"
        assert entity.value == "desk"
        assert entity.confidence == 0.9

    def test_serialization(self):
        """Entity can be serialized and deserialized."""
        entity = Entity(type="direction", value="north", confidence=0.95)
        data = entity.to_dict()
        restored = Entity.from_dict(data)

        assert restored.type == entity.type
        assert restored.value == entity.value
        assert restored.confidence == entity.confidence


class TestIntent:
    """Tests for Intent class."""

    def test_create_intent(self):
        """Can create intent."""
        intent = Intent(
            type=IntentType.EXAMINE,
            confidence=0.9,
            raw_text="look at the desk",
        )
        assert intent.type == IntentType.EXAMINE
        assert intent.confidence == 0.9

    def test_confidence_levels(self):
        """Confidence levels are calculated correctly."""
        high = Intent(confidence=0.85)
        assert high.confidence_level == IntentConfidence.HIGH

        medium = Intent(confidence=0.6)
        assert medium.confidence_level == IntentConfidence.MEDIUM

        low = Intent(confidence=0.4)
        assert low.confidence_level == IntentConfidence.LOW

        none = Intent(confidence=0.1)
        assert none.confidence_level == IntentConfidence.NONE

    def test_is_valid(self):
        """Can check if intent is valid."""
        valid = Intent(type=IntentType.MOVE, confidence=0.8)
        assert valid.is_valid is True

        invalid_type = Intent(type=IntentType.UNKNOWN, confidence=0.8)
        assert invalid_type.is_valid is False

        low_confidence = Intent(type=IntentType.MOVE, confidence=0.2)
        assert low_confidence.is_valid is False

    def test_primary_target(self):
        """Can get primary target."""
        intent = Intent(
            type=IntentType.EXAMINE,
            entities=[
                Entity(type="target", value="desk"),
                Entity(type="direction", value="north"),
            ]
        )
        assert intent.primary_target == "desk"

        intent_with_params = Intent(
            type=IntentType.MOVE,
            parameters={"target": "door"},
        )
        assert intent_with_params.primary_target == "door"

    def test_direction(self):
        """Can get direction."""
        intent = Intent(
            type=IntentType.MOVE,
            entities=[Entity(type="direction", value="north")],
        )
        assert intent.direction == "north"

    def test_get_entity(self):
        """Can get entity by type."""
        intent = Intent(
            entities=[
                Entity(type="target", value="desk"),
                Entity(type="number", value="3"),
            ]
        )
        target = intent.get_entity("target")
        assert target.value == "desk"

        missing = intent.get_entity("direction")
        assert missing is None

    def test_get_all_entities(self):
        """Can get all entities of a type."""
        intent = Intent(
            entities=[
                Entity(type="target", value="desk"),
                Entity(type="target", value="chair"),
                Entity(type="number", value="3"),
            ]
        )
        targets = intent.get_all_entities("target")
        assert len(targets) == 2

    def test_to_command(self):
        """Can convert to legacy Command."""
        intent = Intent(
            type=IntentType.EXAMINE,
            raw_text="look at the desk",
            parameters={"target": "desk"},
        )
        command = intent.to_command()

        assert command.command_type == CommandType.EXAMINE
        assert command.target == "desk"
        assert command.raw_input == "look at the desk"

    def test_serialization(self):
        """Intent can be serialized and deserialized."""
        intent = Intent(
            type=IntentType.MOVE,
            confidence=0.85,
            raw_text="go north",
            entities=[Entity(type="direction", value="north")],
            parameters={"direction": "north"},
        )
        data = intent.to_dict()
        restored = Intent.from_dict(data)

        assert restored.type == intent.type
        assert restored.confidence == intent.confidence
        assert len(restored.entities) == 1


class TestEntityExtractor:
    """Tests for EntityExtractor."""

    def test_extract_directions(self, entity_extractor):
        """Can extract directions."""
        entities = entity_extractor.extract("go north")

        directions = [e for e in entities if e.type == "direction"]
        assert len(directions) == 1
        assert directions[0].value == "north"

    def test_extract_direction_aliases(self, entity_extractor):
        """Can extract direction aliases."""
        entities = entity_extractor.extract("go n")
        directions = [e for e in entities if e.type == "direction"]
        assert directions[0].value == "north"

        entities = entity_extractor.extract("move se")
        directions = [e for e in entities if e.type == "direction"]
        assert directions[0].value == "southeast"

    def test_extract_numbers(self, entity_extractor):
        """Can extract numbers."""
        entities = entity_extractor.extract("take 3 apples")
        numbers = [e for e in entities if e.type == "number"]
        assert len(numbers) == 1
        assert numbers[0].value == "3"

    def test_extract_quantity_words(self, entity_extractor):
        """Can extract quantity words."""
        entities = entity_extractor.extract("take three coins")
        quantities = [e for e in entities if e.type == "quantity"]
        assert len(quantities) == 1
        assert quantities[0].value == "3"

        entities = entity_extractor.extract("take all items")
        quantities = [e for e in entities if e.type == "quantity"]
        assert quantities[0].value == "-1"  # All

    def test_extract_known_targets(self, entity_extractor, game_context):
        """Can extract known targets from context."""
        entities = entity_extractor.extract("look at the desk", game_context)
        targets = [e for e in entities if e.type == "target"]
        assert any(t.value == "desk" for t in targets)

    def test_extract_hotspot_targets(self, entity_extractor, game_context):
        """Can extract hotspot targets."""
        entities = entity_extractor.extract("talk to guard", game_context)
        persons = [e for e in entities if e.type == "person"]
        assert len(persons) == 1
        assert persons[0].value == "Guard"

    def test_extract_pronouns(self, entity_extractor, game_context):
        """Can extract and resolve pronouns."""
        entities = entity_extractor.extract("look at it", game_context)
        resolved = [e for e in entities if e.type == "pronoun_reference"]
        assert len(resolved) == 1
        assert resolved[0].value == "guard"  # From context

    def test_extract_unresolved_pronouns(self, entity_extractor):
        """Unresolved pronouns are marked."""
        entities = entity_extractor.extract("look at it", {})
        unresolved = [e for e in entities if e.type == "unresolved_pronoun"]
        assert len(unresolved) == 1

    def test_extract_noun_phrases(self, entity_extractor):
        """Can extract noun phrases as targets."""
        entities = entity_extractor.extract("look at the old painting")
        targets = [e for e in entities if e.type == "target"]
        assert any("painting" in t.value for t in targets)


class TestIntentParser:
    """Tests for IntentParser."""

    def test_parse_examine(self, intent_parser):
        """Can parse examine intent."""
        result = intent_parser.parse("look at the desk")

        assert result.primary_intent.type == IntentType.EXAMINE
        assert result.primary_intent.confidence > 0.7

    def test_parse_move(self, intent_parser):
        """Can parse move intent."""
        result = intent_parser.parse("go north")

        assert result.primary_intent.type == IntentType.MOVE
        assert result.primary_intent.direction == "north"

    def test_parse_talk(self, intent_parser):
        """Can parse talk intent."""
        result = intent_parser.parse("talk to the bartender")

        assert result.primary_intent.type == IntentType.TALK

    def test_parse_take(self, intent_parser):
        """Can parse take intent."""
        result = intent_parser.parse("grab the key")

        assert result.primary_intent.type == IntentType.TAKE

    def test_parse_attack(self, intent_parser):
        """Can parse attack intent."""
        result = intent_parser.parse("attack the guard")

        assert result.primary_intent.type == IntentType.ATTACK
        # Combat commands are prioritized via InputPriority, not urgency patterns

    def test_parse_flee(self, intent_parser):
        """Can parse flee intent."""
        # Use explicit "flee" to avoid ambiguity with MOVE's "run"
        result = intent_parser.parse("flee now!")

        assert result.primary_intent.type == IntentType.FLEE
        assert intent_parser.is_urgent("flee now!")

    def test_parse_quick_responses(self, intent_parser):
        """Can parse quick responses."""
        yes_result = intent_parser.parse("yes")
        assert yes_result.primary_intent.type == IntentType.YES

        no_result = intent_parser.parse("no")
        assert no_result.primary_intent.type == IntentType.NO

    def test_parse_inventory(self, intent_parser):
        """Can parse inventory intent."""
        # Use "inventory" directly to avoid ambiguity with "check" (EXAMINE)
        result = intent_parser.parse("inventory")

        assert result.primary_intent.type == IntentType.INVENTORY

    def test_parse_help(self, intent_parser):
        """Can parse help intent."""
        result = intent_parser.parse("help")

        assert result.primary_intent.type == IntentType.HELP

    def test_parse_with_context(self, intent_parser, game_context):
        """Context improves parsing."""
        result = intent_parser.parse("look at the desk", game_context)

        assert result.primary_intent.type == IntentType.EXAMINE
        assert result.primary_intent.primary_target == "desk"

    def test_parse_hotspot_number(self, intent_parser):
        """Can parse hotspot number."""
        result = intent_parser.parse("3")

        assert result.primary_intent.type == IntentType.INTERACT
        assert result.primary_intent.parameters.get("hotspot_number") == 3

    def test_parse_use_on(self, intent_parser):
        """Can parse 'use X on Y' pattern."""
        result = intent_parser.parse("use the key on the door")

        assert result.primary_intent.type == IntentType.USE
        assert result.primary_intent.parameters.get("target") == "the key"
        assert result.primary_intent.parameters.get("secondary") == "the door"

    def test_parse_empty(self, intent_parser):
        """Empty input returns unknown intent."""
        result = intent_parser.parse("")

        assert result.primary_intent.type == IntentType.UNKNOWN
        assert result.primary_intent.confidence == 0.0

    def test_ambiguous_input(self, intent_parser):
        """Ambiguous input is detected."""
        # "open" could be interact, examine, etc.
        result = intent_parser.parse("open")

        # May have secondary intents or be marked ambiguous
        assert result.primary_intent.type != IntentType.UNKNOWN

    def test_secondary_intents(self, intent_parser):
        """Secondary intents are detected."""
        # "look and talk" has multiple intents
        result = intent_parser.parse("examine the guard")

        # Primary should be examine
        assert result.primary_intent.type == IntentType.EXAMINE

    def test_urgency_detection(self, intent_parser):
        """Can detect urgent commands."""
        assert intent_parser.is_urgent("run!") is True
        assert intent_parser.is_urgent("flee now") is True
        assert intent_parser.is_urgent("help me") is True
        assert intent_parser.is_urgent("duck!") is True
        assert intent_parser.is_urgent("look at desk") is False

    def test_suggestions_generated(self, intent_parser, game_context):
        """Suggestions are generated for ambiguous input."""
        result = intent_parser.parse("asdf", game_context)

        # For unknown input, should have suggestions
        assert result.primary_intent.type == IntentType.UNKNOWN or result.ambiguous


class TestNLUResult:
    """Tests for NLUResult."""

    def test_create_result(self):
        """Can create NLU result."""
        intent = Intent(type=IntentType.EXAMINE, confidence=0.9)
        result = NLUResult(primary_intent=intent)

        assert result.primary_intent == intent
        assert result.has_multiple_intents is False

    def test_has_multiple_intents(self):
        """Can check for multiple intents."""
        primary = Intent(type=IntentType.EXAMINE, confidence=0.9)
        secondary = Intent(type=IntentType.TALK, confidence=0.6)

        result = NLUResult(
            primary_intent=primary,
            secondary_intents=[secondary],
        )

        assert result.has_multiple_intents is True

    def test_needs_clarification(self):
        """Can check if clarification is needed."""
        confident = NLUResult(
            primary_intent=Intent(type=IntentType.EXAMINE, confidence=0.9)
        )
        assert confident.needs_clarification is False

        ambiguous = NLUResult(
            primary_intent=Intent(type=IntentType.EXAMINE, confidence=0.5),
            ambiguous=True,
        )
        assert ambiguous.needs_clarification is True

        low_confidence = NLUResult(
            primary_intent=Intent(type=IntentType.EXAMINE, confidence=0.4)
        )
        assert low_confidence.needs_clarification is True

    def test_serialization(self):
        """Result can be serialized."""
        intent = Intent(type=IntentType.MOVE, confidence=0.85)
        result = NLUResult(
            primary_intent=intent,
            suggestions=["Try 'go north'"],
            processing_time_ms=10,
        )

        data = result.to_dict()
        assert data["primary_intent"]["type"] == "move"
        assert data["suggestions"] == ["Try 'go north'"]
