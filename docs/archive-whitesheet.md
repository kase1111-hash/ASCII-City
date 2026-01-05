SHADOWENGINE
A Procedural Noir Storytelling Game Engine (CLI / ASCII)

Status: Concept → Prototype-ready
Primary Interface: Command Line (ASCII-rendered scenes)
Core Innovation: Memory-driven procedural storytelling with environmental simulation

1. Executive Summary

ShadowEngine is a lightweight storytelling game engine that generates coherent, replayable narrative experiences in a command-line interface using ASCII visuals, procedural systems, and persistent story memory.

Instead of scripting stories, ShadowEngine simulates world state, character psychology, environmental pressure, and moral consequence, allowing emergent noir crime dramas (and future genres) to unfold differently every run.

It blends:

Classic point-and-click adventure design (Sierra-era)

Roguelike procedural generation

AI-assisted narrative synthesis

Atmospheric ASCII rendering

The result: stories that feel authored, but are never the same twice.

2. Problem Statement

Traditional narrative games suffer from:

Linear content exhaustion

Expensive authoring costs

Shallow replayability

Cosmetic procedural text with no structural memory

AI story tools often produce:

Incoherent plots

Forgetful characters

No causal continuity

ShadowEngine solves this by separating story structure from story expression and grounding narrative generation in memory, systems, and constraints.

3. Core Design Principles

Memory First

Nothing meaningful is generated without memory.

Systems Over Scripts

Characters, weather, time, and morality are simulations.

Atmosphere Communicates State

Visuals reflect narrative tension.

Player Is a Lens, Not a God

Perspective matters; truth is filtered.

Procedural ≠ Random

All randomness is bounded by narrative rules.

4. Engine Architecture (High Level)
┌─────────────────────────┐
│        Input Layer       │  ← commands / choices
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│     Narrative Engine     │  ← story logic & rules
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│       Memory Bank        │  ← world / character / player
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  Environment Simulator  │  ← weather / time / pressure
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│    ASCII Render Engine   │  ← scenes / particles / UI
└─────────────────────────┘

5. Key Engine Modules
5.1 Narrative Spine Generator

Creates the hidden truth of the story.

Case type

True culprit / resolution

Red herrings

Required revelations

Narrative twist probability

Guarantees coherence even with procedural expression.

5.2 Character Simulation Engine

Each NPC is an autonomous narrative agent.

Character State Includes:

Archetype

Secret truth

Public lie

Motivation vectors

Fear / greed / loyalty scores

Memory of player actions

NPCs:

Lie consistently

Crack under pressure

Change behavior over time

5.3 Memory Bank System

The engine’s core differentiator.

Three Memory Layers:

Layer	Purpose
World Memory	What objectively happened
Character Memory	What NPCs believe
Player Memory	Jack’s perception & bias

Memory drives:

Dialogue variation

Narration tone

Ending composition

5.4 Environment & Weather Simulator

Atmosphere as mechanics.

Weather alters clue availability

Time gates events

Visual density reflects tension

Environmental pressure escalates stakes

Weather is procedural, persistent, and reactive.

5.5 ASCII Scene Renderer

Not static art — procedural staging.

Multi-layer rendering

Depth-aware particle systems

Dynamic overlays (fog, rain, shadow)

Semantic creatures as alerts / omens

Scenes react to narrative state.

5.6 Interaction & Input Engine

Sierra-style interaction, keyboard-driven.

Numbered hotspots

Context-sensitive actions

Natural-language-lite commands

Fail-soft parsing

The engine interprets intent, not exact syntax.

5.7 Moral & Consequence Engine

Tracks shades, not alignment.

Pragmatic

Corrupt

Compassionate

Ruthless

Idealistic

These influence:

NPC cooperation

Police pressure

Endgame tone

Player self-narration

6. Example Game Built on ShadowEngine
Noir York Shadows

A procedurally generated 1940s New York crime drama where each playthrough is a complete, coherent noir story with multiple endings and moral ambiguity.

7. Extensibility & Genre Portability

ShadowEngine is genre-agnostic.

Possible skins:

Cyberpunk detective

Gothic horror

Hard sci-fi investigation

Espionage thriller

Weird western

Change:

Archetypes

Weather physics

Moral axes

Dialogue tone rules

Keep:

Memory

Simulation

Rendering

8. Technical Footprint

Language: Python (initial)

Interface: CMD / Terminal

Dependencies: Standard library

Optional AI: Markov / offline LLM hooks

Save System: JSON memory snapshots

Deterministic Seeds for replay/sharing

Runs anywhere a terminal exists.

9. Differentiation
Feature	ShadowEngine	AI Text Games
Narrative Coherence	✔️	❌
Persistent Memory	✔️	❌
Atmospheric Rendering	✔️	❌
Replayability	High	Low
Authoring Cost	Low	High
10. Roadmap (High Level)

Phase 1:

Core memory + narrative spine

Single playable noir scenario

Phase 2:

Expanded NPC simulation

Weather-driven mechanics

Save/load

Phase 3:

Modding support

Genre packs

External AI hooks

11. Vision Statement

ShadowEngine is not about replacing writers.

It is about building worlds that remember.

A story engine where every rainstorm matters, every lie persists, and every ending feels inevitable in hindsight.
