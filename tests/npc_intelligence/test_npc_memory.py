"""Tests for NPCMemory system."""

import pytest
from src.shadowengine.npc_intelligence.npc_memory import (
    NPCMemory, MemorySource, MemoryDecaySystem,
    NPCMemoryBank, NPC_MEMORY_CAPACITY
)


class TestNPCMemory:
    """Tests for NPCMemory dataclass."""

    def test_memory_creation(self):
        """Test creating a memory."""
        memory = NPCMemory(
            event_id="evt_001",
            summary="Someone got hurt near the falls",
            tags=["danger", "water"],
            confidence=0.8,
            emotional_weight=0.6,
            fear=0.4,
            source=MemorySource.SELF,
            timestamp=100.0,
            location="waterfall"
        )

        assert memory.event_id == "evt_001"
        assert memory.summary == "Someone got hurt near the falls"
        assert "danger" in memory.tags
        assert memory.confidence == 0.8
        assert memory.memory_id.startswith("mem_")

    def test_memory_auto_id(self):
        """Test that memories get auto-generated IDs."""
        mem1 = NPCMemory(summary="test1")
        mem2 = NPCMemory(summary="test2")

        assert mem1.memory_id != mem2.memory_id

    def test_retention_priority(self):
        """Test retention priority calculation."""
        high_priority = NPCMemory(
            confidence=1.0,
            emotional_weight=0.8,
            fear=0.9,
            source=MemorySource.SELF
        )
        low_priority = NPCMemory(
            confidence=0.2,
            emotional_weight=0.1,
            fear=0.0,
            source=MemorySource.RUMOR
        )

        assert high_priority.get_retention_priority() > low_priority.get_retention_priority()

    def test_share_probability(self):
        """Test share probability calculation."""
        shareable = NPCMemory(
            emotional_weight=0.9,
            confidence=0.8,
            fear=0.5,
            anger=0.5
        )
        not_shareable = NPCMemory(
            emotional_weight=0.1,
            confidence=0.2,
            fear=0.0,
            anger=0.0
        )

        assert shareable.get_share_probability() > not_shareable.get_share_probability()

    def test_has_tag(self):
        """Test tag checking."""
        memory = NPCMemory(tags=["danger", "violence", "mob"])

        assert memory.has_tag("danger")
        assert memory.has_tag("violence")
        assert not memory.has_tag("safety")

    def test_add_tag(self):
        """Test adding tags."""
        memory = NPCMemory(tags=["danger"])
        memory.add_tag("conspiracy")
        memory.add_tag("danger")  # Duplicate

        assert "conspiracy" in memory.tags
        assert memory.tags.count("danger") == 1  # No duplicates

    def test_involves_actor(self):
        """Test actor checking."""
        memory = NPCMemory(actors=["thug", "victim"])

        assert memory.involves_actor("thug")
        assert memory.involves_actor("victim")
        assert not memory.involves_actor("bystander")

    def test_recall(self):
        """Test recalling memory updates timestamp."""
        memory = NPCMemory(timestamp=100.0, last_recalled=100.0)
        memory.recall(150.0)

        assert memory.last_recalled == 150.0

    def test_memory_serialization(self):
        """Test memory to_dict and from_dict."""
        memory = NPCMemory(
            event_id="evt_test",
            summary="Test event",
            tags=["test", "serialization"],
            confidence=0.75,
            emotional_weight=0.5,
            fear=0.3,
            anger=0.2,
            source=MemorySource.FRIEND,
            source_npc="friend_001",
            timestamp=200.0,
            location="test_location",
            location_coords=(10, 20),
            is_traumatic=True,
            actors=["actor1", "actor2"]
        )

        data = memory.to_dict()
        restored = NPCMemory.from_dict(data)

        assert restored.event_id == memory.event_id
        assert restored.summary == memory.summary
        assert restored.tags == memory.tags
        assert restored.confidence == memory.confidence
        assert restored.source == memory.source
        assert restored.location_coords == (10, 20)


class TestMemoryDecaySystem:
    """Tests for MemoryDecaySystem."""

    def test_basic_decay(self):
        """Test basic memory decay."""
        system = MemoryDecaySystem()
        memory = NPCMemory(confidence=1.0, decay_rate=0.1)

        new_confidence = system.decay_memory(memory, dt=1.0)

        assert new_confidence < 1.0
        assert memory.confidence == new_confidence

    def test_emotional_memory_decays_slower(self):
        """Test that emotional memories decay slower."""
        system = MemoryDecaySystem()

        emotional = NPCMemory(confidence=1.0, decay_rate=0.1, emotional_weight=0.8)
        normal = NPCMemory(confidence=1.0, decay_rate=0.1, emotional_weight=0.2)

        system.decay_memory(emotional, dt=1.0)
        system.decay_memory(normal, dt=1.0)

        assert emotional.confidence > normal.confidence

    def test_traumatic_memory_barely_decays(self):
        """Test that traumatic memories barely decay."""
        system = MemoryDecaySystem()

        traumatic = NPCMemory(confidence=1.0, decay_rate=0.1, is_traumatic=True)
        normal = NPCMemory(confidence=1.0, decay_rate=0.1, is_traumatic=False)

        system.decay_memory(traumatic, dt=1.0)
        system.decay_memory(normal, dt=1.0)

        assert traumatic.confidence > normal.confidence

    def test_high_fear_memory_barely_decays(self):
        """Test that high-fear memories barely decay."""
        system = MemoryDecaySystem()

        fearful = NPCMemory(confidence=1.0, decay_rate=0.1, fear=0.9)
        normal = NPCMemory(confidence=1.0, decay_rate=0.1, fear=0.1)

        system.decay_memory(fearful, dt=1.0)
        system.decay_memory(normal, dt=1.0)

        assert fearful.confidence > normal.confidence

    def test_decay_all_memories(self):
        """Test decaying all memories and removing forgotten ones."""
        system = MemoryDecaySystem()
        memories = [
            NPCMemory(confidence=1.0, decay_rate=0.01),
            NPCMemory(confidence=0.1, decay_rate=0.5),  # Will be forgotten
            NPCMemory(confidence=0.8, decay_rate=0.01)
        ]

        result = system.decay_all_memories(memories, dt=1.0)

        # Low confidence memory should be pruned
        assert len(result) <= len(memories)

    def test_prune_memories_over_capacity(self):
        """Test pruning memories when over capacity."""
        system = MemoryDecaySystem()
        memories = [
            NPCMemory(summary=f"Memory {i}", confidence=0.1 + (i * 0.1))
            for i in range(10)
        ]

        pruned = system.prune_memories(memories, capacity=5)

        assert len(pruned) == 5
        # Should keep highest priority memories
        assert all(m.confidence >= 0.5 for m in pruned)

    def test_prune_memories_under_capacity(self):
        """Test no pruning when under capacity."""
        system = MemoryDecaySystem()
        memories = [NPCMemory(summary=f"Memory {i}") for i in range(3)]

        pruned = system.prune_memories(memories, capacity=10)

        assert len(pruned) == 3

    def test_get_memory_capacity(self):
        """Test getting memory capacity by NPC type."""
        system = MemoryDecaySystem()

        assert system.get_memory_capacity("bartender") == 25
        assert system.get_memory_capacity("informant") == 40
        assert system.get_memory_capacity("unknown_type") == 20  # default


class TestNPCMemoryBank:
    """Tests for NPCMemoryBank."""

    def test_memory_bank_creation(self):
        """Test creating a memory bank."""
        bank = NPCMemoryBank("npc_001", "bartender")

        assert bank.npc_id == "npc_001"
        assert bank.npc_type == "bartender"
        assert bank.capacity == 25
        assert len(bank.memories) == 0

    def test_add_memory(self):
        """Test adding memories."""
        bank = NPCMemoryBank("npc_001")
        memory = NPCMemory(summary="Test memory")

        bank.add_memory(memory)

        assert len(bank.memories) == 1
        assert bank.memories[0].summary == "Test memory"

    def test_add_memory_prunes_at_capacity(self):
        """Test that adding memories prunes at capacity."""
        bank = NPCMemoryBank("npc_001")
        bank.capacity = 5

        for i in range(10):
            bank.add_memory(NPCMemory(
                summary=f"Memory {i}",
                confidence=0.1 + (i * 0.1)
            ))

        assert len(bank.memories) <= 5

    def test_update_decays_memories(self):
        """Test that update decays memories."""
        bank = NPCMemoryBank("npc_001")
        bank.add_memory(NPCMemory(confidence=1.0, decay_rate=0.1))

        bank.update(dt=1.0)

        assert bank.memories[0].confidence < 1.0

    def test_get_memories_about(self):
        """Test finding memories about a subject."""
        bank = NPCMemoryBank("npc_001")
        bank.add_memory(NPCMemory(summary="The mob is dangerous", tags=["mob"]))
        bank.add_memory(NPCMemory(summary="Nice weather today", tags=["weather"]))
        bank.add_memory(NPCMemory(summary="mob related", actors=["mob"]))

        mob_memories = bank.get_memories_about("mob")

        assert len(mob_memories) == 2

    def test_get_memories_at_location(self):
        """Test finding memories at location."""
        bank = NPCMemoryBank("npc_001")
        bank.add_memory(NPCMemory(summary="Event at bar", location="bar"))
        bank.add_memory(NPCMemory(summary="Event at alley", location="alley"))
        bank.add_memory(NPCMemory(summary="Another at bar", location="bar"))

        bar_memories = bank.get_memories_at_location("bar")

        assert len(bar_memories) == 2

    def test_get_memories_by_tag(self):
        """Test finding memories by tag."""
        bank = NPCMemoryBank("npc_001")
        bank.add_memory(NPCMemory(tags=["danger", "violence"]))
        bank.add_memory(NPCMemory(tags=["safety"]))
        bank.add_memory(NPCMemory(tags=["danger"]))

        danger_memories = bank.get_memories_by_tag("danger")

        assert len(danger_memories) == 2

    def test_get_recent_memories(self):
        """Test getting most recent memories."""
        bank = NPCMemoryBank("npc_001")
        bank.add_memory(NPCMemory(summary="Old", timestamp=100.0))
        bank.add_memory(NPCMemory(summary="Newer", timestamp=200.0))
        bank.add_memory(NPCMemory(summary="Newest", timestamp=300.0))

        recent = bank.get_recent_memories(count=2)

        assert len(recent) == 2
        assert recent[0].summary == "Newest"
        assert recent[1].summary == "Newer"

    def test_get_emotional_memories(self):
        """Test getting high-emotion memories."""
        bank = NPCMemoryBank("npc_001")
        bank.add_memory(NPCMemory(summary="Emotional", emotional_weight=0.8))
        bank.add_memory(NPCMemory(summary="Neutral", emotional_weight=0.2))

        emotional = bank.get_emotional_memories(threshold=0.5)

        assert len(emotional) == 1
        assert emotional[0].summary == "Emotional"

    def test_get_shareable_memories(self):
        """Test getting shareable memories."""
        bank = NPCMemoryBank("npc_001")
        bank.add_memory(NPCMemory(
            summary="Shareable",
            emotional_weight=0.8,
            confidence=0.9
        ))
        bank.add_memory(NPCMemory(
            summary="Not shareable",
            emotional_weight=0.1,
            confidence=0.2
        ))

        shareable = bank.get_shareable_memories(threshold=0.3)

        assert len(shareable) == 1
        assert shareable[0].summary == "Shareable"

    def test_has_memory_of_event(self):
        """Test checking for event memory."""
        bank = NPCMemoryBank("npc_001")
        bank.add_memory(NPCMemory(event_id="evt_001"))
        bank.add_memory(NPCMemory(event_id="evt_002"))

        assert bank.has_memory_of_event("evt_001")
        assert bank.has_memory_of_event("evt_002")
        assert not bank.has_memory_of_event("evt_003")

    def test_get_memory_of_event(self):
        """Test getting specific event memory."""
        bank = NPCMemoryBank("npc_001")
        bank.add_memory(NPCMemory(event_id="evt_001", summary="Event 1"))
        bank.add_memory(NPCMemory(event_id="evt_002", summary="Event 2"))

        memory = bank.get_memory_of_event("evt_001")

        assert memory is not None
        assert memory.summary == "Event 1"
        assert bank.get_memory_of_event("evt_999") is None

    def test_recall_memory(self):
        """Test recalling a memory."""
        bank = NPCMemoryBank("npc_001")
        memory = NPCMemory(last_recalled=0.0)
        bank.add_memory(memory)
        bank.current_time = 100.0

        recalled = bank.recall_memory(memory.memory_id)

        assert recalled is not None
        assert recalled.last_recalled == 100.0

    def test_memory_bank_serialization(self):
        """Test memory bank to_dict and from_dict."""
        bank = NPCMemoryBank("npc_001", "informant")
        bank.add_memory(NPCMemory(summary="Memory 1", confidence=0.8))
        bank.add_memory(NPCMemory(summary="Memory 2", confidence=0.6))
        bank.current_time = 500.0

        data = bank.to_dict()
        restored = NPCMemoryBank.from_dict(data)

        assert restored.npc_id == bank.npc_id
        assert restored.npc_type == bank.npc_type
        assert len(restored.memories) == 2
        assert restored.current_time == 500.0
