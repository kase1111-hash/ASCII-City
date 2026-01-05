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

### Phase 4: Emergent World Systems ✓

**Goal**: Implement behavioral circuits and reactive world mechanics.

- [x] Universal BehaviorCircuit model
- [x] Circuit types (mechanical, biological, environmental)
- [x] Input/output signal system
- [x] LLM integration for circuit evaluation
- [x] State persistence and serialization
- [x] Grid-based world structure with Z-levels
- [x] Terrain types with default affordances
- [x] Affordance inheritance and override
- [x] Environmental properties (temperature, moisture, light)
- [x] Sound propagation (tile-to-tile, attenuation)
- [x] Line of sight (blocking, visibility modifiers)
- [x] Threat proximity (dynamic radius, reaction timing)
- [x] Multi-sense detection combining

### Phase 5: ASCII Art Studio ✓

**Goal**: Player creativity becomes world content.

- [x] Studio interface within game world
- [x] Drawing tools and grid editor
- [x] Semantic tagging system
- [x] LLM interpretation of art meaning
- [x] Variant generation from player art
- [x] World asset pool integration
- [x] Usage tracking and feedback loop
- [x] Gallery mode for sharing
- [x] Dynamic entity system with animations
- [x] Personality templates

### Phase 6: STT & Real-Time Input ✓

**Goal**: Voice control for fast, immersive gameplay.

- [x] STT integration (Whisper, Vosk, mock engines)
- [x] Keyboard fallback for accessibility
- [x] Natural language intent parsing
- [x] Real-time threat response system
- [x] Voice command vocabulary
- [x] Input queue management
- [x] Priority-based processing
- [x] 173 tests for voice/STT systems

### Phase 7: NPC Intelligence ✓

**Goal**: Deep NPC memory and social dynamics.

- [x] Persistent NPC memory system
- [x] Rumor propagation network
- [x] Trust/fear modeling per-entity
- [x] NPC-to-NPC relationships
- [x] Memory-driven behavior changes
- [x] Emergent social storylines

### Phase 8: Inspection & Zoom ✓

**Goal**: Progressive detail revelation.

- [x] Natural language inspection commands
- [x] Zoom level system (coarse → fine)
- [x] Tool-based inspection (magnifying glass, telescope)
- [x] LLM-generated micro-details
- [x] Persistent zoom state per object

### Phase 9: Audio & TTS ✓

**Goal**: Full audio experience.

- [x] TTS character voice system
- [x] Voice personality customization (presets, profiles)
- [x] Post-TTS sound processing (effects chains)
- [x] Ambient sound generation (location-based, weather-reactive)
- [x] Sound effect library (tension-driven)
- [x] Audio synthesis system with mock/real backends
- [x] Voice library with emotional states
- [x] 312 tests for audio synthesis

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

- [x] Theme pack specification (vocabulary, weather, atmosphere)
- [x] Custom archetype definitions (motivations, behaviors)
- [x] Scenario scripting system (events, triggers, actions)
- [x] Mod registry and content management
- [x] Built-in themes: Noir, Cyberpunk, Gothic Horror
- [x] Built-in archetypes: Femme Fatale, Corrupt Cop, Street Informant, Grieving Widow
- [x] Validation system for mod content
- [x] 228 tests for modding system
- [x] 30 E2E and integration tests

---

## Post-Completion: NFT Art Export

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
