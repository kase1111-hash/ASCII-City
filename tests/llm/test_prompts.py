"""Tests for LLM prompt templates."""

import pytest
from shadowengine.llm import (
    CharacterPrompt,
    NarrativePrompt,
    BehaviorPrompt,
)
from shadowengine.llm.prompts import PromptTemplate


class TestPromptTemplate:
    """Tests for base PromptTemplate."""

    def test_render_with_variables(self):
        """Test rendering with variables."""
        template = PromptTemplate(
            template="Hello, $name! You are $role.",
            variables={"name": "Detective", "role": "investigating"}
        )
        result = template.render()
        assert result == "Hello, Detective! You are investigating."

    def test_render_with_overrides(self):
        """Test rendering with variable overrides."""
        template = PromptTemplate(
            template="Hello, $name!",
            variables={"name": "Default"}
        )
        result = template.render(name="Override")
        assert result == "Hello, Override!"

    def test_missing_variables_stay(self):
        """Test that missing variables are kept as-is."""
        template = PromptTemplate(template="Hello, $name!")
        result = template.render()
        assert "$name" in result


class TestCharacterPrompt:
    """Tests for CharacterPrompt."""

    @pytest.fixture
    def butler_prompt(self):
        """Create a butler character prompt."""
        return CharacterPrompt(
            name="Mr. Blackwood",
            description="The family butler, nervous and evasive",
            archetype="Guilty",
            trust=30,
            mood="nervous",
            secret_truth="I stole the watch to pay my gambling debts",
            public_lie="I was polishing silver all morning"
        )

    def test_system_prompt_contains_character_info(self, butler_prompt):
        """Test that system prompt contains character information."""
        system = butler_prompt.get_system_prompt()
        assert "Mr. Blackwood" in system
        assert "butler" in system.lower()
        assert "Guilty" in system
        assert "nervous" in system
        assert "gambling debts" in system

    def test_response_prompt_contains_question(self, butler_prompt):
        """Test that response prompt contains the question."""
        response = butler_prompt.get_response_prompt(
            question="Where were you this morning?",
            location="study"
        )
        assert "Where were you this morning?" in response
        assert "study" in response
        assert "Mr. Blackwood" in response

    def test_response_prompt_with_topics(self, butler_prompt):
        """Test response prompt with discussed topics."""
        response = butler_prompt.get_response_prompt(
            question="About the watch?",
            topics_discussed=["morning routine", "other staff"]
        )
        assert "morning routine" in response
        assert "other staff" in response

    def test_response_prompt_with_evidence(self, butler_prompt):
        """Test response prompt with evidence."""
        response = butler_prompt.get_response_prompt(
            question="Explain this!",
            evidence=["pawn ticket", "gambling receipt"]
        )
        assert "pawn ticket" in response
        assert "gambling receipt" in response


class TestNarrativePrompt:
    """Tests for NarrativePrompt."""

    def test_system_prompt_contains_guidelines(self):
        """Test that system prompt has noir guidelines."""
        prompt = NarrativePrompt()
        system = prompt.get_system_prompt()
        assert "noir" in system.lower()
        assert "narrator" in system.lower()
        assert "atmospheric" in system.lower()

    def test_scene_prompt_contains_all_elements(self):
        """Test that scene prompt contains all elements."""
        prompt = NarrativePrompt()
        scene = prompt.get_scene_prompt(
            location="study",
            time="midnight",
            weather="rain",
            characters=["butler", "maid"],
            events=["watch stolen", "argument heard"],
            action="entered the room"
        )
        assert "study" in scene
        assert "midnight" in scene
        assert "rain" in scene
        assert "butler" in scene
        assert "maid" in scene
        assert "entered the room" in scene

    def test_scene_prompt_with_empty_lists(self):
        """Test scene prompt handles empty lists."""
        prompt = NarrativePrompt()
        scene = prompt.get_scene_prompt(
            location="alley",
            time="dawn",
            weather="fog",
            characters=[],
            events=[],
            action="looked around"
        )
        assert "alley" in scene
        assert "none" in scene  # For empty lists


class TestBehaviorPrompt:
    """Tests for BehaviorPrompt."""

    def test_system_prompt_contains_json_format(self):
        """Test that system prompt specifies JSON output."""
        prompt = BehaviorPrompt()
        system = prompt.get_system_prompt()
        assert "JSON" in system
        assert "action" in system
        assert "intensity" in system

    def test_evaluation_prompt_contains_context(self):
        """Test that evaluation prompt contains all context."""
        prompt = BehaviorPrompt()
        evaluation = prompt.get_evaluation_prompt(
            npc_name="Guard",
            npc_type="hostile",
            personality="aggressive, territorial",
            state="patrolling",
            stimulus="player spotted",
            distance=5.0,
            threat_level=0.7,
            time="night",
            nearby_npcs=["other_guard"]
        )
        assert "Guard" in evaluation
        assert "hostile" in evaluation
        assert "aggressive" in evaluation
        assert "patrolling" in evaluation
        assert "player spotted" in evaluation
        assert "5.0" in evaluation
        assert "70" in evaluation  # 0.7 as percentage
        assert "night" in evaluation
        assert "other_guard" in evaluation

    def test_evaluation_prompt_with_no_nearby(self):
        """Test evaluation prompt with no nearby NPCs."""
        prompt = BehaviorPrompt()
        evaluation = prompt.get_evaluation_prompt(
            npc_name="Cat",
            npc_type="animal",
            personality="skittish",
            state="sleeping",
            stimulus="loud noise",
            distance=10.0,
            threat_level=0.3,
            time="afternoon",
            nearby_npcs=[]
        )
        assert "none" in evaluation  # For empty nearby list
