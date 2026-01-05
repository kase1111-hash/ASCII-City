# Module 06: Interaction Engine

## Purpose

Sierra-style interaction with keyboard-driven input. The engine interprets player intent, not exact syntax. Fail-soft parsing ensures players aren't frustrated by rigid commands.

## Input Methods

### Primary: Hotspot Numbers

Quick interaction via numbered hotspots:
```
> 1          → Interact with hotspot 1
> 1 examine  → Examine hotspot 1
> 1 talk     → Talk to person at hotspot 1
```

### Secondary: Natural Language-Lite

Simple verb-noun commands:
```
> examine desk
> talk to bartender
> take letter
> use key on door
> go north
```

### Future: Voice Input

See [FUTURE_TTS.md](../FUTURE_TTS.md) for voice control plans.

## Command Parsing

### Fail-Soft Philosophy

The parser tries to understand intent:
```
"look at the desk" → examine desk
"check desk"       → examine desk
"desk"             → examine desk (if only one action makes sense)
"tlak bartender"   → talk bartender (typo correction)
```

### Parse Pipeline

```python
def parse_input(raw_input: str) -> Command:
    # 1. Normalize
    text = raw_input.lower().strip()

    # 2. Check hotspot shortcut
    if text.isdigit():
        return hotspot_default_action(int(text))

    # 3. Tokenize
    tokens = tokenize(text)

    # 4. Extract verb
    verb = find_verb(tokens)  # with fuzzy matching

    # 5. Extract target
    target = find_target(tokens)  # match against visible objects

    # 6. Build command
    return Command(verb=verb, target=target, raw=raw_input)
```

### Verb Recognition

Core verbs with aliases:
| Canonical | Aliases |
|-----------|---------|
| examine | look, check, inspect, see, view, read |
| talk | speak, ask, question, interview, chat |
| take | get, grab, pick up, collect |
| use | apply, put, insert, combine |
| go | walk, move, enter, exit, leave |
| open | unlock, access |
| wait | pass time, rest |

### Fuzzy Matching

- Levenshtein distance for typo correction
- Synonym expansion
- Partial matching ("bart" → "bartender")

## Context-Sensitive Actions

### Default Actions

When player just enters a number or object name:
| Target Type | Default Action |
|-------------|---------------|
| Person | talk |
| Object | examine |
| Door/Exit | go |
| Item (takeable) | take |
| Container | open |

### Contextual Modifiers

Available actions change based on context:
- Can't "take" a person
- Can't "talk to" a door
- "use" requires having an item
- Some actions require prerequisites

## Dialogue System

### Dialogue State

```python
DialogueState:
    active_npc: str | None
    topics_available: list[str]
    topics_exhausted: list[str]
    pressure_applied: int
    relationship_this_convo: int  # changes during conversation
```

### Dialogue Actions

During conversation:
```
> ask about murder     → query topic
> accuse              → apply pressure
> threaten            → apply heavy pressure (moral impact)
> sympathize          → build trust
> show [item]         → present evidence
> leave               → end conversation
```

### Topic System

- Topics unlock based on discoveries
- NPCs may redirect or refuse topics
- Exhausted topics give abbreviated responses
- New information can reopen topics

## Inventory System

### Inventory State

```python
Inventory:
    items: list[Item]
    capacity: int  # optional limit

Item:
    id: str
    name: str
    description: str
    usable_on: list[str]  # what it can interact with
    is_evidence: bool
```

### Inventory Commands

```
> inventory           → list items
> examine [item]      → detailed look
> use [item] on [target]  → attempt combination
> show [item] to [person] → present in dialogue
```

## Error Handling

### Unclear Input

```
> flurbnarg
"I don't understand 'flurbnarg'. Try: examine, talk, take, go, or use."

> look
"Look at what? Available: [1] desk, [2] window, [3] door"
```

### Invalid Actions

```
> take bartender
"I can't take the bartender. Try talking instead?"

> use key
"Use key on what?"
```

### Friendly Failures

- Never just "invalid command"
- Suggest alternatives
- Acknowledge partial understanding
- Keep player in flow

## Integration Points

- **ASCII Renderer**: Displays available hotspots
- **Memory Bank**: Records player actions
- **Character Simulation**: Routes dialogue to NPCs
- **Moral System**: Tracks aggressive/kind actions

## Implementation Notes

- Command history for up-arrow recall
- Tab completion for known objects/verbs
- Help system accessible anytime
- Parser learns from context (recently mentioned objects)
