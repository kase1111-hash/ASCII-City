"""
The first session shouldn't lose the player.

Transcript tests through the real parser and game loop for the bugs a
newcomer hits in their first minutes: ordinary words that quit, world
events wiped by the screen clear, "alley" leading to the bar, hints that
fail when followed, verbs that do nothing, and a climax that needs two
accusations.
"""

import os
import pytest

from shadowengine.game import Game
from shadowengine.scenarios.study_escape import create_study_escape
from shadowengine.interaction import CommandParser, CommandType
from shadowengine.interaction.matching import best_match, match_rank
from shadowengine.render import Renderer
from shadowengine.testimony import advance_leads
from shadowengine.config import GameConfig
from shadowengine.llm.client import safe_base_url, DEFAULT_BASE_URL


@pytest.fixture(autouse=True)
def offline_llm(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "mock")


def seed_for(culprit: str) -> int:
    for seed in range(1, 500):
        if create_study_escape(seed=seed).state.spine.true_resolution.culprit_id == culprit:
            return seed
    raise AssertionError(culprit)


def noir(culprit: str = "informant", start: str = None, tmp_path=None) -> Game:
    game = create_study_escape(seed=seed_for(culprit))
    game.renderer.use_clear = False
    game.renderer.wait_for_key = lambda prompt="": None
    game.renderer.render_confirm = lambda question: True
    if tmp_path is not None:
        game.config = GameConfig(save_dir=str(tmp_path))
    if start:
        game.state.current_location_id = start
    return game


def drive(game: Game, inputs: list[str]) -> None:
    queue = list(inputs)
    game.renderer.render_prompt = lambda: queue.pop(0)
    game.renderer.render_dialogue_prompt = lambda speaker: queue.pop(0)
    while queue and game.state.is_running:
        if game.state.in_conversation:
            game.conversation_manager.conversation_loop(game.state)
        else:
            game._exploration_loop()


# ============================================================
# Ordinary words don't end the session
# ============================================================

@pytest.mark.integration
class TestQuitting:

    def test_exit_label_leaves_the_bar(self):
        game = noir(start="bar")
        drive(game, ["exit to street", "case"])
        assert game.state.is_running
        assert game.state.current_location_id == "street"

    @pytest.mark.parametrize("words", ["exam desk", "quiet", "exits?", "edit", "quote", "guilt"])
    def test_typos_never_quit(self, words):
        game = noir(start="office")
        drive(game, [words, "case"])
        assert game.state.is_running

    def test_typos_never_save_load_or_open_settings(self):
        parser = CommandParser()
        for word in ("sav", "saev", "lod", "laod", "setings", "quti"):
            assert parser.parse(word).command_type not in (
                CommandType.SAVE, CommandType.LOAD, CommandType.SETTINGS, CommandType.QUIT,
            ), word

    @pytest.mark.parametrize("word", ["quit", "q", "exit"])
    def test_quit_asks_first(self, word):
        game = noir(start="office")
        asked = []
        game.renderer.render_confirm = lambda question: asked.append(question) or False
        drive(game, [word, "case"])
        assert asked
        assert game.state.is_running

    def test_quit_saves_the_case(self, tmp_path):
        game = noir(start="office", tmp_path=tmp_path)
        drive(game, ["take magnifying glass", "quit"])
        assert not game.state.is_running
        save = tmp_path / "savegame.json"
        assert save.exists()

        resumed = noir(tmp_path=tmp_path)
        drive(resumed, ["load", "inventory"])
        assert "magnifying glass" in resumed.state.inventory

    def test_end_of_input_counts_as_yes(self, monkeypatch):
        renderer = Renderer()

        def eof(prompt=""):
            raise EOFError
        monkeypatch.setattr("builtins.input", eof)
        assert renderer.render_confirm("Quit? (y/n)") is True

    def test_common_typos_still_understood(self):
        parser = CommandParser()
        assert parser.parse("tlak harrow").command_type == CommandType.TALK
        assert parser.parse("examin desk").command_type == CommandType.EXAMINE
        assert parser.parse("tak glass").command_type == CommandType.TAKE
        assert parser.parse("arrest mickey").command_type == CommandType.ACCUSE
        assert parser.parse("back").command_type != CommandType.TALK
        assert parser.parse("press").command_type != CommandType.WAIT


# ============================================================
# The world's moves are visible
# ============================================================

@pytest.mark.integration
class TestWorldNewsVisible:

    def test_flee_warning_is_printed_beneath_the_scene(self, capsys):
        game = noir("bartender", start="bar")
        game.renderer.use_clear = True
        game.renderer.clear_screen = lambda: print("<<CLEAR>>")
        drive(game, ["talk mickey", "threaten", "leave", "wait"])
        assert game.npc_agency.flee_deadline is not None

        screens = capsys.readouterr().out.split("<<CLEAR>>")
        warned = [s for s in screens if "making moves to leave town" in s]
        assert warned, "the flee warning never reached a screen"
        screen = warned[0]
        assert screen.index("O'Malley's Bar") < screen.index("making moves to leave town")

    def test_game_over_from_the_world_is_shown(self, capsys):
        game = noir("bartender", start="bar")
        game.renderer.use_clear = True
        game.renderer.clear_screen = lambda: print("<<CLEAR>>")
        mickey = game.state.characters["bartender"]
        mickey.state.pressure_accumulated = mickey.trust_threshold - 1
        drive(game, ["wait"] * 40)
        out = capsys.readouterr().out
        assert not game.state.is_running
        assert "THE TRAIL WENT COLD" in out.split("<<CLEAR>>")[-1]


# ============================================================
# Words mean what they say
# ============================================================

@pytest.mark.integration
class TestNaming:

    @pytest.mark.parametrize("phrase", ["go alley", "go to the alley", "alley", "walk to the alley"])
    def test_alley_is_the_alley(self, phrase):
        game = noir(start="street")
        drive(game, [phrase])
        assert game.state.current_location_id == "alley"

    @pytest.mark.parametrize("phrase", ["go bar", "go omalleys", "go to o'malley's"])
    def test_bar_is_the_bar(self, phrase):
        game = noir(start="street")
        drive(game, [phrase])
        assert game.state.current_location_id == "bar"

    def test_whole_words_beat_fragments(self):
        assert best_match("alley", ["O'Malley's Bar", "Dark Alley"]) == 1
        assert best_match("bar", ["Mickey O'Malley (Bartender)", "O'Malley's Bar"]) == 1
        assert best_match("bart", ["Mickey O'Malley (Bartender)"]) == 0
        assert match_rank("door to street", "Door to Street") == 0
        assert match_rank("piano", "Dark Alley") is None

    def test_legend_numbers_match_what_typing_them_does(self, capsys):
        game = noir(start="office")
        drive(game, ["case"])          # one tick renders the office legend
        out = capsys.readouterr().out
        assert "People here: [1] Councilman Harrow" in out
        drive(game, ["1"])
        assert game.state.conversation_partner == "politician"


# ============================================================
# Hints and verbs that work when followed
# ============================================================

@pytest.mark.integration
class TestCommandsDoSomething:

    def test_look_closer_after_examine(self, capsys):
        game = noir(start="office")
        drive(game, ["examine desk", "look closer"])
        out = capsys.readouterr().out
        assert "Look closer at what?" not in out
        obj = game.inspection_manager._object_by_hotspot.get("hs_desk")
        assert obj is not None

    @pytest.mark.parametrize("phrase", ["look", "look around", "l"])
    def test_look_takes_in_the_room(self, phrase, capsys):
        game = noir(start="office")
        drive(game, [phrase])
        out = capsys.readouterr().out
        assert "I don't see that here" not in out
        assert "Councilman Harrow" in out

    def test_help_keeps_its_layout(self, capsys):
        game = noir(start="office")
        drive(game, ["help"])
        out = capsys.readouterr().out
        assert "\n  Getting around:\n" in out
        assert "save / load" in out

    @pytest.mark.parametrize("phrase", ["back", "go back", "b", "leave"])
    def test_back_returns(self, phrase):
        game = noir(start="office")
        drive(game, ["go door to street", phrase])
        assert game.state.current_location_id == "office"

    def test_back_with_nowhere_to_go_says_so(self, capsys):
        game = noir(start="office")
        drive(game, ["back"])
        assert game.state.current_location_id == "office"
        assert "nowhere to go back to" in capsys.readouterr().out

    def test_bare_go_lists_exits(self, capsys):
        game = noir(start="bar")
        drive(game, ["go"])
        assert "From here: Exit to Street" in capsys.readouterr().out

    def test_threaten_from_the_street(self):
        game = noir(start="bar")
        mickey = game.state.characters["bartender"]
        drive(game, ["threaten mickey"])
        assert game.state.in_conversation
        assert mickey.state.pressure_accumulated > 0

    def test_accuse_from_the_street(self):
        game = noir(start="office")
        harrow = game.state.characters["politician"]
        drive(game, ["accuse harrow"])
        assert game.state.conversation_partner == "politician"
        assert harrow.state.pressure_accumulated > 0

    def test_ask_someone_about_something(self):
        game = noir(start="bar")
        mickey = game.state.characters["bartender"]
        drive(game, ["ask mickey about marcus webb"])
        assert game.state.conversation_partner == "bartender"
        assert "marcus webb" in mickey.exhausted_topics

    def test_talk_to_someone_about_something(self):
        game = noir(start="bar")
        drive(game, ["talk to mickey about that night"])
        assert "that night" in game.state.characters["bartender"].exhausted_topics

    def test_show_evidence_to_someone(self):
        game = noir(start="bar")
        drive(game, ["examine back booth", "show napkin to mickey"])
        memory = game.state.memory.get_character_memory("bartender")
        assert any(i.interaction_type == "shown_evidence" for i in memory.player_interactions)

    def test_case_and_inventory_work_mid_conversation(self, capsys):
        game = noir(start="bar")
        calls = []
        handler = game.conversation_manager.dialogue_handler
        original = handler.generate_response
        handler.generate_response = lambda *a, **k: calls.append(1) or original(*a, **k)
        drive(game, ["talk mickey", "case", "inventory"])
        assert calls == []                        # not sent to Mickey
        assert "CASE" in capsys.readouterr().out.upper()
        assert game.state.in_conversation

    def test_accuse_him_in_conversation(self):
        game = noir(start="office")
        harrow = game.state.characters["politician"]
        drive(game, ["talk harrow", "I accuse you"])
        drive(game, ["accuse him"])
        assert harrow.state.pressure_accumulated > 0

    def test_show_needs_something_to_show(self, capsys):
        game = noir(start="bar")
        game.state.inventory.append("magnifying glass")
        drive(game, ["talk mickey", "show him"])
        assert "Show them what?" in capsys.readouterr().out


# ============================================================
# The climax takes one accusation
# ============================================================

@pytest.mark.integration
class TestOneAccusation:

    @pytest.mark.parametrize("culprit", ["bartender", "informant", "politician"])
    def test_cornered_culprit_falls_to_one_accusation(self, culprit):
        game = noir(culprit)
        for lead in ("witness_account", "physical_evidence"):
            game.state.memory.player_discovers(
                fact_id=lead, description=lead, location="alley",
                source="test", is_evidence=True,
            )
        advance_leads(game.state)
        suspect = game.state.characters[culprit]
        game.conversation_manager.handle_accuse(suspect, game.state)
        assert game.state.spine.is_solved
        assert not game.state.is_running


# ============================================================
# Renderer and client details
# ============================================================

class TestRendererAndClient:

    def test_wrap_keeps_paragraphs_and_indents(self):
        renderer = Renderer(width=40)
        lines = renderer._word_wrap("Title:\n  short line\n\nA long paragraph " + "word " * 12, 30)
        assert lines[0] == "Title:"
        assert lines[1] == "  short line"
        assert lines[2] == ""
        assert all(len(line) <= 30 for line in lines)

    def test_held_output_shows_beneath(self, capsys):
        renderer = Renderer()
        with renderer.held_output() as held:
            print("the world moved")
        assert capsys.readouterr().out == ""
        renderer.show_held(held)
        assert "the world moved" in capsys.readouterr().out

    @pytest.mark.parametrize("url,expected", [
        ("http://localhost:11434", "http://localhost:11434"),
        ("https://api.openai.com/v1/", "https://api.openai.com/v1"),
        ("localhost:11434", "http://localhost:11434"),
        ("file:///etc/passwd", DEFAULT_BASE_URL),
        ("ftp://host", DEFAULT_BASE_URL),
        ("", DEFAULT_BASE_URL),
    ])
    def test_llm_endpoints_are_http_only(self, url, expected):
        assert safe_base_url(url) == expected
