"""Tests for tile event system."""

import pytest

from src.shadowengine.grid.events import (
    TileEventType,
    TileEvent,
    TileEventBus,
    create_movement_event,
    create_damage_event,
    create_environmental_event,
)


class TestTileEventType:
    """Test TileEventType enum."""

    def test_movement_events(self):
        """Test movement event types."""
        assert TileEventType.ENTITY_ENTERED.value == "entity_entered"
        assert TileEventType.ENTITY_EXITED.value == "entity_exited"
        assert TileEventType.ENTITY_MOVED.value == "entity_moved"

    def test_state_events(self):
        """Test state change event types."""
        assert TileEventType.TILE_DAMAGED.value == "tile_damaged"
        assert TileEventType.TERRAIN_CHANGED.value == "terrain_changed"

    def test_environmental_events(self):
        """Test environmental event types."""
        assert TileEventType.FLOODED.value == "flooded"
        assert TileEventType.FROZEN.value == "frozen"


class TestTileEvent:
    """Test TileEvent class."""

    def test_event_creation(self):
        """Test creating an event."""
        event = TileEvent(
            type=TileEventType.ENTITY_ENTERED,
            tile_position=(5, 10, 0),
        )
        assert event.type == TileEventType.ENTITY_ENTERED
        assert event.tile_position == (5, 10, 0)
        assert event.timestamp > 0

    def test_event_with_cause(self):
        """Test event with cause information."""
        event = TileEvent(
            type=TileEventType.TILE_DAMAGED,
            tile_position=(0, 0, 0),
            cause_id="player",
            cause_type="entity",
            damage_amount=10.0,
            damage_type="physical",
        )
        assert event.cause_id == "player"
        assert event.damage_amount == 10.0
        assert event.damage_type == "physical"

    def test_movement_event_positions(self):
        """Test movement event positions."""
        event = TileEvent(
            type=TileEventType.ENTITY_MOVED,
            tile_position=(5, 5, 0),
            from_position=(4, 5, 0),
            to_position=(5, 5, 0),
        )
        assert event.from_position == (4, 5, 0)
        assert event.to_position == (5, 5, 0)

    def test_event_serialization(self):
        """Test event serialization."""
        event = TileEvent(
            type=TileEventType.TRIGGERED,
            tile_position=(10, 10, 0),
            cause_id="player",
            data={"trigger_id": "trap_1"},
        )
        data = event.to_dict()
        restored = TileEvent.from_dict(data)

        assert restored.type == event.type
        assert restored.tile_position == event.tile_position
        assert restored.cause_id == event.cause_id
        assert restored.data["trigger_id"] == "trap_1"


class TestTileEventBus:
    """Test TileEventBus class."""

    def test_event_bus_creation(self):
        """Test creating event bus."""
        bus = TileEventBus()
        assert bus.stats["events_dispatched"] == 0

    def test_subscribe_and_dispatch(self):
        """Test subscribing and dispatching events."""
        bus = TileEventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(TileEventType.ENTITY_ENTERED, handler)

        event = TileEvent(
            type=TileEventType.ENTITY_ENTERED,
            tile_position=(0, 0, 0),
        )
        handlers_called = bus.dispatch(event)

        assert handlers_called == 1
        assert len(received) == 1
        assert received[0] == event

    def test_subscribe_multiple_handlers(self):
        """Test multiple handlers for same event."""
        bus = TileEventBus()
        count = [0]

        def handler1(event):
            count[0] += 1

        def handler2(event):
            count[0] += 10

        bus.subscribe(TileEventType.TILE_DAMAGED, handler1)
        bus.subscribe(TileEventType.TILE_DAMAGED, handler2)

        bus.dispatch(TileEvent(
            type=TileEventType.TILE_DAMAGED,
            tile_position=(0, 0, 0),
        ))

        assert count[0] == 11

    def test_subscribe_all(self):
        """Test subscribing to all events."""
        bus = TileEventBus()
        received = []

        bus.subscribe_all(lambda e: received.append(e.type))

        bus.dispatch(TileEvent(type=TileEventType.ENTITY_ENTERED, tile_position=(0, 0, 0)))
        bus.dispatch(TileEvent(type=TileEventType.TILE_DAMAGED, tile_position=(0, 0, 0)))

        assert TileEventType.ENTITY_ENTERED in received
        assert TileEventType.TILE_DAMAGED in received

    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        bus = TileEventBus()
        count = [0]

        def handler(event):
            count[0] += 1

        bus.subscribe(TileEventType.ENTITY_ENTERED, handler)
        bus.dispatch(TileEvent(type=TileEventType.ENTITY_ENTERED, tile_position=(0, 0, 0)))
        assert count[0] == 1

        bus.unsubscribe(TileEventType.ENTITY_ENTERED, handler)
        bus.dispatch(TileEvent(type=TileEventType.ENTITY_ENTERED, tile_position=(0, 0, 0)))
        assert count[0] == 1  # Not increased

    def test_emit_entered(self):
        """Test emit_entered helper."""
        bus = TileEventBus()
        received = []

        bus.subscribe(TileEventType.ENTITY_ENTERED, lambda e: received.append(e))

        event = bus.emit_entered((5, 5, 0), "entity_1", from_position=(4, 5, 0))

        assert len(received) == 1
        assert received[0].cause_id == "entity_1"
        assert received[0].from_position == (4, 5, 0)

    def test_emit_exited(self):
        """Test emit_exited helper."""
        bus = TileEventBus()
        received = []

        bus.subscribe(TileEventType.ENTITY_EXITED, lambda e: received.append(e))

        bus.emit_exited((5, 5, 0), "entity_1", to_position=(6, 5, 0))

        assert len(received) == 1
        assert received[0].to_position == (6, 5, 0)

    def test_emit_damaged(self):
        """Test emit_damaged helper."""
        bus = TileEventBus()
        received = []

        bus.subscribe(TileEventType.TILE_DAMAGED, lambda e: received.append(e))

        bus.emit_damaged((0, 0, 0), 25.0, "fire", cause_id="torch")

        assert len(received) == 1
        assert received[0].damage_amount == 25.0
        assert received[0].damage_type == "fire"

    def test_emit_triggered(self):
        """Test emit_triggered helper."""
        bus = TileEventBus()
        received = []

        bus.subscribe(TileEventType.TRIGGERED, lambda e: received.append(e))

        bus.emit_triggered((5, 5, 0), "pressure_plate", cause_id="player")

        assert len(received) == 1
        assert received[0].data["trigger_id"] == "pressure_plate"

    def test_emit_custom(self):
        """Test emit_custom helper."""
        bus = TileEventBus()
        received = []

        bus.subscribe(TileEventType.CUSTOM, lambda e: received.append(e))

        bus.emit_custom((0, 0, 0), "special_event", data={"value": 42})

        assert len(received) == 1
        assert received[0].data["event_name"] == "special_event"
        assert received[0].data["value"] == 42

    def test_event_history(self):
        """Test event history recording."""
        bus = TileEventBus()

        for i in range(5):
            bus.dispatch(TileEvent(
                type=TileEventType.ENTITY_ENTERED,
                tile_position=(i, 0, 0),
            ))

        history = bus.get_history()
        assert len(history) == 5

    def test_history_filtering(self):
        """Test history filtering."""
        bus = TileEventBus()

        bus.dispatch(TileEvent(type=TileEventType.ENTITY_ENTERED, tile_position=(0, 0, 0)))
        bus.dispatch(TileEvent(type=TileEventType.TILE_DAMAGED, tile_position=(0, 0, 0)))
        bus.dispatch(TileEvent(type=TileEventType.ENTITY_ENTERED, tile_position=(1, 1, 0)))

        entered_events = bus.get_history(event_type=TileEventType.ENTITY_ENTERED)
        assert len(entered_events) == 2

        pos_events = bus.get_history(tile_position=(0, 0, 0))
        assert len(pos_events) == 2

    def test_clear_history(self):
        """Test clearing history."""
        bus = TileEventBus()
        bus.dispatch(TileEvent(type=TileEventType.ENTITY_ENTERED, tile_position=(0, 0, 0)))
        bus.clear_history()
        assert len(bus.get_history()) == 0

    def test_stats(self):
        """Test event bus statistics."""
        bus = TileEventBus()
        bus.subscribe(TileEventType.ENTITY_ENTERED, lambda e: None)

        for _ in range(10):
            bus.dispatch(TileEvent(type=TileEventType.ENTITY_ENTERED, tile_position=(0, 0, 0)))

        stats = bus.get_stats()
        assert stats["events_dispatched"] == 10
        assert stats["handlers_called"] == 10

    def test_reset_stats(self):
        """Test resetting statistics."""
        bus = TileEventBus()
        bus.dispatch(TileEvent(type=TileEventType.ENTITY_ENTERED, tile_position=(0, 0, 0)))
        bus.reset_stats()
        assert bus.stats["events_dispatched"] == 0


class TestEventFactories:
    """Test event factory functions."""

    def test_create_movement_event(self):
        """Test creating movement event."""
        event = create_movement_event("player", (0, 0, 0), (1, 0, 0))
        assert event.type == TileEventType.ENTITY_MOVED
        assert event.cause_id == "player"
        assert event.from_position == (0, 0, 0)
        assert event.to_position == (1, 0, 0)

    def test_create_damage_event(self):
        """Test creating damage event."""
        event = create_damage_event((5, 5, 0), 50.0, "explosion", "bomb")
        assert event.type == TileEventType.TILE_DAMAGED
        assert event.damage_amount == 50.0
        assert event.damage_type == "explosion"
        assert event.cause_id == "bomb"

    def test_create_environmental_event(self):
        """Test creating environmental event."""
        event = create_environmental_event((0, 0, 0), TileEventType.FLOODED, 0.8)
        assert event.type == TileEventType.FLOODED
        assert event.data["intensity"] == 0.8
