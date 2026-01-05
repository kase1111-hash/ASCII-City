"""
Tests for Inventory System.

These tests verify that the inventory system correctly:
- Manages item collection and removal
- Supports item examination and use
- Handles evidence presentation
- Serializes/deserializes properly
"""

import pytest
from shadowengine.inventory import (
    Item, ItemType, Evidence, Inventory,
    EvidencePresentation, PresentationResult
)
from shadowengine.inventory.item import create_key, create_document, create_physical_evidence
from shadowengine.inventory.presentation import ReactionType


class TestItem:
    """Item tests."""

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_create_item(self):
        """Can create an item."""
        item = Item(
            id="brass_key",
            name="Brass Key",
            description="A small brass key"
        )

        assert item.id == "brass_key"
        assert item.name == "Brass Key"
        assert item.item_type == ItemType.GENERIC

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_examine_item(self):
        """Examining marks item as examined."""
        item = Item(
            id="key",
            name="Key",
            description="A key",
            examine_text="It has intricate engravings."
        )

        assert item.examined is False

        text = item.examine()

        assert item.examined is True
        assert "engravings" in text

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_usable_item(self):
        """Usable items work correctly."""
        item = Item(
            id="key",
            name="Key",
            description="A key",
            usable=True,
            use_target="locked_door"
        )

        assert item.can_use_on("locked_door") is True
        assert item.can_use_on("window") is False

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_combinable_item(self):
        """Combinable items work correctly."""
        item = Item(
            id="torn_letter_part1",
            name="Torn Letter (Left)",
            description="Half of a letter",
            combinable=True,
            combines_with=["torn_letter_part2"],
            combination_result="complete_letter"
        )

        assert item.can_combine_with("torn_letter_part2") is True
        assert item.can_combine_with("random_item") is False


class TestEvidence:
    """Evidence item tests."""

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_create_evidence(self):
        """Can create evidence."""
        evidence = Evidence(
            id="bloody_knife",
            name="Bloody Knife",
            description="A knife with dried blood",
            fact_id="murder_weapon",
            implicates=["butler"]
        )

        assert evidence.item_type == ItemType.EVIDENCE
        assert evidence.fact_id == "murder_weapon"
        assert "butler" in evidence.implicates

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_evidence_presentation_intro(self):
        """Evidence has presentation intro."""
        evidence = Evidence(
            id="letter",
            name="Incriminating Letter",
            description="A letter",
            presentation_text="You hold up the letter accusingly."
        )

        assert "accusingly" in evidence.get_presentation_intro()

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_create_key_factory(self):
        """Key factory creates key items."""
        key = create_key(
            id="study_key",
            name="Study Key",
            description="Key to the study",
            unlocks="study_door"
        )

        assert key.item_type == ItemType.KEY
        assert key.unlocks == "study_door"
        assert key.usable is True

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_create_document_factory(self):
        """Document factory creates evidence."""
        doc = create_document(
            id="confession",
            name="Confession Letter",
            description="A handwritten confession",
            content="I admit to taking the jewels...",
            fact_id="confession_fact",
            implicates=["maid"]
        )

        assert isinstance(doc, Evidence)
        assert doc.fact_id == "confession_fact"
        assert "maid" in doc.implicates


class TestInventory:
    """Inventory tests."""

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_create_inventory(self):
        """Can create an inventory."""
        inv = Inventory()

        assert inv.count() == 0
        assert inv.is_full() is False

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_add_item(self):
        """Can add items to inventory."""
        inv = Inventory()
        item = Item(id="key", name="Key", description="A key")

        result = inv.add(item)

        assert result is True
        assert inv.count() == 1
        assert inv.has("key") is True

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_remove_item(self):
        """Can remove items from inventory."""
        inv = Inventory()
        item = Item(id="key", name="Key", description="A key")
        inv.add(item)

        removed = inv.remove("key")

        assert removed is not None
        assert removed.id == "key"
        assert inv.has("key") is False

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_get_item(self):
        """Can get items by ID."""
        inv = Inventory()
        item = Item(id="key", name="Key", description="A key")
        inv.add(item)

        retrieved = inv.get("key")

        assert retrieved is not None
        assert retrieved.name == "Key"

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_capacity_limit(self):
        """Inventory respects capacity limit."""
        inv = Inventory(max_capacity=3)

        for i in range(3):
            item = Item(id=f"item{i}", name=f"Item {i}", description="")
            result = inv.add(item)
            assert result is True

        # Fourth should fail
        item4 = Item(id="item4", name="Item 4", description="")
        result = inv.add(item4)

        assert result is False
        assert inv.count() == 3

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_get_by_type(self):
        """Can filter items by type."""
        inv = Inventory()
        inv.add(Item(id="key1", name="Key 1", description="", item_type=ItemType.KEY))
        inv.add(Item(id="key2", name="Key 2", description="", item_type=ItemType.KEY))
        inv.add(Item(id="tool", name="Tool", description="", item_type=ItemType.TOOL))

        keys = inv.get_by_type(ItemType.KEY)

        assert len(keys) == 2

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_get_evidence(self):
        """Can get all evidence items."""
        inv = Inventory()
        inv.add(Item(id="generic", name="Generic", description=""))
        inv.add(Evidence(id="clue1", name="Clue 1", description="", fact_id="f1"))
        inv.add(Evidence(id="clue2", name="Clue 2", description="", fact_id="f2"))

        evidence = inv.get_evidence()

        assert len(evidence) == 2

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_get_unlocking_item(self):
        """Can find item that unlocks a hotspot."""
        inv = Inventory()
        key = Item(
            id="study_key",
            name="Study Key",
            description="",
            item_type=ItemType.KEY,
            unlocks="study_door"
        )
        inv.add(key)

        found = inv.get_unlocking_item("study_door")

        assert found is not None
        assert found.id == "study_key"

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_examine_item(self):
        """Can examine items in inventory."""
        inv = Inventory()
        item = Item(
            id="note",
            name="Note",
            description="A folded note",
            examine_text="It reads: 'Meet me at midnight.'"
        )
        inv.add(item)

        text = inv.examine("note")

        assert "midnight" in text

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_use_item(self):
        """Can use items from inventory."""
        inv = Inventory()
        item = Item(
            id="key",
            name="Key",
            description="",
            usable=True,
            use_text="You insert the key."
        )
        inv.add(item)

        success, message = inv.use_item("key")

        assert success is True
        assert "insert" in message

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_use_consumable(self):
        """Consumable items are removed on use."""
        inv = Inventory()
        item = Item(
            id="potion",
            name="Potion",
            description="",
            usable=True,
            consumed_on_use=True
        )
        inv.add(item)

        inv.use_item("potion")

        assert inv.has("potion") is False

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_search_items(self):
        """Can search items by name/description."""
        inv = Inventory()
        inv.add(Item(id="key1", name="Brass Key", description="Small"))
        inv.add(Item(id="key2", name="Iron Key", description="Large brass handle"))
        inv.add(Item(id="note", name="Note", description="A paper note"))

        results = inv.search("brass")

        assert len(results) == 2

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_display_list(self):
        """Can get display list."""
        inv = Inventory()
        inv.add(Item(id="key", name="Old Key", description="", item_type=ItemType.KEY))
        inv.add(Evidence(id="letter", name="Letter", description="", fact_id="f1"))

        display = inv.get_display_list()

        assert len(display) == 2
        assert any("[key]" in line for line in display)
        assert any("[evidence]" in line for line in display)


class TestEvidencePresentation:
    """Evidence presentation tests."""

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_create_presenter(self):
        """Can create evidence presenter."""
        presenter = EvidencePresentation()

        assert presenter is not None

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_present_implicating_evidence(self):
        """Presenting implicating evidence causes defensive reaction."""
        presenter = EvidencePresentation()
        evidence = Evidence(
            id="bloody_knife",
            name="Bloody Knife",
            description="",
            fact_id="murder_weapon",
            implicates=["butler"]
        )

        result = presenter.present(
            evidence=evidence,
            character_id="butler",
            character_archetype="guilty",
            character_is_implicated=True,
            character_pressure=20
        )

        assert result.reaction in (
            ReactionType.NERVOUS,
            ReactionType.DEFENSIVE,
            ReactionType.FRIGHTENED
        )
        assert result.trust_change < 0

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_present_exonerating_evidence(self):
        """Presenting exonerating evidence causes relief."""
        presenter = EvidencePresentation()
        evidence = Evidence(
            id="alibi_photo",
            name="Photograph",
            description="",
            fact_id="alibi_proof",
            exonerates=["maid"]
        )

        result = presenter.present(
            evidence=evidence,
            character_id="maid",
            character_archetype="innocent",
            character_is_exonerated=True
        )

        assert result.reaction == ReactionType.RELIEVED
        assert result.trust_change > 0

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_high_pressure_causes_crack(self):
        """High pressure with implicating evidence causes crack."""
        presenter = EvidencePresentation()
        evidence = Evidence(
            id="confession",
            name="Confession",
            description="",
            fact_id="confession_fact",
            implicates=["culprit"]
        )

        result = presenter.present(
            evidence=evidence,
            character_id="culprit",
            character_archetype="guilty",
            character_is_implicated=True,
            character_pressure=80
        )

        assert result.reaction == ReactionType.CRACKED

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_presentation_applies_pressure(self):
        """Presenting implicating evidence applies pressure."""
        presenter = EvidencePresentation()
        evidence = Evidence(
            id="clue",
            name="Clue",
            description="",
            implicates=["suspect"]
        )

        result = presenter.present(
            evidence=evidence,
            character_id="suspect",
            character_archetype="survivor",
            character_is_implicated=True,
            character_pressure=30
        )

        assert result.pressure_applied > 0

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_cooperative_reaction_reveals_info(self):
        """Cooperative reaction can reveal information."""
        presenter = EvidencePresentation()
        evidence = Evidence(
            id="clue",
            name="Clue",
            description="",
            fact_id="important_fact",
            related_facts=["related_fact"]
        )

        result = presenter.present(
            evidence=evidence,
            character_id="witness",
            character_archetype="outsider",
            character_trust=30,
            character_knows_fact=True
        )

        if result.reaction == ReactionType.COOPERATIVE:
            assert result.unlocks_topic is not None or result.reveals_fact is not None

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_get_effective_evidence(self):
        """Can get evidence effective against a character."""
        presenter = EvidencePresentation()

        evidence_list = [
            Evidence(id="e1", name="E1", description="", implicates=["alice"]),
            Evidence(id="e2", name="E2", description="", exonerates=["bob"]),
            Evidence(id="e3", name="E3", description="", implicates=["charlie"]),
        ]

        effective = presenter.get_effective_evidence(evidence_list, "alice")

        assert len(effective) == 1
        assert effective[0].id == "e1"


class TestInventorySerialization:
    """Inventory serialization tests."""

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_serialize_item(self):
        """Can serialize an item."""
        item = Item(
            id="key",
            name="Key",
            description="A brass key",
            item_type=ItemType.KEY,
            examined=True,
            unlocks="door"
        )

        data = item.to_dict()

        assert data["id"] == "key"
        assert data["item_type"] == "KEY"
        assert data["examined"] is True

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_deserialize_item(self):
        """Can deserialize an item."""
        item = Item(
            id="key",
            name="Key",
            description="A key",
            usable=True,
            use_target="door"
        )

        data = item.to_dict()
        restored = Item.from_dict(data)

        assert restored.id == "key"
        assert restored.usable is True
        assert restored.use_target == "door"

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_serialize_evidence(self):
        """Can serialize evidence."""
        evidence = Evidence(
            id="letter",
            name="Letter",
            description="A letter",
            fact_id="letter_fact",
            implicates=["butler", "maid"]
        )

        data = evidence.to_dict()

        assert data["fact_id"] == "letter_fact"
        assert "butler" in data["implicates"]

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_deserialize_evidence(self):
        """Can deserialize evidence."""
        evidence = Evidence(
            id="photo",
            name="Photo",
            description="",
            fact_id="alibi",
            exonerates=["guest"]
        )

        data = evidence.to_dict()
        restored = Evidence.from_dict(data)

        assert restored.fact_id == "alibi"
        assert "guest" in restored.exonerates

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_serialize_inventory(self):
        """Can serialize inventory."""
        inv = Inventory(max_capacity=20)
        inv.add(Item(id="key", name="Key", description=""))
        inv.add(Evidence(id="clue", name="Clue", description="", fact_id="f1"))

        data = inv.to_dict()

        assert data["max_capacity"] == 20
        assert "key" in data["items"]
        assert data["items"]["clue"]["type"] == "Evidence"

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_deserialize_inventory(self):
        """Can deserialize inventory."""
        inv = Inventory()
        inv.add(Item(id="key", name="Key", description="", item_type=ItemType.KEY))
        inv.add(Evidence(id="letter", name="Letter", description="", fact_id="f1"))

        data = inv.to_dict()
        restored = Inventory.from_dict(data)

        assert restored.has("key") is True
        assert restored.has("letter") is True
        assert isinstance(restored.get("letter"), Evidence)

    @pytest.mark.unit
    @pytest.mark.inventory
    def test_roundtrip_preserves_state(self):
        """Roundtrip preserves all state."""
        inv = Inventory(max_capacity=30)

        key = Item(
            id="study_key",
            name="Study Key",
            description="Opens the study",
            item_type=ItemType.KEY,
            usable=True,
            unlocks="study_door"
        )
        key.examined = True
        inv.add(key)

        evidence = Evidence(
            id="bloody_knife",
            name="Bloody Knife",
            description="A knife",
            fact_id="murder_weapon",
            implicates=["butler"],
            exonerates=["maid"]
        )
        inv.add(evidence)

        data = inv.to_dict()
        restored = Inventory.from_dict(data)

        restored_key = restored.get("study_key")
        assert restored_key.examined is True
        assert restored_key.unlocks == "study_door"

        restored_evidence = restored.get("bloody_knife")
        assert "butler" in restored_evidence.implicates
        assert "maid" in restored_evidence.exonerates
