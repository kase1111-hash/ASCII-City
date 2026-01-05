"""
End-to-end tests for the Modding & Extensibility system.

These tests verify complete workflows for mod creation, loading,
validation, and application to game systems.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.shadowengine.modding.registry import (
    ModRegistry, ModInfo, ModType, ContentConflict,
)
from src.shadowengine.modding.theme_pack import (
    ThemePack, VocabularyConfig, WeatherConfig, AtmosphereConfig,
    ThemeConfig, load_theme_pack, save_theme_pack, create_theme_pack,
    NOIR_THEME, CYBERPUNK_THEME, GOTHIC_HORROR_THEME,
    get_builtin_theme, list_builtin_themes,
)
from src.shadowengine.modding.archetype import (
    ArchetypeDefinition, MotivationPreset, BehaviorPattern,
    ArchetypeRegistry, CustomArchetype, BehaviorTendency, ResponseStyle,
    create_archetype, register_archetype, get_archetype, list_archetypes,
    FEMME_FATALE, CORRUPT_COP, STREET_INFORMANT, GRIEVING_WIDOW,
)
from src.shadowengine.modding.scenario import (
    ScenarioScript, ScriptedEvent, EventTrigger, EventAction,
    TriggerType, ActionType, CharacterTemplate, LocationTemplate,
    ConflictTemplate, ScenarioValidator, ScenarioLoader,
)
from src.shadowengine.modding.validator import (
    ModValidator, ValidationResult, validate_theme_pack,
    validate_archetype, validate_scenario, validate_json_file,
)


class TestModCreationPipeline:
    """E2E tests for mod creation workflow."""

    def test_create_complete_theme_pack_mod(self):
        """Create a complete theme pack mod from scratch."""
        # Step 1: Create vocabulary configuration
        vocab = VocabularyConfig(
            examine_verbs=["inspect", "scrutinize", "assess"],
            talk_verbs=["interrogate", "question", "probe"],
            take_verbs=["acquire", "secure", "confiscate"],
            use_verbs=["employ", "utilize", "deploy"],
            go_verbs=["proceed", "advance", "relocate"],
            attack_verbs=["neutralize", "eliminate", "engage"],
            custom_terms={
                "money": "credits",
                "gun": "piece",
                "police": "enforcement",
            }
        )

        # Step 2: Create weather configuration
        weather = WeatherConfig(
            weather_weights={
                "clear": 0.1,
                "fog": 0.3,
                "rain": 0.4,
                "storm": 0.2,
            },
            weather_descriptions={
                "fog": "Thick smog blankets the streets.",
                "rain": "Acid rain drizzles from the polluted sky.",
            }
        )

        # Step 3: Create atmosphere configuration
        atmosphere = AtmosphereConfig(
            primary_color="neon_blue",
            secondary_color="magenta",
            ambient_sounds=["traffic_hum", "distant_sirens", "electronic_buzz"],
            particle_effects=["rain_drops", "neon_flicker", "holographic_ads"],
            effect_intensity=0.8,
            tempo_base=120,
        )

        # Step 4: Create theme configuration
        theme = ThemeConfig(
            location_types=["megacorp_tower", "data_haven", "street_market", "club"],
            conflict_types=["data_theft", "corporate_espionage", "assassination"],
            time_periods={
                "night_shift": (22, 6),
                "corp_hours": (8, 18),
            }
        )

        # Step 5: Assemble theme pack
        pack = ThemePack(
            id="neo_noir_2084",
            name="Neo Noir 2084",
            version="1.0.0",
            author="Test Creator",
            description="A cyberpunk noir experience set in 2084",
            vocabulary=vocab,
            weather=weather,
            atmosphere=atmosphere,
            theme=theme,
        )

        # Step 6: Validate the theme pack
        result = validate_theme_pack(pack)
        assert result.valid is True, f"Validation failed: {result.errors}"

        # Step 7: Save to file and reload
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "neo_noir_2084.json"
            save_theme_pack(pack, str(file_path))

            # Verify file exists and is valid JSON
            assert file_path.exists()
            with open(file_path) as f:
                data = json.load(f)
            assert data["id"] == "neo_noir_2084"

            # Step 8: Load and verify
            loaded = load_theme_pack(str(file_path))
            assert loaded is not None
            assert loaded.name == "Neo Noir 2084"
            assert loaded.vocabulary.examine_verbs == vocab.examine_verbs
            assert loaded.weather.weather_weights["fog"] == 0.3

    def test_create_custom_archetype_mod(self):
        """Create custom archetypes and register them."""
        # Step 1: Create motivation preset
        motivations = MotivationPreset(
            fear=30,
            greed=80,
            loyalty=20,
            pride=60,
            guilt=10,
            ambition=90,
            revenge=40,
            love=15,
            duty=25,
            survival=70,
        )

        # Step 2: Create behavior pattern
        behavior = BehaviorPattern(
            tendency=BehaviorTendency.AGGRESSIVE,
            response_style=ResponseStyle.CALCULATED,
            will_lie=True,
            lie_probability=0.7,
            deflect_probability=0.5,
            cracks_easily=False,
            trust_threshold=80,
            pressure_resistance=0.8,
            anger_threshold=0.4,
            fear_threshold=0.6,
            breakdown_threshold=0.95,
        )

        # Step 3: Create archetype definition
        archetype = ArchetypeDefinition(
            id="corporate_fixer",
            name="Corporate Fixer",
            description="A cold, efficient problem solver for megacorporations",
            motivations=motivations,
            behavior=behavior,
            greeting_templates=[
                "I don't have time for small talk.",
                "State your business.",
                "You have exactly one minute.",
            ],
            deflection_templates=[
                "That's above your clearance level.",
                "My employer wouldn't appreciate that question.",
                "Let's stay focused on the matter at hand.",
            ],
            denial_templates=[
                "I see you've done your research.",
                "Who sent you? Really?",
                "Interesting line of inquiry.",
            ],
            confession_templates=[
                "Fine. You want the truth? Here it is...",
                "They'll kill me for this, but...",
            ],
            compatible_themes=["cyberpunk", "noir", "corporate"],
            can_be_culprit=True,
            can_be_witness=True,
            can_be_victim=False,
            can_be_red_herring=True,
        )

        # Step 4: Validate
        result = validate_archetype(archetype)
        assert result.valid is True, f"Validation failed: {result.errors}"

        # Step 5: Register to a registry
        registry = ArchetypeRegistry()
        success = registry.register(archetype)
        assert success is True

        # Step 6: Retrieve and verify
        retrieved = registry.get(archetype.id)
        assert retrieved is not None
        assert retrieved.name == "Corporate Fixer"
        assert retrieved.motivations.ambition == 90
        assert retrieved.behavior.tendency == BehaviorTendency.AGGRESSIVE

        # Step 7: Get as CustomArchetype for game use
        custom = registry.get_custom(archetype.id)
        assert isinstance(custom, CustomArchetype)
        assert custom.value == "corporate_fixer"

        # Step 8: Serialize and restore
        data = archetype.to_dict()
        restored = ArchetypeDefinition.from_dict(data)
        assert restored.id == archetype.id
        assert restored.motivations.ambition == 90

    def test_create_scenario_mod(self):
        """Create a complete scenario mod."""
        # Step 1: Define characters
        detective = CharacterTemplate(
            id="detective_chen",
            name="Detective Chen",
            archetype="corrupt_cop",
            description="A veteran detective with hidden debts",
            starting_location="precinct",
            starting_mood="stressed",
            known_facts=["victim_identity", "time_of_death"],
            secrets=["gambling_debt", "evidence_tampering"],
            dialogue_pool=[
                "Another day, another body.",
                "This case stinks.",
            ],
            topics=["victim", "suspects", "evidence"],
            is_culprit=False,
            is_witness=True,
        )

        suspect = CharacterTemplate(
            id="victor_crane",
            name="Victor Crane",
            archetype="femme_fatale",
            description="A wealthy entrepreneur with secrets",
            starting_location="penthouse",
            starting_mood="nervous",
            known_facts=["victim_business_partner"],
            secrets=["affair_with_victim", "financial_fraud"],
            dialogue_pool=[
                "I have nothing to hide.",
                "My lawyers will hear about this.",
            ],
            topics=["business", "victim", "alibi"],
            is_culprit=True,
            is_witness=False,
        )

        # Step 2: Define locations
        precinct = LocationTemplate(
            id="precinct",
            name="12th Precinct",
            description="A grimy police station",
            is_outdoor=False,
            base_light_level=0.7,
            ambient_description="Fluorescent lights buzz overhead.",
            exits={"south": "street", "east": "morgue"},
            items=["case_files", "coffee_cup"],
            evidence=["victim_photo"],
        )

        penthouse = LocationTemplate(
            id="penthouse",
            name="Crane Penthouse",
            description="A luxurious high-rise apartment",
            is_outdoor=False,
            base_light_level=0.5,
            ambient_description="Floor-to-ceiling windows show the city lights.",
            exits={"down": "lobby"},
            items=["expensive_art", "whiskey_decanter"],
            evidence=["bloody_gloves"],
            initially_locked=True,
            requires_key="penthouse_key",
        )

        street = LocationTemplate(
            id="street",
            name="Rain-Slicked Street",
            description="A dark alley outside the precinct",
            is_outdoor=True,
            base_light_level=0.2,
            exits={"north": "precinct", "west": "bar"},
        )

        # Step 3: Define conflict
        conflict = ConflictTemplate(
            id="crane_murder",
            name="The Crane Murder",
            conflict_type="murder",
            description="A wealthy businessman found dead in his office",
            solution_description="Victor Crane killed his partner to hide fraud.",
            motive="Financial fraud about to be exposed",
            method="Poison in evening drink",
            opportunity="Alone in office after hours",
            evidence_chain=["victim_photo", "financial_records", "bloody_gloves", "poison_vial"],
            revelations=[
                {"id": "affair_revealed", "fact": "Victor had an affair with victim's wife"},
                {"id": "fraud_revealed", "fact": "Victor was embezzling company funds"},
            ],
            red_herrings=[
                {"id": "jealous_wife", "description": "The victim's wife had motive"},
            ],
            has_twist=True,
            twist_type="hidden_identity",
            twist_description="The 'victim' faked his death to escape with money",
            twist_trigger_progress=0.7,
        )

        # Step 4: Define events
        intro_event = ScriptedEvent(
            id="game_start",
            name="Case Introduction",
            triggers=[
                EventTrigger(
                    trigger_type=TriggerType.ON_GAME_START,
                    once=True,
                )
            ],
            actions=[
                EventAction(
                    action_type=ActionType.SHOW_NARRATION,
                    value="The rain hasn't stopped for three days...",
                ),
                EventAction(
                    action_type=ActionType.SET_WEATHER,
                    value="rain",
                ),
                EventAction(
                    action_type=ActionType.SET_TENSION,
                    value=0.3,
                ),
            ],
        )

        discovery_event = ScriptedEvent(
            id="find_gloves",
            name="Bloody Gloves Discovery",
            triggers=[
                EventTrigger(
                    trigger_type=TriggerType.ON_DISCOVER_EVIDENCE,
                    target="bloody_gloves",
                    once=True,
                )
            ],
            actions=[
                EventAction(
                    action_type=ActionType.SHOW_DIALOGUE,
                    target="detective_chen",
                    value="Well, well... someone got careless.",
                ),
                EventAction(
                    action_type=ActionType.SET_TENSION,
                    value=0.6,
                ),
                EventAction(
                    action_type=ActionType.TRIGGER_REVELATION,
                    target="affair_revealed",
                ),
            ],
        )

        confrontation_event = ScriptedEvent(
            id="final_confrontation",
            name="Final Confrontation",
            triggers=[
                EventTrigger(
                    trigger_type=TriggerType.ON_PROGRESS,
                    value=0.9,
                    once=True,
                )
            ],
            actions=[
                EventAction(
                    action_type=ActionType.SET_TENSION,
                    value=0.95,
                ),
                EventAction(
                    action_type=ActionType.PLAY_MUSIC,
                    value="confrontation_theme",
                ),
                EventAction(
                    action_type=ActionType.CRACK_CHARACTER,
                    target="victor_crane",
                ),
            ],
        )

        # Step 5: Assemble scenario
        scenario = ScenarioScript(
            id="crane_murder_mystery",
            name="The Crane Murder Mystery",
            version="1.0.0",
            author="Test Author",
            description="A noir murder mystery in the corporate world",
            theme_pack="noir",
            conflict=conflict,
            characters=[detective, suspect],
            locations=[precinct, penthouse, street],
            events=[intro_event, discovery_event, confrontation_event],
            starting_location="precinct",
            starting_time=22,
            starting_weather="rain",
            starting_tension=0.3,
            initial_flags={"case_open": True, "suspect_known": False},
            initial_counters={"clues_found": 0},
            tags=["noir", "murder", "corporate"],
            difficulty="normal",
            estimated_playtime=45,
        )

        # Step 6: Validate scenario
        validator = ScenarioValidator()
        is_valid = validator.validate(scenario)
        assert is_valid is True, f"Errors: {validator.errors}"

        # Also use ModValidator
        result = validate_scenario(scenario)
        assert result.valid is True, f"Validation failed: {result.errors}"

        # Step 7: Save and reload
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ScenarioLoader(tmpdir)
            loader.save(scenario)

            # Reload
            loaded = loader.load(scenario.id)
            assert loaded is not None
            assert loaded.name == "The Crane Murder Mystery"
            assert len(loaded.characters) == 2
            assert len(loaded.locations) == 3
            assert len(loaded.events) == 3
            assert loaded.conflict.has_twist is True

        # Step 8: Test scenario queries
        assert scenario.get_character("detective_chen") is not None
        assert scenario.get_location("penthouse") is not None
        assert scenario.get_event("find_gloves") is not None

        # Step 9: Test active events
        game_state = {}
        active = scenario.get_active_events(game_state)
        # game_start event should be active at start
        assert any(e.id == "game_start" for e in active)


class TestModRegistryPipeline:
    """E2E tests for mod registry workflow."""

    def test_register_and_manage_multiple_mods(self):
        """Test complete mod registration and management workflow."""
        registry = ModRegistry()

        # Step 1: Create and register multiple mods
        mods = [
            ModInfo(
                id="noir_expansion",
                name="Noir Expansion Pack",
                version="1.0.0",
                author="Creator A",
                mod_type=ModType.THEME_PACK,
            ),
            ModInfo(
                id="cyberpunk_chars",
                name="Cyberpunk Characters",
                version="2.0.0",
                author="Creator B",
                mod_type=ModType.ARCHETYPE,
            ),
            ModInfo(
                id="mystery_scenarios",
                name="Mystery Scenarios",
                version="1.5.0",
                author="Creator C",
                mod_type=ModType.SCENARIO,
            ),
        ]

        for mod in mods:
            success = registry.register_mod(mod)
            assert success is True

        # Step 2: Verify all mods registered
        all_mods = registry.list_mods()
        assert len(all_mods) == 3

        # Step 3: Get specific mod
        noir = registry.get_mod("noir_expansion")
        assert noir is not None
        assert noir.name == "Noir Expansion Pack"

        # Step 4: Enable/disable mods
        registry.disable_mod("cyberpunk_chars")
        enabled = registry.enabled_mods
        assert len(enabled) == 2
        assert "cyberpunk_chars" not in [m.id for m in enabled]

        registry.enable_mod("cyberpunk_chars")
        enabled = registry.enabled_mods
        assert len(enabled) == 3

        # Step 5: Register theme pack content
        theme = ThemePack(id="noir_dark", name="Dark Noir")
        registry.register_theme_pack(theme, "noir_expansion")
        retrieved_theme = registry.get_theme_pack("noir_dark")
        assert retrieved_theme is not None

        # Step 6: Register archetype content
        archetype = ArchetypeDefinition(
            id="cyber_hacker",
            name="Cyber Hacker",
        )
        registry.register_archetype(archetype, "cyberpunk_chars")

        # Step 7: Register scenario content
        scenario = ScenarioScript(
            id="locked_room",
            name="Locked Room Mystery",
        )
        registry.register_scenario(scenario, "mystery_scenarios")

        # Step 8: Get statistics
        stats = registry.get_stats()
        assert stats["total_mods"] == 3
        assert stats["enabled_mods"] == 3

        # Step 9: Serialize and restore registry
        data = registry.to_dict()
        restored = ModRegistry.from_dict(data)
        assert len(restored.list_mods()) == 3

        # Step 10: Unregister mod
        success = registry.unregister_mod("mystery_scenarios")
        assert success is True
        assert len(registry.list_mods()) == 2

    def test_mod_dependencies_and_conflicts(self):
        """Test mod dependency and conflict handling."""
        registry = ModRegistry()

        # Register base mod
        base_mod = ModInfo(
            id="base_noir",
            name="Base Noir",
            version="1.0.0",
        )
        registry.register_mod(base_mod)

        # Register dependent mod (dependencies are checked during registration)
        dependent_mod = ModInfo(
            id="noir_expansion",
            name="Noir Expansion",
            version="1.0.0",
            dependencies=["base_noir"],
        )
        # Should succeed since base_noir is registered
        registry.register_mod(dependent_mod)
        assert registry.get_mod("noir_expansion") is not None

        # Verify both mods are registered
        assert len(registry.list_mods()) == 2

        # Mod with conflicts_with field
        mod_a = ModInfo(
            id="theme_a",
            name="Theme A",
            version="1.0.0",
            conflicts_with=["theme_b"],
        )
        registry.register_mod(mod_a)

        # Verify mod was registered with conflict info
        retrieved = registry.get_mod("theme_a")
        assert retrieved is not None
        assert "theme_b" in retrieved.conflicts_with


class TestModValidationPipeline:
    """E2E tests for mod validation workflow."""

    def test_validate_complete_mod_package(self):
        """Validate a complete mod package with all content types."""
        validator = ModValidator()

        # Create complete mod package
        theme = ThemePack(
            id="complete_theme",
            name="Complete Theme",
            vocabulary=VocabularyConfig(),
            weather=WeatherConfig(),
            atmosphere=AtmosphereConfig(),
            theme=ThemeConfig(),
        )

        archetype = ArchetypeDefinition(
            id="complete_archetype",
            name="Complete Archetype",
            motivations=MotivationPreset(),
            behavior=BehaviorPattern(),
            greeting_templates=["Hello."],
        )

        scenario = ScenarioScript(
            id="complete_scenario",
            name="Complete Scenario",
            characters=[
                CharacterTemplate(id="char1", name="Character", archetype="test")
            ],
            locations=[
                LocationTemplate(id="loc1", name="Location")
            ],
            starting_location="loc1",
        )

        # Validate each component
        theme_result = validator.validate_theme_pack(theme)
        assert theme_result.valid is True

        archetype_result = validator.validate_archetype(archetype)
        assert archetype_result.valid is True

        scenario_result = validator.validate_scenario(scenario)
        assert scenario_result.valid is True

        # Check for warnings
        all_warnings = (
            theme_result.warnings +
            archetype_result.warnings +
            scenario_result.warnings
        )
        # Some warnings expected for minimal content
        assert len(all_warnings) >= 0

    def test_validate_json_mod_file(self):
        """Validate mod files in JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid mod file
            valid_mod = {
                "mod_info": {
                    "id": "test_mod",
                    "name": "Test Mod",
                    "version": "1.0.0",
                },
                "theme_pack": {
                    "id": "test_theme",
                    "name": "Test Theme",
                }
            }

            valid_path = Path(tmpdir) / "valid_mod.json"
            with open(valid_path, 'w') as f:
                json.dump(valid_mod, f)

            result = validate_json_file(str(valid_path))
            assert result.valid is True

            # Create invalid mod file (missing mod_info)
            invalid_mod = {
                "theme_pack": {
                    "id": "test_theme",
                    "name": "Test Theme",
                }
            }

            invalid_path = Path(tmpdir) / "invalid_mod.json"
            with open(invalid_path, 'w') as f:
                json.dump(invalid_mod, f)

            result = validate_json_file(str(invalid_path))
            assert result.valid is False

            # Create malformed JSON
            malformed_path = Path(tmpdir) / "malformed.json"
            with open(malformed_path, 'w') as f:
                f.write("{invalid json content")

            result = validate_json_file(str(malformed_path))
            assert result.valid is False
            assert result.has_critical_errors is True


class TestBuiltinContentPipeline:
    """E2E tests for built-in content access."""

    def test_access_all_builtin_themes(self):
        """Access and verify all built-in themes."""
        themes = list_builtin_themes()
        assert len(themes) >= 3

        for theme_id in themes:
            theme = get_builtin_theme(theme_id)
            assert theme is not None
            assert theme.id == theme_id
            assert theme.name != ""

            # Verify each theme is valid
            result = validate_theme_pack(theme)
            assert result.valid is True, f"Theme {theme_id} invalid: {result.errors}"

    def test_access_all_builtin_archetypes(self):
        """Access and verify all built-in archetypes."""
        archetypes = list_archetypes()
        assert len(archetypes) >= 4

        for arch_id in archetypes:
            arch = get_archetype(arch_id)
            assert arch is not None
            assert arch.id == arch_id
            assert arch.name != ""

            # Verify each archetype is valid
            result = validate_archetype(arch)
            assert result.valid is True, f"Archetype {arch_id} invalid: {result.errors}"

    def test_use_builtin_theme_pack(self):
        """Use a built-in theme pack for game configuration."""
        # Get noir theme
        noir = NOIR_THEME
        assert noir is not None

        # Use vocabulary
        verb = noir.vocabulary.get_verb("examine")
        assert verb is not None

        # Use weather
        prob = noir.weather.get_weather_probability("rain")
        assert prob > 0

        # Use atmosphere
        color = noir.atmosphere.get_tension_color(0.8)
        assert color is not None

    def test_use_builtin_archetypes(self):
        """Use built-in archetypes for character creation."""
        # Use femme fatale
        ff = FEMME_FATALE
        assert ff.motivations.ambition > 50

        # Use corrupt cop
        cc = CORRUPT_COP
        assert cc.behavior.tendency == BehaviorTendency.AGGRESSIVE

        # Use street informant
        si = STREET_INFORMANT
        assert si.behavior.cracks_easily is True

        # Use grieving widow
        gw = GRIEVING_WIDOW
        assert gw.behavior.response_style == ResponseStyle.EMOTIONAL


class TestScenarioExecutionPipeline:
    """E2E tests for scenario execution simulation."""

    def test_scenario_event_execution(self):
        """Simulate scenario event execution."""
        # Create simple scenario
        trigger = EventTrigger(
            trigger_type=TriggerType.ON_ENTER_LOCATION,
            target="office",
        )

        action = EventAction(
            action_type=ActionType.SHOW_DIALOGUE,
            target="npc",
            value="Welcome!",
        )

        event = ScriptedEvent(
            id="welcome_event",
            name="Welcome Event",
            triggers=[trigger],
            actions=[action],
            max_executions=1,
        )

        # Simulate game state
        game_state = {}

        # Event should be executable
        assert event.can_execute(game_state) is True

        # Execute event
        result = event.execute(None)  # Stub game object
        assert result is True
        assert event.executed_count == 1

        # Event should not be executable again (max_executions=1)
        # The trigger is marked as triggered
        assert event.can_execute(game_state) is False

        # Reset and verify
        event.reset()
        assert event.executed_count == 0
        assert event.can_execute(game_state) is True

    def test_scenario_progress_tracking(self):
        """Track scenario progress through events."""
        # Create scenario with multiple events
        events = []

        for i in range(5):
            trigger = EventTrigger(
                trigger_type=TriggerType.ON_PROGRESS,
                value=i * 0.2,
                once=True,
            )
            action = EventAction(
                action_type=ActionType.SET_FLAG,
                target=f"milestone_{i}",
                value=True,
            )
            event = ScriptedEvent(
                id=f"milestone_{i}",
                name=f"Milestone {i}",
                triggers=[trigger],
                actions=[action],
            )
            events.append(event)

        scenario = ScenarioScript(
            id="progress_test",
            name="Progress Test",
            events=events,
        )

        # Simulate progress
        for i, progress in enumerate([0.0, 0.2, 0.4, 0.6, 0.8]):
            game_state = {"progress": progress}
            active = scenario.get_active_events(game_state)
            # Each milestone should be active at its threshold
            assert len(active) >= 1


class TestCompleteModWorkflow:
    """E2E tests for complete mod workflows."""

    def test_full_mod_lifecycle(self):
        """Test complete mod lifecycle from creation to removal."""
        # Step 1: Create mod registry
        registry = ModRegistry()

        # Step 2: Create mod info
        mod_info = ModInfo(
            id="full_lifecycle_mod",
            name="Full Lifecycle Mod",
            version="1.0.0",
            author="Test Author",
            mod_type=ModType.THEME_PACK,
        )

        # Step 3: Create content
        theme = ThemePack(
            id="lifecycle_theme",
            name="Lifecycle Theme",
        )

        archetype = ArchetypeDefinition(
            id="lifecycle_archetype",
            name="Lifecycle Archetype",
            greeting_templates=["Hello."],
        )

        scenario = ScenarioScript(
            id="lifecycle_scenario",
            name="Lifecycle Scenario",
        )

        # Step 4: Validate all content
        validator = ModValidator()
        assert validator.validate_theme_pack(theme).valid
        assert validator.validate_archetype(archetype).valid
        assert validator.validate_scenario(scenario).valid

        # Step 5: Register mod
        registry.register_mod(mod_info)
        registry.register_theme_pack(theme, mod_info.id)
        registry.register_archetype(archetype, mod_info.id)
        registry.register_scenario(scenario, mod_info.id)

        # Step 6: Verify registration
        assert registry.get_mod(mod_info.id) is not None
        assert registry.get_theme_pack(theme.id) is not None

        # Step 7: Save registry state
        saved_state = registry.to_dict()
        assert saved_state is not None

        # Step 8: Disable mod
        registry.disable_mod(mod_info.id)
        assert mod_info.id not in [m.id for m in registry.enabled_mods]

        # Step 9: Re-enable mod
        registry.enable_mod(mod_info.id)
        assert mod_info.id in [m.id for m in registry.enabled_mods]

        # Step 10: Unregister mod
        registry.unregister_mod(mod_info.id)
        assert registry.get_mod(mod_info.id) is None


# Run all E2E tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
