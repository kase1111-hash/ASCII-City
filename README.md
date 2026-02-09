# ShadowEngine

**An Emergent ASCII World Engine — LLM-Powered Game Simulation for Natural Language Gaming**

---

## What Is This?

ShadowEngine is an AI-driven ASCII game engine where locations, dialogue, and interactions are generated dynamically by an LLM (Ollama or OpenAI). Instead of scripted stories, the engine uses natural language parsing and procedural generation to create an open-ended text adventure where the player can go anywhere and talk to anyone.

The long-term goal is systemic emergence: behavioral circuits, NPC rumor networks, and layered memory producing stories no one pre-wrote. Right now the engine delivers LLM-driven exploration and dialogue with a three-layer memory system. See [REFOCUS_PLAN.md](REFOCUS_PLAN.md) for the integration roadmap.

## Key Features

- **LLM-Driven Simulation** - Dynamic responses via Ollama/OpenAI, not pre-scripted outcomes
- **Three-Layer Memory** - World truth, character beliefs, and player knowledge tracked separately
- **Natural Language Input** - Free-form commands parsed by LLM when structured parsing fails
- **Procedural Location Generation** - New areas generated on-the-fly as the player explores
- **NPC Dialogue** - LLM-generated character responses shaped by archetype and game state
- **Atmospheric Simulation** - Weather, time of day, and pressure affect the world
- **Zoom Inspection** - Progressive detail reveal with tools

### Planned (code exists, not yet integrated into game loop)

- **Behavioral Circuits** - Universal entity interaction model via signal processing
- **NPC Intelligence** - Rumor propagation, social networks, subjective NPC memory
- **ASCII Art Studio** - Player-created art editor (deferred)
- **Audio / TTS** - Text-to-speech and ambient audio (deferred)
- **Modding System** - Theme packs, custom scenarios, content registry (deferred)
- **Voice Input** - Speech-to-text command recognition (deferred)

## Core Philosophy

**No Pre-Programming**: Player input is never limited to a fixed verb list. Free-form commands are interpreted by the LLM when structured parsing fails.

**Memory-First**: Every event is recorded in a three-layer memory system (world truth, character beliefs, player knowledge). Nothing meaningful happens without being remembered.

**Systemic Emergence** (in progress): The engine is being refocused to wire behavioral circuits, NPC intelligence, and rumor networks into the game loop so that player actions produce cascading, unscripted consequences.

---

## Status

**Refocusing** — Subsystems are built and tested; now wiring them into the game loop.

| System | Status | Integrated |
|--------|--------|:----------:|
| Game Loop & Commands | Working | Yes |
| LLM Location Generation | Working | Yes |
| LLM NPC Dialogue | Working | Yes |
| Three-Layer Memory | Working | Partial (player only) |
| Environment / Weather | Working | Yes |
| Behavioral Circuits | Tested, isolated | No |
| NPC Intelligence & Rumors | Tested, isolated | No |
| Inspection / Zoom | Working | Yes |
| Audio / TTS | Deferred | -- |
| ASCII Art Studio | Deferred | -- |
| Modding System | Deferred | -- |
| Voice Input (STT) | Deferred | -- |

See [REFOCUS_PLAN.md](REFOCUS_PLAN.md) for the integration roadmap.

---

## Documentation

### Core Documents

| Document | Description |
|----------|-------------|
| [Design](docs/DESIGN.md) | Complete emergent world design vision |
| [Architecture](docs/ARCHITECTURE.md) | System design and data flow |
| [Roadmap](docs/ROADMAP.md) | Phased development plan |
| [Future TTS](docs/FUTURE_TTS.md) | Voice control & audio planning |

### Module Documentation

| Module | Description |
|--------|-------------|
| [Narrative Spine](docs/modules/01-narrative-spine.md) | Hidden story structure |
| [Character Simulation](docs/modules/02-character-simulation.md) | NPC behavior & psychology |
| [Memory Bank](docs/modules/03-memory-bank.md) | Three-layer memory system |
| [Environment](docs/modules/04-environment-weather.md) | Weather & time mechanics |
| [ASCII Renderer](docs/modules/05-ascii-renderer.md) | Scene rendering system |
| [Interaction Engine](docs/modules/06-interaction-engine.md) | Input parsing & affordances |
| [Behavioral Circuits](docs/modules/08-behavioral-circuits.md) | Universal entity interaction model |

Specification documents are in [docs/specs/](docs/specs/).

---

## Technical

- **Language**: Python 3.10+ (standard library for core, LLM API for generation)
- **LLM Backend**: Ollama (local, default) or OpenAI API
- **Interface**: Terminal / CMD / Shell
- **Save System**: JSON memory snapshots
- **Dependencies**: Zero for core game (pytest for testing)
- **Tests**: ~2,000 active tests (deferred modules excluded)

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

ShadowEngine is about building worlds that remember — where every lie persists, every storm matters, and every ending feels inevitable in hindsight.

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
