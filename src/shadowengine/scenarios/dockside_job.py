"""
The Dockside Job — Phase 5 integration demo.

A noir mystery scenario that exercises every wired system:
- BehaviorCircuits via SignalRouter (locked crate, broken radio, blood stain)
- CharacterMemory via DialogueHandler (NPCs remember conversations)
- PropagationEngine via GameEventBridge (rumors, gossip, behavior hints)
- NarrativeSpine with evidence chains (multiple solve paths)

Scenario:
  Someone was killed at the dock last night.
  Three NPCs know fragments of the truth.
  Three circuit objects gate physical clues.
  Player actions ripple across all systems.
"""

from ..game import Game, GameState
from ..config import GameConfig
from ..character import Character, Archetype
from ..narrative import NarrativeSpine, ConflictType, TrueResolution, Revelation
from ..render import Location
from ..interaction import Hotspot, HotspotType
from ..circuits import (
    BehaviorCircuit, CircuitType, CircuitState,
    SignalType, InputSignal, OutputSignal,
)


# ============================================================================
# ASCII Art
# ============================================================================

DOCK_ART = [
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    "@@░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░@@",
    "@@░░  NIGHT HARBOR  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░@@",
    "@@░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░@@",
    "@@  ┌─────────────┐     ┌──────────┐     ┌──────────┐               @@",
    "@@  │ LOCKED CRATE │     │  RADIO   │     │ BOLLARD  │               @@",
    "@@  │  ▓▓▓▓▓▓▓▓▓  │     │  ░░ ≈≈   │     │  ███     │               @@",
    "@@  └─────────────┘     └──────────┘     └──────────┘               @@",
    "@@                                                                  @@",
    "@@═══════════════════════════════════════════════════════════════════@@",
    "@@  ▒▒▒▒▒▒▒▒▒▒▒▒  WOODEN DOCK  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  @@",
    "@@═══════════════════════════════════════════════════════════════════@@",
    "@@  ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈ DARK WATER ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈ @@",
    "@@  ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈ @@",
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
]

WAREHOUSE_ART = [
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    "@@@@@@@@@@GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG@@@@@@@@@@@@",
    "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
    "@@@@@@@@@@G   ┌────────────────────┐  ┌────────────────┐  G@@@@@@@@@@@@",
    "@@@@@@@@@@G   │ SHIPPING CRATES    │  │  OFFICE DOOR   │  G@@@@@@@@@@@@",
    "@@@@@@@@@@G   │ ▓▓▓▓▓  ▓▓▓▓▓      │  │     ╔══╗      │  G@@@@@@@@@@@@",
    "@@@@@@@@@@G   └────────────────────┘  └────────────────┘  G@@@@@@@@@@@@",
    "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
    "@@@@@@@@@@G       ░░░ BLOODSTAIN ░░░                      G@@@@@@@@@@@@",
    "@@@@@@@@@@G       ░░░░░░░░░░░░░░░░░░                      G@@@@@@@@@@@@",
    "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
    "@@@@@@@@@@G   ═════════     ┌──────────────────────────┐  G@@@@@@@@@@@@",
    "@@@@@@@@@@G   ║FORKLIFT║    │     CARGO BAY DOOR       │  G@@@@@@@@@@@@",
    "@@@@@@@@@@G   ═════════     └──────────────────────────┘  G@@@@@@@@@@@@",
    "@@@@@@@@@@GLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLG@@@@@@@@@@@@",
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
]

BAR_ART = [
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    "@@@@@@@@@@GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG@@@@@@@@@@@@",
    "@@@@@@@@@@G  ┌──────────────────────────────────────────┐ G@@@@@@@@@@@@",
    "@@@@@@@@@@G  │░░░░░░░░░░░░░░ ANCHOR BAR ░░░░░░░░░░░░░░│ G@@@@@@@@@@@@",
    "@@@@@@@@@@G  │  ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗     │ G@@@@@@@@@@@@",
    "@@@@@@@@@@G  │  ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║     │ G@@@@@@@@@@@@",
    "@@@@@@@@@@G  └──────────────────────────────────────────┘ G@@@@@@@@@@@@",
    "@@@@@@@@@@G                @                              G@@@@@@@@@@@@",
    "@@@@@@@@@@G             BARTENDER                         G@@@@@@@@@@@@",
    "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
    "@@@@@@@@@@G    ═══    ═══    ═══    ═══       @           G@@@@@@@@@@@@",
    "@@@@@@@@@@G   STOOL  STOOL  STOOL  STOOL   STRANGER      G@@@@@@@@@@@@",
    "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
    "@@@@@@@@@@G   ┌────────┐                                  G@@@@@@@@@@@@",
    "@@@@@@@@@@G   │ EXIT   │          JUKEBOX ♪               G@@@@@@@@@@@@",
    "@@@@@@@@@@GLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLG@@@@@@@@@@@@",
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
]

ALLEY_ART = [
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    "@@▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓@@",
    "@@▓▓                                                              ▓▓@@",
    "@@▓▓   BRICK WALL                              BRICK WALL         ▓▓@@",
    "@@▓▓                                                              ▓▓@@",
    "@@▓▓       ┌─────────┐                                            ▓▓@@",
    "@@▓▓       │ DUMPSTER│    ░░░░░░░░░░░░░░░                        ▓▓@@",
    "@@▓▓       │ ▓▓▓▓▓▓▓ │    ░ DRAG MARKS ░░                        ▓▓@@",
    "@@▓▓       └─────────┘    ░░░░░░░░░░░░░░░                        ▓▓@@",
    "@@▓▓                                                              ▓▓@@",
    "@@▓▓                          @                                   ▓▓@@",
    "@@▓▓                       DOCKWORKER                             ▓▓@@",
    "@@▓▓                                                              ▓▓@@",
    "@@▓▓                                                              ▓▓@@",
    "@@▓▓   ← DOCK                                     WAREHOUSE →    ▓▓@@",
    "@@▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓@@",
    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
]


# ============================================================================
# Circuit Processors (custom behavior for interactive objects)
# ============================================================================

def _crate_processor(circuit: BehaviorCircuit, signal: InputSignal) -> list[OutputSignal]:
    """
    Locked Crate — mechanical circuit.

    - LOOK: describes current state
    - KICK/PUSH: damages it, produces sound; 3 kicks breaks it open
    - PULL: tries to pry it open, less effective
    - PRESS: tries the latch (locked without key)
    """
    outputs = []

    if signal.type == SignalType.LOOK:
        # Describe based on health
        if circuit.state.health > 0.7:
            desc = "A heavy wooden crate, padlocked shut. Sturdy but not invincible."
        elif circuit.state.health > 0.3:
            desc = "The crate is cracked and splintering. One more hit might do it."
        else:
            desc = "The crate is barely holding together."
        outputs.append(OutputSignal(
            type=SignalType.EMIT,
            strength=0.2,
            source_id=circuit.id,
            data={"description": desc},
        ))
        return outputs

    if signal.type in (SignalType.KICK, SignalType.PUSH):
        # Damage the crate
        destroyed = circuit.state.apply_damage(0.35)
        outputs.append(OutputSignal(
            type=SignalType.SOUND,
            strength=0.7,
            source_id=circuit.id,
            radius=5.0,
            data={"description": "A loud crack echoes across the dock as you hit the crate."},
        ))
        if destroyed:
            outputs.append(OutputSignal(
                type=SignalType.COLLAPSE,
                strength=1.0,
                source_id=circuit.id,
                data={"description": "The crate splinters open!"},
            ))
            # Reveal hidden evidence inside
            outputs.append(OutputSignal(
                type=SignalType.TRIGGER,
                strength=1.0,
                source_id=circuit.id,
                data={
                    "fact_id": "smuggled_goods",
                    "description": "Inside the crate: stacks of counterfeit bills and a shipping manifest.",
                    "is_evidence": True,
                },
            ))
        return outputs

    if signal.type == SignalType.PULL:
        # Pry at the lock — less effective
        circuit.state.apply_damage(0.15)
        outputs.append(OutputSignal(
            type=SignalType.SOUND,
            strength=0.4,
            source_id=circuit.id,
            radius=3.0,
            data={"description": "You pry at the crate. Wood creaks."},
        ))
        return outputs

    if signal.type == SignalType.PRESS:
        # Try the latch
        if circuit.state.custom.get("unlocked"):
            outputs.append(OutputSignal(
                type=SignalType.COLLAPSE,
                strength=0.5,
                source_id=circuit.id,
                data={"description": "The latch clicks open. The crate lid lifts."},
            ))
            outputs.append(OutputSignal(
                type=SignalType.TRIGGER,
                strength=1.0,
                source_id=circuit.id,
                data={
                    "fact_id": "smuggled_goods",
                    "description": "Inside the crate: stacks of counterfeit bills and a shipping manifest.",
                    "is_evidence": True,
                },
            ))
        else:
            outputs.append(OutputSignal(
                type=SignalType.EMIT,
                strength=0.2,
                source_id=circuit.id,
                data={"description": "The padlock holds firm. You need a key — or brute force."},
            ))
        return outputs

    return outputs


def _radio_processor(circuit: BehaviorCircuit, signal: InputSignal) -> list[OutputSignal]:
    """
    Broken Radio — environmental circuit.

    - LOOK: describes current state
    - PRESS: powers it on/off — when powered, picks up a fragment
    - KICK: damages it further (may destroy)
    """
    outputs = []

    if signal.type == SignalType.LOOK:
        if not circuit.state.active:
            desc = "A smashed dock radio. Wires dangle. It might still work."
        elif circuit.state.custom.get("powered"):
            desc = "The radio crackles with static. Fragments of a transmission."
        else:
            desc = "A battered dock radio. The power switch is off."
        outputs.append(OutputSignal(
            type=SignalType.EMIT,
            strength=0.2,
            source_id=circuit.id,
            data={"description": desc},
        ))
        return outputs

    if signal.type == SignalType.PRESS:
        if not circuit.state.active:
            outputs.append(OutputSignal(
                type=SignalType.EMIT,
                strength=0.1,
                source_id=circuit.id,
                data={"description": "The radio is too damaged to turn on."},
            ))
            return outputs

        powered = circuit.state.custom.get("powered", False)
        circuit.state.custom["powered"] = not powered

        if not powered:
            # Turning on — reveal a clue via the transmission
            outputs.append(OutputSignal(
                type=SignalType.SOUND,
                strength=0.5,
                source_id=circuit.id,
                radius=4.0,
                data={"description": "The radio hisses to life with static and fragments of a voice."},
            ))
            outputs.append(OutputSignal(
                type=SignalType.TRIGGER,
                strength=0.8,
                source_id=circuit.id,
                data={
                    "fact_id": "radio_transmission",
                    "description": (
                        "Through the static: '...shipment moved at 2 AM... "
                        "warehouse clear... the accountant won't be a problem anymore...'"
                    ),
                    "is_evidence": True,
                },
            ))
        else:
            outputs.append(OutputSignal(
                type=SignalType.EMIT,
                strength=0.1,
                source_id=circuit.id,
                data={"description": "The radio clicks off."},
            ))
        return outputs

    if signal.type in (SignalType.KICK, SignalType.PUSH):
        destroyed = circuit.state.apply_damage(0.5)
        outputs.append(OutputSignal(
            type=SignalType.SOUND,
            strength=0.4,
            source_id=circuit.id,
            radius=3.0,
            data={"description": "You smash the radio. Components scatter."},
        ))
        if destroyed:
            circuit.state.active = False
            outputs.append(OutputSignal(
                type=SignalType.COLLAPSE,
                strength=0.8,
                source_id=circuit.id,
                data={"description": "The radio is completely destroyed."},
            ))
        return outputs

    return outputs


def _bloodstain_processor(circuit: BehaviorCircuit, signal: InputSignal) -> list[OutputSignal]:
    """
    Bloodstain — environmental circuit.

    - LOOK: reveals more detail on repeated examinations
    - PULL/PRESS: scraping reveals hidden evidence underneath
    """
    outputs = []
    look_count = circuit.state.custom.get("look_count", 0)

    if signal.type == SignalType.LOOK:
        circuit.state.custom["look_count"] = look_count + 1

        if look_count == 0:
            desc = "Dark stains on the warehouse floor. Could be oil... or blood."
        elif look_count == 1:
            desc = "Definitely blood. A lot of it. The drag marks lead toward the dock."
            outputs.append(OutputSignal(
                type=SignalType.TRIGGER,
                strength=0.6,
                source_id=circuit.id,
                data={
                    "fact_id": "drag_marks",
                    "description": "Drag marks lead from the bloodstain toward the dock. The body was moved.",
                    "is_evidence": True,
                },
            ))
        else:
            desc = "Under the blood: scuff marks from expensive shoes. And a monogrammed cufflink — V.H."
            outputs.append(OutputSignal(
                type=SignalType.TRIGGER,
                strength=1.0,
                source_id=circuit.id,
                data={
                    "fact_id": "cufflink_evidence",
                    "description": "A monogrammed cufflink 'V.H.' found in the bloodstain. Victor Harlow?",
                    "is_evidence": True,
                },
            ))

        outputs.append(OutputSignal(
            type=SignalType.EMIT,
            strength=0.3,
            source_id=circuit.id,
            data={"description": desc},
        ))
        # Alert nearby NPCs that you're examining the crime scene
        outputs.append(OutputSignal(
            type=SignalType.ALERT,
            strength=0.4,
            source_id=circuit.id,
            data={"description": "The detective is examining the bloodstain."},
        ))
        return outputs

    return outputs


# ============================================================================
# Circuit Factories
# ============================================================================

def create_crate_circuit() -> BehaviorCircuit:
    """Create the locked crate mechanical circuit."""
    circuit = BehaviorCircuit(
        id="circuit_crate",
        name="Locked Crate",
        circuit_type=CircuitType.MECHANICAL,
        description="A heavy padlocked shipping crate.",
        input_signals=[
            SignalType.LOOK, SignalType.KICK, SignalType.PUSH,
            SignalType.PULL, SignalType.PRESS,
        ],
        output_signals=[
            SignalType.SOUND, SignalType.COLLAPSE, SignalType.TRIGGER,
            SignalType.EMIT,
        ],
        affordances=["examine", "kick", "force", "unlock"],
    )
    circuit.set_processor(_crate_processor)
    return circuit


def create_radio_circuit() -> BehaviorCircuit:
    """Create the broken radio environmental circuit."""
    circuit = BehaviorCircuit(
        id="circuit_radio",
        name="Broken Radio",
        circuit_type=CircuitType.ENVIRONMENTAL,
        description="A battered dock radio, half-smashed.",
        input_signals=[
            SignalType.LOOK, SignalType.PRESS, SignalType.KICK, SignalType.PUSH,
        ],
        output_signals=[
            SignalType.SOUND, SignalType.COLLAPSE, SignalType.TRIGGER,
            SignalType.EMIT,
        ],
        state=CircuitState(health=0.6),
        affordances=["examine", "use", "smash"],
    )
    circuit.set_processor(_radio_processor)
    return circuit


def create_bloodstain_circuit() -> BehaviorCircuit:
    """Create the bloodstain environmental circuit."""
    circuit = BehaviorCircuit(
        id="circuit_blood",
        name="Bloodstain",
        circuit_type=CircuitType.ENVIRONMENTAL,
        description="A dark stain on the warehouse floor.",
        input_signals=[SignalType.LOOK, SignalType.PULL, SignalType.PRESS],
        output_signals=[
            SignalType.TRIGGER, SignalType.EMIT, SignalType.ALERT,
        ],
        affordances=["examine", "scrape"],
    )
    circuit.set_processor(_bloodstain_processor)
    return circuit


# ============================================================================
# Scenario Setup
# ============================================================================

def setup_dockside_scenario(game: Game) -> None:
    """
    Set up "The Dockside Job" scenario on an existing Game instance.

    Creates 4 locations, 3 NPCs, 3 circuit objects, and a narrative spine.
    """
    game.new_game(seed=42)

    # ------------------------------------------------------------------
    # Narrative Spine
    # ------------------------------------------------------------------
    spine = NarrativeSpine(
        conflict_type=ConflictType.MURDER,
        conflict_description=(
            "An accountant named Eddie Marsh was killed at the waterfront "
            "last night. His body was dumped off the dock."
        ),
        true_resolution=TrueResolution(
            culprit_id="stranger",
            motive="Eddie discovered the counterfeit operation and threatened to go to the police",
            method="beaten in the warehouse, body dragged to the dock and dumped",
            opportunity="met Eddie at 2 AM under the pretense of a business deal",
            evidence_chain=[
                "drag_marks",
                "radio_transmission",
                "smuggled_goods",
                "cufflink_evidence",
            ],
        ),
        revelations=[
            Revelation(
                id="drag_marks",
                description="Drag marks lead from the warehouse bloodstain to the dock",
                importance=2,
                source="Examine the bloodstain closely",
            ),
            Revelation(
                id="radio_transmission",
                description="Radio intercept: shipment at 2 AM, accountant 'handled'",
                importance=2,
                source="Power on the dock radio",
            ),
            Revelation(
                id="smuggled_goods",
                description="Counterfeit bills and a shipping manifest inside the crate",
                importance=3,
                prerequisites=["radio_transmission"],
                source="Break open or unlock the crate",
            ),
            Revelation(
                id="cufflink_evidence",
                description="Monogrammed cufflink 'V.H.' found at the scene",
                importance=3,
                prerequisites=["drag_marks"],
                source="Examine the bloodstain multiple times",
            ),
        ],
    )
    game.set_spine(spine)

    # ------------------------------------------------------------------
    # Characters
    # ------------------------------------------------------------------
    bartender = Character(
        id="bartender",
        name="Gus Renko",
        archetype=Archetype.SURVIVOR,
        description="A grizzled bartender with cauliflower ears and a permanent frown.",
        secret_truth=(
            "I saw Victor Harlow drag someone toward the dock at 2 AM. "
            "I didn't say anything because Harlow owns half the waterfront."
        ),
        public_lie="I was closing up. Didn't see nothing unusual.",
        role_in_spine="witness",
        trust_threshold=30,
        initial_location="bar",
    )
    bartender.add_knowledge("Eddie Marsh was a regular — quiet, nervous type")
    bartender.add_knowledge("Victor Harlow drinks here sometimes, always pays cash")
    bartender.add_topic("eddie marsh")
    bartender.add_topic("last night")
    bartender.add_topic("the dock")
    bartender.add_topic("victor harlow")

    dockworker = Character(
        id="dockworker",
        name="Pete Navarro",
        archetype=Archetype.INNOCENT,
        description="A wiry dockworker with calloused hands, jumpy as a cat.",
        secret_truth=(
            "I heard screaming from the warehouse around 2 AM. "
            "I saw two figures near the crate. I ran."
        ),
        public_lie="I clocked out at midnight. Didn't hear anything.",
        role_in_spine="witness",
        trust_threshold=20,
        initial_location="alley",
    )
    dockworker.add_knowledge("Crates get moved at night — I don't ask what's inside")
    dockworker.add_knowledge("The warehouse belongs to Harlow's company")
    dockworker.add_topic("the warehouse")
    dockworker.add_topic("the screaming")
    dockworker.add_topic("night shift")

    stranger = Character(
        id="stranger",
        name="Victor Harlow",
        archetype=Archetype.GUILTY,
        description="A well-dressed man with cold eyes, nursing expensive whiskey.",
        secret_truth=(
            "I killed Eddie Marsh. He found out about the counterfeit operation "
            "and was going to talk. I beat him in the warehouse and dumped the body."
        ),
        public_lie="I'm a businessman. I was at a dinner party last night.",
        role_in_spine="culprit",
        trust_threshold=50,
        initial_location="bar",
    )
    stranger.add_knowledge("Eddie Marsh owed me money — that's all")
    stranger.add_topic("eddie marsh")
    stranger.add_topic("your business")
    stranger.add_topic("the waterfront")

    game.add_character(bartender)
    game.add_character(dockworker)
    game.add_character(stranger)

    # ------------------------------------------------------------------
    # Locations
    # ------------------------------------------------------------------

    # 1. The Dock
    dock = Location(
        id="dock",
        name="Harbor Dock",
        description=(
            "Cold wind off the water. Creaking wood underfoot. "
            "A locked crate and a broken radio sit near the bollards."
        ),
        art=DOCK_ART,
        is_outdoor=True,
        ambient_description="Waves lap against the pilings. Fog rolls in.",
    )
    dock.add_hotspot(Hotspot(
        id="hs_crate",
        label="Locked Crate",
        hotspot_type=HotspotType.CONTAINER,
        position=(10, 5),
        description="A heavy shipping crate, padlocked shut.",
        examine_text="Markings read: 'HARLOW IMPORTS — FRAGILE'. The lock is industrial grade.",
        circuit=create_crate_circuit(),
    ))
    dock.add_hotspot(Hotspot(
        id="hs_radio",
        label="Broken Radio",
        hotspot_type=HotspotType.OBJECT,
        position=(35, 5),
        description="A dock radio, half-smashed on the ground.",
        examine_text="The dial is cracked but the wiring looks intact.",
        use_text="You fiddle with the power switch.",
        circuit=create_radio_circuit(),
    ))
    dock.add_hotspot(Hotspot.create_exit(
        id="hs_dock_to_alley",
        label="Alley",
        position=(10, 15),
        destination="alley",
        description="A narrow alley leads between the buildings.",
    ))
    dock.add_hotspot(Hotspot.create_exit(
        id="hs_dock_to_bar",
        label="The Anchor Bar",
        position=(55, 5),
        destination="bar",
        description="A dive bar at the end of the wharf.",
    ))
    game.add_location(dock, is_indoor=False)

    # 2. The Warehouse
    warehouse = Location(
        id="warehouse",
        name="Harlow Imports Warehouse",
        description=(
            "Cavernous and cold. Rows of shipping crates. "
            "Something dark stains the concrete floor."
        ),
        art=WAREHOUSE_ART,
        is_outdoor=False,
        ambient_description="Dripping water echoes. The smell of iron.",
    )
    warehouse.add_hotspot(Hotspot(
        id="hs_bloodstain",
        label="Bloodstain",
        hotspot_type=HotspotType.EVIDENCE,
        position=(20, 9),
        description="A large dark stain on the concrete.",
        examine_text="Dark stains on the warehouse floor. Could be oil... or blood.",
        circuit=create_bloodstain_circuit(),
    ))
    warehouse.add_hotspot(Hotspot(
        id="hs_shipping_crates",
        label="Shipping Crates",
        hotspot_type=HotspotType.OBJECT,
        position=(20, 4),
        description="Rows of identical crates, all marked HARLOW IMPORTS.",
        examine_text="Dozens of crates. Most are empty. A few smell faintly of ink.",
    ))
    warehouse.add_hotspot(Hotspot(
        id="hs_forklift",
        label="Forklift",
        hotspot_type=HotspotType.OBJECT,
        position=(10, 13),
        description="An old forklift with a key still in the ignition.",
        examine_text="The seat is stained with something dark. Recently used.",
    ))
    warehouse.add_hotspot(Hotspot.create_exit(
        id="hs_warehouse_to_alley",
        label="Back to Alley",
        position=(55, 13),
        destination="alley",
        description="The cargo bay door leads to the alley.",
    ))
    game.add_location(warehouse, is_indoor=True)

    # 3. The Bar
    bar = Location(
        id="bar",
        name="The Anchor Bar",
        description=(
            "Smoke, cheap bourbon, and secrets. "
            "The bartender knows everyone. The stranger in the corner watches you."
        ),
        art=BAR_ART,
        is_outdoor=False,
        ambient_description="A jukebox plays something slow and sad.",
    )
    bar.add_hotspot(Hotspot.create_person(
        id="hs_bartender",
        name="Gus Renko (Bartender)",
        position=(30, 8),
        character_id="bartender",
        description="He polishes a glass that's already clean.",
    ))
    bar.add_hotspot(Hotspot.create_person(
        id="hs_stranger",
        name="Victor Harlow (Well-Dressed Man)",
        position=(52, 11),
        character_id="stranger",
        description="A well-dressed man nursing expensive whiskey.",
    ))
    bar.add_hotspot(Hotspot(
        id="hs_jukebox",
        label="Jukebox",
        hotspot_type=HotspotType.OBJECT,
        position=(52, 14),
        description="An old jukebox with a cracked display.",
        examine_text="Playing 'Ain't Misbehavin'. The playlist hasn't changed in twenty years.",
    ))
    bar.add_hotspot(Hotspot.create_exit(
        id="hs_bar_to_dock",
        label="Exit to Dock",
        position=(10, 14),
        destination="dock",
        description="Back to the waterfront.",
    ))
    bar.add_hotspot(Hotspot.create_exit(
        id="hs_bar_to_alley",
        label="Back Door (Alley)",
        position=(55, 14),
        destination="alley",
        description="A back door leads to the alley.",
    ))
    game.add_location(bar, is_indoor=True)

    # 4. The Alley
    alley = Location(
        id="alley",
        name="Waterfront Alley",
        description=(
            "Narrow, dark, between the warehouse and the bar. "
            "Drag marks in the grime. Someone was here recently."
        ),
        art=ALLEY_ART,
        is_outdoor=True,
        ambient_description="Rats scatter. A fire escape creaks overhead.",
    )
    alley.add_hotspot(Hotspot.create_person(
        id="hs_dockworker",
        name="Pete Navarro (Dockworker)",
        position=(35, 11),
        character_id="dockworker",
        description="A nervous dockworker, smoking in the shadows.",
    ))
    alley.add_hotspot(Hotspot(
        id="hs_dumpster",
        label="Dumpster",
        hotspot_type=HotspotType.CONTAINER,
        position=(15, 7),
        description="Overflowing. Something metallic glints inside.",
        examine_text="Under the garbage: an empty wallet. The ID reads 'Edward Marsh'.",
        reveals_fact="drag_marks",
    ))
    alley.add_hotspot(Hotspot.create_exit(
        id="hs_alley_to_dock",
        label="Dock",
        position=(5, 15),
        destination="dock",
        description="Back to the harbor dock.",
    ))
    alley.add_hotspot(Hotspot.create_exit(
        id="hs_alley_to_warehouse",
        label="Warehouse",
        position=(60, 15),
        destination="warehouse",
        description="The warehouse door is ajar.",
    ))
    alley.add_hotspot(Hotspot.create_exit(
        id="hs_alley_to_bar",
        label="Bar (Side Door)",
        position=(35, 15),
        destination="bar",
        description="A side door into The Anchor Bar.",
    ))
    game.add_location(alley, is_indoor=False)

    # ------------------------------------------------------------------
    # Start position
    # ------------------------------------------------------------------
    game.set_start_location("dock")

    # ------------------------------------------------------------------
    # WorldState enrichment
    # ------------------------------------------------------------------
    ws = game.state.world_state
    ws.world_genre = "noir mystery"
    ws.world_era = "1940s"
    ws.world_rules = [
        "The waterfront is controlled by Victor Harlow",
        "Everyone has a price or a fear",
        "The police don't come down here after dark",
    ]

    ws.set_main_mystery({
        "victim": "Eddie Marsh",
        "crime": "murder",
        "location": "waterfront warehouse / dock",
        "suspects": [
            "Gus Renko (bartender)",
            "Pete Navarro (dockworker)",
            "Victor Harlow (businessman)",
        ],
        "culprit_id": "stranger",
    })

    for loc_id, loc in game.state.locations.items():
        ws.register_location({
            "id": loc.id,
            "name": loc.name,
            "location_type": loc_id,
            "description": loc.description,
            "is_outdoor": loc.is_outdoor,
        })

    ws.register_npc({
        "id": "bartender",
        "name": "Gus Renko",
        "description": bartender.description,
        "archetype": bartender.archetype.value,
        "secret": bartender.secret_truth,
        "public_persona": bartender.public_lie,
        "topics": list(bartender.available_topics),
    }, "bar")

    ws.register_npc({
        "id": "dockworker",
        "name": "Pete Navarro",
        "description": dockworker.description,
        "archetype": dockworker.archetype.value,
        "secret": dockworker.secret_truth,
        "public_persona": dockworker.public_lie,
        "topics": list(dockworker.available_topics),
    }, "alley")

    ws.register_npc({
        "id": "stranger",
        "name": "Victor Harlow",
        "description": stranger.description,
        "archetype": stranger.archetype.value,
        "secret": stranger.secret_truth,
        "public_persona": stranger.public_lie,
        "topics": list(stranger.available_topics),
    }, "bar")

    ws.add_npc_relationship("bartender", "stranger", "serves drinks to")
    ws.add_npc_relationship("bartender", "dockworker", "knows from the bar")
    ws.add_npc_relationship("stranger", "dockworker", "employer")
    ws.add_npc_relationship("dockworker", "stranger", "afraid of")

    ws.add_fact(
        "victim_found",
        "Eddie Marsh's body was pulled from the harbor this morning",
        "police report",
        locations=["dock"],
    )
    ws.add_fact(
        "victim_occupation",
        "Eddie Marsh was a freelance accountant — he did books for Harlow Imports",
        "public record",
        npcs=["stranger"],
    )

    ws.record_event(
        "eddie_murder",
        "Eddie Marsh was killed at the waterfront",
        "warehouse",
        npcs=["stranger"],
        is_public=True,
    )


def create_dockside_job(seed: int = 42) -> Game:
    """Create and return a fully configured Dockside Job game."""
    game = Game(config=GameConfig(enable_audio=False, enable_speech=False))
    setup_dockside_scenario(game)
    return game


def run_dockside_job():
    """Run the Dockside Job scenario interactively."""
    print()
    print("=" * 72)
    print("  THE DOCKSIDE JOB")
    print("  A ShadowEngine Demo")
    print("=" * 72)
    print()
    print("An accountant named Eddie Marsh was pulled from the harbor this morning.")
    print("The cops don't care. You do.")
    print()
    print("Commands: examine [object], talk [person], go [place]")
    print("          threaten, accuse, use [object], kick [object], wait")
    print()
    input("Press Enter to begin...")

    game = create_dockside_job()
    game.run()


if __name__ == "__main__":
    run_dockside_job()
