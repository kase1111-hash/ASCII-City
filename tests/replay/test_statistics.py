"""Tests for the statistics system."""

import pytest
from src.shadowengine.replay.statistics import (
    GameStatistics, AggregateStatistics,
    Achievement, AchievementManager, ACHIEVEMENTS
)


class TestGameStatistics:
    """Tests for GameStatistics."""

    def test_creation(self):
        """Should create game statistics."""
        stats = GameStatistics()
        assert stats.solved is False
        assert stats.commands_entered == 0

    def test_completion_percentage(self):
        """Should calculate completion percentage."""
        stats = GameStatistics(
            locations_visited=5,
            locations_total=10,
            hotspots_examined=8,
            hotspots_total=10,
            evidence_collected=3,
            evidence_total=5,
            characters_talked=2,
            characters_total=4,
            revelations_discovered=1,
            revelations_total=2
        )

        # Total: 5+8+3+2+1 = 19 found, 10+10+5+4+2 = 31 total
        expected = 19 / 31
        assert abs(stats.completion_percentage() - expected) < 0.01

    def test_completion_percentage_empty(self):
        """Should handle zero totals."""
        stats = GameStatistics()
        assert stats.completion_percentage() == 0.0

    def test_efficiency_score(self):
        """Should calculate efficiency score."""
        stats = GameStatistics(
            locations_visited=10,
            locations_total=10,
            commands_entered=100
        )

        # Efficiency = completion / (commands/100)
        # completion ~= 1.0, efficiency = 1.0 / 1.0 = 1.0
        assert stats.efficiency_score() > 0

    def test_efficiency_zero_commands(self):
        """Should handle zero commands."""
        stats = GameStatistics()
        assert stats.efficiency_score() == 0.0

    def test_serialization(self):
        """Should serialize and deserialize."""
        stats = GameStatistics(
            game_id="test_game",
            seed=12345,
            solved=True,
            locations_visited=5
        )

        data = stats.to_dict()
        restored = GameStatistics.from_dict(data)

        assert restored.game_id == "test_game"
        assert restored.seed == 12345
        assert restored.solved is True
        assert restored.locations_visited == 5


class TestAggregateStatistics:
    """Tests for AggregateStatistics."""

    def test_creation(self):
        """Should create aggregate statistics."""
        agg = AggregateStatistics()
        assert agg.games_played == 0
        assert agg.games_solved == 0

    def test_solve_rate(self):
        """Should calculate solve rate."""
        agg = AggregateStatistics(games_played=10, games_solved=7)
        assert agg.solve_rate() == 0.7

    def test_solve_rate_zero(self):
        """Should handle zero games."""
        agg = AggregateStatistics()
        assert agg.solve_rate() == 0.0

    def test_update_from_game(self):
        """Should update from game statistics."""
        agg = AggregateStatistics()
        game = GameStatistics(
            game_id="game1",
            solved=True,
            time_played_seconds=300,
            commands_entered=50,
            evidence_collected=3,
            characters_talked=2,
            locations_visited=5,
            ending_id="good_ending",
            moral_shade="pragmatic"
        )

        agg.update_from_game(game)

        assert agg.games_played == 1
        assert agg.games_solved == 1
        assert agg.total_time_seconds == 300
        assert agg.total_commands == 50
        assert agg.total_evidence_collected == 3
        assert agg.fastest_solve_seconds == 300
        assert agg.endings_achieved.get("good_ending") == 1
        assert agg.shades_achieved.get("pragmatic") == 1

    def test_update_fastest_solve(self):
        """Should track fastest solve."""
        agg = AggregateStatistics()

        game1 = GameStatistics(solved=True, time_played_seconds=600)
        agg.update_from_game(game1)
        assert agg.fastest_solve_seconds == 600

        game2 = GameStatistics(solved=True, time_played_seconds=300)
        agg.update_from_game(game2)
        assert agg.fastest_solve_seconds == 300

        game3 = GameStatistics(solved=True, time_played_seconds=400)
        agg.update_from_game(game3)
        assert agg.fastest_solve_seconds == 300  # Still 300

    def test_serialization(self):
        """Should serialize and deserialize."""
        agg = AggregateStatistics(
            games_played=10,
            games_solved=7,
            endings_achieved={"good": 5, "bad": 2}
        )

        data = agg.to_dict()
        restored = AggregateStatistics.from_dict(data)

        assert restored.games_played == 10
        assert restored.games_solved == 7
        assert restored.endings_achieved.get("good") == 5


class TestAchievement:
    """Tests for Achievement."""

    def test_creation(self):
        """Should create achievement."""
        ach = Achievement(
            id="test",
            name="Test Achievement",
            description="A test achievement"
        )
        assert ach.id == "test"
        assert not ach.unlocked

    def test_unlock(self):
        """Should unlock achievement."""
        ach = Achievement(
            id="test",
            name="Test",
            description="Test"
        )

        ach.unlock()

        assert ach.unlocked
        assert ach.unlock_time is not None

    def test_unlock_idempotent(self):
        """Unlocking twice should not change unlock time."""
        ach = Achievement(
            id="test",
            name="Test",
            description="Test"
        )

        ach.unlock()
        first_time = ach.unlock_time

        ach.unlock()
        assert ach.unlock_time == first_time

    def test_serialization(self):
        """Should serialize and deserialize."""
        ach = Achievement(
            id="test",
            name="Test",
            description="Test",
            hidden=True
        )
        ach.unlock()

        data = ach.to_dict()
        restored = Achievement.from_dict(data)

        assert restored.id == "test"
        assert restored.hidden is True
        assert restored.unlocked is True


class TestPredefinedAchievements:
    """Tests for predefined achievements."""

    def test_achievements_exist(self):
        """Should have predefined achievements."""
        assert len(ACHIEVEMENTS) > 0

    def test_achievements_have_content(self):
        """Achievements should have name and description."""
        for ach in ACHIEVEMENTS:
            assert ach.name
            assert ach.description


class TestAchievementManager:
    """Tests for AchievementManager."""

    def test_creation(self):
        """Should create manager with achievements."""
        manager = AchievementManager()
        assert len(manager.achievements) > 0

    def test_get_achievement(self):
        """Should get achievement by ID."""
        manager = AchievementManager()
        ach = manager.get_achievement("first_solve")
        assert ach is not None
        assert ach.id == "first_solve"

    def test_unlock(self):
        """Should unlock achievement."""
        manager = AchievementManager()

        result = manager.unlock("first_solve")
        assert result is True

        ach = manager.get_achievement("first_solve")
        assert ach.unlocked

    def test_unlock_already_unlocked(self):
        """Should return False if already unlocked."""
        manager = AchievementManager()

        manager.unlock("first_solve")
        result = manager.unlock("first_solve")

        assert result is False

    def test_check_first_solve(self):
        """Should unlock first_solve on first solve."""
        manager = AchievementManager()

        game = GameStatistics(solved=True)
        agg = AggregateStatistics(games_solved=1)

        unlocked = manager.check_achievements(game, agg)

        assert any(a.id == "first_solve" for a in unlocked)

    def test_check_perfect_solve(self):
        """Should unlock perfect_solve with no wrong accusations."""
        manager = AchievementManager()

        game = GameStatistics(solved=True, wrong_accusations=0)
        agg = AggregateStatistics()

        unlocked = manager.check_achievements(game, agg)

        assert any(a.id == "perfect_solve" for a in unlocked)

    def test_check_speed_demon(self):
        """Should unlock speed_demon for fast solve."""
        manager = AchievementManager()

        game = GameStatistics(solved=True, time_played_seconds=500)
        agg = AggregateStatistics()

        unlocked = manager.check_achievements(game, agg)

        assert any(a.id == "speed_demon" for a in unlocked)

    def test_check_thorough(self):
        """Should unlock thorough for examining all hotspots."""
        manager = AchievementManager()

        game = GameStatistics(
            hotspots_examined=10,
            hotspots_total=10
        )
        agg = AggregateStatistics()

        unlocked = manager.check_achievements(game, agg)

        assert any(a.id == "thorough" for a in unlocked)

    def test_get_unlocked(self):
        """Should get all unlocked achievements."""
        manager = AchievementManager()
        manager.unlock("first_solve")
        manager.unlock("perfect_solve")

        unlocked = manager.get_unlocked()
        assert len(unlocked) == 2

    def test_get_locked(self):
        """Should get locked achievements."""
        manager = AchievementManager()
        manager.unlock("first_solve")

        locked = manager.get_locked()
        assert len(locked) < len(manager.achievements)
        assert not any(a.id == "first_solve" for a in locked)

    def test_get_locked_excludes_hidden(self):
        """Should exclude hidden achievements by default."""
        manager = AchievementManager()

        locked = manager.get_locked(include_hidden=False)
        hidden_count = sum(1 for a in manager.achievements if a.hidden and not a.unlocked)
        locked_with_hidden = manager.get_locked(include_hidden=True)

        assert len(locked_with_hidden) - len(locked) >= hidden_count

    def test_get_progress(self):
        """Should calculate progress percentage."""
        manager = AchievementManager()
        total = len(manager.achievements)

        manager.unlock("first_solve")
        manager.unlock("perfect_solve")

        progress = manager.get_progress()
        assert progress == 2 / total

    def test_serialization(self):
        """Should serialize and deserialize."""
        manager = AchievementManager()
        manager.unlock("first_solve")

        data = manager.to_dict()
        restored = AchievementManager.from_dict(data)

        ach = restored.get_achievement("first_solve")
        assert ach.unlocked
