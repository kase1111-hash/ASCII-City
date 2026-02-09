"""
Gallery system for community sharing and discovery.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
from enum import Enum, auto
import uuid
import json

from .art import ASCIIArt, ArtCategory
from .static_art import StaticArt
from .entity import DynamicEntity
from .tags import ObjectType


class GalleryCategory(Enum):
    """Categories for gallery organization."""
    FEATURED = auto()      # Staff picks
    POPULAR = auto()       # Most liked
    RECENT = auto()        # Newest
    TRENDING = auto()      # Rising popularity
    CLASSIC = auto()       # High-quality staples
    COMMUNITY = auto()     # Community favorites
    SEASONAL = auto()      # Time-limited/seasonal
    CONTEST = auto()       # Contest entries


class ContentRating(Enum):
    """Content rating for art."""
    EVERYONE = auto()      # Suitable for all
    TEEN = auto()          # Some mature themes
    MATURE = auto()        # Adult content


@dataclass
class GalleryEntry:
    """
    Entry in the gallery for sharing.

    Attributes:
        id: Unique entry ID
        art: The ASCII art
        title: Display title
        description: Creator's description
        creator_id: Creator's player ID
        creator_name: Display name
        submitted_at: Submission timestamp
        category: Gallery category
        content_rating: Content rating
        tags: Search tags
        likes: Like count
        downloads: Download count
        views: View count
        featured: Whether entry is featured
        featured_at: When it was featured
        comments: List of comments
    """
    art: ASCIIArt
    title: str
    creator_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    creator_name: str = "Anonymous"
    submitted_at: datetime = field(default_factory=datetime.now)
    category: GalleryCategory = GalleryCategory.RECENT
    content_rating: ContentRating = ContentRating.EVERYONE
    tags: Set[str] = field(default_factory=set)
    likes: int = 0
    downloads: int = 0
    views: int = 0
    featured: bool = False
    featured_at: Optional[datetime] = None
    comments: List[Dict[str, Any]] = field(default_factory=list)

    def add_like(self) -> int:
        """Add a like and return new count."""
        self.likes += 1
        return self.likes

    def remove_like(self) -> int:
        """Remove a like and return new count."""
        self.likes = max(0, self.likes - 1)
        return self.likes

    def record_download(self) -> int:
        """Record a download and return new count."""
        self.downloads += 1
        return self.downloads

    def record_view(self) -> int:
        """Record a view and return new count."""
        self.views += 1
        return self.views

    def add_comment(
        self,
        player_id: str,
        player_name: str,
        text: str
    ) -> Dict[str, Any]:
        """Add a comment."""
        comment = {
            "id": str(uuid.uuid4()),
            "player_id": player_id,
            "player_name": player_name,
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        self.comments.append(comment)
        return comment

    def remove_comment(self, comment_id: str) -> bool:
        """Remove a comment by ID."""
        for i, comment in enumerate(self.comments):
            if comment["id"] == comment_id:
                self.comments.pop(i)
                return True
        return False

    def set_featured(self, featured: bool = True) -> None:
        """Set featured status."""
        self.featured = featured
        if featured:
            self.featured_at = datetime.now()
            self.category = GalleryCategory.FEATURED
        else:
            self.featured_at = None

    @property
    def popularity_score(self) -> float:
        """Calculate popularity score."""
        return self.likes * 3 + self.downloads * 2 + self.views * 0.1

    def to_dict(self) -> dict:
        """Serialize entry to dictionary."""
        return {
            "id": self.id,
            "art": self.art.to_dict(),
            "title": self.title,
            "description": self.description,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "submitted_at": self.submitted_at.isoformat(),
            "category": self.category.name,
            "content_rating": self.content_rating.name,
            "tags": list(self.tags),
            "likes": self.likes,
            "downloads": self.downloads,
            "views": self.views,
            "featured": self.featured,
            "featured_at": self.featured_at.isoformat() if self.featured_at else None,
            "comments": self.comments
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GalleryEntry":
        """Create entry from dictionary."""
        art_data = data["art"]
        category = ArtCategory[art_data.get("category", "STATIC")]

        if category == ArtCategory.STATIC:
            art = StaticArt.from_dict(art_data)
        else:
            art = DynamicEntity.from_dict(art_data)

        return cls(
            id=data["id"],
            art=art,
            title=data["title"],
            description=data.get("description", ""),
            creator_id=data["creator_id"],
            creator_name=data.get("creator_name", "Anonymous"),
            submitted_at=datetime.fromisoformat(data["submitted_at"]) if "submitted_at" in data else datetime.now(),
            category=GalleryCategory[data.get("category", "RECENT")],
            content_rating=ContentRating[data.get("content_rating", "EVERYONE")],
            tags=set(data.get("tags", [])),
            likes=data.get("likes", 0),
            downloads=data.get("downloads", 0),
            views=data.get("views", 0),
            featured=data.get("featured", False),
            featured_at=datetime.fromisoformat(data["featured_at"]) if data.get("featured_at") else None,
            comments=data.get("comments", [])
        )


class Gallery:
    """
    Community gallery for sharing and discovering art.

    The gallery allows players to share their creations,
    browse others' work, and import art into their games.
    """

    def __init__(self):
        self._entries: Dict[str, GalleryEntry] = {}
        self._by_creator: Dict[str, Set[str]] = {}
        self._by_category: Dict[GalleryCategory, Set[str]] = {}
        self._by_tag: Dict[str, Set[str]] = {}
        self._likes_by_player: Dict[str, Set[str]] = {}  # player_id -> entry_ids

    @property
    def count(self) -> int:
        """Total number of gallery entries."""
        return len(self._entries)

    def submit(
        self,
        art: ASCIIArt,
        title: str,
        creator_id: str,
        creator_name: str = "Anonymous",
        description: str = "",
        tags: Set[str] = None,
        content_rating: ContentRating = ContentRating.EVERYONE
    ) -> GalleryEntry:
        """
        Submit art to the gallery.

        Args:
            art: The art to submit
            title: Display title
            creator_id: Creator's player ID
            creator_name: Display name
            description: Description of the art
            tags: Search tags
            content_rating: Content rating

        Returns:
            Created GalleryEntry
        """
        entry = GalleryEntry(
            art=art,
            title=title,
            creator_id=creator_id,
            creator_name=creator_name,
            description=description,
            tags=tags or set(),
            content_rating=content_rating
        )

        self._entries[entry.id] = entry

        # Index by creator
        if creator_id not in self._by_creator:
            self._by_creator[creator_id] = set()
        self._by_creator[creator_id].add(entry.id)

        # Index by category
        if entry.category not in self._by_category:
            self._by_category[entry.category] = set()
        self._by_category[entry.category].add(entry.id)

        # Index by tags
        for tag in entry.tags:
            tag_lower = tag.lower()
            if tag_lower not in self._by_tag:
                self._by_tag[tag_lower] = set()
            self._by_tag[tag_lower].add(entry.id)

        return entry

    def remove(self, entry_id: str) -> bool:
        """Remove an entry from the gallery."""
        if entry_id not in self._entries:
            return False

        entry = self._entries[entry_id]

        # Remove from indices
        if entry.creator_id in self._by_creator:
            self._by_creator[entry.creator_id].discard(entry_id)

        if entry.category in self._by_category:
            self._by_category[entry.category].discard(entry_id)

        for tag in entry.tags:
            tag_lower = tag.lower()
            if tag_lower in self._by_tag:
                self._by_tag[tag_lower].discard(entry_id)

        del self._entries[entry_id]
        return True

    def get_entry(self, entry_id: str) -> Optional[GalleryEntry]:
        """Get entry by ID."""
        return self._entries.get(entry_id)

    def view_entry(self, entry_id: str) -> Optional[GalleryEntry]:
        """View an entry (records view count)."""
        entry = self._entries.get(entry_id)
        if entry:
            entry.record_view()
        return entry

    def like_entry(self, entry_id: str, player_id: str) -> bool:
        """
        Like an entry.

        Args:
            entry_id: Entry to like
            player_id: Player liking the entry

        Returns:
            True if like was added (not already liked)
        """
        entry = self._entries.get(entry_id)
        if not entry:
            return False

        if player_id not in self._likes_by_player:
            self._likes_by_player[player_id] = set()

        if entry_id in self._likes_by_player[player_id]:
            return False  # Already liked

        self._likes_by_player[player_id].add(entry_id)
        entry.add_like()
        return True

    def unlike_entry(self, entry_id: str, player_id: str) -> bool:
        """Remove a like from an entry."""
        entry = self._entries.get(entry_id)
        if not entry:
            return False

        if player_id not in self._likes_by_player:
            return False

        if entry_id not in self._likes_by_player[player_id]:
            return False  # Wasn't liked

        self._likes_by_player[player_id].discard(entry_id)
        entry.remove_like()
        return True

    def download_entry(self, entry_id: str) -> Optional[ASCIIArt]:
        """
        Download art from an entry.

        Args:
            entry_id: Entry to download from

        Returns:
            Copy of the art or None if not found
        """
        entry = self._entries.get(entry_id)
        if not entry:
            return None

        entry.record_download()
        return entry.art.copy()

    def search(
        self,
        query: str = "",
        tags: Set[str] = None,
        category: GalleryCategory = None,
        creator_id: str = None,
        object_type: ObjectType = None,
        content_rating: ContentRating = None,
        sort_by: str = "recent",
        limit: int = 50
    ) -> List[GalleryEntry]:
        """
        Search gallery entries.

        Args:
            query: Text search query
            tags: Filter by tags
            category: Filter by category
            creator_id: Filter by creator
            object_type: Filter by art object type
            content_rating: Maximum content rating
            sort_by: "recent", "popular", "likes", "downloads"
            limit: Maximum results

        Returns:
            List of matching entries
        """
        candidates = set(self._entries.keys())

        # Filter by category
        if category is not None:
            cat_ids = self._by_category.get(category, set())
            candidates &= cat_ids

        # Filter by creator
        if creator_id is not None:
            creator_ids = self._by_creator.get(creator_id, set())
            candidates &= creator_ids

        # Filter by tags
        if tags:
            for tag in tags:
                tag_ids = self._by_tag.get(tag.lower(), set())
                candidates &= tag_ids

        # Apply remaining filters and text search
        results = []
        query_lower = query.lower()

        for entry_id in candidates:
            entry = self._entries[entry_id]

            # Content rating filter
            if content_rating is not None:
                if entry.content_rating.value > content_rating.value:
                    continue

            # Object type filter
            if object_type is not None:
                if entry.art.tags.object_type != object_type:
                    continue

            # Text search
            if query_lower:
                searchable = f"{entry.title} {entry.description} {entry.creator_name}".lower()
                if query_lower not in searchable:
                    # Check tags
                    if not any(query_lower in tag.lower() for tag in entry.tags):
                        continue

            results.append(entry)

        # Sort results
        if sort_by == "popular":
            results.sort(key=lambda e: e.popularity_score, reverse=True)
        elif sort_by == "likes":
            results.sort(key=lambda e: e.likes, reverse=True)
        elif sort_by == "downloads":
            results.sort(key=lambda e: e.downloads, reverse=True)
        else:  # recent
            results.sort(key=lambda e: e.submitted_at, reverse=True)

        return results[:limit]

    def get_featured(self, limit: int = 10) -> List[GalleryEntry]:
        """Get featured entries."""
        featured = [e for e in self._entries.values() if e.featured]
        featured.sort(key=lambda e: e.featured_at or datetime.min, reverse=True)
        return featured[:limit]

    def get_popular(self, limit: int = 10) -> List[GalleryEntry]:
        """Get most popular entries."""
        return self.search(sort_by="popular", limit=limit)

    def get_recent(self, limit: int = 10) -> List[GalleryEntry]:
        """Get most recent entries."""
        return self.search(sort_by="recent", limit=limit)

    def get_by_creator(self, creator_id: str) -> List[GalleryEntry]:
        """Get all entries by a creator."""
        return self.search(creator_id=creator_id, limit=1000)

    def get_player_likes(self, player_id: str) -> List[GalleryEntry]:
        """Get entries a player has liked."""
        liked_ids = self._likes_by_player.get(player_id, set())
        return [self._entries[eid] for eid in liked_ids if eid in self._entries]

    def feature_entry(self, entry_id: str) -> bool:
        """Feature an entry."""
        entry = self._entries.get(entry_id)
        if not entry:
            return False

        # Remove from old category
        if entry.category in self._by_category:
            self._by_category[entry.category].discard(entry_id)

        entry.set_featured(True)

        # Add to featured category
        if GalleryCategory.FEATURED not in self._by_category:
            self._by_category[GalleryCategory.FEATURED] = set()
        self._by_category[GalleryCategory.FEATURED].add(entry_id)

        return True

    def unfeature_entry(self, entry_id: str) -> bool:
        """Remove featured status from entry."""
        entry = self._entries.get(entry_id)
        if not entry:
            return False

        entry.set_featured(False)
        entry.category = GalleryCategory.COMMUNITY

        # Update category index
        if GalleryCategory.FEATURED in self._by_category:
            self._by_category[GalleryCategory.FEATURED].discard(entry_id)

        if GalleryCategory.COMMUNITY not in self._by_category:
            self._by_category[GalleryCategory.COMMUNITY] = set()
        self._by_category[GalleryCategory.COMMUNITY].add(entry_id)

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get gallery statistics."""
        total_likes = sum(e.likes for e in self._entries.values())
        total_downloads = sum(e.downloads for e in self._entries.values())
        total_views = sum(e.views for e in self._entries.values())

        return {
            "total_entries": self.count,
            "total_likes": total_likes,
            "total_downloads": total_downloads,
            "total_views": total_views,
            "unique_creators": len(self._by_creator),
            "featured_count": len([e for e in self._entries.values() if e.featured]),
            "by_category": {c.name: len(ids) for c, ids in self._by_category.items()},
            "popular_tags": self._get_popular_tags(10)
        }

    def _get_popular_tags(self, count: int) -> List[tuple[str, int]]:
        """Get most popular tags."""
        tag_counts = [(tag, len(ids)) for tag, ids in self._by_tag.items()]
        tag_counts.sort(key=lambda x: x[1], reverse=True)
        return tag_counts[:count]

    def export_entry(self, entry_id: str) -> Optional[str]:
        """
        Export entry as JSON string.

        Args:
            entry_id: Entry to export

        Returns:
            JSON string or None if not found
        """
        entry = self._entries.get(entry_id)
        if not entry:
            return None

        return json.dumps(entry.to_dict(), indent=2)

    def import_entry(
        self,
        json_data: str,
        importer_id: str,
        importer_name: str = "Anonymous"
    ) -> Optional[GalleryEntry]:
        """
        Import entry from JSON string.

        Args:
            json_data: JSON string of entry data
            importer_id: ID of player importing
            importer_name: Name of player importing

        Returns:
            New GalleryEntry or None if import failed
        """
        try:
            data = json.loads(json_data)
            original_entry = GalleryEntry.from_dict(data)

            # Create copy with new ID and importer as creator
            new_art = original_entry.art.copy()
            new_art.original_creator = original_entry.creator_id
            new_art.player_id = importer_id

            new_entry = self.submit(
                art=new_art,
                title=f"{original_entry.title} (imported)",
                creator_id=importer_id,
                creator_name=importer_name,
                description=f"Imported from {original_entry.creator_name}. {original_entry.description}",
                tags=original_entry.tags,
                content_rating=original_entry.content_rating
            )

            return new_entry

        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def to_dict(self) -> dict:
        """Serialize gallery to dictionary."""
        return {
            "entries": [e.to_dict() for e in self._entries.values()],
            "likes_by_player": {k: list(v) for k, v in self._likes_by_player.items()}
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Gallery":
        """Create gallery from dictionary."""
        gallery = cls()

        for entry_data in data.get("entries", []):
            entry = GalleryEntry.from_dict(entry_data)
            gallery._entries[entry.id] = entry

            # Rebuild indices
            if entry.creator_id not in gallery._by_creator:
                gallery._by_creator[entry.creator_id] = set()
            gallery._by_creator[entry.creator_id].add(entry.id)

            if entry.category not in gallery._by_category:
                gallery._by_category[entry.category] = set()
            gallery._by_category[entry.category].add(entry.id)

            for tag in entry.tags:
                tag_lower = tag.lower()
                if tag_lower not in gallery._by_tag:
                    gallery._by_tag[tag_lower] = set()
                gallery._by_tag[tag_lower].add(entry.id)

        for player_id, entry_ids in data.get("likes_by_player", {}).items():
            gallery._likes_by_player[player_id] = set(entry_ids)

        return gallery

    def __len__(self) -> int:
        return self.count

    def __contains__(self, entry_id: str) -> bool:
        return entry_id in self._entries

    def __iter__(self):
        return iter(self._entries.values())
