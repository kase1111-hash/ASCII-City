"""
Tests for Scene and Location - renderable game areas.

These tests verify that scenes correctly:
- Manage hotspots and visibility
- Generate hotspot legends
- Support serialization
"""

import pytest
from shadowengine.render import Scene, Location
from shadowengine.interaction import Hotspot, HotspotType


class TestLocation:
    """Location functionality tests."""

    @pytest.mark.unit
    @pytest.mark.render
    def test_create_location(self, basic_location):
        """Can create a location."""
        assert basic_location.id == "study"
        assert basic_location.name == "The Study"

    @pytest.mark.unit
    @pytest.mark.render
    def test_location_hotspots(self, basic_location):
        """Location has hotspots."""
        hotspots = basic_location.get_visible_hotspots()
        assert len(hotspots) == 4

    @pytest.mark.unit
    @pytest.mark.render
    def test_get_hotspot_by_id(self, basic_location):
        """Can get hotspot by ID."""
        hotspot = basic_location.get_hotspot_by_id("hs_person")
        assert hotspot is not None
        assert hotspot.label == "John"

    @pytest.mark.unit
    @pytest.mark.render
    def test_get_hotspot_by_label(self, basic_location):
        """Can get hotspot by label."""
        hotspot = basic_location.get_hotspot_by_label("Key")
        assert hotspot is not None
        assert hotspot.id == "hs_item"

    @pytest.mark.unit
    @pytest.mark.render
    def test_get_people(self, basic_location):
        """Can get person hotspots."""
        people = basic_location.get_people()
        assert len(people) == 1
        assert people[0].label == "John"

    @pytest.mark.unit
    @pytest.mark.render
    def test_get_exits(self, basic_location):
        """Can get exit hotspots."""
        exits = basic_location.get_exits_list()
        assert len(exits) == 1
        assert exits[0].label == "Door"

    @pytest.mark.unit
    @pytest.mark.render
    def test_hidden_hotspots_not_visible(self, basic_location):
        """Hidden hotspots don't appear in visible list."""
        # Hide one hotspot
        hotspot = basic_location.get_hotspot_by_id("hs_item")
        hotspot.hide()

        visible = basic_location.get_visible_hotspots()
        assert len(visible) == 3

    @pytest.mark.unit
    @pytest.mark.render
    def test_location_exits_dict(self, basic_location):
        """Location tracks exits in dictionary."""
        assert "north" in basic_location.exits
        assert basic_location.exits["north"] == "hallway"


class TestScene:
    """Scene functionality tests."""

    @pytest.mark.unit
    @pytest.mark.render
    def test_create_scene(self, scene):
        """Can create a scene."""
        assert scene.location is not None

    @pytest.mark.unit
    @pytest.mark.render
    def test_number_hotspots(self, scene):
        """Scene numbers visible hotspots."""
        scene.number_hotspots()

        visible = scene.location.get_visible_hotspots()
        numbers = [h.number for h in visible]

        assert 1 in numbers
        assert 2 in numbers
        assert len(numbers) == 4

    @pytest.mark.unit
    @pytest.mark.render
    def test_hotspot_legend(self, scene):
        """Scene generates hotspot legend."""
        scene.number_hotspots()
        legend = scene.get_hotspot_legend()

        assert len(legend) > 0
        assert any("interact with" in line.lower() for line in legend)

    @pytest.mark.unit
    @pytest.mark.render
    def test_rendered_scene(self, scene):
        """Scene generates complete render output."""
        lines = scene.get_rendered_scene()

        # Should have header, description, and legend
        assert len(lines) > 5

        # Should contain location name
        assert any("Study" in line for line in lines)


class TestLocationSerialization:
    """Location serialization tests."""

    @pytest.mark.unit
    @pytest.mark.render
    def test_serialize_location(self, basic_location):
        """Can serialize location."""
        data = basic_location.to_dict()

        assert data["id"] == "study"
        assert data["name"] == "The Study"
        assert len(data["hotspots"]) == 4
        assert "north" in data["exits"]

    @pytest.mark.unit
    @pytest.mark.render
    def test_deserialize_location(self, basic_location):
        """Can deserialize location."""
        data = basic_location.to_dict()
        restored = Location.from_dict(data)

        assert restored.id == "study"
        assert len(restored.hotspots) == 4
        assert restored.exits["north"] == "hallway"

    @pytest.mark.unit
    @pytest.mark.render
    def test_roundtrip_with_state_changes(self, basic_location):
        """Roundtrip preserves hotspot state changes."""
        # Modify a hotspot
        hotspot = basic_location.get_hotspot_by_id("hs_item")
        hotspot.mark_discovered()
        hotspot.deactivate()

        data = basic_location.to_dict()
        restored = Location.from_dict(data)

        restored_hs = restored.get_hotspot_by_id("hs_item")
        assert restored_hs.discovered is True
        assert restored_hs.active is False
