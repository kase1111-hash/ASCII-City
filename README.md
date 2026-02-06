# ShadowEngine

**An Emergent ASCII World Engine — LLM-Powered Game Simulation for Natural Language Gaming**

---

## What Is This?

ShadowEngine is an **AI-driven ASCII game engine** and fully reactive, **LLM-powered game** universe where every object, creature, and environmental element functions as an interactive **behavioral circuit** with emergent properties. Built as a **procedural ASCII world** generator, it enables **natural language game interaction** and **emergent storytelling** through AI simulation.

Instead of scripted stories, this **text-based world simulation** engine simulates **world state**, **character psychology**, **environmental physics**, and **player creativity**—allowing **narrative emergence** and **player-driven storytelling** to unfold naturally. Every button, bug, or boulder becomes a potential story seed in a fully reactive sandbox where player creativity literally shapes the game world. Think of it as an **AI dungeon crawler** meets **prose-first game development**.

## Key Features

- **Behavioral Circuits** - Universal interaction model enabling **emergent AI gameplay**
- **LLM-Driven Simulation** - **AI game simulation** with dynamic responses, not pre-scripted outcomes
- **Memory & Rumor Networks** - **Psychological AI architecture** where NPCs remember, share information, evolve
- **ASCII Art Studio** - Player-created art becomes world content through **human-AI collaboration**
- **Sound & Vision Systems** - Audio synthesis, TTS, and atmospheric rendering *(sound propagation planned)*
- **Threat Proximity** - STT voice input with threat response framework *(real-time reaction timing planned)*
- **Zoom Inspection** - Progressive detail reveal with tools
- **Atmospheric Simulation** - Weather, time, and pressure affect everything in this **living world simulation**

## Core Philosophy

**No Pre-Programming**: Player input never follows rigid scripts. This **language-native game architecture** means even trivial actions (poke rock, kick bug) have dynamic consequences driven by **LLM-powered interpretation**.

**Living World**: All entities exist as interactive circuits with **AI emotional continuity**, not static ASCII. Every interaction ripples through the simulation like a **semantic game engine**.

**Player as Creator**: Player-made ASCII art literally shapes the game world through iterative feedback loops—true **cognitive work attribution** for creative contributions.

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
| Modding System | ✓ Complete | 3325 |

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

- **Language**: Python (standard library for core, **LLM API** for brain)
- **Interface**: Terminal / CMD / Shell (STT optional for **voice-controlled gaming**)
- **Save System**: JSON memory snapshots with **cognitive artifact storage**
- **Deterministic**: **Procedural generation** with seeded replay capability
- **Architecture**: **Agent orchestration framework** for NPC coordination
- **Tests**: 3325 tests passing

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

ShadowEngine is not about replacing writers. It's about building **AI-powered interactive fiction** and worlds that remember—where every lie persists, every storm matters, and every ending feels inevitable in hindsight. This is **emergent narrative design** at its core: where every piece of player creativity becomes part of the living world through **intent preservation** and **process legibility**.

---

## Part of the Game Development Ecosystem

ShadowEngine connects to a broader ecosystem of **AI-driven games** and **natural language programming** projects:

### 🎮 Related Game Projects

| Repository | Description |
|------------|-------------|
| [Shredsquatch](https://github.com/kase1111-hash/Shredsquatch) | 3D first-person snowboarding infinite runner — SkiFree spiritual successor |
| [Midnight-pulse](https://github.com/kase1111-hash/Midnight-pulse) | Procedurally generated synthwave night driving experience |
| [Long-Home](https://github.com/kase1111-hash/Long-Home) | Atmospheric narrative Godot game |

### 🤖 Agent-OS Ecosystem

| Repository | Description |
|------------|-------------|
| [Agent-OS](https://github.com/kase1111-hash/Agent-OS) | Natural language operating system for AI agents (NLOS) |
| [synth-mind](https://github.com/kase1111-hash/synth-mind) | NLOS-based agent with psychological modules for emergent AI personality |
| [memory-vault](https://github.com/kase1111-hash/memory-vault) | Sovereign, owner-controlled storage for cognitive artifacts |
| [boundary-daemon](https://github.com/kase1111-hash/boundary-daemon-) | Trust enforcement layer defining AI cognition boundaries |

### 🔗 NatLangChain Ecosystem

| Repository | Description |
|------------|-------------|
| [NatLangChain](https://github.com/kase1111-hash/NatLangChain) | Prose-first, intent-native blockchain for human-readable smart contracts |
| [IntentLog](https://github.com/kase1111-hash/IntentLog) | Git for human reasoning — tracks "why" changes happen via prose commits |
| [mediator-node](https://github.com/kase1111-hash/mediator-node) | LLM mediation layer for semantic matching and negotiation |

---

*Built for terminals. Designed for emergence. Powered by natural language.*
