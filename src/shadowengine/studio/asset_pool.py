"""
Asset pool for world integration of player-created art.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set, Tuple
from datetime import datetime
import random

from .art import ASCIIArt, ArtCategory
from .static_art import StaticArt
from .entity import DynamicEntity
from .tags import (
    ObjectType, Size, Placement, EnvironmentType
)


@dataclass
class AssetQuery:
    """Query parameters for finding assets."""
    object_type: Optional[ObjectType] = None
    category: Optional[ArtCategory] = None
    environment: Optional[EnvironmentType] = None
    size: Optional[Size] = None
    placement: Optional[Placement] = None
    min_rating: float = 0.0
    player_id: Optional[str] = None
    tags: Optional[Set[str]] = None
    limit: int = 100


@dataclass
class AssetEntry:
    """Entry in the asset pool with metadata."""
    asset: ASCIIArt
    usage_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    added_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    environments_used: Set[str] = field(default_factory=set)

    def record_usage(self, environment: Optional[str] = None) -> None:
        """Record that asset was used."""
        self.usage_count += 1
        self.last_used = datetime.now()
        if environment:
            self.environments_used.add(environment)

    def add_rating(self, rating: float) -> float:
        """Add a rating and return new average."""
        if not 0.0 <= rating <= 5.0:
            raise ValueError("Rating must be between 0.0 and 5.0")

        total = self.rating * self.rating_count + rating
        self.rating_count += 1
        self.rating = total / self.rating_count
        return self.rating

    def to_dict(self) -> dict:
        """Serialize entry to dictionary."""
        return {
            "asset": self.asset.to_dict(),
            "usage_count": self.usage_count,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "added_at": self.added_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "environments_used": list(self.environments_used)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AssetEntry":
        """Create entry from dictionary."""
        asset_data = data["asset"]
        category = ArtCategory[asset_data.get("category", "STATIC")]

        if category == ArtCategory.STATIC:
            asset = StaticArt.from_dict(asset_data)
        else:
            asset = DynamicEntity.from_dict(asset_data)

        return cls(
            asset=asset,
            usage_count=data.get("usage_count", 0),
            rating=data.get("rating", 0.0),
            rating_count=data.get("rating_count", 0),
            added_at=datetime.fromisoformat(data["added_at"]) if "added_at" in data else datetime.now(),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            environments_used=set(data.get("environments_used", []))
        )


class AssetPool:
    """
    Central pool for world-integrated art assets.

    Manages all player-created art that can be used in
    world generation and gameplay.
    """

    def __init__(self):
        self._entries: Dict[str, AssetEntry] = {}
        self._by_type: Dict[ObjectType, Set[str]] = {}
        self._by_category: Dict[ArtCategory, Set[str]] = {}
        self._by_environment: Dict[EnvironmentType, Set[str]] = {}
        self._by_player: Dict[str, Set[str]] = {}

    @property
    def count(self) -> int:
        """Total number of assets in pool."""
        return len(self._entries)

    def add_asset(self, asset: ASCIIArt) -> AssetEntry:
        """
        Add asset to the pool.

        Args:
            asset: Art asset to add

        Returns:
            AssetEntry for the added asset
        """
        if asset.id in self._entries:
            return self._entries[asset.id]

        entry = AssetEntry(asset=asset)
        self._entries[asset.id] = entry

        # Index by type
        obj_type = asset.tags.object_type
        if obj_type not in self._by_type:
            self._by_type[obj_type] = set()
        self._by_type[obj_type].add(asset.id)

        # Index by category
        if asset.category not in self._by_category:
            self._by_category[asset.category] = set()
        self._by_category[asset.category].add(asset.id)

        # Index by environments
        for env in asset.tags.environment_types:
            if env not in self._by_environment:
                self._by_environment[env] = set()
            self._by_environment[env].add(asset.id)

        # Index by player
        if asset.player_id not in self._by_player:
            self._by_player[asset.player_id] = set()
        self._by_player[asset.player_id].add(asset.id)

        return entry

    def remove_asset(self, asset_id: str) -> bool:
        """
        Remove asset from pool.

        Args:
            asset_id: ID of asset to remove

        Returns:
            True if asset was removed
        """
        if asset_id not in self._entries:
            return False

        entry = self._entries[asset_id]
        asset = entry.asset

        # Remove from indices
        obj_type = asset.tags.object_type
        if obj_type in self._by_type:
            self._by_type[obj_type].discard(asset_id)

        if asset.category in self._by_category:
            self._by_category[asset.category].discard(asset_id)

        for env in asset.tags.environment_types:
            if env in self._by_environment:
                self._by_environment[env].discard(asset_id)

        if asset.player_id in self._by_player:
            self._by_player[asset.player_id].discard(asset_id)

        del self._entries[asset_id]
        return True

    def get_asset(self, asset_id: str) -> Optional[ASCIIArt]:
        """Get asset by ID."""
        entry = self._entries.get(asset_id)
        return entry.asset if entry else None

    def get_entry(self, asset_id: str) -> Optional[AssetEntry]:
        """Get asset entry by ID."""
        return self._entries.get(asset_id)

    def query(self, query: AssetQuery) -> List[ASCIIArt]:
        """
        Query assets matching criteria.

        Args:
            query: Query parameters

        Returns:
            List of matching assets
        """
        # Start with all asset IDs
        candidates = set(self._entries.keys())

        # Filter by object type
        if query.object_type is not None:
            type_ids = self._by_type.get(query.object_type, set())
            candidates &= type_ids

        # Filter by category
        if query.category is not None:
            cat_ids = self._by_category.get(query.category, set())
            candidates &= cat_ids

        # Filter by environment
        if query.environment is not None:
            env_ids = self._by_environment.get(query.environment, set())
            candidates &= env_ids

        # Filter by player
        if query.player_id is not None:
            player_ids = self._by_player.get(query.player_id, set())
            candidates &= player_ids

        # Apply remaining filters
        results = []
        for asset_id in candidates:
            entry = self._entries[asset_id]
            asset = entry.asset

            # Check rating
            if entry.rating < query.min_rating:
                continue

            # Check size
            if query.size is not None and asset.tags.size != query.size:
                continue

            # Check placement
            if query.placement is not None and asset.tags.placement != query.placement:
                continue

            # Check custom tags
            if query.tags is not None:
                if not query.tags.issubset(asset.tags.custom_tags):
                    continue

            results.append(asset)

            if len(results) >= query.limit:
                break

        return results

    def get_random(
        self,
        object_type: Optional[ObjectType] = None,
        environment: Optional[EnvironmentType] = None,
        weighted: bool = True
    ) -> Optional[ASCIIArt]:
        """
        Get a random asset, optionally weighted by spawn_weight.

        Args:
            object_type: Filter by object type
            environment: Filter by environment
            weighted: Use spawn weights if True

        Returns:
            Random asset or None if no matches
        """
        query = AssetQuery(
            object_type=object_type,
            environment=environment
        )
        candidates = self.query(query)

        if not candidates:
            return None

        if weighted:
            weights = []
            for asset in candidates:
                if isinstance(asset, StaticArt):
                    weights.append(asset.spawn_weight)
                else:
                    weights.append(1.0)

            return random.choices(candidates, weights=weights, k=1)[0]
        else:
            return random.choice(candidates)

    def get_for_environment(
        self,
        environment: EnvironmentType,
        count: int = 10
    ) -> List[ASCIIArt]:
        """
        Get assets suitable for an environment.

        Args:
            environment: Target environment
            count: Maximum number to return

        Returns:
            List of suitable assets
        """
        query = AssetQuery(environment=environment, limit=count)
        return self.query(query)

    def get_by_player(self, player_id: str) -> List[ASCIIArt]:
        """Get all assets by a player."""
        query = AssetQuery(player_id=player_id)
        return self.query(query)

    def record_usage(
        self,
        asset_id: str,
        environment: Optional[str] = None
    ) -> bool:
        """
        Record that an asset was used.

        Args:
            asset_id: ID of used asset
            environment: Where it was used

        Returns:
            True if usage was recorded
        """
        entry = self._entries.get(asset_id)
        if entry:
            entry.record_usage(environment)
            return True
        return False

    def rate_asset(self, asset_id: str, rating: float) -> Optional[float]:
        """
        Rate an asset.

        Args:
            asset_id: ID of asset to rate
            rating: Rating value (0.0 to 5.0)

        Returns:
            New average rating or None if asset not found
        """
        entry = self._entries.get(asset_id)
        if entry:
            return entry.add_rating(rating)
        return None

    def get_top_rated(self, count: int = 10) -> List[Tuple[ASCIIArt, float]]:
        """Get top-rated assets with their ratings."""
        sorted_entries = sorted(
            self._entries.values(),
            key=lambda e: (e.rating, e.rating_count),
            reverse=True
        )
        return [(e.asset, e.rating) for e in sorted_entries[:count]]

    def get_most_used(self, count: int = 10) -> List[Tuple[ASCIIArt, int]]:
        """Get most-used assets with their usage counts."""
        sorted_entries = sorted(
            self._entries.values(),
            key=lambda e: e.usage_count,
            reverse=True
        )
        return [(e.asset, e.usage_count) for e in sorted_entries[:count]]

    def get_recent(self, count: int = 10) -> List[ASCIIArt]:
        """Get most recently added assets."""
        sorted_entries = sorted(
            self._entries.values(),
            key=lambda e: e.added_at,
            reverse=True
        )
        return [e.asset for e in sorted_entries[:count]]

    def get_statistics(self) -> Dict[str, Any]:
        """Get pool statistics."""
        total_usage = sum(e.usage_count for e in self._entries.values())
        rated_count = sum(1 for e in self._entries.values() if e.rating_count > 0)

        return {
            "total_assets": self.count,
            "static_count": len(self._by_category.get(ArtCategory.STATIC, set())),
            "dynamic_count": len(self._by_category.get(ArtCategory.DYNAMIC, set())),
            "total_usage": total_usage,
            "rated_count": rated_count,
            "unique_players": len(self._by_player),
            "by_type": {t.name: len(ids) for t, ids in self._by_type.items()},
            "by_environment": {e.name: len(ids) for e, ids in self._by_environment.items()}
        }

    def clear(self) -> int:
        """Clear all assets from pool. Returns count cleared."""
        count = self.count
        self._entries.clear()
        self._by_type.clear()
        self._by_category.clear()
        self._by_environment.clear()
        self._by_player.clear()
        return count

    def to_dict(self) -> dict:
        """Serialize pool to dictionary."""
        return {
            "entries": [entry.to_dict() for entry in self._entries.values()]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AssetPool":
        """Create pool from dictionary."""
        pool = cls()
        for entry_data in data.get("entries", []):
            entry = AssetEntry.from_dict(entry_data)
            pool._entries[entry.asset.id] = entry

            # Rebuild indices
            asset = entry.asset
            obj_type = asset.tags.object_type
            if obj_type not in pool._by_type:
                pool._by_type[obj_type] = set()
            pool._by_type[obj_type].add(asset.id)

            if asset.category not in pool._by_category:
                pool._by_category[asset.category] = set()
            pool._by_category[asset.category].add(asset.id)

            for env in asset.tags.environment_types:
                if env not in pool._by_environment:
                    pool._by_environment[env] = set()
                pool._by_environment[env].add(asset.id)

            if asset.player_id not in pool._by_player:
                pool._by_player[asset.player_id] = set()
            pool._by_player[asset.player_id].add(asset.id)

        return pool

    def __len__(self) -> int:
        return self.count

    def __contains__(self, asset_id: str) -> bool:
        return asset_id in self._entries

    def __iter__(self):
        return iter(e.asset for e in self._entries.values())
