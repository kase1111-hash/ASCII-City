"""
Game Statistics - Track player performance and game metrics.

Provides:
- Per-game statistics tracking
- Aggregate statistics across games
- Achievement tracking
- Performance analysis
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class GameStatistics:
    """Statistics for a single game session."""

    # Identification
    game_id: str = ""
    seed: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    # Outcome
    solved: bool = False
    correct_accusation: bool = False
    wrong_accusations: int = 0
    ending_id: str = ""

    # Exploration
    locations_visited: int = 0
    locations_total: int = 0
    hotspots_examined: int = 0
    hotspots_total: int = 0

    # Evidence
    evidence_collected: int = 0
    evidence_total: int = 0
    evidence_presented: int = 0

    # Characters
    characters_talked: int = 0
    characters_total: int = 0
    trust_gained: int = 0
    trust_lost: int = 0

    # Narrative
    revelations_discovered: int = 0
    revelations_total: int = 0
    twists_triggered: int = 0
    moral_shade: str = ""

    # Gameplay
    commands_entered: int = 0
    time_played_seconds: int = 0

    def completion_percentage(self) -> float:
        """Calculate overall completion percentage."""
        metrics = [
            (self.locations_visited, self.locations_total),
            (self.hotspots_examined, self.hotspots_total),
            (self.evidence_collected, self.evidence_total),
            (self.characters_talked, self.characters_total),
            (self.revelations_discovered, self.revelations_total)
        ]

        total_found = sum(found for found, _ in metrics)
        total_possible = sum(total for _, total in metrics)

        if total_possible == 0:
            return 0.0
        return total_found / total_possible

    def efficiency_score(self) -> float:
        """Calculate efficiency (completion vs commands)."""
        if self.commands_entered == 0:
            return 0.0
        return self.completion_percentage() / (self.commands_entered / 100)

    def to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "seed": self.seed,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "solved": self.solved,
            "correct_accusation": self.correct_accusation,
            "wrong_accusations": self.wrong_accusations,
            "ending_id": self.ending_id,
            "locations_visited": self.locations_visited,
            "locations_total": self.locations_total,
            "hotspots_examined": self.hotspots_examined,
            "hotspots_total": self.hotspots_total,
            "evidence_collected": self.evidence_collected,
            "evidence_total": self.evidence_total,
            "evidence_presented": self.evidence_presented,
            "characters_talked": self.characters_talked,
            "characters_total": self.characters_total,
            "trust_gained": self.trust_gained,
            "trust_lost": self.trust_lost,
            "revelations_discovered": self.revelations_discovered,
            "revelations_total": self.revelations_total,
            "twists_triggered": self.twists_triggered,
            "moral_shade": self.moral_shade,
            "commands_entered": self.commands_entered,
            "time_played_seconds": self.time_played_seconds
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GameStatistics":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AggregateStatistics:
    """Aggregate statistics across multiple games."""

    games_played: int = 0
    games_solved: int = 0
    total_time_seconds: int = 0
    total_commands: int = 0

    # Best performance
    fastest_solve_seconds: int = 0
    most_efficient_game_id: str = ""
    highest_completion: float = 0.0

    # Averages
    avg_solve_time_seconds: float = 0.0
    avg_commands_per_game: float = 0.0
    avg_completion: float = 0.0

    # Totals
    total_evidence_collected: int = 0
    total_characters_talked: int = 0
    total_locations_visited: int = 0

    # Ending distribution
    endings_achieved: dict[str, int] = field(default_factory=dict)

    # Shade distribution
    shades_achieved: dict[str, int] = field(default_factory=dict)

    def solve_rate(self) -> float:
        """Get percentage of games solved."""
        if self.games_played == 0:
            return 0.0
        return self.games_solved / self.games_played

    def update_from_game(self, stats: GameStatistics) -> None:
        """Update aggregate stats from a completed game."""
        self.games_played += 1
        self.total_time_seconds += stats.time_played_seconds
        self.total_commands += stats.commands_entered
        self.total_evidence_collected += stats.evidence_collected
        self.total_characters_talked += stats.characters_talked
        self.total_locations_visited += stats.locations_visited

        if stats.solved:
            self.games_solved += 1

            # Check for fastest solve
            if self.fastest_solve_seconds == 0 or stats.time_played_seconds < self.fastest_solve_seconds:
                self.fastest_solve_seconds = stats.time_played_seconds

        # Check for highest completion
        completion = stats.completion_percentage()
        if completion > self.highest_completion:
            self.highest_completion = completion

        # Check for most efficient
        if stats.efficiency_score() > 0:
            if not self.most_efficient_game_id:
                self.most_efficient_game_id = stats.game_id

        # Track ending
        if stats.ending_id:
            self.endings_achieved[stats.ending_id] = self.endings_achieved.get(stats.ending_id, 0) + 1

        # Track shade
        if stats.moral_shade:
            self.shades_achieved[stats.moral_shade] = self.shades_achieved.get(stats.moral_shade, 0) + 1

        # Recalculate averages
        self._recalculate_averages()

    def _recalculate_averages(self) -> None:
        """Recalculate average statistics."""
        if self.games_played > 0:
            self.avg_commands_per_game = self.total_commands / self.games_played
            self.avg_completion = self.highest_completion  # Simplified

        if self.games_solved > 0:
            self.avg_solve_time_seconds = self.total_time_seconds / self.games_solved

    def to_dict(self) -> dict:
        return {
            "games_played": self.games_played,
            "games_solved": self.games_solved,
            "total_time_seconds": self.total_time_seconds,
            "total_commands": self.total_commands,
            "fastest_solve_seconds": self.fastest_solve_seconds,
            "most_efficient_game_id": self.most_efficient_game_id,
            "highest_completion": self.highest_completion,
            "avg_solve_time_seconds": self.avg_solve_time_seconds,
            "avg_commands_per_game": self.avg_commands_per_game,
            "avg_completion": self.avg_completion,
            "total_evidence_collected": self.total_evidence_collected,
            "total_characters_talked": self.total_characters_talked,
            "total_locations_visited": self.total_locations_visited,
            "endings_achieved": self.endings_achieved,
            "shades_achieved": self.shades_achieved
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AggregateStatistics":
        stats = cls()
        for key, value in data.items():
            if hasattr(stats, key):
                setattr(stats, key, value)
        return stats


@dataclass
class Achievement:
    """An achievement that can be unlocked."""
    id: str
    name: str
    description: str
    hidden: bool = False
    unlocked: bool = False
    unlock_time: Optional[str] = None

    def unlock(self) -> None:
        """Unlock this achievement."""
        if not self.unlocked:
            self.unlocked = True
            self.unlock_time = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "hidden": self.hidden,
            "unlocked": self.unlocked,
            "unlock_time": self.unlock_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Achievement":
        return cls(**data)


# Predefined achievements
ACHIEVEMENTS: list[Achievement] = [
    Achievement(
        id="first_solve",
        name="Case Closed",
        description="Solve your first mystery"
    ),
    Achievement(
        id="perfect_solve",
        name="Perfect Detective",
        description="Solve a case without any wrong accusations"
    ),
    Achievement(
        id="speed_demon",
        name="Speed Demon",
        description="Solve a case in under 10 minutes"
    ),
    Achievement(
        id="thorough",
        name="Thorough Investigator",
        description="Examine every hotspot in a game"
    ),
    Achievement(
        id="social_butterfly",
        name="Social Butterfly",
        description="Talk to every character in a game"
    ),
    Achievement(
        id="evidence_hoarder",
        name="Evidence Hoarder",
        description="Collect all evidence in a game"
    ),
    Achievement(
        id="all_endings",
        name="Completionist",
        description="Experience all endings",
        hidden=True
    ),
    Achievement(
        id="ten_games",
        name="Veteran",
        description="Play 10 games"
    ),
    Achievement(
        id="master_detective",
        name="Master Detective",
        description="Solve 5 cases correctly",
        hidden=True
    )
]


class AchievementManager:
    """Manages achievements and unlocking."""

    def __init__(self, achievements: list[Achievement] = None):
        self.achievements = achievements if achievements is not None else [
            Achievement(**a.to_dict()) for a in ACHIEVEMENTS
        ]

    def get_achievement(self, achievement_id: str) -> Optional[Achievement]:
        """Get an achievement by ID."""
        for achievement in self.achievements:
            if achievement.id == achievement_id:
                return achievement
        return None

    def unlock(self, achievement_id: str) -> bool:
        """Unlock an achievement. Returns True if newly unlocked."""
        achievement = self.get_achievement(achievement_id)
        if achievement and not achievement.unlocked:
            achievement.unlock()
            return True
        return False

    def check_achievements(
        self,
        game_stats: GameStatistics,
        aggregate_stats: AggregateStatistics
    ) -> list[Achievement]:
        """
        Check for achievements that should be unlocked.

        Returns list of newly unlocked achievements.
        """
        # Define achievement conditions as (achievement_id, condition_checker)
        achievement_checks = [
            ("first_solve", lambda g, a: g.solved and a.games_solved == 1),
            ("perfect_solve", lambda g, a: g.solved and g.wrong_accusations == 0),
            ("speed_demon", lambda g, a: g.solved and g.time_played_seconds < 600),
            ("thorough", lambda g, a: g.hotspots_total > 0 and g.hotspots_examined >= g.hotspots_total),
            ("social_butterfly", lambda g, a: g.characters_total > 0 and g.characters_talked >= g.characters_total),
            ("evidence_hoarder", lambda g, a: g.evidence_total > 0 and g.evidence_collected >= g.evidence_total),
            ("ten_games", lambda g, a: a.games_played >= 10),
            ("master_detective", lambda g, a: a.games_solved >= 5),
        ]

        newly_unlocked = []
        for achievement_id, check_condition in achievement_checks:
            if check_condition(game_stats, aggregate_stats) and self.unlock(achievement_id):
                newly_unlocked.append(self.get_achievement(achievement_id))

        return newly_unlocked

    def get_unlocked(self) -> list[Achievement]:
        """Get all unlocked achievements."""
        return [a for a in self.achievements if a.unlocked]

    def get_locked(self, include_hidden: bool = False) -> list[Achievement]:
        """Get all locked achievements."""
        locked = [a for a in self.achievements if not a.unlocked]
        if not include_hidden:
            locked = [a for a in locked if not a.hidden]
        return locked

    def get_progress(self) -> float:
        """Get achievement completion percentage."""
        if not self.achievements:
            return 0.0
        return len(self.get_unlocked()) / len(self.achievements)

    def to_dict(self) -> dict:
        return {
            "achievements": [a.to_dict() for a in self.achievements]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AchievementManager":
        achievements = [Achievement.from_dict(a) for a in data.get("achievements", [])]
        return cls(achievements=achievements)
