"""
ShadowEngine Modding System.

Provides extensibility and content creation support including:
- Theme packs for genre customization
- Custom archetype definitions
- Scenario scripting system
- Mod registry and loading

Example usage:
    from shadowengine.modding import ModRegistry, ThemePack, load_theme_pack

    # Register a theme pack
    registry = ModRegistry()
    pack = load_theme_pack("mods/cyberpunk_noir.json")
    registry.register_theme_pack(pack)

    # Apply theme to game
    game.apply_theme_pack(registry.get_theme_pack("cyberpunk_noir"))
"""

from .registry import (
    ModRegistry,
    ModInfo,
    ModType,
    ContentConflict,
    ModLoadError,
    ModValidationError,
)

from .theme_pack import (
    ThemePack,
    ThemeConfig,
    VocabularyConfig,
    WeatherConfig,
    AtmosphereConfig,
    load_theme_pack,
    save_theme_pack,
    create_theme_pack,
)

from .archetype import (
    CustomArchetype,
    ArchetypeDefinition,
    MotivationPreset,
    BehaviorPattern,
    ArchetypeRegistry,
    create_archetype,
    register_archetype,
)

from .scenario import (
    ScenarioScript,
    ScriptedEvent,
    EventTrigger,
    TriggerType,
    EventAction,
    ActionType,
    ScenarioLoader,
    ScenarioValidator,
    ConflictTemplate,
    CharacterTemplate,
    LocationTemplate,
)

from .validator import (
    ModValidator,
    ValidationResult,
    ValidationError,
    ValidationWarning,
    validate_theme_pack,
    validate_archetype,
    validate_scenario,
)

__all__ = [
    # Registry
    "ModRegistry",
    "ModInfo",
    "ModType",
    "ContentConflict",
    "ModLoadError",
    "ModValidationError",
    # Theme Pack
    "ThemePack",
    "ThemeConfig",
    "VocabularyConfig",
    "WeatherConfig",
    "AtmosphereConfig",
    "load_theme_pack",
    "save_theme_pack",
    "create_theme_pack",
    # Archetypes
    "CustomArchetype",
    "ArchetypeDefinition",
    "MotivationPreset",
    "BehaviorPattern",
    "ArchetypeRegistry",
    "create_archetype",
    "register_archetype",
    # Scenarios
    "ScenarioScript",
    "ScriptedEvent",
    "EventTrigger",
    "TriggerType",
    "EventAction",
    "ActionType",
    "ScenarioLoader",
    "ScenarioValidator",
    "ConflictTemplate",
    "CharacterTemplate",
    "LocationTemplate",
    # Validation
    "ModValidator",
    "ValidationResult",
    "ValidationError",
    "ValidationWarning",
    "validate_theme_pack",
    "validate_archetype",
    "validate_scenario",
]
