"""
Tests for the mod validation system.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.shadowengine.modding.validator import (
    ValidationSeverity, ValidationError, ValidationWarning,
    ValidationResult, ModValidator,
    validate_theme_pack, validate_archetype, validate_scenario,
    validate_json_file,
)
from src.shadowengine.modding.theme_pack import (
    ThemePack, VocabularyConfig, WeatherConfig, AtmosphereConfig, ThemeConfig,
)
from src.shadowengine.modding.archetype import (
    ArchetypeDefinition, MotivationPreset, BehaviorPattern,
    BehaviorTendency, ResponseStyle,
)
from src.shadowengine.modding.scenario import (
    ScenarioScript, CharacterTemplate, LocationTemplate, ConflictTemplate,
    ScriptedEvent, EventTrigger, EventAction, TriggerType, ActionType,
)


class TestValidationSeverity:
    """Tests for ValidationSeverity enum."""

    def test_all_severities_exist(self):
        """All expected severities exist."""
        assert hasattr(ValidationSeverity, "INFO")
        assert hasattr(ValidationSeverity, "WARNING")
        assert hasattr(ValidationSeverity, "ERROR")
        assert hasattr(ValidationSeverity, "CRITICAL")


class TestValidationError:
    """Tests for ValidationError."""

    def test_create_error(self):
        """Can create validation error."""
        error = ValidationError(message="Test error")
        assert error.message == "Test error"
        assert error.severity == ValidationSeverity.ERROR

    def test_create_with_all_fields(self):
        """Can create error with all fields."""
        error = ValidationError(
            message="Test error",
            severity=ValidationSeverity.CRITICAL,
            path="test.field",
            suggestion="Fix it"
        )
        assert error.severity == ValidationSeverity.CRITICAL
        assert error.path == "test.field"
        assert error.suggestion == "Fix it"

    def test_serialization(self):
        """ValidationError can be serialized."""
        error = ValidationError(
            message="Test",
            severity=ValidationSeverity.ERROR,
            path="test.path",
            suggestion="Fix"
        )
        data = error.to_dict()
        assert data["message"] == "Test"
        assert data["severity"] == "ERROR"
        assert data["path"] == "test.path"


class TestValidationWarning:
    """Tests for ValidationWarning."""

    def test_create_warning(self):
        """Can create validation warning."""
        warning = ValidationWarning(message="Test warning")
        assert warning.message == "Test warning"

    def test_create_with_all_fields(self):
        """Can create warning with all fields."""
        warning = ValidationWarning(
            message="Test warning",
            path="test.field",
            suggestion="Consider fixing"
        )
        assert warning.path == "test.field"
        assert warning.suggestion == "Consider fixing"

    def test_serialization(self):
        """ValidationWarning can be serialized."""
        warning = ValidationWarning(
            message="Test",
            path="test.path"
        )
        data = warning.to_dict()
        assert data["message"] == "Test"
        assert data["path"] == "test.path"


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_create_valid_result(self):
        """Can create valid result."""
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert result.error_count == 0
        assert result.warning_count == 0

    def test_create_invalid_result(self):
        """Can create invalid result."""
        result = ValidationResult(valid=False)
        assert result.valid is False

    def test_add_error(self):
        """Can add error to result."""
        result = ValidationResult(valid=True)
        result.add_error("Test error")
        assert result.valid is False
        assert result.error_count == 1

    def test_add_error_with_details(self):
        """Can add error with details."""
        result = ValidationResult(valid=True)
        result.add_error(
            "Test error",
            path="test.path",
            suggestion="Fix it",
            severity=ValidationSeverity.CRITICAL
        )
        assert result.error_count == 1
        assert result.errors[0].severity == ValidationSeverity.CRITICAL

    def test_add_warning(self):
        """Can add warning to result."""
        result = ValidationResult(valid=True)
        result.add_warning("Test warning")
        assert result.valid is True  # Warnings don't invalidate
        assert result.warning_count == 1

    def test_add_info(self):
        """Can add info message."""
        result = ValidationResult(valid=True)
        result.add_info("Test info")
        assert len(result.info) == 1
        assert result.info[0] == "Test info"

    def test_has_critical_errors(self):
        """Can check for critical errors."""
        result = ValidationResult(valid=True)
        assert result.has_critical_errors is False

        result.add_error("Normal error")
        assert result.has_critical_errors is False

        result.add_error("Critical", severity=ValidationSeverity.CRITICAL)
        assert result.has_critical_errors is True

    def test_merge(self):
        """Can merge results."""
        result1 = ValidationResult(valid=True)
        result1.add_warning("Warning 1")

        result2 = ValidationResult(valid=False)
        result2.add_error("Error 1")
        result2.add_info("Info 1")

        result1.merge(result2)
        assert result1.valid is False
        assert result1.error_count == 1
        assert result1.warning_count == 1
        assert len(result1.info) == 1

    def test_summary(self):
        """Can get summary string."""
        result = ValidationResult(valid=True)
        summary = result.summary()
        assert "VALID" in summary
        assert "0 errors" in summary

        result.add_error("Error")
        summary = result.summary()
        assert "INVALID" in summary
        assert "1 errors" in summary

    def test_serialization(self):
        """ValidationResult can be serialized."""
        result = ValidationResult(valid=True)
        result.add_warning("Warning")
        result.add_info("Info")

        data = result.to_dict()
        assert data["valid"] is True
        assert len(data["warnings"]) == 1
        assert len(data["info"]) == 1


class TestModValidatorIDValidation:
    """Tests for ModValidator ID validation."""

    def test_valid_id(self):
        """Valid IDs pass."""
        validator = ModValidator()
        result = validator.validate_id("valid_id")
        assert result.valid is True

    def test_empty_id(self):
        """Empty ID fails."""
        validator = ModValidator()
        result = validator.validate_id("")
        assert result.valid is False
        assert result.has_critical_errors is True

    def test_invalid_id_format(self):
        """Invalid ID format fails."""
        validator = ModValidator()

        # Starts with number
        result = validator.validate_id("123_invalid")
        assert result.valid is False

        # Contains uppercase
        result = validator.validate_id("Invalid_Id")
        assert result.valid is False

        # Contains spaces
        result = validator.validate_id("invalid id")
        assert result.valid is False

    def test_id_too_long(self):
        """Too long ID fails."""
        validator = ModValidator()
        long_id = "a" * 100
        result = validator.validate_id(long_id)
        assert result.valid is False


class TestModValidatorThemePack:
    """Tests for ModValidator theme pack validation."""

    def test_valid_theme_pack(self):
        """Valid theme pack passes."""
        pack = ThemePack(
            id="test_theme",
            name="Test Theme"
        )
        result = validate_theme_pack(pack)
        assert result.valid is True

    def test_theme_pack_no_name(self):
        """Theme pack without name fails."""
        pack = ThemePack(id="test_theme", name="")
        result = validate_theme_pack(pack)
        assert result.valid is False

    def test_theme_pack_invalid_id(self):
        """Theme pack with invalid ID fails."""
        pack = ThemePack(id="InvalidID", name="Test")
        result = validate_theme_pack(pack)
        assert result.valid is False

    def test_theme_pack_empty_vocabulary(self):
        """Empty vocabulary generates warning."""
        pack = ThemePack(
            id="test_theme",
            name="Test Theme",
            vocabulary=VocabularyConfig(examine_verbs=[])
        )
        result = validate_theme_pack(pack)
        assert result.warning_count > 0

    def test_theme_pack_invalid_weather_weights(self):
        """Invalid weather weights generate warning."""
        pack = ThemePack(
            id="test_theme",
            name="Test Theme",
            weather=WeatherConfig(
                weather_weights={"rain": 0.5, "clear": 0.3}  # Doesn't sum to 1.0
            )
        )
        result = validate_theme_pack(pack)
        assert result.warning_count > 0

    def test_theme_pack_negative_weather_weight(self):
        """Negative weather weight fails."""
        pack = ThemePack(
            id="test_theme",
            name="Test Theme",
            weather=WeatherConfig(
                weather_weights={"rain": -0.5, "clear": 1.5}
            )
        )
        result = validate_theme_pack(pack)
        assert result.valid is False

    def test_theme_pack_invalid_effect_intensity(self):
        """Invalid effect intensity fails."""
        pack = ThemePack(
            id="test_theme",
            name="Test Theme",
            atmosphere=AtmosphereConfig(effect_intensity=1.5)
        )
        result = validate_theme_pack(pack)
        assert result.valid is False

    def test_theme_pack_unusual_tempo(self):
        """Unusual tempo generates warning."""
        pack = ThemePack(
            id="test_theme",
            name="Test Theme",
            atmosphere=AtmosphereConfig(tempo_base=500)
        )
        result = validate_theme_pack(pack)
        assert result.warning_count > 0

    def test_theme_pack_invalid_time_period(self):
        """Invalid time period fails."""
        pack = ThemePack(
            id="test_theme",
            name="Test Theme",
            theme=ThemeConfig(
                time_periods={"invalid": (25, 30)}
            )
        )
        result = validate_theme_pack(pack)
        assert result.valid is False


class TestModValidatorArchetype:
    """Tests for ModValidator archetype validation."""

    def test_valid_archetype(self):
        """Valid archetype passes."""
        archetype = ArchetypeDefinition(
            id="test_archetype",
            name="Test Archetype"
        )
        result = validate_archetype(archetype)
        assert result.valid is True

    def test_archetype_no_name(self):
        """Archetype without name fails."""
        archetype = ArchetypeDefinition(id="test_archetype", name="")
        result = validate_archetype(archetype)
        assert result.valid is False

    def test_archetype_invalid_motivation(self):
        """Invalid motivation value fails validation."""
        archetype = ArchetypeDefinition(
            id="test_archetype",
            name="Test",
            motivations=MotivationPreset(fear=150)  # Out of range - not clamped at construction
        )
        # MotivationPreset does not clamp on construction, so validation catches it
        result = validate_archetype(archetype)
        assert result.valid is False
        assert any("out of range" in str(e.message) for e in result.errors)

    def test_archetype_invalid_behavior_probability(self):
        """Invalid behavior probability fails."""
        archetype = ArchetypeDefinition(
            id="test_archetype",
            name="Test",
            behavior=BehaviorPattern(lie_probability=1.5)
        )
        result = validate_archetype(archetype)
        assert result.valid is False

    def test_archetype_no_roles(self):
        """Archetype with no roles generates warning."""
        archetype = ArchetypeDefinition(
            id="test_archetype",
            name="Test",
            can_be_culprit=False,
            can_be_witness=False,
            can_be_victim=False,
            can_be_red_herring=False
        )
        result = validate_archetype(archetype)
        assert result.warning_count > 0

    def test_archetype_no_greetings(self):
        """Archetype with no greetings generates warning."""
        archetype = ArchetypeDefinition(
            id="test_archetype",
            name="Test",
            greeting_templates=[]
        )
        result = validate_archetype(archetype)
        assert result.warning_count > 0


class TestModValidatorScenario:
    """Tests for ModValidator scenario validation."""

    def test_valid_scenario(self):
        """Valid scenario passes."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test Scenario"
        )
        result = validate_scenario(scenario)
        assert result.valid is True

    def test_scenario_no_name(self):
        """Scenario without name fails."""
        scenario = ScenarioScript(id="test_scenario", name="")
        result = validate_scenario(scenario)
        assert result.valid is False

    def test_scenario_duplicate_character_ids(self):
        """Duplicate character IDs fail."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test",
            characters=[
                CharacterTemplate(id="char1", name="Char 1", archetype="test"),
                CharacterTemplate(id="char1", name="Char 2", archetype="test")
            ]
        )
        result = validate_scenario(scenario)
        assert result.valid is False

    def test_scenario_duplicate_location_ids(self):
        """Duplicate location IDs fail."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test",
            locations=[
                LocationTemplate(id="loc1", name="Loc 1"),
                LocationTemplate(id="loc1", name="Loc 2")
            ]
        )
        result = validate_scenario(scenario)
        assert result.valid is False

    def test_scenario_invalid_starting_location(self):
        """Invalid starting location fails."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test",
            starting_location="nonexistent"
        )
        result = validate_scenario(scenario)
        assert result.valid is False

    def test_scenario_invalid_starting_time(self):
        """Invalid starting time fails."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test",
            starting_time=25
        )
        result = validate_scenario(scenario)
        assert result.valid is False

    def test_scenario_invalid_starting_tension(self):
        """Invalid starting tension fails."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test",
            starting_tension=1.5
        )
        result = validate_scenario(scenario)
        assert result.valid is False

    def test_scenario_conflict_no_type(self):
        """Conflict without type fails."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test",
            conflict=ConflictTemplate(id="c1", name="Conflict", conflict_type="")
        )
        result = validate_scenario(scenario)
        assert result.valid is False

    def test_scenario_conflict_no_evidence(self):
        """Conflict without evidence chain generates warning."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test",
            conflict=ConflictTemplate(
                id="c1",
                name="Conflict",
                conflict_type="murder",
                evidence_chain=[]
            )
        )
        result = validate_scenario(scenario)
        assert result.warning_count > 0

    def test_scenario_character_no_name(self):
        """Character without name fails."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test",
            characters=[
                CharacterTemplate(id="char1", name="", archetype="test")
            ]
        )
        result = validate_scenario(scenario)
        assert result.valid is False

    def test_scenario_character_invalid_location(self):
        """Character with invalid starting location generates warning."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test",
            characters=[
                CharacterTemplate(
                    id="char1",
                    name="Char",
                    archetype="test",
                    starting_location="nonexistent"
                )
            ]
        )
        result = validate_scenario(scenario)
        assert result.warning_count > 0

    def test_scenario_location_invalid_light_level(self):
        """Location with invalid light level fails."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test",
            locations=[
                LocationTemplate(id="loc1", name="Loc", base_light_level=1.5)
            ]
        )
        result = validate_scenario(scenario)
        assert result.valid is False

    def test_scenario_location_invalid_exit(self):
        """Location with invalid exit generates warning."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test",
            locations=[
                LocationTemplate(
                    id="loc1",
                    name="Loc",
                    exits={"north": "nonexistent"}
                )
            ]
        )
        result = validate_scenario(scenario)
        assert result.warning_count > 0

    def test_scenario_event_no_triggers(self):
        """Event without triggers generates warning."""
        scenario = ScenarioScript(
            id="test_scenario",
            name="Test",
            events=[
                ScriptedEvent(id="e1", name="Event", triggers=[], actions=[])
            ]
        )
        result = validate_scenario(scenario)
        assert result.warning_count > 0


class TestModValidatorJSONFile:
    """Tests for ModValidator JSON file validation."""

    def test_valid_json_file(self):
        """Valid JSON file passes."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump({"mod_info": {"id": "test", "name": "Test"}}, f)
            f.flush()

            result = validate_json_file(f.name)
            assert result.valid is True

    def test_nonexistent_file(self):
        """Nonexistent file fails."""
        result = validate_json_file("/nonexistent/file.json")
        assert result.valid is False
        assert result.has_critical_errors is True

    def test_invalid_json(self):
        """Invalid JSON fails."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            f.write("not valid json {{{")
            f.flush()

            result = validate_json_file(f.name)
            assert result.valid is False
            assert result.has_critical_errors is True

    def test_missing_mod_info(self):
        """Missing mod_info section fails."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump({"some_key": "some_value"}, f)
            f.flush()

            result = validate_json_file(f.name)
            assert result.valid is False


class TestConvenienceFunctions:
    """Tests for convenience validation functions."""

    def test_validate_theme_pack_function(self):
        """validate_theme_pack works."""
        pack = ThemePack(id="test", name="Test")
        result = validate_theme_pack(pack)
        assert isinstance(result, ValidationResult)

    def test_validate_archetype_function(self):
        """validate_archetype works."""
        archetype = ArchetypeDefinition(id="test", name="Test")
        result = validate_archetype(archetype)
        assert isinstance(result, ValidationResult)

    def test_validate_scenario_function(self):
        """validate_scenario works."""
        scenario = ScenarioScript(id="test", name="Test")
        result = validate_scenario(scenario)
        assert isinstance(result, ValidationResult)

    def test_validate_json_file_function(self):
        """validate_json_file works."""
        result = validate_json_file("/nonexistent")
        assert isinstance(result, ValidationResult)


# Run all validator tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
