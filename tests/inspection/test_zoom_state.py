"""Tests for ZoomState and ZoomStateManager."""

import pytest
from src.shadowengine.inspection.zoom_state import (
    ZoomState, ZoomStateManager, ZoomHistory
)
from src.shadowengine.inspection.zoom_level import ZoomLevel


class TestZoomHistory:
    """Tests for ZoomHistory."""

    def test_create_history(self):
        """Test creating a zoom history entry."""
        history = ZoomHistory(
            timestamp=100.0,
            object_id="obj_123",
            from_level=ZoomLevel.COARSE,
            to_level=ZoomLevel.MEDIUM
        )
        assert history.timestamp == 100.0
        assert history.object_id == "obj_123"
        assert history.from_level == ZoomLevel.COARSE
        assert history.to_level == ZoomLevel.MEDIUM

    def test_history_with_tool(self):
        """Test history entry with tool used."""
        history = ZoomHistory(
            timestamp=150.0,
            object_id="obj_123",
            from_level=ZoomLevel.MEDIUM,
            to_level=ZoomLevel.FINE,
            tool_used="magnifying_glass"
        )
        assert history.tool_used == "magnifying_glass"

    def test_history_with_discoveries(self):
        """Test history entry with discoveries."""
        history = ZoomHistory(
            timestamp=150.0,
            object_id="obj_123",
            from_level=ZoomLevel.MEDIUM,
            to_level=ZoomLevel.FINE,
            discoveries=["fact:clue_1", "item:key"]
        )
        assert "fact:clue_1" in history.discoveries
        assert "item:key" in history.discoveries

    def test_serialization(self):
        """Test to_dict/from_dict."""
        history = ZoomHistory(
            timestamp=100.0,
            object_id="obj_123",
            from_level=ZoomLevel.COARSE,
            to_level=ZoomLevel.MEDIUM,
            tool_used="telescope"
        )
        data = history.to_dict()
        restored = ZoomHistory.from_dict(data)
        assert restored.timestamp == history.timestamp
        assert restored.object_id == history.object_id
        assert restored.from_level == history.from_level
        assert restored.to_level == history.to_level
        assert restored.tool_used == history.tool_used


class TestZoomState:
    """Tests for ZoomState."""

    def test_create_state(self):
        """Test creating zoom state."""
        state = ZoomState(object_id="obj_123")
        assert state.object_id == "obj_123"
        assert state.current_level == ZoomLevel.COARSE
        assert state.max_level_reached == ZoomLevel.COARSE
        assert state.inspection_count == 0

    def test_record_inspection(self):
        """Test recording an inspection."""
        state = ZoomState(object_id="obj_123")
        new_discoveries = state.record_inspection(
            zoom_level=ZoomLevel.MEDIUM,
            timestamp=100.0
        )
        assert state.current_level == ZoomLevel.MEDIUM
        assert state.inspection_count == 1
        assert state.first_inspected == 100.0
        assert state.last_inspected == 100.0

    def test_record_inspection_with_discoveries(self):
        """Test recording inspection with discoveries."""
        state = ZoomState(object_id="obj_123")
        discoveries = {
            "facts": ["clue_1"],
            "items": ["key"],
            "hotspots": ["secret_area"]
        }
        new_discoveries = state.record_inspection(
            zoom_level=ZoomLevel.FINE,
            timestamp=100.0,
            discoveries=discoveries
        )
        assert "fact:clue_1" in new_discoveries
        assert "item:key" in new_discoveries
        assert "hotspot:secret_area" in new_discoveries
        assert "clue_1" in state.discovered_facts
        assert "key" in state.discovered_items
        assert "secret_area" in state.discovered_hotspots

    def test_record_inspection_with_tool(self):
        """Test recording inspection with tool."""
        state = ZoomState(object_id="obj_123")
        state.record_inspection(
            zoom_level=ZoomLevel.FINE,
            timestamp=100.0,
            tool_used="magnifying_glass"
        )
        assert "magnifying_glass" in state.tools_used

    def test_max_level_tracking(self):
        """Test that max level is tracked."""
        state = ZoomState(object_id="obj_123")
        state.record_inspection(ZoomLevel.MEDIUM, 100.0)
        state.record_inspection(ZoomLevel.FINE, 101.0)
        assert state.max_level_reached == ZoomLevel.FINE

        state.record_inspection(ZoomLevel.COARSE, 102.0)
        assert state.current_level == ZoomLevel.COARSE
        assert state.max_level_reached == ZoomLevel.FINE  # Still FINE

    def test_is_first_time_at_level(self):
        """Test first time at level detection."""
        state = ZoomState(object_id="obj_123")
        assert state.is_first_time_at_level(ZoomLevel.MEDIUM)

        state.record_inspection(ZoomLevel.MEDIUM, 100.0)
        assert not state.is_first_time_at_level(ZoomLevel.MEDIUM)
        assert state.is_first_time_at_level(ZoomLevel.FINE)

    def test_has_discovered(self):
        """Test discovery tracking."""
        state = ZoomState(object_id="obj_123")
        state.record_inspection(
            ZoomLevel.MEDIUM,
            100.0,
            discoveries={"facts": ["clue_1"]}
        )
        assert state.has_discovered("fact", "clue_1")
        assert not state.has_discovered("fact", "clue_2")

    def test_get_time_since_last_inspection(self):
        """Test time since last inspection."""
        state = ZoomState(object_id="obj_123")
        assert state.get_time_since_last_inspection(100.0) is None

        state.record_inspection(ZoomLevel.MEDIUM, 100.0)
        assert state.get_time_since_last_inspection(150.0) == 50.0

    def test_serialization(self):
        """Test to_dict/from_dict."""
        state = ZoomState(object_id="obj_123")
        state.record_inspection(
            ZoomLevel.MEDIUM,
            100.0,
            tool_used="magnifying_glass",
            discoveries={"facts": ["clue_1"]}
        )

        data = state.to_dict()
        restored = ZoomState.from_dict(data)

        assert restored.object_id == state.object_id
        assert restored.current_level == state.current_level
        assert restored.max_level_reached == state.max_level_reached
        assert restored.inspection_count == state.inspection_count
        assert "clue_1" in restored.discovered_facts
        assert "magnifying_glass" in restored.tools_used


class TestZoomStateManager:
    """Tests for ZoomStateManager."""

    def test_create_manager(self):
        """Test creating a state manager."""
        manager = ZoomStateManager()
        assert len(manager.states) == 0

    def test_get_state(self):
        """Test getting or creating state."""
        manager = ZoomStateManager()

        state = manager.get_state("obj_1")
        assert state.object_id == "obj_1"

        # Same object returns same state
        state2 = manager.get_state("obj_1")
        assert state is state2

    def test_has_state(self):
        """Test checking for state existence."""
        manager = ZoomStateManager()

        assert not manager.has_state("obj_1")
        manager.get_state("obj_1")
        assert manager.has_state("obj_1")

    def test_get_current_zoom(self):
        """Test getting current zoom level."""
        manager = ZoomStateManager()

        # Default for unknown object
        assert manager.get_current_zoom("obj_1") == ZoomLevel.COARSE

        manager.record_zoom("obj_1", ZoomLevel.MEDIUM)
        assert manager.get_current_zoom("obj_1") == ZoomLevel.MEDIUM

    def test_get_max_zoom_reached(self):
        """Test getting max zoom reached."""
        manager = ZoomStateManager()

        assert manager.get_max_zoom_reached("obj_1") == ZoomLevel.COARSE

        manager.record_zoom("obj_1", ZoomLevel.FINE)
        manager.record_zoom("obj_1", ZoomLevel.COARSE)
        assert manager.get_max_zoom_reached("obj_1") == ZoomLevel.FINE

    def test_record_zoom(self):
        """Test recording zoom actions."""
        manager = ZoomStateManager()
        manager.set_time(100.0)

        new_discoveries = manager.record_zoom(
            "obj_1",
            ZoomLevel.MEDIUM,
            discoveries={"facts": ["clue_1"]}
        )

        assert "fact:clue_1" in new_discoveries
        assert manager.get_current_zoom("obj_1") == ZoomLevel.MEDIUM
        assert len(manager.history) == 1

    def test_zoom_in(self):
        """Test zooming in on object."""
        manager = ZoomStateManager()

        new_level = manager.zoom_in("obj_1")
        assert new_level == ZoomLevel.MEDIUM
        assert manager.get_current_zoom("obj_1") == ZoomLevel.MEDIUM

        new_level = manager.zoom_in("obj_1")
        assert new_level == ZoomLevel.FINE

        # Can't zoom past FINE
        new_level = manager.zoom_in("obj_1")
        assert new_level is None

    def test_zoom_out(self):
        """Test zooming out from object."""
        manager = ZoomStateManager()
        manager.record_zoom("obj_1", ZoomLevel.FINE)

        new_level = manager.zoom_out("obj_1")
        assert new_level == ZoomLevel.MEDIUM

        new_level = manager.zoom_out("obj_1")
        assert new_level == ZoomLevel.COARSE

        # Can't zoom past COARSE
        new_level = manager.zoom_out("obj_1")
        assert new_level is None

    def test_reset_zoom(self):
        """Test resetting zoom."""
        manager = ZoomStateManager()
        manager.record_zoom("obj_1", ZoomLevel.FINE)

        new_level = manager.reset_zoom("obj_1")
        assert new_level == ZoomLevel.COARSE
        assert manager.get_current_zoom("obj_1") == ZoomLevel.COARSE

    def test_set_and_advance_time(self):
        """Test time management."""
        manager = ZoomStateManager()

        manager.set_time(100.0)
        assert manager.current_time == 100.0

        manager.advance_time(50.0)
        assert manager.current_time == 150.0

    def test_get_recently_inspected(self):
        """Test getting recently inspected objects."""
        manager = ZoomStateManager()
        manager.set_time(100.0)

        manager.record_zoom("obj_1", ZoomLevel.MEDIUM)
        manager.advance_time(10.0)
        manager.record_zoom("obj_2", ZoomLevel.MEDIUM)
        manager.advance_time(10.0)

        recent = manager.get_recently_inspected(time_window=60.0)
        assert "obj_1" in recent
        assert "obj_2" in recent

    def test_get_fully_inspected(self):
        """Test getting fully inspected objects."""
        manager = ZoomStateManager()

        manager.record_zoom("obj_1", ZoomLevel.FINE)
        manager.record_zoom("obj_2", ZoomLevel.MEDIUM)

        fully_inspected = manager.get_fully_inspected()
        assert "obj_1" in fully_inspected
        assert "obj_2" not in fully_inspected

    def test_get_never_inspected_beyond_coarse(self):
        """Test getting objects only at coarse level."""
        manager = ZoomStateManager()

        manager.get_state("obj_1")  # Creates at COARSE
        manager.record_zoom("obj_2", ZoomLevel.MEDIUM)

        coarse_only = manager.get_never_inspected_beyond_coarse()
        assert "obj_1" in coarse_only
        assert "obj_2" not in coarse_only

    def test_get_all_discoveries(self):
        """Test getting all discoveries."""
        manager = ZoomStateManager()

        manager.record_zoom("obj_1", ZoomLevel.MEDIUM, discoveries={"facts": ["clue_1"]})
        manager.record_zoom("obj_2", ZoomLevel.MEDIUM, discoveries={"items": ["key"]})

        all_discoveries = manager.get_all_discoveries()
        assert "clue_1" in all_discoveries["facts"]
        assert "key" in all_discoveries["items"]

    def test_get_inspection_statistics(self):
        """Test getting inspection statistics."""
        manager = ZoomStateManager()

        manager.record_zoom("obj_1", ZoomLevel.FINE, tool_used="magnifying_glass")
        manager.record_zoom("obj_2", ZoomLevel.MEDIUM)

        stats = manager.get_inspection_statistics()
        assert stats["total_inspections"] == 2
        assert stats["objects_inspected"] == 2
        assert stats["fully_inspected"] == 1
        assert stats["unique_tools_used"] == 1

    def test_serialization(self):
        """Test to_dict/from_dict."""
        manager = ZoomStateManager()
        manager.set_time(100.0)
        manager.record_zoom("obj_1", ZoomLevel.MEDIUM, discoveries={"facts": ["clue_1"]})

        data = manager.to_dict()
        restored = ZoomStateManager.from_dict(data)

        assert "obj_1" in restored.states
        assert restored.current_time == 100.0
        assert restored.get_current_zoom("obj_1") == ZoomLevel.MEDIUM
