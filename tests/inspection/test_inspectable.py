"""Tests for InspectableObject and related types."""

import pytest
from src.shadowengine.inspection.inspectable import (
    DetailLayer, InspectableObject, InspectableFactory
)
from src.shadowengine.inspection.zoom_level import ZoomLevel, ZoomConstraints


class TestDetailLayer:
    """Tests for DetailLayer."""

    def test_create_layer(self):
        """Test creating a detail layer."""
        layer = DetailLayer(
            zoom_level=ZoomLevel.MEDIUM,
            description="You see more details."
        )
        assert layer.zoom_level == ZoomLevel.MEDIUM
        assert layer.description == "You see more details."

    def test_layer_with_reveals(self):
        """Test layer with discoveries."""
        layer = DetailLayer(
            zoom_level=ZoomLevel.FINE,
            description="Hidden compartment found!",
            reveals_facts=["hidden_compartment"],
            reveals_items=["secret_key"],
            reveals_hotspots=["new_area"]
        )
        assert "hidden_compartment" in layer.reveals_facts
        assert "secret_key" in layer.reveals_items
        assert "new_area" in layer.reveals_hotspots

    def test_get_description_first_time(self):
        """Test getting first-time description."""
        layer = DetailLayer(
            zoom_level=ZoomLevel.MEDIUM,
            description="Normal description",
            first_time_text="First time! Something special!"
        )
        assert layer.get_description(first_time=True) == "First time! Something special!"
        assert layer.get_description(first_time=False) == "Normal description"

    def test_get_description_return_text(self):
        """Test getting return description."""
        layer = DetailLayer(
            zoom_level=ZoomLevel.MEDIUM,
            description="Normal description",
            return_text="You remember this..."
        )
        assert layer.get_description(first_time=False) == "You remember this..."

    def test_can_view_default(self):
        """Test can_view with no requirements."""
        layer = DetailLayer(
            zoom_level=ZoomLevel.MEDIUM,
            description="Test"
        )
        assert layer.can_view() is True

    def test_can_view_requires_light(self):
        """Test can_view with light requirement."""
        layer = DetailLayer(
            zoom_level=ZoomLevel.MEDIUM,
            description="Test",
            requires_light=True
        )
        assert layer.can_view(has_light=True) is True
        assert layer.can_view(has_light=False) is False

    def test_can_view_requires_tool(self):
        """Test can_view with tool requirement."""
        layer = DetailLayer(
            zoom_level=ZoomLevel.FINE,
            description="Test",
            requires_tool="magnifying_glass"
        )
        assert layer.can_view(has_tool=False) is False
        assert layer.can_view(has_tool=True, tool_type="telescope") is False
        assert layer.can_view(has_tool=True, tool_type="magnifying_glass") is True

    def test_can_view_requires_fact(self):
        """Test can_view with fact requirement."""
        layer = DetailLayer(
            zoom_level=ZoomLevel.MEDIUM,
            description="Test",
            requires_fact="found_clue"
        )
        assert layer.can_view(known_facts=set()) is False
        assert layer.can_view(known_facts={"other_fact"}) is False
        assert layer.can_view(known_facts={"found_clue"}) is True

    def test_serialization(self):
        """Test to_dict/from_dict."""
        layer = DetailLayer(
            zoom_level=ZoomLevel.MEDIUM,
            description="Test",
            reveals_facts=["fact1"],
            tags=["test_tag"]
        )
        data = layer.to_dict()
        restored = DetailLayer.from_dict(data)
        assert restored.zoom_level == layer.zoom_level
        assert restored.description == layer.description
        assert "fact1" in restored.reveals_facts


class TestInspectableObject:
    """Tests for InspectableObject."""

    def test_create_object(self):
        """Test creating an inspectable object."""
        obj = InspectableObject(
            name="Test Object",
            base_description="A test object"
        )
        assert obj.name == "Test Object"
        assert obj.id  # Auto-generated

    def test_add_and_get_layer(self):
        """Test adding and retrieving layers."""
        obj = InspectableObject(name="Test")
        layer = DetailLayer(
            zoom_level=ZoomLevel.MEDIUM,
            description="Medium detail"
        )
        obj.add_layer(layer)
        assert obj.has_layer(ZoomLevel.MEDIUM)
        assert obj.get_layer(ZoomLevel.MEDIUM) == layer

    def test_get_visible_layers(self):
        """Test getting visible layers up to a zoom level."""
        obj = InspectableObject(name="Test")
        obj.add_layer(DetailLayer(ZoomLevel.COARSE, "Coarse"))
        obj.add_layer(DetailLayer(ZoomLevel.MEDIUM, "Medium"))
        obj.add_layer(DetailLayer(ZoomLevel.FINE, "Fine"))

        layers = obj.get_visible_layers(ZoomLevel.MEDIUM)
        assert len(layers) == 2
        assert layers[0].zoom_level == ZoomLevel.COARSE
        assert layers[1].zoom_level == ZoomLevel.MEDIUM

    def test_get_description_at_zoom(self):
        """Test getting combined description at zoom level."""
        obj = InspectableObject(
            name="Test",
            base_description="Base description"
        )
        obj.add_layer(DetailLayer(ZoomLevel.COARSE, "Coarse detail"))
        obj.add_layer(DetailLayer(ZoomLevel.MEDIUM, "More detail"))

        desc = obj.get_description_at_zoom(ZoomLevel.MEDIUM)
        assert "More detail" in desc

    def test_get_ascii_at_zoom(self):
        """Test getting ASCII art at zoom level."""
        obj = InspectableObject(name="Test")
        obj.add_layer(DetailLayer(
            ZoomLevel.COARSE,
            "Test",
            ascii_art="[===]"
        ))

        assert obj.get_ascii_at_zoom(ZoomLevel.COARSE) == "[===]"
        assert obj.get_ascii_at_zoom(ZoomLevel.FINE) is None

    def test_get_all_reveals(self):
        """Test getting all reveals up to zoom level."""
        obj = InspectableObject(name="Test")
        obj.add_layer(DetailLayer(
            ZoomLevel.COARSE,
            "Coarse",
            reveals_facts=["fact1"]
        ))
        obj.add_layer(DetailLayer(
            ZoomLevel.MEDIUM,
            "Medium",
            reveals_items=["item1"],
            reveals_hotspots=["hotspot1"]
        ))

        reveals = obj.get_all_reveals(ZoomLevel.MEDIUM)
        assert "fact1" in reveals["facts"]
        assert "item1" in reveals["items"]
        assert "hotspot1" in reveals["hotspots"]

    def test_can_zoom_to_default(self):
        """Test can_zoom_to with default constraints."""
        obj = InspectableObject(name="Test")
        assert obj.can_zoom_to(ZoomLevel.COARSE) is True
        assert obj.can_zoom_to(ZoomLevel.MEDIUM) is True
        assert obj.can_zoom_to(ZoomLevel.FINE) is True

    def test_can_zoom_to_with_constraints(self):
        """Test can_zoom_to with custom constraints."""
        obj = InspectableObject(
            name="Test",
            constraints=ZoomConstraints(
                requires_tool_for_fine=True,
                required_tool_type="magnifying_glass"
            )
        )
        assert obj.can_zoom_to(ZoomLevel.FINE, has_tool=False) is False
        assert obj.can_zoom_to(ZoomLevel.FINE, has_tool=True, tool_type="magnifying_glass") is True

    def test_get_max_zoom_with_tool(self):
        """Test getting max zoom based on tools."""
        obj = InspectableObject(
            name="Test",
            constraints=ZoomConstraints(requires_tool_for_fine=True)
        )
        assert obj.get_max_zoom_with_tool(has_tool=False) == ZoomLevel.MEDIUM
        assert obj.get_max_zoom_with_tool(has_tool=True) == ZoomLevel.FINE

    def test_serialization(self):
        """Test to_dict/from_dict."""
        obj = InspectableObject(
            name="Test",
            base_description="A test",
            tags=["test"],
            material="wood"
        )
        obj.add_layer(DetailLayer(ZoomLevel.COARSE, "Coarse"))

        data = obj.to_dict()
        restored = InspectableObject.from_dict(data)

        assert restored.name == obj.name
        assert restored.base_description == obj.base_description
        assert "test" in restored.tags
        assert restored.material == "wood"
        assert restored.has_layer(ZoomLevel.COARSE)


class TestInspectableFactory:
    """Tests for InspectableFactory."""

    def test_create_simple(self):
        """Test creating simple inspectable."""
        obj = InspectableFactory.create_simple(
            name="Simple Object",
            description="A simple object",
            detailed_description="More details",
            fine_description="Fine details"
        )
        assert obj.name == "Simple Object"
        assert obj.has_layer(ZoomLevel.COARSE)
        assert obj.has_layer(ZoomLevel.MEDIUM)
        assert obj.has_layer(ZoomLevel.FINE)

    def test_create_with_hidden(self):
        """Test creating inspectable with hidden detail."""
        obj = InspectableFactory.create_with_hidden(
            name="Secret Box",
            description="An ornate box",
            hidden_fact="secret_compartment",
            hidden_description="A hidden compartment!",
            requires_tool="magnifying_glass"
        )
        assert obj.constraints.requires_tool_for_fine
        fine_layer = obj.get_layer(ZoomLevel.FINE)
        assert fine_layer is not None
        assert "secret_compartment" in fine_layer.reveals_facts

    def test_create_distant(self):
        """Test creating distant inspectable."""
        obj = InspectableFactory.create_distant(
            name="Far Tower",
            description="A tower in the distance",
            telescope_description="Detailed tower view"
        )
        assert obj.is_distant
        assert obj.constraints.requires_tool_for_fine
        assert obj.constraints.required_tool_type == "telescope"

    def test_create_evidence(self):
        """Test creating evidence item."""
        obj = InspectableFactory.create_evidence(
            name="Bloody Knife",
            description="A knife with stains",
            evidence_fact="murder_weapon",
            evidence_description="The blood matches the victim"
        )
        assert "evidence" in obj.tags
        medium_layer = obj.get_layer(ZoomLevel.MEDIUM)
        assert medium_layer is not None
        assert "murder_weapon" in medium_layer.reveals_facts
