"""
Testimony - every NPC can carry a piece of the case.

A character's `leads` are spine revelation ids they can give up. What
they know is the revelation's `testimony` (ground truth, authored by the
scenario); the character voices it in their own words, and the truth is
what lands in the case file.

People open up in two ways:

- Rapport: asking about the things they care about (their topics) earns
  trust, once per topic. Past TESTIMONY_TRUST_THRESHOLD, a non-culprit
  tells you what they know.
- Pressure: a cracked character tells all.

The culprit never volunteers, and won't crack until the detective has
them cornered: every lead their confession rests on must already be
uncovered. Pressure without proof just makes them sweat — and a culprit
who sweats long enough runs (see npc_agency).

Testimony is recorded as evidence under the revelation's id, so it
counts toward the spine's evidence chain, and leads cascade as their
prerequisites fall into place.
"""

from typing import Optional, TYPE_CHECKING
import logging
import re

from .config import RAPPORT_TRUST_GAIN, TESTIMONY_TRUST_THRESHOLD

if TYPE_CHECKING:
    from .character import Character
    from .llm.client import LLMClient
    from .narrative import Revelation
    from .render import Renderer

logger = logging.getLogger(__name__)

# Words that don't make a topic: "the bar" is about the bar
_TOPIC_STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "to", "and", "or", "about",
    "your", "my", "his", "her", "their", "who", "what", "that", "this",
}

MAX_VOICED_LINE_LENGTH = 400


def lead_fact(revelation: 'Revelation') -> str:
    """The truth behind a lead, as someone who knows it would put it."""
    return (getattr(revelation, "testimony", "") or revelation.description).strip()


def advance_leads(state, renderer: Optional['Renderer'] = None) -> list[str]:
    """
    Uncover every lead whose evidence is in hand and whose prerequisites
    are met — repeatedly, so one lead clicking can unlock the next.

    Returns the ids uncovered this call.
    """
    spine = getattr(state, "spine", None)
    if spine is None:
        return []

    uncovered = []
    progress = True
    while progress:
        progress = False
        for revelation in list(spine.revelations):
            if revelation.id in spine.revealed_facts:
                continue
            if not state.memory.player.has_discovered(revelation.id):
                continue
            if spine.make_revelation(revelation.id):
                uncovered.append(revelation)
                progress = True

    if renderer:
        for revelation in uncovered:
            renderer.render_discovery(f"LEAD UNCOVERED: {revelation.description}")
    return [r.id for r in uncovered]


def _stem(word: str) -> str:
    return word[:5] if len(word) >= 5 else word


class Testimony:
    """Turns what NPCs know about the case into evidence."""

    def __init__(self, llm_client: Optional['LLMClient'] = None):
        self.llm_client = llm_client

    # ------------------------------------------------------------------
    # Who knows what
    # ------------------------------------------------------------------

    @staticmethod
    def is_culprit(character: 'Character', state) -> bool:
        spine = getattr(state, "spine", None)
        return bool(spine) and character.id == spine.true_resolution.culprit_id

    @staticmethod
    def pending_leads(character: 'Character', state) -> list['Revelation']:
        """Leads this character holds that the detective doesn't have yet."""
        spine = getattr(state, "spine", None)
        if not spine:
            return []
        pending = []
        for lead_id in character.leads:
            revelation = spine.get_revelation(lead_id)
            if revelation is None:
                continue
            if state.memory.player.has_discovered(lead_id):
                continue
            pending.append(revelation)
        return pending

    def case_knowledge(self, character: 'Character', state) -> list[str]:
        """What a non-culprit knows about the case, for their dialogue prompt."""
        if self.is_culprit(character, state):
            return []  # their secret already carries the truth
        return [lead_fact(r) for r in self.pending_leads(character, state)]

    def is_open(self, character: 'Character', state) -> bool:
        """Is this character ready to tell the detective what they know?"""
        if character.state.is_cracked:
            return True
        if self.is_culprit(character, state):
            return False
        return character.current_trust >= TESTIMONY_TRUST_THRESHOLD

    def can_crack(self, character: 'Character', state) -> bool:
        """
        The culprit only breaks once cornered: every prerequisite of the
        leads they hold (other than their own) is already uncovered.
        Everyone else can be broken at any time.
        """
        spine = getattr(state, "spine", None)
        if not spine or not self.is_culprit(character, state):
            return True
        own = set(character.leads)
        for lead_id in character.leads:
            revelation = spine.get_revelation(lead_id)
            if revelation is None:
                continue
            for prereq in revelation.prerequisites:
                if prereq not in own and prereq not in spine.revealed_facts:
                    return False
        return True

    # ------------------------------------------------------------------
    # Rapport
    # ------------------------------------------------------------------

    @staticmethod
    def mentions_topic(text: str, topic: str) -> bool:
        """Does the player's line touch on this topic?"""
        words = {_stem(w) for w in re.findall(r"[a-z0-9']+", text.lower())}
        topic_words = [
            w for w in re.findall(r"[a-z0-9']+", topic.lower())
            if w not in _TOPIC_STOPWORDS
        ]
        return any(_stem(w) in words for w in topic_words)

    def note_rapport(self, character: 'Character', player_input: str) -> int:
        """Asking about what they care about earns trust, once per topic."""
        gained = 0
        for topic in sorted(character.get_available_topics()):
            if self.mentions_topic(player_input, topic):
                character.exhaust_topic(topic)
                character.modify_trust(RAPPORT_TRUST_GAIN)
                gained += RAPPORT_TRUST_GAIN
        return gained

    # ------------------------------------------------------------------
    # Giving testimony
    # ------------------------------------------------------------------

    def offer(self, character: 'Character', state, renderer: 'Renderer', speak) -> list[str]:
        """
        If they're ready to talk, they tell you what they know.

        `speak(character, line)` shows a line of dialogue. Returns the lead
        ids given.
        """
        if not getattr(state, "is_running", True):
            return []
        if not self.is_open(character, state):
            return []
        pending = self.pending_leads(character, state)
        if not pending:
            return []

        culprit = self.is_culprit(character, state)
        if not culprit:
            renderer.render_narration(
                f"{character.name} glances around, then lowers their voice."
            )

        given = []
        for revelation in pending:
            fact = lead_fact(revelation)
            # A cracked culprit has just confessed in their own words
            if not culprit:
                speak(character, self.voice(character, fact, state))
            state.memory.player_discovers(
                fact_id=revelation.id,
                description=fact,
                location=state.current_location_id,
                source=f"{character.name}'s {'confession' if culprit else 'testimony'}",
                is_evidence=True,
                related_to=[character.id],
            )
            renderer.render_discovery(
                f"{'CONFESSION' if culprit else 'TESTIMONY'}: {fact}"
            )
            given.append(revelation.id)

            state.world_state.generation_memory.record_dialogue(
                npc_id=character.id,
                player_said="[testimony]",
                npc_response=fact,
                location_id=state.current_location_id,
                revealed=fact,
                timestamp=state.memory.current_time,
            )

        char_memory = state.memory.get_character_memory(character.id)
        if char_memory:
            char_memory.record_player_interaction(
                timestamp=state.memory.current_time,
                interaction_type="testified",
                player_tone="neutral",
                outcome="told_what_they_know",
                trust_change=0,
                topic=lead_fact(pending[0])[:50],
            )

        advance_leads(state, renderer)
        return given

    def voice(self, character: 'Character', fact: str, state) -> str:
        """
        The character says it in their own words. The facts must survive
        the voicing — if the LLM drops a name, the plain truth is used.
        """
        if self.llm_client is None:
            return fact
        try:
            response = self.llm_client.chat([
                {
                    "role": "system",
                    "content": (
                        f"You are {character.name}: {character.description}\n"
                        "You've decided to tell the detective what you know "
                        "about the case — maybe you saw it, maybe you heard "
                        "it around. Say it in one or two sentences of noir "
                        "dialogue, in your own voice. Keep every name and "
                        "fact; add nothing new. Respond with only the spoken "
                        "line, no quotes."
                    ),
                },
                {"role": "user", "content": f"What you know: {fact}"},
            ])
        except Exception as e:  # a voicing failure must never lose the lead
            logger.warning("Testimony voicing failed: %s", e)
            return fact

        if not (response.success and response.text):
            return fact
        line = response.text.strip().strip('"').strip()
        if not line or len(line) > MAX_VOICED_LINE_LENGTH:
            return fact
        for name in self._names_in(fact, state):
            if name.lower() not in line.lower():
                return fact
        return line

    @staticmethod
    def _names_in(fact: str, state) -> list[str]:
        """Surnames of cast members a fact mentions."""
        names = []
        lower = fact.lower()
        for other in getattr(state, "characters", {}).values():
            surname = other.name.split()[-1] if other.name.split() else ""
            if len(surname) >= 3 and surname.lower() in lower:
                names.append(surname)
        return names

    # ------------------------------------------------------------------
    # Weaving newcomers into the case
    # ------------------------------------------------------------------

    @staticmethod
    def weave_bystander(character: 'Character', state) -> Optional[str]:
        """
        Give a newcomer a piece of the case, so every NPC the city
        produces can matter. They get an outstanding lead that a witness
        (not the culprit) could know — the one with the fewest holders,
        so the knowledge spreads across the cast.

        Returns the lead id assigned, if any.
        """
        spine = getattr(state, "spine", None)
        if not spine or character.leads:
            return None
        culprit_id = spine.true_resolution.culprit_id
        if character.id == culprit_id:
            return None

        holders: dict[str, int] = {}
        for other in state.characters.values():
            if other.id in (culprit_id, character.id):
                continue
            for lead_id in other.leads:
                holders[lead_id] = holders.get(lead_id, 0) + 1

        candidates = [
            r for r in spine.revelations
            if r.id in holders
            and r.id not in spine.revealed_facts
            and not state.memory.player.has_discovered(r.id)
        ]
        if not candidates:
            return None

        chosen = min(candidates, key=lambda r: holders[r.id])
        character.add_lead(chosen.id)
        logger.info("Wove %s into the case with lead %s", character.id, chosen.id)
        return chosen.id
