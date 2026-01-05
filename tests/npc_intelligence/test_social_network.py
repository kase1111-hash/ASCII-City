"""Tests for SocialNetwork system."""

import pytest
from src.shadowengine.npc_intelligence.social_network import (
    SocialRelation, RelationType, SocialEvent,
    RelationshipDynamics, SocialNetwork
)


class TestSocialRelation:
    """Tests for SocialRelation dataclass."""

    def test_relation_creation(self):
        """Test creating a social relation."""
        relation = SocialRelation(
            from_npc="npc_001",
            to_npc="npc_002",
            relation_type=RelationType.ACQUAINTANCE,
            affinity=30,
            trust=20
        )

        assert relation.from_npc == "npc_001"
        assert relation.to_npc == "npc_002"
        assert relation.relation_type == RelationType.ACQUAINTANCE
        assert relation.relation_id.startswith("rel_")

    def test_modify_affinity(self):
        """Test modifying affinity."""
        relation = SocialRelation(affinity=0)

        relation.modify_affinity(30)
        assert relation.affinity == 30

        relation.modify_affinity(-50)
        assert relation.affinity == -20

    def test_modify_affinity_clamping(self):
        """Test affinity clamping."""
        relation = SocialRelation(affinity=90)

        relation.modify_affinity(50)
        assert relation.affinity == 100  # Max

        relation.modify_affinity(-250)
        assert relation.affinity == -100  # Min

    def test_modify_trust(self):
        """Test modifying trust."""
        relation = SocialRelation(trust=0)

        relation.modify_trust(40)
        assert relation.trust == 40

    def test_modify_tension(self):
        """Test modifying tension."""
        relation = SocialRelation(tension=0)

        relation.modify_tension(50)
        assert relation.tension == 50

        relation.modify_tension(-30)
        assert relation.tension == 20

    def test_type_updates_based_on_affinity(self):
        """Test relation type updates with affinity."""
        relation = SocialRelation(
            from_npc="a",
            to_npc="b",
            relation_type=RelationType.STRANGER,
            affinity=0,
            trust=0
        )

        # Become friends
        relation.modify_affinity(60)
        assert relation.relation_type == RelationType.FRIEND

        # Become close friends
        relation.modify_trust(70)
        relation.modify_affinity(30)  # Total 90
        assert relation.relation_type == RelationType.CLOSE_FRIEND

        # Become enemies
        relation.modify_affinity(-200)  # To -110, clamped to -100
        assert relation.relation_type == RelationType.ENEMY

    def test_family_type_doesnt_change(self):
        """Test that family relationship doesn't change."""
        relation = SocialRelation(
            from_npc="a",
            to_npc="b",
            relation_type=RelationType.FAMILY,
            affinity=-50
        )

        relation.modify_affinity(-50)  # Even more negative
        assert relation.relation_type == RelationType.FAMILY

    def test_add_shared_secret(self):
        """Test adding shared secret increases trust."""
        relation = SocialRelation(trust=20)

        relation.add_shared_secret("the_truth")
        relation.add_shared_secret("the_truth")  # Duplicate

        assert "the_truth" in relation.shared_secrets
        assert len(relation.shared_secrets) == 1
        assert relation.trust == 25  # +5 for sharing

    def test_record_interaction(self):
        """Test recording interaction."""
        relation = SocialRelation()

        relation.record_interaction(
            interaction_type="conversation",
            timestamp=100.0,
            outcome="friendly"
        )

        assert len(relation.interaction_history) == 1
        assert relation.last_interaction == 100.0

    def test_will_share_with(self):
        """Test share willingness check."""
        trusting = SocialRelation(trust=30, affinity=10)
        distrusting = SocialRelation(trust=-30, affinity=10)
        hostile = SocialRelation(trust=30, affinity=-30)

        assert trusting.will_share_with()
        assert not distrusting.will_share_with()
        assert not hostile.will_share_with()

    def test_will_protect(self):
        """Test protection check."""
        friend = SocialRelation(affinity=60, relation_type=RelationType.FRIEND)
        family = SocialRelation(affinity=-10, relation_type=RelationType.FAMILY)
        enemy = SocialRelation(affinity=-60, relation_type=RelationType.ENEMY)

        assert friend.will_protect()
        assert family.will_protect()  # Family protects even if not liking
        assert not enemy.will_protect()

    def test_will_betray(self):
        """Test betrayal check."""
        tense_enemy = SocialRelation(affinity=-50, tension=70)
        peaceful_enemy = SocialRelation(affinity=-50, tension=30)
        tense_friend = SocialRelation(affinity=50, tension=70)

        assert tense_enemy.will_betray()
        assert not peaceful_enemy.will_betray()
        assert not tense_friend.will_betray()

    def test_relation_serialization(self):
        """Test relation to_dict and from_dict."""
        relation = SocialRelation(
            from_npc="npc_a",
            to_npc="npc_b",
            relation_type=RelationType.FRIEND,
            affinity=60,
            trust=40,
            shared_secrets=["secret1"],
            shared_memories=["mem1"]
        )

        data = relation.to_dict()
        restored = SocialRelation.from_dict(data)

        assert restored.from_npc == relation.from_npc
        assert restored.to_npc == relation.to_npc
        assert restored.relation_type == RelationType.FRIEND
        assert restored.affinity == 60
        assert "secret1" in restored.shared_secrets


class TestRelationshipDynamics:
    """Tests for RelationshipDynamics."""

    def test_apply_helped_event(self):
        """Test applying 'helped' event."""
        dynamics = RelationshipDynamics()
        relation = SocialRelation(affinity=0, trust=0)

        dynamics.apply_event(relation, "helped")

        assert relation.affinity > 0
        assert relation.trust > 0

    def test_apply_betrayed_event(self):
        """Test applying 'betrayed' event."""
        dynamics = RelationshipDynamics()
        relation = SocialRelation(affinity=50, trust=50, tension=0)

        dynamics.apply_event(relation, "betrayed")

        assert relation.affinity < 50
        assert relation.trust < 50
        assert relation.tension > 0

    def test_apply_event_with_magnitude(self):
        """Test applying event with magnitude scaling."""
        dynamics = RelationshipDynamics()
        relation1 = SocialRelation(affinity=0)
        relation2 = SocialRelation(affinity=0)

        dynamics.apply_event(relation1, "helped", magnitude=1.0)
        dynamics.apply_event(relation2, "helped", magnitude=0.5)

        assert relation1.affinity > relation2.affinity

    def test_decay_tension(self):
        """Test tension decay over time."""
        dynamics = RelationshipDynamics()
        relation = SocialRelation(tension=50)

        dynamics.decay_tension(relation, dt=10.0)

        assert relation.tension < 50

    def test_check_for_conflict(self):
        """Test conflict detection."""
        dynamics = RelationshipDynamics()
        explosive = SocialRelation(tension=90, affinity=-30)
        peaceful = SocialRelation(tension=30, affinity=-30)
        friendly_tense = SocialRelation(tension=90, affinity=30)

        assert dynamics.check_for_conflict(explosive)
        assert not dynamics.check_for_conflict(peaceful)
        assert not dynamics.check_for_conflict(friendly_tense)

    def test_check_for_reconciliation(self):
        """Test reconciliation detection."""
        dynamics = RelationshipDynamics()
        # Affinity <= -60 keeps ENEMY type, and -40 is above threshold for reconciliation
        reconciling = SocialRelation(
            relation_type=RelationType.ENEMY,
            tension=10,
            affinity=-65  # Keep as ENEMY (needs <= -60)
        )
        # Manually set to ensure type stays ENEMY
        reconciling.relation_type = RelationType.ENEMY
        reconciling.affinity = -40  # Now in reconciliation range

        still_angry = SocialRelation(
            relation_type=RelationType.ENEMY,
            tension=60,
            affinity=-70  # Keep as ENEMY
        )
        still_angry.relation_type = RelationType.ENEMY
        still_angry.affinity = -40

        not_enemy = SocialRelation(
            relation_type=RelationType.RIVAL,
            tension=10,
            affinity=-40
        )

        assert dynamics.check_for_reconciliation(reconciling)
        assert not dynamics.check_for_reconciliation(still_angry)
        assert not dynamics.check_for_reconciliation(not_enemy)


class TestSocialNetwork:
    """Tests for SocialNetwork."""

    def test_network_creation(self):
        """Test creating social network."""
        network = SocialNetwork()

        assert len(network.relations) == 0

    def test_get_or_create_relation(self):
        """Test getting or creating relation."""
        network = SocialNetwork()

        rel1 = network.get_or_create_relation("npc_a", "npc_b")
        rel2 = network.get_or_create_relation("npc_a", "npc_b")

        assert rel1 is rel2
        assert rel1.from_npc == "npc_a"
        assert rel1.to_npc == "npc_b"

    def test_get_relation_none(self):
        """Test getting nonexistent relation."""
        network = SocialNetwork()

        relation = network.get_relation("npc_a", "npc_b")

        assert relation is None

    def test_get_all_relations_for(self):
        """Test getting all relations for NPC."""
        network = SocialNetwork()
        network.get_or_create_relation("npc_a", "npc_b")
        network.get_or_create_relation("npc_a", "npc_c")
        network.get_or_create_relation("npc_d", "npc_a")

        relations = network.get_all_relations_for("npc_a")

        assert len(relations) == 3

    def test_get_outgoing_relations(self):
        """Test getting outgoing relations."""
        network = SocialNetwork()
        network.get_or_create_relation("npc_a", "npc_b")
        network.get_or_create_relation("npc_a", "npc_c")
        network.get_or_create_relation("npc_d", "npc_a")

        outgoing = network.get_outgoing_relations("npc_a")

        assert len(outgoing) == 2

    def test_get_friends(self):
        """Test getting friends list."""
        network = SocialNetwork()
        friend_rel = network.get_or_create_relation("npc_a", "npc_b")
        friend_rel.modify_affinity(60)  # Make friend

        enemy_rel = network.get_or_create_relation("npc_a", "npc_c")
        enemy_rel.modify_affinity(-60)  # Make enemy

        friends = network.get_friends("npc_a")

        assert "npc_b" in friends
        assert "npc_c" not in friends

    def test_get_enemies(self):
        """Test getting enemies list."""
        network = SocialNetwork()
        enemy_rel = network.get_or_create_relation("npc_a", "npc_b")
        enemy_rel.modify_affinity(-70)

        enemies = network.get_enemies("npc_a")

        assert "npc_b" in enemies

    def test_get_trusted_npcs(self):
        """Test getting trusted NPCs."""
        network = SocialNetwork()
        trusted = network.get_or_create_relation("npc_a", "npc_b")
        trusted.modify_trust(50)

        untrusted = network.get_or_create_relation("npc_a", "npc_c")
        untrusted.modify_trust(-10)

        trusted_list = network.get_trusted_npcs("npc_a", threshold=30)

        assert "npc_b" in trusted_list
        assert "npc_c" not in trusted_list

    def test_record_interaction(self):
        """Test recording interaction."""
        network = SocialNetwork()

        network.record_interaction(
            from_npc="npc_a",
            to_npc="npc_b",
            interaction_type="helped",
            timestamp=100.0,
            bidirectional=True
        )

        rel_ab = network.get_relation("npc_a", "npc_b")
        rel_ba = network.get_relation("npc_b", "npc_a")

        assert rel_ab is not None
        assert rel_ba is not None
        assert rel_ab.affinity > 0  # Helped increases affinity

    def test_share_rumor_between(self):
        """Test sharing rumor between NPCs."""
        network = SocialNetwork()

        network.share_rumor_between(
            from_npc="npc_a",
            to_npc="npc_b",
            rumor_id="rum_001",
            timestamp=100.0
        )

        relation = network.get_relation("npc_a", "npc_b")

        assert "rum_001" in relation.shared_rumors

    def test_update_creates_events(self):
        """Test update can create social events."""
        network = SocialNetwork()

        # Create explosive relationship
        rel = network.get_or_create_relation("npc_a", "npc_b")
        rel.tension = 90
        rel.affinity = -50

        events = network.update(dt=1.0)

        # Should detect conflict
        conflict_events = [e for e in events if e.event_type == "conflict"]
        assert len(conflict_events) > 0

    def test_get_emergent_storylines(self):
        """Test detecting emergent storylines."""
        network = SocialNetwork()

        # Create high tension relationship
        tense = network.get_or_create_relation("npc_a", "npc_b")
        tense.tension = 80

        storylines = network.get_emergent_storylines()

        # Should find high tension storyline
        tension_stories = [s for s in storylines if s["type"] == "high_tension"]
        assert len(tension_stories) > 0

    def test_friend_of_enemy_storyline(self):
        """Test detecting friend-of-enemy storyline."""
        network = SocialNetwork()

        # A is friends with B
        friend_rel = network.get_or_create_relation("npc_a", "npc_b")
        friend_rel.modify_affinity(60)

        # A is enemies with C
        enemy_rel = network.get_or_create_relation("npc_a", "npc_c")
        enemy_rel.modify_affinity(-60)

        # B is friends with C (friend of enemy)
        bridge_rel = network.get_or_create_relation("npc_b", "npc_c")
        bridge_rel.modify_affinity(60)

        storylines = network.get_emergent_storylines()

        friend_of_enemy = [s for s in storylines if s["type"] == "friend_of_enemy"]
        assert len(friend_of_enemy) > 0

    def test_network_serialization(self):
        """Test network to_dict and from_dict."""
        network = SocialNetwork()
        network.get_or_create_relation("npc_a", "npc_b").modify_affinity(50)
        network.get_or_create_relation("npc_a", "npc_c").modify_trust(30)
        network.current_time = 500.0

        data = network.to_dict()
        restored = SocialNetwork.from_dict(data)

        assert len(restored.relations) == 2
        assert restored.current_time == 500.0
