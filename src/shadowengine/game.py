"""
Game - Main game engine and loop.

Coordinates all systems and manages game state.
"""

from typing import Optional, Callable
import json
import os

from .config import GameConfig, DEFAULT_CONFIG
from .memory import MemoryBank, EventType
from .character import Character, Archetype, DialogueManager, DialogueTopic
from .narrative import NarrativeSpine, SpineGenerator, ConflictType
from .interaction import CommandParser, Command, CommandType, Hotspot
from .render import Scene, Location, Renderer
from .environment import Environment, WeatherType, TimePeriod


class GameState:
    """Container for all game state."""

    def __init__(self):
        self.memory = MemoryBank()
        self.characters: dict[str, Character] = {}
        self.locations: dict[str, Location] = {}
        self.current_location_id: str = ""
        self.spine: Optional[NarrativeSpine] = None
        self.dialogue_manager = DialogueManager()
        self.inventory: list[str] = []
        self.is_running: bool = True
        self.in_conversation: bool = False
        self.conversation_partner: Optional[str] = None
        self.environment: Environment = Environment()


class Game:
    """
    The main game engine.

    Manages the game loop and coordinates all subsystems.
    """

    def __init__(self, config: GameConfig = None):
        self.config = config or DEFAULT_CONFIG
        self.state = GameState()
        self.parser = CommandParser()
        self.renderer = Renderer(
            width=self.config.screen_width,
            height=self.config.screen_height
        )

    def new_game(self, seed: int = None) -> None:
        """Start a new game."""
        self.state = GameState()
        self.state.memory.game_seed = seed
        if seed is not None:
            self.state.environment.set_seed(seed)

    def add_character(self, character: Character) -> None:
        """Add a character to the game."""
        self.state.characters[character.id] = character
        self.state.memory.register_character(character.id)

    def add_location(self, location: Location, is_indoor: bool = True, **env_kwargs) -> None:
        """Add a location to the game."""
        self.state.locations[location.id] = location
        # Register location for environment tracking
        self.state.environment.register_location(
            location.id,
            is_indoor=is_indoor,
            **env_kwargs
        )

    def set_start_location(self, location_id: str) -> None:
        """Set the starting location."""
        self.state.current_location_id = location_id

    def set_spine(self, spine: NarrativeSpine) -> None:
        """Set the narrative spine."""
        self.state.spine = spine

    @property
    def current_location(self) -> Optional[Location]:
        """Get the current location."""
        return self.state.locations.get(self.state.current_location_id)

    def run(self) -> None:
        """Run the main game loop."""
        self.renderer.render_title_screen(
            "SHADOWENGINE",
            "A Procedural Storytelling Game"
        )
        self.renderer.wait_for_key()

        while self.state.is_running:
            if self.state.in_conversation:
                self._conversation_loop()
            else:
                self._exploration_loop()

        self.renderer.render_text("Thanks for playing!")

    def _exploration_loop(self) -> None:
        """Handle exploration mode."""
        location = self.current_location
        if not location:
            self.renderer.render_error("No location set!")
            self.state.is_running = False
            return

        # Mark location as visited
        self.state.memory.player.visit_location(location.id)

        # Create and render scene
        scene = Scene(location=location, width=self.config.screen_width)
        self.renderer.render_scene(scene)

        # Get player input
        raw_input = self.renderer.render_prompt()

        # Build context for parser
        context = {
            "targets": [h.label for h in location.get_visible_hotspots()],
            "hotspots": [
                {"label": h.label, "type": h.hotspot_type.value}
                for h in location.get_visible_hotspots()
            ]
        }

        # Parse command
        command = self.parser.parse(raw_input, context)

        # Handle command
        self._handle_command(command, context)

    def _handle_command(self, command: Command, context: dict) -> None:
        """Handle a parsed command."""
        location = self.current_location

        if command.command_type == CommandType.QUIT:
            self.state.is_running = False
            return

        if command.command_type == CommandType.HELP:
            self.renderer.render_text(self.parser.get_help_text())
            self.renderer.wait_for_key()
            return

        if command.command_type == CommandType.INVENTORY:
            self.renderer.render_inventory(self.state.inventory)
            self.renderer.wait_for_key()
            return

        if command.command_type == CommandType.UNKNOWN:
            self.renderer.render_error(
                self.parser.get_error_suggestion(command, context)
            )
            self.renderer.wait_for_key()
            return

        # Find target hotspot
        hotspot = None
        if command.hotspot_number:
            hotspot = location.get_hotspot_by_number(command.hotspot_number)
        elif command.target:
            hotspot = location.get_hotspot_by_label(command.target)

        if not hotspot and command.command_type not in [CommandType.WAIT, CommandType.SAVE, CommandType.LOAD]:
            self.renderer.render_error(f"I don't see that here.")
            self.renderer.wait_for_key()
            return

        # Handle specific command types
        if command.command_type == CommandType.EXAMINE:
            self._handle_examine(hotspot)
        elif command.command_type == CommandType.TALK:
            self._handle_talk(hotspot)
        elif command.command_type == CommandType.TAKE:
            self._handle_take(hotspot)
        elif command.command_type == CommandType.GO:
            self._handle_go(hotspot)
        elif command.command_type == CommandType.HOTSPOT:
            # Default action for hotspot
            if hotspot:
                default = hotspot.get_default_action()
                if default == "talk":
                    self._handle_talk(hotspot)
                elif default == "take":
                    self._handle_take(hotspot)
                elif default == "go":
                    self._handle_go(hotspot)
                else:
                    self._handle_examine(hotspot)
        elif command.command_type == CommandType.WAIT:
            self._handle_wait()
        elif command.command_type == CommandType.SAVE:
            self._handle_save()
        elif command.command_type == CommandType.LOAD:
            self._handle_load()

    def _handle_examine(self, hotspot: Hotspot) -> None:
        """Handle examining something."""
        hotspot.mark_discovered()

        self.renderer.render_action_result(hotspot.examine_text or hotspot.description)

        # Check if this reveals a fact
        if hotspot.reveals_fact:
            self.state.memory.player_discovers(
                fact_id=hotspot.reveals_fact,
                description=hotspot.examine_text,
                location=self.state.current_location_id,
                source=f"examined {hotspot.label}",
                is_evidence=True,
                related_to=[]
            )
            self.renderer.render_discovery(hotspot.examine_text)

            # Update spine if relevant
            if self.state.spine:
                self.state.spine.make_revelation(hotspot.reveals_fact)

        # Advance time
        if self.config.time_passes_on_action:
            self.state.memory.advance_time(self.config.time_units_per_action)

        self.renderer.wait_for_key()

    def _handle_talk(self, hotspot: Hotspot) -> None:
        """Start conversation with a character."""
        if hotspot.hotspot_type.value != "person":
            self.renderer.render_error("You can't talk to that.")
            self.renderer.wait_for_key()
            return

        character_id = hotspot.target_id
        if character_id not in self.state.characters:
            self.renderer.render_error("That person isn't available.")
            self.renderer.wait_for_key()
            return

        self.state.in_conversation = True
        self.state.conversation_partner = character_id

        character = self.state.characters[character_id]
        character.record_conversation()
        self.state.memory.player.mark_talked_to(character_id)

    def _handle_take(self, hotspot: Hotspot) -> None:
        """Take an item."""
        if hotspot.hotspot_type.value not in ["item", "evidence"]:
            self.renderer.render_error("You can't take that.")
            self.renderer.wait_for_key()
            return

        self.renderer.render_action_result(
            hotspot.take_text or f"You take the {hotspot.label}."
        )

        if hotspot.gives_item:
            self.state.inventory.append(hotspot.gives_item)
            self.renderer.render_text(f"Added to inventory: {hotspot.gives_item}")

        # Check if this reveals a fact
        if hotspot.reveals_fact:
            self.state.memory.player_discovers(
                fact_id=hotspot.reveals_fact,
                description=hotspot.examine_text,
                location=self.state.current_location_id,
                source=f"took {hotspot.label}",
                is_evidence=True
            )
            self.renderer.render_discovery(hotspot.examine_text)

        # Deactivate the hotspot
        hotspot.deactivate()

        if self.config.time_passes_on_action:
            self.state.memory.advance_time(self.config.time_units_per_action)

        self.renderer.wait_for_key()

    def _handle_go(self, hotspot: Hotspot) -> None:
        """Move to another location."""
        if hotspot.hotspot_type.value != "exit":
            self.renderer.render_error("You can't go there.")
            self.renderer.wait_for_key()
            return

        destination_id = hotspot.target_id
        if destination_id not in self.state.locations:
            self.renderer.render_error("That destination doesn't exist.")
            self.renderer.wait_for_key()
            return

        self.state.current_location_id = destination_id

        self.state.memory.world.record(
            event_type=EventType.MOVEMENT,
            description=f"Player moved to {destination_id}",
            location=destination_id,
            actors=["player"]
        )

        if self.config.time_passes_on_action:
            self.state.memory.advance_time(self.config.time_units_per_action)

    def _handle_wait(self) -> None:
        """Pass time."""
        # Advance environment time
        changes = self.state.environment.update(15)  # 15 minutes pass

        self.renderer.render_narration("Time passes...")

        # Report any significant changes
        if changes.get("period_changed"):
            period = changes["period_changed"]
            self.renderer.render_narration(period.get_description())

        if changes.get("weather_changed"):
            weather_desc = self.state.environment.weather.get_description()
            self.renderer.render_narration(weather_desc)

        # Handle triggered events
        for event in changes.get("time_events", []):
            if event.description:
                self.renderer.render_narration(event.description)

        self.state.memory.advance_time(5)
        self.renderer.wait_for_key()

    def _handle_save(self) -> None:
        """Save the game."""
        save_path = os.path.join(self.config.save_dir, "savegame.json")
        try:
            self.state.memory.save(save_path)
            self.renderer.render_text(f"Game saved to {save_path}")
        except Exception as e:
            self.renderer.render_error(f"Failed to save: {e}")
        self.renderer.wait_for_key()

    def _handle_load(self) -> None:
        """Load a saved game."""
        save_path = os.path.join(self.config.save_dir, "savegame.json")
        try:
            self.state.memory = MemoryBank.load(save_path)
            self.renderer.render_text("Game loaded!")
        except FileNotFoundError:
            self.renderer.render_error("No save file found.")
        except Exception as e:
            self.renderer.render_error(f"Failed to load: {e}")
        self.renderer.wait_for_key()

    def _conversation_loop(self) -> None:
        """Handle conversation mode."""
        character_id = self.state.conversation_partner
        character = self.state.characters.get(character_id)

        if not character:
            self.state.in_conversation = False
            return

        # Show character and available topics
        self.renderer.clear_screen()
        self.renderer.render_text(f"\nTalking to {character.name}")
        self.renderer.render_text(f"Mood: {character.state.mood.value}")

        if character.state.is_cracked:
            self.renderer.render_text("(They seem broken, ready to confess)")

        # Show topics
        topics = list(character.available_topics)
        if topics:
            self.renderer.render_text("\nTopics:")
            for i, topic in enumerate(topics, 1):
                exhausted = " (discussed)" if topic in character.exhausted_topics else ""
                self.renderer.render_text(f"  [{i}] {topic}{exhausted}")
        else:
            self.renderer.render_text("\nNo specific topics available.")

        self.renderer.render_text("\nCommands: ask [topic], accuse, threaten, leave")

        # Get input
        raw_input = self.renderer.render_dialogue_prompt(character.name)

        # Parse dialogue command
        command = self.parser.parse(raw_input)

        if command.command_type == CommandType.LEAVE or raw_input.lower() in ["leave", "bye", "goodbye"]:
            self.state.in_conversation = False
            self.state.conversation_partner = None
            self.renderer.render_narration(f"You end the conversation with {character.name}.")
            self.renderer.wait_for_key()
            return

        if command.command_type == CommandType.THREATEN or raw_input.lower() == "threaten":
            self._handle_threaten(character)
            return

        if command.command_type == CommandType.ACCUSE or raw_input.lower() == "accuse":
            self._handle_accuse(character)
            return

        # Try topic selection by number
        if raw_input.isdigit():
            topic_num = int(raw_input) - 1
            if 0 <= topic_num < len(topics):
                self._handle_ask_topic(character, topics[topic_num])
                return

        # Default: character responds generically
        mood_mod = character.get_response_mood_modifier()
        if character.will_cooperate():
            self.renderer.render_dialogue(
                character.name,
                "What would you like to know?",
                mood_mod
            )
        else:
            self.renderer.render_dialogue(
                character.name,
                "I don't have much to say to you.",
                mood_mod
            )

        self.renderer.wait_for_key()

    def _handle_ask_topic(self, character: Character, topic: str) -> None:
        """Handle asking about a topic."""
        mood_mod = character.get_response_mood_modifier()

        if character.state.is_cracked and character.secret_truth:
            # Reveal secret if cracked
            self.renderer.render_dialogue(
                character.name,
                f"Fine! You want the truth? {character.secret_truth}",
                "desperately"
            )
        elif topic in character.exhausted_topics:
            self.renderer.render_dialogue(
                character.name,
                "I've already told you everything I know about that.",
                mood_mod
            )
        else:
            # Normal response
            if character.public_lie and not character.will_cooperate():
                self.renderer.render_dialogue(
                    character.name,
                    character.public_lie,
                    mood_mod
                )
            else:
                self.renderer.render_dialogue(
                    character.name,
                    f"About {topic}? I suppose I can tell you what I know.",
                    mood_mod
                )
            character.exhaust_topic(topic)

        self.renderer.wait_for_key()

    def _handle_threaten(self, character: Character) -> None:
        """Handle threatening a character."""
        # Apply pressure
        cracked = character.apply_pressure(20)

        # Record moral action
        self.state.memory.player.record_moral_action(
            action_type="threaten",
            description=f"Threatened {character.name}",
            timestamp=self.state.memory.current_time,
            target=character.id,
            shade_effects={"ruthless": 0.3, "compassionate": -0.2, "idealistic": -0.1},
            weight=0.8
        )

        if cracked:
            self.renderer.render_narration(
                f"{character.name} breaks down under your pressure!"
            )
            self.renderer.render_dialogue(
                character.name,
                f"Stop! I'll tell you everything! {character.secret_truth}",
                "desperately"
            )
        else:
            mood_mod = character.get_response_mood_modifier()
            self.renderer.render_dialogue(
                character.name,
                "You don't scare me... much.",
                mood_mod
            )

        character.modify_trust(-10)
        self.renderer.wait_for_key()

    def _handle_accuse(self, character: Character) -> None:
        """Handle accusing a character."""
        character.apply_pressure(30)

        # Check if this is the real culprit
        if self.state.spine and character.id == self.state.spine.true_resolution.culprit_id:
            evidence = set(self.state.memory.player.discoveries.keys())
            is_correct, explanation = self.state.spine.check_solution(character.id, evidence)

            if is_correct:
                self.renderer.render_narration("Your accusation hits home!")
                character.state.is_cracked = True
                self.renderer.render_dialogue(
                    character.name,
                    f"How did you know? Yes... {character.secret_truth}",
                    "defeated"
                )
                self.renderer.render_game_over(
                    f"You solved the case! {character.name} was responsible.\n\n"
                    f"Dominant moral shade: {self.state.memory.player.get_dominant_shade().value}"
                )
                self.state.is_running = False
            else:
                self.renderer.render_dialogue(
                    character.name,
                    "You think you're so clever, but you can't prove anything!",
                    "defensively"
                )
                self.renderer.render_narration(explanation)
        else:
            # Wrong person
            self.renderer.render_dialogue(
                character.name,
                "What?! You're completely wrong! I didn't do anything!",
                "angrily"
            )
            character.modify_trust(-20)

        self.renderer.wait_for_key()

    def get_state_summary(self) -> dict:
        """Get a summary of the current game state."""
        return {
            "current_location": self.state.current_location_id,
            "time": self.state.memory.current_time,
            "discoveries": len(self.state.memory.player.discoveries),
            "inventory_items": len(self.state.inventory),
            "characters_met": len(self.state.memory.player.talked_to),
            "moral_shade": self.state.memory.player.get_dominant_shade().value,
            "environment": self.state.environment.get_display_status(),
            "visibility": self.state.environment.get_visibility(
                self.state.current_location_id
            ),
        }

    def set_weather(self, weather_type: WeatherType, **kwargs) -> None:
        """Set the current weather."""
        self.state.environment.set_weather(weather_type, **kwargs)

    def set_time(self, hour: int, minute: int = 0) -> None:
        """Set the current game time."""
        self.state.environment.time.set_time(hour, minute)

    def get_environment_description(self) -> list[str]:
        """Get atmospheric description for current location."""
        return self.state.environment.get_atmospheric_description(
            self.state.current_location_id
        )
