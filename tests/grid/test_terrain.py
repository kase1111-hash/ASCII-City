"""
Comprehensive tests for terrain types and modifiers.
"""

import pytest
from shadowengine.grid import TerrainType, TerrainModifier, FluidType
from shadowengine.grid.terrain import TERRAIN_DEFAULTS, TERRAIN_COST, MODIFIER_DEFAULTS


class TestTerrainTypeProperties:
    """Tests for TerrainType enum and properties."""

    @pytest.mark.unit
    def test_all_terrain_types_exist(self, all_terrain_types):
        """All expected terrain types exist."""
        expected = {"ROCK", "WATER", "SOIL", "METAL", "VOID", "WOOD", "GLASS"}
        actual = {t.name for t in all_terrain_types}
        assert actual == expected

    @pytest.mark.unit
    def test_terrain_default_properties(self, all_terrain_types):
        """Each terrain type has default properties."""
        for terrain in all_terrain_types:
            props = terrain.get_default_properties()
            assert "passable" in props
            assert "opaque" in props
            assert "affordances" in props
            assert "movement_cost" in props

    @pytest.mark.unit
    def test_rock_properties(self):
        """Rock terrain has correct properties."""
        props = TerrainType.ROCK.get_default_properties()
        assert props["passable"] is False
        assert props["opaque"] is True
        assert "mineable" in props["affordances"]
        assert "solid" in props["affordances"]

    @pytest.mark.unit
    def test_water_properties(self):
        """Water terrain has correct properties."""
        props = TerrainType.WATER.get_default_properties()
        assert props["passable"] is True  # Partial - with swimming
        assert props["opaque"] is False
        assert "swimmable" in props["affordances"]
        assert "drownable" in props["affordances"]

    @pytest.mark.unit
    def test_soil_properties(self):
        """Soil terrain has correct properties."""
        props = TerrainType.SOIL.get_default_properties()
        assert props["passable"] is True
        assert props["opaque"] is False
        assert "diggable" in props["affordances"]
        assert "plantable" in props["affordances"]

    @pytest.mark.unit
    def test_metal_properties(self):
        """Metal terrain has correct properties."""
        props = TerrainType.METAL.get_default_properties()
        assert props["passable"] is True
        assert props["opaque"] is True
        assert "conductive" in props["affordances"]
        assert "resonant" in props["affordances"]

    @pytest.mark.unit
    def test_void_properties(self):
        """Void terrain has correct properties."""
        props = TerrainType.VOID.get_default_properties()
        assert props["passable"] is False
        assert props["opaque"] is False
        assert "fallable" in props["affordances"]
        assert "echoing" in props["affordances"]

    @pytest.mark.unit
    def test_wood_properties(self):
        """Wood terrain has correct properties."""
        props = TerrainType.WOOD.get_default_properties()
        assert props["passable"] is True
        assert props["opaque"] is True
        assert "flammable" in props["affordances"]
        assert "breakable" in props["affordances"]

    @pytest.mark.unit
    def test_glass_properties(self):
        """Glass terrain has correct properties."""
        props = TerrainType.GLASS.get_default_properties()
        assert props["passable"] is False
        assert props["opaque"] is False  # Transparent
        assert "breakable" in props["affordances"]
        assert "transparent" in props["affordances"]

    @pytest.mark.unit
    def test_is_passable_by_default(self, passable_terrains, impassable_terrains):
        """Passability check works correctly."""
        for terrain in passable_terrains:
            assert terrain.is_passable_by_default() is True

        for terrain in impassable_terrains:
            assert terrain.is_passable_by_default() is False

    @pytest.mark.unit
    def test_is_opaque_by_default(self):
        """Opacity check works correctly."""
        assert TerrainType.ROCK.is_opaque_by_default() is True
        assert TerrainType.METAL.is_opaque_by_default() is True
        assert TerrainType.WOOD.is_opaque_by_default() is True
        assert TerrainType.WATER.is_opaque_by_default() is False
        assert TerrainType.GLASS.is_opaque_by_default() is False
        assert TerrainType.VOID.is_opaque_by_default() is False

    @pytest.mark.unit
    def test_get_default_affordances(self):
        """Can get default affordances."""
        affordances = TerrainType.WOOD.get_default_affordances()
        assert isinstance(affordances, set)
        assert "flammable" in affordances
        assert "climbable" in affordances

    @pytest.mark.unit
    def test_affordances_are_copies(self):
        """Affordance sets are copies, not references."""
        aff1 = TerrainType.WOOD.get_default_affordances()
        aff2 = TerrainType.WOOD.get_default_affordances()
        aff1.add("test")
        assert "test" not in aff2


class TestTerrainCosts:
    """Tests for terrain movement costs."""

    @pytest.mark.unit
    def test_all_terrains_have_costs(self, all_terrain_types):
        """All terrain types have movement costs defined."""
        for terrain in all_terrain_types:
            assert terrain in TERRAIN_COST

    @pytest.mark.unit
    def test_impassable_terrain_cost(self):
        """Impassable terrains have high movement cost."""
        assert TERRAIN_COST[TerrainType.ROCK] >= 999
        assert TERRAIN_COST[TerrainType.VOID] >= 999
        assert TERRAIN_COST[TerrainType.GLASS] >= 999

    @pytest.mark.unit
    def test_normal_terrain_cost(self):
        """Normal terrains have standard movement cost."""
        assert TERRAIN_COST[TerrainType.SOIL] == 1.0
        assert TERRAIN_COST[TerrainType.WOOD] == 1.0
        assert TERRAIN_COST[TerrainType.METAL] == 1.0

    @pytest.mark.unit
    def test_water_terrain_cost(self):
        """Water has increased movement cost."""
        assert TERRAIN_COST[TerrainType.WATER] > 1.0


class TestTerrainModifier:
    """Tests for TerrainModifier class."""

    @pytest.mark.unit
    def test_create_modifier_basic(self, wet_modifier):
        """Can create a basic modifier."""
        assert wet_modifier.type == "wet"
        assert wet_modifier.intensity == 0.8

    @pytest.mark.unit
    def test_create_modifier_default_intensity(self):
        """Default intensity is 1.0."""
        mod = TerrainModifier(type="frozen")
        assert mod.intensity == 1.0

    @pytest.mark.unit
    def test_modifier_intensity_validation(self):
        """Intensity must be between 0 and 1."""
        with pytest.raises(ValueError):
            TerrainModifier(type="wet", intensity=-0.1)

        with pytest.raises(ValueError):
            TerrainModifier(type="wet", intensity=1.5)

    @pytest.mark.unit
    def test_modifier_type_validation(self):
        """Modifier type must be valid."""
        with pytest.raises(ValueError):
            TerrainModifier(type="invalid_type")

    @pytest.mark.unit
    def test_valid_modifier_types(self):
        """All valid modifier types work."""
        valid_types = ["wet", "frozen", "cracked", "overgrown", "scorched", "rusty", "mossy"]
        for mod_type in valid_types:
            mod = TerrainModifier(type=mod_type)
            assert mod.type == mod_type

    @pytest.mark.unit
    def test_modifier_default_affects(self, wet_modifier):
        """Modifiers get default affects from type."""
        assert "passable" in wet_modifier.affects or "affordances" in wet_modifier.affects

    @pytest.mark.unit
    def test_modifier_custom_affects(self):
        """Can specify custom affects."""
        mod = TerrainModifier(type="wet", affects={"visibility", "movement"})
        assert "visibility" in mod.affects
        assert "movement" in mod.affects

    @pytest.mark.unit
    def test_modifier_get_effects(self, wet_modifier):
        """Can get modifier effects."""
        effects = wet_modifier.get_effects()
        assert isinstance(effects, dict)

    @pytest.mark.unit
    def test_frozen_modifier_effects(self, frozen_modifier):
        """Frozen modifier has correct effects."""
        effects = frozen_modifier.get_effects()
        assert "makes_passable" in effects or "adds_affordances" in effects

    @pytest.mark.unit
    def test_cracked_modifier_effects(self, cracked_modifier):
        """Cracked modifier has stability reduction."""
        effects = cracked_modifier.get_effects()
        assert "stability_reduction" in effects or "adds_affordances" in effects

    @pytest.mark.unit
    def test_modifier_intensity_scales_effects(self):
        """Effects are scaled by intensity."""
        mod1 = TerrainModifier(type="cracked", intensity=1.0)
        mod2 = TerrainModifier(type="cracked", intensity=0.5)

        effects1 = mod1.get_effects()
        effects2 = mod2.get_effects()

        # Numeric effects should be scaled
        if "stability_reduction" in effects1:
            assert effects2["stability_reduction"] < effects1["stability_reduction"]

    @pytest.mark.unit
    def test_modifier_serialization(self, wet_modifier):
        """Modifier can be serialized to dict."""
        data = wet_modifier.to_dict()
        assert data["type"] == "wet"
        assert data["intensity"] == 0.8
        assert isinstance(data["affects"], list)

    @pytest.mark.unit
    def test_modifier_deserialization(self, wet_modifier):
        """Modifier can be deserialized from dict."""
        data = wet_modifier.to_dict()
        restored = TerrainModifier.from_dict(data)
        assert restored.type == wet_modifier.type
        assert restored.intensity == wet_modifier.intensity


class TestFluidType:
    """Tests for FluidType enum."""

    @pytest.mark.unit
    def test_all_fluid_types_exist(self):
        """All expected fluid types exist."""
        expected = {"NONE", "WATER", "LAVA", "GAS", "OIL", "ACID"}
        actual = {f.name for f in FluidType}
        assert actual == expected

    @pytest.mark.unit
    def test_fluid_properties(self):
        """Each fluid type has properties."""
        for fluid in FluidType:
            props = fluid.get_properties()
            assert "dangerous" in props
            assert "movement_modifier" in props
            assert "visibility_modifier" in props

    @pytest.mark.unit
    def test_none_fluid_properties(self):
        """NONE fluid is not dangerous."""
        props = FluidType.NONE.get_properties()
        assert props["dangerous"] is False
        assert props["movement_modifier"] == 1.0
        assert props["visibility_modifier"] == 1.0

    @pytest.mark.unit
    def test_water_fluid_properties(self):
        """Water fluid properties."""
        props = FluidType.WATER.get_properties()
        assert props["dangerous"] is False
        assert props["movement_modifier"] > 1.0

    @pytest.mark.unit
    def test_lava_fluid_properties(self):
        """Lava is dangerous."""
        props = FluidType.LAVA.get_properties()
        assert props["dangerous"] is True
        assert props["movement_modifier"] > 1.0
        assert "damage_per_turn" in props

    @pytest.mark.unit
    def test_acid_fluid_properties(self):
        """Acid is dangerous."""
        props = FluidType.ACID.get_properties()
        assert props["dangerous"] is True
        assert "damage_per_turn" in props

    @pytest.mark.unit
    def test_oil_is_flammable(self):
        """Oil is flammable."""
        props = FluidType.OIL.get_properties()
        assert props.get("flammable") is True

    @pytest.mark.unit
    def test_gas_reduces_visibility(self):
        """Gas significantly reduces visibility."""
        props = FluidType.GAS.get_properties()
        assert props["visibility_modifier"] < 0.5


class TestModifierDefaults:
    """Tests for modifier default configurations."""

    @pytest.mark.unit
    def test_all_modifier_defaults_exist(self):
        """All modifier types have defaults."""
        expected_types = {"wet", "frozen", "cracked", "overgrown", "scorched", "rusty", "mossy"}
        assert expected_types <= set(MODIFIER_DEFAULTS.keys())

    @pytest.mark.unit
    def test_modifier_defaults_have_required_fields(self):
        """Modifier defaults have required fields."""
        for mod_type, defaults in MODIFIER_DEFAULTS.items():
            assert "affects" in defaults
            assert "adds_affordances" in defaults

    @pytest.mark.unit
    def test_wet_adds_slippery(self):
        """Wet modifier adds slippery affordance."""
        assert "slippery" in MODIFIER_DEFAULTS["wet"]["adds_affordances"]

    @pytest.mark.unit
    def test_frozen_adds_slippery(self):
        """Frozen modifier adds slippery affordance."""
        assert "slippery" in MODIFIER_DEFAULTS["frozen"]["adds_affordances"]

    @pytest.mark.unit
    def test_frozen_removes_swimmable(self):
        """Frozen modifier removes swimmable affordance."""
        assert "swimmable" in MODIFIER_DEFAULTS["frozen"]["removes_affordances"]

    @pytest.mark.unit
    def test_scorched_removes_flammable(self):
        """Scorched modifier removes flammable affordance."""
        assert "flammable" in MODIFIER_DEFAULTS["scorched"]["removes_affordances"]

    @pytest.mark.unit
    def test_overgrown_adds_hideable(self):
        """Overgrown modifier adds hideable affordance."""
        assert "hideable" in MODIFIER_DEFAULTS["overgrown"]["adds_affordances"]
