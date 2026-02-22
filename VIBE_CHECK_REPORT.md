# Vibe-Code Detection Audit v2.0
**Project:** ShadowEngine (ASCII-City)
**Date:** 2026-02-22
**Auditor:** Claude (automated analysis)

## Executive Summary

ShadowEngine is a ~95,000-line Python project with 87 commits, 80 of which are attributed to "Claude" and 7 to "Kase." The commit messages are overwhelmingly formulaic ("Add X," "Fix Y," "Phase N: Z"), and the codebase bears numerous hallmarks of AI-generated code: uniform naming, tutorial-style comments, massive test suites dominated by formulaic docstrings, and extensive subsystems that are built but never wired into the main game loop. The core game loop (exploration, LLM-driven dialogue, location generation) does function end-to-end with genuine depth in validation, memory management, and prompt engineering. However, a large portion of the codebase—audio, voice, modding, studio, replay systems—exists in a `_deferred/` directory and is completely disconnected from any running code path.

The project scores highest on Behavioral Integrity for its core features: the LLM client, command routing, conversation system, and memory bank are genuinely wired together. It scores lowest on Surface Provenance due to the overwhelming AI authorship signal. The result is a codebase that has real value in its core engine but significant decorative bulk in peripheral systems.

## Scoring Summary

| Domain | Weight | Score | Percentage | Rating |
|--------|--------|-------|------------|--------|
| A. Surface Provenance | 20% | 8/21 | 38% | Weak-Moderate |
| B. Behavioral Integrity | 50% | 13/21 | 62% | Moderate |
| C. Interface Authenticity | 30% | 10/21 | 48% | Moderate |

**Weighted Authenticity:** (38% × 0.20) + (62% × 0.50) + (48% × 0.30) = 7.6% + 31.0% + 14.4% = **53.0%**
**Vibe-Code Confidence:** 100% − 53.0% = **47.0%**
**Classification: Substantially Vibe-Coded**

---

## Domain A: Surface Provenance (8/21 = 38%)

### A1. Commit History Patterns — Score: 1 (Weak)

**Evidence:**
- 80/87 commits (92%) attributed to author "Claude"
- 7/87 commits (8%) attributed to "Kase"
- 70/87 (80%) commit messages match formulaic patterns (`Add X`, `Fix Y`, `Phase N:`, `feat:`)
- Only 2 human frustration/iteration markers found in commit messages
- 0 reverts
- AI branch naming present: `claude/code-review-vibe-check-JOwDp`

**Sample commit messages (all formulaic):**
```
Fix 30+ additional bugs across remaining HIGH, MEDIUM, and LOW issues
Phase 5: Build "The Dockside Job" demo scenario
Phase 4: Wire NPC intelligence into game loop
Add comprehensive module functionality review documenting 100+ bugs
Replace inflated evaluation with rigorous spec-to-code analysis
```

**Assessment:** The commit history is almost entirely AI-generated. The 7 human commits are dwarfed by 80 Claude commits. There are virtually no course-correction signals (reverts, WIP, oops, typo).

**Remediation:** Squash AI commits into logical changesets with human-written summaries describing *why* the change was made. Add iterative commit patterns that show debugging and rework.

---

### A2. Comment Archaeology — Score: 1 (Weak)

**Evidence:**
- 113 tutorial-style comments across 267 source files (0.42 per file)
- 96 section divider comments (`# ====`, `# ----`)
- Only 16 TODO/FIXME/HACK markers (0.06 per file — extremely low for a 95K-line codebase)
- 25 WHY comments (`because`, `NOTE:`, `due to`)

**Tutorial-style samples:**
- `tests/inspection/test_inspection_engine.py:479`: `# Step 1: Initial look`
- `tests/_deferred/integration/test_modding_integration.py:509`: `# Step 1: Set up mod registry`
- `tests/_deferred/studio/test_e2e_pipeline.py:38`: `# Step 1: Create studio instance`

**WHY comment samples (the few that exist):**
- `src/shadowengine/circuits/circuit.py:37`: `age: float = 0.0  # Time since creation` (describes WHAT, not WHY)
- `tests/circuits/test_affordances.py:349`: `# Crate is flammable because it's wood` (genuine WHY)

**Assessment:** Comments are overwhelmingly descriptive ("Step 1:") rather than explanatory. The near-absence of TODOs and FIXMEs is a strong AI signal — human-written codebases accumulate these organically. Only 2 actual TODOs exist in production code (`src/shadowengine/generation/location_generator.py:170-171`).

**Remediation:** Replace tutorial comments with WHY explanations. Add TODOs for known gaps (there are many unintegrated subsystems that should have them).

---

### A3. Test Quality Signals — Score: 2 (Moderate)

**Evidence:**
- 3,879 test functions across 97 test files
- 389 trivial assertions (`assert X is not None`)
- 51 error path tests (`pytest.raises`)
- 443 formulaic test docstrings (`"""Tests for X."""`)
- Only 9 parametrized tests
- Test-to-source ratio is very high (~2,100 active claimed, 3,879 total including deferred)

**Assessment:** The test suite is massive but shallow. The 10:1 ratio of trivial assertions to error-path tests is a strong AI signal. However, examination of specific test files reveals some genuine depth — `tests/llm/test_validation.py` tests injection detection, truncation, and edge cases meaningfully. The circuit tests verify actual state transitions. The weakness is in the deferred modules where tests exist for code that can never run in the actual application.

**Sample of genuine test quality:** `tests/llm/test_validation.py` — tests prompt injection detection with specific markers, control character stripping, multiline collapse. This is real testing.

**Sample of weak test quality:** Many test classes follow the pattern of testing every enum value and default constructor, which adds count without meaningful coverage.

**Remediation:** Remove or archive tests for deferred modules. Add parametrized tests for core functionality. Increase error-path coverage in command handling and LLM response parsing.

---

### A4. Import & Dependency Hygiene — Score: 3 (Strong)

**Evidence:**
- `requirements.txt` declares only `pytest>=7.0.0` and `pytest-cov>=4.0.0` as required deps
- All optional deps (numpy, sounddevice, whisper, openai) are properly commented out
- Zero wildcard imports
- All imports are from standard library or internal (`shadowengine`) packages
- Lazy import pattern used for audio module (`src/shadowengine/game.py:31-38`):
  ```python
  try:
      from .audio import create_audio_engine
      _AUDIO_AVAILABLE = True
  except ImportError:
      _AUDIO_AVAILABLE = False
  ```

**Assessment:** The dependency hygiene is genuinely clean. The project runs on Python stdlib + pytest only. Optional dependencies are properly gated with try/except imports. No phantom dependencies, no unused declarations.

---

### A5. Naming Consistency — Score: 1 (Weak)

**Evidence:**
- 500+ class names, all following PascalCase with zero deviations
- 48 factory functions all using `create_` prefix
- 13 logger initializations all using `logging.getLogger(__name__)`
- Function names uniformly follow `snake_case` with no abbreviations, legacy names, or inconsistencies

**Assessment:** The naming is robotically uniform across the entire codebase. In a 95K-line project with ostensibly 2 contributors, you would expect some naming drift — abbreviated names, legacy conventions, different patterns in different modules. This level of uniformity across 267 files is a strong AI-generation signal.

**Remediation:** This is cosmetic and doesn't affect functionality. If the uniformity works for the project, keep it — but be aware it signals automated generation to any reviewer.

---

### A6. Documentation vs Reality — Score: 2 (Moderate)

**Evidence:**
- 15 markdown files (README, 8 docs/, plus evaluation/review files)
- README status table honestly marks systems as "Working | Yes", "Tested, isolated | No", or "Deferred"
- The "Planned" section clearly labels unintegrated features
- ~2,100 active tests claimed; actual test function count is 3,879 (includes deferred)
- README says "Zero for core game (pytest for testing)" — accurate

**Positive:** The README is honest. The status table (`README.md:46-59`) accurately reflects the current state. Features are not falsely claimed as working.

**Negative:** The volume of documentation (8+ design docs, concept docs, roadmap docs, evaluation reports) is disproportionate to the actual working feature set. The `REFOCUS_PLAN.md`, `CONCEPT_EXECUTION_EVALUATION.md`, and `REVIEW_MODULE_FUNCTIONALITY.md` are meta-documents about the project's own quality — unusual for a project this young.

**Remediation:** Archive or consolidate the evaluation/review docs. Keep ARCHITECTURE.md and README.md as the primary docs.

---

### A7. Dependency Utilization — Score: 2 (Moderate)

**Evidence:**
- Standard library modules are well-utilized:
  - `dataclasses`: 89 files
  - `enum`: 107 files
  - `json`: 37 files
  - `typing`: 97 files
  - `logging`: 15 files (with consistent `getLogger(__name__)` pattern)
- `hashlib`: used in 3 files for deterministic seeding (`md5`) and replay seeds (`sha256`)
- `asyncio`: imported in 1 file but 0 async functions exist in the codebase — phantom import
- `threading`: imported in 2 files with 2 lock usages

**Assessment:** Core stdlib deps are well-utilized. The `asyncio` import with zero async functions is a minor phantom. The `hashlib` usage for deterministic content generation is a genuine design choice (not crypto-related, so `md5` is acceptable).

**Remediation:** Remove unused `asyncio` import. Verify `threading` usage is justified.

---

## Domain B: Behavioral Integrity (13/21 = 62%)

### B1. Error Handling Authenticity — Score: 2 (Moderate)

**Evidence:**
- 5 bare `except Exception:` handlers total (quite low for 95K lines)
- 0 `except: pass` swallowed exceptions
- 4 custom exception classes:
  - `src/shadowengine/llm/validation.py:15`: `ValidationError`
  - `src/shadowengine/_deferred/modding/registry.py:29`: `ModLoadError`
  - `src/shadowengine/_deferred/modding/registry.py:33`: `ModValidationError`
  - `src/shadowengine/_deferred/audio/tts_engine.py:281`: `TTSEngineError`
- 21 typed exception handlers (e.g., `except urllib.error.URLError`, `except json.JSONDecodeError`)
- 1 exception chaining (`raise X from e`)

**Bare except locations (all reviewed):**
- `src/shadowengine/config.py:58` — fallback for terminal size detection (acceptable)
- `src/shadowengine/llm/client.py:123` — Ollama availability check (acceptable — returns False)
- `src/shadowengine/llm/client.py:248` — OpenAI availability check (acceptable)
- `src/shadowengine/ui/help.py:460` — UI edge case (acceptable)
- `src/shadowengine/_deferred/voice/realtime.py:636` — deferred module

**Assessment:** Error handling in the core LLM client (`client.py:166-173`) is genuinely typed — it catches `URLError`, `HTTPError`, and `JSONDecodeError` separately with appropriate messages. The 5 bare excepts are all in non-critical paths (availability checks, terminal size). No swallowed exceptions. The main gap is that only 2 of the 4 custom exceptions are in active code.

**Remediation:** Add exception chaining in the LLM client fallback path (`client.py:217`). Consider custom exceptions for command handler errors.

---

### B2. Configuration Actually Used — Score: 2 (Moderate)

**Evidence:**
- Zero environment variable reads in source code (all config is via `GameConfig` dataclass)
- `LLMConfig.from_env()` reads `LLM_BACKEND`, `LLM_MODEL`, `OLLAMA_HOST`, `OPENAI_API_KEY`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_TIMEOUT` — all consumed by LLM client
- `GameConfig` fields: `screen_width/height` → used by Renderer, `auto_save/save_dir` → used by save/load, `time_passes_on_action` → used in command handler, `enable_audio/speech` → used in Game.__init__
- Audio config fields (`master_volume`, `speech_volume`, `ambient_volume`) are defined but the audio engine is deferred, so these are partially ghost config
- `ThemeConfig` is defined with verb lists and weather weights but only verb lists are consumed by CommandParser

**Assessment:** Core config is wired. Audio config is ghost config since the audio engine is deferred. ThemeConfig weather weights are defined but not consumed by the weather system.

**Remediation:** Remove audio config fields until audio is integrated. Wire ThemeConfig weather weights to WeatherSystem or remove them.

---

### B3. Call Chain Completeness — Score: 2 (Moderate)

**Feature trace: LLM-Driven Location Generation** (COMPLETE)
```
Game.run() → _exploration_loop() → CommandParser.parse() → CommandHandler.handle_command()
  → LocationManager.handle_direction() / handle_free_movement()
  → generate_and_move() → llm_client.chat() → parse_location_response()
  → validate_location_response() → Location created + registered in WorldState
  → state.current_location_id updated → memory recorded
```
All functions exist, all return values consumed. Fallback path (`create_fallback_location`) also complete.

**Feature trace: NPC Dialogue** (COMPLETE)
```
CommandHandler._handle_talk() → state.in_conversation = True
→ Game.run() → ConversationManager.conversation_loop()
→ handle_free_dialogue() → generate_dialogue()
→ DialogueHandler.generate_response() → llm_client.chat()
→ show_dialogue() → renderer.render_dialogue()
→ world_state.generation_memory.record_dialogue()
→ character_memory.record_player_interaction()
```
Complete chain including NPC intelligence hints from PropagationEngine.

**Feature trace: Behavioral Circuits** (PARTIALLY CONNECTED)
```
CommandHandler._handle_examine() → _send_circuit_signal() → hotspot.circuit.receive_signal()
  → ProcessingResult → SignalRouter.route_outputs()
```
Circuits are wired into the command handler for examine/use/take/kick/push actions. However, no circuits are actually created in the game's `new_game()` or in LLM-generated locations. The demo scenario (`scenarios/dockside_job.py`) does create them.

**Feature trace: NPC Intelligence / Rumors** (PARTIALLY CONNECTED)
```
CommandHandler._handle_wait() → propagation_engine.update() → trigger_gossip()
CommandHandler._record_witnessed_event() → event_bridge.bridge_event()
ConversationManager.handle_threaten() → event_bridge.on_threaten()
ConversationManager.generate_dialogue() → engine.get_npc_behavior_hints() + get_rumors_known_by()
```
The wiring exists but only fires when NPCs are co-located. LLM-generated NPCs don't get registered with the propagation engine during location generation (only `Game.add_character()` does that, not the inline NPC creation in `LocationManager.parse_location_response()`).

**Feature trace: Audio/Voice/Studio/Modding** (DEAD)
All `_deferred/` modules are importable but have zero connections to the game loop.

**Assessment:** 2 of 5 traced features are fully complete. 2 are partially wired (circuits, NPC intelligence). 4+ deferred modules are completely dead code.

**Remediation:**
- Wire `propagation_engine.register_npc()` call into `LocationManager.parse_location_response()` when NPCs are created inline
- Either integrate or clearly archive deferred modules (they're already in `_deferred/` which is honest)

---

### B4. Async Correctness — Score: N/A (Skip)

**Evidence:** 0 async functions in the codebase. The project is synchronous. No asyncio usage.

**Note:** `asyncio` is imported in 1 file but never used — remove this phantom import.

---

### B5. State Management Coherence — Score: 2 (Moderate)

**Evidence:**
- `GameState` (`game.py:43-60`) is the central state container — holds memory, characters, locations, environment, world_state, propagation_engine, event_bridge
- 2 thread lock usages (in deferred audio module only)
- 35 cache/size limit references across codebase
- Config constants define explicit limits: `MAX_DIALOGUE_HISTORY_PER_NPC = 50`, `MAX_LOCATION_DETAILS_HISTORY = 100`, `MAX_REVEALED_CLUES_HISTORY = 200`, `MAX_GENERATED_LORE_HISTORY = 100`, `MAX_LOCATIONS_IN_CONTEXT = 10` (all in `config.py:33-43`)

**Assessment:** State is centralized in `GameState` with clear ownership. Memory limits are defined and referenced in context-building for LLM prompts. The `Game.new_game()` method properly recreates all delegate objects when starting fresh (`game.py:121-148`). No unbounded growth vectors were found in core paths. Thread safety is irrelevant since the project is single-threaded.

**Remediation:** Consider adding explicit cleanup/shutdown for the save system.

---

### B6. Security Implementation Depth — Score: 2 (Moderate)

**Evidence:**
- Prompt injection protection: `sanitize_player_input()` in `validation.py:194-225` — truncates to 500 chars, strips control characters, detects 10 injection marker phrases
- Input validation: 334 `validate`/`sanitize` references across codebase
- LLM response validation: `safe_parse_json()` extracts JSON with regex, applies schema validators
- Config deserialization protection: `GameConfig.load()` uses `_VALID_FIELDS` allowlist to prevent injection of unexpected keys (`config.py:114-136`)
- No SQL, no web server, no user auth — attack surface is limited to LLM prompt injection and save file manipulation
- Hashlib usage is for deterministic seeding (md5) and replay seeds (sha256) — not crypto
- Zero hardcoded secrets
- Zero SQL injection vectors
- Zero rate limiting (no need — local LLM calls)

**Assessment:** Security is appropriate for the threat model (local terminal game with LLM backend). Prompt injection protection is real and tested. Config deserialization uses an allowlist. The main gap is that save file loading (`MemoryBank.load()`) trusts JSON structure without deep validation.

**Remediation:** Add schema validation to save file loading. Consider adding a file integrity check (hash) for save files.

---

### B7. Resource Management — Score: 3 (Strong)

**Evidence:**
- 104 context manager (`with`) usages
- 0 file handles opened without context managers
- 95 cleanup/shutdown handler references
- LLM client uses `urllib.request.urlopen` inside `with` blocks (`client.py:119`, `client.py:154`, `client.py:200`)
- `GameConfig.save()` uses `with open(path, 'w') as f:` (`config.py:111`)
- No background threads in core code
- No leaked handles detected

**Assessment:** Resource management is clean. All file I/O uses context managers. HTTP connections are properly scoped. No background tasks leak.

---

## Domain C: Interface Authenticity (10/21 = 48%)

### C1. API Design Consistency — Score: 2 (Moderate)

**Evidence:**
- `CommandHandler.handle_command()` uses consistent dispatch pattern (dict of lambdas) for both simple and hotspot commands (`command_handler.py:60-67`, `command_handler.py:129-140`)
- `LLMClient` uses ABC pattern with `generate()` and `chat()` abstract methods — all 3 implementations (Ollama, OpenAI, Mock) follow the contract
- `LocationManager`, `ConversationManager`, `CommandHandler` all take dependency-injected collaborators in `__init__`

**Assessment:** Internal API design is consistent. The delegation pattern (Game → CommandHandler → LocationManager/ConversationManager) is clean. The weakness is that some modules use `hasattr()` checks instead of proper interface guarantees (`command_handler.py:227`, `command_handler.py:525`).

**Remediation:** Replace `hasattr(state, 'event_bridge')` checks with proper interface or Optional typing.

---

### C2. UI Implementation Depth — Score: 2 (Moderate)

**Evidence:**
- Terminal-based UI with `Renderer` class handling all output
- Scene rendering, dialogue rendering, narration, discovery, game over screens
- No web or GUI frontend — this is appropriate for a terminal game
- The UI module has `Tutorial`, `HelpSystem`, `HintSystem`, `CommandHistory`, `UndoStack` (`src/shadowengine/ui/`) — these are implemented but it's unclear how deeply they're wired into the game loop

**Assessment:** For a terminal text adventure, the UI is functional. The rendering system works. The tutorial/help/hint systems exist but their integration depth needs verification.

---

### C3. State Management (Frontend) — Score: N/A (No Frontend)

The project is a terminal application. No frontend state management applies.

---

### C4. Security Infrastructure — Score: 2 (Moderate)

(Scored same as B6 — prompt injection protection is the relevant security layer)

---

### C5. WebSocket Implementation — Score: N/A (Not Applicable)

No WebSocket or network server component.

---

### C6. Error UX — Score: 1 (Weak)

**Evidence:**
- `renderer.render_error()` used for user-facing errors — shows plain text messages
- Error messages are generic: "You can't talk to that.", "I don't see that here.", "You can't go there."
- LLM failure fallback: "You consider your options..." (acceptable)
- Save/load shows raw exception message: `f"Failed to save: {e}"` (`command_handler.py:544`)

**Assessment:** Error messages are functional but minimal. Exposing raw exception strings to the user (`Failed to save: {e}`) is not polished. The generic responses for game commands are fine for a text adventure, but the system errors should be friendlier.

**Remediation:** Wrap system errors (save/load, LLM failures) in user-friendly messages without exposing exception internals.

---

### C7. Logging & Observability — Score: 1 (Weak)

**Evidence:**
- 13 files use `logger = logging.getLogger(__name__)`
- Standard library `logging` only — no structured logging (JSON)
- No request tracing or correlation IDs
- No metrics collection
- No health check endpoint (not applicable for CLI)
- LLM client logs warnings on fallback but no response timing/token metrics are surfaced

**Assessment:** Logging is minimal. The LLM response dataclass tracks `tokens_used` and `latency_ms` but these aren't logged or aggregated anywhere. For a game engine, basic logging is acceptable, but the LLM integration should log request/response metrics for debugging.

**Remediation:** Add LLM call logging (model, latency, token usage, success/failure). Consider writing session logs for debugging.

---

## High Severity Findings

| Finding | Location | Impact | Remediation |
|---------|----------|--------|-------------|
| ~~LLM-generated NPCs not registered with PropagationEngine~~ | `location_manager.py:300-329` | **FALSE POSITIVE** — `add_character_fn(npc)` routes through `Game.add_character()` which already calls `propagation_engine.register_npc()`. No fix needed. | N/A |
| Audio config fields are ghost config | `config.py:102-107` | `master_volume`, `speech_volume`, `ambient_volume` have no effect since audio is deferred | **REMEDIATED** — defaults set to False, fields marked with TODO comments |
| Deferred modules contain ~40K+ lines of dead code | `src/shadowengine/_deferred/` | Inflates codebase size and test count without contributing functionality | Already isolated in `_deferred/` — consider moving to separate repo or clearly archiving |

## Medium Severity Findings

| Finding | Location | Impact | Remediation |
|---------|----------|--------|-------------|
| `hasattr()` checks for optional subsystems | `command_handler.py:227,525` | Fragile coupling — fails silently if attribute name changes | **REMEDIATED** — replaced with direct attribute access |
| Raw exception messages shown to users | `command_handler.py:544,556` | Poor UX on save/load failures | **REMEDIATED** — typed exceptions with user-friendly messages |
| No save file schema validation | (save/load path) | Malformed save files could cause crashes | **REMEDIATED** — required-key validation added to `MemoryBank.load()` |
| Missing TODO markers for known gaps | Various | Makes it hard to track what's intentionally incomplete | **REMEDIATED** — TODOs added for circuits, weather weights, audio |
| `asyncio` phantom import | 1 file (`tests/_deferred/`) | Unused dependency in deferred test | Low priority — only in deferred test code, not active source |
| `validate_free_exploration_response` allows undocumented actions | `validation.py:164-167` | `kick`, `push`, `use` are handled in command_handler but not in the valid_actions set | **REMEDIATED** — added `kick`, `push`, `use` to valid_actions |

## What's Genuine

- **LLM integration architecture**: The `LLMClient` ABC with Ollama/OpenAI/Mock implementations is well-designed. The Ollama client has proper fallback from chat to generate endpoint (`client.py:213-217`). Real HTTP error handling with typed exceptions.
- **Prompt injection protection**: `sanitize_player_input()` is a real security measure with specific marker detection, not decorative (`validation.py:194-225`).
- **Three-layer memory system**: World truth, character beliefs, and player knowledge are genuinely separate data structures with different access patterns. Context limits are enforced when building LLM prompts (`config.py:39-43`).
- **Config deserialization allowlist**: `GameConfig.load()` filters input through `_VALID_FIELDS` — genuine defense against save file manipulation (`config.py:114-136`).
- **Call chain completeness for core features**: Location generation and NPC dialogue trace end-to-end with no stubs or dead ends.
- **Resource management**: Zero leaked file handles, consistent context manager usage, proper HTTP connection scoping.
- **Honest README**: The status table accurately reflects what works and what doesn't.

## What's Vibe-Coded

- **Deferred module bulk**: ~40K+ lines across audio, voice, modding, studio, replay systems that are fully built, fully tested, but completely disconnected from any running code path. This is the classic vibe-code pattern: AI generates complete-looking modules that pass their own tests but never integrate.
- **Test suite inflation**: 3,879 test functions, ~443 formulaic docstrings, 389 trivial `is not None` assertions, only 9 parametrized tests. Quantity over quality.
- **Tutorial-style comments**: 113 "Step 1:", "Here we define" style comments — AI narrating its own code generation.
- **Robotic naming uniformity**: 500+ classes and functions with zero naming drift across the entire codebase.
- **Section divider comments**: 96 decorative `# ====` / `# ----` dividers (organizational, but volume signals automated generation).
- **Evaluation meta-documents**: Multiple markdown files evaluating the project's own quality (`CONCEPT_EXECUTION_EVALUATION.md`, `REVIEW_MODULE_FUNCTIONALITY.md`) — a pattern where AI reviews its own AI-generated code.
- **Commit history**: 92% AI-authored commits with formulaic messages and zero course-correction signals.

## Remediation Checklist

- [x] ~~Register dynamically-generated NPCs with `PropagationEngine`~~ — FALSE POSITIVE (already wired via `Game.add_character()`)
- [x] Mark ghost audio config fields in `GameConfig` — defaults set to False, TODOs added
- [x] Add `kick`, `push`, `use` to `valid_actions` in `validate_free_exploration_response()`
- [x] Replace `hasattr()` checks with direct attribute access for `event_bridge` and `propagation_engine`
- [x] Wrap raw exception messages in user-friendly errors for save/load
- [x] Add schema validation to `MemoryBank.load()` for save file integrity
- [x] Add LLM call logging (model, latency, tokens, success/failure)
- [x] Add TODO markers for known integration gaps (circuits, weather weights, audio)
- [x] Archive evaluation meta-documents — moved to `docs/archive/`
- [ ] Consider squashing Claude commit history into meaningful human-authored changesets
- [x] Replace tutorial-style comments with WHY explanations in test files
- [x] Add parametrized tests for core validation — injection markers, hotspot types, archetypes, JSON parsing (+53 new tests)
- [x] Wire `ThemeConfig.weather_weights` to `WeatherSystem` via `apply_theme_weights()` in `Game.new_game()`
