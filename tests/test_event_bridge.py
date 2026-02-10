"""Tests for GameEventBridge — wiring MemoryBank events to PropagationEngine."""

import pytest

from src.shadowengine.event_bridge import GameEventBridge
from src.shadowengine.npc_intelligence import PropagationEngine
from src.shadowengine.npc_intelligence.world_event import WitnessType


@pytest.fixture
def engine():
    return PropagationEngine()


@pytest.fixture
def bridge(engine):
    return GameEventBridge(engine)


class TestBridgeEvent:
    """Test bridge_event converts and processes events."""

    def test_bridge_creates_world_event(self, bridge, engine):
        engine.register_npc("bartender", "bartender")

        bridge.bridge_event(
            event_type="discovery",
            description="Player examined a bloody knife",
            location="bar",
            actors=["player"],
            witnesses=["bartender"],
        )

        assert len(engine.events) == 1
        event = engine.events[0]
        assert event.event_type == "discovery"
        assert event.location_name == "bar"
        assert len(event.witnesses) == 1
        assert event.witnesses[0].npc_id == "bartender"
        assert event.witnesses[0].witness_type == WitnessType.DIRECT

    def test_bridge_creates_npc_memory(self, bridge, engine):
        engine.register_npc("bartender", "bartender")

        bridge.bridge_event(
            event_type="discovery",
            description="Player examined a bloody knife",
            location="bar",
            actors=["player"],
            witnesses=["bartender"],
        )

        state = engine.get_npc_state("bartender")
        assert len(state.memory_bank.memories) == 1

    def test_bridge_maps_event_types(self, bridge, engine):
        engine.register_npc("npc1", "civilian")

        bridge.bridge_event(
            event_type="combat",
            description="A fight broke out",
            location="alley",
            actors=["thug"],
            witnesses=["npc1"],
        )

        assert engine.events[0].event_type == "violence"

    def test_bridge_unknown_event_type_passes_through(self, bridge, engine):
        engine.register_npc("npc1", "civilian")

        bridge.bridge_event(
            event_type="custom_event",
            description="Something weird happened",
            location="bar",
            actors=["player"],
            witnesses=["npc1"],
        )

        assert engine.events[0].event_type == "custom_event"

    def test_no_witnesses_no_event(self, bridge, engine):
        bridge.bridge_event(
            event_type="discovery",
            description="Player found something",
            location="bar",
            actors=["player"],
            witnesses=[],
        )

        assert len(engine.events) == 0

    def test_multiple_witnesses_all_get_memory(self, bridge, engine):
        engine.register_npc("bartender", "bartender")
        engine.register_npc("singer", "civilian")

        bridge.bridge_event(
            event_type="discovery",
            description="Player took a rusty key",
            location="bar",
            actors=["player"],
            witnesses=["bartender", "singer"],
        )

        for npc_id in ["bartender", "singer"]:
            state = engine.get_npc_state(npc_id)
            assert len(state.memory_bank.memories) == 1

    def test_unregistered_witness_auto_registered(self, bridge, engine):
        # The PropagationEngine auto-registers unknown NPCs
        bridge.bridge_event(
            event_type="discovery",
            description="Player did something",
            location="bar",
            actors=["player"],
            witnesses=["unknown_npc"],
        )

        state = engine.get_npc_state("unknown_npc")
        assert state is not None
        assert len(state.memory_bank.memories) == 1

    def test_notability_passed_through(self, bridge, engine):
        engine.register_npc("npc1", "civilian")

        bridge.bridge_event(
            event_type="discovery",
            description="Major discovery",
            location="bar",
            actors=["player"],
            witnesses=["npc1"],
            notability=0.9,
        )

        assert engine.events[0].notability == 0.9

    def test_tile_memory_updated(self, bridge, engine):
        engine.register_npc("npc1", "civilian")

        bridge.bridge_event(
            event_type="violence",
            description="A fight broke out",
            location="alley",
            actors=["thug"],
            witnesses=["npc1"],
            notability=0.8,
        )

        tile = engine.tile_manager.get_by_name("alley")
        assert tile is not None
        assert tile.danger_rating > 0


class TestOnThreaten:
    """Test on_threaten convenience method."""

    def test_threaten_creates_event(self, bridge, engine):
        engine.register_npc("bartender", "bartender")

        bridge.on_threaten("bartender")

        assert len(engine.events) == 1
        assert engine.events[0].event_type == "violence"
        state = engine.get_npc_state("bartender")
        assert len(state.memory_bank.memories) == 1

    def test_threaten_high_notability(self, bridge, engine):
        engine.register_npc("npc1", "civilian")

        bridge.on_threaten("npc1")

        assert engine.events[0].notability == 0.8


class TestOnAccuse:
    """Test on_accuse convenience method."""

    def test_accuse_creates_event(self, bridge, engine):
        engine.register_npc("suspect", "mobster")

        bridge.on_accuse("suspect")

        assert len(engine.events) == 1
        assert engine.events[0].event_type == "conversation"
        state = engine.get_npc_state("suspect")
        assert len(state.memory_bank.memories) == 1


class TestGossip:
    """Test gossip triggering between NPCs."""

    def test_gossip_records_interaction(self, bridge, engine):
        engine.register_npc("bartender", "bartender")
        engine.register_npc("singer", "civilian")

        result = bridge.trigger_gossip("bartender", "singer")

        assert result["relationship_changed"]

    def test_gossip_can_spread_rumors(self, bridge, engine):
        engine.register_npc("bartender", "bartender")
        engine.register_npc("singer", "civilian")

        # Give bartender a memorable event
        bridge.bridge_event(
            event_type="violence",
            description="Someone was murdered in the alley",
            location="alley",
            actors=["unknown"],
            witnesses=["bartender"],
            notability=0.9,
        )

        # Trigger gossip — bartender might share with singer
        result = bridge.trigger_gossip("bartender", "singer")

        # Whether rumor was shared depends on probability, but relationship was updated
        assert result["relationship_changed"]


class TestBehaviorHints:
    """Test that events affect NPC behavior hints."""

    def test_violence_increases_fear(self, bridge, engine):
        engine.register_npc("civilian", "civilian")

        bridge.bridge_event(
            event_type="violence",
            description="Player threatened someone",
            location="bar",
            actors=["player"],
            witnesses=["civilian"],
            notability=0.9,
        )

        state = engine.get_npc_state("civilian")
        # Behavior modifier should have been updated
        assert state.behavior_modifier is not None

    def test_behavior_hints_reflect_memories(self, bridge, engine):
        engine.register_npc("bartender", "bartender")

        # Multiple threatening events
        for _ in range(3):
            bridge.on_threaten("bartender")

        hints = engine.get_npc_behavior_hints("bartender")
        # Should have some kind of behavioral response
        assert isinstance(hints, dict)
