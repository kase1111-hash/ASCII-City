# ShadowEngine Core Concepts

This document explains the fundamental mental model behind ShadowEngine. Understanding these concepts will help you work with the codebase effectively.

## Overview

ShadowEngine is an **LLM-powered emergent storytelling engine** built on three core principles:

1. **Memory-First Architecture** - Everything that happens is remembered
2. **Behavioral Circuits** - Universal interaction model for all entities
3. **Emergent Narrative** - Stories emerge from systems, not scripts

---

## 1. Memory-First Architecture

### The Problem It Solves

Traditional game engines treat state as disposable. ShadowEngine inverts this: **memory is the foundation**, and gameplay is just memory in motion.

### The Three Memory Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY BANK (Coordinator)                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   LAYER 1: World Memory (Objective Truth)                    │
│   ├─ Events that actually happened                           │
│   ├─ Immutable once recorded                                 │
│   └─ The "ground truth" for consistency                      │
│                                                              │
│   LAYER 2: Character Memory (Subjective Beliefs)             │
│   ├─ What each NPC *believes* happened                       │
│   ├─ Can be wrong, biased, or incomplete                     │
│   ├─ Includes rumors and second-hand information             │
│   └─ Drives NPC behavior and dialogue                        │
│                                                              │
│   LAYER 3: Player Memory (Discoveries)                       │
│   ├─ What the player has discovered                          │
│   ├─ Evidence collected                                      │
│   ├─ Characters talked to                                    │
│   └─ Moral choices made (shade tracking)                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Why This Matters

- **Consistency**: The LLM always has ground truth to reference
- **Emergent Stories**: NPCs react based on their (possibly flawed) beliefs
- **Player Agency**: Discoveries feel meaningful because they're tracked
- **Replayability**: Different playthroughs create different memories

### Key Classes

- `MemoryBank` - Coordinates all three layers
- `WorldMemory` - Records objective events
- `CharacterMemory` - NPC subjective beliefs
- `PlayerMemory` - Player discoveries and moral state

---

## 2. Behavioral Circuits

### The Problem It Solves

Traditional game objects have hardcoded behaviors. A door can open or close. A rat can move or bite. ShadowEngine unifies ALL interactive entities under a single **input/output signal model**.

### The Circuit Model

```
                    ┌──────────────────────────────────────┐
                    │           BEHAVIOR CIRCUIT           │
                    │                                      │
  INPUT SIGNALS     │   ┌──────────────────────────────┐   │    OUTPUT SIGNALS
  ──────────────────┼──>│         PROCESSOR            │───┼──────────────────>
  (kick, talk,      │   │                              │   │   (sound, move,
   press, damage)   │   │  LLM evaluation OR           │   │    activate, emit)
                    │   │  rule-based logic            │   │
                    │   │                              │   │
                    │   └──────────────────────────────┘   │
                    │                 │                    │
                    │                 ▼                    │
                    │   ┌──────────────────────────────┐   │
                    │   │       CIRCUIT STATE          │   │
                    │   │                              │   │
                    │   │  health: 0.0-1.0             │   │
                    │   │  power: 0.0-1.0              │   │
                    │   │  fatigue: 0.0-1.0            │   │
                    │   │  trust: 0.0-1.0              │   │
                    │   │  age: seconds                │   │
                    │   │  custom: {}                  │   │
                    │   │                              │   │
                    │   └──────────────────────────────┘   │
                    │                                      │
                    │   AFFORDANCES: [examine, kick,       │
                    │                 talk, press, ...]    │
                    │                                      │
                    └──────────────────────────────────────┘
```

### Circuit Types

| Type | Examples | Typical Behaviors |
|------|----------|-------------------|
| **MECHANICAL** | Elevator, door, light switch | Activate, spark, jam, break |
| **BIOLOGICAL** | Rat, NPC, guard dog | Flee, attack, trust, communicate |
| **ENVIRONMENTAL** | Waterfall, fire, wind | Emit sounds, spread, affect area |

### Why This Matters

- **Uniformity**: One system handles all interactions
- **Emergence**: Complex behaviors emerge from simple signals
- **LLM Integration**: Circuits can delegate decisions to the LLM
- **Composability**: Circuits can trigger other circuits

### Key Classes

- `BehaviorCircuit` - The universal entity model
- `CircuitState` - Persistent entity state
- `SignalType` - Input/output signal definitions
- `InputSignal` / `OutputSignal` - Signal messages

### Example: A Rusty Elevator Button

```python
# An old elevator button might:
# - Spark when pressed (output: LIGHT, SOUND)
# - Sometimes stick (state: fatigue increases)
# - Eventually break (state: health depletes)
# - Scare nearby rats (output signal propagates)

button = BehaviorCircuit(
    id="elevator_button_3",
    name="Rusty Elevator Button",
    circuit_type=CircuitType.MECHANICAL,
    input_signals=[SignalType.PRESS, SignalType.KICK],
    output_signals=[SignalType.ACTIVATE, SignalType.SOUND, SignalType.LIGHT],
    state=CircuitState(health=0.7, fatigue=0.3, age=31536000),  # 1 year old
    affordances=["press", "examine", "kick"]
)
```

---

## 3. Emergent Narrative

### The Problem It Solves

Traditional games have scripted stories. ShadowEngine provides a **narrative spine** (hidden structure) that guides emergent storytelling without dictating it.

### The Narrative Spine

```
┌──────────────────────────────────────────────────────────────┐
│                     NARRATIVE SPINE                          │
│                                                              │
│   CONFLICT: What happened?                                   │
│   ├─ ConflictType: MURDER, THEFT, BETRAYAL, etc.            │
│   └─ Description: "Marcus Webb was found dead..."            │
│                                                              │
│   TRUE RESOLUTION: The actual truth (hidden from player)     │
│   ├─ Culprit: who did it                                     │
│   ├─ Motive: why they did it                                 │
│   ├─ Method: how they did it                                 │
│   ├─ Opportunity: when/where                                 │
│   └─ Evidence Chain: clues that prove it                     │
│                                                              │
│   REVELATIONS: Facts the player can discover                 │
│   ├─ Prerequisites: what must be known first                 │
│   ├─ Importance: how critical to solution                    │
│   └─ Source: how to discover it                              │
│                                                              │
│   RED HERRINGS: False leads                                  │
│   └─ Designed to mislead but not block                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### How Stories Emerge

1. **The spine defines truth** - There IS a murderer, a motive, evidence
2. **NPCs have partial knowledge** - Based on their character memory
3. **Player discovers through interaction** - Talk, examine, pressure
4. **The LLM fills gaps** - Generates consistent details on demand
5. **Player assembles the picture** - From fragments across memories

### Moral Shades

Player actions are tracked across five moral dimensions:

- **Ruthless** - Achieved goals through intimidation/violence
- **Compassionate** - Showed empathy, helped others
- **Idealistic** - Pursued truth regardless of consequences
- **Pragmatic** - Made practical, expedient choices
- **Neutral** - Balanced approach

These affect NPC reactions and available endings.

### Key Classes

- `NarrativeSpine` - The hidden story structure
- `TrueResolution` - The actual solution
- `Revelation` - Discoverable facts
- `MoralShade` - Player morality tracking

---

## 4. World State (LLM Consistency)

### The Problem It Solves

LLMs don't remember previous conversations. ShadowEngine's `WorldState` provides a **consistency context** that gets passed to every LLM call.

### What WorldState Tracks

```
WORLD STATE
├─ Generated Locations (id, name, type, connections)
├─ Generated NPCs (id, name, archetype, relationships)
├─ World Events (what happened, when, who was involved)
├─ Story Facts (established truths that can't contradict)
├─ Active Threads (ongoing narrative lines)
├─ Generation Memory (all LLM-generated text)
└─ Main Mystery (the spine's public-facing elements)
```

### Why This Matters

- **No contradictions**: LLM sees what it said before
- **Consistency**: NPCs remember previous conversations
- **World building**: New locations connect to existing ones
- **Story coherence**: Facts don't contradict each other

---

## 5. The Interaction Loop

Here's how these systems work together:

```
┌─────────────────────────────────────────────────────────────┐
│                    PLAYER INPUT                              │
│                   "kick the door"                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               COMMAND PARSER (Fail-Soft)                     │
│  - Identifies verb: "kick"                                   │
│  - Identifies target: "door"                                 │
│  - Handles typos, synonyms                                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 CIRCUIT LOOKUP                               │
│  - Find door's BehaviorCircuit                               │
│  - Create InputSignal(type=KICK)                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               CIRCUIT PROCESSING                             │
│  - Processor receives signal                                 │
│  - Updates state (damage, fatigue)                           │
│  - Returns OutputSignals (SOUND, maybe OPEN)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 SIGNAL PROPAGATION                           │
│  - SOUND signal reaches nearby circuits                      │
│  - NPCs hear it (update their CharacterMemory)               │
│  - Environment might react                                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 MEMORY UPDATE                                │
│  - Record in WorldMemory: "Player kicked door"               │
│  - Update NPC beliefs who witnessed                          │
│  - Track in PlayerMemory as action taken                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    RENDER                                    │
│  - Display narrative result                                  │
│  - Update scene                                              │
│  - Wait for next input                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Key Design Decisions

### Why Dataclasses?

- Clean, immutable-by-default models
- Built-in serialization support
- Type hints for IDE support
- Reduced boilerplate

### Why Enums for Types?

- Type safety at compile time
- IDE autocomplete
- Prevents typos in string comparisons
- Self-documenting code

### Why Separation of Concerns?

The active modules each handle one thing:
- `memory/` - Just memory
- `circuits/` - Just circuits
- `narrative/` - Just story structure
- `render/` - Just display

This means you can understand one system without understanding all systems.

### Why LLM Fallbacks?

Every system that uses LLM has a fallback:
- Location generation → Template locations
- Dialogue → Simple rule-based responses
- Free exploration → Best-effort parsing

This ensures the game works even without an LLM connected.

---

## 7. Common Patterns

### Pattern: to_dict / from_dict

All major classes implement serialization:

```python
# Save
data = circuit.to_dict()
json.dump(data, file)

# Load
circuit = BehaviorCircuit.from_dict(data)
```

### Pattern: Factory Methods

Complex objects have named constructors:

```python
hotspot = Hotspot.create_person(id="hs_1", name="John", ...)
hotspot = Hotspot.create_exit(id="hs_2", destination="hallway", ...)
```

### Pattern: Event Recording

Everything notable gets recorded:

```python
memory_bank.record_witnessed_event(
    event_type=EventType.ACTION,
    description="Player examined the desk",
    location="study",
    actors=["player"],
    witnesses=["npc_butler"],
    player_witnessed=True
)
```

---

## Summary

ShadowEngine's power comes from the interaction of its core systems:

1. **Memory makes actions meaningful** - What happened matters
2. **Circuits make the world consistent** - Everything behaves the same way
3. **Narrative provides structure** - There's a mystery to solve
4. **World State keeps LLM consistent** - No contradictions
5. **Emergence creates stories** - Not scripted, discovered

When you understand these five concepts, you understand ShadowEngine.

---

*For implementation details, see [ARCHITECTURE.md](ARCHITECTURE.md).*
*For the complete design vision, see [DESIGN.md](DESIGN.md).*
