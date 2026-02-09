# ShadowEngine — Threat Proximity & Reaction Timing System

> **Version**: 1.0.0
> **Status**: Core Real-Time System
> **Purpose**: Make time a mechanic, STT meaningful, hesitation lethal

---

## Core Design Rule

**The world advances whether the player acts or not.**

- No "waiting for input"
- No safe parser pause
- Time is always moving

This is not a turn-based system with real-time decoration.
This is continuous simulation with player interrupts.

---

## Conceptual Model

Every threat exists in **continuous time**, not turns.

```
┌─────────────────────────────────────────────────────────────────┐
│                    THREAT vs PLAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  THREAT HAS:                    PLAYER HAS:                      │
│  ├─ Distance                    ├─ Reaction latency              │
│  ├─ Speed                       ├─ Movement affordances          │
│  ├─ Awareness                   ├─ Cognitive load                │
│  ├─ Intent                      ├─ Injury modifiers              │
│  └─ Lethality window            └─ Fear state                    │
│                                                                  │
│                         ↓                                        │
│              SYSTEM RESOLVES COLLISION                           │
│                    OF INTENT                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Threat Object Schema

```python
@dataclass
class Threat:
    """An active danger in the world."""

    id: str
    threat_type: str                # "gunman", "fire", "vehicle", "collapse"

    # Position & movement
    position: tuple[float, float]
    velocity: float                 # Tiles per second
    direction: tuple[float, float]  # Movement vector

    # Perception
    awareness: float                # 0.0-1.0: Probability of detecting player
    vision_cone: float              # Degrees of vision
    hearing_range: float            # Tiles

    # Behavior
    intent: str                     # "pursue", "patrol", "ambush", "flee"
    escalation_stage: int           # Current stage (0-4)

    # Danger parameters
    lethality_range: float          # Distance at which damage triggers
    reaction_window: float          # Seconds before decisive action
    damage_potential: float         # 0.0-1.0

    # Stealth factors
    sound_signature: float          # How loud the threat is
    visibility: float               # How visible in current conditions

    # Behavior modifiers
    fearless: bool                  # Ignores player intimidation
    persistent: bool                # Doesn't give up pursuit
```

### Threat Schema (JSON)

```json
{
  "id": "threat_7721",
  "threat_type": "gunman",
  "position": [12, 8],
  "velocity": 0.6,
  "direction": [1, 0],
  "awareness": 0.7,
  "vision_cone": 120,
  "hearing_range": 15,
  "intent": "pursue",
  "escalation_stage": 1,
  "lethality_range": 2.0,
  "reaction_window": 1.2,
  "damage_potential": 0.8,
  "sound_signature": 0.5,
  "visibility": 0.8,
  "fearless": false,
  "persistent": true
}
```

### Key Fields Explained

| Field | Meaning |
|-------|---------|
| `velocity` | Tiles per second (0.6 = walking, 1.2 = running) |
| `awareness` | Probability of reacting to player action |
| `reaction_window` | Seconds before threat takes decisive action |
| `lethality_range` | Distance at which damage triggers |
| `escalation_stage` | Current aggression level (see Section 7) |

---

## 2. Player Reaction Model

### Timing Components

```python
@dataclass
class PlayerReactionState:
    """Factors affecting player's reaction speed."""

    # Base values
    base_reaction: float = 0.3      # Seconds (human baseline)

    # Input latency
    stt_latency: float = 0.0        # STT processing time
    input_latency: float = 0.0      # Keyboard/parsing time

    # Modifiers
    injury_penalty: float = 0.0     # From wounds
    fear_penalty: float = 0.0       # From psychological state
    fatigue_penalty: float = 0.0    # From exhaustion

    # Bonuses
    adrenaline_bonus: float = 0.0   # Combat readiness
    preparation_bonus: float = 0.0  # Already planning to act

    def effective_reaction_time(self) -> float:
        """Calculate total reaction time."""
        return max(0.1, (
            self.base_reaction +
            self.stt_latency +
            self.input_latency +
            self.injury_penalty +
            self.fear_penalty +
            self.fatigue_penalty -
            self.adrenaline_bonus -
            self.preparation_bonus
        ))
```

### Component Sources

| Component | Source |
|-----------|--------|
| `stt_latency` | Microphone + speech processing |
| `injury_penalty` | Current wounds (leg injury = +0.2s) |
| `fear_penalty` | Threat proximity + NPC aggression |
| `adrenaline_bonus` | Recent combat, high threat awareness |

### The Critical Comparison

```python
def resolve_reaction(player: Player, threat: Threat) -> ReactionResult:
    """Determine who acts first."""

    player_time = player.reaction_state.effective_reaction_time()
    threat_window = threat.reaction_window

    if player_time <= threat_window * 0.5:
        return ReactionResult.EARLY          # Full success
    elif player_time <= threat_window * 0.8:
        return ReactionResult.ON_TIME        # Success with cost
    elif player_time <= threat_window:
        return ReactionResult.LATE           # Partial success
    else:
        return ReactionResult.TOO_LATE       # Threat acts first
```

---

## 3. Threat Proximity Bands

**Distance is not binary.** Proximity creates escalating pressure.

### Proximity States

```python
class ProximityBand(Enum):
    FAR = "far"             # > 15 tiles
    MEDIUM = "medium"       # 8-15 tiles
    NEAR = "near"           # 3-8 tiles
    IMMINENT = "imminent"   # 1-3 tiles
    CONTACT = "contact"     # < 1 tile
```

### Band Effects

| Distance | State | Effect |
|----------|-------|--------|
| > 15 tiles | FAR | Audio cues only |
| 8-15 tiles | MEDIUM | Visual jitter begins |
| 3-8 tiles | NEAR | Input penalty, screen pressure |
| 1-3 tiles | IMMINENT | Reaction window shrinking |
| < 1 tile | CONTACT | Damage resolution |

### Proximity System

```python
class ProximitySystem:
    """Manage threat distance and effects."""

    BAND_THRESHOLDS = {
        ProximityBand.FAR: 15.0,
        ProximityBand.MEDIUM: 8.0,
        ProximityBand.NEAR: 3.0,
        ProximityBand.IMMINENT: 1.0,
        ProximityBand.CONTACT: 0.0,
    }

    def get_band(self, distance: float) -> ProximityBand:
        """Determine proximity band from distance."""
        for band, threshold in self.BAND_THRESHOLDS.items():
            if distance > threshold:
                return band
        return ProximityBand.CONTACT

    def get_effects(self, band: ProximityBand) -> ProximityEffects:
        """Get effects for current proximity band."""

        EFFECTS = {
            ProximityBand.FAR: ProximityEffects(
                audio_cues=True,
                visual_effects=False,
                reaction_modifier=0.0,
                fear_generation=0.1,
            ),
            ProximityBand.MEDIUM: ProximityEffects(
                audio_cues=True,
                visual_effects=True,
                visual_intensity=0.3,
                reaction_modifier=0.0,
                fear_generation=0.3,
            ),
            ProximityBand.NEAR: ProximityEffects(
                audio_cues=True,
                visual_effects=True,
                visual_intensity=0.6,
                reaction_modifier=+0.1,  # Slower reactions
                fear_generation=0.5,
            ),
            ProximityBand.IMMINENT: ProximityEffects(
                audio_cues=True,
                visual_effects=True,
                visual_intensity=0.9,
                reaction_modifier=+0.2,
                fear_generation=0.8,
                reaction_window_shrink=0.3,  # 30% less time
            ),
            ProximityBand.CONTACT: ProximityEffects(
                damage_resolution=True,
                reaction_modifier=+0.5,
                fear_generation=1.0,
            ),
        }

        return EFFECTS[band]
```

---

## 4. ASCII Proximity Rendering

**The screen communicates danger without UI elements.**

### Visual Effects by Proximity

```python
class ProximityRenderer:
    """Render threat proximity through ASCII effects."""

    def apply_proximity_effects(
        self,
        frame: Frame,
        threats: list[Threat],
        player_pos: tuple[int, int],
    ) -> Frame:
        """Apply visual effects based on threat proximity."""

        for threat in threats:
            distance = self._distance(player_pos, threat.position)
            band = self.proximity.get_band(distance)
            direction = self._direction(player_pos, threat.position)

            if band == ProximityBand.MEDIUM:
                # Subtle jitter in threat direction
                frame = self._apply_directional_jitter(
                    frame, direction, intensity=0.3
                )

            elif band == ProximityBand.NEAR:
                # Screen pressure - edges darken
                frame = self._apply_edge_pressure(
                    frame, direction, intensity=0.6
                )
                # Threat character thickens
                frame = self._thicken_threat_char(frame, threat.position)

            elif band == ProximityBand.IMMINENT:
                # Flicker rate increases
                frame = self._apply_flicker(frame, rate=0.8)
                # Partial redraw distortion
                frame = self._apply_redraw_glitch(frame, intensity=0.5)
                # Screen shake
                frame = self._apply_shake(frame, intensity=0.4)

            elif band == ProximityBand.CONTACT:
                # Full distortion
                frame = self._apply_impact_flash(frame)

        return frame

    def _thicken_threat_char(self, frame: Frame, pos: tuple) -> Frame:
        """Make threat character more prominent."""
        # @ becomes █ or ▓
        # Surrounding tiles get shadow
        ...

    def _apply_directional_jitter(
        self,
        frame: Frame,
        direction: str,
        intensity: float,
    ) -> Frame:
        """Jitter tiles in the direction of threat."""
        # Tiles on left shimmer if threat is left
        ...
```

### Audio Cues

```python
class ProximityAudio:
    """Audio feedback for threat proximity."""

    def get_audio_cue(self, band: ProximityBand) -> Optional[str]:
        """Get terminal audio cue for proximity."""

        if band == ProximityBand.FAR:
            return None  # Distant sounds handled by sound system

        elif band == ProximityBand.MEDIUM:
            return "\a"  # Single terminal bell

        elif band == ProximityBand.NEAR:
            return "\a\a"  # Double bell

        elif band == ProximityBand.IMMINENT:
            return "\a\a\a"  # Triple bell (urgent)

        return None
```

### Rendering Examples

```
FAR (> 15 tiles):
┌────────────────────────────────────────┐
│                                        │
│    Normal rendering                    │
│    Distant footsteps (audio only)      │
│                                        │
└────────────────────────────────────────┘

MEDIUM (8-15 tiles):
┌────────────────────────────────────────┐
│                                  ▒     │
│    Subtle jitter on right edge   ▒     │
│    Direction indicator appears   →     │
│                                  ▒     │
└────────────────────────────────────────┘

NEAR (3-8 tiles):
┌────────────────────────────────────────┐
│                                ▓▓▓▓▓▓▓ │
│    Edge darkening               ▓▓▓▓▓ │
│    Threat char thickens   ☻ →   ▓▓▓▓▓ │
│                                ▓▓▓▓▓▓▓ │
└────────────────────────────────────────┘

IMMINENT (1-3 tiles):
┌──────────────────────────────────────┐
│▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▓│
│▒▒▒ Screen flicker             █ ▓▓▓▓│
│▒▒▒ Partial redraw glitch     @  ▓▓▓▓│
│▒▒▒ Shake effect                 ▓▓▓▓│
│▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▓▓│
└──────────────────────────────────────┘
```

---

## 5. Awareness & Line of Sight

Threat awareness updates every tick based on player actions.

### Awareness Factors

```python
class AwarenessSystem:
    """Calculate threat awareness of player."""

    def calculate_awareness(
        self,
        threat: Threat,
        player: Player,
        environment: Environment,
    ) -> float:
        """Calculate how aware threat is of player."""

        base_awareness = threat.awareness
        modifiers = []

        # Movement increases detection
        if player.is_moving:
            if player.is_running:
                modifiers.append(("running", +0.3))
            else:
                modifiers.append(("walking", +0.1))

        # Sound signature
        player_noise = player.current_sound_signature
        if player_noise > 0.5:
            modifiers.append(("noise", +player_noise * 0.4))

        # Light exposure
        player_light = environment.get_light_at(player.position)
        if player_light > 0.7:
            modifiers.append(("lit", +0.2))
        elif player_light < 0.3:
            modifiers.append(("dark", -0.2))

        # Weather effects
        if environment.weather == Weather.HEAVY_RAIN:
            modifiers.append(("rain_cover", -0.3))
        elif environment.weather == Weather.FOG:
            modifiers.append(("fog_cover", -0.4))

        # Previous memory (rumors about player)
        if threat.has_memory("player_location"):
            modifiers.append(("memory", +0.2))

        # Standing still in cover
        if player.is_stationary and player.is_in_cover:
            modifiers.append(("hidden", -0.4))

        # Calculate final
        total_modifier = sum(m[1] for m in modifiers)
        final_awareness = max(0.0, min(1.0, base_awareness + total_modifier))

        return final_awareness

    def check_detection(self, threat: Threat, player: Player) -> bool:
        """Roll for detection."""
        awareness = self.calculate_awareness(threat, player, self.environment)
        return random() < awareness
```

### Line of Sight

```python
class LineOfSight:
    """Vision cone and obstruction checks."""

    def can_see(
        self,
        threat: Threat,
        player: Player,
        world: WorldGrid,
    ) -> bool:
        """Check if threat can see player."""

        # Distance check
        distance = self._distance(threat.position, player.position)
        if distance > threat.hearing_range:
            return False  # Too far

        # Vision cone check
        angle = self._angle_to(threat.position, threat.direction, player.position)
        if abs(angle) > threat.vision_cone / 2:
            return False  # Outside vision cone

        # Obstruction check
        path = self._trace_line(threat.position, player.position)
        for tile_pos in path:
            tile = world.get_tile(*tile_pos)
            if tile.blocks_vision:
                return False  # Obstructed

        return True
```

---

## 6. STT Integration (Critical)

**Voice input does not pause the world.** Input is interrupt-based.

### Input as Interrupt

```python
class STTInterruptSystem:
    """Process voice input as real-time interrupts."""

    async def process_voice_input(
        self,
        audio: bytes,
        world_state: WorldState,
        active_threats: list[Threat],
    ) -> VoiceInputResult:
        """Process voice input against real-time threats."""

        # Capture timestamp IMMEDIATELY
        input_timestamp = time.time()

        # Transcribe (this takes time)
        transcription_start = time.time()
        transcript = await self.stt_engine.transcribe(audio)
        stt_latency = time.time() - transcription_start

        # Parse intent
        intent = self.intent_parser.parse(transcript)

        # Find most urgent threat
        urgent_threat = self._get_most_urgent_threat(active_threats)

        if urgent_threat:
            # Calculate reaction timing
            player_reaction = self.player.reaction_state.effective_reaction_time()
            player_reaction += stt_latency  # Add STT processing time

            # Compare to threat window
            result = self._resolve_timing(
                player_reaction,
                urgent_threat.reaction_window,
                intent,
                urgent_threat,
            )

            return result

        else:
            # No urgent threat - normal resolution
            return VoiceInputResult(
                success=True,
                intent=intent,
                timing="normal",
            )

    def _resolve_timing(
        self,
        player_time: float,
        threat_window: float,
        intent: Intent,
        threat: Threat,
    ) -> VoiceInputResult:
        """Resolve voice command timing against threat."""

        ratio = player_time / threat_window

        if ratio <= 0.5:
            # EARLY: Full success
            return VoiceInputResult(
                success=True,
                intent=intent,
                timing="early",
                message="You react instantly.",
                damage=0.0,
            )

        elif ratio <= 0.8:
            # ON TIME: Success with minor cost
            return VoiceInputResult(
                success=True,
                intent=intent,
                timing="on_time",
                message="You react just in time.",
                damage=threat.damage_potential * 0.1,
            )

        elif ratio <= 1.0:
            # LATE: Partial success
            return VoiceInputResult(
                success=True,
                partial=True,
                intent=intent,
                timing="late",
                message="You react, but not fast enough.",
                damage=threat.damage_potential * 0.4,
            )

        else:
            # TOO LATE: Threat acts first
            return VoiceInputResult(
                success=False,
                intent=intent,
                timing="too_late",
                message="Too slow.",
                damage=threat.damage_potential * 0.8,
            )
```

### Partial Success Outcomes

| Timing | Result | Example |
|--------|--------|---------|
| Early (< 50%) | Full escape | Clean getaway |
| On time (50-80%) | Minor cost | Graze wound |
| Late (80-100%) | Injury + escape | Shoulder hit, but moving |
| Too late (> 100%) | Threat wins | Knockdown or worse |

### Voice Command Flow

```
Player shouts: "Run away!"
         │
         ▼
┌─────────────────────┐
│ Capture timestamp   │  t = 0.0s
│ (immediately)       │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ STT processing      │  t = 0.3s (STT latency)
│ "Run away" → FLEE   │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Intent parsing      │  t = 0.35s
│ intent: flee        │
│ direction: away     │
│ urgency: 0.9        │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Timing comparison   │  Player: 0.65s
│ threat_window: 1.2s │  Threat: 1.2s
│ ratio: 0.54         │  Result: ON_TIME
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Resolution          │  Escape with graze
│ Apply 10% damage    │
│ Update position     │
└─────────────────────┘
```

---

## 7. Threat Escalation Ladder

**Threats don't instantly kill. They escalate.**

### Escalation Stages

```python
class EscalationStage(Enum):
    NOTICE = 0          # Threat notices player
    CHALLENGE = 1       # Verbal warning
    ADVANCE = 2         # Moving toward player
    AIM = 3             # Preparing attack
    WARNING = 4         # Warning action (warning shot)
    LETHAL = 5          # Attack to kill


ESCALATION_PROPERTIES = {
    EscalationStage.NOTICE: {
        "reaction_window": 3.0,     # 3 seconds to respond
        "player_options": ["hide", "flee", "talk", "wait"],
        "threat_action": "notices player, pauses",
    },
    EscalationStage.CHALLENGE: {
        "reaction_window": 2.0,
        "player_options": ["flee", "talk", "surrender", "attack"],
        "threat_action": "shouts 'Hey!'",
    },
    EscalationStage.ADVANCE: {
        "reaction_window": 1.5,
        "player_options": ["flee", "attack", "surrender"],
        "threat_action": "moves toward player",
    },
    EscalationStage.AIM: {
        "reaction_window": 1.0,
        "player_options": ["duck", "attack", "surrender"],
        "threat_action": "raises weapon, aims",
    },
    EscalationStage.WARNING: {
        "reaction_window": 0.8,
        "player_options": ["duck", "surrender"],
        "threat_action": "fires warning shot",
    },
    EscalationStage.LETHAL: {
        "reaction_window": 0.5,
        "player_options": ["duck"],
        "threat_action": "fires to kill",
    },
}
```

### Escalation Flow

```
GUNMAN ESCALATION:

Stage 0: NOTICE (3.0s window)
  "Hey, who's there?"
  Player can: hide, flee, talk, wait

Stage 1: CHALLENGE (2.0s window)
  "Don't move!"
  Player can: flee, talk, surrender, attack

Stage 2: ADVANCE (1.5s window)
  *footsteps approaching*
  Player can: flee, attack, surrender

Stage 3: AIM (1.0s window)
  *weapon raised*
  Player can: duck, attack, surrender

Stage 4: WARNING (0.8s window)
  *BANG* (warning shot)
  Player can: duck, surrender

Stage 5: LETHAL (0.5s window)
  *aims at center mass*
  Player can: duck

Each stage:
  - Shrinks reaction window
  - Increases fear
  - Narrows options
```

### Escalation System

```python
class EscalationSystem:
    """Manage threat escalation over time."""

    def tick_threat(self, threat: Threat, dt: float, player: Player) -> list[Event]:
        """Update threat escalation state."""

        events = []

        # Check if player is still detected
        if not self.awareness.check_detection(threat, player):
            # Player escaped detection
            threat.escalation_stage = max(0, threat.escalation_stage - 1)
            return events

        # Check if current stage reaction window expired
        stage_props = ESCALATION_PROPERTIES[EscalationStage(threat.escalation_stage)]
        window = stage_props["reaction_window"]

        if threat.stage_timer >= window:
            # Escalate to next stage
            if threat.escalation_stage < EscalationStage.LETHAL.value:
                threat.escalation_stage += 1
                threat.stage_timer = 0

                new_stage = EscalationStage(threat.escalation_stage)
                events.append(EscalationEvent(
                    threat=threat,
                    new_stage=new_stage,
                    action=ESCALATION_PROPERTIES[new_stage]["threat_action"],
                ))

        else:
            threat.stage_timer += dt

        return events

    def get_player_options(self, threat: Threat) -> list[str]:
        """Get available player actions for current escalation."""
        stage = EscalationStage(threat.escalation_stage)
        return ESCALATION_PROPERTIES[stage]["player_options"]
```

---

## 8. Multiple Threats

**Threats interact. Multiple enemies create compound danger.**

### Multi-Threat Resolution

```python
class MultiThreatSystem:
    """Handle multiple simultaneous threats."""

    def calculate_compound_effects(
        self,
        threats: list[Threat],
        player: Player,
    ) -> CompoundThreatEffects:
        """Calculate combined effects of multiple threats."""

        effects = CompoundThreatEffects()

        if len(threats) < 2:
            return effects  # No compound effects

        # Flanking detection
        if self._is_flanked(threats, player):
            effects.reaction_modifier += 0.3  # 30% slower reactions
            effects.escape_affordances -= 0.4  # Fewer escape routes

        # Crossfire
        if self._has_crossfire(threats, player):
            effects.cover_effectiveness -= 0.5  # Cover less effective
            effects.damage_multiplier += 0.3

        # Noise compounds
        total_noise = sum(t.sound_signature for t in threats)
        if total_noise > 1.5:
            effects.third_party_attraction += 0.4  # Attracts more threats

        # Fear compounds
        effects.fear_multiplier = 1.0 + (len(threats) - 1) * 0.3

        return effects

    def _is_flanked(self, threats: list[Threat], player: Player) -> bool:
        """Check if threats are on opposite sides."""
        if len(threats) < 2:
            return False

        angles = []
        for threat in threats:
            angle = self._angle_from_player(player.position, threat.position)
            angles.append(angle)

        # Check if any two threats are > 90 degrees apart
        for i, a1 in enumerate(angles):
            for a2 in angles[i+1:]:
                if abs(a1 - a2) > 90:
                    return True

        return False
```

### Multi-Threat Scenario

```
TWO GUNMEN SCENARIO:

Gunman A: Left side, Stage 2 (ADVANCE)
Gunman B: Right side, Stage 1 (CHALLENGE)

Compound Effects:
  - Player is FLANKED
  - Reaction time: +0.3s penalty
  - Escape affordances: -40%
  - "run left" blocked by Gunman A
  - "run right" blocked by Gunman B
  - Best option: cover + negotiate

If Player attacks Gunman A:
  - Gunman B escalates immediately
  - Now facing lethal threat from behind
```

---

## 9. Environmental Threats

**Threats aren't just NPCs.** The environment is dangerous.

### Environmental Threat Types

```python
class EnvironmentalThreat:
    """Non-NPC danger sources."""

    TYPES = {
        "fire": {
            "velocity": 0.2,            # Spreads slowly
            "lethality_range": 0.5,     # Must be very close
            "reaction_window": 2.0,     # Time to escape
            "damage_type": "burn",
            "awareness": 0.0,           # Doesn't "see" player
            "blocks_path": True,
        },
        "flooding": {
            "velocity": 0.4,
            "lethality_range": 0.0,     # Drowning is gradual
            "damage_type": "drown",
            "time_to_drown": 30.0,      # Seconds in deep water
            "movement_penalty": 0.5,
        },
        "collapse": {
            "velocity": 0.0,            # Instant
            "lethality_range": 3.0,     # Area effect
            "reaction_window": 0.5,     # Very short warning
            "damage_type": "crush",
            "warning_signs": ["creak", "dust", "shake"],
        },
        "falling": {
            "velocity": 9.8,            # Gravity
            "damage_per_meter": 0.1,    # Scales with height
            "reaction_window": 0.3,     # Grab ledge time
        },
        "vehicle": {
            "velocity": 5.0,            # Fast
            "lethality_range": 1.0,
            "reaction_window": 0.8,
            "sound_signature": 0.9,     # Loud warning
            "awareness": 0.0,           # Doesn't track player
        },
        "crowd": {
            "velocity": 0.3,
            "damage_type": "trample",
            "stampede_threshold": 10,   # NPCs before danger
            "movement_penalty": 0.7,
        },
    }
```

### Waterfall as Threat

```python
waterfall_threat = EnvironmentalThreat(
    threat_type="waterfall",
    properties={
        "pull_force": 0.6,          # Forced movement toward
        "slipperiness": 0.8,        # Fall risk
        "noise_masking": 0.7,       # Can't hear threats
        "visibility_reduction": 0.4, # Spray obscures
        "injury_on_fall": 0.4,      # Rocks below
    },
)

# In the waterfall zone:
# - You can't hear footsteps approaching
# - But approaching threats CAN hear you
# - Reaction windows are shortened (can't hear warnings)
# - Escape affordances reduced (slippery + pull)
```

---

## 10. Injury → Reaction Degradation

**Injuries modify reaction capability.**

### Injury Effects on Reaction

```python
INJURY_REACTION_EFFECTS = {
    "leg_injured": {
        "movement_speed": -0.4,
        "reaction_latency": +0.1,
        "balance": -0.3,
        "escape_options": ["run", "flee"],  # These are penalized
    },
    "arm_injured": {
        "manipulation_speed": -0.4,
        "reaction_latency": +0.05,
        "attack_options": ["shoot", "punch"],  # Penalized
    },
    "head_injured": {
        "reaction_latency": +0.3,
        "awareness": -0.3,
        "stt_error_rate": +0.2,  # Speech recognition worse
    },
    "torso_injured": {
        "breath_commands": +0.2,   # Delayed
        "stamina_drain": +0.5,
        "shout_volume": -0.3,      # Quieter voice
    },
    "bleeding": {
        "time_pressure": True,     # Every action costs more time
        "reaction_latency": +0.1,
        "degradation_rate": 0.01,  # Gets worse
    },
    "fear": {
        "reaction_latency": +0.3,
        "intent_clarity": -0.3,    # LLM misparsing risk
        "voice_tremor": +0.2,      # STT error rate
    },
}


class InjuryReactionSystem:
    """Apply injury effects to reaction timing."""

    def apply_injuries(
        self,
        player: Player,
        base_reaction: float,
    ) -> float:
        """Calculate reaction time with injury penalties."""

        total_penalty = 0.0

        for injury in player.injuries:
            effects = INJURY_REACTION_EFFECTS.get(injury.type, {})
            latency_mod = effects.get("reaction_latency", 0.0)

            # Scale by severity
            total_penalty += latency_mod * injury.severity

        return base_reaction + total_penalty

    def apply_stt_degradation(
        self,
        player: Player,
        transcript: str,
    ) -> tuple[str, float]:
        """Injuries can cause STT errors."""

        error_rate = 0.0

        for injury in player.injuries:
            effects = INJURY_REACTION_EFFECTS.get(injury.type, {})
            error_rate += effects.get("stt_error_rate", 0.0) * injury.severity

        # Apply potential misinterpretation
        if random() < error_rate:
            # Fuzzy match to wrong command
            transcript = self._corrupt_transcript(transcript)

        return transcript, error_rate
```

### Example Degradation

```
PLAYER STATE: Head injury (severity 0.6), fear (severity 0.8)

Reaction time calculation:
  Base:           0.30s
  Head injury:    +0.18s  (0.3 × 0.6)
  Fear:           +0.24s  (0.3 × 0.8)
  Total:          0.72s

STT error rate:
  Head injury:    +0.12   (0.2 × 0.6)
  Fear tremor:    +0.16   (0.2 × 0.8)
  Total:          28% error chance

Player says: "Run away"
  28% chance → "Run a way" → parsed as confused intent
  Result: Delayed or wrong action

This is brutal. This is correct.
```

---

## 11. Fear Feedback Loop

**Fear is not cosmetic. It has mechanical effects.**

### Fear System

```python
class FearSystem:
    """Fear affects player capability and perception."""

    def calculate_fear(
        self,
        player: Player,
        threats: list[Threat],
        environment: Environment,
    ) -> float:
        """Calculate current fear level."""

        base_fear = 0.0

        # Threat proximity generates fear
        for threat in threats:
            distance = self._distance(player.position, threat.position)
            proximity_fear = self.proximity.get_effects(
                self.proximity.get_band(distance)
            ).fear_generation
            base_fear = max(base_fear, proximity_fear)

        # Multiple threats compound
        if len(threats) > 1:
            base_fear *= 1.0 + (len(threats) - 1) * 0.3

        # Environmental fear
        if environment.is_dark:
            base_fear += 0.1
        if environment.is_isolated:
            base_fear += 0.1

        # Injury increases fear
        if player.is_bleeding:
            base_fear += 0.2

        # Previous trauma (memory)
        if player.has_trauma_at(player.position):
            base_fear += 0.15

        return min(1.0, base_fear)

    def apply_fear_effects(
        self,
        player: Player,
        fear_level: float,
    ) -> FearEffects:
        """Apply fear to player state and rendering."""

        effects = FearEffects()

        if fear_level > 0.3:
            # Hesitation begins
            effects.reaction_penalty = fear_level * 0.3
            effects.intent_narrowing = True  # Fewer options considered

        if fear_level > 0.5:
            # Screen effects
            effects.screen_shake = fear_level * 0.5
            effects.audio_distortion = fear_level * 0.3

        if fear_level > 0.7:
            # Affordance surfacing slows
            effects.affordance_delay = 0.3  # 300ms delay showing options
            effects.misinterpretation_risk = 0.2

        if fear_level > 0.9:
            # Panic
            effects.freeze_chance = 0.2  # May not respond at all
            effects.random_action_chance = 0.1  # May do wrong thing

        return effects
```

### Fear Rendering

```python
class FearRenderer:
    """Render fear state through ASCII effects."""

    def apply_fear_effects(self, frame: Frame, fear_level: float) -> Frame:
        """Apply visual fear effects."""

        if fear_level > 0.3:
            # Subtle vignette
            frame = self._apply_edge_darkening(frame, intensity=fear_level * 0.3)

        if fear_level > 0.5:
            # Screen shake
            frame = self._apply_shake(frame, intensity=fear_level * 0.4)
            # Characters may render wrong
            frame = self._apply_char_corruption(frame, rate=fear_level * 0.1)

        if fear_level > 0.7:
            # Audio distortion (if supported)
            self._apply_audio_distortion(fear_level * 0.5)
            # Slower affordance reveal
            frame = self._delay_hotspot_render(frame, delay=0.3)

        if fear_level > 0.9:
            # Tunnel vision
            frame = self._apply_tunnel_vision(frame, intensity=0.6)
            # Heartbeat pulse
            frame = self._apply_pulse(frame, rate=2.0)

        return frame
```

---

## 12. Example Scene (End-to-End)

```
SCENE: Dark alley at night

1. INITIAL STATE
   ┌────────────────────────────────────────┐
   │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓      │
   │    ▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓       │
   │    ▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓       │
   │    ▓░░░░░░░@░░░░░░░░░░░░░░░░░░▓       │
   │    ▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓       │
   │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓      │
   └────────────────────────────────────────┘
   Audio: Distant footsteps (FAR band)
   Fear: 0.1

2. THREAT ENTERS MEDIUM BAND
   ┌────────────────────────────────────────┐
   │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▒  │
   │    ▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓    ▒  │
   │    ▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓ →  ▒  │
   │    ▓░░░░░░░@░░░░░░░░░░░░░░░░░░▓    ▒  │
   │    ▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓    ▒  │
   │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▒  │
   └────────────────────────────────────────┘
   Audio: Footsteps accelerate (*bell*)
   Visual: Right edge jitter
   Fear: 0.3

3. THREAT ENTERS NEAR BAND - NPC SHOUTS
   ┌────────────────────────────────────────┐
   │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
   │    ▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓  ▓▓▓▓▓│
   │    ▓░░░░░░░░░░░░░░░░░░░░░☻░░░░▓  ▓▓▓▓▓│
   │    ▓░░░░░░░@░░░░░░░░░░░░░░░░░░▓  ▓▓▓▓▓│
   │    ▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓  ▓▓▓▓▓│
   │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
   └────────────────────────────────────────┘
   NPC: "Hey! Don't move!"
   Escalation: CHALLENGE (2.0s window)
   Fear: 0.5

4. PLAYER SAYS "RUN BEHIND DUMPSTER"
   Input timestamp: 0.0s
   STT processing: 0.3s
   Intent: flee + cover
   Player reaction: 0.65s (fear penalty)
   Threat window: 2.0s
   Ratio: 0.325 → EARLY

5. THREAT ENTERS IMMINENT - PLAYER MOVING
   ┌────────────────────────────────────────┐
   │▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
   │▒▒▒▓░░░░░░░░░░░░░░░░░░░░░░░☻░░▓▓▓▓▓▓▓▓▓│
   │▒▒▒▓░░░░░░░░░░░░░░░░░░█░░░░░░░▓▓▓▓▓▓▓▓▓│
   │▒▒▒▓░░░░@←░░░░░░░░░░░░█░░░░░░░▓▓▓▓▓▓▓▓▓│
   │▒▒▒▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓▓▓▓▓▓▓▓│
   │▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
   └────────────────────────────────────────┘
   Screen: Flicker + shake
   Player: Moving toward dumpster
   Threat: Advancing, Stage 2

6. RESOLUTION - PARTIAL SUCCESS
   Player clips corner of dumpster
   Shoulder injury: severity 0.3
   Position: Behind cover
   Threat: Lost line of sight

   ┌────────────────────────────────────────┐
   │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓      │
   │    ▓░░░░░░░░░░░░░░░░░░░░░░○░░░▓       │
   │    ▓░░░░░@░░░░░░░░░░░░█░░░░░░░▓       │
   │    ▓░░░░░░░░░░░░░░░░░░█░░░░░░░▓       │
   │    ▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓       │
   │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓      │
   └────────────────────────────────────────┘
   Narration: "You dive behind the dumpster.
               Your shoulder clips the corner—
               pain flares, but you're hidden."

7. RUMOR SEEDED
   Event logged: "Player barely escaped gunman"
   Witness: Gunman (hostile)
   Memory formed: "That detective is quick"
   Rumor potential: "He barely got away"
```

**No cutscene. No combat menu. Just consequence.**

---

## 13. Why This System Works

| Problem | Solution |
|---------|----------|
| Turn-based feels fake | Continuous time |
| Parser death | LLM intent resolution |
| Voice feels gimmicky | STT has real timing stakes |
| Combat is separate | Threats are part of world |
| Difficulty is arbitrary | Injury degrades capability |
| Fear is cosmetic | Fear has mechanical effects |

---

## 14. Implementation Order

### Phase 1: Single Threat

```
- One threat object
- Linear distance calculation
- Reaction window comparison
- STT interrupt processing
- Basic success/failure
```

### Phase 2: Awareness & Rendering

```
- Awareness calculation
- Line of sight
- Proximity bands
- ASCII proximity effects
- Audio cues
```

### Phase 3: Escalation & Environment

```
- Escalation ladder
- Stage transitions
- Environmental threats
- Multiple threat interaction
```

### Phase 4: Degradation & Fear

```
- Injury → reaction effects
- Fear accumulation
- Fear rendering
- STT degradation
```

---

## 15. What This Unlocks Next

This system directly enables:

- **Sound propagation** (threats hear you)
- **Line-of-sight cones** (visibility matters)
- **Crowd simulation** (NPCs as obstacles and cover)
- **Chase dynamics** (pursuit and evasion)
- **Stealth gameplay** (emergent from awareness)

---

*End of Threat Proximity & Reaction Timing System*
