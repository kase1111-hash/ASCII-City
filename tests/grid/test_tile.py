"""Tests for Tile and Position classes."""

import pytest

from src.shadowengine.grid.tile import (
    Position,
    DIRECTIONS,
    TileEnvironment,
    Tile,
)
from src.shadowengine.grid.terrain import (
    TerrainType,
    FluidType,
    TerrainModifier,
)


class TestPosition:
    """Test Position class."""

    def test_position_creation(self):
        """Test creating a position."""
        pos = Position(5, 10, 2)
        assert pos.x == 5
        assert pos.y == 10
        assert pos.z == 2

    def test_position_default_z(self):
        """Test position with default z."""
        pos = Position(5, 10)
        assert pos.z == 0

    def test_position_addition(self):
        """Test position addition."""
        pos1 = Position(1, 2, 3)
        pos2 = Position(4, 5, 6)
        result = pos1 + pos2
        assert result == Position(5, 7, 9)

    def test_position_subtraction(self):
        """Test position subtraction."""
        pos1 = Position(5, 7, 9)
        pos2 = Position(1, 2, 3)
        result = pos1 - pos2
        assert result == Position(4, 5, 6)

    def test_distance_to(self):
        """Test Euclidean distance calculation."""
        pos1 = Position(0, 0, 0)
        pos2 = Position(3, 4, 0)
        assert pos1.distance_to(pos2) == 5.0

    def test_manhattan_distance(self):
        """Test Manhattan distance calculation."""
        pos1 = Position(0, 0, 0)
        pos2 = Position(3, 4, 2)
        assert pos1.manhattan_distance(pos2) == 9

    def test_to_tuple(self):
        """Test conversion to tuple."""
        pos = Position(1, 2, 3)
        assert pos.to_tuple() == (1, 2, 3)

    def test_from_tuple_3d(self):
        """Test creation from 3D tuple."""
        pos = Position.from_tuple((1, 2, 3))
        assert pos == Position(1, 2, 3)

    def test_from_tuple_2d(self):
        """Test creation from 2D tuple."""
        pos = Position.from_tuple((1, 2))
        assert pos == Position(1, 2, 0)

    def test_to_key(self):
        """Test string key generation."""
        pos = Position(1, 2, 3)
        assert pos.to_key() == "1,2,3"

    def test_from_key(self):
        """Test creation from key."""
        pos = Position.from_key("1,2,3")
        assert pos == Position(1, 2, 3)

    def test_position_is_hashable(self):
        """Test that positions can be used as dict keys."""
        pos = Position(1, 2, 3)
        d = {pos: "value"}
        assert d[Position(1, 2, 3)] == "value"


class TestDirections:
    """Test direction constants."""

    def test_cardinal_directions(self):
        """Test cardinal directions."""
        assert DIRECTIONS["north"] == Position(0, -1, 0)
        assert DIRECTIONS["south"] == Position(0, 1, 0)
        assert DIRECTIONS["east"] == Position(1, 0, 0)
        assert DIRECTIONS["west"] == Position(-1, 0, 0)

    def test_diagonal_directions(self):
        """Test diagonal directions."""
        assert DIRECTIONS["northeast"] == Position(1, -1, 0)
        assert DIRECTIONS["southwest"] == Position(-1, 1, 0)

    def test_vertical_directions(self):
        """Test up/down directions."""
        assert DIRECTIONS["up"] == Position(0, 0, 1)
        assert DIRECTIONS["down"] == Position(0, 0, -1)


class TestTileEnvironment:
    """Test TileEnvironment class."""

    def test_default_environment(self):
        """Test default environment values."""
        env = TileEnvironment()
        assert env.fluid is None
        assert env.temperature == 20.0
        assert env.sound_level == 0.0
        assert env.light_level == 0.5
        assert env.moisture == 0.0

    def test_temperature_effect(self):
        """Test temperature effect categories."""
        env = TileEnvironment(temperature=-30)
        assert env.get_temperature_effect() == "freezing"

        env.temperature = 25
        assert env.get_temperature_effect() == "comfortable"

        env.temperature = 60
        assert env.get_temperature_effect() == "extreme"

    def test_moisture_effect(self):
        """Test moisture effect categories."""
        env = TileEnvironment(moisture=0.1)
        assert env.get_moisture_effect() == "dry"

        env.moisture = 0.9
        assert env.get_moisture_effect() == "flooded"

    def test_light_effect(self):
        """Test light effect categories."""
        env = TileEnvironment(light_level=0.05)
        assert env.get_light_effect() == "pitch_black"

        env.light_level = 0.5
        assert env.get_light_effect() == "normal"

    def test_environment_serialization(self):
        """Test environment serialization."""
        env = TileEnvironment(
            fluid=FluidType.WATER,
            temperature=15.0,
            moisture=0.5,
        )
        data = env.to_dict()
        restored = TileEnvironment.from_dict(data)
        assert restored.fluid == env.fluid
        assert restored.temperature == env.temperature
        assert restored.moisture == env.moisture


class TestTile:
    """Test Tile class."""

    def test_tile_creation(self):
        """Test creating a tile."""
        tile = Tile(position=Position(5, 10, 0))
        assert tile.position == Position(5, 10, 0)
        assert tile.terrain_type == TerrainType.FLOOR

    def test_tile_with_terrain(self):
        """Test tile with specific terrain."""
        tile = Tile(
            position=Position(0, 0, 0),
            terrain_type=TerrainType.ROCK,
        )
        assert tile.terrain_type == TerrainType.ROCK
        assert tile.passable is False
        assert tile.opaque is True

    def test_tile_affordances(self):
        """Test tile affordances from terrain."""
        tile = Tile(
            position=Position(0, 0, 0),
            terrain_type=TerrainType.WATER,
        )
        affordances = tile.affordances
        assert "swimmable" in affordances

    def test_tile_has_affordance(self):
        """Test checking for specific affordance."""
        tile = Tile(
            position=Position(0, 0, 0),
            terrain_type=TerrainType.WOOD,
        )
        assert tile.has_affordance("flammable") is True
        assert tile.has_affordance("swimmable") is False

    def test_add_modifier(self):
        """Test adding terrain modifier."""
        tile = Tile(
            position=Position(0, 0, 0),
            terrain_type=TerrainType.FLOOR,
        )
        mod = TerrainModifier(
            type="wet",
            adds_affordances=["slippery"],
        )
        tile.add_modifier(mod)
        assert tile.has_modifier("wet")
        assert "slippery" in tile.affordances

    def test_remove_modifier(self):
        """Test removing terrain modifier."""
        tile = Tile(position=Position(0, 0, 0))
        tile.add_modifier(TerrainModifier(type="wet"))
        assert tile.has_modifier("wet")
        tile.remove_modifier("wet")
        assert tile.has_modifier("wet") is False

    def test_movement_cost(self):
        """Test movement cost calculation."""
        tile = Tile(
            position=Position(0, 0, 0),
            terrain_type=TerrainType.FLOOR,
        )
        assert tile.movement_cost == 1.0

        # Water has higher cost
        tile.set_terrain(TerrainType.WATER)
        assert tile.movement_cost > 1.0

    def test_modifier_affects_movement_cost(self):
        """Test modifier affects movement cost."""
        tile = Tile(position=Position(0, 0, 0))
        base_cost = tile.movement_cost
        tile.add_modifier(TerrainModifier(
            type="slippery",
            movement_cost_modifier=1.5,
        ))
        assert tile.movement_cost == base_cost * 1.5

    def test_environment_affects_affordances(self):
        """Test environment modifies affordances."""
        tile = Tile(
            position=Position(0, 0, 0),
            terrain_type=TerrainType.WOOD,
        )
        assert "flammable" in tile.affordances

        # High moisture removes flammable
        tile.set_environment(moisture=0.9)
        assert "flammable" not in tile.affordances
        assert "slippery" in tile.affordances

    def test_add_entity(self):
        """Test adding entity to tile."""
        tile = Tile(position=Position(0, 0, 0))
        tile.add_entity("entity_1")
        assert tile.has_entity("entity_1")
        assert "entity_1" in tile.entity_ids

    def test_remove_entity(self):
        """Test removing entity from tile."""
        tile = Tile(position=Position(0, 0, 0))
        tile.add_entity("entity_1")
        tile.remove_entity("entity_1")
        assert tile.has_entity("entity_1") is False

    def test_add_feature(self):
        """Test adding feature to tile."""
        tile = Tile(position=Position(0, 0, 0))
        tile.add_feature("door_1")
        assert "door_1" in tile.feature_ids

    def test_is_empty(self):
        """Test empty tile check."""
        tile = Tile(position=Position(0, 0, 0))
        assert tile.is_empty() is True
        tile.add_entity("entity_1")
        assert tile.is_empty() is False

    def test_set_terrain(self):
        """Test changing terrain type."""
        tile = Tile(position=Position(0, 0, 0))
        tile.set_terrain(TerrainType.ROCK)
        assert tile.terrain_type == TerrainType.ROCK
        assert tile.passable is False

    def test_tile_serialization(self):
        """Test tile serialization."""
        tile = Tile(
            position=Position(5, 10, 2),
            terrain_type=TerrainType.WATER,
            height=1.5,
        )
        tile.add_modifier(TerrainModifier(type="frozen"))
        tile.add_entity("fish_1")

        data = tile.to_dict()
        restored = Tile.from_dict(data)

        assert restored.position == tile.position
        assert restored.terrain_type == tile.terrain_type
        assert restored.height == tile.height
        assert restored.has_modifier("frozen")
        assert restored.has_entity("fish_1")

    def test_tile_clone(self):
        """Test cloning a tile."""
        original = Tile(
            position=Position(0, 0, 0),
            terrain_type=TerrainType.ROCK,
        )
        original.add_modifier(TerrainModifier(type="cracked"))
        original.add_entity("entity_1")

        clone = original.clone(Position(5, 5, 0))

        assert clone.position == Position(5, 5, 0)
        assert clone.terrain_type == original.terrain_type
        assert clone.has_modifier("cracked")
        # Entities should not be cloned
        assert not clone.has_entity("entity_1")
