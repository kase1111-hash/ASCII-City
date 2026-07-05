"""
DetailHandler - LLM-generated progressive inspection detail.

Generates zoom detail layers for anything the player looks closer at.
Each layer is generated once and cached on the InspectableObject so the
world stays consistent: once the engine says the wood is scratched,
it stays scratched.
"""

from typing import Optional, TYPE_CHECKING
import logging

from ..llm.validation import safe_parse_json, validate_detail_layer_response

if TYPE_CHECKING:
    from ..llm.client import LLMClient
    from ..world_state import WorldState

logger = logging.getLogger(__name__)


# What the eye (or lens) can resolve at each zoom level — keeps the LLM
# writing at the right physical scale instead of repeating the overview.
ZOOM_SCALE_GUIDANCE = {
    2: (  # MEDIUM
        "ARM'S LENGTH: overall condition, wear patterns, distinct features, "
        "anything odd about how it sits in the scene. No microscopic detail."
    ),
    3: (  # CLOSE
        "INCHES AWAY: fine textures (woodgrain, weave, corrosion), tool marks, "
        "faint stains, smudges, small scratches, traces left by handling."
    ),
    4: (  # FINE
        "UNDER MAGNIFICATION: individual fibers, residue, hairline cracks, "
        "minute inscriptions, particles caught in crevices. The finest detail "
        "a magnifying glass reveals."
    ),
}


class LLMDetailHandler:
    """
    Generates inspection detail layers via LLM.

    Returns validated dicts:
        {"description": str, "detail_hooks": [str], "discovery": dict|None}
    or None when the LLM is unavailable or returns garbage, in which case
    the caller falls back to template-based detail generation.
    """

    def __init__(self, llm_client: 'LLMClient', world_state: 'WorldState'):
        self.llm_client = llm_client
        self.world_state = world_state

    def generate_layer(
        self,
        object_name: str,
        base_description: str,
        zoom_value: int,
        location_name: str = "",
        location_description: str = "",
        prior_layers: list[str] = None,
        is_evidence: bool = False,
        clue_hint: Optional[str] = None,
        aspect: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Generate one detail layer.

        Args:
            object_name: What is being inspected
            base_description: Its known description
            zoom_value: ZoomLevel value (2=MEDIUM, 3=CLOSE, 4=FINE)
            location_name/location_description: Scene context
            prior_layers: Descriptions already shown at earlier zoom levels
            is_evidence: Whether this object is a known clue
            clue_hint: Hidden-truth context the discovery should connect to
            aspect: Optional viewpoint ("under it", "behind it", "the carvings")
        """
        system_prompt = self._build_system_prompt(zoom_value, is_evidence)
        user_prompt = self._build_user_prompt(
            object_name, base_description, zoom_value,
            location_name, location_description,
            prior_layers or [], clue_hint, aspect,
        )

        response = self.llm_client.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        if not (response.success and response.text):
            logger.info("Detail layer generation unavailable for '%s'", object_name)
            return None

        data, error = safe_parse_json(
            response.text, validator=validate_detail_layer_response
        )
        if error:
            logger.warning(
                "Detail layer validation failed for '%s': %s", object_name, error
            )
            return None
        return data

    def _build_system_prompt(self, zoom_value: int, is_evidence: bool) -> str:
        genre = getattr(self.world_state, "world_genre", "") or "noir mystery"
        era = getattr(self.world_state, "world_era", "") or ""
        setting = f"{era} {genre}".strip()

        if is_evidence:
            discovery_rule = (
                "This object is a CLUE. Include a \"discovery\" — one concrete, "
                "specific finding a sharp investigator would notice at this range. "
                "It must be a physical detail, not a conclusion."
            )
        elif zoom_value >= 4:
            discovery_rule = (
                "At magnification, small secrets surface. Include a \"discovery\" "
                "if the object plausibly hides one (about half the time); "
                "otherwise set it to null."
            )
        else:
            discovery_rule = (
                "Only include a \"discovery\" if it feels genuinely earned "
                "(roughly one time in three); otherwise set it to null. "
                "Ordinary objects are allowed to be ordinary."
            )

        return f"""You write close-up sensory detail for a {setting} game.
The player is inspecting an object at a specific physical distance.
Describe ONLY what is visible at that scale — never repeat the overview,
never zoom past the stated range, never narrate actions or conclusions.
Write 2-3 tight, atmospheric sentences. Concrete nouns, no purple prose.

Respond with JSON only:
{{
    "description": "what is visible at this range (2-3 sentences)",
    "detail_hooks": ["up to 2 small features worth focusing on"],
    "discovery": {{
        "fact_id": "short_snake_case_id",
        "description": "the specific thing found",
        "is_evidence": true/false,
        "reveals_object": {{
            "label": "Torn Matchbook",
            "type": "item|evidence|object|container",
            "description": "what this new object looks like"
        }} or null
    }} or null
}}

RULES:
1. {discovery_rule}
2. detail_hooks are physical features on the object (e.g. "the scratched hinge"),
   each 2-4 words, lowercase.
3. Every layer must reveal something NEW that the earlier layers did not mention.
4. Stay consistent with everything already established about the object.
5. If the discovery is a DISTINCT PHYSICAL THING that could be picked up or
   examined on its own (a hidden note, a black box wired in, a dropped
   cufflink), set discovery.reveals_object so it enters the scene.
   If the discovery is just a trace or observation, set reveals_object null."""

    def _build_user_prompt(
        self,
        object_name: str,
        base_description: str,
        zoom_value: int,
        location_name: str,
        location_description: str,
        prior_layers: list[str],
        clue_hint: Optional[str],
        aspect: Optional[str],
    ) -> str:
        scale = ZOOM_SCALE_GUIDANCE.get(zoom_value, ZOOM_SCALE_GUIDANCE[3])

        parts = [f"OBJECT: {object_name}"]
        if base_description:
            parts.append(f"KNOWN DESCRIPTION: {base_description}")
        if location_name:
            parts.append(f"SCENE: {location_name}. {location_description}".strip())

        if prior_layers:
            parts.append("ALREADY OBSERVED AT EARLIER ZOOM LEVELS:")
            for i, layer in enumerate(prior_layers, 1):
                parts.append(f"  {i}. {layer}")

        if clue_hint:
            parts.append(f"HIDDEN CONTEXT (do not state directly, let physical evidence imply it): {clue_hint}")

        if aspect:
            parts.append(f"VIEWPOINT: the player is looking specifically at {aspect}.")

        parts.append(f"CURRENT VIEWING RANGE — {scale}")
        parts.append("Describe what the player sees. JSON only.")

        return "\n".join(parts)
