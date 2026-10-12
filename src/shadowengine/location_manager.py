"""
LocationManager - Handles location generation, movement, and world building.

Extracted from game.py to isolate LLM-driven location creation and
directional movement into a testable, focused module.
"""

from typing import Optional
import logging
import re

from .config import GameConfig
from .memory import MemoryBank, EventType
from .character import Character, Archetype
from .interaction import Hotspot, HotspotType
from .render import Location, Renderer
from .llm import LocationPrompt
from .llm.client import LLMClient
from .llm.validation import safe_parse_json, validate_location_response
from .world_state import WorldState
from .generation.location_generator import LocationGenerator
from .testimony import Testimony

logger = logging.getLogger(__name__)


class LocationManager:
    """
    Manages location generation, movement between locations,
    and world-building via LLM.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        world_state: WorldState,
        renderer: Renderer,
    ):
        self.llm_client = llm_client
        self.world_state = world_state
        self.renderer = renderer
        self.location_prompt = LocationPrompt()
        self.location_generator = LocationGenerator(llm_client, world_state)

        # Track directional connections and distances
        self.location_connections: dict[str, dict[str, str]] = {}
        self.location_distances: dict[str, int] = {}

    def handle_direction(
        self,
        direction: str,
        current_location: Location,
        state: 'GameState',
        config: GameConfig,
        add_character_fn,
    ) -> None:
        """Handle directional movement (north, south, east, west, back)."""
        # Check existing exit hotspots for this direction
        for hotspot in current_location.hotspots:
            if hotspot.hotspot_type == HotspotType.EXIT:
                label_lower = hotspot.label.lower()
                if direction in label_lower or (
                    hasattr(hotspot, 'direction') and hotspot.direction == direction
                ):
                    self.handle_go(hotspot, current_location, state, config, add_character_fn)
                    return

        # No existing exit — generate new location in that direction
        self.renderer.render_narration(f"You head {direction}...")
        self.generate_and_move(
            f"{current_location.id}_{direction}",
            direction,
            current_location,
            state,
            config,
            add_character_fn,
        )

    def handle_go(
        self,
        hotspot: Hotspot,
        current_location: Optional[Location],
        state: 'GameState',
        config: GameConfig,
        add_character_fn,
    ) -> None:
        """Move to another location via an exit hotspot."""
        if hotspot.hotspot_type.value != "exit":
            self.renderer.render_error("You can't go there.")
            self.renderer.wait_for_key()
            return

        destination_id = hotspot.target_id

        # If destination doesn't exist, generate it dynamically
        if destination_id not in state.locations:
            self.renderer.render_narration(f"Heading towards {hotspot.label}...")
            self.generate_and_move(
                destination_id, hotspot.label, current_location,
                state, config, add_character_fn,
            )
            return

        state.current_location_id = destination_id

        state.memory.world.record(
            event_type=EventType.MOVEMENT,
            description=f"Player moved to {destination_id}",
            location=destination_id,
            actors=["player"],
        )

        if config.time_passes_on_action:
            state.memory.advance_time(config.time_units_per_action)

    def handle_free_movement(
        self,
        destination: str,
        current_location: Optional[Location],
        state: 'GameState',
        config: GameConfig,
        add_character_fn,
    ) -> None:
        """Handle free-form movement to any place the player names."""
        if not current_location:
            return

        # "go 7" means a number on screen, never a place called "7"
        if destination.strip().strip("[]#").isdigit():
            self.renderer.render_error(f"Nothing here is numbered {destination.strip()}.")
            self.renderer.wait_for_key()
            return

        dest_id = destination.lower().replace(" ", "_").replace("'", "")

        # Check existing locations for a match
        known_id = None
        for loc_id, location in state.locations.items():
            if dest_id == loc_id or destination.lower() == location.name.lower():
                known_id = loc_id
                break
        if known_id is None:
            known_id = self.match_known_location(destination, state)
        if known_id is not None:
            location = state.locations[known_id]
            state.current_location_id = known_id
            state.memory.world.record(
                event_type=EventType.MOVEMENT,
                description=f"Player traveled to {location.name}",
                location=known_id,
                actors=["player"],
            )
            return

        # Destination doesn't exist — generate it
        self.renderer.render_narration(f"You set out for {destination}...")
        self.generate_and_move(
            dest_id, destination, current_location,
            state, config, add_character_fn,
        )

    _PLACE_STOPWORDS = {
        "the", "a", "an", "to", "your", "my", "back", "exit", "toward",
        "towards", "into", "inside", "go", "head", "return", "through",
        "via", "out", "outside", "down", "up", "of", "onto",
    }

    @classmethod
    def _place_words(cls, text: str) -> set[str]:
        return {
            w for w in re.findall(r"[a-z0-9']+", text.lower().replace("_", " "))
            if w not in cls._PLACE_STOPWORDS
        }

    def match_known_location(self, destination: str, state: 'GameState') -> Optional[str]:
        """
        Find a known place by any name the world has used for it — its
        name, its id, or the label of an exit that leads there — so "go
        office" or "go your office building" returns to the real office
        instead of inventing a new one. Every word the player used has to
        fit; anything new is left for generation.
        """
        wanted = self._place_words(destination)
        if not wanted:
            return None

        own: dict[str, set[str]] = {
            loc_id: self._place_words(loc.name) | self._place_words(loc_id)
            for loc_id, loc in state.locations.items()
        }
        names = {loc_id: set(words) for loc_id, words in own.items()}
        for loc in state.locations.values():
            for hotspot in loc.hotspots:
                if hotspot.hotspot_type == HotspotType.EXIT and hotspot.target_id in names:
                    names[hotspot.target_id] |= self._place_words(hotspot.label)

        matches = [loc_id for loc_id, words in names.items() if wanted <= words]
        if not matches:
            return None
        # The place whose own name the player said most completely wins:
        # "go office" means the office, not "office_north"
        return min(
            matches,
            key=lambda loc_id: (len(own[loc_id] - wanted), len(names[loc_id]), loc_id),
        )

    def generate_and_move(
        self,
        dest_id: str,
        destination_desc: str,
        current_location: Optional[Location],
        state: 'GameState',
        config: GameConfig,
        add_character_fn,
    ) -> None:
        """Generate a new location via LLM and move there."""
        # Calculate distance
        current_distance = self.location_distances.get(state.current_location_id, 0)
        new_distance = current_distance + 1
        self.location_distances[dest_id] = new_distance

        # Build context
        world_context = self.world_state.get_world_context_for_generation("location")

        story_context = world_context
        if state.spine:
            story_context += f"\n\nNARRATIVE SPINE: {state.spine.conflict_description}"

        narrative_adaptation = self.world_state.get_narrative_prompt_addition(
            state.current_location_id, new_distance
        )
        story_context += f"\n\n{narrative_adaptation}"

        convergence_hint = self.world_state.check_for_story_convergence()
        if convergence_hint:
            story_context += f"\n\nSTORY CONVERGENCE: {convergence_hint}"

        visited = list(state.memory.player.visited_locations)

        time_str = state.environment.time.current_period.value if state.environment else "night"
        weather_str = state.environment.weather.get_description() if state.environment else "clear"

        self.renderer.render_text("Generating new area...")

        system_prompt = self.location_prompt.get_system_prompt()
        generation_prompt = self.location_prompt.get_generation_prompt(
            current_location=current_location.name if current_location else "unknown",
            current_description=current_location.description if current_location else "",
            destination=destination_desc,
            time=time_str,
            weather=weather_str,
            genre=self.world_state.world_genre,
            story_context=story_context,
            visited_locations=visited,
            inventory=state.inventory,
        )

        response = self.llm_client.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": generation_prompt},
        ])

        if response.success:
            location = self.parse_location_response(
                response.text, dest_id, destination_desc,
                current_location, state, add_character_fn,
            )
            if location:
                state.locations[location.id] = location
                state.environment.register_location(
                    location.id, is_indoor=not location.is_outdoor
                )
                state.current_location_id = location.id

                state.memory.world.record(
                    event_type=EventType.MOVEMENT,
                    description=f"Player discovered {location.name}",
                    location=location.id,
                    actors=["player"],
                )

                if config.time_passes_on_action:
                    state.memory.advance_time(config.time_units_per_action * 2)
                return

        # Fallback
        self.create_fallback_location(dest_id, destination_desc, current_location, state)

    def parse_location_response(
        self,
        text: str,
        fallback_id: str,
        fallback_name: str,
        current_location: Optional[Location],
        state: 'GameState',
        add_character_fn,
    ) -> Optional[Location]:
        """Parse LLM response into a Location object."""
        data, error = safe_parse_json(text, validator=validate_location_response)

        if error:
            logger.warning(f"Location generation parsing issue: {error}")
            self.renderer.render_error(f"Generation parsing issue: {error}")
            return None

        try:
            location_id = data["id"] if data["id"] else fallback_id
            location_name = data["name"] if data["name"] else fallback_name.title()

            location = Location(
                id=location_id,
                name=location_name,
                description=data["description"],
                art=LocationGenerator.get_art_for_type(data["location_type"]),
                is_outdoor=data["is_outdoor"],
                ambient_description=data["ambient"],
            )

            # Register with WorldState
            self.world_state.register_location({
                "id": location.id,
                "name": location.name,
                "location_type": data.get("location_type", "generic"),
                "description": location.description,
                "is_outdoor": location.is_outdoor,
                "connections": data.get("connections", {}),
                "generated_from": current_location.id if current_location else None,
            })

            # People first, so the scene's person hotspots can be tied to
            # real characters: everyone you can see, you can talk to
            taken_ids = set(state.characters)
            # Who each name/id in this response refers to; None means
            # someone already standing elsewhere in the world
            npc_refs: dict[str, Optional[Character]] = {}
            new_npcs: list[Character] = []
            arrivals: list[Character] = []   # existing cast turning up here
            for npc_data in data.get("npcs", []):
                existing = self._existing_character(None, npc_data.get("name"), state)
                if existing is not None:
                    # The LLM brought back someone we already know
                    npc = self._arrive(existing, location.id, state)
                    if npc is not None:
                        arrivals.append(npc)
                else:
                    npc = self._build_npc(npc_data, location.id, taken_ids)
                    new_npcs.append(npc)
                for ref in (npc_data.get("id"), npc_data.get("name")):
                    if ref:
                        npc_refs[str(ref).lower()] = npc

            # Add hotspots
            # TODO: attach BehaviorCircuits to LLM-generated hotspots based on type
            # (currently only hand-built scenarios like dockside_job create circuits)
            placed: set[str] = set()   # characters already given a place here
            for hs_data in data.get("hotspots", []):
                hs_type_str = hs_data.get("type", "object")
                hs_type = (
                    HotspotType(hs_type_str)
                    if hs_type_str in [e.value for e in HotspotType]
                    else HotspotType.OBJECT
                )
                hs_id = hs_data.get("id") or f"hs_{hs_data.get('label', 'unknown').lower().replace(' ', '_')}"

                if hs_type == HotspotType.PERSON:
                    character = self._character_for_person_hotspot(
                        hs_data, location.id, npc_refs, new_npcs, state, taken_ids,
                    )
                    if character is None or character.id in placed:
                        continue  # elsewhere in the world, or already here
                    placed.add(character.id)
                    hotspot = Hotspot.create_person(
                        id=hs_id,
                        name=hs_data.get("label") or character.name,
                        position=(30, 10),
                        character_id=character.id,
                        description=hs_data.get("description", "") or character.description,
                    )
                else:
                    hotspot = Hotspot(
                        id=hs_id,
                        label=hs_data.get("label", "Something"),
                        hotspot_type=hs_type,
                        position=(30, 10),
                        description=hs_data.get("description", ""),
                        examine_text=hs_data.get("examine_text", hs_data.get("description", "")),
                        target_id=hs_data.get("exit_to") if hs_type == HotspotType.EXIT else None,
                    )
                location.add_hotspot(hotspot)

            # Bring the newcomers into the world — and into the case
            for npc in new_npcs:
                add_character_fn(npc)
                self.world_state.register_npc({
                    "id": npc.id,
                    "name": npc.name,
                    "description": npc.description,
                    "archetype": npc.archetype.value,
                    "secret": npc.secret_truth,
                    "public_persona": npc.public_lie,
                    "topics": sorted(npc.available_topics),
                }, location.id)
                Testimony.weave_bystander(npc, state)

            for npc in new_npcs + arrivals:
                if npc.id not in placed:
                    placed.add(npc.id)
                    location.add_hotspot(Hotspot.create_person(
                        id=f"hs_{npc.id}",
                        name=npc.name,
                        position=(30, 10),
                        character_id=npc.id,
                        description=npc.description,
                    ))

            # Store connections
            if "connections" in data:
                self.location_connections[location.id] = data["connections"]

            # Back exit
            if current_location:
                location.add_hotspot(Hotspot(
                    id="hs_back",
                    label=f"Back to {current_location.name}",
                    hotspot_type=HotspotType.EXIT,
                    position=(10, 15),
                    description=f"Return to {current_location.name}",
                    target_id=current_location.id,
                ))

            return location

        except (KeyError, TypeError, ValueError) as e:
            self.renderer.render_text(f"(Location creation issue: {e})")
            return None

    @staticmethod
    def _unique_character_id(base: str, taken_ids: set[str]) -> str:
        """A character id that can't overwrite anyone already in the world."""
        base = re.sub(r"[^a-z0-9_]", "", base.lower().replace(" ", "_").replace("'", "")) or "npc"
        candidate, n = base, 2
        while candidate in taken_ids:
            candidate = f"{base}_{n}"
            n += 1
        taken_ids.add(candidate)
        return candidate

    def _build_npc(self, npc_data: dict, location_id: str, taken_ids: set[str]) -> Character:
        """Create a character from the LLM's npc entry."""
        archetype_str = str(npc_data.get("archetype", "survivor")).upper()
        try:
            archetype = Archetype[archetype_str]
        except KeyError:
            archetype = Archetype.SURVIVOR

        name = npc_data.get("name") or "A Stranger"
        npc = Character(
            id=self._unique_character_id(
                npc_data.get("id") or f"npc_{name}", taken_ids,
            ),
            name=name,
            archetype=archetype,
            description=npc_data.get("description", ""),
            secret_truth=npc_data.get("secret", ""),
            public_lie=npc_data.get("public_persona", ""),
            initial_location=location_id,
        )
        for topic in npc_data.get("topics", []):
            npc.add_topic(str(topic))
        return npc

    def _character_for_person_hotspot(
        self,
        hs_data: dict,
        location_id: str,
        npc_refs: dict[str, Character],
        new_npcs: list[Character],
        state: 'GameState',
        taken_ids: set[str],
    ) -> Optional[Character]:
        """
        Tie a person in the scene to a character. Matches this location's
        new NPCs by id or name, then the existing cast; a person nobody
        described becomes a character of their own. Returns None when the
        person is someone already present elsewhere in the world.
        """
        label = hs_data.get("label") or ""
        for ref in (hs_data.get("character_id"), label):
            if ref and str(ref).lower() in npc_refs:
                return npc_refs[str(ref).lower()]

        existing = self._existing_character(hs_data.get("character_id"), label, state)
        if existing is not None:
            return self._arrive(existing, location_id, state)

        npc = self._build_npc(
            {
                "id": f"npc_{label}" if label else "",
                "name": label or "A Stranger",
                "description": hs_data.get("description", ""),
            },
            location_id, taken_ids,
        )
        new_npcs.append(npc)
        npc_refs[npc.name.lower()] = npc
        return npc

    @staticmethod
    def _existing_character(
        character_id: Optional[str], name: Optional[str], state: 'GameState',
    ) -> Optional[Character]:
        """Someone already in the cast, by id or by name."""
        if character_id and character_id in state.characters:
            return state.characters[character_id]
        if name:
            for character in state.characters.values():
                if character.name.lower() == str(name).lower():
                    return character
        return None

    def _arrive(
        self, character: Character, location_id: str, state: 'GameState',
    ) -> Optional[Character]:
        """
        An existing character turns up in a new location — unless they're
        already standing somewhere else (or gone for good), in which case
        the scene doesn't get a duplicate.
        """
        if not character.state.is_available or self._has_presence(character.id, state):
            return None
        character.move_to(location_id)
        return character

    @staticmethod
    def _has_presence(character_id: str, state: 'GameState') -> bool:
        """Is this character already standing somewhere in the world?"""
        return any(
            hs.hotspot_type == HotspotType.PERSON
            and hs.target_id == character_id
            and hs.active
            for loc in state.locations.values()
            for hs in loc.hotspots
        )

    def create_fallback_location(
        self,
        dest_id: str,
        destination_desc: str,
        current_location: Optional[Location],
        state: 'GameState',
    ) -> None:
        """Create a simple fallback location when LLM fails."""
        location = Location(
            id=dest_id,
            name=destination_desc.title(),
            description=f"You've arrived at {destination_desc}. The area is unfamiliar.",
            art=LocationGenerator.get_art_for_type("generic"),
            is_outdoor=True,
            ambient_description="An unexplored area stretches before you.",
        )

        if current_location:
            location.add_hotspot(Hotspot(
                id="hs_back",
                label=f"Back to {current_location.name}",
                hotspot_type=HotspotType.EXIT,
                position=(10, 15),
                description=f"Return to {current_location.name}",
                target_id=current_location.id,
            ))

        for direction in ["north", "south", "east", "west"]:
            location.add_hotspot(Hotspot(
                id=f"hs_{direction}",
                label=f"Go {direction.title()}",
                hotspot_type=HotspotType.EXIT,
                position=(30, 10),
                description=f"Continue {direction}",
                target_id=f"{dest_id}_{direction}",
            ))

        state.locations[location.id] = location
        state.environment.register_location(location.id, is_indoor=False)
        state.current_location_id = location.id

        state.memory.world.record(
            event_type=EventType.MOVEMENT,
            description=f"Player arrived at {destination_desc}",
            location=dest_id,
            actors=["player"],
        )
