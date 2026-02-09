"""Tests for LocationManager — location generation, movement, fallback creation."""

import json
import pytest
from unittest.mock import MagicMock

from src.shadowengine.location_manager import LocationManager
from src.shadowengine.game import GameState
from src.shadowengine.config import DEFAULT_CONFIG, GameConfig
from src.shadowengine.interaction import Hotspot, HotspotType
from src.shadowengine.render import Location, Renderer
from src.shadowengine.llm.client import (
    MockLLMClient, LLMConfig, LLMBackend, LLMResponse,
)
from src.shadowengine.character import Character, Archetype
from src.shadowengine.memory import EventType


def make_location_json(
    loc_id="alley_01",
    name="Dark Alley",
    description="A narrow alley.",
    location_type="alley",
    is_outdoor=True,
    ambient="Dripping water echoes.",
    hotspots=None,
    npcs=None,
    connections=None,
):
    return json.dumps({
        "id": loc_id,
        "name": name,
        "description": description,
        "location_type": location_type,
        "is_outdoor": is_outdoor,
        "ambient": ambient,
        "hotspots": hotspots or [],
        "npcs": npcs or [],
        "connections": connections or {},
    })


@pytest.fixture
def mock_renderer():
    return MagicMock(spec=Renderer)


@pytest.fixture
def mock_llm():
    config = LLMConfig(backend=LLMBackend.MOCK)
    return MockLLMClient(config)


@pytest.fixture
def state():
    s = GameState()
    loc = Location(id="bar", name="The Bar", description="A smoky bar.")
    s.locations["bar"] = loc
    s.current_location_id = "bar"
    s.environment.register_location("bar", is_indoor=True)
    return s


@pytest.fixture
def loc_mgr(mock_renderer, mock_llm):
    from src.shadowengine.world_state import WorldState
    ws = WorldState()
    return LocationManager(
        llm_client=mock_llm,
        world_state=ws,
        renderer=mock_renderer,
    )


def noop_add_character(char):
    """Stub for add_character callback."""
    pass


class TestHandleGo:
    """Test movement via exit hotspots."""

    def test_go_to_existing_location(self, loc_mgr, state):
        dest = Location(id="alley", name="The Alley", description="A dark alley.")
        state.locations["alley"] = dest
        state.environment.register_location("alley", is_indoor=False)

        exit_hs = Hotspot(
            id="hs_door", label="Back Door", hotspot_type=HotspotType.EXIT,
            position=(10, 15), description="A back door.", target_id="alley",
        )

        loc_mgr.handle_go(exit_hs, state.locations["bar"], state, DEFAULT_CONFIG, noop_add_character)

        assert state.current_location_id == "alley"

    def test_go_non_exit_fails(self, loc_mgr, state):
        hotspot = Hotspot(
            id="hs_chair", label="Chair", hotspot_type=HotspotType.OBJECT,
            position=(10, 10), description="A chair.",
        )

        loc_mgr.handle_go(hotspot, state.locations["bar"], state, DEFAULT_CONFIG, noop_add_character)

        assert state.current_location_id == "bar"  # Didn't move
        loc_mgr.renderer.render_error.assert_called_with("You can't go there.")

    def test_go_records_movement_event(self, loc_mgr, state):
        dest = Location(id="alley", name="The Alley", description="A dark alley.")
        state.locations["alley"] = dest
        state.environment.register_location("alley", is_indoor=False)

        exit_hs = Hotspot(
            id="hs_door", label="Back Door", hotspot_type=HotspotType.EXIT,
            position=(10, 15), description="A back door.", target_id="alley",
        )

        loc_mgr.handle_go(exit_hs, state.locations["bar"], state, DEFAULT_CONFIG, noop_add_character)

        events = state.memory.world.events
        movement_events = [e for e in events if e.event_type == EventType.MOVEMENT]
        assert len(movement_events) >= 1


class TestHandleDirection:
    """Test directional movement."""

    def test_direction_matches_exit_label(self, loc_mgr, state):
        dest = Location(id="street", name="Street", description="A wet street.")
        state.locations["street"] = dest
        state.environment.register_location("street", is_indoor=False)

        exit_hs = Hotspot(
            id="hs_north", label="Go North to Street", hotspot_type=HotspotType.EXIT,
            position=(10, 15), description="Head north.", target_id="street",
        )
        state.locations["bar"].add_hotspot(exit_hs)

        loc_mgr.handle_direction("north", state.locations["bar"], state, DEFAULT_CONFIG, noop_add_character)

        assert state.current_location_id == "street"

    def test_direction_no_exit_generates_location(self, loc_mgr, state):
        # Mock LLM to return valid location JSON
        loc_mgr.llm_client = MagicMock()
        loc_mgr.llm_client.chat.return_value = LLMResponse(
            text=make_location_json(loc_id="bar_north", name="Northern Street"),
            success=True,
        )

        loc_mgr.handle_direction("north", state.locations["bar"], state, DEFAULT_CONFIG, noop_add_character)

        assert "bar_north" in state.locations or state.current_location_id != "bar"


class TestHandleFreeMovement:
    """Test free-form movement to named destinations."""

    def test_free_movement_to_existing_location(self, loc_mgr, state):
        dest = Location(id="docks", name="The Docks", description="Foggy docks.")
        state.locations["docks"] = dest
        state.environment.register_location("docks", is_indoor=False)

        loc_mgr.handle_free_movement("the docks", state.locations["bar"], state, DEFAULT_CONFIG, noop_add_character)

        assert state.current_location_id == "docks"

    def test_free_movement_generates_new_location(self, loc_mgr, state):
        loc_mgr.llm_client = MagicMock()
        loc_mgr.llm_client.chat.return_value = LLMResponse(
            text=make_location_json(loc_id="warehouse", name="The Warehouse"),
            success=True,
        )

        loc_mgr.handle_free_movement("warehouse", state.locations["bar"], state, DEFAULT_CONFIG, noop_add_character)

        assert state.current_location_id == "warehouse"


class TestParseLocationResponse:
    """Test LLM response parsing into Location objects."""

    def test_valid_response_creates_location(self, loc_mgr, state):
        text = make_location_json(
            loc_id="alley_01",
            name="Dark Alley",
            description="A narrow, trash-strewn alley.",
            hotspots=[
                {"label": "Dumpster", "type": "object", "description": "A rusty dumpster."},
            ],
        )

        location = loc_mgr.parse_location_response(
            text, "fallback_id", "fallback name",
            state.locations["bar"], state, noop_add_character,
        )

        assert location is not None
        assert location.id == "alley_01"
        assert location.name == "Dark Alley"
        assert len(location.hotspots) >= 1  # At least the dumpster

    def test_response_with_npcs_creates_characters(self, loc_mgr, state):
        added_chars = []

        def track_add(char):
            added_chars.append(char)

        text = make_location_json(
            npcs=[{
                "id": "npc_stranger",
                "name": "Mysterious Stranger",
                "archetype": "outsider",
                "description": "A figure in a trench coat.",
                "topics": ["the night", "the victim"],
            }],
        )

        location = loc_mgr.parse_location_response(
            text, "fb_id", "fb_name",
            state.locations["bar"], state, track_add,
        )

        assert location is not None
        assert len(added_chars) == 1
        assert added_chars[0].name == "Mysterious Stranger"

    def test_response_adds_back_exit(self, loc_mgr, state):
        text = make_location_json()

        location = loc_mgr.parse_location_response(
            text, "fb_id", "fb_name",
            state.locations["bar"], state, noop_add_character,
        )

        back_exits = [h for h in location.hotspots if "Back to" in h.label]
        assert len(back_exits) == 1
        assert back_exits[0].target_id == "bar"

    def test_invalid_json_returns_none(self, loc_mgr, state):
        location = loc_mgr.parse_location_response(
            "this is not json", "fb_id", "fb_name",
            state.locations["bar"], state, noop_add_character,
        )
        assert location is None

    def test_uses_fallback_id_when_response_id_empty(self, loc_mgr, state):
        text = make_location_json(loc_id="")

        location = loc_mgr.parse_location_response(
            text, "my_fallback", "My Fallback",
            state.locations["bar"], state, noop_add_character,
        )

        assert location is not None
        assert location.id == "my_fallback"

    def test_exit_hotspot_has_target_id(self, loc_mgr, state):
        text = make_location_json(
            hotspots=[{
                "label": "North Exit",
                "type": "exit",
                "description": "An exit heading north.",
                "exit_to": "street_north",
            }],
        )

        location = loc_mgr.parse_location_response(
            text, "fb_id", "fb_name",
            state.locations["bar"], state, noop_add_character,
        )

        exits = [h for h in location.hotspots if h.hotspot_type == HotspotType.EXIT and h.label == "North Exit"]
        assert len(exits) == 1
        assert exits[0].target_id == "street_north"

    def test_connections_stored(self, loc_mgr, state):
        text = make_location_json(
            loc_id="street",
            connections={"north": "park", "south": "bar"},
        )

        location = loc_mgr.parse_location_response(
            text, "fb_id", "fb_name",
            state.locations["bar"], state, noop_add_character,
        )

        assert "street" in loc_mgr.location_connections
        assert loc_mgr.location_connections["street"]["north"] == "park"


class TestCreateFallbackLocation:
    """Test fallback location creation when LLM fails."""

    def test_fallback_creates_location(self, loc_mgr, state):
        loc_mgr.create_fallback_location("warehouse", "the warehouse", state.locations["bar"], state)

        assert "warehouse" in state.locations
        assert state.current_location_id == "warehouse"

    def test_fallback_has_back_exit(self, loc_mgr, state):
        loc_mgr.create_fallback_location("warehouse", "the warehouse", state.locations["bar"], state)

        loc = state.locations["warehouse"]
        back_exits = [h for h in loc.hotspots if "Back to" in h.label]
        assert len(back_exits) == 1
        assert back_exits[0].target_id == "bar"

    def test_fallback_has_directional_exits(self, loc_mgr, state):
        loc_mgr.create_fallback_location("warehouse", "the warehouse", state.locations["bar"], state)

        loc = state.locations["warehouse"]
        directions = [h.label for h in loc.hotspots if h.hotspot_type == HotspotType.EXIT]
        assert "Go North" in directions
        assert "Go South" in directions
        assert "Go East" in directions
        assert "Go West" in directions

    def test_fallback_records_movement(self, loc_mgr, state):
        loc_mgr.create_fallback_location("warehouse", "the warehouse", state.locations["bar"], state)

        events = state.memory.world.events
        movement_events = [e for e in events if e.event_type == EventType.MOVEMENT]
        assert len(movement_events) >= 1


class TestGenerateAndMove:
    """Test the full generate-and-move pipeline."""

    def test_successful_generation_moves_player(self, loc_mgr, state):
        loc_mgr.llm_client = MagicMock()
        loc_mgr.llm_client.chat.return_value = LLMResponse(
            text=make_location_json(loc_id="new_loc", name="New Location"),
            success=True,
        )

        loc_mgr.generate_and_move(
            "new_loc", "some place",
            state.locations["bar"], state, DEFAULT_CONFIG, noop_add_character,
        )

        assert state.current_location_id == "new_loc"
        assert "new_loc" in state.locations

    def test_failed_generation_creates_fallback(self, loc_mgr, state):
        loc_mgr.llm_client = MagicMock()
        loc_mgr.llm_client.chat.return_value = LLMResponse(
            text="", success=False, error="timeout",
        )

        loc_mgr.generate_and_move(
            "nowhere", "nowhere",
            state.locations["bar"], state, DEFAULT_CONFIG, noop_add_character,
        )

        assert state.current_location_id == "nowhere"
        assert "nowhere" in state.locations

    def test_tracks_distance(self, loc_mgr, state):
        loc_mgr.location_distances["bar"] = 0

        loc_mgr.llm_client = MagicMock()
        loc_mgr.llm_client.chat.return_value = LLMResponse(
            text=make_location_json(loc_id="loc_1"),
            success=True,
        )

        loc_mgr.generate_and_move(
            "loc_1", "first place",
            state.locations["bar"], state, DEFAULT_CONFIG, noop_add_character,
        )

        assert loc_mgr.location_distances["loc_1"] == 1
