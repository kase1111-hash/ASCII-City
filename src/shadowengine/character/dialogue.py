"""
Dialogue System - Topic-based conversation management.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum


class ResponseType(Enum):
    """Types of dialogue responses."""
    HONEST = "honest"           # Truthful response
    LIE = "lie"                 # Deliberate falsehood
    DEFLECT = "deflect"         # Avoids the question
    REFUSE = "refuse"           # Won't discuss
    REVEAL = "reveal"           # Reveals secret (when cracked)
    PARTIAL = "partial"         # Partial truth


@dataclass
class DialogueResponse:
    """A response to a dialogue topic."""

    text: str
    response_type: ResponseType
    reveals_fact: Optional[str] = None  # Fact ID this reveals
    is_evidence: bool = False           # Is this usable evidence?
    trust_change: int = 0               # How this affects trust
    pressure_applied: int = 0           # Pressure from asking this
    unlocks_topics: list[str] = field(default_factory=list)
    mood_modifier: str = ""             # Added based on character mood


@dataclass
class DialogueTopic:
    """A topic that can be discussed with a character."""

    id: str
    name: str                           # Display name
    description: str                    # What asking about this means
    requires_discovery: Optional[str] = None  # Fact player must know first
    requires_trust: int = 0             # Minimum trust to ask
    is_accusation: bool = False         # Is this accusing the character
    pressure_amount: int = 0            # Pressure applied when asked

    # Responses based on character state
    honest_response: str = ""
    lie_response: str = ""
    cracked_response: str = ""
    refuse_response: str = "I don't want to talk about that."

    # What this topic reveals
    reveals_on_honest: Optional[str] = None
    reveals_on_cracked: Optional[str] = None

    def get_response(
        self,
        is_cracked: bool,
        will_lie: bool,
        will_refuse: bool
    ) -> DialogueResponse:
        """Get appropriate response based on character state."""

        if will_refuse:
            return DialogueResponse(
                text=self.refuse_response,
                response_type=ResponseType.REFUSE,
                pressure_applied=self.pressure_amount
            )

        if is_cracked and self.cracked_response:
            return DialogueResponse(
                text=self.cracked_response,
                response_type=ResponseType.REVEAL,
                reveals_fact=self.reveals_on_cracked,
                is_evidence=True,
                pressure_applied=0
            )

        if will_lie and self.lie_response:
            return DialogueResponse(
                text=self.lie_response,
                response_type=ResponseType.LIE,
                pressure_applied=self.pressure_amount
            )

        return DialogueResponse(
            text=self.honest_response,
            response_type=ResponseType.HONEST,
            reveals_fact=self.reveals_on_honest,
            pressure_applied=self.pressure_amount
        )


class DialogueManager:
    """
    Manages dialogue topics and responses for all characters.
    """

    def __init__(self):
        self.topics: dict[str, DialogueTopic] = {}
        self.character_topics: dict[str, set[str]] = {}  # char_id -> topic_ids

    def register_topic(self, topic: DialogueTopic) -> None:
        """Register a dialogue topic."""
        self.topics[topic.id] = topic

    def assign_topic_to_character(self, character_id: str, topic_id: str) -> None:
        """Assign a topic to a character."""
        if character_id not in self.character_topics:
            self.character_topics[character_id] = set()
        self.character_topics[character_id].add(topic_id)

    def get_character_topics(self, character_id: str) -> list[DialogueTopic]:
        """Get all topics available for a character."""
        topic_ids = self.character_topics.get(character_id, set())
        return [self.topics[tid] for tid in topic_ids if tid in self.topics]

    def get_available_topics(
        self,
        character_id: str,
        player_discoveries: set[str],
        player_trust: int,
        exhausted: set[str]
    ) -> list[DialogueTopic]:
        """
        Get topics the player can currently ask about.

        Filters based on discoveries, trust, and what's been exhausted.
        """
        all_topics = self.get_character_topics(character_id)
        available = []

        for topic in all_topics:
            # Skip exhausted topics
            if topic.id in exhausted:
                continue

            # Check discovery requirement
            if topic.requires_discovery and topic.requires_discovery not in player_discoveries:
                continue

            # Check trust requirement
            if topic.requires_trust > player_trust:
                continue

            available.append(topic)

        return available

    def get_topic(self, topic_id: str) -> Optional[DialogueTopic]:
        """Get a specific topic by ID."""
        return self.topics.get(topic_id)

    def create_greeting_topic(self, character_name: str, greeting: str) -> DialogueTopic:
        """Create a standard greeting topic for a character."""
        return DialogueTopic(
            id=f"greet_{character_name.lower()}",
            name="Greeting",
            description=f"Greet {character_name}",
            honest_response=greeting,
            lie_response=greeting,  # Greeting doesn't really have a lie version
            refuse_response=greeting
        )

    def create_accusation_topic(
        self,
        character_name: str,
        crime: str,
        denial: str,
        confession: str
    ) -> DialogueTopic:
        """Create an accusation topic for a character."""
        return DialogueTopic(
            id=f"accuse_{character_name.lower()}",
            name="Accusation",
            description=f"Accuse {character_name} of {crime}",
            is_accusation=True,
            pressure_amount=30,
            honest_response=denial,
            lie_response=denial,
            cracked_response=confession,
            refuse_response=f"How dare you! I won't dignify that with a response.",
            reveals_on_cracked=f"{character_name.lower()}_confession"
        )


# Global dialogue manager instance
dialogue_manager = DialogueManager()
