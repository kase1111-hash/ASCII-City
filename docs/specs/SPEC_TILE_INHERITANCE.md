# ShadowEngine — Tile → Affordance Inheritance Model

> **Version**: 1.0.0
> **Status**: Canonical Definition
> **Dependency**: SPEC_AFFORDANCE_SCHEMA.md
> **Purpose**: Define how tiles compose affordances through layered inheritance

---

## 1. Core Rule (Lock This In)

**Affordances are inherited, modified, and combined — never replaced.**

```
A tile does not define reality.
It filters and shapes what already exists.
```

This prevents:
- Magical interaction gaps
- Special-case logic
- "Why can I do it here but not there?"

---

## 2. Tile Is a Context, Not an Object

A tile is a **local environmental context**.

### What a Tile Does NOT Do

| ❌ Does Not | Why |
|-------------|-----|
| Contain logic | Logic is in systems, not data |
| Decide outcomes | Simulation decides |
| Know the story | Narrative spine is separate |

### What a Tile DOES Do

| ✅ Does | How |
|---------|-----|
| Modify affordance intensity | `slippery: +0.4` |
| Gate traversal | `traversal_cost: 2.0` |
| Affect perception | `visibility_modifier: 0.6` |
| Accumulate history | `state: ["bloodied", "wet"]` |

---

## 3. Tile Base Schema

Every tile shares a minimal, universal structure.

### JSON Schema

```json
{
  "tile_id": "rocky_ground",
  "position": [45, 23],
  "layer": "ground",

  "base_affordances": [
    {"id": "supports", "intensity": 0.9},
    {"id": "injures", "intensity": 0.2}
  ],

  "traversal_cost": 1.2,
  "visibility_modifier": 1.0,
  "sound_modifier": 1.0,
  "elevation": 0,

  "state": [],
  "entities": [],
  "history": []
}
```

**This is the default truth of that tile.**

### Python Implementation

```python
@dataclass
class TileBase:
    """Universal tile structure."""

    tile_id: str
    position: tuple[int, int]
    layer: str                      # "ground", "water", "air"

    # Base affordances (before modifiers)
    base_affordances: list[Affordance]

    # Movement
    traversal_cost: float           # 1.0 = normal, 2.0 = slow, inf = blocked

    # Perception
    visibility_modifier: float      # 1.0 = clear, 0.0 = opaque
    sound_modifier: float           # 1.0 = normal, 0.0 = silent

    # Verticality
    elevation: int                  # Height level (0 = ground)

    # Mutable state
    state: list[TileState]          # ["wet", "bloodied", "burning"]
    entities: list[EntityID]        # Things on this tile
    history: list[TileEvent]        # What happened here

    # Discovery
    explored: bool = False
    hidden_affordances: list[Affordance] = field(default_factory=list)
```

---

## 4. Inheritance Layers (Very Important)

**Affordances are built by stacking layers.**

### Inheritance Order (Bottom → Top)

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 7: TEMPORAL CONTEXT (night, chaos, alert state)         │
├─────────────────────────────────────────────────────────────────┤
│  Layer 6: WEATHER OVERLAY (rain, fog, storm)                   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 5: ENTITIES ON TILE (waterfall, NPC, debris)            │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: TILE STATE (wet, damaged, burning)                   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: TILE BASE (rocky_ground, wooden_floor)               │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: BIOME (forest, alley, sewer, cliff)                  │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: WORLD RULES (gravity, time, physics)                 │
└─────────────────────────────────────────────────────────────────┘
```

### Each Layer Can:

| Operation | Example |
|-----------|---------|
| **Add** affordances | Weather adds `slippery` |
| **Modify** intensities | Wet state: `slippery: +0.4` |
| **Introduce** conditions | Night: `conceals` requires `in_shadow` |

### Critical Rule

**Nothing deletes anything.**

Layers only add and modify. Affordances are never removed, only reduced to 0.0 intensity.

---

## 5. Layer Definitions

### Layer 1: World Rules

Universal physics that apply everywhere.

```python
WORLD_RULES = {
    "gravity": Affordance(
        affordance_id="falls",
        intensity=1.0,
        conditions={"unsupported": "true"},
    ),
    "inertia": Affordance(
        affordance_id="forced_motion",
        intensity=0.0,  # Modified by other layers
    ),
    "sound_propagation": Affordance(
        affordance_id="emits_sound",
        intensity=1.0,  # All actions can make sound
    ),
}
```

### Layer 2: Biome

Regional characteristics.

```python
BIOMES = {
    "cliffside": {
        "affordances": [
            Affordance("elevated", intensity=0.7),
            Affordance("exposes", intensity=0.5),
            Affordance("falls", intensity=0.6, conditions={"edge": "true"}),
        ],
    },
    "alley": {
        "affordances": [
            Affordance("funnels", intensity=0.9),
            Affordance("conceals", intensity=0.5),
            Affordance("threatens", intensity=0.3, conditions={"night": "true"}),
        ],
    },
    "sewer": {
        "affordances": [
            Affordance("encloses", intensity=0.8),
            Affordance("obscures_vision", intensity=0.4),
            Affordance("poisons", intensity=0.2),
            Affordance("deadens_sound", intensity=0.3),
        ],
    },
}
```

### Layer 3: Tile Base

Specific tile type properties.

```python
TILE_TYPES = {
    "rocky_ledge": {
        "base_affordances": [
            Affordance("supports", intensity=0.8),
            Affordance("slippery", intensity=0.3),
            Affordance("injures", intensity=0.3),
        ],
        "traversal_cost": 1.3,
    },
    "wooden_floor": {
        "base_affordances": [
            Affordance("supports", intensity=1.0),
            Affordance("emits_sound", intensity=0.4),  # Creaks
        ],
        "traversal_cost": 1.0,
    },
    "shallow_water": {
        "base_affordances": [
            Affordance("supports", intensity=0.6),
            Affordance("slippery", intensity=0.5),
            Affordance("emits_sound", intensity=0.6),  # Splashing
        ],
        "traversal_cost": 1.8,
    },
}
```

### Layer 4: Tile State

Mutable conditions applied to tiles.

```python
TILE_STATES = {
    "wet": {
        "modifiers": {
            "slippery": +0.4,
            "supports": -0.2,
            "emits_sound": +0.2,  # Squelching
        },
    },
    "bloodied": {
        "modifiers": {
            "slippery": +0.2,
        },
        "adds": [
            Affordance("signals_violence", intensity=0.8),
        ],
    },
    "burning": {
        "modifiers": {
            "traversal_cost": +1.0,
        },
        "adds": [
            Affordance("burns", intensity=0.7),
            Affordance("illuminates", intensity=0.9),
            Affordance("threatens", intensity=0.6),
        ],
    },
    "cracked": {
        "modifiers": {
            "supports": -0.3,
            "unstable": +0.5,
        },
    },
    "flooded": {
        "modifiers": {
            "traversal_cost": +0.8,
            "slippery": +0.3,
        },
        "adds": [
            Affordance("drowns", intensity=0.4),
        ],
    },
}
```

### Layer 5: Entities on Tile

Things occupying the tile.

```python
# Waterfall entity adds these when on/adjacent to tile
waterfall_affordances = [
    Affordance("conceals", intensity=0.9),
    Affordance("deadens_sound", intensity=0.7),
    Affordance("forced_motion", intensity=0.6),
    Affordance("obscures_vision", intensity=0.8),
]

# NPC entity adds these
hostile_npc_affordances = [
    Affordance("threatens", intensity=0.8),
    Affordance("blocks", intensity=0.5),
]

# Debris entity adds these
debris_affordances = [
    Affordance("conceals", intensity=0.4),
    Affordance("injures", intensity=0.3),
    Affordance("unstable", intensity=0.5),
]
```

### Layer 6: Weather Overlay

Current weather conditions.

```python
WEATHER_OVERLAYS = {
    "rain": {
        "modifiers": {
            "slippery": +0.2,
            "visibility": -0.2,
            "emits_sound": -0.1,  # Rain covers sounds
        },
    },
    "heavy_rain": {
        "modifiers": {
            "slippery": +0.4,
            "visibility": -0.4,
            "emits_sound": -0.3,
        },
        "adds": [
            Affordance("disorients", intensity=0.3),
        ],
    },
    "fog": {
        "modifiers": {
            "visibility": -0.6,
            "conceals": +0.4,
        },
    },
    "storm": {
        "modifiers": {
            "slippery": +0.5,
            "visibility": -0.5,
            "emits_sound": -0.4,
        },
        "adds": [
            Affordance("threatens", intensity=0.4),  # Lightning
            Affordance("disorients", intensity=0.5),
        ],
    },
}
```

### Layer 7: Temporal Context

Time-based and situational modifiers.

```python
TEMPORAL_CONTEXTS = {
    "night": {
        "modifiers": {
            "visibility": -0.4,
            "conceals": +0.3,
        },
        "adds": [
            Affordance("threatens", intensity=0.2),
        ],
    },
    "chaos": {  # Combat, chase, alarm
        "modifiers": {
            "emits_sound": +0.2,  # Everything louder
        },
        "adds": [
            Affordance("accelerates", intensity=0.7),  # Time pressure
        ],
    },
    "alert_state": {  # Guards searching
        "modifiers": {
            "conceals": -0.2,  # Harder to hide
        },
        "adds": [
            Affordance("threatens", intensity=0.4),
        ],
    },
}
```

---

## 6. Affordance Computation

### Computing Final Affordances

```python
class AffordanceComputer:
    """Compute final affordances from all layers."""

    def compute(
        self,
        tile: TileBase,
        biome: str,
        weather: str,
        temporal: list[str],
        world: WorldGrid,
    ) -> dict[str, float]:
        """Stack all layers to get final affordance intensities."""

        # Start with empty slate
        final: dict[str, float] = {}

        # Layer 1: World rules
        for aff in WORLD_RULES.values():
            final[aff.affordance_id] = aff.intensity

        # Layer 2: Biome
        biome_data = BIOMES.get(biome, {})
        for aff in biome_data.get("affordances", []):
            self._merge_affordance(final, aff)

        # Layer 3: Tile base
        for aff in tile.base_affordances:
            self._merge_affordance(final, aff)

        # Layer 4: Tile state
        for state in tile.state:
            state_data = TILE_STATES.get(state, {})
            # Apply modifiers
            for aff_id, modifier in state_data.get("modifiers", {}).items():
                final[aff_id] = final.get(aff_id, 0.0) + modifier
            # Add new affordances
            for aff in state_data.get("adds", []):
                self._merge_affordance(final, aff)

        # Layer 5: Entities
        for entity_id in tile.entities:
            entity = world.get_entity(entity_id)
            for aff in entity.affordances:
                self._merge_affordance(final, aff)

        # Layer 6: Weather
        weather_data = WEATHER_OVERLAYS.get(weather, {})
        for aff_id, modifier in weather_data.get("modifiers", {}).items():
            final[aff_id] = final.get(aff_id, 0.0) + modifier
        for aff in weather_data.get("adds", []):
            self._merge_affordance(final, aff)

        # Layer 7: Temporal
        for context in temporal:
            context_data = TEMPORAL_CONTEXTS.get(context, {})
            for aff_id, modifier in context_data.get("modifiers", {}).items():
                final[aff_id] = final.get(aff_id, 0.0) + modifier
            for aff in context_data.get("adds", []):
                self._merge_affordance(final, aff)

        # Clamp all values to 0.0-1.0
        for aff_id in final:
            final[aff_id] = max(0.0, min(1.0, final[aff_id]))

        return final

    def _merge_affordance(self, final: dict, aff: Affordance) -> None:
        """Merge an affordance, taking the higher intensity."""
        current = final.get(aff.affordance_id, 0.0)
        final[aff.affordance_id] = max(current, aff.intensity)
```

---

## 7. Complete Example: Tile Behind a Waterfall

### Layer-by-Layer Computation

```python
# Starting position: rocky ledge behind waterfall, night, heavy rain

# Layer 1: World Rules
{
    "falls": 1.0,
    "forced_motion": 0.0,
    "emits_sound": 1.0,
}

# Layer 2: Biome (cliffside)
+ {
    "elevated": 0.7,
    "exposes": 0.5,
}

# Layer 3: Tile Base (rocky_ledge)
+ {
    "supports": 0.8,
    "slippery": 0.3,
    "injures": 0.3,
}

# Layer 4: Tile State (wet)
+ {
    "slippery": +0.4,    # 0.3 + 0.4 = 0.7
    "supports": -0.2,    # 0.8 - 0.2 = 0.6
}

# Layer 5: Entity (waterfall, adjacent)
+ {
    "conceals": 0.9,
    "deadens_sound": 0.7,
    "forced_motion": 0.6,
    "obscures_vision": 0.8,
}

# Layer 6: Weather (heavy_rain)
+ {
    "slippery": +0.4,    # 0.7 + 0.4 = 1.1 → clamped to 1.0
    "visibility": -0.4,
    "disorients": 0.3,
}

# Layer 7: Temporal (night)
+ {
    "visibility": -0.4,  # Already modified
    "conceals": +0.3,    # 0.9 + 0.3 = 1.2 → clamped to 1.0
}
```

### Final Computed Affordances

```python
{
    "supports": 0.6,
    "slippery": 1.0,          # Maximum danger
    "conceals": 1.0,          # Perfect hiding
    "deadens_sound": 0.7,     # Very quiet
    "injures": 0.3,           # Moderate risk
    "forced_motion": 0.6,     # Water pushes
    "exposes": 0.5,           # Still visible from some angles
    "elevated": 0.7,          # Height advantage
    "obscures_vision": 0.8,   # Hard to see through
    "disorients": 0.3,        # Slightly confusing
}
```

**No scripts. No "behind waterfall" exception.**
**Just layered physics.**

---

## 8. Tile Adjacency (Edges Are Dangerous)

Tiles inherit **partial affordances** from neighbors.

### Adjacency Rules

```python
class AdjacentAffordanceSpread:
    """How affordances spread to neighboring tiles."""

    # Spread factors (what % reaches adjacent tiles)
    SPREAD_FACTORS = {
        "conceals": 0.4,        # Partial hiding near cover
        "deadens_sound": 0.3,   # Some sound masking nearby
        "illuminates": 0.6,     # Light spreads well
        "threatens": 0.5,       # Danger is nearby
        "burns": 0.3,           # Heat spreads somewhat
        "poisons": 0.2,         # Gas disperses
    }

    def get_adjacent_affordances(
        self,
        tile: TileBase,
        neighbor: TileBase,
        world: WorldGrid,
    ) -> dict[str, float]:
        """Get affordances that spread from neighbor to tile."""

        neighbor_affs = self.compute(neighbor, ...)
        spread = {}

        for aff_id, intensity in neighbor_affs.items():
            if aff_id in self.SPREAD_FACTORS:
                spread[aff_id] = intensity * self.SPREAD_FACTORS[aff_id]

        return spread
```

### Example: Standing Near Waterfall

```python
# Tile adjacent to waterfall (not behind it)

# Waterfall's affordances
waterfall = {
    "conceals": 0.9,
    "deadens_sound": 0.7,
}

# Adjacent tile receives (with spread factors)
adjacent = {
    "conceals": 0.9 * 0.4 = 0.36,        # Partially hidden
    "deadens_sound": 0.7 * 0.3 = 0.21,   # Some sound masking
}
```

### Why This Matters

This enables:
- **Gradual transitions**: "Almost hidden"
- **Risky peeking**: "You're partially concealed"
- **Proximity tactics**: "Stay close to the waterfall"

---

## 9. Verticality Without 3D Maps

Tiles support height metadata in 2D space.

### Elevation System

```python
@dataclass
class TileElevation:
    """Height information for a tile."""

    elevation: int          # Height level (0 = ground, 1 = raised, -1 = pit)
    climbable_up: bool      # Can ascend from here
    climbable_down: bool    # Can descend from here
    fall_risk: float        # 0.0 to 1.0

# Example: Fire escape
fire_escape = TileBase(
    tile_id="fire_escape",
    elevation=2,
    base_affordances=[
        Affordance("supports", intensity=0.7),
        Affordance("elevated", intensity=0.8),
        Affordance("climbable", intensity=0.9),
        Affordance("falls", intensity=0.4, conditions={"edge": "true"}),
    ],
)
```

### Elevation Effects

| Effect | How |
|--------|-----|
| **Fall risk** | `falls` affordance activates at edges |
| **Line of sight** | Higher elevation sees further |
| **Sound travel** | Sound travels up (reduced), down (normal) |
| **Forced movement** | Falling down is faster than climbing up |

### Elevation in ASCII

```
Street Level (0):     ════════════════
                      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

Fire Escape (2):               ┌─────┐
                               │  @  │
                               └──┬──┘
                                  │
Building Roof (4):         ╔═══════════╗
                           ║           ║
```

---

## 10. Tile State Is Mutable (World Memory)

**Tiles remember what happened.**

### State Examples

| State | Applied When | Affordance Effects |
|-------|--------------|-------------------|
| `wet` | Rain, water, spill | `slippery +0.4`, `supports -0.2` |
| `bloodied` | Violence | `slippery +0.2`, `signals_violence 0.8` |
| `burned` | Fire | `unstable +0.5`, `injures +0.3` |
| `cracked` | Impact | `supports -0.3`, `unstable +0.5` |
| `flooded` | Rising water | `drowns 0.4`, `traversal +0.8` |
| `darkened` | Light destroyed | `conceals +0.3`, `visibility -0.4` |

### State Accumulation

```python
class TileStateManager:
    """Manage mutable tile states."""

    def apply_state(self, tile: TileBase, state: str) -> None:
        """Apply a state to a tile."""
        if state not in tile.state:
            tile.state.append(state)
            tile.history.append(TileEvent(
                event_type="state_applied",
                state=state,
                timestamp=self.current_time,
            ))

    def decay_states(self, tile: TileBase, dt: float) -> None:
        """Some states decay over time."""

        DECAY_RATES = {
            "wet": 0.01,        # Dries slowly
            "bloodied": 0.005,  # Dries very slowly
            "burning": 0.02,    # Burns out
        }

        for state in tile.state[:]:
            if state in DECAY_RATES:
                # Track decay progress
                if self._should_remove(state, dt, DECAY_RATES[state]):
                    tile.state.remove(state)
```

### Returning to Changed Tiles

```python
# Player returns to alley where fight happened

tile.state = ["bloodied", "cracked"]

# Computed affordances now include:
{
    "slippery": 0.2,           # Blood
    "signals_violence": 0.8,   # Something happened here
    "unstable": 0.5,           # Damaged
    "supports": 0.5,           # Less stable
}

# LLM narration:
"The alley looks different now. Dark stains on the concrete.
 The ground feels wrong underfoot. This place remembers."
```

---

## 11. Discovery vs Reality (Critical for Exploration)

**Tiles have hidden affordances.**

### Hidden Affordance Schema

```python
@dataclass
class HiddenAffordance:
    """An affordance the player doesn't know about yet."""

    affordance: Affordance
    known: bool = False
    suspected: bool = False
    revealed: bool = False
    reveal_condition: str           # "player_enters", "examine", "story_reveal"
```

### Example: Secret Passage

```python
wall_tile = TileBase(
    tile_id="brick_wall",
    base_affordances=[
        Affordance("blocks", intensity=1.0),
    ],
    hidden_affordances=[
        HiddenAffordance(
            affordance=Affordance("connects", intensity=1.0,
                                   enables=["passage"]),
            reveal_condition="player_examines_closely",
        ),
    ],
)
```

### Discovery Flow

1. **Unknown**: Player sees solid wall, `blocks` affordance
2. **Suspected**: Dialogue hints at passage, player suspects
3. **Revealed**: Player examines carefully, discovers loose brick
4. **Known**: Player has used passage, fully aware

### LLM Behavior

| State | LLM Allowed |
|-------|-------------|
| Unknown | Cannot mention |
| Suspected | "Something about this wall..." |
| Revealed | "The loose brick is here." |
| Known | "You know this way." |

**The LLM may hint, but never confirm unknowns.**

---

## 12. Performance & Infinite World Safety

**You do NOT simulate everything.**

### Simulation Rules

```python
class PerformanceRules:
    """Rules for efficient world simulation."""

    PERCEPTION_RADIUS = 15          # Tiles around player
    SOUND_RADIUS = 25               # Sound propagation limit
    SIMULATION_RADIUS = 20          # Full simulation range

    # Beyond simulation radius
    DISTANT_TILE_BEHAVIOR = {
        "affordances": "cached",     # Use last computed
        "entities": "frozen",        # Don't update
        "state": "preserved",        # Keep state but don't decay
    }

    def should_simulate(self, tile: TileBase, player_pos: tuple) -> bool:
        """Determine if tile needs full simulation."""
        distance = self._distance(tile.position, player_pos)
        return distance <= self.SIMULATION_RADIUS

    def get_tile_mode(self, distance: float) -> str:
        """Get simulation mode for tile at distance."""
        if distance <= self.PERCEPTION_RADIUS:
            return "full"           # Full computation
        elif distance <= self.SIMULATION_RADIUS:
            return "partial"        # Compute but don't render
        else:
            return "cached"         # Use cached values
```

### Lazy Affordance Computation

```python
class LazyAffordanceCache:
    """Compute affordances only when needed."""

    cache: dict[tuple[int, int], CachedAffordances]

    def get_affordances(self, tile: TileBase, context: Context) -> dict:
        """Get affordances, computing only if stale."""

        cache_key = tile.position

        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if not self._is_stale(cached, context):
                return cached.affordances

        # Recompute
        affordances = self.computer.compute(tile, ...)
        self.cache[cache_key] = CachedAffordances(
            affordances=affordances,
            timestamp=self.current_time,
            context_hash=self._hash_context(context),
        )

        return affordances

    def _is_stale(self, cached: CachedAffordances, context: Context) -> bool:
        """Check if cached values are still valid."""
        return (
            self.current_time - cached.timestamp > 1.0 or  # Time passed
            self._hash_context(context) != cached.context_hash  # Context changed
        )
```

### What This Enables

| Capability | How |
|------------|-----|
| Infinite wandering | Only nearby tiles computed |
| STT reaction fast | No distant tile computation |
| Simulation stable | Bounded computation per frame |
| Memory efficient | Cache eviction for distant tiles |

---

## 13. LLM Boundary (Strict)

### What LLM Is Allowed To Do

| ✅ Allowed | Example |
|------------|---------|
| Identify which tiles are referenced | "Behind waterfall" → tile at (45, 24) |
| Map language → spatial intent | "Sneak through" → movement + stealth modifier |
| Describe computed results | Narrate outcome based on simulation |

### What LLM Is NOT Allowed To Do

| ❌ Forbidden | Why |
|--------------|-----|
| Invent tile states | States come from simulation events |
| Modify affordances | Affordances are computed, not narrated |
| Decide traversal success | Physics simulation decides |
| Create new tiles | Procedural generator creates tiles |

### Enforcement

```python
class LLMBoundaryEnforcer:
    """Ensure LLM stays within allowed actions."""

    def validate_interpretation(self, llm_output: dict) -> ValidationResult:
        """Validate LLM interpretation is in bounds."""

        errors = []

        # Check for forbidden fields
        FORBIDDEN = ["create_tile", "modify_affordance", "set_outcome"]
        for field in FORBIDDEN:
            if field in llm_output:
                errors.append(f"LLM attempted forbidden action: {field}")

        # Check target exists
        if "target" in llm_output:
            if not self.world.entity_exists(llm_output["target"]):
                errors.append(f"LLM referenced non-existent target")

        return ValidationResult(valid=len(errors) == 0, errors=errors)
```

---

## 14. ASCII Rendering Alignment

**Rendering uses affordance intensity, not tile type.**

### Rendering Rules

| Affordance | Visual Effect |
|------------|---------------|
| High `slippery` | Jitter/shimmer animation |
| High `conceals` | Dense noise/shadow overlay |
| High `danger` | Flicker, high contrast |
| High `illuminates` | Bright characters |
| High `obscures_vision` | Fog overlay |
| High `unstable` | Shake effect |

### Implementation

```python
class AffordanceRenderer:
    """Render tiles based on affordance intensities."""

    def get_tile_effect(self, affordances: dict) -> RenderEffect:
        """Get visual effect based on affordances."""

        effects = []

        if affordances.get("slippery", 0) > 0.7:
            effects.append(JitterEffect(intensity=affordances["slippery"]))

        if affordances.get("conceals", 0) > 0.5:
            effects.append(ShadowOverlay(density=affordances["conceals"]))

        if affordances.get("threatens", 0) > 0.6:
            effects.append(FlickerEffect(rate=affordances["threatens"]))

        if affordances.get("illuminates", 0) > 0.5:
            effects.append(BrightnessBoost(amount=affordances["illuminates"]))

        return CompositeEffect(effects)

    def render_tile(self, tile: TileBase, affordances: dict) -> str:
        """Render tile with affordance-based effects."""

        base_char = self.get_base_char(tile)
        color = self.get_affordance_color(affordances)
        effect = self.get_tile_effect(affordances)

        return effect.apply(base_char, color)
```

### The Screen Teaches the Player

```
High slippery (0.9):     ≈~≈~≈     (shimmer)
High conceals (0.8):     ▒▓▒▓▒     (dense shadow)
High danger (0.7):       ▓█▓█▓     (high contrast flicker)
High illuminates (0.9):  ░░░░░     (bright)
```

---

## 15. Summary (Key Insight)

You are **not** building:
```
rooms with exits
```

You are building:
```
a layered physical reality expressed in text
```

**Tiles don't say "you can."**

They say:
```
"Here is what the world allows — try it."
```

---

## Appendix: Quick Reference

### Inheritance Stack

```
7. Temporal (night, chaos)
6. Weather (rain, fog)
5. Entities (waterfall, NPC)
4. State (wet, bloodied)
3. Tile Base (rocky_ledge)
2. Biome (cliffside)
1. World Rules (gravity)
```

### State Types

```
wet, bloodied, burned, cracked, flooded, darkened, unstable, frozen
```

### Spread Factors

```
conceals: 0.4, deadens_sound: 0.3, illuminates: 0.6,
threatens: 0.5, burns: 0.3, poisons: 0.2
```

### LLM Boundaries

```
✅ Identify tiles, map intent, narrate outcomes
❌ Invent states, modify affordances, decide success
```

---

*End of Tile Inheritance Model*
