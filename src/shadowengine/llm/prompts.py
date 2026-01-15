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


# =============================================================================
# LOCATION GENERATION - For procedural world building
# =============================================================================

LOCATION_SYSTEM = """You are a world-builder for a procedural noir/adventure game.
You generate new locations as the player explores in any direction.

The world is infinite - players can go anywhere: cities, wilderness, other countries,
fantasy realms, the south pole, space - wherever their imagination takes them.

Your job is to create coherent, interesting locations that:
1. Make logical sense given where the player is coming from
2. Maintain consistency with the game's current narrative/mood
3. Provide interesting things to examine and people to talk to
4. Can connect back to the main story or create new story threads

Output format (JSON):
{
    "id": "unique_snake_case_id",
    "name": "Location Display Name",
    "description": "2-3 sentence atmospheric description",
    "location_type": "street|bar|office|alley|wilderness|building|vehicle|other",
    "is_outdoor": true/false,
    "ambient": "Short ambient description for mood",
    "hotspots": [
        {
            "id": "hs_unique_id",
            "label": "Display Name",
            "type": "object|person|exit|evidence|container",
            "description": "What player sees",
            "examine_text": "Detailed examination text",
            "character_id": "only for person type - null otherwise",
            "exit_to": "only for exit type - direction or place name"
        }
    ],
    "npcs": [
        {
            "id": "unique_npc_id",
            "name": "NPC Name",
            "description": "Physical/personality description",
            "archetype": "survivor|opportunist|authority|outsider|innocent|guilty",
            "secret": "What they're hiding",
            "public_persona": "How they present themselves",
            "topics": ["topic1", "topic2"]
        }
    ],
    "connections": {
        "north": "brief description of what's north",
        "south": "brief description of what's south",
        "east": "brief description of what's east",
        "west": "brief description of what's west",
        "back": "the place player came from"
    }
}"""


LOCATION_GENERATE = """Generate a new location for the player.

CURRENT CONTEXT:
- Player is at: $current_location ($current_description)
- Player wants to go: $destination (direction or specific place)
- Time of day: $time
- Weather: $weather
- Game genre/mood: $genre

STORY CONTEXT:
$story_context

WORLD SO FAR:
$visited_locations

PLAYER INVENTORY:
$inventory

Generate an appropriate new location. Be creative but consistent.
If the player wants to go somewhere unexpected (like "the moon" or "ancient Rome"),
create a transition that makes narrative sense - maybe they find a vehicle,
a portal, fall asleep and dream, or discover the world is stranger than expected."""


@dataclass
class LocationPrompt:
    """Prompt generator for procedural location generation."""

    def get_system_prompt(self) -> str:
        """Get the system prompt for location generation."""
        return LOCATION_SYSTEM

    def get_generation_prompt(
        self,
        current_location: str,
        current_description: str,
        destination: str,
        time: str = "night",
        weather: str = "clear",
        genre: str = "noir mystery",
        story_context: str = "",
        visited_locations: Optional[list] = None,
        inventory: Optional[list] = None
    ) -> str:
        """Get prompt for generating a new location."""
        visited = "\n".join([f"- {loc}" for loc in (visited_locations or [])]) or "None yet"
        items = ", ".join(inventory or []) or "Nothing"

        return Template(LOCATION_GENERATE).safe_substitute(
            current_location=current_location,
            current_description=current_description,
            destination=destination,
            time=time,
            weather=weather,
            genre=genre,
            story_context=story_context or "No specific story yet - player is exploring freely",
            visited_locations=visited,
            inventory=items
        )
