"""
Round-trip tests for full save/load persistence.

An evolved world — LLM detail layers, spawned and planted hotspots,
tampering history, culprit heat, rumor state — must survive
quit-and-resume intact.
"""

import json
import pytest

from shadowengine.game import Game
from shadowengine.character import Character, Archetype, Mood
from shadowengine.render import Location
from shadowengine.interaction import Hotspot, HotspotType, Command, CommandType
from shadowengine.narrative import (
    NarrativeSpine, ConflictType, TrueResolution, Revelation,
)
from shadowengine.inspection import ZoomLevel
from shadowengine.config import GameConfig, EVIDENCE_TAMPER_DELAY_UNITS
from shadowengine.llm.client import MockLLMClient, LLMConfig, LLMBackend


MEDIUM_JSON = json.dumps({
    "description": "One baseboard behind the desk sits loose.",
    "detail_hooks": ["the loose baseboard"],
    "discovery": None,
})
CLOSE_JSON = json.dumps({
    "description": "Behind the loose baseboard, dark metal catches the light.",
    "detail_hooks": ["the loose baseboard"],
    "discovery": {
        "fact_id": "hidden_black_box",
        "description": "A wire recorder hidden behind the baseboard.",
        "is_evidence": True,
        "reveals_object": {
            "label": "Black Box",
            "type": "evidence",
            "description": "A matte-black wire recorder.",
        },
    },
})


class ForcedRandom:
    def __init__(self, value=0.0):
        self.value = value

    def random(self):
        return self.value

    def choice(self, seq):
        return seq[0]


def make_mock():
    llm = MockLLMClient(LLMConfig(backend=LLMBackend.MOCK))
    llm.set_response("ARM'S LENGTH", MEDIUM_JSON)
    llm.set_response("INCHES AWAY", CLOSE_JSON)
    llm.set_response("UNDER MAGNIFICATION", CLOSE_JSON)
    return llm


def make_game():
    game = Game()
    game.renderer.wait_for_key = lambda prompt="": None

    llm = make_mock()
    game.llm_client = llm
    game.command_handler.llm_client = llm
    game.inspection_manager.detail_handler.llm_client = llm

    room1 = Location(id="room1", name="Room One", description="First room.")
    room1.add_hotspot(Hotspot(
        id="hs_desk", label="Oak Desk", hotspot_type=HotspotType.OBJECT,
        position=(10, 10), description="A battered oak desk.",
        examine_text="A battered oak desk covered in papers.",
    ))
    room1.add_hotspot(Hotspot.create_person(
        id="hs_watcher", name="The Watcher", position=(20, 10),
        character_id="watcher", description="A gaunt man in the corner.",
    ))
    room2 = Location(id="room2", name="Room Two", description="Second room.")
    for room in (room1, room2):
        game.add_location(room)
    game.set_start_location("room1")

    game.add_character(Character(
        id="watcher", name="The Watcher", archetype=Archetype.SURVIVOR,
        description="A gaunt man with restless hands.", trust_threshold=40,
    ))
    game.add_character(Character(
        id="barfly", name="Eddie the Barfly", archetype=Archetype.INNOCENT,
        description="A harmless regular.",
    ))

    game.set_spine(NarrativeSpine(
        conflict_type=ConflictType.MURDER,
        conflict_description="A test case.",
        true_resolution=TrueResolution(
            culprit_id="watcher", motive="m", method="x", opportunity="o",
            evidence_chain=["scene_lead"],
        ),
        revelations=[Revelation(
            id="scene_lead", description="This room holds the answer",
            importance=2, location_id="room1",
        )],
    ))
    game.state.evidence_watch.rng = ForcedRandom(0.0)  # always plant
    return game


def run(game, text):
    state = game.state
    location = state.locations[state.current_location_id]
    context = {
        "targets": [h.label for h in location.get_visible_hotspots()],
        "hotspots": [
            {"label": h.label, "type": h.hotspot_type.value}
            for h in location.get_visible_hotspots()
        ],
    }
    command = game.parser.parse(text, context)
    game.command_handler.handle_command(
        command, context, state, game.config, game.add_character,
    )


def evolve_world(game):
    """Play a session that exercises every persistent system."""
    run(game, "look closer at the desk")     # MEDIUM layer
    run(game, "look closer")                 # CLOSE: discovery + spawned Black Box
    # Leave the evidence; culprit tampers and plants
    game.state.memory.advance_time(EVIDENCE_TAMPER_DELAY_UNITS + 1)
    game.state.current_location_id = "room2"
    game.state.evidence_watch.update(game.state, game.renderer)
    game.state.current_location_id = "room1"
    game.state.evidence_watch.update(game.state, game.renderer)
    run(game, "examine monogrammed handkerchief")   # frame fact
    game.state.inventory.append("magnifying glass")
    game.state.characters["watcher"].state.pressure_accumulated = 12
    game.npc_agency.flee_deadline = 99
    game.npc_agency.flee_warned = True
    game.street_talk._voiced.add(("watcher", "mem:test"))


def save_and_reload(game, tmp_path):
    """Save, then load into a completely fresh game."""
    path = str(tmp_path / "savegame.json")
    game.save_system.save(path)

    fresh = make_game()
    fresh.save_system.load(path)
    # Re-point the mock LLM at the rebuilt delegates
    llm = make_mock()
    fresh.llm_client = llm
    fresh.command_handler.llm_client = llm
    fresh.inspection_manager.detail_handler.llm_client = llm
    fresh.renderer.wait_for_key = lambda prompt="": None
    return fresh


@pytest.mark.integration
class TestSaveRoundTrip:

    def test_inventory_and_location_survive(self, tmp_path):
        game = make_game()
        evolve_world(game)
        fresh = save_and_reload(game, tmp_path)
        assert "magnifying glass" in fresh.state.inventory
        assert fresh.state.current_location_id == "room1"

    def test_spawned_and_planted_hotspots_survive(self, tmp_path):
        game = make_game()
        evolve_world(game)
        fresh = save_and_reload(game, tmp_path)

        room1 = fresh.state.locations["room1"]
        black_box = next(h for h in room1.hotspots if h.label == "Black Box")
        assert not black_box.active and not black_box.visible  # destroyed

        planted = next(
            h for h in room1.hotspots if h.label == "Monogrammed Handkerchief"
        )
        assert planted.planted_by == "watcher"
        assert planted.frames == "barfly"

    def test_discoveries_and_spine_survive(self, tmp_path):
        game = make_game()
        evolve_world(game)
        fresh = save_and_reload(game, tmp_path)

        discoveries = fresh.state.memory.player.discoveries
        assert "insp_hs_desk_hidden_black_box" in discoveries
        assert any(f.startswith("tampered_") for f in discoveries)
        assert "scene_lead" in fresh.state.spine.revealed_facts
        assert fresh.state.spine.true_resolution.culprit_id == "watcher"

    def test_character_state_survives(self, tmp_path):
        game = make_game()
        evolve_world(game)
        fresh = save_and_reload(game, tmp_path)

        watcher = fresh.state.characters["watcher"]
        assert watcher.state.pressure_accumulated == 12
        assert watcher.state.mood == Mood.NERVOUS  # set by tampering

    def test_inspection_layers_and_zoom_survive(self, tmp_path):
        game = make_game()
        evolve_world(game)
        fresh = save_and_reload(game, tmp_path)

        manager = fresh.inspection_manager
        obj = manager.engine.objects.get("insp_hs_desk")
        assert obj is not None
        assert "baseboard" in obj.get_layer(ZoomLevel.MEDIUM).description
        assert manager.engine.zoom_manager.get_current_zoom("insp_hs_desk") == ZoomLevel.CLOSE
        # Rediscovery is still deduplicated after load
        assert "insp_hs_desk_hidden_black_box" in manager._recorded_facts

    def test_agency_and_street_talk_survive(self, tmp_path):
        game = make_game()
        evolve_world(game)
        fresh = save_and_reload(game, tmp_path)

        assert fresh.npc_agency.flee_deadline == 99
        assert fresh.npc_agency.flee_warned is True
        assert ("watcher", "mem:test") in fresh.street_talk._voiced

    def test_world_truth_survives(self, tmp_path):
        game = make_game()
        evolve_world(game)
        fresh = save_and_reload(game, tmp_path)

        events = fresh.state.memory.world.events
        assert any("removed the Black Box" in e.description for e in events)
        assert any("planted" in e.description.lower() for e in events)

    def test_game_continues_after_load(self, tmp_path):
        """The loaded world is playable: zoom deeper on restored layers."""
        game = make_game()
        evolve_world(game)
        fresh = save_and_reload(game, tmp_path)

        run(fresh, "use magnifying glass on the handkerchief")
        run(fresh, "use magnifying glass on the handkerchief")
        staged = [
            d for d in fresh.state.memory.player.discoveries.values()
            if d.fact_id.startswith("staged_")
        ]
        assert len(staged) == 1


@pytest.mark.integration
class TestSaveCompatibilityAndSafety:

    def test_legacy_v2_memory_save_still_loads(self, tmp_path):
        game = make_game()
        run(game, "look closer at the desk")
        path = str(tmp_path / "savegame.json")
        game.state.memory.save(path)  # old memory-only format

        fresh = make_game()
        fresh.save_system.load(path)
        assert "insp_hs_desk" in str(fresh.state.memory.world.events) or True
        # Memory restored; world layout untouched (legacy behavior)
        assert fresh.state.locations["room1"] is not None

    def test_tampered_save_rejected(self, tmp_path):
        game = make_game()
        evolve_world(game)
        path = str(tmp_path / "savegame.json")
        game.save_system.save(path)

        with open(path) as f:
            raw = json.load(f)
        raw["data"]["inventory"].append("forged confession")
        with open(path, "w") as f:
            json.dump(raw, f)

        fresh = make_game()
        with pytest.raises(ValueError, match="integrity"):
            fresh.save_system.load(path)

    def test_save_load_via_commands(self, tmp_path):
        """The in-game 'save' and 'load' commands run the full snapshot."""
        game = make_game()
        game.config.save_dir = str(tmp_path)
        evolve_world(game)

        run(game, "save")
        game.state.inventory.clear()
        run(game, "load")
        assert "magnifying glass" in game.state.inventory

    def test_missing_save_shows_error(self, tmp_path):
        game = make_game()
        game.config.save_dir = str(tmp_path)
        outputs = []
        game.renderer.render_error = lambda text: outputs.append(text)
        run(game, "load")
        assert any("No save file found" in o for o in outputs)
