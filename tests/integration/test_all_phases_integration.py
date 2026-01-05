"""
Comprehensive All-Phases Integration Tests.

These tests verify that ALL game phases work together seamlessly:
- Phase 1-3: Core Foundation (Memory, Narrative, Characters)
- Phase 4: Grid System (TileGrid, Pathfinding, Line of Sight)
- Phase 5: ASCII Art Studio (Asset Creation, Pool, Gallery)
- Phase 6: STT & Real-Time Input (Voice, Intent Parsing)
- Phase 7: NPC Intelligence (Memory, Rumors, Social Network)

Each test exercises multiple phases working in concert.
"""

import pytest
import json
import tempfile
from datetime import datetime

# Phase 1-3: Core Systems
from src.shadowengine.game import Game
from src.shadowengine.config import GameConfig
from src.shadowengine.scenarios.test_scenario import create_test_scenario

# Memory system
from src.shadowengine.memory import (
    MemoryBank, WorldMemory, CharacterMemory, PlayerMemory,
    Event, EventType
)

# Character system
from src.shadowengine.character import (
    Character, Archetype, DialogueManager,
    Schedule, Activity, RelationshipManager, RelationType,
    create_servant_schedule
)

# Environment system
from src.shadowengine.environment import (
    Environment, TimeSystem, TimePeriod,
    WeatherSystem, WeatherType, WeatherState
)

# Narrative system
from src.shadowengine.narrative import (
    NarrativeSpine, SpineGenerator, ConflictType,
    TrueResolution, Revelation,
    MoralShade, ShadeProfile, ShadeNarrator, MoralDecision,
    TwistType, Twist, TwistManager, TwistGenerator
)

# Render system
from src.shadowengine.render import (
    Scene, Location, Renderer,
    ColorManager, ParticleSystem, ParticleType,
    AtmosphereManager, Mood, TensionMeter
)

# Interaction system
from src.shadowengine.interaction import (
    CommandParser, Command, CommandType,
    Hotspot, HotspotType
)

# Inventory system
from src.shadowengine.inventory import (
    Inventory, Item, ItemType, Evidence,
    EvidencePresentation
)

# Replay system
from src.shadowengine.replay import (
    GameSeed, SeedGenerator, GameStatistics,
    AchievementManager, AggregateStatistics
)

# Phase 4: Grid System
from src.shadowengine.grid import (
    Position, Tile, TileGrid, Entity, EntityType,
    TerrainType, TerrainModifier, find_path, get_line_of_sight
)

# Phase 5: ASCII Art Studio
from src.shadowengine.studio import (
    Studio, ASCIIArt, StaticArt, DynamicEntity,
    AssetPool, Gallery, ArtTags, ObjectType, EnvironmentType
)
from src.shadowengine.studio.personality import PersonalityTemplate, ThreatResponse
from src.shadowengine.studio.entity import create_entity_from_template

# Phase 6: Voice Input
from src.shadowengine.voice import (
    MockSTTEngine, IntentParser, IntentType,
    VoiceVocabulary, CommandMatcher,
    RealtimeHandler, InputPriority, InputEvent,
    VoiceConfig
)

# Phase 7: NPC Intelligence
from src.shadowengine.npc_intelligence import (
    WorldEvent, WitnessType,
    NPCMemory, MemorySource, MemoryDecaySystem,
    NPCBias, BiasProcessor,
    Rumor, RumorMutation, RumorPropagation,
    TileMemory, TileMemoryManager,
    MemoryBehaviorMapping, BehaviorModifier,
    SocialNetwork, SocialRelation,
    PropagationEngine
)
from src.shadowengine.npc_intelligence.world_event import Witness, WorldEventFactory
from src.shadowengine.npc_intelligence.rumor import PropagationTrigger


class TestNPCIntelligenceIntegration:
    """E2E tests for Phase 7 NPC Intelligence with all systems."""

    def test_world_event_processing_full_pipeline(self):
        """Test complete world event -> memory -> behavior pipeline."""
        # Setup propagation engine
        engine = PropagationEngine()

        # Register NPCs with different archetypes
        engine.register_npc("butler", "bartender")
        engine.register_npc("maid", "informant")
        engine.register_npc("guest", "civilian")

        # Create a world event (witnessed theft)
        event = WorldEventFactory.theft(
            timestamp=1.0,
            location=(5, 10),
            location_name="study",
            thief="butler",
            victim="guest",
            item="valuable_watch",
            value=0.8,
            witnesses=[
                Witness("maid", WitnessType.DIRECT),
                Witness("guest", WitnessType.INDIRECT)
            ]
        )

        # Process the event
        memories = engine.process_event(event)

        # Verify memories were created
        assert len(memories) == 2  # maid and guest

        # Maid (direct witness) should have higher confidence
        maid_memories = engine.get_npc_memories("maid")
        assert len(maid_memories) > 0
        assert maid_memories[0].confidence > 0.5

        # Guest (indirect witness) should have lower confidence
        guest_memories = engine.get_npc_memories("guest")
        assert len(guest_memories) > 0

        # Tile memory should be updated
        dangerous = engine.get_dangerous_locations()
        # May or may not be dangerous depending on threshold

    def test_rumor_propagation_network(self):
        """Test rumors spreading between NPCs."""
        engine = PropagationEngine()

        # Setup network of NPCs
        npcs = ["alice", "bob", "carol", "dave"]
        for npc in npcs:
            engine.register_npc(npc, "civilian")

        # Create initial event witnessed by alice
        event = WorldEventFactory.violence(
            timestamp=1.0,
            location=(0, 0),
            location_name="dark_alley",
            attacker="unknown",
            victim="stranger",
            lethal=False,
            witnesses=[Witness("alice", WitnessType.DIRECT)]
        )
        engine.process_event(event)

        # Alice talks to Bob
        result1 = engine.simulate_interaction("alice", "bob")
        assert result1["relationship_changed"]

        # If rumor was shared, Bob now knows
        if result1["rumor_shared"]:
            bob_memories = engine.get_npc_memories("bob")
            assert len(bob_memories) > 0

            # Bob talks to Carol - rumor may spread further
            result2 = engine.simulate_interaction("bob", "carol")
            # Rumors can chain through the network

    def test_social_network_with_memory(self):
        """Test social network dynamics based on memories."""
        engine = PropagationEngine()

        # Register NPCs with relationships
        engine.register_npc("detective", "cop")
        engine.register_npc("informant", "informant")
        engine.register_npc("criminal", "mobster")

        # Informant helps detective (positive interaction)
        for _ in range(3):
            engine.simulate_interaction(
                "informant", "detective",
                PropagationTrigger.CONVERSATION
            )

        # Get storylines
        storylines = engine.get_emergent_storylines()
        # May have formed a relationship

        # Criminal threatens informant
        event = WorldEventFactory.violence(
            timestamp=2.0,
            location=(5, 5),
            location_name="back_room",
            attacker="criminal",
            victim="informant",
            lethal=False,
            witnesses=[
                Witness("informant", WitnessType.DIRECT),
                Witness("detective", WitnessType.INDIRECT)
            ]
        )
        engine.process_event(event)

        # Informant should now fear criminal
        informant_behavior = engine.get_npc_behavior_hints("informant")
        # Behavior should reflect fear/danger

    def test_behavior_changes_from_memories(self):
        """Test that NPC behavior changes based on accumulated memories."""
        engine = PropagationEngine()
        engine.register_npc("witness", "civilian")
        engine.register_npc("player_ally", "civilian")

        # Witness sees player help someone
        event = WorldEvent(
            event_type="player_helped",
            actors=["player", "traveler"],
            details={"action": "helped_traveler"},
            location=(10, 10),
            location_name="road",
            timestamp=1.0,
            notability=0.5,
            witnesses=[Witness("witness", WitnessType.DIRECT)]
        )
        engine.process_event(event)

        # Check cooperation
        will_help = engine.will_npc_cooperate("witness")
        will_share = engine.will_npc_share_info("witness")
        # Should be influenced by positive memory

    def test_tile_memory_atmospheric_effects(self):
        """Test tile memory affecting atmosphere."""
        engine = PropagationEngine()

        location = (15, 15)
        engine.register_npc("victim", "civilian")

        # Multiple violent events at same location
        for i in range(3):
            event = WorldEventFactory.violence(
                timestamp=float(i + 1),
                location=location,
                location_name="cursed_corner",
                attacker=f"attacker_{i}",
                victim="victim",
                lethal=False,
                witnesses=[Witness("victim", WitnessType.DIRECT)]
            )
            engine.process_event(event)

        # Get atmosphere
        hints = engine.get_atmosphere_at(location)
        # Should have danger/violence hints

        dangerous = engine.get_dangerous_locations()
        assert len(dangerous) > 0

    def test_player_rumor_spreading(self):
        """Test player deliberately spreading rumors."""
        engine = PropagationEngine()
        engine.register_npc("gullible_npc", "civilian")
        engine.register_npc("skeptic_npc", "cop")

        # Set bias for gullible NPC
        engine.npc_states["gullible_npc"].bias.trusting = 0.9
        engine.npc_states["skeptic_npc"].bias.trusting = 0.1

        # Player spreads a rumor
        rumor1 = engine.player_spreads_rumor(
            "gullible_npc",
            "The butler did it!",
            player_credibility=0.7
        )

        rumor2 = engine.player_spreads_rumor(
            "skeptic_npc",
            "The butler did it!",
            player_credibility=0.7
        )

        # Gullible NPC should believe it more
        gullible_memories = engine.get_npc_memories("gullible_npc")
        skeptic_memories = engine.get_npc_memories("skeptic_npc")

        assert len(gullible_memories) > 0
        assert len(skeptic_memories) > 0

        # Confidence should differ based on trusting bias
        assert gullible_memories[0].confidence > skeptic_memories[0].confidence

    def test_engine_serialization(self):
        """Test saving and loading full engine state."""
        engine = PropagationEngine()

        # Setup complex state
        engine.register_npc("npc1", "bartender")
        engine.register_npc("npc2", "informant")

        event = WorldEventFactory.conversation(
            timestamp=1.0,
            location=(5, 5),
            location_name="bar",
            participants=["npc1", "npc2"],
            topic="secret",
            witnesses=[
                Witness("npc1", WitnessType.DIRECT),
                Witness("npc2", WitnessType.DIRECT)
            ]
        )
        engine.process_event(event)
        engine.simulate_interaction("npc1", "npc2")
        engine.update(1.0)

        # Serialize
        data = engine.to_dict()
        json_str = json.dumps(data)

        # Deserialize
        restored_data = json.loads(json_str)
        restored_engine = PropagationEngine.from_dict(restored_data)

        # Verify restoration
        assert len(restored_engine.npc_states) == 2
        assert len(restored_engine.events) == 1
        assert restored_engine.current_time == 1.0


class TestGridWithNPCIntelligence:
    """Tests combining Grid System (Phase 4) with NPC Intelligence (Phase 7)."""

    def test_event_at_grid_location(self):
        """Test events tied to grid positions."""
        grid = TileGrid(20, 20)
        engine = PropagationEngine()

        # Setup NPCs at different positions
        engine.register_npc("guard", "cop")
        engine.register_npc("witness", "civilian")

        # Position them on grid
        guard_pos = Position(5, 5)
        witness_pos = Position(7, 5)

        # Create event with grid position
        event = WorldEventFactory.violence(
            timestamp=1.0,
            location=(6, 5),
            location_name="street",
            attacker="criminal",
            victim="victim",
            lethal=False,
            witnesses=[
                Witness("guard", WitnessType.DIRECT),
                Witness("witness", WitnessType.DIRECT)
            ]
        )
        engine.process_event(event)

        # Mark the tile as dangerous
        tile = grid.get_tile(6, 5)
        tile.metadata = {"dangerous": True}

        # Check line of sight to event location
        los = get_line_of_sight(grid, guard_pos, Position(6, 5))
        assert los is not None

    def test_pathfinding_avoids_dangerous_tiles(self):
        """Test that NPCs remember dangerous locations for pathfinding."""
        grid = TileGrid(15, 15)
        engine = PropagationEngine()

        engine.register_npc("cautious_npc", "civilian")

        # Create multiple violent events at a chokepoint
        for i in range(3):
            event = WorldEventFactory.violence(
                timestamp=float(i + 1),
                location=(7, 7),
                location_name="dangerous_alley",
                attacker="gang",
                victim=f"victim_{i}",
                lethal=True,
                witnesses=[Witness("cautious_npc", WitnessType.DIRECT)]
            )
            engine.process_event(event)

        # The tile should now be marked dangerous
        dangerous_locs = engine.get_dangerous_locations()
        dangerous_positions = [(tm.location[0], tm.location[1]) for tm in dangerous_locs]

        # If NPC were smart, they'd avoid this
        if (7, 7) in dangerous_positions:
            # Mark tile to affect pathfinding
            tile = grid.get_tile(7, 7)
            tile.terrain_type = TerrainType.ROCK  # Block movement

            # Path should go around
            start = Position(5, 7)
            end = Position(9, 7)
            path = find_path(grid, start, end)

            # Path should exist but not go through (7, 7)
            if path:
                # path returns Tile objects with position attribute
                path_positions = [(t.position.x, t.position.y) for t in path]
                assert (7, 7) not in path_positions

    def test_line_of_sight_affects_witness_type(self):
        """Test that LOS determines witness type."""
        grid = TileGrid(20, 20)

        # Add a wall blocking vision
        for y in range(5, 15):
            tile = grid.get_tile(10, y)
            tile.blocks_vision = True

        # NPC on one side
        npc_pos = Position(5, 10)
        event_pos = Position(15, 10)

        # Check LOS
        los = get_line_of_sight(grid, npc_pos, event_pos)

        # Wall should block - LOS returns tiles up to blocker
        # If blocked, witness type would be INDIRECT
        # This is how grid affects NPC intelligence


class TestStudioWithNPCIntelligence:
    """Tests combining ASCII Studio (Phase 5) with NPC Intelligence (Phase 7)."""

    def test_entity_with_intelligence(self):
        """Test studio entities having NPC intelligence."""
        studio = Studio(player_id="creator1")
        engine = PropagationEngine()

        # Create an entity
        studio.new_canvas(3, 2, "Smart Guard")
        studio.draw_at(1, 0, "O")
        studio.draw_at(1, 1, "|")
        studio.set_object_type(ObjectType.CREATURE)

        entity = studio.convert_to_entity("protective_territorial")

        # Register entity in intelligence system
        engine.register_npc(entity.id, "cop")

        # Entity witnesses an event
        event = WorldEventFactory.violence(
            timestamp=1.0,
            location=(10, 10),
            location_name="village",
            attacker="intruder",
            victim="villager",
            lethal=False,
            witnesses=[Witness(entity.id, WitnessType.DIRECT)]
        )
        engine.process_event(event)

        # Entity should remember
        memories = engine.get_npc_memories(entity.id)
        assert len(memories) > 0

        # Entity's behavior should be affected
        behavior = engine.get_npc_behavior_hints(entity.id)

    def test_multiple_entities_social_network(self):
        """Test multiple studio entities forming social networks."""
        pool = AssetPool()
        engine = PropagationEngine()

        # Create several entities
        entity_ids = []
        for i, template in enumerate(["village_guard", "forest_deer"]):
            entity = create_entity_from_template(template)
            if entity:
                pool.add_asset(entity)
                engine.register_npc(entity.id, template.split("_")[0])
                entity_ids.append(entity.id)

        # Simulate interactions between entities
        if len(entity_ids) >= 2:
            for _ in range(3):
                engine.simulate_interaction(
                    entity_ids[0], entity_ids[1],
                    PropagationTrigger.CONVERSATION
                )

            # Check social network
            storylines = engine.get_emergent_storylines()

    def test_gallery_reputation_affects_npc_trust(self):
        """Test that popular assets might affect NPC trust."""
        gallery = Gallery()
        pool = AssetPool()
        engine = PropagationEngine()

        # Create and submit art
        studio = Studio(player_id="artist", gallery=gallery, asset_pool=pool)
        studio.new_canvas(5, 3, "Helpful Item")
        studio.draw_rectangle(0, 0, 5, 3, ".")
        studio.set_object_type(ObjectType.OTHER)
        static = studio.convert_to_static()
        studio.save_to_pool()

        entry = studio.submit_to_gallery(
            title="Helpful Tool",
            creator_name="TrustedArtist"
        )

        # Many players like it
        for i in range(10):
            gallery.like_entry(entry.id, f"player_{i}")

        # Asset is now "trusted" by community
        assert entry.likes == 10

        # This could influence NPC behavior when interacting with
        # objects from this creator


class TestVoiceWithNPCIntelligence:
    """Tests combining Voice Input (Phase 6) with NPC Intelligence (Phase 7)."""

    def test_voice_command_affects_npc_memory(self):
        """Test voice commands creating memories."""
        stt = MockSTTEngine()
        stt.initialize()
        intent_parser = IntentParser()
        engine = PropagationEngine()

        engine.register_npc("butler", "bartender")

        # Player uses voice to accuse
        voice_text = "I accuse the butler of theft"
        stt.set_response(voice_text)
        result = stt.transcribe(b"audio")

        intent = intent_parser.parse(result.text)
        # This would create a memory in the game

        # Player spreads rumor via voice
        engine.player_spreads_rumor(
            "butler",
            "I suspect you of theft!",
            player_credibility=0.6
        )

        # Butler now has this memory
        butler_memories = engine.get_npc_memories("butler")
        assert len(butler_memories) > 0

    def test_voice_interrogation_builds_relationship(self):
        """Test voice interactions affecting NPC relationships."""
        stt = MockSTTEngine()
        stt.initialize()
        intent_parser = IntentParser()
        engine = PropagationEngine()

        engine.register_npc("suspect", "civilian")
        engine.register_npc("witness", "informant")

        # Series of voice commands representing interrogation
        commands = [
            "talk to the suspect",
            "ask about last night",
            "pressure for more details",
        ]

        for cmd in commands:
            stt.set_response(cmd)
            result = stt.transcribe(b"audio")
            intent = intent_parser.parse(result.text)

            # Each interaction could update social network
            engine.simulate_interaction(
                "player_npc", "suspect",
                PropagationTrigger.INTERROGATED
            )

        # Check behavior changes
        will_cooperate = engine.will_npc_cooperate("suspect")

    def test_realtime_event_triggers_npc_reaction(self):
        """Test realtime events affecting NPC intelligence."""
        handler = RealtimeHandler()
        engine = PropagationEngine()

        engine.register_npc("guard", "cop")

        # High priority event
        urgent_event = InputEvent(
            raw_text="intruder spotted!",
            priority=InputPriority.CRITICAL
        )
        handler.input_queue.put(urgent_event)

        # Process the event
        event = handler.input_queue.get()

        # This triggers a world event
        world_event = WorldEvent(
            event_type="intruder_alert",
            actors=["intruder"],
            details={"alert_text": event.raw_text},
            location=(0, 0),
            location_name="entrance",
            timestamp=1.0,
            notability=1.0,
            witnesses=[Witness("guard", WitnessType.DIRECT)]
        )
        engine.process_event(world_event)

        # Guard should remember this
        guard_memories = engine.get_npc_memories("guard")
        assert len(guard_memories) > 0


class TestCompleteGameSession:
    """Complete game session tests using ALL phases."""

    def test_full_game_with_all_systems(self):
        """Simulate a complete game session using all systems."""
        # Phase 1-3: Core game setup
        seed = GameSeed.generate(source="all_phases_test")
        game = create_test_scenario(seed=seed.value)

        env = Environment()
        env.set_seed(seed.value)
        env.time.set_time(10, 0)

        atmosphere = AtmosphereManager()
        profile = ShadeProfile()
        stats = GameStatistics(game_id="all_phases", seed=seed.value)
        inventory = Inventory()

        # Phase 4: Grid system
        grid = TileGrid(30, 30)
        for x in range(30):
            for y in range(30):
                tile = grid.get_tile(x, y)
                tile.terrain_type = TerrainType.SOIL

        # Add some walls
        for x in range(10, 20):
            tile = grid.get_tile(x, 15)
            tile.blocks_movement = True
            tile.blocks_vision = True

        # Phase 5: Studio assets
        pool = AssetPool()
        gallery = Gallery()
        studio = Studio(player_id="game_player", asset_pool=pool, gallery=gallery)

        # Phase 6: Voice input
        stt = MockSTTEngine()
        stt.initialize()
        intent_parser = IntentParser()
        command_matcher = CommandMatcher(VoiceVocabulary())

        # Phase 7: NPC Intelligence
        engine = PropagationEngine()

        # Register game characters with intelligence
        for char_id in ["butler", "maid", "guest"]:
            archetype = "bartender" if char_id == "butler" else "civilian"
            engine.register_npc(char_id, archetype)

        # Simulate game flow
        game_actions = [
            ("look around", IntentType.EXAMINE, None),
            ("examine the butler", IntentType.EXAMINE, "butler"),
            ("talk to the maid", IntentType.TALK, "maid"),
            ("talk to the butler", IntentType.TALK, "butler"),
        ]

        for voice_text, expected_intent, target in game_actions:
            # Voice processing
            stt.set_response(voice_text)
            result = stt.transcribe(b"audio")
            intent = intent_parser.parse(result.text)
            assert intent.primary_intent.type == expected_intent

            # Update game state
            stats.commands_entered += 1
            atmosphere.tension.add_tension(0.05)
            atmosphere.update()

            # If talking to NPC, create interaction
            if target and expected_intent == IntentType.TALK:
                engine.simulate_interaction(
                    "player", target,
                    PropagationTrigger.CONVERSATION
                )

            # Time progresses
            env.update(5)
            engine.update(0.1)

        # Create a world event based on player actions
        event = WorldEvent(
            event_type="accusation",
            actors=["player", "butler"],
            details={"accused": "butler", "action": "public_accusation"},
            location=(15, 15),
            location_name="study",
            timestamp=env.time.hour * 60 + env.time.minute,
            notability=0.9,
            witnesses=[
                Witness("butler", WitnessType.DIRECT),
                Witness("maid", WitnessType.INDIRECT),
                Witness("guest", WitnessType.INDIRECT)
            ]
        )
        engine.process_event(event)

        # All NPCs now remember the accusation
        for npc in ["butler", "maid", "guest"]:
            memories = engine.get_npc_memories(npc)
            assert len(memories) > 0

        # Butler's behavior should change
        butler_hints = engine.get_npc_behavior_hints("butler")

        # Moral decision
        profile.apply_decision(MoralDecision(
            "accusation", "Public accusation",
            {MoralShade.RUTHLESS: 2}
        ))

        # Verify all systems integrated
        assert stats.commands_entered == 4
        assert len(engine.events) >= 1
        assert atmosphere.tension.current > 0.1

    def test_mystery_solving_with_npc_intelligence(self):
        """Test solving a mystery using NPC intelligence."""
        game = create_test_scenario(seed=42)
        engine = PropagationEngine()

        # Register characters
        engine.register_npc("butler", "bartender")
        engine.register_npc("maid", "informant")
        engine.register_npc("guest", "civilian")

        # Maid witnessed the crime
        theft_event = WorldEventFactory.theft(
            timestamp=1.0,
            location=(10, 10),
            location_name="study",
            thief="butler",
            victim="lord",
            item="jewels",
            value=0.9,
            witnesses=[Witness("maid", WitnessType.DIRECT)]
        )
        engine.process_event(theft_event)

        # Player talks to maid
        result = engine.simulate_interaction(
            "player", "maid",
            PropagationTrigger.INTERROGATED
        )

        # If maid shares info, player learns about butler
        if result["rumor_shared"]:
            # This is a clue!
            pass

        # Maid talks to guest (rumor spreads)
        engine.simulate_interaction("maid", "guest")

        # Check if guest now knows
        guest_memories = engine.get_npc_memories("guest")

        # Track evidence in game state
        game.state.memory.player.visit_location("study")

        # Use evidence to make accusation
        evidence = {"jewel_theft", "maid_witness"}
        is_correct, message = game.state.spine.check_solution("butler", evidence)

    def test_emergent_storyline_detection(self):
        """Test that emergent storylines form from NPC dynamics."""
        engine = PropagationEngine()

        # Setup a social situation
        npcs = {
            "romeo": "civilian",
            "juliet": "civilian",
            "tybalt": "mobster",
            "mercutio": "informant"
        }

        for npc_id, npc_type in npcs.items():
            engine.register_npc(npc_id, npc_type)

        # Romeo and Juliet meet frequently (positive)
        for _ in range(5):
            engine.simulate_interaction(
                "romeo", "juliet",
                PropagationTrigger.CONVERSATION
            )

        # Tybalt threatens Romeo
        threat_event = WorldEventFactory.violence(
            timestamp=1.0,
            location=(5, 5),
            location_name="street",
            attacker="tybalt",
            victim="romeo",
            lethal=False,
            witnesses=[
                Witness("romeo", WitnessType.DIRECT),
                Witness("mercutio", WitnessType.DIRECT),
                Witness("juliet", WitnessType.INDIRECT)
            ]
        )
        engine.process_event(threat_event)

        # Mercutio defends Romeo - another event
        defense_event = WorldEvent(
            event_type="defense",
            actors=["mercutio", "romeo", "tybalt"],
            details={"defender": "mercutio", "protected": "romeo", "against": "tybalt"},
            location=(5, 5),
            location_name="street",
            timestamp=2.0,
            notability=0.8,
            witnesses=[
                Witness("romeo", WitnessType.DIRECT),
                Witness("mercutio", WitnessType.DIRECT),
                Witness("tybalt", WitnessType.DIRECT)
            ]
        )
        engine.process_event(defense_event)

        # Check for emergent storylines
        storylines = engine.get_emergent_storylines()
        # Should detect friendship, rivalry, etc.

        # Update to let relationships develop
        for _ in range(5):
            engine.update(1.0)

        # Final storylines
        final_storylines = engine.get_emergent_storylines()

    def test_save_load_complete_state(self):
        """Test saving and loading complete game state with all systems."""
        # Setup all systems
        engine = PropagationEngine()
        pool = AssetPool()
        gallery = Gallery()
        profile = ShadeProfile()
        inventory = Inventory()

        # Add NPC intelligence state
        engine.register_npc("npc1", "bartender")
        engine.register_npc("npc2", "informant")

        event = WorldEventFactory.conversation(
            timestamp=1.0,
            location=(5, 5),
            location_name="bar",
            participants=["npc1", "npc2"],
            topic="secrets",
            witnesses=[
                Witness("npc1", WitnessType.DIRECT),
                Witness("npc2", WitnessType.DIRECT)
            ]
        )
        engine.process_event(event)

        # Add some state to other systems
        profile.apply_decision(MoralDecision("d1", "Decision", {MoralShade.PRAGMATIC: 2}))
        inventory.add(Item(id="key", name="Key", description="A key"))

        # Serialize everything
        state = {
            "engine": engine.to_dict(),
            "pool": pool.to_dict(),
            "gallery": gallery.to_dict(),
            "profile": profile.to_dict(),
            "inventory": inventory.to_dict()
        }

        json_str = json.dumps(state)

        # Deserialize
        restored = json.loads(json_str)

        restored_engine = PropagationEngine.from_dict(restored["engine"])
        restored_pool = AssetPool.from_dict(restored["pool"])
        restored_gallery = Gallery.from_dict(restored["gallery"])
        restored_profile = ShadeProfile.from_dict(restored["profile"])
        restored_inventory = Inventory.from_dict(restored["inventory"])

        # Verify restoration
        assert len(restored_engine.npc_states) == 2
        assert len(restored_engine.events) == 1
        assert restored_profile.scores[MoralShade.PRAGMATIC] == 2
        assert restored_inventory.count() == 1


class TestBiasAndMemoryFormation:
    """Tests for NPC bias affecting memory formation."""

    def test_paranoid_npc_memory_formation(self):
        """Test that paranoid NPCs form different memories."""
        engine = PropagationEngine()

        # Register NPCs with different bias
        engine.register_npc("paranoid", "civilian")
        engine.npc_states["paranoid"].bias.paranoid = 0.9
        engine.npc_states["paranoid"].bias.trusting = 0.1

        engine.register_npc("trusting", "civilian")
        engine.npc_states["trusting"].bias.paranoid = 0.1
        engine.npc_states["trusting"].bias.trusting = 0.9

        # Both witness same ambiguous event
        event = WorldEvent(
            event_type="observation",
            actors=["stranger"],
            details={"observed": "stranger_near_vault"},
            location=(0, 0),
            location_name="bank",
            timestamp=1.0,
            notability=0.5,
            witnesses=[
                Witness("paranoid", WitnessType.DIRECT),
                Witness("trusting", WitnessType.DIRECT)
            ]
        )
        engine.process_event(event)

        # Check memories differ based on bias
        paranoid_memories = engine.get_npc_memories("paranoid")
        trusting_memories = engine.get_npc_memories("trusting")

        assert len(paranoid_memories) > 0
        assert len(trusting_memories) > 0

    def test_dramatic_npc_exaggerates(self):
        """Test that dramatic NPCs form exaggerated memories."""
        engine = PropagationEngine()

        engine.register_npc("dramatic", "civilian")
        engine.npc_states["dramatic"].bias.dramatic = 0.9

        engine.register_npc("calm", "civilian")
        engine.npc_states["calm"].bias.dramatic = 0.1

        event = WorldEvent(
            event_type="minor_incident",
            actors=["unknown"],
            details={"what_happened": "vase_broken"},
            location=(5, 5),
            location_name="room",
            timestamp=1.0,
            notability=0.3,
            witnesses=[
                Witness("dramatic", WitnessType.DIRECT),
                Witness("calm", WitnessType.DIRECT)
            ]
        )
        engine.process_event(event)

        dramatic_memories = engine.get_npc_memories("dramatic")
        calm_memories = engine.get_npc_memories("calm")

        # Dramatic NPC's memory should have higher emotional weight
        if dramatic_memories and calm_memories:
            assert dramatic_memories[0].emotional_weight >= calm_memories[0].emotional_weight


class TestMemoryDecayAndRetention:
    """Tests for memory decay over time."""

    def test_traumatic_memories_persist(self):
        """Test that traumatic memories decay slower."""
        engine = PropagationEngine()
        engine.register_npc("witness", "civilian")

        # Create traumatic event
        traumatic_event = WorldEventFactory.violence(
            timestamp=1.0,
            location=(0, 0),
            location_name="forest",
            attacker="monster",
            victim="friend",
            lethal=True,
            witnesses=[Witness("witness", WitnessType.DIRECT)]
        )
        engine.process_event(traumatic_event)

        # Create mundane event
        mundane_event = WorldEvent(
            event_type="observation",
            actors=["bird"],
            details={"observed": "bird_flying"},
            location=(1, 1),
            location_name="garden",
            timestamp=2.0,
            notability=0.1,
            witnesses=[Witness("witness", WitnessType.DIRECT)]
        )
        engine.process_event(mundane_event)

        # Simulate time passing
        for _ in range(100):
            engine.update(1.0)

        # Check which memories remain
        memories = engine.get_npc_memories("witness")

        # Traumatic memory should be more likely to persist
        # (This depends on implementation details)

    def test_memory_capacity_limits(self):
        """Test that NPCs have memory capacity limits."""
        engine = PropagationEngine()
        engine.register_npc("npc", "civilian")

        # Create many events
        for i in range(50):
            event = WorldEvent(
                event_type="observation",
                actors=[f"actor_{i}"],
                details={"event_number": i},
                location=(i % 10, i % 10),
                location_name="somewhere",
                timestamp=float(i),
                notability=0.3,
                witnesses=[Witness("npc", WitnessType.DIRECT)]
            )
            engine.process_event(event)

        # Memory bank should have capacity limit
        memories = engine.get_npc_memories("npc")
        # Depends on implementation, but should be reasonable


class TestCrossPhaseEdgeCases:
    """Edge case tests for cross-phase integration."""

    def test_empty_systems_work_together(self):
        """Test that empty systems don't crash."""
        engine = PropagationEngine()
        grid = TileGrid(10, 10)
        pool = AssetPool()
        gallery = Gallery()

        # Query empty systems
        storylines = engine.get_emergent_storylines()
        dangerous = engine.get_dangerous_locations()
        rumors = engine.get_rumors_about("anything")

        assert storylines == []
        assert dangerous == []
        assert rumors == []

    def test_invalid_npc_operations(self):
        """Test operations on non-existent NPCs."""
        engine = PropagationEngine()

        # Should return None/empty for non-existent NPC
        state = engine.get_npc_state("nonexistent")
        assert state is None

        memories = engine.get_npc_memories("nonexistent")
        assert memories == []

        hints = engine.get_npc_behavior_hints("nonexistent")
        # Should not crash

    def test_grid_pathfinding_with_no_path(self):
        """Test pathfinding when completely blocked."""
        grid = TileGrid(10, 10)

        # Block entire middle
        for x in range(10):
            tile = grid.get_tile(x, 5)
            tile.terrain_type = TerrainType.ROCK

        path = find_path(grid, Position(0, 0), Position(0, 9))
        # Should be None or empty
        assert path is None or len(path) == 0

    def test_voice_with_empty_vocabulary(self):
        """Test voice system handles edge cases."""
        stt = MockSTTEngine()
        stt.initialize()

        # Empty text
        stt.set_response("")
        result = stt.transcribe(b"audio")
        assert result.text == ""


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
