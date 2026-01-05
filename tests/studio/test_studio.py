"""
Tests for Studio interface.
"""

import pytest
from src.shadowengine.studio.studio import (
    Studio, StudioMode, Tool, Selection
)
from src.shadowengine.studio.art import ArtCategory
from src.shadowengine.studio.static_art import StaticArt
from src.shadowengine.studio.entity import DynamicEntity
from src.shadowengine.studio.tags import ObjectType, InteractionType, EnvironmentType


class TestStudioMode:
    """Tests for StudioMode enum."""

    def test_modes_exist(self):
        """All modes exist."""
        expected = ["DRAW", "TAG", "ANIMATE", "PERSONALITY", "PREVIEW", "EXPORT"]
        for name in expected:
            assert hasattr(StudioMode, name)


class TestTool:
    """Tests for Tool enum."""

    def test_tools_exist(self):
        """All tools exist."""
        expected = [
            "PENCIL", "LINE", "RECTANGLE", "FILL",
            "ERASER", "SELECT", "MOVE", "COPY", "PASTE"
        ]
        for name in expected:
            assert hasattr(Tool, name)


class TestSelection:
    """Tests for Selection class."""

    def test_create_selection(self):
        """Can create selection."""
        selection = Selection(x=5, y=5, width=10, height=10)
        assert selection.x == 5
        assert selection.width == 10

    def test_contains(self):
        """Can check if point in selection."""
        selection = Selection(x=5, y=5, width=10, height=10)

        assert selection.contains(5, 5) is True
        assert selection.contains(14, 14) is True
        assert selection.contains(4, 5) is False
        assert selection.contains(15, 5) is False

    def test_get_bounds(self):
        """Can get bounds."""
        selection = Selection(x=5, y=5, width=10, height=10)
        bounds = selection.get_bounds()

        assert bounds == (5, 5, 10, 10)


class TestStudio:
    """Tests for Studio class."""

    def test_create_studio(self, empty_studio):
        """Can create studio."""
        assert empty_studio.player_id == "test_player"
        assert empty_studio.mode == StudioMode.DRAW
        assert empty_studio.tool == Tool.PENCIL
        assert empty_studio.current_art is None

    def test_set_mode(self, empty_studio):
        """Can change mode."""
        empty_studio.set_mode(StudioMode.TAG)
        assert empty_studio.mode == StudioMode.TAG

    def test_set_tool(self, empty_studio):
        """Can change tool."""
        empty_studio.set_tool(Tool.LINE)
        assert empty_studio.tool == Tool.LINE

    def test_set_char(self, empty_studio):
        """Can set drawing character."""
        empty_studio.set_char("*")
        assert empty_studio._current_char == "*"

        # Invalid character ignored
        empty_studio.set_char("")
        assert empty_studio._current_char == "*"

    # === Canvas Operations ===

    def test_new_canvas(self, empty_studio):
        """Can create new canvas."""
        art = empty_studio.new_canvas(20, 10, "Test Canvas")

        assert art is not None
        assert art.name == "Test Canvas"
        assert art.width == 20
        assert art.height == 10
        assert empty_studio.current_art == art

    def test_load_art(self, empty_studio, basic_art):
        """Can load existing art."""
        empty_studio.load_art(basic_art)

        assert empty_studio.current_art == basic_art
        assert empty_studio._canvas_width == basic_art.width
        assert empty_studio._canvas_height == basic_art.height

    def test_load_from_string(self, empty_studio):
        """Can load art from string."""
        art = empty_studio.load_from_string("Box", "###\n# #\n###")

        assert art.name == "Box"
        assert art.width == 3
        assert art.height == 3

    def test_load_template(self, empty_studio):
        """Can load template."""
        art = empty_studio.load_template("small_tree")

        assert art is not None
        assert art.tags.object_type == ObjectType.TREE

    def test_load_invalid_template(self, empty_studio):
        """Invalid template returns None."""
        art = empty_studio.load_template("nonexistent")
        assert art is None

    def test_resize_canvas(self, studio_with_canvas):
        """Can resize canvas."""
        studio_with_canvas.resize_canvas(30, 15)

        assert studio_with_canvas._canvas_width == 30
        assert studio_with_canvas._canvas_height == 15
        assert studio_with_canvas.current_art.height == 15

    # === Drawing Operations ===

    def test_move_cursor(self, studio_with_canvas):
        """Can move cursor."""
        pos = studio_with_canvas.move_cursor(5, 3)

        assert pos == (5, 3)
        assert studio_with_canvas.cursor_position == (5, 3)

    def test_move_cursor_clamped(self, studio_with_canvas):
        """Cursor is clamped to canvas."""
        studio_with_canvas.move_cursor(100, 100)

        assert studio_with_canvas._cursor_x == 19  # Max for 20-wide canvas
        assert studio_with_canvas._cursor_y == 9   # Max for 10-high canvas

    def test_set_cursor(self, studio_with_canvas):
        """Can set cursor directly."""
        pos = studio_with_canvas.set_cursor(10, 5)
        assert pos == (10, 5)

    def test_draw_at_cursor(self, studio_with_canvas):
        """Can draw at cursor."""
        studio_with_canvas.set_cursor(5, 5)
        studio_with_canvas.draw_at_cursor("X")

        assert studio_with_canvas.current_art.get_tile(5, 5) == "X"

    def test_draw_at(self, studio_with_canvas):
        """Can draw at specific position."""
        studio_with_canvas.draw_at(3, 3, "O")

        assert studio_with_canvas.current_art.get_tile(3, 3) == "O"

    def test_draw_line(self, studio_with_canvas):
        """Can draw line."""
        studio_with_canvas.draw_line(0, 0, 5, 0, "-")

        for x in range(6):
            assert studio_with_canvas.current_art.get_tile(x, 0) == "-"

    def test_draw_rectangle(self, studio_with_canvas):
        """Can draw rectangle."""
        studio_with_canvas.draw_rectangle(2, 2, 5, 3, "#")

        # Check corners
        assert studio_with_canvas.current_art.get_tile(2, 2) == "#"
        assert studio_with_canvas.current_art.get_tile(6, 2) == "#"
        assert studio_with_canvas.current_art.get_tile(2, 4) == "#"
        assert studio_with_canvas.current_art.get_tile(6, 4) == "#"

    def test_draw_rectangle_filled(self, studio_with_canvas):
        """Can draw filled rectangle."""
        studio_with_canvas.draw_rectangle(2, 2, 3, 3, "#", filled=True)

        for y in range(2, 5):
            for x in range(2, 5):
                assert studio_with_canvas.current_art.get_tile(x, y) == "#"

    def test_flood_fill(self, studio_with_canvas):
        """Can flood fill."""
        filled = studio_with_canvas.flood_fill(0, 0, ".")

        assert filled > 0
        assert studio_with_canvas.current_art.get_tile(0, 0) == "."

    def test_flood_fill_same_char(self, studio_with_canvas):
        """Flood fill with same character does nothing."""
        studio_with_canvas.draw_at(0, 0, " ")
        filled = studio_with_canvas.flood_fill(0, 0, " ")

        assert filled == 0

    def test_erase_at(self, studio_with_canvas):
        """Can erase at position."""
        studio_with_canvas.draw_at(5, 5, "X")
        studio_with_canvas.erase_at(5, 5)

        assert studio_with_canvas.current_art.get_tile(5, 5) == " "

    # === Selection Operations ===

    def test_select_region(self, studio_with_canvas):
        """Can select region."""
        studio_with_canvas.draw_at(5, 5, "X")
        selection = studio_with_canvas.select_region(4, 4, 3, 3)

        assert selection.x == 4
        assert selection.width == 3
        assert selection.content is not None

    def test_clear_selection(self, studio_with_canvas):
        """Can clear selection."""
        studio_with_canvas.select_region(0, 0, 5, 5)
        studio_with_canvas.clear_selection()

        assert studio_with_canvas._selection is None

    def test_copy_selection(self, studio_with_canvas):
        """Can copy selection."""
        studio_with_canvas.draw_at(5, 5, "X")
        studio_with_canvas.select_region(5, 5, 1, 1)

        result = studio_with_canvas.copy_selection()

        assert result is True
        assert studio_with_canvas._clipboard is not None

    def test_copy_no_selection(self, studio_with_canvas):
        """Copy without selection fails."""
        result = studio_with_canvas.copy_selection()
        assert result is False

    def test_cut_selection(self, studio_with_canvas):
        """Can cut selection."""
        studio_with_canvas.draw_at(5, 5, "X")
        studio_with_canvas.select_region(5, 5, 1, 1)

        result = studio_with_canvas.cut_selection()

        assert result is True
        assert studio_with_canvas.current_art.get_tile(5, 5) == " "

    def test_paste(self, studio_with_canvas):
        """Can paste clipboard."""
        studio_with_canvas.draw_at(5, 5, "X")
        studio_with_canvas.select_region(5, 5, 1, 1)
        studio_with_canvas.copy_selection()

        result = studio_with_canvas.paste(10, 10)

        assert result is True
        assert studio_with_canvas.current_art.get_tile(10, 10) == "X"

    def test_paste_no_clipboard(self, studio_with_canvas):
        """Paste without clipboard fails."""
        result = studio_with_canvas.paste()
        assert result is False

    # === History Operations ===

    def test_undo(self, studio_with_canvas):
        """Can undo changes."""
        original = studio_with_canvas.current_art.get_tile(5, 5)
        studio_with_canvas.draw_rectangle(5, 5, 3, 3, "#")

        result = studio_with_canvas.undo()

        assert result is True
        assert studio_with_canvas.current_art.get_tile(5, 5) == original

    def test_redo(self, studio_with_canvas):
        """Can redo changes."""
        studio_with_canvas.draw_rectangle(5, 5, 3, 3, "#")
        studio_with_canvas.undo()

        result = studio_with_canvas.redo()

        assert result is True
        assert studio_with_canvas.current_art.get_tile(5, 5) == "#"

    def test_can_undo_redo(self, studio_with_canvas):
        """Can check undo/redo availability."""
        assert studio_with_canvas.can_undo() is False  # Just created

        studio_with_canvas.draw_rectangle(0, 0, 3, 3, "#")
        assert studio_with_canvas.can_undo() is True
        assert studio_with_canvas.can_redo() is False

        studio_with_canvas.undo()
        assert studio_with_canvas.can_redo() is True

    # === Tagging Operations ===

    def test_set_object_type(self, studio_with_canvas):
        """Can set object type."""
        studio_with_canvas.set_object_type(ObjectType.TREE)

        assert studio_with_canvas.current_art.tags.object_type == ObjectType.TREE

    def test_add_interaction(self, studio_with_canvas):
        """Can add interaction type."""
        studio_with_canvas.add_interaction(InteractionType.CLIMBABLE)

        assert InteractionType.CLIMBABLE in studio_with_canvas.current_art.tags.interaction_types

    def test_remove_interaction(self, studio_with_canvas):
        """Can remove interaction type."""
        studio_with_canvas.add_interaction(InteractionType.CLIMBABLE)
        studio_with_canvas.remove_interaction(InteractionType.CLIMBABLE)

        assert InteractionType.CLIMBABLE not in studio_with_canvas.current_art.tags.interaction_types

    def test_add_environment(self, studio_with_canvas):
        """Can add environment type."""
        studio_with_canvas.add_environment(EnvironmentType.FOREST)

        assert EnvironmentType.FOREST in studio_with_canvas.current_art.tags.environment_types

    def test_add_custom_tag(self, studio_with_canvas):
        """Can add custom tag."""
        studio_with_canvas.add_custom_tag("custom")

        assert "custom" in studio_with_canvas.current_art.tags.custom_tags

    # === Conversion Operations ===

    def test_convert_to_static(self, studio_with_canvas):
        """Can convert to static art."""
        static = studio_with_canvas.convert_to_static()

        assert static is not None
        assert isinstance(static, StaticArt)
        assert static.category == ArtCategory.STATIC

    def test_convert_to_entity(self, studio_with_canvas):
        """Can convert to entity."""
        entity = studio_with_canvas.convert_to_entity("curious_neutral")

        assert entity is not None
        assert isinstance(entity, DynamicEntity)
        assert entity.category == ArtCategory.DYNAMIC

    # === Save and Export ===

    def test_save_to_pool(self, full_studio):
        """Can save to asset pool."""
        asset_id = full_studio.save_to_pool()

        assert asset_id is not None
        assert full_studio.asset_pool.get_asset(asset_id) is not None

    def test_submit_to_gallery(self, full_studio):
        """Can submit to gallery."""
        entry = full_studio.submit_to_gallery(
            title="My Art",
            description="A test",
            tags={"test"},
            creator_name="Tester"
        )

        assert entry is not None
        assert entry.title == "My Art"
        assert full_studio.gallery.count == 1

    def test_export_to_string(self, studio_with_canvas):
        """Can export as string."""
        studio_with_canvas.draw_at(0, 0, "X")
        result = studio_with_canvas.export_to_string()

        assert result is not None
        assert "X" in result

    def test_export_to_dict(self, studio_with_canvas):
        """Can export as dictionary."""
        result = studio_with_canvas.export_to_dict()

        assert result is not None
        assert "name" in result
        assert "tiles" in result

    # === Template Listing ===

    def test_list_static_templates(self):
        """Can list static templates."""
        templates = Studio.list_static_templates()
        assert "small_tree" in templates
        assert "large_rock" in templates

    def test_list_entity_templates(self):
        """Can list entity templates."""
        templates = Studio.list_entity_templates()
        assert "forest_deer" in templates
        assert "village_guard" in templates

    def test_list_personality_templates(self):
        """Can list personality templates."""
        templates = Studio.list_personality_templates()
        assert "timid_prey" in templates
        assert "territorial_predator" in templates

    # === Render ===

    def test_render_preview(self, studio_with_canvas):
        """Can render preview."""
        preview = studio_with_canvas.render_preview()

        assert preview is not None
        assert "Test Canvas" in preview
        assert "Mode:" in preview

    def test_render_preview_no_art(self, empty_studio):
        """Render without art shows message."""
        preview = empty_studio.render_preview()
        assert "no art loaded" in preview

    def test_get_status(self, studio_with_canvas):
        """Can get status."""
        status = studio_with_canvas.get_status()

        assert "mode" in status
        assert "tool" in status
        assert "cursor" in status
        assert "has_art" in status
        assert status["has_art"] is True
