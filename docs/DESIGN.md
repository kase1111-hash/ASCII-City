# Emergent ASCII World - Complete Design

## Overview

A fully reactive, LLM-driven ASCII universe where every object, creature, and environmental element functions as an interactive "behavioral circuit" with emergent properties. The world is procedural, persistent, and continuously evolving based on player actions, NPC memory, and systemic simulations.

---

## Core Design Philosophy

**No Pre-Programming**: Player input never follows rigid scripts. Even trivial actions (poke rock, kick bug) have dynamic consequences driven by LLM interpretation.

**Living Simulation**: All entities "exist" as interactive circuits, not static ASCII. Every button, bug, or boulder becomes a potential story seed.

**Player Creativity Matters**: Player-created ASCII art literally shapes the game world through iterative feedback loops in a fully reactive sandbox.

---

## World Structure & Mechanics

### Grid-Based Tile System

The world is built on a tile grid where each tile carries rich information:

```python
Tile {
    position: (x, y, z)           # Including Z-level/height
    terrain_type: str             # rock, water, soil, metal, void
    affordances: list[str]        # Inherited interaction possibilities
    entities: list[Entity]        # Objects/creatures present
    environment: {
        fluid: bool               # Contains liquid/gas
        temperature: float        # Affects behavior
        sound_level: float        # Sound propagation modifier
    }
}
```

### Affordance Inheritance

Tiles pass default affordances to contained objects unless overridden:

| Terrain | Default Affordances |
|---------|---------------------|
| Rock | climbable, breakable, solid |
| Water | swimmable, splashable, drownable |
| Forest | climbable, flammable, harvestable |
| Metal | conductive, climbable, resonant |
| Void | fallable, echoing |

**Entity Override**: Objects can extend or override tile affordances:
- Trapdoor in rock = climbable + triggerable
- Boat in water = removes drownable, adds rideable
- Torch in forest = adds lit, reveals hidden

---

## Universal Behavioral Circuit Model

Every interactive entity in the world uses this unified structure:

```python
BehaviorCircuit {
    id: str
    type: enum                    # mechanical, biological, environmental

    # Input Signals (what triggers this entity)
    input_signals: [
        "press", "kick", "poke", "look", "listen", "say",
        "heat", "wet", "electric", "proximity"
    ]

    # Processing (LLM-evaluated)
    process: {
        context: dict             # Current world state
        history: list             # Past interactions
        personality: dict         # For biological entities
    }

    # Output Signals (what this entity produces)
    output_signals: [
        "move", "scurry", "collapse", "play_sound",
        "change_state", "emit", "trigger"
    ]

    # Persistent State
    state: {
        health: float
        power: float
        fatigue: float
        trust: float              # For NPCs
        last_interaction: timestamp
    }

    # What can be done to/with this entity
    affordances: list[str]
}
```

### Application Examples

**Mechanical Circuits**:
- Elevator buttons: spark/stick/fail based on age and condition
- Gears: grind/spin/jam based on lubrication and wear
- Locks: pick/break/rust based on material and exposure

**Biological Circuits**:
- Rats: scurry/bite/freeze based on fear, hunger, trust
- NPCs: talk/flee/attack based on memory, mood, relationships
- Plants: grow/wilt/spread based on water, light, season

**Environmental Circuits**:
- Waterfalls: splash/echo/trigger hazards based on physics
- Cliffs: crumble/support/reveal based on weight and erosion
- Wind: push/carry/extinguish based on intensity and obstacles

---

## Interaction Systems

### Action Categories

| Category | Actions | Notes |
|----------|---------|-------|
| **Physical** | kick, push, pull, climb, throw, press | Affected by strength, encumbrance |
| **Auditory** | shout, listen, mimic, whistle | Propagates through sound system |
| **Visual** | look, inspect, tag, zoom | Uses line-of-sight system |
| **Creative** | draw, engrave, write, code | ASCII Studio integration |
| **Social** | talk, trade, bribe, threaten | Uses NPC memory/trust |
| **Combat** | attack, dodge, parry, flee | Proximity-based resolution |

### Threat & Proximity Dynamics

```python
ThreatSystem {
    # Dynamic threat radius per entity
    calculate_threat_radius(entity) -> float

    # Reaction timing (STT enables "run away" before threat reaches player)
    evaluate_reaction_time(player, threat) -> bool

    # NPC/creature reactions influenced by:
    reaction_factors: {
        personality_traits: dict
        experience_memory: list
        environmental_context: dict
        random_emergence: float    # Unpredictability factor
    }

    # Combined with perception systems
    line_of_sight: LineOfSightSystem
    sound_propagation: SoundSystem
}
```

### Sound Propagation System

Sound travels tile-to-tile with realistic physics:

```
Source → Adjacent Tiles → Distance Falloff → Obstacle Modulation

Examples:
- Scream (~~~) muffled by waterfall: 100% → 30%
- Footsteps on metal: propagates far, alerts guards
- Whisper in cave: creates echoes, confuses direction
```

**Sound Properties**:
- Volume (loudness at source)
- Frequency (pitch affects travel through materials)
- Directionality (focused vs. omnidirectional)
- Duration (brief vs. sustained)

**Applications**:
- Alerts NPCs and animals
- Enables acoustic puzzles
- Allows eavesdropping mechanics
- Creates environmental storytelling

### Line-of-Sight System

Vision is blocked by tiles and affected by lighting:

```python
LineOfSight {
    # Tiles can block vision
    blocking_tiles: ["wall", "rock", "dense_foliage"]

    # Detection radius altered by:
    visibility_modifiers: {
        lighting: float           # 0.0 (dark) to 1.0 (bright)
        weather: float            # fog, rain reduce visibility
        movement: float           # moving targets easier to spot
        camouflage: float         # hiding skill/equipment
    }

    # Affects:
    - Combat targeting
    - NPC awareness of player
    - Rumor propagation (witnessing events)
    - Environmental puzzle solutions
}
```

---

## ASCII Art Studio

A revolutionary system where player creativity becomes world content.

### Studio Mechanics

```python
ASCIIArt {
    id: str
    tiles: char[][]               # 2D character array

    # Semantic tags for world integration
    tags: {
        object_type: str          # tree, rock, NPC, item
        interaction_type: str     # climbable, collectible, hideable
        environment_type: str     # forest, urban, cave, river
    }

    player_id: str                # Creator
    version: int                  # Iteration count

    usage_stats: {
        times_rendered: int
        interactions_triggered: int
        player_rating: float
    }
}
```

### Creation Workflow

1. **Enter Studio**: Player visits special studio location in ASCII world
2. **Draw**: Create ASCII art (single tiles, multi-tile structures, creatures, textures)
3. **Tag**: Assign semantic categories
   - Object: tree, rock, waterfall, NPC, item, structure
   - Interaction: climbable, hideable, collectible, dangerous
   - Environment: forest, urban, cave, river, mountain, dungeon
4. **LLM Interpretation**: System interprets meaning and generates procedural variants
5. **World Integration**: Generator injects variants dynamically with appropriate affordances

### Iterative Learning Loop

```
Player draws → Game uses it → LLM observes interactions
                    ↓
        LLM suggests tweaks → Player modifies
                    ↓
        Game adapts → Continuous improvement
```

**Feedback Mechanisms**:
- Usage frequency tracking
- Interaction success rates
- Player engagement metrics
- Community ratings (collaborative mode)

### Collaborative Gallery Mode

- Visit other players' studio worlds
- Import/export assets between games
- Community feedback tags enhance procedural variety
- Player creativity becomes actual world content, not just cosmetic

---

## NPC Systems

### Persistent Memory Architecture

```python
NPCMemory {
    # Direct interactions with player
    player_interactions: [
        {timestamp, action, outcome, emotional_impact}
    ]

    # Observed events (witnessed, not participated)
    observed_events: [
        {timestamp, location, actors, event_type, significance}
    ]

    # Information from other NPCs
    rumors: [
        {source, content, credibility, timestamp}
    ]

    # Learned behaviors
    learned_patterns: {
        player_tendencies: dict
        environmental_dangers: list
        social_hierarchies: dict
    }
}
```

### Rumor Propagation Network

NPCs share information dynamically:

```
Event occurs → Witnesses remember → Spread to connected NPCs
                                           ↓
                                    Credibility decay
                                           ↓
                              Influences: trust, fear, trade, aggression
                                           ↓
                              Emergent storylines form
```

**Rumor Properties**:
- Source credibility (reliable NPCs trusted more)
- Time decay (old rumors less influential)
- Corroboration (multiple sources increase impact)
- Distortion (each retelling may change details)

---

## Inspection & Zoom System

### Natural Language Input Examples

**Basic Inspection**:
- "Look at the statue"
- "Examine the rocks by the river"

**Incremental Zooming**:
- "Look closer at the carvings"
- "Zoom in on the gears"

**Tool-Based Inspection**:
- "Use magnifying glass to inspect the insect"
- "Bring telescope up to distant tower"

**Context-Aware**:
- "Check behind the waterfall"
- "Look under the table"
- "Focus on the glowing glyphs"

### LLM Processing Pipeline

```
1. Object Identification
   Parse sentence → Identify target → Look up in world context

2. Tool Consideration
   Check player inventory → Adjust detail level based on tool affordances

3. Detail Scaling
   Zoom 1: coarse outline → Zoom 2: medium detail → Zoom 3: fine detail

4. Persistent State
   Track current zoom level per object for additive inspection

5. Dynamic Recalculation
   Adjust for tool switches, distance changes, player movement
```

### Output Rendering

- ASCII art dynamically refines with zoom level
- Additional flavor text generated contextually
- Recursive zooming bounded by:
  - Tool resolution limits
  - Player perception capabilities
  - World detail availability
- LLM can procedurally invent micro-details as needed

---

## Player Input & Real-Time Simulation

### Input Methods

| Method | Use Case | Speed |
|--------|----------|-------|
| **STT (Speech-to-Text)** | Combat, stealth, urgent actions | Fast |
| **Natural Language Text** | Exploration, dialogue, puzzles | Medium |
| **Quick Commands** | Common actions | Fastest |

### Interaction Pipeline

```
1. Player Input (STT or typed)
        ↓
2. System Query to LLM:
   - Current entity state
   - World context (adjacent tiles, physics, previous events)
   - Player intent interpretation
        ↓
3. LLM Response:
   - Behavior signal(s)
   - State updates
        ↓
4. World Update:
   - Entity states change
   - Environment reacts
        ↓
5. Render:
   - ASCII visual feedback
   - Sound effects (if enabled)
        ↓
6. History Log:
   - Feed NPC memory
   - Update rumor networks
   - Track for emergent storytelling
```

---

## Procedural World Generation

### LLM Integration

The LLM serves as the world's "brain", generating:

- **Terrain**: Biomes, structures, hazards, weather patterns
- **History**: Past events, NPC backstories, cultural context
- **Behavior**: Entity reactions through behavioral circuits
- **Consequences**: State evolution from player actions
- **Story**: Emergent narrative from accumulated events

### World Loop Summary

```
Player interacts (STT or text)
        ↓
LLM evaluates: input + tile context + entity state + NPC memory + threat proximity
        ↓
Outputs behavior signals + updates world state
        ↓
ASCII + sound renders immediate feedback
        ↓
Changes persist: NPC memory, rumor networks, procedural world evolution
        ↓
Player-created ASCII art feeds back into world asset pool
        ↓
[Loop continues]
```

---

## Emergent Combat & Hazards

### Physics Simulation

Abstract but meaningful body-part and physics simulation:

```python
CombatResolution {
    # Body part targeting
    targets: ["head", "torso", "arms", "legs"]

    # Environmental factors
    terrain_modifiers: dict       # Footing, cover
    visibility_effects: dict      # Lighting, obscurement

    # Weapon/tool considerations
    reach: float
    damage_type: str              # blunt, sharp, elemental

    # Dynamic reactions
    npc_reactions: based on personality + experience
    animal_reactions: based on instinct + fear_level
}
```

### Environmental Hazards

Complex interactions resolved by LLM:

**Example Chain**:
```
Player pushes boulder
    → Boulder rolls
        → Triggers pressure plate trap
            → Trap snaps
                → Injures nearby rat
                    → Rat squeals (sound propagation)
                        → Guards alerted
                            → Water pipe breaks
                                → Water flow changes
                                    → New paths available
```

---

## System Integration Map

```
┌──────────────────────────────────────────────────────────────────────┐
│                           INPUT LAYER                                 │
│                  (STT / Natural Language / Quick Commands)            │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        LLM BRAIN CORE                                 │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐    │
│  │   Intent     │  │   Context    │  │   Behavior Circuit       │    │
│  │   Parser     │→ │   Resolver   │→ │   Evaluator              │    │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘    │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      SIMULATION LAYER                                 │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐    │
│  │   Tile       │  │   Entity     │  │   Physics                │    │
│  │   Grid       │  │   Manager    │  │   (Sound/Light/Motion)   │    │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘    │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐    │
│  │   NPC        │  │   Rumor      │  │   Threat                 │    │
│  │   Memory     │  │   Network    │  │   Assessment             │    │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘    │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       OUTPUT LAYER                                    │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                    ASCII Render Engine                        │    │
│  │    (Scenes / Particles / Zoom Levels / Player Art Assets)    │    │
│  └──────────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                     Audio Engine                              │    │
│  │    (TTS / Sound Effects / Ambient / Music)                    │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     PLAYER CREATIVITY LOOP                            │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                    ASCII Art Studio                           │    │
│  │    (Create → Tag → Submit → World Integration → Feedback)     │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase A: Behavioral Circuit Foundation
- Implement universal BehaviorCircuit model
- Create tile grid system with affordances
- Basic LLM integration for entity evaluation

### Phase B: Perception Systems
- Sound propagation engine
- Line-of-sight calculations
- Threat proximity dynamics

### Phase C: NPC Intelligence
- Persistent memory system
- Rumor network propagation
- Trust and relationship tracking

### Phase D: ASCII Art Studio
- Drawing interface
- Semantic tagging system
- World asset integration
- LLM interpretation for variants

### Phase E: Full Integration
- STT input support
- Zoom/inspection system
- Emergent combat resolution
- Complete world loop

---

## Appendix: Design Decisions

### Why Behavioral Circuits?

Unified model enables:
1. Consistent interaction patterns across all entities
2. LLM can reason about any entity the same way
3. Emergent behavior from simple rules
4. Easy extension for new entity types

### Why Player-Created Art?

1. Infinite content without dev effort
2. Player investment in world
3. Community building through sharing
4. Unique worlds per player

### Why LLM-Driven?

1. Handles edge cases humans couldn't anticipate
2. Natural language feels more immersive
3. Enables true emergence from simple systems
4. Scales complexity without exponential scripting

---

*The world remembers. The world reacts. The world is yours to shape.*
