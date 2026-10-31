"""
Every NPC can be brought into the story.

- Testimony: suspects carry leads (witness account, motive, confession)
  that become evidence when they open up — through rapport or pressure.
- The culprit only confesses once cornered; threats without proof make
  them sweat (and run).
- The noir case is solvable end to end, through the real game loop,
  offline, whoever the culprit is.
- NPCs the LLM generates are real, talkable characters, can't overwrite
  the cast, and get woven a piece of the case.
- Navigation found broken in playtesting: exits with articles in their
  names, 'examine back booth', returning to known places by name.
"""

import json
import os
import pytest

from shadowengine.game import Game
from shadowengine.character import Character, Archetype
from shadowengine.render import Location
from shadowengine.interaction import Hotspot, HotspotType
from shadowengine.narrative import (
    NarrativeSpine, ConflictType, TrueResolution, Revelation,
)
from shadowengine.scenarios.study_escape import create_study_escape
from shadowengine.testimony import advance_leads
from shadowengine.config import (
    RAPPORT_TRUST_GAIN, TESTIMONY_TRUST_THRESHOLD,
    CULPRIT_FLEE_HEAT_FRACTION,
)
from shadowengine.llm.client import MockLLMClient, LLMConfig, LLMBackend


SUSPECT_SHORT = {"bartender": "mickey", "informant": "sally", "politician": "harrow"}

# Questions that touch each suspect's topics (three earns enough rapport)
RAPPORT_QUESTIONS = {
    "bartender": [
        "Did you know marcus webb?",
        "What happened that night?",
        "Who are your regulars?",
    ],
    "informant": [
        "What's on the streets?",
        "Any rumors about marcus?",
        "Who should I trust?",
    ],
    "politician": [
        "Tell me about marcus webb.",
        "How's city business?",
        "Who are your connections?",
    ],
}


@pytest.fixture(autouse=True)
def offline_llm(monkeypatch):
    """Every subsystem gets the mock backend: no network, fallbacks only."""
    monkeypatch.setenv("LLM_BACKEND", "mock")


def seed_for(culprit: str) -> int:
    for seed in range(1, 500):
        if create_study_escape(seed=seed).state.spine.true_resolution.culprit_id == culprit:
            return seed
    raise AssertionError(f"no seed picks {culprit}")


def noir(culprit: str) -> Game:
    game = create_study_escape(seed=seed_for(culprit))
    game.renderer.use_clear = False
    game.renderer.wait_for_key = lambda prompt="": None
    return game


def drive(game: Game, inputs: list[str]) -> None:
    """Play through the real game loop with scripted input."""
    queue = list(inputs)
    game.renderer.render_prompt = lambda: queue.pop(0)
    game.renderer.render_dialogue_prompt = lambda speaker: queue.pop(0)
    while queue and game.state.is_running:
        if game.state.in_conversation:
            game.conversation_manager.conversation_loop(game.state)
        else:
            game._exploration_loop()


def talk_route(suspect_id: str) -> list[str]:
    return [f"talk {SUSPECT_SHORT[suspect_id]}", *RAPPORT_QUESTIONS[suspect_id], "leave"]


def full_investigation(culprit: str) -> list[str]:
    """Interview everyone, work the scenes, then corner the culprit."""
    script = ["take magnifying glass"]
    script += talk_route("politician")
    script += ["go door to street"]
    script += talk_route("informant")
    script += ["go o'malley's bar"]
    script += talk_route("bartender")
    script += ["examine back booth", "go exit to street", "go dark alley",
               "examine chalk outline", "go street"]
    script += {
        "bartender": ["go o'malley's bar"],
        "informant": [],
        "politician": ["go your office building"],
    }[culprit]
    script += [f"talk {SUSPECT_SHORT[culprit]}", "show chalk", "threaten", "accuse"]
    return script


def discovery_sources(game: Game) -> dict[str, str]:
    return {
        fact_id: d.source
        for fact_id, d in game.state.memory.player.discoveries.items()
    }


# ============================================================
# The case is solvable — whoever did it
# ============================================================

@pytest.mark.integration
class TestCaseIsSolvable:

    @pytest.mark.parametrize("culprit", ["bartender", "informant", "politician"])
    def test_full_playthrough_solves_case(self, culprit):
        game = noir(culprit)
        drive(game, full_investigation(culprit))

        spine = game.state.spine
        assert spine.is_solved
        assert game.state.is_running is False
        assert spine.revealed_facts == {
            "witness_account", "physical_evidence", "motive_revealed", "confession",
        }

    @pytest.mark.parametrize("culprit", ["bartender", "informant", "politician"])
    def test_every_suspect_brings_something(self, culprit):
        """Each innocent suspect's testimony lands in the case file."""
        game = noir(culprit)
        innocents = [c for c in SUSPECT_SHORT if c != culprit]
        for suspect in innocents:
            assert game.state.characters[suspect].leads, f"{suspect} knows nothing"

        # Interview each innocent on their own, before anyone else talks
        for suspect in innocents:
            fresh = noir(culprit)
            location = fresh.state.characters[suspect].state.location
            fresh.state.current_location_id = location
            drive(fresh, talk_route(suspect))
            sources = discovery_sources(fresh)
            name = fresh.state.characters[suspect].name
            for lead in fresh.state.characters[suspect].leads:
                assert sources.get(lead) == f"{name}'s testimony", (suspect, lead)

    @pytest.mark.parametrize("culprit", ["bartender", "informant", "politician"])
    def test_each_chain_lead_has_an_innocent_source(self, culprit):
        game = noir(culprit)
        innocent_leads = {
            lead
            for cid, c in game.state.characters.items() if cid != culprit
            for lead in c.leads
        }
        assert {"witness_account", "motive_revealed"} <= innocent_leads
        assert set(game.state.characters[culprit].leads) == {"motive_revealed", "confession"}


# ============================================================
# Rapport and testimony
# ============================================================

@pytest.mark.integration
class TestRapport:

    def test_topic_question_builds_trust_once(self):
        game = noir("informant")
        mickey = game.state.characters["bartender"]
        cm = game.conversation_manager
        cm.handle_free_dialogue(mickey, "What happened that night?", game.state)
        assert mickey.current_trust == RAPPORT_TRUST_GAIN
        cm.handle_free_dialogue(mickey, "Seriously, that night?", game.state)
        assert mickey.current_trust == RAPPORT_TRUST_GAIN

    def test_offtopic_chatter_builds_nothing(self):
        game = noir("informant")
        mickey = game.state.characters["bartender"]
        game.conversation_manager.handle_free_dialogue(
            mickey, "Nice weather we're having.", game.state,
        )
        assert mickey.current_trust == 0

    def test_testimony_arrives_once_trust_is_earned(self):
        game = noir("informant")
        game.state.current_location_id = "bar"
        drive(game, ["talk mickey", "Did you know marcus webb?", "What happened that night?"])
        assert not game.state.memory.player.has_discovered("witness_account")

        drive(game, ["Who are your regulars?"])
        assert game.state.characters["bartender"].current_trust >= TESTIMONY_TRUST_THRESHOLD
        discovery = game.state.memory.player.discoveries["witness_account"]
        assert "Sally Malone" in discovery.description   # names the real culprit
        assert discovery.is_evidence
        assert "witness_account" in game.state.spine.revealed_facts

    def test_cracked_innocent_testifies(self):
        game = noir("informant")
        mickey = game.state.characters["bartender"]
        cm = game.conversation_manager
        for _ in range(3):
            if mickey.state.is_cracked:
                break
            cm.handle_threaten(mickey, game.state)
        assert mickey.state.is_cracked
        assert game.state.memory.player.has_discovered("witness_account")

    def test_culprit_never_volunteers(self):
        game = noir("bartender")
        mickey = game.state.characters["bartender"]
        mickey.current_trust = 100
        assert game.conversation_manager.offer_testimony(mickey, game.state) == []

    def test_testimony_given_only_once(self):
        game = noir("informant")
        mickey = game.state.characters["bartender"]
        mickey.current_trust = TESTIMONY_TRUST_THRESHOLD
        cm = game.conversation_manager
        assert cm.offer_testimony(mickey, game.state) == ["witness_account"]
        assert cm.offer_testimony(mickey, game.state) == []

    def test_leads_cascade_when_prerequisites_land(self):
        """Motive heard early stays pending until the scene is worked."""
        game = noir("informant")
        harrow = game.state.characters["politician"]
        harrow.current_trust = TESTIMONY_TRUST_THRESHOLD
        game.conversation_manager.offer_testimony(harrow, game.state)

        spine = game.state.spine
        assert game.state.memory.player.has_discovered("motive_revealed")
        assert "motive_revealed" not in spine.revealed_facts  # needs the scene

        game.state.current_location_id = "bar"
        drive(game, talk_route("bartender"))      # the witness account
        game.state.current_location_id = "alley"
        drive(game, ["examine chalk outline"])
        assert {"witness_account", "physical_evidence", "motive_revealed"} <= spine.revealed_facts

    def test_dialogue_prompt_carries_case_knowledge(self):
        """An LLM-voiced witness knows what they're holding back."""
        class Recording(MockLLMClient):
            def chat(self, messages):
                self.messages = messages
                return super().chat(messages)

        game = noir("informant")
        llm = Recording(LLMConfig(backend=LLMBackend.MOCK))
        game.conversation_manager.dialogue_handler.llm_client = llm
        mickey = game.state.characters["bartender"]
        game.conversation_manager.generate_dialogue(mickey, "hello", game.state)
        system = llm.messages[0]["content"]
        assert "WHAT YOU KNOW ABOUT THE CASE" in system
        assert "back booth" in system and "Sally Malone" in system

    def test_culprit_prompt_has_no_case_knowledge_section(self):
        class Recording(MockLLMClient):
            def chat(self, messages):
                self.messages = messages
                return super().chat(messages)

        game = noir("bartender")
        llm = Recording(LLMConfig(backend=LLMBackend.MOCK))
        game.conversation_manager.dialogue_handler.llm_client = llm
        mickey = game.state.characters["bartender"]
        game.conversation_manager.generate_dialogue(mickey, "hello", game.state)
        assert "WHAT YOU KNOW ABOUT THE CASE" not in llm.messages[0]["content"]


@pytest.mark.integration
class TestVoicing:

    def make(self, reply):
        game = noir("informant")
        mock = MockLLMClient(LLMConfig(backend=LLMBackend.MOCK))
        mock.set_response("What you know:", reply)
        game.conversation_manager.testimony.llm_client = mock
        return game

    def test_llm_voices_the_testimony(self):
        line = "Sally Malone sat with Marcus in my back booth. They walked out together."
        game = self.make(line)
        mickey = game.state.characters["bartender"]
        fact = "Marcus Webb spent his last night with Sally Malone."
        assert game.conversation_manager.testimony.voice(mickey, fact, game.state) == line

    def test_voicing_that_drops_the_name_falls_back_to_truth(self):
        game = self.make("Some dame sat with Marcus. That's all I know.")
        mickey = game.state.characters["bartender"]
        fact = "Marcus Webb spent his last night with Sally Malone."
        assert game.conversation_manager.testimony.voice(mickey, fact, game.state) == fact

    def test_case_file_keeps_ground_truth(self):
        game = self.make("Sally Malone. Back booth. Ugly night.")
        mickey = game.state.characters["bartender"]
        mickey.current_trust = TESTIMONY_TRUST_THRESHOLD
        game.conversation_manager.offer_testimony(mickey, game.state)
        recorded = game.state.memory.player.discoveries["witness_account"].description
        assert recorded == game.state.spine.get_revelation("witness_account").testimony


# ============================================================
# The culprit holds until cornered
# ============================================================

@pytest.mark.integration
class TestCulpritCornered:

    def test_threats_without_proof_dont_break_the_culprit(self):
        game = noir("bartender")
        mickey = game.state.characters["bartender"]
        cm = game.conversation_manager
        for _ in range(4):
            cm.handle_threaten(mickey, game.state)
        assert not mickey.state.is_cracked
        assert mickey.state.pressure_accumulated == mickey.trust_threshold - 1
        assert not game.state.memory.player.has_discovered("confession")

    def test_sweating_culprit_starts_to_run(self):
        game = noir("bartender")
        game.state.current_location_id = "bar"
        drive(game, ["talk mickey", "threaten", "threaten", "leave", "wait"])
        mickey = game.state.characters["bartender"]
        assert not mickey.state.is_cracked
        assert mickey.state.pressure_accumulated >= CULPRIT_FLEE_HEAT_FRACTION * mickey.trust_threshold
        assert game.npc_agency.flee_deadline is not None

    def test_cornered_culprit_confesses(self):
        game = noir("bartender")
        spine = game.state.spine
        for lead in ("witness_account", "physical_evidence"):
            game.state.memory.player_discovers(
                fact_id=lead, description=lead, location="alley",
                source="test", is_evidence=True,
            )
        advance_leads(game.state)
        assert spine.revealed_facts == {"witness_account", "physical_evidence"}

        mickey = game.state.characters["bartender"]
        cm = game.conversation_manager
        for _ in range(3):
            if mickey.state.is_cracked:
                break
            cm.handle_threaten(mickey, game.state)
        assert mickey.state.is_cracked
        sources = discovery_sources(game)
        assert sources["confession"] == "Mickey O'Malley's confession"
        assert sources["motive_revealed"] == "Mickey O'Malley's confession"
        assert spine.revealed_facts >= {"motive_revealed", "confession"}

        cm.handle_accuse(mickey, game.state)
        assert spine.is_solved

    def test_confession_reads_cleanly(self):
        game = noir("bartender")
        secret = game.state.characters["bartender"].secret_truth
        assert secret.startswith("I killed Marcus Webb. ")
        assert "I used" not in secret


# ============================================================
# Generated NPCs are real, talkable, and part of the case
# ============================================================

def location_json(**overrides):
    data = {
        "id": "docks",
        "name": "The Docks",
        "description": "Fog rolls over black water.",
        "location_type": "street",
        "is_outdoor": True,
        "ambient": "Gulls. Rope creaking.",
        "hotspots": [],
        "npcs": [],
        "connections": {},
    }
    data.update(overrides)
    return json.dumps(data)


def generated(game: Game, **overrides) -> Location:
    location = game.location_manager.parse_location_response(
        location_json(**overrides), "docks", "the docks",
        game.state.locations["street"], game.state, game.add_character,
    )
    game.state.locations[location.id] = location
    return location


def people(location: Location) -> list[Hotspot]:
    return [h for h in location.hotspots if h.hotspot_type == HotspotType.PERSON]


@pytest.mark.integration
class TestGeneratedNPCs:

    def test_person_hotspot_without_character_becomes_one(self):
        game = noir("informant")
        location = generated(game, hotspots=[{
            "id": "hs_fisherman", "label": "Old Fisherman", "type": "person",
            "description": "Mending nets by lamplight.", "character_id": None,
        }])
        (hotspot,) = people(location)
        assert hotspot.target_id in game.state.characters
        assert game.state.characters[hotspot.target_id].name == "Old Fisherman"

    def test_generated_npc_cannot_overwrite_the_cast(self):
        game = noir("informant")
        original = game.state.characters["bartender"]
        location = generated(game, npcs=[{
            "id": "bartender", "name": "Joe Kowalski", "archetype": "survivor",
            "description": "Runs the dockside shack.",
        }])
        assert game.state.characters["bartender"] is original
        assert original.leads == ["witness_account"]
        (hotspot,) = people(location)
        assert hotspot.target_id != "bartender"
        assert game.state.characters[hotspot.target_id].name == "Joe Kowalski"

    def test_hotspot_and_npc_entry_make_one_person(self):
        game = noir("informant")
        location = generated(
            game,
            hotspots=[{"id": "hs_joe", "label": "Joe", "type": "person",
                       "character_id": "npc_joe"}],
            npcs=[{"id": "npc_joe", "name": "Joe", "description": "A dockhand."}],
        )
        assert len(people(location)) == 1
        assert people(location)[0].target_id == "npc_joe"

    def test_known_character_is_not_cloned(self):
        game = noir("informant")
        before = len(game.state.characters)
        location = generated(game, npcs=[{
            "id": "npc_mickey", "name": "Mickey O'Malley", "description": "Again?",
        }])
        assert len(game.state.characters) == before
        assert people(location) == []   # he's still behind his bar

    def test_newcomer_is_woven_into_the_case(self):
        game = noir("informant")
        location = generated(game, npcs=[{
            "id": "npc_joe", "name": "Joe", "description": "A dockhand.",
            "topics": ["the docks", "night shift", "the fog"],
        }])
        joe = game.state.characters[people(location)[0].target_id]
        assert len(joe.leads) == 1
        assert joe.leads[0] in {"witness_account", "motive_revealed"}

    def test_newcomers_spread_across_leads(self):
        game = noir("informant")
        location = generated(game, npcs=[
            {"id": "npc_a", "name": "Ada", "description": "x"},
            {"id": "npc_b", "name": "Bo", "description": "y"},
        ])
        leads = [game.state.characters[h.target_id].leads[0] for h in people(location)]
        assert sorted(leads) == ["motive_revealed", "witness_account"]

    def test_culprit_only_leads_are_never_woven(self):
        game = noir("informant")
        location = generated(game, npcs=[
            {"id": f"npc_{i}", "name": f"Stranger {i}", "description": "z"}
            for i in range(5)
        ])
        for hotspot in people(location):
            assert "confession" not in game.state.characters[hotspot.target_id].leads

    def test_walk_in_meet_and_hear_testimony(self):
        """Through the real loop: a generated stranger testifies."""
        game = noir("informant")
        mock = MockLLMClient(LLMConfig(backend=LLMBackend.MOCK))
        mock.set_response("Generate a new location", location_json(npcs=[{
            "id": "npc_joe", "name": "Dockhand Joe", "archetype": "innocent",
            "description": "Wiry, nervous, smells of tar.",
            "topics": ["the docks", "night shift", "the fog"],
        }]))
        game.location_manager.llm_client = mock
        game.state.current_location_id = "street"

        drive(game, ["go to the docks"])
        assert game.state.current_location_id == "docks"

        drive(game, [
            "talk joe",
            "How are the docks tonight?",
            "Working the night shift?",
            "Thick fog, huh?",
        ])
        joe = next(c for c in game.state.characters.values() if c.name == "Dockhand Joe")
        lead = joe.leads[0]
        discovery = game.state.memory.player.discoveries[lead]
        assert discovery.source == "Dockhand Joe's testimony"

    def test_generated_npc_can_be_framed_or_talked_to(self):
        """A woven newcomer is in the propagation network like everyone else."""
        game = noir("informant")
        location = generated(game, npcs=[{"id": "npc_joe", "name": "Joe", "description": "d"}])
        joe_id = people(location)[0].target_id
        assert game.state.propagation_engine.get_npc_state(joe_id) is not None


# ============================================================
# Navigation and naming
# ============================================================

@pytest.mark.integration
class TestNavigation:

    def test_exit_with_article_in_label(self):
        game = noir("informant")
        drive(game, ["go door to street"])
        assert game.state.current_location_id == "street"

    def test_examine_back_booth_is_not_a_zoom_out(self):
        game = noir("informant")
        game.state.current_location_id = "bar"
        drive(game, ["examine back booth"])
        assert game.state.memory.player.has_discovered("booth_napkin")

    def test_napkin_is_a_clue_not_the_eyewitness(self):
        """Examining the booth first must not silence the real witness."""
        game = noir("informant")
        game.state.current_location_id = "bar"
        drive(game, ["examine back booth"])
        assert not game.state.memory.player.has_discovered("witness_account")
        drive(game, talk_route("bartender"))
        assert discovery_sources(game)["witness_account"] == "Mickey O'Malley's testimony"

    def test_step_back_still_zooms_out(self):
        game = noir("informant")
        assert game.inspection_manager.wants_inspection("step back")
        assert game.inspection_manager.wants_inspection("zoom out")
        assert not game.inspection_manager.wants_inspection("examine back booth")

    @pytest.mark.parametrize("phrase", ["go office", "go your office building", "go to your office"])
    def test_return_to_known_place_by_name(self, phrase):
        game = noir("informant")
        game.state.current_location_id = "street"
        drive(game, [phrase])
        assert game.state.current_location_id == "office"
        assert "office_2" not in game.state.locations

    def test_unknown_place_is_still_generated(self):
        game = noir("informant")
        game.state.current_location_id = "street"
        drive(game, ["go to the train station"])
        assert game.state.current_location_id not in ("office", "street", "bar", "alley")

    @pytest.mark.parametrize("phrase", ["talk vincent harrow", "talk councilman", "talk politician"])
    def test_talk_by_any_part_of_name_or_role(self, phrase):
        game = noir("informant")
        drive(game, [phrase])
        assert game.state.in_conversation
        assert game.state.conversation_partner == "politician"

    def test_show_evidence_by_where_it_was_found(self):
        game = noir("informant")
        game.state.current_location_id = "alley"
        drive(game, ["examine chalk outline"])
        found = game.conversation_manager._find_discovery("chalk", game.state)
        assert found is not None and found.fact_id == "physical_evidence"


# ============================================================
# Persistence
# ============================================================

@pytest.mark.integration
class TestPersistence:

    def test_leads_and_testimony_survive_save_and_load(self, tmp_path):
        game = noir("politician")
        path = str(tmp_path / "case.json")
        game.save_system.save(path)

        resumed = noir("informant")   # a different case, overwritten by the load
        resumed.save_system.load(path)

        assert resumed.state.spine.true_resolution.culprit_id == "politician"
        for cid, character in game.state.characters.items():
            assert resumed.state.characters[cid].leads == character.leads
        assert (
            resumed.state.spine.get_revelation("witness_account").testimony
            == game.state.spine.get_revelation("witness_account").testimony
        )

    def test_resumed_case_still_solvable(self, tmp_path):
        game = noir("politician")
        drive(game, talk_route("politician") + ["go door to street"])
        path = str(tmp_path / "mid_case.json")
        game.save_system.save(path)

        resumed = noir("informant")
        resumed.save_system.load(path)
        resumed.renderer.use_clear = False
        resumed.renderer.wait_for_key = lambda prompt="": None
        script = full_investigation("politician")
        # Already interviewed Harrow and stepped outside
        script = script[script.index("talk sally"):]
        drive(resumed, script)
        assert resumed.state.spine.is_solved

    def test_old_saves_without_leads_still_load(self):
        data = Character(
            id="x", name="X", archetype=Archetype.INNOCENT,
        ).to_dict()
        del data["leads"]
        assert Character.from_dict(data).leads == []
        rev = Revelation(id="r", description="d", importance=1).to_dict()
        del rev["testimony"]
        assert Revelation.from_dict(rev).testimony == ""


@pytest.mark.integration
class TestKnownPlaceRanking:

    def test_office_beats_generated_side_street(self):
        """A fallback 'office_north' must not hijack 'go office'."""
        game = noir("informant")
        game.state.current_location_id = "office"
        drive(game, ["north"])                 # generates office_north (fallback)
        assert game.state.current_location_id == "office_north"
        drive(game, ["go office"])
        assert game.state.current_location_id == "office"

    def test_side_street_reachable_by_its_own_name(self):
        game = noir("informant")
        game.state.current_location_id = "office"
        drive(game, ["north", "go street"])
        assert game.state.current_location_id == "street"


@pytest.mark.integration
class TestBareDirections:

    @pytest.mark.parametrize("word", ["north", "n"])
    def test_bare_direction_moves(self, word):
        game = noir("informant")
        game.state.current_location_id = "office"
        drive(game, [word])
        assert game.state.current_location_id == "office_north"
