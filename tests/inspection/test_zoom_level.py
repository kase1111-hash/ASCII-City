"""Tests for ZoomLevel and related types."""

import pytest
from src.shadowengine.inspection.zoom_level import (
    ZoomLevel, ZoomDirection, ZoomConstraints,
    DEFAULT_CONSTRAINTS, get_default_constraints
)


class TestZoomLevel:
    """Tests for ZoomLevel enum."""

    def test_zoom_level_values(self):
        """Test zoom level numeric values."""
        assert ZoomLevel.COARSE.value == 1
        assert ZoomLevel.MEDIUM.value == 2
        assert ZoomLevel.CLOSE.value == 3
        assert ZoomLevel.FINE.value == 4

    def test_zoom_level_descriptions(self):
        """Test zoom level descriptions."""
        assert "overview" in ZoomLevel.COARSE.description
        assert "detailed" in ZoomLevel.MEDIUM.description
        assert "close" in ZoomLevel.CLOSE.description
        assert "magnified" in ZoomLevel.FINE.description

    def test_viewing_descriptions(self):
        """Test viewing descriptions explain what can be seen."""
        assert "shapes" in ZoomLevel.COARSE.viewing_description
        assert "textures" in ZoomLevel.MEDIUM.viewing_description
        assert "woodgrain" in ZoomLevel.CLOSE.viewing_description
        assert "fibers" in ZoomLevel.FINE.viewing_description

    def test_detail_multiplier(self):
        """Test detail multipliers increase with zoom."""
        assert ZoomLevel.COARSE.detail_multiplier < ZoomLevel.MEDIUM.detail_multiplier
        assert ZoomLevel.MEDIUM.detail_multiplier < ZoomLevel.CLOSE.detail_multiplier
        assert ZoomLevel.CLOSE.detail_multiplier < ZoomLevel.FINE.detail_multiplier

    def test_can_zoom_in(self):
        """Test can_zoom_in at each level."""
        assert ZoomLevel.COARSE.can_zoom_in() is True
        assert ZoomLevel.MEDIUM.can_zoom_in() is True
        assert ZoomLevel.CLOSE.can_zoom_in() is True
        assert ZoomLevel.FINE.can_zoom_in() is False

    def test_can_zoom_out(self):
        """Test can_zoom_out at each level."""
        assert ZoomLevel.COARSE.can_zoom_out() is False
        assert ZoomLevel.MEDIUM.can_zoom_out() is True
        assert ZoomLevel.CLOSE.can_zoom_out() is True
        assert ZoomLevel.FINE.can_zoom_out() is True

    def test_zoom_in(self):
        """Test zoom_in transitions."""
        assert ZoomLevel.COARSE.zoom_in() == ZoomLevel.MEDIUM
        assert ZoomLevel.MEDIUM.zoom_in() == ZoomLevel.CLOSE
        assert ZoomLevel.CLOSE.zoom_in() == ZoomLevel.FINE
        assert ZoomLevel.FINE.zoom_in() == ZoomLevel.FINE

    def test_zoom_out(self):
        """Test zoom_out transitions."""
        assert ZoomLevel.COARSE.zoom_out() == ZoomLevel.COARSE
        assert ZoomLevel.MEDIUM.zoom_out() == ZoomLevel.COARSE
        assert ZoomLevel.CLOSE.zoom_out() == ZoomLevel.MEDIUM
        assert ZoomLevel.FINE.zoom_out() == ZoomLevel.CLOSE

    def test_from_string(self):
        """Test parsing zoom level from string."""
        assert ZoomLevel.from_string("coarse") == ZoomLevel.COARSE
        assert ZoomLevel.from_string("overview") == ZoomLevel.COARSE
        assert ZoomLevel.from_string("far") == ZoomLevel.COARSE
        assert ZoomLevel.from_string("medium") == ZoomLevel.MEDIUM
        assert ZoomLevel.from_string("detailed") == ZoomLevel.MEDIUM
        assert ZoomLevel.from_string("normal") == ZoomLevel.MEDIUM
        assert ZoomLevel.from_string("close") == ZoomLevel.CLOSE
        assert ZoomLevel.from_string("near") == ZoomLevel.CLOSE
        assert ZoomLevel.from_string("woodgrain") == ZoomLevel.CLOSE
        assert ZoomLevel.from_string("fine") == ZoomLevel.FINE
        assert ZoomLevel.from_string("magnified") == ZoomLevel.FINE
        assert ZoomLevel.from_string("fibers") == ZoomLevel.FINE
        assert ZoomLevel.from_string("unknown") is None

    def test_serialization(self):
        """Test to_dict/from_dict."""
        for level in ZoomLevel:
            data = level.to_dict()
            restored = ZoomLevel.from_dict(data)
            assert restored == level


class TestZoomDirection:
    """Tests for ZoomDirection enum."""

    def test_directions(self):
        """Test direction values exist."""
        assert ZoomDirection.IN is not None
        assert ZoomDirection.OUT is not None
        assert ZoomDirection.RESET is not None


class TestZoomConstraints:
    """Tests for ZoomConstraints."""

    def test_default_constraints(self):
        """Test default constraint values - FINE requires tool by default."""
        c = ZoomConstraints()
        assert c.min_level == ZoomLevel.COARSE
        assert c.max_level == ZoomLevel.FINE
        assert c.requires_tool_for_fine is True  # Default is now True
        assert c.max_unaided_level == ZoomLevel.CLOSE

    def test_level_accessibility_default(self):
        """Test level accessibility with default constraints (tool required for FINE)."""
        c = ZoomConstraints()
        assert c.is_level_accessible(ZoomLevel.COARSE) is True
        assert c.is_level_accessible(ZoomLevel.MEDIUM) is True
        assert c.is_level_accessible(ZoomLevel.CLOSE) is True
        # FINE requires tool by default
        assert c.is_level_accessible(ZoomLevel.FINE, has_required_tool=False) is False
        assert c.is_level_accessible(ZoomLevel.FINE, has_required_tool=True) is True

    def test_level_accessibility_no_tool_required(self):
        """Test level accessibility when no tool is required."""
        c = ZoomConstraints(requires_tool_for_fine=False)
        assert c.is_level_accessible(ZoomLevel.COARSE) is True
        assert c.is_level_accessible(ZoomLevel.MEDIUM) is True
        assert c.is_level_accessible(ZoomLevel.CLOSE) is True
        assert c.is_level_accessible(ZoomLevel.FINE) is True

    def test_level_accessibility_with_tool_requirement(self):
        """Test level accessibility when tool is required."""
        c = ZoomConstraints(
            requires_tool_for_fine=True,
            required_tool_type="magnifying_glass"
        )
        assert c.is_level_accessible(ZoomLevel.COARSE) is True
        assert c.is_level_accessible(ZoomLevel.MEDIUM) is True
        assert c.is_level_accessible(ZoomLevel.CLOSE) is True
        assert c.is_level_accessible(ZoomLevel.FINE, has_required_tool=False) is False
        assert c.is_level_accessible(ZoomLevel.FINE, has_required_tool=True) is True

    def test_max_accessible_level(self):
        """Test get_max_accessible_level - CLOSE without tool, FINE with tool."""
        c = ZoomConstraints(requires_tool_for_fine=True)
        assert c.get_max_accessible_level(has_required_tool=False) == ZoomLevel.CLOSE
        assert c.get_max_accessible_level(has_required_tool=True) == ZoomLevel.FINE

    def test_limited_max_level(self):
        """Test constraints with limited max level."""
        c = ZoomConstraints(max_level=ZoomLevel.MEDIUM, requires_tool_for_fine=False)
        assert c.is_level_accessible(ZoomLevel.CLOSE) is False
        assert c.is_level_accessible(ZoomLevel.FINE) is False
        assert c.get_max_accessible_level() == ZoomLevel.MEDIUM

    def test_serialization(self):
        """Test to_dict/from_dict."""
        c = ZoomConstraints(
            min_level=ZoomLevel.COARSE,
            max_level=ZoomLevel.FINE,
            requires_tool_for_fine=True,
            required_tool_type="telescope",
            max_unaided_level=ZoomLevel.CLOSE
        )
        data = c.to_dict()
        restored = ZoomConstraints.from_dict(data)
        assert restored.requires_tool_for_fine == c.requires_tool_for_fine
        assert restored.required_tool_type == c.required_tool_type
        assert restored.max_unaided_level == c.max_unaided_level


class TestDefaultConstraints:
    """Tests for default constraint presets."""

    def test_standard_constraints(self):
        """Test standard constraints - can reach CLOSE unaided, FINE needs tool."""
        c = get_default_constraints("standard")
        assert c.max_level == ZoomLevel.FINE
        assert c.requires_tool_for_fine is True
        assert c.max_unaided_level == ZoomLevel.CLOSE
        assert c.required_tool_type == "magnifying_glass"

    def test_small_constraints(self):
        """Test small object constraints."""
        c = get_default_constraints("small")
        assert c.requires_tool_for_fine is True
        assert c.required_tool_type == "magnifying_glass"
        assert c.max_unaided_level == ZoomLevel.CLOSE

    def test_distant_constraints(self):
        """Test distant object constraints."""
        c = get_default_constraints("distant")
        assert c.max_level == ZoomLevel.MEDIUM

    def test_distant_with_telescope_constraints(self):
        """Test distant with telescope constraints."""
        c = get_default_constraints("distant_with_telescope")
        assert c.max_level == ZoomLevel.CLOSE
        assert c.required_tool_type == "telescope"
        assert c.max_unaided_level == ZoomLevel.COARSE

    def test_detailed_surface_constraints(self):
        """Test detailed surface - can see woodgrain without tools."""
        c = get_default_constraints("detailed_surface")
        assert c.max_level == ZoomLevel.CLOSE
        assert c.requires_tool_for_fine is False

    def test_unknown_category(self):
        """Test unknown category returns standard (with tool requirement)."""
        c = get_default_constraints("unknown_category")
        assert c.max_level == ZoomLevel.FINE
        assert c.requires_tool_for_fine is True
