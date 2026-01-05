"""Tests for InspectionTool and related types."""

import pytest
from src.shadowengine.inspection.tool import (
    InspectionTool, ToolType, ToolAffordance,
    INSPECTION_TOOLS, get_tool, get_tools_with_affordance,
    get_best_tool_for_inspection
)


class TestToolType:
    """Tests for ToolType enum."""

    def test_tool_types_exist(self):
        """Test all expected tool types exist."""
        assert ToolType.MAGNIFYING_GLASS is not None
        assert ToolType.TELESCOPE is not None
        assert ToolType.LANTERN is not None
        assert ToolType.SPECTACLES is not None
        assert ToolType.UV_LIGHT is not None
        assert ToolType.MIRROR is not None
        assert ToolType.STETHOSCOPE is not None
        assert ToolType.PROBE is not None


class TestToolAffordance:
    """Tests for ToolAffordance enum."""

    def test_affordances_exist(self):
        """Test all expected affordances exist."""
        assert ToolAffordance.MAGNIFY is not None
        assert ToolAffordance.DISTANT_VIEW is not None
        assert ToolAffordance.ILLUMINATE is not None
        assert ToolAffordance.READ_SMALL is not None
        assert ToolAffordance.REVEAL_HIDDEN is not None


class TestInspectionTool:
    """Tests for InspectionTool."""

    def test_create_tool(self):
        """Test creating an inspection tool."""
        tool = InspectionTool(
            id="test_tool",
            name="Test Tool",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="A test tool",
            affordances=[ToolAffordance.MAGNIFY],
            zoom_bonus=1
        )
        assert tool.id == "test_tool"
        assert tool.name == "Test Tool"
        assert tool.zoom_bonus == 1

    def test_can_inspect_default(self):
        """Test can_inspect with default parameters."""
        tool = InspectionTool(
            id="test",
            name="Test",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="Test"
        )
        assert tool.can_inspect() is True

    def test_can_inspect_requires_proximity(self):
        """Test can_inspect with proximity requirement."""
        tool = InspectionTool(
            id="test",
            name="Test",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="Test",
            requires_proximity=True,
            effective_range=1.0
        )
        assert tool.can_inspect(distance=0.5) is True
        assert tool.can_inspect(distance=2.0) is False

    def test_can_inspect_requires_light(self):
        """Test can_inspect with light requirement."""
        tool = InspectionTool(
            id="test",
            name="Test",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="Test",
            requires_light=True
        )
        assert tool.can_inspect(has_light=True) is True
        assert tool.can_inspect(has_light=False) is False

    def test_has_affordance(self):
        """Test has_affordance check."""
        tool = InspectionTool(
            id="test",
            name="Test",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="Test",
            affordances=[ToolAffordance.MAGNIFY, ToolAffordance.READ_SMALL]
        )
        assert tool.has_affordance(ToolAffordance.MAGNIFY) is True
        assert tool.has_affordance(ToolAffordance.READ_SMALL) is True
        assert tool.has_affordance(ToolAffordance.DISTANT_VIEW) is False

    def test_effective_zoom_bonus(self):
        """Test zoom bonus calculation based on distance."""
        tool = InspectionTool(
            id="test",
            name="Test",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="Test",
            zoom_bonus=2,
            effective_range=2.0
        )
        assert tool.get_effective_zoom_bonus(0.0) == 2
        assert tool.get_effective_zoom_bonus(1.0) > 0
        assert tool.get_effective_zoom_bonus(5.0) == 0

    def test_inspection_text(self):
        """Test getting inspection text."""
        tool = InspectionTool(
            id="test",
            name="Test Glass",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="Test",
            use_text="You peer through the {tool} at {target}..."
        )
        text = tool.get_inspection_text("the statue")
        assert "Test Glass" in text
        assert "the statue" in text

    def test_serialization(self):
        """Test to_dict/from_dict."""
        tool = InspectionTool(
            id="test",
            name="Test",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="Test",
            affordances=[ToolAffordance.MAGNIFY],
            zoom_bonus=2
        )
        data = tool.to_dict()
        restored = InspectionTool.from_dict(data)
        assert restored.id == tool.id
        assert restored.name == tool.name
        assert restored.zoom_bonus == tool.zoom_bonus
        assert ToolAffordance.MAGNIFY in restored.affordances


class TestPredefinedTools:
    """Tests for predefined inspection tools."""

    def test_magnifying_glass_exists(self):
        """Test magnifying glass tool."""
        tool = get_tool("magnifying_glass")
        assert tool is not None
        assert tool.has_affordance(ToolAffordance.MAGNIFY)
        assert tool.zoom_bonus > 0

    def test_telescope_exists(self):
        """Test telescope tool."""
        tool = get_tool("telescope")
        assert tool is not None
        assert tool.has_affordance(ToolAffordance.DISTANT_VIEW)
        assert tool.effective_range > 10

    def test_lantern_exists(self):
        """Test lantern tool."""
        tool = get_tool("lantern")
        assert tool is not None
        assert tool.has_affordance(ToolAffordance.ILLUMINATE)
        assert tool.requires_light is False  # Provides its own

    def test_uv_light_exists(self):
        """Test UV light tool."""
        tool = get_tool("uv_light")
        assert tool is not None
        assert tool.has_affordance(ToolAffordance.REVEAL_HIDDEN)

    def test_all_tools_have_ids(self):
        """Test all predefined tools have IDs."""
        for tool_id, tool in INSPECTION_TOOLS.items():
            assert tool.id == tool_id
            assert tool.name
            assert tool.description


class TestToolHelpers:
    """Tests for tool helper functions."""

    def test_get_tool(self):
        """Test get_tool function."""
        tool = get_tool("magnifying_glass")
        assert tool is not None
        assert get_tool("nonexistent") is None

    def test_get_tools_with_affordance(self):
        """Test filtering tools by affordance."""
        magnify_tools = get_tools_with_affordance(ToolAffordance.MAGNIFY)
        assert len(magnify_tools) >= 1
        for tool in magnify_tools:
            assert tool.has_affordance(ToolAffordance.MAGNIFY)

    def test_get_best_tool_basic(self):
        """Test finding best tool for inspection."""
        tools = [get_tool("magnifying_glass"), get_tool("telescope")]
        tools = [t for t in tools if t]

        best = get_best_tool_for_inspection(
            tools,
            distance=0.0,
            needs_magnification=True
        )
        assert best is not None
        assert best.has_affordance(ToolAffordance.MAGNIFY)

    def test_get_best_tool_distant(self):
        """Test finding best tool for distant object."""
        tools = [get_tool("magnifying_glass"), get_tool("telescope")]
        tools = [t for t in tools if t]

        best = get_best_tool_for_inspection(
            tools,
            distance=50.0,
            needs_distant_view=True
        )
        assert best is not None
        assert best.id == "telescope"

    def test_get_best_tool_no_match(self):
        """Test when no tool matches."""
        tools = [get_tool("magnifying_glass")]
        tools = [t for t in tools if t]

        best = get_best_tool_for_inspection(
            tools,
            distance=0.0,
            needs_distant_view=True
        )
        assert best is None
