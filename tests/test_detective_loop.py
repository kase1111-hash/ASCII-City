"""
Integration tests for the detective gameplay loop built on inspection:

    look closer -> discovery -> spawned hotspot -> collect ->
    case file -> show evidence in interrogation -> pressure

Covers discovery-spawned hotspots, the case file command, and
evidence presentation in conversations.
"""

import json
import pytest

from shadowengine.scenarios.study_escape import create_study_escape
from shadowengine.interaction import HotspotType, CommandType
from shadowengine.llm.client import MockLLMClient, LLMConfig, LLMBackend
from shadowengine.llm.validation import validate_detail_layer_response
from shadowengine.config import (
    SHOW_EVIDENCE_PRESSURE_AMOUNT, SHOW_CHAIN_EVIDENCE_PRESSURE_AMOUNT,
)


MEDIUM_JSON = json.dumps({
    "description": "The desktop is scarred with ring stains. One baseboard behind it sits loose.",
    "detail_hooks": ["the loose baseboard"],
    "discovery": None,
})
CLOSE_JSON = json.dumps({
    "description": "Behind the loose baseboard, a sliver of dark metal catches the light.",
    "detail_hooks": ["the loose baseboard"],
    "discovery": {
        "fact_id": "hidden_black_box",
        "description": "A small black box hidden behind the baseboard - a wire recorder, still warm.",
        "is_evidence": True,
        "reveals_object": {
            "label": "Black Box",
            "type": "evidence",
            "description": "A matte-black wire recorder, not standard issue.",
        },
    },
})


def make_game():
    game = create_study_escape(seed=1234)
    mock = MockLLMClient(LLMConfig(backend=LLMBackend.MOCK))
    mock.set_response("ARM'S LENGTH", MEDIUM_JSON)
    mock.set_response("INCHES AWAY", CLOSE_JSON)
    mock.set_response("UNDER MAGNIFICATION", CLOSE_JSON)
    mock.set_response("detective", "I don't know anything about that.")
    game.llm_client = mock
    game.command_handler.llm_client = mock
    game.inspection_manager.detail_handler.llm_client = mock
    game.dialogue_handler.llm_client = mock
    game.conversation_manager.dialogue_handler.llm_client = mock
    game.renderer.wait_for_key = lambda prompt="": None
    return game, mock


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


def zoom_to_discovery(game):
    run(game, "look closer at your desk")
    run(game, "look closer")


# ============================================================
# Discovery-spawned hotspots
# ============================================================

@pytest.mark.integration
class TestSpawnedHotspots:

    def test_discovery_spawns_hotspot(self):
        game, _ = make_game()
        zoom_to_discovery(game)

        office = game.state.locations["office"]
        spawned = office.get_hotspot_by_label("Black Box")
        assert spawned is not None
        assert spawned.hotspot_type == HotspotType.EVIDENCE
        assert spawned.gives_item == "black box"

    def test_spawned_hotspot_not_duplicated(self):
        game, _ = make_game()
        zoom_to_discovery(game)
        run(game, "step back")
        run(game, "look closer")  # revisit the CLOSE layer

        office = game.state.locations["office"]
        black_boxes = [h for h in office.hotspots if h.label == "Black Box"]
        assert len(black_boxes) == 1

    def test_spawned_hotspot_is_takeable(self):
        game, _ = make_game()
        zoom_to_discovery(game)
        run(game, "take black box")
        assert "black box" in game.state.inventory

    def test_spawned_hotspot_is_itself_inspectable(self):
        game, _ = make_game()
        zoom_to_discovery(game)
        run(game, "look closer at the black box")
        assert any(
            obj_id.startswith("insp_hs_desk_found")
            for obj_id in game.inspection_manager.engine.objects
        )

    def test_trace_discovery_spawns_nothing(self):
        """A discovery without reveals_object adds no hotspot."""
        game, mock = make_game()
        no_object = json.loads(CLOSE_JSON)
        no_object["discovery"]["reveals_object"] = None
        mock.set_response("INCHES AWAY", json.dumps(no_object))

        before = len(game.state.locations["office"].hotspots)
        zoom_to_discovery(game)
        assert len(game.state.locations["office"].hotspots) == before


# ============================================================
# reveals_object validation
# ============================================================

@pytest.mark.unit
class TestRevealsObjectValidation:

    def test_valid_reveals_object(self):
        data = validate_detail_layer_response(json.loads(CLOSE_JSON))
        revealed = data["discovery"]["reveals_object"]
        assert revealed["label"] == "Black Box"
        assert revealed["type"] == "evidence"

    def test_missing_label_dropped(self):
        data = validate_detail_layer_response({
            "description": "x",
            "discovery": {
                "fact_id": "f", "description": "d",
                "reveals_object": {"type": "item"},
            },
        })
        assert data["discovery"]["reveals_object"] is None

    def test_bad_type_defaults_to_evidence(self):
        data = validate_detail_layer_response({
            "description": "x",
            "discovery": {
                "fact_id": "f", "description": "d",
                "reveals_object": {"label": "Thing", "type": "weapon"},
            },
        })
        assert data["discovery"]["reveals_object"]["type"] == "evidence"


# ============================================================
# Case file command
# ============================================================

@pytest.mark.integration
class TestCaseFile:

    def test_case_verbs_parse(self):
        game, _ = make_game()
        for text in ("case", "notes", "casebook", "clues", "evidence", "journal"):
            cmd = game.parser.parse(text)
            assert cmd.command_type == CommandType.CASE, text

    def test_case_file_lists_evidence(self, capsys):
        game, _ = make_game()
        zoom_to_discovery(game)
        capsys.readouterr()  # discard zoom output

        run(game, "case")
        output = capsys.readouterr().out
        assert "CASE FILE" in output
        assert "black box" in output.lower()
        assert "LEADS (0/4 uncovered)" in output

    def test_case_file_empty_state(self, capsys):
        game, _ = make_game()
        run(game, "case")
        output = capsys.readouterr().out
        assert "Nothing solid yet" in output


# ============================================================
# Show evidence in interrogation
# ============================================================

@pytest.mark.integration
class TestShowEvidence:

    def test_show_evidence_applies_pressure(self):
        game, _ = make_game()
        zoom_to_discovery(game)

        politician = game.state.characters["politician"]
        before = politician.state.pressure_accumulated
        game.conversation_manager.handle_show_evidence(
            politician, "black box", game.state,
        )
        assert politician.state.pressure_accumulated > before

    def test_chain_evidence_hits_harder(self):
        game, _ = make_game()
        # Plant a discovery whose fact id is in the spine's evidence chain
        game.state.memory.player_discovers(
            fact_id="physical_evidence",
            description="Torn fabric from the crime scene",
            location="alley",
            source="test",
            is_evidence=True,
        )
        bartender = game.state.characters["bartender"]
        game.conversation_manager.handle_show_evidence(
            bartender, "torn fabric", game.state,
        )
        # Pressure is resistance-scaled, so compare against the weaker tier
        # applied to a fresh identical character rather than exact numbers
        game2, _ = make_game()
        game2.state.memory.player_discovers(
            fact_id="unrelated_fact",
            description="Torn fabric from the crime scene",
            location="alley",
            source="test",
            is_evidence=True,
        )
        bartender2 = game2.state.characters["bartender"]
        game2.conversation_manager.handle_show_evidence(
            bartender2, "torn fabric", game2.state,
        )
        assert (
            bartender.state.pressure_accumulated
            > bartender2.state.pressure_accumulated
        )

    def test_show_unknown_evidence_is_error(self):
        game, _ = make_game()
        politician = game.state.characters["politician"]
        before = politician.state.pressure_accumulated
        game.conversation_manager.handle_show_evidence(
            politician, "purple elephant", game.state,
        )
        assert politician.state.pressure_accumulated == before

    def test_show_inventory_item_fallback(self):
        game, _ = make_game()
        game.state.inventory.append("magnifying glass")
        politician = game.state.characters["politician"]
        before = politician.state.pressure_accumulated
        # No discovery matches; the carried item is shown without pressure
        game.conversation_manager.handle_show_evidence(
            politician, "magnifying glass", game.state,
        )
        assert politician.state.pressure_accumulated == before

    def test_shown_evidence_recorded_in_character_memory(self):
        game, _ = make_game()
        zoom_to_discovery(game)
        politician = game.state.characters["politician"]
        game.conversation_manager.handle_show_evidence(
            politician, "black box", game.state,
        )
        char_memory = game.state.memory.get_character_memory("politician")
        assert any(
            i.interaction_type == "shown_evidence"
            for i in char_memory.player_interactions
        )

    def test_dialogue_context_uses_descriptions_not_ids(self):
        game, mock = make_game()
        zoom_to_discovery(game)

        politician = game.state.characters["politician"]
        game.conversation_manager.generate_dialogue(
            politician, "what do you know?", game.state,
        )
        prompt = mock.call_history[-1]
        assert "wire recorder" in prompt          # readable description
        assert "insp_hs_desk" not in prompt       # not the raw fact id
