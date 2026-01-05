"""Tests for the seed system."""

import pytest
from src.shadowengine.replay.seeds import (
    GameSeed, DailyChallenge, SeedCollection, SeedGenerator
)


class TestGameSeed:
    """Tests for GameSeed."""

    def test_creation(self):
        """Should create a game seed."""
        seed = GameSeed(value=12345)
        assert seed.value == 12345

    def test_generate_random(self):
        """Should generate random seed."""
        seed = GameSeed.generate()
        assert seed.value is not None
        assert 0 <= seed.value < 2**32

    def test_generate_from_source(self):
        """Should generate deterministic seed from source."""
        seed1 = GameSeed.generate(source="test")
        seed2 = GameSeed.generate(source="test")

        assert seed1.value == seed2.value

    def test_generate_different_sources(self):
        """Different sources should produce different seeds."""
        seed1 = GameSeed.generate(source="test1")
        seed2 = GameSeed.generate(source="test2")

        assert seed1.value != seed2.value

    def test_from_daily(self):
        """Should generate daily seed."""
        seed = GameSeed.from_daily()
        assert seed.value is not None

    def test_daily_same_day(self):
        """Same day should produce same daily seed."""
        seed1 = GameSeed.from_daily()
        seed2 = GameSeed.from_daily()

        assert seed1.value == seed2.value

    def test_daily_different_days(self):
        """Different days should produce different seeds."""
        seed_today = GameSeed.from_daily(offset=0)
        seed_tomorrow = GameSeed.from_daily(offset=1)

        assert seed_today.value != seed_tomorrow.value

    def test_to_share_code(self):
        """Should generate share code."""
        seed = GameSeed(
            value=12345,
            difficulty="hard",
            character_count=7,
            twist_enabled=True
        )

        code = seed.to_share_code()
        assert code.startswith("SH")
        assert len(code) > 2

    def test_from_share_code(self):
        """Should parse share code."""
        original = GameSeed(
            value=12345,
            difficulty="hard",
            character_count=7,
            twist_enabled=True
        )

        code = original.to_share_code()
        restored = GameSeed.from_share_code(code)

        assert restored is not None
        assert restored.value == 12345
        assert restored.difficulty == "hard"
        assert restored.character_count == 7
        assert restored.twist_enabled is True

    def test_from_share_code_invalid(self):
        """Should return None for invalid code."""
        assert GameSeed.from_share_code("invalid") is None
        assert GameSeed.from_share_code("XX") is None
        assert GameSeed.from_share_code("SHinvalid!!!") is None

    def test_share_code_roundtrip(self):
        """Share code should roundtrip correctly."""
        original = GameSeed(
            value=99999,
            difficulty="nightmare",
            character_count=10,
            twist_enabled=False,
            conflict_type="murder"
        )

        code = original.to_share_code()
        restored = GameSeed.from_share_code(code)

        assert restored.value == original.value
        assert restored.difficulty == original.difficulty
        assert restored.character_count == original.character_count
        assert restored.twist_enabled == original.twist_enabled
        assert restored.conflict_type == original.conflict_type

    def test_serialization(self):
        """Should serialize and deserialize."""
        seed = GameSeed(
            value=12345,
            difficulty="hard",
            name="Test Seed",
            author="Tester"
        )

        data = seed.to_dict()
        restored = GameSeed.from_dict(data)

        assert restored.value == 12345
        assert restored.difficulty == "hard"
        assert restored.name == "Test Seed"


class TestDailyChallenge:
    """Tests for DailyChallenge."""

    def test_for_today(self):
        """Should create today's challenge."""
        challenge = DailyChallenge.for_today()

        assert challenge.date_str is not None
        assert challenge.seed is not None
        assert challenge.title is not None

    def test_add_score(self):
        """Should add score to leaderboard."""
        challenge = DailyChallenge.for_today()

        challenge.add_score("player1", 300, solved=True)
        challenge.add_score("player2", 200, solved=True)

        assert len(challenge.leaderboard) == 2
        # Faster player should be first
        assert challenge.leaderboard[0]["player"] == "player2"

    def test_add_score_unsolved(self):
        """Unsolved should rank after solved."""
        challenge = DailyChallenge.for_today()

        challenge.add_score("slow_solver", 600, solved=True)
        challenge.add_score("fast_unsolved", 100, solved=False)

        assert challenge.leaderboard[0]["player"] == "slow_solver"

    def test_get_rank(self):
        """Should get player rank."""
        challenge = DailyChallenge.for_today()

        challenge.add_score("player1", 300, solved=True)
        challenge.add_score("player2", 200, solved=True)

        assert challenge.get_rank("player2") == 1
        assert challenge.get_rank("player1") == 2
        assert challenge.get_rank("unknown") is None

    def test_serialization(self):
        """Should serialize and deserialize."""
        challenge = DailyChallenge.for_today()
        challenge.add_score("player1", 300, solved=True)

        data = challenge.to_dict()
        restored = DailyChallenge.from_dict(data)

        assert restored.date_str == challenge.date_str
        assert len(restored.leaderboard) == 1


class TestSeedCollection:
    """Tests for SeedCollection."""

    def test_creation(self):
        """Should create empty collection."""
        collection = SeedCollection()
        assert len(collection.seeds) == 0

    def test_add(self):
        """Should add seed."""
        collection = SeedCollection()
        seed = GameSeed(value=12345, name="Test")

        collection.add(seed)

        assert len(collection.seeds) == 1

    def test_remove(self):
        """Should remove seed by value."""
        collection = SeedCollection()
        seed = GameSeed(value=12345)
        collection.add(seed)

        result = collection.remove(12345)

        assert result is True
        assert len(collection.seeds) == 0

    def test_remove_not_found(self):
        """Should return False if seed not found."""
        collection = SeedCollection()
        result = collection.remove(99999)
        assert result is False

    def test_get(self):
        """Should get seed by value."""
        collection = SeedCollection()
        seed = GameSeed(value=12345, name="Test")
        collection.add(seed)

        found = collection.get(12345)

        assert found is not None
        assert found.name == "Test"

    def test_get_not_found(self):
        """Should return None if not found."""
        collection = SeedCollection()
        assert collection.get(99999) is None

    def test_toggle_favorite(self):
        """Should toggle favorite status."""
        collection = SeedCollection()
        seed = GameSeed(value=12345)
        collection.add(seed)

        result = collection.toggle_favorite(12345)
        assert result is True
        assert 12345 in collection.favorites

        result = collection.toggle_favorite(12345)
        assert result is False
        assert 12345 not in collection.favorites

    def test_get_favorites(self):
        """Should get favorited seeds."""
        collection = SeedCollection()
        seed1 = GameSeed(value=111)
        seed2 = GameSeed(value=222)
        collection.add(seed1)
        collection.add(seed2)
        collection.toggle_favorite(111)

        favorites = collection.get_favorites()

        assert len(favorites) == 1
        assert favorites[0].value == 111

    def test_search(self):
        """Should search by name and description."""
        collection = SeedCollection()
        seed1 = GameSeed(value=111, name="Murder Mystery")
        seed2 = GameSeed(value=222, name="Theft Case", description="A theft at the museum")
        collection.add(seed1)
        collection.add(seed2)

        murder_results = collection.search("murder")
        assert len(murder_results) == 1
        assert murder_results[0].value == 111

        museum_results = collection.search("museum")
        assert len(museum_results) == 1
        assert museum_results[0].value == 222

    def test_serialization(self):
        """Should serialize and deserialize."""
        collection = SeedCollection()
        collection.add(GameSeed(value=111, name="Test"))
        collection.toggle_favorite(111)

        data = collection.to_dict()
        restored = SeedCollection.from_dict(data)

        assert len(restored.seeds) == 1
        assert 111 in restored.favorites


class TestSeedGenerator:
    """Tests for SeedGenerator."""

    def test_creation(self):
        """Should create generator."""
        generator = SeedGenerator()
        assert generator is not None

    def test_seeded_generator(self):
        """Should produce reproducible seeds with base seed."""
        gen1 = SeedGenerator(base_seed=42)
        seed1 = gen1.generate_themed("noir")

        gen2 = SeedGenerator(base_seed=42)
        seed2 = gen2.generate_themed("noir")

        assert seed1.value == seed2.value

    def test_generate_themed(self):
        """Should generate themed seed."""
        generator = SeedGenerator()
        seed = generator.generate_themed("horror")

        assert seed.value is not None
        assert "Horror" in seed.name
        assert "horror" in seed.description.lower()

    def test_generate_difficulty_easy(self):
        """Should generate easy difficulty seed."""
        generator = SeedGenerator()
        seed = generator.generate_difficulty("easy")

        assert seed.difficulty == "easy"
        assert seed.character_count == 3
        assert seed.twist_enabled is False

    def test_generate_difficulty_hard(self):
        """Should generate hard difficulty seed."""
        generator = SeedGenerator()
        seed = generator.generate_difficulty("hard")

        assert seed.difficulty == "hard"
        assert seed.character_count == 7
        assert seed.twist_enabled is True

    def test_generate_difficulty_nightmare(self):
        """Should generate nightmare difficulty seed."""
        generator = SeedGenerator()
        seed = generator.generate_difficulty("nightmare")

        assert seed.difficulty == "nightmare"
        assert seed.character_count == 10

    def test_generate_with_conflict(self):
        """Should generate seed with conflict type."""
        generator = SeedGenerator()
        seed = generator.generate_with_conflict("murder")

        assert seed.conflict_type == "murder"

    def test_generate_series(self):
        """Should generate related series of seeds."""
        generator = SeedGenerator()
        series = generator.generate_series(5, prefix="Chapter")

        assert len(series) == 5
        for i, seed in enumerate(series):
            assert f"Chapter {i + 1}" in seed.name
