"""
Tests for the scenario scripting system.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.shadowengine.modding.scenario import (
    TriggerType, ActionType, EventTrigger, EventAction,
    ScriptedEvent, CharacterTemplate, LocationTemplate,
    ConflictTemplate, ScenarioScript, ScenarioValidator,
    ScenarioLoader,
)


class TestTriggerType:
    """Tests for TriggerType enum."""

    def test_all_trigger_types_exist(self):
        """All expected trigger types exist."""
        expected = [
            "ON_GAME_START", "ON_TIME", "AFTER_DELAY",
            "ON_ENTER_LOCATION", "ON_EXIT_LOCATION", "ON_FIRST_VISIT",
            "ON_TALK_TO", "ON_CHARACTER_CRACK", "ON_CHARACTER_DEATH",
            "ON_DISCOVER_FACT", "ON_DISCOVER_EVIDENCE", "ON_REVELATION",
            "ON_PROGRESS", "ON_ACCUSATION", "ON_CORRECT_ACCUSATION", "ON_WRONG_ACCUSATION",
            "ON_TAKE_ITEM", "ON_USE_ITEM", "ON_GIVE_ITEM",
            "ON_TENSION_THRESHOLD", "ON_WEATHER_CHANGE", "ON_MORAL_SHIFT",
            "CUSTOM",
        ]
        for name in expected:
            assert hasattr(TriggerType, name)

    def test_trigger_type_count(self):
        """Correct number of trigger types."""
        assert len(TriggerType) >= 23


class TestActionType:
    """Tests for ActionType enum."""

    def test_all_action_types_exist(self):
        """All expected action types exist."""
        expected = [
            "SHOW_DIALOGUE", "SHOW_NARRATION", "SET_DIALOGUE_OPTION",
            "SPAWN_CHARACTER", "MOVE_CHARACTER", "REMOVE_CHARACTER",
            "SET_CHARACTER_STATE", "SET_CHARACTER_MOOD", "CRACK_CHARACTER",
            "UNLOCK_LOCATION", "LOCK_LOCATION", "MODIFY_LOCATION",
            "ADD_ITEM", "REMOVE_ITEM", "REVEAL_EVIDENCE",
            "TRIGGER_REVELATION", "SET_PROGRESS", "TRIGGER_TWIST", "SET_TENSION",
            "SET_WEATHER", "SET_TIME", "PLAY_SOUND", "PLAY_MUSIC",
            "SAVE_CHECKPOINT", "END_GAME", "SET_FLAG", "INCREMENT_COUNTER",
            "CUSTOM", "CALL_FUNCTION",
        ]
        for name in expected:
            assert hasattr(ActionType, name)

    def test_action_type_count(self):
        """Correct number of action types."""
        assert len(ActionType) >= 24


class TestEventTrigger:
    """Tests for EventTrigger."""

    def test_create_trigger(self, event_trigger):
        """Can create event trigger."""
        assert event_trigger.trigger_type == TriggerType.ON_ENTER_LOCATION
        assert event_trigger.target == "office"

    def test_default_values(self):
        """Default values are set."""
        trigger = EventTrigger(trigger_type=TriggerType.ON_GAME_START)
        assert trigger.target is None
        assert trigger.value is None
        assert trigger.conditions == {}
        assert trigger.once is False
        assert trigger.priority == 0
        assert trigger.triggered is False

    def test_check_conditions(self, event_trigger):
        """Can check conditions."""
        event_trigger.conditions = {"has_key": True}

        game_state = {"has_key": True}
        assert event_trigger.check_conditions(game_state) is True

        game_state = {"has_key": False}
        assert event_trigger.check_conditions(game_state) is False

    def test_can_trigger(self, event_trigger):
        """Can check if trigger can fire."""
        game_state = {}
        assert event_trigger.can_trigger(game_state) is True

        event_trigger.once = True
        event_trigger.triggered = True
        assert event_trigger.can_trigger(game_state) is False

    def test_mark_triggered(self, event_trigger):
        """Can mark trigger as fired."""
        event_trigger.mark_triggered()
        assert event_trigger.triggered is True

    def test_reset(self, event_trigger):
        """Can reset trigger state."""
        event_trigger.triggered = True
        event_trigger.reset()
        assert event_trigger.triggered is False

    def test_serialization(self, event_trigger):
        """EventTrigger can be serialized."""
        data = event_trigger.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = EventTrigger.from_dict(restored_data)

        assert restored.trigger_type == event_trigger.trigger_type
        assert restored.target == event_trigger.target


class TestEventAction:
    """Tests for EventAction."""

    def test_create_action(self, event_action):
        """Can create event action."""
        assert event_action.action_type == ActionType.SHOW_DIALOGUE
        assert event_action.target == "detective"

    def test_default_values(self):
        """Default values are set."""
        action = EventAction(action_type=ActionType.PLAY_SOUND)
        assert action.target is None
        assert action.value is None
        assert action.parameters == {}
        assert action.delay == 0.0
        assert action.duration == 0.0

    def test_execute(self, event_action):
        """Can execute action."""
        # Stub implementation returns True
        result = event_action.execute(None)
        assert result is True

    def test_serialization(self, event_action):
        """EventAction can be serialized."""
        data = event_action.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = EventAction.from_dict(restored_data)

        assert restored.action_type == event_action.action_type
        assert restored.target == event_action.target


class TestScriptedEvent:
    """Tests for ScriptedEvent."""

    def test_create_event(self, scripted_event):
        """Can create scripted event."""
        assert scripted_event.id == "intro_event"
        assert scripted_event.name == "Introduction"

    def test_add_trigger(self, scripted_event, event_trigger):
        """Can add trigger."""
        initial_count = len(scripted_event.triggers)
        scripted_event.add_trigger(event_trigger)
        assert len(scripted_event.triggers) == initial_count + 1

    def test_add_action(self, scripted_event, event_action):
        """Can add action."""
        initial_count = len(scripted_event.actions)
        scripted_event.add_action(event_action)
        assert len(scripted_event.actions) == initial_count + 1

    def test_can_execute_disabled(self, scripted_event):
        """Disabled events cannot execute."""
        scripted_event.enabled = False
        assert scripted_event.can_execute({}) is False

    def test_can_execute_max_reached(self, scripted_event):
        """Events with max executions reached cannot execute."""
        scripted_event.max_executions = 1
        scripted_event.executed_count = 1
        assert scripted_event.can_execute({}) is False

    def test_can_execute_no_triggers(self, scripted_event):
        """Events with no triggers cannot execute."""
        scripted_event.triggers = []
        assert scripted_event.can_execute({}) is False

    def test_can_execute_require_all_triggers(self, scripted_event, event_trigger):
        """Require all triggers mode."""
        scripted_event.triggers = [event_trigger]
        scripted_event.require_all_triggers = True
        assert scripted_event.can_execute({}) is True

        # Add failing trigger
        failing_trigger = EventTrigger(
            trigger_type=TriggerType.ON_TALK_TO,
            target="nobody",
            conditions={"impossible": True}
        )
        scripted_event.triggers.append(failing_trigger)
        assert scripted_event.can_execute({}) is False

    def test_execute(self, scripted_event, event_action):
        """Can execute event."""
        scripted_event.actions = [event_action]
        result = scripted_event.execute(None)
        assert result is True
        assert scripted_event.executed_count == 1

    def test_reset(self, scripted_event, event_trigger):
        """Can reset event state."""
        scripted_event.triggers = [event_trigger]
        scripted_event.executed_count = 5
        event_trigger.triggered = True

        scripted_event.reset()
        assert scripted_event.executed_count == 0
        assert event_trigger.triggered is False

    def test_serialization(self, scripted_event):
        """ScriptedEvent can be serialized."""
        data = scripted_event.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = ScriptedEvent.from_dict(restored_data)

        assert restored.id == scripted_event.id
        assert restored.name == scripted_event.name


class TestCharacterTemplate:
    """Tests for CharacterTemplate."""

    def test_create_template(self, character_template):
        """Can create character template."""
        assert character_template.id == "detective"
        assert character_template.name == "Detective"
        assert character_template.archetype == "corrupt_cop"

    def test_default_values(self):
        """Default values are set."""
        template = CharacterTemplate(
            id="test",
            name="Test",
            archetype="test"
        )
        assert template.starting_mood == "neutral"
        assert template.known_facts == []
        assert template.secrets == []
        assert template.is_culprit is False
        assert template.is_victim is False

    def test_narrative_roles(self, character_template):
        """Can set narrative roles."""
        character_template.is_culprit = True
        character_template.is_witness = True
        assert character_template.is_culprit is True
        assert character_template.is_witness is True

    def test_serialization(self, character_template):
        """CharacterTemplate can be serialized."""
        data = character_template.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = CharacterTemplate.from_dict(restored_data)

        assert restored.id == character_template.id
        assert restored.name == character_template.name
        assert restored.archetype == character_template.archetype


class TestLocationTemplate:
    """Tests for LocationTemplate."""

    def test_create_template(self, location_template):
        """Can create location template."""
        assert location_template.id == "office"
        assert location_template.name == "Detective's Office"

    def test_default_values(self):
        """Default values are set."""
        template = LocationTemplate(id="test", name="Test")
        assert template.is_outdoor is False
        assert template.base_light_level == 0.5
        assert template.exits == {}
        assert template.items == []
        assert template.initially_locked is False

    def test_exits(self, location_template):
        """Can set exits."""
        location_template.exits = {"north": "hallway", "east": "street"}
        assert "north" in location_template.exits
        assert location_template.exits["north"] == "hallway"

    def test_accessibility(self, location_template):
        """Can set accessibility requirements."""
        location_template.requires_key = "office_key"
        location_template.initially_locked = True
        assert location_template.requires_key == "office_key"
        assert location_template.initially_locked is True

    def test_serialization(self, location_template):
        """LocationTemplate can be serialized."""
        data = location_template.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = LocationTemplate.from_dict(restored_data)

        assert restored.id == location_template.id
        assert restored.name == location_template.name


class TestConflictTemplate:
    """Tests for ConflictTemplate."""

    def test_create_template(self, conflict_template):
        """Can create conflict template."""
        assert conflict_template.id == "murder_case"
        assert conflict_template.conflict_type == "murder"

    def test_default_values(self):
        """Default values are set."""
        template = ConflictTemplate(
            id="test",
            name="Test",
            conflict_type="theft"
        )
        assert template.evidence_chain == []
        assert template.revelations == []
        assert template.has_twist is False

    def test_solution_details(self, conflict_template):
        """Can set solution details."""
        conflict_template.motive = "revenge"
        conflict_template.method = "poison"
        conflict_template.opportunity = "alone in room"
        assert conflict_template.motive == "revenge"
        assert conflict_template.method == "poison"

    def test_twist(self, conflict_template):
        """Can set twist details."""
        conflict_template.has_twist = True
        conflict_template.twist_type = "identity"
        conflict_template.twist_description = "The victim is actually alive"
        assert conflict_template.has_twist is True
        assert conflict_template.twist_type == "identity"

    def test_serialization(self, conflict_template):
        """ConflictTemplate can be serialized."""
        data = conflict_template.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = ConflictTemplate.from_dict(restored_data)

        assert restored.id == conflict_template.id
        assert restored.conflict_type == conflict_template.conflict_type


class TestScenarioScript:
    """Tests for ScenarioScript."""

    def test_create_scenario(self, scenario_script):
        """Can create scenario script."""
        assert scenario_script.id == "test_scenario"
        assert scenario_script.name == "Test Scenario"

    def test_default_values(self):
        """Default values are set."""
        script = ScenarioScript(id="test", name="Test")
        assert script.version == "1.0.0"
        assert script.author == "Unknown"
        assert script.starting_time == 20
        assert script.starting_weather == "clear"
        assert script.starting_tension == 0.3
        assert script.difficulty == "normal"

    def test_get_character(self, scenario_script, character_template):
        """Can get character by ID."""
        scenario_script.characters = [character_template]
        result = scenario_script.get_character(character_template.id)
        assert result is not None
        assert result.id == character_template.id

        result = scenario_script.get_character("nonexistent")
        assert result is None

    def test_get_location(self, scenario_script, location_template):
        """Can get location by ID."""
        scenario_script.locations = [location_template]
        result = scenario_script.get_location(location_template.id)
        assert result is not None
        assert result.id == location_template.id

        result = scenario_script.get_location("nonexistent")
        assert result is None

    def test_get_event(self, scenario_script, scripted_event):
        """Can get event by ID."""
        scenario_script.events = [scripted_event]
        result = scenario_script.get_event(scripted_event.id)
        assert result is not None
        assert result.id == scripted_event.id

        result = scenario_script.get_event("nonexistent")
        assert result is None

    def test_get_active_events(self, scenario_script, scripted_event, event_trigger):
        """Can get active events."""
        scripted_event.triggers = [event_trigger]
        scenario_script.events = [scripted_event]

        active = scenario_script.get_active_events({})
        assert len(active) == 1
        assert active[0].id == scripted_event.id

    def test_full_scenario(
        self, scenario_script, character_template, location_template,
        conflict_template, scripted_event
    ):
        """Can create full scenario with all elements."""
        scenario_script.conflict = conflict_template
        scenario_script.characters = [character_template]
        scenario_script.locations = [location_template]
        scenario_script.events = [scripted_event]
        scenario_script.starting_location = location_template.id

        assert scenario_script.conflict is not None
        assert len(scenario_script.characters) == 1
        assert len(scenario_script.locations) == 1
        assert len(scenario_script.events) == 1

    def test_serialization(self, scenario_script, character_template, location_template):
        """ScenarioScript can be serialized."""
        scenario_script.characters = [character_template]
        scenario_script.locations = [location_template]

        data = scenario_script.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = ScenarioScript.from_dict(restored_data)

        assert restored.id == scenario_script.id
        assert restored.name == scenario_script.name
        assert len(restored.characters) == 1
        assert len(restored.locations) == 1


class TestScenarioValidator:
    """Tests for ScenarioValidator."""

    def test_create_validator(self):
        """Can create scenario validator."""
        validator = ScenarioValidator()
        assert validator.errors == []
        assert validator.warnings == []

    def test_validate_empty_scenario(self):
        """Empty scenario fails validation."""
        validator = ScenarioValidator()
        script = ScenarioScript(id="", name="")
        result = validator.validate(script)
        assert result is False
        assert len(validator.errors) > 0

    def test_validate_minimal_scenario(self, scenario_script):
        """Minimal valid scenario passes."""
        validator = ScenarioValidator()
        result = validator.validate(scenario_script)
        assert result is True

    def test_validate_duplicate_character_ids(self, scenario_script, character_template):
        """Duplicate character IDs are detected."""
        validator = ScenarioValidator()
        scenario_script.characters = [character_template, character_template]
        result = validator.validate(scenario_script)
        assert result is False
        assert any("Duplicate character" in e for e in validator.errors)

    def test_validate_duplicate_location_ids(self, scenario_script, location_template):
        """Duplicate location IDs are detected."""
        validator = ScenarioValidator()
        scenario_script.locations = [location_template, location_template]
        result = validator.validate(scenario_script)
        assert result is False
        assert any("Duplicate location" in e for e in validator.errors)

    def test_validate_invalid_starting_location(
        self, scenario_script, location_template
    ):
        """Invalid starting location is detected."""
        validator = ScenarioValidator()
        scenario_script.locations = [location_template]
        scenario_script.starting_location = "nonexistent"
        result = validator.validate(scenario_script)
        assert result is False
        assert any("Starting location" in e for e in validator.errors)

    def test_validate_conflict(self, scenario_script, conflict_template):
        """Conflict is validated."""
        validator = ScenarioValidator()
        conflict_template.conflict_type = ""
        scenario_script.conflict = conflict_template
        result = validator.validate(scenario_script)
        assert result is False

    def test_validate_character_no_name(self, scenario_script, character_template):
        """Character without name fails."""
        validator = ScenarioValidator()
        character_template.name = ""
        scenario_script.characters = [character_template]
        result = validator.validate(scenario_script)
        assert result is False

    def test_validate_warnings(self, scenario_script, conflict_template):
        """Warnings are collected."""
        validator = ScenarioValidator()
        conflict_template.evidence_chain = []
        scenario_script.conflict = conflict_template
        validator.validate(scenario_script)
        assert len(validator.warnings) > 0


class TestScenarioLoader:
    """Tests for ScenarioLoader."""

    def test_create_loader(self):
        """Can create scenario loader."""
        loader = ScenarioLoader()
        assert loader.scenarios_dir == Path("scenarios")

    def test_create_loader_custom_dir(self):
        """Can create loader with custom directory."""
        loader = ScenarioLoader("custom/scenarios")
        assert loader.scenarios_dir == Path("custom/scenarios")

    def test_list_available_empty(self):
        """List available returns empty for nonexistent dir."""
        loader = ScenarioLoader("nonexistent_dir")
        available = loader.list_available()
        assert available == []

    def test_load_nonexistent(self):
        """Loading nonexistent scenario returns None."""
        loader = ScenarioLoader()
        result = loader.load("nonexistent_scenario")
        assert result is None

    def test_save_and_load(self, scenario_script, character_template):
        """Can save and load scenario."""
        scenario_script.characters = [character_template]

        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ScenarioLoader(tmpdir)
            file_path = Path(tmpdir) / "test.json"

            # Save
            loader.save(scenario_script, str(file_path))
            assert file_path.exists()

            # Load
            loaded = loader.load_from_file(str(file_path))
            assert loaded.id == scenario_script.id
            assert loaded.name == scenario_script.name
            assert len(loaded.characters) == 1

    def test_cache(self, scenario_script):
        """Loader caches loaded scenarios."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ScenarioLoader(tmpdir)
            file_path = Path(tmpdir) / f"{scenario_script.id}.json"

            loader.save(scenario_script, str(file_path))

            # First load
            loaded1 = loader.load(scenario_script.id)
            assert loaded1 is not None

            # Should be cached
            assert scenario_script.id in loader.get_loaded()

            # Second load should return cached
            loaded2 = loader.load(scenario_script.id)
            assert loaded2 is loaded1

    def test_unload(self, scenario_script):
        """Can unload scenario from cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ScenarioLoader(tmpdir)
            file_path = Path(tmpdir) / f"{scenario_script.id}.json"

            loader.save(scenario_script, str(file_path))
            loader.load(scenario_script.id)

            assert scenario_script.id in loader.get_loaded()

            result = loader.unload(scenario_script.id)
            assert result is True
            assert scenario_script.id not in loader.get_loaded()

    def test_unload_nonexistent(self):
        """Unloading nonexistent returns False."""
        loader = ScenarioLoader()
        result = loader.unload("nonexistent")
        assert result is False


# Run all scenario tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
