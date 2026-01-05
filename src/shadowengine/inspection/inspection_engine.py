"""
InspectionEngine - Main engine for the inspection and zoom system.

Coordinates all inspection systems:
- Parsing natural language commands
- Managing zoom state per object
- Generating procedural details
- Handling tool-based inspection
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import random

from .zoom_level import ZoomLevel, ZoomDirection, ZoomConstraints
from .tool import InspectionTool, ToolAffordance, get_tool, get_best_tool_for_inspection
from .inspectable import InspectableObject, DetailLayer, InspectableFactory
from .zoom_state import ZoomState, ZoomStateManager, ZoomHistory
from .detail_generator import DetailGenerator, DetailType
from .inspection_parser import InspectionParser, InspectionCommand, InspectionIntent


@dataclass
class InspectionContext:
    """Context for an inspection action."""
    object_id: str
    object_name: str
    current_zoom: ZoomLevel
    max_zoom: ZoomLevel
    tool_used: Optional[str] = None
    has_light: bool = True
    distance: float = 0.0
    known_facts: set[str] = field(default_factory=set)


@dataclass
class InspectionResult:
    """Result of an inspection action."""
    success: bool
    description: str
    zoom_level: ZoomLevel
    ascii_art: Optional[str] = None

    # Discoveries
    new_facts: list[str] = field(default_factory=list)
    new_items: list[str] = field(default_factory=list)
    new_hotspots: list[str] = field(default_factory=list)

    # State
    first_time_at_level: bool = False
    tool_helped: bool = False
    zoom_changed: bool = False
    generated_details: list[str] = field(default_factory=list)

    # Errors/messages
    error: Optional[str] = None
    hint: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "success": self.success,
            "description": self.description,
            "zoom_level": self.zoom_level.value,
            "ascii_art": self.ascii_art,
            "new_facts": self.new_facts,
            "new_items": self.new_items,
            "new_hotspots": self.new_hotspots,
            "first_time_at_level": self.first_time_at_level,
            "tool_helped": self.tool_helped,
            "zoom_changed": self.zoom_changed,
            "generated_details": self.generated_details,
            "error": self.error,
            "hint": self.hint
        }


class InspectionEngine:
    """
    Main engine for inspection and zoom system.

    Coordinates:
    - Object registration and management
    - Zoom state tracking
    - Detail generation
    - Tool integration
    - Natural language parsing
    """

    def __init__(self, seed: Optional[int] = None):
        self.parser = InspectionParser()
        self.zoom_manager = ZoomStateManager()
        self.detail_generator = DetailGenerator(seed=seed)

        # Object registry
        self.objects: dict[str, InspectableObject] = {}

        # Player state
        self.player_tools: list[InspectionTool] = []
        self.player_facts: set[str] = set()

        # Current context
        self.current_location: Optional[str] = None
        self.has_light: bool = True

    def register_object(self, obj: InspectableObject) -> None:
        """Register an inspectable object."""
        self.objects[obj.id] = obj

    def remove_object(self, object_id: str) -> None:
        """Remove an inspectable object."""
        if object_id in self.objects:
            del self.objects[object_id]

    def get_object(self, object_id: str) -> Optional[InspectableObject]:
        """Get an inspectable object by ID."""
        return self.objects.get(object_id)

    def find_object_by_name(self, name: str) -> Optional[InspectableObject]:
        """Find an object by name (fuzzy match)."""
        name_lower = name.lower()
        for obj in self.objects.values():
            if name_lower in obj.name.lower() or obj.name.lower() in name_lower:
                return obj
        return None

    def add_player_tool(self, tool: InspectionTool) -> None:
        """Add a tool to player inventory."""
        if tool not in self.player_tools:
            self.player_tools.append(tool)

    def remove_player_tool(self, tool_id: str) -> None:
        """Remove a tool from player inventory."""
        self.player_tools = [t for t in self.player_tools if t.id != tool_id]

    def has_tool(self, tool_id: str) -> bool:
        """Check if player has a specific tool."""
        return any(t.id == tool_id for t in self.player_tools)

    def get_tool_by_id(self, tool_id: str) -> Optional[InspectionTool]:
        """Get a player's tool by ID."""
        for tool in self.player_tools:
            if tool.id == tool_id:
                return tool
        return None

    def add_player_fact(self, fact_id: str) -> None:
        """Add a fact to player knowledge."""
        self.player_facts.add(fact_id)

    def process_command(
        self,
        text: str,
        target_override: Optional[str] = None
    ) -> InspectionResult:
        """
        Process a natural language inspection command.

        Returns an InspectionResult with description, discoveries, etc.
        """
        command = self.parser.parse(text)

        # Override target if specified
        if target_override:
            command.target = target_override

        # Handle different intents
        if command.intent == InspectionIntent.LOOK_AROUND:
            return self._handle_look_around()

        elif command.intent == InspectionIntent.INSPECT:
            return self._handle_inspect(command)

        elif command.intent == InspectionIntent.ZOOM_IN:
            return self._handle_zoom_in(command)

        elif command.intent == InspectionIntent.ZOOM_OUT:
            return self._handle_zoom_out(command)

        elif command.intent == InspectionIntent.USE_TOOL:
            return self._handle_use_tool(command)

        elif command.intent == InspectionIntent.LOOK_DIRECTION:
            return self._handle_directional(command)

        elif command.intent == InspectionIntent.FOCUS:
            return self._handle_focus(command)

        elif command.intent == InspectionIntent.RESET:
            return self._handle_reset(command)

        return InspectionResult(
            success=False,
            description="I don't understand that inspection command.",
            zoom_level=ZoomLevel.COARSE,
            error="Unknown inspection intent"
        )

    def inspect_object(
        self,
        object_id: str,
        zoom_level: Optional[ZoomLevel] = None,
        tool: Optional[InspectionTool] = None
    ) -> InspectionResult:
        """
        Directly inspect an object at a specific zoom level.

        Lower-level API for programmatic inspection.
        """
        obj = self.objects.get(object_id)
        if not obj:
            return InspectionResult(
                success=False,
                description=f"Cannot find object '{object_id}'.",
                zoom_level=ZoomLevel.COARSE,
                error="Object not found"
            )

        # Determine zoom level
        if zoom_level is None:
            zoom_level = self.zoom_manager.get_current_zoom(object_id)

        # Check if zoom level is accessible
        tool_type = tool.tool_type.value if tool else None
        has_tool = tool is not None
        if not obj.can_zoom_to(zoom_level, has_tool, tool_type):
            max_zoom = obj.get_max_zoom_with_tool(has_tool, tool_type)
            return InspectionResult(
                success=False,
                description=f"You can't see that level of detail without the right tools.",
                zoom_level=max_zoom,
                hint=f"You might need a {obj.constraints.required_tool_type} to see finer details."
            )

        # Get state
        state = self.zoom_manager.get_state(object_id)
        first_time = state.is_first_time_at_level(zoom_level)

        # Build description
        description = obj.get_description_at_zoom(
            zoom_level=zoom_level,
            first_time=first_time,
            has_tool=has_tool,
            tool_type=tool_type,
            has_light=self.has_light,
            known_facts=self.player_facts
        )

        # Get ASCII art
        ascii_art = obj.get_ascii_at_zoom(zoom_level)

        # Get reveals
        reveals = obj.get_all_reveals(
            max_zoom=zoom_level,
            has_tool=has_tool,
            tool_type=tool_type,
            has_light=self.has_light,
            known_facts=self.player_facts
        )

        # Generate procedural details if enabled
        generated = []
        if obj.allow_generated_details and zoom_level.value >= ZoomLevel.MEDIUM.value:
            generated = self.detail_generator.generate_details(
                object_id=object_id,
                zoom_level=zoom_level.value,
                count=zoom_level.value,  # More details at higher zoom
                tags=obj.tags,
                material=obj.material,
                era=obj.era
            )
            if generated:
                description += "\n\n" + "\n".join(generated)

        # Record inspection
        zoom_changed = zoom_level != state.current_level
        new_discoveries = self.zoom_manager.record_zoom(
            object_id=object_id,
            new_level=zoom_level,
            tool_used=tool.id if tool else None,
            discoveries=reveals
        )

        # Update player facts
        for fact in reveals.get("facts", []):
            self.player_facts.add(fact)

        # Build tool text
        if tool:
            tool_text = tool.get_inspection_text(obj.name)
            description = tool_text + "\n\n" + description

        return InspectionResult(
            success=True,
            description=description,
            zoom_level=zoom_level,
            ascii_art=ascii_art,
            new_facts=reveals.get("facts", []),
            new_items=reveals.get("items", []),
            new_hotspots=reveals.get("hotspots", []),
            first_time_at_level=first_time,
            tool_helped=tool is not None,
            zoom_changed=zoom_changed,
            generated_details=generated
        )

    def zoom_in_on(
        self,
        object_id: str,
        tool: Optional[InspectionTool] = None
    ) -> InspectionResult:
        """Zoom in one level on an object."""
        current = self.zoom_manager.get_current_zoom(object_id)
        if not current.can_zoom_in():
            return InspectionResult(
                success=False,
                description="You're already examining this as closely as possible.",
                zoom_level=current,
                hint="You've reached maximum zoom."
            )

        new_level = current.zoom_in()
        return self.inspect_object(object_id, new_level, tool)

    def zoom_out_from(self, object_id: str) -> InspectionResult:
        """Zoom out one level from an object."""
        current = self.zoom_manager.get_current_zoom(object_id)
        if not current.can_zoom_out():
            return InspectionResult(
                success=False,
                description="You're already viewing this from the farthest perspective.",
                zoom_level=current
            )

        new_level = current.zoom_out()
        return self.inspect_object(object_id, new_level)

    def _handle_look_around(self) -> InspectionResult:
        """Handle general look around command."""
        # List inspectable objects at current location
        objects_here = [
            obj for obj in self.objects.values()
            if obj.location_id == self.current_location or obj.location_id is None
        ]

        if not objects_here:
            return InspectionResult(
                success=True,
                description="You look around but don't see anything particularly notable.",
                zoom_level=ZoomLevel.COARSE
            )

        descriptions = ["You look around and notice:"]
        for obj in objects_here:
            descriptions.append(f"- {obj.name}: {obj.base_description[:50]}...")

        return InspectionResult(
            success=True,
            description="\n".join(descriptions),
            zoom_level=ZoomLevel.COARSE
        )

    def _handle_inspect(self, command: InspectionCommand) -> InspectionResult:
        """Handle basic inspection command."""
        if not command.target:
            return self._handle_look_around()

        obj = self.find_object_by_name(command.target)
        if not obj:
            return InspectionResult(
                success=False,
                description=f"You don't see '{command.target}' here.",
                zoom_level=ZoomLevel.COARSE,
                error="Target not found"
            )

        return self.inspect_object(obj.id)

    def _handle_zoom_in(self, command: InspectionCommand) -> InspectionResult:
        """Handle zoom in command."""
        # Find target
        if command.target:
            obj = self.find_object_by_name(command.target)
        else:
            # Zoom in on last inspected object
            recent = self.zoom_manager.get_recently_inspected(60.0, limit=1)
            obj = self.objects.get(recent[0]) if recent else None

        if not obj:
            return InspectionResult(
                success=False,
                description="What would you like to look closer at?",
                zoom_level=ZoomLevel.COARSE,
                error="No target specified"
            )

        # Find best tool
        tool = get_best_tool_for_inspection(
            self.player_tools,
            needs_magnification=True
        )

        return self.zoom_in_on(obj.id, tool)

    def _handle_zoom_out(self, command: InspectionCommand) -> InspectionResult:
        """Handle zoom out command."""
        if command.target:
            obj = self.find_object_by_name(command.target)
        else:
            recent = self.zoom_manager.get_recently_inspected(60.0, limit=1)
            obj = self.objects.get(recent[0]) if recent else None

        if not obj:
            return InspectionResult(
                success=False,
                description="What would you like to step back from?",
                zoom_level=ZoomLevel.COARSE
            )

        return self.zoom_out_from(obj.id)

    def _handle_use_tool(self, command: InspectionCommand) -> InspectionResult:
        """Handle tool usage command."""
        if not command.tool:
            return InspectionResult(
                success=False,
                description="Use which tool?",
                zoom_level=ZoomLevel.COARSE,
                error="No tool specified"
            )

        tool = self.get_tool_by_id(command.tool)
        if not tool:
            return InspectionResult(
                success=False,
                description=f"You don't have a {command.tool}.",
                zoom_level=ZoomLevel.COARSE,
                error="Tool not available"
            )

        if not command.target:
            return InspectionResult(
                success=False,
                description=f"Use the {tool.name} on what?",
                zoom_level=ZoomLevel.COARSE,
                error="No target specified"
            )

        obj = self.find_object_by_name(command.target)
        if not obj:
            return InspectionResult(
                success=False,
                description=f"You don't see '{command.target}' here.",
                zoom_level=ZoomLevel.COARSE,
                error="Target not found"
            )

        # Check if tool is useful
        if not tool.can_inspect(obj.is_distant, obj.size, self.has_light):
            return InspectionResult(
                success=False,
                description=tool.fail_text.format(tool=tool.name, target=obj.name),
                zoom_level=self.zoom_manager.get_current_zoom(obj.id)
            )

        # Zoom in with tool
        current = self.zoom_manager.get_current_zoom(obj.id)
        target_value = min(
            current.value + tool.zoom_bonus + 1,
            ZoomLevel.FINE.value
        )
        target_zoom = ZoomLevel(target_value)

        return self.inspect_object(obj.id, target_zoom, tool)

    def _handle_directional(self, command: InspectionCommand) -> InspectionResult:
        """Handle directional inspection (behind, under, etc.)."""
        if not command.target:
            return InspectionResult(
                success=False,
                description=f"Look {command.direction} what?",
                zoom_level=ZoomLevel.COARSE
            )

        obj = self.find_object_by_name(command.target)
        if not obj:
            return InspectionResult(
                success=False,
                description=f"You don't see '{command.target}' here.",
                zoom_level=ZoomLevel.COARSE
            )

        # Generate directional description
        direction_descriptions = {
            "behind": f"You look behind {obj.name}...",
            "under": f"You crouch down and look under {obj.name}...",
            "beneath": f"You examine beneath {obj.name}...",
            "above": f"You look up above {obj.name}...",
            "inside": f"You peer inside {obj.name}...",
        }

        base_desc = direction_descriptions.get(
            command.direction,
            f"You look {command.direction} {obj.name}..."
        )

        # Generate detail for this direction
        detail = self.detail_generator.generate_detail(
            object_id=obj.id,
            zoom_level=2,
            tags=obj.tags + [command.direction],
            material=obj.material
        )

        if detail:
            description = f"{base_desc}\n\n{detail}"
        else:
            description = f"{base_desc}\n\nYou don't notice anything unusual."

        return InspectionResult(
            success=True,
            description=description,
            zoom_level=ZoomLevel.MEDIUM,
            generated_details=[detail] if detail else []
        )

    def _handle_focus(self, command: InspectionCommand) -> InspectionResult:
        """Handle focus on specific feature."""
        if command.target:
            obj = self.find_object_by_name(command.target)
        else:
            recent = self.zoom_manager.get_recently_inspected(60.0, limit=1)
            obj = self.objects.get(recent[0]) if recent else None

        if not obj:
            return InspectionResult(
                success=False,
                description="Focus on what?",
                zoom_level=ZoomLevel.COARSE
            )

        # Generate feature-specific detail
        feature = command.feature or "details"
        detail = self.detail_generator.generate_detail(
            object_id=obj.id,
            zoom_level=3,
            tags=obj.tags + [feature],
            material=obj.material,
            extra_context={"feature": feature}
        )

        description = f"You focus on the {feature} of {obj.name}...\n\n"
        if detail:
            description += detail
        else:
            description += f"The {feature} don't reveal anything new."

        return InspectionResult(
            success=True,
            description=description,
            zoom_level=ZoomLevel.FINE,
            generated_details=[detail] if detail else []
        )

    def _handle_reset(self, command: InspectionCommand) -> InspectionResult:
        """Handle reset zoom command."""
        if command.target:
            obj = self.find_object_by_name(command.target)
            if obj:
                self.zoom_manager.reset_zoom(obj.id)
                return InspectionResult(
                    success=True,
                    description=f"You step back from {obj.name}.",
                    zoom_level=ZoomLevel.COARSE,
                    zoom_changed=True
                )

        return InspectionResult(
            success=False,
            description="Reset zoom on what?",
            zoom_level=ZoomLevel.COARSE
        )

    def get_inspection_stats(self) -> dict[str, Any]:
        """Get inspection statistics."""
        return self.zoom_manager.get_inspection_statistics()

    def set_time(self, time: float) -> None:
        """Set current game time."""
        self.zoom_manager.set_time(time)

    def advance_time(self, dt: float) -> None:
        """Advance game time."""
        self.zoom_manager.advance_time(dt)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "objects": {k: v.to_dict() for k, v in self.objects.items()},
            "zoom_manager": self.zoom_manager.to_dict(),
            "detail_generator": self.detail_generator.to_dict(),
            "player_tools": [t.to_dict() for t in self.player_tools],
            "player_facts": list(self.player_facts),
            "current_location": self.current_location,
            "has_light": self.has_light
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'InspectionEngine':
        """Deserialize from dictionary."""
        engine = cls()

        # Restore objects
        engine.objects = {
            k: InspectableObject.from_dict(v)
            for k, v in data.get("objects", {}).items()
        }

        # Restore zoom manager
        engine.zoom_manager = ZoomStateManager.from_dict(
            data.get("zoom_manager", {})
        )

        # Restore detail generator
        engine.detail_generator = DetailGenerator.from_dict(
            data.get("detail_generator", {})
        )

        # Restore player state
        engine.player_tools = [
            InspectionTool.from_dict(t)
            for t in data.get("player_tools", [])
        ]
        engine.player_facts = set(data.get("player_facts", []))
        engine.current_location = data.get("current_location")
        engine.has_light = data.get("has_light", True)

        return engine
