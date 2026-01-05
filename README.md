# ShadowEngine

**An Emergent ASCII World Engine**

---

## What Is This?

ShadowEngine is a fully reactive, LLM-driven ASCII universe where every object, creature, and environmental element functions as an interactive **behavioral circuit** with emergent properties.

Instead of scripted stories, it simulates **world state**, **character psychology**, **environmental physics**, and **player creativity**—allowing stories to emerge naturally. Every button, bug, or boulder becomes a potential story seed in a fully reactive sandbox where player creativity literally shapes the game world.

## Key Features

- **Behavioral Circuits** - Universal interaction model for all entities
- **LLM-Driven Simulation** - Dynamic responses, not pre-scripted outcomes
- **Memory & Rumor Networks** - NPCs remember, share information, evolve
- **ASCII Art Studio** - Player-created art becomes world content
- **Sound & Vision Systems** - Realistic propagation for emergent gameplay
- **Threat Proximity** - Real-time STT reactions enable urgent actions
- **Zoom Inspection** - Progressive detail reveal with tools
- **Atmospheric Simulation** - Weather, time, and pressure affect everything

## Core Philosophy

**No Pre-Programming**: Player input never follows rigid scripts. Even trivial actions (poke rock, kick bug) have dynamic consequences driven by LLM interpretation.

**Living World**: All entities exist as interactive circuits, not static ASCII. Every interaction ripples through the simulation.

**Player as Creator**: Player-made ASCII art literally shapes the game world through iterative feedback loops.

---

## Status

**All 10 Phases Complete** - Full engine implementation with modding support

| System | Status | Tests |
|--------|--------|-------|
| Core Foundation | ✓ Complete | 274 |
| Simulation Depth | ✓ Complete | 462 |
| Polish & Content | ✓ Complete | 969 |
| Emergent World | ✓ Complete | ~1200 |
| ASCII Art Studio | ✓ Complete | ~1500 |
| STT & Real-Time | ✓ Complete | 1673 |
| NPC Intelligence | ✓ Complete | ~1800 |
| Inspection & Zoom | ✓ Complete | ~2000 |
| Audio & TTS | ✓ Complete | 2373 |
| Modding System | ✓ Complete | 2631 |

See [ROADMAP.md](docs/ROADMAP.md) for development phases.

---

## Documentation

### Core Documents

| Document | Description |
|----------|-------------|
| [Design](docs/DESIGN.md) | Complete emergent world design vision |
| [Architecture](docs/ARCHITECTURE.md) | System design and data flow |
| [Roadmap](docs/ROADMAP.md) | Phased development plan |
| [Future TTS](docs/FUTURE_TTS.md) | Voice control & audio planning |

### System Specifications

| System | Description |
|--------|-------------|
| [Behavioral Circuits](docs/modules/08-behavioral-circuits.md) | Universal entity interaction model |
| [Tile Grid](docs/modules/09-tile-grid.md) | World structure and affordances |
| [Perception Systems](docs/modules/10-perception-systems.md) | Sound, vision, threat proximity |
| [ASCII Art Studio](docs/modules/11-ascii-studio.md) | Player creativity integration |
| [Art Creation Framework](docs/modules/12-art-creation-framework.md) | Static vs dynamic art, LLM-assisted scene generation |

### Module Specifications

| Module | Description |
|--------|-------------|
| [01 - Narrative Spine](docs/modules/01-narrative-spine.md) | Hidden story structure |
| [02 - Character Simulation](docs/modules/02-character-simulation.md) | NPC behavior & psychology |
| [03 - Memory Bank](docs/modules/03-memory-bank.md) | Three-layer memory system |
| [04 - Environment](docs/modules/04-environment-weather.md) | Weather & time mechanics |
| [05 - ASCII Renderer](docs/modules/05-ascii-renderer.md) | Scene rendering system |
| [06 - Interaction](docs/modules/06-interaction-engine.md) | Input parsing & affordances |
| [07 - Moral System](docs/modules/07-moral-consequence.md) | Shade-based consequences |

---

## Technical

- **Language**: Python (standard library for core, LLM API for brain)
- **Interface**: Terminal / CMD / Shell (STT optional)
- **Save System**: JSON memory snapshots
- **Deterministic**: Seeded generation for replay
- **Tests**: 2631 tests passing

---

## Quick Example

```
> kick the rusty button

The button sparks briefly, then sticks halfway. A grinding sound
echoes through the shaft. The elevator shudders but doesn't move.

A rat in the corner freezes, ears perked toward the noise.

> look closer at the button

[Zoom 1] The button housing is corroded, green patina spreading
across the brass. Wires peek through a crack in the casing.

> use screwdriver on button

You pry open the casing. The wiring inside is a mess of splices
and exposed copper. One wire leads to a suspicious black box
that wasn't part of the original installation...
```

---

## Philosophy

> *The world remembers. The world reacts. The world is yours to shape.*

ShadowEngine is not about replacing writers. It's about building worlds that remember—where every lie persists, every storm matters, and every ending feels inevitable in hindsight. And now, where every piece of player creativity becomes part of the living world.

---

*Built for terminals. Designed for emergence.*
