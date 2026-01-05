"""
Tests for the mod registry system.
"""

import pytest
import json

from src.shadowengine.modding.registry import (
    ModRegistry, ModInfo, ModType, ContentConflict,
    ModLoadError, ModValidationError,
)


class TestModInfo:
    """Tests for ModInfo."""

    def test_create_mod_info(self, mod_info):
        """Can create mod info."""
        assert mod_info.id == "test_mod"
        assert mod_info.name == "Test Mod"
        assert mod_info.version == "1.0.0"

    def test_default_values(self):
        """Default values are set correctly."""
        info = ModInfo(id="mod", name="Mod", version="1.0")
        assert info.enabled is True
        assert info.load_order == 0
        assert info.dependencies == []
        assert info.conflicts_with == []

    def test_serialization(self, mod_info):
        """ModInfo can be serialized and deserialized."""
        data = mod_info.to_dict()
        restored = ModInfo.from_dict(data)

        assert restored.id == mod_info.id
        assert restored.name == mod_info.name
        assert restored.version == mod_info.version
        assert restored.author == mod_info.author

    def test_mod_type_serialization(self):
        """ModType is serialized correctly."""
        info = ModInfo(
            id="mod", name="Mod", version="1.0",
            mod_type=ModType.SCENARIO
        )
        data = info.to_dict()
        assert data["mod_type"] == "SCENARIO"

        restored = ModInfo.from_dict(data)
        assert restored.mod_type == ModType.SCENARIO


class TestModRegistry:
    """Tests for ModRegistry."""

    def test_create_registry(self, mod_registry):
        """Can create a mod registry."""
        assert mod_registry.mod_count == 0
        assert not mod_registry.has_conflicts

    def test_register_mod(self, mod_registry, mod_info):
        """Can register a mod."""
        result = mod_registry.register_mod(mod_info)
        assert result is True
        assert mod_registry.mod_count == 1

    def test_duplicate_registration_fails(self, mod_registry, mod_info):
        """Cannot register the same mod twice."""
        mod_registry.register_mod(mod_info)

        with pytest.raises(ModValidationError):
            mod_registry.register_mod(mod_info)

    def test_unregister_mod(self, mod_registry, mod_info):
        """Can unregister a mod."""
        mod_registry.register_mod(mod_info)
        assert mod_registry.mod_count == 1

        result = mod_registry.unregister_mod(mod_info.id)
        assert result is True
        assert mod_registry.mod_count == 0

    def test_get_mod(self, mod_registry, mod_info):
        """Can get a mod by ID."""
        mod_registry.register_mod(mod_info)
        retrieved = mod_registry.get_mod(mod_info.id)

        assert retrieved is not None
        assert retrieved.id == mod_info.id

    def test_get_nonexistent_mod(self, mod_registry):
        """Getting nonexistent mod returns None."""
        result = mod_registry.get_mod("nonexistent")
        assert result is None

    def test_list_mods(self, mod_registry):
        """Can list all mods."""
        for i in range(3):
            info = ModInfo(id=f"mod_{i}", name=f"Mod {i}", version="1.0")
            mod_registry.register_mod(info)

        mods = mod_registry.list_mods()
        assert len(mods) == 3

    def test_enable_disable_mod(self, mod_registry, mod_info):
        """Can enable and disable mods."""
        mod_registry.register_mod(mod_info)

        mod_registry.disable_mod(mod_info.id)
        assert not mod_registry.get_mod(mod_info.id).enabled

        mod_registry.enable_mod(mod_info.id)
        assert mod_registry.get_mod(mod_info.id).enabled

    def test_enabled_mods_filter(self, mod_registry):
        """Can filter enabled mods."""
        for i in range(3):
            info = ModInfo(id=f"mod_{i}", name=f"Mod {i}", version="1.0")
            mod_registry.register_mod(info)

        mod_registry.disable_mod("mod_1")

        enabled = mod_registry.enabled_mods
        assert len(enabled) == 2


class TestContentRegistration:
    """Tests for content registration."""

    def test_register_theme_pack(self, mod_registry, theme_pack):
        """Can register a theme pack."""
        result = mod_registry.register_theme_pack(theme_pack)
        assert result is True
        assert len(mod_registry.list_theme_packs()) == 1

    def test_get_theme_pack(self, mod_registry, theme_pack):
        """Can retrieve a registered theme pack."""
        mod_registry.register_theme_pack(theme_pack)
        retrieved = mod_registry.get_theme_pack(theme_pack.id)

        assert retrieved is not None
        assert retrieved.id == theme_pack.id

    def test_register_archetype(self, mod_registry, archetype_definition):
        """Can register a custom archetype."""
        result = mod_registry.register_archetype(archetype_definition)
        assert result is True
        assert len(mod_registry.list_archetypes()) == 1

    def test_register_scenario(self, mod_registry, scenario_script):
        """Can register a scenario."""
        result = mod_registry.register_scenario(scenario_script)
        assert result is True
        assert len(mod_registry.list_scenarios()) == 1

    def test_content_conflict_detection(self, mod_registry, theme_pack):
        """Detects content conflicts."""
        mod_registry.register_theme_pack(theme_pack, mod_id="mod1")

        # Register same ID again
        theme_pack2 = theme_pack  # Same ID
        mod_registry.register_theme_pack(theme_pack2, mod_id="mod2")

        assert mod_registry.has_conflicts
        assert len(mod_registry.conflicts) == 1


class TestDependencies:
    """Tests for mod dependencies."""

    def test_dependency_check(self, mod_registry):
        """Cannot register mod with missing dependency."""
        info = ModInfo(
            id="dependent_mod",
            name="Dependent Mod",
            version="1.0",
            dependencies=["missing_mod"]
        )

        with pytest.raises(ModValidationError):
            mod_registry.register_mod(info)

    def test_satisfied_dependency(self, mod_registry):
        """Can register mod when dependency is present."""
        base_mod = ModInfo(id="base_mod", name="Base", version="1.0")
        dependent_mod = ModInfo(
            id="dependent_mod",
            name="Dependent",
            version="1.0",
            dependencies=["base_mod"]
        )

        mod_registry.register_mod(base_mod)
        result = mod_registry.register_mod(dependent_mod)
        assert result is True

    def test_conflict_check(self, mod_registry):
        """Cannot register conflicting mods."""
        mod1 = ModInfo(id="mod1", name="Mod 1", version="1.0")
        mod2 = ModInfo(
            id="mod2",
            name="Mod 2",
            version="1.0",
            conflicts_with=["mod1"]
        )

        mod_registry.register_mod(mod1)

        with pytest.raises(ModValidationError):
            mod_registry.register_mod(mod2)


class TestCallbacks:
    """Tests for registry callbacks."""

    def test_mod_loaded_callback(self, mod_registry, mod_info):
        """Mod loaded callback is called."""
        loaded_mods = []
        mod_registry.on_mod_loaded(lambda m: loaded_mods.append(m.id))

        mod_registry.register_mod(mod_info)

        assert mod_info.id in loaded_mods

    def test_content_added_callback(self, mod_registry, theme_pack):
        """Content added callback is called."""
        added_content = []
        mod_registry.on_content_added(
            lambda t, id, c: added_content.append((t.name, id))
        )

        mod_registry.register_theme_pack(theme_pack)

        assert ("THEME_PACK", theme_pack.id) in added_content


class TestSerialization:
    """Tests for registry serialization."""

    def test_to_dict(self, mod_registry, mod_info):
        """Can serialize registry to dict."""
        mod_registry.register_mod(mod_info)
        data = mod_registry.to_dict()

        assert "mods" in data
        assert mod_info.id in data["mods"]

    def test_from_dict(self, mod_registry, mod_info):
        """Can restore registry from dict."""
        mod_registry.register_mod(mod_info)
        data = mod_registry.to_dict()

        restored = ModRegistry.from_dict(data)
        assert restored.mod_count == 1
        assert mod_info.id in [m.id for m in restored.list_mods()]


class TestFileLoading:
    """Tests for loading mods from files."""

    def test_load_from_file(self, mod_registry, sample_mod_file):
        """Can load a mod from a file."""
        mod_info = mod_registry.load_mod_from_file(str(sample_mod_file))

        assert mod_info.id == "sample_mod"
        assert mod_info.name == "Sample Mod"

    def test_load_nonexistent_file(self, mod_registry):
        """Loading nonexistent file raises error."""
        with pytest.raises(ModLoadError):
            mod_registry.load_mod_from_file("nonexistent.json")

    def test_load_from_directory(self, mod_registry, temp_mod_dir):
        """Can load mods from a directory."""
        # Create multiple mod files
        for i in range(3):
            mod_data = {
                "mod_info": {
                    "id": f"mod_{i}",
                    "name": f"Mod {i}",
                    "version": "1.0",
                }
            }
            with open(temp_mod_dir / f"mod_{i}.json", "w") as f:
                json.dump(mod_data, f)

        loaded = mod_registry.load_mods_from_directory(str(temp_mod_dir))

        assert len(loaded) == 3


class TestStats:
    """Tests for registry statistics."""

    def test_get_stats(self, mod_registry, mod_info, theme_pack, archetype_definition):
        """Can get registry statistics."""
        mod_registry.register_mod(mod_info)
        mod_registry.register_theme_pack(theme_pack)
        mod_registry.register_archetype(archetype_definition)

        stats = mod_registry.get_stats()

        assert stats["total_mods"] == 1
        assert stats["theme_packs"] == 1
        assert stats["archetypes"] == 1
