# Module 12: Art Creation Framework

## Overview

This module defines the complete framework for creating both **static art** (scenery, backgrounds, decorations) and **dynamic entities** (creatures, NPCs, interactive objects) within the ASCII Art Studio. The system leverages LLM assistance to render complete scenes within seconds and generate animations and personalities for entities.

---

## Art Categories

### Static Art

Non-interactive visual elements that form the world's backdrop:

```python
class StaticArt(ASCIIArt):
    """Decorative, non-interactive art."""

    category = ArtCategory.STATIC

    # Static art properties
    layer: RenderLayer             # background, midground, foreground
    tile_coverage: TileCoverage    # single, multi_tile, tiling_pattern
    transparency: dict[str, bool]  # Which characters are "see-through"

    # No behavioral circuit - purely visual
    circuit: None
```

**Examples**:
- Background mountains, clouds, sky
- Floor patterns, wall textures
- Decorative borders, frames
- Environmental details (distant trees, rocks)

### Dynamic Entities

Interactive elements with behavioral circuits and potential animation:

```python
class DynamicEntity(ASCIIArt):
    """Interactive entity with behavior and animation."""

    category = ArtCategory.DYNAMIC

    # Behavioral properties
    circuit: BehaviorCircuit       # How it responds to input
    personality: PersonalityTemplate  # Behavior patterns

    # Animation
    animations: dict[str, Animation]  # idle, walk, attack, etc.
    current_state: EntityState

    # Interaction
    affordances: list[str]         # What can be done to/with it
    dialogue: DialogueTree | None  # For NPCs
```

**Examples**:
- NPCs with personalities
- Creatures (rats, birds, monsters)
- Interactive objects (doors, switches, chests)
- Environmental hazards (traps, moving platforms)

---

## Creation Modes in Studio

### Mode 1: Static Art Creation

```
> create static

=== Static Art Studio ===

What are you creating?
1. Background element (sky, distant scenery)
2. Terrain texture (floor, wall pattern)
3. Decoration (furniture, plants, details)
4. Overlay effect (fog, lighting, weather)

> 1

[Background Mode]
Canvas: 40x12 (full scene width)
Layer: background (renders behind everything)

Draw your background, or say "generate mountain range"
```

### Mode 2: Dynamic Entity Creation

```
> create entity

=== Entity Studio ===

What type of entity?
1. NPC (character with dialogue)
2. Creature (animal/monster)
3. Interactive Object (responds to actions)
4. Hazard (environmental danger)

> 2

[Creature Mode]
Size: 3x3 (adjustable)
Will need: appearance, animations, personality

Start with appearance, or say "generate rat"
```

---

## LLM-Assisted Rapid Creation

### Instant Scene Generation

Request complete scenes and get them in seconds:

```python
class SceneGenerator:
    """LLM-powered rapid scene creation."""

    def generate_scene(self, description: str) -> Scene:
        """Generate complete scene from natural language."""

        prompt = f"""
        Create an ASCII scene for: "{description}"

        Generate:
        1. Background layer (static art)
        2. Midground elements (terrain, structures)
        3. Foreground details (decorations)
        4. Entity placements (if mentioned)
        5. Lighting/atmosphere suggestions

        Output as structured scene data with ASCII tiles.
        Respond in under 3 seconds.
        """

        response = self.llm.generate(prompt, max_time=3.0)
        return self.parse_scene(response)
```

**Example Usage**:

```
> generate scene "abandoned warehouse at night, rain, one guard patrolling"

[Generating... 2.3s]

Scene created:
┌────────────────────────────────────────┐
│  ~~~  ~~~  ~~~  ~~~  ~~~  ~~~  ~~~    │ ← rain (animated)
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │ ← warehouse wall
│ ▓▓▓  ┌──────────────────────┐  ▓▓▓   │
│ ▓▓▓  │  ░░░░░░░░░░░░░░░░░░  │  ▓▓▓   │ ← interior
│ ▓▓▓  │  ░░░ [crates] ░░░░░  │  ▓▓▓   │
│ ▓▓▓  │  ░░░░░░░░░░░ @→ ░░░  │  ▓▓▓   │ ← guard (entity)
│ ▓▓▓  └──────────────────────┘  ▓▓▓   │
│ ════════════════════════════════════  │ ← ground
└────────────────────────────────────────┘

Entities created:
- Guard (@): patrolling, alert personality
- Crates: interactive, searchable

Edit? [y/n]
```

### Instant Entity Generation

```python
def generate_entity(self, description: str) -> DynamicEntity:
    """Generate entity with appearance, animations, and personality."""

    prompt = f"""
    Create an ASCII entity: "{description}"

    Generate:
    1. Base appearance (idle state)
    2. Animation frames: idle, move_left, move_right, action
    3. Personality traits (aggression, fear, curiosity, etc.)
    4. Behavioral circuit (input signals it responds to)
    5. Suggested affordances

    Keep each frame 3-5 characters wide for performance.
    """

    response = self.llm.generate(prompt)
    return self.build_entity(response)
```

**Example**:

```
> generate entity "nervous street cat, skinny, always watching"

[Generating... 1.8s]

Entity: Street Cat

Appearance (idle):
 /\_/\
( o.o )
 > ^ <

Animations:
- idle: ears twitch every 2s
- alert: ears up, eyes wide
- flee: blur effect, speed lines
- hunt: low crouch, focused

Personality:
- fear: 0.7 (high - runs from threats)
- curiosity: 0.6 (investigates sounds)
- aggression: 0.2 (only if cornered)
- trust: 0.1 (very wary of players)

Behavioral Circuit:
- Inputs: proximity, sound, food_present
- Outputs: flee, investigate, approach_cautiously

Accept? [y/n/edit]
```

---

## Personality Templates

### Predefined Templates

```python
class PersonalityTemplate:
    """Behavioral personality for entities."""

    name: str

    # Core traits (0.0 to 1.0)
    traits: {
        "aggression": float,      # Fight tendency
        "fear": float,            # Flee tendency
        "curiosity": float,       # Investigate tendency
        "loyalty": float,         # Protect/follow tendency
        "greed": float,           # Collect/hoard tendency
        "social": float,          # Interact with others tendency
    }

    # Behavioral patterns
    idle_behavior: IdleBehavior   # What it does when nothing happens
    threat_response: ThreatResponse
    player_attitude: Attitude     # How it treats player initially

    # Memory settings
    memory_duration: float        # How long it remembers
    grudge_factor: float          # How much bad experiences matter

# Predefined templates
TEMPLATES = {
    "timid_prey": PersonalityTemplate(
        name="Timid Prey",
        traits={"fear": 0.9, "curiosity": 0.3, "aggression": 0.1},
        idle_behavior=IdleBehavior.FORAGE,
        threat_response=ThreatResponse.FLEE,
    ),

    "territorial_predator": PersonalityTemplate(
        name="Territorial Predator",
        traits={"aggression": 0.8, "fear": 0.2, "curiosity": 0.4},
        idle_behavior=IdleBehavior.PATROL,
        threat_response=ThreatResponse.CHALLENGE,
    ),

    "curious_neutral": PersonalityTemplate(
        name="Curious Neutral",
        traits={"curiosity": 0.8, "fear": 0.4, "social": 0.6},
        idle_behavior=IdleBehavior.WANDER,
        threat_response=ThreatResponse.OBSERVE,
    ),

    "loyal_guardian": PersonalityTemplate(
        name="Loyal Guardian",
        traits={"loyalty": 0.9, "aggression": 0.5, "fear": 0.1},
        idle_behavior=IdleBehavior.GUARD,
        threat_response=ThreatResponse.PROTECT,
    ),

    "greedy_collector": PersonalityTemplate(
        name="Greedy Collector",
        traits={"greed": 0.9, "curiosity": 0.5, "aggression": 0.4},
        idle_behavior=IdleBehavior.SEARCH,
        threat_response=ThreatResponse.PROTECT_HOARD,
    ),
}
```

### Custom Personality Creation

```
> create personality

Name: Paranoid Merchant

Trait sliders:
  Aggression: [====------] 0.4
  Fear:       [========--] 0.8
  Curiosity:  [===-------] 0.3
  Loyalty:    [==========] 0.0
  Greed:      [==========-] 0.9
  Social:     [======----] 0.6

Idle behavior: GUARD (watches surroundings)
Threat response: BRIBE (offers items to leave)
Player attitude: SUSPICIOUS (requires trust building)

Memory: Long (remembers for days)
Grudge: High (never forgets theft)

Save as template? [y/n]
```

---

## Animation System

### Animation Structure

```python
class Animation:
    """Frame-based ASCII animation."""

    name: str
    frames: list[AnimationFrame]
    duration: float               # Total animation time
    loop: bool

    # Triggers
    trigger: AnimationTrigger     # always, on_action, on_state
    state_condition: str | None   # "moving", "attacking", etc.

class AnimationFrame:
    tiles: list[list[str]]        # ASCII art for this frame
    duration: float               # How long this frame shows
    offset: tuple[int, int]       # Position offset from base
    sound: str | None             # Optional sound effect
```

### Animation Creation in Studio

```
> animate guard

Current appearance:
  @
 /|\
 / \

[Animation Mode]
Creating: walk_right

Frame 1 (base):    Frame 2:          Frame 3:
  @                   @                 @
 /|\                 /|>               /|\
 / \                / /               < \

Duration per frame: 0.2s
Loop: yes

Preview? [y/n] > y

[Playing animation...]

  @     @     @     @     @
 /|\   /|>   /|\   /|>   /|\
 / \   / /   < \   / /   / \

Save? [y/n]
```

### LLM Animation Assistance

```python
def generate_animations(self, entity: DynamicEntity, actions: list[str]) -> dict[str, Animation]:
    """LLM generates animation frames for requested actions."""

    prompt = f"""
    Entity base appearance:
    ```
    {render_tiles(entity.tiles)}
    ```

    Generate animation frames for: {actions}

    Rules:
    - Keep same dimensions ({entity.width}x{entity.height})
    - Maintain character recognition
    - 2-4 frames per animation
    - Consider physics (walking = legs move)

    Output: frames for each action
    """

    return self.parse_animations(self.llm.generate(prompt))
```

---

## Complete Entity Creation Flow

### Step-by-Step Process

```
1. INITIATE
   > create entity "goblin guard with spear"

2. LLM GENERATES BASE
   [2.1s] Base appearance created

     o
    /|\
    / \ ─┼

3. REVIEW ANIMATIONS
   Generated animations: idle, walk, attack, death, alert

   [Preview each? y/n]

4. ASSIGN PERSONALITY
   Suggested: territorial_predator

   Customize? [y/n] > y

   Adjusted traits:
   - aggression: 0.7 (down from 0.8)
   - loyalty: 0.6 (guards location)

5. SET BEHAVIORAL CIRCUIT
   Inputs: proximity, sound, damage, command
   Outputs: patrol, attack, alert_others, flee

   Thresholds:
   - Attack if: proximity < 3 AND player_threat > 0.5
   - Alert if: sound_detected AND source_unknown
   - Flee if: health < 0.2

6. TEST IN SANDBOX
   > test entity

   [Sandbox loaded]
   Try interacting with your goblin...

   > approach slowly

   The goblin spots you. It raises its spear
   and barks a warning. "Halt!"

7. SAVE TO LIBRARY
   > save

   Entity "Goblin Guard" saved to library.
   - Available in: dungeon, cave, fortress
   - Variants will be generated on use
```

---

## Scene Composition

### Layered Rendering

```python
class Scene:
    """Complete scene with all layers."""

    name: str
    dimensions: tuple[int, int]

    # Art layers (back to front)
    background: list[StaticArt]   # Sky, distant scenery
    midground: list[StaticArt]    # Terrain, structures
    entities: list[DynamicEntity] # Interactive elements
    foreground: list[StaticArt]   # Overlays, effects

    # Environmental
    lighting: LightingState
    weather: WeatherState
    ambient_sounds: list[str]

    def render(self) -> list[list[str]]:
        """Composite all layers into final ASCII output."""
        canvas = self.create_canvas()

        for layer in [self.background, self.midground]:
            self.render_static_layer(canvas, layer)

        for entity in self.entities:
            self.render_entity(canvas, entity)

        for overlay in self.foreground:
            self.render_overlay(canvas, overlay)

        return canvas
```

### Rapid Scene Request Examples

```
> generate "cozy tavern interior, fireplace, 3 patrons, bartender"

> generate "dark forest path, moonlight, eyes watching from bushes"

> generate "cyberpunk alley, neon signs, rain, homeless robot"

> generate "ancient temple entrance, crumbling, guardian statues"
```

Each generates in 2-4 seconds with:
- Complete layered scene
- Placed entities with personalities
- Appropriate lighting/atmosphere
- Interactive elements tagged

---

## Integration with Behavioral Circuits

### Connecting Art to Behavior

```python
def bind_circuit_to_entity(entity: DynamicEntity, circuit: BehaviorCircuit):
    """Connect visual entity to behavioral circuit."""

    entity.circuit = circuit

    # Map animations to circuit outputs
    entity.animation_bindings = {
        "move": circuit.output_signals.get("move"),
        "attack": circuit.output_signals.get("attack"),
        "idle": circuit.output_signals.get("idle"),
        "react": circuit.output_signals.get("react"),
    }

    # Map appearance states to circuit state
    entity.appearance_bindings = {
        "health < 0.3": "injured_appearance",
        "alert == True": "alert_appearance",
        "friendly == True": "friendly_appearance",
    }
```

---

## Performance Considerations

### Rapid Generation Targets

| Operation | Target Time | Method |
|-----------|-------------|--------|
| Simple entity | < 2s | Cached templates + LLM delta |
| Complex entity | < 4s | Full LLM generation |
| Scene generation | < 5s | Parallel layer generation |
| Animation set | < 3s | LLM with frame constraints |

### Caching Strategy

```python
class GenerationCache:
    """Cache for rapid regeneration."""

    # Frequently used patterns
    template_cache: dict[str, ASCIIArt]

    # Recent generations (for variants)
    recent_cache: LRUCache[str, ASCIIArt]

    # Personality combinations
    personality_cache: dict[tuple, PersonalityTemplate]

    def get_or_generate(self, key: str, generator: Callable) -> ASCIIArt:
        if key in self.template_cache:
            return self.apply_variations(self.template_cache[key])
        return generator()
```

---

## Summary: Static vs Dynamic

| Aspect | Static Art | Dynamic Entity |
|--------|------------|----------------|
| **Purpose** | Visual backdrop | Interactive element |
| **Behavior** | None | Behavioral circuit |
| **Animation** | Optional (ambient) | Required (actions) |
| **Personality** | None | Required template |
| **Affordances** | Decoration only | Full interaction set |
| **Memory** | None | Remembers interactions |
| **LLM Role** | Appearance only | Appearance + behavior + dialogue |
| **Creation Time** | ~1s | ~3s |

---

## Integration Points

- **Module 08 (Behavioral Circuits)**: Entity behavior binding
- **Module 10 (Perception)**: Entity sensory responses
- **Module 11 (ASCII Studio)**: Base creation interface
- **Module 05 (ASCII Renderer)**: Layered rendering
- **Module 02 (Character Simulation)**: NPC personality integration
