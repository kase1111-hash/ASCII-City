# ShadowEngine

**An Emergent ASCII World Engine — LLM-Powered Game Simulation for Natural Language Gaming**

---

## What Is This?

ShadowEngine is an AI-driven ASCII game engine where locations, dialogue, and interactions are generated dynamically by an LLM (Ollama or OpenAI). Instead of scripted stories, the engine uses natural language parsing and procedural generation to create an open-ended text adventure where the player can go anywhere and talk to anyone.

The long-term goal is systemic emergence: behavioral circuits, NPC rumor networks, and layered memory producing stories no one pre-wrote. The engine now delivers LLM-driven exploration and dialogue backed by a three-layer memory system, signal-driven behavioral circuits, and NPC rumor propagation. See [REFOCUS_PLAN.md](REFOCUS_PLAN.md) for the integration roadmap.

## Key Features

- **LLM-Driven Simulation** - Dynamic responses via Ollama/OpenAI, not pre-scripted outcomes
- **Three-Layer Memory** - World truth, character beliefs, and player knowledge tracked separately
- **Natural Language Input** - Free-form commands parsed by LLM when structured parsing fails
- **Procedural Location Generation** - New areas generated on-the-fly as the player explores
- **NPC Dialogue** - LLM-generated character responses shaped by archetype and game state
- **Atmospheric Simulation** - Weather, time of day, and pressure affect the world
- **Behavioral Circuits** - Objects respond to signals (kick, push, press) with cascading physical effects
- **NPC Intelligence** - Rumor propagation, gossip between NPCs, and subjective NPC memory

### Planned (code exists, not yet integrated into game loop)

- **Zoom Inspection** - Progressive detail reveal with tools
- **ASCII Art Studio** - Player-created art editor (deferred)
- **Audio / TTS** - Text-to-speech and ambient audio (deferred)
- **Modding System** - Theme packs, custom scenarios, content registry (deferred)
- **Voice Input** - Speech-to-text command recognition (deferred)

## Core Philosophy

**No Pre-Programming**: Player input is never limited to a fixed verb list. Free-form commands are interpreted by the LLM when structured parsing fails.

**Memory-First**: Every event is recorded in a three-layer memory system (world truth, character beliefs, player knowledge). Nothing meaningful happens without being remembered.

**Systemic Emergence**: Behavioral circuits, NPC intelligence, and rumor networks are wired into the game loop — NPCs witness player actions, form subjective memories, and spread rumors, while interactive objects react to signals with cascading physical effects.

---

## Status

**Refocusing** — Core subsystems are wired into the game loop; remaining modules are tested but isolated.

| System | Status | Integrated |
|--------|--------|:----------:|
| Game Loop & Commands | Working | Yes |
| LLM Location Generation | Working | Yes |
| LLM NPC Dialogue | Working | Yes |
| Three-Layer Memory | Working | Yes |
| Environment / Weather | Working | Yes |
| Behavioral Circuits | Working | Yes (used in Dockside Job scenario) |
| NPC Intelligence & Rumors | Working | Yes |
| Inspection / Zoom | Tested, isolated | No |
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
| [Concepts](docs/CONCEPTS.md) | Core mental model and key abstractions |
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
| [Moral & Consequence](docs/modules/07-moral-consequence.md) | Shade-based morality tracking |
| [Behavioral Circuits](docs/modules/08-behavioral-circuits.md) | Universal entity interaction model |
| [Tile Grid](docs/modules/09-tile-grid.md) | World structure and affordances |
| [Perception Systems](docs/modules/10-perception-systems.md) | Sound, vision, threat proximity |
| [ASCII Art Studio](docs/modules/11-ascii-studio.md) | Player creativity integration (deferred) |
| [Art Creation Framework](docs/modules/12-art-creation-framework.md) | Art asset system (deferred) |

Specification documents are in [docs/specs/](docs/specs/).

---

## Technical

- **Language**: Python 3.10+ (standard library for core, LLM API for generation)
- **LLM Backend**: Ollama (local, default) or OpenAI API
- **Interface**: Terminal / CMD / Shell
- **Save System**: JSON memory snapshots
- **Dependencies**: Zero for core game (pytest for testing)
- **Tests**: ~2,200 active tests (deferred modules excluded)

---

## Getting Started

### Prerequisites

- Python 3.10 or higher

### Installation

```bash
# Clone the repository
git clone https://github.com/kase1111-hash/ASCII-City.git
cd ASCII-City

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Game

```bash
python main.py
```

The game requires an LLM backend for dynamic generation. By default it connects to [Ollama](https://ollama.ai/) at `http://localhost:11434` using the `llama3.2` model. Without Ollama running, the game falls back to template-based responses.

### Running Tests

```bash
pytest                           # All active tests (~2,200)
pytest -v                        # Verbose output
pytest -m unit                   # Unit tests only
pytest -m integration            # Integration tests only
pytest --cov=shadowengine        # With coverage report
```

On Windows, you can also use `build.bat` (setup) and `run.bat` (run game).

---

## Quick Example

```
> kick the rusty button

The button sparks briefly, then sticks halfway. A grinding sound
echoes through the shaft. The elevator shudders but doesn't move.

A rat in the corner freezes, ears perked toward the noise.

> examine the button

The button housing is corroded, green patina spreading
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
