"""
InspectionManager - Wires the zoom/inspection system into the game loop.

Bridges the gap between the live world (hotspots, inventory, environment,
memory) and the inspection engine (zoom levels, tools, detail layers):

- Any hotspot becomes inspectable the first time the player looks closer,
  with detail layers generated lazily by the LLM (template fallback offline).
- Layers are cached so the world stays consistent between looks.
- Tools are recognized straight from the player's inventory.
- Darkness (night, weather, unlit rooms) limits what can be seen.
- Discoveries flow into the memory bank; NPCs present may witness the
  player scrutinizing things, feeding the rumor network.
"""

from typing import Optional, TYPE_CHECKING
import logging

from .inspection import (
    InspectionEngine, InspectionResult, InspectionIntent,
    InspectableObject, DetailLayer, ZoomLevel, ZoomConstraints,
    get_tool, get_best_tool_for_inspection,
)
from .config import SPINE_EVIDENCE_THRESHOLD
from .interaction import Hotspot, HotspotType
from .memory import EventType
from .generation.detail_handler import LLMDetailHandler

if TYPE_CHECKING:
    from .interaction import Hotspot
    from .render import Location, Renderer
    from .llm.client import LLMClient
    from .world_state import WorldState

logger = logging.getLogger(__name__)

_ARTICLES = {"the", "a", "an", "your", "his", "her", "their", "its", "some"}


def definite_label(name: str) -> str:
    """'Your Desk' -> 'your desk', 'Dumpster' -> 'the dumpster'."""
    lower = name.strip().lower()
    if not lower:
        return "it"
    if lower.split()[0] in _ARTICLES:
        return lower
    return f"the {lower}"


def check_location_leads(state, renderer: 'Renderer') -> None:
    """
    Piece leads together from accumulated evidence.

    A revelation tagged with a location_id is satisfied once the player
    has gathered enough evidence discoveries at that location — so clues
    the LLM invented on the spot can still advance the authored case.
    """
    spine = state.spine
    if not spine:
        return

    counts: dict[str, int] = {}
    for discovery in state.memory.player.discoveries.values():
        if discovery.is_evidence:
            counts[discovery.location] = counts.get(discovery.location, 0) + 1

    for revelation in spine.revelations:
        location_id = getattr(revelation, "location_id", None)
        if not location_id or revelation.id in spine.revealed_facts:
            continue
        if counts.get(location_id, 0) < SPINE_EVIDENCE_THRESHOLD:
            continue
        # make_revelation enforces prerequisites; if they aren't met yet,
        # this quietly retries the next time evidence lands here
        if spine.make_revelation(revelation.id):
            renderer.render_narration(
                "The pieces click together. What you've found here "
                "adds up to something."
            )
            renderer.render_discovery(f"LEAD UNCOVERED: {revelation.description}")


def guess_material(text: str) -> Optional[str]:
    """Cheap material guess so template details read naturally offline."""
    lower = text.lower()
    for keyword, material in (
        ("wood", "wood"), ("desk", "wood"), ("door", "wood"), ("crate", "wood"),
        ("booth", "wood"), ("counter", "wood"), ("chair", "wood"),
        ("metal", "metal"), ("brass", "metal"), ("iron", "metal"),
        ("steel", "metal"), ("ladder", "metal"), ("dumpster", "metal"),
        ("pipe", "metal"), ("escape", "metal"), ("lamppost", "metal"),
        ("stone", "stone"), ("brick", "stone"), ("concrete", "stone"),
        ("wall", "stone"), ("pavement", "stone"),
    ):
        if keyword in lower:
            return material
    return None


# Visibility below this is too dark for close inspection without a light
DARKNESS_THRESHOLD = 0.35

# Inventory keywords -> inspection tool ids (checked in order; "magnif"
# must come before any bare "glass" style matching)
TOOL_KEYWORDS = [
    ("magnif", "magnifying_glass"),
    ("loupe", "jewelers_loupe"),
    ("telescope", "telescope"),
    ("spyglass", "telescope"),
    ("lantern", "lantern"),
    ("flashlight", "lantern"),
    ("torch", "lantern"),
    ("uv light", "uv_light"),
    ("uv lamp", "uv_light"),
    ("blacklight", "uv_light"),
    ("spectacle", "spectacles"),
    ("stethoscope", "stethoscope"),
    ("mirror", "mirror"),
    ("probe", "probe"),
]

# Sensory tools reveal what zooming can't: each generates its own
# tool-flavored detail instead of stepping through zoom levels.
# (Magnifying tools — glass, loupe, telescope — use the zoom path.)
TOOL_ASPECTS = {
    "uv_light": (
        "it under ultraviolet light — reveal ONLY what UV shows: cleaned "
        "stains, organic traces, invisible marks, treated surfaces",
        "You sweep the ultraviolet lamp across {label}. The visible world "
        "falls away...",
    ),
    "stethoscope": (
        "it through a stethoscope pressed against it — reveal ONLY what can "
        "be heard: mechanisms, hollows, movement, ticking, flowing",
        "You press the stethoscope to {label} and close your eyes...",
    ),
    "mirror": (
        "its hidden faces using an angled mirror — reveal ONLY what is "
        "normally out of sight: undersides, back panels, recesses",
        "You angle the mirror to see what {label} keeps hidden...",
    ),
    "probe": (
        "its gaps and openings explored with a thin probe — reveal ONLY "
        "what touch finds: obstructions, hidden catches, lodged objects",
        "You work the thin probe into {label}...",
    ),
}

# First words that always mean movement, never inspection
_MOVEMENT_WORDS = {
    "go", "walk", "move", "head", "enter", "exit", "leave", "travel",
    "run", "back", "b", "n", "s", "e", "w",
    "north", "south", "east", "west",
}

# Intents this manager handles; everything else stays with the normal flow
_HANDLED_INTENTS = {
    InspectionIntent.ZOOM_IN,
    InspectionIntent.ZOOM_OUT,
    InspectionIntent.USE_TOOL,
    InspectionIntent.LOOK_DIRECTION,
    InspectionIntent.FOCUS,
    InspectionIntent.RESET,
}


class InspectionManager:
    """Runtime bridge between hotspots and the inspection engine."""

    def __init__(
        self,
        llm_client: 'LLMClient',
        world_state: 'WorldState',
        renderer: 'Renderer',
        seed: Optional[int] = None,
    ):
        self.engine = InspectionEngine(seed=seed)
        self.detail_handler = LLMDetailHandler(llm_client, world_state)
        self.renderer = renderer

        self._object_by_hotspot: dict[str, str] = {}   # hotspot.id -> object.id
        self._hotspot_by_object: dict[str, str] = {}   # object.id -> hotspot.id
        self._layers_attempted: dict[str, set[int]] = {}
        self._fact_details: dict[str, dict] = {}       # fact_id -> discovery dict
        self._recorded_facts: set[str] = set()
        self._granted_items: set[tuple[str, str]] = set()
        self._aspect_cache: dict[tuple[str, str], dict] = {}
        self._tool_line: Optional[str] = None          # flavor line for tool use

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def wants_inspection(self, raw_input: str) -> bool:
        """
        Decide whether player input is a close-inspection command.

        Deliberately conservative: plain "examine X" / "look at X" stays
        with the normal examine flow; movement and numeric selection are
        never intercepted.
        """
        text = (raw_input or "").strip().lower()
        if not text or text[0].isdigit():
            return False

        first = text.split()[0]
        if first in _MOVEMENT_WORDS:
            return False

        command = self.engine.parser.parse(text)
        return command.intent in _HANDLED_INTENTS

    def handle(self, raw_input: str, state: 'GameState', config) -> bool:
        """
        Handle an inspection command.

        Returns True if fully handled; False to let the normal command
        flow (including LLM free exploration) take over.
        """
        location = state.locations.get(state.current_location_id)
        if not location:
            return False

        command = self.engine.parser.parse(raw_input)
        self.engine.current_location = state.current_location_id
        self._sync_tools(state)
        self._sync_light(state)

        # Resolve the target: explicit label, or the last thing inspected here
        if command.target:
            hotspot = location.get_hotspot_by_label(command.target)
            if hotspot is None:
                # Unknown target — let the LLM free-exploration narrate it
                return False
            obj = self._ensure_object(hotspot, state)
        else:
            obj = self._recent_object(location)
            if obj is None:
                if command.intent in (InspectionIntent.ZOOM_OUT, InspectionIntent.RESET):
                    self.renderer.render_narration("You take in the scene as a whole again.")
                else:
                    self.renderer.render_narration(
                        "Look closer at what? Try examining something first."
                    )
                self.renderer.wait_for_key()
                return True
            hotspot = self._hotspot_for(obj, location)
            if hotspot is None:
                return False

        result = self._dispatch(command, obj, hotspot, state)
        if result is None:
            # Already rendered a terminal message (missing tool, personal space)
            self.renderer.wait_for_key()
            return True

        self._render_result(obj, result)
        self._apply_result(result, hotspot, state, config, location)
        self.renderer.wait_for_key()
        return True

    # ------------------------------------------------------------------
    # Command dispatch
    # ------------------------------------------------------------------

    def _dispatch(
        self, command, obj: InspectableObject, hotspot: 'Hotspot', state,
    ) -> Optional[InspectionResult]:
        intent = command.intent

        if intent == InspectionIntent.ZOOM_IN:
            return self._do_zoom_in(obj, hotspot, state)

        if intent == InspectionIntent.ZOOM_OUT:
            return self.engine.zoom_out_from(obj.id)

        if intent == InspectionIntent.RESET:
            self.engine.zoom_manager.reset_zoom(obj.id)
            result = InspectionResult(
                success=True,
                description=(
                    f"You step back from {definite_label(obj.name)} "
                    "and take in the whole of it again."
                ),
                zoom_level=ZoomLevel.COARSE,
                zoom_changed=True,
            )
            result._verbatim = True
            return result

        if intent == InspectionIntent.USE_TOOL:
            return self._do_tool(command, obj, hotspot, state)

        if intent in (InspectionIntent.LOOK_DIRECTION, InspectionIntent.FOCUS):
            return self._do_aspect(command, obj, hotspot, state)

        return None

    def _do_zoom_in(
        self, obj: InspectableObject, hotspot: 'Hotspot', state,
    ) -> Optional[InspectionResult]:
        current = self.engine.zoom_manager.get_current_zoom(obj.id)

        # People get a hard, in-fiction proximity limit
        if (
            hotspot.hotspot_type == HotspotType.PERSON
            and current.value >= ZoomLevel.CLOSE.value
        ):
            self.renderer.render_narration(
                f"{hotspot.label} shifts under your stare. Any closer and this "
                "stops being detective work. Some things you learn by talking."
            )
            return None

        # Too dark to make out finer detail without a light source
        if not self.engine.has_light and current.value >= ZoomLevel.MEDIUM.value:
            self.renderer.render_narration(
                f"It's too dark to make out finer detail on "
                f"{definite_label(obj.name)}. You'd need a light."
            )
            return None

        if current.can_zoom_in():
            self._ensure_layer(obj, current.zoom_in(), hotspot, state)

        tool = get_best_tool_for_inspection(
            self.engine.player_tools, needs_magnification=True
        )
        return self.engine.zoom_in_on(obj.id, tool)

    def _do_tool(
        self, command, obj: InspectableObject, hotspot: 'Hotspot', state,
    ) -> Optional[InspectionResult]:
        tool = self.engine.get_tool_by_id(command.tool)
        if tool is None:
            nice_name = (command.tool or "tool").replace("_", " ")
            self.renderer.render_error(f"You don't have a {nice_name}.")
            return None

        # Sensory tools (UV, stethoscope, mirror, probe) reveal their own
        # kind of detail rather than stepping through zoom levels
        if tool.id in TOOL_ASPECTS:
            return self._do_tool_aspect(tool, obj, hotspot, state)

        current = self.engine.zoom_manager.get_current_zoom(obj.id)
        target_value = min(
            current.value + tool.zoom_bonus + 1, ZoomLevel.FINE.value
        )
        for value in range(ZoomLevel.MEDIUM.value, target_value + 1):
            self._ensure_layer(obj, ZoomLevel(value), hotspot, state)

        if not tool.can_inspect(obj.is_distant, obj.size, self.engine.has_light):
            return InspectionResult(
                success=False,
                description=tool.fail_text.format(tool=tool.name, target=obj.name),
                zoom_level=current,
            )

        self._tool_line = tool.get_inspection_text(obj.name)
        return self.engine.inspect_object(obj.id, ZoomLevel(target_value), tool)

    def _do_tool_aspect(
        self, tool, obj: InspectableObject, hotspot: 'Hotspot', state,
    ) -> InspectionResult:
        """A sensory tool's unique view of an object (cached per pair)."""
        aspect_prompt, lead_template = TOOL_ASPECTS[tool.id]
        label = definite_label(obj.name)
        lead_in = lead_template.format(label=label)

        cache_key = (obj.id, f"tool:{tool.id}")
        data = self._aspect_cache.get(cache_key)
        if data is None:
            location = state.locations.get(state.current_location_id)
            data = self.detail_handler.generate_layer(
                object_name=obj.name,
                base_description=obj.base_description,
                zoom_value=ZoomLevel.FINE.value,
                location_name=location.name if location else "",
                location_description=location.description if location else "",
                prior_layers=self._layer_descriptions(obj),
                is_evidence=self._is_evidence(hotspot),
                clue_hint=self._clue_hint(hotspot),
                aspect=aspect_prompt,
                scale_override=(
                    "THROUGH THE INSTRUMENT: describe only what this "
                    "instrument can reveal — nothing the naked eye would see."
                ),
            )
            if data is not None:
                self._aspect_cache[cache_key] = data

        if data is None:
            result = InspectionResult(
                success=True,
                description=(
                    f"{lead_in}\n\nNothing out of the ordinary presents "
                    "itself this time."
                ),
                zoom_level=ZoomLevel.FINE,
            )
            result._verbatim = True
            return result

        new_facts = []
        discovery = data.get("discovery")
        if discovery:
            fact_id = f"insp_{hotspot.id}_{discovery['fact_id']}"
            self._fact_details[fact_id] = discovery
            new_facts = [fact_id]

        result = InspectionResult(
            success=True,
            description=f"{lead_in}\n\n{data['description']}",
            zoom_level=ZoomLevel.FINE,
            new_facts=new_facts,
            tool_helped=True,
            generated_details=data.get("detail_hooks", []),
        )
        result._verbatim = True
        return result

    def _do_aspect(
        self, command, obj: InspectableObject, hotspot: 'Hotspot', state,
    ) -> InspectionResult:
        """Directional looks ("under the desk") and feature focus."""
        label = definite_label(obj.name)
        if command.intent == InspectionIntent.LOOK_DIRECTION:
            aspect_key = command.direction or "around"
            aspect_text = f"{aspect_key} {label}"
            lead_in = f"You look {aspect_key} {label}..."
        else:
            aspect_key = command.feature or "details"
            aspect_text = f"the {aspect_key} of {label}"
            lead_in = f"You focus on the {aspect_key}..."

        cache_key = (obj.id, aspect_key)
        data = self._aspect_cache.get(cache_key)
        if data is None:
            location = state.locations.get(state.current_location_id)
            data = self.detail_handler.generate_layer(
                object_name=obj.name,
                base_description=obj.base_description,
                zoom_value=ZoomLevel.CLOSE.value,
                location_name=location.name if location else "",
                location_description=location.description if location else "",
                prior_layers=self._layer_descriptions(obj),
                is_evidence=self._is_evidence(hotspot),
                clue_hint=self._clue_hint(hotspot),
                aspect=aspect_text,
            )
            if data is not None:
                self._aspect_cache[cache_key] = data

        if data is None:
            # LLM unavailable — fall back to the engine's template details
            detail = self.engine.detail_generator.generate_detail(
                object_id=obj.id,
                zoom_level=ZoomLevel.CLOSE.value,
                tags=obj.tags + [aspect_key],
                material=obj.material,
            )
            body = detail or "You don't notice anything unusual."
            result = InspectionResult(
                success=True,
                description=f"{lead_in}\n\n{body}",
                zoom_level=ZoomLevel.CLOSE,
                generated_details=[detail] if detail else [],
            )
            result._verbatim = True
            return result

        new_facts = []
        discovery = data.get("discovery")
        if discovery:
            fact_id = f"insp_{hotspot.id}_{discovery['fact_id']}"
            self._fact_details[fact_id] = discovery
            new_facts = [fact_id]

        result = InspectionResult(
            success=True,
            description=f"{lead_in}\n\n{data['description']}",
            zoom_level=ZoomLevel.CLOSE,
            new_facts=new_facts,
            generated_details=data.get("detail_hooks", []),
        )
        result._verbatim = True  # aspect text must not be rebuilt from layers
        return result

    # ------------------------------------------------------------------
    # Object and layer management
    # ------------------------------------------------------------------

    def _ensure_object(self, hotspot: 'Hotspot', state) -> InspectableObject:
        """Get or lazily create the InspectableObject for a hotspot."""
        object_id = self._object_by_hotspot.get(hotspot.id)
        if object_id and object_id in self.engine.objects:
            obj = self.engine.objects[object_id]
            obj.location_id = state.current_location_id
            return obj

        is_person = hotspot.hotspot_type == HotspotType.PERSON
        base = hotspot.examine_text or hotspot.description or f"The {hotspot.label}."
        if is_person and hotspot.target_id in state.characters:
            base = state.characters[hotspot.target_id].description or base

        obj = InspectableObject(
            id=f"insp_{hotspot.id}",
            name=hotspot.label,
            base_description=base,
            location_id=state.current_location_id,
            tags=[hotspot.hotspot_type.value],
            category="standard",
            material=guess_material(f"{hotspot.label} {base}"),
        )
        if is_person:
            obj.constraints = ZoomConstraints(
                max_level=ZoomLevel.CLOSE,
                requires_tool_for_fine=False,
                max_unaided_level=ZoomLevel.CLOSE,
            )
            obj.allow_generated_details = False  # material templates fit objects, not people
        obj.add_layer(DetailLayer(zoom_level=ZoomLevel.COARSE, description=base))

        # Planted evidence carries a tell: under magnification the staging
        # shows. Looking closer is the counter to a frame-up.
        if hotspot.planted_by:
            framed = state.characters.get(hotspot.frames)
            framed_name = framed.name if framed else "someone else"
            staged_fact = f"staged_{hotspot.id}"[:64]
            obj.add_layer(DetailLayer(
                zoom_level=ZoomLevel.FINE,
                description=(
                    "Under magnification the story falls apart. The wear is "
                    "wrong — edges too clean, no dust in the creases, resting "
                    "ON the grime instead of in it. This wasn't dropped. "
                    "It was placed."
                ),
                reveals_facts=[staged_fact],
                first_time_text=(
                    "Under the lens, the story falls apart: edges too clean, "
                    "no dust in the creases, sitting ON the grime rather than "
                    "in it. This wasn't dropped here. It was placed — recently, "
                    "and carefully."
                ),
            ))
            self._fact_details[staged_fact] = {
                "description": (
                    f"The {hotspot.label} was planted. Someone staged it to "
                    f"point you at {framed_name} — which means someone else "
                    "has something to hide."
                ),
                "is_evidence": True,
            }

        self.engine.register_object(obj)
        self._object_by_hotspot[hotspot.id] = obj.id
        self._hotspot_by_object[obj.id] = hotspot.id
        return obj

    def _ensure_layer(
        self, obj: InspectableObject, level: ZoomLevel, hotspot: 'Hotspot', state,
    ) -> None:
        """Lazily generate the LLM detail layer for a zoom level."""
        if level.value < ZoomLevel.MEDIUM.value or obj.has_layer(level):
            return

        attempted = self._layers_attempted.setdefault(obj.id, set())
        if level.value in attempted:
            return
        attempted.add(level.value)

        location = state.locations.get(state.current_location_id)
        is_evidence = self._is_evidence(hotspot)
        data = self.detail_handler.generate_layer(
            object_name=obj.name,
            base_description=obj.base_description,
            zoom_value=level.value,
            location_name=location.name if location else "",
            location_description=location.description if location else "",
            prior_layers=self._layer_descriptions(obj),
            is_evidence=is_evidence and level.value >= ZoomLevel.CLOSE.value,
            clue_hint=self._clue_hint(hotspot) if level.value >= ZoomLevel.CLOSE.value else None,
        )
        if data is None:
            # Offline: the engine's template DetailGenerator still adds
            # procedural micro-details on top of existing layers.
            return

        # A degenerate LLM can repeat itself; don't stack identical layers
        # unless this one carries a new discovery
        description = data["description"].strip()
        discovery = data.get("discovery")
        is_duplicate = any(
            existing.description.strip() == description
            for existing in obj.layers.values()
        )
        brings_new_fact = (
            discovery is not None
            and f"insp_{hotspot.id}_{discovery['fact_id']}" not in self._fact_details
        )
        if is_duplicate and not brings_new_fact:
            return

        layer = DetailLayer(
            zoom_level=level,
            description=description,
            tags=data.get("detail_hooks", []),
        )
        if discovery:
            fact_id = f"insp_{hotspot.id}_{discovery['fact_id']}"
            layer.reveals_facts = [fact_id]
            self._fact_details[fact_id] = discovery
        obj.add_layer(layer)

    @staticmethod
    def _layer_descriptions(obj: InspectableObject) -> list[str]:
        layers = sorted(obj.layers.values(), key=lambda l: l.zoom_level.value)
        return [l.description for l in layers if l.description]

    @staticmethod
    def _is_evidence(hotspot: 'Hotspot') -> bool:
        return (
            hotspot.hotspot_type == HotspotType.EVIDENCE
            or hotspot.reveals_fact is not None
        )

    @staticmethod
    def _clue_hint(hotspot: 'Hotspot') -> Optional[str]:
        if hotspot.planted_by:
            return (
                "this object was planted here recently to mislead the "
                "detective — physical details should feel subtly wrong "
                "(too clean, wear inconsistent with its supposed history)"
            )
        if hotspot.reveals_fact:
            return hotspot.examine_text or hotspot.description or None
        return None

    def _recent_object(self, location: 'Location') -> Optional[InspectableObject]:
        """Most recently inspected object that is still present here."""
        for object_id in self.engine.zoom_manager.get_recently_inspected(
            600.0, limit=5
        ):
            obj = self.engine.objects.get(object_id)
            if obj is None:
                continue
            hotspot_id = self._hotspot_by_object.get(object_id)
            for hs in location.hotspots:
                if hs.id == hotspot_id and hs.visible and hs.active:
                    return obj
        return None

    def _hotspot_for(
        self, obj: InspectableObject, location: 'Location'
    ) -> Optional['Hotspot']:
        hotspot_id = self._hotspot_by_object.get(obj.id)
        for hs in location.hotspots:
            if hs.id == hotspot_id:
                return hs
        return None

    # ------------------------------------------------------------------
    # World-state sync
    # ------------------------------------------------------------------

    def _sync_tools(self, state) -> None:
        """Recognize inspection tools straight from the inventory."""
        for item in state.inventory:
            item_lower = str(item).lower()
            for keyword, tool_id in TOOL_KEYWORDS:
                if keyword in item_lower and not self.engine.has_tool(tool_id):
                    tool = get_tool(tool_id)
                    if tool:
                        self.engine.add_player_tool(tool)
                    break

    def _sync_light(self, state) -> None:
        """Darkness limits inspection unless the player carries a light."""
        try:
            visibility = state.environment.get_visibility(state.current_location_id)
        except Exception:
            visibility = 1.0
        has_lantern = self.engine.has_tool("lantern")
        self.engine.has_light = visibility >= DARKNESS_THRESHOLD or has_lantern

    # ------------------------------------------------------------------
    # Output and consequences
    # ------------------------------------------------------------------

    def _render_result(self, obj: InspectableObject, result: InspectionResult) -> None:
        tool_line, self._tool_line = self._tool_line, None

        if not result.success:
            self.renderer.render_narration(result.description)
            if result.hint:
                self.renderer.render_text(f"({result.hint})")
            return

        hooks = []
        layer = obj.get_layer(result.zoom_level)
        if layer and layer.tags:
            hooks = [t for t in layer.tags if isinstance(t, str)][:2]

        hint = self._depth_hint(obj, result.zoom_level)
        self.renderer.render_zoom_view(
            target_name=obj.name,
            zoom_level=result.zoom_level,
            text=self._display_text(obj, result, tool_line),
            hooks=hooks,
            hint=hint,
        )

    @staticmethod
    def _display_text(
        obj: InspectableObject, result: InspectionResult, tool_line: Optional[str],
    ) -> str:
        """
        Text to show for this zoom step.

        The engine concatenates every visible layer, which re-prints
        everything already read. Show only what THIS depth reveals: the
        current layer plus any procedurally generated micro-details.
        """
        if getattr(result, "_verbatim", False):
            return result.description

        layer = obj.get_layer(result.zoom_level)
        if layer is None or not layer.description:
            # Offline fallback: no LLM layer at this depth, but the template
            # generator still produced micro-details — show those alone
            # instead of re-printing every earlier layer.
            if result.zoom_level != ZoomLevel.COARSE and result.generated_details:
                parts = [tool_line] if tool_line else []
                parts.append(f"You study {definite_label(obj.name)} more closely.")
                parts.extend(d for d in result.generated_details if d)
                return "\n\n".join(parts)
            return result.description

        parts = []
        if tool_line:
            parts.append(tool_line)
        parts.append(layer.get_description(result.first_time_at_level))
        parts.extend(d for d in result.generated_details if d)
        return "\n\n".join(parts)

    def _depth_hint(self, obj: InspectableObject, level: ZoomLevel) -> Optional[str]:
        """Tell the player whether — and how — they can go deeper."""
        if not level.can_zoom_in():
            return None
        next_level = level.zoom_in()
        if next_level.value > obj.constraints.max_level.value:
            return None

        has_magnifier = any(
            t.zoom_bonus > 0 for t in self.engine.player_tools
        )
        if next_level == ZoomLevel.FINE and obj.constraints.requires_tool_for_fine:
            if has_magnifier:
                return "Your magnifying glass could reveal even finer detail."
            return "Finer detail would take a magnifying glass."
        return "You could look closer still."

    def _apply_result(
        self, result: InspectionResult, hotspot: 'Hotspot', state, config,
        location: 'Location',
    ) -> None:
        if not result.success:
            return

        # Record discoveries in the player's memory
        for fact_id in result.new_facts:
            if fact_id in self._recorded_facts or state.memory.player.has_discovered(fact_id):
                continue
            self._recorded_facts.add(fact_id)

            detail = self._fact_details.get(fact_id)
            description = (
                detail["description"] if detail
                else fact_id.replace("_", " ")
            )
            state.memory.player_discovers(
                fact_id=fact_id,
                description=description,
                location=state.current_location_id,
                source=f"close inspection of {hotspot.label}",
                is_evidence=detail.get("is_evidence", True) if detail else True,
            )
            self.renderer.render_discovery(description)

            if state.spine:
                state.spine.make_revelation(fact_id)

            # A find that is a distinct physical thing enters the scene
            # as its own hotspot — inspectable and takeable in turn
            if detail and detail.get("reveals_object"):
                self._spawn_hotspot(
                    detail["reveals_object"], fact_id, hotspot, location, state,
                )

        # Enough evidence in one place can crack a lead in the case
        if result.new_facts:
            check_location_leads(state, self.renderer)

        # Grant found items
        for item in result.new_items:
            key = (hotspot.id, item)
            if key in self._granted_items:
                continue
            self._granted_items.add(key)
            state.inventory.append(item)
            self.renderer.render_text(f"Added to inventory: {item}")

        # Reveal hidden hotspots
        for hotspot_id in result.new_hotspots:
            for hs in location.hotspots:
                if hs.id == hotspot_id and not hs.visible:
                    hs.show()
                    self.renderer.render_narration(f"You notice {hs.label}.")

        # NPCs present notice close scrutiny — this feeds the rumor network
        if result.zoom_level.value >= ZoomLevel.CLOSE.value:
            self._record_witnessed(hotspot, state, location)

        # Time passes; the inspection engine tracks it for recency
        if config.time_passes_on_action:
            state.memory.advance_time(config.time_units_per_action)
            self.engine.advance_time(float(config.time_units_per_action))

    _SPAWN_TYPE_MAP = {
        "item": HotspotType.ITEM,
        "evidence": HotspotType.EVIDENCE,
        "object": HotspotType.OBJECT,
        "container": HotspotType.CONTAINER,
    }

    def _spawn_hotspot(
        self,
        revealed: dict,
        fact_id: str,
        source_hotspot: 'Hotspot',
        location: 'Location',
        state,
    ) -> None:
        """Materialize a discovered object as a new hotspot in the scene."""
        label = revealed["label"]

        # Never duplicate: the same discovery only spawns once, and don't
        # shadow any existing hotspot with the same name — including ones
        # that were destroyed or hidden (a removed object must stay removed)
        spawn_id = f"{source_hotspot.id}_found_{fact_id[-24:]}"
        if any(hs.id == spawn_id for hs in location.hotspots):
            return
        if any(hs.label.lower() == label.lower() for hs in location.hotspots):
            return

        hotspot_type = self._SPAWN_TYPE_MAP.get(
            revealed.get("type", "evidence"), HotspotType.EVIDENCE
        )
        description = (
            revealed.get("description")
            or f"Found while inspecting {definite_label(source_hotspot.label)}."
        )

        x, y = source_hotspot.position
        new_hotspot = Hotspot(
            id=spawn_id,
            label=label,
            hotspot_type=hotspot_type,
            position=(x + 2, y + 1),
            description=description,
            examine_text=description,
        )
        if hotspot_type in (HotspotType.ITEM, HotspotType.EVIDENCE):
            new_hotspot.gives_item = label.lower()
            new_hotspot.take_text = f"You carefully collect {definite_label(label)}."

        location.add_hotspot(new_hotspot)
        self.renderer.render_narration(
            f"New point of interest: {label}. "
            f"({definite_label(label)} can now be examined on its own.)"
        )

        # Found in front of witnesses? Word travels. Leave it here too
        # long and someone with a secret will get to it first.
        witnesses = self._witnesses_at(state, location, source_hotspot)
        watch = getattr(state, 'evidence_watch', None)
        if witnesses and watch is not None and state.spine:
            watch.register(
                hotspot_id=new_hotspot.id,
                location_id=state.current_location_id,
                label=label,
                fact_id=fact_id,
                witnesses=witnesses,
                created_time=state.memory.current_time,
            )

    @staticmethod
    def _witnesses_at(
        state, location: 'Location', exclude: Optional['Hotspot'] = None,
    ) -> list[str]:
        """NPCs present who can see what the player is doing."""
        exclude_id = exclude.target_id if exclude else None
        return [
            hs.target_id
            for hs in location.hotspots
            if (
                hs.hotspot_type == HotspotType.PERSON
                and hs.target_id
                and hs.target_id in state.characters
                and hs.active
                and hs.target_id != exclude_id
            )
        ]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize everything the manager learned this playthrough."""
        return {
            "engine": self.engine.to_dict(),
            "object_by_hotspot": dict(self._object_by_hotspot),
            "hotspot_by_object": dict(self._hotspot_by_object),
            "layers_attempted": {
                k: sorted(v) for k, v in self._layers_attempted.items()
            },
            "fact_details": dict(self._fact_details),
            "recorded_facts": sorted(self._recorded_facts),
            "granted_items": [list(pair) for pair in sorted(self._granted_items)],
            "aspect_cache": [
                [obj_id, aspect, data]
                for (obj_id, aspect), data in self._aspect_cache.items()
            ],
        }

    def restore(self, data: Optional[dict]) -> None:
        """Restore manager state from a snapshot."""
        if not data:
            return
        from .inspection import InspectionEngine
        if data.get("engine"):
            self.engine = InspectionEngine.from_dict(data["engine"])
        self._object_by_hotspot = dict(data.get("object_by_hotspot", {}))
        self._hotspot_by_object = dict(data.get("hotspot_by_object", {}))
        self._layers_attempted = {
            k: set(v) for k, v in data.get("layers_attempted", {}).items()
        }
        self._fact_details = dict(data.get("fact_details", {}))
        self._recorded_facts = set(data.get("recorded_facts", []))
        self._granted_items = {
            tuple(pair) for pair in data.get("granted_items", [])
        }
        self._aspect_cache = {
            (obj_id, aspect): cached
            for obj_id, aspect, cached in data.get("aspect_cache", [])
        }

    def _record_witnessed(
        self, hotspot: 'Hotspot', state, location: 'Location'
    ) -> None:
        witnesses = self._witnesses_at(state, location, hotspot)
        if not witnesses:
            return

        description = f"Player scrutinized the {hotspot.label} very closely"
        state.memory.record_witnessed_event(
            event_type=EventType.DISCOVERY,
            description=description,
            location=state.current_location_id,
            actors=["player"],
            witnesses=witnesses,
            player_witnessed=False,
        )
        bridge = getattr(state, 'event_bridge', None)
        if bridge:
            bridge.bridge_event(
                event_type="discovery",
                description=description,
                location=state.current_location_id,
                actors=["player"],
                witnesses=witnesses,
            )
