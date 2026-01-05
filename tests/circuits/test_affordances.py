"""Tests for the affordance system."""

import pytest

from src.shadowengine.circuits.affordances import (
    Affordance,
    AffordanceSet,
    DEFAULT_AFFORDANCES,
    get_default_affordances,
    create_affordance_set,
)


class TestAffordance:
    """Test Affordance dataclass."""

    def test_simple_affordance(self):
        """Test creating a simple affordance."""
        aff = Affordance(name="pressable")
        assert aff.name == "pressable"
        assert aff.requires_tool is None
        assert aff.skill_required == 0.0

    def test_affordance_with_requirements(self):
        """Test affordance with requirements."""
        aff = Affordance(
            name="lockpick",
            requires_tool="lockpick",
            skill_required=0.5,
            energy_cost=0.2,
            cooldown=5.0
        )
        assert aff.requires_tool == "lockpick"
        assert aff.skill_required == 0.5
        assert aff.energy_cost == 0.2
        assert aff.cooldown == 5.0

    def test_can_use_no_requirements(self):
        """Test can_use when no requirements."""
        aff = Affordance(name="observable")
        assert aff.can_use() is True

    def test_can_use_missing_tool(self):
        """Test can_use when tool is missing."""
        aff = Affordance(name="pry_open", requires_tool="crowbar")
        assert aff.can_use(has_tool=False) is False

    def test_can_use_has_tool(self):
        """Test can_use when tool is available."""
        aff = Affordance(name="pry_open", requires_tool="crowbar")
        assert aff.can_use(has_tool=True) is True

    def test_can_use_insufficient_skill(self):
        """Test can_use when skill is insufficient."""
        aff = Affordance(name="hack", skill_required=0.7)
        assert aff.can_use(skill_level=0.3) is False

    def test_can_use_sufficient_skill(self):
        """Test can_use when skill is sufficient."""
        aff = Affordance(name="hack", skill_required=0.7)
        assert aff.can_use(skill_level=0.8) is True

    def test_can_use_insufficient_energy(self):
        """Test can_use when energy is low."""
        aff = Affordance(name="sprint", energy_cost=0.5)
        assert aff.can_use(energy=0.3) is False

    def test_can_use_sufficient_energy(self):
        """Test can_use when energy is sufficient."""
        aff = Affordance(name="sprint", energy_cost=0.5)
        assert aff.can_use(energy=0.7) is True

    def test_affordance_serialization(self):
        """Test affordance serialization."""
        aff = Affordance(
            name="unlock",
            requires_tool="key",
            cooldown=2.0
        )
        data = aff.to_dict()
        assert data["name"] == "unlock"
        assert data["requires_tool"] == "key"
        assert data["cooldown"] == 2.0

    def test_affordance_deserialization(self):
        """Test affordance deserialization."""
        data = {
            "name": "climb",
            "skill_required": 0.3,
            "energy_cost": 0.3
        }
        aff = Affordance.from_dict(data)
        assert aff.name == "climb"
        assert aff.skill_required == 0.3
        assert aff.energy_cost == 0.3


class TestAffordanceSet:
    """Test AffordanceSet class."""

    def test_empty_set(self):
        """Test creating empty affordance set."""
        aff_set = AffordanceSet()
        assert len(aff_set) == 0

    def test_set_with_affordances(self):
        """Test creating set with affordances."""
        aff_set = AffordanceSet(["look", "touch"])
        assert len(aff_set) == 2

    def test_add_affordance(self):
        """Test adding affordance."""
        aff_set = AffordanceSet()
        aff_set.add("kick")
        assert aff_set.has("kick")

    def test_add_affordance_with_details(self):
        """Test adding affordance with details."""
        aff_set = AffordanceSet()
        details = Affordance(name="hack", skill_required=0.5)
        aff_set.add("hack", details)
        assert aff_set.has("hack")
        assert aff_set.get_details("hack").skill_required == 0.5

    def test_remove_affordance(self):
        """Test removing affordance."""
        aff_set = AffordanceSet(["look", "touch"])
        aff_set.remove("look")
        assert not aff_set.has("look")
        assert aff_set.has("touch")

    def test_has_affordance(self):
        """Test checking if affordance exists."""
        aff_set = AffordanceSet(["pressable"])
        assert aff_set.has("pressable") is True
        assert aff_set.has("climbable") is False

    def test_get_details(self):
        """Test getting affordance details."""
        details = Affordance(name="hackable", skill_required=0.7)
        aff_set = AffordanceSet()
        aff_set.add("hackable", details)
        retrieved = aff_set.get_details("hackable")
        assert retrieved is not None
        assert retrieved.skill_required == 0.7

    def test_get_nonexistent_details(self):
        """Test getting details for affordance without details."""
        aff_set = AffordanceSet(["simple"])
        assert aff_set.get_details("simple") is None

    def test_get_all(self):
        """Test getting all affordances."""
        aff_set = AffordanceSet(["a", "b", "c"])
        all_affs = aff_set.get_all()
        assert set(all_affs) == {"a", "b", "c"}

    def test_block_affordance(self):
        """Test blocking affordance."""
        aff_set = AffordanceSet(["open", "close"])
        aff_set.block("open")
        blocked = aff_set.get_blocked()
        assert "open" in blocked

    def test_unblock_affordance(self):
        """Test unblocking affordance."""
        aff_set = AffordanceSet(["open"])
        aff_set.block("open")
        aff_set.unblock("open")
        blocked = aff_set.get_blocked()
        assert "open" not in blocked

    def test_blocked_not_in_has(self):
        """Test blocked affordances not available via has."""
        aff_set = AffordanceSet(["open", "close"])
        aff_set.block("open")
        assert aff_set.has("open") is False
        assert aff_set.has("close") is True

    def test_blocked_not_in_get_all(self):
        """Test blocked affordances not in get_all."""
        aff_set = AffordanceSet(["open", "close"])
        aff_set.block("open")
        all_affs = aff_set.get_all()
        assert "open" not in all_affs
        assert "close" in all_affs

    def test_inherit_from(self):
        """Test inheriting affordances from another set."""
        parent = AffordanceSet(["look", "touch"])
        child = AffordanceSet(["open"])
        child.inherit_from(parent)
        assert child.has("look")
        assert child.has("touch")
        assert child.has("open")

    def test_inherit_respects_blocked(self):
        """Test inherited affordances respect blocked list."""
        parent = AffordanceSet(["look", "touch"])
        child = AffordanceSet(["open"])
        child.block("look")  # Block before inheriting
        child.inherit_from(parent)
        assert child.has("look") is False  # Still blocked
        assert child.has("touch") is True

    def test_merge_with(self):
        """Test merging two affordance sets."""
        set1 = AffordanceSet(["a", "b"])
        set2 = AffordanceSet(["c", "d"])
        merged = set1.merge_with(set2)
        assert merged.has("a")
        assert merged.has("b")
        assert merged.has("c")
        assert merged.has("d")

    def test_serialization(self):
        """Test affordance set serialization."""
        aff_set = AffordanceSet(["open", "close"])
        aff_set.block("open")
        data = aff_set.to_dict()
        # Note: blocking removes from affordances set
        assert "close" in data["affordances"]
        assert "open" in data["blocked"]

    def test_deserialization(self):
        """Test affordance set deserialization."""
        data = {
            "affordances": ["climb", "jump"],
            "blocked": ["climb"],
            "details": {}
        }
        aff_set = AffordanceSet.from_dict(data)
        assert "climb" in aff_set.get_blocked()
        assert aff_set.has("jump")

    def test_contains_operator(self):
        """Test 'in' operator."""
        aff_set = AffordanceSet(["pressable"])
        assert "pressable" in aff_set
        assert "climbable" not in aff_set

    def test_iterator(self):
        """Test iterating over affordance set."""
        aff_set = AffordanceSet(["a", "b", "c"])
        names = list(aff_set)
        assert set(names) == {"a", "b", "c"}


class TestDefaultAffordances:
    """Test default affordance definitions."""

    def test_terrain_affordances_exist(self):
        """Test terrain affordances are defined."""
        assert "rock" in DEFAULT_AFFORDANCES
        assert "water" in DEFAULT_AFFORDANCES
        assert "soil" in DEFAULT_AFFORDANCES

    def test_rock_affordances(self):
        """Test rock terrain affordances."""
        rock = DEFAULT_AFFORDANCES["rock"]
        assert "climbable" in rock
        assert "solid" in rock

    def test_water_affordances(self):
        """Test water terrain affordances."""
        water = DEFAULT_AFFORDANCES["water"]
        assert "swimmable" in water
        assert "drinkable" in water

    def test_material_affordances_exist(self):
        """Test material affordances are defined."""
        assert "wood" in DEFAULT_AFFORDANCES
        assert "metal" in DEFAULT_AFFORDANCES
        assert "glass" in DEFAULT_AFFORDANCES

    def test_wood_affordances(self):
        """Test wood material affordances."""
        wood = DEFAULT_AFFORDANCES["wood"]
        assert "flammable" in wood
        assert "breakable" in wood

    def test_metal_affordances(self):
        """Test metal material affordances."""
        metal = DEFAULT_AFFORDANCES["metal"]
        assert "conductive" in metal
        assert "climbable" in metal

    def test_glass_affordances(self):
        """Test glass material affordances."""
        glass = DEFAULT_AFFORDANCES["glass"]
        assert "breakable" in glass
        assert "transparent" in glass

    def test_object_affordances_exist(self):
        """Test object type affordances are defined."""
        assert "door" in DEFAULT_AFFORDANCES
        assert "container" in DEFAULT_AFFORDANCES
        assert "button" in DEFAULT_AFFORDANCES

    def test_door_affordances(self):
        """Test door affordances."""
        door = DEFAULT_AFFORDANCES["door"]
        assert "openable" in door
        assert "lockable" in door

    def test_container_affordances(self):
        """Test container affordances."""
        container = DEFAULT_AFFORDANCES["container"]
        assert "openable" in container
        assert "searchable" in container

    def test_button_affordances(self):
        """Test button affordances."""
        button = DEFAULT_AFFORDANCES["button"]
        assert "pressable" in button


class TestAffordanceHelpers:
    """Test helper functions."""

    def test_get_default_affordances(self):
        """Test getting default affordances for category."""
        wood_affs = get_default_affordances("wood")
        assert "flammable" in wood_affs
        assert isinstance(wood_affs, list)

    def test_get_default_affordances_unknown(self):
        """Test getting default affordances for unknown category."""
        unknown = get_default_affordances("nonexistent")
        assert unknown == []

    def test_create_affordance_set(self):
        """Test creating affordance set from categories."""
        aff_set = create_affordance_set(["wood", "door"])
        assert aff_set.has("flammable")  # from wood
        assert aff_set.has("openable")   # from door


class TestAffordanceInheritance:
    """Test complex affordance inheritance scenarios."""

    def test_terrain_to_object_inheritance(self):
        """Test object inherits terrain affordances."""
        wood_affordances = AffordanceSet(["flammable", "breakable"])
        crate = AffordanceSet(["pushable", "climbable"])

        # Inherit material properties
        crate.inherit_from(wood_affordances)
        # Crate is flammable because it's wood
        assert crate.has("flammable")
        assert crate.has("pushable")

    def test_conditional_blocking(self):
        """Test blocking based on state."""
        door = AffordanceSet(["openable", "closable", "lockable"])

        # When door is locked, block opening
        is_locked = True
        if is_locked:
            door.block("openable")

        available = door.get_all()
        assert "openable" not in available
        assert "closable" in available
