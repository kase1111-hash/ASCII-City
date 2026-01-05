# ShadowEngine Development Roadmap

## Overview

Development is organized into phases. Each phase produces a playable milestone before proceeding to the next.

---

## Phase 1: Core Foundation

**Goal**: Minimal playable prototype with core memory and narrative systems.

### Deliverables

- [ ] **Project Structure**
  - Python package structure
  - Configuration system
  - Logging and debugging tools

- [ ] **Memory Bank (Core)**
  - World memory implementation
  - Basic character memory
  - Player memory / discoveries
  - JSON save/load

- [ ] **Narrative Spine (Basic)**
  - Simple conflict generator
  - Resolution structure
  - Red herring placement
  - Required revelations list

- [ ] **Character System (Basic)**
  - Character state model
  - Basic dialogue (topic-based)
  - Secret/lie mechanics
  - Trust tracking

- [ ] **Interaction Engine (Basic)**
  - Hotspot number selection
  - Simple verb-noun parsing
  - Basic error handling

- [ ] **ASCII Renderer (Basic)**
  - Single-layer scene rendering
  - Static scene templates
  - Hotspot display
  - Basic text UI

- [ ] **Test Scenario**
  - One location with 2-3 NPCs
  - One simple mystery to solve
  - Basic ending based on discoveries

### Success Criteria
- Player can navigate, talk, discover clues
- Memory persists correctly
- Save/load works
- Story can be completed

---

## Phase 2: Simulation Depth

**Goal**: Full NPC simulation and environmental systems.

### Deliverables

- [ ] **Character Simulation (Full)**
  - Archetype system
  - Motivation vectors (fear/greed/loyalty)
  - Pressure and cracking mechanics
  - NPC-to-NPC interactions
  - Memory-driven behavior changes

- [ ] **Environment System**
  - Weather simulation
  - Time of day system
  - Weather effects on gameplay
  - Time-gated events
  - Location state tracking

- [ ] **Moral System**
  - Five shade tracking
  - Action classification
  - NPC reactions to shade
  - Basic ending variation

- [ ] **Expanded Interaction**
  - Full natural language-lite parsing
  - Fuzzy matching / typo correction
  - Inventory system
  - Evidence presentation

- [ ] **ASCII Renderer (Enhanced)**
  - Multi-layer rendering
  - Basic particle systems (rain, fog)
  - Dynamic overlays

- [ ] **Expanded Scenario**
  - Multiple locations
  - 5+ NPCs with full simulation
  - Branching based on approach
  - Multiple endings

### Success Criteria
- Weather affects gameplay
- NPCs crack under pressure
- Moral shade influences outcomes
- Endings feel earned

---

## Phase 3: Polish & Content

**Goal**: Complete experience with full atmosphere and replayability.

### Deliverables

- [ ] **ASCII Renderer (Full)**
  - Full particle systems
  - Semantic creatures/symbols
  - Tension-based atmosphere
  - Optional ANSI colors

- [ ] **Narrative Polish**
  - Narration tone by shade
  - Self-reflection moments
  - Twist implementation
  - Ending composition system

- [ ] **Full Theme Pack (First)**
  - Complete archetype set
  - All dialogue tones
  - Weather patterns
  - Location templates
  - Full scenario

- [ ] **Replayability**
  - Seed-based generation
  - Multiple spine variations
  - Seed sharing system
  - Statistics tracking

- [ ] **Quality of Life**
  - Help system
  - Tutorial/onboarding
  - Command history
  - Settings/preferences

### Success Criteria
- Multiple complete playthroughs feel different
- Atmosphere is immersive
- New players can learn easily
- Seeds produce identical runs

---

## Phase 4: Extensibility

**Goal**: Modding support and additional content.

### Deliverables

- [ ] **Modding System**
  - Theme pack specification
  - Custom archetype definitions
  - Location template format
  - Scenario scripting

- [ ] **Additional Theme Packs**
  - Second genre (cyberpunk or horror)
  - Third genre (sci-fi or western)

- [ ] **AI Integration (Optional)**
  - Dialogue variation hooks
  - Markov chain text generation
  - Offline LLM integration points

- [ ] **Documentation**
  - Modding guide
  - API documentation
  - Example theme packs

### Success Criteria
- Community can create content
- Multiple genres playable
- AI enhances without breaking coherence

---

## Phase 5: Voice & Audio (Future)

**Goal**: Full audio experience with voice control.

See [FUTURE_TTS.md](FUTURE_TTS.md) for detailed planning.

### High-Level Deliverables

- [ ] Voice input system (primary control method)
- [ ] Keyboard fallback for accessibility
- [ ] TTS character voice system
- [ ] Voice personality customization
- [ ] Post-TTS sound processing
- [ ] Ambient sound generation

### Success Criteria
- Game fully playable by voice
- Each character has distinct voice
- Sound effects enhance atmosphere
- Accessibility maintained

---

## Development Principles

1. **Playable at Each Phase** - No phase ends without working game
2. **Memory First** - Core memory system is foundation of everything
3. **Test Continuously** - Each system testable in isolation
4. **Document As Built** - Keep docs current with implementation
5. **Seed Reproducibility** - All randomness must be deterministic

---

## Getting Started

Phase 1 recommended starting order:
1. Project structure and config
2. Memory bank system
3. Basic character model
4. Simple interaction loop
5. ASCII renderer
6. Connect into playable loop
7. Add narrative spine
8. Test scenario
