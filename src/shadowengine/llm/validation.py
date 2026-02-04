"""
LLM Response Validation - Schema validation for LLM-generated JSON.

Provides validation functions to ensure LLM responses match expected schemas,
with graceful fallbacks for malformed responses.
"""

from typing import Optional, Any
import logging


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when LLM response validation fails."""
    pass


def validate_location_response(data: dict) -> dict:
    """
    Validate and normalize a location generation response.

    Expected schema:
    {
        "id": str (optional),
        "name": str (required),
        "description": str (required),
        "location_type": str (optional, default: "generic"),
        "is_outdoor": bool (optional, default: True),
        "ambient": str (optional),
        "connections": dict (optional),
        "hotspots": list[dict] (optional),
        "npcs": list[dict] (optional)
    }

    Returns normalized data with defaults filled in.
    Raises ValidationError if required fields are missing.
    """
    if not isinstance(data, dict):
        raise ValidationError(f"Expected dict, got {type(data).__name__}")

    # Check required fields
    if "name" not in data or not data["name"]:
        raise ValidationError("Missing required field: name")
    if "description" not in data or not data["description"]:
        raise ValidationError("Missing required field: description")

    # Normalize with defaults
    normalized = {
        "id": data.get("id", ""),
        "name": str(data["name"]),
        "description": str(data["description"]),
        "location_type": str(data.get("location_type", "generic")),
        "is_outdoor": bool(data.get("is_outdoor", True)),
        "ambient": str(data.get("ambient", "")),
        "connections": data.get("connections", {}),
        "hotspots": [],
        "npcs": []
    }

    # Validate and normalize hotspots
    for hs in data.get("hotspots", []):
        if isinstance(hs, dict):
            validated_hs = validate_hotspot(hs)
            if validated_hs:
                normalized["hotspots"].append(validated_hs)

    # Validate and normalize NPCs
    for npc in data.get("npcs", []):
        if isinstance(npc, dict):
            validated_npc = validate_npc(npc)
            if validated_npc:
                normalized["npcs"].append(validated_npc)

    return normalized


def validate_hotspot(data: dict) -> Optional[dict]:
    """
    Validate and normalize a hotspot from LLM response.

    Returns normalized hotspot dict or None if invalid.
    """
    if not isinstance(data, dict):
        logger.warning(f"Invalid hotspot data type: {type(data).__name__}")
        return None

    # Label is required
    label = data.get("label", data.get("name", ""))
    if not label:
        logger.warning("Hotspot missing label/name, skipping")
        return None

    # Normalize type
    hs_type = str(data.get("type", "object")).lower()
    valid_types = {"person", "object", "item", "exit", "evidence"}
    if hs_type not in valid_types:
        hs_type = "object"

    return {
        "id": data.get("id", f"hs_{label.lower().replace(' ', '_')}"),
        "label": str(label),
        "type": hs_type,
        "description": str(data.get("description", "")),
        "examine_text": str(data.get("examine_text", data.get("description", ""))),
        "exit_to": data.get("exit_to"),
        "character_id": data.get("character_id"),
    }


def validate_npc(data: dict) -> Optional[dict]:
    """
    Validate and normalize an NPC from LLM response.

    Returns normalized NPC dict or None if invalid.
    """
    if not isinstance(data, dict):
        logger.warning(f"Invalid NPC data type: {type(data).__name__}")
        return None

    # Name is required
    name = data.get("name", "")
    if not name:
        logger.warning("NPC missing name, skipping")
        return None

    # Normalize archetype
    archetype = str(data.get("archetype", "survivor")).upper()
    valid_archetypes = {
        "GUILTY", "INNOCENT", "OUTSIDER", "PROTECTOR",
        "OPPORTUNIST", "TRUE_BELIEVER", "SURVIVOR", "AUTHORITY"
    }
    if archetype not in valid_archetypes:
        archetype = "SURVIVOR"

    return {
        "id": data.get("id", f"npc_{name.lower().replace(' ', '_')}"),
        "name": str(name),
        "archetype": archetype.lower(),
        "description": str(data.get("description", "")),
        "secret": str(data.get("secret", "")),
        "public_persona": str(data.get("public_persona", "")),
        "topics": list(data.get("topics", [])),
    }


def validate_free_exploration_response(data: dict) -> dict:
    """
    Validate and normalize a free exploration interpretation response.

    Expected schema:
    {
        "action": str (required, one of: examine, talk, take, go, wait, other),
        "target": str (optional),
        "narrative": str (required),
        "success": bool (optional, default: True)
    }
    """
    if not isinstance(data, dict):
        raise ValidationError(f"Expected dict, got {type(data).__name__}")

    # Normalize action
    action = str(data.get("action", "other")).lower()
    valid_actions = {"examine", "talk", "take", "go", "wait", "other"}
    if action not in valid_actions:
        action = "other"

    return {
        "action": action,
        "target": str(data.get("target", "")) if data.get("target") else "",
        "narrative": str(data.get("narrative", "You consider your options...")),
        "success": bool(data.get("success", True))
    }


def safe_parse_json(text: str, validator: callable = None) -> tuple[Optional[dict], Optional[str]]:
    """
    Safely parse JSON from LLM response text.

    Args:
        text: Raw text that may contain JSON
        validator: Optional validation function to apply

    Returns:
        Tuple of (parsed_data, error_message)
        If successful, error_message is None
        If failed, parsed_data is None
    """
    import json
    import re

    if not text:
        return None, "Empty response"

    # Try to extract JSON from response
    json_match = re.search(r'\{[\s\S]*\}', text)
    if not json_match:
        return None, "No JSON object found in response"

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"

    # Apply validation if provided
    if validator:
        try:
            data = validator(data)
        except ValidationError as e:
            return None, f"Validation error: {e}"
        except Exception as e:
            logger.warning(f"Unexpected validation error: {e}")
            return None, f"Validation error: {e}"

    return data, None
