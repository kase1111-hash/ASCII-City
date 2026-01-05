"""Tests for NPCBias system."""

import pytest
from src.shadowengine.npc_intelligence.npc_bias import NPCBias, BiasProcessor
from src.shadowengine.npc_intelligence.world_event import (
    WorldEvent, WitnessType, Witness
)
from src.shadowengine.npc_intelligence.npc_memory import MemorySource, NPCMemory


class TestNPCBias:
    """Tests for NPCBias dataclass."""

    def test_bias_creation(self):
        """Test creating NPC bias."""
        bias = NPCBias(
            fearful=0.8,
            paranoid=0.6,
            talkative=0.9,
            dramatic=0.7
        )

        assert bias.fearful == 0.8
        assert bias.paranoid == 0.6
        assert bias.talkative == 0.9
        assert bias.dramatic == 0.7

    def test_bias_clamping(self):
        """Test that bias values are clamped to 0-1."""
        bias = NPCBias(
            fearful=1.5,  # Over max
            paranoid=-0.5  # Under min
        )

        assert bias.fearful == 1.0
        assert bias.paranoid == 0.0

    def test_memory_decay_modifier(self):
        """Test memory decay modifier calculation."""
        forgetful = NPCBias(forgetful=1.0)
        remembering = NPCBias(forgetful=0.0)

        assert forgetful.get_memory_decay_modifier() > remembering.get_memory_decay_modifier()
        assert forgetful.get_memory_decay_modifier() == 1.5

    def test_share_probability_modifier(self):
        """Test share probability modifier calculation."""
        talkative = NPCBias(talkative=1.0)
        quiet = NPCBias(talkative=0.0)

        assert talkative.get_share_probability_modifier() > quiet.get_share_probability_modifier()

    def test_ally_enemy_tracking(self):
        """Test ally and enemy lists."""
        bias = NPCBias(
            allies=["friend_1", "friend_2"],
            enemies=["enemy_1"]
        )

        assert bias.is_ally("friend_1")
        assert bias.is_ally("friend_2")
        assert not bias.is_ally("stranger")

        assert bias.is_enemy("enemy_1")
        assert not bias.is_enemy("friend_1")

    def test_bias_serialization(self):
        """Test bias to_dict and from_dict."""
        bias = NPCBias(
            fearful=0.7,
            paranoid=0.8,
            loyal=0.9,
            allies=["ally1"],
            enemies=["enemy1"]
        )

        data = bias.to_dict()
        restored = NPCBias.from_dict(data)

        assert restored.fearful == bias.fearful
        assert restored.paranoid == bias.paranoid
        assert restored.loyal == bias.loyal
        assert "ally1" in restored.allies
        assert "enemy1" in restored.enemies

    def test_random_bias(self):
        """Test generating random bias."""
        bias1 = NPCBias.random(seed=42)
        bias2 = NPCBias.random(seed=42)
        bias3 = NPCBias.random(seed=123)

        # Same seed should produce same bias
        assert bias1.fearful == bias2.fearful

        # Different seed should (usually) produce different bias
        assert bias1.fearful != bias3.fearful or bias1.paranoid != bias3.paranoid

    def test_from_archetype(self):
        """Test creating bias from archetype."""
        bartender = NPCBias.from_archetype("bartender")
        informant = NPCBias.from_archetype("informant")
        cop = NPCBias.from_archetype("cop")

        # Bartenders are talkative
        assert bartender.talkative == 0.8

        # Informants are very talkative but paranoid
        assert informant.talkative == 0.9
        assert informant.paranoid == 0.7

        # Cops are suspicious
        assert cop.suspicious == 0.7

    def test_unknown_archetype_returns_default(self):
        """Test that unknown archetype returns default bias."""
        unknown = NPCBias.from_archetype("unknown_type")

        # Should get default values
        assert unknown.fearful == 0.5
        assert unknown.talkative == 0.5


class TestBiasProcessor:
    """Tests for BiasProcessor."""

    def test_interpret_injury_event_fearful(self):
        """Test fearful NPC interprets injury as near death."""
        processor = BiasProcessor()
        event = WorldEvent(event_type="injury")
        bias = NPCBias(fearful=0.8)

        summary = processor.interpret_event(event, bias, WitnessType.DIRECT)

        assert "nearly died" in summary or "died" in summary.lower()

    def test_interpret_violence_event_paranoid(self):
        """Test paranoid NPC sees mob conspiracy."""
        processor = BiasProcessor()
        event = WorldEvent(event_type="violence")
        bias = NPCBias(paranoid=0.8)

        summary = processor.interpret_event(event, bias, WitnessType.DIRECT)

        assert "mob" in summary.lower()

    def test_interpret_event_cynical(self):
        """Test cynical NPC interpretation."""
        processor = BiasProcessor()
        event = WorldEvent(event_type="injury")
        bias = NPCBias(cynical=0.8)

        summary = processor.interpret_event(event, bias, WitnessType.DIRECT)

        assert "coming to them" in summary.lower()

    def test_interpret_default(self):
        """Test default interpretation for neutral NPC."""
        processor = BiasProcessor()
        event = WorldEvent(event_type="injury")
        bias = NPCBias()  # All defaults (0.3-0.5)

        summary = processor.interpret_event(event, bias, WitnessType.DIRECT)

        assert "hurt" in summary.lower() or "accident" in summary.lower()

    def test_extract_tags_base(self):
        """Test base tag extraction."""
        processor = BiasProcessor()
        event = WorldEvent(event_type="violence")
        bias = NPCBias()

        tags = processor.extract_tags(event, bias)

        assert "violence" in tags
        assert "danger" in tags

    def test_extract_tags_with_bias(self):
        """Test tag extraction with bias influence."""
        processor = BiasProcessor()
        event = WorldEvent(event_type="conversation")
        bias = NPCBias(paranoid=0.8)

        tags = processor.extract_tags(event, bias)

        assert "suspicious" in tags

    def test_calculate_emotional_weight_direct_witness(self):
        """Test emotional weight higher for direct witnesses."""
        processor = BiasProcessor()
        event = WorldEvent(event_type="violence", notability=0.5)
        bias = NPCBias()

        direct_weight = processor.calculate_emotional_weight(
            event, bias, WitnessType.DIRECT
        )
        indirect_weight = processor.calculate_emotional_weight(
            event, bias, WitnessType.INDIRECT
        )

        assert direct_weight > indirect_weight

    def test_calculate_emotional_weight_dramatic(self):
        """Test dramatic NPCs have higher emotional weight."""
        processor = BiasProcessor()
        event = WorldEvent(event_type="conversation", notability=0.3)
        dramatic = NPCBias(dramatic=0.9)
        normal = NPCBias(dramatic=0.1)

        dramatic_weight = processor.calculate_emotional_weight(
            event, dramatic, WitnessType.DIRECT
        )
        normal_weight = processor.calculate_emotional_weight(
            event, normal, WitnessType.DIRECT
        )

        assert dramatic_weight > normal_weight

    def test_calculate_fear(self):
        """Test fear calculation for dangerous events."""
        processor = BiasProcessor()
        violence = WorldEvent(event_type="violence")
        conversation = WorldEvent(event_type="conversation")
        fearful = NPCBias(fearful=0.8)

        violence_fear = processor.calculate_fear(violence, fearful)
        conversation_fear = processor.calculate_fear(conversation, fearful)

        assert violence_fear > conversation_fear
        assert violence_fear > 0.5  # Violence causes fear

    def test_calculate_anger_ally_involved(self):
        """Test anger when ally is involved in violence."""
        processor = BiasProcessor()
        event = WorldEvent(event_type="violence", actors=["ally_1", "attacker"])
        bias = NPCBias(allies=["ally_1"])

        anger = processor.calculate_anger(event, bias)

        assert anger > 0

    def test_form_memory_from_event_direct(self):
        """Test forming memory from direct witnessing."""
        processor = BiasProcessor()
        event = WorldEvent(
            id="evt_001",
            event_type="violence",
            timestamp=100.0,
            location=(10, 20),
            location_name="alley",
            actors=["thug", "victim"],
            notability=0.8
        )
        event.add_witness("witness_npc", WitnessType.DIRECT, clarity=0.9)
        bias = NPCBias(fearful=0.6)

        memory = processor.form_memory_from_event(
            event, bias, WitnessType.DIRECT, "witness_npc"
        )

        assert memory.event_id == "evt_001"
        assert memory.confidence > 0.8  # High for direct witness
        assert memory.source == MemorySource.SELF
        assert memory.timestamp == 100.0
        assert memory.location == "alley"
        assert "danger" in memory.tags or "violence" in memory.tags

    def test_form_memory_from_event_indirect(self):
        """Test forming memory from indirect witnessing."""
        processor = BiasProcessor()
        event = WorldEvent(
            id="evt_002",
            event_type="conversation",
            timestamp=50.0,
            location_name="bar"
        )
        event.add_witness("eavesdropper", WitnessType.INDIRECT)
        bias = NPCBias()

        memory = processor.form_memory_from_event(
            event, bias, WitnessType.INDIRECT, "eavesdropper"
        )

        assert memory.confidence < 0.6  # Lower for indirect

    def test_form_memory_paranoid_adds_conspiracy(self):
        """Test that paranoid NPCs may add conspiracy tags."""
        processor = BiasProcessor()
        event = WorldEvent(event_type="conversation")
        bias = NPCBias(paranoid=0.9)

        # Run multiple times due to randomness
        conspiracy_found = False
        for _ in range(10):
            memory = processor.form_memory_from_event(
                event, bias, WitnessType.DIRECT, "paranoid_npc"
            )
            if "conspiracy" in memory.tags:
                conspiracy_found = True
                break

        # High paranoid should eventually add conspiracy
        assert conspiracy_found

    def test_apply_bias_to_retelling_dramatic(self):
        """Test dramatic bias affects retelling."""
        processor = BiasProcessor()
        memory = NPCMemory(
            summary="Someone got hurt",
            emotional_weight=0.5
        )
        bias = NPCBias(dramatic=0.8)

        # Create a copy to test modification
        memory_copy = NPCMemory(
            summary=memory.summary,
            emotional_weight=memory.emotional_weight,
            tags=memory.tags.copy()
        )

        modified = processor.apply_bias_to_retelling(memory_copy, bias)

        # Dramatic might change "got hurt" to "nearly died"
        # or increase emotional weight
        assert (modified.summary != memory.summary or
                modified.emotional_weight >= memory.emotional_weight)

    def test_loyal_npc_softens_ally_involvement(self):
        """Test loyal NPCs soften ally involvement."""
        processor = BiasProcessor()
        memory = NPCMemory(
            summary="Ally attacked someone",
            actors=["ally_1"]
        )
        bias = NPCBias(loyal=0.8, allies=["ally_1"])

        # The softening happens in retelling
        # This tests the helper method
        softened = processor._soften_ally_involvement(
            "ally_1 attacked the victim",
            "ally_1"
        )

        assert "defended" in softened
