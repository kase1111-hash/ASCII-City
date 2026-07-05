"""
Integration tests for the evolving-world round:

- The culprit plants false evidence framing another suspect
- Close inspection exposes the staging (the counter to a frame-up)
- Tampering makes the culprit nervous
- StreetTalk: NPCs voice rumor-network knowledge unprompted
"""

import json
import pytest

from shadowengine.game import Game
from shadowengine.character import Character, Archetype, Mood
from shadowengine.render import Location
from shadowengine.interaction import Hotspot, HotspotType
from shadowengine.narrative import (
    NarrativeSpine, ConflictType, TrueResolution, Revelation,
)
from shadowengine.config import EVIDENCE_TAMPER_DELAY_UNITS
from shadowengine.street_talk import StreetTalk, REMARK_COOLDOWN_UNITS
from shadowengine.llm.client import (
    LLMClient, LLMConfig, LLMResponse, LLMBackend, MockLLMClient,
)


MEDIUM_JSON = json.dumps({
    "description": "One baseboard behind the desk sits loose.",
    "detail_hooks": ["the loose baseboard"],
    "discovery": None,
})
CLOSE_JSON = json.dumps({
    "description": "Behind the loose baseboard, dark metal catches the light.",
    "detail_hooks": ["the loose baseboard"],
    "discovery": {
        "fact_id": "hidden_black_box",
        "description": "A wire recorder hidden behind the baseboard.",
        "is_evidence": True,
        "reveals_object": {
            "label": "Black Box",
            "type": "evidence",
            "description": "A matte-black wire recorder.",
        },
    },
})
HANKY_JSON = json.dumps({
    "description": "Fine silk, barely used. The monogram thread is brighter than the fabric around it.",
    "detail_hooks": ["the bright monogram"],
    "discovery": None,
})


class DeadLLM(LLMClient):
    def check_availability(self):
        return False

    def generate(self, prompt, system=None):
        return LLMResponse.error_response("connection refused")


class ForcedRandom:
    """Deterministic stand-in for random.Random."""

    def __init__(self, value: float):
        self.value = value

    def random(self):
        return self.value

    def choice(self, seq):
        return seq[0]


def make_game(plant=True):
    game = Game()
    game.renderer.wait_for_key = lambda prompt="": None

    llm = MockLLMClient(LLMConfig(backend=LLMBackend.MOCK))
    # Object-specific response first: MockLLMClient matches in insertion order
    llm.set_response("Handkerchief", HANKY_JSON)
    llm.set_response("ARM'S LENGTH", MEDIUM_JSON)
    llm.set_response("INCHES AWAY", CLOSE_JSON)
    llm.set_response("UNDER MAGNIFICATION", CLOSE_JSON)
    game.llm_client = llm
    game.command_handler.llm_client = llm
    game.inspection_manager.detail_handler.llm_client = llm

    room = Location(id="room", name="Back Room", description="A cramped back room.")
    room.add_hotspot(Hotspot(
        id="hs_desk",
        label="Oak Desk",
        hotspot_type=HotspotType.OBJECT,
        position=(10, 10),
        description="A battered oak desk.",
        examine_text="A battered oak desk covered in papers.",
    ))
    room.add_hotspot(Hotspot.create_person(
        id="hs_watcher",
        name="The Watcher",
        position=(20, 10),
        character_id="watcher",
        description="A gaunt man watching from the corner.",
    ))
    game.add_location(room)
    game.set_start_location("room")

    game.add_character(Character(
        id="watcher", name="The Watcher",
        archetype=Archetype.SURVIVOR,
        description="A gaunt man with restless hands.",
    ))
    game.add_character(Character(
        id="barfly", name="Eddie the Barfly",
        archetype=Archetype.INNOCENT,
        description="A harmless regular who talks too much.",
    ))

    game.set_spine(NarrativeSpine(
        conflict_type=ConflictType.MURDER,
        conflict_description="A test case.",
        true_resolution=TrueResolution(
            culprit_id="watcher", motive="m", method="x", opportunity="o",
            evidence_chain=["scene_lead"],
        ),
        revelations=[Revelation(
            id="scene_lead", description="This room holds the answer",
            importance=2, location_id="room",
        )],
    ))

    game.state.evidence_watch.rng = ForcedRandom(0.0 if plant else 1.0)
    return game


def run(game, text):
    state = game.state
    location = state.locations[state.current_location_id]
    context = {
        "targets": [h.label for h in location.get_visible_hotspots()],
        "hotspots": [
            {"label": h.label, "type": h.hotspot_type.value}
            for h in location.get_visible_hotspots()
        ],
    }
    command = game.parser.parse(text, context)
    game.command_handler.handle_command(
        command, context, state, game.config, game.add_character,
    )


def tamper_cycle(game):
    """Find evidence witnessed, leave, let the culprit act."""
    run(game, "look closer at the desk")
    run(game, "look closer")
    game.state.memory.advance_time(EVIDENCE_TAMPER_DELAY_UNITS + 1)
    game.state.current_location_id = "elsewhere"
    game.state.evidence_watch.update(game.state, game.renderer)
    game.state.current_location_id = "room"


# ============================================================
# Evidence planting
# ============================================================

@pytest.mark.integration
class TestEvidencePlanting:

    def test_culprit_plants_false_evidence(self):
        game = make_game(plant=True)
        tamper_cycle(game)

        room = game.state.locations["room"]
        planted = room.get_hotspot_by_label("Monogrammed Handkerchief")
        assert planted is not None
        assert planted.planted_by == "watcher"
        assert planted.frames == "barfly"
        assert planted.hotspot_type == HotspotType.EVIDENCE

    def test_no_plant_when_dice_say_no(self):
        game = make_game(plant=False)
        tamper_cycle(game)
        room = game.state.locations["room"]
        assert room.get_hotspot_by_label("Monogrammed Handkerchief") is None

    def test_planting_recorded_as_world_truth(self):
        game = make_game(plant=True)
        tamper_cycle(game)
        assert any(
            "planted" in e.description.lower() and "watcher" in e.actors
            for e in game.state.memory.world.events
        )

    def test_return_narration_mentions_plant(self, capsys):
        game = make_game(plant=True)
        tamper_cycle(game)
        capsys.readouterr()
        game.state.evidence_watch.update(game.state, game.renderer)
        output = capsys.readouterr().out
        assert "wasn't here before" in output

    def test_examining_plant_implicates_framed_suspect(self):
        game = make_game(plant=True)
        tamper_cycle(game)
        game.state.evidence_watch.update(game.state, game.renderer)

        run(game, "examine monogrammed handkerchief")
        frame_facts = [
            d for d in game.state.memory.player.discoveries.values()
            if d.fact_id.startswith("frame_barfly")
        ]
        assert len(frame_facts) == 1
        assert "Eddie the Barfly" in frame_facts[0].description

    def test_magnified_inspection_exposes_the_staging(self):
        game = make_game(plant=True)
        tamper_cycle(game)
        game.state.evidence_watch.update(game.state, game.renderer)
        game.state.inventory.append("magnifying glass")

        # The glass steps closer each use; the second use reaches FINE,
        # where the staging tell lives
        run(game, "use magnifying glass on the handkerchief")
        run(game, "use magnifying glass on the handkerchief")

        staged = [
            d for d in game.state.memory.player.discoveries.values()
            if d.fact_id.startswith("staged_")
        ]
        assert len(staged) == 1
        assert staged[0].is_evidence
        assert "planted" in staged[0].description.lower()

    def test_culprit_goes_nervous_after_tampering(self):
        game = make_game(plant=True)
        assert game.state.characters["watcher"].state.mood != Mood.NERVOUS
        tamper_cycle(game)
        assert game.state.characters["watcher"].state.mood == Mood.NERVOUS


# ============================================================
# Street talk
# ============================================================

class StubMemory:
    def __init__(self, summary):
        self.summary = summary


class StubMemoryBank:
    def __init__(self, summaries):
        self._memories = [StubMemory(s) for s in summaries]

    def get_shareable_memories(self, threshold=0.3):
        return self._memories


class StubNPCState:
    def __init__(self, summaries):
        self.memory_bank = StubMemoryBank(summaries)


class StubRumor:
    def __init__(self, claim):
        self.core_claim = claim


class StubRumorPropagation:
    def __init__(self, claims):
        self._claims = claims

    def get_rumors_known_by(self, npc_id):
        return [StubRumor(c) for c in self._claims]


class StubEngine:
    def __init__(self, summaries=(), claims=()):
        self._summaries = list(summaries)
        self.rumor_propagation = StubRumorPropagation(list(claims))

    def get_npc_state(self, npc_id):
        return StubNPCState(self._summaries)


@pytest.mark.integration
class TestStreetTalk:

    def _game_with_knowledge(self, summaries=(), claims=()):
        game = make_game()
        dead = DeadLLM(LLMConfig(backend=LLMBackend.OLLAMA))
        game.street_talk = StreetTalk(dead)
        game.state.propagation_engine = StubEngine(summaries, claims)
        return game

    def test_npc_voices_investigation_rumor(self, capsys):
        game = self._game_with_knowledge(
            summaries=["Player scrutinized the Oak Desk very closely"],
        )
        capsys.readouterr()
        game.street_talk.update(game.state, game.renderer)
        output = capsys.readouterr().out
        assert "The Watcher" in output
        assert "Word travels, detective" in output

    def test_each_item_voiced_only_once(self, capsys):
        game = self._game_with_knowledge(
            summaries=["Player scrutinized the Oak Desk very closely"],
        )
        game.street_talk.update(game.state, game.renderer)
        game.state.memory.advance_time(REMARK_COOLDOWN_UNITS + 1)
        capsys.readouterr()
        game.street_talk.update(game.state, game.renderer)
        assert capsys.readouterr().out.strip() == ""

    def test_cooldown_limits_remarks(self, capsys):
        game = self._game_with_knowledge(
            summaries=[
                "Player scrutinized the Oak Desk very closely",
                "The Black Box disappeared from room",
            ],
        )
        game.street_talk.update(game.state, game.renderer)  # first remark
        capsys.readouterr()
        game.street_talk.update(game.state, game.renderer)  # cooldown blocks
        assert capsys.readouterr().out.strip() == ""

        game.state.memory.advance_time(REMARK_COOLDOWN_UNITS + 1)
        game.street_talk.update(game.state, game.renderer)  # second remark
        assert "Word travels" in capsys.readouterr().out

    def test_mundane_knowledge_stays_quiet(self, capsys):
        game = self._game_with_knowledge(
            summaries=["The weather turned cold last night"],
        )
        capsys.readouterr()
        game.street_talk.update(game.state, game.renderer)
        assert capsys.readouterr().out.strip() == ""

    def test_no_npcs_no_remarks(self, capsys):
        game = self._game_with_knowledge(
            summaries=["Player scrutinized the Oak Desk very closely"],
        )
        room = game.state.locations["room"]
        for hs in room.hotspots:
            if hs.hotspot_type == HotspotType.PERSON:
                hs.deactivate()
        capsys.readouterr()
        game.street_talk.update(game.state, game.renderer)
        assert capsys.readouterr().out.strip() == ""
