"""
Seed System - Reproducible game generation and sharing.

Provides:
- Seed encoding/decoding
- Shareable seed strings
- Seed-based challenge creation
- Daily seed generation
"""

from dataclasses import dataclass, field
from typing import Optional
import hashlib
import random
import base64
from datetime import datetime, date


@dataclass
class GameSeed:
    """A seed that defines a unique game configuration."""

    # Core seed value
    value: int

    # Optional metadata
    conflict_type: Optional[str] = None
    difficulty: str = "normal"
    character_count: int = 5
    twist_enabled: bool = True

    # Creation info
    created_at: Optional[str] = None
    author: str = ""
    name: str = ""
    description: str = ""

    @classmethod
    def generate(cls, source: str = None) -> "GameSeed":
        """Generate a new random seed."""
        if source:
            # Deterministic from source string
            hash_bytes = hashlib.sha256(source.encode()).digest()
            value = int.from_bytes(hash_bytes[:4], 'big')
        else:
            value = random.randint(0, 2**32 - 1)

        return cls(
            value=value,
            created_at=datetime.now().isoformat()
        )

    @classmethod
    def from_daily(cls, offset: int = 0) -> "GameSeed":
        """Generate seed for today's date (or offset days)."""
        today = date.today()
        if offset:
            from datetime import timedelta
            today = today + timedelta(days=offset)

        date_str = today.isoformat()
        return cls.generate(source=f"daily_{date_str}")

    def to_share_code(self) -> str:
        """
        Generate a shareable code string.

        Format: BASE64(seed_value:difficulty:characters:twist)
        """
        data = f"{self.value}:{self.difficulty}:{self.character_count}:{1 if self.twist_enabled else 0}"
        if self.conflict_type:
            data += f":{self.conflict_type}"

        encoded = base64.urlsafe_b64encode(data.encode()).decode()
        # Add prefix for identification
        return f"SH{encoded}"

    @classmethod
    def from_share_code(cls, code: str) -> Optional["GameSeed"]:
        """Parse a seed from a share code."""
        if not code.startswith("SH"):
            return None

        try:
            encoded = code[2:]  # Remove prefix
            data = base64.urlsafe_b64decode(encoded.encode()).decode()
            parts = data.split(":")

            seed = cls(
                value=int(parts[0]),
                difficulty=parts[1] if len(parts) > 1 else "normal",
                character_count=int(parts[2]) if len(parts) > 2 else 5,
                twist_enabled=parts[3] == "1" if len(parts) > 3 else True
            )

            if len(parts) > 4:
                seed.conflict_type = parts[4]

            return seed

        except (ValueError, IndexError):
            return None

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "conflict_type": self.conflict_type,
            "difficulty": self.difficulty,
            "character_count": self.character_count,
            "twist_enabled": self.twist_enabled,
            "created_at": self.created_at,
            "author": self.author,
            "name": self.name,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameSeed":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DailyChallenge:
    """A daily challenge with a specific seed."""

    date_str: str
    seed: GameSeed
    title: str = ""
    special_rules: list[str] = field(default_factory=list)
    leaderboard: list[dict] = field(default_factory=list)

    @classmethod
    def for_today(cls) -> "DailyChallenge":
        """Create today's challenge."""
        today = date.today()
        seed = GameSeed.from_daily()

        # Generate title based on day
        day_names = ["Mystery Monday", "Thrilling Tuesday", "Whodunit Wednesday",
                     "Thriller Thursday", "Finale Friday", "Suspense Saturday", "Sinister Sunday"]
        title = day_names[today.weekday()]

        return cls(
            date_str=today.isoformat(),
            seed=seed,
            title=title
        )

    def add_score(self, player: str, time_seconds: int, solved: bool) -> None:
        """Add a score to the leaderboard."""
        self.leaderboard.append({
            "player": player,
            "time_seconds": time_seconds,
            "solved": solved,
            "timestamp": datetime.now().isoformat()
        })
        # Sort by solved first, then time
        self.leaderboard.sort(
            key=lambda x: (not x["solved"], x["time_seconds"])
        )

    def get_rank(self, player: str) -> Optional[int]:
        """Get a player's rank on the leaderboard."""
        for i, entry in enumerate(self.leaderboard):
            if entry["player"] == player:
                return i + 1
        return None

    def to_dict(self) -> dict:
        return {
            "date_str": self.date_str,
            "seed": self.seed.to_dict(),
            "title": self.title,
            "special_rules": self.special_rules,
            "leaderboard": self.leaderboard
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DailyChallenge":
        return cls(
            date_str=data["date_str"],
            seed=GameSeed.from_dict(data["seed"]),
            title=data.get("title", ""),
            special_rules=data.get("special_rules", []),
            leaderboard=data.get("leaderboard", [])
        )


@dataclass
class SeedCollection:
    """A collection of saved seeds."""

    seeds: list[GameSeed] = field(default_factory=list)
    favorites: set[int] = field(default_factory=set)

    def add(self, seed: GameSeed) -> None:
        """Add a seed to the collection."""
        self.seeds.append(seed)

    def remove(self, seed_value: int) -> bool:
        """Remove a seed by value."""
        for i, seed in enumerate(self.seeds):
            if seed.value == seed_value:
                self.seeds.pop(i)
                self.favorites.discard(seed_value)
                return True
        return False

    def get(self, seed_value: int) -> Optional[GameSeed]:
        """Get a seed by value."""
        for seed in self.seeds:
            if seed.value == seed_value:
                return seed
        return None

    def toggle_favorite(self, seed_value: int) -> bool:
        """Toggle favorite status. Returns new status."""
        if seed_value in self.favorites:
            self.favorites.remove(seed_value)
            return False
        else:
            self.favorites.add(seed_value)
            return True

    def get_favorites(self) -> list[GameSeed]:
        """Get all favorited seeds."""
        return [s for s in self.seeds if s.value in self.favorites]

    def search(self, query: str) -> list[GameSeed]:
        """Search seeds by name or description."""
        query = query.lower()
        return [
            s for s in self.seeds
            if query in s.name.lower() or query in s.description.lower()
        ]

    def to_dict(self) -> dict:
        return {
            "seeds": [s.to_dict() for s in self.seeds],
            "favorites": list(self.favorites)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SeedCollection":
        collection = cls()
        collection.seeds = [GameSeed.from_dict(s) for s in data.get("seeds", [])]
        collection.favorites = set(data.get("favorites", []))
        return collection


class SeedGenerator:
    """
    Generates seeds with specific characteristics.

    Can create themed seeds, difficulty-adjusted seeds,
    and seeds with specific conflict types.
    """

    def __init__(self, base_seed: int = None):
        if base_seed is not None:
            random.seed(base_seed)

    def generate_themed(self, theme: str) -> GameSeed:
        """Generate a seed themed around a concept."""
        # Use theme as part of seed source
        seed = GameSeed.generate(source=f"theme_{theme}_{random.random()}")
        seed.name = f"{theme.title()} Mystery"
        seed.description = f"A mystery themed around {theme}"
        return seed

    def generate_difficulty(self, difficulty: str) -> GameSeed:
        """Generate a seed with specific difficulty."""
        seed = GameSeed.generate()
        seed.difficulty = difficulty

        if difficulty == "easy":
            seed.character_count = 3
            seed.twist_enabled = False
        elif difficulty == "hard":
            seed.character_count = 7
            seed.twist_enabled = True
        elif difficulty == "nightmare":
            seed.character_count = 10
            seed.twist_enabled = True

        return seed

    def generate_with_conflict(self, conflict_type: str) -> GameSeed:
        """Generate a seed with a specific conflict type."""
        seed = GameSeed.generate()
        seed.conflict_type = conflict_type
        return seed

    def generate_series(self, count: int, prefix: str = "Episode") -> list[GameSeed]:
        """Generate a series of related seeds."""
        series = []
        base = random.randint(0, 2**24)

        for i in range(count):
            seed = GameSeed(
                value=base + i,
                name=f"{prefix} {i + 1}",
                description=f"Part {i + 1} of {count} in the {prefix} series"
            )
            series.append(seed)

        return series
