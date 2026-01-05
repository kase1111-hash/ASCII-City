"""Tests for Rumor system."""

import pytest
from src.shadowengine.npc_intelligence.rumor import (
    Rumor, RumorMutation, RumorPropagation, PropagationTrigger
)
from src.shadowengine.npc_intelligence.npc_memory import NPCMemory, MemorySource
from src.shadowengine.npc_intelligence.npc_bias import NPCBias


class TestRumor:
    """Tests for Rumor dataclass."""

    def test_rumor_creation(self):
        """Test creating a rumor."""
        rumor = Rumor(
            core_claim="Someone died at the waterfall",
            tags=["death", "waterfall"],
            confidence=0.8,
            origin_location="north_falls",
            origin_timestamp=100.0
        )

        assert rumor.core_claim == "Someone died at the waterfall"
        assert "death" in rumor.tags
        assert rumor.confidence == 0.8
        assert rumor.rumor_id.startswith("rum_")

    def test_rumor_auto_id(self):
        """Test that rumors get auto-generated IDs."""
        rum1 = Rumor(core_claim="test1")
        rum2 = Rumor(core_claim="test2")

        assert rum1.rumor_id != rum2.rumor_id

    def test_add_carrier(self):
        """Test adding carriers to rumor."""
        rumor = Rumor()
        rumor.add_carrier("npc_001")
        rumor.add_carrier("npc_002")
        rumor.add_carrier("npc_001")  # Duplicate

        assert rumor.carrier_count == 2
        assert rumor.is_carrier("npc_001")
        assert rumor.is_carrier("npc_002")

    def test_has_tag(self):
        """Test tag checking."""
        rumor = Rumor(tags=["danger", "mob"])

        assert rumor.has_tag("danger")
        assert not rumor.has_tag("safety")

    def test_add_tag(self):
        """Test adding tags."""
        rumor = Rumor(tags=["danger"])
        rumor.add_tag("conspiracy")
        rumor.add_tag("danger")  # Duplicate

        assert "conspiracy" in rumor.tags
        assert rumor.tags.count("danger") == 1

    def test_record_mutation(self):
        """Test recording mutations."""
        rumor = Rumor()
        rumor.record_mutation("exaggerated")
        rumor.record_mutation("simplified")

        assert "exaggerated" in rumor.mutation_history
        assert "simplified" in rumor.mutation_history

    def test_rumor_from_memory(self):
        """Test creating rumor from memory."""
        memory = NPCMemory(
            memory_id="mem_001",
            event_id="evt_001",
            summary="The mob is dangerous",
            tags=["mob", "danger"],
            confidence=0.9,
            timestamp=100.0,
            location="downtown"
        )

        rumor = Rumor.from_memory(memory, "npc_001")

        assert rumor.core_claim == memory.summary
        assert rumor.origin_memory == "mem_001"
        assert rumor.origin_event == "evt_001"
        assert rumor.origin_npc == "npc_001"
        assert rumor.is_carrier("npc_001")
        assert rumor.confidence < memory.confidence  # Slight loss

    def test_rumor_serialization(self):
        """Test rumor to_dict and from_dict."""
        rumor = Rumor(
            core_claim="Test rumor",
            details=["Detail 1", "Detail 2"],
            tags=["test"],
            confidence=0.7,
            distortion=0.3,
            spread_count=5,
            carriers={"npc_001", "npc_002"},
            origin_event="evt_001",
            origin_location="test_location",
            is_active=True
        )

        data = rumor.to_dict()
        restored = Rumor.from_dict(data)

        assert restored.core_claim == rumor.core_claim
        assert restored.details == rumor.details
        assert restored.confidence == rumor.confidence
        assert restored.distortion == rumor.distortion
        assert restored.is_carrier("npc_001")


class TestRumorMutation:
    """Tests for RumorMutation."""

    def test_mutate_decreases_confidence(self):
        """Test that mutation decreases confidence."""
        mutation = RumorMutation()
        rumor = Rumor(confidence=1.0, distortion=0.0)
        source_bias = NPCBias()
        target_bias = NPCBias()

        mutated = mutation.mutate(rumor, source_bias, target_bias, 100.0)

        assert mutated.confidence < 1.0

    def test_mutate_increases_distortion(self):
        """Test that mutation increases distortion."""
        mutation = RumorMutation()
        rumor = Rumor(confidence=1.0, distortion=0.0)
        source_bias = NPCBias()
        target_bias = NPCBias()

        mutated = mutation.mutate(rumor, source_bias, target_bias, 100.0)

        assert mutated.distortion > 0.0

    def test_mutate_increments_spread_count(self):
        """Test that mutation increments spread count."""
        mutation = RumorMutation()
        rumor = Rumor(spread_count=3)
        source_bias = NPCBias()
        target_bias = NPCBias()

        mutated = mutation.mutate(rumor, source_bias, target_bias, 100.0)

        assert mutated.spread_count == 4

    def test_dramatic_source_exaggerates(self):
        """Test that dramatic sources exaggerate."""
        mutation = RumorMutation()
        rumor = Rumor(core_claim="Someone got hurt")
        dramatic_bias = NPCBias(dramatic=0.9)
        target_bias = NPCBias()

        # Apply source bias
        claim = mutation._apply_source_bias(rumor.core_claim, dramatic_bias)

        # Dramatic might exaggerate
        assert claim != rumor.core_claim or "nearly died" in claim

    def test_forgetful_target_loses_details(self):
        """Test that forgetful targets lose details."""
        mutation = RumorMutation()
        details = ["Detail 1", "Detail 2", "Detail 3"]
        forgetful_bias = NPCBias(forgetful=0.9)

        # Run multiple times due to randomness
        lost_detail = False
        for _ in range(20):
            filtered = mutation._filter_by_target_bias(details.copy(), forgetful_bias)
            if len(filtered) < len(details):
                lost_detail = True
                break

        assert lost_detail

    def test_simplify_removes_details(self):
        """Test simplification removes details."""
        mutation = RumorMutation()
        rumor = Rumor(details=["Detail 1", "Detail 2", "Detail 3"])

        simplified = mutation._simplify(rumor)

        assert len(simplified.details) < 3
        assert "simplified" in simplified.mutation_history

    def test_exaggerate_transforms_claim(self):
        """Test exaggeration transforms claim."""
        mutation = RumorMutation()
        rumor = Rumor(core_claim="Someone got hurt")
        fearful_bias = NPCBias(fearful=0.9)

        exaggerated = mutation._exaggerate(rumor, fearful_bias)

        if "exaggerated" in exaggerated.mutation_history:
            assert "nearly died" in exaggerated.core_claim

    def test_misattribute_changes_claim(self):
        """Test misattribution changes claim."""
        mutation = RumorMutation()
        rumor = Rumor(core_claim="It was an accident")

        # Run multiple times due to randomness
        misattributed = False
        for _ in range(20):
            test_rumor = Rumor(core_claim="It was an accident")
            result = mutation._misattribute(test_rumor)
            if "murder" in result.core_claim:
                misattributed = True
                break

        # Should eventually misattribute
        assert misattributed


class TestRumorPropagation:
    """Tests for RumorPropagation."""

    def test_propagation_init(self):
        """Test propagation system initialization."""
        propagation = RumorPropagation()

        assert propagation.mutation_system is not None
        assert len(propagation.active_rumors) == 0

    def test_should_propagate_base_probability(self):
        """Test base propagation probability."""
        propagation = RumorPropagation()
        bias = NPCBias(talkative=0.5)

        # Gossip has high base probability
        gossip_propagates = False
        for _ in range(20):
            if propagation.should_propagate(bias, "npc_002", PropagationTrigger.GOSSIP):
                gossip_propagates = True
                break

        assert gossip_propagates

    def test_should_propagate_friend_bonus(self):
        """Test propagation bonus for friends."""
        propagation = RumorPropagation()
        bias = NPCBias(talkative=0.5, allies=["friend_npc"])

        # Should be more likely to propagate to friends
        friend_count = sum(
            1 for _ in range(100)
            if propagation.should_propagate(
                bias, "friend_npc", PropagationTrigger.CONVERSATION
            )
        )
        stranger_count = sum(
            1 for _ in range(100)
            if propagation.should_propagate(
                bias, "stranger_npc", PropagationTrigger.CONVERSATION
            )
        )

        assert friend_count > stranger_count

    def test_should_propagate_enemy_penalty(self):
        """Test propagation penalty for enemies."""
        propagation = RumorPropagation()
        bias = NPCBias(talkative=0.5, enemies=["enemy_npc"])

        # Should be less likely to propagate to enemies
        enemy_count = sum(
            1 for _ in range(100)
            if propagation.should_propagate(
                bias, "enemy_npc", PropagationTrigger.CONVERSATION
            )
        )
        stranger_count = sum(
            1 for _ in range(100)
            if propagation.should_propagate(
                bias, "stranger_npc", PropagationTrigger.CONVERSATION
            )
        )

        assert enemy_count < stranger_count

    def test_select_rumor_to_share_context(self):
        """Test rumor selection based on context."""
        propagation = RumorPropagation()
        rumors = [
            Rumor(core_claim="Mob activity", tags=["mob", "crime"], confidence=0.5),
            Rumor(core_claim="Nice weather", tags=["weather"], confidence=0.5),
            Rumor(core_claim="More mob stuff", tags=["mob"], confidence=0.5)
        ]
        bias = NPCBias()

        selected = propagation.select_rumor_to_share(rumors, bias, context_tags=["mob"])

        # Should select a mob-related rumor
        assert selected is not None
        assert "mob" in selected.tags

    def test_propagate_success(self):
        """Test successful propagation."""
        propagation = RumorPropagation()
        rumor = Rumor(
            core_claim="Test rumor",
            confidence=0.8,
            carriers={"npc_001"}
        )
        source_bias = NPCBias(talkative=1.0)  # Very talkative
        target_bias = NPCBias(trusting=0.8)

        # Force propagation by using high-probability trigger
        result = None
        for _ in range(50):
            result = propagation.propagate(
                rumor=rumor,
                source_id="npc_001",
                source_bias=source_bias,
                target_id="npc_002",
                target_bias=target_bias,
                trigger=PropagationTrigger.GOSSIP,
                current_time=100.0
            )
            if result is not None:
                break

        assert result is not None
        assert result.is_carrier("npc_002")

    def test_propagate_blocks_known_rumor(self):
        """Test that propagation fails if target already knows rumor."""
        propagation = RumorPropagation()
        rumor = Rumor(
            core_claim="Test rumor",
            carriers={"npc_001", "npc_002"}  # Target already knows
        )

        result = propagation.propagate(
            rumor=rumor,
            source_id="npc_001",
            source_bias=NPCBias(talkative=1.0),
            target_id="npc_002",
            target_bias=NPCBias(),
            trigger=PropagationTrigger.GOSSIP,
            current_time=100.0
        )

        assert result is None

    def test_convert_memory_to_rumor(self):
        """Test converting memory to rumor."""
        propagation = RumorPropagation()
        memory = NPCMemory(
            memory_id="mem_001",
            summary="Test event",
            tags=["test"],
            confidence=0.9
        )

        rumor = propagation.convert_memory_to_rumor(memory, "npc_001")

        assert rumor.core_claim == memory.summary
        assert rumor.rumor_id in propagation.active_rumors
        assert rumor.is_carrier("npc_001")

    def test_get_rumors_by_tag(self):
        """Test finding rumors by tag."""
        propagation = RumorPropagation()
        propagation.active_rumors = {
            "rum_1": Rumor(rumor_id="rum_1", tags=["mob", "crime"]),
            "rum_2": Rumor(rumor_id="rum_2", tags=["weather"]),
            "rum_3": Rumor(rumor_id="rum_3", tags=["mob"])
        }

        mob_rumors = propagation.get_rumors_by_tag("mob")

        assert len(mob_rumors) == 2

    def test_get_rumors_about_location(self):
        """Test finding rumors by location."""
        propagation = RumorPropagation()
        propagation.active_rumors = {
            "rum_1": Rumor(rumor_id="rum_1", origin_location="bar"),
            "rum_2": Rumor(rumor_id="rum_2", origin_location="alley"),
            "rum_3": Rumor(rumor_id="rum_3", origin_location="bar")
        }

        bar_rumors = propagation.get_rumors_about_location("bar")

        assert len(bar_rumors) == 2

    def test_get_rumors_known_by(self):
        """Test finding rumors known by NPC."""
        propagation = RumorPropagation()
        propagation.active_rumors = {
            "rum_1": Rumor(rumor_id="rum_1", carriers={"npc_001", "npc_002"}),
            "rum_2": Rumor(rumor_id="rum_2", carriers={"npc_002"}),
            "rum_3": Rumor(rumor_id="rum_3", carriers={"npc_001"})
        }

        npc1_rumors = propagation.get_rumors_known_by("npc_001")

        assert len(npc1_rumors) == 2

    def test_decay_rumors(self):
        """Test rumor decay."""
        propagation = RumorPropagation()
        # rum_1 has low confidence but enough carriers to not be deleted
        rum_1 = Rumor(rumor_id="rum_1", confidence=0.05, is_active=True, carrier_count=3)
        rum_1.carriers = {"a", "b", "c"}
        propagation.active_rumors = {
            "rum_1": rum_1,
            "rum_2": Rumor(rumor_id="rum_2", confidence=0.5, is_active=True)
        }

        propagation.decay_rumors(dt=1.0)

        # Low confidence rumor should become inactive but not removed (has carriers)
        assert not propagation.active_rumors["rum_1"].is_active
