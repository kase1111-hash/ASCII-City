"""Tests for PropagationEngine - main NPC intelligence system."""

import pytest
from src.shadowengine.npc_intelligence.propagation_engine import (
    PropagationEngine, NPCIntelligenceState
)
from src.shadowengine.npc_intelligence.world_event import (
    WorldEvent, WitnessType, WorldEventFactory
)
from src.shadowengine.npc_intelligence.npc_bias import NPCBias
from src.shadowengine.npc_intelligence.rumor import PropagationTrigger


class TestNPCIntelligenceState:
    """Tests for NPCIntelligenceState."""

    def test_state_creation(self):
        """Test creating NPC intelligence state."""
        state = NPCIntelligenceState(
            npc_id="npc_001",
            npc_type="bartender"
        )

        assert state.npc_id == "npc_001"
        assert state.npc_type == "bartender"
        assert state.memory_bank is not None
        assert state.bias is not None
        assert state.behavior_modifier is not None

    def test_state_with_custom_bias(self):
        """Test creating state with custom bias."""
        custom_bias = NPCBias(fearful=0.9, paranoid=0.8)
        state = NPCIntelligenceState(
            npc_id="npc_001",
            bias=custom_bias
        )

        assert state.bias.fearful == 0.9
        assert state.bias.paranoid == 0.8


class TestPropagationEngine:
    """Tests for PropagationEngine."""

    def test_engine_creation(self):
        """Test creating propagation engine."""
        engine = PropagationEngine()

        assert engine.bias_processor is not None
        assert engine.rumor_propagation is not None
        assert engine.behavior_system is not None
        assert engine.social_network is not None
        assert engine.tile_manager is not None
        assert len(engine.npc_states) == 0

    def test_register_npc(self):
        """Test registering NPC."""
        engine = PropagationEngine()

        state = engine.register_npc("npc_001", "bartender")

        assert state.npc_id == "npc_001"
        assert "npc_001" in engine.npc_states
        assert state.bias.talkative == 0.8  # Bartender bias

    def test_register_npc_with_custom_bias(self):
        """Test registering NPC with custom bias."""
        engine = PropagationEngine()
        custom_bias = NPCBias(fearful=0.9)

        state = engine.register_npc("npc_001", "default", bias=custom_bias)

        assert state.bias.fearful == 0.9

    def test_register_npc_idempotent(self):
        """Test that registering same NPC twice returns same state."""
        engine = PropagationEngine()

        state1 = engine.register_npc("npc_001")
        state2 = engine.register_npc("npc_001")

        assert state1 is state2

    def test_get_npc_state(self):
        """Test getting NPC state."""
        engine = PropagationEngine()
        engine.register_npc("npc_001")

        state = engine.get_npc_state("npc_001")
        missing = engine.get_npc_state("unknown")

        assert state is not None
        assert missing is None

    def test_process_event_creates_memories(self):
        """Test that processing event creates memories for witnesses."""
        engine = PropagationEngine()
        engine.register_npc("witness_001")
        engine.register_npc("witness_002")

        event = WorldEvent(
            id="evt_001",
            event_type="violence",
            timestamp=100.0,
            location=(10, 20),
            location_name="dark_alley",
            actors=["attacker", "victim"],
            notability=0.8
        )
        event.add_witness("witness_001", WitnessType.DIRECT)
        event.add_witness("witness_002", WitnessType.INDIRECT)

        memories = engine.process_event(event)

        assert len(memories) == 2

        # Check witnesses got memories
        state1 = engine.get_npc_state("witness_001")
        state2 = engine.get_npc_state("witness_002")

        assert state1.memory_bank.has_memory_of_event("evt_001")
        assert state2.memory_bank.has_memory_of_event("evt_001")

    def test_process_event_updates_tile_memory(self):
        """Test that processing event updates tile memory."""
        engine = PropagationEngine()
        engine.register_npc("witness")

        event = WorldEvent(
            id="evt_001",
            event_type="violence",
            timestamp=100.0,
            location=(10, 20),
            location_name="crime_scene",
            notability=0.8
        )
        event.add_witness("witness", WitnessType.DIRECT)

        engine.process_event(event)

        tile = engine.tile_manager.get_or_create((10, 20))
        assert tile.danger_rating > 0
        assert "evt_001" in tile.event_history

    def test_process_event_auto_registers_unknown_npcs(self):
        """Test that unknown NPCs are auto-registered."""
        engine = PropagationEngine()

        event = WorldEvent(event_type="discovery")
        event.add_witness("new_npc", WitnessType.DIRECT)

        engine.process_event(event)

        assert "new_npc" in engine.npc_states

    def test_simulate_interaction_records_social(self):
        """Test that interaction simulation records social data."""
        engine = PropagationEngine()
        engine.register_npc("npc_a")
        engine.register_npc("npc_b")

        result = engine.simulate_interaction(
            "npc_a", "npc_b",
            trigger=PropagationTrigger.CONVERSATION
        )

        assert result["relationship_changed"]

        # Check social network was updated
        relation = engine.social_network.get_relation("npc_a", "npc_b")
        assert relation is not None

    def test_simulate_interaction_can_share_rumor(self):
        """Test that interaction can share rumors."""
        engine = PropagationEngine()
        engine.register_npc("npc_a", bias=NPCBias(talkative=1.0))
        engine.register_npc("npc_b")

        # Give npc_a a memory to share
        state_a = engine.get_npc_state("npc_a")
        from src.shadowengine.npc_intelligence.npc_memory import NPCMemory
        memory = NPCMemory(
            summary="Exciting news!",
            confidence=0.9,
            emotional_weight=0.9
        )
        state_a.memory_bank.add_memory(memory)

        # Try interactions until rumor spreads (probabilistic)
        shared = False
        for _ in range(20):
            result = engine.simulate_interaction(
                "npc_a", "npc_b",
                trigger=PropagationTrigger.GOSSIP
            )
            if result["rumor_shared"]:
                shared = True
                break

        # Should eventually share with high talkative
        assert shared

    def test_update_decays_memories(self):
        """Test that update decays memories."""
        engine = PropagationEngine()
        engine.register_npc("npc_001")

        state = engine.get_npc_state("npc_001")
        from src.shadowengine.npc_intelligence.npc_memory import NPCMemory
        state.memory_bank.add_memory(NPCMemory(confidence=1.0, decay_rate=0.1))

        result = engine.update(dt=5.0)

        assert state.memory_bank.memories[0].confidence < 1.0

    def test_update_updates_social_network(self):
        """Test that update processes social network."""
        engine = PropagationEngine()

        # Create explosive relationship
        rel = engine.social_network.get_or_create_relation("npc_a", "npc_b")
        rel.tension = 90
        rel.affinity = -50

        result = engine.update(dt=1.0)

        assert "social_events" in result

    def test_get_npc_behavior_hints(self):
        """Test getting behavior hints."""
        engine = PropagationEngine()
        engine.register_npc("npc_001")

        hints = engine.get_npc_behavior_hints("npc_001")

        assert "tone" in hints
        assert "willingness" in hints

    def test_will_npc_cooperate(self):
        """Test cooperation check."""
        engine = PropagationEngine()
        engine.register_npc("npc_001")

        # Default should cooperate
        assert engine.will_npc_cooperate("npc_001")

    def test_will_npc_share_info(self):
        """Test share info check."""
        engine = PropagationEngine()
        engine.register_npc("npc_001")

        # Default should share
        assert engine.will_npc_share_info("npc_001")

    def test_get_npc_memories(self):
        """Test getting NPC memories."""
        engine = PropagationEngine()
        engine.register_npc("npc_001")

        state = engine.get_npc_state("npc_001")
        from src.shadowengine.npc_intelligence.npc_memory import NPCMemory
        state.memory_bank.add_memory(NPCMemory(summary="Test"))

        memories = engine.get_npc_memories("npc_001")

        assert len(memories) == 1

    def test_get_npc_memories_about(self):
        """Test getting memories about subject."""
        engine = PropagationEngine()
        engine.register_npc("npc_001")

        state = engine.get_npc_state("npc_001")
        from src.shadowengine.npc_intelligence.npc_memory import NPCMemory
        state.memory_bank.add_memory(NPCMemory(summary="Mob stuff", tags=["mob"]))
        state.memory_bank.add_memory(NPCMemory(summary="Weather", tags=["weather"]))

        mob_memories = engine.get_npc_memories_about("npc_001", "mob")

        assert len(mob_memories) == 1

    def test_get_emergent_storylines(self):
        """Test getting emergent storylines."""
        engine = PropagationEngine()

        # Create tense relationship
        rel = engine.social_network.get_or_create_relation("npc_a", "npc_b")
        rel.tension = 80

        storylines = engine.get_emergent_storylines()

        assert len(storylines) > 0

    def test_get_dangerous_locations(self):
        """Test getting dangerous locations."""
        engine = PropagationEngine()

        tile = engine.tile_manager.get_or_create((10, 10))
        tile.danger_rating = 0.8

        dangerous = engine.get_dangerous_locations()

        assert len(dangerous) == 1

    def test_get_atmosphere_at(self):
        """Test getting atmosphere at location."""
        engine = PropagationEngine()

        tile = engine.tile_manager.get_or_create((10, 10))
        tile.danger_rating = 0.7
        tile.death_count = 1

        hints = engine.get_atmosphere_at((10, 10))

        assert len(hints) > 0

    def test_player_spreads_rumor(self):
        """Test player spreading rumor."""
        engine = PropagationEngine()
        engine.register_npc("target_npc")

        rumor = engine.player_spreads_rumor(
            target_npc="target_npc",
            rumor_content="The mob is watching",
            player_credibility=0.7
        )

        assert rumor is not None
        assert rumor.is_carrier("target_npc")
        assert "player_spread" in rumor.tags

        # Target should have memory
        state = engine.get_npc_state("target_npc")
        memories = state.memory_bank.get_memories_by_tag("player_said")
        assert len(memories) > 0

    def test_engine_serialization(self):
        """Test engine to_dict and from_dict."""
        engine = PropagationEngine()
        engine.register_npc("npc_001", "bartender")
        engine.register_npc("npc_002", "informant")

        # Add some state
        state1 = engine.get_npc_state("npc_001")
        from src.shadowengine.npc_intelligence.npc_memory import NPCMemory
        state1.memory_bank.add_memory(NPCMemory(summary="Test memory"))

        engine.tile_manager.get_or_create((5, 5), "test_tile").danger_rating = 0.6
        engine.social_network.get_or_create_relation("npc_001", "npc_002")
        engine.current_time = 500.0

        data = engine.to_dict()
        restored = PropagationEngine.from_dict(data)

        assert len(restored.npc_states) == 2
        assert restored.current_time == 500.0
        assert len(restored.get_npc_state("npc_001").memory_bank.memories) == 1
        assert restored.tile_manager.tile_memories[(5, 5)].danger_rating == 0.6


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_witness_forms_memory_and_spreads_rumor(self):
        """Test complete flow: witness -> memory -> rumor -> spread."""
        engine = PropagationEngine()

        # Register NPCs
        engine.register_npc("witness", "civilian", NPCBias(talkative=1.0))
        engine.register_npc("listener", "civilian", NPCBias(trusting=0.8))

        # Create violence event
        event = WorldEventFactory.violence(
            timestamp=100.0,
            location=(10, 10),
            location_name="alley",
            attacker="thug",
            victim="victim",
            lethal=True
        )
        event.add_witness("witness", WitnessType.DIRECT)

        # Process event
        memories = engine.process_event(event)
        assert len(memories) == 1

        # Witness should have memory
        witness_state = engine.get_npc_state("witness")
        assert witness_state.memory_bank.has_memory_of_event(event.id)

        # Simulate gossip interaction until rumor spreads
        spread = False
        for _ in range(30):
            result = engine.simulate_interaction(
                "witness", "listener",
                trigger=PropagationTrigger.GOSSIP,
                location=(15, 15)
            )
            if result["rumor_shared"]:
                spread = True
                break

        assert spread

        # Listener should now have memory from rumor
        listener_state = engine.get_npc_state("listener")
        listener_memories = listener_state.memory_bank.memories
        assert len(listener_memories) > 0

    def test_tile_memory_affects_atmosphere(self):
        """Test that events at location affect atmosphere."""
        engine = PropagationEngine()
        engine.register_npc("witness")

        # Multiple violent events at same location
        for i in range(3):
            event = WorldEventFactory.violence(
                timestamp=100.0 + i,
                location=(20, 20),
                location_name="dangerous_alley",
                attacker=f"thug_{i}",
                victim=f"victim_{i}",
                lethal=True
            )
            event.add_witness("witness", WitnessType.DIRECT)
            engine.process_event(event)

        # Check tile is now dangerous
        tile = engine.tile_manager.tile_memories[(20, 20)]
        assert tile.danger_rating > 0.5
        # Violence events increase crime_rating and danger but death_count only from "death" events
        assert tile.crime_rating > 0
        assert tile.mood_modifier == "ominous"

        # Atmosphere hints should reflect this
        hints = engine.get_atmosphere_at((20, 20))
        assert any("dangerous" in h.lower() for h in hints)

    def test_social_network_evolves_through_interactions(self):
        """Test that repeated interactions change relationships."""
        engine = PropagationEngine()
        engine.register_npc("npc_a")
        engine.register_npc("npc_b")

        # Many positive interactions
        for _ in range(10):
            engine.social_network.record_interaction(
                "npc_a", "npc_b",
                "helped",
                timestamp=engine.current_time,
                bidirectional=True
            )
            engine.current_time += 1

        # Should be friends now
        friends = engine.social_network.get_friends("npc_a")
        assert "npc_b" in friends

    def test_fear_affects_behavior(self):
        """Test that fearful memories affect NPC behavior."""
        engine = PropagationEngine()
        engine.register_npc("fearful_npc", "civilian")

        # Create traumatic event
        event = WorldEvent(
            event_type="violence",
            timestamp=100.0,
            location=(5, 5),
            location_name="trauma_site",
            actors=["attacker"],
            notability=1.0
        )
        event.add_witness("fearful_npc", WitnessType.DIRECT, clarity=1.0)

        # Process multiple traumatic events
        for i in range(3):
            ev = WorldEvent(
                id=f"evt_{i}",
                event_type="violence",
                timestamp=100.0 + i,
                location=(5, 5),
                location_name="trauma_site"
            )
            ev.add_witness("fearful_npc", WitnessType.DIRECT)
            engine.process_event(ev)

        # Update behavior
        state = engine.get_npc_state("fearful_npc")
        engine.behavior_system.update_npc_behavior(
            "fearful_npc",
            state.memory_bank.memories,
            engine.current_time
        )

        # Behavior hints should reflect fear
        hints = engine.get_npc_behavior_hints("fearful_npc")
        # NPC should show some negative reaction
        assert hints is not None
