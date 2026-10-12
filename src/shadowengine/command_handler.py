"""
CommandHandler - Routes parsed commands to appropriate handlers.

Extracted from game.py to isolate command processing, hotspot
interaction, and LLM-based free exploration into a testable module.
"""

from typing import Optional
import json
import logging
import os
import re

from .config import GameConfig, WAIT_TIME_MINUTES
from .memory import MemoryBank, EventType
from .memory.character_memory import BeliefConfidence
from .character import Character
from .interaction import CommandParser, Command, CommandType, Hotspot, HotspotType
from .render import Scene, Location, Renderer
from .llm.client import LLMClient
from .llm.validation import safe_parse_json, validate_free_exploration_response, sanitize_player_input
from .location_manager import LocationManager
from .conversation import ConversationManager
from .circuits import SignalType, InputSignal, OutputSignal, ProcessingResult
from .testimony import advance_leads
from .interaction.matching import label_words

# Separate slots: quitting auto-saves without overwriting a case you saved
SAVE_FILE = "savegame.json"
AUTOSAVE_FILE = "autosave.json"

logger = logging.getLogger(__name__)


class CommandHandler:
    """
    Routes parsed commands to the appropriate handler.
    Manages examine, take, wait, save/load, and LLM-based free exploration.
    """

    def __init__(
        self,
        parser: CommandParser,
        renderer: Renderer,
        llm_client: LLMClient,
        location_manager: LocationManager,
        conversation_manager: ConversationManager,
        signal_router=None,
        inspection_manager=None,
        save_system=None,
    ):
        self.parser = parser
        self.renderer = renderer
        self.llm_client = llm_client
        self.location_manager = location_manager
        self.conversation_manager = conversation_manager
        self.signal_router = signal_router
        self.inspection_manager = inspection_manager
        self.save_system = save_system

    def handle_command(
        self,
        command: Command,
        context: dict,
        state: 'GameState',
        config: GameConfig,
        add_character_fn,
    ) -> None:
        """Route a parsed command to the appropriate handler."""
        # Commands that don't require a hotspot
        simple_handlers = {
            CommandType.QUIT: lambda: self._handle_quit(state, config),
            CommandType.HELP: lambda: self._show_text(self.parser.get_help_text()),
            CommandType.INVENTORY: lambda: self._show_inventory(state),
            CommandType.CASE: lambda: self._handle_case(state),
            CommandType.WAIT: lambda: self._handle_wait(state, config),
            CommandType.SAVE: lambda: self._handle_save(state, config),
            CommandType.LOAD: lambda: self._handle_load(state, config),
            CommandType.SETTINGS: lambda: self._handle_settings(state, config),
        }

        if command.command_type in simple_handlers:
            simple_handlers[command.command_type]()
            return

        raw_lower = (command.raw_input or "").lower().strip()
        words = raw_lower.split()
        current_location = state.locations.get(state.current_location_id)

        # A farewell with no one to say it to
        if command.command_type == CommandType.LEAVE and words and words[0] != "leave":
            self._show_error("You're not talking to anyone.")
            return

        # "back", "go back", "leave": retrace your steps
        if raw_lower in self._BACK_WORDS or raw_lower == "leave":
            self._go_back(state, config, add_character_fn)
            return

        # "back to the bar", "return to the office", "go back to the street"
        back_to = self._BACK_TO.match(raw_lower)
        if back_to:
            self._go_to(back_to.group(1), current_location, state, config, add_character_fn)
            return

        # "leave the bar", "exit the office": take the way out of this room.
        # (Checked on the player's own words: the parser may already have
        # matched "the bar" to the Bar Counter.)
        said_place = " ".join(words[1:])
        if (
            command.command_type in (CommandType.LEAVE, CommandType.GO)
            and said_place
            and not command.hotspot_number
            and self._names_current_room(said_place, state)
        ):
            if words[0] in ("leave", "exit"):
                self._leave_room(state, config, add_character_fn)
            else:
                location = state.locations[state.current_location_id]
                self._show_error(
                    f"You're already in {location.name}. {self._exits_text(location)}"
                )
            return
        if command.command_type == CommandType.LEAVE:
            command.command_type = CommandType.GO   # "leave through the door"

        # Bare "look", "look around the room", "examine the alley" (while in
        # it): take in the room again
        if (
            command.command_type == CommandType.EXAMINE
            and not command.hotspot_number
            and self._is_look_around(command.target, state)
        ):
            self._handle_look_around(state)
            return

        # Close-inspection commands (look closer, zoom, step back, look
        # under X, focus on X, use magnifying glass on X) route to the
        # inspection system before anything else sees them.
        if (
            self.inspection_manager
            and command.raw_input
            and self.inspection_manager.wants_inspection(command.raw_input)
        ):
            if self.inspection_manager.handle(command.raw_input, state, config):
                return

        if command.command_type == CommandType.UNKNOWN:
            raw = command.raw_input.lower().strip() if command.raw_input else ""

            directions = {
                "north": "north", "n": "north",
                "south": "south", "s": "south",
                "east": "east", "e": "east",
                "west": "west", "w": "west",
            }

            if raw in directions:
                self.location_manager.handle_direction(
                    directions[raw], current_location, state, config, add_character_fn
                )
                return

            go_match = re.match(r'^go\s+(.+)$', raw)
            if go_match:
                destination = go_match.group(1).strip()
                if destination in directions:
                    self.location_manager.handle_direction(
                        directions[destination], current_location, state, config, add_character_fn
                    )
                else:
                    self.location_manager.handle_free_movement(
                        destination, current_location, state, config, add_character_fn
                    )
                return

            self._handle_free_exploration(command.raw_input, context, state, config, add_character_fn)
            return

        # A bare direction ("north", "n") parses as a GO verb with no
        # target: the direction itself is where they want to go
        if (
            command.command_type == CommandType.GO
            and not command.target
            and not command.hotspot_number
        ):
            dir_map = {"n": "north", "s": "south", "e": "east", "w": "west"}
            if raw_lower in dir_map or raw_lower in dir_map.values():
                self.location_manager.handle_direction(
                    dir_map.get(raw_lower, raw_lower), current_location, state, config, add_character_fn
                )
                return

        # Acting on a person from the street: accuse, threaten, ask, show
        if command.command_type in (
            CommandType.ACCUSE, CommandType.THREATEN, CommandType.ASK, CommandType.SHOW,
        ):
            self._handle_person_verb(command, current_location, state)
            return

        # A bare "go": say where you can go
        if (
            command.command_type == CommandType.GO
            and not command.target
            and not command.hotspot_number
        ):
            self._show_exits(current_location)
            return

        # Find target hotspot
        hotspot = self._resolve_hotspot(command, current_location, state)
        if not hotspot:
            if command.command_type == CommandType.GO and command.target:
                target = command.target.lower()
                dir_map = {"n": "north", "s": "south", "e": "east", "w": "west"}
                if target in dir_map or target in dir_map.values():
                    self.location_manager.handle_direction(
                        dir_map.get(target, target), current_location, state, config, add_character_fn
                    )
                    return
                self.location_manager.handle_free_movement(
                    command.target, current_location, state, config, add_character_fn
                )
                return
            # Just a place name ("alley"): go there, if it's a place we know
            if (
                command.command_type == CommandType.EXAMINE
                and command.target
                and words and words[0] not in self.parser.word_to_verb
            ):
                known = self.location_manager.match_known_location(command.target, state)
                if known and known != state.current_location_id:
                    self.location_manager.handle_free_movement(
                        command.target, current_location, state, config, add_character_fn
                    )
                    return
            self._show_error("I don't see that here.")
            return

        # "go alley" from the bar shouldn't walk into Mickey: going somewhere
        # that isn't a way out means the place by that name, if there is one
        if command.command_type == CommandType.GO and hotspot.hotspot_type != HotspotType.EXIT:
            known = (
                self.location_manager.match_known_location(command.target, state)
                if command.target else None
            )
            if known and known != state.current_location_id:
                self.location_manager.handle_free_movement(
                    command.target, current_location, state, config, add_character_fn
                )
            else:
                self._show_error(f"{hotspot.label} isn't a way out. {self._exits_text(current_location)}")
            return

        # Commands that require a hotspot
        hotspot_handlers = {
            CommandType.EXAMINE: lambda h: self._handle_examine(h, state, config),
            CommandType.TALK: lambda h: self._handle_talk(h, state),
            CommandType.TAKE: lambda h: self._handle_take(h, state, config),
            CommandType.USE: lambda h: self._handle_use(h, state, config),
            CommandType.GO: lambda h: self.location_manager.handle_go(
                h, current_location, state, config, add_character_fn
            ),
            CommandType.HOTSPOT: lambda h: self._handle_hotspot_default(
                h, state, config, current_location, add_character_fn
            ),
        }

        handler = hotspot_handlers.get(command.command_type)
        if handler:
            handler(hotspot)
            # "talk to mickey about the booth"
            if command.topic and state.in_conversation:
                self._ask_about(state, command.topic)

    def handle_meta(self, raw_input: str, state: 'GameState', config: GameConfig) -> bool:
        """
        Run a case/inventory/save/load/quit command typed mid-conversation.
        Returns True if the input was one of those.
        """
        command = self.parser.parse(raw_input, {})
        handlers = {
            CommandType.CASE: lambda: self._handle_case(state),
            CommandType.INVENTORY: lambda: self._show_inventory(state),
            CommandType.SAVE: lambda: self._handle_save(state, config),
            CommandType.LOAD: lambda: self._handle_load(state, config),
            CommandType.QUIT: lambda: self._handle_quit(state, config),
        }
        handler = handlers.get(command.command_type)
        if handler is None:
            return False
        handler()
        return True

    _BACK_WORDS = {"back", "b", "go back", "return", "go back out", "head back"}
    _BACK_TO = re.compile(r"^(?:go\s+|head\s+)?(?:back|return)\s+(?:to\s+)?(.+)$")

    # Words that point at the room itself rather than anything in it
    _ROOM_WORDS = {"around", "about", "round", "here", "me", "room", "place", "scene", "area"}

    def _handle_quit(self, state: 'GameState', config: GameConfig = None) -> None:
        """Quit — after asking, and with the case auto-saved if that's on."""
        autosave = bool(config is not None and config.auto_save and self.save_system)
        question = (
            "Quit the game? Your case will be saved. (y/n)" if autosave
            else "Quit the game? Unsaved progress will be lost. (y/n)"
        )
        if not self.renderer.render_confirm(question):
            self.renderer.render_text("Back to work.")
            return

        if autosave:
            # Its own slot: quitting never overwrites a case you saved
            save_path = os.path.join(config.save_dir, AUTOSAVE_FILE)
            try:
                self.save_system.save(save_path)
                self.renderer.render_text(
                    "Case saved. Type 'load' next time to pick up where you left off."
                )
            except OSError as e:
                logger.error("Auto-save on quit failed: %s", e)
                self.renderer.render_error("Couldn't save the case.")
                if not self.renderer.render_confirm("Quit without saving? (y/n)"):
                    return
        state.is_running = False

    def _go_back(self, state: 'GameState', config: GameConfig, add_character_fn) -> None:
        """Retrace your steps: the last place you came from, then the one before."""
        trail = getattr(state, "location_trail", [])
        while trail:
            previous = trail.pop()
            if previous in state.locations and previous != state.current_location_id:
                state.retracing = True
                state.current_location_id = previous
                state.memory.world.record(
                    event_type=EventType.MOVEMENT,
                    description=f"Player went back to {state.locations[previous].name}",
                    location=previous,
                    actors=["player"],
                )
                if config.time_passes_on_action:
                    state.memory.advance_time(config.time_units_per_action)
                return
        self._leave_room(state, config, add_character_fn, nowhere_message=True)

    def _leave_room(
        self, state: 'GameState', config: GameConfig, add_character_fn,
        nowhere_message: bool = False,
    ) -> None:
        """Take the way out of this room: its 'Back to'/'Exit' door, or its only exit."""
        location = state.locations.get(state.current_location_id)
        exits = location.get_exits_list() if location else []
        way_out = next(
            (h for h in exits if h.label.lower().startswith(("back", "exit"))), None,
        )
        if way_out is None and len(exits) == 1:
            way_out = exits[0]
        if way_out is not None:
            self.location_manager.handle_go(way_out, location, state, config, add_character_fn)
            return
        prefix = "There's nowhere to go back to. " if nowhere_message else ""
        self._show_error(prefix + self._exits_text(location))

    def _go_to(
        self, destination: str, location: Optional[Location], state: 'GameState',
        config: GameConfig, add_character_fn,
    ) -> None:
        """Go somewhere by name: an exit here, or a place already known."""
        hotspot = location.get_hotspot_by_label(destination) if location else None
        if hotspot is not None and hotspot.hotspot_type == HotspotType.EXIT:
            self.location_manager.handle_go(hotspot, location, state, config, add_character_fn)
        else:
            self.location_manager.handle_free_movement(
                destination, location, state, config, add_character_fn,
            )

    def _names_current_room(self, text: str, state: 'GameState') -> bool:
        """Does this text name the room the player is standing in?"""
        location = state.locations.get(state.current_location_id)
        if location is None:
            return False
        wanted = set(label_words(text))
        if not wanted:
            return False
        # Its name, not its id: a generated "office_north" isn't the office
        if wanted <= set(label_words(location.name)):
            return True
        return self.location_manager.match_known_location(text, state) == location.id

    def _is_look_around(self, target: Optional[str], state: 'GameState') -> bool:
        """'look', 'look around the room', 'examine the alley' (while in it)."""
        if not target:
            return True
        rest = [w for w in label_words(target) if w not in self._ROOM_WORDS]
        return not rest or self._names_current_room(" ".join(rest), state)

    @staticmethod
    def _exits_text(location: Optional[Location]) -> str:
        exits = location.get_exits_list() if location else []
        if exits:
            return "From here: " + ", ".join(h.label for h in exits) + "."
        return "Name a place, or a direction like 'north'."

    def _show_exits(self, location: Optional[Location]) -> None:
        self._show_error("Go where? " + self._exits_text(location))

    def _handle_look_around(self, state: 'GameState') -> None:
        """Describe the room again — who's here and what's worth a look."""
        location = state.locations.get(state.current_location_id)
        if not location:
            return
        self.renderer.render_narration(f"{location.name}. {location.description}")
        if location.ambient_description:
            self.renderer.render_text(location.ambient_description)
        people = [h.label for h in location.get_people()]
        things = [
            h.label for h in location.get_visible_hotspots()
            if h.hotspot_type not in (HotspotType.PERSON, HotspotType.EXIT)
        ]
        if people:
            self.renderer.render_text(f"People here: {', '.join(people)}")
        if things:
            self.renderer.render_text(f"You notice: {', '.join(things)}")
        exits = [h.label for h in location.get_exits_list()]
        if exits:
            self.renderer.render_text(f"Exits: {', '.join(exits)}")
        self.renderer.wait_for_key()

    _SHOW_TO = re.compile(r"^(?:show|present|give)\s+(.+?)\s+to\s+(.+)$")
    # "accuse mickey of murder", "ask sally what she saw"
    _TRAILING_CLAUSE = re.compile(
        r"\s+(?:of|for|with|about|what|who|where|why|how|when|that|if|whether)\s+.*$"
    )
    _PRONOUNS = {"him", "her", "them", "he", "she", "they", "you"}

    def _find_person(
        self, text: Optional[str], location: Optional[Location], state: 'GameState',
        number: Optional[int] = None,
    ) -> Optional[Hotspot]:
        """
        Someone in the room, by legend number, pronoun (when only one
        person is here), name, nickname or role — ignoring trailing words.
        """
        if location is None:
            return None
        if number is not None:
            hotspot = location.get_hotspot_by_number(number)
            return hotspot if hotspot and hotspot.hotspot_type == HotspotType.PERSON else None
        if not text:
            return None
        text = self._TRAILING_CLAUSE.sub("", " " + text.lower().strip()).strip()
        words = [w for w in text.split() if w not in ("the", "a", "an", "to", "with", "at")]
        if not words:
            return None
        people = location.get_people()
        if len(words) == 1 and words[0] in self._PRONOUNS:
            return people[0] if len(people) == 1 else None
        # The longest run of leading words that names someone
        for size in range(len(words), 0, -1):
            candidate = " ".join(words[:size])
            hotspot = location.get_hotspot_by_label(candidate)
            if hotspot is None or hotspot.hotspot_type != HotspotType.PERSON:
                hotspot = self._resolve_person_by_name(candidate, location, state)
            if hotspot is not None:
                return hotspot
        return None

    def _handle_person_verb(
        self, command: Command, location: Optional[Location], state: 'GameState',
    ) -> None:
        """
        accuse/threaten/ask/show aimed at someone in the room: walk up to
        them and do it — the conversation carries on from there.
        """
        raw_lower = (command.raw_input or "").lower().strip()
        verb = command.command_type
        after_verb = raw_lower.split(maxsplit=1)[1] if len(raw_lower.split()) > 1 else ""

        evidence_query = topic = None
        hotspot = None
        if verb == CommandType.SHOW:
            match = self._SHOW_TO.match(raw_lower)
            if match:
                evidence_query = match.group(1)
                hotspot = self._find_person(match.group(2), location, state)
            else:
                # "show mickey the napkin": the leading words name the person
                words = after_verb.split()
                for cut in range(1, len(words)):
                    found = self._find_person(" ".join(words[:cut]), location, state)
                    if found is not None:
                        hotspot, evidence_query = found, " ".join(words[cut:])
                        break
                if hotspot is None:
                    self._show_error(
                        "Show what to whom? Try 'show [evidence] to [person]', or "
                        "talk to them first."
                    )
                    return
        else:
            if verb == CommandType.ASK:
                topic = command.topic
                if not topic:
                    # "ask sally what she saw"
                    clause = self._TRAILING_CLAUSE.search(" " + after_verb)
                    if clause:
                        topic = clause.group(0).strip()
            hotspot = self._find_person(
                after_verb.split(" about ")[0] if after_verb else None,
                location, state, number=command.hotspot_number,
            )

        if hotspot is None:
            if not after_verb and command.hotspot_number is None:
                action = {
                    CommandType.ACCUSE: "Accuse", CommandType.THREATEN: "Threaten",
                    CommandType.ASK: "Ask", CommandType.SHOW: "Show",
                }[verb]
                self._show_error(f"{action} whom? Name someone here.")
            else:
                self._show_error("There's no one here by that description.")
            return

        self._handle_talk(hotspot, state)
        if not state.in_conversation:
            return
        character = state.characters[hotspot.target_id]
        if verb == CommandType.ACCUSE:
            self.conversation_manager.handle_accuse(character, state)
        elif verb == CommandType.THREATEN:
            self.conversation_manager.handle_threaten(character, state)
        elif verb == CommandType.SHOW:
            self.conversation_manager.handle_show_evidence(character, evidence_query, state)
        elif topic:
            self._ask_about(state, topic)

    def _ask_about(self, state: 'GameState', topic: str) -> None:
        """Open the conversation with a question about a topic."""
        character = state.characters.get(state.conversation_partner or "")
        if character is None:
            return
        self.conversation_manager.handle_free_dialogue(
            character, f"What can you tell me about {topic}?", state,
        )
        self.conversation_manager.offer_testimony(character, state)
        self.renderer.wait_for_key()

    def _show_text(self, text: str) -> None:
        """Show text and wait for key."""
        self.renderer.render_text(text)
        self.renderer.wait_for_key()

    def _show_inventory(self, state: 'GameState') -> None:
        """Show inventory and wait for key."""
        self.renderer.render_inventory(state.inventory)
        self.renderer.wait_for_key()

    def _handle_case(self, state: 'GameState') -> None:
        """Show the case file: the case, leads, evidence, and notes."""
        lines = []

        if state.spine:
            lines.append("THE CASE:")
            lines.append(f"  {state.spine.conflict_description}")
            lines.append("")

            revealed = state.spine.revealed_facts
            total = len(state.spine.revelations)
            lines.append(f"LEADS ({len(revealed)}/{total} uncovered):")
            for revelation in state.spine.revelations:
                if revelation.id in revealed:
                    lines.append(f"  [X] {revelation.description}")
                else:
                    lines.append(f"  [ ] ??? — {revelation.source}")
            lines.append("")

        discoveries = list(state.memory.player.discoveries.values())
        evidence = [d for d in discoveries if d.is_evidence]
        notes = [d for d in discoveries if not d.is_evidence]

        lines.append(f"EVIDENCE ({len(evidence)}):")
        if evidence:
            for d in evidence:
                lines.append(f"  - {d.description} [{d.source}; {d.location}]")
        else:
            lines.append("  (Nothing solid yet. Examine things. Look closer.)")

        if notes:
            lines.append("")
            lines.append("NOTES:")
            for d in notes[-10:]:
                lines.append(f"  - {d.description}")

        talked_to = state.memory.player.talked_to
        if talked_to:
            lines.append("")
            names = [
                state.characters[cid].name if cid in state.characters else cid
                for cid in talked_to
            ]
            lines.append(f"PEOPLE INTERVIEWED: {', '.join(sorted(names))}")

        lines.append("")
        lines.append("(In conversation, 'show <evidence>' puts it on the table.)")

        self.renderer.render_case_file(lines)
        self.renderer.wait_for_key()

    def _show_error(self, message: str) -> None:
        """Show error and wait for key."""
        self.renderer.render_error(message)
        self.renderer.wait_for_key()

    def _resolve_hotspot(
        self, command: Command, location: Optional[Location], state: 'GameState' = None,
    ) -> Optional[Hotspot]:
        """Resolve command target to a hotspot."""
        if not location:
            return None
        if command.hotspot_number:
            return location.get_hotspot_by_number(command.hotspot_number)
        elif command.target:
            hotspot = location.get_hotspot_by_label(command.target)
            if hotspot is None and state is not None:
                hotspot = self._resolve_person_by_name(command.target, location, state)
            return hotspot
        return None

    @staticmethod
    def _resolve_person_by_name(
        target: str, location: Location, state: 'GameState',
    ) -> Optional[Hotspot]:
        """
        Find someone here by any part of their name or role, even when the
        scene labels them differently ("talk harrow", "talk informant").
        """
        def words(text: str) -> set[str]:
            # "Sally 'Whispers' Malone" answers to whispers; o'malley to omalley
            return set(re.findall(r"[a-z0-9]+", text.lower().replace("'", "").replace("\u2019", "")))

        wanted = words(target) - {"the", "a", "an", "to", "with", "mr", "mrs", "miss"}
        if not wanted:
            return None
        for hotspot in location.get_people():
            character = state.characters.get(hotspot.target_id or "")
            if character is None:
                continue
            known = (
                words(character.name) | words(hotspot.label)
                | words(character.id.replace("_", " "))
            )
            if wanted <= known:
                return hotspot
        return None

    def _handle_hotspot_default(
        self, hotspot: Hotspot, state: 'GameState', config: GameConfig,
        current_location: Optional[Location], add_character_fn,
    ) -> None:
        """Handle default action for a hotspot."""
        default = hotspot.get_default_action()
        if default == "talk":
            self._handle_talk(hotspot, state)
        elif default == "take":
            self._handle_take(hotspot, state, config)
        elif default == "go":
            self.location_manager.handle_go(
                hotspot, current_location, state, config, add_character_fn
            )
        else:
            self._handle_examine(hotspot, state, config)

    def _get_npcs_at_location(self, state: 'GameState') -> list[str]:
        """Get character IDs of NPCs present at the player's current location."""
        location = state.locations.get(state.current_location_id)
        if not location:
            return []

        npc_ids = []
        for hotspot in location.hotspots:
            if (
                hotspot.hotspot_type == HotspotType.PERSON
                and hotspot.target_id
                and hotspot.target_id in state.characters
                and hotspot.active
            ):
                npc_ids.append(hotspot.target_id)
        return npc_ids

    def _record_witnessed_event(
        self, state: 'GameState', description: str
    ) -> None:
        """Record an event witnessed by NPCs present at the current location."""
        witness_ids = self._get_npcs_at_location(state)
        if not witness_ids:
            return

        state.memory.record_witnessed_event(
            event_type=EventType.DISCOVERY,
            description=description,
            location=state.current_location_id,
            actors=["player"],
            witnesses=witness_ids,
            player_witnessed=False,
        )

        # Feed into NPC intelligence so witnesses form subjective memories
        bridge = getattr(state, 'event_bridge', None)
        if bridge:
            bridge.bridge_event(
                event_type="discovery",
                description=description,
                location=state.current_location_id,
                actors=["player"],
                witnesses=witness_ids,
            )

    def _send_circuit_signal(
        self,
        hotspot: Hotspot,
        signal_type: SignalType,
        strength: float,
        state: 'GameState',
    ) -> Optional[ProcessingResult]:
        """Send a signal to a hotspot's circuit and route the outputs.

        Returns the ProcessingResult if the hotspot has a circuit, else None.
        """
        if not hotspot.circuit:
            return None

        signal = InputSignal(
            type=signal_type,
            strength=strength,
            source_id="player",
        )
        outputs = hotspot.circuit.receive_signal(signal)

        result = ProcessingResult(
            circuit_id=hotspot.circuit.id,
            input_signal=signal,
            output_signals=outputs,
        )

        if self.signal_router and result.has_outputs():
            location = state.locations.get(state.current_location_id)
            self.signal_router.route_outputs(result, hotspot, state, location)

        return result

    def _handle_use(self, hotspot: Hotspot, state: 'GameState', config: GameConfig) -> None:
        """Handle using an object — route through its circuit if present."""
        if hotspot.circuit:
            result = self._send_circuit_signal(
                hotspot, SignalType.PRESS, 0.5, state,
            )
            # Show use_text as flavor text
            if hotspot.use_text:
                self.renderer.render_action_result(hotspot.use_text)
        elif hotspot.use_text:
            self.renderer.render_action_result(hotspot.use_text)
        else:
            self.renderer.render_error("You can't use that.")

        if config.time_passes_on_action:
            state.memory.advance_time(config.time_units_per_action)

        self.renderer.wait_for_key()

    _INSPECTABLE_TYPES = {
        HotspotType.OBJECT, HotspotType.EVIDENCE,
        HotspotType.ITEM, HotspotType.CONTAINER,
    }

    def _handle_examine(self, hotspot: Hotspot, state: 'GameState', config: GameConfig) -> None:
        """Handle examining something."""
        first_look = not hotspot.discovered
        hotspot.mark_discovered()

        self.renderer.render_action_result(hotspot.examine_text or hotspot.description)

        # Whatever you examine is what a bare "look closer" means next
        if self.inspection_manager and hotspot.hotspot_type in self._INSPECTABLE_TYPES:
            self.inspection_manager.note_attention(hotspot, state.current_location_id)

        # First examine of a physical object: teach the zoom mechanic
        if (
            first_look
            and self.inspection_manager
            and hotspot.hotspot_type in self._INSPECTABLE_TYPES
        ):
            from .inspection_manager import definite_label
            self.renderer.render_text(
                f"(Something about {definite_label(hotspot.label)} might "
                "reward a closer look. Try 'look closer'.)"
            )

        # If hotspot has a circuit, send a LOOK signal for dynamic response
        if hotspot.circuit:
            self._send_circuit_signal(hotspot, SignalType.LOOK, 0.5, state)

        if hotspot.reveals_fact:
            state.memory.player_discovers(
                fact_id=hotspot.reveals_fact,
                description=hotspot.examine_text,
                location=state.current_location_id,
                source=f"examined {hotspot.label}",
                is_evidence=True,
                related_to=[],
            )
            self.renderer.render_discovery(hotspot.examine_text)

            advance_leads(state, self.renderer)

            # NPCs present witness the player examining evidence
            self._record_witnessed_event(
                state, f"Player examined {hotspot.label} and found evidence"
            )

        if config.time_passes_on_action:
            state.memory.advance_time(config.time_units_per_action)

        self.renderer.wait_for_key()

    def _handle_talk(self, hotspot: Hotspot, state: 'GameState') -> None:
        """Start conversation with a character."""
        if hotspot.hotspot_type.value != "person":
            self.renderer.render_error("You can't talk to that.")
            self.renderer.wait_for_key()
            return

        character_id = hotspot.target_id
        if character_id not in state.characters:
            self.renderer.render_error("That person isn't available.")
            self.renderer.wait_for_key()
            return

        state.in_conversation = True
        state.conversation_partner = character_id

        character = state.characters[character_id]
        character.record_conversation()
        state.memory.player.mark_talked_to(character_id)

    def _handle_take(self, hotspot: Hotspot, state: 'GameState', config: GameConfig) -> None:
        """Take an item."""
        if hotspot.hotspot_type.value not in ["item", "evidence"]:
            self.renderer.render_error("You can't take that.")
            self.renderer.wait_for_key()
            return

        self.renderer.render_action_result(
            hotspot.take_text or f"You take the {hotspot.label}."
        )

        if hotspot.gives_item:
            state.inventory.append(hotspot.gives_item)
            self.renderer.render_text(f"Added to inventory: {hotspot.gives_item}")

        if hotspot.reveals_fact:
            state.memory.player_discovers(
                fact_id=hotspot.reveals_fact,
                description=hotspot.examine_text,
                location=state.current_location_id,
                source=f"took {hotspot.label}",
                is_evidence=True,
            )
            self.renderer.render_discovery(hotspot.examine_text)
            advance_leads(state, self.renderer)

        # NPCs present witness the player taking something
        self._record_witnessed_event(
            state, f"Player took {hotspot.label}"
        )

        # If hotspot has a circuit, send a signal before deactivation
        if hotspot.circuit:
            self._send_circuit_signal(hotspot, SignalType.PULL, 0.5, state)

        hotspot.deactivate()

        if config.time_passes_on_action:
            state.memory.advance_time(config.time_units_per_action)

        self.renderer.wait_for_key()

    def _handle_free_exploration(
        self, player_input: str, context: dict,
        state: 'GameState', config: GameConfig, add_character_fn,
    ) -> None:
        """Handle free-form exploration input by sending to LLM for interpretation."""
        location = state.locations.get(state.current_location_id)
        if not location:
            return

        hotspots_desc = []
        for h in location.get_visible_hotspots():
            hotspots_desc.append(f"- {h.label} ({h.hotspot_type.value}): {h.description or 'no description'}")

        system_prompt = """You are interpreting player commands in a text adventure game.
Given the player's free-form input and the current scene, determine what they want to do.

Respond in JSON format with:
{
    "action": "examine|talk|take|use|kick|push|go|wait|other",
    "target": "name of target from available items/people/exits",
    "narrative": "A brief atmospheric description of what happens (1-2 sentences)",
    "success": true/false
}

RULES:
1. If the player wants to examine/look at something, action = "examine"
2. If they want to talk/speak to someone, action = "talk"
3. If they want to take/get something, action = "take"
4. If they want to go somewhere or through an exit, action = "go"
5. If they want to wait or pass time, action = "wait"
6. If they want to use, press, or activate something, action = "use"
7. If they want to kick something, action = "kick"
8. If they want to push or shove something, action = "push"
9. For anything else or if unclear, action = "other" with a narrative response
10. Match target to the closest available hotspot name
11. Write atmospheric noir-style narrative descriptions
12. If they ask a question about the environment, describe what they observe"""

        user_prompt = f"""CURRENT LOCATION: {location.name}
{location.description}

AVAILABLE IN THIS SCENE:
{chr(10).join(hotspots_desc) if hotspots_desc else "Nothing notable"}

PLAYER'S INVENTORY: {', '.join(state.inventory) if state.inventory else 'Empty'}

PLAYER SAYS: "{sanitize_player_input(player_input)}"

Interpret what the player wants to do and respond with JSON."""

        response = self.llm_client.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        if response.success and response.text:
            data, error = safe_parse_json(
                response.text, validator=validate_free_exploration_response
            )

            if data:
                action = data["action"]
                target = data["target"]
                narrative = data["narrative"]

                if narrative:
                    self.renderer.render_narration(narrative)

                if action == "examine" and target:
                    hotspot = location.get_hotspot_by_label(target)
                    if hotspot:
                        self._handle_examine(hotspot, state, config)
                        return
                elif action == "talk" and target:
                    hotspot = location.get_hotspot_by_label(target)
                    if hotspot:
                        self._handle_talk(hotspot, state)
                        return
                elif action == "take" and target:
                    hotspot = location.get_hotspot_by_label(target)
                    if hotspot:
                        self._handle_take(hotspot, state, config)
                        return
                elif action == "go" and target:
                    hotspot = location.get_hotspot_by_label(target)
                    if hotspot:
                        self.location_manager.handle_go(
                            hotspot, location, state, config, add_character_fn
                        )
                        return
                    else:
                        self.location_manager.handle_free_movement(
                            target, location, state, config, add_character_fn
                        )
                        return
                elif action == "use" and target:
                    hotspot = location.get_hotspot_by_label(target)
                    if hotspot:
                        self._handle_use(hotspot, state, config)
                        return
                elif action in ("kick", "push") and target:
                    hotspot = location.get_hotspot_by_label(target)
                    if hotspot and hotspot.circuit:
                        signal_map = {"kick": SignalType.KICK, "push": SignalType.PUSH}
                        self._send_circuit_signal(
                            hotspot, signal_map[action], 0.7, state,
                        )
                        if config.time_passes_on_action:
                            state.memory.advance_time(config.time_units_per_action)
                        self.renderer.wait_for_key()
                        return
                elif action == "wait":
                    self._handle_wait(state, config)
                    return

                self.renderer.wait_for_key()
                return

        self.renderer.render_narration("You consider your options...")
        self.renderer.wait_for_key()

    def _handle_wait(self, state: 'GameState', config: GameConfig) -> None:
        """Pass time."""
        changes = state.environment.update(WAIT_TIME_MINUTES)

        self.renderer.render_narration("Time passes...")

        if changes.get("period_changed"):
            period = changes["period_changed"]
            self.renderer.render_narration(period.get_description())

        if changes.get("weather_changed"):
            weather_desc = state.environment.weather.get_description()
            self.renderer.render_narration(weather_desc)

        for event in changes.get("time_events", []):
            if event.description:
                self.renderer.render_narration(event.description)

        state.memory.advance_time(config.time_units_per_action)

        # Update NPC intelligence: decay memories, evolve relationships, spread rumors
        prop_engine = getattr(state, 'propagation_engine', None)
        if prop_engine:
            prop_engine.update(config.time_units_per_action)

            # NPCs at the same location may gossip
            npc_ids = self._get_npcs_at_location(state)
            bridge = getattr(state, 'event_bridge', None)
            if len(npc_ids) >= 2 and bridge:
                for i in range(len(npc_ids)):
                    for j in range(i + 1, len(npc_ids)):
                        bridge.trigger_gossip(npc_ids[i], npc_ids[j])

        self.renderer.wait_for_key()

    def _handle_save(self, state: 'GameState', config: GameConfig) -> None:
        """Save the game (full world snapshot when the save system is wired)."""
        save_path = os.path.join(config.save_dir, SAVE_FILE)
        try:
            if self.save_system:
                self.save_system.save(save_path)
            else:
                state.memory.save(save_path)
            self.renderer.render_text(f"Game saved to {save_path}")
        except PermissionError:
            self.renderer.render_error("Cannot save — permission denied. Check your save directory.")
        except OSError:
            self.renderer.render_error("Cannot save — disk may be full or path is invalid.")
        except Exception as e:
            logger.error(f"Save failed: {type(e).__name__}: {e}")
            self.renderer.render_error("Save failed due to an unexpected error. Check the logs.")
        self.renderer.wait_for_key()

    def _handle_load(self, state: 'GameState', config: GameConfig) -> None:
        """
        Load a saved game (full world snapshot when the save system is
        wired): whichever is newer of your save and the quit auto-save.
        """
        save_path = os.path.join(config.save_dir, SAVE_FILE)
        if self.save_system:
            slots = [
                os.path.join(config.save_dir, name) for name in (SAVE_FILE, AUTOSAVE_FILE)
            ]
            existing = [path for path in slots if os.path.exists(path)]
            if existing:
                save_path = max(existing, key=os.path.getmtime)
        try:
            if self.save_system:
                self.save_system.load(save_path)
            else:
                state.memory = MemoryBank.load(save_path)
            if save_path.endswith(AUTOSAVE_FILE):
                self.renderer.render_text("Game loaded! (from when you last quit)")
            else:
                self.renderer.render_text("Game loaded!")
        except FileNotFoundError:
            self.renderer.render_error("No save file found.")
        except (json.JSONDecodeError, ValueError):
            self.renderer.render_error("Save file is corrupted. Starting fresh may be necessary.")
        except Exception as e:
            logger.error(f"Load failed: {type(e).__name__}: {e}")
            self.renderer.render_error("Load failed due to an unexpected error. Check the logs.")
        self.renderer.wait_for_key()

    # Defines the menu items shown in the settings screen.
    # Each tuple: (config_attr, label, is_toggle)
    _SETTINGS_ITEMS = [
        ("debug_mode",              "Debug Mode",              True),
        ("show_world_memory",       "Show World Memory",       True),
        ("time_passes_on_action",   "Time Passes on Action",   True),
        ("auto_save",               "Auto-Save",               True),
        ("npc_trust_threshold_modifier", "NPC Trust Difficulty (0.5-2.0)", False),
        ("evidence_decay_rate",     "Evidence Decay Rate (0-1.0)",        False),
    ]

    def _handle_settings(self, state: 'GameState', config: GameConfig) -> None:
        """Interactive settings menu loop."""
        while True:
            menu_items = []
            for attr, label, is_toggle in self._SETTINGS_ITEMS:
                raw_value = getattr(config, attr)
                if isinstance(raw_value, bool):
                    display = "ON" if raw_value else "OFF"
                else:
                    display = str(raw_value)
                menu_items.append({
                    "key": attr,
                    "label": label,
                    "value": display,
                    "toggleable": is_toggle,
                })

            choice = self.renderer.render_settings_menu(menu_items)

            if not choice or choice.lower() in ("back", "b", "quit", "q", "exit"):
                break

            if not choice.isdigit():
                continue

            idx = int(choice) - 1
            if idx < 0 or idx >= len(self._SETTINGS_ITEMS):
                continue

            attr, label, is_toggle = self._SETTINGS_ITEMS[idx]
            current = getattr(config, attr)

            if is_toggle:
                setattr(config, attr, not current)
            else:
                # Numeric setting — prompt for new value
                try:
                    raw = input(f"  Enter new value for {label} (current: {current}): ").strip()
                    if raw:
                        setattr(config, attr, type(current)(raw))
                except (ValueError, EOFError, KeyboardInterrupt):
                    pass
