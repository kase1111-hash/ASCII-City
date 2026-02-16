"""
Game - Main game engine and loop.

Thin coordinator that delegates to:
- CommandHandler: command routing, examine, take, wait, save/load
- LocationManager: location generation, movement
- ConversationManager: NPC dialogue, threats, accusations
"""

from typing import Optional
import logging

from .config import GameConfig, DEFAULT_CONFIG
from .memory import MemoryBank
from .character import Character, Archetype, DialogueManager
from .narrative import NarrativeSpine
from .interaction import CommandParser
from .render import Scene, Location, Renderer
from .environment import Environment, WeatherType
from .llm import create_llm_client
from .world_state import WorldState
from .generation.dialogue_handler import DialogueHandler
from .location_manager import LocationManager
from .conversation import ConversationManager
from .command_handler import CommandHandler
from .signal_router import SignalRouter
from .npc_intelligence import PropagationEngine
from .event_bridge import GameEventBridge

# Audio deferred — see _deferred/audio/
try:
    from .audio import create_audio_engine
    _AUDIO_AVAILABLE = True
except ImportError:
    _AUDIO_AVAILABLE = False

    def create_audio_engine(**kwargs):
        return None

logger = logging.getLogger(__name__)


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
        self.world_state: WorldState = WorldState()
        self.propagation_engine: PropagationEngine = PropagationEngine()
        self.event_bridge: GameEventBridge = GameEventBridge(self.propagation_engine)


class Game:
    """
    The main game engine.

    Manages the game loop and coordinates subsystems.
    All command handling, location generation, and conversation
    logic is delegated to focused modules.
    """

    def __init__(self, config: GameConfig = None):
        self.config = config or DEFAULT_CONFIG
        self.state = GameState()
        self.parser = CommandParser()
        self.renderer = Renderer(
            width=self.config.screen_width,
            height=self.config.screen_height,
        )

        # Audio (deferred — may not be available)
        self.audio_engine = None
        if self.config.enable_audio and _AUDIO_AVAILABLE:
            self.audio_engine = create_audio_engine(use_mock_tts=True)

        # LLM
        self.llm_client = create_llm_client()

        # Dialogue handler
        self.dialogue_handler = DialogueHandler(self.llm_client, self.state.world_state)

        # Delegates
        self.location_manager = LocationManager(
            llm_client=self.llm_client,
            world_state=self.state.world_state,
            renderer=self.renderer,
        )

        self.conversation_manager = ConversationManager(
            renderer=self.renderer,
            dialogue_handler=self.dialogue_handler,
            audio_engine=self.audio_engine,
            speech_enabled=self.config.enable_speech,
        )

        self.signal_router = SignalRouter(renderer=self.renderer)

        self.command_handler = CommandHandler(
            parser=self.parser,
            renderer=self.renderer,
            llm_client=self.llm_client,
            location_manager=self.location_manager,
            conversation_manager=self.conversation_manager,
            signal_router=self.signal_router,
        )

    # ------------------------------------------------------------------
    # Game setup
    # ------------------------------------------------------------------

    def new_game(self, seed: int = None) -> None:
        """Start a new game."""
        self.state = GameState()
        self.state.memory.game_seed = seed
        if seed is not None:
            self.state.environment.set_seed(seed)

        # Update delegates that hold references to world_state
        self.dialogue_handler = DialogueHandler(self.llm_client, self.state.world_state)
        self.location_manager = LocationManager(
            llm_client=self.llm_client,
            world_state=self.state.world_state,
            renderer=self.renderer,
        )
        self.conversation_manager = ConversationManager(
            renderer=self.renderer,
            dialogue_handler=self.dialogue_handler,
            audio_engine=self.audio_engine,
            speech_enabled=self.config.enable_speech,
        )
        self.command_handler = CommandHandler(
            parser=self.parser,
            renderer=self.renderer,
            llm_client=self.llm_client,
            location_manager=self.location_manager,
            conversation_manager=self.conversation_manager,
            signal_router=self.signal_router,
        )

    # Map Character archetypes to npc_intelligence types
    _NPC_TYPE_MAP = {
        Archetype.GUILTY: "mobster",
        Archetype.INNOCENT: "civilian",
        Archetype.OUTSIDER: "civilian",
        Archetype.PROTECTOR: "cop",
        Archetype.OPPORTUNIST: "informant",
        Archetype.TRUE_BELIEVER: "civilian",
        Archetype.SURVIVOR: "bartender",
        Archetype.AUTHORITY: "cop",
    }

    def add_character(self, character: Character) -> None:
        """Add a character to the game."""
        self.state.characters[character.id] = character
        self.state.memory.register_character(character.id)

        # Register with NPC intelligence system
        npc_type = self._NPC_TYPE_MAP.get(character.archetype, "default")
        self.state.propagation_engine.register_npc(character.id, npc_type)

        if self.audio_engine:
            voice_archetype = self._get_voice_archetype(character.archetype)
            self.audio_engine.create_voice_from_archetype(
                character_id=character.id,
                name=character.name,
                archetype=voice_archetype,
            )

    def _get_voice_archetype(self, archetype: Archetype) -> str:
        """Map character archetype to voice archetype for TTS."""
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

    def add_location(self, location: Location, is_indoor: bool = True, **env_kwargs) -> None:
        """Add a location to the game."""
        self.state.locations[location.id] = location
        self.state.environment.register_location(
            location.id, is_indoor=is_indoor, **env_kwargs
        )

    def set_start_location(self, location_id: str) -> None:
        """Set the starting location."""
        self.state.current_location_id = location_id
        self.location_manager.location_distances[location_id] = 0

    def set_spine(self, spine: NarrativeSpine) -> None:
        """Set the narrative spine."""
        self.state.spine = spine

    @property
    def current_location(self) -> Optional[Location]:
        """Get the current location."""
        return self.state.locations.get(self.state.current_location_id)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Run the main game loop."""
        self.renderer.render_title_screen(
            "SHADOWENGINE",
            "A Procedural Storytelling Game",
        )
        self.renderer.wait_for_key()

        while self.state.is_running:
            if self.state.in_conversation:
                self.conversation_manager.conversation_loop(self.state)
            else:
                self._exploration_loop()

        self.renderer.render_text("Thanks for playing!")

    def _exploration_loop(self) -> None:
        """Handle one tick of exploration mode."""
        location = self.current_location
        if not location:
            self.renderer.render_error("No location set!")
            self.state.is_running = False
            return

        self.state.memory.player.visit_location(location.id)

        scene = Scene(location=location, width=self.config.screen_width)
        self.renderer.render_scene(scene)

        raw_input = self.renderer.render_prompt()

        context = {
            "targets": [h.label for h in location.get_visible_hotspots()],
            "hotspots": [
                {"label": h.label, "type": h.hotspot_type.value}
                for h in location.get_visible_hotspots()
            ],
        }

        command = self.parser.parse(raw_input, context)

        self.command_handler.handle_command(
            command, context, self.state, self.config, self.add_character,
        )

    # ------------------------------------------------------------------
    # Convenience accessors (used by scenarios)
    # ------------------------------------------------------------------

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
