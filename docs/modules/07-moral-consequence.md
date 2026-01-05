# Module 07: Moral & Consequence System

## Purpose

Instead of binary good/evil morality, ShadowEngine tracks shades—nuanced moral positions that affect NPC behavior, endings, and self-narration.

## Moral Shades

### The Five Shades

| Shade | Description | Characterized By |
|-------|-------------|------------------|
| **Pragmatic** | Ends justify means | Efficiency over ethics, calculated |
| **Corrupt** | Self-serving | Bribery, exploitation, personal gain |
| **Compassionate** | People first | Mercy, help, sacrifice for others |
| **Ruthless** | Power through fear | Threats, violence, intimidation |
| **Idealistic** | Principles above all | Justice, truth, refusing compromise |

### Shade Tracking

```python
MoralState:
    shades: dict[str, float]    # each shade 0.0 to 1.0
    dominant_shade: str         # highest value
    secondary_shade: str        # second highest
    recent_actions: list[dict]  # last N moral choices
```

Players can embody multiple shades—most will have a dominant with secondary influences.

## Action Classification

### Moral Weight

Each action has moral implications:

```python
MoralAction:
    action_type: str
    shade_effects: dict[str, float]  # how it affects each shade
    weight: float                     # significance (0.1 minor, 1.0 major)
    context: str                      # situation description
```

### Example Actions

| Action | Pragmatic | Corrupt | Compassionate | Ruthless | Idealistic |
|--------|-----------|---------|---------------|----------|------------|
| Accept bribe | +0.3 | +0.5 | -0.2 | — | -0.4 |
| Help stranger | -0.1 | -0.2 | +0.4 | -0.2 | +0.2 |
| Threaten NPC | +0.1 | — | -0.3 | +0.5 | -0.2 |
| Tell truth (harmful) | -0.2 | -0.3 | — | — | +0.5 |
| Mercy killing | +0.2 | — | +0.2* | +0.1 | -0.3 |
| Let guilty escape | -0.3 | +0.2 | +0.1* | — | -0.5 |

*Context-dependent

### Context Matters

The same action can have different effects based on circumstances:
- Threatening a bully vs. threatening a victim
- Lying to protect someone vs. lying for gain
- Violence in self-defense vs. unprovoked

## Consequences

### NPC Reactions

NPCs respond to player's moral shade:

| NPC Type | Reaction to Shades |
|----------|-------------------|
| Criminal | Trusts corrupt/pragmatic, fears ruthless |
| Victim | Trusts compassionate, fears ruthless |
| Authority | Trusts idealistic, suspicious of corrupt |
| Neutral | Reads the room, adapts |

### Cooperation Effects

```python
def calculate_cooperation(npc, player_shade):
    base = npc.base_cooperation
    modifier = npc.shade_preferences[player_shade]
    return base * modifier
```

### Dialogue Variations

NPCs may:
- Share more with trusted shades
- Lie more to distrusted shades
- Refuse to talk to certain shades
- Change their behavior based on reputation

## Ending Composition

### Ending Types

Endings are composed from player's:
1. Discoveries (what they learned)
2. Actions (what they did)
3. Moral shade (how they did it)

### Shade-Influenced Endings

| Dominant Shade | Ending Tone |
|----------------|-------------|
| Pragmatic | "The case closed. The cost was acceptable." |
| Corrupt | "You got what you wanted. So did they." |
| Compassionate | "Justice tempered with mercy." |
| Ruthless | "They'll remember not to cross you." |
| Idealistic | "The truth, no matter the price." |

### Narration Voice

Internal monologue reflects shade:
- Pragmatic: Clinical, calculating
- Corrupt: Cynical, self-justifying
- Compassionate: Empathetic, conflicted
- Ruthless: Cold, satisfied
- Idealistic: Righteous, sometimes naive

## Player Self-Narration

### Inner Voice

The game narrates the player's internal state based on shade:

```
[Compassionate] "She looked tired. Maybe pushing harder wasn't the answer."
[Ruthless] "She looked tired. Perfect time to push harder."
[Pragmatic] "She looked tired. Fatigue leads to mistakes—hers or mine."
```

### Reflection Moments

At key points, the game reflects the player's path:
- "You've built a reputation for getting results, no matter the cost."
- "People trust you. That trust has been... useful."
- "The truth matters to you. Even when it shouldn't."

## Integration Points

- **Memory Bank**: Moral actions recorded in player memory
- **Character Simulation**: NPCs react to player's shade
- **Narrative Spine**: Endings shaped by moral state
- **Dialogue System**: Available options may vary by shade

## Implementation Notes

- Shade values normalized to always sum to 1.0
- Actions decay over time (recent actions matter more)
- Major moral choices have lasting impact
- Players can shift shade but not instantly flip
- Theme packs can define different moral axes
