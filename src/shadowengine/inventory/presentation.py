"""
Evidence Presentation - Show evidence to NPCs for reactions.

Provides:
- Presentation mechanics
- NPC reaction determination
- Trust/pressure effects from presentation
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum, auto

from .item import Evidence


class ReactionType(Enum):
    """Types of reactions to presented evidence."""
    INDIFFERENT = auto()     # No significant reaction
    NERVOUS = auto()         # Shows signs of discomfort
    DEFENSIVE = auto()       # Becomes defensive
    FRIGHTENED = auto()      # Shows fear
    ANGRY = auto()           # Becomes angry
    CONFUSED = auto()        # Doesn't understand relevance
    RELIEVED = auto()        # Evidence helps them
    COOPERATIVE = auto()     # Willing to share more
    CRACKED = auto()         # Breaks and confesses


@dataclass
class PresentationResult:
    """Result of presenting evidence to an NPC."""

    evidence_id: str
    character_id: str
    reaction: ReactionType

    # Effects on character
    trust_change: int = 0
    pressure_applied: int = 0
    mood_change: Optional[str] = None

    # Information revealed
    reveals_fact: Optional[str] = None
    unlocks_topic: Optional[str] = None
    triggers_dialogue: Optional[str] = None

    # Narrative description
    reaction_text: str = ""


@dataclass
class EvidencePresentation:
    """
    Manages the presentation of evidence to NPCs.

    Determines appropriate reactions based on:
    - Character's relationship to the evidence
    - Character's archetype and psychology
    - Current game state
    """

    # Custom reaction handlers
    _reaction_handlers: dict[str, Callable] = field(
        default_factory=dict, repr=False
    )

    def present(
        self,
        evidence: Evidence,
        character_id: str,
        character_archetype: str,
        character_is_implicated: bool = False,
        character_is_exonerated: bool = False,
        character_trust: int = 0,
        character_pressure: int = 0,
        character_knows_fact: bool = False
    ) -> PresentationResult:
        """
        Present evidence to a character.

        Returns the result including reaction and effects.
        """
        # Check for custom handler
        handler_key = f"{evidence.id}:{character_id}"
        if handler_key in self._reaction_handlers:
            return self._reaction_handlers[handler_key](
                evidence, character_id
            )

        # Determine reaction
        reaction = self._determine_reaction(
            evidence=evidence,
            character_id=character_id,
            archetype=character_archetype,
            is_implicated=character_is_implicated,
            is_exonerated=character_is_exonerated,
            trust=character_trust,
            pressure=character_pressure,
            knows_fact=character_knows_fact
        )

        # Calculate effects
        trust_change = self._calculate_trust_change(reaction, character_is_implicated)
        pressure = self._calculate_pressure(reaction, character_is_implicated)

        # Generate reaction text
        reaction_text = self._generate_reaction_text(
            evidence, character_id, reaction
        )

        # Determine if any new information is revealed
        reveals_fact = None
        unlocks_topic = None

        if reaction in (ReactionType.CRACKED, ReactionType.COOPERATIVE):
            if evidence.fact_id and not character_knows_fact:
                reveals_fact = evidence.fact_id

        if reaction == ReactionType.COOPERATIVE:
            # Might unlock a new dialogue topic
            if evidence.related_facts:
                unlocks_topic = f"about_{evidence.related_facts[0]}"

        return PresentationResult(
            evidence_id=evidence.id,
            character_id=character_id,
            reaction=reaction,
            trust_change=trust_change,
            pressure_applied=pressure,
            reveals_fact=reveals_fact,
            unlocks_topic=unlocks_topic,
            reaction_text=reaction_text
        )

    def _determine_reaction(
        self,
        evidence: Evidence,
        character_id: str,
        archetype: str,
        is_implicated: bool,
        is_exonerated: bool,
        trust: int,
        pressure: int,
        knows_fact: bool
    ) -> ReactionType:
        """Determine the character's reaction."""

        # If evidence clears them
        if is_exonerated:
            return ReactionType.RELIEVED

        # If evidence implicates them
        if is_implicated:
            # Check if they crack under pressure
            if pressure > 70:
                return ReactionType.CRACKED
            elif pressure > 50:
                return ReactionType.FRIGHTENED
            elif pressure > 30:
                return ReactionType.NERVOUS
            else:
                return ReactionType.DEFENSIVE

        # If they have relevant knowledge
        if knows_fact:
            if trust > 20:
                return ReactionType.COOPERATIVE
            else:
                return ReactionType.NERVOUS

        # Archetype-based default reactions
        archetype_reactions = {
            "guilty": ReactionType.DEFENSIVE,
            "survivor": ReactionType.NERVOUS,
            "authority": ReactionType.INDIFFERENT,
            "protector": ReactionType.DEFENSIVE if is_implicated else ReactionType.COOPERATIVE,
            "opportunist": ReactionType.COOPERATIVE if trust > 0 else ReactionType.INDIFFERENT,
            "true_believer": ReactionType.ANGRY,
            "outsider": ReactionType.COOPERATIVE,
            "innocent": ReactionType.CONFUSED
        }

        return archetype_reactions.get(archetype.lower(), ReactionType.INDIFFERENT)

    def _calculate_trust_change(
        self,
        reaction: ReactionType,
        is_implicated: bool
    ) -> int:
        """Calculate trust change from reaction."""
        trust_effects = {
            ReactionType.INDIFFERENT: 0,
            ReactionType.NERVOUS: -5,
            ReactionType.DEFENSIVE: -10,
            ReactionType.FRIGHTENED: -15,
            ReactionType.ANGRY: -20,
            ReactionType.CONFUSED: 0,
            ReactionType.RELIEVED: 15,
            ReactionType.COOPERATIVE: 10,
            ReactionType.CRACKED: -25
        }

        return trust_effects.get(reaction, 0)

    def _calculate_pressure(
        self,
        reaction: ReactionType,
        is_implicated: bool
    ) -> int:
        """Calculate pressure applied from reaction."""
        if not is_implicated:
            return 0

        pressure_effects = {
            ReactionType.NERVOUS: 10,
            ReactionType.DEFENSIVE: 15,
            ReactionType.FRIGHTENED: 20,
            ReactionType.ANGRY: 5,
            ReactionType.CRACKED: 0  # Already cracked
        }

        return pressure_effects.get(reaction, 0)

    def _generate_reaction_text(
        self,
        evidence: Evidence,
        character_id: str,
        reaction: ReactionType
    ) -> str:
        """Generate narrative text for the reaction."""
        reaction_texts = {
            ReactionType.INDIFFERENT: [
                "They barely glance at it.",
                "They show no particular interest.",
                "They seem unaffected by the evidence."
            ],
            ReactionType.NERVOUS: [
                "They shift uncomfortably.",
                "You notice a slight tremor in their hands.",
                "Their eyes dart away from the evidence."
            ],
            ReactionType.DEFENSIVE: [
                "They cross their arms defensively.",
                "\"Where did you get that?\" they demand.",
                "They take a step back, face hardening."
            ],
            ReactionType.FRIGHTENED: [
                "The color drains from their face.",
                "They look like they've seen a ghost.",
                "Their voice wavers as they speak."
            ],
            ReactionType.ANGRY: [
                "Their face flushes with anger.",
                "\"How dare you!\" they snap.",
                "They look ready to lash out."
            ],
            ReactionType.CONFUSED: [
                "They tilt their head in confusion.",
                "\"I don't understand what this means,\" they admit.",
                "They examine it with genuine puzzlement."
            ],
            ReactionType.RELIEVED: [
                "Relief washes over their face.",
                "They let out a breath they'd been holding.",
                "\"Thank goodness,\" they whisper."
            ],
            ReactionType.COOPERATIVE: [
                "They nod thoughtfully.",
                "\"I think I can help you with this,\" they say.",
                "They lean in with interest."
            ],
            ReactionType.CRACKED: [
                "They collapse into themselves.",
                "\"I... I can't do this anymore,\" they whisper.",
                "The fight goes out of them completely."
            ]
        }

        import random
        texts = reaction_texts.get(reaction, ["They react."])
        return random.choice(texts)

    def register_custom_reaction(
        self,
        evidence_id: str,
        character_id: str,
        handler: Callable[[Evidence, str], PresentationResult]
    ) -> None:
        """Register a custom reaction handler for specific evidence+character."""
        key = f"{evidence_id}:{character_id}"
        self._reaction_handlers[key] = handler

    def get_effective_evidence(
        self,
        evidence_list: list[Evidence],
        character_id: str
    ) -> list[Evidence]:
        """Get evidence that would have an effect on a character."""
        effective = []
        for evidence in evidence_list:
            if character_id in evidence.implicates:
                effective.append(evidence)
            elif character_id in evidence.exonerates:
                effective.append(evidence)
            elif evidence.related_facts:
                effective.append(evidence)
        return effective
