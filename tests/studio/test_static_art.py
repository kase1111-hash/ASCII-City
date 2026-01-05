"""
Tests for StaticArt class.
"""

import pytest
from src.shadowengine.studio.static_art import (
    StaticArt, RenderLayer, TileCoverage,
    STATIC_ART_TEMPLATES, create_from_template
)
from src.shadowengine.studio.art import ArtCategory
from src.shadowengine.studio.tags import ArtTags, ObjectType


class TestRenderLayer:
    """Tests for RenderLayer enum."""

    def test_layers_exist(self):
        """All render layers exist."""
        expected = ["GROUND", "FLOOR", "OBJECT", "STRUCTURE", "OVERLAY", "EFFECT", "UI"]
        for name in expected:
            assert hasattr(RenderLayer, name)

    def test_layer_ordering(self):
        """Layers have correct ordering."""
        assert RenderLayer.GROUND.value < RenderLayer.OBJECT.value
        assert RenderLayer.OBJECT.value < RenderLayer.STRUCTURE.value
        assert RenderLayer.STRUCTURE.value < RenderLayer.OVERLAY.value


class TestTileCoverage:
    """Tests for TileCoverage enum."""

    def test_coverages_exist(self):
        """All coverage types exist."""
        expected = ["SINGLE", "MULTI_TILE", "ANCHOR"]
        for name in expected:
            assert hasattr(TileCoverage, name)


class TestStaticArt:
    """Tests for StaticArt class."""

    def test_create_static_art(self, static_tree):
        """Can create static art."""
        assert static_tree.name == "Pine Tree"
        assert static_tree.category == ArtCategory.STATIC
        assert static_tree.render_layer == RenderLayer.STRUCTURE
        assert static_tree.blocks_movement is True
        assert static_tree.blocks_vision is False

    def test_provides_cover(self, static_tree, static_rock):
        """Cover values are set correctly."""
        assert static_tree.provides_cover == 0.3
        assert static_rock.provides_cover == 0.8

    def test_provides_cover_validation(self):
        """Invalid cover value raises error."""
        tags = ArtTags(object_type=ObjectType.OTHER)
        with pytest.raises(ValueError):
            StaticArt(
                name="Bad",
                tiles=[["#"]],
                tags=tags,
                provides_cover=1.5  # Invalid
            )

    def test_collision_mask_generation(self, static_tree):
        """Collision mask is auto-generated."""
        assert static_tree.collision_mask is not None
        # Non-space characters should be solid
        assert static_tree.collision_mask[0][2] is True  # ^ is solid
        assert static_tree.collision_mask[0][0] is False  # space is not solid

    def test_is_solid_at(self, static_tree):
        """Can check if position is solid."""
        # Trunk position should be solid
        assert static_tree.is_solid_at(2, 0) is True
        # Empty space should not be solid
        assert static_tree.is_solid_at(0, 0) is False

    def test_is_solid_at_no_blocking(self):
        """Non-blocking art has no solid tiles."""
        tags = ArtTags(object_type=ObjectType.DECORATION)
        art = StaticArt(
            name="Passable",
            tiles=[["#", "#"], ["#", "#"]],
            tags=tags,
            blocks_movement=False
        )
        assert art.is_solid_at(0, 0) is False
        assert art.is_solid_at(1, 1) is False

    def test_get_world_bounds(self, static_tree):
        """Can get world-space bounds."""
        bounds = static_tree.get_world_bounds(10, 10)
        # anchor_point is (0, 0) by default
        assert bounds == (10, 10, 14, 12)  # width=5, height=3

    def test_get_world_bounds_with_anchor(self):
        """Anchor point affects bounds."""
        tags = ArtTags(object_type=ObjectType.OTHER)
        art = StaticArt(
            name="Anchored",
            tiles=[["#", "#", "#"], ["#", "#", "#"]],
            tags=tags,
            anchor_point=(1, 1)
        )
        bounds = art.get_world_bounds(10, 10)
        assert bounds == (9, 9, 11, 10)  # Offset by anchor

    def test_get_tiles_covered(self, static_tree):
        """Can get list of covered tiles."""
        covered = static_tree.get_tiles_covered(0, 0)
        # Should include non-space positions
        assert (2, 0) in covered  # ^
        assert (1, 1) in covered  # /
        assert (2, 1) in covered  # |
        assert (3, 1) in covered  # \
        assert (2, 2) in covered  # |
        # Should not include space positions
        assert (0, 0) not in covered

    def test_can_place_at(self, static_tree):
        """Can check placement validity."""
        occupied = set()
        assert static_tree.can_place_at(0, 0, occupied) is True

        # Occupy a tile the tree would cover
        occupied.add((2, 0))
        assert static_tree.can_place_at(0, 0, occupied) is False

    def test_add_remove_variant(self, static_tree):
        """Can manage variant IDs."""
        static_tree.add_variant("variant1")
        assert "variant1" in static_tree.variants

        static_tree.add_variant("variant1")  # Duplicate
        assert static_tree.variants.count("variant1") == 1

        assert static_tree.remove_variant("variant1") is True
        assert "variant1" not in static_tree.variants
        assert static_tree.remove_variant("variant1") is False

    def test_serialization(self, static_tree):
        """Static art can be serialized and deserialized."""
        data = static_tree.to_dict()
        restored = StaticArt.from_dict(data)

        assert restored.id == static_tree.id
        assert restored.name == static_tree.name
        assert restored.render_layer == static_tree.render_layer
        assert restored.blocks_movement == static_tree.blocks_movement
        assert restored.provides_cover == static_tree.provides_cover
        assert restored.collision_mask == static_tree.collision_mask

    def test_from_string(self):
        """Can create static art from string."""
        art_string = "###\n# #\n###"
        tags = ArtTags(object_type=ObjectType.STRUCTURE)
        art = StaticArt.from_string(
            "Wall",
            art_string,
            tags,
            blocks_movement=True,
            render_layer=RenderLayer.STRUCTURE
        )

        assert art.name == "Wall"
        assert art.blocks_movement is True
        assert art.render_layer == RenderLayer.STRUCTURE

    def test_copy(self, static_tree):
        """Static art can be copied."""
        copy = static_tree.copy()

        assert copy.id != static_tree.id
        assert copy.name == "Pine Tree (copy)"
        assert copy.render_layer == static_tree.render_layer
        assert copy.blocks_movement == static_tree.blocks_movement
        assert copy.tiles is not static_tree.tiles


class TestStaticArtTemplates:
    """Tests for predefined templates."""

    def test_templates_exist(self):
        """Predefined templates exist."""
        expected = ["small_tree", "large_rock", "bush", "grass_patch", "wooden_fence"]
        for name in expected:
            assert name in STATIC_ART_TEMPLATES

    def test_create_from_template(self):
        """Can create art from template."""
        tree = create_from_template("small_tree", "player1")

        assert tree is not None
        assert tree.name == "Small Tree"
        assert tree.tags.object_type == ObjectType.TREE
        assert tree.player_id == "player1"
        assert tree.blocks_movement is True

    def test_create_from_invalid_template(self):
        """Invalid template returns None."""
        result = create_from_template("nonexistent", "player1")
        assert result is None

    def test_rock_template(self):
        """Rock template has correct properties."""
        rock = create_from_template("large_rock")

        assert rock is not None
        assert rock.tags.object_type == ObjectType.ROCK
        assert rock.blocks_movement is True
        assert rock.blocks_vision is True
        assert rock.provides_cover == 0.8

    def test_grass_template(self):
        """Grass template is passable."""
        grass = create_from_template("grass_patch")

        assert grass is not None
        assert grass.tags.object_type == ObjectType.TERRAIN
        assert grass.render_layer == RenderLayer.GROUND
        assert grass.blocks_movement is False
