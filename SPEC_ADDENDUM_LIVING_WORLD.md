# ShadowEngine: Living World Addendum

> **Version**: 2.0.0
> **Status**: Architectural Extension
> **Dependency**: Requires SPEC_SHEET.md as foundation
> **Core Change**: Scene-based → Continuous Spatial Simulation + LLM Interpretation

---

## Executive Summary

This addendum transforms ShadowEngine from a **procedural narrative engine** into an **interpretable ASCII reality engine** where:

- The world exists as continuous space, not discrete scenes
- Players express **intent**, not commands
- An LLM **interprets meaning**, not outcomes
- Systems **decide consequences**, not prose
- Voice input enables **real-time panic reactions**
- No interaction ever fails—everything has a response

---

## Table of Contents

1. [Architecture Shift](#1-architecture-shift)
2. [Spatial World System](#2-spatial-world-system)
3. [LLM Interpretation Layer](#3-llm-interpretation-layer)
4. [Affordance System](#4-affordance-system)
5. [Continuous Time Engine](#5-continuous-time-engine)
6. [Voice Input (STT) System](#6-voice-input-stt-system)
7. [Graded Danger System](#7-graded-danger-system)
8. [World Memory Extension](#8-world-memory-extension)
9. [Procedural Generation Pipeline](#9-procedural-generation-pipeline)
10. [Integration Architecture](#10-integration-architecture)

---

## 1. Architecture Shift

### 1.1 Before vs After

```
BEFORE (Scene-Based):
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Office  │───▶│  Alley  │───▶│  Bar    │
└─────────┘    └─────────┘    └─────────┘
     │              │              │
     ▼              ▼              ▼
 [scripted]    [scripted]    [scripted]

AFTER (Continuous Spatial):
┌────────────────────────────────────────┐
│  ░░░░░▓▓▓▓░░░░░███████░░░░░░░░░░░░░░░  │
│  ░░░░░▓▓▓▓░░░░░███████░░░░░≈≈≈≈≈░░░░░  │
│  ░░░@░▓▓▓▓░░░░░███████░░░░≈≈≈█≈≈░░░░░  │ @ = player
│  ░░░░░░░░░░░░░░░░░░░░░░░░░≈≈≈≈≈░░░░░░  │ ≈ = water
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ █ = structure
└────────────────────────────────────────┘
     │
     ▼
 [emergent from simulation + LLM interpretation]
```

### 1.2 New Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                     LIVING WORLD PIPELINE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │    INPUT     │    │     LLM      │    │   INTENT     │           │
│  │  (text/STT)  │───▶│ INTERPRETER  │───▶│   RESOLVER   │           │
│  └──────────────┘    └──────────────┘    └──────────────┘           │
│                                                 │                    │
│                                                 ▼                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │    WORLD     │◀───│  AFFORDANCE  │◀───│   PHYSICS    │           │
│  │    STATE     │    │    ENGINE    │    │   RESOLVER   │           │
│  └──────────────┘    └──────────────┘    └──────────────┘           │
│         │                                       │                    │
│         ▼                                       ▼                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │   SPATIAL    │───▶│   RENDERER   │◀───│  CONTINUOUS  │           │
│  │  SIMULATION  │    │   (ASCII)    │    │    TIME      │           │
│  └──────────────┘    └──────────────┘    └──────────────┘           │
│                             │                                        │
│                             ▼                                        │
│                      ┌──────────────┐                                │
│                      │   TERMINAL   │                                │
│                      └──────────────┘                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Spatial World System

### 2.1 World Representation

The world is a **continuous tile-based simulation**, not discrete rooms.

```python
@dataclass
class Tile:
    """Atomic unit of world space."""
    x: int
    y: int
    z: int                          # Elevation/layers

    # Physical properties
    terrain: TerrainType
    material: Material
    elevation: float
    temperature: float
    wetness: float

    # Simulation properties
    traversable: bool
    traversal_cost: float           # Movement speed modifier
    visibility: float               # 0.0 = opaque, 1.0 = clear
    sound_transmission: float       # How sound travels through

    # Danger
    danger_level: float             # 0.0 to 1.0
    danger_type: Optional[DangerType]

    # Contents
    entities: list[EntityID]
    items: list[ItemID]
    effects: list[EffectID]         # Fire, water, gas, etc.

    # Generation state
    generated: bool                 # Has LLM filled in details?
    generation_seed: int
    affordances: list[Affordance]   # What can be done here


class TerrainType(Enum):
    VOID = "void"                   # Nothing/ungenerated
    GROUND = "ground"
    WATER_SHALLOW = "water_shallow"
    WATER_DEEP = "water_deep"
    WALL = "wall"
    DOOR = "door"
    WINDOW = "window"
    STAIRS_UP = "stairs_up"
    STAIRS_DOWN = "stairs_down"
    LEDGE = "ledge"
    ROOF = "roof"
    VEGETATION = "vegetation"
    DEBRIS = "debris"


class Material(Enum):
    STONE = "stone"
    WOOD = "wood"
    METAL = "metal"
    GLASS = "glass"
    WATER = "water"
    FABRIC = "fabric"
    EARTH = "earth"
    CONCRETE = "concrete"
```

### 2.2 Chunk System

World loads in chunks around the player to enable infinite exploration.

```python
CHUNK_SIZE = 32  # tiles per chunk side

@dataclass
class Chunk:
    """A loadable section of the world."""
    chunk_x: int
    chunk_y: int
    tiles: list[list[Tile]]         # CHUNK_SIZE x CHUNK_SIZE

    # Generation
    biome: BiomeType
    district: str                   # "docks", "downtown", "slums"
    generation_template: str
    is_generated: bool

    # Persistence
    is_modified: bool               # Player changed something
    last_accessed: float


class WorldGrid:
    """Manages the infinite world space."""

    loaded_chunks: dict[tuple[int, int], Chunk]
    generation_queue: deque[tuple[int, int]]
    active_radius: int = 3          # Chunks loaded around player

    def get_tile(self, x: int, y: int) -> Tile: ...
    def set_tile(self, x: int, y: int, tile: Tile) -> None: ...
    def load_chunk(self, cx: int, cy: int) -> Chunk: ...
    def unload_chunk(self, cx: int, cy: int) -> None: ...
    def get_tiles_in_radius(self, x: int, y: int, r: int) -> list[Tile]: ...
    def get_visible_tiles(self, x: int, y: int, fov: int) -> list[Tile]: ...
    def raycast(self, x1: int, y1: int, x2: int, y2: int) -> RaycastResult: ...
```

### 2.3 Viewport Rendering

Only render what the player can see.

```python
@dataclass
class Viewport:
    """What the player currently sees."""
    center_x: int
    center_y: int
    width: int = 80
    height: int = 24

    # Field of view
    fov_radius: int = 15
    fov_angle: float = 360          # Degrees (can be limited)

    # Visibility calculation
    lit_tiles: set[tuple[int, int]]
    remembered_tiles: dict[tuple[int, int], Tile]  # Fog of war


class SpatialRenderer:
    """Renders world state to ASCII."""

    viewport: Viewport
    tile_chars: dict[TerrainType, str]
    entity_chars: dict[EntityType, str]

    # Rendering layers (back to front)
    LAYERS = [
        "terrain",
        "items",
        "effects",
        "entities",
        "player",
        "ui_overlay"
    ]

    def render_frame(self, world: WorldGrid, player: Player) -> str: ...
    def get_tile_char(self, tile: Tile) -> tuple[str, str]: ...  # char, color
    def apply_lighting(self, char: str, light_level: float) -> str: ...
    def render_fog_of_war(self, tile: Tile, remembered: bool) -> str: ...
```

### 2.4 ASCII Character Mapping

```python
TERRAIN_CHARS = {
    TerrainType.GROUND: ".",
    TerrainType.WATER_SHALLOW: "~",
    TerrainType.WATER_DEEP: "≈",
    TerrainType.WALL: "█",
    TerrainType.DOOR: "▐",
    TerrainType.WINDOW: "▒",
    TerrainType.STAIRS_UP: "<",
    TerrainType.STAIRS_DOWN: ">",
    TerrainType.LEDGE: "=",
    TerrainType.VEGETATION: "♣",
    TerrainType.DEBRIS: "%",
}

ENTITY_CHARS = {
    "player": "@",
    "npc_friendly": "☺",
    "npc_neutral": "○",
    "npc_hostile": "☻",
    "corpse": "&",
    "animal": "a",
}

EFFECT_CHARS = {
    "fire": "^",
    "smoke": "░",
    "blood": "·",
    "water_flow": "~",
    "electricity": "*",
}

# Dynamic features (rendered from world state)
FEATURE_PATTERNS = {
    "waterfall": [
        "███",
        "█~█",
        "~≈~",
        "≈≈≈",
    ],
    "door_open": ".",
    "door_closed": "+",
    "window_broken": "'",
}
```

---

## 3. LLM Interpretation Layer

### 3.1 Core Principle

> **The LLM never decides success/failure. It translates intent.**

```
Player Input: "go behind the waterfall"
                    │
                    ▼
┌─────────────────────────────────────────────┐
│           LLM INTERPRETATION                │
│                                             │
│  Input: "go behind the waterfall"           │
│                                             │
│  Extracted:                                 │
│    - Action Type: MOVEMENT                  │
│    - Target: waterfall (entity_id: wf_042)  │
│    - Modifier: behind/concealment           │
│    - Urgency: low                           │
│                                             │
│  NOT Decided:                               │
│    - Success/failure                        │
│    - What's behind it                       │
│    - Whether player survives                │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│           SYSTEMS RESOLUTION                │
│                                             │
│  Physics: Can player reach it? YES          │
│  Space: Is there space behind? GENERATE     │
│  Danger: Risk assessment? 0.6 (slippery)    │
│  Time: How long? 4 seconds                  │
│                                             │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│           LLM NARRATION                     │
│                                             │
│  "You press through the curtain of water.   │
│   The roar swallows everything. Behind it,  │
│   slick rocks and darkness. One wrong step  │
│   and you're done."                         │
│                                             │
└─────────────────────────────────────────────┘
```

### 3.2 Intent Classification

```python
class IntentType(Enum):
    # Movement
    MOVE = "move"                   # Go somewhere
    FLEE = "flee"                   # Escape danger (URGENT)
    PURSUE = "pursue"              # Chase something
    HIDE = "hide"                   # Seek concealment
    CLIMB = "climb"                 # Vertical movement

    # Interaction
    EXAMINE = "examine"             # Learn about something
    TAKE = "take"                   # Acquire item
    USE = "use"                     # Use item/object
    MANIPULATE = "manipulate"       # Change object state

    # Social
    COMMUNICATE = "communicate"     # Talk/signal
    THREATEN = "threaten"           # Intimidate
    DECEIVE = "deceive"             # Lie/misdirect
    PERSUADE = "persuade"           # Convince

    # Combat
    ATTACK = "attack"               # Harm target
    DEFEND = "defend"               # Protect self
    DISARM = "disarm"               # Remove threat

    # Meta
    WAIT = "wait"                   # Pass time
    OBSERVE = "observe"             # Passive awareness


@dataclass
class ParsedIntent:
    """LLM's interpretation of player input."""

    raw_input: str
    intent_type: IntentType

    # Target resolution
    primary_target: Optional[EntityID]
    secondary_target: Optional[EntityID]
    target_location: Optional[tuple[int, int]]

    # Modifiers
    modifiers: dict[str, Any]       # "behind", "quietly", "quickly"

    # Urgency (affects time system)
    urgency: float                  # 0.0 = leisurely, 1.0 = panic

    # Confidence
    confidence: float               # How sure LLM is about interpretation
    alternatives: list['ParsedIntent']  # Other possible interpretations

    # For ambiguity resolution
    needs_clarification: bool
    clarification_prompt: Optional[str]
```

### 3.3 LLM Integration

```python
class LLMInterpreter:
    """Bridges player input to game systems via LLM."""

    def __init__(self, config: LLMConfig):
        self.model = config.model           # "claude-3-sonnet", "local-llama", etc.
        self.context_window = config.context_window
        self.temperature = config.temperature

    async def interpret_input(
        self,
        raw_input: str,
        world_context: WorldContext,
        player_state: PlayerState,
    ) -> ParsedIntent:
        """Convert raw input to structured intent."""

        prompt = self._build_interpretation_prompt(
            raw_input, world_context, player_state
        )

        response = await self._query_llm(prompt)
        return self._parse_intent_response(response)

    async def generate_narration(
        self,
        action_result: ActionResult,
        world_context: WorldContext,
        player_state: PlayerState,
    ) -> str:
        """Generate narrative description of what happened."""

        prompt = self._build_narration_prompt(
            action_result, world_context, player_state
        )

        return await self._query_llm(prompt)

    async def expand_world(
        self,
        location: tuple[int, int],
        trigger: str,                       # What prompted expansion
        constraints: GenerationConstraints,
    ) -> WorldExpansion:
        """Generate new world content when player explores unknown."""

        prompt = self._build_expansion_prompt(
            location, trigger, constraints
        )

        response = await self._query_llm(prompt)
        return self._parse_expansion_response(response)


@dataclass
class WorldContext:
    """What the LLM needs to know about current state."""

    # Visible environment
    visible_tiles: list[TileSummary]
    visible_entities: list[EntitySummary]
    visible_items: list[ItemSummary]

    # Recent events
    recent_events: list[str]        # Last 10 things that happened

    # Player state
    player_location: tuple[int, int]
    player_facing: Direction
    player_inventory: list[str]
    player_status: list[str]        # "injured", "wet", "afraid"

    # Ambient
    time_of_day: str
    weather: str
    ambient_sounds: list[str]
    ambient_smells: list[str]


@dataclass
class GenerationConstraints:
    """Rules for LLM world generation."""

    # Must respect
    narrative_spine: NarrativeSpine     # Can't contradict core mystery
    established_facts: list[str]        # Already decided truths

    # Style
    genre: str
    era: str
    tone: str

    # Limits
    max_new_entities: int = 3
    max_new_items: int = 5
    danger_range: tuple[float, float] = (0.0, 0.8)

    # Forbidden
    forbidden_elements: list[str]       # "no magic", "no sci-fi", etc.
```

### 3.4 LLM Prompt Templates

```python
INTERPRETATION_PROMPT = """
You are the interpreter for an ASCII noir game. Your job is to understand
what the player WANTS to do, not to decide what happens.

CURRENT SCENE:
{world_context}

PLAYER STATUS:
{player_state}

PLAYER INPUT: "{raw_input}"

Analyze this input and return a JSON object:
{{
    "intent_type": "MOVE|EXAMINE|TAKE|USE|COMMUNICATE|ATTACK|FLEE|HIDE|...",
    "primary_target": "entity/item/location being acted on, or null",
    "target_location": [x, y] or null,
    "modifiers": {{"quietly": true, "behind": true, ...}},
    "urgency": 0.0-1.0,
    "confidence": 0.0-1.0,
    "needs_clarification": true/false,
    "clarification_prompt": "Did you mean X or Y?" or null
}}

RULES:
- NEVER decide success or failure
- NEVER invent objects not in the scene
- If ambiguous, set needs_clarification=true
- Urgency 1.0 = panic/emergency (for voice commands like "RUN!")
"""

NARRATION_PROMPT = """
You are the narrator of a 1940s noir story. Describe what just happened
in 1-3 sentences. Be atmospheric but concise.

WHAT HAPPENED:
{action_result}

PLAYER'S MORAL PROFILE: {moral_profile}
PLAYER'S INJURIES: {injuries}
TIME: {time_of_day}
WEATHER: {weather}

Write in second person, present tense. Match the mood to the player's
moral alignment:
- Pragmatic: matter-of-fact
- Corrupt: cynical
- Compassionate: empathetic
- Ruthless: cold
- Idealistic: dramatic

Keep it punchy. This is noir.
"""

EXPANSION_PROMPT = """
The player has explored somewhere new that needs to be generated.

LOCATION: {location}
TRIGGER: {trigger}
SURROUNDING CONTEXT: {context}
NARRATIVE CONSTRAINTS: {constraints}

Generate what exists here as JSON:
{{
    "description": "Brief description",
    "terrain_modifications": [...],
    "new_entities": [...],
    "new_items": [...],
    "hazards": [...],
    "affordances": [...],
    "connects_to": [...],
    "secrets": [...]  // Things not immediately visible
}}

CRITICAL RULES:
- Must fit the noir 1940s setting
- Cannot contradict established facts: {established_facts}
- If this relates to the mystery, respect the spine: {narrative_spine}
- Danger level should be in range {danger_range}
- Be plausible. A waterfall might hide rocks, a cave, or nothing.
  It shouldn't hide a dragon.
"""
```

---

## 4. Affordance System

### 4.1 Core Concept

> **Objects don't have "use" commands. They have affordances—what they permit.**

```python
class AffordanceType(Enum):
    # Physical
    SUPPORT = "support"             # Can stand on
    CONTAIN = "contain"             # Can hold items
    BLOCK = "block"                 # Prevents passage
    CONCEAL = "conceal"             # Can hide behind/in
    CONNECT = "connect"             # Links two spaces

    # Manipulation
    OPEN = "open"                   # Can be opened
    CLOSE = "close"                 # Can be closed
    BREAK = "break"                 # Can be destroyed
    MOVE = "move"                   # Can be relocated

    # Sensory
    ILLUMINATE = "illuminate"       # Produces light
    OBSCURE = "obscure"             # Blocks vision
    MUFFLE = "muffle"               # Blocks sound
    EMIT_SOUND = "emit_sound"       # Makes noise

    # Danger
    DAMAGE = "damage"               # Can hurt
    TRAP = "trap"                   # Can restrain
    POISON = "poison"               # Toxic
    DROWN = "drown"                 # Deep water
    FALL = "fall"                   # Height danger

    # Interaction
    COMMUNICATE = "communicate"     # Can be talked to
    TRADE = "trade"                 # Can exchange items
    INFORM = "inform"               # Has information


@dataclass
class Affordance:
    """A single thing an object permits."""

    type: AffordanceType

    # Conditions
    requires: list[str]             # What's needed to use this
    blocked_by: list[str]           # What prevents it

    # Costs
    time_cost: float                # Seconds
    noise_level: float              # 0.0 to 1.0
    energy_cost: float              # Stamina
    risk: float                     # Danger probability

    # Effects
    state_changes: dict[str, Any]   # What changes in the world
    creates: list[str]              # New entities/items
    destroys: list[str]             # Removed entities/items


class AffordanceEngine:
    """Resolves what players can do with objects."""

    def get_affordances(
        self,
        entity: Entity,
        context: WorldContext
    ) -> list[Affordance]:
        """Get all current affordances for an entity."""
        ...

    def can_use_affordance(
        self,
        affordance: Affordance,
        actor: Entity,
        context: WorldContext,
    ) -> tuple[bool, str]:          # Success, reason
        """Check if an affordance can be used."""
        ...

    def resolve_affordance(
        self,
        affordance: Affordance,
        actor: Entity,
        target: Entity,
        context: WorldContext,
    ) -> AffordanceResult:
        """Execute an affordance and return results."""
        ...

    def match_intent_to_affordances(
        self,
        intent: ParsedIntent,
        available: list[Affordance],
    ) -> list[Affordance]:
        """Find affordances that match player intent."""
        ...
```

### 4.2 Example: Waterfall Affordances

```python
waterfall_affordances = [
    Affordance(
        type=AffordanceType.CONCEAL,
        requires=["player_can_move"],
        blocked_by=["too_weak", "carrying_heavy"],
        time_cost=4.0,
        noise_level=0.0,            # Waterfall covers sound
        energy_cost=0.3,
        risk=0.4,                   # Slippery
        state_changes={"player_wet": True, "player_hidden": True},
    ),
    Affordance(
        type=AffordanceType.OBSCURE,
        requires=[],
        blocked_by=[],
        time_cost=0.0,
        noise_level=0.0,
        energy_cost=0.0,
        risk=0.0,
        state_changes={},           # Passive - always obscures
    ),
    Affordance(
        type=AffordanceType.MUFFLE,
        requires=[],
        blocked_by=[],
        time_cost=0.0,
        noise_level=0.0,
        energy_cost=0.0,
        risk=0.0,
        state_changes={},           # Passive - covers sounds
    ),
    Affordance(
        type=AffordanceType.DAMAGE,
        requires=["player_enters_water"],
        blocked_by=["player_strong"],
        time_cost=0.0,
        noise_level=0.0,
        energy_cost=0.0,
        risk=0.6,                   # Can knock player down
        state_changes={"damage_type": "impact", "damage_amount": 15},
    ),
]
```

### 4.3 No Failed Interactions

```python
class InteractionResolver:
    """Ensures every interaction has a meaningful response."""

    def resolve(
        self,
        intent: ParsedIntent,
        world: WorldGrid,
        llm: LLMInterpreter,
    ) -> InteractionResult:

        # Find target
        target = self._resolve_target(intent, world)

        if target is None:
            # LLM interprets what player might have meant
            return self._handle_no_target(intent, world, llm)

        # Get affordances
        affordances = self.affordance_engine.get_affordances(target, world)

        # Match intent to affordances
        matching = self.affordance_engine.match_intent_to_affordances(
            intent, affordances
        )

        if matching:
            # Execute the best match
            return self._execute_affordance(matching[0], intent, target)

        else:
            # No direct match - LLM finds creative interpretation
            return self._handle_no_affordance(intent, target, world, llm)

    def _handle_no_target(
        self,
        intent: ParsedIntent,
        world: WorldGrid,
        llm: LLMInterpreter,
    ) -> InteractionResult:
        """When target doesn't exist, find something meaningful."""

        # Ask LLM: What might player have meant?
        # Maybe "waterfall" refers to something nearby?
        # Generate a reason why it doesn't work, not a parser error

        # NEVER return "I don't understand"
        # Return "There's no waterfall here, just rain-slicked concrete"
        ...

    def _handle_no_affordance(
        self,
        intent: ParsedIntent,
        target: Entity,
        world: WorldGrid,
        llm: LLMInterpreter,
    ) -> InteractionResult:
        """When action doesn't match, explain why naturally."""

        # NEVER return "You can't do that"
        # Return "The wall is solid concrete. No way through."
        ...
```

---

## 5. Continuous Time Engine

### 5.1 Real-Time World Simulation

```python
class TimeScale(Enum):
    PAUSED = 0
    SLOW = 0.25         # Dialogue, examination
    NORMAL = 1.0        # Exploration
    FAST = 2.0          # Waiting
    REALTIME = -1       # 1:1 with real time (danger!)


class ContinuousTimeEngine:
    """World keeps moving. Hesitation has cost."""

    game_time: float                # Seconds since game start
    time_scale: TimeScale

    # Real-time tracking
    last_tick: float
    accumulated_time: float

    # Scheduled events
    event_queue: PriorityQueue[ScheduledEvent]

    # Active threats (force real-time)
    active_threats: list[ThreatID]

    def tick(self, real_dt: float) -> list[TimeEvent]:
        """Advance world time and return events that occurred."""

        game_dt = real_dt * self.time_scale.value
        self.game_time += game_dt

        events = []

        # Process scheduled events
        while self.event_queue and self.event_queue.peek().time <= self.game_time:
            event = self.event_queue.pop()
            events.append(self._process_event(event))

        # Tick all active simulations
        self._tick_npcs(game_dt)
        self._tick_environment(game_dt)
        self._tick_threats(game_dt)

        return events

    def enter_danger(self, threat: Threat) -> None:
        """Switch to real-time when danger appears."""
        self.active_threats.append(threat.id)
        if len(self.active_threats) == 1:
            self.time_scale = TimeScale.REALTIME
            self._alert_player("Time is moving.")

    def exit_danger(self, threat_id: ThreatID) -> None:
        """Return to normal time when safe."""
        self.active_threats.remove(threat_id)
        if not self.active_threats:
            self.time_scale = TimeScale.NORMAL


@dataclass
class Threat:
    """An active danger with time pressure."""

    id: ThreatID
    entity_id: EntityID
    threat_type: str                # "approaching", "aiming", "chasing"

    # Position
    location: tuple[int, int]
    target_location: tuple[int, int]
    speed: float                    # Tiles per second

    # Timing
    time_to_contact: float          # Seconds until threat resolves
    warning_given: bool

    # Resolution
    on_contact: str                 # "damage", "capture", "death"
    escape_affordances: list[str]   # What player can do
```

### 5.2 Threat Approach System

```python
class ThreatSimulator:
    """Simulates approaching dangers in real-time."""

    def tick(self, dt: float, world: WorldGrid) -> list[ThreatEvent]:
        events = []

        for threat in self.active_threats:
            # Move threat toward target
            old_distance = threat.distance_to_player
            threat.tick(dt, world)
            new_distance = threat.distance_to_player

            # Announce approach at thresholds
            if old_distance > 10 and new_distance <= 10:
                events.append(ThreatEvent(
                    type="distant_threat",
                    message="Footsteps. Getting closer.",
                    urgency=0.3,
                ))
            elif old_distance > 5 and new_distance <= 5:
                events.append(ThreatEvent(
                    type="near_threat",
                    message="He's almost here.",
                    urgency=0.6,
                ))
            elif old_distance > 2 and new_distance <= 2:
                events.append(ThreatEvent(
                    type="immediate_threat",
                    message="NOW.",
                    urgency=1.0,
                ))

            # Contact
            if new_distance <= 0:
                events.append(self._resolve_contact(threat))

        return events

    def calculate_time_to_contact(self, threat: Threat, player: Player) -> float:
        """How long until threat reaches player."""
        distance = self._calculate_path_distance(threat.location, player.location)
        return distance / threat.speed
```

### 5.3 Urgency-Aware Input

```python
class UrgencyInputHandler:
    """Input handling that respects time pressure."""

    async def get_input(
        self,
        threat_level: float,
        time_remaining: Optional[float],
    ) -> tuple[str, InputSource]:

        if threat_level >= 0.8 and time_remaining and time_remaining < 3.0:
            # High urgency - prioritize voice
            voice_task = asyncio.create_task(self._get_voice_input(timeout=2.0))
            text_task = asyncio.create_task(self._get_text_input(timeout=2.0))

            done, pending = await asyncio.wait(
                [voice_task, text_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()

            result = done.pop().result()
            return result

        else:
            # Normal - text with optional voice
            return await self._get_text_input(timeout=None)
```

---

## 6. Voice Input (STT) System

### 6.1 Design Philosophy

> **Voice is for panic. Keyboard is for thought.**

Voice input should be:
- An **interrupt**, not a replacement for text
- Used for **urgent reactions** (1-3 words)
- Processed **immediately** without confirmation
- Active during **real-time danger**

### 6.2 Voice Command System

```python
class VoiceCommandType(Enum):
    # Movement (urgent)
    RUN = "run"
    HIDE = "hide"
    DUCK = "duck"
    JUMP = "jump"
    STOP = "stop"

    # Combat (urgent)
    SHOOT = "shoot"
    ATTACK = "attack"
    BLOCK = "block"

    # Social (urgent)
    SURRENDER = "surrender"
    HELP = "help"

    # Items (semi-urgent)
    GUN = "gun"                     # Draw weapon
    LIGHT = "light"                 # Use light source

    # Meta
    PAUSE = "pause"
    WAIT = "wait"


@dataclass
class VoiceCommand:
    """A recognized voice input."""

    raw_audio: bytes
    transcript: str
    command_type: VoiceCommandType
    confidence: float

    # Timing
    timestamp: float
    processing_latency: float       # How long STT took

    # Context
    threat_active: bool
    player_state: str


class VoiceInputSystem:
    """Speech-to-text integration for urgent commands."""

    def __init__(self, config: VoiceConfig):
        self.stt_engine = config.engine      # "whisper", "vosk", "browser"
        self.sample_rate = config.sample_rate
        self.vocabulary = self._load_vocabulary()

        # State
        self.is_listening = False
        self.audio_buffer = []

    async def start_listening(self) -> None:
        """Begin capturing audio input."""
        self.is_listening = True
        self._start_audio_capture()

    async def stop_listening(self) -> None:
        """Stop capturing audio input."""
        self.is_listening = False
        self._stop_audio_capture()

    async def get_command(self, timeout: float = None) -> Optional[VoiceCommand]:
        """Wait for and return a voice command."""

        audio = await self._capture_utterance(timeout)
        if not audio:
            return None

        transcript = await self._transcribe(audio)
        command_type = self._classify_command(transcript)

        return VoiceCommand(
            raw_audio=audio,
            transcript=transcript,
            command_type=command_type,
            confidence=self._calculate_confidence(transcript, command_type),
            timestamp=time.time(),
            processing_latency=self._last_latency,
            threat_active=self._threat_active,
            player_state=self._player_state,
        )

    def _classify_command(self, transcript: str) -> VoiceCommandType:
        """Match transcript to command vocabulary."""

        transcript_lower = transcript.lower().strip()

        # Direct matches
        for cmd_type in VoiceCommandType:
            if cmd_type.value in transcript_lower:
                return cmd_type

        # Synonym matching
        SYNONYMS = {
            VoiceCommandType.RUN: ["go", "move", "escape", "flee", "away"],
            VoiceCommandType.HIDE: ["cover", "down", "conceal"],
            VoiceCommandType.DUCK: ["crouch", "low", "down"],
            VoiceCommandType.SHOOT: ["fire", "kill", "bang"],
            VoiceCommandType.SURRENDER: ["give up", "don't shoot", "okay"],
        }

        for cmd_type, synonyms in SYNONYMS.items():
            for syn in synonyms:
                if syn in transcript_lower:
                    return cmd_type

        # Fallback to LLM classification if no match
        return self._llm_classify(transcript)
```

### 6.3 Voice + Time Integration

```python
class VoiceTimeIntegration:
    """Voice commands that interact with the time system."""

    def __init__(self, time_engine: ContinuousTimeEngine, voice: VoiceInputSystem):
        self.time = time_engine
        self.voice = voice

    async def run_danger_mode(self, threat: Threat) -> ActionResult:
        """Handle input during active danger with voice priority."""

        # Start listening
        await self.voice.start_listening()

        try:
            while threat.time_to_contact > 0:
                # Check for voice input (non-blocking)
                voice_cmd = await self.voice.get_command(timeout=0.1)

                if voice_cmd and voice_cmd.confidence > 0.7:
                    # Voice command received - execute immediately
                    return await self._execute_urgent_command(voice_cmd, threat)

                # Check for text input (non-blocking)
                text_input = await self._check_text_input()

                if text_input:
                    # Text input - parse and execute
                    intent = await self.llm.interpret_input(text_input, urgent=True)
                    return await self._execute_intent(intent, threat)

                # Tick time forward
                self.time.tick(0.1)

                # Re-render to show threat approach
                self._render_danger_state(threat)

            # Threat reached player - no input received in time
            return self._resolve_threat_contact(threat)

        finally:
            await self.voice.stop_listening()

    async def _execute_urgent_command(
        self,
        cmd: VoiceCommand,
        threat: Threat
    ) -> ActionResult:
        """Execute a voice command immediately."""

        # Map voice command to action
        ACTION_MAP = {
            VoiceCommandType.RUN: self._action_flee,
            VoiceCommandType.HIDE: self._action_hide,
            VoiceCommandType.DUCK: self._action_duck,
            VoiceCommandType.SHOOT: self._action_shoot,
            VoiceCommandType.SURRENDER: self._action_surrender,
        }

        action_fn = ACTION_MAP.get(cmd.command_type)
        if action_fn:
            return await action_fn(threat)

        # Unknown command - LLM interprets
        return await self._llm_interpret_urgent(cmd.transcript, threat)
```

### 6.4 STT Engine Configuration

```python
@dataclass
class VoiceConfig:
    """Configuration for voice input system."""

    # Engine selection
    engine: str = "whisper"         # "whisper", "vosk", "browser", "azure"
    model_size: str = "tiny"        # For Whisper: tiny, base, small, medium

    # Audio settings
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024

    # Recognition settings
    language: str = "en"
    vocabulary_boost: list[str] = None  # Boost game-specific words

    # Timing
    min_audio_length: float = 0.3   # Minimum utterance length
    max_audio_length: float = 3.0   # Maximum utterance length
    silence_threshold: float = 0.5  # Seconds of silence to end utterance

    # Performance
    use_gpu: bool = False
    max_latency: float = 0.5        # Target STT latency


# Supported STT backends
STT_BACKENDS = {
    "whisper": {
        "library": "openai-whisper",
        "local": True,
        "latency": "medium",
        "accuracy": "high",
    },
    "vosk": {
        "library": "vosk",
        "local": True,
        "latency": "low",
        "accuracy": "medium",
    },
    "browser": {
        "library": "SpeechRecognition (Web API)",
        "local": False,
        "latency": "low",
        "accuracy": "high",
    },
    "azure": {
        "library": "azure-cognitiveservices-speech",
        "local": False,
        "latency": "low",
        "accuracy": "very_high",
    },
}
```

---

## 7. Graded Danger System

### 7.1 No Instant Death

> **Death should be rare, inevitable in hindsight, caused by accumulation.**

```python
class DamageType(Enum):
    PHYSICAL = "physical"           # Punches, falls
    PIERCING = "piercing"           # Bullets, knives
    ENVIRONMENTAL = "environmental" # Cold, heat, drowning
    PSYCHOLOGICAL = "psychological" # Fear, trauma
    EXHAUSTION = "exhaustion"       # Stamina depletion


@dataclass
class Injury:
    """A specific harm to the player."""

    id: str
    damage_type: DamageType
    severity: float                 # 0.0 to 1.0
    location: str                   # "head", "torso", "arm", etc.

    # Effects
    stat_modifiers: dict[str, float]
    action_penalties: dict[str, float]

    # Progression
    is_bleeding: bool
    bleed_rate: float               # HP loss per second
    is_infected: bool
    infection_rate: float

    # Recovery
    heal_rate: float                # Natural recovery per hour
    requires_treatment: bool

    # Narrative
    visible: bool                   # NPCs can see it
    description: str


class PlayerHealth:
    """Multi-layered health system."""

    # Vitals
    hp: float = 100.0
    max_hp: float = 100.0

    stamina: float = 100.0
    max_stamina: float = 100.0

    # Mental state
    composure: float = 100.0        # Psychological resilience
    max_composure: float = 100.0

    # Active injuries
    injuries: list[Injury]

    # Accumulated effects
    blood_loss: float = 0.0
    exhaustion: float = 0.0
    trauma: float = 0.0

    def take_damage(self, damage: Damage) -> DamageResult:
        """Apply damage and return what happened."""

        # Create injury
        injury = self._create_injury(damage)
        self.injuries.append(injury)

        # Apply immediate HP loss
        actual_damage = damage.amount * (1.0 - self._get_resistance(damage.type))
        self.hp -= actual_damage

        # Check for incapacitation (not death)
        if self.hp <= 0:
            return DamageResult(
                injury=injury,
                incapacitated=True,
                death=self.hp <= -50,  # Only massive damage kills instantly
                message=self._get_incapacitation_message(injury),
            )

        return DamageResult(
            injury=injury,
            incapacitated=False,
            death=False,
            message=self._get_damage_message(injury),
        )

    def tick(self, dt: float) -> list[HealthEvent]:
        """Process ongoing health effects."""

        events = []

        # Bleeding
        for injury in self.injuries:
            if injury.is_bleeding:
                blood_loss = injury.bleed_rate * dt
                self.hp -= blood_loss
                self.blood_loss += blood_loss

                if self.blood_loss > 30:
                    events.append(HealthEvent("blood_loss_severe"))

        # Exhaustion recovery (when resting)
        if self.is_resting:
            self.stamina = min(self.max_stamina, self.stamina + 10 * dt)

        # Natural healing
        for injury in self.injuries:
            if not injury.requires_treatment:
                injury.severity -= injury.heal_rate * dt
                if injury.severity <= 0:
                    self.injuries.remove(injury)
                    events.append(HealthEvent("injury_healed", injury=injury))

        # Death check
        if self.hp <= 0 or self.blood_loss > 50:
            events.append(HealthEvent("death"))

        return events
```

### 7.2 Consequence Cascade

```python
class ConsequenceEngine:
    """Injuries and status effects that compound over time."""

    def apply_consequence(
        self,
        player: PlayerHealth,
        consequence: Consequence,
    ) -> list[Effect]:
        """Apply a consequence and return cascading effects."""

        effects = []

        # Direct effect
        direct = consequence.apply(player)
        effects.append(direct)

        # Check for cascades
        if player.blood_loss > 20:
            effects.append(Effect("dizzy", "Vision blurs at the edges."))

        if player.stamina < 20:
            effects.append(Effect("exhausted", "Every step is lead."))

        if player.composure < 30:
            effects.append(Effect("shaken", "Your hands won't stop trembling."))

        if len(player.injuries) > 3:
            effects.append(Effect("overwhelmed", "Too much. Too fast."))

        return effects

    def get_action_modifiers(self, player: PlayerHealth) -> dict[str, float]:
        """How injuries affect actions."""

        modifiers = {}

        for injury in player.injuries:
            for action, penalty in injury.action_penalties.items():
                modifiers[action] = modifiers.get(action, 0) + penalty

        # Global modifiers from status
        if player.blood_loss > 20:
            modifiers["accuracy"] = modifiers.get("accuracy", 0) - 0.2
            modifiers["speed"] = modifiers.get("speed", 0) - 0.3

        if player.exhaustion > 50:
            modifiers["speed"] = modifiers.get("speed", 0) - 0.4
            modifiers["strength"] = modifiers.get("strength", 0) - 0.3

        return modifiers


# Example: Behind the waterfall
WATERFALL_RISKS = [
    Consequence(
        trigger="slip",
        probability=0.4,
        damage=Damage(type=DamageType.PHYSICAL, amount=15, location="legs"),
        message="Your foot finds nothing. Stone meets shin.",
    ),
    Consequence(
        trigger="force",
        probability=0.2,
        damage=Damage(type=DamageType.PHYSICAL, amount=25, location="torso"),
        message="The water hammers you against rock.",
    ),
    Consequence(
        trigger="cold",
        probability=0.8,
        effect=StatusEffect("cold", duration=300, stamina_drain=0.5),
        message="The cold bites deep. Won't shake this for a while.",
    ),
]
```

### 7.3 Incapacitation vs Death

```python
class IncapacitationHandler:
    """What happens when HP hits zero (not death)."""

    def handle_incapacitation(
        self,
        player: Player,
        cause: str,
        context: WorldContext,
    ) -> IncapacitationResult:
        """Player is down but not necessarily dead."""

        # Determine outcome based on context
        if self._is_lethal_situation(context):
            # Enemies present, will finish player off
            return IncapacitationResult(
                outcome="death",
                delay=5.0,  # 5 seconds to be saved or escape
                can_be_saved=True,
                message="You're down. They're coming to finish it.",
            )

        elif self._has_ally_nearby(context):
            # Ally can help
            return IncapacitationResult(
                outcome="rescued",
                delay=10.0,
                rescuer=self._get_nearest_ally(context),
                message="Darkness. Then hands, pulling you up.",
            )

        else:
            # Alone, but not in danger
            return IncapacitationResult(
                outcome="recovery",
                delay=30.0,  # 30 seconds unconscious
                hp_on_recovery=10,
                message="Time passes. Pain brings you back.",
            )
```

---

## 8. World Memory Extension

### 8.1 Spatial Memory

The world remembers what happened where.

```python
@dataclass
class SpatialMemory:
    """Memory attached to locations."""

    location: tuple[int, int]

    # Events that happened here
    events: list[WorldEvent]

    # Physical changes
    blood_stains: list[BloodStain]
    bullet_holes: list[BulletHole]
    broken_objects: list[BrokenObject]
    moved_objects: list[MovedObject]

    # Sensory traces
    smells: list[Smell]             # Decay over time
    sounds_heard: list[Sound]       # Recent sounds

    # NPC knowledge
    witnessed_by: list[str]         # Who saw something here
    discovered_by: list[str]        # Who found evidence here


class WorldMemoryExtension:
    """Extended memory system for spatial persistence."""

    spatial_memories: dict[tuple[int, int], SpatialMemory]

    def record_spatial_event(
        self,
        event: WorldEvent,
        location: tuple[int, int],
    ) -> None:
        """Record an event at a specific location."""

        if location not in self.spatial_memories:
            self.spatial_memories[location] = SpatialMemory(location=location)

        memory = self.spatial_memories[location]
        memory.events.append(event)

        # Add physical traces based on event type
        if event.type == "gunshot":
            memory.bullet_holes.append(BulletHole(
                position=event.data["impact_point"],
                direction=event.data["direction"],
                timestamp=event.timestamp,
            ))
            memory.sounds_heard.append(Sound(
                type="gunshot",
                volume=0.9,
                timestamp=event.timestamp,
            ))

        elif event.type == "violence":
            if event.data.get("blood"):
                memory.blood_stains.append(BloodStain(
                    amount=event.data["blood_amount"],
                    position=event.data["position"],
                    timestamp=event.timestamp,
                ))

    def get_location_description_modifiers(
        self,
        location: tuple[int, int],
    ) -> list[str]:
        """Get narrative modifiers based on location history."""

        modifiers = []

        if location in self.spatial_memories:
            memory = self.spatial_memories[location]

            if memory.blood_stains:
                age = self._get_oldest_stain_age(memory.blood_stains)
                if age < 3600:  # Less than 1 hour
                    modifiers.append("fresh_blood")
                elif age < 86400:  # Less than 1 day
                    modifiers.append("dried_blood")
                else:
                    modifiers.append("old_stains")

            if memory.bullet_holes:
                modifiers.append("bullet_damage")

            if any(e.type == "death" for e in memory.events):
                modifiers.append("death_site")

        return modifiers
```

### 8.2 NPC Spatial Awareness

```python
class NPCSpatialAwareness:
    """NPCs know about and react to spatial history."""

    def get_npc_reaction_to_location(
        self,
        npc: Character,
        location: tuple[int, int],
        world_memory: WorldMemoryExtension,
    ) -> Optional[NPCReaction]:
        """How an NPC reacts to a location's history."""

        memory = world_memory.spatial_memories.get(location)
        if not memory:
            return None

        # Check if NPC witnessed something here
        if npc.id in memory.witnessed_by:
            event = self._get_witnessed_event(npc.id, memory)
            return NPCReaction(
                type="recall",
                intensity=0.7,
                dialogue_available=True,
                topic=f"witnessed_{event.type}",
            )

        # Check if NPC discovers evidence
        if memory.blood_stains and npc.id not in memory.discovered_by:
            memory.discovered_by.append(npc.id)
            return NPCReaction(
                type="discovery",
                intensity=0.9,
                triggers_behavior=True,
                behavior="investigate_or_flee",
            )

        # Check if this is significant to NPC's story
        if self._location_significant_to_npc(npc, memory):
            return NPCReaction(
                type="emotional",
                intensity=0.5,
                changes_dialogue=True,
            )

        return None
```

---

## 9. Procedural Generation Pipeline

### 9.1 Deferred Generation

> **Only generate what's needed, when it's needed.**

```python
class DeferredGenerator:
    """Generate world content on-demand, not upfront."""

    def __init__(self, llm: LLMInterpreter, constraints: GenerationConstraints):
        self.llm = llm
        self.constraints = constraints
        self.generation_cache = {}

    async def ensure_generated(
        self,
        location: tuple[int, int],
        trigger: str,
    ) -> None:
        """Make sure a location is fully generated."""

        tile = self.world.get_tile(*location)

        if tile.generated:
            return

        # Get surrounding context
        context = self._gather_context(location)

        # Ask LLM to fill in details
        expansion = await self.llm.expand_world(
            location=location,
            trigger=trigger,
            constraints=self.constraints,
        )

        # Apply expansion to world
        self._apply_expansion(location, expansion)

        tile.generated = True

    async def generate_behind(
        self,
        feature: Entity,
        approach_direction: Direction,
    ) -> GeneratedSpace:
        """Generate what's behind/inside something."""

        # Example: "go behind the waterfall"

        prompt_context = {
            "feature": feature.to_dict(),
            "approach": approach_direction.value,
            "surroundings": self._get_surroundings(feature.location),
            "narrative_context": self.constraints.narrative_spine.relevant_info,
        }

        result = await self.llm.generate_hidden_space(prompt_context)

        # Validate against constraints
        if not self._validate_generation(result):
            result = self._constrain_generation(result)

        # Create tiles for new space
        new_tiles = self._create_tiles_from_generation(result)

        # Link to existing world
        self._connect_spaces(feature.location, new_tiles, approach_direction)

        return GeneratedSpace(
            tiles=new_tiles,
            description=result.description,
            entities=result.new_entities,
            hazards=result.hazards,
        )
```

### 9.2 Generation Constraints

```python
@dataclass
class GenerationConstraints:
    """Rules that bound procedural generation."""

    # Narrative spine (cannot contradict)
    narrative_spine: NarrativeSpine

    # Established facts (immutable)
    established_facts: dict[str, Any]

    # Setting rules
    genre: str = "noir"
    era: str = "1940s"
    location_type: str = "urban"

    # Plausibility bounds
    tech_level: str = "period_appropriate"
    supernatural: bool = False

    # Danger bounds
    min_danger: float = 0.0
    max_danger: float = 0.8         # Reserve 1.0 for scripted moments

    # Density bounds
    max_entities_per_chunk: int = 10
    max_items_per_room: int = 20

    # Forbidden elements
    forbidden: list[str] = field(default_factory=lambda: [
        "magic",
        "aliens",
        "time_travel",
        "resurrection",
    ])

    def validate(self, generation: WorldExpansion) -> ValidationResult:
        """Check if generation respects constraints."""

        errors = []

        # Check forbidden elements
        for forbidden in self.forbidden:
            if forbidden in generation.description.lower():
                errors.append(f"Contains forbidden element: {forbidden}")

        # Check narrative consistency
        if generation.contradicts(self.narrative_spine):
            errors.append("Contradicts narrative spine")

        # Check established facts
        for fact_key, fact_value in self.established_facts.items():
            if generation.contradicts_fact(fact_key, fact_value):
                errors.append(f"Contradicts established fact: {fact_key}")

        # Check danger bounds
        if generation.danger_level < self.min_danger:
            errors.append("Below minimum danger")
        if generation.danger_level > self.max_danger:
            errors.append("Above maximum danger")

        return ValidationResult(valid=len(errors) == 0, errors=errors)
```

### 9.3 Consistency Maintenance

```python
class ConsistencyEngine:
    """Ensures generated content doesn't contradict itself."""

    def __init__(self):
        self.facts = FactDatabase()
        self.spatial_facts = SpatialFactDatabase()

    def record_fact(self, fact: Fact) -> None:
        """Record a new established fact."""

        # Check for contradictions
        contradictions = self.facts.find_contradictions(fact)
        if contradictions:
            raise ConsistencyError(f"New fact contradicts: {contradictions}")

        self.facts.add(fact)

    def record_spatial_fact(self, location: tuple[int, int], fact: Fact) -> None:
        """Record a fact about a specific location."""
        self.spatial_facts.add(location, fact)

    def get_constraints_for_location(
        self,
        location: tuple[int, int],
    ) -> list[Fact]:
        """Get all facts that constrain generation at a location."""

        constraints = []

        # Global facts
        constraints.extend(self.facts.get_relevant(location))

        # Local facts
        constraints.extend(self.spatial_facts.get(location))

        # Nearby facts (things in adjacent tiles affect this one)
        for neighbor in self._get_neighbors(location):
            constraints.extend(self.spatial_facts.get(neighbor))

        return constraints


# Example facts
EXAMPLE_FACTS = [
    Fact("waterfall_exists", location=(45, 23), permanent=True),
    Fact("waterfall_has_cave", location=(45, 23), permanent=True,
         discovered_by="player"),
    Fact("cave_contains_body", location=(46, 23), permanent=True,
         clue_id="victim_hiding_spot"),
]
```

---

## 10. Integration Architecture

### 10.1 Full System Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LIVING WORLD ENGINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  INPUT LAYER                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │  Text Input    │  │  Voice (STT)   │  │  Hotkey        │                 │
│  │  (keyboard)    │  │  (microphone)  │  │  (shortcuts)   │                 │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘                 │
│          │                   │                   │                          │
│          └───────────────────┼───────────────────┘                          │
│                              │                                               │
│                              ▼                                               │
│  INTERPRETATION LAYER                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                    LLM INTERPRETER                                │       │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │       │
│  │  │   Intent     │  │   World      │  │  Narration   │            │       │
│  │  │   Parser     │  │   Expander   │  │  Generator   │            │       │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                              │                                               │
│                              ▼                                               │
│  RESOLUTION LAYER                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Affordance  │  │   Physics    │  │    Time      │  │   Danger     │     │
│  │   Engine     │  │   Resolver   │  │   Engine     │  │   System     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │                 │              │
│         └─────────────────┼─────────────────┼─────────────────┘              │
│                           │                 │                                │
│                           ▼                 ▼                                │
│  STATE LAYER                                                                 │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │       │
│  │  │    World     │  │   Memory     │  │   Player     │            │       │
│  │  │    Grid      │  │    Bank      │  │    State     │            │       │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                              │                                               │
│                              ▼                                               │
│  OUTPUT LAYER                                                                │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                    ASCII RENDERER                                 │       │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │       │
│  │  │   Viewport   │  │  Particles   │  │     UI       │            │       │
│  │  │   Renderer   │  │   System     │  │   Overlay    │            │       │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                              │                                               │
│                              ▼                                               │
│                     ┌──────────────┐                                         │
│                     │   Terminal   │                                         │
│                     └──────────────┘                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Main Loop Integration

```python
class LivingWorldEngine:
    """Main engine integrating all systems."""

    def __init__(self, config: EngineConfig):
        # Core systems
        self.world = WorldGrid()
        self.memory = MemoryBank()
        self.time = ContinuousTimeEngine()

        # Interpretation
        self.llm = LLMInterpreter(config.llm)
        self.intent_resolver = IntentResolver()

        # Resolution
        self.affordances = AffordanceEngine()
        self.physics = PhysicsResolver()
        self.danger = DangerSystem()

        # Generation
        self.generator = DeferredGenerator(self.llm, config.constraints)
        self.consistency = ConsistencyEngine()

        # Input
        self.text_input = TextInputHandler()
        self.voice_input = VoiceInputSystem(config.voice)

        # Output
        self.renderer = SpatialRenderer()

        # State
        self.player = Player()
        self.npcs = NPCManager()

    async def run(self) -> None:
        """Main game loop."""

        while self.running:
            # 1. Render current state
            frame = self.renderer.render_frame(self.world, self.player)
            self._present(frame)

            # 2. Get input (respecting time pressure)
            threat_level = self.danger.get_current_threat_level()

            if threat_level > 0.7:
                # Real-time danger mode
                input_result = await self._get_urgent_input()
            else:
                # Normal input
                input_result = await self._get_normal_input()

            # 3. Interpret input
            intent = await self.llm.interpret_input(
                input_result.text,
                self._get_world_context(),
                self._get_player_state(),
            )

            # 4. Resolve intent through systems
            result = await self._resolve_intent(intent)

            # 5. Update world state
            self._apply_result(result)

            # 6. Tick time
            time_events = self.time.tick(self._get_dt())
            for event in time_events:
                await self._handle_time_event(event)

            # 7. Generate narration
            narration = await self.llm.generate_narration(
                result,
                self._get_world_context(),
                self._get_player_state(),
            )

            # 8. Display narration
            self._display_narration(narration)

    async def _resolve_intent(self, intent: ParsedIntent) -> ActionResult:
        """Run intent through all resolution systems."""

        # Ensure target area is generated
        if intent.target_location:
            await self.generator.ensure_generated(
                intent.target_location,
                trigger=f"player_{intent.intent_type.value}",
            )

        # Get affordances for target
        if intent.primary_target:
            target = self.world.get_entity(intent.primary_target)
            affordances = self.affordances.get_affordances(target, self._get_context())
            matched = self.affordances.match_intent_to_affordances(intent, affordances)
        else:
            matched = []

        # Resolve through physics
        if matched:
            physics_result = self.physics.resolve(intent, matched[0])
        else:
            physics_result = self.physics.resolve_freeform(intent)

        # Apply danger calculations
        danger_result = self.danger.calculate_danger(intent, physics_result)

        # Combine into final result
        return ActionResult(
            success=physics_result.success,
            effects=physics_result.effects + danger_result.effects,
            time_elapsed=physics_result.time_cost,
            danger_events=danger_result.events,
        )
```

### 10.3 New Dependencies

```python
# requirements.txt additions

# LLM Integration
anthropic>=0.18.0               # Claude API
# OR
openai>=1.0.0                   # OpenAI API
# OR
llama-cpp-python>=0.2.0         # Local LLaMA

# Voice Input (choose one or more)
openai-whisper>=20231117        # Local STT (Whisper)
vosk>=0.3.45                    # Local STT (Vosk)
SpeechRecognition>=3.10.0       # Browser/cloud STT
azure-cognitiveservices-speech>=1.35.0  # Azure STT

# Audio capture
sounddevice>=0.4.6
numpy>=1.24.0

# Async support
asyncio                         # Built-in
aiohttp>=3.9.0                  # Async HTTP for API calls
```

---

## Appendix: Implementation Priority

### Phase 1: Spatial Foundation
1. Tile-based world grid
2. Chunk loading/unloading
3. Viewport rendering
4. Basic movement

### Phase 2: LLM Integration
1. Intent interpretation
2. World expansion
3. Narration generation
4. Consistency engine

### Phase 3: Affordance System
1. Affordance definitions
2. Intent-to-affordance matching
3. No-fail interaction resolution

### Phase 4: Time & Danger
1. Continuous time engine
2. Threat simulation
3. Graded damage system
4. Incapacitation handling

### Phase 5: Voice Input
1. STT integration
2. Voice command classification
3. Urgency-aware input handling
4. Real-time danger mode

---

*End of Living World Addendum*
