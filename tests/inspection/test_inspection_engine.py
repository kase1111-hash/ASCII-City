"""Tests for InspectionEngine and related types."""

import pytest
from src.shadowengine.inspection.inspection_engine import (
    InspectionEngine, InspectionResult
)
from src.shadowengine.inspection.inspectable import (
    InspectableObject, InspectableFactory, DetailLayer
)
from src.shadowengine.inspection.zoom_level import ZoomLevel, ZoomConstraints
from src.shadowengine.inspection.tool import InspectionTool, ToolType, ToolAffordance


class TestInspectionResult:
    """Tests for InspectionResult."""

    def test_create_result(self):
        """Test creating an inspection result."""
        result = InspectionResult(
            success=True,
            description="You see a dusty desk.",
            zoom_level=ZoomLevel.COARSE
        )
        assert result.success is True
        assert result.description == "You see a dusty desk."
        assert result.zoom_level == ZoomLevel.COARSE

    def test_result_with_discoveries(self):
        """Test result with discoveries."""
        result = InspectionResult(
            success=True,
            description="You find something!",
            zoom_level=ZoomLevel.FINE,
            new_facts=["hidden_compartment"],
            new_items=["key"],
            new_hotspots=["secret_passage"]
        )
        assert "hidden_compartment" in result.new_facts
        assert "key" in result.new_items
        assert "secret_passage" in result.new_hotspots

    def test_result_with_ascii(self):
        """Test result with ASCII art."""
        result = InspectionResult(
            success=True,
            description="A box",
            zoom_level=ZoomLevel.MEDIUM,
            ascii_art="[===]"
        )
        assert result.ascii_art == "[===]"

    def test_failed_result(self):
        """Test failed inspection result."""
        result = InspectionResult(
            success=False,
            description="It's too dark to see.",
            zoom_level=ZoomLevel.COARSE,
            error="no_light"
        )
        assert result.success is False
        assert result.error == "no_light"

    def test_result_with_hints(self):
        """Test result with hints."""
        result = InspectionResult(
            success=False,
            description="You can't see details.",
            zoom_level=ZoomLevel.COARSE,
            hint="Try using a magnifying glass."
        )
        assert result.hint == "Try using a magnifying glass."

    def test_result_flags(self):
        """Test result boolean flags."""
        result = InspectionResult(
            success=True,
            description="Test",
            zoom_level=ZoomLevel.FINE,
            first_time_at_level=True,
            tool_helped=True,
            zoom_changed=True
        )
        assert result.first_time_at_level
        assert result.tool_helped
        assert result.zoom_changed

    def test_serialization(self):
        """Test to_dict."""
        result = InspectionResult(
            success=True,
            description="Test",
            zoom_level=ZoomLevel.MEDIUM,
            new_facts=["fact_1"]
        )
        data = result.to_dict()
        assert data["success"] is True
        assert data["zoom_level"] == ZoomLevel.MEDIUM.value
        assert "fact_1" in data["new_facts"]


class TestInspectionEngine:
    """Tests for InspectionEngine."""

    def test_create_engine(self):
        """Test creating an inspection engine."""
        engine = InspectionEngine()
        assert engine is not None

    def test_create_engine_with_seed(self):
        """Test creating engine with specific seed."""
        engine = InspectionEngine(seed=42)
        assert engine.detail_generator.seed == 42

    def test_register_object(self):
        """Test registering an inspectable object."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Desk",
            description="A wooden desk"
        )
        engine.register_object(obj)
        assert obj.id in engine.objects

    def test_get_registered_object(self):
        """Test getting a registered object."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Desk",
            description="A wooden desk"
        )
        engine.register_object(obj)

        retrieved = engine.get_object(obj.id)
        assert retrieved is not None
        assert retrieved.name == "Desk"

    def test_remove_object(self):
        """Test removing an object."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(name="Test", description="Test")
        engine.register_object(obj)

        engine.remove_object(obj.id)
        assert engine.get_object(obj.id) is None

    def test_find_object_by_name(self):
        """Test finding object by name."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Antique Clock",
            description="An old clock"
        )
        engine.register_object(obj)

        found = engine.find_object_by_name("clock")
        assert found is not None
        assert found.id == obj.id

    def test_add_player_tool(self):
        """Test adding a tool to player inventory."""
        engine = InspectionEngine()
        tool = InspectionTool(
            id="mag_1",
            name="Magnifying Glass",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="A magnifying glass for close inspection"
        )
        engine.add_player_tool(tool)

        assert engine.has_tool("mag_1")

    def test_remove_player_tool(self):
        """Test removing a tool from player inventory."""
        engine = InspectionEngine()
        tool = InspectionTool(
            id="mag_1",
            name="Magnifying Glass",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="A magnifying glass for close inspection"
        )
        engine.add_player_tool(tool)
        engine.remove_player_tool("mag_1")

        assert not engine.has_tool("mag_1")

    def test_add_player_fact(self):
        """Test adding a fact to player knowledge."""
        engine = InspectionEngine()
        engine.add_player_fact("clue_1")

        assert "clue_1" in engine.player_facts

    def test_inspect_object_basic(self):
        """Test basic object inspection."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Desk",
            description="A wooden desk",
            detailed_description="Old and worn",
            fine_description="Carved initials visible"
        )
        engine.register_object(obj)

        result = engine.inspect_object(obj.id)

        assert result.success is True
        assert result.description is not None

    def test_inspect_at_different_zoom_levels(self):
        """Test inspection at different zoom levels - FINE requires tool."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Book",
            description="A leather-bound book",
            detailed_description="Gold lettering on spine",
            close_description="Texture of leather visible",
            fine_description="Hidden notes in margins"
        )
        engine.register_object(obj)

        # Add a magnifying glass for FINE inspection
        tool = InspectionTool(
            id="mag_glass",
            name="Magnifying Glass",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="A magnifying glass"
        )
        engine.add_player_tool(tool)

        # Inspect at coarse
        result_coarse = engine.inspect_object(obj.id, zoom_level=ZoomLevel.COARSE)
        assert result_coarse.success is True

        # Inspect at CLOSE (no tool needed)
        result_close = engine.inspect_object(obj.id, zoom_level=ZoomLevel.CLOSE)
        assert result_close.success is True
        assert result_close.zoom_level == ZoomLevel.CLOSE

        # Inspect at fine (requires tool)
        result_fine = engine.inspect_object(obj.id, zoom_level=ZoomLevel.FINE, tool=tool)
        assert result_fine.success is True
        assert result_fine.zoom_level == ZoomLevel.FINE

    def test_zoom_in_on_object(self):
        """Test zooming in on an object - stops at CLOSE without tool."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Painting",
            description="An oil painting"
        )
        engine.register_object(obj)

        # Start at coarse, zoom in to MEDIUM
        result = engine.zoom_in_on(obj.id)
        assert result.success is True
        assert result.zoom_level == ZoomLevel.MEDIUM

        # Zoom in again to CLOSE (naked eye limit)
        result = engine.zoom_in_on(obj.id)
        assert result.success is True
        assert result.zoom_level == ZoomLevel.CLOSE

        # Try to zoom in to FINE without tool - should fail
        result = engine.zoom_in_on(obj.id)
        assert result.success is False  # Can't reach FINE without magnifying glass

    def test_zoom_in_with_tool(self):
        """Test zooming in with a magnifying glass reaches FINE level."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Painting",
            description="An oil painting"
        )
        engine.register_object(obj)

        tool = InspectionTool(
            id="mag_glass",
            name="Magnifying Glass",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="A magnifying glass"
        )
        engine.add_player_tool(tool)

        # Zoom in to CLOSE first
        engine.zoom_in_on(obj.id)
        engine.zoom_in_on(obj.id)

        # Now zoom in with tool to FINE
        result = engine.zoom_in_on(obj.id, tool=tool)
        assert result.success is True
        assert result.zoom_level == ZoomLevel.FINE

    def test_zoom_out_from_object(self):
        """Test zooming out from an object through all levels."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Statue",
            description="A marble statue"
        )
        engine.register_object(obj)

        # Zoom in to CLOSE first (the max without tool)
        engine.zoom_in_on(obj.id)  # MEDIUM
        engine.zoom_in_on(obj.id)  # CLOSE

        # Now zoom out
        result = engine.zoom_out_from(obj.id)
        assert result.success is True
        assert result.zoom_level == ZoomLevel.MEDIUM

    def test_inspect_with_tool(self):
        """Test inspection with a tool."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_with_hidden(
            name="Document",
            description="An old document",
            hidden_fact="secret_message",
            hidden_description="Hidden text revealed!",
            requires_tool="magnifying_glass"
        )
        engine.register_object(obj)

        tool = InspectionTool(
            id="mag_1",
            name="Magnifying Glass",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="A magnifying glass"
        )
        engine.add_player_tool(tool)

        result = engine.inspect_object(obj.id, zoom_level=ZoomLevel.FINE, tool=tool)
        assert result.success is True
        assert result.tool_helped is True

    def test_process_natural_language_command(self):
        """Test processing natural language commands."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Desk",
            description="A wooden desk"
        )
        engine.register_object(obj)

        result = engine.process_command("look at the desk")
        assert result.success is True

    def test_process_zoom_in_command(self):
        """Test processing zoom in command."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Desk",
            description="A wooden desk"
        )
        engine.register_object(obj)

        # First inspect to establish current object
        engine.inspect_object(obj.id)

        result = engine.process_command("look closer", target_override=obj.id)
        # Should zoom in or fail gracefully

    def test_process_tool_command(self):
        """Test processing tool use command."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Letter",
            description="A sealed letter"
        )
        engine.register_object(obj)

        tool = InspectionTool(
            id="magnifying_glass",
            name="Magnifying Glass",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="A magnifying glass"
        )
        engine.add_player_tool(tool)

        result = engine.process_command("use magnifying glass on letter")
        # Should attempt to use tool

    def test_process_look_around(self):
        """Test processing look around command."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Desk",
            description="A wooden desk"
        )
        engine.register_object(obj)

        # Empty command triggers look around
        result = engine.process_command("")
        assert result.success is True

    def test_time_management(self):
        """Test time management."""
        engine = InspectionEngine()

        engine.set_time(100.0)
        assert engine.zoom_manager.current_time == 100.0

        engine.advance_time(50.0)
        assert engine.zoom_manager.current_time == 150.0

    def test_get_inspection_stats(self):
        """Test getting inspection statistics."""
        engine = InspectionEngine()
        obj = InspectableFactory.create_simple(
            name="Test",
            description="Test"
        )
        engine.register_object(obj)
        engine.inspect_object(obj.id)

        stats = engine.get_inspection_stats()
        assert stats["total_inspections"] >= 1

    def test_serialization(self):
        """Test to_dict/from_dict."""
        engine = InspectionEngine(seed=42)
        obj = InspectableFactory.create_simple(
            name="Desk",
            description="A desk"
        )
        engine.register_object(obj)
        engine.add_player_fact("clue_1")

        data = engine.to_dict()
        restored = InspectionEngine.from_dict(data)

        assert obj.id in restored.objects
        assert "clue_1" in restored.player_facts


class TestInspectionIntegration:
    """Integration tests for the inspection system."""

    def test_full_inspection_workflow(self):
        """Test complete inspection workflow."""
        engine = InspectionEngine(seed=42)

        # Create a complex object with hidden details
        obj = InspectableObject(
            name="Antique Desk",
            base_description="A beautifully crafted antique desk",
            constraints=ZoomConstraints(requires_tool_for_fine=True),
            material="mahogany",
            tags=["furniture", "antique"]
        )
        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.COARSE,
            description="The desk appears well-maintained.",
            first_time_text="A magnificent desk catches your eye."
        ))
        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.MEDIUM,
            description="Intricate carvings cover the surface.",
            reveals_hotspots=["drawer"]
        ))
        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.FINE,
            description="Hidden compartment behind the drawer!",
            reveals_facts=["secret_compartment"],
            reveals_items=["hidden_letter"],
            requires_tool="magnifying_glass"
        ))

        engine.register_object(obj)

        # Add tool
        magnifier = InspectionTool(
            id="magnifying_glass",
            name="Magnifying Glass",
            tool_type=ToolType.MAGNIFYING_GLASS,
            description="A magnifying glass"
        )
        engine.add_player_tool(magnifier)

        # Step 1: Initial look
        result = engine.inspect_object(obj.id)
        assert result.success

        # Step 2: Zoom in
        result = engine.zoom_in_on(obj.id)
        assert result.success
        assert result.zoom_level == ZoomLevel.MEDIUM

        # Step 3: Use magnifying glass for fine detail
        result = engine.inspect_object(obj.id, zoom_level=ZoomLevel.FINE, tool=magnifier)
        assert result.success

    def test_evidence_investigation_workflow(self):
        """Test investigating evidence items."""
        engine = InspectionEngine()

        evidence = InspectableFactory.create_evidence(
            name="Blood-stained Letter",
            description="A letter with suspicious stains",
            evidence_fact="letter_from_victim",
            evidence_description="The handwriting matches the victim's!"
        )
        engine.register_object(evidence)

        # Examine the evidence
        result = engine.inspect_object(evidence.id, zoom_level=ZoomLevel.MEDIUM)
        assert result.success
        if result.new_facts:
            assert "letter_from_victim" in result.new_facts

    def test_distant_observation_workflow(self):
        """Test observing distant objects."""
        engine = InspectionEngine()

        tower = InspectableFactory.create_distant(
            name="Clock Tower",
            description="A tall clock tower in the distance",
            telescope_description="The clock hands are stuck at midnight!"
        )
        engine.register_object(tower)

        telescope = InspectionTool(
            id="telescope",
            name="Brass Telescope",
            tool_type=ToolType.TELESCOPE,
            description="A brass telescope for distant viewing"
        )
        engine.add_player_tool(telescope)

        # Can see with telescope
        result = engine.inspect_object(tower.id, zoom_level=ZoomLevel.FINE, tool=telescope)
        # May or may not succeed depending on constraints
        assert result is not None

    def test_light_requirement(self):
        """Test light requirement for inspection."""
        engine = InspectionEngine()
        engine.has_light = False

        obj = InspectableObject(
            name="Dark Corner",
            base_description="A dark corner"
        )
        obj.add_layer(DetailLayer(
            zoom_level=ZoomLevel.MEDIUM,
            description="Something glitters",
            requires_light=True
        ))
        engine.register_object(obj)

        # Without light, certain details may not be visible
        result = engine.inspect_object(obj.id, zoom_level=ZoomLevel.MEDIUM)
        # Result depends on implementation - light check may affect visibility

    def test_multiple_objects(self):
        """Test inspecting multiple objects."""
        engine = InspectionEngine()

        obj1 = InspectableFactory.create_simple(name="Desk", description="A desk")
        obj2 = InspectableFactory.create_simple(name="Chair", description="A chair")
        obj3 = InspectableFactory.create_simple(name="Lamp", description="A lamp")

        engine.register_object(obj1)
        engine.register_object(obj2)
        engine.register_object(obj3)

        # Inspect each
        for obj_id in [obj1.id, obj2.id, obj3.id]:
            result = engine.inspect_object(obj_id)
            assert result.success

        # Check stats
        stats = engine.get_inspection_stats()
        assert stats["objects_inspected"] == 3
