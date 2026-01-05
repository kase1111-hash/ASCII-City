"""
Tests for Memory Bank - the unified memory system.

These tests verify that the memory bank correctly:
- Coordinates all three memory layers
- Records events with proper propagation
- Handles save/load operations
"""

import pytest
import os
import tempfile
from shadowengine.memory import MemoryBank, EventType


class TestMemoryBankBasics:
    """Basic memory bank functionality."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_create_memory_bank(self, memory_bank):
        """Memory bank initializes correctly."""
        assert memory_bank.world is not None
        assert memory_bank.player is not None
        assert len(memory_bank.characters) == 0

    @pytest.mark.unit
    @pytest.mark.memory
    def test_register_character(self, memory_bank):
        """Can register characters."""
        char_memory = memory_bank.register_character("alice")

        assert "alice" in memory_bank.characters
        assert char_memory.character_id == "alice"

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_character_memory(self, memory_bank):
        """Can retrieve character memory."""
        memory_bank.register_character("bob")

        bob_memory = memory_bank.get_character_memory("bob")
        assert bob_memory is not None
        assert bob_memory.character_id == "bob"

        # Non-existent character returns None
        assert memory_bank.get_character_memory("nobody") is None


class TestMemoryBankEventRecording:
    """Event recording with propagation to all layers."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_record_witnessed_event(self, memory_bank):
        """Recording events updates all relevant memory layers."""
        memory_bank.register_character("alice")
        memory_bank.register_character("bob")

        event = memory_bank.record_witnessed_event(
            event_type=EventType.ACTION,
            description="Something happened",
            location="study",
            actors=["alice"],
            witnesses=["bob"],
            player_witnessed=True
        )

        # World memory should have event
        assert len(memory_bank.world.events) == 1

        # Witness should have belief
        bob_memory = memory_bank.get_character_memory("bob")
        assert len(bob_memory.beliefs) == 1

        # Player should have discovery
        assert len(memory_bank.player.discoveries) == 1

    @pytest.mark.unit
    @pytest.mark.memory
    def test_event_not_witnessed_by_player(self, memory_bank):
        """Events not witnessed by player don't create player discoveries."""
        memory_bank.register_character("alice")

        memory_bank.record_witnessed_event(
            event_type=EventType.ACTION,
            description="Secret event",
            location="hidden_room",
            actors=["alice"],
            witnesses=["alice"],
            player_witnessed=False
        )

        # World has event
        assert len(memory_bank.world.events) == 1

        # Player doesn't know
        assert len(memory_bank.player.discoveries) == 0

    @pytest.mark.unit
    @pytest.mark.memory
    def test_character_tells_player(self, memory_bank):
        """Character telling player truth or lies."""
        memory_bank.register_character("alice")

        # Truth
        memory_bank.character_tells_player(
            character_id="alice",
            information="The key is under the mat",
            is_true=True,
            topic="key location"
        )

        # Player has discovery
        assert len(memory_bank.player.discoveries) == 1

        # Alice has interaction recorded
        alice_memory = memory_bank.get_character_memory("alice")
        assert len(alice_memory.player_interactions) == 1

    @pytest.mark.unit
    @pytest.mark.memory
    def test_player_discovers(self, memory_bank):
        """Direct player discovery."""
        memory_bank.player_discovers(
            fact_id="hidden_safe",
            description="A hidden safe behind the painting",
            location="study",
            source="examined painting",
            is_evidence=True
        )

        # World has discovery event
        discoveries = memory_bank.world.get_events_by_type(EventType.DISCOVERY)
        assert len(discoveries) == 1

        # Player knows
        assert memory_bank.player.has_discovered("hidden_safe")


class TestMemoryBankTime:
    """Time management."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_advance_time(self, memory_bank):
        """Time advances correctly."""
        assert memory_bank.current_time == 0

        memory_bank.advance_time(10)
        assert memory_bank.current_time == 10

    @pytest.mark.unit
    @pytest.mark.memory
    def test_events_get_current_timestamp(self, memory_bank):
        """Events get the current time as timestamp."""
        memory_bank.advance_time(50)

        memory_bank.record_witnessed_event(
            event_type=EventType.ACTION,
            description="Later event",
            location="study",
            actors=["player"]
        )

        assert memory_bank.world.events[0].timestamp == 50


class TestMemoryBankPersistence:
    """Save and load functionality."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_save_memory_bank(self, populated_memory_bank):
        """Can save memory bank to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_save.json")
            populated_memory_bank.save(filepath)

            assert os.path.exists(filepath)

    @pytest.mark.unit
    @pytest.mark.memory
    def test_load_memory_bank(self, populated_memory_bank):
        """Can load memory bank from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_save.json")
            populated_memory_bank.game_seed = 12345
            populated_memory_bank.save(filepath)

            restored = MemoryBank.load(filepath)

            assert restored.game_seed == 12345
            assert len(restored.world.events) > 0
            assert len(restored.characters) == 2
            assert restored.player.has_discovered("clue_1")

    @pytest.mark.unit
    @pytest.mark.memory
    def test_roundtrip_preservation(self, memory_bank):
        """Save/load roundtrip preserves all data."""
        # Build complex state
        memory_bank.game_seed = 42
        memory_bank.register_character("alice")
        memory_bank.register_character("bob")

        memory_bank.advance_time(100)

        memory_bank.record_witnessed_event(
            event_type=EventType.DEATH,
            description="A murder occurred",
            location="library",
            actors=["victim", "killer"],
            witnesses=["alice"],
            player_witnessed=True
        )

        memory_bank.player.add_suspicion("alice", 0.5)
        memory_bank.player.update_relationship("bob", 10)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "roundtrip.json")
            memory_bank.save(filepath)
            restored = MemoryBank.load(filepath)

            assert restored.game_seed == 42
            assert restored.current_time == 100
            assert len(restored.world.events) == 1
            assert "alice" in restored.characters
            assert restored.player.get_suspicion("alice") == 0.5
            assert restored.player.get_relationship("bob") == 10


class TestMemoryBankSummary:
    """Summary and status functionality."""

    @pytest.mark.unit
    @pytest.mark.memory
    def test_get_summary(self, populated_memory_bank):
        """Can get memory bank summary."""
        summary = populated_memory_bank.get_summary()

        assert "current_time" in summary
        assert "total_events" in summary
        assert "characters_tracked" in summary
        assert "player_discoveries" in summary
        assert "player_dominant_shade" in summary
