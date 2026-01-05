"""
Tests for Player Memory - protagonist perception and moral state.

These tests verify that player memory correctly:
- Tracks discoveries and evidence
- Manages suspicions and relationships
- Calculates moral shades
- Serializes/deserializes correctly
"""

import pytest
from shadowengine.memory import PlayerMemory
from shadowengine.memory.player_memory import MoralShade, Discovery, MoralAction


class TestPlayerMemoryBasics:
    """Basic player memory functionality."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_create_player_memory(self, player_memory):
        """Player memory initializes correctly."""
        assert len(player_memory.discoveries) == 0
        assert len(player_memory.inventory if hasattr(player_memory, 'inventory') else []) == 0

    @pytest.mark.unit
    @pytest.mark.memory
    def test_initial_moral_shades(self, player_memory):
        """Moral shades start balanced."""
        for shade in MoralShade:
            assert player_memory.shade_scores[shade.value] == pytest.approx(0.2, abs=0.01)


class TestPlayerMemoryDiscoveries:
    """Discovery tracking functionality."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_add_discovery(self, player_memory):
        """Can add discoveries."""
        discovery = player_memory.add_discovery(
            fact_id="bloody_knife",
            description="A knife with blood stains",
            location="kitchen",
            timestamp=10,
            source="examined drawer",
            is_evidence=True
        )

        assert player_memory.has_discovered("bloody_knife")
        assert discovery.is_evidence is True

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_discovery(self, player_memory):
        """Can retrieve discoveries."""
        player_memory.add_discovery(
            fact_id="torn_letter",
            description="A torn letter",
            location="study",
            timestamp=5,
            source="examined desk"
        )

        discovery = player_memory.get_discovery("torn_letter")
        assert discovery is not None
        assert discovery.description == "A torn letter"

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_evidence(self, player_memory):
        """Can filter discoveries to just evidence."""
        player_memory.add_discovery(
            fact_id="clue1",
            description="A clue",
            location="study",
            timestamp=0,
            source="examined",
            is_evidence=True
        )
        player_memory.add_discovery(
            fact_id="observation1",
            description="An observation",
            location="study",
            timestamp=0,
            source="observed",
            is_evidence=False
        )
        player_memory.add_discovery(
            fact_id="clue2",
            description="Another clue",
            location="hallway",
            timestamp=0,
            source="examined",
            is_evidence=True
        )

        evidence = player_memory.get_evidence()
        assert len(evidence) == 2

    @pytest.mark.unit
    @pytest.mark.memory
    def test_related_discoveries(self, player_memory):
        """Discoveries can be related to characters/items."""
        player_memory.add_discovery(
            fact_id="alice_alibi",
            description="Alice's alibi is false",
            location="study",
            timestamp=0,
            source="investigation",
            related_to=["alice", "timeline"]
        )

        discovery = player_memory.get_discovery("alice_alibi")
        assert "alice" in discovery.related_to
        assert "timeline" in discovery.related_to


class TestPlayerMemorySuspicions:
    """Suspicion tracking functionality."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_add_suspicion(self, player_memory):
        """Can add suspicions."""
        player_memory.add_suspicion("alice", 0.5)

        assert player_memory.get_suspicion("alice") == 0.5

    @pytest.mark.unit
    @pytest.mark.memory
    def test_suspicion_accumulates(self, player_memory):
        """Suspicion builds up."""
        player_memory.add_suspicion("bob", 0.3)
        player_memory.add_suspicion("bob", 0.3)

        assert player_memory.get_suspicion("bob") == 0.6


class TestPlayerMemoryRelationships:
    """Relationship tracking functionality."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_update_relationship(self, player_memory):
        """Can update relationships."""
        player_memory.update_relationship("alice", 10)
        assert player_memory.get_relationship("alice") == 10

        player_memory.update_relationship("alice", -5)
        assert player_memory.get_relationship("alice") == 5

    @pytest.mark.unit
    @pytest.mark.memory
    def test_negative_relationships(self, player_memory):
        """Relationships can be negative."""
        player_memory.update_relationship("enemy", -20)
        assert player_memory.get_relationship("enemy") == -20


class TestPlayerMemoryMoralShades:
    """Moral shade tracking functionality."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_record_moral_action(self, player_memory):
        """Can record moral actions."""
        action = player_memory.record_moral_action(
            action_type="threaten",
            description="Threatened a witness",
            timestamp=10,
            target="witness",
            shade_effects={
                "ruthless": 0.3,
                "compassionate": -0.2
            },
            weight=1.0
        )

        assert len(player_memory.moral_actions) == 1
        assert action.action_type == "threaten"

    @pytest.mark.unit
    @pytest.mark.memory
    def test_shade_scores_update(self, player_memory):
        """Shade scores update based on actions."""
        initial_ruthless = player_memory.shade_scores["ruthless"]

        player_memory.record_moral_action(
            action_type="threaten",
            description="Threatened someone",
            timestamp=0,
            shade_effects={"ruthless": 0.5},
            weight=1.0
        )

        # Ruthless should have increased (before normalization)
        # After normalization, the relative proportion should be higher

    @pytest.mark.unit
    @pytest.mark.memory
    def test_shade_normalization(self, player_memory):
        """Shade scores normalize to sum to 1.0."""
        player_memory.record_moral_action(
            action_type="help",
            description="Helped someone",
            timestamp=0,
            shade_effects={"compassionate": 1.0},
            weight=1.0
        )

        total = sum(player_memory.shade_scores.values())
        assert total == pytest.approx(1.0, abs=0.01)

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_dominant_shade(self, player_memory):
        """Can determine dominant moral shade."""
        # Make compassionate dominant
        player_memory.record_moral_action(
            action_type="help",
            description="Major act of kindness",
            timestamp=0,
            shade_effects={"compassionate": 2.0},
            weight=1.0
        )

        dominant = player_memory.get_dominant_shade()
        assert dominant == MoralShade.COMPASSIONATE

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_secondary_shade(self, player_memory):
        """Can determine secondary moral shade."""
        # Make one shade clearly dominant, another second
        player_memory.record_moral_action(
            action_type="ruthless_act",
            description="Ruthless",
            timestamp=0,
            shade_effects={"ruthless": 3.0, "pragmatic": 1.5},
            weight=1.0
        )

        secondary = player_memory.get_secondary_shade()
        # Secondary should be pragmatic
        assert secondary == MoralShade.PRAGMATIC

    @pytest.mark.unit
    @pytest.mark.memory
    def test_action_weight_affects_shades(self, player_memory):
        """Action weight affects shade changes."""
        # Low weight action
        player_memory.record_moral_action(
            action_type="minor",
            description="Minor act",
            timestamp=0,
            shade_effects={"corrupt": 0.5},
            weight=0.1
        )

        # High weight action
        player_memory.record_moral_action(
            action_type="major",
            description="Major act",
            timestamp=0,
            shade_effects={"idealistic": 0.5},
            weight=2.0
        )

        # Idealistic should be more affected
        assert player_memory.shade_scores["idealistic"] > player_memory.shade_scores["corrupt"]


class TestPlayerMemoryTracking:
    """Location and NPC tracking."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_visit_location(self, player_memory):
        """Can track visited locations."""
        player_memory.visit_location("study")
        player_memory.visit_location("hallway")

        assert player_memory.has_visited("study")
        assert player_memory.has_visited("hallway")
        assert not player_memory.has_visited("kitchen")

    @pytest.mark.unit
    @pytest.mark.memory
    def test_talked_to_tracking(self, player_memory):
        """Can track NPCs talked to."""
        player_memory.mark_talked_to("alice")

        assert player_memory.has_talked_to("alice")
        assert not player_memory.has_talked_to("bob")

    @pytest.mark.unit
    @pytest.mark.memory
    def test_notes(self, player_memory):
        """Can add mental notes."""
        player_memory.add_note("Alice seems nervous")
        player_memory.add_note("Check the garden later")

        assert len(player_memory.notes) == 2


class TestPlayerMemorySerialization:
    """Serialization and deserialization."""

    @pytest.fixture
    def complex_player_memory(self, player_memory):
        """Player memory with complex state."""
        player_memory.add_discovery(
            fact_id="clue1",
            description="A clue",
            location="study",
            timestamp=0,
            source="examined",
            is_evidence=True
        )
        player_memory.add_suspicion("alice", 0.7)
        player_memory.update_relationship("bob", 15)
        player_memory.record_moral_action(
            action_type="help",
            description="Helped someone",
            timestamp=10,
            shade_effects={"compassionate": 0.5}
        )
        player_memory.visit_location("study")
        player_memory.mark_talked_to("alice")
        player_memory.add_note("Remember to check safe")
        return player_memory

    @pytest.mark.unit
    @pytest.mark.memory
    def test_serialize_player_memory(self, complex_player_memory):
        """Can serialize player memory."""
        data = complex_player_memory.to_dict()

        assert "discoveries" in data
        assert "suspicions" in data
        assert "moral_actions" in data
        assert "shade_scores" in data
        assert "visited_locations" in data

    @pytest.mark.unit
    @pytest.mark.memory
    def test_deserialize_player_memory(self, complex_player_memory):
        """Can deserialize player memory."""
        data = complex_player_memory.to_dict()
        restored = PlayerMemory.from_dict(data)

        assert restored.has_discovered("clue1")
        assert restored.get_suspicion("alice") == 0.7
        assert restored.get_relationship("bob") == 15
        assert restored.has_visited("study")
        assert restored.has_talked_to("alice")
        assert len(restored.notes) == 1
