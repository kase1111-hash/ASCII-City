# ShadowEngine

**A Procedural ASCII Storytelling Game Engine**

---

## What Is This?

ShadowEngine generates coherent, replayable narrative experiences in the terminal using ASCII visuals, procedural systems, and persistent memory.

Instead of scripted stories, it simulates **world state**, **character psychology**, **environmental pressure**, and **moral consequence**—allowing stories to emerge naturally. Each playthrough produces a complete narrative that feels authored, without being prewritten.

## Key Features

- **Memory-Driven Storytelling** - Events persist and affect future interactions
- **Autonomous NPCs** - Characters lie, crack under pressure, remember your actions
- **Atmospheric Simulation** - Weather and time affect gameplay, not just visuals
- **Moral Shades** - No binary good/evil; nuanced consequences
- **Procedural Coherence** - Randomness bounded by narrative logic
- **ASCII Rendering** - Atmospheric scenes with particles and overlays

## Status

**Concept → In Development**

See [ROADMAP.md](docs/ROADMAP.md) for development phases.

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design and data flow |
| [Roadmap](docs/ROADMAP.md) | Phased development plan |
| [Future TTS](docs/FUTURE_TTS.md) | Voice control & audio planning |

### Module Specifications

| Module | Description |
|--------|-------------|
| [01 - Narrative Spine](docs/modules/01-narrative-spine.md) | Hidden story structure |
| [02 - Character Simulation](docs/modules/02-character-simulation.md) | NPC behavior & psychology |
| [03 - Memory Bank](docs/modules/03-memory-bank.md) | Three-layer memory system |
| [04 - Environment](docs/modules/04-environment-weather.md) | Weather & time mechanics |
| [05 - ASCII Renderer](docs/modules/05-ascii-renderer.md) | Scene rendering system |
| [06 - Interaction](docs/modules/06-interaction-engine.md) | Input parsing & hotspots |
| [07 - Moral System](docs/modules/07-moral-consequence.md) | Shade-based consequences |

## Technical

- **Language**: Python (standard library only for core)
- **Interface**: Terminal / CMD / Shell
- **Save System**: JSON memory snapshots
- **Deterministic**: Seeded generation for replay

## Philosophy

> *The strongest stories emerge from systems that remember.*

ShadowEngine is not about replacing writers. It's about building worlds that remember—where every lie persists, every storm matters, and every ending feels inevitable in hindsight.

---

*Built for terminals. Designed for stories.*
