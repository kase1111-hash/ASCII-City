"""
Tests for Hotspot System - interactive scene elements.

These tests verify that hotspots correctly:
- Initialize with proper types
- Track visibility and discovery
- Handle requirements
- Provide appropriate actions
"""

import pytest
from shadowengine.interaction import Hotspot, HotspotType


class TestHotspotCreation:
    """Hotspot creation and initialization."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_create_basic_hotspot(self):
        """Can create a basic hotspot."""
        hotspot = Hotspot(
            id="test_hs",
            label="Test Hotspot",
            hotspot_type=HotspotType.OBJECT,
            position=(10, 5),
            description="A test hotspot"
        )

        assert hotspot.id == "test_hs"
        assert hotspot.label == "Test Hotspot"
        assert hotspot.hotspot_type == HotspotType.OBJECT

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_create_person_hotspot(self, sample_hotspots):
        """Person hotspot factory works."""
        person = sample_hotspots[0]  # First is person

        assert person.hotspot_type == HotspotType.PERSON
        assert person.target_id == "john"

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_create_item_hotspot(self):
        """Item hotspot factory works."""
        item = Hotspot.create_item(
            id="key_hs",
            label="Brass Key",
            position=(5, 5),
            description="A shiny brass key",
            item_id="brass_key",
            take_text="You pick up the key."
        )

        assert item.hotspot_type == HotspotType.ITEM
        assert item.gives_item == "brass_key"
        assert "pick up" in item.take_text

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_create_exit_hotspot(self):
        """Exit hotspot factory works."""
        exit_hs = Hotspot.create_exit(
            id="door_hs",
            label="Wooden Door",
            position=(30, 10),
            destination="hallway",
            description="A sturdy wooden door"
        )

        assert exit_hs.hotspot_type == HotspotType.EXIT
        assert exit_hs.target_id == "hallway"

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_create_evidence_hotspot(self):
        """Evidence hotspot factory works."""
        evidence = Hotspot.create_evidence(
            id="letter_hs",
            label="Torn Letter",
            position=(15, 8),
            description="A letter torn in half",
            fact_id="letter_content"
        )

        assert evidence.hotspot_type == HotspotType.EVIDENCE
        assert evidence.reveals_fact == "letter_content"


class TestHotspotState:
    """Hotspot state management."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_initial_state(self, sample_hotspots):
        """Hotspots start visible, active, undiscovered."""
        for hotspot in sample_hotspots:
            assert hotspot.visible is True
            assert hotspot.active is True
            assert hotspot.discovered is False

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_mark_discovered(self, sample_hotspots):
        """Can mark hotspot as discovered."""
        hotspot = sample_hotspots[0]
        hotspot.mark_discovered()

        assert hotspot.discovered is True

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_hide_hotspot(self, sample_hotspots):
        """Can hide hotspot."""
        hotspot = sample_hotspots[0]
        hotspot.hide()

        assert hotspot.visible is False

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_show_hotspot(self, sample_hotspots):
        """Can show hidden hotspot."""
        hotspot = sample_hotspots[0]
        hotspot.hide()
        hotspot.show()

        assert hotspot.visible is True

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_deactivate_hotspot(self, sample_hotspots):
        """Can deactivate hotspot."""
        hotspot = sample_hotspots[0]
        hotspot.deactivate()

        assert hotspot.active is False


class TestHotspotActions:
    """Hotspot action functionality."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_default_action_person(self):
        """Person default action is talk."""
        person = Hotspot.create_person(
            id="p", name="Person", position=(0, 0),
            character_id="char"
        )

        assert person.get_default_action() == "talk"

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_default_action_item(self):
        """Item default action is take."""
        item = Hotspot.create_item(
            id="i", label="Item", position=(0, 0),
            description="An item", item_id="item"
        )

        assert item.get_default_action() == "take"

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_default_action_exit(self):
        """Exit default action is go."""
        exit_hs = Hotspot.create_exit(
            id="e", label="Exit", position=(0, 0),
            destination="elsewhere"
        )

        assert exit_hs.get_default_action() == "go"

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_default_action_evidence(self):
        """Evidence default action is examine."""
        evidence = Hotspot.create_evidence(
            id="ev", label="Evidence", position=(0, 0),
            description="Some evidence", fact_id="fact"
        )

        assert evidence.get_default_action() == "examine"

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_available_actions_person(self):
        """Person has talk and show actions."""
        person = Hotspot.create_person(
            id="p", name="Person", position=(0, 0),
            character_id="char"
        )

        actions = person.get_available_actions()

        assert "examine" in actions
        assert "talk" in actions
        assert "show" in actions

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_available_actions_item(self):
        """Item has take action."""
        item = Hotspot.create_item(
            id="i", label="Item", position=(0, 0),
            description="An item", item_id="item"
        )

        actions = item.get_available_actions()

        assert "examine" in actions
        assert "take" in actions


class TestHotspotRequirements:
    """Hotspot requirement checking."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_no_requirements(self):
        """Hotspot without requirements can be interacted with."""
        hotspot = Hotspot(
            id="simple",
            label="Simple",
            hotspot_type=HotspotType.OBJECT,
            position=(0, 0)
        )

        assert hotspot.can_interact() is True

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_requires_item(self):
        """Hotspot requiring item checks correctly."""
        locked = Hotspot(
            id="locked_door",
            label="Locked Door",
            hotspot_type=HotspotType.EXIT,
            position=(0, 0),
            requires_item="door_key"
        )

        # Without key
        assert locked.can_interact(player_items=set()) is False

        # With key
        assert locked.can_interact(player_items={"door_key"}) is True

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_requires_discovery(self):
        """Hotspot requiring discovery checks correctly."""
        hidden = Hotspot(
            id="secret",
            label="Secret Compartment",
            hotspot_type=HotspotType.OBJECT,
            position=(0, 0),
            requires_discovery="knows_secret"
        )

        # Without discovery
        assert hidden.can_interact(player_discoveries=set()) is False

        # With discovery
        assert hidden.can_interact(player_discoveries={"knows_secret"}) is True

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_inactive_not_interactable(self):
        """Inactive hotspots can't be interacted with."""
        hotspot = Hotspot(
            id="taken",
            label="Taken Item",
            hotspot_type=HotspotType.ITEM,
            position=(0, 0)
        )
        hotspot.deactivate()

        assert hotspot.can_interact() is False

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_hidden_not_interactable(self):
        """Hidden hotspots can't be interacted with."""
        hotspot = Hotspot(
            id="hidden",
            label="Hidden",
            hotspot_type=HotspotType.OBJECT,
            position=(0, 0)
        )
        hotspot.hide()

        assert hotspot.can_interact() is False


class TestHotspotSerialization:
    """Serialization and deserialization."""

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_serialize_hotspot(self, sample_hotspots):
        """Can serialize hotspot."""
        hotspot = sample_hotspots[0]
        hotspot.number = 1
        hotspot.mark_discovered()

        data = hotspot.to_dict()

        assert data["id"] == hotspot.id
        assert data["number"] == 1
        assert data["discovered"] is True

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_deserialize_hotspot(self, sample_hotspots):
        """Can deserialize hotspot."""
        hotspot = sample_hotspots[1]
        hotspot.mark_discovered()
        hotspot.deactivate()

        data = hotspot.to_dict()
        restored = Hotspot.from_dict(data)

        assert restored.id == hotspot.id
        assert restored.discovered is True
        assert restored.active is False

    @pytest.mark.unit
    @pytest.mark.interaction
    def test_roundtrip_all_properties(self):
        """Roundtrip preserves all properties."""
        original = Hotspot(
            id="complex",
            label="Complex Hotspot",
            hotspot_type=HotspotType.EVIDENCE,
            position=(25, 15),
            description="A complex hotspot",
            examine_text="You examine it closely",
            reveals_fact="important_clue",
            requires_item="magnifying_glass",
            requires_discovery="knows_location"
        )
        original.number = 5
        original.mark_discovered()

        data = original.to_dict()
        restored = Hotspot.from_dict(data)

        assert restored.position == (25, 15)
        assert restored.reveals_fact == "important_clue"
        assert restored.requires_item == "magnifying_glass"
        assert restored.number == 5
        assert restored.discovered is True
