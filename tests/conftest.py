"""
Shared test fixtures for ShadowEngine tests.

This file provides reusable fixtures that can be used across all test modules.
Fixtures are designed to be composable and extensible for future LLM integration.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shadowengine.memory import MemoryBank, WorldMemory, CharacterMemory, PlayerMemory, EventType
from shadowengine.character import Character, Archetype, DialogueManager, DialogueTopic
from shadowengine.narrative import NarrativeSpine, SpineGenerator, ConflictType, TrueResolution, Revelation
from shadowengine.interaction import CommandParser, Hotspot, HotspotType
from shadowengine.render import Scene, Location, Renderer
from shadowengine.game import Game, GameState
from shadowengine.config import GameConfig


# =============================================================================
# Memory Fixtures
# =============================================================================

@pytest.fixture
def world_memory():
    """Fresh world memory instance."""
    return WorldMemory()


@pytest.fixture
def character_memory():
    """Fresh character memory for a test character."""
    return CharacterMemory("test_character")


@pytest.fixture
def player_memory():
    """Fresh player memory instance."""
    return PlayerMemory()


@pytest.fixture
def memory_bank():
    """Fresh memory bank with all three layers."""
    return MemoryBank()


@pytest.fixture
def populated_memory_bank(memory_bank):
    """Memory bank with some pre-populated data."""
    # Register characters
    memory_bank.register_character("alice")
    memory_bank.register_character("bob")

    # Add some events
    memory_bank.world.record(
        event_type=EventType.ACTION,
        description="Alice entered the room",
        location="study",
        actors=["alice"],
        witnesses=["bob"]
    )

    # Add player discovery
    memory_bank.player.add_discovery(
        fact_id="clue_1",
        description="A torn letter",
        location="study",
        timestamp=0,
        source="examined desk"
    )

    return memory_bank


# =============================================================================
# Character Fixtures
# =============================================================================

@pytest.fixture
def basic_character():
    """A basic test character."""
    return Character(
        id="test_char",
        name="Test Character",
        archetype=Archetype.INNOCENT,
        description="A test character",
        initial_location="study"
    )


@pytest.fixture
def guilty_character():
    """A guilty character with secrets."""
    char = Character(
        id="culprit",
        name="The Culprit",
        archetype=Archetype.GUILTY,
        description="Someone hiding something",
        secret_truth="I did it because I had no choice",
        public_lie="I was nowhere near there",
        trust_threshold=40,
        initial_location="study"
    )
    char.add_topic("alibi")
    char.add_topic("the incident")
    return char


@pytest.fixture
def witness_character():
    """A witness character who saw something."""
    char = Character(
        id="witness",
        name="The Witness",
        archetype=Archetype.SURVIVOR,
        description="Someone who saw something",
        secret_truth="I saw everything but I'm scared to talk",
        trust_threshold=20,
        initial_location="study"
    )
    char.add_knowledge("saw_culprit")
    char.add_topic("what you saw")
    return char


@pytest.fixture
def character_set(guilty_character, witness_character, basic_character):
    """A set of characters for scenario testing."""
    return {
        "culprit": guilty_character,
        "witness": witness_character,
        "innocent": basic_character
    }


# =============================================================================
# Narrative Fixtures
# =============================================================================

@pytest.fixture
def spine_generator():
    """Spine generator with fixed seed for reproducibility."""
    return SpineGenerator(seed=42)


@pytest.fixture
def basic_spine():
    """A basic narrative spine for testing."""
    return NarrativeSpine(
        conflict_type=ConflictType.THEFT,
        conflict_description="Something was stolen",
        true_resolution=TrueResolution(
            culprit_id="culprit",
            motive="greed",
            method="stealth",
            opportunity="was alone",
            evidence_chain=["clue_1", "clue_2", "clue_3"]
        ),
        revelations=[
            Revelation(
                id="clue_1",
                description="First clue",
                importance=1,
                source="examine scene"
            ),
            Revelation(
                id="clue_2",
                description="Second clue",
                importance=2,
                prerequisites=["clue_1"],
                source="talk to witness"
            ),
            Revelation(
                id="clue_3",
                description="Final proof",
                importance=3,
                prerequisites=["clue_2"],
                source="confront culprit"
            )
        ]
    )


# =============================================================================
# Interaction Fixtures
# =============================================================================

@pytest.fixture
def command_parser():
    """Fresh command parser."""
    return CommandParser()


@pytest.fixture
def sample_hotspots():
    """A set of sample hotspots for testing."""
    return [
        Hotspot.create_person(
            id="hs_person",
            name="John",
            position=(10, 5),
            character_id="john",
            description="A person standing here"
        ),
        Hotspot.create_item(
            id="hs_item",
            label="Key",
            position=(20, 5),
            description="A brass key",
            item_id="brass_key"
        ),
        Hotspot.create_exit(
            id="hs_exit",
            label="Door",
            position=(30, 10),
            destination="hallway"
        ),
        Hotspot.create_evidence(
            id="hs_evidence",
            label="Letter",
            position=(15, 8),
            description="A torn letter with partial text",
            fact_id="letter_clue"
        )
    ]


@pytest.fixture
def parser_context(sample_hotspots):
    """Context dict for parser testing."""
    return {
        "targets": [h.label for h in sample_hotspots],
        "hotspots": [
            {"label": h.label, "type": h.hotspot_type.value}
            for h in sample_hotspots
        ]
    }


# =============================================================================
# Location and Scene Fixtures
# =============================================================================

@pytest.fixture
def basic_location(sample_hotspots):
    """A basic location with hotspots."""
    location = Location(
        id="study",
        name="The Study",
        description="A wood-paneled room",
        art=[
            "╔════════════════════╗",
            "║   STUDY            ║",
            "╚════════════════════╝"
        ]
    )
    for hotspot in sample_hotspots:
        location.add_hotspot(hotspot)
    location.add_exit("north", "hallway")
    return location


@pytest.fixture
def scene(basic_location):
    """A scene for the basic location."""
    return Scene(location=basic_location)


# =============================================================================
# Game Fixtures
# =============================================================================

@pytest.fixture
def game_config():
    """Test game configuration."""
    return GameConfig(
        screen_width=60,
        screen_height=20,
        debug_mode=True,
        auto_save=False
    )


@pytest.fixture
def game(game_config):
    """A fresh game instance."""
    return Game(config=game_config)


@pytest.fixture
def populated_game(game, basic_location, guilty_character, witness_character):
    """A game with location and characters set up."""
    game.add_location(basic_location)
    game.add_character(guilty_character)
    game.add_character(witness_character)
    game.set_start_location("study")
    return game


# =============================================================================
# Procedural Generation Fixtures (Expandable for LLM)
# =============================================================================

@pytest.fixture
def generation_seeds():
    """A set of seeds for reproducible procedural generation testing."""
    return [42, 123, 456, 789, 1000]


@pytest.fixture
def conflict_types():
    """All available conflict types for comprehensive testing."""
    return list(ConflictType)


@pytest.fixture
def archetypes():
    """All available character archetypes."""
    return list(Archetype)


# =============================================================================
# Helper Functions (available to all tests)
# =============================================================================

class TestHelpers:
    """Helper methods for tests."""

    @staticmethod
    def apply_pressure_until_cracked(character, max_attempts=10):
        """Apply pressure to character until they crack or max attempts."""
        for i in range(max_attempts):
            if character.apply_pressure(15):
                return True, i + 1
        return False, max_attempts

    @staticmethod
    def discover_all_revelations(spine, memory_bank):
        """Discover all revelations in order."""
        discovered = []
        for rev in spine.revelations:
            if spine.check_revelation(rev.id):
                spine.make_revelation(rev.id)
                discovered.append(rev.id)
        return discovered

    @staticmethod
    def simulate_commands(parser, commands, context=None):
        """Parse a list of commands and return results."""
        context = context or {}
        return [parser.parse(cmd, context) for cmd in commands]


@pytest.fixture
def helpers():
    """Test helper methods."""
    return TestHelpers()
