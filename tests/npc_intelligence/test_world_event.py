"""Tests for WorldEvent system."""

import pytest
from src.shadowengine.npc_intelligence.world_event import (
    WorldEvent, WitnessType, Witness, WorldEventFactory
)


class TestWitness:
    """Tests for Witness dataclass."""

    def test_witness_creation(self):
        """Test creating a witness."""
        witness = Witness(
            npc_id="npc_001",
            witness_type=WitnessType.DIRECT,
            clarity=0.9,
            distance=5.0
        )
        assert witness.npc_id == "npc_001"
        assert witness.witness_type == WitnessType.DIRECT
        assert witness.clarity == 0.9
        assert witness.distance == 5.0

    def test_witness_serialization(self):
        """Test witness to_dict and from_dict."""
        witness = Witness(
            npc_id="npc_002",
            witness_type=WitnessType.INDIRECT,
            clarity=0.5
        )
        data = witness.to_dict()
        restored = Witness.from_dict(data)

        assert restored.npc_id == witness.npc_id
        assert restored.witness_type == witness.witness_type
        assert restored.clarity == witness.clarity


class TestWorldEvent:
    """Tests for WorldEvent dataclass."""

    def test_event_creation(self):
        """Test creating a world event."""
        event = WorldEvent(
            timestamp=100.0,
            location=(10, 20),
            location_name="dark_alley",
            event_type="violence",
            actors=["thug", "victim"],
            details={"weapon": "knife"}
        )

        assert event.timestamp == 100.0
        assert event.location == (10, 20)
        assert event.event_type == "violence"
        assert "thug" in event.actors
        assert event.id.startswith("evt_")

    def test_event_auto_id(self):
        """Test that events get auto-generated IDs."""
        event1 = WorldEvent(event_type="test")
        event2 = WorldEvent(event_type="test")

        assert event1.id != event2.id
        assert event1.id.startswith("evt_")

    def test_add_witness(self):
        """Test adding witnesses to event."""
        event = WorldEvent(event_type="theft")
        event.add_witness("npc_001", WitnessType.DIRECT)
        event.add_witness("npc_002", WitnessType.INDIRECT, clarity=0.5)

        assert len(event.witnesses) == 2
        assert event.was_witnessed_by("npc_001")
        assert event.was_witnessed_by("npc_002")
        assert not event.was_witnessed_by("npc_003")

    def test_direct_indirect_witnesses(self):
        """Test getting direct vs indirect witnesses."""
        event = WorldEvent(event_type="conversation")
        event.add_witness("direct_1", WitnessType.DIRECT)
        event.add_witness("direct_2", WitnessType.DIRECT)
        event.add_witness("indirect_1", WitnessType.INDIRECT)

        assert len(event.direct_witnesses) == 2
        assert len(event.indirect_witnesses) == 1
        assert "direct_1" in event.direct_witnesses
        assert "indirect_1" in event.indirect_witnesses

    def test_get_witness(self):
        """Test getting specific witness record."""
        event = WorldEvent(event_type="discovery")
        event.add_witness("npc_001", WitnessType.DIRECT, clarity=0.8, distance=3.0)

        witness = event.get_witness("npc_001")
        assert witness is not None
        assert witness.clarity == 0.8
        assert witness.distance == 3.0

        assert event.get_witness("nonexistent") is None

    def test_event_serialization(self):
        """Test event to_dict and from_dict."""
        event = WorldEvent(
            timestamp=50.0,
            location=(5, 10),
            location_name="bar",
            event_type="conversation",
            actors=["bartender", "patron"],
            details={"topic": "weather"},
            leaves_evidence=False,
            notability=0.3
        )
        event.add_witness("eavesdropper", WitnessType.INDIRECT)

        data = event.to_dict()
        restored = WorldEvent.from_dict(data)

        assert restored.timestamp == event.timestamp
        assert restored.location == event.location
        assert restored.event_type == event.event_type
        assert restored.actors == event.actors
        assert len(restored.witnesses) == 1


class TestWorldEventFactory:
    """Tests for WorldEventFactory."""

    def test_injury_event(self):
        """Test creating injury event."""
        event = WorldEventFactory.injury(
            timestamp=100.0,
            location=(10, 20),
            location_name="waterfall",
            victim="player",
            severity=0.6,
            cause="slipped"
        )

        assert event.event_type == "injury"
        assert event.actors == ["player"]
        assert event.details["severity"] == 0.6
        assert event.leaves_evidence  # severity > 0.3
        assert event.notability == 0.6

    def test_violence_event(self):
        """Test creating violence event."""
        event = WorldEventFactory.violence(
            timestamp=200.0,
            location=(50, 50),
            location_name="alley",
            attacker="thug",
            victim="target",
            weapon="pistol",
            lethal=True
        )

        assert event.event_type == "violence"
        assert "thug" in event.actors
        assert "target" in event.actors
        assert event.details["weapon"] == "pistol"
        assert event.details["result"] == "death"
        assert event.evidence_type == "body"
        assert event.sound_radius == 15.0  # pistol is loud

    def test_conversation_event(self):
        """Test creating conversation event."""
        event = WorldEventFactory.conversation(
            timestamp=50.0,
            location=(5, 5),
            location_name="office",
            participants=["boss", "employee"],
            topic="project",
            tone="loud"
        )

        assert event.event_type == "conversation"
        assert len(event.actors) == 2
        assert event.details["tone"] == "loud"
        assert event.sound_radius == 3.0  # loud conversation

    def test_discovery_event(self):
        """Test creating discovery event."""
        event = WorldEventFactory.discovery(
            timestamp=150.0,
            location=(30, 30),
            location_name="crime_scene",
            discoverer="detective",
            what="bloody_knife",
            significance=0.9
        )

        assert event.event_type == "discovery"
        assert event.actors == ["detective"]
        assert event.details["discovered"] == "bloody_knife"
        assert event.notability == 0.9

    def test_movement_event(self):
        """Test creating movement event."""
        event = WorldEventFactory.movement(
            timestamp=75.0,
            from_location=(0, 0),
            to_location=(10, 10),
            location_name="corridor",
            mover="suspicious_person",
            manner="running"
        )

        assert event.event_type == "movement"
        assert event.details["manner"] == "running"
        assert event.sound_radius == 5.0  # running is loud

    def test_theft_event(self):
        """Test creating theft event."""
        event = WorldEventFactory.theft(
            timestamp=300.0,
            location=(20, 20),
            location_name="vault",
            thief="cat_burglar",
            victim="bank",
            item="diamonds",
            value=1.0
        )

        assert event.event_type == "theft"
        assert event.details["item"] == "diamonds"
        assert event.notability == 1.0
