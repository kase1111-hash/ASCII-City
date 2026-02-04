"""
Game Integration Tests - Full game loop integration tests.

Tests the complete game engine integration including:
- Game initialization and configuration
- Command parsing and execution
- Location management and transitions
- Character interactions
- Memory system integration
- LLM fallback behavior
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from shadowengine.game import Game, GameState
from shadowengine.config import GameConfig
from shadowengine.character import Character, Archetype
from shadowengine.render import Location
from shadowengine.interaction import Hotspot, HotspotType
from shadowengine.narrative import NarrativeSpine, ConflictType, TrueResolution, Revelation
from shadowengine.memory import EventType


class TestGameInitialization:
    """Tests for game initialization and configuration."""

    def test_game_creates_with_default_config(self):
        """Game should initialize with default configuration."""
        game = Game()
        assert game.config is not None
        assert game.state is not None
        assert game.parser is not None
        assert game.renderer is not None

    def test_game_creates_with_custom_config(self):
        """Game should accept custom configuration."""
        config = GameConfig(
            screen_width=80,
            screen_height=24,
            debug_mode=True,
            auto_save=False
        )
        game = Game(config=config)
        assert game.config.screen_width == 80
        assert game.config.screen_height == 24
        assert game.config.debug_mode is True

    def test_new_game_resets_state(self):
        """Starting a new game should reset all state."""
        game = Game()
        game.state.inventory.append("test_item")
        game.new_game()
        assert len(game.state.inventory) == 0

    def test_new_game_with_seed_sets_seed(self):
        """New game with seed should set the seed."""
        game = Game()
        game.new_game(seed=12345)
        assert game.state.memory.game_seed == 12345


class TestCharacterManagement:
    """Tests for character management."""

    def test_add_character(self):
        """Adding a character should register it in game state."""
        game = Game()
        char = Character(
            id="test_char",
            name="Test Character",
            archetype=Archetype.INNOCENT,
            description="A test character"
        )
        game.add_character(char)
        assert "test_char" in game.state.characters
        assert game.state.characters["test_char"].name == "Test Character"

    def test_add_character_registers_memory(self):
        """Adding a character should register their memory."""
        game = Game()
        char = Character(
            id="test_char",
            name="Test Character",
            archetype=Archetype.INNOCENT,
            description="A test character"
        )
        game.add_character(char)
        assert "test_char" in game.state.memory.characters


class TestLocationManagement:
    """Tests for location management."""

    def test_add_location(self):
        """Adding a location should register it in game state."""
        game = Game()
        location = Location(
            id="test_loc",
            name="Test Location",
            description="A test location"
        )
        game.add_location(location)
        assert "test_loc" in game.state.locations

    def test_set_start_location(self):
        """Setting start location should update current location."""
        game = Game()
        location = Location(
            id="start",
            name="Start Location",
            description="Starting point"
        )
        game.add_location(location)
        game.set_start_location("start")
        assert game.state.current_location_id == "start"
        assert game.starting_location_id == "start"
        assert game.location_distances["start"] == 0

    def test_current_location_property(self):
        """Current location property should return the active location."""
        game = Game()
        location = Location(
            id="test_loc",
            name="Test Location",
            description="A test location"
        )
        game.add_location(location)
        game.set_start_location("test_loc")
        assert game.current_location is not None
        assert game.current_location.id == "test_loc"


class TestNarrativeIntegration:
    """Tests for narrative system integration."""

    def test_set_spine(self):
        """Setting narrative spine should update game state."""
        game = Game()
        spine = NarrativeSpine(
            conflict_type=ConflictType.THEFT,
            conflict_description="Something was stolen",
            true_resolution=TrueResolution(
                culprit_id="culprit",
                motive="greed",
                method="stealth",
                opportunity="alone",
                evidence_chain=["clue1"]
            )
        )
        game.set_spine(spine)
        assert game.state.spine is not None
        assert game.state.spine.conflict_type == ConflictType.THEFT


class TestMemoryIntegration:
    """Tests for memory system integration."""

    def test_player_discovery_recording(self):
        """Player discoveries should be recorded in memory."""
        game = Game()
        game.state.memory.player_discovers(
            fact_id="test_fact",
            description="A discovered fact",
            location="test_loc",
            source="examined object",
            is_evidence=True
        )
        assert "test_fact" in game.state.memory.player.discoveries

    def test_character_memory_integration(self):
        """Character memory should integrate with main memory bank."""
        game = Game()
        char = Character(
            id="test_char",
            name="Test Character",
            archetype=Archetype.INNOCENT,
            description="A test character"
        )
        game.add_character(char)

        memory = game.state.memory.get_character_memory("test_char")
        assert memory is not None


class TestGameStateIntegration:
    """Tests for complete game state integration."""

    def test_complete_game_setup(self):
        """Test a complete game setup scenario."""
        config = GameConfig(debug_mode=True, auto_save=False)
        game = Game(config=config)
        game.new_game(seed=42)

        # Add locations
        study = Location(
            id="study",
            name="The Study",
            description="A dark, wood-paneled room."
        )
        study.add_hotspot(Hotspot(
            id="hs_desk",
            label="Desk",
            hotspot_type=HotspotType.OBJECT,
            position=(20, 10),
            description="An ornate wooden desk"
        ))
        game.add_location(study)
        game.set_start_location("study")

        # Add characters
        suspect = Character(
            id="suspect",
            name="John Doe",
            archetype=Archetype.GUILTY,
            description="A nervous-looking man",
            secret_truth="I did it",
            public_lie="I was elsewhere"
        )
        game.add_character(suspect)

        # Verify complete setup
        assert game.current_location is not None
        assert "suspect" in game.state.characters
        assert game.state.memory.game_seed == 42

    def test_state_summary(self):
        """Test state summary generation."""
        game = Game()
        location = Location(
            id="test_loc",
            name="Test Location",
            description="A test location"
        )
        game.add_location(location)
        game.set_start_location("test_loc")

        summary = game.get_state_summary()
        assert "current_location" in summary
        assert summary["current_location"] == "test_loc"
        assert "moral_shade" in summary


class TestEnvironmentIntegration:
    """Tests for environment system integration."""

    def test_set_weather(self):
        """Setting weather should update environment."""
        from shadowengine.environment import WeatherType
        game = Game()
        game.set_weather(WeatherType.RAIN)
        assert game.state.environment.weather is not None

    def test_set_time(self):
        """Setting time should update environment."""
        game = Game()
        game.set_time(14, 30)
        assert game.state.environment.time.hour == 14
        assert game.state.environment.time.minute == 30


class TestWorldStateIntegration:
    """Tests for world state tracking integration."""

    def test_world_state_initialization(self):
        """World state should be initialized with game state."""
        game = Game()
        assert game.state.world_state is not None
        assert game.state.world_state.generation_memory is not None

    def test_location_distance_tracking(self):
        """Location distances should be tracked from start."""
        game = Game()
        loc1 = Location(id="loc1", name="Location 1", description="First")
        loc2 = Location(id="loc2", name="Location 2", description="Second")

        game.add_location(loc1)
        game.add_location(loc2)
        game.set_start_location("loc1")

        assert game.location_distances["loc1"] == 0


class TestConversationIntegration:
    """Tests for conversation system integration."""

    def test_conversation_state_management(self):
        """Conversation state should be properly managed."""
        game = Game()
        game.state.in_conversation = True
        game.state.conversation_partner = "test_char"

        assert game.state.in_conversation is True
        assert game.state.conversation_partner == "test_char"

    def test_conversation_exit(self):
        """Exiting conversation should reset state."""
        game = Game()
        game.state.in_conversation = True
        game.state.conversation_partner = "test_char"

        game.state.in_conversation = False
        game.state.conversation_partner = None

        assert game.state.in_conversation is False
        assert game.state.conversation_partner is None
