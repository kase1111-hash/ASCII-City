"""Tests for CommandHandler — command routing, examine, take, wait, save/load."""

import os
import json
import pytest
from unittest.mock import MagicMock, patch

from src.shadowengine.command_handler import CommandHandler
from src.shadowengine.location_manager import LocationManager
from src.shadowengine.conversation import ConversationManager
from src.shadowengine.game import GameState
from src.shadowengine.config import GameConfig, DEFAULT_CONFIG
from src.shadowengine.interaction import CommandParser, Command, CommandType, Hotspot, HotspotType
from src.shadowengine.render import Location, Renderer
from src.shadowengine.llm.client import MockLLMClient, LLMConfig, LLMBackend, LLMResponse
from src.shadowengine.character import Character, Archetype
from src.shadowengine.memory import EventType


@pytest.fixture
def mock_renderer():
    r = MagicMock(spec=Renderer)
    r.render_prompt = MagicMock(return_value="")
    return r


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
def config():
    return DEFAULT_CONFIG


@pytest.fixture
def handler(mock_renderer, mock_llm):
    parser = CommandParser()
    loc_mgr = MagicMock(spec=LocationManager)
    conv_mgr = MagicMock(spec=ConversationManager)
    return CommandHandler(
        parser=parser,
        renderer=mock_renderer,
        llm_client=mock_llm,
        location_manager=loc_mgr,
        conversation_manager=conv_mgr,
    )


class TestCommandRouting:
    """Test that commands are routed to the correct handler."""

    def test_quit_stops_game(self, handler, state, config):
        cmd = Command(command_type=CommandType.QUIT, raw_input="quit")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        assert state.is_running is False

    def test_help_shows_text(self, handler, state, config):
        cmd = Command(command_type=CommandType.HELP, raw_input="help")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.renderer.render_text.assert_called()
        handler.renderer.wait_for_key.assert_called()

    def test_inventory_shows_items(self, handler, state, config):
        state.inventory = ["knife", "key"]
        cmd = Command(command_type=CommandType.INVENTORY, raw_input="inventory")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.renderer.render_inventory.assert_called_once_with(["knife", "key"])

    def test_wait_advances_time(self, handler, state, config):
        initial_time = state.memory.current_time
        cmd = Command(command_type=CommandType.WAIT, raw_input="wait")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.renderer.render_narration.assert_called()

    def test_unknown_direction_north(self, handler, state, config):
        cmd = Command(command_type=CommandType.UNKNOWN, raw_input="north")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.location_manager.handle_direction.assert_called_once()
        args = handler.location_manager.handle_direction.call_args
        assert args[0][0] == "north"

    def test_unknown_go_someplace(self, handler, state, config):
        cmd = Command(command_type=CommandType.UNKNOWN, raw_input="go the docks")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.location_manager.handle_free_movement.assert_called_once()
        args = handler.location_manager.handle_free_movement.call_args
        assert args[0][0] == "the docks"

    def test_unknown_go_direction(self, handler, state, config):
        cmd = Command(command_type=CommandType.UNKNOWN, raw_input="go east")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.location_manager.handle_direction.assert_called_once()
        args = handler.location_manager.handle_direction.call_args
        assert args[0][0] == "east"


class TestExamine:
    """Test examine command handler."""

    def test_examine_shows_description(self, handler, state, config):
        hotspot = Hotspot(
            id="hs_lamp", label="Old Lamp", hotspot_type=HotspotType.OBJECT,
            position=(10, 10), description="A dusty lamp.",
            examine_text="The lamp flickers weakly.",
        )
        state.locations["bar"].add_hotspot(hotspot)
        cmd = Command(command_type=CommandType.EXAMINE, target="Old Lamp", raw_input="examine old lamp")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.renderer.render_action_result.assert_called_with("The lamp flickers weakly.")

    def test_examine_reveals_fact(self, handler, state, config):
        hotspot = Hotspot(
            id="hs_note", label="Crumpled Note", hotspot_type=HotspotType.EVIDENCE,
            position=(10, 10), description="A crumpled note.",
            examine_text="The note reads: 'Meet me at midnight.'",
            reveals_fact="midnight_meeting",
        )
        state.locations["bar"].add_hotspot(hotspot)
        cmd = Command(command_type=CommandType.EXAMINE, target="Crumpled Note", raw_input="examine note")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        assert "midnight_meeting" in state.memory.player.discoveries
        handler.renderer.render_discovery.assert_called()

    def test_examine_updates_spine(self, handler, state, config):
        spine = MagicMock()
        state.spine = spine
        hotspot = Hotspot(
            id="hs_clue", label="Clue", hotspot_type=HotspotType.EVIDENCE,
            position=(10, 10), description="A clue.", examine_text="Important clue.",
            reveals_fact="clue_1",
        )
        state.locations["bar"].add_hotspot(hotspot)
        cmd = Command(command_type=CommandType.EXAMINE, target="Clue", raw_input="examine clue")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        spine.make_revelation.assert_called_with("clue_1")

    def test_examine_marks_discovered(self, handler, state, config):
        hotspot = Hotspot(
            id="hs_obj", label="Object", hotspot_type=HotspotType.OBJECT,
            position=(10, 10), description="An object.",
        )
        state.locations["bar"].add_hotspot(hotspot)
        assert not hotspot.discovered
        cmd = Command(command_type=CommandType.EXAMINE, target="Object", raw_input="examine object")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        assert hotspot.discovered


class TestTake:
    """Test take command handler."""

    def test_take_item_adds_to_inventory(self, handler, state, config):
        hotspot = Hotspot(
            id="hs_key", label="Rusty Key", hotspot_type=HotspotType.ITEM,
            position=(10, 10), description="A rusty key.",
            gives_item="rusty_key",
        )
        state.locations["bar"].add_hotspot(hotspot)
        cmd = Command(command_type=CommandType.TAKE, target="Rusty Key", raw_input="take key")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        assert "rusty_key" in state.inventory

    def test_take_deactivates_hotspot(self, handler, state, config):
        hotspot = Hotspot(
            id="hs_coin", label="Coin", hotspot_type=HotspotType.ITEM,
            position=(10, 10), description="A coin.",
        )
        state.locations["bar"].add_hotspot(hotspot)
        assert hotspot.active
        cmd = Command(command_type=CommandType.TAKE, target="Coin", raw_input="take coin")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        assert not hotspot.active

    def test_take_non_item_fails(self, handler, state, config):
        hotspot = Hotspot(
            id="hs_wall", label="Wall", hotspot_type=HotspotType.OBJECT,
            position=(10, 10), description="A wall.",
        )
        state.locations["bar"].add_hotspot(hotspot)
        cmd = Command(command_type=CommandType.TAKE, target="Wall", raw_input="take wall")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.renderer.render_error.assert_called_with("You can't take that.")

    def test_take_evidence_reveals_fact(self, handler, state, config):
        hotspot = Hotspot(
            id="hs_ev", label="Bloodied Cloth", hotspot_type=HotspotType.EVIDENCE,
            position=(10, 10), description="A bloodied cloth.",
            examine_text="Blood-stained fabric.",
            gives_item="bloodied_cloth",
            reveals_fact="blood_evidence",
        )
        state.locations["bar"].add_hotspot(hotspot)
        cmd = Command(command_type=CommandType.TAKE, target="Bloodied Cloth", raw_input="take cloth")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        assert "bloodied_cloth" in state.inventory
        assert "blood_evidence" in state.memory.player.discoveries


class TestTalk:
    """Test talk command handler."""

    def test_talk_to_person_starts_conversation(self, handler, state, config):
        char = Character(
            id="bartender", name="Joe", archetype=Archetype.INNOCENT,
            description="The bartender.",
        )
        state.characters["bartender"] = char
        state.memory.register_character("bartender")

        hotspot = Hotspot.create_person(
            id="hs_bartender", name="Joe", position=(30, 10),
            character_id="bartender", description="The bartender.",
        )
        state.locations["bar"].add_hotspot(hotspot)

        cmd = Command(command_type=CommandType.TALK, target="Joe", raw_input="talk joe")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        assert state.in_conversation is True
        assert state.conversation_partner == "bartender"

    def test_talk_to_object_fails(self, handler, state, config):
        hotspot = Hotspot(
            id="hs_chair", label="Chair", hotspot_type=HotspotType.OBJECT,
            position=(10, 10), description="A chair.",
        )
        state.locations["bar"].add_hotspot(hotspot)
        cmd = Command(command_type=CommandType.TALK, target="Chair", raw_input="talk chair")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.renderer.render_error.assert_called_with("You can't talk to that.")

    def test_talk_missing_character_fails(self, handler, state, config):
        hotspot = Hotspot.create_person(
            id="hs_ghost", name="Ghost", position=(30, 10),
            character_id="nonexistent", description="A ghost.",
        )
        state.locations["bar"].add_hotspot(hotspot)
        cmd = Command(command_type=CommandType.TALK, target="Ghost", raw_input="talk ghost")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.renderer.render_error.assert_called_with("That person isn't available.")


class TestGo:
    """Test go command delegation to location manager."""

    def test_go_exit_delegates_to_location_manager(self, handler, state, config):
        hotspot = Hotspot(
            id="hs_door", label="Back Door", hotspot_type=HotspotType.EXIT,
            position=(10, 15), description="A back door.",
            target_id="alley",
        )
        state.locations["bar"].add_hotspot(hotspot)
        cmd = Command(command_type=CommandType.GO, target="Back Door", raw_input="go back door")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.location_manager.handle_go.assert_called_once()

    def test_go_nonexistent_target_tries_free_movement(self, handler, state, config):
        cmd = Command(command_type=CommandType.GO, target="the docks", raw_input="go the docks")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.location_manager.handle_free_movement.assert_called_once()


class TestFreeExploration:
    """Test LLM-based free exploration fallback."""

    def test_free_exploration_with_llm_response(self, handler, state, config):
        # Set up mock LLM to return a valid JSON response
        handler.llm_client = MagicMock()
        handler.llm_client.chat.return_value = LLMResponse(
            text=json.dumps({
                "action": "other",
                "target": "",
                "narrative": "You look around the smoky bar.",
                "success": True,
            }),
            success=True,
        )

        cmd = Command(command_type=CommandType.UNKNOWN, raw_input="look around carefully")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.renderer.render_narration.assert_called_with("You look around the smoky bar.")

    def test_free_exploration_llm_failure_shows_fallback(self, handler, state, config):
        handler.llm_client = MagicMock()
        handler.llm_client.chat.return_value = LLMResponse(
            text="", success=False, error="timeout",
        )

        cmd = Command(command_type=CommandType.UNKNOWN, raw_input="do something weird")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        handler.renderer.render_narration.assert_called_with("You consider your options...")


class TestSaveLoad:
    """Test save and load commands."""

    def test_save_calls_memory_save(self, handler, state, config, tmp_path):
        config_copy = GameConfig(save_dir=str(tmp_path))
        cmd = Command(command_type=CommandType.SAVE, raw_input="save")
        handler.handle_command(cmd, {}, state, config_copy, lambda c: None)
        handler.renderer.render_text.assert_called()

    def test_load_nonexistent_shows_error(self, handler, state, config, tmp_path):
        config_copy = GameConfig(save_dir=str(tmp_path))
        cmd = Command(command_type=CommandType.LOAD, raw_input="load")
        handler.handle_command(cmd, {}, state, config_copy, lambda c: None)
        handler.renderer.render_error.assert_called_with("No save file found.")


class TestHotspotDefault:
    """Test default hotspot action routing."""

    def test_person_hotspot_defaults_to_talk(self, handler, state, config):
        char = Character(
            id="npc1", name="NPC", archetype=Archetype.SURVIVOR, description="An NPC.",
        )
        state.characters["npc1"] = char
        state.memory.register_character("npc1")

        hotspot = Hotspot.create_person(
            id="hs_npc1", name="NPC", position=(30, 10),
            character_id="npc1", description="An NPC.",
        )
        state.locations["bar"].add_hotspot(hotspot)
        cmd = Command(command_type=CommandType.HOTSPOT, target="NPC", raw_input="1")
        handler.handle_command(cmd, {}, state, config, lambda c: None)
        assert state.in_conversation is True
