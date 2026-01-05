"""
Command Parser - Fail-soft input parsing.

Interprets player intent, handles typos, and provides helpful error messages.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum
import re


class CommandType(Enum):
    """Types of commands the player can issue."""
    EXAMINE = "examine"
    TALK = "talk"
    TAKE = "take"
    USE = "use"
    GO = "go"
    INVENTORY = "inventory"
    WAIT = "wait"
    HELP = "help"
    SAVE = "save"
    LOAD = "load"
    QUIT = "quit"
    HOTSPOT = "hotspot"         # Numeric hotspot selection
    UNKNOWN = "unknown"

    # Dialogue-specific commands
    ASK = "ask"
    ACCUSE = "accuse"
    THREATEN = "threaten"
    SHOW = "show"
    LEAVE = "leave"


@dataclass
class Command:
    """A parsed player command."""

    command_type: CommandType
    target: Optional[str] = None        # What/who the command targets
    secondary: Optional[str] = None     # Secondary target (use X on Y)
    raw_input: str = ""                 # Original input
    hotspot_number: Optional[int] = None  # If hotspot selection
    topic: Optional[str] = None         # For dialogue commands

    def is_valid(self) -> bool:
        """Check if this is a valid, actionable command."""
        return self.command_type != CommandType.UNKNOWN


class CommandParser:
    """
    Fail-soft command parser that interprets player intent.
    """

    def __init__(self):
        # Verb mappings
        self.verb_mappings = {
            CommandType.EXAMINE: [
                "examine", "look", "check", "inspect", "see", "view",
                "read", "study", "observe", "x", "l"
            ],
            CommandType.TALK: [
                "talk", "speak", "ask", "question", "interview",
                "chat", "converse", "say", "t"
            ],
            CommandType.TAKE: [
                "take", "get", "grab", "pick", "collect", "acquire", "g"
            ],
            CommandType.USE: [
                "use", "apply", "put", "insert", "combine", "u"
            ],
            CommandType.GO: [
                "go", "walk", "move", "enter", "exit", "leave", "head",
                "n", "s", "e", "w", "north", "south", "east", "west"
            ],
            CommandType.INVENTORY: [
                "inventory", "inv", "items", "i"
            ],
            CommandType.WAIT: [
                "wait", "rest", "pass", "z"
            ],
            CommandType.HELP: [
                "help", "?", "commands", "h"
            ],
            CommandType.SAVE: ["save"],
            CommandType.LOAD: ["load"],
            CommandType.QUIT: ["quit", "exit", "q"],

            # Dialogue commands
            CommandType.ASK: ["ask about", "ask"],
            CommandType.ACCUSE: ["accuse", "confront"],
            CommandType.THREATEN: ["threaten", "intimidate"],
            CommandType.SHOW: ["show", "present", "give"],
            CommandType.LEAVE: ["leave", "goodbye", "bye", "end"]
        }

        # Build reverse mapping
        self.word_to_verb = {}
        for cmd_type, words in self.verb_mappings.items():
            for word in words:
                self.word_to_verb[word] = cmd_type

        # Common words to strip
        self.articles = {"the", "a", "an", "at", "to", "with", "on", "in"}

        # Direction shortcuts
        self.directions = {
            "n": "north", "s": "south", "e": "east", "w": "west",
            "ne": "northeast", "nw": "northwest",
            "se": "southeast", "sw": "southwest",
            "u": "up", "d": "down"
        }

    def parse(self, raw_input: str, context: dict = None) -> Command:
        """
        Parse player input into a Command.

        Args:
            raw_input: The raw text input from player
            context: Optional dict with available targets, hotspots, etc.

        Returns:
            A Command object representing the parsed input
        """
        context = context or {}

        # Normalize input
        text = raw_input.lower().strip()

        if not text:
            return Command(
                command_type=CommandType.UNKNOWN,
                raw_input=raw_input
            )

        # Check for hotspot number
        if text.isdigit():
            return Command(
                command_type=CommandType.HOTSPOT,
                hotspot_number=int(text),
                raw_input=raw_input
            )

        # Check for "number verb" pattern (e.g., "1 examine")
        match = re.match(r'^(\d+)\s+(.+)$', text)
        if match:
            hotspot_num = int(match.group(1))
            rest = match.group(2)
            cmd = self._parse_verb_phrase(rest, context)
            cmd.hotspot_number = hotspot_num
            cmd.raw_input = raw_input
            return cmd

        # Parse as verb phrase
        cmd = self._parse_verb_phrase(text, context)
        cmd.raw_input = raw_input
        return cmd

    def _parse_verb_phrase(self, text: str, context: dict) -> Command:
        """Parse a verb phrase (no hotspot number)."""
        tokens = text.split()
        if not tokens:
            return Command(command_type=CommandType.UNKNOWN)

        # Try to find verb
        verb_type, remaining_tokens = self._find_verb(tokens)

        if verb_type == CommandType.UNKNOWN:
            # Maybe they just typed a noun - try to figure out default action
            return self._infer_from_noun(tokens, context)

        # Extract target
        target = self._extract_target(remaining_tokens, context)

        # Check for "use X on Y" pattern
        secondary = None
        if verb_type == CommandType.USE and target:
            parts = target.split(" on ")
            if len(parts) == 2:
                target = parts[0].strip()
                secondary = parts[1].strip()

        return Command(
            command_type=verb_type,
            target=target,
            secondary=secondary
        )

    def _find_verb(self, tokens: list[str]) -> Tuple[CommandType, list[str]]:
        """Find the verb in tokens and return remaining tokens."""

        # Try two-word verbs first ("ask about")
        if len(tokens) >= 2:
            two_word = f"{tokens[0]} {tokens[1]}"
            if two_word in self.word_to_verb:
                return self.word_to_verb[two_word], tokens[2:]

        # Try single word verb
        if tokens[0] in self.word_to_verb:
            return self.word_to_verb[tokens[0]], tokens[1:]

        # Try fuzzy match for typos
        fuzzy_match = self._fuzzy_find_verb(tokens[0])
        if fuzzy_match:
            return fuzzy_match, tokens[1:]

        return CommandType.UNKNOWN, tokens

    def _fuzzy_find_verb(self, word: str, max_distance: int = 2) -> Optional[CommandType]:
        """Try to find a verb with typo tolerance."""
        for verb_word, cmd_type in self.word_to_verb.items():
            if len(verb_word) > 2 and self._levenshtein(word, verb_word) <= max_distance:
                return cmd_type
        return None

    def _levenshtein(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _extract_target(self, tokens: list[str], context: dict) -> Optional[str]:
        """Extract the target from remaining tokens."""
        # Remove articles
        filtered = [t for t in tokens if t not in self.articles]

        if not filtered:
            return None

        target = " ".join(filtered)

        # Try to match against known targets
        known_targets = context.get("targets", [])
        for known in known_targets:
            if known.lower() in target or target in known.lower():
                return known

        # Check for partial match
        for known in known_targets:
            if target in known.lower() or known.lower().startswith(target):
                return known

        return target if target else None

    def _infer_from_noun(self, tokens: list[str], context: dict) -> Command:
        """
        Infer command from noun only (player just typed object name).
        """
        target = " ".join([t for t in tokens if t not in self.articles])

        # Try to match against known targets and infer action
        hotspots = context.get("hotspots", [])
        for hotspot in hotspots:
            if target in hotspot.get("label", "").lower():
                hotspot_type = hotspot.get("type", "object")
                if hotspot_type == "person":
                    return Command(
                        command_type=CommandType.TALK,
                        target=hotspot.get("label")
                    )
                elif hotspot_type == "exit":
                    return Command(
                        command_type=CommandType.GO,
                        target=hotspot.get("label")
                    )
                else:
                    return Command(
                        command_type=CommandType.EXAMINE,
                        target=hotspot.get("label")
                    )

        # Default to examine for unknown nouns
        return Command(
            command_type=CommandType.EXAMINE,
            target=target
        )

    def get_help_text(self) -> str:
        """Return help text for available commands."""
        return """
Available Commands:
  [number]          - Interact with numbered hotspot
  examine [thing]   - Look at something closely
  talk [person]     - Start conversation with someone
  take [item]       - Pick up an item
  use [item] on [thing] - Use an item on something
  go [direction]    - Move to another location
  inventory         - Check your items
  wait              - Pass time
  help              - Show this help
  save              - Save your game
  quit              - Exit the game

During Conversation:
  ask about [topic] - Ask about something
  accuse            - Accuse them of something
  threaten          - Threaten them (affects morality)
  show [item]       - Show them something
  leave             - End conversation

Shortcuts: x=examine, t=talk, g=take, i=inventory, n/s/e/w=directions
"""

    def get_error_suggestion(self, command: Command, context: dict) -> str:
        """Generate a helpful error message for an unknown command."""
        if command.target:
            targets = context.get("targets", [])
            if targets:
                return f"I don't understand '{command.raw_input}'. Try one of: {', '.join(targets[:5])}"
            return f"I don't see '{command.target}' here."
        return "I don't understand. Type 'help' for available commands."
