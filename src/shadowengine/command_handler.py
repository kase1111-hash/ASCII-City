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

        # "back", "go back", "leave": return to where you just were
        if raw_lower in self._BACK_WORDS or (
            command.command_type == CommandType.LEAVE and not command.target
        ):
            self._go_back(state, config, add_character_fn)
            return

        # Bare "look" / "look around": take in the room again
        if (
            command.command_type == CommandType.EXAMINE
            and not command.hotspot_number
            and (not command.target or command.target in self._LOOK_AROUND_TARGETS)
            and (not command.target or raw_lower.split()[0] in ("look", "l"))
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

        current_location = state.locations.get(state.current_location_id)

        if command.command_type == CommandType.UNKNOWN:
            raw = command.raw_input.lower().strip() if command.raw_input else ""

            directions = {
                "north": "north", "n": "north",
                "south": "south", "s": "south",
                "east": "east", "e": "east",
                "west": "west", "w": "west",
                "back": "back", "b": "back",
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
            raw = (command.raw_input or "").lower().strip()
            dir_map = {"n": "north", "s": "south", "e": "east", "w": "west"}
            if raw in dir_map or raw in dir_map.values():
                self.location_manager.handle_direction(
                    dir_map.get(raw, raw), current_location, state, config, add_character_fn
                )
                return

        # Acting on a person from the street: accuse, threaten, ask, show
        if command.command_type in (
            CommandType.ACCUSE, CommandType.THREATEN, CommandType.ASK, CommandType.SHOW,
        ):
            self._handle_person_verb(command, current_location, state)
            return

        # A bare "go" / "exit": say where you can go
        if (
            command.command_type == CommandType.GO
            and not command.target
            and not command.hotspot_number
        ):
            self._show_exits(current_location)
            return

        # "talk to mickey about marcus" talks to Mickey, then asks
        topic = None
        if command.command_type == CommandType.TALK and command.target and " about " in f" {command.target} ":
            person, _, topic = f" {command.target} ".partition(" about ")
            command.target = person.strip() or command.target
            topic = topic.strip() or None

        # Find target hotspot
        hotspot = self._resolve_hotspot(command, current_location, state)
        if not hotspot:
            if command.command_type == CommandType.GO and command.target:
                target = command.target.lower()
                dir_set = {"north", "south", "east", "west", "back", "n", "s", "e", "w", "b"}
                if target in dir_set:
                    dir_map = {"n": "north", "s": "south", "e": "east", "w": "west", "b": "back"}
                    self.location_manager.handle_direction(
                        dir_map.get(target, target), current_location, state, config, add_character_fn
                    )
                    return
                else:
                    self.location_manager.handle_free_movement(
                        command.target, current_location, state, config, add_character_fn
                    )
                    return
            self._show_error("I don't see that here.")
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
            if topic and state.in_conversation:
                self._ask_about(state, topic)

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
    _LOOK_AROUND_TARGETS = {"around", "room", "here", "about", "scene", "place"}

    def _handle_quit(self, state: 'GameState', config: GameConfig = None) -> None:
        """Quit — after asking, and with the case saved if auto-save is on."""
        if not self.renderer.render_confirm("Close the case file for tonight? (y/n)"):
            self.renderer.render_text("Back to work.")
            return

        if config is not None and config.auto_save and self.save_system:
            save_path = os.path.join(config.save_dir, "savegame.json")
            try:
                self.save_system.save(save_path)
                self.renderer.render_text(
                    f"Case saved to {save_path}. Type 'load' next time to "
                    "pick up where you left off."
                )
            except OSError as e:
                logger.error("Auto-save on quit failed: %s", e)
                self.renderer.render_error("Couldn't save the case on the way out.")
        state.is_running = False

    def _go_back(self, state: 'GameState', config: GameConfig, add_character_fn) -> None:
        """Return to the previous location (or take the way back out)."""
        previous = getattr(state, "previous_location_id", "")
        if previous and previous in state.locations and previous != state.current_location_id:
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

        location = state.locations.get(state.current_location_id)
        if location:
            for hotspot in location.get_exits_list():
                if hotspot.label.lower().startswith("back"):
                    self.location_manager.handle_go(
                        hotspot, location, state, config, add_character_fn,
                    )
                    return
        self._show_error("There's nowhere to go back to. Try 'go' to see the exits.")

    def _show_exits(self, location: Optional[Location]) -> None:
        exits = location.get_exits_list() if location else []
        if exits:
            names = ", ".join(h.label for h in exits)
            self._show_error(f"Go where? From here: {names}.")
        else:
            self._show_error("Go where? Name a place, or a direction like 'north'.")

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
    _ASK_ABOUT = re.compile(r"^(?:ask)\s+(.+?)\s+about\s+(.+)$")

    def _handle_person_verb(
        self, command: Command, location: Optional[Location], state: 'GameState',
    ) -> None:
        """
        accuse/threaten/ask/show aimed at someone in the room: walk up to
        them and do it — the conversation carries on from there.
        """
        raw = (command.raw_input or "").strip()
        raw_lower = raw.lower()
        verb = command.command_type

        person_text = command.target
        evidence_query = topic = None
        if verb == CommandType.SHOW:
            match = self._SHOW_TO.match(raw_lower)
            if not match:
                self._show_error(
                    "Show what to whom? Try 'show [evidence] to [person]', or "
                    "talk to them first."
                )
                return
            evidence_query, person_text = match.group(1), match.group(2)
        elif verb == CommandType.ASK:
            match = self._ASK_ABOUT.match(raw_lower)
            if match:
                person_text, topic = match.group(1), match.group(2)

        if not person_text:
            action = {
                CommandType.ACCUSE: "Accuse", CommandType.THREATEN: "Threaten",
                CommandType.ASK: "Ask", CommandType.SHOW: "Show",
            }[verb]
            self._show_error(f"{action} whom? Name someone here.")
            return

        for prefix in ("the ", "a ", "an "):
            if person_text.startswith(prefix):
                person_text = person_text[len(prefix):]
        hotspot = None
        if location:
            hotspot = location.get_hotspot_by_label(person_text)
            if hotspot is None or hotspot.hotspot_type != HotspotType.PERSON:
                hotspot = self._resolve_person_by_name(person_text, location, state)
        if hotspot is None or hotspot.hotspot_type != HotspotType.PERSON:
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
            return set(re.findall(r"[a-z0-9']+", text.lower()))

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
        save_path = os.path.join(config.save_dir, "savegame.json")
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
        """Load a saved game (full world snapshot when the save system is wired)."""
        save_path = os.path.join(config.save_dir, "savegame.json")
        try:
            if self.save_system:
                self.save_system.load(save_path)
            else:
                state.memory = MemoryBank.load(save_path)
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
