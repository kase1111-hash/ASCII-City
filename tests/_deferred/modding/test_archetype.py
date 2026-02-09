"""
Tests for the custom archetype system.
"""

import pytest
import json

from src.shadowengine.modding.archetype import (
    MotivationPreset, BehaviorPattern, ArchetypeDefinition,
    CustomArchetype, ArchetypeRegistry,
    BehaviorTendency, ResponseStyle,
    create_archetype, register_archetype, get_archetype, list_archetypes,
    FEMME_FATALE, CORRUPT_COP, STREET_INFORMANT, GRIEVING_WIDOW,
)


class TestMotivationPreset:
    """Tests for MotivationPreset."""

    def test_create_default(self):
        """Default motivations are 50."""
        preset = MotivationPreset()
        assert preset.fear == 50
        assert preset.greed == 50
        assert preset.loyalty == 50

    def test_create_custom(self, motivation_preset):
        """Can create custom motivations."""
        assert motivation_preset.fear == 60
        assert motivation_preset.loyalty == 80

    def test_get_motivation(self, motivation_preset):
        """Can get motivation by name."""
        value = motivation_preset.get_motivation("fear")
        assert value == 60

    def test_set_motivation(self, motivation_preset):
        """Can set motivation value."""
        motivation_preset.set_motivation("fear", 80)
        assert motivation_preset.fear == 80

    def test_set_motivation_clamped(self, motivation_preset):
        """Motivation values are clamped."""
        motivation_preset.set_motivation("fear", 150)
        assert motivation_preset.fear == 100

        motivation_preset.set_motivation("fear", -10)
        assert motivation_preset.fear == 0

    def test_get_dominant_motivation(self, motivation_preset):
        """Can get dominant motivation."""
        dominant = motivation_preset.get_dominant_motivation()
        assert dominant == "loyalty"  # 80 is highest

    def test_get_weakness(self):
        """Can determine weakness."""
        preset = MotivationPreset(fear=80, guilt=30)
        weakness = preset.get_weakness()
        assert weakness == "fear"

    def test_serialization(self, motivation_preset):
        """MotivationPreset can be serialized."""
        data = motivation_preset.to_dict()
        restored = MotivationPreset.from_dict(data)

        assert restored.fear == motivation_preset.fear
        assert restored.loyalty == motivation_preset.loyalty


class TestBehaviorPattern:
    """Tests for BehaviorPattern."""

    def test_create_default(self):
        """Default behavior has values."""
        pattern = BehaviorPattern()
        assert pattern.tendency == BehaviorTendency.EVASIVE
        assert pattern.response_style == ResponseStyle.DIRECT

    def test_create_custom(self, behavior_pattern):
        """Can create custom behavior."""
        assert behavior_pattern.tendency == BehaviorTendency.EVASIVE
        assert behavior_pattern.response_style == ResponseStyle.CALCULATED
        assert behavior_pattern.trust_threshold == 60

    def test_should_lie(self, behavior_pattern):
        """Can determine if should lie."""
        import random
        rng = random.Random(42)

        # Will lie is true by default
        behavior_pattern.will_lie = True
        behavior_pattern.lie_probability = 1.0
        assert behavior_pattern.should_lie(0.3, rng) is True

        behavior_pattern.will_lie = False
        assert behavior_pattern.should_lie(0.3, rng) is False

    def test_should_deflect(self, behavior_pattern):
        """Can determine if should deflect."""
        import random
        rng = random.Random(42)

        behavior_pattern.deflect_probability = 1.0
        assert behavior_pattern.should_deflect(0.5, rng) is True

        behavior_pattern.deflect_probability = 0.0
        assert behavior_pattern.should_deflect(0.5, rng) is False

    def test_get_mood_modifier(self, behavior_pattern):
        """Can get mood based on pressure."""
        behavior_pattern.anger_threshold = 0.7
        behavior_pattern.fear_threshold = 0.5
        behavior_pattern.breakdown_threshold = 0.9

        assert behavior_pattern.get_mood_modifier(0.3) == "calm"
        assert behavior_pattern.get_mood_modifier(0.6) == "nervous"
        assert behavior_pattern.get_mood_modifier(0.8) == "angry"
        assert behavior_pattern.get_mood_modifier(0.95) == "broken"

    def test_serialization(self, behavior_pattern):
        """BehaviorPattern can be serialized."""
        data = behavior_pattern.to_dict()
        restored = BehaviorPattern.from_dict(data)

        assert restored.tendency == behavior_pattern.tendency
        assert restored.response_style == behavior_pattern.response_style
        assert restored.trust_threshold == behavior_pattern.trust_threshold


class TestArchetypeDefinition:
    """Tests for ArchetypeDefinition."""

    def test_create_archetype(self, archetype_definition):
        """Can create archetype definition."""
        assert archetype_definition.id == "test_archetype"
        assert archetype_definition.name == "Test Archetype"

    def test_default_roles(self, archetype_definition):
        """Default narrative roles are set."""
        assert archetype_definition.can_be_culprit is True
        assert archetype_definition.can_be_witness is True
        assert archetype_definition.can_be_victim is True

    def test_get_greeting(self, archetype_definition):
        """Can get greeting template."""
        import random
        rng = random.Random(42)
        greeting = archetype_definition.get_greeting(rng=rng)
        assert greeting in archetype_definition.greeting_templates

    def test_get_deflection(self, archetype_definition):
        """Can get deflection template."""
        deflection = archetype_definition.get_deflection()
        assert deflection in archetype_definition.deflection_templates

    def test_serialization(self, archetype_definition):
        """ArchetypeDefinition can be serialized."""
        data = archetype_definition.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = ArchetypeDefinition.from_dict(restored_data)

        assert restored.id == archetype_definition.id
        assert restored.name == archetype_definition.name
        assert restored.motivations.fear == archetype_definition.motivations.fear


class TestCustomArchetype:
    """Tests for CustomArchetype wrapper."""

    def test_create_wrapper(self, archetype_definition):
        """Can create CustomArchetype wrapper."""
        custom = CustomArchetype(archetype_definition)
        assert custom.id == archetype_definition.id
        assert custom.name == archetype_definition.name

    def test_enum_compatibility(self, archetype_definition):
        """CustomArchetype is compatible with enum-like usage."""
        custom = CustomArchetype(archetype_definition)
        assert custom.value == archetype_definition.id

    def test_equality(self, archetype_definition):
        """CustomArchetype equality works."""
        custom1 = CustomArchetype(archetype_definition)
        custom2 = CustomArchetype(archetype_definition)

        assert custom1 == custom2

    def test_hash(self, archetype_definition):
        """CustomArchetype can be hashed."""
        custom = CustomArchetype(archetype_definition)
        hash_value = hash(custom)
        assert isinstance(hash_value, int)

    def test_get_motivations(self, archetype_definition):
        """Can get motivations from wrapper."""
        custom = CustomArchetype(archetype_definition)
        motivations = custom.get_motivations()
        assert motivations.fear == archetype_definition.motivations.fear


class TestArchetypeRegistry:
    """Tests for ArchetypeRegistry."""

    def test_create_registry(self, archetype_registry):
        """Can create archetype registry."""
        assert len(archetype_registry.list_all()) == 0

    def test_register_archetype(self, archetype_registry, archetype_definition):
        """Can register an archetype."""
        result = archetype_registry.register(archetype_definition)
        assert result is True
        assert len(archetype_registry.list_all()) == 1

    def test_duplicate_registration(self, archetype_registry, archetype_definition):
        """Cannot register duplicate ID."""
        archetype_registry.register(archetype_definition)
        result = archetype_registry.register(archetype_definition)
        assert result is False

    def test_get_archetype(self, archetype_registry, archetype_definition):
        """Can get archetype by ID."""
        archetype_registry.register(archetype_definition)
        retrieved = archetype_registry.get(archetype_definition.id)

        assert retrieved is not None
        assert retrieved.id == archetype_definition.id

    def test_get_custom(self, archetype_registry, archetype_definition):
        """Can get CustomArchetype wrapper."""
        archetype_registry.register(archetype_definition)
        custom = archetype_registry.get_custom(archetype_definition.id)

        assert isinstance(custom, CustomArchetype)
        assert custom.id == archetype_definition.id

    def test_unregister(self, archetype_registry, archetype_definition):
        """Can unregister an archetype."""
        archetype_registry.register(archetype_definition)
        result = archetype_registry.unregister(archetype_definition.id)

        assert result is True
        assert len(archetype_registry.list_all()) == 0

    def test_list_by_theme(self, archetype_registry, archetype_definition):
        """Can list archetypes by theme."""
        archetype_definition.compatible_themes = ["noir", "cyberpunk"]
        archetype_registry.register(archetype_definition)

        noir_archetypes = archetype_registry.list_for_theme("noir")
        assert archetype_definition.id in noir_archetypes

    def test_list_by_role(self, archetype_registry, archetype_definition):
        """Can list archetypes by narrative role."""
        archetype_registry.register(archetype_definition)

        culprits = archetype_registry.list_culprits()
        assert archetype_definition.id in culprits

        archetype_definition.can_be_culprit = False
        archetype_definition.id = "victim_only"
        archetype_registry.register(archetype_definition)

        victims = archetype_registry.list_victims()
        assert "victim_only" in victims

    def test_serialization(self, archetype_registry, archetype_definition):
        """ArchetypeRegistry can be serialized."""
        archetype_registry.register(archetype_definition)
        data = archetype_registry.to_dict()

        restored = ArchetypeRegistry.from_dict(data)
        assert archetype_definition.id in restored.list_all()


class TestGlobalFunctions:
    """Tests for global archetype functions."""

    def test_create_archetype_function(self):
        """Can use create_archetype helper."""
        archetype = create_archetype(
            id="new_archetype",
            name="New Archetype",
            description="A new archetype",
        )
        assert archetype.id == "new_archetype"
        assert archetype.name == "New Archetype"


class TestPredefinedArchetypes:
    """Tests for predefined archetypes."""

    def test_femme_fatale_exists(self):
        """Femme fatale archetype exists."""
        assert FEMME_FATALE is not None
        assert FEMME_FATALE.id == "femme_fatale"
        assert FEMME_FATALE.motivations.ambition > 50

    def test_corrupt_cop_exists(self):
        """Corrupt cop archetype exists."""
        assert CORRUPT_COP is not None
        assert CORRUPT_COP.id == "corrupt_cop"
        assert CORRUPT_COP.behavior.tendency == BehaviorTendency.AGGRESSIVE

    def test_street_informant_exists(self):
        """Street informant archetype exists."""
        assert STREET_INFORMANT is not None
        assert STREET_INFORMANT.id == "street_informant"
        assert STREET_INFORMANT.behavior.cracks_easily is True

    def test_grieving_widow_exists(self):
        """Grieving widow archetype exists."""
        assert GRIEVING_WIDOW is not None
        assert GRIEVING_WIDOW.id == "grieving_widow"
        assert GRIEVING_WIDOW.behavior.response_style == ResponseStyle.EMOTIONAL

    def test_predefined_are_registered(self):
        """Predefined archetypes are in global registry."""
        archetypes = list_archetypes()
        assert "femme_fatale" in archetypes
        assert "corrupt_cop" in archetypes
        assert "street_informant" in archetypes
        assert "grieving_widow" in archetypes

    def test_get_predefined(self):
        """Can get predefined archetype from global registry."""
        femme = get_archetype("femme_fatale")
        assert femme is not None
        assert femme.name == "Femme Fatale"
