"""Tests for LLM integration with game systems."""

import pytest
from shadowengine.llm import (
    LLMConfig,
    LLMBackend,
    MockLLMClient,
    LLMIntegration,
    DialogueGenerator,
    BehaviorEvaluator,
    CharacterPrompt,
)


class TestDialogueGenerator:
    """Tests for DialogueGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a dialogue generator with mock client."""
        config = LLMConfig(backend=LLMBackend.MOCK)
        client = MockLLMClient(config, responses={
            "watch": "I don't know anything about any watch.",
            "morning": "I was in the kitchen all morning.",
        })
        return DialogueGenerator(client)

    @pytest.fixture
    def character_prompt(self):
        """Create a test character prompt."""
        return CharacterPrompt(
            name="Test Character",
            description="A suspicious person",
            archetype="Guilty",
            trust=40,
            mood="nervous",
            secret_truth="I took the money",
            public_lie="I was elsewhere"
        )

    def test_generate_with_matching_keyword(self, generator, character_prompt):
        """Test generating dialogue with matching keyword."""
        result = generator.generate(
            character_prompt,
            "Tell me about the watch"
        )
        assert result.success
        assert "watch" in result.text.lower()

    def test_generate_fallback_when_no_match(self, generator, character_prompt):
        """Test fallback response when no keyword matches."""
        result = generator.generate(
            character_prompt,
            "What's your favorite color?"
        )
        assert result.success
        # Should use default response

    def test_fallback_response_by_mood(self, generator):
        """Test fallback responses vary by mood."""
        # Create generator without keyword responses
        fallback_gen = DialogueGenerator(MockLLMClient(LLMConfig()))

        nervous_result = fallback_gen._fallback_response("nervous")
        assert nervous_result.fallback_used
        assert nervous_result.success

        hostile_result = fallback_gen._fallback_response("angry")
        assert hostile_result.fallback_used
        assert hostile_result.success

    def test_reveals_info_detection(self, generator):
        """Test detection of revealed information."""
        # "took" and "money" are in the secret
        assert generator._check_reveals_info(
            "I took the money from the safe",
            "I took the money"
        )
        # No overlap
        assert not generator._check_reveals_info(
            "The weather is nice",
            "I stole the diamonds"
        )


class TestBehaviorEvaluator:
    """Tests for BehaviorEvaluator."""

    @pytest.fixture
    def evaluator(self):
        """Create a behavior evaluator with mock client."""
        config = LLMConfig(backend=LLMBackend.MOCK)
        client = MockLLMClient(config, responses={
            "threat": '{"action": "flee", "intensity": 0.9, "narrative": "They run away scared."}',
            "player": '{"action": "approach", "intensity": 0.5}',
        })
        return BehaviorEvaluator(client)

    def test_evaluate_returns_result(self, evaluator):
        """Test that evaluate returns a BehaviorResult."""
        result = evaluator.evaluate(
            npc_name="Guard",
            npc_type="hostile",
            personality="aggressive",
            state="patrolling",
            stimulus="player spotted",
            distance=5.0,
            threat_level=0.5,
            time="night"
        )
        assert result is not None
        assert result.action in ["flee", "hide", "approach", "ignore", "alert", "investigate"]

    def test_parse_json_response(self, evaluator):
        """Test parsing JSON behavior response."""
        result = evaluator._parse_behavior_response(
            '{"action": "flee", "intensity": 0.8, "target": "door", "narrative": "Runs to door"}'
        )
        assert result.action == "flee"
        assert result.intensity == 0.8
        assert result.target == "door"
        assert result.narrative == "Runs to door"

    def test_parse_malformed_response(self, evaluator):
        """Test parsing malformed response extracts action."""
        result = evaluator._parse_behavior_response(
            "The guard decides to flee from the threat."
        )
        assert result.action == "flee"
        assert result.success

    def test_parse_completely_invalid(self, evaluator):
        """Test parsing completely invalid response defaults to ignore."""
        result = evaluator._parse_behavior_response(
            "Some random text with no actions"
        )
        assert result.action == "ignore"

    def test_fallback_high_threat_coward(self, evaluator):
        """Test fallback for high threat with coward personality."""
        result = evaluator._fallback_behavior("nervous coward", 0.8)
        assert result.action == "flee"
        assert result.intensity > 0.7

    def test_fallback_high_threat_brave(self, evaluator):
        """Test fallback for high threat with brave personality."""
        result = evaluator._fallback_behavior("brave aggressive", 0.8)
        assert result.action == "approach"

    def test_fallback_medium_threat(self, evaluator):
        """Test fallback for medium threat."""
        result = evaluator._fallback_behavior("neutral", 0.5)
        assert result.action == "investigate"

    def test_fallback_low_threat(self, evaluator):
        """Test fallback for low threat."""
        result = evaluator._fallback_behavior("calm", 0.1)
        assert result.action == "ignore"


class TestLLMIntegration:
    """Tests for main LLMIntegration class."""

    @pytest.fixture
    def integration(self):
        """Create integration with mock backend."""
        config = LLMConfig(backend=LLMBackend.MOCK)
        return LLMIntegration(config)

    def test_is_available(self, integration):
        """Test availability check."""
        assert integration.is_available  # Mock is always available

    def test_generate_dialogue(self, integration):
        """Test dialogue generation."""
        result = integration.generate_dialogue(
            name="Butler",
            description="The family butler",
            archetype="Guilty",
            trust=30,
            mood="nervous",
            secret_truth="I did it",
            public_lie="I was away",
            question="Where were you?"
        )
        assert result.success
        assert len(result.text) > 0

    def test_evaluate_behavior(self, integration):
        """Test behavior evaluation."""
        result = integration.evaluate_behavior(
            npc_name="Cat",
            npc_type="animal",
            personality="skittish",
            state="resting",
            stimulus="loud noise",
            distance=3.0,
            threat_level=0.4,
            time="afternoon"
        )
        assert result.action in ["flee", "hide", "approach", "ignore", "alert", "investigate"]

    def test_generate_narrative(self, integration):
        """Test narrative generation."""
        result = integration.generate_narrative(
            location="dark alley",
            time="midnight",
            weather="rain",
            characters=["suspicious figure"],
            events=["gunshot heard"],
            action="crept forward"
        )
        assert len(result) > 0

    def test_fallback_narrative(self, integration):
        """Test fallback narrative."""
        result = integration._fallback_narrative("study", "looked around")
        assert "study" in result
        assert "looked around" in result

    def test_get_circuit_evaluator(self, integration):
        """Test getting circuit evaluator callback."""
        evaluator = integration.get_circuit_evaluator()
        assert callable(evaluator)


class TestLLMIntegrationWithUnavailableBackend:
    """Tests for LLM integration when backend is unavailable."""

    @pytest.fixture
    def integration(self):
        """Create integration with unavailable Ollama."""
        config = LLMConfig(
            backend=LLMBackend.OLLAMA,
            base_url="http://localhost:99999"  # Invalid port
        )
        return LLMIntegration(config)

    def test_fallback_dialogue(self, integration):
        """Test that dialogue falls back gracefully."""
        result = integration.generate_dialogue(
            name="Butler",
            description="A butler",
            archetype="Neutral",
            trust=50,
            mood="calm",
            secret_truth="",
            public_lie="",
            question="Hello?"
        )
        # Should still return a result using fallback
        assert result.success
        assert result.fallback_used

    def test_fallback_behavior(self, integration):
        """Test that behavior falls back gracefully."""
        result = integration.evaluate_behavior(
            npc_name="Guard",
            npc_type="hostile",
            personality="aggressive",
            state="alert",
            stimulus="noise",
            distance=5.0,
            threat_level=0.6,
            time="night"
        )
        # Should still return a result
        assert result.action is not None

    def test_fallback_narrative(self, integration):
        """Test that narrative falls back gracefully."""
        result = integration.generate_narrative(
            location="office",
            time="evening",
            weather="clear",
            characters=[],
            events=[],
            action="entered"
        )
        assert len(result) > 0
