"""
Tests for the ASCIIArt base class.
"""

import pytest
from datetime import datetime
from src.shadowengine.studio.art import ASCIIArt, ArtCategory
from src.shadowengine.studio.tags import ArtTags, ObjectType


class TestASCIIArt:
    """Tests for ASCIIArt class."""

    def test_create_art(self, basic_art):
        """Can create ASCII art."""
        assert basic_art.name == "Test Art"
        assert basic_art.category == ArtCategory.STATIC
        assert basic_art.width == 3
        assert basic_art.height == 3

    def test_dimensions(self, tree_art):
        """Art reports correct dimensions."""
        assert tree_art.width == 5
        assert tree_art.height == 3
        assert tree_art.dimensions == (5, 3)

    def test_get_tile(self, basic_art):
        """Can get tiles by position."""
        assert basic_art.get_tile(0, 0) == "#"
        assert basic_art.get_tile(1, 1) == " "
        assert basic_art.get_tile(2, 2) == "#"

    def test_get_tile_out_of_bounds(self, basic_art):
        """Out of bounds returns space."""
        assert basic_art.get_tile(-1, 0) == " "
        assert basic_art.get_tile(10, 10) == " "

    def test_set_tile(self, basic_art):
        """Can set tiles."""
        basic_art.set_tile(1, 1, "X")
        assert basic_art.get_tile(1, 1) == "X"

    def test_set_tile_invalid_char(self, basic_art):
        """Setting invalid character fails."""
        assert not basic_art.set_tile(1, 1, "")
        assert not basic_art.set_tile(1, 1, "AB")

    def test_set_tile_expands_grid(self, basic_art):
        """Setting tile can expand grid."""
        basic_art.set_tile(5, 5, "X")
        assert basic_art.get_tile(5, 5) == "X"
        assert basic_art.height >= 6
        assert basic_art.width >= 6

    def test_render(self, basic_art):
        """Art can be rendered to string."""
        rendered = basic_art.render()
        lines = rendered.split("\n")
        assert len(lines) == 3
        assert lines[0] == "###"
        assert lines[1] == "# #"
        assert lines[2] == "###"

    def test_render_tiles(self, basic_art):
        """Art can be rendered as tile list."""
        tiles = basic_art.render_tiles()
        assert len(tiles) == 3
        assert tiles[0] == "###"
        assert tiles[1] == "# #"

    def test_normalize(self):
        """Normalize makes all rows same width."""
        tags = ArtTags(object_type=ObjectType.OTHER)
        art = ASCIIArt(
            name="Uneven",
            tiles=[["#", "#", "#"], ["#"], ["#", "#"]],
            tags=tags
        )
        art.normalize()
        assert all(len(row) == 3 for row in art.tiles)

    def test_trim(self):
        """Trim removes empty edges."""
        tags = ArtTags(object_type=ObjectType.OTHER)
        art = ASCIIArt(
            name="Padded",
            tiles=[
                [" ", " ", " ", " "],
                [" ", "#", "#", " "],
                [" ", "#", "#", " "],
                [" ", " ", " ", " "]
            ],
            tags=tags
        )
        art.trim()
        assert art.width == 2
        assert art.height == 2
        assert art.get_tile(0, 0) == "#"

    def test_trim_empty_art(self):
        """Trimming empty art leaves single space."""
        tags = ArtTags(object_type=ObjectType.OTHER)
        art = ASCIIArt(
            name="Empty",
            tiles=[[" ", " "], [" ", " "]],
            tags=tags
        )
        art.trim()
        assert art.tiles == [[" "]]

    def test_copy(self, basic_art):
        """Art can be copied."""
        copy = basic_art.copy()
        assert copy.id != basic_art.id
        assert copy.name == "Test Art (copy)"
        assert copy.tiles == basic_art.tiles
        assert copy.imported_from == basic_art.id

        # Modifying copy doesn't affect original
        copy.set_tile(1, 1, "X")
        assert basic_art.get_tile(1, 1) == " "

    def test_create_variant(self, basic_art):
        """Can create variants."""
        variant_tiles = [["*", "*", "*"], ["*", " ", "*"], ["*", "*", "*"]]
        variant = basic_art.create_variant(variant_tiles, 2)

        assert variant.name == "Test Art v2"
        assert variant.version == 2
        assert variant.tiles == variant_tiles
        assert variant.imported_from == basic_art.id

    def test_serialization(self, tree_art):
        """Art can be serialized and deserialized."""
        data = tree_art.to_dict()
        restored = ASCIIArt.from_dict(data)

        assert restored.id == tree_art.id
        assert restored.name == tree_art.name
        assert restored.tiles == tree_art.tiles
        assert restored.tags.object_type == tree_art.tags.object_type
        assert restored.description == tree_art.description

    def test_from_string(self):
        """Can create art from string."""
        art_string = "###\n# #\n###"
        tags = ArtTags(object_type=ObjectType.STRUCTURE)
        art = ASCIIArt.from_string("Box", art_string, tags)

        assert art.name == "Box"
        assert art.width == 3
        assert art.height == 3
        assert art.get_tile(1, 1) == " "

    def test_create_blank(self):
        """Can create blank canvas."""
        tags = ArtTags(object_type=ObjectType.OTHER)
        art = ASCIIArt.create_blank("Canvas", 10, 5, tags)

        assert art.name == "Canvas"
        assert art.width == 10
        assert art.height == 5
        assert all(c == " " for row in art.tiles for c in row)

    def test_equality_by_id(self, basic_art):
        """Equality is based on ID."""
        copy = basic_art.copy()
        assert basic_art != copy

        # Same ID = equal
        same = ASCIIArt(
            id=basic_art.id,
            name="Different Name",
            tiles=[["X"]],
            tags=ArtTags(object_type=ObjectType.OTHER)
        )
        assert basic_art == same

    def test_hash(self, basic_art):
        """Art can be hashed."""
        art_set = {basic_art}
        assert basic_art in art_set

    def test_repr(self, basic_art):
        """Art has readable repr."""
        repr_str = repr(basic_art)
        assert "Test Art" in repr_str
        assert "3x3" in repr_str

    def test_metadata_tracking(self, basic_art):
        """Timestamps are tracked."""
        original_updated = basic_art.updated_at
        basic_art.set_tile(0, 0, "X")
        assert basic_art.updated_at >= original_updated

    def test_player_id(self, basic_art):
        """Player ID is tracked."""
        assert basic_art.player_id == "system"  # Default
        basic_art.player_id = "player123"
        assert basic_art.player_id == "player123"

    def test_empty_tiles_raises(self):
        """Empty tiles raises error."""
        tags = ArtTags(object_type=ObjectType.OTHER)
        with pytest.raises(ValueError):
            ASCIIArt(name="Empty", tiles=[], tags=tags)

    def test_invalid_tiles_raises(self):
        """Invalid tile structure raises error."""
        tags = ArtTags(object_type=ObjectType.OTHER)
        with pytest.raises(ValueError):
            ASCIIArt(name="Bad", tiles=["not", "a", "list"], tags=tags)


class TestArtCategory:
    """Tests for ArtCategory enum."""

    def test_categories_exist(self):
        """Both categories exist."""
        assert ArtCategory.STATIC is not None
        assert ArtCategory.DYNAMIC is not None

    def test_default_is_static(self, basic_art):
        """Default category is STATIC."""
        assert basic_art.category == ArtCategory.STATIC
