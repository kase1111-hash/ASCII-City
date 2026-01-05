"""
Inspection & Zoom System - Progressive detail revelation.

Phase 8 Implementation: Natural language inspection, zoom levels,
tool-based inspection, and procedural micro-detail generation.

Core principle: "Look closer" always reveals something new.
"""

from .zoom_level import ZoomLevel, ZoomDirection
from .tool import (
    InspectionTool,
    ToolType,
    ToolAffordance,
    INSPECTION_TOOLS,
    get_tool
)
from .inspectable import (
    DetailLayer,
    InspectableObject,
    InspectableFactory
)
from .zoom_state import (
    ZoomState,
    ZoomStateManager,
    ZoomHistory
)
from .detail_generator import (
    DetailGenerator,
    DetailType,
    DetailTemplate,
    DETAIL_TEMPLATES
)
from .inspection_parser import (
    InspectionParser,
    InspectionIntent,
    InspectionCommand
)
from .inspection_engine import (
    InspectionEngine,
    InspectionResult,
    InspectionContext
)

__all__ = [
    # Zoom Levels
    "ZoomLevel",
    "ZoomDirection",
    # Tools
    "InspectionTool",
    "ToolType",
    "ToolAffordance",
    "INSPECTION_TOOLS",
    "get_tool",
    # Inspectable Objects
    "DetailLayer",
    "InspectableObject",
    "InspectableFactory",
    # Zoom State
    "ZoomState",
    "ZoomStateManager",
    "ZoomHistory",
    # Detail Generation
    "DetailGenerator",
    "DetailType",
    "DetailTemplate",
    "DETAIL_TEMPLATES",
    # Parsing
    "InspectionParser",
    "InspectionIntent",
    "InspectionCommand",
    # Engine
    "InspectionEngine",
    "InspectionResult",
    "InspectionContext",
]
