# Module 08: Behavioral Circuits

## Overview

The Behavioral Circuit is the universal interaction model for all entities in the world. Every object, creature, and environmental element uses this unified structure, enabling consistent LLM evaluation and emergent behavior.

---

## Core Structure

```python
BehaviorCircuit {
    id: str                       # Unique identifier
    type: CircuitType             # mechanical, biological, environmental

    # Input Signals - What can trigger this entity
    input_signals: [
        "press", "kick", "poke", "look", "listen", "say",
        "heat", "wet", "electric", "proximity", "time"
    ]

    # Processing - LLM evaluates input with context
    process: {
        context: WorldContext     # Current world state
        history: list[Event]      # Past interactions
        personality: dict         # For biological entities
        condition: dict           # Current state factors
    }

    # Output Signals - What this entity produces
    output_signals: [
        "move", "scurry", "collapse", "play_sound",
        "change_state", "emit", "trigger", "damage"
    ]

    # Persistent State
    state: {
        health: float             # 0.0 to 1.0
        power: float              # Energy/charge level
        fatigue: float            # Wear/tiredness
        trust: float              # For NPCs
        age: float                # Time since creation
        last_interaction: timestamp
        custom: dict              # Entity-specific state
    }

    # Interaction possibilities
    affordances: list[str]
}
```

---

## Circuit Types

### Mechanical Circuits

Objects with physical mechanisms that respond predictably (with wear/degradation):

```python
class MechanicalCircuit(BehaviorCircuit):
    type = CircuitType.MECHANICAL

    properties = {
        "material": str           # metal, wood, plastic
        "lubrication": float      # Affects friction/jamming
        "age": float              # Degradation factor
        "last_maintenance": timestamp
    }
```

**Examples**:
- **Elevator Button**: Sparks when old, sticks when wet, fails when damaged
- **Gear Assembly**: Grinds when dry, jams when overloaded
- **Lock**: Picks easier when worn, rusts in moisture

### Biological Circuits

Living entities with psychology and survival instincts:

```python
class BiologicalCircuit(BehaviorCircuit):
    type = CircuitType.BIOLOGICAL

    properties = {
        "species": str
        "fear": float             # 0.0 to 1.0
        "hunger": float           # 0.0 to 1.0
        "trust": dict[str, float] # Per-entity trust levels
        "memory": list[Event]     # What they remember
        "personality": Personality
    }
```

**Examples**:
- **Rat**: Scurries when startled, bites when cornered, freezes when uncertain
- **Guard NPC**: Investigates sounds, remembers player actions, spreads rumors
- **Plant**: Grows toward light, wilts without water, spreads seeds

### Environmental Circuits

Natural phenomena and terrain features:

```python
class EnvironmentalCircuit(BehaviorCircuit):
    type = CircuitType.ENVIRONMENTAL

    properties = {
        "terrain_type": str
        "fluid_dynamics": dict    # For water, lava, gas
        "stability": float        # Collapse threshold
        "propagation": dict       # Sound, heat, etc.
    }
```

**Examples**:
- **Waterfall**: Splashes when disturbed, echoes sound, creates mist
- **Cliff Edge**: Crumbles under weight, reveals caves when broken
- **Wind Corridor**: Pushes objects, carries sounds, extinguishes flames

---

## Signal Processing

### Input Signal Evaluation

When an input signal reaches an entity:

```python
def evaluate_signal(circuit, signal, context):
    """LLM-based signal evaluation."""

    prompt = f"""
    Entity: {circuit.description}
    Current State: {circuit.state}
    History: {circuit.history[-5:]}  # Last 5 interactions
    Environment: {context.environment}

    Received Signal: {signal.type} from {signal.source}
    Signal Strength: {signal.strength}

    What happens? Consider:
    - Entity's nature and current condition
    - Previous interactions with this source
    - Environmental factors
    - Random emergence factor

    Output: behavior_signals, state_changes, flavor_text
    """

    return llm.evaluate(prompt)
```

### Output Signal Propagation

Outputs ripple through the world:

```python
def propagate_output(signal, source_circuit, world):
    """Propagate output signal to affected entities."""

    affected_tiles = calculate_signal_reach(signal, source_circuit.position)

    for tile in affected_tiles:
        for entity in tile.entities:
            if entity.responds_to(signal.type):
                entity.receive_signal(signal.attenuate(distance))
```

---

## Affordances

Affordances define what can be done to/with an entity:

### Default Affordances by Type

| Type | Default Affordances |
|------|---------------------|
| Mechanical | press, activate, repair, break, examine |
| Biological | talk, feed, frighten, befriend, attack |
| Environmental | traverse, shelter, harvest, damage |

### Affordance Inheritance

Entities inherit affordances from their tile but can override:

```python
class Entity:
    def get_affordances(self):
        # Start with tile's affordances
        affordances = self.tile.affordances.copy()

        # Add entity-specific affordances
        affordances.extend(self.own_affordances)

        # Remove blocked affordances
        for blocked in self.blocked_affordances:
            affordances.remove(blocked)

        return affordances
```

**Example**:
- Rock tile: `[climbable, breakable, solid]`
- Trapdoor on rock: adds `[openable, triggerable]`, removes `[solid]`

---

## State Management

### State Changes

State changes are tracked and can trigger cascading effects:

```python
def update_state(circuit, changes):
    """Update circuit state with cascading triggers."""

    old_state = circuit.state.copy()

    for key, value in changes.items():
        circuit.state[key] = value

        # Check for threshold triggers
        if key == "health" and value <= 0:
            circuit.emit_signal("death")

        if key == "power" and value <= 0:
            circuit.emit_signal("power_failure")

        if key == "trust" and value > 0.8:
            circuit.emit_signal("befriended")

    # Log state change for memory
    log_state_change(circuit, old_state, circuit.state)
```

### Persistent State

State persists between sessions:

```python
def serialize_circuit(circuit):
    return {
        "id": circuit.id,
        "type": circuit.type,
        "state": circuit.state,
        "history": circuit.history[-100:],  # Last 100 events
        "position": circuit.position
    }
```

---

## Example: Complete Interaction

```
Player: "kick the rusty elevator button"

1. Parse Input:
   - Action: kick
   - Target: elevator button (id: elev_btn_001)
   - Modifier: rusty (recognized as state indicator)

2. Gather Context:
   - Button state: health=0.3, power=0.8, age=high
   - Environment: humid, poorly lit
   - History: last pressed 2 hours ago

3. LLM Evaluation:
   "The button is old and corroded. A kick is aggressive
   input that could damage it further. Given humidity
   and age, there's a chance of electrical spark..."

4. Output Signals:
   - spark (brief electrical discharge)
   - stick (button jams halfway)
   - grind_sound (mechanical protest)
   - no_movement (elevator doesn't respond)

5. State Changes:
   - health: 0.3 -> 0.2
   - jammed: False -> True

6. Propagation:
   - Sound reaches rat entity (3 tiles away)
   - Rat receives "loud_noise" signal
   - Rat evaluates: fear rises, freezes

7. Render:
   "The button sparks briefly, then sticks halfway.
   A grinding sound echoes through the shaft.
   A rat in the corner freezes, ears perked."
```

---

## Integration Points

- **Tile Grid** (Module 09): Circuits exist within tiles, inherit affordances
- **Perception Systems** (Module 10): Sound/light signals propagate
- **Memory Bank** (Module 03): Interactions logged for NPC memory
- **Narrative Spine** (Module 01): Significant events flag for story tracking

---

## Implementation Notes

1. **LLM Caching**: Common signal/state combinations can be cached
2. **Batch Evaluation**: Multiple signals evaluated together for efficiency
3. **State Compression**: Old history pruned, only significant events kept
4. **Deterministic Seeds**: Random factors use seeded RNG for replay
