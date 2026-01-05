"""
Comprehensive tests for tile event system.
"""

import pytest
import time
from shadowengine.grid import (
    Position, Tile, TileGrid,
    TerrainType, Entity, EntityType
)
from shadowengine.grid.events import (
    TileEvent, TileEventType, TileEventManager,
    on_tile_entered, on_tile_damaged, on_tile_flooded
)


class TestTileEventType:
    """Tests for TileEventType enum."""

    @pytest.mark.unit
    def test_all_event_types_exist(self):
        """All expected event types exist."""
        expected = {
            "ENTERED", "EXITED", "DAMAGED", "FLOODED",
            "FROZEN", "HEATED", "LIT", "MODIFIED",
            "ENTITY_ADDED", "ENTITY_REMOVED", "COLLAPSED", "TRIGGERED"
        }
        actual = {t.name for t in TileEventType}
        assert actual == expected


class TestTileEventCreation:
    """Tests for TileEvent creation."""

    @pytest.mark.unit
    def test_create_event(self, basic_tile, basic_entity):
        """Can create a tile event."""
        event = TileEvent(
            event_type=TileEventType.ENTERED,
            tile=basic_tile,
            cause=basic_entity
        )
        assert event.event_type == TileEventType.ENTERED
        assert event.tile == basic_tile
        assert event.cause == basic_entity

    @pytest.mark.unit
    def test_event_auto_timestamp(self, basic_tile):
        """Event gets automatic timestamp."""
        before = time.time()
        event = TileEvent(
            event_type=TileEventType.ENTERED,
            tile=basic_tile
        )
        after = time.time()

        assert before <= event.timestamp <= after

    @pytest.mark.unit
    def test_event_with_data(self, basic_tile):
        """Event can have additional data."""
        event = TileEvent(
            event_type=TileEventType.DAMAGED,
            tile=basic_tile,
            data={"damage": 50, "type": "fire"}
        )
        assert event.data["damage"] == 50
        assert event.data["type"] == "fire"

    @pytest.mark.unit
    def test_event_to_dict(self, basic_tile, basic_entity):
        """Event can be serialized."""
        event = TileEvent(
            event_type=TileEventType.ENTERED,
            tile=basic_tile,
            cause=basic_entity,
            data={"key": "value"}
        )
        data = event.to_dict()

        assert data["event_type"] == "ENTERED"
        assert data["tile_position"] == basic_tile.position.to_tuple()
        assert data["cause_id"] == basic_entity.id
        assert data["data"] == {"key": "value"}

    @pytest.mark.unit
    def test_event_without_cause(self, basic_tile):
        """Event can have no cause."""
        event = TileEvent(
            event_type=TileEventType.FLOODED,
            tile=basic_tile
        )
        assert event.cause is None
        assert event.to_dict()["cause_id"] is None


class TestTileEventManager:
    """Tests for TileEventManager."""

    @pytest.mark.unit
    def test_create_manager(self):
        """Can create event manager."""
        manager = TileEventManager()
        assert manager is not None

    @pytest.mark.unit
    def test_subscribe_handler(self):
        """Can subscribe handler to event type."""
        manager = TileEventManager()
        received = []

        def handler(event):
            received.append(event)

        manager.subscribe(TileEventType.ENTERED, handler)

        tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)
        event = TileEvent(event_type=TileEventType.ENTERED, tile=tile)
        manager.emit(event)

        assert len(received) == 1
        assert received[0] == event

    @pytest.mark.unit
    def test_subscribe_multiple_handlers(self):
        """Multiple handlers can subscribe to same event."""
        manager = TileEventManager()
        received1 = []
        received2 = []

        manager.subscribe(TileEventType.ENTERED, lambda e: received1.append(e))
        manager.subscribe(TileEventType.ENTERED, lambda e: received2.append(e))

        tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)
        event = TileEvent(event_type=TileEventType.ENTERED, tile=tile)
        manager.emit(event)

        assert len(received1) == 1
        assert len(received2) == 1

    @pytest.mark.unit
    def test_subscribe_different_events(self):
        """Handlers only receive subscribed event types."""
        manager = TileEventManager()
        entered = []
        exited = []

        manager.subscribe(TileEventType.ENTERED, lambda e: entered.append(e))
        manager.subscribe(TileEventType.EXITED, lambda e: exited.append(e))

        tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)
        enter_event = TileEvent(event_type=TileEventType.ENTERED, tile=tile)
        manager.emit(enter_event)

        assert len(entered) == 1
        assert len(exited) == 0

    @pytest.mark.unit
    def test_unsubscribe_handler(self):
        """Can unsubscribe handler."""
        manager = TileEventManager()
        received = []

        def handler(event):
            received.append(event)

        manager.subscribe(TileEventType.ENTERED, handler)
        assert manager.unsubscribe(TileEventType.ENTERED, handler) is True

        tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)
        event = TileEvent(event_type=TileEventType.ENTERED, tile=tile)
        manager.emit(event)

        assert len(received) == 0

    @pytest.mark.unit
    def test_unsubscribe_nonexistent(self):
        """Unsubscribing nonexistent handler returns False."""
        manager = TileEventManager()

        def handler(event):
            pass

        assert manager.unsubscribe(TileEventType.ENTERED, handler) is False

    @pytest.mark.unit
    def test_prevent_duplicate_subscription(self):
        """Same handler not subscribed twice."""
        manager = TileEventManager()
        received = []

        def handler(event):
            received.append(event)

        manager.subscribe(TileEventType.ENTERED, handler)
        manager.subscribe(TileEventType.ENTERED, handler)  # Duplicate

        tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)
        event = TileEvent(event_type=TileEventType.ENTERED, tile=tile)
        manager.emit(event)

        assert len(received) == 1  # Only called once


class TestEventHistory:
    """Tests for event history tracking."""

    @pytest.mark.unit
    def test_events_stored_in_history(self):
        """Events are stored in history."""
        manager = TileEventManager()
        tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)

        for i in range(5):
            event = TileEvent(event_type=TileEventType.ENTERED, tile=tile)
            manager.emit(event)

        history = manager.get_history()
        assert len(history) == 5

    @pytest.mark.unit
    def test_history_limit(self):
        """History respects limit parameter."""
        manager = TileEventManager()
        tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)

        for i in range(10):
            event = TileEvent(event_type=TileEventType.ENTERED, tile=tile)
            manager.emit(event)

        history = manager.get_history(limit=5)
        assert len(history) == 5

    @pytest.mark.unit
    def test_history_filter_by_type(self):
        """Can filter history by event type."""
        manager = TileEventManager()
        tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)

        manager.emit(TileEvent(event_type=TileEventType.ENTERED, tile=tile))
        manager.emit(TileEvent(event_type=TileEventType.EXITED, tile=tile))
        manager.emit(TileEvent(event_type=TileEventType.ENTERED, tile=tile))

        history = manager.get_history(event_type=TileEventType.ENTERED)
        assert len(history) == 2

    @pytest.mark.unit
    def test_history_most_recent_first(self):
        """History returns most recent first."""
        manager = TileEventManager()
        tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)

        event1 = TileEvent(event_type=TileEventType.ENTERED, tile=tile)
        manager.emit(event1)

        event2 = TileEvent(event_type=TileEventType.ENTERED, tile=tile)
        manager.emit(event2)

        history = manager.get_history()
        assert history[0].timestamp >= history[-1].timestamp

    @pytest.mark.unit
    def test_clear_history(self):
        """Can clear event history."""
        manager = TileEventManager()
        tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)

        for i in range(5):
            manager.emit(TileEvent(event_type=TileEventType.ENTERED, tile=tile))

        manager.clear_history()
        history = manager.get_history()
        assert len(history) == 0


class TestEventHandlerErrors:
    """Tests for event handler error handling."""

    @pytest.mark.unit
    def test_handler_error_doesnt_stop_others(self):
        """Error in one handler doesn't stop others."""
        manager = TileEventManager()
        received = []

        def bad_handler(event):
            raise ValueError("Test error")

        def good_handler(event):
            received.append(event)

        manager.subscribe(TileEventType.ENTERED, bad_handler)
        manager.subscribe(TileEventType.ENTERED, good_handler)

        tile = Tile(position=Position(0, 0, 0), terrain_type=TerrainType.SOIL)
        event = TileEvent(event_type=TileEventType.ENTERED, tile=tile)
        manager.emit(event)

        # Good handler should still receive event
        assert len(received) == 1


class TestGridEventIntegration:
    """Tests for event integration with TileGrid."""

    @pytest.mark.unit
    def test_place_entity_emits_entered(self, small_grid):
        """Placing entity emits ENTERED event."""
        received = []
        small_grid.subscribe_to_event(TileEventType.ENTERED, lambda e: received.append(e))

        entity = Entity(id="test", name="Test", entity_type=EntityType.ITEM)
        small_grid.place_entity(entity, Position(5, 5, 0))

        assert len(received) == 1
        assert received[0].event_type == TileEventType.ENTERED
        assert received[0].cause == entity

    @pytest.mark.unit
    def test_remove_entity_emits_removed(self, small_grid):
        """Removing entity emits ENTITY_REMOVED event."""
        received = []
        small_grid.subscribe_to_event(TileEventType.ENTITY_REMOVED, lambda e: received.append(e))

        entity = Entity(id="test", name="Test", entity_type=EntityType.ITEM)
        small_grid.place_entity(entity, Position(5, 5, 0))
        small_grid.remove_entity(entity)

        assert len(received) == 1
        assert received[0].cause == entity

    @pytest.mark.unit
    def test_move_entity_emits_exit_and_enter(self, small_grid):
        """Moving entity emits EXITED and ENTERED events."""
        exited = []
        entered = []
        small_grid.subscribe_to_event(TileEventType.EXITED, lambda e: exited.append(e))
        small_grid.subscribe_to_event(TileEventType.ENTERED, lambda e: entered.append(e))

        entity = Entity(id="test", name="Test", entity_type=EntityType.ITEM)
        small_grid.place_entity(entity, Position(5, 5, 0))
        small_grid.move_entity(entity, Position(6, 6, 0))

        assert len(entered) == 2  # Initial placement + move
        assert len(exited) == 1   # Just the move

    @pytest.mark.unit
    def test_event_contains_correct_tile(self, small_grid):
        """Event contains the correct tile."""
        received = []
        small_grid.subscribe_to_event(TileEventType.ENTERED, lambda e: received.append(e))

        entity = Entity(id="test", name="Test", entity_type=EntityType.ITEM)
        small_grid.place_entity(entity, Position(5, 5, 0))

        assert received[0].tile.position == Position(5, 5, 0)


class TestDefaultEventHandlers:
    """Tests for default event handler functions."""

    @pytest.mark.unit
    def test_on_tile_entered_with_trigger(self, basic_tile, trigger_entity):
        """Entering tile with trigger doesn't raise error."""
        basic_tile.add_entity(trigger_entity)
        event = TileEvent(
            event_type=TileEventType.ENTERED,
            tile=basic_tile,
            cause=trigger_entity
        )
        # Should not raise
        on_tile_entered(event)

    @pytest.mark.unit
    def test_on_tile_entered_without_cause(self, basic_tile):
        """Entering tile without cause handles gracefully."""
        event = TileEvent(
            event_type=TileEventType.ENTERED,
            tile=basic_tile,
            cause=None
        )
        # Should not raise
        on_tile_entered(event)

    @pytest.mark.unit
    def test_on_tile_damaged_glass(self, glass_tile):
        """Damaging glass tile with high damage."""
        event = TileEvent(
            event_type=TileEventType.DAMAGED,
            tile=glass_tile,
            data={"damage": 50}
        )
        # Should not raise
        on_tile_damaged(event)

    @pytest.mark.unit
    def test_on_tile_flooded(self, basic_tile):
        """Flooding tile updates moisture."""
        event = TileEvent(
            event_type=TileEventType.FLOODED,
            tile=basic_tile
        )
        on_tile_flooded(event)
        assert basic_tile.environment.moisture == 1.0
