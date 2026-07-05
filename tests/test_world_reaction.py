"""
Integration tests for the world reacting to investigation:

- Evidence tampering: witnessed finds left uncollected disappear,
  recorded as world truth, discoverable as tampering evidence
- Tool-specific reveals: UV light / stethoscope / mirror / probe
  generate their own kind of detail
- Spine advancement: accumulated evidence at a location satisfies
  location-tagged revelations
"""

import json
import pytest

from shadowengine.game import Game
from shadowengine.character import Character, Archetype
from shadowengine.render import Location
from shadowengine.interaction import Hotspot, HotspotType
from shadowengine.narrative import (
    NarrativeSpine, ConflictType, TrueResolution, Revelation,
)
from shadowengine.config import EVIDENCE_TAMPER_DELAY_UNITS
from shadowengine.llm.client import (
    LLMClient, LLMConfig, LLMResponse, LLMBackend, MockLLMClient,
)


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
UV_JSON = json.dumps({
    "description": "Under the lamp, a wide smear glows pale - someone scrubbed this surface with solvent, recently and in a hurry.",
    "detail_hooks": ["the scrubbed smear"],
    "discovery": {
        "fact_id": "cleaned_stain",
        "description": "A large stain was scrubbed off the desk with solvent - recently.",
        "is_evidence": True,
    },
})


class DeadLLM(LLMClient):
    def check_availability(self):
        return False

    def generate(self, prompt, system=None):
        return LLMResponse.error_response("connection refused")


def make_spine():
    return NarrativeSpine(
        conflict_type=ConflictType.MURDER,
        conflict_description="A test case.",
        true_resolution=TrueResolution(
            culprit_id="watcher",
            motive="m", method="x", opportunity="o",
            evidence_chain=["scene_lead"],
        ),
        revelations=[
            Revelation(
                id="scene_lead",
                description="This room holds the answer",
                importance=2,
                location_id="room",
            ),
        ],
    )


def make_game(llm=None, with_witness=True, with_spine=True):
    game = Game()
    game.renderer.wait_for_key = lambda prompt="": None

    if llm is None:
        llm = MockLLMClient(LLMConfig(backend=LLMBackend.MOCK))
        llm.set_response("ARM'S LENGTH", MEDIUM_JSON)
        llm.set_response("INCHES AWAY", CLOSE_JSON)
        llm.set_response("UNDER MAGNIFICATION", CLOSE_JSON)
        llm.set_response("ultraviolet", UV_JSON)
    game.llm_client = llm
    game.command_handler.llm_client = llm
    game.inspection_manager.detail_handler.llm_client = llm

    room = Location(id="room", name="Back Room", description="A cramped back room.")
    room.add_hotspot(Hotspot(
        id="hs_desk",
        label="Oak Desk",
        hotspot_type=HotspotType.OBJECT,
        position=(10, 10),
        description="A battered oak desk.",
        examine_text="A battered oak desk covered in papers.",
    ))
    if with_witness:
        room.add_hotspot(Hotspot.create_person(
            id="hs_watcher",
            name="The Watcher",
            position=(20, 10),
            character_id="watcher",
            description="A gaunt man watching from the corner.",
        ))
    game.add_location(room)
    game.set_start_location("room")

    watcher = Character(
        id="watcher", name="The Watcher",
        archetype=Archetype.SURVIVOR,
        description="A gaunt man with restless hands.",
    )
    game.add_character(watcher)

    if with_spine:
        game.set_spine(make_spine())
    return game, llm


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


def find_evidence(game):
    """Zoom to the CLOSE discovery, spawning the Black Box."""
    run(game, "look closer at the desk")
    run(game, "look closer")


# ============================================================
# Evidence tampering
# ============================================================

@pytest.mark.integration
class TestEvidenceTampering:

    def test_witnessed_find_registers_threat(self):
        game, _ = make_game()
        find_evidence(game)
        threats = game.state.evidence_watch.threats
        assert len(threats) == 1
        assert threats[0].label == "Black Box"
        assert "watcher" in threats[0].witnesses

    def test_unwitnessed_find_registers_nothing(self):
        game, _ = make_game(with_witness=False)
        find_evidence(game)
        assert game.state.evidence_watch.threats == []

    def test_collecting_evidence_clears_threat(self):
        game, _ = make_game()
        find_evidence(game)
        run(game, "take black box")
        game.state.evidence_watch.update(game.state, game.renderer)
        assert game.state.evidence_watch.threats == []

    def test_uncollected_evidence_disappears_when_away(self):
        game, _ = make_game()
        find_evidence(game)

        game.state.memory.advance_time(EVIDENCE_TAMPER_DELAY_UNITS + 1)
        game.state.current_location_id = "elsewhere"
        game.state.evidence_watch.update(game.state, game.renderer)

        room = game.state.locations["room"]
        black_box = next(h for h in room.hotspots if h.label == "Black Box")
        assert not black_box.active
        assert not black_box.visible
        assert game.state.evidence_watch.threats[0].destroyed

    def test_tampering_recorded_as_world_truth(self):
        game, _ = make_game()
        find_evidence(game)
        game.state.memory.advance_time(EVIDENCE_TAMPER_DELAY_UNITS + 1)
        game.state.current_location_id = "elsewhere"
        game.state.evidence_watch.update(game.state, game.renderer)

        assert any(
            "watcher" in e.actors and "removed" in e.description.lower()
            for e in game.state.memory.world.events
        )

    def test_returning_reveals_tampering_as_evidence(self):
        game, _ = make_game()
        find_evidence(game)
        game.state.memory.advance_time(EVIDENCE_TAMPER_DELAY_UNITS + 1)
        game.state.current_location_id = "elsewhere"
        game.state.evidence_watch.update(game.state, game.renderer)

        game.state.current_location_id = "room"
        game.state.evidence_watch.update(game.state, game.renderer)

        tampered = [
            d for d in game.state.memory.player.discoveries.values()
            if d.fact_id.startswith("tampered_")
        ]
        assert len(tampered) == 1
        assert tampered[0].is_evidence
        assert game.state.evidence_watch.threats == []

    def test_player_presence_blocks_tampering(self):
        game, _ = make_game()
        find_evidence(game)
        game.state.memory.advance_time(EVIDENCE_TAMPER_DELAY_UNITS + 1)
        # Player stays in the room, standing guard
        game.state.evidence_watch.update(game.state, game.renderer)

        room = game.state.locations["room"]
        black_box = next(h for h in room.hotspots if h.label == "Black Box")
        assert black_box.active

    def test_no_spine_means_no_tampering(self):
        game, _ = make_game(with_spine=False)
        find_evidence(game)
        game.state.evidence_watch.update(game.state, game.renderer)
        assert game.state.evidence_watch.threats == []


# ============================================================
# Tool-specific reveals
# ============================================================

@pytest.mark.integration
class TestToolReveals:

    def test_uv_light_generates_tool_flavored_detail(self):
        game, _ = make_game()
        game.state.inventory.append("uv lamp")
        run(game, "use uv light on the desk")

        discoveries = game.state.memory.player.discoveries
        assert "insp_hs_desk_cleaned_stain" in discoveries
        assert discoveries["insp_hs_desk_cleaned_stain"].is_evidence

    def test_uv_lamp_name_recognized(self):
        game, _ = make_game()
        game.state.inventory.append("uv lamp")
        assert game.inspection_manager.wants_inspection("use uv lamp on the desk")
        run(game, "use uv lamp on the desk")
        assert "insp_hs_desk_cleaned_stain" in game.state.memory.player.discoveries

    def test_tool_view_is_cached(self):
        game, mock = make_game()
        game.state.inventory.append("uv lamp")
        run(game, "use uv light on the desk")
        calls_after_first = len(mock.call_history)
        run(game, "use uv light on the desk")
        assert len(mock.call_history) == calls_after_first

    def test_tool_reveal_works_offline(self):
        game, _ = make_game(llm=DeadLLM(LLMConfig(backend=LLMBackend.OLLAMA)))
        game.state.inventory.append("uv lamp")
        run(game, "use uv light on the desk")  # no exception, no discovery
        assert not any(
            "cleaned_stain" in fid
            for fid in game.state.memory.player.discoveries
        )

    def test_missing_sensory_tool_reports_error(self):
        game, _ = make_game()
        run(game, "use uv light on the desk")
        assert "insp_hs_desk_cleaned_stain" not in game.state.memory.player.discoveries


# ============================================================
# Spine advancement from accumulated evidence
# ============================================================

@pytest.mark.integration
class TestSpineAdvancement:

    def test_enough_evidence_at_location_reveals_lead(self):
        game, _ = make_game()
        find_evidence(game)  # 1st piece of evidence at "room"
        assert "scene_lead" not in game.state.spine.revealed_facts

        game.state.inventory.append("uv lamp")
        run(game, "use uv light on the desk")  # 2nd piece at "room"
        assert "scene_lead" in game.state.spine.revealed_facts

    def test_prerequisites_still_gate_leads(self):
        game, _ = make_game()
        game.state.spine.revelations[0].prerequisites = ["earlier_lead"]
        game.state.spine.revelations.append(
            Revelation(id="earlier_lead", description="First thread", importance=1)
        )

        find_evidence(game)
        game.state.inventory.append("uv lamp")
        run(game, "use uv light on the desk")
        assert "scene_lead" not in game.state.spine.revealed_facts

        # Prerequisite satisfied -> next evidence completes the lead
        game.state.spine.make_revelation("earlier_lead")
        game.state.memory.player_discovers(
            fact_id="third_clue", description="one more thread",
            location="room", source="test", is_evidence=True,
        )
        from shadowengine.inspection_manager import check_location_leads
        check_location_leads(game.state, game.renderer)
        assert "scene_lead" in game.state.spine.revealed_facts

    def test_evidence_elsewhere_does_not_count(self):
        game, _ = make_game()
        for i in range(3):
            game.state.memory.player_discovers(
                fact_id=f"far_clue_{i}", description="far away",
                location="docks", source="test", is_evidence=True,
            )
        from shadowengine.inspection_manager import check_location_leads
        check_location_leads(game.state, game.renderer)
        assert "scene_lead" not in game.state.spine.revealed_facts

    def test_study_escape_alley_lead_is_location_tagged(self):
        from shadowengine.scenarios.study_escape import create_study_escape
        game = create_study_escape(seed=5)
        physical = next(
            r for r in game.state.spine.revelations if r.id == "physical_evidence"
        )
        assert physical.location_id == "alley"

    def test_politician_now_reachable_in_office(self):
        from shadowengine.scenarios.study_escape import create_study_escape
        game = create_study_escape(seed=5)
        office = game.state.locations["office"]
        person = office.get_hotspot_by_label("Councilman Harrow")
        assert person is not None
        assert person.target_id == "politician"
