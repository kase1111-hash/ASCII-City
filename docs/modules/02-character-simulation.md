# Module 02: Character Simulation Engine

## Purpose

Each NPC is an autonomous narrative agent with psychology, secrets, and memory. Characters behave consistently based on their internal state, not scripted dialogue trees.

## Character State Model

```python
Character:
    # Identity
    id: str
    name: str
    archetype: str              # template defining base behavior

    # Secrets
    secret_truth: str           # what they're hiding
    public_lie: str             # what they claim instead
    role_in_spine: str | None   # connection to narrative spine

    # Psychology
    motivations: dict           # fear, greed, loyalty, etc. (0-100)
    trust_threshold: int        # pressure needed to reveal truth
    current_trust: int          # trust toward player (can be negative)

    # State
    is_cracked: bool            # has revealed secret under pressure
    mood: str                   # current emotional state
    location: str               # current location

    # Memory
    memory: list[dict]          # remembered interactions with player
```

## Behavior Rules

### Lying Consistently
- Characters maintain their public lie until cracked
- Lies are internally consistent (they remember what they said)
- Contradictions only emerge under pressure or between characters

### Cracking Under Pressure
- Pressure accumulates from:
  - Evidence presented
  - Threats or intimidation
  - Witnessing other characters crack
  - Time passing (some characters break down)
- When pressure exceeds `trust_threshold`, character reveals truth

### Trust Dynamics
- Trust increases: helping them, keeping secrets, consistent behavior
- Trust decreases: threats, betrayal, siding with enemies
- Negative trust = hostile behavior, may lie more aggressively

### Memory-Driven Reactions
- Characters remember what player did
- Past actions affect dialogue options and cooperation
- "You helped me before" vs "You threatened my friend"

## Archetype System

Archetypes provide templates that theme packs can customize:

| Archetype | Behavior Pattern |
|-----------|-----------------|
| Protector | Loyal but secretive about those they protect |
| Opportunist | Helpful when beneficial, betrays when advantageous |
| True Believer | Ideologically driven, hard to crack |
| Survivor | Self-preservation first, cracks easily |
| Authority | Controls information, resents challenges |
| Outsider | Knows things but isn't trusted by others |

## Integration Points

- **Narrative Spine**: Characters know their role in the hidden truth
- **Memory Bank**: Character memory is stored in Character Memory layer
- **Moral System**: Player's moral shade affects NPC reactions
- **Environment**: Weather/time can affect mood and availability

## Implementation Notes

- Characters update state each game tick
- Dialogue is generated from state, not selected from trees
- NPCs can interact with each other off-screen (recorded in memory)
