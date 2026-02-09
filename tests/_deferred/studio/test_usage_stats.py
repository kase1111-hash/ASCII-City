"""
Tests for UsageStats system.
"""

import pytest
import time
from datetime import datetime, timedelta
from src.shadowengine.studio.usage_stats import (
    UsageStats, UsageEvent, FeedbackEntry, FeedbackType, AssetStats
)


class TestFeedbackType:
    """Tests for FeedbackType enum."""

    def test_types_exist(self):
        """All feedback types exist."""
        expected = ["LIKE", "DISLIKE", "REPORT", "FAVORITE", "FEATURE_REQUEST"]
        for name in expected:
            assert hasattr(FeedbackType, name)


class TestUsageEvent:
    """Tests for UsageEvent class."""

    def test_create_event(self):
        """Can create usage event."""
        event = UsageEvent(
            asset_id="asset1",
            event_type="spawn",
            timestamp=datetime.now(),
            environment="forest"
        )
        assert event.asset_id == "asset1"
        assert event.event_type == "spawn"
        assert event.environment == "forest"

    def test_serialization(self):
        """Event can be serialized and deserialized."""
        event = UsageEvent(
            asset_id="asset1",
            event_type="interact",
            timestamp=datetime.now(),
            player_id="player1",
            details={"key": "value"}
        )
        data = event.to_dict()
        restored = UsageEvent.from_dict(data)

        assert restored.asset_id == event.asset_id
        assert restored.event_type == event.event_type
        assert restored.details == event.details


class TestFeedbackEntry:
    """Tests for FeedbackEntry class."""

    def test_create_feedback(self):
        """Can create feedback entry."""
        feedback = FeedbackEntry(
            asset_id="asset1",
            player_id="player1",
            feedback_type=FeedbackType.LIKE,
            timestamp=datetime.now()
        )
        assert feedback.feedback_type == FeedbackType.LIKE

    def test_feedback_with_comment(self):
        """Can add comment to feedback."""
        feedback = FeedbackEntry(
            asset_id="asset1",
            player_id="player1",
            feedback_type=FeedbackType.REPORT,
            timestamp=datetime.now(),
            comment="Inappropriate content"
        )
        assert feedback.comment == "Inappropriate content"

    def test_serialization(self):
        """Feedback can be serialized and deserialized."""
        feedback = FeedbackEntry(
            asset_id="asset1",
            player_id="player1",
            feedback_type=FeedbackType.FAVORITE,
            timestamp=datetime.now()
        )
        data = feedback.to_dict()
        restored = FeedbackEntry.from_dict(data)

        assert restored.feedback_type == feedback.feedback_type
        assert restored.player_id == feedback.player_id


class TestAssetStats:
    """Tests for AssetStats class."""

    def test_create_stats(self):
        """Can create asset stats."""
        stats = AssetStats(asset_id="asset1")

        assert stats.total_spawns == 0
        assert stats.total_interactions == 0
        assert stats.likes == 0

    def test_popularity_score(self):
        """Popularity score is calculated correctly."""
        stats = AssetStats(asset_id="asset1")
        stats.total_spawns = 10
        stats.total_interactions = 5
        stats.likes = 3
        stats.dislikes = 1

        # 10 + 5*2 + 3*5 - 1*3 = 10 + 10 + 15 - 3 = 32
        assert stats.popularity_score == 32

    def test_engagement_rate(self):
        """Engagement rate is calculated correctly."""
        stats = AssetStats(asset_id="asset1")
        stats.total_spawns = 10
        stats.total_interactions = 5

        assert stats.engagement_rate == 0.5

    def test_engagement_rate_zero_spawns(self):
        """Engagement rate with zero spawns is 0."""
        stats = AssetStats(asset_id="asset1")
        assert stats.engagement_rate == 0.0

    def test_like_ratio(self):
        """Like ratio is calculated correctly."""
        stats = AssetStats(asset_id="asset1")
        stats.likes = 8
        stats.dislikes = 2

        assert stats.like_ratio == 0.8

    def test_like_ratio_no_votes(self):
        """Like ratio with no votes is 0.5."""
        stats = AssetStats(asset_id="asset1")
        assert stats.like_ratio == 0.5

    def test_record_event(self):
        """Can record events."""
        stats = AssetStats(asset_id="asset1")
        event = UsageEvent(
            asset_id="asset1",
            event_type="spawn",
            timestamp=datetime.now(),
            environment="forest",
            player_id="player1"
        )
        stats.record_event(event)

        assert stats.total_spawns == 1
        assert "forest" in stats.environments_used
        assert "player1" in stats.players_interacted

    def test_record_feedback(self):
        """Can record feedback."""
        stats = AssetStats(asset_id="asset1")

        like = FeedbackEntry(
            asset_id="asset1",
            player_id="player1",
            feedback_type=FeedbackType.LIKE,
            timestamp=datetime.now()
        )
        stats.record_feedback(like)
        assert stats.likes == 1

        dislike = FeedbackEntry(
            asset_id="asset1",
            player_id="player2",
            feedback_type=FeedbackType.DISLIKE,
            timestamp=datetime.now()
        )
        stats.record_feedback(dislike)
        assert stats.dislikes == 1


class TestUsageStats:
    """Tests for UsageStats class."""

    def test_create_stats(self, empty_stats):
        """Can create usage stats."""
        assert len(empty_stats._asset_stats) == 0
        assert len(empty_stats._recent_events) == 0

    def test_record_event(self, empty_stats):
        """Can record events."""
        event = empty_stats.record_event(
            asset_id="asset1",
            event_type="spawn",
            environment="forest",
            player_id="player1"
        )

        assert event.asset_id == "asset1"
        assert len(empty_stats._recent_events) == 1

        stats = empty_stats.get_asset_stats("asset1")
        assert stats is not None
        assert stats.total_spawns == 1

    def test_record_feedback(self, empty_stats):
        """Can record feedback."""
        feedback = empty_stats.record_feedback(
            asset_id="asset1",
            player_id="player1",
            feedback_type=FeedbackType.LIKE
        )

        assert feedback.feedback_type == FeedbackType.LIKE

        stats = empty_stats.get_asset_stats("asset1")
        assert stats.likes == 1

    def test_record_favorite(self, empty_stats):
        """Favorites are tracked per player."""
        empty_stats.record_feedback(
            asset_id="asset1",
            player_id="player1",
            feedback_type=FeedbackType.FAVORITE
        )

        favorites = empty_stats.get_player_favorites("player1")
        assert "asset1" in favorites

    def test_get_recent_events(self, stats_with_data):
        """Can get recent events."""
        events = stats_with_data.get_recent_events(count=10)
        assert len(events) <= 10

    def test_get_recent_events_filtered(self, stats_with_data):
        """Can filter recent events."""
        events = stats_with_data.get_recent_events(event_type="spawn")
        assert all(e.event_type == "spawn" for e in events)

    def test_get_feedback(self, stats_with_data):
        """Can get feedback."""
        feedback = stats_with_data.get_feedback()
        assert len(feedback) > 0

    def test_get_feedback_filtered(self, stats_with_data):
        """Can filter feedback."""
        likes = stats_with_data.get_feedback(feedback_type=FeedbackType.LIKE)
        assert all(f.feedback_type == FeedbackType.LIKE for f in likes)

    def test_get_top_assets(self, stats_with_data):
        """Can get top assets by metric."""
        top = stats_with_data.get_top_assets(count=5, metric="spawns")
        assert len(top) <= 5

        # Should be sorted by spawns descending
        if len(top) >= 2:
            assert top[0][1] >= top[1][1]

    def test_get_trending(self, empty_stats):
        """Can get trending assets."""
        # Add some recent events
        for i in range(5):
            empty_stats.record_event("asset1", "spawn")
        for i in range(3):
            empty_stats.record_event("asset2", "spawn")

        trending = empty_stats.get_trending(hours=24, count=5)

        assert len(trending) == 2
        assert trending[0][0] == "asset1"  # More events
        assert trending[0][1] == 5

    def test_get_reported_assets(self, empty_stats):
        """Can get reported assets."""
        empty_stats.record_feedback("asset1", "player1", FeedbackType.REPORT)
        empty_stats.record_feedback("asset1", "player2", FeedbackType.REPORT)
        empty_stats.record_feedback("asset2", "player1", FeedbackType.LIKE)

        reported = empty_stats.get_reported_assets(min_reports=2)
        assert "asset1" in reported
        assert "asset2" not in reported

    def test_get_environment_popularity(self, stats_with_data):
        """Can get environment popularity."""
        popularity = stats_with_data.get_environment_popularity()

        assert "forest" in popularity
        assert popularity["forest"] > 0

    def test_get_summary(self, stats_with_data):
        """Can get summary statistics."""
        summary = stats_with_data.get_summary()

        assert "total_assets_tracked" in summary
        assert "total_events" in summary
        assert "total_feedback" in summary
        assert "total_likes" in summary

    def test_clear_old_events(self, empty_stats):
        """Can clear old events."""
        # Add some events
        for i in range(10):
            empty_stats.record_event("asset1", "spawn")

        # All are recent, none should be cleared
        cleared = empty_stats.clear_old_events(older_than_days=1)
        assert cleared == 0

    def test_max_events_limit(self):
        """Events are limited."""
        stats = UsageStats(max_events=5)

        for i in range(10):
            stats.record_event("asset1", "spawn")

        assert len(stats._recent_events) == 5

    def test_serialization(self, stats_with_data):
        """Stats can be serialized and deserialized."""
        data = stats_with_data.to_dict()
        restored = UsageStats.from_dict(data)

        assert len(restored._asset_stats) == len(stats_with_data._asset_stats)
        assert len(restored._feedback) == len(stats_with_data._feedback)
