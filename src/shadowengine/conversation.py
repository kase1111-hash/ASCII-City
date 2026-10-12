"""
ConversationManager - Handles NPC dialogue, threats, and accusations.

Extracted from game.py to isolate the conversation loop and
LLM-driven dialogue into a testable, focused module.
"""

from typing import Optional
import logging

from .config import (
    THREATEN_PRESSURE_AMOUNT, THREATEN_TRUST_PENALTY,
    ACCUSE_PRESSURE_AMOUNT, ACCUSE_WRONG_TRUST_PENALTY,
    THREATEN_MORAL_WEIGHT, THREATEN_RUTHLESS_EFFECT,
    THREATEN_COMPASSIONATE_EFFECT, THREATEN_IDEALISTIC_EFFECT,
    SHOW_EVIDENCE_PRESSURE_AMOUNT, SHOW_CHAIN_EVIDENCE_PRESSURE_AMOUNT,
)
from .character import Character
from .render import Renderer
from .generation.dialogue_handler import DialogueHandler
from .testimony import Testimony

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages NPC conversations: free-form dialogue, threats, accusations.
    """

    def __init__(
        self,
        renderer: Renderer,
        dialogue_handler: DialogueHandler,
        audio_engine=None,
        speech_enabled: bool = False,
        testimony: Optional[Testimony] = None,
    ):
        self.renderer = renderer
        self.dialogue_handler = dialogue_handler
        self.audio_engine = audio_engine
        self.speech_enabled = speech_enabled
        self.testimony = testimony or Testimony()
        # Handles case/inventory/save/load/quit typed mid-conversation;
        # returns True if it handled the input (wired by the Game)
        self.meta_handler = None

    def speak_dialogue(self, character_id: str, text: str, mood: str = "") -> None:
        """Speak dialogue using TTS if enabled."""
        if not self.speech_enabled or not self.audio_engine:
            return

        try:
            # AudioEmotion may not be available if audio is deferred
            from .audio import EmotionalState as AudioEmotion
            emotion_mapping = {
                "angrily": AudioEmotion.ANGRY,
                "sadly": AudioEmotion.SAD,
                "nervously": AudioEmotion.NERVOUS,
                "desperately": AudioEmotion.FEARFUL,
                "defensively": AudioEmotion.SUSPICIOUS,
                "defeated": AudioEmotion.TIRED,
                "happily": AudioEmotion.HAPPY,
                "excitedly": AudioEmotion.EXCITED,
            }
            emotion = emotion_mapping.get(mood.lower()) if mood else None
        except ImportError:
            emotion = None

        self.audio_engine.speak(character_id, text, emotion)

    def show_dialogue(self, character: Character, text: str, mood: str = "") -> None:
        """Display dialogue and speak it using TTS."""
        self.renderer.render_dialogue(character.name, text, mood)
        self.speak_dialogue(character.id, text, mood)

    def offer_testimony(self, character: Character, state: 'GameState') -> list[str]:
        """If the exchange left them ready to talk, they tell what they know."""
        return self.testimony.offer(
            character, state, self.renderer,
            speak=lambda c, line: self.show_dialogue(
                c, line, c.get_response_mood_modifier()
            ),
        )

    def conversation_loop(self, state: 'GameState') -> None:
        """Handle one tick of conversation mode."""
        character_id = state.conversation_partner
        character = state.characters.get(character_id)

        if not character:
            state.in_conversation = False
            return

        # Show character info
        self.renderer.clear_screen()
        self.renderer.render_text(f"\n{'=' * 60}")
        self.renderer.render_text(f"  {character.name}")
        self.renderer.render_text(f"  {character.description}")
        self.renderer.render_text(f"{'=' * 60}")

        if character.state.is_cracked:
            if self.testimony.is_culprit(character, state):
                self.renderer.render_text("\n(They seem broken, ready to confess...)")
            else:
                self.renderer.render_text("\n(They've stopped holding anything back.)")

        topics = sorted(character.get_available_topics())
        if topics:
            self.renderer.render_text(f"(They might open up about: {', '.join(topics)})")
        self.renderer.render_text(self.ACTIONS_FOOTER)

        # Get free-form input
        raw_input = self.renderer.render_dialogue_prompt(character.name)
        input_lower = raw_input.lower().strip()
        words = input_lower.replace("!", " ").replace("?", " ").replace(".", " ").split()
        first = words[0] if words else ""

        if input_lower in ["leave", "bye", "goodbye", "exit", "go", "back"]:
            state.in_conversation = False
            state.conversation_partner = None
            self.renderer.render_narration(f"You end the conversation with {character.name}.")
            self.renderer.wait_for_key()
            return

        if input_lower in ("help", "?", "h", "commands"):
            self.renderer.render_text(self.CONVERSATION_HELP)
            self.renderer.wait_for_key()
            return

        # The case file, pockets, save/load/quit work mid-conversation too
        if input_lower in self.META_WORDS and self.meta_handler:
            if self.meta_handler(input_lower, state):
                return

        if first in ("threaten", "intimidate"):
            self.handle_threaten(character, state)
            return

        if first in ("accuse", "arrest") or input_lower in ("i accuse you", "you did it"):
            self.handle_accuse(character, state)
            return

        if first in ("show", "present"):
            self.handle_show_evidence(character, raw_input.strip()[len(first):].strip(), state)
            return

        # Free-form dialogue via LLM
        self.handle_free_dialogue(character, raw_input, state)
        self.offer_testimony(character, state)
        self.renderer.wait_for_key()

    ACTIONS_FOOTER = (
        "(Say anything. Or: show [evidence], threaten, accuse, case, leave)"
    )

    CONVERSATION_HELP = """
While talking, just type what you'd say. Ask about the things they care
about and they'll warm to you; when they trust you, they'll tell you what
they know.

  show [evidence]   Lay something from your case file on the table
  threaten          Lean on them (they'll trust you less)
  accuse            Name them as the killer
  case              Check your case file without leaving
  inventory         Check your pockets
  leave             End the conversation
"""

    META_WORDS = {
        "case", "casebook", "notes", "journal", "clues", "evidence",
        "inventory", "inv", "items", "i", "save", "load", "quit", "q",
    }

    def handle_free_dialogue(
        self, character: Character, player_input: str, state: 'GameState'
    ) -> None:
        """Handle any free-form dialogue input via LLM."""
        # Asking about what they care about builds rapport
        self.testimony.note_rapport(character, player_input)

        mood_mod = character.get_response_mood_modifier()
        char_memory = state.memory.get_character_memory(character.id)

        # If character is cracked, they reveal their secret
        if character.state.is_cracked and character.secret_truth:
            response_text = f"Fine! You want the truth? {character.secret_truth}"
            self.show_dialogue(character, response_text, "desperately")
            state.world_state.generation_memory.record_dialogue(
                npc_id=character.id,
                player_said=player_input,
                npc_response=response_text,
                location_id=state.current_location_id,
                revealed=character.secret_truth,
                timestamp=state.memory.current_time,
            )
            # Record confession in character memory
            if char_memory:
                char_memory.record_player_interaction(
                    timestamp=state.memory.current_time,
                    interaction_type="confessed_to",
                    player_tone="pressing",
                    outcome="revealed_secret",
                    trust_change=0,
                    topic=player_input[:50],
                )
            return

        # Generate response via LLM (with character memory context)
        response = self.generate_dialogue(character, player_input, state)

        if response:
            self.show_dialogue(character, response, mood_mod)
            state.world_state.generation_memory.record_dialogue(
                npc_id=character.id,
                player_said=player_input,
                npc_response=response,
                location_id=state.current_location_id,
                timestamp=state.memory.current_time,
            )
            # Record interaction in character memory
            if char_memory:
                char_memory.record_player_interaction(
                    timestamp=state.memory.current_time,
                    interaction_type="talked",
                    player_tone="neutral",
                    outcome="shared_info" if character.will_cooperate() else "deflected",
                    trust_change=0,
                    topic=player_input[:50],
                )
        else:
            if character.will_cooperate():
                fallback = "Hmm... I'm not sure what to say about that."
            else:
                fallback = "I don't have anything to tell you."
            self.show_dialogue(character, fallback, mood_mod)

    def generate_dialogue(
        self, character: Character, player_input: str, state: 'GameState'
    ) -> Optional[str]:
        """Generate NPC dialogue response using LLM, enriched with memory and intelligence."""
        char_memory = state.memory.get_character_memory(character.id)

        # Pull intelligence hints from PropagationEngine (rumors, behavior)
        intelligence_hints = None
        if getattr(state, 'propagation_engine', None):
            engine = state.propagation_engine
            hints = engine.get_npc_behavior_hints(character.id)

            # Get rumors known by this NPC
            rumors = []
            npc_memories = []
            npc_state = engine.get_npc_state(character.id)
            if npc_state:
                shareable = npc_state.memory_bank.get_shareable_memories()
                npc_memories = [m.summary for m in shareable[:5]]

                known_rumors = engine.rumor_propagation.get_rumors_known_by(character.id)
                rumors = [r.core_claim for r in known_rumors[:5]]

            if hints or rumors or npc_memories:
                intelligence_hints = {**hints, "rumors": rumors, "memories": npc_memories}

        # Recent discoveries as readable descriptions — raw fact ids are
        # meaningless to the LLM
        recent_evidence = [
            d.description
            for d in list(state.memory.player.discoveries.values())[-10:]
        ]

        return self.dialogue_handler.generate_response(
            character=character,
            player_input=player_input,
            spine=state.spine,
            mystery=getattr(state, 'mystery', None),
            evidence_found=recent_evidence,
            current_location_id=state.current_location_id,
            character_memory=char_memory,
            intelligence_hints=intelligence_hints,
            case_knowledge=self.testimony.case_knowledge(character, state),
        )

    @staticmethod
    def _find_discovery(query: str, state: 'GameState'):
        """Match player wording against discovered facts (evidence first)."""
        query = query.lower().strip()
        if not query:
            return None
        discoveries = list(state.memory.player.discoveries.values())
        ranked = sorted(discoveries, key=lambda d: not d.is_evidence)
        for discovery in ranked:
            # Where it came from counts too: "show chalk" finds what the
            # chalk outline revealed
            haystack = (
                f"{discovery.description} {discovery.fact_id} {discovery.source}"
            ).lower()
            if all(word in haystack for word in query.split()):
                return discovery
        return None

    def handle_show_evidence(
        self, character: Character, query: str, state: 'GameState'
    ) -> None:
        """
        Present a discovered fact (or carried item) to an NPC.

        Hard evidence applies interrogation pressure — more if the fact is
        part of the chain that actually proves the case. This is the payoff
        loop for close inspection: what you find, you can use.
        """
        # "show him the chalk" is about the chalk
        query = " ".join(
            w for w in query.lower().split()
            if w not in ("him", "her", "them", "you", "the", "a", "an", "this", "that", "my", "to")
        )
        if not query:
            self.renderer.render_error(
                "Show them what? Name something from your case file ('case')."
            )
            self.renderer.wait_for_key()
            return
        discovery = self._find_discovery(query, state)

        # Fall back to showing a carried item as free dialogue
        if discovery is None:
            query_lower = query.lower()
            item = next(
                (i for i in state.inventory if query_lower in str(i).lower()),
                None,
            )
            if item is None:
                self.renderer.render_error(
                    f"You have nothing like '{query}' to show. "
                    "Check 'case' for what you've gathered."
                )
                self.renderer.wait_for_key()
                return
            self.handle_free_dialogue(
                character,
                f"[The detective shows you: {item}]",
                state,
            )
            self.renderer.wait_for_key()
            return

        self.renderer.render_narration(
            f"You lay it out for {character.name}: {discovery.description}"
        )

        # Pressure: hard evidence rattles; case-proving evidence rattles more
        pressure = 0
        if discovery.is_evidence:
            pressure = SHOW_EVIDENCE_PRESSURE_AMOUNT
            if (
                state.spine
                and discovery.fact_id in state.spine.true_resolution.evidence_chain
            ):
                pressure = SHOW_CHAIN_EVIDENCE_PRESSURE_AMOUNT

        cracked = character.apply_pressure(
            pressure, can_crack=self.testimony.can_crack(character, state),
        ) if pressure else False

        if cracked and character.secret_truth:
            self.renderer.render_narration(
                f"{character.name} stares at the evidence. Something behind "
                "their eyes gives way."
            )
            self.show_dialogue(
                character,
                f"Where did you... Fine. FINE. {character.secret_truth}",
                "desperately",
            )
        else:
            self.handle_free_dialogue(
                character,
                f"[The detective shows you evidence: {discovery.description}]",
                state,
            )

        # Record the confrontation in memories and the world
        char_memory = state.memory.get_character_memory(character.id)
        if char_memory:
            char_memory.record_player_interaction(
                timestamp=state.memory.current_time,
                interaction_type="shown_evidence",
                player_tone="pressing",
                outcome="cracked" if cracked else "held_firm",
                trust_change=0,
                topic=discovery.description[:50],
            )
        state.world_state.generation_memory.record_dialogue(
            npc_id=character.id,
            player_said=f"[showed evidence: {discovery.description[:80]}]",
            npc_response="confessed" if cracked else "reacted",
            location_id=state.current_location_id,
            timestamp=state.memory.current_time,
        )

        self.offer_testimony(character, state)
        self.renderer.wait_for_key()

    def handle_threaten(self, character: Character, state: 'GameState') -> None:
        """Handle threatening a character."""
        already_cracked = character.state.is_cracked
        cracked = character.apply_pressure(
            THREATEN_PRESSURE_AMOUNT,
            can_crack=self.testimony.can_crack(character, state),
        )

        state.memory.player.record_moral_action(
            action_type="threaten",
            description=f"Threatened {character.name}",
            timestamp=state.memory.current_time,
            target=character.id,
            shade_effects={
                "ruthless": THREATEN_RUTHLESS_EFFECT,
                "compassionate": THREATEN_COMPASSIONATE_EFFECT,
                "idealistic": THREATEN_IDEALISTIC_EFFECT,
            },
            weight=THREATEN_MORAL_WEIGHT,
        )

        response_text: str
        if cracked:
            self.renderer.render_narration(
                f"{character.name} breaks down under your pressure!"
            )
            response_text = f"Stop! I'll tell you everything! {character.secret_truth}"
            self.show_dialogue(character, response_text, "desperately")
        elif already_cracked:
            response_text = "I already told you everything! What more do you want?"
            self.show_dialogue(character, response_text, "desperately")
        else:
            mood_mod = character.get_response_mood_modifier()
            response_text = "You don't scare me... much."
            self.show_dialogue(character, response_text, mood_mod)

        character.modify_trust(THREATEN_TRUST_PENALTY)

        # Record in generation memory so LLM knows about the threat
        state.world_state.generation_memory.record_dialogue(
            npc_id=character.id,
            player_said="[threatened]",
            npc_response=response_text,
            location_id=state.current_location_id,
            timestamp=state.memory.current_time,
        )

        # Record threat in character memory
        char_memory = state.memory.get_character_memory(character.id)
        if char_memory:
            char_memory.record_player_interaction(
                timestamp=state.memory.current_time,
                interaction_type="threatened",
                player_tone="aggressive",
                outcome="cracked" if cracked else "resisted",
                trust_change=THREATEN_TRUST_PENALTY,
            )

        # Feed into NPC intelligence — other NPCs may hear about this
        bridge = getattr(state, 'event_bridge', None)
        if bridge:
            bridge.on_threaten(
                character.id, location=state.current_location_id
            )

        self.offer_testimony(character, state)
        self.renderer.wait_for_key()

    def handle_accuse(self, character: Character, state: 'GameState') -> None:
        """Handle accusing a character."""
        cracked = character.apply_pressure(
            ACCUSE_PRESSURE_AMOUNT,
            can_crack=self.testimony.can_crack(character, state),
        )

        if state.spine and character.id == state.spine.true_resolution.culprit_id:
            # Cornered and accused, the culprit breaks — and their confession
            # is part of the case being judged, not something you have to
            # accuse them a second time to have counted
            if cracked:
                self.renderer.render_narration(
                    f"{character.name}'s composure goes all at once."
                )
                self.offer_testimony(character, state)
            evidence = set(state.memory.player.discoveries.keys())
            is_correct, explanation = state.spine.check_solution(character.id, evidence)

            if is_correct:
                self.renderer.render_narration("Your accusation hits home!")
                character.state.is_cracked = True
                self.show_dialogue(
                    character,
                    f"How did you know? Yes... {character.secret_truth}",
                    "defeated",
                )
                self.renderer.render_game_over(
                    f"You solved the case! {character.name} was responsible.\n\n"
                    f"Dominant moral shade: {state.memory.player.get_dominant_shade().value}"
                )
                state.is_running = False
            else:
                self.show_dialogue(
                    character,
                    "You think you're so clever, but you can't prove anything!",
                    "defensively",
                )
                self.renderer.render_narration(explanation)
                # Accusing the right person without evidence still costs trust
                character.modify_trust(ACCUSE_WRONG_TRUST_PENALTY // 2)
        else:
            self.show_dialogue(
                character,
                "What?! You're completely wrong! I didn't do anything!",
                "angrily",
            )
            character.modify_trust(ACCUSE_WRONG_TRUST_PENALTY)

        # Record in generation memory so LLM knows about the accusation
        state.world_state.generation_memory.record_dialogue(
            npc_id=character.id,
            player_said="[accused]",
            npc_response="denied" if state.is_running else "confessed",
            location_id=state.current_location_id,
            timestamp=state.memory.current_time,
        )

        # Record accusation in character memory
        char_memory = state.memory.get_character_memory(character.id)
        if char_memory:
            char_memory.record_player_interaction(
                timestamp=state.memory.current_time,
                interaction_type="accused",
                player_tone="aggressive",
                outcome="caught" if (not state.is_running) else "denied",
                trust_change=ACCUSE_WRONG_TRUST_PENALTY if state.is_running else 0,
            )

        # Feed into NPC intelligence
        bridge = getattr(state, 'event_bridge', None)
        if bridge:
            bridge.on_accuse(
                character.id, location=state.current_location_id
            )

        self.offer_testimony(character, state)
        self.renderer.wait_for_key()
