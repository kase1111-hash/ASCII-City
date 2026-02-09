# ShadowEngine — Unified Schema

> **Version**: 1.0.0
> **Status**: Master Integration Document
> **Purpose**: Single source of truth for all engine systems

---

## Overview

ShadowEngine is a **real-time ASCII world engine** where:
- Player improvisation matters (STT + LLM)
- NPCs behave realistically (memory, rumor, perception)
- Emergent danger is felt, not scripted
- World responds dynamically (affordances, LOS, sound)

This document consolidates all system specifications into a unified schema.

---

## Document Index

| Spec | Purpose | Lines |
|------|---------|-------|
| `SPEC_SHEET.md` | Core architecture, modules, data structures | 1,412 |
| `SPEC_ADDENDUM_LIVING_WORLD.md` | Spatial simulation, LLM interpretation | 2,091 |
| `SPEC_ADDENDUM_SOUND_AND_SYSTEMS.md` | Sound propagation, fuzzy STT, reaction windows | ~1,200 |
| `SPEC_AFFORDANCE_SCHEMA.md` | Canonical affordance system | ~1,200 |
| `SPEC_TILE_INHERITANCE.md` | 7-layer tile affordance composition | 1,044 |
| `SPEC_DESIGN_PHILOSOPHY.md` | Core principles (world-first, capability damage) | 970 |
| `SPEC_NPC_MEMORY_RUMORS.md` | NPC beliefs, rumor mutation, social simulation | 1,250 |
| `SPEC_THREAT_PROXIMITY.md` | Real-time danger, escalation, STT timing | 1,350 |
| `SPEC_PERCEPTION_LOS_SOUND.md` | FPV rendering, LOS, sound propagation | 1,512 |
| **This Document** | Unified integration schema | - |

**Total Specification: ~12,000 lines**

---

## 1. Tile Definition

Each tile represents a unit of the world (1×1 in world space, variable in FPV rendering).

### Unified Tile Schema

```python
@dataclass
class Tile:
    """Complete tile definition with all systems integrated."""

    # Identity
    id: str
    position: tuple[int, int]
    tile_type: str                  # "stone_wall", "waterfall", "forest", etc.

    # Physical properties
    elevation: int                  # Height level for LOS/movement
    liquid_depth: float             # 0 = none, >0 = depth

    # Perception properties (→ SPEC_PERCEPTION_LOS_SOUND.md)
    opacity: float                  # 0.0 = transparent, 1.0 = solid
    sound_absorption: float         # Fraction of sound dampened
    sound_emission: float           # Continuous sound (waterfall)
    light_modifier: float           # Affects visibility

    # Affordance system (→ SPEC_AFFORDANCE_SCHEMA.md)
    base_affordances: list[Affordance]
    computed_affordances: dict[str, float]  # After inheritance

    # State (→ SPEC_TILE_INHERITANCE.md)
    state: list[str]                # ["wet", "bloodied", "burning"]
    entities: list[str]             # Entity IDs on this tile
    history: list[TileEvent]        # What happened here

    # Memory (→ SPEC_NPC_MEMORY_RUMORS.md)
    tile_memory: TileMemory         # Rumor density, danger rating

    # Generation
    generated: bool
    generation_seed: int
```

### JSON Schema

```json
{
  "id": "tile_45_23",
  "position": [45, 23],
  "tile_type": "waterfall",
  "elevation": 0,
  "liquid_depth": 0.5,
  "opacity": 0.6,
  "sound_absorption": 0.3,
  "sound_emission": 0.7,
  "light_modifier": 0.8,
  "base_affordances": [
    {"id": "conceals", "intensity": 0.9},
    {"id": "traversable", "intensity": 0.4},
    {"id": "slippery", "intensity": 0.8}
  ],
  "state": ["wet"],
  "entities": ["waterfall_entity_01"],
  "tile_memory": {
    "rumor_density": 0.3,
    "danger_rating": 0.4
  }
}
```

### Affordance Inheritance Stack

```
Layer 7: Temporal     (night, chaos, alert)
Layer 6: Weather      (rain, fog, storm)
Layer 5: Entities     (waterfall, NPC, debris)
Layer 4: State        (wet, bloodied, burning)
Layer 3: Tile Base    (rocky_ledge, wooden_floor)
Layer 2: Biome        (cliffside, alley, sewer)
Layer 1: World Rules  (gravity, sound propagation)
```

See: `SPEC_TILE_INHERITANCE.md`

---

## 2. World Perception System

**Everything is filtered through perception, not direct information.**

### 2.1 First-Person View (FPV)

```
┌──────────────────────────────────────────────────────────────────────────┐
│        ▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓▓▓▓▓▓▓              │
│      ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████████            │
│     ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██████████████           │
│    ████████████████         ☻ ←threat          ████████████████          │
│   ██████████████████                          ██████████████████         │
│  ████████████████████████████████████████████████████████████████        │
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
└──────────────────────────────────────────────────────────────────────────┘
                           Forward-facing, depth-shaded
```

- Raycasting for wall rendering
- Depth shading: `█ → ▓ → ▒ → ░ → ·` by distance
- Entity sprites scale with distance

See: `SPEC_PERCEPTION_LOS_SOUND.md` Section 1

### 2.2 Line-of-Sight (LOS)

```python
def calculate_los(origin: tuple, target: tuple, world: WorldGrid) -> Visibility:
    """Raycast with accumulated opacity."""

    accumulated_opacity = 0.0

    for tile in raycast_path(origin, target):
        visibility = 1.0 - accumulated_opacity
        accumulated_opacity += tile.opacity

        if accumulated_opacity >= 0.99:
            return Visibility.BLOCKED

    return Visibility(clarity=1.0 - accumulated_opacity)
```

**Dynamic Obstructions:**
- Waterfall: LOS blocked + muffled sound
- Smoke/fire: LOS reduced, glare effects
- Darkness: LOS shrinks, vision flicker

See: `SPEC_PERCEPTION_LOS_SOUND.md` Section 3

### 2.3 Sound Propagation

```python
def propagate_sound(source: tuple, volume: float, world: WorldGrid) -> dict:
    """BFS wavefront sound propagation."""

    sound_map = {}
    queue = deque([(source, volume)])

    while queue:
        position, current_volume = queue.popleft()
        sound_map[position] = current_volume

        for neighbor in get_neighbors(position):
            tile = world.get_tile(*neighbor)
            attenuation = 1.0 / (distance ** 2)
            attenuation *= (1.0 - tile.sound_absorption)
            new_volume = current_volume * attenuation

            if new_volume > 0.01:
                queue.append((neighbor, new_volume))

    return sound_map
```

**Audio Indicators:**
- `*` = faint noise
- `!` = urgent, loud
- `~` = flowing water
- Position on screen edge indicates direction

See: `SPEC_PERCEPTION_LOS_SOUND.md` Section 4

---

## 3. NPC System

### 3.1 NPC Schema

```python
@dataclass
class NPC:
    """Complete NPC with all systems integrated."""

    # Identity
    id: str
    name: str
    archetype: str

    # Position & movement
    position: tuple[float, float]
    facing_angle: float
    velocity: float

    # Perception (→ SPEC_PERCEPTION_LOS_SOUND.md)
    sight_range: float
    fov: float                      # Field of view degrees
    hearing_range: float

    # Awareness (→ SPEC_THREAT_PROXIMITY.md)
    awareness_score: float          # 0.0 to 1.0
    awareness_state: AwarenessState # UNAWARE → SUSPICIOUS → ALERT → ENGAGED

    # Memory (→ SPEC_NPC_MEMORY_RUMORS.md)
    memories: list[NPCMemory]
    memory_capacity: int
    rumor_beliefs: list[Rumor]

    # Behavior
    behavior_state: str             # "idle", "patrol", "alert", "combat", "flee"
    escalation_stage: int           # 0-5 for threats

    # Psychology
    bias: NPCBias                   # fearful, paranoid, loyal, etc.
    motivations: MotivationVector   # fear, greed, loyalty, etc.

    # Threat properties
    is_threat: bool
    reaction_window: float
    damage_potential: float
```

### 3.2 Awareness Calculation

```python
awareness = base_awareness
         + f(LOS_visibility)        # Can they see player?
         + f(sound_intensity)       # Can they hear player?
         + f(memory_relevance)      # Do they remember player?
         + f(rumor_beliefs)         # Have they heard about player?
         × curiosity_modifier       # Personality factor
```

**Awareness States:**

| Score | State | Behavior |
|-------|-------|----------|
| 0.0-0.1 | UNAWARE | Normal patrol/idle |
| 0.1-0.3 | SUSPICIOUS | Pauses, looks around |
| 0.3-0.6 | ALERT | Investigates |
| 0.6-1.0 | ENGAGED | Pursues/attacks |

See: `SPEC_THREAT_PROXIMITY.md` Section 6

### 3.3 Memory & Rumor System

```
EVENT (ground truth)      →  MEMORY (subjective)     →  RUMOR (mutated)
"Player slipped"          →  "Someone fell"          →  "Waterfall kills"
                                                     →  "Mob dumps bodies"
```

**Memory Properties:**
- `summary`: NPC's interpretation (not fact)
- `confidence`: Decays over time
- `emotional_weight`: How often recalled
- `trust_source`: "self", "friend", "rumor", "enemy"

**Rumor Mutation:**
- Confidence decreases each transfer
- Content simplifies, exaggerates, or misattributes
- Bias affects what's remembered and shared

See: `SPEC_NPC_MEMORY_RUMORS.md`

---

## 4. Threat & Reaction System

### 4.1 Threat Schema

```python
@dataclass
class Threat:
    """Active danger source."""

    id: str
    threat_type: str                # "gunman", "fire", "vehicle"
    position: tuple[float, float]
    velocity: float                 # Tiles per second

    # Danger parameters
    awareness: float                # Detection probability
    lethality_range: float          # Distance for damage
    reaction_window: float          # Seconds before action
    escalation_stage: int           # 0-5

    # Perception
    sound_signature: float
    visibility: float
```

### 4.2 Reaction Timing

```python
effective_reaction_time = (
    base_reaction
    + stt_latency
    + injury_penalty
    + fear_penalty
    - adrenaline_bonus
)

if effective_reaction_time <= threat.reaction_window * 0.5:
    result = "EARLY"        # Full success
elif effective_reaction_time <= threat.reaction_window * 0.8:
    result = "ON_TIME"      # Success with minor cost
elif effective_reaction_time <= threat.reaction_window:
    result = "LATE"         # Partial success, injury
else:
    result = "TOO_LATE"     # Threat wins
```

### 4.3 Escalation Ladder

```
Stage 0: NOTICE     (3.0s) "Hey, who's there?"
Stage 1: CHALLENGE  (2.0s) "Don't move!"
Stage 2: ADVANCE    (1.5s) *footsteps*
Stage 3: AIM        (1.0s) *weapon raised*
Stage 4: WARNING    (0.8s) *BANG* (warning shot)
Stage 5: LETHAL     (0.5s) *fires to kill*

Each stage: window shrinks, options narrow
```

### 4.4 Proximity Bands

| Distance | Band | Effect |
|----------|------|--------|
| > 15 tiles | FAR | Audio cues only |
| 8-15 tiles | MEDIUM | Visual jitter |
| 3-8 tiles | NEAR | Input penalty, screen pressure |
| 1-3 tiles | IMMINENT | Flicker, shake, shrinking window |
| < 1 tile | CONTACT | Damage resolution |

See: `SPEC_THREAT_PROXIMITY.md`

---

## 5. Affordance & Interaction Layer

### 5.1 Affordance Categories

```
SPATIAL:        supports, blocks, conceals, funnels, elevates
MOVEMENT:       traversable, slippery, climbable, unstable
SENSORY:        obscures_vision, deadens_sound, illuminates
PHYSICAL_RISK:  injures, fatigues, bleeds, burns
SOCIAL:         threatens, intimidates, reassures
TEMPORAL:       delays, accelerates, creates_deadline
```

### 5.2 Intent → Affordance Resolution

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Step 1: PLAYER INTENT                                                  │
│  "Go behind the waterfall"                                              │
├─────────────────────────────────────────────────────────────────────────┤
│  Step 2: LLM INTERPRETATION                                             │
│  {"intent_type": "movement", "target": "waterfall",                     │
│   "modifiers": ["concealment"]}                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  Step 3: AFFORDANCE MATCHING                                            │
│  waterfall.conceals = 0.9 ✓                                             │
│  waterfall.traversable = 0.4 ✓                                          │
│  waterfall.slippery = 0.8 (risk)                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  Step 4: SIMULATION RESOLUTION                                          │
│  Physics: slip_roll(0.8) → slipped                                      │
│  Damage: 12 HP                                                          │
│  Position: behind waterfall                                             │
├─────────────────────────────────────────────────────────────────────────┤
│  Step 5: LLM NARRATION                                                  │
│  "You force through the curtain of water. Your foot finds nothing—      │
│   stone meets shin, hard. But you're through."                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.3 LLM Boundaries

| ✅ Allowed | ❌ Forbidden |
|------------|--------------|
| Identify tiles referenced | Invent tile states |
| Map language → intent | Modify affordances |
| Describe outcomes (constrained) | Decide success/failure |
| Generate hidden spaces (constrained) | Violate narrative spine |

See: `SPEC_AFFORDANCE_SCHEMA.md`

---

## 6. Player Input: STT Integration

### 6.1 Voice as Interrupt

```python
async def process_voice_input(audio: bytes, world_state: WorldState) -> Result:
    # 1. Capture timestamp immediately
    input_timestamp = time.time()

    # 2. STT processing (adds latency)
    transcript = await stt_engine.transcribe(audio)
    stt_latency = time.time() - input_timestamp

    # 3. Parse intent
    intent = intent_parser.parse(transcript)

    # 4. Create in-world sound event (player spoke!)
    sound_event = propagate_sound(
        player.position,
        volume=get_voice_volume(audio),
        world=world,
    )

    # 5. Resolve against active threats
    result = resolve_with_timing(intent, threats, stt_latency)

    return result
```

### 6.2 Fuzzy STT Matching

```python
# "rum away" → "run away"
# "chute" → "shoot"
# "duck" → "duck"

# Phonetic matching + context awareness
if threat_level > 0.7:
    # Prioritize defensive commands
    prefer = ["run", "hide", "duck", "flee"]
```

### 6.3 Voice Creates Sound

Player shouts "Run!" → Sound event (volume 0.7) → NPCs may hear

```python
VOICE_VOLUMES = {
    "whisper": 0.1,
    "normal": 0.3,
    "shout": 0.7,
}
```

See: `SPEC_ADDENDUM_SOUND_AND_SYSTEMS.md`

---

## 7. Rendering & Feedback

### 7.1 FPV ASCII Rendering

```python
def render_frame(world: WorldGrid, player: Player) -> str:
    frame = empty_frame(80, 24)

    # 1. Raycast walls for each screen column
    for screen_x in range(80):
        ray_angle = get_ray_angle(screen_x, player.facing_angle)
        hit = cast_ray(player.position, ray_angle, world)

        if hit:
            wall_height = calculate_height(hit.distance)
            wall_char = get_depth_char(hit.distance)  # █▓▒░·
            draw_wall_strip(frame, screen_x, wall_height, wall_char)

    # 2. Render entities (NPCs, items) as sprites
    for entity in visible_entities:
        sprite = get_entity_sprite(entity, distance)
        draw_sprite(frame, entity.screen_position, sprite)

    # 3. Apply perception effects
    apply_partial_visibility(frame, partial_tiles)
    apply_threat_proximity_effects(frame, threats)
    apply_fear_effects(frame, player.fear_level)

    # 4. Render audio indicators
    for sound in active_sounds:
        direction = get_sound_direction(player, sound.source)
        draw_audio_indicator(frame, direction, sound.volume)

    return frame_to_string(frame)
```

### 7.2 Visual Effects by State

| Condition | Effect |
|-----------|--------|
| Partial visibility | Flicker, dim characters |
| Threat MEDIUM | Edge jitter toward threat |
| Threat NEAR | Edge darkening, character thickening |
| Threat IMMINENT | Screen shake, flicker |
| Fear > 0.5 | Shake, audio distortion |
| Fear > 0.9 | Tunnel vision, pulse |

### 7.3 Audio Representation

```
Sound indicators on screen edges:

    [*] = left, quiet       [!] = left, loud
                    [*]
                     │
    ┌────────────────┼────────────────┐
    │                │                │
[*] │     GAME       │     VIEW       │ [!]
    │                │                │
    └────────────────┴────────────────┘
                    [*]
                     = behind, quiet
```

See: `SPEC_PERCEPTION_LOS_SOUND.md` Section 7

---

## 8. Main Processing Loop

```python
class GameLoop:
    """Main engine loop - 50-100ms tick for real-time responsiveness."""

    TICK_RATE = 0.05  # 50ms = 20 ticks/second

    async def run(self):
        while self.running:
            dt = self.get_delta_time()

            # 1. GATHER INPUT
            voice_input = await self.stt.get_pending_input()
            keyboard_input = self.keyboard.get_pending_input()

            # 2. PROCESS INPUT (voice or keyboard)
            if voice_input:
                intent, sound_event = self.process_voice(voice_input)
                self.active_sounds.append(sound_event)
            elif keyboard_input:
                intent = self.parse_keyboard(keyboard_input)
            else:
                intent = None

            # 3. UPDATE WORLD STATE
            self.environment.tick(dt)           # Weather, time
            self.sound_system.tick(dt)          # Sound propagation
            self.sound_system.decay_sounds(dt)  # Sounds fade

            # 4. UPDATE NPC PERCEPTION
            for npc in self.npcs:
                # Calculate LOS
                los = self.los_system.calculate(npc, self.player, self.world)

                # Calculate sound awareness
                sound_awareness = self.get_sound_at(npc.position)

                # Update awareness
                npc.awareness = self.calculate_awareness(
                    npc, los, sound_awareness, npc.memories, npc.rumors
                )

                # Update behavior state
                self.update_npc_state(npc)

            # 5. PROCESS THREATS
            for threat in self.active_threats:
                # Update escalation
                self.threat_system.tick(threat, dt, self.player)

                # Check reaction windows
                if threat.window_expired:
                    self.resolve_threat_action(threat)

            # 6. RESOLVE PLAYER INTENT
            if intent:
                result = await self.resolve_intent(intent)
                self.apply_result(result)

            # 7. UPDATE MEMORIES & RUMORS
            for event in self.pending_events:
                self.journal.record(event)
                self.propagate_to_witnesses(event)

            # 8. RENDER
            frame = self.renderer.render(
                self.world,
                self.player,
                self.npcs,
                self.active_sounds,
                self.active_threats,
            )
            self.display(frame)

            # 9. MAINTAIN TICK RATE
            await self.sleep_until_next_tick()
```

### Loop Summary

| Step | System | Reference |
|------|--------|-----------|
| 1. Input | STT + Keyboard | SPEC_ADDENDUM_SOUND_AND_SYSTEMS |
| 2. Process | Intent parsing | SPEC_AFFORDANCE_SCHEMA |
| 3. World | Environment sim | SPEC_ADDENDUM_LIVING_WORLD |
| 4. Perception | LOS + Sound | SPEC_PERCEPTION_LOS_SOUND |
| 5. Threats | Reaction timing | SPEC_THREAT_PROXIMITY |
| 6. Resolution | Affordance matching | SPEC_AFFORDANCE_SCHEMA |
| 7. Memory | Event journaling | SPEC_NPC_MEMORY_RUMORS |
| 8. Render | FPV ASCII | SPEC_PERCEPTION_LOS_SOUND |

---

## 9. System Integration Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SHADOWENGINE                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  INPUT LAYER                                                                 │
│  ┌──────────────┐  ┌──────────────┐                                         │
│  │  Voice (STT) │  │   Keyboard   │                                         │
│  └──────┬───────┘  └──────┬───────┘                                         │
│         └──────────┬──────┘                                                  │
│                    ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    LLM INTERPRETATION                                │    │
│  │  Intent parsing │ Affordance matching │ Narration generation        │    │
│  └─────────────────────────────┬───────────────────────────────────────┘    │
│                                │                                             │
│         ┌──────────────────────┼──────────────────────┐                     │
│         ▼                      ▼                      ▼                     │
│  ┌──────────────┐  ┌───────────────────┐  ┌──────────────────┐              │
│  │  AFFORDANCE  │  │   WORLD STATE     │  │   THREAT         │              │
│  │  RESOLUTION  │  │   SIMULATION      │  │   SYSTEM         │              │
│  │              │  │                   │  │                  │              │
│  │ • Intent     │  │ • Tile grid       │  │ • Proximity      │              │
│  │ • Matching   │  │ • Environment     │  │ • Escalation     │              │
│  │ • Physics    │  │ • Time            │  │ • Reaction       │              │
│  └──────┬───────┘  └─────────┬─────────┘  └────────┬─────────┘              │
│         │                    │                     │                         │
│         └────────────────────┼─────────────────────┘                         │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    PERCEPTION LAYER                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │     LOS      │  │    SOUND     │  │   AWARENESS  │               │    │
│  │  │  Raycasting  │  │ Propagation  │  │  Calculation │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  └─────────────────────────────┬───────────────────────────────────────┘    │
│                                │                                             │
│         ┌──────────────────────┼──────────────────────┐                     │
│         ▼                      ▼                      ▼                     │
│  ┌──────────────┐  ┌───────────────────┐  ┌──────────────────┐              │
│  │     NPC      │  │   EVENT           │  │   PLAYER         │              │
│  │   BEHAVIOR   │  │   JOURNAL         │  │   STATE          │              │
│  │              │  │                   │  │                  │              │
│  │ • Memory     │  │ • World events    │  │ • Health         │              │
│  │ • Rumors     │  │ • Tile history    │  │ • Injuries       │              │
│  │ • Decisions  │  │ • NPC memories    │  │ • Fear           │              │
│  └──────────────┘  └───────────────────┘  └──────────────────┘              │
│                                                                              │
│                                │                                             │
│                                ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    FPV ASCII RENDERER                                │    │
│  │  Raycasting │ Depth shading │ Sprites │ Effects │ Audio indicators  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                │                                             │
│                                ▼                                             │
│                         ┌──────────────┐                                     │
│                         │   TERMINAL   │                                     │
│                         └──────────────┘                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Core Design Principles

### From SPEC_DESIGN_PHILOSOPHY.md

| Principle | Implementation |
|-----------|----------------|
| World First, Player Second | Simulation runs independent of input |
| Capability Damage, Not HP | Injuries reduce affordances, not numbers |
| Event Journaling | Every meaningful event logged |
| Losing Is Fun | Death creates stories, not punishment |
| World Is the UI | Screen communicates through effects |
| Hesitation Degrades Outcomes | Late actions have reduced effectiveness |
| Diegetic Memory Access | History through world, not menus |
| Threats Are Affordance Profiles | No stat blocks, just affordances |

### Non-Negotiable Rules

```
1. The world doesn't care about the player
2. Injuries reduce capability, not HP
3. Every meaningful event is logged
4. Death is output, not bug
5. The screen teaches without tutorials
6. Hesitation has mechanical cost
7. History surfaces through the world, not UI
8. Threats are affordance profiles, not stat blocks
9. NPCs act on beliefs, not truth
10. LLM interprets, simulation resolves
```

---

## 11. Implementation Phases

### Phase 1: Foundation
```
- Tile grid with perception properties
- Basic FPV raycasting
- Single player movement
- LOS calculation
- Sound propagation (BFS)
```

### Phase 2: Interaction
```
- Affordance system
- LLM intent interpretation
- Basic NPC with awareness
- Single threat with reaction window
- STT integration
```

### Phase 3: Social Simulation
```
- NPC memory system
- Rumor propagation
- Memory → behavior mapping
- Tile memory
- Event journaling
```

### Phase 4: Combat & Danger
```
- Threat escalation ladder
- Multiple threats
- Injury system
- Fear feedback loop
- Proximity rendering effects
```

### Phase 5: Polish
```
- Full FPV with sprites
- Audio indicators
- Partial visibility effects
- Fuzzy STT matching
- Prototype scenario (park + waterfall)
```

---

## 12. What This Engine Creates

An ASCII world where:

| Aspect | Experience |
|--------|------------|
| **Exploration** | FPV reveals world through perception |
| **Stealth** | LOS + sound create hide-and-seek gameplay |
| **Combat** | Real-time reactions with voice commands |
| **Social** | NPCs believe rumors, act on memories |
| **Consequence** | Events journal, world remembers |
| **Emergence** | Systems interact, stories happen |

**The player never sees truth. They see beliefs in motion.**
**The world never explains itself. It affords.**
**Time doesn't wait. Hesitation kills.**

---

*End of Unified Schema*
