"""
Fixtures for modding system tests.
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.shadowengine.modding.registry import ModRegistry, ModInfo, ModType
from src.shadowengine.modding.theme_pack import (
    ThemePack, ThemeConfig, VocabularyConfig,
    WeatherConfig, AtmosphereConfig,
)
from src.shadowengine.modding.archetype import (
    ArchetypeDefinition, MotivationPreset, BehaviorPattern,
    BehaviorTendency, ResponseStyle, ArchetypeRegistry,
)
from src.shadowengine.modding.scenario import (
    ScenarioScript, ScriptedEvent, EventTrigger, EventAction,
    TriggerType, ActionType, CharacterTemplate, LocationTemplate,
    ConflictTemplate,
)
from src.shadowengine.modding.validator import ModValidator, ValidationResult


@pytest.fixture
def mod_registry():
    """Fresh mod registry."""
    return ModRegistry()


@pytest.fixture
def mod_info():
    """Basic mod info."""
    return ModInfo(
        id="test_mod",
        name="Test Mod",
        version="1.0.0",
        author="Test Author",
        description="A test mod",
    )


@pytest.fixture
def theme_pack():
    """Basic theme pack."""
    return ThemePack(
        id="test_theme",
        name="Test Theme",
        author="Test Author",
        description="A test theme pack",
    )


@pytest.fixture
def cyberpunk_theme():
    """Cyberpunk theme pack."""
    return ThemePack(
        id="cyberpunk_test",
        name="Cyberpunk Test",
        vocabulary=VocabularyConfig(
            examine_verbs=["scan", "analyze", "probe"],
            talk_verbs=["ping", "message", "query"],
        ),
        atmosphere=AtmosphereConfig(
            primary_color="cyan",
            secondary_color="magenta",
        ),
        theme=ThemeConfig(
            location_types=["megacorp", "club", "server_farm"],
            conflict_types=["data_theft", "murder"],
        ),
    )


@pytest.fixture
def vocabulary_config():
    """Basic vocabulary config."""
    return VocabularyConfig()


@pytest.fixture
def weather_config():
    """Basic weather config."""
    return WeatherConfig()


@pytest.fixture
def atmosphere_config():
    """Basic atmosphere config."""
    return AtmosphereConfig()


@pytest.fixture
def theme_config():
    """Basic theme config."""
    return ThemeConfig()


@pytest.fixture
def motivation_preset():
    """Basic motivation preset."""
    return MotivationPreset(
        fear=60,
        greed=40,
        loyalty=80,
        pride=50,
        guilt=30,
    )


@pytest.fixture
def behavior_pattern():
    """Basic behavior pattern."""
    return BehaviorPattern(
        tendency=BehaviorTendency.EVASIVE,
        response_style=ResponseStyle.CALCULATED,
        cracks_easily=False,
        trust_threshold=60,
    )


@pytest.fixture
def archetype_definition(motivation_preset, behavior_pattern):
    """Basic archetype definition."""
    return ArchetypeDefinition(
        id="test_archetype",
        name="Test Archetype",
        description="A test archetype",
        motivations=motivation_preset,
        behavior=behavior_pattern,
        greeting_templates=["Hello there.", "What do you want?"],
        deflection_templates=["I don't want to talk about that."],
    )


@pytest.fixture
def archetype_registry():
    """Fresh archetype registry."""
    return ArchetypeRegistry()


@pytest.fixture
def character_template():
    """Basic character template."""
    return CharacterTemplate(
        id="detective",
        name="Detective",
        archetype="corrupt_cop",
        starting_location="office",
    )


@pytest.fixture
def location_template():
    """Basic location template."""
    return LocationTemplate(
        id="office",
        name="Detective's Office",
        description="A dimly lit office",
        ascii_art=["######", "#    #", "######"],
        exits={"north": "hallway"},
    )


@pytest.fixture
def conflict_template():
    """Basic conflict template."""
    return ConflictTemplate(
        id="murder_case",
        name="The Murder Case",
        conflict_type="murder",
        evidence_chain=["clue_1", "clue_2", "clue_3"],
    )


@pytest.fixture
def event_trigger():
    """Basic event trigger."""
    return EventTrigger(
        trigger_type=TriggerType.ON_ENTER_LOCATION,
        target="office",
    )


@pytest.fixture
def event_action():
    """Basic event action."""
    return EventAction(
        action_type=ActionType.SHOW_DIALOGUE,
        target="detective",
        value="Welcome to the office!",
    )


@pytest.fixture
def scripted_event(event_trigger, event_action):
    """Basic scripted event."""
    event = ScriptedEvent(
        id="intro_event",
        name="Introduction",
    )
    event.add_trigger(event_trigger)
    event.add_action(event_action)
    return event


@pytest.fixture
def scenario_script(character_template, location_template, conflict_template, scripted_event):
    """Basic scenario script."""
    return ScenarioScript(
        id="test_scenario",
        name="Test Scenario",
        author="Test Author",
        conflict=conflict_template,
        characters=[character_template],
        locations=[location_template],
        events=[scripted_event],
        starting_location="office",
    )


@pytest.fixture
def validator():
    """Mod validator instance."""
    return ModValidator()


@pytest.fixture
def temp_mod_dir():
    """Temporary directory for mod files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_mod_file(temp_mod_dir):
    """Create a sample mod file."""
    mod_data = {
        "mod_info": {
            "id": "sample_mod",
            "name": "Sample Mod",
            "version": "1.0.0",
            "author": "Test",
        },
        "theme_pack": {
            "id": "sample_theme",
            "name": "Sample Theme",
        },
    }
    file_path = temp_mod_dir / "sample_mod.json"
    with open(file_path, "w") as f:
        json.dump(mod_data, f)
    return file_path
