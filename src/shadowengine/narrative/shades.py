"""
Moral Shades System - Player morality tracking and narrative consequences.

Provides:
- Five moral shades for player character
- Decision tracking and shade calculation
- Shade-based narrative text generation
- Ending determination based on shade
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum, auto


class MoralShade(Enum):
    """The five moral shades a player can embody."""
    PRAGMATIC = "pragmatic"       # Gets results, means justify ends
    CORRUPT = "corrupt"           # Self-serving, exploits situations
    COMPASSIONATE = "compassionate"  # Prioritizes people over justice
    RUTHLESS = "ruthless"         # Justice at any cost
    IDEALISTIC = "idealistic"     # Follows principles regardless of outcome


@dataclass
class MoralDecision:
    """A decision that affects moral shade."""
    id: str
    description: str
    shade_effects: dict[MoralShade, int] = field(default_factory=dict)
    timestamp: float = 0.0
    context: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "shade_effects": {k.value: v for k, v in self.shade_effects.items()},
            "timestamp": self.timestamp,
            "context": self.context
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MoralDecision":
        return cls(
            id=data["id"],
            description=data["description"],
            shade_effects={MoralShade(k): v for k, v in data.get("shade_effects", {}).items()},
            timestamp=data.get("timestamp", 0.0),
            context=data.get("context", "")
        )


@dataclass
class ShadeProfile:
    """Tracks the player's moral shade scores."""

    scores: dict[MoralShade, int] = field(default_factory=lambda: {
        MoralShade.PRAGMATIC: 0,
        MoralShade.CORRUPT: 0,
        MoralShade.COMPASSIONATE: 0,
        MoralShade.RUTHLESS: 0,
        MoralShade.IDEALISTIC: 0
    })
    decisions: list[MoralDecision] = field(default_factory=list)

    def apply_decision(self, decision: MoralDecision) -> None:
        """Apply a decision's effects to the profile."""
        for shade, effect in decision.shade_effects.items():
            self.scores[shade] = self.scores.get(shade, 0) + effect
        self.decisions.append(decision)

    def get_dominant_shade(self) -> MoralShade:
        """Get the current dominant moral shade."""
        if not self.scores:
            return MoralShade.PRAGMATIC

        max_score = max(self.scores.values())
        if max_score <= 0:
            return MoralShade.PRAGMATIC

        # Find shade with highest score
        for shade, score in self.scores.items():
            if score == max_score:
                return shade

        return MoralShade.PRAGMATIC

    def get_shade_strength(self, shade: MoralShade) -> float:
        """Get strength of a shade (0.0 to 1.0)."""
        total = sum(max(0, s) for s in self.scores.values())
        if total == 0:
            return 0.0
        return max(0, self.scores.get(shade, 0)) / total

    def get_dominant_strength(self) -> float:
        """Get how strongly the dominant shade dominates."""
        return self.get_shade_strength(self.get_dominant_shade())

    def is_conflicted(self) -> bool:
        """Check if player has no clear dominant shade."""
        return self.get_dominant_strength() < 0.3

    def to_dict(self) -> dict:
        return {
            "scores": {k.value: v for k, v in self.scores.items()},
            "decisions": [d.to_dict() for d in self.decisions]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ShadeProfile":
        profile = cls()
        profile.scores = {MoralShade(k): v for k, v in data.get("scores", {}).items()}
        profile.decisions = [MoralDecision.from_dict(d) for d in data.get("decisions", [])]
        return profile


# Predefined decision templates for common situations
DECISION_TEMPLATES: dict[str, dict[MoralShade, int]] = {
    # Evidence handling
    "planted_evidence": {MoralShade.CORRUPT: 3, MoralShade.RUTHLESS: 1},
    "hid_evidence": {MoralShade.COMPASSIONATE: 2, MoralShade.CORRUPT: 1},
    "reported_all_evidence": {MoralShade.IDEALISTIC: 2, MoralShade.PRAGMATIC: 1},

    # Interrogation approaches
    "used_threats": {MoralShade.RUTHLESS: 2},
    "showed_empathy": {MoralShade.COMPASSIONATE: 2},
    "made_deal": {MoralShade.PRAGMATIC: 2, MoralShade.CORRUPT: 1},
    "stuck_to_rules": {MoralShade.IDEALISTIC: 2},

    # Accusation results
    "accused_innocent": {MoralShade.RUTHLESS: 2, MoralShade.IDEALISTIC: -2},
    "let_guilty_go": {MoralShade.COMPASSIONATE: 2, MoralShade.CORRUPT: 1},
    "found_truth": {MoralShade.IDEALISTIC: 1, MoralShade.PRAGMATIC: 1},

    # Character interactions
    "betrayed_trust": {MoralShade.CORRUPT: 2, MoralShade.PRAGMATIC: 1},
    "kept_secret": {MoralShade.COMPASSIONATE: 1},
    "broke_promise": {MoralShade.RUTHLESS: 1, MoralShade.PRAGMATIC: 1},
    "honored_promise": {MoralShade.IDEALISTIC: 2},

    # Resource usage
    "took_bribe": {MoralShade.CORRUPT: 3},
    "refused_bribe": {MoralShade.IDEALISTIC: 2},
    "used_bribe_as_leverage": {MoralShade.PRAGMATIC: 2},
}


@dataclass
class NarrationStyle:
    """Defines narrative text style for a shade."""
    tone: str                    # Overall writing tone
    vocabulary: list[str]        # Characteristic words
    sentence_style: str          # Short/long, simple/complex
    perspective_phrases: list[str]  # Common internal monologue phrases


# Shade-specific narration styles
SHADE_STYLES: dict[MoralShade, NarrationStyle] = {
    MoralShade.PRAGMATIC: NarrationStyle(
        tone="practical",
        vocabulary=["efficient", "useful", "works", "results", "necessary"],
        sentence_style="direct",
        perspective_phrases=[
            "Whatever works.",
            "The end justifies the means.",
            "Time to get practical.",
            "Results matter."
        ]
    ),
    MoralShade.CORRUPT: NarrationStyle(
        tone="cynical",
        vocabulary=["opportunity", "leverage", "angle", "advantage", "payoff"],
        sentence_style="calculating",
        perspective_phrases=[
            "Everyone has their price.",
            "Nothing personal.",
            "An opportunity presents itself.",
            "What's in it for me?"
        ]
    ),
    MoralShade.COMPASSIONATE: NarrationStyle(
        tone="empathetic",
        vocabulary=["understand", "feel", "hurt", "help", "forgive"],
        sentence_style="reflective",
        perspective_phrases=[
            "There has to be another way.",
            "I can't let them suffer.",
            "Everyone deserves a chance.",
            "Justice isn't everything."
        ]
    ),
    MoralShade.RUTHLESS: NarrationStyle(
        tone="cold",
        vocabulary=["justice", "punishment", "deserve", "guilty", "pay"],
        sentence_style="clipped",
        perspective_phrases=[
            "No mercy for the guilty.",
            "They'll pay for this.",
            "Justice demands sacrifice.",
            "The truth, no matter the cost."
        ]
    ),
    MoralShade.IDEALISTIC: NarrationStyle(
        tone="principled",
        vocabulary=["right", "wrong", "truth", "honor", "principle"],
        sentence_style="measured",
        perspective_phrases=[
            "There's a right way to do this.",
            "I won't compromise my principles.",
            "The truth will out.",
            "Honor before expedience."
        ]
    )
}


class ShadeNarrator:
    """
    Generates shade-appropriate narrative text.

    Adjusts narration style based on player's moral shade.
    """

    def __init__(self, profile: ShadeProfile = None):
        self.profile = profile or ShadeProfile()

    def get_style(self) -> NarrationStyle:
        """Get narration style for current shade."""
        shade = self.profile.get_dominant_shade()
        return SHADE_STYLES.get(shade, SHADE_STYLES[MoralShade.PRAGMATIC])

    def get_internal_thought(self) -> str:
        """Get a characteristic internal thought."""
        import random
        style = self.get_style()
        return random.choice(style.perspective_phrases)

    def narrate_discovery(self, item: str) -> str:
        """Generate shade-appropriate discovery narration."""
        shade = self.profile.get_dominant_shade()

        templates = {
            MoralShade.PRAGMATIC: f"Found {item}. Could be useful.",
            MoralShade.CORRUPT: f"Interesting. {item} might have value.",
            MoralShade.COMPASSIONATE: f"There's {item} here. Someone left it behind.",
            MoralShade.RUTHLESS: f"{item}. Another piece of evidence.",
            MoralShade.IDEALISTIC: f"I've found {item}. The truth reveals itself."
        }

        return templates.get(shade, f"Found {item}.")

    def narrate_confrontation(self, character: str) -> str:
        """Generate shade-appropriate confrontation narration."""
        shade = self.profile.get_dominant_shade()

        templates = {
            MoralShade.PRAGMATIC: f"Time to have a talk with {character}.",
            MoralShade.CORRUPT: f"{character} has information I need.",
            MoralShade.COMPASSIONATE: f"I need to hear {character}'s side.",
            MoralShade.RUTHLESS: f"{character} will answer for this.",
            MoralShade.IDEALISTIC: f"I must speak with {character} honestly."
        }

        return templates.get(shade, f"Approaching {character}.")

    def narrate_accusation(self, character: str, correct: bool) -> str:
        """Generate shade-appropriate accusation result narration."""
        shade = self.profile.get_dominant_shade()

        if correct:
            templates = {
                MoralShade.PRAGMATIC: f"Case closed. {character} was the one.",
                MoralShade.CORRUPT: f"{character} should have covered their tracks better.",
                MoralShade.COMPASSIONATE: f"It was {character}. I wish it weren't true.",
                MoralShade.RUTHLESS: f"Justice is served. {character} will pay.",
                MoralShade.IDEALISTIC: f"The truth prevails. {character} is guilty."
            }
        else:
            templates = {
                MoralShade.PRAGMATIC: f"Wrong call on {character}. Back to work.",
                MoralShade.CORRUPT: f"{character} wasn't the easy mark I thought.",
                MoralShade.COMPASSIONATE: f"I accused {character} wrongly. The guilt weighs heavy.",
                MoralShade.RUTHLESS: f"The guilty one still walks free.",
                MoralShade.IDEALISTIC: f"I failed {character}. I must find the real truth."
            }

        return templates.get(shade, "The accusation is made.")

    def narrate_scene_entry(self, location: str) -> str:
        """Generate shade-appropriate scene description."""
        shade = self.profile.get_dominant_shade()

        templates = {
            MoralShade.PRAGMATIC: f"The {location}. Time to look around.",
            MoralShade.CORRUPT: f"The {location}. Lots of dark corners here.",
            MoralShade.COMPASSIONATE: f"The {location}. Echoes of what happened here.",
            MoralShade.RUTHLESS: f"The {location}. Every inch holds potential evidence.",
            MoralShade.IDEALISTIC: f"The {location}. The truth is waiting to be found."
        }

        return templates.get(shade, f"Entering {location}.")


@dataclass
class Ending:
    """Defines a possible game ending."""
    id: str
    name: str
    shade_requirement: Optional[MoralShade] = None
    shade_strength_min: float = 0.0
    solved_requirement: bool = True
    description: str = ""
    epilogue: str = ""

    def check_requirements(
        self,
        profile: ShadeProfile,
        mystery_solved: bool
    ) -> bool:
        """Check if this ending's requirements are met."""
        if self.solved_requirement and not mystery_solved:
            return False

        if self.shade_requirement:
            if profile.get_dominant_shade() != self.shade_requirement:
                return False
            if profile.get_dominant_strength() < self.shade_strength_min:
                return False

        return True


# Predefined endings
ENDINGS: list[Ending] = [
    Ending(
        id="pragmatic_solved",
        name="The Professional",
        shade_requirement=MoralShade.PRAGMATIC,
        shade_strength_min=0.3,
        solved_requirement=True,
        description="You solved the case efficiently, using whatever methods worked.",
        epilogue="Another case closed. The methods don't matter - only the results."
    ),
    Ending(
        id="corrupt_solved",
        name="The Crooked Path",
        shade_requirement=MoralShade.CORRUPT,
        shade_strength_min=0.3,
        solved_requirement=True,
        description="You found the truth, but profited along the way.",
        epilogue="Justice was served, but so were your own interests. A profitable arrangement."
    ),
    Ending(
        id="compassionate_solved",
        name="The Human Touch",
        shade_requirement=MoralShade.COMPASSIONATE,
        shade_strength_min=0.3,
        solved_requirement=True,
        description="You solved the case while remembering the people involved.",
        epilogue="The case is closed, but the healing has just begun."
    ),
    Ending(
        id="ruthless_solved",
        name="Justice Absolute",
        shade_requirement=MoralShade.RUTHLESS,
        shade_strength_min=0.3,
        solved_requirement=True,
        description="You found the guilty party and ensured they faced consequences.",
        epilogue="Justice is blind, and so were you to everything but the truth."
    ),
    Ending(
        id="idealistic_solved",
        name="The Righteous Path",
        shade_requirement=MoralShade.IDEALISTIC,
        shade_strength_min=0.3,
        solved_requirement=True,
        description="You solved the case without compromising your principles.",
        epilogue="The truth was found the right way. Your conscience is clear."
    ),
    Ending(
        id="neutral_solved",
        name="Case Closed",
        shade_requirement=None,
        solved_requirement=True,
        description="You solved the case.",
        epilogue="The mystery is solved. Time moves on."
    ),
    Ending(
        id="unsolved",
        name="Cold Case",
        shade_requirement=None,
        solved_requirement=False,
        description="The case remains unsolved.",
        epilogue="Some mysteries aren't meant to be solved. Or perhaps you just weren't good enough."
    )
]


class EndingDeterminator:
    """Determines the appropriate ending based on game state."""

    def __init__(self, endings: list[Ending] = None):
        self.endings = endings if endings is not None else ENDINGS

    def determine_ending(
        self,
        profile: ShadeProfile,
        mystery_solved: bool
    ) -> Ending:
        """Determine the most appropriate ending."""
        # First check shade-specific endings
        for ending in self.endings:
            if ending.shade_requirement and ending.check_requirements(profile, mystery_solved):
                return ending

        # Fall back to generic endings
        for ending in self.endings:
            if not ending.shade_requirement and ending.check_requirements(profile, mystery_solved):
                return ending

        # Ultimate fallback
        return Ending(
            id="default",
            name="The End",
            description="The story concludes.",
            epilogue="And so it ends."
        )

    def get_possible_endings(
        self,
        profile: ShadeProfile,
        mystery_solved: bool
    ) -> list[Ending]:
        """Get all endings that could currently be achieved."""
        return [
            e for e in self.endings
            if e.check_requirements(profile, mystery_solved)
        ]
