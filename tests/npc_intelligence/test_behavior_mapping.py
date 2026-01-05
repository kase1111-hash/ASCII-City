"""Tests for MemoryBehaviorMapping system."""

import pytest
from src.shadowengine.npc_intelligence.behavior_mapping import (
    BehaviorType, BehaviorModifier, MemoryBehaviorMapping,
    MemoryBehaviorSystem, MEMORY_TAG_BEHAVIORS
)
from src.shadowengine.npc_intelligence.npc_memory import NPCMemory


class TestBehaviorModifier:
    """Tests for BehaviorModifier dataclass."""

    def test_modifier_creation(self):
        """Test creating behavior modifier."""
        modifier = BehaviorModifier(
            trusts=0.5,
            reveals=0.3,
            fears=-0.2
        )

        assert modifier.trusts == 0.5
        assert modifier.reveals == 0.3
        assert modifier.fears == -0.2

    def test_modifier_apply(self):
        """Test applying modifiers together."""
        mod1 = BehaviorModifier(trusts=0.3, fears=0.2)
        mod2 = BehaviorModifier(trusts=0.2, fears=0.3)

        combined = mod1.apply(mod2)

        assert combined.trusts == 0.5
        assert combined.fears == 0.5

    def test_modifier_apply_clamping(self):
        """Test that apply clamps values."""
        mod1 = BehaviorModifier(trusts=0.8)
        mod2 = BehaviorModifier(trusts=0.5)

        combined = mod1.apply(mod2)

        assert combined.trusts == 1.0  # Clamped

    def test_modifier_scale(self):
        """Test scaling modifiers."""
        modifier = BehaviorModifier(trusts=0.6, fears=0.4)

        scaled = modifier.scale(0.5)

        assert scaled.trusts == 0.3
        assert scaled.fears == 0.2

    def test_modifier_serialization(self):
        """Test modifier to_dict and from_dict."""
        modifier = BehaviorModifier(
            trusts=0.5,
            reveals=0.3,
            cooperates=-0.2,
            fears=0.4
        )

        data = modifier.to_dict()
        restored = BehaviorModifier.from_dict(data)

        assert restored.trusts == modifier.trusts
        assert restored.reveals == modifier.reveals
        assert restored.cooperates == modifier.cooperates
        assert restored.fears == modifier.fears


class TestMemoryBehaviorMapping:
    """Tests for MemoryBehaviorMapping."""

    def test_mapping_init(self):
        """Test mapping initialization."""
        mapping = MemoryBehaviorMapping()

        assert mapping.tag_behaviors is not None
        assert "danger" in mapping.tag_behaviors

    def test_calculate_recency_weight(self):
        """Test recency weight calculation."""
        mapping = MemoryBehaviorMapping()

        recent_weight = mapping.calculate_recency_weight(99.0, 100.0)
        old_weight = mapping.calculate_recency_weight(0.0, 100.0)

        # Recent memories should have higher or equal weight
        assert recent_weight >= old_weight
        assert recent_weight <= 1.0
        assert old_weight >= 0.1

    def test_get_behavior_from_memory_danger(self):
        """Test getting behavior from danger memory."""
        mapping = MemoryBehaviorMapping()
        memory = NPCMemory(tags=["danger"], confidence=1.0)

        behavior, modifier = mapping.get_behavior_from_memory(memory)

        assert behavior == BehaviorType.AVOID_AREA
        assert modifier.cooperates < 0

    def test_get_behavior_from_memory_player_helpful(self):
        """Test getting behavior from player-helpful memory."""
        mapping = MemoryBehaviorMapping()
        memory = NPCMemory(tags=["player_helpful"], confidence=1.0)

        behavior, modifier = mapping.get_behavior_from_memory(memory)

        assert behavior == BehaviorType.HELP_PLAYER
        assert modifier.trusts > 0
        assert modifier.reveals > 0

    def test_get_behavior_from_memory_mob_involved(self):
        """Test getting behavior from mob-involved memory."""
        mapping = MemoryBehaviorMapping()
        memory = NPCMemory(tags=["mob_involved"], confidence=1.0)

        behavior, modifier = mapping.get_behavior_from_memory(memory)

        assert behavior == BehaviorType.SILENCE
        assert modifier.reveals < 0
        assert modifier.fears > 0

    def test_aggregate_modifiers(self):
        """Test aggregating modifiers from multiple memories."""
        mapping = MemoryBehaviorMapping()
        memories = [
            NPCMemory(tags=["player_helpful"], confidence=0.8, timestamp=90.0),
            NPCMemory(tags=["danger"], confidence=0.5, timestamp=80.0)
        ]

        total = mapping.aggregate_modifiers(memories, current_time=100.0)

        # Should have combined effects
        assert isinstance(total, BehaviorModifier)

    def test_get_response_type_flee(self):
        """Test response type detection - flee."""
        mapping = MemoryBehaviorMapping()
        modifier = BehaviorModifier(fears=0.7)

        response = mapping.get_response_type(modifier)

        assert response == "flee"

    def test_get_response_type_help(self):
        """Test response type detection - help."""
        mapping = MemoryBehaviorMapping()
        modifier = BehaviorModifier(trusts=0.7)

        response = mapping.get_response_type(modifier)

        assert response == "help"

    def test_get_response_type_lie(self):
        """Test response type detection - lie."""
        mapping = MemoryBehaviorMapping()
        modifier = BehaviorModifier(reveals=-0.7)

        response = mapping.get_response_type(modifier)

        assert response == "lie"

    def test_get_response_type_refuse(self):
        """Test response type detection - refuse."""
        mapping = MemoryBehaviorMapping()
        modifier = BehaviorModifier(cooperates=-0.5)

        response = mapping.get_response_type(modifier)

        assert response == "refuse"

    def test_get_response_type_neutral(self):
        """Test response type detection - neutral."""
        mapping = MemoryBehaviorMapping()
        modifier = BehaviorModifier()

        response = mapping.get_response_type(modifier)

        assert response == "neutral"

    def test_will_share_information(self):
        """Test share information check."""
        mapping = MemoryBehaviorMapping()

        willing = BehaviorModifier(reveals=0.2)
        unwilling = BehaviorModifier(reveals=-0.5)

        assert mapping.will_share_information(willing)
        assert not mapping.will_share_information(unwilling)

    def test_will_cooperate(self):
        """Test cooperation check."""
        mapping = MemoryBehaviorMapping()

        cooperative = BehaviorModifier(cooperates=0.3, fears=0.2)
        fearful = BehaviorModifier(cooperates=0.3, fears=0.8)
        uncooperative = BehaviorModifier(cooperates=-0.5)

        assert mapping.will_cooperate(cooperative)
        assert not mapping.will_cooperate(fearful)
        assert not mapping.will_cooperate(uncooperative)

    def test_get_dialogue_modifiers_fearful(self):
        """Test dialogue modifiers for fearful state."""
        mapping = MemoryBehaviorMapping()
        modifier = BehaviorModifier(fears=0.6)

        hints = mapping.get_dialogue_modifiers(modifier)

        assert hints["tone"] == "fearful"

    def test_get_dialogue_modifiers_friendly(self):
        """Test dialogue modifiers for friendly state."""
        mapping = MemoryBehaviorMapping()
        modifier = BehaviorModifier(trusts=0.6)

        hints = mapping.get_dialogue_modifiers(modifier)

        assert hints["tone"] == "friendly"

    def test_get_dialogue_modifiers_evasive(self):
        """Test dialogue modifiers for evasive state."""
        mapping = MemoryBehaviorMapping()
        modifier = BehaviorModifier(reveals=-0.4)

        hints = mapping.get_dialogue_modifiers(modifier)

        assert hints["honesty"] == "evasive"


class TestMemoryBehaviorSystem:
    """Tests for MemoryBehaviorSystem."""

    def test_system_init(self):
        """Test system initialization."""
        system = MemoryBehaviorSystem()

        assert system.mapping is not None
        assert len(system.npc_modifiers) == 0

    def test_update_npc_behavior(self):
        """Test updating NPC behavior."""
        system = MemoryBehaviorSystem()
        memories = [
            NPCMemory(tags=["player_helpful"], confidence=0.8, timestamp=90.0),
            NPCMemory(tags=["player_trustworthy"], confidence=0.7, timestamp=85.0)
        ]

        modifier = system.update_npc_behavior("npc_001", memories, current_time=100.0)

        assert modifier.trusts > 0
        assert "npc_001" in system.npc_modifiers

    def test_get_npc_response(self):
        """Test getting NPC response type."""
        system = MemoryBehaviorSystem()
        system.npc_modifiers["npc_001"] = BehaviorModifier(trusts=0.7)

        response = system.get_npc_response("npc_001")

        assert response == "help"

    def test_get_npc_response_unknown(self):
        """Test getting response for unknown NPC."""
        system = MemoryBehaviorSystem()

        response = system.get_npc_response("unknown_npc")

        assert response == "neutral"

    def test_get_npc_dialogue_hints(self):
        """Test getting dialogue hints."""
        system = MemoryBehaviorSystem()
        system.npc_modifiers["npc_001"] = BehaviorModifier(fears=0.6)

        hints = system.get_npc_dialogue_hints("npc_001")

        assert hints["tone"] == "fearful"

    def test_will_npc_share(self):
        """Test checking if NPC will share."""
        system = MemoryBehaviorSystem()
        system.npc_modifiers["willing"] = BehaviorModifier(reveals=0.3)
        system.npc_modifiers["unwilling"] = BehaviorModifier(reveals=-0.5)

        assert system.will_npc_share("willing")
        assert not system.will_npc_share("unwilling")

    def test_will_npc_cooperate(self):
        """Test checking if NPC will cooperate."""
        system = MemoryBehaviorSystem()
        system.npc_modifiers["coop"] = BehaviorModifier(cooperates=0.3)
        system.npc_modifiers["uncoop"] = BehaviorModifier(cooperates=-0.5)

        assert system.will_npc_cooperate("coop")
        assert not system.will_npc_cooperate("uncoop")

    def test_add_memory_effect(self):
        """Test adding effect of single memory."""
        system = MemoryBehaviorSystem()
        system.npc_modifiers["npc_001"] = BehaviorModifier(trusts=0.2)

        memory = NPCMemory(tags=["player_helpful"], confidence=1.0)
        system.add_memory_effect("npc_001", memory)

        assert system.npc_modifiers["npc_001"].trusts > 0.2

    def test_clear_npc(self):
        """Test clearing NPC modifiers."""
        system = MemoryBehaviorSystem()
        system.npc_modifiers["npc_001"] = BehaviorModifier(trusts=0.5)

        system.clear_npc("npc_001")

        assert "npc_001" not in system.npc_modifiers

    def test_system_serialization(self):
        """Test system to_dict and from_dict."""
        system = MemoryBehaviorSystem()
        system.npc_modifiers["npc_001"] = BehaviorModifier(trusts=0.5)
        system.npc_modifiers["npc_002"] = BehaviorModifier(fears=0.3)

        data = system.to_dict()
        restored = MemoryBehaviorSystem.from_dict(data)

        assert len(restored.npc_modifiers) == 2
        assert restored.npc_modifiers["npc_001"].trusts == 0.5
        assert restored.npc_modifiers["npc_002"].fears == 0.3
