"""Tests for TileMemory system."""

import pytest
from src.shadowengine.npc_intelligence.tile_memory import (
    TileMemory, TileMemoryManager
)


class TestTileMemory:
    """Tests for TileMemory dataclass."""

    def test_tile_memory_creation(self):
        """Test creating tile memory."""
        tile = TileMemory(
            location=(10, 20),
            location_name="dark_alley"
        )

        assert tile.location == (10, 20)
        assert tile.location_name == "dark_alley"
        assert tile.danger_rating == 0.0
        assert tile.mood_modifier == "neutral"

    def test_add_violence_event(self):
        """Test adding violence event increases danger."""
        tile = TileMemory(location=(0, 0))

        tile.add_event(
            event_id="evt_001",
            event_type="violence",
            tags=["violence"],
            timestamp=100.0,
            severity=0.8
        )

        assert tile.danger_rating > 0
        assert tile.crime_rating > 0
        assert tile.npc_avoidance > 0
        assert "evt_001" in tile.event_history

    def test_add_death_event(self):
        """Test adding death event."""
        tile = TileMemory(location=(0, 0))

        tile.add_event(
            event_id="evt_001",
            event_type="death",
            tags=["death"],
            timestamp=100.0,
            severity=1.0
        )

        assert tile.death_count == 1
        assert tile.danger_rating >= 0.5
        assert tile.mood_modifier == "ominous"

    def test_add_conversation_event(self):
        """Test adding conversation increases activity."""
        tile = TileMemory(location=(0, 0), activity_level=0.3)

        tile.add_event(
            event_id="evt_001",
            event_type="conversation",
            tags=["social"],
            timestamp=100.0
        )

        assert tile.activity_level > 0.3
        assert tile.rumor_density > 0

    def test_add_rumor_activity(self):
        """Test increasing rumor density."""
        tile = TileMemory(location=(0, 0))

        tile.add_rumor_activity(0.3)
        tile.add_rumor_activity(0.3)

        assert tile.rumor_density == 0.6

    def test_decay_reduces_metrics(self):
        """Test decay reduces danger and avoidance."""
        tile = TileMemory(
            location=(0, 0),
            danger_rating=0.5,
            crime_rating=0.4,
            npc_avoidance=0.3
        )

        tile.decay(dt=10.0)

        assert tile.danger_rating < 0.5
        assert tile.crime_rating < 0.4
        assert tile.npc_avoidance < 0.3

    def test_mood_updates_based_on_state(self):
        """Test mood modifier updates with state."""
        tile = TileMemory(location=(0, 0))

        # Add multiple violence events to make it tense/ominous
        tile.add_event("evt_1", "violence", [], 100.0, 1.0)
        tile.add_event("evt_2", "violence", [], 101.0, 1.0)
        assert tile.mood_modifier in ["tense", "ominous"]

        # High activity makes it busy
        tile2 = TileMemory(location=(1, 1), activity_level=0.8)
        tile2._update_mood()
        assert tile2.mood_modifier == "busy"

    def test_get_atmosphere_hints(self):
        """Test getting atmosphere hints."""
        tile = TileMemory(
            location=(0, 0),
            danger_rating=0.7,
            death_count=1,
            npc_avoidance=0.7,
            event_tags={"blood"}
        )

        hints = tile.get_atmosphere_hints()

        assert len(hints) > 0
        assert any("dangerous" in h.lower() for h in hints)
        assert any("death" in h.lower() for h in hints)

    def test_get_dialogue_tone(self):
        """Test getting dialogue tone."""
        dangerous = TileMemory(location=(0, 0), danger_rating=0.8)
        gossipy = TileMemory(location=(1, 1), rumor_density=0.7)
        deadly = TileMemory(location=(2, 2), death_count=2)

        assert dangerous.get_dialogue_tone() == "whispered"
        assert gossipy.get_dialogue_tone() == "gossipy"
        assert deadly.get_dialogue_tone() == "somber"

    def test_should_npc_avoid(self):
        """Test NPC avoidance check."""
        tile = TileMemory(location=(0, 0), npc_avoidance=0.7)

        # Fearful NPC should avoid
        assert tile.should_npc_avoid(npc_fear_level=0.8)

        # Brave NPC might not
        assert not tile.should_npc_avoid(npc_fear_level=0.2)

    def test_tile_memory_serialization(self):
        """Test tile memory to_dict and from_dict."""
        tile = TileMemory(
            location=(5, 10),
            location_name="test_location",
            event_history=["evt_1", "evt_2"],
            event_tags={"violence", "danger"},
            danger_rating=0.6,
            death_count=1,
            mood_modifier="ominous"
        )

        data = tile.to_dict()
        restored = TileMemory.from_dict(data)

        assert restored.location == (5, 10)
        assert restored.location_name == "test_location"
        assert restored.danger_rating == 0.6
        assert restored.death_count == 1
        assert "violence" in restored.event_tags


class TestTileMemoryManager:
    """Tests for TileMemoryManager."""

    def test_manager_creation(self):
        """Test creating manager."""
        manager = TileMemoryManager()

        assert len(manager.tile_memories) == 0

    def test_get_or_create(self):
        """Test getting or creating tile memory."""
        manager = TileMemoryManager()

        tile1 = manager.get_or_create((10, 20), "alley")
        tile2 = manager.get_or_create((10, 20))  # Same location

        assert tile1 is tile2
        assert tile1.location_name == "alley"
        assert (10, 20) in manager.tile_memories

    def test_get_by_name(self):
        """Test getting tile by name."""
        manager = TileMemoryManager()
        manager.get_or_create((10, 20), "dark_alley")

        tile = manager.get_by_name("dark_alley")

        assert tile is not None
        assert tile.location == (10, 20)
        assert manager.get_by_name("nonexistent") is None

    def test_record_event(self):
        """Test recording event at location."""
        manager = TileMemoryManager()

        tile = manager.record_event(
            location=(5, 5),
            location_name="crime_scene",
            event_id="evt_001",
            event_type="violence",
            tags=["violence", "blood"],
            timestamp=100.0,
            severity=0.8
        )

        assert tile.danger_rating > 0
        assert "evt_001" in tile.event_history

    def test_update_decays_all(self):
        """Test update decays all tiles."""
        manager = TileMemoryManager()
        manager.get_or_create((0, 0)).danger_rating = 0.5
        manager.get_or_create((1, 1)).danger_rating = 0.5

        manager.update(dt=10.0)

        for tile in manager.tile_memories.values():
            assert tile.danger_rating < 0.5

    def test_get_dangerous_locations(self):
        """Test finding dangerous locations."""
        manager = TileMemoryManager()
        manager.get_or_create((0, 0)).danger_rating = 0.8
        manager.get_or_create((1, 1)).danger_rating = 0.2
        manager.get_or_create((2, 2)).danger_rating = 0.9

        dangerous = manager.get_dangerous_locations(threshold=0.5)

        assert len(dangerous) == 2

    def test_get_avoided_locations(self):
        """Test finding avoided locations."""
        manager = TileMemoryManager()
        manager.get_or_create((0, 0)).npc_avoidance = 0.7
        manager.get_or_create((1, 1)).npc_avoidance = 0.3

        avoided = manager.get_avoided_locations(threshold=0.5)

        assert len(avoided) == 1

    def test_get_rumor_hotspots(self):
        """Test finding rumor hotspots."""
        manager = TileMemoryManager()
        manager.get_or_create((0, 0)).rumor_density = 0.8
        manager.get_or_create((1, 1)).rumor_density = 0.2

        hotspots = manager.get_rumor_hotspots(threshold=0.5)

        assert len(hotspots) == 1

    def test_get_locations_with_deaths(self):
        """Test finding death locations."""
        manager = TileMemoryManager()
        manager.get_or_create((0, 0)).death_count = 2
        manager.get_or_create((1, 1)).death_count = 0
        manager.get_or_create((2, 2)).death_count = 1

        deadly = manager.get_locations_with_deaths()

        assert len(deadly) == 2

    def test_modify_path_for_npc(self):
        """Test modifying path for fearful NPC."""
        manager = TileMemoryManager()
        manager.get_or_create((1, 1)).npc_avoidance = 0.9

        path = [(0, 0), (1, 1), (2, 2)]

        # Path still contains all points (in simple implementation)
        modified = manager.modify_path_for_npc(path, npc_fear_level=0.8)

        assert len(modified) == 3

    def test_get_all_hints_at(self):
        """Test getting hints at location."""
        manager = TileMemoryManager()
        tile = manager.get_or_create((5, 5))
        tile.danger_rating = 0.7
        tile.death_count = 1

        hints = manager.get_all_hints_at((5, 5))

        assert len(hints) > 0

    def test_get_all_hints_at_empty_location(self):
        """Test getting hints at empty location."""
        manager = TileMemoryManager()

        hints = manager.get_all_hints_at((99, 99))

        assert hints == []

    def test_manager_serialization(self):
        """Test manager to_dict and from_dict."""
        manager = TileMemoryManager()
        manager.get_or_create((0, 0), "location_a").danger_rating = 0.5
        manager.get_or_create((1, 1), "location_b").death_count = 1
        manager.current_time = 500.0

        data = manager.to_dict()
        restored = TileMemoryManager.from_dict(data)

        assert len(restored.tile_memories) == 2
        assert restored.current_time == 500.0
        assert restored.tile_memories[(0, 0)].danger_rating == 0.5
