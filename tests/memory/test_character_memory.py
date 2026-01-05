"""
Tests for Character Memory - what NPCs believe.

These tests verify that character memory correctly:
- Tracks beliefs with confidence levels
- Records player interactions
- Manages knowledge and suspicions
- Serializes/deserializes correctly
"""

import pytest
from shadowengine.memory import CharacterMemory, Belief
from shadowengine.memory.character_memory import BeliefConfidence, PlayerInteraction


class TestCharacterMemoryBasics:
    """Basic character memory functionality."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_create_character_memory(self, character_memory):
        """Character memory initializes correctly."""
        assert character_memory.character_id == "test_character"
        assert len(character_memory.beliefs) == 0
        assert len(character_memory.knowledge) == 0

    @pytest.mark.unit
    @pytest.mark.memory
    def test_add_belief(self, character_memory):
        """Can add beliefs to character."""
        belief = character_memory.add_belief(
            subject="murder",
            content="I think Bob did it",
            confidence=BeliefConfidence.SUSPICIOUS,
            source="overheard conversation",
            timestamp=10
        )

        assert len(character_memory.beliefs) == 1
        assert belief.subject == "murder"
        assert belief.confidence == BeliefConfidence.SUSPICIOUS

    @pytest.mark.unit
    @pytest.mark.memory
    def test_add_knowledge(self, character_memory):
        """Can add knowledge facts."""
        character_memory.add_knowledge("saw_alice_at_noon")
        character_memory.add_knowledge("knows_secret_passage")

        assert character_memory.knows("saw_alice_at_noon")
        assert character_memory.knows("knows_secret_passage")
        assert not character_memory.knows("unknown_fact")


class TestCharacterMemoryBeliefs:
    """Belief management functionality."""

    @pytest.fixture
    def character_with_beliefs(self, character_memory):
        """Character with multiple beliefs."""
        character_memory.add_belief(
            subject="alice",
            content="Alice is suspicious",
            confidence=BeliefConfidence.UNCERTAIN,
            source="gut feeling",
            timestamp=5
        )
        character_memory.add_belief(
            subject="alice",
            content="Alice was at the scene",
            confidence=BeliefConfidence.CERTAIN,
            source="witnessed",
            timestamp=10
        )
        character_memory.add_belief(
            subject="bob",
            content="Bob is innocent",
            confidence=BeliefConfidence.CONFIDENT,
            source="alibi verified",
            timestamp=15
        )
        return character_memory

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_beliefs_about_subject(self, character_with_beliefs):
        """Can query beliefs about a subject."""
        alice_beliefs = character_with_beliefs.get_beliefs_about("alice")
        assert len(alice_beliefs) == 2

        bob_beliefs = character_with_beliefs.get_beliefs_about("bob")
        assert len(bob_beliefs) == 1

    @pytest.mark.unit
    @pytest.mark.memory
    def test_belief_confidence_levels(self, character_memory):
        """Beliefs can have different confidence levels."""
        for confidence in BeliefConfidence:
            character_memory.add_belief(
                subject=f"test_{confidence.value}",
                content="Test belief",
                confidence=confidence,
                source="test",
                timestamp=0
            )

        assert len(character_memory.beliefs) == 4

    @pytest.mark.unit
    @pytest.mark.memory
    def test_belief_truth_tracking(self, character_memory):
        """Beliefs track whether they're objectively true."""
        true_belief = character_memory.add_belief(
            subject="fact",
            content="The sky is blue",
            confidence=BeliefConfidence.CERTAIN,
            source="observed",
            timestamp=0,
            is_true=True
        )

        false_belief = character_memory.add_belief(
            subject="lie",
            content="I was told a lie",
            confidence=BeliefConfidence.CONFIDENT,
            source="told by liar",
            timestamp=0,
            is_true=False
        )

        assert true_belief.is_true is True
        assert false_belief.is_true is False


class TestCharacterMemorySuspicions:
    """Suspicion tracking functionality."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_add_suspicion(self, character_memory):
        """Can add suspicions about others."""
        character_memory.add_suspicion("alice", 0.3)

        assert character_memory.get_suspicion("alice") == 0.3
        assert character_memory.get_suspicion("unknown") == 0.0

    @pytest.mark.unit
    @pytest.mark.memory
    def test_suspicion_accumulates(self, character_memory):
        """Suspicion accumulates over time."""
        character_memory.add_suspicion("alice", 0.3)
        character_memory.add_suspicion("alice", 0.4)

        assert character_memory.get_suspicion("alice") == 0.7

    @pytest.mark.unit
    @pytest.mark.memory
    def test_suspicion_caps_at_one(self, character_memory):
        """Suspicion cannot exceed 1.0."""
        character_memory.add_suspicion("alice", 0.8)
        character_memory.add_suspicion("alice", 0.5)

        assert character_memory.get_suspicion("alice") == 1.0

    @pytest.mark.unit
    @pytest.mark.memory
    def test_suspicion_floors_at_zero(self, character_memory):
        """Suspicion cannot go below 0.0."""
        character_memory.add_suspicion("alice", -0.5)

        assert character_memory.get_suspicion("alice") == 0.0


class TestCharacterMemoryInteractions:
    """Player interaction tracking."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_record_player_interaction(self, character_memory):
        """Can record player interactions."""
        interaction = character_memory.record_player_interaction(
            timestamp=10,
            interaction_type="interrogation",
            player_tone="aggressive",
            outcome="refused",
            trust_change=-5,
            topic="alibi"
        )

        assert len(character_memory.player_interactions) == 1
        assert interaction.player_tone == "aggressive"
        assert interaction.trust_change == -5

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_recent_interactions(self, character_memory):
        """Can get recent interactions."""
        for i in range(10):
            character_memory.record_player_interaction(
                timestamp=i,
                interaction_type="talk",
                player_tone="neutral",
                outcome="cooperated",
                trust_change=1
            )

        recent = character_memory.get_recent_interactions(3)
        assert len(recent) == 3
        assert recent[-1].timestamp == 9

    @pytest.mark.unit
    @pytest.mark.memory
    def test_total_trust_change(self, character_memory):
        """Can calculate total trust change."""
        character_memory.record_player_interaction(
            timestamp=0, interaction_type="help",
            player_tone="friendly", outcome="grateful",
            trust_change=10
        )
        character_memory.record_player_interaction(
            timestamp=5, interaction_type="threaten",
            player_tone="aggressive", outcome="scared",
            trust_change=-15
        )
        character_memory.record_player_interaction(
            timestamp=10, interaction_type="apologize",
            player_tone="friendly", outcome="forgave",
            trust_change=5
        )

        assert character_memory.total_trust_change() == 0


class TestCharacterMemorySerialization:
    """Serialization and deserialization."""

    @pytest.fixture
    def complex_character_memory(self, character_memory):
        """Character memory with complex state."""
        character_memory.add_belief(
            subject="crime",
            content="I know who did it",
            confidence=BeliefConfidence.CERTAIN,
            source="witnessed",
            timestamp=100
        )
        character_memory.add_knowledge("secret_1")
        character_memory.add_knowledge("secret_2")
        character_memory.add_suspicion("alice", 0.7)
        character_memory.record_player_interaction(
            timestamp=50,
            interaction_type="interrogation",
            player_tone="neutral",
            outcome="cooperated",
            trust_change=5,
            topic="the crime"
        )
        return character_memory

    @pytest.mark.unit
    @pytest.mark.memory
    def test_serialize_character_memory(self, complex_character_memory):
        """Can serialize character memory."""
        data = complex_character_memory.to_dict()

        assert data["character_id"] == "test_character"
        assert len(data["beliefs"]) == 1
        assert len(data["knowledge"]) == 2
        assert "alice" in data["suspicions"]

    @pytest.mark.unit
    @pytest.mark.memory
    def test_deserialize_character_memory(self, complex_character_memory):
        """Can deserialize character memory."""
        data = complex_character_memory.to_dict()
        restored = CharacterMemory.from_dict(data)

        assert restored.character_id == "test_character"
        assert len(restored.beliefs) == 1
        assert restored.knows("secret_1")
        assert restored.get_suspicion("alice") == 0.7
        assert len(restored.player_interactions) == 1
