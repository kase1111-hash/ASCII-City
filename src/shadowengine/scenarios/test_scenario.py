"""
Test Scenario - A simple mystery for testing Phase 1.

The Missing Heirloom:
A valuable family heirloom has been stolen from the study.
Three suspects: the Butler, the Maid, and the Guest.
The Butler did it, motivated by gambling debts.
"""

from ..game import Game
from ..character import Character, Archetype
from ..narrative import NarrativeSpine, SpineGenerator, ConflictType, TrueResolution, Revelation
from ..render import Location
from ..interaction import Hotspot, HotspotType


def create_test_scenario(seed: int = None) -> Game:
    """
    Create a simple test scenario: The Missing Heirloom.

    A playable mystery with:
    - 1 main location (the study)
    - 3 NPCs (butler, maid, guest)
    - Several clues to find
    - A solvable mystery
    """
    game = Game()
    game.new_game(seed=seed)

    # Create the narrative spine
    spine = NarrativeSpine(
        conflict_type=ConflictType.THEFT,
        conflict_description="The family heirloom - a golden pocket watch - has been stolen from the study.",
        true_resolution=TrueResolution(
            culprit_id="butler",
            motive="gambling debts - he owes money to dangerous people",
            method="took it while cleaning the study alone",
            opportunity="was alone in the study this morning",
            evidence_chain=["butler_alone", "gambling_debts", "hidden_pawn_ticket"]
        ),
        revelations=[
            Revelation(
                id="butler_alone",
                description="The butler was alone in the study this morning",
                importance=2,
                source="Ask the maid about the morning routine"
            ),
            Revelation(
                id="gambling_debts",
                description="The butler has significant gambling debts",
                importance=3,
                prerequisites=["butler_alone"],
                source="Examine the butler's quarters or pressure him"
            ),
            Revelation(
                id="hidden_pawn_ticket",
                description="A pawn shop ticket hidden in the butler's coat",
                importance=3,
                prerequisites=["gambling_debts"],
                source="Search the butler's belongings"
            )
        ],
        twist_probability=0.0
    )
    game.set_spine(spine)

    # Create characters
    butler = Character(
        id="butler",
        name="Mr. Blackwood",
        archetype=Archetype.GUILTY,
        description="The family butler, impeccably dressed but with worried eyes.",
        secret_truth="I took the watch to pay off my gambling debts. I was desperate!",
        public_lie="I was polishing silver all morning. I never touched the watch.",
        role_in_spine="culprit",
        trust_threshold=40,
        initial_location="study"
    )
    butler.add_topic("morning routine")
    butler.add_topic("the watch")
    butler.add_topic("other staff")
    butler.add_knowledge("study_layout")
    game.add_character(butler)

    maid = Character(
        id="maid",
        name="Mrs. Chen",
        archetype=Archetype.INNOCENT,
        description="The household maid, observant and somewhat nervous.",
        secret_truth="I saw Mr. Blackwood acting strangely this morning, but I'm afraid to say.",
        public_lie="",  # She doesn't lie, just withholds
        role_in_spine="witness",
        trust_threshold=20,
        initial_location="study"
    )
    maid.add_topic("morning routine")
    maid.add_topic("the watch")
    maid.add_topic("the butler")
    maid.add_knowledge("butler_alone")
    game.add_character(maid)

    guest = Character(
        id="guest",
        name="Lord Pemberton",
        archetype=Archetype.OUTSIDER,
        description="A visiting nobleman, seems uncomfortable with the situation.",
        secret_truth="I was actually here to buy the watch legitimately, but now I look suspicious.",
        public_lie="I barely noticed the watch. I'm here on unrelated business.",
        role_in_spine="red_herring",
        trust_threshold=35,
        initial_location="study"
    )
    guest.add_topic("your visit")
    guest.add_topic("the watch")
    guest.add_topic("the household")
    game.add_character(guest)

    # Create the study location
    study = Location(
        id="study",
        name="The Study",
        description="A wood-paneled study filled with books and curios. An empty display case sits prominently on the desk - where the heirloom watch once rested.",
        art=[
            "    ╔═══════════════════════════════════════════╗",
            "    ║  ┌─────┐   ╭───────╮   ┌─────┐           ║",
            "    ║  │BOOKS│   │DISPLAY│   │BOOKS│   ☐ ☐    ║",
            "    ║  │     │   │ CASE  │   │     │  WINDOW  ║",
            "    ║  └─────┘   ╰───────╯   └─────┘           ║",
            "    ║                                          ║",
            "    ║    @          @           @              ║",
            "    ║  BUTLER     MAID       GUEST             ║",
            "    ║                                          ║",
            "    ║        ┌─────────────┐                   ║",
            "    ║        │    DESK     │                   ║",
            "    ║        └─────────────┘                   ║",
            "    ╚═══════════════════════════════════════════╝",
        ],
        is_outdoor=False,
        ambient_description="Dust motes float in the light from the window. The room feels tense."
    )

    # Add hotspots to the study
    study.add_hotspot(Hotspot.create_person(
        id="hs_butler",
        name="Mr. Blackwood (Butler)",
        position=(10, 7),
        character_id="butler",
        description="The butler stands stiffly, hands clasped. He avoids eye contact."
    ))

    study.add_hotspot(Hotspot.create_person(
        id="hs_maid",
        name="Mrs. Chen (Maid)",
        position=(20, 7),
        character_id="maid",
        description="The maid wrings her hands nervously, glancing at the butler."
    ))

    study.add_hotspot(Hotspot.create_person(
        id="hs_guest",
        name="Lord Pemberton (Guest)",
        position=(32, 7),
        character_id="guest",
        description="The nobleman stands apart from the servants, looking uncomfortable."
    ))

    study.add_hotspot(Hotspot(
        id="hs_display_case",
        label="Empty Display Case",
        hotspot_type=HotspotType.EVIDENCE,
        position=(22, 3),
        description="A velvet-lined case, now empty. The watch was kept here.",
        examine_text="The display case is empty. Fine scratches suggest the watch was removed hastily, not carefully lifted.",
        reveals_fact="hasty_removal"
    ))

    study.add_hotspot(Hotspot(
        id="hs_desk",
        label="Desk",
        hotspot_type=HotspotType.OBJECT,
        position=(22, 11),
        description="A large mahogany desk covered in papers.",
        examine_text="Among the papers, you find a cleaning schedule. It shows Mr. Blackwood was assigned to clean the study alone this morning."
    ))

    study.add_hotspot(Hotspot(
        id="hs_butler_coat",
        label="Butler's Coat Rack",
        hotspot_type=HotspotType.EVIDENCE,
        position=(5, 5),
        description="A coat rack near the door with Mr. Blackwood's jacket.",
        examine_text="Searching the coat pockets, you find a crumpled pawn shop ticket dated yesterday. It's for a 'gold pocket watch - family heirloom type.'",
        reveals_fact="hidden_pawn_ticket",
        requires_discovery="butler_alone"  # Can only find this after learning he was alone
    ))

    study.add_hotspot(Hotspot(
        id="hs_window",
        label="Window",
        hotspot_type=HotspotType.OBJECT,
        position=(42, 3),
        description="A window overlooking the garden.",
        examine_text="The window is locked from the inside. No one could have entered this way."
    ))

    game.add_location(study)
    game.set_start_location("study")

    return game


def run_test_scenario():
    """Run the test scenario."""
    print("Creating test scenario: The Missing Heirloom")
    print("=" * 50)
    print()
    print("A valuable family heirloom has been stolen!")
    print("Investigate the study, talk to the suspects,")
    print("and find the truth.")
    print()
    print("Commands: examine, talk, take, accuse, threaten")
    print("Type 'help' for more commands.")
    print()
    input("Press Enter to begin...")

    game = create_test_scenario()
    game.run()


if __name__ == "__main__":
    run_test_scenario()
