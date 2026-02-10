"""
Dialogue Handler - LLM-driven NPC dialogue generation.

Handles generating character dialogue responses via the LLM,
including building character context, conversation history,
memory-based beliefs, and cleaning up responses.
"""

from typing import Optional, TYPE_CHECKING
import logging

from ..character import Character
from ..llm.validation import sanitize_player_input

if TYPE_CHECKING:
    from ..llm import LLMClient
    from ..world_state import WorldState
    from ..narrative import NarrativeSpine
    from ..memory.character_memory import CharacterMemory

logger = logging.getLogger(__name__)


class DialogueHandler:
    """
    Handles LLM-driven NPC dialogue generation.

    Encapsulates prompt construction, LLM interaction, and response
    cleaning for character conversations.
    """

    def __init__(self, llm_client: 'LLMClient', world_state: 'WorldState'):
        self.llm_client = llm_client
        self.world_state = world_state

    def generate_response(
        self,
        character: Character,
        player_input: str,
        spine: Optional['NarrativeSpine'] = None,
        mystery: Optional[dict] = None,
        evidence_found: Optional[list[str]] = None,
        current_location_id: str = "",
        character_memory: Optional['CharacterMemory'] = None,
        intelligence_hints: Optional[dict] = None,
    ) -> Optional[str]:
        """
        Generate an NPC dialogue response using the LLM.

        Args:
            character: The NPC being spoken to
            player_input: What the player said
            spine: The narrative spine for story context
            mystery: Mystery details dict (victim, crime, suspects)
            evidence_found: List of evidence IDs the player has found
            current_location_id: ID of the current location
            character_memory: The NPC's subjective memory (beliefs, interactions)
            intelligence_hints: Behavior hints from PropagationEngine (tone, willingness, rumors)

        Returns:
            The generated dialogue string, or None if generation failed
        """
        evidence_found = evidence_found or []

        # Build story context
        story_context = ""
        if spine:
            story_context = f"Mystery: {spine.conflict_description}"
        if mystery:
            story_context += f"\nVictim: {mystery.get('victim', 'unknown')}"

        # Get NPC's knowledge from WorldState
        npc_knowledge = self.world_state.get_npc_knowledge(character.id)

        # Get NPC context (relationships, events)
        npc_context = self.world_state.get_npc_context(character.id)
        relationships_str = ""
        if npc_context.get("relationships"):
            relationships_str = "PEOPLE YOU KNOW:\n" + "\n".join(
                f"- {r}" for r in npc_context["relationships"]
            )

        # Get conversation history
        topics_discussed = list(character.exhausted_topics)

        # Get previous dialogue with this NPC
        dialogue_history = self.world_state.generation_memory.get_npc_dialogue_history(
            character.id, limit=3
        )

        # Build memory context from CharacterMemory
        memory_context = self._build_memory_context(character_memory)

        # Build intelligence context from PropagationEngine
        intel_context = self._build_intelligence_context(intelligence_hints)

        # Build the system prompt
        system_prompt = self._build_system_prompt(
            character, relationships_str, npc_knowledge,
            story_context, memory_context, intel_context,
        )

        # Build the user prompt
        user_prompt = self._build_user_prompt(
            character, player_input, dialogue_history,
            topics_discussed, evidence_found, current_location_id,
        )

        # Call LLM
        response = self.llm_client.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        if response.success and response.text:
            return self._clean_response(response.text, character.name)

        logger.warning(f"Dialogue generation failed for character '{character.id}'")
        return None

    @staticmethod
    def _build_memory_context(
        character_memory: Optional['CharacterMemory'],
    ) -> str:
        """Build prompt context from character's subjective memory."""
        if not character_memory:
            return ""

        parts = []

        # Recent beliefs
        recent_beliefs = character_memory.beliefs[-5:] if character_memory.beliefs else []
        if recent_beliefs:
            belief_lines = []
            for b in recent_beliefs:
                conf = b.confidence.value
                belief_lines.append(f"- [{conf}] {b.content} (source: {b.source})")
            parts.append("THINGS YOU BELIEVE:\n" + "\n".join(belief_lines))

        # Suspicions
        if character_memory.suspicions:
            susp_lines = [
                f"- {target}: {conf:.0%} suspicious"
                for target, conf in character_memory.suspicions.items()
                if conf > 0.1
            ]
            if susp_lines:
                parts.append("YOUR SUSPICIONS:\n" + "\n".join(susp_lines))

        # Previous interactions with the player
        recent_interactions = character_memory.get_recent_interactions(3)
        if recent_interactions:
            interaction_lines = []
            for i in recent_interactions:
                topic_str = f" about {i.topic}" if i.topic else ""
                interaction_lines.append(
                    f"- Player {i.interaction_type}{topic_str} "
                    f"(tone: {i.player_tone}, you {i.outcome})"
                )
            parts.append(
                "YOUR HISTORY WITH THE DETECTIVE:\n"
                + "\n".join(interaction_lines)
            )

        # Net trust from interactions
        net_trust = character_memory.total_trust_change()
        if net_trust != 0:
            direction = "warmer toward" if net_trust > 0 else "colder toward"
            parts.append(f"Overall you feel {direction} the detective (trust shift: {net_trust:+d})")

        return "\n\n".join(parts)

    @staticmethod
    def _build_intelligence_context(
        intelligence_hints: Optional[dict],
    ) -> str:
        """Build prompt context from NPC intelligence system (rumors, behavior)."""
        if not intelligence_hints:
            return ""

        parts = []

        # Dialogue modifiers from behavior system
        tone = intelligence_hints.get("tone", "neutral")
        willingness = intelligence_hints.get("willingness", "medium")
        honesty = intelligence_hints.get("honesty", "honest")

        if tone != "neutral" or willingness != "medium" or honesty != "honest":
            parts.append(
                f"YOUR CURRENT DISPOSITION: tone={tone}, "
                f"willingness to share={willingness}, honesty={honesty}"
            )

        # Rumors this NPC has heard
        rumors = intelligence_hints.get("rumors", [])
        if rumors:
            rumor_lines = [f"- {r}" for r in rumors[:5]]
            parts.append("RUMORS YOU'VE HEARD:\n" + "\n".join(rumor_lines))

        # NPC memories of notable events
        npc_memories = intelligence_hints.get("memories", [])
        if npc_memories:
            mem_lines = [f"- {m}" for m in npc_memories[:5]]
            parts.append("THINGS YOU REMEMBER:\n" + "\n".join(mem_lines))

        return "\n\n".join(parts)

    @staticmethod
    def _build_system_prompt(
        character: Character,
        relationships_str: str,
        npc_knowledge: str,
        story_context: str,
        memory_context: str = "",
        intelligence_context: str = "",
    ) -> str:
        """Build the system prompt for character dialogue generation."""
        memory_section = f"\n\n{memory_context}" if memory_context else ""
        intel_section = f"\n\n{intelligence_context}" if intelligence_context else ""

        return f"""You are {character.name}, {character.description}

PERSONALITY:
- Archetype: {character.archetype.value}
- Trust level: {character.current_trust} (higher = more open)
- Current mood: {character.state.mood.value}
- Pressure level: {character.state.pressure_accumulated}

YOUR SECRET (never reveal unless trust > 70 or you're "cracked"):
{character.secret_truth}

YOUR COVER STORY (use this to deflect):
{character.public_lie}

{relationships_str}

WHAT YOU KNOW ABOUT THE WORLD:
{npc_knowledge if npc_knowledge else 'Nothing special'}

STORY CONTEXT:
{story_context}{memory_section}{intel_section}

RULES:
1. Stay completely in character
2. If trust < 30, be evasive and defensive
3. If trust > 70, be more open but still cautious
4. Never directly reveal your secret unless specifically pressured
5. Respond in 1-3 sentences, noir dialogue style
6. React based on your archetype and mood
7. If asked about something you know, hint at it without fully revealing
8. Reference people you know or events you've heard about when relevant
9. Reference previous interactions with the detective when relevant — show that you remember
10. If you've heard rumors, you may reference them obliquely or use them to deflect"""

    @staticmethod
    def _build_user_prompt(
        character: Character,
        player_input: str,
        dialogue_history: str,
        topics_discussed: list[str],
        evidence_found: list[str],
        current_location_id: str,
    ) -> str:
        """Build the user prompt for dialogue generation."""
        history_section = ""
        if dialogue_history:
            history_section = f"\nPREVIOUS CONVERSATION WITH THIS DETECTIVE:\n{dialogue_history}\n"

        return f"""The detective says: "{sanitize_player_input(player_input)}"
{history_section}
Topics already discussed: {', '.join(topics_discussed) if topics_discussed else 'None'}
Evidence the detective has shown: {', '.join(evidence_found) if evidence_found else 'None'}
Current location: {current_location_id}

Remember what you said before and stay consistent. Respond as {character.name} would."""

    @staticmethod
    def _clean_response(text: str, character_name: str) -> str:
        """Clean up LLM response text."""
        text = text.strip()
        # Remove any "Character:" prefix the LLM might add
        if text.lower().startswith(character_name.lower() + ":"):
            text = text[len(character_name) + 1:].strip()
        return text
