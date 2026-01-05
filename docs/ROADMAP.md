# ShadowEngine Development Roadmap

## Overview

Development is organized into phases. Each phase produces a playable milestone before proceeding to the next.

> For the complete design vision, see [DESIGN.md](DESIGN.md)

---

## Completed Phases

### Phase 1: Core Foundation ✓

**Goal**: Minimal playable prototype with core memory and narrative systems.

- [x] Project structure and configuration
- [x] Memory Bank (world, character, player layers)
- [x] Narrative Spine (conflict generator, revelations)
- [x] Character System (archetypes, dialogue, trust)
- [x] Interaction Engine (hotspots, parsing)
- [x] ASCII Renderer (scene templates, basic UI)
- [x] Test scenario (274 tests passing)

### Phase 2: Simulation Depth ✓

**Goal**: Full NPC simulation and environmental systems.

- [x] Character Simulation (motivation vectors, pressure/cracking)
- [x] Environment System (weather, time of day)
- [x] Moral System (five shade tracking)
- [x] Inventory and evidence presentation
- [x] Multi-layer ASCII rendering
- [x] Expanded scenario (462 tests)

### Phase 3: Polish & Content ✓

**Goal**: Complete experience with full atmosphere and replayability.

- [x] Full particle systems (rain, snow, fog)
- [x] ANSI color support with tension-based atmosphere
- [x] Narrative polish (shade narrator, twists, endings)
- [x] Seed-based generation and sharing
- [x] Statistics and achievements
- [x] Help system, tutorial, command history
- [x] Full test coverage (969 tests passing)

---

## Current Phase

### Phase 4: Emergent World Systems

**Goal**: Implement behavioral circuits and reactive world mechanics.

See [DESIGN.md](DESIGN.md) for complete specifications.

#### 4.1 Behavioral Circuit Foundation
- [ ] Universal BehaviorCircuit model
- [ ] Circuit types (mechanical, biological, environmental)
- [ ] Input/output signal system
- [ ] LLM integration for circuit evaluation
- [ ] State persistence and serialization

#### 4.2 Tile Grid System
- [ ] Grid-based world structure with Z-levels
- [ ] Terrain types with default affordances
- [ ] Affordance inheritance and override
- [ ] Environmental properties (temperature, moisture, light)
- [ ] Entity placement and stacking

#### 4.3 Perception Systems
- [ ] Sound propagation (tile-to-tile, attenuation)
- [ ] Line of sight (blocking, visibility modifiers)
- [ ] Threat proximity (dynamic radius, reaction timing)
- [ ] Multi-sense detection combining

#### 4.4 Integration
- [ ] Connect circuits to existing character system
- [ ] Connect perception to NPC behavior
- [ ] Update renderer for new grid system
- [ ] Comprehensive integration tests

### Success Criteria
- Entities respond dynamically through circuits
- Sound and vision affect gameplay
- NPCs react to sensory input
- World feels alive and reactive

---

## Upcoming Phases

### Phase 5: ASCII Art Studio

**Goal**: Player creativity becomes world content.

#### Deliverables
- [ ] Studio interface within game world
- [ ] Drawing tools and grid editor
- [ ] Semantic tagging system
- [ ] LLM interpretation of art meaning
- [ ] Variant generation from player art
- [ ] World asset pool integration
- [ ] Usage tracking and feedback loop
- [ ] Gallery mode for sharing

### Success Criteria
- Players can create and tag ASCII art
- Art appears in procedurally generated worlds
- Feedback improves art usage over time
- Community can share creations

---

### Phase 6: STT & Real-Time Input

**Goal**: Voice control for fast, immersive gameplay.

#### Deliverables
- [ ] STT integration (primary input method)
- [ ] Keyboard fallback for accessibility
- [ ] Natural language intent parsing
- [ ] Real-time threat response system
- [ ] Voice command vocabulary

### Success Criteria
- Game fully playable by voice
- Fast reactions possible for threats
- Fallback ensures accessibility

---

### Phase 7: NPC Intelligence

**Goal**: Deep NPC memory and social dynamics.

#### Deliverables
- [ ] Persistent NPC memory system
- [ ] Rumor propagation network
- [ ] Trust/fear modeling per-entity
- [ ] NPC-to-NPC relationships
- [ ] Memory-driven behavior changes
- [ ] Emergent social storylines

### Success Criteria
- NPCs remember all interactions
- Information spreads between NPCs
- Relationships evolve over time
- Emergent stories form from NPC dynamics

---

### Phase 8: Inspection & Zoom

**Goal**: Progressive detail revelation.

#### Deliverables
- [ ] Natural language inspection commands
- [ ] Zoom level system (coarse → fine)
- [ ] Tool-based inspection (magnifying glass, telescope)
- [ ] LLM-generated micro-details
- [ ] Persistent zoom state per object

### Success Criteria
- "Look closer" reveals new details
- Tools enhance inspection capability
- Details feel coherent and surprising

---

### Phase 9: Audio & TTS ✓

**Goal**: Full audio experience.

See [FUTURE_TTS.md](FUTURE_TTS.md) for detailed planning.

#### Deliverables
- [x] TTS character voice system (CharacterVoice, VoiceParameters, archetypes)
- [x] Voice personality customization (emotional modulation, speech quirks)
- [x] Post-TTS sound processing (effects chain, presets)
- [x] Ambient sound generation (weather, tension, atmospheric layers)
- [x] Sound effect library (categorized sounds, procedural generation)
- [x] Comprehensive test coverage (231 audio tests)

### Success Criteria
- Each character has distinct voice ✓
- Sound effects enhance atmosphere ✓
- Audio maintains accessibility ✓

---

## Current Phase

### Phase 10: Extensibility & Modding

**Goal**: Community content creation.

#### Deliverables
- [ ] Theme pack specification
- [ ] Custom archetype definitions
- [ ] Scenario scripting system
- [ ] Modding documentation
- [ ] Example theme packs

### Success Criteria
- Community can create content
- Multiple genres playable
- Clear documentation for modders

---

### Post-Completion: NFT Art Export

> ⚠️ **DO NOT IMPLEMENT** without explicit instruction from project lead.
> This feature is planned for after the game is fully complete.

**Goal**: Allow players to mint their original ASCII art creations as NFTs.

#### Deliverables (Future)
- [ ] Blockchain integration for art minting
- [ ] Authorship verification and timestamp proof
- [ ] Export interface for original creations
- [ ] Marketplace integration (optional)

#### Why Wait
- Core game must be complete first
- Requires careful legal/regulatory consideration
- Blockchain ecosystem may evolve significantly
- Focus on gameplay, not monetization

---

## Development Principles

1. **Playable at Each Phase** - No phase ends without working game
2. **Memory First** - Core memory system is foundation of everything
3. **Behavioral Circuits** - Unified model for all entity interactions
4. **Test Continuously** - Each system testable in isolation (currently 2560 tests)
5. **Document As Built** - Keep docs current with implementation
6. **Seed Reproducibility** - All randomness must be deterministic
7. **LLM Fallback** - Systems work without LLM, enhanced with it

---

## Technical Milestones

| Phase | Tests | Key Feature |
|-------|-------|-------------|
| 1 ✓ | 274 | Core narrative loop |
| 2 ✓ | 462 | NPC simulation |
| 3 ✓ | 969 | Polish & replayability |
| 4 ✓ | 1200+ | Behavioral circuits |
| 5 ✓ | 1400+ | ASCII Art Studio |
| 6 ✓ | 1700+ | Voice control |
| 7 ✓ | 1900+ | NPC intelligence |
| 8 ✓ | 2100+ | Zoom inspection |
| 9 ✓ | 2560 | Audio system |
| 10 | TBD | Modding support |

---

## Getting Started

For new contributors, recommended starting order:

1. Read [DESIGN.md](DESIGN.md) for vision
2. Read [ARCHITECTURE.md](ARCHITECTURE.md) for structure
3. Run test suite: `pytest`
4. Explore src/shadowengine/ modules
5. Check module docs in docs/modules/
