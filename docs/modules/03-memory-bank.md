# Module 03: Memory Bank System

## Purpose

The engine's core differentiator. Nothing meaningful happens without being remembered. Memory drives dialogue, narration, clue availability, and endings.

## Three Memory Layers

### 1. World Memory (Objective Truth)

What actually happened, regardless of who knows it.

```python
WorldMemory:
    events: list[Event]         # timestamped objective events
    evidence_states: dict       # what evidence exists, where, condition
    location_states: dict       # physical state of each location
    time_elapsed: int           # game time units passed
```

**Examples:**
- "The weapon was moved from the study to the garden at 11pm"
- "Rain began at midnight and continued for 3 hours"
- "Character A died at location B"

### 2. Character Memory (NPC Beliefs)

What each character believes happened. May be incomplete, biased, or false.

```python
CharacterMemory:
    character_id: str
    beliefs: list[Belief]       # what they think happened
    knowledge: set[str]         # facts they know
    suspicions: dict            # who they suspect, confidence level
    player_interactions: list   # history with player
```

**Examples:**
- "I saw someone leave at 10pm" (incomplete)
- "I believe my friend is innocent" (biased)
- "The player threatened me on day 2" (interaction memory)

### 3. Player Memory (Protagonist Perception)

What the player character perceives. Filtered by bias, attention, and moral state.

```python
PlayerMemory:
    discovered_facts: set[str]  # confirmed information
    suspicions: dict            # player's working theories
    relationships: dict         # trust/distrust per character
    moral_actions: list         # choices made (for shade calculation)
    unreliable_notes: list      # things player might misremember
```

**Examples:**
- "I found the letter in the desk"
- "I suspect the butler (70% confidence)"
- "I threatened the witness" (moral record)

## Memory Operations

### Recording Events
```python
def record_event(event, witnesses: list[str]):
    world_memory.add(event)  # always recorded
    for character_id in witnesses:
        character_memory[character_id].add_belief(event, perspective)
    if player_witnessed:
        player_memory.add_discovery(event)
```

### Querying Memory
```python
def what_does_character_know(character_id, topic):
    return character_memory[character_id].query(topic)

def has_player_discovered(fact):
    return fact in player_memory.discovered_facts
```

### Memory Conflicts
- Characters may have conflicting memories
- Player can compare testimonies to find inconsistencies
- World memory is arbiter of truth (hidden from player)

## Memory Effects on Gameplay

| System | How Memory Affects It |
|--------|----------------------|
| Dialogue | NPCs reference past interactions |
| Clues | Only discovered evidence is usable |
| Endings | Composed from what player knows + did |
| Narration | Tone reflects player's moral memory |
| NPC Behavior | Trust based on interaction history |

## Save/Load System

Memory bank serializes to JSON for save games:
```json
{
  "world_memory": {...},
  "character_memories": {...},
  "player_memory": {...},
  "game_seed": 12345,
  "timestamp": "..."
}
```

## Integration Points

- **All modules** read from and write to memory
- Memory is the source of truth for game state
- Deterministic seeds + memory = reproducible playthroughs
