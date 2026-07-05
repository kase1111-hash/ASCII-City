"""
Integration tests for the look-closer / zoom system in the live game loop.

Covers:
- Command routing: inspection commands intercepted, normal commands untouched
- Progressive zoom with LLM-generated layers and discovery recording
- Tool gating (FINE requires a magnifying glass from inventory)
- Offline fallback to template detail generation
- Layer caching/consistency and discovery dedup
- NPC witnessing of close scrutiny
- Person proximity limits
- Darkness limits
"""

import json
import pytest

from shadowengine.game import Game
from shadowengine.character import Character, Archetype
from shadowengine.render import Location
from shadowengine.interaction import Hotspot, HotspotType
from shadowengine.inspection import ZoomLevel
from shadowengine.inspection_manager import InspectionManager, definite_label, guess_material
from shadowengine.llm.client import (
    LLMClient, LLMConfig, LLMResponse, LLMBackend, MockLLMClient,
)
from shadowengine.llm.validation import (
    validate_detail_layer_response, ValidationError,
)


MEDIUM_JSON = json.dumps({
    "description": "Ring stains and paper cuts scar the leather blotter.",
    "detail_hooks": ["the leather blotter"],
    "discovery": None,
})
CLOSE_JSON = json.dumps({
    "description": "Fresh scratches score the wood around the lock plate.",
    "detail_hooks": ["the scratched lock plate"],
    "discovery": {
        "fact_id": "fresh_pry_marks",
        "description": "Fresh pry marks - someone searched this desk recently.",
        "is_evidence": True,
    },
})
FINE_JSON = json.dumps({
    "description": "Gray wool fibers are caught in the lock plate screws.",
    "detail_hooks": ["the wool fibers"],
    "discovery": {
        "fact_id": "wool_fibers",
        "description": "Gray wool fibers - the intruder wore expensive gloves.",
        "is_evidence": True,
    },
})


class DeadLLM(LLMClient):
    """LLM that always fails, to exercise the offline path."""

    def check_availability(self):
        return False

    def generate(self, prompt, system=None):
        return LLMResponse.error_response("connection refused")


def make_layer_mock() -> MockLLMClient:
    """Mock LLM keyed on the zoom-scale guidance in the prompts."""
    mock = MockLLMClient(LLMConfig(backend=LLMBackend.MOCK))
    mock.set_response("ARM'S LENGTH", MEDIUM_JSON)
    mock.set_response("INCHES AWAY", CLOSE_JSON)
    mock.set_response("UNDER MAGNIFICATION", FINE_JSON)
    return mock


def make_game(llm=None) -> Game:
    """Minimal game with one location, one object, one NPC."""
    game = Game()
    game.renderer.wait_for_key = lambda prompt="": None

    if llm is None:
        llm = make_layer_mock()
    game.llm_client = llm
    game.command_handler.llm_client = llm
    game.inspection_manager.detail_handler.llm_client = llm

    room = Location(
        id="room",
        name="Back Room",
        description="A cramped back room.",
    )
    room.add_hotspot(Hotspot(
        id="hs_desk",
        label="Oak Desk",
        hotspot_type=HotspotType.OBJECT,
        position=(10, 10),
        description="A battered oak desk.",
        examine_text="A battered oak desk covered in papers.",
    ))
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
        id="watcher",
        name="The Watcher",
        archetype=Archetype.SURVIVOR,
        description="A gaunt man with restless hands and a tobacco-stained coat.",
    )
    game.add_character(watcher)
    return game


def run_command(game: Game, text: str) -> None:
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


# ============================================================
# Routing
# ============================================================

@pytest.mark.integration
class TestInspectionRouting:
    """wants_inspection must only claim close-inspection commands."""

    @pytest.fixture
    def manager(self):
        return make_game().inspection_manager

    def test_claims_zoom_commands(self, manager):
        for text in (
            "look closer", "look closer at the desk", "zoom in",
            "zoom in on the desk", "step back", "zoom out",
            "look under the desk", "look behind the desk",
            "focus on the lock plate",
            "use magnifying glass on the desk",
            "magnify the inscription",
        ):
            assert manager.wants_inspection(text), text

    def test_ignores_normal_commands(self, manager):
        for text in (
            "examine the desk", "look at the desk", "take the key",
            "talk to the watcher", "go north", "go back", "back", "b",
            "n", "s", "e", "w", "north", "inventory", "help", "wait",
            "use screwdriver on button", "3", "1 examine",
            "kick the door",
        ):
            assert not manager.wants_inspection(text), text


# ============================================================
# Progressive zoom with LLM layers
# ============================================================

@pytest.mark.integration
class TestZoomProgression:

    def test_zoom_in_advances_level_and_caches_layer(self):
        game = make_game()
        run_command(game, "look closer at the desk")

        manager = game.inspection_manager
        obj = manager.engine.objects["insp_hs_desk"]
        assert manager.engine.zoom_manager.get_current_zoom(obj.id) == ZoomLevel.MEDIUM
        assert obj.has_layer(ZoomLevel.MEDIUM)
        assert "blotter" in obj.get_layer(ZoomLevel.MEDIUM).description

    def test_targetless_look_closer_uses_recent_object(self):
        game = make_game()
        run_command(game, "look closer at the desk")
        run_command(game, "look closer")  # no target - continue on the desk

        zoom = game.inspection_manager.engine.zoom_manager.get_current_zoom("insp_hs_desk")
        assert zoom == ZoomLevel.CLOSE

    def test_close_zoom_records_discovery_in_memory(self):
        game = make_game()
        run_command(game, "look closer at the desk")
        run_command(game, "look closer")

        discoveries = game.state.memory.player.discoveries
        assert "insp_hs_desk_fresh_pry_marks" in discoveries
        discovery = discoveries["insp_hs_desk_fresh_pry_marks"]
        assert discovery.is_evidence

    def test_discovery_not_duplicated_on_revisit(self):
        game = make_game()
        run_command(game, "look closer at the desk")
        run_command(game, "look closer")
        run_command(game, "step back")
        run_command(game, "look closer")  # back to CLOSE, same layer

        events = [
            e for e in game.state.memory.world.events
            if "fresh pry marks" in e.description.lower()
        ]
        assert len(events) == 1

    def test_zoom_out_reduces_level(self):
        game = make_game()
        run_command(game, "look closer at the desk")
        run_command(game, "look closer")
        run_command(game, "step back")

        zoom = game.inspection_manager.engine.zoom_manager.get_current_zoom("insp_hs_desk")
        assert zoom == ZoomLevel.MEDIUM

    def test_layers_are_stable_across_visits(self):
        """Memory-first: the same layer text on every revisit."""
        game = make_game()
        run_command(game, "look closer at the desk")
        obj = game.inspection_manager.engine.objects["insp_hs_desk"]
        first = obj.get_layer(ZoomLevel.MEDIUM).description

        run_command(game, "step back")
        run_command(game, "look closer")
        assert obj.get_layer(ZoomLevel.MEDIUM).description == first


# ============================================================
# Tool gating
# ============================================================

@pytest.mark.integration
class TestToolGating:

    def test_fine_zoom_blocked_without_tool(self):
        game = make_game()
        run_command(game, "look closer at the desk")
        run_command(game, "look closer")
        run_command(game, "look closer")  # would be FINE - no magnifier

        zoom = game.inspection_manager.engine.zoom_manager.get_current_zoom("insp_hs_desk")
        assert zoom == ZoomLevel.CLOSE

    def test_magnifying_glass_from_inventory_unlocks_fine(self):
        game = make_game()
        game.state.inventory.append("magnifying glass")

        run_command(game, "look closer at the desk")
        run_command(game, "use magnifying glass on the desk")

        manager = game.inspection_manager
        assert manager.engine.zoom_manager.get_current_zoom("insp_hs_desk") == ZoomLevel.FINE
        assert "insp_hs_desk_wool_fibers" in game.state.memory.player.discoveries

    def test_missing_tool_reports_error(self):
        game = make_game()
        run_command(game, "use magnifying glass on the desk")

        # No zoom happened; the object may not even be registered yet
        manager = game.inspection_manager
        zoom = manager.engine.zoom_manager.get_current_zoom("insp_hs_desk")
        assert zoom == ZoomLevel.COARSE


# ============================================================
# Offline fallback
# ============================================================

@pytest.mark.integration
class TestOfflineFallback:

    def test_zoom_works_without_llm(self):
        game = make_game(llm=DeadLLM(LLMConfig(backend=LLMBackend.OLLAMA)))
        run_command(game, "look closer at the desk")
        run_command(game, "look closer")

        zoom = game.inspection_manager.engine.zoom_manager.get_current_zoom("insp_hs_desk")
        assert zoom == ZoomLevel.CLOSE

    def test_directional_look_works_without_llm(self):
        game = make_game(llm=DeadLLM(LLMConfig(backend=LLMBackend.OLLAMA)))
        run_command(game, "look under the desk")
        # Handled without exception; desk registered as inspectable
        assert "insp_hs_desk" in game.inspection_manager.engine.objects

    def test_material_guessed_for_templates(self):
        game = make_game(llm=DeadLLM(LLMConfig(backend=LLMBackend.OLLAMA)))
        run_command(game, "look closer at the desk")
        obj = game.inspection_manager.engine.objects["insp_hs_desk"]
        assert obj.material == "wood"


# ============================================================
# World consequences
# ============================================================

@pytest.mark.integration
class TestWorldConsequences:

    def test_npc_witnesses_close_scrutiny(self):
        game = make_game()
        run_command(game, "look closer at the desk")
        run_command(game, "look closer")  # CLOSE - witnessed

        watcher_memory = game.state.memory.get_character_memory("watcher")
        assert any(
            "scrutinized" in b.content.lower() for b in watcher_memory.beliefs
        )

    def test_medium_zoom_not_witnessed(self):
        game = make_game()
        run_command(game, "look closer at the desk")  # MEDIUM only

        watcher_memory = game.state.memory.get_character_memory("watcher")
        assert not any(
            "scrutinized" in b.content.lower() for b in watcher_memory.beliefs
        )

    def test_time_passes_on_inspection(self):
        game = make_game()
        before = game.state.memory.current_time
        run_command(game, "look closer at the desk")
        assert game.state.memory.current_time == before + game.config.time_units_per_action

    def test_person_zoom_capped_at_close(self):
        game = make_game()
        run_command(game, "look closer at the watcher")
        run_command(game, "look closer")
        run_command(game, "look closer")  # personal space
        run_command(game, "look closer")

        zoom = game.inspection_manager.engine.zoom_manager.get_current_zoom("insp_hs_watcher")
        assert zoom.value <= ZoomLevel.CLOSE.value

    def test_darkness_blocks_close_inspection(self):
        game = make_game()
        game.state.environment.get_visibility = lambda loc_id=None: 0.1

        run_command(game, "look closer at the desk")   # MEDIUM ok in the dark
        run_command(game, "look closer")               # CLOSE blocked

        zoom = game.inspection_manager.engine.zoom_manager.get_current_zoom("insp_hs_desk")
        assert zoom == ZoomLevel.MEDIUM

    def test_lantern_restores_inspection_in_darkness(self):
        game = make_game()
        game.state.environment.get_visibility = lambda loc_id=None: 0.1
        game.state.inventory.append("lantern")

        run_command(game, "look closer at the desk")
        run_command(game, "look closer")

        zoom = game.inspection_manager.engine.zoom_manager.get_current_zoom("insp_hs_desk")
        assert zoom == ZoomLevel.CLOSE


# ============================================================
# Validation
# ============================================================

@pytest.mark.unit
class TestDetailLayerValidation:

    def test_valid_response(self):
        data = validate_detail_layer_response(json.loads(CLOSE_JSON))
        assert data["description"].startswith("Fresh scratches")
        assert data["discovery"]["fact_id"] == "fresh_pry_marks"
        assert data["discovery"]["is_evidence"] is True

    def test_missing_description_rejected(self):
        with pytest.raises(ValidationError):
            validate_detail_layer_response({"detail_hooks": ["x"]})

    def test_fact_id_slugified(self):
        data = validate_detail_layer_response({
            "description": "A thing.",
            "discovery": {"fact_id": "Weird ID! With Spaces", "description": "found"},
        })
        assert " " not in data["discovery"]["fact_id"]
        assert "!" not in data["discovery"]["fact_id"]

    def test_hooks_capped(self):
        data = validate_detail_layer_response({
            "description": "A thing.",
            "detail_hooks": ["a", "b", "c", "d", "e"],
        })
        assert len(data["detail_hooks"]) == 3

    def test_null_discovery_ok(self):
        data = validate_detail_layer_response({
            "description": "A thing.", "discovery": None,
        })
        assert data["discovery"] is None


# ============================================================
# Helpers
# ============================================================

@pytest.mark.unit
class TestHelpers:

    def test_definite_label(self):
        assert definite_label("Your Desk") == "your desk"
        assert definite_label("Dumpster") == "the dumpster"
        assert definite_label("The Chalk Outline") == "the chalk outline"
        assert definite_label("") == "it"

    def test_guess_material(self):
        assert guess_material("Oak Desk battered wood") == "wood"
        assert guess_material("Fire Escape rusty ladder") == "metal"
        assert guess_material("Brick Wall") == "stone"
        assert guess_material("Napkin") is None
