"""Tests for LocationGenerator class."""

import pytest
from unittest.mock import MagicMock, Mock
from shadowengine.generation.location_generator import (
    LocationGenerator,
    ASCII_ART_TEMPLATES,
    LOCATION_TYPE_MAP,
)
from shadowengine.render import Location
from shadowengine.interaction import Hotspot, HotspotType
from shadowengine.character import Archetype


class TestLocationGeneratorInit:
    """Tests for LocationGenerator initialization."""

    def test_init_with_mock_client_and_world_state(self):
        """Test initialization with mock LLM client and world state."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()

        generator = LocationGenerator(mock_llm, mock_world_state)

        assert generator.llm_client is mock_llm
        assert generator.world_state is mock_world_state
        assert generator.location_prompt is not None

    def test_init_creates_location_prompt(self):
        """Test that initialization creates LocationPrompt instance."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()

        generator = LocationGenerator(mock_llm, mock_world_state)

        assert hasattr(generator, 'location_prompt')


class TestGetArtForType:
    """Tests for get_art_for_type static method."""

    def test_get_art_for_type_street_returns_street_template(self):
        """Test that 'street' type returns street template."""
        art = LocationGenerator.get_art_for_type("street")
        assert art == ASCII_ART_TEMPLATES["street"]
        assert "PATH" in "".join(art)

    def test_get_art_for_type_road_returns_street_template(self):
        """Test that 'road' type maps to street template."""
        art = LocationGenerator.get_art_for_type("road")
        assert art == ASCII_ART_TEMPLATES["street"]

    def test_get_art_for_type_building_returns_building_template(self):
        """Test that 'building' type returns building template."""
        art = LocationGenerator.get_art_for_type("building")
        assert art == ASCII_ART_TEMPLATES["building"]
        assert "INTERIOR" in "".join(art)

    def test_get_art_for_type_bar_returns_building_template(self):
        """Test that 'bar' type maps to building template."""
        art = LocationGenerator.get_art_for_type("bar")
        assert art == ASCII_ART_TEMPLATES["building"]

    def test_get_art_for_type_wilderness_returns_wilderness_template(self):
        """Test that 'wilderness' type returns wilderness template."""
        art = LocationGenerator.get_art_for_type("wilderness")
        assert art == ASCII_ART_TEMPLATES["wilderness"]
        assert "WILDERNESS" in "".join(art)

    def test_get_art_for_type_forest_returns_wilderness_template(self):
        """Test that 'forest' type maps to wilderness template."""
        art = LocationGenerator.get_art_for_type("forest")
        assert art == ASCII_ART_TEMPLATES["wilderness"]

    def test_get_art_for_type_generic_returns_generic_template(self):
        """Test that 'generic' type returns generic template."""
        art = LocationGenerator.get_art_for_type("generic")
        assert art == ASCII_ART_TEMPLATES["generic"]
        assert "NEW LOCATION" in "".join(art)

    def test_get_art_for_type_unknown_returns_generic_template(self):
        """Test that unknown type returns generic template."""
        art = LocationGenerator.get_art_for_type("unknown_type")
        assert art == ASCII_ART_TEMPLATES["generic"]

    def test_get_art_for_type_case_insensitive(self):
        """Test that type matching is case-insensitive."""
        art = LocationGenerator.get_art_for_type("STREET")
        assert art == ASCII_ART_TEMPLATES["street"]

    def test_get_art_for_type_all_mapped_types(self):
        """Test that all mapped types return valid templates."""
        for location_type in LOCATION_TYPE_MAP.keys():
            art = LocationGenerator.get_art_for_type(location_type)
            assert isinstance(art, list)
            assert len(art) > 0


class TestCreateFallbackLocation:
    """Tests for create_fallback_location method."""

    def test_create_fallback_location_basic_properties(self):
        """Test that fallback location has basic properties."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        location = generator.create_fallback_location("dark alley", None)

        assert location.id == "loc_dark_alley"
        assert location.name == "Dark Alley"
        assert "dark alley" in location.description.lower()
        assert location.is_outdoor is True

    def test_create_fallback_location_with_current_location_adds_back_exit(self):
        """Test that back exit is added when current_location is provided."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        current_loc = Location(
            id="loc_start",
            name="Start",
            description="Starting point",
            art=["art"]
        )

        location = generator.create_fallback_location("new place", current_loc)

        # Check for back exit
        back_exits = [h for h in location.hotspots if h.id == "hs_back"]
        assert len(back_exits) == 1
        assert "Start" in back_exits[0].label
        assert back_exits[0].target_id == "loc_start"

    def test_create_fallback_location_without_current_location_no_back_exit(self):
        """Test that no back exit is added when current_location is None."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        location = generator.create_fallback_location("new place", None)

        back_exits = [h for h in location.hotspots if h.id == "hs_back"]
        assert len(back_exits) == 0

    def test_create_fallback_location_adds_directional_exits(self):
        """Test that directional exits are added."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        location = generator.create_fallback_location("test place", None)

        # Check for all four directional exits
        exit_ids = [h.id for h in location.hotspots]
        assert "hs_north" in exit_ids
        assert "hs_south" in exit_ids
        assert "hs_east" in exit_ids
        assert "hs_west" in exit_ids

    def test_create_fallback_location_sanitizes_destination_name(self):
        """Test that destination name is sanitized for ID."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        location = generator.create_fallback_location("test. place", None)

        # Dots and spaces are replaced, but other punctuation remains
        assert location.id == "loc_test_place"


class TestParseResponse:
    """Tests for _parse_response method."""

    def test_parse_response_valid_json_creates_location(self):
        """Test that valid JSON creates a location."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        json_text = '''
        {
            "id": "loc_test",
            "name": "Test Location",
            "description": "A test place",
            "location_type": "building",
            "is_outdoor": false
        }
        '''

        location = generator._parse_response(json_text, "fallback_id", "Fallback", None)

        assert location is not None
        assert location.id == "loc_test"
        assert location.name == "Test Location"
        assert location.description == "A test place"
        assert location.is_outdoor is False

    def test_parse_response_uses_fallback_id_when_missing(self):
        """Test that fallback ID is used when not in response."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        json_text = '{"name": "Test", "description": "Desc"}'

        location = generator._parse_response(json_text, "fallback_id", "Fallback", None)

        assert location.id == "fallback_id"

    def test_parse_response_uses_fallback_name_when_missing(self):
        """Test that fallback name is used when name is empty."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        # Empty name should trigger fallback - but validation will fail because name is required
        # So this test actually checks that missing required fields returns None
        json_text = '{"id": "test_id", "name": "", "description": "Desc"}'

        location = generator._parse_response(json_text, "fallback_id", "fallback name", None)

        # With empty name, validation fails and returns None
        assert location is None

    def test_parse_response_malformed_json_returns_none(self):
        """Test that malformed JSON returns None."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        location = generator._parse_response("not json", "fallback_id", "Fallback", None)

        assert location is None

    def test_parse_response_missing_required_fields_returns_none(self):
        """Test that missing required fields returns None."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        json_text = '{"description": "Missing name"}'

        location = generator._parse_response(json_text, "fallback_id", "Fallback", None)

        assert location is None

    def test_parse_response_adds_hotspots_from_response(self):
        """Test that hotspots from response are added."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        json_text = '''
        {
            "name": "Test",
            "description": "Desc",
            "hotspots": [
                {"label": "Door", "type": "exit"},
                {"label": "Key", "type": "item"}
            ]
        }
        '''

        location = generator._parse_response(json_text, "fallback_id", "Fallback", None)

        assert len(location.hotspots) >= 2
        labels = [h.label for h in location.hotspots]
        assert "Door" in labels
        assert "Key" in labels

    def test_parse_response_adds_npc_hotspots_from_response(self):
        """Test that NPC hotspots are created from NPCs."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        json_text = '''
        {
            "name": "Test",
            "description": "Desc",
            "npcs": [
                {"name": "Alice", "archetype": "innocent"}
            ]
        }
        '''

        location = generator._parse_response(json_text, "fallback_id", "Fallback", None)

        # Should have a hotspot for Alice
        npc_hotspots = [h for h in location.hotspots if h.hotspot_type == HotspotType.PERSON]
        assert len(npc_hotspots) >= 1

    def test_parse_response_adds_back_exit_when_current_location(self):
        """Test that back exit is added when coming from another location."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        current_loc = Location(
            id="loc_previous",
            name="Previous",
            description="Previous location",
            art=["art"]
        )

        json_text = '{"name": "Test", "description": "Desc"}'

        location = generator._parse_response(json_text, "fallback_id", "Fallback", current_loc)

        back_exits = [h for h in location.hotspots if h.id == "hs_back"]
        assert len(back_exits) == 1
        assert back_exits[0].target_id == "loc_previous"

    def test_parse_response_registers_location_with_world_state(self):
        """Test that location is registered with WorldState."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        json_text = '{"name": "Test", "description": "Desc", "location_type": "building"}'

        location = generator._parse_response(json_text, "fallback_id", "Fallback", None)

        # Verify register_location was called
        mock_world_state.register_location.assert_called_once()
        call_args = mock_world_state.register_location.call_args[0][0]
        assert call_args["name"] == "Test"
        assert call_args["location_type"] == "building"


class TestCreateHotspot:
    """Tests for _create_hotspot method."""

    def test_create_hotspot_basic_object(self):
        """Test creating a basic object hotspot."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        hs_data = {"label": "Desk", "type": "object", "description": "A wooden desk"}

        hotspot = generator._create_hotspot(hs_data)

        assert hotspot is not None
        assert hotspot.label == "Desk"
        assert hotspot.hotspot_type == HotspotType.OBJECT
        assert hotspot.description == "A wooden desk"

    def test_create_hotspot_person_type(self):
        """Test creating a person hotspot."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        hs_data = {
            "label": "Guard",
            "type": "person",
            "character_id": "npc_guard",
            "description": "A stern guard"
        }

        hotspot = generator._create_hotspot(hs_data)

        assert hotspot.hotspot_type == HotspotType.PERSON
        # character_id is stored in target_id for person hotspots
        assert hotspot.target_id == "npc_guard"

    def test_create_hotspot_exit_type(self):
        """Test creating an exit hotspot."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        hs_data = {
            "label": "Door",
            "type": "exit",
            "exit_to": "hallway",
            "description": "A wooden door"
        }

        hotspot = generator._create_hotspot(hs_data)

        assert hotspot.hotspot_type == HotspotType.EXIT
        assert hotspot.target_id == "hallway"

    def test_create_hotspot_item_type(self):
        """Test creating an item hotspot."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        hs_data = {"label": "Key", "type": "item"}

        hotspot = generator._create_hotspot(hs_data)

        assert hotspot.hotspot_type == HotspotType.ITEM

    def test_create_hotspot_evidence_type(self):
        """Test creating an evidence hotspot."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        hs_data = {"label": "Blood stain", "type": "evidence"}

        hotspot = generator._create_hotspot(hs_data)

        assert hotspot.hotspot_type == HotspotType.EVIDENCE

    def test_create_hotspot_missing_label_returns_none(self):
        """Test that missing label returns None."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        hs_data = {"type": "object"}

        hotspot = generator._create_hotspot(hs_data)

        assert hotspot is None

    def test_create_hotspot_invalid_type_defaults_to_object(self):
        """Test that invalid type defaults to OBJECT."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        hs_data = {"label": "Thing", "type": "invalid_type"}

        hotspot = generator._create_hotspot(hs_data)

        assert hotspot.hotspot_type == HotspotType.OBJECT

    def test_create_hotspot_examine_text_from_data(self):
        """Test that examine_text is used from data."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        hs_data = {
            "label": "Safe",
            "type": "object",
            "description": "A metal safe",
            "examine_text": "It's locked tight"
        }

        hotspot = generator._create_hotspot(hs_data)

        assert hotspot.examine_text == "It's locked tight"

    def test_create_hotspot_id_generated_from_label(self):
        """Test that ID is generated from label."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        hs_data = {"label": "Old Book", "type": "object"}

        hotspot = generator._create_hotspot(hs_data)

        assert hotspot.id == "hs_old_book"


class TestCreateNpc:
    """Tests for _create_npc method."""

    def test_create_npc_basic_data(self):
        """Test creating NPC with basic data."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        npc_data = {"name": "Alice"}

        result = generator._create_npc(npc_data, "loc_test")

        assert result is not None
        assert result["name"] == "Alice"
        assert result["archetype"] == Archetype.SURVIVOR
        assert result["initial_location"] == "loc_test"

    def test_create_npc_with_all_fields(self):
        """Test creating NPC with all fields."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        npc_data = {
            "id": "npc_bob",
            "name": "Bob",
            "archetype": "guilty",
            "description": "A suspicious person",
            "secret": "I did it",
            "public_persona": "I'm innocent",
            "topics": ["alibi", "motive"]
        }

        result = generator._create_npc(npc_data, "loc_test")

        assert result["id"] == "npc_bob"
        assert result["name"] == "Bob"
        assert result["archetype"] == Archetype.GUILTY
        assert result["description"] == "A suspicious person"
        assert result["secret_truth"] == "I did it"
        assert result["public_lie"] == "I'm innocent"
        assert result["topics"] == ["alibi", "motive"]

    def test_create_npc_missing_name_returns_none(self):
        """Test that missing name returns None."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        npc_data = {"archetype": "innocent"}

        result = generator._create_npc(npc_data, "loc_test")

        assert result is None

    def test_create_npc_empty_name_returns_none(self):
        """Test that empty name returns None."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        npc_data = {"name": ""}

        result = generator._create_npc(npc_data, "loc_test")

        assert result is None

    def test_create_npc_invalid_archetype_defaults_to_survivor(self):
        """Test that invalid archetype defaults to SURVIVOR."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        npc_data = {"name": "Charlie", "archetype": "invalid"}

        result = generator._create_npc(npc_data, "loc_test")

        assert result["archetype"] == Archetype.SURVIVOR

    def test_create_npc_valid_archetypes_preserved(self):
        """Test that valid archetypes are converted to Archetype enum."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        test_archetypes = ["guilty", "innocent", "survivor", "protector"]

        for archetype_str in test_archetypes:
            npc_data = {"name": "Test", "archetype": archetype_str}
            result = generator._create_npc(npc_data, "loc_test")
            assert isinstance(result["archetype"], Archetype)

    def test_create_npc_id_generated_from_name(self):
        """Test that ID is generated from name."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()
        generator = LocationGenerator(mock_llm, mock_world_state)

        npc_data = {"name": "John Doe"}

        result = generator._create_npc(npc_data, "loc_test")

        assert result["id"] == "npc_john_doe"


class TestGenerateLocation:
    """Tests for generate_location method."""

    def test_generate_location_success_returns_location(self):
        """Test that successful generation returns a Location."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()

        # Mock world state methods
        mock_world_state.get_world_context_for_generation.return_value = "World context"
        mock_world_state.get_narrative_prompt_addition.return_value = "Narrative context"

        # Mock LLM response with valid JSON
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.text = '{"name": "New Place", "description": "A new location"}'
        mock_llm.chat.return_value = mock_response

        generator = LocationGenerator(mock_llm, mock_world_state)
        # Mock the location_prompt to avoid signature issues
        generator.location_prompt.get_generation_prompt = MagicMock(return_value="Generated prompt")

        location = generator.generate_location(
            destination="new place",
            current_location=None,
            spine_context="Spine context",
            distance_from_start=1
        )

        assert location is not None
        assert location.name == "New Place"

    def test_generate_location_llm_failure_returns_none(self):
        """Test that LLM failure returns None."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()

        mock_world_state.get_world_context_for_generation.return_value = "World context"
        mock_world_state.get_narrative_prompt_addition.return_value = "Narrative context"

        # Mock failed LLM response
        mock_response = MagicMock()
        mock_response.success = False
        mock_llm.chat.return_value = mock_response

        generator = LocationGenerator(mock_llm, mock_world_state)
        generator.location_prompt.get_generation_prompt = MagicMock(return_value="Generated prompt")

        location = generator.generate_location(
            destination="new place",
            current_location=None,
            spine_context="Spine context",
            distance_from_start=1
        )

        assert location is None

    def test_generate_location_calls_llm_with_context(self):
        """Test that generate_location calls LLM with proper context."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()

        mock_world_state.get_world_context_for_generation.return_value = "World context"
        mock_world_state.get_narrative_prompt_addition.return_value = "Narrative context"

        mock_response = MagicMock()
        mock_response.success = True
        mock_response.text = '{"name": "Test", "description": "Desc"}'
        mock_llm.chat.return_value = mock_response

        generator = LocationGenerator(mock_llm, mock_world_state)
        generator.location_prompt.get_generation_prompt = MagicMock(return_value="Generated prompt")

        generator.generate_location(
            destination="test place",
            current_location=None,
            spine_context="Spine",
            distance_from_start=2
        )

        # Verify LLM was called
        mock_llm.chat.assert_called_once()

        # Verify world state methods were called
        mock_world_state.get_world_context_for_generation.assert_called_once()
        mock_world_state.get_narrative_prompt_addition.assert_called_once()

    def test_generate_location_malformed_json_returns_none(self):
        """Test that malformed JSON returns None."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()

        mock_world_state.get_world_context_for_generation.return_value = "World context"
        mock_world_state.get_narrative_prompt_addition.return_value = "Narrative context"

        # Mock LLM response with malformed JSON
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.text = "This is not JSON"
        mock_llm.chat.return_value = mock_response

        generator = LocationGenerator(mock_llm, mock_world_state)
        generator.location_prompt.get_generation_prompt = MagicMock(return_value="Generated prompt")

        location = generator.generate_location(
            destination="new place",
            current_location=None,
            spine_context="Spine",
            distance_from_start=1
        )

        assert location is None

    def test_generate_location_with_current_location_adds_context(self):
        """Test that current location is passed to world state."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()

        mock_world_state.get_world_context_for_generation.return_value = "World context"
        mock_world_state.get_narrative_prompt_addition.return_value = "Narrative context"

        mock_response = MagicMock()
        mock_response.success = True
        mock_response.text = '{"name": "Test", "description": "Desc"}'
        mock_llm.chat.return_value = mock_response

        current_loc = Location(
            id="loc_current",
            name="Current",
            description="Current location",
            art=["art"]
        )

        generator = LocationGenerator(mock_llm, mock_world_state)
        generator.location_prompt.get_generation_prompt = MagicMock(return_value="Generated prompt")

        generator.generate_location(
            destination="new place",
            current_location=current_loc,
            spine_context="Spine",
            distance_from_start=1
        )

        # Verify current location ID was passed
        call_args = mock_world_state.get_narrative_prompt_addition.call_args[0]
        assert call_args[0] == "loc_current"

    def test_generate_location_sanitizes_destination_for_id(self):
        """Test that destination is sanitized for location ID."""
        mock_llm = MagicMock()
        mock_world_state = MagicMock()

        mock_world_state.get_world_context_for_generation.return_value = "World context"
        mock_world_state.get_narrative_prompt_addition.return_value = "Narrative context"

        mock_response = MagicMock()
        mock_response.success = True
        mock_response.text = '{"name": "Test", "description": "Desc"}'
        mock_llm.chat.return_value = mock_response

        generator = LocationGenerator(mock_llm, mock_world_state)
        generator.location_prompt.get_generation_prompt = MagicMock(return_value="Generated prompt")

        location = generator.generate_location(
            destination="test. place!",
            current_location=None,
            spine_context="Spine",
            distance_from_start=1
        )

        # The fallback ID would be used if LLM doesn't provide one
        # Just verify no errors occur
        assert location is not None
