# ShadowEngine Architecture

## Overview

ShadowEngine is a genre-agnostic procedural storytelling engine for terminal/CLI environments. It generates coherent, replayable narrative experiences using ASCII visuals, simulation systems, and persistent memory.

## Core Design Principles

1. **Memory First** - Nothing meaningful happens without being remembered
2. **Systems Over Scripts** - Characters and worlds obey rules, not dialogue trees
3. **Procedural ≠ Random** - All randomness is constrained by narrative logic
4. **Atmosphere Is Mechanics** - Visuals communicate story state
5. **Player Is a Lens** - Perspective shapes truth; the player filters reality

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                              │
│              (Commands / Choices / Voice* / Keyboard)            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      NARRATIVE ENGINE                            │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ Narrative Spine  │  │    Character     │  │    Moral &    │  │
│  │    Generator     │  │    Simulation    │  │  Consequence  │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       MEMORY BANK                                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ World Memory │  │  Character   │  │    Player Memory     │   │
│  │ (objective)  │  │   Memory     │  │  (perception/bias)   │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ENVIRONMENT SIMULATOR                          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Weather    │  │     Time     │  │  Environmental       │   │
│  │   System     │  │    System    │  │  Pressure/Stakes     │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT LAYER                                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  ASCII Render Engine                      │   │
│  │  (Scenes / Particles / Overlays / Semantic Symbols)       │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Audio Engine (Future)                    │   │
│  │  (TTS Voices / Post-processed Sound Effects)              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

* Voice input is a planned future feature
```

## Data Flow

1. **Input** → Player issues command (keyboard, future: voice)
2. **Parse** → Interaction engine interprets intent (fail-soft parsing)
3. **Evaluate** → Narrative engine checks rules, character states, spine constraints
4. **Update** → Memory bank records what happened (world, character, player layers)
5. **Simulate** → Environment updates (weather, time, pressure)
6. **Render** → ASCII scene reflects new state
7. **Output** → Scene displayed (future: narrated via TTS)

## Module Index

| Module | Purpose | Doc |
|--------|---------|-----|
| Narrative Spine | Hidden story structure & coherence | [01-narrative-spine.md](modules/01-narrative-spine.md) |
| Character Simulation | NPC behavior, psychology, memory | [02-character-simulation.md](modules/02-character-simulation.md) |
| Memory Bank | Three-layer persistent memory system | [03-memory-bank.md](modules/03-memory-bank.md) |
| Environment & Weather | Atmosphere as mechanics | [04-environment-weather.md](modules/04-environment-weather.md) |
| ASCII Renderer | Procedural scene rendering | [05-ascii-renderer.md](modules/05-ascii-renderer.md) |
| Interaction Engine | Input parsing & hotspots | [06-interaction-engine.md](modules/06-interaction-engine.md) |
| Moral & Consequence | Shade-based morality tracking | [07-moral-consequence.md](modules/07-moral-consequence.md) |

## Technical Stack

- **Language**: Python
- **Interface**: Terminal / CMD / PowerShell / Unix shells
- **Dependencies**: Standard library only (core engine)
- **Save System**: JSON memory snapshots
- **Deterministic Seeds**: Replayable story generation
- **Optional AI**: Markov chains or offline LLM hooks for text variation

## Genre Support

The engine is genre-agnostic. Theme packs swap:
- Archetypes & character templates
- Weather physics & effects
- Moral axes & consequence rules
- Dialogue tone & vocabulary

Core systems (memory, simulation, rendering) remain unchanged.

### Example Themes
- **Noir Crime** (1940s detective drama)
- **Cyberpunk** (dystopian investigations)
- **Gothic Horror** (supernatural mysteries)
- **Espionage** (cold war thrillers)
- **Weird Western** (frontier supernatural)
- **Hard Sci-Fi** (space station mysteries)

## Future Systems

See [FUTURE_TTS.md](FUTURE_TTS.md) for planned audio features:
- Voice control input (primary) with keyboard backup
- TTS character voices with personality customization
- Post-TTS sound processing for effects
