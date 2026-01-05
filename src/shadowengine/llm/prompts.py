"""
Prompt Templates - Structured prompts for game LLM interactions.

Provides templates for character dialogue, narrative generation,
and behavioral evaluation.
"""

from dataclasses import dataclass, field
from typing import Optional
from string import Template


@dataclass
class PromptTemplate:
    """Base prompt template with variable substitution."""
    template: str
    variables: dict = field(default_factory=dict)

    def render(self, **kwargs) -> str:
        """Render the template with given variables."""
        merged = {**self.variables, **kwargs}
        return Template(self.template).safe_substitute(merged)


# Character system prompt template
CHARACTER_SYSTEM = """You are $name, $description

Your personality:
- Archetype: $archetype
- Trust level: $trust (0-100, higher = more willing to share)
- Current mood: $mood

Your secret: $secret_truth
Your cover story: $public_lie

Rules:
1. Stay in character at all times
2. If trust is below 30, be evasive and defensive
3. If trust is above 70, be more open but still cautious
4. Never directly reveal your secret unless "cracked"
5. Respond in 1-3 sentences, noir style
6. Use period-appropriate language (1940s-1950s)"""


# Character response prompt
CHARACTER_RESPONSE = """The player asks you: "$question"

Context:
- Location: $location
- Time: $time
- Previous topics discussed: $topics_discussed
- Evidence player has shown: $evidence

Respond as $name would, staying in character."""


@dataclass
class CharacterPrompt:
    """Prompt generator for character dialogue."""
    name: str
    description: str
    archetype: str
    trust: int
    mood: str
    secret_truth: str
    public_lie: str

    def get_system_prompt(self) -> str:
        """Get the system prompt for this character."""
        return Template(CHARACTER_SYSTEM).safe_substitute(
            name=self.name,
            description=self.description,
            archetype=self.archetype,
            trust=self.trust,
            mood=self.mood,
            secret_truth=self.secret_truth,
            public_lie=self.public_lie
        )

    def get_response_prompt(
        self,
        question: str,
        location: str = "unknown",
        time: str = "evening",
        topics_discussed: Optional[list] = None,
        evidence: Optional[list] = None
    ) -> str:
        """Get the response prompt for a player question."""
        return Template(CHARACTER_RESPONSE).safe_substitute(
            question=question,
            location=location,
            time=time,
            topics_discussed=", ".join(topics_discussed or ["none"]),
            evidence=", ".join(evidence or ["none"]),
            name=self.name
        )


# Narrative generation template
NARRATIVE_SYSTEM = """You are the narrator for a noir mystery game.
Your role is to describe scenes, actions, and atmosphere.

Style guidelines:
1. Use evocative, atmospheric language
2. Keep descriptions to 2-4 sentences
3. Focus on sensory details: shadows, sounds, smells
4. Maintain noir tone: cynical, moody, atmospheric
5. Never break the fourth wall"""


NARRATIVE_SCENE = """Describe the following scene:
Location: $location
Time: $time
Weather: $weather
Characters present: $characters
Recent events: $events

The player has just $action."""


@dataclass
class NarrativePrompt:
    """Prompt generator for narrative descriptions."""

    def get_system_prompt(self) -> str:
        """Get the system prompt for narration."""
        return NARRATIVE_SYSTEM

    def get_scene_prompt(
        self,
        location: str,
        time: str,
        weather: str,
        characters: list[str],
        events: list[str],
        action: str
    ) -> str:
        """Get prompt for scene description."""
        return Template(NARRATIVE_SCENE).safe_substitute(
            location=location,
            time=time,
            weather=weather,
            characters=", ".join(characters) if characters else "none",
            events=", ".join(events[-3:]) if events else "none",  # Last 3 events
            action=action
        )


# Behavior evaluation template
BEHAVIOR_SYSTEM = """You are evaluating NPC behavior for a noir mystery game.
Given a situation, determine the most appropriate behavioral response.

Output format (JSON):
{
    "action": "action type (flee/hide/approach/ignore/alert/investigate)",
    "intensity": 0.0-1.0,
    "target": "optional target",
    "narrative": "brief description of the behavior"
}"""


BEHAVIOR_EVALUATE = """Evaluate NPC behavior:
NPC: $npc_name ($npc_type)
Personality: $personality
Current state: $state

Situation:
- Stimulus: $stimulus
- Distance: $distance tiles away
- Threat level: $threat_level
- Time of day: $time
- Other NPCs nearby: $nearby_npcs

What should $npc_name do?"""


@dataclass
class BehaviorPrompt:
    """Prompt generator for behavioral evaluation."""

    def get_system_prompt(self) -> str:
        """Get the system prompt for behavior evaluation."""
        return BEHAVIOR_SYSTEM

    def get_evaluation_prompt(
        self,
        npc_name: str,
        npc_type: str,
        personality: str,
        state: str,
        stimulus: str,
        distance: float,
        threat_level: float,
        time: str,
        nearby_npcs: list[str]
    ) -> str:
        """Get prompt for behavior evaluation."""
        return Template(BEHAVIOR_EVALUATE).safe_substitute(
            npc_name=npc_name,
            npc_type=npc_type,
            personality=personality,
            state=state,
            stimulus=stimulus,
            distance=f"{distance:.1f}",
            threat_level=f"{threat_level:.1%}",
            time=time,
            nearby_npcs=", ".join(nearby_npcs) if nearby_npcs else "none"
        )
