# SHADOWENGINE

*A Procedural ASCII Storytelling Game Engine*

---

## What Is ShadowEngine?

**ShadowEngine** is a lightweight, terminal-based storytelling game engine designed to generate **coherent, replayable narrative experiences** using ASCII art, procedural simulation, and persistent memory.

Instead of scripting fixed stories, ShadowEngine simulates **world state, character psychology, environmental pressure, and moral consequence**, allowing stories to *emerge* naturally. Each playthrough produces a complete, internally consistent narrative that feels authored—without being prewritten.

The engine is optimized for command-line interfaces (CMD, PowerShell, Unix terminals) and draws inspiration from classic text adventures, Sierra-style point‑and‑click games, roguelikes, and modern AI narrative systems.

---

## Why ShadowEngine Exists

Traditional narrative games:

* Exhaust content quickly
* Require heavy manual authoring
* Offer limited replayability

Modern AI text games:

* Forget past events
* Produce incoherent plots
* Lack causal structure

**ShadowEngine bridges this gap** by separating *story structure* from *story expression* and grounding all generation in memory-backed systems.

---

## Design Philosophy

1. **Memory First** – Nothing meaningful happens without being remembered.
2. **Systems Over Scripts** – Characters and worlds obey rules, not dialogue trees.
3. **Procedural ≠ Random** – All randomness is constrained by narrative logic.
4. **Atmosphere Is Mechanics** – Visuals communicate story state.
5. **Player Is a Lens** – Perspective shapes truth.

---

## Core Engine Architecture

```
Input (Commands / Choices)
        ↓
Narrative Engine (Story Logic)
        ↓
Memory Bank (World / Character / Player)
        ↓
Environment Simulator (Weather / Time)
        ↓
ASCII Render Engine (Scenes / Particles)
```

Each layer feeds the next, ensuring causal continuity and emergent storytelling.

---

## Key Modules

### 1. Narrative Spine Generator

At game start, the engine generates a hidden **Narrative Spine**:

* Case type or central conflict
* True resolution
* Red herrings
* Required revelations
* Twist probabilities

This guarantees coherence regardless of procedural variation.

---

### 2. Character Simulation Engine

Each NPC is an autonomous narrative agent with:

* Archetype
* Secret truth
* Public lie
* Motivations (fear, greed, loyalty)
* Trust thresholds
* Memory of player actions

NPC behavior evolves over time based on pressure and memory.

---

### 3. Memory Bank System (Core Innovation)

ShadowEngine maintains three parallel memory layers:

| Memory Layer     | Description                     |
| ---------------- | ------------------------------- |
| World Memory     | Objective events that occurred  |
| Character Memory | What each NPC believes          |
| Player Memory    | Protagonist perception and bias |

Memory influences dialogue, narration tone, clue availability, and endings.

---

### 4. Environment & Weather Simulator

Weather and time are **mechanical systems**, not visuals.

Examples:

* Rain washes away evidence
* Fog obscures hotspots
* Heat increases violence
* Late-night hours unlock dangerous encounters

Atmosphere reflects narrative tension and progression.

---

### 5. ASCII Scene Renderer

Scenes are procedurally staged, not static art.

Features:

* Multi-layer rendering
* Depth-aware particle systems
* Dynamic overlays (rain, fog, shadow)
* Semantic creatures and symbols

Visual state mirrors narrative pressure.

---

### 6. Interaction Engine

Inspired by classic Sierra adventures:

* Numbered hotspots
* Context-sensitive actions
* Natural-language-lite commands
* Fail-soft input parsing

The engine interprets *intent*, not strict syntax.

---

### 7. Moral & Consequence System

Instead of binary morality, ShadowEngine tracks **shades**:

* Pragmatic
* Corrupt
* Compassionate
* Ruthless
* Idealistic

These affect NPC behavior, endings, and self-narration.

---

## Example Game Built on ShadowEngine

### *Noir York Shadows*

A procedurally generated 1940s New York crime drama where every run is a complete noir story:

* Corrupt cops
* Double-crossing allies
* Weather-driven investigations
* Multiple moral endings

---

## Historical & Design Influences

ShadowEngine draws from decades of text and ASCII-based games:

* **Colossal Cave Adventure / Zork** – Parser-driven world interaction
* **Sierra Quest Series** – Point-and-click logic and environmental puzzles
* **Roguelikes (NetHack, Rogue)** – Procedural worlds with persistent consequences
* **MUDs** – World simulation over scripted narrative
* **Dwarf Fortress** – Emergent storytelling through systems
* **ASCII Demoscene** – Atmospheric rendering with limited mediums

Key insight from these traditions:

> *The strongest stories emerge from systems that remember.*

---

## Extensibility & Genre Support

ShadowEngine is genre-agnostic. By swapping archetypes, rules, and tone packs, it can support:

* Cyberpunk investigations
* Gothic horror
* Espionage thrillers
* Weird westerns
* Hard sci‑fi mysteries

The core memory and simulation engine remains unchanged.

---

## Technical Details

* Language: Python (initial reference implementation)
* Interface: Terminal / CMD
* Dependencies: Standard library only
* Save System: JSON memory snapshots
* Deterministic Seeds: Replayable story generation
* Optional AI Hooks: Markov chains or offline LLMs

Runs anywhere a terminal exists.

---

## Roadmap

**Phase 1**

* Core memory system
* Single playable scenario

**Phase 2**

* Expanded NPC simulation
* Weather-driven mechanics
* Save/load

**Phase 3**

* Modding support
* Genre packs
* External AI integration

---

## Vision

ShadowEngine is not about replacing writers.

It is about **building worlds that remember**.

A storytelling engine where every lie persists, every storm matters, and every ending feels inevitable in hindsight.

---

*Built for terminals. Designed for stories.*
