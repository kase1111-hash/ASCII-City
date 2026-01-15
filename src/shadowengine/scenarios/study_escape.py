"""
Noir Detective Scenario - An LLM-driven procedural mystery.

The city generates as you explore. NPCs respond dynamically.
Every playthrough is unique based on your actions and the LLM.
"""

import random
import time
from typing import Optional

from ..game import Game
from ..character import Character, Archetype
from ..narrative import NarrativeSpine, ConflictType, TrueResolution, Revelation
from ..render import Location
from ..interaction import Hotspot, HotspotType
from ..llm import LLMIntegration, LLMConfig


# ============================================================================
# ASCII ART - Dynamically selected based on location type
# ============================================================================

LOCATION_ART = {
    "office": [
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "@@@@@@@@@@GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG@@@@@@@@@@@@",
        "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
        "@@@@@@@@@@G   ╔══════╗                      ┌────────┐   G@@@@@@@@@@@@",
        "@@@@@@@@@@G   ║FILING║   @                  │ WINDOW │   G@@@@@@@@@@@@",
        "@@@@@@@@@@G   ║CABINT║  YOU                 │ ░░░░░░ │   G@@@@@@@@@@@@",
        "@@@@@@@@@@G   ╚══════╝                      │ ░░░░░░ │   G@@@@@@@@@@@@",
        "@@@@@@@@@@G                                 └────────┘   G@@@@@@@@@@@@",
        "@@@@@@@@@@G   ┌─────────────────────────┐                G@@@@@@@@@@@@",
        "@@@@@@@@@@G   │░░░░░░░░ YOUR DESK ░░░░░░│                G@@@@@@@@@@@@",
        "@@@@@@@@@@G   └─────────────────────────┘                G@@@@@@@@@@@@",
        "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
        "@@@@@@@@@@G       ═══════════         ┌──────────────┐   G@@@@@@@@@@@@",
        "@@@@@@@@@@G       ║ CHAIR  ║         │   DOOR OUT   │   G@@@@@@@@@@@@",
        "@@@@@@@@@@G       ═══════════         └──────────────┘   G@@@@@@@@@@@@",
        "@@@@@@@@@@GLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLG@@@@@@@@@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    ],
    "street": [
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "@@░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░@@",
        "@@░░ NIGHT SKY ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░@@",
        "@@░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░@@",
        "@@ ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐     @@",
        "@@ │▓▓▓▓▓▓│  │▓▓▓▓▓▓│  │▓▓▓▓▓▓│  │▓▓▓▓▓▓│  │▓▓▓▓▓▓│  │▓▓▓▓▓▓│     @@",
        "@@ │BUILDING│ │BUILDING│ │  BAR │  │ SHOP │  │BUILDING│ │ALLEY │     @@",
        "@@ │▓▓▓▓▓▓│  │▓▓▓▓▓▓│  │▓▓▓▓▓▓│  │▓▓▓▓▓▓│  │▓▓▓▓▓▓│  │▓▓▓▓▓▓│     @@",
        "@@ └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘     @@",
        "@@                                                                  @@",
        "@@═══════════════════════════════════════════════════════════════════@@",
        "@@  ░░░░░░░░░░░░░░  RAIN-SLICKED STREET  ░░░░░░░░░░░░░░░░░░░░░░░░░░  @@",
        "@@═══════════════════════════════════════════════════════════════════@@",
        "@@       @                    ╬                  @                   @@",
        "@@    FIGURE               LAMPPOST           SHADOW                 @@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    ],
    "bar": [
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "@@@@@@@@@@GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG@@@@@@@@@@@@",
        "@@@@@@@@@@G  ┌──────────────────────────────────────────┐ G@@@@@@@@@@@@",
        "@@@@@@@@@@G  │░░░░░░░░░░░░░░░░ BAR ░░░░░░░░░░░░░░░░░░░░░│ G@@@@@@@@@@@@",
        "@@@@@@@@@@G  │  ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗   │ G@@@@@@@@@@@@",
        "@@@@@@@@@@G  │  ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║ ║   │ G@@@@@@@@@@@@",
        "@@@@@@@@@@G  └──────────────────────────────────────────┘ G@@@@@@@@@@@@",
        "@@@@@@@@@@G                   @                            G@@@@@@@@@@@@",
        "@@@@@@@@@@G                BARTENDER                       G@@@@@@@@@@@@",
        "@@@@@@@@@@G                                                G@@@@@@@@@@@@",
        "@@@@@@@@@@G    ═══    ═══    ═══    ═══                   G@@@@@@@@@@@@",
        "@@@@@@@@@@G   STOOL  STOOL  STOOL  STOOL    @     @       G@@@@@@@@@@@@",
        "@@@@@@@@@@G                               PATRON PATRON    G@@@@@@@@@@@@",
        "@@@@@@@@@@G   ┌────────┐                                   G@@@@@@@@@@@@",
        "@@@@@@@@@@G   │ EXIT   │    ╔════════╗    JUKEBOX ♪       G@@@@@@@@@@@@",
        "@@@@@@@@@@G   └────────┘    ║ BOOTH  ║                    G@@@@@@@@@@@@",
        "@@@@@@@@@@GLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLG@@@@@@@@@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    ],
    "alley": [
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "@@▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓@@",
        "@@▓▓                                                              ▓▓@@",
        "@@▓▓   BRICK WALL                              BRICK WALL         ▓▓@@",
        "@@▓▓                                                              ▓▓@@",
        "@@▓▓       ┌─────────┐                                            ▓▓@@",
        "@@▓▓       │ DUMPSTER│    ░░░░░░░░░░░░░░░                        ▓▓@@",
        "@@▓▓       │ ▓▓▓▓▓▓▓ │    ░ SOMETHING ░░                         ▓▓@@",
        "@@▓▓       └─────────┘    ░░ ON GROUND ░                          ▓▓@@",
        "@@▓▓                      ░░░░░░░░░░░░░░░                         ▓▓@@",
        "@@▓▓                                                              ▓▓@@",
        "@@▓▓   @                                              FIRE        ▓▓@@",
        "@@▓▓  RAT                                             ESCAPE      ▓▓@@",
        "@@▓▓                                                    │         ▓▓@@",
        "@@▓▓                                                    │         ▓▓@@",
        "@@▓▓   ← STREET                              DEAD END →           ▓▓@@",
        "@@▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    ],
    "generic": [
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "@@@@@@@@@@GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG@@@@@@@@@@@@",
        "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
        "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
        "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
        "@@@@@@@@@@G              [ LOCATION ]                     G@@@@@@@@@@@@",
        "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
        "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
        "@@@@@@@@@@G                   @                           G@@@@@@@@@@@@",
        "@@@@@@@@@@G                  YOU                          G@@@@@@@@@@@@",
        "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
        "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
        "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
        "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
        "@@@@@@@@@@G                                               G@@@@@@@@@@@@",
        "@@@@@@@@@@GLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLG@@@@@@@@@@@@",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
    ],
}


def get_art_for_location(location_type: str) -> list[str]:
    """Get appropriate ASCII art for a location type."""
    return LOCATION_ART.get(location_type, LOCATION_ART["generic"])


def create_study_escape(seed: int = None) -> Game:
    """
    Create a noir detective scenario.

    This is an LLM-driven mystery where:
    - The narrative spine defines the hidden truth
    - NPCs have personalities and secrets - LLM generates their dialogue
    - The city expands as you explore
    - Clues emerge from your investigations
    """
    game = Game()
    game.new_game(seed=seed)

    # Initialize LLM integration
    llm = LLMIntegration()
    game.llm = llm  # Attach for dynamic generation

    # Randomize the mystery for each playthrough
    if seed:
        random.seed(seed)

    # Generate the hidden truth - this is what the LLM uses to stay consistent
    culprits = ["bartender", "informant", "politician"]
    motives = [
        "gambling debts to dangerous people",
        "blackmail - the victim knew their secret",
        "jealousy over a love affair",
        "business deal gone wrong",
        "witness to a crime that needed silencing",
    ]
    methods = [
        "poison in a drink",
        "hired muscle",
        "staged accident",
        "pushed from a height",
    ]

    chosen_culprit = random.choice(culprits)
    chosen_motive = random.choice(motives)
    chosen_method = random.choice(methods)

    # Create the narrative spine - the hidden truth
    spine = NarrativeSpine(
        conflict_type=ConflictType.MURDER,
        conflict_description="A body was found in the alley behind O'Malley's Bar. "
                           "The victim: Marcus Webb, a small-time accountant with big connections.",
        true_resolution=TrueResolution(
            culprit_id=chosen_culprit,
            motive=chosen_motive,
            method=chosen_method,
            opportunity="was alone with the victim that night",
            evidence_chain=["witness_account", "physical_evidence", "motive_revealed", "confession"]
        ),
        revelations=[
            Revelation(
                id="witness_account",
                description="Someone saw the victim with another person",
                importance=2,
                source="Talk to people who were there that night"
            ),
            Revelation(
                id="physical_evidence",
                description="Evidence at the crime scene",
                importance=3,
                prerequisites=["witness_account"],
                source="Examine the alley carefully"
            ),
            Revelation(
                id="motive_revealed",
                description=f"The culprit's motive: {chosen_motive}",
                importance=3,
                prerequisites=["physical_evidence"],
                source="Dig into the suspect's background"
            ),
            Revelation(
                id="confession",
                description="The culprit breaks down and confesses",
                importance=3,
                prerequisites=["motive_revealed"],
                source="Confront the culprit with evidence"
            )
        ],
        twist_probability=0.2
    )
    game.set_spine(spine)

    # Create starting characters with rich personalities
    # The LLM will generate their dialogue based on these traits

    bartender = Character(
        id="bartender",
        name="Mickey O'Malley",
        archetype=Archetype.SURVIVOR if chosen_culprit != "bartender" else Archetype.GUILTY,
        description="A weathered bartender who's seen too much. "
                   "Gray hair, tired eyes, hands that never stop moving.",
        secret_truth=f"I killed Marcus Webb. {chosen_motive}. I used {chosen_method}."
                    if chosen_culprit == "bartender"
                    else "I saw who Marcus was talking to that night, but I'm scared to say.",
        public_lie="I don't know nothing. I just pour drinks."
                  if chosen_culprit == "bartender"
                  else "Busy night, didn't see much.",
        role_in_spine="culprit" if chosen_culprit == "bartender" else "witness",
        trust_threshold=30,
        initial_location="bar"
    )
    bartender.add_topic("marcus webb")
    bartender.add_topic("that night")
    bartender.add_topic("the bar")
    bartender.add_topic("regulars")
    game.add_character(bartender)

    informant = Character(
        id="informant",
        name="Sally 'Whispers' Malone",
        archetype=Archetype.OPPORTUNIST if chosen_culprit != "informant" else Archetype.GUILTY,
        description="A street informant with ears everywhere. "
                   "Small, quick, always watching the exits.",
        secret_truth=f"I killed Marcus Webb. {chosen_motive}. I used {chosen_method}."
                    if chosen_culprit == "informant"
                    else "I know who did it, but information isn't free.",
        public_lie="Marcus? Sure, I knew him. Everybody did."
                  if chosen_culprit == "informant"
                  else "I hear things, but I don't remember them for free.",
        role_in_spine="culprit" if chosen_culprit == "informant" else "informant",
        trust_threshold=25,
        initial_location="street"
    )
    informant.add_topic("marcus webb")
    informant.add_topic("rumors")
    informant.add_topic("the streets")
    informant.add_topic("who to trust")
    game.add_character(informant)

    politician = Character(
        id="politician",
        name="Councilman Vincent Harrow",
        archetype=Archetype.AUTHORITY if chosen_culprit != "politician" else Archetype.GUILTY,
        description="A city councilman with expensive tastes and powerful friends. "
                   "Slicked hair, gold watch, smile that doesn't reach his eyes.",
        secret_truth=f"I killed Marcus Webb. {chosen_motive}. I used {chosen_method}."
                    if chosen_culprit == "politician"
                    else "Marcus was doing my books. He found something he shouldn't have.",
        public_lie="Tragic loss. Marcus was a... friend of the community."
                  if chosen_culprit == "politician"
                  else "I barely knew the man. Ask his employer.",
        role_in_spine="culprit" if chosen_culprit == "politician" else "connected",
        trust_threshold=45,
        initial_location="office"
    )
    politician.add_topic("marcus webb")
    politician.add_topic("city business")
    politician.add_topic("your connections")
    politician.add_topic("the night in question")
    game.add_character(politician)

    # Create starting location - your detective office
    office = Location(
        id="office",
        name="Your Office",
        description="A cramped detective's office. Rain streaks the window. "
                   "The phone just stopped ringing - a new case.",
        art=get_art_for_location("office"),
        is_outdoor=False,
        ambient_description="The neon sign outside flickers. Another long night ahead."
    )

    office.add_hotspot(Hotspot(
        id="hs_desk",
        label="Your Desk",
        hotspot_type=HotspotType.OBJECT,
        position=(25, 10),
        description="Cluttered with case files and cold coffee.",
        examine_text="A folder sits on top: 'WEBB, Marcus - Deceased'. "
                    "Body found in the alley behind O'Malley's Bar. No witnesses... yet."
    ))

    office.add_hotspot(Hotspot(
        id="hs_window",
        label="Window",
        hotspot_type=HotspotType.OBJECT,
        position=(55, 5),
        description="Looking out at the rain-slicked streets.",
        examine_text="The city sprawls below. Somewhere out there, a killer thinks they got away with it."
    ))

    office.add_hotspot(Hotspot(
        id="hs_door_out",
        label="Door to Street",
        hotspot_type=HotspotType.EXIT,
        position=(55, 14),
        description="Time to hit the streets.",
        examine_text="The city awaits.",
        target_id="street"
    ))

    game.add_location(office)

    # Create the street - hub location
    street = Location(
        id="street",
        name="Rain-Slicked Street",
        description="A noir tableau. Streetlights cast pools of sickly yellow. "
                   "The rain never stops in this city.",
        art=get_art_for_location("street"),
        is_outdoor=True,
        ambient_description="Distant sirens. The smell of wet asphalt. Shadows move in doorways."
    )

    street.add_hotspot(Hotspot.create_person(
        id="hs_informant",
        name="Shadowy Figure (Sally)",
        position=(8, 14),
        character_id="informant",
        description="A small figure lurks near the lamppost, watching."
    ))

    street.add_hotspot(Hotspot(
        id="hs_bar_entrance",
        label="O'Malley's Bar",
        hotspot_type=HotspotType.EXIT,
        position=(25, 7),
        description="A dive bar. Neon sign buzzing.",
        examine_text="The kind of place where questions get answered - for a price.",
        target_id="bar"
    ))

    street.add_hotspot(Hotspot(
        id="hs_alley",
        label="Dark Alley",
        hotspot_type=HotspotType.EXIT,
        position=(60, 7),
        description="The crime scene. Police tape flutters.",
        examine_text="Where Marcus Webb took his last breath.",
        target_id="alley"
    ))

    street.add_hotspot(Hotspot(
        id="hs_office_return",
        label="Your Office Building",
        hotspot_type=HotspotType.EXIT,
        position=(8, 7),
        description="Back to base.",
        target_id="office"
    ))

    game.add_location(street)

    # Create the bar
    bar = Location(
        id="bar",
        name="O'Malley's Bar",
        description="Smoke hangs in the air. A jukebox plays something sad. "
                   "The bartender polishes a glass that's already clean.",
        art=get_art_for_location("bar"),
        is_outdoor=False,
        ambient_description="The clink of glasses. Murmured conversations that stop when you get close."
    )

    bar.add_hotspot(Hotspot.create_person(
        id="hs_bartender",
        name="Mickey O'Malley (Bartender)",
        position=(35, 8),
        character_id="bartender",
        description="The owner. He's seen your type before."
    ))

    bar.add_hotspot(Hotspot(
        id="hs_bar_counter",
        label="Bar Counter",
        hotspot_type=HotspotType.OBJECT,
        position=(35, 5),
        description="Sticky with years of spilled drinks.",
        examine_text="Initials carved into the wood. 'MW' - Marcus Webb? He was a regular."
    ))

    bar.add_hotspot(Hotspot(
        id="hs_booth",
        label="Back Booth",
        hotspot_type=HotspotType.OBJECT,
        position=(35, 15),
        description="A private booth in the shadows.",
        examine_text="Someone left a napkin with a phone number. The ink is fresh.",
        reveals_fact="witness_account"
    ))

    bar.add_hotspot(Hotspot(
        id="hs_bar_exit",
        label="Exit to Street",
        hotspot_type=HotspotType.EXIT,
        position=(10, 14),
        target_id="street"
    ))

    game.add_location(bar)

    # Create the alley - crime scene
    alley = Location(
        id="alley",
        name="Dark Alley (Crime Scene)",
        description="Police tape marks where the body was found. "
                   "The rain has washed away most of the blood, but not all.",
        art=get_art_for_location("alley"),
        is_outdoor=True,
        ambient_description="Rats scatter at your approach. The fire escape creaks in the wind."
    )

    alley.add_hotspot(Hotspot(
        id="hs_crime_scene",
        label="Chalk Outline",
        hotspot_type=HotspotType.EVIDENCE,
        position=(40, 8),
        description="Where Marcus Webb fell.",
        examine_text="The body position suggests he was taken by surprise. "
                    "He never saw it coming.",
        reveals_fact="physical_evidence",
        requires_discovery="witness_account"
    ))

    alley.add_hotspot(Hotspot(
        id="hs_dumpster",
        label="Dumpster",
        hotspot_type=HotspotType.CONTAINER,
        position=(15, 7),
        description="Overflowing with garbage.",
        examine_text="Under the trash... a torn piece of fabric. Expensive material. "
                    "Someone wealthy was here."
    ))

    alley.add_hotspot(Hotspot(
        id="hs_fire_escape",
        label="Fire Escape",
        hotspot_type=HotspotType.OBJECT,
        position=(60, 12),
        description="Rusty ladder leading up.",
        examine_text="Fresh scuff marks. Someone climbed down recently. An escape route?"
    ))

    alley.add_hotspot(Hotspot(
        id="hs_alley_exit",
        label="Back to Street",
        hotspot_type=HotspotType.EXIT,
        position=(10, 16),
        target_id="street"
    ))

    game.add_location(alley)

    game.set_start_location("office")

    # Store mystery details for LLM context
    game.mystery = {
        "culprit": chosen_culprit,
        "motive": chosen_motive,
        "method": chosen_method,
        "victim": "Marcus Webb"
    }

    # Initialize WorldState for consistent LLM generation
    ws = game.state.world_state
    ws.world_genre = "noir mystery"
    ws.world_era = "1940s"
    ws.world_rules = [
        "Rain is constant in this city",
        "Everyone has secrets",
        "Trust is earned, not given",
        "The night hides many sins"
    ]

    # Set the main mystery in world state
    ws.set_main_mystery({
        "victim": "Marcus Webb",
        "crime": "murder",
        "location": "alley behind O'Malley's Bar",
        "suspects": ["Mickey O'Malley (bartender)", "Sally Malone (informant)", "Councilman Harrow"],
        "culprit_id": chosen_culprit,  # Hidden from NPCs
    })

    # Register initial locations
    for loc_id, loc in game.state.locations.items():
        ws.register_location({
            "id": loc.id,
            "name": loc.name,
            "location_type": "office" if "office" in loc.id else "bar" if "bar" in loc.id else "alley" if "alley" in loc.id else "street",
            "description": loc.description,
            "is_outdoor": loc.is_outdoor,
        })

    # Register initial NPCs with relationships
    ws.register_npc({
        "id": "bartender",
        "name": "Mickey O'Malley",
        "description": bartender.description,
        "archetype": bartender.archetype.value,
        "secret": bartender.secret_truth,
        "public_persona": bartender.public_lie,
        "topics": list(bartender.available_topics)
    }, "bar")

    ws.register_npc({
        "id": "informant",
        "name": "Sally 'Whispers' Malone",
        "description": informant.description,
        "archetype": informant.archetype.value,
        "secret": informant.secret_truth,
        "public_persona": informant.public_lie,
        "topics": list(informant.available_topics)
    }, "street")

    ws.register_npc({
        "id": "politician",
        "name": "Councilman Vincent Harrow",
        "description": politician.description,
        "archetype": politician.archetype.value,
        "secret": politician.secret_truth,
        "public_persona": politician.public_lie,
        "topics": list(politician.available_topics)
    }, "office")

    # Set up NPC relationships
    ws.add_npc_relationship("bartender", "informant", "knows")
    ws.add_npc_relationship("politician", "bartender", "customer")
    ws.add_npc_relationship("informant", "politician", "watches")

    # Add initial story facts
    ws.add_fact(
        "victim_found",
        "Marcus Webb was found dead in the alley behind O'Malley's Bar",
        "case file",
        locations=["alley", "bar"]
    )

    ws.add_fact(
        "victim_occupation",
        "Marcus Webb was an accountant who handled books for powerful people",
        "case file",
        npcs=["politician"]
    )

    # Record the murder event (public knowledge)
    ws.record_event(
        "marcus_murder",
        "Marcus Webb was found murdered in the alley",
        "alley",
        npcs=[chosen_culprit],
        is_public=True
    )

    return game


def run_study_escape():
    """Run the Noir Detective scenario."""
    seed = int(time.time() * 1000) % (2**31)
    random.seed(seed)

    print()
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("@@@@@@@@@@GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG@@@@@@@@@@@@")
    print("@@@@@@@@@@G                                               G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ╔═════════════════════════════════════╗    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ║         SHADOWENGINE                ║    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ║     Procedural Noir Detective       ║    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ║                                     ║    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ║   The city never sleeps.            ║    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ║   Neither do you.                   ║    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ╚═════════════════════════════════════╝    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G                                               G@@@@@@@@@@@@")
    print("@@@@@@@@@@GLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLG@@@@@@@@@@@@")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print()
    print("=" * 72)
    print(f"[Game Seed: {seed}]")
    print("=" * 72)
    print()
    print("A body in the alley. A city full of secrets.")
    print("Everyone's got something to hide. Find the truth.")
    print()
    print("Commands: examine [object], talk [person], go [place]")
    print("          threaten, accuse, inventory, wait, help")
    print()
    print("The LLM generates NPC dialogue and narrative dynamically.")
    print("Every playthrough tells a different story.")
    print()
    input("Press Enter to begin your investigation...")

    game = create_study_escape(seed=seed)
    game.run()


if __name__ == "__main__":
    run_study_escape()
