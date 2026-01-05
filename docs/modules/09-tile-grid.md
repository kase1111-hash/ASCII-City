# Module 09: Tile Grid System

## Overview

The world is built on a tile grid where each tile carries rich information about terrain, contents, and environmental properties. Tiles form the foundation for spatial relationships, affordance inheritance, and physics propagation.

---

## Tile Structure

```python
class Tile:
    position: Position            # (x, y, z) coordinates

    # Core Properties
    terrain_type: TerrainType     # rock, water, soil, metal, void
    passable: bool                # Can entities traverse?
    opaque: bool                  # Blocks line of sight?
    height: float                 # Z-level elevation

    # Contents
    entities: list[Entity]        # Objects, creatures, items
    features: list[Feature]       # Permanent terrain features

    # Environmental
    environment: {
        fluid: FluidType | None   # water, lava, gas, None
        temperature: float        # -100 to 100 scale
        sound_level: float        # Current ambient noise
        light_level: float        # 0.0 (dark) to 1.0 (bright)
        moisture: float           # 0.0 (dry) to 1.0 (flooded)
    }

    # Affordances (what can be done here)
    affordances: list[str]
```

---

## Terrain Types

### Default Properties by Terrain

| Terrain | Passable | Opaque | Default Affordances |
|---------|----------|--------|---------------------|
| **Rock** | No | Yes | climbable, breakable, solid, mineable |
| **Water** | Partial | No | swimmable, splashable, drownable |
| **Soil** | Yes | No | diggable, plantable, trackable |
| **Metal** | Yes | Yes | conductive, climbable, resonant |
| **Void** | No | No | fallable, echoing |
| **Wood** | Yes | Yes | flammable, climbable, breakable |
| **Glass** | No | Partial | breakable, transparent, reflective |

### Terrain Modifiers

Tiles can have modifiers that affect their base properties:

```python
class TerrainModifier:
    type: str                     # wet, frozen, cracked, overgrown
    intensity: float              # 0.0 to 1.0
    affects: list[str]            # Which properties modified
```

**Examples**:
- `wet` rock: slippery, reduced climb success
- `frozen` water: becomes passable, breakable
- `cracked` floor: may collapse under weight

---

## Z-Levels and Height

The world supports vertical space:

```python
class Position:
    x: int
    y: int
    z: int                        # Ground level = 0, up = positive

# Height affects
- Line of sight (looking down/up)
- Sound propagation (echoes in tall spaces)
- Fall damage calculation
- Environmental effects (rain reaches top first)
```

### Multi-Level Structures

```
Level 2:  [===]     <- Roof
Level 1:  |   |     <- Walls with interior
Level 0:  =====     <- Floor/Ground
Level -1: [cave]    <- Underground
```

---

## Affordance System

### Affordance Inheritance

Tiles pass affordances to contained entities unless overridden:

```python
def get_entity_affordances(entity, tile):
    """Calculate effective affordances for an entity."""

    # Start with tile affordances
    affordances = set(tile.affordances)

    # Add entity's own affordances
    affordances.update(entity.own_affordances)

    # Remove any blocked by entity
    affordances -= set(entity.blocked_affordances)

    # Apply environmental modifiers
    if tile.environment.moisture > 0.7:
        affordances.add("slippery")
        if "flammable" in affordances:
            affordances.remove("flammable")

    return list(affordances)
```

### Common Affordances

| Affordance | Meaning | Enabled By |
|------------|---------|------------|
| `climbable` | Can be climbed | Rock, trees, ladders |
| `breakable` | Can be destroyed | Glass, wood, weak stone |
| `flammable` | Can catch fire | Wood, paper, cloth |
| `swimmable` | Can swim through | Water, non-viscous fluid |
| `hideable` | Can hide behind/in | Bushes, furniture, shadows |
| `triggerable` | Activates something | Buttons, levers, plates |
| `collectible` | Can be picked up | Items, loot, tools |
| `conductive` | Carries electricity | Metal, water, wires |

---

## Entity Placement

### Entity Types on Tiles

```python
class Entity:
    """Base class for tile contents."""
    circuit: BehaviorCircuit      # How it behaves
    position: Position            # Where it is
    size: Size                    # How much space it takes
    layer: Layer                  # ground, object, ceiling

class Layer(Enum):
    GROUND = 0    # Floor items, rugs, markings
    OBJECT = 1    # Furniture, creatures, characters
    CEILING = 2   # Hanging items, lights, signs
```

### Stacking Rules

```python
def can_place_entity(tile, entity):
    """Check if entity can be placed on tile."""

    # Check tile passability
    if not tile.passable and entity.requires_passable:
        return False

    # Check layer conflicts
    same_layer = [e for e in tile.entities if e.layer == entity.layer]
    if sum(e.size for e in same_layer) + entity.size > MAX_LAYER_SIZE:
        return False

    # Check specific conflicts
    for existing in tile.entities:
        if conflicts(existing, entity):
            return False

    return True
```

---

## Environmental Properties

### Temperature

Affects entity behavior and state:

```python
temperature_effects = {
    (-100, -20): "freezing",      # Water freezes, organisms slow
    (-20, 0): "cold",             # Reduced stamina, visible breath
    (0, 30): "comfortable",       # Normal behavior
    (30, 50): "hot",              # Faster fatigue, fire risk
    (50, 100): "extreme"          # Damage over time, spontaneous combustion
}
```

### Moisture

Affects flammability, movement, and sound:

```python
moisture_effects = {
    (0.0, 0.2): "dry",            # Fire spreads fast, dust clouds
    (0.2, 0.5): "normal",         # Standard behavior
    (0.5, 0.8): "damp",           # Slippery, fire resistant
    (0.8, 1.0): "flooded"         # Swimming required, muffled sound
}
```

### Light Level

Affects visibility and NPC behavior:

```python
light_effects = {
    (0.0, 0.1): "pitch_black",    # No vision without light source
    (0.1, 0.3): "dim",            # Limited vision, -50% detection
    (0.3, 0.7): "normal",         # Standard visibility
    (0.7, 1.0): "bright"          # Enhanced vision, +25% detection
}
```

---

## Pathfinding

### Movement Costs

```python
def get_movement_cost(from_tile, to_tile, entity):
    """Calculate movement cost between tiles."""

    base_cost = 1.0

    # Terrain type cost
    base_cost *= TERRAIN_COST[to_tile.terrain_type]

    # Height difference
    height_diff = abs(to_tile.height - from_tile.height)
    base_cost += height_diff * 0.5

    # Environmental modifiers
    if to_tile.environment.moisture > 0.7:
        base_cost *= 1.5  # Harder to move in water

    if to_tile.environment.light_level < 0.2:
        base_cost *= 1.2  # Slower in darkness

    # Entity-specific modifiers
    base_cost *= entity.movement_modifiers.get(to_tile.terrain_type, 1.0)

    return base_cost
```

### Tile Queries

```python
class TileGrid:
    def get_tile(self, x, y, z=0) -> Tile
    def get_adjacent(self, tile) -> list[Tile]
    def get_in_radius(self, center, radius) -> list[Tile]
    def get_line_of_sight(self, from_tile, to_tile) -> list[Tile]
    def find_path(self, start, end, entity) -> list[Tile]
```

---

## Tile Events

Tiles can emit events when their state changes:

```python
class TileEvent:
    type: EventType               # entered, exited, damaged, flooded
    tile: Tile
    cause: Entity | None
    timestamp: float

# Event handlers
def on_tile_entered(tile, entity):
    """Called when entity enters a tile."""
    for circuit in tile.entities:
        circuit.receive_signal(Signal("proximity", entity))

    # Check for triggers
    if "triggerable" in tile.affordances:
        trigger_plate(tile, entity)

def on_tile_damaged(tile, damage):
    """Called when tile takes damage."""
    if tile.terrain_type == "glass" and damage > 10:
        shatter_tile(tile)

    if tile.stability < damage:
        collapse_tile(tile)
```

---

## Serialization

```python
def serialize_tile(tile):
    return {
        "position": [tile.position.x, tile.position.y, tile.position.z],
        "terrain": tile.terrain_type,
        "modifiers": [m.to_dict() for m in tile.modifiers],
        "environment": tile.environment,
        "entities": [e.id for e in tile.entities],
        "affordances": tile.affordances
    }

def serialize_grid(grid):
    return {
        "dimensions": [grid.width, grid.height, grid.depth],
        "tiles": {pos_key(t): serialize_tile(t) for t in grid.all_tiles()},
        "entities": {e.id: e.serialize() for e in grid.all_entities()}
    }
```

---

## Integration Points

- **Behavioral Circuits** (Module 08): Entities on tiles
- **Perception Systems** (Module 10): Tiles affect propagation
- **Environment & Weather** (Module 04): Weather modifies tile properties
- **ASCII Renderer** (Module 05): Tiles determine visual rendering
