"""
Comprehensive tests for Entity class.
"""

import pytest
from shadowengine.grid import (
    Position, Entity, EntityType, Layer
)
from shadowengine.grid.entity import MAX_LAYER_SIZE, conflicts


class TestEntityCreation:
    """Tests for Entity creation."""

    @pytest.mark.unit
    def test_create_basic_entity(self, basic_entity):
        """Can create a basic entity."""
        assert basic_entity.id == "test_entity"
        assert basic_entity.name == "Test Entity"
        assert basic_entity.entity_type == EntityType.ITEM
        assert basic_entity.size == 1
        assert basic_entity.layer == Layer.OBJECT

    @pytest.mark.unit
    def test_create_character_entity(self, character_entity):
        """Can create a character entity."""
        assert character_entity.entity_type == EntityType.CHARACTER
        assert character_entity.passable is False

    @pytest.mark.unit
    def test_entity_default_values(self):
        """Entity has correct defaults."""
        entity = Entity(
            id="test",
            name="Test",
            entity_type=EntityType.ITEM
        )
        assert entity.position is None
        assert entity.size == 1
        assert entity.layer == Layer.OBJECT
        assert entity.passable is True
        assert entity.opaque is False
        assert len(entity.own_affordances) == 0
        assert len(entity.blocked_affordances) == 0
        assert entity.requires_passable is True

    @pytest.mark.unit
    def test_entity_size_validation(self):
        """Entity size must be between 1 and MAX_LAYER_SIZE."""
        with pytest.raises(ValueError):
            Entity(id="test", name="Test", entity_type=EntityType.ITEM, size=0)

        with pytest.raises(ValueError):
            Entity(id="test", name="Test", entity_type=EntityType.ITEM, size=MAX_LAYER_SIZE + 1)

    @pytest.mark.unit
    def test_entity_valid_sizes(self):
        """All valid sizes work."""
        for size in range(1, MAX_LAYER_SIZE + 1):
            entity = Entity(id=f"test{size}", name="Test", entity_type=EntityType.ITEM, size=size)
            assert entity.size == size


class TestEntityTypes:
    """Tests for EntityType enum."""

    @pytest.mark.unit
    def test_all_entity_types_exist(self):
        """All expected entity types exist."""
        expected = {
            "CHARACTER", "CREATURE", "ITEM", "FURNITURE",
            "DECORATION", "TRIGGER", "LIGHT_SOURCE", "CONTAINER"
        }
        actual = {t.name for t in EntityType}
        assert actual == expected

    @pytest.mark.unit
    def test_character_entity_type(self, character_entity):
        """Character has CHARACTER type."""
        assert character_entity.entity_type == EntityType.CHARACTER

    @pytest.mark.unit
    def test_furniture_entity_type(self, furniture_entity):
        """Furniture has FURNITURE type."""
        assert furniture_entity.entity_type == EntityType.FURNITURE

    @pytest.mark.unit
    def test_trigger_entity_type(self, trigger_entity):
        """Trigger has TRIGGER type."""
        assert trigger_entity.entity_type == EntityType.TRIGGER


class TestEntityLayers:
    """Tests for Layer enum and layer placement."""

    @pytest.mark.unit
    def test_all_layers_exist(self):
        """All expected layers exist."""
        assert Layer.GROUND.value == 0
        assert Layer.OBJECT.value == 1
        assert Layer.CEILING.value == 2

    @pytest.mark.unit
    def test_ground_layer_entity(self, trigger_entity):
        """Trigger is on ground layer."""
        assert trigger_entity.layer == Layer.GROUND

    @pytest.mark.unit
    def test_object_layer_entity(self, basic_entity):
        """Items are on object layer by default."""
        assert basic_entity.layer == Layer.OBJECT

    @pytest.mark.unit
    def test_ceiling_layer_entity(self, light_source_entity):
        """Light source is on ceiling layer."""
        assert light_source_entity.layer == Layer.CEILING


class TestEntityPlacement:
    """Tests for entity placement logic."""

    @pytest.mark.unit
    def test_can_be_placed_on_passable(self, basic_entity):
        """Entity can be placed on passable terrain."""
        assert basic_entity.can_be_placed_on(terrain_passable=True) is True

    @pytest.mark.unit
    def test_cannot_be_placed_on_impassable(self, basic_entity):
        """Entity requiring passable cannot be on impassable terrain."""
        assert basic_entity.can_be_placed_on(terrain_passable=False) is False

    @pytest.mark.unit
    def test_non_requiring_entity_on_impassable(self):
        """Entity not requiring passable can be on any terrain."""
        entity = Entity(
            id="ghost",
            name="Ghost",
            entity_type=EntityType.CREATURE,
            requires_passable=False
        )
        assert entity.can_be_placed_on(terrain_passable=False) is True


class TestEntityAffordances:
    """Tests for entity affordance system."""

    @pytest.mark.unit
    def test_get_own_affordances(self, light_source_entity):
        """Can get entity's own affordances."""
        affordances = light_source_entity.get_affordances()
        assert "illuminating" in affordances
        assert "flammable" in affordances

    @pytest.mark.unit
    def test_affordances_are_copies(self, light_source_entity):
        """Affordance set is a copy."""
        aff1 = light_source_entity.get_affordances()
        aff2 = light_source_entity.get_affordances()
        aff1.add("test")
        assert "test" not in aff2

    @pytest.mark.unit
    def test_blocks_affordance(self):
        """Can check if entity blocks an affordance."""
        entity = Entity(
            id="cover",
            name="Cover",
            entity_type=EntityType.FURNITURE,
            blocked_affordances={"diggable", "plantable"}
        )
        assert entity.blocks_affordance("diggable") is True
        assert entity.blocks_affordance("walkable") is False


class TestEntityConflicts:
    """Tests for entity conflict detection."""

    @pytest.mark.unit
    def test_no_conflict_different_layers(self, basic_entity, trigger_entity):
        """Entities on different layers don't conflict."""
        assert conflicts(basic_entity, trigger_entity) is False

    @pytest.mark.unit
    def test_characters_conflict(self):
        """Two characters always conflict."""
        char1 = Entity(id="c1", name="C1", entity_type=EntityType.CHARACTER)
        char2 = Entity(id="c2", name="C2", entity_type=EntityType.CHARACTER)
        assert conflicts(char1, char2) is True

    @pytest.mark.unit
    def test_impassable_entities_conflict(self):
        """Impassable entities conflict."""
        e1 = Entity(id="e1", name="E1", entity_type=EntityType.FURNITURE, passable=False)
        e2 = Entity(id="e2", name="E2", entity_type=EntityType.FURNITURE, passable=True)
        assert conflicts(e1, e2) is True

    @pytest.mark.unit
    def test_passable_entities_no_conflict(self):
        """Passable entities don't conflict."""
        e1 = Entity(id="e1", name="E1", entity_type=EntityType.ITEM, passable=True)
        e2 = Entity(id="e2", name="E2", entity_type=EntityType.ITEM, passable=True)
        assert conflicts(e1, e2) is False


class TestEntitySerialization:
    """Tests for entity serialization."""

    @pytest.mark.unit
    def test_entity_serialize(self, basic_entity):
        """Can serialize entity to dict."""
        data = basic_entity.serialize()
        assert data["id"] == "test_entity"
        assert data["name"] == "Test Entity"
        assert data["entity_type"] == "ITEM"
        assert data["size"] == 1
        assert data["layer"] == "OBJECT"

    @pytest.mark.unit
    def test_entity_serialize_with_position(self, basic_entity):
        """Serialization includes position."""
        basic_entity.position = Position(5, 5, 0)
        data = basic_entity.serialize()
        assert data["position"] == (5, 5, 0)

    @pytest.mark.unit
    def test_entity_serialize_without_position(self, basic_entity):
        """Serialization handles None position."""
        data = basic_entity.serialize()
        assert data["position"] is None

    @pytest.mark.unit
    def test_entity_from_dict(self, basic_entity):
        """Can deserialize entity from dict."""
        data = basic_entity.serialize()
        restored = Entity.from_dict(data)
        assert restored.id == basic_entity.id
        assert restored.name == basic_entity.name
        assert restored.entity_type == basic_entity.entity_type

    @pytest.mark.unit
    def test_entity_roundtrip(self, light_source_entity):
        """Entity survives serialization roundtrip."""
        light_source_entity.position = Position(10, 10, 2)
        data = light_source_entity.serialize()
        restored = Entity.from_dict(data)

        assert restored.id == light_source_entity.id
        assert restored.layer == light_source_entity.layer
        assert restored.own_affordances == light_source_entity.own_affordances
        assert restored.position == light_source_entity.position

    @pytest.mark.unit
    def test_entity_with_movement_modifiers(self):
        """Entity with movement modifiers serializes correctly."""
        entity = Entity(
            id="swimmer",
            name="Swimmer",
            entity_type=EntityType.CHARACTER,
            movement_modifiers={"WATER": 0.5, "SOIL": 1.0}
        )
        data = entity.serialize()
        restored = Entity.from_dict(data)
        assert restored.movement_modifiers == entity.movement_modifiers


class TestEntityEquality:
    """Tests for entity equality and hashing."""

    @pytest.mark.unit
    def test_entities_equal_by_id(self):
        """Entities with same ID are equal."""
        e1 = Entity(id="test", name="Test 1", entity_type=EntityType.ITEM)
        e2 = Entity(id="test", name="Test 2", entity_type=EntityType.FURNITURE)
        assert e1 == e2

    @pytest.mark.unit
    def test_entities_different_ids(self):
        """Entities with different IDs are not equal."""
        e1 = Entity(id="test1", name="Test", entity_type=EntityType.ITEM)
        e2 = Entity(id="test2", name="Test", entity_type=EntityType.ITEM)
        assert e1 != e2

    @pytest.mark.unit
    def test_entity_hash(self):
        """Entities can be used in sets."""
        e1 = Entity(id="test", name="Test 1", entity_type=EntityType.ITEM)
        e2 = Entity(id="test", name="Test 2", entity_type=EntityType.FURNITURE)

        entities = {e1, e2}
        assert len(entities) == 1

    @pytest.mark.unit
    def test_entity_as_dict_key(self, basic_entity):
        """Entities can be used as dictionary keys."""
        data = {basic_entity: "value"}
        assert data[basic_entity] == "value"
