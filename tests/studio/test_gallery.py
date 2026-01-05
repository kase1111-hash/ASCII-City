"""
Tests for Gallery system.
"""

import pytest
import json
from src.shadowengine.studio.gallery import (
    Gallery, GalleryEntry, GalleryCategory, ContentRating
)
from src.shadowengine.studio.tags import ObjectType


class TestGalleryCategory:
    """Tests for GalleryCategory enum."""

    def test_categories_exist(self):
        """All categories exist."""
        expected = [
            "FEATURED", "POPULAR", "RECENT", "TRENDING",
            "CLASSIC", "COMMUNITY", "SEASONAL", "CONTEST"
        ]
        for name in expected:
            assert hasattr(GalleryCategory, name)


class TestContentRating:
    """Tests for ContentRating enum."""

    def test_ratings_exist(self):
        """All ratings exist."""
        expected = ["EVERYONE", "TEEN", "MATURE"]
        for name in expected:
            assert hasattr(ContentRating, name)

    def test_rating_ordering(self):
        """Ratings have correct ordering."""
        assert ContentRating.EVERYONE.value < ContentRating.TEEN.value
        assert ContentRating.TEEN.value < ContentRating.MATURE.value


class TestGalleryEntry:
    """Tests for GalleryEntry class."""

    def test_create_entry(self, static_tree):
        """Can create gallery entry."""
        entry = GalleryEntry(
            art=static_tree,
            title="Beautiful Tree",
            creator_id="player1",
            creator_name="TreeLover"
        )

        assert entry.title == "Beautiful Tree"
        assert entry.creator_id == "player1"
        assert entry.likes == 0
        assert entry.downloads == 0

    def test_add_like(self, static_tree):
        """Can add likes."""
        entry = GalleryEntry(art=static_tree, title="Test", creator_id="p1")

        new_count = entry.add_like()
        assert new_count == 1
        assert entry.likes == 1

    def test_remove_like(self, static_tree):
        """Can remove likes."""
        entry = GalleryEntry(art=static_tree, title="Test", creator_id="p1")
        entry.likes = 5

        new_count = entry.remove_like()
        assert new_count == 4

    def test_remove_like_minimum(self, static_tree):
        """Likes don't go below zero."""
        entry = GalleryEntry(art=static_tree, title="Test", creator_id="p1")

        new_count = entry.remove_like()
        assert new_count == 0

    def test_record_download(self, static_tree):
        """Can record downloads."""
        entry = GalleryEntry(art=static_tree, title="Test", creator_id="p1")

        count = entry.record_download()
        assert count == 1

    def test_record_view(self, static_tree):
        """Can record views."""
        entry = GalleryEntry(art=static_tree, title="Test", creator_id="p1")

        count = entry.record_view()
        assert count == 1

    def test_add_comment(self, static_tree):
        """Can add comments."""
        entry = GalleryEntry(art=static_tree, title="Test", creator_id="p1")

        comment = entry.add_comment("player2", "Commenter", "Great work!")

        assert "id" in comment
        assert comment["text"] == "Great work!"
        assert len(entry.comments) == 1

    def test_remove_comment(self, static_tree):
        """Can remove comments."""
        entry = GalleryEntry(art=static_tree, title="Test", creator_id="p1")
        comment = entry.add_comment("player2", "Commenter", "Great work!")

        result = entry.remove_comment(comment["id"])
        assert result is True
        assert len(entry.comments) == 0

        result = entry.remove_comment("fake_id")
        assert result is False

    def test_set_featured(self, static_tree):
        """Can set featured status."""
        entry = GalleryEntry(art=static_tree, title="Test", creator_id="p1")

        entry.set_featured(True)
        assert entry.featured is True
        assert entry.featured_at is not None
        assert entry.category == GalleryCategory.FEATURED

        entry.set_featured(False)
        assert entry.featured is False
        assert entry.featured_at is None

    def test_popularity_score(self, static_tree):
        """Popularity score is calculated correctly."""
        entry = GalleryEntry(art=static_tree, title="Test", creator_id="p1")
        entry.likes = 10
        entry.downloads = 5
        entry.views = 100

        # 10*3 + 5*2 + 100*0.1 = 30 + 10 + 10 = 50
        assert entry.popularity_score == 50.0

    def test_serialization(self, static_tree):
        """Entry can be serialized and deserialized."""
        entry = GalleryEntry(
            art=static_tree,
            title="Test",
            creator_id="p1",
            description="A test entry",
            tags={"tag1", "tag2"}
        )
        entry.add_like()

        data = entry.to_dict()
        restored = GalleryEntry.from_dict(data)

        assert restored.id == entry.id
        assert restored.title == entry.title
        assert restored.likes == entry.likes


class TestGallery:
    """Tests for Gallery class."""

    def test_create_gallery(self, empty_gallery):
        """Can create empty gallery."""
        assert empty_gallery.count == 0

    def test_submit_art(self, empty_gallery, static_tree):
        """Can submit art to gallery."""
        entry = empty_gallery.submit(
            art=static_tree,
            title="My Tree",
            creator_id="player1",
            creator_name="TreeLover",
            description="A beautiful tree",
            tags={"tree", "nature"}
        )

        assert entry is not None
        assert empty_gallery.count == 1

    def test_remove_entry(self, populated_gallery):
        """Can remove entry from gallery."""
        entries = list(populated_gallery)
        entry_id = entries[0].id
        initial_count = populated_gallery.count

        result = populated_gallery.remove(entry_id)

        assert result is True
        assert populated_gallery.count == initial_count - 1

    def test_remove_nonexistent(self, empty_gallery):
        """Removing nonexistent entry returns False."""
        assert empty_gallery.remove("fake_id") is False

    def test_get_entry(self, populated_gallery):
        """Can get entry by ID."""
        entries = list(populated_gallery)
        entry = populated_gallery.get_entry(entries[0].id)

        assert entry is not None
        assert entry.id == entries[0].id

    def test_view_entry(self, populated_gallery):
        """Viewing entry records view."""
        entries = list(populated_gallery)
        initial_views = entries[0].views

        entry = populated_gallery.view_entry(entries[0].id)

        assert entry.views == initial_views + 1

    def test_like_entry(self, populated_gallery):
        """Can like entry."""
        entries = list(populated_gallery)
        entry_id = entries[0].id

        result = populated_gallery.like_entry(entry_id, "player_liker")

        assert result is True
        assert entries[0].likes == 1

    def test_like_entry_duplicate(self, populated_gallery):
        """Can't like same entry twice."""
        entries = list(populated_gallery)
        entry_id = entries[0].id

        populated_gallery.like_entry(entry_id, "player_liker")
        result = populated_gallery.like_entry(entry_id, "player_liker")

        assert result is False
        assert entries[0].likes == 1

    def test_unlike_entry(self, populated_gallery):
        """Can unlike entry."""
        entries = list(populated_gallery)
        entry_id = entries[0].id

        populated_gallery.like_entry(entry_id, "player_liker")
        result = populated_gallery.unlike_entry(entry_id, "player_liker")

        assert result is True
        assert entries[0].likes == 0

    def test_download_entry(self, populated_gallery):
        """Can download entry."""
        entries = list(populated_gallery)

        art = populated_gallery.download_entry(entries[0].id)

        assert art is not None
        assert art.id != entries[0].art.id  # Should be a copy
        assert entries[0].downloads == 1

    def test_search_all(self, populated_gallery):
        """Empty search returns all."""
        results = populated_gallery.search()
        assert len(results) == populated_gallery.count

    def test_search_by_query(self, populated_gallery):
        """Can search by text query."""
        results = populated_gallery.search(query="tree")
        assert len(results) >= 1
        assert any("tree" in r.title.lower() for r in results)

    def test_search_by_tags(self, populated_gallery):
        """Can search by tags."""
        results = populated_gallery.search(tags={"nature"})
        assert len(results) >= 1

    def test_search_by_creator(self, populated_gallery):
        """Can search by creator."""
        results = populated_gallery.search(creator_id="player1")
        assert all(r.creator_id == "player1" for r in results)

    def test_search_by_object_type(self, populated_gallery):
        """Can search by object type."""
        results = populated_gallery.search(object_type=ObjectType.TREE)
        assert all(r.art.tags.object_type == ObjectType.TREE for r in results)

    def test_search_sorted(self, populated_gallery):
        """Can sort search results."""
        entries = list(populated_gallery)
        entries[0].add_like()
        entries[0].add_like()

        results = populated_gallery.search(sort_by="likes")

        if len(results) >= 2:
            assert results[0].likes >= results[1].likes

    def test_search_limit(self, populated_gallery):
        """Search respects limit."""
        results = populated_gallery.search(limit=1)
        assert len(results) == 1

    def test_get_featured(self, populated_gallery):
        """Can get featured entries."""
        entries = list(populated_gallery)
        populated_gallery.feature_entry(entries[0].id)

        featured = populated_gallery.get_featured()
        assert len(featured) >= 1
        assert all(e.featured for e in featured)

    def test_get_popular(self, populated_gallery):
        """Can get popular entries."""
        popular = populated_gallery.get_popular(limit=5)
        assert len(popular) <= 5

    def test_get_recent(self, populated_gallery):
        """Can get recent entries."""
        recent = populated_gallery.get_recent(limit=5)
        assert len(recent) <= 5

    def test_get_by_creator(self, populated_gallery):
        """Can get entries by creator."""
        entries = populated_gallery.get_by_creator("player1")
        assert all(e.creator_id == "player1" for e in entries)

    def test_get_player_likes(self, populated_gallery):
        """Can get player's liked entries."""
        entries = list(populated_gallery)
        populated_gallery.like_entry(entries[0].id, "player_liker")
        populated_gallery.like_entry(entries[1].id, "player_liker")

        liked = populated_gallery.get_player_likes("player_liker")
        assert len(liked) == 2

    def test_feature_entry(self, populated_gallery):
        """Can feature entry."""
        entries = list(populated_gallery)

        result = populated_gallery.feature_entry(entries[0].id)

        assert result is True
        assert entries[0].featured is True
        assert entries[0].category == GalleryCategory.FEATURED

    def test_unfeature_entry(self, populated_gallery):
        """Can unfeature entry."""
        entries = list(populated_gallery)
        populated_gallery.feature_entry(entries[0].id)

        result = populated_gallery.unfeature_entry(entries[0].id)

        assert result is True
        assert entries[0].featured is False
        assert entries[0].category == GalleryCategory.COMMUNITY

    def test_get_statistics(self, populated_gallery):
        """Can get gallery statistics."""
        stats = populated_gallery.get_statistics()

        assert "total_entries" in stats
        assert "total_likes" in stats
        assert "unique_creators" in stats
        assert "popular_tags" in stats

    def test_export_entry(self, populated_gallery):
        """Can export entry as JSON."""
        entries = list(populated_gallery)

        json_str = populated_gallery.export_entry(entries[0].id)

        assert json_str is not None
        data = json.loads(json_str)
        assert "art" in data
        assert "title" in data

    def test_import_entry(self, empty_gallery, populated_gallery):
        """Can import entry from JSON."""
        entries = list(populated_gallery)
        json_str = populated_gallery.export_entry(entries[0].id)

        new_entry = empty_gallery.import_entry(
            json_str,
            importer_id="importer1",
            importer_name="Importer"
        )

        assert new_entry is not None
        assert new_entry.creator_id == "importer1"
        assert "(imported)" in new_entry.title
        assert empty_gallery.count == 1

    def test_import_invalid_json(self, empty_gallery):
        """Invalid JSON returns None."""
        result = empty_gallery.import_entry("invalid json", "p1")
        assert result is None

    def test_serialization(self, populated_gallery):
        """Gallery can be serialized and deserialized."""
        # Add some likes
        entries = list(populated_gallery)
        populated_gallery.like_entry(entries[0].id, "player_liker")

        data = populated_gallery.to_dict()
        restored = Gallery.from_dict(data)

        assert restored.count == populated_gallery.count
        assert len(restored._likes_by_player) == len(populated_gallery._likes_by_player)

    def test_contains(self, populated_gallery):
        """Can check if entry in gallery."""
        entries = list(populated_gallery)
        assert entries[0].id in populated_gallery
        assert "fake_id" not in populated_gallery

    def test_len(self, populated_gallery):
        """Gallery has correct length."""
        assert len(populated_gallery) == populated_gallery.count

    def test_iter(self, populated_gallery):
        """Can iterate over gallery."""
        entries = list(populated_gallery)
        assert len(entries) == populated_gallery.count
