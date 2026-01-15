"""
Game - Main game engine and loop.

Coordinates all systems and manages game state.
"""

from typing import Optional
import os
import json
import re

from .config import GameConfig, DEFAULT_CONFIG
from .memory import MemoryBank, EventType
from .character import Character, Archetype, DialogueManager
from .narrative import NarrativeSpine
from .interaction import CommandParser, Command, CommandType, Hotspot, HotspotType
from .render import Scene, Location, Renderer
from .environment import Environment, WeatherType
from .audio import create_audio_engine, AudioEngine, EmotionalState as AudioEmotion
from .llm import LLMIntegration, LocationPrompt, create_llm_client


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
        # Audio engine for TTS speech (uses mock TTS by default)
        self.audio_engine: Optional[AudioEngine] = None
        if self.config.enable_audio:
            self.audio_engine = create_audio_engine(use_mock_tts=True)
        self.speech_enabled = self.config.enable_speech

        # LLM integration for dynamic content generation
        self.llm_client = create_llm_client()
        self.location_prompt = LocationPrompt()

        # Track what directions are available from current location
        self.location_connections: dict[str, dict[str, str]] = {}

        # Genre/mood for world generation (can be changed dynamically)
        self.world_genre = "noir mystery"

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

        # Register character voice with audio engine
        if self.audio_engine:
            # Map character archetype to voice archetype
            voice_archetype = self._get_voice_archetype(character.archetype)
            self.audio_engine.create_voice_from_archetype(
                character_id=character.id,
                name=character.name,
                archetype=voice_archetype
            )

    def _get_voice_archetype(self, archetype: Archetype) -> str:
        """Map character archetype to voice archetype."""
        mapping = {
            Archetype.GUILTY: "gangster",
            Archetype.INNOCENT: "bartender",
            Archetype.OUTSIDER: "politician",
            Archetype.PROTECTOR: "informant",
            Archetype.OPPORTUNIST: "street_kid",
            Archetype.TRUE_BELIEVER: "corrupt_cop",
            Archetype.SURVIVOR: "bartender",
            Archetype.AUTHORITY: "politician",
        }
        return mapping.get(archetype, "default")

    def speak_dialogue(self, character_id: str, text: str, mood: str = "") -> None:
        """Speak dialogue using TTS if enabled."""
        if not self.speech_enabled or not self.audio_engine:
            return

        # Map mood string to audio emotion
        emotion_mapping = {
            "angrily": AudioEmotion.ANGRY,
            "sadly": AudioEmotion.SAD,
            "nervously": AudioEmotion.NERVOUS,
            "desperately": AudioEmotion.FEARFUL,
            "defensively": AudioEmotion.SUSPICIOUS,
            "defeated": AudioEmotion.TIRED,
            "happily": AudioEmotion.HAPPY,
            "excitedly": AudioEmotion.EXCITED,
        }
        emotion = emotion_mapping.get(mood.lower()) if mood else None

        # Synthesize and queue speech
        self.audio_engine.speak(character_id, text, emotion)

    def _show_dialogue(self, character: Character, text: str, mood: str = "") -> None:
        """Display dialogue and speak it using TTS."""
        # Render to screen
        self.renderer.render_dialogue(character.name, text, mood)
        # Speak with TTS
        self.speak_dialogue(character.id, text, mood)

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
        # Commands that don't require a hotspot
        simple_handlers = {
            CommandType.QUIT: self._handle_quit,
            CommandType.HELP: lambda: self._show_text(self.parser.get_help_text()),
            CommandType.INVENTORY: lambda: self._show_inventory(),
            CommandType.WAIT: self._handle_wait,
            CommandType.SAVE: self._handle_save,
            CommandType.LOAD: self._handle_load,
        }

        if command.command_type in simple_handlers:
            simple_handlers[command.command_type]()
            return

        if command.command_type == CommandType.UNKNOWN:
            # Check if this is a directional movement or free-form "go somewhere"
            raw = command.raw_input.lower().strip() if command.raw_input else ""

            # Check for directional commands: north, south, east, west, n, s, e, w
            directions = {
                "north": "north", "n": "north",
                "south": "south", "s": "south",
                "east": "east", "e": "east",
                "west": "west", "w": "west",
                "back": "back", "b": "back",
            }

            # Check if raw input is a direction
            if raw in directions:
                self._handle_direction(directions[raw])
                return

            # Check for "go [somewhere]" pattern for free-form movement
            go_match = re.match(r'^go\s+(.+)$', raw)
            if go_match:
                destination = go_match.group(1).strip()
                # Check if it's a direction
                if destination in directions:
                    self._handle_direction(directions[destination])
                else:
                    # Free-form destination - generate it!
                    self._handle_free_movement(destination)
                return

            self._show_error(self.parser.get_error_suggestion(command, context))
            return

        # Find target hotspot for commands that need one
        hotspot = self._resolve_hotspot(command)
        if not hotspot:
            # For GO commands, check if target is a direction or place name
            if command.command_type == CommandType.GO and command.target:
                target = command.target.lower()
                directions = {"north", "south", "east", "west", "back", "n", "s", "e", "w", "b"}
                if target in directions:
                    dir_map = {"n": "north", "s": "south", "e": "east", "w": "west", "b": "back"}
                    self._handle_direction(dir_map.get(target, target))
                    return
                else:
                    # Free-form destination
                    self._handle_free_movement(command.target)
                    return
            self._show_error("I don't see that here.")
            return

        # Commands that require a hotspot
        hotspot_handlers = {
            CommandType.EXAMINE: self._handle_examine,
            CommandType.TALK: self._handle_talk,
            CommandType.TAKE: self._handle_take,
            CommandType.GO: self._handle_go,
            CommandType.HOTSPOT: self._handle_hotspot_default,
        }

        handler = hotspot_handlers.get(command.command_type)
        if handler:
            handler(hotspot)

    def _handle_quit(self) -> None:
        """Handle quit command."""
        self.state.is_running = False

    def _show_text(self, text: str) -> None:
        """Show text and wait for key."""
        self.renderer.render_text(text)
        self.renderer.wait_for_key()

    def _show_inventory(self) -> None:
        """Show inventory and wait for key."""
        self.renderer.render_inventory(self.state.inventory)
        self.renderer.wait_for_key()

    def _show_error(self, message: str) -> None:
        """Show error and wait for key."""
        self.renderer.render_error(message)
        self.renderer.wait_for_key()

    def _resolve_hotspot(self, command: Command) -> Optional[Hotspot]:
        """Resolve command target to a hotspot."""
        location = self.current_location
        if command.hotspot_number:
            return location.get_hotspot_by_number(command.hotspot_number)
        elif command.target:
            return location.get_hotspot_by_label(command.target)
        return None

    def _handle_hotspot_default(self, hotspot: Hotspot) -> None:
        """Handle default action for a hotspot."""
        default_action_handlers = {
            "talk": self._handle_talk,
            "take": self._handle_take,
            "go": self._handle_go,
        }
        default = hotspot.get_default_action()
        handler = default_action_handlers.get(default, self._handle_examine)
        handler(hotspot)

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

        # If destination doesn't exist, generate it dynamically!
        if destination_id not in self.state.locations:
            self.renderer.render_narration(f"Heading towards {hotspot.label}...")
            self._generate_and_move(destination_id, hotspot.label)
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

    def _handle_direction(self, direction: str) -> None:
        """Handle directional movement (north, south, east, west, back)."""
        current_loc = self.current_location
        if not current_loc:
            return

        # Check if we have stored connections for this location
        connections = self.location_connections.get(current_loc.id, {})

        # Check existing exit hotspots for this direction
        for hotspot in current_loc.hotspots:
            if hotspot.hotspot_type == HotspotType.EXIT:
                # Check if hotspot matches direction
                label_lower = hotspot.label.lower()
                if direction in label_lower or (hasattr(hotspot, 'direction') and hotspot.direction == direction):
                    self._handle_go(hotspot)
                    return

        # No existing exit - generate new location in that direction!
        self.renderer.render_narration(f"You head {direction}...")
        self._generate_and_move(f"{current_loc.id}_{direction}", direction)

    def _handle_free_movement(self, destination: str) -> None:
        """Handle free-form movement to any place the player names."""
        current_loc = self.current_location
        if not current_loc:
            return

        # Check if this destination already exists
        dest_id = destination.lower().replace(" ", "_").replace("'", "")

        # Check existing locations for a match
        for loc_id, location in self.state.locations.items():
            if dest_id in loc_id or destination.lower() in location.name.lower():
                self.state.current_location_id = loc_id
                self.state.memory.world.record(
                    event_type=EventType.MOVEMENT,
                    description=f"Player traveled to {location.name}",
                    location=loc_id,
                    actors=["player"]
                )
                return

        # Destination doesn't exist - generate it!
        self.renderer.render_narration(f"You set out for {destination}...")
        self._generate_and_move(dest_id, destination)

    def _generate_and_move(self, dest_id: str, destination_desc: str) -> None:
        """Generate a new location via LLM and move there."""
        current_loc = self.current_location

        # Build context for generation
        story_context = ""
        if self.state.spine:
            story_context = f"Main conflict: {self.state.spine.conflict_description}"
            if hasattr(self, 'mystery'):
                story_context += f"\nVictim: {self.mystery.get('victim', 'unknown')}"

        visited = list(self.state.memory.player.locations_visited)

        # Get current environment info
        time_str = self.state.environment.time.get_period().value if self.state.environment else "night"
        weather_str = self.state.environment.weather.get_description() if self.state.environment else "clear"

        # Generate via LLM
        self.renderer.render_text("Generating new area...")

        system_prompt = self.location_prompt.get_system_prompt()
        generation_prompt = self.location_prompt.get_generation_prompt(
            current_location=current_loc.name if current_loc else "unknown",
            current_description=current_loc.description if current_loc else "",
            destination=destination_desc,
            time=time_str,
            weather=weather_str,
            genre=self.world_genre,
            story_context=story_context,
            visited_locations=visited,
            inventory=self.state.inventory
        )

        response = self.llm_client.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": generation_prompt}
        ])

        if response.success:
            location = self._parse_location_response(response.text, dest_id, destination_desc)
            if location:
                self.add_location(location, is_indoor=not location.is_outdoor)
                self.state.current_location_id = location.id

                self.state.memory.world.record(
                    event_type=EventType.MOVEMENT,
                    description=f"Player discovered {location.name}",
                    location=location.id,
                    actors=["player"]
                )

                if self.config.time_passes_on_action:
                    self.state.memory.advance_time(self.config.time_units_per_action * 2)  # Travel takes time
                return

        # Fallback: create a simple generated location
        self._create_fallback_location(dest_id, destination_desc)

    def _parse_location_response(self, text: str, fallback_id: str, fallback_name: str) -> Optional[Location]:
        """Parse LLM response into a Location object."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', text)
            if not json_match:
                return None

            data = json.loads(json_match.group())

            # Create Location
            location = Location(
                id=data.get("id", fallback_id),
                name=data.get("name", fallback_name.title()),
                description=data.get("description", f"You've arrived at {fallback_name}."),
                art=self._get_art_for_type(data.get("location_type", "generic")),
                is_outdoor=data.get("is_outdoor", True),
                ambient_description=data.get("ambient", "")
            )

            # Add hotspots from response
            for hs_data in data.get("hotspots", []):
                hs_type_str = hs_data.get("type", "object")
                hs_type = HotspotType(hs_type_str) if hs_type_str in [e.value for e in HotspotType] else HotspotType.OBJECT

                if hs_type == HotspotType.PERSON:
                    hotspot = Hotspot.create_person(
                        id=hs_data.get("id", f"hs_{hs_data.get('label', 'unknown').lower().replace(' ', '_')}"),
                        name=hs_data.get("label", "Someone"),
                        position=(30, 10),
                        character_id=hs_data.get("character_id"),
                        description=hs_data.get("description", "")
                    )
                else:
                    hotspot = Hotspot(
                        id=hs_data.get("id", f"hs_{hs_data.get('label', 'unknown').lower().replace(' ', '_')}"),
                        label=hs_data.get("label", "Something"),
                        hotspot_type=hs_type,
                        position=(30, 10),
                        description=hs_data.get("description", ""),
                        examine_text=hs_data.get("examine_text", hs_data.get("description", "")),
                        target_id=hs_data.get("exit_to") if hs_type == HotspotType.EXIT else None
                    )
                location.add_hotspot(hotspot)

            # Create any NPCs defined in response
            for npc_data in data.get("npcs", []):
                archetype_str = npc_data.get("archetype", "survivor").upper()
                try:
                    archetype = Archetype[archetype_str]
                except KeyError:
                    archetype = Archetype.SURVIVOR

                npc = Character(
                    id=npc_data.get("id", f"npc_{npc_data.get('name', 'stranger').lower().replace(' ', '_')}"),
                    name=npc_data.get("name", "A Stranger"),
                    archetype=archetype,
                    description=npc_data.get("description", ""),
                    secret_truth=npc_data.get("secret", ""),
                    public_lie=npc_data.get("public_persona", ""),
                    initial_location=location.id
                )
                for topic in npc_data.get("topics", []):
                    npc.add_topic(topic)
                self.add_character(npc)

                # Add hotspot for this NPC
                location.add_hotspot(Hotspot.create_person(
                    id=f"hs_{npc.id}",
                    name=npc.name,
                    position=(30, 10),
                    character_id=npc.id,
                    description=npc.description
                ))

            # Store connections for directional movement
            if "connections" in data:
                self.location_connections[location.id] = data["connections"]

            # Always add a "back" exit to where we came from
            current = self.current_location
            if current:
                location.add_hotspot(Hotspot(
                    id="hs_back",
                    label=f"Back to {current.name}",
                    hotspot_type=HotspotType.EXIT,
                    position=(10, 15),
                    description=f"Return to {current.name}",
                    target_id=current.id
                ))

            return location

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.renderer.render_text(f"(Generation parsing issue: {e})")
            return None

    def _create_fallback_location(self, dest_id: str, destination_desc: str) -> None:
        """Create a simple fallback location when LLM fails."""
        current = self.current_location

        location = Location(
            id=dest_id,
            name=destination_desc.title(),
            description=f"You've arrived at {destination_desc}. The area is unfamiliar.",
            art=self._get_art_for_type("generic"),
            is_outdoor=True,
            ambient_description="An unexplored area stretches before you."
        )

        # Add basic back exit
        if current:
            location.add_hotspot(Hotspot(
                id="hs_back",
                label=f"Back to {current.name}",
                hotspot_type=HotspotType.EXIT,
                position=(10, 15),
                description=f"Return to {current.name}",
                target_id=current.id
            ))

        # Add direction exits
        for direction in ["north", "south", "east", "west"]:
            location.add_hotspot(Hotspot(
                id=f"hs_{direction}",
                label=f"Go {direction.title()}",
                hotspot_type=HotspotType.EXIT,
                position=(30, 10),
                description=f"Continue {direction}",
                target_id=f"{dest_id}_{direction}"
            ))

        self.add_location(location, is_indoor=False)
        self.state.current_location_id = location.id

        self.state.memory.world.record(
            event_type=EventType.MOVEMENT,
            description=f"Player arrived at {destination_desc}",
            location=dest_id,
            actors=["player"]
        )

    def _get_art_for_type(self, location_type: str) -> list[str]:
        """Get ASCII art for a location type."""
        # Basic ASCII art templates - these would ideally come from the scenario
        art_templates = {
            "street": [
                "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
                "@@                                                                    @@",
                "@@  The road stretches ahead into the unknown...                      @@",
                "@@                                                                    @@",
                "@@     @                                              @               @@",
                "@@  FIGURE                                         FIGURE             @@",
                "@@                                                                    @@",
                "@@════════════════════════════════════════════════════════════════════@@",
                "@@                         PATH                                       @@",
                "@@════════════════════════════════════════════════════════════════════@@",
                "@@                                                                    @@",
                "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
            ],
            "wilderness": [
                "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
                "@@  @@@@   @@@@@@   @@@   @@@@@@   @@@@@   @@@@@@@   @@@@@@  @@@@@@   @@",
                "@@   @@     @@@@    @@     @@@@    @@@@     @@@@@     @@@@    @@@@    @@",
                "@@          @@             @@               @@@       @@      @@      @@",
                "@@    *           *              *                *         *         @@",
                "@@         *            *              *     *        *       *       @@",
                "@@  ~~~         ~~~          ~~~            ~~~          ~~~          @@",
                "@@     ~~~   ~~~      ~~~         ~~~    ~~~      ~~~        ~~~      @@",
                "@@  WILDERNESS STRETCHES IN ALL DIRECTIONS                           @@",
                "@@                                                                    @@",
                "@@      @                                                             @@",
                "@@     YOU                                                            @@",
                "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
            ],
            "building": [
                "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
                "@@GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG@@",
                "@@G                                                                  G@@",
                "@@G   ┌──────────────────────────────────────────────────────────┐  G@@",
                "@@G   │                                                          │  G@@",
                "@@G   │                    INTERIOR                              │  G@@",
                "@@G   │                                                          │  G@@",
                "@@G   │                       @                                  │  G@@",
                "@@G   │                      YOU                                 │  G@@",
                "@@G   │                                                          │  G@@",
                "@@G   └──────────────────────────────────────────────────────────┘  G@@",
                "@@G                                                                  G@@",
                "@@GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG@@",
                "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
            ],
            "generic": [
                "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
                "@@                                                                    @@",
                "@@                                                                    @@",
                "@@                      [ NEW LOCATION ]                              @@",
                "@@                                                                    @@",
                "@@                                                                    @@",
                "@@                            @                                       @@",
                "@@                           YOU                                      @@",
                "@@                                                                    @@",
                "@@                                                                    @@",
                "@@                                                                    @@",
                "@@                                                                    @@",
                "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
            ],
        }

        # Map various types to our templates
        type_map = {
            "street": "street",
            "road": "street",
            "path": "street",
            "bar": "building",
            "office": "building",
            "building": "building",
            "shop": "building",
            "house": "building",
            "wilderness": "wilderness",
            "forest": "wilderness",
            "mountain": "wilderness",
            "desert": "wilderness",
            "arctic": "wilderness",
            "alley": "street",
            "vehicle": "building",
            "other": "generic",
        }

        template_key = type_map.get(location_type.lower(), "generic")
        return art_templates.get(template_key, art_templates["generic"])

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
            self._show_dialogue(
                character,
                f"Fine! You want the truth? {character.secret_truth}",
                "desperately"
            )
        elif topic in character.exhausted_topics:
            self._show_dialogue(
                character,
                "I've already told you everything I know about that.",
                mood_mod
            )
        else:
            # Normal response
            if character.public_lie and not character.will_cooperate():
                self._show_dialogue(
                    character,
                    character.public_lie,
                    mood_mod
                )
            else:
                self._show_dialogue(
                    character,
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
            self._show_dialogue(
                character,
                f"Stop! I'll tell you everything! {character.secret_truth}",
                "desperately"
            )
        else:
            mood_mod = character.get_response_mood_modifier()
            self._show_dialogue(
                character,
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
                self._show_dialogue(
                    character,
                    f"How did you know? Yes... {character.secret_truth}",
                    "defeated"
                )
                self.renderer.render_game_over(
                    f"You solved the case! {character.name} was responsible.\n\n"
                    f"Dominant moral shade: {self.state.memory.player.get_dominant_shade().value}"
                )
                self.state.is_running = False
            else:
                self._show_dialogue(
                    character,
                    "You think you're so clever, but you can't prove anything!",
                    "defensively"
                )
                self.renderer.render_narration(explanation)
        else:
            # Wrong person
            self._show_dialogue(
                character,
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
