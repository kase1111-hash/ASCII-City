"""
Tests for the tagging system.
"""

import pytest
from src.shadowengine.studio.tags import (
    ArtTags, TagQuery, ObjectType, Size, Placement,
    InteractionType, EnvironmentType
)


class TestObjectType:
    """Tests for ObjectType enum."""

    def test_all_types_exist(self):
        """Verify all expected object types exist."""
        expected = [
            "TREE", "ROCK", "PLANT", "WATER", "STRUCTURE",
            "FURNITURE", "ITEM", "NPC", "CREATURE", "VEHICLE",
            "DECORATION", "TERRAIN", "EFFECT", "OTHER"
        ]
        for name in expected:
            assert hasattr(ObjectType, name)

    def test_types_are_unique(self):
        """Object type values should be unique."""
        values = [t.value for t in ObjectType]
        assert len(values) == len(set(values))


class TestSize:
    """Tests for Size enum."""

    def test_all_sizes_exist(self):
        """Verify all size categories exist."""
        expected = ["TINY", "SMALL", "MEDIUM", "LARGE", "HUGE", "MULTI_TILE"]
        for name in expected:
            assert hasattr(Size, name)


class TestPlacement:
    """Tests for Placement enum."""

    def test_all_placements_exist(self):
        """Verify all placement types exist."""
        expected = ["FLOOR", "WALL", "CEILING", "FLOATING", "WATER", "UNDERGROUND"]
        for name in expected:
            assert hasattr(Placement, name)


class TestInteractionType:
    """Tests for InteractionType enum."""

    def test_all_interactions_exist(self):
        """Verify all interaction types exist."""
        expected = [
            "NONE", "CLIMBABLE", "COLLECTIBLE", "HIDEABLE",
            "SEARCHABLE", "BREAKABLE", "FLAMMABLE", "PUSHABLE",
            "OPENABLE", "READABLE", "TALKABLE", "RIDEABLE",
            "WEARABLE", "CONSUMABLE", "TRIGGERABLE"
        ]
        for name in expected:
            assert hasattr(InteractionType, name)


class TestEnvironmentType:
    """Tests for EnvironmentType enum."""

    def test_all_environments_exist(self):
        """Verify all environment types exist."""
        expected = [
            "FOREST", "URBAN", "CAVE", "RIVER", "MOUNTAIN",
            "DESERT", "OCEAN", "SWAMP", "PLAINS", "DUNGEON",
            "CASTLE", "VILLAGE", "RUINS", "UNDERGROUND", "SKY",
            "INDOOR", "OUTDOOR"
        ]
        for name in expected:
            assert hasattr(EnvironmentType, name)


class TestArtTags:
    """Tests for ArtTags dataclass."""

    def test_create_minimal_tags(self, basic_tags):
        """Can create tags with just object type."""
        assert basic_tags.object_type == ObjectType.TREE
        assert basic_tags.size == Size.MEDIUM  # Default
        assert basic_tags.placement == Placement.FLOOR  # Default
        assert len(basic_tags.interaction_types) == 0
        assert len(basic_tags.environment_types) == 0

    def test_create_full_tags(self, full_tags):
        """Can create fully populated tags."""
        assert full_tags.object_type == ObjectType.STRUCTURE
        assert full_tags.size == Size.LARGE
        assert full_tags.placement == Placement.FLOOR
        assert InteractionType.CLIMBABLE in full_tags.interaction_types
        assert InteractionType.HIDEABLE in full_tags.interaction_types
        assert EnvironmentType.FOREST in full_tags.environment_types
        assert EnvironmentType.VILLAGE in full_tags.environment_types
        assert full_tags.mood == "peaceful"
        assert full_tags.era == "medieval"
        assert full_tags.material == "wood"
        assert "custom1" in full_tags.custom_tags

    def test_add_interaction(self, basic_tags):
        """Can add interaction types."""
        basic_tags.add_interaction(InteractionType.CLIMBABLE)
        assert InteractionType.CLIMBABLE in basic_tags.interaction_types

    def test_remove_interaction(self, full_tags):
        """Can remove interaction types."""
        full_tags.remove_interaction(InteractionType.CLIMBABLE)
        assert InteractionType.CLIMBABLE not in full_tags.interaction_types

    def test_add_environment(self, basic_tags):
        """Can add environment types."""
        basic_tags.add_environment(EnvironmentType.FOREST)
        assert EnvironmentType.FOREST in basic_tags.environment_types

    def test_remove_environment(self, full_tags):
        """Can remove environment types."""
        full_tags.remove_environment(EnvironmentType.FOREST)
        assert EnvironmentType.FOREST not in full_tags.environment_types

    def test_add_custom_tag(self, basic_tags):
        """Can add custom tags."""
        basic_tags.add_custom_tag("  Custom TAG  ")
        assert "custom tag" in basic_tags.custom_tags  # Normalized

    def test_has_interaction(self, full_tags):
        """Can check for interaction."""
        assert full_tags.has_interaction(InteractionType.CLIMBABLE)
        assert not full_tags.has_interaction(InteractionType.CONSUMABLE)

    def test_fits_environment(self, full_tags):
        """Can check environment fit."""
        assert full_tags.fits_environment(EnvironmentType.FOREST)
        assert not full_tags.fits_environment(EnvironmentType.DESERT)

    def test_get_affordances(self, full_tags):
        """Can get affordance strings."""
        affordances = full_tags.get_affordances()
        assert "climbable" in affordances
        assert "hideable" in affordances

    def test_serialization(self, full_tags):
        """Tags can be serialized and deserialized."""
        data = full_tags.to_dict()
        restored = ArtTags.from_dict(data)

        assert restored.object_type == full_tags.object_type
        assert restored.size == full_tags.size
        assert restored.placement == full_tags.placement
        assert restored.interaction_types == full_tags.interaction_types
        assert restored.environment_types == full_tags.environment_types
        assert restored.mood == full_tags.mood
        assert restored.custom_tags == full_tags.custom_tags


class TestTagQuery:
    """Tests for TagQuery matching."""

    def test_empty_query_matches_all(self, basic_tags, full_tags):
        """Empty query matches any tags."""
        query = TagQuery()
        assert basic_tags.matches_query(query)
        assert full_tags.matches_query(query)

    def test_object_type_filter(self, basic_tags, full_tags):
        """Can filter by object type."""
        tree_query = TagQuery(object_type=ObjectType.TREE)
        structure_query = TagQuery(object_type=ObjectType.STRUCTURE)

        assert basic_tags.matches_query(tree_query)
        assert not basic_tags.matches_query(structure_query)
        assert full_tags.matches_query(structure_query)
        assert not full_tags.matches_query(tree_query)

    def test_size_filter(self, basic_tags, full_tags):
        """Can filter by size."""
        medium_query = TagQuery(size=Size.MEDIUM)
        large_query = TagQuery(size=Size.LARGE)

        assert basic_tags.matches_query(medium_query)
        assert not basic_tags.matches_query(large_query)
        assert full_tags.matches_query(large_query)

    def test_placement_filter(self, basic_tags):
        """Can filter by placement."""
        floor_query = TagQuery(placement=Placement.FLOOR)
        wall_query = TagQuery(placement=Placement.WALL)

        assert basic_tags.matches_query(floor_query)
        assert not basic_tags.matches_query(wall_query)

    def test_required_interactions_filter(self, full_tags):
        """Can filter by required interactions."""
        query = TagQuery(required_interactions={InteractionType.CLIMBABLE})
        assert full_tags.matches_query(query)

        query2 = TagQuery(required_interactions={InteractionType.CONSUMABLE})
        assert not full_tags.matches_query(query2)

    def test_required_environments_filter(self, full_tags):
        """Can filter by required environments (any match)."""
        query = TagQuery(required_environments={EnvironmentType.FOREST})
        assert full_tags.matches_query(query)

        query2 = TagQuery(required_environments={EnvironmentType.DESERT})
        assert not full_tags.matches_query(query2)

    def test_material_filter(self, full_tags):
        """Can filter by material."""
        wood_query = TagQuery(material="wood")
        stone_query = TagQuery(material="stone")

        assert full_tags.matches_query(wood_query)
        assert not full_tags.matches_query(stone_query)

    def test_combined_filters(self, full_tags):
        """Can combine multiple filters."""
        query = TagQuery(
            object_type=ObjectType.STRUCTURE,
            size=Size.LARGE,
            required_interactions={InteractionType.CLIMBABLE},
            required_environments={EnvironmentType.FOREST}
        )
        assert full_tags.matches_query(query)

        # Change one filter to fail
        query2 = TagQuery(
            object_type=ObjectType.STRUCTURE,
            size=Size.SMALL,  # Wrong size
            required_interactions={InteractionType.CLIMBABLE}
        )
        assert not full_tags.matches_query(query2)
