# Module 10: Perception Systems

## Overview

Perception systems govern how information travels through the world—sound propagation, line of sight, and threat proximity. These systems enable emergent gameplay through realistic sensory mechanics.

---

## Sound Propagation System

### Sound Properties

```python
class Sound:
    source: Position              # Origin point
    volume: float                 # Loudness at source (0-100)
    frequency: SoundFrequency     # low, medium, high
    type: SoundType               # footstep, voice, impact, ambient
    direction: Direction | None   # Focused vs omnidirectional
    duration: Duration            # brief, sustained, continuous
```

### Propagation Rules

Sound travels tile-to-tile with attenuation:

```python
def propagate_sound(sound, grid):
    """Propagate sound through the tile grid."""

    # Initialize with source tile at full volume
    sound_map = {sound.source: sound.volume}
    to_process = [sound.source]

    while to_process:
        current = to_process.pop(0)
        current_volume = sound_map[current]

        if current_volume < HEARING_THRESHOLD:
            continue

        for neighbor in grid.get_adjacent(current):
            # Calculate attenuation
            attenuation = calculate_attenuation(
                current, neighbor, sound.frequency
            )

            new_volume = current_volume * attenuation

            # Only update if louder than existing
            if new_volume > sound_map.get(neighbor, 0):
                sound_map[neighbor] = new_volume
                to_process.append(neighbor)

    return sound_map
```

### Attenuation Factors

| Factor | Effect | Examples |
|--------|--------|----------|
| **Distance** | -3dB per tile | Natural falloff |
| **Obstacles** | -10 to -30dB | Walls block, curtains muffle |
| **Medium** | Varies | Water transmits further, air normal |
| **Frequency** | High blocked more | Bass penetrates, treble stops |

### Special Sound Behaviors

```python
# Echoes in large open spaces
def calculate_echo(sound, tile):
    if tile.has_feature("canyon") or tile.height > 5:
        return Echo(
            delay=tile.height * 0.1,
            volume=sound.volume * 0.3,
            count=2
        )
    return None

# Sound masking (waterfall covers conversation)
def apply_masking(sound_map, ambient_sources):
    for source in ambient_sources:
        if source.type == "waterfall":
            for tile in source.affected_tiles:
                if tile in sound_map:
                    sound_map[tile] *= 0.3  # 70% reduction
```

### Sound Detection

NPCs and creatures react to sounds:

```python
def check_sound_detection(entity, sound_map):
    """Check if entity detects a sound."""

    tile = entity.position
    sound_level = sound_map.get(tile, 0)

    # Hearing threshold based on entity
    threshold = entity.hearing_threshold

    # Environmental modifiers
    if entity.is_sleeping:
        threshold *= 2  # Harder to wake

    if entity.is_alert:
        threshold *= 0.5  # More sensitive

    if sound_level > threshold:
        return SoundDetection(
            volume=sound_level,
            direction=estimate_direction(entity, sound_map),
            confidence=calculate_confidence(sound_level, threshold)
        )

    return None
```

---

## Line of Sight System

### Vision Properties

```python
class Vision:
    range: float                  # Maximum sight distance
    field_of_view: float          # Angle in degrees (180 = hemisphere)
    dark_vision: float            # Ability to see in darkness
    facing: Direction             # Current look direction
```

### Visibility Calculation

```python
def calculate_visibility(observer, target, grid):
    """Calculate visibility between two entities."""

    # Check distance
    distance = calculate_distance(observer.position, target.position)
    if distance > observer.vision.range:
        return Visibility(visible=False, reason="out_of_range")

    # Check field of view
    angle = calculate_angle(observer.facing, target.position)
    if angle > observer.vision.field_of_view / 2:
        return Visibility(visible=False, reason="out_of_fov")

    # Ray cast for obstacles
    path = grid.get_line_of_sight(observer.position, target.position)
    for tile in path[1:-1]:  # Exclude start and end
        if tile.opaque:
            return Visibility(visible=False, reason="blocked", blocker=tile)

    # Calculate visibility quality
    quality = calculate_visibility_quality(
        distance, grid.get_tile(target.position), observer
    )

    return Visibility(visible=True, quality=quality)
```

### Visibility Modifiers

| Modifier | Effect | Source |
|----------|--------|--------|
| **Light Level** | Low light = -50% range | Tile environment |
| **Weather** | Fog/rain = -30% range | Weather system |
| **Movement** | Moving targets +25% visible | Entity state |
| **Camouflage** | Hiding = -50% visible | Entity action |
| **Size** | Large = +25%, small = -25% | Entity properties |

### Detection States

```python
class DetectionState(Enum):
    UNAWARE = 0       # Doesn't know target exists
    SUSPICIOUS = 1    # Thinks something might be there
    ALERTED = 2       # Knows something is there
    IDENTIFIED = 3    # Knows exactly what/who it is
    TRACKING = 4      # Actively following target
```

---

## Threat Proximity System

### Threat Assessment

```python
class Threat:
    source: Entity
    type: ThreatType              # physical, environmental, social
    radius: float                 # Danger zone size
    intensity: float              # How dangerous (0-1)
    direction: Direction | None   # Which way it's heading
    speed: float                  # How fast it's approaching
```

### Dynamic Threat Radius

Threat radius changes based on entity state:

```python
def calculate_threat_radius(entity):
    """Calculate current threat radius for an entity."""

    base_radius = THREAT_RADIUS[entity.type]

    # Weapon/capability multiplier
    if entity.equipped_weapon:
        base_radius *= entity.equipped_weapon.range_multiplier

    # State modifiers
    if entity.is_hostile:
        base_radius *= 1.5

    if entity.is_injured:
        base_radius *= 0.7  # Less threatening when hurt

    if entity.is_fleeing:
        base_radius *= 0.3

    return base_radius
```

### Reaction Timing

STT enables fast reactions to threats:

```python
def evaluate_reaction_time(player, threat):
    """Determine if player can react before threat reaches them."""

    distance = calculate_distance(player.position, threat.source.position)
    closing_speed = threat.speed

    if closing_speed <= 0:
        return ReactionWindow(infinite=True)

    time_to_contact = distance / closing_speed

    # STT input is faster than typing
    input_method = player.current_input_method
    if input_method == "stt":
        reaction_time = 0.5  # 500ms
    else:
        reaction_time = 2.0  # 2 seconds for typing

    can_react = time_to_contact > reaction_time

    return ReactionWindow(
        can_react=can_react,
        time_available=time_to_contact,
        suggested_actions=get_valid_reactions(player, threat, time_to_contact)
    )
```

### Threat Response

NPCs and creatures respond to threats based on personality:

```python
def evaluate_threat_response(entity, threat):
    """Determine entity's response to a threat."""

    # Factor in personality
    aggression = entity.personality.aggression
    fear = entity.personality.fear
    loyalty = entity.personality.loyalty

    # Factor in experience
    past_encounters = entity.memory.get_encounters(threat.source)
    won = sum(1 for e in past_encounters if e.outcome == "won")
    lost = sum(1 for e in past_encounters if e.outcome == "lost")

    # Calculate response weights
    fight_weight = aggression + (won * 0.1) - (lost * 0.2)
    flee_weight = fear + (lost * 0.2) - (won * 0.1)
    hide_weight = 1.0 - aggression - fear

    # Select response
    responses = {
        "fight": fight_weight,
        "flee": flee_weight,
        "hide": hide_weight,
        "submit": fear * 0.5 if threat.intensity > 0.8 else 0
    }

    return max(responses, key=responses.get)
```

---

## Combined Perception

### Multi-Sense Detection

Entities can detect through multiple senses:

```python
def detect_entity(observer, target, grid, sound_map):
    """Attempt to detect an entity through all senses."""

    detections = []

    # Visual detection
    visibility = calculate_visibility(observer, target, grid)
    if visibility.visible:
        detections.append(Detection(
            sense="sight",
            confidence=visibility.quality,
            position=target.position
        ))

    # Audio detection
    if target.is_making_sound:
        sound_detection = check_sound_detection(observer, sound_map)
        if sound_detection:
            detections.append(Detection(
                sense="sound",
                confidence=sound_detection.confidence,
                direction=sound_detection.direction
            ))

    # Combine detections
    if detections:
        return combine_detections(detections)

    return None

def combine_detections(detections):
    """Combine multiple sense detections."""

    best = max(detections, key=lambda d: d.confidence)

    # Multiple senses increase confidence
    combined_confidence = best.confidence
    for d in detections:
        if d != best:
            combined_confidence += d.confidence * 0.3

    return Detection(
        senses=[d.sense for d in detections],
        confidence=min(1.0, combined_confidence),
        position=best.position,
        direction=best.direction if hasattr(best, 'direction') else None
    )
```

---

## Integration Points

- **Behavioral Circuits** (Module 08): Entities emit and receive signals
- **Tile Grid** (Module 09): Tiles affect propagation
- **Character Simulation** (Module 02): NPCs use perception for behavior
- **Memory Bank** (Module 03): Detections become memories
- **Interaction Engine** (Module 06): Player actions trigger sounds
