# ShadowEngine: Sound, Fuzzy Input, and Systems Addendum

> **Version**: 2.1.0
> **Status**: Gap-fill for Living World Addendum
> **Purpose**: Add missing systems identified in review

---

## 1. Sound Propagation System

Sound is a first-class simulation element. Noise travels through tiles, alerts NPCs, and creates emergent gameplay.

### 1.1 Sound Model

```python
@dataclass
class Sound:
    """A sound event in the world."""

    id: str
    origin: tuple[int, int]
    timestamp: float

    # Properties
    volume: float               # 0.0 to 1.0 (1.0 = gunshot)
    frequency: str              # "low", "mid", "high" (affects transmission)
    sound_type: SoundType

    # Propagation state
    current_radius: float       # How far it's traveled
    max_radius: float           # Based on initial volume
    decay_rate: float           # Volume loss per tile

    # Source
    source_entity: Optional[str]
    source_action: str          # "gunshot", "footstep", "splash", "speech"


class SoundType(Enum):
    IMPACT = "impact"           # Gunshots, punches, crashes
    FOOTSTEP = "footstep"       # Movement sounds
    VOICE = "voice"             # Speech, shouts
    AMBIENT = "ambient"         # Rain, machinery, traffic
    WATER = "water"             # Splashes, flowing
    MECHANICAL = "mechanical"   # Doors, engines


# Volume reference levels
VOLUME_LEVELS = {
    "gunshot": 1.0,
    "shout": 0.8,
    "crash": 0.7,
    "speech": 0.4,
    "footstep_run": 0.3,
    "footstep_walk": 0.15,
    "footstep_sneak": 0.05,
    "splash_large": 0.6,
    "splash_small": 0.2,
    "door_slam": 0.5,
    "door_quiet": 0.1,
    "whisper": 0.1,
}
```

### 1.2 Sound Propagation

```python
class SoundPropagationEngine:
    """Simulates how sound travels through the world."""

    active_sounds: list[Sound]

    # Material transmission coefficients (how much sound passes through)
    TRANSMISSION = {
        Material.AIR: 1.0,          # Full transmission
        Material.WATER: 0.3,        # Muffled
        Material.GLASS: 0.7,        # Mostly passes
        Material.WOOD: 0.4,         # Partial block
        Material.STONE: 0.1,        # Heavy block
        Material.METAL: 0.2,        # Reflects most
        Material.FABRIC: 0.6,       # Some absorption
    }

    # Special cases
    WATERFALL_MASK_RADIUS = 5       # Waterfall drowns sounds within 5 tiles
    RAIN_VOLUME_PENALTY = 0.3       # Rain reduces all sound detection

    def propagate(self, sound: Sound, world: WorldGrid, dt: float) -> list[SoundEvent]:
        """Expand sound wave and check for listeners."""

        events = []

        # Expand radius
        old_radius = sound.current_radius
        sound.current_radius += self._get_propagation_speed(world) * dt

        if sound.current_radius > sound.max_radius:
            self.active_sounds.remove(sound)
            return events

        # Find newly reached tiles
        new_tiles = self._get_ring_tiles(
            sound.origin,
            old_radius,
            sound.current_radius
        )

        for tile_pos in new_tiles:
            tile = world.get_tile(*tile_pos)

            # Calculate volume at this position
            distance = self._distance(sound.origin, tile_pos)
            volume = self._calculate_volume_at(sound, tile_pos, world)

            # Check for listeners (NPCs, player)
            for entity in tile.entities:
                if self._can_hear(entity, volume, sound.frequency):
                    events.append(SoundEvent(
                        listener=entity,
                        sound=sound,
                        perceived_volume=volume,
                        perceived_direction=self._get_direction(tile_pos, sound.origin),
                    ))

        return events

    def _calculate_volume_at(
        self,
        sound: Sound,
        position: tuple[int, int],
        world: WorldGrid
    ) -> float:
        """Calculate perceived volume considering obstacles."""

        # Base decay from distance
        distance = self._distance(sound.origin, position)
        volume = sound.volume * (1.0 - (distance / sound.max_radius) * sound.decay_rate)

        # Trace path for obstacles
        path = self._trace_path(sound.origin, position)

        for tile_pos in path:
            tile = world.get_tile(*tile_pos)

            # Material transmission
            volume *= self.TRANSMISSION.get(tile.material, 0.5)

            # Special sound masks
            if self._has_waterfall_nearby(tile_pos, world):
                volume *= 0.1  # Waterfall drowns most sounds

            if volume < 0.01:
                return 0.0  # Inaudible

        # Weather effects
        if world.environment.weather == Weather.RAIN:
            volume *= (1.0 - self.RAIN_VOLUME_PENALTY)
        elif world.environment.weather == Weather.HEAVY_RAIN:
            volume *= (1.0 - self.RAIN_VOLUME_PENALTY * 2)

        return max(0.0, min(1.0, volume))

    def emit_sound(
        self,
        origin: tuple[int, int],
        sound_type: str,
        source_entity: Optional[str] = None,
        volume_modifier: float = 1.0,
    ) -> Sound:
        """Create a new sound at a location."""

        base_volume = VOLUME_LEVELS.get(sound_type, 0.3)

        sound = Sound(
            id=self._generate_id(),
            origin=origin,
            timestamp=self.current_time,
            volume=base_volume * volume_modifier,
            frequency=self._get_frequency(sound_type),
            sound_type=self._classify_type(sound_type),
            current_radius=0.0,
            max_radius=base_volume * 20,  # Louder = travels further
            decay_rate=0.7,
            source_entity=source_entity,
            source_action=sound_type,
        )

        self.active_sounds.append(sound)
        return sound
```

### 1.3 NPC Sound Response

```python
class NPCSoundResponse:
    """How NPCs react to sounds they hear."""

    def process_sound_event(
        self,
        npc: Character,
        event: SoundEvent,
    ) -> Optional[NPCBehaviorChange]:
        """Determine NPC reaction to hearing a sound."""

        # Threshold based on NPC alertness
        hearing_threshold = self._get_hearing_threshold(npc)

        if event.perceived_volume < hearing_threshold:
            return None  # Didn't notice

        # Classify threat level
        threat = self._assess_threat(event.sound, npc)

        if threat > 0.7:
            # High threat - investigate or flee
            if npc.personality.brave > 0.5:
                return NPCBehaviorChange(
                    behavior="investigate",
                    target_location=event.sound.origin,
                    urgency=threat,
                    dialogue_available="heard_threat",
                )
            else:
                return NPCBehaviorChange(
                    behavior="flee",
                    flee_from=event.sound.origin,
                    urgency=threat,
                )

        elif threat > 0.3:
            # Medium threat - become alert
            return NPCBehaviorChange(
                behavior="alert",
                look_direction=event.perceived_direction,
                duration=10.0,  # Stay alert for 10 seconds
            )

        else:
            # Low threat - note but ignore
            npc.memory.add_observation(f"heard_{event.sound.source_action}")
            return None

    def _assess_threat(self, sound: Sound, npc: Character) -> float:
        """How threatening is this sound to this NPC?"""

        THREAT_BY_TYPE = {
            "gunshot": 0.95,
            "shout": 0.6,
            "crash": 0.5,
            "footstep_run": 0.4,
            "splash_large": 0.3,
            "speech": 0.2,
            "footstep_walk": 0.15,
        }

        base_threat = THREAT_BY_TYPE.get(sound.source_action, 0.2)

        # Modify by NPC state
        if npc.is_on_guard:
            base_threat *= 1.5
        if npc.is_searching_for_player:
            base_threat *= 2.0
        if npc.is_relaxed:
            base_threat *= 0.5

        return min(1.0, base_threat)
```

### 1.4 Waterfall Sound Masking

```python
class WaterfallSoundMask:
    """Waterfalls and loud ambient sounds mask other sounds."""

    def get_mask_zones(self, world: WorldGrid) -> list[MaskZone]:
        """Find all sound-masking zones in the world."""

        zones = []

        # Find waterfalls
        for entity in world.get_entities_of_type("waterfall"):
            zones.append(MaskZone(
                center=entity.location,
                radius=5,
                mask_strength=0.9,  # Blocks 90% of sounds
                source="waterfall",
            ))

        # Find other loud sources
        for entity in world.get_entities_of_type("machinery"):
            zones.append(MaskZone(
                center=entity.location,
                radius=3,
                mask_strength=0.6,
                source="machinery",
            ))

        # Rain creates global mask
        if world.environment.weather in [Weather.HEAVY_RAIN, Weather.STORM]:
            zones.append(MaskZone(
                center=None,  # Global
                radius=float('inf'),
                mask_strength=0.4,
                source="weather",
            ))

        return zones

    def apply_mask(
        self,
        sound_volume: float,
        listener_pos: tuple[int, int],
        mask_zones: list[MaskZone],
    ) -> float:
        """Reduce sound volume based on masking zones."""

        for zone in mask_zones:
            if zone.center is None:
                # Global mask
                sound_volume *= (1.0 - zone.mask_strength)
            else:
                distance = self._distance(listener_pos, zone.center)
                if distance < zone.radius:
                    # Inside mask zone
                    proximity = 1.0 - (distance / zone.radius)
                    reduction = zone.mask_strength * proximity
                    sound_volume *= (1.0 - reduction)

        return sound_volume
```

**Gameplay Example:**
```
Player splashes through waterfall (volume: 0.6)
    → Sound propagates outward
    → Goon 8 tiles away would hear at 0.3 volume
    → BUT waterfall masks to 0.03 (inaudible)
    → Player passes undetected

Player fires gun behind waterfall (volume: 1.0)
    → Masked to 0.1 by waterfall
    → Goon 8 tiles away hears at 0.05
    → Below threshold - no alert

Player fires gun 10 tiles from waterfall (volume: 1.0)
    → No mask
    → Goon hears at 0.7
    → HIGH ALERT - investigates
```

---

## 2. Fuzzy STT Matching

Handle voice recognition errors gracefully. Never fail on mishears.

### 2.1 Phonetic Similarity Engine

```python
class FuzzyVoiceMatcher:
    """Match misheard voice commands to intended actions."""

    def __init__(self):
        # Build phonetic index of all valid commands
        self.command_phonetics = self._build_phonetic_index()
        self.soundex = Soundex()
        self.metaphone = Metaphone()

    def match(self, transcript: str) -> FuzzyMatch:
        """Find best matching command for a transcript."""

        transcript_clean = transcript.lower().strip()

        # Try exact match first
        if transcript_clean in self.valid_commands:
            return FuzzyMatch(
                original=transcript,
                matched=transcript_clean,
                confidence=1.0,
                method="exact",
            )

        # Try phonetic matching
        candidates = []

        for word in transcript_clean.split():
            # Soundex matching (consonant-based)
            soundex_code = self.soundex.encode(word)
            soundex_matches = self._find_by_soundex(soundex_code)
            candidates.extend(soundex_matches)

            # Metaphone matching (pronunciation-based)
            metaphone_code = self.metaphone.encode(word)
            metaphone_matches = self._find_by_metaphone(metaphone_code)
            candidates.extend(metaphone_matches)

        # Score candidates
        scored = []
        for candidate in set(candidates):
            score = self._calculate_similarity(transcript_clean, candidate)
            scored.append((candidate, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        if scored and scored[0][1] > 0.6:
            return FuzzyMatch(
                original=transcript,
                matched=scored[0][0],
                confidence=scored[0][1],
                method="phonetic",
                alternatives=[s[0] for s in scored[1:4]],
            )

        # Try semantic matching via LLM
        return self._llm_fallback(transcript)

    def _calculate_similarity(self, input_word: str, candidate: str) -> float:
        """Combined similarity score."""

        # Levenshtein distance (edit distance)
        lev_score = 1.0 - (self._levenshtein(input_word, candidate) /
                          max(len(input_word), len(candidate)))

        # Phonetic similarity
        soundex_match = self.soundex.encode(input_word) == self.soundex.encode(candidate)
        metaphone_match = self.metaphone.encode(input_word) == self.metaphone.encode(candidate)

        phonetic_score = (0.5 if soundex_match else 0.0) + (0.5 if metaphone_match else 0.0)

        # Weighted combination
        return (lev_score * 0.4) + (phonetic_score * 0.6)


# Common mishears mapping
COMMON_MISHEARS = {
    # Movement
    "rum": "run",
    "ron": "run",
    "rin": "run",
    "hide": "hide",
    "height": "hide",
    "high": "hide",
    "duck": "duck",
    "dock": "duck",
    "dunk": "duck",

    # Combat
    "shoot": "shoot",
    "chute": "shoot",
    "suit": "shoot",
    "fire": "fire",
    "higher": "fire",
    "fyre": "fire",

    # Objects
    "gun": "gun",
    "gone": "gun",
    "gum": "gun",
    "knife": "knife",
    "life": "knife",
    "night": "knife",

    # Directions
    "left": "left",
    "lift": "left",
    "loft": "left",
    "right": "right",
    "write": "right",
    "rite": "right",
    "back": "back",
    "pack": "back",
    "black": "back",
}
```

### 2.2 Context-Aware Disambiguation

```python
class ContextualVoiceResolver:
    """Use game context to resolve ambiguous voice input."""

    def resolve(
        self,
        matches: list[FuzzyMatch],
        world_context: WorldContext,
        threat_level: float,
    ) -> VoiceCommand:
        """Pick best match given current context."""

        if len(matches) == 1 or matches[0].confidence > 0.9:
            return self._to_command(matches[0])

        # Ambiguous - use context
        for match in matches:
            context_score = self._score_in_context(match, world_context, threat_level)
            match.adjusted_confidence = match.confidence * context_score

        matches.sort(key=lambda m: m.adjusted_confidence, reverse=True)

        # If still ambiguous, prefer defensive actions during danger
        if threat_level > 0.5:
            defensive = ["run", "hide", "duck", "back", "flee"]
            for match in matches:
                if match.matched in defensive:
                    return self._to_command(match)

        return self._to_command(matches[0])

    def _score_in_context(
        self,
        match: FuzzyMatch,
        context: WorldContext,
        threat_level: float,
    ) -> float:
        """How appropriate is this command in context?"""

        score = 1.0

        # "shoot" only makes sense if player has weapon
        if match.matched == "shoot":
            if not context.player_has_weapon:
                score *= 0.1
            if context.has_visible_enemy:
                score *= 2.0

        # "hide" only makes sense if cover exists
        if match.matched == "hide":
            if context.cover_nearby:
                score *= 1.5
            else:
                score *= 0.5

        # "run" makes more sense with high threat
        if match.matched == "run":
            score *= (1.0 + threat_level)

        # "talk" makes no sense during combat
        if match.matched in ["talk", "speak", "ask"]:
            if threat_level > 0.7:
                score *= 0.1

        return score
```

### 2.3 Confidence Thresholds

```python
class VoiceConfidenceHandler:
    """Handle low-confidence voice recognition gracefully."""

    # Thresholds
    HIGH_CONFIDENCE = 0.85      # Execute immediately
    MEDIUM_CONFIDENCE = 0.6    # Execute with brief flash confirmation
    LOW_CONFIDENCE = 0.4       # Pause and confirm
    REJECT_THRESHOLD = 0.2     # Ask to repeat

    def process(
        self,
        match: FuzzyMatch,
        threat_level: float,
    ) -> VoiceProcessResult:

        # During high threat, lower thresholds - assume intent
        if threat_level > 0.8:
            effective_threshold = self.MEDIUM_CONFIDENCE * 0.7
        else:
            effective_threshold = self.MEDIUM_CONFIDENCE

        if match.confidence >= self.HIGH_CONFIDENCE:
            return VoiceProcessResult(
                action="execute",
                command=match.matched,
                show_confirmation=False,
            )

        elif match.confidence >= effective_threshold:
            return VoiceProcessResult(
                action="execute",
                command=match.matched,
                show_confirmation=True,  # Brief flash: "RUN!"
                confirmation_duration=0.3,
            )

        elif match.confidence >= self.LOW_CONFIDENCE:
            if threat_level > 0.5:
                # Danger - execute anyway, can't wait
                return VoiceProcessResult(
                    action="execute",
                    command=match.matched,
                    show_confirmation=True,
                    confirmation_duration=0.5,
                )
            else:
                # Safe - ask for confirmation
                return VoiceProcessResult(
                    action="confirm",
                    prompt=f'Did you say "{match.matched}"?',
                    alternatives=match.alternatives[:2],
                )

        else:
            return VoiceProcessResult(
                action="retry",
                prompt="Didn't catch that. Say again?",
            )
```

---

## 3. Explicit Reaction Windows

Codify timing for urgent situations.

### 3.1 Reaction Window System

```python
@dataclass
class ReactionWindow:
    """A time-limited opportunity to act."""

    id: str
    trigger: str                    # What started this window

    # Timing
    duration: float                 # Seconds to react
    elapsed: float = 0.0

    # Phases (fraction of duration)
    comfortable_phase: float = 0.5  # First 50% - no penalty
    urgent_phase: float = 0.3       # Next 30% - warnings
    critical_phase: float = 0.2     # Final 20% - severe warnings

    # State
    phase: str = "comfortable"
    warnings_given: int = 0

    # Resolution
    default_action: str             # What happens if no input
    success_actions: list[str]      # What player can do

    # Callbacks
    on_phase_change: Optional[Callable] = None
    on_timeout: Optional[Callable] = None


class ReactionWindowManager:
    """Manages time-limited reaction opportunities."""

    active_windows: list[ReactionWindow]

    # Standard windows
    WINDOW_PRESETS = {
        "thug_approach": ReactionWindow(
            duration=5.0,
            default_action="thug_attacks",
            success_actions=["run", "hide", "fight", "talk", "surrender"],
        ),
        "gunpoint": ReactionWindow(
            duration=3.0,
            default_action="shot",
            success_actions=["surrender", "duck", "disarm", "talk"],
        ),
        "falling": ReactionWindow(
            duration=1.5,
            default_action="fall_damage",
            success_actions=["grab", "roll"],
        ),
        "car_approaching": ReactionWindow(
            duration=2.0,
            default_action="hit_by_car",
            success_actions=["jump", "run", "duck"],
        ),
        "fire_spreading": ReactionWindow(
            duration=8.0,
            default_action="burned",
            success_actions=["run", "smother", "escape"],
        ),
    }

    def start_window(
        self,
        window_type: str,
        custom_duration: Optional[float] = None,
    ) -> ReactionWindow:
        """Begin a reaction window."""

        preset = self.WINDOW_PRESETS.get(window_type)
        if not preset:
            raise ValueError(f"Unknown window type: {window_type}")

        window = ReactionWindow(
            id=self._generate_id(),
            trigger=window_type,
            duration=custom_duration or preset.duration,
            default_action=preset.default_action,
            success_actions=preset.success_actions,
        )

        self.active_windows.append(window)

        # Notify systems
        self._emit_window_started(window)

        return window

    def tick(self, dt: float) -> list[WindowEvent]:
        """Update all windows, return events."""

        events = []

        for window in self.active_windows[:]:  # Copy list for removal
            window.elapsed += dt
            progress = window.elapsed / window.duration

            # Check phase transitions
            old_phase = window.phase

            if progress < window.comfortable_phase:
                window.phase = "comfortable"
            elif progress < (window.comfortable_phase + window.urgent_phase):
                window.phase = "urgent"
            else:
                window.phase = "critical"

            # Phase change events
            if window.phase != old_phase:
                events.append(WindowEvent(
                    type="phase_change",
                    window=window,
                    new_phase=window.phase,
                    time_remaining=window.duration - window.elapsed,
                ))

                # Generate warnings
                if window.phase == "urgent":
                    events.append(WindowEvent(
                        type="warning",
                        window=window,
                        message=self._get_urgent_warning(window),
                    ))
                elif window.phase == "critical":
                    events.append(WindowEvent(
                        type="warning",
                        window=window,
                        message=self._get_critical_warning(window),
                    ))

            # Timeout
            if window.elapsed >= window.duration:
                events.append(WindowEvent(
                    type="timeout",
                    window=window,
                    default_action=window.default_action,
                ))
                self.active_windows.remove(window)

        return events

    def resolve_action(
        self,
        window: ReactionWindow,
        action: str,
    ) -> WindowResolution:
        """Player acted within window."""

        if action in window.success_actions:
            self.active_windows.remove(window)

            # Calculate success modifier based on timing
            progress = window.elapsed / window.duration

            if progress < window.comfortable_phase:
                timing_bonus = 1.2  # Extra good
            elif progress < (window.comfortable_phase + window.urgent_phase):
                timing_bonus = 1.0  # Normal
            else:
                timing_bonus = 0.8  # Barely made it

            return WindowResolution(
                success=True,
                action=action,
                timing_bonus=timing_bonus,
                phase_completed=window.phase,
            )

        else:
            # Wrong action - counts as attempt but doesn't resolve
            return WindowResolution(
                success=False,
                action=action,
                message=f"Can't {action} right now!",
            )

    def _get_urgent_warning(self, window: ReactionWindow) -> str:
        """Warning message for urgent phase."""

        remaining = window.duration - window.elapsed

        WARNINGS = {
            "thug_approach": f"He's closing in. {remaining:.1f} seconds.",
            "gunpoint": f"His finger's on the trigger. {remaining:.1f}s.",
            "falling": "GRAB SOMETHING!",
            "car_approaching": "CAR! MOVE!",
            "fire_spreading": f"Fire's spreading. {remaining:.0f} seconds to escape.",
        }

        return WARNINGS.get(window.trigger, f"Act now! {remaining:.1f}s remaining.")

    def _get_critical_warning(self, window: ReactionWindow) -> str:
        """Warning message for critical phase."""

        CRITICAL = {
            "thug_approach": "NOW!",
            "gunpoint": "—",  # No time for words
            "falling": "—",
            "car_approaching": "—",
            "fire_spreading": "OUT! NOW!",
        }

        return CRITICAL.get(window.trigger, "NOW!")
```

### 3.2 Visual Feedback

```python
class ReactionWindowRenderer:
    """Visual representation of reaction windows."""

    def render_timer(self, window: ReactionWindow) -> str:
        """Render a visual timer for the window."""

        progress = window.elapsed / window.duration
        remaining = window.duration - window.elapsed

        # Bar representation
        bar_width = 20
        filled = int((1.0 - progress) * bar_width)

        if window.phase == "comfortable":
            color = "\033[32m"  # Green
            fill_char = "█"
        elif window.phase == "urgent":
            color = "\033[33m"  # Yellow
            fill_char = "▓"
        else:  # critical
            color = "\033[31m"  # Red
            fill_char = "░"
            # Flash effect
            if int(remaining * 4) % 2 == 0:
                fill_char = "█"

        reset = "\033[0m"

        bar = color + (fill_char * filled) + ("·" * (bar_width - filled)) + reset
        time_str = f"{remaining:.1f}s"

        return f"[{bar}] {time_str}"

    def render_warning(self, event: WindowEvent) -> str:
        """Render a warning message with urgency styling."""

        if event.window.phase == "comfortable":
            return event.message
        elif event.window.phase == "urgent":
            return f"\033[33m{event.message}\033[0m"  # Yellow
        else:
            return f"\033[31m\033[1m{event.message}\033[0m"  # Bold red
```

---

## 4. Procedural Terrain Generation

Use Perlin noise for coherent world generation.

### 4.1 Perlin Noise Terrain

```python
import math
from dataclasses import dataclass

class PerlinNoise:
    """2D Perlin noise generator for terrain."""

    def __init__(self, seed: int):
        self.seed = seed
        self.permutation = self._generate_permutation(seed)

    def noise(self, x: float, y: float) -> float:
        """Get noise value at position (-1.0 to 1.0)."""

        # Grid cell coordinates
        x0 = int(math.floor(x)) & 255
        y0 = int(math.floor(y)) & 255
        x1 = (x0 + 1) & 255
        y1 = (y0 + 1) & 255

        # Relative position in cell
        xf = x - math.floor(x)
        yf = y - math.floor(y)

        # Smoothstep
        u = self._fade(xf)
        v = self._fade(yf)

        # Hash corners
        aa = self.permutation[(self.permutation[x0] + y0) & 255]
        ab = self.permutation[(self.permutation[x0] + y1) & 255]
        ba = self.permutation[(self.permutation[x1] + y0) & 255]
        bb = self.permutation[(self.permutation[x1] + y1) & 255]

        # Gradient dots
        g_aa = self._grad(aa, xf, yf)
        g_ab = self._grad(ab, xf, yf - 1)
        g_ba = self._grad(ba, xf - 1, yf)
        g_bb = self._grad(bb, xf - 1, yf - 1)

        # Interpolate
        x1_interp = self._lerp(g_aa, g_ba, u)
        x2_interp = self._lerp(g_ab, g_bb, u)

        return self._lerp(x1_interp, x2_interp, v)

    def octave_noise(
        self,
        x: float,
        y: float,
        octaves: int = 4,
        persistence: float = 0.5,
    ) -> float:
        """Multi-octave noise for more natural terrain."""

        total = 0.0
        frequency = 1.0
        amplitude = 1.0
        max_value = 0.0

        for _ in range(octaves):
            total += self.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2.0

        return total / max_value

    def _fade(self, t: float) -> float:
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    def _grad(self, hash_val: int, x: float, y: float) -> float:
        h = hash_val & 3
        if h == 0: return x + y
        if h == 1: return -x + y
        if h == 2: return x - y
        return -x - y


class TerrainGenerator:
    """Generate terrain using layered Perlin noise."""

    def __init__(self, seed: int):
        self.noise = PerlinNoise(seed)

        # Different noise layers for different features
        self.elevation_noise = PerlinNoise(seed)
        self.moisture_noise = PerlinNoise(seed + 1000)
        self.urban_noise = PerlinNoise(seed + 2000)

    def generate_chunk(self, chunk_x: int, chunk_y: int) -> list[list[Tile]]:
        """Generate a chunk of terrain."""

        tiles = []

        for local_y in range(CHUNK_SIZE):
            row = []
            for local_x in range(CHUNK_SIZE):
                world_x = chunk_x * CHUNK_SIZE + local_x
                world_y = chunk_y * CHUNK_SIZE + local_y

                tile = self._generate_tile(world_x, world_y)
                row.append(tile)
            tiles.append(row)

        return tiles

    def _generate_tile(self, x: int, y: int) -> Tile:
        """Generate a single tile based on noise."""

        # Sample noise at this position
        scale = 0.05  # Adjust for feature size

        elevation = self.elevation_noise.octave_noise(x * scale, y * scale)
        moisture = self.moisture_noise.octave_noise(x * scale * 0.7, y * scale * 0.7)
        urban = self.urban_noise.octave_noise(x * scale * 0.3, y * scale * 0.3)

        # Determine terrain type based on noise values
        terrain = self._classify_terrain(elevation, moisture, urban)

        return Tile(
            x=x,
            y=y,
            z=0,
            terrain=terrain,
            material=self._get_material(terrain),
            elevation=elevation,
            traversable=self._is_traversable(terrain),
            visibility=self._get_visibility(terrain),
            generated=True,
        )

    def _classify_terrain(
        self,
        elevation: float,
        moisture: float,
        urban: float,
    ) -> TerrainType:
        """Classify terrain based on noise values."""

        # Water in low areas with moisture
        if elevation < -0.3 and moisture > 0.2:
            if elevation < -0.5:
                return TerrainType.WATER_DEEP
            return TerrainType.WATER_SHALLOW

        # Urban areas
        if urban > 0.4:
            if urban > 0.7:
                return TerrainType.WALL  # Buildings
            return TerrainType.GROUND   # Streets

        # Natural areas
        if moisture > 0.5:
            return TerrainType.VEGETATION

        if elevation > 0.6:
            return TerrainType.DEBRIS  # Rocky high ground

        return TerrainType.GROUND


class RiverGenerator:
    """Generate rivers that snake through the city."""

    def __init__(self, noise: PerlinNoise):
        self.noise = noise

    def generate_river(
        self,
        start: tuple[int, int],
        length: int,
        world: WorldGrid,
    ) -> list[tuple[int, int]]:
        """Generate a meandering river path."""

        path = [start]
        current = start

        for i in range(length):
            # Use noise to determine meander
            meander = self.noise.noise(current[0] * 0.1, current[1] * 0.1)

            # Generally flow in one direction with wobble
            dx = 1  # Main flow direction
            dy = int(meander * 2)  # -1, 0, or 1

            next_pos = (current[0] + dx, current[1] + dy)
            path.append(next_pos)
            current = next_pos

            # Carve river into world
            tile = world.get_tile(*current)
            tile.terrain = TerrainType.WATER_SHALLOW
            tile.material = Material.WATER

            # Widen river randomly
            if abs(meander) > 0.5:
                for offset in [-1, 1]:
                    neighbor = (current[0], current[1] + offset)
                    n_tile = world.get_tile(*neighbor)
                    n_tile.terrain = TerrainType.WATER_SHALLOW

        return path
```

### 4.2 Feature Placement

```python
class FeaturePlacer:
    """Place special features like waterfalls procedurally."""

    def place_waterfall(
        self,
        world: WorldGrid,
        river_path: list[tuple[int, int]],
        rng: SeededRNG,
    ) -> Optional[Entity]:
        """Place a waterfall along a river if appropriate."""

        # Find elevation changes along river
        for i, pos in enumerate(river_path[:-5]):
            current_elevation = world.get_tile(*pos).elevation
            downstream = world.get_tile(*river_path[i + 5]).elevation

            drop = current_elevation - downstream

            if drop > 0.3:  # Significant drop
                if rng.probability_check(0.6):  # 60% chance
                    return self._create_waterfall(pos, drop, world)

        return None

    def _create_waterfall(
        self,
        position: tuple[int, int],
        drop: float,
        world: WorldGrid,
    ) -> Entity:
        """Create a waterfall entity."""

        # Determine size based on drop
        height = max(2, int(drop * 10))
        width = 3

        waterfall = Entity(
            id=f"waterfall_{position[0]}_{position[1]}",
            entity_type="waterfall",
            location=position,
            dimensions=(width, height),

            # Affordances
            affordances=[
                Affordance(type=AffordanceType.CONCEAL, risk=0.4),
                Affordance(type=AffordanceType.OBSCURE),
                Affordance(type=AffordanceType.MUFFLE),
                Affordance(type=AffordanceType.DAMAGE, risk=0.6),
            ],

            # Sound
            sound_emission=Sound(
                volume=0.7,
                frequency="low",
                sound_type=SoundType.WATER,
                continuous=True,
            ),

            # Visual
            ascii_pattern=self._generate_waterfall_pattern(width, height),

            # Hidden space potential
            has_hidden_space=True,
            hidden_space_generated=False,
        )

        world.add_entity(waterfall)
        return waterfall
```

---

## 5. Auto-Generated Tile Affordances

Affordances generated from terrain type, not manually defined.

### 5.1 Terrain-Based Affordance Generation

```python
class AffordanceGenerator:
    """Generate affordances automatically from terrain properties."""

    # Base affordances by terrain type
    TERRAIN_AFFORDANCES = {
        TerrainType.GROUND: [
            (AffordanceType.SUPPORT, {"always": True}),
        ],
        TerrainType.WATER_SHALLOW: [
            (AffordanceType.SUPPORT, {"cost": 2.0}),  # Slow movement
            (AffordanceType.CONCEAL, {"partial": True}),  # Can crouch in
        ],
        TerrainType.WATER_DEEP: [
            (AffordanceType.DROWN, {"time": 30.0}),  # Can drown
            (AffordanceType.CONCEAL, {"full": True}),  # Underwater
        ],
        TerrainType.WALL: [
            (AffordanceType.BLOCK, {"always": True}),
            (AffordanceType.CONCEAL, {"adjacent": True}),  # Hide behind
        ],
        TerrainType.DOOR: [
            (AffordanceType.BLOCK, {"when_closed": True}),
            (AffordanceType.OPEN, {}),
            (AffordanceType.CLOSE, {}),
            (AffordanceType.CONNECT, {"to": "other_side"}),
        ],
        TerrainType.WINDOW: [
            (AffordanceType.BLOCK, {"partial": True}),
            (AffordanceType.BREAK, {"noise": 0.8}),
            (AffordanceType.CONNECT, {"when_broken": True}),
        ],
        TerrainType.LEDGE: [
            (AffordanceType.SUPPORT, {"narrow": True}),
            (AffordanceType.FALL, {"adjacent": True}),
            (AffordanceType.CONCEAL, {"from_below": True}),
        ],
        TerrainType.VEGETATION: [
            (AffordanceType.SUPPORT, {"always": True}),
            (AffordanceType.CONCEAL, {"partial": True}),
            (AffordanceType.MUFFLE, {"footsteps": True}),
        ],
        TerrainType.DEBRIS: [
            (AffordanceType.SUPPORT, {"unstable": True}),
            (AffordanceType.CONCEAL, {"partial": True}),
            (AffordanceType.DAMAGE, {"trip_hazard": True}),
        ],
    }

    # Material modifiers
    MATERIAL_MODIFIERS = {
        Material.GLASS: {
            AffordanceType.BREAK: {"easier": True, "noise": 0.9},
        },
        Material.WOOD: {
            AffordanceType.BREAK: {"possible": True, "noise": 0.5},
            AffordanceType.EMIT_SOUND: {"creaks": True},
        },
        Material.METAL: {
            AffordanceType.EMIT_SOUND: {"clangs": True},
            AffordanceType.BREAK: {"difficult": True},
        },
        Material.FABRIC: {
            AffordanceType.MUFFLE: {"bonus": 0.3},
            AffordanceType.CONCEAL: {"bonus": 0.2},
        },
    }

    def generate_affordances(self, tile: Tile) -> list[Affordance]:
        """Generate all affordances for a tile."""

        affordances = []

        # Base affordances from terrain
        terrain_affs = self.TERRAIN_AFFORDANCES.get(tile.terrain, [])
        for aff_type, params in terrain_affs:
            affordances.append(self._create_affordance(aff_type, params, tile))

        # Apply material modifiers
        material_mods = self.MATERIAL_MODIFIERS.get(tile.material, {})
        for aff in affordances:
            if aff.type in material_mods:
                self._apply_modifier(aff, material_mods[aff.type])

        # Context-based additions
        affordances.extend(self._generate_contextual(tile))

        return affordances

    def _generate_contextual(self, tile: Tile) -> list[Affordance]:
        """Generate affordances based on surroundings."""

        contextual = []

        # If next to water, can be pushed in
        if self._adjacent_to(tile, TerrainType.WATER_DEEP):
            contextual.append(Affordance(
                type=AffordanceType.FALL,
                requires=["force_applied"],
                state_changes={"enters_water": True},
            ))

        # If on high ground, can see further
        if tile.elevation > 0.5:
            contextual.append(Affordance(
                type=AffordanceType.OBSERVE,
                state_changes={"vision_bonus": 2},
            ))

        # If in shadow (low visibility), can hide
        if tile.visibility < 0.5:
            contextual.append(Affordance(
                type=AffordanceType.CONCEAL,
                requires=[],
                risk=0.1,
            ))

        return contextual
```

---

## 6. LLM Constraint Prompting

Be explicit with the LLM about what it can and cannot do.

### 6.1 Strict Interpretation Prompts

```python
LLM_INTERPRETATION_PROMPT = """
You are the INTENT INTERPRETER for a noir ASCII game. Your ONLY job is to understand what the player WANTS to do.

CRITICAL RULES:
1. INTERPRET intent strictly - do not invent or embellish
2. DESCRIBE outcomes procedurally - based on world state, not imagination
3. NEVER decide success or failure - that's the simulation's job
4. NEVER create objects, NPCs, or locations that don't exist in the provided state
5. If the input is ambiguous, pick the most contextually appropriate interpretation

WORLD STATE:
{world_state}

PLAYER INPUT: "{input}"

OUTPUT FORMAT (JSON):
{{
    "intent_type": "MOVE|EXAMINE|INTERACT|TALK|ATTACK|FLEE|USE",
    "target": "entity_id or null",
    "target_location": [x, y] or null,
    "modifiers": {{"stealth": bool, "speed": "slow|normal|fast", "force": bool}},
    "confidence": 0.0-1.0,
    "interpretation": "One sentence explaining your interpretation"
}}

EXAMPLES:
Input: "go behind the waterfall"
Output: {{"intent_type": "MOVE", "target": "waterfall_01", "modifiers": {{"stealth": true}}, "interpretation": "Player wants to move to concealment behind waterfall"}}

Input: "check the body"
Output: {{"intent_type": "EXAMINE", "target": "corpse_02", "interpretation": "Player wants to examine the corpse for clues"}}
"""

LLM_EXPANSION_PROMPT = """
You are generating HIDDEN CONTENT for a location the player is exploring.

STRICT CONSTRAINTS:
1. Genre: 1940s noir crime drama
2. Technology: Period-appropriate only (no computers, modern weapons, etc.)
3. Supernatural: FORBIDDEN (no magic, ghosts, impossible physics)
4. Must respect established facts: {established_facts}
5. Must not contradict the narrative spine: {narrative_spine}
6. Danger level MUST be between {min_danger} and {max_danger}

LOCATION BEING GENERATED: {location_description}
TRIGGER: Player said "{trigger_action}"
SURROUNDING CONTEXT: {context}

Generate plausible content. A waterfall might hide:
- A rocky cavity (dangerous but passable)
- A maintenance tunnel (urban infrastructure)
- Just rocks and spray (nothing special)
- A hidden alcove (someone's stash)

It should NOT hide:
- A magical portal
- A high-tech facility
- A dragon
- Anything impossible for 1940s NYC

OUTPUT FORMAT (JSON):
{{
    "description": "2-3 sentences describing what's here",
    "terrain_changes": [...],
    "hazards": [{{"type": "...", "severity": 0.0-1.0}}],
    "items": [{{"id": "...", "name": "...", "clue_value": true/false}}],
    "secrets": ["things not immediately visible"],
    "danger_level": 0.0-1.0
}}
"""

LLM_NARRATION_PROMPT = """
You are the NARRATOR for a 1940s noir story. Describe what just happened.

STYLE RULES:
1. Second person, present tense
2. Short, punchy sentences - this is noir, not poetry
3. Maximum 3 sentences
4. Match tone to player's moral alignment: {moral_alignment}
   - Pragmatic: matter-of-fact, dry
   - Corrupt: cynical, dark humor
   - Compassionate: empathetic, noting cost
   - Ruthless: cold, efficient
   - Idealistic: dramatic, principled

WHAT HAPPENED: {action_result}
PLAYER STATE: {player_state}
ENVIRONMENT: {environment}

Write the narration. No preamble. Just the text.
"""
```

---

## 7. Prototype-First Development

Start small. One area. Prove the concept.

### 7.1 Minimum Viable Prototype

```python
# prototype_scope.py
"""
PROTOTYPE SCOPE: Riverside Park with Waterfall

One location. All core systems. Prove the concept.
"""

PROTOTYPE_BOUNDS = {
    "size": (50, 50),  # 50x50 tile area
    "location": "riverside_park",
    "features": [
        "river (generated via Perlin noise)",
        "waterfall (placed procedurally)",
        "park paths",
        "benches (cover)",
        "trees (concealment)",
        "bridge (chokepoint)",
        "one NPC (patrolling thug)",
    ],
}

PROTOTYPE_SYSTEMS = {
    "MUST HAVE": [
        "Tile-based world (50x50)",
        "Basic movement (WASD or intent)",
        "LLM intent interpretation",
        "One NPC with patrol behavior",
        "Sound propagation (basic)",
        "Waterfall with hidden space generation",
        "One reaction window (thug approach)",
    ],
    "NICE TO HAVE": [
        "STT integration",
        "Multiple NPCs",
        "Weather effects",
        "Full injury system",
    ],
    "DEFER": [
        "Infinite world generation",
        "Save/load",
        "Multiple scenarios",
        "Full narrative spine",
    ],
}

PROTOTYPE_SUCCESS_CRITERIA = [
    "Player can wander the park freely",
    "Player can say 'go behind waterfall' and it works",
    "LLM generates what's behind (rocks, cave, nothing)",
    "Thug patrols and reacts to sound",
    "Player can hide and evade",
    "No 'I don't understand' errors ever",
    "Reaction window works with keyboard input",
]

class PrototypeGame:
    """Minimal implementation to prove concept."""

    def __init__(self, seed: int = 42):
        # Core systems only
        self.world = WorldGrid(width=50, height=50)
        self.terrain_gen = TerrainGenerator(seed)
        self.sound = SoundPropagationEngine()
        self.llm = LLMInterpreter(model="claude-3-haiku")  # Fast, cheap
        self.renderer = SimpleASCIIRenderer()

        # Single NPC
        self.thug = PatrollingNPC(
            route=[(10, 25), (40, 25), (40, 10), (10, 10)],
            hearing_threshold=0.2,
        )

        # Player
        self.player = Player(position=(25, 25))

        # Generate world
        self._generate_park()

    def _generate_park(self):
        """Generate the test park."""

        # Base terrain from noise
        for y in range(50):
            for x in range(50):
                self.world.set_tile(x, y, self.terrain_gen._generate_tile(x, y))

        # Carve river
        river = RiverGenerator(self.terrain_gen.noise)
        river_path = river.generate_river((0, 25), 50, self.world)

        # Place waterfall
        placer = FeaturePlacer()
        self.waterfall = placer.place_waterfall(
            self.world, river_path, SeededRNG(42)
        )

    async def run(self):
        """Main loop."""

        while True:
            # Render
            frame = self.renderer.render(self.world, self.player, [self.thug])
            print(frame)

            # Get input
            raw_input = input("> ")

            # Interpret
            intent = await self.llm.interpret_input(
                raw_input,
                self._get_context(),
            )

            # Resolve
            result = self._resolve_intent(intent)

            # Narrate
            narration = await self.llm.generate_narration(result)
            print(narration)

            # Update world
            self.sound.tick(0.5)
            self.thug.tick(0.5, self.world, self.sound)

            # Check for reaction windows
            if self.thug.can_see(self.player):
                window = ReactionWindow(
                    duration=5.0,
                    default_action="thug_attacks",
                    success_actions=["run", "hide", "fight"],
                )
                result = await self._run_reaction_window(window)
```

### 7.2 Test Scenarios

```python
PROTOTYPE_TEST_SCENARIOS = [
    {
        "name": "Waterfall Exploration",
        "setup": "Player near waterfall, thug far away",
        "input": "go behind the waterfall",
        "expected": [
            "LLM interprets as MOVE + CONCEAL",
            "World generates hidden space (or not)",
            "Player moves there",
            "Sound is masked by waterfall",
            "Narration describes the experience",
        ],
    },
    {
        "name": "Sound Alert",
        "setup": "Player runs across gravel, thug within earshot",
        "input": "run to the bridge",
        "expected": [
            "Movement generates sound (0.3 volume)",
            "Sound propagates to thug",
            "Thug hears, becomes alert",
            "Thug changes behavior to investigate",
        ],
    },
    {
        "name": "Waterfall Sound Mask",
        "setup": "Player near waterfall, thug nearby",
        "input": "fire my gun",
        "expected": [
            "Gunshot (1.0 volume) is masked by waterfall",
            "Thug hears reduced volume (0.1)",
            "Below threshold - no alert",
            "Player gets away with it",
        ],
    },
    {
        "name": "Reaction Window",
        "setup": "Thug spots player",
        "trigger": "Thug approaches",
        "expected": [
            "5 second window starts",
            "Visual timer displayed",
            "Player can type 'run', 'hide', 'fight'",
            "If timeout, thug attacks",
            "If success, action resolves",
        ],
    },
    {
        "name": "Fuzzy Input",
        "setup": "Any",
        "input": "rum away",  # Typo
        "expected": [
            "Fuzzy matcher catches 'rum' -> 'run'",
            "Executes run action",
            "No parser error",
        ],
    },
]
```

---

## Summary: What Was Missing

| System | Status | Added In |
|--------|--------|----------|
| Sound propagation | **NEW** | Section 1 |
| NPC sound response | **NEW** | Section 1.3 |
| Waterfall sound masking | **NEW** | Section 1.4 |
| Fuzzy STT matching | **NEW** | Section 2 |
| Phonetic similarity | **NEW** | Section 2.1 |
| Context disambiguation | **NEW** | Section 2.2 |
| Explicit reaction windows | **NEW** | Section 3 |
| Timed phases (comfortable/urgent/critical) | **NEW** | Section 3.1 |
| Perlin noise terrain | **NEW** | Section 4 |
| River/waterfall generation | **NEW** | Section 4.2 |
| Auto-generated affordances | **NEW** | Section 5 |
| Strict LLM prompts | **NEW** | Section 6 |
| Prototype scope definition | **NEW** | Section 7 |

---

*End of Sound and Systems Addendum*
