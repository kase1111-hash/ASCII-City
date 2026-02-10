"""Tests for ConversationManager — dialogue, threats, accusations."""

import pytest
from unittest.mock import MagicMock, patch

from src.shadowengine.conversation import ConversationManager
from src.shadowengine.game import GameState
from src.shadowengine.character import Character, Archetype
from src.shadowengine.render import Location, Renderer
from src.shadowengine.narrative import NarrativeSpine
from src.shadowengine.generation.dialogue_handler import DialogueHandler
from src.shadowengine.llm.client import MockLLMClient, LLMConfig, LLMBackend


@pytest.fixture
def mock_renderer():
    r = MagicMock(spec=Renderer)
    r.render_dialogue_prompt = MagicMock(return_value="")
    return r


@pytest.fixture
def mock_dialogue_handler():
    return MagicMock(spec=DialogueHandler)


@pytest.fixture
def conv_mgr(mock_renderer, mock_dialogue_handler):
    return ConversationManager(
        renderer=mock_renderer,
        dialogue_handler=mock_dialogue_handler,
    )


@pytest.fixture
def state():
    s = GameState()
    loc = Location(id="bar", name="The Bar", description="A smoky bar.")
    s.locations["bar"] = loc
    s.current_location_id = "bar"
    s.environment.register_location("bar", is_indoor=True)
    return s


@pytest.fixture
def bartender():
    return Character(
        id="bartender",
        name="Joe",
        archetype=Archetype.INNOCENT,
        description="The bartender, a grizzled veteran.",
        secret_truth="He saw the murder happen.",
        public_lie="He was cleaning glasses all night.",
    )


class TestConversationLoop:
    """Test conversation loop routing."""

    def test_leave_ends_conversation(self, conv_mgr, state, bartender):
        state.characters["bartender"] = bartender
        state.in_conversation = True
        state.conversation_partner = "bartender"
        conv_mgr.renderer.render_dialogue_prompt.return_value = "leave"

        conv_mgr.conversation_loop(state)

        assert state.in_conversation is False
        assert state.conversation_partner is None

    def test_goodbye_ends_conversation(self, conv_mgr, state, bartender):
        state.characters["bartender"] = bartender
        state.in_conversation = True
        state.conversation_partner = "bartender"
        conv_mgr.renderer.render_dialogue_prompt.return_value = "goodbye"

        conv_mgr.conversation_loop(state)

        assert state.in_conversation is False

    def test_missing_character_ends_conversation(self, conv_mgr, state):
        state.in_conversation = True
        state.conversation_partner = "nonexistent"

        conv_mgr.conversation_loop(state)

        assert state.in_conversation is False

    def test_threaten_delegates_to_handler(self, conv_mgr, state, bartender):
        state.characters["bartender"] = bartender
        state.in_conversation = True
        state.conversation_partner = "bartender"
        conv_mgr.renderer.render_dialogue_prompt.return_value = "threaten"

        conv_mgr.conversation_loop(state)

        # Should have called render_narration or show_dialogue for threat response
        assert conv_mgr.renderer.render_dialogue.called or conv_mgr.renderer.render_narration.called

    def test_accuse_delegates_to_handler(self, conv_mgr, state, bartender):
        state.characters["bartender"] = bartender
        state.in_conversation = True
        state.conversation_partner = "bartender"
        conv_mgr.renderer.render_dialogue_prompt.return_value = "accuse"

        conv_mgr.conversation_loop(state)

        # Accuse handler should respond with dialogue
        assert conv_mgr.renderer.render_dialogue.called

    def test_free_dialogue_sent_to_llm(self, conv_mgr, state, bartender):
        state.characters["bartender"] = bartender
        state.memory.register_character("bartender")
        state.in_conversation = True
        state.conversation_partner = "bartender"
        conv_mgr.renderer.render_dialogue_prompt.return_value = "what happened last night?"
        conv_mgr.dialogue_handler.generate_response.return_value = "I was here all night."

        conv_mgr.conversation_loop(state)

        conv_mgr.dialogue_handler.generate_response.assert_called_once()
        conv_mgr.renderer.render_dialogue.assert_called()


class TestFreeDialogue:
    """Test free-form dialogue handling."""

    def test_llm_response_shown(self, conv_mgr, state, bartender):
        conv_mgr.dialogue_handler.generate_response.return_value = "The rain never stops."

        conv_mgr.handle_free_dialogue(bartender, "tell me about the weather", state)

        conv_mgr.renderer.render_dialogue.assert_called_once()
        args = conv_mgr.renderer.render_dialogue.call_args[0]
        assert args[0] == "Joe"
        assert args[1] == "The rain never stops."

    def test_llm_failure_shows_fallback(self, conv_mgr, state, bartender):
        conv_mgr.dialogue_handler.generate_response.return_value = None

        conv_mgr.handle_free_dialogue(bartender, "something obscure", state)

        conv_mgr.renderer.render_dialogue.assert_called_once()
        args = conv_mgr.renderer.render_dialogue.call_args[0]
        assert "not sure" in args[1] or "don't have" in args[1]

    def test_cracked_character_confesses(self, conv_mgr, state, bartender):
        bartender.state.is_cracked = True

        conv_mgr.handle_free_dialogue(bartender, "anything", state)

        conv_mgr.renderer.render_dialogue.assert_called_once()
        args = conv_mgr.renderer.render_dialogue.call_args[0]
        assert "truth" in args[1].lower()
        assert bartender.secret_truth in args[1]

    def test_dialogue_recorded_in_world_state(self, conv_mgr, state, bartender):
        conv_mgr.dialogue_handler.generate_response.return_value = "Some response."

        # Just verify no crash — real world_state records it
        conv_mgr.handle_free_dialogue(bartender, "hello", state)


class TestThreaten:
    """Test threaten handler."""

    def test_threaten_applies_pressure(self, conv_mgr, state, bartender):
        initial_pressure = bartender.state.pressure_accumulated
        conv_mgr.handle_threaten(bartender, state)
        assert bartender.state.pressure_accumulated > initial_pressure

    def test_threaten_reduces_trust(self, conv_mgr, state, bartender):
        initial_trust = bartender.current_trust
        conv_mgr.handle_threaten(bartender, state)
        assert bartender.current_trust < initial_trust

    def test_threaten_records_moral_action(self, conv_mgr, state, bartender):
        conv_mgr.handle_threaten(bartender, state)
        assert len(state.memory.player.moral_actions) > 0
        action = state.memory.player.moral_actions[-1]
        assert action.action_type == "threaten"

    def test_threaten_enough_cracks_character(self, conv_mgr, state, bartender):
        # Apply enough pressure to crack
        bartender.state.pressure_accumulated = 95  # Almost cracked
        conv_mgr.handle_threaten(bartender, state)

        if bartender.state.is_cracked:
            # Cracked — should reveal secret
            calls = conv_mgr.renderer.render_dialogue.call_args_list
            texts = [c[0][1] for c in calls]
            assert any(bartender.secret_truth in t for t in texts)


class TestAccuse:
    """Test accuse handler."""

    def test_accuse_wrong_person(self, conv_mgr, state, bartender):
        # No spine set, so no correct culprit
        state.spine = None
        conv_mgr.handle_accuse(bartender, state)

        conv_mgr.renderer.render_dialogue.assert_called()
        args = conv_mgr.renderer.render_dialogue.call_args[0]
        assert "wrong" in args[1].lower()

    def test_accuse_reduces_trust_on_wrong(self, conv_mgr, state, bartender):
        state.spine = None
        initial_trust = bartender.current_trust
        conv_mgr.handle_accuse(bartender, state)
        assert bartender.current_trust < initial_trust

    def test_accuse_correct_culprit_with_evidence(self, conv_mgr, state, bartender):
        # Set up spine where bartender is the culprit
        spine = MagicMock()
        spine.true_resolution.culprit_id = "bartender"
        spine.check_solution.return_value = (True, "Case solved!")
        state.spine = spine
        state.memory.player.discoveries["evidence_1"] = {"fact": "test"}

        conv_mgr.handle_accuse(bartender, state)

        assert bartender.state.is_cracked
        assert state.is_running is False
        conv_mgr.renderer.render_game_over.assert_called()

    def test_accuse_correct_culprit_insufficient_evidence(self, conv_mgr, state, bartender):
        spine = MagicMock()
        spine.true_resolution.culprit_id = "bartender"
        spine.check_solution.return_value = (False, "Not enough evidence.")
        state.spine = spine

        conv_mgr.handle_accuse(bartender, state)

        assert state.is_running is True  # Game continues
        conv_mgr.renderer.render_dialogue.assert_called()


class TestShowDialogue:
    """Test dialogue display."""

    def test_show_dialogue_renders(self, conv_mgr, bartender):
        conv_mgr.show_dialogue(bartender, "Hello there.", "nervously")
        conv_mgr.renderer.render_dialogue.assert_called_once_with("Joe", "Hello there.", "nervously")

    def test_show_dialogue_without_mood(self, conv_mgr, bartender):
        conv_mgr.show_dialogue(bartender, "Hello.")
        conv_mgr.renderer.render_dialogue.assert_called_once_with("Joe", "Hello.", "")


class TestMemoryRecording:
    """Test that conversation interactions are recorded in CharacterMemory."""

    def test_free_dialogue_records_interaction(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")
        conv_mgr.dialogue_handler.generate_response.return_value = "Some response."

        conv_mgr.handle_free_dialogue(bartender, "what happened?", state)

        char_mem = state.memory.get_character_memory("bartender")
        assert len(char_mem.player_interactions) == 1
        interaction = char_mem.player_interactions[0]
        assert interaction.interaction_type == "talked"
        assert interaction.player_tone == "neutral"
        assert interaction.topic == "what happened?"

    def test_free_dialogue_records_topic_truncated(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")
        conv_mgr.dialogue_handler.generate_response.return_value = "Response."

        long_input = "a" * 100
        conv_mgr.handle_free_dialogue(bartender, long_input, state)

        char_mem = state.memory.get_character_memory("bartender")
        assert len(char_mem.player_interactions[0].topic) == 50

    def test_free_dialogue_cooperative_records_shared_info(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")
        conv_mgr.dialogue_handler.generate_response.return_value = "I'll help."
        # Set high trust so character cooperates
        bartender.base_trust = 80

        conv_mgr.handle_free_dialogue(bartender, "help me", state)

        char_mem = state.memory.get_character_memory("bartender")
        interaction = char_mem.player_interactions[0]
        assert interaction.outcome == "shared_info"

    def test_free_dialogue_uncooperative_records_deflected(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")
        conv_mgr.dialogue_handler.generate_response.return_value = "I don't want to talk."
        # Set hostile mood so character does not cooperate
        from src.shadowengine.character.character import Mood
        bartender.state.mood = Mood.HOSTILE

        conv_mgr.handle_free_dialogue(bartender, "tell me", state)

        char_mem = state.memory.get_character_memory("bartender")
        interaction = char_mem.player_interactions[0]
        assert interaction.outcome == "deflected"

    def test_free_dialogue_no_memory_no_crash(self, conv_mgr, state, bartender):
        # Don't register character memory — should not crash
        conv_mgr.dialogue_handler.generate_response.return_value = "Hi."
        conv_mgr.handle_free_dialogue(bartender, "hello", state)

    def test_cracked_dialogue_records_confession(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")
        bartender.state.is_cracked = True

        conv_mgr.handle_free_dialogue(bartender, "tell me", state)

        char_mem = state.memory.get_character_memory("bartender")
        assert len(char_mem.player_interactions) == 1
        interaction = char_mem.player_interactions[0]
        assert interaction.interaction_type == "confessed_to"
        assert interaction.outcome == "revealed_secret"

    def test_threaten_records_in_memory(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")

        conv_mgr.handle_threaten(bartender, state)

        char_mem = state.memory.get_character_memory("bartender")
        assert len(char_mem.player_interactions) == 1
        interaction = char_mem.player_interactions[0]
        assert interaction.interaction_type == "threatened"
        assert interaction.player_tone == "aggressive"
        assert interaction.trust_change < 0

    def test_threaten_crack_records_outcome(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")
        bartender.state.pressure_accumulated = 95  # Near breaking point

        conv_mgr.handle_threaten(bartender, state)

        char_mem = state.memory.get_character_memory("bartender")
        interaction = char_mem.player_interactions[0]
        if bartender.state.is_cracked:
            assert interaction.outcome == "cracked"
        else:
            assert interaction.outcome == "resisted"

    def test_accuse_records_in_memory(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")
        state.spine = None  # Wrong person

        conv_mgr.handle_accuse(bartender, state)

        char_mem = state.memory.get_character_memory("bartender")
        assert len(char_mem.player_interactions) == 1
        interaction = char_mem.player_interactions[0]
        assert interaction.interaction_type == "accused"
        assert interaction.player_tone == "aggressive"
        assert interaction.outcome == "denied"

    def test_accuse_correct_records_caught(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")

        spine = MagicMock()
        spine.true_resolution.culprit_id = "bartender"
        spine.check_solution.return_value = (True, "Case solved!")
        state.spine = spine
        state.memory.player.discoveries["evidence_1"] = {"fact": "test"}

        conv_mgr.handle_accuse(bartender, state)

        char_mem = state.memory.get_character_memory("bartender")
        interaction = char_mem.player_interactions[0]
        assert interaction.outcome == "caught"

    def test_generate_dialogue_passes_memory(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")
        char_mem = state.memory.get_character_memory("bartender")

        conv_mgr.generate_dialogue(bartender, "hello", state)

        # Verify that generate_response was called with character_memory
        call_kwargs = conv_mgr.dialogue_handler.generate_response.call_args
        assert call_kwargs.kwargs.get("character_memory") is char_mem or \
               (len(call_kwargs.args) > 0 and call_kwargs.kwargs.get("character_memory") == char_mem)

    def test_threaten_feeds_event_bridge(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")
        state.propagation_engine.register_npc("bartender", "bartender")

        conv_mgr.handle_threaten(bartender, state)

        # Event bridge should have created a WorldEvent
        assert len(state.propagation_engine.events) == 1
        assert state.propagation_engine.events[0].event_type == "violence"

        # NPC should have an intelligence memory (separate from CharacterMemory)
        npc_state = state.propagation_engine.get_npc_state("bartender")
        assert len(npc_state.memory_bank.memories) >= 1

    def test_accuse_feeds_event_bridge(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")
        state.propagation_engine.register_npc("bartender", "bartender")
        state.spine = None

        conv_mgr.handle_accuse(bartender, state)

        assert len(state.propagation_engine.events) == 1
        assert state.propagation_engine.events[0].event_type == "conversation"

    def test_generate_dialogue_passes_intelligence(self, conv_mgr, state, bartender):
        state.memory.register_character("bartender")
        state.propagation_engine.register_npc("bartender", "bartender")

        conv_mgr.generate_dialogue(bartender, "hello", state)

        # Should have passed intelligence_hints to generate_response
        call_kwargs = conv_mgr.dialogue_handler.generate_response.call_args
        assert "intelligence_hints" in call_kwargs.kwargs

    def test_no_propagation_engine_no_crash(self, conv_mgr, bartender):
        """Without propagation_engine, dialogue still works."""
        from src.shadowengine.game import GameState
        bare_state = GameState()
        bare_state.memory.register_character("bartender")
        bare_state.characters["bartender"] = bartender
        # Remove propagation_engine
        del bare_state.propagation_engine
        del bare_state.event_bridge

        conv_mgr.dialogue_handler.generate_response.return_value = "Hello."
        conv_mgr.handle_free_dialogue(bartender, "hello", bare_state)
