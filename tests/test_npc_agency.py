"""
Integration tests for NPC agency:

- Culprit relocates under moderate heat
- Culprit attempts to flee under high heat (ticking clock)
- Escape ends the game as a cold case; cracking prevents flight
- Framed NPCs bring the player their alibi
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
from shadowengine.config import (
    CULPRIT_FLEE_COUNTDOWN_UNITS, FRAMED_DEFENSE_DELAY_UNITS,
    EVIDENCE_TAMPER_DELAY_UNITS,
)
from shadowengine.llm.client import (
    LLMClient, LLMConfig, LLMResponse, LLMBackend, MockLLMClient,
)


MEDIUM_JSON = json.dumps({
    "description": "One baseboard behind the desk sits loose.",
    "detail_hooks": [],
    "discovery": None,
})
CLOSE_JSON = json.dumps({
    "description": "Behind the loose baseboard, dark metal catches the light.",
    "detail_hooks": [],
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


class DeadLLM(LLMClient):
    def check_availability(self):
        return False

    def generate(self, prompt, system=None):
        return LLMResponse.error_response("connection refused")


class ForcedRandom:
    def __init__(self, value=0.0):
        self.value = value

    def random(self):
        return self.value

    def choice(self, seq):
        return seq[0]


def make_game():
    """Three rooms; culprit 'watcher' in room1; innocent 'barfly' in room2."""
    game = Game()
    game.renderer.wait_for_key = lambda prompt="": None

    llm = MockLLMClient(LLMConfig(backend=LLMBackend.MOCK))
    llm.set_response("ARM'S LENGTH", MEDIUM_JSON)
    llm.set_response("INCHES AWAY", CLOSE_JSON)
    llm.set_response("UNDER MAGNIFICATION", CLOSE_JSON)
    game.llm_client = llm
    game.command_handler.llm_client = llm
    game.inspection_manager.detail_handler.llm_client = llm
    game.npc_agency.llm_client = DeadLLM(LLMConfig(backend=LLMBackend.OLLAMA))
    game.npc_agency.rng = ForcedRandom()

    room1 = Location(id="room1", name="Room One", description="First room.")
    room1.add_hotspot(Hotspot(
        id="hs_desk", label="Oak Desk", hotspot_type=HotspotType.OBJECT,
        position=(10, 10), description="A battered oak desk.",
        examine_text="A battered oak desk covered in papers.",
    ))
    room1.add_hotspot(Hotspot.create_person(
        id="hs_watcher", name="The Watcher", position=(20, 10),
        character_id="watcher", description="A gaunt man in the corner.",
    ))
    room2 = Location(id="room2", name="Room Two", description="Second room.")
    room2.add_hotspot(Hotspot.create_person(
        id="hs_barfly", name="Eddie the Barfly", position=(20, 10),
        character_id="barfly", description="A harmless regular.",
    ))
    room3 = Location(id="room3", name="Room Three", description="Third room.")

    for room in (room1, room2, room3):
        game.add_location(room)
    game.set_start_location("room1")

    game.add_character(Character(
        id="watcher", name="The Watcher", archetype=Archetype.SURVIVOR,
        description="A gaunt man with restless hands.", trust_threshold=40,
    ))
    game.add_character(Character(
        id="barfly", name="Eddie the Barfly", archetype=Archetype.INNOCENT,
        description="A harmless regular who talks too much.",
    ))

    game.set_spine(NarrativeSpine(
        conflict_type=ConflictType.MURDER,
        conflict_description="A test case.",
        true_resolution=TrueResolution(
            culprit_id="watcher", motive="m", method="x", opportunity="o",
            evidence_chain=["scene_lead"],
        ),
        revelations=[Revelation(id="scene_lead", description="d", importance=1)],
    ))
    game.state.evidence_watch.rng = ForcedRandom(0.0)  # always plant
    return game


def agency_tick(game):
    game.npc_agency.update(game.state, game.renderer)


def culprit_hotspot_location(game):
    for loc_id, location in game.state.locations.items():
        for hs in location.hotspots:
            if (
                hs.hotspot_type == HotspotType.PERSON
                and hs.target_id == "watcher"
                and hs.active
            ):
                return loc_id
    return None


# ============================================================
# Relocation
# ============================================================

@pytest.mark.integration
class TestCulpritRelocation:

    def test_calm_culprit_stays_put(self):
        game = make_game()
        agency_tick(game)
        assert culprit_hotspot_location(game) == "room1"

    def test_heated_culprit_relocates_away_from_player(self):
        game = make_game()
        watcher = game.state.characters["watcher"]
        watcher.state.pressure_accumulated = 20  # 0.5 of threshold 40

        agency_tick(game)
        # Player is in room1; culprit was in room1 -> moves to room2/room3
        assert culprit_hotspot_location(game) in ("room2", "room3")

    def test_relocation_recorded_and_visible_when_watched(self, capsys):
        game = make_game()
        game.state.characters["watcher"].state.pressure_accumulated = 20
        capsys.readouterr()
        agency_tick(game)
        assert "slips out" in capsys.readouterr().out
        assert any(
            "avoiding the detective" in e.description
            for e in game.state.memory.world.events
        )

    def test_relocation_respects_cooldown(self):
        game = make_game()
        game.state.characters["watcher"].state.pressure_accumulated = 20
        agency_tick(game)
        first = culprit_hotspot_location(game)
        agency_tick(game)  # cooldown: no second move yet
        assert culprit_hotspot_location(game) == first


# ============================================================
# Flight
# ============================================================

@pytest.mark.integration
class TestCulpritFlight:

    def test_high_heat_starts_countdown(self, capsys):
        game = make_game()
        game.state.characters["watcher"].state.pressure_accumulated = 30  # 0.75
        capsys.readouterr()
        agency_tick(game)
        assert game.npc_agency.flee_deadline is not None
        assert "leave town" in capsys.readouterr().out

    def test_nervousness_contributes_to_heat(self):
        game = make_game()
        watcher = game.state.characters["watcher"]
        watcher.state.pressure_accumulated = 20   # 0.5 alone: relocate only
        watcher.state.mood = Mood.NERVOUS         # +0.25 -> 0.75: flee
        agency_tick(game)
        assert game.npc_agency.flee_deadline is not None

    def test_escape_ends_game_as_cold_case(self, capsys):
        game = make_game()
        game.state.characters["watcher"].state.pressure_accumulated = 30
        agency_tick(game)  # countdown starts

        game.state.memory.advance_time(CULPRIT_FLEE_COUNTDOWN_UNITS + 1)
        capsys.readouterr()
        agency_tick(game)

        output = capsys.readouterr().out
        assert "TRAIL WENT COLD" in output
        assert game.state.is_running is False
        assert game.npc_agency.culprit_fled is True
        assert culprit_hotspot_location(game) is None

    def test_halfway_warning_fires_once(self, capsys):
        game = make_game()
        game.state.characters["watcher"].state.pressure_accumulated = 30
        agency_tick(game)
        game.state.memory.advance_time(CULPRIT_FLEE_COUNTDOWN_UNITS // 2 + 1)
        capsys.readouterr()
        agency_tick(game)
        assert "Not much time" in capsys.readouterr().out
        agency_tick(game)
        assert "Not much time" not in capsys.readouterr().out

    def test_cracked_culprit_does_not_flee(self):
        game = make_game()
        watcher = game.state.characters["watcher"]
        watcher.state.pressure_accumulated = 99
        watcher.state.is_cracked = True
        agency_tick(game)
        assert game.npc_agency.flee_deadline is None


# ============================================================
# Framed NPCs defend themselves
# ============================================================

@pytest.mark.integration
class TestFramedDefense:

    def _frame_barfly(self, game):
        """Run the plant cycle and examine the planted evidence."""
        state = game.state
        location = state.locations["room1"]

        def run(text):
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

        run("look closer at the desk")
        run("look closer")
        state.memory.advance_time(EVIDENCE_TAMPER_DELAY_UNITS + 1)
        state.current_location_id = "room3"
        state.evidence_watch.update(state, game.renderer)
        state.current_location_id = "room1"
        state.evidence_watch.update(state, game.renderer)
        run("examine monogrammed handkerchief")

    def test_framed_npc_delivers_alibi(self, capsys):
        game = make_game()
        self._frame_barfly(game)

        game.state.memory.advance_time(FRAMED_DEFENSE_DELAY_UNITS + 1)
        game.state.current_location_id = "room2"  # where Eddie is
        capsys.readouterr()
        agency_tick(game)

        output = capsys.readouterr().out
        assert "Eddie the Barfly crosses the room" in output
        assert "isn't mine" in output
        alibi = game.state.memory.player.discoveries.get("alibi_barfly")
        assert alibi is not None
        assert alibi.is_evidence

    def test_defense_delivered_only_once(self, capsys):
        game = make_game()
        self._frame_barfly(game)
        game.state.memory.advance_time(FRAMED_DEFENSE_DELAY_UNITS + 1)
        game.state.current_location_id = "room2"
        agency_tick(game)
        capsys.readouterr()
        agency_tick(game)
        assert "crosses the room" not in capsys.readouterr().out

    def test_no_defense_before_word_spreads(self):
        game = make_game()
        self._frame_barfly(game)
        game.state.current_location_id = "room2"
        agency_tick(game)  # delay not yet elapsed
        assert "alibi_barfly" not in game.state.memory.player.discoveries

    def test_no_defense_without_meeting_the_framed(self):
        game = make_game()
        self._frame_barfly(game)
        game.state.memory.advance_time(FRAMED_DEFENSE_DELAY_UNITS + 1)
        # Player stays in room1; Eddie is in room2
        agency_tick(game)
        assert "alibi_barfly" not in game.state.memory.player.discoveries
