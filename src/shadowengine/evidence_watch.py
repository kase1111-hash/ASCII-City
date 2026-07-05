"""
EvidenceWatch - The world reacts to what the player finds.

When the player uncovers physical evidence in front of witnesses, word
travels. If the evidence is left uncollected too long, the culprit gets
to it first: the object disappears, the act is recorded as world truth
(the world memory knows who did it, even if the player never learns),
and the player finds only the absence — which is itself a clue.

Counterplay: collect evidence immediately, or inspect when no one is
watching.
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
import logging

from .config import EVIDENCE_TAMPER_DELAY_UNITS
from .memory import EventType

if TYPE_CHECKING:
    from .render import Renderer

logger = logging.getLogger(__name__)


@dataclass
class EvidenceThreat:
    """A piece of witnessed, uncollected evidence the culprit may reach."""
    hotspot_id: str
    location_id: str
    label: str
    fact_id: str
    witnesses: list[str] = field(default_factory=list)
    created_time: int = 0
    destroyed: bool = False     # Tampered with; player hasn't seen it yet

    @property
    def destroy_time(self) -> int:
        return self.created_time + EVIDENCE_TAMPER_DELAY_UNITS


class EvidenceWatch:
    """Tracks witnessed evidence and lets the culprit clean up after you."""

    def __init__(self):
        self.threats: list[EvidenceThreat] = []

    def register(
        self,
        hotspot_id: str,
        location_id: str,
        label: str,
        fact_id: str,
        witnesses: list[str],
        created_time: int,
    ) -> None:
        """Register newly found evidence that was seen being found."""
        if any(t.hotspot_id == hotspot_id for t in self.threats):
            return
        self.threats.append(EvidenceThreat(
            hotspot_id=hotspot_id,
            location_id=location_id,
            label=label,
            fact_id=fact_id,
            witnesses=list(witnesses),
            created_time=created_time,
        ))
        logger.info(
            "Evidence threat registered: %s at %s (witnessed by %s)",
            label, location_id, ", ".join(witnesses),
        )

    def update(self, state, renderer: 'Renderer') -> None:
        """
        Advance the world's counter-move. Called once per exploration tick.

        - Word of a witnessed find reaches the culprit; once the delay
          passes and the player isn't standing guard, the evidence goes.
        - When the player next visits, they find it missing.
        """
        spine = state.spine
        if spine is None:
            self.threats.clear()
            return

        culprit_id = spine.true_resolution.culprit_id
        now = state.memory.current_time
        here = state.current_location_id

        for threat in list(self.threats):
            location = state.locations.get(threat.location_id)
            hotspot = None
            if location:
                hotspot = next(
                    (h for h in location.hotspots if h.id == threat.hotspot_id),
                    None,
                )

            # Collected or gone for other reasons — threat over
            if not threat.destroyed and (hotspot is None or not hotspot.active):
                self.threats.remove(threat)
                continue

            # Culprit acts: delay elapsed and the player isn't there
            if (
                not threat.destroyed
                and now >= threat.destroy_time
                and here != threat.location_id
            ):
                hotspot.deactivate()
                hotspot.hide()
                threat.destroyed = True

                # World truth: this really happened, whether or not the
                # player ever pieces it together
                state.memory.record_witnessed_event(
                    event_type=EventType.DISCOVERY,
                    description=(
                        f"{culprit_id} removed the {threat.label} "
                        f"before the detective could collect it"
                    ),
                    location=threat.location_id,
                    actors=[culprit_id],
                    witnesses=[culprit_id],
                    player_witnessed=False,
                )
                bridge = getattr(state, 'event_bridge', None)
                if bridge:
                    bridge.bridge_event(
                        event_type="discovery",
                        description=f"The {threat.label} disappeared from {threat.location_id}",
                        location=threat.location_id,
                        actors=[culprit_id],
                        witnesses=[culprit_id],
                    )
                logger.info("Evidence tampered: %s at %s", threat.label, threat.location_id)
                continue

            # Player returns to find the evidence gone
            if threat.destroyed and here == threat.location_id:
                renderer.render_narration(
                    f"Something's off. The {threat.label} is gone — someone "
                    "got here before you. They knew you'd found it."
                )
                state.memory.player_discovers(
                    fact_id=f"tampered_{threat.fact_id}"[:64],
                    description=(
                        f"The {threat.label} vanished before you could collect "
                        "it. Whoever took it knew what you'd found — and had "
                        "a reason to bury it."
                    ),
                    location=threat.location_id,
                    source="returned to the scene",
                    is_evidence=True,
                )
                renderer.render_discovery(
                    f"The {threat.label} was taken. Someone is covering their tracks."
                )
                self.threats.remove(threat)

                # Tampering is evidence too — it can crack a lead
                from .inspection_manager import check_location_leads
                check_location_leads(state, renderer)

    def pending_at(self, location_id: str) -> list[EvidenceThreat]:
        """Active (not yet destroyed) threats at a location."""
        return [
            t for t in self.threats
            if t.location_id == location_id and not t.destroyed
        ]
