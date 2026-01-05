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
        assert ZoomLevel.FINE.value == 3

    def test_zoom_level_descriptions(self):
        """Test zoom level descriptions."""
        assert "overview" in ZoomLevel.COARSE.description
        assert "detailed" in ZoomLevel.MEDIUM.description
        assert "close" in ZoomLevel.FINE.description

    def test_detail_multiplier(self):
        """Test detail multipliers increase with zoom."""
        assert ZoomLevel.COARSE.detail_multiplier < ZoomLevel.MEDIUM.detail_multiplier
        assert ZoomLevel.MEDIUM.detail_multiplier < ZoomLevel.FINE.detail_multiplier

    def test_can_zoom_in(self):
        """Test can_zoom_in at each level."""
        assert ZoomLevel.COARSE.can_zoom_in() is True
        assert ZoomLevel.MEDIUM.can_zoom_in() is True
        assert ZoomLevel.FINE.can_zoom_in() is False

    def test_can_zoom_out(self):
        """Test can_zoom_out at each level."""
        assert ZoomLevel.COARSE.can_zoom_out() is False
        assert ZoomLevel.MEDIUM.can_zoom_out() is True
        assert ZoomLevel.FINE.can_zoom_out() is True

    def test_zoom_in(self):
        """Test zoom_in transitions."""
        assert ZoomLevel.COARSE.zoom_in() == ZoomLevel.MEDIUM
        assert ZoomLevel.MEDIUM.zoom_in() == ZoomLevel.FINE
        assert ZoomLevel.FINE.zoom_in() == ZoomLevel.FINE

    def test_zoom_out(self):
        """Test zoom_out transitions."""
        assert ZoomLevel.COARSE.zoom_out() == ZoomLevel.COARSE
        assert ZoomLevel.MEDIUM.zoom_out() == ZoomLevel.COARSE
        assert ZoomLevel.FINE.zoom_out() == ZoomLevel.MEDIUM

    def test_from_string(self):
        """Test parsing zoom level from string."""
        assert ZoomLevel.from_string("coarse") == ZoomLevel.COARSE
        assert ZoomLevel.from_string("overview") == ZoomLevel.COARSE
        assert ZoomLevel.from_string("medium") == ZoomLevel.MEDIUM
        assert ZoomLevel.from_string("detailed") == ZoomLevel.MEDIUM
        assert ZoomLevel.from_string("fine") == ZoomLevel.FINE
        assert ZoomLevel.from_string("close") == ZoomLevel.FINE
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
        """Test default constraint values."""
        c = ZoomConstraints()
        assert c.min_level == ZoomLevel.COARSE
        assert c.max_level == ZoomLevel.FINE
        assert c.requires_tool_for_fine is False

    def test_level_accessibility_default(self):
        """Test level accessibility with default constraints."""
        c = ZoomConstraints()
        assert c.is_level_accessible(ZoomLevel.COARSE) is True
        assert c.is_level_accessible(ZoomLevel.MEDIUM) is True
        assert c.is_level_accessible(ZoomLevel.FINE) is True

    def test_level_accessibility_with_tool_requirement(self):
        """Test level accessibility when tool is required."""
        c = ZoomConstraints(
            requires_tool_for_fine=True,
            required_tool_type="magnifying_glass"
        )
        assert c.is_level_accessible(ZoomLevel.COARSE) is True
        assert c.is_level_accessible(ZoomLevel.MEDIUM) is True
        assert c.is_level_accessible(ZoomLevel.FINE, has_required_tool=False) is False
        assert c.is_level_accessible(ZoomLevel.FINE, has_required_tool=True) is True

    def test_max_accessible_level(self):
        """Test get_max_accessible_level."""
        c = ZoomConstraints(requires_tool_for_fine=True)
        assert c.get_max_accessible_level(has_required_tool=False) == ZoomLevel.MEDIUM
        assert c.get_max_accessible_level(has_required_tool=True) == ZoomLevel.FINE

    def test_limited_max_level(self):
        """Test constraints with limited max level."""
        c = ZoomConstraints(max_level=ZoomLevel.MEDIUM)
        assert c.is_level_accessible(ZoomLevel.FINE) is False
        assert c.get_max_accessible_level() == ZoomLevel.MEDIUM

    def test_serialization(self):
        """Test to_dict/from_dict."""
        c = ZoomConstraints(
            min_level=ZoomLevel.COARSE,
            max_level=ZoomLevel.FINE,
            requires_tool_for_fine=True,
            required_tool_type="telescope"
        )
        data = c.to_dict()
        restored = ZoomConstraints.from_dict(data)
        assert restored.requires_tool_for_fine == c.requires_tool_for_fine
        assert restored.required_tool_type == c.required_tool_type


class TestDefaultConstraints:
    """Tests for default constraint presets."""

    def test_standard_constraints(self):
        """Test standard constraints preset."""
        c = get_default_constraints("standard")
        assert c.max_level == ZoomLevel.FINE
        assert c.requires_tool_for_fine is False

    def test_small_constraints(self):
        """Test small object constraints."""
        c = get_default_constraints("small")
        assert c.requires_tool_for_fine is True
        assert c.required_tool_type == "magnifying_glass"

    def test_distant_constraints(self):
        """Test distant object constraints."""
        c = get_default_constraints("distant")
        assert c.max_level == ZoomLevel.MEDIUM

    def test_unknown_category(self):
        """Test unknown category returns default."""
        c = get_default_constraints("unknown_category")
        assert c.max_level == ZoomLevel.FINE
