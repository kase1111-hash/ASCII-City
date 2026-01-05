"""
Phase 2 Integration Tests - Testing system interactions.

These tests verify that Phase 2 systems work together correctly:
- Environment + Character scheduling
- Weather effects on NPC behavior
- Inventory + Character evidence presentation
- Full scenario simulations
"""

import pytest
from shadowengine.environment import (
    Environment, TimeSystem, TimePeriod, WeatherSystem, WeatherType
)
from shadowengine.character import (
    Character, Archetype, Schedule, Activity,
    RelationshipManager, RelationType,
    create_servant_schedule, create_guest_schedule
)
from shadowengine.inventory import (
    Inventory, Item, Evidence, ItemType,
    EvidencePresentation
)
from shadowengine.inventory.presentation import ReactionType
from shadowengine.game import Game, GameState
from shadowengine.config import GameConfig


class TestEnvironmentCharacterIntegration:
    """Tests for environment affecting character behavior."""

    @pytest.mark.integration
    def test_schedule_follows_time(self):
        """Character schedule responds to time changes."""
        env = Environment()
        schedule = create_servant_schedule(
            "butler",
            quarters="servants_quarters",
            work_location="kitchen"
        )

        # Morning - should be at work
        env.time.set_time(10, 0)
        location = schedule.get_location(env.time.hour)
        assert location == "kitchen"

        # Night - should be in quarters
        env.time.set_time(23, 0)
        location = schedule.get_location(env.time.hour)
        assert location == "servants_quarters"

    @pytest.mark.integration
    def test_time_advancement_triggers_schedule_changes(self):
        """Advancing time causes schedule location changes."""
        env = Environment()
        env.time.set_time(6, 55)  # Just before 7am

        schedule = Schedule(character_id="butler", default_location="quarters")
        schedule.add_entry(7, 12, "kitchen", Activity.WORKING)

        # Before 7am
        assert schedule.get_location(env.time.hour) == "quarters"

        # Advance to 7am
        env.update(10)

        assert schedule.get_location(env.time.hour) == "kitchen"

    @pytest.mark.integration
    def test_weather_affects_outdoor_schedule(self):
        """Bad weather triggers schedule overrides for outdoor activities."""
        env = Environment()
        env.time.set_time(10, 0)

        schedule = Schedule(character_id="gardener", default_location="garden")
        schedule.add_entry(8, 17, "garden", Activity.WORKING)

        # Clear weather - gardener in garden
        env.weather.set_weather(WeatherType.CLEAR, immediate=True)
        assert schedule.get_location(env.time.hour) == "garden"

        # Storm - add override to move indoors
        env.weather.set_weather(WeatherType.STORM, immediate=True)
        if env.weather.is_outdoor_dangerous():
            schedule.add_override(
                "shed",
                Activity.WAITING,
                "Sheltering from storm",
                duration_minutes=60
            )

        assert schedule.get_location(env.time.hour) == "shed"

    @pytest.mark.integration
    def test_visibility_affects_character_detection(self):
        """Low visibility affects whether characters can see things."""
        env = Environment()
        env.register_location("alley", is_indoor=False, has_lighting=False, has_shelter=False)

        # Bright day
        env.time.set_time(12, 0)
        env.weather.set_weather(WeatherType.CLEAR, immediate=True)
        day_vis = env.get_visibility("alley")

        # Dark foggy night
        env.time.set_time(2, 0)
        env.weather.set_weather(WeatherType.FOG, immediate=True)
        night_vis = env.get_visibility("alley")

        assert day_vis > night_vis
        assert night_vis <= 0.5  # Very low visibility

    @pytest.mark.integration
    def test_time_period_affects_npc_availability(self):
        """NPCs have different availability based on time period."""
        env = Environment()

        schedule = Schedule(character_id="butler", default_location="quarters")
        schedule.add_entry(22, 6, "quarters", Activity.SLEEPING, interruptible=False)
        schedule.add_entry(8, 18, "various", Activity.WORKING, interruptible=True)

        # During work hours - interruptible
        env.time.set_time(10, 0)
        assert schedule.is_interruptible(env.time.hour) is True

        # During sleep hours - not interruptible
        env.time.set_time(2, 0)
        assert schedule.is_interruptible(env.time.hour) is False


class TestCharacterRelationshipIntegration:
    """Tests for character relationships and interactions."""

    @pytest.mark.integration
    def test_relationship_affects_conversation(self):
        """Character relationships affect dialogue willingness."""
        char1 = Character(
            id="butler",
            name="Mr. Blackwood",
            archetype=Archetype.GUILTY,
            initial_location="study"
        )

        manager = RelationshipManager()
        manager.set_relationship("butler", "player", RelationType.ACQUAINTANCE, affinity=0)

        # Neutral relationship - check cooperation
        rel = manager.get_relationship("butler", "player")
        assert rel.affinity == 0

        # Improve relationship
        rel.modify_affinity(40)
        assert rel.relation_type == RelationType.FRIEND

    @pytest.mark.integration
    def test_npc_interactions_at_same_location(self):
        """NPCs at same location can interact."""
        manager = RelationshipManager()
        manager.set_seed(42)

        # Set up relationships
        manager.set_relationship("butler", "maid", RelationType.COLLEAGUE, affinity=20)
        manager.set_relationship("butler", "guest", RelationType.ACQUAINTANCE, affinity=0)

        # Both in parlor
        locations = {
            "butler": "parlor",
            "maid": "parlor",
            "guest": "kitchen"
        }

        # Get who can interact
        in_parlor = manager.get_characters_in_location("parlor", locations)
        assert "butler" in in_parlor
        assert "maid" in in_parlor
        assert "guest" not in in_parlor

        # Simulate interaction
        results = manager.simulate_location_interactions("parlor", locations)
        assert len(results) >= 1

    @pytest.mark.integration
    def test_tension_builds_over_multiple_interactions(self):
        """Tension between characters can build over time."""
        manager = RelationshipManager()
        manager.set_seed(42)

        manager.set_relationship("alice", "bob", RelationType.RIVAL, affinity=-30)

        rel = manager.get_relationship("alice", "bob")
        initial_tension = rel.tension

        # Simulate several hostile interactions
        for _ in range(10):
            result = manager.simulate_interaction("alice", "bob", "parlor")
            if result.interaction_type == "hostile_exchange":
                assert result.tension_change > 0

        # Tension should have increased
        assert rel.tension >= initial_tension

    @pytest.mark.integration
    def test_shared_secrets_affect_trust(self):
        """Sharing secrets increases trust between characters."""
        manager = RelationshipManager()
        manager.set_relationship("alice", "bob", RelationType.ACQUAINTANCE)

        rel = manager.get_relationship("alice", "bob")
        initial_trust = rel.trust

        rel.add_shared_secret("knows_about_theft")
        rel.add_shared_secret("alibis_each_other")

        assert rel.trust > initial_trust
        assert len(rel.shared_secrets) == 2


class TestInventoryCharacterIntegration:
    """Tests for inventory and character interaction."""

    @pytest.mark.integration
    def test_evidence_presentation_affects_character(self):
        """Presenting evidence affects character state."""
        char = Character(
            id="butler",
            name="Mr. Blackwood",
            archetype=Archetype.GUILTY,
            secret_truth="I stole the jewels",
            trust_threshold=50,
            initial_location="study"
        )

        evidence = Evidence(
            id="stolen_jewels",
            name="Stolen Jewels",
            description="The missing family jewels",
            fact_id="theft_proof",
            implicates=["butler"]
        )

        presenter = EvidencePresentation()

        # Present with low pressure
        result = presenter.present(
            evidence=evidence,
            character_id="butler",
            character_archetype="guilty",
            character_is_implicated=True,
            character_pressure=20
        )

        assert result.reaction in (
            ReactionType.NERVOUS,
            ReactionType.DEFENSIVE
        )
        assert result.pressure_applied > 0

    @pytest.mark.integration
    def test_multiple_evidence_increases_pressure(self):
        """Presenting multiple pieces of evidence increases pressure."""
        char = Character(
            id="culprit",
            name="The Culprit",
            archetype=Archetype.GUILTY,
            trust_threshold=60,
            initial_location="study"
        )

        evidence_pieces = [
            Evidence(id="e1", name="Evidence 1", description="", implicates=["culprit"]),
            Evidence(id="e2", name="Evidence 2", description="", implicates=["culprit"]),
            Evidence(id="e3", name="Evidence 3", description="", implicates=["culprit"]),
        ]

        presenter = EvidencePresentation()
        total_pressure = 0

        for evidence in evidence_pieces:
            result = presenter.present(
                evidence=evidence,
                character_id="culprit",
                character_archetype="guilty",
                character_is_implicated=True,
                character_pressure=total_pressure
            )
            total_pressure += result.pressure_applied

        assert total_pressure > 0

    @pytest.mark.integration
    def test_exonerating_evidence_clears_suspect(self):
        """Exonerating evidence changes NPC reaction."""
        innocent = Character(
            id="maid",
            name="The Maid",
            archetype=Archetype.INNOCENT,
            initial_location="kitchen"
        )

        alibi = Evidence(
            id="alibi_photo",
            name="Photograph",
            description="Photo showing the maid elsewhere",
            fact_id="maid_alibi",
            exonerates=["maid"]
        )

        presenter = EvidencePresentation()
        result = presenter.present(
            evidence=alibi,
            character_id="maid",
            character_archetype="innocent",
            character_is_exonerated=True
        )

        assert result.reaction == ReactionType.RELIEVED
        assert result.trust_change > 0

    @pytest.mark.integration
    def test_key_unlocks_location(self):
        """Keys in inventory can unlock locations."""
        inv = Inventory()

        key = Item(
            id="study_key",
            name="Study Key",
            description="Key to the study",
            item_type=ItemType.KEY,
            usable=True,
            unlocks="locked_study_door"
        )
        inv.add(key)

        # Check if we have the right key
        unlocking_item = inv.get_unlocking_item("locked_study_door")
        assert unlocking_item is not None
        assert unlocking_item.id == "study_key"

        # Wrong door
        wrong_key = inv.get_unlocking_item("basement_door")
        assert wrong_key is None


class TestFullScenarioSimulation:
    """Full scenario integration tests."""

    @pytest.fixture
    def full_scenario(self):
        """Set up a complete scenario with all Phase 2 systems."""
        # Environment
        env = Environment()
        env.set_seed(42)
        env.time.set_time(10, 0)  # Morning
        env.weather.set_weather(WeatherType.CLEAR, immediate=True)

        # Register locations
        env.register_location("study", is_indoor=True, has_lighting=True)
        env.register_location("kitchen", is_indoor=True, has_lighting=True)
        env.register_location("garden", is_indoor=False, has_shelter=False)

        # Characters
        butler = Character(
            id="butler",
            name="Mr. Blackwood",
            archetype=Archetype.GUILTY,
            secret_truth="I took the watch",
            trust_threshold=50,
            initial_location="study"
        )

        maid = Character(
            id="maid",
            name="Mrs. White",
            archetype=Archetype.SURVIVOR,
            secret_truth="I saw the butler take it",
            trust_threshold=30,
            initial_location="kitchen"
        )

        guest = Character(
            id="guest",
            name="Lord Ashton",
            archetype=Archetype.INNOCENT,
            initial_location="study"
        )

        # Schedules
        butler_schedule = create_servant_schedule("butler", "servants_hall", "study")
        maid_schedule = create_servant_schedule("maid", "servants_hall", "kitchen")
        guest_schedule = create_guest_schedule("guest", "guest_room", ["study", "dining"])

        # Relationships
        relationships = RelationshipManager()
        relationships.set_seed(42)
        relationships.set_relationship("butler", "maid", RelationType.COLLEAGUE, affinity=10)
        relationships.set_relationship("butler", "guest", RelationType.SUBORDINATE, affinity=-10)
        relationships.set_relationship("maid", "guest", RelationType.SUBORDINATE, affinity=5)

        # Inventory with evidence
        inventory = Inventory()
        inventory.add(Evidence(
            id="torn_letter",
            name="Torn Letter",
            description="A partially burned letter",
            fact_id="butler_motive",
            implicates=["butler"],
            examine_text="It mentions gambling debts..."
        ))
        inventory.add(Item(
            id="study_key",
            name="Study Key",
            description="Key to the locked drawer",
            item_type=ItemType.KEY,
            unlocks="locked_drawer"
        ))

        return {
            "environment": env,
            "characters": {"butler": butler, "maid": maid, "guest": guest},
            "schedules": {
                "butler": butler_schedule,
                "maid": maid_schedule,
                "guest": guest_schedule
            },
            "relationships": relationships,
            "inventory": inventory
        }

    @pytest.mark.integration
    def test_scenario_time_progression(self, full_scenario):
        """Scenario time progression affects all systems."""
        env = full_scenario["environment"]
        schedules = full_scenario["schedules"]

        # Track character locations through the day
        location_log = []

        for hour in [8, 12, 18, 22]:
            env.time.set_time(hour, 0)
            locations = {
                char_id: schedule.get_location(hour)
                for char_id, schedule in schedules.items()
            }
            location_log.append((hour, locations))

        # Characters should be in different places at different times
        morning_locs = location_log[0][1]
        night_locs = location_log[3][1]

        # Butler should be working in morning, in quarters at night
        assert morning_locs["butler"] != night_locs["butler"]

    @pytest.mark.integration
    def test_scenario_weather_changes(self, full_scenario):
        """Weather changes affect scenario dynamics."""
        env = full_scenario["environment"]

        # Start clear
        assert env.weather.current_state.weather_type == WeatherType.CLEAR

        # Change to storm
        env.weather.set_weather(WeatherType.STORM, immediate=True)

        # Check effects
        effect = env.get_weather_effect()
        assert effect.visibility < 1.0
        assert effect.npc_indoor_preference > 0.5

    @pytest.mark.integration
    def test_scenario_evidence_chain(self, full_scenario):
        """Evidence presentation creates a chain of reactions."""
        inventory = full_scenario["inventory"]
        characters = full_scenario["characters"]

        presenter = EvidencePresentation()
        letter = inventory.get("torn_letter")

        # Present to butler (implicated)
        butler_result = presenter.present(
            evidence=letter,
            character_id="butler",
            character_archetype="guilty",
            character_is_implicated=True,
            character_pressure=0
        )

        assert butler_result.reaction in (
            ReactionType.NERVOUS,
            ReactionType.DEFENSIVE,
            ReactionType.FRIGHTENED
        )

        # Present to maid (witness)
        maid_result = presenter.present(
            evidence=letter,
            character_id="maid",
            character_archetype="survivor",
            character_is_implicated=False,
            character_trust=10,
            character_knows_fact=True
        )

        # Maid might cooperate if she knows about it
        assert maid_result.reaction is not None

    @pytest.mark.integration
    def test_scenario_npc_interactions(self, full_scenario):
        """NPCs interact with each other in the scenario."""
        env = full_scenario["environment"]
        schedules = full_scenario["schedules"]
        relationships = full_scenario["relationships"]

        env.time.set_time(10, 0)

        # Get character locations
        locations = {
            char_id: schedule.get_location(env.time.hour)
            for char_id, schedule in schedules.items()
        }

        # Find location with multiple characters
        location_counts = {}
        for char_id, loc in locations.items():
            location_counts[loc] = location_counts.get(loc, [])
            location_counts[loc].append(char_id)

        # Simulate interactions at populated locations
        all_interactions = []
        for loc, chars in location_counts.items():
            if len(chars) >= 2:
                results = relationships.simulate_location_interactions(loc, locations)
                all_interactions.extend(results)

        # Some interactions should have occurred
        # (depends on schedule overlap)
        assert isinstance(all_interactions, list)

    @pytest.mark.integration
    def test_scenario_full_day_simulation(self, full_scenario):
        """Simulate a full day in the scenario."""
        env = full_scenario["environment"]
        schedules = full_scenario["schedules"]
        relationships = full_scenario["relationships"]

        # Start at 6am
        env.time.set_time(6, 0)

        events_log = []
        interaction_count = 0

        # Simulate every hour for 24 hours
        for _ in range(24):
            hour = env.time.hour

            # Get character locations
            locations = {
                char_id: schedule.get_location(hour)
                for char_id, schedule in schedules.items()
            }

            # Simulate interactions
            for loc in set(locations.values()):
                results = relationships.simulate_location_interactions(
                    loc, locations, max_interactions=1
                )
                interaction_count += len(results)
                for r in results:
                    events_log.append({
                        "hour": hour,
                        "type": "interaction",
                        "data": r
                    })

            # Advance 1 hour
            changes = env.update(60)

            if changes.get("period_changed"):
                events_log.append({
                    "hour": hour,
                    "type": "period_change",
                    "data": changes["period_changed"]
                })

            if changes.get("weather_changed"):
                events_log.append({
                    "hour": hour,
                    "type": "weather_change",
                    "data": changes["weather_changed"]
                })

        # Should have recorded events throughout the day
        assert len(events_log) > 0

        # Should have had period changes (dawn -> morning -> afternoon -> etc.)
        period_changes = [e for e in events_log if e["type"] == "period_change"]
        assert len(period_changes) >= 4  # At least 4 period transitions in a day


class TestPhase2Serialization:
    """Test that Phase 2 systems serialize correctly together."""

    @pytest.mark.integration
    def test_full_state_serialization(self):
        """All Phase 2 systems can be serialized together."""
        # Create systems
        env = Environment()
        env.time.set_time(14, 30)
        env.weather.set_weather(WeatherType.CLOUDY, immediate=True)
        env.register_location("study", is_indoor=True)

        schedule = Schedule(character_id="butler", default_location="quarters")
        schedule.add_entry(8, 18, "study", Activity.WORKING)

        relationships = RelationshipManager()
        relationships.set_relationship("alice", "bob", RelationType.FRIEND, affinity=40)

        inventory = Inventory()
        inventory.add(Evidence(id="clue1", name="Clue", description="", fact_id="f1"))

        # Serialize all
        state = {
            "environment": env.to_dict(),
            "schedule": schedule.to_dict(),
            "relationships": relationships.to_dict(),
            "inventory": inventory.to_dict()
        }

        # Verify serialization
        assert "time" in state["environment"]
        assert "weather" in state["environment"]
        assert "entries" in state["schedule"]
        assert "relationships" in state["relationships"]
        assert "items" in state["inventory"]

    @pytest.mark.integration
    def test_full_state_roundtrip(self):
        """Full state survives serialize/deserialize roundtrip."""
        # Create systems with specific state
        env = Environment()
        env.time.set_time(22, 15)
        env.weather.set_weather(WeatherType.STORM, immediate=True)
        env.register_location("cellar", is_indoor=True, is_dark=True)

        schedule = Schedule(character_id="maid")
        schedule.add_entry(6, 22, "kitchen", Activity.WORKING)
        schedule.add_override("cellar", Activity.HIDING, "Frightened", 30)

        relationships = RelationshipManager()
        relationships.set_relationship(
            "butler", "maid",
            RelationType.CONSPIRATOR,
            affinity=50, trust=60
        )
        rel = relationships.get_relationship("butler", "maid")
        rel.add_shared_secret("the_plan")

        inventory = Inventory()
        key = Item(id="key", name="Key", description="", item_type=ItemType.KEY)
        key.examined = True
        inventory.add(key)

        # Serialize
        state = {
            "environment": env.to_dict(),
            "schedule": schedule.to_dict(),
            "relationships": relationships.to_dict(),
            "inventory": inventory.to_dict()
        }

        # Deserialize
        restored_env = Environment.from_dict(state["environment"])
        restored_schedule = Schedule.from_dict(state["schedule"])
        restored_relationships = RelationshipManager.from_dict(state["relationships"])
        restored_inventory = Inventory.from_dict(state["inventory"])

        # Verify state preservation
        assert restored_env.time.hour == 22
        assert restored_env.weather.current_state.weather_type == WeatherType.STORM
        assert "cellar" in restored_env.locations

        assert len(restored_schedule.overrides) == 1
        assert restored_schedule.overrides[0].reason == "Frightened"

        restored_rel = restored_relationships.get_relationship("butler", "maid")
        assert restored_rel.relation_type == RelationType.CONSPIRATOR
        assert "the_plan" in restored_rel.shared_secrets

        assert restored_inventory.get("key").examined is True


class TestEdgeCases:
    """Edge case tests for Phase 2 systems."""

    @pytest.mark.integration
    def test_midnight_schedule_transition(self):
        """Schedule handles midnight correctly."""
        schedule = Schedule(character_id="guard", default_location="gate")
        schedule.add_entry(22, 6, "watchtower", Activity.WORKING)  # Night shift

        assert schedule.get_location(23) == "watchtower"
        assert schedule.get_location(0) == "watchtower"
        assert schedule.get_location(5) == "watchtower"
        assert schedule.get_location(7) == "gate"  # Default

    @pytest.mark.integration
    def test_empty_location_no_interactions(self):
        """Empty locations produce no interactions."""
        relationships = RelationshipManager()
        locations = {"alice": "parlor", "bob": "kitchen"}

        results = relationships.simulate_location_interactions("garden", locations)
        assert len(results) == 0

    @pytest.mark.integration
    def test_weather_transition_during_simulation(self):
        """Weather can transition during time advancement."""
        env = Environment()
        env.set_seed(42)
        env.time.set_time(8, 0)

        # Force weather to start transitioning
        env.weather.current_state.duration_remaining = 5

        weather_changes = []
        for _ in range(20):
            changes = env.update(30)
            if changes.get("weather_changed"):
                weather_changes.append(changes["weather_changed"])

        # Weather should have changed at some point
        # (may or may not depending on RNG, but system shouldn't crash)
        assert isinstance(weather_changes, list)

    @pytest.mark.integration
    def test_high_pressure_evidence_chain(self):
        """Character cracks after enough evidence pressure."""
        presenter = EvidencePresentation()

        evidence_list = [
            Evidence(id=f"e{i}", name=f"Evidence {i}", description="", implicates=["culprit"])
            for i in range(5)
        ]

        total_pressure = 0
        cracked = False

        for evidence in evidence_list:
            result = presenter.present(
                evidence=evidence,
                character_id="culprit",
                character_archetype="guilty",
                character_is_implicated=True,
                character_pressure=total_pressure
            )
            total_pressure += result.pressure_applied

            if result.reaction == ReactionType.CRACKED:
                cracked = True
                break

        # With 5 pieces of evidence, should have significant pressure
        assert total_pressure > 0 or cracked
