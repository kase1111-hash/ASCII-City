"""
SaveSystem - Full snapshot of an evolved world.

The whole point of a naturally evolving detective game is that the world
accumulates history: LLM-generated detail layers, spawned and planted
hotspots, rumors in flight, a culprit mid-escape. A save that only kept
the memory bank would forget all of it.

Save format v3: a checksummed envelope containing every stateful
subsystem. Legacy v1/v2 saves (memory bank only) still load.

Known limitation: behavioral circuits attached to hotspots are not
serialized (only the scripted Dockside Job scenario uses them).
"""

from typing import Optional, TYPE_CHECKING
import hashlib
import hmac
import json
import logging
import os

from .memory import MemoryBank
from .memory.memory_bank import _SAVE_INTEGRITY_KEY
from .render import Location
from .character import Character
from .narrative import NarrativeSpine
from .world_state import WorldState
from .environment import Environment
from .npc_intelligence import PropagationEngine
from .event_bridge import GameEventBridge

if TYPE_CHECKING:
    from .game import Game

logger = logging.getLogger(__name__)

SAVE_VERSION = 3


class SaveSystem:
    """Serializes and restores the complete game state."""

    def __init__(self, game: 'Game'):
        self.game = game

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, filepath: str) -> None:
        """Write a full v3 snapshot."""
        game = self.game
        state = game.state

        data = {
            "memory": state.memory.to_dict(),
            "inventory": list(state.inventory),
            "current_location_id": state.current_location_id,
            "locations": [loc.to_dict() for loc in state.locations.values()],
            "characters": [c.to_dict() for c in state.characters.values()],
            "spine": state.spine.to_dict() if state.spine else None,
            "world_state": state.world_state.to_dict(),
            "environment": state.environment.to_dict(),
            "propagation": state.propagation_engine.to_dict(),
            "evidence_watch": state.evidence_watch.to_dict(),
            "inspection": game.inspection_manager.to_dict(),
            "npc_agency": game.npc_agency.to_dict(),
            "street_talk": game.street_talk.to_dict(),
        }

        envelope = {
            "version": SAVE_VERSION,
            "checksum": self._checksum(data),
            "data": data,
        }

        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(envelope, f, indent=2)
        logger.info("Saved full game state to %s", filepath)

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load(self, filepath: str) -> None:
        """Restore a snapshot; raises on missing/corrupt files."""
        with open(filepath, "r") as f:
            raw = json.load(f)

        if not isinstance(raw, dict):
            raise ValueError("Invalid save file: not a JSON object")

        version = raw.get("version", 1)
        if version < SAVE_VERSION:
            # Legacy memory-only save: keep old behavior
            logger.info("Loading legacy (v%s) memory-only save", version)
            self.game.state.memory = MemoryBank.load(filepath)
            return

        data = raw.get("data")
        expected = raw.get("checksum", "")
        if not isinstance(data, dict):
            raise ValueError("Invalid save file: missing data section")
        if not hmac.compare_digest(expected, self._checksum(data)):
            raise ValueError("Save file integrity check failed: checksum mismatch")

        self._restore(data)

    def _restore(self, data: dict) -> None:
        from .game import GameState

        game = self.game
        state = GameState()

        state.memory = MemoryBank.from_dict(data["memory"])
        state.inventory = [str(i) for i in data.get("inventory", [])]
        state.current_location_id = data.get("current_location_id", "")

        state.locations = {}
        for loc_data in data.get("locations", []):
            location = Location.from_dict(loc_data)
            state.locations[location.id] = location

        state.characters = {}
        for char_data in data.get("characters", []):
            character = Character.from_dict(char_data)
            state.characters[character.id] = character

        if data.get("spine"):
            state.spine = NarrativeSpine.from_dict(data["spine"])
        if data.get("world_state"):
            state.world_state = WorldState.from_dict(data["world_state"])
        if data.get("environment"):
            state.environment = Environment.from_dict(data["environment"])
        if data.get("propagation"):
            state.propagation_engine = PropagationEngine.from_dict(
                data["propagation"]
            )
        state.event_bridge = GameEventBridge(state.propagation_engine)

        state.evidence_watch.restore(data.get("evidence_watch"))
        state.evidence_watch.seed(state.memory.game_seed)

        # Swap in the restored state, then rebuild the delegates that hold
        # references to it (dialogue, locations, inspection, agency...)
        game.state = state
        game.rebuild_delegates(seed=state.memory.game_seed)

        # Restore subsystem internals AFTER the rebuild created fresh ones
        game.inspection_manager.restore(data.get("inspection"))
        game.npc_agency.restore(data.get("npc_agency"))
        game.street_talk.restore(data.get("street_talk"))

        logger.info(
            "Restored game state: %d locations, %d characters, %d discoveries",
            len(state.locations), len(state.characters),
            len(state.memory.player.discoveries),
        )

    @staticmethod
    def _checksum(data: dict) -> str:
        payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hmac.new(_SAVE_INTEGRITY_KEY, payload, hashlib.sha256).hexdigest()
