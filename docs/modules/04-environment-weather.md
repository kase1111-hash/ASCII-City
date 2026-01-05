# Module 04: Environment & Weather Simulator

## Purpose

Atmosphere is mechanics, not decoration. Weather and time are simulation systems that affect gameplay, clue availability, NPC behavior, and narrative tension.

## Weather System

### Weather States

```python
Weather:
    current: str                # clear, rain, fog, storm, heat, cold
    intensity: float            # 0.0 to 1.0
    duration_remaining: int     # time units until change
    next_weather: str           # queued weather state
```

### Weather Effects

| Weather | Mechanical Effects |
|---------|-------------------|
| Rain | Washes away outdoor evidence, reduces visibility, NPCs seek shelter |
| Fog | Obscures hotspots, reduces sight range, increases ambush chance |
| Storm | Loud noise masks sounds, NPCs stay indoors, power may fail |
| Heat | Increases NPC irritability/violence, outdoor evidence degrades faster |
| Cold | NPCs bundle up (harder to identify), breath visible, tracks in snow |
| Clear | Baseline state, no modifiers |

### Weather Generation

- Weather changes procedurally based on weighted probabilities
- Theme packs define weather patterns (noir = more rain, western = more heat)
- Narrative tension can influence weather (storm during climax)
- Deterministic with seed for replay

## Time System

### Time Structure

```python
GameTime:
    hour: int                   # 0-23
    day: int                    # day count
    period: str                 # dawn, morning, afternoon, evening, night, late_night
```

### Time Effects

| Period | Effects |
|--------|---------|
| Dawn | Some NPCs waking, transitional |
| Morning | Most NPCs active, businesses open |
| Afternoon | Peak activity, crowds |
| Evening | Activity winding down, social venues busy |
| Night | Reduced NPCs, different crowd, some locations closed |
| Late Night | Dangerous encounters, secrets emerge, guards tired |

### Time-Gated Events

- Some NPCs only available at certain times
- Locations change based on time (bar empty at noon, packed at night)
- Evidence may only be accessible during certain hours
- Late-night unlocks riskier but more revealing encounters

## Environmental Pressure

### Pressure Mechanics

```python
EnvironmentPressure:
    tension_level: float        # 0.0 to 1.0
    escalation_rate: float      # how fast tension builds
    triggers: list[str]         # what causes escalation
```

### Pressure Effects

- Higher tension = more aggressive weather
- NPCs become more nervous/hostile
- Stakes feel higher (reflected in narration)
- Endgame approaches

### Escalation Triggers

- Major revelations
- Character deaths
- Player aggressive actions
- Time passing without resolution
- Multiple interrogations

## Location System

### Location State

```python
Location:
    id: str
    name: str
    type: str                   # indoor, outdoor, transitional
    weather_exposure: float     # how much weather affects it
    current_npcs: list[str]     # who is here now
    evidence: list[str]         # clues present
    hotspots: list[Hotspot]     # interactive elements
    atmosphere: dict            # lighting, sound, mood descriptors
```

### Location + Weather Interaction

- Outdoor locations fully affected by weather
- Indoor locations have ambient weather effects (rain on windows)
- Transitional spaces (porches, alleys) partially affected
- Weather affects what evidence survives at locations

## Integration Points

- **Memory Bank**: Weather events recorded in world memory
- **Character Simulation**: Weather affects NPC mood and location
- **ASCII Renderer**: Weather rendered as overlays and particles
- **Narrative Spine**: Tension can accelerate toward revelations

## Implementation Notes

- Weather updates each game tick
- Time advances with player actions (not real-time)
- Environment state saved with memory bank
- Theme packs customize weather patterns and effects
