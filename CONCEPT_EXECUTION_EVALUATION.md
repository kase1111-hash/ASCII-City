# PROJECT EVALUATION REPORT

**Primary Classification:** Underdeveloped
**Secondary Tags:** Good Concept / Bad Execution, Feature Creep

---

## CONCEPT ASSESSMENT

**What real problem does this solve?**
Traditional text adventures use pre-scripted dialogue trees and fixed narratives. ShadowEngine proposes a world where every interaction is dynamically generated via LLM, every NPC has persistent subjective memory, and player creativity (ASCII art) feeds back into the game world. The problem is real: static interactive fiction feels dead after one playthrough.

**Who is the user? Is the pain real or optional?**
The user is a niche audience: enthusiasts of text-based games, interactive fiction, and AI-driven emergent gameplay. The pain is optional — existing IF tools (Inform 7, Twine, AI Dungeon) serve this audience already. This is a "would be cool" problem, not a "my hair is on fire" problem.

**Is this solved better elsewhere?**
AI Dungeon and NovelAI offer LLM-driven interactive fiction with larger user bases and more mature products. ShadowEngine's differentiator is its *systemic* approach — behavioral circuits, three-layer memory, rumor propagation — rather than just raw LLM text generation. That's a genuine architectural distinction, but the implementation hasn't delivered on it yet.

**Value prop in one sentence:**
An ASCII game engine where every entity is a behavioral circuit with persistent memory, enabling emergent stories through LLM-powered systemic simulation rather than scripted content.

**Verdict: Sound but Fragile.** The core idea — systemic emergence through behavioral circuits + LLM + layered memory — is architecturally interesting and genuinely different from "just feed everything to GPT." But the value depends entirely on execution, and execution is where this falls apart. The concept only works if the systems actually interact to produce emergent behavior. Right now, they mostly exist in isolation.

---

## EXECUTION ASSESSMENT

### Architecture: Over-Specified, Under-Delivered

The project has **21 specification documents** totaling thousands of lines describing systems like FPV raycasting, sound propagation via BFS wavefront, threat proximity with reaction timing windows, and affordance discovery state machines. Per the project's own `SPEC_STATUS.md`:

- **9.7% fully implemented** (3 of 31 spec sections)
- **58.1% not started** (18 of 31 spec sections)
- **9.7% diverged** from specification

This is a codebase that spent more time writing specs than writing code. The specs describe a real-time perception/threat engine; the actual code is a turn-based text adventure. These are fundamentally different applications.

### Code Quality: Bimodal

**What's good:**
- `memory/memory_bank.py` — Clean three-layer architecture (world truth, character beliefs, player knowledge). Well-tested. Serialization works. This is the strongest subsystem.
- `circuits/circuit.py` — The behavioral circuit model is genuinely novel. Signal processing, state management, serialization — all solid.
- `npc_intelligence/npc_memory.py` — Sophisticated NPC memory with decay mechanics, emotional weighting, traumatic memory handling. Production-quality code.
- `_deferred/studio/studio.py` (701 lines) — Full ASCII art editor with undo/redo, selection, clipboard, drawing tools. Well-implemented (deferred).
- `_deferred/modding/registry.py` (633 lines) — Real mod management with conflict detection, dependency tracking, lifecycle callbacks (deferred).

**What's problematic:**
- `game.py` — Was 1,124 lines; has since been refactored into `game.py` (272 lines), `command_handler.py` (557 lines), `location_manager.py` (398 lines), and `conversation.py` (309 lines). Test coverage on these extracted modules still needs improvement.
- `llm/validation.py` — 13% test coverage on the code responsible for sanitizing LLM output. This is a security-critical path.
- `generation/location_generator.py` — 0% test coverage. Untested subsystem for a core feature.
- `renderer.py` — 19% test coverage on the terminal output layer.

### The Test Count is Misleading

There are ~2,100 active tests (deferred module tests excluded). Coverage is concentrated in peripheral systems. The systems that matter most — the game loop, LLM integration, rendering, and location generation — are the least tested. The NPC memory system has 39 tests and near-complete coverage; the game engine that ties everything together has almost none.

### Tech Stack: Appropriate but Limited

Zero external dependencies for the core is a legitimate strength. Using Python stdlib `urllib` for LLM API calls instead of `requests` is defensible for a game engine that wants minimal footprint. The Ollama/OpenAI abstraction in `llm/client.py` is clean with proper fallback chains.

However, the `max_tokens: 256` default in `LLMConfig` is too low for generating rich location descriptions and dialogue. The mock LLM client works for testing but means the game's core feature — dynamic LLM-driven content — is never actually exercised in the test suite.

### Security Concerns

Player input is interpolated directly into LLM prompts in `game.py:538`:
```python
PLAYER SAYS: "{sanitize_player_input(player_input)}"
```
The `sanitize_player_input` function exists but `game.py`'s LLM integration code (`_handle_free_exploration`, `_generate_and_move`) passes context through string formatting that could allow prompt injection. This matters because the LLM response directly controls game state (creating locations, NPCs, hotspots).

**Verdict: Execution does not match ambition.** The project has pockets of excellent code (memory system, circuits, NPC intelligence, studio, modding) surrounded by under-tested critical paths and a monolithic game engine. The ambition expressed in 21 spec documents is at least 5x what the implementation delivers. The best code is in systems that *support* emergent gameplay; the game engine that's supposed to *orchestrate* emergence is the weakest link.

---

## SCOPE ANALYSIS

**Core Feature:** LLM-driven emergent world simulation via behavioral circuits and layered memory.

**Supporting:**
- Three-layer memory system (world/character/player) — directly enables emergence
- NPC intelligence (memory, bias, rumor propagation) — required for believable characters
- Command parser with LLM fallback — required for natural language interaction
- LLM client abstraction (Ollama/OpenAI/Mock) — required infrastructure

**Nice-to-Have:**
- Weather/environment system — atmosphere, not core
- Narrative spine (hidden story structure) — useful scaffolding but optional for sandbox play
- Moral consequence system (shades) — adds depth but deferrable
- Zoom/inspection system — progressive detail reveal, deferrable
- Inventory/evidence system — supports detective genre, genre-specific

**Distractions:**
- ASCII Art Studio (701 lines) — A full drawing application embedded inside a game engine. Undo/redo, selection tools, clipboard, flood fill. This is an impressive piece of code that has nothing to do with making the core game loop work. It should be a standalone tool or post-MVP feature.
- Audio/TTS system (12 files) — Text-to-speech, ambient audio, motifs, sound synthesis. The game runs in a terminal. Audio in a terminal game is a novelty, not a necessity. All dependencies are commented out in requirements.txt.
- STT/Voice input system (6 files) — Speech-to-text with intent recognition. Only a mock engine exists. Six files of infrastructure for a feature that doesn't work.
- Particle effects system — Visual effects in an ASCII terminal renderer. Low value per engineering effort.

**Wrong Product:**
- Modding system (registry.py: 633 lines, scenario.py: 751 lines, 6 total files) — A full mod management platform with dependency tracking, conflict resolution, content validation, and file loading. This is a game *platform* feature, not a game *engine* feature. The core game loop can't reliably generate a single location yet; a modding API is premature by at least a major version.
- Theme packs / genre system — Genre-agnostic design (Noir, Cyberpunk, Gothic Horror) before any single genre works end-to-end.
- Replay system with deterministic seeds — Replay infrastructure for a game that can't complete a single playthrough.

**Scope Verdict: Feature Creep.** The project has 24 subsystems across 116 source files (43,210 LOC) but can't demonstrate a working gameplay session. The peripheral systems (studio, modding, audio, STT, replay) are individually well-implemented but collectively represent thousands of lines of code that don't make the core experience work. The ratio of "supporting infrastructure" to "core gameplay that functions" is inverted.

---

## RECOMMENDATIONS

### CUT IMMEDIATELY

- **Audio system** (12 files) — All dependencies are commented out. The feature is inert. Remove entirely or archive to a branch. Reclaim cognitive overhead.
- **STT/Voice system** (6 files) — Only mock implementations exist. Zero functional capability. Delete.
- **Particle effects** — Terminal visual effects add near-zero value. Remove.
- **Replay system** (3 files) — Premature. Can't replay what doesn't play. Archive.
- **21 specification documents** describing unimplemented features — Move to a `specs/future/` directory or delete. They create a false impression of project completeness and waste reader time. Keep only specs that describe *implemented* behavior.
- **README feature claims** for unimplemented systems — The README lists "Sound Propagation," "Threat Proximity," and "STT voice input" as features. They are not features. They are aspirations. Fix the README to reflect reality.

### DEFER

- **Modding system** — Solid code, wrong time. Archive to a branch, re-integrate when the core game works.
- **ASCII Art Studio** — Move to standalone tool or post-1.0 feature.
- **Theme/genre system** — Pick one genre (noir) and make it work. Genre-agnostic design can come later.
- **Zoom/inspection system** — Nice-to-have after core exploration works.
- **Moral consequence system** — Deferrable until NPC interactions are rich enough to warrant moral tracking.

### DOUBLE DOWN

- **`game.py` refactoring** — Break the 1,124-line monolith into focused components: `GameLoop`, `CommandHandler`, `LocationManager`, `DialogueManager`. This is the single highest-leverage change. Get test coverage above 80%.
- **LLM integration testing** — The core value proposition (dynamic LLM content) has 0% coverage on location generation and 13% on validation. Write integration tests with recorded LLM responses. Test the prompt→parse→create pipeline end-to-end.
- **Behavioral circuit ↔ game loop integration** — The circuit system exists in isolation. Wire it into the game loop so that entity interactions actually produce emergent signals. This is where the concept lives or dies.
- **One working demo scenario** — Create a single, polished 15-minute gameplay experience. One location, two NPCs, one mystery. Prove the concept works before adding more systems.

### FINAL VERDICT: **Refocus**

The concept is sound. The architectural ideas (behavioral circuits, three-layer memory, rumor networks) are genuinely interesting and differentiated. Several subsystems are well-implemented. But the project has built an impressive collection of components without assembling them into a working product.

The path forward is surgical: strip the peripheral systems, focus the game engine on delivering one complete gameplay loop, and prove that behavioral circuits + LLM + layered memory actually produce emergent stories. If that demo works, every deferred system can be re-integrated. If it doesn't, no amount of modding infrastructure or ASCII art tools will save it.

**Next Step:** Refactor `game.py` into testable components and write one end-to-end integration test that starts a game, generates a location via LLM, creates an NPC, has a conversation, and verifies that the memory system recorded it all correctly. That single test will force the core systems to actually work together.
