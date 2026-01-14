"""
Scenario Scripting System for ShadowEngine.

Provides a declarative way to define scenarios, events, triggers,
and actions that can be loaded from files or created programmatically.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import json


class TriggerType(Enum):
    """Types of event triggers."""
    # Time-based
    ON_GAME_START = auto()
    ON_TIME = auto()             # Specific time
    AFTER_DELAY = auto()         # After X time units

    # Location-based
    ON_ENTER_LOCATION = auto()
    ON_EXIT_LOCATION = auto()
    ON_FIRST_VISIT = auto()

    # Character-based
    ON_TALK_TO = auto()
    ON_CHARACTER_CRACK = auto()
    ON_CHARACTER_DEATH = auto()

    # Discovery-based
    ON_DISCOVER_FACT = auto()
    ON_DISCOVER_EVIDENCE = auto()
    ON_REVELATION = auto()

    # Progress-based
    ON_PROGRESS = auto()         # Story progress percentage
    ON_ACCUSATION = auto()
    ON_CORRECT_ACCUSATION = auto()
    ON_WRONG_ACCUSATION = auto()

    # Item-based
    ON_TAKE_ITEM = auto()
    ON_USE_ITEM = auto()
    ON_GIVE_ITEM = auto()

    # State-based
    ON_TENSION_THRESHOLD = auto()
    ON_WEATHER_CHANGE = auto()
    ON_MORAL_SHIFT = auto()

    # Custom
    CUSTOM = auto()


class ActionType(Enum):
    """Types of scripted actions."""
    # Dialogue
    SHOW_DIALOGUE = auto()
    SHOW_NARRATION = auto()
    SET_DIALOGUE_OPTION = auto()

    # Character
    SPAWN_CHARACTER = auto()
    MOVE_CHARACTER = auto()
    REMOVE_CHARACTER = auto()
    SET_CHARACTER_STATE = auto()
    SET_CHARACTER_MOOD = auto()
    CRACK_CHARACTER = auto()

    # Location
    UNLOCK_LOCATION = auto()
    LOCK_LOCATION = auto()
    MODIFY_LOCATION = auto()

    # Items/Evidence
    ADD_ITEM = auto()
    REMOVE_ITEM = auto()
    REVEAL_EVIDENCE = auto()

    # Narrative
    TRIGGER_REVELATION = auto()
    SET_PROGRESS = auto()
    TRIGGER_TWIST = auto()
    SET_TENSION = auto()

    # Environment
    SET_WEATHER = auto()
    SET_TIME = auto()
    PLAY_SOUND = auto()
    PLAY_MUSIC = auto()

    # Game State
    SAVE_CHECKPOINT = auto()
    END_GAME = auto()
    SET_FLAG = auto()
    INCREMENT_COUNTER = auto()

    # Custom
    CUSTOM = auto()
    CALL_FUNCTION = auto()


@dataclass
class EventTrigger:
    """
    Defines when a scripted event should fire.
    """

    trigger_type: TriggerType
    target: Optional[str] = None      # Target ID (location, character, etc.)
    value: Optional[Any] = None       # Threshold or specific value
    conditions: Dict[str, Any] = field(default_factory=dict)  # Additional conditions
    once: bool = False                # Only trigger once
    priority: int = 0                 # Higher = earlier execution

    # State tracking
    triggered: bool = False

    def check_conditions(self, game_state: Dict[str, Any]) -> bool:
        """Check if all conditions are met."""
        for key, expected in self.conditions.items():
            actual = game_state.get(key)
            if actual != expected:
                return False
        return True

    def can_trigger(self, game_state: Dict[str, Any]) -> bool:
        """Check if this trigger can fire."""
        if self.once and self.triggered:
            return False
        return self.check_conditions(game_state)

    def mark_triggered(self) -> None:
        """Mark this trigger as having fired."""
        self.triggered = True

    def reset(self) -> None:
        """Reset trigger state."""
        self.triggered = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trigger_type": self.trigger_type.name,
            "target": self.target,
            "value": self.value,
            "conditions": self.conditions,
            "once": self.once,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventTrigger':
        """Create from dictionary."""
        data = data.copy()
        if "trigger_type" in data and isinstance(data["trigger_type"], str):
            data["trigger_type"] = TriggerType[data["trigger_type"]]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class EventAction:
    """
    Defines an action to perform when an event fires.
    """

    action_type: ActionType
    target: Optional[str] = None      # Target ID
    value: Optional[Any] = None       # Value to set/use
    parameters: Dict[str, Any] = field(default_factory=dict)  # Additional params
    delay: float = 0.0                # Delay in time units
    duration: float = 0.0             # Duration for timed actions

    def execute(self, game: Any) -> bool:
        """
        Execute this action.

        Args:
            game: Game instance to modify

        Returns:
            True if action completed successfully
        """
        # This is a stub - actual implementation would interact with game
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_type": self.action_type.name,
            "target": self.target,
            "value": self.value,
            "parameters": self.parameters,
            "delay": self.delay,
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventAction':
        """Create from dictionary."""
        data = data.copy()
        if "action_type" in data and isinstance(data["action_type"], str):
            data["action_type"] = ActionType[data["action_type"]]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ScriptedEvent:
    """
    A scripted event combining triggers and actions.
    """

    id: str
    name: str
    description: str = ""

    # When to trigger
    triggers: List[EventTrigger] = field(default_factory=list)

    # What to do
    actions: List[EventAction] = field(default_factory=list)

    # Control flow
    enabled: bool = True
    require_all_triggers: bool = False  # AND vs OR for multiple triggers
    priority: int = 0

    # State
    executed_count: int = 0
    max_executions: int = -1  # -1 = unlimited

    def add_trigger(self, trigger: EventTrigger) -> None:
        """Add a trigger to this event."""
        self.triggers.append(trigger)

    def add_action(self, action: EventAction) -> None:
        """Add an action to this event."""
        self.actions.append(action)

    def can_execute(self, game_state: Dict[str, Any]) -> bool:
        """Check if this event can execute."""
        if not self.enabled:
            return False
        if self.max_executions >= 0 and self.executed_count >= self.max_executions:
            return False

        if not self.triggers:
            return False

        if self.require_all_triggers:
            return all(t.can_trigger(game_state) for t in self.triggers)
        else:
            return any(t.can_trigger(game_state) for t in self.triggers)

    def execute(self, game: Any) -> bool:
        """Execute all actions for this event."""
        success = True
        for action in sorted(self.actions, key=lambda a: a.delay):
            if not action.execute(game):
                success = False
        if success:
            self.executed_count += 1
            for trigger in self.triggers:
                if trigger.once:
                    trigger.mark_triggered()
        return success

    def reset(self) -> None:
        """Reset event state."""
        self.executed_count = 0
        for trigger in self.triggers:
            trigger.reset()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "triggers": [t.to_dict() for t in self.triggers],
            "actions": [a.to_dict() for a in self.actions],
            "enabled": self.enabled,
            "require_all_triggers": self.require_all_triggers,
            "priority": self.priority,
            "max_executions": self.max_executions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScriptedEvent':
        """Create from dictionary."""
        data = data.copy()
        if "triggers" in data:
            data["triggers"] = [
                EventTrigger.from_dict(t) for t in data["triggers"]
            ]
        if "actions" in data:
            data["actions"] = [
                EventAction.from_dict(a) for a in data["actions"]
            ]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CharacterTemplate:
    """Template for spawning characters in a scenario."""

    id: str
    name: str
    archetype: str  # Archetype ID (built-in or custom)
    description: str = ""

    # Initial state
    starting_location: Optional[str] = None
    starting_mood: str = "neutral"

    # Knowledge
    known_facts: List[str] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)

    # Dialogue
    dialogue_pool: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)

    # Relationships
    relationships: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Role in narrative
    is_culprit: bool = False
    is_victim: bool = False
    is_witness: bool = False
    is_red_herring: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "archetype": self.archetype,
            "description": self.description,
            "starting_location": self.starting_location,
            "starting_mood": self.starting_mood,
            "known_facts": self.known_facts,
            "secrets": self.secrets,
            "dialogue_pool": self.dialogue_pool,
            "topics": self.topics,
            "relationships": self.relationships,
            "is_culprit": self.is_culprit,
            "is_victim": self.is_victim,
            "is_witness": self.is_witness,
            "is_red_herring": self.is_red_herring,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterTemplate':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class LocationTemplate:
    """Template for creating locations in a scenario."""

    id: str
    name: str
    description: str = ""

    # Visual
    ascii_art: List[str] = field(default_factory=list)

    # Properties
    is_outdoor: bool = False
    base_light_level: float = 0.5
    ambient_description: str = ""

    # Connections
    exits: Dict[str, str] = field(default_factory=dict)  # direction -> location_id

    # Hotspots
    hotspots: List[Dict[str, Any]] = field(default_factory=list)

    # Items and evidence
    items: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

    # Accessibility
    requires_key: Optional[str] = None
    requires_discovery: Optional[str] = None
    initially_locked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "ascii_art": self.ascii_art,
            "is_outdoor": self.is_outdoor,
            "base_light_level": self.base_light_level,
            "ambient_description": self.ambient_description,
            "exits": self.exits,
            "hotspots": self.hotspots,
            "items": self.items,
            "evidence": self.evidence,
            "requires_key": self.requires_key,
            "requires_discovery": self.requires_discovery,
            "initially_locked": self.initially_locked,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationTemplate':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ConflictTemplate:
    """Template for defining a conflict/mystery."""

    id: str
    name: str
    conflict_type: str  # murder, theft, etc.
    description: str = ""

    # Resolution
    solution_description: str = ""
    motive: str = ""
    method: str = ""
    opportunity: str = ""

    # Evidence chain (fact IDs needed to solve)
    evidence_chain: List[str] = field(default_factory=list)

    # Revelations
    revelations: List[Dict[str, Any]] = field(default_factory=list)

    # Red herrings
    red_herrings: List[Dict[str, Any]] = field(default_factory=list)

    # Twist
    has_twist: bool = False
    twist_type: str = ""
    twist_description: str = ""
    twist_trigger_progress: float = 0.6

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "conflict_type": self.conflict_type,
            "description": self.description,
            "solution_description": self.solution_description,
            "motive": self.motive,
            "method": self.method,
            "opportunity": self.opportunity,
            "evidence_chain": self.evidence_chain,
            "revelations": self.revelations,
            "red_herrings": self.red_herrings,
            "has_twist": self.has_twist,
            "twist_type": self.twist_type,
            "twist_description": self.twist_description,
            "twist_trigger_progress": self.twist_trigger_progress,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConflictTemplate':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ScenarioScript:
    """
    Complete scenario definition.

    Combines all elements needed to create a playable scenario.
    """

    # Identity
    id: str
    name: str
    version: str = "1.0.0"
    author: str = "Unknown"
    description: str = ""

    # Theme
    theme_pack: Optional[str] = None  # Theme pack ID to use

    # Content
    conflict: Optional[ConflictTemplate] = None
    characters: List[CharacterTemplate] = field(default_factory=list)
    locations: List[LocationTemplate] = field(default_factory=list)
    events: List[ScriptedEvent] = field(default_factory=list)

    # Configuration
    starting_location: str = ""
    starting_time: int = 20  # Hour (0-23)
    starting_weather: str = "clear"
    starting_tension: float = 0.3

    # Flags and variables
    initial_flags: Dict[str, bool] = field(default_factory=dict)
    initial_counters: Dict[str, int] = field(default_factory=dict)

    # Metadata
    tags: List[str] = field(default_factory=list)
    difficulty: str = "normal"  # easy, normal, hard
    estimated_playtime: int = 30  # minutes

    def get_character(self, char_id: str) -> Optional[CharacterTemplate]:
        """Get a character template by ID."""
        for char in self.characters:
            if char.id == char_id:
                return char
        return None

    def get_location(self, loc_id: str) -> Optional[LocationTemplate]:
        """Get a location template by ID."""
        for loc in self.locations:
            if loc.id == loc_id:
                return loc
        return None

    def get_event(self, event_id: str) -> Optional[ScriptedEvent]:
        """Get an event by ID."""
        for event in self.events:
            if event.id == event_id:
                return event
        return None

    def get_active_events(self, game_state: Dict[str, Any]) -> List[ScriptedEvent]:
        """Get events that can currently execute."""
        return [
            e for e in self.events
            if e.can_execute(game_state)
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "theme_pack": self.theme_pack,
            "conflict": self.conflict.to_dict() if self.conflict else None,
            "characters": [c.to_dict() for c in self.characters],
            "locations": [l.to_dict() for l in self.locations],
            "events": [e.to_dict() for e in self.events],
            "starting_location": self.starting_location,
            "starting_time": self.starting_time,
            "starting_weather": self.starting_weather,
            "starting_tension": self.starting_tension,
            "initial_flags": self.initial_flags,
            "initial_counters": self.initial_counters,
            "tags": self.tags,
            "difficulty": self.difficulty,
            "estimated_playtime": self.estimated_playtime,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScenarioScript':
        """Create from dictionary."""
        data = data.copy()
        if "conflict" in data and data["conflict"]:
            data["conflict"] = ConflictTemplate.from_dict(data["conflict"])
        if "characters" in data:
            data["characters"] = [
                CharacterTemplate.from_dict(c) for c in data["characters"]
            ]
        if "locations" in data:
            data["locations"] = [
                LocationTemplate.from_dict(l) for l in data["locations"]
            ]
        if "events" in data:
            data["events"] = [
                ScriptedEvent.from_dict(e) for e in data["events"]
            ]
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ScenarioValidator:
    """Validates scenario scripts for consistency and completeness."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, scenario: ScenarioScript) -> bool:
        """
        Validate a scenario script.

        Returns:
            True if valid (may still have warnings)
        """
        self.errors = []
        self.warnings = []

        # Required fields
        if not scenario.id:
            self.errors.append("Scenario must have an ID")
        if not scenario.name:
            self.errors.append("Scenario must have a name")

        # Validate conflict
        if scenario.conflict:
            self._validate_conflict(scenario.conflict)

        # Validate characters
        char_ids = set()
        for char in scenario.characters:
            if char.id in char_ids:
                self.errors.append(f"Duplicate character ID: {char.id}")
            char_ids.add(char.id)
            self._validate_character(char)

        # Validate locations
        loc_ids = set()
        for loc in scenario.locations:
            if loc.id in loc_ids:
                self.errors.append(f"Duplicate location ID: {loc.id}")
            loc_ids.add(loc.id)
            self._validate_location(loc, loc_ids, char_ids)

        # Validate starting location
        if scenario.starting_location and scenario.starting_location not in loc_ids:
            self.errors.append(
                f"Starting location '{scenario.starting_location}' not found"
            )

        # Validate events
        event_ids = set()
        for event in scenario.events:
            if event.id in event_ids:
                self.errors.append(f"Duplicate event ID: {event.id}")
            event_ids.add(event.id)
            self._validate_event(event, char_ids, loc_ids)

        return len(self.errors) == 0

    def _validate_conflict(self, conflict: ConflictTemplate) -> None:
        """Validate a conflict template."""
        if not conflict.conflict_type:
            self.errors.append("Conflict must have a type")
        if not conflict.evidence_chain:
            self.warnings.append("Conflict has no evidence chain")

    def _validate_character(self, char: CharacterTemplate) -> None:
        """Validate a character template."""
        if not char.name:
            self.errors.append(f"Character {char.id} has no name")
        if not char.archetype:
            self.warnings.append(f"Character {char.id} has no archetype")

    def _validate_location(
        self,
        loc: LocationTemplate,
        all_locs: Set[str],
        all_chars: Set[str]
    ) -> None:
        """Validate a location template."""
        if not loc.name:
            self.errors.append(f"Location {loc.id} has no name")

        # Check exit targets
        for direction, target in loc.exits.items():
            if target not in all_locs:
                self.warnings.append(
                    f"Location {loc.id} exit '{direction}' points to unknown location '{target}'"
                )

    def _validate_event(
        self,
        event: ScriptedEvent,
        all_chars: Set[str],
        all_locs: Set[str]
    ) -> None:
        """Validate a scripted event."""
        if not event.triggers:
            self.warnings.append(f"Event {event.id} has no triggers")
        if not event.actions:
            self.warnings.append(f"Event {event.id} has no actions")


class ScenarioLoader:
    """Loads scenarios from files."""

    def __init__(self, scenarios_dir: str = "scenarios"):
        self.scenarios_dir = Path(scenarios_dir)
        self._loaded: Dict[str, ScenarioScript] = {}

    def load(self, scenario_id: str) -> Optional[ScenarioScript]:
        """Load a scenario by ID."""
        if scenario_id in self._loaded:
            return self._loaded[scenario_id]

        # Try to find scenario file
        file_path = self.scenarios_dir / f"{scenario_id}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            scenario = ScenarioScript.from_dict(data)
            self._loaded[scenario_id] = scenario
            return scenario
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading scenario {scenario_id}: {e}")
            return None

    def load_from_file(self, file_path: str) -> ScenarioScript:
        """Load a scenario from a specific file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return ScenarioScript.from_dict(data)

    def save(self, scenario: ScenarioScript, file_path: Optional[str] = None) -> None:
        """Save a scenario to a file."""
        if file_path is None:
            file_path = self.scenarios_dir / f"{scenario.id}.json"
        else:
            file_path = Path(file_path)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w') as f:
            json.dump(scenario.to_dict(), f, indent=2)

    def list_available(self) -> List[str]:
        """List available scenario IDs."""
        if not self.scenarios_dir.exists():
            return []
        return [
            f.stem for f in self.scenarios_dir.glob("*.json")
        ]

    def get_loaded(self) -> Dict[str, ScenarioScript]:
        """Get all loaded scenarios."""
        return self._loaded.copy()

    def unload(self, scenario_id: str) -> bool:
        """Unload a scenario from memory."""
        if scenario_id in self._loaded:
            del self._loaded[scenario_id]
            return True
        return False
