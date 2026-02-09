# REFOCUS PLAN

## Diagnosis

ShadowEngine has 24 subsystems across 116 files. The central promise — emergent stories through behavioral circuits + LLM + layered memory — requires these systems to *talk to each other*. They don't. Here's the actual integration state:

| System | Code Exists | Wired Into Game Loop |
|--------|:-----------:|:--------------------:|
| BehaviorCircuit / Signals | Yes (272 lines) | **No** |
| PropagationEngine | Yes | **No** |
| SocialNetwork | Yes | **No** |
| RumorSystem | Yes | **No** |
| NPC Memory / Bias | Yes | **No** |
| MemoryBank | Yes | **Partial** (player events only) |
| LocationGenerator | Yes | Yes |
| DialogueHandler | Yes | Yes |
| Audio / TTS | Yes (12 files) | Yes (mock only, deps commented out) |
| ASCII Art Studio | Yes (701 lines) | **No** |
| Modding System | Yes (6 files, ~1,400 lines) | **No** |
| STT / Voice | Yes (6 files) | **No** |
| Replay System | Yes (3 files) | **No** |

The game loop (`game.py`) only uses: MemoryBank (player layer only), LocationGenerator, DialogueHandler, Environment, Renderer, CommandParser. Everything else — the entire NPC intelligence stack, the behavioral circuit model, the studio, the modding system — exists only in tests.

**The project is a collection of parts that have never been assembled.**

---

## Goal

Deliver a single, playable 15-minute demo that proves the core thesis: behavioral circuits + LLM + layered memory produces emergent stories that feel different from static interactive fiction.

Everything in this plan exists to make that demo work. Nothing else gets attention until it does.

---

## Phase 0: Triage (1 session)

### Archive peripheral systems

Move these to a `_deferred/` directory. They aren't deleted — they're parked. No code changes, just `git mv`:

| System | Files | Reason |
|--------|-------|--------|
| `audio/` | 12 files | All deps commented out. Mock-only. Zero gameplay impact. |
| `studio/` | 11 files | Full art editor disconnected from game. Post-MVP. |
| `modding/` | 6 files | Platform feature before the platform works. |
| `voice/` | 6 files | STT with mock-only engine. No functional capability. |
| `replay/` | 3 files | Can't replay what doesn't play. |

Move corresponding test directories to `tests/_deferred/`.

**Why:** Reduces cognitive surface area from 116 files to ~78. Every file you don't have to think about is a file that can't confuse you.

### Fix the README

Remove feature claims for: Sound Propagation, Threat Proximity, STT Voice Input, FPV Rendering, Affordance Discovery. Replace with honest "Planned" markers. The README should describe the game you can play today, not the game you designed.

### Consolidate specs

Move all `SPEC_*.md` files (8 documents) to `docs/specs/`. They're design references, not implementation guides. The only document in the root should be `README.md`.

**Deliverable:** A clean root directory, an honest README, and a codebase that reflects what's real.

---

## Phase 1: Break the Monolith (1-2 sessions)

`game.py` is 1,125 lines handling: game loop, command routing, location generation, dialogue, movement, save/load, conversation state, LLM prompting, NPC creation, and environment queries. It has 21% test coverage.

### Split into focused modules

```
src/shadowengine/
  game.py              → GameLoop only (run, exploration_loop, conversation_loop)
  command_handler.py   → All _handle_* methods, command routing
  location_manager.py  → _generate_and_move, _parse_location_response, _create_fallback
  conversation.py      → _conversation_loop, _handle_free_dialogue, threaten/accuse
```

### Extraction plan

**Step 1: Extract `CommandHandler`**

Move from `game.py`:
- `_handle_command()` (lines 246-325)
- `_handle_quit()`, `_show_text()`, `_show_inventory()`, `_show_error()`
- `_handle_hotspot_default()`, `_handle_examine()`, `_handle_talk()`, `_handle_take()`
- `_handle_go()`, `_handle_direction()`, `_handle_free_exploration()`, `_handle_free_movement()`
- `_handle_wait()`, `_handle_save()`, `_handle_load()`
- `_resolve_hotspot()`

`CommandHandler` takes a reference to `GameState`, `Renderer`, `MemoryBank`, `LLMClient`. This is a pure refactor — no behavior changes.

**Step 2: Extract `LocationManager`**

Move from `game.py`:
- `_generate_and_move()` (lines 625-702)
- `_parse_location_response()` (lines 704-818)
- `_create_fallback_location()` (lines 820-863)
- `_get_art_for_type()`
- `location_connections` tracking
- `location_distances` tracking

**Step 3: Extract `ConversationManager`**

Move from `game.py`:
- `_conversation_loop()` (lines 915-957)
- `_handle_ask_topic()`
- `_handle_free_dialogue()` (lines 966-1005)
- `_generate_character_dialogue()`
- `_handle_threaten()` (lines 1018-1055)
- `_handle_accuse()` (lines 1057-1095)
- `speak_dialogue()`, `_show_dialogue()`

**Step 4: Write tests for each extracted module**

Target: 80%+ coverage on `CommandHandler`, `LocationManager`, `ConversationManager`. These are the critical paths that currently sit at 21%.

The mock LLM client makes this testable without a running Ollama instance. Record example LLM responses as fixtures and test the parse→create pipeline end-to-end.

**Deliverable:** `game.py` drops from 1,125 lines to ~150 (initialization + loop delegation). Each component is independently testable. Critical path coverage goes from 21% to 80%+.

---

## Phase 2: Wire the Memory System (1-2 sessions)

Currently: `MemoryBank` records player events. `CharacterMemory` exists but is never populated during gameplay. NPCs have no memory of what the player did.

### Connect character memory to dialogue

**In `ConversationManager._handle_free_dialogue()`:**

When the player talks to an NPC, before generating a response:
1. Retrieve `CharacterMemory` for the NPC
2. Include recent beliefs and interaction history in the LLM prompt context
3. After the NPC responds, record the interaction in their `CharacterMemory`

Currently the dialogue handler generates responses in a vacuum. The NPC doesn't know what they said last time, what the player discovered, or what other NPCs told the player. Fixing this is the single most impactful change for emergent gameplay.

**Concrete changes to `DialogueHandler.generate_response()`:**

```python
# Before generating, pull character memory
char_memory = memory_bank.get_character_memory(character.id)
if char_memory:
    recent_beliefs = char_memory.get_recent_beliefs(5)
    player_interactions = char_memory.get_player_interactions()
    # Add to prompt context
    prompt += f"\nYOU REMEMBER: {format_beliefs(recent_beliefs)}"
    prompt += f"\nPREVIOUS CONVERSATIONS: {format_interactions(player_interactions)}"
```

```python
# After generating, record the interaction
char_memory.record_player_interaction(
    timestamp=current_time,
    interaction_type="conversation",
    topic=extract_topic(player_input),
    player_tone=infer_tone(player_input),
    outcome="shared_info",
    trust_change=0
)
```

### Connect character memory to events

When the player examines something, takes evidence, or moves to a new location — if an NPC is present, record it in their `CharacterMemory` as a witnessed event. This means NPCs can later reference "I saw you poking around the crime scene."

**Deliverable:** NPCs remember previous conversations and react to player actions they witnessed. Dialogue feels continuous instead of amnesiac.

---

## Phase 3: Wire the Behavioral Circuits (1-2 sessions)

Currently: `BehaviorCircuit` exists with a signal processing pipeline, but nothing in the game ever creates a circuit or sends it a signal. The interaction model in `game.py` is hardcoded: examine → show text, take → add to inventory, use → not implemented.

### Replace hotspot interactions with circuit signals

**Step 1: Give hotspots a circuit**

Add a `circuit: Optional[BehaviorCircuit]` field to `Hotspot`. When the player examines, kicks, uses, or interacts with a hotspot, translate the command into an `InputSignal` and send it to the circuit.

```python
# In CommandHandler._handle_examine()
if hotspot.circuit:
    signal = InputSignal(type=SignalType.EXAMINE, strength=0.5, source_id="player")
    outputs = hotspot.circuit.receive_signal(signal)
    for output in outputs:
        self._process_output_signal(output, hotspot)
```

**Step 2: Add LLM processor for circuits**

The `BehaviorCircuit._processor` callback is the integration point. Create an `LLMCircuitProcessor` that:
1. Takes the circuit state, signal, and context
2. Asks the LLM "Given this entity (rusty button, health=0.7, kicked 3 times) and this action (kick, strength=0.8), what happens?"
3. Returns output signals that ripple to nearby circuits

This is where emergence happens: the LLM interprets interactions based on accumulated state, not pre-scripted responses.

**Step 3: Wire output signals to game effects**

When a circuit emits a `SignalType.SOUND`, nearby NPCs should notice. When it emits `SignalType.COLLAPSE`, the entity is destroyed. When it emits `SignalType.ACTIVATE`, connected circuits fire.

Create a `SignalRouter` that takes output signals and translates them into game state changes:
- `SOUND` → record in MemoryBank, alert NPCs in range
- `COLLAPSE` → remove hotspot, update location description
- `ACTIVATE` → trigger connected circuit
- `REVEAL` → create new discovery in PlayerMemory

**Deliverable:** Objects respond dynamically to player actions through the circuit system. Kicking a button three times actually degrades it. Breaking something makes a sound that NPCs notice.

---

## Phase 4: Wire NPC Intelligence (1-2 sessions)

Currently: `PropagationEngine`, `SocialNetwork`, `RumorSystem`, `NPCMemoryBank`, `NPCBias` — all exist, all tested, none instantiated during gameplay.

### Instantiate the PropagationEngine

Add to `GameState.__init__()`:
```python
self.propagation_engine = PropagationEngine()
```

### Feed game events into the engine

Every event recorded in `MemoryBank` should also flow through `PropagationEngine`. Create a thin adapter:

```python
class GameEventBridge:
    """Connects MemoryBank events to NPC intelligence."""

    def on_event(self, event, witnesses):
        # Form memories in NPC memory banks
        for witness_id in witnesses:
            self.propagation_engine.process_witnessed_event(witness_id, event)

        # Trigger rumor propagation
        self.propagation_engine.propagate_rumors(time_step=1)
```

Hook this into `MemoryBank.record_witnessed_event()`.

### Use NPC state in dialogue generation

The `PropagationEngine` updates NPC emotional state, behavior priorities, and rumor knowledge. Feed these into the dialogue prompt:

```python
npc_state = propagation_engine.get_npc_state(character.id)
prompt += f"\nYOUR CURRENT MOOD: {npc_state.dominant_emotion}"
prompt += f"\nRUMORS YOU'VE HEARD: {npc_state.known_rumors}"
prompt += f"\nYOUR TRUST IN PLAYER: {npc_state.player_trust}"
```

Now NPCs react differently based on what they've heard through the rumor network — not just what the player told them directly.

**Deliverable:** NPCs gossip. If you threaten one NPC, others hear about it and trust you less. If you discover evidence, NPCs who witnessed it might mention it to other NPCs before you get to them.

---

## Phase 5: The Demo (1 session)

Build one polished scenario that exercises every integrated system:

### Scenario: "The Dockside Job"

- **One location cluster:** 3-4 interconnected areas (dock, warehouse, bar, alley)
- **Three NPCs:** A bartender (knows everything, shares nothing), a dockworker (witnessed something, scared), a stranger (new to town, asking questions)
- **One mystery:** Someone was killed at the dock last night. Who? Why?
- **Circuit objects:** A locked crate (mechanical circuit — can be forced, picked, or key-opened), a broken radio (environmental circuit — picks up fragments when powered), a blood stain (environmental circuit — reveals more on close examination)
- **The test:** Player actions ripple through all systems. Threatening the dockworker causes the bartender to hear about it via rumor propagation. Examining the crate produces sound that the stranger notices. Breaking the radio reveals a clue that updates the narrative spine.

### Success criteria

The demo passes if:
1. NPCs reference previous conversations (memory works)
2. NPCs react to events they weren't present for (rumors work)
3. Objects degrade and change state through interaction (circuits work)
4. Player actions in one area affect NPC behavior in another (propagation works)
5. The mystery can be solved through multiple paths (emergence works)
6. The whole thing runs without Ollama via MockLLMClient (testable)

### Write it as a test

```python
def test_dockside_demo_emergence():
    """Integration test: prove that systems interact to produce emergence."""
    game = Game(config=GameConfig(enable_audio=False))
    game.llm_client = MockLLMClient(config, responses={...})

    # Setup scenario
    setup_dockside_scenario(game)

    # Player threatens dockworker
    simulate_command(game, "threaten")

    # Move to bar, talk to bartender
    simulate_command(game, "go bar")
    simulate_command(game, "talk bartender")

    # Bartender should reference the threat (rumor propagated)
    response = get_last_dialogue(game)
    assert "heard" in response or "word" in response  # Evidence of rumor

    # Dockworker's trust should have dropped
    dockworker = game.state.characters["dockworker"]
    assert dockworker.state.trust < 0.5

    # Kick the crate 3 times
    simulate_command(game, "go dock")
    for _ in range(3):
        simulate_command(game, "kick crate")

    # Crate circuit should be damaged
    crate = get_hotspot(game, "crate")
    assert crate.circuit.state.health < 1.0
```

**Deliverable:** A runnable demo that proves emergence works, backed by an integration test that verifies it programmatically.

---

## Phase Summary

| Phase | Focus | Key Metric | Sessions |
|-------|-------|------------|----------|
| 0 | Triage | 116 → ~78 source files, honest README | 1 |
| 1 | Break monolith | `game.py` 1,125 → ~150 lines, coverage 21% → 80%+ | 1-2 |
| 2 | Wire memory | NPCs remember conversations, reference past events | 1-2 |
| 3 | Wire circuits | Objects respond dynamically, signals ripple | 1-2 |
| 4 | Wire NPC intelligence | Rumors propagate, NPCs react to indirect events | 1-2 |
| 5 | Demo | One provably emergent 15-minute scenario | 1 |

**Total: 6-10 sessions.**

---

## What Gets Deferred (and When It Comes Back)

| System | Comes Back When | Prerequisite |
|--------|----------------|--------------|
| Audio/TTS | Demo works, user feedback says "I want to hear it" | Working game loop |
| ASCII Studio | Players want to create content for the game | Working game + gallery integration point |
| Modding | Multiple scenarios exist, community wants to create more | Stable API surface |
| STT/Voice | Terminal UX is proven, voice adds convenience | Audio system working |
| Replay | Players want to share/compare playthroughs | Deterministic game state |
| FPV Rendering | Core gameplay proven, visual upgrade desired | Renderer refactor |
| Sound Propagation | Circuit signals working, audio system integrated | Phase 3 + Audio |
| Threat Proximity | NPC awareness working, real-time tension desired | Phase 4 + timer system |

Every deferred system has a clear re-entry condition. Nothing is killed — it's sequenced.

---

## Non-Negotiable Constraints

1. **No new subsystems** until the demo works. Every line of code goes toward integration, not invention.
2. **No spec documents** for unimplemented features. Specs follow code, not the other way around.
3. **Tests before integration.** Each phase starts by writing the test that proves the integration works, then writing the code to make it pass.
4. **MockLLMClient for all tests.** The demo must be fully testable without Ollama. Record real LLM responses as fixtures for realistic mocking.
5. **One branch per phase.** Each phase is a PR. No mixing concerns.
