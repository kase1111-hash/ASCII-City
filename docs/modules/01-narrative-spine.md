# Module 01: Narrative Spine Generator

## Purpose

Creates the hidden truth of each story at game start. This ensures narrative coherence regardless of procedural variation in expression.

## Responsibilities

- Generate the core conflict/case type
- Determine the true resolution
- Plant red herrings and false leads
- Define required revelations (what must be discovered)
- Set twist probabilities and timing

## Generated Structure

```python
NarrativeSpine:
    conflict_type: str          # murder, theft, conspiracy, etc.
    true_resolution: dict       # who, what, why, how
    red_herrings: list[dict]    # false leads with plausibility scores
    revelations: list[dict]     # required discoveries, order-flexible
    twist_probability: float    # chance of late-game reversal
    twist_type: str | None      # type of twist if triggered
```

## Design Principles

1. **Hidden from Player** - The spine is never directly exposed
2. **Constrains Generation** - All procedural content must be spine-consistent
3. **Flexible Expression** - Same spine can produce different surface narratives
4. **Revelation Gating** - Some truths unlock only after prerequisites

## Integration Points

- **Character Simulation**: Characters know their role in the spine
- **Memory Bank**: Revelations are recorded when discovered
- **Moral System**: Player choices can alter which ending manifests

## Example Spine (Genre-Neutral)

```
Conflict: A trusted ally is secretly the antagonist
True Resolution: The mentor betrayed the protagonist for ideological reasons
Red Herrings:
  - Suspicious outsider (70% plausibility)
  - Rival with grudge (50% plausibility)
Revelations Required:
  1. Discover the method
  2. Find the motive
  3. Connect mentor to evidence
Twist: 30% chance mentor had sympathetic reasons
```

## Implementation Notes

- Spine generation uses weighted random selection from templates
- Seeds allow deterministic replay of same spine
- Theme packs provide conflict types and resolution templates
