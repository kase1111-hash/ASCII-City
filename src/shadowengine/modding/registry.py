"""
Mod Registry for ShadowEngine.

Provides central management for loading, registering, and
organizing mod content including theme packs, archetypes,
scenarios, and custom content.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set, Callable
from pathlib import Path
import json
import os


class ModType(Enum):
    """Types of moddable content."""
    THEME_PACK = auto()      # Full theme/genre pack
    ARCHETYPE = auto()       # Character archetype
    SCENARIO = auto()        # Scripted scenario
    LOCATION = auto()        # Location template
    DIALOGUE = auto()        # Dialogue pack
    ASCII_ART = auto()       # ASCII art assets
    AUDIO = auto()           # Audio/voice configuration
    PERSONALITY = auto()     # Personality template
    CONFLICT = auto()        # Conflict type definition


class ModLoadError(Exception):
    """Error loading a mod."""
    pass


class ModValidationError(Exception):
    """Error validating mod content."""
    pass


@dataclass
class ContentConflict:
    """Describes a conflict between mod content."""

    content_type: ModType
    content_id: str
    source_mod: str
    conflicting_mod: str
    description: str
    resolvable: bool = True
    resolution_strategy: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content_type": self.content_type.name,
            "content_id": self.content_id,
            "source_mod": self.source_mod,
            "conflicting_mod": self.conflicting_mod,
            "description": self.description,
            "resolvable": self.resolvable,
            "resolution_strategy": self.resolution_strategy,
        }


@dataclass
class ModInfo:
    """Information about a loaded mod."""

    id: str
    name: str
    version: str
    author: str = "Unknown"
    description: str = ""
    mod_type: ModType = ModType.THEME_PACK

    # Dependencies and compatibility
    dependencies: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    game_version_min: str = "1.0.0"
    game_version_max: Optional[str] = None

    # Content registration
    registered_content: Dict[str, List[str]] = field(default_factory=dict)

    # State
    enabled: bool = True
    load_order: int = 0
    file_path: Optional[str] = None

    # Metadata
    tags: List[str] = field(default_factory=list)
    preview_image: Optional[str] = None
    homepage: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "mod_type": self.mod_type.name,
            "dependencies": self.dependencies,
            "conflicts_with": self.conflicts_with,
            "game_version_min": self.game_version_min,
            "game_version_max": self.game_version_max,
            "registered_content": self.registered_content,
            "enabled": self.enabled,
            "load_order": self.load_order,
            "file_path": self.file_path,
            "tags": self.tags,
            "preview_image": self.preview_image,
            "homepage": self.homepage,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModInfo':
        """Create from dictionary."""
        data = data.copy()
        if "mod_type" in data and isinstance(data["mod_type"], str):
            data["mod_type"] = ModType[data["mod_type"]]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ModRegistry:
    """
    Central registry for all mod content.

    Manages loading, registration, conflict resolution,
    and provides access to registered mod content.
    """

    def __init__(self):
        # Registered mods by ID
        self._mods: Dict[str, ModInfo] = {}

        # Content registries by type
        self._theme_packs: Dict[str, Any] = {}
        self._archetypes: Dict[str, Any] = {}
        self._scenarios: Dict[str, Any] = {}
        self._locations: Dict[str, Any] = {}
        self._dialogues: Dict[str, Any] = {}
        self._ascii_art: Dict[str, Any] = {}
        self._personalities: Dict[str, Any] = {}
        self._conflicts: Dict[str, Any] = {}

        # Content to mod mapping
        self._content_sources: Dict[str, str] = {}  # content_id -> mod_id

        # Detected conflicts
        self._conflicts_list: List[ContentConflict] = []

        # Load order tracking
        self._load_order: List[str] = []

        # Callbacks for content changes
        self._on_content_added: List[Callable[[ModType, str, Any], None]] = []
        self._on_content_removed: List[Callable[[ModType, str], None]] = []
        self._on_mod_loaded: List[Callable[[ModInfo], None]] = []
        self._on_mod_unloaded: List[Callable[[str], None]] = []

    # Properties

    @property
    def mod_count(self) -> int:
        """Get number of registered mods."""
        return len(self._mods)

    @property
    def enabled_mods(self) -> List[ModInfo]:
        """Get list of enabled mods."""
        return [m for m in self._mods.values() if m.enabled]

    @property
    def conflicts(self) -> List[ContentConflict]:
        """Get detected content conflicts."""
        return self._conflicts_list.copy()

    @property
    def has_conflicts(self) -> bool:
        """Check if there are unresolved conflicts."""
        return len(self._conflicts_list) > 0

    # Mod Registration

    def register_mod(self, mod_info: ModInfo) -> bool:
        """
        Register a mod with the registry.

        Args:
            mod_info: Information about the mod

        Returns:
            True if registered successfully

        Raises:
            ModValidationError: If mod fails validation
        """
        # Check for duplicate
        if mod_info.id in self._mods:
            raise ModValidationError(
                f"Mod '{mod_info.id}' is already registered"
            )

        # Check dependencies
        for dep_id in mod_info.dependencies:
            if dep_id not in self._mods:
                raise ModValidationError(
                    f"Missing dependency '{dep_id}' for mod '{mod_info.id}'"
                )

        # Check conflicts
        for conflict_id in mod_info.conflicts_with:
            if conflict_id in self._mods and self._mods[conflict_id].enabled:
                raise ModValidationError(
                    f"Mod '{mod_info.id}' conflicts with enabled mod '{conflict_id}'"
                )

        # Register mod
        self._mods[mod_info.id] = mod_info
        self._load_order.append(mod_info.id)
        mod_info.load_order = len(self._load_order) - 1

        # Notify callbacks
        for callback in self._on_mod_loaded:
            callback(mod_info)

        return True

    def unregister_mod(self, mod_id: str) -> bool:
        """
        Unregister a mod and all its content.

        Args:
            mod_id: ID of the mod to unregister

        Returns:
            True if unregistered successfully
        """
        if mod_id not in self._mods:
            return False

        mod_info = self._mods[mod_id]

        # Check if other mods depend on this
        for other_mod in self._mods.values():
            if mod_id in other_mod.dependencies and other_mod.enabled:
                raise ModValidationError(
                    f"Cannot unregister '{mod_id}': mod '{other_mod.id}' depends on it"
                )

        # Remove all content from this mod
        content_to_remove = [
            (content_id, self._content_sources[content_id])
            for content_id in list(self._content_sources.keys())
            if self._content_sources.get(content_id) == mod_id
        ]

        for content_id, _ in content_to_remove:
            self._remove_content(content_id)

        # Remove mod
        del self._mods[mod_id]
        self._load_order.remove(mod_id)

        # Notify callbacks
        for callback in self._on_mod_unloaded:
            callback(mod_id)

        return True

    def enable_mod(self, mod_id: str) -> bool:
        """Enable a disabled mod."""
        if mod_id not in self._mods:
            return False

        mod = self._mods[mod_id]
        mod.enabled = True
        return True

    def disable_mod(self, mod_id: str) -> bool:
        """Disable an enabled mod."""
        if mod_id not in self._mods:
            return False

        mod = self._mods[mod_id]
        mod.enabled = False
        return True

    def get_mod(self, mod_id: str) -> Optional[ModInfo]:
        """Get mod info by ID."""
        return self._mods.get(mod_id)

    def list_mods(self) -> List[ModInfo]:
        """Get all registered mods in load order."""
        return [self._mods[mid] for mid in self._load_order if mid in self._mods]

    # Content Registration

    def register_theme_pack(self, pack: Any, mod_id: str = "core") -> bool:
        """Register a theme pack."""
        return self._register_content(
            ModType.THEME_PACK, pack.id, pack, mod_id, self._theme_packs
        )

    def register_archetype(self, archetype: Any, mod_id: str = "core") -> bool:
        """Register a custom archetype."""
        return self._register_content(
            ModType.ARCHETYPE, archetype.id, archetype, mod_id, self._archetypes
        )

    def register_scenario(self, scenario: Any, mod_id: str = "core") -> bool:
        """Register a scenario script."""
        return self._register_content(
            ModType.SCENARIO, scenario.id, scenario, mod_id, self._scenarios
        )

    def register_location(self, location: Any, mod_id: str = "core") -> bool:
        """Register a location template."""
        return self._register_content(
            ModType.LOCATION, location.id, location, mod_id, self._locations
        )

    def register_dialogue(self, dialogue: Any, mod_id: str = "core") -> bool:
        """Register a dialogue pack."""
        return self._register_content(
            ModType.DIALOGUE, dialogue.id, dialogue, mod_id, self._dialogues
        )

    def register_ascii_art(self, art: Any, mod_id: str = "core") -> bool:
        """Register ASCII art assets."""
        return self._register_content(
            ModType.ASCII_ART, art.id, art, mod_id, self._ascii_art
        )

    def register_personality(self, personality: Any, mod_id: str = "core") -> bool:
        """Register a personality template."""
        return self._register_content(
            ModType.PERSONALITY, personality.name, personality, mod_id, self._personalities
        )

    def register_conflict_type(self, conflict: Any, mod_id: str = "core") -> bool:
        """Register a conflict type definition."""
        return self._register_content(
            ModType.CONFLICT, conflict.id, conflict, mod_id, self._conflicts
        )

    def _register_content(
        self,
        content_type: ModType,
        content_id: str,
        content: Any,
        mod_id: str,
        registry: Dict[str, Any],
    ) -> bool:
        """Internal method to register content."""
        # Check for conflict
        if content_id in registry:
            existing_mod = self._content_sources.get(content_id, "unknown")
            conflict = ContentConflict(
                content_type=content_type,
                content_id=content_id,
                source_mod=existing_mod,
                conflicting_mod=mod_id,
                description=f"{content_type.name} '{content_id}' already exists",
                resolvable=True,
                resolution_strategy="override",
            )
            self._conflicts_list.append(conflict)

        # Register content
        registry[content_id] = content
        self._content_sources[content_id] = mod_id

        # Update mod info
        if mod_id in self._mods:
            if content_type.name not in self._mods[mod_id].registered_content:
                self._mods[mod_id].registered_content[content_type.name] = []
            self._mods[mod_id].registered_content[content_type.name].append(content_id)

        # Notify callbacks
        for callback in self._on_content_added:
            callback(content_type, content_id, content)

        return True

    def _remove_content(self, content_id: str) -> bool:
        """Remove content by ID."""
        # Find and remove from appropriate registry
        registries = [
            (ModType.THEME_PACK, self._theme_packs),
            (ModType.ARCHETYPE, self._archetypes),
            (ModType.SCENARIO, self._scenarios),
            (ModType.LOCATION, self._locations),
            (ModType.DIALOGUE, self._dialogues),
            (ModType.ASCII_ART, self._ascii_art),
            (ModType.PERSONALITY, self._personalities),
            (ModType.CONFLICT, self._conflicts),
        ]

        for content_type, registry in registries:
            if content_id in registry:
                del registry[content_id]
                del self._content_sources[content_id]

                # Notify callbacks
                for callback in self._on_content_removed:
                    callback(content_type, content_id)

                return True

        return False

    # Content Retrieval

    def get_theme_pack(self, pack_id: str) -> Optional[Any]:
        """Get a theme pack by ID."""
        return self._theme_packs.get(pack_id)

    def get_archetype(self, archetype_id: str) -> Optional[Any]:
        """Get an archetype by ID."""
        return self._archetypes.get(archetype_id)

    def get_scenario(self, scenario_id: str) -> Optional[Any]:
        """Get a scenario by ID."""
        return self._scenarios.get(scenario_id)

    def get_location(self, location_id: str) -> Optional[Any]:
        """Get a location template by ID."""
        return self._locations.get(location_id)

    def get_dialogue(self, dialogue_id: str) -> Optional[Any]:
        """Get a dialogue pack by ID."""
        return self._dialogues.get(dialogue_id)

    def get_ascii_art(self, art_id: str) -> Optional[Any]:
        """Get ASCII art by ID."""
        return self._ascii_art.get(art_id)

    def get_personality(self, personality_name: str) -> Optional[Any]:
        """Get a personality template by name."""
        return self._personalities.get(personality_name)

    def get_conflict_type(self, conflict_id: str) -> Optional[Any]:
        """Get a conflict type by ID."""
        return self._conflicts.get(conflict_id)

    # Listing

    def list_theme_packs(self) -> List[str]:
        """List all registered theme pack IDs."""
        return list(self._theme_packs.keys())

    def list_archetypes(self) -> List[str]:
        """List all registered archetype IDs."""
        return list(self._archetypes.keys())

    def list_scenarios(self) -> List[str]:
        """List all registered scenario IDs."""
        return list(self._scenarios.keys())

    def list_locations(self) -> List[str]:
        """List all registered location IDs."""
        return list(self._locations.keys())

    def list_personalities(self) -> List[str]:
        """List all registered personality names."""
        return list(self._personalities.keys())

    def list_conflict_types(self) -> List[str]:
        """List all registered conflict type IDs."""
        return list(self._conflicts.keys())

    # Conflict Resolution

    def resolve_conflict(
        self,
        conflict: ContentConflict,
        strategy: str = "keep_existing"
    ) -> bool:
        """
        Resolve a content conflict.

        Args:
            conflict: The conflict to resolve
            strategy: Resolution strategy:
                - "keep_existing": Keep the original content
                - "override": Replace with new content
                - "merge": Attempt to merge (if supported)

        Returns:
            True if resolved successfully
        """
        if conflict not in self._conflicts_list:
            return False

        if strategy == "keep_existing":
            # Remove conflicting content (already handled by registration)
            pass
        elif strategy == "override":
            # Content was already overwritten during registration
            pass
        elif strategy == "merge":
            # Merging would require content-specific logic
            pass

        self._conflicts_list.remove(conflict)
        return True

    def clear_conflicts(self) -> int:
        """Clear all conflicts. Returns number cleared."""
        count = len(self._conflicts_list)
        self._conflicts_list.clear()
        return count

    # Callbacks

    def on_content_added(
        self, callback: Callable[[ModType, str, Any], None]
    ) -> None:
        """Register callback for content addition."""
        self._on_content_added.append(callback)

    def on_content_removed(
        self, callback: Callable[[ModType, str], None]
    ) -> None:
        """Register callback for content removal."""
        self._on_content_removed.append(callback)

    def on_mod_loaded(self, callback: Callable[[ModInfo], None]) -> None:
        """Register callback for mod loading."""
        self._on_mod_loaded.append(callback)

    def on_mod_unloaded(self, callback: Callable[[str], None]) -> None:
        """Register callback for mod unloading."""
        self._on_mod_unloaded.append(callback)

    # Loading

    def load_mod_from_file(self, file_path: str) -> ModInfo:
        """
        Load a mod from a JSON file.

        Args:
            file_path: Path to the mod file

        Returns:
            ModInfo for the loaded mod

        Raises:
            ModLoadError: If loading fails
        """
        path = Path(file_path)
        if not path.exists():
            raise ModLoadError(f"Mod file not found: {file_path}")

        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ModLoadError(f"Invalid JSON in mod file: {e}")

        # Extract mod info
        if "mod_info" not in data:
            raise ModLoadError("Missing 'mod_info' section in mod file")

        mod_info = ModInfo.from_dict(data["mod_info"])
        mod_info.file_path = str(path.absolute())

        # Register the mod
        self.register_mod(mod_info)

        return mod_info

    def load_mods_from_directory(self, directory: str) -> List[ModInfo]:
        """
        Load all mods from a directory.

        Args:
            directory: Path to the mods directory

        Returns:
            List of loaded ModInfo objects
        """
        path = Path(directory)
        if not path.exists():
            return []

        loaded = []
        for mod_file in path.glob("*.json"):
            try:
                mod_info = self.load_mod_from_file(str(mod_file))
                loaded.append(mod_info)
            except (ModLoadError, ModValidationError) as e:
                # Log error but continue loading other mods
                print(f"Warning: Failed to load mod {mod_file}: {e}")

        return loaded

    # Serialization

    def to_dict(self) -> Dict[str, Any]:
        """Convert registry state to dictionary."""
        return {
            "mods": {mid: m.to_dict() for mid, m in self._mods.items()},
            "load_order": self._load_order,
            "conflicts": [c.to_dict() for c in self._conflicts_list],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModRegistry':
        """Restore registry state from dictionary."""
        registry = cls()
        registry._load_order = data.get("load_order", [])

        for mod_id, mod_data in data.get("mods", {}).items():
            mod_info = ModInfo.from_dict(mod_data)
            registry._mods[mod_id] = mod_info

        return registry

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_mods": len(self._mods),
            "enabled_mods": len([m for m in self._mods.values() if m.enabled]),
            "theme_packs": len(self._theme_packs),
            "archetypes": len(self._archetypes),
            "scenarios": len(self._scenarios),
            "locations": len(self._locations),
            "personalities": len(self._personalities),
            "conflicts": len(self._conflicts),
            "content_conflicts": len(self._conflicts_list),
        }
