"""
End-to-end pipeline tests for the ASCII Art Studio system.

These tests verify complete workflows from art creation through
world integration, covering all major user journeys.
"""

import pytest
import time
import json
from datetime import datetime

from src.shadowengine.studio.art import ASCIIArt, ArtCategory
from src.shadowengine.studio.tags import (
    ArtTags, ObjectType, Size, Placement,
    InteractionType, EnvironmentType, TagQuery
)
from src.shadowengine.studio.static_art import StaticArt, RenderLayer, create_from_template
from src.shadowengine.studio.entity import (
    DynamicEntity, EntityState, EntityStats,
    create_entity_from_template
)
from src.shadowengine.studio.personality import (
    PersonalityTemplate, PERSONALITY_TEMPLATES, ThreatResponse, Attitude
)
from src.shadowengine.studio.animation import Animation, AnimationFrame, AnimationTrigger
from src.shadowengine.studio.asset_pool import AssetPool, AssetQuery
from src.shadowengine.studio.usage_stats import UsageStats, FeedbackType
from src.shadowengine.studio.gallery import Gallery, GalleryCategory, ContentRating
from src.shadowengine.studio.studio import Studio, StudioMode, Tool


class TestArtCreationPipeline:
    """E2E tests for the art creation workflow."""

    def test_create_static_art_from_scratch(self):
        """Complete pipeline: create static art in studio and save to pool."""
        # Step 1: Create studio instance
        studio = Studio(player_id="artist1")

        # Step 2: Create new canvas
        art = studio.new_canvas(10, 5, "My Tree")
        assert art is not None

        # Step 3: Draw the tree using various tools
        studio.set_tool(Tool.PENCIL)

        # Draw trunk
        studio.draw_line(5, 2, 5, 4, "|")

        # Draw foliage
        studio.draw_at(5, 0, "^")
        studio.draw_at(4, 1, "/")
        studio.draw_at(5, 1, "|")
        studio.draw_at(6, 1, "\\")

        # Step 4: Tag the art
        studio.set_object_type(ObjectType.TREE)
        studio.add_environment(EnvironmentType.FOREST)
        studio.add_environment(EnvironmentType.PLAINS)
        studio.add_interaction(InteractionType.CLIMBABLE)
        studio.add_custom_tag("deciduous")

        # Step 5: Convert to static art with properties
        static = studio.convert_to_static()
        assert isinstance(static, StaticArt)
        assert static.category == ArtCategory.STATIC

        # Step 6: Save to asset pool
        asset_id = studio.save_to_pool()
        assert asset_id is not None

        # Step 7: Verify asset is in pool and queryable
        query = AssetQuery(
            object_type=ObjectType.TREE,
            environment=EnvironmentType.FOREST
        )
        results = studio.asset_pool.query(query)
        assert len(results) == 1
        assert results[0].id == asset_id

    def test_create_entity_with_personality_and_animations(self):
        """Complete pipeline: create animated entity with AI."""
        studio = Studio(player_id="creator1")

        # Step 1: Create creature art
        studio.new_canvas(5, 3, "Forest Fox")

        # Draw the fox
        studio.draw_at(1, 0, "/")
        studio.draw_at(2, 0, "^")
        studio.draw_at(3, 0, "\\")
        studio.draw_at(1, 1, "(")
        studio.draw_at(2, 1, "o")
        studio.draw_at(3, 1, ")")
        studio.draw_at(0, 2, "=")
        studio.draw_at(4, 2, "~")

        # Step 2: Configure tags
        studio.set_object_type(ObjectType.CREATURE)
        studio.add_environment(EnvironmentType.FOREST)
        studio.add_interaction(InteractionType.TALKABLE)

        # Step 3: Convert to entity with personality
        entity = studio.convert_to_entity("curious_neutral")
        assert isinstance(entity, DynamicEntity)

        # Step 4: Customize entity stats
        entity.stats.health = 40
        entity.stats.max_health = 40
        entity.stats.speed = 1.8

        # Step 5: Add dialogue
        entity.add_dialogue("*sniffs curiously*")
        entity.add_dialogue("Yip!")

        # Step 6: Add loot table
        entity.loot_table = {"fox_fur": 0.6, "fox_tail": 0.2}

        # Step 7: Create idle animation
        idle_frames = [
            AnimationFrame.from_string("/^\\\n(o)\n= ~", duration=0.5),
            AnimationFrame.from_string("/^\\\n(O)\n= ~", duration=0.3),
            AnimationFrame.from_string("/^\\\n(o)\n= ~", duration=0.5),
        ]
        idle_anim = Animation(
            name="idle",
            frames=idle_frames,
            loop=True,
            trigger=AnimationTrigger.ON_IDLE
        )
        entity.add_animation(idle_anim)

        # Step 8: Add spawn conditions
        entity.spawn_conditions = {
            "environments": ["forest", "plains"],
            "time_of_day": ["day", "dusk"]
        }

        # Step 9: Save to pool
        studio._current_art = entity
        asset_id = studio.save_to_pool()

        # Step 10: Verify entity behavior
        retrieved = studio.asset_pool.get_asset(asset_id)
        assert retrieved.can_spawn_in("forest", "day")
        assert not retrieved.can_spawn_in("cave", "day")

        # Test personality response
        response = retrieved.respond_to_threat(0.3)
        assert response in (ThreatResponse.OBSERVE, ThreatResponse.FLEE)

    def test_edit_existing_art_workflow(self):
        """Pipeline for loading and editing existing art."""
        # Create initial art
        studio = Studio(player_id="editor1")
        studio.new_canvas(5, 3, "Simple Rock")
        studio.draw_rectangle(0, 0, 5, 3, "#")
        studio.set_object_type(ObjectType.ROCK)
        static = studio.convert_to_static()
        studio.save_to_pool()

        # Create new studio session
        studio2 = Studio(player_id="editor1", asset_pool=studio.asset_pool)

        # Load the existing art
        studio2.load_art(static)

        # Modify it with an operation that saves history
        original_char = studio2.current_art.get_tile(2, 1)
        studio2.draw_rectangle(2, 1, 1, 1, " ")  # Erase with rectangle (saves history)

        # Undo and redo
        assert studio2.undo() is True
        assert studio2.current_art.get_tile(2, 1) == original_char

        assert studio2.redo() is True
        assert studio2.current_art.get_tile(2, 1) == " "

        # Save as new version
        new_art = studio2.current_art.copy()
        new_art.version = 2
        studio2.asset_pool.add_asset(new_art)

        # Verify both versions exist
        assert studio2.asset_pool.count == 2


class TestGalleryPipeline:
    """E2E tests for gallery sharing workflow."""

    def test_submit_rate_download_workflow(self):
        """Complete pipeline: submit to gallery, rate, and download."""
        # Setup
        gallery = Gallery()
        pool = AssetPool()
        stats = UsageStats()

        # Step 1: Creator submits art
        creator_studio = Studio(
            player_id="creator1",
            asset_pool=pool,
            gallery=gallery,
            usage_stats=stats
        )
        creator_studio.new_canvas(8, 4, "Mountain Peak")
        creator_studio.draw_at(3, 0, "/")
        creator_studio.draw_at(4, 0, "\\")
        creator_studio.draw_at(2, 1, "/")
        creator_studio.draw_at(5, 1, "\\")
        creator_studio.draw_rectangle(1, 2, 6, 2, "_")

        creator_studio.set_object_type(ObjectType.TERRAIN)
        creator_studio.add_environment(EnvironmentType.MOUNTAIN)

        entry = creator_studio.submit_to_gallery(
            title="Majestic Mountain",
            description="A towering mountain peak with snow",
            tags={"mountain", "terrain", "nature", "snow"},
            creator_name="MountainMaker"
        )
        assert entry is not None
        entry_id = entry.id

        # Step 2: Multiple players view and rate
        for i in range(5):
            gallery.view_entry(entry_id)

        # Get the entry from gallery to verify counts
        gallery_entry = gallery.get_entry(entry_id)
        assert gallery_entry.views == 5

        # Step 3: Players like the entry
        gallery.like_entry(entry_id, "player1")
        gallery.like_entry(entry_id, "player2")
        gallery.like_entry(entry_id, "player3")
        assert gallery_entry.likes == 3

        # Step 4: A player downloads the art
        downloaded = gallery.download_entry(entry_id)
        assert downloaded is not None
        assert downloaded.id != gallery_entry.art.id  # Should be a copy
        assert gallery_entry.downloads == 1

        # Step 5: Downloaded art is used in another player's pool
        player_studio = Studio(player_id="player1", asset_pool=pool)
        pool.add_asset(downloaded)

        # Step 6: Verify it appears in searches
        results = gallery.search(query="mountain", sort_by="likes")
        assert len(results) >= 1
        assert results[0].title == "Majestic Mountain"

    def test_gallery_import_export_workflow(self):
        """Test exporting and importing gallery entries."""
        # Setup two separate galleries (simulating different servers/instances)
        gallery1 = Gallery()
        gallery2 = Gallery()

        # Create and submit art to gallery 1
        tags = ArtTags(
            object_type=ObjectType.STRUCTURE,
            environment_types={EnvironmentType.VILLAGE}
        )
        house = StaticArt.from_string(
            "Cottage",
            " /\\\n/  \\\n|[]|",
            tags,
            blocks_movement=True
        )

        entry = gallery1.submit(
            art=house,
            title="Cozy Cottage",
            creator_id="builder1",
            creator_name="Builder",
            description="A small village cottage",
            tags={"house", "village", "medieval"}
        )

        # Add some engagement
        gallery1.like_entry(entry.id, "player1")
        gallery1.like_entry(entry.id, "player2")

        # Export to JSON
        json_data = gallery1.export_entry(entry.id)
        assert json_data is not None

        # Import to gallery 2
        imported = gallery2.import_entry(
            json_data,
            importer_id="importer1",
            importer_name="Importer"
        )

        assert imported is not None
        assert "(imported)" in imported.title
        assert imported.creator_id == "importer1"
        assert gallery2.count == 1

    def test_featured_and_popular_workflow(self):
        """Test featuring entries and popularity rankings."""
        gallery = Gallery()

        # Submit multiple entries
        entries = []
        for i in range(5):
            tags = ArtTags(object_type=ObjectType.TREE)
            tree = StaticArt.from_string(
                f"Tree{i}",
                "  ^\n /|\\\n  |",
                tags
            )
            entry = gallery.submit(
                art=tree,
                title=f"Tree Design {i}",
                creator_id=f"creator{i}",
                description=f"Tree design number {i}"
            )
            entries.append(entry)

        # Give different engagement levels
        # Entry 2 gets most likes
        for _ in range(10):
            gallery.like_entry(entries[2].id, f"player{_}")

        # Entry 4 gets second most
        for _ in range(5):
            gallery.like_entry(entries[4].id, f"liker{_}")

        # Feature entry 0
        gallery.feature_entry(entries[0].id)

        # Verify featured
        featured = gallery.get_featured()
        assert len(featured) == 1
        assert featured[0].id == entries[0].id

        # Verify popular (sorted by likes)
        popular = gallery.get_popular(limit=3)
        assert popular[0].likes == 10  # Entry 2
        assert popular[1].likes == 5   # Entry 4


class TestWorldIntegrationPipeline:
    """E2E tests for world integration workflow."""

    def test_asset_spawning_and_tracking(self):
        """Pipeline: spawn assets in world and track usage."""
        pool = AssetPool()
        stats = UsageStats()

        # Create various assets
        tree = create_from_template("small_tree", "system")
        rock = create_from_template("large_rock", "system")

        pool.add_asset(tree)
        pool.add_asset(rock)

        # Simulate world generation spawning assets
        environments = ["forest", "forest", "mountain", "plains"]

        for env in environments:
            # Query suitable assets
            query = AssetQuery(environment=EnvironmentType[env.upper()] if env != "plains" else None)
            available = pool.query(query)

            if available:
                # Spawn some assets
                for asset in available[:2]:
                    pool.record_usage(asset.id, env)
                    stats.record_event(asset.id, "spawn", env)

        # Simulate player interactions
        for _ in range(5):
            stats.record_event(tree.id, "interact", "forest", "player1")

        # Verify tracking
        tree_stats = stats.get_asset_stats(tree.id)
        assert tree_stats.total_spawns > 0
        assert tree_stats.total_interactions == 5
        assert "forest" in tree_stats.environments_used

        # Check pool statistics
        pool_stats = pool.get_statistics()
        assert pool_stats["total_assets"] == 2
        assert pool_stats["total_usage"] > 0

    def test_entity_world_behavior_simulation(self):
        """Simulate entity behavior in world context."""
        # Create entity from template
        deer = create_entity_from_template("forest_deer")
        guard = create_entity_from_template("village_guard")

        assert deer is not None
        assert guard is not None

        # Simulate world update loop
        for tick in range(10):
            delta_time = 0.1  # 100ms per tick

            deer.update(delta_time)
            guard.update(delta_time)

            # Deer should be idle
            idle_action = deer.decide_idle_action()
            assert idle_action is not None

        # Simulate threat encounter
        deer_response = deer.respond_to_threat(0.7, "wolf1")
        assert deer_response == ThreatResponse.FLEE
        assert deer.state == EntityState.FLEEING

        guard_response = guard.respond_to_threat(0.5, "bandit1")
        assert guard_response in (ThreatResponse.ATTACK, ThreatResponse.CHALLENGE, ThreatResponse.PROTECT)

        # Simulate combat
        damage = guard.attack(deer)
        assert damage > 0 or guard.stats.energy < 100  # Either dealt damage or used energy

    def test_random_asset_selection_for_environment(self):
        """Test weighted random selection for world population."""
        pool = AssetPool()

        # Add multiple forest assets with different spawn weights
        for i in range(5):
            tags = ArtTags(
                object_type=ObjectType.TREE,
                environment_types={EnvironmentType.FOREST}
            )
            tree = StaticArt.from_string(
                f"ForestTree{i}",
                "^\n|",
                tags,
                spawn_weight=1.0 + i * 0.5  # Increasing weights
            )
            pool.add_asset(tree)

        # Select many random assets
        selections = {}
        for _ in range(100):
            asset = pool.get_random(
                object_type=ObjectType.TREE,
                environment=EnvironmentType.FOREST,
                weighted=True
            )
            if asset:
                selections[asset.id] = selections.get(asset.id, 0) + 1

        # Higher weight assets should appear more often (statistically)
        assert len(selections) > 0


class TestFeedbackAndRatingPipeline:
    """E2E tests for the feedback and rating system."""

    def test_complete_feedback_workflow(self):
        """Full feedback workflow from creation to rating adjustments."""
        pool = AssetPool()
        stats = UsageStats()
        gallery = Gallery()

        # Create and submit art
        tags = ArtTags(object_type=ObjectType.PLANT)
        flower = StaticArt.from_string("Rose", "@", tags)
        pool.add_asset(flower)

        entry = gallery.submit(
            art=flower,
            title="Red Rose",
            creator_id="gardener1",
            creator_name="Gardener"
        )

        # Multiple players provide feedback
        players = ["player1", "player2", "player3", "player4", "player5"]

        for i, player in enumerate(players):
            # Record spawn events
            stats.record_event(flower.id, "spawn", "garden", player)

            # Record interaction
            stats.record_event(flower.id, "interact", "garden", player)

            # Rate in pool
            pool.rate_asset(flower.id, 3.0 + i * 0.5)  # 3.0, 3.5, 4.0, 4.5, 5.0

            # Like in gallery
            gallery.like_entry(entry.id, player)

            # Some favorite it
            if i >= 3:
                stats.record_feedback(flower.id, player, FeedbackType.FAVORITE)

        # Verify aggregated stats
        asset_stats = stats.get_asset_stats(flower.id)
        assert asset_stats.total_spawns == 5
        assert asset_stats.total_interactions == 5
        assert asset_stats.favorites == 2

        # Verify rating
        pool_entry = pool.get_entry(flower.id)
        assert pool_entry.rating == 4.0  # Average of 3.0-5.0

        # Verify gallery engagement
        assert entry.likes == 5

        # Check trending
        trending = stats.get_trending(hours=24, count=5)
        assert len(trending) > 0
        assert trending[0][0] == flower.id

    def test_report_and_moderation_workflow(self):
        """Test content reporting workflow."""
        stats = UsageStats()
        gallery = Gallery()

        # Create potentially problematic content
        tags = ArtTags(object_type=ObjectType.OTHER)
        art = StaticArt.from_string("Reported", "XXX", tags)

        entry = gallery.submit(
            art=art,
            title="Reported Content",
            creator_id="badactor",
            content_rating=ContentRating.EVERYONE
        )

        # Multiple users report it
        for i in range(3):
            stats.record_feedback(art.id, f"reporter{i}", FeedbackType.REPORT, "Inappropriate")

        # Check reported assets
        reported = stats.get_reported_assets(min_reports=2)
        assert art.id in reported

        # Verify report count in stats
        art_stats = stats.get_asset_stats(art.id)
        assert art_stats.reports == 3


class TestMultiPlayerCollaborationPipeline:
    """E2E tests for multi-player scenarios."""

    def test_shared_asset_pool_workflow(self):
        """Multiple players contributing to shared pool."""
        # Shared resources
        shared_pool = AssetPool()
        shared_gallery = Gallery()
        shared_stats = UsageStats()

        # Create art directly with different player IDs
        art_configs = [
            ("artist1", "Tree", ObjectType.TREE, " ^ \n/|\\\n |"),
            ("artist2", "Rock", ObjectType.ROCK, "___\n\\_/"),
            ("artist3", "Flower", ObjectType.PLANT, "@"),
        ]

        for player_id, name, obj_type, art_str in art_configs:
            tags = ArtTags(object_type=obj_type)
            art = StaticArt.from_string(name, art_str, tags, player_id=player_id)
            shared_pool.add_asset(art)
            shared_gallery.submit(
                art=art,
                title=f"{name} by {player_id}",
                creator_id=player_id,
                creator_name=player_id
            )

        # Verify shared pool has all assets
        assert shared_pool.count == 3

        # All assets are queryable
        available = shared_pool.query(AssetQuery())
        assert len(available) == 3

        # Players can rate each other's work
        assets = list(shared_pool)
        shared_pool.rate_asset(assets[1].id, 4.5)

        # Verify player-specific queries work
        artist1_assets = shared_pool.get_by_player("artist1")
        assert len(artist1_assets) == 1

    def test_entity_interaction_between_players(self):
        """Test entities created by different players interacting."""
        # Create two entities using valid templates
        guard = create_entity_from_template("village_guard")
        deer = create_entity_from_template("forest_deer")

        assert guard is not None, "village_guard template should exist"
        assert deer is not None, "forest_deer template should exist"

        guard.player_id = "player1"
        deer.player_id = "player2"

        # Simulate guard attacking deer
        initial_health = deer.stats.health

        # Guard attacks
        damage = guard.attack(deer)

        assert damage > 0
        assert deer.stats.health < initial_health

        # Deer remembers the attack and has grudge
        assert guard.id in deer.memory.grudges

        # Deer responds to threat
        response = deer.respond_to_threat(0.8, guard.id)
        assert response == ThreatResponse.FLEE
        assert deer.state == EntityState.FLEEING


class TestCompleteStudioWorkflow:
    """E2E tests for complete studio sessions."""

    def test_full_creation_session(self):
        """Simulate a complete art creation session."""
        studio = Studio(player_id="session_user")

        # Session: Create a detailed house
        studio.new_canvas(15, 10, "Village House")

        # Draw roof
        studio.draw_line(3, 0, 7, 0, "_")
        studio.draw_at(2, 1, "/")
        studio.draw_at(8, 1, "\\")
        studio.draw_line(1, 2, 9, 2, "-")

        # Draw walls
        studio.draw_line(1, 3, 1, 8, "|")
        studio.draw_line(9, 3, 9, 8, "|")

        # Draw floor
        studio.draw_line(1, 9, 9, 9, "_")

        # Add door
        studio.draw_rectangle(4, 6, 3, 3, "#")
        studio.draw_at(5, 7, " ")
        studio.draw_at(5, 8, " ")

        # Add windows
        studio.draw_rectangle(2, 4, 2, 2, "#")
        studio.draw_rectangle(7, 4, 2, 2, "#")

        # Configure tags
        studio.set_object_type(ObjectType.STRUCTURE)
        studio.add_environment(EnvironmentType.VILLAGE)
        studio.add_environment(EnvironmentType.PLAINS)
        studio.add_interaction(InteractionType.OPENABLE)
        studio.add_custom_tag("residential")
        studio.add_custom_tag("medieval")

        # Convert and configure
        static = studio.convert_to_static()
        static.blocks_movement = True
        static.blocks_vision = True
        static.render_layer = RenderLayer.STRUCTURE
        static.provides_cover = 1.0

        # Save to pool
        asset_id = studio.save_to_pool()

        # Submit to gallery
        entry = studio.submit_to_gallery(
            title="Medieval Village House",
            description="A cozy two-story house for village NPCs",
            tags={"house", "medieval", "village", "building"},
            creator_name="ArchitectMaster"
        )

        # Verify everything is set up correctly
        assert studio.asset_pool.count == 1
        assert studio.gallery.count == 1

        # Check asset properties
        asset = studio.asset_pool.get_asset(asset_id)
        assert asset.blocks_movement
        assert asset.provides_cover == 1.0
        assert InteractionType.OPENABLE in asset.tags.interaction_types

        # Get status
        status = studio.get_status()
        assert status["has_art"]
        assert status["can_undo"]

    def test_template_based_creation_session(self):
        """Create content starting from templates."""
        studio = Studio(player_id="template_user")

        # List available templates
        static_templates = Studio.list_static_templates()
        entity_templates = Studio.list_entity_templates()
        personality_templates = Studio.list_personality_templates()

        assert len(static_templates) > 0
        assert len(entity_templates) > 0
        assert len(personality_templates) > 0

        # Load a static template
        studio.load_template("small_tree")
        assert studio.current_art is not None
        assert studio.current_art.tags.object_type == ObjectType.TREE

        # Modify it
        studio.draw_at(0, 0, "*")  # Add a star

        # Save variant
        studio.current_art.name = "Christmas Tree"
        studio.add_custom_tag("holiday")
        studio.save_to_pool()

        # Load entity template
        studio.load_template("village_guard")
        assert isinstance(studio.current_art, DynamicEntity)

        # Customize guard
        studio.current_art.add_dialogue("Welcome to the village!")
        studio.current_art.add_dialogue("Stay out of trouble.")

        studio.save_to_pool()

        # Verify both are in pool
        assert studio.asset_pool.count == 2


class TestSerializationPipeline:
    """E2E tests for data persistence workflows."""

    def test_full_system_serialization(self):
        """Test serializing and restoring entire system state."""
        # Create and populate system
        pool = AssetPool()
        gallery = Gallery()
        stats = UsageStats()

        studio = Studio(
            player_id="persist_user",
            asset_pool=pool,
            gallery=gallery,
            usage_stats=stats
        )

        # Create some content
        studio.new_canvas(5, 3, "Test Art")
        studio.draw_rectangle(0, 0, 5, 3, "#")
        studio.set_object_type(ObjectType.STRUCTURE)
        static = studio.convert_to_static()
        studio.save_to_pool()

        entry = studio.submit_to_gallery(
            title="Test Structure",
            creator_name="TestUser"
        )

        # Add engagement
        gallery.like_entry(entry.id, "player1")
        stats.record_event(static.id, "spawn", "test_env")
        stats.record_feedback(static.id, "player1", FeedbackType.LIKE)

        # Serialize everything
        pool_data = pool.to_dict()
        gallery_data = gallery.to_dict()
        stats_data = stats.to_dict()

        # Restore from serialized data
        restored_pool = AssetPool.from_dict(pool_data)
        restored_gallery = Gallery.from_dict(gallery_data)
        restored_stats = UsageStats.from_dict(stats_data)

        # Verify restoration
        assert restored_pool.count == pool.count
        assert restored_gallery.count == gallery.count
        assert len(restored_stats._asset_stats) == len(stats._asset_stats)

        # Verify content integrity
        restored_asset = list(restored_pool)[0]
        assert restored_asset.name == "Test Art"
        assert restored_asset.tags.object_type == ObjectType.STRUCTURE

        restored_entry = list(restored_gallery)[0]
        assert restored_entry.likes == 1

    def test_art_json_round_trip(self):
        """Test individual art serialization round-trip."""
        # Create complex art
        tags = ArtTags(
            object_type=ObjectType.CREATURE,
            interaction_types={InteractionType.TALKABLE, InteractionType.COLLECTIBLE},
            environment_types={EnvironmentType.FOREST, EnvironmentType.CAVE},
            size=Size.SMALL,
            mood="mysterious",
            custom_tags={"rare", "magical"}
        )

        entity = DynamicEntity.from_string(
            "Magic Creature",
            "***\n*@*\n***",
            tags,
            personality=PERSONALITY_TEMPLATES["curious_neutral"].copy()
        )

        entity.stats.health = 75
        entity.add_dialogue("Greetings, traveler!")
        entity.loot_table = {"magic_dust": 0.5}

        # Add animation
        anim = Animation(
            name="sparkle",
            frames=[
                AnimationFrame.from_string("*.*\n.@.\n*.*", duration=0.2),
                AnimationFrame.from_string(".*.\n*@*\n.*.", duration=0.2),
            ],
            loop=True
        )
        entity.add_animation(anim)

        # Serialize
        data = entity.to_dict()
        json_str = json.dumps(data)

        # Deserialize
        restored_data = json.loads(json_str)
        restored = DynamicEntity.from_dict(restored_data)

        # Verify everything
        assert restored.name == entity.name
        assert restored.stats.health == 75
        assert restored.personality.name == entity.personality.name
        assert "sparkle" in restored.animations
        assert len(restored.animations["sparkle"].frames) == 2
        assert "Greetings, traveler!" in restored.dialogue_pool


class TestErrorHandlingPipeline:
    """E2E tests for error handling and edge cases."""

    def test_invalid_operations_handled(self):
        """Test that invalid operations are handled gracefully."""
        studio = Studio(player_id="error_test")

        # Operations without art should not crash
        assert studio.export_to_string() is None
        assert studio.export_to_dict() is None
        assert studio.save_to_pool() is None

        preview = studio.render_preview()
        assert "no art loaded" in preview

        # Create art
        studio.new_canvas(5, 5, "Test")

        # Paste without clipboard
        assert studio.paste() is False

        # Undo with no history
        studio._clear_history()
        assert studio.undo() is False

        # Redo with nothing to redo
        assert studio.redo() is False

    def test_concurrent_access_simulation(self):
        """Simulate concurrent access patterns."""
        shared_pool = AssetPool()
        shared_gallery = Gallery()

        # Multiple studios accessing same resources
        studios = [
            Studio(player_id=f"user{i}", asset_pool=shared_pool, gallery=shared_gallery)
            for i in range(5)
        ]

        # Each creates and shares content
        for i, studio in enumerate(studios):
            studio.new_canvas(3, 3, f"Art{i}")
            studio.draw_at(1, 1, str(i))
            studio.set_object_type(ObjectType.OTHER)
            studio.convert_to_static()
            studio.save_to_pool()
            studio.submit_to_gallery(
                title=f"Art by User {i}",
                creator_name=f"User{i}"
            )

        # All content accessible
        assert shared_pool.count == 5
        assert shared_gallery.count == 5

        # All studios can query all content
        for studio in studios:
            assert len(studio.asset_pool.query(AssetQuery())) == 5


# Run all E2E tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
