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
        assert (tmp_path / "autosave.json").exists()

        resumed = noir(tmp_path=tmp_path)
        drive(resumed, ["load", "inventory"])
        assert "magnifying glass" in resumed.state.inventory

    def test_quitting_never_overwrites_a_saved_case(self, tmp_path):
        """A fresh session quit must not clobber the case you saved."""
        game = noir(start="office", tmp_path=tmp_path)
        drive(game, ["take magnifying glass", "save"])
        saved = (tmp_path / "savegame.json").read_text()

        fresh = noir(start="office", tmp_path=tmp_path)
        drive(fresh, ["quit"])
        assert (tmp_path / "savegame.json").read_text() == saved

    @pytest.mark.parametrize("phrase", ["exit game", "exit the game", "quit now", "leave the game"])
    def test_exit_the_game_quits(self, phrase):
        game = noir(start="office")
        drive(game, [phrase])
        assert not game.state.is_running
        assert set(game.state.locations) == {"office", "street", "bar", "alley"}

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

    def test_back_retraces_the_trail(self):
        game = noir(start="office")
        drive(game, ["go door to street", "go bar", "back", "back"])
        assert game.state.current_location_id == "office"

    def test_back_with_no_trail_takes_the_way_out(self):
        game = noir(start="bar")
        drive(game, ["back"])
        assert game.state.current_location_id == "street"

    @pytest.mark.parametrize("phrase", ["leave the bar", "exit the bar", "exit bar", "leave"])
    def test_leaving_the_room_by_name(self, phrase):
        game = noir(start="bar")
        drive(game, [phrase])
        assert game.state.current_location_id == "street"

    @pytest.mark.parametrize("phrase", ["back to the bar", "return to the bar", "go back to the bar"])
    def test_back_to_somewhere(self, phrase):
        game = noir(start="office")
        drive(game, ["go door to street", phrase])
        assert game.state.current_location_id == "bar"

    @pytest.mark.parametrize("word", ["bye", "goodbye", "end"])
    def test_farewells_outside_conversation_go_nowhere(self, word, capsys):
        game = noir(start="office")
        drive(game, ["go door to street", word])
        assert game.state.current_location_id == "street"
        assert "not talking to anyone" in capsys.readouterr().out

    def test_back_after_load_stays_in_the_loaded_game(self, tmp_path):
        game = noir(start="office", tmp_path=tmp_path)
        drive(game, ["go door to street", "go bar", "save"])
        other = noir(start="alley", tmp_path=tmp_path)
        drive(other, ["load", "back"])
        assert other.state.current_location_id == "street"

    @pytest.mark.parametrize("form", ["go {}", "go [{}]", "go #{}"])
    def test_go_by_legend_number(self, form):
        game = noir(start="office")
        drive(game, ["case"])             # a tick numbers the legend
        door = game.state.locations["office"].get_exits_list()[0].number
        drive(game, [form.format(door)])
        assert game.state.current_location_id == "street"
        assert set(game.state.locations) == {"office", "street", "bar", "alley"}

    def test_go_to_a_number_never_invents_a_place(self):
        game = noir(start="office")
        drive(game, ["case", "go 99"])
        assert game.state.current_location_id == "office"
        assert set(game.state.locations) == {"office", "street", "bar", "alley"}

    @pytest.mark.parametrize("phrase", ["go to the alley", "go alley"])
    def test_alley_from_inside_the_bar(self, phrase):
        game = noir(start="bar")
        drive(game, [phrase])
        assert not game.state.in_conversation
        assert game.state.current_location_id == "alley"

    def test_bare_place_name_elsewhere_gives_directions(self, capsys):
        """A bare 'alley' in the bar isn't Mickey O'Malley — and isn't a teleport."""
        game = noir(start="bar")
        drive(game, ["alley"])
        assert not game.state.in_conversation
        assert game.state.current_location_id == "bar"
        assert "try 'go alley'" in capsys.readouterr().out

    @pytest.mark.parametrize("phrase", ["pick up the magnifying glass", "examine my desk", "search the desk"])
    def test_extra_words_still_find_the_thing(self, phrase, capsys):
        game = noir(start="office")
        drive(game, [phrase])
        assert "I don't see that here" not in capsys.readouterr().out

    @pytest.mark.parametrize("phrase", ["look around the room", "look around here", "examine the room", "look at the office"])
    def test_ways_to_look_around(self, phrase, capsys):
        game = noir(start="office")
        drive(game, [phrase])
        out = capsys.readouterr().out
        assert "I don't see that here" not in out
        assert "People here: Councilman Harrow" in out

    def test_go_to_the_room_you_are_in(self, capsys):
        game = noir(start="bar")
        drive(game, ["go bar"])
        assert game.state.current_location_id == "bar"
        assert "already in O'Malley's Bar" in capsys.readouterr().out

    def test_back_with_nowhere_to_go_says_so(self, capsys):
        from shadowengine.render import Location
        game = noir(start="office")
        game.state.locations["void"] = Location(id="void", name="The Void", description="Nothing.")
        game.state.current_location_id = "void"
        drive(game, ["back"])
        assert game.state.current_location_id == "void"
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
        out = capsys.readouterr().out
        assert "CASE FILE" in out and "LEADS (" in out
        assert game.state.in_conversation

    @pytest.mark.parametrize("line", ["accuse him", "I accuse you!", "I accuse you.", "You did it!", "accuse harrow of murder"])
    def test_accusing_the_partner(self, line):
        game = noir(start="office")
        harrow = game.state.characters["politician"]
        drive(game, ["talk harrow"])
        before = harrow.state.pressure_accumulated
        drive(game, [line])
        assert harrow.state.pressure_accumulated > before

    @pytest.mark.parametrize("line", ["accuse mickey", "threaten sally", "arrest the bartender"])
    def test_naming_someone_else_leaves_the_partner_alone(self, line, capsys):
        game = noir(start="office")
        harrow = game.state.characters["politician"]
        drive(game, ["talk harrow", line])
        assert harrow.state.pressure_accumulated == 0
        assert "Leave the conversation first" in capsys.readouterr().out

    def test_show_me_is_just_talk(self, capsys):
        game = noir(start="bar")
        drive(game, ["talk mickey", "Show me your hands"])
        assert "nothing like" not in capsys.readouterr().out

    def test_show_the_partner_something(self):
        game = noir(start="bar")
        drive(game, ["examine back booth", "talk mickey", "show the bartender the napkin"])
        memory = game.state.memory.get_character_memory("bartender")
        assert any(i.interaction_type == "shown_evidence" for i in memory.player_interactions)

    def test_cracked_witness_stops_repeating_their_secret(self, capsys):
        game = noir("informant", start="bar")
        drive(game, ["talk mickey", "threaten", "threaten", "what now?", "and then?"])
        out = capsys.readouterr().out
        assert out.count("Fine! You want the truth?") <= 1

    @pytest.mark.parametrize("phrase", ["accuse mickey of murder", "threaten mickey with the napkin", "ask mickey what he saw"])
    def test_person_verbs_ignore_trailing_words(self, phrase):
        game = noir(start="bar")
        drive(game, [phrase])
        assert game.state.conversation_partner == "bartender"

    def test_ask_with_a_question_word_keeps_the_question(self):
        game = noir(start="bar")
        drive(game, ["ask mickey what happened that night"])
        assert "that night" in game.state.characters["bartender"].exhausted_topics

    def test_pronoun_when_one_person_is_here(self):
        game = noir(start="office")
        drive(game, ["threaten him"])
        assert game.state.conversation_partner == "politician"

    def test_show_person_the_thing(self):
        game = noir(start="bar")
        drive(game, ["examine back booth", "show mickey the napkin"])
        memory = game.state.memory.get_character_memory("bartender")
        assert any(i.interaction_type == "shown_evidence" for i in memory.player_interactions)

    def test_talk_about_something_in_the_room(self):
        game = noir(start="office")
        drive(game, ["talk to councilman harrow about the window"])
        assert game.state.conversation_partner == "politician"

    @pytest.mark.parametrize("phrase", ["tell mickey", "interrogate mickey", "talk whispers"])
    def test_more_ways_to_talk(self, phrase):
        start = "street" if "whispers" in phrase else "bar"
        game = noir(start=start)
        drive(game, [phrase])
        assert game.state.in_conversation

    @pytest.mark.parametrize("phrase,expected", [("accuse 1", "politician"), ("1 accuse", "politician"), ("talk 1", "politician")])
    def test_person_verbs_take_legend_numbers(self, phrase, expected):
        game = noir(start="office")
        drive(game, ["case", phrase])        # a tick to number the legend
        assert game.state.conversation_partner == expected

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

    def test_dialogue_paragraph_breaks_are_blank_not_quoted(self, capsys):
        Renderer().render_dialogue("Mickey", "First part.\n\nSecond part.")
        out = capsys.readouterr().out
        assert '""' not in out
        assert '"First part."' in out and '"Second part."' in out

    def test_no_escape_codes_when_not_a_terminal(self, capsys):
        Renderer().clear_screen()      # pytest's stdout is not a tty
        assert "\033" not in capsys.readouterr().out

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
        ("localhost", "http://localhost:11434"),
        ("0.0.0.0:11434", "http://0.0.0.0:11434"),
        ("[::1", DEFAULT_BASE_URL),
        ("http://[bad", DEFAULT_BASE_URL),
    ])
    def test_llm_endpoints_are_http_only(self, url, expected):
        assert safe_base_url(url) == expected


# ============================================================
# Second review round: looser matching must not move you anywhere odd
# ============================================================

AUTHORED = {"office", "street", "bar", "alley"}


@pytest.mark.integration
class TestNothingInventsPlaces:

    @pytest.mark.parametrize("start", ["office", "bar", "alley"])
    def test_bare_street_goes_to_the_street(self, start):
        game = noir(start=start)
        drive(game, ["street"])
        assert game.state.current_location_id == "street"

    def test_back_booth_is_the_booth(self):
        game = noir(start="bar")
        drive(game, ["back booth"])
        assert game.state.current_location_id == "bar"
        assert game.state.memory.player.has_discovered("booth_napkin")

    @pytest.mark.parametrize("start,phrase", [
        ("office", "go to elm street"), ("street", "go to webb's office"),
        ("street", "go to the jazz bar"), ("bar", "go to the back room"),
    ])
    def test_new_places_are_not_swallowed_by_old_exits(self, start, phrase):
        game = noir(start=start)
        drive(game, [phrase])
        assert game.state.current_location_id not in AUTHORED

    @pytest.mark.parametrize("phrase", [
        "leave the room", "leave here", "leave this place", "leave him alone",
        "leave quietly", "leave a tip", "leave the building", "exit the room",
        "go out of the bar", "go out", "leave now", "back off", "back out",
    ])
    def test_leaving_never_invents_a_place(self, phrase):
        game = noir(start="bar")
        drive(game, [phrase])
        assert game.state.is_running
        assert set(game.state.locations) == AUTHORED
        assert game.state.current_location_id == "street"

    @pytest.mark.parametrize("phrase", ["return to mickey", "back to the desk", "return the uv lamp"])
    def test_back_to_unknown_places_says_so(self, phrase):
        game = noir(start="bar")
        drive(game, [phrase])
        assert set(game.state.locations) == AUTHORED

    def test_back_to_where_you_are(self, capsys):
        game = noir(start="office")
        drive(game, ["back to the office"])
        assert "already in Your Office" in capsys.readouterr().out

    def test_go_north_from_a_room_called_north(self):
        game = noir(start="alley")
        drive(game, ["go north", "go north"])
        assert game.state.current_location_id == "alley_north_north"

    @pytest.mark.parametrize("word", ["rain", "building"])
    def test_stray_words_do_not_move_you(self, word):
        game = noir(start="bar")
        drive(game, [word])
        assert game.state.current_location_id == "bar"

    def test_malleys_without_the_o(self):
        game = noir(start="street")
        drive(game, ["go to malley's"])
        assert game.state.current_location_id == "bar"

    def test_direction_words_decide_between_similar_exits(self):
        from shadowengine.render import Location
        from shadowengine.interaction import Hotspot, HotspotType
        game = noir(start="office")
        hotel = Location(id="hotel", name="Hotel Lobby", description="Marble.")
        for label, target in (("Stairs Up", "office"), ("Stairs Down", "bar"), ("Way Out", "street")):
            hotel.add_hotspot(Hotspot(
                id=f"hs_{target}", label=label, hotspot_type=HotspotType.EXIT,
                position=(1, 1), target_id=target,
            ))
        game.state.locations["hotel"] = hotel
        game.state.current_location_id = "hotel"
        drive(game, ["go down the stairs"])
        assert game.state.current_location_id == "bar"
        game.state.current_location_id = "hotel"
        drive(game, ["go out"])
        assert game.state.current_location_id == "street"


@pytest.mark.integration
class TestSaveSlots:

    def test_load_offers_the_manual_save_after_a_quit(self, tmp_path, capsys):
        game = noir(start="office", tmp_path=tmp_path)
        drive(game, ["take magnifying glass", "save"])
        fresh = noir(start="office", tmp_path=tmp_path)
        drive(fresh, ["quit"])

        later = noir(tmp_path=tmp_path)
        drive(later, ["load"])
        assert "magnifying glass" not in later.state.inventory     # newest: the quit
        assert "'load save'" in capsys.readouterr().out
        drive(later, ["load save"])
        assert "magnifying glass" in later.state.inventory

    def test_damaged_newest_slot_falls_back(self, tmp_path):
        game = noir(start="office", tmp_path=tmp_path)
        drive(game, ["take magnifying glass", "save"])
        (tmp_path / "autosave.json").write_text('{"version": 3, "chec')
        later = noir(tmp_path=tmp_path)
        drive(later, ["load"])
        assert "magnifying glass" in later.state.inventory

    def test_saves_are_written_whole(self, tmp_path):
        game = noir(start="office", tmp_path=tmp_path)
        drive(game, ["save"])
        assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.integration
class TestWhatCountsAsPressure:

    @pytest.mark.parametrize("line", [
        "You did it?", "Did someone threaten you?", "I accused the wrong man",
        "I accuse you of lying", "I'm accusing you of lying to me", "Who did you accuse?",
    ])
    def test_talk_about_accusing_is_just_talk(self, line):
        game = noir("informant", start="bar")
        mickey = game.state.characters["bartender"]
        drive(game, ["talk mickey", line])
        assert mickey.state.pressure_accumulated == 0

    @pytest.mark.parametrize("line", [
        "I accuse you, Mickey O'Malley, of murder!", "threaten you, mickey",
        "accuse mr. o'malley", "I'm arresting you, Mickey.", "accuse the bartender",
    ])
    def test_natural_ways_to_lean_on_the_partner(self, line):
        game = noir("informant", start="bar")
        mickey = game.state.characters["bartender"]
        drive(game, ["talk mickey", line])
        assert mickey.state.pressure_accumulated > 0

    def test_cracked_witness_says_their_secret_once(self, capsys):
        game = noir("informant", start="bar")
        drive(game, ["talk mickey", "threaten", "threaten", "what did you see?", "who was it?"])
        out = capsys.readouterr().out
        assert out.count("I'm scared to say") == 1

    @pytest.mark.parametrize("phrase", ["talk to him", "speak with him", "interrogate him"])
    def test_talk_to_a_pronoun(self, phrase):
        game = noir(start="bar")
        drive(game, [phrase])
        assert game.state.conversation_partner == "bartender"

    @pytest.mark.parametrize("phrase", ["accuse 1 of murder", "ask 1 about marcus", "talk 1 about marcus"])
    def test_numbers_with_more_words(self, phrase):
        game = noir(start="bar")
        drive(game, ["case", phrase])
        assert game.state.conversation_partner == "bartender"
