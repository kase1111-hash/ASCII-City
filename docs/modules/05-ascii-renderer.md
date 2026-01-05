# Module 05: ASCII Render Engine

## Purpose

Scenes are procedurally staged, not static art. Visual state mirrors narrative pressure. The renderer creates atmospheric ASCII scenes that communicate game state.

## Rendering Architecture

### Layer System

Scenes are composited from multiple layers (back to front):

```
Layer 0: Background (sky, walls, floor)
Layer 1: Environment (furniture, structures)
Layer 2: Characters (NPCs, player indicator)
Layer 3: Foreground (objects in front)
Layer 4: Particles (rain, fog, snow)
Layer 5: UI Overlay (hotspot numbers, status)
```

### Scene Structure

```python
Scene:
    width: int                  # character columns
    height: int                 # character rows
    layers: list[Layer]         # rendering layers
    hotspots: list[Hotspot]     # interactive elements
    atmosphere: AtmosphereState # current mood/weather
```

### Layer Structure

```python
Layer:
    id: str
    z_index: int
    content: list[list[char]]   # 2D character grid
    transparency: dict          # which chars are transparent
```

## Rendering Features

### Multi-Layer Compositing

- Layers blend back-to-front
- Transparent characters (space, special markers) show layer below
- Depth creates parallax-like effect in ASCII

### Particle Systems

```python
ParticleSystem:
    type: str                   # rain, snow, fog, smoke, sparks
    density: float              # particles per area
    direction: tuple            # movement vector
    characters: list[str]       # ASCII chars to use
    depth_layer: int            # which layer to render on
```

**Particle Types:**
| Type | Characters | Behavior |
|------|------------|----------|
| Rain | `\|` `'` `,` | Falls downward, diagonal in wind |
| Snow | `*` `.` `+` | Drifts slowly, accumulates |
| Fog | `░` `▒` | Drifts horizontally, obscures |
| Smoke | `~` `≈` | Rises, dissipates |
| Sparks | `*` `'` | Erratic, short-lived |

### Dynamic Overlays

- Weather overlays composite on top of scene
- Lighting effects (darkness, spotlight) modify character brightness
- Shadow effects using shading characters: `░▒▓█`

### Semantic Creatures/Symbols

Creatures and symbols that appear based on narrative state:

| Symbol | Meaning |
|--------|---------|
| Crow/raven | Death, omen |
| Cat | Secrets, observation |
| Rat | Decay, underworld |
| Dog | Loyalty, threat |
| Clock | Time pressure |
| Eye | Being watched |

These are omens—their presence signals narrative weight.

## Hotspot System

### Hotspot Definition

```python
Hotspot:
    id: str
    number: int                 # display number for selection
    position: tuple             # (x, y) in scene
    label: str                  # short description
    interaction_type: str       # examine, talk, take, use
    target: str                 # what it connects to
    visible: bool               # currently visible
    discovered: bool            # player has seen it
```

### Hotspot Display

```
Scene with numbered hotspots:

    ┌───────────────────────┐
    │  Office               │
    │                       │
    │   [1]     @@    [2]   │
    │   Desk   Person  Safe │
    │                       │
    │         [3]           │
    │        Door           │
    └───────────────────────┘

1. Examine desk
2. Open safe
3. Exit to hallway
```

## Atmosphere Integration

### Visual Tension Indicators

| Tension Level | Visual Effects |
|---------------|----------------|
| Low (0-0.3) | Normal lighting, calm weather |
| Medium (0.3-0.6) | Shadows lengthen, weather shifts |
| High (0.6-0.8) | Dark corners, ominous particles |
| Critical (0.8-1.0) | Storm, heavy shadow, creatures appear |

### Time-of-Day Rendering

- Dawn: Soft lighting, pink/orange tones (described in text)
- Day: Full visibility, clear
- Evening: Long shadows, warm tones
- Night: Limited visibility, dark areas
- Late night: Minimal light, danger zones

## Terminal Compatibility

### Character Set

- ASCII printable characters (32-126)
- Box drawing: `─│┌┐└┘├┤┬┴┼`
- Shading: `░▒▓█`
- Common symbols: `@#$%&*+-=<>[]{}()`

### Color Support (Optional)

- ANSI color codes for terminals that support it
- Graceful fallback to monochrome
- Color conveys mood, not required information

## Integration Points

- **Environment**: Weather state controls particles and overlays
- **Memory Bank**: Only discovered hotspots are visible
- **Narrative Spine**: Tension level affects atmosphere
- **Character Simulation**: NPC positions and states rendered

## Implementation Notes

- Render at ~10-20 FPS equivalent for smooth particles
- Double-buffer to prevent flicker
- Scene templates by location type, procedurally populated
- Terminal size detection for responsive layout
