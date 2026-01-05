# ShadowEngine Technical Specification Sheet

> **Version**: 1.0.0
> **Status**: Implementation Ready
> **Target Platform**: Cross-platform CLI (Terminal/CMD)
> **Language**: Python 3.10+

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Core Modules](#3-core-modules)
4. [Data Structures](#4-data-structures)
5. [APIs & Interfaces](#5-apis--interfaces)
6. [Rendering System](#6-rendering-system)
7. [Input System](#7-input-system)
8. [Save/Load System](#8-saveload-system)
9. [Configuration](#9-configuration)
10. [Implementation Phases](#10-implementation-phases)

---

## 1. System Overview

### 1.1 Purpose

ShadowEngine is a memory-first procedural storytelling game engine for CLI/terminal environments. It generates coherent, replayable narrative experiences using procedural systems, persistent memory, and ASCII art visualization.

### 1.2 Core Principles

| Principle | Implementation |
|-----------|----------------|
| Memory First | All game events persist in a three-layer memory system |
| Systems Over Scripts | Character behavior emerges from simulation, not dialogue trees |
| Procedural ≠ Random | All randomness constrained by narrative logic via seed system |
| Atmosphere Is Mechanics | Weather/environment affects gameplay, not just visuals |
| Player Is a Lens | Player perception tracked separately from objective truth |

### 1.3 Technical Requirements

```
Python Version:     >= 3.10
Dependencies:       Standard library only (no external packages required)
Terminal:           Minimum 80x24 characters, 256-color support recommended
Memory:             < 100MB RAM
Storage:            < 50MB per save file
```

---

## 2. Architecture

### 2.1 System Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                        GAME LOOP                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   INPUT      │───▶│  NARRATIVE   │───▶│   MEMORY     │       │
│  │   SYSTEM     │    │   ENGINE     │    │   BANK       │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         │                   ▼                   │                │
│         │           ┌──────────────┐            │                │
│         │           │  CHARACTER   │◀───────────┘                │
│         │           │  SIMULATION  │                             │
│         │           └──────────────┘                             │
│         │                   │                                    │
│         │                   ▼                                    │
│         │           ┌──────────────┐                             │
│         │           │ ENVIRONMENT  │                             │
│         │           │  SIMULATOR   │                             │
│         │           └──────────────┘                             │
│         │                   │                                    │
│         ▼                   ▼                                    │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              ASCII RENDER ENGINE                      │       │
│  └──────────────────────────────────────────────────────┘       │
│                            │                                     │
│                            ▼                                     │
│                     ┌──────────────┐                             │
│                     │   TERMINAL   │                             │
│                     │   OUTPUT     │                             │
│                     └──────────────┘                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Module Dependency Graph

```
                    ┌─────────────┐
                    │    CORE     │
                    │   CONFIG    │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  MEMORY  │    │   RNG    │    │  UTILS   │
    │   BANK   │    │  SYSTEM  │    │          │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
  ┌────────────┐  ┌────────────┐  ┌────────────┐
  │ NARRATIVE  │  │ CHARACTER  │  │ENVIRONMENT │
  │   SPINE    │  │    SIM     │  │    SIM     │
  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
                 ┌────────────┐
                 │   SCENE    │
                 │  MANAGER   │
                 └─────┬──────┘
                       │
           ┌───────────┼───────────┐
           │           │           │
           ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  INPUT   │ │  RENDER  │ │  MORAL   │
    │  ENGINE  │ │  ENGINE  │ │  ENGINE  │
    └──────────┘ └──────────┘ └──────────┘
```

### 2.3 Directory Structure

```
shadowengine/
├── __init__.py
├── main.py                    # Entry point
├── config.py                  # Configuration loader
│
├── core/
│   ├── __init__.py
│   ├── game_loop.py          # Main game loop
│   ├── rng.py                # Seeded random system
│   ├── events.py             # Event bus system
│   └── utils.py              # Shared utilities
│
├── memory/
│   ├── __init__.py
│   ├── memory_bank.py        # Main memory coordinator
│   ├── world_memory.py       # Objective world state
│   ├── character_memory.py   # Per-NPC memory
│   └── player_memory.py      # Player perception
│
├── narrative/
│   ├── __init__.py
│   ├── spine_generator.py    # Narrative spine creation
│   ├── story_state.py        # Current story state
│   ├── dialogue.py           # Dialogue generation
│   └── endings.py            # Ending determination
│
├── simulation/
│   ├── __init__.py
│   ├── character_sim.py      # NPC behavior simulation
│   ├── environment_sim.py    # Weather/time simulation
│   └── moral_engine.py       # Moral consequence tracking
│
├── render/
│   ├── __init__.py
│   ├── renderer.py           # Main render coordinator
│   ├── scene.py              # Scene composition
│   ├── particles.py          # Particle systems
│   ├── ui.py                 # UI elements
│   └── assets/
│       ├── __init__.py
│       └── ascii_art.py      # ASCII art definitions
│
├── input/
│   ├── __init__.py
│   ├── parser.py             # Command parser
│   ├── hotspots.py           # Hotspot system
│   └── actions.py            # Action handlers
│
├── persistence/
│   ├── __init__.py
│   ├── save_manager.py       # Save/load system
│   └── serializers.py        # JSON serialization
│
└── data/
    ├── scenarios/            # Game scenario definitions
    │   └── noir_york/
    │       ├── config.json
    │       ├── locations.json
    │       ├── characters.json
    │       └── archetypes.json
    └── templates/            # Text templates
        ├── dialogue.json
        └── narration.json
```

---

## 3. Core Modules

### 3.1 Game Loop (`core/game_loop.py`)

```python
class GameLoop:
    """Main game loop coordinator."""

    # Constants
    TARGET_FPS: int = 30
    TICK_RATE: float = 1.0 / 30.0

    # States
    class State(Enum):
        INITIALIZING = auto()
        RUNNING = auto()
        PAUSED = auto()
        DIALOGUE = auto()
        CUTSCENE = auto()
        MENU = auto()
        SAVING = auto()
        LOADING = auto()
        QUITTING = auto()

    # Methods
    def __init__(self, config: Config) -> None: ...
    def start(self, scenario: str, seed: Optional[int] = None) -> None: ...
    def tick(self) -> None: ...
    def process_input(self) -> None: ...
    def update(self, dt: float) -> None: ...
    def render(self) -> None: ...
    def shutdown(self) -> None: ...
```

### 3.2 Seeded RNG System (`core/rng.py`)

```python
class SeededRNG:
    """Deterministic random number generator for reproducible gameplay."""

    def __init__(self, seed: int) -> None: ...
    def get_seed(self) -> int: ...
    def random(self) -> float: ...                              # 0.0 to 1.0
    def randint(self, a: int, b: int) -> int: ...              # inclusive
    def choice(self, seq: Sequence[T]) -> T: ...
    def weighted_choice(self, weights: dict[T, float]) -> T: ...
    def shuffle(self, seq: MutableSequence) -> None: ...
    def fork(self, subsystem: str) -> 'SeededRNG': ...         # Create child RNG

    # Narrative-specific methods
    def probability_check(self, chance: float) -> bool: ...
    def bell_curve(self, mean: float, stddev: float) -> float: ...
```

### 3.3 Event Bus (`core/events.py`)

```python
@dataclass
class GameEvent:
    """Base class for all game events."""
    timestamp: float
    source: str
    data: dict[str, Any]

class EventType(Enum):
    # Narrative Events
    STORY_BEAT_TRIGGERED = auto()
    CLUE_DISCOVERED = auto()
    CHARACTER_MET = auto()
    DIALOGUE_STARTED = auto()
    DIALOGUE_ENDED = auto()

    # World Events
    LOCATION_ENTERED = auto()
    LOCATION_EXITED = auto()
    TIME_ADVANCED = auto()
    WEATHER_CHANGED = auto()

    # Character Events
    NPC_STATE_CHANGED = auto()
    NPC_TRUST_CHANGED = auto()
    NPC_REVEALED_SECRET = auto()

    # Player Events
    PLAYER_ACTION = auto()
    MORAL_SHIFT = auto()
    ITEM_ACQUIRED = auto()
    ITEM_USED = auto()

    # System Events
    GAME_SAVED = auto()
    GAME_LOADED = auto()
    SCENE_CHANGED = auto()

class EventBus:
    """Publish-subscribe event system."""

    def subscribe(self, event_type: EventType, handler: Callable) -> None: ...
    def unsubscribe(self, event_type: EventType, handler: Callable) -> None: ...
    def publish(self, event_type: EventType, event: GameEvent) -> None: ...
    def queue(self, event_type: EventType, event: GameEvent, delay: float) -> None: ...
    def process_queue(self) -> None: ...
```

---

## 4. Data Structures

### 4.1 Memory System (`memory/`)

#### World Memory

```python
@dataclass
class WorldEvent:
    """An objective event that occurred in the world."""
    id: str
    timestamp: float
    location: str
    event_type: str
    actors: list[str]           # Character IDs involved
    data: dict[str, Any]
    is_public: bool             # Witnessed by NPCs?
    witnesses: list[str]        # Who saw it

class WorldMemory:
    """Objective truth of what happened in the game world."""

    events: list[WorldEvent]
    location_states: dict[str, LocationState]
    item_locations: dict[str, str]           # item_id -> location_id
    time_of_day: TimeOfDay
    current_weather: Weather
    global_flags: dict[str, Any]

    def record_event(self, event: WorldEvent) -> None: ...
    def query_events(self, filters: EventFilter) -> list[WorldEvent]: ...
    def get_events_at_location(self, location: str) -> list[WorldEvent]: ...
    def get_events_involving(self, character: str) -> list[WorldEvent]: ...
```

#### Character Memory

```python
@dataclass
class Belief:
    """Something a character believes to be true."""
    subject: str
    content: str
    confidence: float           # 0.0 to 1.0
    source: str                 # How they learned it
    timestamp: float

@dataclass
class Relationship:
    """A character's feelings toward another."""
    target_id: str
    trust: float               # -1.0 to 1.0
    fear: float                # 0.0 to 1.0
    respect: float             # -1.0 to 1.0
    history: list[str]         # Key interaction IDs

class CharacterMemory:
    """What a specific NPC knows and believes."""

    character_id: str
    beliefs: list[Belief]
    relationships: dict[str, Relationship]
    witnessed_events: list[str]    # WorldEvent IDs
    secrets_known: list[str]       # Secret IDs
    lies_told: list[str]           # To track consistency
    emotional_state: EmotionalState

    def add_belief(self, belief: Belief) -> None: ...
    def update_relationship(self, target: str, changes: dict) -> None: ...
    def knows_about(self, subject: str) -> bool: ...
    def would_reveal(self, secret: str, to_player: bool) -> float: ...  # Probability
```

#### Player Memory

```python
@dataclass
class PlayerPerception:
    """What the player character perceives about something."""
    subject: str
    perception: str
    bias: str                  # How player views it
    certainty: float

class PlayerMemory:
    """The protagonist's subjective experience."""

    perceptions: dict[str, PlayerPerception]
    suspects: dict[str, float]      # character_id -> suspicion level
    clues_found: list[str]
    locations_visited: set[str]
    characters_met: set[str]
    current_theories: list[str]     # Player's working hypotheses
    moral_profile: MoralProfile
    narration_tone: NarrationTone   # Affects how events are described

    def record_perception(self, perception: PlayerPerception) -> None: ...
    def update_suspicion(self, character: str, delta: float) -> None: ...
    def get_narration_style(self) -> NarrationStyle: ...
```

### 4.2 Character System (`simulation/character_sim.py`)

```python
@dataclass
class CharacterArchetype:
    """Template for character generation."""
    id: str
    name_patterns: list[str]
    occupation_pool: list[str]
    personality_weights: dict[str, float]
    secret_types: list[str]
    dialogue_style: str
    visual_descriptors: list[str]

@dataclass
class MotivationVector:
    """What drives a character's behavior."""
    fear: float            # 0.0 to 1.0
    greed: float           # 0.0 to 1.0
    loyalty: float         # 0.0 to 1.0
    pride: float           # 0.0 to 1.0
    desperation: float     # 0.0 to 1.0

@dataclass
class Character:
    """A fully realized NPC."""
    id: str
    name: str
    archetype: str
    occupation: str

    # Truth vs Lies
    true_role: str              # Actual role in the crime
    public_persona: str         # What they show the world
    secret: str                 # What they're hiding
    alibi: str                  # Their story (may be false)

    # Psychology
    motivations: MotivationVector
    breaking_point: float       # Pressure threshold for confession
    current_pressure: float     # Accumulated interrogation pressure

    # State
    location: str
    schedule: dict[TimeOfDay, str]    # Where they are when
    is_alive: bool
    is_arrested: bool
    is_fleeing: bool

    # Memory
    memory: CharacterMemory

class CharacterSimulator:
    """Runs NPC behavior and responses."""

    def tick(self, dt: float) -> None: ...
    def apply_pressure(self, character: str, amount: float) -> PressureResult: ...
    def get_dialogue_response(self, character: str, topic: str) -> DialogueResponse: ...
    def would_lie_about(self, character: str, topic: str) -> bool: ...
    def update_schedule(self, time: TimeOfDay) -> None: ...
    def process_witness(self, character: str, event: WorldEvent) -> None: ...
```

### 4.3 Narrative Spine (`narrative/spine_generator.py`)

```python
@dataclass
class NarrativeSpine:
    """The hidden truth architecture of the story."""

    # Core Mystery
    case_type: CaseType                    # murder, theft, conspiracy, etc.
    true_culprit: str                      # Character ID
    true_motive: str                       # Why they did it
    true_method: str                       # How they did it

    # Key Story Beats
    inciting_incident: StoryBeat
    required_revelations: list[StoryBeat]  # Must be discovered to solve
    optional_revelations: list[StoryBeat]  # Enrich but not required

    # Deception Layer
    red_herrings: list[RedHerring]
    false_suspects: list[str]              # Deliberately suspicious NPCs
    planted_evidence: list[Evidence]

    # Resolution
    possible_endings: list[Ending]
    twist_probability: float               # Chance of late-game twist
    twist_type: Optional[TwistType]

    # Pacing
    act_structure: list[Act]
    tension_curve: list[float]             # Target tension by story %

@dataclass
class StoryBeat:
    """A significant narrative moment."""
    id: str
    description: str
    requirements: list[str]         # What must happen first
    reveals: list[str]              # What information this unlocks
    characters_involved: list[str]
    location: str
    triggers: list[Trigger]         # What activates this beat
    is_discovered: bool = False

class SpineGenerator:
    """Creates the narrative spine at game start."""

    def generate(self, scenario: ScenarioConfig, rng: SeededRNG) -> NarrativeSpine: ...
    def validate_solvability(self, spine: NarrativeSpine) -> bool: ...
    def generate_clue_chain(self, spine: NarrativeSpine) -> list[Clue]: ...
```

### 4.4 Environment System (`simulation/environment_sim.py`)

```python
class TimeOfDay(Enum):
    DAWN = "dawn"           # 5:00 - 7:00
    MORNING = "morning"     # 7:00 - 12:00
    AFTERNOON = "afternoon" # 12:00 - 17:00
    EVENING = "evening"     # 17:00 - 21:00
    NIGHT = "night"         # 21:00 - 1:00
    LATE_NIGHT = "late"     # 1:00 - 5:00

class Weather(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    FOG = "fog"
    STORM = "storm"
    SNOW = "snow"

@dataclass
class WeatherEffects:
    """Mechanical effects of weather conditions."""
    visibility_modifier: float      # Affects hotspot detection
    evidence_decay_rate: float      # Rain washes away clues
    npc_schedule_modifier: dict     # Changes where NPCs go
    violence_modifier: float        # Heat increases aggression
    particle_density: int           # Visual particles to render
    ambient_sound: str

@dataclass
class EnvironmentState:
    """Current state of the game world environment."""
    time_of_day: TimeOfDay
    weather: Weather
    temperature: float              # Celsius
    days_elapsed: int
    current_hour: int
    current_minute: int
    moon_phase: MoonPhase

class EnvironmentSimulator:
    """Simulates weather, time, and environmental effects."""

    state: EnvironmentState

    def tick(self, dt: float) -> None: ...
    def advance_time(self, minutes: int) -> list[TimeEvent]: ...
    def get_weather_effects(self) -> WeatherEffects: ...
    def is_outdoor_location(self, location: str) -> bool: ...
    def calculate_visibility(self, location: str) -> float: ...
    def should_evidence_decay(self, evidence: Evidence) -> bool: ...
    def get_ambient_description(self) -> str: ...
```

### 4.5 Moral Engine (`simulation/moral_engine.py`)

```python
class MoralAxis(Enum):
    PRAGMATIC = "pragmatic"         # Ends justify means
    CORRUPT = "corrupt"             # Self-serving
    COMPASSIONATE = "compassionate" # Helps others
    RUTHLESS = "ruthless"           # Disregards cost
    IDEALISTIC = "idealistic"       # Follows principles

@dataclass
class MoralProfile:
    """Player's accumulated moral standing."""
    axes: dict[MoralAxis, float]    # -1.0 to 1.0 for each
    key_choices: list[MoralChoice]
    reputation: dict[str, float]    # How factions view player

@dataclass
class MoralChoice:
    """A significant moral decision."""
    id: str
    description: str
    choice_made: str
    axis_impacts: dict[MoralAxis, float]
    timestamp: float
    witnesses: list[str]

class MoralEngine:
    """Tracks moral consequences and their effects."""

    profile: MoralProfile

    def record_choice(self, choice: MoralChoice) -> None: ...
    def get_dominant_axis(self) -> MoralAxis: ...
    def calculate_npc_reaction(self, npc: str, action: str) -> float: ...
    def get_ending_modifiers(self) -> dict[str, float]: ...
    def affects_dialogue(self, npc: str) -> DialogueModifier: ...
    def get_narration_flavor(self) -> str: ...
```

---

## 5. APIs & Interfaces

### 5.1 Scene Manager API

```python
class SceneManager:
    """Coordinates scene transitions and state."""

    current_scene: Scene
    scene_stack: list[Scene]        # For overlays/menus

    def load_scene(self, scene_id: str) -> None: ...
    def push_scene(self, scene: Scene) -> None: ...      # Overlay
    def pop_scene(self) -> Scene: ...
    def transition_to(self, scene_id: str, transition: Transition) -> None: ...
    def get_available_hotspots(self) -> list[Hotspot]: ...
    def get_visible_characters(self) -> list[Character]: ...
    def get_ambient_state(self) -> AmbientState: ...

@dataclass
class Scene:
    """A game location/screen."""
    id: str
    name: str
    description: str
    ascii_template: str
    hotspots: list[Hotspot]
    ambient_particles: list[ParticleConfig]
    connected_scenes: dict[str, str]    # direction -> scene_id
    lighting: LightingConfig
    is_interior: bool
```

### 5.2 Dialogue API

```python
@dataclass
class DialogueNode:
    """A single exchange in dialogue."""
    id: str
    speaker: str
    text: str
    conditions: list[Condition]         # When this appears
    responses: list[DialogueResponse]
    effects: list[Effect]               # What happens after

@dataclass
class DialogueResponse:
    """A player response option."""
    id: str
    text: str
    display_text: str                   # What player sees (may differ)
    conditions: list[Condition]
    next_node: str
    effects: list[Effect]
    moral_impact: Optional[MoralChoice]

class DialogueEngine:
    """Manages conversations."""

    active_dialogue: Optional[Dialogue]

    def start_dialogue(self, npc: str, topic: Optional[str] = None) -> Dialogue: ...
    def get_available_topics(self, npc: str) -> list[str]: ...
    def select_response(self, response_id: str) -> DialogueNode: ...
    def end_dialogue(self) -> None: ...

    # Generation
    def generate_line(self, npc: str, context: DialogueContext) -> str: ...
    def apply_npc_personality(self, text: str, npc: Character) -> str: ...
    def apply_relationship_tone(self, text: str, relationship: Relationship) -> str: ...
```

### 5.3 Action API

```python
class ActionType(Enum):
    LOOK = "look"
    EXAMINE = "examine"
    TALK = "talk"
    TAKE = "take"
    USE = "use"
    COMBINE = "combine"
    GO = "go"
    WAIT = "wait"
    ACCUSE = "accuse"
    THREATEN = "threaten"
    BRIBE = "bribe"

@dataclass
class Action:
    """A player action."""
    type: ActionType
    target: Optional[str]
    secondary_target: Optional[str]     # For COMBINE, USE...ON
    raw_input: str

@dataclass
class ActionResult:
    """Outcome of an action."""
    success: bool
    message: str
    events_triggered: list[GameEvent]
    state_changes: list[StateChange]
    time_cost: int                      # Minutes elapsed

class ActionHandler:
    """Processes player actions."""

    def execute(self, action: Action) -> ActionResult: ...
    def get_available_actions(self, target: str) -> list[ActionType]: ...
    def validate_action(self, action: Action) -> tuple[bool, str]: ...
```

---

## 6. Rendering System

### 6.1 Renderer Architecture

```python
class RenderLayer(Enum):
    BACKGROUND = 0          # Sky, distant elements
    SCENERY = 1             # Buildings, terrain
    OBJECTS = 2             # Interactable items
    CHARACTERS = 3          # NPCs
    PARTICLES = 4           # Weather, effects
    UI = 5                  # Hotspots, text
    OVERLAY = 6             # Menus, dialogue

@dataclass
class RenderBuffer:
    """A single layer's render output."""
    width: int
    height: int
    chars: list[list[str]]
    colors: list[list[str]]         # ANSI color codes

class Renderer:
    """Main ASCII render engine."""

    screen_width: int = 80
    screen_height: int = 24
    layers: dict[RenderLayer, RenderBuffer]

    def clear(self) -> None: ...
    def draw_to_layer(self, layer: RenderLayer, x: int, y: int,
                      content: str, color: str = None) -> None: ...
    def draw_box(self, layer: RenderLayer, x: int, y: int,
                 w: int, h: int, style: BoxStyle) -> None: ...
    def composite(self) -> str: ...     # Merge all layers
    def present(self) -> None: ...      # Output to terminal
```

### 6.2 ASCII Art Specification

```python
@dataclass
class ASCIISprite:
    """A renderable ASCII art piece."""
    id: str
    frames: list[list[str]]         # Animation frames
    width: int
    height: int
    anchor_x: int                   # Origin point
    anchor_y: int
    color_map: dict[str, str]       # char -> ANSI color

# Character set guidelines
CHARSET = {
    "solid_blocks":     "█▓▒░",
    "box_drawing":      "─│┌┐└┘├┤┬┴┼",
    "double_box":       "═║╔╗╚╝╠╣╦╩╬",
    "shading":          "·:;+*#@",
    "weather":          ".:·°'`",
    "special":          "◆◇○●□■△▽",
}

# Color palette (ANSI 256)
PALETTE = {
    "noir_shadow":      "\033[38;5;232m",
    "noir_highlight":   "\033[38;5;255m",
    "blood_red":        "\033[38;5;124m",
    "neon_blue":        "\033[38;5;39m",
    "amber":            "\033[38;5;214m",
    "fog_grey":         "\033[38;5;245m",
    "night_blue":       "\033[38;5;17m",
}
```

### 6.3 Particle System

```python
class ParticleType(Enum):
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    SNOW = "snow"
    FOG = "fog"
    SMOKE = "smoke"
    SPARKS = "sparks"
    LEAVES = "leaves"
    SHADOW = "shadow"

@dataclass
class Particle:
    """A single particle."""
    x: float
    y: float
    vx: float
    vy: float
    char: str
    color: str
    lifetime: float
    age: float = 0.0

@dataclass
class ParticleEmitter:
    """Spawns and manages particles."""
    particle_type: ParticleType
    spawn_rate: float           # Particles per second
    spawn_area: tuple[int, int, int, int]   # x, y, w, h
    config: ParticleConfig

class ParticleSystem:
    """Manages all particle effects."""

    emitters: list[ParticleEmitter]
    particles: list[Particle]
    max_particles: int = 500

    def add_emitter(self, emitter: ParticleEmitter) -> None: ...
    def remove_emitter(self, emitter_id: str) -> None: ...
    def tick(self, dt: float) -> None: ...
    def render(self, buffer: RenderBuffer) -> None: ...
```

### 6.4 UI Components

```python
class UIComponent:
    """Base class for UI elements."""
    x: int
    y: int
    width: int
    height: int
    visible: bool

    def render(self, buffer: RenderBuffer) -> None: ...
    def handle_input(self, key: str) -> bool: ...

class HotspotDisplay(UIComponent):
    """Shows numbered interaction points."""
    hotspots: list[Hotspot]
    selected_index: int

class DialogueBox(UIComponent):
    """Displays dialogue text and options."""
    speaker: str
    text: str
    options: list[str]
    selected_option: int
    typewriter_pos: int         # For text animation

class StatusBar(UIComponent):
    """Shows game status info."""
    time_display: str
    weather_icon: str
    location_name: str

class InventoryPanel(UIComponent):
    """Shows player inventory."""
    items: list[Item]
    selected_item: int
    columns: int = 4
```

---

## 7. Input System

### 7.1 Command Parser

```python
@dataclass
class ParsedCommand:
    """Result of parsing player input."""
    action: ActionType
    target: Optional[str]
    modifiers: dict[str, str]
    raw: str
    confidence: float           # How sure we are about parsing

class CommandParser:
    """Natural-language-lite command parser."""

    # Vocabulary mappings
    action_synonyms: dict[str, ActionType] = {
        "look": ActionType.LOOK,
        "examine": ActionType.EXAMINE,
        "check": ActionType.EXAMINE,
        "inspect": ActionType.EXAMINE,
        "talk": ActionType.TALK,
        "speak": ActionType.TALK,
        "ask": ActionType.TALK,
        "take": ActionType.TAKE,
        "grab": ActionType.TAKE,
        "pick": ActionType.TAKE,
        # ... etc
    }

    def parse(self, input_str: str) -> ParsedCommand: ...
    def suggest_correction(self, input_str: str) -> Optional[str]: ...
    def get_context_actions(self, scene: Scene) -> list[str]: ...
```

### 7.2 Hotspot System

```python
@dataclass
class Hotspot:
    """An interactable point in a scene."""
    id: str
    number: int                 # Display number (1-9)
    name: str
    description: str
    x: int
    y: int
    width: int
    height: int
    actions: list[ActionType]   # Available actions
    visibility: float           # 0.0 to 1.0 (weather affects)
    is_character: bool
    requires_item: Optional[str]
    one_time: bool              # Disappears after interaction

class HotspotManager:
    """Manages scene hotspots."""

    hotspots: list[Hotspot]

    def get_visible_hotspots(self, visibility_mod: float) -> list[Hotspot]: ...
    def select_by_number(self, num: int) -> Optional[Hotspot]: ...
    def select_by_name(self, name: str) -> Optional[Hotspot]: ...
    def get_actions_for(self, hotspot: Hotspot) -> list[ActionType]: ...
    def update_visibility(self, weather: Weather) -> None: ...
```

### 7.3 Input Modes

```python
class InputMode(Enum):
    EXPLORATION = "exploration"     # Moving, looking
    DIALOGUE = "dialogue"           # Conversation choices
    INVENTORY = "inventory"         # Managing items
    MENU = "menu"                   # Game menus
    CUTSCENE = "cutscene"          # Non-interactive

class InputHandler:
    """Handles all player input."""

    current_mode: InputMode
    key_bindings: dict[str, Callable]

    def get_input(self) -> str: ...
    def process(self, key: str) -> Optional[Action]: ...
    def set_mode(self, mode: InputMode) -> None: ...

    # Default bindings
    DEFAULT_BINDINGS = {
        "1-9":      "select_hotspot",
        "l/L":      "look",
        "t/T":      "talk",
        "e/E":      "examine",
        "i/I":      "inventory",
        "arrow":    "navigate",
        "enter":    "confirm",
        "esc":      "cancel/menu",
        "space":    "advance_dialogue",
        "?":        "help",
    }
```

---

## 8. Save/Load System

### 8.1 Save Format

```python
@dataclass
class SaveData:
    """Complete game state for serialization."""

    # Metadata
    version: str
    timestamp: str
    playtime_seconds: int
    save_name: str

    # Core state
    seed: int
    scenario_id: str

    # Memory snapshots
    world_memory: dict
    character_memories: dict[str, dict]
    player_memory: dict

    # Narrative state
    narrative_spine: dict
    story_progress: dict
    discovered_clues: list[str]
    triggered_beats: list[str]

    # Simulation state
    characters: dict[str, dict]
    environment: dict
    moral_profile: dict

    # Scene state
    current_scene: str
    scene_states: dict[str, dict]
    inventory: list[dict]

    # RNG state
    rng_state: dict

class SaveManager:
    """Handles save/load operations."""

    save_directory: Path

    def save(self, slot: int, name: str = "") -> bool: ...
    def load(self, slot: int) -> SaveData: ...
    def list_saves(self) -> list[SaveMetadata]: ...
    def delete_save(self, slot: int) -> bool: ...
    def export_seed(self) -> str: ...           # Share seed for replay
    def import_seed(self, seed_str: str) -> int: ...

    # Auto-save
    def auto_save(self) -> None: ...
    def has_auto_save(self) -> bool: ...
    def load_auto_save(self) -> SaveData: ...
```

### 8.2 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ShadowEngine Save File",
  "type": "object",
  "required": ["version", "seed", "scenario_id", "memories", "narrative", "simulation"],
  "properties": {
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "timestamp": { "type": "string", "format": "date-time" },
    "seed": { "type": "integer" },
    "scenario_id": { "type": "string" },
    "memories": {
      "type": "object",
      "properties": {
        "world": { "$ref": "#/definitions/worldMemory" },
        "characters": { "type": "object" },
        "player": { "$ref": "#/definitions/playerMemory" }
      }
    },
    "narrative": {
      "type": "object",
      "properties": {
        "spine": { "$ref": "#/definitions/narrativeSpine" },
        "progress": { "type": "number", "minimum": 0, "maximum": 1 },
        "current_act": { "type": "integer" }
      }
    },
    "simulation": {
      "type": "object",
      "properties": {
        "characters": { "type": "object" },
        "environment": { "$ref": "#/definitions/environment" },
        "morality": { "$ref": "#/definitions/moralProfile" }
      }
    }
  }
}
```

---

## 9. Configuration

### 9.1 Engine Configuration

```python
@dataclass
class EngineConfig:
    """Core engine settings."""

    # Display
    screen_width: int = 80
    screen_height: int = 24
    use_color: bool = True
    color_depth: int = 256          # 16 or 256

    # Performance
    target_fps: int = 30
    max_particles: int = 500
    enable_animations: bool = True

    # Gameplay
    auto_save_interval: int = 300   # Seconds
    text_speed: float = 1.0         # Typewriter speed
    difficulty: str = "normal"

    # Debug
    debug_mode: bool = False
    show_fps: bool = False
    log_level: str = "INFO"

# config.json
{
    "engine": {
        "screen_width": 80,
        "screen_height": 24,
        "use_color": true,
        "target_fps": 30
    },
    "gameplay": {
        "text_speed": 1.0,
        "auto_save": true,
        "difficulty": "normal"
    },
    "accessibility": {
        "high_contrast": false,
        "screen_reader_mode": false
    }
}
```

### 9.2 Scenario Configuration

```python
@dataclass
class ScenarioConfig:
    """Defines a game scenario/story setting."""

    id: str
    name: str
    description: str
    genre: str
    era: str

    # Content
    locations_file: str
    characters_file: str
    archetypes_file: str
    dialogue_templates: str

    # Narrative rules
    case_types: list[str]
    moral_axes: list[str]
    twist_types: list[str]
    act_count: int

    # Environment rules
    weather_weights: dict[str, float]
    time_scale: float               # Real seconds per game minute

    # Starting conditions
    start_location: str
    start_time: str
    initial_inventory: list[str]

# scenarios/noir_york/config.json
{
    "id": "noir_york",
    "name": "Noir York Shadows",
    "genre": "noir",
    "era": "1940s",
    "case_types": ["murder", "theft", "conspiracy", "missing_person"],
    "locations_file": "locations.json",
    "characters_file": "characters.json",
    "start_location": "office",
    "weather_weights": {
        "rain": 0.4,
        "fog": 0.25,
        "clear": 0.2,
        "cloudy": 0.15
    }
}
```

---

## 10. Implementation Phases

### Phase 1: Foundation (Core Systems)

```
Priority: CRITICAL
Duration: First milestone

Deliverables:
├── core/
│   ├── game_loop.py         ✓ Basic game loop
│   ├── rng.py               ✓ Seeded RNG
│   └── events.py            ✓ Event bus
│
├── memory/
│   ├── memory_bank.py       ✓ Memory coordinator
│   ├── world_memory.py      ✓ Event recording
│   └── player_memory.py     ✓ Player state
│
├── render/
│   ├── renderer.py          ✓ Basic ASCII output
│   └── ui.py                ✓ Text display
│
├── input/
│   └── parser.py            ✓ Basic command parsing
│
└── persistence/
    └── save_manager.py      ✓ JSON save/load

Success Criteria:
- Player can navigate between 3 test locations
- Commands are parsed and executed
- Game state persists across save/load
- Events are recorded in memory
```

### Phase 2: Narrative Core

```
Priority: HIGH
Duration: Second milestone

Deliverables:
├── narrative/
│   ├── spine_generator.py   ✓ Generate mystery structure
│   ├── story_state.py       ✓ Track progress
│   └── dialogue.py          ✓ Basic dialogue trees
│
├── simulation/
│   └── character_sim.py     ✓ NPC behavior basics
│
└── memory/
    └── character_memory.py  ✓ NPC knowledge tracking

Success Criteria:
- One complete playable mystery from start to end
- NPCs respond differently based on knowledge
- Multiple endings achievable
- Clue chain is solvable
```

### Phase 3: Atmosphere Engine

```
Priority: MEDIUM
Duration: Third milestone

Deliverables:
├── simulation/
│   ├── environment_sim.py   ✓ Weather/time system
│   └── moral_engine.py      ✓ Consequence tracking
│
├── render/
│   ├── scene.py             ✓ Dynamic scene composition
│   ├── particles.py         ✓ Weather effects
│   └── assets/              ✓ ASCII art library

Success Criteria:
- Weather affects gameplay mechanically
- Time passes and affects NPC schedules
- Moral choices have visible consequences
- Atmospheric particle effects working
```

### Phase 4: Polish & Extensibility

```
Priority: LOWER
Duration: Final milestone

Deliverables:
├── Full scenario: Noir York Shadows
├── Modding documentation
├── Additional endings
├── Performance optimization
├── Accessibility options
└── Optional: LLM integration hooks

Success Criteria:
- 4+ hour playable experience
- 5+ distinct endings
- Modding system documented
- Runs smoothly on minimum spec
```

---

## Appendix A: Terminal Compatibility

```python
# Minimum terminal requirements
TERMINAL_REQUIREMENTS = {
    "min_width": 80,
    "min_height": 24,
    "encoding": "utf-8",
    "color_support": "optional",  # Graceful fallback
}

# Tested terminals
TESTED_TERMINALS = [
    "Windows Terminal",
    "Windows CMD (with UTF-8)",
    "macOS Terminal.app",
    "iTerm2",
    "GNOME Terminal",
    "Konsole",
    "xterm",
    "Alacritty",
    "Kitty",
]

# Fallback for limited terminals
def get_charset(terminal_capability: str) -> dict:
    if terminal_capability == "full_unicode":
        return UNICODE_CHARSET
    elif terminal_capability == "extended_ascii":
        return EXTENDED_ASCII_CHARSET
    else:
        return BASIC_ASCII_CHARSET
```

---

## Appendix B: Error Handling

```python
class ShadowEngineError(Exception):
    """Base exception for engine errors."""
    pass

class NarrativeError(ShadowEngineError):
    """Error in narrative generation or progression."""
    pass

class MemoryError(ShadowEngineError):
    """Error in memory system."""
    pass

class RenderError(ShadowEngineError):
    """Error in rendering system."""
    pass

class SaveLoadError(ShadowEngineError):
    """Error in save/load system."""
    pass

# Error recovery strategies
ERROR_RECOVERY = {
    NarrativeError: "reload_last_checkpoint",
    MemoryError: "reconstruct_from_events",
    RenderError: "fallback_to_basic_render",
    SaveLoadError: "prompt_user_retry",
}
```

---

## Appendix C: Performance Targets

```
Metric                  Target          Maximum
─────────────────────────────────────────────────
Frame time              33ms            50ms
Input latency           <16ms           <50ms
Scene transition        <100ms          <500ms
Save operation          <500ms          <2000ms
Load operation          <1000ms         <3000ms
Memory usage            <100MB          <200MB
Particle count          500             1000
Active NPCs             20              50
```

---

*End of Specification*
