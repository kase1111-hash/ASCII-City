"""
CommandHandler - Routes parsed commands to appropriate handlers.

Extracted from game.py to isolate command processing, hotspot
interaction, and LLM-based free exploration into a testable module.
"""

from typing import Optional
import logging
import os
import re

from .config import GameConfig, WAIT_TIME_MINUTES
from .memory import MemoryBank, EventType
from .character import Character
from .interaction import CommandParser, Command, CommandType, Hotspot, HotspotType
from .render import Scene, Location, Renderer
from .llm.client import LLMClient
from .llm.validation import safe_parse_json, validate_free_exploration_response, sanitize_player_input
from .location_manager import LocationManager
from .conversation import ConversationManager

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
    ):
        self.parser = parser
        self.renderer = renderer
        self.llm_client = llm_client
        self.location_manager = location_manager
        self.conversation_manager = conversation_manager

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
            CommandType.QUIT: lambda: self._handle_quit(state),
            CommandType.HELP: lambda: self._show_text(self.parser.get_help_text()),
            CommandType.INVENTORY: lambda: self._show_inventory(state),
            CommandType.WAIT: lambda: self._handle_wait(state, config),
            CommandType.SAVE: lambda: self._handle_save(state, config),
            CommandType.LOAD: lambda: self._handle_load(state, config),
        }

        if command.command_type in simple_handlers:
            simple_handlers[command.command_type]()
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

        # Find target hotspot
        hotspot = self._resolve_hotspot(command, current_location)
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

    def _handle_quit(self, state: 'GameState') -> None:
        """Handle quit command."""
        state.is_running = False

    def _show_text(self, text: str) -> None:
        """Show text and wait for key."""
        self.renderer.render_text(text)
        self.renderer.wait_for_key()

    def _show_inventory(self, state: 'GameState') -> None:
        """Show inventory and wait for key."""
        self.renderer.render_inventory(state.inventory)
        self.renderer.wait_for_key()

    def _show_error(self, message: str) -> None:
        """Show error and wait for key."""
        self.renderer.render_error(message)
        self.renderer.wait_for_key()

    def _resolve_hotspot(self, command: Command, location: Optional[Location]) -> Optional[Hotspot]:
        """Resolve command target to a hotspot."""
        if not location:
            return None
        if command.hotspot_number:
            return location.get_hotspot_by_number(command.hotspot_number)
        elif command.target:
            return location.get_hotspot_by_label(command.target)
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

    def _handle_examine(self, hotspot: Hotspot, state: 'GameState', config: GameConfig) -> None:
        """Handle examining something."""
        hotspot.mark_discovered()

        self.renderer.render_action_result(hotspot.examine_text or hotspot.description)

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

            if state.spine:
                state.spine.make_revelation(hotspot.reveals_fact)

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
    "action": "examine|talk|take|go|wait|other",
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
6. For anything else or if unclear, action = "other" with a narrative response
7. Match target to the closest available hotspot name
8. Write atmospheric noir-style narrative descriptions
9. If they ask a question about the environment, describe what they observe"""

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
        self.renderer.wait_for_key()

    def _handle_save(self, state: 'GameState', config: GameConfig) -> None:
        """Save the game."""
        save_path = os.path.join(config.save_dir, "savegame.json")
        try:
            state.memory.save(save_path)
            self.renderer.render_text(f"Game saved to {save_path}")
        except Exception as e:
            self.renderer.render_error(f"Failed to save: {e}")
        self.renderer.wait_for_key()

    def _handle_load(self, state: 'GameState', config: GameConfig) -> None:
        """Load a saved game."""
        save_path = os.path.join(config.save_dir, "savegame.json")
        try:
            state.memory = MemoryBank.load(save_path)
            self.renderer.render_text("Game loaded!")
        except FileNotFoundError:
            self.renderer.render_error("No save file found.")
        except Exception as e:
            self.renderer.render_error(f"Failed to load: {e}")
        self.renderer.wait_for_key()
