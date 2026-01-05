"""
Comprehensive tests for Tile and TileEnvironment classes.
"""

import pytest
from shadowengine.grid import (
    Position, Tile, TileEnvironment,
    TerrainType, TerrainModifier, FluidType,
    Entity, EntityType, Layer
)


class TestTileEnvironmentCreation:
    """Tests for TileEnvironment creation."""

    @pytest.mark.unit
    def test_create_default_environment(self, default_environment):
        """Can create default environment."""
        assert default_environment.fluid == FluidType.NONE
        assert default_environment.temperature == 20.0
        assert default_environment.sound_level == 0.0
        assert 0.0 <= default_environment.light_level <= 1.0
        assert 0.0 <= default_environment.moisture <= 1.0

    @pytest.mark.unit
    def test_create_custom_environment(self):
        """Can create environment with custom values."""
        env = TileEnvironment(
            fluid=FluidType.WATER,
            temperature=15.0,
            sound_level=0.5,
            light_level=0.8,
            moisture=0.9
        )
        assert env.fluid == FluidType.WATER
        assert env.temperature == 15.0
        assert env.sound_level == 0.5
        assert env.light_level == 0.8
        assert env.moisture == 0.9

    @pytest.mark.unit
    def test_environment_temperature_validation(self):
        """Temperature must be in valid range."""
        with pytest.raises(ValueError):
            TileEnvironment(temperature=-150.0)

        with pytest.raises(ValueError):
            TileEnvironment(temperature=150.0)

    @pytest.mark.unit
    def test_environment_sound_level_validation(self):
        """Sound level must be between 0 and 1."""
        with pytest.raises(ValueError):
            TileEnvironment(sound_level=-0.1)

        with pytest.raises(ValueError):
            TileEnvironment(sound_level=1.5)

    @pytest.mark.unit
    def test_environment_light_level_validation(self):
        """Light level must be between 0 and 1."""
        with pytest.raises(ValueError):
            TileEnvironment(light_level=-0.1)

        with pytest.raises(ValueError):
            TileEnvironment(light_level=1.5)

    @pytest.mark.unit
    def test_environment_moisture_validation(self):
        """Moisture must be between 0 and 1."""
        with pytest.raises(ValueError):
            TileEnvironment(moisture=-0.1)

        with pytest.raises(ValueError):
            TileEnvironment(moisture=1.5)


class TestTileEnvironmentEffects:
    """Tests for TileEnvironment effect categorization."""

    @pytest.mark.unit
    def test_temperature_effect_freezing(self, freezing_environment):
        """Freezing temperature effect."""
        assert freezing_environment.get_temperature_effect() == "freezing"

    @pytest.mark.unit
    def test_temperature_effect_cold(self):
        """Cold temperature effect."""
        env = TileEnvironment(temperature=-10.0)
        assert env.get_temperature_effect() == "cold"

    @pytest.mark.unit
    def test_temperature_effect_comfortable(self, default_environment):
        """Comfortable temperature effect."""
        assert default_environment.get_temperature_effect() == "comfortable"

    @pytest.mark.unit
    def test_temperature_effect_hot(self, hot_environment):
        """Hot temperature effect."""
        assert hot_environment.get_temperature_effect() == "hot"

    @pytest.mark.unit
    def test_temperature_effect_extreme(self):
        """Extreme temperature effect."""
        env = TileEnvironment(temperature=60.0)
        assert env.get_temperature_effect() == "extreme"

    @pytest.mark.unit
    def test_moisture_effect_dry(self):
        """Dry moisture effect."""
        env = TileEnvironment(moisture=0.1)
        assert env.get_moisture_effect() == "dry"

    @pytest.mark.unit
    def test_moisture_effect_normal(self):
        """Normal moisture effect."""
        env = TileEnvironment(moisture=0.4)
        assert env.get_moisture_effect() == "normal"

    @pytest.mark.unit
    def test_moisture_effect_damp(self):
        """Damp moisture effect."""
        env = TileEnvironment(moisture=0.6)
        assert env.get_moisture_effect() == "damp"

    @pytest.mark.unit
    def test_moisture_effect_flooded(self, flooded_environment):
        """Flooded moisture effect."""
        assert flooded_environment.get_moisture_effect() == "flooded"

    @pytest.mark.unit
    def test_light_effect_pitch_black(self, dark_environment):
        """Pitch black light effect."""
        assert dark_environment.get_light_effect() == "pitch_black"

    @pytest.mark.unit
    def test_light_effect_dim(self):
        """Dim light effect."""
        env = TileEnvironment(light_level=0.2)
        assert env.get_light_effect() == "dim"

    @pytest.mark.unit
    def test_light_effect_normal(self, default_environment):
        """Normal light effect."""
        assert default_environment.get_light_effect() == "normal"

    @pytest.mark.unit
    def test_light_effect_bright(self):
        """Bright light effect."""
        env = TileEnvironment(light_level=0.9)
        assert env.get_light_effect() == "bright"


class TestTileEnvironmentSerialization:
    """Tests for TileEnvironment serialization."""

    @pytest.mark.unit
    def test_environment_to_dict(self, default_environment):
        """Can serialize environment to dict."""
        data = default_environment.to_dict()
        assert "fluid" in data
        assert "temperature" in data
        assert "sound_level" in data
        assert "light_level" in data
        assert "moisture" in data

    @pytest.mark.unit
    def test_environment_from_dict(self, default_environment):
        """Can deserialize environment from dict."""
        data = default_environment.to_dict()
        restored = TileEnvironment.from_dict(data)
        assert restored.fluid == default_environment.fluid
        assert restored.temperature == default_environment.temperature
        assert restored.light_level == default_environment.light_level

    @pytest.mark.unit
    def test_environment_roundtrip(self, flooded_environment):
        """Environment survives serialization roundtrip."""
        data = flooded_environment.to_dict()
        restored = TileEnvironment.from_dict(data)
        assert restored.fluid == flooded_environment.fluid
        assert restored.moisture == flooded_environment.moisture


class TestTileCreation:
    """Tests for Tile creation."""

    @pytest.mark.unit
    def test_create_basic_tile(self, basic_tile):
        """Can create a basic tile."""
        assert basic_tile.position == Position(5, 5, 0)
        assert basic_tile.terrain_type == TerrainType.SOIL
        assert basic_tile.passable is True
        assert basic_tile.opaque is False

    @pytest.mark.unit
    def test_create_tile_with_terrain(self, rock_tile):
        """Tile inherits terrain defaults."""
        assert rock_tile.passable is False
        assert rock_tile.opaque is True

    @pytest.mark.unit
    def test_create_tile_override_defaults(self):
        """Can override terrain defaults."""
        tile = Tile(
            position=Position(0, 0, 0),
            terrain_type=TerrainType.ROCK,
            passable=True  # Override rock's default
        )
        assert tile.passable is True

    @pytest.mark.unit
    def test_tile_default_entities_empty(self, basic_tile):
        """Tile starts with no entities."""
        assert len(basic_tile.entities) == 0

    @pytest.mark.unit
    def test_tile_default_modifiers_empty(self, basic_tile):
        """Tile starts with no modifiers."""
        assert len(basic_tile.modifiers) == 0

    @pytest.mark.unit
    def test_tile_default_stability(self, basic_tile):
        """Tile starts with full stability."""
        assert basic_tile.stability == 1.0


class TestTilePassability:
    """Tests for tile passability."""

    @pytest.mark.unit
    def test_soil_is_passable(self, basic_tile):
        """Soil tile is passable."""
        assert basic_tile.is_passable() is True

    @pytest.mark.unit
    def test_rock_is_not_passable(self, rock_tile):
        """Rock tile is not passable."""
        assert rock_tile.is_passable() is False

    @pytest.mark.unit
    def test_frozen_water_becomes_passable(self, water_tile, frozen_modifier):
        """Frozen water becomes passable."""
        water_tile.passable = False  # Unfrozen water might not be passable
        water_tile.add_modifier(frozen_modifier)
        assert water_tile.is_passable() is True

    @pytest.mark.unit
    def test_glass_is_not_passable(self, glass_tile):
        """Glass tile is not passable."""
        assert glass_tile.is_passable() is False


class TestTileOpacity:
    """Tests for tile opacity (line of sight blocking)."""

    @pytest.mark.unit
    def test_rock_is_opaque(self, rock_tile):
        """Rock blocks line of sight."""
        assert rock_tile.is_opaque() is True

    @pytest.mark.unit
    def test_glass_is_transparent(self, glass_tile):
        """Glass is transparent despite being impassable."""
        assert glass_tile.is_opaque() is False

    @pytest.mark.unit
    def test_soil_is_transparent(self, basic_tile):
        """Soil doesn't block line of sight."""
        assert basic_tile.is_opaque() is False

    @pytest.mark.unit
    def test_opaque_entity_blocks_los(self, basic_tile):
        """Opaque entity on tile blocks line of sight."""
        entity = Entity(
            id="wall",
            name="Wall",
            entity_type=EntityType.FURNITURE,
            opaque=True
        )
        basic_tile.add_entity(entity)
        assert basic_tile.is_opaque() is True


class TestTileAffordances:
    """Tests for tile affordance system."""

    @pytest.mark.unit
    def test_tile_gets_terrain_affordances(self, basic_tile):
        """Tile gets affordances from terrain type."""
        affordances = basic_tile.get_affordances()
        assert "diggable" in affordances
        assert "plantable" in affordances

    @pytest.mark.unit
    def test_wood_tile_is_flammable(self, wood_tile):
        """Wood tile has flammable affordance."""
        affordances = wood_tile.get_affordances()
        assert "flammable" in affordances

    @pytest.mark.unit
    def test_water_tile_is_swimmable(self, water_tile):
        """Water tile has swimmable affordance."""
        affordances = water_tile.get_affordances()
        assert "swimmable" in affordances

    @pytest.mark.unit
    def test_modifier_adds_affordances(self, basic_tile, wet_modifier):
        """Modifier adds affordances."""
        basic_tile.add_modifier(wet_modifier)
        affordances = basic_tile.get_affordances()
        assert "slippery" in affordances

    @pytest.mark.unit
    def test_high_moisture_adds_slippery(self, tile_with_flooded_env):
        """High moisture adds slippery affordance."""
        affordances = tile_with_flooded_env.get_affordances()
        assert "slippery" in affordances

    @pytest.mark.unit
    def test_high_moisture_removes_flammable(self, wood_tile):
        """High moisture removes flammable affordance."""
        wood_tile.environment.moisture = 0.9
        affordances = wood_tile.get_affordances()
        assert "flammable" not in affordances

    @pytest.mark.unit
    def test_dark_tile_is_hideable(self, tile_with_dark_env):
        """Dark tiles are hideable."""
        affordances = tile_with_dark_env.get_affordances()
        assert "hideable" in affordances

    @pytest.mark.unit
    def test_entity_affordances_included(self, basic_tile, trigger_entity):
        """Entity affordances are included."""
        basic_tile.add_entity(trigger_entity)
        affordances = basic_tile.get_affordances()
        assert "triggerable" in affordances

    @pytest.mark.unit
    def test_entity_blocked_affordances(self, basic_tile):
        """Entity can block tile affordances."""
        entity = Entity(
            id="cover",
            name="Cover",
            entity_type=EntityType.FURNITURE,
            blocked_affordances={"diggable"}
        )
        basic_tile.add_entity(entity)
        affordances = basic_tile.get_affordances()
        assert "diggable" not in affordances

    @pytest.mark.unit
    def test_get_entity_affordances(self, basic_tile, basic_entity):
        """Can get affordances for specific entity."""
        basic_entity.own_affordances = {"pickable"}
        basic_tile.add_entity(basic_entity)
        entity_affordances = basic_tile.get_entity_affordances(basic_entity)
        assert "pickable" in entity_affordances
        assert "diggable" in entity_affordances  # From tile


class TestTileModifiers:
    """Tests for tile modifiers."""

    @pytest.mark.unit
    def test_add_modifier(self, basic_tile, wet_modifier):
        """Can add modifier to tile."""
        basic_tile.add_modifier(wet_modifier)
        assert len(basic_tile.modifiers) == 1
        assert basic_tile.modifiers[0].type == "wet"

    @pytest.mark.unit
    def test_remove_modifier(self, basic_tile, wet_modifier):
        """Can remove modifier from tile."""
        basic_tile.add_modifier(wet_modifier)
        assert basic_tile.remove_modifier("wet") is True
        assert len(basic_tile.modifiers) == 0

    @pytest.mark.unit
    def test_remove_nonexistent_modifier(self, basic_tile):
        """Removing nonexistent modifier returns False."""
        assert basic_tile.remove_modifier("wet") is False

    @pytest.mark.unit
    def test_has_modifier(self, basic_tile, wet_modifier):
        """Can check if tile has modifier."""
        assert basic_tile.has_modifier("wet") is False
        basic_tile.add_modifier(wet_modifier)
        assert basic_tile.has_modifier("wet") is True

    @pytest.mark.unit
    def test_modifier_replaces_same_type(self, basic_tile):
        """Adding modifier of same type replaces existing."""
        mod1 = TerrainModifier(type="wet", intensity=0.5)
        mod2 = TerrainModifier(type="wet", intensity=1.0)

        basic_tile.add_modifier(mod1)
        basic_tile.add_modifier(mod2)

        assert len(basic_tile.modifiers) == 1
        assert basic_tile.modifiers[0].intensity == 1.0

    @pytest.mark.unit
    def test_cracked_modifier_reduces_stability(self, basic_tile, cracked_modifier):
        """Cracked modifier reduces tile stability."""
        initial_stability = basic_tile.stability
        basic_tile.add_modifier(cracked_modifier)
        assert basic_tile.stability < initial_stability


class TestTileMovementCost:
    """Tests for tile movement cost calculation."""

    @pytest.mark.unit
    def test_soil_movement_cost(self, basic_tile):
        """Soil has base movement cost."""
        cost = basic_tile.get_movement_cost()
        assert cost == 1.0

    @pytest.mark.unit
    def test_rock_movement_cost_high(self, rock_tile):
        """Rock has very high movement cost (impassable)."""
        cost = rock_tile.get_movement_cost()
        assert cost >= 999.0

    @pytest.mark.unit
    def test_water_movement_cost(self, water_tile):
        """Water has higher movement cost."""
        cost = water_tile.get_movement_cost()
        assert cost > 1.0

    @pytest.mark.unit
    def test_height_difference_increases_cost(self, basic_tile):
        """Height difference increases movement cost."""
        from_tile = Tile(position=Position(4, 5, 0), terrain_type=TerrainType.SOIL)
        from_tile.height = 0.0
        basic_tile.height = 2.0

        cost = basic_tile.get_movement_cost(from_tile=from_tile)
        assert cost > 1.0

    @pytest.mark.unit
    def test_flooded_increases_cost(self, tile_with_flooded_env):
        """Flooded environment increases movement cost."""
        cost = tile_with_flooded_env.get_movement_cost()
        assert cost > 1.0

    @pytest.mark.unit
    def test_dark_increases_cost(self, tile_with_dark_env):
        """Dark environment increases movement cost."""
        cost = tile_with_dark_env.get_movement_cost()
        assert cost > 1.0

    @pytest.mark.unit
    def test_entity_movement_modifier(self, basic_tile):
        """Entity can have terrain-specific movement modifiers."""
        entity = Entity(
            id="swimmer",
            name="Swimmer",
            entity_type=EntityType.CHARACTER,
            movement_modifiers={"SOIL": 0.5}  # Faster on soil
        )
        cost = basic_tile.get_movement_cost(entity=entity)
        assert cost < 1.0


class TestTileEntityManagement:
    """Tests for entity management on tiles."""

    @pytest.mark.unit
    def test_can_place_entity_basic(self, basic_tile, basic_entity):
        """Can place entity on passable tile."""
        assert basic_tile.can_place_entity(basic_entity) is True

    @pytest.mark.unit
    def test_cannot_place_on_impassable(self, rock_tile, basic_entity):
        """Cannot place entity requiring passable on impassable tile."""
        assert rock_tile.can_place_entity(basic_entity) is False

    @pytest.mark.unit
    def test_add_entity_success(self, basic_tile, basic_entity):
        """Can add entity to tile."""
        assert basic_tile.add_entity(basic_entity) is True
        assert basic_entity in basic_tile.entities
        assert basic_entity.position == basic_tile.position

    @pytest.mark.unit
    def test_add_entity_failure(self, rock_tile, basic_entity):
        """Adding entity to impassable tile fails."""
        assert rock_tile.add_entity(basic_entity) is False
        assert basic_entity not in rock_tile.entities

    @pytest.mark.unit
    def test_remove_entity(self, basic_tile, basic_entity):
        """Can remove entity from tile."""
        basic_tile.add_entity(basic_entity)
        assert basic_tile.remove_entity(basic_entity) is True
        assert basic_entity not in basic_tile.entities
        assert basic_entity.position is None

    @pytest.mark.unit
    def test_remove_nonexistent_entity(self, basic_tile, basic_entity):
        """Removing nonexistent entity returns False."""
        assert basic_tile.remove_entity(basic_entity) is False

    @pytest.mark.unit
    def test_get_entity_by_id(self, basic_tile, basic_entity):
        """Can get entity by ID."""
        basic_tile.add_entity(basic_entity)
        found = basic_tile.get_entity_by_id("test_entity")
        assert found == basic_entity

    @pytest.mark.unit
    def test_get_nonexistent_entity(self, basic_tile):
        """Getting nonexistent entity returns None."""
        assert basic_tile.get_entity_by_id("nonexistent") is None

    @pytest.mark.unit
    def test_get_entities_by_layer(self, basic_tile, basic_entity, trigger_entity):
        """Can get entities by layer."""
        basic_tile.add_entity(basic_entity)  # OBJECT layer
        basic_tile.add_entity(trigger_entity)  # GROUND layer

        object_entities = basic_tile.get_entities_by_layer(Layer.OBJECT)
        ground_entities = basic_tile.get_entities_by_layer(Layer.GROUND)

        assert basic_entity in object_entities
        assert trigger_entity in ground_entities
        assert trigger_entity not in object_entities

    @pytest.mark.unit
    def test_get_entities_by_type(self, basic_tile, basic_entity, character_entity):
        """Can get entities by type."""
        basic_tile.add_entity(basic_entity)  # ITEM type
        # Note: character_entity might not be placeable if passable=False
        item = Entity(id="item2", name="Item 2", entity_type=EntityType.ITEM)
        basic_tile.add_entity(item)

        items = basic_tile.get_entities_by_type(EntityType.ITEM)
        assert len(items) == 2

    @pytest.mark.unit
    def test_layer_capacity(self, basic_tile):
        """Layer has maximum capacity."""
        # MAX_LAYER_SIZE is 4
        for i in range(4):
            entity = Entity(id=f"e{i}", name=f"Entity {i}", entity_type=EntityType.ITEM, size=1)
            assert basic_tile.add_entity(entity) is True

        # Fifth should fail
        overflow = Entity(id="overflow", name="Overflow", entity_type=EntityType.ITEM, size=1)
        assert basic_tile.can_place_entity(overflow) is False

    @pytest.mark.unit
    def test_character_conflict(self, basic_tile):
        """Two characters cannot occupy same tile."""
        char1 = Entity(id="char1", name="Char 1", entity_type=EntityType.CHARACTER, size=1)
        char2 = Entity(id="char2", name="Char 2", entity_type=EntityType.CHARACTER, size=1)

        assert basic_tile.add_entity(char1) is True
        assert basic_tile.can_place_entity(char2) is False


class TestTileSerialization:
    """Tests for tile serialization."""

    @pytest.mark.unit
    def test_tile_serialize(self, basic_tile):
        """Can serialize tile to dict."""
        data = basic_tile.serialize()
        assert "position" in data
        assert "terrain" in data
        assert "passable" in data
        assert "environment" in data
        assert "affordances" in data

    @pytest.mark.unit
    def test_tile_from_dict(self, basic_tile):
        """Can deserialize tile from dict."""
        data = basic_tile.serialize()
        restored = Tile.from_dict(data)
        assert restored.position == basic_tile.position
        assert restored.terrain_type == basic_tile.terrain_type

    @pytest.mark.unit
    def test_tile_roundtrip(self, wood_tile, wet_modifier):
        """Tile survives serialization roundtrip."""
        wood_tile.add_modifier(wet_modifier)
        wood_tile.height = 1.5

        data = wood_tile.serialize()
        restored = Tile.from_dict(data)

        assert restored.terrain_type == wood_tile.terrain_type
        assert restored.height == wood_tile.height
        assert len(restored.modifiers) == len(wood_tile.modifiers)

    @pytest.mark.unit
    def test_tile_with_entities_serialization(self, basic_tile, basic_entity):
        """Tile with entities serializes entity IDs."""
        basic_tile.add_entity(basic_entity)
        data = basic_tile.serialize()
        assert "entities" in data
        assert basic_entity.id in data["entities"]


class TestTileEquality:
    """Tests for tile equality and hashing."""

    @pytest.mark.unit
    def test_tiles_equal_by_position(self):
        """Tiles with same position are equal."""
        tile1 = Tile(position=Position(5, 5, 0), terrain_type=TerrainType.SOIL)
        tile2 = Tile(position=Position(5, 5, 0), terrain_type=TerrainType.ROCK)
        assert tile1 == tile2

    @pytest.mark.unit
    def test_tiles_different_positions(self):
        """Tiles with different positions are not equal."""
        tile1 = Tile(position=Position(5, 5, 0), terrain_type=TerrainType.SOIL)
        tile2 = Tile(position=Position(6, 5, 0), terrain_type=TerrainType.SOIL)
        assert tile1 != tile2

    @pytest.mark.unit
    def test_tile_hash(self):
        """Tiles can be used in sets."""
        tile1 = Tile(position=Position(5, 5, 0), terrain_type=TerrainType.SOIL)
        tile2 = Tile(position=Position(5, 5, 0), terrain_type=TerrainType.ROCK)

        tiles = {tile1, tile2}
        assert len(tiles) == 1

    @pytest.mark.unit
    def test_tile_repr(self, basic_tile):
        """Tile has readable repr."""
        repr_str = repr(basic_tile)
        assert "Tile" in repr_str
        assert "SOIL" in repr_str
