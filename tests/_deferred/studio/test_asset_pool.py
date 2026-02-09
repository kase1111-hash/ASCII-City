"""
Tests for AssetPool system.
"""

import pytest
from src.shadowengine.studio.asset_pool import AssetPool, AssetQuery, AssetEntry
from src.shadowengine.studio.art import ArtCategory
from src.shadowengine.studio.tags import ObjectType, EnvironmentType, Size, Placement


class TestAssetEntry:
    """Tests for AssetEntry class."""

    def test_create_entry(self, static_tree):
        """Can create asset entry."""
        entry = AssetEntry(asset=static_tree)

        assert entry.asset == static_tree
        assert entry.usage_count == 0
        assert entry.rating == 0.0
        assert entry.rating_count == 0

    def test_record_usage(self, static_tree):
        """Can record usage."""
        entry = AssetEntry(asset=static_tree)
        entry.record_usage("forest")

        assert entry.usage_count == 1
        assert "forest" in entry.environments_used
        assert entry.last_used is not None

    def test_add_rating(self, static_tree):
        """Can add ratings."""
        entry = AssetEntry(asset=static_tree)

        entry.add_rating(4.0)
        assert entry.rating == 4.0
        assert entry.rating_count == 1

        entry.add_rating(2.0)
        assert entry.rating == 3.0  # Average
        assert entry.rating_count == 2

    def test_add_rating_validation(self, static_tree):
        """Invalid rating raises error."""
        entry = AssetEntry(asset=static_tree)

        with pytest.raises(ValueError):
            entry.add_rating(6.0)  # Over 5.0

        with pytest.raises(ValueError):
            entry.add_rating(-1.0)  # Under 0.0

    def test_serialization(self, static_tree):
        """Entry can be serialized and deserialized."""
        entry = AssetEntry(asset=static_tree)
        entry.record_usage("forest")
        entry.add_rating(4.5)

        data = entry.to_dict()
        restored = AssetEntry.from_dict(data)

        assert restored.asset.id == static_tree.id
        assert restored.usage_count == entry.usage_count
        assert restored.rating == entry.rating


class TestAssetQuery:
    """Tests for AssetQuery class."""

    def test_create_empty_query(self):
        """Can create empty query."""
        query = AssetQuery()
        assert query.object_type is None
        assert query.limit == 100

    def test_create_filtered_query(self):
        """Can create query with filters."""
        query = AssetQuery(
            object_type=ObjectType.TREE,
            environment=EnvironmentType.FOREST,
            min_rating=3.0,
            limit=10
        )
        assert query.object_type == ObjectType.TREE
        assert query.environment == EnvironmentType.FOREST
        assert query.min_rating == 3.0
        assert query.limit == 10


class TestAssetPool:
    """Tests for AssetPool class."""

    def test_create_pool(self, empty_pool):
        """Can create empty pool."""
        assert empty_pool.count == 0

    def test_add_asset(self, empty_pool, static_tree):
        """Can add assets to pool."""
        entry = empty_pool.add_asset(static_tree)

        assert empty_pool.count == 1
        assert entry.asset == static_tree

    def test_add_duplicate_asset(self, empty_pool, static_tree):
        """Adding duplicate returns existing entry."""
        entry1 = empty_pool.add_asset(static_tree)
        entry2 = empty_pool.add_asset(static_tree)

        assert entry1 is entry2
        assert empty_pool.count == 1

    def test_remove_asset(self, populated_pool, static_tree):
        """Can remove assets from pool."""
        initial_count = populated_pool.count
        result = populated_pool.remove_asset(static_tree.id)

        assert result is True
        assert populated_pool.count == initial_count - 1

    def test_remove_nonexistent_asset(self, empty_pool):
        """Removing nonexistent asset returns False."""
        assert empty_pool.remove_asset("fake_id") is False

    def test_get_asset(self, populated_pool, static_tree):
        """Can get asset by ID."""
        asset = populated_pool.get_asset(static_tree.id)
        assert asset == static_tree

    def test_get_nonexistent_asset(self, populated_pool):
        """Getting nonexistent asset returns None."""
        assert populated_pool.get_asset("fake_id") is None

    def test_get_entry(self, populated_pool, static_tree):
        """Can get entry by ID."""
        entry = populated_pool.get_entry(static_tree.id)
        assert entry is not None
        assert entry.asset == static_tree

    def test_query_all(self, populated_pool):
        """Empty query returns all assets."""
        results = populated_pool.query(AssetQuery())
        assert len(results) == populated_pool.count

    def test_query_by_object_type(self, populated_pool):
        """Can query by object type."""
        query = AssetQuery(object_type=ObjectType.TREE)
        results = populated_pool.query(query)

        assert len(results) >= 1
        assert all(r.tags.object_type == ObjectType.TREE for r in results)

    def test_query_by_category(self, populated_pool):
        """Can query by category."""
        query = AssetQuery(category=ArtCategory.STATIC)
        results = populated_pool.query(query)

        assert all(r.category == ArtCategory.STATIC for r in results)

    def test_query_by_environment(self, populated_pool):
        """Can query by environment."""
        query = AssetQuery(environment=EnvironmentType.FOREST)
        results = populated_pool.query(query)

        assert len(results) >= 1
        for r in results:
            assert EnvironmentType.FOREST in r.tags.environment_types

    def test_query_by_rating(self, populated_pool, static_tree):
        """Can filter by minimum rating."""
        # Add a rating
        entry = populated_pool.get_entry(static_tree.id)
        entry.add_rating(4.5)

        query = AssetQuery(min_rating=4.0)
        results = populated_pool.query(query)

        assert static_tree in results

        query2 = AssetQuery(min_rating=5.0)
        results2 = populated_pool.query(query2)
        assert static_tree not in results2

    def test_query_limit(self, populated_pool):
        """Query respects limit."""
        query = AssetQuery(limit=1)
        results = populated_pool.query(query)

        assert len(results) == 1

    def test_get_random(self, populated_pool):
        """Can get random asset."""
        asset = populated_pool.get_random()
        assert asset is not None

    def test_get_random_filtered(self, populated_pool):
        """Can get random asset with filter."""
        asset = populated_pool.get_random(object_type=ObjectType.TREE)

        if asset:  # May be None if no trees
            assert asset.tags.object_type == ObjectType.TREE

    def test_get_random_empty_pool(self, empty_pool):
        """Random from empty pool returns None."""
        assert empty_pool.get_random() is None

    def test_get_for_environment(self, populated_pool):
        """Can get assets for environment."""
        results = populated_pool.get_for_environment(EnvironmentType.FOREST, count=5)

        for asset in results:
            assert EnvironmentType.FOREST in asset.tags.environment_types

    def test_get_by_player(self, empty_pool, static_tree, static_rock):
        """Can get assets by player."""
        static_tree.player_id = "player1"
        static_rock.player_id = "player2"

        empty_pool.add_asset(static_tree)
        empty_pool.add_asset(static_rock)

        results = empty_pool.get_by_player("player1")
        assert len(results) == 1
        assert results[0] == static_tree

    def test_record_usage(self, populated_pool, static_tree):
        """Can record asset usage."""
        result = populated_pool.record_usage(static_tree.id, "forest")

        assert result is True
        entry = populated_pool.get_entry(static_tree.id)
        assert entry.usage_count == 1

    def test_rate_asset(self, populated_pool, static_tree):
        """Can rate asset."""
        new_rating = populated_pool.rate_asset(static_tree.id, 4.0)

        assert new_rating == 4.0
        entry = populated_pool.get_entry(static_tree.id)
        assert entry.rating == 4.0

    def test_get_top_rated(self, populated_pool, static_tree, static_rock):
        """Can get top-rated assets."""
        populated_pool.get_entry(static_tree.id).add_rating(5.0)
        populated_pool.get_entry(static_rock.id).add_rating(3.0)

        top = populated_pool.get_top_rated(count=2)

        assert len(top) >= 2
        # First should have higher rating
        assert top[0][1] >= top[1][1]

    def test_get_most_used(self, populated_pool, static_tree):
        """Can get most-used assets."""
        entry = populated_pool.get_entry(static_tree.id)
        for _ in range(10):
            entry.record_usage()

        most_used = populated_pool.get_most_used(count=1)

        assert most_used[0][0] == static_tree
        assert most_used[0][1] == 10

    def test_get_recent(self, populated_pool):
        """Can get recent assets."""
        recent = populated_pool.get_recent(count=3)
        assert len(recent) <= 3

    def test_get_statistics(self, populated_pool):
        """Can get pool statistics."""
        stats = populated_pool.get_statistics()

        assert "total_assets" in stats
        assert "static_count" in stats
        assert "dynamic_count" in stats
        assert "by_type" in stats

    def test_clear(self, populated_pool):
        """Can clear pool."""
        initial_count = populated_pool.count
        cleared = populated_pool.clear()

        assert cleared == initial_count
        assert populated_pool.count == 0

    def test_serialization(self, populated_pool):
        """Pool can be serialized and deserialized."""
        data = populated_pool.to_dict()
        restored = AssetPool.from_dict(data)

        assert restored.count == populated_pool.count

    def test_contains(self, populated_pool, static_tree):
        """Can check if asset in pool."""
        assert static_tree.id in populated_pool
        assert "fake_id" not in populated_pool

    def test_len(self, populated_pool):
        """Pool has correct length."""
        assert len(populated_pool) == populated_pool.count

    def test_iter(self, populated_pool):
        """Can iterate over pool."""
        assets = list(populated_pool)
        assert len(assets) == populated_pool.count
