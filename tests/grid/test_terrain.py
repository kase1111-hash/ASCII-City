"""Tests for terrain types and modifiers."""

import pytest

from src.shadowengine.grid.terrain import (
    TerrainType,
    FluidType,
    TerrainModifier,
    TERRAIN_PROPERTIES,
    TERRAIN_MODIFIERS,
    get_terrain_properties,
    get_predefined_modifier,
    create_modifier,
)


class TestTerrainType:
    """Test TerrainType enum."""

    def test_basic_types(self):
        """Test basic terrain types exist."""
        assert TerrainType.ROCK.value == "rock"
        assert TerrainType.WATER.value == "water"
        assert TerrainType.VOID.value == "void"

    def test_all_types_have_properties(self):
        """Test all terrain types have defined properties."""
        for terrain_type in TerrainType:
            props = get_terrain_properties(terrain_type)
            assert "passable" in props
            assert "opaque" in props
            assert "movement_cost" in props


class TestFluidType:
    """Test FluidType enum."""

    def test_fluid_types(self):
        """Test fluid types exist."""
        assert FluidType.WATER.value == "water"
        assert FluidType.LAVA.value == "lava"
        assert FluidType.GAS.value == "gas"


class TestTerrainProperties:
    """Test terrain property definitions."""

    def test_rock_properties(self):
        """Test rock terrain properties."""
        props = get_terrain_properties(TerrainType.ROCK)
        assert props["passable"] is False
        assert props["opaque"] is True
        assert "climbable" in props["affordances"]
        assert "mineable" in props["affordances"]

    def test_water_properties(self):
        """Test water terrain properties."""
        props = get_terrain_properties(TerrainType.WATER)
        assert props["passable"] is True
        assert props["movement_cost"] > 1.0
        assert "swimmable" in props["affordances"]

    def test_void_properties(self):
        """Test void terrain properties."""
        props = get_terrain_properties(TerrainType.VOID)
        assert props["passable"] is False
        assert props["movement_cost"] == float('inf')
        assert "fallable" in props["affordances"]

    def test_floor_properties(self):
        """Test basic floor properties."""
        props = get_terrain_properties(TerrainType.FLOOR)
        assert props["passable"] is True
        assert props["movement_cost"] == 1.0


class TestTerrainModifier:
    """Test TerrainModifier class."""

    def test_default_modifier(self):
        """Test default modifier values."""
        mod = TerrainModifier(type="test")
        assert mod.type == "test"
        assert mod.intensity == 1.0
        assert mod.movement_cost_modifier == 1.0

    def test_wet_modifier(self):
        """Test wet modifier properties."""
        mod = get_predefined_modifier("wet")
        assert mod is not None
        assert "slippery" in mod.adds_affordances
        assert "flammable" in mod.removes_affordances
        assert mod.movement_cost_modifier > 1.0

    def test_frozen_modifier(self):
        """Test frozen modifier properties."""
        mod = get_predefined_modifier("frozen")
        assert mod is not None
        assert "slippery" in mod.adds_affordances
        assert "swimmable" in mod.removes_affordances

    def test_apply_to_affordances(self):
        """Test applying modifier to affordances."""
        mod = TerrainModifier(
            type="test",
            adds_affordances=["new_ability"],
            removes_affordances=["old_ability"],
        )
        initial = {"old_ability", "keep_this"}
        result = mod.apply_to_affordances(initial)
        assert "new_ability" in result
        assert "old_ability" not in result
        assert "keep_this" in result

    def test_modifier_serialization(self):
        """Test modifier serialization."""
        mod = TerrainModifier(
            type="custom",
            intensity=0.5,
            adds_affordances=["test"],
            movement_cost_modifier=1.5,
        )
        data = mod.to_dict()
        restored = TerrainModifier.from_dict(data)
        assert restored.type == mod.type
        assert restored.intensity == mod.intensity
        assert restored.adds_affordances == mod.adds_affordances
        assert restored.movement_cost_modifier == mod.movement_cost_modifier


class TestCreateModifier:
    """Test create_modifier function."""

    def test_create_predefined(self):
        """Test creating from predefined type."""
        mod = create_modifier("wet", intensity=0.5)
        assert mod.type == "wet"
        assert mod.intensity == 0.5
        assert "slippery" in mod.adds_affordances

    def test_create_custom(self):
        """Test creating custom modifier."""
        mod = create_modifier(
            "custom_mod",
            intensity=0.8,
            adds_affordances=["special"],
        )
        assert mod.type == "custom_mod"
        assert mod.intensity == 0.8
        assert "special" in mod.adds_affordances

    def test_create_with_override(self):
        """Test creating predefined with overrides."""
        mod = create_modifier(
            "wet",
            intensity=1.0,
            movement_cost_modifier=2.0,
        )
        assert mod.type == "wet"
        assert mod.movement_cost_modifier == 2.0
