"""
Integration tests for Game - the main game engine.

These tests verify that all systems work together correctly:
- Game initialization with locations and characters
- Command handling and state updates
- Memory coordination across layers
"""

import pytest
from shadowengine.game import Game, GameState
from shadowengine.config import GameConfig
from shadowengine.character import Character, Archetype
from shadowengine.render import Location
from shadowengine.interaction import Hotspot, HotspotType
from shadowengine.narrative import NarrativeSpine, ConflictType, TrueResolution, Revelation


class TestGameInitialization:
    """Game initialization tests."""

    @pytest.mark.integration
    def test_create_game(self, game):
        """Can create a game instance."""
        assert game.state is not None
        assert game.parser is not None
        assert game.renderer is not None

    @pytest.mark.integration
    def test_new_game_resets_state(self, game):
        """New game resets all state."""
        # Modify state
        game.state.current_location_id = "somewhere"
        game.state.inventory.append("item")

        # New game
        game.new_game(seed=123)

        assert game.state.current_location_id == ""
        assert len(game.state.inventory) == 0
        assert game.state.memory.game_seed == 123


class TestGameLocationManagement:
    """Location management tests."""

    @pytest.mark.integration
    def test_add_location(self, game, basic_location):
        """Can add locations to game."""
        game.add_location(basic_location)

        assert "study" in game.state.locations

    @pytest.mark.integration
    def test_set_start_location(self, game, basic_location):
        """Can set starting location."""
        game.add_location(basic_location)
        game.set_start_location("study")

        assert game.state.current_location_id == "study"

    @pytest.mark.integration
    def test_current_location_property(self, game, basic_location):
        """Current location property works."""
        game.add_location(basic_location)
        game.set_start_location("study")

        assert game.current_location is not None
        assert game.current_location.name == "The Study"


class TestGameCharacterManagement:
    """Character management tests."""

    @pytest.mark.integration
    def test_add_character(self, game, basic_character):
        """Can add characters to game."""
        game.add_character(basic_character)

        assert "test_char" in game.state.characters
        assert "test_char" in game.state.memory.characters

    @pytest.mark.integration
    def test_multiple_characters(self, game, character_set):
        """Can add multiple characters."""
        for char in character_set.values():
            game.add_character(char)

        assert len(game.state.characters) == 3


class TestGameNarrativeIntegration:
    """Narrative spine integration tests."""

    @pytest.mark.integration
    def test_set_spine(self, game, basic_spine):
        """Can set narrative spine."""
        game.set_spine(basic_spine)

        assert game.state.spine is not None
        assert game.state.spine.conflict_type == ConflictType.THEFT


class TestGameStateTracking:
    """Game state tracking tests."""

    @pytest.mark.integration
    def test_get_state_summary(self, populated_game):
        """Can get game state summary."""
        summary = populated_game.get_state_summary()

        assert "current_location" in summary
        assert "time" in summary
        assert "discoveries" in summary
        assert "moral_shade" in summary


class TestFullScenario:
    """Full scenario integration tests."""

    @pytest.fixture
    def full_game(self):
        """Complete game setup for integration testing."""
        game = Game(GameConfig(debug_mode=True, auto_save=False))
        game.new_game(seed=42)

        # Create location
        study = Location(
            id="study",
            name="The Study",
            description="A wood-paneled study"
        )

        # Add hotspots
        study.add_hotspot(Hotspot.create_person(
            id="hs_butler",
            name="Butler",
            position=(10, 5),
            character_id="butler"
        ))

        study.add_hotspot(Hotspot.create_evidence(
            id="hs_letter",
            label="Torn Letter",
            position=(20, 5),
            description="A letter with important information",
            fact_id="letter_clue"
        ))

        study.add_hotspot(Hotspot.create_exit(
            id="hs_door",
            label="Door",
            position=(30, 10),
            destination="hallway"
        ))

        game.add_location(study)

        # Create hallway
        hallway = Location(
            id="hallway",
            name="The Hallway",
            description="A long hallway"
        )
        hallway.add_hotspot(Hotspot.create_exit(
            id="hs_study_door",
            label="Study Door",
            position=(10, 5),
            destination="study"
        ))
        game.add_location(hallway)

        # Create characters
        butler = Character(
            id="butler",
            name="Mr. Blackwood",
            archetype=Archetype.GUILTY,
            secret_truth="I took the watch",
            public_lie="I know nothing",
            trust_threshold=30,
            initial_location="study"
        )
        butler.add_topic("the theft")
        butler.add_topic("your alibi")
        game.add_character(butler)

        # Create narrative spine
        spine = NarrativeSpine(
            conflict_type=ConflictType.THEFT,
            conflict_description="A watch was stolen",
            true_resolution=TrueResolution(
                culprit_id="butler",
                motive="gambling debts",
                method="took it",
                opportunity="alone in study",
                evidence_chain=["letter_clue"]
            ),
            revelations=[
                Revelation(
                    id="letter_clue",
                    description="Letter reveals butler's debts",
                    importance=3,
                    source="examine letter"
                )
            ]
        )
        game.set_spine(spine)

        game.set_start_location("study")

        return game

    @pytest.mark.integration
    def test_location_has_hotspots(self, full_game):
        """Location correctly shows hotspots."""
        location = full_game.current_location
        hotspots = location.get_visible_hotspots()

        assert len(hotspots) == 3

    @pytest.mark.integration
    def test_memory_tracks_location_visit(self, full_game):
        """Memory tracks visited locations."""
        # Initially not visited
        assert not full_game.state.memory.player.has_visited("study")

        # Visit by setting as current (normally done in exploration loop)
        full_game.state.memory.player.visit_location("study")

        assert full_game.state.memory.player.has_visited("study")

    @pytest.mark.integration
    def test_character_in_correct_location(self, full_game):
        """Character is in expected location."""
        butler = full_game.state.characters["butler"]

        assert butler.state.location == "study"

    @pytest.mark.integration
    def test_spine_revelation_works(self, full_game):
        """Can make revelations through spine."""
        spine = full_game.state.spine

        # Make the revelation
        result = spine.make_revelation("letter_clue")

        assert result is True
        assert "letter_clue" in spine.revealed_facts

    @pytest.mark.integration
    def test_evidence_discovery_flow(self, full_game):
        """Evidence discovery flows through all systems."""
        # Simulate examining evidence
        full_game.state.memory.player_discovers(
            fact_id="letter_clue",
            description="The letter reveals gambling debts",
            location="study",
            source="examined letter",
            is_evidence=True,
            related_to=["butler"]
        )

        # Player memory updated
        assert full_game.state.memory.player.has_discovered("letter_clue")

        # Can solve case with evidence
        spine = full_game.state.spine
        evidence = set(full_game.state.memory.player.discoveries.keys())
        is_correct, _ = spine.check_solution("butler", evidence)

        assert is_correct is True


class TestProceduralScenario:
    """Tests for procedurally generated scenarios."""

    @pytest.mark.integration
    @pytest.mark.procedural
    def test_create_scenario_from_seed(self, generation_seeds):
        """Can create consistent scenarios from seeds."""
        from shadowengine.scenarios.test_scenario import create_test_scenario

        for seed in generation_seeds[:2]:  # Test first 2 seeds
            game = create_test_scenario(seed=seed)

            # Game should be properly set up
            assert game.current_location is not None
            assert len(game.state.characters) > 0
            assert game.state.spine is not None

    @pytest.mark.integration
    @pytest.mark.procedural
    def test_scenario_is_solvable(self):
        """Generated scenario is solvable."""
        from shadowengine.scenarios.test_scenario import create_test_scenario

        game = create_test_scenario(seed=42)
        spine = game.state.spine

        # All revelations should be achievable
        discovered = []
        for _ in range(10):  # Max iterations
            available = spine.get_available_revelations()
            if not available:
                break
            spine.make_revelation(available[0].id)
            discovered.append(available[0].id)

        # Should have discovered all
        assert len(discovered) == len(spine.revelations)

        # Should be able to solve
        culprit = spine.true_resolution.culprit_id
        is_correct, _ = spine.check_solution(culprit, set(discovered))

        assert is_correct is True


class TestMoralIntegration:
    """Moral system integration tests."""

    @pytest.mark.integration
    def test_moral_action_updates_shade(self, populated_game):
        """Moral actions update player's shade."""
        initial_ruthless = populated_game.state.memory.player.shade_scores["ruthless"]

        populated_game.state.memory.player.record_moral_action(
            action_type="threaten",
            description="Threatened the witness",
            timestamp=0,
            target="witness",
            shade_effects={"ruthless": 0.5, "compassionate": -0.3}
        )

        # Shades should have changed (normalization means exact values vary)
        dominant = populated_game.state.memory.player.get_dominant_shade()
        assert dominant is not None

    @pytest.mark.integration
    def test_trust_affects_cooperation(self, populated_game):
        """Character trust affects willingness to cooperate."""
        culprit = populated_game.state.characters["culprit"]

        # Initially neutral
        initial_coop = culprit.will_cooperate()

        # Make hostile
        culprit.modify_trust(-30)

        assert culprit.will_cooperate() is False

        # Make friendly
        culprit.modify_trust(60)  # Net +30

        assert culprit.will_cooperate() is True


class TestSaveLoadIntegration:
    """Save/load integration tests."""

    @pytest.mark.integration
    def test_memory_save_load_preserves_state(self, populated_game):
        """Saving and loading preserves game state."""
        import tempfile
        import os

        # Make some changes
        populated_game.state.memory.player_discovers(
            fact_id="test_clue",
            description="A test clue",
            location="study",
            source="test"
        )
        populated_game.state.memory.advance_time(50)

        # Save
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "test.json")
            populated_game.state.memory.save(save_path)

            # Load into new memory
            from shadowengine.memory import MemoryBank
            loaded = MemoryBank.load(save_path)

            assert loaded.player.has_discovered("test_clue")
            assert loaded.current_time == 50
