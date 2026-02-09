"""
Pytest fixtures for ASCII Studio tests.
"""

import pytest
from datetime import datetime

from src.shadowengine.studio.art import ASCIIArt, ArtCategory
from src.shadowengine.studio.tags import (
    ArtTags, ObjectType, Size, Placement,
    InteractionType, EnvironmentType
)
from src.shadowengine.studio.static_art import StaticArt, RenderLayer, TileCoverage
from src.shadowengine.studio.entity import (
    DynamicEntity, EntityState, EntityStats, EntityMemory
)
from src.shadowengine.studio.personality import (
    PersonalityTemplate, IdleBehavior, ThreatResponse, Attitude
)
from src.shadowengine.studio.animation import Animation, AnimationFrame, AnimationTrigger
from src.shadowengine.studio.asset_pool import AssetPool
from src.shadowengine.studio.usage_stats import UsageStats, FeedbackType
from src.shadowengine.studio.gallery import Gallery, GalleryEntry, ContentRating
from src.shadowengine.studio.studio import Studio, StudioMode, Tool


# === Tag Fixtures ===

@pytest.fixture
def basic_tags():
    """Basic art tags."""
    return ArtTags(object_type=ObjectType.TREE)


@pytest.fixture
def full_tags():
    """Fully populated art tags."""
    return ArtTags(
        object_type=ObjectType.STRUCTURE,
        interaction_types={InteractionType.CLIMBABLE, InteractionType.HIDEABLE},
        environment_types={EnvironmentType.FOREST, EnvironmentType.VILLAGE},
        size=Size.LARGE,
        placement=Placement.FLOOR,
        mood="peaceful",
        era="medieval",
        material="wood",
        custom_tags={"custom1", "custom2"}
    )


# === Art Fixtures ===

@pytest.fixture
def simple_tiles():
    """Simple 3x3 tile array."""
    return [
        ["#", "#", "#"],
        ["#", " ", "#"],
        ["#", "#", "#"]
    ]


@pytest.fixture
def tree_tiles():
    """Tree-shaped tiles."""
    return [
        [" ", " ", "^", " ", " "],
        [" ", "/", "|", "\\", " "],
        [" ", " ", "|", " ", " "]
    ]


@pytest.fixture
def basic_art(simple_tiles, basic_tags):
    """Basic ASCII art instance."""
    return ASCIIArt(
        name="Test Art",
        tiles=simple_tiles,
        tags=basic_tags
    )


@pytest.fixture
def tree_art(tree_tiles):
    """Tree ASCII art."""
    tags = ArtTags(
        object_type=ObjectType.TREE,
        environment_types={EnvironmentType.FOREST},
        size=Size.SMALL
    )
    return ASCIIArt(
        name="Pine Tree",
        tiles=tree_tiles,
        tags=tags,
        description="A small pine tree"
    )


# === Static Art Fixtures ===

@pytest.fixture
def static_tree(tree_tiles):
    """Static tree art."""
    tags = ArtTags(
        object_type=ObjectType.TREE,
        environment_types={EnvironmentType.FOREST},
        size=Size.SMALL
    )
    return StaticArt(
        name="Pine Tree",
        tiles=tree_tiles,
        tags=tags,
        render_layer=RenderLayer.STRUCTURE,
        blocks_movement=True,
        blocks_vision=False,
        provides_cover=0.3
    )


@pytest.fixture
def static_rock():
    """Static rock art."""
    tiles = [
        [" ", "_", "_", "_", " "],
        ["/", " ", " ", " ", "\\"],
        ["\\", "_", "_", "_", "/"]
    ]
    tags = ArtTags(
        object_type=ObjectType.ROCK,
        environment_types={EnvironmentType.MOUNTAIN, EnvironmentType.CAVE},
        size=Size.MEDIUM
    )
    return StaticArt(
        name="Large Rock",
        tiles=tiles,
        tags=tags,
        render_layer=RenderLayer.OBJECT,
        blocks_movement=True,
        blocks_vision=True,
        provides_cover=0.8
    )


# === Personality Fixtures ===

@pytest.fixture
def basic_personality():
    """Basic personality template."""
    return PersonalityTemplate(name="Basic")


@pytest.fixture
def aggressive_personality():
    """Aggressive personality template."""
    return PersonalityTemplate(
        name="Aggressive",
        traits={"aggression": 0.9, "fear": 0.1, "curiosity": 0.4},
        idle_behavior=IdleBehavior.PATROL,
        threat_response=ThreatResponse.ATTACK,
        player_attitude=Attitude.HOSTILE
    )


@pytest.fixture
def timid_personality():
    """Timid personality template."""
    return PersonalityTemplate(
        name="Timid",
        traits={"aggression": 0.1, "fear": 0.9, "curiosity": 0.3},
        idle_behavior=IdleBehavior.FORAGE,
        threat_response=ThreatResponse.FLEE,
        player_attitude=Attitude.AFRAID
    )


# === Entity Fixtures ===

@pytest.fixture
def basic_entity(simple_tiles, basic_tags, basic_personality):
    """Basic dynamic entity."""
    return DynamicEntity(
        name="Test Entity",
        tiles=simple_tiles,
        tags=basic_tags,
        personality=basic_personality
    )


@pytest.fixture
def creature_entity(timid_personality):
    """Creature entity with full configuration."""
    tiles = [
        [" ", "/", "\\", " "],
        ["(", "o", "o", ")"],
        [" ", "|", "|", " "]
    ]
    tags = ArtTags(
        object_type=ObjectType.CREATURE,
        environment_types={EnvironmentType.FOREST},
        size=Size.SMALL
    )
    return DynamicEntity(
        name="Forest Creature",
        tiles=tiles,
        tags=tags,
        personality=timid_personality,
        stats=EntityStats(health=50, max_health=50, speed=1.5),
        dialogue_pool=["Squeak!", "..."],
        loot_table={"fur": 0.8, "meat": 0.5}
    )


@pytest.fixture
def npc_entity(basic_personality):
    """NPC entity."""
    tiles = [
        [" ", "O", " "],
        ["/", "|", "\\"],
        ["/", " ", "\\"]
    ]
    tags = ArtTags(
        object_type=ObjectType.NPC,
        interaction_types={InteractionType.TALKABLE},
        environment_types={EnvironmentType.VILLAGE}
    )
    return DynamicEntity(
        name="Villager",
        tiles=tiles,
        tags=tags,
        personality=basic_personality,
        dialogue_pool=["Hello there!", "Nice weather.", "Need something?"]
    )


# === Animation Fixtures ===

@pytest.fixture
def simple_frame():
    """Simple animation frame."""
    return AnimationFrame(
        tiles=[["*"]],
        duration=0.5
    )


@pytest.fixture
def idle_frames():
    """Frames for idle animation."""
    return [
        AnimationFrame(tiles=[["O"]], duration=0.5),
        AnimationFrame(tiles=[["o"]], duration=0.5),
        AnimationFrame(tiles=[["O"]], duration=0.5),
        AnimationFrame(tiles=[["O"]], duration=1.0)
    ]


@pytest.fixture
def idle_animation(idle_frames):
    """Idle animation."""
    return Animation(
        name="idle",
        frames=idle_frames,
        loop=True,
        trigger=AnimationTrigger.ON_IDLE
    )


@pytest.fixture
def attack_animation():
    """Attack animation (non-looping)."""
    frames = [
        AnimationFrame(tiles=[["\\O/"]], duration=0.1),
        AnimationFrame(tiles=[["_O_"]], duration=0.1),
        AnimationFrame(tiles=[["/O\\"]], duration=0.1),
        AnimationFrame(tiles=[["\\O/"]], duration=0.2)
    ]
    return Animation(
        name="attack",
        frames=frames,
        loop=False,
        trigger=AnimationTrigger.ON_ACTION
    )


# === Asset Pool Fixtures ===

@pytest.fixture
def empty_pool():
    """Empty asset pool."""
    return AssetPool()


@pytest.fixture
def populated_pool(static_tree, static_rock, creature_entity):
    """Pool with various assets."""
    pool = AssetPool()
    pool.add_asset(static_tree)
    pool.add_asset(static_rock)
    pool.add_asset(creature_entity)
    return pool


# === Usage Stats Fixtures ===

@pytest.fixture
def empty_stats():
    """Empty usage stats."""
    return UsageStats()


@pytest.fixture
def stats_with_data(static_tree, creature_entity):
    """Usage stats with recorded data."""
    stats = UsageStats()

    # Record some events
    for i in range(10):
        stats.record_event(static_tree.id, "spawn", "forest")
    for i in range(5):
        stats.record_event(creature_entity.id, "spawn", "forest")
        stats.record_event(creature_entity.id, "interact", "forest", "player1")

    # Record feedback
    stats.record_feedback(static_tree.id, "player1", FeedbackType.LIKE)
    stats.record_feedback(static_tree.id, "player2", FeedbackType.LIKE)
    stats.record_feedback(creature_entity.id, "player1", FeedbackType.FAVORITE)

    return stats


# === Gallery Fixtures ===

@pytest.fixture
def empty_gallery():
    """Empty gallery."""
    return Gallery()


@pytest.fixture
def populated_gallery(static_tree, static_rock, creature_entity):
    """Gallery with entries."""
    gallery = Gallery()

    gallery.submit(
        art=static_tree,
        title="Beautiful Tree",
        creator_id="player1",
        creator_name="TreeLover",
        description="A nice pine tree",
        tags={"tree", "nature", "forest"}
    )

    gallery.submit(
        art=static_rock,
        title="Rocky Rock",
        creator_id="player2",
        creator_name="RockFan",
        description="A solid rock",
        tags={"rock", "nature", "mountain"}
    )

    gallery.submit(
        art=creature_entity,
        title="Cute Creature",
        creator_id="player1",
        creator_name="TreeLover",
        description="A forest creature",
        tags={"creature", "forest", "cute"}
    )

    return gallery


# === Studio Fixtures ===

@pytest.fixture
def empty_studio():
    """Empty studio instance."""
    return Studio(player_id="test_player")


@pytest.fixture
def studio_with_canvas(empty_studio):
    """Studio with a canvas created."""
    empty_studio.new_canvas(20, 10, "Test Canvas")
    return empty_studio


@pytest.fixture
def studio_with_art(empty_studio, basic_art):
    """Studio with art loaded."""
    empty_studio.load_art(basic_art)
    return empty_studio


@pytest.fixture
def full_studio(static_tree, creature_entity):
    """Fully configured studio."""
    pool = AssetPool()
    gallery = Gallery()
    stats = UsageStats()

    pool.add_asset(static_tree)
    pool.add_asset(creature_entity)

    studio = Studio(
        player_id="test_player",
        asset_pool=pool,
        gallery=gallery,
        usage_stats=stats
    )
    studio.new_canvas(30, 15, "Full Test")

    return studio
