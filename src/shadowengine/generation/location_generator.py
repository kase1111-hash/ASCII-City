"""
Location Generator - LLM-driven location generation.

Handles procedural generation of game locations, including:
- Generating new locations from player movement
- Parsing LLM responses into Location objects
- Creating fallback locations when LLM fails
- Providing ASCII art templates for location types
"""

from typing import Optional, TYPE_CHECKING
import logging

from ..render import Location
from ..interaction import Hotspot, HotspotType
from ..character import Character, Archetype
from ..memory import EventType
from ..llm import LocationPrompt
from ..llm.validation import safe_parse_json, validate_location_response

if TYPE_CHECKING:
    from ..game import Game
    from ..world_state import WorldState
    from ..llm import LLMClient

logger = logging.getLogger(__name__)


# ASCII Art Templates for different location types
# See _get_art_for_type() for the design rationale
ASCII_ART_TEMPLATES = {
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

# Map various location types to base templates
LOCATION_TYPE_MAP = {
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


class LocationGenerator:
    """
    Handles LLM-driven location generation.

    This class encapsulates all location generation logic, providing:
    - Generation of new locations from player movement
    - Parsing of LLM responses into Location objects
    - Fallback location creation when LLM fails
    - ASCII art template selection
    """

    def __init__(self, llm_client: 'LLMClient', world_state: 'WorldState'):
        """
        Initialize the location generator.

        Args:
            llm_client: The LLM client for content generation
            world_state: The world state for consistency tracking
        """
        self.llm_client = llm_client
        self.world_state = world_state
        self.location_prompt = LocationPrompt()

    def generate_location(
        self,
        destination: str,
        current_location: Optional[Location],
        spine_context: str,
        distance_from_start: int
    ) -> Optional[Location]:
        """
        Generate a new location based on the destination description.

        Args:
            destination: The description of where the player wants to go
            current_location: The current location (for back link)
            spine_context: Narrative spine context for generation
            distance_from_start: How far from the starting location

        Returns:
            A new Location object, or None if generation failed
        """
        dest_id = f"loc_{destination.lower().replace(' ', '_').replace('.', '')}"

        # Get world context for consistency
        world_context = self.world_state.get_world_context_for_generation()
        narrative_adaptation = self.world_state.get_narrative_prompt_addition(
            current_location.id if current_location else None,
            distance_from_start
        )

        # Build generation prompt
        generation_prompt = self.location_prompt.get_generation_prompt(
            destination=destination,
            spine_context=spine_context,
            visited_locations=[],  # TODO: Pass actual visited locations
            current_weather="clear"  # TODO: Pass actual weather
        )

        # Add world context and narrative adaptation
        full_prompt = f"{generation_prompt}\n\n{world_context}\n\n{narrative_adaptation}"

        # Call LLM
        response = self.llm_client.chat([
            {"role": "system", "content": "You are generating a location for a noir mystery game. Respond with JSON only."},
            {"role": "user", "content": full_prompt}
        ])

        if response.success and response.text:
            location = self._parse_response(
                response.text,
                dest_id,
                destination,
                current_location
            )
            if location:
                return location

        # LLM failed, return None to trigger fallback
        logger.warning(f"LLM location generation failed for '{destination}'")
        return None

    def _parse_response(
        self,
        text: str,
        fallback_id: str,
        fallback_name: str,
        current_location: Optional[Location]
    ) -> Optional[Location]:
        """
        Parse LLM response into a Location object.

        Args:
            text: The raw LLM response text
            fallback_id: ID to use if not in response
            fallback_name: Name to use if not in response
            current_location: Current location for back link

        Returns:
            A Location object, or None if parsing failed
        """
        # Parse and validate JSON response
        data, error = safe_parse_json(text, validator=validate_location_response)

        if error:
            logger.warning(f"Location parsing failed: {error}")
            return None

        try:
            # Use validated data with fallbacks
            location_id = data["id"] if data["id"] else fallback_id
            location_name = data["name"] if data["name"] else fallback_name.title()

            # Create Location from validated data
            location = Location(
                id=location_id,
                name=location_name,
                description=data["description"],
                art=self.get_art_for_type(data["location_type"]),
                is_outdoor=data["is_outdoor"],
                ambient_description=data["ambient"]
            )

            # Register location with WorldState for consistency tracking
            self.world_state.register_location({
                "id": location.id,
                "name": location.name,
                "location_type": data["location_type"],
                "description": location.description,
                "is_outdoor": location.is_outdoor,
                "connections": data.get("connections", {}),
                "generated_from": current_location.id if current_location else None
            })

            # Add hotspots from response
            for hs_data in data.get("hotspots", []):
                hotspot = self._create_hotspot(hs_data)
                if hotspot:
                    location.add_hotspot(hotspot)

            # Create NPCs and add their hotspots
            existing_hs_ids = {hs.id for hs in location.hotspots}
            for idx, npc_data in enumerate(data.get("npcs", [])):
                npc = self._create_npc(npc_data, location.id)
                if npc:
                    hs_id = f"hs_{npc['id']}"
                    # Skip if already added via hotspots list (avoid duplicates)
                    if hs_id in existing_hs_ids:
                        continue
                    # Distribute NPC positions across the scene
                    npc_x = 20 + (idx * 15) % 40
                    npc_y = 8 + (idx * 5) % 10
                    location.add_hotspot(Hotspot.create_person(
                        id=hs_id,
                        name=npc['name'],
                        position=(npc_x, npc_y),
                        character_id=npc['id'],
                        description=npc['description']
                    ))
                    existing_hs_ids.add(hs_id)

            # Add back exit if we came from somewhere
            if current_location:
                location.add_hotspot(Hotspot(
                    id="hs_back",
                    label=f"Back to {current_location.name}",
                    hotspot_type=HotspotType.EXIT,
                    position=(10, 15),
                    description=f"Return to {current_location.name}",
                    target_id=current_location.id
                ))

            return location

        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Location creation failed: {e}")
            return None

    def _create_hotspot(self, hs_data: dict) -> Optional[Hotspot]:
        """Create a Hotspot from parsed data."""
        if not hs_data.get("label"):
            return None

        hs_type_str = hs_data.get("type", "object")
        try:
            hs_type = HotspotType(hs_type_str)
        except ValueError:
            hs_type = HotspotType.OBJECT

        if hs_type == HotspotType.PERSON:
            return Hotspot.create_person(
                id=hs_data.get("id", f"hs_{hs_data['label'].lower().replace(' ', '_')}"),
                name=hs_data["label"],
                position=(30, 10),
                character_id=hs_data.get("character_id"),
                description=hs_data.get("description", "")
            )
        else:
            return Hotspot(
                id=hs_data.get("id", f"hs_{hs_data['label'].lower().replace(' ', '_')}"),
                label=hs_data["label"],
                hotspot_type=hs_type,
                position=(30, 10),
                description=hs_data.get("description", ""),
                examine_text=hs_data.get("examine_text", hs_data.get("description", "")),
                target_id=hs_data.get("exit_to") if hs_type == HotspotType.EXIT else None
            )

    def _create_npc(self, npc_data: dict, location_id: str) -> Optional[dict]:
        """
        Create NPC data dict from parsed data.

        Note: The actual Character object should be created by the game
        via add_character() to properly register voice, memory, etc.
        This just returns the data needed to create it.
        """
        if not npc_data.get("name"):
            return None

        archetype_str = npc_data.get("archetype", "survivor").upper()
        try:
            archetype = Archetype[archetype_str]
        except KeyError:
            archetype = Archetype.SURVIVOR

        return {
            "id": npc_data.get("id", f"npc_{npc_data['name'].lower().replace(' ', '_')}"),
            "name": npc_data["name"],
            "archetype": archetype,
            "description": npc_data.get("description", ""),
            "secret_truth": npc_data.get("secret", ""),
            "public_lie": npc_data.get("public_persona", ""),
            "initial_location": location_id,
            "topics": npc_data.get("topics", [])
        }

    def create_fallback_location(
        self,
        destination: str,
        current_location: Optional[Location]
    ) -> Location:
        """
        Create a simple fallback location when LLM generation fails.

        Args:
            destination: The destination description
            current_location: Current location for back link

        Returns:
            A basic Location object
        """
        dest_id = f"loc_{destination.lower().replace(' ', '_').replace('.', '')}"

        location = Location(
            id=dest_id,
            name=destination.title(),
            description=f"You've arrived at {destination}. The area is unfamiliar.",
            art=self.get_art_for_type("generic"),
            is_outdoor=True
        )

        # Add a back exit
        if current_location:
            location.add_hotspot(Hotspot(
                id="hs_back",
                label=f"Back to {current_location.name}",
                hotspot_type=HotspotType.EXIT,
                position=(10, 15),
                description=f"Return to {current_location.name}",
                target_id=current_location.id
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

        return location

    @staticmethod
    def get_art_for_type(location_type: str) -> list[str]:
        """
        Get ASCII art template for a location type.

        Fallback ASCII Art Logic:
        This method provides default visual templates when the scenario doesn't
        supply custom art for a location. The templates serve three purposes:

        1. Visual Consistency: Every location has some visual representation
        2. Player Orientation: Templates include "YOU" marker for positioning
        3. Atmosphere Setting: Different templates convey different moods

        Args:
            location_type: The type of location (e.g., "street", "building")

        Returns:
            List of strings representing ASCII art lines
        """
        template_key = LOCATION_TYPE_MAP.get(location_type.lower(), "generic")
        return ASCII_ART_TEMPLATES.get(template_key, ASCII_ART_TEMPLATES["generic"])
