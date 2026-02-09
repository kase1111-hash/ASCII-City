"""Tests for DialogueHandler — LLM prompt construction and memory context building."""

import pytest
from unittest.mock import MagicMock

from src.shadowengine.generation.dialogue_handler import DialogueHandler
from src.shadowengine.character import Character, Archetype
from src.shadowengine.memory.character_memory import (
    CharacterMemory, Belief, BeliefConfidence, PlayerInteraction,
)
from src.shadowengine.llm.client import MockLLMClient, LLMConfig, LLMBackend, LLMResponse


@pytest.fixture
def mock_llm():
    config = LLMConfig(backend=LLMBackend.MOCK)
    return MockLLMClient(config)


@pytest.fixture
def world_state():
    ws = MagicMock()
    ws.get_npc_knowledge.return_value = ""
    ws.get_npc_context.return_value = {"relationships": []}
    ws.generation_memory.get_npc_dialogue_history.return_value = ""
    return ws


@pytest.fixture
def handler(mock_llm, world_state):
    return DialogueHandler(llm_client=mock_llm, world_state=world_state)


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


class TestBuildMemoryContext:
    """Test _build_memory_context formats CharacterMemory into prompt text."""

    def test_none_memory_returns_empty(self):
        result = DialogueHandler._build_memory_context(None)
        assert result == ""

    def test_empty_memory_returns_empty(self):
        mem = CharacterMemory("npc1")
        result = DialogueHandler._build_memory_context(mem)
        assert result == ""

    def test_beliefs_formatted(self):
        mem = CharacterMemory("npc1")
        mem.add_belief(
            subject="player",
            content="The detective examined the bloody knife",
            confidence=BeliefConfidence.CERTAIN,
            source="witnessed",
            timestamp=10,
        )

        result = DialogueHandler._build_memory_context(mem)

        assert "THINGS YOU BELIEVE" in result
        assert "certain" in result
        assert "bloody knife" in result
        assert "witnessed" in result

    def test_only_last_5_beliefs_used(self):
        mem = CharacterMemory("npc1")
        for i in range(8):
            mem.add_belief(
                subject=f"event_{i}",
                content=f"Belief number {i}",
                confidence=BeliefConfidence.UNCERTAIN,
                source="heard",
                timestamp=i,
            )

        result = DialogueHandler._build_memory_context(mem)

        # First 3 should be excluded, last 5 included
        assert "Belief number 0" not in result
        assert "Belief number 2" not in result
        assert "Belief number 3" in result
        assert "Belief number 7" in result

    def test_suspicions_formatted(self):
        mem = CharacterMemory("npc1")
        mem.add_suspicion("suspect_a", 0.7)
        mem.add_suspicion("suspect_b", 0.3)

        result = DialogueHandler._build_memory_context(mem)

        assert "YOUR SUSPICIONS" in result
        assert "suspect_a" in result
        assert "70%" in result
        assert "suspect_b" in result

    def test_low_suspicions_filtered_out(self):
        mem = CharacterMemory("npc1")
        mem.add_suspicion("barely_suspicious", 0.05)

        result = DialogueHandler._build_memory_context(mem)

        # 0.05 is below the 0.1 threshold, so filtered out
        assert "barely_suspicious" not in result

    def test_interactions_formatted(self):
        mem = CharacterMemory("npc1")
        mem.record_player_interaction(
            timestamp=5,
            interaction_type="talked",
            player_tone="friendly",
            outcome="shared_info",
            trust_change=5,
            topic="the victim",
        )

        result = DialogueHandler._build_memory_context(mem)

        assert "YOUR HISTORY WITH THE DETECTIVE" in result
        assert "talked" in result
        assert "the victim" in result
        assert "friendly" in result
        assert "shared_info" in result

    def test_interactions_without_topic(self):
        mem = CharacterMemory("npc1")
        mem.record_player_interaction(
            timestamp=5,
            interaction_type="threatened",
            player_tone="aggressive",
            outcome="resisted",
            trust_change=-10,
        )

        result = DialogueHandler._build_memory_context(mem)

        assert "threatened" in result
        assert "aggressive" in result

    def test_positive_trust_change_shows_warmer(self):
        mem = CharacterMemory("npc1")
        mem.record_player_interaction(
            timestamp=1,
            interaction_type="talked",
            player_tone="friendly",
            outcome="cooperated",
            trust_change=10,
        )

        result = DialogueHandler._build_memory_context(mem)

        assert "warmer toward" in result
        assert "+10" in result

    def test_negative_trust_change_shows_colder(self):
        mem = CharacterMemory("npc1")
        mem.record_player_interaction(
            timestamp=1,
            interaction_type="threatened",
            player_tone="aggressive",
            outcome="resisted",
            trust_change=-15,
        )

        result = DialogueHandler._build_memory_context(mem)

        assert "colder toward" in result
        assert "-15" in result

    def test_zero_trust_change_omitted(self):
        mem = CharacterMemory("npc1")
        mem.record_player_interaction(
            timestamp=1,
            interaction_type="talked",
            player_tone="neutral",
            outcome="deflected",
            trust_change=0,
        )

        result = DialogueHandler._build_memory_context(mem)

        assert "warmer" not in result
        assert "colder" not in result

    def test_full_memory_has_all_sections(self):
        mem = CharacterMemory("npc1")
        mem.add_belief(
            subject="clue", content="The knife was moved",
            confidence=BeliefConfidence.CONFIDENT, source="witnessed",
            timestamp=1,
        )
        mem.add_suspicion("suspect_x", 0.6)
        mem.record_player_interaction(
            timestamp=2, interaction_type="talked",
            player_tone="neutral", outcome="shared_info",
            trust_change=5, topic="the crime",
        )

        result = DialogueHandler._build_memory_context(mem)

        assert "THINGS YOU BELIEVE" in result
        assert "YOUR SUSPICIONS" in result
        assert "YOUR HISTORY WITH THE DETECTIVE" in result
        assert "warmer toward" in result


class TestBuildSystemPrompt:
    """Test system prompt includes memory context."""

    def test_system_prompt_includes_memory(self, bartender):
        mem = CharacterMemory("bartender")
        mem.add_belief(
            subject="player", content="Saw the detective arrive",
            confidence=BeliefConfidence.CERTAIN, source="witnessed",
            timestamp=1,
        )

        memory_context = DialogueHandler._build_memory_context(mem)
        prompt = DialogueHandler._build_system_prompt(
            character=bartender,
            relationships_str="",
            npc_knowledge="",
            story_context="A murder mystery.",
            memory_context=memory_context,
        )

        assert "THINGS YOU BELIEVE" in prompt
        assert "detective arrive" in prompt
        assert bartender.name in prompt

    def test_system_prompt_without_memory(self, bartender):
        prompt = DialogueHandler._build_system_prompt(
            character=bartender,
            relationships_str="",
            npc_knowledge="",
            story_context="A murder mystery.",
            memory_context="",
        )

        assert bartender.name in prompt
        assert "THINGS YOU BELIEVE" not in prompt

    def test_system_prompt_includes_rule_9(self, bartender):
        prompt = DialogueHandler._build_system_prompt(
            character=bartender,
            relationships_str="",
            npc_knowledge="",
            story_context="",
        )

        assert "previous interactions" in prompt.lower()


class TestGenerateResponse:
    """Test that generate_response passes memory through to prompt building."""

    def test_character_memory_passed_to_llm(self, handler, bartender, world_state):
        # Set up LLM to return a response
        handler.llm_client = MagicMock()
        handler.llm_client.chat.return_value = LLMResponse(
            text="I was here all night.", success=True,
        )

        mem = CharacterMemory("bartender")
        mem.add_belief(
            subject="crime", content="Someone was murdered",
            confidence=BeliefConfidence.CERTAIN, source="witnessed",
            timestamp=1,
        )

        result = handler.generate_response(
            character=bartender,
            player_input="What happened?",
            character_memory=mem,
        )

        assert result == "I was here all night."
        # Verify LLM was called with a system prompt containing memory context
        call_args = handler.llm_client.chat.call_args[0][0]
        system_prompt = call_args[0]["content"]
        assert "THINGS YOU BELIEVE" in system_prompt

    def test_no_memory_still_generates(self, handler, bartender):
        handler.llm_client = MagicMock()
        handler.llm_client.chat.return_value = LLMResponse(
            text="Hello, detective.", success=True,
        )

        result = handler.generate_response(
            character=bartender,
            player_input="Hello",
            character_memory=None,
        )

        assert result == "Hello, detective."

    def test_failed_llm_returns_none(self, handler, bartender):
        handler.llm_client = MagicMock()
        handler.llm_client.chat.return_value = LLMResponse(
            text="", success=False, error="timeout",
        )

        result = handler.generate_response(
            character=bartender,
            player_input="Hello",
        )

        assert result is None


class TestCleanResponse:
    """Test response cleaning."""

    def test_removes_character_prefix(self):
        result = DialogueHandler._clean_response("Joe: Hello there.", "Joe")
        assert result == "Hello there."

    def test_case_insensitive_prefix_removal(self):
        result = DialogueHandler._clean_response("joe: Hello there.", "Joe")
        assert result == "Hello there."

    def test_no_prefix_unchanged(self):
        result = DialogueHandler._clean_response("Hello there.", "Joe")
        assert result == "Hello there."

    def test_strips_whitespace(self):
        result = DialogueHandler._clean_response("  Hello there.  ", "Joe")
        assert result == "Hello there."
