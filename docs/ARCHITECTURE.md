# ShadowEngine Architecture

## Overview

ShadowEngine is a fully reactive, LLM-driven ASCII universe where every object, creature, and environmental element functions as an interactive "behavioral circuit" with emergent properties. The world is procedural, persistent, and continuously evolving based on player actions, NPC memory, and systemic simulations.

> For the complete design vision, see [DESIGN.md](DESIGN.md)

## Core Design Principles

1. **Memory First** - Nothing meaningful happens without being remembered
2. **Systems Over Scripts** - Characters and worlds obey rules, not dialogue trees
3. **Behavioral Circuits** - All entities use a unified interaction model
4. **Procedural ≠ Random** - All randomness is constrained by narrative logic
5. **Atmosphere Is Mechanics** - Visuals communicate story state
6. **Player Is Creator** - Player-made art becomes world content

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                           INPUT LAYER                                 │
│              (STT / Natural Language / Quick Commands)                │
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

## Universal Behavioral Circuit Model

Every interactive entity uses this unified structure:

```python
BehaviorCircuit {
    id: str
    type: enum                    # mechanical, biological, environmental

    input_signals: list           # What triggers this entity
    process: LLMEvaluation        # Context + history + personality
    output_signals: list          # What this entity produces
    state: dict                   # Health, power, fatigue, trust
    affordances: list[str]        # Possible interactions
}
```

**Examples**:
- **Mechanical**: Elevator buttons that spark/stick/fail based on age
- **Biological**: Rats that scurry/bite/freeze based on fear, hunger, trust
- **Environmental**: Waterfalls that splash/echo/trigger hazards

> See [DESIGN.md](DESIGN.md) for complete behavioral circuit specification

---

## Data Flow

1. **Input** → Player issues command (STT, text, or quick command)
2. **Parse** → LLM interprets intent with context awareness
3. **Evaluate** → Behavioral circuits process signals through LLM
4. **Update** → Entity states change, world reacts
5. **Memory** → NPC memory and rumor networks update
6. **Simulate** → Physics propagation (sound, light, motion)
7. **Render** → ASCII scene reflects new state with zoom levels
8. **Output** → Scene displayed, sound generated

---

## Core Systems

### Tile Grid System

World built on tiles with rich properties:

| Property | Description |
|----------|-------------|
| Terrain Type | rock, water, soil, metal, void |
| Z-Level | Height for multi-level environments |
| Affordances | Inherited interaction possibilities |
| Entities | Objects and creatures present |
| Environment | Fluid, temperature, sound propagation |

### Perception Systems

| System | Purpose |
|--------|---------|
| Sound Propagation | Tile-to-tile sound transmission |
| Line of Sight | Vision blocking and detection |
| Threat Proximity | Dynamic threat radius calculation |

### NPC Intelligence

| Component | Function |
|-----------|----------|
| Persistent Memory | Tracks all player interactions |
| Rumor Network | NPCs share information dynamically |
| Trust/Fear Modeling | Relationships affect behavior |

---

## Module Index

| Module | Purpose | Doc |
|--------|---------|-----|
| Narrative Spine | Hidden story structure & coherence | [01-narrative-spine.md](modules/01-narrative-spine.md) |
| Character Simulation | NPC behavior, memory, psychology | [02-character-simulation.md](modules/02-character-simulation.md) |
| Memory Bank | Three-layer persistent memory | [03-memory-bank.md](modules/03-memory-bank.md) |
| Environment & Weather | Atmosphere as mechanics | [04-environment-weather.md](modules/04-environment-weather.md) |
| ASCII Renderer | Procedural scene & zoom rendering | [05-ascii-renderer.md](modules/05-ascii-renderer.md) |
| Interaction Engine | Input parsing & affordances | [06-interaction-engine.md](modules/06-interaction-engine.md) |
| Moral & Consequence | Shade-based morality tracking | [07-moral-consequence.md](modules/07-moral-consequence.md) |

---

## ASCII Art Studio

Player creativity becomes world content:

1. **Create**: Draw ASCII art in special studio location
2. **Tag**: Assign semantic categories (object type, interactions, environment)
3. **Submit**: LLM interprets meaning and generates variants
4. **Integrate**: World generator injects assets with appropriate affordances
5. **Feedback**: Usage stats improve future generation

> See [DESIGN.md](DESIGN.md) for complete studio specification

---

## Technical Stack

- **Language**: Python
- **Interface**: Terminal / CMD / Shell (STT optional)
- **Dependencies**: Standard library (core), LLM API (brain)
- **Save System**: JSON memory snapshots
- **Deterministic Seeds**: Replayable world generation

---

## Genre Support

The engine is genre-agnostic. Theme packs swap:
- Archetypes & character templates
- Weather physics & effects
- Moral axes & consequence rules
- Dialogue tone & vocabulary
- ASCII art asset pools

Core systems (behavioral circuits, memory, simulation, rendering) remain unchanged.

### Example Themes
- **Noir Crime** (1940s detective drama)
- **Cyberpunk** (dystopian investigations)
- **Gothic Horror** (supernatural mysteries)
- **Espionage** (cold war thrillers)
- **Weird Western** (frontier supernatural)
- **Hard Sci-Fi** (space station mysteries)

---

## Related Documentation

- [DESIGN.md](DESIGN.md) - Complete emergent world design
- [ROADMAP.md](ROADMAP.md) - Development phases
- [FUTURE_TTS.md](FUTURE_TTS.md) - Voice control & audio planning
