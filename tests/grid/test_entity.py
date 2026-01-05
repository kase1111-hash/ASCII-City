"""Tests for Entity class and related components."""

import pytest

from src.shadowengine.grid.entity import (
    Layer,
    EntityType,
    Size,
    Entity,
    MAX_LAYER_SIZE,
    create_item,
    create_furniture,
    create_creature,
    create_feature,
)


class TestLayer:
    """Test Layer enum."""

    def test_layer_values(self):
        """Test layer values."""
        assert Layer.GROUND.value == 0
        assert Layer.OBJECT.value == 1
        assert Layer.CEILING.value == 2

    def test_layer_ordering(self):
        """Test layer ordering."""
        assert Layer.GROUND.value < Layer.OBJECT.value < Layer.CEILING.value


class TestEntityType:
    """Test EntityType enum."""

    def test_entity_types(self):
        """Test entity type values."""
        assert EntityType.ITEM.value == "item"
        assert EntityType.CREATURE.value == "creature"
        assert EntityType.FEATURE.value == "feature"


class TestSize:
    """Test Size class."""

    def test_default_size(self):
        """Test default size values."""
        size = Size()
        assert size.width == 1.0
        assert size.height == 1.0
        assert size.depth == 1.0

    def test_custom_size(self):
        """Test custom size values."""
        size = Size(2.0, 1.5, 0.5)
        assert size.width == 2.0
        assert size.height == 1.5
        assert size.depth == 0.5

    def test_volume(self):
        """Test volume calculation."""
        size = Size(2.0, 3.0, 4.0)
        assert size.volume() == 24.0

    def test_to_tuple(self):
        """Test conversion to tuple."""
        size = Size(1.0, 2.0, 3.0)
        assert size.to_tuple() == (1.0, 2.0, 3.0)

    def test_from_tuple(self):
        """Test creation from tuple."""
        size = Size.from_tuple((1.0, 2.0, 3.0))
        assert size.width == 1.0
        assert size.height == 2.0
        assert size.depth == 3.0


class TestEntity:
    """Test Entity class."""

    def test_entity_creation(self):
        """Test creating an entity."""
        entity = Entity(name="Test Entity")
        assert entity.name == "Test Entity"
        assert entity.id is not None
        assert entity.entity_type == EntityType.ITEM
        assert entity.layer == Layer.OBJECT

    def test_entity_with_type(self):
        """Test entity with specific type."""
        entity = Entity(
            name="Guard",
            entity_type=EntityType.CHARACTER,
            layer=Layer.OBJECT,
        )
        assert entity.entity_type == EntityType.CHARACTER

    def test_entity_affordances(self):
        """Test entity own affordances."""
        entity = Entity(
            name="Key",
            own_affordances=["collectible", "usable"],
        )
        assert entity.has_affordance("collectible")
        assert entity.has_affordance("usable")

    def test_add_affordance(self):
        """Test adding an affordance."""
        entity = Entity(name="Test")
        entity.add_affordance("special")
        assert entity.has_affordance("special")

    def test_remove_affordance(self):
        """Test removing an affordance."""
        entity = Entity(name="Test", own_affordances=["removable"])
        entity.remove_affordance("removable")
        assert not entity.has_affordance("removable")

    def test_block_affordance(self):
        """Test blocking an affordance."""
        entity = Entity(name="Test")
        entity.block_affordance("blocked")
        assert entity.blocks_affordance("blocked")

    def test_unblock_affordance(self):
        """Test unblocking an affordance."""
        entity = Entity(name="Test", blocked_affordances=["blocked"])
        entity.unblock_affordance("blocked")
        assert not entity.blocks_affordance("blocked")

    def test_effective_affordances(self):
        """Test calculating effective affordances."""
        entity = Entity(
            name="Test",
            own_affordances=["special"],
            blocked_affordances=["blocked"],
        )
        tile_affordances = ["tile_aff", "blocked"]
        effective = entity.get_effective_affordances(tile_affordances)
        assert "special" in effective
        assert "tile_aff" in effective
        assert "blocked" not in effective

    def test_movement_modifier(self):
        """Test movement modifier by terrain."""
        entity = Entity(
            name="Test",
            movement_modifiers={"water": 0.5, "rock": 2.0},
        )
        assert entity.get_movement_modifier("water") == 0.5
        assert entity.get_movement_modifier("rock") == 2.0
        assert entity.get_movement_modifier("unknown") == 1.0

    def test_entity_conflicts(self):
        """Test entity conflict detection."""
        entity1 = Entity(
            name="E1",
            layer=Layer.OBJECT,
            blocks_movement=True,
        )
        entity2 = Entity(
            name="E2",
            layer=Layer.OBJECT,
            blocks_movement=True,
        )
        entity3 = Entity(
            name="E3",
            layer=Layer.GROUND,
            blocks_movement=True,
        )
        # Same layer, both block = conflict
        assert entity1.conflicts_with(entity2)
        # Different layers = no conflict
        assert not entity1.conflicts_with(entity3)

    def test_entity_serialization(self):
        """Test entity serialization."""
        entity = Entity(
            id="test_id",
            name="Test Entity",
            description="A test entity",
            entity_type=EntityType.FURNITURE,
            layer=Layer.OBJECT,
            size=Size(2.0, 1.0, 1.0),
            blocks_movement=True,
            own_affordances=["usable"],
            circuit_id="circuit_1",
        )
        data = entity.to_dict()
        restored = Entity.from_dict(data)

        assert restored.id == entity.id
        assert restored.name == entity.name
        assert restored.entity_type == entity.entity_type
        assert restored.layer == entity.layer
        assert restored.size.width == 2.0
        assert restored.blocks_movement is True
        assert "usable" in restored.own_affordances
        assert restored.circuit_id == "circuit_1"


class TestEntityFactories:
    """Test entity factory functions."""

    def test_create_item(self):
        """Test creating an item entity."""
        item = create_item("Gold Coin", "A shiny coin")
        assert item.name == "Gold Coin"
        assert item.entity_type == EntityType.ITEM
        assert item.layer == Layer.GROUND
        assert item.blocks_movement is False
        assert "collectible" in item.own_affordances

    def test_create_furniture(self):
        """Test creating furniture entity."""
        furniture = create_furniture("Table", blocks=True)
        assert furniture.name == "Table"
        assert furniture.entity_type == EntityType.FURNITURE
        assert furniture.blocks_movement is True
        assert "usable" in furniture.own_affordances

    def test_create_furniture_non_blocking(self):
        """Test creating non-blocking furniture."""
        rug = create_furniture("Rug", blocks=False)
        assert rug.blocks_movement is False

    def test_create_creature(self):
        """Test creating creature entity."""
        creature = create_creature("Wolf")
        assert creature.name == "Wolf"
        assert creature.entity_type == EntityType.CREATURE
        assert creature.blocks_movement is True
        assert "fightable" in creature.own_affordances
        assert "observable" in creature.own_affordances

    def test_create_feature(self):
        """Test creating feature entity."""
        door = create_feature("Door", blocks=True, affordances=["openable", "lockable"])
        assert door.name == "Door"
        assert door.entity_type == EntityType.FEATURE
        assert door.blocks_movement is True
        assert door.requires_passable is False
        assert "openable" in door.own_affordances

    def test_create_with_custom_affordances(self):
        """Test creating entities with custom affordances."""
        item = create_item("Magic Ring", affordances=["wearable", "magical"])
        assert "wearable" in item.own_affordances
        assert "magical" in item.own_affordances
