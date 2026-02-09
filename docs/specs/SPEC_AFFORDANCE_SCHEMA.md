# ShadowEngine — Affordance Schema

> **Version**: 1.0.0
> **Status**: Canonical Definition
> **Purpose**: Define the formal affordance system that replaces traditional parsers

---

## 0. Core Principle (Lock This In)

**Affordances describe what the world allows, not what the player can do.**

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Player Intent  │────▶│   Affordances   │────▶│   Simulation    │
│  (expression)   │     │   (possibility) │     │   (resolution)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

- The **player** expresses intent
- **Affordances** define possibility space
- **Simulation** resolves outcomes

**The LLM is only allowed to map intent → affordances.**
**It is forbidden from inventing mechanics or results.**

---

## 1. What an Affordance Is (Formal Definition)

> An affordance is a **latent interaction possibility** exposed by an entity **because of its nature**.

### Examples

| Entity | Affordances |
|--------|-------------|
| Water | flows, pushes, obscures, drowns |
| Rock | blocks, supports, injures |
| Darkness | conceals, disorients |
| Human | threatens, negotiates, flees |
| Door | blocks, connects, opens |
| Fire | damages, illuminates, spreads |

**Affordances exist even if the player never uses them.**

They are properties of the world, not player abilities.

---

## 2. Affordance Object Model

Each world entity exposes a set of **affordance descriptors**.

### 2.1 Base Schema

```json
{
  "affordance_id": "concealment",
  "category": "spatial",
  "source": "waterfall",
  "intensity": 0.8,
  "conditions": {
    "visibility": "< 0.5",
    "distance": "<= 1 tile"
  },
  "risks": ["injury", "noise"],
  "enables": ["hiding", "ambush"],
  "blocks": ["clear_sight", "ranged_accuracy"]
}
```

**This is data, not logic.**

### 2.2 Python Implementation

```python
@dataclass
class Affordance:
    """A single affordance exposed by an entity."""

    # Identity
    affordance_id: str              # Unique identifier
    category: AffordanceCategory    # See Section 3
    source: str                     # Entity that exposes this

    # Strength
    intensity: float                # 0.0 to 1.0
    variance: float = 0.0           # Random variation

    # Conditions (when this affordance is active)
    conditions: dict[str, str]      # "visibility": "< 0.5"

    # Consequences
    risks: list[str]                # What dangers this creates
    enables: list[str]              # What actions this permits
    blocks: list[str]               # What this prevents

    # Knowledge state (per-player)
    known: bool = False             # Player has used it
    suspected: bool = False         # Player might guess it
    revealed: bool = False          # Explicitly shown


class AffordanceCategory(Enum):
    SPATIAL = "spatial"
    MOVEMENT = "movement"
    SENSORY = "sensory"
    PHYSICAL_RISK = "physical_risk"
    SOCIAL = "social"
    TEMPORAL = "temporal"
```

---

## 3. Affordance Categories (Canonical Set)

**These are finite and stable. Do not add categories lightly.**

### A. Spatial Affordances

How things exist in space.

| Affordance | Description | Example |
|------------|-------------|---------|
| `supports` | Can bear weight | Floor, table, ledge |
| `blocks` | Prevents passage | Wall, door, crowd |
| `conceals` | Hides from view | Dumpster, shadow, fog |
| `funnels` | Constrains movement | Alley, corridor |
| `elevates` | Provides height advantage | Rooftop, stairs |
| `encloses` | Surrounds on multiple sides | Room, car |
| `exposes` | Leaves visible/vulnerable | Open plaza, spotlight |

```python
# Examples
alley_affordances = [
    Affordance(affordance_id="funnels", category=AffordanceCategory.SPATIAL,
               source="alley", intensity=0.9),
    Affordance(affordance_id="conceals", category=AffordanceCategory.SPATIAL,
               source="alley_shadow", intensity=0.6),
]

rooftop_affordances = [
    Affordance(affordance_id="elevates", category=AffordanceCategory.SPATIAL,
               source="rooftop", intensity=1.0, enables=["observe", "snipe"]),
    Affordance(affordance_id="exposes", category=AffordanceCategory.SPATIAL,
               source="rooftop", intensity=0.7),
]
```

### B. Movement Affordances

How entities can move through or around something.

| Affordance | Description | Example |
|------------|-------------|---------|
| `traversable` | Can be crossed | Path, shallow water |
| `slippery` | Reduces control | Ice, wet floor, blood |
| `climbable` | Can be ascended | Ladder, pipe, wall |
| `unstable` | May collapse/shift | Debris, rotten floor |
| `impeding` | Slows movement | Mud, crowd, furniture |
| `forced_motion` | Pushes in direction | Current, wind, crowd |

```python
# Waterfall movement affordances
waterfall_movement = [
    Affordance(affordance_id="traversable", intensity=0.4,
               risks=["injury", "knockdown"]),
    Affordance(affordance_id="forced_motion", intensity=0.6,
               conditions={"direction": "downstream"}),
    Affordance(affordance_id="slippery", intensity=0.8),
    Affordance(affordance_id="unstable", intensity=0.5),
]
```

### C. Sensory Affordances

How perception is affected.

| Affordance | Description | Example |
|------------|-------------|---------|
| `obscures_vision` | Reduces sight | Fog, smoke, darkness |
| `amplifies_sound` | Makes sounds louder | Empty room, metal floor |
| `deadens_sound` | Muffles sounds | Carpet, rain, waterfall |
| `emits_light` | Provides illumination | Lamp, fire, neon |
| `casts_shadow` | Creates dark areas | Building, tree |
| `distracts` | Draws attention | Noise, movement, light |

```python
# Sensory affordances for stealth gameplay
fog_sensory = [
    Affordance(affordance_id="obscures_vision", intensity=0.7,
               enables=["stealth", "escape"],
               blocks=["clear_sight", "ranged_accuracy"]),
]

waterfall_sensory = [
    Affordance(affordance_id="deadens_sound", intensity=0.8,
               enables=["silent_action", "secret_conversation"],
               blocks=["eavesdropping"]),
    Affordance(affordance_id="obscures_vision", intensity=0.6),
]
```

**This is crucial for stealth and panic decisions.**

### D. Physical Risk Affordances

Danger without binary death.

| Affordance | Description | Example |
|------------|-------------|---------|
| `injures` | Causes physical harm | Sharp rocks, fall |
| `fatigues` | Drains stamina | Cold, exertion |
| `disorients` | Causes confusion | Darkness, blow to head |
| `bleeds` | Causes ongoing damage | Cut, gunshot |
| `burns` | Heat damage | Fire, steam |
| `poisons` | Toxic damage | Gas, tainted water |

```python
# Risk affordances stack over time
sharp_rocks = [
    Affordance(affordance_id="injures", intensity=0.4,
               conditions={"contact": "true"},
               risks=["laceration", "fall"]),
    Affordance(affordance_id="bleeds", intensity=0.3,
               conditions={"injured": "true"}),
]
```

**These stack over time. Death is accumulation, not instant.**

### E. Social / Psychological Affordances

Only for sentient entities or environments.

| Affordance | Description | Example |
|------------|-------------|---------|
| `threatens` | Implies violence | Armed person, growling dog |
| `intimidates` | Creates fear | Size, reputation, position |
| `reassures` | Reduces anxiety | Ally, safe space |
| `provokes` | Encourages aggression | Insult, territory |
| `invites_trust` | Opens dialogue | Open posture, smile |
| `signals_authority` | Implies power | Uniform, badge, office |

```python
# A uniformed cop affords authority even before speaking
cop_social = [
    Affordance(affordance_id="signals_authority", intensity=0.8,
               source="uniform",
               enables=["command", "interrogate"],
               blocks=["casual_approach"]),
    Affordance(affordance_id="threatens", intensity=0.4,
               source="holstered_weapon"),
]

# A dark alley affords menace
alley_psychological = [
    Affordance(affordance_id="threatens", intensity=0.5,
               source="environment",
               conditions={"time": "night", "isolated": "true"}),
]
```

### F. Temporal Affordances

How time behaves here.

| Affordance | Description | Example |
|------------|-------------|---------|
| `delays` | Forces waiting | Lock, traffic |
| `accelerates` | Creates urgency | Timer, pursuit |
| `forces_wait` | Cannot rush | Elevator, train |
| `creates_deadline` | Time limit | Bomb, bleeding out |

```python
# Temporal pressure examples
subway_platform = [
    Affordance(affordance_id="forces_wait", intensity=0.9,
               source="train_schedule",
               conditions={"train_present": "false"}),
    Affordance(affordance_id="accelerates", intensity=0.7,
               source="approaching_threat",
               conditions={"pursued": "true"}),
]

rooftop_chase = [
    Affordance(affordance_id="accelerates", intensity=0.8,
               enables=["desperate_action"],
               risks=["reckless_choice"]),
]
```

---

## 4. Affordance Strength & Gradients

**Nothing is binary.**

Each affordance has:

| Property | Type | Description |
|----------|------|-------------|
| `intensity` | float (0.0-1.0) | How strong the affordance is |
| `variance` | float (0.0-0.5) | Random variation per check |

### Examples

| Condition | `obscures_vision` Intensity |
|-----------|----------------------------|
| Thin fog | 0.3 |
| Heavy fog | 0.9 |
| Light rain | 0.2 |
| Heavy rain | 0.6 |
| Pitch black | 1.0 |
| Dim streetlight | 0.4 |

### Why Gradients Matter

This allows:
- **Partial success**: "You mostly stay hidden..."
- **Risky actions**: "You can try, but..."
- **Unclear outcomes**: "You're not sure if they saw you."

```python
def resolve_affordance(affordance: Affordance, rng: SeededRNG) -> float:
    """Get effective intensity with variance."""
    base = affordance.intensity
    if affordance.variance > 0:
        delta = rng.random() * affordance.variance * 2 - affordance.variance
        return max(0.0, min(1.0, base + delta))
    return base
```

---

## 5. Affordance Discovery (Player Knowledge ≠ World Truth)

**Affordances exist even if the player doesn't know them.**

### Three Knowledge States

```python
@dataclass
class AffordanceKnowledge:
    """What the player knows about an affordance."""

    affordance_id: str
    source: str

    # Knowledge states (exactly one is primary)
    known: bool = False         # Player has used/experienced it
    suspected: bool = False     # Player might guess it exists
    revealed: bool = False      # Explicitly shown (tutorial, observation)

    # Evidence
    discovery_method: Optional[str] = None
    discovery_time: Optional[float] = None
```

### How This Creates Drama

| State | LLM Narration | Truth |
|-------|---------------|-------|
| `known=False, suspected=False` | (Not mentioned) | May exist |
| `known=False, suspected=True` | "You think you can fit behind the waterfall." | 60% chance |
| `known=True` | "The gap behind the falls—you've been there." | Certain |
| `revealed=True` | "The old man mentioned a cave behind the water." | Certain |

### Discovery Mechanics

```python
class AffordanceDiscovery:
    """How players learn about affordances."""

    def observe(self, player: Player, entity: Entity) -> list[AffordanceKnowledge]:
        """Player examines something—what do they learn?"""

        learned = []

        for aff in entity.affordances:
            # Obvious affordances are revealed
            if aff.intensity > 0.7:
                learned.append(AffordanceKnowledge(
                    affordance_id=aff.affordance_id,
                    source=entity.id,
                    revealed=True,
                    discovery_method="observation",
                ))
            # Moderate affordances become suspected
            elif aff.intensity > 0.3:
                learned.append(AffordanceKnowledge(
                    affordance_id=aff.affordance_id,
                    source=entity.id,
                    suspected=True,
                ))
            # Weak/hidden affordances require interaction

        return learned

    def experience(self, player: Player, affordance: Affordance) -> AffordanceKnowledge:
        """Player used an affordance—now they know."""

        return AffordanceKnowledge(
            affordance_id=affordance.affordance_id,
            source=affordance.source,
            known=True,
            discovery_method="experience",
            discovery_time=self.current_time,
        )
```

---

## 6. Intent → Affordance Resolution Pipeline

**This is the heart of the system.**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RESOLUTION PIPELINE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Step 1: PLAYER INTENT                                                   │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  "Go behind the waterfall"                                      │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                              │                                           │
│                              ▼                                           │
│  Step 2: LLM INTERPRETATION (STRICT)                                     │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  {                                                              │     │
│  │    "intent_type": "movement",                                   │     │
│  │    "target": "waterfall",                                       │     │
│  │    "modifiers": ["concealment", "escape"]                       │     │
│  │  }                                                              │     │
│  │                                                                 │     │
│  │  ⚠️  NO OUTCOMES. NO STORY. JUST STRUCTURE.                    │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                              │                                           │
│                              ▼                                           │
│  Step 3: AFFORDANCE MATCHING                                             │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  Engine queries waterfall entity:                               │     │
│  │  ├─ Does it expose `conceals`? → YES (0.9)                     │     │
│  │  ├─ Does it allow `traversable`? → PARTIAL (0.4)               │     │
│  │  ├─ What are `risks`? → [injury, slippery, forced_motion]      │     │
│  │  └─ Any `blocks`? → [clear_sight, ranged_accuracy]             │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                              │                                           │
│                              ▼                                           │
│  Step 4: SIMULATION RESOLUTION                                           │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  Physics + Stats + State decide:                                │     │
│  │  ├─ Is there space behind? → Generate (70% cave, 30% rocks)    │     │
│  │  ├─ Do you slip? → Roll vs slippery (0.8) → YES                │     │
│  │  ├─ How much damage? → injures (0.4) × fall = 12 HP            │     │
│  │  └─ How much time passes? → 4 seconds                          │     │
│  │                                                                 │     │
│  │  Result: {success: true, damage: 12, position: "behind",        │     │
│  │           discovered: "small_cave", time: 4}                    │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                              │                                           │
│                              ▼                                           │
│  Step 5: LLM NARRATION (LAST)                                            │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │  LLM describes what happened, CONSTRAINED TO FACTS:             │     │
│  │                                                                 │     │
│  │  "You force through the curtain of water. Your foot finds       │     │
│  │   nothing—stone meets shin, hard. But you're through. A cavity  │     │
│  │   opens behind the falls, dark and damp. No one followed."      │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Code Implementation

```python
class ResolutionPipeline:
    """The 5-step intent-to-outcome pipeline."""

    async def resolve(self, raw_input: str, context: WorldContext) -> Resolution:
        # Step 1: Raw input
        player_input = raw_input

        # Step 2: LLM Interpretation (STRICT)
        intent = await self.llm.interpret(
            input=player_input,
            context=context,
            rules=STRICT_INTERPRETATION_RULES,
        )
        # intent = {"intent_type": "movement", "target": "waterfall", ...}

        # Step 3: Affordance Matching
        target = self.world.get_entity(intent["target"])
        matched_affordances = self._match_affordances(
            intent=intent,
            entity=target,
        )
        # matched = [conceals(0.9), traversable(0.4)]

        # Step 4: Simulation Resolution
        outcome = self.simulator.resolve(
            intent=intent,
            affordances=matched_affordances,
            player=self.player,
            world=self.world,
        )
        # outcome = {success: true, damage: 12, position: "behind", ...}

        # Step 5: LLM Narration (constrained to outcome)
        narration = await self.llm.narrate(
            outcome=outcome,
            context=context,
            style=self.player.narrative_style,
        )

        return Resolution(
            intent=intent,
            affordances=matched_affordances,
            outcome=outcome,
            narration=narration,
        )

    def _match_affordances(
        self,
        intent: dict,
        entity: Entity,
    ) -> list[Affordance]:
        """Find affordances that match the player's intent."""

        intent_type = intent["intent_type"]
        modifiers = intent.get("modifiers", [])

        matched = []

        for aff in entity.affordances:
            # Movement intents look for traversable, climbable, etc.
            if intent_type == "movement":
                if aff.affordance_id in ["traversable", "climbable", "forced_motion"]:
                    matched.append(aff)
                if "concealment" in modifiers and aff.affordance_id == "conceals":
                    matched.append(aff)

            # Examine intents reveal affordances
            elif intent_type == "examine":
                matched.append(aff)  # Show all

            # Hide intents need concealment
            elif intent_type == "hide":
                if aff.affordance_id in ["conceals", "obscures_vision", "casts_shadow"]:
                    matched.append(aff)

            # Attack intents need access
            elif intent_type == "attack":
                if aff.affordance_id == "blocks":
                    matched.append(aff)  # Might block attack

        return matched
```

---

## 7. Why This Avoids Text-Game Failure

### Classic Failure

```
> go behind the waterfall
I don't understand "behind".
```

### ShadowEngine Rule

**If an affordance exists, something happens.**

Even if that something is:
- **Pain**: "The rocks tear your hands."
- **Loss**: "Your hat is gone, carried by the current."
- **Noise**: "The splash echoes. Someone heard."
- **Regret**: "You made it, but at what cost?"

```python
def ensure_outcome(intent: dict, affordances: list[Affordance]) -> Outcome:
    """Something always happens. No parser errors."""

    if not affordances:
        # No matching affordances—but still describe the attempt
        return Outcome(
            success=False,
            reason="nothing_to_interact",
            narration_hint="attempted_but_found_nothing",
        )

    # At least one affordance matched
    primary = affordances[0]

    if primary.intensity < 0.2:
        # Very weak affordance—marginal success
        return Outcome(
            success=True,
            partial=True,
            narration_hint="barely_managed",
        )

    # Normal resolution
    return Outcome(
        success=True,
        effects=primary.enables,
        risks=primary.risks,
    )
```

---

## 8. Voice Input (STT) Compatibility

Voice commands map perfectly to the affordance system.

| Spoken | Intent Type | Affordances Queried |
|--------|-------------|---------------------|
| "Run!" | `escape` | `traversable`, `funnels`, `impeding` |
| "Hide!" | `conceal` | `conceals`, `casts_shadow`, `obscures_vision` |
| "Duck!" | `evade` | `blocks`, `supports` (for cover) |
| "Get down!" | `posture` | `exposes`, `conceals` |
| "Shoot!" | `attack` | `blocks` (obstruction check) |
| "Stop!" | `command` | `signals_authority`, `threatens` |

**No grammar. No menus. Reaction speed matters.**

```python
class VoiceToAffordance:
    """Map voice commands directly to affordance queries."""

    VOICE_MAPPINGS = {
        "run": {
            "intent_type": "escape",
            "query_affordances": ["traversable", "funnels", "impeding"],
            "urgency": 1.0,
        },
        "hide": {
            "intent_type": "conceal",
            "query_affordances": ["conceals", "casts_shadow", "obscures_vision"],
            "urgency": 0.8,
        },
        "duck": {
            "intent_type": "evade",
            "query_affordances": ["blocks", "supports"],
            "urgency": 1.0,
        },
        "shoot": {
            "intent_type": "attack",
            "query_affordances": ["blocks"],  # Check for obstructions
            "urgency": 1.0,
        },
    }

    def map(self, voice_command: str) -> dict:
        """Convert voice to intent + affordance query."""
        return self.VOICE_MAPPINGS.get(
            voice_command.lower(),
            {"intent_type": "unknown", "query_affordances": [], "urgency": 0.5}
        )
```

---

## 9. Entity Examples (Fully Defined)

### Waterfall

```json
{
  "entity": "waterfall",
  "type": "terrain_feature",
  "affordances": [
    {
      "affordance_id": "conceals",
      "category": "spatial",
      "intensity": 0.9,
      "enables": ["hiding", "ambush", "secret_meeting"],
      "blocks": ["clear_sight", "ranged_accuracy"]
    },
    {
      "affordance_id": "obscures_vision",
      "category": "sensory",
      "intensity": 0.8
    },
    {
      "affordance_id": "deadens_sound",
      "category": "sensory",
      "intensity": 0.7,
      "enables": ["silent_action", "private_conversation"],
      "blocks": ["eavesdropping", "sound_detection"]
    },
    {
      "affordance_id": "forced_motion",
      "category": "movement",
      "intensity": 0.6,
      "conditions": {"in_water": "true"},
      "risks": ["knockdown", "swept_away"]
    },
    {
      "affordance_id": "slippery",
      "category": "movement",
      "intensity": 0.8,
      "risks": ["fall", "injury"]
    },
    {
      "affordance_id": "injures",
      "category": "physical_risk",
      "intensity": 0.4,
      "conditions": {"traversing": "true"}
    },
    {
      "affordance_id": "traversable",
      "category": "movement",
      "intensity": 0.4,
      "variance": 0.2,
      "conditions": {"strength": "> 0.3"}
    }
  ]
}
```

### Dark Alley

```json
{
  "entity": "dark_alley",
  "type": "location",
  "affordances": [
    {
      "affordance_id": "conceals",
      "category": "spatial",
      "intensity": 0.7
    },
    {
      "affordance_id": "funnels",
      "category": "spatial",
      "intensity": 0.9,
      "blocks": ["flank", "surround"]
    },
    {
      "affordance_id": "obscures_vision",
      "category": "sensory",
      "intensity": 0.6,
      "conditions": {"time": "night"}
    },
    {
      "affordance_id": "threatens",
      "category": "social",
      "intensity": 0.5,
      "conditions": {"time": "night", "isolated": "true"}
    },
    {
      "affordance_id": "amplifies_sound",
      "category": "sensory",
      "intensity": 0.4
    }
  ]
}
```

### Armed Thug

```json
{
  "entity": "armed_thug",
  "type": "npc",
  "affordances": [
    {
      "affordance_id": "threatens",
      "category": "social",
      "intensity": 0.8,
      "source": "visible_weapon"
    },
    {
      "affordance_id": "intimidates",
      "category": "social",
      "intensity": 0.6,
      "enables": ["demand", "extort"],
      "blocks": ["casual_approach"]
    },
    {
      "affordance_id": "injures",
      "category": "physical_risk",
      "intensity": 0.9,
      "conditions": {"hostile": "true", "in_range": "true"}
    },
    {
      "affordance_id": "blocks",
      "category": "spatial",
      "intensity": 0.7,
      "conditions": {"guarding": "true"}
    }
  ]
}
```

**No script. No special case. The world just *is*.**

---

## 10. Non-Negotiable Rules

Write these on the wall:

| Rule | Meaning |
|------|---------|
| **LLM never decides outcomes** | It interprets and narrates. Simulation resolves. |
| **Affordances are finite** | Use the canonical categories. Don't invent new ones. |
| **Danger accumulates** | No instant death. Stack injuries over time. |
| **The world doesn't explain itself** | Affordances exist; players discover them. |
| **Player intent is always respected** | Something always happens. Never "I don't understand." |

---

## What This Unlocks

| Capability | How Affordances Enable It |
|------------|---------------------------|
| **Infinite verbs without parsers** | Intent maps to affordances, not keywords |
| **Speech-driven panic actions** | Voice → intent → affordance in <100ms |
| **Consistent AI behavior** | NPCs query same affordances as players |
| **Emergent problem-solving** | Combine affordances creatively |
| **A world that feels physical** | Affordances are properties of reality |

---

## Summary

**This schema is the backbone of a true ASCII immersive sim.**

The player doesn't learn commands.
The player learns the world.
And the world *affords*.

---

*End of Affordance Schema*
