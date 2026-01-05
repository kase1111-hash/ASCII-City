"""
Usage statistics tracking for art assets.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timedelta
from enum import Enum, auto
import json


class FeedbackType(Enum):
    """Types of player feedback."""
    LIKE = auto()
    DISLIKE = auto()
    REPORT = auto()
    FAVORITE = auto()
    FEATURE_REQUEST = auto()


@dataclass
class UsageEvent:
    """Single usage event for tracking."""
    asset_id: str
    event_type: str  # "spawn", "interact", "destroy", etc.
    timestamp: datetime
    environment: Optional[str] = None
    player_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize event to dictionary."""
        return {
            "asset_id": self.asset_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "environment": self.environment,
            "player_id": self.player_id,
            "details": self.details
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UsageEvent":
        """Create event from dictionary."""
        return cls(
            asset_id=data["asset_id"],
            event_type=data["event_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            environment=data.get("environment"),
            player_id=data.get("player_id"),
            details=data.get("details", {})
        )


@dataclass
class FeedbackEntry:
    """Player feedback on an asset."""
    asset_id: str
    player_id: str
    feedback_type: FeedbackType
    timestamp: datetime
    comment: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize feedback to dictionary."""
        return {
            "asset_id": self.asset_id,
            "player_id": self.player_id,
            "feedback_type": self.feedback_type.name,
            "timestamp": self.timestamp.isoformat(),
            "comment": self.comment
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FeedbackEntry":
        """Create feedback from dictionary."""
        return cls(
            asset_id=data["asset_id"],
            player_id=data["player_id"],
            feedback_type=FeedbackType[data["feedback_type"]],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            comment=data.get("comment")
        )


@dataclass
class AssetStats:
    """Aggregated statistics for a single asset."""
    asset_id: str
    total_spawns: int = 0
    total_interactions: int = 0
    total_destroys: int = 0
    likes: int = 0
    dislikes: int = 0
    favorites: int = 0
    reports: int = 0
    environments_used: Set[str] = field(default_factory=set)
    players_interacted: Set[str] = field(default_factory=set)
    first_used: Optional[datetime] = None
    last_used: Optional[datetime] = None

    @property
    def popularity_score(self) -> float:
        """Calculate popularity score."""
        base = self.total_spawns + self.total_interactions * 2
        like_bonus = self.likes * 5 - self.dislikes * 3
        favorite_bonus = self.favorites * 10
        report_penalty = self.reports * 20
        return max(0, base + like_bonus + favorite_bonus - report_penalty)

    @property
    def engagement_rate(self) -> float:
        """Calculate interaction rate per spawn."""
        if self.total_spawns == 0:
            return 0.0
        return self.total_interactions / self.total_spawns

    @property
    def like_ratio(self) -> float:
        """Calculate like/dislike ratio."""
        total = self.likes + self.dislikes
        if total == 0:
            return 0.5
        return self.likes / total

    def record_event(self, event: UsageEvent) -> None:
        """Record a usage event."""
        now = event.timestamp

        if self.first_used is None:
            self.first_used = now
        self.last_used = now

        if event.environment:
            self.environments_used.add(event.environment)

        if event.player_id:
            self.players_interacted.add(event.player_id)

        if event.event_type == "spawn":
            self.total_spawns += 1
        elif event.event_type == "interact":
            self.total_interactions += 1
        elif event.event_type == "destroy":
            self.total_destroys += 1

    def record_feedback(self, feedback: FeedbackEntry) -> None:
        """Record feedback."""
        if feedback.feedback_type == FeedbackType.LIKE:
            self.likes += 1
        elif feedback.feedback_type == FeedbackType.DISLIKE:
            self.dislikes += 1
        elif feedback.feedback_type == FeedbackType.FAVORITE:
            self.favorites += 1
        elif feedback.feedback_type == FeedbackType.REPORT:
            self.reports += 1

    def to_dict(self) -> dict:
        """Serialize stats to dictionary."""
        return {
            "asset_id": self.asset_id,
            "total_spawns": self.total_spawns,
            "total_interactions": self.total_interactions,
            "total_destroys": self.total_destroys,
            "likes": self.likes,
            "dislikes": self.dislikes,
            "favorites": self.favorites,
            "reports": self.reports,
            "environments_used": list(self.environments_used),
            "players_interacted": list(self.players_interacted),
            "first_used": self.first_used.isoformat() if self.first_used else None,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AssetStats":
        """Create stats from dictionary."""
        return cls(
            asset_id=data["asset_id"],
            total_spawns=data.get("total_spawns", 0),
            total_interactions=data.get("total_interactions", 0),
            total_destroys=data.get("total_destroys", 0),
            likes=data.get("likes", 0),
            dislikes=data.get("dislikes", 0),
            favorites=data.get("favorites", 0),
            reports=data.get("reports", 0),
            environments_used=set(data.get("environments_used", [])),
            players_interacted=set(data.get("players_interacted", [])),
            first_used=datetime.fromisoformat(data["first_used"]) if data.get("first_used") else None,
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None
        )


class UsageStats:
    """
    Central usage statistics tracker.

    Tracks all usage events, feedback, and aggregates
    statistics for art assets.
    """

    def __init__(self, max_events: int = 10000):
        self._asset_stats: Dict[str, AssetStats] = {}
        self._recent_events: List[UsageEvent] = []
        self._feedback: List[FeedbackEntry] = []
        self._max_events = max_events
        self._player_favorites: Dict[str, Set[str]] = {}  # player_id -> asset_ids

    def record_event(
        self,
        asset_id: str,
        event_type: str,
        environment: Optional[str] = None,
        player_id: Optional[str] = None,
        details: Dict[str, Any] = None
    ) -> UsageEvent:
        """
        Record a usage event.

        Args:
            asset_id: ID of the asset
            event_type: Type of event (spawn, interact, destroy, etc.)
            environment: Where the event occurred
            player_id: Who triggered the event
            details: Additional event details

        Returns:
            The recorded UsageEvent
        """
        event = UsageEvent(
            asset_id=asset_id,
            event_type=event_type,
            timestamp=datetime.now(),
            environment=environment,
            player_id=player_id,
            details=details or {}
        )

        # Add to recent events
        self._recent_events.append(event)
        if len(self._recent_events) > self._max_events:
            self._recent_events = self._recent_events[-self._max_events:]

        # Update asset stats
        if asset_id not in self._asset_stats:
            self._asset_stats[asset_id] = AssetStats(asset_id=asset_id)
        self._asset_stats[asset_id].record_event(event)

        return event

    def record_feedback(
        self,
        asset_id: str,
        player_id: str,
        feedback_type: FeedbackType,
        comment: Optional[str] = None
    ) -> FeedbackEntry:
        """
        Record player feedback.

        Args:
            asset_id: ID of the asset
            player_id: Who gave the feedback
            feedback_type: Type of feedback
            comment: Optional comment

        Returns:
            The recorded FeedbackEntry
        """
        feedback = FeedbackEntry(
            asset_id=asset_id,
            player_id=player_id,
            feedback_type=feedback_type,
            timestamp=datetime.now(),
            comment=comment
        )

        self._feedback.append(feedback)

        # Update asset stats
        if asset_id not in self._asset_stats:
            self._asset_stats[asset_id] = AssetStats(asset_id=asset_id)
        self._asset_stats[asset_id].record_feedback(feedback)

        # Track favorites
        if feedback_type == FeedbackType.FAVORITE:
            if player_id not in self._player_favorites:
                self._player_favorites[player_id] = set()
            self._player_favorites[player_id].add(asset_id)

        return feedback

    def get_asset_stats(self, asset_id: str) -> Optional[AssetStats]:
        """Get statistics for an asset."""
        return self._asset_stats.get(asset_id)

    def get_all_stats(self) -> Dict[str, AssetStats]:
        """Get all asset statistics."""
        return self._asset_stats.copy()

    def get_recent_events(
        self,
        count: int = 100,
        asset_id: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> List[UsageEvent]:
        """Get recent events with optional filtering."""
        events = self._recent_events

        if asset_id:
            events = [e for e in events if e.asset_id == asset_id]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events[-count:]

    def get_feedback(
        self,
        asset_id: Optional[str] = None,
        player_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None
    ) -> List[FeedbackEntry]:
        """Get feedback with optional filtering."""
        feedback = self._feedback

        if asset_id:
            feedback = [f for f in feedback if f.asset_id == asset_id]

        if player_id:
            feedback = [f for f in feedback if f.player_id == player_id]

        if feedback_type:
            feedback = [f for f in feedback if f.feedback_type == feedback_type]

        return feedback

    def get_player_favorites(self, player_id: str) -> Set[str]:
        """Get a player's favorited assets."""
        return self._player_favorites.get(player_id, set()).copy()

    def get_top_assets(
        self,
        count: int = 10,
        metric: str = "popularity"
    ) -> List[tuple[str, float]]:
        """
        Get top assets by metric.

        Args:
            count: Number of assets to return
            metric: "popularity", "spawns", "interactions", "likes"

        Returns:
            List of (asset_id, score) tuples
        """
        if metric == "popularity":
            key = lambda s: s.popularity_score
        elif metric == "spawns":
            key = lambda s: s.total_spawns
        elif metric == "interactions":
            key = lambda s: s.total_interactions
        elif metric == "likes":
            key = lambda s: s.likes
        else:
            key = lambda s: s.popularity_score

        sorted_stats = sorted(self._asset_stats.values(), key=key, reverse=True)
        return [(s.asset_id, key(s)) for s in sorted_stats[:count]]

    def get_trending(
        self,
        hours: int = 24,
        count: int = 10
    ) -> List[tuple[str, int]]:
        """Get trending assets in recent time period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [e for e in self._recent_events if e.timestamp >= cutoff]

        # Count events per asset
        counts: Dict[str, int] = {}
        for event in recent:
            counts[event.asset_id] = counts.get(event.asset_id, 0) + 1

        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_counts[:count]

    def get_reported_assets(self, min_reports: int = 1) -> List[str]:
        """Get assets with reports."""
        return [
            asset_id for asset_id, stats in self._asset_stats.items()
            if stats.reports >= min_reports
        ]

    def get_environment_popularity(self) -> Dict[str, int]:
        """Get usage counts by environment."""
        env_counts: Dict[str, int] = {}
        for event in self._recent_events:
            if event.environment:
                env_counts[event.environment] = env_counts.get(event.environment, 0) + 1
        return env_counts

    def get_summary(self) -> Dict[str, Any]:
        """Get overall statistics summary."""
        total_spawns = sum(s.total_spawns for s in self._asset_stats.values())
        total_interactions = sum(s.total_interactions for s in self._asset_stats.values())
        total_likes = sum(s.likes for s in self._asset_stats.values())
        total_dislikes = sum(s.dislikes for s in self._asset_stats.values())
        total_reports = sum(s.reports for s in self._asset_stats.values())

        return {
            "total_assets_tracked": len(self._asset_stats),
            "total_events": len(self._recent_events),
            "total_feedback": len(self._feedback),
            "total_spawns": total_spawns,
            "total_interactions": total_interactions,
            "total_likes": total_likes,
            "total_dislikes": total_dislikes,
            "total_reports": total_reports,
            "unique_players": len(self._player_favorites)
        }

    def clear_old_events(self, older_than_days: int = 30) -> int:
        """Clear events older than specified days."""
        cutoff = datetime.now() - timedelta(days=older_than_days)
        original_count = len(self._recent_events)
        self._recent_events = [e for e in self._recent_events if e.timestamp >= cutoff]
        return original_count - len(self._recent_events)

    def to_dict(self) -> dict:
        """Serialize stats to dictionary."""
        return {
            "asset_stats": {k: v.to_dict() for k, v in self._asset_stats.items()},
            "recent_events": [e.to_dict() for e in self._recent_events],
            "feedback": [f.to_dict() for f in self._feedback],
            "player_favorites": {k: list(v) for k, v in self._player_favorites.items()},
            "max_events": self._max_events
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UsageStats":
        """Create stats from dictionary."""
        stats = cls(max_events=data.get("max_events", 10000))

        for asset_id, stat_data in data.get("asset_stats", {}).items():
            stats._asset_stats[asset_id] = AssetStats.from_dict(stat_data)

        for event_data in data.get("recent_events", []):
            stats._recent_events.append(UsageEvent.from_dict(event_data))

        for feedback_data in data.get("feedback", []):
            stats._feedback.append(FeedbackEntry.from_dict(feedback_data))

        for player_id, favorites in data.get("player_favorites", {}).items():
            stats._player_favorites[player_id] = set(favorites)

        return stats
