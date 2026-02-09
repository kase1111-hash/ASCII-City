# ShadowEngine — Design Philosophy & Emergent Systems

> **Version**: 1.0.0
> **Status**: Core Design Document
> **Inspiration**: Dwarf Fortress principles, evolved for real-time + voice

---

## 1. World First, Player Second

**The world does not generate for intent. Player intent collides with reality.**

### Core Rules

| Principle | Implementation |
|-----------|----------------|
| The world exists before the player acts | Simulation runs independent of input |
| Death is valid and expected output | Engine never prevents failure |
| The world never asks "is this fun?" | It asks "is this plausible?" |
| Systems keep running | No pause-to-think safety net |

### What This Means in Practice

```python
class WorldFirstPrinciple:
    """The world doesn't care about the player."""

    def should_world_accommodate_player(self, action: str) -> bool:
        """Always returns False. World doesn't bend."""
        return False

    def resolve_collision(
        self,
        player_intent: Intent,
        world_state: WorldState,
    ) -> Resolution:
        """Intent meets reality. Reality wins."""

        # Player wants to go behind waterfall
        # World has: rocks, current, cold, darkness

        # World doesn't ask: "Will this be fun?"
        # World asks: "What would happen?"

        return self.physics.resolve(player_intent, world_state)
```

### The Engine Never Corrects

```python
# WRONG (protective engine)
def resolve_waterfall(player):
    if is_too_dangerous():
        return "You sense danger and hesitate."  # ← Engine protecting player

# RIGHT (indifferent engine)
def resolve_waterfall(player):
    danger = calculate_danger()  # 0.8
    player_capability = player.get_capability("balance")  # 0.4
    return physics.resolve(danger, player_capability)  # Player slips
```

**Death is output, not bug.**

---

## 2. Capability Damage, Not Health Damage

**Injuries reduce what you can do, not a number.**

### Traditional HP System (Wrong)

```
Player HP: 100 → 70 → 40 → 10 → 0 (dead)
```

Nothing changes until 0. Player is fully capable at 1 HP.

### Capability Damage System (Right)

```
Leg injured    → movement affordance -0.4
Arm injured    → manipulation affordance -0.5
Bleeding       → time pressure (actions have deadline)
Fear           → reaction delay +0.3s
Exhaustion     → all physical affordances -0.2
```

### Implementation

```python
@dataclass
class Injury:
    """An injury that affects capabilities, not HP."""

    location: str                   # "leg", "arm", "torso", "head"
    severity: float                 # 0.0 to 1.0

    # Capability reductions (the actual game effect)
    affordance_modifiers: dict[str, float]

    # Progression
    bleeding: bool
    bleed_rate: float               # Capability loss per second
    infection_risk: float


class CapabilityDamageSystem:
    """Injuries modify what player can do."""

    def apply_injury(self, player: Player, injury: Injury) -> None:
        """Apply injury by modifying player's affordance access."""

        for affordance_id, modifier in injury.affordance_modifiers.items():
            player.affordance_modifiers[affordance_id] += modifier

    def get_effective_affordance(
        self,
        player: Player,
        affordance_id: str,
        base_intensity: float,
    ) -> float:
        """Get affordance intensity after injury modifiers."""

        modifier = player.affordance_modifiers.get(affordance_id, 0.0)
        return max(0.0, base_intensity + modifier)


# Example injuries and their effects
INJURY_EFFECTS = {
    "leg_injured": {
        "location": "leg",
        "affordance_modifiers": {
            "traversable": -0.4,     # Slower movement
            "climbable": -0.6,       # Much harder to climb
            "forced_motion": +0.2,   # Easier to push over
        },
    },
    "arm_injured": {
        "location": "arm",
        "affordance_modifiers": {
            "manipulates": -0.5,     # Hard to use items
            "climbable": -0.3,       # Harder to climb
            "threatens": -0.2,       # Less intimidating
        },
    },
    "concussion": {
        "location": "head",
        "affordance_modifiers": {
            "observes": -0.4,        # Blurred vision
            "reaction_time": +0.3,   # Slower reactions (inverted)
        },
    },
    "fear": {
        "location": "psychological",
        "affordance_modifiers": {
            "reaction_delay": +0.3,  # 300ms slower
            "threatens": -0.4,       # Less intimidating
            "conceals": -0.2,        # Shaking gives you away
        },
    },
}
```

### Why This Fits STT

```
Player is bleeding:
  → Every second matters
  → Delayed voice command = worse outcome
  → "run away" at 2s works
  → "run away" at 4s = you stumble

Player is scared:
  → Voice commands have 300ms processing delay added
  → Hesitation is literal mechanical penalty
```

---

## 3. Event Journaling (Legends Mode Concept)

**Every meaningful event is logged. History emerges after the fact.**

### The Journal

```python
@dataclass
class WorldEvent:
    """A significant thing that happened."""

    id: str
    timestamp: float
    location: tuple[int, int]

    # What happened
    event_type: str                 # "death", "violence", "discovery", "escape"
    description: str                # Generated by LLM post-hoc

    # Who was involved
    actors: list[str]
    witnesses: list[str]

    # Consequences
    tile_states_changed: list[str]  # ["bloodied", "cracked"]
    affordances_revealed: list[str]
    npcs_affected: list[str]

    # Discoverability
    physical_evidence: bool         # Left traces?
    rumor_spread: float             # How much NPCs talk about it


class EventJournal:
    """The world's memory of what happened."""

    events: list[WorldEvent]

    def record(self, event: WorldEvent) -> None:
        """Log an event to world history."""
        self.events.append(event)

        # Events may spread as rumors
        if event.rumor_spread > 0.3:
            self._propagate_rumor(event)

    def query_location(self, location: tuple[int, int]) -> list[WorldEvent]:
        """What happened at this location?"""
        return [e for e in self.events if e.location == location]

    def query_actor(self, actor_id: str) -> list[WorldEvent]:
        """What has this actor been involved in?"""
        return [e for e in self.events if actor_id in e.actors]

    def get_recent(self, hours: float = 24) -> list[WorldEvent]:
        """What happened recently?"""
        cutoff = self.current_time - (hours * 3600)
        return [e for e in self.events if e.timestamp > cutoff]
```

### Example Event Chain

```python
# Player goes behind waterfall, slips, survives

event_1 = WorldEvent(
    event_type="injury",
    location=(45, 23),
    description="A traveler fell on the rocks behind the falls.",
    actors=["player"],
    tile_states_changed=["bloodied"],
    physical_evidence=True,
    rumor_spread=0.0,  # No witnesses
)

# Later, player is found injured in town

event_2 = WorldEvent(
    event_type="social",
    location=(100, 50),
    description="An injured stranger stumbled into the bar.",
    actors=["player", "bartender"],
    witnesses=["patron_1", "patron_2"],
    rumor_spread=0.6,  # People talk
)

# Now NPCs know about the waterfall

# When player returns to waterfall:
# LLM can reference: "The rocks here look worn. Stained."
# Because: tile.state includes "bloodied"
# And: event_journal has record of what happened
```

### No Authored Lore. Just Consequences.

```python
class DiegeticHistoryAccess:
    """Surface history through the world, not menus."""

    def get_history_hints(
        self,
        player: Player,
        location: tuple[int, int],
        journal: EventJournal,
    ) -> list[str]:
        """What hints about history exist here?"""

        hints = []
        events = journal.query_location(location)

        for event in events:
            # Physical evidence
            if event.physical_evidence:
                hints.append(self._physical_hint(event))

            # Player was there
            if "player" in event.actors:
                hints.append(self._personal_memory(event))

            # Player heard rumors
            if self._player_heard_rumor(player, event):
                hints.append(self._rumor_hint(event))

        return hints

    def _physical_hint(self, event: WorldEvent) -> str:
        """Hint from physical traces."""
        HINTS = {
            "death": "Something bad happened here. You can tell.",
            "violence": "Marks on the ground. Old, but unmistakable.",
            "fire": "Char marks. The air still smells of smoke.",
        }
        return HINTS.get(event.event_type, "This place has history.")

    def _rumor_hint(self, event: WorldEvent) -> str:
        """Hint from overheard information."""
        return f"You've heard stories about this place."
```

---

## 4. Procedural Threat Archetypes

**Threats defined by affordance profiles, not lore.**

### No Monster Manual

Traditional approach:
```
Thug:
  - 50 HP
  - Attacks for 10 damage
  - Drops $20
  - Behavior: "aggressive"
```

Affordance approach:
```python
thug_profile = ThreatProfile(
    affordances={
        "approaches": 0.8,       # How fast it closes distance
        "threatens": 0.9,        # How intimidating
        "injures": 0.7,          # Damage capability
        "pursues": 0.6,          # Will it chase?
        "negotiates": 0.2,       # Can you talk it down?
        "reveals_in_dark": 0.4,  # Visible at night?
    },
)
```

### Threat Generation

```python
@dataclass
class ThreatProfile:
    """A threat defined purely by affordances."""

    # Movement behavior
    approaches: float           # 0.0 = static, 1.0 = rushes
    pursues: float              # 0.0 = gives up, 1.0 = relentless
    patrols: float              # 0.0 = stationary, 1.0 = covers area

    # Danger level
    threatens: float            # Intimidation factor
    injures: float              # Damage capability
    kills: float                # Lethality (usually low)

    # Perception
    detects_sound: float        # Hearing range
    detects_motion: float       # Vision range
    reveals_in_dark: float      # Visible at night?

    # Social
    negotiates: float           # Can be talked to?
    surrenders: float           # Will give up?
    calls_backup: float         # Summons others?


class ThreatGenerator:
    """Generate threats from affordance profiles."""

    ARCHETYPES = {
        "stalker": ThreatProfile(
            approaches=0.6,
            pursues=0.9,
            threatens=0.7,
            injures=0.5,
            detects_motion=0.8,
            reveals_in_dark=0.2,  # Hard to see
            negotiates=0.0,
        ),
        "enforcer": ThreatProfile(
            approaches=0.9,
            pursues=0.4,
            threatens=0.8,
            injures=0.8,
            detects_sound=0.6,
            reveals_in_dark=0.8,
            negotiates=0.3,
        ),
        "watcher": ThreatProfile(
            approaches=0.2,
            pursues=0.1,
            threatens=0.4,
            injures=0.2,
            detects_motion=0.9,
            calls_backup=0.9,
        ),
    }

    def generate(self, archetype: str, variance: float = 0.1) -> ThreatProfile:
        """Generate a threat with some random variance."""
        base = self.ARCHETYPES[archetype]
        return self._apply_variance(base, variance)
```

### No Lore Required

```
ASCII + Sound + Pressure = Fear

The player doesn't need to know:
  "This is a Level 3 Enforcer with 80 HP"

The player feels:
  - Heavy footsteps (sound propagation)
  - Getting closer (threat.approaches = 0.9)
  - Screen flickers (high threat.threatens)
  - Time pressure (reaction window shrinking)
```

---

## 5. The World Is the UI

**The screen becomes a threat radar, not decoration.**

### Visual Affordance Communication

| Affordance | Visual Effect | What Player Learns |
|------------|---------------|-------------------|
| High `danger` | Flicker, contrast spike | Threat nearby |
| High `conceals` | Dense shadow overlay | Can hide here |
| High `slippery` | Shimmer/jitter | Unstable footing |
| High `unstable` | Subtle shake | May collapse |
| Threat proximity | Pulse from direction | Enemy location |
| Low visibility | Fog/blur overlay | Can't see far |

### Implementation

```python
class WorldAsUI:
    """Render the world to communicate state, not just display it."""

    def get_tile_effects(self, tile: TileBase, context: Context) -> list[Effect]:
        """Visual effects based on affordances and threats."""

        effects = []
        affordances = self.compute_affordances(tile)

        # Danger visualization
        threat_level = context.get_threat_level_at(tile.position)
        if threat_level > 0.5:
            effects.append(FlickerEffect(
                intensity=threat_level,
                rate=threat_level * 10,  # Faster = more danger
            ))

        # Concealment visualization
        concealment = affordances.get("conceals", 0)
        if concealment > 0.3:
            effects.append(ShadowOverlay(
                density=concealment,
                pattern="noise",
            ))

        # Instability visualization
        slippery = affordances.get("slippery", 0)
        if slippery > 0.5:
            effects.append(JitterEffect(
                intensity=slippery,
                direction="horizontal",
            ))

        # Threat direction pulse
        threat_direction = context.get_threat_direction(tile.position)
        if threat_direction:
            effects.append(DirectionalPulse(
                direction=threat_direction,
                intensity=threat_level,
                color="danger",
            ))

        return effects

    def render_threat_proximity(self, viewport: Viewport, threats: list[Threat]) -> None:
        """Pulse the screen edges based on threat proximity."""

        for threat in threats:
            direction = self._get_direction_to(threat.position)
            distance = self._get_distance_to(threat.position)

            # Closer = stronger pulse
            intensity = 1.0 - (distance / self.MAX_THREAT_DISTANCE)

            # Apply edge pulse
            self._pulse_edge(direction, intensity)
```

### The Screen Teaches the Player

```
Learning threat proximity:
  Player sees: Edge of screen pulsing red ←
  Player learns: Danger is to the left

Learning safe zones:
  Player sees: Dense shadow overlay on alley
  Player learns: Can hide in alleys

Learning danger zones:
  Player sees: Tiles shaking slightly
  Player learns: Floor unstable here

No tutorial needed.
The world communicates directly.
```

---

## 6. Event Pressure Clock

**Every affordance has a time cost. Hesitation degrades outcomes.**

### Time Costs

```python
@dataclass
class AffordanceTimeCost:
    """How long using an affordance takes."""

    affordance_id: str
    base_time: float                # Seconds

    # Modifiers
    injury_multiplier: dict[str, float]  # Injuries slow you down
    terrain_multiplier: float       # Terrain difficulty
    urgency_bonus: float            # Panic speeds things up (but adds risk)


TIME_COSTS = {
    "traversable": AffordanceTimeCost(
        affordance_id="traversable",
        base_time=0.5,  # Half second per tile
        injury_multiplier={"leg_injured": 1.5},
    ),
    "conceals": AffordanceTimeCost(
        affordance_id="conceals",
        base_time=1.0,  # 1 second to hide
        injury_multiplier={"leg_injured": 1.3},
    ),
    "climbable": AffordanceTimeCost(
        affordance_id="climbable",
        base_time=2.0,  # 2 seconds to climb
        injury_multiplier={"leg_injured": 2.0, "arm_injured": 1.8},
    ),
}
```

### Hesitation Degrades Outcomes

```python
class HesitationPenalty:
    """Late actions are worse actions."""

    def calculate_effectiveness(
        self,
        action: Action,
        reaction_time: float,
        optimal_time: float,
    ) -> float:
        """How effective is an action based on timing?"""

        if reaction_time <= optimal_time:
            return 1.0  # Full effectiveness

        # Every 0.5s delay reduces effectiveness by 20%
        delay = reaction_time - optimal_time
        penalty = delay / 0.5 * 0.2

        return max(0.2, 1.0 - penalty)  # Minimum 20% effectiveness

    def apply_hesitation(
        self,
        action: Action,
        effectiveness: float,
    ) -> ActionResult:
        """Apply hesitation penalty to action outcome."""

        if effectiveness >= 0.9:
            return ActionResult(
                success=True,
                message="You react instantly.",
            )
        elif effectiveness >= 0.6:
            return ActionResult(
                success=True,
                partial=True,
                message="You react, but not quite fast enough.",
            )
        elif effectiveness >= 0.3:
            return ActionResult(
                success=True,
                partial=True,
                cost_increased=True,
                message="You stumble, but make it.",
            )
        else:
            return ActionResult(
                success=False,
                message="Too slow.",
            )
```

### STT + Hesitation

```python
class VoiceTimingSystem:
    """Voice commands respect timing."""

    def process_voice_command(
        self,
        command: VoiceCommand,
        threat: Threat,
        reaction_window: ReactionWindow,
    ) -> ActionResult:
        """Process voice command with timing considerations."""

        # Calculate when command was given
        elapsed = reaction_window.elapsed
        optimal = reaction_window.duration * 0.3  # First 30% is optimal

        effectiveness = self.hesitation.calculate_effectiveness(
            action=command.to_action(),
            reaction_time=elapsed,
            optimal_time=optimal,
        )

        # "Run away" at 2s: effectiveness = 0.9
        # "Run away" at 4s: effectiveness = 0.5

        result = self.hesitation.apply_hesitation(
            action=command.to_action(),
            effectiveness=effectiveness,
        )

        # Late "run away" = you run but take a hit
        if result.partial:
            damage = threat.injures * (1.0 - effectiveness)
            self.player.apply_damage(damage)
            result.message = "You run, but not before he lands a hit."

        return result
```

---

## 7. Diegetic Memory Access

**Surface history through the world, not menus.**

### No UI Popups

Traditional approach:
```
[Quest Log]
- Discovered waterfall cave
- Heard rumor about missing person
- Found bloodstain in alley
```

Diegetic approach:
```
[Player examines tile]
LLM: "The rocks here are stained. You've seen this before.
      In the bar, someone mentioned a traveler who never came back."
```

### Sources of Diegetic Information

```python
class DiegeticInformationSources:
    """Ways the world tells you things."""

    SOURCES = {
        "physical_evidence": {
            "examples": ["bloodstains", "bullet holes", "footprints"],
            "reveals": "Something happened here",
            "persistence": "permanent until cleaned",
        },
        "environmental_hints": {
            "examples": ["smell", "temperature", "sound"],
            "reveals": "Current conditions, recent events",
            "persistence": "temporary",
        },
        "npc_dialogue": {
            "examples": ["rumors", "warnings", "lies"],
            "reveals": "Events, opinions, misinformation",
            "persistence": "NPC memory",
        },
        "player_memory": {
            "examples": ["recognition", "flashback", "déjà vu"],
            "reveals": "Player has been here/seen this before",
            "persistence": "player journal",
        },
        "found_objects": {
            "examples": ["notes", "newspapers", "photographs"],
            "reveals": "Backstory, clues, world-building",
            "persistence": "inventory",
        },
    }

    def get_available_information(
        self,
        player: Player,
        location: tuple[int, int],
        world: WorldGrid,
        journal: EventJournal,
    ) -> list[Information]:
        """What information is available at this location?"""

        info = []

        # Physical evidence on tile
        tile = world.get_tile(*location)
        for state in tile.state:
            if state in ["bloodied", "burned", "cracked"]:
                info.append(Information(
                    source="physical_evidence",
                    content=self._describe_evidence(state, tile),
                    reliability=1.0,  # Physical evidence doesn't lie
                ))

        # Player memory
        if location in player.visited_locations:
            events = journal.query_location(location)
            for event in events:
                if "player" in event.actors:
                    info.append(Information(
                        source="player_memory",
                        content=f"You remember what happened here.",
                        reliability=1.0,
                    ))

        # NPC rumors (if player heard them)
        rumors = self._get_relevant_rumors(player, location)
        for rumor in rumors:
            info.append(Information(
                source="npc_dialogue",
                content=rumor.content,
                reliability=rumor.reliability,  # Rumors may be wrong
            ))

        return info
```

### LLM Surfaces Memory In-World

```python
class NarrativeMemorySurfacing:
    """LLM weaves history into narration."""

    async def generate_location_description(
        self,
        location: tuple[int, int],
        player: Player,
        world: WorldGrid,
        journal: EventJournal,
    ) -> str:
        """Generate description that includes relevant history."""

        # Gather information
        info = self.diegetic.get_available_information(
            player, location, world, journal
        )

        # Build context for LLM
        context = {
            "location": self._describe_location(location, world),
            "available_information": [i.to_dict() for i in info],
            "player_state": player.get_state_summary(),
            "player_knowledge": player.get_known_facts(),
        }

        # LLM generates description that weaves in history
        prompt = """
        Describe this location. Weave in available information naturally.
        Don't dump exposition. Let details emerge.

        Location: {location}
        Information available: {available_information}
        Player knows: {player_knowledge}

        Write 2-3 sentences. Present tense. Noir style.
        """

        return await self.llm.generate(prompt.format(**context))


# Example output:
# "The rocks behind the falls are slick with more than water.
#  You've heard stories about this place. Someone didn't come back."
```

---

## 8. "Losing Is Fun" Design Constraint

**Failure creates stories. The engine doesn't protect you.**

### Design Rules

```python
class LosingIsFunRules:
    """Rules that make failure interesting."""

    RULES = [
        # 1. Failure creates narrative
        Rule(
            "Failure creates stories",
            implementation="Every death/failure is logged with context",
            example="Died behind waterfall → story about the rocks claiming another",
        ),

        # 2. No invisible walls
        Rule(
            "No invisible protection",
            implementation="If physics says you die, you die",
            example="Waterfall is dangerous → you can die there",
        ),

        # 3. Warnings exist, but are diegetic
        Rule(
            "Warnings are in-world",
            implementation="Scratches on rocks, NPC warnings, player memory",
            example="'The old man said to be careful near the falls'",
        ),

        # 4. Death has meaning
        Rule(
            "Death matters",
            implementation="World continues, remembers player's fate",
            example="NPC mentions 'that detective who went missing'",
        ),

        # 5. Near-misses are common
        Rule(
            "Injury > death",
            implementation="Capability damage usually precedes death",
            example="Leg injury from rocks → can still escape → or not",
        ),
    ]
```

### Failure Logging

```python
class FailureJournal:
    """Log failures as narrative seeds."""

    def log_death(
        self,
        player: Player,
        cause: str,
        location: tuple[int, int],
        context: Context,
    ) -> DeathRecord:
        """Record a player death with full context."""

        record = DeathRecord(
            player_name=player.name,
            cause=cause,
            location=location,
            timestamp=context.current_time,

            # What led to this
            recent_actions=player.action_history[-10:],
            injuries_at_death=player.injuries,
            was_fleeing=player.is_fleeing,
            was_hiding=player.is_hidden,

            # World state
            weather=context.weather,
            time_of_day=context.time_of_day,
            threats_present=[t.id for t in context.active_threats],

            # Narrative seed
            story_seed=self._generate_story_seed(player, cause, context),
        )

        # This death becomes part of world history
        self.journal.record(WorldEvent(
            event_type="death",
            location=location,
            description=record.story_seed,
            physical_evidence=True,  # Body, blood, etc.
            rumor_spread=0.8,  # People will talk
        ))

        return record

    def _generate_story_seed(
        self,
        player: Player,
        cause: str,
        context: Context,
    ) -> str:
        """Generate a narrative seed from death circumstances."""

        # "A detective went behind the falls on a rainy night.
        #  They never came back. The rocks claimed another."

        return f"A {player.profession} died {cause} during {context.time_of_day}."
```

---

## 9. Summary: What Dwarf Fortress Validates

| DF Principle | ShadowEngine Implementation |
|--------------|----------------------------|
| World first | Simulation runs independent of player |
| Legends Mode | Event journal with diegetic access |
| Body-part damage | Capability damage, not HP |
| Losing is fun | Death creates stories, isn't punished |
| Simulation > Content | Affordances create depth |
| Z-levels | Elevation metadata in 2D |
| Adventure mode | Real-time + voice fixes its friction |

### What ShadowEngine Adds Beyond DF

| Innovation | Why DF Couldn't Do It |
|------------|----------------------|
| Voice input (STT) | 2006 technology |
| LLM interpretation | AI didn't exist |
| Real-time reaction windows | DF is pausable |
| Hesitation mechanics | No time pressure |
| World-as-UI visualization | Terminal limitations |

---

## 10. Non-Negotiable Design Rules

Write these on the wall:

```
1. The world doesn't care about the player
2. Injuries reduce capability, not HP
3. Every meaningful event is logged
4. Death is output, not bug
5. The screen teaches without tutorials
6. Hesitation has mechanical cost
7. History surfaces through the world, not UI
8. Threats are affordance profiles, not stat blocks
```

---

*End of Design Philosophy*
