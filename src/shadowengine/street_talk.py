"""
StreetTalk - NPCs voice what the rumor network knows.

The propagation engine already carries rumors and subjective memories of
the player's investigation (witnessed scrutiny, vanished evidence,
threats, gossip). This makes that knowledge audible: when the player
walks into a room, someone who has heard something may say so —
unprompted, once, in their own voice.

The world evolving stops being invisible bookkeeping and becomes a line
someone mutters as you pass.
"""

from typing import Optional, TYPE_CHECKING
import logging

from .interaction import HotspotType

if TYPE_CHECKING:
    from .llm.client import LLMClient
    from .render import Renderer

logger = logging.getLogger(__name__)

# Minimum time units between unprompted remarks — the street doesn't babble
REMARK_COOLDOWN_UNITS = 4

# Only knowledge that concerns the investigation gets voiced
_INVESTIGATION_MARKERS = (
    "player", "detective", "scrutin", "disappear", "removed", "examined",
    "found evidence", "threatened", "accused", "took",
)


class StreetTalk:
    """Turns rumor-network knowledge into unprompted NPC remarks."""

    def __init__(self, llm_client: 'LLMClient'):
        self.llm_client = llm_client
        self._voiced: set[tuple[str, str]] = set()
        self._last_remark_time: int = -REMARK_COOLDOWN_UNITS

    def to_dict(self) -> dict:
        return {
            "voiced": [list(pair) for pair in sorted(self._voiced)],
            "last_remark_time": self._last_remark_time,
        }

    def restore(self, data) -> None:
        if not data:
            return
        self._voiced = {tuple(pair) for pair in data.get("voiced", [])}
        self._last_remark_time = data.get(
            "last_remark_time", -REMARK_COOLDOWN_UNITS
        )

    def update(self, state, renderer: 'Renderer') -> None:
        """Called once per exploration tick; at most one remark fires."""
        engine = getattr(state, 'propagation_engine', None)
        if engine is None:
            return

        now = state.memory.current_time
        if now - self._last_remark_time < REMARK_COOLDOWN_UNITS:
            return

        location = state.locations.get(state.current_location_id)
        if not location:
            return

        for hotspot in location.hotspots:
            if (
                hotspot.hotspot_type != HotspotType.PERSON
                or not hotspot.target_id
                or hotspot.target_id not in state.characters
                or not hotspot.active
            ):
                continue

            npc_id = hotspot.target_id
            knowledge = self._investigation_knowledge(engine, npc_id)
            for key, text in knowledge:
                if (npc_id, key) in self._voiced:
                    continue
                self._voiced.add((npc_id, key))
                self._last_remark_time = now
                self._deliver_remark(
                    state.characters[npc_id], text, renderer,
                )
                return  # one remark per tick, then the street goes quiet

    @staticmethod
    def _investigation_knowledge(engine, npc_id: str) -> list[tuple[str, str]]:
        """What this NPC knows about the player's investigation."""
        found: list[tuple[str, str]] = []

        npc_state = engine.get_npc_state(npc_id)
        if npc_state:
            for memory in npc_state.memory_bank.get_shareable_memories():
                summary = memory.summary or ""
                if any(m in summary.lower() for m in _INVESTIGATION_MARKERS):
                    found.append((f"mem:{summary[:48]}", summary))

        for rumor in engine.rumor_propagation.get_rumors_known_by(npc_id):
            claim = rumor.core_claim or ""
            if any(m in claim.lower() for m in _INVESTIGATION_MARKERS):
                found.append((f"rumor:{claim[:48]}", claim))

        return found

    def _deliver_remark(self, character, knowledge: str, renderer: 'Renderer') -> None:
        """One unprompted line, in the NPC's voice."""
        line = self._generate_line(character, knowledge)
        renderer.render_narration(f'{character.name} catches your eye. "{line}"')

    def _generate_line(self, character, knowledge: str) -> str:
        response = self.llm_client.chat([
            {
                "role": "system",
                "content": (
                    f"You are {character.name}: {character.description}\n"
                    "In ONE short line of noir dialogue (under 25 words), "
                    "needle the detective about something you heard. Don't "
                    "state it flatly — imply, warn, or tease. Respond with "
                    "only the spoken line, no quotes."
                ),
            },
            {
                "role": "user",
                "content": f"What you heard: {knowledge}",
            },
        ])

        if response.success and response.text:
            line = response.text.strip().strip('"').strip()
            if line:
                return line[:160]

        # Offline: a serviceable murmur built from the knowledge itself
        gist = knowledge.strip().rstrip(".")
        gist = gist.replace("Player", "you").replace("player", "you")
        return f"Word travels, detective. They say {gist[:1].lower()}{gist[1:]}."
