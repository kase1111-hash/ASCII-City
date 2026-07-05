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
- **Look Closer** - Progressive zoom on anything: four depth levels of LLM-generated detail, tool-gated magnification, hidden discoveries, and darkness that actually matters
- **Discoveries Become the World** - A find at high zoom can materialize as a new object in the scene, itself inspectable and collectible
- **Evidence-Driven Interrogation** - A case file tracks every lead and clue; 'show \<evidence\>' puts a discovery on the table mid-conversation and applies real pressure
- **The World Fights Back** - Find evidence in front of witnesses and leave it behind, and the culprit gets to it first. The absence becomes a clue of its own
- **Sensory Tools** - UV light exposes scrubbed stains, a stethoscope hears hidden mechanisms, a mirror sees behind things — each tool generates its own kind of detail on any object
- **Clues Add Up** - Accumulate enough evidence at the right place and the case's hidden leads click together, even from clues the LLM invented on the spot

### Planned (code exists, not yet integrated into game loop)

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
> examine the desk

A folder sits on top: 'WEBB, Marcus - Deceased'. Body found in
the alley behind O'Malley's Bar. No witnesses... yet.

  (Something about your desk might reward a closer look. Try 'look closer'.)

> look closer at the desk

  [Zoom 2 ##--] DETAILED VIEW -- Your Desk
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    The desktop is scarred with overlapping ring stains and a fan
    of paper cuts in the leather blotter. The brass drawer pull
    hangs slightly loose.

    You could focus on: the loose drawer pull, the leather blotter

    (You could look closer still.)

> look closer

  [Zoom 3 ###-] CLOSE INSPECTION -- Your Desk
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Up close, the wood grain around the lock plate is scored with
    fresh scratches - bright, unweathered wood shows through the
    varnish.

    (Finer detail would take a magnifying glass.)

  DISCOVERED: Fresh pry marks around the desk lock -
  someone searched this desk recently.

> use magnifying glass on the desk

  [Zoom 4 ####] MAGNIFIED VIEW -- Your Desk
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Under the lens, gray fibers are caught in the lock plate
    screws - wool, expensive weave. Whoever pried at this drawer
    wore fine gloves.
```

Every object in the world supports this: detail layers are generated
by the LLM on first look and then remembered, so the world stays
consistent. Depth is tool-gated (a magnifying glass unlocks the finest
level), darkness blocks close inspection without a light, and NPCs who
watch you scrutinize something will remember it — and talk.

Discoveries feed the whole detective loop. A find at high zoom can
materialize as a new hotspot in the scene (that wire recorder behind
the baseboard is now an object you can take). Everything you've
gathered lives in the case file:

```
> case

  ============================ CASE FILE ============================
  THE CASE:
    A body was found in the alley behind O'Malley's Bar...

  LEADS (1/4 uncovered):
    [X] Someone saw the victim with another person
    [ ] ??? — Examine the alley carefully

  EVIDENCE (2):
    - Fresh pry marks around the desk lock [close inspection; office]
    - A wire recorder, still warm [close inspection of Your Desk; office]
  ===================================================================

> talk to the councilman
> show wire recorder

  You lay it out for Councilman Vincent Harrow: a wire recorder,
  still warm...

Councilman Harrow says nervously:
  "You... where did you get that? I've never seen it before in my life."
```

Showing hard evidence applies interrogation pressure — enough of it
and suspects crack.

And the city pushes back. Find something incriminating while someone's
watching, then leave it uncollected? Word travels. Come back and it's
gone — but the theft itself is evidence, recorded in world memory as
truth whether or not you ever pin it on them:

```
> (returning to your office)

  Something's off. The Black Box is gone — someone got here
  before you. They knew you'd found it.

  DISCOVERED: The Black Box was taken. Someone is covering
  their tracks.
```

Collect evidence fast, or investigate when no one is watching.

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
