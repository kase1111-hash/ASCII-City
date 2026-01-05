"""
Tests for Character Relationships System.

These tests verify that the relationship system correctly:
- Tracks relationships between NPCs
- Simulates NPC-to-NPC interactions
- Updates affinity and tension
- Serializes/deserializes properly
"""

import pytest
from shadowengine.character import (
    RelationshipManager, Relationship, RelationType, NPCInteractionResult
)


class TestRelationship:
    """Relationship tests."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_create_relationship(self):
        """Can create a relationship."""
        rel = Relationship(
            target_id="bob",
            relation_type=RelationType.FRIEND,
            affinity=50
        )

        assert rel.target_id == "bob"
        assert rel.relation_type == RelationType.FRIEND
        assert rel.affinity == 50

    @pytest.mark.unit
    @pytest.mark.character
    def test_modify_affinity_clamped(self):
        """Affinity is clamped to -100 to 100."""
        rel = Relationship(target_id="bob", affinity=90)

        rel.modify_affinity(20)
        assert rel.affinity == 100

        rel.modify_affinity(-250)
        assert rel.affinity == -100

    @pytest.mark.unit
    @pytest.mark.character
    def test_modify_trust_clamped(self):
        """Trust is clamped to -100 to 100."""
        rel = Relationship(target_id="bob", trust=80)

        rel.modify_trust(30)
        assert rel.trust == 100

    @pytest.mark.unit
    @pytest.mark.character
    def test_modify_tension_clamped(self):
        """Tension is clamped to 0 to 100."""
        rel = Relationship(target_id="bob", tension=20)

        rel.modify_tension(-50)
        assert rel.tension == 0

        rel.modify_tension(150)
        assert rel.tension == 100

    @pytest.mark.unit
    @pytest.mark.character
    def test_affinity_updates_type(self):
        """High/low affinity updates relationship type."""
        rel = Relationship(target_id="bob", affinity=0)

        rel.modify_affinity(70)
        assert rel.relation_type == RelationType.CLOSE_FRIEND

        rel.modify_affinity(-130)  # Now at -60
        assert rel.relation_type == RelationType.ENEMY

    @pytest.mark.unit
    @pytest.mark.character
    def test_special_types_not_overridden(self):
        """Special relationship types aren't overridden by affinity."""
        rel = Relationship(
            target_id="sibling",
            relation_type=RelationType.FAMILY,
            affinity=-50
        )

        rel.modify_affinity(-20)
        # Should still be family, not enemy
        assert rel.relation_type == RelationType.FAMILY

    @pytest.mark.unit
    @pytest.mark.character
    def test_add_shared_secret(self):
        """Can add shared secrets."""
        rel = Relationship(target_id="bob")
        initial_trust = rel.trust

        rel.add_shared_secret("knows_about_theft")

        assert "knows_about_theft" in rel.shared_secrets
        assert rel.trust > initial_trust

    @pytest.mark.unit
    @pytest.mark.character
    def test_add_to_history(self):
        """Can record history events."""
        rel = Relationship(target_id="bob")

        rel.add_to_history("Had an argument about the letter")

        assert len(rel.history) == 1


class TestRelationshipManager:
    """Relationship manager tests."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_create_manager(self):
        """Can create a relationship manager."""
        manager = RelationshipManager()

        assert manager is not None
        assert len(manager.relationships) == 0

    @pytest.mark.unit
    @pytest.mark.character
    def test_register_character(self):
        """Can register characters."""
        manager = RelationshipManager()
        manager.register_character("alice")

        assert "alice" in manager.relationships

    @pytest.mark.unit
    @pytest.mark.character
    def test_set_relationship(self):
        """Can set relationships."""
        manager = RelationshipManager()
        manager.set_relationship(
            "alice", "bob",
            RelationType.FRIEND,
            affinity=40
        )

        rel = manager.get_relationship("alice", "bob")
        assert rel is not None
        assert rel.affinity == 40

    @pytest.mark.unit
    @pytest.mark.character
    def test_bidirectional_relationship(self):
        """Bidirectional relationships are created."""
        manager = RelationshipManager()
        manager.set_relationship(
            "alice", "bob",
            RelationType.FRIEND,
            bidirectional=True
        )

        assert manager.get_relationship("alice", "bob") is not None
        assert manager.get_relationship("bob", "alice") is not None

    @pytest.mark.unit
    @pytest.mark.character
    def test_hierarchical_relationship(self):
        """Hierarchical relationships have correct reverse types."""
        manager = RelationshipManager()
        manager.set_relationship(
            "butler", "lord",
            RelationType.SUBORDINATE,
            bidirectional=True
        )

        butler_to_lord = manager.get_relationship("butler", "lord")
        lord_to_butler = manager.get_relationship("lord", "butler")

        assert butler_to_lord.relation_type == RelationType.SUBORDINATE
        assert lord_to_butler.relation_type == RelationType.SUPERIOR

    @pytest.mark.unit
    @pytest.mark.character
    def test_get_all_relationships(self):
        """Can get all relationships for a character."""
        manager = RelationshipManager()
        manager.set_relationship("alice", "bob", RelationType.FRIEND)
        manager.set_relationship("alice", "charlie", RelationType.RIVAL)

        rels = manager.get_all_relationships("alice")

        assert len(rels) == 2
        assert "bob" in rels
        assert "charlie" in rels


class TestNPCInteractions:
    """NPC interaction simulation tests."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_simulate_interaction(self):
        """Can simulate an interaction."""
        manager = RelationshipManager()
        manager.set_seed(42)
        manager.set_relationship("alice", "bob", RelationType.FRIEND, affinity=30)

        result = manager.simulate_interaction(
            "alice", "bob", "parlor"
        )

        assert result.character1_id == "alice"
        assert result.character2_id == "bob"
        assert result.interaction_type is not None

    @pytest.mark.unit
    @pytest.mark.character
    def test_interaction_affects_affinity(self):
        """Interactions affect relationship affinity."""
        manager = RelationshipManager()
        manager.set_seed(42)
        manager.set_relationship("alice", "bob", RelationType.FRIEND, affinity=30)

        initial = manager.get_relationship("alice", "bob").affinity

        # Simulate several interactions
        for _ in range(5):
            manager.simulate_interaction("alice", "bob", "parlor")

        final = manager.get_relationship("alice", "bob").affinity

        # Affinity should have changed
        assert final != initial

    @pytest.mark.unit
    @pytest.mark.character
    def test_hostile_interaction(self):
        """Hostile relationships produce hostile interactions."""
        manager = RelationshipManager()
        manager.set_seed(42)
        manager.set_relationship("alice", "bob", RelationType.ENEMY, affinity=-60)

        result = manager.simulate_interaction("alice", "bob", "parlor")

        assert result.interaction_type in ("hostile_exchange", "confrontation")

    @pytest.mark.unit
    @pytest.mark.character
    def test_high_tension_causes_confrontation(self):
        """High tension leads to confrontations."""
        manager = RelationshipManager()
        manager.set_seed(42)
        manager.set_relationship("alice", "bob", RelationType.ACQUAINTANCE)

        # Set high tension
        rel = manager.get_relationship("alice", "bob")
        rel.tension = 80

        result = manager.simulate_interaction("alice", "bob", "parlor")

        assert result.interaction_type == "confrontation"

    @pytest.mark.unit
    @pytest.mark.character
    def test_interaction_logged(self):
        """Interactions are logged."""
        manager = RelationshipManager()
        manager.simulate_interaction("alice", "bob", "parlor")

        assert len(manager.interaction_log) == 1

    @pytest.mark.unit
    @pytest.mark.character
    def test_witnesses_recorded(self):
        """Witnesses are recorded in interaction."""
        manager = RelationshipManager()
        result = manager.simulate_interaction(
            "alice", "bob", "parlor",
            witnesses=["charlie", "david"]
        )

        assert "charlie" in result.witnessed_by
        assert "david" in result.witnessed_by


class TestLocationInteractions:
    """Location-based interaction tests."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_get_characters_in_location(self):
        """Can get characters in a location."""
        manager = RelationshipManager()
        locations = {
            "alice": "parlor",
            "bob": "parlor",
            "charlie": "kitchen"
        }

        in_parlor = manager.get_characters_in_location("parlor", locations)

        assert len(in_parlor) == 2
        assert "alice" in in_parlor
        assert "bob" in in_parlor
        assert "charlie" not in in_parlor

    @pytest.mark.unit
    @pytest.mark.character
    def test_simulate_location_interactions(self):
        """Can simulate interactions at a location."""
        manager = RelationshipManager()
        manager.set_seed(42)

        locations = {
            "alice": "parlor",
            "bob": "parlor",
            "charlie": "parlor"
        }

        results = manager.simulate_location_interactions("parlor", locations)

        assert len(results) >= 1

    @pytest.mark.unit
    @pytest.mark.character
    def test_no_interactions_alone(self):
        """No interactions when alone in location."""
        manager = RelationshipManager()

        locations = {"alice": "parlor"}

        results = manager.simulate_location_interactions("parlor", locations)

        assert len(results) == 0


class TestRelationshipSerialization:
    """Relationship serialization tests."""

    @pytest.mark.unit
    @pytest.mark.character
    def test_serialize_relationship(self):
        """Can serialize a relationship."""
        rel = Relationship(
            target_id="bob",
            relation_type=RelationType.FRIEND,
            affinity=40,
            trust=30
        )
        rel.add_shared_secret("secret1")
        rel.add_to_history("event1")

        data = rel.to_dict()

        assert data["target_id"] == "bob"
        assert data["relation_type"] == "FRIEND"
        assert "secret1" in data["shared_secrets"]

    @pytest.mark.unit
    @pytest.mark.character
    def test_deserialize_relationship(self):
        """Can deserialize a relationship."""
        rel = Relationship(
            target_id="bob",
            relation_type=RelationType.CONSPIRATOR,
            affinity=50,
            tension=30
        )

        data = rel.to_dict()
        restored = Relationship.from_dict(data)

        assert restored.target_id == "bob"
        assert restored.relation_type == RelationType.CONSPIRATOR
        assert restored.tension == 30

    @pytest.mark.unit
    @pytest.mark.character
    def test_serialize_manager(self):
        """Can serialize relationship manager."""
        manager = RelationshipManager()
        manager.set_relationship("alice", "bob", RelationType.FRIEND, affinity=30)
        manager.simulate_interaction("alice", "bob", "parlor")

        data = manager.to_dict()

        assert "relationships" in data
        assert "alice" in data["relationships"]
        assert len(data["interaction_log"]) == 1

    @pytest.mark.unit
    @pytest.mark.character
    def test_deserialize_manager(self):
        """Can deserialize relationship manager."""
        manager = RelationshipManager()
        manager.set_relationship("alice", "bob", RelationType.FRIEND, affinity=30)
        manager.simulate_interaction("alice", "bob", "parlor")

        data = manager.to_dict()
        restored = RelationshipManager.from_dict(data)

        assert "alice" in restored.relationships
        rel = restored.get_relationship("alice", "bob")
        assert rel is not None
        assert len(restored.interaction_log) == 1

    @pytest.mark.unit
    @pytest.mark.character
    def test_roundtrip_preserves_all_state(self):
        """Roundtrip preserves all state."""
        manager = RelationshipManager()
        manager.set_relationship(
            "alice", "bob",
            RelationType.CONSPIRATOR,
            affinity=60,
            trust=40
        )
        rel = manager.get_relationship("alice", "bob")
        rel.tension = 25
        rel.add_shared_secret("the_plan")
        rel.add_to_history("Met in secret")

        data = manager.to_dict()
        restored = RelationshipManager.from_dict(data)

        restored_rel = restored.get_relationship("alice", "bob")
        assert restored_rel.tension == 25
        assert "the_plan" in restored_rel.shared_secrets
        assert "Met in secret" in restored_rel.history
