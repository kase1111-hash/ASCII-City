"""
InspectionParser - Natural language inspection command parsing.

Parses commands like:
- "look at the statue"
- "examine the painting closely"
- "zoom in on the gears"
- "use magnifying glass on the inscription"
- "look under the table"
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple
from enum import Enum
import re


class InspectionIntent(Enum):
    """Types of inspection intents."""
    INSPECT = "inspect"             # Basic examination
    ZOOM_IN = "zoom_in"             # Look closer
    ZOOM_OUT = "zoom_out"           # Step back
    USE_TOOL = "use_tool"           # Use a specific tool
    LOOK_AROUND = "look_around"     # General look
    LOOK_DIRECTION = "look_direction"   # Look in a direction (behind, under, etc.)
    FOCUS = "focus"                 # Focus on specific feature
    RESET = "reset"                 # Reset zoom


@dataclass
class InspectionCommand:
    """A parsed inspection command."""
    intent: InspectionIntent
    target: Optional[str] = None        # What to inspect
    tool: Optional[str] = None          # Tool to use
    direction: Optional[str] = None     # Direction (behind, under, etc.)
    feature: Optional[str] = None       # Specific feature to focus on
    raw_input: str = ""                 # Original input

    @property
    def wants_closer_look(self) -> bool:
        """Check if command wants to zoom in."""
        return self.intent in (InspectionIntent.ZOOM_IN, InspectionIntent.USE_TOOL, InspectionIntent.FOCUS)

    @property
    def wants_tool(self) -> bool:
        """Check if command specifies a tool."""
        return self.tool is not None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "intent": self.intent.value,
            "target": self.target,
            "tool": self.tool,
            "direction": self.direction,
            "feature": self.feature,
            "raw_input": self.raw_input
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'InspectionCommand':
        """Deserialize from dictionary."""
        data["intent"] = InspectionIntent(data["intent"])
        return cls(**data)


class InspectionParser:
    """
    Parser for natural language inspection commands.

    Recognizes patterns like:
    - Basic: "look at X", "examine X", "inspect X"
    - Zooming: "look closer", "zoom in", "look more closely"
    - Tools: "use magnifying glass on X", "examine X with telescope"
    - Directional: "look behind X", "check under X"
    - Focus: "focus on the carvings", "look at the gears"
    """

    def __init__(self):
        # Basic inspection verbs
        self.inspect_verbs = {
            "look", "examine", "inspect", "see", "view", "check",
            "study", "observe", "watch", "regard", "scrutinize"
        }

        # Zoom in phrases
        self.zoom_in_phrases = {
            "closer", "closely", "more closely", "in", "nearer",
            "zoom in", "zoom", "magnify", "enlarge", "enhance"
        }

        # Zoom out phrases
        self.zoom_out_phrases = {
            "back", "out", "away", "farther", "further",
            "zoom out", "step back", "pull back"
        }

        # Direction prepositions
        self.directions = {
            "behind", "under", "beneath", "above", "over",
            "inside", "within", "between", "through", "around"
        }

        # Tool names (mapped to tool IDs)
        self.tool_names = {
            "magnifying glass": "magnifying_glass",
            "magnifier": "magnifying_glass",
            "glass": "magnifying_glass",
            "loupe": "jewelers_loupe",
            "jeweler's loupe": "jewelers_loupe",
            "telescope": "telescope",
            "spyglass": "telescope",
            "lantern": "lantern",
            "lamp": "lantern",
            "light": "lantern",
            "spectacles": "spectacles",
            "glasses": "spectacles",
            "reading glasses": "spectacles",
            "uv light": "uv_light",
            "blacklight": "uv_light",
            "ultraviolet": "uv_light",
            "mirror": "mirror",
            "stethoscope": "stethoscope",
            "probe": "probe",
        }

        # Words to ignore
        self.articles = {"the", "a", "an", "at", "to", "on", "in", "with"}

    def parse(self, raw_input: str) -> InspectionCommand:
        """Parse an inspection command from natural language."""
        text = raw_input.lower().strip()

        if not text:
            return InspectionCommand(
                intent=InspectionIntent.LOOK_AROUND,
                raw_input=raw_input
            )

        # Check for tool usage patterns
        tool_result = self._check_tool_usage(text)
        if tool_result:
            return InspectionCommand(
                intent=InspectionIntent.USE_TOOL,
                target=tool_result[1],
                tool=tool_result[0],
                raw_input=raw_input
            )

        # Check for zoom commands
        zoom_result = self._check_zoom_command(text)
        if zoom_result:
            return InspectionCommand(
                intent=zoom_result[0],
                target=zoom_result[1],
                raw_input=raw_input
            )

        # Check for directional look
        direction_result = self._check_directional(text)
        if direction_result:
            return InspectionCommand(
                intent=InspectionIntent.LOOK_DIRECTION,
                target=direction_result[1],
                direction=direction_result[0],
                raw_input=raw_input
            )

        # Check for focus on feature
        focus_result = self._check_focus(text)
        if focus_result:
            return InspectionCommand(
                intent=InspectionIntent.FOCUS,
                target=focus_result[0],
                feature=focus_result[1],
                raw_input=raw_input
            )

        # Parse as basic inspection
        target = self._extract_target(text)

        # Determine if it's a general look or targeted inspection
        if target:
            return InspectionCommand(
                intent=InspectionIntent.INSPECT,
                target=target,
                raw_input=raw_input
            )
        else:
            return InspectionCommand(
                intent=InspectionIntent.LOOK_AROUND,
                raw_input=raw_input
            )

    def _check_tool_usage(self, text: str) -> Optional[Tuple[str, Optional[str]]]:
        """Check for tool usage pattern."""
        # Pattern: "use X on Y" or "examine Y with X"
        for tool_phrase, tool_id in self.tool_names.items():
            if tool_phrase in text:
                # "use X on Y"
                use_pattern = rf"use\s+{re.escape(tool_phrase)}\s+(?:on|to\s+(?:examine|look\s+at|inspect))\s+(.+)"
                match = re.search(use_pattern, text)
                if match:
                    target = self._clean_target(match.group(1))
                    return (tool_id, target)

                # "examine Y with X"
                with_pattern = rf"(?:examine|look\s+at|inspect)\s+(.+?)\s+(?:with|using)\s+{re.escape(tool_phrase)}"
                match = re.search(with_pattern, text)
                if match:
                    target = self._clean_target(match.group(1))
                    return (tool_id, target)

                # Just "use X" (no target)
                if f"use {tool_phrase}" in text or f"use the {tool_phrase}" in text:
                    return (tool_id, None)

        return None

    def _check_zoom_command(self, text: str) -> Optional[Tuple[InspectionIntent, Optional[str]]]:
        """Check for zoom in/out command."""
        # Check zoom out first (more specific)
        for phrase in self.zoom_out_phrases:
            if phrase in text:
                return (InspectionIntent.ZOOM_OUT, None)

        # Check zoom in
        for phrase in self.zoom_in_phrases:
            if phrase in text:
                # Try to extract target
                target = None
                patterns = [
                    rf"(?:look|zoom|examine)\s+{phrase}\s+(?:at|on)?\s*(.+)",
                    rf"(?:look|zoom|examine)\s+(?:at|on)?\s*(.+?)\s+{phrase}",
                ]
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        target = self._clean_target(match.group(1))
                        break
                return (InspectionIntent.ZOOM_IN, target)

        return None

    def _check_directional(self, text: str) -> Optional[Tuple[str, Optional[str]]]:
        """Check for directional inspection."""
        for direction in self.directions:
            pattern = rf"(?:look|check|see|examine)\s+{direction}\s+(.+)"
            match = re.search(pattern, text)
            if match:
                target = self._clean_target(match.group(1))
                return (direction, target)

        return None

    def _check_focus(self, text: str) -> Optional[Tuple[Optional[str], str]]:
        """Check for focus on specific feature."""
        # Pattern: "focus on X" or "look at the X on Y"
        focus_patterns = [
            r"focus\s+(?:on|at)\s+(.+)",
            r"(?:look|examine)\s+(?:at|the)\s+(\w+)\s+(?:on|of)\s+(.+)",
        ]

        for pattern in focus_patterns:
            match = re.search(pattern, text)
            if match:
                if match.lastindex == 1:
                    return (None, self._clean_target(match.group(1)))
                else:
                    feature = self._clean_target(match.group(1))
                    target = self._clean_target(match.group(2))
                    return (target, feature)

        return None

    def _extract_target(self, text: str) -> Optional[str]:
        """Extract the target of inspection."""
        # Remove verb
        for verb in self.inspect_verbs:
            text = re.sub(rf"^{verb}\s+", "", text)

        # Remove prepositions
        text = re.sub(r"^(?:at|on|the)\s+", "", text)

        target = self._clean_target(text)
        return target if target else None

    def _clean_target(self, target: str) -> str:
        """Clean up target string."""
        words = target.split()
        # Remove articles from start
        while words and words[0] in self.articles:
            words.pop(0)
        # Remove trailing articles/prepositions
        while words and words[-1] in self.articles:
            words.pop()
        return " ".join(words).strip()

    def get_zoom_words(self) -> list[str]:
        """Get words that indicate zooming."""
        return list(self.zoom_in_phrases | self.zoom_out_phrases)

    def get_tool_names(self) -> list[str]:
        """Get recognized tool names."""
        return list(self.tool_names.keys())

    def is_inspection_command(self, text: str) -> bool:
        """Check if text is an inspection command."""
        text = text.lower().strip()

        # Check for inspection verbs
        for verb in self.inspect_verbs:
            if text.startswith(verb):
                return True

        # Check for zoom words
        for phrase in self.zoom_in_phrases | self.zoom_out_phrases:
            if phrase in text:
                return True

        # Check for tool names
        for tool in self.tool_names:
            if tool in text:
                return True

        return False

    def suggest_completion(self, partial: str) -> list[str]:
        """Suggest completions for partial input."""
        partial = partial.lower().strip()
        suggestions = []

        # Suggest verbs if just starting
        if len(partial.split()) <= 1:
            for verb in self.inspect_verbs:
                if verb.startswith(partial):
                    suggestions.append(verb)

        # Suggest zoom phrases
        for phrase in self.zoom_in_phrases:
            if phrase.startswith(partial) or partial in phrase:
                suggestions.append(f"look {phrase}")

        # Suggest tool usage
        if "use" in partial:
            for tool in self.tool_names:
                suggestions.append(f"use {tool} on")

        return suggestions[:5]


def parse_inspection(text: str) -> InspectionCommand:
    """Convenience function to parse inspection command."""
    parser = InspectionParser()
    return parser.parse(text)
