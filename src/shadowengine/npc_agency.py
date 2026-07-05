"""
NPCAgency - NPCs act on their own behalf.

Two behaviors that make the cast feel alive rather than waiting:

- The culprit protects themselves. As interrogation heat builds they
  relocate to avoid you; push them close to breaking and they try to
  leave town on a countdown. If they make it out, the case goes cold —
  a losing ending. Crack them or accuse them (with evidence) first.

- The framed defend themselves. When the player has found planted
  evidence pointing at an innocent, word reaches them; the next time
  you share a room they come to you, scared, with their alibi — which
  is itself evidence that someone staged the scene.
"""

from typing import Optional, TYPE_CHECKING
import logging
import random

from .config import (
    CULPRIT_NERVOUS_HEAT_FRACTION,
    CULPRIT_RELOCATE_HEAT_FRACTION,
    CULPRIT_FLEE_HEAT_FRACTION,
    CULPRIT_FLEE_COUNTDOWN_UNITS,
    CULPRIT_RELOCATE_COOLDOWN_UNITS,
    FRAMED_DEFENSE_DELAY_UNITS,
)
from .character import Mood
from .interaction import Hotspot, HotspotType
from .memory import EventType

if TYPE_CHECKING:
    from .llm.client import LLMClient
    from .render import Renderer

logger = logging.getLogger(__name__)


class NPCAgency:
    """Self-interested moves by the cast, ticked once per exploration turn."""

    def __init__(self, llm_client: 'LLMClient', rng: Optional[random.Random] = None):
        self.llm_client = llm_client
        self.rng = rng or random.Random()

        # Culprit state
        self.flee_deadline: Optional[int] = None
        self.flee_warned: bool = False
        self.culprit_fled: bool = False
        self._last_relocate_time: int = -CULPRIT_RELOCATE_COOLDOWN_UNITS

        # Framed-defense state
        self._defended: set[str] = set()

    def seed(self, seed: Optional[int]) -> None:
        if seed is not None:
            self.rng = random.Random(seed)

    def to_dict(self) -> dict:
        return {
            "flee_deadline": self.flee_deadline,
            "flee_warned": self.flee_warned,
            "culprit_fled": self.culprit_fled,
            "last_relocate_time": self._last_relocate_time,
            "defended": sorted(self._defended),
        }

    def restore(self, data: Optional[dict]) -> None:
        if not data:
            return
        self.flee_deadline = data.get("flee_deadline")
        self.flee_warned = data.get("flee_warned", False)
        self.culprit_fled = data.get("culprit_fled", False)
        self._last_relocate_time = data.get(
            "last_relocate_time", -CULPRIT_RELOCATE_COOLDOWN_UNITS
        )
        self._defended = set(data.get("defended", []))

    def update(self, state, renderer: 'Renderer') -> None:
        if not state.spine or not state.is_running:
            return
        self._framed_defense(state, renderer)
        if state.is_running:
            self._culprit_self_preservation(state, renderer)

    # ------------------------------------------------------------------
    # Culprit self-preservation
    # ------------------------------------------------------------------

    @staticmethod
    def culprit_heat(culprit) -> float:
        """Interrogation heat: pressure plus a nerve penalty."""
        heat = float(culprit.state.pressure_accumulated)
        if culprit.state.mood == Mood.NERVOUS:
            heat += CULPRIT_NERVOUS_HEAT_FRACTION * culprit.trust_threshold
        return heat

    def _culprit_self_preservation(self, state, renderer: 'Renderer') -> None:
        culprit_id = state.spine.true_resolution.culprit_id
        culprit = state.characters.get(culprit_id)
        if culprit is None or self.culprit_fled:
            return
        # A cracked suspect is done running
        if culprit.state.is_cracked or state.spine.is_solved:
            return

        now = state.memory.current_time
        heat = self.culprit_heat(culprit)
        threshold = max(culprit.trust_threshold, 1)

        # Escape attempt already underway
        if self.flee_deadline is not None:
            remaining = self.flee_deadline - now
            if remaining <= 0:
                self._culprit_escapes(culprit, state, renderer)
            elif not self.flee_warned and remaining <= CULPRIT_FLEE_COUNTDOWN_UNITS // 2:
                self.flee_warned = True
                renderer.render_narration(
                    f"A newsboy hollers the evening edition. Somewhere across "
                    f"town, {culprit.name} is settling accounts. Not much "
                    "time left."
                )
            return

        # Heat crosses the breaking point: they start packing
        if heat >= CULPRIT_FLEE_HEAT_FRACTION * threshold:
            self.flee_deadline = now + CULPRIT_FLEE_COUNTDOWN_UNITS
            renderer.render_narration(
                f"Word hits the street like a dropped glass: {culprit.name} "
                "is making moves to leave town. If they slip away, the case "
                "goes with them."
            )
            state.memory.record_witnessed_event(
                event_type=EventType.MOVEMENT,
                description=f"{culprit_id} began preparing to flee the city",
                location=culprit.state.location or "unknown",
                actors=[culprit_id],
                witnesses=[culprit_id],
                player_witnessed=False,
            )
            return

        # Moderate heat: avoid the detective, change haunts
        if (
            heat >= CULPRIT_RELOCATE_HEAT_FRACTION * threshold
            and now - self._last_relocate_time >= CULPRIT_RELOCATE_COOLDOWN_UNITS
        ):
            self._relocate_culprit(culprit, state, renderer)
            self._last_relocate_time = now

    def _relocate_culprit(self, culprit, state, renderer: 'Renderer') -> None:
        """Move the culprit's presence to a location away from the player."""
        source = None
        source_hotspot = None
        for loc_id, location in state.locations.items():
            for hs in location.hotspots:
                if (
                    hs.hotspot_type == HotspotType.PERSON
                    and hs.target_id == culprit.id
                    and hs.active
                ):
                    source, source_hotspot = loc_id, hs
                    break
            if source_hotspot:
                break
        if source_hotspot is None:
            return

        destinations = sorted(
            loc_id for loc_id in state.locations
            if loc_id not in (source, state.current_location_id)
        )
        if not destinations:
            return
        destination = self.rng.choice(destinations)

        # If the player is watching, the exit is visible
        if state.current_location_id == source:
            renderer.render_narration(
                f"{culprit.name} checks a watch that doesn't need checking, "
                "mutters an excuse, and slips out."
            )

        source_hotspot.deactivate()
        source_hotspot.hide()

        state.locations[destination].add_hotspot(Hotspot.create_person(
            id=f"hs_{culprit.id}_moved_{state.memory.current_time}",
            name=source_hotspot.label,
            position=(30, 10),
            character_id=culprit.id,
            description=f"{culprit.name} — keeping a lower profile than before.",
        ))
        culprit.state.location = destination

        state.memory.record_witnessed_event(
            event_type=EventType.MOVEMENT,
            description=f"{culprit.id} moved from {source} to {destination}, avoiding the detective",
            location=destination,
            actors=[culprit.id],
            witnesses=[culprit.id],
            player_witnessed=(state.current_location_id == source),
        )
        bridge = getattr(state, 'event_bridge', None)
        if bridge:
            bridge.bridge_event(
                event_type="movement",
                description=f"{culprit.name} has been avoiding their usual spots",
                location=destination,
                actors=[culprit.id],
                witnesses=[culprit.id],
            )
        logger.info("Culprit relocated: %s -> %s", source, destination)

    def _culprit_escapes(self, culprit, state, renderer: 'Renderer') -> None:
        """The countdown ran out: the case goes cold."""
        self.culprit_fled = True
        for location in state.locations.values():
            for hs in location.hotspots:
                if hs.hotspot_type == HotspotType.PERSON and hs.target_id == culprit.id:
                    hs.deactivate()
                    hs.hide()
        culprit.state.is_available = False

        state.memory.record_witnessed_event(
            event_type=EventType.MOVEMENT,
            description=f"{culprit.id} fled the city before being caught",
            location="unknown",
            actors=[culprit.id],
            witnesses=[culprit.id],
            player_witnessed=False,
        )

        renderer.render_narration(
            f"The morning papers say a private car left the city before "
            f"dawn. No name on the manifest, but you know. {culprit.name} "
            "is gone, and the truth went with them."
        )
        renderer.render_game_over(
            f"THE TRAIL WENT COLD.\n\n"
            f"{culprit.name} slipped away before you could close the case. "
            "You pushed hard enough to spook them — but not fast enough "
            "to stop them.\n\n"
            f"Dominant moral shade: {state.memory.player.get_dominant_shade().value}"
        )
        state.is_running = False

    # ------------------------------------------------------------------
    # The framed defend themselves
    # ------------------------------------------------------------------

    def _framed_defense(self, state, renderer: 'Renderer') -> None:
        now = state.memory.current_time
        location = state.locations.get(state.current_location_id)
        if not location:
            return

        for framed_id, frame_time, plant_label in self._known_frames(state):
            if framed_id in self._defended:
                continue
            if now - frame_time < FRAMED_DEFENSE_DELAY_UNITS:
                continue

            framed = state.characters.get(framed_id)
            if framed is None:
                continue
            present = any(
                hs.hotspot_type == HotspotType.PERSON
                and hs.target_id == framed_id
                and hs.active
                for hs in location.hotspots
            )
            if not present:
                continue

            self._defended.add(framed_id)
            self._deliver_defense(framed, plant_label, state, renderer)
            return  # one approach per tick

    @staticmethod
    def _known_frames(state) -> list[tuple[str, int, str]]:
        """(framed_id, discovery_time, plant_label) for frame facts the player found."""
        frames = []
        planted_by_fact: dict[str, tuple[str, str]] = {}
        for location in state.locations.values():
            for hs in location.hotspots:
                if hs.planted_by and hs.frames and hs.reveals_fact:
                    planted_by_fact[hs.reveals_fact] = (hs.frames, hs.label)

        for discovery in state.memory.player.discoveries.values():
            if discovery.fact_id in planted_by_fact:
                framed_id, label = planted_by_fact[discovery.fact_id]
                frames.append((framed_id, discovery.timestamp, label))
        return frames

    def _deliver_defense(self, framed, plant_label: str, state, renderer: 'Renderer') -> None:
        renderer.render_narration(
            f"{framed.name} crosses the room to you, voice low and urgent."
        )
        line = self._defense_line(framed, plant_label)
        renderer.render_narration(f'"{line}"')

        alibi_fact = f"alibi_{framed.id}"
        if not state.memory.player.has_discovered(alibi_fact):
            state.memory.player_discovers(
                fact_id=alibi_fact,
                description=(
                    f"{framed.name} came to you unprompted, scared: they can "
                    f"account for their whereabouts, and they say the "
                    f"{plant_label.lower()} isn't theirs. If that's true, "
                    "someone staged it — and staging takes a guilty reason."
                ),
                location=state.current_location_id,
                source=f"{framed.name}'s own defense",
                is_evidence=True,
                related_to=[framed.id],
            )
            renderer.render_discovery(
                f"{framed.name} has an alibi — and somebody wanted you "
                "to think they didn't."
            )

        # Their fear is on the record
        char_memory = state.memory.get_character_memory(framed.id)
        if char_memory:
            char_memory.record_player_interaction(
                timestamp=state.memory.current_time,
                interaction_type="pleaded_innocence",
                player_tone="neutral",
                outcome="gave_alibi",
                trust_change=5,
            )

    def _defense_line(self, framed, plant_label: str) -> str:
        response = self.llm_client.chat([
            {
                "role": "system",
                "content": (
                    f"You are {framed.name}: {framed.description}\n"
                    "You just learned evidence was planted to frame you for "
                    "a murder you didn't commit. In ONE line (under 30 words), "
                    "scared but sincere, tell the detective it isn't yours and "
                    "offer your alibi. Respond with only the spoken line, "
                    "no quotes."
                ),
            },
            {
                "role": "user",
                "content": f"The planted object: {plant_label}",
            },
        ])
        if response.success and response.text:
            line = response.text.strip().strip('"').strip()
            if line:
                return line[:200]
        return (
            f"That {plant_label.lower()} isn't mine, I swear it. Check my "
            "whereabouts that night — I can prove where I was. Someone's "
            "setting me up."
        )
