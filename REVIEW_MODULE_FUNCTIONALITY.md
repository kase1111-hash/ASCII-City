# Module Functionality Review: Bugs That Pass Tests But Don't Function

This document catalogs code defects across the ShadowEngine codebase that would pass the
existing test suite (2,091 tests) but produce incorrect behavior in real gameplay. Findings
are organized by severity, then by module.

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| **Critical** | 15 | Game-breaking: data loss, completely broken features, dead core systems |
| **High** | 30 | Major gameplay impact: wrong results, silent failures in key paths |
| **Medium** | 40 | Noticeable issues: stale state, missing effects, edge-case failures |
| **Low** | 20+ | Minor: cosmetic, redundant code, non-ideal semantics |

---

## CRITICAL Issues

### 1. Save/Load is fundamentally broken -- only saves MemoryBank, not game state
**Files:** `command_handler.py:537-545` (save), `command_handler.py:547-557` (load)

`_handle_save` only calls `state.memory.save(save_path)`. Characters, locations, inventory,
world state, environment, narrative spine -- none are persisted. `_handle_load` only restores
`state.memory`, leaving all other state from the current session. After loading, the memory
references locations/NPCs that don't exist, while current locations/characters have no memory
context. **Save/load is completely non-functional as a feature.**

The `WorldState` class has full `to_dict()`/`from_dict()` serialization (world_state.py:546-784)
that is never used by the save/load system.

### 2. `new_game()` leaves delegates pointing to the old WorldState
**File:** `game.py:121-126`

When `new_game()` is called, `self.state` is replaced with a fresh `GameState()`. But
`self.location_manager`, `self.conversation_manager`, and `self.dialogue_handler` still
reference the **old** `self.state.world_state` from `__init__`. All new locations and
dialogue will be registered in the discarded WorldState. The new `self.state.world_state`
stays empty.

### 3. Narrative distance thresholds are inverted -- "no connection" branch is dead code
**File:** `world_state.py:612-626`

```python
if distance_from_start > NARRATIVE_WEAK_CONNECTION_DISTANCE:   # > 5
    adaptation["connection_strength"] = "weak"
elif distance_from_start > NARRATIVE_NO_CONNECTION_DISTANCE:   # > 10
    adaptation["connection_strength"] = "none"                 # UNREACHABLE
```

Since 5 < 10, any distance > 10 also satisfies > 5 and hits the first branch. The narrative
never disconnects from the main mystery regardless of distance, breaking exploration freedom.

### 4. `broadcast_signal` radius value is discarded -- no distance filtering
**File:** `circuits/processor.py:245`

```python
radius or getattr(signal, 'radius', float('inf'))  # bare expression, not assigned
```

Should be `radius = radius or ...`. Furthermore, the radius is never used for filtering --
every broadcast hits every registered circuit regardless of distance.

### 5. Rumor mutation overwrites original in shared dict
**File:** `npc_intelligence/rumor.py:179-242, 472`

`RumorMutation.mutate()` creates a new `Rumor` with the **same `rumor_id`** as the original.
When stored via `self.active_rumors[mutated.rumor_id] = mutated`, the original is overwritten.
Every NPC receives the compounding-mutated version instead of branching from the source.

### 6. `apply_bias_to_retelling` permanently mutates the NPC's own stored memory
**File:** `npc_intelligence/npc_bias.py:439-471`

The method mutates the input `memory` object directly instead of creating a copy. Each
retelling compounds dramatization/bias. After 10 retellings, a dramatic NPC's memory will
have `emotional_weight` inflated by up to 1.0 and progressively distorted summaries.

### 7. `decay_rumors` never actually decays confidence -- `dt` parameter ignored
**File:** `npc_intelligence/rumor.py:504-513`

Despite the name and the `dt` parameter, this method never reduces rumor confidence. It only
checks if confidence is already low and removes inactive rumors. A rumor that is never retold
maintains its confidence forever.

### 8. Bidirectional interaction reverse effects always silently fail
**File:** `npc_intelligence/social_network.py:362-388`

Reverse event types like `"was_helped"`, `"was_betrayed"` are generated, but
`EVENT_EFFECTS` only contains `"helped"`, `"betrayed"` (no `"was_"` prefix). The
`if reverse_type in EVENT_EFFECTS` check is always False. B->A relationships never get
updated during bidirectional interactions.

### 9. Reconciliation between enemies is mathematically impossible
**File:** `npc_intelligence/social_network.py:253-257`

`check_for_reconciliation` requires `relation_type == ENEMY` AND `affinity > -50`. But
`_update_type()` requires `affinity <= -60` to be ENEMY. If affinity rises above -60,
`_update_type()` changes the type to RIVAL. The conditions are mutually exclusive.

### 10. Tile damage handler always crashes silently -- "collapsed" is not a valid modifier type
**File:** `grid/events.py:211-218`

`on_tile_damaged` creates `TerrainModifier(type="collapsed")`, but `__post_init__` validates
against `{"wet", "frozen", "cracked", "overgrown", "scorched", "rusty", "mossy"}`. The
`ValueError` is caught and swallowed by the event handler's `except Exception`. Tiles never
actually collapse.

### 11. `move_entity` ignores `add_entity` return value -- entities can be lost
**File:** `grid/grid.py:352-362`

After removing the entity from the old tile, `to_tile.add_entity(entity)` may return False
(placement fails). But the return value is discarded, and the method returns True. The entity
has been removed from the old tile but never placed on the new tile -- lost in limbo.

### 12. Missing lie_response silently reveals honest truth
**File:** `character/dialogue.py:80-92`

If `will_lie=True` but `lie_response` is empty/falsy, the code falls through to return an
HONEST response with `reveals_on_honest`. A character supposed to lie instead gives truthful
information, simply because no lie text was configured.

### 13. Actors don't remember their own actions
**File:** `memory/memory_bank.py:73-85`

`record_witnessed_event` only creates beliefs for `witnesses`, not `actors`. An NPC who
performed an action (e.g., Alice who murdered Bob) has no memory of their own action unless
they are also listed as a witness.

### 14. Corrupt save files silently wipe all progress to empty state
**File:** `memory/memory_bank.py:224-241`

If save data is corrupt (wrong types), each section is silently replaced with `{}`, producing
empty WorldMemory/CharacterMemory/PlayerMemory. No warning, no error. The player's progress
is silently erased.

### 15. Cascaded circuit activation outputs are discarded
**File:** `signal_router.py:154-175`

`_handle_activate` calls `hs.circuit.receive_signal(activation)` but discards the returned
`OutputSignal` list. Chain reactions (button A activates circuit B which emits sound/collapse)
are silently lost.

---

## HIGH Issues

### Character Module

**16. `modify_trust` and `apply_pressure` fight over mood state** (`character.py:141-176`)
Both methods unconditionally overwrite `self.state.mood`. Calling `apply_pressure` then
`modify_trust` flips mood from DEFENSIVE to FRIENDLY instantly, ignoring interrogation state.

**17. Post-crack pressure downgrades mood from SCARED to DEFENSIVE** (`character.py:155-166`)
After cracking (`is_cracked=True`), subsequent `apply_pressure` calls skip the first branch
but still hit the mood-update code, changing mood from SCARED to DEFENSIVE.

**18. Cracked character can still refuse in dialogue** (`character/dialogue.py:56-92`)
`get_response` checks `will_refuse` before `is_cracked`. A cracked character with
`will_refuse=True` still refuses, contradicting the cracking mechanic.

**19. `_determine_interaction_type` ignores rel2 and context entirely**
(`character/relationships.py:254-283`)
All checks use only `rel1`. Asymmetric relationships produce random interaction types
depending on which character is listed first.

**20. Asymmetric relationships cause silently dropped affinity/tension changes**
(`character/relationships.py:226-247`)
When `rel1` exists but `rel2` doesn't (created with `bidirectional=False`), `rel2` stays
None and all changes for character 2 are silently dropped.

**21. ALLY and COLLEAGUE demoted by `_update_type`** (`character/relationships.py:57-78`)
These types are not in the "protected" set. An ALLY with moderate affinity gets demoted to
ACQUAINTANCE on the next `modify_affinity` call.

### Grid Module

**22. A* heuristic uses position.z (discrete) while costs use tile.height (continuous)**
(`grid/pathfinding.py:75-81`)
The heuristic can overestimate actual cost, making it inadmissible and breaking A*'s
optimality guarantee.

**23. `all_tiles()` force-creates every tile, defeating lazy initialization**
(`grid/grid.py:414-421`)
Calling `all_tiles()` on a 1000x1000 grid creates 1,000,000 Tile objects. Methods like
`find_tiles()` and `get_passable_tiles()` call `all_tiles()`, causing memory explosion.

**24. `is_passable()` has no `makes_impassable` handling** (`grid/tile.py:143-159`)
Modifiers can make tiles passable but never impassable. One-directional processing.

**25. Boolean `makes_passable` scaled by intensity** (`grid/terrain.py:182-194`)
`isinstance(True, int)` is True in Python. `True * 0.0 = 0` (falsy). A frozen modifier
at intensity 0.0 fails to make tile passable.

**26. Bresenham LOS can see through wall corners** (`grid/grid.py:199-218`)
Diagonal steps let entities "cut through" corner-adjacent opaque tiles.

### Memory Module

**27. `character_tells_player` uses random set element for location**
(`memory/memory_bank.py:119`)
Gets an arbitrary element from `visited_locations` set instead of the current location.

**28. Non-unique fact IDs cause silent data loss** (`memory/memory_bank.py:127`)
`fact_id=f"told_{character_id}_{timestamp}"` -- multiple calls at same game-time silently
overwrite previous discoveries.

**29. Negative shade scores after normalization** (`memory/player_memory.py:172-187`)
Negative `shade_effects` values produce negative scores. Normalization with negative values
produces nonsensical results (negative "probabilities").

### Circuits Module

**30. Signal strength can exceed 1.0** (`circuits/types.py:407,414`)
Fight/flight outputs add 0.2-0.3 to values already up to 1.0. Downstream assumes [0,1] range.

**31. `attenuate()` returns base Signal, loses subclass fields**
(`circuits/signals.py:77-85`)
Called on InputSignal/OutputSignal, it loses direction, distance, radius, target_id.

**32. BiologicalCircuit emits undeclared COLLAPSE; MechanicalCircuit emits undeclared EMIT**
(`circuits/types.py:391, 184`)
These signal types aren't in `output_signals`. Code using `can_emit()` for filtering will
miss them.

**33. Self-triggering circuits during propagation** (`circuits/processor.py:261-307`)
No source-exclusion in broadcast. A circuit that emits SOUND and responds to SOUND
triggers itself repeatedly until max_depth.

**34. `block()` then `add()` still returns `has()=False`** (`circuits/affordances.py:77-88`)
`block()` adds to `_blocked` set. `add()` puts it back in `_affordances` but doesn't
remove from `_blocked`. `has()` checks both, returns False.

### NPC Intelligence Module

**35. All witness types get `MemorySource.SELF`** (`npc_intelligence/npc_bias.py:396-404`)
Direct, indirect, and inferred witnesses all recorded as firsthand, giving inflated authority.

**36. `__post_init__` overrides ALLY/ROMANTIC/INFORMANT types**
(`npc_intelligence/social_network.py:67-90`)
Creating `SocialRelation(relation_type=ALLY)` with default affinity 0 silently becomes
ACQUAINTANCE.

**37. `modify_path_for_npc` is a complete no-op** (`npc_intelligence/tile_memory.py:278-298`)
Both branches of the if/else do the same thing: `modified.append(pos)`. Path is returned
unchanged.

**38. Tile mood stuck "ominous" forever after any death**
(`npc_intelligence/tile_memory.py:113-126`)
`death_count` only increments, never decays. One death = permanently ominous location.

### Core Engine

**39. `handle_free_movement` matches substrings -- "bar" matches "harbor"**
(`location_manager.py:130-131`)
Uses `in` (substring containment). First dict-iteration match wins, teleporting player to
wrong location.

**40. `handle_accuse` has no trust penalty when accusing right person with insufficient evidence**
(`conversation.py:258-292`)
The trust penalty is only in the `else` (wrong person) branch. Repeatedly accusing the
correct culprit without evidence has no consequence.

**41. All witnessed events categorized as EventType.DISCOVERY**
(`command_handler.py:209-224`, `signal_router.py:107-113`)
Taking items, hearing sounds, all uniformly DISCOVERY. Flattens the event type system.

**42. `on_threaten`/`on_accuse` hardcode location=""** (`event_bridge.py:85-106`)
Events recorded with empty location. NPC intelligence can't determine where threats happened.

**43. Threaten/accuse not recorded in `generation_memory`** (`conversation.py:100-106`)
LLM dialogue history misses all threats and accusations. Subsequent LLM responses won't
know these interactions happened.

**44. Duplicate NPC hotspot registration** (`location_manager.py:272-329`)
If LLM response has both `hotspots` with type "person" AND `npcs`, the same NPC gets two
hotspots in the scene.

**45. `_handle_save` doesn't create save directory** (`command_handler.py:537-545`)
No `os.makedirs`. On fresh install, save always fails until someone manually creates `saves/`.

### Other Modules

**46. `_check_reveals_info` treats common words as secret overlap**
(`llm/integration.py:122-131`)
Words like "I", "the", "was" inflate the overlap percentage. A secret "I killed Eddie"
triggers at 50% overlap if the response contains "I" and "the".

**47. LLM circuit evaluator returns empty outputs list**
(`llm/integration.py:309-334`)
The evaluator produces narrative text but zero OutputSignals. Circuits using LLM evaluation
produce no game effects.

---

## MEDIUM Issues

### State Management / Serialization

- **`CharacterState.from_dict` mutates its input dict** (`character.py:94-96`) -- overwrites
  `data["mood"]` with Mood enum.
- **`WorldEvent.from_dict` mutates and pops from input dict**
  (`npc_intelligence/world_event.py:139-145`)
- **`SocialRelation.from_dict` mutates input dict**
  (`npc_intelligence/social_network.py:179-182`)
- **`InspectableObject.from_dict` mutates input dict via `data.pop()`**
  (`inspection/inspectable.py:277-291`)
- **`Belief.from_dict` mutates input dict** (`memory/character_memory.py:46-49`)
- **`Event.from_dict` mutates input dict** (`memory/world_memory.py:57-60`)
- **`from_dict` on MechanicalCircuit/BiologicalCircuit loses constructor parameters**
  (`circuits/types.py:214-224, 457-467`)
- **`EnvironmentalCircuit.from_dict` gives rock affordances regardless of terrain**
  (`circuits/types.py:648-660`)
- **Time callbacks lost on deserialization** (`environment/time.py:260-284`)
- **Weather RNG state not restored** (`environment/weather.py:413-440`)

### Missing Bounds / Clamping

- **`Character.modify_trust` has no clamping** (`character.py:168-176`) -- trust grows
  unbounded.
- **`PlayerMemory.update_relationship` has no bounds** (`memory/player_memory.py:143-146`)
- **`add_shared_secret` bypasses trust clamping** (`npc_intelligence/social_network.py:114-118`)
  -- directly uses `+=` instead of `modify_trust()`.
- **Stability goes negative; repeated COLLAPSE events** (`circuits/types.py:558`)
- **Temperature unbounded and no thaw logic** (`circuits/types.py:600,612`)
- **BiologicalCircuit fear floor is 0.1, never reaches 0.0** (`circuits/types.py:441-442`)
- **`get_share_probability` can exceed 1.0** (`npc_intelligence/npc_memory.py:88-97`)

### Time / Progression

- **`handle_free_movement` doesn't advance time** (`location_manager.py:130-139`)
- **`create_fallback_location` doesn't advance time** (`location_manager.py:352-398`)
- **TimeEvent.matches_time triggers repeatedly within same hour**
  (`environment/time.py:71-75`) -- `minute >= trigger_minute` matches every subsequent minute.
- **Repeating events only reset at exact midnight boundary**
  (`environment/time.py:183-186`)

### Game Logic

- **`_state_changes` captured post-mutation, not as deltas** (`circuits/processor.py:194-198`)
- **`get_in_radius` only searches center's z-level** (`grid/grid.py:144-166`)
- **`fill_rect` doesn't clear entities/modifiers for new terrain** (`grid/grid.py:458-489`)
- **Duplicate movement cost implementations diverge** (`grid/tile.py:332-374` vs
  `grid/pathfinding.py:18-72`)
- **`register_npc` appends to location NPC list without dedup** (`world_state.py:304-320`)
- **`NPCBias.random()` and `SpineGenerator.__init__` seed global random**
  (`npc_intelligence/npc_bias.py:112-130`, `narrative/spine.py:234-237`)
- **`_dramatize` and `_exaggerate` destroy proper noun casing**
  (`npc_intelligence/npc_bias.py:483-495`, `npc_intelligence/rumor.py:290-302`)
- **Memory recency decay is too aggressive** (`npc_intelligence/behavior_mapping.py:173-180`)
  -- any memory older than 9 time units hits 0.1 floor.
- **Behavior tag priority depends on insertion order**
  (`npc_intelligence/behavior_mapping.py:194-208`)
- **`get_response_type` priority ordering prevents certain responses**
  (`npc_intelligence/behavior_mapping.py:233-247`)
- **Bloodstain processor emits evidence on every look past count 1**
  (`scenarios/dockside_job.py:316-344`)
- **All generated hotspots share position (30, 10)**
  (`generation/location_generator.py:262, 300-301`)
- **Tutorial wildcard "contains" pattern is dead code** (`ui/tutorial.py:44-60`)
- **`sanitize_player_input` flags common English words as injection**
  (`llm/validation.py`) -- "system", "ignore", "forget" in normal gameplay text.

---

## LOW Issues

- `will_cooperate` FRIENDLY check is dead code (`character.py:214-225`)
- `Motivations.from_dict({})` silently returns all-default values (`character.py:52-53`)
- `Character.from_dict` double-sets location (`character.py:257-270`)
- `pressure_accumulated` reuses `trust_threshold` as cracking threshold (`character.py:155`)
- Tension change always symmetric in interactions (`character/relationships.py:242-247`)
- `simulate_location_interactions` collision wastes iterations
  (`character/relationships.py:402-428`)
- `dialogue_manager` global singleton retains stale state (`character/dialogue.py:189`)
- REFUSE response still reports `pressure_applied` (`character/dialogue.py:64-69`)
- No schedule overlap detection (`character/schedule.py`)
- `get_history(limit=0)` returns all events instead of none (`grid/events.py:150`)
- `Tile.__eq__` only compares position (`grid/tile.py:426-429`)
- `get_events_since` uses `>=` (includes boundary) (`memory/world_memory.py:119-121`)
- Event ID hash collisions possible (`memory/world_memory.py:41`)
- Non-deterministic shade tie-breaking (`memory/player_memory.py:189-203`)
- Incomplete `__init__.py` exports across multiple modules
- `to_dict` serializes signal data by reference (`circuits/signals.py:94`)
- Exception swallowing hides real errors in circuit processor
  (`circuits/processor.py:218-225`)
- Exception swallowing hides handler bugs in grid events (`grid/events.py:120-128`)
- Terminal size captured at import, never updated (`config.py:62-63`)
- Audio import silently swallows all ImportError (`game.py:31-38`)
- Inspection description duplicated at COARSE zoom (`inspection/inspectable.py:180-192`)
- Inspection always truncates with "..." even for short descriptions
  (`inspection/inspection_engine.py:367-369`)
- Objects with `location_id=None` shown at every location
  (`inspection/inspection_engine.py:355-358`)

---

## Patterns Observed

### 1. `from_dict` methods that mutate input dictionaries
Found in 8+ classes. These cause subtle bugs when dicts are reused, logged, or deserialized
twice. Fix: `data = data.copy()` at the start of each `from_dict`.

### 2. Silent exception swallowing
Event handlers, circuit processors, and config loading all catch `Exception` broadly and
either log-and-continue or return defaults. This hides real bugs during gameplay.

### 3. Missing clamping on numeric values
Trust, relationship, temperature, stability, signal strength, shade scores -- many values
grow unbounded. Only some setters clamp; direct `+=` bypasses clamping.

### 4. Global `random.seed()` calls
At least 4 locations seed the global random module, making all subsequent random calls
deterministic. Should use `random.Random(seed)` instances instead.

### 5. Incomplete save/load
Only MemoryBank is persisted. The full WorldState serialization exists but is never wired
into the save/load commands.

### 6. Discarded return values
Circuit outputs, `add_entity` results, `get_dominant_drive` results, and computed radius
values are all evaluated and thrown away, breaking chain reactions and validation.
