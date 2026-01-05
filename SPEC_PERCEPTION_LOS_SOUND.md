# ShadowEngine — Sound & Line-of-Sight Propagation System

> **Version**: 1.0.0
> **Status**: Core Perception Layer
> **Purpose**: World communicates through perception, not messages
> **Major Feature**: First-Person View (FPV) ASCII rendering

---

## Core Principle

**The world communicates itself to player and NPCs through perception, not direct messages.**

- Player sees ASCII tiles → partial info (fog, flicker, hidden threats)
- Player hears → positional cues, distance, urgency
- NPCs detect player → triggers adaptive behaviors
- Threat proximity & reaction timing system consumes this info

---

## 1. First-Person View (FPV) Rendering

**This is not a top-down roguelike.** This is forward-facing, like Doom but in ASCII.

### FPV vs Top-Down

```
TOP-DOWN (traditional roguelike):
┌────────────────────────────┐
│  . . . . . . . . . . . .   │
│  . . . # # # . . . . . .   │
│  . . . # . # . . @ . . .   │  ← Player sees everything around
│  . . . # . # . . . . . .   │
│  . . . . . . . . . . . .   │
└────────────────────────────┘

FPV (ShadowEngine):
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│          ▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▒▒▒▒▒▒▒▒▒         │
│        ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓▓▓▓▓▓▓▓▓         │
│      ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░████████████       │
│     ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██████████████      │
│    ████████████████                                  ████████████████     │
│   ██████████████████         ALLEY                  ██████████████████    │
│  ████████████████████                              ████████████████████   │
│ ██████████████████████      ☻ ←threat             ██████████████████████  │
│████████████████████████                          ████████████████████████ │
│████████████████████████████████████████████████████████████████████████████│
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
└────────────────────────────────────────────────────────────────────────────┘
    ← Left                       Forward                          Right →
```

### FPV Projection

```python
class FPVRenderer:
    """First-person perspective ASCII renderer."""

    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 24
    FOV_DEGREES = 90          # Field of view
    MAX_DRAW_DISTANCE = 30    # Tiles

    def __init__(self):
        self.player_pos = (0, 0)
        self.player_angle = 0.0  # Radians, 0 = North

    def render_frame(self, world: WorldGrid, player: Player) -> str:
        """Render the world from player's perspective."""

        frame = [[' ' for _ in range(self.SCREEN_WIDTH)]
                 for _ in range(self.SCREEN_HEIGHT)]

        # Cast rays for each column of the screen
        for screen_x in range(self.SCREEN_WIDTH):
            # Calculate ray angle for this column
            ray_angle = self._get_ray_angle(screen_x)

            # Cast ray and find wall
            hit = self._cast_ray(
                player.position,
                ray_angle,
                world,
            )

            # Calculate wall height based on distance
            if hit:
                wall_height = self._calculate_wall_height(hit.distance)
                wall_char = self._get_wall_char(hit.tile, hit.distance)
                wall_color = self._get_distance_color(hit.distance)

                # Draw vertical wall strip
                self._draw_wall_strip(
                    frame,
                    screen_x,
                    wall_height,
                    wall_char,
                    wall_color,
                )

            # Draw entities visible in this column
            self._draw_entities_in_column(
                frame,
                screen_x,
                ray_angle,
                hit.distance if hit else self.MAX_DRAW_DISTANCE,
                world,
            )

        return self._frame_to_string(frame)

    def _cast_ray(
        self,
        origin: tuple[float, float],
        angle: float,
        world: WorldGrid,
    ) -> Optional[RayHit]:
        """Cast a ray and find first opaque tile."""

        step_size = 0.1
        distance = 0.0

        while distance < self.MAX_DRAW_DISTANCE:
            x = origin[0] + math.cos(angle) * distance
            y = origin[1] + math.sin(angle) * distance

            tile = world.get_tile(int(x), int(y))

            if tile.opacity >= 0.9:
                return RayHit(
                    tile=tile,
                    distance=distance,
                    position=(x, y),
                    side=self._get_hit_side(x, y),
                )

            distance += step_size

        return None

    def _calculate_wall_height(self, distance: float) -> int:
        """Taller walls when closer."""
        if distance < 0.5:
            distance = 0.5
        return int((self.SCREEN_HEIGHT * 1.5) / distance)

    def _get_wall_char(self, tile: Tile, distance: float) -> str:
        """Wall character based on distance (depth shading)."""

        if distance < 3:
            return "█"      # Solid, very close
        elif distance < 6:
            return "▓"      # Dense
        elif distance < 10:
            return "▒"      # Medium
        elif distance < 15:
            return "░"      # Light
        else:
            return "·"      # Distant
```

### FPV Direction & Movement

```python
@dataclass
class PlayerOrientation:
    """Player's facing direction in FPV."""

    position: tuple[float, float]
    angle: float                    # Radians (0 = North)

    def turn_left(self, amount: float = 0.1) -> None:
        self.angle -= amount

    def turn_right(self, amount: float = 0.1) -> None:
        self.angle += amount

    def move_forward(self, distance: float, world: WorldGrid) -> bool:
        """Move forward if not blocked."""
        new_x = self.position[0] + math.cos(self.angle) * distance
        new_y = self.position[1] + math.sin(self.angle) * distance

        if world.is_walkable(int(new_x), int(new_y)):
            self.position = (new_x, new_y)
            return True
        return False

    def strafe_left(self, distance: float, world: WorldGrid) -> bool:
        """Strafe left."""
        strafe_angle = self.angle - math.pi / 2
        new_x = self.position[0] + math.cos(strafe_angle) * distance
        new_y = self.position[1] + math.sin(strafe_angle) * distance

        if world.is_walkable(int(new_x), int(new_y)):
            self.position = (new_x, new_y)
            return True
        return False
```

### FPV Entity Rendering

```python
class FPVEntityRenderer:
    """Render entities (NPCs, items) in FPV."""

    def draw_entities_in_column(
        self,
        frame: list[list[str]],
        screen_x: int,
        ray_angle: float,
        wall_distance: float,
        world: WorldGrid,
        player: Player,
    ) -> None:
        """Draw visible entities in this screen column."""

        for entity in world.get_visible_entities(player):
            # Calculate entity's angle from player
            entity_angle = self._angle_to_entity(player, entity)

            # Is entity in this column's ray?
            if self._angle_in_column(entity_angle, ray_angle, screen_x):
                entity_distance = self._distance_to(player, entity)

                # Only draw if closer than wall
                if entity_distance < wall_distance:
                    entity_height = self._calculate_entity_height(entity_distance)
                    entity_char = self._get_entity_char(entity, entity_distance)

                    self._draw_entity_sprite(
                        frame,
                        screen_x,
                        entity_height,
                        entity_char,
                        entity.threat_level,
                    )

    def _get_entity_char(self, entity: Entity, distance: float) -> str:
        """Entity character changes with distance."""

        if entity.is_threat:
            if distance < 5:
                return "☻"      # Clear threat
            elif distance < 10:
                return "○"      # Visible figure
            else:
                return "·"      # Distant shape
        else:
            if distance < 5:
                return "☺"
            else:
                return "○"
```

---

## 2. World as Perception Graph

Every tile has perception properties.

### Tile Perception Schema

```python
@dataclass
class TilePerception:
    """Perception properties of a tile."""

    tile_type: str

    # Vision
    opacity: float              # 0.0 = transparent, 1.0 = solid
    emits_light: float          # 0.0-1.0 (lamp, fire)
    reflects_light: float       # How much ambient light bounces

    # Sound
    sound_absorption: float     # Fraction of sound dampened
    sound_emission: float       # Continuous sound (waterfall, machinery)
    sound_reflection: float     # Echo factor

    # Physical
    elevation: int              # Height level
    liquid_depth: float         # Affects sound + movement

    # LOS modifiers
    los_modifier: str           # "blocks", "partial", "none"
```

### Tile Type Defaults

```python
TILE_PERCEPTION_DEFAULTS = {
    "stone_wall": TilePerception(
        tile_type="stone_wall",
        opacity=1.0,
        emits_light=0.0,
        sound_absorption=0.8,
        sound_emission=0.0,
        elevation=0,
        liquid_depth=0,
        los_modifier="blocks",
    ),
    "waterfall": TilePerception(
        tile_type="waterfall",
        opacity=0.6,            # Partial visibility
        emits_light=0.0,
        sound_absorption=0.3,   # Absorbs some, but loud itself
        sound_emission=0.7,     # Continuous noise
        elevation=0,
        liquid_depth=0.5,
        los_modifier="partial",
    ),
    "tree": TilePerception(
        tile_type="tree",
        opacity=0.3,
        emits_light=0.0,
        sound_absorption=0.5,
        sound_emission=0.1,     # Rustling
        elevation=0,
        liquid_depth=0,
        los_modifier="partial",
    ),
    "open_field": TilePerception(
        tile_type="open_field",
        opacity=0.0,
        emits_light=0.0,
        sound_absorption=0.0,
        sound_emission=0.0,
        elevation=0,
        liquid_depth=0,
        los_modifier="none",
    ),
    "grass": TilePerception(
        tile_type="grass",
        opacity=0.0,
        emits_light=0.0,
        sound_absorption=0.2,   # Muffles footsteps slightly
        sound_emission=0.0,
        elevation=0,
        liquid_depth=0,
        los_modifier="none",
    ),
    "shallow_water": TilePerception(
        tile_type="shallow_water",
        opacity=0.0,
        emits_light=0.0,
        sound_absorption=0.0,
        sound_emission=0.2,     # Splashing
        elevation=-1,
        liquid_depth=0.3,
        los_modifier="none",
    ),
    "smoke": TilePerception(
        tile_type="smoke",
        opacity=0.7,
        emits_light=0.1,        # Glowing edges
        sound_absorption=0.1,
        sound_emission=0.0,
        elevation=0,
        liquid_depth=0,
        los_modifier="partial",
    ),
    "fire": TilePerception(
        tile_type="fire",
        opacity=0.4,
        emits_light=0.9,        # Bright
        sound_absorption=0.0,
        sound_emission=0.4,     # Crackling
        elevation=0,
        liquid_depth=0,
        los_modifier="partial",
    ),
}
```

### Tile Perception Table

| Tile Type | Opacity | Sound Absorption | LOS Modifier |
|-----------|---------|------------------|--------------|
| Stone Wall | 1.0 | 0.8 | blocks |
| Waterfall | 0.6 | 0.3 | partial |
| Tree | 0.3 | 0.5 | partial |
| Open Field | 0.0 | 0.0 | none |
| Grass | 0.0 | 0.2 | none |
| Smoke | 0.7 | 0.1 | partial |
| Fire | 0.4 | 0.0 | partial |

---

## 3. Line-of-Sight (LOS) System

### Raycast LOS

```python
class LineOfSightSystem:
    """Calculate what can be seen from a position."""

    def calculate_los(
        self,
        origin: tuple[float, float],
        direction: float,           # Facing angle
        fov: float,                 # Field of view in degrees
        max_distance: float,
        world: WorldGrid,
    ) -> LOSResult:
        """Calculate all visible tiles from origin."""

        visible_tiles = []
        partial_tiles = []

        # Cast rays across FOV
        num_rays = int(fov * 2)  # Ray density
        start_angle = direction - math.radians(fov / 2)
        angle_step = math.radians(fov) / num_rays

        for i in range(num_rays):
            ray_angle = start_angle + i * angle_step
            ray_result = self._cast_visibility_ray(
                origin, ray_angle, max_distance, world
            )

            for tile_pos, visibility in ray_result:
                if visibility >= 0.9:
                    visible_tiles.append(tile_pos)
                elif visibility > 0.1:
                    partial_tiles.append((tile_pos, visibility))

        return LOSResult(
            origin=origin,
            direction=direction,
            visible_tiles=set(visible_tiles),
            partial_tiles=partial_tiles,
        )

    def _cast_visibility_ray(
        self,
        origin: tuple[float, float],
        angle: float,
        max_distance: float,
        world: WorldGrid,
    ) -> list[tuple[tuple[int, int], float]]:
        """Cast ray and return tiles with visibility levels."""

        results = []
        accumulated_opacity = 0.0
        step_size = 0.5

        for dist in range(int(max_distance / step_size)):
            distance = dist * step_size
            x = origin[0] + math.cos(angle) * distance
            y = origin[1] + math.sin(angle) * distance
            tile_pos = (int(x), int(y))

            tile = world.get_tile(*tile_pos)

            # Calculate visibility after passing through previous tiles
            visibility = 1.0 - accumulated_opacity

            # Distance falloff
            distance_factor = 1.0 - (distance / max_distance) ** 2
            visibility *= distance_factor

            if visibility > 0.1:
                results.append((tile_pos, visibility))

            # Accumulate opacity
            accumulated_opacity += tile.perception.opacity * step_size
            accumulated_opacity = min(1.0, accumulated_opacity)

            # Stop if fully blocked
            if accumulated_opacity >= 0.99:
                break

        return results

    def can_see(
        self,
        observer: Entity,
        target: Entity,
        world: WorldGrid,
    ) -> tuple[bool, float]:
        """Can observer see target? Returns (can_see, clarity)."""

        # Distance check
        distance = self._distance(observer.position, target.position)
        if distance > observer.vision_range:
            return (False, 0.0)

        # FOV check
        angle_to_target = self._angle_to(observer.position, target.position)
        angle_diff = abs(angle_to_target - observer.facing_angle)
        if angle_diff > observer.fov / 2:
            return (False, 0.0)

        # Raycast for obstacles
        ray = self._cast_visibility_ray(
            observer.position,
            angle_to_target,
            distance + 1,
            world,
        )

        # Find visibility at target position
        target_tile = (int(target.position[0]), int(target.position[1]))
        for tile_pos, visibility in ray:
            if tile_pos == target_tile:
                return (visibility > 0.3, visibility)

        return (False, 0.0)
```

### Dynamic Obstruction Effects

```python
class DynamicObstructions:
    """Environmental effects that modify LOS."""

    def apply_obstructions(
        self,
        base_visibility: float,
        tile: Tile,
        environment: Environment,
    ) -> float:
        """Modify visibility based on dynamic conditions."""

        visibility = base_visibility

        # Waterfall: LOS blocked + spray
        if tile.has_entity("waterfall"):
            visibility *= 0.4
            # Also affects sound (handled separately)

        # Smoke: Heavy reduction
        if tile.has_state("smoke"):
            visibility *= 0.3

        # Fire: Glare effect (can see fire, hard to see past)
        if tile.has_state("fire"):
            visibility *= 0.6

        # Darkness: Global reduction
        light_level = environment.get_light_at(tile.position)
        visibility *= light_level

        # Fog/weather
        if environment.weather == Weather.FOG:
            visibility *= 0.5
        elif environment.weather == Weather.HEAVY_RAIN:
            visibility *= 0.7

        return visibility
```

### Partial Visibility Rendering

```python
class PartialVisibilityRenderer:
    """Render partially visible tiles in FPV."""

    def render_partial_tile(
        self,
        tile: Tile,
        visibility: float,
        distance: float,
    ) -> tuple[str, str]:
        """Get character and effect for partial visibility."""

        # Base character
        base_char = self._get_base_char(tile, distance)

        # Apply visibility effects
        if visibility < 0.3:
            # Barely visible - flicker occasionally
            return (base_char, "flicker_rare")
        elif visibility < 0.5:
            # Dim and unstable
            return (base_char, "flicker_frequent")
        elif visibility < 0.7:
            # Visible but dim
            return (base_char, "dim")
        else:
            # Nearly clear
            return (base_char, "normal")

    def apply_flicker(self, char: str, effect: str, frame_count: int) -> str:
        """Apply flicker effect to character."""

        if effect == "flicker_rare":
            # Show 30% of frames
            if hash(frame_count) % 10 < 3:
                return char
            return " "

        elif effect == "flicker_frequent":
            # Show 50% of frames
            if frame_count % 2 == 0:
                return char
            return "░"

        elif effect == "dim":
            # Always show but dimmed
            DIM_MAP = {"█": "▓", "▓": "▒", "▒": "░", "░": "·"}
            return DIM_MAP.get(char, char)

        return char
```

---

## 4. Sound Propagation System

### Sound Map (BFS Wavefront)

```python
class SoundPropagationSystem:
    """Propagate sound through the world using BFS."""

    def propagate_sound(
        self,
        source: tuple[int, int],
        volume: float,
        world: WorldGrid,
    ) -> dict[tuple[int, int], float]:
        """Propagate sound from source, return volume at each tile."""

        sound_map = {}
        queue = deque([(source, volume)])
        visited = {source}

        while queue:
            position, current_volume = queue.popleft()

            # Store volume at this position
            sound_map[position] = current_volume

            # Stop propagating if too quiet
            if current_volume < 0.01:
                continue

            # Propagate to neighbors
            for neighbor in self._get_neighbors(position):
                if neighbor in visited:
                    continue
                visited.add(neighbor)

                # Calculate attenuation
                distance = 1.0  # One tile
                tile = world.get_tile(*neighbor)

                # Base attenuation (inverse square)
                attenuation = 1.0 / (distance ** 2)

                # Tile absorption
                absorption = tile.perception.sound_absorption
                attenuation *= (1.0 - absorption)

                # New volume at neighbor
                new_volume = current_volume * attenuation

                if new_volume > 0.01:
                    queue.append((neighbor, new_volume))

        return sound_map

    def create_sound_event(
        self,
        source: tuple[int, int],
        sound_type: str,
        volume: float,
        world: WorldGrid,
    ) -> SoundEvent:
        """Create a sound event and propagate it."""

        # Propagate sound
        sound_map = self.propagate_sound(source, volume, world)

        return SoundEvent(
            source=source,
            sound_type=sound_type,
            initial_volume=volume,
            sound_map=sound_map,
            timestamp=self.current_time,
        )
```

### Sound Types and Volumes

```python
SOUND_TYPES = {
    # Player actions
    "footstep_walk": 0.2,
    "footstep_run": 0.4,
    "footstep_sneak": 0.05,
    "speech_whisper": 0.1,
    "speech_normal": 0.3,
    "speech_shout": 0.7,
    "weapon_fire": 1.0,

    # Environmental
    "waterfall": 0.6,           # Continuous
    "machinery": 0.5,           # Continuous
    "door_open": 0.3,
    "door_slam": 0.6,
    "glass_break": 0.8,
    "collapse": 0.9,

    # NPC actions
    "npc_footstep": 0.3,
    "npc_speech": 0.4,
    "npc_weapon": 1.0,
}
```

### Directionality (Left/Right Perception)

```python
class DirectionalSound:
    """Player perceives sound direction."""

    def calculate_direction(
        self,
        player: Player,
        sound_source: tuple[int, int],
    ) -> SoundDirection:
        """Calculate which direction sound is coming from."""

        # Angle from player to sound
        angle_to_sound = math.atan2(
            sound_source[1] - player.position[1],
            sound_source[0] - player.position[0],
        )

        # Relative to player's facing direction
        relative_angle = angle_to_sound - player.facing_angle

        # Normalize to -π to π
        while relative_angle > math.pi:
            relative_angle -= 2 * math.pi
        while relative_angle < -math.pi:
            relative_angle += 2 * math.pi

        # Convert to left/right/front/back
        if abs(relative_angle) < math.pi / 4:
            direction = "front"
        elif abs(relative_angle) > 3 * math.pi / 4:
            direction = "back"
        elif relative_angle > 0:
            direction = "left"
        else:
            direction = "right"

        # Calculate stereo balance (-1.0 left to 1.0 right)
        stereo_balance = math.sin(relative_angle)

        return SoundDirection(
            direction=direction,
            angle=relative_angle,
            stereo_balance=stereo_balance,
        )

    def render_sound_indicator(
        self,
        direction: SoundDirection,
        volume: float,
        frame: list[list[str]],
    ) -> None:
        """Render directional sound indicator on screen."""

        # Position based on direction
        if direction.direction == "front":
            x = self.SCREEN_WIDTH // 2
            y = 2
        elif direction.direction == "back":
            x = self.SCREEN_WIDTH // 2
            y = self.SCREEN_HEIGHT - 2
        elif direction.direction == "left":
            x = 2
            y = self.SCREEN_HEIGHT // 2
        else:  # right
            x = self.SCREEN_WIDTH - 2
            y = self.SCREEN_HEIGHT // 2

        # Character based on volume
        if volume > 0.7:
            char = "!"         # Loud
            flash = True
        elif volume > 0.4:
            char = "*"         # Medium
            flash = False
        elif volume > 0.2:
            char = "·"         # Quiet
            flash = False
        else:
            return            # Too quiet to indicate

        # Draw indicator
        frame[y][x] = char
        if flash:
            frame[y][x-1] = "["
            frame[y][x+1] = "]"
```

### Continuous Sound Sources

```python
class ContinuousSoundSources:
    """Environmental sounds that persist."""

    def tick(self, world: WorldGrid, dt: float) -> list[SoundEvent]:
        """Generate continuous sound events."""

        events = []

        for entity in world.get_entities_with_sound():
            # Get base sound emission
            sound_level = entity.perception.sound_emission

            if sound_level > 0:
                # Create continuous sound event
                event = self.propagation.create_sound_event(
                    source=entity.position,
                    sound_type=entity.sound_type,
                    volume=sound_level,
                    world=world,
                )
                events.append(event)

        return events


# Waterfall example
waterfall = Entity(
    entity_type="waterfall",
    position=(45, 23),
    perception=TilePerception(
        sound_emission=0.7,     # Loud continuous
        sound_absorption=0.3,   # But also absorbs
    ),
)

# Effect: Waterfall creates "dead zone" behind it
# Sound from behind is masked
# Sound INTO waterfall area is absorbed
```

---

## 5. STT Sound Interaction

**Player speech creates sound events.**

```python
class STTSoundIntegration:
    """Player voice commands create in-world sounds."""

    def process_voice_command(
        self,
        transcript: str,
        volume: float,          # From microphone level
        player: Player,
        world: WorldGrid,
    ) -> tuple[Intent, SoundEvent]:
        """Process voice command and create corresponding sound."""

        # Parse intent
        intent = self.intent_parser.parse(transcript)

        # Determine in-world volume
        if intent.urgency > 0.8:
            # Shouting
            world_volume = volume * 1.5
            sound_type = "speech_shout"
        elif intent.urgency > 0.4:
            # Normal speech
            world_volume = volume
            sound_type = "speech_normal"
        else:
            # Whispered command (player spoke quietly)
            world_volume = volume * 0.3
            sound_type = "speech_whisper"

        # Create sound event
        sound_event = self.propagation.create_sound_event(
            source=player.position,
            sound_type=sound_type,
            volume=world_volume,
            world=world,
        )

        return (intent, sound_event)

    def evaluate_detection_risk(
        self,
        sound_event: SoundEvent,
        threats: list[Threat],
    ) -> list[ThreatAwarenessUpdate]:
        """Check which threats heard the player's voice."""

        updates = []

        for threat in threats:
            # Get sound volume at threat's position
            volume_at_threat = sound_event.sound_map.get(
                threat.position, 0.0
            )

            if volume_at_threat > 0.1:
                # Threat heard something
                updates.append(ThreatAwarenessUpdate(
                    threat_id=threat.id,
                    awareness_delta=volume_at_threat * 0.5,
                    heard_from=sound_event.source,
                    sound_type=sound_event.sound_type,
                ))

        return updates
```

---

## 6. NPC Awareness from Perception

### Awareness Score

```python
class NPCAwarenessSystem:
    """Calculate NPC awareness based on perception."""

    def calculate_awareness(
        self,
        npc: NPC,
        player: Player,
        world: WorldGrid,
        active_sounds: list[SoundEvent],
    ) -> float:
        """Calculate NPC's awareness of player."""

        base_awareness = npc.base_awareness

        # Visual component
        can_see, clarity = self.los.can_see(npc, player, world)
        if can_see:
            visual_awareness = clarity * 0.5
        else:
            visual_awareness = 0.0

        # Audio component
        audio_awareness = 0.0
        for sound in active_sounds:
            volume = sound.sound_map.get(npc.position, 0.0)
            if volume > 0.1:
                # NPC hears something
                audio_awareness = max(audio_awareness, volume * 0.4)

        # Memory component (from rumor system)
        if npc.has_memory_of(player):
            memory_awareness = 0.2
        else:
            memory_awareness = 0.0

        # Curiosity multiplier
        curiosity_mult = 1.0 + npc.bias.curious * 0.3

        # Calculate total
        total = base_awareness + visual_awareness + audio_awareness + memory_awareness
        total *= curiosity_mult

        return min(1.0, total)

    def update_awareness_state(
        self,
        npc: NPC,
        awareness: float,
    ) -> AwarenessState:
        """Convert awareness score to behavioral state."""

        if awareness < 0.1:
            return AwarenessState.UNAWARE
        elif awareness < 0.3:
            return AwarenessState.SUSPICIOUS
        elif awareness < 0.6:
            return AwarenessState.ALERT
        else:
            return AwarenessState.ENGAGED


class AwarenessState(Enum):
    UNAWARE = "unaware"         # Normal behavior
    SUSPICIOUS = "suspicious"   # Looking around
    ALERT = "alert"            # Actively searching
    ENGAGED = "engaged"        # Pursuing/attacking
```

### Awareness Thresholds

| Awareness | State | NPC Behavior |
|-----------|-------|--------------|
| 0.0 - 0.1 | Unaware | Normal patrol/idle |
| 0.1 - 0.3 | Suspicious | Pauses, looks around |
| 0.3 - 0.6 | Alert | Investigates sound/movement |
| 0.6 - 1.0 | Engaged | Approaches, challenges, attacks |

### Awareness Decay

```python
class AwarenessDecay:
    """Awareness decreases when stimulus disappears."""

    DECAY_RATES = {
        AwarenessState.ENGAGED: 0.05,     # Slow decay
        AwarenessState.ALERT: 0.1,
        AwarenessState.SUSPICIOUS: 0.15,
    }

    def decay_awareness(self, npc: NPC, dt: float) -> None:
        """Decay awareness if no current stimulus."""

        if not npc.has_current_stimulus:
            decay_rate = self.DECAY_RATES.get(npc.awareness_state, 0.1)
            npc.awareness -= decay_rate * dt
            npc.awareness = max(0.0, npc.awareness)
```

---

## 7. Player Perception Rendering

### Visual Perception in FPV

```python
class PlayerVisualPerception:
    """What the player sees in FPV."""

    def render_player_view(
        self,
        player: Player,
        world: WorldGrid,
        environment: Environment,
    ) -> Frame:
        """Render what player can perceive."""

        frame = Frame(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

        # Calculate visible tiles
        los = self.los_system.calculate_los(
            player.position,
            player.facing_angle,
            player.fov,
            player.vision_range,
            world,
        )

        # Apply environmental modifiers
        modified_los = self.obstructions.apply_obstructions(
            los,
            environment,
        )

        # Render FPV
        self.fpv_renderer.render(frame, modified_los, world)

        # Apply partial visibility effects
        for tile_pos, visibility in modified_los.partial_tiles:
            self.partial_renderer.apply_effect(frame, tile_pos, visibility)

        # Render entities
        self.entity_renderer.render_entities(frame, world, player)

        return frame
```

### Audio Perception Indicators

```python
class AudioPerceptionRenderer:
    """Render sound cues in ASCII."""

    def render_audio_cues(
        self,
        frame: Frame,
        player: Player,
        active_sounds: list[SoundEvent],
    ) -> None:
        """Add audio indicators to frame."""

        for sound in active_sounds:
            # Get volume at player position
            volume = sound.sound_map.get(player.position, 0.0)

            if volume < 0.1:
                continue  # Too quiet

            # Calculate direction
            direction = self.directional.calculate_direction(
                player, sound.source
            )

            # Render indicator
            self.directional.render_sound_indicator(
                direction, volume, frame
            )

    def get_audio_character(self, volume: float, sound_type: str) -> str:
        """Get character for audio cue."""

        if sound_type in ["weapon_fire", "collapse", "glass_break"]:
            # Violent sounds
            if volume > 0.5:
                return "!"
            return "*"

        elif sound_type in ["footstep_run", "npc_footstep"]:
            # Movement sounds
            if volume > 0.5:
                return "·"
            return "'"

        elif sound_type in ["speech_shout", "npc_speech"]:
            # Voice sounds
            if volume > 0.5:
                return "\""
            return "'"

        else:
            # Generic
            return "*"
```

### FPV Audio Visualization

```
SOUND INDICATORS IN FPV:

Footsteps to the left:
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  ·                                                                         │
│  ·                                                                         │
│  ·        ████████████████████████████████████████████████████████         │
│  ·       ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██          │
│ [*]     ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██         │
│  ·       ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██          │
│  ·        ████████████████████████████████████████████████████████         │
│  ·                                                                         │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
     [*] = sound indicator (left, medium volume)

Gunshot ahead:
┌────────────────────────────────────────────────────────────────────────────┐
│                                   [!]                                      │
│                                    │                                       │
│          ████████████████████████████████████████████████████████          │
│         ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██           │
│        ██░░░░░░░░░░░░░░░░░░☻░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██          │
│         ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██           │
│          ████████████████████████████████████████████████████████          │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
     [!] = loud sound indicator (front, high volume)
```

---

## 8. Threat Detection Logic

### Detection Flow

```python
class ThreatDetectionSystem:
    """NPCs detect and respond to player presence."""

    def tick_detection(
        self,
        npcs: list[NPC],
        player: Player,
        world: WorldGrid,
        active_sounds: list[SoundEvent],
    ) -> list[DetectionEvent]:
        """Update detection for all NPCs."""

        events = []

        for npc in npcs:
            # Calculate perception inputs
            los_result = self.los.calculate_los(
                npc.position,
                npc.facing_angle,
                npc.fov,
                npc.vision_range,
                world,
            )

            # Calculate awareness
            awareness = self.awareness.calculate_awareness(
                npc, player, world, active_sounds
            )

            # Update NPC state
            old_state = npc.awareness_state
            new_state = self.awareness.update_awareness_state(npc, awareness)

            if new_state != old_state:
                events.append(DetectionEvent(
                    npc=npc,
                    old_state=old_state,
                    new_state=new_state,
                    trigger=self._get_trigger(npc, los_result, active_sounds),
                ))

            npc.awareness_state = new_state
            npc.awareness = awareness

        return events

    def _get_trigger(
        self,
        npc: NPC,
        los: LOSResult,
        sounds: list[SoundEvent],
    ) -> str:
        """Determine what triggered detection."""

        # Check visual
        if npc.target_in_los(los):
            return "visual"

        # Check audio
        for sound in sounds:
            vol = sound.sound_map.get(npc.position, 0.0)
            if vol > 0.3:
                return f"audio:{sound.sound_type}"

        return "unknown"
```

### Detection-Triggered Behaviors

```python
class DetectionBehaviors:
    """NPC behaviors triggered by detection."""

    def respond_to_detection(
        self,
        npc: NPC,
        event: DetectionEvent,
        world: WorldGrid,
    ) -> NPCAction:
        """Determine NPC response to detection event."""

        if event.new_state == AwarenessState.SUSPICIOUS:
            # Look around, pause
            return NPCAction(
                action_type="search_area",
                duration=5.0,
                dialog="Hm?",
            )

        elif event.new_state == AwarenessState.ALERT:
            # Move toward sound/sighting
            if event.trigger.startswith("audio:"):
                return NPCAction(
                    action_type="investigate",
                    target=event.sound_source,
                    dialog="Who's there?",
                )
            else:
                return NPCAction(
                    action_type="investigate",
                    target=event.visual_position,
                    dialog="Hey!",
                )

        elif event.new_state == AwarenessState.ENGAGED:
            # Pursue/attack
            return NPCAction(
                action_type="engage",
                target=event.player_position,
                escalation_stage=1,  # Start challenge
            )

        return NPCAction(action_type="continue")
```

---

## 9. Integration with Threat Proximity

### Perception Informs Reaction Windows

```python
class PerceptionReactionIntegration:
    """LOS + sound affects reaction timing."""

    def modify_reaction_window(
        self,
        threat: Threat,
        player: Player,
        world: WorldGrid,
    ) -> float:
        """Modify threat's reaction window based on perception."""

        base_window = threat.reaction_window

        # Check if threat can see player clearly
        can_see, clarity = self.los.can_see(threat, player, world)

        if can_see:
            # Clear sight = faster reaction
            window_mod = 1.0 - (clarity * 0.3)  # Up to 30% faster
        else:
            # No sight = slower reaction
            window_mod = 1.2  # 20% slower

        # Sound clarity affects reaction
        sound_at_threat = self.get_player_sound_at(threat.position)
        if sound_at_threat > 0.5:
            # Loud player = faster threat reaction
            window_mod *= 0.9

        return base_window * window_mod

    def get_player_warning_level(
        self,
        player: Player,
        threats: list[Threat],
        world: WorldGrid,
    ) -> float:
        """How much warning does player have?"""

        warning = 0.0

        for threat in threats:
            # Can player see the threat?
            can_see, clarity = self.los.can_see(player, threat, world)
            if can_see:
                warning = max(warning, clarity)

            # Can player hear the threat?
            threat_sound = threat.sound_signature
            distance = self._distance(player.position, threat.position)
            heard_volume = threat_sound / (distance ** 2)
            warning = max(warning, heard_volume)

        return warning
```

### Example Integration

```
SCENARIO: Player behind waterfall, threat approaching

Perception state:
  - Player LOS: Blocked by waterfall (opacity 0.6)
  - Player hearing: Masked by waterfall (sound_emission 0.7)
  - Threat LOS: Blocked (same waterfall)
  - Threat hearing: Masked

Result:
  - Threat doesn't see player: reaction_window × 1.2 (slower)
  - Threat can't hear player shout: awareness stays low
  - Player can't hear footsteps: no audio warning
  - Player can't see threat: must guess from ripples in water

Both are partially blind.
First one to break cover loses advantage.
```

---

## 10. Emergent Behavior Examples

### Waterfall Chase

```
SETUP:
- Player runs behind waterfall
- Threat pursuing from street

PERCEPTION STATE:
- Waterfall: opacity 0.6, sound_absorption 0.3, sound_emission 0.7

PLAYER EFFECTS:
- Cannot hear footsteps (masked by waterfall)
- Cannot be heard (noise cover)
- Partially invisible (waterfall blocks 60% of light)

THREAT EFFECTS:
- Loses visual contact (partial opacity)
- Sound trail ends at waterfall
- Must guess player's path

RISKS:
- Slipping (wet rocks)
- Hidden hazards behind falls
- If player speaks loud, sound may carry around

GAMEPLAY:
- Player can hide and wait
- Or use cover to flank
- Or run through to other side
- All create different sound/LOS signatures
```

### Forest Ambush

```
SETUP:
- Player moves through dense foliage
- Multiple threats positioned for ambush

PERCEPTION STATE:
- Trees: opacity 0.3, sound_absorption 0.5

PLAYER EFFECTS:
- LOS blocked by trees (can only see 3-4 tiles ahead)
- Footsteps muffled (50% absorbed)
- Can hear threats if they move (same absorption)

THREAT EFFECTS:
- Each threat has limited LOS
- Must coordinate by sound
- Player moving triggers awareness

EMERGENT BEHAVIOR:
- Threats don't see player until close
- First threat to spot triggers alert
- Alert = sound event = other threats aware
- Player may hear alert, react with STT
```

### City Street Gunshot

```
SETUP:
- Gunshot occurs 15 tiles away
- Multiple NPCs in area

PERCEPTION STATE:
- Gunshot: volume 1.0
- Stone buildings: sound_absorption 0.8

SOUND PROPAGATION:
- Direct line: 15 tiles × attenuation = volume 0.5 at player
- Through building: blocked/heavily attenuated
- Around corner: partial attenuation

NPC REACTIONS:
- NPCs in direct line: awareness → ENGAGED
- NPCs behind buildings: awareness → ALERT
- Distant NPCs: awareness → SUSPICIOUS

PLAYER EXPERIENCE:
- Hears gunshot from direction (right)
- Audio indicator: [!] on right edge
- Doesn't know exact source
- Can investigate or flee
- STT: "What was that?" → intent = investigate
```

---

## 11. Implementation Order

### Phase 1: Core LOS + Sound

```
- Single player + single NPC
- Basic raycast LOS
- Simple sound propagation (BFS)
- FPV rendering (basic)
- Awareness scoring
```

### Phase 2: FPV Polish + Environmental

```
- Full FPV with depth shading
- Entity rendering in FPV
- Environmental modifiers (water, trees, smoke)
- Partial visibility effects
- Audio direction indicators
```

### Phase 3: Integration

```
- Rumor/memory affects awareness
- Multiple threats with sound coordination
- STT creates sound events
- Reaction timing uses perception
- Full emergent behaviors
```

---

## 12. Summary: What This Unlocks

| System | Enabled By Perception |
|--------|----------------------|
| **Stealth** | LOS + sound avoidance |
| **Pursuit** | Sound tracking, LOS breaks |
| **Ambush** | Reduced awareness zones |
| **Voice tactics** | Shouting creates sound, affects detection |
| **Environment use** | Waterfall, smoke, darkness as tools |
| **Threat warning** | Audio cues before visual contact |
| **Fear/panic** | Unknown sounds, partial visibility |

---

*End of Sound & Line-of-Sight Propagation System*
