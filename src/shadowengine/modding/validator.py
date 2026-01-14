"""
Mod Validation System for ShadowEngine.

Provides comprehensive validation for all mod content including
theme packs, archetypes, scenarios, and custom content.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Any, Set
from pathlib import Path
import json
import re


class ValidationSeverity(Enum):
    """Severity level of validation issues."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class ValidationError:
    """A validation error."""

    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    path: str = ""  # Path to the problematic element
    suggestion: str = ""  # Suggested fix

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "severity": self.severity.name,
            "path": self.path,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationWarning:
    """A validation warning."""

    message: str
    path: str = ""
    suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "path": self.path,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """Result of validation."""

    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    info: List[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @property
    def has_critical_errors(self) -> bool:
        return any(e.severity == ValidationSeverity.CRITICAL for e in self.errors)

    def add_error(
        self,
        message: str,
        path: str = "",
        suggestion: str = "",
        severity: ValidationSeverity = ValidationSeverity.ERROR
    ) -> None:
        """Add an error."""
        self.errors.append(ValidationError(
            message=message,
            severity=severity,
            path=path,
            suggestion=suggestion
        ))
        self.valid = False

    def add_warning(
        self,
        message: str,
        path: str = "",
        suggestion: str = ""
    ) -> None:
        """Add a warning."""
        self.warnings.append(ValidationWarning(
            message=message,
            path=path,
            suggestion=suggestion
        ))

    def add_info(self, message: str) -> None:
        """Add an info message."""
        self.info.append(message)

    def merge(self, other: 'ValidationResult') -> None:
        """Merge another result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)
        if not other.valid:
            self.valid = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "info": self.info,
        }

    def summary(self) -> str:
        """Get a summary string."""
        status = "VALID" if self.valid else "INVALID"
        return f"{status}: {self.error_count} errors, {self.warning_count} warnings"


class ModValidator:
    """
    Comprehensive validator for mod content.

    Validates theme packs, archetypes, scenarios, and
    ensures compatibility and consistency.
    """

    def __init__(self):
        # ID pattern for validation
        self._id_pattern = re.compile(r'^[a-z][a-z0-9_]*$')

        # Known built-in IDs
        self._builtin_archetypes = {
            "protector", "opportunist", "true_believer", "survivor",
            "authority", "outsider", "innocent", "guilty"
        }
        self._builtin_conflicts = {
            "murder", "theft", "betrayal", "conspiracy",
            "disappearance", "blackmail", "sabotage"
        }
        self._builtin_weather = {
            "clear", "cloudy", "rain", "fog", "storm"
        }

    def validate_id(self, id_value: str, context: str = "") -> ValidationResult:
        """Validate an ID string."""
        result = ValidationResult(valid=True)

        if not id_value:
            result.add_error(
                "ID cannot be empty",
                path=context,
                severity=ValidationSeverity.CRITICAL
            )
            return result

        if not self._id_pattern.match(id_value):
            result.add_error(
                f"Invalid ID format: '{id_value}'",
                path=context,
                suggestion="IDs should be lowercase with underscores, starting with a letter"
            )

        if len(id_value) > 64:
            result.add_error(
                f"ID too long: {len(id_value)} chars (max 64)",
                path=context
            )

        return result

    def validate_theme_pack(self, pack: Any) -> ValidationResult:
        """
        Validate a theme pack.

        Args:
            pack: ThemePack instance

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        # Validate ID
        id_result = self.validate_id(pack.id, "theme_pack.id")
        result.merge(id_result)

        # Required fields
        if not pack.name:
            result.add_error(
                "Theme pack must have a name",
                path="theme_pack.name"
            )

        # Validate vocabulary
        if pack.vocabulary:
            vocab_result = self._validate_vocabulary(pack.vocabulary)
            result.merge(vocab_result)

        # Validate weather config
        if pack.weather:
            weather_result = self._validate_weather_config(pack.weather)
            result.merge(weather_result)

        # Validate atmosphere
        if pack.atmosphere:
            atmos_result = self._validate_atmosphere(pack.atmosphere)
            result.merge(atmos_result)

        # Validate theme config
        if pack.theme:
            theme_result = self._validate_theme_config(pack.theme)
            result.merge(theme_result)

        # Check for empty content
        if (not pack.archetypes and not pack.conflicts and
            not pack.art_templates and not pack.dialogue_templates):
            result.add_warning(
                "Theme pack has no custom content",
                suggestion="Consider adding custom archetypes, conflicts, or art templates"
            )

        result.add_info(f"Theme pack '{pack.name}' validation complete")
        return result

    def _validate_vocabulary(self, vocab: Any) -> ValidationResult:
        """Validate vocabulary configuration."""
        result = ValidationResult(valid=True)

        # Check verb lists
        verb_types = ["examine", "talk", "take", "use", "go", "attack"]
        for vtype in verb_types:
            verbs = getattr(vocab, f"{vtype}_verbs", [])
            if not verbs:
                result.add_warning(
                    f"Empty verb list: {vtype}_verbs",
                    path=f"vocabulary.{vtype}_verbs",
                    suggestion="Add at least one verb"
                )

        return result

    def _validate_weather_config(self, weather: Any) -> ValidationResult:
        """Validate weather configuration."""
        result = ValidationResult(valid=True)

        # Check weight distribution
        total_weight = sum(weather.weather_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            result.add_warning(
                f"Weather weights sum to {total_weight:.2f}, should sum to 1.0",
                path="weather.weather_weights",
                suggestion="Normalize weights to sum to 1.0"
            )

        # Check for negative weights
        for wtype, weight in weather.weather_weights.items():
            if weight < 0:
                result.add_error(
                    f"Negative weight for weather type '{wtype}'",
                    path=f"weather.weather_weights.{wtype}"
                )

        return result

    def _validate_atmosphere(self, atmosphere: Any) -> ValidationResult:
        """Validate atmosphere configuration."""
        result = ValidationResult(valid=True)

        # Check effect intensity
        if atmosphere.effect_intensity < 0 or atmosphere.effect_intensity > 1:
            result.add_error(
                f"Effect intensity {atmosphere.effect_intensity} out of range [0, 1]",
                path="atmosphere.effect_intensity"
            )

        # Check tempo
        if atmosphere.tempo_base < 20 or atmosphere.tempo_base > 300:
            result.add_warning(
                f"Unusual tempo: {atmosphere.tempo_base} BPM",
                path="atmosphere.tempo_base",
                suggestion="Typical range is 60-180 BPM"
            )

        return result

    def _validate_theme_config(self, theme: Any) -> ValidationResult:
        """Validate theme configuration."""
        result = ValidationResult(valid=True)

        # Check time periods
        for period, (start, end) in theme.time_periods.items():
            if not (0 <= start <= 24 and 0 <= end <= 24):
                result.add_error(
                    f"Invalid time range for period '{period}': {start}-{end}",
                    path=f"theme.time_periods.{period}"
                )

        # Check conflict types
        for ctype in theme.conflict_types:
            if ctype not in self._builtin_conflicts:
                result.add_info(f"Custom conflict type: {ctype}")

        return result

    def validate_archetype(self, archetype: Any) -> ValidationResult:
        """
        Validate a custom archetype.

        Args:
            archetype: ArchetypeDefinition instance

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        # Validate ID
        id_result = self.validate_id(archetype.id, "archetype.id")
        result.merge(id_result)

        # Required fields
        if not archetype.name:
            result.add_error(
                "Archetype must have a name",
                path="archetype.name"
            )

        # Validate motivations
        if archetype.motivations:
            motiv_result = self._validate_motivations(archetype.motivations)
            result.merge(motiv_result)

        # Validate behavior
        if archetype.behavior:
            behav_result = self._validate_behavior(archetype.behavior)
            result.merge(behav_result)

        # Check role flags
        if not (archetype.can_be_culprit or archetype.can_be_witness or
                archetype.can_be_victim or archetype.can_be_red_herring):
            result.add_warning(
                "Archetype cannot play any narrative role",
                suggestion="Enable at least one role flag"
            )

        # Check dialogue templates
        if not archetype.greeting_templates:
            result.add_warning(
                "No greeting templates defined",
                path="archetype.greeting_templates"
            )

        result.add_info(f"Archetype '{archetype.name}' validation complete")
        return result

    def _validate_motivations(self, motivations: Any) -> ValidationResult:
        """Validate motivation preset."""
        result = ValidationResult(valid=True)

        motivation_names = [
            "fear", "greed", "loyalty", "pride", "guilt",
            "ambition", "revenge", "love", "duty", "survival"
        ]

        for name in motivation_names:
            value = getattr(motivations, name, 50)
            if not (0 <= value <= 100):
                result.add_error(
                    f"Motivation '{name}' value {value} out of range [0, 100]",
                    path=f"motivations.{name}"
                )

        return result

    def _validate_behavior(self, behavior: Any) -> ValidationResult:
        """Validate behavior pattern."""
        result = ValidationResult(valid=True)

        # Check probability values
        probabilities = [
            ("lie_probability", behavior.lie_probability),
            ("deflect_probability", behavior.deflect_probability),
            ("pressure_resistance", behavior.pressure_resistance),
        ]

        for name, value in probabilities:
            if not (0.0 <= value <= 1.0):
                result.add_error(
                    f"Probability '{name}' value {value} out of range [0, 1]",
                    path=f"behavior.{name}"
                )

        # Check thresholds
        thresholds = [
            ("trust_threshold", behavior.trust_threshold, 0, 100),
            ("anger_threshold", behavior.anger_threshold, 0.0, 1.0),
            ("fear_threshold", behavior.fear_threshold, 0.0, 1.0),
            ("breakdown_threshold", behavior.breakdown_threshold, 0.0, 1.0),
        ]

        for name, value, min_val, max_val in thresholds:
            if not (min_val <= value <= max_val):
                result.add_error(
                    f"Threshold '{name}' value {value} out of range [{min_val}, {max_val}]",
                    path=f"behavior.{name}"
                )

        return result

    def validate_scenario(self, scenario: Any) -> ValidationResult:
        """
        Validate a scenario script.

        Args:
            scenario: ScenarioScript instance

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        # Validate ID
        id_result = self.validate_id(scenario.id, "scenario.id")
        result.merge(id_result)

        # Required fields
        if not scenario.name:
            result.add_error(
                "Scenario must have a name",
                path="scenario.name"
            )

        # Collect all IDs for cross-referencing
        char_ids = {c.id for c in scenario.characters}
        loc_ids = {l.id for l in scenario.locations}
        {e.id for e in scenario.events}

        # Validate conflict
        if scenario.conflict:
            conflict_result = self._validate_conflict(scenario.conflict)
            result.merge(conflict_result)

        # Validate characters
        for i, char in enumerate(scenario.characters):
            char_result = self._validate_character(char, f"characters[{i}]", loc_ids)
            result.merge(char_result)

        # Check for duplicate character IDs
        seen_char_ids = set()
        for char in scenario.characters:
            if char.id in seen_char_ids:
                result.add_error(
                    f"Duplicate character ID: {char.id}",
                    severity=ValidationSeverity.ERROR
                )
            seen_char_ids.add(char.id)

        # Validate locations
        for i, loc in enumerate(scenario.locations):
            loc_result = self._validate_location(loc, f"locations[{i}]", loc_ids, char_ids)
            result.merge(loc_result)

        # Check for duplicate location IDs
        seen_loc_ids = set()
        for loc in scenario.locations:
            if loc.id in seen_loc_ids:
                result.add_error(
                    f"Duplicate location ID: {loc.id}",
                    severity=ValidationSeverity.ERROR
                )
            seen_loc_ids.add(loc.id)

        # Validate events
        for i, event in enumerate(scenario.events):
            event_result = self._validate_event(event, f"events[{i}]", char_ids, loc_ids)
            result.merge(event_result)

        # Check starting location
        if scenario.starting_location and scenario.starting_location not in loc_ids:
            result.add_error(
                f"Starting location '{scenario.starting_location}' not found",
                path="scenario.starting_location"
            )

        # Check starting time
        if not (0 <= scenario.starting_time <= 23):
            result.add_error(
                f"Invalid starting time: {scenario.starting_time}",
                path="scenario.starting_time",
                suggestion="Use 0-23 for hour of day"
            )

        # Check tension
        if not (0.0 <= scenario.starting_tension <= 1.0):
            result.add_error(
                f"Starting tension {scenario.starting_tension} out of range [0, 1]",
                path="scenario.starting_tension"
            )

        result.add_info(f"Scenario '{scenario.name}' validation complete")
        return result

    def _validate_conflict(self, conflict: Any) -> ValidationResult:
        """Validate a conflict template."""
        result = ValidationResult(valid=True)

        if not conflict.conflict_type:
            result.add_error(
                "Conflict must have a type",
                path="conflict.conflict_type"
            )

        if not conflict.evidence_chain:
            result.add_warning(
                "Conflict has no evidence chain",
                path="conflict.evidence_chain",
                suggestion="Add fact IDs to the evidence chain"
            )

        if conflict.has_twist and not conflict.twist_description:
            result.add_warning(
                "Conflict has twist enabled but no description",
                path="conflict.twist_description"
            )

        return result

    def _validate_character(
        self,
        char: Any,
        path: str,
        valid_locations: Set[str]
    ) -> ValidationResult:
        """Validate a character template."""
        result = ValidationResult(valid=True)

        if not char.name:
            result.add_error(
                "Character must have a name",
                path=f"{path}.name"
            )

        if not char.archetype:
            result.add_warning(
                "Character has no archetype",
                path=f"{path}.archetype"
            )

        if char.starting_location and char.starting_location not in valid_locations:
            result.add_warning(
                f"Character starting location '{char.starting_location}' not found",
                path=f"{path}.starting_location"
            )

        return result

    def _validate_location(
        self,
        loc: Any,
        path: str,
        valid_locations: Set[str],
        valid_chars: Set[str]
    ) -> ValidationResult:
        """Validate a location template."""
        result = ValidationResult(valid=True)

        if not loc.name:
            result.add_error(
                "Location must have a name",
                path=f"{path}.name"
            )

        if not (0.0 <= loc.base_light_level <= 1.0):
            result.add_error(
                f"Light level {loc.base_light_level} out of range [0, 1]",
                path=f"{path}.base_light_level"
            )

        # Check exits
        for direction, target in loc.exits.items():
            if target not in valid_locations:
                result.add_warning(
                    f"Exit '{direction}' points to unknown location '{target}'",
                    path=f"{path}.exits.{direction}"
                )

        return result

    def _validate_event(
        self,
        event: Any,
        path: str,
        valid_chars: Set[str],
        valid_locs: Set[str]
    ) -> ValidationResult:
        """Validate a scripted event."""
        result = ValidationResult(valid=True)

        if not event.triggers:
            result.add_warning(
                "Event has no triggers",
                path=f"{path}.triggers"
            )

        if not event.actions:
            result.add_warning(
                "Event has no actions",
                path=f"{path}.actions"
            )

        # Validate each trigger
        for i, trigger in enumerate(event.triggers):
            if trigger.target:
                # Check if target exists based on trigger type
                if trigger.trigger_type.name.endswith("_LOCATION"):
                    if trigger.target not in valid_locs:
                        result.add_warning(
                            f"Trigger target location '{trigger.target}' not found",
                            path=f"{path}.triggers[{i}].target"
                        )
                elif "CHARACTER" in trigger.trigger_type.name or "TALK" in trigger.trigger_type.name:
                    if trigger.target not in valid_chars:
                        result.add_warning(
                            f"Trigger target character '{trigger.target}' not found",
                            path=f"{path}.triggers[{i}].target"
                        )

        return result

    def validate_json_file(self, file_path: str) -> ValidationResult:
        """
        Validate a JSON mod file.

        Args:
            file_path: Path to the JSON file

        Returns:
            ValidationResult
        """
        result = ValidationResult(valid=True)

        path = Path(file_path)
        if not path.exists():
            result.add_error(
                f"File not found: {file_path}",
                severity=ValidationSeverity.CRITICAL
            )
            return result

        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            result.add_error(
                f"Invalid JSON: {e}",
                severity=ValidationSeverity.CRITICAL
            )
            return result

        # Check for required mod_info section
        if "mod_info" not in data:
            result.add_error(
                "Missing 'mod_info' section",
                suggestion="Add mod_info with id, name, and version"
            )

        result.add_info(f"JSON file '{path.name}' is valid")
        return result


# Convenience functions

def validate_theme_pack(pack: Any) -> ValidationResult:
    """Validate a theme pack."""
    validator = ModValidator()
    return validator.validate_theme_pack(pack)


def validate_archetype(archetype: Any) -> ValidationResult:
    """Validate a custom archetype."""
    validator = ModValidator()
    return validator.validate_archetype(archetype)


def validate_scenario(scenario: Any) -> ValidationResult:
    """Validate a scenario script."""
    validator = ModValidator()
    return validator.validate_scenario(scenario)


def validate_json_file(file_path: str) -> ValidationResult:
    """Validate a JSON mod file."""
    validator = ModValidator()
    return validator.validate_json_file(file_path)
