"""Extended tests for replay systems."""

import pytest
from src.shadowengine.replay.statistics import (
    GameStatistics, AggregateStatistics,
    Achievement, AchievementManager, ACHIEVEMENTS
)
from src.shadowengine.replay.seeds import (
    GameSeed, DailyChallenge, SeedCollection, SeedGenerator
)


class TestStatisticsEdgeCases:
    """Edge case tests for statistics system."""

    def test_completion_percentage_all_zeros(self):
        """Should handle all zero totals without division error."""
        stats = GameStatistics()
        # All totals are zero
        assert stats.completion_percentage() == 0.0

    def test_completion_percentage_full_completion(self):
        """Full completion should be 100%."""
        stats = GameStatistics(
            locations_visited=10,
            locations_total=10,
            hotspots_examined=20,
            hotspots_total=20,
            evidence_collected=5,
            evidence_total=5,
            characters_talked=3,
            characters_total=3,
            revelations_discovered=2,
            revelations_total=2
        )
        assert stats.completion_percentage() == 1.0

    def test_efficiency_with_high_commands(self):
        """Efficiency with very high command count."""
        stats = GameStatistics(
            locations_visited=10,
            locations_total=10,
            commands_entered=10000
        )
        # Should not overflow or error
        efficiency = stats.efficiency_score()
        assert efficiency <= 0.01  # Very inefficient

    def test_statistics_preserve_all_fields(self):
        """All fields should survive serialization."""
        stats = GameStatistics(
            game_id="test123",
            seed=54321,
            solved=True,
            time_played_seconds=1234.5,
            commands_entered=100,
            locations_visited=5,
            locations_total=10,
            hotspots_examined=15,
            hotspots_total=20,
            evidence_collected=3,
            evidence_total=6,
            characters_talked=2,
            characters_total=4,
            revelations_discovered=1,
            revelations_total=3,
            wrong_accusations=2,
            ending_id="neutral",
            moral_shade="pragmatic"
        )

        data = stats.to_dict()
        restored = GameStatistics.from_dict(data)

        assert restored.game_id == stats.game_id
        assert restored.seed == stats.seed
        assert restored.solved == stats.solved
        assert restored.time_played_seconds == stats.time_played_seconds
        assert restored.wrong_accusations == stats.wrong_accusations
        assert restored.moral_shade == stats.moral_shade


class TestAggregateStatisticsEdgeCases:
    """Edge case tests for aggregate statistics."""

    def test_update_from_many_games(self):
        """Should handle updates from many games."""
        agg = AggregateStatistics()

        for i in range(100):
            game = GameStatistics(
                game_id=f"game_{i}",
                solved=i % 2 == 0,
                time_played_seconds=100 + i * 10,
                commands_entered=50 + i,
                evidence_collected=3,
                ending_id=f"ending_{i % 5}",
                moral_shade=["pragmatic", "idealistic", "corrupt"][i % 3]
            )
            agg.update_from_game(game)

        assert agg.games_played == 100
        assert agg.games_solved == 50  # Half solved
        assert len(agg.endings_achieved) == 5
        assert len(agg.shades_achieved) == 3

    def test_fastest_solve_only_counts_solved(self):
        """Fastest solve should only count solved games."""
        agg = AggregateStatistics()

        # Unsolved game with short time
        unsolved = GameStatistics(solved=False, time_played_seconds=10)
        agg.update_from_game(unsolved)

        # Unsolved should not affect fastest solve (stays at init value)
        initial_fastest = agg.fastest_solve_seconds

        # Solved game
        solved = GameStatistics(solved=True, time_played_seconds=500)
        agg.update_from_game(solved)

        assert agg.fastest_solve_seconds == 500

    def test_average_solve_time(self):
        """Should calculate average solve time correctly."""
        agg = AggregateStatistics()

        for seconds in [100, 200, 300]:
            game = GameStatistics(solved=True, time_played_seconds=seconds)
            agg.update_from_game(game)

        # Average should be 200
        avg = agg.total_time_seconds / agg.games_played
        assert avg == 200


class TestAchievementEdgeCases:
    """Edge case tests for achievements."""

    def test_all_achievements_have_unique_ids(self):
        """All achievements should have unique IDs."""
        ids = [a.id for a in ACHIEVEMENTS]
        assert len(ids) == len(set(ids))

    def test_achievement_manager_unknown_id(self):
        """Should handle unknown achievement ID gracefully."""
        manager = AchievementManager()

        result = manager.unlock("nonexistent_achievement_12345")
        assert result is False

        ach = manager.get_achievement("nonexistent_achievement_12345")
        assert ach is None

    def test_multiple_achievements_in_one_game(self):
        """Should unlock multiple achievements from one game."""
        manager = AchievementManager()

        game = GameStatistics(
            solved=True,
            time_played_seconds=400,  # Fast
            wrong_accusations=0,  # Perfect
            hotspots_examined=10,
            hotspots_total=10  # Thorough
        )
        agg = AggregateStatistics(games_solved=1)

        unlocked = manager.check_achievements(game, agg)

        achievement_ids = [a.id for a in unlocked]
        assert "first_solve" in achievement_ids
        assert "perfect_solve" in achievement_ids
        assert "speed_demon" in achievement_ids
        assert "thorough" in achievement_ids

    def test_achievement_already_unlocked_not_reported(self):
        """Already unlocked achievements should not be reported again."""
        manager = AchievementManager()

        game = GameStatistics(solved=True)
        agg = AggregateStatistics(games_solved=1)

        # First check
        first_unlocked = manager.check_achievements(game, agg)
        assert any(a.id == "first_solve" for a in first_unlocked)

        # Second check should not report first_solve again
        second_unlocked = manager.check_achievements(game, agg)
        assert not any(a.id == "first_solve" for a in second_unlocked)


class TestSeedEdgeCases:
    """Edge case tests for seed system."""

    def test_seed_boundary_values(self):
        """Should handle boundary seed values."""
        # Zero
        seed_zero = GameSeed(value=0)
        code_zero = seed_zero.to_share_code()
        restored_zero = GameSeed.from_share_code(code_zero)
        assert restored_zero.value == 0

        # Max 32-bit
        seed_max = GameSeed(value=2**32 - 1)
        code_max = seed_max.to_share_code()
        restored_max = GameSeed.from_share_code(code_max)
        assert restored_max.value == 2**32 - 1

    def test_share_code_with_all_options(self):
        """Share code should preserve all options."""
        seed = GameSeed(
            value=12345,
            difficulty="nightmare",
            character_count=10,
            twist_enabled=True,
            conflict_type="conspiracy",
            name="Test Seed",
            description="A test",
            author="Tester"
        )

        code = seed.to_share_code()
        restored = GameSeed.from_share_code(code)

        assert restored.difficulty == "nightmare"
        assert restored.character_count == 10
        assert restored.twist_enabled is True
        assert restored.conflict_type == "conspiracy"

    def test_daily_challenge_consistency(self):
        """Daily challenge should be consistent within same day."""
        today1 = DailyChallenge.for_today()
        today2 = DailyChallenge.for_today()

        # Same day should produce same challenge
        assert today1.date_str == today2.date_str
        assert today1.seed.value == today2.seed.value

    def test_leaderboard_sorting_with_ties(self):
        """Leaderboard with tie-breaking."""
        challenge = DailyChallenge.for_today()

        # Same time, same solved status
        challenge.add_score("player1", 300, solved=True)
        challenge.add_score("player2", 300, solved=True)
        challenge.add_score("player3", 300, solved=True)

        # All should be ranked
        assert len(challenge.leaderboard) == 3
        # Ranks should still work
        assert challenge.get_rank("player1") is not None


class TestSeedCollectionEdgeCases:
    """Edge case tests for seed collection."""

    def test_empty_search(self):
        """Search with empty query."""
        collection = SeedCollection()
        collection.add(GameSeed(value=111, name="Test"))

        results = collection.search("")
        # Empty search should return all or none
        assert isinstance(results, list)

    def test_case_insensitive_search(self):
        """Search should be case insensitive."""
        collection = SeedCollection()
        collection.add(GameSeed(value=111, name="Murder Mystery"))
        collection.add(GameSeed(value=222, name="THEFT CASE"))

        upper_results = collection.search("MURDER")
        lower_results = collection.search("theft")

        assert len(upper_results) == 1
        assert len(lower_results) == 1

    def test_add_duplicate_seed(self):
        """Adding seed with same value."""
        collection = SeedCollection()
        seed1 = GameSeed(value=111, name="First")
        seed2 = GameSeed(value=111, name="Second")

        collection.add(seed1)
        collection.add(seed2)

        # Behavior depends on implementation
        found = collection.get(111)
        assert found is not None

    def test_toggle_favorite_nonexistent(self):
        """Toggle favorite on nonexistent seed."""
        collection = SeedCollection()
        # Should not crash
        result = collection.toggle_favorite(99999)
        # Result depends on implementation
        assert isinstance(result, bool)


class TestSeedGeneratorVariety:
    """Tests for seed generator variety."""

    def test_different_themes_produce_variety(self):
        """Different themes should produce different seeds."""
        generator = SeedGenerator()
        themes = ["noir", "horror", "cozy", "classic"]

        seeds = [generator.generate_themed(theme) for theme in themes]
        names = set(s.name for s in seeds)

        # Should have variety
        assert len(names) >= 3

    def test_series_continuity(self):
        """Series should have related names."""
        generator = SeedGenerator()
        series = generator.generate_series(5, prefix="Case")

        for i, seed in enumerate(series):
            assert f"Case {i + 1}" in seed.name

    def test_difficulty_parameters(self):
        """Each difficulty should set appropriate parameters."""
        generator = SeedGenerator()

        # Verify character counts for different difficulties
        easy = generator.generate_difficulty("easy")
        normal = generator.generate_difficulty("normal")
        hard = generator.generate_difficulty("hard")
        nightmare = generator.generate_difficulty("nightmare")

        assert easy.character_count == 3
        assert normal.character_count == 5
        assert hard.character_count == 7
        assert nightmare.character_count == 10

        # Verify difficulty is set correctly
        assert easy.difficulty == "easy"
        assert normal.difficulty == "normal"
        assert hard.difficulty == "hard"
        assert nightmare.difficulty == "nightmare"


class TestDailyChallengeLeaderboard:
    """Tests for daily challenge leaderboard functionality."""

    def test_leaderboard_max_size(self):
        """Leaderboard should handle many entries."""
        challenge = DailyChallenge.for_today()

        for i in range(100):
            challenge.add_score(f"player_{i}", i * 10, solved=True)

        # Should maintain order
        assert challenge.leaderboard[0]["time_seconds"] < challenge.leaderboard[-1]["time_seconds"]

    def test_unsolved_always_after_solved(self):
        """Unsolved entries should always rank after solved."""
        challenge = DailyChallenge.for_today()

        challenge.add_score("fast_unsolved", 50, solved=False)
        challenge.add_score("slow_solved", 1000, solved=True)

        assert challenge.leaderboard[0]["player"] == "slow_solved"
        assert challenge.leaderboard[1]["player"] == "fast_unsolved"

    def test_get_rank_after_many_additions(self):
        """Rank should be accurate after many additions."""
        challenge = DailyChallenge.for_today()

        for i in range(50):
            challenge.add_score(f"player_{i}", (i + 1) * 10, solved=True)

        # Fastest player should be rank 1
        assert challenge.get_rank("player_0") == 1
        # Slowest player should be rank 50
        assert challenge.get_rank("player_49") == 50


class TestStatisticsSerialization:
    """Tests for statistics serialization roundtrips."""

    def test_aggregate_full_roundtrip(self):
        """Aggregate stats should survive full roundtrip."""
        agg = AggregateStatistics()

        # Add multiple games
        for i in range(10):
            game = GameStatistics(
                solved=i % 2 == 0,
                time_played_seconds=100 + i * 50,
                commands_entered=50 + i * 10,
                evidence_collected=i,
                ending_id=f"ending_{i % 3}",
                moral_shade=["pragmatic", "idealistic"][i % 2]
            )
            agg.update_from_game(game)

        # Serialize and restore
        data = agg.to_dict()
        restored = AggregateStatistics.from_dict(data)

        assert restored.games_played == agg.games_played
        assert restored.games_solved == agg.games_solved
        assert restored.total_time_seconds == agg.total_time_seconds
        assert restored.endings_achieved == agg.endings_achieved
        assert restored.shades_achieved == agg.shades_achieved

    def test_achievement_manager_full_roundtrip(self):
        """Achievement manager state should survive roundtrip."""
        manager = AchievementManager()

        # Unlock several achievements
        manager.unlock("first_solve")
        manager.unlock("perfect_solve")
        manager.unlock("thorough")

        data = manager.to_dict()
        restored = AchievementManager.from_dict(data)

        assert restored.get_achievement("first_solve").unlocked
        assert restored.get_achievement("perfect_solve").unlocked
        assert restored.get_achievement("thorough").unlocked
        assert not restored.get_achievement("speed_demon").unlocked


class TestSeedCollectionSerialization:
    """Tests for seed collection serialization."""

    def test_full_collection_roundtrip(self):
        """Full collection should survive roundtrip."""
        collection = SeedCollection()

        # Add seeds with various properties
        for i in range(5):
            seed = GameSeed(
                value=1000 + i,
                name=f"Seed {i}",
                description=f"Description {i}",
                difficulty=["easy", "normal", "hard"][i % 3]
            )
            collection.add(seed)

        # Favorite some
        collection.toggle_favorite(1001)
        collection.toggle_favorite(1003)

        # Serialize and restore
        data = collection.to_dict()
        restored = SeedCollection.from_dict(data)

        assert len(restored.seeds) == 5
        assert 1001 in restored.favorites
        assert 1003 in restored.favorites
        assert 1002 not in restored.favorites

